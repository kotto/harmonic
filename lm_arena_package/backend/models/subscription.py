from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Enum, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base

class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tier = Column(Enum(SubscriptionTier), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    
    # Limits
    monthly_audio_limit = Column(Integer, default=10)
    monthly_video_limit = Column(Integer, default=10)
    max_file_size_mb = Column(Integer, default=100)
    max_concurrent_jobs = Column(Integer, default=1)
    
    # Features
    has_api_access = Column(Boolean, default=False)
    has_priority_processing = Column(Boolean, default=False)
    has_custom_integration = Column(Boolean, default=False)
    has_dedicated_support = Column(Boolean, default=False)
    
    # Pricing
    monthly_price_eur = Column(Numeric(10, 2), default=0.00)
    yearly_price_eur = Column(Numeric(10, 2))
    stripe_price_id = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<SubscriptionPlan(id={self.id}, tier={self.tier}, name={self.name})>"

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)
    plan_id = Column(String(36), ForeignKey("subscription_plans.id"), nullable=False)
    
    # Subscription details
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    current_period_start = Column(DateTime(timezone=True))
    current_period_end = Column(DateTime(timezone=True))
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime(timezone=True))
    
    # Billing
    stripe_subscription_id = Column(String(100), unique=True)
    stripe_customer_id = Column(String(100))
    payment_method_id = Column(String(100))
    
    # Trial
    trial_start = Column(DateTime(timezone=True))
    trial_end = Column(DateTime(timezone=True))
    
    # Usage tracking
    audio_usage_current_month = Column(Integer, default=0)
    video_usage_current_month = Column(Integer, default=0)
    last_reset_date = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="subscription")
    plan = relationship("SubscriptionPlan")
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, status={self.status})>"