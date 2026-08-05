"""
Table de features articulatoires pour les 36 phonèmes du français.

Chaque phonème est représenté par un vecteur de 10 features binaires ou
graduées (0.0 à 1.0). Ces features sont utilisées par le SymbolicEncoder
pour construire un vecteur ψ ∈ ℂ⁵¹² qui préserve la proximité phonétique :
deux phonèmes partageant des features ont un produit scalaire élevé.

Features :
  0. voisé        (0/1)   — vibration des cordes vocales
  1. nasal         (0/1)   — résonance nasale
  2. arrondi       (0/1)   — lèvres arrondies
  3. continu       (0/1)   — flux d'air continu (fricatives, voyelles)
  4. antérieur     (0..1)  — lieu d'articulation avant (1) à arrière (0)
  5. ouvert        (0..1)  — degré d'ouverture (fermé=0, ouvert=1)
  6. F1_normalisé  (0..1)  — premier formant normalisé (corrélé à l'ouverture)
  7. F2_normalisé  (0..1)  — deuxième formant normalisé (corrélé à l'antériorité)
  8. mode          (0..1)  — mode d'articulation (0=occlusif, 0.5=fricatif, 1=voyelle)
  9. latéral/rhot  (0/1)   — spécifique liquides (l, r)
"""

from typing import Dict, Tuple, List

# ═══════════════════════════════════════════════════════════════════════════════
# Table de features — 36 phonèmes français
# ═══════════════════════════════════════════════════════════════════════════════

