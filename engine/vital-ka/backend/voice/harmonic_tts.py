"""
TTS DIRECT — Synthèse spectrale → IFFT → overlap-add.
Sans codec, sans ψ, sans complexité inutile.
"""

import os, sys, math, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tts_engine import text_to_phonemes

SR = 22050
FFT_SIZE = 1024
HOP = FFT_SIZE // 4
PHI = 1.618033988749895
TAU = 2.0 * math.pi

# ═══════════════════════════════════════════════════════════════════
# SPÉCIFICATIONS
# ═══════════════════════════════════════════════════════════════════

FORMANTS = {
    "a": [(750, 1.0, 90), (1200, 0.7, 110), (2400, 0.4, 170), (3500, 0.2, 250)],
    "e": [(400, 0.8, 70), (2000, 1.0, 110), (2800, 0.5, 170), (3700, 0.2, 250)],
    "i": [(280, 0.7, 60), (2300, 1.0, 100), (3000, 0.5, 160), (3800, 0.2, 240)],
    "o": [(500, 0.9, 85), (900, 0.6, 110), (2500, 0.3, 170), (3500, 0.1, 250)],
    "u": [(300, 0.7, 60), (700, 0.5, 85), (2200, 0.2, 160), (3300, 0.1, 220)],
    "y": [(280, 0.7, 60), (1900, 0.8, 100), (2300, 0.4, 160), (3400, 0.2, 240)],
    "eu":[(400, 0.8, 80), (1500, 0.7, 110), (2300, 0.3, 170), (3400, 0.1, 250)],
    "a~":[(350, 0.7, 100),(1100, 0.5, 130), (2400, 0.25, 200),(3300, 0.08, 280)],
    "e~":[(300, 0.7, 90), (1600, 0.5, 130), (2600, 0.25, 200),(3500, 0.08, 280)],
    "o~":[(400, 0.7, 100),(900, 0.5, 130),  (2500, 0.25, 200),(3400, 0.08, 280)],
    "w":  [(300, 0.5, 60), (700, 0.4, 100),  (2300, 0.2, 160)],
    "b":  [(400, 0.5, 250),(1200, 0.4, 350)],
    "d":  [(400, 0.5, 250),(2000, 0.4, 350)],
    "g":  [(400, 0.5, 250),(1500, 0.4, 400)],
    "p":  [(400, 0.3, 250),(1200, 0.35, 350)],
    "t":  [(400, 0.3, 250),(2000, 0.35, 350)],
    "k":  [(400, 0.25, 250),(1500, 0.35, 400)],
    "v":  [(1500, 0.4, 500),(3500, 0.2, 600)],
    "f":  [(2000, 0.3, 600),(4000, 0.2, 700)],
    "z":  [(3000, 0.5, 600),(4500, 0.2, 700)],
    "s":  [(3500, 0.4, 700),(5000, 0.3, 800)],
    "j":  [(2200, 0.5, 500),(3800, 0.2, 600)],
    "ch": [(2500, 0.4, 600),(4000, 0.3, 700)],
    "l":  [(350, 0.6, 100),(1200, 0.3, 160), (2600, 0.2, 220)],
    "r":  [(400, 0.5, 160),(1300, 0.3, 220), (2400, 0.4, 300)],
    "m":  [(280, 0.6, 60), (1000, 0.2, 160), (2400, 0.08, 300)],
    "n":  [(280, 0.6, 60), (1700, 0.2, 160), (2600, 0.08, 300)],
}

VOICED = set("aeiouyeua~e~o~bv dgz j lrmnw")


# ═══════════════════════════════════════════════════════════════════
# MOTEUR
# ═══════════════════════════════════════════════════════════════════

def _build_magnitude(phoneme: str, f0: float, n_bins: int) -> np.ndarray:
    """Construit un spectre de magnitude pour un phonème."""
    freqs = np.fft.rfftfreq(FFT_SIZE, 1.0 / SR)[:n_bins]
    mag = np.zeros(n_bins, dtype=np.float64)
    
    fs = FORMANTS.get(phoneme, FORMANTS["a"])
    for freq, amp, bw in fs:
        if freq <= 0 or freq >= SR / 2:
            continue
        sigma = bw / 2.0
        mag += amp * np.exp(-0.5 * ((freqs - freq) / sigma) ** 2)
    
    # Harmoniques si voisé
    if phoneme in VOICED and f0 > 0:
        for h in range(1, min(int(SR / 2 / f0), 100)):
            hf = h * f0
            if hf >= SR / 2:
                break
            ha = (1.0 / h ** 1.5) * 0.2
            mag += ha * np.exp(-0.5 * ((freqs - hf) / (f0 * 0.08)) ** 2)
    
    # Bruit de fond + tilt spectral
    mag += 0.01
    tilt = np.ones(n_bins)
    mask = freqs > 500
    tilt[mask] = (500.0 / freqs[mask]) ** 0.5
    mag *= tilt
    
    return mag.astype(np.float64)


