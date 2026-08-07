# ──────────────────────────────────────────────
# API Router Principal
# ──────────────────────────────────────────────
from fastapi import APIRouter

from app.api.v1 import auth, doctors, versions, admin, wallet, telecom, records, teleconsult

api_router = APIRouter()

# NOTE: les routers ont déjà leur prefix interne (ex: APIRouter(prefix="/auth"))
api_router.include_router(auth.router, tags=["Auth"])
api_router.include_router(doctors.router, tags=["Doctors"])
api_router.include_router(versions.router, tags=["Versions"])
api_router.include_router(admin.router, tags=["Admin"])
api_router.include_router(wallet.router, tags=["Wallet"])
api_router.include_router(telecom.router, tags=["Telecom"])
api_router.include_router(records.router, tags=["Records"])
api_router.include_router(teleconsult.router, tags=["Teleconsult"])