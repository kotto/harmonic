"""
Spectral Embedding — Plongement sémantique ondulatoire
======================================================
Implémente le pipeline PPMI → Laplacian Eigenmaps → phases S¹
pour donner aux vecteurs d'onde une SIGNIFICATION SÉMANTIQUE.

Principe ondulatoire :
  Chaque mot reçoit une phase θ(mot) ∈ [0, 2π] telle que :
    |θ("coeur") - θ("cardiaque")| est faible  (co-occurrence forte)
    |θ("coeur") - θ("galaxie")| est grand     (jamais co-occurrence)

  La phase est dérivée du Laplacien du graphe de co-occurrence PPMI :
    L = I - D^{-1/2} W D^{-1/2}
    θ(mot) = arg(v₁(mot) + i·v₂(mot))
    où v₁, v₂ sont les 2 premiers vecteurs propres non-triviaux de L

  Le vecteur d'onde complexe final combine :
    - La phase sémantique θ (sens du mot)
    - L'amplitude spectrale (fréquence d'usage)
    - Le bruit Gaussien résiduel (orthogonalité HRR)

Usage :
  from spectral_embedding import SpectralEmbedding
  
  # Phase 1 : construire depuis un corpus
  se = SpectralEmbedding(dim=512)
  se.build_from_corpus(sentences)  # liste de listes de mots
  se.save('data/spectral_phases.json')
  
  # Phase 2 : utiliser au démarrage
  se = SpectralEmbedding(dim=512)
  se.load('data/spectral_phases.json')
  v = se.get_vector("lumiere")  # vecteur complexe sémantiquement informé
"""

import sys, os, math, time, json, logging
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Dict, Optional, Tuple
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
log = logging.getLogger(__name__)

# Constantes harmoniques
PHI = (1 + math.sqrt(5)) / 2
PHI_INV = 1.0 / PHI
TAU = 2.0 * math.pi

# Tentative d'import scipy (accélération massive pour grandes matrices)
try:
    from scipy.sparse import lil_matrix, csr_matrix, diags, eye
    from scipy.sparse.linalg import eigsh
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTRUCTION PPMI
# ═══════════════════════════════════════════════════════════════════════════════

def build_ppmi_matrix(sentences: List[List[str]],
                      window: int = 5,
                      min_freq: int = 2) -> Tuple[np.ndarray, Dict[str, int]]:
    """
    Construit la matrice PPMI (Positive Pointwise Mutual Information).
    
    PPMI(A,B) = max(0, log[ count(A,B) · N / (count(A) · count(B)) ])
    
    Args:
        sentences: corpus tokenisé (liste de phrases = liste de mots)
        window: taille de la fenêtre de co-occurrence
        min_freq: fréquence minimale pour qu'un mot soit dans le vocabulaire
    
    Returns:
        (matrice PPMI dense ou sparse, vocabulaire {mot: index})
    """
    # 1. Compter les fréquences de mots
    word_counts = Counter()
    for sent in sentences:
        for w in sent:
            if len(w) > 1:
                word_counts[w] += 1
    
    # Filtrer par fréquence minimale
    vocab = {w: i for i, (w, c) in enumerate(
        sorted([(w, c) for w, c in word_counts.items() if c >= min_freq],
               key=lambda x: -x[1])
    )}
    N = len(vocab)
    if N == 0:
        return np.zeros((1, 1)), {}
    
    log.info(f"  Vocabulaire PPMI : {N} mots (min_freq={min_freq})")
    
    # 2. Compter les co-occurrences
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
    
    log.info(f"  Co-occurrences : {total_pairs:,} paires")
    
    # 3. Calculer PPMI
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
        W = csr_matrix((ppmi_vals, (rows, cols)), shape=(N, N))
        W = (W + W.T) / 2  # symétriser
    else:
        W = np.zeros((N, N), dtype=np.float64)
        for i in range(N):
            for j in range(N):
                if cooc[i, j] > 0:
                    freq_prod = word_freq[i] * word_freq[j]
                    if freq_prod > 0:
                        pmi = math.log(cooc[i, j] * total_pairs / freq_prod)
                        W[i, j] = max(0, pmi)
        W = (W + W.T) / 2
    
    return W, vocab


