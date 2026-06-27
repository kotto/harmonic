#!/usr/bin/env python3
"""
Chat Endpoints - LM Arena Integration
======================================
Endpoints pour l'intégration avec les services LM Arena
- Génération de réponses avec DeepSeek API
- Traitement audio/vidéo harmonique
- Gestion des sessions de chat
"""

import logging
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.audio_job import AudioJob, AudioJobStatus
from app.models.video_job import VideoJob, VideoJobStatus
from app.schemas.audio import AudioProcessingRequest, AudioProcessingResponse
from app.schemas.video import VideoProcessingRequest, VideoProcessingResponse
from app.schemas.chat import ChatRequest, ChatResponse, ChatSession
from app.services.lm_arena_integration import (
    LMArenaIntegrationService,
    get_lm_arena_service,
    DeepSeekRequest,
    AudioProcessingRequest as AudioRequest,
    VideoProcessingRequest as VideoRequest
)
from app.services.audio_service import AudioService
from app.services.video_service import VideoService
from app.tasks.audio_tasks import process_audio_task
from app.tasks.video_tasks import process_video_task

router = APIRouter()
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# CHAT ENDPOINTS
# ----------------------------------------------------------------------------

@router.post("/generate", response_model=ChatResponse)
async def generate_chat_response(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    lm_arena_service: LMArenaIntegrationService = Depends(get_lm_arena_service),
    db: Session = Depends(get_db)
) -> Any:
    """
    Générer une réponse de chat avec intégration LM Arena
    
    Args:
        request: Requête de chat
        current_user: Utilisateur authentifié
        lm_arena_service: Service d'intégration LM Arena
        db: Session de base de données
        
    Returns:
        Réponse de chat formatée
    """
    try:
        logger.info(f"Chat generation request from user {current_user.id}: {request.prompt[:100]}...")
        
        # Vérifier les limites d'utilisation
        if not AudioService.check_usage_limit(db, current_user):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Monthly usage limit exceeded"
            )
        
        # Appeler le service LM Arena
        response = await lm_arena_service.generate_lm_arena_response(
            prompt=request.prompt,
            user_id=current_user.id
        )
        
        # Mettre à jour les métriques d'utilisation
        AudioService.update_usage_metrics(db, current_user, "chat", 1)
        
        # Créer la réponse
        chat_response = ChatResponse(
            success=True,
            response=response["response"],
            confidence=response["confidence"],
            processing_time=response["processing_time"],
            response_id=response["response_id"],
            verified_mode=response["verified_mode"],
            citations=response["citations"],
            user_id=current_user.id,
            timestamp=datetime.utcnow().isoformat()
        )
        
        logger.info(f"Chat generation successful for user {current_user.id}")
        return chat_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat generation failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat generation error: {str(e)}"
        )

