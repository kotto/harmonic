# ──────────────────────────────────────────────
# API Auth - Login, Refresh, Password, Register
# ──────────────────────────────────────────────
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from fastapi import (
    APIRouter, Depends, HTTPException, status, Request
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_db, get_current_user, get_current_doctor, get_client_info,
    log_audit, ClientInfo
)
from app.core.security import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    decode_token, TokenPayload, Role, Permission,
)
from app.models import User, Doctor, UserRole, UserStatus, DoctorStatus
from app.schemas import (
    LoginRequest, LoginResponse, TokenResponse, UserInfo,
    DoctorLoginRequest, DoctorLoginResponse, DoctorInfo,
    RefreshTokenRequest, PasswordChangeRequest,
    PasswordResetConfirmRequest,
    AdminUserCreateRequest, AdminUserResponse,
)
from app.services.email_service import email_service


router = APIRouter(prefix="/auth", tags=["Auth"])

security = HTTPBearer(auto_error=False)


# ──────────────────────────────────────────────
# Admin/Validator Login
# ──────────────────────────────────────────────
@router.post("/login", response_model=LoginResponse)
async def login_admin(
    data: LoginRequest,
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Connexion admin/validateur"""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        await log_audit(
            db, "auth.login_failed", "user", None,
            client=client,
            metadata={"email": data.email},
            success=False,
            error_message="Identifiants invalides",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
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

    # Reset failed attempts
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.now(timezone.utc)

    # Créer tokens
    access_token = create_access_token(user.id, user.email, user.role.value)
    refresh_token = create_refresh_token(user.id, user.email, user.role.value)

    expires_in = 1800 if not data.remember_me else 604800  # 30min ou 7 jours

    await log_audit(
        db, "auth.login", "user", user.id,
        user=user, client=client,
        success=True,
    )

    await db.commit()

    return LoginResponse(
        user=UserInfo.model_validate(user),
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        ),
    )


# ──────────────────────────────────────────────
# Doctor Login (déjà dans doctors.py mais gardé ici pour cohérence)
# ──────────────────────────────────────────────
@router.post("/doctor/login", response_model=DoctorLoginResponse)
async def login_doctor(
    data: DoctorLoginRequest,
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Connexion médecin"""
    result = await db.execute(select(Doctor).where(Doctor.email == data.email))
    doctor = result.scalar_one_or_none()

    if not doctor or not verify_password(data.password, doctor.password_hash):
        await log_audit(
            db, "auth.doctor_login_failed", "doctor", None,
            client=client,
            metadata={"email": data.email},
            success=False,
            error_message="Identifiants invalides",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )

    if not doctor.is_active:
        raise HTTPException(status_code=403, detail="Compte désactivé")

    if doctor.status not in (DoctorStatus.VALIDATED, DoctorStatus.UNDER_REVIEW):
        raise HTTPException(
            status_code=403,
            detail=f"Compte non validé (statut: {doctor.status.value})",
        )

    doctor.last_login = datetime.now(timezone.utc)
    doctor.login_count += 1

    access_token = create_access_token(doctor.id, doctor.email, Role.DOCTOR)
    refresh_token = create_refresh_token(doctor.id, doctor.email, Role.DOCTOR)

    expires_in = 1800 if not data.remember_me else 604800

    await log_audit(
        db, "auth.doctor_login", "doctor", doctor.id,
        doctor=doctor, client=client,
        success=True,
    )

    await db.commit()

    return DoctorLoginResponse(
        doctor=DoctorInfo.model_validate(doctor),
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        ),
    )


# ──────────────────────────────────────────────
# Token Refresh
# ──────────────────────────────────────────────
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Rafraîchir access token"""
    payload = decode_token(data.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Refresh token invalide")

    if payload.type != "refresh":
        raise HTTPException(status_code=401, detail="Type de token invalide")

    # Vérifier utilisateur existe encore
    if payload.role == Role.DOCTOR:
        result = await db.execute(select(Doctor).where(Doctor.id == UUID(payload.sub)))
        entity = result.scalar_one_or_none()
        if not entity or not entity.is_active:
            raise HTTPException(status_code=401, detail="Compte invalide")
        role = Role.DOCTOR
    else:
        result = await db.execute(select(User).where(User.id == UUID(payload.sub)))
        entity = result.scalar_one_or_none()
        if not entity or entity.status != UserStatus.ACTIVE:
            raise HTTPException(status_code=401, detail="Compte invalide")
        role = entity.role.value

    # Nouveaux tokens
    access_token = create_access_token(UUID(payload.sub), payload.email, role)
    refresh_token = create_refresh_token(UUID(payload.sub), payload.email, role)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800,
    )


# ──────────────────────────────────────────────
# Current User Info
# ──────────────────────────────────────────────
@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Info utilisateur connecté (admin/validator)"""
    return UserInfo.model_validate(current_user)


