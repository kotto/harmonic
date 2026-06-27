import httpx
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.config import settings
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionTier
from app.models.video_job import VideoJob, VideoJobStatus
from app.schemas.video import VideoProcessingRequest

logger = logging.getLogger(__name__)

class VideoService:
    @staticmethod
    def check_usage_limit(db: Session, user: User) -> bool:
        """
        Check if user has reached monthly video usage limit
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
                monthly_limit = plan.monthly_video_limit
            
            # Check usage for current month
            first_day_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            usage_count = db.query(VideoJob).filter(
                VideoJob.user_id == user.id,
                VideoJob.created_at >= first_day_of_month,
                VideoJob.status.in_([VideoJobStatus.COMPLETED, VideoJobStatus.PROCESSING])
            ).count()
            
            return usage_count < monthly_limit
        
        else:
            # Check if usage reset is needed
            if not subscription.last_reset_date or subscription.last_reset_date.month != datetime.now().month:
                subscription.video_usage_current_month = 0
                subscription.last_reset_date = datetime.now()
                db.commit()
            
            plan = subscription.plan
            return subscription.video_usage_current_month < plan.monthly_video_limit
    
    @staticmethod
    def check_enterprise_access(db: Session, user: User) -> bool:
        """
        Check if user has enterprise subscription for advanced features
        """
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status == "active"
        ).first()
        
        if not subscription:
            return False
        
        plan = subscription.plan
        return plan.tier == SubscriptionTier.ENTERPRISE
    
    @staticmethod
    def increment_usage(db: Session, user: User) -> None:
        """
        Increment user's video usage count
        """
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status == "active"
        ).first()
        
        if subscription:
            subscription.video_usage_current_month += 1
            db.commit()
            
            logger.debug(f"Video usage incremented for user: {user.email}")
    
    @staticmethod
    async def process_video(
        video_request: VideoProcessingRequest,
        input_file_url: Optional[str] = None,
        input_file_content: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Process video using Harmonic AI video service
        """
        try:
            # Prepare request for video service
            request_data = {
                "processing_mode": video_request.processing_mode.value,
                "target_resolution": video_request.target_resolution,
                "target_fps": video_request.target_fps,
                "enable_hdr": video_request.enable_hdr,
                "enable_frame_gen": video_request.enable_frame_gen,
                "enable_continuous": video_request.enable_continuous,
                "custom_parameters": video_request.custom_parameters or {}
            }
            
            # Add file data if provided
            if input_file_url:
                request_data["input_file_url"] = input_file_url
            elif input_file_content:
                # For small files, we can send directly
                request_data["input_file_content"] = input_file_content.hex()
            
            # Call video service
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{settings.VIDEO_SERVICE_URL}/process",
                    json=request_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    logger.info(f"Video processing completed successfully")
                    
                    return {
                        "success": True,
                        "result": result,
                        "error": None
                    }
                else:
                    error_msg = f"Video service error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    
                    return {
                        "success": False,
                        "result": None,
                        "error": error_msg
                    }
                    
        except httpx.TimeoutException:
            error_msg = "Video service timeout"
            logger.error(error_msg)
            
            return {
                "success": False,
                "result": None,
                "error": error_msg
            }
            
        except Exception as e:
            error_msg = f"Video processing error: {str(e)}"
            logger.error(error_msg)
            
            return {
                "success": False,
                "result": None,
                "error": error_msg
            }
    
    @staticmethod
    async def get_job_status(external_job_id: str) -> Dict[str, Any]:
        """
        Get status of video processing job from external service
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{settings.VIDEO_SERVICE_URL}/status/{external_job_id}"
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
    def estimate_processing_time(
        file_size_bytes: int, 
        duration_seconds: float,
        processing_mode: str
    ) -> int:
        """
        Estimate processing time in milliseconds
        """
        # Base processing time per MB
        base_time_per_mb = 500  # ms per MB for video
        
        # Mode multipliers
        mode_multipliers = {
            "hcs_4k_clarity": 2.0,
            "hcs_8k_master": 4.0,
            "hcs_hdr_vision": 2.5,
            "hcs_frame_gen": 3.0,
            "hcs_movie_continuous": 10.0  # Continuous generation is intensive
        }
        
        multiplier = mode_multipliers.get(processing_mode, 1.0)
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        # Factor in duration for frame-based processing
        duration_factor = max(1.0, duration_seconds / 60.0)  # Longer videos take more time
        
        estimated_time = int(base_time_per_mb * file_size_mb * multiplier * duration_factor)
        
        # Minimum and maximum bounds
        estimated_time = max(estimated_time, 5000)  # At least 5 seconds
        estimated_time = min(estimated_time, 3600000)  # At most 1 hour
        
        return estimated_time
    
    @staticmethod
    def validate_video_file(file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Validate video file before processing
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
            
            if file_ext not in settings.ALLOWED_VIDEO_EXTENSIONS:
                return {
                    "valid": False,
                    "error": f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_VIDEO_EXTENSIONS)}"
                }
            
            # Basic video validation (could be extended with actual video analysis)
            if len(file_content) < 1024:  # Minimum 1KB
                return {
                    "valid": False,
                    "error": "File too small to be a valid video file"
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
    def calculate_cost(
        file_size_bytes: int, 
        duration_seconds: float,
        processing_mode: str, 
        user_tier: str
    ) -> float:
        """
        Calculate cost for video processing
        """
        # Cost per MB based on tier
        cost_per_mb = {
            "free": 0.50,
            "pro": 0.25,
            "enterprise": 0.10
        }
        
        # Mode multipliers
        mode_multipliers = {
            "hcs_4k_clarity": 2.0,
            "hcs_8k_master": 4.0,
            "hcs_hdr_vision": 2.5,
            "hcs_frame_gen": 3.0,
            "hcs_movie_continuous": 20.0  # Continuous generation is expensive
        }
        
        base_cost = cost_per_mb.get(user_tier, 0.50)
        multiplier = mode_multipliers.get(processing_mode, 1.0)
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        # Factor in duration for frame-based processing
        duration_factor = max(1.0, duration_seconds / 60.0)
        
        cost = base_cost * file_size_mb * multiplier * duration_factor
        
        # Minimum cost
        cost = max(cost, 0.10)
        
        # Round to 4 decimal places
        return round(cost, 4)
    
    @staticmethod
    def get_supported_resolutions(processing_mode: str) -> list[str]:
        """
        Get supported resolutions for a processing mode
        """
        resolutions = {
            "hcs_4k_clarity": ["1920x1080", "2560x1440", "3840x2160"],
            "hcs_8k_master": ["3840x2160", "7680x4320"],
            "hcs_hdr_vision": ["1920x1080", "2560x1440", "3840x2160"],
            "hcs_frame_gen": ["1920x1080", "2560x1440", "3840x2160"],
            "hcs_movie_continuous": ["1920x1080", "2560x1440", "3840x2160", "7680x4320"]
        }
        
        return resolutions.get(processing_mode, ["1920x1080"])
    
    @staticmethod
    def get_supported_formats() -> list[str]:
        """
        Get supported video formats
        """
        return settings.ALLOWED_VIDEO_EXTENSIONS