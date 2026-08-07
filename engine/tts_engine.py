#!/usr/bin/env python3
"""
KA TTS v2 — Moteur de synthèse vocale paramétrique français.
=============================================================
Synthèse formantique avec G2P complet, prosodie, clonage spectral.
Zéro réseau de neurones — 100% déterministe, CPU uniquement.

Usage :
    python tts_engine.py "Bonjour le monde"
    python tts_engine.py --test
    python tts_engine.py --record 30 --out voix.wav
    python tts_engine.py --clone voix.wav "Texte cloné"
    python tts_engine.py --devices
"""

from __future__ import annotations

import sys, os, math, time, wave, io, re, argparse
from typing import Optional

import numpy as np

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

SAMPLE_RATE = 22050
PHI = 1.618033988749895
TAU = 2.0 * math.pi

# ═══════════════════════════════════════════════════════════════════════════════
# AUDIO I/O
# ═══════════════════════════════════════════════════════════════════════════════

def list_devices() -> None:
    """Liste tous les périphériques audio (entrée + sortie)."""
    import sounddevice as sd
    print("\n📢 SORTIES :")
    for i, d in enumerate(sd.query_devices()):
        if d["max_output_channels"] > 0:
            print(f"  [{i:2d}] {d['name'][:55]}")
    print("\n🎤 ENTRÉES :")
    for i, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] > 0:
            print(f"  [{i:2d}] {d['name'][:55]}")


def test_audio(device: Optional[int] = None) -> None:
    """Émet un bip 440 Hz + sweep 200→2000 Hz pour tester la sortie."""
    import sounddevice as sd
    sr = 44100

    t_bip = np.arange(0, int(0.3 * sr)) / sr
    bip = np.sin(TAU * 440 * t_bip).astype(np.float32)

    silence = np.zeros(int(0.15 * sr), dtype=np.float32)

    t_sweep = np.arange(0, int(0.5 * sr)) / sr
    sweep = np.sin(TAU * (200 + 1800 * t_sweep / t_sweep[-1]) * t_sweep).astype(np.float32)

    audio = np.concatenate([bip, silence, sweep]) * 0.6
    print(f"\n🔊 Test audio — device: {'défaut' if device is None else device}")
    print("   Tu dois entendre : BIP → silence → son montant (200→2000 Hz)")
    sd.play(audio, sr, device=device)
    sd.wait()
    print("   ✅ Fin du test.\n")


def play_wav(path: str, device: Optional[int] = None) -> None:
    """Joue un fichier WAV via sounddevice."""
    import sounddevice as sd
    with wave.open(path, "rb") as w:
        sr = w.getframerate()
        n = w.getnframes()
        if n == 0:
            print(f"   ⚠️  Fichier vide: {path}")
            return
        pcm = np.frombuffer(w.readframes(n), dtype="<i2")
    audio = pcm.astype(np.float32) / 32767.0
    print(f"   ▶️  {path} ({len(audio)/sr:.1f}s, {sr}Hz)")
    sd.play(audio, sr, device=device)
    sd.wait()


def record_mic(duration_s: float = 30.0, device: Optional[int] = None) -> Optional[tuple]:
    """Enregistre depuis le micro. Retourne (audio, sr) ou None si muet."""
    import sounddevice as sd
    sr = 44100
    print(f"🔴 Enregistrement {duration_s:.0f}s... Parle !")
    audio = sd.rec(int(duration_s * sr), samplerate=sr, channels=1, device=device, dtype="float32")
    sd.wait()
    peak = float(np.max(np.abs(audio)))
    if peak < 0.001:
        print("⚠️  Micro muet — vérifie le périphérique d'entrée.")
        return None
    audio = audio[:, 0] / (peak + 1e-10) * 0.95
    print(f"✅ {len(audio)/sr:.1f}s enregistrées (peak={peak:.3f})")
    return audio.astype(np.float32), sr


def save_wav(audio: np.ndarray, path: str, sr: int = SAMPLE_RATE) -> str:
    """Sauvegarde un buffer float32 [-1,1] en WAV 16-bit PCM mono."""
    audio = np.clip(audio, -1.0, 1.0)
    pcm = (audio * 32767.0).astype("<i2")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    return path


# ═══════════════════════════════════════════════════════════════════════════════
# G2P — GRAPHÈME → PHONÈME (français complet)
# ═══════════════════════════════════════════════════════════════════════════════

# Phonèmes utilisés (notation ASCII lisible)
# Voyelles orales  : a, e, i, o, u, y, eu, oe, schwa
# Voyelles nasales : a~, e~, o~, oe~
# Semi-voyelles    : w, yod, ui
# Occlusives       : p, b, t, d, k, g
# Fricatives       : f, v, s, z, ch, j, ss
# Liquides         : l, r
# Nasales          : m, n, gn
# Silence          : _

