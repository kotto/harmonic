"""
Corpus Encoder — Phase sémantique + syntaxique depuis un vrai corpus
======================================================================
Pipeline complet :
  1. Corpus texte → tokenisation → PPMI (co-occurrence)
  2. PPMI → SVD → phases sémantiques θ_sem(mot)
  3. Corpus → bigrammes → phases de transition θ_trans(mot_i → mot_{i+1})
  4. Fusion : ψ = α·ψ_sem + (1-α)·ψ_trans + bruit FNV1a

Résultat : un encodeur de mots où :
  - Deux mots sémantiquement proches ont des phases proches
  - Les transitions grammaticales sont encodées (déterminant → nom)
  - L'unicité HRR est préservée (bruit FNV1a résiduel)

Usage :
    encoder = CorpusEncoder(dim=512)
    encoder.build('data/corpus_extracted.txt')
    encoder.save('data/corpus_phases.json')
    
    psi = encoder.encode('lune')
    # → vecteur complexe avec phase sémantique + syntaxique

Author: Univers-Holistique
"""

import math, json, time, re
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional
import numpy as np

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════

PHI = 1.618033988749895
PI = math.pi
TAU = 2.0 * PI

try:
    from scipy.sparse import lil_matrix, csr_matrix
    from scipy.sparse.linalg import svds
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE DE CONSTRUCTION
# ═══════════════════════════════════════════════════════════════════════════════

def tokenize(text: str) -> List[str]:
    """Tokenise un texte français en mots normalisés."""
    text = text.lower()
    # Garder les lettres, apostrophes, tirets
    words = re.findall(r"[a-zàâäéèêëîïôöùûüçœæ'-]+", text)
    return [w for w in words if len(w) >= 1]


def build_ppmi(sentences: List[List[str]], window: int = 8,
               min_freq: int = 1) -> Tuple[np.ndarray, Dict[str, int]]:
    """
    Construit la matrice PPMI à partir de phrases tokenisées.
    
    Args:
        sentences: liste de phrases (chaque phrase = liste de mots)
        window: taille de la fenêtre de co-occurrence
        min_freq: fréquence minimale pour inclure un mot
        
    Returns:
        (matrice PPMI, vocabulaire {mot: index})
    """
    # Fréquences
    word_counts = Counter()
    for sent in sentences:
        for w in sent:
            word_counts[w] += 1
    
    # Vocabulaire (trié par fréquence décroissante)
    vocab_items = [(w, c) for w, c in word_counts.items() if c >= min_freq]
    vocab_items.sort(key=lambda x: -x[1])
    vocab = {w: i for i, (w, _) in enumerate(vocab_items)}
    N = len(vocab)
    
    if N < 3:
        return np.zeros((1, 1)), {}
    
    print(f"  Vocabulaire: {N} mots (min_freq={min_freq})")
    
    # Co-occurrences (sparse si scipy dispo)
    if HAS_SCIPY:
        cooc = lil_matrix((N, N), dtype=np.float64)
    else:
        cooc = np.zeros((N, N), dtype=np.float64)
    
    word_freq = np.zeros(N)
    total_pairs = 0
    
    for sent in sentences:
        ids = [vocab[w] for w in sent if w in vocab]
        for i, center in enumerate(ids):
            word_freq[center] += 1
            start = max(0, i - window)
            end = min(len(ids), i + window + 1)
            for j in range(start, end):
                if j != i:
                    ctx = ids[j]
                    if HAS_SCIPY:
                        cooc[center, ctx] += 1
                    else:
                        cooc[center, ctx] += 1
                    total_pairs += 1
    
    if HAS_SCIPY:
        cooc = cooc.tocsr()
    
    print(f"  Paires de co-occurrence: {total_pairs:,}")
    
    # PPMI
    total_pairs = max(total_pairs, 1)
    
    if HAS_SCIPY:
        cx = cooc.tocoo()
        rows, cols, vals = cx.row, cx.col, cx.data
        freq_prod = word_freq[rows] * word_freq[cols]
        ppmi_vals = np.where(
            freq_prod > 0,
            np.log(np.maximum(vals * total_pairs / freq_prod, 1e-10)),
            0.0
        )
        ppmi_vals = np.maximum(ppmi_vals, 0)
        ppmi = csr_matrix((ppmi_vals, (rows, cols)), shape=(N, N))
    else:
        ppmi = np.zeros((N, N))
        for i in range(N):
            for j in range(N):
                if cooc[i, j] > 0:
                    pmi = math.log(max(cooc[i, j] * total_pairs / 
                                      (word_freq[i] * word_freq[j]), 1e-10))
                    ppmi[i, j] = max(0, pmi)
    
    return ppmi, vocab


