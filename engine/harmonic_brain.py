"""
Harmonic Brain — Architecture Cerveau Humain Ondulatoire
==========================================================
Inspiré du modèle conscient/inconscient du cerveau humain.

ARCHITECTURE :
  ┌─────────────────────────────────────────────────────────┐
  │           INCONSCIENT (HolographicStore)                 │
  │  · Stocke TOUT sans filtrer : H += ψ_f                  │
  │  · Retrieval pur par résonance : H ⊗ ψ_Q               │
  │  · Apprentissage par RÉPÉTITION : amplitude += 1       │
  │  · Rumination (sommeil) : consolidation périodique      │
  │  · Oubli naturel φ⁻ᵗ (noyau ABC)                       │
  └────────────────────────┬────────────────────────────────┘
                           │
                           ▼  flux brut (tous les faits résonnants)
  ┌─────────────────────────────────────────────────────────┐
  │             CONSCIENT (ConsciousFilter)                  │
  │  · Filtre par COHÉRENCE MUTUELLE                        │
  │  · Applique les SFT (vérités ancrées)                   │
  │  · FEEDBACK → Inconscient (renforce/affaiblit)          │
  │  · Capacité limitée : traite N ≤ 10 faits               │
  └────────────────────────┬────────────────────────────────┘
                           │
                           ▼  faits validés (1-3)
                    ┌──────────────┐
                    │  EXPRESSION   │
                    │  (WaveDecoder)│
                    └──────────────┘

PRINCIPE FONDATEUR :
  L'inconscient enregistre sans comprendre.
  Le sens ÉMERGE par répétition + interférence.
  Le conscient ne JUGE que ce qui remonte — il ne stocke rien.

Usage:
    from harmonic_brain import HarmonicBrain

    brain = HarmonicBrain(knowledge_base)
    brain.ingest("La lumière est une onde électromagnétique.")
    brain.ingest_corpus("data/corpus/")
    brain.ruminate()  # consolidation nocturne

    result = brain.process("explique la lumière")
    print(result.response)  # fluide, validé par le conscient
"""

import math, time, logging, re
from collections import defaultdict, Counter
from typing import List, Tuple, Dict, Set, Optional
from dataclasses import dataclass, field
import numpy as np
from pathlib import Path
import sys

_MODULE_DIR = Path(__file__).resolve().parent
if str(_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULE_DIR))

from holographic_encoder import (
    HolographicEncoder, _circular_convolve, _circular_correlate,
    _fnv1a_hash, build_holographic_waves
)

# 🌐 Web Retriever — connecte l'IA à Internet
_WEB_RETRIEVER = None
try:
    from web_retriever import WebRetriever
    _WEB_RETRIEVER = WebRetriever()
    log = logging.getLogger(__name__)
    log.info("🌐 WebRetriever chargé — recherche Internet disponible")
except Exception as e:
    log = logging.getLogger(__name__)
    log.warning(f"WebRetriever non disponible: {e}")

# 🔗 Phase Amplifier — propagation ψ profonde
_PHASE_AMPLIFIER_AVAILABLE = False
try:
    from phase_amplifier import PhaseAmplifier, deep_reason
    _PHASE_AMPLIFIER_AVAILABLE = True
except ImportError:
    PhaseAmplifier = None
    deep_reason = None

# 🧪 Few-Shot Injector — apprentissage par injection temporaire
_FEW_SHOT_AVAILABLE = False
try:
    from few_shot_injector import FewShotInjector
    _FEW_SHOT_AVAILABLE = True
except ImportError:
    FewShotInjector = None

# 🎯 Harmonic Attention — ψ contextuels dynamiques
_HARMONIC_ATTENTION_AVAILABLE = False
try:
    from harmonic_attention import HarmonicAttention, ContextualEncoder
    _HARMONIC_ATTENTION_AVAILABLE = True
except ImportError:
    HarmonicAttention = None
    ContextualEncoder = None

# 📚 Apprentissage continu
_WAVE_FINE_TUNE_AVAILABLE = False
try:
    from wave_fine_tune import WaveFineTuner
    _WAVE_FINE_TUNE_AVAILABLE = True
except ImportError:
    WaveFineTuner = None

_FAST_LEARNER_AVAILABLE = False
try:
    from fast_learner import FastLearner
    _FAST_LEARNER_AVAILABLE = True
except ImportError:
    FastLearner = None

_FEEDBACK_LOOP_AVAILABLE = False
try:
    from feedback_loop import FeedbackLoop
    _FEEDBACK_LOOP_AVAILABLE = True
except ImportError:
    FeedbackLoop = None

# FastLearner et WaveFineTuner sont importés lazy (dans __init__)
# pour éviter l'import circulaire (fast_learner importe HarmonicBrain)

# FeedbackLoop
_FEEDBACK_LOOP_AVAILABLE = False
try:
    from feedback_loop import FeedbackLoop
    _FEEDBACK_LOOP_AVAILABLE = True
except ImportError:
    FeedbackLoop = None

try:
    from harmonic_quality import HIGH_AMPLITUDE_FACTS
except ImportError:
    HIGH_AMPLITUDE_FACTS = {}

# Spectral Embedding (plongement sémantique ondulatoire)
_SPECTRAL = None
try:
    from spectral_embedding import _SPECTRAL as _spec
    _SPECTRAL = _spec
except ImportError:
    pass

# Prompt Parser (parseur ondulatoire de question)
from prompt_parser import PromptParser, StructuredPrompt

# Conscient Intelligent (raisonnement, pas juste filtrage)
from conscious_intelligence import ConsciousIntelligence

# Domaines de raisonnement (adaptateur multi-domaine)
from wave_domains import DomainAdapter, DOMAINS

# 🔥 Composer de réponses naturelles (30+ micro-structures)
try:
    from response_composer import ResponseComposer
except ImportError:
    ResponseComposer = None

# 🔥 Analyseur de question (détection d'intention)
try:
    from question_analyzer import analyze_question as _analyze_q
except ImportError:
    _analyze_q = None

# 🔥 Module Mathématique (micro-calculateur déterministe, 100% précis)
try:
    from wave_math import wave_solve as try_math_solve
except ImportError:
    try:
        from math_bridge import try_math_solve
    except ImportError:
        try_math_solve = None

# 🔥 Logique Ondulatoire (syllogisme, déduction, induction)
try:
    from wave_logic import WaveLogic
except ImportError:
    WaveLogic = None

# 🔥 Raisonnement par propagation (chaîne de résonance)
try:
    from wave_reasoning import WaveReasoner
except ImportError:
    WaveReasoner = None

# 🔥 Conversation multi-tours (contexte ψ ondulatoire)
try:
    from wave_conversation import WaveConversation
except ImportError:
    WaveConversation = None

log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI
TAU = 2.0 * math.pi

# Poids de feedback conscient → inconscient
ALPHA_REINFORCE = 0.1   # renforcement (acceptation)
ALPHA_WEAKEN = 0.05     # affaiblissement (rejet)

# Seuils
RESONANCE_THRESHOLD = 0.01  # seuil minimal pour qu'un fait remonte
COHERENCE_THRESHOLD = 0.3   # seuil de cohérence mutuelle

# Stopwords
_STOPWORDS = {
    'the','a','an','is','are','was','were','of','in','on','at','to',
    'for','with','by','from','and','it','its','that','this',
    'these','those','which','who','whom','what','when','where','why','how',
    'le','la','les','un','une','des','de','du','d','l','est','sont',
    'a','ont','que','qui','quoi','dont','dans','sur','pour','par',
    'avec','et','il','elle','ils','elles','ce','cet','cette','ces',
}


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def _clean_text(text: str) -> str:
    """Nettoie un texte (préfixes numériques, années, espaces)."""
    text = re.sub(r'^\d+[\.\)]\s*', '', text.strip())
    text = re.sub(r'\s*\(\d{4}[\-\–]\d{4}\)\s*', ' ', text)
    text = re.sub(r'\s*\(\d{4}\)\s*', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def _split_camel_snake(text: str) -> str:
    """Découpe camelCase et snake_case en mots séparés pour le matching technique."""
    text = re.sub(r'_+', ' ', text)
    text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)
    text = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', ' ', text)
    return text

def _tokenize(text: str) -> List[str]:
    """Tokenisation avec stopwords + termes techniques."""
    text = text.replace("'", " ").replace("'", " ")
    text = _split_camel_snake(text)
    tokens = [w.strip('.,!?;:()[]{}«»\"') for w in text.lower().split()
              if len(w) >= 2 and w not in _STOPWORDS]
    extra = []
    for t in tokens:
        if '.' in t:
            extra.append(t.replace('.', ''))
    return tokens + extra

def _normalize(text: str) -> str:
    """Normalise un texte (accents, casse, symboles grecs)."""
    return text.lower().replace('é','e').replace('è','e').replace('ê','e')\
               .replace('à','a').replace('ù','u').replace('ô','o')\
               .replace('î','i').replace('ï','i').replace('ç','c')\
               .replace('φ','phi').replace('α','alpha').replace('β','beta')\
               .replace('γ','gamma').replace('δ','delta').replace('ψ','psi')


# ═══════════════════════════════════════════════════════════════════════════════
# DATACLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class FactRecord:
    """Un fait stocké dans l'inconscient avec ses métadonnées."""
    sujet: str
    relation: str
    objet: str
    secteur: str
    psi: np.ndarray          # vecteur d'onde du fait (ℂ⁵¹²)
    amplitude: float = 1.0   # renforcée par répétition
    count: int = 1           # nombre d'ingestions
    last_seen: float = 0.0   # timestamp dernier accès
    confidence: float = 0.5  # mise à jour par le conscient
    times_retrieved: int = 0 # combien de fois remonté
    times_accepted: int = 0  # combien de fois validé par le conscient

@dataclass
class BrainResult:
    """Résultat du processus cerveau complet."""
    response: str
    confidence: float
    facts_used: List[FactRecord]
    facts_rejected: List[FactRecord]
    retrieval_count: int     # combien de faits sont remontés de l'inconscient
    total_time_ms: float


# ═══════════════════════════════════════════════════════════════════════════════
# INCONSCIENT — HolographicStore
# ═══════════════════════════════════════════════════════════════════════════════

