#!/usr/bin/env python3
"""
Endpoints Raisonnement Conscient
==================================
Chaînage, analogie, contradiction, généralisation.
"""

import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.reasoning import (
    ReasonRequest, ReasoningResponse,
    AnalogyRequest, AnalogyResponse,
    ContradictionRequest, ContradictionResponse,
    GeneralizeRequest, GeneralizeResponse,
)
from app.services.reasoning_service import get_reasoning_service, ReasoningService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/reason", response_model=ReasoningResponse)
async def reason(
    request: ReasonRequest,
    service: ReasoningService = Depends(get_reasoning_service),
) -> Any:
    """Raisonnement général (chaînage, abduction, etc.)."""
    try:
        result = service.reason(
            question=request.question,
            method=request.method.value if request.method else "auto",
            max_depth=request.max_depth,
            domain=request.domain,
            verified_mode=request.verified_mode,
        )
        return ReasoningResponse(**result)
    except Exception as e:
        logger.error(f"Reason error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analogy", response_model=AnalogyResponse)
async def analogy(
    request: AnalogyRequest,
    service: ReasoningService = Depends(get_reasoning_service),
) -> Any:
    """Raisonnement par analogie : A:B :: C:?"""
    try:
        result = service.analogy(
            term_a=request.term_a,
            term_b=request.term_b,
            term_c=request.term_c,
            domain=request.domain,
            max_candidates=request.max_candidates,
        )
        return AnalogyResponse(**result)
    except Exception as e:
        logger.error(f"Analogy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contradictions", response_model=ContradictionResponse)
async def detect_contradictions(
    request: ContradictionRequest,
    service: ReasoningService = Depends(get_reasoning_service),
) -> Any:
    """Détecte les contradictions dans une liste de déclarations."""
    try:
        result = service.detect_contradictions(
            statements=request.statements,
            domain=request.domain,
        )
        return ContradictionResponse(**result)
    except Exception as e:
        logger.error(f"Contradiction detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generalize", response_model=GeneralizeResponse)
async def generalize(
    request: GeneralizeRequest,
    service: ReasoningService = Depends(get_reasoning_service),
) -> Any:
    """Généralise à partir d'exemples pour former un concept abstrait."""
    try:
        result = service.generalize(
            examples=request.examples,
            domain=request.domain,
            target_level=request.target_abstraction_level,
        )
        return GeneralizeResponse(**result)
    except Exception as e:
        logger.error(f"Generalize error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
