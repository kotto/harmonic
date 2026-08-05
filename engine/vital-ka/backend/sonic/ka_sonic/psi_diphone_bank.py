"""
Harmonic Diphone Bank — Corpus de diphones en ψ via le codec harmonique.

Principe :
  1. Une voix humaine est enregistrée (30-60s de parole)
  2. Le codec HarmonicVoiceCodecV2 encode l'audio en trames ψ ∈ ℂ⁵¹²
  3. Les trames sont segmentées par énergie en « diphones »
  4. Chaque diphone = moyenne des ψ sur sa durée → signature ψ stockée
  5. Synthèse : texte → G2P → pour chaque diphone, retrieval du ψ le plus
     proche dans la banque → décodage → audio naturel

Avantage sur la synthèse formantique : les ψ contiennent la VRAIE structure
spectrale de la voix humaine — formants, transitions, coarticulation.
La qualité est celle de la synthèse par concaténation, mais stockée
en ψ (compressé, ~512 floats par diphone au lieu de milliers de samples).
"""

import os, sys, math, time, wave, io
import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

_ENGINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ENGINE_DIR)

from harmonic_voice_codec_v2 import HarmonicVoiceCodecV2

DEFAULT_SR = 24000  # sample rate natif du codec


# ═══════════════════════════════════════════════════════════════════════════════
# Banque de diphones en ψ
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PsiDiphone:
    """Un diphone stocké en ψ."""
    left: str          # phonème gauche
    right: str         # phonème droit
    psi: np.ndarray    # ψ ∈ ℂ⁵¹² (vecteur complexe)
    duration_s: float  # durée originale
    energy: float      # énergie RMS

    @property
    def n_samples_approx(self) -> int:
        return int(self.duration_s * DEFAULT_SR)


