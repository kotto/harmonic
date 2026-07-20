#!/usr/bin/env python3
"""
Modèle HPC Job
===============
Suivi des jobs de calcul haute performance : repliement protéique,
simulation quantique, calcul NP-complet, dynamique moléculaire.
"""

from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey, Enum, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class HPCJobType(str, enum.Enum):
    PROTEIN_FOLDING = "protein_folding"
    QUANTUM_SIMULATION = "quantum_simulation"
    NP_COMPLETE = "np_complete"
    MOLECULAR_DYNAMICS = "molecular_dynamics"
    FLUID_DYNAMICS = "fluid_dynamics"
    WEATHER_MODELING = "weather_modeling"
    GENOMIC_ANALYSIS = "genomic_analysis"
    FINANCIAL_MODELING = "financial_modeling"


class HPCJobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class HPCJob(Base):
    __tablename__ = "hpc_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    # Job identity
    name = Column(String(255), default="HPC Job")
    job_type = Column(Enum(HPCJobType), nullable=False)
    status = Column(Enum(HPCJobStatus), default=HPCJobStatus.PENDING)
    priority = Column(Integer, default=1)

    # Parameters (JSON)
    parameters = Column(JSON, default=dict)

    # Input
    input_data = Column(Text, nullable=True)
    input_file_url = Column(String(500), nullable=True)
    input_size_bytes = Column(Integer, nullable=True)

    # Output
    result = Column(JSON, nullable=True)
    output_file_url = Column(String(500), nullable=True)
    output_size_bytes = Column(Integer, nullable=True)

    # Performance metrics
    estimated_duration_seconds = Column(Float, nullable=True)
    actual_duration_ms = Column(Float, nullable=True)
    progress_percent = Column(Float, default=0.0)
    harmonic_speedup = Column(Float, nullable=True, doc="Facteur d'accélération harmonique")
    co2_saved_kg = Column(Float, nullable=True, doc="CO₂ économisé vs calcul classique")
    cpu_seconds_used = Column(Float, nullable=True)

    # Quality
    confidence = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    service_response = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="hpc_jobs")
