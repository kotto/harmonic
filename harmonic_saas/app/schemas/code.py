#!/usr/bin/env python3
"""
Schémas Code Intelligent
==========================
Modèles pour la génération, explication, traduction et refactoring de code.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class ProgrammingLanguage(str, Enum):
    """Langages supportés."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    RUST = "rust"
    GO = "go"
    SQL = "sql"
    JAVA = "java"
    CPP = "cpp"
    HTML = "html"
    CSS = "css"
    AUTO = "auto"


class CodeGenMode(str, Enum):
    FUNCTION = "function"
    CLASS = "class"
    SCRIPT = "script"
    ALGORITHM = "algorithm"
    API_ENDPOINT = "api_endpoint"
    DATA_PIPELINE = "data_pipeline"
    AUTO = "auto"


class CodeGenRequest(BaseModel):
    """Requête de génération de code."""
    prompt: str = Field(..., min_length=3, max_length=5000, description="Description en langage naturel")
    language: ProgrammingLanguage = Field(default=ProgrammingLanguage.PYTHON)
    mode: CodeGenMode = Field(default=CodeGenMode.AUTO)
    context: Optional[str] = Field(default=None, description="Code contextuel existant")
    max_tokens: int = Field(default=2000, ge=100, le=8000)
    include_tests: bool = False
    include_docs: bool = True
    novel_synthesis: bool = Field(default=False, description="Synthèse novatrice via HRRUnbinder")


class CodeGenResponse(BaseModel):
    """Réponse de génération de code."""
    code: str
    language: str
    confidence: float = Field(ge=0.0, le=1.0)
    intent: str
    source: str = Field(description="Source: template, corpus, novel_synthesis")
    facts_used: int = 0
    explanation: Optional[str] = None
    tests: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class CodeExplainRequest(BaseModel):
    """Requête d'explication de code."""
    code: str = Field(..., min_length=1, max_length=50000)
    language: Optional[ProgrammingLanguage] = None
    detail_level: str = Field(default="detailed", description="summary, detailed, line_by_line")


class LineExplanation(BaseModel):
    """Explication ligne par ligne."""
    line_number: int
    code: str
    explanation: str
    complexity_note: Optional[str] = None


class CodeExplainResponse(BaseModel):
    """Réponse d'explication de code."""
    summary: str
    detailed: str
    line_by_line: Optional[List[LineExplanation]] = None
    patterns_detected: List[str] = Field(default_factory=list)
    language: str
    confidence: float
    complexity: str = Field(description="Estimation de complexité: O(1), O(n), O(n²), etc.")
    suggestions: List[str] = Field(default_factory=list)


class CodeTranslateRequest(BaseModel):
    """Requête de traduction de code."""
    code: str = Field(..., min_length=1, max_length=50000)
    source_language: ProgrammingLanguage
    target_language: ProgrammingLanguage
    preserve_comments: bool = True
    optimize_for_target: bool = True


class CodeTranslateResponse(BaseModel):
    """Réponse de traduction de code."""
    translated_code: str
    source_language: str
    target_language: str
    confidence: float
    notes: List[str] = Field(default_factory=list)
    changes_summary: Optional[str] = None


class CodeRefactorRequest(BaseModel):
    """Requête de refactoring de code."""
    code: str = Field(..., min_length=1, max_length=50000)
    language: ProgrammingLanguage
    refactor_type: str = Field(default="auto", description="auto, performance, readability, design_pattern, security")
    target_pattern: Optional[str] = Field(default=None, description="Pattern cible: Singleton, Factory, Observer, etc.")


class CodeRefactorResponse(BaseModel):
    """Réponse de refactoring."""
    original_code: str
    refactored_code: str
    changes: List[Dict[str, Any]] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    confidence: float
    risks: List[str] = Field(default_factory=list)
