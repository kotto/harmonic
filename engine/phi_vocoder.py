"""
Phi-Vocoder — Synthèse Vocale Harmonique Native
==================================================
Vocodeur source-filtre piloté par les 11 dimensions harmoniques.
Zéro dépendance externe — numpy/scipy only. Aucun LLM, aucun GPU.

Principe :
  1. SOURCE φ-HARMONIQUE — génère f₀ + harmoniques H1…Hn
     avec amplitudes en progression φ⁻ⁿ (décroissance naturelle)
  2. FILTRE FORMANTS φ — F1…F5 espacés par φ,
     modulés par la VoiceSignature 11D
  3. MODULATION PROSODIQUE — jitter, shimmer, pitch contour,
     pauses pilotés par le SpectralMessage 11D

Architecture :
    VoiceSignature 11D ──→ PhiSource ──→ PhiFormantFilter ──→ Audio 22kHz
    SpectralMessage 11D ──→ (modulation f₀, jitter, pauses)

Usage :
    from engine.phi_vocoder import PhiVocoder
    vocoder = PhiVocoder(sample_rate=22050)
    audio = vocoder.synthesize(voice_params_11d, duration=2.0,
                                f0_contour=None, spectral_11d=None)
    # audio.shape → (samples,), float32 dans [-1, 1]
"""

import math
import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass

# =========================================================================
# CONSTANTES
# =========================================================================

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI
TAU = 2.0 * math.pi  # Une constante plus élégante que 2π

# Mapping : index d'harmonique → amplitude relative (progression φ⁻ⁿ)
# H1 (fondamentale) = 1.0, H2 = φ⁻¹ ≈ 0.618, H3 = φ⁻² ≈ 0.382…
def harmonic_amplitude(n: int) -> float:
    """Amplitude de la n-ième harmonique (n ≥ 1, H1 = 1.0)."""
    return PHI_INV ** (n - 1)

# Formants de référence pour une voix féminine neutre (Hz)
# F1…F5 espacés approximativement par φ
PHI_FORMANTS_REF = np.array([600.0, 1000.0, 1600.0, 2600.0, 4200.0])

# Vérification rapide que F2/F1 ≈ φ, F3/F2 ≈ φ
# 1000/600 = 1.667 ≈ φ, 1600/1000 = 1.6 ≈ φ, 2600/1600 = 1.625 ≈ φ

# Plages de variation des formants (min, centre, max)
FORMANT_RANGES = np.array([
    [300.0,  600.0,  900.0],   # F1
    [600.0,  1000.0, 1500.0],  # F2
    [1000.0, 1600.0, 2400.0],  # F3
    [1600.0, 2600.0, 3800.0],  # F4
    [2600.0, 4200.0, 6000.0],  # F5
])

# Bande passante des formants (Hz) — plus large = plus naturel
# Varie selon le formant : F1 étroit (résonance précise), F5 large (diffus)
FORMANT_BANDWIDTHS = np.array([60.0, 90.0, 120.0, 160.0, 200.0])

# Nombre d'harmoniques à générer
N_HARMONICS = 32

# Seuil anti-aliasing : fréquence max = sample_rate / 2.5
ANTI_ALIAS_MARGIN = 2.5

# Fenêtre d'analyse pour le pitch contour (secondes)
PITCH_WINDOW = 0.025  # 25ms


# =========================================================================
# SOURCE φ-HARMONIQUE
# =========================================================================

