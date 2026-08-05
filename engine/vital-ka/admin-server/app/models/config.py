# ──────────────────────────────────────────────
# Modèles SQLAlchemy - Audit & Config Système
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Acteur
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    user_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv6 max 45 chars
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Action
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # ex: doctor.validate, version.upload, config.update
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # doctor, version, bundle, config, user
    resource_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    
    # Détails
    old_values: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_values: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    
    # Résultat
    success: Mapped[bool] = mapped_column(default=True, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    __table_args__ = (
        Index("ix_audit_logs_user_created", "user_id", "created_at"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
        Index("ix_audit_logs_action_created", "action", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} on {self.resource_type}:{self.resource_id}>"


class SystemConfig(Base):
    __tablename__ = "system_config"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)  # Valeur typée stockée en JSON
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="general", index=True)  # general, diagnostic, notifications, security, storage
    is_public: Mapped[bool] = mapped_column(default=False, nullable=False)  # Exposable via API publique
    is_sensitive: Mapped[bool] = mapped_column(default=False, nullable=False)  # Masquer dans logs/audit
    
    # Validation
    schema: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # JSON Schema pour validation
    
    # Historique
    updated_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    
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
        Index("ix_system_config_category", "category"),
    )

    def __repr__(self) -> str:
        return f"<SystemConfig {self.key}>"


# ──────────────────────────────────────────────
# Clés de configuration par défaut
# ──────────────────────────────────────────────
DEFAULT_CONFIGS = {
    # Général
    "app.name": {
        "value": {"value": "Vital KA"},
        "description": "Nom de l'application",
        "category": "general",
        "is_public": True,
    },
    "app.version": {
        "value": {"value": "2.1.0"},
        "description": "Version actuelle de l'app",
        "category": "general",
        "is_public": True,
    },
    "app.maintenance_mode": {
        "value": {"value": False},
        "description": "Mode maintenance (bloque nouvelles connexions)",
        "category": "general",
        "is_public": True,
    },
    
    # Diagnostic
    "diagnostic.confidence_threshold": {
        "value": {"value": 0.75},
        "description": "Seuil de confiance minimum pour diagnostic",
        "category": "diagnostic",
        "schema": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "diagnostic.max_pathologies": {
        "value": {"value": 5},
        "description": "Nombre max de pathologies retournées",
        "category": "diagnostic",
        "schema": {"type": "integer", "minimum": 1, "maximum": 20},
    },
    "diagnostic.enable_ai_assist": {
        "value": {"value": True},
        "description": "Activer assistance IA diagnostic",
        "category": "diagnostic",
    },
    
    # Notifications
    "notifications.email_enabled": {
        "value": {"value": True},
        "description": "Activer emails",
        "category": "notifications",
    },
    "notifications.sms_enabled": {
        "value": {"value": False},
        "description": "Activer SMS",
        "category": "notifications",
    },
    "notifications.push_enabled": {
        "value": {"value": True},
        "description": "Activer push notifications",
        "category": "notifications",
    },
    
    # Sécurité
    "security.password_min_length": {
        "value": {"value": 12},
        "description": "Longueur min mot de passe",
        "category": "security",
        "schema": {"type": "integer", "minimum": 8, "maximum": 64},
    },
    "security.session_timeout_minutes": {
        "value": {"value": 480},  # 8h
        "description": "Timeout session (minutes)",
        "category": "security",
    },
    "security.max_login_attempts": {
        "value": {"value": 5},
        "description": "Tentatives max avant verrouillage",
        "category": "security",
    },
    "security.lockout_duration_minutes": {
        "value": {"value": 30},
        "description": "Durée verrouillage (minutes)",
        "category": "security",
    },
    
    # Stockage
    "storage.max_apk_size_mb": {
        "value": {"value": 100},
        "description": "Taille max APK (MB)",
        "category": "storage",
    },
    "storage.max_bundle_size_mb": {
        "value": {"value": 500},
        "description": "Taille max bundle hologrammes (MB)",
        "category": "storage",
    },
    "storage.retention_days": {
        "value": {"value": 365},
        "description": "Rétention fichiers (jours)",
        "category": "storage",
    },
    
    # Webhooks
    "webhooks.version_published_urls": {
        "value": {"value": []},
        "description": "URLs webhook pour publication version",
        "category": "webhooks",
        "is_sensitive": True,
    },
    "webhooks.bundle_published_urls": {
        "value": {"value": []},
        "description": "URLs webhook pour publication bundle",
        "category": "webhooks",
        "is_sensitive": True,
    },
    "webhooks.retry_attempts": {
        "value": {"value": 3},
        "description": "Tentatives webhook",
        "category": "webhooks",
    },
    "webhooks.timeout_seconds": {
        "value": {"value": 30},
        "description": "Timeout webhook (secondes)",
        "category": "webhooks",
    },
}