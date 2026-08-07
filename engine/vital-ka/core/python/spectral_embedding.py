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
import collections
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
    Convertit le plongement K-dim en K/2 phases sur S¹.
    
    θ_j(mot) = arg(v_{2j}(mot) + i·v_{2j+1}(mot)) ∈ [0, 2π]
    
    Pour K=2 → 1 phase par mot
    Pour K=8 → 4 phases par mot (signature sémantique riche)
    """
    K = embedding.shape[1]
    n_phases = K // 2
    phases = np.zeros((embedding.shape[0], n_phases))
    for j in range(n_phases):
        phases[:, j] = np.arctan2(embedding[:, 2*j+1], embedding[:, 2*j]) % TAU
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
        K = 8  # 4 phases sémantiques par mot (richesse sémantique)
        if use_svd:
            log.info(f"SVD (k={K})...")
            embedding, values = svd_embedding(W, k=K)
        else:
            log.info(f"Laplacian Eigenmaps (k={K})...")
            embedding, values = laplacian_eigenmaps(W, k=K)
        self.embedding = embedding
        
        # 3. Phases S¹ (K/2 phases par mot)
        phases = embedding_to_phases(embedding)  # [N, K/2]
        
        for word, idx in vocab.items():
            self.phases[word] = phases[idx].tolist()  # liste de K/2 phases
        
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
        """Retourne la première phase sémantique θ₁(word) ∈ [0, 2π], ou None."""
        val = self.phases.get(word.lower().strip())
        if val is None:
            return None
        if isinstance(val, list):
            return val[0] if val else None
        return float(val)
    
    def get_phases(self, word: str) -> Optional[List[float]]:
        """Retourne toutes les phases sémantiques [θ₁, θ₂, ...] du mot, ou None."""
        val = self.phases.get(word.lower().strip())
        if val is None:
            return None
        if isinstance(val, list):
            return val
        return [float(val)]  # Ancien format → liste de 1 phase
    
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
            # Normaliser : phase peut être un float ou une liste de phases
            if isinstance(phase, list):
                phase_list = phase
            else:
                phase_list = [float(phase)]
            
            # Injecter la phase dans plusieurs paires de dimensions
            # pour qu'elle DOMINE le produit scalaire
            # Stratégie : utiliser les 32 premières paires de dimensions
            n_phase_dims = min(32, self.dim // 2)
            boost = math.sqrt(self.dim / (2.0 * n_phase_dims)) * sigma
            for k in range(n_phase_dims):
                # Chaque paire de dimensions porte une harmonique de la phase
                # Utiliser les phases sémantiques disponibles (cycliquement si moins que n_phase_dims)
                p = phase_list[k % len(phase_list)]
                phase_k = p * (1.0 + k * PHI_INV)
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
        """Charge les phases depuis JSON (compatible ancien et nouveau format)."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.dim = data.get('dim', self.dim)
            raw_phases = data.get('phases', {})
            # Compatible : float (ancien) ou list (nouveau)
            self.phases = {}
            for w, t in raw_phases.items():
                if isinstance(t, list):
                    self.phases[w] = [float(x) for x in t]
                else:
                    self.phases[w] = float(t)
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


# ═══════════════════════════════════════════════════════════════════════════════
# GAP DETECTION — Détection de communautés et trous de connaissance
# ═══════════════════════════════════════════════════════════════════════════════

