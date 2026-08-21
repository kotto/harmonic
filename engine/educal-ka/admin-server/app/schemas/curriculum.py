# ──────────────────────────────────────────────
# Schémas Programme (unités éducatives)
# ──────────────────────────────────────────────
from uuid import UUID

from pydantic import BaseModel

from app.models.curriculum import UnitStatus


class UnitSyncItem(BaseModel):
    unit_id: str
    discipline: str
    niveau: str
    programme: str = ""
    titre: str
    version: int = 1
    facts_count: int = 0
    quality_score: float = 0.0
    hologramme_associe: str | None = None


class UnitResponse(BaseModel):
    id: UUID
    unit_id: str
    discipline: str
    niveau: str
    programme: str | None
    titre: str
    version: int
    facts_count: int
    quality_score: float
    status: UnitStatus
    hologramme_associe: str | None

    model_config = {"from_attributes": True}
