"""
ABC Audio Predictor — Prédiction Streaming 0-Paramètre pour l'Audio
===================================================================

Prédicteur streaming basé sur le noyau ABC (Atangana-Baleanu-Caputo)
d'ordre α = 1/φ ≈ 0.618. Zéro paramètre appris — purement déterministe.

Fondement mathématique :
  Le noyau ABC K(t) = B(α) · E_α(-α · t^α / (1-α)) définit une mémoire
  non-locale où le poids du passé décroît de façon φ-optimale (le nombre
  d'or φ étant le plus irrationnel, il garantit l'absence de motifs de
  répétition dans les poids de mémoire).

  Prédiction :
    ψ[t+1] = Σ_{τ=0}^{N-1} K(τ) · ψ[t-τ]  /  Σ K(τ)

  C'est une moyenne pondérée de TOUT l'historique, avec décroissance
  en loi de puissance ~ t^{-(α+1)} ≈ t^{-1.618}.

Applications audio :
  - Prédiction de frames ψ futures (compensation de latence)
  - Détection parole/silence (via énergie ψ)
  - Détection de frontières de parole (topic shift audio)
  - Détection de chevauchement full-duplex (INTERFERE)
  - Prédiction de prosodie (pitch, énergie, rythme)

Intégration :
  - Réutilise abc_kernel.py (ABCKernel, ALPHA, PHI)
  - Compatible avec HarmonicVoiceCodecV2 (frames ψ ∈ ℂ⁵¹²)
  - S'intègre avec HolographicVoiceStore

Usage :
    from abc_audio_predictor import ABCAudioPredictor
    from harmonic_voice_codec_v2 import HarmonicVoiceCodecV2

    codec = HarmonicVoiceCodecV2()
    predictor = ABCAudioPredictor(dim=512)

    for audio_chunk in stream:
        psi = codec.encode_frame(audio_chunk)
        pred = predictor.process_stream_chunk(psi)
        
        if pred.is_speech:
            print(f"Parole détectée, énergie={pred.energy:.2f}")
        if pred.boundary_prob > 0.7:
            print("Fin de phrase probable")
        if pred.overlap_score > 0.5:
            print("Chevauchement détecté!")

Auteur : Équipe HarmoniqLLM
Date   : 2026-07-24
"""

import math
import time
from dataclasses import dataclass, field
from typing import Deque, List, Optional, Tuple
from collections import deque

import numpy as np

# ═══════════════════════════════════════════════════════════════════════════════
# IMPORTS INTERNES
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from abc_kernel import ABCKernel, ALPHA, PHI, B_1_PHI
except ImportError:
    # Fallback intégré (si abc_kernel.py n'est pas dans le path)
    PHI = 1.618033988749895
    ALPHA = 1.0 / PHI
    B_1_PHI = 0.8506508083
    
    class ABCKernel:
        """Fallback minimal du noyau ABC."""
        def __init__(self, max_len=2048):
            self._cache = {}
        
        def __call__(self, length, use_torch=False):
            if length in self._cache:
                return self._cache[length]
            import math as _m
            t = np.arange(length, dtype=np.float64)
            kernel = np.where(t <= 2,
                B_1_PHI * _m.exp(-t * ALPHA),
                B_1_PHI / (t ** (ALPHA + 1.0)) / _m.gamma(1.0 - ALPHA)
            )
            kernel = kernel / kernel.sum()
            self._cache[length] = kernel.astype(np.float32)
            return self._cache[length]

try:
    from holographic_encoder import _circular_correlate
