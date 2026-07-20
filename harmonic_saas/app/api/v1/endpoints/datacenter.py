#!/usr/bin/env python3
"""
Endpoints Datacenter Holographique
====================================
API Boîte Noire — ingestion one-pass, génération enrichie, sessions hologrammes.
"""

import logging
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.datacenter import (
    TrainRequest, TrainResponse,
    GenerateRequest, GenerateResponse,
    HologramSessionResponse, DatacenterStatsResponse,
)
from app.services.datacenter_service import get_datacenter_service, DatacenterService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/train", response_model=TrainResponse)
async def train_hologram(
    request: TrainRequest,
    current_user: User = Depends(get_current_user),
    service: DatacenterService = Depends(get_datacenter_service),
) -> Any:
    """Ingère des documents dans l'hologramme du client (one-pass CPU, 0€)."""
    try:
        result = service.train(
            session_id=request.session_id,
            documents=request.documents,
            amplitude=request.amplitude,
            user_id=current_user.id,
        )
        return TrainResponse(**result)
    except Exception as e:
        logger.error(f"Train error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=GenerateResponse)
async def generate_from_hologram(
    request: GenerateRequest,
    current_user: User = Depends(get_current_user),
    service: DatacenterService = Depends(get_datacenter_service),
) -> Any:
    """Génère une réponse enrichie par l'hologramme du client."""
    try:
        result = service.generate(
            session_id=request.session_id,
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            verified_mode=request.verified_mode,
        )
        return GenerateResponse(**result)
    except Exception as e:
        logger.error(f"Generate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=List[HologramSessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    service: DatacenterService = Depends(get_datacenter_service),
) -> Any:
    """Liste toutes les sessions holographiques de l'utilisateur."""
    sessions = service.list_sessions(user_id=current_user.id)
    return [HologramSessionResponse(**s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=HologramSessionResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    service: DatacenterService = Depends(get_datacenter_service),
) -> Any:
    """Récupère l'état d'une session holographique."""
    session = service.get_session(session_id, current_user.id)
    holo_path = service.storage_path + "/" + session.get("hologramme_file", "")
    import os
    taille = os.path.getsize(holo_path) if os.path.exists(holo_path) else 0
    return HologramSessionResponse(**session, taille_hologramme=taille)


@router.get("/stats", response_model=DatacenterStatsResponse)
async def get_datacenter_stats(
    service: DatacenterService = Depends(get_datacenter_service),
) -> Any:
    """Statistiques globales du datacenter."""
    return DatacenterStatsResponse(**service.get_stats())


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    service: DatacenterService = Depends(get_datacenter_service),
) -> Any:
    """Désactive une session holographique."""
    registry = service._load_registry()
    if session_id in registry and registry[session_id].get("user_id") == current_user.id:
        registry[session_id]["active"] = False
        service._save_registry(registry)
        return {"success": True, "message": f"Session {session_id} désactivée"}
    raise HTTPException(status_code=404, detail="Session non trouvée")
