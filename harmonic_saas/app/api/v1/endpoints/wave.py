#!/usr/bin/env python3
"""
Endpoints Wave & Créativité
=============================
Explication scientifique, cross-lingual, génération créative.
"""

import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from app.schemas.wave import (
    WaveExplainRequest, WaveExplainResponse,
    CrossLingualRequest, CrossLingualResponse,
    CreativeRequest, CreativeResponse,
    WaveStatsResponse,
)
from app.services.wave_service import get_wave_service, WaveService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/explain", response_model=WaveExplainResponse)
async def explain_science(
    request: WaveExplainRequest,
    service: WaveService = Depends(get_wave_service),
) -> Any:
    """Génère une explication scientifique par résonance harmonique."""
    try:
        result = service.explain(
            question=request.question,
            domain=request.domain.value if request.domain else "auto",
            language=request.language,
            detail_level=request.detail_level,
            include_causal_chain=request.include_causal_chain,
            include_references=request.include_references,
        )
        return WaveExplainResponse(**result)
    except Exception as e:
        logger.error(f"Wave explain error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cross-lingual", response_model=CrossLingualResponse)
async def cross_lingual(
    request: CrossLingualRequest,
    service: WaveService = Depends(get_wave_service),
) -> Any:
    """Opération cross-linguale (similarité, alignement conceptuel)."""
    try:
        result = service.cross_lingual(
            text=request.text,
            source_lang=request.source_language.value if request.source_language else "auto",
            target_lang=request.target_language.value,
            mode=request.mode,
        )
        return CrossLingualResponse(**result)
    except Exception as e:
        logger.error(f"Cross-lingual error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/creative", response_model=CreativeResponse)
async def creative_generate(
    request: CreativeRequest,
    service: WaveService = Depends(get_wave_service),
) -> Any:
    """Génération créative (haïku, poème, métaphore, histoire)."""
    try:
        result = service.creative(
            mode=request.mode.value,
            theme=request.theme,
            style=request.style.value if request.style else "classic",
            language=request.language,
            max_length=request.max_length,
            context=request.additional_context,
        )
        return CreativeResponse(**result)
    except Exception as e:
        logger.error(f"Creative error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=WaveStatsResponse)
async def get_wave_stats(
    service: WaveService = Depends(get_wave_service),
) -> Any:
    """Statistiques des services Wave."""
    return WaveStatsResponse(**service.get_stats())
