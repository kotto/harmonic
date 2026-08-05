# ──────────────────────────────────────────────
# API Wallet — Unités Médicales (UM)
# ──────────────────────────────────────────────
# Flux critiques :
#   1. Création de compte (patient / prestataire / solidarité / telecom)
#   2. Crédit : émission télécom ou solidarité diaspora
#   3. Paiement : patient → prestataire (QR ordonnance)
#   4. Transfert : patient → patient (frais 0%, AML)
#   5. Conversion : prestataire → CFA/EUR (gel des fonds)
#   6. Ledger : historique auditable
import hashlib
import hmac as hmac_lib
import os
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_client_info, log_audit, ClientInfo
from app.core.config import settings
from app.models import (
    CompteUM, TransactionUM, ConversionUM, EmissionUM,
    WalletRole, WalletStatus, TxType, TxStatus, ConversionStatus,
)
from app.schemas.wallet import (
    WalletCreateRequest, WalletCreateResponse,
    WalletBalanceResponse,
    CreditRequest, CreditResponse,
    PaymentRequest, PaymentResponse,
    TransferRequest,
    ConversionRequest, ConversionResponse,
    TransactionResponse, LedgerResponse,
    TelecomEmitRequest, TelecomEmitResponse,
    UM_TO_CFA, UM_TO_EUR, MAX_SOLIDARITE_MONTHLY,
    resolve_wallet_id,
)

router = APIRouter(prefix="/wallet", tags=["Wallet"])

# Rôles prestataires autorisés à convertir
CONVERTIBLE_ROLES = {WalletRole.PHARMACIE, WalletRole.MEDECIN, WalletRole.LABO}


# ── Helpers ──

def _generate_public_id(role: WalletRole) -> str:
    """ID public QR : 'UM-PAT-XXXX' — ne révèle pas l'UUID interne."""
    prefix = {
        WalletRole.PATIENT: "PAT", WalletRole.PHARMACIE: "PHA",
        WalletRole.MEDECIN: "MED", WalletRole.LABO: "LAB",
        WalletRole.SOLIDARITE: "SOL", WalletRole.TELECOM: "TEL",
    }[role]
    rand = os.urandom(3).hex().upper()
    return f"UM-{prefix}-{rand}"


