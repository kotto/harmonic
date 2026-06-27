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
from app.models.video_job import VideoJob, VideoJobStatus
from app.schemas.video import (
    VideoJob, VideoJobCreate, VideoJobUpdate,
    VideoProcessingRequest, VideoProcessingResponse
)
from app.services.video_service import VideoService
from app.services.storage_service import StorageService
from app.tasks.video_tasks import process_video_task

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/process", response_model=VideoProcessingResponse)
async def process_video(
    background_tasks: BackgroundTasks,
    processing_request: VideoProcessingRequest,
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Process video file with Harmonic AI technology
    """
    logger.info(f"Video processing request from user: {current_user.email}")
    
    # Check user subscription limits
    if not VideoService.check_usage_limit(db, current_user):
        logger.warning(f"Usage limit exceeded for user: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Monthly usage limit exceeded. Please upgrade your subscription."
        )
    
    # Create video job record
    video_job = VideoJob(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        job_name=processing_request.processing_mode.value,
        processing_mode=processing_request.processing_mode,
        status=VideoJobStatus.PENDING,
        created_at=security.datetime.utcnow()
    )
    
    db.add(video_job)
    db.commit()
    db.refresh(video_job)
    
    logger.info(f"Video job created: {video_job.id}")
    
    # Return immediate response
    return VideoProcessingResponse(
        job_id=video_job.id,
        status=VideoJobStatus.PENDING,
        message="Video processing job created. Processing will start shortly."
    )

@router.post("/upload", response_model=dict)
async def upload_video(
    file: UploadFile = File(...),
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Upload video file for processing
    """
    logger.info(f"Video upload request from user: {current_user.email}")
    
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_VIDEO_EXTENSIONS:
        logger.warning(f"Invalid video file extension: {file_ext}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_VIDEO_EXTENSIONS)}"
        )
    
    # Validate file size
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    content = await file.read()
    
    if len(content) > max_size:
        logger.warning(f"Video file too large: {len(content)} bytes")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB"
        )
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    
    # Upload to storage
    upload_url = StorageService.upload_video_file(
        content=content,
        filename=unique_filename,
        user_id=current_user.id
    )
    
    logger.info(f"Video file uploaded: {unique_filename}")
    
    return {
        "upload_id": str(uuid.uuid4()),
        "filename": unique_filename,
        "original_filename": file.filename,
        "filesize_bytes": len(content),
        "upload_url": upload_url,
        "message": "Video file uploaded successfully"
    }

@router.get("/jobs", response_model=List[VideoJob])
async def list_video_jobs(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List user's video processing jobs
    """
    logger.info(f"List video jobs request from user: {current_user.email}")
    
    jobs = db.query(VideoJob).filter(
        VideoJob.user_id == current_user.id
    ).order_by(
        VideoJob.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return jobs

@router.get("/jobs/{job_id}", response_model=VideoJob)
async def get_video_job(
    job_id: str,
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get video job details
    """
    logger.info(f"Get video job request: {job_id}")
    
    video_job = db.query(VideoJob).filter(
        VideoJob.id == job_id,
        VideoJob.user_id == current_user.id
    ).first()
    
    if not video_job:
        logger.warning(f"Video job not found: {job_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video job not found"
        )
    
    return video_job

@router.delete("/jobs/{job_id}")
async def delete_video_job(
    job_id: str,
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete video job
    """
    logger.info(f"Delete video job request: {job_id}")
    
    video_job = db.query(VideoJob).filter(
        VideoJob.id == job_id,
        VideoJob.user_id == current_user.id
    ).first()
    
    if not video_job:
        logger.warning(f"Video job not found: {job_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video job not found"
        )
    
    # Delete from storage if exists
    if video_job.output_filepath:
        StorageService.delete_file(video_job.output_filepath)
    
    if video_job.input_filepath:
        StorageService.delete_file(video_job.input_filepath)
    
    # Delete from database
    db.delete(video_job)
    db.commit()
    
    logger.info(f"Video job deleted: {job_id}")
    
    return {
        "message": "Video job deleted successfully"
    }

@router.get("/status/{job_id}")
async def get_video_job_status(
    job_id: str,
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get video job status
    """
    logger.info(f"Get video job status request: {job_id}")
    
    video_job = db.query(VideoJob).filter(
        VideoJob.id == job_id,
        VideoJob.user_id == current_user.id
    ).first()
    
    if not video_job:
        logger.warning(f"Video job not found: {job_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video job not found"
        )
    
    return {
        "job_id": video_job.id,
        "status": video_job.status.value,
        "processing_mode": video_job.processing_mode.value,
        "created_at": video_job.created_at,
        "updated_at": video_job.updated_at,
        "completed_at": video_job.completed_at,
        "error_message": video_job.error_message
    }

@router.post("/jobs/{job_id}/retry")
async def retry_video_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retry failed video job
    """
    logger.info(f"Retry video job request: {job_id}")
    
    video_job = db.query(VideoJob).filter(
        VideoJob.id == job_id,
        VideoJob.user_id == current_user.id
    ).first()
    
    if not video_job:
        logger.warning(f"Video job not found: {job_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video job not found"
        )
    
    if video_job.status != VideoJobStatus.FAILED:
        logger.warning(f"Cannot retry job with status: {video_job.status}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only failed jobs can be retried"
        )
    
    # Reset job status
    video_job.status = VideoJobStatus.PENDING
    video_job.error_message = None
    video_job.retry_count += 1
    
    db.commit()
    
    # Queue for processing
    background_tasks.add_task(
        process_video_task,
        job_id=video_job.id,
        user_id=current_user.id
    )
    
    logger.info(f"Video job queued for retry: {job_id}")
    
    return {
        "message": "Video job queued for retry",
        "job_id": job_id,
        "retry_count": video_job.retry_count
    }

@router.post("/generate-movie")
async def generate_continuous_movie(
    processing_request: VideoProcessingRequest,
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Generate continuous movie with Harmonic AI technology
    """
    logger.info(f"Continuous movie generation request from user: {current_user.email}")
    
    # Check if user has enterprise subscription
    if not VideoService.check_enterprise_access(db, current_user):
        logger.warning(f"Enterprise access required for user: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Continuous movie generation requires Enterprise subscription"
        )
    
    # Create video job for movie generation
    video_job = VideoJob(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        job_name="Continuous Movie Generation",
        processing_mode=VideoProcessingMode.HCS_MOVIE_CONTINUOUS,
        status=VideoJobStatus.PENDING,
        created_at=security.datetime.utcnow()
    )
    
    db.add(video_job)
    db.commit()
    db.refresh(video_job)
    
    logger.info(f"Continuous movie job created: {video_job.id}")
    
    return {
        "job_id": video_job.id,
        "status": VideoJobStatus.PENDING.value,
        "message": "Continuous movie generation job created. Processing will start shortly.",
        "estimated_duration": "Variable (up to unlimited)",
        "output_format": "MP4 H.265",
        "resolution": "4K/8K based on input"
    }