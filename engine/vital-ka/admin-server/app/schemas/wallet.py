# ──────────────────────────────────────────────
# Schémas Pydantic — Wallet UM
# ──────────────────────────────────────────────
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.wallet import (
    WalletRole, WalletStatus, TxType, TxStatus, ConversionStatus,
)

# ── Constantes économiques ──
UM_TO_EUR = 1.0
UM_TO_CFA = 655.0
MAX_SOLIDARITE_MONTHLY = 5000.0  # limite anti-blanchiment


# ── Création de compte ──
class WalletCreateRequest(BaseModel):
    owner_id: UUID
    role: WalletRole
    public_id: str = Field(min_length=5, max_length=40)


class WalletCreateResponse(BaseModel):
    id: UUID
    owner_id: UUID
    role: WalletRole
    public_id: str
    balance_um: float
    convertible: bool
    status: WalletStatus
    created_at: datetime


# ── Solde ──
class WalletBalanceResponse(BaseModel):
    owner_id: UUID
    public_id: str
    role: WalletRole
    balance_um: float
    balance_eur: float
    balance_cfa: float
    convertible: bool
    status: WalletStatus


# ── Crédit (émission / solidarité) ──
class CreditRequest(BaseModel):
    owner_id: UUID
    amount_um: float = Field(gt=0)
    type: TxType = TxType.SOLIDARITE_CREDIT
    reference: Optional[str] = None
    metadata: Optional[dict] = None


class CreditResponse(BaseModel):
    tx_id: str
    type: TxType
    amount_um: float
    balance_after: float
    status: TxStatus


# ── Paiement (patient → prestataire) ──
class PaymentRequest(BaseModel):
    from_owner_id: UUID
    to_owner_id: UUID
    amount_um: float = Field(gt=0)
    reference: Optional[str] = None          # ex: n° ordonnance
    prescription_qr: Optional[str] = None    # contenu QR de l'ordonnance
    metadata: Optional[dict] = None


class PaymentResponse(BaseModel):
    tx_id: str
    type: TxType
    amount_um: float
    from_owner_id: UUID
    to_owner_id: UUID
    from_balance_after: float
    to_balance_after: float
    status: TxStatus


# ── Transfert entre proches (frais 0%) ──
class TransferRequest(BaseModel):
    from_owner_id: UUID
    to_owner_id: UUID
    amount_um: float = Field(gt=0)


# ── Conversion prestataire ──
class ConversionRequest(BaseModel):
    account_id: UUID
    amount_um: float = Field(gt=0)
    currency: str = Field(default="CFA", pattern="^(CFA|EUR)$")
    bank_info: Optional[dict] = None


class ConversionResponse(BaseModel):
    id: UUID
    account_id: UUID
    amount_um: float
    currency: str
    amount_currency: float
    status: ConversionStatus


# ── Ledger ──
class TransactionResponse(BaseModel):
    tx_id: str
    type: TxType
    status: TxStatus
    from_account: Optional[UUID]
    to_account: Optional[UUID]
    amount_um: float
    fee_um: float
    reference: Optional[str]
    created_at: datetime


class LedgerResponse(BaseModel):
    owner_id: UUID
    transactions: list[TransactionResponse]


# ── Émission télécom ──
class TelecomEmitRequest(BaseModel):
    operator: str = Field(min_length=2, max_length=50)
    operator_key: str = Field(min_length=8)       # clé API opérateur (HMAC)
    patient_public_id: str = Field(min_length=5, max_length=40)
    amount_um: float = Field(gt=0, le=10000)
    operator_tx_ref: str = Field(min_length=5, max_length=100)
    msisdn: Optional[str] = None                  # n° mobile money
    mtn_tx_id: Optional[str] = None               # ref transaction MTN


class TelecomEmitResponse(BaseModel):
    success: bool
    tx_id: Optional[str]
    patient_public_id: str
    amount_um: float
    operator_tx_ref: str
    message: str
