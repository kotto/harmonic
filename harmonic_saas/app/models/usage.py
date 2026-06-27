from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Enum, Numeric, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base

class ResourceType(str, enum.Enum):
    AUDIO = "audio"
    VIDEO = "video"
    TEXT = "text"

class UsageRecord(Base):
    __tablename__ = "usage_records"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Resource details
    resource_type = Column(Enum(ResourceType), nullable=False)
    resource_id = Column(String(100))  # Job ID or other identifier
    operation = Column(String(100))  # e.g., "upscale", "enhance", "transcribe"
    
    # Usage metrics
    input_size_bytes = Column(Integer)
    output_size_bytes = Column(Integer)
    processing_time_ms = Column(Integer)
    cost_credits = Column(Numeric(10, 4), default=0.0)
    
    # Quality metrics (for audio/video)
    input_quality_score = Column(Numeric(5, 2))
    output_quality_score = Column(Numeric(5, 2))
    quality_improvement = Column(Numeric(5, 2))
    
    # Status
    status = Column(String(50), default="completed")
    error_message = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="usage_records")
    
    def __repr__(self):
        return f"<UsageRecord(id={self.id}, user_id={self.user_id}, resource_type={self.resource_type})>"

class UsageMetrics(Base):
    """Monthly usage metrics per user"""
    __tablename__ = "usage_metrics"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    audio_minutes = Column(Float, default=0.0)
    video_minutes = Column(Float, default=0.0)
    api_calls = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="usage_metrics")
    
    def __repr__(self):
        return f"<UsageMetrics(user_id={self.user_id}, date={self.date})>"
