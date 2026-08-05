# ──────────────────────────────────────────────
# Schémas Pydantic — Téléconsultation par lien
# ──────────────────────────────────────────────
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.teleconsult import TeleconsultStatus


class TeleconsultLinkRequest(BaseModel):
    """Le patient crée un lien de session."""
    patient_id: str = Field(min_length=1)          # walletId patient
    patient_name: Optional[str] = None
    doctor_wallet_id: Optional[str] = None         # si médecin connu
    doctor_name: Optional[str] = None
    doctor_specialty: Optional[str] = None
    amount_um: Optional[float] = Field(default=0, ge=0)   # honoraires convenus


class TeleconsultLinkResponse(BaseModel):
    token: str
    link: str
    expires_at: datetime
    ttl_minutes: int


class TeleconsultAcceptRequest(BaseModel):
    """Le médecin s'identifie et accepte."""
    doctor_wallet_id: Optional[str] = None
    doctor_name: Optional[str] = None
    doctor_license: Optional[str] = None


class TeleconsultInfoResponse(BaseModel):
    token: str
    patient_id: str
    patient_name: Optional[str]
    doctor_name: Optional[str]
    amount_um: float
    status: TeleconsultStatus
    expires_at: datetime
    created_at: datetime
