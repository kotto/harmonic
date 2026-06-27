from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class InvoiceStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class InvoiceItem(BaseModel):
    description: str
    quantity: int = 1
    unit_price: float
    total: float

class InvoiceBase(BaseModel):
    amount: float
    currency: str = "EUR"
    status: InvoiceStatus = InvoiceStatus.PENDING
    items: List[InvoiceItem] = []

class InvoiceCreate(InvoiceBase):
    user_id: str
    subscription_id: Optional[str] = None
    stripe_invoice_id: Optional[str] = None

class InvoiceUpdate(BaseModel):
    status: Optional[InvoiceStatus] = None
    paid_at: Optional[datetime] = None
    stripe_invoice_id: Optional[str] = None

class Invoice(InvoiceBase):
    id: str
    user_id: str
    subscription_id: Optional[str] = None
    invoice_number: str
    stripe_invoice_id: Optional[str] = None
    paid_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class InvoiceResponse(BaseModel):
    """Response model for invoice data"""
    id: str
    user_id: str
    subscription_id: Optional[str] = None
    amount: float
    currency: str = "EUR"
    status: str = "pending"
    stripe_invoice_id: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    paid_at: Optional[str] = None
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True
