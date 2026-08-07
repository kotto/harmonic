#!/usr/bin/env python3
"""
Schémas Raisonnement Conscient
================================
Modèles pour le raisonnement par chaînage, analogie, contradiction, généralisation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class ReasoningMethod(str, Enum):
    """Méthodes de raisonnement disponibles."""
    CHAIN = "chain"               # Inférence transitive
    ANALOGY = "analogy"           # Raisonnement par analogie
    CONTRADICTION = "contradiction"  # Détection de contradictions
    GENERALIZATION = "generalization"  # Généralisation à partir de patterns
    ABDUCTION = "abduction"       # Inférence vers la meilleure explication
    AUTO = "auto"                 # Sélection automatique


class ReasonRequest(BaseModel):
    """Requête de raisonnement."""
    question: str = Field(..., min_length=1, max_length=5000)
    method: ReasoningMethod = Field(default=ReasoningMethod.AUTO)
    domain: Optional[str] = None
    max_depth: int = Field(default=3, ge=1, le=10, description="Profondeur max de la chaîne de raisonnement")
    include_sources: bool = True
    verified_mode: bool = False
    language: str = Field(default="fr")


class ReasoningStep(BaseModel):
    """Étape intermédiaire de raisonnement."""
    step_number: int
    operation: str
    input_facts: List[str] = Field(default_factory=list)
    conclusion: str
    confidence: float = Field(ge=0.0, le=1.0)
    method: str


class ReasoningResponse(BaseModel):
    """Réponse de raisonnement."""
    question: str
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    method_used: str
    depth_reached: int
    steps: List[ReasoningStep] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    duration_ms: float
    alternative_answers: List[Dict[str, Any]] = Field(default_factory=list)


class AnalogyRequest(BaseModel):
    """Requête d'analogie (A:B :: C:?)."""
    term_a: str = Field(..., min_length=1)
    term_b: str = Field(..., min_length=1)
    term_c: str = Field(..., min_length=1)
    domain: Optional[str] = None
    max_candidates: int = Field(default=5, ge=1, le=20)


class AnalogyResponse(BaseModel):
    """Réponse d'analogie."""
    term_a: str
    term_b: str
    term_c: str
    predicted_term: str
    candidates: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float
    vector_distance: float
    explanation: Optional[str] = None


class ContradictionRequest(BaseModel):
    """Requête de détection de contradictions."""
    statements: List[str] = Field(..., min_length=2, max_length=50)
    domain: Optional[str] = None


class ContradictionPair(BaseModel):
    """Paire de déclarations contradictoires."""
    statement_a: str
    statement_b: str
    contradiction_score: float = Field(ge=0.0, le=1.0)
    explanation: str
    resolution_suggestion: Optional[str] = None


class ContradictionResponse(BaseModel):
    """Réponse de détection de contradictions."""
    contradictions: List[ContradictionPair]
    total_pairs_checked: int
    is_internally_consistent: bool
    overall_consistency_score: float = Field(ge=0.0, le=1.0)


class GeneralizeRequest(BaseModel):
    """Requête de généralisation."""
    examples: List[str] = Field(..., min_length=2, max_length=100)
    domain: Optional[str] = None
    target_abstraction_level: int = Field(default=1, ge=1, le=5)


class GeneralizeResponse(BaseModel):
    """Réponse de généralisation."""
    generalization: str
    confidence: float
    examples_used: int
    abstraction_level: int
    related_concepts: List[str] = Field(default_factory=list)
    counter_examples: List[str] = Field(default_factory=list)
