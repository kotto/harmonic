# ──────────────────────────────────────────────
# Modèle Élève — carnet d'apprentissage
# (jumeau de Record/dossier patient : progression, compétences, lacunes)
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Learner(Base):
    __tablename__ = "learners"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, nullable=False, index=True
    )
    parent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    level: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 6e, 4e, Terminale...
    school: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Carnet d'apprentissage (synchronisé depuis /api/educal/progress)
    validated_units: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)  # {unit_id: date}
    skills: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)           # {objectif: 0.0-1.0}
    lacunes: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)          # [objectif]
    sessions: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)         # historique quiz

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
        Index("ix_learners_level_school", "level", "school"),
    )

    def __repr__(self) -> str:
        return f"<Learner {self.level or '?'} · {len(self.validated_units or {})} unités validées>"