@router.get("/sessions", response_model=List[ChatSession])
async def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Récupérer les sessions de chat de l'utilisateur
    
    Args:
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        Liste des sessions de chat
    """
    try:
        # Dans une implémentation réelle, on récupérerait les sessions depuis la base
        # Pour l'instant, retourner une liste vide ou mock
        return []
        
    except Exception as e:
        logger.error(f"Failed to get chat sessions for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chat sessions: {str(e)}"
        )

# ----------------------------------------------------------------------------
# AUDIO PROCESSING ENDPOINTS
# ----------------------------------------------------------------------------

@router.post("/audio/process", response_model=AudioProcessingResponse)
async def process_audio(
    background_tasks: BackgroundTasks,
    processing_request: AudioProcessingRequest,
    current_user: User = Depends(get_current_user),
    lm_arena_service: LMArenaIntegrationService = Depends(get_lm_arena_service),
    db: Session = Depends(get_db)
) -> Any:
    """
    Traiter un fichier audio avec le service harmonique
    
    Args:
        background_tasks: Tâches en arrière-plan
        processing_request: Requête de traitement audio
        current_user: Utilisateur authentifié
        lm_arena_service: Service d'intégration LM Arena
        db: Session de base de données
        
    Returns:
        Réponse de traitement audio
    """
    try:
        logger.info(f"Audio processing request from user {current_user.id}, mode: {processing_request.processing_mode}")
        
        # Vérifier les limites d'utilisation
        if not AudioService.check_usage_limit(db, current_user):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Monthly audio processing limit exceeded"
            )
        
        # Vérifier l'accès au mode demandé
        if not AudioService.check_mode_access(db, current_user, processing_request.processing_mode):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access to {processing_request.processing_mode} mode not allowed for your subscription"
            )
        
        # Créer un job audio
        audio_job = AudioJob(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            status=AudioJobStatus.PENDING,
            processing_mode=processing_request.processing_mode,
            target_profile=processing_request.target_profile,
            enhance_clarity=processing_request.enhance_clarity,
            spatial_enhancement=processing_request.spatial_enhancement,
            dynamic_range_boost=processing_request.dynamic_range_boost,
            vintage_restoration=processing_request.vintage_restoration,
            created_at=datetime.utcnow()
        )
        
        db.add(audio_job)
        db.commit()
        
        # Préparer la requête pour le service audio
        audio_request = AudioRequest(
            audio_data=processing_request.audio_data,
            audio_url=processing_request.audio_url,
            source_format=processing_request.source_format or "mp3_128",
            target_mode=processing_request.processing_mode.value,
            duration_seconds=processing_request.duration_seconds or 60.0,
            channels=processing_request.channels or 2,
            real_time=processing_request.real_time or False
        )
        
        # Lancer le traitement en arrière-plan
        background_tasks.add_task(
            process_audio_task,
            audio_job.id,
            current_user.id,
            audio_request
        )
        
        # Retourner la réponse
        response = AudioProcessingResponse(
            success=True,
            job_id=audio_job.id,
            status=audio_job.status.value,
            processing_mode=audio_job.processing_mode.value,
            estimated_processing_time=AudioService.estimate_processing_time(
                processing_request.processing_mode,
                processing_request.duration_seconds or 60.0
            ),
            user_id=current_user.id,
            timestamp=datetime.utcnow().isoformat()
        )
        
        logger.info(f"Audio processing job created: {audio_job.id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio processing request failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio processing request failed: {str(e)}"
        )

@router.get("/audio/jobs", response_model=List[AudioProcessingResponse])
async def get_audio_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Récupérer les jobs audio de l'utilisateur
    
    Args:
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        Liste des jobs audio
    """
    try:
        jobs = db.query(AudioJob).filter(
            AudioJob.user_id == current_user.id
        ).order_by(AudioJob.created_at.desc()).all()
        
        responses = []
        for job in jobs:
            response = AudioProcessingResponse(
                success=job.status == AudioJobStatus.COMPLETED,
                job_id=job.id,
                status=job.status.value,
                processing_mode=job.processing_mode.value,
                estimated_processing_time=job.estimated_processing_time,
                actual_processing_time=job.actual_processing_time,
                input_file_size=job.input_file_size,
                output_file_size=job.output_file_size,
                quality_improvement=job.quality_improvement,
                clarity_score=job.clarity_score,
                spatial_score=job.spatial_score,
                dynamic_range_score=job.dynamic_range_score,
                user_id=job.user_id,
                timestamp=job.created_at.isoformat() if job.created_at else None
            )
            responses.append(response)
        
        return responses
        
    except Exception as e:
        logger.error(f"Failed to get audio jobs for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audio jobs: {str(e)}"
        )

