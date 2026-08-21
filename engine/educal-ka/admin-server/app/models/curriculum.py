# ──────────────────────────────────────────────
# Modèle Unité du Programme (jumeau de Version médicale)
# Indexe le catalogue des unités éducatives du moteur KA + versionnage
# ──────────────────────────────────────────────
import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, Float, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UnitStatus(str, enum.Enum):
    DRAFT = "draft"            # En rédaction
    PUBLISHED = "published"    # Disponible au catalogue
    ARCHIVED = "archived"      # Remplacée


class CurriculumUnit(Base):
    __tablename__ = "curriculum_units"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    unit_id: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    discipline: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    niveau: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    programme: Mapped[str | None] = mapped_column(String(80), nullable=True)
    titre: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    facts_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    status: Mapped[UnitStatus] = mapped_column(
        Enum(UnitStatus, native_enum=False), default=UnitStatus.PUBLISHED, nullable=False
    )
    hologramme_associe: Mapped[str | None] = mapped_column(String(80), nullable=True)

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
        Index("ix_units_discipline_niveau", "discipline", "niveau"),
    )

    def __repr__(self) -> str:
        return f"<CurriculumUnit {self.unit_id} v{self.version} [{self.status.value}]>"
