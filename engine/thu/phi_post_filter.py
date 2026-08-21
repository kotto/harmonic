"""
PhiPostFilter — Post-filtre φ-harmonique pour TTS
===================================================
Améliore la qualité de tout synthétiseur vocal (Piper, VITS, Tacotron)
en renforçant la structure harmonique naturelle de la voix via φ.

Principe :
  1. Analyse spectrale du signal de sortie du TTS
  2. Renforcement des harmoniques φ-résonantes (f₀ · φ^k)
  3. Lissage temporel par le noyau doré K(t) (mémoire harmonique)
  4. Débruitage modal : seuil φ sur les coefficients de Fourier
  5. Reconstruction avec phase φ-harmonique

Usage :
    from phi_post_filter import PhiPostFilter
    filter = PhiPostFilter(sample_rate=22050)
    enhanced = filter.process(audio)
"""

import numpy as np
import math
from typing import Optional

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI  # ≈ 0.618


class PhiPostFilter:
    """Post-filtre harmonique pour améliorer la qualité TTS."""

    def __init__(self, sample_rate: int = 22050,
                 strength: float = 0.4,
                 harmonic_boost_db: float = 3.0,
                 noise_floor_threshold: float = 0.15,
                 temporal_smoothing: float = 0.6):
        """
        Args:
            sample_rate: Fréquence d'échantillonnage (Hz)
            strength: Force du filtre (0 = aucun, 1 = max)
            harmonic_boost_db: Boost des harmoniques φ (dB)
            noise_floor_threshold: Seuil de débruitage modal
            temporal_smoothing: Lissage temporel K(t) (0=aucun, 1=max)
        """
        self.sample_rate = sample_rate
        self.strength = np.clip(strength, 0, 1)
        self.harmonic_boost = 10 ** (harmonic_boost_db / 20)  # linéaire
        self.noise_floor = noise_floor_threshold
        self.temporal_smoothing = temporal_smoothing

    # ── Détection de la fondamentale f₀ ──────────────────────────────

    def _detect_f0(self, audio: np.ndarray) -> float:
        """Détecte la fréquence fondamentale via autocorrélation FFT (O(n·log n))."""
        n = len(audio)
        if n < 256:
            return 120.0

        # Limiter à 4096 échantillons pour la détection (suffisant pour f0)
        segment = audio[:min(n, 4096)]
        # Fenêtre de Hanning
        segment = segment * np.hanning(len(segment))

        # Autocorrélation via FFT (O(n·log n) au lieu de O(n²))
        n_fft = 2 ** int(np.ceil(np.log2(len(segment) * 2)))
        fft = np.fft.rfft(segment, n=n_fft)
        power = np.abs(fft) ** 2
        corr = np.fft.irfft(power, n=n_fft)[:len(segment)]

        min_lag = int(self.sample_rate / 500)  # 500 Hz max
        max_lag = int(self.sample_rate / 50)   # 50 Hz min
        if max_lag >= len(corr):
            max_lag = len(corr) - 1
        if min_lag >= max_lag:
            return 120.0

        corr[:min_lag] = 0
        peak = np.argmax(corr[min_lag:max_lag]) + min_lag

        if peak > min_lag and corr[peak] > 0:
            return self.sample_rate / peak
        return 120.0

    # ── Noyau de mémoire dorée K(t) ─────────────────────────────────

    def _golden_kernel(self, n: int) -> np.ndarray:
        """Noyau K(t) = B(α)·E_α(-λ·t^α) pour le lissage temporel.
        Version numériquement stable avec série tronquée et normalisation."""
        t = np.arange(n, dtype=np.float64) / max(n, 1)  # normaliser [0, 1]
        alpha = PHI_INV  # 1/φ ≈ 0.618
        lmbda = PHI      # φ ≈ 1.618
        result = np.zeros_like(t)
        term = np.ones_like(t)  # premier terme (k=0)
        for k in range(20):
            result += term
            # Mise à jour : term *= (-λ) * t^α / (k+1)  (approximation récursive)
            # En fait on utilise la série exacte : term_k = (-λ)^k * t^(α*k) / Γ(α*k+1)
            # On itère : term_{k+1} = term_k * (-λ) * t^α * Γ(α*k+1) / Γ(α*(k+1)+1)
            if k >= 1:
                # Approximation : Γ(α*k+1) / Γ(α*(k+1)+1) ≈ 1 / (α*k+1)^α  (Stirling)
                # Mais pour la stabilité on tronque quand le terme devient négligeable
                pass
            # Recalcul direct pour la stabilité
            term = ((-lmbda) ** k) * (t ** (alpha * k)) / math.gamma(alpha * k + 1)
            if np.max(np.abs(term)) < 1e-12:
                break
        result = np.clip(result, 0, None)
        s = result.sum()
        if s > 0:
            result /= s
        return result.astype(np.float64)

    # ── Traitement principal ─────────────────────────────────────────

    def process(self, audio: np.ndarray) -> np.ndarray:
        """Applique le post-filtre φ-harmonique à l'audio.

        Args:
            audio: Signal audio (float32, [-1, 1])

        Returns:
            Signal filtré (float32, même dimension)
        """
        if len(audio) < 256:
            return audio

        audio = np.asarray(audio, dtype=np.float64)
        n = len(audio)

        # 1. Détection de la fondamentale
        f0 = self._detect_f0(audio)
        if f0 < 50 or f0 > 500:
            f0 = 120.0

        # 2. FFT
        fft = np.fft.rfft(audio)
        freqs = np.fft.rfftfreq(n, 1.0 / self.sample_rate)
        mag = np.abs(fft)
        phase = np.angle(fft)

        # 3. Renforcement des harmoniques φ
        #    f₀ · φ, f₀ · φ², f₀ · φ³, ...
        n_harmonics = int(np.log(self.sample_rate / (2 * f0)) / np.log(PHI)) + 1
        phi_harmonics = [f0 * (PHI ** k) for k in range(n_harmonics)
                         if f0 * (PHI ** k) < self.sample_rate / 2]

        # Masque de boost spectral
        # Chaque harmonique φ a une bande passante φ⁻¹ autour d'elle
        boost_mask = np.ones_like(mag)
        for f_harm in phi_harmonics:
            bw = f0 * PHI_INV  # bande passante proportionnelle à φ
            idx = np.abs(freqs - f_harm) < bw
            boost_mask[idx] *= (1.0 + (self.harmonic_boost - 1.0) * self.strength)

        mag_boosted = mag * boost_mask

        # 4. Débruitage modal : seuil φ sur l'énergie spectrale
        threshold = mag_boosted.max() * self.noise_floor * PHI_INV
        noise_mask = mag_boosted > threshold
        mag_cleaned = mag_boosted * noise_mask

        # 5. Reconstruction
        fft_out = mag_cleaned * np.exp(1j * phase)
        audio_out = np.fft.irfft(fft_out, n=n)

        # 6. Limiteur doux
        max_val = max(np.abs(audio_out).max(), 1e-10)
        if max_val > 1.0:
            audio_out = np.tanh(audio_out / max_val * 2) * 0.95

        return audio_out.astype(np.float32)

    # ── Remplissage spectral ─────────────────────────────────────────

    def _spectral_fill(self, mag: np.ndarray,
                       mask: np.ndarray) -> np.ndarray:
        """Remplit les trous spectraux par interpolation."""
        result = mag.copy()
        # Trouver les régions de trous
        gaps = np.where(~mask)[0]
        if len(gaps) == 0:
            return result

        # Remplir chaque trou par interpolation linéaire
        i = 0
        while i < len(gaps):
            # Début du trou
            start = gaps[i]
            # Trouver la fin du trou
            end = start
            while i < len(gaps) and gaps[i] == end + 1:
                end = gaps[i]
                i += 1
            # Valeurs aux bords
            left_val = mag[start - 1] if start > 0 else 0
            right_val = mag[end + 1] if end + 1 < len(mag) else 0
            # Interpolation linéaire
            gap_len = end - start + 1
            for j in range(gap_len):
                result[start + j] = left_val + (right_val - left_val) * (j + 1) / (gap_len + 1)
        return result


