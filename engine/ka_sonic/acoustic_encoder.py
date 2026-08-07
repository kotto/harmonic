"""
AcousticEncoder — Couche acoustique en ℝ¹⁶⁻²⁴.

Cette couche gère :
  - Extraction de features acoustiques réelles pour chaque diphone
  - Projection d'un phonème vers des features acoustiques cibles (règles)
  - Recherche KD-tree du meilleur diphone dans la banque

ESPACE ACOUSTIQUE (16 dimensions) :
  dim  0 : f0_log           — log(F0) normalisé [0..1]  (pitch)
  dim  1 : delta_f0         — variation F0 sur le diphone [0..1]
  dim  2 : energy           — RMS normalisé [0..1]
  dim  3 : duration         — durée normalisée [0..1]  (100ms = 0.5)
  dim  4-7 : F1, F2, F3, F4  — formants normalisés (Bark scale → [0..1])
  dim  8 : centroid         — centroïde spectral normalisé [0..1]
  dim  9 : harmonicity      — ratio harmonique/bruit [0..1]
  dim 10 : zcr              — zero-crossing rate normalisé [0..1]
  dim 11 : voicing          — voisé? [0/1]
  dim 12-13 : ctx_left_onehot — phonème gauche encodé
  dim 14-15 : ctx_right_onehot — phonème droit encodé

Le KD-tree indexe les diphones de la banque sur ces 16 dimensions.
La recherche utilise une distance de Mahalanobis diagonale (poids par dim).

Zéro dépendance externe : numpy + scipy (spatial.KDTree).
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

from .phoneme_features import PHONEME_FEATURES, VOYELLES, OCCLUSIVES, FRICATIVES, LIQUIDES

# ═══════════════════════════════════════════════════════════════════════════════
# Constantes
# ═══════════════════════════════════════════════════════════════════════════════

ACOUSTIC_DIM = 16  # Dimension de l'espace acoustique (features réelles)
DEFAULT_SAMPLE_RATE = 22050
DEFAULT_F0_REF = 100.0   # Hz de référence pour log_F0
DEFAULT_F0_MAX = 400.0   # Hz max pour normalisation


# ═══════════════════════════════════════════════════════════════════════════════
# Règles de projection : phonème → features acoustiques cibles
# ═══════════════════════════════════════════════════════════════════════════════

def phoneme_to_acoustic_target(phoneme: str, is_vowel: bool = False) -> np.ndarray:
    """Projette un phonème vers ses features acoustiques cibles (règles).
    
    Ces cibles servent à interroger le KD-tree pour trouver le diphone
    le plus proche dans la banque synthétique.
    
    Règles simplifiées basées sur la phonétique articulatoire :
      - Voyelles : F1/F2 depuis features[6-7], F0 ≈ 120 Hz, durée longue
      - Occlusives : burst + silence, F0 = 0 (non voisé) ou 120 (voisé)
      - Fricatives : bruit large bande, durée moyenne, F0 = 0 ou 120
      - Liquides : formants + voisé, durée moyenne-longue
    """
    features = PHONEME_FEATURES.get(phoneme)
    if features is None:
        # Fallback : phonème inconnu → valeurs neutres
        return np.full(ACOUSTIC_DIM, 0.5, dtype=np.float32)

    voise = features[0]   # 0=non-voisé, 1=voisé
    nasal = features[1]
    arrondi = features[2]
    ant = features[4]     # 0=postérieur, 1=antérieur
    ouvert = features[5]  # 0=fermé, 1=ouvert
    F1_norm = features[6]
    F2_norm = features[7]
    mode = features[8]    # 0=occlusif, 0.5=fricatif, 1=voyelle

    target = np.zeros(ACOUSTIC_DIM, dtype=np.float32)

    # F0 : dépend du voisement et du mode
    if voise:
        # Voyelles : F0 ~120 Hz, consonnes voisées : F0 ~100 Hz
        f0_hz = 120.0 if mode > 0.5 else 100.0
        f0_log = math.log(f0_hz / DEFAULT_F0_REF) / math.log(DEFAULT_F0_MAX / DEFAULT_F0_REF)
        target[0] = np.clip(f0_log, 0.0, 1.0)
    else:
        target[0] = 0.0  # non voisé → pas de F0

    # Delta F0 (variation) : voyelles ont un contour, consonnes stable
    target[1] = 0.15 if mode > 0.5 else 0.05

    # Énergie : voyelles fortes, fricatives moyennes, occlusives faibles
    if mode >= 1.0:
        target[2] = 0.8
    elif mode >= 0.4:
        target[2] = 0.5
    else:
        target[2] = 0.2

    # Durée (normalisée, 100ms = 0.5)
    if mode >= 1.0:
        target[3] = 0.6   # voyelles ~120ms
    elif mode >= 0.4:
        target[3] = 0.4   # fricatives ~80ms
    else:
        target[3] = 0.25  # occlusives ~50ms

    # Formants F1-F4 (Bark-normalisés)
    # F1 ≈ 300-900 Hz → Bark 3-9 → [0,1]
    # F2 ≈ 700-2500 Hz → Bark 7-15 → [0,1]
    # F3 ≈ 2200-3500 Hz → Bark 15-20 → [0,1]
    # F4 ≈ 3500-5000 Hz → Bark 20-24 → [0,1]
    if mode >= 0.8:  # Voyelles et semi-voyelles
        target[4] = 0.25 + 0.65 * F1_norm     # F1 (corrélé à l'ouverture)
        target[5] = 0.20 + 0.70 * F2_norm      # F2 (corrélé à l'antériorité)
        target[6] = 0.55 + (1.0 - ant) * 0.15  # F3 (antérieur → plus haut)
        target[7] = 0.60 + arrondi * 0.10       # F4 (arrondi → plus bas)
    elif mode >= 0.4:  # Fricatives
        # Fricatives : pas de vrais formants, bruit large bande
        target[4] = 0.2
        target[5] = 0.3 + 0.5 * ant
        target[6] = 0.4
        target[7] = 0.5
    else:  # Occlusives
        target[4] = 0.1
        target[5] = 0.2 + 0.5 * ant  # burst → F2 indicatif du lieu
        target[6] = 0.3
        target[7] = 0.4

    # Centroïde spectral : dépend du mode et du lieu
    if mode >= 0.8:
        target[8] = 0.3 + 0.3 * ant  # antérieur → centroïde plus haut
    elif mode >= 0.4:
        target[8] = 0.6 + 0.2 * ant  # fricatives → centroïde haut
    else:
        target[8] = 0.4

    # Harmonicité : ratio harmonique/bruit
    if mode >= 0.8:
        target[9] = 0.85  # voyelles très harmoniques
    elif voise:
        target[9] = 0.6   # consonnes voisées
    else:
        target[9] = 0.1   # non voisées → bruit

    # ZCR (zero-crossing rate)
    if mode >= 0.8:
        target[10] = 0.2   # voyelles → ZCR bas
    elif mode >= 0.4:
        target[10] = 0.7   # fricatives → ZCR haut
    else:
        target[10] = 0.5

    # Voicing (binaire)
    target[11] = float(voise)

    # Contexte gauche/droite — sera rempli par le KD-tree query
    target[12] = 0.0
    target[13] = 0.0
    target[14] = 0.0
    target[15] = 0.0

    return target.astype(np.float32)


# ═══════════════════════════════════════════════════════════════════════════════
# Poids de Mahalanobis diagonale (importance relative par dimension)
# ═══════════════════════════════════════════════════════════════════════════════

# Poids par défaut : F1/F2/durée les plus importants pour la sélection
_ACOUSTIC_WEIGHTS = np.array([
    0.5,   # f0_log — important mais secondaire (pitch contrôlé post-concat)
    0.2,   # delta_f0
    0.3,   # energy — contrôlé post-concat
    1.0,   # duration — CRITIQUE pour la prosodie
    1.0,   # F1 — très discriminant (ouverture)
    1.0,   # F2 — très discriminant (antériorité)
    0.5,   # F3
    0.3,   # F4
    0.3,   # centroid
    0.3,   # harmonicity
    0.2,   # zcr
    0.5,   # voicing
    0.0,   # ctx_left (rempli au query time)
    0.0,   # ctx_right
    0.0,   # ctx_left
    0.0,   # ctx_right
], dtype=np.float32)

# Normaliser
_ACOUSTIC_WEIGHTS /= np.sum(_ACOUSTIC_WEIGHTS) / ACOUSTIC_DIM


def weighted_distance(a: np.ndarray, b: np.ndarray, weights: np.ndarray = _ACOUSTIC_WEIGHTS) -> float:
    """Distance de Mahalanobis diagonale entre deux vecteurs acoustiques."""
    diff = (a - b) * weights
    return float(np.sqrt(np.sum(diff ** 2)))


# ═══════════════════════════════════════════════════════════════════════════════
# AcousticEncoder — API publique
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AcousticEntry:
    """Un diphone dans la banque acoustique."""
    left: str
    right: str
    features: np.ndarray      # vecteur 16D
    audio: np.ndarray         # samples float32 [-1, 1]
    sample_rate: int = DEFAULT_SAMPLE_RATE

    @property
    def duration_s(self) -> float:
        return len(self.audio) / self.sample_rate


class AcousticEncoder:
    """Couche acoustique — index et recherche de diphones par features réelles.
    
    Usage :
        enc = AcousticEncoder()
        enc.add_diphone("a", "l", features_16d, audio_samples)
        enc.build_index()
        best = enc.query(target_features_16d, k=3)
    """

    def __init__(self, dim: int = ACOUSTIC_DIM):
        self.dim = dim
        self.weights = _ACOUSTIC_WEIGHTS.copy()
        self._entries: List[AcousticEntry] = []
        self._index: Optional[object] = None  # scipy.spatial.KDTree
        self._index_built = False

    def add_diphone(
        self,
        left: str,
        right: str,
        features: np.ndarray,
        audio: np.ndarray,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
    ):
        """Ajoute un diphone à la banque."""
        features = np.asarray(features, dtype=np.float32)
        if len(features) < self.dim:
            features = np.pad(features, (0, self.dim - len(features)))
        elif len(features) > self.dim:
            features = features[:self.dim]
        self._entries.append(AcousticEntry(
            left=left, right=right,
            features=features, audio=audio,
            sample_rate=sample_rate,
        ))
        self._index_built = False

    def build_index(self):
        """Construit le KD-tree sur les features acoustiques."""
        if len(self._entries) == 0:
            return
        try:
            from scipy.spatial import KDTree  # type: ignore
        except ImportError:
            # Fallback : KD-tree maison (linéaire, ok pour <10000 entrées)
            self._index = None
            self._index_built = True
            return

        data = np.array([e.features for e in self._entries], dtype=np.float32)
        # Appliquer les poids avant l'indexation
        weighted_data = data * self.weights
        self._index = KDTree(weighted_data)
        self._index_built = True

    def query(self, target: np.ndarray, k: int = 1) -> List[Tuple[AcousticEntry, float]]:
        """Recherche les k diphones les plus proches de la cible acoustique."""
        target = np.asarray(target, dtype=np.float32)
        if len(target) < self.dim:
            target = np.pad(target, (0, self.dim - len(target)))
        elif len(target) > self.dim:
            target = target[:self.dim]

        if not self._entries:
            return []

        if self._index is not None:
            # KD-tree SciPy
            weighted_target = target * self.weights
            distances, indices = self._index.query(weighted_target, k=min(k, len(self._entries)))
            if k == 1:
                distances = [distances]
                indices = [indices]
            return [(self._entries[int(i)], float(d)) for i, d in zip(indices, distances)]
        else:
            # Fallback linéaire
            scored = []
            for entry in self._entries:
                d = weighted_distance(target, entry.features, self.weights)
                scored.append((entry, d))
            scored.sort(key=lambda x: x[1])
            return scored[:k]

    def __len__(self) -> int:
        return len(self._entries)

    def stats(self) -> dict:
        return {
            "n_entries": len(self._entries),
            "index_built": self._index_built,
            "dim": self.dim,
        }
