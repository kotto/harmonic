# ──────────────────────────────────────────────
# Modèle Utilisateur (Admins, Validateurs)
# ──────────────────────────────────────────────
import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    VALIDATOR = "validator"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False), default=UserRole.VALIDATOR, nullable=False, index=True
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, native_enum=False), default=UserStatus.ACTIVE, nullable=False
    )
    
    # Sécurité
    failed_login_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # 2FA (optionnel)
    totp_secret: Mapped[str | None] = mapped_column(String(32), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    
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

    __table_args__ = (
        Index("ix_users_role_status", "role", "status"),
    )

    def __repr__(self) -> str:
        return f"<User {self.email} [{self.role}]>"