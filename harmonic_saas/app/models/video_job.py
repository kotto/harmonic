from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Enum, Boolean, JSON, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base

class VideoProcessingMode(str, enum.Enum):
    HCS_4K_CLARITY = "hcs_4k_clarity"
    HCS_8K_MASTER = "hcs_8k_master"
    HCS_HDR_VISION = "hcs_hdr_vision"
    HCS_FRAME_GEN = "hcs_frame_gen"
    HCS_MOVIE_CONTINUOUS = "hcs_movie_continuous"

class VideoJobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class VideoJob(Base):
    __tablename__ = "video_jobs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Job details
    job_name = Column(String(255))
    processing_mode = Column(Enum(VideoProcessingMode), nullable=False)
    status = Column(Enum(VideoJobStatus), default=VideoJobStatus.PENDING)
    priority = Column(Integer, default=0)  # Higher number = higher priority
    
    # File information
    input_filename = Column(String(255))
    input_filepath = Column(String(500))
    input_filesize_bytes = Column(Integer)
    input_format = Column(String(50))
    input_duration_seconds = Column(Numeric(10, 2))
    
    output_filename = Column(String(255))
    output_filepath = Column(String(500))
    output_filesize_bytes = Column(Integer)
    output_format = Column(String(50))
    output_duration_seconds = Column(Numeric(10, 2))
    
    # Video specifications
    input_resolution = Column(String(50))  # e.g., "1920x1080"
    output_resolution = Column(String(50))  # e.g., "3840x2160"
    input_fps = Column(Integer)  # Frames per second
    output_fps = Column(Integer)
    input_bitrate_kbps = Column(Integer)
    output_bitrate_kbps = Column(Integer)
    input_color_space = Column(String(50))
    output_color_space = Column(String(50))
    input_hdr = Column(Boolean, default=False)
    output_hdr = Column(Boolean, default=False)
    
    # Processing metrics
    processing_time_ms = Column(Integer)
    queue_time_ms = Column(Integer)
    total_time_ms = Column(Integer)
    frames_processed = Column(Integer)
    frames_generated = Column(Integer)
    
    # Quality metrics
    input_quality_score = Column(Integer)  # 0-100
    output_quality_score = Column(Integer)  # 0-100
    quality_improvement = Column(Integer)  # Percentage improvement
    psnr_db = Column(Numeric(5, 2))  # Peak Signal-to-Noise Ratio
    ssim = Column(Numeric(5, 4))  # Structural Similarity Index
    
    # External service references
    external_job_id = Column(String(100))  # ID from video service
    service_response = Column(JSON)  # Full response from video service
    
    # Error handling
    error_message = Column(String(500))
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="video_jobs")
    
    def __repr__(self):
        return f"<VideoJob(id={self.id}, user_id={self.user_id}, status={self.status})>"