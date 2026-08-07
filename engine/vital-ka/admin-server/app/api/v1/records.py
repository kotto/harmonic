# ──────────────────────────────────────────────
# API Records — Dossier Médical Patient
# ──────────────────────────────────────────────
# Le médecin scanne le QR patient → télécharge le dossier via /records.
# Le patient synchronise son dossier depuis l'app.
import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_client_info, log_audit, ClientInfo
from app.models import MedicalRecord, RecordStatus
from app.schemas.record import (
    MedicalRecordCreate, MedicalRecordUpdate, MedicalRecordResponse,
)
from app.schemas.wallet import resolve_wallet_id

log = logging.getLogger(__name__)
router = APIRouter(prefix="/records", tags=["Records"])


def _to_response(record: MedicalRecord) -> MedicalRecordResponse:
    return MedicalRecordResponse(
        patient_id=record.patient_id,
        profile=record.profile or {},
        antecedents=record.antecedents or [],
        allergies=record.allergies or [],
        vaccines=record.vaccines or [],
        medications=record.medications or [],
        vitals=record.vitals or [],
        appointments=record.appointments or [],
        analyses=record.analyses or [],
        ordonnances=record.ordonnances or [],
        updated_at=record.updated_at,
    )


@router.get("/{patient_id}", response_model=MedicalRecordResponse)
async def get_record(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Récupère le dossier médical d'un patient (par walletId ou UUID)."""
    owner_uuid = resolve_wallet_id(patient_id)
    result = await db.execute(
        select(MedicalRecord).where(MedicalRecord.patient_id == owner_uuid)
    )
    record = result.scalar_one_or_none()
    if not record or record.status != RecordStatus.ACTIVE:
        raise HTTPException(status_code=404, detail="Dossier médical introuvable")
    return _to_response(record)


@router.post("", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_record(
    data: MedicalRecordCreate,
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Crée le dossier médical d'un patient (première synchronisation)."""
    owner_uuid = resolve_wallet_id(data.patient_id)
    existing = await db.execute(
        select(MedicalRecord).where(MedicalRecord.patient_id == owner_uuid)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Dossier déjà existant — utiliser PUT")

    record = MedicalRecord(
        id=uuid4(),
        patient_id=owner_uuid,
        profile=data.profile or {},
        antecedents=data.antecedents or [],
        allergies=data.allergies or [],
        vaccines=data.vaccines or [],
        medications=data.medications or [],
        vitals=data.vitals or [],
        appointments=data.appointments or [],
        analyses=data.analyses or [],
        ordonnances=data.ordonnances or [],
    )
    db.add(record)
    await log_audit(db, "record.create", "medical_record",
                    resource_id=record.id, client=client,
                    metadata={"patient": str(owner_uuid)})
    await db.commit()
    await db.refresh(record)
    return _to_response(record)


@router.put("/{patient_id}", response_model=MedicalRecordResponse)
async def update_record(
    patient_id: str,
    data: MedicalRecordUpdate,
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Met à jour le dossier (merge partiel : les champs fournis remplacent)."""
    owner_uuid = resolve_wallet_id(patient_id)
    result = await db.execute(
        select(MedicalRecord).where(MedicalRecord.patient_id == owner_uuid)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Dossier médical introuvable")

    updates = data.model_dump(exclude_none=True)
    for key, value in updates.items():
        setattr(record, key, value)

    await log_audit(db, "record.update", "medical_record",
                    resource_id=record.id, client=client,
                    metadata={"patient": str(owner_uuid), "fields": list(updates.keys())})
    await db.commit()
    await db.refresh(record)
    return _to_response(record)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Archive le dossier (soft delete — droit à l'effacement RGPD)."""
    owner_uuid = resolve_wallet_id(patient_id)
    result = await db.execute(
        select(MedicalRecord).where(MedicalRecord.patient_id == owner_uuid)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Dossier médical introuvable")
    record.status = RecordStatus.ARCHIVED
    await db.commit()