class KnowledgeGapAnalyzer:
    """
    Analyse le graphe de connaissance pour détecter :
    1. Les communautés de concepts (clusters thématiques)
    2. Les GAPS — paires de communautés proches sémantiquement mais sans edges
    
    Usage :
        analyzer = KnowledgeGapAnalyzer()
        analyzer.build_from_facts(facts)  # liste de (s, r, o, sec)
        gaps = analyzer.find_gaps(min_gap_score=0.3)
        for gap in gaps:
            print(f"Gap: {gap['cluster_a']} ↔ {gap['cluster_b']} (score={gap['score']:.2f})")
            print(f"  Suggestion: {gap['distill_prompt']}")
    """
    
    def __init__(self, max_nodes: int = 5000):
        self.max_nodes = max_nodes
        self.adj_matrix: Optional[np.ndarray] = None      # sparse adjacency
        self.node_list: List[str] = []                     # index → concept
        self.node_to_idx: Dict[str, int] = {}
        self.communities: Dict[int, List[int]] = {}        # cluster_id → [node indices]
        self.node_community: Dict[int, int] = {}            # node_idx → cluster_id
        self.community_labels: Dict[int, str] = {}          # cluster_id → label
        self.gaps: List[Dict] = []
        self._spectral: Optional[SpectralEmbedding] = None
    
    def build_from_facts(self, facts: List[Tuple[str, str, str, str]]):
        """
        Construit le graphe de co-occurrence à partir des triplets.
        
        Chaque triplet (s, r, o) crée une arête entre s et o dans le graphe.
        """
        import collections
        
        # Compter les co-occurrences sujet-objet
        cooc = collections.Counter()
        concept_freq = collections.Counter()
        
        for s, r, o, sec in facts:
            s_clean = s.lower().strip()
            o_clean = o.lower().strip()
            if s_clean and o_clean and s_clean != o_clean:
                cooc[(s_clean, o_clean)] += 1
                concept_freq[s_clean] += 1
                concept_freq[o_clean] += 1
        
        # Garder les N concepts les plus fréquents
        top_concepts = [c for c, _ in concept_freq.most_common(self.max_nodes)]
        self.node_list = top_concepts
        self.node_to_idx = {c: i for i, c in enumerate(top_concepts)}
        
        n = len(top_concepts)
        self.adj_matrix = np.zeros((n, n), dtype=np.float32)
        
        for (a, b), weight in cooc.items():
            if a in self.node_to_idx and b in self.node_to_idx:
                i, j = self.node_to_idx[a], self.node_to_idx[b]
                self.adj_matrix[i, j] += weight
                self.adj_matrix[j, i] += weight  # symétrique
        
        log.info(f"KnowledgeGapAnalyzer: graphe {n}x{n}, "
                 f"{int(np.count_nonzero(self.adj_matrix)//2)} arêtes")
        
        # Exécuter l'analyse complète
        self._find_communities()
        self._label_communities()
        self.find_gaps()
    
    def _find_communities(self):
        """
        Détection de communautés par propagation de labels (Louvain simplifié).
        """
        if self.adj_matrix is None or len(self.node_list) < 3:
            return
        
        n = len(self.node_list)
        # Initialiser chaque nœud dans sa propre communauté
        self.node_community = {i: i for i in range(n)}
        
        # Propagation simple : chaque nœud rejoint la communauté majoritaire
        # de ses voisins (poids des arêtes)
        for _ in range(10):  # max 10 itérations
            changed = 0
            for i in range(n):
                if self.adj_matrix[i].sum() == 0:
                    continue
                # Compter les votes des voisins
                neighbor_votes = collections.Counter()
                for j in range(n):
                    if self.adj_matrix[i, j] > 0:
                        neighbor_votes[self.node_community[j]] += self.adj_matrix[i, j]
                if neighbor_votes:
                    best_community = neighbor_votes.most_common(1)[0][0]
                    if self.node_community[i] != best_community:
                        self.node_community[i] = best_community
                        changed += 1
            if changed == 0:
                break
        
        # Regrouper par communauté
        self.communities = {}
        for node_idx, comm_id in self.node_community.items():
            if comm_id not in self.communities:
                self.communities[comm_id] = []
            self.communities[comm_id].append(node_idx)
        
        # Garder les communautés avec ≥ 3 nœuds
        self.communities = {k: v for k, v in self.communities.items() if len(v) >= 3}
        log.info(f"  → {len(self.communities)} communautés détectées")
    
    def _label_communities(self):
        """Nomme chaque communauté d'après ses 3 concepts les plus fréquents."""
        for comm_id, nodes in self.communities.items():
            labels = [self.node_list[i] for i in nodes[:3]]
            self.community_labels[comm_id] = ' / '.join(labels)
    
    def find_gaps(self, min_gap_score: float = 0.2, max_gaps: int = 20) -> List[Dict]:
        """
        Détecte les gaps : paires de communautés qui DEVRAIENT être connectées
        (proches sémantiquement) mais ont peu/pas d'arêtes entre elles.
        
        Args:
            min_gap_score: score minimum pour considérer un gap (0-1)
            max_gaps: nombre maximum de gaps à retourner
        
        Returns:
            Liste de gaps triés par score décroissant
        """
        self.gaps = []
        comm_ids = list(self.communities.keys())
        if len(comm_ids) < 2:
            return []
        
        # 1. Calculer la connectivité inter-communautés
        inter_edges = {}
        for i, ci in enumerate(comm_ids):
            for cj in comm_ids[i+1:]:
                edges_ij = 0
                for ni in self.communities[ci]:
                    for nj in self.communities[cj]:
                        edges_ij += self.adj_matrix[ni, nj]
                inter_edges[(ci, cj)] = int(edges_ij)
        
        # 2. Calculer la similarité sémantique (via co-occurrence partagée)
        # Deux communautés sont proches si elles partagent des mots dans leurs sujets
        semantic_sim = {}
        for ci in comm_ids:
            words_i = set()
            for ni in self.communities[ci]:
                words_i.update(self.node_list[ni].split())
            
            for cj in comm_ids:
                if ci >= cj: continue
                words_j = set()
                for nj in self.communities[cj]:
                    words_j.update(self.node_list[nj].split())
                
                # Similarité Jaccard sur les mots
                intersection = len(words_i & words_j)
                union = len(words_i | words_j)
                semantic_sim[(ci, cj)] = intersection / max(union, 1)
        
        # 3. Calculer le gap score
        # Gap élevé = forte similarité sémantique MAIS faible connectivité
        max_edges = max(inter_edges.values()) if inter_edges else 1
        max_sim = max(semantic_sim.values()) if semantic_sim else 1
        
        for (ci, cj) in inter_edges:
            connectivity_norm = inter_edges[(ci, cj)] / max(max_edges, 1)
            sim = semantic_sim.get((ci, cj), 0)
            sim_norm = sim / max(max_sim, 0.01)
            
            # Gap = similarité élevée + connectivité faible
            gap_score = sim_norm * (1.0 - connectivity_norm)
            
            if gap_score >= min_gap_score:
                label_a = self.community_labels.get(ci, str(ci))
                label_b = self.community_labels.get(cj, str(cj))
                
                # Générer un prompt de distillation pour combler ce gap
                prompt = (f"Liste 30 faits reliant {label_a} et {label_b}. "
                         f"Format: sujet | relation | objet. Un par ligne.")
                
                self.gaps.append({
                    'cluster_a': label_a,
                    'cluster_b': label_b,
                    'score': round(gap_score, 3),
                    'connectivity': round(connectivity_norm, 3),
                    'semantic_sim': round(sim, 3),
                    'distill_prompt': prompt,
                    'nodes_a': len(self.communities[ci]),
                    'nodes_b': len(self.communities[cj]),
                })
        
        self.gaps.sort(key=lambda g: -g['score'])
        self.gaps = self.gaps[:max_gaps]
        
        log.info(f"  → {len(self.gaps)} gaps détectés (top score: "
                 f"{self.gaps[0]['score']:.3f})" if self.gaps else "  → 0 gaps")
        
        return self.gaps
    
    def print_report(self):
        """Affiche un rapport des gaps détectés."""
        if not self.gaps:
            print("Aucun gap détecté.")
            return
        
        print(f"\n{'='*70}")
        print(f"  🔍 GAPS DE CONNAISSANCE — Top {min(10, len(self.gaps))}")
        print(f"{'='*70}")
        for i, g in enumerate(self.gaps[:10]):
            print(f"\n  #{i+1} [{g['score']:.2f}] {g['cluster_a']} ↔ {g['cluster_b']}")
            print(f"      Similarité: {g['semantic_sim']:.2f} | Connectivité: {g['connectivity']:.2f}")
            print(f"      Nœuds: {g['nodes_a']} + {g['nodes_b']}")
            print(f"      → Prompt: {g['distill_prompt'][:80]}...")
        print()


if __name__ == '__main__':
    demo()

# ═══════════════════════════════════════════════════════════════════════════════
# INSTANCE GLOBALE (chargée une fois au démarrage)
# ═══════════════════════════════════════════════════════════════════════════════
_SPECTRAL = SpectralEmbedding(dim=512)
_PHASES_PATH = Path(__file__).resolve().parent / 'data' / 'spectral_phases.json'
if _PHASES_PATH.exists():
    _SPECTRAL.load(str(_PHASES_PATH))
