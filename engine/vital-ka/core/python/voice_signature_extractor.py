"""
Extracteur de Signatures Vocales 11D — Parselmouth + SpeechBrain
================================================================
Extrait les 11 dimensions harmoniques d'une voix à partir d'un fichier audio,
conformément au modèle défini dans IMPLEMENTATION_MODELE_VOCAL_HARMONIQUE.md.

Dimensions extraites :
    H_pitch_mean      — f₀ moyen
    H_pitch_range     — Écart-type f₀ / variation de hauteur
    H_speed           — Débit syllabique estimé
    H_timbre          — Centroïde spectral
    H_breathiness    — Ratio bruit/harmonique
    H_resonance       — Alignement φ des formants
    H_emotion_range   — Plage expressive (jitter/shimmer)
    H_clarity         — Netteté articulatoire
    H_pause_pattern   — Pattern de pauses
    H_phi_alignment   — Score φ global
    H_naturalness     — Score MOS-like estimé

Dépendances : parselmouth, numpy, scipy, speechbrain (optionnel pour ECAPA-TDNN)
Usage :
    extractor = VoiceSignatureExtractor()
    signature = extractor.extract("audio.wav")
    print(signature)  # dict avec 11 dimensions
"""

import math
import numpy as np
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field
from pathlib import Path

# =========================================================================
# CONSTANTES HARMONIQUES
# =========================================================================

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI  # ≈ 0.618
PHI_SQ = PHI * PHI    # φ² ≈ 2.618

# Plages de normalisation pour chaque dimension (min, max, φ_ref)
# φ_ref = point d'équilibre harmonique idéal
VOICE_RANGES = {
    'H_pitch_mean':     (50.0,   500.0,  220.0),   # Hz, φ_ref = 220 Hz (~φ × 136)
    'H_pitch_range':    (0.0,    120.0,  74.0),     # Hz, écart-type f₀
    'H_speed':          (2.0,    8.0,    4.94),     # syllabes/seconde (8/φ)
    'H_timbre':         (500.0,  4000.0, 2472.0),   # Hz centroïde spectral (4000/φ)
    'H_breathiness':    (0.0,    0.5,    0.191),    # ratio bruit/harmonique
    'H_resonance':      (0.0,    1.0,    0.618),    # score φ formants
    'H_emotion_range':  (0.0,    0.05,   0.019),    # jitter (0.05/φ²)
    'H_clarity':        (0.0,    1.0,    0.618),    # ratio HNR
    'H_pause_pattern':  (0.0,    1.0,    0.382),    # φ⁻²
    'H_phi_alignment':  (0.0,    1.0,    0.618),    # score φ global
    'H_naturalness':    (1.0,    5.0,    4.05),     # MOS-like (5 - 1/φ)
}

# Noms affichables et descriptions
DIMENSION_NAMES = {
    'H_pitch_mean':     'f₀ moyen (Hz)',
    'H_pitch_range':    'Plage de hauteur (Hz)',
    'H_speed':          'Débit syllabique (syll/s)',
    'H_timbre':         'Centroïde spectral (Hz)',
    'H_breathiness':    'Ratio bruit/harmonique',
    'H_resonance':      'Alignement φ des formants',
    'H_emotion_range':  'Plage expressive (jitter)',
    'H_clarity':        'Netteté articulatoire',
    'H_pause_pattern':  'Pattern de pauses',
    'H_phi_alignment':  'Score φ global',
    'H_naturalness':    'Score MOS estimé',
}


# =========================================================================
# STRUCTURE DE DONNÉES
# =========================================================================

