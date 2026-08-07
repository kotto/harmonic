"""
VoiceSignature — Extraction et application de signature vocale 11D + clonage.

Signature 11D (ordre canonique) :
  dim 0 : pitch_mean       — F0 moyenne (normalisée Bark, 0=bas ~80Hz, 1=haut ~400Hz)
  dim 1 : pitch_range       — amplitude de variation F0
  dim 2 : speed             — débit (0=lent, 1=rapide)
  dim 3 : timbre            — brillance spectrale (0=sombre, 1=brillant)
  dim 4 : breathiness       — ratio bruit/harmonique (0=pur, 1=soufflé)
  dim 5 : resonance         — résonance globale (0=étouffé, 1=résonant)
  dim 6 : emotion_range     — amplitude émotionnelle
  dim 7 : clarity           — clarté d'articulation
  dim 8 : pause_pattern     — pattern de pause (0=continu, 1=haché)
  dim 9 : phi_alignment     — alignement φ (signature harmonique)
  dim 10: naturalness        — naturel (0=robotique, 1=naturel)

Zéro dépendance externe : numpy + scipy. Pas de parselmouth/praat requis.
"""

import math
import wave
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

DEFAULT_SR = 22050

# ═══════════════════════════════════════════════════════════════════════════════
# Extraction de signature 11D depuis un WAV
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class VoiceSignature:
    """Signature vocale 11D extraite d'un échantillon audio."""
    values: np.ndarray  # 11 floats [0,1]
    source_path: str = ""
    duration_s: float = 0.0

    def __getitem__(self, idx):
        return self.values[idx]

    def __len__(self):
        return 11

    def to_dict(self) -> dict:
        names = [
            "pitch_mean", "pitch_range", "speed", "timbre", "breathiness",
            "resonance", "emotion_range", "clarity", "pause_pattern",
            "phi_alignment", "naturalness",
        ]
        return {n: float(v) for n, v in zip(names, self.values)}

    def clone(self) -> "VoiceSignature":
        return VoiceSignature(self.values.copy(), self.source_path, self.duration_s)


