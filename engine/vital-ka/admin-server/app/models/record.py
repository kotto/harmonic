# ──────────────────────────────────────────────
# Modèles SQLAlchemy — Dossier Médical Patient
# ──────────────────────────────────────────────
# Dossier santé portable :
#   - Antécédents, allergies, vaccins, traitements
#   - Constantes (tension, glycémie, poids, SpO2...)
#   - Rendez-vous, analyses
#   - Crypté AES-GCM côté application (chiffrement au repos)
import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RecordStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class MedicalRecord(Base):
    """Dossier médical d'un patient, identifié par son walletId (UUID5)."""
    __tablename__ = "medical_records"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    patient_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), index=True, nullable=False, unique=True
    )  # walletId patient résolu (UUID5) — un dossier par patient

    # Profil
    profile: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    #   {name, age, gender, blood, weight, height, shortCode}

    # Données médicales
    antecedents: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    allergies: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    vaccines: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    medications: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    vitals: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    appointments: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    analyses: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # Ordonnances reçues (QR signés décodés)
    ordonnances: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, native_enum=False), default=RecordStatus.ACTIVE, nullable=False
    )

    # Traçabilité
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_medical_records_patient", "patient_id"),
    )

    def __repr__(self) -> str:
        return f"<MedicalRecord patient={self.patient_id} allergies={len(self.allergies)}>"