@router.get("/audio/jobs/{job_id}", response_model=AudioProcessingResponse)
async def get_audio_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Récupérer un job audio spécifique
    
    Args:
        job_id: ID du job
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        Détails du job audio
    """
    try:
        job = db.query(AudioJob).filter(
            AudioJob.id == job_id,
            AudioJob.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio job not found"
            )
        
        response = AudioProcessingResponse(
            success=job.status == AudioJobStatus.COMPLETED,
            job_id=job.id,
            status=job.status.value,
            processing_mode=job.processing_mode.value,
            estimated_processing_time=job.estimated_processing_time,
            actual_processing_time=job.actual_processing_time,
            input_file_size=job.input_file_size,
            output_file_size=job.output_file_size,
            quality_improvement=job.quality_improvement,
            clarity_score=job.clarity_score,
            spatial_score=job.spatial_score,
            dynamic_range_score=job.dynamic_range_score,
            user_id=job.user_id,
            timestamp=job.created_at.isoformat() if job.created_at else None
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audio job {job_id} for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audio job: {str(e)}"
        )

# ----------------------------------------------------------------------------
# VIDEO PROCESSING ENDPOINTS
# ----------------------------------------------------------------------------

@router.post("/video/process", response_model=VideoProcessingResponse)
async def process_video(
    background_tasks: BackgroundTasks,
    processing_request: VideoProcessingRequest,
    current_user: User = Depends(get_current_user),
    lm_arena_service: LMArenaIntegrationService = Depends(get_lm_arena_service),
    db: Session = Depends(get_db)
) -> Any:
    """
    Traiter un fichier vidéo avec le service harmonique
    
    Args:
        background_tasks: Tâches en arrière-plan
        processing_request: Requête de traitement vidéo
        current_user: Utilisateur authentifié
        lm_arena_service: Service d'intégration LM Arena
        db: Session de base de données
        
    Returns:
        Réponse de traitement vidéo
    """
    try:
        logger.info(f"Video processing request from user {current_user.id}, mode: {processing_request.processing_mode}")
        
        # Vérifier les limites d'utilisation
        if not VideoService.check_usage_limit(db, current_user):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Monthly video processing limit exceeded"
            )
        
        # Vérifier l'accès au mode demandé
        if not VideoService.check_mode_access(db, current_user, processing_request.processing_mode):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access to {processing_request.processing_mode} mode not allowed for your subscription"
            )
        
        # Créer un job vidéo
        video_job = VideoJob(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            status=VideoJobStatus.PENDING,
            processing_mode=processing_request.processing_mode,
            target_resolution=processing_request.target_resolution,
            enable_hdr=processing_request.enable_hdr,
            frame_interpolation=processing_request.frame_interpolation,
            noise_reduction=processing_request.noise_reduction,
            color_correction=processing_request.color_correction,
            created_at=datetime.utcnow()
        )
        
        db.add(video_job)
        db.commit()
        
        # Préparer la requête pour le service vidéo
        video_request = VideoRequest(
            video_data=processing_request.video_data,
            video_url=processing_request.video_url,
            source_format=processing_request.source_format or "h264_1080p",
            target_mode=processing_request.processing_mode.value,
            duration_seconds=processing_request.duration_seconds or 60.0,
            resolution=processing_request.target_resolution or "1920x1080",
            framerate=processing_request.framerate or 30,
            real_time=processing_request.real_time or False,
            user_id=current_user.id
        )
        
        # Lancer le traitement en arrière-plan
        background_tasks.add_task(
            process_video_task,
            video_job.id,
            current_user.id,
            video_request
        )
        
        # Retourner la réponse
        response = VideoProcessingResponse(
            success=True,
            job_id=video_job.id,
            status=video_job.status.value,
            processing_mode=video_job.processing_mode.value,
            estimated_processing_time=VideoService.estimate_processing_time(
                processing_request.processing_mode,
                processing_request.duration_seconds or 60.0,
                processing_request.target_resolution or "1920x1080"
            ),
            user_id=current_user.id,
            timestamp=datetime.utcnow().isoformat()
        )
        
        logger.info(f"Video processing job created: {video_job.id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video processing request failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video processing request failed: {str(e)}"
        )

@router.get("/video/jobs", response_model=List[VideoProcessingResponse])
async def get_video_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Récupérer les jobs vidéo de l'utilisateur
    
    Args:
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        Liste des jobs vidéo
    """
    try:
        jobs = db.query(VideoJob).filter(
            VideoJob.user_id == current_user.id
        ).order_by(VideoJob.created_at.desc()).all()
        
        responses = []
        for job in jobs:
            response = VideoProcessingResponse(
                success=job.status == VideoJobStatus.COMPLETED,
                job_id=job.id,
                status=job.status.value,
                processing_mode=job.processing_mode.value,
                estimated_processing_time=job.estimated_processing_time,
                actual_processing_time=job.actual_processing_time,
                input_file_size=job.input_file_size,
                output_file_size=job.output_file_size,
                quality_improvement=job.quality_improvement,
                resolution_improvement=job.resolution_improvement,
                framerate_improvement=job.framerate_improvement,
                hdr_improvement=job.hdr_improvement,
                noise_reduction_score=job.noise_reduction_score,
                color_accuracy_score=job.color_accuracy_score,
                user_id=job.user_id,
                timestamp=job.created_at.isoformat() if job.created_at else None
            )
            responses.append(response)
        
        return responses
        
    except Exception as e:
        logger.error(f"Failed to get video jobs for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get video jobs: {str(e)}"
        )

