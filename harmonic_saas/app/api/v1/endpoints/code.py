#!/usr/bin/env python3
"""
Endpoints Code Intelligent
============================
Génération zero-LLM, explication, traduction, refactoring.
"""

import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.code import (
    CodeGenRequest, CodeGenResponse,
    CodeExplainRequest, CodeExplainResponse,
    CodeTranslateRequest, CodeTranslateResponse,
    CodeRefactorRequest, CodeRefactorResponse,
)
from app.services.code_service import get_code_service, CodeService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/generate", response_model=CodeGenResponse)
async def generate_code(
    request: CodeGenRequest,
    current_user: User = Depends(get_current_user),
    service: CodeService = Depends(get_code_service),
) -> Any:
    """Génère du code à partir d'une description en langage naturel (zero-LLM)."""
    try:
        result = service.generate(
            prompt=request.prompt,
            language=request.language.value if request.language else "python",
            mode=request.mode.value if request.mode else "auto",
            context=request.context,
            include_tests=request.include_tests,
            include_docs=request.include_docs,
            novel_synthesis=request.novel_synthesis,
        )
        return CodeGenResponse(**result)
    except Exception as e:
        logger.error(f"Code gen error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain", response_model=CodeExplainResponse)
async def explain_code(
    request: CodeExplainRequest,
    service: CodeService = Depends(get_code_service),
) -> Any:
    """Explique un code source en langage naturel."""
    try:
        result = service.explain(
            code=request.code,
            language=request.language.value if request.language else None,
            detail_level=request.detail_level,
        )
        return CodeExplainResponse(**result)
    except Exception as e:
        logger.error(f"Code explain error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/translate", response_model=CodeTranslateResponse)
async def translate_code(
    request: CodeTranslateRequest,
    service: CodeService = Depends(get_code_service),
) -> Any:
    """Traduit du code d'un langage à un autre."""
    try:
        result = service.translate(
            code=request.code,
            source_lang=request.source_language.value,
            target_lang=request.target_language.value,
            preserve_comments=request.preserve_comments,
            optimize=request.optimize_for_target,
        )
        return CodeTranslateResponse(**result)
    except Exception as e:
        logger.error(f"Code translate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refactor", response_model=CodeRefactorResponse)
async def refactor_code(
    request: CodeRefactorRequest,
    service: CodeService = Depends(get_code_service),
) -> Any:
    """Refactore du code."""
    try:
        result = service.refactor(
            code=request.code,
            language=request.language.value if request.language else "python",
            refactor_type=request.refactor_type,
            target_pattern=request.target_pattern,
        )
        return CodeRefactorResponse(**result)
    except Exception as e:
        logger.error(f"Code refactor error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
