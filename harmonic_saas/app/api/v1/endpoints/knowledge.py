#!/usr/bin/env python3
"""
Endpoints Base de Connaissances
=================================
Ingestion, recherche sémantique, émergence de patterns.
"""

import logging
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.knowledge_job import KnowledgeJob, KnowledgeJobType, KnowledgeJobStatus
from app.schemas.knowledge import (
    IngestRequest, IngestResponse,
    RetrieveRequest, RetrieveResponse,
    KnowledgeStatsResponse,
    PatternResponse,
)
from app.services.knowledge_service import get_knowledge_service, KnowledgeService
import uuid
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/ingest", response_model=IngestResponse)
async def ingest_knowledge(
    request: IngestRequest,
    current_user: User = Depends(get_current_user),
    service: KnowledgeService = Depends(get_knowledge_service),
    db: Session = Depends(get_db),
) -> Any:
    """Ingère des connaissances dans la base harmonique."""
    try:
        result = service.ingest(
            text=request.text,
            documents=request.documents,
            domain=request.domain.value,
            language=request.language,
            amplitude=request.amplitude,
        )

        job = KnowledgeJob(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            name=f"Ingest: {request.domain.value}",
            job_type=KnowledgeJobType.INGEST,
            status=KnowledgeJobStatus.COMPLETED,
            domain=request.domain.value,
            language=request.language,
            facts_extracted=result["facts_extracted"],
            tokens_processed=result["tokens_processed"],
            patterns_emerged=result["patterns_emerged"],
            duration_ms=result["duration_ms"],
            energie_hologramme=result["energie_hologramme"],
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db.add(job)
        db.commit()

        return IngestResponse(**result)
    except Exception as e:
        logger.error(f"Ingest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_knowledge(
    request: RetrieveRequest,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> Any:
    """Recherche sémantique dans la base de connaissances."""
    try:
        result = service.retrieve(
            query=request.query,
            domain=request.domain.value if request.domain else None,
            max_results=request.max_results,
            min_confidence=request.min_confidence,
            include_patterns=request.include_patterns,
            cross_lingual=request.cross_lingual,
        )
        return RetrieveResponse(**result)
    except Exception as e:
        logger.error(f"Retrieve error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_knowledge(
    request: RetrieveRequest,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> Any:
    """Recherche simplifiée (alias de /retrieve)."""
    result = service.search(
        query=request.query,
        domain=request.domain.value if request.domain else None,
        limit=request.max_results,
    )
    return result


@router.get("/stats", response_model=KnowledgeStatsResponse)
async def get_knowledge_stats(
    service: KnowledgeService = Depends(get_knowledge_service),
) -> Any:
    """Statistiques de la base de connaissances."""
    return KnowledgeStatsResponse(**service.get_stats())


@router.get("/patterns", response_model=List[PatternResponse])
async def get_patterns(
    service: KnowledgeService = Depends(get_knowledge_service),
) -> Any:
    """Liste les patterns émergés de la base."""
    return [PatternResponse(**p) for p in service.get_patterns()]


@router.delete("/clear")
async def clear_knowledge(
    current_user: User = Depends(get_current_user),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> Any:
    """Réinitialise la base de connaissances (admin)."""
    service._facts_stored = 0
    service._patterns = []
    if service._brain:
        try:
            service._brain = None  # Sera réinitialisé au prochain appel
        except Exception:
            pass
    return {"success": True, "message": "Base de connaissances réinitialisée"}
