# ──────────────────────────────────────────────
# API Teleconsult — Lien patient → médecin (diaspora)
# ──────────────────────────────────────────────
# Flux :
#   1. Patient : POST /teleconsult/link → token de session (30 min)
#   2. Patient : partage https://vitalka.health/t/{token} (WhatsApp/SMS)
#   3. Médecin (navigateur) : GET /teleconsult/{token} → valide la session
#   4. Médecin : POST /teleconsult/{token}/accept → s'identifie, ouvre
#   5. Consultation WebRTC (page standalone)
#   6. Patient : POST /teleconsult/{token}/pay → paie en UM
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_client_info, log_audit, ClientInfo
from app.models import TeleconsultSession, TeleconsultStatus
from app.schemas.wallet import resolve_wallet_id
from app.schemas.teleconsult import (
    TeleconsultLinkRequest, TeleconsultLinkResponse,
    TeleconsultInfoResponse, TeleconsultAcceptRequest,
)

log = None
router = APIRouter(prefix="/teleconsult", tags=["Teleconsult"])

LINK_TTL_MINUTES = 30


def _generate_token() -> str:
    """Token de session : 32 chars aléatoires sécurisés."""
    return secrets.token_hex(16)


@router.post("/link", response_model=TeleconsultLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_link(
    data: TeleconsultLinkRequest,
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Le patient crée un lien de session à partager avec son médecin."""
    patient_uuid = resolve_wallet_id(data.patient_id)
    token = _generate_token()
    session = TeleconsultSession(
        id=uuid4(),
        token=token,
        patient_id=patient_uuid,
        patient_name=data.patient_name,
        doctor_wallet_id=data.doctor_wallet_id,
        doctor_name=data.doctor_name,
        amount_um=data.amount_um or 0,
        status=TeleconsultStatus.PENDING,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=LINK_TTL_MINUTES),
        metadata_json={"doctor_specialty": data.doctor_specialty} if data.doctor_specialty else None,
    )
    db.add(session)
    await log_audit(db, "teleconsult.link_created", "teleconsult_session",
                    resource_id=session.id, client=client,
                    metadata={"patient": str(patient_uuid),
                              "doctor": data.doctor_wallet_id or "any",
                              "amount_um": data.amount_um or 0})
    await db.commit()
    await db.refresh(session)
    return TeleconsultLinkResponse(
        token=token,
        link=f"https://vitalka.health/t/{token}",
        expires_at=session.expires_at,
        ttl_minutes=LINK_TTL_MINUTES,
    )


@router.get("/{token}", response_model=TeleconsultInfoResponse)
async def get_session(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Le médecin valide le lien reçu (clique → page de consultation)."""
    result = await db.execute(
        select(TeleconsultSession).where(TeleconsultSession.token == token)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable (lien invalide)")

    # Expiration (SQLite ne stocke pas le timezone → on compare en naive)
    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    expires_naive = session.expires_at.replace(tzinfo=None) if session.expires_at.tzinfo else session.expires_at
    if session.status == TeleconsultStatus.PENDING and expires_naive < now_naive:
        session.status = TeleconsultStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=410, detail="Lien expiré — demandez un nouveau lien au patient")

    if session.status in (TeleconsultStatus.EXPIRED, TeleconsultStatus.CANCELLED):
        raise HTTPException(status_code=410, detail=f"Session {session.status.value}")

    return TeleconsultInfoResponse(
        token=session.token,
        patient_id=str(session.patient_id),
        patient_name=session.patient_name,
        doctor_name=session.doctor_name,
        amount_um=session.amount_um,
        status=session.status,
        expires_at=session.expires_at,
        created_at=session.created_at,
    )


@router.post("/{token}/accept", response_model=TeleconsultInfoResponse)
async def accept_session(
    token: str,
    data: TeleconsultAcceptRequest,
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Le médecin s'identifie (KYC) et accepte la session."""
    result = await db.execute(
        select(TeleconsultSession).where(TeleconsultSession.token == token)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")

    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    expires_naive = session.expires_at.replace(tzinfo=None) if session.expires_at.tzinfo else session.expires_at
    if session.status == TeleconsultStatus.PENDING and expires_naive < now_naive:
        session.status = TeleconsultStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=410, detail="Lien expiré")

    if session.status not in (TeleconsultStatus.PENDING, TeleconsultStatus.ACCEPTED):
        raise HTTPException(status_code=409, detail=f"Session {session.status.value}")

    session.status = TeleconsultStatus.ACCEPTED
    session.doctor_wallet_id = data.doctor_wallet_id or session.doctor_wallet_id
    session.doctor_name = data.doctor_name or session.doctor_name
    session.accepted_at = datetime.now(timezone.utc)

    await log_audit(db, "teleconsult.accepted", "teleconsult_session",
                    resource_id=session.id, client=client,
                    metadata={"doctor": data.doctor_wallet_id or "unknown",
                              "doctor_name": data.doctor_name or "unknown"})
    await db.commit()
    await db.refresh(session)

    return TeleconsultInfoResponse(
        token=session.token,
        patient_id=str(session.patient_id),
        patient_name=session.patient_name,
        doctor_name=session.doctor_name,
        amount_um=session.amount_um,
        status=session.status,
        expires_at=session.expires_at,
        created_at=session.created_at,
    )
