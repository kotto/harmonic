# ──────────────────────────────────────────────
# API Élèves — carnet d'apprentissage (jumeau des dossiers patients)
# ──────────────────────────────────────────────
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.deps import require_permission
from app.core.security import Permission
from app.models import Learner, User
from app.schemas import LearnerProfile, ProgressSyncRequest

router = APIRouter(prefix="/learners", tags=["Learners"])


async def _get_own_learner(user: User, db: AsyncSession) -> Learner | None:
    """Carnet de l'élève courant (ou de l'enfant pour un parent)."""
    return await db.scalar(select(Learner).where(Learner.user_id == user.id))


@router.get("/me", response_model=LearnerProfile)
async def get_my_learner(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    learner = await _get_own_learner(user, db)
    if learner is None:
        raise HTTPException(status_code=404, detail="Profil élève introuvable")
    return learner


@router.patch("/me", response_model=LearnerProfile)
async def update_my_learner(
    data: LearnerProfile,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    learner = await _get_own_learner(user, db)
    if learner is None:
        learner = Learner(user_id=user.id)
        db.add(learner)
    if data.level is not None:
        learner.level = data.level
    if data.school is not None:
        learner.school = data.school
    if data.parent_id is not None:
        learner.parent_id = data.parent_id
    await db.commit()
    await db.refresh(learner)
    return learner


@router.get("/progress")
async def get_progress(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Carnet d'apprentissage : unités validées, compétences, lacunes."""
    learner = await _get_own_learner(user, db)
    if learner is None:
        return {"validated_units": {}, "skills": {}, "lacunes": [], "sessions": []}
    return {
        "level": learner.level,
        "validated_units": learner.validated_units or {},
        "skills": learner.skills or {},
        "lacunes": learner.lacunes or [],
        "sessions": learner.sessions or [],
    }


@router.post("/progress/sync")
async def sync_progress(
    data: ProgressSyncRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Synchronise le carnet depuis le moteur KA (POST /api/educal/quiz/submit).
    Le carnet vit côté moteur (data/educal_progress/) ET ici (établissement).
    """
    learner = await _get_own_learner(user, db)
    if learner is None:
        learner = Learner(user_id=user.id)
        db.add(learner)
        await db.flush()

    validated = dict(learner.validated_units or {})
    skills = dict(learner.skills or {})
    sessions = list(learner.sessions or [])

    if data.reussite:
        validated[data.unit_id] = __import__("datetime").datetime.now().isoformat()[:10]
    for skill, score in data.skills.items():
        skills[skill] = max(skills.get(skill, 0.0), score)
    for lacune in data.lacunes:
        skills[lacune] = 0.0
    sessions.append({
        "unit_id": data.unit_id,
        "quiz_score": data.quiz_score,
        "exercices_score": data.exercices_score,
        "lacunes": data.lacunes,
        "date": __import__("datetime").datetime.now().isoformat(),
    })

    learner.validated_units = validated
    learner.skills = skills
    learner.lacunes = list(dict.fromkeys([*(learner.lacunes or []), *data.lacunes]))
    learner.sessions = sessions[-50:]  # historique borné
    await db.commit()
    return {"synced": True, "validated_units": len(validated), "skills": len(skills)}
