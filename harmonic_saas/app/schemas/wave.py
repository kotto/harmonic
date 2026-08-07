#!/usr/bin/env python3
"""
Schémas Wave & Créativité
===========================
Modèles pour l'explication scientifique, le cross-lingual et la génération créative.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class ScientificDomain(str, Enum):
    """Domaines scientifiques supportés."""
    AUTO = "auto"
    PHYSICS = "physics"
    BIOLOGY = "biology"
    ASTRONOMY = "astronomy"
    CHEMISTRY = "chemistry"
    MATHEMATICS = "mathematics"
    COMPUTER_SCIENCE = "computer_science"
    MEDICINE = "medicine"
    QUANTUM = "quantum"


class WaveExplainRequest(BaseModel):
    """Requête d'explication scientifique."""
    question: str = Field(..., min_length=3, max_length=3000)
    domain: ScientificDomain = Field(default=ScientificDomain.AUTO)
    language: str = Field(default="fr", description="fr, en")
    detail_level: str = Field(default="comprehensive", description="simple, comprehensive, academic")
    include_causal_chain: bool = True
    include_references: bool = True


class CausalStep(BaseModel):
    """Étape de chaîne causale."""
    step: int
    description: str
    evidence: str = ""
    confidence: float = 1.0


class WaveExplainResponse(BaseModel):
    """Réponse d'explication scientifique."""
    question: str
    domain: str
    explanation: str
    causal_chain: List[CausalStep] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)
    confidence: float
    language: str
    analogies_used: List[str] = Field(default_factory=list)


class Language(str, Enum):
    FR = "fr"
    EN = "en"
    ES = "es"
    DE = "de"
    AUTO = "auto"


class CrossLingualRequest(BaseModel):
    """Requête cross-linguale."""
    text: str = Field(..., min_length=1, max_length=10000)
    source_language: Language = Field(default=Language.AUTO)
    target_language: Language
    mode: str = Field(default="similarity", description="similarity, translate_concepts, align")


class CrossLingualResponse(BaseModel):
    """Réponse cross-linguale."""
    source_text: str
    source_language: str
    target_language: str
    similarity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    aligned_concepts: List[Dict[str, str]] = Field(default_factory=list)
    translated_concepts: Optional[str] = None
    rotation_matrix_applied: bool = True


class CreativeMode(str, Enum):
    HAIKU = "haiku"
    METAPHOR = "metaphor"
    POEM = "poem"
    STORY = "story"
    DIALOGUE = "dialogue"
    SLOGAN = "slogan"


class CreativeStyle(str, Enum):
    CLASSIC = "classic"
    SURREAL = "surreal"
    LYRICAL = "lyrical"
    PHILOSOPHICAL = "philosophical"
    HUMORISTIC = "humoristic"
    TECHNICAL = "technical"


class CreativeRequest(BaseModel):
    """Requête de génération créative."""
    mode: CreativeMode
    theme: str = Field(..., min_length=1, max_length=500)
    style: CreativeStyle = Field(default=CreativeStyle.CLASSIC)
    language: str = Field(default="fr")
    max_length: int = Field(default=500, ge=20, le=2000)
    additional_context: Optional[str] = None


class CreativeResponse(BaseModel):
    """Réponse de génération créative."""
    mode: str
    theme: str
    text: str
    form: str = Field(description="Forme: haiku (5-7-5), metaphor, free_verse, etc.")
    language: str
    confidence: float
    harmonic_resonance: float = Field(description="Score de résonance harmonique φ")
    inspiration_facts: List[str] = Field(default_factory=list, description="Faits ayant inspiré la création")


class WaveStatsResponse(BaseModel):
    """Statistiques des services Wave."""
    total_explanations: int = 0
    total_cross_lingual_requests: int = 0
    total_creative_generations: int = 0
    supported_languages: List[str] = Field(default_factory=lambda: ["fr", "en", "es", "de"])
    supported_domains: List[str] = Field(default_factory=list)
