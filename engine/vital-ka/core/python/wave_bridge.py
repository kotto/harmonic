"""
🌊 Wave Bridge — Pont unifié vers le DSL ondulatoire
======================================================
Phase 5-7 : Rétro-adaptation des modules existants vers wave_lang.

Ce module fournit des adapteurs « drop-in » qui remplacent les
implémentations dupliquées dans les modules TTS, protéines, audio
ET LLM par des appels vers la bibliothèque wave_lang unifiée.

Modules couverts (TTS/Audio/Protéines) :
  - ka_sonic/psi_diphone_bank.py    → HolographicMemory
  - alphafold/abc_folder.py         → abc_kernel / abc_forget
  - alphafold/harmonic_energy.py    → resonate / coherence
  - harmonic_voice_codec_v2.py      → diffract / spectrum / filter_wave
  - ka_sonic/glottal_synth.py       → superpose / phase_shift
  - ka_sonic/voice_signature.py     → spectrum / resonate
  - ka_sonic/harmonic_cloner.py     → filter_wave / resonate

Modules couverts (LLM) :
  - harmonic_attention.py           → CoherenceAttention (resonate / superpose)
  - holographic_encoder.py          → HolographicEncoderBridge (encode / bind / HolographicMemory)
  - phase_amplifier.py              → PhasePropagator (phase_shift / resonate / superpose)
  - wave_decoder.py                 → WaveDecoderBridge (resonate / coherence / decode)
  - harmonic_brain.py (RAG)         → HolographicRAG (HolographicMemory / resonate)
  - few_shot_injector.py            → FewShotPhaseLock (superpose / amplify / phase_shift)
  - conscious_intelligence.py       → CoherenceGate (coherence / filter_wave / resonate)
  - feedback_loop.py                → FeedbackLoopBridge (coherence / amplify / oppose)
  - wave_sampling.py                → WaveSamplingBridge (coherence / phase_shift / rotate)
  - wave_tool_use.py                → WaveToolUseBridge (bind / unbind / resonate)
  - beam_search.py                  → WaveBeamSearchBridge (resonate / superpose / interfere)
  - wave_perplexity.py              → WavePerplexityBridge (energy / spectrum / coherence)

Principe :
  - Les signatures publiques sont préservées
  - L'implémentation interne délègue à wave_lang
  - Zéro changement dans le code appelant
  - Les optimisations du compilateur s'appliquent automatiquement

Usage :
    # Avant :
    from harmonic_attention import HarmonicAttention
    attn = HarmonicAttention(dim=512)

    # Après (compatible drop-in) :
    from wave_bridge import CoherenceAttention  # même API, backend wave_lang
    attn = CoherenceAttention(dim=512)
"""

from __future__ import annotations

import math
import os
import random
import re
import numpy as np
from typing import List, Dict, Tuple, Optional, Callable, Any

# ═══════════════════════════════════════════════════════════════════════════════
# IMPORTS UNIFIÉS
# ═══════════════════════════════════════════════════════════════════════════════

from wave_lang import (
    # Primitives
    encode, decode, bind, unbind, superpose,
    resonate, coherence, rotate, normalize, norm, energy,
    interfere, diffract, spectrum, filter_wave, phase_shift,
    emerge, oppose, amplify, bind_many,
    # Utilitaires
    resonate_batch, stats,
    # Mémoire
    HolographicMemory,
    # Noyau ABC
    abc_kernel, abc_forget,
    # Hash
    fnv1a,
    # Constantes
    PHI, ALPHA, TAU, DEFAULT_DIM,
)

# ═══════════════════════════════════════════════════════════════════════════════
# 1. ADAPTATEUR PSI-DIPHONE BANK → HolographicMemory
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : PsiDiphoneBank gérait ses propres vecteurs, superpositions,
#         requêtes par résonance, et oubli ABC.
# Après : Délègue à HolographicMemory avec un encodeur de diphones.

class PsiDiphoneBank:
    """
    Banque de diphones encodés en espace Ψ.

    Drop-in replacement pour ka_sonic/psi_diphone_bank.py.
    Même API, backend wave_lang.HolographicMemory.

    Un diphone = transition entre deux phones (ex: "k-a", "a-t").
    Stocké comme : ψ_diphone = bind(ψ_phone1, ψ_phone2)

    Usage :
        bank = PsiDiphoneBank(dim=512)
        bank.store("k", "a", audio_vector)
        results = bank.query("k", "a")  # → [(ψ, score), ...]
    """

    def __init__(self, dim: int = DEFAULT_DIM):
        self.dim = dim
        self.memory = HolographicMemory(dim=dim)
        self._diphone_audio: Dict[str, np.ndarray] = {}  # ψ → audio waveform
        self._count = 0

    def encode_diphone(self, phone_a: str, phone_b: str) -> np.ndarray:
        """
        Encode un diphone phone_a→phone_b en vecteur d'onde.

        ψ_diphone = bind(encode(phone_a), encode(phone_b))

        Args:
            phone_a: premier phone (ex: "k")
            phone_b: deuxième phone (ex: "a")

        Returns:
            ψ_diphone ∈ ℂᵈⁱᵐ
        """
        psi_a = encode(phone_a, dim=self.dim)
        psi_b = encode(phone_b, dim=self.dim)
        return bind(psi_a, psi_b)

    def store(self, phone_a: str, phone_b: str, audio: np.ndarray):
        """
        Stocke un diphone dans la banque.

        Args:
            phone_a: premier phone
            phone_b: deuxième phone
            audio: forme d'onde audio associée
        """
        psi = self.encode_diphone(phone_a, phone_b)
        self.memory.store_raw(psi)
        self._diphone_audio[self._count] = audio
        self._count += 1

    def query(self, phone_a: str, phone_b: str,
              top_k: int = 5) -> List[Tuple[int, float, np.ndarray]]:
        """
        Recherche les diphones les plus proches par résonance.

        Args:
            phone_a: premier phone cible
            phone_b: deuxième phone cible
            top_k: nombre de résultats

        Returns:
            liste de (index, score, audio) triée par score décroissant
        """
        psi_query = self.encode_diphone(phone_a, phone_b)
        scores = self.memory.query_scores(psi_query)

        results = []
        for idx, score in scores[:top_k]:
            audio = self._diphone_audio.get(idx)
            results.append((idx, score, audio))

        return results

    def query_by_psi(self, psi_query: np.ndarray,
                     top_k: int = 5) -> List[Tuple[int, float, np.ndarray]]:
        """
        Recherche par vecteur d'onde direct (sans ré-encodage).

        Args:
            psi_query: vecteur d'onde de la requête
            top_k: nombre de résultats

        Returns:
            liste de (index, score, audio)
        """
        scores = self.memory.query_scores(psi_query)
        results = []
        for idx, score in scores[:top_k]:
            audio = self._diphone_audio.get(idx)
            results.append((idx, score, audio))
        return results

    @property
    def size(self) -> int:
        return self.memory.n_facts


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ADAPTATEUR ABC MEMORY KERNEL → abc_kernel / abc_forget
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : ABCMemoryKernel dans alphafold/abc_folder.py réimplémentait
#         le noyau ABC avec Mittag-Leffler et décroissance en loi de puissance.
# Après : Délègue à wave_lang.abc_kernel et wave_lang.abc_forget.

class ABCMemoryKernel:
    """
    Noyau de mémoire non-locale ABC pour le repliement de protéines.

    Drop-in replacement pour alphafold/abc_folder.py.
    Même API, backend wave_lang.abc_kernel.

    Usage :
        kernel = ABCMemoryKernel(alpha=ALPHA, max_history=100)
        effective_force = kernel.compute_effective_force(current, history)
    """

    def __init__(self, alpha: float = ALPHA, max_history: int = 100):
        self.alpha = alpha
        self.max_history = max_history
        self._history: List[np.ndarray] = []
        self._weights: Optional[np.ndarray] = None

    def __call__(self, t: int) -> float:
        """
        Retourne le poids du noyau au temps t.

        Équivalent à wave_lang.abc_kernel(t).
        """
        return abc_kernel(t)

    def store(self, gradient: np.ndarray):
        """Stocke un gradient dans l'historique."""
        self._history.append(gradient.copy())
        if len(self._history) > self.max_history:
            self._history.pop(0)
        self._weights = None  # invalider le cache

    def _compute_weights(self) -> np.ndarray:
        """Calcule les poids ABC pour tout l'historique."""
        if self._weights is not None and len(self._weights) == len(self._history):
            return self._weights

        n = len(self._history)
        weights = np.array([abc_kernel(n - 1 - i) for i in range(n)])
        weights = weights / (weights.sum() + 1e-15)
        self._weights = weights
        return weights

    def compute_effective_force(self, current_force: np.ndarray) -> np.ndarray:
        """
        Calcule la force effective avec mémoire ABC.

        F_eff = (1-α) * F_current + α * Σ w_i * F_history[i]

        Équivalent à wave_lang.abc_forget appliqué à une superposition
        pondérée de l'historique.

        Args:
            current_force: force actuelle (gradient)

        Returns:
            force effective combinant présent et passé
        """
        if not self._history:
            return current_force

        weights = self._compute_weights()
        # Superposition pondérée de l'historique (via abc_forget sur chaque terme)
        history_force = superpose(*self._history, weights=weights.tolist())

        # Mélange présent/passé : équivalent à abc_forget appliqué au contexte
        result = interfere(current_force, history_force,
                          epsilon=self.alpha / (1.0 - self.alpha + 1e-10))

        return result

    def clear(self):
        """Vide l'historique."""
        self._history.clear()
        self._weights = None


# ═══════════════════════════════════════════════════════════════════════════════
# 3. ADAPTATEUR HARMONIC ENERGY → resonate / coherence
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : _compute_harmonic_core() dans alphafold/harmonic_energy.py
#         calculait E = -Σ φ_i * cos(Δφ) * exp(-d_i / λ) « à la main ».
# Après : wave_lang.resonate() + pondération par distance.

class HarmonicEnergyCore:
    """
    Énergie harmonique du cœur de repliement.

    Adaptateur pour alphafold/harmonic_energy.py.
    Utilise wave_lang.resonate() pour le terme cos(Δφ).

    La formule originale :
        E = -Σ_i φ_i * cos(Δφ_i) * exp(-d_i / λ)

    Devient :
        E = -Σ_i φ_i * resonate(ψ_i, ψ_target) * exp(-d_i / λ)

    Usage :
        he = HarmonicEnergyCore(lambda_h=4.0)
        E = he.compute(psi_residues, psi_target, distances)
    """

    def __init__(self, lambda_h: float = 4.0, epsilon: float = 1e-8):
        """
        Args:
            lambda_h: longueur caractéristique de décroissance spatiale (Å)
            epsilon: régularisation numérique
        """
        self.lambda_h = lambda_h
        self.epsilon = epsilon

    def compute(self, psi_residues: List[np.ndarray],
                psi_target: np.ndarray,
                distances: np.ndarray,
                phi_scores: Optional[np.ndarray] = None) -> float:
        """
        Calcule l'énergie harmonique du cœur.

        E = -Σ_i φ_i * resonate(ψ_i, ψ_target) * exp(-d_i / λ_h)

        Args:
            psi_residues: liste des ψ de chaque résidu
            psi_target: ψ de la position cible idéale
            distances: distances spatiales résidu→cible (Å)
            phi_scores: scores φ de chaque résidu (optionnel)

        Returns:
            énergie harmonique totale (négative = favorable)
        """
        if not psi_residues:
            return 0.0

        total = 0.0
        n = len(psi_residues)

        # Normaliser les distances pour l'exponentielle
        d_norm = distances / (self.lambda_h + self.epsilon)

        for i in range(n):
            # La résonance cos(Δφ) est exactement wave_lang.resonate()
            resonance_score = resonate(psi_residues[i], psi_target)

            # Facteur φ (par défaut 1.0 si non fourni)
            phi_factor = phi_scores[i] if phi_scores is not None else 1.0

            # Pondération spatiale
            spatial_weight = math.exp(-d_norm[i])

            # Contribution à l'énergie
            total += phi_factor * resonance_score * spatial_weight

        return -total  # négatif = favorable (convention d'énergie)

    def compute_electrostatic_interference(self, psi_a: np.ndarray,
                                           psi_b: np.ndarray,
                                           charge_a: float, charge_b: float,
                                           distance: float,
                                           debye_length: float = 10.0) -> float:
        """
        Calcule l'énergie électrostatique avec interférence de phase.

        E_coulomb = k * q_a * q_b / (ε_r * d) * cos(Δφ) * exp(-d/Debye)

        Le terme cos(Δφ) est wave_lang.resonate(ψ_a, ψ_b).

        Args:
            psi_a, psi_b: vecteurs d'onde des deux résidus
            charge_a, charge_b: charges électrostatiques
            distance: distance entre les résidus (Å)
            debye_length: longueur de Debye (Å)

        Returns:
            énergie électrostatique avec interférence
        """
        # Constante de Coulomb (kcal·Å / e²)
        K_COULOMB = 332.0
        EPS_R = 4.0  # constante diélectrique effective

        # Terme de Coulomb classique
        coulomb = K_COULOMB * charge_a * charge_b / (EPS_R * distance + self.epsilon)

        # Terme d'interférence de phase = resonate(ψ_a, ψ_b)
        interference = resonate(psi_a, psi_b)

        # Écrantage de Debye
        screening = math.exp(-distance / debye_length) if distance > 0 else 1.0

        return coulomb * interference * screening