def svd_phases(ppmi: np.ndarray, k: int = 4) -> Tuple[np.ndarray, np.ndarray]:
    """
    SVD de la matrice PPMI → phases sémantiques.
    
    Chaque mot reçoit k/2 phases (paires sin/cos).
    
    Returns:
        (phases [N, k//2], valeurs singulières [k])
    """
    N = ppmi.shape[0]
    k = min(k, N - 1)
    
    if HAS_SCIPY:
        U, S, Vt = svds(ppmi, k=k, which='LM')
    else:
        U, S, Vt = np.linalg.svd(ppmi.toarray() if hasattr(ppmi, 'toarray') else ppmi, 
                                  full_matrices=False)
        U = U[:, :k]
        S = S[:k]
        Vt = Vt[:k, :]
    
    # Trier par valeur singulière décroissante
    idx = np.argsort(-S)
    U = U[:, idx]
    S = S[idx]
    
    # Extraire les phases (k/2 paires)
    n_phases = k // 2
    phases = np.zeros((N, n_phases))
    for p in range(n_phases):
        phases[:, p] = np.arctan2(U[:, 2*p+1], U[:, 2*p])
        phases[:, p] = (phases[:, p] + TAU) % TAU
    
    print(f"  SVD: {k} composantes, {n_phases} phases/mot")
    print(f"  Valeurs singulières: {[f'{s:.1f}' for s in S[:5]]}")
    
    return phases, S


def build_bigram_phases(sentences: List[List[str]], vocab: Dict[str, int],
                        n_phase_dims: int = 16) -> np.ndarray:
    """
    Construit des phases de transition bigramme.
    
    Pour chaque paire (w_i, w_{i+1}), on encode la force de transition
    comme une phase. Deux mots qui apparaissent souvent ensemble
    ont des phases de transition alignées.
    
    Returns:
        bigram_phases [N, n_phase_dims] — phases de transition par mot
    """
    N = len(vocab)
    rev_vocab = {i: w for w, i in vocab.items()}
    
    # Compter les bigrammes
    bigram_counts = Counter()
    follower_counts = defaultdict(Counter)
    
    for sent in sentences:
        ids = [vocab[w] for w in sent if w in vocab]
        for i in range(len(ids) - 1):
            bigram = (ids[i], ids[i+1])
            bigram_counts[bigram] += 1
            follower_counts[ids[i]][ids[i+1]] += 1
    
    # Construire les phases de transition
    # Chaque mot a une « signature de followers » encodée en phases
    bigram_phases = np.zeros((N, n_phase_dims))
    
    for word_idx in range(N):
        followers = follower_counts.get(word_idx, {})
        if not followers:
            continue
        
        # Trier les followers par fréquence
        sorted_followers = sorted(followers.items(), key=lambda x: -x[1])
        total = sum(c for _, c in sorted_followers)
        
        # Encoder les top followers comme phases harmoniques
        for j, (follower_idx, count) in enumerate(sorted_followers[:n_phase_dims]):
            prob = count / total if total > 0 else 0
            # Phase dominante pour ce follower
            phase = (j / n_phase_dims) * TAU
            # Amplitude = probabilité
            bigram_phases[word_idx, j % n_phase_dims] = phase * prob
    
    print(f"  Bigrammes: {len(bigram_counts):,} paires uniques")
    
    return bigram_phases


