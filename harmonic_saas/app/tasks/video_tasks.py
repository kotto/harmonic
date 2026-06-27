#!/usr/bin/env python3
"""
Video Tasks - Celery Tasks for Video Processing
================================================
Tâches Celery asynchrones pour le traitement vidéo harmonique
"""

import os
import sys
import json
import time
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

from celery import shared_task
from sqlalchemy.orm import Session
import httpx

from app.core.database import SessionLocal
from app.models.video_job import VideoJob, VideoJobStatus
from app.services.lm_arena_integration import VideoProcessingRequest as VideoRequest
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# VIDEO PROCESSING TASK
# ----------------------------------------------------------------------------

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_video_task(self, job_id: str, user_id: str, video_request: Dict[str, Any]):
    """
    Tâche Celery pour traiter un fichier vidéo
    
    Args:
        job_id: ID du job vidéo
        user_id: ID de l'utilisateur
        video_request: Requête de traitement vidéo
    """
    db: Session = SessionLocal()
    
    try:
        logger.info(f"Starting video processing task for job {job_id}, user {user_id}")
        
        # Récupérer le job vidéo
        video_job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
        
        if not video_job:
            logger.error(f"Video job {job_id} not found")
            return
        
        # Mettre à jour le statut
        video_job.status = VideoJobStatus.PROCESSING
        video_job.started_at = datetime.utcnow()
        db.commit()
        
        # Convertir la requête
        video_req = VideoRequest(**video_request)
        
        # Appeler le service vidéo
        result = asyncio.run(_call_video_service(video_req, user_id))
        
        if result.get("success"):
            # Traitement réussi
            video_job.status = VideoJobStatus.COMPLETED
            video_job.completed_at = datetime.utcnow()
            video_job.processing_time_ms = result.get("processing_time_ms", 0)
            video_job.upscale_factor = result.get("upscale_factor", 1.0)
            video_job.hdr_enabled = result.get("hdr_enabled", False)
            video_job.result_url = result.get("result_url")
            video_job.quality_score = result.get("quality_score", 0.0)
            video_job.metadata = json.dumps(result.get("metadata", {}))
            
            logger.info(f"Video processing completed for job {job_id}")
            
        else:
            # Traitement échoué
            video_job.status = VideoJobStatus.FAILED
            video_job.completed_at = datetime.utcnow()
            video_job.error_message = result.get("error_message", "Unknown error")
            
            logger.error(f"Video processing failed for job {job_id}: {video_job.error_message}")
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Video processing task failed for job {job_id}: {str(e)}")
        
        # Mettre à jour le statut en cas d'erreur
        try:
            video_job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
            if video_job:
                video_job.status = VideoJobStatus.FAILED
                video_job.completed_at = datetime.utcnow()
                video_job.error_message = f"Task error: {str(e)}"
                db.commit()
        except Exception as update_error:
            logger.error(f"Failed to update job status: {str(update_error)}")
        
        # Relancer la tâche si nécessaire
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        
    finally:
        db.close()

# ----------------------------------------------------------------------------
# VIDEO SERVICE CALL
# ----------------------------------------------------------------------------

async def _call_video_service(video_request: VideoRequest, user_id: str) -> Dict[str, Any]:
    """
    Appeler le service vidéo harmonique
    
    Args:
        video_request: Requête de traitement vidéo
        user_id: ID de l'utilisateur
        
    Returns:
        Résultat du traitement
    """
    try:
        # Configuration du service
        video_service_url = os.getenv("VIDEO_SERVICE_URL", "http://localhost:9018")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Préparer la requête
            payload = {
                "video_url": video_request.video_url,
                "source_format": video_request.source_format,
                "target_mode": video_request.target_mode,
                "duration_seconds": video_request.duration_seconds,
                "resolution": video_request.resolution,
                "framerate": video_request.framerate,
                "real_time": video_request.real_time,
                "user_id": user_id
            }
            
            # Envoyer la requête
            start_time = time.time()
            
            if video_request.video_data:
                # Envoyer comme fichier
                files = {"video_file": ("video.mp4", video_request.video_data, "video/mp4")}
                response = await client.post(
                    f"{video_service_url}/process",
                    data=payload,
                    files=files
                )
            else:
                # Envoyer comme JSON
                response = await client.post(
                    f"{video_service_url}/process",
                    json=payload
                )
            
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                # Ajouter les métriques
                result["processing_time_ms"] = elapsed_time * 1000
                result["user_id"] = user_id
                result["timestamp"] = datetime.utcnow().isoformat()
                
                # Sauvegarder le résultat si disponible
                if result.get("enhanced_video_url"):
                    # Télécharger et sauvegarder le résultat
                    try:
                        enhanced_content = await client.get(result["enhanced_video_url"])
                        if enhanced_content.status_code == 200:
                            # Sauvegarder dans le stockage
                            filename = f"enhanced_video_{uuid.uuid4().hex[:8]}.mp4"
                            result_url = StorageService.upload_video_file(
                                enhanced_content.content,
                                filename,
                                user_id
                            )
                            result["result_url"] = result_url
                    except Exception as download_error:
                        logger.warning(f"Failed to download enhanced video: {str(download_error)}")
                
                return result
                
            else:
                return {
                    "success": False,
                    "error_message": f"Video service error: {response.status_code}",
                    "processing_time_ms": elapsed_time * 1000
                }
                
    except httpx.TimeoutException:
        return {
            "success": False,
            "error_message": "Video service timeout",
            "processing_time_ms": 0
        }
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Video service error: {str(e)}",
            "processing_time_ms": 0
        }

