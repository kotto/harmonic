# ──────────────────────────────────────────────
# Sécurité : hachage, JWT, rôles & permissions
# ──────────────────────────────────────────────
"""Sécurité EDUCAL KA — jumeau simplifié de vital-ka (sans dépendance
passlib : PBKDF2 natif + JWT via PyJWT si disponible, fallback HMAC)."""

import base64
import hashlib
import hmac
import json
import secrets
import time
from enum import Enum

from app.core.config import settings


# ════════════════════════════════════════════════════════════════
# RÔLES & PERMISSIONS
# ════════════════════════════════════════════════════════════════

class Role(str, Enum):
    ADMIN = "admin"          # Direction de l'établissement
    TEACHER = "teacher"      # Professeur
    PARENT = "parent"        # Parent d'élève
    STUDENT = "student"      # Élève


class Permission(str, Enum):
    MANAGE_UNITS = "manage_units"      # Publier/versionner les unités
    VALIDATE_TEACHERS = "validate_teachers"
    VIEW_LEARNERS = "view_learners"
    TUTOR = "tutor"                     # Créer des sessions de tutorat


ROLE_PERMISSIONS = {
    Role.ADMIN: {p for p in Permission},
    Role.TEACHER: {Permission.MANAGE_UNITS, Permission.VIEW_LEARNERS, Permission.TUTOR},
    Role.PARENT: {Permission.VIEW_LEARNERS},
    Role.STUDENT: set(),
}


def has_permission(role: Role, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())


# ════════════════════════════════════════════════════════════════
# HACHAGE DE MOT DE PASSE (PBKDF2 — stdlib)
# ════════════════════════════════════════════════════════════════

_ITERATIONS = 210_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return f"pbkdf2${_ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iters, salt_b64, dk_b64 = stored.split("$")
        salt = base64.b64decode(salt_b64)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iters))
        return hmac.compare_digest(dk, base64.b64decode(dk_b64))
    except Exception:
        return False


# ════════════════════════════════════════════════════════════════
# TOKENS (JWT via PyJWT si dispo, fallback HMAC signé)
# ════════════════════════════════════════════════════════════════

try:
    import jwt as _pyjwt
    _HAS_PYJWT = True
except ImportError:
    _pyjwt = None
    _HAS_PYJWT = False


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def create_access_token(user_id: str, role: Role, expires_minutes: int = None) -> str:
    minutes = expires_minutes or settings.access_token_expire_minutes
    payload = {
        "sub": str(user_id),
        "role": role.value,
        "exp": int(time.time()) + minutes * 60,
        "iat": int(time.time()),
    }
    if _HAS_PYJWT:
        return _pyjwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    # Fallback HMAC : header.payload.signature
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = _b64url(json.dumps(payload).encode())
    sig = _b64url(hmac.new(settings.jwt_secret_key.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest())
    return f"{header}.{body}.{sig}"


def decode_token(token: str) -> dict:
    """Décode et vérifie un token. Lève ValueError si invalide/expiré."""
    if _HAS_PYJWT:
        return _pyjwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("token malformé")
    header, body, sig = parts
    expected = _b64url(hmac.new(settings.jwt_secret_key.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(sig, expected):
        raise ValueError("signature invalide")
    payload = json.loads(base64.urlsafe_b64decode(body + "=="))
    if payload.get("exp", 0) < time.time():
        raise ValueError("token expiré")
    return payload
