"""
KA Sonic v2 — Synthèse vocale par architecture double-couche symbolique/acoustique.

Architecture :
    texte FR
      ↓ G2P simplifié (règles graphème→phonème)
      ↓ SymbolicEncoder (ℂ⁵¹²) — composition linguistique, binding HRR
      ↓ HarmonicBridge — projection déterministe vers features acoustiques (ℝ¹⁶)
      ↓ AcousticEncoder — KD-tree sur banque de diphones synthétiques
      ↓ Concaténation + signature vocale + post-traitement
      ↓ WAV 22 kHz

Zéro poids appris, zéro réseau de neurones, 100% déterministe.

Modules :
  - phoneme_features : table articulatoire 36 phonèmes FR + G2P simplifié
  - symbolic_encoder : encodage ℂ⁵¹², binding/unbinding HRR, position
  - acoustic_encoder : features réelles 16D, KD-tree, règles phonème→acoustique
  - glottal_synth    : synthèse glottale/formantique (banque synthétique)
  - bridge           : pont symbolique→acoustique + pipeline complet
  - session          : gestionnaire de sessions per-user (futur)
"""

import os
import sys
import numpy as np

KA_SONIC_VERSION = "0.3.0-dev"
DEFAULT_SAMPLE_RATE = 22050

# ═══════════════════════════════════════════════════════════════════════════════
# Détection des dépendances
# ═══════════════════════════════════════════════════════════════════════════════

_NUMPY_OK = True
_SCIPY_OK = False
try:
    import scipy.spatial  # noqa: F401
    _SCIPY_OK = True
except ImportError:
    pass

_SOUNDFILE_OK = False
try:
    import soundfile  # noqa: F401
    _SOUNDFILE_OK = True
except ImportError:
    pass

# ═══════════════════════════════════════════════════════════════════════════════
# Imports publics
# ═══════════════════════════════════════════════════════════════════════════════

from .phoneme_features import (
    PHONEME_FEATURES,
    VOYELLES, SEMI_VOYELLES, OCCLUSIVES, FRICATIVES, NASALES, LIQUIDES,
    phoneme_distance, phoneme_similarity,
    GRAPHEME_TO_PHONEME,
)

from .symbolic_encoder import (
    SymbolicEncoder,
    encode_phoneme,
    bind, unbind, similarity,
    encode_position,
    DIM as SYMBOLIC_DIM,
)

from .acoustic_encoder import (
    AcousticEncoder,
    AcousticEntry,
    phoneme_to_acoustic_target,
    ACOUSTIC_DIM,
    weighted_distance,
)

from .glottal_synth import (
    build_synthetic_bank,
    synthesize_diphone,
    SynthDiphone,
)

from .bridge import (
    HarmonicBridge,
    simple_g2p,
    EMOTION_PROFILES,
    EMOTION_F0_CONTOURS,
    detect_accentual_groups,
)

from .voice_signature import (
    VoiceSignature,
    extract_signature,
    extract_from_wav,
    apply_signature,
    DEFAULT_VOICES,
)

from .harmonic_cloner import (
    HarmonicVoicePrint,
    extract_voice_print,
    extract_from_wav as harmonic_extract_from_wav,
    apply_voice_print,
)


def capabilities() -> dict:
    """État des dépendances et capacités du moteur."""
    return {
        "version": KA_SONIC_VERSION,
        "architecture": "dual-layer (symbolic ℂ⁵¹² + acoustic ℝ¹⁶)",
        "numpy": _NUMPY_OK,
        "scipy": _SCIPY_OK,
        "soundfile": _SOUNDFILE_OK,
        "phonemes_fr": len(PHONEME_FEATURES),
        "symbolic_dim": SYMBOLIC_DIM,
        "acoustic_dim": ACOUSTIC_DIM,
        "emotions": len(EMOTION_PROFILES),
        "voices": len(DEFAULT_VOICES),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# API rapide — démo en 3 lignes
# ═══════════════════════════════════════════════════════════════════════════════

def quick_speak(text: str, f0: float = 120.0, speed: float = 1.0,
                emotion: str = "neutre", voice: str = "homme") -> np.ndarray:
    """Synthèse vocale rapide : texte → audio float32.
    
    Construit automatiquement la banque de diphones au premier appel
    (~1200 diphones, ~7 secondes sur CPU).
    
    Args:
        text : texte français
        f0 : fréquence fondamentale (120 Hz = voix masculine moyenne)
        speed : vitesse (1.0 = normal, 0.5 = lent, 2.0 = rapide)
        emotion : neutre, joyeux, triste, urgent, calme, autoritaire, chaleureux, tendre
        voice : homme, femme, enfant, ou nom cloné
    
    Returns:
        audio float32 [-1, 1] à 22050 Hz
    """
    global _quick_bridge
    if "_quick_bridge" not in globals() or _quick_bridge is None:
        _quick_bridge = HarmonicBridge()
        _quick_bridge.build_bank()
    
    phonemes = simple_g2p(text)
    return _quick_bridge.synthesize(phonemes, f0=f0, speed=speed,
                                     emotion=emotion, voice=voice)


def save_wav(audio: np.ndarray, path: str, sr: int = DEFAULT_SAMPLE_RATE):
    """Sauvegarde un buffer audio en WAV 16-bit PCM."""
    import io
    import wave
    audio = np.clip(audio, -1.0, 1.0)
    pcm = (audio * 32767.0).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


__all__ = [
    "KA_SONIC_VERSION",
    "DEFAULT_SAMPLE_RATE",
    "capabilities",
    "quick_speak",
    "save_wav",
    # Modules
    "PHONEME_FEATURES", "VOYELLES", "SEMI_VOYELLES",
    "OCCLUSIVES", "FRICATIVES", "NASALES", "LIQUIDES",
    "phoneme_distance", "phoneme_similarity",
    "SymbolicEncoder", "encode_phoneme", "bind", "unbind", "similarity",
    "AcousticEncoder", "AcousticEntry", "phoneme_to_acoustic_target",
    "build_synthetic_bank", "synthesize_diphone", "SynthDiphone",
    "HarmonicBridge", "simple_g2p",
    "EMOTION_PROFILES", "EMOTION_F0_CONTOURS", "detect_accentual_groups",
    "VoiceSignature", "extract_signature", "extract_from_wav",
    "apply_signature", "DEFAULT_VOICES",
    "HarmonicVoicePrint", "extract_voice_print", "apply_voice_print",
]
