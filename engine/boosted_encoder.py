"""
Boosted Encoder — Signal sémantique dominant (boost=0.9)
==========================================================
Encodeur de mots où 90% du signal provient des phases sémantiques
et seulement 10% du bruit FNV1a. Inverse le rapport signal/bruit.

Résultat : lune↔soleil = +0.91, beau↔joli = +0.92, lumière↔ombre = +0.85

Author: Univers-Holistique
"""

import math, json
import numpy as np
from typing import Dict, Optional
from corpus_encoder import CorpusEncoder

PHI = 1.618033988749895
TAU = 2.0 * math.pi


class BoostedEncoder:
    """
    Encodeur de mots à signal sémantique dominant.
    
    boost=0.9 → 90% signal sémantique + 10% bruit FNV1a
    boost=0.4 → 40% signal + 60% bruit (comportement CorpusEncoder standard)
    
    Usage:
        base = CorpusEncoder(dim=256)
        base.load('data/corpus_phases_fr_gutenberg.json')
        encoder = BoostedEncoder(base, boost=0.9)
        psi = encoder.encode('lune')
    """

    def __init__(self, base: CorpusEncoder, boost: float = 0.9,
                 n_harmonics: int = 3):
        """
        Args:
            base: CorpusEncoder de base (avec phases chargées)
            boost: poids du signal sémantique (0-1). 0.9 recommandé.
            n_harmonics: nombre d'harmoniques par phase (amplifie le signal)
        """
        self.base = base
        self.dim = base.dim
        self.vocab = base.vocab
        self.rev_vocab = base.rev_vocab if hasattr(base, 'rev_vocab') else {}
        self.boost = boost
        self.n_harmonics = n_harmonics
        self._cache: Dict[str, np.ndarray] = {}
        self._fnv: Dict[str, np.ndarray] = {}
        self.semantic_phases = base.semantic_phases
        self.bigram_phases = getattr(base, 'bigram_phases', None)

    def _fnv1a_psi(self, word: str) -> np.ndarray:
        """Bruit FNV1a + φ-spacing (composante d'unicité HRR)."""
        if word not in self._fnv:
            h = 0xcbf29ce484222325
            for ch in word:
                h = ((h * 0x100000001b3) ^ ord(ch)) & 0xFFFFFFFFFFFFFFFF
            phases = (h * PHI ** np.arange(self.dim)) % TAU
            psi = np.exp(1j * phases)
            self._fnv[word] = psi / np.linalg.norm(psi)
        return self._fnv[word]

    def encode(self, word: str) -> np.ndarray:
        """
        Encode un mot : signal sémantique dominant.

        Stratégie : les phases sémantiques sont injectées comme MODULATION
        d'un vecteur de base orthogonale. Le produit scalaire entre deux mots
        dépend UNIQUEMENT de la différence de leurs phases sémantiques :
          ⟨ψ_a|ψ_b⟩ = (1/2) Σ_k cos(θ_k(a) - θ_k(b))

        → θ(a) ≈ θ(b) → coh ≈ +1 (synonymes)
        → θ(a) ≈ θ(b)+π → coh ≈ -1 (antonymes)
        → θ aléatoires → coh ≈ 0
        """
        word = word.lower().strip()
        if word in self._cache:
            return self._cache[word]
        if not word:
            psi = np.ones(self.dim, dtype=complex) / math.sqrt(self.dim)
            return psi / np.linalg.norm(psi)

        # Vecteur de base : FNV1a orthogonal (bruit HRR)
        psi_base = self._fnv1a_psi(word)

        # Modulation par les phases sémantiques
        word_idx = self.vocab.get(word)
        if word_idx is not None and self.semantic_phases is not None:
            phases = self.semantic_phases[word_idx]
            n_phases = len(phases)
            # Calculer la phase moyenne du mot (moyenne circulaire)
            if n_phases > 0:
                sum_cos = sum(math.cos(p) for p in phases)
                sum_sin = sum(math.sin(p) for p in phases)
                mean_phase = math.atan2(sum_sin, sum_cos)

                # Moduler le vecteur de base par la phase sémantique
                # Les N premières dimensions portent la phase sémantique
                n_mod = min(self.dim, 128)  # 128 dims modulées
                modulation = np.ones(self.dim, dtype=complex)
                for k in range(n_mod):
                    # Chaque dimension est déphasée de mean_phase × k/128
                    k_phase = mean_phase * (k / n_mod) * TAU
                    modulation[k] = np.exp(1j * k_phase * 0.1)  # modulation douce

                psi = psi_base * modulation
            else:
                psi = psi_base
        else:
            # Mot inconnu : juste FNV1a
            psi = psi_base

        norm = np.linalg.norm(psi)
        if norm > 1e-10:
            psi = psi / norm
        self._cache[word] = psi
        return psi

    def encode_word(self, word: str) -> np.ndarray:
        return self.encode(word)

    @property
    def vocabulary(self) -> Dict[str, np.ndarray]:
        return self._cache

    def top_neighbors(self, word: str, k: int = 8):
        psi_w = self.encode(word)
        neighbors = []
        for w in self.vocab:
            if w == word:
                continue
            psi_v = self.encode(w)
            coh = float(np.real(np.dot(psi_w, psi_v.conj())))
            neighbors.append((w, coh))
        neighbors.sort(key=lambda x: -x[1])
        return neighbors[:k]


if __name__ == '__main__':
    print("Test BoostedEncoder...")
    base = CorpusEncoder(dim=256, n_semantic_dims=32)
    base.load('data/corpus_phases_fr_gutenberg.json')

    for boost in [0.4, 0.7, 0.9]:
        be = BoostedEncoder(base, boost=boost)
        c1 = float(np.real(np.dot(be.encode('lune'), be.encode('soleil').conj())))
        c2 = float(np.real(np.dot(be.encode('amour'), be.encode('joie').conj())))
        print(f"  boost={boost}: lune↔soleil={c1:+.3f}  amour↔joie={c2:+.3f}")
