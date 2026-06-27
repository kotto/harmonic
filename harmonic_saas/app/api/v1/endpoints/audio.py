from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
import logging
import uuid
import os

from app.core import security
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.audio_job import AudioJob, AudioJobStatus
from app.schemas.audio import (
    AudioJob, AudioJobCreate, AudioJobUpdate, 
    AudioProcessingRequest, AudioProcessingResponse
)
from app.services.audio_service import AudioService
from app.services.storage_service import StorageService
from app.tasks.audio_tasks import process_audio_task

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/process", response_model=AudioProcessingResponse)
async def process_audio(
    background_tasks: BackgroundTasks,
    processing_request: AudioProcessingRequest,
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Process audio file with Harmonic AI technology
    """
    logger.info(f"Audio processing request from user: {current_user.email}")
    
    # Check user subscription limits
    if not AudioService.check_usage_limit(db, current_user):
        logger.warning(f"Usage limit exceeded for user: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Monthly usage limit exceeded. Please upgrade your subscription."
        )
    
    # Create audio job record
    audio_job = AudioJob(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        job_name=processing_request.processing_mode.value,
        processing_mode=processing_request.processing_mode,
        status=AudioJobStatus.PENDING,
        created_at=security.datetime.utcnow()
    )
    
    db.add(audio_job)
    db.commit()
    db.refresh(audio_job)
    
    logger.info(f"Audio job created: {audio_job.id}")
    
    # Return immediate response
    return AudioProcessingResponse(
        job_id=audio_job.id,
        status=AudioJobStatus.PENDING,
        message="Audio processing job created. Processing will start shortly."
    )

@router.post("/upload", response_model=dict)
async def upload_audio(
    file: UploadFile = File(...),
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Upload audio file for processing
    """
    logger.info(f"Audio upload request from user: {current_user.email}")
    
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_AUDIO_EXTENSIONS:
        logger.warning(f"Invalid audio file extension: {file_ext}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_AUDIO_EXTENSIONS)}"
        )
    
    # Validate file size
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    content = await file.read()
    
    if len(content) > max_size:
        logger.warning(f"Audio file too large: {len(content)} bytes")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB"
        )
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    
    # Upload to storage
    upload_url = StorageService.upload_audio_file(
        content=content,
        filename=unique_filename,
        user_id=current_user.id
    )
    
    logger.info(f"Audio file uploaded: {unique_filename}")
    
    return {
        "upload_id": str(uuid.uuid4()),
        "filename": unique_filename,
        "original_filename": file.filename,
        "filesize_bytes": len(content),
        "upload_url": upload_url,
        "message": "Audio file uploaded successfully"
    }

@router.get("/jobs", response_model=List[AudioJob])
async def list_audio_jobs(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List user's audio processing jobs
    """
    logger.info(f"List audio jobs request from user: {current_user.email}")
    
    jobs = db.query(AudioJob).filter(
        AudioJob.user_id == current_user.id
    ).order_by(
        AudioJob.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return jobs

@router.get("/jobs/{job_id}", response_model=AudioJob)
async def get_audio_job(
    job_id: str,
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get audio job details
    """
    logger.info(f"Get audio job request: {job_id}")
    
    audio_job = db.query(AudioJob).filter(
        AudioJob.id == job_id,
        AudioJob.user_id == current_user.id
    ).first()
    
    if not audio_job:
        logger.warning(f"Audio job not found: {job_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio job not found"
        )
    
    return audio_job

@router.delete("/jobs/{job_id}")
async def delete_audio_job(
    job_id: str,
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete audio job
    """
    logger.info(f"Delete audio job request: {job_id}")
    
    audio_job = db.query(AudioJob).filter(
        AudioJob.id == job_id,
        AudioJob.user_id == current_user.id
    ).first()
    
    if not audio_job:
        logger.warning(f"Audio job not found: {job_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio job not found"
        )
    
    # Delete from storage if exists
    if audio_job.output_filepath:
        StorageService.delete_file(audio_job.output_filepath)
    
    if audio_job.input_filepath:
        StorageService.delete_file(audio_job.input_filepath)
    
    # Delete from database
    db.delete(audio_job)
    db.commit()
    
    logger.info(f"Audio job deleted: {job_id}")
    
    return {
        "message": "Audio job deleted successfully"
    }

@router.get("/status/{job_id}")
async def get_audio_job_status(
    job_id: str,
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get audio job status
    """
    logger.info(f"Get audio job status request: {job_id}")
    
    audio_job = db.query(AudioJob).filter(
        AudioJob.id == job_id,
        AudioJob.user_id == current_user.id
    ).first()
    
    if not audio_job:
        logger.warning(f"Audio job not found: {job_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio job not found"
        )
    
    return {
        "job_id": audio_job.id,
        "status": audio_job.status.value,
        "processing_mode": audio_job.processing_mode.value,
        "created_at": audio_job.created_at,
        "updated_at": audio_job.updated_at,
        "completed_at": audio_job.completed_at,
        "error_message": audio_job.error_message
    }

@router.post("/jobs/{job_id}/retry")
async def retry_audio_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retry failed audio job
    """
    logger.info(f"Retry audio job request: {job_id}")
    
    audio_job = db.query(AudioJob).filter(
        AudioJob.id == job_id,
        AudioJob.user_id == current_user.id
    ).first()
    
    if not audio_job:
        logger.warning(f"Audio job not found: {job_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio job not found"
        )
    
    if audio_job.status != AudioJobStatus.FAILED:
        logger.warning(f"Cannot retry job with status: {audio_job.status}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only failed jobs can be retried"
        )
    
    # Reset job status
    audio_job.status = AudioJobStatus.PENDING
    audio_job.error_message = None
    audio_job.retry_count += 1
    
    db.commit()
    
    # Queue for processing
    background_tasks.add_task(
        process_audio_task,
        job_id=audio_job.id,
        user_id=current_user.id
    )
    
    logger.info(f"Audio job queued for retry: {job_id}")
    
    return {
        "message": "Audio job queued for retry",
        "job_id": job_id,
        "retry_count": audio_job.retry_count
    }