# Règles ordonnées par priorité (les plus longues d'abord)
G2P_RULES = [
    # ── Digrammes / trigrammes prioritaires ──
    ("eau", "o"),  ("aud", "o"),  ("aut", "o"),  ("aux", "o"),
    ("aient", "e"), ("ais", "e"), ("ait", "e"),
    # "er"/"ez" en fin de mot uniquement — géré dans le post-traitement
    ("oint", "w+e~"), ("ouin", "w+e~"),
    ("oin", "w+e~"),  ("oui", "w+i"),
    ("ille", "i+yod"), ("ill", "i+yod"),
    ("eil", "e+yod"),  ("euil", "eu+yod"),
    ("ail", "a+yod"),  ("ouil", "u+yod"),

    # ── Nasales (suivies de consonne ou fin de mot) ──
    ("an", "a~"), ("am", "a~"), ("en", "a~"), ("em", "a~"),
    ("in", "e~"), ("im", "e~"), ("ain", "e~"), ("aim", "e~"),
    ("ein", "e~"), ("yn", "e~"), ("ym", "e~"),
    ("on", "o~"), ("om", "o~"),
    ("un", "e~"), ("um", "e~"),

    # ── Digrammes consonne ──
    ("ch", "ch"), ("ph", "f"),  ("th", "t"),
    ("gn", "gn"), ("gu", "g"),  ("qu", "k"),
    ("ge", "j"),  ("gi", "j"),  ("gy", "j"),
    ("ce", "s"),  ("ci", "s"),  ("cy", "s"),
    ("ç", "s"),

    # ── Voyelles composées ──
    ("eu", "eu"), ("oeu", "eu"), ("oe", "eu"),
    ("au", "o"),  ("eau", "o"),
    ("ai", "e"),  ("ei", "e"),  ("et", "e"),
    ("ou", "u"),  ("où", "u"),
    ("oi", "w+a"),

    # ── Consonnes simples ──
    ("b", "b"), ("c", "k"), ("d", "d"), ("f", "f"),
    ("g", "g"), ("h", "_"), ("j", "j"), ("k", "k"),
    ("l", "l"), ("m", "m"), ("n", "n"), ("p", "p"),
    ("r", "r"), ("s", "s"), ("t", "t"), ("v", "v"),
    ("w", "w"), ("x", "s"), ("z", "z"),

    # ── Voyelles simples ──
    ("a", "a"), ("à", "a"), ("â", "a"),
    ("e", "eu"), ("é", "e"), ("è", "e"), ("ê", "e"), ("ë", "e"),
    ("i", "i"), ("î", "i"), ("ï", "i"),
    ("o", "o"), ("ô", "o"),
    ("u", "u"), ("ù", "u"), ("û", "u"), ("ü", "u"),
    ("y", "i"),
]

# Lettres muettes en fin de mot (sauf liaison)
SILENT_ENDINGS = {"e", "s", "x", "z", "t", "d", "p", "g", "h", "ent"}

# Mots où le 'e' final se prononce (schwa)
E_MUET_EXCEPTIONS = {"le", "ce", "de", "ne", "que", "je", "te", "se", "me"}


def _is_vowel_char(c: str) -> bool:
    return c in "aeiouyéèêëàâîïôûùüœ"