@router.get("/video/jobs/{job_id}", response_model=VideoProcessingResponse)
async def get_video_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Récupérer un job vidéo spécifique
    
    Args:
        job_id: ID du job
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        Détails du job vidéo
    """
    try:
        job = db.query(VideoJob).filter(
            VideoJob.id == job_id,
            VideoJob.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video job not found"
            )
        
        response = VideoProcessingResponse(
            success=job.status == VideoJobStatus.COMPLETED,
            job_id=job.id,
            status=job.status.value,
            processing_mode=job.processing_mode.value,
            estimated_processing_time=job.estimated_processing_time,
            actual_processing_time=job.actual_processing_time,
            input_file_size=job.input_file_size,
            output_file_size=job.output_file_size,
            quality_improvement=job.quality_improvement,
            resolution_improvement=job.resolution_improvement,
            framerate_improvement=job.framerate_improvement,
            hdr_improvement=job.hdr_improvement,
            noise_reduction_score=job.noise_reduction_score,
            color_accuracy_score=job.color_accuracy_score,
            user_id=job.user_id,
            timestamp=job.created_at.isoformat() if job.created_at else None
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video job {job_id} for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get video job: {str(e)}"
        )

# ----------------------------------------------------------------------------
# HEALTH CHECK ENDPOINTS
# ----------------------------------------------------------------------------

@router.get("/health")
async def lm_arena_health(
    lm_arena_service: LMArenaIntegrationService = Depends(get_lm_arena_service)
) -> Any:
    """
    Vérifier la santé des services LM Arena
    
    Args:
        lm_arena_service: Service d'intégration LM Arena
        
    Returns:
        Statut de santé des services
    """
    try:
        health_status = await lm_arena_service.check_health()
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )

@router.get("/status")
async def lm_arena_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Récupérer le statut des services LM Arena pour l'utilisateur
    
    Args:
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        Statut des services et métriques d'utilisation
    """
    try:
        # Récupérer les métriques d'utilisation
        usage_metrics = AudioService.get_usage_metrics(db, current_user)
        
        # Récupérer les jobs récents
        recent_audio_jobs = db.query(AudioJob).filter(
            AudioJob.user_id == current_user.id
        ).order_by(AudioJob.created_at.desc()).limit(5).all()
        
        recent_video_jobs = db.query(VideoJob).filter(
            VideoJob.user_id == current_user.id
        ).order_by(VideoJob.created_at.desc()).limit(5).all()
        
        # Formater la réponse
        status_response = {
            "user_id": current_user.id,
            "timestamp": datetime.utcnow().isoformat(),
            "usage_metrics": usage_metrics,
            "recent_audio_jobs": [
                {
                    "job_id": job.id,
                    "status": job.status.value,
                    "processing_mode": job.processing_mode.value,
                    "created_at": job.created_at.isoformat() if job.created_at else None
                }
                for job in recent_audio_jobs
            ],
            "recent_video_jobs": [
                {
                    "job_id": job.id,
                    "status": job.status.value,
                    "processing_mode": job.processing_mode.value,
                    "created_at": job.created_at.isoformat() if job.created_at else None
                }
                for job in recent_video_jobs
            ],
            "service_status": {
                "deepseek_api": "unknown",
                "audio_service": "unknown",
                "video_service": "unknown"
            }
        }
        
        return status_response
        
    except Exception as e:
        logger.error(f"Status check failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status check failed: {str(e)}"
        )
            target_mode=processing_request.processing_mode.value,
            duration_seconds=processing_request.duration_seconds or 60.0,
            channels=processing_request.channels or 2,
            real_time=processing_request.real_time or False
        )
        
        # Ajouter la tâche en arrière-plan
        background_tasks.add_task(
            process_audio_task,
            job_id=audio_job.id,
            user_id=current_user.id,
            audio_request=audio_request
        )
        
        # Créer la réponse
        response = AudioProcessingResponse(
            success=True,
            job_id=audio_job.id,
            status=audio_job.status.value,
            processing_mode=audio_job.processing_mode.value,
            estimated_processing_time=AudioService.estimate_processing_time(
                processing_request.processing_mode,
                processing_request.duration_seconds or 60.0
            ),
            message="Audio processing job created successfully"
        )
        
        logger.info(f"Audio processing job created for user {current_user.id}: {audio_job.id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio processing request failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio processing error: {str(e)}"
        )

