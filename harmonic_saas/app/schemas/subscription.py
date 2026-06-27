from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class SubscriptionTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

# Alias pour compatibilité
SubscriptionPlan = SubscriptionTier

class PlanDefinition(BaseModel):
    """Définition complète d'un plan d'abonnement"""
    tier: SubscriptionTier
    name: str
    price_monthly: float
    price_yearly: float
    features: List[str]
    limits: Dict[str, Any]

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    TRIAL = "trial"

class SubscriptionBase(BaseModel):
    plan: SubscriptionPlan = SubscriptionPlan.FREE
    status: SubscriptionStatus = SubscriptionStatus.TRIAL
    auto_renew: bool = True

class SubscriptionCreate(SubscriptionBase):
    user_id: str
    stripe_subscription_id: Optional[str] = None

class SubscriptionUpdate(BaseModel):
    plan: Optional[SubscriptionPlan] = None
    status: Optional[SubscriptionStatus] = None
    auto_renew: Optional[bool] = None
    stripe_subscription_id: Optional[str] = None

class Subscription(SubscriptionBase):
    id: str
    user_id: str
    stripe_subscription_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SubscriptionResponse(BaseModel):
    """Response model for subscription data"""
    id: str
    user_id: str
    plan: SubscriptionPlan
    status: SubscriptionStatus
    auto_renew: bool = True
    stripe_subscription_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class InvoiceResponse(BaseModel):
    """Response model for invoice data"""
    id: str
    user_id: str
    subscription_id: str
    amount: float
    currency: str = "EUR"
    status: str = "pending"
    description: Optional[str] = None
    invoice_url: Optional[str] = None
    created_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PaymentIntentResponse(BaseModel):
    """Response model for payment intent"""
    id: str
    client_secret: str
    amount: float
    currency: str = "EUR"
    status: str = "requires_payment_method"
    
    class Config:
        from_attributes = True

class UsageMetrics(BaseModel):
    """Usage metrics for current billing period"""
    audio_jobs_used: int = 0
    audio_jobs_limit: int = 10
    video_jobs_used: int = 0
    video_jobs_limit: int = 5
    storage_used_mb: float = 0.0
    storage_limit_mb: float = 100.0
    api_calls_used: int = 0
    api_calls_limit: int = 1000
