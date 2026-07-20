#!/usr/bin/env python3
"""
Schémas Datacenter Holographique
=================================
Modèles de requêtes/réponses pour le service Datacenter Harmonique (Boîte Noire).
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TrainRequest(BaseModel):
    """Requête d'ingestion de documents dans l'hologramme client."""
    session_id: str = Field(default="default", description="Identifiant de session client")
    documents: List[str] = Field(..., min_length=1, description="Documents texte à ingérer")
    amplitude: Optional[float] = Field(default=0.5, ge=0.0, le=1.0, description="Amplitude d'ingestion (0-1)")


class TrainResponse(BaseModel):
    """Réponse après ingestion de documents."""
    session_id: str
    documents_ingérés: int
    tokens_ingérés: int
    temps_ms: float
    tok_s: float
    energie_hologramme: float
    taille_hologramme: int = Field(description="Taille du fichier .holo en octets")
    cout_estime: str = "0€ (one-pass CPU)"


class GenerateRequest(BaseModel):
    """Requête de génération enrichie par l'hologramme."""
    session_id: str = Field(default="default")
    prompt: str = Field(..., min_length=1, max_length=32000)
    max_tokens: int = Field(default=500, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    verified_mode: bool = Field(default=False, description="Mode vérifié déterministe")


class GenerateResponse(BaseModel):
    """Réponse générée enrichie par l'hologramme."""
    session_id: str
    texte_genere: str
    n_tokens: int
    temps_ms: float
    energie_hologramme: float
    mode: str = "harmonic"
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    response_id: Optional[str] = Field(default=None, description="SHA256 pour audit déterministe")
    citations: List[str] = Field(default_factory=list)


class HologramSessionResponse(BaseModel):
    """État d'une session holographique."""
    session_id: str
    created: str
    total_tokens: int
    requests: int
    taille_hologramme: int = 0
    active: bool = True
    last_activity: Optional[str] = None
    energie: float = 0.0

    model_config = {"from_attributes": True}


class DatacenterStatsResponse(BaseModel):
    """Statistiques globales du datacenter."""
    total_clients: int
    total_tokens_ingérés: int
    total_requetes: int
    stockage_total_octets: int
    marge_estimee: str = "99.5%"
    uptime: str = "99.9%"
