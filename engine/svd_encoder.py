"""
SVD Encoder — Vecteurs propres réels comme embeddings complexes
=================================================================
Utilise directement les vecteurs propres U de la décomposition SVD
de la matrice PPMI comme embeddings de mots.

Contrairement aux approches basées sur les phases, ici le produit
scalaire entre deux mots correspond à la VRAIE similarité cosinus
de leurs embeddings SVD — ce qui est exactement ce que font
Word2Vec, GloVe et LSA.

ψ(word) = U[word_idx, :k]  (vecteur réel, normalisé)

⟨ψ_a|ψ_b⟩ = cos(angle entre embeddings SVD)
  ≈ +1 : synonymes / mots très liés
  ≈  0 : mots sans rapport
  ≈ -1 : mots antinomiques

Author: Univers-Holistique
"""

import math, json, time
import numpy as np
from typing import Dict, Optional

PHI = 1.618033988749895


class SVDEncoder:
    """
    Encodeur basé sur les vecteurs propres SVD de la matrice PPMI.

    C'est l'équivalent exact de LSA (Latent Semantic Analysis) projeté
    dans un espace complexe pour compatibilité avec Wave GPT.

    Usage:
        encoder = SVDEncoder()
        encoder.load('data/svd_encoder_fr.json')
        psi = encoder.encode('lune')
    """

    def __init__(self, dim: int = 256):
        self.dim = dim
        self.vocab: Dict[str, int] = {}
        self.rev_vocab: Dict[int, str] = {}
        self.embeddings: Optional[np.ndarray] = None  # [N, k] réels
        self.k = 0
        self._cache: Dict[str, np.ndarray] = {}

    def build_from_ppmi(self, ppmi, vocab: Dict[str, int], k: int = 16):
        """
        Construit l'encodeur depuis une matrice PPMI.

        Args:
            ppmi: matrice PPMI (sparse ou dense)
            vocab: {mot: index}
            k: nombre de composantes SVD
        """
        N = len(vocab)
        k = min(k, N - 1)

        # SVD
        try:
            from scipy.sparse.linalg import svds
            U, S, Vt = svds(ppmi, k=k, which='LM')
        except ImportError:
            arr = ppmi.toarray() if hasattr(ppmi, 'toarray') else ppmi
            U, S, Vt = np.linalg.svd(arr, full_matrices=False)
            U = U[:, :k]; S = S[:k]; Vt = Vt[:k, :]

        # Trier par valeur singulière décroissante
        idx = np.argsort(-S)
        U = U[:, idx]; S = S[idx]

        # Normaliser chaque ligne
        for i in range(N):
            norm = np.linalg.norm(U[i])
            if norm > 1e-10:
                U[i] /= norm

        self.vocab = vocab
        self.rev_vocab = {i: w for w, i in vocab.items()}
        self.embeddings = U
        self.k = k
        self._cache.clear()
        print(f"  SVDEncoder: {N} mots, k={k}, SVs={S[:5].round(1)}")

    def encode(self, word: str) -> np.ndarray:
        """
        Encode un mot en vecteur complexe ψ ∈ ℂ^dim.

        ψ[k] = U[word, k]  pour k < k_svd
        ψ[k] = 0           pour k >= k_svd

        Le produit scalaire ⟨ψ_a|ψ_b⟩ = Σ U[a]·U[b] = similarité cosinus SVD.
        """
        word = word.lower().strip()
        if word in self._cache:
            return self._cache[word]

        word_idx = self.vocab.get(word)
        if word_idx is not None and self.embeddings is not None:
            u = self.embeddings[word_idx]  # [k] réel
            psi = np.zeros(self.dim, dtype=complex)
            # Projeter les k premières composantes réelles dans ℂ
            for i in range(min(self.k, self.dim)):
                psi[i] = u[i]
            norm = np.linalg.norm(psi)
            if norm > 1e-10:
                psi = psi / norm
        else:
            # Mot inconnu : vecteur aléatoire déterministe
            seed = 2166136261
            for ch in word:
                seed = ((seed ^ ord(ch)) * 16777619) & 0xFFFFFFFF
            rng = np.random.RandomState(seed)
            psi = rng.randn(self.dim) + 1j * rng.randn(self.dim)
            psi = psi / np.linalg.norm(psi)

        self._cache[word] = psi
        return psi

    def encode_word(self, word: str) -> np.ndarray:
        return self.encode(word)

    @property
    def vocabulary(self) -> Dict[str, np.ndarray]:
        return self._cache

    @property
    def semantic_phases(self):
        """Compatibilité avec l'interface CorpusEncoder."""
        return None

    @property
    def bigram_phases(self):
        return None

    def top_neighbors(self, word: str, k: int = 10):
        psi_w = self.encode(word)
        neighbors = []
        for w in self.vocab:
            if w == word:
                continue
            psi_v = self.encode(w)
            coh = float(np.real(np.dot(psi_w.conj(), psi_v)))
            neighbors.append((w, coh))
        neighbors.sort(key=lambda x: -x[1])
        return neighbors[:k]

    def save(self, path: str):
        """Sauvegarde au format JSON."""
        data = {
            'dim': self.dim,
            'k': self.k,
            'vocab': {w: int(i) for w, i in self.vocab.items()},
            'embeddings': self.embeddings.tolist() if self.embeddings is not None else None,
        }
        with open(path, 'w') as f:
            json.dump(data, f)
        print(f"Saved: {path} ({len(self.vocab)} mots)")

    def load(self, path: str) -> bool:
        """Charge depuis JSON."""
        with open(path) as f:
            data = json.load(f)
        self.dim = data['dim']
        self.k = data['k']
        self.vocab = {w: int(i) for w, i in data['vocab'].items()}
        self.rev_vocab = {i: w for w, i in self.vocab.items()}
        self.embeddings = np.array(data['embeddings']) if data['embeddings'] else None
        self._cache.clear()
        return True


if __name__ == '__main__':
    print("Test SVDEncoder...")
    import sys; sys.path.insert(0, '.')
    from corpus_encoder import tokenize, build_ppmi
    import random

    with open('data/corpora/merged_fr.txt', encoding='utf-8') as f:
        lines = f.readlines()
    random.seed(42)
    sentences = [tokenize(l) for l in lines]
    sentences = [s for s in sentences if len(s) >= 2]
    if len(sentences) > 80000:
        sentences = random.sample(sentences, 80000)

    ppmi, vocab = build_ppmi(sentences, window=6, min_freq=3)
    enc = SVDEncoder(dim=256)
    enc.build_from_ppmi(ppmi, vocab, k=16)

    pairs = [
        ('lune', 'soleil'), ('lune', 'football'), ('amour', 'table'),
        ('guerre', 'paix'), ('beau', 'joli'), ('mort', 'vie'),
    ]
    for w1, w2 in pairs:
        c = float(np.real(np.dot(enc.encode(w1).conj(), enc.encode(w2))))
        print(f"  {w1}↔{w2} = {c:+.3f}")

    enc.save('data/svd_encoder_fr.json')