@dataclass
class VoiceSignature:
    """Signature vocale 11D complète avec métadonnées."""
    # 11 dimensions normalisées [0, 1]
    H_pitch_mean: float = 0.618
    H_pitch_range: float = 0.618
    H_speed: float = 0.618
    H_timbre: float = 0.618
    H_breathiness: float = 0.191
    H_resonance: float = 0.618
    H_emotion_range: float = 0.382
    H_clarity: float = 0.618
    H_pause_pattern: float = 0.382
    H_phi_alignment: float = 0.618
    H_naturalness: float = 0.75  # ~4.0 MOS

    # Valeurs brutes (avant normalisation)
    raw_values: Optional[Dict[str, float]] = None

    # Métadonnées
    source_file: Optional[str] = None
    duration_seconds: float = 0.0
    sample_rate: int = 22050
    speaker_id: Optional[str] = None
    language: Optional[str] = "fr"

    def to_dict(self) -> Dict[str, float]:
        """Retourne les 11 dimensions sous forme de dict."""
        return {
            'H_pitch_mean': self.H_pitch_mean,
            'H_pitch_range': self.H_pitch_range,
            'H_speed': self.H_speed,
            'H_timbre': self.H_timbre,
            'H_breathiness': self.H_breathiness,
            'H_resonance': self.H_resonance,
            'H_emotion_range': self.H_emotion_range,
            'H_clarity': self.H_clarity,
            'H_pause_pattern': self.H_pause_pattern,
            'H_phi_alignment': self.H_phi_alignment,
            'H_naturalness': self.H_naturalness,
        }

    def to_array(self) -> np.ndarray:
        """Retourne les 11 dimensions sous forme de np.ndarray [11]."""
        return np.array([
            self.H_pitch_mean, self.H_pitch_range, self.H_speed,
            self.H_timbre, self.H_breathiness, self.H_resonance,
            self.H_emotion_range, self.H_clarity, self.H_pause_pattern,
            self.H_phi_alignment, self.H_naturalness,
        ])

    @classmethod
    def from_array(cls, arr: np.ndarray, **metadata) -> 'VoiceSignature':
        """Crée une VoiceSignature à partir d'un array [11]."""
        return cls(
            H_pitch_mean=float(arr[0]),
            H_pitch_range=float(arr[1]),
            H_speed=float(arr[2]),
            H_timbre=float(arr[3]),
            H_breathiness=float(arr[4]),
            H_resonance=float(arr[5]),
            H_emotion_range=float(arr[6]),
            H_clarity=float(arr[7]),
            H_pause_pattern=float(arr[8]),
            H_phi_alignment=float(arr[9]),
            H_naturalness=float(arr[10]),
            **metadata,
        )

    def phi_distance_to(self, other: 'VoiceSignature') -> float:
        """
        Calcule la distance harmonique φ-pondérée entre deux signatures.
        Les dimensions sont pondérées par φ pour donner plus de poids
        aux harmoniques supérieures (timbre, résonance, clarté).
        """
        weights = np.array([
            1.0,           # H_pitch_mean
            1.0,           # H_pitch_range
            1.0,           # H_speed
            PHI,           # H_timbre (poids φ : timbre = signature unique)
            PHI_INV,       # H_breathiness
            PHI * PHI_INV, # H_resonance (poids 1)
            PHI_INV ** 2,  # H_emotion_range
            PHI,           # H_clarity
            PHI_INV,       # H_pause_pattern
            PHI,           # H_phi_alignment
            PHI,           # H_naturalness
        ])
        weights = weights / weights.sum()

        a = self.to_array()
        b = other.to_array()
        # Distance euclidienne pondérée normalisée
        diff = (a - b) ** 2
        return float(np.sqrt(np.sum(diff * weights)))

    def dominant_style(self) -> str:
        """Détermine le style vocal dominant basé sur les dimensions."""
        if self.H_breathiness > 0.5:
            return "chuchoté"
        if self.H_emotion_range > 0.65:
            return "expressif"
        if self.H_clarity > 0.8:
            return "clair/narratif"
        if self.H_speed > 0.7:
            return "rapide/dynamique"
        if self.H_speed < 0.35:
            return "lent/posé"
        if self.H_timbre > 0.7:
            return "brillant"
        if self.H_resonance > 0.75:
            return "résonant/chaud"
        return "neutre"


# =========================================================================
# EXTRACTEUR DE SIGNATURES VOCALES
# =========================================================================

