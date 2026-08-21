# ──────────────────────────────────────────────
# Modèle Professeur (jumeau de Doctor — profil + matières + classes)
# ──────────────────────────────────────────────
import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TeacherStatus(str, enum.Enum):
    PENDING = "pending"            # En attente de validation
    VALIDATED = "validated"        # Validé — peut enseigner
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, nullable=False, index=True
    )
    subject: Mapped[str] = mapped_column(String(100), default="", nullable=False, index=True)
    school: Mapped[str | None] = mapped_column(String(200), nullable=True)
    qualifications: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {diplômes: [...]}
    classes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {niveau: [unit_ids]}
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[TeacherStatus] = mapped_column(
        Enum(TeacherStatus, native_enum=False),
        default=TeacherStatus.PENDING, nullable=False, index=True
    )
    validated_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

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
        Index("ix_teachers_status_subject", "status", "subject"),
    )

    def __repr__(self) -> str:
        return f"<Teacher {self.subject} [{self.status.value}]>"