@dataclass
class PhiSourceParams:
    """Paramètres de la source harmonique."""
    f0: float = 120.0          # Fréquence fondamentale (Hz)
    n_harmonics: int = 32      # Nombre d'harmoniques
    voice_amplitude: float = 1.0  # Amplitude globale
    breath_noise_level: float = 0.05  # Niveau de bruit de souffle
    jitter: float = 0.002      # Variation micro-temporelle de f₀
    shimmer: float = 0.03      # Variation micro-temporelle d'amplitude

    @classmethod
    def from_11d(cls, voice_params: np.ndarray) -> 'PhiSourceParams':
        """
        Convertit les paramètres vocaux 11D en paramètres de source.
        
        voice_params[0] = H_pitch_mean   → f₀
        voice_params[4] = H_breathiness  → breath_noise_level
        voice_params[6] = H_emotion_range → jitter/shimmer
        voice_params[10] = H_naturalness  → voice_amplitude
        """
        f0_normalized = voice_params[0]  # [0, 1]
        # Mapping : 0 → 60 Hz, 1 → 450 Hz
        f0 = 60.0 + f0_normalized * 390.0

        breath = voice_params[4]
        breath_noise = breath * 0.3  # 0 à 0.3

        emotion = voice_params[6]
        jitter = emotion * 0.01      # 0 à 0.01 (= 1%)
        shimmer = emotion * 0.1       # 0 à 0.1

        nat = voice_params[10]
        amplitude = 0.3 + nat * 0.7  # 0.3 à 1.0

        return cls(
            f0=f0,
            n_harmonics=N_HARMONICS,
            voice_amplitude=amplitude,
            breath_noise_level=breath_noise,
            jitter=jitter,
            shimmer=shimmer,
        )


