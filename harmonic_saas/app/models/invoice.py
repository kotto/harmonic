from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Enum, Numeric, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base

class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Invoice details
    invoice_number = Column(String(50), unique=True, nullable=False)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    
    # Billing period
    period_start = Column(DateTime(timezone=True))
    period_end = Column(DateTime(timezone=True))
    
    # Amounts
    subtotal_eur = Column(Numeric(10, 2), default=0.00)
    tax_eur = Column(Numeric(10, 2), default=0.00)
    total_eur = Column(Numeric(10, 2), default=0.00)
    amount_paid_eur = Column(Numeric(10, 2), default=0.00)
    amount_due_eur = Column(Numeric(10, 2), default=0.00)
    
    # Usage breakdown
    audio_units = Column(Integer, default=0)
    video_units = Column(Integer, default=0)
    text_units = Column(Integer, default=0)
    
    # External references
    stripe_invoice_id = Column(String(100), unique=True)
    stripe_payment_intent_id = Column(String(100))
    
    # Payment details
    paid_at = Column(DateTime(timezone=True))
    due_date = Column(DateTime(timezone=True))
    
    # PDF generation
    pdf_url = Column(String(500))
    pdf_generated_at = Column(DateTime(timezone=True))
    
    # Metadata
    notes = Column(String(1000))
    is_finalized = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="invoices")
    
    def __repr__(self):
        return f"<Invoice(id={self.id}, invoice_number={self.invoice_number}, status={self.status})>"