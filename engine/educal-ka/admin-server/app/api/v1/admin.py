# ──────────────────────────────────────────────
# API Admin — statistiques de l'établissement
# ──────────────────────────────────────────────
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.deps import require_permission
from app.core.security import Permission
from app.models import CurriculumUnit, Learner, Teacher, TutoringSession, User

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats")
async def stats(
    admin: User = Depends(require_permission(Permission.VIEW_LEARNERS)),
    db: AsyncSession = Depends(get_db),
):
    """Indicateurs de l'établissement (jumeau du dashboard vital-ka)."""
    users = await db.scalar(select(func.count()).select_from(User))
    teachers = await db.scalar(select(func.count()).select_from(Teacher))
    learners = await db.scalar(select(func.count()).select_from(Learner))
    units = await db.scalar(select(func.count()).select_from(CurriculumUnit))
    sessions = await db.scalar(select(func.count()).select_from(TutoringSession))

    # Compétences globales (somme des skills sur les carnets)
    all_learners = (await db.execute(select(Learner))).scalars().all()
    total_skills = sum(len(l.skills or {}) for l in all_learners)
    total_validated = sum(len(l.validated_units or {}) for l in all_learners)

    return {
        "utilisateurs": users or 0,
        "professeurs": teachers or 0,
        "eleves": learners or 0,
        "unites_au_programme": units or 0,
        "sessions_tutorat": sessions or 0,
        "competences_acquises": total_skills,
        "unites_validees_total": total_validated,
    }
