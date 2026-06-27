#!/usr/bin/env python3
"""
Chat Endpoints - LM Arena Integration
======================================
Endpoints pour l'intégration avec les services LM Arena
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
    """Générer une réponse de chat avec intégration LM Arena"""
    try:
        logger.info(f"Chat generation request from user {current_user.id}: {request.prompt[:100]}...")
        
        response = await lm_arena_service.generate_lm_arena_response(
            prompt=request.prompt,
            user_id=current_user.id
        )
        
        AudioService.update_usage_metrics(db, current_user, "chat", 1)
        
        return ChatResponse(
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat generation error: {str(e)}")

@router.get("/sessions", response_model=List[ChatSession])
async def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Récupérer les sessions de chat de l'utilisateur"""
    return []

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
    """Traiter un fichier audio avec le service harmonique"""
    try:
        logger.info(f"Audio processing request from user {current_user.id}, mode: {processing_request.processing_mode}")
        
        if not AudioService.check_usage_limit(db, current_user):
            raise HTTPException(status_code=429, detail="Monthly audio processing limit exceeded")
        
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
        
        audio_request = AudioRequest(
            audio_data=processing_request.audio_data,
            audio_url=processing_request.audio_url,
            source_format=processing_request.source_format or "mp3_128",
            target_mode=processing_request.processing_mode.value,
            duration_seconds=processing_request.duration_seconds or 60.0,
            channels=processing_request.channels or 2,
            real_time=processing_request.real_time or False
        )
        
        background_tasks.add_task(process_audio_task, audio_job.id, current_user.id, audio_request)
        
        return AudioProcessingResponse(
            success=True,
            job_id=audio_job.id,
            status=audio_job.status.value,
            processing_mode=audio_job.processing_mode.value,
            estimated_processing_time=AudioService.estimate_processing_time(
                processing_request.processing_mode, processing_request.duration_seconds or 60.0
            ),
            user_id=current_user.id,
            timestamp=datetime.utcnow().isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Audio processing error: {str(e)}")

@router.get("/audio/jobs", response_model=List[AudioProcessingResponse])
async def get_audio_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Récupérer les jobs audio de l'utilisateur"""
    try:
        jobs = db.query(AudioJob).filter(AudioJob.user_id == current_user.id).order_by(AudioJob.created_at.desc()).all()
        responses = []
        for job in jobs:
            responses.append(AudioProcessingResponse(
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
            ))
        return responses
    except Exception as e:
        logger.error(f"Failed to get audio jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get audio jobs: {str(e)}")

@router.get("/audio/jobs/{job_id}", response_model=AudioProcessingResponse)
async def get_audio_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Récupérer un job audio spécifique"""
    try:
        job = db.query(AudioJob).filter(AudioJob.id == job_id, AudioJob.user_id == current_user.id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Audio job not found")
        return AudioProcessingResponse(
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audio job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get audio job: {str(e)}")

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
    """Traiter un fichier vidéo avec le service harmonique"""
    try:
        logger.info(f"Video processing request from user {current_user.id}, mode: {processing_request.processing_mode}")
        
        if not VideoService.check_usage_limit(db, current_user):
            raise HTTPException(status_code=429, detail="Monthly video processing limit exceeded")
        
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
        
        background_tasks.add_task(process_video_task, video_job.id, current_user.id, video_request)
        
        return VideoProcessingResponse(
            success=True,
            job_id=video_job.id,
            status=video_job.status.value,
            processing_mode=video_job.processing_mode.value,
            estimated_processing_time=VideoService.estimate_processing_time(
                processing_request.processing_mode, processing_request.duration_seconds or 60.0,
                processing_request.target_resolution or "1920x1080"
            ),
            user_id=current_user.id,
            timestamp=datetime.utcnow().isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Video processing error: {str(e)}")

@router.get("/video/jobs", response_model=List[VideoProcessingResponse])
async def get_video_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Récupérer les jobs vidéo de l'utilisateur"""
    try:
        jobs = db.query(VideoJob).filter(VideoJob.user_id == current_user.id).order_by(VideoJob.created_at.desc()).all()
        responses = []
        for job in jobs:
            responses.append(VideoProcessingResponse(
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
            ))
        return responses
    except Exception as e:
        logger.error(f"Failed to get video jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get video jobs: {str(e)}")

@router.get("/video/jobs/{job_id}", response_model=VideoProcessingResponse)
async def get_video_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Récupérer un job vidéo spécifique"""
    try:
        job = db.query(VideoJob).filter(VideoJob.id == job_id, VideoJob.user_id == current_user.id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Video job not found")
        return VideoProcessingResponse(
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get video job: {str(e)}")

# ----------------------------------------------------------------------------
# HEALTH & STATUS ENDPOINTS
# ----------------------------------------------------------------------------

@router.get("/health")
async def health_check(
    lm_arena_service: LMArenaIntegrationService = Depends(get_lm_arena_service)
) -> Any:
    """Vérifier la santé des services LM Arena"""
    try:
        return await lm_arena_service.check_health()
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

@router.get("/status")
async def service_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Récupérer le statut des services pour l'utilisateur"""
    try:
        usage_metrics = AudioService.get_usage_metrics(db, current_user)
        recent_audio_jobs = db.query(AudioJob).filter(
            AudioJob.user_id == current_user.id
        ).order_by(AudioJob.created_at.desc()).limit(5).all()
        recent_video_jobs = db.query(VideoJob).filter(
            VideoJob.user_id == current_user.id
        ).order_by(VideoJob.created_at.desc()).limit(5).all()
        
        return {
            "user_id": current_user.id,
            "timestamp": datetime.utcnow().isoformat(),
            "usage_metrics": usage_metrics,
            "recent_audio_jobs": [
                {"job_id": j.id, "status": j.status.value, "processing_mode": j.processing_mode.value,
                 "created_at": j.created_at.isoformat() if j.created_at else None}
                for j in recent_audio_jobs
            ],
            "recent_video_jobs": [
                {"job_id": j.id, "status": j.status.value, "processing_mode": j.processing_mode.value,
                 "created_at": j.created_at.isoformat() if j.created_at else None}
                for j in recent_video_jobs
            ],
            "service_status": {
                "deepseek_api": "unknown",
                "audio_service": "unknown",
                "video_service": "unknown"
            }
        }
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")
