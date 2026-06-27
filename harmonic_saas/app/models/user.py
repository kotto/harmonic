from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    
    # Profile
    company = Column(String(255))
    job_title = Column(String(100))
    phone = Column(String(50))
    country = Column(String(100))
    timezone = Column(String(50), default="UTC")
    
    # Settings
    language = Column(String(10), default="en")
    theme = Column(String(20), default="dark")
    notifications_enabled = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    audio_jobs = relationship("AudioJob", back_populates="user")
    video_jobs = relationship("VideoJob", back_populates="user")
    usage_records = relationship("UsageRecord", back_populates="user")
    invoices = relationship("Invoice", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"