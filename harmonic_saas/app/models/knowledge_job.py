#!/usr/bin/env python3
"""
Modèle KnowledgeJob
====================
Suivi des jobs d'ingestion et traitement de connaissances.
"""

from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey, Enum, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class KnowledgeJobType(str, enum.Enum):
    INGEST = "ingest"
    RETRIEVAL = "retrieval"
    PATTERN_EMERGENCE = "pattern_emergence"
    CORPUS_BATCH = "corpus_batch"
    RUMINATION = "rumination"
    CROSS_LINGUAL_ALIGN = "cross_lingual_align"


class KnowledgeJobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class KnowledgeJob(Base):
    __tablename__ = "knowledge_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    # Job identity
    name = Column(String(255), default="Knowledge Job")
    job_type = Column(Enum(KnowledgeJobType), nullable=False)
    status = Column(Enum(KnowledgeJobStatus), default=KnowledgeJobStatus.PENDING)

    # Domain
    domain = Column(String(100), default="general")
    language = Column(String(10), default="fr")

    # Input
    input_text = Column(Text, nullable=True)
    input_corpus_path = Column(String(500), nullable=True)
    input_documents_count = Column(Integer, nullable=True)

    # Output
    facts_extracted = Column(Integer, default=0)
    tokens_processed = Column(Integer, default=0)
    patterns_emerged = Column(Integer, default=0)
    knowledge_base_size = Column(Integer, nullable=True)

    # Performance
    duration_ms = Column(Float, nullable=True)
    energie_hologramme = Column(Float, default=0.0)
    throughput_tokens_per_sec = Column(Float, nullable=True)

    # Quality
    confidence = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="knowledge_jobs")
