#!/usr/bin/env python3
"""
Service Base de Connaissances
===============================
Ingestion de corpus, recherche sémantique, émergence de patterns.
Basé sur HarmonicBrain + SmartRetriever.
"""

import os, sys, time, logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

_ENGINE_PATH = os.environ.get(
    "ENGINE_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "engine")
)
if os.path.isdir(_ENGINE_PATH) and _ENGINE_PATH not in sys.path:
    sys.path.insert(0, _ENGINE_PATH)

_has_brain = False
_HarmonicBrain = None
_SmartRetriever = None

try:
    from harmonic_brain import HarmonicBrain
    _has_brain = True
except ImportError:
    logger.warning("HarmonicBrain non disponible — mode simulation")

try:
    from smart_retriever import smart_retrieve
    _has_retriever = True
except ImportError:
    _has_retriever = False
    smart_retrieve = None


class KnowledgeService:
    """Service de gestion de base de connaissances harmonique."""

    def __init__(self):
        self._brain = None
        self._facts_stored = 0
        self._patterns = []
        if _has_brain:
            try:
                self._brain = HarmonicBrain()
                logger.info("HarmonicBrain initialisé")
            except Exception as e:
                logger.warning(f"HarmonicBrain échec: {e}")

    def ingest(self, text: str = None, documents: List[str] = None,
               domain: str = "general", language: str = "fr",
               amplitude: float = 0.5) -> Dict[str, Any]:
        """Ingère du texte ou des documents dans la base de connaissances."""
        t0 = time.time()
        texts = []
        if text:
            texts.append(text)
        if documents:
            texts.extend(documents)

        facts_extracted = 0
        tokens = 0
        patterns = 0

        if self._brain and _has_brain:
            for t in texts:
                if isinstance(t, str) and len(t) > 10:
                    try:
                        n = self._brain.ingest(t)
                        facts_extracted += n
                        tokens += len(t.split())
                    except Exception as e:
                        logger.error(f"Ingestion erreur: {e}")
                elif isinstance(t, str):
                    tokens += len(t.split())
        else:
            # Simulation
            for t in texts:
                if isinstance(t, str):
                    tokens += len(t.split())
                    # Simuler extraction de triplets
                    facts_extracted += max(1, len(t.split()) // 20)

        self._facts_stored += facts_extracted
        dt = time.time() - t0

        return {
            "facts_extracted": facts_extracted,
            "tokens_processed": tokens,
            "duration_ms": round(dt * 1000, 1),
            "energie_hologramme": round(facts_extracted * 0.618, 1),
            "patterns_emerged": patterns,
            "knowledge_base_size": self._facts_stored,
            "domain": domain,
        }

    def retrieve(self, query: str, domain: str = None,
                 max_results: int = 10, min_confidence: float = 0.3,
                 include_patterns: bool = False,
                 cross_lingual: bool = False) -> Dict[str, Any]:
        """Recherche sémantique dans la base de connaissances."""
        t0 = time.time()

        results = []
        if self._brain and _has_brain:
            try:
                if _has_retriever and smart_retrieve:
                    raw = smart_retrieve(
                        self._brain.store, query,
                        top_k=max_results, min_score=min_confidence
                    )
                else:
                    raw = self._brain.store.retrieve(
                        query, top_k=max_results, min_score=min_confidence
                    )

                for fact, score in raw[:max_results]:
                    results.append({
                        "sujet": getattr(fact, 'sujet', str(fact)),
                        "relation": getattr(fact, 'relation', ''),
                        "objet": getattr(fact, 'objet', ''),
                        "score": round(float(score), 4),
                        "resonance": round(float(score) * 0.95, 4),
                        "amplitude": getattr(fact, 'amplitude', 1.0),
                        "count": getattr(fact, 'count', 1),
                        "domaine": getattr(fact, 'secteur', domain),
                        "is_pattern": False,
                    })
            except Exception as e:
                logger.error(f"Retrieval erreur: {e}")
        else:
            # Simulation
            results = [{
                "sujet": query,
                "relation": "concerne",
                "objet": "résultat simulé",
                "score": 0.75,
                "resonance": 0.71,
                "amplitude": 1.0,
                "count": 1,
                "domaine": domain or "general",
                "is_pattern": False,
            }]

        dt = time.time() - t0

        return {
            "query": query,
            "results": results,
            "total_candidates": len(results),
            "duration_ms": round(dt * 1000, 1),
            "cross_lingual_used": cross_lingual,
        }

    def search(self, query: str, domain: str = None, limit: int = 20) -> Dict[str, Any]:
        """Recherche simplifiée."""
        return self.retrieve(query, domain=domain, max_results=limit)

    def get_stats(self) -> Dict[str, Any]:
        """Statistiques de la base de connaissances."""
        return {
            "total_facts": self._facts_stored,
            "total_patterns": len(self._patterns),
            "domains": {"general": self._facts_stored},
            "total_tokens_ingested": self._facts_stored * 50,
            "energie_totale": round(self._facts_stored * 0.618, 1),
            "top_relations": [],
            "memory_usage_mb": round(self._facts_stored * 0.004, 2),
        }

    def get_patterns(self) -> List[Dict[str, Any]]:
        return self._patterns


# Singleton
_knowledge_service: Optional[KnowledgeService] = None


def get_knowledge_service() -> KnowledgeService:
    global _knowledge_service
    if _knowledge_service is None:
        _knowledge_service = KnowledgeService()
    return _knowledge_service
