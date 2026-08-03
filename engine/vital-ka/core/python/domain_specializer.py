"""
Domain Specializer — Spécialisation Dynamique de l'IA Harmonique
================================================================
Permet à l'utilisateur de dire « Spécialise-toi en [domaine] » et le système
explore le web de façon encyclopédique, extrait des triplets de connaissance,
construit une base holographique personnelle persistante.

Pipeline :
  1. Génération de requêtes systématiques
  2. Exploration web multi-niveaux (Wikipedia + web large)
  3. Extraction de triplets (regex + LLM)
  4. Construction de la KB holographique personnelle
  5. Rapport de spécialisation

Usage :
  spec = DomainSpecializer(brain=brain, web_retriever=web)
  result = spec.specialize("photographie", "expert", "user_123")
  print(result.message)
"""

import os
import re
import sys
import time
import json
import uuid
import logging
import threading
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Callable, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter

import numpy as np

log = logging.getLogger(__name__)

# ── Chemins ────────────────────────────────────────────────────────────────
_ENGINE_DIR = Path(__file__).resolve().parent
_USERS_DIR = _ENGINE_DIR / "data" / "users"
_USERS_DIR.mkdir(parents=True, exist_ok=True)

# ── Imports locaux (lazy pour éviter les circulaires) ─────────────────────
_WEB_RETRIEVER = None
_BOOTSTRAPPER_LLM = None
_BOOTSTRAPPER_SIMPLE = None
_HarmonicBrain = None
_UserProfile = None


def _ensure_imports():
    """Initialise les imports lazy."""
    global _WEB_RETRIEVER, _BOOTSTRAPPER_LLM, _BOOTSTRAPPER_SIMPLE, _HarmonicBrain, _UserProfile

    if _HarmonicBrain is None:
        sys.path.insert(0, str(_ENGINE_DIR))
        from harmonic_brain import HarmonicBrain
        _HarmonicBrain = HarmonicBrain

    if _BOOTSTRAPPER_LLM is None:
        try:
            from bootstrapper import extract_triples_llm
            _BOOTSTRAPPER_LLM = extract_triples_llm
        except ImportError:
            _BOOTSTRAPPER_LLM = None

    if _BOOTSTRAPPER_SIMPLE is None:
        try:
            from bootstrapper import extract_triples_simple
            _BOOTSTRAPPER_SIMPLE = extract_triples_simple
        except ImportError:
            _BOOTSTRAPPER_SIMPLE = None

    if _UserProfile is None:
        try:
            from memory.user_profile import UserProfile
            _UserProfile = UserProfile
        except ImportError:
            _UserProfile = None


# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURES DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SpecializationResult:
    """Résultat d'une spécialisation terminée."""
    domain: str
    depth: str
    triplets_count: int
    sources_count: int
    kb_path: str
    elapsed_seconds: float
    top_concepts: List[str] = field(default_factory=list)
    message: str = ""
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "domain": self.domain,
            "depth": self.depth,
            "triplets_count": self.triplets_count,
            "sources_count": self.sources_count,
            "kb_path": self.kb_path,
            "elapsed_seconds": round(self.elapsed_seconds, 1),
            "top_concepts": self.top_concepts[:10],
            "message": self.message,
            "success": self.success,
            "error": self.error,
        }


@dataclass
class SpecializationJob:
    """Tâche de spécialisation en cours ou terminée."""
    job_id: str
    user_id: str
    domain: str
    depth: str
    status: str = "pending"  # pending | searching | extracting | encoding | done | error
    progress: float = 0.0
    queries_done: int = 0
    queries_total: int = 0
    triplets_extracted: int = 0
    sources_consulted: int = 0
    started_at: str = ""
    eta_seconds: float = 0.0
    result: Optional[SpecializationResult] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        d = {
            "job_id": self.job_id,
            "user_id": self.user_id,
            "domain": self.domain,
            "depth": self.depth,
            "status": self.status,
            "progress": round(self.progress, 3),
            "queries_done": self.queries_done,
            "queries_total": self.queries_total,
            "triplets_extracted": self.triplets_extracted,
            "sources_consulted": self.sources_consulted,
            "started_at": self.started_at,
            "eta_seconds": round(self.eta_seconds, 1),
        }
        if self.result:
            d["result"] = self.result.to_dict()
        if self.error:
            d["error"] = self.error
        return d


