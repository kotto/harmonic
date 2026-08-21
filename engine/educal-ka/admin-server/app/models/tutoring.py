# ──────────────────────────────────────────────
# Modèle Session de Tutorat (jumeau de Teleconsult)
# ──────────────────────────────────────────────
import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TutoringStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TutoringSession(Base):
    __tablename__ = "tutoring_sessions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    teacher_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("teachers.id"), nullable=False, index=True
    )
    learner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("learners.id"), nullable=False, index=True
    )
    unit_id: Mapped[str | None] = mapped_column(String(120), nullable=True)  # unité travaillée
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[TutoringStatus] = mapped_column(
        Enum(TutoringStatus, native_enum=False), default=TutoringStatus.SCHEDULED, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # compte-rendu professeur

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        Index("ix_tutoring_teacher_status", "teacher_id", "status"),
        Index("ix_tutoring_learner_status", "learner_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Tutoring {self.teacher_id}→{self.learner_id} [{self.status.value}]>"