class VoiceSignatureExtractor:
    """
    Extrait les 11 dimensions harmoniques d'une voix à partir d'un fichier audio.

    Utilise Parselmouth (wrapper Praat) pour l'analyse acoustique.
    SpeechBrain ECAPA-TDNN est utilisé en option pour l'embedding locuteur.

    Usage :
        extractor = VoiceSignatureExtractor()
        sig = extractor.extract("voix.wav")
        print(sig.to_dict())
    """

    def __init__(self, sample_rate: int = 22050, use_speechbrain: bool = False):
        """
        Args:
            sample_rate: Taux d'échantillonnage cible
            use_speechbrain: Si True, charge ECAPA-TDNN pour embedding locuteur
        """
        self.sample_rate = sample_rate
        self.use_speechbrain = use_speechbrain
        self._sb_encoder = None

        # Vérifier la disponibilité de Parselmouth
        try:
            import parselmouth
            self._parselmouth_available = True
        except ImportError:
            print("[VoiceSignatureExtractor] WARN Parselmouth non installe. "
                  "pip install parselmouth praat-parselmouth")
            self._parselmouth_available = False

        # Vérifier SpeechBrain (optionnel)
        if use_speechbrain:
            try:
                import speechbrain
                self._speechbrain_available = True
            except ImportError:
                print("[VoiceSignatureExtractor] WARN SpeechBrain non installe. "
                      "pip install speechbrain")
                self._speechbrain_available = False

    # -----------------------------------------------------------------
    # MÉTHODE PRINCIPALE
    # -----------------------------------------------------------------

    def extract(self, audio_path: str) -> VoiceSignature:
        """
        Extrait la signature vocale 11D d'un fichier audio.

        Args:
            audio_path: Chemin vers le fichier audio (WAV, MP3, FLAC…)

        Returns:
            VoiceSignature avec les 11 dimensions et métadonnées
        """
        if not self._parselmouth_available:
            return self._fallback_signature(audio_path)

        import parselmouth

        # Charger l'audio
        try:
            snd = parselmouth.Sound(str(audio_path))
        except Exception as e:
            print(f"[VoiceSignatureExtractor] Erreur chargement {audio_path}: {e}")
            return self._fallback_signature(audio_path)

        duration = snd.duration

        # Resample si nécessaire
        if snd.sampling_frequency != self.sample_rate:
            snd = snd.resample(self.sample_rate)

        # --- 11 extractions ---

        # H1 : H_pitch_mean — f₀ moyen
        f0, harmonics, hnr, jitter, shimmer = self._extract_harmonics(snd)

        # H2 : H_pitch_range — écart-type f₀
        H_pitch_mean = self._normalize('H_pitch_mean', np.mean(f0)) if len(f0) > 0 else 0.5
        H_pitch_range = self._normalize('H_pitch_range', np.std(f0)) if len(f0) > 0 else 0.3

        # H3 : H_speed — débit syllabique estimé
        H_speed = self._measure_speed(snd)

        # H4 : H_timbre — centroïde spectral
        H_timbre = self._measure_timbre(snd)

        # H5 : H_breathiness — ratio bruit/harmonique
        H_breathiness = self._measure_breath(hnr)

        # H6 : H_resonance — alignement φ des formants
        H_resonance = self._measure_phi_spacing(harmonics, snd)

        # H7 : H_emotion_range — plage expressive (jitter/shimmer)
        H_emotion_range = self._measure_emotion_range(jitter, shimmer)

        # H8 : H_clarity — netteté articulatoire
        H_clarity = self._measure_clarity(hnr, f0)

        # H9 : H_pause_pattern — pattern de pauses
        H_pause_pattern = self._measure_pause_pattern(snd, f0)

        # H10 : H_phi_alignment — score φ global
        H_phi_alignment = self._measure_phi_alignment(
            H_pitch_mean, H_pitch_range, H_speed, H_timbre,
            H_breathiness, H_resonance, H_emotion_range,
            H_clarity, H_pause_pattern
        )

        # H11 : H_naturalness — score MOS-like
        H_naturalness = self._measure_naturalness(
            H_pitch_mean, H_clarity, H_breathiness, H_resonance, H_emotion_range
        )

        # Construire la signature
        raw_values = {
            'f0_mean': np.mean(f0) if len(f0) > 0 else 0.0,
            'f0_std': np.std(f0) if len(f0) > 0 else 0.0,
            'hnr_mean': np.mean(hnr) if len(hnr) > 0 else 0.0,
            'jitter_mean': jitter,
            'shimmer_mean': shimmer,
        }

        return VoiceSignature(
            H_pitch_mean=H_pitch_mean,
            H_pitch_range=H_pitch_range,
            H_speed=H_speed,
            H_timbre=H_timbre,
            H_breathiness=H_breathiness,
            H_resonance=H_resonance,
            H_emotion_range=H_emotion_range,
            H_clarity=H_clarity,
            H_pause_pattern=H_pause_pattern,
            H_phi_alignment=H_phi_alignment,
            H_naturalness=H_naturalness,
            raw_values=raw_values,
            source_file=str(audio_path),
            duration_seconds=float(duration),
            sample_rate=self.sample_rate,
        )

    # -----------------------------------------------------------------
    # EXTRACTIONS INDIVIDUELLES
    # -----------------------------------------------------------------

    def _extract_harmonics(self, snd) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float, float]:
        """
        Extrait f0, harmoniques HNR, jitter, shimmer via Parselmouth / Praat.
        Returns: (f0_array, harmonics_array, hnr_array, jitter_avg, shimmer_avg)
        """
        import parselmouth

        # Extraire le pitch (f0)
        # selected_array est un ndarray structure avec champs 'frequency', 'strength'
        try:
            pitch = snd.to_pitch(time_step=0.01, pitch_floor=50.0, pitch_ceiling=500.0)
            if pitch.selected_array is not None and 'frequency' in pitch.selected_array.dtype.names:
                f0_values = pitch.selected_array['frequency']
            else:
                f0_values = np.array([120.0])
        except Exception:
            f0_values = np.array([120.0])

        # Filtrer les silences (f0 == 0)
        f0_values = f0_values[f0_values > 0]

        # Extraire les harmoniques (HNR = Harmonics-to-Noise Ratio)
        try:
            hnr_obj = snd.to_harmonicity(time_step=0.01)
            hnr_values = np.array(hnr_obj.values).flatten()
            hnr_values = hnr_values[hnr_values > -200]  # Filtrer valeurs aberrantes
        except Exception:
            hnr_values = np.array([10.0])  # Valeur par defaut si echec

        # Jitter et Shimmer via PointProcess
        try:
            pp = snd.to_point_process(pitch) if pitch.n_frames > 0 else None
            if pp is not None and pp.get_number_of_points() > 1:
                jitter_avg = float(pp.get_jitter_local())
                shimmer_avg = float(pp.get_shimmer_local())
            else:
                jitter_avg = 0.01
                shimmer_avg = 0.05
        except Exception:
            jitter_avg = 0.01
            shimmer_avg = 0.05

        return (
            f0_values if len(f0_values) > 0 else np.array([120.0]),
            np.array([]),  # harmonics placeholder
            hnr_values,
            jitter_avg,
            shimmer_avg,
        )

    def _normalize(self, dim_name: str, raw_value: float) -> float:
        """
        Normalise une valeur brute en [0, 1] avec scaling φ.
        Le point φ_ref est mappé à φ⁻¹ ≈ 0.618 (équilibre harmonique).
        """
        vmin, vmax, phi_ref = VOICE_RANGES[dim_name]

        # Clipper d'abord
        value = np.clip(raw_value, vmin, vmax)

        # Normalisation non-linéaire centrée sur φ_ref
        # En dessous de φ_ref : scaling sigmoïde
        # Au-dessus de φ_ref : scaling exponentiel
        if value <= phi_ref:
            # Mapping [vmin, phi_ref] → [0, PHI_INV]
            normalized = PHI_INV * ((value - vmin) / (phi_ref - vmin + 1e-8))
        else:
            # Mapping [phi_ref, vmax] → [PHI_INV, 1]
            normalized = PHI_INV + (1.0 - PHI_INV) * ((value - phi_ref) / (vmax - phi_ref + 1e-8))

        return float(np.clip(normalized, 0.0, 1.0))

    def _measure_speed(self, snd) -> float:
        """
        Estime le débit syllabique en syllabes/seconde.
        Utilise l'enveloppe d'intensité pour détecter les noyaux syllabiques.

        Méthode : compter les pics d'intensité > seuil adaptatif,
        diviser par la durée de parole effective.
        """
        import parselmouth

        # Intensité
        intensity = snd.to_intensity(time_step=0.01)
        int_values = intensity.values.flatten()
        int_values = int_values[int_values > 0]

        if len(int_values) < 3:
            return self._normalize('H_speed', 4.0)

        # Détection des pics syllabiques
        # Un pic = maximum local au-dessus du percentile 40%
        threshold = np.percentile(int_values, 40)
        above_threshold = int_values > threshold
        syllable_count = 0
        for i in range(1, len(above_threshold) - 1):
            # Détection de front montant : passage en dessous → au-dessus du seuil
            if not above_threshold[i - 1] and above_threshold[i]:
                syllable_count += 1

        # Durée effective de parole (intensité > seuil)
        speech_duration = np.sum(above_threshold) * 0.01  # time_step = 0.01s

        if speech_duration < 0.1:
            return self._normalize('H_speed', 4.0)

        syllable_rate = syllable_count / speech_duration
        return self._normalize('H_speed', syllable_rate)

    def _measure_timbre(self, snd) -> float:
        """
        Mesure le centroïde spectral (centre de gravité du spectre).
        Capturé via l'analyse spectrale à court terme.
        """
        # Utiliser le spectre moyen
        try:
            import parselmouth
            spectrogram = snd.to_spectrogram(window_length=0.025)
            # Calculer le centroïde spectral moyen
            freqs = spectrogram.bin_center_frequencies()
            if len(freqs) == 0:
                return self._normalize('H_timbre', 2000.0)

            # Moyenne pondérée par l'énergie
            spec_matrix = spectrogram.values  # [freq_bins, time_frames]
            if spec_matrix.size == 0:
                return self._normalize('H_timbre', 2000.0)

            # Énergie moyenne par fréquence
            mean_spec = np.mean(spec_matrix, axis=1)
            mean_spec = np.maximum(mean_spec, 0)

            if np.sum(mean_spec) == 0:
                return self._normalize('H_timbre', 2000.0)

            centroid = np.sum(freqs * mean_spec) / np.sum(mean_spec)
            return self._normalize('H_timbre', float(centroid))

        except Exception:
            return self._normalize('H_timbre', 2000.0)  # Valeur médiane

    def _measure_breath(self, hnr_values: np.ndarray) -> float:
        """
        Mesure le ratio bruit/harmonique (breathiness).
        HNR faible = voix soufflée/chuchotée.
        """
        if len(hnr_values) == 0:
            return self._normalize('H_breathiness', 0.2)

        # HNR moyen en dB — plus bas = plus de souffle
        mean_hnr = float(np.mean(hnr_values))

        # Convertir HNR en ratio : breathiness = 1 / (1 + 10^(HNR/10))
        # Simplification : breathiness ~ exp(-HNR / 20)
        breath_ratio = math.exp(-mean_hnr / 20.0)
        breath_ratio = np.clip(breath_ratio, 0.0, 1.0)

        return self._normalize('H_breathiness', breath_ratio)

    def _measure_phi_spacing(self, harmonics: np.ndarray, snd) -> float:
        """
        Mesure l'alignement φ des formants.
        Vérifie si les formants (F1, F2, F3) sont espacés selon φ.

        Un espacement F2/F1 ≈ φ et F3/F2 ≈ φ indique une voix
        particulièrement résonante et agréable (corde vocale harmonique).
        """
        try:
            import parselmouth

            # Extraire les formants
            formant = snd.to_formant_burg(max_number_of_formants=5,
                                          window_length=0.025,
                                          time_step=0.01)

            # Formants moyens sur la durée
            n_frames = formant.get_number_of_frames()
            if n_frames < 2:
                return self._normalize('H_resonance', 0.5)

            f1_vals, f2_vals, f3_vals = [], [], []
            for i in range(1, n_frames + 1):
                t = formant.get_time_from_frame_number(i)
                try:
                    f1_vals.append(formant.get_value_at_time(1, t))
                    f2_vals.append(formant.get_value_at_time(2, t))
                    f3_vals.append(formant.get_value_at_time(3, t))
                except Exception:
                    continue

            if len(f1_vals) < 2:
                return self._normalize('H_resonance', 0.5)

            f1 = np.median(f1_vals)
            f2 = np.median(f2_vals)
            f3 = np.median(f3_vals)

            # Calculer les ratios
            ratio_21 = f2 / f1 if f1 > 0 else 1.0
            ratio_32 = f3 / f2 if f2 > 0 else 1.0

            # Écart aux ratios φ idéaux
            phi_error = abs(ratio_21 - PHI) + abs(ratio_32 - PHI)
            phi_error = np.clip(phi_error, 0.0, 5.0)

            # Score de résonance : 1 - erreur_normalisée
            resonance_score = 1.0 - (phi_error / 5.0)
            resonance_score = np.clip(resonance_score, 0.0, 1.0)

            return self._normalize('H_resonance', resonance_score)

        except Exception:
            return self._normalize('H_resonance', PHI_INV)

    def _measure_emotion_range(self, jitter: float, shimmer: float) -> float:
        """
        Mesure la plage expressive via jitter et shimmer.
        Jitter = variation de f₀ (micro-prosodie)
        Shimmer = variation d'amplitude
        """
        # Combiner jitter et shimmer avec pondération φ
        emotion = jitter * PHI + shimmer * PHI_INV
        return self._normalize('H_emotion_range', emotion)

    def _measure_clarity(self, hnr_values: np.ndarray, f0_values: np.ndarray) -> float:
        """
        Mesure la netteté articulatoire.
        Combine HNR (signal/bruit) et stabilité de f₀.
        """
        # Composante HNR
        if len(hnr_values) > 0:
            mean_hnr = float(np.mean(hnr_values))
            # Mapping : HNR de 0 à 25 dB → clarity de 0 à 1
            hnr_clarity = np.clip(mean_hnr / 25.0, 0.0, 1.0)
        else:
            hnr_clarity = 0.5

        # Composante stabilité f₀ (faible variance = bonne clarté)
        if len(f0_values) > 5:
            f0_cv = np.std(f0_values) / (np.mean(f0_values) + 1e-8)
            stability = 1.0 - np.clip(f0_cv * 3.0, 0.0, 1.0)
        else:
            stability = 0.5

        # Mélange φ-pondéré
        clarity = hnr_clarity * PHI_INV + stability * (1.0 - PHI_INV)
        return self._normalize('H_clarity', clarity)

    def _measure_pause_pattern(self, snd, f0_values: np.ndarray) -> float:
        """
        Analyse le pattern de pauses.
        Ratio de silence vs parole, distribution des durées de pauses.
        Un score élevé = pauses naturelles, bien réparties.
        """
        try:
            import parselmouth

            # Détection des segments voisés/non-voisés via l'intensité
            intensity = snd.to_intensity(time_step=0.01)
            int_values = intensity.values.flatten()

            if len(int_values) < 2:
                return self._normalize('H_pause_pattern', 0.4)

            # Seuil de silence : 25e percentile
            silence_threshold = np.percentile(int_values, 25)
            is_silence = int_values <= silence_threshold

            # Ratio de pauses
            pause_ratio = float(np.mean(is_silence))

            # Pattern idéal : ~25-30% de pauses (φ⁻² ≈ 0.382)
            pattern_score = 1.0 - abs(pause_ratio - PHI_INV**2) / 0.5
            pattern_score = np.clip(pattern_score, 0.0, 1.0)

            return self._normalize('H_pause_pattern', pattern_score)

        except Exception:
            return self._normalize('H_pause_pattern', PHI_INV**2)

    def _measure_phi_alignment(self, *dims: float) -> float:
        """
        Mesure le score φ global : à quel point les 9 premières dimensions
        sont alignées avec les proportions φ (équilibre harmonique global).
        """
        arr = np.array(dims)

        # Score 1 : écart-type des dimensions (φ⁻² idéal)
        std = float(np.std(arr))
        std_score = 1.0 - abs(std - PHI_INV**2) / 0.5

        # Score 2 : les dimensions H_timbre (idx 3), H_resonance (idx 5),
        # H_naturalness (déjà calculée) devraient dominer
        # Vérifier que H_timbre et H_resonance ne sont pas trop proches
        # (φ-spacing : elles devraient être distantes d'au moins φ⁻²)
        if len(dims) >= 6:
            dist_timbre_res = abs(dims[3] - dims[5])  # timbre vs resonance
            spacing_score = 1.0 - abs(dist_timbre_res - PHI_INV) / 0.5
        else:
            spacing_score = 0.618

        phi_align = std_score * PHI_INV + spacing_score * (1.0 - PHI_INV)
        return self._normalize('H_phi_alignment', np.clip(phi_align, 0.0, 1.0))

    def _measure_naturalness(self, pitch_mean: float, clarity: float,
                             breath: float, resonance: float,
                             emotion: float) -> float:
        """
        Estime un score MOS-like (1-5) basé sur les dimensions extraites.

        Formule : MOS = 5 - pénalités sur chaque dimension
        - Pénalité si pitch trop loin de φ_ref
        - Pénalité si breathiness trop élevée
        - Bonus si clarté bonne
        - Bonus si résonance bonne
        """
        # Chaque dimension contribue avec un poids φ-décroissant
        # Les dimensions sont en [0, 1], on veut un MOS en [1, 5]

        # Score de base : 3.0 (milieu)
        mos = 3.0

        # Bonus clarté : +1 si clarté > 0.618
        mos += (clarity - PHI_INV) * 2.0

        # Bonus résonance : +0.5 si résonance > 0.618
        mos += (resonance - PHI_INV) * 1.0

        # Pénalité breathiness : -0.5 si breathiness > 0.3
        if breath > 0.3:
            mos -= (breath - 0.3) * 2.0

        # Pénalité émotion excessive : -0.3 si emotion_range > 0.7
        if emotion > 0.7:
            mos -= (emotion - 0.7) * 1.5

        # Stabilité pitch : pénalité si trop loin de l'équilibre
        pitch_dev = abs(pitch_mean - PHI_INV)
        mos -= pitch_dev * 1.5

        mos = np.clip(mos, 1.0, 5.0)
        return self._normalize('H_naturalness', mos)

    # -----------------------------------------------------------------
    # FALLBACK
    # -----------------------------------------------------------------

    def _fallback_signature(self, audio_path: str) -> VoiceSignature:
        """
        Signature par défaut quand Parselmouth n'est pas disponible.
        Utilise des valeurs φ-basées pour une voix neutre équilibrée.
        """
        return VoiceSignature(
            H_pitch_mean=PHI_INV,       # 0.618
            H_pitch_range=PHI_INV**2,   # 0.382
            H_speed=PHI_INV,
            H_timbre=PHI_INV,
            H_breathiness=PHI_INV**3,   # 0.236
            H_resonance=PHI_INV,
            H_emotion_range=PHI_INV**2,
            H_clarity=0.75,
            H_pause_pattern=PHI_INV**2,
            H_phi_alignment=PHI_INV,
            H_naturalness=0.75,
            source_file=str(audio_path),
            sample_rate=self.sample_rate,
        )


