"""
Unified Semantic Pipeline — Pipeline Sémantique Harmonique Unifié
==================================================================
Architecture en 4 couches basée sur les 5 axiomes du principe fondateur :

  Couche 0 — UNIFIED ENCODER    : encodage HRR + index auxiliaires (une fois)
  Couche 1 — UNIFIED RETRIEVER   : scoring I×P×H×D (inconscient, ~1ms)
  Couche 2 — CONSCIOUS VERIFIER  : vérification + synthèse ψ_R (conscient, ~10ms)
  Couche 3 — WAVE DECODER        : décodage → langage naturel (livraison, ~5ms)

Principe : Ψ_RÉPONSE = H ⊗ [ Σ φ⁻ⁿ · exp(i·θ(w)) ]

Usage:
    from unified_semantic_pipeline import SemanticPipeline

    pipeline = SemanticPipeline(knowledge_base)
    result = pipeline.process("explique la lumiere")
    print(result.response)  # texte fluide émergeant de l'onde
    print(result.confidence)  # score de confiance [0, 1]
"""

import math, time, logging
from collections import Counter, defaultdict
from typing import List, Tuple, Dict, Set, Optional
from dataclasses import dataclass, field
import numpy as np

# Chemins relatifs
from pathlib import Path
import sys
_MODULE_DIR = Path(__file__).resolve().parent
if str(_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULE_DIR))

from holographic_encoder import (
    HolographicEncoder, _circular_convolve, _circular_correlate,
    _fnv1a_hash, build_holographic_waves
)

# SFT High-Amplitude Facts (faits validés manuellement, équivalent RLHF)
try:
    from harmonic_quality import HIGH_AMPLITUDE_FACTS
except ImportError:
    HIGH_AMPLITUDE_FACTS = {}

log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES FONDAMENTALES
# ═══════════════════════════════════════════════════════════════════════════════

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI       # ≈ 0.618
PHI_INV2 = PHI_INV ** 2   # ≈ 0.382
PHI_INV3 = PHI_INV ** 3   # ≈ 0.236
PHI_INV4 = PHI_INV ** 4   # ≈ 0.146
TAU = 2.0 * math.pi

# Poids du scoring unifié (décroissance φ⁻ⁿ)
W_I = PHI_INV    # Interférence directionnelle (poids dominant)
W_P = PHI_INV2   # Cohérence de phase PPMI
W_H = PHI_INV3   # Résonance holographique
W_D = PHI_INV4   # Alignement domaine (Harmonic7D)

# Seuils de confiance
CONF_HIGH = 0.70
CONF_MEDIUM = 0.50
CONF_LOW = 0.35

# Stopwords universels (FR + EN)
_STOPWORDS = {
    'the','a','an','is','are','was','were','of','in','on','at','to',
    'for','with','by','from','and','or','it','its','that','this',
    'these','those','which','who','whom','what','when','where','why','how',
    'be','been','being','have','has','had','do','does','did','will','would',
    'could','should','may','might','shall','can','not','but','if','so','as',
    'le','la','les','un','une','des','de','du','d','l','est','sont',
    'a','ont','que','qui','quoi','dont','dans','sur','pour','par',
    'avec','et','il','elle','ils','elles','ce','cet','cette','ces',
    'ne','pas','plus','moins','très','trop','aussi','mais','donc','or','car',
}

# Préfixes de question FR + EN (pour le tokenizer)
_QUESTION_PREFIXES_FR = [
    'qu est-ce que', 'qu est ce que', 'qui a invente', 'qui a cree',
    'qui a decouvert', 'qui a peint', 'qui a ecrit', 'qui est',
    'explique', 'pourquoi', 'comment', 'decris', 'definis',
    'quelle est la capitale de', 'quelle est la capitale du',
    'quel est le', 'quelle est', 'quand', 'ou se trouve', 'ou est',
    'que signifie', 'donne moi', 'parle moi de', 'dis moi',
    'qu est ce qu', 'a quoi sert', 'combien',
]
_QUESTION_PREFIXES_EN = [
    'what is the', 'what is a', 'what is', 'what are',
    'who is', 'who was', 'who wrote', 'who painted',
    'who discovered', 'who invented', 'who created',
    'when did', 'when was', 'when', 'where is', 'where are',
    'where', 'why is', 'why does', 'why', 'how does', 'how do', 'how',
    'explain', 'describe', 'define', 'tell me about', 'tell me',
    'which', 'whose',
]

# Verbes faibles FR + EN (pénalisés dans le score I)
_WEAK_WORDS = {
    'explique', 'est', 'sont', 'fait', 'donne', 'permet', 'dit',
    'explain', 'is', 'are', 'does', 'make', 'allows', 'says',
    'a', 'ont', 'was', 'were', 'be', 'been', 'being',
}

# Connecteurs logiques FR + EN pour le WaveDecoder
_CONNECTORS_FR = ['', ' De plus, ', ' Plus précisément, ', ' En effet, ', ' Ainsi, ']
_CONNECTORS_EN = ['', ' Moreover, ', ' More precisely, ', ' Indeed, ', ' Thus, ']

# Patterns structurels bilingues
_STRUCTURAL_PATTERNS = {
    # (motif_rel, boost) — si le motif est dans la relation, booster
    'capitale': ('capitale', 'capital'),
    'peint': ('peint', 'painted'),
    'découvert': ('decouvert', 'discovered'),
    'inventé': ('invente', 'invented'),
    'écrit': ('ecrit', 'wrote', 'written'),
    'composé': ('compose', 'composed'),
    'fondé': ('fonde', 'founded'),
}

# Mapping secteur → 7 constantes actives (de harmonic7d)
SECTOR_CONSTANTS = {
    'PHYSIQUE_FOND':  {'π': 0.8, 'e': 0.6, 'φ': 0.4, '√2': 0.3, '√3': 0.3},
    'PHYSIQUE_APPLI': {'π': 0.7, 'e': 0.5, 'φ': 0.3, '√3': 0.4},
    'MATHS_PURES':    {'π': 0.9, '√2': 0.5, 'φ': 0.4, 'i': 0.3},
    'BIOLOGIE':       {'√5': 0.8, 'φ': 0.6, 'e': 0.4, '√3': 0.3},
    'CHIMIE':         {'√3': 0.6, 'e': 0.5, 'φ': 0.3, '√2': 0.3},
    'GEOGRAPHIE':     {'π': 0.7, '√3': 0.5, 'φ': 0.2},
    'GEOGRAPHY':      {'π': 0.7, '√3': 0.5, 'φ': 0.2},
    'HISTOIRE':       {'π': 0.6, 'e': 0.5, 'φ': 0.3},
    'HISTORY':        {'π': 0.6, 'e': 0.5, 'φ': 0.3},
    'LITTERATURE':    {'√5': 0.6, 'φ': 0.5, 'i': 0.3},
    'ART':            {'√5': 0.8, 'φ': 0.5, 'i': 0.3},
    'MUSIQUE':        {'π': 0.5, '√5': 0.7, 'φ': 0.4},
    'PHILOSOPHIE':    {'i': 0.7, '√2': 0.5, 'φ': 0.4},
    'CONSCIENCE':     {'i': 0.9, 'φ': 0.4, '√2': 0.3},
    'SPIRITUALITE':   {'i': 0.8, 'φ': 0.4, '√2': 0.3},
    'EMOTION_POS':    {'√2': 0.7, 'φ': 0.4, 'i': 0.3},
    'CULTURE_G':      {'π': 0.4, 'φ': 0.3, '√5': 0.3, 'i': 0.2},
    'CULTURE':        {'π': 0.4, 'φ': 0.3, '√5': 0.3},
    'TECHNOLOGIE':    {'√3': 0.5, 'e': 0.5, 'φ': 0.3},
    'ECONOMIE':       {'e': 0.6, 'φ': 0.5, 'π': 0.3},
    'POLITIQUE':      {'√2': 0.6, 'φ': 0.4, 'π': 0.3},
    'SANTE':          {'e': 0.5, '√5': 0.4, 'φ': 0.3},
    'SCIENCE':        {'π': 0.6, 'e': 0.5, 'φ': 0.3},
    'GENERAL':        {'π': 0.3, 'φ': 0.3, 'e': 0.3},
    'SYNONYME':       {'i': 0.5, '√2': 0.5},
}