def _word_to_phonemes(word: str, is_last: bool = False) -> list[str]:
    """Convertit un mot français en liste de phonèmes.

    Gère : digrammes, nasales contextuelles, lettres muettes, schwa final.
    """
    if not word:
        return []

    word = word.lower()
    phonemes: list[str] = []
    i = 0
    n = len(word)

    while i < n:
        matched = False
        for length in range(min(4, n - i), 0, -1):
            chunk = word[i:i + length]
            # Vérifier si une règle correspond
            for pattern, ph in G2P_RULES:
                if pattern == chunk:
                    # Règles contextuelles : nasales seulement si suivies
                    # d'une consonne (ou fin de mot)
                    if ph in ("a~", "e~", "o~", "oe~"):
                        next_i = i + length
                        if next_i < n and (
                            _is_vowel_char(word[next_i])
                            or word[next_i] in "nm"
                        ):
                            if chunk[0] in G2P_RULES_DICT:
                                phonemes.append(G2P_RULES_DICT[chunk[0]])
                            if chunk[1] in G2P_RULES_DICT:
                                phonemes.append(G2P_RULES_DICT[chunk[1]])
                            i += length
                            matched = True
                            break

                    # Gérer les phonèmes multiples (séparés par +)
                    if "+" in ph:
                        for sub_ph in ph.split("+"):
                            if sub_ph in PHONEME_DEFS or sub_ph == "_":
                                phonemes.append(sub_ph)
                    else:
                        phonemes.append(ph)
                    i += length
                    matched = True
                    break
            if matched:
                break

        if not matched:
            i += 1  # ignorer caractère inconnu

    # ── Post-traitement ──────────────────────────────────────────────

    # 'er'/'ez' en fin de mot → 'e' (infinitif/2e personne)
    if len(phonemes) >= 2:
        last_two = "".join(phonemes[-2:])
        if word.endswith("er") and phonemes[-2:] == ["eu", "r"]:
            phonemes[-2:] = ["e"]
        elif word.endswith("ez") and phonemes[-1] == "z":
            # Déjà géré : 'ez' non matché → 'e'+'u'+'z', puis 'z' supprimé
            if phonemes[-1] == "z":
                phonemes.pop()
            if len(phonemes) >= 2 and phonemes[-2] == "e" and phonemes[-1] == "u":
                phonemes[-2:] = ["e"]

    # Fusionner les consonnes doublées (ll→l, mm→m, etc.)
    # MAIS ne pas perdre de consonnes : juste éviter les doublons adjacents
    merged: list[str] = []
    for ph in phonemes:
        if merged and ph == merged[-1] and ph in "lmnprstbfgk":
            continue
        merged.append(ph)
    phonemes = merged

    # 'e' muet final — sauf monosyllabes
    if phonemes and phonemes[-1] == "eu" and word not in E_MUET_EXCEPTIONS:
        if len(phonemes) > 2:
            phonemes.pop()

    # 'ent' final — muet (3e personne pluriel)
    if word.endswith("ent") and len(phonemes) >= 2:
        if phonemes[-1] == "t" and phonemes[-2] == "a~":
            phonemes.pop()  # supprimer le 't' muet

    # Consonnes muettes finales : s, x, z, t, d, p (pluriel, liaisons)
    silent_final = {"s", "x", "z", "t", "d", "p"}
    while len(phonemes) >= 3 and phonemes[-1] in silent_final:
        # Garder si mot très court
        if len(phonemes) <= 2:
            break
        if phonemes[-1] == "s" or phonemes[-1] == "x":
            phonemes.pop()
        elif phonemes[-1] in ("t", "d", "z"):
            if len(phonemes) >= 4:
                phonemes.pop()
            else:
                break
        else:
            break

    return phonemes


# Cache pour les règles G2P
G2P_RULES_DICT = {p: ph for p, ph in G2P_RULES if len(p) == 1}


def _is_punctuation(c: str) -> bool:
    return c in ".!?,;:…"


def text_to_phonemes(text: str) -> list[str]:
    """Convertit un texte français complet en séquence de phonèmes.

    Gère : ponctuation → pauses, mots → phonèmes, liaisons simples.
    """
    text = text.strip()
    if not text:
        return ["_"]

    # Insérer des espaces autour de la ponctuation
    text = re.sub(r"([.!?,;:…])", r" \1 ", text)
    text = re.sub(r"\s+", " ", text).strip()

    tokens = text.lower().split()
    phonemes: list[str] = []
    prev_word_had_vowel_end = False

    for ti, token in enumerate(tokens):
        # Ponctuation → pause
        if token in ".!?":
            phonemes.append("_")  # pause longue
            prev_word_had_vowel_end = False
            continue
        elif token in ",;:":
            phonemes.append("_")  # pause courte
            prev_word_had_vowel_end = False
            continue
        elif token == "…":
            phonemes.extend(["_", "_"])
            prev_word_had_vowel_end = False
            continue

        # Apostrophe → coller au mot suivant
        if token in ("l'", "d'", "s'", "n'", "m'", "t'", "c'", "j'", "qu'"):
            prev_word_had_vowel_end = False
            continue

        # Mot normal
        is_last = (ti == len(tokens) - 1)
        word_ph = _word_to_phonemes(token, is_last=is_last)

        if not word_ph:
            continue

        # Liaison simple : mot précédent terminé par consonne muette,
        # mot suivant commence par voyelle
        if prev_word_had_vowel_end and word_ph and word_ph[0] in "aeiouy":
            # Ajouter un 'z' de liaison léger
            pass  # Simplifié — pas de liaison complète pour l'instant

        # Pause entre mots
        if phonemes and phonemes[-1] != "_":
            phonemes.append("_")

        phonemes.extend(word_ph)

        # Détecter si le mot se termine par une voyelle (pour liaison future)
        if word_ph:
            last_ph = word_ph[-1]
            prev_word_had_vowel_end = last_ph in "aeiouyeuoeschwa" or last_ph.startswith("a~") or last_ph.startswith("e~") or last_ph.startswith("o~")

    return phonemes if phonemes else ["_"]


# ═══════════════════════════════════════════════════════════════════════════════
# SYNTHÈSE DE PHONÈMES — modèle source-filtre audible
# ═══════════════════════════════════════════════════════════════════════════════

