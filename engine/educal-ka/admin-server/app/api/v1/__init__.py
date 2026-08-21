# ──────────────────────────────────────────────
# API Router Principal
# ──────────────────────────────────────────────
from fastapi import APIRouter

from app.api.v1 import auth, teachers, learners, curriculum, tutoring, admin

api_router = APIRouter()

api_router.include_router(auth.router, tags=["Auth"])
api_router.include_router(teachers.router, tags=["Teachers"])
api_router.include_router(learners.router, tags=["Learners"])
api_router.include_router(curriculum.router, tags=["Curriculum"])
api_router.include_router(tutoring.router, tags=["Tutoring"])
api_router.include_router(admin.router, tags=["Admin"])
