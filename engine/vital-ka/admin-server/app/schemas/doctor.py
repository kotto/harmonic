# ──────────────────────────────────────────────
# Schémas Pydantic - Docteurs
# ──────────────────────────────────────────────
from datetime import datetime
from typing import Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class DoctorStatus(str, Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    VALIDATED = "validated"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class KYCDocumentType(str, Enum):
    IDENTITY = "identity"
    MEDICAL_DEGREE = "medical_degree"
    LICENSE = "license"
    SPECIALTY_CERT = "specialty_cert"
    PROOF_ADDRESS = "proof_address"
    CV = "cv"
    OTHER = "other"


# ──────────────────────────────────────────────
# Requests
# ──────────────────────────────────────────────
class DoctorRegisterRequest(BaseModel):
    """Inscription médecin"""
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)
    license_number: str = Field(..., min_length=1, max_length=50)
    specialty: Optional[str] = Field(None, max_length=100)
    sub_specialty: Optional[str] = Field(None, max_length=100)
    years_experience: Optional[int] = Field(None, ge=0, le=60)
    country: str = Field(default="France", max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    practice_address: Optional[str] = None
    coordinates: Optional[dict] = None  # {"lat": float, "lng": float}


class DoctorProfileUpdate(BaseModel):
    """Mise à jour profil médecin"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)
    specialty: Optional[str] = Field(None, max_length=100)
    sub_specialty: Optional[str] = Field(None, max_length=100)
    years_experience: Optional[int] = Field(None, ge=0, le=60)
    country: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    practice_address: Optional[str] = None
    coordinates: Optional[dict] = None


class DoctorValidateRequest(BaseModel):
    """Validation médecin par admin/validateur"""
    notes: Optional[str] = None


class DoctorRejectRequest(BaseModel):
    """Rejet médecin"""
    reason: str = Field(..., min_length=10, max_length=1000)
    notes: Optional[str] = None


class DoctorSuspendRequest(BaseModel):
    """Suspension médecin"""
    reason: str = Field(..., min_length=10, max_length=1000)


class DoctorSearchFilters(BaseModel):
    """Filtres recherche annuaire"""
    status: Optional[DoctorStatus] = None
    specialty: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    validated_only: bool = True
    query: Optional[str] = None  # Recherche textuelle nom/email/license
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# ──────────────────────────────────────────────
# KYC Documents
# ──────────────────────────────────────────────
class KYCDocumentUploadRequest(BaseModel):
    """Upload document KYC (metadata, fichier via multipart)"""
    document_type: KYCDocumentType


class KYCDocumentVerifyRequest(BaseModel):
    """Validation document KYC"""
    is_verified: bool
    rejection_reason: Optional[str] = Field(None, max_length=1000)


# ──────────────────────────────────────────────
# Responses
# ──────────────────────────────────────────────
class KYCDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_type: KYCDocumentType
    file_name: str
    file_size: int
    mime_type: str
    is_verified: bool
    verified_at: Optional[datetime]
    rejection_reason: Optional[str]
    created_at: datetime


class VerificationLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    action: str
    from_status: Optional[DoctorStatus]
    to_status: Optional[DoctorStatus]
    performed_by: Optional[UUID]
    notes: Optional[str]
    metadata: Optional[dict] = Field(None, validation_alias="metadata_json", serialization_alias="metadata")
    created_at: datetime


class DoctorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str]
    license_number: str
    specialty: Optional[str]
    sub_specialty: Optional[str]
    years_experience: Optional[int]
    country: str
    city: Optional[str]
    practice_address: Optional[str]
    coordinates: Optional[dict]
    status: DoctorStatus
    validated_by: Optional[UUID]
    validated_at: Optional[datetime]
    rejection_reason: Optional[str]
    is_active: bool
    last_login: Optional[datetime]
    login_count: int
    created_at: datetime
    updated_at: datetime
    documents: list[KYCDocumentResponse] = []
    verification_logs: list[VerificationLogResponse] = []


class DoctorListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    license_number: str
    specialty: Optional[str]
    city: Optional[str]
    country: str
    status: DoctorStatus
    validated_at: Optional[datetime]
    created_at: datetime


class DoctorSearchResponse(BaseModel):
    items: list[DoctorListResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DoctorStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    status: DoctorStatus
    validated_at: Optional[datetime]
    rejection_reason: Optional[str]
    documents_verified: int
    documents_total: int