# Définition des phonèmes : (type, voisé, [(freq, amp, bw), ...], noise_gain)
PHONEME_DEFS: dict[str, tuple] = {
    # ── Voyelles orales ──────────────────────────────────────────────
    "a":     ("vowel", True,  [(750,  1.0, 60), (1200, 0.7, 70), (2400, 0.4, 110), (3500, 0.2, 170)], 0.0),
    "e":     ("vowel", True,  [(400,  0.8, 50), (2000, 1.0, 70), (2800, 0.5, 110), (3700, 0.2, 170)], 0.0),
    "i":     ("vowel", True,  [(280,  0.7, 40), (2300, 1.0, 60), (3000, 0.5, 100), (3800, 0.2, 160)], 0.0),
    "o":     ("vowel", True,  [(500,  0.9, 50), (900,  0.6, 70), (2500, 0.3, 110), (3500, 0.1, 170)], 0.0),
    "u":     ("vowel", True,  [(300,  0.7, 40), (700,  0.5, 50), (2200, 0.2, 100), (3300, 0.1, 150)], 0.0),
    "y":     ("vowel", True,  [(280,  0.7, 40), (1900, 0.8, 60), (2300, 0.4, 100), (3400, 0.2, 160)], 0.0),
    "eu":    ("vowel", True,  [(400,  0.8, 50), (1500, 0.7, 70), (2300, 0.3, 110), (3400, 0.1, 170)], 0.0),
    "oe":    ("vowel", True,  [(480,  0.8, 55), (1400, 0.6, 75), (2350, 0.3, 115), (3450, 0.1, 175)], 0.0),

    # ── Voyelles nasales ─────────────────────────────────────────────
    "a~":    ("nasal",  True,  [(350, 0.7, 60), (1100, 0.5, 80), (2400, 0.3, 120), (3300, 0.1, 180)], 0.15),
    "e~":    ("nasal",  True,  [(300, 0.7, 55), (1600, 0.5, 80), (2600, 0.3, 120), (3500, 0.1, 180)], 0.15),
    "o~":    ("nasal",  True,  [(400, 0.7, 60), (900,  0.5, 80), (2500, 0.3, 120), (3400, 0.1, 180)], 0.15),
    "oe~":   ("nasal",  True,  [(380, 0.7, 60), (1300, 0.5, 80), (2450, 0.3, 120), (3400, 0.1, 180)], 0.15),

    # ── Semi-voyelles ────────────────────────────────────────────────
    "w":     ("vowel", True,  [(300, 0.5, 40), (700,  0.4, 60),  (2300, 0.2, 100), (3100, 0.1, 140)], 0.0),
    "yod":   ("vowel", True,  [(280, 0.5, 40), (2100, 0.5, 60),  (3000, 0.2, 100), (3700, 0.1, 150)], 0.0),
    "ui":    ("vowel", True,  [(290, 0.5, 42), (1850, 0.5, 62),  (2350, 0.2, 102), (3400, 0.1, 155)], 0.0),

    # ── Occlusives ───────────────────────────────────────────────────
    "p":     ("stop", False, [(400, 0.2, 200), (1200, 0.3, 300)], 0.6),
    "b":     ("stop", True,  [(400, 0.4, 200), (1200, 0.3, 300)], 0.2),
    "t":     ("stop", False, [(400, 0.2, 200), (2000, 0.3, 300)], 0.6),
    "d":     ("stop", True,  [(400, 0.4, 200), (2000, 0.3, 300)], 0.2),
    "k":     ("stop", False, [(400, 0.2, 200), (1500, 0.3, 350)], 0.6),
    "g":     ("stop", True,  [(400, 0.4, 200), (1500, 0.3, 350)], 0.2),

    # ── Fricatives ───────────────────────────────────────────────────
    "f":     ("fricative", False, [(400, 0.1, 400), (2000, 0.2, 500)], 1.2),
    "v":     ("fricative", True,  [(400, 0.3, 300), (1500, 0.2, 400)], 0.7),
    "s":     ("fricative", False, [(400, 0.1, 600), (3500, 0.3, 600)], 1.5),
    "z":     ("fricative", True,  [(400, 0.3, 400), (3000, 0.2, 500)], 0.8),
    "ss":    ("fricative", False, [(400, 0.1, 550), (3200, 0.2, 550)], 1.4),
    "ch":    ("fricative", False, [(400, 0.1, 400), (2500, 0.3, 500)], 1.3),
    "j":     ("fricative", True,  [(400, 0.3, 300), (2200, 0.2, 400)], 0.8),

    # ── Liquides ─────────────────────────────────────────────────────
    "l":     ("liquid",  True,  [(350, 0.6, 60),  (1200, 0.3, 100), (2600, 0.2, 150)], 0.1),
    "r":     ("liquid",  True,  [(400, 0.5, 100), (1300, 0.3, 150), (2400, 0.4, 200)], 0.3),

    # ── Nasales ──────────────────────────────────────────────────────
    "m":     ("nasal",   True,  [(280, 0.6, 40),  (1000, 0.2, 100), (2400, 0.1, 200)], 0.0),
    "n":     ("nasal",   True,  [(280, 0.6, 40),  (1700, 0.2, 100), (2600, 0.1, 200)], 0.0),
    "gn":    ("nasal",   True,  [(300, 0.5, 50),  (2000, 0.2, 120), (2700, 0.1, 200)], 0.1),

    # ── Silence ──────────────────────────────────────────────────────
    "_":     ("silence", False, [], 0.0),
}