def speak(text: str, f0: float = 130.0) -> np.ndarray:
    """Synthèse source-filtre : pulse train → FFT → filtre spectral → IFFT."""
    phonemes = text_to_phonemes(text)
    if not phonemes:
        return np.zeros(int(0.3 * SR), dtype=np.float32)
    
    n_bins = FFT_SIZE // 2 + 1
    dur_per_ph = 0.140
    samples_per_ph = int(dur_per_ph * SR)
    
    # Générer la source glottale continue (pulse train à F0 variable)
    total_dur = len(phonemes) * dur_per_ph
    n_total = int(total_dur * SR)
    
    # Source = pulse train
    source = np.zeros(n_total, dtype=np.float64)
    period = int(SR / f0)
    for i in range(0, n_total, period):
        # Impulsion de Rosenborg (glottale simplifiée)
        pulse_len = min(int(0.004 * SR), n_total - i)
        if pulse_len > 0:
            t = np.linspace(0, np.pi, pulse_len)
            source[i:i + pulse_len] = np.sin(t) * 0.9
    
    # Ajouter un peu de bruit pour les fricatives
    rng = np.random.RandomState(abs(hash(text)) % (2**31))
    noise = rng.normal(0, 0.05, n_total)
    source += noise
    
    # ── Filtrage spectral frame par frame ─────────────────────────
    frames_out = []
    
    for i, ph in enumerate(phonemes):
        ph_start = i * samples_per_ph
        n_frames = max(1, samples_per_ph // HOP)
        
        mag_curr = _build_magnitude(ph, f0, n_bins)
        mag_next = _build_magnitude(
            phonemes[i + 1] if i + 1 < len(phonemes) else ph, f0, n_bins
        )
        mag_prev = _build_magnitude(
            phonemes[i - 1] if i > 0 else ph, f0, n_bins
        )
        
        for j in range(n_frames):
            t = j / max(n_frames - 1, 1)
            w = 0.5 - 0.5 * math.cos(t * math.pi)
            if t < 0.5:
                mag = mag_prev * (1 - 2*w) + mag_curr * (2*w)
            else:
                mag = mag_curr * (2 - 2*w) + mag_next * (2*w - 1)
            
            # Extraire la frame source
            pos = ph_start + j * HOP
            frame_src = source[pos:pos + FFT_SIZE]
            if len(frame_src) < FFT_SIZE:
                frame_src = np.pad(frame_src, (0, FFT_SIZE - len(frame_src)))
            
            # FFT → appliquer le filtre → IFFT
            src_spec = np.fft.rfft(frame_src * np.hanning(FFT_SIZE))
            # Multiplication spectrale (filtrage)
            filtered_spec = src_spec * mag[:len(src_spec)]
            frame_out = np.fft.irfft(filtered_spec, n=FFT_SIZE).real
            
            win = np.hanning(FFT_SIZE)
            frames_out.append(frame_out * win)
    
    if not frames_out:
        return np.zeros(int(0.3 * SR), dtype=np.float32)
    
    # ── Overlap-add ──────────────────────────────────────────────
    total_len = FFT_SIZE + HOP * (len(frames_out) - 1)
    out = np.zeros(total_len, dtype=np.float64)
    norm = np.zeros(total_len, dtype=np.float64)
    
    for i, f in enumerate(frames_out):
        pos = i * HOP
        out[pos:pos + FFT_SIZE] += f
        norm[pos:pos + FFT_SIZE] += 1.0
    
    norm[norm < 1e-6] = 1.0
    result = out / norm
    
    result -= np.mean(result)
    try:
        from scipy import signal
        b, a = signal.butter(2, 80 / (SR / 2), btype="high")
        result = signal.lfilter(b, a, result)
    except:
        pass
    
    peak = np.max(np.abs(result)) + 1e-10
    return (result / peak * 0.95).astype(np.float32)


# ═══════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import wave, os
    
    print("🎵 Direct TTS — IFFT + overlap-add")
    
    t0 = time.perf_counter()
    audio = speak("Bonjour le monde. Comment allez-vous ?", f0=130)
    elapsed = (time.perf_counter() - t0) * 1000
    
    path = os.path.join(os.path.dirname(__file__), "direct_tts.wav")
    pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    
    rms = np.sqrt(np.mean(audio**2))
    spec = np.abs(np.fft.rfft(audio))
    freqs = np.fft.rfftfreq(len(audio), 1 / SR)
    sp = np.sum(spec[(freqs >= 300) & (freqs <= 3400)]) / np.sum(spec) * 100
    
    print(f"   RMS={rms:.3f} | Parole={sp:.0f}% | {len(audio)/SR:.1f}s | {elapsed:.0f}ms")
    print(f"   💾 {path}")
