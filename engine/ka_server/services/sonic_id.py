"""
sonic_id.py — Empreinte sonore pseudo-aléatoire agréable.

À partir d'un identifiant (numéro de commande, dossier patient, user ID…),
génère un court signal audio déterministe (pentatonique, timbre doux) qui lui
est unique — une *signature sonore* reconnaissable par l'oreille humaine.

Usage :
    from ka_server.services.sonic_id import sonic_id_wav
    wav_bytes = sonic_id_wav("ABC-2026-00042", variant="mobile")
    # → bytes WAV prêt à servir

Variants :
    "mobile"  : gamme majeure, tempo vif (100-140), légère réverbération
    "care"    : gamme mineure/dorienne, tempo lent (70-95), plus spacieux
    "default" : équilibré, choix aléatoire mais déterministe

Cache :
    Le résultat est mis en cache LRU (512 entrées) — les appels répétés
    avec le même identifiant retournent les mêmes bytes instantanément.
"""

import hashlib
import io
import struct
from functools import lru_cache
from typing import Optional

import numpy as np

# ── Intervalles musicaux (degrés relatifs à la fondamentale) ────────────────

SCALES = {
    "major_pentatonic": [0, 2, 4, 7, 9],
    "minor_pentatonic": [0, 3, 5, 7, 10],
    "dorian":           [0, 2, 3, 5, 7, 9, 10],
    "lydian":           [0, 2, 4, 6, 7, 9, 11],
    "mixolydian":       [0, 2, 4, 5, 7, 9, 10],
}

SCALE_PREFERENCE = {
    "mobile": ["major_pentatonic", "lydian"],
    "care":   ["minor_pentatonic", "dorian", "mixolydian"],
    "default": list(SCALES.keys()),
}

SAMPLE_RATE = 22050  # plus léger que 44100, qualité suffisante pour une notification


# ── Helpers ──────────────────────────────────────────────────────────────────

