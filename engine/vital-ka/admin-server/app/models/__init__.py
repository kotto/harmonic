# ──────────────────────────────────────────────
# Models Package
# ──────────────────────────────────────────────
from app.models.config import DEFAULT_CONFIGS, SystemConfig, AuditLog
from app.models.doctor import Doctor, KYCDocument, KYCDocumentType, VerificationLog, DoctorStatus
from app.models.user import User, UserRole, UserStatus
from app.models.version import APKVersion, HologramBundle, ReleaseChannel, WebhookLog
from app.models.wallet import (
    CompteUM, TransactionUM, ConversionUM, EmissionUM,
    WalletRole, WalletStatus, TxType, TxStatus, ConversionStatus,
)
from app.models.record import MedicalRecord, RecordStatus
from app.models.teleconsult import TeleconsultSession, TeleconsultStatus

__all__ = [
    # User
    "User",
    "UserRole",
    "UserStatus",
    # Doctor
    "Doctor",
    "DoctorStatus",
    "KYCDocument",
    "KYCDocumentType",
    "VerificationLog",
    # Version
    "APKVersion",
    "HologramBundle",
    "ReleaseChannel",
    "WebhookLog",
    # Config & Audit
    "SystemConfig",
    "DEFAULT_CONFIGS",
    "AuditLog",
    # Wallet UM
    "CompteUM",
    "TransactionUM",
    "ConversionUM",
    "EmissionUM",
    "WalletRole",
    "WalletStatus",
    "TxType",
    "TxStatus",
    "ConversionStatus",
    # Dossier médical
    "MedicalRecord",
    "RecordStatus",
    # Téléconsultation
    "TeleconsultSession",
    "TeleconsultStatus",
]