# ----------------------------------------------------------------------------
# BATCH PROCESSING TASK
# ----------------------------------------------------------------------------

@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def batch_process_videos_task(self, job_ids: list, user_id: str):
    """
    Tâche Celery pour traiter plusieurs fichiers vidéo en batch
    
    Args:
        job_ids: Liste des IDs de jobs vidéo
        user_id: ID de l'utilisateur
    """
    logger.info(f"Starting batch video processing for {len(job_ids)} jobs, user {user_id}")
    
    results = []
    
    for job_id in job_ids:
        try:
            # Exécuter chaque job individuellement
            result = process_video_task.apply_async(args=[job_id, user_id, {}])
            results.append({
                "job_id": job_id,
                "task_id": result.id,
                "status": "started"
            })
            
        except Exception as e:
            logger.error(f"Failed to start video job {job_id}: {str(e)}")
            results.append({
                "job_id": job_id,
                "error": str(e),
                "status": "failed"
            })
    
    return {
        "success": True,
        "total_jobs": len(job_ids),
        "started_jobs": len([r for r in results if r.get("status") == "started"]),
        "failed_jobs": len([r for r in results if r.get("status") == "failed"]),
        "results": results
    }

# ----------------------------------------------------------------------------
# CLEANUP TASK
# ----------------------------------------------------------------------------

@shared_task
def cleanup_old_video_jobs_task(days_old: int = 30):
    """
    Nettoyer les vieux jobs vidéo
    
    Args:
        days_old: Nombre de jours avant suppression
    """
    db: Session = SessionLocal()
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Récupérer les vieux jobs
        old_jobs = db.query(VideoJob).filter(
            VideoJob.created_at < cutoff_date,
            VideoJob.status.in_([VideoJobStatus.COMPLETED, VideoJobStatus.FAILED])
        ).all()
        
        deleted_count = 0
        
        for job in old_jobs:
            try:
                # Supprimer les fichiers associés si nécessaire
                if job.result_url:
                    StorageService.delete_file(job.result_url)
                
                db.delete(job)
                deleted_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to delete video job {job.id}: {str(e)}")
        
        db.commit()
        
        logger.info(f"Cleaned up {deleted_count} old video jobs (older than {days_old} days)")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Video jobs cleanup failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
        
    finally:
        db.close()

# ----------------------------------------------------------------------------
# MONITORING TASK
# ----------------------------------------------------------------------------

@shared_task
def monitor_video_processing_health_task():
    """
    Surveiller la santé du traitement vidéo
    """
    db: Session = SessionLocal()
    
    try:
        # Récupérer les statistiques
        total_jobs = db.query(VideoJob).count()
        pending_jobs = db.query(VideoJob).filter(VideoJob.status == VideoJobStatus.PENDING).count()
        processing_jobs = db.query(VideoJob).filter(VideoJob.status == VideoJobStatus.PROCESSING).count()
        completed_jobs = db.query(VideoJob).filter(VideoJob.status == VideoJobStatus.COMPLETED).count()
        failed_jobs = db.query(VideoJob).filter(VideoJob.status == VideoJobStatus.FAILED).count()
        
        # Calculer les taux
        success_rate = completed_jobs / total_jobs if total_jobs > 0 else 0
        failure_rate = failed_jobs / total_jobs if total_jobs > 0 else 0
        
        # Récupérer les jobs en échec récents
        recent_failures = db.query(VideoJob).filter(
            VideoJob.status == VideoJobStatus.FAILED,
            VideoJob.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).limit(10).all()
        
        failure_details = [
            {
                "job_id": job.id,
                "error_message": job.error_message,
                "created_at": job.created_at.isoformat() if job.created_at else None
            }
            for job in recent_failures
        ]
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "statistics": {
                "total_jobs": total_jobs,
                "pending_jobs": pending_jobs,
                "processing_jobs": processing_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "success_rate": success_rate,
                "failure_rate": failure_rate
            },
            "recent_failures": failure_details
        }
        
    except Exception as e:
        logger.error(f"Video processing health monitoring failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    finally:
        db.close()