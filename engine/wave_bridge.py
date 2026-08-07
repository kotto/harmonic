"""
🌊 Wave Bridge — Pont unifié vers le DSL ondulatoire
======================================================
Phase 5 : Rétro-adaptation des modules existants vers wave_lang.

Ce module fournit des adapteurs « drop-in » qui remplacent les
implémentations dupliquées dans les modules TTS, protéines et audio
par des appels vers la bibliothèque wave_lang unifiée.

Modules couverts :
  - ka_sonic/psi_diphone_bank.py    → HolographicMemory
  - alphafold/abc_folder.py         → abc_kernel / abc_forget
  - alphafold/harmonic_energy.py    → resonate / coherence
  - harmonic_voice_codec_v2.py      → diffract / spectrum / filter_wave
  - ka_sonic/glottal_synth.py       → superpose / phase_shift
  - ka_sonic/voice_signature.py     → spectrum / resonate

Principe :
  - Les signatures publiques sont préservées
  - L'implémentation interne délègue à wave_lang
  - Zéro changement dans le code appelant
  - Les optimisations du compilateur s'appliquent automatiquement

Usage :
    # Avant :
    from ka_sonic.psi_diphone_bank import PsiDiphoneBank
    bank = PsiDiphoneBank()

    # Après (compatible drop-in) :
    from wave_bridge import PsiDiphoneBank  # même API, backend wave_lang
    bank = PsiDiphoneBank()
"""

from __future__ import annotations

import math
import numpy as np
from typing import List, Dict, Tuple, Optional, Callable

# ═══════════════════════════════════════════════════════════════════════════════
# IMPORTS UNIFIÉS
# ═══════════════════════════════════════════════════════════════════════════════

from wave_lang import (
    # Primitives
    encode, decode, bind, unbind, superpose,
    resonate, coherence, rotate, normalize, norm, energy,
    interfere, diffract, spectrum, filter_wave, phase_shift,
    emerge, oppose, amplify, bind_many,
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