CONSTANTS_ORDER = ['π', 'φ', 'e', '√2', '√3', '√5', 'i']
C7 = len(CONSTANTS_ORDER)

# Templates de réponse minimaux (fallback ultime)
_RESPONSE_TEMPLATES_FR = {
    'definition': "Le concept de {sujet} est lié à {mots}. {w0} est en relation avec {w1}.",
    'factual': "{w0} {relation} {w1}.",
    'not_found': "Je n'ai pas assez de connaissances sur {sujet} pour répondre précisément.",
    'no_understand': "Je ne comprends pas assez la question sur {sujet}.",
}

_RESPONSE_TEMPLATES_EN = {
    'definition': "The concept of {sujet} relates to {mots}. {w0} is connected to {w1}.",
    'factual': "{w0} {relation} {w1}.",
    'not_found': "I don't have enough knowledge about {sujet} to answer precisely.",
    'no_understand': "I don't quite understand the question about {sujet}.",
}


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES DE NETTOYAGE
# ═══════════════════════════════════════════════════════════════════════════════

import re

def _clean_fact_text(text: str) -> str:
    """
    Nettoie le texte d'un fait (sujet, relation, objet).

    Supprime :
      - Préfixes numériques : "2. tokyo" → "tokyo"
      - Parenthèses d'années : "(1503-1519)" → ""
      - Caractères parasites
    """
    # Supprimer les préfixes numériques (ex: "2. ", "10. ", "1)")
    text = re.sub(r'^\d+[\.\)]\s*', '', text.strip())

    # Supprimer les années entre parenthèses (ex: "(1503-1519)", "(1928)")
    text = re.sub(r'\s*\(\d{4}[\-\–]\d{4}\)\s*', ' ', text)
    text = re.sub(r'\s*\(\d{4}\)\s*', ' ', text)

    # Nettoyer les espaces multiples
    text = re.sub(r'\s+', ' ', text).strip()

    return text

@dataclass
class PipelineResult:
    """Résultat complet du pipeline sémantique."""
    response: str
    confidence: float
    facts_used: List[Tuple[str, str, str, str]]
    phase_scores: Dict[str, float] = field(default_factory=dict)
    retrieval_time_ms: float = 0.0
    decode_time_ms: float = 0.0
    total_time_ms: float = 0.0
    layer_used: str = ""  # "unified", "creative", "fallback"

    @property
    def is_confident(self) -> bool:
        return self.confidence >= CONF_HIGH

    @property
    def is_uncertain(self) -> bool:
        return self.confidence < CONF_LOW


# ═══════════════════════════════════════════════════════════════════════════════
# COUCHE 0 — UNIFIED ENCODER (construit UNE FOIS au démarrage)
# ═══════════════════════════════════════════════════════════════════════════════