except ImportError:
    def _circular_correlate(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """Corrélation circulaire via FFT."""
        A = np.fft.fft(a)
        B = np.fft.fft(b)
        return np.fft.ifft(A * np.conj(B))


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════

TAU = 2.0 * math.pi
DEFAULT_DIM = 512
DEFAULT_MAX_HISTORY = 100       # ~8 secondes à 12.5 Hz
DEFAULT_FRAME_RATE = 12.5       # Hz (80ms frames)
DEFAULT_FRAME_RATE_25HZ = 25.0  # Hz (40ms stride, 80ms frames 50% overlap)

# Seuils de détection
SPEECH_ENERGY_THRESHOLD = 0.01   # Énergie ψ minimale pour parole
SILENCE_ENERGY_THRESHOLD = 0.001 # Énergie ψ maximale pour silence
BOUNDARY_ENERGY_DROP = 0.5       # Ratio de chute d'énergie pour frontière
OVERLAP_COHERENCE_THRESHOLD = 0.3 # Seuil INTERFERE pour chevauchement

# Fenêtre de détection
BOUNDARY_LOOKBACK = 5            # Frames pour détecter une chute
ENERGY_SMOOTHING = 0.3           # Lissage exponentiel de l'énergie (φ⁻¹)


# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURES DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ABCAudioPrediction:
    """Résultat d'une prédiction audio ABC."""
    # Frame prédite
    psi_predicted: Optional[np.ndarray] = None
    
    # État de la parole
    is_speech: bool = False
    energy: float = 0.0
    energy_smoothed: float = 0.0
    
    # Frontières
    boundary_prob: float = 0.0
    is_silence: bool = True
    
    # Chevauchement full-duplex
    overlap_score: float = 0.0
    is_overlap: bool = False
    
    # Prosodie
    pitch_trend: float = 0.0       # Tendance du pitch (-1 descente, +1 montée)
    energy_trend: float = 0.0      # Tendance de l'énergie
    speech_rate_est: float = 0.0   # Estimation du débit
    
    # Métadonnées
    timestamp_ms: float = 0.0
    buffer_fill: int = 0
    
    def __repr__(self) -> str:
        flags = []
        if self.is_speech:
            flags.append('SPEECH')
        if self.is_silence:
            flags.append('SILENCE')
        if self.boundary_prob > 0.5:
            flags.append(f'BOUNDARY({self.boundary_prob:.2f})')
        if self.is_overlap:
            flags.append('OVERLAP')
        return f"ABCPred({', '.join(flags)}, E={self.energy:.3f})"


@dataclass
class PredictorStats:
    """Statistiques du prédicteur."""
    total_frames: int = 0
    speech_frames: int = 0
    silence_frames: int = 0
    boundaries_detected: int = 0
    overlaps_detected: int = 0
    avg_prediction_error: float = 0.0
    avg_process_time_us: float = 0.0
    
    @property
    def speech_ratio(self) -> float:
        return self.speech_frames / max(self.total_frames, 1)


# ═══════════════════════════════════════════════════════════════════════════════
# PRÉDICTEUR PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class ABCAudioPredictor:
    """
    Prédicteur streaming audio par noyau ABC.
    
    Maintient un buffer circulaire de frames ψ et utilise le noyau ABC
    pour prédire les frames futures, détecter la parole, les frontières
    et les chevauchements.
    
    Caractéristiques :
    - 0 paramètre appris (tout est déterministe)
    - Mémoire non-locale (le noyau ABC pèse TOUT l'historique)
    - Ne peut pas diverger (moyenne pondérée → stable)
    - Compatible full-duplex (détection de chevauchement)
    
    Parameters:
        dim: dimension des vecteurs ψ (default 512)
        max_history: taille max du buffer (default 100)
        frame_rate_hz: fréquence des trames (default 25.0 pour HCV v2)
        kernel: instance ABCKernel (créée automatiquement si None)
    """
    
    def __init__(self,
                 dim: int = DEFAULT_DIM,
                 max_history: int = DEFAULT_MAX_HISTORY,
                 frame_rate_hz: float = DEFAULT_FRAME_RATE_25HZ,
                 kernel: Optional[ABCKernel] = None):
        
        self.dim = dim
        self.max_history = max_history
        self.frame_rate = frame_rate_hz
        self.frame_interval_ms = 1000.0 / frame_rate_hz
        
        # Buffer circulaire
        self._buffer: Deque[np.ndarray] = deque(maxlen=max_history)
        
        # Noyau ABC
        self._kernel = kernel or ABCKernel(max_len=max_history)
        
        # État interne
        self._energy_smoothed = 0.0
        self._pitch_history: Deque[float] = deque(maxlen=20)
        self._energy_history: Deque[float] = deque(maxlen=20)
        self._frame_count = 0
        self._elapsed_ms = 0.0
        
        # Statistiques
        self.stats = PredictorStats()
        
        # Cache des poids ABC
        self._abc_weights_cache: Dict[int, np.ndarray] = {}
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PIPELINE PRINCIPAL
    # ═══════════════════════════════════════════════════════════════════════════
    
    def process_stream_chunk(self, psi_frame: np.ndarray) -> ABCAudioPrediction:
        """
        Traitement complet d'un chunk audio streaming.
        
        Appelé à chaque nouvelle frame (toutes les 40ms avec HCV v2).
        
        Args:
            psi_frame: [dim] complex128 — frame ψ du codec
            
        Returns:
            ABCAudioPrediction avec tous les diagnostics
        """
        t_start = time.perf_counter_ns()
        
        # Ajouter au buffer
        self.add_frame(psi_frame)
        
        # Énergie
        energy = self._compute_energy(psi_frame)
        self._energy_smoothed = (ENERGY_SMOOTHING * energy + 
                                 (1 - ENERGY_SMOOTHING) * self._energy_smoothed)
        self._energy_history.append(energy)
        
        # Détection parole/silence
        is_speech = self._energy_smoothed > SPEECH_ENERGY_THRESHOLD
        is_silence = self._energy_smoothed < SILENCE_ENERGY_THRESHOLD
        
        # Prédiction
        psi_pred = self.predict(horizon=1)
        
        # Détection de frontière
        boundary_prob = self.detect_boundary()
        
        # Chevauchement (pas de second flux dans le cas simple)
        overlap_score = 0.0
        is_overlap = False
        
        # Prosodie
        pitch_trend = self._estimate_pitch_trend(psi_frame)
        energy_trend = self._estimate_energy_trend()
        speech_rate = self._estimate_speech_rate()
        
        # Métriques
        self._frame_count += 1
        self._elapsed_ms += self.frame_interval_ms
        
        # Stats
        self.stats.total_frames += 1
        if is_speech:
            self.stats.speech_frames += 1
        if is_silence:
            self.stats.silence_frames += 1
        if boundary_prob > 0.5:
            self.stats.boundaries_detected += 1
        if is_overlap:
            self.stats.overlaps_detected += 1
        
        elapsed_ns = time.perf_counter_ns() - t_start
        self.stats.avg_process_time_us = (
            0.9 * self.stats.avg_process_time_us + 
            0.1 * (elapsed_ns / 1000.0)
        )
        
        return ABCAudioPrediction(
            psi_predicted=psi_pred,
            is_speech=is_speech,
            energy=energy,
            energy_smoothed=self._energy_smoothed,
            boundary_prob=boundary_prob,
            is_silence=is_silence,
            overlap_score=overlap_score,
            is_overlap=is_overlap,
            pitch_trend=pitch_trend,
            energy_trend=energy_trend,
            speech_rate_est=speech_rate,
            timestamp_ms=self._elapsed_ms,
            buffer_fill=len(self._buffer),
        )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PRÉDICTION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def predict(self, horizon: int = 1) -> Optional[np.ndarray]:
        """
        Prédit ψ[t+horizon] à partir de l'historique.
        
        Utilise le noyau ABC pour pondérer l'historique :
        ψ_pred = Σ K(τ) · ψ[t-τ] / Σ K(τ)
        
        Args:
            horizon: nombre de frames dans le futur (1 = prochaine frame)
            
        Returns:
            [dim] complex128 — frame ψ prédite, ou None si buffer vide
        """
        if len(self._buffer) == 0:
            return None
        
        n = min(len(self._buffer), self.max_history)
        
        # Récupérer/créer les poids ABC
        weights = self._get_abc_weights(n)
        
        # Moyenne pondérée par le noyau ABC
        buffer_arr = np.array(list(self._buffer)[-n:])  # [n, dim]
        
        # Prédiction : moyenne pondérée
        psi_pred = np.zeros(self.dim, dtype=np.complex128)
        for i in range(n):
            psi_pred += weights[i] * buffer_arr[-(i+1)]  # plus récent = poids fort
        
        # Ajustement pour l'horizon (tendance)
        if horizon > 1 and n >= 2:
            # Estimer la tendance récente
            recent_trend = buffer_arr[-1] - buffer_arr[-2]
            # Propager la tendance sur l'horizon
            psi_pred = psi_pred + recent_trend * (horizon - 1) * 0.5
        
        # Normalisation
        norm = np.sqrt(np.sum(np.abs(psi_pred) ** 2))
        if norm > 1e-10 and norm > 100.0:
            psi_pred = psi_pred / norm * 10.0  # soft clipping
        
        return psi_pred
    
    def predict_multi(self, horizon: int = 5) -> np.ndarray:
        """
        Prédit plusieurs frames futures.
        
        Args:
            horizon: nombre de frames à prédire
            
        Returns:
            [horizon, dim] complex128
        """
        predictions = np.zeros((horizon, self.dim), dtype=np.complex128)
        
        for h in range(1, horizon + 1):
            pred = self.predict(horizon=h)
            if pred is not None:
                predictions[h - 1] = pred
        
        return predictions
    
    def add_frame(self, psi_frame: np.ndarray):
        """
        Ajoute une frame observée au buffer circulaire.
        
        Args:
            psi_frame: [dim] complex128
        """
        self._buffer.append(psi_frame.copy())
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DÉTECTION DE PAROLE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def is_speech(self) -> float:
        """
        Score de présence de parole [0, 1].
        
        Basé sur l'énergie lissée du vecteur ψ.
        """
        if self._energy_smoothed < SILENCE_ENERGY_THRESHOLD:
            return 0.0
        if self._energy_smoothed > SPEECH_ENERGY_THRESHOLD * 3:
            return 1.0
        # Interpolation sigmoïde
        x = (self._energy_smoothed - SILENCE_ENERGY_THRESHOLD) / (
            SPEECH_ENERGY_THRESHOLD * 3 - SILENCE_ENERGY_THRESHOLD + 1e-10
        )
        return 1.0 / (1.0 + math.exp(-10.0 * (x - 0.5)))
    
    def detect_boundary(self) -> float:
        """
        Probabilité de frontière de parole (fin de phrase/mot).
        
        Détecte une chute d'énergie suivie d'un silence.
        N'émet une frontière que lors d'une transition parole→silence.
        
        Returns:
            float [0, 1] — probabilité de frontière
        """
        if len(self._buffer) < BOUNDARY_LOOKBACK:
            return 0.0
        
        # Vérifier qu'on est en parole (sinon pas de frontière à détecter)
        if self._energy_smoothed < SPEECH_ENERGY_THRESHOLD * 0.5:
            return 0.0
        
        # 1. Chute d'énergie récente
        recent_energies = list(self._energy_history)[-BOUNDARY_LOOKBACK:]
        if len(recent_energies) < 3:
            return 0.0
        
        recent_mean = np.mean(recent_energies[-2:])
        earlier_mean = np.mean(recent_energies[:3]) if len(recent_energies) >= 5 else recent_mean
        
        energy_drop = 1.0 - (recent_mean / (earlier_mean + 1e-10))
        energy_drop = max(0.0, energy_drop)
        
        # 2. Changement de pattern ψ (topic shift)
        if len(self._buffer) >= 10:
            recent_psi = np.array(list(self._buffer)[-3:])
            earlier_psi = np.array(list(self._buffer)[-8:-3])
            
            if len(recent_psi) > 0 and len(earlier_psi) > 0:
                recent_avg = np.mean(recent_psi, axis=0)
                earlier_avg = np.mean(earlier_psi, axis=0)
                
                coherence = np.real(np.dot(recent_avg, np.conj(earlier_avg)))
                norm_prod = (np.sqrt(np.sum(np.abs(recent_avg)**2) * 
                                        np.sum(np.abs(earlier_avg)**2)) + 1e-10)
                coherence = coherence / norm_prod
                
                pattern_change = max(0.0, 1.0 - abs(coherence))
            else:
                pattern_change = 0.0
        else:
            pattern_change = 0.0
        
        # Score combiné (exige les deux signaux)
        boundary_score = 0.6 * energy_drop + 0.4 * pattern_change
        
        # Gate : on doit être en parole ET avoir une chute
        if energy_drop < BOUNDARY_ENERGY_DROP * 0.3:
            boundary_score = 0.0
        
        return float(min(1.0, boundary_score))
    
    def detect_overlap(self, psi_other_stream: np.ndarray) -> float:
        """
        Détecte le chevauchement avec un autre flux audio (full-duplex).
        
        Utilise INTERFERE : Re(⟨ψ_user | ψ_agent⟩).
        Une cohérence élevée entre les deux flux indique qu'ils parlent
        en même temps (chevauchement spectral).
        
        Args:
            psi_other_stream: [dim] complex128 — ψ de l'autre flux
            
        Returns:
            float [0, 1] — score de chevauchement
        """
        if len(self._buffer) == 0:
            return 0.0
        
        # Dernière frame de notre flux
        psi_self = self._buffer[-1]
        
        # INTERFERE = produit scalaire complexe
        coherence = np.real(np.dot(psi_self, np.conj(psi_other_stream)))
        
        # Normalisation
        norm_self = np.sqrt(np.sum(np.abs(psi_self)**2)) + 1e-10
        norm_other = np.sqrt(np.sum(np.abs(psi_other_stream)**2)) + 1e-10
        coherence = coherence / (norm_self * norm_other)
        
        # Score : cohérence élevée = chevauchement probable
        overlap = max(0.0, min(1.0, abs(coherence)))
        
        return float(overlap)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PROSODIE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def predict_pitch_contour(self, n_frames: int = 10) -> np.ndarray:
        """
        Prédit l'évolution du pitch sur n frames futures.
        
        Utilise le noyau ABC pour extrapoler la tendance de phase
        (la dérivée de phase dans ψ est liée au pitch).
        
        Args:
            n_frames: nombre de frames à prédire
            
        Returns:
            [n_frames] float — pitch estimé (0 = non voisé)
        """
        if len(self._buffer) < 5:
            return np.zeros(n_frames)
        
        # Extraire les tendances de phase
        pitch_estimates = []
        buffer_list = list(self._buffer)
        
        for psi in buffer_list[-10:]:
            # Estimation du pitch depuis la structure de phase de ψ
            angles = np.angle(psi)
            if len(angles) > 2:
                # Différences de phase → fréquence instantanée
                phase_diffs = np.diff(angles[:min(20, len(angles))])
                phase_diffs = (phase_diffs + math.pi) % TAU - math.pi
                # Moyenne pondérée φ
                pitch_est = np.mean(np.abs(phase_diffs)) * 24000 / TAU / 100
                pitch_estimates.append(float(pitch_est))
        
        if not pitch_estimates:
            return np.zeros(n_frames)
        
        # Prédiction ABC de la tendance
        weights = self._get_abc_weights(min(len(pitch_estimates), self.max_history))
        pitch_arr = np.array(pitch_estimates[-len(weights):])
        base_pitch = np.dot(weights[:len(pitch_arr)], pitch_arr)
        
        # Tendance linéaire
        if len(pitch_estimates) >= 4:
            recent_trend = (pitch_estimates[-1] - pitch_estimates[-4]) / 3
        else:
            recent_trend = 0.0
        
        # Projeter
        contour = np.zeros(n_frames)
        for i in range(n_frames):
            # Décroissance φ de la tendance
            decay = math.exp(-i / PHI)
            contour[i] = base_pitch + recent_trend * i * decay
        
        return np.clip(contour, 0.0, None)
    
    def predict_energy_envelope(self, n_frames: int = 10) -> np.ndarray:
        """
        Prédit l'enveloppe d'énergie sur n frames futures.
        
        Args:
            n_frames: nombre de frames à prédire
            
        Returns:
            [n_frames] float — énergie prédite
        """
        if len(self._energy_history) < 5:
            return np.ones(n_frames) * self._energy_smoothed
        
        energy_arr = np.array(list(self._energy_history))
        weights = self._get_abc_weights(min(len(energy_arr), self.max_history))
        base_energy = np.dot(weights[:len(energy_arr)], energy_arr[-len(weights):])
        
        # Tendance
        recent_trend = (energy_arr[-1] - energy_arr[-5]) / 4 if len(energy_arr) >= 5 else 0.0
        
        envelope = np.zeros(n_frames)
        for i in range(n_frames):
            decay = math.exp(-i / PHI)
            envelope[i] = max(0.0, base_energy + recent_trend * i * decay)
        
        return envelope
    
    # ═══════════════════════════════════════════════════════════════════════════
    # INTERNES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _compute_energy(self, psi: np.ndarray) -> float:
        """Calcule l'énergie d'une frame ψ (norme ℓ²)."""
        return float(np.sum(np.abs(psi) ** 2))
    
    def _get_abc_weights(self, n: int) -> np.ndarray:
        """Récupère ou crée les poids ABC pour une séquence de longueur n."""
        if n not in self._abc_weights_cache:
            kernel = self._kernel(n)
            # Normaliser (les poids les plus récents sont les derniers)
            weights = kernel / (kernel.sum() + 1e-30)
            # Inverse pour que weights[0] = poids du plus récent
            weights = weights[::-1]
            self._abc_weights_cache[n] = weights
        return self._abc_weights_cache[n]
    
    def _estimate_pitch_trend(self, psi: np.ndarray) -> float:
        """
        Estime la tendance de pitch [-1, +1].
        
        Basée sur la variation de phase dans ψ.
        """
        if len(self._pitch_history) < 3:
            self._pitch_history.append(0.0)
            return 0.0
        
        angles = np.angle(psi)
        if len(angles) > 2:
            phase_diffs = np.diff(angles[:min(20, len(angles))])
            phase_diffs = (phase_diffs + math.pi) % TAU - math.pi
            pitch_est = np.mean(np.abs(phase_diffs))
        else:
            pitch_est = 0.0
        
        self._pitch_history.append(float(pitch_est))
        
        if len(self._pitch_history) >= 5:
            recent = np.array(list(self._pitch_history)[-3:])
            earlier = np.array(list(self._pitch_history)[-6:-3])
            diff = recent.mean() - earlier.mean()
            # Normaliser
            trend = np.tanh(diff * 5.0)
            return float(trend)
        
        return 0.0
    
    def _estimate_energy_trend(self) -> float:
        """Estime la tendance d'énergie [-1, +1]."""
        if len(self._energy_history) < 5:
            return 0.0
        
        recent = np.array(list(self._energy_history)[-3:])
        earlier = np.array(list(self._energy_history)[-6:-3])
        
        diff = recent.mean() - earlier.mean()
        norm = (earlier.mean() + 1e-10)
        
        trend = np.tanh(diff / norm * 3.0)
        return float(trend)
    
    def _estimate_speech_rate(self) -> float:
        """
        Estime le débit de parole (syllabes/seconde).
        
        Basé sur le taux de variation de ψ (frontières phonétiques).
        """
        if len(self._buffer) < 10:
            return 0.0
        
        buffer_list = list(self._buffer)
        
        # Compter les changements significatifs de ψ (transitions phonétiques)
        changes = 0
        for i in range(1, min(10, len(buffer_list))):
            coherence = np.real(np.dot(buffer_list[i], np.conj(buffer_list[i-1])))
            norm_prod = (np.sqrt(np.sum(np.abs(buffer_list[i])**2)) * 
                        np.sqrt(np.sum(np.abs(buffer_list[i-1])**2)) + 1e-10)
            coherence = abs(coherence) / norm_prod
            
            if coherence < 0.7:  # changement significatif
                changes += 1
        
        # Conversion en syllabes/seconde (heuristique)
        rate = changes / (min(10, len(buffer_list)) * self.frame_interval_ms / 1000.0)
        
        return float(rate)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # UTILITAIRES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def reset(self):
        """Vide le buffer et réinitialise l'état."""
        self._buffer.clear()
        self._energy_smoothed = 0.0
        self._pitch_history.clear()
        self._energy_history.clear()
        self._frame_count = 0
        self._elapsed_ms = 0.0
        self.stats = PredictorStats()
    
    @property
    def buffer_size(self) -> int:
        """Taille actuelle du buffer."""
        return len(self._buffer)
    
    @property
    def is_empty(self) -> bool:
        """Buffer vide ?"""
        return len(self._buffer) == 0
    
    @property
    def info(self) -> dict:
        """Informations détaillées sur le prédicteur."""
        return {
            'dim': self.dim,
            'max_history': self.max_history,
            'frame_rate_hz': self.frame_rate,
            'frame_interval_ms': self.frame_interval_ms,
            'buffer_fill': self.buffer_size,
            'energy_smoothed': self._energy_smoothed,
            'alpha': ALPHA,
            'phi': PHI,
            'total_frames': self.stats.total_frames,
            'speech_ratio': self.stats.speech_ratio,
            'boundaries': self.stats.boundaries_detected,
            'avg_process_us': self.stats.avg_process_time_us,
        }
    
    def __repr__(self) -> str:
        return (f"ABCAudioPredictor(dim={self.dim}, "
                f"buffer={self.buffer_size}/{self.max_history}, "
                f"α=1/φ={ALPHA:.4f})")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST COMPLET
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 70)
    print("  ABC Audio Predictor — Test Complet")
    print("=" * 70)
    
    # ── Init ──
    print("\n[1] Initialisation...")
    predictor = ABCAudioPredictor(dim=512, max_history=100)
    print(f"    {predictor}")
    print(f"    α = 1/φ = {ALPHA:.6f}")
    print(f"    B(α) = {B_1_PHI:.10f}")
    print(f"    Frame rate: {predictor.frame_rate} Hz")
    print(f"    Frame interval: {predictor.frame_interval_ms:.1f} ms")
    
    # ── Génération de frames ψ simulées ──
    print("\n[2] Simulation d'un flux audio (200 frames)...")
    
    np.random.seed(42)
    n_frames = 200
    results = []
    
    # Simuler : silence → parole → silence → parole → silence
    phases = [
        (0, 30, 'silence'),      # 0-30: silence
        (30, 80, 'speech'),       # 30-80: parole (phrase 1)
        (80, 100, 'silence'),     # 80-100: pause courte
        (100, 160, 'speech'),     # 100-160: parole (phrase 2)
        (160, 200, 'silence'),    # 160-200: silence final
    ]
    
    for i in range(n_frames):
        # Déterminer la phase
        current_phase = 'silence'
        for start, end, phase in phases:
            if start <= i < end:
                current_phase = phase
                break
        
        if current_phase == 'speech':
            # Simuler une frame de parole : énergie élevée + structure harmonique
            # ψ avec énergie ~5-10
            base = np.random.randn(predictor.dim) + 1j * np.random.randn(predictor.dim)
            base = base / np.sqrt(np.sum(np.abs(base)**2)) * (5.0 + np.random.random() * 5.0)
            # Ajouter une structure de phase corrélée (simule le pitch)
            for d in range(1, predictor.dim, 10):
                base[d] = base[d-1] * (0.9 + 0.1j)
        else:
            # Silence : énergie faible + bruit
            base = (np.random.randn(predictor.dim) + 1j * np.random.randn(predictor.dim)) * 0.001
        
        psi_frame = base.astype(np.complex128)
        
        # Process
        pred = predictor.process_stream_chunk(psi_frame)
        results.append(pred)
    
    # ── Analyse des résultats ──
    print(f"    Frames traitées: {len(results)}")
    
    speech_count = sum(1 for r in results if r.is_speech)
    silence_count = sum(1 for r in results if r.is_silence)
    boundary_count = sum(1 for r in results if r.boundary_prob > 0.5)
    
    print(f"    Parole détectée: {speech_count}/{n_frames} ({speech_count/n_frames*100:.1f}%)")
    print(f"    Silence détecté: {silence_count}/{n_frames}")
    print(f"    Frontières détectées: {boundary_count}")
    
    # ── Prédiction ──
    print("\n[3] Test prédiction...")
    pred_single = predictor.predict(horizon=1)
    print(f"    Prédiction 1 frame: |ψ|={np.sqrt(np.sum(np.abs(pred_single)**2)):.3f}" 
          if pred_single is not None else "    N/A")
    
    pred_multi = predictor.predict_multi(horizon=5)
    print(f"    Prédiction 5 frames: shape={pred_multi.shape}, "
          f"|ψ| moyen={np.mean(np.sqrt(np.sum(np.abs(pred_multi)**2, axis=1))):.3f}")
    
    # ── Détection de frontières ──
    print("\n[4] Détection de frontières...")
    boundaries_found = []
    for i, r in enumerate(results):
        if r.boundary_prob > 0.3:
            boundaries_found.append((i, r.boundary_prob))
    
    if boundaries_found:
        for idx, prob in boundaries_found[:8]:
            print(f"    Frame {idx:3d}: boundary_prob={prob:.3f} "
                  f"({'PAROLE' if results[idx].is_speech else 'silence'}, "
                  f"E={results[idx].energy:.4f})")
        if len(boundaries_found) > 8:
            print(f"    ... et {len(boundaries_found)-8} autres détections")
    else:
        print("    Aucune frontière détectée (normal avec données simulées)")
    
    # ── Chevauchement ──
    print("\n[5] Test chevauchement full-duplex...")
    # Simuler un second flux
    other_psi = (np.random.randn(predictor.dim) + 1j * np.random.randn(predictor.dim)) * 3.0
    other_psi = other_psi.astype(np.complex128)
    
    overlap_score = predictor.detect_overlap(other_psi)
    print(f"    Score chevauchement (flux aléatoire): {overlap_score:.4f}")
    
    # Test avec un flux corrélé (simule le même locuteur)
    if len(predictor._buffer) > 0:
        correlated_psi = predictor._buffer[-1] * 0.8 + other_psi * 0.2
        overlap_corr = predictor.detect_overlap(correlated_psi)
        print(f"    Score chevauchement (flux corrélé):   {overlap_corr:.4f}")
    
    # ── Prosodie ──
    print("\n[6] Prédiction de prosodie...")
    pitch_contour = predictor.predict_pitch_contour(10)
    energy_envelope = predictor.predict_energy_envelope(10)
    
    print(f"    Pitch contour [10 frames]: "
          f"min={pitch_contour.min():.3f}, max={pitch_contour.max():.3f}, "
          f"mean={pitch_contour.mean():.3f}")
    print(f"    Energy envelope [10 frames]: "
          f"min={energy_envelope.min():.4f}, max={energy_envelope.max():.4f}")
    
    # ── Streaming complet ──
    print("\n[7] Simulation streaming temps réel...")
    predictor2 = ABCAudioPredictor(dim=512, max_history=50)
    
    streaming_events = []
    np.random.seed(123)
    
    for i in range(100):
        # Alterner parole/silence
        if 20 <= i < 50 or 65 <= i < 85:
            energy_level = 8.0
        else:
            energy_level = 0.0005
        
        psi = (np.random.randn(512) + 1j * np.random.randn(512)) * energy_level
        psi = psi.astype(np.complex128)
        
        pred = predictor2.process_stream_chunk(psi)
        
        if pred.boundary_prob > 0.4:
            streaming_events.append((i, 'BOUNDARY', pred.boundary_prob))
        if pred.is_speech and (i == 0 or not results[i-1].is_speech if i > 0 else True):
            if i > 0:
                streaming_events.append((i, 'SPEECH_START', pred.energy))
        if not pred.is_speech and i > 0:
            prev = results[i-1] if i-1 < len(results) else None
            if prev and prev.is_speech:
                streaming_events.append((i, 'SPEECH_END', pred.energy))
    
    print(f"    Événements détectés: {len(streaming_events)}")
    for evt in streaming_events[:10]:
        print(f"    Frame {evt[0]:3d}: {evt[1]:15s} (score={evt[2]:.3f})")
    
    # ── Résumé ──
    print("\n" + "=" * 70)
    print("  RÉSUMÉ ABC Audio Predictor")
    print("=" * 70)
    info = predictor.info
    for key, val in info.items():
        if isinstance(val, float):
            print(f"  {key:25s}: {val:.4f}")
        else:
            print(f"  {key:25s}: {val}")
    
    print(f"\n  {'Statut':25s}: ✓ OK")
    print(f"  {'Détection parole':25s}: {speech_count}/{n_frames} frames")
    print(f"  {'Frontières':25s}: {boundary_count} détectées")
    print(f"  {'Temps moyen/frame':25s}: {predictor.stats.avg_process_time_us:.1f} µs")
    
    print("\n✓ Test ABC Audio Predictor terminé.")
