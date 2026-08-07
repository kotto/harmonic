# ──────────────────────────────────────────────
# Modèles SQLAlchemy — Wallet Unités Médicales (UM)
# ──────────────────────────────────────────────
# Économie médicale Vital Ka :
#   1 UM = 1 EUR = 655 CFA (taux fixe, non spéculatif)
#   Non-convertible pour les patients (dépenses médicales uniquement)
#   Convertible pour les prestataires (sur demande, gel des fonds)
#   Émission par opérateur télécom (partenaire technique) — HMAC signé
#   Ledger append-only, auditable
import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class WalletRole(str, enum.Enum):
    PATIENT = "patient"          # Wallet patient — non convertible
    PHARMACIE = "pharmacie"      # Prestataire — convertible
    MEDECIN = "medecin"          # Prestataire — convertible
    LABO = "labo"                # Prestataire — convertible
    SOLIDARITE = "solidarite"    # Diaspora — émetteur
    TELECOM = "telecom"          # Opérateur — émetteur (partenaire)


class WalletStatus(str, enum.Enum):
    ACTIVE = "active"
    FROZEN = "frozen"            # Gelé (conversion en attente / fraude)
    CLOSED = "closed"


class TxType(str, enum.Enum):
    EMISSION_TELECOM = "emission_telecom"      # Opérateur → patient
    SOLIDARITE_CREDIT = "solidarite_credit"    # Diaspora → patient
    PAYMENT = "payment"                        # Patient → prestataire
    TRANSFER = "transfer"                      # Patient → patient (frais 0%)
    CONVERSION = "conversion"                  # Prestataire → devise
    REFUND = "refund"                          # Remboursement


class TxStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConversionStatus(str, enum.Enum):
    PENDING = "pending"          # Gel des fonds en attente
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"


class CompteUM(Base):
    """Compte UM — le portefeuille électronique médical."""
    __tablename__ = "wallet_accounts"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), index=True, nullable=False)
    role: Mapped[WalletRole] = mapped_column(
        Enum(WalletRole, native_enum=False), nullable=False, index=True
    )
    # Identifiant public pour QR (ex: "UM-6F3A..." — ne révèle pas l'UUID interne)
    public_id: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    balance_um: Mapped[float] = mapped_column(Numeric(20, 6), default=0, nullable=False)

    # Non-convertible patient = dépenses médicales uniquement
    convertible: Mapped[bool] = mapped_column(default=False, nullable=False)
    status: Mapped[WalletStatus] = mapped_column(
        Enum(WalletStatus, native_enum=False), default=WalletStatus.ACTIVE, nullable=False
    )
    monthly_solidarite_sent: Mapped[float] = mapped_column(Numeric(20, 6), default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    transactions: Mapped[list["TransactionUM"]] = relationship(
        "TransactionUM", foreign_keys="TransactionUM.from_account",
        back_populates="from_wallet", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CompteUM {self.public_id} [{self.role}] balance={self.balance_um}>"


class TransactionUM(Base):
    """Transaction UM — ledger append-only, signée HMAC."""
    __tablename__ = "wallet_transactions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tx_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    type: Mapped[TxType] = mapped_column(Enum(TxType, native_enum=False), nullable=False, index=True)
    status: Mapped[TxStatus] = mapped_column(
        Enum(TxStatus, native_enum=False), default=TxStatus.COMPLETED, nullable=False, index=True
    )

    from_account: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("wallet_accounts.id"), nullable=True, index=True
    )
    to_account: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("wallet_accounts.id"), nullable=True, index=True
    )
    amount_um: Mapped[float] = mapped_column(Numeric(20, 6), nullable=False)
    fee_um: Mapped[float] = mapped_column(Numeric(20, 6), default=0, nullable=False)

    # Signature HMAC (générée côté client KA_BRIDGE ou serveur)
    hmac_sig: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # Référence externe (ex: ref opérateur télécom, n° ordonnance)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    from_wallet: Mapped["CompteUM"] = relationship(
        "CompteUM", foreign_keys=[from_account], back_populates="transactions"
    )

    __table_args__ = (
        Index("ix_wallet_tx_from_created", "from_account", "created_at"),
        Index("ix_wallet_tx_to_created", "to_account", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<TxUM {self.tx_id} {self.type} {self.amount_um} UM>"


class ConversionUM(Base):
    """Conversion prestataire : UM → CFA/EUR (gel des fonds en attente)."""
    __tablename__ = "wallet_conversions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("wallet_accounts.id"), nullable=False, index=True
    )
    amount_um: Mapped[float] = mapped_column(Numeric(20, 6), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="CFA", nullable=False)  # CFA | EUR
    amount_currency: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    bank_info: Mapped[dict] = mapped_column(JSONB, nullable=True)  # {iban, holder, bank}
    status: Mapped[ConversionStatus] = mapped_column(
        Enum(ConversionStatus, native_enum=False), default=ConversionStatus.PENDING, nullable=False
    )
    processed_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ConversionUM {self.amount_um} UM → {self.amount_currency} {self.currency} [{self.status}]>"


class EmissionUM(Base):
    """Émission d'UM par l'opérateur télécom (partenaire technique)."""
    __tablename__ = "wallet_emissions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    operator: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # ex: "MTN"
    operator_tx_ref: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    patient_account_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("wallet_accounts.id"), nullable=False, index=True
    )
    amount_um: Mapped[float] = mapped_column(Numeric(20, 6), nullable=False)
    # Preuve d'achat : transaction mobile money (MSISDN → ID)
    msisdn: Mapped[str | None] = mapped_column(String(30), nullable=True)
    mtn_tx_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hmac_sig: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[TxStatus] = mapped_column(
        Enum(TxStatus, native_enum=False), default=TxStatus.COMPLETED, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("operator", "operator_tx_ref", name="uq_operator_tx_ref"),
    )

    def __repr__(self) -> str:
        return f"<EmissionUM {self.operator} {self.amount_um} UM → {self.patient_account_id}>"
