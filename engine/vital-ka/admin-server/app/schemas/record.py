# ──────────────────────────────────────────────
# Schémas Pydantic — Dossier Médical
# ──────────────────────────────────────────────
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MedicalRecordCreate(BaseModel):
    """Création / mise à jour complète du dossier patient."""
    patient_id: str = Field(min_length=1)   # walletId patient
    profile: Optional[dict] = None
    antecedents: Optional[list] = None
    allergies: Optional[list] = None
    vaccines: Optional[list] = None
    medications: Optional[list] = None
    vitals: Optional[list] = None
    appointments: Optional[list] = None
    analyses: Optional[list] = None
    ordonnances: Optional[list] = None


class MedicalRecordUpdate(BaseModel):
    """Mise à jour partielle (merge)."""
    profile: Optional[dict] = None
    antecedents: Optional[list] = None
    allergies: Optional[list] = None
    vaccines: Optional[list] = None
    medications: Optional[list] = None
    vitals: Optional[list] = None
    appointments: Optional[list] = None
    analyses: Optional[list] = None
    ordonnances: Optional[list] = None


class MedicalRecordResponse(BaseModel):
    patient_id: UUID
    profile: dict
    antecedents: list
    allergies: list
    vaccines: list
    medications: list
    vitals: list
    appointments: list
    analyses: list
    ordonnances: list
    updated_at: datetime