class UnifiedEncoder:
    """
    Encodeur unifié — toutes les structures de données pré-calculées.

    Construit en une seule passe sur la KB :
      - HolographicEncoder : ψ_w ∈ ℂ⁵¹² pour chaque mot
      - Binding HRR : ψ_f = ψ_s ⊛ ψ_r ⊛ ψ_o pour chaque fait
      - Hologramme global : H = Σ ψ_f
      - Index inversé : mot → liste de faits (O(1) lookup)
      - PPMI neighbors : expansion sémantique (top-15 voisins/mot)
      - Vecteurs Harmonic7D : alignement domaine/constantes
    """

    def __init__(self, knowledge_base: List[Tuple[str, str, str, str]],
                 dim: int = 512, vocab_size: int = 5000,
                 top_neighbors: int = 15):
        t0 = time.time()
        self.kb = list(knowledge_base)
        self.N = len(self.kb)
        self.dim = dim

        # ── 1. HolographicEncoder ──
        self.encoder = HolographicEncoder(dim=dim)
        self.kx, self.ky, self.w2i, self.encoder = build_holographic_waves(
            self.kb, encoder=self.encoder, dim=dim
        )

        # ── 2. Binding HRR pour chaque fait ──
        self.fact_vectors: List[np.ndarray] = []
        for s, r, o, sec in self.kb:
            psi_f = self.encoder.encode_fact(s, r, o)
            self.fact_vectors.append(psi_f)

        # ── 3. Hologramme global ──
        self.hologram = np.zeros(dim, dtype=np.complex128)
        for psi_f in self.fact_vectors:
            self.hologram += psi_f

        # ── 4. Index inversé (mot → faits) ──
        self.word_to_facts: Dict[str, Set[int]] = defaultdict(set)
        self.fact_words: Dict[int, Set[str]] = {}
        self.word_counts = Counter()

        for fid, (s, r, o, sec) in enumerate(self.kb):
            words = set(self._tokenize(f"{s} {r} {o}"))
            self.fact_words[fid] = words
            for w in words:
                self.word_to_facts[w].add(fid)
                self.word_counts[w] += 1

        # ── 5. IDF ──
        self.idf = {}
        for w, df_set in self.word_to_facts.items():
            df = len(df_set)
            self.idf[w] = math.log(self.N / max(df, 1)) + 1.0

        # ── 6. Vocabulaire discriminant (ni trop rare, ni trop fréquent) ──
        min_df, max_df = 2, max(3, self.N // 3)
        self.vocab = [w for w, c in self.word_counts.most_common(vocab_size * 2)
                      if min_df <= len(self.word_to_facts[w]) <= max_df][:vocab_size]
        self.vocab_idx = {w: i for i, w in enumerate(self.vocab)}

        # ── 7. PPMI neighbors ──
        self.neighbors: Dict[str, List[Tuple[str, float]]] = {}
        self._build_ppmi(top_neighbors)

        # ── 8. Vecteurs Harmonic7D pour les faits ──
        self.fact_7d_vectors: List[List[float]] = []
        self._build_harmonic7d_vectors()

        self._build_time = time.time() - t0
        log.info(f"UnifiedEncoder: {len(self.vocab)} mots, "
                 f"{sum(len(v) for v in self.neighbors.values())} liens PPMI, "
                 f"{self.N} faits, build {self._build_time:.1f}s")

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenisation bilingue (FR/EN) avec stopwords + bigrammes.

        Gère les contractions françaises (d', l') et anglaises (don't, it's).
        Ajoute les bigrammes pertinents pour la recherche multi-mots.
        """
        # Normaliser les apostrophes et contractions
        text = text.replace("'", " ").replace("'", " ").replace("'", " ")
        # Normaliser les contractions anglaises
        for en_contraction in ["don t", "doesn t", "isn t", "aren t", "wasn t",
                                "weren t", "can t", "won t", "wouldn t", "it s",
                                "that s", "what s", "who s", "let s"]:
            text = text.replace(en_contraction, en_contraction.replace(" ", ""))

        raw_tokens = [w.strip('.,!?;:()[]{}«»\"') for w in text.lower().split()]

        # Filtrer stopwords et mots courts
        tokens = []
        for w in raw_tokens:
            if w in _STOPWORDS:
                continue
            if len(w) < 2:
                continue
            tokens.append(w)

        # Ajouter les bigrammes issus des motifs "X d Y" (contraction française)
        extra_tokens = []
        for i in range(len(raw_tokens) - 2):
            if (raw_tokens[i+1] in ("d", "l") and
                len(raw_tokens[i]) >= 2 and len(raw_tokens[i+2]) >= 2):
                extra_tokens.append(f"{raw_tokens[i]} {raw_tokens[i+2]}")

        # Ajouter les bigrammes consécutifs présents dans l'index
        for i in range(len(tokens) - 1):
            bigram = f"{tokens[i]} {tokens[i+1]}"
            if bigram in self.word_to_facts:
                extra_tokens.append(bigram)

        return tokens + extra_tokens

    def _tokenize_with_lang(self, text: str) -> Tuple[List[str], str]:
        """
        Tokenise et détecte la langue (fr/en).
        Retourne (tokens, 'fr'|'en').
        """
        text_lower = text.lower()
        # Détection simple : présence de mots anglais spécifiques
        en_markers = {'what', 'who', 'when', 'where', 'why', 'how', 'the', 'is', 'are'}
        fr_markers = {'est', 'sont', 'dans', 'pour', 'avec', 'quoi', 'comment', 'pourquoi'}
        en_score = sum(1 for w in text_lower.split() if w.strip('?') in en_markers)
        fr_score = sum(1 for w in text_lower.split() if w.strip('?') in fr_markers)
        lang = 'en' if en_score > fr_score else 'fr'
        return self._tokenize(text), lang

    def _build_ppmi(self, top_neighbors: int):
        """
        Construit les voisins PPMI — optimisé pour 76K+ faits.

        Optimisations :
          - Skip les mots-hubs (fréquence > N/3) : non discriminants
          - Skip les paires avec co-occurrence = 1 : non significatives
          - Calcul PPMI seulement pour les paires viables
          - Limite top_neighbors par mot pour contrôle mémoire
        """
        # Filtrer les hubs (mots apparaissant dans >33% des faits)
        hub_threshold = max(3, self.N // 3)
        non_hub_words = {w for w in self.vocab_idx if len(self.word_to_facts[w]) <= hub_threshold}

        # Co-occurrence : dict de dict pour O(1) lookup
        co = defaultdict(lambda: defaultdict(int))
        for fid, words in self.fact_words.items():
            word_list = [w for w in words if w in non_hub_words]
            if len(word_list) < 2:
                continue
            # Pour chaque paire unique dans le fait
            for i, w1 in enumerate(word_list):
                co_w1 = co[w1]
                for w2 in word_list[i+1:]:
                    co_w1[w2] += 1
                    co[w2][w1] += 1  # symétrique

        # PPMI : ne calculer que pour les paires avec co-occurrence >= 2
        total_pairs = max(self.N, 1)
        total_unigrams = sum(self.word_counts[w] for w in non_hub_words) + 1

        for w1, neighbors_dict in co.items():
            w1_count = self.word_counts[w1]
            candidates = []
            for w2, c in neighbors_dict.items():
                if c < 2:  # ignorer les co-occurrences uniques (bruit)
                    continue
                w2_count = self.word_counts[w2]
                # PPMI(w1, w2) = max(0, log(P(w1,w2) / (P(w1)*P(w2))))
                p_xy = c / total_pairs
                p_x = w1_count / total_unigrams
                p_y = w2_count / total_unigrams
                pmi = math.log(p_xy / (p_x * p_y + 1e-12))
                if pmi > 0:
                    candidates.append((w2, pmi))

            candidates.sort(key=lambda x: -x[1])
            self.neighbors[w1] = candidates[:top_neighbors]

    def _build_harmonic7d_vectors(self):
        """Construit les vecteurs 7D pour chaque fait (alignement domaine)."""
        # Vecteur 7D pour chaque secteur
        sector_7d = {}
        for sec, consts in SECTOR_CONSTANTS.items():
            vec = [0.0] * C7
            for cname, cval in consts.items():
                vec[CONSTANTS_ORDER.index(cname)] = cval
            norm = math.sqrt(sum(v*v for v in vec))
            if norm > 0:
                vec = [v/norm for v in vec]
            sector_7d[sec] = vec

        # Vecteur par défaut (neutre)
        default_vec = [0.2] * C7
        default_norm = math.sqrt(sum(v*v for v in default_vec))
        default_vec = [v/default_norm for v in default_vec]

        for s, r, o, sec in self.kb:
            vec = sector_7d.get(sec, default_vec)
            self.fact_7d_vectors.append(vec)

    def encode_query(self, question: str) -> np.ndarray:
        """Encode une question en vecteur complexe ψ_Q."""
        return self.encoder.encode_query(question)

    def expand_query_tokens(self, tokens: List[str]) -> List[str]:
        """Expansion PPMI : ajoute les voisins sémantiques."""
        expanded = list(tokens)
        for t in tokens:
            for n, ppmi in self.neighbors.get(t, [])[:3]:
                if ppmi > 0.5 and n not in expanded:
                    expanded.append(n)
        return expanded

    def get_candidates(self, tokens: List[str], max_candidates: int = 200) -> List[int]:
        """
        Génère les candidats via index inversé + expansion PPMI.
        Retourne les IDs des faits candidats.
        """
        expanded = self.expand_query_tokens(tokens)
        candidate_scores = defaultdict(float)

        for w in expanded:
            t_idf = self.idf.get(w, 1.0)
            for fid in self.word_to_facts.get(w, set()):
                candidate_scores[fid] += t_idf

        if not candidate_scores:
            # Fallback sans expansion
            for w in tokens:
                t_idf = self.idf.get(w, 1.0)
                for fid in self.word_to_facts.get(w, set()):
                    candidate_scores[fid] += t_idf

        # Top-N par score IDF cumulé
        sorted_fids = sorted(candidate_scores.items(), key=lambda x: -x[1])
        return [fid for fid, _ in sorted_fids[:max_candidates]]

    def get_query_7d(self, tokens: List[str]) -> List[float]:
        """Vecteur 7D pour la question (moyenne des secteurs des mots)."""
        # Accumuler les constantes des secteurs où apparaissent les mots
        vec = [0.0] * C7
        count = 0
        for t in tokens:
            if t not in self.word_to_facts:
                continue
            # Moyenne des secteurs des faits contenant ce mot
            for fid in list(self.word_to_facts[t])[:5]:
                if fid < len(self.fact_7d_vectors):
                    for i in range(C7):
                        vec[i] += self.fact_7d_vectors[fid][i]
                    count += 1

        if count > 0:
            norm = math.sqrt(sum(v*v for v in vec))
            if norm > 0:
                vec = [v/norm for v in vec]
        return vec


# ═══════════════════════════════════════════════════════════════════════════════
# COUCHE 1 — UNIFIED RETRIEVER (Inconscient, ~1ms)
# ═══════════════════════════════════════════════════════════════════════════════

class UnifiedRetriever:
    """
    Retrieval unifié par interférence I×P×H×D.

    score(f) = I(f)^W_I × P(f)^W_P × H(f)^W_H × D(f)^W_D

    où :
      I = cos(ψ_Q, ψ_f)                              [Interférence directionnelle]
      P = Σ PPMI entre mots de Q et mots de f         [Cohérence sémantique]
      H = Re(⟨ψ_f | H ⊗ ψ_Q⟩)                         [Résonance holographique]
      D = cos(vec7D(Q), vec7D(f))                      [Alignement domaine/constantes]

    Poids en décroissance φ⁻ⁿ : W_I=1/φ, W_P=1/φ², W_H=1/φ³, W_D=1/φ⁴
    """

    def __init__(self, encoder: UnifiedEncoder):
        self.enc = encoder

    def retrieve(self, question: str, max_results: int = 5) -> List[Tuple[Tuple, float, Dict]]:
        """
        Retrieval unifié complet.

        Returns:
            liste de (fait, score, diagnostic) triée par score décroissant
        """
        t0 = time.time()

        # Tokenisation
        tokens = self.enc._tokenize(question)
        if not tokens:
            return []

        # Vecteur question
        psi_q = self.enc.encode_query(question)
        q_7d = self.enc.get_query_7d(tokens)

        # H ⊗ ψ_Q (unbinding holographique — calculé une seule fois)
        h_unbind = _circular_correlate(self.enc.hologram, psi_q)

        # Candidats
        candidates = self.enc.get_candidates(tokens, max_candidates=200)

        if not candidates:
            candidates = list(range(min(self.enc.N, 500)))

        # Scorer chaque candidat
        scored = []
        for fid in candidates:
            if fid >= self.enc.N:
                continue

            psi_f = self.enc.fact_vectors[fid]
            s, r, o, sec = self.enc.kb[fid]

            # I : Interférence directionnelle (mot-à-mot)
            I = self._score_I(psi_q, psi_f, fid, tokens)

            # P : Cohérence de phase PPMI
            P = self._score_P(tokens, fid)

            # H : Résonance holographique
            H_score = self._score_H(psi_f, h_unbind)

            # D : Alignement domaine
            D = self._score_D(q_7d, fid)

            # Bonus sujet exact + objet + relation
            s_lower = s.lower().strip()
            o_lower = o.lower().strip()
            r_lower = r.lower().strip()

            # Nettoyer le sujet (sans préfixe numérique)
            s_clean = _clean_fact_text(s).lower()

            # Bonus sujet : token ÉGAL au sujet nettoyé → très fort
            bonus_sujet_exact = 10.0 if any(s_clean == t for t in tokens) else 0.0
            # Bonus bigramme : le sujet contient les deux mots d'un bigramme
            bonus_bigram = 0.0
            for t in tokens:
                if ' ' in t:
                    parts = t.split()
                    if all(p in s_clean for p in parts):
                        bonus_bigram += 6.0
            # Bonus sujet : token DANS le sujet
            bonus_sujet_partial = sum(3.0 for t in tokens if ' ' not in t and t in s_clean and t != s_clean)
            # Bonus objet : token DANS l'objet
            bonus_objet = sum(2.0 for t in tokens if t in o_lower)
            # Bonus relation : token DANS la relation
            bonus_rel = sum(4.0 for t in tokens if t in r_lower)

            # 🔥 BONUS STRUCTUREL BILINGUE
            bonus_structural = 0.0
            # Motif "X de Y" / "X of Y" → relation contient X, objet contient Y
            for i in range(len(tokens) - 1):
                t1, t2 = tokens[i], tokens[i+1]
                # "capitale/capital de X" → relation a capitale/capital, objet a X
                if t1 in ('capitale', 'capital') and t2 in o_lower:
                    bonus_structural += 8.0
                # "X de/du Y" générique
                if t2 in o_lower and t1 in r_lower:
                    bonus_structural += 3.0
            # "qui a peint/découvert/inventé/écrit X" / "who painted/discovered/invented/wrote X"
            structural_verbs = {
                'peint', 'painted', 'découvert', 'decouvert', 'discovered',
                'inventé', 'invente', 'invented', 'created',
                'écrit', 'ecrit', 'wrote', 'written',
                'composé', 'compose', 'composed',
                'fondé', 'fonde', 'founded',
            }
            for verb in structural_verbs:
                if verb in r_lower:
                    for t in tokens:
                        if len(t) >= 3 and t != verb and t in o_lower:
                            bonus_structural += 6.0

            # 🔥 BONUS OBJET EXACT : l'objet du fait MATCH EXACTEMENT le sujet de la question
            # "capitale de la france" → question a pour cible "france"
            # Un fait avec objet == "france" est bien meilleur qu'avec objet == "president of france"
            bonus_objet_exact = 0.0
            for t in tokens:
                if len(t) >= 3 and ' ' not in t:
                    if o_lower == t:
                        bonus_objet_exact += 10.0
                    elif o_lower.startswith(t + ' ') or o_lower.endswith(' ' + t):
                        bonus_objet_exact += 5.0  # objet contient le token comme mot complet

            # 🔥 BONUS SFT (High-Amplitude Facts) : faits validés manuellement
            # Équivalent harmonique du RLHF — les bons faits résonnent plus fort
            # Condition : le SFT ne s'applique que si la question est PERTINENTE
            # (les tokens de la question matchent le sujet ou l'objet du SFT)
            sft_amplitude = 1.0
            s_clean_lower = s_clean.lower()
            o_lower_norm = o_lower.replace('é','e').replace('è','e').replace('ê','e').replace('à','a').replace('ù','u').replace('ô','o').replace('î','i').replace('ï','i').replace('ç','c')
            for (sf_s, sf_r, sf_o), amp in HIGH_AMPLITUDE_FACTS.items():
                sf_s_lower = sf_s.lower().strip()
                sf_o_norm = sf_o.lower().replace('é','e').replace('è','e').replace('ê','e').replace('à','a').replace('ù','u').replace('ô','o').replace('î','i').replace('ï','i').replace('ç','c')
                # Match sujet + objet (insensible aux accents)
                subject_match = (s_clean_lower == sf_s_lower or s_clean_lower in sf_s_lower or sf_s_lower in s_clean_lower)
                # Objet match fuzzy : substring OU forte similarité
                object_match = (o_lower_norm == sf_o_norm or sf_o_norm in o_lower_norm or o_lower_norm in sf_o_norm)
                if not object_match and len(sf_o_norm) >= 6 and len(o_lower_norm) >= 6:
                    # Fuzzy match : au moins 80% des caractères en commun
                    common = sum(1 for c in sf_o_norm if c in o_lower_norm)
                    ratio = common / max(len(sf_o_norm), 1)
                    object_match = ratio >= 0.75
                if subject_match and object_match:
                    # Vérifier la PERTINENCE : la question doit contenir des mots du SFT
                    sf_all_words = set((sf_s_lower + ' ' + sf_o_norm).split())
                    # Normaliser les accents des tokens de la question aussi
                    q_tokens_norm = set(t.replace('é','e').replace('è','e').replace('ê','e').replace('à','a').replace('ù','u').replace('ô','o').replace('î','i').replace('ï','i').replace('ç','c') for t in tokens)
                    relevance = len(sf_all_words & q_tokens_norm) / max(len(sf_all_words), 1)
                    if relevance > 0:
                        sft_amplitude = 1.0 + (amp - 1.0) * min(1.0, relevance * 3)  # boost proportionnel, max 3x relevance
                    break

            bonus = (bonus_sujet_exact * 0.5 + bonus_sujet_partial * 0.3 +
                     bonus_bigram * 0.5 + bonus_objet * 0.15 + bonus_rel * 0.10 +
                     bonus_structural * 0.6 + bonus_objet_exact * 0.5) / max(len(tokens), 1)

            # Score unifié (puissance pour amplifier les différences)
            score = (I ** W_I) * (max(P, 0.01) ** W_P) * (max(H_score, 0.01) ** W_H) * (max(D, 0.01) ** W_D)
            score += bonus * 0.15
            score *= sft_amplitude  # amplificateur SFT (1.0 par défaut, 5.0 pour faits validés)  # bonus plus fort qu'avant

            if score > 0.001:
                scored.append(((s, r, o, sec), score, {
                    'I': I, 'P': P, 'H': H_score, 'D': D, 'bonus': bonus
                }))

        # Trier + dédupliquer
        scored.sort(key=lambda x: -x[1])
        results, seen = [], set()
        for fact, score, diag in scored:
            if fact[0] not in seen:
                results.append((fact, score, diag))
                seen.add(fact[0])
            if len(results) >= max_results:
                break

        return results

    def _score_I(self, psi_q: np.ndarray, psi_f: np.ndarray, fid: int, tokens: List[str]) -> float:
        """
        I : Interférence directionnelle mots-à-mots.

        Pour chaque mot de la question, on cherche sa meilleure similarité
        cosinus avec les mots du fait. La moyenne donne le score I.

        Les verbes génériques (FR/EN) sont pénalisés (×0.2) car ils
        apparaissent dans trop de faits et ne sont pas discriminants.
        """
        if fid not in self.enc.fact_words:
            return 0.01

        fact_words = self.enc.fact_words[fid]
        fact_words_with_vecs = [fw for fw in fact_words if fw in self.enc.encoder.word_vectors]

        if not fact_words_with_vecs:
            return 0.01

        scores = []
        for t in tokens:
            if t not in self.enc.encoder.word_vectors:
                continue
            v_t = self.enc.encoder.word_vectors[t]

            # Meilleure similarité avec les mots du fait
            best_sim = 0.0
            for fw in fact_words_with_vecs:
                v_fw = self.enc.encoder.word_vectors[fw]
                sim = float(np.real(np.dot(v_t, np.conj(v_fw))))
                if sim > best_sim:
                    best_sim = sim

            # Pénaliser les verbes génériques (FR + EN)
            weight = 0.2 if t in _WEAK_WORDS else 1.0
            scores.append(max(0.0, best_sim) * weight)

        if not scores:
            return 0.01

        return sum(scores) / len(scores)

    def _score_P(self, tokens: List[str], fid: int) -> float:
        """P : cohérence PPMI entre les mots de la question et ceux du fait."""
        if fid not in self.enc.fact_words:
            return 0.01
        fact_words = self.enc.fact_words[fid]
        ppmi_sum = 0.0
        count = 0
        for t in tokens:
            if t in fact_words:
                ppmi_sum += 1.0  # co-occurrence directe = signal max
                count += 1
            elif t in self.enc.neighbors:
                for n, ppmi_val in self.enc.neighbors[t][:3]:
                    if n in fact_words:
                        ppmi_sum += ppmi_val * 0.5
                        count += 1
        return max(0.01, ppmi_sum / max(count, 1))

    def _score_H(self, psi_f: np.ndarray, h_unbind: np.ndarray) -> float:
        """H : résonance holographique — à quel point le fait vibre dans H⊗ψ_Q."""
        resonance = np.real(np.dot(psi_f, np.conj(h_unbind)))
        # Normalisation : tanh pour mapper dans [0,1] avec saturation douce
        return max(0.0, float(np.tanh(abs(resonance) * 50.0)))

    def _score_D(self, q_7d: List[float], fid: int) -> float:
        """D : alignement entre le domaine de la question et celui du fait."""
        if fid >= len(self.enc.fact_7d_vectors):
            return 0.3
        f_7d = self.enc.fact_7d_vectors[fid]
        dot = sum(q_7d[i] * f_7d[i] for i in range(C7))
        return max(0.0, min(1.0, dot))


# ═══════════════════════════════════════════════════════════════════════════════
# COUCHE 2a — CONSCIOUS VERIFIER (Conscient, ~10ms)
# ═══════════════════════════════════════════════════════════════════════════════

class ConsciousVerifier:
    """
    Vérification consciente des faits candidats.

    Phase A : Vérification de cohérence (interférence mutuelle des faits)
    Phase B : Expansion cross-domain si confiance basse
    Phase C : Synthèse ondulatoire ψ_R = Σ ψ_f
    """

    def __init__(self, encoder: UnifiedEncoder):
        self.enc = encoder

    def verify(self, question: str, candidates: List[Tuple[Tuple, float, Dict]],
               psi_q: np.ndarray) -> Tuple[List[Tuple], float, np.ndarray]:
        """
        Vérifie les candidats et synthétise l'onde de réponse.

        Returns:
            (faits_validés, confiance, ψ_R)
        """
        if not candidates:
            return [], 0.0, np.zeros(self.enc.dim, dtype=np.complex128)

        # Phase A : Vérification de cohérence
        validated, coherence_score = self._check_coherence(candidates)

        # Confiance = combinaison du meilleur score et de la cohérence
        top_score = candidates[0][1] if candidates else 0.0
        confidence = min(1.0, top_score * 1.5 + coherence_score * 0.5)

        # Phase B : Expansion cross-domain si confiance basse
        if confidence < CONF_MEDIUM and len(validated) < 2:
            expanded = self._cross_domain_expand(question, validated)
            if expanded:
                validated = expanded
                confidence = max(confidence, CONF_MEDIUM * 0.8)

        # Phase C : Synthèse ondulatoire ψ_R
        psi_R = self._synthesize_response_wave(validated)

        return validated, confidence, psi_R

    def _check_coherence(self, candidates: List[Tuple[Tuple, float, Dict]]
                         ) -> Tuple[List[Tuple], float]:
        """
        Vérifie la cohérence mutuelle des faits.

        Deux faits sont cohérents si leurs vecteurs d'onde interfèrent
        constructivement : Re(⟨ψ_f1 | ψ_f2⟩) > 0.
        Si interférence destructive (< 0) → contradiction → élimination du moins bon.
        """
        if len(candidates) <= 1:
            return [(f, s, d) for f, s, d in candidates], 0.5

        validated = []
        coherence_scores = []

        for i, (fact_i, score_i, diag_i) in enumerate(candidates):
            is_coherent = True
            for j, (fact_j, score_j, diag_j) in enumerate(candidates[:i]):
                if i == j:
                    continue
                fid_i = self._get_fact_id(fact_i)
                fid_j = self._get_fact_id(fact_j)
                if fid_i is not None and fid_j is not None:
                    psi_i = self.enc.fact_vectors[fid_i]
                    psi_j = self.enc.fact_vectors[fid_j]
                    interference = float(np.real(np.dot(psi_i, np.conj(psi_j))))
                    if interference < -0.1:  # interférence destructive → contradiction
                        is_coherent = False
                        break
                    coherence_scores.append(max(0.0, interference))

            if is_coherent:
                validated.append((fact_i, score_i, diag_i))

        avg_coherence = sum(coherence_scores) / max(len(coherence_scores), 1) if coherence_scores else 0.5
        return validated, min(1.0, avg_coherence * 2.0)

    def _get_fact_id(self, fact: Tuple) -> Optional[int]:
        """Trouve l'ID d'un fait dans la KB."""
        s, r, o, sec = fact
        for fid, (ks, kr, ko, ksec) in enumerate(self.enc.kb):
            if ks == s and kr == r and ko == o:
                return fid
        # Fallback : chercher par sujet
        for fid, (ks, kr, ko, ksec) in enumerate(self.enc.kb):
            if ks == s:
                return fid
        return None

    def _cross_domain_expand(self, question: str,
                             validated: List[Tuple]) -> List[Tuple]:
        """
        Expansion cross-domain : cherche dans d'autres secteurs.
        Utile quand les faits trouvés sont tous dans le même domaine.
        """
        if not validated:
            return []

        current_sectors = set(f[0][3] for f in validated if len(f[0]) > 3)
        tokens = self.enc._tokenize(question)

        cross_facts = []
        for fid in range(min(self.enc.N, 2000)):
            s, r, o, sec = self.enc.kb[fid]
            if sec in current_sectors:
                continue
            combined = f"{s} {r} {o}".lower()
            overlap = sum(1 for t in tokens if t in combined)
            if overlap >= 2:
                score = overlap / max(len(tokens), 1)
                cross_facts.append(((s, r, o, sec), score, {'I': score, 'P': 0.5, 'H': 0.3, 'D': 0.5}))

        cross_facts.sort(key=lambda x: -x[1])
        return cross_facts[:3] + validated

    def _synthesize_response_wave(self, validated: List[Tuple]) -> np.ndarray:
        """
        Synthèse ondulatoire : ψ_R = Σ ψ_f (superposition des faits validés).

        Les faits sont pondérés par leur score. La superposition amplifie
        les mots communs à plusieurs faits (interférence constructive).
        """
        if not validated:
            return np.zeros(self.enc.dim, dtype=np.complex128)

        psi_R = np.zeros(self.enc.dim, dtype=np.complex128)
        total_weight = 0.0

        for fact_tuple, score, diag in validated:
            fid = self._get_fact_id(fact_tuple)
            if fid is not None and fid < len(self.enc.fact_vectors):
                weight = score
                psi_R += weight * self.enc.fact_vectors[fid]
                total_weight += weight

        if total_weight > 0:
            psi_R /= total_weight

        return psi_R


# ═══════════════════════════════════════════════════════════════════════════════
# COUCHE 3 — WAVE DECODER (Livraison, ~5ms)
# ═══════════════════════════════════════════════════════════════════════════════

class WaveDecoder:
    """
    Décodeur ondulatoire avancé — transforme ψ_R + faits validés en langage naturel fluide.

    Principe : la réponse ÉMERGE de la structure de phase entre les faits validés.
    Les relations de phase déterminent les connecteurs logiques.

    Architecture :
      1. Faits validés → ordonnancement par score + proximité de phase
      2. Relations de phase → connecteurs logiques (et/car/cependant/de plus)
      3. Rendu naturel → phrase fluide sans template rigide
      4. Fallback → extraction Born + clustering si aucun fait validé
    """

    def __init__(self, encoder: UnifiedEncoder):
        self.enc = encoder
        self._cached_vocab_vectors = None

    def _ensure_vocab_vectors(self):
        """Pré-calcule les vecteurs du vocabulaire pour le fallback rapide."""
        if self._cached_vocab_vectors is not None:
            return
        self._cached_vocab_vectors = {}
        for w in self.enc.vocab[:3000]:
            if w in self.enc.encoder.word_vectors:
                self._cached_vocab_vectors[w] = self.enc.encoder.word_vectors[w]
        log.info(f"WaveDecoder: {len(self._cached_vocab_vectors)} mots pré-encodés")

    # ═════════════════════════════════════════════════════════════════════
    # DÉCODAGE PRINCIPAL
    # ═════════════════════════════════════════════════════════════════════

    def decode(self, psi_R: np.ndarray, question: str = "",
               validated_facts: List[Tuple] = None,
               lang: str = 'fr') -> str:
        """
        Décode en texte naturel — priorité aux faits validés.

        Args:
            psi_R: vecteur d'onde de réponse (ℂ⁵¹²)
            question: question originale
            validated_facts: liste de (fact_tuple, score, diagnostic)
            lang: 'fr' ou 'en'

        Returns:
            réponse fluide en langage naturel
        """
        # PRIORITÉ : utiliser les faits validés directement
        if validated_facts and len(validated_facts) > 0:
            return self._decode_from_facts(validated_facts, question, lang)

        # FALLBACK : décodage ondulatoire pur (règle de Born)
        return self._decode_from_wave(psi_R, question, lang)

    # ═════════════════════════════════════════════════════════════════════
    # DÉCODAGE DEPUIS LES FAITS VALIDÉS (chemin principal)
    # ═════════════════════════════════════════════════════════════════════

    def _decode_from_facts(self, validated_facts: List[Tuple],
                           question: str, lang: str) -> str:
        """
        Synthèse fluide à partir des faits validés.

        Stratégie :
          - Filtre les faits peu pertinents (score < 50% du meilleur)
          - 1 fait → phrase simple et propre
          - 2 faits cohérents → deux phrases connectées
          - 3+ faits très cohérents → mini-paragraphe
        """
        facts = []
        for fact_tuple, score, diag in validated_facts:
            s, r, o, sec = fact_tuple
            s_clean = _clean_fact_text(s)
            r_clean = _clean_fact_text(r)
            o_clean = _clean_fact_text(o)
            facts.append({
                's': s_clean, 'r': r_clean, 'o': o_clean, 'sec': sec,
                'score': score, 'diag': diag
            })

        if not facts:
            return self._fallback_not_found(question, lang)

        # Ordonner par score décroissant
        facts.sort(key=lambda f: -f['score'])

        # Filtrer : ne garder que les faits avec score >= 50% du meilleur
        best_score = facts[0]['score']
        facts = [f for f in facts if f['score'] >= best_score * 0.4]

        # Limiter à 3 faits maximum
        facts = facts[:3]

        # Détecter si la question demande une explication (plusieurs faits bienvenus)
        q_lower = question.lower()
        is_explanatory = any(w in q_lower for w in
            ('explique', 'explain', 'pourquoi', 'why', 'comment', 'how',
             'decris', 'describe', 'parle', 'tell'))

        # 1 seul fait ou question non-explicative → phrase simple
        if len(facts) == 1 or not is_explanatory:
            return self._render_single_fact(facts[0], question, lang)

        # 2 faits → deux phrases connectées
        if len(facts) == 2:
            return self._render_two_facts(facts[0], facts[1], question, lang)

        # 3 faits → paragraphe structuré
        return self._render_paragraph(facts, question, lang)

    def _render_single_fact(self, fact: dict, question: str, lang: str) -> str:
        """Rend un fait unique en phrase naturelle."""
        s, r, o = fact['s'], fact['r'], fact['o']

        # Capitaliser le sujet
        s_display = s[0].upper() + s[1:] if s else s

        # Choisir le format selon le type de relation
        r_lower = r.lower()

        # Relations d'identité : "X est Y" → "X est Y."
        if any(v in r_lower for v in ('est', 'is', 'sont', 'are')):
            return f"{s_display} {r} {o}."

        # Relations de découverte/création : "X a découvert Y" → "X a découvert Y."
        if any(v in r_lower for v in ('a découvert', 'a peint', 'a écrit', 'a inventé',
                                       'discovered', 'painted', 'wrote', 'invented')):
            return f"{s_display} {r} {o}."

        # Relations de localisation : "X se trouve à Y"
        if any(v in r_lower for v in ('capitale', 'capital', 'situé', 'located')):
            return f"{s_display} {r} {o}."

        # Format générique
        return f"{s_display} {r} {o}."

    def _render_two_facts(self, f1: dict, f2: dict, question: str, lang: str) -> str:
        """Deux faits connectés par une relation de phase."""
        # Déterminer le connecteur selon la relation de phase entre les deux faits
        connector = self._phase_connector(f1, f2, lang)

        sentence1 = self._render_single_fact(f1, question, lang).rstrip('.')
        sentence2 = self._render_single_fact(f2, question, lang)
        # Minuscule pour la deuxième phrase si connecteur
        if connector and sentence2:
            sentence2 = sentence2[0].lower() + sentence2[1:]

        return f"{sentence1}. {connector}{sentence2}"

    def _render_paragraph(self, facts: List[dict], question: str, lang: str) -> str:
        """Paragraphe structuré pour 3+ faits."""
        if not facts:
            return self._fallback_not_found(question, lang)

        intro_words = {
            'fr': ['D\'abord, ', 'En premier lieu, ', 'Fondamentalement, '],
            'en': ['First, ', 'Primarily, ', 'Fundamentally, '],
        }
        mid_connectors = {
            'fr': ['De plus, ', 'Par ailleurs, ', 'En outre, ', 'Également, '],
            'en': ['Moreover, ', 'Furthermore, ', 'Additionally, ', 'Also, '],
        }
        conclusion_words = {
            'fr': ['En résumé, ', 'Ainsi, ', 'En définitive, '],
            'en': ['In summary, ', 'Thus, ', 'Ultimately, '],
        }

        intro = intro_words[lang][hash(question) % len(intro_words[lang])]
        concl = conclusion_words[lang][hash(question + 'end') % len(conclusion_words[lang])]

        sentences = []
        # Première phrase avec intro
        first = self._render_single_fact(facts[0], question, lang)
        if first and first[0].isupper():
            first = first[0].lower() + first[1:]
        sentences.append(intro + first.rstrip('.') + '.')

        # Phrases du milieu avec connecteurs variés
        for i, fact in enumerate(facts[1:-1], 1):
            conn = mid_connectors[lang][(i-1) % len(mid_connectors[lang])]
            s = self._render_single_fact(fact, question, lang)
            if s and s[0].isupper():
                s = s[0].lower() + s[1:]
            sentences.append(conn + s.rstrip('.') + '.')

        # Dernière phrase avec conclusion
        if len(facts) >= 3:
            last = self._render_single_fact(facts[-1], question, lang)
            if last and last[0].isupper():
                last = last[0].lower() + last[1:]
            sentences.append(concl + last.rstrip('.') + '.')

        return ' '.join(sentences)

    def _phase_connector(self, f1: dict, f2: dict, lang: str) -> str:
        """
        Détermine le connecteur logique selon la relation de phase entre deux faits.

        Phase = cos(ψ_f1, ψ_f2) ∈ [-1, 1]
          - cos > 0.7  : même sujet → "et" / "and"
          - cos > 0.3  : sujets liés → "de plus" / "moreover"
          - cos > -0.1 : sujets distincts → "par ailleurs" / "furthermore"
          - cos < -0.1 : sujets opposés → "cependant" / "however"
        """
        # Calculer la similarité de phase via les vecteurs de fait
        fid1 = self._find_fact_id(f1)
        fid2 = self._find_fact_id(f2)

        if fid1 is not None and fid2 is not None:
            psi1 = self.enc.fact_vectors[fid1]
            psi2 = self.enc.fact_vectors[fid2]
            phase_cos = float(np.real(np.dot(psi1, np.conj(psi2))))
        else:
            # Fallback : similarité des sujets
            s1_words = set(f1['s'].lower().split())
            s2_words = set(f2['s'].lower().split())
            overlap = len(s1_words & s2_words)
            phase_cos = min(1.0, overlap / max(len(s1_words | s2_words), 1))

        if lang == 'fr':
            if phase_cos > 0.7:
                return 'Et '
            elif phase_cos > 0.3:
                return 'De plus, '
            elif phase_cos > -0.1:
                return 'Par ailleurs, '
            else:
                return 'Cependant, '
        else:
            if phase_cos > 0.7:
                return 'And '
            elif phase_cos > 0.3:
                return 'Moreover, '
            elif phase_cos > -0.1:
                return 'Furthermore, '
            else:
                return 'However, '

    def _find_fact_id(self, fact_dict: dict) -> Optional[int]:
        """Trouve l'ID d'un fait dans la KB encodée."""
        s, r, o = fact_dict['s'], fact_dict['r'], fact_dict['o']
        for fid, (ks, kr, ko, ksec) in enumerate(self.enc.kb):
            ks_clean = _clean_fact_text(ks).lower()
            ko_clean = _clean_fact_text(ko).lower()
            if ks_clean == s.lower() and ko_clean == o.lower():
                return fid
        return None

    # ═════════════════════════════════════════════════════════════════════
    # FALLBACK : DÉCODAGE ONDULATOIRE PUR (règle de Born)
    # ═════════════════════════════════════════════════════════════════════

    def _decode_from_wave(self, psi_R: np.ndarray, question: str, lang: str) -> str:
        """Fallback : extraction des mots résonnants depuis ψ_R."""
        self._ensure_vocab_vectors()

        norm_R = np.sqrt(np.sum(np.abs(psi_R)**2))
        if norm_R < 1e-10:
            return self._fallback_not_found(question, lang)

        resonant_words = self._extract_resonant_words(psi_R, question, top_k=20)
        if not resonant_words:
            return self._fallback_not_found(question, lang)

        # Prendre les 3-5 mots les plus résonnants
        top_words = [w for w, s in resonant_words[:5] if s > 0.01]
        if len(top_words) < 2:
            return self._fallback_not_found(question, lang)

        if lang == 'fr':
            mots_str = ', '.join(top_words[:-1]) + ' et ' + top_words[-1]
            return f"Ce sujet est lié aux concepts suivants : {mots_str}."
        else:
            words_str = ', '.join(top_words[:-1]) + ' and ' + top_words[-1]
            return f"This topic relates to the following concepts: {words_str}."

    def _extract_resonant_words(self, psi_R: np.ndarray, question: str,
                                top_k: int = 20) -> List[Tuple[str, float]]:
        """Règle de Born : résonance(w) = |⟨ψ_w | ψ_R⟩|²."""
        scores = []
        for word, v_w in self._cached_vocab_vectors.items():
            amplitude = float(np.real(np.dot(v_w, np.conj(psi_R))))
            resonance = amplitude ** 2
            if resonance > 0.001:
                scores.append((word, resonance))

        scores.sort(key=lambda x: -x[1])

        # Filtrer les mots de la question
        q_tokens = set(self.enc._tokenize(question) if question else [])
        scores = [(w, s) for w, s in scores if w not in q_tokens]

        return scores[:top_k]

    # ═════════════════════════════════════════════════════════════════════
    # FALLBACK ULTIME
    # ═════════════════════════════════════════════════════════════════════

    def _fallback_not_found(self, question: str, lang: str) -> str:
        """Message de fallback quand aucune information n'est trouvée."""
        sujet = question.strip('?.,!;: ') if question else "ce sujet"
        sujet = sujet[:80]  # tronquer
        if lang == 'fr':
            return f"Je ne trouve pas assez d'informations sur {sujet} dans ma base de connaissances."
        return f"I don't have enough information about {sujet} in my knowledge base."


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL — Orchestration des 4 couches
# ═══════════════════════════════════════════════════════════════════════════════

class SemanticPipeline:
    """
    Pipeline sémantique harmonique unifié.

    Remplace les 7+ fallbacks de harmonic_ai.ask() par un seul flux
    déterministe en 4 couches :

      Couche 1 (Inconscient)  → UnifiedRetriever   : scoring I×P×H×D
      Couche 2 (Conscient)    → ConsciousVerifier   : vérification + ψ_R
      Couche 3 (Livraison)    → WaveDecoder         : décodage → texte

    Usage:
        pipeline = SemanticPipeline(knowledge_base)
        result = pipeline.process("explique la lumiere")
        print(result.response)
    """

    def __init__(self, knowledge_base: List[Tuple[str, str, str, str]],
                 dim: int = 512, enable_creative: bool = False):
        t0 = time.time()

        # Couche 0 — Encodage (une seule fois)
        self.encoder = UnifiedEncoder(knowledge_base, dim=dim)

        # Couche 1 — Retrieval
        self.retriever = UnifiedRetriever(self.encoder)

        # Couche 2 — Vérification consciente
        self.verifier = ConsciousVerifier(self.encoder)

        # Couche 3 — Décodage
        self.decoder = WaveDecoder(self.encoder)

        # Dialogue créatif (optionnel)
        self.creative_dialogue = None
        if enable_creative:
            try:
                from creative_dialogue import CreativeDialogue
                self.creative_dialogue = CreativeDialogue(
                    knowledge_base,
                    retriever=None  # on utilise notre propre retriever
                )
            except ImportError:
                pass

        self._init_time = time.time() - t0
        log.info(f"SemanticPipeline initialisé en {self._init_time:.1f}s "
                 f"({len(knowledge_base)} faits)")

    def process(self, question: str, lang: str = 'fr',
                max_facts: int = 5) -> PipelineResult:
        """
        Traitement complet d'une question.

        Args:
            question: question en langage naturel
            lang: langue ('fr' ou 'en')
            max_facts: nombre max de faits à retourner

        Returns:
            PipelineResult avec réponse, confiance, diagnostics
        """
        t_start = time.time()

        # ── Couche 1 : Retrieval Inconscient ──
        t1 = time.time()
        candidates = self.retriever.retrieve(question, max_results=max_facts)
        retrieval_time = (time.time() - t1) * 1000

        # ── Couche 2 : Vérification Consciente + Synthèse ψ_R ──
        psi_q = self.encoder.encode_query(question)
        validated, confidence, psi_R = self.verifier.verify(question, candidates, psi_q)

        # Si confiance basse et dialogue créatif activé
        layer_used = "unified"
        if confidence < CONF_MEDIUM and self.creative_dialogue:
            try:
                creative_facts, _, creative_score = self.creative_dialogue.create(
                    question, max_iterations=3
                )
                if creative_facts and creative_score > 0.3:
                    validated = creative_facts[:3]
                    confidence = max(confidence, creative_score * 0.7)
                    layer_used = "creative"
                    # Re-synthétiser ψ_R avec les faits créatifs
                    psi_R = self.verifier._synthesize_response_wave(
                        [(f, 0.5, {}) for f in validated]
                    )
            except Exception:
                pass

        # ── Couche 3 : Décodage Ondulatoire ──
        t3 = time.time()
        response = self.decoder.decode(
            psi_R, question=question,
            validated_facts=validated,
            lang=lang
        )
        decode_time = (time.time() - t3) * 1000

        # Si toujours pas de réponse satisfaisante → fallback
        if not response or len(response) < 15:
            response = self.decoder._fallback_not_found(question, lang)
            layer_used = "fallback"

        total_time = (time.time() - t_start) * 1000

        # Collecter les diagnostics
        phase_scores = {}
        if candidates:
            best_diag = candidates[0][2] if candidates else {}
            phase_scores = {
                'I': best_diag.get('I', 0),
                'P': best_diag.get('P', 0),
                'H': best_diag.get('H', 0),
                'D': best_diag.get('D', 0),
            }

        facts_used = [f[0] for f in validated] if validated else []

        return PipelineResult(
            response=response,
            confidence=confidence,
            facts_used=facts_used,
            phase_scores=phase_scores,
            retrieval_time_ms=retrieval_time,
            decode_time_ms=decode_time,
            total_time_ms=total_time,
            layer_used=layer_used,
        )

    def process_batch(self, questions: List[str], lang: str = 'fr'
                      ) -> List[PipelineResult]:
        """Traite un lot de questions."""
        return [self.process(q, lang=lang) for q in questions]

    @property
    def stats(self) -> dict:
        """Statistiques du pipeline."""
        return {
            'faits': self.encoder.N,
            'vocabulaire': len(self.encoder.vocab),
            'mots_encoder': self.encoder.encoder.vocab_size,
            'liens_ppmi': sum(len(v) for v in self.encoder.neighbors.values()),
            'init_time_s': round(self._init_time, 1),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE CONVENIENCE
# ═══════════════════════════════════════════════════════════════════════════════

def create_pipeline(knowledge_base: List[Tuple[str, str, str, str]],
                    dim: int = 512) -> SemanticPipeline:
    """
    Crée un pipeline sémantique prêt à l'emploi.

    Usage:
        from unified_semantic_pipeline import create_pipeline
        pipeline = create_pipeline(harmonic_ai.model.knowledge_base)
        result = pipeline.process("explique la lumière")
    """
    return SemanticPipeline(knowledge_base, dim=dim)


# ═══════════════════════════════════════════════════════════════════════════════
# AUTO-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # Base de test
    test_kb = [
        ("lumiere", "est une", "onde electromagnetique", "PHYSIQUE_FOND"),
        ("lumiere", "se deplace a", "300000 km/s", "PHYSIQUE_FOND"),
        ("lumiere", "est composee de", "photons", "PHYSIQUE_FOND"),
        ("einstein", "a decouvert", "la relativite", "PHYSIQUE_FOND"),
        ("relativite", "unifie", "espace et temps", "PHYSIQUE_FOND"),
        ("gravite", "est", "la courbure de l espace temps", "PHYSIQUE_FOND"),
        ("tokyo", "est la capitale du", "japon", "GEOGRAPHIE"),
        ("paris", "est la capitale de", "la france", "GEOGRAPHIE"),
        ("berlin", "est la capitale de", "l allemagne", "GEOGRAPHIE"),
        ("leonard de vinci", "a peint", "la joconde", "ART"),
        ("joconde", "est aussi appelee", "mona lisa", "ART"),
        ("musique", "est", "l art des sons", "MUSIQUE"),
        ("phi", "est le", "nombre d or", "MATHS_PURES"),
        ("phi", "vaut", "1.618", "MATHS_PURES"),
        ("conscience", "est", "la perception de soi et du monde", "CONSCIENCE"),
    ]

    print("=" * 60)
    print("Initialisation du pipeline...")
    pipeline = SemanticPipeline(test_kb)
    print(f"Stats: {pipeline.stats}")

    questions = [
        "explique la lumiere",
        "quelle est la capitale du japon",
        "qui a peint la joconde",
        "qu est ce que le nombre d or",
        "explique la relativite",
    ]

    print("\n" + "=" * 60)
    for q in questions:
        print(f"\nQ: {q}")
        result = pipeline.process(q)
        print(f"R: {result.response}")
        print(f"   Confiance: {result.confidence:.2f} | "
              f"I={result.phase_scores.get('I', 0):.2f} "
              f"P={result.phase_scores.get('P', 0):.2f} "
              f"H={result.phase_scores.get('H', 0):.2f} "
              f"D={result.phase_scores.get('D', 0):.2f} | "
              f"{result.total_time_ms:.1f}ms [{result.layer_used}]")