# =========================================================================
# BANQUE DE PROFILS DE RÉFÉRENCE
# =========================================================================

# Profils prédéfinis (seront enrichis par extraction réelle sur corpus)
REFERENCE_PROFILES = {
    "lj_speech_female_us": VoiceSignature(
        H_pitch_mean=0.72,      # ~220 Hz → normalisé (220-50)/(500-50) ≈ 0.378 → ajusté φ
        H_pitch_range=0.45,
        H_speed=0.55,
        H_timbre=0.68,
        H_breathiness=0.18,
        H_resonance=0.72,
        H_emotion_range=0.42,
        H_clarity=0.85,
        H_pause_pattern=0.40,
        H_phi_alignment=0.72,
        H_naturalness=0.82,
    ),
    "vctk_p225_male_uk": VoiceSignature(
        H_pitch_mean=0.38,      # ~110 Hz
        H_pitch_range=0.35,
        H_speed=0.48,
        H_timbre=0.55,
        H_breathiness=0.15,
        H_resonance=0.68,
        H_emotion_range=0.30,
        H_clarity=0.78,
        H_pause_pattern=0.45,
        H_phi_alignment=0.68,
        H_naturalness=0.78,
    ),
    "vctk_p227_female_uk": VoiceSignature(
        H_pitch_mean=0.65,
        H_pitch_range=0.55,
        H_speed=0.62,
        H_timbre=0.72,
        H_breathiness=0.20,
        H_resonance=0.74,
        H_emotion_range=0.52,
        H_clarity=0.82,
        H_pause_pattern=0.38,
        H_phi_alignment=0.74,
        H_naturalness=0.80,
    ),
    "ted_speaker_1_female_us": VoiceSignature(
        H_pitch_mean=0.42,      # ~130 Hz
        H_pitch_range=0.60,
        H_speed=0.58,
        H_timbre=0.65,
        H_breathiness=0.12,
        H_resonance=0.81,
        H_emotion_range=0.55,
        H_clarity=0.88,
        H_pause_pattern=0.50,
        H_phi_alignment=0.81,
        H_naturalness=0.85,
    ),
    "librimix_best": VoiceSignature(
        H_pitch_mean=PHI_INV,
        H_pitch_range=0.45,
        H_speed=PHI_INV,
        H_timbre=0.65,
        H_breathiness=0.15,
        H_resonance=0.72,
        H_emotion_range=0.40,
        H_clarity=0.80,
        H_pause_pattern=0.42,
        H_phi_alignment=0.72,
        H_naturalness=0.80,
    ),
    "css10_fr_native": VoiceSignature(
        H_pitch_mean=0.58,      # ~180 Hz
        H_pitch_range=0.48,
        H_speed=0.52,
        H_timbre=0.62,
        H_breathiness=0.16,
        H_resonance=0.70,
        H_emotion_range=0.38,
        H_clarity=0.80,
        H_pause_pattern=0.42,
        H_phi_alignment=0.70,
        H_naturalness=0.78,
    ),
}


