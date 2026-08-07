"""
SymbolicEncoder — Couche symbolique VSA/HRR en ℂ⁵¹².

Cette couche gère la composition/décomposition de la structure linguistique :
  - Encodage des phonèmes via features articulatoires → ℂ⁵¹²
  - Binding HRR (convolution circulaire) : diphone = gauche ⊛ droite
  - Unbinding : gauche ≈ diphone ⊛ droite⁻¹
  - Superposition additive : mot = Σ (phonème_i ⊛ POSITION_i)

NE PAS utiliser pour la sélection audio — c'est le rôle de l'AcousticEncoder.
Le binding HRR détruit la structure métrique → "proche dans ℂⁿ" après binding
ne correspond PAS à "acoustiquement proche".

Dépendances : numpy + phoneme_features (table articulatoire).
Aucune dépendance externe (pas de torch, pas d'onnx, pas de ML).
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional

from .phoneme_features import PHONEME_FEATURES, VOYELLES, SEMI_VOYELLES

# ═══════════════════════════════════════════════════════════════════════════════
# Constantes
# ═══════════════════════════════════════════════════════════════════════════════

DIM = 512  # Dimension de l'espace symbolique ℂᵈⁱᵐ
PHI = 1.618033988749895
TAU = 2.0 * math.pi

# Vecteurs de base pour chaque feature articulatoire (10 features → 10 bases)
# Générés une fois via FNV-1a comme seed, reproductibles bit à bit
_BASE_VECTORS: Optional[List[np.ndarray]] = None


# ═══════════════════════════════════════════════════════════════════════════════
# FNV-1a (déterministe, portable)
# ═══════════════════════════════════════════════════════════════════════════════

def fnv1a_64(s: str) -> int:
    """FNV-1a 64-bit hash — déterministe, portable."""
    h = 0xCBF29CE484222325
    for ch in s:
        h ^= ord(ch)
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h


def _init_base_vectors():
    """Initialise les 10 vecteurs de base ℂ⁵¹² (un par feature articulatoire).
    
    Chaque base est un vecteur complexe unitaire généré déterministiquement
    via FNV-1a + φ-spacing. Appelé une seule fois au premier usage.
    """
    global _BASE_VECTORS
    if _BASE_VECTORS is not None:
        return

    _BASE_VECTORS = []
    for feat_idx in range(10):
        seed = fnv1a_64(f"phoneme_feature_{feat_idx}")
        base = np.zeros(DIM, dtype=np.complex128)
        for d in range(DIM):
            phase = ((seed >> (d % 32)) ^ (d * 2654435761)) % 2147483647
            phase = (phase * PHI) % TAU
            base[d] = math.cos(phase) + 1j * math.sin(phase)
        # Normalisation L2
        base /= np.sqrt(np.sum(np.abs(base) ** 2))
        _BASE_VECTORS.append(base)


# ═══════════════════════════════════════════════════════════════════════════════
# Encoding des phonèmes par features articulatoires
# ═══════════════════════════════════════════════════════════════════════════════

def encode_phoneme(phoneme: str) -> np.ndarray:
    """Encode un phonème en ψ ∈ ℂ⁵¹² via ses features articulatoires.
    
    Principe : ψ = Σ (feature_i × base_i), normalisé.
    Deux phonèmes partageant des features ont un produit scalaire élevé.
    """
    features = PHONEME_FEATURES.get(phoneme)
    if features is None:
        # Phonème inconnu → fallback FNV-1a (évite le crash)
        seed = fnv1a_64(phoneme)
        psi = np.zeros(DIM, dtype=np.complex128)
        for d in range(DIM):
            phase = ((seed >> (d % 32)) ^ (d * 2654435761)) % 2147483647
            phase = (phase * PHI) % TAU
            psi[d] = math.cos(phase) + 1j * math.sin(phase)
        psi /= np.sqrt(np.sum(np.abs(psi) ** 2))
        return psi

    _init_base_vectors()

    psi = np.zeros(DIM, dtype=np.complex128)
    for feat_val, base_vec in zip(features, _BASE_VECTORS):
        if feat_val > 0.01:
            psi += feat_val * base_vec

    # Normalisation L2
    norm = np.sqrt(np.sum(np.abs(psi) ** 2))
    if norm > 1e-10:
        psi /= norm
    return psi


# ═══════════════════════════════════════════════════════════════════════════════
# Binding / Unbinding HRR (convolution circulaire dans ℂᵈⁱᵐ)
# ═══════════════════════════════════════════════════════════════════════════════

def bind(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Binding HRR : a ⊛ b = IFFT(FFT(a) × FFT(b)).
    
    Associatif, commutatif (en module), inversible.
    Utilisé pour composer : diphone = gauche ⊛ droite.
    """
    fa = np.fft.fft(a)
    fb = np.fft.fft(b)
    result = np.fft.ifft(fa * fb)
    # Normalisation
    norm = np.sqrt(np.sum(np.abs(result) ** 2))
    if norm > 1e-10:
        result /= norm
    return result