PHONEME_FEATURES: Dict[str, Tuple[float, ...]] = {
    # ── Voyelles orales ──────────────────────────────────────────────────
    "a":  (1, 0, 0, 1, 0.3, 1.0, 0.90, 0.55, 1.0, 0),   # ouvert antérieur non-arrondi
    "ɑ":  (1, 0, 0, 1, 0.1, 0.9, 0.85, 0.40, 1.0, 0),   # ouvert postérieur
    "ə":  (1, 0, 0, 1, 0.5, 0.5, 0.50, 0.50, 1.0, 0),   # schwa (moyen central)
    "ø":  (1, 0, 1, 1, 0.6, 0.4, 0.40, 0.65, 1.0, 0),   # fermé antérieur arrondi (eu)
    "œ":  (1, 0, 1, 1, 0.5, 0.6, 0.55, 0.60, 1.0, 0),   # ouvert antérieur arrondi
    "ɛ":  (1, 0, 0, 1, 0.6, 0.7, 0.60, 0.70, 1.0, 0),   # ouvert antérieur non-arrondi (è)
    "e":  (1, 0, 0, 1, 0.7, 0.3, 0.35, 0.80, 1.0, 0),   # fermé antérieur non-arrondi (é)
    "i":  (1, 0, 0, 1, 0.9, 0.1, 0.25, 0.90, 1.0, 0),   # fermé antérieur non-arrondi
    "o":  (1, 0, 1, 1, 0.2, 0.4, 0.40, 0.35, 1.0, 0),   # fermé postérieur arrondi
    "ɔ":  (1, 0, 1, 1, 0.2, 0.7, 0.60, 0.35, 1.0, 0),   # ouvert postérieur arrondi (o ouvert)
    "u":  (1, 0, 1, 1, 0.1, 0.1, 0.25, 0.20, 1.0, 0),   # fermé postérieur arrondi (ou)
    "y":  (1, 0, 1, 1, 0.8, 0.1, 0.25, 0.85, 1.0, 0),   # fermé antérieur arrondi (u)

    # ── Voyelles nasales ─────────────────────────────────────────────────
    "ɑ̃": (1, 1, 0, 1, 0.2, 0.8, 0.80, 0.40, 1.0, 0),   # an/en
    "ɛ̃": (1, 1, 0, 1, 0.6, 0.6, 0.55, 0.70, 1.0, 0),   # in/ain
    "ɔ̃": (1, 1, 1, 1, 0.2, 0.6, 0.55, 0.35, 1.0, 0),   # on
    "œ̃": (1, 1, 1, 1, 0.5, 0.5, 0.50, 0.60, 1.0, 0),   # un (rare, tendance vers ɛ̃)

    # ── Semi-voyelles ────────────────────────────────────────────────────
    "j":  (1, 0, 0, 1, 0.9, 0.05, 0.22, 0.92, 0.85, 0),  # yod (i consonne)
    "w":  (1, 0, 1, 1, 0.1, 0.05, 0.22, 0.18, 0.85, 0),  # w (ou consonne)
    "ɥ":  (1, 0, 1, 1, 0.8, 0.05, 0.22, 0.87, 0.85, 0),  # u consonne (huit)

    # ── Occlusives ───────────────────────────────────────────────────────
    "p":  (0, 0, 0, 0, 1.0, 0.0, 0.15, 0.30, 0.0, 0),   # bilabiale sourde
    "b":  (1, 0, 0, 0, 1.0, 0.0, 0.15, 0.30, 0.0, 0),   # bilabiale voisée
    "t":  (0, 0, 0, 0, 0.8, 0.0, 0.15, 0.70, 0.0, 0),   # dentale sourde
    "d":  (1, 0, 0, 0, 0.8, 0.0, 0.15, 0.70, 0.0, 0),   # dentale voisée
    "k":  (0, 0, 0, 0, 0.2, 0.0, 0.15, 0.45, 0.0, 0),   # vélaire sourde
    "ɡ":  (1, 0, 0, 0, 0.2, 0.0, 0.15, 0.45, 0.0, 0),   # vélaire voisée (g dur)

    # ── Fricatives ───────────────────────────────────────────────────────
    "f":  (0, 0, 0, 1, 1.0, 0.0, 0.15, 0.25, 0.5, 0),   # labiodentale sourde
    "v":  (1, 0, 0, 1, 1.0, 0.0, 0.15, 0.25, 0.5, 0),   # labiodentale voisée
    "s":  (0, 0, 0, 1, 0.8, 0.0, 0.15, 0.80, 0.5, 0),   # alvéolaire sourde
    "z":  (1, 0, 0, 1, 0.8, 0.0, 0.15, 0.80, 0.5, 0),   # alvéolaire voisée
    "ʃ":  (0, 0, 1, 1, 0.5, 0.0, 0.15, 0.55, 0.5, 0),   # post-alvéolaire sourde (ch)
    "ʒ":  (1, 0, 1, 1, 0.5, 0.0, 0.15, 0.55, 0.5, 0),   # post-alvéolaire voisée (j)

    # ── Nasales ──────────────────────────────────────────────────────────
    "m":  (1, 1, 0, 0, 1.0, 0.0, 0.15, 0.25, 0.0, 0),   # bilabiale nasale
    "n":  (1, 1, 0, 0, 0.8, 0.0, 0.15, 0.70, 0.0, 0),   # dentale nasale
    "ɲ":  (1, 1, 0, 0, 0.6, 0.0, 0.15, 0.65, 0.0, 0),   # palatale nasale (gn)

    # ── Liquides ─────────────────────────────────────────────────────────
    "l":  (1, 0, 0, 1, 0.8, 0.0, 0.15, 0.65, 0.3, 1),   # latérale
    "ʁ":  (1, 0, 0, 1, 0.2, 0.0, 0.15, 0.40, 0.3, 1),   # rhotique (r français moderne)

    # ── Pauses et silence ────────────────────────────────────────────────
    "_":  (0, 0, 0, 0, 0.5, 0.0, 0.05, 0.05, 0.0, 0),   # silence/pause
    "#":  (0, 0, 0, 0, 0.5, 0.0, 0.05, 0.05, 0.0, 0),   # frontière de mot
}

# ═══════════════════════════════════════════════════════════════════════════════
# Regroupement phonétiques (classes naturelles)
# ═══════════════════════════════════════════════════════════════════════════════

