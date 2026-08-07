# ──────────────────────────────────────────────
# Dépendances FastAPI - Auth & RBAC
# ──────────────────────────────────────────────
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token, TokenPayload, Role, Permission, has_permission
from app.models import User, Doctor, UserRole, UserStatus, DoctorStatus

# Security scheme
security = HTTPBearer(auto_error=False)


# ──────────────────────────────────────────────
# Utilisateur Admin/Validateur (depuis table users)
# ──────────────────────────────────────────────
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Récupérer l'utilisateur admin/validateur depuis le token JWT"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token d'authentification requis",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Type de token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Récupérer user en base
    result = await db.execute(
        select(User).where(User.id == UUID(payload.sub))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur non trouvé",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Compte {user.status.value}",
        )

    # Vérifier lockout
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte temporairement verrouillé",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Utilisateur actif (alias pour clarté)"""
    return current_user


def require_role(*roles: UserRole):
    """Dépendance pour exiger un rôle spécifique"""
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rôle requis: {[r.value for r in roles]}",
            )
        return current_user
    return checker


def require_permission(permission: Permission):
    """Dépendance pour exiger une permission spécifique"""
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if not has_permission(current_user.role.value, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission requise: {permission}",
            )
        return current_user
    return checker


# ──────────────────────────────────────────────
# Médecin (depuis table doctors)
# ──────────────────────────────────────────────
async def get_current_doctor(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Doctor:
    """Récupérer le médecin depuis le token JWT"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token d'authentification requis",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Type de token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Vérifier que c'est un médecin (role dans token)
    if payload.role != Role.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux médecins",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(
        select(Doctor).where(Doctor.id == UUID(payload.sub))
    )
    doctor = result.scalar_one_or_none()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Médecin non trouvé",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not doctor.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé",
        )

    if doctor.status not in (DoctorStatus.VALIDATED, DoctorStatus.UNDER_REVIEW):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Statut non autorisé: {doctor.status.value}",
        )

    return doctor


# ──────────────────────────────────────────────
# Patient / Public (token optionnel)
# ──────────────────────────────────────────────
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Utilisateur optionnel (pour endpoints publics avec auth optionnelle)"""
    if not credentials:
        return None

    payload = decode_token(credentials.credentials)
    if not payload or payload.type != "access":
        return None

    result = await db.execute(
        select(User).where(User.id == UUID(payload.sub))
    )
    user = result.scalar_one_or_none()

    if user and user.status == UserStatus.ACTIVE:
        return user
    return None


# ──────────────────────────────────────────────
# Client Info (IP, User-Agent)
# ──────────────────────────────────────────────
class ClientInfo:
    def __init__(self, request: Request):
        self.ip = request.client.host if request.client else None
        self.user_agent = request.headers.get("user-agent")
        self.forwarded_for = request.headers.get("x-forwarded-for")


def get_client_info(request: Request) -> ClientInfo:
    return ClientInfo(request)


# ──────────────────────────────────────────────
# Audit Log Helper
# ──────────────────────────────────────────────
async def log_audit(
    db: AsyncSession,
    action: str,
    resource_type: str,
    resource_id: Optional[UUID] = None,
    user: Optional[User] = None,
    doctor: Optional[Doctor] = None,
    client: Optional[ClientInfo] = None,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
    metadata: Optional[dict] = None,
    success: bool = True,
    error_message: Optional[str] = None,
) -> None:
    """Enregistrer une entrée d'audit"""
    from app.models import AuditLog
    from uuid import uuid4

    audit = AuditLog(
        id=uuid4(),
        user_id=user.id if user else (doctor.id if doctor else None),
        user_email=user.email if user else (doctor.email if doctor else None),
        user_role=user.role.value if user else (Role.DOCTOR if doctor else None),
        ip_address=client.ip if client else None,
        user_agent=client.user_agent if client else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        old_values=old_values,
        new_values=new_values,
        metadata=metadata,
        success=success,
        error_message=error_message,
    )
    db.add(audit)
    await db.flush()