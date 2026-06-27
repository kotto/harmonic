"""
Signature Vocale 7D Harmonique
==============================
Extrait une signature harmonique 7D a partir d'un signal audio.
"""
import math
from dataclasses import dataclass

PHI = 1.618033988749895
PHI_INV = 0.6180339887498949

@dataclass
class VoiceSignature7D:
    duration_s: float = 0.5
    dominant_freq_hz: float = 220.0
    energy_db: float = -20.0
    emotion_label: str = "neutral"
    phi_voice: float = 0.618
    alpha_voice: float = 1.176
    r_voice: float = 0.5
    c_voice: float = 0.3
    m_voice: float = 0.2
    f_voice: float = 1.0
    k_voice: float = 0.618

def extract_voice_signature(samples, sr):
    """Extrait la signature vocale 7D d'un signal audio."""
    n = len(samples)
    if n == 0:
        return VoiceSignature7D()
    
    duration = n / sr
    
    # Frequence dominante (approximation simple)
    # Compter les zero-crossings
    zero_crossings = sum(1 for i in range(1, n) if samples[i] * samples[i-1] < 0)
    dominant_freq = zero_crossings * sr / (2 * n) if n > 0 else 0
    
    # Energie
    energy = sum(s**2 for s in samples) / n
    energy_db = 10 * math.log10(energy + 1e-10)
    
    # Detection d'emotion (simplifiee)
    amplitude_max = max(abs(s) for s in samples)
    if amplitude_max > 0.8:
        emotion = "excited"
    elif amplitude_max > 0.5:
        emotion = "neutral"
    else:
        emotion = "calm"
    
    return VoiceSignature7D(
        duration_s=duration,
        dominant_freq_hz=dominant_freq,
        energy_db=energy_db,
        emotion_label=emotion,
        phi_voice=PHI_INV,
        alpha_voice=1.0 / PHI_INV,
        r_voice=min(1.0, dominant_freq / 1000),
        c_voice=min(1.0, amplitude_max),
        m_voice=min(1.0, energy * 10),
        f_voice=min(1.0, duration / 10),
        k_voice=PHI_INV
    )