def unbind(composite: np.ndarray, known: np.ndarray) -> np.ndarray:
    """Unbinding HRR : composite ⊘ known ≈ unknown.
    
    Utilise la corrélation circulaire : IFFT(FFT(composite) × conj(FFT(known))).
    """
    fc = np.fft.fft(composite)
    fk = np.fft.fft(known)
    result = np.fft.ifft(fc * np.conj(fk))
    norm = np.sqrt(np.sum(np.abs(result) ** 2))
    if norm > 1e-10:
        result /= norm
    return result


def similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Similarité cosinus entre deux vecteurs complexes de ℂᵈⁱᵐ (0..1)."""
    return float(np.real(np.dot(np.conj(a), b)))


# ═══════════════════════════════════════════════════════════════════════════════
# Encodage positionnel (position dans l'énoncé)
# ═══════════════════════════════════════════════════════════════════════════════

_POSITION_VECTORS: Dict[int, np.ndarray] = {}


def encode_position(pos: int) -> np.ndarray:
    """Encode une position entière en ψ ∈ ℂ⁵¹².
    
    Utilise FNV-1a + φ-spacing. Deux positions consécutives ne sont PAS
    orthogonales (elles doivent pouvoir être partiellement confondues,
    ce qui est désirable pour la généralisation positionnelle).
    """
    if pos in _POSITION_VECTORS:
        return _POSITION_VECTORS[pos]

    seed = fnv1a_64(f"pos_{pos}")
    psi = np.zeros(DIM, dtype=np.complex128)
    for d in range(DIM):
        # φ-spacing : les positions voisines ont des phases proches
        phase = ((seed + d * PHI * 100) % 1048573) / 1048573.0 * TAU
        psi[d] = math.cos(phase) + 1j * math.sin(phase)
    psi /= np.sqrt(np.sum(np.abs(psi) ** 2))
    _POSITION_VECTORS[pos] = psi
    return psi


# ═══════════════════════════════════════════════════════════════════════════════
# SymbolicEncoder — API publique
# ═══════════════════════════════════════════════════════════════════════════════

class SymbolicEncoder:
    """Couche symbolique VSA/HRR — composition linguistique en ℂ⁵¹².
    
    Usage :
        enc = SymbolicEncoder()
        psi_phrase = enc.encode_phrase(["b", "ɔ̃", "ʒ", "u", "ʁ"])
        diphone = enc.bind_diphone("b", "ɔ̃")
        recovered = enc.unbind_diphone(diphone, "ɔ̃")  # ≈ ψ("b")
    """

    def __init__(self):
        _init_base_vectors()

    # ── Encodage de base ────────────────────────────────────────────────

    def encode(self, phoneme: str) -> np.ndarray:
        """Encode un phonème unique."""
        return encode_phoneme(phoneme)

    def encode_sequence(self, phonemes: List[str]) -> np.ndarray:
        """Superposition positionnelle : Σ (ψ(phonème_i) ⊛ ψ(pos_i))."""
        result = np.zeros(DIM, dtype=np.complex128)
        for i, p in enumerate(phonemes):
            ph = encode_phoneme(p)
            pos = encode_position(i)
            bound = bind(ph, pos)
            result += bound
        norm = np.sqrt(np.sum(np.abs(result) ** 2))
        if norm > 1e-10:
            result /= norm
        return result

    def encode_phrase(self, phonemes: List[str]) -> np.ndarray:
        """Alias pour encode_sequence."""
        return self.encode_sequence(phonemes)

    # ── Binding/Unbinding diphones ──────────────────────────────────────

    def bind_diphone(self, left: str, right: str) -> np.ndarray:
        """Crée un diphone : ψ_gauche ⊛ ψ_droite."""
        l = encode_phoneme(left)
        r = encode_phoneme(right)
        return bind(l, r)

    def unbind_diphone(self, diphone: np.ndarray, known: str) -> np.ndarray:
        """Retrouve l'autre phonème à partir du diphone et d'un connu."""
        k = encode_phoneme(known)
        return unbind(diphone, k)

    # ── Similarité ──────────────────────────────────────────────────────

    def sim(self, a: np.ndarray, b: np.ndarray) -> float:
        """Similarité cosinus entre deux vecteurs."""
        return similarity(a, b)

    def phoneme_sim(self, p1: str, p2: str) -> float:
        """Similarité entre deux phonèmes (0 = orthogonal, 1 = identique)."""
        return similarity(encode_phoneme(p1), encode_phoneme(p2))
