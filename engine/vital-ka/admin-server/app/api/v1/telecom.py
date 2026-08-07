# ──────────────────────────────────────────────
# API Telecom — Émission d'Unités Médicales
# ──────────────────────────────────────────────
# Partenariat opérateur mobile (ex: MTN) :
#   L'opérateur émet des UM après achat mobile money.
#   Authentification : clé API opérateur + signature HMAC du payload.
#   Idempotence : operator_tx_ref unique → pas de double émission.
import hashlib
import hmac as hmac_lib
import os
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_client_info, log_audit, ClientInfo
from app.core.config import settings
from app.models import CompteUM, TransactionUM, EmissionUM, WalletRole, TxType, TxStatus
from app.schemas.wallet import TelecomEmitRequest, TelecomEmitResponse

router = APIRouter(prefix="/telecom", tags=["Telecom"])


def _verify_operator_hmac(payload: str, provided_sig: str, secret: str) -> bool:
    """Vérifie la signature HMAC-SHA256 de l'opérateur."""
    expected = hmac_lib.new(
        secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    return hmac_lib.compare_digest(expected, provided_sig)


# Clé opérateur depuis la config (à définir en prod : settings.telecom_secret)
def _get_operator_secret(operator: str) -> str:
    secret = getattr(settings, "telecom_secret", None)
    if not secret:
        # Fallback dev : clé par opérateur en clair (⚠️ à remplacer en prod)
        secret = os.environ.get("TELECOM_SECRET", "dev-telecom-key-change-me")
    return f"{secret}:{operator}"


@router.post("/emit", response_model=TelecomEmitResponse)
async def telecom_emit(
    data: TelecomEmitRequest,
    request: Request,
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """
    Émission d'UM par l'opérateur (achat mobile money → crédit patient).

    Authentification :
      Header 'X-Operator-Signature': HMAC-SHA256(
        f"{operator_tx_ref}|{patient_public_id}|{amount_um}", secret
      )
    Idempotence : operator_tx_ref unique → 409 si déjà traité.
    """
    # 1. Vérifier la signature opérateur
    sig = request.headers.get("X-Operator-Signature")
    payload = f"{data.operator_tx_ref}|{data.patient_public_id}|{data.amount_um}"
    secret = _get_operator_secret(data.operator)
    if sig and not _verify_operator_hmac(payload, sig, secret):
        raise HTTPException(status_code=401, detail="Signature opérateur invalide")

    # 2. Idempotence : la ref opérateur ne doit pas déjà exister
    existing = await db.execute(
        select(EmissionUM).where(EmissionUM.operator_tx_ref == data.operator_tx_ref)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Transaction opérateur déjà traitée")

    # 3. Trouver le compte patient par public_id (QR)
    result = await db.execute(
        select(CompteUM).where(CompteUM.public_id == data.patient_public_id)
    )
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Compte patient introuvable (QR)")
    if patient.role != WalletRole.PATIENT:
        raise HTTPException(status_code=422, detail="Le compte cible n'est pas un patient")

    # 4. Créditer le patient + enregistrer l'émission
    patient.balance_um = Decimal(float(patient.balance_um) + data.amount_um)

    emission = EmissionUM(
        id=uuid4(), operator=data.operator,
        operator_tx_ref=data.operator_tx_ref,
        patient_account_id=patient.id,
        amount_um=Decimal(str(data.amount_um)),
        msisdn=data.msisdn, mtn_tx_id=data.mtn_tx_id,
        hmac_sig=sig, status=TxStatus.COMPLETED,
    )
    tx = TransactionUM(
        id=uuid4(), tx_id=f"tx_{uuid4().hex[:12]}",
        type=TxType.EMISSION_TELECOM, status=TxStatus.COMPLETED,
        to_account=patient.id, amount_um=Decimal(str(data.amount_um)),
        fee_um=Decimal("0"), reference=data.operator_tx_ref,
        metadata_json={"operator": data.operator, "msisdn": data.msisdn,
                       "mtn_tx_id": data.mtn_tx_id},
    )
    db.add(emission)
    db.add(tx)
    await log_audit(
        db, "telecom.emit", "wallet_emission",
        resource_id=emission.id, client=client,
        metadata={"operator": data.operator, "amount_um": data.amount_um,
                  "ref": data.operator_tx_ref, "patient": data.patient_public_id},
    )
    await db.commit()

    return TelecomEmitResponse(
        success=True, tx_id=tx.tx_id,
        patient_public_id=patient.public_id,
        amount_um=data.amount_um,
        operator_tx_ref=data.operator_tx_ref,
        message=f"{data.amount_um:g} UM crédités sur le portefeuille santé",
    )