# ═══════════════════════════════════════════════════════════════════════════════
# ENCODEUR PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class CorpusEncoder:
    """
    Encodeur de mots entraîné sur un corpus réel.
    
    Combine :
      - Phases sémantiques (PPMI + SVD)
      - Phases de transition (bigrammes)
      - Bruit FNV1a (unicité HRR)
    """

    def __init__(self, dim: int = 512, n_semantic_dims: int = 32,
                 n_bigram_dims: int = 16):
        self.dim = dim
        self.n_semantic_dims = n_semantic_dims
        self.n_bigram_dims = n_bigram_dims
        
        self.vocab: Dict[str, int] = {}
        self.rev_vocab: Dict[int, str] = {}
        
        self.semantic_phases: Optional[np.ndarray] = None  # [N, n_phases]
        self.bigram_phases: Optional[np.ndarray] = None    # [N, n_bigram_dims]
        
        self._cache: Dict[str, np.ndarray] = {}

    def build(self, corpus_path: str, window: int = 8,
              min_freq: int = 1, k_svd: int = 8):
        """
        Pipeline complet : corpus → PPMI → SVD → phases.
        
        Args:
            corpus_path: chemin vers un fichier texte (une phrase par ligne)
            window: fenêtre de co-occurrence PPMI
            min_freq: fréquence minimale des mots
            k_svd: nombre de composantes SVD
        """
        t0 = time.time()
        
        # 1. Charger et tokeniser
        print(f"Chargement du corpus: {corpus_path}")
        with open(corpus_path, encoding='utf-8') as f:
            lines = f.readlines()
        
        sentences = []
        for line in lines:
            words = tokenize(line)
            if len(words) >= 2:
                sentences.append(words)
        
        print(f"  {len(sentences)} phrases, {sum(len(s) for s in sentences)} mots")
        
        # 2. PPMI
        print("Construction PPMI...")
        ppmi, vocab = build_ppmi(sentences, window=window, min_freq=min_freq)
        self.vocab = vocab
        self.rev_vocab = {i: w for w, i in vocab.items()}
        N = len(vocab)
        
        if N < 3:
            print("  ⚠️ Vocabulaire trop petit")
            return
        
        # 3. SVD → phases sémantiques
        print("SVD → phases sémantiques...")
        self.semantic_phases, S = svd_phases(ppmi, k=k_svd)
        
        # 4. Bigrammes → phases de transition
        print("Construction bigrammes...")
        self.bigram_phases = build_bigram_phases(sentences, vocab, self.n_bigram_dims)
        
        dt = time.time() - t0
        print(f"✅ CorpusEncoder construit en {dt:.1f}s ({N} mots)")
        
        # Vider le cache (les phases ont changé)
        self._cache.clear()

    def encode(self, word: str) -> np.ndarray:
        """
        Encode un mot en vecteur d'onde ψ ∈ ℂ^dim.
        
        Combine phases sémantiques + bigrammes + bruit FNV1a.
        """
        word = word.lower().strip()
        if not word:
            return self._zero_psi()
        
        if word in self._cache:
            return self._cache[word]
        
        # Bruit FNV1a de base
        psi = self._fnv1a_psi(word)
        
        # Injecter les phases sémantiques si le mot est dans le vocabulaire
        word_idx = self.vocab.get(word)
        if word_idx is not None and self.semantic_phases is not None:
            n_sem = min(self.n_semantic_dims, self.semantic_phases.shape[1])
            boost = 0.4  # poids de la composante sémantique
            for k in range(n_sem):
                phase = self.semantic_phases[word_idx, k]
                # Injecter dans les premières dimensions
                psi[2*k] += boost * math.cos(phase)
                psi[2*k+1] += boost * math.sin(phase)
        
        # Injecter les phases de transition (bigrammes)
        if word_idx is not None and self.bigram_phases is not None:
            n_bg = min(self.n_bigram_dims, self.bigram_phases.shape[1])
            boost = 0.25  # poids de la composante syntaxique
            offset = self.n_semantic_dims * 2
            for k in range(n_bg):
                phase = self.bigram_phases[word_idx, k]
                if phase > 0:  # seulement si des followers existent
                    idx = offset + 2*k
                    if idx + 1 < self.dim:
                        psi[idx] += boost * math.cos(phase)
                        psi[idx+1] += boost * math.sin(phase)
        
        # Normaliser
        norm = np.linalg.norm(psi)
        if norm > 1e-10:
            psi = psi / norm
        
        self._cache[word] = psi
        return psi

    def _fnv1a_psi(self, word: str) -> np.ndarray:
        """Base FNV1a + φ-spacing."""
        h = 0xcbf29ce484222325
        for ch in word:
            h = ((h * 0x100000001b3) ^ ord(ch)) & 0xFFFFFFFFFFFFFFFF
        phases = (h * PHI ** np.arange(self.dim)) % TAU
        psi = np.exp(1j * phases)
        return psi / np.linalg.norm(psi)

    def _zero_psi(self):
        psi = np.ones(self.dim, dtype=complex) / math.sqrt(self.dim)
        return psi / np.linalg.norm(psi)

    def encode_word(self, word: str) -> np.ndarray:
        return self.encode(word)

    @property
    def vocabulary(self) -> Dict[str, np.ndarray]:
        return self._cache

    def save(self, path: str):
        """Sauvegarde le modèle."""
        data = {
            'dim': self.dim,
            'n_semantic_dims': self.n_semantic_dims,
            'n_bigram_dims': self.n_bigram_dims,
            'vocab': self.vocab,
            'semantic_phases': self.semantic_phases.tolist() if self.semantic_phases is not None else None,
            'bigram_phases': self.bigram_phases.tolist() if self.bigram_phases is not None else None,
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Sauvegardé: {path} ({len(self.vocab)} mots)")

    def load(self, path: str) -> bool:
        """Charge un modèle sauvegardé."""
        with open(path) as f:
            data = json.load(f)
        self.dim = data['dim']
        self.n_semantic_dims = data['n_semantic_dims']
        self.n_bigram_dims = data['n_bigram_dims']
        self.vocab = {k: int(v) for k, v in data['vocab'].items()}
        self.rev_vocab = {int(i): w for w, i in self.vocab.items()}
        self.semantic_phases = np.array(data['semantic_phases']) if data['semantic_phases'] else None
        self.bigram_phases = np.array(data['bigram_phases']) if data['bigram_phases'] else None
        self._cache.clear()
        return True

    def top_neighbors(self, word: str, k: int = 8) -> List[Tuple[str, float]]:
        """Retourne les k plus proches voisins sémantiques d'un mot."""
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


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def _test():
    """Test rapide."""
    print("=" * 60)
    print("TEST : CorpusEncoder — Phases depuis corpus réel")
    print("=" * 60)

    encoder = CorpusEncoder(dim=256, n_semantic_dims=16, n_bigram_dims=8)
    encoder.build('data/corpus_extracted.txt', window=8, min_freq=1, k_svd=8)
    
    print(f"\n─── Top voisins sémantiques ───")
    for word in ['lune', 'amour', 'nuit', 'mer', 'ciel', 'fleur', 'temps']:
        if word in encoder.vocab:
            neighbors = encoder.top_neighbors(word, k=5)
            print(f"  {word}: {[(w, round(s, 3)) for w, s in neighbors]}")
    
    print(f"\n─── Similarités sémantiques ───")
    import numpy as np
    pairs = [
        ('lune', 'nuit'), ('lune', 'soleil'), ('amour', 'cœur'),
        ('mer', 'vague'), ('fleur', 'jardin'), ('ciel', 'étoile'),
    ]
    for w1, w2 in pairs:
        v1 = encoder.encode(w1)
        v2 = encoder.encode(w2)
        coh = float(np.real(np.dot(v1, v2.conj())))
        print(f"  {w1:8s} ↔ {w2:8s}  coh={coh:+.3f}")
    
    # Save
    encoder.save('data/corpus_phases.json')
    print("\n✅ Terminé !")


if __name__ == '__main__':
    _test()
