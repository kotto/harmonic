# ──────────────────────────────────────────────
# Sécurité - JWT, Hash, RBAC
# ──────────────────────────────────────────────
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings


# ──────────────────────────────────────────────
# Password Hashing
# ──────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hasher un mot de passe"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifier un mot de passe"""
    return pwd_context.verify(plain_password, hashed_password)


# ──────────────────────────────────────────────
# JWT Tokens
# ──────────────────────────────────────────────
class TokenPayload(BaseModel):
    sub: str  # user_id
    email: str
    role: str
    exp: int
    iat: int
    type: str  # "access" ou "refresh"
    jti: str  # JWT ID pour révocation


def create_token(
    user_id: UUID,
    email: str,
    role: str,
    expires_delta: timedelta,
    token_type: str = "access",
) -> str:
    """Créer un JWT token"""
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    import uuid
    jti = str(uuid.uuid4())

    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": token_type,
        "jti": jti,
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: UUID, email: str, role: str) -> str:
    return create_token(
        user_id,
        email,
        role,
        timedelta(minutes=settings.access_token_expire_minutes),
        "access",
    )


def create_refresh_token(user_id: UUID, email: str, role: str) -> str:
    return create_token(
        user_id,
        email,
        role,
        timedelta(days=settings.refresh_token_expire_days),
        "refresh",
    )


def decode_token(token: str) -> Optional[TokenPayload]:
    """Décoder et valider un token"""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return TokenPayload(**payload)
    except JWTError:
        return None


def is_token_expired(payload: TokenPayload) -> bool:
    return datetime.now(timezone.utc).timestamp() > payload.exp


# ──────────────────────────────────────────────
# RBAC - Rôles et Permissions
# ──────────────────────────────────────────────
class Role(str):
    ADMIN = "admin"
    VALIDATOR = "validator"
    DOCTOR = "doctor"
    PATIENT = "patient"


class Permission(str):
    # Doctors
    DOCTOR_CREATE = "doctor:create"
    DOCTOR_READ = "doctor:read"
    DOCTOR_UPDATE = "doctor:update"
    DOCTOR_DELETE = "doctor:delete"
    DOCTOR_VALIDATE = "doctor:validate"
    DOCTOR_LIST = "doctor:list"

    # Versions
    VERSION_CREATE = "version:create"
    VERSION_READ = "version:read"
    VERSION_UPDATE = "version:update"
    VERSION_DELETE = "version:delete"
    VERSION_ROLLBACK = "version:rollback"

    # Admin
    ADMIN_CONFIG_READ = "admin:config:read"
    ADMIN_CONFIG_WRITE = "admin:config:write"
    ADMIN_AUDIT_READ = "admin:audit:read"
    ADMIN_BACKUP_CREATE = "admin:backup:create"
    ADMIN_HEALTH_READ = "admin:health:read"
    ADMIN_METRICS_READ = "admin:metrics:read"

    # System
    SYSTEM_NOTIFICATION_SEND = "system:notification:send"


# Mapping Rôle -> Permissions
ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    Role.ADMIN: {
        # Tout
        Permission.DOCTOR_CREATE,
        Permission.DOCTOR_READ,
        Permission.DOCTOR_UPDATE,
        Permission.DOCTOR_DELETE,
        Permission.DOCTOR_VALIDATE,
        Permission.DOCTOR_LIST,
        Permission.VERSION_CREATE,
        Permission.VERSION_READ,
        Permission.VERSION_UPDATE,
        Permission.VERSION_DELETE,
        Permission.VERSION_ROLLBACK,
        Permission.ADMIN_CONFIG_READ,
        Permission.ADMIN_CONFIG_WRITE,
        Permission.ADMIN_AUDIT_READ,
        Permission.ADMIN_BACKUP_CREATE,
        Permission.ADMIN_HEALTH_READ,
        Permission.ADMIN_METRICS_READ,
        Permission.SYSTEM_NOTIFICATION_SEND,
    },
    Role.VALIDATOR: {
        Permission.DOCTOR_READ,
        Permission.DOCTOR_UPDATE,
        Permission.DOCTOR_VALIDATE,
        Permission.DOCTOR_LIST,
        Permission.VERSION_READ,
        Permission.ADMIN_HEALTH_READ,
    },
    Role.DOCTOR: {
        Permission.DOCTOR_READ,  # Son propre profil
        Permission.VERSION_READ,
    },
    Role.PATIENT: {
        Permission.VERSION_READ,  # Check MAJ
    },
}


def has_permission(role: str, permission: Permission) -> bool:
    """Vérifier si un rôle a une permission"""
    return permission in ROLE_PERMISSIONS.get(role, set())


def require_permission(permission: Permission):
    """Dépendance FastAPI pour vérifier permission"""
    from fastapi import Depends, HTTPException, status
    from app.api.deps import get_current_user

    def checker(current_user=Depends(get_current_user)):
        if not has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission requise: {permission}",
            )
        return current_user

    return checker