# ──────────────────────────────────────────────
# Schémas Auth
# ──────────────────────────────────────────────
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.core.security import Role


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=2)
    role: Role = Role.STUDENT


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: Role
    is_active: bool

    model_config = {"from_attributes": True}


TokenResponse.model_rebuild()