# =========================================================================
# FONCTIONS UTILITAIRES
# =========================================================================

def extract_corpus_signatures(audio_dir: str,
                              output_json: Optional[str] = None,
                              recursive: bool = True) -> List[Dict]:
    """
    Extrait les signatures 11D de tous les fichiers audio d'un répertoire.

    Args:
        audio_dir: Répertoire contenant les fichiers audio
        output_json: Si fourni, sauvegarde les signatures en JSON
        recursive: Parcours récursif des sous-dossiers

    Returns:
        Liste de dicts {file, signature_11d, duration, ...}
    """
    import json

    audio_extensions = {'.wav', '.mp3', '.flac', '.ogg', '.m4a', '.aac'}
    audio_files = []

    path = Path(audio_dir)
    if recursive:
        for ext in audio_extensions:
            audio_files.extend(path.rglob(f'*{ext}'))
            audio_files.extend(path.rglob(f'*{ext.upper()}'))
    else:
        for f in path.iterdir():
            if f.suffix.lower() in audio_extensions:
                audio_files.append(f)

    extractor = VoiceSignatureExtractor()
    signatures = []

    for i, audio_file in enumerate(audio_files):
        print(f"[{i+1}/{len(audio_files)}] Extraction: {audio_file.name}")
        try:
            sig = extractor.extract(str(audio_file))
            signatures.append({
                'file': str(audio_file),
                'filename': audio_file.name,
                'signature_11d': sig.to_dict(),
                'raw_values': sig.raw_values,
                'duration': sig.duration_seconds,
            })
        except Exception as e:
            print(f"  ⚠ Erreur: {e}")

    if output_json:
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(signatures, f, indent=2, ensure_ascii=False)
        print(f"\n✓ {len(signatures)} signatures sauvegardées dans {output_json}")

    return signatures