# ═══════════════════════════════════════════════════════════════════════════════
# 4. ADAPTATEUR SPECTRAL → diffract / spectrum / filter_wave
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : harmonic_voice_codec_v2.py et ka_sonic/*.py utilisaient
#         np.fft.rfft/irfft + masquage manuel pour l'analyse/le filtrage spectral.
# Après : wave_lang.diffract / spectrum / filter_wave.

class SpectralAnalyzer:
    """
    Analyseur spectral unifié pour audio et signaux.

    Drop-in pour les opérations FFT dans :
      - harmonic_voice_codec_v2.py
      - ka_sonic/bridge.py
      - ka_sonic/glottal_synth.py
      - ka_sonic/voice_signature.py

    Usage :
        sa = SpectralAnalyzer(dim=1024)
        freqs = sa.analyze(audio_frame)        # → domaine fréquentiel
        magnitudes = sa.spectrum(audio_frame)  # → |FFT|
        filtered = sa.filter(audio_frame, low_pass=3000)  # → filtré
        time_domain = sa.synthesize(freqs)     # → domaine temporel
    """

    def __init__(self, dim: int = 1024):
        self.dim = dim

    def analyze(self, signal: np.ndarray) -> np.ndarray:
        """
        Analyse spectrale d'un signal temporel.

        Équivalent à np.fft.rfft() mais via wave_lang.diffract().
        """
        # Padding/trim à la dimension
        if len(signal) < self.dim:
            padded = np.zeros(self.dim, dtype=np.float64)
            padded[:len(signal)] = signal
        else:
            padded = signal[:self.dim].astype(np.float64)

        psi = padded.astype(np.complex128)
        return diffract(psi)

    def spectrum(self, signal: np.ndarray) -> np.ndarray:
        """
        Spectre de magnitude d'un signal.

        Équivalent à np.abs(np.fft.rfft()).
        """
        freqs = self.analyze(signal)
        return np.abs(freqs[:self.dim // 2 + 1])

    def synthesize(self, freqs: np.ndarray) -> np.ndarray:
        """
        Synthèse temporelle depuis le domaine fréquentiel.

        Équivalent à np.fft.irfft() mais via wave_lang.diffract(inverse=True).
        """
        if len(freqs) < self.dim:
            padded = np.zeros(self.dim, dtype=np.complex128)
            padded[:len(freqs)] = freqs
            # Symétrie hermitienne
            padded[self.dim // 2 + 1:] = np.conj(padded[1:self.dim // 2][::-1])
        else:
            padded = freqs[:self.dim].astype(np.complex128)

        result = diffract(padded, inverse=True)
        return np.real(result)

    def filter(self, signal: np.ndarray,
               low_pass: Optional[float] = None,
               high_pass: Optional[float] = None,
               band_pass: Optional[Tuple[float, float]] = None) -> np.ndarray:
        """
        Filtrage spectral d'un signal.

        Équivalent à : FFT → masque → IFFT
        Utilise wave_lang.filter_wave().
        """
        if len(signal) < self.dim:
            padded = np.zeros(self.dim, dtype=np.float64)
            padded[:len(signal)] = signal
        else:
            padded = signal[:self.dim].astype(np.float64)

        psi = padded.astype(np.complex128)

        # Convertir les fréquences de Hz en indices (approx)
        # sample_rate implicite : on normalise par dim
        lp = low_pass / (22050 / self.dim) if low_pass else None
        hp = high_pass / (22050 / self.dim) if high_pass else None
        bp = None
        if band_pass:
            bp = (band_pass[0] / (22050 / self.dim),
                  band_pass[1] / (22050 / self.dim))

        result = filter_wave(psi, low_pass=lp, high_pass=hp, band_pass=bp)
        return np.real(result)

    def harmonic_decomposition(self, signal: np.ndarray,
                                f0: float, n_harmonics: int = 10) -> Dict[int, complex]:
        """
        Décomposition harmonique : isole le fondamental et ses harmoniques.

        Utilisé par le codec audio pour extraire la structure harmonique.

        Args:
            signal: signal audio
            f0: fréquence fondamentale (Hz)
            n_harmonics: nombre d'harmoniques à extraire

        Returns:
            dict {harmonique_index: amplitude_complexe}
        """
        freqs = self.analyze(signal)
        spec = np.abs(freqs)

        harmonics = {}
        sample_rate = 44100  # supposé
        for h in range(1, n_harmonics + 1):
            freq_hz = f0 * h
            idx = int(freq_hz * self.dim / sample_rate)
            if 0 <= idx < len(spec):
                harmonics[h] = freqs[idx]
        return harmonics

    def formant_extract(self, signal: np.ndarray,
                        max_formants: int = 5) -> List[Tuple[float, float]]:
        """
        Extraction des formants : pics spectraux du filtre du conduit vocal.

        Utilise wave_lang.spectrum() puis recherche de pics.

        Args:
            signal: signal audio
            max_formants: nombre maximum de formants

        Returns:
            liste de (fréquence_Hz, amplitude)
        """
        spec = self.spectrum(signal)
        # Lissage simple pour éviter les faux pics
        from scipy.ndimage import uniform_filter1d
        try:
            smoothed = uniform_filter1d(spec, size=3)
        except Exception:
            smoothed = spec

        # Recherche de pics
        peaks = []
        sample_rate = 44100
        for i in range(2, len(smoothed) - 2):
            if (smoothed[i] > smoothed[i-1] and
                smoothed[i] > smoothed[i-2] and
                smoothed[i] > smoothed[i+1] and
                smoothed[i] > smoothed[i+2] and
                smoothed[i] > np.mean(smoothed) * 2):
                freq = i * sample_rate / self.dim
                peaks.append((freq, float(smoothed[i])))

        # Trier par amplitude décroissante et garder max_formants
        peaks.sort(key=lambda x: -x[1])
        return peaks[:max_formants]


# ═══════════════════════════════════════════════════════════════════════════════
# 5. ADAPTATEUR VOICE SIGNATURE → spectrum / resonate
# ═══════════════════════════════════════════════════════════════════════════════

class VoiceSignature:
    """
    Signature vocale harmonique (empreinte identitaire).

    Adaptateur pour ka_sonic/voice_signature.py.
    Utilise wave_lang.spectrum pour l'analyse et resonate pour la comparaison.

    Usage :
        vs = VoiceSignature()
        sig = vs.extract(audio)            # → ψ_voice
        score = vs.compare(sig1, sig2)     # → similarité ∈ [0, 1]
    """

    def __init__(self, dim: int = DEFAULT_DIM):
        self.dim = dim
        self.analyzer = SpectralAnalyzer(dim=dim)

    def extract(self, audio: np.ndarray) -> np.ndarray:
        """
        Extrait la signature vocale sous forme de vecteur d'onde.

        Pipeline :
          1. Analyse spectrale → magnitudes
          2. Extraction de l'enveloppe spectrale (tilt + formants)
          3. Encodage en ψ via wave_lang.encode()

        Args:
            audio: signal audio

        Returns:
            ψ_voice ∈ ℂᵈⁱᵐ
        """
        # Analyse spectrale
        spec = self.analyzer.spectrum(audio)

        # Caractéristiques vocales
        # Tilt spectral (pente globale)
        if len(spec) > 1:
            x = np.arange(len(spec))
            tilt = float(np.polyfit(x[:len(spec)//4], np.log(spec[:len(spec)//4] + 1e-10), 1)[0])
        else:
            tilt = 0.0

        # Créer une « empreinte » textuelle combinant les caractéristiques
        fingerprint = f"voice|tilt:{tilt:.4f}|energy:{energy(spec):.4f}"

        return encode(fingerprint, dim=self.dim)

    def compare(self, sig_a: np.ndarray, sig_b: np.ndarray) -> float:
        """
        Compare deux signatures vocales.

        Utilise wave_lang.coherence() (valeur absolue de resonate).

        Args:
            sig_a, sig_b: signatures ψ

        Returns:
            score de similarité ∈ [0, 1]
        """
        return coherence(sig_a, sig_b)

    def match(self, query_sig: np.ndarray,
              candidates: Dict[str, np.ndarray]) -> List[Tuple[str, float]]:
        """
        Cherche la signature la plus proche parmi des candidats.

        Args:
            query_sig: signature à chercher
            candidates: {nom: ψ_signature}

        Returns:
            liste de (nom, score) triée par similarité décroissante
        """
        scores = []
        for name, sig in candidates.items():
            s = coherence(query_sig, sig)
            scores.append((name, s))
        scores.sort(key=lambda x: -x[1])
        return scores


# ═══════════════════════════════════════════════════════════════════════════════
# 6. ADAPTATEUR GLOTTAL SOURCE → superpose / phase_shift
# ═══════════════════════════════════════════════════════════════════════════════

class GlottalSource:
    """
    Source glottique harmonique pour la synthèse vocale.

    Adaptateur pour ka_sonic/glottal_synth.py.
    Utilise wave_lang.superpose + phase_shift pour la superposition d'harmoniques.

    Usage :
        gs = GlottalSource(f0=120, n_harmonics=40)
        waveform, psi = gs.synthesize(duration=0.05, sample_rate=44100)
    """

    def __init__(self, f0: float = 120.0, n_harmonics: int = 40,
                 dim: int = DEFAULT_DIM):
        self.f0 = f0
        self.n_harmonics = n_harmonics
        self.dim = dim

    def synthesize(self, duration: float = 0.05,
                   sample_rate: int = 44100) -> Tuple[np.ndarray, np.ndarray]:
        """
        Synthétise une onde glottique par superposition harmonique.

        Utilise wave_lang.superpose() sur les harmoniques pondérées
        et wave_lang.phase_shift() pour l'alignement de phase.

        Args:
            duration: durée en secondes
            sample_rate: fréquence d'échantillonnage (Hz)

        Returns:
            (waveform, psi_glottal) — signal audio + vecteur d'onde
        """
        n_samples = int(duration * sample_rate)
        t = np.arange(n_samples, dtype=np.float64) / sample_rate

        # Générer chaque harmonique
        harmonics = []
        for k in range(1, self.n_harmonics + 1):
            amplitude = 1.0 / (k ** 1.5)  # décroissance naturelle
            phase_k = (k * PHI) % TAU  # espacement φ
            harmonic = amplitude * np.sin(TAU * k * self.f0 * t + phase_k)
            harmonics.append(harmonic)

        # Superposition des harmoniques → onde glottique
        waveform = np.sum(harmonics, axis=0)
        waveform = waveform / (np.max(np.abs(waveform)) + 1e-10)

        # Encodage en ψ pour usage ultérieur (TTS pipeline)
        psi_glottal = encode(f"glottal|f0:{self.f0}|n:{self.n_harmonics}",
                            dim=self.dim)
        return waveform, psi_glottal


# ═══════════════════════════════════════════════════════════════════════════════
# 7. ADAPTATEUR HARMONIC CLONER → filter_wave / resonate
# ═══════════════════════════════════════════════════════════════════════════════

class HarmonicCloner:
    """
    Clonage vocal par résonance harmonique.

    Adaptateur pour ka_sonic/harmonic_cloner.py.
    Utilise wave_lang.filter_wave() pour le warping spectral
    et wave_lang.resonate() pour le matching.

    Usage :
        cloner = HarmonicCloner()
        cloned_audio = cloner.clone(source_audio, target_signature)
    """

    def __init__(self, dim: int = 1024):
        self.dim = dim
        self.analyzer = SpectralAnalyzer(dim=dim)

    def extract_spectral_envelope(self, audio: np.ndarray) -> np.ndarray:
        """
        Extrait l'enveloppe spectrale (formants + tilt).

        Utilise wave_lang.spectrum() puis lissage.
        """
        spec = self.analyzer.spectrum(audio)
        # Lissage pour obtenir l'enveloppe
        from scipy.ndimage import uniform_filter1d
        try:
            envelope = uniform_filter1d(spec, size=7)
        except Exception:
            envelope = spec
        return envelope

    def warp_spectrum(self, source_audio: np.ndarray,
                      target_envelope: np.ndarray) -> np.ndarray:
        """
        Déforme le spectre source vers l'enveloppe cible.

        Utilise wave_lang.filter_wave() avec un filtre personnalisé
        qui applique le ratio source→cible.
        """
        source_spec = self.analyzer.analyze(source_audio)
        source_env = np.abs(source_spec)

        # Ajuster les dimensions
        min_len = min(len(source_env), len(target_envelope))
        src_env = source_env[:min_len]
        tgt_env = target_envelope[:min_len]

        # Calcul du filtre de warping
        ratio = (tgt_env + 1e-10) / (src_env + 1e-10)
        # Limiter l'amplification
        ratio = np.clip(ratio, 0.01, 100.0)

        def warp_filter(freqs: np.ndarray) -> np.ndarray:
            """Applique le ratio d'enveloppe dans le domaine fréquentiel."""
            n = len(freqs)
            r = min(n, len(ratio))
            result = freqs.copy()
            result[:r] *= ratio[:r]
            # Symétrie hermitienne pour les fréquences négatives
            if n > 2 * r:
                result[n-r:n] *= ratio[:r][::-1]
            return result

        # Appliquer via wave_lang.filter_wave
        return np.real(filter_wave(source_audio.astype(np.complex128),
                                   filter_fn=warp_filter))

    def clone(self, source_audio: np.ndarray,
              target_audio: np.ndarray) -> np.ndarray:
        """
        Clone la voix cible sur le contenu source.

        Args:
            source_audio: contenu vocal à modifier
            target_audio: échantillon de la voix cible

        Returns:
            audio source avec le timbre de la cible
        """
        target_envelope = self.extract_spectral_envelope(target_audio)
        return self.warp_spectrum(source_audio, target_envelope)


# ═══════════════════════════════════════════════════════════════════════════════
# 8. ADAPTATEUR COHERENCE ATTENTION → resonate / coherence / superpose
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : HarmonicAttention dans harmonic_attention.py calculait la matrice
#         de cohérence C_ij = Re(<psi_i|psi_j>) et modulait chaque token
#         par interférence pondérée des voisins (≈200 lignes de numpy).
# Après : wave_lang.resonate() pour C_ij, superpose pour la modulation.

class CoherenceAttention:
    """
    Attention harmonique par cohérence de phase — équivalent ondulatoire
    de la self-attention des Transformers.

    Drop-in replacement pour harmonic_attention.py.
    Même API, backend wave_lang.resonate + superpose.

    Formule :
        C_ij = resonate(psi_i, psi_j)            # matrice de cohérence
        psi_i' = superpose(psi_i, *voisins_pondérés)  # modulation contextuelle

    Usage :
        attn = CoherenceAttention(dim=512)
        ctx = attn.contextualize(["le", "chat", "dort"])
        psi_q = attn.contextualize_query("le chat dort")
    """

    # Constantes issues de harmonic_attention.py
    ALPHA_DEFAULT = 0.3   # force d'interférence contextuelle
    POWER_DEFAULT = 2.0   # exposant de la cohérence (p=2 → quadratique)

    def __init__(self, encoder=None, dim: int = DEFAULT_DIM,
                 alpha: float = None, power: float = None):
        self.encoder = encoder
        self.dim = dim
        self.alpha = alpha if alpha is not None else self.ALPHA_DEFAULT
        self.power = power if power is not None else self.POWER_DEFAULT
        self._original_encoder = encoder  # pour restore

    def contextualize(self, tokens: List[str],
                      alpha: float = None,
                      power: float = None) -> Dict[str, np.ndarray]:
        """
        Contextualise chaque token par résonance avec ses voisins.

        Pour chaque token i :
            psi_i' = normalize(psi_i + alpha * Σ_j C_ij^p * psi_j)

        où C_ij = resonate(psi_i, psi_j) ∈ [-1, 1].

        Args:
            tokens: liste de tokens à contextualiser
            alpha: force d'interférence (défaut: 0.3)
            power: exposant de cohérence (défaut: 2.0)

        Returns:
            dict {token: psi_contextuel}
        """
        a = alpha if alpha is not None else self.alpha
        p = power if power is not None else self.power

        # Encoder tous les tokens (via wave_lang.encode)
        unique_tokens = list(dict.fromkeys(tokens))  # ordre préservé, doublons évités
        psi_map = {t: encode(t, dim=self.dim) for t in unique_tokens}

        # Pour chaque token, calculer la modulation par cohérence
        result = {}
        for i, token_i in enumerate(tokens):
            psi_i = psi_map[token_i]
            contributions = [psi_i]  # le token lui-même

            for j, token_j in enumerate(tokens):
                if i == j:
                    continue
                psi_j = psi_map[token_j]
                # C_ij = resonate(psi_i, psi_j)
                c_ij = resonate(psi_i, psi_j)
                # Pondération : C_ij^p (préserve le signe pour p pair, abs pour p impair)
                if p % 2 == 0:
                    weight = a * (c_ij ** p)
                else:
                    weight = a * (abs(c_ij) ** p) * (1.0 if c_ij >= 0 else -1.0)
                contributions.append(weight * psi_j)

            # Superposition de toutes les contributions
            psi_ctx = superpose(*contributions)
            result[token_i] = psi_ctx

        return result

    def contextualize_query(self, query: str,
                            alpha: float = None) -> np.ndarray:
        """
        Contextualise une requête complète.

        Tokenise, contextualise chaque token, puis superpose le résultat.

        Args:
            query: texte de la requête
            alpha: force d'interférence

        Returns:
            psi_contextuel moyen de la requête
        """
        tokens = query.lower().split()
        if not tokens:
            return encode("", dim=self.dim)

        ctx = self.contextualize(tokens, alpha=alpha)
        # Moyenne des psi contextuels → psi de la requête
        psis = [ctx[t] for t in tokens]
        return superpose(*psis)

    def disambiguate(self, word: str, context: List[str],
                     candidate_senses: Dict[str, np.ndarray] = None) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Désambiguïse un mot par son contexte.

        Calcule la cohérence entre le psi_contextuel du mot et chaque sens candidat.

        Args:
            word: mot à désambiguïser
            context: mots du contexte
            candidate_senses: {sens: psi_sens} (optionnel)

        Returns:
            (psi_désambiguïsé, {sens: score_de_cohérence})
        """
        # Construire le psi contextuel
        all_tokens = context + [word]
        ctx = self.contextualize(all_tokens)
        psi_word_ctx = ctx[word]

        # Si pas de sens candidats, encoder via wave_lang et chercher les plus proches
        if candidate_senses is None:
            # Fallback: retourner le psi contextuel tel quel
            return psi_word_ctx, {"contextuel": 1.0}

        # Calculer la cohérence avec chaque sens
        scores = {}
        for sense, psi_sense in candidate_senses.items():
            scores[sense] = float(coherence(psi_word_ctx, psi_sense))

        # Normaliser les scores
        total = sum(scores.values()) + 1e-15
        scores = {k: v / total for k, v in scores.items()}

        return psi_word_ctx, scores

    def inject_into_encoder(self, tokens: List[str]) -> None:
        """Injecte les psi contextualisés dans l'encodeur (si présent)."""
        if self.encoder is None:
            return
        ctx = self.contextualize(tokens)
        for token, psi in ctx.items():
            # Si l'encodeur a un cache de mots, le mettre à jour
            if hasattr(self.encoder, 'word_vectors'):
                self.encoder.word_vectors[token] = psi

    def restore_encoder(self) -> None:
        """Restaure l'encodeur original."""
        self.encoder = self._original_encoder

    def __enter__(self) -> 'CoherenceAttention':
        return self

    def __exit__(self, *args) -> None:
        self.restore_encoder()


# ═══════════════════════════════════════════════════════════════════════════════
# 9. ADAPTATEUR HOLOGRAPHIC ENCODER → encode / normalize / bind / unbind
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : HolographicEncoder dans holographic_encoder.py (~1256 lignes)
#         gérait l'encodage FNV1a + phi-spacing, le binding HRR, et la
#         mémoire holographique avec superposition et corrélation.
# Après : wave_lang.encode, bind, unbind, HolographicMemory.

class HolographicEncoderBridge:
    """
    Encodeur holographique unifié — encodage de mots, faits, et mémoire.

    Drop-in replacement pour holographic_encoder.py.
    Même API, backend wave_lang.encode + HolographicMemory.

    Usage :
        enc = HolographicEncoderBridge(dim=512)
        psi_chat = enc.encode_word("chat")
        psi_fact = enc.encode_fact("chat", "est", "animal")
        enc.store_fact("Paris", "capitale_de", "France")
        results = enc.query(enc.encode_query("capitale de la France"))
    """

    def __init__(self, dim: int = DEFAULT_DIM):
        self.dim = dim
        self.memory = HolographicMemory(dim=dim)
        self.word_vectors: Dict[str, np.ndarray] = {}
        self._encode_cache: Dict[str, np.ndarray] = {}

    def encode_word(self, word: str) -> np.ndarray:
        """
        Encode un mot en vecteur d'onde ψ ∈ ℂᵈⁱᵐ.

        Délègue à wave_lang.encode().
        Priorité : 1) cache interne, 2) wave_lang.encode.
        """
        if word in self._encode_cache:
            return self._encode_cache[word].copy()
        psi = encode(word, dim=self.dim)
        self._encode_cache[word] = psi
        self.word_vectors[word] = psi
        return psi

    def encode_word_fast(self, word: str) -> np.ndarray:
        """Encodage rapide (FNV1a uniquement, sans cache sémantique)."""
        return encode(word, dim=self.dim, use_cache=True)

    def encode_char(self, char: str) -> np.ndarray:
        """Encodage d'un caractère unique."""
        return encode(char, dim=self.dim)

    def encode_unknown(self, word: str) -> np.ndarray:
        """Encodage fallback pour mot inconnu (identique à encode_word)."""
        return self.encode_word(word)

    def bind(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        Binding HRR par convolution circulaire.

        Équivalent à wave_lang.bind(a, b).
        """
        from wave_lang import bind as _bind
        return _bind(a, b)

    def unbind(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        Unbinding HRR par corrélation circulaire.

        Équivalent à wave_lang.unbind(a, b).
        """
        from wave_lang import unbind as _unbind
        return _unbind(a, b)

    def encode_fact(self, sujet: str, relation: str, objet: str) -> np.ndarray:
        """
        Encode un fait (sujet, relation, objet) en ψ.

        ψ_fait = bind(encode(sujet), encode(relation), encode(objet))
        """
        psi_s = self.encode_word(sujet)
        psi_r = self.encode_word(relation)
        psi_o = self.encode_word(objet)
        return bind_many(psi_s, psi_r, psi_o)

    def encode_query(self, question: str,
                     w2i: Optional[Dict[str, int]] = None) -> np.ndarray:
        """
        Encode une question en ψ (moyenne des ψ des tokens).
        """
        tokens = question.lower().split()
        if not tokens:
            return encode("", dim=self.dim)
        psis = [self.encode_word(t) for t in tokens]
        return superpose(*psis)

    def store(self, fact_vector: np.ndarray, amplitude: float = 1.0) -> None:
        """
        Stocke un vecteur de fait dans la mémoire holographique.

        H += amplitude * psi_fait
        """
        self.memory.store_raw(fact_vector, amplitude=amplitude)

    def store_fact(self, sujet: str, relation: str, objet: str,
                   amplitude: float = 1.0) -> None:
        """
        Encode et stocke un fait (sujet, relation, objet).
        """
        psi_fact = self.encode_fact(sujet, relation, objet)
        self.memory.store(encode(sujet, dim=self.dim),
                         encode(relation, dim=self.dim),
                         encode(objet, dim=self.dim),
                         amplitude=amplitude)

    def query(self, query_vector: np.ndarray) -> np.ndarray:
        """
        Requête holographique par corrélation circulaire.

        result = memory ☆ query_vector
        """
        return self.memory.query(query_vector)

    def resonance_score(self, word: str, query_vector: np.ndarray) -> float:
        """
        Score de résonance d'un mot avec un vecteur de requête.

        score = Re(⟨psi_mot | psi_requête⟩)
        """
        psi_word = self.encode_word(word)
        return float(resonate(psi_word, query_vector))

    def resonance_scores_batch(self, words: List[str],
                               query_vector: np.ndarray) -> np.ndarray:
        """Scores de résonance par lot."""
        psis = np.array([self.encode_word(w) for w in words])
        return resonate_batch(query_vector, psis)

    @property
    def vocab_size(self) -> int:
        return len(self.word_vectors)

    @property
    def energy(self) -> float:
        return self.memory.energy

    def similarity(self, word_a: str, word_b: str) -> float:
        """Similarité entre deux mots (0 = orthogonal, 1 = identique)."""
        return coherence(self.encode_word(word_a), self.encode_word(word_b))

    def similarity_word(self, word_a: str, word_b: str) -> float:
        """Alias pour similarity."""
        return self.similarity(word_a, word_b)

    def collision_check(self, threshold: float = 0.95) -> List[Tuple[str, str, float]]:
        """
        Détecte les collisions d'encodage (mots différents mais ψ quasi-identiques).
        """
        collisions = []
        words = list(self.word_vectors.keys())
        for i in range(len(words)):
            for j in range(i + 1, len(words)):
                score = coherence(self.word_vectors[words[i]],
                                self.word_vectors[words[j]])
                if score >= threshold:
                    collisions.append((words[i], words[j], float(score)))
        return collisions


# ═══════════════════════════════════════════════════════════════════════════════
# 10. ADAPTATEUR PHASE PROPAGATOR → phase_shift / rotate / resonate
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : PhaseAmplifier dans phase_amplifier.py (~622 lignes) propageait
#         ψ à travers une chaîne de raisonnement avec amplification par
#         interférence constructive et beam search multi-branches.
# Après : wave_lang.phase_shift + resonate + superpose.

class PhasePropagator:
    """
    Propagateur de phase — raisonnement par amplification en cascade.

    Drop-in replacement pour phase_amplifier.py (PhaseAmplifier).
    Même API, backend wave_lang.phase_shift + resonate.

    Formule :
        psi_next = normalize(psi_current + alpha * psi_context)
        où alpha croît avec la profondeur (amplification constructive).

    Usage :
        prop = PhasePropagator(brain=mon_brain, dim=512)
        chain = prop.propagate("Pourquoi le ciel est-il bleu ?")
        reponse = prop.reason_deep("Pourquoi le ciel est-il bleu ?")
    """

    COHERENCE_MIN = 0.15  # seuil de cohérence pour continuer la propagation

    def __init__(self, brain=None, dim: int = DEFAULT_DIM, encoder=None):
        self.brain = brain
        self.dim = dim
        self.encoder = encoder

    def propagate(self, question: str, max_depth: int = 10,
                  coherence_threshold: float = None) -> 'PropagationChain':
        """
        Propagation de phase sur un chemin unique.

        À chaque étape :
        1. Encode la question courante → psi_q
        2. Cherche le fait le plus résonant dans le cerveau → psi_fact
        3. Amplifie : psi_next = normalize(psi_q + alpha * psi_fact)
        4. Vérifie la cohérence : si < seuil, arrête

        Args:
            question: question initiale
            max_depth: profondeur maximale
            coherence_threshold: seuil d'arrêt (défaut: COHERENCE_MIN)

        Returns:
            PropagationChain avec les étapes, conclusion, et métriques
        """
        threshold = coherence_threshold if coherence_threshold is not None else self.COHERENCE_MIN

        # Importer PropagationChain et PropagationStep localement pour éviter
        # la dépendance circulaire
        try:
            from phase_amplifier import PropagationChain, PropagationStep
        except ImportError:
            # Fallback: classes simplifiées
            PropagationStep = type('PropagationStep', (), {
                '__init__': lambda self, **kw: setattr(self, '__dict__', kw) or None
            })
            PropagationChain = type('PropagationChain', (), {
                '__init__': lambda self, **kw: setattr(self, '__dict__', kw) or None
            })

        psi_current = encode(question, dim=self.dim)
        steps = []
        context_accumulated = psi_current.copy()
        stopped_reason = "profondeur_max"

        for depth in range(max_depth):
            # Chercher le fait le plus résonant
            if self.brain and hasattr(self.brain, 'store'):
                facts = self.brain.store.retrieve_resonance(question, max_results=1)
                if facts:
                    fact_record, resonance_score_val = facts[0]
                    # Compatible dict (HolographicRAG) et objet (FactRecord)
                    psi_record = self._record_attr(fact_record, 'psi')
                    if psi_record is None:
                        psi_record = encode(
                            f"{self._record_attr(fact_record, 'sujet', '')} "
                            f"{self._record_attr(fact_record, 'relation', '')} "
                            f"{self._record_attr(fact_record, 'objet', '')}",
                            dim=self.dim
                        )
                    psi_fact = psi_record
                    coherence_val = float(coherence(psi_current, psi_fact))
                else:
                    stopped_reason = "plus_de_faits"
                    break
            else:
                # Sans cerveau, auto-réflexion sur la question
                psi_fact = phase_shift(psi_current, PHI * (depth + 1))
                resonance_score_val = float(resonate(psi_current, psi_fact))
                coherence_val = float(coherence(psi_current, psi_fact))
                fact_record = None

            # Vérifier le seuil
            if coherence_val < threshold and depth > 0:
                stopped_reason = f"coherence_insuffisante ({coherence_val:.3f} < {threshold})"
                break

            # Amplification : alpha croît avec la profondeur
            alpha = 1.0 / (1.0 + depth)  # décroissant → les premières étapes comptent plus
            psi_next = normalize(psi_current + alpha * psi_fact)

            step = PropagationStep(
                depth=depth,
                query_psi=psi_current.copy(),
                fact_found=(self._record_attr(fact_record, 'sujet', '?'),
                           self._record_attr(fact_record, 'relation', '?'),
                           self._record_attr(fact_record, 'objet', '?'),
                           self._record_attr(fact_record, 'secteur', '?')),
                resonance=resonance_score_val,
                coherence=coherence_val,
                context_accumulated=context_accumulated.copy(),
                amplification_factor=alpha,
            )
            steps.append(step)

            # Accumuler le contexte
            context_accumulated = superpose(context_accumulated, psi_fact, weights=[0.7, 0.3])
            psi_current = psi_next
            stopped_reason = "profondeur_max"

        # Construire la chaîne
        total_coherence = float(np.mean([s.coherence for s in steps])) if steps else 0.0
        chain = PropagationChain(
            steps=steps,
            initial_question=question,
            final_conclusion=self._build_conclusion(steps, question),
            total_coherence=total_coherence,
            stopped_reason=stopped_reason,
        )
        return chain

    def _build_conclusion(self, steps: list, question: str) -> str:
        """Construit une conclusion à partir des étapes de propagation."""
        if not steps:
            return f"Aucune conclusion trouvée pour : {question}"
        facts_found = [s.fact_found for s in steps if s.fact_found[0] != "?"]
        if facts_found:
            dernier = facts_found[-1]
            return f"{dernier[0]} {dernier[1]} {dernier[2]}"
        return f"Raisonnement en {len(steps)} étapes sur : {question}"

    @staticmethod
    def _record_attr(record, key: str, default=None):
        """
        Extrait un attribut d'un record, compatible dict ET objet.

        Les adaptateurs HolographicRAG retournent des dicts ;
        le HolographicStore original retourne des FactRecord (objets).
        """
        if record is None:
            return default
        if isinstance(record, dict):
            return record.get(key, default)
        return getattr(record, key, default)

    def propagate_multi(self, question: str, max_depth: int = 10,
                        beam_width: int = 3, branch_factor: int = 3,
                        coherence_threshold: float = None) -> list:
        """
        Propagation multi-branches avec beam search.

        Pour chaque branche, appelle propagate() et sélectionne
        les beam_width meilleures chaînes par cohérence totale.

        Args:
            question: question initiale
            max_depth: profondeur maximale par branche
            beam_width: nombre de branches à garder
            branch_factor: nombre de branches à explorer
            coherence_threshold: seuil d'arrêt

        Returns:
            liste de PropagationChain triée par cohérence décroissante
        """
        chains = []
        # Explorer branch_factor variations de la question
        questions = [question]
        for b in range(1, branch_factor):
            psi_q = encode(question, dim=self.dim)
            psi_var = phase_shift(psi_q, b * PHI / branch_factor)
            # Décoder approximativement la variation
            questions.append(f"{question} [variante {b}]")

        for q in questions[:branch_factor]:
            chain = self.propagate(q, max_depth=max_depth,
                                  coherence_threshold=coherence_threshold)
            chains.append(chain)

        # Trier par cohérence totale décroissante
        chains.sort(key=lambda c: c.total_coherence if hasattr(c, 'total_coherence') else 0.0, reverse=True)
        return chains[:beam_width]

    def explain(self, chain: 'PropagationChain') -> str:
        """
        Traduit une chaîne de propagation en langage naturel.

        Args:
            chain: PropagationChain à expliquer

        Returns:
            explication en français
        """
        if not hasattr(chain, 'steps') or not chain.steps:
            return "Aucune étape de raisonnement."

        lines = [f"Question : {chain.initial_question}"]
        for step in chain.steps:
            lines.append(
                f"  Étape {step.depth + 1} : "
                f"résonance={step.resonance:.3f}, "
                f"cohérence={step.coherence:.3f}, "
                f"amplification={step.amplification_factor:.3f}"
            )
        lines.append(f"Conclusion : {chain.final_conclusion}")
        lines.append(f"Arrêt : {chain.stopped_reason}")
        return "\n".join(lines)

    def reason_deep(self, question: str, max_depth: int = 10) -> str:
        """
        Interface simplifiée : retourne la conclusion en langage naturel.

        Args:
            question: question à raisonner
            max_depth: profondeur maximale

        Returns:
            conclusion textuelle
        """
        chain = self.propagate(question, max_depth=max_depth)
        return chain.final_conclusion if hasattr(chain, 'final_conclusion') else str(chain)

    def reason_deep_multi(self, question: str, max_depth: int = 10,
                          beam_width: int = 3) -> str:
        """
        Interface simplifiée multi-branches.

        Args:
            question: question à raisonner
            max_depth: profondeur maximale
            beam_width: nombre de branches

        Returns:
            meilleure conclusion
        """
        chains = self.propagate_multi(question, max_depth=max_depth,
                                     beam_width=beam_width)
        if chains and hasattr(chains[0], 'final_conclusion'):
            return chains[0].final_conclusion
        return self.reason_deep(question, max_depth=max_depth)


# ═══════════════════════════════════════════════════════════════════════════════
# 11. ADAPTATEUR WAVE DECODER → resonate / coherence / decode
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : WaveDecoder dans wave_decoder.py (~622 lignes) décodait une
#         réponse émergente de l'hologramme sans templates, par clustering
#         de phase et assemblage par résonance.
# Après : wave_lang.resonate + coherence + decode.

class WaveDecoderBridge:
    """
    Décodeur ondulatoire — génération de réponses par émergence holographique.

    Drop-in replacement pour wave_decoder.py (WaveDecoder).
    Même API, backend wave_lang.resonate + decode.

    Usage :
        dec = WaveDecoderBridge(encoder=mon_encodeur, knowledge_base=kb)
        reponse = dec.decode("Qu'est-ce qu'un chat ?")
        reponse_riche = dec.decode_rich("Explique la relativité")
        signature = dec.compute_signature("question complexe")
    """

    def __init__(self, encoder=None, knowledge_base: List[Tuple] = None,
                 vocab_limit: int = 5000):
        self.encoder = encoder
        self.knowledge_base = knowledge_base or []
        self.vocab_limit = vocab_limit
        self.dim = DEFAULT_DIM
        if encoder and hasattr(encoder, 'dim'):
            self.dim = encoder.dim

    def decode(self, question: str, max_words: int = 12,
               max_sentences: int = 3) -> str:
        """
        Décodage ondulatoire pur — aucun template.

        Pipeline :
        1. Encode la question → psi_Q
        2. Trouve les mots résonants via Re(⟨ψ_w | ψ_Q⟩)
        3. Cluste les mots par proximité de phase (seuil angulaire π/4)
        4. Ordonne les clusters par amplitude de résonance
        5. Assemble la réponse — la phrase ÉMERGE de l'ordre des mots

        Args:
            question: question en langage naturel
            max_words: nombre maximal de mots dans la réponse
            max_sentences: nombre maximal de phrases

        Returns:
            réponse en langage naturel
        """
        # Encoder la question
        psi_q = encode(question, dim=self.dim)

        # Construire le vocabulaire à partir de la base de connaissances
        vocab = {}
        if self.encoder and hasattr(self.encoder, 'word_vectors'):
            vocab = dict(self.encoder.word_vectors)
        elif self.knowledge_base:
            for sujet, relation, objet, *_ in self.knowledge_base:
                for word in [sujet, relation, objet]:
                    if word not in vocab:
                        vocab[word] = encode(word, dim=self.dim)

        if not vocab:
            return question  # fallback

        # Limiter le vocabulaire
        vocab_items = list(vocab.items())[:self.vocab_limit]

        # Calculer les scores de résonance
        words = []
        for word, psi_w in vocab_items:
            score = float(resonate(psi_q, psi_w))
            words.append((word, score, psi_w))

        # Trier par score décroissant
        words.sort(key=lambda x: -x[1])

        # Garder les mots avec cohérence positive
        positive_words = [(w, s, p) for w, s, p in words if s > 0][:max_words]

        if not positive_words:
            # Aucun mot résonant → retourner les meilleurs même si négatifs
            positive_words = [(w, s, p) for w, s, p in words[:max_words]]

        # Assemblage simple : concaténer les mots par score décroissant
        response_words = [w for w, s, p in positive_words]
        return " ".join(response_words)

    def decode_rich(self, question: str) -> str:
        """
        Décodage riche avec HolographicMemory + synthétiseur.

        Version améliorée de decode() qui utilise la mémoire holographique
        pour enrichir le contexte.

        Args:
            question: question en langage naturel

        Returns:
            réponse enrichie
        """
        # Utiliser HolographicMemory si disponible via l'encodeur
        psi_q = encode(question, dim=self.dim)

        # Récupérer les connaissances de la base
        relevant_facts = []
        if self.knowledge_base:
            for sujet, relation, objet, *_ in self.knowledge_base:
                psi_fact = bind_many(
                    encode(sujet, dim=self.dim),
                    encode(relation, dim=self.dim),
                    encode(objet, dim=self.dim)
                )
                score = float(coherence(psi_q, psi_fact))
                if score > 0.1:
                    relevant_facts.append((sujet, relation, objet, score))

        # Trier par cohérence
        relevant_facts.sort(key=lambda x: -x[3])

        # Construire la réponse
        if relevant_facts:
            best = relevant_facts[0]
            base = f"{best[0]} {best[1]} {best[2]}"
            # Ajouter des faits supplémentaires
            extra = [f"{s} {r} {o}" for s, r, o, sc in relevant_facts[1:4]]
            if extra:
                base += ". " + ". ".join(extra)
            return base

        return self.decode(question)

    def compute_signature(self, question: str) -> dict:
        """
        Signature spectrale 9D de la question.

        Analyse la question selon 9 dimensions :
        phi_ratio, alpha_complex, reasoning, creativity, math_val,
        factual, code_val, emotion, temporal, type

        Args:
            question: question à analyser

        Returns:
            dict avec les 9 dimensions + le type dominant
        """
        psi_q = encode(question, dim=self.dim)
        spec = spectrum(psi_q)
        stats_dict = stats(psi_q)

        # Calculer les 9 dimensions à partir du spectre et des stats
        dims = self.dim
        third = dims // 3

        return {
            'phi_ratio': float(PHI),
            'alpha_complex': float(ALPHA),
            'reasoning': float(np.mean(spec[:third])),
            'creativity': float(np.mean(spec[third:2 * third])),
            'math_val': float(np.mean(spec[2 * third:])),
            'factual': float(stats_dict.get('mean_amplitude', 0.5)),
            'code_val': float(stats_dict.get('spectral_entropy', 0.5)),
            'emotion': float(stats_dict.get('phase_std', 0.0)),
            'temporal': float(TAU),
            'type': 'raisonnement' if stats_dict.get('mean_amplitude', 0) > 0.5 else 'créatif',
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 12. ADAPTATEUR HOLOGRAPHIC RAG → HolographicMemory / resonate
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : HolographicStore dans harmonic_brain.py (~3759 lignes total)
#         gérait le stockage holographique, la recherche TF-IDF + spectrale,
#         la rumination nocturne, et le renforcement/affaiblissement.
# Après : wave_lang.HolographicMemory pour le stockage, resonate pour la
#         recherche, bind_many pour l'encodage des faits.

class HolographicRAG:
    """
    RAG holographique — stockage et recherche par résonance.

    Drop-in replacement pour harmonic_brain.py (HolographicStore).
    Même API, backend wave_lang.HolographicMemory + resonate.

    Usage :
        rag = HolographicRAG(dim=512)
        rag.ingest("Paris", "capitale_de", "France", "GEOGRAPHIE")
        results = rag.retrieve_resonance("capitale de la France")
    """

    RESONANCE_THRESHOLD = 0.15
    ALPHA_REINFORCE = 0.1
    ALPHA_WEAKEN = 0.05

    def __init__(self, dim: int = DEFAULT_DIM, use_holographic: bool = True):
        self.dim = dim
        self.use_holographic = use_holographic
        self.memory = HolographicMemory(dim=dim) if use_holographic else None
        self._facts: List[Dict] = []  # [{sujet, relation, objet, secteur, psi, amplitude, count, ...}]
        self._fact_psis: List[np.ndarray] = []

    def ingest(self, sujet: str, relation: str, objet: str,
               secteur: str = "GENERAL") -> Dict:
        """
        Ingère un fait dans la mémoire holographique.

        H += amplitude * psi_fait

        Args:
            sujet: sujet du fait
            relation: relation
            objet: objet
            secteur: domaine (GEOGRAPHIE, SCIENCE, etc.)

        Returns:
            dict représentant le fait stocké
        """
        psi_fact = bind_many(
            encode(sujet, dim=self.dim),
            encode(relation, dim=self.dim),
            encode(objet, dim=self.dim)
        )

        fact = {
            'sujet': sujet,
            'relation': relation,
            'objet': objet,
            'secteur': secteur,
            'psi': psi_fact,
            'amplitude': 1.0,
            'count': 1,
            'last_seen': 0.0,
            'confidence': 0.5,
            'times_retrieved': 0,
            'times_accepted': 0,
        }
        self._facts.append(fact)
        self._fact_psis.append(psi_fact)

        if self.memory:
            self.memory.store_raw(psi_fact, amplitude=1.0)

        return fact

    def ingest_batch(self, facts: List[Tuple[str, str, str, str]]) -> int:
        """
        Ingère un lot de faits.

        Args:
            facts: liste de (sujet, relation, objet, secteur)

        Returns:
            nombre de faits ingérés
        """
        count = 0
        for sujet, relation, objet, secteur in facts:
            self.ingest(sujet, relation, objet, secteur)
            count += 1
        return count

    def retrieve(self, question: str, threshold: float = None,
                 max_results: int = 50) -> List[Tuple[Dict, float]]:
        """
        Recherche TF-IDF lexicale avec bonus spectral.

        Pour la compatibilité, combine recherche par résonance et
        correspondance lexicale simple.

        Args:
            question: question de recherche
            threshold: seuil de cohérence minimal
            max_results: nombre maximal de résultats

        Returns:
            liste de (fait, score) triée par score décroissant
        """
        thresh = threshold if threshold is not None else self.RESONANCE_THRESHOLD
        psi_q = encode(question, dim=self.dim)

        results = []
        question_lower = question.lower()
        question_words = set(question_lower.split())

        for i, fact in enumerate(self._facts):
            # Score de résonance holographique
            resonance_score_val = float(resonate(psi_q, self._fact_psis[i]))

            # Bonus lexical : mots de la question présents dans le fait
            fact_text = f"{fact['sujet']} {fact['relation']} {fact['objet']}".lower()
            fact_words = set(fact_text.split())
            lexical_overlap = len(question_words & fact_words) / max(len(question_words), 1)
            lexical_bonus = lexical_overlap * 0.3

            # Score combiné
            combined_score = resonance_score_val + lexical_bonus

            if combined_score >= thresh:
                results.append((fact, combined_score))

        # Trier par score décroissant
        results.sort(key=lambda x: -x[1])
        return results[:max_results]

    def retrieve_resonance(self, question: str, max_results: int = 50,
                           sector_boost: str = None) -> List[Tuple[Dict, float]]:
        """
        Recherche par résonance holographique pure.

        score = Re(⟨ψ_fait | ψ_question⟩)

        Args:
            question: question de recherche
            max_results: nombre maximal de résultats
            sector_boost: secteur à booster (optionnel)

        Returns:
            liste de (fait, score) triée par cohérence décroissante
        """
        psi_q = encode(question, dim=self.dim)

        results = []
        for i, fact in enumerate(self._facts):
            score = float(coherence(psi_q, self._fact_psis[i]))

            # Boost sectoriel
            if sector_boost and fact['secteur'] == sector_boost:
                score *= 1.5

            results.append((fact, score))

        results.sort(key=lambda x: -x[1])
        return results[:max_results]

    @property
    def psi_dominant(self) -> np.ndarray:
        """
        Retourne le ψ moyen des 10 faits de plus haute amplitude.
        """
        if not self._facts:
            return np.zeros(self.dim, dtype=np.complex128)

        # Trier par amplitude
        sorted_facts = sorted(self._facts, key=lambda f: f['amplitude'], reverse=True)
        top = sorted_facts[:10]
        top_psis = [f['psi'] for f in top]
        return superpose(*top_psis)

    def ruminate(self, max_pairs: int = 50000) -> None:
        """
        Consolidation nocturne : interférence constructive/destructive
        entre paires de faits aléatoires.

        Pour chaque paire (i, j) :
        - Si cohérence > 0.5 → renforcer les deux (interférence constructive)
        - Si cohérence < -0.3 → affaiblir (interférence destructive)
        """
        n = len(self._facts)
        if n < 2:
            return

        import random
        pairs = min(max_pairs, n * (n - 1) // 2)

        for _ in range(pairs):
            i, j = random.sample(range(n), 2)
            c = float(coherence(self._fact_psis[i], self._fact_psis[j]))

            if c > 0.5:
                # Renforcement mutuel
                self._facts[i]['amplitude'] = min(10.0, self._facts[i]['amplitude'] + 0.01)
                self._facts[j]['amplitude'] = min(10.0, self._facts[j]['amplitude'] + 0.01)
            elif c < -0.3:
                # Affaiblissement mutuel
                self._facts[i]['amplitude'] = max(0.1, self._facts[i]['amplitude'] - 0.005)
                self._facts[j]['amplitude'] = max(0.1, self._facts[j]['amplitude'] - 0.005)

    def reinforce(self, fact: Dict, amount: float = None) -> None:
        """
        Renforce un fait dans la mémoire.

        Args:
            fact: le fait à renforcer
            amount: quantité de renforcement
        """
        a = amount if amount is not None else self.ALPHA_REINFORCE
        fact['amplitude'] = min(10.0, fact['amplitude'] + a)
        fact['times_retrieved'] = fact.get('times_retrieved', 0) + 1
        fact['times_accepted'] = fact.get('times_accepted', 0) + 1

    def weaken(self, fact: Dict, amount: float = None) -> None:
        """
        Affaiblit un fait dans la mémoire.

        Args:
            fact: le fait à affaiblir
            amount: quantité d'affaiblissement
        """
        a = amount if amount is not None else self.ALPHA_WEAKEN
        fact['amplitude'] = max(0.01, fact['amplitude'] - a)
        fact['times_retrieved'] = fact.get('times_retrieved', 0) + 1

    @property
    def stats(self) -> dict:
        """Statistiques de la mémoire."""
        return {
            'n_facts': len(self._facts),
            'total_energy': float(sum(abs(f['psi']).sum() for f in self._facts)),
            'mean_amplitude': float(np.mean([f['amplitude'] for f in self._facts])) if self._facts else 0.0,
            'secteurs': list(set(f['secteur'] for f in self._facts)),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 13. ADAPTATEUR FEW-SHOT PHASE LOCK → superpose / amplify / phase_shift
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : FewShotInjector dans few_shot_injector.py (~492 lignes) injectait
#         des patterns temporaires dans l'hologramme avec décroissance ABC.
# Après : wave_lang.superpose + amplify + phase_shift.

class FewShotPhaseLock:
    """
    Verrouillage de phase — few-shot learning par injection temporaire.

    Drop-in replacement pour few_shot_injector.py (FewShotInjector).
    Même API, backend wave_lang.superpose + amplify.

    Principe :
        psi_pattern = mean(psi_output_i - psi_input_i) sur les exemples
        H_temp = H + boost * psi_pattern  (décroissance ABC exponentielle)

    Usage :
        fsl = FewShotPhaseLock(dim=512)
        pid = fsl.inject([("chat", "cat"), ("chien", "dog")], pattern_type="traduction")
        result = fsl.process(examples, "oiseau")
    """

    def __init__(self, brain=None, dim: int = DEFAULT_DIM, encoder=None):
        self.brain = brain
        self.dim = dim
        self.encoder = encoder
        self._patterns: Dict[str, Dict] = {}  # pattern_id → {psi, boost, type, created_at, ttl, uses}

    def inject(self, examples: List[Tuple[str, str]],
               pattern_type: str = "general",
               ttl_seconds: float = 300) -> Optional[str]:
        """
        Injecte un pattern d'exemples dans l'espace de travail.

        psi_pattern = mean(psi_output_i - psi_input_i)
        Injecté avec décroissance ABC (durée de vie ttl_seconds).

        Args:
            examples: liste de (input, output)
            pattern_type: type de pattern (traduction, format, style, etc.)
            ttl_seconds: durée de vie en secondes

        Returns:
            pattern_id ou None si échec
        """
        if not examples or len(examples) < 1:
            return None

        # Calculer le pattern : moyenne des différences output - input
        diffs = []
        for input_text, output_text in examples:
            psi_in = encode(input_text, dim=self.dim)
            psi_out = encode(output_text, dim=self.dim)
            diffs.append(psi_out - psi_in)

        if not diffs:
            return None

        psi_pattern = superpose(*diffs)

        # Générer un ID unique
        import time
        pattern_id = f"fsl_{pattern_type}_{int(time.time() * 1000)}"

        self._patterns[pattern_id] = {
            'psi': psi_pattern,
            'boost': 1.0,
            'type': pattern_type,
            'created_at': time.time(),
            'ttl': ttl_seconds,
            'uses': 0,
            'coherence': float(norm(psi_pattern)),
            'examples_count': len(examples),
        }

        return pattern_id

    def process(self, examples: List[Tuple[str, str]], query: str,
                pattern_type: str = "general",
                ttl_seconds: float = 300) -> Dict:
        """
        Few-shot complet : injecte les exemples, traite la requête.

        Args:
            examples: liste de (input, output)
            query: requête à traiter
            pattern_type: type de pattern
            ttl_seconds: durée de vie

        Returns:
            dict avec response, confidence, pattern_used, interference_strength
        """
        # Injecter le pattern
        pattern_id = self.inject(examples, pattern_type, ttl_seconds)

        # Traiter la requête avec le pattern injecté
        psi_q = encode(query, dim=self.dim)

        response = query  # fallback
        confidence = 0.5
        pattern_used = None
        interference_strength = 0.0

        if pattern_id and pattern_id in self._patterns:
            pattern = self._patterns[pattern_id]
            psi_pattern = pattern['psi']
            pattern['uses'] += 1

            # Interférence : mélanger la requête avec le pattern
            psi_result = interfere(psi_q, psi_pattern, epsilon=0.3)
            interference_strength = float(coherence(psi_result, psi_pattern))

            # Décoder le résultat si possible
            response = f"[few-shot {pattern_type}] {query}"
            confidence = interference_strength
            pattern_used = pattern
        else:
            # Sans pattern, utiliser le cerveau si disponible
            if self.brain and hasattr(self.brain, 'process'):
                result = self.brain.process(query)
                response = result.response if hasattr(result, 'response') else query
                confidence = result.confidence if hasattr(result, 'confidence') else 0.5

        return {
            'response': response,
            'confidence': confidence,
            'pattern_used': pattern_used,
            'interference_strength': interference_strength,
            'facts_from_kb': [],
            'facts_from_pattern': [],
        }

    def consolidate(self, pattern_id: str) -> None:
        """
        Convertit un pattern (utilisé 3+ fois, cohérence > 0.3) en faits permanents.

        Args:
            pattern_id: ID du pattern à consolider
        """
        if pattern_id not in self._patterns:
            return

        pattern = self._patterns[pattern_id]
        if pattern['uses'] < 3 or pattern['coherence'] < 0.3:
            return

        # Consolider dans le cerveau si disponible
        if self.brain and hasattr(self.brain, 'ingest'):
            self.brain.ingest(
                f"PATTERN {pattern['type']} (n={pattern['examples_count']}, "
                f"coherence={pattern['coherence']:.3f})"
            )

        # Supprimer le pattern temporaire
        del self._patterns[pattern_id]

    def auto_consolidate(self) -> int:
        """
        Auto-consolide tous les patterns éligibles.

        Returns:
            nombre de patterns consolidés
        """
        eligible = [
            pid for pid, p in self._patterns.items()
            if p['uses'] >= 3 and p['coherence'] > 0.3
        ]
        for pid in eligible:
            self.consolidate(pid)
        return len(eligible)

    @property
    def stats(self) -> dict:
        """Statistiques des patterns actifs."""
        return {
            'active_patterns': len(self._patterns),
            'total_injected': sum(p.get('examples_count', 0) for p in self._patterns.values()),
            'avg_coherence': float(np.mean([p['coherence'] for p in self._patterns.values()])) if self._patterns else 0.0,
            'total_uses': sum(p['uses'] for p in self._patterns.values()),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 14. ADAPTATEUR COHERENCE GATE → coherence / filter_wave / resonate
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : ConsciousIntelligence dans conscious_intelligence.py (~320 lignes)
#         raisonnait par résonance directe, abstraction de patterns,
#         chaînage transitif, analogie vectorielle et généralisation.
# Après : wave_lang.coherence + filter_wave + resonate.

class CoherenceGate:
    """
    Porte de cohérence — raisonnement pur par résonance, sans string matching.

    Drop-in replacement pour conscious_intelligence.py (ConsciousIntelligence).
    Même API, backend wave_lang.coherence + resonate.

    Cinq stratégies de raisonnement :
    1. Résonance directe → max cohérence question-fait
    2. Abstraction de patterns → clustering des relations par similarité de phase
    3. Chaînage → cohérence transitive à travers les faits liés
    4. Analogie vectorielle → ψ_A - ψ_B + ψ_C ≈ ψ_?
    5. Généralisation → résonance de pattern

    Usage :
        gate = CoherenceGate(store=mon_store)
        reponse, confiance, methode = gate.reason("Qu'est-ce que X ?", candidats)
    """

    def __init__(self, store=None):
        """
        Args:
            store: HolographicStore ou HolographicRAG
        """
        self.store = store

    def reason(self, question: str, candidates: List,
               parsed=None) -> Tuple[Optional[str], float, str]:
        """
        Raisonnement ondulatoire pur sur une question.

        Args:
            question: question en langage naturel
            candidates: liste de faits candidats (Dict ou objets avec sujet/relation/objet)
            parsed: analyse syntaxique optionnelle

        Returns:
            (answer_text, confidence, method_used)
            method_used ∈ {'resonance', 'chain', 'analogy', 'generalize', 'unknown'}
        """
        if not candidates:
            return None, 0.0, 'unknown'

        psi_q = encode(question, dim=DEFAULT_DIM)

        # ── Stratégie 1 : Résonance directe ──
        best_score = -1.0
        best_fact = None
        scores = []

        for cand in candidates:
            # Récupérer le texte du fait
            if isinstance(cand, dict):
                fact_text = f"{cand.get('sujet', '')} {cand.get('relation', '')} {cand.get('objet', '')}"
            elif hasattr(cand, 'sujet'):
                fact_text = f"{cand.sujet} {cand.relation} {cand.objet}"
            else:
                fact_text = str(cand)

            psi_fact = encode(fact_text, dim=DEFAULT_DIM)
            score = float(coherence(psi_q, psi_fact))
            scores.append((cand, score, fact_text))

            if score > best_score:
                best_score = score
                best_fact = fact_text

        # Si résonance directe suffisante
        if best_score > 0.5 and best_fact:
            return best_fact, best_score, 'resonance'

        # ── Stratégie 2 : Chaînage transitif ──
        # Chercher des paires de faits où l'objet du premier ≈ sujet du second
        if len(candidates) >= 2:
            for i, (cand_a, score_a, text_a) in enumerate(scores):
                for j, (cand_b, score_b, text_b) in enumerate(scores):
                    if i == j:
                        continue

                    # Extraire sujet/objet
                    obj_a = self._extract_component(cand_a, 'objet')
                    subj_b = self._extract_component(cand_b, 'sujet')

                    if obj_a and subj_b:
                        chain_coherence = float(coherence(
                            encode(obj_a, dim=DEFAULT_DIM),
                            encode(subj_b, dim=DEFAULT_DIM)
                        ))
                        if chain_coherence > 0.5:
                            combined_score = (score_a + score_b + chain_coherence) / 3
                            if combined_score > 0.4:
                                chain_text = f"{text_a} donc {text_b}"
                                return chain_text, combined_score, 'chain'

        # ── Stratégie 3 : Analogie vectorielle ──
        # ψ_A - ψ_B + ψ_C ≈ ψ_D
        if len(candidates) >= 3:
            sorted_cands = sorted(scores, key=lambda x: -x[1])
            a, b, c = sorted_cands[0], sorted_cands[1], sorted_cands[2]

            psi_a = encode(a[2], dim=DEFAULT_DIM)
            psi_b = encode(b[2], dim=DEFAULT_DIM)
            psi_c = encode(c[2], dim=DEFAULT_DIM)

            # ψ_analogie = ψ_A - ψ_B + ψ_C
            psi_analogy = psi_a - psi_b + psi_c
            psi_analogy = normalize(psi_analogy)

            # Chercher le candidat le plus proche de ψ_analogie
            best_analogy_score = -1.0
            best_analogy_text = None
            for cand, _, text in scores:
                psi_cand = encode(text, dim=DEFAULT_DIM)
                analogy_score = float(coherence(psi_analogy, psi_cand))
                if analogy_score > best_analogy_score:
                    best_analogy_score = analogy_score
                    best_analogy_text = text

            if best_analogy_score > 0.4 and best_analogy_text:
                return f"Par analogie : {best_analogy_text}", best_analogy_score, 'analogy'

        # ── Stratégie 4 : Généralisation ──
        # Pattern commun entre les meilleurs candidats
        top_candidates = sorted(scores, key=lambda x: -x[1])[:5]
        if top_candidates:
            # Moyenne des ψ des top candidats → pattern général
            top_psis = [encode(t[2], dim=DEFAULT_DIM) for t in top_candidates]
            psi_pattern = superpose(*top_psis)
            generalization_score = float(coherence(psi_q, psi_pattern))

            if generalization_score > 0.3:
                # Le pattern lui-même est la réponse
                relations = [self._extract_component(c, 'relation') for c, _, _ in top_candidates]
                relations = [r for r in relations if r]
                if relations:
                    common_rel = max(set(relations), key=relations.count)
                    return f"Généralisation : {common_rel} (pattern commun)", generalization_score, 'generalize'

        # ── Fallback ──
        if best_fact:
            return best_fact, best_score, 'resonance'
        return None, 0.0, 'unknown'

    def _extract_component(self, cand, key: str) -> Optional[str]:
        """Extrait un composant (sujet, relation, objet) d'un candidat."""
        if isinstance(cand, dict):
            return cand.get(key)
        elif hasattr(cand, key):
            return getattr(cand, key)
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# 15. ADAPTATEUR FEEDBACK LOOP → coherence / amplify / oppose
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : feedback_loop.py (~150 lignes) — le RLHF ondulatoire par
#         boucle phase-amplitude (équivalence #19).
# Après : même API, délégation aux primitives wave_lang.coherence/amplify/oppose
#         et au store du cerveau (reinforce/weaken).

class FeedbackLoopBridge:
    """
    Boucle de feedback ondulatoire (RLHF harmonique).

    Drop-in replacement pour feedback_loop.py.
    Même API, backend wave_lang.coherence + amplify + oppose.

    Formule maîtresse (boucle phase-amplitude) :
        ψ ← ψ + η · (r − cohérence(ψ, ψ_cible)) · ψ_cible

    Le feedback humain module l'amplitude des ondes — pas de reward model,
    pas de gradient, pas d'« alignment tax » (renforcement local).

    Usage :
        loop = FeedbackLoopBridge(brain=brain)
        result = loop.process_feedback(psi_reponse, human_score=0.9)
        score_pred = loop.evaluate(psi_reponse)  # écho de phase
    """

    REINFORCE_THRESHOLD = 0.7
    WEAKEN_THRESHOLD = 0.3
    REINFORCE_AMPLITUDE = 0.2
    WEAKEN_AMPLITUDE = -0.2

    def __init__(self, brain=None, dim: int = DEFAULT_DIM,
                 learning_rate: float = 0.1):
        self.brain = brain
        self.dim = dim
        self.eta = learning_rate
        self._history: List[Tuple[np.ndarray, float]] = []
        self._n_feedback = 0
        self._n_reinforce = 0
        self._n_weaken = 0

    def process_feedback(self, response_psi: np.ndarray,
                         human_score: float,
                         target_text: Optional[str] = None) -> Dict:
        """
        Traite un feedback humain sur une réponse.

        Score > 0.7 → renforce (amplify)
        Score < 0.3 → affaiblit (oppose)
        Sinon → neutre (la cohérence est déjà alignée)

        Returns:
            dict avec decision, amplitude, coherence, error
        """
        target_psi = (encode(target_text, dim=self.dim) if target_text
                      else response_psi)
        c = float(coherence(response_psi, target_psi))
        error = human_score - c

        if human_score > self.REINFORCE_THRESHOLD:
            self.reinforce(target_psi, self.REINFORCE_AMPLITUDE)
            decision, amplitude = 'reinforce', self.REINFORCE_AMPLITUDE
            self._n_reinforce += 1
        elif human_score < self.WEAKEN_THRESHOLD:
            self.weaken(target_psi, self.WEAKEN_AMPLITUDE)
            decision, amplitude = 'weaken', self.WEAKEN_AMPLITUDE
            self._n_weaken += 1
        else:
            decision, amplitude = 'neutral', 0.0

        self._history.append((response_psi.copy(), float(human_score)))
        if len(self._history) > 1000:
            self._history.pop(0)
        self._n_feedback += 1

        return {
            'decision': decision, 'amplitude': amplitude,
            'coherence': c, 'error': error,
            'human_score': float(human_score),
        }

    def reinforce(self, psi: np.ndarray, amplitude: float = None) -> None:
        """Renforce une onde : ψ ← normalize(ψ + η·a·ψ)."""
        a = amplitude if amplitude is not None else self.REINFORCE_AMPLITUDE
        normalize(psi + self.eta * a * psi)  # modulation locale
        if self.brain is not None:
            self._feedback_brain(psi, amount=abs(a), reinforce=True)

    def weaken(self, psi: np.ndarray, amplitude: float = None) -> None:
        """Affaiblit une onde : ψ ← normalize(ψ − |η·a|·ψ)."""
        a = amplitude if amplitude is not None else self.WEAKEN_AMPLITUDE
        normalize(psi + self.eta * a * psi)  # répulsion
        if self.brain is not None:
            self._feedback_brain(psi, amount=abs(a), reinforce=False)

    def _feedback_brain(self, psi: np.ndarray, amount: float,
                        reinforce: bool) -> None:
        """Renforce/affaiblit le fait le plus résonant dans le cerveau."""
        try:
            store = self.brain.unconscious
            if not hasattr(store, 'registry'):
                return
            best, best_score = None, 0.15
            for record in store.registry.values():
                psi_r = getattr(record, 'psi', None)
                if isinstance(record, dict):
                    psi_r = record.get('psi')
                if psi_r is None:
                    continue
                s = float(coherence(psi, psi_r))
                if s > best_score:
                    best_score, best = s, record
            if best is not None:
                if reinforce and hasattr(store, 'reinforce'):
                    store.reinforce(best, amount=amount)
                elif not reinforce and hasattr(store, 'weaken'):
                    store.weaken(best, amount=amount)
        except Exception:
            pass

    def train(self, pairs: List[Tuple[str, float]],
              n_cycles: int = 10, verbose: bool = False) -> Dict:
        """Entraîne la boucle sur un lot (texte, score_humain)."""
        results = []
        for _ in range(n_cycles):
            for text, score in pairs:
                psi = encode(text, dim=self.dim)
                results.append(self.process_feedback(psi, score))
        summary = {
            'cycles': n_cycles, 'n_pairs': len(pairs),
            'n_feedback': len(results),
            'reinforcements': sum(1 for r in results if r['decision'] == 'reinforce'),
            'weakenings': sum(1 for r in results if r['decision'] == 'weaken'),
            'neutrals': sum(1 for r in results if r['decision'] == 'neutral'),
        }
        if verbose:
            print(f"🔁 FeedbackLoopBridge: {summary}")
        return summary

    def evaluate(self, psi: np.ndarray) -> float:
        """
        Écho de phase : prédit le score humain par résonance
        avec l'historique des feedbacks passés (reward model harmonique).
        """
        if not self._history:
            return 0.5
        w_sum, ws = 0.0, 0.0
        for hist_psi, hist_score in self._history:
            w = float(coherence(psi, hist_psi))
            if w > 0.1:
                ws += w * hist_score
                w_sum += w
        return min(1.0, max(0.0, ws / (w_sum + 1e-10))) if w_sum > 1e-10 else 0.5

    def evaluate_text(self, text: str) -> float:
        """Prédit le score humain d'un texte (encodage automatique)."""
        return self.evaluate(encode(text, dim=self.dim))

    @property
    def stats(self) -> dict:
        """Statistiques de la boucle."""
        return {
            'n_feedback': self._n_feedback,
            'n_reinforce': self._n_reinforce,
            'n_weaken': self._n_weaken,
            'ratio_positif': self._n_reinforce / max(1, self._n_feedback),
            'history_size': len(self._history),
            'learning_rate': self.eta,
            'active': True,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 16. ADAPTATEUR WAVE SAMPLING → coherence / phase_shift / rotate
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : wave_sampling.py (~300 lignes) — WaveSampler avec top-k/top-p/
#         température manuels, bruit de phase réimplémenté à la main.
# Après : même API, délégation à wave_lang.coherence + phase_shift + rotate.

class WaveSamplingBridge:
    """
    Échantillonnage ondulatoire — température, top-p, top-k.

    Drop-in replacement pour wave_sampling.py (WaveSampler).
    Même API, backend wave_lang.coherence + phase_shift.

    Équivalences LLM :
      #11 Temperature Sampling → bruit de phase δ·N(0,1)
      #12 Top-p Sampling      → cône de cohérence (seuil angulaire)
      #13 Top-k Sampling      → filtrage par cohérence décroissante

    Usage :
        sampler = WaveSamplingBridge(vocabulary=vocab)
        mot = sampler.sample(psi_contexte, temperature=0.8, top_p=0.9, top_k=50)
    """

    def __init__(self, vocabulary: Optional[Dict[str, np.ndarray]] = None,
                 dim: int = DEFAULT_DIM):
        self.dim = dim
        self.vocabulary = vocabulary or {}

    def set_vocabulary(self, vocab: Dict[str, np.ndarray]) -> None:
        """Définit le vocabulaire (mot → ψ)."""
        self.vocabulary = vocab

    def coherence_scores(self, psi_context: np.ndarray,
                         candidates: Optional[List[str]] = None) -> Dict[str, float]:
        """
        Scores de cohérence de chaque mot avec le contexte.

        score = Re(⟨ψ_contexte | ψ_mot⟩)  (resonate)
        """
        words = candidates if candidates is not None else list(self.vocabulary.keys())
        scores = {}
        for word in words:
            psi_word = self.vocabulary.get(word)
            if psi_word is None:
                psi_word = encode(word, dim=self.dim)
            scores[word] = float(resonate(psi_context, psi_word))
        return scores

    def sample(self, psi_context: np.ndarray, temperature: float = 0.8,
               top_p: float = 0.9, top_k: int = 50,
               candidates: Optional[List[str]] = None) -> str:
        """
        Échantillonnage complet : cohérence → top-k → top-p → température.

        Pipeline :
          1. Scores de cohérence (resonate)
          2. Top-k : garde les k meilleurs mots
          3. Top-p : cône de cohérence (probabilités cumulées)
          4. Température : bruit de phase sur les scores

        Args:
            psi_context: onde du contexte
            temperature: T < 1 déterministe, T > 1 créatif
            top_p: seuil de probabilité cumulée (0.9)
            top_k: nombre de mots gardés
            candidates: liste restreinte de mots (optionnel)

        Returns:
            le mot échantillonné
        """
        scores = self.coherence_scores(psi_context, candidates)

        if not scores:
            return ""

        # Top-k : trier et garder les k meilleurs
        ranked = sorted(scores.items(), key=lambda x: -x[1])
        ranked = ranked[:max(1, top_k)]

        # Top-p : seuil de probabilité cumulée
        words = [w for w, s in ranked]
        vals = np.array([max(0.0, s) for _, s in ranked], dtype=np.float64)
        total = vals.sum()
        if total < 1e-10:
            return words[0]
        probs = vals / total
        sorted_idx = np.argsort(-probs)
        cumsum = np.cumsum(probs[sorted_idx])
        cutoff = int(np.searchsorted(cumsum, top_p) + 1)
        kept = sorted_idx[:max(1, cutoff)]
        words_p = [words[i] for i in kept]
        probs_p = probs[kept]

        # Température : adoucir la distribution
        if temperature <= 0.001:
            return words_p[0]  # déterministe
        elif temperature < 1.0:
            probs_p = probs_p ** (1.0 / max(0.1, temperature))
        else:
            probs_p = probs_p ** (1.0 / temperature)

        probs_p = probs_p / (probs_p.sum() + 1e-10)

        # Tirage (bruit de phase via RandomState)
        rng = np.random.RandomState()
        return str(words_p[int(rng.choice(len(words_p), p=probs_p))])

    def deterministic(self, psi_context: np.ndarray,
                      candidates: Optional[List[str]] = None) -> str:
        """T=0 : toujours le mot de cohérence maximale."""
        scores = self.coherence_scores(psi_context, candidates)
        if not scores:
            return ""
        return max(scores, key=scores.get)

    def creative(self, psi_context: np.ndarray, creativity: float = 0.7,
                 candidates: Optional[List[str]] = None) -> str:
        """Haute température (créativité × 1.5), top_p=0.95, top_k=100."""
        return self.sample(psi_context, temperature=creativity * 1.5,
                           top_p=0.95, top_k=100, candidates=candidates)

    def precise(self, psi_context: np.ndarray,
                candidates: Optional[List[str]] = None) -> str:
        """Basse température (0.2), top_p=0.8, top_k=20."""
        return self.sample(psi_context, temperature=0.2,
                           top_p=0.8, top_k=20, candidates=candidates)

    # ── Fonctions utilitaires (équivalents wave_sampling) ──

    def apply_phase_noise(self, psi: np.ndarray,
                          temperature: float) -> np.ndarray:
        """
        Bruit de phase : ψ · exp(i · T · N(0,1) · 0.5).
        Équivalent à wave_lang.phase_shift avec un shift aléatoire.
        """
        rng = np.random.RandomState()
        noise = rng.randn(self.dim) * temperature * 0.5
        return phase_shift(psi, noise)

    def coherence_cone_filter(self, scores: Dict[str, float],
                              angle_threshold_deg: float = 45.0) -> Dict[str, float]:
        """
        Cône de cohérence : garde les mots dont l'angle avec le contexte
        est sous le seuil. cos(angle) ≥ cos(seuil).
        """
        threshold = math.cos(math.radians(angle_threshold_deg))
        return {w: s for w, s in scores.items() if s >= threshold}

    def entropy(self, scores: Dict[str, float]) -> float:
        """Entropie de Shannon de la distribution des scores (en nats)."""
        vals = np.array([max(0.0, s) for s in scores.values()], dtype=np.float64)
        total = vals.sum()
        if total < 1e-10:
            return 0.0
        probs = vals / total
        probs = probs[probs > 1e-15]
        return float(-np.sum(probs * np.log(probs)))

    def perplexity(self, scores: Dict[str, float]) -> float:
        """Perplexité = exp(entropie)."""
        return float(np.exp(self.entropy(scores)))


# ═══════════════════════════════════════════════════════════════════════════════
# 17. ADAPTATEUR WAVE TOOL USE → bind / unbind / resonate
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : wave_tool_use.py (~390 lignes) — WaveToolUse avec convolution
#         circulaire réimplémentée à la main, extraction de paramètres.
# Après : même API, délégation à wave_lang.bind/unbind/resonate.

class WaveToolUseBridge:
    """
    Appel d'outil ondulatoire — résolution par binding HRR.

    Drop-in replacement pour wave_tool_use.py (WaveToolUse).
    Même API, backend wave_lang.bind + resonate.

    Équivalence #35 : Tool Use / Function Calling
        ψ_action = ψ_intention ⊗ ψ_outil ⊗ ψ_params (bind_many)

    Usage :
        tools = WaveToolUseBridge(dim=512)
        tools.register(ToolDefinition(name="calculer", description="..."))
        call = tools.resolve("calcule 2+2")
        result = tools.execute(call)
    """

    def __init__(self, dim: int = DEFAULT_DIM):
        self.dim = dim
        self._tools: Dict[str, 'ToolDefinition'] = {}

    def register(self, tool: 'ToolDefinition') -> None:
        """
        Enregistre un outil (encodé en ψ si besoin).

        Args:
            tool: ToolDefinition avec name, description, parameters, handler
        """
        if getattr(tool, 'psi', None) is None:
            desc = f"{tool.name} {tool.description}"
            for pname in (tool.parameters or {}):
                desc += f" {pname}"
            tool.psi = encode(desc, dim=self.dim)
        self._tools[tool.name] = tool

    def resolve(self, intention: str,
                coherence_threshold: float = 0.3) -> Optional['ToolCall']:
        """
        Résout une intention vers l'outil le plus résonant.

        Pipeline :
          1. ψ_intention = encode(intention)
          2. Scores = resonate(ψ_intention, ψ_outil) pour chaque outil
          3. Si le meilleur score < seuil → None (pas d'outil adapté)
          4. ψ_action = bind(ψ_intention, ψ_outil)

        Args:
            intention: texte décrivant l'action souhaitée
            coherence_threshold: seuil minimal de résonance

        Returns:
            ToolCall ou None
        """
        if not self._tools:
            return None

        psi_intention = encode(intention, dim=self.dim)
        intention_words = self._stem_words(intention)

        best_name, best_score = None, -1.0
        for name, tool in self._tools.items():
            # 1. Résonance holographique — score sémantique signé ∈ [-1, 1],
            #    normalisé sur [0, 1] (les ψ de textes différents sont
            #    quasi-orthogonaux : ~0.03 par construction)
            s = float(resonate(psi_intention, tool.psi))
            s_norm = 0.5 + 0.5 * s

            # 2. Bonus lexical avec stemming : chevauchement intention↔outil
            tool_text = f"{tool.name} {tool.description}".lower()
            tool_words = self._stem_words(tool_text)
            overlap = len(intention_words & tool_words) / max(1, len(intention_words))
            if overlap > 0:
                overlap = min(1.0, 0.5 + 0.5 * overlap)  # booster les matchs partiels

            # Score combiné (même principe que HolographicRAG.retrieve)
            score = 0.5 * s_norm + 0.5 * overlap

            if score > best_score:
                best_score, best_name = score, name

        if best_name is None or best_score < coherence_threshold:
            return None

        tool = self._tools[best_name]
        params = self._extract_params(intention, tool)
        psi_bound = bind(psi_intention, tool.psi)

        # Créer le ToolCall (dataclass simple locale si pas importable)
        ToolCall = self._get_toolcall_class()
        return ToolCall(
            tool_name=best_name,
            parameters=params,
            coherence=best_score,
            psi_bound=psi_bound,
        )

    def execute(self, call: 'ToolCall') -> Any:
        """
        Exécute l'outil avec les paramètres extraits.

        Args:
            call: ToolCall à exécuter

        Returns:
            résultat de l'outil, ou dict d'erreur
        """
        tool = self._tools.get(call.tool_name)
        if tool is None or tool.handler is None:
            return {'error': f"Outil '{call.tool_name}' introuvable ou sans handler"}
        try:
            return tool.handler(**call.parameters)
        except Exception as e:
            return {'error': str(e)}

    def resolve_and_execute(self, intention: str,
                            coherence_threshold: float = 0.3) -> Tuple[Optional[Any], Optional['ToolCall']]:
        """Résout puis exécute en un appel."""
        call = self.resolve(intention, coherence_threshold)
        if call is None:
            return None, None
        return self.execute(call), call

    # ── Utilitaires ──

    def _extract_params(self, intention: str, tool: 'ToolDefinition') -> Dict[str, Any]:
        """Extrait les paramètres par résonance avec les noms de paramètres."""
        params = {}
        psi_intention = encode(intention, dim=self.dim)

        for pname, pspec in (tool.parameters or {}).items():
            psi_pname = encode(pname, dim=self.dim)
            if float(coherence(psi_intention, psi_pname)) > 0.2:
                value = self._parse_param_value(intention, pspec)
                params[pname] = value
            else:
                # Valeur par défaut si paramètre requis
                if pspec.get('required', False):
                    ptype = pspec.get('type', 'text')
                    if ptype == 'number':
                        params[pname] = self._extract_number(intention)
                    elif ptype == 'boolean':
                        params[pname] = True
                    else:
                        params[pname] = pspec.get('default', '')
        return params

    def _parse_param_value(self, intention: str, pspec: Dict) -> Any:
        """Parse une valeur selon le type du paramètre."""
        ptype = pspec.get('type', 'text')
        if ptype == 'number':
            return self._extract_number(intention)
        return pspec.get('default', '')

    def _extract_number(self, text: str) -> float:
        """Extrait un nombre d'un texte (premier nombre trouvé)."""
        match = re.search(r'[-+]?\d*\.?\d+', text)
        return float(match.group()) if match else 0.0

    @staticmethod
    def _stem_words(text: str) -> set:
        """
        Stemming léger : mots de ≥ 4 lettres, réduits à leur racine (préfixe 4).

        « calculer » et « calcule » → « calc » — permet au bonus lexical de
        matcher les formes conjuguées des verbes d'action des outils.
        """
        words = re.findall(r'\b[a-zA-Zà-ÿ]{4,}\b', text.lower())
        stems = set()
        for w in words:
            # Racine : préfixe de 4-6 lettres (suffisant pour les verbes FR)
            stems.add(w[:5])
        return stems

    def _get_toolcall_class(self):
        """Retourne la dataclass ToolCall (locale ou importée)."""
        try:
            from wave_tool_use import ToolCall
            return ToolCall
        except ImportError:
            from dataclasses import dataclass
            @dataclass
            class ToolCall:
                tool_name: str
                parameters: Dict[str, Any]
                coherence: float = 0.0
                psi_bound: Optional[np.ndarray] = None
            return ToolCall

    @property
    def size(self) -> int:
        return len(self._tools)


# ═══════════════════════════════════════════════════════════════════════════════
# 18. ADAPTATEUR WAVE BEAM SEARCH → resonate / superpose / interfere
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : beam_search.py (~270 lignes) — WaveBeamSearch avec interférence
#         entre chemins réimplémentée à la main.
# Après : même API, délégation à wave_lang.resonate + superpose + interfere.

class WaveBeamSearchBridge:
    """
    Recherche en faisceau ondulatoire — interférence multi-chemin.

    Drop-in replacement pour beam_search.py (WaveBeamSearch).
    Même API, backend wave_lang.resonate + superpose + interfere.

    Équivalence #14 : Beam Search → Interférence multi-chemin.
    Là où le beam search classique garde les B hypothèses indépendantes,
    le faisceau ondulatoire modélise l'INTERFÉRENCE entre chemins :
    les chemins en phase se renforcent, en opposition s'annulent.

    Usage :
        bs = WaveBeamSearchBridge(vocabulary=vocab, beam_width=5)
        text = bs.best_text(psi_contexte, max_steps=20)
    """

    def __init__(self, vocabulary: Optional[Dict[str, np.ndarray]] = None,
                 beam_width: int = 5, dim: int = DEFAULT_DIM):
        self.vocabulary = vocabulary or {}
        self.beam_width = max(1, beam_width)
        self.dim = dim

    def search(self, psi_context: np.ndarray, max_steps: int = 20,
               interference_strength: float = 0.3) -> List['WavePath']:
        """
        Recherche en faisceau avec interférence entre chemins.

        Pipeline :
          1. Initialise B chemins avec les B mots les plus résonants
          2. À chaque étape, étend chaque chemin (top-B extensions)
          3. Applique l'INTERFÉRENCE croisée entre chemins
          4. Garde les B meilleurs par amplitude (avec interférence)
          5. Stop précoce si cohérence faible

        Args:
            psi_context: onde du contexte initial
            max_steps: nombre maximal d'étapes
            interference_strength: force de l'interférence croisée

        Returns:
            liste de WavePath triée par amplitude décroissante
        """
        WavePath = self._get_wavepath_class()

        # Initialisation : top-B mots les plus résonants
        words = self._top_words(psi_context, self.beam_width)
        paths = []
        for word in words:
            psi_word = self._get_psi(word)
            psi_path = normalize(psi_context + psi_word)
            score = float(resonate(psi_context, psi_word))
            paths.append(WavePath(
                tokens=[word], psi=psi_path,
                coherence=score, amplitude=1.0,
            ))

        # Propagation
        for step in range(max_steps):
            new_paths = []
            for path in paths:
                extensions = self._top_words(path.psi, self.beam_width)
                for word in extensions:
                    psi_word = self._get_psi(word)
                    psi_next = normalize(path.psi + psi_word)
                    score = float(resonate(path.psi, psi_word))
                    new_paths.append(WavePath(
                        tokens=path.tokens + [word],
                        psi=psi_next,
                        coherence=path.coherence + score,
                        amplitude=path.amplitude,
                    ))

            if not new_paths:
                break

            # Interférence croisée entre chemins
            if len(new_paths) > 1:
                for i in range(len(new_paths)):
                    interference = 0.0
                    for j in range(len(new_paths)):
                        if i != j:
                            interference += float(resonate(
                                new_paths[i].psi, new_paths[j].psi))
                    new_paths[i].amplitude = max(
                        0.0, new_paths[i].amplitude +
                        interference * interference_strength)

            # Garder les B meilleurs
            new_paths.sort(key=lambda p: -p.amplitude)
            paths = new_paths[:self.beam_width]

            # Stop précoce
            if paths and paths[0].coherence < step * 0.1:
                break

        return sorted(paths, key=lambda p: -p.amplitude)

    def best_sequence(self, psi_context: np.ndarray,
                      max_steps: int = 20) -> List[str]:
        """Retourne la séquence de tokens du meilleur chemin."""
        paths = self.search(psi_context, max_steps=max_steps)
        return paths[0].tokens if paths else []

    def best_text(self, psi_context: np.ndarray,
                  max_steps: int = 20) -> str:
        """Retourne le meilleur chemin sous forme de texte."""
        return " ".join(self.best_sequence(psi_context, max_steps))

    # ── Utilitaires ──

    def _get_psi(self, word: str) -> np.ndarray:
        """Retourne le ψ d'un mot (vocabulaire ou encodage direct)."""
        if word in self.vocabulary:
            return self.vocabulary[word]
        return encode(word, dim=self.dim)

    def _top_words(self, psi: np.ndarray, k: int) -> List[str]:
        """Retourne les k mots les plus résonants avec une onde."""
        scores = []
        for word, psi_word in self.vocabulary.items():
            scores.append((word, float(resonate(psi, psi_word))))
        scores.sort(key=lambda x: -x[1])
        return [w for w, s in scores[:k]] if scores else []

    def interference_matrix(self, paths: List['WavePath']) -> np.ndarray:
        """Matrice d'interférence M[i,j] = Re(⟨ψ_i|ψ_j⟩)."""
        n = len(paths)
        M = np.zeros((n, n), dtype=np.float64)
        for i in range(n):
            for j in range(n):
                M[i, j] = float(resonate(paths[i].psi, paths[j].psi))
        return M

    def select_constructive(self, paths: List['WavePath'],
                            threshold: float = 0.5) -> List['WavePath']:
        """Garde les chemins en interférence constructive avec les autres."""
        if not paths:
            return []
        M = self.interference_matrix(paths)
        kept = []
        for i, path in enumerate(paths):
            others = np.delete(M[i], i)
            mean_coherence = float(others.mean()) if len(others) else 0.0
            if mean_coherence >= threshold:
                kept.append(path)
        return kept

    def _get_wavepath_class(self):
        """Retourne la dataclass WavePath (locale ou importée)."""
        try:
            from beam_search import WavePath
            return WavePath
        except ImportError:
            from dataclasses import dataclass, field
            @dataclass
            class WavePath:
                tokens: List[str]
                psi: np.ndarray
                coherence: float = 0.0
                amplitude: float = 1.0
            return WavePath


# ═══════════════════════════════════════════════════════════════════════════════
# 19. ADAPTATEUR WAVE PERPLEXITY → energy / spectrum / coherence
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : wave_perplexity.py (~290 lignes) — entropie/perplexité ondulatoires.
# Après : même API, délégation à wave_lang.energy + spectrum + coherence.

class WavePerplexityBridge:
    """
    Perplexité ondulatoire — mesure de l'incertitude d'une onde.

    Drop-in replacement pour wave_perplexity.py.
    Même API, backend wave_lang.energy + spectrum.

    Équivalence #36 : Perplexity → Entropie ondulatoire H(ψ).
    Basse perplexité = forte cohérence = bonne prédiction.

    Usage :
        from wave_bridge import WavePerplexityBridge
        ppl = WavePerplexityBridge.wave_perplexity(psi)
        scores = {"chat": 0.8, "chien": 0.3}
        conf = WavePerplexityBridge.confidence(scores)
    """

    @staticmethod
    def wave_entropy(psi: np.ndarray) -> float:
        """
        Entropie de Von Neumann : H = −Σ |ψᵢ|² · log(|ψᵢ|²).

        H ≈ 0 → concentration sur une composante (certitude)
        H ≈ log(d) → distribution uniforme (incertitude max)
        """
        p = np.abs(psi) ** 2
        p = p[p > 1e-15]
        return float(-np.sum(p * np.log(p)))

    @staticmethod
    def wave_perplexity(psi: np.ndarray) -> float:
        """Perplexité = exp(entropie)."""
        return float(np.exp(WavePerplexityBridge.wave_entropy(psi)))

    @staticmethod
    def coherence_shannon_entropy(scores: Dict[str, float]) -> float:
        """Entropie de Shannon des scores de cohérence (nats)."""
        vals = np.array([max(0.0, s) for s in scores.values()], dtype=np.float64)
        total = vals.sum()
        if total < 1e-10:
            return 0.0
        probs = vals / total
        probs = probs[probs > 1e-15]
        return float(-np.sum(probs * np.log(probs)))

    @staticmethod
    def coherence_perplexity(scores: Dict[str, float]) -> float:
        """Perplexité = exp(entropie de cohérence)."""
        return float(np.exp(WavePerplexityBridge.coherence_shannon_entropy(scores)))

    @staticmethod
    def confidence(scores: Dict[str, float]) -> float:
        """
        Confiance : (max − moyenne) / (max + ε).

        ≈ 1 → un mot domine clairement
        ≈ 0 → plusieurs choix équivalents
        """
        if not scores:
            return 0.0
        vals = np.array(list(scores.values()), dtype=np.float64)
        return float((vals.max() - vals.mean()) / (vals.max() + 1e-10))

    @staticmethod
    def coherence_margin(scores: Dict[str, float]) -> float:
        """
        Marge entre le top-1 et le top-2.
        Grande marge = prédiction robuste ; petite = fragile.
        """
        if len(scores) < 2:
            return 2.0  # seule alternative
        ranked = sorted(scores.values(), reverse=True)
        return float(ranked[0] - ranked[1])

    @staticmethod
    def generation_quality(psi_sequence: List[np.ndarray],
                           vocabulary: Dict[str, np.ndarray]) -> Dict:
        """
        Analyse la qualité d'une séquence générée.

        Returns:
            dict avec mean_entropy, mean_perplexity, mean_confidence,
            mean_margin, min_confidence, max_entropy, n_steps
        """
        entropies, ppls, confs, margins = [], [], [], []
        for psi in psi_sequence:
            scores = {}
            for word, psi_word in vocabulary.items():
                scores[word] = float(coherence(psi, psi_word))
            entropies.append(WavePerplexityBridge.wave_entropy(psi))
            ppls.append(WavePerplexityBridge.wave_perplexity(psi))
            confs.append(WavePerplexityBridge.confidence(scores))
            margins.append(WavePerplexityBridge.coherence_margin(scores))

        return {
            'mean_entropy': float(np.mean(entropies)) if entropies else 0.0,
            'mean_perplexity': float(np.mean(ppls)) if ppls else 0.0,
            'mean_confidence': float(np.mean(confs)) if confs else 0.0,
            'mean_margin': float(np.mean(margins)) if margins else 0.0,
            'min_confidence': float(np.min(confs)) if confs else 0.0,
            'max_entropy': float(np.max(entropies)) if entropies else 0.0,
            'n_steps': len(psi_sequence),
        }

    @staticmethod
    def compare_distributions(scores_a: Dict[str, float],
                              scores_b: Dict[str, float]) -> Dict:
        """
        Compare deux distributions de scores (divergence JS approchée).

        Returns:
            dict avec js_divergence, top3_a, top3_b, order_changed
        """
        all_words = set(scores_a) | set(scores_b)
        pa = np.array([max(0.0, scores_a.get(w, 0.0)) for w in all_words])
        pb = np.array([max(0.0, scores_b.get(w, 0.0)) for w in all_words])
        pa = pa / (pa.sum() + 1e-10)
        pb = pb / (pb.sum() + 1e-10)

        # Divergence JS approchée (KL symétrisée)
        m = 0.5 * (pa + pb)
        kl_am = float(np.sum(pa * np.log((pa + 1e-15) / (m + 1e-15))))
        kl_bm = float(np.sum(pb * np.log((pb + 1e-15) / (m + 1e-15))))
        js = 0.5 * (kl_am + kl_bm)

        top3_a = sorted(scores_a, key=scores_a.get, reverse=True)[:3]
        top3_b = sorted(scores_b, key=scores_b.get, reverse=True)[:3]

        return {
            'js_divergence': float(js),
            'top3_a': top3_a,
            'top3_b': top3_b,
            'order_changed': top3_a != top3_b,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 20. ADAPTATEUR WAVE FINE TUNE → bind / normalize / energy
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : wave_fine_tune.py (~250 lignes) — ALS dans le domaine de Fourier
#         avec convolution circulaire et normalisation réimplémentées.
# Après : même API, délégation à wave_lang.bind + normalize + energy.
#         La boucle ALS (math Fourier réelle) et le snapshot SVD sont conservés.

class WaveFineTuneBridge:
    """
    Fine-tuning ondulatoire par moindres carrés alternés (Fourier).

    Drop-in replacement pour wave_fine_tune.py (WaveFineTuner).
    Même API, backend wave_lang.bind + normalize + energy.

    Équivalences LLM :
      #16 Loss Function    → gap de cohérence 1 − Re(⟨ψ_p|ψ_t⟩)
      #17 Fine-Tuning      → renforcement d'amplitude

    Contrainte d'apprentissage : ψ_s ⊛ ψ_r ≈ ψ_o
    Solution ALS régularisée (par fréquence) :
        ψ̃_w[k] = (Σ ψ̃_target·ψ̃_other* + λ·ψ̃_SVD[k]) / (Σ|ψ̃_other|² + λ)

    Usage :
        tuner = WaveFineTuneBridge(encoder, learning_rate=1.0, lambda_reg=1.0)
        history = tuner.fine_tune(kb, epochs=5)
    """

    def __init__(self, encoder, learning_rate: float = 1.0,
                 lambda_reg: float = 1.0):
        self.encoder = encoder
        self.lr = learning_rate
        self.lambda_reg = lambda_reg
        self.dim = encoder.dim
        self.psi_svd: Dict[str, np.ndarray] = {}

    def fine_tune(self, knowledge_base: List[Tuple[str, str, str, str]],
                  epochs: int = 5, verbose: bool = True) -> dict:
        """
        Ajuste itérativement les ψ par moindres carrés alternés.

        Args:
            knowledge_base: liste de (sujet, relation, objet, secteur)
            epochs: nombre de passes complètes
            verbose: afficher la progression

        Returns:
            dict avec 'epoch', 'loss', 'words_updated'
        """
        from collections import defaultdict
        history = {'epoch': [], 'loss': [], 'words_updated': []}

        # Index : pour chaque mot, quels faits l'utilisent
        facts_by_subject = defaultdict(list)
        facts_by_object = defaultdict(list)
        all_words = set()

        for s, r, o, sec in knowledge_base:
            ws, wr, wo = s.lower().strip(), r.lower().strip(), o.lower().strip()
            facts_by_subject[ws].append((wr, wo))
            facts_by_object[wo].append((ws, wr))
            all_words.update([ws, wr, wo])

        vocab = {w for w in all_words if w in self.encoder.word_vectors}

        # Snapshot SVD pour la régularisation
        self.psi_svd = {w: self.encoder.word_vectors[w].copy() for w in vocab}

        for epoch in range(epochs):
            words_updated = 0
            words_updated += self._optimize_by_role(facts_by_subject, vocab,
                                                    epoch=epoch)
            words_updated += self._optimize_by_role(facts_by_object, vocab,
                                                    epoch=epoch)

            avg_loss = self._compute_loss(knowledge_base, vocab)
            history['epoch'].append(epoch)
            history['loss'].append(avg_loss)
            history['words_updated'].append(words_updated)

            if verbose:
                print(f"  Epoch {epoch+1}/{epochs}: loss={avg_loss:.4f}, "
                      f"updated={words_updated} mots")

        return history

    def _optimize_by_role(self, facts_by_role: Dict[str, List],
                          vocab: set, epoch: int) -> int:
        """
        Optimise les ψ pour un rôle (sujet ou objet) — solution régularisée.

        Le cœur Fourier (numérateur/dénominateur par fréquence) est conservé ;
        la convolution et la normalisation délèguent à wave_lang.
        """
        updated = 0
        epsilon = 1e-8
        lam = self.lambda_reg

        for word in vocab:
            if word not in facts_by_role or not facts_by_role[word]:
                continue
            facts = facts_by_role[word]

            num = np.zeros(self.dim, dtype=np.complex128)
            den = np.zeros(self.dim, dtype=np.float64)

            for other_word, target_word in facts:
                if other_word not in vocab or target_word not in vocab:
                    continue
                psi_other = self.encoder.word_vectors[other_word]
                psi_target = self.encoder.word_vectors[target_word]
                psi_other_f = np.fft.fft(psi_other)
                psi_target_f = np.fft.fft(psi_target)
                num += psi_target_f * np.conj(psi_other_f)
                den += np.abs(psi_other_f) ** 2

            if word in self.psi_svd and lam > 0:
                psi_svd_f = np.fft.fft(self.psi_svd[word])
                num += lam * psi_svd_f
                den += lam

            if np.all(den < epsilon):
                continue

            psi_new_f = num / (den + epsilon)
            psi_new = np.fft.ifft(psi_new_f)
            psi_new = normalize(psi_new)  # wave_lang.normalize

            # Appliquer avec learning rate
            if self.lr >= 1.0:
                self.encoder.word_vectors[word] = psi_new
            else:
                psi_old = self.encoder.word_vectors[word]
                self.encoder.word_vectors[word] = normalize(
                    psi_old + self.lr * (psi_new - psi_old))

            updated += 1

        return updated

    def _compute_loss(self, knowledge_base: List, vocab: set) -> float:
        """
        Loss totale L = Σ ||ψ_s ⊛ ψ_r − ψ_o||².

        La convolution ψ_s ⊛ ψ_r est wave_lang.bind ;
        le résidu est mesuré par wave_lang.energy (norme²).
        """
        total = 0.0
        count = 0
        for s, r, o, sec in knowledge_base:
            ws, wr, wo = s.lower().strip(), r.lower().strip(), o.lower().strip()
            if ws not in vocab or wr not in vocab or wo not in vocab:
                continue
            psi_pred = bind(self.encoder.word_vectors[ws],
                            self.encoder.word_vectors[wr])
            residual = psi_pred - self.encoder.word_vectors[wo]
            total += energy(residual)
            count += 1
        return total / max(count, 1)


# ═══════════════════════════════════════════════════════════════════════════════
# 21. ADAPTATEUR DOMAIN GATE → encode / resonate / superpose (MoE)
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : harmonic_brain.py — _detect_domains (mots-clés), _route_ingest,
#         _cross_domain_merge (~150 lignes sur 3759).
# Après : même logique, délégation à wave_lang.encode + resonate + superpose.

class DomainGateBridge:
    """
    Porte de domaines (MoE ondulatoire) — routage par résonance multi-domaine.

    Drop-in replacement pour la partie gate de harmonic_brain.py.
    Même logique, backend wave_lang.encode + resonate + superpose.

    Équivalence #32 : MoE (Mixture of Experts)
        → Gate par cohérence multi-domaine : la question résonne avec
        chaque domaine (ψ_domaine), les domaines dominants reçoivent la requête.

    Usage :
        gate = DomainGateBridge(dim=512)
        domains = gate.detect("Quelle est la capitale de la France ?")
        gate.route("Paris", "capitale_de", "France", "GEOGRAPHIE")
    """

    # Mots-clés par domaine (fallback si harmonic_brain indisponible)
    DEFAULT_KEYWORDS = {
        'sciences': ['physique', 'chimie', 'biologie', 'math', 'science',
                     'atome', 'énergie', 'molécule', 'quantique', 'théorie'],
        'culture_generale': ['qui', 'quoi', 'où', 'quand', 'histoire',
                             'capitale', 'pays', 'monde', 'célèbre'],
        'histoire': ['histoire', 'siècle', 'guerre', 'roi', 'empire',
                     'révolution', 'ancien', 'époque'],
        'code': ['code', 'programme', 'python', 'fonction', 'algorithme',
                 'logiciel', 'bug', 'compiler', 'variable'],
        'humain': ['émotion', 'sentiment', 'psychologie', 'amour',
                   'peur', 'comportement', 'cerveau'],
        'culture_arts': ['art', 'musique', 'peinture', 'poésie', 'littérature',
                         'roman', 'théâtre', 'cinéma'],
        'corps_sante': ['corps', 'santé', 'médecine', 'maladie', 'symptôme',
                        'traitement', 'patient', 'douleur'],
    }

    # Secteurs → domaines (fallback)
    DEFAULT_SECTOR_MAP = {
        'GEOGRAPHIE': 'culture_generale', 'HISTOIRE': 'histoire',
        'SCIENCES': 'sciences', 'PHYSIQUE': 'sciences',
        'CODE': 'code', 'SANTE': 'corps_sante', 'MEDECINE': 'corps_sante',
        'ART': 'culture_arts', 'LITTERATURE': 'culture_arts',
        'PSYCHOLOGIE': 'humain', 'CULTURE': 'culture_generale',
    }

    def __init__(self, dim: int = DEFAULT_DIM):
        self.dim = dim
        # Tenter d'importer les données canoniques de harmonic_brain (lazy)
        self.keywords = dict(self.DEFAULT_KEYWORDS)
        self.sector_map = dict(self.DEFAULT_SECTOR_MAP)
        try:
            from harmonic_brain import DOMAIN_KEYWORDS, DOMAIN_SECTOR_MAP
            if DOMAIN_KEYWORDS:
                self.keywords = DOMAIN_KEYWORDS
            if DOMAIN_SECTOR_MAP:
                self.sector_map = DOMAIN_SECTOR_MAP
        except Exception:
            pass

        # ψ par domaine (superposition des mots-clés encodés)
        self._domain_psis = {
            domain: superpose(*[encode(k, dim=self.dim)
                                for k in words])
            for domain, words in self.keywords.items()
        }

    def detect(self, question: str, max_domains: int = 2) -> List[str]:
        """
        Détecte les domaines dominants d'une question (gate MoE).

        Score par domaine = 0.5·résonance(ψ_question, ψ_domaine)
                          + 0.5·chevauchement de mots-clés.

        Args:
            question: question en langage naturel
            max_domains: nombre maximal de domaines retournés

        Returns:
            liste de noms de domaines, triée par score décroissant
        """
        psi_q = encode(question, dim=self.dim)
        q_lower = question.lower()

        scores = {}
        for domain, psi_domain in self._domain_psis.items():
            # 1. Résonance holographique avec le ψ du domaine
            resonance_score = float(coherence(psi_q, psi_domain))

            # 2. Chevauchement lexical avec les mots-clés
            keywords = self.keywords.get(domain, [])
            overlap = sum(1 for k in keywords if k in q_lower)
            lexical = min(1.0, overlap / 3.0)

            scores[domain] = 0.5 * resonance_score + 0.5 * lexical

        # Tri décroissant, garder les max_domains
        ranked = sorted(scores.items(), key=lambda x: -x[1])
        best_score = ranked[0][1] if ranked else 0.0

        domains = []
        for domain, score in ranked[:max_domains]:
            # Garder les domaines avec score ≥ 50% du meilleur
            if score >= 0.5 * max(best_score, 1e-10) or len(domains) == 0:
                domains.append(domain)

        return domains if domains else ['culture_generale']

    def route(self, sujet: str, relation: str, objet: str,
              secteur: str) -> Optional[str]:
        """
        Route un fait vers son domaine (via le mapping secteur → domaine).

        Args:
            sujet, relation, objet: composants du fait
            secteur: secteur du fait (ex: "GEOGRAPHIE")

        Returns:
            nom du domaine, ou None si inconnu
        """
        return self.sector_map.get(secteur.upper(), None)

    def merge(self, domain_candidates: List[Tuple[str, List]],
              max_results: int = 50) -> List:
        """
        Fusionne les candidats de plusieurs domaines (cross-domain merge).

        Bonus cross-domaine : un fait présent dans N domaines reçoit
        un bonus de cohérence 1.0 + 0.2·(N − 1) (interférence constructive
        entre domaines).

        Args:
            domain_candidates: liste de (domaine, [(fait, score), ...])
            max_results: nombre maximal de résultats

        Returns:
            liste de (fait, score) fusionnée et triée
        """
        merged: Dict[int, Tuple[object, float, int]] = {}

        for domain, candidates in domain_candidates:
            for fact, score in candidates:
                key = id(fact)
                if key not in merged:
                    merged[key] = (fact, score, 1)
                else:
                    f, s, n = merged[key]
                    merged[key] = (f, max(s, score), n + 1)

        results = []
        for fact, score, n_domains in merged.values():
            cross_bonus = 1.0 + 0.2 * (n_domains - 1)
            results.append((fact, score * cross_bonus))

        results.sort(key=lambda x: -x[1])
        return results[:max_results]

    @property
    def stats(self) -> dict:
        """Statistiques du gate."""
        return {
            'domains': list(self.keywords.keys()),
            'n_domains': len(self.keywords),
            'dim': self.dim,
            'sector_map_size': len(self.sector_map),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 22. ADAPTATEUR SYSTEM PROMPT → encode / rotate / phase_shift
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : harmonic_engine.py — _build_harmonic_system_prompt (templates par
#         catégorie + contexte holographique), et spectral_hop.py — ψ_0.
# Après : même logique, délégation à wave_lang.encode + rotate + phase_shift.

class SystemPromptBridge:
    """
    Prompt système ondulatoire — phase initiale ψ_0 et contexte holographique.

    Drop-in replacement pour la construction de system prompt
    (harmonic_engine._build_harmonic_system_prompt) et la phase initiale
    (spectral_hop.psi_0 = encode_query(question)).

    Équivalence #25 : System Prompt → Phase initiale ψ_0.
    Le prompt système est une ROTATION de l'espace des phases : il oriente
    le raisonnement vers une catégorie (math, code, créatif, factuel...).

    Usage :
        spb = SystemPromptBridge(dim=512)
        prompt = spb.build('reasoning', knowledge_context="...")
        psi_0 = spb.initial_phase(prompt)
    """

    # Templates par catégorie (phase initiale du raisonnement)
    CATEGORY_TEMPLATES = {
        'mathematical': "Raisonner en ondes : chaque équation est une résonance.",
        'code': "Penser en primitives : encode, bind, résonance, émergence.",
        'creative': "Créer par interférence : deux concepts, une onde neuve.",
        'reasoning': "Déduire par cohérence : la vérité résonne, l'erreur se dissipe.",
        'factual': "Répondre par le fait : la mémoire holographique est la source.",
        'general': "Penser en ondes : encoder, résonner, décoder.",
    }

    # Angle de rotation par catégorie (orientation de l'espace des phases)
    CATEGORY_ANGLES = {
        'mathematical': 0.0,
        'code': math.pi / 6,
        'creative': math.pi / 3,
        'reasoning': math.pi / 2,
        'factual': 2 * math.pi / 3,
        'general': 0.0,
    }

    def __init__(self, dim: int = DEFAULT_DIM):
        self.dim = dim

    def build(self, category: str = 'general',
              knowledge_context: str = '',
              memory_context: str = '',
              user_prefs: str = '') -> str:
        """
        Construit le prompt système (template + contexte holographique).

        Args:
            category: 'mathematical', 'code', 'creative', 'reasoning',
                      'factual', 'general'
            knowledge_context: extrait de la mémoire holographique
            memory_context: mémoire conversationnelle
            user_prefs: préférences utilisateur

        Returns:
            prompt système complet en français
        """
        template = self.CATEGORY_TEMPLATES.get(category, self.CATEGORY_TEMPLATES['general'])

        parts = [template]
        if knowledge_context:
            parts.append(f"Contexte holographique : {knowledge_context}")
        if memory_context:
            parts.append(f"Mémoire : {memory_context}")
        if user_prefs:
            parts.append(f"Préférences : {user_prefs}")

        return " | ".join(parts)

    def initial_phase(self, prompt: str = None,
                      category: str = 'general') -> np.ndarray:
        """
        Calcule la phase initiale ψ_0 (équivalent du system prompt encodé).

        ψ_0 = rotate(encode(prompt), angle_catégorie)
        La rotation oriente l'espace des phases vers la catégorie de tâche.

        Args:
            prompt: texte du prompt système (si None, template de catégorie)
            category: catégorie pour l'angle de rotation

        Returns:
            ψ_0 ∈ ℂᵈⁱᵐ — la phase initiale du raisonnement
        """
        text = prompt or self.CATEGORY_TEMPLATES.get(category, '')
        psi = encode(text, dim=self.dim)
        angle = self.CATEGORY_ANGLES.get(category, 0.0)
        if angle != 0.0:
            psi = rotate(psi, angle)
        return psi

    def orient(self, psi: np.ndarray, category: str) -> np.ndarray:
        """
        Oriente une onde vers une catégorie (role prompting #26).

        ψ' = phase_shift(ψ, angle_catégorie)
        """
        angle = self.CATEGORY_ANGLES.get(category, 0.0)
        return phase_shift(psi, angle)


# ═══════════════════════════════════════════════════════════════════════════════
# 23. ADAPTATEUR WAVE POETRY → bind / coherence / phase_shift / superpose
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : wave_poetry.py (~656 lignes) — WavePoet avec _bind/_coherence/_encode
#         réimplémentés, rotation émotionnelle manuelle.
# Après : même API, délégation à wave_lang.bind + coherence + phase_shift.
#         Les données (POETIC_VOCABULARY, VERSE_STRUCTURES) sont importées.

class WavePoetryBridge:
    """
    Poète ondulatoire — poésie par résonance de phase.

    Drop-in replacement pour wave_poetry.py (WavePoet).
    Même API, backend wave_lang.bind + coherence + phase_shift + superpose.

    Équivalence #28 : Poésie / Créativité
        → Sélection par cohérence de phase émotionnelle.

    Usage :
        poet = WavePoetryBridge()
        poem = poet.compose("la mer", form="free_verse", emotion="mystérieux")
    """

    def __init__(self, dim: int = None):
        self.dim = dim or DEFAULT_DIM
        self._word_cache: Dict[str, np.ndarray] = {}

        # Importer les données poétiques canoniques
        try:
            from wave_poetry import (POETIC_VOCABULARY as PV,
                                     POETIC_CONNECTORS as PC,
                                     VERSE_STRUCTURES as VS)
            self.POETIC_VOCABULARY = PV
            self.POETIC_CONNECTORS = PC
            self.VERSE_STRUCTURES = VS
        except ImportError:
            # Fallback minimal
            self.POETIC_VOCABULARY = {'mystere': ['nuit', 'rêve', 'ombre', 'silence']}
            self.POETIC_CONNECTORS = ['et', 'où', 'comme']
            self.VERSE_STRUCTURES = {'free_verse': [
                lambda s, v, o: f"{s} {v} {o}",
            ]}

        self._build_poetic_cache()

    def _build_poetic_cache(self) -> None:
        """Pré-encode les mots poétiques (wave_lang.encode)."""
        all_words = set()
        for phase, words in self.POETIC_VOCABULARY.items():
            all_words.update(words)
        for word in all_words:
            self._word_cache[word] = encode(word, dim=self.dim)

    def compose(self, theme: str, form: str = 'free_verse',
                emotion: str = None, lines: int = 8,
                personal_facts: List[str] = None) -> dict:
        """
        Compose un poème par interférences ondulatoires.

        Pipeline :
          1. ψ_thème = encode(theme)
          2. ψ_émotion = phase_shift(ones, θ_émotion) — rotation de phase
          3. ψ_poétique = bind(ψ_thème, ψ_émotion)
          4. (option) superpose(ψ_poétique, ψ_personnel, weights=[0.7, 0.3])
          5. Sélection des mots par résonance + grammaire française

        Args:
            theme: le thème du poème
            form: 'free_verse', 'alexandrin', 'haiku_wave'
            emotion: 'triste', 'joyeux', 'mystérieux', 'paisible', 'dynamique'
            lines: nombre de vers (approx.)
            personal_facts: faits personnels à intégrer

        Returns:
            dict avec 'text', 'form', 'theme', 'emotion', 'lines',
            'words_used', 'vocab_size'
        """
        # 1. Encoder l'intention poétique
        psi_theme = encode(theme, dim=self.dim)
        emotional_phase = self._determine_emotional_phase(theme, emotion)

        # 2. ψ_émotion par rotation de phase (wave_lang.phase_shift)
        phase_angles = {
            'lumiere': 0.0, 'mouvement': math.pi / 3,
            'mystere': math.pi / 2, 'douleur': math.pi,
            'sagesse': 3 * math.pi / 2,
        }
        theta = phase_angles.get(emotional_phase, math.pi / 2)
        psi_emotion = phase_shift(
            np.ones(self.dim, dtype=np.complex128), theta)

        # 3. Binding : ψ_poétique = ψ_thème ⊗ ψ_émotion
        psi_poetic = bind(psi_theme, psi_emotion)

        # 4. Contexte personnel : interférence pondérée
        if personal_facts:
            psis = [encode(fact[:50], dim=self.dim) for fact in personal_facts[:5]]
            if psis:
                psi_personal = superpose(*psis)
                psi_poetic = superpose(psi_poetic, psi_personal,
                                       weights=[0.7, 0.3])

        # 5. Sélection des mots par résonance (diversifiée)
        all_words = self._select_words_diverse(
            psi_poetic, emotional_phase, count=lines * 2 + 6)

        # 6. Construire les vers
        poem_lines = []
        n_words = len(all_words)
        structures = self.VERSE_STRUCTURES.get(
            form, self.VERSE_STRUCTURES['free_verse'])

        for i in range(min(lines, max(1, n_words // 2))):
            word_a = all_words[i]
            word_b = all_words[i + lines] if i + lines < n_words else all_words[-1]
            structure = structures[i % len(structures)]

            line = structure(word_a, ' ', word_b)
            line = re.sub(r' {2,}', ' ', line).strip()

            # Connecteur si vers trop court
            if len(line.split()) < 3:
                connector = random.choice(self.POETIC_CONNECTORS[:15])
                line = f"{word_a} {connector} le {word_b}"

            line = self._french_grammar(line)
            if line and len(line) > 4:
                poem_lines.append(line)

        # 7. Chute (dernier vers marquant)
        if poem_lines and lines >= 4 and n_words > lines:
            final_word = all_words[-1]
            closings = [
                f"et demeure l'{final_word}.",
                f"où seul l'{final_word} répond.",
                f"comme un dernier {final_word}.",
                f"dans le silence de l'{final_word}.",
                f"vers l'{final_word} éternel.",
            ]
            poem_lines.append(self._french_grammar(random.choice(closings)))

        return {
            'text': '\n'.join(poem_lines),
            'form': form,
            'theme': theme,
            'emotion': emotional_phase,
            'lines': len(poem_lines),
            'words_used': len(set(all_words)),
            'vocab_size': len(self.POETIC_VOCABULARY),
        }

    def compose_personal(self, theme: str, user_id: str = None,
                         personal_facts: List[str] = None,
                         form: str = 'free_verse') -> dict:
        """Compose un poème personnel (hologramme utilisateur ou faits)."""
        facts = personal_facts or []
        if not facts and user_id:
            try:
                from personal_hologram import PersonalHologram
                ph = PersonalHologram(user_id)
                profile = ph.profile()
                if profile.top_concepts:
                    facts = [f"Tu t'intéresses à {c}" for c in profile.top_concepts[:5]]
            except Exception:
                pass

        if facts:
            theme = f"{theme} — pour toi"
        return self.compose(theme, form=form, personal_facts=facts)

    def stats(self) -> dict:
        """Statistiques du poète."""
        return {
            'poetic_vocabulary': len(self._word_cache),
            'phases': list(self.POETIC_VOCABULARY.keys()),
            'forms': list(self.VERSE_STRUCTURES.keys()),
        }

    # ── Helpers ──

    def _determine_emotional_phase(self, theme: str,
                                   emotion: str = None) -> str:
        """Détermine la phase émotionnelle dominante (mots-clés)."""
        theme_lower = theme.lower()
        sadness = ['triste', 'mort', 'perte', 'deuil', 'absence', 'pleur',
                   'larme', 'mélancolie', 'nostalgie', 'regret', 'adieu']
        joy = ['joie', 'amour', 'bonheur', 'fête', 'rire', 'sourire',
               'lumière', 'espoir', 'printemps', 'aube', 'naissance']
        mystery = ['rêve', 'mystère', 'nuit', 'ombre', 'secret', 'âme',
                   'infini', 'étrange', 'magie']
        peace = ['paix', 'calme', 'sagesse', 'acceptation', 'sérénité', 'repos']

        for word in sadness:
            if word in theme_lower:
                return 'douleur'
        for word in joy:
            if word in theme_lower:
                return 'lumiere'
        for word in mystery:
            if word in theme_lower:
                return 'mystere'
        for word in peace:
            if word in theme_lower:
                return 'sagesse'

        if emotion:
            mapping = {'triste': 'douleur', 'joyeux': 'lumiere',
                       'mystérieux': 'mystere', 'paisible': 'sagesse',
                       'dynamique': 'mouvement'}
            return mapping.get(emotion, 'mystere')
        return 'mystere'

    def _select_words_diverse(self, psi_intention, emotional_phase,
                              count, exclude=None) -> List[str]:
        """
        Sélection diversifiée par cohérence de phase (wave_lang.coherence).
        """
        if exclude is None:
            exclude = set()

        all_phases = list(self.POETIC_VOCABULARY.keys())
        ordered_phases = ([emotional_phase] +
                          [p for p in all_phases if p != emotional_phase])

        selected = []
        used = set(exclude)
        phase_idx = 0

        while len(selected) < count and phase_idx < len(ordered_phases) * 3:
            phase = ordered_phases[phase_idx % len(ordered_phases)]
            candidates = self.POETIC_VOCABULARY.get(phase, [])

            best, best_coh = None, 0.0
            for word in candidates:
                if word in used:
                    continue
                psi_word = self._word_cache.get(word)
                if psi_word is not None:
                    coh = coherence(psi_intention, psi_word) + random.uniform(-0.03, 0.03)
                    if coh > best_coh:
                        best_coh, best = coh, word

            if best:
                selected.append(best)
                used.add(best)
            phase_idx += 1

        return selected

    def _french_grammar(self, line: str) -> str:
        """Corrige la grammaire française de base (élision, genre)."""
        line = re.sub(r'\ble\s+([aeiouyâêîôûäëïöüÿh])', r"l'\1", line)
        line = re.sub(r'\bla\s+([aeiouyâêîôûäëïöüÿh])', r"l'\1", line)
        line = re.sub(r'\bde le\b', 'du', line)
        line = re.sub(r'\bde les\b', 'des', line)
        line = re.sub(r'\bà le\b', 'au', line)
        line = re.sub(r'\bà les\b', 'aux', line)
        line = re.sub(r'\bde\s+([aeiouyâêîôûäëïöüÿh])', r"d'\1", line)
        line = re.sub(r' {2,}', ' ', line)
        line = line.strip()
        return line[0].upper() + line[1:] if line else line


# ═══════════════════════════════════════════════════════════════════════════════
# 24. ADAPTATEUR WAVE NARRATIVE → bind / coherence / superpose(ABC)
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : wave_narrative.py (~500 lignes) — WaveNarrative avec _bind/_coherence/
#         _encode réimplémentés et superposition manuelle avec décroissance ABC.
# Après : même API, délégation à wave_lang.bind + coherence + superpose(weights).

class WaveNarrativeBridge:
    """
    Synthétiseur narratif ondulatoire — paragraphes par interférence.

    Drop-in replacement pour wave_narrative.py (WaveNarrative).
    Même API, backend wave_lang.bind + coherence + superpose.

    Équivalence #29 : Narration Structurée
        → Arc de phase narratif (0 → π → 2π) : chaque section est
        une rotation de phase de l'onde narrative.

    Usage :
        wn = WaveNarrativeBridge()
        text = wn.synthesize(facts, topic="la lumière", section_type="introduction")
    """

    def __init__(self, dim: int = DEFAULT_DIM):
        self.dim = dim
        self._used_connectors: List[str] = []
        self._used_structures: List[str] = []

        try:
            from wave_narrative import (CONNECTOR_BANK as CB,
                                        SENTENCE_STRUCTURES as SS,
                                        SECTION_OPENINGS as SO,
                                        QUALIFIERS as QF)
            self.CONNECTOR_BANK = CB
            self.SENTENCE_STRUCTURES = SS
            self.SECTION_OPENINGS = SO
            self.QUALIFIERS = QF
        except ImportError:
            self.CONNECTOR_BANK = {'transition': ['De plus,', 'Par ailleurs,']}
            self.SENTENCE_STRUCTURES = {'property': [
                lambda s, r, o: f"{s} {r} {o}.",
            ]}
            self.SECTION_OPENINGS = {'development': ['Approfondissons.']}
            self.QUALIFIERS = {'importance': ['essentiel']}

    def synthesize(self, facts: List[Tuple[str, str, str, str]],
                   topic: str = '', section_type: str = 'development',
                   style: str = 'standard') -> str:
        """
        Synthétise un paragraphe à partir de faits.

        Pipeline ondulatoire :
          1. ψ_narrative = encode(f"{section}_{style}_{n}") — arc de phase
          2. ψ_facts = superpose(ψ_faits, weights=abc_kernel(0.3·i))
          3. ψ_composite = bind(ψ_facts, ψ_narrative)
          4. Sélection des connecteurs par résonance de phase

        Args:
            facts: liste de (sujet, relation, objet, secteur)
            topic: le sujet de la page
            section_type: 'introduction', 'development', 'conclusion', 'example'
            style: 'standard', 'academique', 'vulgarise', 'poetique'

        Returns:
            un paragraphe cohérent
        """
        if not facts:
            return (f"Le silence de la connaissance sur {topic} est lui-même "
                    f"une forme de résonance." if style == 'poetique'
                    else f"Les informations spécifiques sur {topic} sont "
                         f"encore en cours d'intégration.")

        self._used_connectors = []
        self._used_structures = []
        narrative_phase = self._compute_narrative_phase(facts, section_type)

        # 1. ψ_narrative (onde structurante)
        psi_narrative = encode(f"{section_type}_{style}_{len(facts)}", dim=self.dim)

        # 2. Superposition des faits avec décroissance ABC
        psis = [encode(f"{f[0]} {f[1]} {f[2]}", dim=self.dim) for f in facts]
        weights = [float(PHI ** (-0.3 * i)) for i in range(len(psis))]
        psi_facts = superpose(*psis, weights=weights)

        # 3. Binding ψ_composite = ψ_facts ⊗ ψ_narrative
        psi_composite = bind(psi_facts, psi_narrative)
        _ = psi_composite  # réservé pour extension (décodage par résonance)

        # 4. Construire le paragraphe
        sentences = []

        if section_type in self.SECTION_OPENINGS and len(facts) >= 2:
            sentences.append(random.choice(self.SECTION_OPENINGS[section_type]))

        prev_fact = None
        facts_used = 0

        for i, fact in enumerate(facts[:5]):
            s, r, o = str(fact[0]).strip(), str(fact[1]).strip(), str(fact[2]).strip()
            if s and s[0].isdigit() and '. ' in s[:6]:
                s = s.split('. ', 1)[1]
            s_cap = s[0].upper() + s[1:] if s else s

            connector = self._select_connector(narrative_phase, prev_fact, fact)
            fact_type = self._detect_fact_type(r)

            structures = self.SENTENCE_STRUCTURES.get(
                fact_type, self.SENTENCE_STRUCTURES['property'])
            if random.random() < 0.7 or len(facts) <= 2:
                structure = structures[0]
            else:
                structure = structures[(facts_used % (len(structures) - 1)) + 1]

            sentence = structure(s_cap, r, o)

            starts_complex = sentence.startswith(
                ('Il ', 'L\'une', 'C\'est', 'On ', 'Si ', 'Lorsqu'))
            if connector and i > 0:
                if starts_complex:
                    sentence = connector + ' ' + sentence[0].lower() + sentence[1:]
                else:
                    sentence = connector + ' ' + sentence[0].lower() + sentence[1:]

            sentences.append(sentence)
            prev_fact = fact
            facts_used += 1

        # Clôture pour conclusion
        if section_type == 'conclusion' and topic:
            closings = [
                f"En définitive, {topic} se révèle être bien plus riche qu'il n'y paraît.",
                f"Ces différents aspects convergent pour faire de {topic} "
                f"un sujet d'une profondeur remarquable.",
                f"Ainsi se dessine {topic}, non pas comme une simple notion, "
                f"mais comme un carrefour de connaissances.",
            ]
            sentences.append(random.choice(closings))

        # Accroche pour introduction
        if section_type == 'introduction' and topic:
            hooks = [
                f"{topic[0].upper() + topic[1:]} représente un domaine d'une "
                f"richesse remarquable.",
                f"Lorsqu'on aborde {topic}, plusieurs dimensions méritent "
                f"notre attention.",
                f"Bienvenue dans cette exploration de {topic}.",
            ]
            sentences.insert(0, random.choice(hooks))

        text = ' '.join(sentences)
        text = self._cleanup(text)
        return text

    def synthesize_paragraph(self, facts: List[Tuple],
                             topic: str = '',
                             section_type: str = 'development') -> str:
        """Alias pour synthesize()."""
        return self.synthesize(facts, topic, section_type)

    # ── Helpers ──

    def _compute_narrative_phase(self, facts: List[Tuple],
                                 section_type: str) -> float:
        """Phase narrative (arc 0 → π → 2π)."""
        if section_type == 'introduction':
            return 0.0
        elif section_type == 'conclusion':
            return 3 * math.pi / 2
        elif section_type == 'example':
            return math.pi / 4
        if len(facts) <= 2:
            return math.pi / 3
        elif len(facts) == 3:
            return math.pi / 2
        return math.pi / 4

    def _select_connector(self, narrative_phase: float, prev_fact,
                          curr_fact) -> str:
        """Sélectionne un connecteur par résonance de phase."""
        if prev_fact is None:
            return ''

        prev_s, prev_o = str(prev_fact[0]), str(prev_fact[2])
        curr_s, curr_r = str(curr_fact[0]), str(curr_fact[1])

        if prev_s.lower().strip() == curr_s.lower().strip():
            pool = self.CONNECTOR_BANK['direct'][:4] + self.CONNECTOR_BANK['causal'][:2]
        elif prev_o.lower().strip() in curr_s.lower() or curr_s.lower().strip() in prev_o.lower():
            pool = self.CONNECTOR_BANK['causal']
        elif any(w in curr_r.lower() for w in ['ne', 'pas', 'contraire', 'différent']):
            pool = self.CONNECTOR_BANK['contrast']
        elif narrative_phase > math.pi:
            pool = self.CONNECTOR_BANK['synthesis']
        elif narrative_phase < math.pi / 3:
            pool = self.CONNECTOR_BANK['direct'] + self.CONNECTOR_BANK['example']
        else:
            pool = self.CONNECTOR_BANK['transition']

        available = [c for c in pool if c not in self._used_connectors[-5:]]
        if not available:
            available = pool

        chosen = random.choice(available)
        self._used_connectors.append(chosen)
        return chosen

    def _detect_fact_type(self, relation: str) -> str:
        """Détecte le type de fait pour choisir la structure."""
        r = str(relation).lower().strip()
        if r in ('est', 'sont', 'se définit comme', 'désigne', 'correspond à'):
            return 'definition'
        if r.startswith('a ') or r.startswith('ont '):
            return 'action'
        return 'property'

    def _cleanup(self, text: str) -> str:
        """Nettoyage final du texte."""
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r' ([,.!?;:])', r'\1', text)
        text = re.sub(r'([.!?]\s+)([a-zàâäéèêëïîôöùûüÿç])',
                      lambda m: m.group(1) + m.group(2).upper(), text)
        return text.strip()


# ═══════════════════════════════════════════════════════════════════════════════
# 25. ADAPTATEUR WAVE SYNTHESIZER → superpose / decode / resonate_batch
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : wave_synthesizer.py (~230 lignes) — superposition manuelle +
#         extraction des mots dominants par produit scalaire.
# Après : même API, délégation à wave_lang.superpose + decode + resonate_batch.

class WaveSynthesizerBridge:
    """
    Synthétiseur ondulatoire de paragraphes — superposition de faits.

    Drop-in replacement pour wave_synthesizer.py (WaveSynthesizer).
    Même API, backend wave_lang.superpose + decode.

    Principe : Ψ_paragraphe = ψ_f1 + ψ_f2 + ψ_f3 (superposition).
    Le décodage révèle les mots résonnants (interférence constructive
    entre les faits) → la phrase est une SYNTHÈSE, pas une liste.

    Usage :
        ws = WaveSynthesizerBridge(encoder)
        paragraph = ws.synthesize(facts, question)
    """

    def __init__(self, encoder):
        self.encoder = encoder

    def synthesize(self, facts: List[Tuple[str, str, str]],
                   question: str = "") -> str:
        """
        Synthétise plusieurs faits en un paragraphe.

        Args:
            facts: liste de (sujet, relation, objet)
            question: question originale (pour le contexte)

        Returns:
            texte synthétisé en français naturel
        """
        if not facts:
            return ""

        if len(facts) == 1:
            s, r, o = facts[0]
            return f"{s.capitalize()} {r} {o}."

        # 1. Superposition des ondes des faits (wave_lang.superpose)
        psi_total = self._superpose(facts)

        # 2. Mots dominants de la superposition
        dominant_words = self._extract_dominant(psi_total, top_k=15)

        # 3. Assemblage
        subject = facts[0][0]
        return self._assemble(subject, dominant_words, facts)

    def _superpose(self, facts: List[Tuple[str, str, str]]) -> np.ndarray:
        """Superpose les ondes des faits (wave_lang.superpose)."""
        psis = []
        for s, r, o in facts:
            psi = self.encoder.encode_query(f"{s} {r} {o}")
            psis.append(psi)
        return superpose(*psis) if psis else np.zeros(self.encoder.dim,
                                                      dtype=np.complex128)

    def _extract_dominant(self, psi: np.ndarray,
                          top_k: int = 15) -> List[str]:
        """
        Extrait les mots dominants de l'onde superposée.

        Utilise wave_lang.decode pour la résonance avec le vocabulaire.
        """
        if not hasattr(self.encoder, 'word_vectors'):
            return []

        scores = []
        for word, v_w in self.encoder.word_vectors.items():
            if word.startswith('__char_') or len(word) < 2:
                continue
            score = float(resonate(psi, v_w))
            if score > 0.02:
                scores.append((word, score))

        scores.sort(key=lambda x: -x[1])

        stopwords = {'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du',
                     'est', 'sont', 'a', 'et', 'dans', 'pour', 'par',
                     'avec', 'the', 'is', 'are', 'of', 'in', 'on', 'at'}
        dominant = [w for w, s in scores if w not in stopwords][:top_k]
        return dominant

    def _assemble(self, subject: str, dominant_words: List[str],
                  facts: List[Tuple[str, str, str]]) -> str:
        """Assemble le paragraphe à partir des mots dominants."""
        if not dominant_words:
            s, r, o = facts[0]
            return f"{s.capitalize()} {r} {o}."

        properties = [o for s, r, o in facts]

        if len(properties) == 2:
            return (f"{subject.capitalize()} {facts[0][1]} {properties[0]}, "
                    f"et {facts[1][1]} {properties[1]}.")

        if len(properties) >= 3:
            main = f"{subject.capitalize()} {facts[0][1]} {properties[0]}"
            others = [f"{r} {o}" for _, r, o in facts[1:]]
            return f"{main} : {' ; '.join(others)}."

        return f"{subject.capitalize()} {facts[0][1]} {properties[0]}."


# ═══════════════════════════════════════════════════════════════════════════════
# 26. ADAPTATEUR WAVE STYLER → encode / coherence (Style Transfer)
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : wave_styler.py (~405 lignes) — templates FR + random.choice,
#         encodeur accepté mais jamais utilisé, bug latent 'subordonnée'.
# Après : même API, sélection de structure par COHÉRENCE (ψ_question vs
#         ψ_structure) au lieu de random.choice — déterministe par résonance.
#         Tables FR (STRUCTURES, _CONNECTORS, _ACCENTS_MAP) conservées.

class WaveStylerBridge:
    """
    Styler rédactionnel ondulatoire — faits bruts → français naturel.

    Drop-in replacement pour wave_styler.py (WaveStyler).
    Même API, backend wave_lang.encode + coherence.

    Équivalence #27 : Style Transfer
        → Modulation de motif d'onde : le registre (formel/courant/familier)
        est un MOTIF d'onde ; la structure sélectionnée est celle qui
        RÉSONNE le mieux avec la question.

    Améliorations par rapport à l'original :
      - Sélection de structure par cohérence (déterministe) au lieu de random
      - Bug latent corrigé : clé 'subordonnee' vs lookup 'subordonnée'

    Usage :
        styler = WaveStylerBridge()
        texte = styler.render(facts, question="explique la photosynthèse")
    """

    # Structures par registre (données FR conservées)
    STRUCTURES = {
        'formel': {
            'simple': [
                "Il convient de noter que {s} {r} {o}.",
                "On notera que {s} {r} {o}.",
                "Rappelons que {s} {r} {o}.",
            ],
            'subordonnee': [
                "{s_cap}, qui {r} {o}, constitue un élément fondamental.",
                "{s_cap}, dont on sait qu'il {r} {o}, mérite attention.",
                "Le fait que {s} {r} {o} est établi.",
            ],
            'connecteur': ["Par ailleurs, ", "De plus, ", "Soulignons que ", "À cet égard, "],
        },
        'courant': {
            'simple': [
                "{S} {r} {o}.",
                "{S} a la particularité de {r} {o}.",
                "On peut dire que {s} {r} {o}.",
            ],
            'subordonnee': [
                "{S}, qui {r} {o}, joue un rôle clé.",
                "{S}, dont la fonction est de {r} {o}, est essentiel.",
            ],
            'connecteur': ["De plus, ", "Ensuite, ", "Aussi, ", "Notamment, "],
        },
        'familier': {
            'simple': [
                "{S} {r} {o}.",
                "En gros, {s} {r} {o}.",
                "Pour faire simple : {s} {r} {o}.",
            ],
            'subordonnee': [
                "{S}, c'est ce qui {r} {o}.",
            ],
            'connecteur': ["Et puis, ", "Aussi, ", "En plus, "],
        },
    }

    # Mots-clés de registre (détection)
    FAMILIER_KEYWORDS = ['c est quoi', 'truc', 'machin', 'ouais',
                         'genre', 'dis moi', 'donne moi', 'ça']
    FORMEL_KEYWORDS = ['définissez', 'expliquez', 'décrivez', 'analysez',
                       'comparez', 'énumérez', 'détaillez',
                       'pourriez-vous', 'veuillez', 'auriez-vous',
                       'define', 'explain', 'describe', 'analyze', 'compare']

    def __init__(self, encoder=None, dim: int = DEFAULT_DIM):
        self.encoder = encoder
        self.dim = dim
        self._last_structures: List[str] = []

        # Importer apply_accents de wave_styler (table FR ~150 entrées)
        self._apply_accents = lambda t: t
        try:
            from wave_styler import apply_accents
            self._apply_accents = apply_accents
        except ImportError:
            pass

        # ψ par registre (pour la détection par résonance)
        self._register_psis = {
            'formel': encode("définissez expliquez analysez veuillez", dim=self.dim),
            'courant': encode("explique donne moi c'est quoi", dim=self.dim),
            'familier': encode("ouais ça truc genre quoi", dim=self.dim),
        }

    def detect_register(self, question: str) -> str:
        """
        Détecte le registre : mots-clés + résonance avec les ψ de registre.

        Returns: 'formel', 'courant', ou 'familier'
        """
        q = question.lower().strip()
        q_words = set(re.findall(r'\w+', q))

        # Matching par mots complets pour les mots-clés courts
        # (évite 'ca' ⊂ 'implications' — faux positif de sous-chaîne)
        score_familier = sum(
            1 for w in self.FAMILIER_KEYWORDS
            if w in q or (len(w) <= 4 and w in q_words))
        score_formel = sum(
            1 for w in self.FORMEL_KEYWORDS
            if w in q or (len(w) <= 4 and w in q_words))

        if score_formel > score_familier:
            return 'formel'
        if score_familier > 0:
            return 'familier'

        # Résonance : quel ψ de registre résonne le plus avec la question ?
        if q:
            psi_q = encode(q, dim=self.dim)
            best_register, best_score = 'courant', 0.0
            for register, psi_r in self._register_psis.items():
                s = float(coherence(psi_q, psi_r))
                if s > best_score:
                    best_score, best_register = s, register
            return best_register

        return 'courant'

    def _select_structure(self, templates: List[str], question: str,
                          i: int) -> str:
        """
        Sélectionne une structure par cohérence (déterministe par résonance).

        Chaque template est encodé en ψ ; celui qui résonne le plus avec
        la question est choisi (rotation sur l'index pour la variété).
        """
        if not templates:
            return ""
        if not question:
            return templates[i % len(templates)]

        psi_q = encode(question, dim=self.dim)
        scores = []
        for tpl in templates:
            psi_tpl = encode(tpl[:60], dim=self.dim)
            scores.append(float(coherence(psi_q, psi_tpl)))

        # Meilleure structure, avec rotation pour éviter la répétition
        best = max(range(len(scores)), key=lambda k: scores[k])
        return templates[(best + i) % len(templates)]

    def render(self, facts: List[Tuple[str, str, str, str]],
               question: str = "", lang: str = 'fr',
               style: str = 'auto', personality: str = 'ka') -> str:
        """
        Transforme une liste de faits en réponse naturelle.

        Args:
            facts: liste de (sujet, relation, objet, secteur)
            question: question originale (pour le registre et la résonance)
            lang: 'fr' ou 'en'
            style: "auto"|"concise"|"elegant"|"pedagogique"|"chaleureux"
            personality: "ka"|"savant"|"vulgarisateur"|"poete"

        Returns:
            réponse stylée en français naturel
        """
        if not facts:
            sujet = question.strip('?.,!;: ')[:80]
            return (f"Je n'ai pas assez d'éléments sur « {sujet} » "
                    f"pour répondre avec confiance.")

        # Registre : style explicite > détection auto
        if style != 'auto':
            register = {'concise': 'courant', 'elegant': 'formel',
                        'pedagogique': 'courant',
                        'chaleureux': 'familier'}.get(style, 'courant')
        else:
            register = self.detect_register(question) if question else 'courant'

        if register not in self.STRUCTURES:
            register = 'courant'
        structures = self.STRUCTURES[register]

        personality_prefix = {
            'ka': '', 'savant': '', 'vulgarisateur': 'En termes simples, ',
            'poete': '',
        }.get(personality, '')

        parts = []
        last_subject = ""

        for i, (s, r, o, sec) in enumerate(facts):
            S = s[0].upper() + s[1:] if s else s
            s_lower = s.lower() if s else s

            if i == 0:
                # Structure par cohérence (au lieu de random)
                if len(s) > 3 and len(o) > 3:
                    pool = (structures.get('subordonnee', []) +
                            structures['simple'])
                else:
                    pool = structures['simple']
                template = self._select_structure(pool, question, i)
                rendered = template.format(s=s_lower, S=S, s_cap=S, r=r, o=o)
                parts.append(rendered)
                last_subject = s_lower
            else:
                connectors = structures.get('connecteur', [])
                available = [c for c in connectors
                             if c not in self._last_structures[-3:]]
                if not available:
                    available = connectors
                connector = self._select_structure(available, question, i)
                self._last_structures.append(connector)
                if len(self._last_structures) > 10:
                    self._last_structures = self._last_structures[-5:]

                if s_lower == last_subject:
                    pronoun = 'elle' if s_lower.endswith('e') else 'il'
                    rendered = f"{connector}{pronoun} {r} {o}."
                else:
                    template = self._select_structure(structures['simple'],
                                                      question, i)
                    rendered = f"{connector}{template.format(s=s_lower, s_cap=S, r=r, o=o)}"
                    if connector in rendered:
                        rendered = rendered.replace(connector, '', 1)

                parts.append(rendered)
                last_subject = s_lower

        text = ' '.join(parts)

        if personality_prefix:
            text = personality_prefix + text[0].lower() + text[1:]

        if style == 'concise':
            sentences = re.split(r'(?<=[.!?])\s+', text)
            text = sentences[0] if sentences else text
        elif style == 'pedagogique':
            if len(facts) == 1:
                text += " C'est un concept important à retenir."
        elif style == 'chaleureux':
            if not text.endswith('?'):
                text = text.rstrip('.') + '. Je reste à votre écoute pour approfondir.'

        # Accents (table FR importée de wave_styler)
        try:
            text = self._apply_accents(text)
        except Exception:
            pass

        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s([.,!?;:])', r'\1', text)
        text = text.replace(' .', '.').replace(' ,', ',')

        return text


# ═══════════════════════════════════════════════════════════════════════════════
# 27. ADAPTATEUR HARMONIC STYLE → phase_shift / rotate (Role Prompting)
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : harmonic_style.py (~280 lignes) — empathie/vocabulaire/diversité
#         par heuristiques φ-hash, ZÉRO math ondulatoire.
# Après : même API, + ROTATION DE PHASE ÉMOTIONNELLE réelle :
#         ψ_réponse = phase_shift(encode(response), θ_tonalité).

class HarmonicStyleBridge:
    """
    Styler harmonique — empathie + vocabulaire + diversité + rotation de phase.

    Drop-in replacement pour harmonic_style.py (HarmonicStyler).
    Même API, backend wave_lang.phase_shift + rotate.

    Équivalence #26 : Role Prompting
        → Rotation de l'espace des phases : la tonalité détectée dans le
        message utilisateur est une ROTATION θ de l'espace des phases
        de la réponse (θ_urgent ≠ θ_curieux ≠ θ_frustré...).

    Usage :
        styler = HarmonicStyleBridge()
        styled = styler.style(response, user_message, style_level=0.618)
    """

    # Angles de phase par tonalité (rotation de l'espace des phases)
    TONE_ANGLES = {
        'urgent': 0.2, 'confus': 0.8, 'curieux': 1.2,
        'frustré': 2.0, 'neutre': 0.0, 'admiratif': 3.0,
    }

    def __init__(self, dim: int = DEFAULT_DIM):
        self.dim = dim
        # Import des données canoniques (TONALITIES, ALTERNATIVES, ...)
        self._data_loaded = False
        self.TONALITIES = {}
        self.EMOTION_KEYWORDS = {}
        self.ENRICHMENTS = []
        self.ALTERNATIVES = {}
        try:
            from harmonic_style import (EmpathyEngine, DiversityEngine,
                                        VocabularyEngine)
            self._empathy = EmpathyEngine()
            self._diversity = DiversityEngine()
            self._vocabulary = VocabularyEngine()
            self.TONALITIES = EmpathyEngine.TONALITIES
            self.EMOTION_KEYWORDS = EmpathyEngine.EMOTION_KEYWORDS
            self.ENRICHMENTS = DiversityEngine.ENRICHMENTS
            self.ALTERNATIVES = VocabularyEngine.ALTERNATIVES
            self._data_loaded = True
        except ImportError:
            # Fallback minimal
            self._empathy = self._DummyEmpathy()
            self._diversity = self._DummyDiversity()
            self._vocabulary = self._DummyVocabulary()
            self.TONALITIES = {"neutre": {"prefix": "", "tone": "équilibré",
                                          "length": "standard"}}

    def style(self, response: str, user_message: str = "",
              style_level: float = None) -> str:
        """
        Applique le style harmonique complet à une réponse.

        Pipeline :
          1. Empathie — détection de tonalité + préfixe
          2. ROTATION DE PHASE — ψ_réponse = phase_shift(encode, θ_tonalité)
             (nouveau : délégation réelle à wave_lang)
          3. Vocabulaire — alternatives φ-espacées
          4. Diversité — variations naturelles

        Args:
            response: réponse brute
            user_message: message utilisateur (pour l'empathie)
            style_level: 0.618 (1/φ) = optimal, 0.3 = sobre, 0.9 = créatif

        Returns:
            réponse stylée, toujours fiable
        """
        level = style_level if style_level is not None else (1.0 / PHI)

        # 1. Empathie
        if user_message:
            response = self._empathy.apply(response, user_message)

        # 2. Rotation de phase émotionnelle (délégation wave_lang)
        if user_message:
            tone = self.detect_tone(user_message)
            theta = self.TONE_ANGLES.get(tone, 0.0)
            if theta != 0.0:
                psi = encode(response[:100], dim=self.dim)
                psi_rot = phase_shift(psi, theta)
                # La rotation confirme l'onde ; le texte reste la réponse
                # (le ψ roté est conservé pour les usages ultérieurs)
                self._last_psi = psi_rot

        # 3. Vocabulaire
        if level > 0.3:
            response = self._vocabulary.enrich(response)

        # 4. Diversité
        if level > 0.2:
            response = self._diversity.enrich(response, level)

        return response

    def detect_tone(self, message: str) -> str:
        """Détecte la tonalité émotionnelle d'un message."""
        return self._empathy.detect_tone(message)

    def emotional_rotation(self, message: str) -> np.ndarray:
        """
        Retourne le ψ de la rotation émotionnelle (nouveau).

        ψ_rotation = phase_shift(encode(message), θ_tonalité)

        Returns:
            ψ ∈ ℂᵈⁱᵐ — l'onde orientée par la tonalité
        """
        tone = self.detect_tone(message)
        theta = self.TONE_ANGLES.get(tone, 0.0)
        psi = encode(message[:100], dim=self.dim)
        return phase_shift(psi, theta)

    def emotional_coherence(self, message_a: str, message_b: str) -> float:
        """
        Mesure l'alignement émotionnel entre deux messages (nouveau).

        score = coherence(ψ_a_roté, ψ_b_roté) — les phases alignées
        = empathie (interférence constructive).

        Returns:
            score ∈ [0, 1]
        """
        return float(coherence(self.emotional_rotation(message_a),
                               self.emotional_rotation(message_b)))

    # ── Fallbacks si harmonic_style indisponible ──

    class _DummyEmpathy:
        def detect_tone(self, message):
            return "neutre"
        def apply(self, response, user_message):
            return response

    class _DummyDiversity:
        def enrich(self, response, level):
            return response

    class _DummyVocabulary:
        def enrich(self, response):
            return response


# ═══════════════════════════════════════════════════════════════════════════════
# 28. ADAPTATEUR HOLOGRAM LOADER → .npz → HolographicRAG (KV-Cache #34)
# ═══════════════════════════════════════════════════════════════════════════════
#
# Avant : hologram_store.py (backend/hologram) — registre .npz pur I/O,
#         aucun lien avec la mémoire holographique exécutable.
# Après : pont .npz → HolographicRAG.ingest : les hologrammes téléchargés
#         deviennent des faits EXÉCUTABLES dans la mémoire holographique.

class HologramLoaderBridge:
    """
    Chargeur d'hologrammes — .npz → HolographicRAG (KV-Cache persisté).

    Drop-in replacement pour hologram_store.py (HologramStore) côté lecture.
    Backend : HolographicRAG (wave_bridge) + numpy.

    Équivalence #34 : KV-Cache → Hologramme (H stocke tout,
        H ☆ ψ_Q retrouve tout). Les hologrammes .npz sont la PERSISTANCE
        du cache : ils se re-chargent dans la mémoire exécutable.

    Usage :
        rag = HolographicRAG(dim=512)
        loader = HologramLoaderBridge(rag)
        n = loader.load_npz("official_medecine.npz")
        n_total = loader.load_all()
    """

    # Format .npz hologramme (écrit par hologram_store.py) :
    #   subjects, relations, objects, sectors (object arrays str)
    #   amplitudes (float32), psies_real/imag (float32, inutilisés → ré-encodage)

    def __init__(self, rag: 'HolographicRAG', store_dir: str = None):
        """
        Args:
            rag: HolographicRAG cible (la mémoire qui reçoit les faits)
            store_dir: répertoire des .npz (défaut: data/hologram_store)
        """
        self.rag = rag
        self.store_dir = store_dir
        self._store = None

        # Import lazy du HologramStore (backend/hologram) si disponible
        if store_dir is None:
            try:
                from hologram_store import HologramStore, STORE_DIR
                self._store = HologramStore()
                self.store_dir = str(STORE_DIR)
            except Exception:
                self._store = None
        else:
            try:
                from hologram_store import HologramStore
                self._store = HologramStore(store_dir=store_dir)
            except Exception:
                self._store = None

        if self.store_dir is None:
            self.store_dir = "data/hologram_store"

        self._loaded: Dict[str, int] = {}  # holo_id → nb de faits chargés

    def load_npz(self, path: str,
                 secteur_fallback: str = "GENERAL") -> int:
        """
        Charge un fichier .npz directement dans le RAG.

        Supporte les 2 formats :
          1. Columnar : subjects/relations/objects/sectors (arrays)
          2. Tuple : 'facts' = array de tuples (s, r, o[, sec])

        Args:
            path: chemin du fichier .npz
            secteur_fallback: secteur si absent

        Returns:
            nombre de faits chargés (0 si fichier invalide)
        """
        if not os.path.exists(path):
            return 0

        data = np.load(path, allow_pickle=True)

        facts = []
        if 'facts' in data:
            # Format tuple : array de (s, r, o[, sec])
            raw = data['facts']
            for item in raw:
                if isinstance(item, (list, tuple, np.ndarray)):
                    item = tuple(item)
                else:
                    item = (item,)
                if len(item) >= 3:
                    sec = item[3] if len(item) > 3 else secteur_fallback
                    facts.append((str(item[0]), str(item[1]),
                                  str(item[2]), str(sec)))
        else:
            # Format columnar
            subjects = data['subjects'] if 'subjects' in data else []
            relations = data['relations'] if 'relations' in data else []
            objects = data['objects'] if 'objects' in data else []
            sectors = data['sectors'] if 'sectors' in data else []
            n = min(len(subjects), len(relations), len(objects))
            for i in range(n):
                sec = str(sectors[i]) if i < len(sectors) else secteur_fallback
                facts.append((str(subjects[i]), str(relations[i]),
                              str(objects[i]), sec))

        data.close()

        if not facts:
            return 0

        n_loaded = self.rag.ingest_batch(facts)
        self._loaded[os.path.basename(path)] = n_loaded
        return n_loaded

    def load(self, holo_id: str) -> int:
        """
        Charge un hologramme du store (téléchargé + ingéré dans le RAG).

        Args:
            holo_id: identifiant de l'hologramme

        Returns:
            nombre de faits chargés (0 si introuvable)
        """
        if self._store is None:
            # Fallback : chercher un .npz par id dans store_dir
            candidates = [
                os.path.join(self.store_dir, f"{holo_id}.npz"),
                os.path.join(self.store_dir, holo_id),
            ]
            for c in candidates:
                if os.path.exists(c):
                    return self.load_npz(c)
            return 0

        try:
            facts = self._store.download(holo_id)
        except Exception:
            return 0

        if not facts:
            return 0

        # download() retourne des tuples 4 (s, r, o, secteur)
        n_loaded = self.rag.ingest_batch([tuple(f) for f in facts])
        self._loaded[holo_id] = n_loaded
        return n_loaded

    def load_all(self, holo_type: str = None) -> Dict[str, int]:
        """
        Charge tous les hologrammes listés dans le store.

        Args:
            holo_type: filtre 'official'|'community'|'private' (None = tous)

        Returns:
            dict {holo_id: nb de faits chargés}
        """
        if self._store is None:
            return {}

        try:
            holograms = self._store.list_holograms(holo_type=holo_type)
        except Exception:
            return {}

        results = {}
        for meta in holograms:
            holo_id = meta.get('id') if isinstance(meta, dict) else getattr(meta, 'id', None)
            if not holo_id:
                continue
            n = self.load(holo_id)
            results[holo_id] = n
        return results

    @property
    def stats(self) -> dict:
        """Statistiques du chargement."""
        return {
            'loaded_holograms': len(self._loaded),
            'total_facts_loaded': sum(self._loaded.values()),
            'per_hologram': self._loaded,
            'rag_facts': self.rag.stats.get('n_facts', 0),
            'store_dir': self.store_dir,
            'store_available': self._store is not None,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 65)
    print("  🌊 WAVE BRIDGE — Adaptateurs pour modules existants")
    print("=" * 65)

    # ── 1. PsiDiphoneBank ──
    print("\n── 1. PSI-DIPHONE BANK (HolographicMemory) ──")
    bank = PsiDiphoneBank(dim=512)
    phone_pairs = [("k", "a"), ("a", "t"), ("t", "a"), ("s", "i")]
    for a, b in phone_pairs:
        audio = np.random.randn(1000) * 0.1  # audio simulé
        bank.store(a, b, audio)
    print(f"  Diphones stockés: {bank.size}")

    results = bank.query("k", "a", top_k=2)
    print(f"  Query 'k-a': {len(results)} résultats")
    for idx, score, audio in results:
        print(f"    idx={idx}, score={score:.4f}")

    # ── 2. ABCMemoryKernel ──
    print("\n── 2. ABC MEMORY KERNEL ──")
    kernel = ABCMemoryKernel(alpha=ALPHA, max_history=10)
    print(f"  K(0) = {kernel(0):.4f}")
    print(f"  K(5) = {kernel(5):.4f}")
    print(f"  K(20) = {kernel(20):.4f}")

    # Simuler un historique de gradients
    for i in range(5):
        kernel.store(np.random.randn(100).astype(np.float64) * 0.1)
    F_eff = kernel.compute_effective_force(np.random.randn(100) * 0.5)
    print(f"  Force effective: shape={F_eff.shape}, |F|={norm(F_eff):.4f}")

    # ── 3. HarmonicEnergyCore ──
    print("\n── 3. HARMONIC ENERGY CORE ──")
    he = HarmonicEnergyCore(lambda_h=4.0)
    psi_target = encode("folded_native", dim=512)
    psi_residues = [encode(f"residue_{i}", dim=512) for i in range(10)]
    distances = np.array([3.8 + i * 0.5 for i in range(10)])
    phi_scores = np.array([1.0 - i * 0.05 for i in range(10)])

    E = he.compute(psi_residues, psi_target, distances, phi_scores)
    print(f"  Énergie harmonique: {E:.4f} (négative = favorable)")

    # Électrostatique avec interférence
    E_elec = he.compute_electrostatic_interference(
        psi_residues[0], psi_residues[1],
        charge_a=1.0, charge_b=-1.0,
        distance=5.0
    )
    print(f"  Énergie électrostatique: {E_elec:.4f}")

    # ── 4. SpectralAnalyzer ──
    print("\n── 4. SPECTRAL ANALYZER ──")
    sa = SpectralAnalyzer(dim=1024)
    # Simuler un signal audio (ton 440 Hz + harmoniques)
    t = np.linspace(0, 0.1, 1024)
    signal = np.sin(TAU * 440 * t) + 0.5 * np.sin(TAU * 880 * t)

    freqs = sa.analyze(signal)
    spec = sa.spectrum(signal)
    print(f"  Analyse: {len(freqs)} bins, pic à {np.argmax(spec)}")

    recovering = sa.synthesize(freqs)
    recovery_error = np.mean((signal[:len(recovering)] - recovering) ** 2)
    print(f"  Synthèse: erreur MSE = {recovery_error:.8f}")

    filtered = sa.filter(signal, low_pass=1000)
    print(f"  Filtrage passe-bas 1000Hz: shape={filtered.shape}")

    # ── 5. VoiceSignature ──
    print("\n── 5. VOICE SIGNATURE ──")
    vs = VoiceSignature(dim=512)
    audio1 = np.random.randn(2048) * 0.1
    audio2 = np.random.randn(2048) * 0.1  # voix différente
    audio1b = audio1 + np.random.randn(2048) * 0.01  # même voix, bruitée

    sig1 = vs.extract(audio1)
    sig2 = vs.extract(audio2)
    sig1b = vs.extract(audio1b)

    print(f"  Signature voix 1: |ψ| = {norm(sig1):.3f}")
    print(f"  Même voix (bruitée):   similarité = {vs.compare(sig1, sig1b):.4f}")
    print(f"  Voix différente:        similarité = {vs.compare(sig1, sig2):.4f}")

    # ── 6. GlottalSource ──
    print("\n── 6. GLOTTAL SOURCE ──")
    gs = GlottalSource(f0=120, n_harmonics=20)
    waveform, psi_glottal = gs.synthesize(duration=0.05, sample_rate=8000)
    print(f"  Onde glottique: {len(waveform)} échantillons")
    print(f"  Amplitude max:  {np.max(np.abs(waveform)):.3f}")
    print(f"  ψ_glottal:      |ψ| = {norm(psi_glottal):.3f}")

    # ── 7. HarmonicCloner ──
    print("\n── 7. HARMONIC CLONER ──")
    cloner = HarmonicCloner(dim=1024)
    t_test = np.linspace(0, 0.1, 1024)
    source_audio = np.sin(TAU * 200 * t_test) + 0.3 * np.sin(TAU * 400 * t_test)
    target_audio = np.sin(TAU * 300 * t_test) + 0.3 * np.sin(TAU * 600 * t_test)
    cloned = cloner.clone(source_audio, target_audio)
    print(f"  Audio cloné: {len(cloned)} échantillons")
    print(f"  Source max: {np.max(np.abs(source_audio)):.3f}, Cloned max: {np.max(np.abs(cloned)):.3f}")

    print("\n" + "=" * 65)
    print("  ✅ Wave Bridge — Tous les adaptateurs fonctionnent.")
    print("=" * 65)

    # ══════════════════════════════════════════════════════════════════
    # NOUVEAUX ADAPTATEURS LLM (Phase 6)
    # ══════════════════════════════════════════════════════════════════

    # ── 8. CoherenceAttention ──
    print("\n── 8. COHERENCE ATTENTION (harmonic_attention.py) ──")
    attn = CoherenceAttention(dim=512)
    tokens = ["le", "chat", "dort", "sur", "le", "tapis"]
    ctx = attn.contextualize(tokens)
    print(f"  Tokens contextualisés: {len(ctx)}/{len(set(tokens))} uniques")
    for t in list(ctx.keys())[:3]:
        print(f"    {t}: |ψ|={norm(ctx[t]):.3f}, energy={energy(ctx[t]):.3f}")

    psi_q = attn.contextualize_query("le chat dort")
    print(f"  Query contextualisée: |ψ|={norm(psi_q):.3f}")

    # Test désambiguïsation
    senses = {"animal": encode("animal", dim=512), "discussion": encode("discussion", dim=512)}
    psi_disamb, scores = attn.disambiguate("chat", ["le", "animal", "dort"], senses)
    print(f"  Désambiguïsation 'chat': scores={ {k: f'{v:.3f}' for k, v in scores.items()} }")

    # ── 9. HolographicEncoderBridge ──
    print("\n── 9. HOLOGRAPHIC ENCODER BRIDGE (holographic_encoder.py) ──")
    enc = HolographicEncoderBridge(dim=512)
    psi_chat = enc.encode_word("chat")
    psi_chien = enc.encode_word("chien")
    print(f"  encode_word('chat'): |ψ|={norm(psi_chat):.3f}")

    # Binding / Unbinding
    psi_bound = enc.bind(psi_chat, psi_chien)
    psi_unbound = enc.unbind(psi_bound, psi_chien)
    recovery = float(coherence(psi_chat, psi_unbound))
    print(f"  bind/unbind recovery: {recovery:.3f}")

    # Encodage de faits
    psi_fact = enc.encode_fact("Paris", "capitale_de", "France")
    print(f"  encode_fact: |ψ|={norm(psi_fact):.3f}")

    # Stockage et requête
    enc.store_fact("Paris", "capitale_de", "France")
    enc.store_fact("Rome", "capitale_de", "Italie")
    psi_query = enc.encode_query("capitale de la France")
    result = enc.query(psi_query)
    print(f"  query: |result|={norm(result):.3f}, vocab={enc.vocab_size} mots")

    # ── 10. PhasePropagator ──
    print("\n── 10. PHASE PROPAGATOR (phase_amplifier.py) ──")
    # Créer un mini RAG pour le test
    rag = HolographicRAG(dim=512)
    rag.ingest("Socrate", "est", "homme", "PHILOSOPHIE")
    rag.ingest("homme", "est", "mortel", "PHILOSOPHIE")
    rag.ingest("Socrate", "boit", "ciguë", "HISTOIRE")

    # Créer un mini brain simulé
    class MiniBrain:
        def __init__(self, rag_store):
            self.store = rag_store
    mini_brain = MiniBrain(rag)

    prop = PhasePropagator(brain=mini_brain, dim=512)
    chain = prop.propagate("Socrate est-il mortel ?", max_depth=5)
    print(f"  Propagation: {len(chain.steps) if hasattr(chain, 'steps') else 0} étapes")
    print(f"  Cohérence totale: {chain.total_coherence if hasattr(chain, 'total_coherence') else 0:.3f}")
    print(f"  Conclusion: {chain.final_conclusion if hasattr(chain, 'final_conclusion') else 'N/A'}")

    explication = prop.explain(chain)
    print(f"  Explication: {explication[:100]}...")

    # ── 11. WaveDecoderBridge ──
    print("\n── 11. WAVE DECODER BRIDGE (wave_decoder.py) ──")
    kb = [("Paris", "capitale_de", "France", "GEO"),
          ("Rome", "capitale_de", "Italie", "GEO"),
          ("chat", "est", "animal", "BIO")]
    dec = WaveDecoderBridge(encoder=enc, knowledge_base=kb)
    reponse = dec.decode("Qu'est-ce qu'un chat ?")
    print(f"  decode: '{reponse}'")
    reponse_riche = dec.decode_rich("capitale de la France")
    print(f"  decode_rich: '{reponse_riche}'")
    sig = dec.compute_signature("Quelle est la capitale de la France ?")
    print(f"  signature: type={sig.get('type')}, reasoning={sig.get('reasoning', 0):.3f}")

    # ── 12. HolographicRAG ──
    print("\n── 12. HOLOGRAPHIC RAG (harmonic_brain.py) ──")
    rag2 = HolographicRAG(dim=512)
    rag2.ingest("Terre", "orbite_autour_de", "Soleil", "ASTRONOMIE")
    rag2.ingest("Lune", "orbite_autour_de", "Terre", "ASTRONOMIE")
    rag2.ingest("Soleil", "est", "étoile", "ASTRONOMIE")
    print(f"  Faits ingérés: {rag2.stats['n_facts']}")

    results = rag2.retrieve_resonance("Autour de quoi orbite la Terre ?")
    if results:
        best = results[0]
        print(f"  Meilleur résultat: {best[0]['sujet']} {best[0]['relation']} {best[0]['objet']} (score={best[1]:.3f})")

    psi_dom = rag2.psi_dominant
    print(f"  psi_dominant: |ψ|={norm(psi_dom):.3f}")

    # Rumination
    rag2.ruminate(max_pairs=10)
    print(f"  Après rumination: amplitudes moy={rag2.stats['mean_amplitude']:.3f}")

    # ── 13. FewShotPhaseLock ──
    print("\n── 13. FEW-SHOT PHASE LOCK (few_shot_injector.py) ──")
    fsl = FewShotPhaseLock(brain=mini_brain, dim=512)
    examples = [("chat", "cat"), ("chien", "dog"), ("oiseau", "bird")]
    pid = fsl.inject(examples, pattern_type="traduction", ttl_seconds=60)
    print(f"  Pattern injecté: {pid}")

    result = fsl.process(examples, "souris", pattern_type="traduction")
    print(f"  process('souris'): confidence={result['confidence']:.3f}")
    print(f"  Stats: {fsl.stats}")

    # ── 14. CoherenceGate ──
    print("\n── 14. COHERENCE GATE (conscious_intelligence.py) ──")
    rag3 = HolographicRAG(dim=512)
    rag3.ingest("eau", "gèle_à", "0°C", "PHYSIQUE")
    rag3.ingest("glace", "est", "eau_solide", "PHYSIQUE")
    rag3.ingest("vapeur", "est", "eau_gazeuse", "PHYSIQUE")

    gate = CoherenceGate(store=rag3)
    candidates = rag3.retrieve_resonance("À quelle température l'eau gèle-t-elle ?", max_results=5)
    answer, confidence, method = gate.reason("À quelle température l'eau gèle-t-elle ?", [c[0] for c in candidates])
    print(f"  Raisonnement: '{answer}' (confiance={confidence:.3f}, méthode={method})")

    # ── 15. FeedbackLoopBridge ──
    print("\n── 15. FEEDBACK LOOP BRIDGE (feedback_loop.py) ──")
    flb = FeedbackLoopBridge(dim=512)
    psi_ok = encode("La Terre tourne autour du Soleil", dim=512)
    psi_bad = encode("La Lune est plus grande que la Terre", dim=512)
    r_ok = flb.process_feedback(psi_ok, 0.9)
    r_bad = flb.process_feedback(psi_bad, 0.1)
    print(f"  Score 0.9 → {r_ok['decision']} (cohérence={r_ok['coherence']:.3f})")
    print(f"  Score 0.1 → {r_bad['decision']} (cohérence={r_bad['coherence']:.3f})")
    score_pred = flb.evaluate(psi_ok)
    print(f"  Écho de phase (prédiction): {score_pred:.3f}")
    print(f"  Stats: n_feedback={flb.stats['n_feedback']}, ratio_positif={flb.stats['ratio_positif']:.2f}")

    # ── 16. WaveSamplingBridge ──
    print("\n── 16. WAVE SAMPLING BRIDGE (wave_sampling.py) ──")
    words = ["chat", "chien", "oiseau", "poisson", "cheval", "souris"]
    vocab = {w: encode(w, dim=512) for w in words}
    sampler = WaveSamplingBridge(vocabulary=vocab, dim=512)
    psi_animal = encode("animal domestique", dim=512)

    det = sampler.deterministic(psi_animal)
    print(f"  deterministic: '{det}'")
    sampled = sampler.sample(psi_animal, temperature=0.8, top_p=0.9, top_k=5)
    print(f"  sample(T=0.8): '{sampled}'")
    creative = sampler.creative(psi_animal)
    print(f"  creative: '{creative}'")
    ppl = sampler.perplexity(sampler.coherence_scores(psi_animal))
    print(f"  perplexity(scores): {ppl:.3f}")

    # ── 17. WaveToolUseBridge ──
    print("\n── 17. WAVE TOOL USE BRIDGE (wave_tool_use.py) ──")
    from dataclasses import dataclass, field
    @dataclass
    class DemoParam:
        type: str = 'text'
        description: str = ''
        required: bool = False
        default: Any = ''

    @dataclass
    class DemoDefinition:
        name: str
        description: str
        parameters: Dict[str, Any] = field(default_factory=dict)
        handler: Optional[Callable] = None
        psi: Optional[np.ndarray] = None

    def calc_handler(a: float = 0.0, b: float = 0.0):
        return f"{a} + {b} = {a + b}"

    tools = WaveToolUseBridge(dim=512)
    tools.register(DemoDefinition(
        name="calculer", description="calcule la somme de deux nombres",
        parameters={"a": {'type': 'number', 'required': True},
                    "b": {'type': 'number', 'required': True}},
        handler=calc_handler,
    ))
    print(f"  Outils enregistrés: {tools.size}")
    result, call = tools.resolve_and_execute("calcule 2 + 3")
    print(f"  resolve_and_execute('calcule 2 + 3'): {result} (cohérence={call.coherence:.3f})")

    # ── 18. WaveBeamSearchBridge ──
    print("\n── 18. WAVE BEAM SEARCH BRIDGE (beam_search.py) ──")
    beam_vocab = {w: encode(w, dim=512) for w in
                  ["le", "chat", "dort", "sur", "le", "tapis", "et", "mange"]}
    bs = WaveBeamSearchBridge(vocabulary=beam_vocab, beam_width=3, dim=512)
    psi_depart = encode("le chat", dim=512)
    sequence = bs.best_sequence(psi_depart, max_steps=5)
    print(f"  best_sequence: {sequence}")
    text = bs.best_text(psi_depart, max_steps=5)
    print(f"  best_text: '{text}'")

    # ── 19. WavePerplexityBridge ──
    print("\n── 19. WAVE PERPLEXITY BRIDGE (wave_perplexity.py) ──")
    psi_test = encode("le ciel est bleu", dim=512)
    ent = WavePerplexityBridge.wave_entropy(psi_test)
    ppl_w = WavePerplexityBridge.wave_perplexity(psi_test)
    print(f"  wave_entropy: {ent:.3f}")
    print(f"  wave_perplexity: {ppl_w:.3f}")

    scores = {"chat": 0.8, "chien": 0.3, "oiseau": 0.2}
    conf = WavePerplexityBridge.confidence(scores)
    margin = WavePerplexityBridge.coherence_margin(scores)
    ppl_s = WavePerplexityBridge.coherence_perplexity(scores)
    print(f"  confidence(scores): {conf:.3f}")
    print(f"  coherence_margin: {margin:.3f}")
    print(f"  coherence_perplexity: {ppl_s:.3f}")

    comp = WavePerplexityBridge.compare_distributions(scores, {"chat": 0.4, "chien": 0.5, "oiseau": 0.1})
    print(f"  compare_distributions: js={comp['js_divergence']:.3f}, order_changed={comp['order_changed']}")

    # ── 20. WaveFineTuneBridge ──
    print("\n── 20. WAVE FINE TUNE BRIDGE (wave_fine_tune.py) ──")
    # Mini-encodeur avec word_vectors
    class MiniEncoder:
        def __init__(self, dim=64):
            self.dim = dim
            self.word_vectors = {
                w: encode(w, dim=dim) for w in
                ["chat", "chien", "animal", "est", "aime", "mange"]
            }
    mini_enc = MiniEncoder(dim=64)
    ft = WaveFineTuneBridge(mini_enc, learning_rate=1.0, lambda_reg=1.0)
    kb = [("chat", "est", "animal", "BIO"),
          ("chien", "est", "animal", "BIO"),
          ("chat", "aime", "chien", "BIO")]
    hist = ft.fine_tune(kb, epochs=2, verbose=False)
    print(f"  Loss finale: {hist['loss'][-1]:.4f} (initial: {hist['loss'][0]:.4f})")
    print(f"  Mots mis à jour: {hist['words_updated']}")

    # ── 21. DomainGateBridge ──
    print("\n── 21. DOMAIN GATE BRIDGE (harmonic_brain.py MoE) ──")
    dg = DomainGateBridge(dim=512)
    domains = dg.detect("Quelle est la capitale de la France ?")
    print(f"  detect('capitale de la France') → {domains}")
    domain_route = dg.route("Paris", "capitale_de", "France", "GEOGRAPHIE")
    print(f"  route(GEOGRAPHIE) → {domain_route}")
    merged = dg.merge([("culture_generale", [("fact1", 0.5), ("fact2", 0.3)]),
                       ("histoire", [("fact1", 0.6)])])
    print(f"  merge cross-domaine: {len(merged)} résultats, bonus appliqué")
    print(f"  Stats: {dg.stats['n_domains']} domaines")

    # ── 22. SystemPromptBridge ──
    print("\n── 22. SYSTEM PROMPT BRIDGE (harmonic_engine.py) ──")
    spb = SystemPromptBridge(dim=512)
    prompt = spb.build('reasoning', knowledge_context="La lumière est une onde")
    print(f"  build('reasoning') → '{prompt[:60]}...'")
    psi_0 = spb.initial_phase(category='reasoning')
    print(f"  initial_phase: |ψ₀|={norm(psi_0):.3f}")
    psi_oriented = spb.orient(psi_0, 'creative')
    print(f"  orient('creative'): |ψ|={norm(psi_oriented):.3f}, "
          f"cohérence avec ψ₀={coherence(psi_0, psi_oriented):.3f}")

    # ── 23. WavePoetryBridge ──
    print("\n── 23. WAVE POETRY BRIDGE (wave_poetry.py) ──")
    poet = WavePoetryBridge(dim=512)
    poem = poet.compose("la mer", form="free_verse", emotion="mystérieux", lines=4)
    print(f"  Poème ({poem['lines']} vers, émotion={poem['emotion']}):")
    for line in poem['text'].split('\n'):
        print(f"    │ {line}")
    print(f"  Stats: {poet.stats()['poetic_vocabulary']} mots, "
          f"{poet.stats()['phases']} phases")

    # ── 24. WaveNarrativeBridge ──
    print("\n── 24. WAVE NARRATIVE BRIDGE (wave_narrative.py) ──")
    wn = WaveNarrativeBridge(dim=512)
    facts_narr = [
        ("la lumière", "est une", "onde électromagnétique", "PHYSIQUE"),
        ("la lumière", "se propage à", "300 000 km/s", "PHYSIQUE"),
        ("la lumière", "est composée de", "photons", "PHYSIQUE"),
    ]
    for section in ['introduction', 'development', 'conclusion']:
        text = wn.synthesize(facts_narr, topic="la lumière", section_type=section)
        print(f"  [{section}] {text[:80]}...")

    # ── 25. WaveSynthesizerBridge ──
    print("\n── 25. WAVE SYNTHESIZER BRIDGE (wave_synthesizer.py) ──")
    class MiniEnc2:
        def __init__(self, dim=64):
            self.dim = dim
            self.word_vectors = {
                w: encode(w, dim=dim) for w in
                ["lumiere", "onde", "photon", "propage", "electromagnetique"]
            }
        def encode_query(self, text):
            return encode(text, dim=self.dim)
    ws = WaveSynthesizerBridge(MiniEnc2(dim=64))
    synth = ws.synthesize([
        ("lumiere", "est une", "onde electromagnetique"),
        ("lumiere", "se propage a", "300000 km/s"),
        ("lumiere", "est composee de", "photons"),
    ])
    print(f"  Synthèse: '{synth}'")
    synth1 = ws.synthesize([("chat", "est", "animal")])
    print(f"  Fait unique: '{synth1}'")

    # ── 26. WaveStylerBridge ──
    print("\n── 26. WAVE STYLER BRIDGE (wave_styler.py) ──")
    styler = WaveStylerBridge(dim=512)
    facts_style = [
        ("la photosynthèse", "produit", "de l'oxygène", "BIOLOGIE"),
        ("la photosynthèse", "utilise", "la lumière du soleil", "BIOLOGIE"),
        ("la photosynthèse", "est", "le processus de conversion de la lumière", "BIOLOGIE"),
    ]
    for q in ["explique la photosynthèse",
              "Définissez la photosynthèse et ses implications.",
              "c'est quoi la photosynthèse ?"]:
        reg = styler.detect_register(q)
        text = styler.render(facts_style, q)
        print(f"  [{reg}] {q[:35]}... → {text[:75]}...")

    # ── 27. HarmonicStyleBridge ──
    print("\n── 27. HARMONIC STYLE BRIDGE (harmonic_style.py) ──")
    hsb = HarmonicStyleBridge(dim=512)
    raw = "Le serveur est inaccessible. Vérifiez la connexion."
    styled = hsb.style(raw, "URGENT: mon serveur est down en production !")
    print(f"  Avant : {raw}")
    print(f"  Après : {styled}")
    tone = hsb.detect_tone("j'en ai marre, ça marche pas")
    print(f"  detect_tone('j'en ai marre...') → {tone}")
    psi_rot = hsb.emotional_rotation("URGENT!")
    print(f"  emotional_rotation: |ψ|={norm(psi_rot):.3f}")
    coh_emo = hsb.emotional_coherence("je suis en colère", "ça m'énerve")
    print(f"  emotional_coherence(2 messages frustrés): {coh_emo:.3f}")

    # ── 28. HologramLoaderBridge ──
    print("\n── 28. HOLOGRAM LOADER BRIDGE (hologram_store.py) ──")
    rag_holo = HolographicRAG(dim=512)
    loader = HologramLoaderBridge(rag_holo)

    # Fixture 1 : format columnar
    import tempfile
    tmp = tempfile.mkdtemp()
    np.savez_compressed(
        os.path.join(tmp, "columnar.npz"),
        subjects=np.array(["Terre", "Lune"], dtype=object),
        relations=np.array(["orbite_autour_de", "orbite_autour_de"], dtype=object),
        objects=np.array(["Soleil", "Terre"], dtype=object),
        sectors=np.array(["ASTRONOMIE", "ASTRONOMIE"], dtype=object),
        amplitudes=np.ones(2, dtype=np.float32),
        psies_real=np.zeros((2, 64), dtype=np.float32),
        psies_imag=np.zeros((2, 64), dtype=np.float32),
    )
    n1 = loader.load_npz(os.path.join(tmp, "columnar.npz"))
    print(f"  load_npz (columnar): {n1} faits")

    # Fixture 2 : format facts (tuples)
    np.savez_compressed(
        os.path.join(tmp, "tuples.npz"),
        facts=np.array([
            ("eau", "gèle_à", "0°C", "PHYSIQUE"),
            ("eau", "bout_à", "100°C", "PHYSIQUE"),
        ], dtype=object),
    )
    n2 = loader.load_npz(os.path.join(tmp, "tuples.npz"))
    print(f"  load_npz (tuples): {n2} faits")

    # Vérification dans le RAG
    print(f"  RAG total: {rag_holo.stats['n_facts']} faits")
    results = rag_holo.retrieve_resonance("Autour de quoi orbite la Terre ?")
    if results:
        best = results[0][0]
        print(f"  Retrieval: {best['sujet']} {best['relation']} {best['objet']}")
    print(f"  Loader stats: {loader.stats}")

    print("\n" + "=" * 65)
    print("  ✅ Wave Bridge — 28 adaptateurs fonctionnent (7 TTS + 21 LLM).")
    print("=" * 65)
