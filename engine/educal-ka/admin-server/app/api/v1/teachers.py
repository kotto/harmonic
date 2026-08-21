# ──────────────────────────────────────────────
# API Professeurs — profils, validation, classes
# ──────────────────────────────────────────────
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.deps import require_permission
from app.core.security import Permission
from app.models import Teacher, TeacherStatus, User
from app.schemas import TeacherCreate, TeacherResponse, TeacherValidateRequest

router = APIRouter(prefix="/teachers", tags=["Teachers"])


@router.get("", response_model=list[TeacherResponse])
async def list_teachers(
    subject: str | None = None,
    status_filter: TeacherStatus | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.VIEW_LEARNERS)),
):
    stmt = select(Teacher).order_by(Teacher.created_at.desc())
    if subject:
        stmt = stmt.where(Teacher.subject == subject)
    if status_filter:
        stmt = stmt.where(Teacher.status == status_filter)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
async def complete_teacher_profile(
    data: TeacherCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Complète le profil professeur (matière, école, classes)."""
    result = await db.execute(select(Teacher).where(Teacher.user_id == user.id))
    teacher = result.scalar_one_or_none()
    if teacher is None:
        teacher = Teacher(user_id=user.id)
        db.add(teacher)
    teacher.subject = data.subject
    teacher.school = data.school
    teacher.qualifications = data.qualifications
    teacher.classes = data.classes
    teacher.bio = data.bio
    await db.commit()
    await db.refresh(teacher)
    return teacher


@router.post("/{teacher_id}/validate", response_model=TeacherResponse)
async def validate_teacher(
    teacher_id: UUID,
    data: TeacherValidateRequest,
    admin: User = Depends(require_permission(Permission.VALIDATE_TEACHERS)),
    db: AsyncSession = Depends(get_db),
):
    teacher = await db.get(Teacher, teacher_id)
    if not teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professeur introuvable")
    action = data.action
    if action == "validate":
        teacher.status = TeacherStatus.VALIDATED
    elif action == "reject":
        teacher.status = TeacherStatus.REJECTED
    elif action == "suspend":
        teacher.status = TeacherStatus.SUSPENDED
    else:
        raise HTTPException(status_code=400, detail="action: validate | reject | suspend")
    teacher.validated_by = admin.id
    await db.commit()
    await db.refresh(teacher)
    return teacher
