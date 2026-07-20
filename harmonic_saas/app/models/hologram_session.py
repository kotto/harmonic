#!/usr/bin/env python3
"""
Modèle HologramSession
========================
Suivi des sessions holographiques client pour le Datacenter Harmonique.
Chaque client a un hologramme de 32 Ko stocké comme fichier .holo.
"""

from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class HologramSession(Base):
    __tablename__ = "hologram_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    # Session identity
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), default="Default Session")

    # Hologram data
    hologramme_file = Column(String(500), nullable=True, doc="Chemin vers le fichier .holo")
    taille_hologramme = Column(Integer, default=0, doc="Taille en octets")
    energie = Column(Float, default=0.0, doc="Énergie harmonique de l'hologramme")

    # Usage metrics
    total_tokens = Column(Integer, default=0)
    total_documents = Column(Integer, default=0)
    total_requests = Column(Integer, default=0)
    total_generations = Column(Integer, default=0)

    # Status
    active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)

    # Metadata
    domain = Column(String(100), nullable=True)
    language = Column(String(10), default="fr")
    metadata = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_activity = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="hologram_sessions")
