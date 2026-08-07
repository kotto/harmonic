"""
Harmonic Diphone Bank v2 — Corpus de diphones audio réels.

Approche corrigée : au lieu de stocker des ψ isolés (qui perdent la
continuité de phase au décodage), on stocke les SEGMENTS AUDIO BRUTS
extraits de l'enregistrement original.

Pipeline :
  1. Enregistrer 30-60s de parole couvrant les phonèmes français
  2. Segmenter par énergie → segments audio étiquetés (via transcript)
  3. Stocker les segments PCM par type de phonème
  4. Synthèse : G2P → pour chaque phonème, piocher un segment audio
     du même type → concaténer avec crossfade → WAV

C'est de la synthèse par concaténation classique, mais avec une banque
construite automatiquement depuis UN SEUL enregistrement.
"""

import os, sys, math, time, wave, io
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DEFAULT_SR = 22050


@dataclass
class AudioSegment:
    """Un segment audio étiqueté."""
    phoneme: str
    audio: np.ndarray   # float32 [-1, 1]
    sample_rate: int
    duration_s: float

    @property
    def n_samples(self) -> int:
        return len(self.audio)


class AudioDiphoneBank:
    """Banque de segments audio réels par type de phonème.

    Usage :
        bank = AudioDiphoneBank()
        bank.build_from_wav("voix.wav", transcript="...")
        audio = bank.synthesize(["b", "o~", "j", "u", "r"])
    """

    def __init__(self):
        self.segments: Dict[str, List[AudioSegment]] = {}
        self._built = False

    def build_from_wav(self, wav_path: str, transcript: str = ""):
        """Construit la banque depuis un WAV + transcript."""
        with wave.open(wav_path, "rb") as wf:
            sr = wf.getframerate()
            n = wf.getnframes()
            pcm = np.frombuffer(wf.readframes(n), dtype="<i2>")
        audio = pcm.astype(np.float64) / 32768.0
        if wf.getnchannels() > 1:
            audio = audio.reshape(-1, wf.getnchannels()).mean(axis=1)
        self.build_from_audio(audio.astype(np.float32), sr, transcript)

    def build_from_audio(self, audio: np.ndarray, sr: int, transcript: str = ""):
        """Segmente l'audio par énergie et étiquette via le transcript."""
        # Resample
        if sr != DEFAULT_SR:
            audio = _resample(audio, sr, DEFAULT_SR)
            sr = DEFAULT_SR

        print(f"🔬 Segmentation: {len(audio)/sr:.1f}s d'audio...")
        t0 = time.perf_counter()

        # Segmenter par creux d'énergie
        boundaries = _find_energy_boundaries(audio, sr)
        print(f"   → {len(boundaries)-1} segments")

        # Éti queter
        if transcript:
            from tts_engine import text_to_phonemes
            phonemes = text_to_phonemes(transcript)
            phonemes = [p for p in phonemes if p != "_"]  # enlever les pauses
            print(f"   → {len(phonemes)} phonèmes dans le transcript")
            self._label_segments(audio, sr, boundaries, phonemes)
        else:
            self._label_by_clustering(audio, sr, boundaries)

        self._built = True
        total = sum(len(v) for v in self.segments.values())
        elapsed = (time.perf_counter() - t0) * 1000
        print(f"✅ Banque: {total} segments, {len(self.segments)} types, {elapsed:.0f}ms")

    def _label_segments(self, audio, sr, boundaries, phonemes):
        """Associe chaque segment à un phonème du transcript."""
        n_segs = len(boundaries) - 1
        n_ph = len(phonemes)
        if n_segs == 0 or n_ph == 0:
            return

        for i in range(n_segs):
            start = boundaries[i]
            end = boundaries[i + 1]
            if end <= start:
                continue

            # Assigner le phonème le plus proche (alignement proportionnel)
            ph_idx = min(int(i * n_ph / n_segs), n_ph - 1)
            ph = phonemes[ph_idx]

            seg_audio = audio[start:end].copy()
            dur = len(seg_audio) / sr

            if ph not in self.segments:
                self.segments[ph] = []

            self.segments[ph].append(AudioSegment(
                phoneme=ph, audio=seg_audio,
                sample_rate=sr, duration_s=dur,
            ))

    def _label_by_clustering(self, audio, sr, boundaries):
        """Sans transcript : clustering spectral grossier."""
        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]
            if end <= start:
                continue
            seg_audio = audio[start:end]
            # Centroïde spectral pour classifier
            cent = _spectral_centroid(seg_audio, sr)
            ph = _classify_phoneme(cent)
            if ph not in self.segments:
                self.segments[ph] = []
            self.segments[ph].append(AudioSegment(
                phoneme=ph, audio=seg_audio.copy(),
                sample_rate=sr, duration_s=len(seg_audio)/sr,
            ))

    def synthesize(
        self,
        phonemes: List[str],
        speed: float = 1.0,
    ) -> np.ndarray:
        """Synthèse par concaténation de segments audio réels."""
        if not self._built:
            raise RuntimeError("Banque non construite.")

        fragments = []
        for ph in phonemes:
            if ph == "_":
                fragments.append(np.zeros(int(0.06 * DEFAULT_SR), dtype=np.float32))
                continue

            # Chercher le phonème exact, sinon le plus proche
            segs = self.segments.get(ph)
            if not segs:
                segs = self._find_closest_segments(ph)
            if not segs:
                fragments.append(np.zeros(int(0.08 * DEFAULT_SR), dtype=np.float32))
                continue

            # Prendre un segment aléatoire (déterministe via hash du phonème)
            idx = abs(hash(ph)) % len(segs)
            seg = segs[idx]
            audio = seg.audio.copy()

            # Ajuster la vitesse
            if speed != 1.0:
                audio = _time_stretch(audio, speed)

            fragments.append(audio)

        if not fragments:
            return np.zeros(int(0.3 * DEFAULT_SR), dtype=np.float32)

        # Concaténation avec crossfade
        return _concatenate(fragments, DEFAULT_SR)

    def _find_closest_segments(self, target_ph: str) -> List[AudioSegment]:
        """Trouve les segments du type le plus proche (fallback)."""
        from ka_sonic.psi_diphone_bank import _phoneme_similarity_heuristic
        best_key = None
        best_sim = -1.0
        for key in self.segments:
            sim = _phoneme_similarity_heuristic(target_ph, key)
            if sim > best_sim:
                best_sim = sim
                best_key = key
        return self.segments.get(best_key, [])

    def stats(self) -> dict:
        return {
            "built": self._built,
            "n_types": len(self.segments),
            "n_segments": sum(len(v) for v in self.segments.values()),
            "types": sorted(self.segments.keys()),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Segmentation audio
# ═══════════════════════════════════════════════════════════════════════════════

def _find_energy_boundaries(audio: np.ndarray, sr: int) -> List[int]:
    """Trouve les frontières de segments basées sur les creux d'énergie."""
    frame_len = int(0.025 * sr)
    hop_len = frame_len // 2
    n_frames = max(1, (len(audio) - frame_len) // hop_len + 1)

    energies = np.zeros(n_frames)
    for i in range(n_frames):
        start = i * hop_len
        chunk = audio[start:start + frame_len]
        energies[i] = np.sqrt(np.mean(chunk ** 2))

    if len(energies) < 2:
        return [0, len(audio)]

    # Lissage
    energies = np.convolve(energies, np.ones(3)/3, mode='same')

    # Seuil : médiane - 0.5 * MAD
    med = np.median(energies)
    mad = np.median(np.abs(energies - med))
    threshold = med - 0.5 * mad
    if threshold < 1e-4:
        threshold = med * 0.15

    # Trouver les minima locaux sous le seuil
    boundaries = [0]
    for i in range(2, n_frames - 2):
        if (energies[i] < threshold and
            energies[i] < energies[i-1] and
            energies[i] < energies[i+1]):
            sample_pos = i * hop_len + frame_len // 2
            if sample_pos - boundaries[-1] > int(0.03 * sr):  # min 30ms
                boundaries.append(sample_pos)

    if boundaries[-1] < len(audio) - int(0.05 * sr):
        boundaries.append(len(audio))

    return boundaries


def _concatenate(fragments: List[np.ndarray], sr: int) -> np.ndarray:
    """Concatène avec crossfade Hanning."""
    if len(fragments) == 1:
        return fragments[0]

    ov = max(4, int(0.010 * sr))
    total_len = sum(len(f) for f in fragments) - ov * (len(fragments) - 1)
    out = np.zeros(total_len, dtype=np.float64)
    norm = np.zeros(total_len, dtype=np.float64)
    pos = 0

    for f in fragments:
        L = len(f)
        win = np.hanning(L).astype(np.float64)
        out[pos:pos + L] += f.astype(np.float64) * win
        norm[pos:pos + L] += win
        pos += L - ov

    norm[norm < 1e-6] = 1.0
    result = out / norm
    peak = np.max(np.abs(result)) + 1e-10
    return (result / peak * 0.95).astype(np.float32)


def _resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    if orig_sr == target_sr:
        return audio
    n_out = int(len(audio) * target_sr / orig_sr)
    idx = np.linspace(0, len(audio) - 1, n_out)
    return np.interp(idx, np.arange(len(audio)), audio).astype(np.float32)


def _time_stretch(audio: np.ndarray, factor: float) -> np.ndarray:
    n_out = int(len(audio) / max(factor, 0.25))
    idx = np.linspace(0, len(audio) - 1, max(1, n_out))
    return np.interp(idx, np.arange(len(audio)), audio).astype(np.float32)


def _spectral_centroid(audio: np.ndarray, sr: int) -> float:
    n = len(audio)
    if n < 64:
        return 1000.0
    spec = np.abs(np.fft.rfft(audio * np.hanning(n)))
    freqs = np.fft.rfftfreq(n, 1.0 / sr)
    return float(np.sum(freqs * spec) / (np.sum(spec) + 1e-10))


def _classify_phoneme(centroid: float) -> str:
    if centroid < 500:   return "u"
    if centroid < 800:   return "o"
    if centroid < 1200:  return "a"
    if centroid < 1800:  return "e"
    if centroid < 2500:  return "i"
    if centroid < 3500:  return "s"
    return "ch"
