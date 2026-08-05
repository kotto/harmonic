# ──────────────────────────────────────────────
# Modèles SQLAlchemy — Téléconsultation par lien
# ──────────────────────────────────────────────
# Le patient génère un LIEN de session qu'il partage (WhatsApp/SMS)
# à son médecin — souvent à l'étranger. Le médecin clique, s'identifie,
# consulte (WebRTC), et reçoit ses honoraires en UM convertibles.
import enum
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TeleconsultStatus(str, enum.Enum):
    PENDING = "pending"          # lien créé, en attente du médecin
    ACCEPTED = "accepted"        # médecin identifié, session ouverte
    IN_PROGRESS = "in_progress"  # consultation en cours
    COMPLETED = "completed"      # terminée + paiement
    EXPIRED = "expired"          # token expiré (30 min)
    CANCELLED = "cancelled"


class TeleconsultSession(Base):
    """Session de téléconsultation initiée par le patient via un lien."""
    __tablename__ = "teleconsult_sessions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    patient_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), index=True, nullable=False)
    patient_name: Mapped[str | None] = mapped_column(String(150), nullable=True)

    # Médecin ciblé (optionnel — le lien peut être partagé à n'importe quel médecin)
    doctor_wallet_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    doctor_name: Mapped[str | None] = mapped_column(String(150), nullable=True)

    # Montant convenu (UM)
    amount_um: Mapped[float] = mapped_column(nullable=False, default=0)

    status: Mapped[TeleconsultStatus] = mapped_column(
        Enum(TeleconsultStatus, native_enum=False),
        default=TeleconsultStatus.PENDING, nullable=False, index=True
    )

    # Durée de validité du lien : 30 min par défaut
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Paiement
    payment_tx_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Teleconsult {self.token} [{self.status}] {self.patient_name}>"