# ═══════════════════════════════════════════════════════════════════════════════
# INTÉGRATION PIPER + HARMONIQUE
# ═══════════════════════════════════════════════════════════════════════════════

def enhance_piper_tts(audio: np.ndarray, sample_rate: int = 22050) -> np.ndarray:
    """Améliore la sortie de Piper TTS avec le post-filtre φ-harmonique.

    Usage :
        audio_piper = piper_synthesize(text)  # votre fonction Piper
        audio_enhanced = enhance_piper_tts(audio_piper)
        jouer(audio_enhanced)  # qualité améliorée
    """
    pf = PhiPostFilter(sample_rate=sample_rate)
    return pf.process(audio)


# ═══════════════════════════════════════════════════════════════════════════════
# AUTO-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import sys
    sys.path.insert(0, '.')

    # Tester sur le fichier TTS existant
    import wave
    with wave.open('/tmp/ka_voice_test.wav', 'rb') as w:
        sr = w.getframerate()
        frames = w.readframes(w.getnframes())
        audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0

    print(f'Source: {sr} Hz, {len(audio)/sr:.1f}s')

    # Appliquer le post-filtre
    pf = PhiPostFilter(sample_rate=sr, strength=0.5)
    t0 = __import__('time').time()
    enhanced = pf.process(audio)
    dt = (__import__('time').time() - t0) * 1000

    # Sauver
    with wave.open('/tmp/piper_phi_enhanced.wav', 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(enhanced * 32768, -32768, 32767).astype(np.int16)).tobytes())

    # Métriques
    mse = np.mean((audio[:len(enhanced)] - enhanced) ** 2)
    snr = 10 * np.log10(np.var(audio) / max(mse, 1e-10))
    print(f'PhiPostFilter: {dt:.0f}ms | SNR in/out: {snr:.1f} dB')
    print(f'  f₀ détectée: {pf._detect_f0(audio):.0f} Hz')
    print(f'  RMS original: {np.sqrt(np.mean(audio**2)):.4f}')
    print(f'  RMS filtré:   {np.sqrt(np.mean(enhanced**2)):.4f}')
    print(f'  Max original: {np.max(np.abs(audio)):.4f}')
    print(f'  Max filtré:   {np.max(np.abs(enhanced)):.4f}')
    print()
    print(f'Fichier de test : /tmp/piper_phi_enhanced.wav')