@dataclass
class FilteredResult:
    """Résultat du filtrage qualité des triplets."""
    triplets: List[Tuple]  # (s, r, o, sec, amplitude)
    stats: Dict = field(default_factory=dict)
    top_concepts: List[str] = field(default_factory=list)
    
    @property
    def gold_count(self) -> int:
        return self.stats.get('gold', 0)
    
    @property
    def silver_count(self) -> int:
        return self.stats.get('silver', 0)
    
    @property
    def bronze_count(self) -> int:
        return self.stats.get('bronze', 0)
    
    @property
    def rejected_count(self) -> int:
        return self.stats.get('rejected', 0)
    
    @property
    def total_accepted(self) -> int:
        return self.gold_count + self.silver_count + self.bronze_count

    def to_dict(self) -> Dict:
        return {
            "triplets_count": len(self.triplets),
            "gold": self.gold_count,
            "silver": self.silver_count,
            "bronze": self.bronze_count,
            "rejected": self.rejected_count,
            "acceptance_rate": round(
                self.total_accepted / max(self.total_accepted + self.rejected_count, 1), 3
            ),
            "top_concepts": self.top_concepts[:10],
            "rejection_reasons": self.stats.get('rejection_reasons', {}),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# GÉNÉRATION DE REQUÊTES SYSTÉMATIQUES
# ═══════════════════════════════════════════════════════════════════════════════

# Templates de requêtes par niveau de profondeur
_QUERY_TEMPLATES = {
    "debutant": [
        "{domain}",
        "qu'est-ce que {domain}",
        "{domain} introduction",
        "{domain} principes de base",
        "{domain} guide débutant",
        "histoire de {domain}",
        "{domain} fondamentaux",
        "{domain} explication simple",
        "{domain} pour débutants",
        "apprendre {domain}",
        "comprendre {domain}",
        "{domain} concepts clés",
    ],
    "avance": [
        # Reprend les requêtes débutant +
        "{domain} techniques avancées",
        "{domain} méthodes",
        "{domain} outils professionnels",
        "{domain} workflow",
        "{domain} bonnes pratiques",
        "{domain} théorie",
        "{domain} analyse",
        "{domain} méthodologie",
        "{domain} processus",
        "{domain} standards",
        "{domain} certification",
        "{domain} école",
        "types de {domain}",
        "classification {domain}",
    ],
    "expert": [
        # Reprend avancé +
        "{domain} recherche",
        "{domain} innovation",
        "{domain} pointe",
        "{domain} expert",
        "{domain} maîtrise",
        "{domain} performance",
        "{domain} optimisation",
        "{domain} cas limites",
        "{domain} contre-intuitif",
        "{domain} pièges",
        "{domain} controverses",
        "{domain} science",
        "{domain} ingénierie",
        "{domain} mathématiques",
        "{domain} physique",
        "{domain} chimie",
        "{domain} biologie",
    ],
    "encyclopedique": [
        # Reprend expert +
        "{domain} académique",
        "{domain} publications",
        "{domain} littérature scientifique",
        "{domain} état de l'art",
        "{domain} frontières",
        "{domain} futur",
        "{domain} histoire complète",
        "{domain} étymologie",
        "{domain} philosophie",
        "{domain} éthique",
        "{domain} impact sociétal",
        "{domain} interdisciplinarité",
        "{domain} et intelligence artificielle",
        "{domain} et neuroscience",
        "{domain} et environnement",
        "{domain} et économie",
    ],
}

# Requêtes Wikipedia spécifiques (EN + FR)
_WIKI_QUERIES = [
    "{domain}",
    "History of {domain}",
    "histoire de {domain}",
    "Outline of {domain}",
    "List of {domain}",
    "liste de {domain}",
    "{domain} techniques",
    "{domain} technology",
    "{domain} science",
    "{domain} theory",
    "{domain} principles",
    "{domain} terminology",
    "Glossary of {domain}",
    "glossaire de {domain}",
]


def _generate_search_queries(domain: str, depth: str) -> List[str]:
    """
    Génère une liste systématique de requêtes de recherche pour un domaine.
    
    Args:
        domain: Le domaine à explorer (ex: "photographie")
        depth: Niveau de profondeur ("debutant"|"avance"|"expert"|"encyclopedique")
    
    Returns:
        Liste de 20-80 requêtes uniques.
    """
    queries = []
    domain_lower = domain.lower().strip()
    
    # Déterminer les niveaux à inclure
    depth_levels = {
        "debutant": ["debutant"],
        "avance": ["debutant", "avance"],
        "expert": ["debutant", "avance", "expert"],
        "encyclopedique": ["debutant", "avance", "expert", "encyclopedique"],
    }
    levels = depth_levels.get(depth, ["debutant", "avance", "expert", "encyclopedique"])
    
    # Requêtes par template
    for level in levels:
        for template in _QUERY_TEMPLATES.get(level, []):
            q = template.replace("{domain}", domain_lower)
            queries.append(q)
    
    # Requêtes Wikipedia
    for template in _WIKI_QUERIES:
        q = template.replace("{domain}", domain_lower)
        queries.append(q)
    
    # Requêtes avec variantes (pluriel, synonymes courants)
    variants = [
        f"comment fonctionne {domain_lower}",
        f"pourquoi {domain_lower} est important",
        f"qui a inventé {domain_lower}",
        f"meilleurs livres {domain_lower}",
        f"{domain_lower} tutorial",
        f"{domain_lower} best practices",
        f"{domain_lower} masterclass",
        f"learn {domain_lower}",
        f"{domain_lower} explained",
        f"{domain_lower} in depth",
    ]
    queries.extend(variants)
    
    # Déduplication en gardant l'ordre
    seen = set()
    unique = []
    for q in queries:
        q_clean = q.lower().strip()
        if q_clean not in seen:
            seen.add(q_clean)
            unique.append(q)
    
    # Limiter selon la profondeur
    max_queries = {
        "debutant": 20,
        "avance": 40,
        "expert": 60,
        "encyclopedique": 80,
    }
    limit = max_queries.get(depth, 80)
    
    log.info(f"Généré {len(unique)} requêtes pour '{domain}' (profondeur={depth}), "
             f"limité à {limit}")
    return unique[:limit]


# ═══════════════════════════════════════════════════════════════════════════════
# QUALITY FILTER — Pipeline de qualité en 6 étapes
# ═══════════════════════════════════════════════════════════════════════════════

class QualityFilter:
    """
    Filtre de qualité pour les triplets extraits du web.
    
    Pipeline en 6 étapes :
    1. Autorité de la source (score 1-10 par domaine URL)
    2. Validation structurelle (anti-bruit, anti-concaténation)
    3. Consensus inter-sources (combien de sources confirment chaque fait)
    4. Cohérence interne du domaine (contradictions via ψ)
    5. Filtrage sémantique (opinion vs fait vérifiable)
    6. Scoring final (gold/silver/bronze)
    
    Usage:
        qf = QualityFilter()
        result = qf.filter(triplets, sources, "photographie")
        # result.triplets : liste de (s, r, o, sec, amplitude)
        # result.stats : {'gold': 500, 'silver': 1200, 'bronze': 3000, 'rejected': 800}
    """
    
    # ── Scores d'autorité par domaine URL (plus c'est long/spécifique, plus c'est prioritaire) ──
    AUTHORITY_RULES = [
        (10, ['wikipedia.org', 'wikibooks.org', 'wikiversity.org', 'wikisource.org']),
        (9,  ['.edu', '.gov', 'arxiv.org', 'pubmed.ncbi.nlm.nih.gov', 'doi.org']),
        (8,  ['scholar.google', 'docs.python.org', 'developer.mozilla.org', 'w3.org',
               'pypi.org', 'npmjs.com', 'readthedocs.io']),
        (7,  ['.org', 'github.com', 'gitlab.com', 'stackoverflow.com', 'stackexchange.com',
               'docs.', 'documentation.', 'spec.']),
        (5,  ['medium.com', 'dev.to', 'towardsdatascience.com', 'freecodecamp.org',
               'opensource.com', 'acm.org', 'ieee.org']),
        (4,  ['blog.', 'wordpress.', 'substack.com', 'notion.', 'news.ycombinator.com']),
        (3,  ['reddit.com', 'quora.com', 'twitter.com', 'facebook.com', 'instagram.com',
               'tiktok.com', 'pinterest.com']),
        (2,  ['forum.', 'comment', 'review', 'opinion']),
        (1,  ['spam', 'adult', 'casino', 'clickbank', 'payday']),
    ]
    
    # ── Patterns sémantiques ──
    SPECULATION_KEYWORDS = [
        'pourrait', 'peut-être', 'peut etre', 'hypothèse', 'hypothese',
        'suppose', 'supposé', 'supposee', 'incertain', 'possiblement',
        'probablement', 'suggère', 'suggere', 'semble', 'paraît', 'parait',
        'might', 'maybe', 'perhaps', 'possibly', 'hypothesis',
        'speculated', 'suggested', 'could be', 'may be',
    ]
    
    OPINION_KEYWORDS = [
        'meilleur', 'pire', 'magnifique', 'horrible', 'superbe',
        'je pense', 'à mon avis', 'selon moi', 'personnellement',
        'best', 'worst', 'amazing', 'terrible', 'in my opinion',
        'i think', 'i believe', 'personally',
    ]
    
    DEFINITION_PATTERNS = [
        (re.compile(r'\best\s+(?:un|une|le|la|les|l\')\b', re.IGNORECASE), 1.5),
        (re.compile(r'\bsignifie\b', re.IGNORECASE), 1.4),
        (re.compile(r'\bdésigne\b', re.IGNORECASE), 1.3),
        (re.compile(r'\bse définit\b', re.IGNORECASE), 1.5),
        (re.compile(r'\bis an?\b', re.IGNORECASE), 1.5),
        (re.compile(r'\bmeans\b', re.IGNORECASE), 1.4),
        (re.compile(r'\brefers to\b', re.IGNORECASE), 1.3),
    ]
    
    FACT_PATTERNS = [
        (re.compile(r'\b\d{4}\b'), 1.3),  # date/année → fait vérifiable
        (re.compile(r'\b(?:a découvert|a inventé|a créé|a publié|a fondé)\b'), 1.4),
        (re.compile(r'\b(?:discovered|invented|created|published|founded)\b'), 1.4),
        (re.compile(r'\b(?:est composé de|contient|se compose de)\b'), 1.2),
    ]
    
    # Seuils de classification
    GOLD_THRESHOLD = 5.0    # ≥ 5.0 → gold (quasi-SFT)
    SILVER_THRESHOLD = 2.0  # ≥ 2.0 → silver
    BRONZE_THRESHOLD = 0.2  # ≥ 0.2 → bronze, < 0.2 → rejeté
    MIN_AUTHORITY_SCORE = 2  # Sources avec score < 2 sont ignorées
    
    def __init__(self, enable_coherence: bool = False):
        """
        Args:
            enable_coherence: Active l'étape 4 (cohérence ψ). Coûteux en O(N²).
                              Désactivé par défaut pour les KB > 10K triplets.
        """
        self.enable_coherence = enable_coherence
    
    # ── API publique ───────────────────────────────────────────────────
    
    def filter(
        self,
        triplets: List[Tuple[str, str, str, str]],
        sources: List[Dict[str, str]],
        domain: str = "",
    ) -> FilteredResult:
        """
        Pipeline complet de filtrage qualité.
        
        Args:
            triplets: Liste de (sujet, relation, objet, secteur)
            sources: Liste de dicts {url, title, content, source_type, ...}
            domain: Nom du domaine (pour le rapport)
        
        Returns:
            FilteredResult avec triplets scorés et statistiques.
        """
        t0 = time.time()
        stats = {
            'gold': 0, 'silver': 0, 'bronze': 0, 'rejected': 0,
            'rejection_reasons': {},
        }
        
        if not triplets:
            return FilteredResult(triplets=[], stats=stats, top_concepts=[])
        
        log.info(f"QualityFilter: {len(triplets)} triplets, "
                 f"{len(sources)} sources → filtrage...")
        
        # ── Étape 1 : Score d'autorité par source ──
        source_authority = self._build_source_authority_map(sources, triplets)
        log.info(f"  Étape 1 (autorité): {len(source_authority)} sources notées, "
                 f"moyenne={sum(source_authority.values())/max(len(source_authority),1):.1f}")
        
        # ── Étape 2 : Validation structurelle ──
        valid_triplets, rejected_step2 = self._validate_triples(triplets)
        stats['rejected'] += len(rejected_step2)
        for reason in rejected_step2.values():
            stats['rejection_reasons'][reason] = stats['rejection_reasons'].get(reason, 0) + 1
        log.info(f"  Étape 2 (validation): {len(valid_triplets)} valides, "
                 f"{len(rejected_step2)} rejetés")
        
        if not valid_triplets:
            return FilteredResult(triplets=[], stats=stats, top_concepts=[])
        
        # ── Étape 3 : Consensus inter-sources ──
        consensus_scores = self._compute_consensus(valid_triplets, sources)
        log.info(f"  Étape 3 (consensus): {len(consensus_scores)} faits scorés, "
                 f"moyenne={sum(consensus_scores.values())/len(consensus_scores):.2f}")
        
        # ── Étape 4 : Cohérence interne (optionnel, coûteux) ──
        coherence_rejected = set()
        if self.enable_coherence and len(valid_triplets) <= 10000:
            coherence_rejected = self._check_domain_coherence(valid_triplets)
            log.info(f"  Étape 4 (cohérence): {len(coherence_rejected)} contradictions")
        elif self.enable_coherence:
            log.info(f"  Étape 4 (cohérence): ignorée (trop de triplets: {len(valid_triplets)})")
        
        # ── Étape 5 : Filtrage sémantique ──
        semantic_scores = self._semantic_filter(valid_triplets)
        spec_count = sum(1 for v in semantic_scores.values() if v < 0.5)
        def_count = sum(1 for v in semantic_scores.values() if v > 1.2)
        log.info(f"  Étape 5 (sémantique): {spec_count} opinions/spéculations, "
                 f"{def_count} définitions")
        
        # ── Étape 6 : Scoring final ──
        scored_triplets = []
        for i, (s, r, o, sec) in enumerate(valid_triplets):
            if i in coherence_rejected:
                stats['rejected'] += 1
                stats['rejection_reasons']['cohérence contradictoire'] = \
                    stats['rejection_reasons'].get('cohérence contradictoire', 0) + 1
                continue
            
            key = (s, r, o)
            auth_score = source_authority.get(key, 5.0)
            consensus = consensus_scores.get(key, 0.0)
            semantic = semantic_scores.get(key, 1.0)
            
            # Formule de scoring pondéré
            amplitude = (
                auth_score * 0.3 +
                consensus * 0.4 +
                semantic * 0.3
            )
            amplitude = max(0.0, min(10.0, amplitude))
            
            # Classification
            if amplitude >= self.GOLD_THRESHOLD:
                stats['gold'] += 1
                amplitude = max(amplitude, 5.0)  # gold = minimum SFT-level
            elif amplitude >= self.SILVER_THRESHOLD:
                stats['silver'] += 1
            elif amplitude >= self.BRONZE_THRESHOLD:
                stats['bronze'] += 1
            else:
                stats['rejected'] += 1
                stats['rejection_reasons']['score insuffisant'] = \
                    stats['rejection_reasons'].get('score insuffisant', 0) + 1
                continue
            
            scored_triplets.append((s, r, o, sec, round(amplitude, 2)))
        
        # Concepts dominants
        top_concepts = self._extract_top_concepts(scored_triplets)
        
        elapsed = time.time() - t0
        log.info(f"  ✅ QualityFilter terminé en {elapsed:.1f}s: "
                 f"G={stats['gold']} S={stats['silver']} B={stats['bronze']} "
                 f"R={stats['rejected']} "
                 f"({stats['gold']+stats['silver']+stats['bronze']}/{len(triplets)} acceptés)")
        
        return FilteredResult(
            triplets=scored_triplets,
            stats=stats,
            top_concepts=top_concepts,
        )
    
    # ── Étape 1 : Autorité de la source ──────────────────────────────
    
    def _score_url_authority(self, url: str) -> float:
        """
        Score d'autorité pour une URL. 1-10.
        
        Args:
            url: URL à évaluer
        
        Returns:
            Score entre 1.0 et 10.0
        """
        if not url:
            return 3.0  # Score neutre pour les URLs inconnues
        
        url_lower = url.lower()
        
        # Données entreprise = haute autorité (propriétaires, vérifiées)
        if url_lower.startswith('enterprise://'):
            return 8.0
        
        for score, domains in self.AUTHORITY_RULES:
            for domain in domains:
                if domain in url_lower:
                    return float(score)
        
        return 3.0  # Source inconnue = score neutre
    
    def _build_source_authority_map(
        self,
        sources: List[Dict[str, str]],
        triplets: List[Tuple],
    ) -> Dict[Tuple, float]:
        """
        Construit un mapping (s, r, o) → score d'autorité de la meilleure source.
        """
        # Indexer les URLs par source pour retrouver l'autorité
        # Simplification : associer chaque triplet à l'autorité moyenne des sources
        # En pratique, on a besoin de savoir de quelle source vient chaque triplet.
        # Comme on n'a pas ce mapping direct, on utilise l'autorité moyenne.
        if not sources:
            return {}
        
        # Calculer l'autorité moyenne par source_type
        authority_by_type = {}
        for source in sources:
            url = source.get('url', '')
            source_type = source.get('source_type', 'web')
            auth = self._score_url_authority(url)
            if source_type not in authority_by_type:
                authority_by_type[source_type] = []
            authority_by_type[source_type].append(auth)
        
        # Moyenne par type
        avg_authority = {}
        for stype, scores in authority_by_type.items():
            avg_authority[stype] = sum(scores) / len(scores) if scores else 3.0
        
        # Appliquer aux triplets (simplification : tous les triplets d'une source
        # héritent de l'autorité moyenne de leur type de source)
        result = {}
        for s, r, o, _sec in triplets:
            key = (s, r, o)
            # Estimer : moyenne de toutes les sources
            result[key] = sum(avg_authority.values()) / max(len(avg_authority), 1)
        
        return result
    
    # ── Étape 2 : Validation structurelle ────────────────────────────
    
    def _validate_triples(
        self,
        triplets: List[Tuple[str, str, str, str]],
    ) -> Tuple[List[Tuple], Dict[int, str]]:
        """
        Valide les triplets (anti-bruit, anti-concaténation, etc.).
        
        Returns:
            (triplets_valides, {index: raison_rejet})
        """
        valid = []
        rejected = {}
        
        for i, (s, r, o, sec) in enumerate(triplets):
            s_clean = s.strip()
            r_clean = r.strip()
            o_clean = o.strip()
            
            # 1. Longueurs
            if len(s_clean) < 2:
                rejected[i] = "sujet trop court"
                continue
            if len(o_clean) < 2:
                rejected[i] = "objet trop court"
                continue
            if len(r_clean) < 1 or len(r_clean) > 200:
                rejected[i] = "relation invalide"
                continue
            
            # 2. Anti-concaténation
            concat_patterns = [' puis ', ' -> ', ' >> ', ' et ', ' puis', '->', '>>']
            has_concat = False
            for pat in concat_patterns:
                if pat in r_clean or pat in o_clean:
                    has_concat = True
                    break
            if has_concat:
                rejected[i] = "concaténation"
                continue
            
            # 3. Anti-bruit (symboles, nombres purs)
            if re.match(r'^[\$€£\d\s]+$', s_clean):
                rejected[i] = "bruit (symbole/nombre)"
                continue
            
            # 4. Boucle triviale
            if s_clean.lower() == o_clean.lower():
                rejected[i] = "boucle sujet=objet"
                continue
            
            # 5. Doublon (dans la liste)
            key = (s_clean.lower(), r_clean.lower(), o_clean.lower())
            if any((t[0].lower(), t[1].lower(), t[2].lower()) == key for t in valid):
                rejected[i] = "doublon"
                continue
            
            valid.append((s_clean, r_clean, o_clean, sec))
        
        return valid, rejected
    
    # ── Étape 3 : Consensus inter-sources ─────────────────────────────
    
    def _compute_consensus(
        self,
        triplets: List[Tuple[str, str, str, str]],
        sources: List[Dict[str, str]],
    ) -> Dict[Tuple, float]:
        """
        Calcule un score de consensus : combien de sources indépendantes
        confirment chaque fait normalisé.
        
        Retourne un score 0-10 où :
        - 10 : confirmé par 5+ sources
        - 7  : confirmé par 3-4 sources
        - 5  : confirmé par 2 sources
        - 2  : confirmé par 1 source
        """
        # Comme on n'a pas le mapping exact triplet→source (les triplets sont
        # extraits sans métadonnée de source), on utilise une heuristique :
        # les triplets similaires (même sujet+relation) sont probablement liés.
        # On compte les occurrences de chaque (sujet, relation) normalisé.
        
        subject_rel_counts = Counter()
        for s, r, o, _sec in triplets:
            key = (s.lower().strip(), r.lower().strip())
            subject_rel_counts[key] += 1
        
        # Normaliser en score 0-10
        result = {}
        max_count = max(subject_rel_counts.values()) if subject_rel_counts else 1
        
        for s, r, o, _sec in triplets:
            key = (s, r, o)
            count = subject_rel_counts.get((s.lower().strip(), r.lower().strip()), 1)
            
            # Transformation logarithmique : 1→2, 2→5, 3-4→7, 5+→10
            if count >= 5:
                score = 10.0
            elif count >= 3:
                score = 7.0
            elif count >= 2:
                score = 5.0
            else:
                score = 2.0
            
            result[key] = score
        
        return result
    
    # ── Étape 4 : Cohérence interne ──────────────────────────────────
    
    def _check_domain_coherence(
        self,
        triplets: List[Tuple[str, str, str, str]],
        max_batch: int = 500,
    ) -> Set[int]:
        """
        Détecte les contradictions dans le domaine via similarité lexicale
        (pas de ψ ici — on n'a pas d'encoder dans le QualityFilter).
        
        Utilise les paires de relations opposées (est/n'est pas, etc.)
        pour détecter les contradictions.
        
        Returns:
            Set d'indices des triplets à rejeter.
        """
        opposite_relations = [
            ('est', "n'est pas"),
            ('augmente', 'diminue'),
            ('cause', 'empêche'),
            ('crée', 'détruit'),
            ('favorise', 'inhibe'),
            ('active', 'désactive'),
            ('ouvre', 'ferme'),
            ('produit', 'consomme'),
        ]
        
        rejected = set()
        n = len(triplets)
        
        # Traiter par lots pour éviter O(N²) sur de très grandes listes
        batch_size = min(max_batch, n)
        
        for batch_start in range(0, n, batch_size):
            batch_end = min(batch_start + batch_size, n)
            batch = triplets[batch_start:batch_end]
            
            for i, (s1, r1, o1, _sec1) in enumerate(batch):
                idx1 = batch_start + i
                if idx1 in rejected:
                    continue
                
                for j, (s2, r2, o2, _sec2) in enumerate(batch):
                    idx2 = batch_start + j
                    if idx2 <= idx1 or idx2 in rejected:
                        continue
                    
                    # Même sujet ?
                    if s1.lower().strip() != s2.lower().strip():
                        continue
                    
                    # Relations opposées ?
                    r1_lower = r1.lower().strip()
                    r2_lower = r2.lower().strip()
                    
                    is_opposite = False
                    for pos, neg in opposite_relations:
                        if (pos in r1_lower and neg in r2_lower) or \
                           (neg in r1_lower and pos in r2_lower):
                            is_opposite = True
                            break
                    
                    if not is_opposite:
                        continue
                    
                    # Objets similaires ? (chevauchement lexical)
                    o1_words = set(o1.lower().split())
                    o2_words = set(o2.lower().split())
                    overlap = len(o1_words & o2_words)
                    
                    if overlap > 0:
                        # Contradiction ! Garder le fait le plus fréquent
                        # (pour l'instant : rejeter le second)
                        rejected.add(idx2)
        
        return rejected
    
    # ── Étape 5 : Filtrage sémantique ─────────────────────────────────
    
    def _semantic_filter(
        self,
        triplets: List[Tuple[str, str, str, str]],
    ) -> Dict[Tuple, float]:
        """
        Bonus/malus sémantique selon le type de contenu.
        
        - Définition → ×1.3-1.5
        - Fait historique/vérifiable → ×1.2-1.4
        - Spéculation → ×0.3
        - Opinion → ×0.2
        - Neutre → ×1.0
        
        Returns:
            Dictionnaire (s, r, o) → multiplicateur
        """
        result = {}
        
        for s, r, o, _sec in triplets:
            key = (s, r, o)
            text = f"{r} {o}".lower()
            
            multiplier = 1.0
            
            # Vérifier spéculation
            for kw in self.SPECULATION_KEYWORDS:
                if kw in text:
                    multiplier = min(multiplier, 0.3)
                    break
            
            # Vérifier opinion
            if multiplier == 1.0:
                for kw in self.OPINION_KEYWORDS:
                    if kw in text:
                        multiplier = min(multiplier, 0.2)
                        break
            
            # Vérifier définition (si pas déjà pénalisé)
            if multiplier == 1.0:
                for pattern, boost in self.DEFINITION_PATTERNS:
                    if pattern.search(r):
                        multiplier = max(multiplier, boost)
                        break
            
            # Vérifier fait vérifiable
            if multiplier == 1.0:
                for pattern, boost in self.FACT_PATTERNS:
                    if pattern.search(text):
                        multiplier = max(multiplier, boost)
            
            result[key] = multiplier
        
        return result
    
    # ── Concepts dominants ────────────────────────────────────────────
    
    def _extract_top_concepts(
        self,
        scored_triplets: List[Tuple],
    ) -> List[str]:
        """Extrait les concepts les plus fréquents des triplets scorés."""
        # Pondérer par l'amplitude
        subjects = Counter()
        objects = Counter()
        
        for s, r, o, sec, amp in scored_triplets:
            subjects[s] += amp
            objects[o] += amp * 0.7
        
        combined = Counter()
        for word, weight in subjects.most_common(100):
            combined[word] += weight
        for word, weight in objects.most_common(100):
            combined[word] += weight
        
        stop_words = {"est", "sont", "pas", "plus", "très", "tout", "avec", "dans",
                      "pour", "sur", "the", "and", "for", "with", "that", "this"}
        concepts = [w for w, _ in combined.most_common(30)
                    if len(w) > 3 and w not in stop_words]
        
        return concepts[:15]


# ═══════════════════════════════════════════════════════════════════════════════
# DOMAIN SPECIALIZER
# ═══════════════════════════════════════════════════════════════════════════════

class DomainSpecializer:
    """
    Orchestrateur de spécialisation dynamique.
    
    Explore le web, extrait des connaissances, construit une base holographique
    personnelle pour un domaine donné.
    
    Attributes:
        brain: Le HarmonicBrain principal (pour l'encodage)
        web_retriever: Instance de WebRetriever pour les recherches
        _active_jobs: Dictionnaire des tâches en cours {job_id: SpecializationJob}
        _lock: Verrou pour la thread-safety des jobs
    """
    
    # Politeness delay between API calls (seconds)
    _API_DELAY = 1.0
    
    # Minimum content length to consider a source useful
    _MIN_CONTENT_LENGTH = 200
    
    # Maximum content length to process (avoid huge pages)
    _MAX_CONTENT_LENGTH = 50000
    
    def __init__(self, brain=None, web_retriever=None):
        """
        Args:
            brain: Instance HarmonicBrain (pour from_npz et encodage)
            web_retriever: Instance WebRetriever (optionnel, sera importé sinon)
        """
        _ensure_imports()
        
        self.brain = brain
        self._web = web_retriever
        self._active_jobs: Dict[str, SpecializationJob] = {}
        self._lock = threading.Lock()
        
        # Initialiser le WebRetriever si pas fourni
        if self._web is None:
            try:
                from web_retriever import WebRetriever
                self._web = WebRetriever()
            except ImportError:
                log.warning("WebRetriever non disponible — recherche web désactivée")
                self._web = None
    
    # ── API publique ───────────────────────────────────────────────────────
    
    def specialize(
        self,
        domain: str,
        depth: str = "expert",
        user_id: str = "anonymous",
        on_progress: Optional[Callable[[SpecializationJob], None]] = None,
        async_mode: bool = False,
    ) -> SpecializationResult:
        """
        Lance une spécialisation sur un domaine.
        
        Args:
            domain: Le domaine à explorer (ex: "photographie", "astrophysique")
            depth: "debutant" | "avance" | "expert" | "encyclopedique"
            user_id: Identifiant utilisateur
            on_progress: Callback optionnel pour suivre la progression
            async_mode: Si True, lance en arrière-plan et retourne un job_id
        
        Returns:
            SpecializationResult si async_mode=False, sinon dict avec job_id
        """
        # Validation
        domain = domain.strip().lower()
        if not domain or len(domain) < 2:
            return SpecializationResult(
                domain=domain, depth=depth, triplets_count=0, sources_count=0,
                kb_path="", elapsed_seconds=0, success=False,
                error="Domaine invalide (trop court)",
            )
        
        valid_depths = {"debutant", "avance", "expert", "encyclopedique"}
        if depth not in valid_depths:
            depth = "expert"
        
        # Mode asynchrone
        if async_mode:
            job = SpecializationJob(
                job_id=str(uuid.uuid4())[:8],
                user_id=user_id,
                domain=domain,
                depth=depth,
                status="pending",
                started_at=datetime.now().isoformat(),
            )
            with self._lock:
                self._active_jobs[job.job_id] = job
            
            thread = threading.Thread(
                target=self._run_specialize,
                args=(job, on_progress),
                daemon=True,
            )
            thread.start()
            
            # Retourner une "promesse" — le caller interrogera /api/specialize/status
            return SpecializationResult(
                domain=domain, depth=depth, triplets_count=0, sources_count=0,
                kb_path="", elapsed_seconds=0,
                message=f"Spécialisation lancée en arrière-plan. job_id={job.job_id}",
                success=True,
            )
        
        # Mode synchrone
        job = SpecializationJob(
            job_id=str(uuid.uuid4())[:8],
            user_id=user_id,
            domain=domain,
            depth=depth,
            status="pending",
            started_at=datetime.now().isoformat(),
        )
        return self._run_specialize(job, on_progress)
    
    def get_job(self, job_id: str) -> Optional[SpecializationJob]:
        """Récupère l'état d'une tâche de spécialisation."""
        with self._lock:
            return self._active_jobs.get(job_id)
    
    def get_user_jobs(self, user_id: str) -> List[SpecializationJob]:
        """Récupère toutes les tâches d'un utilisateur."""
        with self._lock:
            return [j for j in self._active_jobs.values() if j.user_id == user_id]
    
    def get_user_domains(self, user_id: str) -> Dict[str, Dict]:
        """Récupère les domaines spécialisés d'un utilisateur depuis son profil."""
        profile_path = _USERS_DIR / user_id / "profile.json"
        if profile_path.exists():
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data.get("specialized_domains", {})
            except Exception:
                pass
        return {}
    
    # ── Pipeline interne ───────────────────────────────────────────────────
    
    def _run_specialize(
        self,
        job: SpecializationJob,
        on_progress: Optional[Callable] = None,
    ) -> SpecializationResult:
        """Exécute le pipeline complet de spécialisation."""
        t0 = time.time()
        
        def _update(progress: float, status: str, **kwargs):
            """Met à jour le job et appelle le callback."""
            job.progress = progress
            job.status = status
            for k, v in kwargs.items():
                if hasattr(job, k):
                    setattr(job, k, v)
            if on_progress:
                try:
                    on_progress(job)
                except Exception:
                    pass
        
        try:
            # ── Étape 1 : Génération de requêtes ──────────────────────────
            _update(0.02, "searching", queries_done=0)
            queries = _generate_search_queries(job.domain, job.depth)
            job.queries_total = len(queries)
            log.info(f"[{job.job_id}] Étape 1 : {len(queries)} requêtes générées "
                     f"pour '{job.domain}'")
            
            # ── Étape 2 : Exploration web multi-niveaux ───────────────────
            _update(0.05, "searching")
            sources = self._deep_search(queries, job, _update)
            job.sources_consulted = len(sources)
            log.info(f"[{job.job_id}] Étape 2 : {len(sources)} sources uniques collectées")
            
            if not sources:
                return self._fail(job, "Aucune source trouvée pour ce domaine", t0)
            
            # ── Étape 3 : Extraction de triplets ──────────────────────────
            _update(0.50, "extracting", triplets_extracted=0)
            all_triplets = self._extract_knowledge(sources, job, _update)
            job.triplets_extracted = len(all_triplets)
            log.info(f"[{job.job_id}] Étape 3 : {len(all_triplets)} triplets extraits")
            
            if len(all_triplets) < 10:
                return self._fail(job, f"Seulement {len(all_triplets)} triplets extraits — "
                                        f"domaine peut-être trop spécifique", t0)
            
            # ── Étape 4 : Construction KB personnelle ─────────────────────
            _update(0.85, "encoding")
            kb_path = self._build_user_kb(job, all_triplets, sources)
            log.info(f"[{job.job_id}] Étape 4 : KB sauvegardée → {kb_path}")
            
            # ── Étape 5 : Rapport ─────────────────────────────────────────
            _update(0.95, "done")
            elapsed = time.time() - t0
            top_concepts = self._extract_top_concepts(all_triplets)
            
            message = self._format_report(job, len(sources), len(all_triplets), 
                                          elapsed, top_concepts)
            
            result = SpecializationResult(
                domain=job.domain,
                depth=job.depth,
                triplets_count=len(all_triplets),
                sources_count=len(sources),
                kb_path=str(kb_path),
                elapsed_seconds=elapsed,
                top_concepts=top_concepts,
                message=message,
                success=True,
            )
            job.result = result
            _update(1.0, "done")
            
            # Charger la KB dans le brain si disponible
            if self.brain is not None:
                try:
                    self.brain.load_user_kb(job.user_id, str(kb_path))
                    log.info(f"[{job.job_id}] KB chargée dans le brain pour user={job.user_id}")
                except Exception as e:
                    log.warning(f"[{job.job_id}] Impossible de charger la KB dans le brain: {e}")
            
            return result
            
        except Exception as e:
            log.exception(f"[{job.job_id}] Erreur pendant la spécialisation: {e}")
            return self._fail(job, str(e), t0)
    
    def _fail(self, job: SpecializationJob, error: str, t0: float) -> SpecializationResult:
        """Crée un résultat d'échec."""
        elapsed = time.time() - t0
        job.status = "error"
        job.error = error
        return SpecializationResult(
            domain=job.domain,
            depth=job.depth,
            triplets_count=job.triplets_extracted,
            sources_count=job.sources_consulted,
            kb_path="",
            elapsed_seconds=elapsed,
            success=False,
            error=error,
            message=f"❌ Échec : {error}",
        )
    
    # ── Exploration web ───────────────────────────────────────────────────
    
    def _deep_search(
        self,
        queries: List[str],
        job: SpecializationJob,
        update_fn: Callable,
    ) -> List[Dict[str, str]]:
        """
        Exploration multi-niveaux :
        Niveau 1 : Wikipedia (via search_wikipedia_multiple + contenu complet)
        Niveau 2 : Pages liées Wikipedia
        Niveau 3 : Web large (DuckDuckGo + Tavily/Brave)
        
        Returns:
            Liste de dicts {title, url, content, source_type}
        """
        all_sources: Dict[str, Dict] = {}  # url → source dict
        
        if self._web is None:
            log.warning("WebRetriever non disponible — recherche web impossible")
            return []
        
        total_queries = len(queries)
        
        # ── Niveau 1 & 3 : Wikipedia + Web pour chaque requête ────────────
        for i, query in enumerate(queries):
            # Mise à jour de la progression (5% → 45%)
            progress = 0.05 + (0.40 * (i / max(total_queries, 1)))
            update_fn(progress, "searching", queries_done=i + 1)
            
            # Petite pause pour être poli avec les APIs
            if i > 0:
                time.sleep(self._API_DELAY)
            
            try:
                # Wikipedia (jusqu'à 3 résultats par requête)
                wiki_results = self._web.search_wikipedia_multiple(query, lang="auto", limit=3)
                for wr in wiki_results:
                    url = wr.get("url", "")
                    if url and url not in all_sources:
                        # Récupérer le contenu complet
                        title = wr.get("title", "")
                        lang = wr.get("language", "fr")
                        full_content = self._fetch_wikipedia_full(title, lang)
                        if full_content and len(full_content) >= self._MIN_CONTENT_LENGTH:
                            all_sources[url] = {
                                "title": title,
                                "url": url,
                                "content": full_content[:self._MAX_CONTENT_LENGTH],
                                "source_type": "wikipedia",
                                "language": lang,
                            }
                
                # Web large (1-2 résultats par requête)
                web_results = self._web.search_web(query, max_results=2, 
                                                   include_wikipedia=False)
                for wr in web_results:
                    url = wr.get("url", "")
                    if url and url not in all_sources:
                        snippet = wr.get("summary") or wr.get("snippet") or ""
                        if len(snippet) >= self._MIN_CONTENT_LENGTH // 2:
                            all_sources[url] = {
                                "title": wr.get("title", ""),
                                "url": url,
                                "content": snippet[:self._MAX_CONTENT_LENGTH],
                                "source_type": wr.get("source", "web"),
                                "language": "auto",
                            }
                
            except Exception as e:
                log.debug(f"Erreur sur la requête '{query}': {e}")
                continue
            
            # Limiter le nombre total de sources pour éviter l'emballement
            max_sources = {
                "debutant": 30,
                "avance": 60,
                "expert": 100,
                "encyclopedique": 150,
            }
            if len(all_sources) >= max_sources.get(job.depth, 100):
                log.info(f"Limite de {max_sources.get(job.depth, 100)} sources atteinte")
                break
        
        # ── Niveau 2 : Pages liées Wikipedia (top 10 articles) ─────────────
        wiki_sources = [s for s in all_sources.values() if s["source_type"] == "wikipedia"]
        wiki_sources_sorted = sorted(wiki_sources, key=lambda s: len(s["content"]), reverse=True)
        
        for ws in wiki_sources_sorted[:10]:
            try:
                linked_titles = self._fetch_wikipedia_links(ws["title"], ws.get("language", "fr"))
                for linked_title in linked_titles[:5]:  # Max 5 liens par article
                    # Construire l'URL
                    lang = ws.get("language", "fr")
                    linked_url = (f"https://{lang}.wikipedia.org/wiki/"
                                  f"{linked_title.replace(' ', '_')}")
                    if linked_url not in all_sources:
                        content = self._fetch_wikipedia_full(linked_title, lang)
                        if content and len(content) >= self._MIN_CONTENT_LENGTH:
                            all_sources[linked_url] = {
                                "title": linked_title,
                                "url": linked_url,
                                "content": content[:self._MAX_CONTENT_LENGTH],
                                "source_type": "wikipedia_linked",
                                "language": lang,
                            }
                time.sleep(0.5)  # Poli
            except Exception:
                continue
        
        log.info(f"_deep_search terminé : {len(all_sources)} sources "
                 f"(wiki={sum(1 for s in all_sources.values() if 'wikipedia' in s['source_type'])}, "
                 f"web={sum(1 for s in all_sources.values() if s['source_type'] == 'web')})")
        
        return list(all_sources.values())
    
    def _fetch_wikipedia_full(self, title: str, lang: str = "fr") -> Optional[str]:
        """
        Récupère le contenu complet d'un article Wikipedia (pas juste l'intro).
        """
        if self._web is None:
            return None
        
        try:
            from urllib.parse import quote_plus
            import urllib.request
            import urllib.error
            
            url = (
                f"https://{lang}.wikipedia.org/w/api.php"
                f"?action=query&prop=extracts&explaintext=1"
                f"&titles={quote_plus(title)}&format=json"
            )
            
            req = urllib.request.Request(url, headers={
                "User-Agent": "HarmonicAI/2.0 (DomainSpecializer; educational)"
            })
            
            with urllib.request.urlopen(req, timeout=15) as resp:
                import json as json_mod
                data = json_mod.loads(resp.read().decode('utf-8'))
            
            if "query" in data and "pages" in data["query"]:
                pages = data["query"]["pages"]
                for page_id, page in pages.items():
                    if page_id != "-1":
                        return page.get("extract", "")
            
            return None
        except Exception as e:
            log.debug(f"Impossible de récupérer l'article Wikipedia '{title}': {e}")
            return None
    
    def _fetch_wikipedia_links(self, title: str, lang: str = "fr") -> List[str]:
        """
        Récupère les titres des articles liés ("See also" / "Voir aussi")
        d'une page Wikipedia.
        """
        if self._web is None:
            return []
        
        try:
            from urllib.parse import quote_plus
            import urllib.request
            
            url = (
                f"https://{lang}.wikipedia.org/w/api.php"
                f"?action=parse&page={quote_plus(title)}"
                f"&prop=links&format=json&pllimit=30"
            )
            
            req = urllib.request.Request(url, headers={
                "User-Agent": "HarmonicAI/2.0 (DomainSpecializer; educational)"
            })
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                import json as json_mod
                data = json_mod.loads(resp.read().decode('utf-8'))
            
            links = []
            if "parse" in data and "links" in data["parse"]:
                for link in data["parse"]["links"]:
                    title_linked = link.get("*", "")
                    # Filtrer les liens internes utiles (pas Aide:, Catégorie:, etc.)
                    if (title_linked and 
                        ":" not in title_linked and
                        title_linked != title):
                        links.append(title_linked)
            
            return links[:20]  # Max 20 liens
        except Exception as e:
            log.debug(f"Impossible de récupérer les liens de '{title}': {e}")
            return []
    
    # ── Extraction de connaissances ───────────────────────────────────────
    
    def _extract_knowledge(
        self,
        sources: List[Dict[str, str]],
        job: SpecializationJob,
        update_fn: Callable,
    ) -> List[Tuple[str, str, str, str]]:
        """
        Extrait les triplets de connaissance de toutes les sources.
        
        Utilise le LLM si disponible, sinon les patterns regex.
        
        Returns:
            Liste de (sujet, relation, objet, secteur)
        """
        all_triplets: List[Tuple[str, str, str, str]] = []
        seen_triplets: set = set()
        
        total = len(sources)
        
        for i, source in enumerate(sources):
            # Progression (50% → 80%)
            progress = 0.50 + (0.30 * (i / max(total, 1)))
            update_fn(progress, "extracting", triplets_extracted=len(all_triplets))
            
            content = source.get("content", "")
            if not content or len(content) < self._MIN_CONTENT_LENGTH:
                continue
            
            try:
                # Essayer LLM d'abord
                if _BOOTSTRAPPER_LLM is not None:
                    try:
                        triples = _BOOTSTRAPPER_LLM(content)
                    except Exception:
                        triples = _BOOTSTRAPPER_SIMPLE(content) if _BOOTSTRAPPER_SIMPLE else []
                elif _BOOTSTRAPPER_SIMPLE is not None:
                    triples = _BOOTSTRAPPER_SIMPLE(content)
                else:
                    # Fallback: extraction basique interne
                    triples = self._basic_extract(content)
                
                # Déduplication et validation
                for s, r, o, sec in triples:
                    s_clean = s.strip().lower()
                    r_clean = r.strip().lower()
                    o_clean = o.strip().lower()
                    
                    # Éviter les triplets triviaux ou vides
                    if not s_clean or not r_clean or not o_clean:
                        continue
                    if len(s_clean) < 2 or len(o_clean) < 2:
                        continue
                    if s_clean == o_clean:
                        continue
                    
                    key = (s_clean, r_clean, o_clean)
                    if key not in seen_triplets:
                        seen_triplets.add(key)
                        all_triplets.append((s_clean, r_clean, o_clean, sec))
                
            except Exception as e:
                log.debug(f"Erreur extraction source '{source.get('title', '?')}': {e}")
                continue
            
            # Limiter pour éviter l'emballement
            if len(all_triplets) >= 100000:
                log.info("Limite de 100 000 triplets atteinte")
                break
        
        log.info(f"_extract_knowledge : {len(all_triplets)} triplets uniques "
                 f"de {total} sources")
        return all_triplets
    
    def _basic_extract(self, text: str) -> List[Tuple[str, str, str, str]]:
        """
        Extraction basique par patterns regex (fallback minimal).
        """
        triples = []
        text_clean = re.sub(r'\([^)]*\)', '', text)  # Enlever parenthèses
        text_clean = re.sub(r'\[[^\]]*\]', '', text_clean)  # Enlever crochets
        
        patterns = [
            # "X est un/une Y"
            (r'([A-ZÀ-Ü][a-zà-ü]{2,30})\s+est\s+(?:un|une)\s+([a-zà-ü\s]{3,60})',
             "est un", "classification"),
            # "X a découvert/inventé/créé Y"
            (r'([A-ZÀ-Ü][a-zà-ü]{2,30})\s+a\s+(?:découvert|inventé|créé|fondé|développé)\s+'
             r'(?:le |la |les |l\')?([a-zà-ü\s]{3,60})',
             "a créé", "découverte"),
            # "X permet de Y"
            (r'([A-Za-zà-ü]{3,40})\s+permet\s+(?:de|d\')\s+([a-zà-ü\s]{3,60})',
             "permet de", "fonction"),
            # "X est composé de Y"
            (r'([A-Za-zà-ü]{3,40})\s+(?:est|sont)\s+composé(?:e?s)?\s+(?:de|d\')\s+'
             r'([a-zà-ü\s]{3,60})',
             "est composé de", "composition"),
        ]
        
        for pattern, relation, secteur in patterns:
            for match in re.finditer(pattern, text_clean, re.IGNORECASE):
                sujet = match.group(1).strip().lower()
                objet = match.group(2).strip().lower()
                if len(sujet) >= 2 and len(objet) >= 2:
                    triples.append((sujet, relation, objet, secteur))
        
        return triples
    
    # ── Construction KB ────────────────────────────────────────────────────
    
    def _build_user_kb(
        self,
        job: SpecializationJob,
        triplets: List[Tuple[str, str, str, str]],
        sources: List[Dict[str, str]] = None,
    ) -> Path:
        """
        Construit un HarmonicBrain personnel à partir des triplets, après filtrage qualité.
        
        Returns:
            Chemin du fichier NPZ.
        """
        # Créer le dossier utilisateur
        user_dir = _USERS_DIR / job.user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # 🆕 FILTRAGE QUALITÉ (6 étapes)
        qf = QualityFilter(enable_coherence=(len(triplets) <= 10000))
        filtered = qf.filter(triplets, sources or [], job.domain)
        
        # Utiliser les triplets filtrés avec leurs amplitudes
        scored_triplets = filtered.triplets
        quality_report = filtered.to_dict()
        
        log.info(f"QualityFilter: {len(triplets)} bruts → {len(scored_triplets)} filtrés "
                 f"(G={filtered.gold_count} S={filtered.silver_count} B={filtered.bronze_count} "
                 f"R={filtered.rejected_count}, "
                 f"taux={quality_report['acceptance_rate']:.0%})")
        
        # Construire le brain personnel
        # dim=128 : bon compromis expressivité/mémoire pour KB spécialisées
        if _HarmonicBrain is not None:
            # Extraire les 4 premiers champs (s, r, o, sec) pour l'ingestion
            facts_for_brain = [(s, r, o, sec) for s, r, o, sec, _amp in scored_triplets]
            user_brain = _HarmonicBrain(facts_for_brain, dim=128, use_holographic=True)
            
            # Appliquer les amplitudes calculées par le QualityFilter
            for (s, r, o, sec, amp), record in zip(
                scored_triplets,
                [user_brain.unconscious.registry.get(
                    (s.lower().strip(), r.lower().strip(), o.lower().strip())
                ) for s, r, o, sec, amp in scored_triplets]
            ):
                if record is not None and amp > record.amplitude:
                    record.amplitude = amp
                    # Les facts gold (amp >= 5) sont quasi-SFT
                    if amp >= 5.0:
                        record.confidence = min(1.0, record.confidence + 0.3)
        else:
            raise RuntimeError("HarmonicBrain non disponible")
        
        # Sauvegarder en NPZ
        kb_filename = f"kb_{job.domain}_{job.depth}.npz"
        kb_path = user_dir / kb_filename
        
        # Format NPZ : array 'facts' de tuples (s, r, o, sec)
        facts_array = np.array(facts_for_brain, dtype=object)
        np.savez(str(kb_path), facts=facts_array)
        
        # Sauvegarder aussi le rapport de qualité
        quality_path = user_dir / f"quality_{job.domain}_{job.depth}.json"
        with open(quality_path, 'w', encoding='utf-8') as f:
            json.dump(quality_report, f, indent=2, ensure_ascii=False)
        
        # Vérifier la taille
        size_mb = kb_path.stat().st_size / (1024 * 1024)
        log.info(f"KB sauvegardée : {kb_path} ({size_mb:.1f} MB, "
                 f"{len(scored_triplets)} triplets filtrés)")
        
        # Mettre à jour le profil utilisateur (avec stats de qualité)
        self._update_user_profile(job, kb_path, len(scored_triplets), size_mb,
                                  quality_report)
        
        return kb_path
    
    def _update_user_profile(
        self,
        job: SpecializationJob,
        kb_path: Path,
        triplets_count: int,
        size_mb: float,
        quality_report: Dict = None,
    ):
        """Met à jour le profil utilisateur avec le nouveau domaine spécialisé."""
        profile_path = _USERS_DIR / job.user_id / "profile.json"
        
        # Charger ou créer le profil
        profile_data = {}
        if profile_path.exists():
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
            except Exception:
                profile_data = {}
        
        if "specialized_domains" not in profile_data:
            profile_data["specialized_domains"] = {}
        
        domain_entry = {
            "depth": job.depth,
            "kb_path": str(kb_path),
            "triplets": triplets_count,
            "size_mb": round(size_mb, 1),
            "specialized_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
        }
        
        # Ajouter les stats de qualité si disponibles
        if quality_report:
            domain_entry["quality"] = {
                "gold": quality_report.get("gold", 0),
                "silver": quality_report.get("silver", 0),
                "bronze": quality_report.get("bronze", 0),
                "rejected": quality_report.get("rejected", 0),
                "acceptance_rate": quality_report.get("acceptance_rate", 0),
            }
        
        profile_data["specialized_domains"][job.domain] = domain_entry
        
        # Ajouter user_id et updated_at
        profile_data["user_id"] = job.user_id
        profile_data["updated_at"] = datetime.now().isoformat()
        
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
        
        log.info(f"Profil utilisateur mis à jour : {profile_path}")
    
    # ── Rapport ────────────────────────────────────────────────────────────
    
    def _extract_top_concepts(self, triplets: List[Tuple]) -> List[str]:
        """Extrait les concepts les plus fréquents des triplets."""
        subjects = Counter(s for s, r, o, sec in triplets)
        objects = Counter(o for s, r, o, sec in triplets)
        
        # Combiner et classer
        combined = Counter()
        for word, count in subjects.most_common(100):
            combined[word] += count
        for word, count in objects.most_common(100):
            combined[word] += count * 0.7  # Les objets sont moins centraux
        
        # Filtrer les mots trop courts ou trop communs
        stop_words = {"est", "sont", "pas", "plus", "très", "tout", "avec", "dans",
                      "pour", "sur", "the", "and", "for", "with", "that", "this"}
        concepts = [w for w, _ in combined.most_common(30) 
                    if len(w) > 3 and w not in stop_words]
        
        return concepts[:15]
    
    def _format_report(
        self,
        job: SpecializationJob,
        sources_count: int,
        triplets_count: int,
        elapsed: float,
        top_concepts: List[str],
    ) -> str:
        """Formate un rapport humain de la spécialisation."""
        depth_labels = {
            "debutant": "Débutant",
            "avance": "Avancé",
            "expert": "Expert",
            "encyclopedique": "Encyclopédique",
        }
        depth_label = depth_labels.get(job.depth, job.depth)
        
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        
        concepts_str = ", ".join(top_concepts[:10])
        
        report = (
            f"✅ **Spécialisation terminée : {job.domain.title()}** ({depth_label})\n\n"
            f"📚 Sources consultées : {sources_count}\n"
            f"🧬 Triplets extraits : {triplets_count:,}\n"
            f"⏱️ Temps : {minutes}min {seconds}s\n\n"
            f"🔑 Concepts clés : {concepts_str}\n\n"
            f"💾 Base sauvegardée : `data/users/{job.user_id}/kb_{job.domain}_{job.depth}.npz`\n\n"
            f"_Je maîtrise maintenant **{job.domain}** au niveau {depth_label.lower()}._ "
            f"_Posez-moi vos questions !_"
        )
        
        return report


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def load_user_kbs_for_brain(brain, user_id: str) -> int:
    """
    Charge toutes les KB spécialisées d'un utilisateur dans le brain.
    
    Args:
        brain: Instance HarmonicBrain
        user_id: Identifiant utilisateur
    
    Returns:
        Nombre de KB chargées.
    """
    _ensure_imports()
    
    user_dir = _USERS_DIR / user_id
    if not user_dir.exists():
        return 0
    
    profile_path = user_dir / "profile.json"
    if not profile_path.exists():
        return 0
    
    try:
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
    except Exception:
        return 0
    
    domains = profile_data.get("specialized_domains", {})
    loaded = 0
    
    for domain, info in domains.items():
        kb_path_str = info.get("kb_path", "")
        kb_path = Path(kb_path_str) if kb_path_str else None
        
        if kb_path and kb_path.exists():
            try:
                brain.load_user_kb(user_id, str(kb_path))
                loaded += 1
                log.info(f"KB chargée pour user={user_id}, domaine={domain}: "
                         f"{info.get('triplets', '?')} triplets")
            except Exception as e:
                log.warning(f"Échec chargement KB {kb_path}: {e}")
        else:
            # Essayer le chemin standard
            kb_filename = f"kb_{domain}_{info.get('depth', 'expert')}.npz"
            standard_path = user_dir / kb_filename
            if standard_path.exists():
                try:
                    brain.load_user_kb(user_id, str(standard_path))
                    loaded += 1
                except Exception as e:
                    log.warning(f"Échec chargement KB standard {standard_path}: {e}")
    
    return loaded


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE DÉTECTION CONVERSATIONNELLE
# ═══════════════════════════════════════════════════════════════════════════════

SPECIALIZE_TRIGGERS = sorted([
    "spécialise-toi", "specialise toi", "spécialise toi",
    "deviens expert", "deviens experte", "deviens spécialiste",
    "apprends", "forme-toi", "documente-toi",
    "je veux que tu maîtrises", "je veux que tu connaisses",
    "peux-tu apprendre", "peux-tu te spécialiser",
    "spécialises", "specialises",  # formes conjuguées
    "connais-tu bien", "es-tu calé en", "es-tu spécialisé",
    "tu t'y connais en", "tu maîtrises",
    "specialize in", "become an expert in",
    "learn about", "study", "master",
], key=lambda t: -len(t))  # Plus long d'abord → évite "apprends" avant "peux-tu apprendre"

DEPTH_KEYWORDS = {
    "debutant": ["débutant", "debutant", "débutante", "debutante", 
                 "base", "bases", "simple", "introduction", "découverte",
                 "beginner", "basic", "intro"],
    "avance": ["avancé", "avance", "avancée", "intermédiaire", "intermediaire",
               "moyen", "confirmed", "intermediate", "advanced"],
    "expert": ["expert", "experte", "pointu", "poussé", "pousse", "professionnel",
               "pro", "master", "professional"],
    "encyclopedique": ["encyclopédique", "encyclopedique", "encyclopédie", "encyclopedie",
                       "complet", "complète", "total", "exhaustif", "encyclopedic",
                       "comprehensive", "exhaustive", "tout"],
}


def detect_specialize_intent(message: str) -> Optional[Dict[str, str]]:
    """
    Détecte si un message utilisateur est une demande de spécialisation.
    
    Args:
        message: Le message utilisateur
    
    Returns:
        {"domain": "...", "depth": "..."} ou None si pas d'intention détectée.
    """
    msg_lower = message.lower().strip()
    # Normaliser les traits d'union et apostrophes pour le matching
    # "spécialise-toi" == "spécialise toi", "l'intelligence" == "l intelligence"
    msg_lower = msg_lower.replace('-', ' ').replace("'", " ")
    
    # Normaliser aussi les triggers de la même façon (un seul coup au chargement)
    _norm_triggers = getattr(detect_specialize_intent, '_norm_triggers', None)
    if _norm_triggers is None:
        _norm_triggers = [t.replace('-', ' ').replace("'", " ") for t in SPECIALIZE_TRIGGERS]
        detect_specialize_intent._norm_triggers = _norm_triggers
    
    # Vérifier si un trigger est présent
    trigger_found = None
    for trigger in _norm_triggers:
        if trigger in msg_lower:
            trigger_found = trigger
            break
    
    if not trigger_found:
        return None
    
    # Extraire la profondeur (avec word boundaries pour éviter "experte" → "expert")
    depth = "expert"  # défaut
    for d, keywords in DEPTH_KEYWORDS.items():
        for kw in keywords:
            # Utiliser word boundary pour éviter les sous-chaînes partielles
            if re.search(r'\b' + re.escape(kw) + r'\b', msg_lower):
                depth = d
                break
    
    # Extraire le domaine (tout ce qui est après le trigger, moins la profondeur)
    # Stratégie : prendre le texte après le trigger, enlever les mots de profondeur
    trigger_pos = msg_lower.find(trigger_found) + len(trigger_found)
    after_trigger = msg_lower[trigger_pos:].strip()
    
    # Nettoyer : enlever "en", "sur", "dans", "le", "la", "les", "l'", "au", "à"
    domain_text = after_trigger
    for prefix in ["en ", "sur ", "dans ", "le ", "la ", "les ", "au ", "à ",
                   "in ", "on ", "about ", "the "]:
        if domain_text.lower().startswith(prefix.lower()):
            domain_text = domain_text[len(prefix):].strip()
    # Cas spécial: l' (avec ou sans espace avant)
    if domain_text.lower().startswith("l'"):
        domain_text = domain_text[2:].strip()
    
    # Enlever les indicateurs de niveau
    for kw_list in DEPTH_KEYWORDS.values():
        for kw in kw_list:
            domain_text = re.sub(r'\b' + re.escape(kw) + r'\b', '', domain_text, 
                                flags=re.IGNORECASE)
    
    # Nettoyer la ponctuation et les espaces
    domain_text = re.sub(r'[,.!?;:]', '', domain_text).strip()
    domain_text = re.sub(r'\s+', ' ', domain_text)
    
    # Enlever les mots de liaison restants
    for stop in ["niveau", "de", "du", "des", "un", "une", "comme", "tel", "que"]:
        domain_text = re.sub(r'\b' + stop + r'\b', '', domain_text, flags=re.IGNORECASE)
    domain_text = re.sub(r'\s+', ' ', domain_text).strip()
    
    if not domain_text or len(domain_text) < 2:
        return None
    
    return {
        "domain": domain_text,
        "depth": depth,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN (test)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    print("═══ Test DomainSpecializer ═══")
    print()
    
    # Test détection conversationnelle
    test_messages = [
        "Spécialise-toi en photographie",
        "Peux-tu apprendre la mécanique quantique niveau expert ?",
        "Je veux que tu maîtrises l'astrophysique",
        "Deviens experte en cuisine moléculaire",
        "Quel temps fait-il aujourd'hui ?",
        "Specialize in machine learning",
    ]
    
    print("Détection conversationnelle :")
    for msg in test_messages:
        intent = detect_specialize_intent(msg)
        print(f"  '{msg}' → {intent}")
    
    print()
    
    # Test génération de requêtes
    queries = _generate_search_queries("photographie", "expert")
    print(f"Requêtes générées pour 'photographie' (expert) : {len(queries)}")
    for i, q in enumerate(queries[:10]):
        print(f"  {i+1}. {q}")
    print(f"  ... et {len(queries) - 10} autres")
    
    print()
    print("✅ Tests de base OK")