@router.get("/doctor/me", response_model=DoctorInfo)
async def get_current_doctor_info(
    doctor: Doctor = Depends(get_current_doctor),
):
    """Info médecin connecté"""
    return DoctorInfo.model_validate(doctor)


# ──────────────────────────────────────────────
# Password Change
# ──────────────────────────────────────────────
@router.post("/change-password")
async def change_password(
    data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Changer mot de passe (admin/validator)"""
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")

    current_user.password_hash = hash_password(data.new_password)
    current_user.password_changed_at = datetime.now(timezone.utc)

    await log_audit(
        db, "auth.password_change", "user", current_user.id,
        user=current_user, client=client,
        success=True,
    )

    await db.commit()
    return {"message": "Mot de passe modifié avec succès"}


@router.post("/doctor/change-password")
async def change_doctor_password(
    data: PasswordChangeRequest,
    doctor: Doctor = Depends(get_current_doctor),
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Changer mot de passe (médecin)"""
    if not verify_password(data.current_password, doctor.password_hash):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")

    doctor.password_hash = hash_password(data.new_password)

    await log_audit(
        db, "auth.doctor_password_change", "doctor", doctor.id,
        doctor=doctor, client=client,
        success=True,
    )

    await db.commit()
    return {"message": "Mot de passe modifié avec succès"}


# ──────────────────────────────────────────────
# Password Reset (Email)
# ──────────────────────────────────────────────
@router.post("/forgot-password")
async def forgot_password(
    email: str,
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Demander reset mot de passe (admin/validator)"""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # Toujours retourner succès (security)
    if user:
        # TODO: Générer token reset, envoyer email
        await email_service.send_password_reset(user)

    return {"message": "Si l'email existe, un lien de réinitialisation a été envoyé"}


@router.post("/doctor/forgot-password")
async def forgot_doctor_password(
    email: str,
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Demander reset mot de passe (médecin)"""
    result = await db.execute(select(Doctor).where(Doctor.email == email))
    doctor = result.scalar_one_or_none()

    if doctor:
        await email_service.send_doctor_password_reset(doctor)

    return {"message": "Si l'email existe, un lien de réinitialisation a été envoyé"}


@router.post("/reset-password")
async def reset_password(
    data: PasswordResetConfirmRequest,
    db: AsyncSession = Depends(get_db),
):
    """Confirmer le reset mot de passe avec le token envoyé par email"""
    # Le token de reset est signé en JWT (payload: type="password_reset", sub=user_id)
    payload = decode_token(data.token)
    if not payload or payload.type != "password_reset":
        raise HTTPException(status_code=400, detail="Token invalide ou expiré")

    result = await db.execute(select(User).where(User.id == payload.sub))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    user.password_hash = hash_password(data.new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    user.failed_login_attempts = 0
    user.locked_until = None
    await db.commit()

    await log_audit(
        db=db,
        action="password_reset",
        resource_type="user",
        resource_id=user.id,
        user=user,
        success=True,
        metadata={"email": user.email},
    )

    return {"message": "Mot de passe réinitialisé avec succès"}


# ──────────────────────────────────────────────
# Logout (Blacklist token - optionnel avec Redis)
# ──────────────────────────────────────────────
@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Déconnexion (blacklist token)"""
    if credentials:
        payload = decode_token(credentials.credentials)
        if payload:
            # Ajouter JTI à blacklist Redis (TTL = remaining token time)
            import redis.asyncio as redis
            from app.core.config import settings
            r = redis.from_url(settings.redis_url)
            ttl = payload.exp - int(datetime.now(timezone.utc).timestamp())
            if ttl > 0:
                await r.setex(f"blacklist:{payload.jti}", ttl, "1")
            await r.close()

    await log_audit(
        db, "auth.logout", "user", current_user.id,
        user=current_user, client=client,
        success=True,
    )

    return {"message": "Déconnecté avec succès"}