# ═══════════════════════════════════════════════════════════════════════════════
# LAPLACIAN EIGENMAPS
# ═══════════════════════════════════════════════════════════════════════════════

def svd_embedding(W, k: int = 2) -> Tuple[np.ndarray, np.ndarray]:
    """
    Plongement par SVD tronquée sur la matrice PPMI.
    
    Plus robuste que Laplacian Eigenmaps sur les petits corpus.
    W ≈ U Σ V^T → embedding = U[:, :k]
    
    Returns:
        (embedding [N, k], singular_values [k])
    """
    N = W.shape[0]
    
    if HAS_SCIPY and hasattr(W, 'toarray'):
        from scipy.sparse.linalg import svds
        log.info(f"  [SVD sparse] Calcul des {k} plus grandes valeurs singulières...")
        U, S, Vt = svds(W, k=k, which='LM')
        # svds retourne en ordre croissant → inverser
        idx = np.argsort(S)[::-1]
        S = S[idx]
        U = U[:, idx]
    else:
        # Dense fallback
        if hasattr(W, 'toarray'):
            W_dense = W.toarray()
        else:
            W_dense = W
        log.info(f"  [SVD dense] Calcul des valeurs singulières (matrice {N}×{N})...")
        U, S, Vt = np.linalg.svd(W_dense, full_matrices=False)
        U = U[:, :k]
        S = S[:k]
    
    log.info(f"  Valeurs singulières : σ₁={S[0]:.2f}, σ₂={S[1]:.2f}")
    return U, S


def embedding_to_phases(embedding: np.ndarray) -> np.ndarray:
    """
    Convertit le plongement 2D en phases sur S¹.
    
    θ(mot) = arg(v₁(mot) + i·v₂(mot)) ∈ [0, 2π]
    """
    phases = np.arctan2(embedding[:, 1], embedding[:, 0]) % TAU
    return phases


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSE PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════

