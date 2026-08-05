# ──────────────────────────────────────────────
# Modèles SQLAlchemy - Versions & Bundles
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


class ReleaseChannel(str, enum.Enum):
    ALPHA = "alpha"       # Interne, test intensif
    BETA = "beta"         # Testeurs externes
    STABLE = "stable"     # Production


class APKVersion(Base):
    __tablename__ = "apk_versions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Version
    version_name: Mapped[str] = mapped_column(String(50), nullable=False)  # ex: "2.1.0"
    version_code: Mapped[int] = mapped_column(nullable=False, unique=True, index=True)  # ex: 20100
    channel: Mapped[ReleaseChannel] = mapped_column(
        Enum(ReleaseChannel, native_enum=False), default=ReleaseChannel.STABLE, nullable=False, index=True
    )
    
    # Fichiers
    apk_file_path: Mapped[str] = mapped_column(String(500), nullable=False)  # MinIO path
    apk_file_size: Mapped[int] = mapped_column(nullable=False)
    apk_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    
    # Bundle hologrammes associé (optionnel)
    bundle_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("hologram_bundles.id"), nullable=True
    )
    
    # Métadonnées
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    release_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    min_app_version: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Version min requise pour MAJ
    
    # Build info
    build_number: Mapped[int | None] = mapped_column(nullable=True)
    git_commit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    git_branch: Mapped[str | None] = mapped_column(String(100), nullable=True)
    built_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    built_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Statut
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(default=False, nullable=False)  # MAJ forcée
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deprecated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relations
    bundle: Mapped["HologramBundle | None"] = relationship("HologramBundle")
    webhook_logs: Mapped[list["WebhookLog"]] = relationship(
        "WebhookLog", back_populates="version", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_apk_versions_channel_active", "channel", "is_active"),
        Index("ix_apk_versions_version_code", "version_code"),
    )

    def __repr__(self) -> str:
        return f"<APKVersion {self.version_name} ({self.channel})>"


class HologramBundle(Base):
    __tablename__ = "hologram_bundles"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Version
    version: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)  # ex: "2024.12.01"
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Fichier
    bundle_file_path: Mapped[str] = mapped_column(String(500), nullable=False)  # MinIO path
    bundle_file_size: Mapped[int] = mapped_column(nullable=False)
    bundle_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    
    # Contenu
    domains_count: Mapped[int] = mapped_column(default=0, nullable=False)
    facts_count: Mapped[int] = mapped_column(default=0, nullable=False)
    pathologies_count: Mapped[int] = mapped_column(default=0, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)  # Détails par domaine
    
    # Build
    built_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    built_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Statut
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relations
    apk_versions: Mapped[list["APKVersion"]] = relationship("APKVersion", back_populates="bundle")

    def __repr__(self) -> str:
        return f"<HologramBundle {self.version}>"


class WebhookLog(Base):
    __tablename__ = "webhook_logs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("apk_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    # Webhook
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # version_published, bundle_published, rollback
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Résultat
    status_code: Mapped[int | None] = mapped_column(nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    success: Mapped[bool] = mapped_column(default=False, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt: Mapped[int] = mapped_column(default=1, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    version: Mapped["APKVersion"] = relationship("APKVersion", back_populates="webhook_logs")

    __table_args__ = (
        Index("ix_webhook_logs_version_created", "version_id", "created_at"),
    )