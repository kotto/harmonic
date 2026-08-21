# ──────────────────────────────────────────────
# Schémas Professeurs
# ──────────────────────────────────────────────
from uuid import UUID

from pydantic import BaseModel

from app.models.teacher import TeacherStatus


class TeacherCreate(BaseModel):
    subject: str
    school: str | None = None
    qualifications: dict | None = None
    classes: dict | None = None
    bio: str | None = None


class TeacherResponse(BaseModel):
    id: UUID
    user_id: UUID
    subject: str
    school: str | None
    qualifications: dict | None
    classes: dict | None
    bio: str | None
    status: TeacherStatus

    model_config = {"from_attributes": True}


class TeacherValidateRequest(BaseModel):
    action: str  # "validate" | "reject" | "suspend"