class SpectralEmbedding:
    """
    Plongement spectral sémantique pour l'encodeur holographique.
    
    Chaque mot reçoit un vecteur complexe dont :
      - La PHASE est dérivée du Laplacian Eigenmaps (sens sémantique)
      - L'AMPLITUDE suit la distribution HRR standard (orthogonalité)
    
    Cela préserve la propriété HRR (binding/unbinding) tout en
    injectant la structure sémantique réelle du langage.
    """
    
    def __init__(self, dim: int = 512):
        self.dim = dim
        self.phases: Dict[str, float] = {}    # mot → θ ∈ [0, 2π]
        self.vocab: Dict[str, int] = {}
        self.embedding: Optional[np.ndarray] = None
        self._cache: Dict[str, np.ndarray] = {}
    
    # ═════════════════════════════════════════════════════════════════════════
    # CONSTRUCTION
    # ═════════════════════════════════════════════════════════════════════════
    
    def build_from_corpus(self, sentences: List[List[str]],
                          window: int = 5, min_freq: int = 2,
                          use_svd: bool = True):
        """
        Pipeline : corpus → PPMI → SVD (ou Laplacian) → phases S¹.
        
        Args:
            sentences: corpus tokenisé
            window: fenêtre de co-occurrence
            min_freq: fréquence minimale
            use_svd: utiliser SVD (plus robuste) au lieu de Laplacian Eigenmaps
        """
        t0 = time.time()
        
        # 1. PPMI
        log.info("Construction PPMI...")
        W, vocab = build_ppmi_matrix(sentences, window, min_freq)
        self.vocab = vocab
        
        if len(vocab) < 3:
            log.warning("Vocabulaire trop petit pour le plongement spectral")
            return
        
        # 2. Plongement (SVD ou Laplacian)
        if use_svd:
            log.info("SVD...")
            embedding, values = svd_embedding(W, k=2)
        else:
            log.info("Laplacian Eigenmaps...")
            embedding, values = laplacian_eigenmaps(W, k=2)
        self.embedding = embedding
        
        # 3. Phases S¹
        phases = embedding_to_phases(embedding)
        
        for word, idx in vocab.items():
            self.phases[word] = float(phases[idx])
        
        dt = time.time() - t0
        log.info(f"  {len(self.phases)} mots plongés en {dt:.1f}s")
    
    def build_from_kb(self, knowledge_base: List[Tuple[str, str, str, str]]):
        """
        Construit le plongement depuis la base de connaissance.
        Chaque fait (sujet, relation, objet) est traité comme une phrase.
        """
        sentences = []
        for s, r, o, _ in knowledge_base:
            # La relation compte comme un mot pour la co-occurrence
            words = []
            for w in f"{s} {r} {o}".lower().split():
                w = w.strip('.,!?;:()[]{}«»""\'\'')
                if len(w) > 1:
                    words.append(w)
            if len(words) >= 2:
                sentences.append(words)
        
        self.build_from_corpus(sentences, window=5, min_freq=1)
    
    # ═════════════════════════════════════════════════════════════════════════
    # ACCÈS AUX VECTEURS
    # ═════════════════════════════════════════════════════════════════════════
    
    def get_phase(self, word: str) -> Optional[float]:
        """Retourne la phase θ(word) ∈ [0, 2π], ou None si inconnu."""
        return self.phases.get(word.lower().strip())
    
    def get_vector(self, word: str) -> np.ndarray:
        """
        Génère un vecteur complexe D-dimensionnel pour un mot.
        
        Stratégie hybride :
          - Si le mot a une phase sémantique θ → l'utiliser comme biais
            directionnel dans les premières dimensions
          - Les dimensions restantes sont remplies par un hash Gaussien
            déterministe (pour préserver l'orthogonalité HRR)
        
        Cela garantit :
          1. Deux mots sémantiquement proches → phases proches → 
             produit scalaire élevé
          2. Deux mots quelconques → toujours quasi-orthogonaux (HRR)
          3. Déterminisme (même mot → même vecteur)
        """
        word = word.lower().strip()
        if word in self._cache:
            return self._cache[word]
        
        # Seed déterministe (hash FNV-1a simple)
        seed = 2166136261
        for ch in word:
            seed = ((seed ^ ord(ch)) * 16777619) & 0xFFFFFFFF
        rng = np.random.RandomState(seed)
        
        sigma = 1.0 / math.sqrt(2.0 * self.dim)
        real = rng.randn(self.dim).astype(np.float64) * sigma
        imag = rng.randn(self.dim).astype(np.float64) * sigma
        
        # Si on a une phase sémantique → l'injecter fortement
        phase = self.phases.get(word)
        if phase is not None:
            # Injecter la phase dans plusieurs paires de dimensions
            # pour qu'elle DOMINE le produit scalaire
            # Stratégie : utiliser les 32 premières paires de dimensions
            n_phase_dims = min(32, self.dim // 2)
            boost = math.sqrt(self.dim / (2.0 * n_phase_dims)) * sigma
            for k in range(n_phase_dims):
                # Chaque paire de dimensions porte une harmonique de la phase
                phase_k = phase * (1.0 + k * PHI_INV)
                real[2*k] = math.cos(phase_k) * boost
                imag[2*k] = math.sin(phase_k) * boost
        
        v = real + 1j * imag
        
        # Normaliser
        norm = np.sqrt(np.sum(np.abs(v)**2))
        if norm > 1e-15:
            v /= norm
        
        self._cache[word] = v
        return v
    
    def get_similarity(self, word_a: str, word_b: str) -> float:
        """
        Similarité sémantique entre deux mots.
        
        Si les deux ont une phase → cos(θ_a - θ_b)
        Sinon → produit scalaire HRR standard
        """
        pa = self.phases.get(word_a.lower())
        pb = self.phases.get(word_b.lower())
        
        if pa is not None and pb is not None:
            # Similarité par phase : cos(Δθ)
            return math.cos(pa - pb)
        
        # Fallback : produit scalaire des vecteurs complets
        va = self.get_vector(word_a)
        vb = self.get_vector(word_b)
        return float(np.real(np.dot(va, np.conj(vb))))
    
    # ═════════════════════════════════════════════════════════════════════════
    # PERSISTANCE
    # ═════════════════════════════════════════════════════════════════════════
    
    def save(self, path: str):
        """Sauvegarde les phases en JSON."""
        data = {
            'dim': self.dim,
            'phases': {w: t for w, t in self.phases.items()},
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        log.info(f"  Phases sauvegardées : {path} ({len(self.phases)} mots)")
    
    def load(self, path: str) -> bool:
        """Charge les phases depuis JSON."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.dim = data.get('dim', self.dim)
            self.phases = {w: float(t) for w, t in data.get('phases', {}).items()}
            self.vocab = {w: i for i, w in enumerate(self.phases.keys())}
            self._cache = {}
            log.info(f"  Phases chargées : {path} ({len(self.phases)} mots)")
            return True
        except Exception as e:
            log.warning(f"  Impossible de charger {path}: {e}")
            return False
    
    @property
    def size(self) -> int:
        """Nombre de mots plongés."""
        return len(self.phases)
    
    @property
    def is_ready(self) -> bool:
        """True si le plongement est disponible."""
        return len(self.phases) > 0
    
    # ═════════════════════════════════════════════════════════════════════════
    # SECTEUR PAR PHASE (remplace detect_sector par mots-clés)
    # ═════════════════════════════════════════════════════════════════════════
    
    # 12 domaines × 30° chacun sur le cercle S¹
    SECTOR_RANGES = {
        'PHYSIQUE':       (0, 30),
        'MATHS':          (30, 60),
        'BIOLOGIE':       (60, 90),
        'ECOLOGIE':       (90, 120),
        'CONSCIENCE':     (120, 150),
        'EMOTION':        (150, 180),
        'ASTRONOMIE':     (180, 210),
        'COSMOLOGIE':     (210, 240),
        'HISTOIRE':       (240, 270),
        'CULTURE':        (270, 300),
        'GEOGRAPHIE':     (300, 330),
        'PHILOSOPHIE':    (330, 360),
    }
    
    def sector_from_phase(self, theta: float) -> str:
        """Détermine le secteur à partir de la phase θ."""
        deg = math.degrees(theta) % 360
        for sector, (lo, hi) in self.SECTOR_RANGES.items():
            if lo <= deg < hi:
                return sector
        return 'GENERAL'
    
    def get_sector(self, word: str) -> str:
        """Retourne le secteur d'un mot basé sur sa phase."""
        phase = self.get_phase(word)
        if phase is None:
            return 'GENERAL'
        return self.sector_from_phase(phase)


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMO
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    print("=" * 65)
    print("SPECTRAL EMBEDDING — Plongement sémantique ondulatoire")
    print("PPMI → Laplacian Eigenmaps → phases S¹")
    print("=" * 65)
    
    # Corpus de test
    corpus = [
        # Physique
        ["lumiere", "est", "une", "onde", "electromagnetique"],
        ["lumiere", "se", "propage", "a", "trois", "cent", "mille", "km"],
        ["lumiere", "composee", "de", "photons"],
        ["photons", "sont", "des", "particules", "sans", "masse"],
        ["onde", "transporte", "energie", "sans", "matiere"],
        ["energie", "se", "mesure", "en", "joules"],
        # Biologie
        ["coeur", "pompe", "le", "sang"],
        ["sang", "transporte", "oxygene"],
        ["coeur", "est", "un", "muscle"],
        ["muscle", "cardiaque", "bat", "soixante", "fois"],
        ["cardiaque", "designe", "le", "coeur"],
        ["oxygene", "necessaire", "aux", "cellules"],
        ["cellules", "sont", "unites", "du", "vivant"],
        # Cosmologie
        ["univers", "commence", "par", "big", "bang"],
        ["big", "bang", "il", "ya", "treize", "milliards"],
        ["galaxie", "contient", "milliards", "etoiles"],
        ["etoiles", "produisent", "lumiere", "par", "fusion"],
        ["fusion", "nucleaire", "transforme", "hydrogene", "helium"],
        # Conscience
        ["conscience", "emerge", "du", "cerveau"],
        ["cerveau", "contient", "neurones"],
        ["neurones", "communiquent", "par", "synapses"],
        ["conscience", "permet", "la", "perception"],
        ["perception", "est", "subjective"],
    ]
    
    se = SpectralEmbedding(dim=512)
    se.build_from_corpus(corpus, window=5, min_freq=1)
    
    print(f"\n📊 {se.size} mots plongés")
    
    # Vérifier la qualité sémantique
    print("\n🔍 Qualité sémantique :")
    
    test_pairs = [
        ("coeur", "cardiaque", "PROCHES"),
        ("coeur", "sang", "LIÉS"),
        ("lumiere", "photons", "LIÉS"),
        ("lumiere", "onde", "LIÉS"),
        ("big", "bang", "LIÉS"),
        ("conscience", "cerveau", "LIÉS"),
        ("cerveau", "neurones", "LIÉS"),
        # Paires éloignées
        ("coeur", "galaxie", "ÉLOIGNÉS"),
        ("lumiere", "neurones", "ÉLOIGNÉS"),
        ("big", "cellules", "ÉLOIGNÉS"),
    ]
    
    print(f"\n  {'Mot A':>14s}  {'Mot B':>14s}  {'Attendu':>10s}  {'sim':>8s}  {'phase_A':>8s}  {'phase_B':>8s}  {'Δθ°':>6s}")
    print(f"  " + "-" * 75)
    
    for a, b, expected in test_pairs:
        sim = se.get_similarity(a, b)
        pa = se.get_phase(a)
        pb = se.get_phase(b)
        if pa is not None and pb is not None:
            dtheta = math.degrees(abs(pa - pb)) % 360
            if dtheta > 180:
                dtheta = 360 - dtheta
            pa_str = f"{math.degrees(pa):.1f}°"
            pb_str = f"{math.degrees(pb):.1f}°"
            dt_str = f"{dtheta:.1f}°"
        else:
            pa_str = "N/A"
            pb_str = "N/A"
            dt_str = "N/A"
        print(f"  {a:>14s}  {b:>14s}  {expected:>10s}  {sim:+8.3f}  {pa_str:>8s}  {pb_str:>8s}  {dt_str:>6s}")
    
    # Vecteurs
    print("\n🧪 Test HRR avec phases sémantiques :")
    v1 = se.get_vector("coeur")
    v2 = se.get_vector("cardiaque")
    v3 = se.get_vector("galaxie")
    
    dot_cc = float(np.real(np.dot(v1, np.conj(v2))))
    dot_cg = float(np.real(np.dot(v1, np.conj(v3))))
    print(f"  ⟨coeur|cardiaque⟩ = {dot_cc:+.4f}  (devrait être élevé)")
    print(f"  ⟨coeur|galaxie⟩   = {dot_cg:+.4f}  (devrait être faible)")
    print(f"  Δ = {abs(dot_cc - dot_cg):.4f}  (écart de discriminabilité)")


if __name__ == '__main__':
    demo()

# ═══════════════════════════════════════════════════════════════════════════════
# INSTANCE GLOBALE (chargée une fois au démarrage)
# ═══════════════════════════════════════════════════════════════════════════════
_SPECTRAL = SpectralEmbedding(dim=512)
_PHASES_PATH = Path(__file__).resolve().parent / 'data' / 'spectral_phases.json'
if _PHASES_PATH.exists():
    _SPECTRAL.load(str(_PHASES_PATH))
