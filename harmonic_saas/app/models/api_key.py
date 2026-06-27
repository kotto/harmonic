from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Key details
    name = Column(String(100), nullable=False)
    key = Column(String(100), unique=True, nullable=False, index=True)
    prefix = Column(String(10))  # First few characters for identification
    
    # Permissions
    can_read = Column(Boolean, default=True)
    can_write = Column(Boolean, default=True)
    can_delete = Column(Boolean, default=False)
    can_manage = Column(Boolean, default=False)
    
    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=60)
    rate_limit_per_hour = Column(Integer, default=1000)
    
    # Security
    last_used = Column(DateTime(timezone=True))
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    revoked_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, user_id={self.user_id}, name={self.name})>"