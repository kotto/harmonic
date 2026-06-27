import logging
from celery import shared_task
from sqlalchemy.orm import Session
from datetime import datetime
import httpx
import uuid

from app.core.database import get_db
from app.core.config import settings
from app.models.audio_job import AudioJob, AudioJobStatus
from app.services.audio_service import AudioService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_audio_task(self, job_id: str, user_id: str):
    """
    Process audio file asynchronously
    """
    logger.info(f"Starting audio processing task for job: {job_id}")
    
    db: Session = next(get_db())
    
    try:
        # Get audio job
        audio_job = db.query(AudioJob).filter(AudioJob.id == job_id).first()
        
        if not audio_job:
            logger.error(f"Audio job not found: {job_id}")
            return {"status": "error", "message": "Job not found"}
        
        # Update job status to processing
        audio_job.status = AudioJobStatus.PROCESSING
        audio_job.started_at = datetime.utcnow()
        db.commit()
        
        # Download input file from storage
        input_content = StorageService.download_file(audio_job.input_filepath)
        
        # Prepare processing request
        from app.schemas.audio import AudioProcessingRequest
        audio_request = AudioProcessingRequest(
            processing_mode=audio_job.processing_mode
        )
        
        # Process audio
        result = AudioService.process_audio(
            audio_request=audio_request,
            input_file_content=input_content
        )
        
        if not result["success"]:
            # Update job status to failed
            audio_job.status = AudioJobStatus.FAILED
            audio_job.error_message = result["error"]
            audio_job.completed_at = datetime.utcnow()
            db.commit()
            
            logger.error(f"Audio processing failed for job {job_id}: {result['error']}")
            
            return {
                "status": "error",
                "job_id": job_id,
                "error": result["error"]
            }
        
        # Extract result data
        result_data = result["result"]
        
        # Upload processed file to storage
        output_filename = f"processed_{uuid.uuid4()}.wav"
        output_url = StorageService.upload_audio_file(
            content=bytes.fromhex(result_data.get("output_content", "")),
            filename=output_filename,
            user_id=user_id
        )
        
        # Update job with results
        audio_job.status = AudioJobStatus.COMPLETED
        audio_job.output_filename = output_filename
        audio_job.output_filepath = f"audio/{datetime.now().strftime('%Y/%m/%d')}/{user_id}/{output_filename}"
        audio_job.output_filesize_bytes = len(bytes.fromhex(result_data.get("output_content", "")))
        audio_job.processing_time_ms = result_data.get("processing_time_ms", 0)
        audio_job.quality_improvement = result_data.get("quality_improvement", 0)
        
        # Audio-specific metrics
        audio_job.input_sample_rate_hz = result_data.get("input_sample_rate_hz", 44100)
        audio_job.output_sample_rate_hz = result_data.get("output_sample_rate_hz", 44100)
        audio_job.input_bit_depth = result_data.get("input_bit_depth", 16)
        audio_job.output_bit_depth = result_data.get("output_bit_depth", 24)
        audio_job.input_channels = result_data.get("input_channels", 2)
        audio_job.output_channels = result_data.get("output_channels", 2)
        audio_job.noise_reduction_db = result_data.get("noise_reduction_db", 0)
        audio_job.dynamic_range_db = result_data.get("dynamic_range_db", 0)
        audio_job.spatial_channels_added = result_data.get("spatial_channels_added", 0)
        
        audio_job.completed_at = datetime.utcnow()
        audio_job.service_response = result_data
        
        db.commit()
        
        # Increment user usage
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            AudioService.increment_usage(db, user)
        
        logger.info(f"Audio processing completed successfully for job: {job_id}")
        
        return {
            "status": "success",
            "job_id": job_id,
            "output_url": output_url,
            "processing_time_ms": audio_job.processing_time_ms,
            "quality_improvement": audio_job.quality_improvement
        }
        
    except httpx.TimeoutException as e:
        logger.error(f"Audio processing timeout for job {job_id}: {str(e)}")
        
        # Update job status
        audio_job = db.query(AudioJob).filter(AudioJob.id == job_id).first()
        if audio_job:
            audio_job.status = AudioJobStatus.FAILED
            audio_job.error_message = f"Timeout: {str(e)}"
            audio_job.completed_at = datetime.utcnow()
            db.commit()
        
        # Retry the task
        raise self.retry(exc=e)
        
    except Exception as e:
        logger.error(f"Audio processing error for job {job_id}: {str(e)}")
        
        # Update job status
        audio_job = db.query(AudioJob).filter(AudioJob.id == job_id).first()
        if audio_job:
            audio_job.status = AudioJobStatus.FAILED
            audio_job.error_message = str(e)
            audio_job.completed_at = datetime.utcnow()
            db.commit()
        
        # Retry the task
        raise self.retry(exc=e)

@shared_task
def check_audio_job_status(job_id: str):
    """
    Check status of audio processing job
    """
    logger.debug(f"Checking status for audio job: {job_id}")
    
    db: Session = next(get_db())
    
    audio_job = db.query(AudioJob).filter(AudioJob.id == job_id).first()
    
    if not audio_job:
        return {"status": "not_found"}
    
    return {
        "job_id": job_id,
        "status": audio_job.status.value,
        "processing_mode": audio_job.processing_mode.value,
        "created_at": audio_job.created_at.isoformat() if audio_job.created_at else None,
        "started_at": audio_job.started_at.isoformat() if audio_job.started_at else None,
        "completed_at": audio_job.completed_at.isoformat() if audio_job.completed_at else None,
        "error_message": audio_job.error_message
    }

@shared_task
def cleanup_audio_jobs(days_old: int = 7):
    """
    Cleanup old audio jobs
    """
    logger.info(f"Cleaning up audio jobs older than {days_old} days")
    
    db: Session = next(get_db())
    
    from datetime import datetime, timedelta
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    
    # Find old jobs
    old_jobs = db.query(AudioJob).filter(
        AudioJob.created_at < cutoff_date
    ).all()
    
    deleted_count = 0
    
    for job in old_jobs:
        try:
            # Delete associated files from storage
            if job.output_filepath:
                StorageService.delete_file(job.output_filepath)
            
            if job.input_filepath:
                StorageService.delete_file(job.input_filepath)
            
            # Delete from database
            db.delete(job)
            deleted_count += 1
            
        except Exception as e:
            logger.error(f"Failed to delete audio job {job.id}: {str(e)}")
    
    db.commit()
    
    logger.info(f"Cleaned up {deleted_count} old audio jobs")
    
    return {
        "deleted_count": deleted_count,
        "days_old": days_old
    }

@shared_task
def batch_process_audio(job_ids: list[str]):
    """
    Process multiple audio jobs in batch
    """
    logger.info(f"Batch processing {len(job_ids)} audio jobs")
    
    results = []
    
    for job_id in job_ids:
        try:
            # Get user ID from job
            db: Session = next(get_db())
            audio_job = db.query(AudioJob).filter(AudioJob.id == job_id).first()
            
            if audio_job:
                # Process each job
                result = process_audio_task.delay(job_id, audio_job.user_id)
                results.append({
                    "job_id": job_id,
                    "task_id": result.id,
                    "status": "queued"
                })
            else:
                results.append({
                    "job_id": job_id,
                    "error": "Job not found"
                })
                
        except Exception as e:
            results.append({
                "job_id": job_id,
                "error": str(e)
            })
    
    return {
        "total_jobs": len(job_ids),
        "queued_jobs": len([r for r in results if "task_id" in r]),
        "failed_jobs": len([r for r in results if "error" in r]),
        "results": results
    }