# ──────────────────────────────────────────────
# API Tutorat — sessions élève-professeur (jumeau de Teleconsult)
# ──────────────────────────────────────────────
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.deps import require_permission
from app.core.security import Permission
from app.models import Learner, Teacher, TutoringSession, TutoringStatus, User
from app.schemas import TutoringCreate, TutoringResponse

router = APIRouter(prefix="/tutoring", tags=["Tutoring"])


@router.post("/sessions", response_model=TutoringResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: TutoringCreate,
    user: User = Depends(require_permission(Permission.TUTOR)),
    db: AsyncSession = Depends(get_db),
):
    """Planifie une session de tutorat entre un professeur et un élève."""
    if not await db.get(Teacher, data.teacher_id):
        raise HTTPException(status_code=404, detail="Professeur introuvable")
    if not await db.get(Learner, data.learner_id):
        raise HTTPException(status_code=404, detail="Élève introuvable")
    session = TutoringSession(**data.model_dump())
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/sessions", response_model=list[TutoringResponse])
async def list_sessions(
    teacher_id: UUID | None = None,
    learner_id: UUID | None = None,
    status_filter: TutoringStatus | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(TutoringSession).order_by(TutoringSession.created_at.desc())
    if teacher_id:
        stmt = stmt.where(TutoringSession.teacher_id == teacher_id)
    if learner_id:
        stmt = stmt.where(TutoringSession.learner_id == learner_id)
    if status_filter:
        stmt = stmt.where(TutoringSession.status == status_filter)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/sessions/{session_id}/status", response_model=TutoringResponse)
async def update_session_status(
    session_id: UUID,
    status_value: TutoringStatus,
    user: User = Depends(require_permission(Permission.TUTOR)),
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(TutoringSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")
    session.status = status_value
    await db.commit()
    await db.refresh(session)
    return session