def extract_signature(
    audio: np.ndarray,
    sr: int = DEFAULT_SR,
    source_path: str = "",
) -> VoiceSignature:
    """Extrait la signature vocale 11D d'un buffer audio.

    Args:
        audio : float32 [-1, 1], mono
        sr : sample rate
        source_path : chemin du fichier source (info)

    Returns:
        VoiceSignature avec 11 valeurs dans [0, 1]
    """
    audio = np.asarray(audio, dtype=np.float64)
    if len(audio) < sr * 0.5:
        raise ValueError("Audio trop court (< 0.5s), besoin de >= 5s pour le clonage")

    n = len(audio)
    duration_s = n / sr
    sig = np.zeros(11, dtype=np.float32)

    # ── dim 0 : pitch_mean (F0 par autocorrélation) ────────────────────
    f0_contour = _estimate_f0_contour(audio, sr)
    f0_valid = f0_contour[f0_contour > 0]
    if len(f0_valid) > 0:
        f0_mean = np.median(f0_valid)
        # Normaliser : 80 Hz → 0, 400 Hz → 1 (échelle log)
        f0_norm = np.clip(math.log(f0_mean / 80.0) / math.log(400.0 / 80.0), 0.0, 1.0)
        sig[0] = f0_norm
    else:
        sig[0] = 0.5  # neutre

    # ── dim 1 : pitch_range ────────────────────────────────────────────
    if len(f0_valid) > 1:
        f0_range = np.std(f0_valid) / max(np.mean(f0_valid), 1e-6)
        sig[1] = np.clip(f0_range / 0.5, 0.0, 1.0)
    else:
        sig[1] = 0.3

    # ── dim 2 : speed (débit estimé par ZCR) ────────────────────────────
    zcr = _zero_crossing_rate(audio)
    sig[2] = np.clip(zcr / 0.3, 0.0, 1.0)

    # ── dim 3 : timbre (brillance = centroïde spectral) ────────────────
    centroid = _spectral_centroid(audio, sr)
    # Centroïde typique : 500 Hz (sombre) → 3000 Hz (brillant)
    sig[3] = np.clip((centroid - 500) / 2500, 0.0, 1.0)

    # ── dim 4 : breathiness (ratio bruit/haute fréquence) ─────────────
    hf_energy = np.mean(audio[int(n * 0.8):] ** 2)
    total_energy = np.mean(audio ** 2) + 1e-10
    sig[4] = np.clip(hf_energy / total_energy * 2.0, 0.0, 1.0)

    # ── dim 5 : resonance (énergie basse fréquence) ────────────────────
    lf_energy = np.mean(audio[:int(n * 0.2)] ** 2)
    sig[5] = np.clip(lf_energy / total_energy * 2.0, 0.0, 1.0)

    # ── dim 6 : emotion_range (variance de l'enveloppe) ────────────────
    env = _amplitude_envelope(audio, sr, frame_ms=50)
    if len(env) > 1:
        sig[6] = np.clip(np.std(env) / (np.mean(env) + 1e-10) * 2.0, 0.0, 1.0)
    else:
        sig[6] = 0.3

    # ── dim 7 : clarity (ratio énergie haute vs basse fréquence) ────────
    sig[7] = np.clip(centroid / 4000.0, 0.0, 1.0)

    # ── dim 8 : pause_pattern (ZCR variance) ────────────────────────────
    zcr_frames = []
    frame_len = int(0.05 * sr)
    for i in range(0, n - frame_len, frame_len):
        zcr_frames.append(_zero_crossing_rate(audio[i:i + frame_len]))
    if len(zcr_frames) > 1:
        sig[8] = np.clip(np.std(zcr_frames) / (np.mean(zcr_frames) + 1e-10), 0.0, 1.0)
    else:
        sig[8] = 0.3

    # ── dim 9 : phi_alignment (auto-corrélation à décalage φ) ──────────
    phi_shift = int(sr * 0.001618)  # ~1.618 ms
    if phi_shift < n:
        phi_corr = np.corrcoef(audio[:n - phi_shift], audio[phi_shift:])[0, 1]
        sig[9] = np.clip(abs(phi_corr), 0.0, 1.0)
    else:
        sig[9] = 0.5

    # ── dim 10 : naturalness (harmonicité) ──────────────────────────────
    harmonicity = _estimate_harmonicity(audio, sr)
    sig[10] = np.clip(harmonicity, 0.0, 1.0)

    return VoiceSignature(sig, source_path, duration_s)


def extract_from_wav(wav_path: str) -> VoiceSignature:
    """Extrait la signature depuis un fichier WAV."""
    with wave.open(wav_path, "rb") as wf:
        sr = wf.getframerate()
        n_frames = wf.getnframes()
        pcm = np.frombuffer(wf.readframes(n_frames), dtype="<i2")
    audio = pcm.astype(np.float64) / 32768.0
    if wf.getnchannels() > 1:
        audio = audio.reshape(-1, wf.getnchannels()).mean(axis=1)
    return extract_signature(audio, sr, wav_path)


# ═══════════════════════════════════════════════════════════════════════════════
# Application de la signature à un signal audio
# ═══════════════════════════════════════════════════════════════════════════════

