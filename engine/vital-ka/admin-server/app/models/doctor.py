# ──────────────────────────────────────────────
# Modèles SQLAlchemy - Docteurs & KYC
# ──────────────────────────────────────────────
import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DoctorStatus(str, enum.Enum):
    PENDING = "pending"           # En attente de validation
    UNDER_REVIEW = "under_review" # En cours de vérification
    VALIDATED = "validated"       # Validé - médecin actif
    REJECTED = "rejected"         # Rejeté
    SUSPENDED = "suspended"       # Suspendu (admin)
    EXPIRED = "expired"           # Expiré (renouvellement requis)


class KYCDocumentType(str, enum.Enum):
    IDENTITY = "identity"              # Pièce identité
    MEDICAL_DEGREE = "medical_degree"  # Diplôme médecine
    LICENSE = "license"                # Numéro ordre/licence
    SPECIALTY_CERT = "specialty_cert"  # Certificat spécialité
    PROOF_ADDRESS = "proof_address"    # Justificatif domicile
    CV = "cv"                          # CV
    OTHER = "other"                    # Autre


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    
    # Infos professionnelles
    license_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    specialty: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    sub_specialty: Mapped[str | None] = mapped_column(String(100), nullable=True)
    years_experience: Mapped[int | None] = mapped_column(nullable=True)
    
    # Localisation
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="France")
    city: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    practice_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    coordinates: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {lat, lng}
    
    # Statut KYC
    status: Mapped[DoctorStatus] = mapped_column(
        Enum(DoctorStatus, native_enum=False),
        default=DoctorStatus.PENDING,
        nullable=False,
        index=True,
    )
    
    # Validation
    validated_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Métadonnées
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    login_count: Mapped[int] = mapped_column(default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relations
    documents: Mapped[list["KYCDocument"]] = relationship(
        "KYCDocument", back_populates="doctor", cascade="all, delete-orphan"
    )
    verification_logs: Mapped[list["VerificationLog"]] = relationship(
        "VerificationLog", back_populates="doctor", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_doctors_status_created", "status", "created_at"),
        Index("ix_doctors_specialty_city", "specialty", "city"),
    )

    def __repr__(self) -> str:
        return f"<Doctor {self.email} [{self.status}]>"


class KYCDocument(Base):
    __tablename__ = "kyc_documents"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    doctor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_type: Mapped[KYCDocumentType] = mapped_column(
        Enum(KYCDocumentType, native_enum=False), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)  # Chemin MinIO
    file_size: Mapped[int] = mapped_column(nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Validation
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    verified_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relation
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="documents")

    __table_args__ = (
        UniqueConstraint("doctor_id", "document_type", name="uq_doctor_document_type"),
    )


class VerificationLog(Base):
    __tablename__ = "verification_logs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    doctor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # created, submitted, reviewed, validated, rejected, suspended
    from_status: Mapped[DoctorStatus | None] = mapped_column(Enum(DoctorStatus, native_enum=False), nullable=True)
    to_status: Mapped[DoctorStatus | None] = mapped_column(Enum(DoctorStatus, native_enum=False), nullable=True)
    performed_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="verification_logs")

    __table_args__ = (
        Index("ix_verification_logs_doctor_created", "doctor_id", "created_at"),
    )