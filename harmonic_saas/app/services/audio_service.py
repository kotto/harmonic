import httpx
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.config import settings
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionTier
from app.models.audio_job import AudioJob, AudioJobStatus
from app.schemas.audio import AudioProcessingRequest

logger = logging.getLogger(__name__)

class AudioService:
    @staticmethod
    def check_usage_limit(db: Session, user: User) -> bool:
        """
        Check if user has reached monthly usage limit
        """
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status == "active"
        ).first()
        
        if not subscription:
            # Free tier by default
            plan = db.query(SubscriptionPlan).filter(
                SubscriptionPlan.tier == SubscriptionTier.FREE
            ).first()
            
            if not plan:
                # Default limits if no plan found
                monthly_limit = 10
            else:
                monthly_limit = plan.monthly_audio_limit
            
            # Check usage for current month
            first_day_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            usage_count = db.query(AudioJob).filter(
                AudioJob.user_id == user.id,
                AudioJob.created_at >= first_day_of_month,
                AudioJob.status.in_([AudioJobStatus.COMPLETED, AudioJobStatus.PROCESSING])
            ).count()
            
            return usage_count < monthly_limit
        
        else:
            # Check if usage reset is needed
            if not subscription.last_reset_date or subscription.last_reset_date.month != datetime.now().month:
                subscription.audio_usage_current_month = 0
                subscription.last_reset_date = datetime.now()
                db.commit()
            
            plan = subscription.plan
            return subscription.audio_usage_current_month < plan.monthly_audio_limit
    
    @staticmethod
    def increment_usage(db: Session, user: User) -> None:
        """
        Increment user's audio usage count
        """
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status == "active"
        ).first()
        
        if subscription:
            subscription.audio_usage_current_month += 1
            db.commit()
            
            logger.debug(f"Audio usage incremented for user: {user.email}")
    
    @staticmethod
    async def process_audio(
        audio_request: AudioProcessingRequest,
        input_file_url: Optional[str] = None,
        input_file_content: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Process audio using Harmonic AI audio service
        """
        try:
            # Prepare request for audio service
            request_data = {
                "processing_mode": audio_request.processing_mode.value,
                "target_profile": audio_request.target_profile,
                "enhance_clarity": audio_request.enhance_clarity,
                "reduce_noise": audio_request.reduce_noise,
                "expand_dynamic_range": audio_request.expand_dynamic_range,
                "add_spatial_channels": audio_request.add_spatial_channels,
                "custom_parameters": audio_request.custom_parameters or {}
            }
            
            # Add file data if provided
            if input_file_url:
                request_data["input_file_url"] = input_file_url
            elif input_file_content:
                # For small files, we can send directly
                request_data["input_file_content"] = input_file_content.hex()
            
            # Call audio service
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.AUDIO_SERVICE_URL}/process",
                    json=request_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    logger.info(f"Audio processing completed successfully")
                    
                    return {
                        "success": True,
                        "result": result,
                        "error": None
                    }
                else:
                    error_msg = f"Audio service error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    
                    return {
                        "success": False,
                        "result": None,
                        "error": error_msg
                    }
                    
        except httpx.TimeoutException:
            error_msg = "Audio service timeout"
            logger.error(error_msg)
            
            return {
                "success": False,
                "result": None,
                "error": error_msg
            }
            
        except Exception as e:
            error_msg = f"Audio processing error: {str(e)}"
            logger.error(error_msg)
            
            return {
                "success": False,
                "result": None,
                "error": error_msg
            }
    
    @staticmethod
    async def get_job_status(external_job_id: str) -> Dict[str, Any]:
        """
        Get status of audio processing job from external service
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{settings.AUDIO_SERVICE_URL}/status/{external_job_id}"
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "status": "unknown",
                        "error": f"Status check failed: {response.status_code}"
                    }
                    
        except Exception as e:
            return {
                "status": "unknown",
                "error": str(e)
            }
    
    @staticmethod
    def estimate_processing_time(file_size_bytes: int, processing_mode: str) -> int:
        """
        Estimate processing time in milliseconds
        """
        # Base processing time per MB
        base_time_per_mb = 100  # ms per MB
        
        # Mode multipliers
        mode_multipliers = {
            "hcs_restore": 1.0,
            "hcs_spatial": 1.5,
            "hcs_clarity": 1.2,
            "hcs_dynamic": 1.3
        }
        
        multiplier = mode_multipliers.get(processing_mode, 1.0)
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        estimated_time = int(base_time_per_mb * file_size_mb * multiplier)
        
        # Minimum and maximum bounds
        estimated_time = max(estimated_time, 1000)  # At least 1 second
        estimated_time = min(estimated_time, 300000)  # At most 5 minutes
        
        return estimated_time
    
    @staticmethod
    def validate_audio_file(file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Validate audio file before processing
        """
        try:
            # Check file size
            max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
            
            if len(file_content) > max_size:
                return {
                    "valid": False,
                    "error": f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB"
                }
            
            # Check file extension
            import os
            file_ext = os.path.splitext(filename)[1].lower()
            
            if file_ext not in settings.ALLOWED_AUDIO_EXTENSIONS:
                return {
                    "valid": False,
                    "error": f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_AUDIO_EXTENSIONS)}"
                }
            
            # Basic audio validation (could be extended with actual audio analysis)
            if len(file_content) < 100:  # Minimum 100 bytes
                return {
                    "valid": False,
                    "error": "File too small to be a valid audio file"
                }
            
            return {
                "valid": True,
                "file_size_bytes": len(file_content),
                "file_extension": file_ext
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"File validation error: {str(e)}"
            }
    
    @staticmethod
    def calculate_cost(file_size_bytes: int, processing_mode: str, user_tier: str) -> float:
        """
        Calculate cost for audio processing
        """
        # Cost per MB based on tier
        cost_per_mb = {
            "free": 0.10,
            "pro": 0.05,
            "enterprise": 0.02
        }
        
        # Mode multipliers
        mode_multipliers = {
            "hcs_restore": 1.0,
            "hcs_spatial": 1.8,
            "hcs_clarity": 1.3,
            "hcs_dynamic": 1.5
        }
        
        base_cost = cost_per_mb.get(user_tier, 0.10)
        multiplier = mode_multipliers.get(processing_mode, 1.0)
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        cost = base_cost * file_size_mb * multiplier
        
        # Minimum cost
        cost = max(cost, 0.01)
        
        # Round to 4 decimal places
        return round(cost, 4)