# ──────────────────────────────────────────────
# Schémas Tutorat
# ──────────────────────────────────────────────
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.tutoring import TutoringStatus


class TutoringCreate(BaseModel):
    teacher_id: UUID
    learner_id: UUID
    unit_id: str | None = None
    scheduled_at: datetime | None = None
    notes: str | None = None


class TutoringResponse(BaseModel):
    id: UUID
    teacher_id: UUID
    learner_id: UUID
    unit_id: str | None
    scheduled_at: datetime | None
    status: TutoringStatus
    notes: str | None

    model_config = {"from_attributes": True}