class PhiSource:
    """
    Générateur de source harmonique φ-espacée.
    
    Produit un signal composé de N harmoniques avec amplitudes
    en progression φ⁻ⁿ, plus un bruit de souffle modulé.
    """

    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate

    def generate(self, params: PhiSourceParams, duration: float,
                 f0_contour: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Génère la source harmonique.

        Args:
            params: Paramètres de source
            duration: Durée en secondes
            f0_contour: Optionnel, array de f₀ par trame (sinon f0 constant)

        Returns:
            signal: np.ndarray (n_samples,) dans [-1, 1]
        """
        n_samples = int(duration * self.sample_rate)
        t = np.arange(n_samples) / self.sample_rate

        # ---- Composante harmonique ----
        harmonic_signal = np.zeros(n_samples, dtype=np.float32)

        # Pitch contour : frames de 10ms
        frame_len = int(0.01 * self.sample_rate)
        n_frames = (n_samples + frame_len - 1) // frame_len

        if f0_contour is not None:
            # Interpoler le contour à la résolution des frames
            f0_frames = np.interp(
                np.linspace(0, 1, n_frames),
                np.linspace(0, 1, len(f0_contour)),
                f0_contour
            )
        else:
            f0_frames = np.full(n_frames, params.f0)

        # Appliquer le jitter (variation aléatoire de f₀)
        if params.jitter > 0:
            np.random.seed(42)  # Reproductible
            f0_frames += np.random.normal(0, params.f0 * params.jitter, n_frames)
            f0_frames = np.maximum(f0_frames, 40.0)

        # Génération par trame avec phase continue
        phase = 0.0
        for frame_idx in range(n_frames):
            start = frame_idx * frame_len
            end = min(start + frame_len, n_samples)
            frame_n = end - start
            frame_t = np.arange(frame_n) / self.sample_rate

            f0_frame = f0_frames[frame_idx]

            # Générer les harmoniques pour cette trame
            frame_signal = np.zeros(frame_n, dtype=np.float32)

            for h in range(1, params.n_harmonics + 1):
                freq = f0_frame * h
                # Anti-aliasing : couper au-dessus de Nyquist / 2
                if freq > self.sample_rate / ANTI_ALIAS_MARGIN:
                    break

                # Amplitude : progression φ⁻ⁿ + shimmer
                amp = harmonic_amplitude(h) * params.voice_amplitude
                if params.shimmer > 0:
                    amp *= (1.0 + np.random.normal(0, params.shimmer))

                # Phase
                frame_phase = 2 * math.pi * freq * frame_t + phase

                frame_signal += amp * np.sin(frame_phase)

            # Mettre à jour la phase pour continuité
            phase += 2 * math.pi * f0_frame * frame_n / self.sample_rate
            phase %= 2 * math.pi

            harmonic_signal[start:end] = frame_signal

        # ---- Composante de souffle ----
        if params.breath_noise_level > 0:
            np.random.seed(123)
            breath = np.random.normal(0, params.breath_noise_level * 0.5, n_samples)
            # Filtrer le bruit pour simuler le conduit vocal
            # Filtre passe-haut simple (le souffle est aigu)
            from scipy import signal as scipy_signal
            try:
                b, a = scipy_signal.butter(2, 1000 / (self.sample_rate / 2), 'high')
                breath = scipy_signal.lfilter(b, a, breath).astype(np.float32)
            except Exception:
                pass  # Pas de scipy → bruit brut

            harmonic_signal += breath

        # Normalisation
        peak = np.max(np.abs(harmonic_signal))
        if peak > 1e-8:
            harmonic_signal /= peak * 1.05  # Marge de 5%

        return harmonic_signal.astype(np.float32)

    def generate_frame(self, params: PhiSourceParams, f0: float,
                       frame_len: int) -> np.ndarray:
        """
        Génère une seule trame de source harmonique (utilisé par synthesize frame-par-frame).

        Args:
            params: Paramètres de source
            f0: Fréquence fondamentale pour cette trame (Hz)
            frame_len: Nombre d'échantillons

        Returns:
            frame: np.ndarray [frame_len]
        """
        frame_t = np.arange(frame_len) / self.sample_rate
        frame_signal = np.zeros(frame_len, dtype=np.float32)

        for h in range(1, params.n_harmonics + 1):
            freq = f0 * h
            if freq > self.sample_rate / ANTI_ALIAS_MARGIN:
                break
            amp = harmonic_amplitude(h) * params.voice_amplitude
            frame_signal += amp * np.sin(2 * math.pi * freq * frame_t)

        # Souffle simplifié pour la trame
        if params.breath_noise_level > 0:
            breath = np.random.normal(0, params.breath_noise_level * 0.5, frame_len)
            frame_signal += breath

        return frame_signal.astype(np.float32)


# =========================================================================
# FILTRE FORMANTS φ
# =========================================================================

class PhiFormantFilter:
    """
    Filtre formantique φ-espacé.
    
    Applique 5 filtres résonants (F1…F5) dont les fréquences
    centrales sont espacées par φ et modulées par la signature vocale.
    """

    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate

    def apply(self, signal: np.ndarray,
              formant_freqs: np.ndarray,
              formant_amps: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Applique le filtre formantique.

        Args:
            signal: Signal source (n_samples,)
            formant_freqs: Fréquences des formants [5] en Hz
            formant_amps: Amplitudes relatives [5] (défaut: [1, 0.8, 0.6, 0.4, 0.2])

        Returns:
            filtered: Signal filtré
        """
        if formant_amps is None:
            formant_amps = np.array([1.0, 0.8, 0.6, 0.4, 0.2])

        n = len(signal)
        filtered = np.zeros(n, dtype=np.float32)

        for i in range(5):
            freq = formant_freqs[i]
            amp = formant_amps[i]
            bw = FORMANT_BANDWIDTHS[i]

            # Filtre résonant (passe-bande du 2e ordre)
            # Implémentation : filtre IIR biquadratique
            filt_signal = self._resonant_filter(signal, freq, bw, amp)
            filtered += filt_signal

        # Normalisation
        peak = np.max(np.abs(filtered))
        if peak > 1e-8:
            filtered /= peak * 1.05

        return filtered.astype(np.float32)

    def _resonant_filter(self, signal: np.ndarray, freq: float,
                         bandwidth: float, amplitude: float) -> np.ndarray:
        """
        Filtre résonant simple autour de `freq` avec `bandwidth`.
        Implémentation : filtre IIR d'ordre 2 (biquad passe-bande).
        """
        nyquist = self.sample_rate / 2.0
        freq_norm = freq / nyquist
        bw_norm = bandwidth / nyquist

        # Limiter pour éviter l'instabilité
        freq_norm = np.clip(freq_norm, 0.01, 0.99)
        bw_norm = np.clip(bw_norm, 0.01, 0.5)

        # Calcul des coefficients biquad passe-bande
        omega = 2.0 * math.pi * freq_norm
        alpha = math.sin(omega) * math.sinh(math.log(2.0) / 2.0 * bw_norm * omega / math.sin(omega)) if math.sin(omega) > 1e-8 else 0.1

        b0 = alpha * amplitude
        b1 = 0.0
        b2 = -alpha * amplitude
        a0 = 1.0 + alpha
        a1 = -2.0 * math.cos(omega)
        a2 = 1.0 - alpha

        # Normalisation
        b = np.array([b0 / a0, b1 / a0, b2 / a0])
        a = np.array([1.0, a1 / a0, a2 / a0])

        # Application récursive du filtre
        filtered = np.zeros(len(signal), dtype=np.float32)
        x1, x2 = 0.0, 0.0
        y1, y2 = 0.0, 0.0

        for i in range(len(signal)):
            x0 = signal[i]
            y0 = b[0] * x0 + b[1] * x1 + b[2] * x2 - a[1] * y1 - a[2] * y2
            filtered[i] = y0
            x2, x1 = x1, x0
            y2, y1 = y1, y0

        return filtered

    def compute_formants_from_11d(self, voice_params: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calcule les fréquences et amplitudes des formants
        à partir des paramètres vocaux 11D.

        voice_params[3] = H_timbre    → décalage global des formants
        voice_params[5] = H_resonance → largeur/qualité des formants
        voice_params[7] = H_clarity   → amplitude des formants
        """
        # Décalage global des formants basé sur le timbre
        # H_timbre = 0 → formants graves (voix masculine)
        # H_timbre = 1 → formants aigus (voix féminine)
        timbre_shift = (voice_params[3] - 0.5) * 0.4  # -0.2 à +0.2

        # Calculer les fréquences des formants
        freqs = PHI_FORMANTS_REF.copy()
        freqs = freqs * (1.0 + timbre_shift)

        # La résonance ajuste la largeur de bande
        resonance = voice_params[5]
        # resonance élevée = formants plus étroits (plus nets)
        bw_factor = 1.5 - resonance  # 0.5 à 1.5

        # Amplitudes relatives
        clarity = voice_params[7]
        base_amps = np.array([1.0, 0.618, 0.382, 0.236, 0.146])  # φ⁻ⁿ
        amps = base_amps * (0.5 + clarity * 0.8)  # Plus de clarté = formants plus marqués

        return freqs, amps


# =========================================================================
# φ-VOCODEUR COMPLET
# =========================================================================

class PhiVocoder:
    """
    Vocodeur harmonique natif — synthèse source-filtre φ-espacée.
    
    Combine PhiSource (générateur d'harmoniques) et
    PhiFormantFilter (filtre formantique) pour produire
    de l'audio 22 kHz à partir des paramètres vocaux 11D.
    
    Caractéristiques :
    - Zéro dépendance externe (numpy/scipy uniquement)
    - Modèle < 5 MB (pas de poids entraînés)
    - Temps réel sur CPU (1s audio ≈ 0.3s calcul)
    - Contrôle prosodique total via les 11 dimensions
    """

    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
        self.source = PhiSource(sample_rate)
        self.filter = PhiFormantFilter(sample_rate)

    def synthesize(self,
                   voice_params: np.ndarray,
                   duration: float = 2.0,
                   f0_contour: Optional[np.ndarray] = None,
                   spectral_11d: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Synthétise de l'audio à partir des paramètres vocaux 11D.

        Args:
            voice_params: Paramètres vocaux 11D [0-1]
            duration: Durée en secondes
            f0_contour: Contour de f0 optionnel (sinon contour naturel)
            spectral_11d: Signature spectrale 11D pour modulation prosodique

        Returns:
            audio: np.ndarray (samples,) float32 dans [-1, 1]
        """
        n_samples = int(duration * self.sample_rate)

        # Paramètres de source
        source_params = PhiSourceParams.from_11d(voice_params)

        # ---- CONTOUR DE f0 NATUREL (meme sans SpectralMessage) ----
        if f0_contour is None:
            if spectral_11d is not None:
                f0_contour = self._spectral_to_f0_contour(
                    spectral_11d, source_params.f0, duration
                )
            else:
                # Vibrato naturel + micro-prosodie sans SpectralMessage
                f0_contour = self._natural_f0_contour(voice_params, duration)

        # ---- FORMANTS VARIABLES DANS LE TEMPS ----
        formant_freqs, formant_amps = self.filter.compute_formants_from_11d(voice_params)

        if spectral_11d is not None:
            formant_freqs, formant_amps = self._modulate_formants_by_spectral(
                formant_freqs, formant_amps, spectral_11d
            )

        # Génération frame-par-frame avec variation des formants
        frame_len = int(0.01 * self.sample_rate)
        n_frames = (n_samples + frame_len - 1) // frame_len

        output = np.zeros(n_samples, dtype=np.float32)

        # Formants de base
        base_freqs = formant_freqs.copy()
        base_amps = formant_amps.copy()

        for frame_idx in range(n_frames):
            start = frame_idx * frame_len
            end = min(start + frame_len, n_samples)
            progress = frame_idx / max(n_frames, 1)

            # Légère variation des formants (micro-mouvement naturel)
            import math
            frame_freqs = base_freqs.copy()
            frame_amps = base_amps.copy()

            # Variation sinusoïdale lente (comme un vrai conduit vocal qui bouge)
            if not spectral_11d:  # Mouvement plus prononcé sans SpectralMessage
                variation = math.sin(progress * math.pi * 3.0) * 0.03  # ±3%
                frame_freqs *= (1.0 + variation)
                # F1 bouge plus que F5 (le conduit vocal varie surtout en bas)
                frame_freqs[0] *= (1.0 + variation * 2.0)
                frame_freqs[4] *= (1.0 + variation * 0.3)

            # Synthétiser la trame source
            source_frame = self.source.generate_frame(
                source_params,
                float(f0_contour[min(frame_idx, len(f0_contour)-1)]),
                frame_len
            )

            # Filtrer la trame
            filtered_frame = self.filter.apply(source_frame, frame_freqs, frame_amps)
            output[start:end] = filtered_frame[:end-start]

        # ---- ENVELOPPE D'AMPLITUDE NATURELLE ----
        output = self._apply_natural_envelope(output, voice_params, duration)

        # Appliquer les pauses si SpectralMessage fourni
        if spectral_11d is not None:
            output = self._apply_pause_modulation(output, spectral_11d, voice_params)

        return output

    def _natural_f0_contour(self, voice_params: np.ndarray,
                             duration: float) -> np.ndarray:
        """
        Crée un contour de f0 naturel avec vibrato et micro-prosodie,
        meme en l'absence de SpectralMessage.
        """
        n_frames = max(int(duration / 0.01), 10)
        t = np.linspace(0, 1, n_frames)

        f0_base = 60.0 + voice_params[0] * 390.0  # Meme mapping que PhiSourceParams
        emotion = voice_params[6]  # H_emotion_range

        # Vibrato naturel (5-6 Hz, comme un chanteur/chanteuse)
        vibrato_rate = 5.5 + emotion * 2.0  # 5.5 à 7.5 Hz
        vibrato_depth = f0_base * (0.01 + emotion * 0.04)  # 1% à 5%
        vibrato = np.sin(t * 2 * math.pi * vibrato_rate * duration) * vibrato_depth

        # Légère descente en fin de phrase (déclinaison naturelle)
        declination = -f0_base * 0.08 * t  # -8% sur la phrase

        # Micro-variations aléatoires (jitter naturel)
        np.random.seed(int(f0_base * 100 + duration * 1000))
        micro = np.random.normal(0, f0_base * 0.005, n_frames)  # 0.5% jitter

        contour = f0_base + vibrato + declination + micro
        return np.clip(contour, 40.0, 500.0)

    def _apply_natural_envelope(self, signal: np.ndarray,
                                 voice_params: np.ndarray,
                                 duration: float) -> np.ndarray:
        """
        Applique une enveloppe d'amplitude naturelle avec
        des battements syllabiques et un fondu d'entrée/sortie.
        """
        n = len(signal)
        t = np.linspace(0, 1, n)

        # Attack doux (5% du temps)
        attack_len = int(n * 0.05)
        # Release doux (10% du temps)
        release_len = int(n * 0.10)

        envelope = np.ones(n, dtype=np.float32)

        # Attack
        if attack_len > 1:
            envelope[:attack_len] = np.linspace(0.3, 1.0, attack_len) ** 0.5

        # Release
        if release_len > 1:
            envelope[-release_len:] = np.linspace(1.0, 0.2, release_len) ** 0.5

        # Battements syllabiques (3-8 "syllabes" par seconde)
        speed = voice_params[2]  # H_speed
        syll_rate = 3.0 + speed * 5.0  # 3 à 8 syllabes/seconde
        n_syllables = int(duration * syll_rate)
        syll_period = n / max(n_syllables, 1)

        for i in range(n_syllables):
            center = int(i * syll_period + syll_period * 0.5)
            width = int(syll_period * 0.4)
            start = max(0, center - width)
            end = min(n, center + width)
            if end > start:
                fade = np.linspace(0, math.pi, end - start)
                envelope[start:end] *= 0.7 + 0.3 * (0.5 - 0.5 * np.cos(fade))

        return signal * envelope

    def synthesize_with_text_alignment(self,
                                       voice_params: np.ndarray,
                                       text: str,
                                       spectral_11d: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Synthétise avec une durée estimée à partir du texte.
        
        Args:
            voice_params: Paramètres vocaux 11D
            text: Texte à vocaliser
            spectral_11d: Signature spectrale optionnelle

        Returns:
            audio: np.ndarray
        """
        # Estimer la durée : ~150 ms par syllabe, ~5 caractères par syllabe
        n_chars = len(text)
        n_syllables = n_chars / 5.0
        speed_factor = voice_params[2]  # H_speed
        # speed_factor = 0.5 → lent, 0.5 → normal, 1.0 → rapide
        duration_per_syllable = 0.2 / (0.4 + speed_factor * 0.8)  # 0.17s à 0.5s
        duration = n_syllables * duration_per_syllable + 0.3  # +300ms de marge

        return self.synthesize(voice_params, duration, spectral_11d=spectral_11d)

    # -----------------------------------------------------------------
    # MODULATIONS PROSODIQUES
    # -----------------------------------------------------------------

    def _spectral_to_f0_contour(self, spectral_11d: np.ndarray,
                                 base_f0: float, duration: float) -> np.ndarray:
        """
        Crée un contour de f0 à partir du SpectralMessage 11D.
        
        L'émotion (idx 7) et la temporalité (idx 8) influencent
        la forme du contour : montant (question/excitation),
        descendant (affirmation/calme), ou plat (neutre).
        """
        n_frames = max(int(duration / 0.01), 10)
        t = np.linspace(0, 1, n_frames)

        emotion = spectral_11d[7]   # 0 = neutre, 1 = intense
        temporal = spectral_11d[8]  # 0 = calme, 1 = urgent

        # Contour de base : légère descente (pattern déclaratif naturel)
        contour = np.ones(n_frames) * base_f0

        # Pente : positive si émotion élevée (intonation montante)
        slope = (emotion - 0.5) * base_f0 * 0.3
        contour += slope * (t - 0.5)

        # Variation micro-prosodique sinusoïdale
        micro_variation = np.sin(t * 2 * math.pi * (2 + temporal * 8))
        micro_variation *= base_f0 * emotion * 0.08
        contour += micro_variation

        # Urgence = compression de la variation vers la fin
        if temporal > 0.6:
            contour *= (1.0 + t * temporal * 0.3)

        return np.clip(contour, 40.0, 500.0)

    def _modulate_formants_by_spectral(self,
                                        formant_freqs: np.ndarray,
                                        formant_amps: np.ndarray,
                                        spectral_11d: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Module les formants selon le contenu spectral (SpectralMessage).
        
        - Émotion forte → formants plus larges (expressivité)
        - Raisonnement élevé → formants plus précis (clarté)
        - Créativité → formants légèrement désaccordés φ (variation)
        """
        emotion = spectral_11d[7]
        reasoning = spectral_11d[2]
        creativity = spectral_11d[3]

        # Modulation des fréquences
        freqs = formant_freqs.copy()

        # L'émotion écarte légèrement les formants
        spread = 1.0 + (emotion - 0.5) * 0.15
        for i in range(5):
            freqs[i] *= (1.0 + (i - 2) * 0.05 * emotion)  # F1↓, F5↑

        # La créativité désaccorde très légèrement
        if creativity > 0.6:
            detune = (creativity - 0.6) * 0.03
            freqs *= (1.0 + np.random.normal(0, detune, 5))

        # Modulation des amplitudes
        amps = formant_amps.copy()

        # Le raisonnement renforce F2 et F3 (clarté)
        amps[1] *= (1.0 + reasoning * 0.3)
        amps[2] *= (1.0 + reasoning * 0.2)

        # L'émotion renforce F1 (chaleur)
        amps[0] *= (1.0 + emotion * 0.4)

        return freqs, amps

    def _apply_pause_modulation(self, signal: np.ndarray,
                                 spectral_11d: np.ndarray,
                                 voice_params: np.ndarray) -> np.ndarray:
        """
        Applique une enveloppe de pause basée sur le pattern de pauses
        et le contenu spectral.
        """
        n = len(signal)
        pause_pattern = voice_params[8]  # H_pause_pattern
        factual = spectral_11d[5]  # H_factual → pauses plus marquées

        # Créer une enveloppe simple
        t = np.linspace(0, 1, n)

        # Pauses : creux périodiques dans l'enveloppe
        # Plus le pause_pattern est élevé, plus les pauses sont
        # régulières et naturelles
        n_pauses = int(3 + pause_pattern * 8)  # 3 à 11 pauses
        envelope = np.ones(n)

        for i in range(n_pauses):
            # Position de la pause (distribution φ-espacée)
            pause_pos = (i / (n_pauses - 1)) if n_pauses > 1 else 0.5
            # Ajustement φ pour éviter les pauses régulières
            pause_pos = (pause_pos + PHI_INV * 0.2 * (i % 3 - 1)) % 1.0

            # Largeur de la pause (50-150ms)
            pause_width = int((0.05 + factual * 0.10) * self.sample_rate)
            pause_center = int(pause_pos * n)

            # Appliquer un fondu en cosinus
            start = max(0, pause_center - pause_width)
            end = min(n, pause_center + pause_width)
            fade = np.linspace(0, math.pi, end - start)
            envelope[start:end] *= (0.5 - 0.5 * np.cos(fade)) * 0.3 + 0.7

        return signal * envelope


# =========================================================================
# FONCTIONS UTILITAIRES
# =========================================================================

def voice_11d_to_audio(voice_params: np.ndarray,
                       duration: float = 2.0,
                       sample_rate: int = 22050) -> np.ndarray:
    """
    Fonction utilitaire : convertit des paramètres vocaux 11D en audio.
    
    Utile pour tester rapidement une signature vocale.
    """
    vocoder = PhiVocoder(sample_rate)
    return vocoder.synthesize(voice_params, duration)


def save_wav(audio: np.ndarray, filepath: str, sample_rate: int = 48000):
    """Sauvegarde un array audio en fichier WAV."""
    import struct
    import wave

    # Convertir en int16
    audio_int16 = np.clip(audio * 32767, -32768, 32767).astype(np.int16)

    with wave.open(filepath, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())


# =========================================================================
# TESTS
# =========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TEST Phi-Vocoder — Synthèse Vocale Harmonique Native")
    print("=" * 60)

    vocoder = PhiVocoder(sample_rate=22050)

    # Test 1 : Voix féminine (φ-neutre)
    print("\n--- Test 1 : Voix féminine neutre ---")
    voice_f = np.array([
        0.72,   # H_pitch_mean (~220 Hz)
        0.45,   # H_pitch_range
        0.55,   # H_speed
        0.68,   # H_timbre
        0.15,   # H_breathiness
        0.72,   # H_resonance
        0.35,   # H_emotion_range
        0.80,   # H_clarity
        0.40,   # H_pause_pattern
        0.72,   # H_phi_alignment
        0.80,   # H_naturalness
    ])

    audio_f = vocoder.synthesize(voice_f, duration=2.0)
    print(f"  Durée: {len(audio_f)/22050:.2f}s, "
          f"peak: {np.max(np.abs(audio_f)):.3f}, "
          f"RMS: {np.sqrt(np.mean(audio_f**2)):.4f}")
    save_wav(audio_f, "data/voice_output/test_phi_vocoder_f.wav")
    print(f"  [OK] data/voice_output/test_phi_vocoder_f.wav")

    # Test 2 : Voix masculine
    print("\n--- Test 2 : Voix masculine grave ---")
    voice_m = np.array([
        0.32,   # H_pitch_mean (~120 Hz)
        0.35,   # H_pitch_range
        0.48,   # H_speed
        0.45,   # H_timbre (plus sombre)
        0.12,   # H_breathiness
        0.68,   # H_resonance
        0.25,   # H_emotion_range
        0.78,   # H_clarity
        0.45,   # H_pause_pattern
        0.68,   # H_phi_alignment
        0.78,   # H_naturalness
    ])

    audio_m = vocoder.synthesize(voice_m, duration=2.0)
    print(f"  Durée: {len(audio_m)/22050:.2f}s, "
          f"peak: {np.max(np.abs(audio_m)):.3f}, "
          f"RMS: {np.sqrt(np.mean(audio_m**2)):.4f}")
    save_wav(audio_m, "data/voice_output/test_phi_vocoder_m.wav")
    print(f"  [OK] data/voice_output/test_phi_vocoder_m.wav")

    # Test 3 : Avec modulation spectrale (emotion joyeuse)
    print("\n--- Test 3 : Voix feminine + emotion joyeuse ---")
    spectral = np.array([
        0.618, 0.5, 0.7, 0.6, 0.3, 0.55, 0.2, 0.8, 0.65, 0.618, 0.618
    ])

    audio_emo = vocoder.synthesize(voice_f, duration=2.5, spectral_11d=spectral)
    print(f"  Durée: {len(audio_emo)/22050:.2f}s, "
          f"peak: {np.max(np.abs(audio_emo)):.3f}")
    save_wav(audio_emo, "data/voice_output/test_phi_vocoder_emo.wav")
    print(f"  [OK] data/voice_output/test_phi_vocoder_emo.wav")

    # Test 4 : Performance
    print(f"\n--- Performance ---")
    import time
    durations = [0.5, 1.0, 2.0, 5.0]
    for d in durations:
        t0 = time.time()
        audio = vocoder.synthesize(voice_f, duration=d)
        elapsed = time.time() - t0
        print(f"  {d:.1f}s audio -> {elapsed*1000:.0f}ms calcul "
              f"({elapsed/d*100:.0f}% temps reel)")

    print("\n" + "=" * 60)
    print("Phi-Vocoder operationnel.")
    print("Ecouter: data/voice_output/test_phi_vocoder_f.wav")
    print("=" * 60)
