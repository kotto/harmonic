# ──────────────────────────────────────────────
# Schémas Élèves (carnet d'apprentissage)
# ──────────────────────────────────────────────
from uuid import UUID

from pydantic import BaseModel


class LearnerProfile(BaseModel):
    id: UUID | None = None  # id de l'enregistrement Learner (≠ id user)
    level: str | None = None
    school: str | None = None
    parent_id: UUID | None = None

    model_config = {"from_attributes": True}


class ProgressSyncRequest(BaseModel):
    """Payload synchronisé depuis POST /api/educal/quiz/submit du moteur."""
    unit_id: str
    quiz_score: float | None = None
    exercices_score: float | None = None
    reussite: bool = False
    lacunes: list[str] = []
    skills: dict[str, float] = {}
    validated_units: dict[str, str] = {}