class PsiDiphoneBank:
    """Banque de diphones encodés en ψ via le codec harmonique.

    Usage :
        bank = PsiDiphoneBank()
        bank.build_from_wav("voix.wav")  # ou bank.build_from_audio(audio, sr)
        audio = bank.synthesize(["b", "o~", "j", "u", "r"])
    """

    def __init__(self):
        self.codec = HarmonicVoiceCodecV2(sample_rate=DEFAULT_SR, dim=512)
        self.diphones: Dict[str, List[PsiDiphone]] = {}  # "left-right" → liste de variantes
        self._built = False

    # ── Construction depuis un WAV ou un buffer ──────────────────────

    def build_from_wav(self, wav_path: str):
        """Construit la banque depuis un fichier WAV (voix humaine, 30-120s)."""
        with wave.open(wav_path, "rb") as wf:
            sr = wf.getframerate()
            n = wf.getnframes()
            pcm = np.frombuffer(wf.readframes(n), dtype="<i2")
        audio = pcm.astype(np.float64) / 32768.0
        if wf.getnchannels() > 1:
            audio = audio.reshape(-1, wf.getnchannels()).mean(axis=1)
        self.build_from_audio(audio.astype(np.float32), sr)

    def build_from_audio(self, audio: np.ndarray, sr: int, transcript: str = ""):
        """Construit la banque depuis un buffer audio float32.

        Si un transcript est fourni, il est utilisé pour étiqueter les segments.
        Sinon, les segments sont stockés sans étiquette et retrievés par similarité ψ.
        """
        print(f"🔬 Encodage en ψ: {len(audio)/sr:.1f}s d'audio...")
        t0 = time.perf_counter()

        # Resample si nécessaire
        if sr != DEFAULT_SR:
            audio = _resample(audio, sr, DEFAULT_SR)

        # Encoder tout l'audio en une fois
        psi_frames = self.codec.encode(audio, sr=DEFAULT_SR)
        n_frames = len(psi_frames)
        print(f"   → {n_frames} trames ψ ∈ ℂ⁵¹² ({ (time.perf_counter()-t0)*1000:.0f}ms)")

        # Segmenter par énergie
        segments = _segment_by_energy(psi_frames, self.codec, audio, DEFAULT_SR)
        print(f"   → {len(segments)} segments détectés")

        # Si on a un transcript, aligner avec les segments
        if transcript:
            from tts_engine import text_to_phonemes
            ref_phonemes = text_to_phonemes(transcript)
            # Alignement simple : distribuer les phonèmes sur les segments
            if ref_phonemes:
                self._build_labeled(psi_frames, segments, ref_phonemes)
                elapsed = (time.perf_counter() - t0) * 1000
                total = sum(len(v) for v in self.diphones.values())
                print(f"✅ Banque étiquetée: {total} diphones, {len(self.diphones)} types, {elapsed:.0f}ms")
                self._built = True
                return

        # Sans transcript : stocker par centroïde spectral (clustering grossier)
        for seg in segments:
            psi_mean = np.mean(psi_frames[seg["start"]:seg["end"]], axis=0)
            norm = np.sqrt(np.sum(np.abs(psi_mean) ** 2))
            if norm > 1e-10:
                psi_mean /= norm

            ph_type = _estimate_phoneme_type(seg["spectral_centroid"], seg["energy"])

            # Stocker SOUS le type estimé
            key = ph_type
            if key not in self.diphones:
                self.diphones[key] = []

            self.diphones[key].append(PsiDiphone(
                left=key, right=key,
                psi=psi_mean,
                duration_s=seg["duration"],
                energy=seg["energy"],
            ))

        self._built = True
        elapsed = (time.perf_counter() - t0) * 1000
        total_diphones = sum(len(v) for v in self.diphones.values())
        print(f"✅ Banque construite: {total_diphones} diphones, "
              f"{len(self.diphones)} types, {elapsed:.0f}ms")

    def _build_labeled(self, psi_frames, segments, ref_phonemes):
        """Étiqueter les segments avec les phonèmes du transcript (alignement simple)."""
        n_segs = len(segments)
        n_ph = len(ref_phonemes)
        if n_segs == 0 or n_ph == 0:
            return

        # Alignement proportionnel : mapper chaque phonème à un segment
        for i, ph in enumerate(ref_phonemes):
            if ph == "_":
                continue
            seg_idx = min(int(i * n_segs / n_ph), n_segs - 1)
            seg = segments[seg_idx]

            psi_mean = np.mean(psi_frames[seg["start"]:seg["end"]], axis=0)
            norm = np.sqrt(np.sum(np.abs(psi_mean) ** 2))
            if norm > 1e-10:
                psi_mean /= norm

            key = ph
            if key not in self.diphones:
                self.diphones[key] = []

            self.diphones[key].append(PsiDiphone(
                left=ph, right=ph,
                psi=psi_mean,
                duration_s=seg["duration"],
                energy=seg["energy"],
            ))

    # ── Synthèse par retrieval ψ ─────────────────────────────────────

    def synthesize(
        self,
        phonemes: List[str],
        f0_hz: float = 120.0,
        speed: float = 1.0,
    ) -> np.ndarray:
        """Synthétise une séquence de phonèmes en audio par interpolation ψ.

        Pour chaque phonème :
          1. Cherche le ψ le plus proche dans la banque
          2. Interpole entre ψ consécutifs pour des transitions douces
          3. Décode toute la séquence en une fois
        """
        if not self._built:
            raise RuntimeError("Banque non construite. Appeler build_from_wav() d'abord.")

        n = len(phonemes)
        if n < 1:
            return np.zeros(int(0.3 * DEFAULT_SR), dtype=np.float32)

        # Pour chaque phonème, trouver le meilleur ψ (ou fallback)
        psi_per_phoneme = []
        for ph in phonemes:
            if ph == "_":
                psi_per_phoneme.append(None)  # silence
                continue

            # Chercher le phonème exact
            if ph in self.diphones and self.diphones[ph]:
                # Prendre la variante médiane (évite les outliers)
                diph = self.diphones[ph][len(self.diphones[ph]) // 2]
                psi_per_phoneme.append(diph.psi)
            else:
                # Fallback : phonème le plus proche par similarité ψ
                psi_per_phoneme.append(self._find_closest_psi(ph))

        # Interpoler entre ψ consécutifs pour des transitions douces
        # Chaque phonème → 2 trames ψ (début + fin interpolés)
        psi_frames = []
        for i in range(n):
            psi_curr = psi_per_phoneme[i]
            psi_next = psi_per_phoneme[i + 1] if i + 1 < n else psi_curr

            if psi_curr is None:
                # Silence : ψ nul
                psi_frames.append(np.zeros(self.codec.dim, dtype=np.complex128))
                psi_frames.append(np.zeros(self.codec.dim, dtype=np.complex128))
            else:
                # Trame de début (interpolation 75% courant, 25% précédent)
                psi_prev = psi_per_phoneme[i - 1] if i > 0 else psi_curr
                if psi_prev is not None:
                    psi_start = psi_curr * 0.75 + psi_prev * 0.25
                else:
                    psi_start = psi_curr

                # Trame de fin (interpolation 75% courant, 25% suivant)
                if psi_next is not None:
                    psi_end = psi_curr * 0.75 + psi_next * 0.25
                else:
                    psi_end = psi_curr

                psi_frames.append(psi_start)
                psi_frames.append(psi_end)

        # Décoder toute la séquence
        if not psi_frames:
            return np.zeros(int(0.3 * DEFAULT_SR), dtype=np.float32)

        psi_array = np.array(psi_frames, dtype=np.complex128)

        # Estimer la longueur de sortie
        hop_samples = int(self.codec.overlap_ms / 1000 * DEFAULT_SR)
        n_target = len(psi_frames) * hop_samples + int(self.codec.frame_ms / 1000 * DEFAULT_SR)

        audio = self.codec.decode(psi_array, original_length=n_target)

        # Normaliser
        peak = np.max(np.abs(audio)) + 1e-10
        audio = (audio / peak * 0.95).astype(np.float32)

        return audio

    def stats(self) -> dict:
        return {
            "built": self._built,
            "n_types": len(self.diphones),
            "n_diphones": sum(len(v) for v in self.diphones.values()),
            "types": sorted(self.diphones.keys())[:30],
        }

    def _find_closest_psi(self, target_ph: str) -> np.ndarray:
        """Trouve le ψ le plus proche d'un phonème cible (fallback)."""
        # Chercher parmi tous les diphones connus
        best_psi = None
        best_sim = -1.0

        for ph, variants in self.diphones.items():
            if not variants:
                continue
            # Similarité grossière : similarité des features phonétiques
            sim = _phoneme_similarity_heuristic(target_ph, ph)
            if sim > best_sim:
                best_sim = sim
                best_psi = variants[len(variants) // 2].psi

        if best_psi is not None:
            return best_psi
        # Fallback ultime
        return np.zeros(self.codec.dim, dtype=np.complex128)


def _phoneme_similarity_heuristic(ph1: str, ph2: str) -> float:
    """Similarité heuristique entre deux phonèmes (basée sur la classe phonétique)."""
    VOWELS = {'a', 'e', 'i', 'o', 'u', 'y', 'eu', 'oe'}
    NASALS = {'a~', 'e~', 'o~', 'oe~', 'm', 'n', 'gn'}
    FRICATIVES = {'f', 'v', 's', 'z', 'ch', 'j', 'ss'}
    STOPS = {'p', 'b', 't', 'd', 'k', 'g'}
    LIQUIDS = {'l', 'r'}

    def class_of(ph):
        if ph in VOWELS: return 'vowel'
        if ph in NASALS: return 'nasal'
        if ph in FRICATIVES: return 'fricative'
        if ph in STOPS: return 'stop'
        if ph in LIQUIDS: return 'liquid'
        return 'other'

    if ph1 == ph2:
        return 1.0
    if class_of(ph1) == class_of(ph2):
        return 0.5
    return 0.1

    def stats(self) -> dict:
        return {
            "built": self._built,
            "n_types": len(self.diphones),
            "n_diphones": sum(len(v) for v in self.diphones.values()),
            "types": sorted(self.diphones.keys())[:20],
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Utilitaires : segmentation, estimation phonème
# ═══════════════════════════════════════════════════════════════════════════════

def _resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """Resampling linéaire."""
    if orig_sr == target_sr:
        return audio
    n_out = int(len(audio) * target_sr / orig_sr)
    idx = np.linspace(0, len(audio) - 1, n_out)
    return np.interp(idx, np.arange(len(audio)), audio).astype(np.float32)


def _segment_by_energy(
    psi_frames: np.ndarray,
    codec: HarmonicVoiceCodecV2,
    audio: np.ndarray,
    sr: int,
) -> List[dict]:
    """Segmente l'audio en « diphones » basés sur les creux d'énergie.

    Retourne une liste de dicts {start, end, duration, energy, spectral_centroid}.
    """
    n_frames = len(psi_frames)
    if n_frames < 3:
        return []

    # Calculer l'énergie par trame
    frame_len = int(codec.frame_ms / 1000 * sr)
    hop_len = int(codec.overlap_ms / 1000 * sr)

    energies = []
    centroids = []
    for i in range(n_frames):
        start = i * hop_len
        end = min(start + frame_len, len(audio))
        if end <= start:
            energies.append(0.0)
            centroids.append(1000.0)
            continue
        chunk = audio[start:end]
        rms = np.sqrt(np.mean(chunk ** 2))
        energies.append(rms)

        # Centroïde spectral
        if len(chunk) > 64:
            spec = np.abs(np.fft.rfft(chunk * np.hanning(len(chunk))))
            freqs = np.fft.rfftfreq(len(chunk), 1.0 / sr)
            cent = np.sum(freqs * spec) / (np.sum(spec) + 1e-10)
        else:
            cent = 1500.0
        centroids.append(float(cent))

    energies = np.array(energies)
    if len(energies) < 2:
        return []

    # Seuil d'énergie : médiane - 0.1 * écart-type
    threshold = np.median(energies) - 0.1 * np.std(energies)
    if threshold < 0.001:
        threshold = np.median(energies) * 0.3

    # Trouver les frontières (creux d'énergie)
    boundaries = [0]
    for i in range(1, n_frames - 1):
        if energies[i] < threshold and energies[i] < energies[i - 1] and energies[i] < energies[i + 1]:
            boundaries.append(i)

    if boundaries[-1] != n_frames - 1:
        boundaries.append(n_frames - 1)

    # Fusionner les segments trop courts (< 3 trames)
    boundaries = sorted(set(boundaries))
    merged = [boundaries[0]]
    for b in boundaries[1:]:
        if b - merged[-1] < 3:
            continue  # fusionner
        merged.append(b)
    if merged[-1] != n_frames - 1:
        merged.append(n_frames - 1)

    # Construire les segments
    segments = []
    for i in range(len(merged) - 1):
        start = merged[i]
        end = merged[i + 1]
        if end <= start:
            continue
        seg_energy = float(np.mean(energies[start:end]))
        seg_centroid = float(np.mean(centroids[start:end]))
        seg_duration = (end - start) * codec.overlap_ms / 1000.0

        segments.append({
            "start": start,
            "end": end,
            "duration": seg_duration,
            "energy": seg_energy,
            "spectral_centroid": seg_centroid,
        })

    return segments


def _estimate_phoneme_type(centroid: float, energy: float) -> str:
    """Estimation grossière du type de phonème basée sur le centroïde spectral.

    Retourne un symbole parmi : a, i, u, s, ch, m, l, _
    """
    if energy < 0.005:
        return "_"
    if centroid < 600:
        return "u"
    elif centroid < 900:
        return "o"
    elif centroid < 1200:
        return "a"
    elif centroid < 1800:
        return "e"
    elif centroid < 2400:
        return "i"
    elif centroid < 3500:
        return "s"
    else:
        return "ch"