class HolographicStore:
    """
    L'INCONSCIENT — mémoire holographique massive et passive.

    Principes :
      - Stocke TOUT sans filtrer : H += ψ_f (superposition additive)
      - Retrieval pur par résonance : H ⊗ ψ_Q → tous les faits qui vibrent
      - Apprentissage par RÉPÉTITION : même fait → amplitude += 1
      - Aucun jugement de valeur — le conscient juge, pas l'inconscient
      - Oubli naturel par le noyau ABC (φ⁻ᵗ)
    """

    def __init__(self, dim: int = 512, use_holographic: bool = True):
        self.dim = dim
        self.use_holographic = use_holographic
        self.encoder = HolographicEncoder(dim=dim) if use_holographic else None

        # L'hologramme : superposition de TOUS les faits
        self.hologram = np.zeros(dim, dtype=np.complex128)

        # Registre des faits (pour le feedback conscient)
        self.registry: Dict[Tuple[str, str, str], FactRecord] = {}

        # Index inversé (pour lookup rapide, pas pour juger)
        self.word_index: Dict[str, Set[Tuple[str, str, str]]] = defaultdict(set)

        # 🔥 Index sous-mot → clés multi-mots (pour retrieval rapide)
        # Ex: "peint" → ["a peint"] → permet de matcher "peint" avec "a peint"
        self._subword_index: Dict[str, List[Tuple[str, np.ndarray]]] = None  # lazy build

        # 🔥 IDF (Inverse Document Frequency) pour scoring lexical
        self._idf: Dict[str, float] = None  # lazy build
        self._total_docs: int = 0

        # 🔥 Spectral Embedding (similarité sémantique ondulatoire)
        self._spectral = _SPECTRAL
        self._spectral_ready = (self._spectral is not None and
                                self._spectral.is_ready and
                                len(self._spectral.phases) > 100)
        self._spectral_quality = 0.0  # sera calibré automatiquement
        self._spectral_neighbors: Dict[str, List[Tuple[str, float]]] = None  # lazy

        # Compteurs
        self.total_ingested = 0
        self.total_retrieved = 0
        self._last_rumination = time.time()

    def _build_subword_index(self):
        """Construit l'index sous-mot → clés multi-mots (appelé une fois)."""
        if self._subword_index is not None:
            return
        self._subword_index = defaultdict(list)
        if self.encoder is not None:
            for key, vec in self.encoder.word_vectors.items():
                for sub in key.split():
                    if len(sub) >= 2:
                        self._subword_index[sub].append((key, vec))
            log.info(f"Subword index: {len(self._subword_index)} sous-mots")

    def _calibrate_spectral(self):
        """
        Évalue la qualité du plongement spectral en mesurant la similarité
        de paires de mots connus pour être sémantiquement liés.

        quality = 0.0 → phases aléatoires (bruit)
        quality = 1.0 → phases parfaitement corrélées au sens
        """
        if not self._spectral_ready:
            self._spectral_quality = 0.0
            return

        # Paires de référence : mots qui DEVRAIENT avoir des phases proches
        reference_pairs = [
            ('lumiere', 'onde'), ('capitale', 'ville'), ('paris', 'france'),
            ('guerre', 'paix'), ('eau', 'mer'), ('musique', 'art'),
            ('livre', 'roman'), ('roi', 'reine'),
        ]
        # Paires de contrôle
        control_pairs = [
            ('lumiere', 'tracteur'), ('capitale', 'fromage'), ('peintre', 'volcan'),
            ('musique', 'beton'), ('roi', 'microbe'),
        ]

        ref_sims = []
        for w1, w2 in reference_pairs:
            sim = self._spectral.get_similarity(w1, w2)
            if sim is not None:
                ref_sims.append(max(0, sim))

        ctrl_sims = []
        for w1, w2 in control_pairs:
            sim = self._spectral.get_similarity(w1, w2)
            if sim is not None:
                ctrl_sims.append(max(0, sim))

        if not ref_sims:
            self._spectral_quality = 0.0
        else:
            avg_ref = sum(ref_sims) / len(ref_sims)
            avg_ctrl = sum(ctrl_sims) / len(ctrl_sims) if ctrl_sims else 0.5
            # Qualité = combien les paires liées sont plus similaires que les paires aléatoires
            quality = max(0.0, min(1.0, (avg_ref - avg_ctrl) * 3.0))
            self._spectral_quality = quality

        log.info(f"Qualité spectrale: {self._spectral_quality:.2f} "
                 f"(0=bruit, 1=parfait) → poids sémantique = {0.2 * self._spectral_quality:.0%}")

    def _build_idf(self):
        """Construit les scores IDF pour tous les mots (appelé une fois)."""
        if self._idf is not None:
            return
        self._idf = {}
        self._total_docs = len(self.registry)
        word_doc_count = Counter()
        for key, record in self.registry.items():
            fact_text = f"{_normalize(record.sujet)} {_normalize(record.relation)} {_normalize(record.objet)}"
            unique_words = set(_tokenize(fact_text))
            for w in list(unique_words):
                for sub in w.split():
                    if len(sub) >= 2:
                        unique_words.add(sub)
            for w in unique_words:
                word_doc_count[w] += 1
        for w, df in word_doc_count.items():
            self._idf[w] = math.log(self._total_docs / max(df, 1)) + 1.0
        log.info(f"IDF: {len(self._idf)} mots indexés")

        # Auto-calibrer la qualité spectrale
        if self._spectral_ready:
            self._calibrate_spectral()
        """Construit les scores IDF pour tous les mots (appelé une fois)."""
        if self._idf is not None:
            return
        self._idf = {}
        self._total_docs = len(self.registry)
        # Compter dans combien de faits chaque mot apparaît
        word_doc_count = Counter()
        for key, record in self.registry.items():
            fact_text = f"{_normalize(record.sujet)} {_normalize(record.relation)} {_normalize(record.objet)}"
            unique_words = set(_tokenize(fact_text))
            # Ajouter aussi les sous-mots
            for w in list(unique_words):
                for sub in w.split():
                    if len(sub) >= 2:
                        unique_words.add(sub)
            for w in unique_words:
                word_doc_count[w] += 1
        # IDF = log(N / df)
        for w, df in word_doc_count.items():
            self._idf[w] = math.log(self._total_docs / max(df, 1)) + 1.0
        log.info(f"IDF: {len(self._idf)} mots indexés")

        # Auto-calibrer la qualité spectrale
        if self._spectral_ready:
            self._calibrate_spectral()

    # ── INGESTION ─────────────────────────────────────────────────────────

    def ingest(self, sujet: str, relation: str, objet: str,
               secteur: str = "GENERAL") -> FactRecord:
        """
        Ingère un fait sans aucun filtre.

        Si le fait existe déjà → renforce (amplitude += 1).
        Sinon → crée un nouveau fait.
        """
        s = _clean_text(sujet)
        r = _clean_text(relation)
        o = _clean_text(objet)
        # Normaliser les accents pour la clé
        key = (_normalize(s).strip(), _normalize(r).strip(), _normalize(o).strip())

        now = time.time()

        # Fait déjà connu ? → RENFORCER
        if key in self.registry:
            record = self.registry[key]
            record.count += 1
            record.amplitude += 1.0
            record.last_seen = now
            # Renforcer dans l'hologramme
            self.hologram += record.psi  # superposition additive
            self.total_ingested += 1
            return record

        # Nouveau fait → ENREGISTRER
        if self.use_holographic and self.encoder:
            psi_f = self.encoder.encode_fact(s, r, o)
        else:
            psi_f = np.zeros(self.dim or 64, dtype=np.complex128)  # Pas d'encodage ℂ

        record = FactRecord(
            sujet=s, relation=r, objet=o, secteur=secteur,
            psi=psi_f, amplitude=1.0, count=1, last_seen=now
        )

        self.registry[key] = record
        self.hologram += psi_f  # superposition

        # Indexer les mots (version normalisée pour la recherche)
        for w in _tokenize(f"{_normalize(s)} {_normalize(r)} {_normalize(o)}"):
            self.word_index[w].add(key)

        self.total_ingested += 1
        return record

    def ingest_batch(self, facts: List[Tuple[str, str, str, str]]) -> int:
        """Ingère un lot de faits. Retourne le nombre de nouveaux."""
        new_count = 0
        for s, r, o, sec in facts:
            key = (s.lower().strip(), r.lower().strip(), o.lower().strip())
            if key not in self.registry:
                new_count += 1
            self.ingest(s, r, o, sec)
        return new_count

    # ── RETRIEVAL PUR ─────────────────────────────────────────────────────

    def retrieve(self, question: str, threshold: float = RESONANCE_THRESHOLD,
                 max_results: int = 50) -> List[Tuple[FactRecord, float]]:
        """Retrieval PUR — TF-IDF lexical + bonus spectral."""
        self._build_subword_index()
        self._build_idf()

        q_tokens = _tokenize(_normalize(question))
        if not q_tokens:
            return []

        # 🔥 Ajouter les bigrammes "X Y" issus de "X d Y" (ex: "nombre d or" → "nombre or")
        raw_toks = _normalize(question).split()
        for i in range(len(raw_toks) - 2):
            if raw_toks[i+1] == 'd' and len(raw_toks[i]) >= 2 and len(raw_toks[i+2]) >= 2:
                q_tokens.append(f"{raw_toks[i]} {raw_toks[i+2]}")
        # Bigrammes consécutifs
        for i in range(len(q_tokens) - 1):
            q_tokens.append(f"{q_tokens[i]} {q_tokens[i+1]}")

        # 🔥 Verbes communs à ignorer (sauf si c'est le seul token)
        _COMMON_VERBS = {'explique', 'est', 'sont', 'fait', 'donne', 'permet', 'dit',
                         'explain', 'is', 'are', 'does', 'make', 'allows', 'says'}
        significant_tokens = [t for t in q_tokens if t not in _COMMON_VERBS]
        if significant_tokens:
            q_tokens = significant_tokens

        max_idf = sum(self._idf.get(t, 1.0) for t in q_tokens) + 0.01

        # 🔥 PRÉ-FILTRE : lexical + spectral expansion
        candidate_keys = set()
        expanded_tokens = set(q_tokens)

        # 1. Expansion spectrale (seulement si qualité > 0.7)
        if self._spectral_ready and self._spectral_quality > 0.35:
            for t in q_tokens:
                phase = self._spectral.get_phase(t)
                if phase is not None:
                    # Chercher les mots avec phase proche dans tout le vocabulaire
                    for w, w_phase in self._spectral.phases.items():
                        d = abs(phase - w_phase)
                        d = min(d, TAU - d)
                        if d < math.pi / 6:  # 30° — seuil de similarité sémantique
                            expanded_tokens.add(w)
                            # Limiter à 10 voisins par token
                            if len(expanded_tokens) > len(q_tokens) + 10:
                                break

        # 2. Lookup dans l'index inversé (tokens originaux + voisins spectraux)
        for t in expanded_tokens:
            if t in self.word_index:
                candidate_keys.update(self.word_index[t])
            if t in self._subword_index:
                for multi_word, _ in self._subword_index[t]:
                    if multi_word in self.word_index:
                        candidate_keys.update(self.word_index[multi_word])

        if not candidate_keys:
            return []

        # 🔥 Pré-calculer les phases de la question (seulement si qualité > 0.7)
        q_phases = []
        if self._spectral_ready and self._spectral_quality > 0.35:
            for t in q_tokens:
                ph = self._spectral.get_phase(t)
                if ph is not None:
                    q_phases.append(ph)

        scored = []
        now = time.time()
        for key in candidate_keys:
            if key not in self.registry:
                continue
            record = self.registry[key]
            fact_text = f"{_normalize(record.sujet)} {_normalize(record.relation)} {_normalize(record.objet)}"
            fact_tokens_raw = set(_tokenize(fact_text))
            fact_tokens = set(fact_tokens_raw)
            for ft in list(fact_tokens_raw):
                for sub in ft.split():
                    if len(sub) >= 2:
                        fact_tokens.add(sub)
            common_tokens = set(q_tokens) & fact_tokens
            tfidf_score = sum(self._idf.get(t, 1.0) for t in common_tokens)

            # Bonus sujet
            sujet_norm = _normalize(record.sujet)
            bonus_sujet = 0.0
            for t in q_tokens:
                if t == sujet_norm:
                    bonus_sujet += 3.0
                elif t in sujet_norm.split():
                    bonus_sujet += 1.0

            # 🔥 BONUS SÉMANTIQUE (seulement si qualité > 0.7)
            semantic_bonus = 0.0
            if self._spectral_quality > 0.35 and q_phases and fact_tokens:
                f_phases = []
                for ft in fact_tokens:
                    ph = self._spectral.get_phase(ft)
                    if ph is not None:
                        f_phases.append(ph)
                if f_phases:
                    sims = []
                    for qp in q_phases:
                        best = max((math.cos(qp - fp) + 1.0) / 2.0 for fp in f_phases)
                        sims.append(best)
                    semantic_bonus = sum(sims) / len(sims)

            # Score final : TF-IDF + Sémantique (seulement si qualité > 0.7) + Sujet
            lexical_score = tfidf_score / max_idf if common_tokens else 0.0
            # Le spectral n'est activé que si la qualité est suffisante (> 0.35)
            if self._spectral_quality > 0.35:
                semantic_weight = 0.6   # 🆕 boosté de 0.3 → 0.6
                lexical_weight = 0.3    # 🆕 réduit de 0.5 → 0.3
            else:
                semantic_weight = 0.0
                lexical_weight = 0.8
            score = (lexical_score * lexical_weight +
                     semantic_bonus * semantic_weight +
                     min(bonus_sujet / 5.0, 0.3) * 0.2)

            # Si aucun chevauchement lexical mais similarité sémantique > 0.5
            if not common_tokens and semantic_bonus < 0.4:
                continue
            # Amplitude factor : normal pour faits standards, boost agressif pour SFT
            if record.amplitude >= 5.0:
                amplitude_factor = record.amplitude  # ×5 à ×10 directement
            else:
                amplitude_factor = 1.0 + math.log1p(record.amplitude) * 0.4
            weighted = score * amplitude_factor
            if weighted > threshold:
                scored.append((record, weighted))
                record.times_retrieved += 1
                record.last_seen = now

        scored.sort(key=lambda x: -x[1])
        self.total_retrieved += 1
        return scored[:max_results]

    def retrieve_resonance(self, question: str, max_results: int = 50,
                           sector_boost: str = None) -> List[Tuple[FactRecord, float]]:
        """
        RETRIEVAL ONDULATOIRE PUR — par résonance holographique ℂ⁵¹².
        
        Remplace le TF-IDF lexical par la cohérence de phase entre
        le ψ de la question et les ψ des faits stockés dans l'hologramme.
        
        Algorithme :
          1. Encoder la question → ψ_Q
          2. Pour chaque fait, mesurer Re(⟨ψ_fact | ψ_Q⟩) → cohérence
          3. Multiplier par l'amplitude du fait
          4. Bonus sujet si le sujet du fait est dans la question
          5. Trier et retourner les meilleurs
        """
        psi_q = self.encoder.encode_query(question)
        if psi_q is None or np.all(psi_q == 0):
            return []
        
        q_norm = _normalize(question)
        q_tokens = set(_tokenize(q_norm))
        
        scored = []
        now = time.time()
        
        for key, record in self.registry.items():
            if record.psi is None:
                continue
            
            # Cohérence de phase entre ψ_fact et ψ_Q
            coherence = float(np.real(np.dot(record.psi, np.conj(psi_q))))
            # Normaliser en [0, 1]
            I = (coherence + 1.0) / 2.0
            
            # Bonus sujet : le sujet du fait apparaît dans la question
            sujet_norm = _normalize(record.sujet)
            bonus_sujet = 0.0
            if sujet_norm in q_norm or any(t == sujet_norm for t in q_tokens):
                bonus_sujet = 0.3
            elif any(t in sujet_norm for t in q_tokens if len(t) >= 4):
                bonus_sujet = 0.15
            
            # Bonus secteur (si spécifié)
            bonus_secteur = 0.0
            if sector_boost and record.secteur == sector_boost:
                bonus_secteur = 0.2
            
            # Facteur d'amplitude
            if record.amplitude >= 5.0:
                amp_factor = record.amplitude / 5.0
            else:
                amp_factor = 1.0 + math.log1p(record.amplitude) * 0.3
            
            # Score final
            score = (I + bonus_sujet + bonus_secteur) * amp_factor
            
            if score > 0.01:  # seuil minimal
                scored.append((record, score))
                record.times_retrieved += 1
                record.last_seen = now
        
        scored.sort(key=lambda x: -x[1])
        self.total_retrieved += 1
        return scored[:max_results]

    def ruminate(self, max_pairs: int = 50000):
        """
        Rumination nocturne — consolidation par interférence.

        Pour des paires de faits aléatoires :
          - Interférence constructive (cos > 0.7) → renforcement mutuel
          - Interférence destructive (cos < -0.1) → affaiblissement du moins fréquent

        Simule le sommeil : le cerveau « rejoue » les souvenirs et les consolide.
        """
        keys = list(self.registry.keys())
        n = len(keys)
        if n < 2:
            return

        rng = np.random.RandomState(42)
        pairs_processed = 0
        reinforced = 0
        weakened = 0

        for _ in range(min(max_pairs, n * (n-1) // 2)):
            i, j = rng.randint(0, n, 2)
            if i == j:
                continue

            rec_i = self.registry[keys[i]]
            rec_j = self.registry[keys[j]]

            # Interférence : cosinus hermitien entre les deux vecteurs
            interference = float(np.real(np.dot(rec_i.psi, np.conj(rec_j.psi))))

            if interference > 0.7:
                # Renforcement mutuel
                boost = 0.01 * interference
                rec_i.amplitude += boost
                rec_j.amplitude += boost
                self.hologram += boost * (rec_i.psi + rec_j.psi)
                reinforced += 1
            elif interference < -0.1:
                # Affaiblir le moins fréquent
                weaker = rec_i if rec_i.count < rec_j.count else rec_j
                decay = 0.01 * abs(interference)
                weaker.amplitude = max(0.1, weaker.amplitude - decay)
                self.hologram -= decay * weaker.psi
                weakened += 1

            pairs_processed += 1

        self._last_rumination = time.time()
        log.info(f"Rumination: {pairs_processed} paires, "
                 f"{reinforced} renforcées, {weakened} affaiblies "
                 f"({n} faits dans l'inconscient)")

    # ── FEEDBACK (appelé par le conscient) ─────────────────────────────────

    def reinforce(self, record: FactRecord, amount: float = ALPHA_REINFORCE):
        """Renforce un fait dans l'hologramme (feedback positif du conscient)."""
        record.amplitude += amount
        record.confidence = min(1.0, record.confidence + amount * 2)
        record.times_accepted += 1
        self.hologram += amount * record.psi

    def weaken(self, record: FactRecord, amount: float = ALPHA_WEAKEN):
        """Affaiblit un fait (feedback négatif du conscient)."""
        record.amplitude = max(0.01, record.amplitude - amount)
        record.confidence = max(0.0, record.confidence - amount * 3)
        self.hologram -= amount * record.psi

    # ── STATS ──────────────────────────────────────────────────────────────

    @property
    def stats(self) -> dict:
        return {
            'faits': len(self.registry),
            'total_ingested': self.total_ingested,
            'total_retrieved': self.total_retrieved,
            'amplitude_moyenne': sum(r.amplitude for r in self.registry.values()) / max(len(self.registry), 1),
            'energie_hologramme': float(np.sum(np.abs(self.hologram)**2)),
            'derniere_rumination': self._last_rumination,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CONSCIENT — ConsciousFilter
# ═══════════════════════════════════════════════════════════════════════════════

class ConsciousFilter:
    """
    LE CONSCIENT — filtre léger mais puissant.

    Principes :
      - Reçoit le flux brut de l'inconscient
      - Vérifie la COHÉRENCE MUTUELLE des faits
      - Applique les SFT (vérités ancrées) comme prior fort
      - FEEDBACK → Inconscient (renforce/affaiblit)
      - Capacité limitée : traite au plus 10-15 faits
    """

    def __init__(self, store: HolographicStore):
        self.store = store

    def filter(self, question: str,
               candidates: List[Tuple[FactRecord, float]],
               max_accepted: int = 3) -> Tuple[List[FactRecord], List[FactRecord]]:
        """
        Filtre les candidats de l'inconscient.

        Critères de filtrage (dans l'ordre) :
          1. PERTINENCE : le fait doit partager au moins 1 mot avec la question
          2. COHÉRENCE MUTUELLE : pas de contradiction avec les faits déjà acceptés
          3. SFT : bonus pour les faits validés manuellement
          4. LIMITE : max_accepted faits pour ne pas surcharger le conscient

        Returns:
            (accepted, rejected)
        """
        if not candidates:
            return [], []

        q_tokens = set(_tokenize(_normalize(question)))
        accepted = []
        rejected = []

        for rec, resonance in candidates:
            # 1. PERTINENCE : chevauchement lexical avec la question
            fact_tokens = set(_tokenize(f"{_normalize(rec.sujet)} {_normalize(rec.relation)} {_normalize(rec.objet)}"))
            relevance = len(set(q_tokens) & fact_tokens)

            if relevance == 0:
                rejected.append(rec)
                continue

            # 2. COHÉRENCE MUTUELLE
            is_coherent = True
            for accepted_rec in accepted:
                interference = float(np.real(np.dot(
                    rec.psi, np.conj(accepted_rec.psi)
                )))
                if interference < -0.1:
                    rejected.append(rec)
                    is_coherent = False
                    break

            if not is_coherent:
                continue

            # 3. SFT bonus
            sft_boost = self._check_sft(rec, question)

            # Score final = résonance + pertinence + SFT
            rec.confidence = min(1.0, resonance * 2.0 + relevance * 0.1 + sft_boost * 0.5)
            accepted.append(rec)

            # 4. Limite du conscient
            if len(accepted) >= max_accepted:
                break

        # Rejeter les candidats restants
        for rec, _ in candidates[len(accepted)+len(rejected):]:
            rejected.append(rec)

        return accepted, rejected

    def _check_sft(self, record: FactRecord, question: str) -> float:
        """
        Vérifie si un fait correspond à un SFT (High-Amplitude Fact).

        Returns:
            boost (0.0 si pas de match, 1.0 si match parfait)
        """
        s_norm = _normalize(record.sujet)
        o_norm = _normalize(record.objet)
        q_norm = _normalize(question)

        for (sf_s, sf_r, sf_o), amp in HIGH_AMPLITUDE_FACTS.items():
            sf_s_norm = _normalize(sf_s)
            sf_o_norm = _normalize(sf_o)

            # Match sujet + objet
            subject_match = (s_norm == sf_s_norm or sf_s_norm in s_norm or s_norm in sf_s_norm)
            object_match = (o_norm == sf_o_norm or sf_o_norm in o_norm or o_norm in sf_o_norm)

            if subject_match and object_match:
                # Pertinence : la question contient-elle des mots du SFT ?
                sf_words = set((sf_s_norm + ' ' + sf_o_norm).split())
                q_words = set(q_norm.split())
                relevance = len(sf_words & q_words) / max(len(sf_words), 1)
                if relevance > 0:
                    return min(1.0, (amp - 1.0) / 4.0 * relevance)

        return 0.0

    def feedback(self, accepted: List[FactRecord], rejected: List[FactRecord]):
        """
        FEEDBACK vers l'inconscient.

        - Accepté → renforcer dans l'hologramme
        - Rejeté → affaiblir dans l'hologramme
        """
        for rec in accepted:
            self.store.reinforce(rec, ALPHA_REINFORCE)
        for rec in rejected:
            self.store.weaken(rec, ALPHA_WEAKEN)


# ═══════════════════════════════════════════════════════════════════════════════
# MULTI-HOLOGRAMME — Domain Stores + Routeur
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DomainStore:
    """Un hologramme spécialisé pour un domaine de connaissance."""
    domain: str
    store: 'HolographicStore'
    sectors: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    
    @property
    def stats(self) -> Dict:
        return {
            'domain': self.domain,
            'facts': self.store.total_ingested,
            'registry_size': len(self.store.registry),
            'sectors': self.sectors,
        }


# Mapping des 26 secteurs → 5 domaines
DOMAIN_SECTOR_MAP: Dict[str, str] = {
    # ── SCIENCES ──
    'PHYSIQUE_FOND': 'sciences',
    'PHYSIQUE_APPLI': 'sciences',
    'MATHS_PURES': 'sciences',
    'MATHS_APPLI': 'sciences',
    'BIOLOGIE': 'sciences',
    'ECOLOGIE': 'sciences',
    'ASTRONOMIE': 'sciences',
    'COSMOLOGIE': 'sciences',
    # ── CULTURE GÉNÉRALE ──
    'GEOGRAPHIE': 'culture_generale',
    'CULTURE': 'culture_generale',
    'POLITIQUE': 'culture_generale',
    'ECONOMIE': 'culture_generale',
    'SANTE': 'culture_generale',
    'EXPRESSION': 'culture_generale',
    'NATURE_ANIM': 'culture_generale',
    'NATURE_VEGET': 'culture_generale',
    'CORPS_ORGANES': 'culture_generale',
    'CORPS_SENS': 'culture_generale',
    # ── HISTOIRE ──
    'PASSE': 'histoire',
    'FUTUR': 'histoire',
    'HISTOIRE': 'histoire',  # produit par detect_sector()
    # ── CODE ──
    'CODE': 'code',
    'DISTILL': 'code',
    # ── HUMAIN ──
    'CONSCIENCE': 'humain',
    'INTELLIGENCE': 'humain',
    'EMOTION_POS': 'humain',
    'EMOTION_NEG': 'humain',
    'METAPHYSIQUE': 'humain',
    'SPIRITUALITE': 'humain',
    'CREATION': 'humain',
}

# Mots-clés de routage par domaine
DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    'sciences': [
        'physique', 'onde', 'atome', 'quantique', 'particule', 'force', 'energie',
        'cellule', 'adn', 'gene', 'proteine', 'organe', 'espece', 'evolution',
        'mathematique', 'nombre', 'geometrie', 'algebre', 'theoreme', 'equation',
        'planete', 'etoile', 'galaxie', 'soleil', 'lune', 'astre', 'univers',
        'cosmos', 'trou noir', 'big bang', 'biologie', 'chimie', 'element',
        'formule', 'molecule', 'reaction', 'acide', 'science', 'scientifique',
        'photosynthese', 'gravite', 'relativite', 'electromagnetique',
    ],
    'culture_generale': [
        'pays', 'capitale', 'continent', 'ville', 'region', 'frontiere',
        'montagne', 'fleuve', 'ocean', 'mer', 'geographie',
        'art', 'musique', 'litterature', 'cinema', 'theatre', 'peinture',
        'politique', 'democratie', 'justice', 'loi', 'etat', 'gouvernement',
        'economie', 'marche', 'commerce', 'monnaie', 'banque', 'entreprise',
        'sante', 'maladie', 'medecin', 'medicament', 'vaccin', 'virus',
        'animal', 'mammifere', 'oiseau', 'poisson', 'plante', 'arbre', 'fleur',
        'corps', 'coeur', 'sang', 'poumon', 'cerveau', 'muscle',
    ],
    'histoire': [
        'histoire', 'guerre', 'revolution', 'empire', 'roi', 'reine',
        'bataille', 'traite', 'independance', 'decouverte', 'inventeur',
        'president', 'pharaon', 'empereur', 'civilisation', 'ancien',
        'siecle', 'moyen age', 'renaissance', 'colonisation',
        'premiere guerre', 'seconde guerre', 'guerre mondiale',
    ],
    'code': [
        'fonction', 'algorithme', 'variable', 'classe', 'objet', 'api',
        'python', 'javascript', 'java', 'html', 'css', 'sql', 'react',
        'docker', 'git', 'linux', 'serveur', 'base de donnees', 'framework',
        'bibliotheque', 'compiler', 'debugger', 'code', 'programmation',
        'kubernetes', 'node', 'typescript', 'json', 'xml', 'http',
    ],
    'humain': [
        'conscience', 'esprit', 'pensee', 'perception', 'meditation', 'reve',
        'emotion', 'sentiment', 'amour', 'joie', 'bonheur', 'paix', 'compassion',
        'peur', 'tristesse', 'colere', 'stress', 'angoise', 'souffrance',
        'philosophie', 'etre', 'existence', 'realite', 'verite', 'essence',
        'dieu', 'ame', 'spirituel', 'religion', 'foi', 'transcendance', 'sacre',
        'creation', 'creer', 'oeuvre', 'artiste', 'sculpture', 'poesie',
    ],
    'culture_arts': [
        'art', 'peinture', 'musique', 'litterature', 'cinema', 'theatre',
        'sculpture', 'architecture', 'danse', 'poesie', 'opera', 'peintre',
        'ecrivain', 'compositeur', 'realisateur', 'acteur', 'film', 'roman',
        'symphonie', 'jazz', 'rock', 'mozart', 'beethoven', 'shakespeare',
        'mona lisa', 'impressionnisme', 'picasso', 'oscar', 'hollywood',
    ],
    'corps_sante': [
        'corps', 'coeur', 'sang', 'cerveau', 'organe', 'muscle', 'os',
        'poumon', 'foie', 'rein', 'nerf', 'anatomie', 'sante', 'maladie',
        'medecin', 'medicament', 'vaccin', 'virus', 'bacterie', 'chirurgie',
        'sport', 'football', 'tennis', 'athletisme', 'olympique', 'cancer',
        'diagnostic', 'traitement', 'symptome', 'infection',
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# ENTITY RETRIEVER — Retrieval entity-centric (inspiré Obsidian)
# ═══════════════════════════════════════════════════════════════════════════════

class EntityIndex:
    """
    Index entity-centric pour retrieval O(1).
    
    Principe Obsidian : au lieu de chercher dans 100K faits avec TF-IDF,
    indexer par ENTITÉ (sujet ou objet) et faire un lookup direct.
    
    Usage:
        index = EntityIndex(brain.unconscious)
        facts = index.lookup("brésil")  # → tous les faits sur le Brésil
        facts = index.search("capitale du Brésil")  # → le fait exact
    """
    
    def __init__(self, store: 'HolographicStore'):
        self.store = store
        self._entity_index: Dict[str, List[Tuple[str, str, str, float]]] = defaultdict(list)
        self._built = False
    
    def build(self):
        """Construit l'index entité → faits."""
        if self._built:
            return
        
        for (s, r, o), record in self.store.registry.items():
            amp = record.amplitude
            # Indexer par sujet complet
            self._entity_index[s].append((s, r, o, amp))
            # Indexer par chaque mot significatif du sujet et de l'objet
            for word in s.split():
                if len(word) > 2:
                    self._entity_index[word].append((s, r, o, amp))
            for word in o.split():
                if len(word) > 2:
                    self._entity_index[word].append((s, r, o, amp))
            # Indexer bigrammes sujet+objet
            s_words = s.split()
            o_words = o.split()
            if len(s_words) >= 2:
                for i in range(len(s_words)-1):
                    bigram = f'{s_words[i]} {s_words[i+1]}'
                    self._entity_index[bigram].append((s, r, o, amp))
            if len(o_words) >= 2:
                for i in range(len(o_words)-1):
                    bigram = f'{o_words[i]} {o_words[i+1]}'
                    self._entity_index[bigram].append((s, r, o, amp))
        
        self._built = True
        log.info(f"EntityIndex: {len(self._entity_index):,} entités indexées")
    
    def lookup(self, entity: str, max_results: int = 20) -> List[Tuple[str, str, str, float]]:
        """Lookup direct par entité. Retourne les faits triés par amplitude."""
        self.build()
        entity_clean = entity.lower().strip()
        results = self._entity_index.get(entity_clean, [])
        # Dédupliquer
        seen = set()
        unique = []
        for s, r, o, amp in results:
            key = (s, r, o)
            if key not in seen:
                seen.add(key)
                unique.append((s, r, o, amp))
        unique.sort(key=lambda x: -x[3])
        return unique[:max_results]
    
    def search(self, question: str, max_results: int = 15) -> List[Tuple[FactRecord, float]]:
        """
        Recherche entity-aware avec parsing question.
        
        Stratégie Question-Aware :
        1. Parser la question pour extraire ENTITÉ + TYPE DE RELATION
        2. Chercher les faits sur l'ENTITÉ
        3. Filtrer/faire monter les faits dont la relation matche le TYPE
        4. Si rien, fallback word-overlap classique
        """
        self.build()
        
        q_lower = question.lower().strip()
        stopwords = {'quelle','quel','quels','quelles','est','sont','qui','que','quoi',
                     'dont','pour','dans','sur','avec','par','plus','moins','tout',
                     'très','cette','cet','ces','aux','des','les','une','dun','comment',
                     'quand','pourquoi','combien','peut','fait','elle','elles','ils',
                     'le','la','un','du','de','et','ou','en','au','se','son','sa','ses',
                     'nous','vous','leur','mes','tes','nos','vos','ce','ça','ont','a',
                     'ont','ete','etre','avoir','aller','venir','faire','dire','voir',
                     'savoir','pouvoir','vouloir','what','is','are','was','were','the',
                     'a','an','of','in','on','at','to','for','and','or','how','when',
                     'who','where','why','which'}
        q_words = [w for w in q_lower.split() if len(w) > 2 and w not in stopwords]
        
        if not q_words:
            return []

        # ── PHASE 1 : Question-Aware Parsing ──────────────────────────
        # Détecter le TYPE de relation demandé
        relation_map = {
            # FR — Géographie
            'capitale': ['capitale', 'capital', 'chef-lieu'],
            'pays': ['pays', 'nation'],
            'continent': ['continent', 'continents'],
            'ocean': ['océan', 'ocean', 'mers', 'mer'],
            'fleuve': ['fleuve', 'rivière', 'riviere', 'cours'],
            'montagne': ['montagne', 'sommet', 'pic', 'everest', 'kilimandjaro'],
            'desert': ['désert', 'desert', 'sahara'],
            'monnaie': ['monnaie', 'devise', 'euro', 'dollar', 'yen', 'livre'],
            'langue': ['langue', 'parle', 'official'],
            # FR — Sciences
            'symbole': ['symbole', 'symboles', 'chimique'],
            'formule': ['formule', 'formules', 'composition', 'compose'],
            'element': ['élément', 'element', 'atome', 'atomique'],
            'decouvert': ['découvert', 'decouvert', 'découverte', 'decouverte', 'trouvé', 'trouve', 'identifié'],
            'invente': ['inventé', 'invente', 'invention', 'créé', 'cree', 'fondé', 'fonde', 'développé', 'developpe'],
            'planete': ['planète', 'planete', 'planetes', 'planètes', 'jupiter', 'mars', 'venus', 'saturne', 'mercure'],
            'systeme': ['système', 'systeme', 'systemes', 'systèmes'],
            'force': ['force', 'gravité', 'gravite', 'attraction'],
            # FR — Corps humain
            'organe': ['organe', 'organes', 'foie', 'rein', 'poumon', 'cerveau', 'coeur', 'cœur'],
            'os': ['os', 'squelette', 'squelette'],
            'muscle': ['muscle', 'muscles'],
            'maladie': ['maladie', 'maladies', 'virus', 'bactérie', 'bacterie', 'infection'],
            'traitement': ['traitement', 'médicament', 'medicament', 'vaccin', 'remède', 'remede', 'soigne'],
            # FR — Histoire
            'date': ['quand', 'année', 'annee', 'date', 'commencé', 'commence', 'terminé', 'termine', 'fondé', 'fonde', 'créé', 'cree', 'eu lieu', 'a lieu'],
            'guerre': ['guerre', 'bataille', 'conflit', 'invasion'],
            'revolution': ['révolution', 'revolution', 'soulèvement', 'soulèvement'],
            'independance': ['indépendance', 'independance', 'autonomie'],
            'empire': ['empire', 'royaume', 'dynastie'],
            'dirigeant': ['roi', 'reine', 'empereur', 'président', 'president', 'dirigeant', 'pharaon', 'souverain', 'chef'],
            # FR — Arts
            'peint': ['peint', 'peinte', 'dessiné', 'dessine', 'toile', 'tableau'],
            'ecrit': ['écrit', 'ecrit', 'rédigé', 'redige', 'composé', 'compose', 'auteur', 'roman', 'livre'],
            'compose': ['composé', 'compose', 'musique', 'symphonie', 'concerto', 'sonate'],
            'realise': ['réalisé', 'realise', 'film', 'cinéma', 'cinema', 'réalisateur', 'realisateur'],
            # FR — Code
            'definition_code': ['qu\'est-ce', 'cest', 'définis', 'definis', 'explique', 'signifie', 'what is'],
            'fonction_code': ['fonction', 'def', 'function', 'écris', 'ecris', 'code'],
            'commande': ['commande', 'commandes', 'syntaxe'],
            # FR — Quantité
            'combien': ['nombre', 'combien', 'total', 'compte', 'dénombrer'],
            'mesure': ['mesure', 'longueur', 'hauteur', 'altitude', 'profondeur', 'poids', 'vitesse', 'superficie'],
            'population': ['population', 'habitants', 'habitants', 'densité', 'densite'],
            # FR — Localisation
            'localisation': ['où', 'ou', 'trouve', 'situé', 'situe', 'localisation', 'lieu', 'endroit'],
            # FR — Comparaison
            'plus_grand': ['plus grand', 'plus grande', 'plus haut', 'plus long', 'plus important', 'plus grand'],
            'plus_petit': ['plus petit', 'plus courte', 'plus bas', 'plus courte'],
            # EN (mêmes concepts)
            'capital_en': ['capital', 'capitals'],
            'discovered_en': ['discovered', 'invented', 'created', 'founded'],
            'symbol_en': ['symbol', 'chemical'],
            'how_many_en': ['how many', 'number of'],
            'when_en': ['when', 'year', 'date'],
            'who_en': ['who'],
            'what_en': ['what'],
        }
        
        detected_relations = []
        for rel_type, keywords in relation_map.items():
            for kw in keywords:
                if kw in q_lower:
                    detected_relations.append((rel_type, kw))
                    break
        
        # ── PHASE 2 : Entity extraction ───────────────────────────────
        # L'entité principale = le mot le plus long/moins commun dans la question
        # (probablement un nom propre ou concept)
        entity_candidates = [w for w in q_words if len(w) > 4]
        # Prioriser les mots qui commencent par une majuscule (noms propres)
        q_original = question.strip()
        proper_nouns = [w.lower() for w in q_original.split() 
                        if w and w[0].isupper() and len(w) > 2 and w.lower() not in stopwords]
        if proper_nouns:
            entity_candidates = proper_nouns + entity_candidates
        
        # ── PHASE 3 : Lookup + Scoring ────────────────────────────────
        all_candidates = {}
        for word in entity_candidates:
            for s, r, o, amp in self.lookup(word, max_results=50):
                key = (s, r, o)
                if key not in all_candidates:
                    fact_text = f'{s} {r} {o}'.lower()
                    keyword_matches = sum(1 for w in q_words if w in fact_text)
                    
                    # Bonus bigrammes
                    for i in range(len(q_words)-1):
                        bigram = f'{q_words[i]} {q_words[i+1]}'
                        if bigram in fact_text:
                            keyword_matches += 2
                    
                    # Score de base
                    score = amp * 0.5 + keyword_matches * 3.0
                    
                    # 🆕 BONUS MASSIF si la relation matche le type demandé
                    relation_match = False
                    if detected_relations:
                        for rel_type, rel_kw in detected_relations:
                            if rel_kw in r.lower() or rel_kw in o.lower():
                                score += 30.0  # bonus énorme
                                relation_match = True
                                break
                    
                    # 🆕 Pénalité pour objets très longs (bruit)
                    if len(o) > 80:
                        score *= 0.5
                    
                    all_candidates[key] = (s, r, o, amp, score, relation_match)
        
        # 🆕 Si une relation est détectée, filtrer pour ne garder QUE les faits qui matchent
        if detected_relations:
            relation_matched = {k: v for k, v in all_candidates.items() if v[5]}
            if len(relation_matched) >= 2:
                all_candidates = relation_matched
        
        # Convertir en FactRecord
        results = []
        for (s, r, o), (s_raw, r_raw, o_raw, amp, score, rel_match) in all_candidates.items():
            record = self.store.registry.get((s, r, o))
            if record:
                results.append((record, score))
        
        results.sort(key=lambda x: -x[1])
        return results[:max_results]
    
    def stats(self) -> Dict:
        return {
            'entities': len(self._entity_index),
            'built': self._built,
        }


class OndulatoireIndex:
    """
    Index entity-centric ONDULATOIRE — lookup par résonance ψ.
    
    Contrairement à EntityIndex (string exact), cet index utilise les
    vecteurs psi du HolographicEncoder pour trouver les entités par
    COHÉRENCE QUANTIQUE, même si l'orthographe diffère.
    
    Usage:
        oidx = OndulatoireIndex(brain.unconscious, brain.unconscious.encoder)
        facts = oidx.search("capitale du Brésil")  # trouve "bresil" aussi
    """
    
    def __init__(self, store: 'HolographicStore', encoder):
        self.store = store
        self.encoder = encoder
        self._psi_entities: Dict[str, np.ndarray] = {}  # entity → psi vector
        self._entity_facts: Dict[str, List[Tuple[str, str, str, float]]] = defaultdict(list)
        self._built = False
    
    def build(self):
        """Encode toutes les entités en ψ et construit l'index."""
        if self._built or self.encoder is None:
            return
        
        for (s, r, o), record in self.store.registry.items():
            # Encoder le sujet comme entité ψ
            if s not in self._psi_entities:
                psi = self.encoder.encode_query(s)
                if psi is not None and np.any(psi != 0):
                    self._psi_entities[s] = psi
            # Encoder les mots-clés de l'objet
            for word in o.split():
                if len(word) > 3 and word not in self._psi_entities:
                    psi = self.encoder.encode_query(word)
                    if psi is not None and np.any(psi != 0):
                        self._psi_entities[word] = psi
            
            # Associer les faits aux entités
            amp = record.amplitude
            if s in self._psi_entities:
                self._entity_facts[s].append((s, r, o, amp))
            for word in o.split():
                if len(word) > 3 and word in self._psi_entities:
                    self._entity_facts[word].append((s, r, o, amp))
        
        self._built = True
        log.info(f"OndulatoireIndex: {len(self._psi_entities)} entités ψ, "
                 f"{sum(len(v) for v in self._entity_facts.values())} liens")
    
    def search(self, question: str, max_results: int = 15, 
               coherence_threshold: float = 0.5) -> List[Tuple[FactRecord, float]]:
        """
        Recherche par résonance ψ.
        
        1. Encode la question en ψ_question
        2. Pour chaque entité ψ, calcule la cohérence |⟨ψ_q|ψ_e⟩|
        3. Si cohérence > seuil, ajoute les faits de cette entité
        4. Bonus proportionnel à la cohérence
        """
        if not self._built or self.encoder is None:
            return []
        
        psi_q = self.encoder.encode_query(question)
        if psi_q is None or np.all(psi_q == 0):
            return []
        
        all_candidates = {}
        
        for entity, psi_e in self._psi_entities.items():
            # Cohérence quantique entre la question et l'entité
            coherence = float(np.abs(np.dot(psi_q.conj(), psi_e)))
            
            if coherence > coherence_threshold:
                for s, r, o, amp in self._entity_facts.get(entity, []):
                    key = (s, r, o)
                    if key not in all_candidates:
                        # Score = amplitude × cohérence
                        score = amp * coherence * 2.0
                        all_candidates[key] = (s, r, o, amp, score)
                    else:
                        # Moyenne des cohérences
                        _, _, _, _, old_score = all_candidates[key]
                        new_score = max(old_score, amp * coherence * 2.0)
                        all_candidates[key] = (s, r, o, amp, new_score)
        
        # Convertir en FactRecord
        results = []
        for (s, r, o), (_, _, _, amp, score) in all_candidates.items():
            record = self.store.registry.get((s, r, o))
            if record:
                results.append((record, score))
        
        results.sort(key=lambda x: -x[1])
        return results[:max_results]
    
    def stats(self) -> Dict:
        return {
            'entities': len(self._psi_entities),
            'built': self._built,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CERVEAU COMPLET — HarmonicBrain
# ═══════════════════════════════════════════════════════════════════════════════

class HarmonicBrain:
    """
    Cerveau Harmonique — orchestre Inconscient + Conscient.

    Cycle complet :
      1. Question → Inconscient.retrieve() → tous les faits résonnants
      2. Conscient.filter() → faits validés cohérents
      4. Conscient.feedback() → renforce/affaiblit dans l'inconscient
      5. WaveDecoder → réponse en langage naturel

    Usage:
        brain = HarmonicBrain()
        brain.ingest("La lumière est une onde électromagnétique.")
        brain.ingest_corpus("data/corpus/")
        brain.ruminate()  # à exécuter périodiquement

        result = brain.process("explique la lumière")
        print(result.response)
    """

    def __init__(self, knowledge_base: List[Tuple[str, str, str, str]] = None,
                 dim: int = 512, use_holographic: bool = True):
        t0 = time.time()

        # 👥 MULTI-HOLOGRAMME : 5 stores spécialisés + 1 global (backward-compat)
        domain_dim = max(32, dim // 2)  # dim réduit par domaine (max 50K faits)
        self._domain_stores: Dict[str, DomainStore] = {}
        self._sector_to_domain_cache: Dict[str, str] = dict(DOMAIN_SECTOR_MAP)
        
        for domain_name in ['sciences', 'culture_generale', 'histoire', 'code', 'humain', 'culture_arts', 'corps_sante']:
            store = HolographicStore(dim=domain_dim, use_holographic=use_holographic)
            self._domain_stores[domain_name] = DomainStore(
                domain=domain_name,
                store=store,
                sectors=[s for s, d in DOMAIN_SECTOR_MAP.items() if d == domain_name],
                keywords=DOMAIN_KEYWORDS.get(domain_name, []),
            )
        
        # L'INCONSCIENT GLOBAL (backward-compatible, reçoit tous les faits)
        self.unconscious = HolographicStore(dim=dim, use_holographic=use_holographic)
        self._global_store = self.unconscious

        # LE CONSCIENT (fonctionne avec l'inconscient global)
        self.conscious = ConsciousFilter(self.unconscious)

        # LE PARSEUR DE PROMPT
        self.parser = PromptParser()

        # LE CONSCIENT INTELLIGENT (raisonne, pas juste filtre)
        self.intelligence = ConsciousIntelligence(self.unconscious)

        # 🔥 LE COMPOSER DE RÉPONSES (style naturel, 30+ structures)
        self.composer = ResponseComposer() if ResponseComposer is not None else None

        # 🔥 LA CONVERSATION (contexte ψ multi-tours)
        self.conversation = None
        if WaveConversation is not None:
            try:
                self.conversation = WaveConversation(self.unconscious.encoder)
            except Exception:
                self.conversation = None

        # 🌐 WEB RETRIEVER (connexion Internet)
        self._web = _WEB_RETRIEVER  # instance globale partagée

        # 🔗 PHASE AMPLIFIER (raisonnement profond)
        self._deep_reasoner = None
        if _PHASE_AMPLIFIER_AVAILABLE:
            try:
                # En mode léger, on passe dim et l'encodeur peut être None
                # (PhaseAmplifier a un fallback hash-based)
                enc = self.unconscious.encoder if use_holographic else None
                self._deep_reasoner = PhaseAmplifier(
                    brain=self, dim=dim, encoder=enc
                )
            except Exception:
                pass

        # 🧪 FEW-SHOT INJECTOR (apprentissage temporaire)
        self._few_shot = None
        if _FEW_SHOT_AVAILABLE:
            try:
                self._few_shot = FewShotInjector(
                    brain=self, dim=dim,
                    encoder=self.unconscious.encoder
                )
            except Exception:
                pass

        # 🎯 ATTENTION DYNAMIQUE (ψ contextuels)
        self._attention = None
        if _HARMONIC_ATTENTION_AVAILABLE:
            try:
                enc = self.unconscious.encoder if use_holographic else None
                self._attention = HarmonicAttention(
                    encoder=enc, dim=dim,
                    alpha=PHI_INV * 0.5  # ~0.309
                )
            except Exception:
                pass

        # 📚 APPRENTISSAGE CONTINU (imports lazy pour éviter circulaire)
        self._fine_tuner = None
        self._fast_learner = None
        self._feedback = None
        self._learn_count = 0
        self._learn_every = 100

        if use_holographic:
            try:
                from wave_fine_tune import WaveFineTuner
                self._fine_tuner = WaveFineTuner(
                    encoder=self.unconscious.encoder,
                    learning_rate=1.0, lambda_reg=2.0
                )
            except Exception:
                pass
        try:
            from fast_learner import FastLearner
            self._fast_learner = FastLearner(self)
        except Exception:
            pass
        try:
            from feedback_loop import FeedbackLoop
            self._feedback = FeedbackLoop(brain=self)
        except Exception:
            pass

        # 🎭 DIALOGUE HARMONIQUE (la forme naturelle)
        self._dialogue = None
        try:
            from harmonic_dialogue import HarmonicDialogue
            enc = self.unconscious.encoder if use_holographic else None
            self._dialogue = HarmonicDialogue(brain=self, dim=dim, encoder=enc)
        except Exception:
            pass

        # 🎨 CONSCIENT CRÉATEUR (créativité ondulatoire)
        self._creator = None
        try:
            from conscious_creator import ConsciousCreator
            enc = self.unconscious.encoder if use_holographic else None
            self._creator = ConsciousCreator(brain=self, dim=dim, encoder=enc)
        except Exception:
            pass

        # 📖 RÉSUMEUR HARMONIQUE (lecture de documents)
        self._summarizer = None
        try:
            from harmonic_summarizer import HarmonicSummarizer
            self._summarizer = HarmonicSummarizer(brain=self, dim=dim, max_facts=15)
        except Exception:
            pass

        # Adaptateur multi-domaine (raisonne dans 12 domaines)
        self._domain_adapters: Dict[str, DomainAdapter] = {}
        self._current_domain: str = 'faits'

        # Pré-charger la KB existante (global + domain stores)
        if knowledge_base:
            for s, r, o, sec in knowledge_base:
                # Ingest dans le global (backward-compat)
                self.unconscious.ingest(s, r, o, sec)
                # Router vers le store de domaine
                self._route_ingest(s, r, o, sec)

        # 🔥 INJECTER LES SFT (faits validés manuellement, amplitude 5.0)
        sft_injected = 0
        for (sf_s, sf_r, sf_o), amp in HIGH_AMPLITUDE_FACTS.items():
            record = self.unconscious.ingest(sf_s, sf_r, sf_o, "SFT")
            if record.amplitude < amp:
                record.amplitude = amp  # forcer l'amplitude SFT
            # 🆕 Router aussi vers les domaines (détecter le secteur depuis le contenu)
            try:
                from bootstrapper import detect_sector
                sft_sector = detect_sector(f"{sf_s} {sf_r} {sf_o}")
                if sft_sector != 'GENERAL':
                    self._route_ingest(sf_s, sf_r, sf_o, sft_sector)
            except Exception:
                pass
            sft_injected += 1
        if sft_injected > 0:
            log.info(f"SFT injectés: {sft_injected} faits avec amplitude {amp}")
        
        # Log des stats par domaine
        for ds in self._domain_stores.values():
            if ds.store.total_ingested > 0:
                log.info(f"  Domaine {ds.domain}: {ds.store.total_ingested} faits")

        # 🔥 RÉ-ENCODAGE SÉMANTIQUE (sur le global seulement)
        try:
            n_reencoded = self.unconscious.encoder.reencode_all_with_semantics()
            if n_reencoded > 0:
                log.info(f"Ré-encodage sémantique: {n_reencoded} mots réalignés")
        except Exception:
            pass

        # 👤 KB UTILISATEUR : dictionnaire de cerveaux personnels par user_id
        self._user_kbs: Dict[str, 'HarmonicBrain'] = {}
        
        # 🔍 ENTITY INDEX : retrieval entity-centric O(1) (inspiré Obsidian)
        self._entity_index = EntityIndex(self.unconscious)
        self._entity_index.build()
        
        # 🌊 ONDULATOIRE INDEX : lookup par résonance ψ
        self._wave_index = OndulatoireIndex(self.unconscious, self.unconscious.encoder)
        if use_holographic:
            self._wave_index.build()
        
        self._init_time = time.time() - t0
        log.info(f"HarmonicBrain initialisé en {self._init_time:.1f}s "
                 f"({len(self.unconscious.registry)} faits dans l'inconscient)")

    @classmethod
    def from_npz(cls, path: str, max_facts: int = None) -> 'HarmonicBrain':
        """
        Charge le cerveau directement depuis un fichier NPZ (sans HarmonicModel).

        Usage:
            brain = HarmonicBrain.from_npz('data/bootstrapper_output/knowledge_base_clean_v2.npz')
        """
        import numpy as np
        data = np.load(path, allow_pickle=True)
        facts = [(str(f[0]), str(f[1]), str(f[2]), str(f[3])) for f in data['facts']]
        if max_facts:
            facts = facts[:max_facts]
        return cls(facts)

    @classmethod
    def from_kb_list(cls, kb: List[Tuple[str, str, str, str]]) -> 'HarmonicBrain':
        """Charge le cerveau depuis une liste de faits (compatibilité HarmonicModel)."""
        return cls(kb)

    # ── ROUTEUR MULTI-HOLOGRAMME ────────────────────────────────────────
    
    def _sector_to_domain(self, secteur: str) -> Optional[str]:
        """Mappe un secteur vers son domaine. Retourne None si inconnu."""
        return self._sector_to_domain_cache.get(secteur.upper().strip())
    
    def _route_ingest(self, sujet: str, relation: str, objet: str, secteur: str):
        """Ingère un fait dans le(s) store(s) de domaine approprié(s)."""
        domain = self._sector_to_domain(secteur)
        if domain and domain in self._domain_stores:
            self._domain_stores[domain].store.ingest(sujet, relation, objet, secteur)
    
    def _detect_domains(self, question: str) -> List[str]:
        """
        Détecte le(s) domaine(s) d'une question.
        Retourne 1-2 domaines les plus pertinents.
        """
        q = question.lower()
        scores = {}
        
        for domain, ds in self._domain_stores.items():
            if not ds.store.registry:
                continue  # domaine vide
            score = sum(1 for kw in ds.keywords if kw in q)
            if score > 0:
                scores[domain] = score
        
        if not scores:
            return ['culture_generale']  # défaut
        
        # Retourner les domaines avec score ≥ 50% du max (max 2)
        max_score = max(scores.values())
        domains = [d for d, s in scores.items() if s >= max_score * 0.5]
        return domains[:2]
    
    def _cross_domain_merge(
        self,
        domain_candidates: List[Tuple[str, List[Tuple]]]
    ) -> List[Tuple]:
        """
        Fusionne les candidats de N domaines avec bonus cross-domaine.
        
        Un fait qui apparaît dans plusieurs domaines reçoit +20% par domaine supplémentaire.
        """
        if len(domain_candidates) == 1:
            return domain_candidates[0][1]
        
        merged = []
        seen = set()
        domain_names = [d for d, _ in domain_candidates]
        
        for domain, cands in domain_candidates:
            for rec, score in cands:
                key = (rec.sujet.lower().strip(), 
                       rec.relation.lower().strip(), 
                       rec.objet.lower().strip())
                
                # Bonus cross-domaine : le fait apparaît dans combien d'autres domaines ?
                cross_count = 0
                for d2 in domain_names:
                    if d2 != domain and d2 in self._domain_stores:
                        if key in self._domain_stores[d2].store.registry:
                            cross_count += 1
                
                cross_bonus = 1.0 + 0.2 * cross_count  # +20% par domaine
                
                if key not in seen:
                    seen.add(key)
                    merged.append((rec, score * cross_bonus))
        
        merged.sort(key=lambda x: -x[1])
        return merged[:50]
    
    # ── KB UTILISATEUR (spécialisation personnelle) ───────────────────────

    def load_user_kb(self, user_id: str, kb_path: str):
        """
        Charge une base de connaissances personnelle depuis un NPZ.

        Args:
            user_id: Identifiant utilisateur (ex: "user_123")
            kb_path: Chemin vers le fichier NPZ
        """
        user_brain = HarmonicBrain.from_npz(kb_path, max_facts=50000)
        self._user_kbs[user_id] = user_brain
        log.info(f"KB utilisateur chargée : user={user_id}, "
                 f"path={kb_path}, "
                 f"facts={len(user_brain.unconscious.registry)}")

    def unload_user_kb(self, user_id: str):
        """Décharge la KB personnelle d'un utilisateur (libère la mémoire)."""
        if user_id in self._user_kbs:
            n_facts = len(self._user_kbs[user_id].unconscious.registry)
            del self._user_kbs[user_id]
            log.info(f"KB utilisateur déchargée : user={user_id}, facts={n_facts}")

    def has_user_kb(self, user_id: str) -> bool:
        """Vérifie si un utilisateur a une KB personnelle chargée."""
        return user_id in self._user_kbs

    @staticmethod
    def _merge_candidates(
        global_candidates: List[Tuple],
        user_candidates: List[Tuple],
        user_boost: float = 1.5,
    ) -> List[Tuple]:
        """
        Fusionne les candidats globaux et personnels.

        Les candidats personnels sont boostés (×user_boost) et apparaissent
        en premier. Déduplication par clé (sujet, relation, objet).

        Args:
            global_candidates: Liste de (FactRecord, score) du cerveau global
            user_candidates: Liste de (FactRecord, score) du cerveau personnel
            user_boost: Multiplicateur de score pour les candidats personnels

        Returns:
            Liste fusionnée triée par score décroissant, max 50 éléments.
        """
        seen = set()
        merged = []

        # D'abord les candidats personnels (boostés, priorité utilisateur)
        for rec, score in user_candidates:
            key = (rec.sujet.lower().strip(), rec.relation.lower().strip(),
                   rec.objet.lower().strip())
            seen.add(key)
            merged.append((rec, score * user_boost))

        # Puis les candidats globaux non redondants
        for rec, score in global_candidates:
            key = (rec.sujet.lower().strip(), rec.relation.lower().strip(),
                   rec.objet.lower().strip())
            if key not in seen:
                seen.add(key)
                merged.append((rec, score))

        # Trier par score décroissant
        merged.sort(key=lambda x: -x[1])
        return merged[:50]

    # ── INGESTION ──────────────────────────────────────────────────────────

    def ingest_via_llm(self, text: str) -> int:
        """
        Ingère un texte via DeepSeek/LLM → extraction de triplets → inconscient.

        Returns:
            nombre de nouveaux faits ajoutés
        """
        try:
            from bootstrapper import extract_triples_llm
            triples = extract_triples_llm(text)
        except ImportError:
            from bootstrapper import extract_triples_simple
            triples = extract_triples_simple(text)

        new_count = 0
        for s, r, o, sec in triples:
            key = (_normalize(s).strip(), _normalize(r).strip(), _normalize(o).strip())
            if key not in self.unconscious.registry:
                new_count += 1
            self.unconscious.ingest(s, r, o, sec)
        return new_count

    def ingest_corpus_via_llm(self, dir_path: str, max_files: int = 50,
                               max_lines: int = 500) -> int:
        """
        Ingère un corpus via LLM (DeepSeek).

        Args:
            dir_path: répertoire contenant des fichiers .txt
            max_files: nombre max de fichiers
            max_lines: nombre max de lignes par fichier

        Returns:
            nombre total de nouveaux faits
        """
        import time as _time
        corpus_path = Path(dir_path)
        total_new = 0
        files = list(corpus_path.glob("*.txt"))[:max_files]

        log.info(f"Ingestion LLM: {len(files)} fichiers")
        for fi, path in enumerate(files):
            if path.stat().st_size < 100:
                continue
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                lines = [l.strip() for l in f if 30 < len(l.strip()) < 500]
            for li, line in enumerate(lines[:max_lines]):
                try:
                    new = self.ingest_via_llm(line)
                    total_new += new
                except Exception as e:
                    log.warning(f"Erreur ingestion L{li}: {e}")
                if (li + 1) % 10 == 0:
                    _time.sleep(0.3)  # rate limit
            log.info(f"  [{fi+1}/{len(files)}] {path.name}: +{total_new} nouveaux")

        log.info(f"Ingestion terminée: {total_new} nouveaux faits "
                 f"({len(self.unconscious.registry)} total)")
        return total_new

    # ── ADAPTATEUR MULTI-DOMAINE ───────────────────────────────────────────
    
    def _get_adapter(self, domain: str = None) -> DomainAdapter:
        """Retourne l'adaptateur pour un domaine (lazy init)."""
        if domain is None:
            domain = self._current_domain
        if domain not in self._domain_adapters:
            self._domain_adapters[domain] = DomainAdapter(domain, self)
        return self._domain_adapters[domain]
    
    def _detect_domain(self, question: str) -> str:
        """
        Détecte automatiquement le domaine de raisonnement.
        
        Mapping :
          - Questions factuelles (capitale, qui, quand, où) → 'faits'
          - Questions logiques (si, donc, déduire, syllogisme) → 'logique'
          - Questions médicales (symptôme, maladie, traitement) → 'medecine'
          - Questions juridiques (loi, article, droit, jugement) → 'droit'
          - Questions musicales (note, accord, harmonie) → 'musique'
          - Questions de code (fonction, bug, compiler) → 'code'
          - Questions émotionnelles (ressentir, humeur, empathie) → 'emotion'
        """
        q = question.lower()
        
        domain_keywords = {
            'medecine': ['symptôme', 'symptome', 'maladie', 'diagnostic', 'traitement',
                        'fievre', 'toux', 'douleur', 'patient', 'medecin', 'infection'],
            'droit': ['loi', 'article', 'juridique', 'tribunal', 'jugement', 'avocat',
                     'prévenu', 'prevenu', 'condamnation', 'légal', 'legal', 'droit'],
            'musique': ['note', 'accord', 'gamme', 'harmonie', 'mélodie', 'melodie',
                       'rythme', 'compositeur', 'symphonie', 'instrument'],
            'code': ['fonction', 'bug', 'compiler', 'débugger', 'debugger', 'algorithme',
                    'variable', 'classe', 'objet', 'api', 'library'],
            'logique': ['donc', 'déduire', 'deduire', 'syllogisme', 'prémisse', 'premisse',
                       'si alors', 'par conséquent', 'par consequent'],
            'emotion': ['ressentir', 'émotion', 'emotion', 'humeur', 'sentiment',
                       'empathie', 'traumatisme', 'joie', 'tristesse', 'peur'],
        }
        
        scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for kw in keywords if kw in q)
            if score > 0:
                scores[domain] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        # Par défaut : faits (le plus général)
        return 'faits'
        """
        Ingère un texte brut dans l'inconscient (extraction regex locale).
        Pour l'ingestion LLM, utiliser ingest_via_llm().
        """
        from bootstrapper import extract_triples_simple
        triples = extract_triples_simple(text)
        for s, r, o, sec in triples:
            self.unconscious.ingest(s, r, o, sec)
        return len(triples)

    def ask_hybrid(self, question: str, lang: str = 'fr') -> Tuple[str, float, bool]:
        """
        Mode hybride : cerveau d'abord, LLM en fallback.

        Returns:
            (réponse, confiance, from_llm: True si le LLM a été utilisé)
        """
        # 1. Essayer le cerveau
        result = self.process(question, lang=lang)

        if result.confidence >= 0.5 and len(result.response) >= 20:
            return result.response, result.confidence, False

        # 2. Fallback LLM
        try:
            from bootstrapper import _LLM_AVAILABLE, _LLM
            if not _LLM_AVAILABLE:
                return result.response, result.confidence, False

            log.info(f"Fallback LLM pour: {question[:80]}")
            llm_resp = _LLM.generate(question, category="factual")
            llm_text = llm_resp.content.strip()

            if llm_text:
                # Apprendre de la réponse LLM
                from bootstrapper import extract_triples_simple
                triples = extract_triples_simple(llm_text)
                for s, r, o, sec in triples:
                    self.unconscious.ingest(s, r, o, sec)
                if triples:
                    log.info(f"  Appris {len(triples)} faits du LLM")
                return llm_text, 1.0, True
        except Exception as e:
            log.warning(f"Fallback LLM échoué: {e}")

        return result.response, result.confidence, False
        """
        Ingère un texte brut dans l'inconscient.

        Le texte est découpé en phrases, chaque phrase → triplets → H += ψ_f.
        Aucun filtrage — l'inconscient absorbe tout.
        """
        from bootstrapper import extract_triples_simple
        triples = extract_triples_simple(text)
        for s, r, o, sec in triples:
            self.unconscious.ingest(s, r, o, sec)

    def ingest(self, text: str) -> int:
        """
        Ingère un texte brut dans l'inconscient (extraction regex locale).
        Pour l'ingestion LLM, utiliser ingest_via_llm().
        """
        from bootstrapper import extract_triples_simple
        triples = extract_triples_simple(text)
        for s, r, o, sec in triples:
            self.unconscious.ingest(s, r, o, sec)
        return len(triples)

    def ingest_corpus(self, dir_path: str, max_files: int = 20):
        """Ingère tout un répertoire de textes."""
        corpus_path = Path(dir_path)
        total = 0
        for path in list(corpus_path.glob("*.txt"))[:max_files]:
            if path.stat().st_size < 100:
                continue
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.strip()
                    if len(line) > 30:
                        self.ingest(line)
                        total += 1
        log.info(f"Corpus ingéré: {total} lignes")
        return total

    def ruminate(self, max_pairs: int = 50000):
        """Lance la rumination nocturne (consolidation)."""
        self.unconscious.ruminate(max_pairs)

    # ── PROCESSUS PRINCIPAL ────────────────────────────────────────────────

    def _style_response(self, response: str, question: str, facts_used: list,
                        lang: str, candidates: list = None) -> str:
        """Applique le WaveStyler avec style/depth/personality configurés."""
        if not response:
            return response
        
        facts_to_style = list(facts_used) if facts_used else []
        if not facts_to_style and candidates:
            facts_to_style = [rec for rec, score in candidates[:3]]
        if not facts_to_style:
            return response

        # Contrôle de profondeur
        max_facts = {'court': 1, 'standard': 2, 'détaillé': 4}.get(
            getattr(self, '_current_depth', 'standard'), 2)
        facts_to_style = facts_to_style[:max_facts]

        try:
            from wave_styler import WaveStyler
            styler = WaveStyler(self.unconscious.encoder if self.unconscious else None)
            fact_tuples = [(f.sujet, f.relation, f.objet, f.secteur) for f in facts_to_style]
            style = getattr(self, '_current_style', 'auto')
            personality = getattr(self, '_current_personality', 'ka')
            styled = styler.render(fact_tuples, question, lang, style=style, personality=personality)
            if styled and len(styled) > 5:
                return styled
        except Exception:
            pass
        return response

    def chat(self, question: str, lang: str = 'fr') -> BrainResult:
        """
        Conversation multi-tours avec contexte ψ ondulatoire.
        Le contexte ψ est mis à jour automatiquement dans process().
        """
        result = self.process(question, lang=lang, use_conversation=True)
        # Extraire le sujet des faits acceptés pour les futurs enrichissements
        if self.conversation is not None and result.facts_used:
            self.conversation.last_subject = result.facts_used[0].sujet
        return result

    def _update_conv_context(self, question: str, response: str,
                              use_conversation: bool):
        """Post-processing : met à jour le contexte de conversation."""
        if not use_conversation or self.conversation is None or not response:
            return
        try:
            conv = self.conversation
            psi_q = conv._encode(question)
            psi_r = conv._encode(response)
            conv._update_context(psi_q, psi_r)
            conv.last_response = response
            conv.turn_count += 1
        except Exception:
            pass

    def process(self, question: str, lang: str = 'fr',
                max_accepted: int = 3, use_conversation: bool = False,
                style: str = 'auto', depth: str = 'standard',
                personality: str = 'ka', user_id: str = None) -> BrainResult:
        """
        Traitement complet par le cerveau harmonique.
        
        0. Parseur → analyse structurée + DÉTECTION DE DOMAINE
        0.5. Math bridge (interception mathématique)
        0.6. Wave logic (syllogismes, déductions)
        0.7. Wave reasoning (propagation de chaîne)
        1. Inconscient → retrieval pur (token pondérés, seuils du domaine)
        2. Conscient → filtre + feedback
        3. Expression → langage naturel (format adapté au type)
        
        Args:
            style: "auto"|"concise"|"elegant"|"pedagogique"|"chaleureux"
            depth: "court"|"standard"|"détaillé"
            personality: "ka"|"savant"|"vulgarisateur"|"poete"
            user_id: si fourni, fusionne avec la KB personnelle de l'utilisateur
            use_conversation: si True, utilise le contexte de conversation ψ
                              (follow-up detection, enrichissement, mémoire)
        """
        t_start = time.time()

        # Stocker pour usage dans _style_response / _try_compose
        self._current_style = style
        self._current_depth = depth
        self._current_personality = personality

        # ── 0.0 FAST PATH : Salutations, Identité, Conversation ──
        try:
            from domain_detector import (
                detect_question_type, handle_greeting, handle_identity,
                handle_out_of_domain
            )
            qtype = detect_question_type(question)
            lang = qtype.get('language', 'fr')

            # Identité (qui es-tu ?)
            if qtype.get('is_identity'):
                resp = handle_identity(lang=lang)
                if resp:
                    self._update_conv_context(question, resp, use_conversation)
                    return BrainResult(response=resp, confidence=1.0,
                        facts_used=[], facts_rejected=[], retrieval_count=0,
                        total_time_ms=(time.time()-t_start)*1000)

            # Salutations (bonjour, merci, au revoir)
            if qtype.get('is_greeting') or qtype.get('is_mercy') or qtype.get('is_bye'):
                resp = handle_greeting(
                    is_mercy=qtype.get('is_mercy', False),
                    is_bye=qtype.get('is_bye', False), lang=lang
                )
                if resp:
                    self._update_conv_context(question, resp, use_conversation)
                    return BrainResult(response=resp, confidence=1.0,
                        facts_used=[], facts_rejected=[], retrieval_count=0,
                        total_time_ms=(time.time()-t_start)*1000)

            # Hors-domaine → tenter la créativité avant d'abandonner
            if qtype.get('is_out_of_domain') and self._creator is not None:
                creative_resp = self._creator.create(question, max_iterations=3)
                if creative_resp and creative_resp.expression:
                    resp = creative_resp.expression
                    self._update_conv_context(question, resp, use_conversation)
                    return BrainResult(response=resp, confidence=0.5,
                        facts_used=[], facts_rejected=[], retrieval_count=0,
                        total_time_ms=(time.time()-t_start)*1000)
        except ImportError:
            lang = 'fr'

        # ── 0. PARSEUR + DOMAINE ──
        parsed = self.parser.parse(question)
        lang = parsed.lang
        self._current_domain = self._detect_domain(question)
        domain = self._get_adapter()

        # ── 0.1. CONVERSATION (contexte ψ multi-tours) ──
        enriched_question = question
        conv_meta = {}
        if use_conversation and self.conversation is not None:
            try:
                is_fu, coh = self.conversation._detect_followup(
                    question, self.conversation._encode(question))
                if is_fu:
                    enriched_question = self.conversation._enrich_question(question)
                conv_meta = {'is_followup': is_fu, 'coherence': coh,
                            'enriched': enriched_question if is_fu else question}
            except Exception:
                enriched_question = question

        # Injecter les tokens pondérés dans la question pour le retrieval
        weighted_question = enriched_question
        for token, weight in parsed.weighted_tokens.items():
            if weight >= 4.0:
                weighted_question += f" {token} {token}"
            elif weight >= 3.0:
                weighted_question += f" {token}"

        # 🎯 ATTENTION DYNAMIQUE : contextualiser les ψ avant retrieval
        if self._attention is not None:
            try:
                ctx_psi = self._attention.contextualize_query(weighted_question)
                if ctx_psi is not None:
                    # Injecter le ψ contextuel comme ψ de requête (override temporaire)
                    self._query_psi_override = ctx_psi
            except Exception:
                self._query_psi_override = None
        else:
            self._query_psi_override = None

        # ── 0.5. MICRO-CALCULATEUR (interception mathématique prioritaire) ──
        if try_math_solve:
            math_result = try_math_solve(question, lang)
            if math_result:
                response = math_result if math_result.endswith('.') else math_result + '.'
                self._update_conv_context(question, response, use_conversation)
                total_time = (time.time() - t_start) * 1000
                return BrainResult(
                    response=response,
                    confidence=0.95,
                    facts_used=[],
                    facts_rejected=[],
                    retrieval_count=0,
                    total_time_ms=total_time,
                )

        # ── 0.6. LOGIQUE ONDULATOIRE (questions de raisonnement pur) ──
        if self._is_logic_question(question, parsed):
            wave_result = self._try_wave_logic(question, parsed)
            if wave_result:
                total_time = (time.time() - t_start) * 1000
                return BrainResult(
                    response=wave_result,
                    confidence=0.90,
                    facts_used=[],
                    facts_rejected=[],
                    retrieval_count=0,
                    total_time_ms=total_time,
                )

        # ── 0.7. RAISONNEMENT PAR PROPAGATION (chaîne de résonance) ──
        if WaveReasoner is not None:
            try:
                chain_result = self._try_wave_chain(question)
                if chain_result:
                    response = self._style_response(chain_result, question, accepted, lang, candidates)
                    total_time = (time.time() - t_start) * 1000
                    return BrainResult(
                        response=response,
                        confidence=0.85,
                        facts_used=[],
                        facts_rejected=[],
                        retrieval_count=0,
                        total_time_ms=total_time,
                    )
            except Exception:
                pass

        # ── 1. INCONSCIENT : retrieval entity-centric + TF-IDF fallback ──
        # 🔍 ENTITY SEARCH (O(1) lookup, inspiré Obsidian)
        entity_candidates = self._entity_index.search(question, max_results=10)
        
        if entity_candidates and entity_candidates[0][1] > 5.0:
            candidates = entity_candidates
        else:
            candidates = self.unconscious.retrieve(weighted_question, max_results=15)
            if entity_candidates:
                candidates = self._merge_candidates(candidates, entity_candidates, user_boost=1.2)

        # 🌊 OndulatoireIndex : fallback si EntityIndex + TF-IDF échouent
        if not candidates or candidates[0][1] < 2.0:
            wave_candidates = self._wave_index.search(question, max_results=10, coherence_threshold=0.4)
            if wave_candidates:
                candidates = wave_candidates
        
        # Boost des candidats qui appartiennent au(x) domaine(s) détecté(s)
        detected_domains = self._detect_domains(question)
        if detected_domains and candidates:
            domain_sectors = set()
            for d in detected_domains:
                if d in self._domain_stores:
                    domain_sectors.update(self._domain_stores[d].sectors)
            
            if domain_sectors:
                boosted = []
                for rec, score in candidates:
                    if rec.secteur.upper().strip() in domain_sectors:
                        boosted.append((rec, score * 1.3))
                    else:
                        boosted.append((rec, score))
                boosted.sort(key=lambda x: -x[1])
                candidates = boosted

        # 👤 FUSION KB PERSONNELLE : si l'utilisateur a une KB spécialisée
        if user_id and user_id in self._user_kbs:
            try:
                user_brain = self._user_kbs[user_id]
                user_candidates = user_brain.unconscious.retrieve(
                    weighted_question, max_results=10
                )
                if user_candidates:
                    candidates = self._merge_candidates(
                        candidates, user_candidates, user_boost=1.5
                    )
                    log.debug(f"Fusion KB utilisateur {user_id}: "
                              f"{len(user_candidates)} perso + {len(candidates)} total")
            except Exception as e:
                log.debug(f"Fusion KB utilisateur ignorée ({e})")

        # Vérifier que les faits remontés correspondent BIEN à la question
        # Si un mot-clé important de la question n'apparaît nulle part → web
        if candidates and self._web is not None:
            q_keywords = set(_tokenize(_normalize(question)))
            COMMON_WORDS = {'capitale','pays','ville','monde','grand','petit','haut','bas',
                'plus','moins','trouve','situe','appelle','fonctionne','marche','passe',
                'donne','fait','quelle','quel','quand','comment','pourquoi','combien',
                'the','is','are','was','were','of','in','on','at','to','a','an','it'}
            important_words = {w for w in q_keywords if len(w) >= 4 and w not in COMMON_WORDS}
            if important_words:
                found_all = True
                for iw in important_words:
                    found_in_any = False
                    for rec, score in candidates[:5]:
                        fact_text = _normalize(f'{rec.sujet} {rec.relation} {rec.objet}')
                        if iw in fact_text:
                            found_in_any = True
                            break
                    if not found_in_any:
                        found_all = False
                        break
                if not found_all:
                    # Les mots-clés de la question ne sont pas dans les faits → web
                    web_result = self._try_web_search(question, lang)
                    if web_result:
                        self._update_conv_context(question, web_result.response, use_conversation)
                        return web_result

        retrieval_count = len(candidates)
        
        # 🔥 BOOST ONDULATOIRE : ajouter un bonus de résonance ψ aux scores TF-IDF
        if candidates and self.unconscious.encoder is not None:
            try:
                psi_q = self.unconscious.encoder.encode_query(weighted_question)
                if psi_q is not None and not np.all(psi_q == 0):
                    boosted = []
                    for rec, tfidf_score in candidates:
                        if rec.psi is not None:
                            coherence = float(np.real(np.dot(rec.psi, np.conj(psi_q))))
                            resonance_boost = max(0, coherence) * 0.3  # +0 à +0.3
                            boosted.append((rec, tfidf_score + resonance_boost))
                        else:
                            boosted.append((rec, tfidf_score))
                    boosted.sort(key=lambda x: -x[1])
                    candidates = boosted
            except Exception:
                pass  # Silencieux : garder les scores TF-IDF

        # ── 1.5. FILTRAGE PAR CONTEXTE (réduit le bruit en conversation) ──
        if use_conversation and self.conversation is not None and candidates:
            candidates = self._rerank_by_context(candidates, enriched_question)
            # Extraire le sujet pour les pronoms et le suivi
            best_subject = candidates[0][0].sujet if candidates else ""
            if self.conversation and best_subject:
                self.conversation.last_subject = best_subject
                conv_meta['subject'] = best_subject

        # ── 2. CONSCIENT : filtrer + feedback ──
        accepted, rejected = self.conscious.filter(question, candidates, max_accepted)
        self.conscious.feedback(accepted, rejected)

        # ── 2b. INTELLIGENCE CONSCIENTE : raisonner si confiance faible ──
        # GARDE-FOU : si aucun candidat → tenter le web avant d'abandonner
        if not accepted and not candidates:
            # 🌐 Fallback Internet
            web_result = self._try_web_search(question, lang)
            if web_result:
                self._update_conv_context(question, web_result.response, use_conversation)
                return web_result

            response = self._dont_know(question, lang)
            total_time = (time.time() - t_start) * 1000
            return BrainResult(
                response=response, confidence=0.0,
                facts_used=[], facts_rejected=[],
                retrieval_count=0, total_time_ms=total_time,
            )
        
        # GARDE-FOU 2 : si les candidats sont de très faible qualité → tenter le web
        if not accepted and candidates:
            best_score = candidates[0][1] if candidates else 0
            if best_score < 1.0:  # Score trop faible → probablement hors KB
                # 🌐 Fallback Internet
                web_result = self._try_web_search(question, lang)
                if web_result:
                    self._update_conv_context(question, web_result.response, use_conversation)
                    return web_result

                response = self._dont_know(question, lang)
                total_time = (time.time() - t_start) * 1000
                return BrainResult(
                    response=response, confidence=0.0,
                    facts_used=[], facts_rejected=[],
                    retrieval_count=retrieval_count, total_time_ms=total_time,
                )
        
        # GARDE-FOU 3 : le sujet spécifique de la question n'apparaît dans aucun candidat
        # → probablement hors KB. S'applique MÊME si des candidats ont été acceptés.
        if candidates:
            q_keywords = set(_tokenize(_normalize(question)))
            COMMON = {'capitale', 'pays', 'ville', 'monde', 'grand',
                      'petit', 'haut', 'bas', 'plus', 'moins', 'trouve', 'situe',
                      'appelle', 'fonctionne', 'marche', 'passe', 'donne', 'fait',
                      'quelle', 'quel', 'quand', 'comment', 'pourquoi', 'combien'}
            q_subjects = {w for w in q_keywords if len(w) >= 3 and w not in COMMON}
            if q_subjects:
                found = False
                for rec, score in candidates[:5]:
                    fact_words = set(_tokenize(_normalize(
                        f'{rec.sujet} {rec.relation} {rec.objet}')))
                    if q_subjects & fact_words:
                        found = True
                        break
                if not found:
                    # 🌐 Fallback Internet avant d'abandonner
                    web_result = self._try_web_search(question, lang)
                    if web_result:
                        self._update_conv_context(question, web_result.response, use_conversation)
                        return web_result

                    response = self._dont_know(question, lang)
                    total_time = (time.time() - t_start) * 1000
                    return BrainResult(
                        response=response, confidence=0.0,
                        facts_used=[], facts_rejected=[],
                        retrieval_count=retrieval_count, total_time_ms=total_time,
                    )

        if not accepted or (accepted and accepted[0].confidence < 0.5):
            answer, conf, method = self.intelligence.reason(
                question, candidates, parsed
            )
            if answer and conf > 0.5:
                # Le conscient intelligent a trouvé une réponse par raisonnement
                response = self._style_response(answer, question, accepted, lang, candidates)
                total_time = (time.time() - t_start) * 1000
                return BrainResult(
                    response=response,
                    confidence=conf,
                    facts_used=accepted,
                    facts_rejected=rejected,
                    retrieval_count=retrieval_count,
                    total_time_ms=total_time,
                )

        # ── 2c. RAISONNEMENT PROFOND (Phase Amplifier) ──
        # Si le conscient intelligent n'a pas trouvé, tenter la propagation amplifiée
        if self._deep_reasoner is not None and (not accepted or
                (accepted and accepted[0].confidence < 0.5)):
            try:
                # Essayer d'abord le multi-branche (plus puissant)
                deep_answer = self._deep_reasoner.reason_deep_multi(
                    question, max_depth=7, beam_width=3
                )
                if deep_answer and len(deep_answer) > 40:
                    response = self._style_response(deep_answer, question, accepted, lang, candidates)
                    total_time = (time.time() - t_start) * 1000
                    return BrainResult(
                        response=response,
                        confidence=0.70,
                        facts_used=accepted,
                        facts_rejected=rejected,
                        retrieval_count=retrieval_count,
                        total_time_ms=total_time,
                    )
            except Exception:
                # Fallback : mono-branche simple
                try:
                    deep_answer = self._deep_reasoner.reason_deep(question, max_depth=7)
                    if deep_answer and len(deep_answer) > 40:
                        response = self._style_response(deep_answer, question, accepted, lang, candidates)
                        total_time = (time.time() - t_start) * 1000
                        return BrainResult(
                            response=response,
                            confidence=0.65,
                            facts_used=accepted,
                            facts_rejected=rejected,
                            retrieval_count=retrieval_count,
                            total_time_ms=total_time,
                        )
                except Exception:
                    pass

        # ── 3. EXPRESSION : adaptée au type de question ──
        response = self._try_compose(accepted, question, parsed, lang)
        if not response:
            response = self._express(accepted, question, parsed)

        total_time = (time.time() - t_start) * 1000

        confidence = 0.0
        if accepted:
            confidence = sum(r.confidence for r in accepted) / len(accepted)

        # 🌐 FALLBACK WEB : si confiance trop faible, tenter Internet
        if confidence < 0.35 and self._web is not None:
            web_result = self._try_web_search(question, lang)
            if web_result:
                self._update_conv_context(question, web_result.response, use_conversation)
                return web_result

        # 🔥 Mise à jour du contexte de conversation
        self._update_conv_context(question, response, use_conversation)

        # 🔥 Appliquer le WaveStyler (améliore TOUTES les réponses)
        response = self._style_response(response, question, accepted, lang, candidates)

        # 🔥 DÉDUPLICATION + FILTRE LANGUE : nettoyer la réponse
        response = self._clean_response(response, lang)

        # 🎭 DIALOGUE HARMONIQUE : transformer la réponse brute en expression naturelle
        if self._dialogue is not None and response:
            try:
                # Extraire les faits pour le dialogue
                facts_for_dialogue = [
                    (f.sujet, f.relation, f.objet, f.secteur)
                    for f in (accepted or [])
                ]
                response = self._dialogue.respond(
                    question=question,
                    facts=facts_for_dialogue if facts_for_dialogue else None,
                    brain_response=response,
                    confidence=confidence,
                )
            except Exception:
                pass  # fallback silencieux à la réponse brute

        # 📚 APPRENTISSAGE CONTINU : feedback + fine-tune périodique
        self._maybe_learn(question, response, confidence, accepted)

        return BrainResult(
            response=response,
            confidence=min(1.0, confidence),
            facts_used=accepted,
            facts_rejected=rejected,
            retrieval_count=retrieval_count,
            total_time_ms=total_time,
        )

    # ── EXPRESSION ─────────────────────────────────────────────────────────

    # 🎨 CRÉATIVITÉ ─────────────────────────────────────────────────────────
    def create(self, prompt: str = "trouve une connexion creative",
               max_iterations: int = 5) -> str:
        """
        Créativité ondulatoire — le conscient manipule l'inconscient.
        
        Combine des concepts par opérations ondulatoires (superposition,
        convolution, déphasage...) et fait émerger des connexions nouvelles.
        """
        if self._creator is None:
            return "Créativité non disponible (module manquant)"
        idea = self._creator.create(prompt, max_iterations=max_iterations)
        return idea.expression if idea else "Aucune idée créative émergée."

    def start_ruminating(self, interval: float = 2.0):
        """Démarre la rumination créative en arrière-plan."""
        if self._creator:
            self._creator.start_ruminating(interval)

    def stop_ruminating(self):
        """Arrête la rumination créative."""
        if self._creator:
            self._creator.stop_ruminating()

    def get_creative_ideas(self, n: int = 5) -> list:
        """Récupère les idées émergentes de la rumination."""
        if self._creator:
            return [i.expression for i in self._creator.get_emergent_ideas(n)]
        return []

    def get_style(self) -> str:
        """Décrit le style créatif émergent du cerveau."""
        if self._creator:
            return self._creator.get_style_description()
        return "Style non disponible."

    # 📖 RÉSUMÉ HARMONIQUE ─────────────────────────────────────────────────
    def summarize(self, text: str, max_facts: int = 15) -> dict:
        """
        Résume un texte long en extrayant ses piliers de connaissance.

        Args:
            text: texte à résumer (1 à 50 pages)
            max_facts: nombre max de faits dans le résumé

        Returns:
            dict avec summary, key_facts, themes, contradictions, stats
        """
        if self._summarizer is None:
            return {'summary': 'Résumeur non disponible', 'key_facts': []}
        result = self._summarizer.summarize(text, max_facts=max_facts)
        return {
            'summary': result.summary,
            'key_facts': [{'subject': s, 'relation': r, 'object': o, 'centrality': round(c, 4)}
                         for s, r, o, c in result.key_facts],
            'themes': result.key_themes,
            'contradictions': len(result.contradictions),
            'stats': result.stats,
        }

    # 🧪 FEW-SHOT LEARNING ──────────────────────────────────────────────────
    def few_shot(self, examples: List[Tuple[str, str]], query: str,
                 pattern_type: str = "general") -> 'BrainResult':
        """
        Apprentissage few-shot par injection temporaire de pattern.

        Montre 3 exemples au cerveau, qui extrait le ψ_pattern commun,
        l'injecte temporairement dans l'hologramme, traite la requête,
        puis laisse le pattern s'estomper naturellement.

        Args:
            examples: liste de (input, output) — les exemples
            query: la nouvelle requête à traiter
            pattern_type: type de pattern

        Returns:
            BrainResult avec la réponse
        """
        if self._few_shot is None:
            return BrainResult(
                response="Few-shot learning non disponible (module manquant)",
                confidence=0.0,
                facts_used=[], facts_rejected=[],
                retrieval_count=0, total_time_ms=0,
            )

        try:
            result = self._few_shot.process(
                examples=examples,
                query=query,
                pattern_type=pattern_type,
            )
            return BrainResult(
                response=result.response,
                confidence=result.confidence,
                facts_used=result.facts_from_kb,
                facts_rejected=[],
                retrieval_count=len(result.facts_from_kb) + len(result.facts_from_pattern),
                total_time_ms=0,
            )
        except Exception as e:
            return BrainResult(
                response=f"Erreur few-shot: {e}",
                confidence=0.0,
                facts_used=[], facts_rejected=[],
                retrieval_count=0, total_time_ms=0,
            )

    # 📚 APPRENTISSAGE CONTINU ──────────────────────────────────────────────
    def _maybe_learn(self, question: str, response: str, confidence: float,
                     accepted: List):
        """
        Apprentissage continu après chaque interaction réussie.
        """
        self._learn_count += 1

        # 1. FEEDBACK : renforcer les faits utilisés
        if self._feedback is not None and confidence > 0.4:
            try:
                for fact in accepted:
                    if hasattr(fact, 'sujet'):
                        key = (_normalize(fact.sujet), _normalize(fact.relation),
                               _normalize(fact.objet))
                        if key in self.unconscious.registry:
                            record = self.unconscious.registry[key]
                            record.amplitude += 0.1 * confidence
                            record.times_accepted += 1
                            if confidence > 0.7:
                                record.confidence = min(1.0, record.confidence + 0.02)
            except Exception:
                pass

        # 2. FINE-TUNE périodique (Fourier ALS)
        if (self._fine_tuner is not None and
                self._learn_count % self._learn_every == 0 and
                len(self.unconscious.registry) > 100):
            try:
                kb_list = [
                    (r.sujet, r.relation, r.objet, r.secteur)
                    for r in self.unconscious.registry.values()
                    if r.times_accepted > 0
                ][:50000]
                if len(kb_list) > 500:
                    history = self._fine_tuner.fine_tune(kb_list, epochs=2, verbose=False)
                    log.info(f"📚 Fine-tune: {history['words_updated'][-1]} mots, "
                             f"loss={history['loss'][-1]:.4f}")
            except Exception as e:
                log.debug(f"Fine-tune skipped: {e}")

        # 3. AUTO-CURRICULUM périodique
        if (self._fast_learner is not None and
                self._learn_count % (self._learn_every * 10) == 0):
            try:
                self._fast_learner.auto_curriculum(target_patterns=10)
            except Exception:
                pass

    def learn(self):
        """Lance un cycle d'apprentissage complet."""
        results = {'fine_tuned': False, 'curriculum': False}
        if self._fine_tuner is not None:
            try:
                kb_list = [(r.sujet, r.relation, r.objet, r.secteur)
                           for r in self.unconscious.registry.values()][:50000]
                if len(kb_list) > 500:
                    self._fine_tuner.fine_tune(kb_list, epochs=3, verbose=True)
                    results['fine_tuned'] = True
            except Exception as e:
                log.warning(f"Fine-tune failed: {e}")
        if self._fast_learner is not None:
            try:
                self._fast_learner.auto_curriculum(target_patterns=20)
                results['curriculum'] = True
            except Exception as e:
                log.warning(f"Curriculum failed: {e}")
        return results

    # 🌐 WEB SEARCH FALLBACK ─────────────────────────────────────────────────
    def _try_web_search(self, question: str, lang: str = 'fr') -> Optional[BrainResult]:
        """
        Tente une recherche Internet si la KB interne n'a rien trouvé.

        Returns:
            BrainResult si une réponse web a été trouvée, None sinon.
        """
        if self._web is None:
            return None

        try:
            results = self._web.search_web(question, max_results=3)
            if not results:
                return None

            # Construire une réponse à partir des résultats web
            best = results[0]
            summary = best.get('summary') or best.get('snippet') or ''

            if len(summary) < 30:
                return None

            # Formater la réponse selon la source
            source_name = best.get('source', 'web')
            title = best.get('title', '')
            url = best.get('url', '')

            if source_name == 'wikipedia':
                prefix = "Selon Wikipédia" if lang == 'fr' else "According to Wikipedia"
            elif source_name == 'duckduckgo':
                prefix = "D'après DuckDuckGo" if lang == 'fr' else "According to DuckDuckGo"
            else:
                prefix = "D'après une recherche web" if lang == 'fr' else "According to a web search"

            if title and title.lower() not in summary.lower():
                response = f"{prefix}, {title} : {summary}"
            else:
                response = f"{prefix} : {summary}"

            # Ajouter les sources additionnelles si disponibles
            if len(results) >= 2:
                extra_sources = []
                for r in results[1:3]:
                    if r.get('snippet') and len(r['snippet']) > 40:
                        extra_sources.append(f"• {r.get('title', 'Source')} : {r['snippet'][:200]}…")
                if extra_sources:
                    response += "\n\nSources complémentaires :\n" + "\n".join(extra_sources)

            # Ajouter les URLs
            if url:
                response += f"\n\n🔗 {url}"
                for r in results[1:2]:
                    if r.get('url'):
                        response += f"\n🔗 {r['url']}"

            t_start = time.time()
            total_time = (time.time() - t_start) * 1000  # approximatif

            return BrainResult(
                response=response,
                confidence=0.60,  # confiance modérée pour le web
                facts_used=[],
                facts_rejected=[],
                retrieval_count=len(results),
                total_time_ms=total_time,
            )
        except Exception:
            return None

    def _is_logic_question(self, question: str, parsed) -> bool:
        """Détecte si la question relève du raisonnement logique pur."""
        q = question.lower()
        logic_markers = [
            'syllogisme', 'deduire', 'deduction', 'donc', 'alors',
            'que peut-on', 'que deduire', 'que conclure', 'conclusion',
            'est-ce coherent', 'contradiction', 'compatible',
            'si ', 'alors ', 'donc ', 'par consequent',
        ]
        # Questions très courtes qui ressemblent à des demandes de raisonnement
        if any(m in q for m in logic_markers):
            return True
        # Questions avec structure "A est B, B est C"
        if parsed and parsed.type in ('identite', 'explication'):
            if ',' in question or ' et ' in question.lower():
                return True
        return False

    def _try_wave_logic(self, question: str, parsed) -> str:
        """Tente de résoudre par logique ondulatoire (WaveLogic)."""
        if WaveLogic is None:
            return None
        try:
            # Extraire les prémisses de la question
            premises = self._extract_premises(question)
            if len(premises) < 1:
                return None

            wl = WaveLogic(self)
            result = wl.solve(premises=premises, question=question)

            if result and result.is_valid and result.confidence > 0.5:
                return result.conclusion
        except Exception:
            pass
        return None

    def _extract_premises(self, question: str) -> list:
        """Extrait les prémisses d'une question (séparées par ',', 'et', 'puisque')."""
        parts = re.split(r'[,;]\s*|\s+et\s+|\s+donc\s+|\s+or\s+|\s+puisque\s+|\s+car\s+', question)
        premises = [p.strip() for p in parts if len(p.strip()) > 5]
        premises = [p for p in premises if not p.startswith('?') and not p.startswith('que ') 
                    and not p.startswith('quelle ') and not p.startswith('quel ')]
        return premises

    def _try_wave_chain(self, question: str) -> str:
        """Raisonnement par propagation de ψ à travers l'hologramme."""
        if WaveReasoner is None:
            return None
        try:
            reasoner = WaveReasoner(self)
            chain = reasoner.reason(question, max_depth=3)
            if chain and chain.is_valid and chain.conclusion:
                return chain.conclusion
        except Exception:
            pass
        return None

    def _try_compose(self, facts: List[FactRecord], question: str,
                     parsed: StructuredPrompt = None, lang: str = 'fr') -> str:
        """Compose une réponse naturelle avec style/depth/personality."""
        # Contrôle de profondeur
        max_facts = {'court': 1, 'standard': 2, 'détaillé': 4}.get(
            getattr(self, '_current_depth', 'standard'), 2)
        facts = facts[:max_facts]

        try:
            from wave_styler import WaveStyler
            styler = WaveStyler(self.unconscious.encoder if self.unconscious else None)
            fact_tuples = [(f.sujet, f.relation, f.objet, f.secteur) for f in facts]
            style = getattr(self, '_current_style', 'auto')
            personality = getattr(self, '_current_personality', 'ka')
            return styler.render(fact_tuples, question, lang, style=style, personality=personality)
        except Exception:
            pass

        # Fallback : rendu simple
        import random
        if not facts:
            return ""
        f0 = facts[0]
        s = f0.sujet[0].upper() + f0.sujet[1:] if f0.sujet else f0.sujet
        parts = [f"{s} {f0.relation} {f0.objet}."]
        for f in facts[1:]:
            parts.append(f"{f.sujet} {f.relation} {f.objet}.")
        return ' '.join(parts)

    def _rerank_by_context(self, candidates: List, question: str) -> List:
        """
        Re-classe les candidats par contexte (ψ + secteur).
        - Cohérence ψ > 0.08 → boost ×(1+coh×3)
        - Cohérence ψ < -0.02 → pénalité ×0.1
        - Même secteur que le tour précédent → boost ×1.5
        - Secteur différent → pénalité ×0.3
        """
        if not candidates or self.conversation is None:
            return candidates
        
        conv = self.conversation
        if np.all(conv.psi_context == 0) and not conv.last_subject:
            return candidates
        
        # Déterminer le secteur dominant du tour précédent
        prev_facts = []
        if hasattr(conv, 'last_response') and conv.last_response:
            prev_facts = self._extract_facts_from_text(conv.last_response)
        prev_sectors = set(f.secteur for f in prev_facts if f.secteur) if prev_facts else set()
        
        scored = []
        for rec, score in candidates:
            adjusted = score
            
            # Filtrage par cohérence ψ
            try:
                psi_fact = rec.psi if hasattr(rec, 'psi') and rec.psi is not None else None
                if psi_fact is None and hasattr(self.unconscious, 'encoder'):
                    psi_fact = self.unconscious.encoder.encode_query(
                        f'{rec.sujet} {rec.objet}')
                
                if psi_fact is not None and not np.all(conv.psi_context == 0):
                    coherence = float(np.real(np.dot(psi_fact, np.conj(conv.psi_context))))
                    if coherence > 0.08:
                        adjusted *= (1.0 + coherence * 3)
                    elif coherence < -0.02:
                        adjusted *= 0.1
                    else:
                        adjusted *= 0.5
            except Exception:
                pass
            
                # Filtrage par secteur (plus fiable que ψ seul)
            if prev_sectors and hasattr(rec, 'secteur'):
                if rec.secteur in prev_sectors:
                    adjusted *= 1.8  # Même secteur → fort boost
                elif rec.secteur and prev_sectors:
                    # Secteur différent → pénalité forte SAUF si le score ψ est élevé
                    if adjusted < score * 0.5:
                        adjusted *= 0.15  # Très probablement du bruit
            
            scored.append((rec, adjusted))
        
        scored.sort(key=lambda x: -x[1])
        
        # Filtrer les scores trop bas (bruit évident)
        if scored and len(scored) > 3:
            max_score = scored[0][1]
            # Ne garder que les candidats avec score > 25% du meilleur
            scored = [(r, s) for r, s in scored if s > max_score * 0.25]
            # Maximum 5 candidats pour limiter le bruit
            scored = scored[:5]
        
        return scored

    def _extract_facts_from_text(self, text: str) -> list:
        """Extrait les FactRecords mentionnés dans un texte de réponse."""
        if not text or not hasattr(self, 'unconscious'):
            return []
        found = []
        text_lower = text.lower()
        for key, rec in self.unconscious.registry.items():
            if rec.sujet.lower() in text_lower:
                found.append(rec)
            if len(found) >= 3:
                break
        return found

    def _clean_response(self, response: str, lang: str) -> str:
        """Nettoie et formate la réponse."""
        if not response:
            return response
        
        # 🆕 Formater : capitaliser la première lettre, ponctuation finale
        response = response.strip()
        if response and response[0].islower():
            response = response[0].upper() + response[1:]
        if response and response[-1] not in '.!?':
            response += '.'
        
        # Découper en phrases
        sentences = [s.strip() for s in response.replace('?', '.').replace('!', '.').split('.') if s.strip()]
        if len(sentences) <= 1:
            return response
        
        # Dédupliquer par similarité (garder la première occurrence)
        seen_norm = set()
        unique = []
        for s in sentences:
            norm = _normalize(s)[:50]  # 50 premiers caractères normalisés
            if norm not in seen_norm:
                seen_norm.add(norm)
                unique.append(s)
        
        # Filtre de langue : détecter les phrases en anglais dans une réponse FR
        if lang == 'fr':
            EN_MARKERS = {'the', 'is', 'are', 'was', 'were', 'has', 'have', 'of', 'in', 'by'}
            filtered = []
            for s in unique:
                words = set(s.lower().split())
                en_score = len(words & EN_MARKERS)
                if en_score >= 3:  # Trop de mots anglais → probablement EN
                    continue
                filtered.append(s)
            if filtered:
                unique = filtered
        
        return '. '.join(unique) + '.' if unique else response
        """Rendu simple : sujet relation objet, avec connecteurs de base."""
        import random
        if not facts:
            return ""
        s = facts[0].sujet[0].upper() + facts[0].sujet[1:] if facts[0].sujet else ""
        parts = [f"{s} {facts[0].relation} {facts[0].objet}."]
        connectors = ["De plus, ", "Par ailleurs, ", "Également, "]
        for f in facts[1:]:
            parts.append(f"{random.choice(connectors)}{f.sujet} {f.relation} {f.objet}.")
        return ' '.join(parts)

    def _dont_know(self, question: str, lang: str) -> str:
        """Réponse quand on ne sait pas — honnête, pas d'invention."""
        sujet = question.strip('?.,!;: ')[:80]
        if lang == 'en':
            return f"I don't have enough information about '{sujet}' to answer with confidence."
        return f"Je n'ai pas assez d'éléments sur « {sujet} » pour répondre avec confiance."

    def _express(self, facts: List[FactRecord], question: str,
                 parsed: StructuredPrompt = None) -> str:
        """Exprime les faits validés — adaptatif au type de question."""
        if not facts:
            sujet = question.strip('?.,!;: ')[:80]
            if parsed and parsed.lang == 'en':
                return f"I don't have enough information about '{sujet}' to answer with confidence."
            return f"Je n'ai pas assez d'éléments sur « {sujet} » pour répondre avec confiance."

        lang = parsed.lang if parsed else 'fr'

        # 🔥 TENTATIVE COMPOSER (style naturel, 30+ structures)
        if self.composer is not None:
            try:
                composed = self._try_compose(facts, question, parsed, lang)
                if composed:
                    return composed
            except Exception:
                pass  # Fallback vers les templates simples

        # Fallback : templates simples
        is_explanatory = parsed.is_explanatory if parsed else False

        # Si question simple → 1 seul fait
        if not is_explanatory or len(facts) == 1:
            return self._render_single(facts[0], lang)

        # Question explicative avec 2 faits → connectés
        if len(facts) == 2:
            return self._render_pair(facts[0], facts[1], lang)

        # Question explicative avec 3+ faits → paragraphe
        return self._render_multi(facts, question, lang)

    def _render_single(self, rec: FactRecord, lang: str) -> str:
        """Rend un fait unique en phrase naturelle."""
        s = rec.sujet[0].upper() + rec.sujet[1:] if rec.sujet else rec.sujet
        return f"{s} {rec.relation} {rec.objet}."

    def _render_pair(self, f1: FactRecord, f2: FactRecord, lang: str) -> str:
        """Deux faits avec connecteur."""
        s1 = self._render_single(f1, lang).rstrip('.')
        s2 = self._render_single(f2, lang)
        s2 = s2[0].lower() + s2[1:]

        connectors_fr = ['De plus, ', 'Par ailleurs, ', 'Également, ']
        connectors_en = ['Moreover, ', 'Furthermore, ', 'Additionally, ']
        conn = (connectors_fr if lang == 'fr' else connectors_en)[0]

        return f"{s1}. {conn}{s2}"

    def _render_multi(self, facts: List[FactRecord], question: str, lang: str) -> str:
        """Mini-paragraphe pour 3 faits."""
        intro_fr = ['D\'abord, ', 'En premier lieu, ', 'Fondamentalement, ']
        intro_en = ['First, ', 'Primarily, ', 'Fundamentally, ']
        mid_fr = ['De plus, ', 'Par ailleurs, ']
        mid_en = ['Moreover, ', 'Furthermore, ']
        concl_fr = ['Ainsi, ']
        concl_en = ['Thus, ']

        intro = (intro_fr if lang == 'fr' else intro_en)[hash(question) % 3]
        mid = (mid_fr if lang == 'fr' else mid_en)
        concl = (concl_fr if lang == 'fr' else concl_en)[0]

        sentences = []
        first = self._render_single(facts[0], lang)
        sentences.append(intro + first[0].lower() + first[1:])

        for i, f in enumerate(facts[1:-1]):
            s = self._render_single(f, lang)
            sentences.append(mid[i % len(mid)] + s[0].lower() + s[1:])

        last = self._render_single(facts[-1], lang)
        sentences.append(concl + last[0].lower() + last[1:])

        return ' '.join(sentences)

    # ── STATS ──────────────────────────────────────────────────────────────

    @property
    def stats(self) -> dict:
        return {
            'inconscient': self.unconscious.stats,
            'init_time_s': round(self._init_time, 1),
            'current_domain': self._current_domain,
            'domains_available': list(DOMAINS.keys()),
            'web_retriever': self._web is not None,
            'deep_reasoner': self._deep_reasoner is not None,
            'few_shot': self._few_shot is not None,
            'harmonic_attention': self._attention is not None,
            'fine_tuner': self._fine_tuner is not None,
            'fast_learner': self._fast_learner is not None,
            'feedback_loop': self._feedback is not None,
            'conscious_creator': self._creator is not None,
            'harmonic_summarizer': self._summarizer is not None,
            'harmonic_dialogue': self._dialogue is not None,
            'learn_count': self._learn_count,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
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
        ("paris", "est la capitale de", "la france", "GEOGRAPHIE"),
        ("tokyo", "est la capitale du", "japon", "GEOGRAPHIE"),
        ("leonard de vinci", "a peint", "la joconde", "ART"),
        ("phi", "est le", "nombre d or", "MATHS_PURES"),
    ]

    print("=" * 60)
    print("Initialisation du cerveau harmonique...")
    brain = HarmonicBrain(test_kb)
    print(f"Stats inconscient: {brain.unconscious.stats}")
    print(f"  → {len(brain.unconscious.registry)} faits stockés sans filtrage")

    # Test d'ingestion répétée (renforcement)
    print("\n--- Test de répétition ---")
    for _ in range(3):
        brain.ingest("La lumière est une onde électromagnétique.")
    rec = brain.unconscious.registry.get(('lumiere', 'est une', 'onde electromagnetique'))
    if rec:
        print(f"  'lumiere est une onde...' → amplitude={rec.amplitude:.1f}, count={rec.count}")

    # Test des questions
    print("\n--- Questions ---")
    tests = [
        "explique la lumiere",
        "capitale de la france",
        "qui a peint la joconde",
        "nombre d or",
    ]
    for q in tests:
        result = brain.process(q)
        print(f"\nQ: {q}")
        print(f"R: {result.response}")
        print(f"   confiance={result.confidence:.2f} | "
              f"remontés={result.retrieval_count} | "
              f"acceptés={len(result.facts_used)} | "
              f"rejetés={len(result.facts_rejected)} | "
              f"{result.total_time_ms:.0f}ms")

    # Test rumination
    print("\n--- Rumination ---")
    brain.ruminate(max_pairs=100)
    print(f"  Stats après rumination: {brain.unconscious.stats}")