# Durées par type de phonème (secondes)
PHONEME_DURATIONS = {
    "vowel": 0.130, "nasal": 0.140, "fricative": 0.100,
    "stop": 0.080, "liquid": 0.090, "silence": 0.060,
}


def _glottal_pulse_train(n_samples: int, f0_hz: float, sr: int) -> np.ndarray:
    """Génère un train d'impulsions glottales (modèle LF simplifié)."""
    if f0_hz <= 0:
        return np.zeros(n_samples, dtype=np.float64)
    period = max(2, int(sr / f0_hz))
    # Une période : montée sinusoïdale + descente exponentielle
    pulse = np.zeros(period, dtype=np.float64)
    open_len = int(period * 0.55)
    t = np.linspace(0, np.pi, open_len)
    pulse[:open_len] = np.sin(t)
    decay_len = period - open_len
    if decay_len > 0:
        pulse[open_len:] = np.exp(-3 * np.linspace(0, 1, decay_len))
    n_periods = n_samples // period + 1
    return np.tile(pulse, n_periods)[:n_samples]


def synthesize_phoneme(
    phoneme: str,
    duration_s: float = 0.120,
    f0_hz: float = 120.0,
    f0_delta: float = 0.0,
    sr: int = SAMPLE_RATE,
) -> np.ndarray:
    """Synthétise un phonème isolé — garanti audible.

    Modèle source-filtre : pulse glottale + bruit → filtres formantiques.
    """
    from scipy import signal as scipy_signal

    n = max(1, int(duration_s * sr))

    # Résoudre le phonème
    key = phoneme.lower().strip()
    if key not in PHONEME_DEFS:
        for k in PHONEME_DEFS:
            if k in key or key in k:
                key = k
                break
        else:
            key = "a"

    ptype, voiced, formants, noise_gain = PHONEME_DEFS[key]

    if ptype == "silence":
        return np.zeros(n, dtype=np.float32)

    # ── Source ────────────────────────────────────────────────────────
    source = np.zeros(n, dtype=np.float64)

    # Source glottale
    if voiced and f0_hz > 0:
        f0_effective = f0_hz + f0_delta
        source += _glottal_pulse_train(n, f0_effective, sr) * 0.7

    # Bruit (toujours présent, dominant pour fricatives/stops)
    rng = np.random.RandomState(abs(hash(phoneme + str(duration_s))) % (2**31))
    noise = rng.normal(0, 1, n).astype(np.float64)
    # Colorer le bruit (passe-bande 300-4500 Hz)
    try:
        b_bp, a_bp = scipy_signal.butter(2, [300/(sr/2), 4500/(sr/2)], btype="band")
        noise = scipy_signal.lfilter(b_bp, a_bp, noise)
    except Exception:
        pass
    eff_noise = noise_gain if noise_gain > 0 else (0.1 if not voiced else 0.02)
    source += noise * eff_noise

    # Normaliser la source
    src_max = np.max(np.abs(source)) + 1e-10
    source /= src_max

    # ── Filtres formantiques (cascade) ─────────────────────────────────
    out = source.copy()
    for freq, amp, bw in formants:
        if freq <= 0 or freq >= sr / 2.1:
            continue
        Q = max(0.5, freq / max(bw, 10))
        try:
            b, a = scipy_signal.iirpeak(freq, Q, sr)
            filtered = scipy_signal.lfilter(b, a, out)
            out = out * (1.0 - amp * 0.4) + filtered * amp * 0.4
        except Exception:
            pass

    # ── Enveloppe ─────────────────────────────────────────────────────
    attack = min(int(0.008 * sr), n // 3)
    decay = min(int(0.015 * sr), n // 3)
    env = np.ones(n, dtype=np.float64)
    if attack > 1:
        env[:attack] = np.linspace(0, 1, attack) ** 2
    if decay > 1:
        env[-decay:] = np.linspace(1, 0, decay) ** 2
    out *= env

    # Supprimer DC offset
    out = out - np.mean(out)

    # Normalisation finale
    peak = np.max(np.abs(out)) + 1e-10
    return (out / peak * 0.95).astype(np.float32)


# ═══════════════════════════════════════════════════════════════════════════════
# PROSODIE — intonation, accentuation, variation F0
# ═══════════════════════════════════════════════════════════════════════════════

def _compute_prosody(
    phonemes: list[str],
    base_f0: float,
    speed: float,
) -> list[tuple[float, float]]:
    """Calcule (durée, f0) pour chaque phonème selon la prosodie française.

    Règles :
      - Phrase déclarative : F0 descend en fin de phrase
      - Phrase interrogative : F0 monte en fin de phrase
      - Accent de groupe : dernière syllabe allongée + F0 modulée
      - Ponctuation : pause après . ! ?
    """
    n = len(phonemes)
    if n == 0:
        return []

    prosody: list[tuple[float, float]] = []

    for i, ph in enumerate(phonemes):
        # Position normalisée dans la phrase
        pos = i / max(n - 1, 1)

        # Durée de base selon le type
        ptype = PHONEME_DEFS.get(ph, ("vowel", True, [], 0))[0]
        dur = PHONEME_DURATIONS.get(ptype, 0.120)

        # Accent de groupe : allonger la dernière syllabe avant pause
        is_before_pause = (i < n - 1 and phonemes[i + 1] == "_") or (i == n - 1)
        is_vowel = ptype in ("vowel", "nasal")
        if is_before_pause and is_vowel:
            dur *= 1.5  # +50% durée sur l'accent final

        # Pause : durée fixe
        if ph == "_":
            dur = 0.080  # pause courte par défaut

        # Vitesse
        dur /= max(speed, 0.25)

        # F0 : contour déclaratif (descente en fin de phrase)
        if pos < 0.6:
            f0_mod = 1.0
        elif pos < 0.85:
            f0_mod = 1.0 - (pos - 0.6) * 0.4  # légère descente
        else:
            f0_mod = 0.85 - (pos - 0.85) * 0.3  # descente finale

        # Micro-variations : vibrato léger sur les voyelles longues
        if is_vowel and dur > 0.12:
            f0_mod += 0.02 * math.sin(pos * 17.0)

        f0 = base_f0 * f0_mod

        # Ponctuation forte → pause longue
        if ph == "_" and i > 0 and phonemes[i - 1] in ".!?":
            dur = 0.250

        prosody.append((dur, f0))

    return prosody


# ═══════════════════════════════════════════════════════════════════════════════
# SYNTHÈSE DE PHRASES
# ═══════════════════════════════════════════════════════════════════════════════

def speak(
    text: str,
    f0_hz: float = 120.0,
    speed: float = 1.0,
    sr: int = SAMPLE_RATE,
) -> np.ndarray:
    """Synthèse vocale : texte → audio avec vibrato naturel et transitions."""
    from scipy import signal as scipy_signal

    phonemes = text_to_phonemes(text)
    if not phonemes:
        return np.zeros(int(0.3 * sr), dtype=np.float32)

    prosody = _compute_prosody(phonemes, f0_hz, speed)
    rng = np.random.RandomState(abs(hash(text)) % (2**31))

    # Synthétiser chaque phonème avec F0 vibrato
    fragments = []
    for i, (ph, (dur, f0_base)) in enumerate(zip(phonemes, prosody)):
        # Vibrato sinusoïdal
        n_ph = max(1, int(dur * sr))
        t = np.arange(n_ph) / sr
        vibrato = 1.0 + 0.025 * np.sin(2 * np.pi * 5.3 * t + i * 0.8)
        jitter = 1.0 + rng.uniform(-0.008, 0.008, n_ph)
        f0_contour = f0_base * vibrato * jitter
        
        # Générer avec F0 variable
        audio = synthesize_phoneme_variable_f0(ph, dur, f0_contour, sr, rng)
        fragments.append(audio)

    if len(fragments) == 1:
        return fragments[0]

    # Crossfade léger (5ms au lieu de 12ms)
    ov = int(0.005 * sr)
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

    # DC removal
    result = result - np.mean(result)
    try:
        b_hp, a_hp = scipy_signal.butter(2, 80/(sr/2), btype='high')
        result = scipy_signal.lfilter(b_hp, a_hp, result)
    except Exception:
        pass

    peak = np.max(np.abs(result)) + 1e-10
    return (result / peak * 0.95).astype(np.float32)


def synthesize_phoneme_variable_f0(
    phoneme: str,
    duration_s: float,
    f0_contour: np.ndarray,
    sr: int,
    rng: np.random.RandomState,
) -> np.ndarray:
    """Synthétise un phonème avec F0 variable (vibrato naturel)."""
    from scipy import signal as scipy_signal

    n = len(f0_contour)

    # Résoudre le phonème
    key = phoneme.lower().strip()
    if key not in PHONEME_DEFS:
        for k in PHONEME_DEFS:
            if k in key or key in k:
                key = k
                break
        else:
            key = "a"

    ptype, voiced, formants, noise_gain = PHONEME_DEFS[key]

    if ptype == "silence":
        return np.zeros(n, dtype=np.float32)

    # ── Source glottale à F0 variable ───────────────────────────────
    source = np.zeros(n, dtype=np.float64)

    if voiced:
        # Construire le pulse train avec F0 variable
        phase = 0.0
        for i in range(n):
            f0 = max(1.0, f0_contour[i])
            phase += f0 / sr
            if phase >= 1.0:
                phase -= 1.0
                # Impulsion glottale brève (3ms)
                pulse_len = min(int(0.003 * sr), n - i)
                if pulse_len > 0:
                    t_pulse = np.linspace(0, np.pi, pulse_len)
                    source[i:i + pulse_len] += np.sin(t_pulse) * 0.7

    # Bruit de souffle
    noise_amp = noise_gain if noise_gain > 0 else (0.04 if not voiced else 0.015)
    noise = rng.normal(0, noise_amp, n)
    # Colorer le bruit
    try:
        b_bp, a_bp = scipy_signal.butter(2, [300/(sr/2), 4500/(sr/2)], btype="band")
        noise = scipy_signal.lfilter(b_bp, a_bp, noise)
    except Exception:
        pass
    source += noise

    src_max = np.max(np.abs(source)) + 1e-10
    source /= src_max

    # ── Filtres formantiques fixes (plus propres que l'interpolation) ──
    out = source.copy()
    for freq, amp, bw in formants:
        if freq <= 0 or freq >= sr / 2.1:
            continue
        Q = max(0.5, freq / max(bw, 10))
        try:
            b, a = scipy_signal.iirpeak(freq, Q, sr)
            filtered = scipy_signal.lfilter(b, a, out)
            out = out * (1.0 - amp * 0.4) + filtered * amp * 0.4
        except Exception:
            pass

    # ── Enveloppe douce ────────────────────────────────────────────
    attack = min(int(0.006 * sr), n // 4)
    decay = min(int(0.010 * sr), n // 4)
    env = np.ones(n, dtype=np.float64)
    if attack > 1:
        env[:attack] = np.linspace(0, 1, attack) ** 2
    if decay > 1:
        env[-decay:] = np.linspace(1, 0, decay) ** 2
    out *= env

    out = out - np.mean(out)
    peak = np.max(np.abs(out)) + 1e-10
    return (out / peak * 0.95).astype(np.float32)


# ═══════════════════════════════════════════════════════════════════════════════
# CLONAGE — extraction + application d'enveloppe spectrale
# ═══════════════════════════════════════════════════════════════════════════════

def extract_voice_print(audio: np.ndarray, sr: int = SAMPLE_RATE) -> Optional[np.ndarray]:
    """Extrait l'enveloppe spectrale moyenne d'un enregistrement vocal."""
    frame_len = int(0.025 * sr)
    hop_len = frame_len // 2
    n_fft = 512

    envelopes: list[np.ndarray] = []
    for start in range(0, len(audio) - frame_len, hop_len):
        frame = audio[start:start + frame_len] * np.hanning(frame_len)
        spec = np.abs(np.fft.rfft(frame, n=n_fft))
        if np.sum(spec) > 1e-6:
            envelopes.append(spec / (np.max(spec) + 1e-10))

    if not envelopes:
        return None

    envelope = np.mean(envelopes, axis=0)

    # Lissage φ bidirectionnel
    alpha = 0.618
    for i in range(1, len(envelope)):
        envelope[i] = alpha * envelope[i] + (1.0 - alpha) * envelope[i - 1]
    for i in range(len(envelope) - 2, -1, -1):
        envelope[i] = alpha * envelope[i] + (1.0 - alpha) * envelope[i + 1]

    return envelope.astype(np.float32)


def apply_voice_print(
    audio: np.ndarray,
    voice_print: np.ndarray,
    sr: int = SAMPLE_RATE,
) -> np.ndarray:
    """Applique une enveloppe spectrale clonée à un signal audio.

    Overlap-add : chaque trame voit sa magnitude remplacée par l'enveloppe
    clonée (blend 70% clone / 30% original), phase préservée.
    """
    n_fft = 512
    hop = n_fft // 4
    n_frames = max(1, (len(audio) - n_fft) // hop + 1)

    output = np.zeros(len(audio), dtype=np.float64)
    weight = np.zeros(len(audio), dtype=np.float64)
    win = np.hanning(n_fft).astype(np.float64)

    voice_print = np.asarray(voice_print, dtype=np.float64)
    if len(voice_print) != n_fft // 2 + 1:
        # Resizer l'enveloppe
        old_len = len(voice_print)
        voice_print = np.interp(
            np.linspace(0, old_len - 1, n_fft // 2 + 1),
            np.arange(old_len),
            voice_print,
        )

    for i in range(n_frames):
        start = i * hop
        if start + n_fft > len(audio):
            break
        frame = audio[start:start + n_fft] * win
        spec = np.fft.rfft(frame)
        mag = np.abs(spec)
        phase = np.angle(spec)

        # Blend : 70% enveloppe clonée, 30% magnitude originale
        new_mag = voice_print * np.mean(mag) * 1.5 * 0.7 + mag * 0.3
        new_spec = new_mag * (np.cos(phase) + 1j * np.sin(phase))
        new_frame = np.fft.irfft(new_spec, n=n_fft)

        output[start:start + n_fft] += new_frame * win
        weight[start:start + n_fft] += win ** 2

    weight[weight < 1e-6] = 1.0
    result = output / weight
    peak = np.max(np.abs(result)) + 1e-10
    return (result / peak * 0.95).astype(np.float32)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN — Interface en ligne de commande
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    p = argparse.ArgumentParser(
        description="KA TTS v2 — Synthèse vocale paramétrique français",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python tts_engine.py "Bonjour le monde"
  python tts_engine.py "Texte" --f0 180 --speed 0.9
  python tts_engine.py --test
  python tts_engine.py --record 30 --out voix.wav
  python tts_engine.py --clone voix.wav "Texte avec ma voix"
  python tts_engine.py --play fichier.wav
  python tts_engine.py --devices
        """,
    )
    p.add_argument("text", nargs="*", help="Texte à synthétiser")
    p.add_argument("--test", action="store_true", help="Test audio bip + sweep")
    p.add_argument("--devices", action="store_true", help="Lister les périphériques audio")
    p.add_argument("--play", type=str, help="Jouer un fichier WAV existant")
    p.add_argument("--record", type=float, default=0.0, help="Enregistrer N secondes depuis le micro")
    p.add_argument("--clone", type=str, help="Cloner un WAV de référence, puis synthétiser")
    p.add_argument("--f0", type=float, default=120.0, help="Fréquence fondamentale Hz (défaut: 120)")
    p.add_argument("--speed", type=float, default=1.0, help="Vitesse (défaut: 1.0)")
    p.add_argument("--out", type=str, default="output.wav", help="Fichier WAV de sortie")
    p.add_argument("--no-play", action="store_true", help="Ne pas jouer le son après synthèse")
    args = p.parse_args()

    # ── Commandes spéciales ──────────────────────────────────────────
    if args.devices:
        list_devices()
        return

    if args.test:
        test_audio()
        return

    if args.play:
        play_wav(args.play)
        return

    # ── Enregistrement micro ─────────────────────────────────────────
    if args.record > 0:
        result = record_mic(args.record)
        if result is not None:
            audio, sr = result
            path = args.out or f"record_{int(time.time())}.wav"
            save_wav(audio, path, sr)
            print(f"💾 Sauvegardé: {path}")
        return

    # ── Clonage + synthèse ───────────────────────────────────────────
    if args.clone:
        if not os.path.exists(args.clone):
            print(f"❌ Fichier introuvable: {args.clone}")
            return
        text = " ".join(args.text) if args.text else "Bonjour, je suis une voix clonée."

        # Charger la référence
        with wave.open(args.clone, "rb") as w:
            ref_sr = w.getframerate()
            ref_n = w.getnframes()
            ref_pcm = np.frombuffer(w.readframes(ref_n), dtype="<i2")
        ref_audio = ref_pcm.astype(np.float32) / 32767.0

        print(f"🎭 Clonage depuis: {args.clone} ({ref_n/ref_sr:.1f}s)")

        # Extraire l'empreinte vocale
        vp = extract_voice_print(ref_audio, ref_sr)
        if vp is None:
            print("❌ Échec extraction — fichier trop court ou silencieux")
            return

        # Synthèse de base (voix neutre)
        print(f"🎙️  Synthèse: \"{text[:80]}{'...' if len(text)>80 else ''}\"")
        base_audio = speak(text, f0_hz=args.f0, speed=args.speed)

        # Appliquer l'empreinte
        cloned = apply_voice_print(base_audio, vp)

        path = save_wav(cloned, args.out)
        dur = len(cloned) / SAMPLE_RATE
        print(f"   → {dur:.1f}s, {os.path.getsize(path)} octets")
        print(f"   💾 {path}")

        if not args.no_play:
            play_wav(path)
        return

    # ── Synthèse standard ────────────────────────────────────────────
    text = " ".join(args.text) if args.text else "Bonjour le monde. Ceci est un test de synthese vocale."

    print(f"🎙️  Synthèse: \"{text[:80]}{'...' if len(text)>80 else ''}\"")
    print(f"   F0: {args.f0:.0f} Hz | Vitesse: {args.speed:.1f}x")

    t0 = time.perf_counter()
    audio = speak(text, f0_hz=args.f0, speed=args.speed)
    elapsed = (time.perf_counter() - t0) * 1000

    path = save_wav(audio, args.out)
    dur = len(audio) / SAMPLE_RATE
    print(f"   → {dur:.1f}s, {elapsed:.0f}ms, {os.path.getsize(path)} octets")
    print(f"   💾 {path}")

    if not args.no_play:
        play_wav(path)


if __name__ == "__main__":
    main()
