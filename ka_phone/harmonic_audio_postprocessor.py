#!/usr/bin/env python3
"""
HARMONIC AUDIO POST-PROCESSOR — Amélioration harmonique de l'audio
=====================================================================
Post-traitement audio par ondes — enrichit n'importe quel fichier WAV
(Piper, XTTS, ou fallback sinusoïdal) avec :

  1. ACCENTUATION φ-HARMONIQUE : boost des fréquences multiples de φ
     → FFT → sélection des pics aux fréquences f₀×φ, f₀×φ², f₀×φ³ → IFFT
  2. LISSAGE TEMPOREL ABC : enveloppe Mittag-Leffler pour transitions douces
  3. RÉDUCTION DE BRUIT SPECTRALE : soustraction spectrale simple

Usage :
  from harmonic_audio_postprocessor import HarmonicAudioPostProcessor
  hpp = HarmonicAudioPostProcessor()
  hpp.process("input.wav", "output.wav", pitch_shift=0.0)

Intégration dans SpeechOrchestrator :
  audio_path = hso.speak("Bonjour")["audio_path"]
  hpp.process(audio_path, audio_path)  # In-place enhancement
"""

import os, sys, math, wave, struct, time
from typing import Dict, Any, Optional
import numpy as np

PHI = 1.618033988749895
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "speech")
os.makedirs(DATA_DIR, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════
# MITTAG-LEFFLER (pour lissage ABC)
# ══════════════════════════════════════════════════════════════════════════

def mittag_leffler(alpha: float, z: float, terms: int = 40) -> float:
    """E_α(z) = Σ z^k / Γ(αk + 1)"""
    if z == 0:
        return 1.0
    result = 0.0
    for k in range(terms):
        try:
            term = z**k / math.gamma(alpha * k + 1)
            result += term
            if abs(term) < 1e-12:
                break
        except OverflowError:
            break
    return result


def abc_envelope(length: int, alpha: float = 0.7) -> np.ndarray:
    """
    Enveloppe temporelle basée sur le noyau ABC pour lisser
    les transitions audio (attaque et déclin).
    """
    t = np.linspace(0, 10, length)
    z = -alpha * t**alpha / (1.0 - alpha)
    env = np.array([mittag_leffler(alpha, zi) for zi in z])
    env = env / (env.max() + 1e-10)
    return env


class HarmonicAudioPostProcessor:
    """
    Post-processeur audio harmonique.
    Améliore la qualité sonore sans modifier le contenu parlé.
    """

    def __init__(self):
        self.stats = {"total_processed": 0, "avg_gain_db": 0.0}

    def process_bytes(self, audio: np.ndarray, sample_rate: int,
                      pitch_shift: float = 0.0,
                      boost_strength: float = 0.12,
                      noise_reduction: bool = True,
                      abc_smoothing: bool = True) -> np.ndarray:
        """
        Post-traite un tableau numpy audio en mémoire.
        Retourne le tableau traité.
        """
        original_rms = np.sqrt(np.mean(audio**2)) if len(audio) > 0 else 0.01

        # ÉTAPE 1 : Accentuation φ-harmonique
        if boost_strength > 0 and sample_rate > 100:
            audio = self._phi_harmonic_boost(audio, sample_rate, boost_strength)

        # ÉTAPE 2 : Lissage temporel ABC
        if abc_smoothing and len(audio) > 100:
            audio = self._abc_temporal_smoothing(audio)

        # ÉTAPE 3 : Pitch shift
        if abs(pitch_shift) > 0.001:
            audio = self._pitch_shift_simple(audio, sample_rate, pitch_shift)

        # ÉTAPE 4 : Réduction de bruit spectrale
        if noise_reduction:
            audio = self._spectral_noise_reduction(audio, sample_rate)

        # ÉTAPE 5 : Normalisation + clipping doux
        # Protection anti-overflow : clip après chaque étape pour éviter
        # que les données FFT/IRFFT produisent des valeurs hors float32.
        audio = np.clip(audio, -100.0, 100.0)  # garde-fou pré-RMS
        final_rms = float(np.sqrt(np.mean(audio.astype(np.float64)**2))) if len(audio) > 0 else 0.0
        if final_rms > 0:
            target_rms = max(float(original_rms) * 0.9, 0.05)
            audio = audio.astype(np.float64) * (target_rms / final_rms)
            audio = audio.astype(np.float32)
        audio = np.tanh(audio.astype(np.float64) * 1.5) / 1.5
        audio = np.clip(audio, -0.99, 0.99)
        audio = audio.astype(np.float32)

        self.stats["total_processed"] += 1
        return audio

    def process(self, input_path: str, output_path: str,
                pitch_shift: float = 0.0,
                boost_strength: float = 0.15,
                noise_reduction: bool = True,
                abc_smoothing: bool = True) -> Dict:
        """
        Post-traite un fichier WAV.

        Args:
            input_path: chemin du WAV d'entrée
            output_path: chemin du WAV de sortie
            pitch_shift: décalage de hauteur (-1.0 = grave, +1.0 = aigu)
            boost_strength: force du boost φ-harmonique (0.0-1.0)
            noise_reduction: activer la réduction de bruit
            abc_smoothing: activer le lissage temporel ABC

        Returns:
            Dict avec stats
        """
        t0 = time.time()

        # Lire le WAV
        try:
            with wave.open(input_path, 'rb') as wf:
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                n_frames = wf.getnframes()
                raw = wf.readframes(n_frames)
        except (FileNotFoundError, wave.Error):
            # Fallback : générer un silence
            n_channels, sampwidth, framerate, n_frames = 1, 2, 22050, 22050
            raw = b'\x00' * (n_frames * sampwidth)

        # Convertir en float
        if sampwidth == 2:
            audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        elif sampwidth == 1:
            audio = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128) / 128.0
        else:
            audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

        if n_channels > 1:
            audio = audio.reshape(-1, n_channels).mean(axis=1)  # Mono

        original_rms = np.sqrt(np.mean(audio**2))

        # === ÉTAPE 1 : Accentuation φ-harmonique ===
        if boost_strength > 0:
            audio = self._phi_harmonic_boost(audio, framerate, boost_strength)

        # === ÉTAPE 2 : Lissage temporel ABC ===
        if abc_smoothing and len(audio) > 100:
            audio = self._abc_temporal_smoothing(audio)

        # === ÉTAPE 3 : Pitch shift (rééchantillonnage simple) ===
        if abs(pitch_shift) > 0.001:
            audio = self._pitch_shift_simple(audio, framerate, pitch_shift)

        # === ÉTAPE 4 : Réduction de bruit spectrale ===
        if noise_reduction:
            audio = self._spectral_noise_reduction(audio, framerate)

        # === ÉTAPE 5 : Normalisation + clipping doux ===
        final_rms = np.sqrt(np.mean(audio**2))
        if final_rms > 0:
            target_rms = max(original_rms * 0.9, 0.05)
            audio = audio * (target_rms / final_rms)

        # Limiter à [-1, 1]
        audio = np.tanh(audio * 1.5) / 1.5
        audio = np.clip(audio, -0.99, 0.99)

        # Sauvegarder
        audio_int16 = (audio * 32767).astype(np.int16)
        with wave.open(output_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(framerate)
            wf.writeframes(audio_int16.tobytes())

        dt_ms = (time.time() - t0) * 1000
        self.stats["total_processed"] += 1
        gain_db = 20 * math.log10(final_rms / (original_rms + 1e-10)) if original_rms > 0 else 0
        self.stats["avg_gain_db"] = (self.stats["avg_gain_db"] * (self.stats["total_processed"] - 1) + gain_db) / self.stats["total_processed"]

        return {
            "input": input_path,
            "output": output_path,
            "duration_s": len(audio) / framerate,
            "original_rms": round(original_rms, 4),
            "final_rms": round(final_rms, 4),
            "gain_db": round(gain_db, 1),
            "time_ms": round(dt_ms, 1),
        }

    # ═══ φ-HARMONIC BOOST ═══

    def _phi_harmonic_boost(self, audio: np.ndarray, sr: int, strength: float) -> np.ndarray:
        """
        Boost les harmoniques basées sur φ.
        
        Méthode :
          1. Estimer la fréquence fondamentale f₀ (pitch)
          2. Calculer les harmoniques φ : f₀×φ, f₀×φ², f₀×φ³
          3. Boost sélectif dans le domaine fréquentiel
        """
        n = len(audio)
        if n < 256:
            return audio

        # FFT
        spectrum = np.fft.rfft(audio)
        freqs = np.fft.rfftfreq(n, 1.0 / sr)

        # Estimer f₀ (fréquence dominante dans la bande vocale 80-400 Hz)
        mag = np.abs(spectrum)
        voice_band = (freqs >= 80) & (freqs <= 400)
        if voice_band.any():
            f0_idx = np.argmax(mag[voice_band])
            f0 = freqs[voice_band][f0_idx]
        else:
            f0 = 150.0  # Fréquence vocale moyenne par défaut

        # Boost aux harmoniques φ
        for k in range(1, 7):
            harmonic_freq = f0 * (PHI ** k)
            if harmonic_freq < sr / 2:
                idx = np.argmin(np.abs(freqs - harmonic_freq))
                bandwidth = max(1, int(harmonic_freq * 0.05 / (sr / n)))
                lo = max(0, idx - bandwidth)
                hi = min(len(spectrum) - 1, idx + bandwidth)
                spectrum[lo:hi] *= (1.0 + strength / k)

        return np.fft.irfft(spectrum, n=n)

    # ═══ ABC TEMPORAL SMOOTHING ═══

    def _abc_temporal_smoothing(self, audio: np.ndarray) -> np.ndarray:
        """
        Lisse les transitions abruptes avec une enveloppe ABC.
        Identique au principe de ABCConversationMemory mais appliqué au signal audio.
        """
        n = len(audio)
        envelope = abc_envelope(n, alpha=0.85)

        # Appliquer l'enveloppe uniquement aux portions de début et de fin (20% de chaque côté)
        fade_len = n // 5
        if fade_len < 10:
            return audio

        smoothed = audio.copy()
        smoothed[:fade_len] *= envelope[:fade_len]
        smoothed[-fade_len:] *= envelope[n - fade_len:][::-1]  # Inverser pour le déclin

        return smoothed

    # ═══ PITCH SHIFT ═══

    def _pitch_shift_simple(self, audio: np.ndarray, sr: int, shift: float) -> np.ndarray:
        """
        Pitch shift par rééchantillonnage simple.
        shift > 0 → plus aigu, shift < 0 → plus grave.
        """
        factor = 2.0 ** (shift / 12.0)  # Conversion demi-tons → ratio
        if abs(factor - 1.0) < 0.001:
            return audio

        # Rééchantillonner
        n = len(audio)
        new_n = int(n / factor)
        indices = np.linspace(0, n - 1, new_n)
        shifted = np.interp(indices, np.arange(n), audio)

        # Ajuster la longueur pour l'adapter au cadre original
        if len(shifted) < n:
            shifted = np.pad(shifted, (0, n - len(shifted)), mode='constant')
        else:
            shifted = shifted[:n]

        return shifted.astype(np.float32)

    # ═══ SPECTRAL NOISE REDUCTION ═══

    def _spectral_noise_reduction(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """
        Réduction de bruit par soustraction spectrale simple.
        Estime le plancher de bruit et le soustrait du spectre.
        Bien adapté à l'audio Edge-TTS (pas de silence initial, parole propre).
        """
        n = len(audio)
        if n < 512:
            return audio

        spectrum = np.fft.rfft(audio)
        mag = np.abs(spectrum)
        phase = np.angle(spectrum)

        # Estimer le plancher de bruit (médiane des magnitudes basses)
        noise_floor = np.median(mag[:len(mag) // 4]) * 1.5

        # Soustraction spectrale
        mag_clean = np.maximum(mag - noise_floor, 0)
        # Limiter l'atténuation à 40 dB max
        mag_clean = np.maximum(mag_clean, mag * 0.01)

        spectrum_clean = mag_clean * np.exp(1j * phase)
        return np.fft.irfft(spectrum_clean, n=n)

    def get_stats(self) -> Dict:
        return self.stats


# ══════════════════════════════════════════════════════════════════════════
# QUICK TEST
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    hpp = HarmonicAudioPostProcessor()

    # Test avec un fichier WAV existant ou générer un test
    test_input = os.path.join(DATA_DIR, "speech_test.wav")
    test_output = os.path.join(DATA_DIR, "speech_enhanced.wav")

    # Si pas de fichier test, en générer un simple
    if not os.path.exists(test_input):
        sr = 22050
        duration = 2.0
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        # Signal vocal simulé : sinusoïde + bruit
        audio = 0.3 * np.sin(2 * np.pi * 220 * t)
        audio += 0.15 * np.sin(2 * np.pi * 440 * t)
        audio += 0.05 * np.random.randn(len(t))
        audio_int16 = (np.clip(audio, -0.99, 0.99) * 32767).astype(np.int16)
        with wave.open(test_input, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(audio_int16.tobytes())
        print(f"Fichier test créé: {test_input}")

    result = hpp.process(test_input, test_output, boost_strength=0.15, noise_reduction=True)
    print(f"Post-traitement terminé:")
    for k, v in result.items():
        print(f"  {k}: {v}")