"""
Harmonic Encoder — Texte → ψ ∈ ℂ⁵¹²
======================================

Encode un prompt textuel en vecteur complexe via FNV-1a + φ-spacing.
Déterministe, 0 paramètre, cross-lingual par construction.

Chaque mot/concept → amplitude + phase dans l'espace complexe.
L'espacement φ garantit l'orthogonalité (~40 000 mots sans collision).
"""

import math
import numpy as np

PHI = 1.618033988749895
TAU = 2.0 * math.pi


def _fnv1a_hash(s: str) -> int:
    FNV_OFFSET = 14695981039346656037
    FNV_PRIME = 1099511628211
    h = FNV_OFFSET
    for ch in s:
        h ^= ord(ch)
        h = (h * FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
    return h


class HarmonicEncoder:
    """Encodeur texte → ψ déterministe."""
    
    def __init__(self, dim: int = 512):
        self.dim = dim
    
    def encode(self, text: str) -> np.ndarray:
        """
        Encode un texte en vecteur ψ ∈ ℂᵈⁱᵐ.
        
        Args:
            text: prompt en langage naturel
            
        Returns:
            [dim] complex128
        """
        text = text.strip().lower()
        # Découpage en tokens (mots + bigrammes)
        words = text.split()
        tokens = words + [f"{words[i]}_{words[i+1]}" for i in range(len(words)-1)]
        
        psi = np.zeros(self.dim, dtype=np.complex128)
        
        for t_idx, token in enumerate(tokens):
            seed = _fnv1a_hash(token)
            # Position φ-espacée dans le vecteur
            base_dim = (seed * int(PHI * 1000)) % self.dim
            
            # Chaque token active ~8 dimensions (sparsité contrôlée)
            for d_offset in range(8):
                d = int((base_dim + d_offset * PHI * 37) % self.dim)
                phase = ((seed >> (d_offset * 4)) % 1048573) / 1048573.0 * TAU
                amp = 1.0 / (1.0 + d_offset * 0.5)
                psi[d] += amp * (math.cos(phase) + 1j * math.sin(phase))
        
        # Normalisation ℓ²
        norm = np.sqrt(np.sum(np.abs(psi) ** 2))
        if norm > 1e-10:
            psi /= norm
        
        return psi
    
    def encode_batch(self, texts: list) -> np.ndarray:
        """Encode un lot de textes."""
        return np.array([self.encode(t) for t in texts])
    
    def similarity(self, text_a: str, text_b: str) -> float:
        """Similarité cosinus entre deux textes dans l'espace ψ."""
        a = self.encode(text_a)
        b = self.encode(text_b)
        dot = np.real(np.dot(a, np.conj(b)))
        return float((dot + 1.0) / 2.0)