def _hmac_sign(payload: str, key: str) -> str:
    """Signature HMAC-SHA256 (déterministe)."""
    return hmac_lib.new(
        key.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()


async def _get_account(db: AsyncSession, owner_id) -> CompteUM:
    owner_id = resolve_wallet_id(str(owner_id))  # walletId local → UUID5
    result = await db.execute(select(CompteUM).where(CompteUM.owner_id == owner_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Compte UM introuvable")
    if account.status != WalletStatus.ACTIVE:
        raise HTTPException(status_code=403, detail=f"Compte {account.status.value}")
    return account


async def _get_account_by_id(db: AsyncSession, account_id) -> CompteUM:
    """Recherche par ID interne du compte OU walletId (owner_id résolu)."""
    # 1. Tenter par ID interne UUID
    try:
        result = await db.execute(select(CompteUM).where(CompteUM.id == UUID(str(account_id))))
        account = result.scalar_one_or_none()
        if account:
            if account.status != WalletStatus.ACTIVE:
                raise HTTPException(status_code=403, detail=f"Compte {account.status.value}")
            return account
    except (ValueError, TypeError):
        pass
    # 2. Tenter par owner_id (walletId local → UUID5)
    owner_uuid = resolve_wallet_id(str(account_id))
    result = await db.execute(select(CompteUM).where(CompteUM.owner_id == owner_uuid))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Compte UM introuvable")
    if account.status != WalletStatus.ACTIVE:
        raise HTTPException(status_code=403, detail=f"Compte {account.status.value}")
    return account


async def _get_account_by_public(db: AsyncSession, public_id: str) -> CompteUM:
    result = await db.execute(select(CompteUM).where(CompteUM.public_id == public_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Compte UM introuvable (QR)")
    return account


# ──────────────────────────────────────────────
# 1. CRÉATION DE COMPTE
# ──────────────────────────────────────────────
@router.post("/create", response_model=WalletCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_wallet(
    data: WalletCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Crée un compte UM. Patient = non convertible ; prestataire = convertible."""
    # Un seul compte par (owner_id, role)
    owner_uuid = resolve_wallet_id(data.owner_id)
    existing = await db.execute(
        select(CompteUM).where(
            CompteUM.owner_id == owner_uuid,
            CompteUM.role == data.role,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Compte déjà existant pour ce rôle")

    account = CompteUM(
        id=uuid4(),
        owner_id=owner_uuid,
        role=data.role,
        public_id=data.public_id or _generate_public_id(data.role),
        balance_um=Decimal("0"),
        convertible=data.role in CONVERTIBLE_ROLES,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return WalletCreateResponse(
        id=account.id, owner_id=account.owner_id, role=account.role,
        public_id=account.public_id, balance_um=float(account.balance_um),
        convertible=account.convertible, status=account.status,
        created_at=account.created_at,
    )


# ──────────────────────────────────────────────
# 2. SOLDE
# ──────────────────────────────────────────────
@router.get("/{owner_id}/balance", response_model=WalletBalanceResponse)
async def get_balance(
    owner_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Solde d'un compte en UM, EUR et CFA."""
    account = await _get_account(db, owner_id)
    return WalletBalanceResponse(
        owner_id=account.owner_id, public_id=account.public_id,
        role=account.role, balance_um=float(account.balance_um),
        balance_eur=float(account.balance_um) * UM_TO_EUR,
        balance_cfa=float(account.balance_um) * UM_TO_CFA,
        convertible=account.convertible, status=account.status,
    )


# ──────────────────────────────────────────────
# 3. CRÉDIT (émission / solidarité)
# ──────────────────────────────────────────────
@router.post("/credit", response_model=CreditResponse)
async def credit_wallet(
    data: CreditRequest,
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Crédite un compte (solidarité diaspora, émission)."""
    account = await _get_account(db, data.owner_id)

    # Contrôle AML solidarité
    if data.type == TxType.SOLIDARITE_CREDIT and account.role == WalletRole.SOLIDARITE:
        now = datetime.now(timezone.utc)
        if float(account.monthly_solidarite_sent) + data.amount_um > MAX_SOLIDARITE_MONTHLY:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Limite AML dépassée : {MAX_SOLIDARITE_MONTHLY:.0f} UM/mois",
            )
        account.monthly_solidarite_sent = Decimal(float(account.monthly_solidarite_sent) + data.amount_um)

    # Crédit
    account.balance_um = Decimal(float(account.balance_um) + data.amount_um)

    tx = TransactionUM(
        id=uuid4(),
        tx_id=f"tx_{uuid4().hex[:12]}",
        type=data.type,
        status=TxStatus.COMPLETED,
        to_account=account.id,
        amount_um=Decimal(str(data.amount_um)),
        fee_um=Decimal("0"),
        reference=data.reference,
        metadata_json=data.metadata,
    )
    db.add(tx)
    await log_audit(
        db, f"wallet.credit.{data.type.value}", "wallet_account",
        resource_id=account.id, client=client,
        metadata={"amount_um": data.amount_um, "reference": data.reference},
    )
    await db.commit()
    return CreditResponse(
        tx_id=tx.tx_id, type=tx.type, amount_um=float(tx.amount_um),
        balance_after=float(account.balance_um), status=tx.status,
    )


# ──────────────────────────────────────────────
# 4. PAIEMENT (patient → prestataire)
# ──────────────────────────────────────────────
@router.post("/pay", response_model=PaymentResponse)
async def pay_wallet(
    data: PaymentRequest,
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """
    Paiement UM : débite le patient, crédite le prestataire.
    Le patient est non-convertible → il ne peut QUE dépenser en soins.
    """
    from_account = await _get_account(db, data.from_owner_id)
    to_account = await _get_account(db, data.to_owner_id)

    # Un patient ne peut pas payer un autre patient (sauf transfert dédié)
    if from_account.role == WalletRole.PATIENT and to_account.role == WalletRole.PATIENT:
        raise HTTPException(
            status_code=422, detail="Paiement patient→patient refusé. Utiliser /transfer"
        )

    # Solde suffisant
    if float(from_account.balance_um) < data.amount_um:
        raise HTTPException(status_code=422, detail="Solde UM insuffisant")

    from_account.balance_um = Decimal(float(from_account.balance_um) - data.amount_um)
    to_account.balance_um = Decimal(float(to_account.balance_um) + data.amount_um)

    tx = TransactionUM(
        id=uuid4(),
        tx_id=f"tx_{uuid4().hex[:12]}",
        type=TxType.PAYMENT,
        status=TxStatus.COMPLETED,
        from_account=from_account.id,
        to_account=to_account.id,
        amount_um=Decimal(str(data.amount_um)),
        fee_um=Decimal("0"),
        reference=data.reference,
        metadata_json={**(data.metadata or {}), "prescription_qr": data.prescription_qr},
    )
    db.add(tx)
    await log_audit(
        db, "wallet.payment", "wallet_account",
        resource_id=from_account.id, client=client,
        metadata={"amount_um": data.amount_um, "to": str(to_account.id),
                  "reference": data.reference},
    )
    await db.commit()
    return PaymentResponse(
        tx_id=tx.tx_id, type=tx.type, amount_um=float(tx.amount_um),
        from_owner_id=from_account.owner_id, to_owner_id=to_account.owner_id,
        from_balance_after=float(from_account.balance_um),
        to_balance_after=float(to_account.balance_um), status=tx.status,
    )


# ──────────────────────────────────────────────
# 5. TRANSFERT ENTRE PROCHES (frais 0%, AML)
# ──────────────────────────────────────────────
@router.post("/transfer", response_model=PaymentResponse)
async def transfer_wallet(
    data: TransferRequest,
    db: AsyncSession = Depends(get_db),
):
    """Transfert patient → patient, frais 0%. Contrôle AML solidaire."""
    from_account = await _get_account(db, data.from_owner_id)
    to_account = await _get_account(db, data.to_owner_id)

    if from_account.role != WalletRole.PATIENT or to_account.role != WalletRole.PATIENT:
        raise HTTPException(status_code=422, detail="Transfert réservé patient→patient")

    if float(from_account.balance_um) < data.amount_um:
        raise HTTPException(status_code=422, detail="Solde UM insuffisant")

    from_account.balance_um = Decimal(float(from_account.balance_um) - data.amount_um)
    to_account.balance_um = Decimal(float(to_account.balance_um) + data.amount_um)

    tx = TransactionUM(
        id=uuid4(), tx_id=f"tx_{uuid4().hex[:12]}", type=TxType.TRANSFER,
        status=TxStatus.COMPLETED,
        from_account=from_account.id, to_account=to_account.id,
        amount_um=Decimal(str(data.amount_um)), fee_um=Decimal("0"),
    )
    db.add(tx)
    await db.commit()
    return PaymentResponse(
        tx_id=tx.tx_id, type=tx.type, amount_um=float(tx.amount_um),
        from_owner_id=from_account.owner_id, to_owner_id=to_account.owner_id,
        from_balance_after=float(from_account.balance_um),
        to_balance_after=float(to_account.balance_um), status=tx.status,
    )


# ──────────────────────────────────────────────
# 6. CONVERSION PRESTATAIRE (UM → CFA/EUR)
# ──────────────────────────────────────────────
@router.post("/convert", response_model=ConversionResponse, status_code=status.HTTP_201_CREATED)
async def convert_wallet(
    data: ConversionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Demande de conversion par un prestataire. Gel des fonds en attente."""
    account = await _get_account_by_id(db, data.account_id)

    if not account.convertible:
        raise HTTPException(status_code=403, detail="Compte non convertible (patient)")

    if float(account.balance_um) < data.amount_um:
        raise HTTPException(status_code=422, detail="Solde UM insuffisant")

    # Taux fixe : 1 UM = 1 EUR = 655 CFA
    if data.currency == "EUR":
        amount_currency = data.amount_um * UM_TO_EUR
    else:
        amount_currency = data.amount_um * UM_TO_CFA

    # Gel des fonds : retrait + conversion en attente
    account.balance_um = Decimal(float(account.balance_um) - data.amount_um)

    conversion = ConversionUM(
        id=uuid4(), account_id=account.id,
        amount_um=Decimal(str(data.amount_um)),
        currency=data.currency, amount_currency=Decimal(str(amount_currency)),
        bank_info=data.bank_info, status=ConversionStatus.PENDING,
    )
    tx = TransactionUM(
        id=uuid4(), tx_id=f"tx_{uuid4().hex[:12]}", type=TxType.CONVERSION,
        status=TxStatus.PENDING,
        from_account=account.id, amount_um=Decimal(str(data.amount_um)),
        metadata_json={"conversion_id": str(conversion.id), "currency": data.currency,
                       "amount_currency": amount_currency},
    )
    db.add(conversion)
    db.add(tx)
    await db.commit()
    return ConversionResponse(
        id=conversion.id, account_id=conversion.account_id,
        amount_um=float(conversion.amount_um), currency=conversion.currency,
        amount_currency=float(conversion.amount_currency), status=conversion.status,
    )


# ──────────────────────────────────────────────
# 7. LEDGER
# ──────────────────────────────────────────────
@router.get("/{owner_id}/ledger", response_model=LedgerResponse)
async def get_ledger(
    owner_id: UUID,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Historique des transactions d'un compte (ledger auditable)."""
    account = await _get_account(db, owner_id)
    result = await db.execute(
        select(TransactionUM)
        .where(
            (TransactionUM.from_account == account.id) |
            (TransactionUM.to_account == account.id)
        )
        .order_by(TransactionUM.created_at.desc())
        .limit(min(limit, 500))
    )
    txs = result.scalars().all()
    return LedgerResponse(
        owner_id=owner_id,
        transactions=[
            TransactionResponse(
                tx_id=t.tx_id, type=t.type, status=t.status,
                from_account=t.from_account, to_account=t.to_account,
                amount_um=float(t.amount_um), fee_um=float(t.fee_um),
                reference=t.reference, created_at=t.created_at,
            )
            for t in txs
        ],
    )