VOYELLES = {"a", "ɑ", "ə", "ø", "œ", "ɛ", "e", "i", "o", "ɔ", "u", "y",
            "ɑ̃", "ɛ̃", "ɔ̃", "œ̃"}
SEMI_VOYELLES = {"j", "w", "ɥ"}
OCCLUSIVES = {"p", "b", "t", "d", "k", "ɡ"}
FRICATIVES = {"f", "v", "s", "z", "ʃ", "ʒ"}
NASALES = {"m", "n", "ɲ"}
LIQUIDES = {"l", "ʁ"}
VOISEES = {p for p, f in PHONEME_FEATURES.items() if f[0] == 1}
NON_VOISEES = {p for p in PHONEME_FEATURES if p not in VOISEES}

# ═══════════════════════════════════════════════════════════════════════════════
# G2P simplifié — règles de phonémisation français (fallback sans espeak-ng)
# ═══════════════════════════════════════════════════════════════════════════════

# Mapping graphème → phonème pour les cas réguliers
GRAPHEME_TO_PHONEME: Dict[str, str] = {
    # Voyelles
    "a": "a", "à": "a", "â": "ɑ",
    "e": "ə", "é": "e", "è": "ɛ", "ê": "ɛ", "ë": "ɛ",
    "i": "i", "î": "i", "ï": "i",
    "o": "ɔ", "ô": "o",
    "u": "y", "ù": "u", "û": "y", "ü": "y",
    "ou": "u", "où": "u", "oû": "u",
    "eu": "ø", "œu": "œ",
    "ai": "ɛ", "ei": "ɛ", "et": "ɛ",  # en fin de mot
    "au": "o", "eau": "o",
    "oi": "wa",  # semi-voyelle + voyelle
    "oin": "wɛ̃",

    # Nasales
    "an": "ɑ̃", "am": "ɑ̃", "en": "ɑ̃", "em": "ɑ̃",
    "in": "ɛ̃", "im": "ɛ̃", "ain": "ɛ̃", "aim": "ɛ̃", "ein": "ɛ̃",
    "on": "ɔ̃", "om": "ɔ̃",
    "un": "œ̃", "um": "œ̃",

    # Consonnes
    "b": "b", "c": "k", "ç": "s",
    "d": "d",
    "f": "f", "ph": "f",
    "g": "ɡ", "gu": "ɡ",
    "j": "ʒ",
    "k": "k",
    "l": "l", "ll": "j",  # sauf ville, mille...
    "m": "m",
    "n": "n",
    "p": "p",
    "qu": "k",
    "r": "ʁ",
    "s": "s", "ss": "s",
    "t": "t", "th": "t",
    "v": "v", "w": "w",
    "x": "ks",
    "z": "z",

    # Digrammes
    "ch": "ʃ",
    "gn": "ɲ",
    "ill": "j",
    "tion": "sjɔ̃",

    # Liaisons fréquentes (pour G2P contextuel)
    "les": "lez",
    "des": "dez",
    "mes": "mez",
    "tes": "tez",
    "ses": "sez",
    "ces": "sez",
    "nos": "noz",
    "vos": "voz",
    "leurs": "lœʁz",
    "aux": "oz",
}


def phoneme_distance(p1: str, p2: str) -> float:
    """Distance euclidienne entre deux phonèmes dans l'espace des features."""
    f1 = PHONEME_FEATURES.get(p1)
    f2 = PHONEME_FEATURES.get(p2)
    if f1 is None or f2 is None:
        return 1.0  # distance maximale si phonème inconnu
    # Distance euclidienne normalisée sur 10 dimensions
    d2 = sum((a - b) ** 2 for a, b in zip(f1, f2))
    return min(1.0, (d2 / 10.0) ** 0.5)


def phoneme_similarity(p1: str, p2: str) -> float:
    """Similarité cosinus entre deux phonèmes (1.0 = identique, 0.0 = orthogonal)."""
    return 1.0 - phoneme_distance(p1, p2)