def select_top_voices(signatures_json: str, top_n: int = 20) -> List[Dict]:
    """
    Sélectionne les N meilleures voix selon le score H_naturalness
    trié par distance φ minimale.
    """
    import json

    with open(signatures_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Trier par H_naturalness décroissant
    data_sorted = sorted(
        data,
        key=lambda x: x['signature_11d']['H_naturalness'],
        reverse=True,
    )

    return data_sorted[:top_n]


# =========================================================================
# TESTS
# =========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TEST VoiceSignatureExtractor — Extraction 11D")
    print("=" * 60)

    extractor = VoiceSignatureExtractor()

    # Test 1 : Signature par défaut (sans Parselmouth)
    sig = extractor._fallback_signature("test.wav")
    print(f"\nSignature par défaut (φ-neutre) :")
    for name, desc in DIMENSION_NAMES.items():
        val = getattr(sig, name)
        bar = "█" * int(val * 40)
        print(f"  {name:>18} ({desc:>35}): {val:.4f} {bar}")

    # Test 2 : Comparaison de profils
    print(f"\nComparaison des profils de référence :")
    profiles = list(REFERENCE_PROFILES.items())
    for i, (name1, sig1) in enumerate(profiles):
        for name2, sig2 in profiles[i + 1:]:
            dist = sig1.phi_distance_to(sig2)
            print(f"  {name1} ↔ {name2}: distance φ = {dist:.4f}")

    # Test 3 : Dominant style
    print(f"\nStyles dominants :")
    for name, sig in REFERENCE_PROFILES.items():
        print(f"  {name:>30}: {sig.dominant_style()}")

    # Test 4 : Parselmouth dispo ?
    try:
        import parselmouth
        print(f"\n[OK] Parselmouth disponible - extraction reelle possible")
        print(f"  Version: {parselmouth.__version__ if hasattr(parselmouth, '__version__') else 'installée'}")
    except ImportError:
        print(f"\nWARN Parselmouth non installe - signatures phi par defaut uniquement")
        print(f"  pip install parselmouth praat-parselmouth")

    print("\n" + "=" * 60)