from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Enum, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base

class AudioProcessingMode(str, enum.Enum):
    HCS_RESTORE = "hcs_restore"
    HCS_SPATIAL = "hcs_spatial"
    HCS_CLARITY = "hcs_clarity"
    HCS_DYNAMIC = "hcs_dynamic"

class AudioJobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AudioJob(Base):
    __tablename__ = "audio_jobs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Job details
    job_name = Column(String(255))
    processing_mode = Column(Enum(AudioProcessingMode), nullable=False)
    status = Column(Enum(AudioJobStatus), default=AudioJobStatus.PENDING)
    priority = Column(Integer, default=0)  # Higher number = higher priority
    
    # File information
    input_filename = Column(String(255))
    input_filepath = Column(String(500))
    input_filesize_bytes = Column(Integer)
    input_format = Column(String(50))
    
    output_filename = Column(String(255))
    output_filepath = Column(String(500))
    output_filesize_bytes = Column(Integer)
    output_format = Column(String(50))
    
    # Processing metrics
    processing_time_ms = Column(Integer)
    queue_time_ms = Column(Integer)
    total_time_ms = Column(Integer)
    
    # Quality metrics
    input_quality_score = Column(Integer)  # 0-100
    output_quality_score = Column(Integer)  # 0-100
    quality_improvement = Column(Integer)  # Percentage improvement
    
    # Audio-specific metrics
    input_sample_rate_hz = Column(Integer)
    output_sample_rate_hz = Column(Integer)
    input_bit_depth = Column(Integer)
    output_bit_depth = Column(Integer)
    input_channels = Column(Integer)
    output_channels = Column(Integer)
    noise_reduction_db = Column(Integer)
    dynamic_range_db = Column(Integer)
    spatial_channels_added = Column(Integer)
    
    # External service references
    external_job_id = Column(String(100))  # ID from audio service
    service_response = Column(JSON)  # Full response from audio service
    
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
    user = relationship("User", back_populates="audio_jobs")
    
    def __repr__(self):
        return f"<AudioJob(id={self.id}, user_id={self.user_id}, status={self.status})>"