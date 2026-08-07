#!/usr/bin/env python3
"""
Schémas Base de Connaissances
===============================
Modèles pour l'ingestion, la recherche sémantique et l'émergence de patterns.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class KnowledgeDomain(str, Enum):
    """Domaines de connaissance supportés."""
    GENERAL = "general"
    SCIENCE = "science"
    MEDICINE = "medicine"
    LAW = "law"
    FINANCE = "finance"
    CODE = "code"
    PHYSICS = "physics"
    BIOLOGY = "biology"
    CHEMISTRY = "chemistry"
    CUSTOM = "custom"


class IngestMode(str, Enum):
    """Modes d'ingestion."""
    TRIPLE_EXTRACTION = "triple_extraction"   # Regex-based triple extraction
    LLM_ASSISTED = "llm_assisted"             # LLM-assisted triple extraction
    RAW_HOLOGRAPHIC = "raw_holographic"       # Direct wave encoding
    CORPUS_BATCH = "corpus_batch"             # Batch corpus ingestion


class IngestRequest(BaseModel):
    """Requête d'ingestion de connaissances."""
    domain: KnowledgeDomain = Field(default=KnowledgeDomain.GENERAL)
    mode: IngestMode = Field(default=IngestMode.TRIPLE_EXTRACTION)
    text: Optional[str] = Field(default=None, description="Texte à ingérer")
    documents: Optional[List[str]] = Field(default=None, description="Documents multiples")
    corpus_path: Optional[str] = Field(default=None, description="Chemin vers un dossier corpus")
    language: str = Field(default="fr", description="Langue: fr, en, auto")
    amplitude: float = Field(default=0.5, ge=0.0, le=1.0)


class IngestResponse(BaseModel):
    """Réponse après ingestion."""
    facts_extracted: int
    tokens_processed: int
    duration_ms: float
    energie_hologramme: float
    patterns_emerged: int = 0
    knowledge_base_size: int = Field(description="Nombre total de faits dans la base")
    domain: str


class RetrieveRequest(BaseModel):
    """Requête de recherche sémantique."""
    query: str = Field(..., min_length=1, max_length=2000)
    domain: Optional[KnowledgeDomain] = None
    max_results: int = Field(default=10, ge=1, le=100)
    min_confidence: float = Field(default=0.3, ge=0.0, le=1.0)
    include_patterns: bool = False
    cross_lingual: bool = Field(default=False, description="Recherche cross-linguale FR/EN")


class RetrievedFact(BaseModel):
    """Fait retrouvé par la recherche."""
    sujet: str
    relation: str
    objet: str
    score: float = Field(ge=0.0, le=1.0)
    resonance: float = Field(description="Score de résonance harmonique")
    amplitude: float
    count: int = Field(description="Nombre de répétitions (renforcement)")
    domaine: Optional[str] = None
    is_pattern: bool = False


class RetrieveResponse(BaseModel):
    """Réponse de recherche sémantique."""
    query: str
    results: List[RetrievedFact]
    total_candidates: int
    duration_ms: float
    cross_lingual_used: bool = False


class KnowledgeStatsResponse(BaseModel):
    """Statistiques de la base de connaissances."""
    total_facts: int
    total_patterns: int
    domains: Dict[str, int] = Field(default_factory=dict)
    total_tokens_ingested: int
    energie_totale: float
    top_relations: List[Dict[str, Any]] = Field(default_factory=list)
    memory_usage_mb: float


class PatternResponse(BaseModel):
    """Pattern émergé de la base."""
    pattern_id: str
    relation: str
    facts_count: int
    confidence: float
    examples: List[str] = Field(default_factory=list)
    emergence_date: Optional[str] = None