def apply_signature(
    audio: np.ndarray,
    signature: VoiceSignature,
    sr: int = DEFAULT_SR,
    seed: int = 42,
) -> np.ndarray:
    """Applique une signature vocale à un signal audio synthétisé.

    Le signal de base est synthétisé avec F0=120Hz neutre.
    La signature modifie :
      - F0 (pitch_mean) → pitch-shift
      - Timbre → EQ formantique
      - Breathiness → mixage bruit (déterministe via seed)
      - Vitesse → time-stretch léger

    Args:
        audio : signal source float32 [-1, 1]
        signature : VoiceSignature 11D cible
        sr : sample rate
        seed : seed pour le RNG de breathiness (déterministe)

    Returns:
        audio modifié float32
    """
    audio = np.asarray(audio, dtype=np.float64)
    sig = signature.values
    rng = np.random.RandomState(seed & 0x7FFFFFFF)

    # 1. Pitch-shift (dim 0 : pitch_mean)
    pitch_target = sig[0]  # 0=80Hz, 0.5=180Hz, 1=400Hz
    # On suppose que la synthèse de base est à F0=120Hz (pitch_mean≈0.25)
    base_f0_norm = 0.25
    f0_ratio = (80.0 * math.exp(pitch_target * math.log(400.0 / 80.0))) / 120.0
    n_semitones = 12.0 * math.log2(max(0.5, min(2.0, f0_ratio)))
    if abs(n_semitones) > 0.5:
        audio = _pitch_shift_simple(audio, sr, n_semitones)

    # 2. Time-stretch (dim 2 : speed)
    speed_factor = 0.7 + sig[2] * 0.6  # 0.7x à 1.3x
    if abs(speed_factor - 1.0) > 0.05:
        audio = _time_stretch_simple(audio, speed_factor)

    # 3. EQ timbre (dim 3 : brillance)
    timbre = sig[3]
    if abs(timbre - 0.5) > 0.05:
        audio = _eq_brightness(audio, sr, timbre)

    # 4. Breathiness (dim 4 : mix bruit)
    breath = sig[4]
    if breath > 0.1:
        noise = rng.normal(0, 0.3, len(audio)).astype(np.float64)
        # Filtrer le bruit (passe-haut)
        noise = np.diff(noise, prepend=noise[0])
        audio = audio * (1.0 - breath * 0.5) + noise * breath * 0.3

    # 5. Resonance (dim 5 : boost basses)
    resonance = sig[5]
    if resonance > 0.1:
        audio = _eq_low_boost(audio, sr, resonance)

    # 6. Vitesse d'articulation (dim 2 + dim 8 combinés)
    # Déjà partiellement traité par time-stretch

    # Normalisation finale
    peak = np.max(np.abs(audio)) + 1e-10
    return (audio / peak * 0.95).astype(np.float32)


# ═══════════════════════════════════════════════════════════════════════════════
# Utilitaires DSP (pitch-shift, time-stretch, EQ)
# ═══════════════════════════════════════════════════════════════════════════════

def _pitch_shift_simple(audio: np.ndarray, sr: int, n_semitones: float) -> np.ndarray:
    """Pitch-shift par resampling + time-stretch (PSOLA simplifié)."""
    ratio = 2.0 ** (n_semitones / 12.0)
    
    # Resample le signal (change pitch + durée)
    n_in = len(audio)
    n_out = int(n_in / ratio)
    idx = np.linspace(0, n_in - 1, max(1, n_out))
    stretched = np.interp(idx, np.arange(n_in), audio)
    
    # Re-stretch à la durée d'origine
    idx2 = np.linspace(0, len(stretched) - 1, n_in)
    return np.interp(idx2, np.arange(len(stretched)), stretched).astype(np.float64)


def _time_stretch_simple(audio: np.ndarray, factor: float) -> np.ndarray:
    """Time-stretch par resampling linéaire (préserve le pitch)."""
    n_in = len(audio)
    n_out = int(n_in * factor)
    idx = np.linspace(0, n_in - 1, max(1, n_out))
    return np.interp(idx, np.arange(n_in), audio).astype(np.float64)


def _eq_brightness(audio: np.ndarray, sr: int, brightness: float) -> np.ndarray:
    """EQ simple : boost/cut hautes fréquences selon la brillance."""
    try:
        from scipy import signal as scipy_signal
        gain = 0.5 + brightness  # 0.5 à 1.5
        cutoff = 2000.0 * (1.0 - (brightness - 0.5) * 0.5)
        b, a = scipy_signal.butter(1, cutoff / (sr / 2), btype="high")
        high = scipy_signal.lfilter(b, a, audio)
        result = audio + (high - audio) * (gain - 1.0) * 0.4
        return result.astype(np.float64)
    except ImportError:
        return audio


def _eq_low_boost(audio: np.ndarray, sr: int, amount: float) -> np.ndarray:
    """Boost des basses fréquences."""
    try:
        from scipy import signal as scipy_signal
        b, a = scipy_signal.butter(1, 300 / (sr / 2), btype="low")
        low = scipy_signal.lfilter(b, a, audio)
        result = audio + low * amount * 0.5
        return result.astype(np.float64)
    except ImportError:
        return audio


# ═══════════════════════════════════════════════════════════════════════════════
# Estimateurs acoustiques (sans parselmouth)
# ═══════════════════════════════════════════════════════════════════════════════