@router.get("/audio/jobs/{job_id}", response_model=AudioProcessingResponse)
async def get_audio_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Récupérer le statut d'un job audio
    
    Args:
        job_id: ID du job audio
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        Statut du job audio
    """
    try:
        # Récupérer le job audio
        audio_job = db.query(AudioJob).filter(
            AudioJob.id == job_id,
            AudioJob.user_id == current_user.id
        ).first()
        
        if not audio_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio job not found"
            )
        
        # Créer la réponse
        response = AudioProcessingResponse(
            success=True,
            job_id=audio_job.id,
            status=audio_job.status.value,
            processing_mode=audio_job.processing_mode.value,
            quality_improvement=audio_job.quality_improvement,
            processing_time_ms=audio_job.processing_time_ms,
            result_url=audio_job.result_url,
            error_message=audio_job.error_message,
            created_at=audio_job.created_at.isoformat() if audio_job.created_at else None,
            completed_at=audio_job.completed_at.isoformat() if audio_job.completed_at else None
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audio job status {job_id} for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audio job status: {str(e)}"
        )

# ----------------------------------------------------------------------------
# VIDEO PROCESSING ENDPOINTS
# ----------------------------------------------------------------------------

@router.post("/video/process", response_model=VideoProcessingResponse)
async def process_video(
    background_tasks: BackgroundTasks,
    processing_request: VideoProcessingRequest,
    current_user: User = Depends(get_current_user),
    lm_arena_service: LMArenaIntegrationService = Depends(get_lm_arena_service),
    db: Session = Depends(get_db)
) -> Any:
    """
    Traiter un fichier vidéo avec le service harmonique
    
    Args:
        background_tasks: Tâches en arrière-plan
        processing_request: Requête de traitement vidéo
        current_user: Utilisateur authentifié
        lm_arena_service: Service d'intégration LM Arena
        db: Session de base de données
        
    Returns:
        Réponse de traitement vidéo
    """
    try:
        logger.info(f"Video processing request from user {current_user.id}, mode: {processing_request.processing_mode}")
        
        # Vérifier les limites d'utilisation
        if not VideoService.check_usage_limit(db, current_user):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Monthly video processing limit exceeded"
            )
        
        # Vérifier l'accès au mode demandé
        if not VideoService.check_mode_access(db, current_user, processing_request.processing_mode):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access to {processing_request.processing_mode} mode not allowed for your subscription"
            )
        
        # Vérifier l'accès entreprise pour certains modes
        if processing_request.processing_mode in [
            VideoProcessingMode.HCS_8K_MASTER,
            VideoProcessingMode.HCS_MOVIE_CONTINUOUS
        ]:
            if not VideoService.check_enterprise_access(db, current_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"{processing_request.processing_mode} mode requires Enterprise subscription"
                )
        
        # Créer un job vidéo
        video_job = VideoJob(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            status=VideoJobStatus.PENDING,
            processing_mode=processing_request.processing_mode,
            target_resolution=processing_request.target_resolution,
            enable_hdr=processing_request.enable_hdr,
            frame_interpolation=processing_request.frame_interpolation,
            continuous_generation=processing_request.continuous_generation,
            created_at=datetime.utcnow()
        )
        
        db.add(video_job)
        db.commit()
        
        # Préparer la requête pour le service vidéo
        video_request = VideoRequest(
            video_data=processing_request.video_data,
            video_url=processing_request.video_url,
            source_format=processing_request.source_format or "h264_1080p",
            target_mode=processing_request.processing_mode.value,
            duration_seconds=processing_request.duration_seconds or 60.0,
            resolution=processing_request.resolution or "1920x1080",
            framerate=processing_request.framerate or 30,
            real_time=processing_request.real_time or False,
            user_id=current_user.id
        )
        
        # Ajouter la tâche en arrière-plan
        background_tasks.add_task(
            process_video_task,
            job_id=video_job.id,
            user_id=current_user.id,
            video_request=video_request
        )
        
        # Créer la réponse
        response = VideoProcessingResponse(
            success=True,
            job_id=video_job.id,
            status=video_job.status.value,
            processing_mode=video_job.processing_mode.value,
            estimated_processing_time=VideoService.estimate_processing_time(
                processing_request.processing_mode,
                processing_request.duration_seconds or 60.0
            ),
            message="Video processing job created successfully"
        )
        
        logger.info(f"Video processing job created for user {current_user.id}: {video_job.id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video processing request failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video processing error: {str(e)}"
        )

@router.get("/video/jobs/{job_id}", response_model=VideoProcessingResponse)
async def get_video_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Récupérer le statut d'un job vidéo
    
    Args:
        job_id: ID du job vidéo
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        Statut du job vidéo
    """
    try:
        # Récupérer le job vidéo
        video_job = db.query(VideoJob).filter(
            VideoJob.id == job_id,
            VideoJob.user_id == current_user.id
        ).first()
        
        if not video_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video job not found"
            )
        
        # Créer la réponse
        response = VideoProcessingResponse(
            success=True,
            job_id=video_job.id,
            status=video_job.status.value,
            processing_mode=video_job.processing_mode.value,
            upscale_factor=video_job.upscale_factor,
            hdr_enabled=video_job.hdr_enabled,
            processing_time_ms=video_job.processing_time_ms,
            result_url=video_job.result_url,
            error_message=video_job.error_message,
            created_at=video_job.created_at.isoformat() if video_job.created_at else None,
            completed_at=video_job.completed_at.isoformat() if video_job.completed_at else None
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video job status {job_id} for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get video job status: {str(e)}"
        )

# ----------------------------------------------------------------------------
# HEALTH CHECK ENDPOINTS
# ----------------------------------------------------------------------------

@router.get("/health")
async def health_check(
    lm_arena_service: LMArenaIntegrationService = Depends(get_lm_arena_service)
) -> Any:
    """
    Vérifier la santé des services LM Arena
    
    Args:
        lm_arena_service: Service d'intégration LM Arena
        
    Returns:
        État de santé des services
    """
    try:
        health_status = await lm_arena_service.check_service_health()
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service health check failed: {str(e)}"
        )

# ----------------------------------------------------------------------------
# UTILITY ENDPOINTS
# ----------------------------------------------------------------------------

@router.get("/status")
async def service_status() -> Any:
    """
    Récupérer le statut du service
    
    Returns:
        Statut du service
    """
    return {
        "service": "Harmonic AI SaaS - LM Arena Integration",
        "version": settings.VERSION,
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "integrated_services": [
            "DeepSeek API AWS",
            "Harmonic Audio Service",
            "Harmonic Video Service"
        ]
    }