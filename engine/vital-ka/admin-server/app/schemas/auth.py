# ──────────────────────────────────────────────
# Schémas Pydantic - Auth
# ──────────────────────────────────────────────
from typing import Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRole(str, Enum):
    ADMIN = "admin"
    VALIDATOR = "validator"
    DOCTOR = "doctor"
    PATIENT = "patient"


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


# ──────────────────────────────────────────────
# Requests
# ──────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)
    remember_me: bool = False


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=12, max_length=128)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=12, max_length=128)


# ──────────────────────────────────────────────
# Responses
# ──────────────────────────────────────────────
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # secondes


class UserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    status: str  # UserStatus
    last_login: Optional[str]
    created_at: str


class LoginResponse(BaseModel):
    user: UserInfo
    tokens: TokenResponse


# ──────────────────────────────────────────────
# Admin User Management
# ──────────────────────────────────────────────
class AdminUserCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.VALIDATOR


class AdminUserUpdateRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    status: Optional[str] = None  # UserStatus


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    status: str
    failed_login_attempts: int
    locked_until: Optional[str]
    last_login: Optional[str]
    totp_enabled: bool
    created_at: str
    updated_at: str


# ──────────────────────────────────────────────
# Doctor Auth (séparé des users admin)
# ──────────────────────────────────────────────
class DoctorLoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class DoctorLoginResponse(BaseModel):
    doctor: "DoctorInfo"
    tokens: TokenResponse


class DoctorInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    license_number: str
    specialty: Optional[str]
    status: str  # DoctorStatus
    validated_at: Optional[str]
    last_login: Optional[str]


# Forward ref
DoctorLoginResponse.model_rebuild()