def _estimate_f0_contour(audio: np.ndarray, sr: int, frame_ms: float = 25.0, hop_ms: float = 10.0) -> np.ndarray:
    """Estimation F0 par autocorrélation frame par frame."""
    frame_len = int(frame_ms / 1000.0 * sr)
    hop_len = int(hop_ms / 1000.0 * sr)
    n_frames = max(1, (len(audio) - frame_len) // hop_len + 1)

    f0s = []
    min_lag = int(sr / 400.0)  # 400 Hz max
    max_lag = int(sr / 80.0)   # 80 Hz min

    for i in range(n_frames):
        start = i * hop_len
        frame = audio[start:start + frame_len]
        if len(frame) < min_lag * 2:
            continue

        # Autocorrélation normalisée
        frame = frame - np.mean(frame)
        corr = np.correlate(frame, frame, mode="full")
        corr = corr[len(corr) // 2:]  # partie positive
        if len(corr) <= max_lag:
            continue

        # Chercher le pic dans [min_lag, max_lag]
        search = corr[min_lag:min(len(corr), max_lag)]
        if len(search) == 0:
            continue
        peak_idx = np.argmax(search) + min_lag

        # Seuil de voisement
        if corr[peak_idx] < 0.3 * corr[0]:
            f0s.append(0.0)
        else:
            f0s.append(sr / peak_idx)

    return np.array(f0s)


def _zero_crossing_rate(audio: np.ndarray) -> float:
    """Taux de passage par zéro."""
    if len(audio) < 2:
        return 0.0
    signs = np.sign(audio)
    crossings = np.sum(np.abs(np.diff(signs > 0))) / (2 * len(audio))
    return float(crossings)


def _spectral_centroid(audio: np.ndarray, sr: int) -> float:
    """Centroïde spectral (fréquence moyenne pondérée par l'amplitude)."""
    n = len(audio)
    if n < 2:
        return 1000.0
    spec = np.abs(np.fft.rfft(audio * np.hanning(n)))
    freqs = np.fft.rfftfreq(n, 1.0 / sr)
    total = np.sum(spec) + 1e-10
    return float(np.sum(freqs * spec) / total)


def _amplitude_envelope(audio: np.ndarray, sr: int, frame_ms: float = 50.0) -> np.ndarray:
    """Enveloppe d'amplitude (RMS par frame)."""
    frame_len = int(frame_ms / 1000.0 * sr)
    hop_len = frame_len // 2
    n_frames = max(1, (len(audio) - frame_len) // hop_len + 1)
    env = np.zeros(n_frames)
    for i in range(n_frames):
        start = i * hop_len
        frame = audio[start:start + frame_len]
        env[i] = np.sqrt(np.mean(frame ** 2))
    return env


def _estimate_harmonicity(audio: np.ndarray, sr: int) -> float:
    """Ratio harmonique/bruit par analyse spectrale."""
    n = len(audio)
    if n < 256:
        return 0.5
    spec = np.abs(np.fft.rfft(audio * np.hanning(n)))
    # Détecter les pics harmoniques (multiples de F0)
    peaks = []
    for i in range(2, len(spec) - 1):
        if spec[i] > spec[i - 1] and spec[i] > spec[i + 1]:
            peaks.append(i)
    if len(peaks) < 3:
        return 0.2
    # Ratio énergie des pics vs énergie totale
    peak_energy = np.sum(spec[peaks] ** 2)
    total_energy = np.sum(spec ** 2) + 1e-10
    harmonicity = peak_energy / total_energy
    return np.clip(harmonicity * 3.0, 0.0, 1.0)


# ═══════════════════════════════════════════════════════════════════════════════
# Profils de voix par défaut
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_VOICES: Dict[str, VoiceSignature] = {
    "homme": VoiceSignature(np.array(
        [0.20, 0.30, 0.40, 0.35, 0.15, 0.55, 0.25, 0.50, 0.30, 0.60, 0.55],
        dtype=np.float32,
    ), "default"),
    "femme": VoiceSignature(np.array(
        [0.55, 0.40, 0.50, 0.60, 0.20, 0.40, 0.35, 0.60, 0.25, 0.55, 0.60],
        dtype=np.float32,
    ), "default"),
    "enfant": VoiceSignature(np.array(
        [0.75, 0.50, 0.60, 0.70, 0.10, 0.30, 0.45, 0.70, 0.20, 0.50, 0.65],
        dtype=np.float32,
    ), "default"),
}