def _seed(identifier: str) -> int:
    digest = hashlib.sha256(identifier.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def _midi_to_hz(note: float) -> float:
    return 440.0 * 2 ** ((note - 69) / 12)


def _envelope(n: int, attack_ratio: float = 0.06, release_ratio: float = 0.25) -> np.ndarray:
    """Enveloppe AR douce (cosinus pour éviter les clics)."""
    env = np.ones(n)
    a = max(1, int(attack_ratio * n))
    r = max(1, int(release_ratio * n))
    env[:a] = 0.5 * (1 - np.cos(np.pi * np.arange(a) / a))
    env[-r:] = 0.5 * (1 + np.cos(np.pi * np.arange(r) / r))
    return env


# ── Générateur principal ────────────────────────────────────────────────────

def _generate_audio(identifier: str, variant: str = "default") -> np.ndarray:
    """Retourne le signal audio (float32 mono) pour un identifiant donné."""
    rng = np.random.default_rng(_seed(identifier))

    # Choix de gamme selon le variant
    scale_names = SCALE_PREFERENCE.get(variant, SCALE_PREFERENCE["default"])
    scale_name = scale_names[int(rng.integers(0, len(scale_names)))]
    scale = SCALES[scale_name]

    # Paramètres musicaux déterministes
    root = int(rng.integers(48, 60))          # Do2–Si2
    if variant == "care":
        root = root - 3                       # plus grave = plus apaisant

    tempo = int(rng.integers(
        75 if variant == "care" else 100,
        100 if variant == "care" else 140,
    ))
    beat_duration = 60.0 / tempo
    note_duration = beat_duration * 0.5       # croche

    melody_length = int(rng.integers(7, 13))

    signal_parts = []

    for i in range(melody_length):
        degree = int(rng.integers(0, len(scale)))
        octave = int(rng.choice([0, 12, 12, 24]))  # on monte plus souvent
        midi_note = root + scale[degree] + octave
        frequency = _midi_to_hz(midi_note)

        duration_factor = float(rng.choice([0.75, 1.0, 1.25, 1.5]))
        duration = note_duration * duration_factor
        n = int(duration * SAMPLE_RATE)
        t = np.arange(n) / SAMPLE_RATE

        # Timbre : fondamentale + harmoniques apaisantes (odd + even)
        tone = (
            0.70 * np.sin(2 * np.pi * frequency * t) +
            0.20 * np.sin(4 * np.pi * frequency * t) +
            0.07 * np.sin(6 * np.pi * frequency * t) +
            0.03 * np.sin(8 * np.pi * frequency * t)
        )

        # Enveloppe de note
        tone *= _envelope(n, attack_ratio=0.05, release_ratio=0.22)
        tone *= float(rng.uniform(0.50, 0.85))

        signal_parts.append(tone)

        # Légère respiration entre les notes
        gap = int(rng.uniform(0.005, 0.06) * SAMPLE_RATE)
        signal_parts.append(np.zeros(gap))

    audio = np.concatenate(signal_parts)

    # Fade global in/out (évite les clics en début/fin de fichier)
    fade_len = int(0.04 * SAMPLE_RATE)
    audio[:fade_len] *= np.linspace(0, 1, fade_len)
    audio[-fade_len:] *= np.linspace(1, 0, fade_len)

    # Normalisation
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio /= peak * 1.05  # léger headroom

    return audio


# ── Encodage WAV en mémoire ─────────────────────────────────────────────────

def _audio_to_wav_bytes(audio: np.ndarray) -> bytes:
    """Encode un tableau float32 en WAV 16-bit PCM et retourne les bytes."""
    n = len(audio)
    # Convertir en int16
    audio_int16 = np.int16(audio * 32767 * 0.95)

    buf = io.BytesIO()

    # Entête WAV
    data_size = n * 2  # 16-bit = 2 bytes par échantillon
    fmt_size = 16
    riff_size = 4 + (8 + fmt_size) + (8 + data_size)

    buf.write(b"RIFF")
    buf.write(struct.pack("<I", riff_size))
    buf.write(b"WAVE")

    buf.write(b"fmt ")
    buf.write(struct.pack("<I", fmt_size))
    buf.write(struct.pack("<HHIIHH",
        1,          # PCM
        1,          # 1 canal (mono)
        SAMPLE_RATE,
        SAMPLE_RATE * 2,  # byte rate
        2,          # block align
        16,         # bits per sample
    ))

    buf.write(b"data")
    buf.write(struct.pack("<I", data_size))
    buf.write(audio_int16.tobytes())

    return buf.getvalue()


# ── Interface publique avec cache ────────────────────────────────────────────

@lru_cache(maxsize=512)
def sonic_id_wav(identifier: str, variant: str = "default") -> bytes:
    """
    Retourne les bytes WAV pour un identifiant.

    Parameters
    ----------
    identifier : str
        Identifiant unique (numéro de commande, dossier patient, etc.)
    variant : str
        "mobile" → gamme majeure, tempo vif
        "care"   → gamme mineure/dorienne, tempo lent, plus grave
        "default" → équilibré

    Returns
    -------
    bytes : contenu WAV 16-bit mono 22050 Hz, prêt à servir comme
            Content-Type: audio/wav
    """
    audio = _generate_audio(identifier, variant=variant)
    return _audio_to_wav_bytes(audio)


def sonic_id_duration(identifier: str, variant: str = "default") -> float:
    """Retourne la durée approximative en secondes (sans générer le WAV)."""
    np.random.default_rng(_seed(identifier))  # seed for reproducibility
    # Approximation simplifiée
    rng = np.random.default_rng(_seed(identifier))
    tempo = int(rng.integers(75, 140))
    beat = 60.0 / tempo
    length = int(rng.integers(7, 13))
    return length * beat * 0.5 * 1.15  # notes + gaps + fades