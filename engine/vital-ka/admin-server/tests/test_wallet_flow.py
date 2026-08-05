# ──────────────────────────────────────────────
# Test d'intégration — Wallet UM (SQLite en mémoire)
# ──────────────────────────────────────────────
# Vérifie le flux complet de l'économie médicale :
#   émission télécom → solidarité → paiement → conversion → ledger
#
# Usage : python -m tests.test_wallet_flow
import asyncio
import os
import sys
from pathlib import Path

# Chemin racine du projet
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Base SQLite temporaire (fichier effacé à chaque exécution — évite la
# persistance des index entre connexions :memory:)
_TEST_DB = ROOT / "tests" / "test_wallet_flow.db"
if _TEST_DB.exists():
    _TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB.as_posix()}"
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("MINIO_ACCESS_KEY", "minioadmin")
os.environ.setdefault("MINIO_SECRET_KEY", "changeme")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-prod")
os.environ.setdefault("TELECOM_SECRET", "test-telecom-secret")


# Mock create_async_engine pour SQLite (les kwargs pool_size sont Postgres-only)
from unittest.mock import patch
from sqlalchemy.ext.asyncio import create_async_engine as _real_create
from sqlalchemy.pool import StaticPool


def _sqlite_engine(url, **kwargs):
    kwargs.pop("pool_size", None)
    kwargs.pop("max_overflow", None)
    kwargs.pop("pool_pre_ping", None)
    kwargs.pop("pool_recycle", None)
    kwargs.pop("echo", None)
    return _real_create(url, poolclass=StaticPool, **kwargs)


# Compilateur SQLite pour PG_UUID → String(36) et JSONB → JSON
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.types import TypeDecorator, String


class SQLiteUUID(TypeDecorator):
    """PG_UUID compatible SQLite : stocké en String(36)."""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return str(value) if value is not None else None

    def process_result_value(self, value, dialect):
        from uuid import UUID
        return UUID(value) if value else None


with patch("sqlalchemy.ext.asyncio.create_async_engine", _sqlite_engine), \
     patch("sqlalchemy.dialects.postgresql.UUID", SQLiteUUID), \
     patch("sqlalchemy.dialects.postgresql.JSONB", SQLiteJSON):
    from app.core.database import Base, engine, async_session_maker
    from app.models import CompteUM, TransactionUM, ConversionUM, EmissionUM
    from app.schemas.wallet import (
        WalletCreateRequest, CreditRequest, PaymentRequest,
        TelecomEmitRequest, ConversionRequest,
    )
    from app.api.v1.wallet import (
        create_wallet, credit_wallet, pay_wallet,
        get_balance, convert_wallet, get_ledger,
    )
    from app.api.v1.telecom import telecom_emit


async def main() -> int:
    from uuid import uuid4
    print(">>> main() démarre")

    # 1. Créer les tables wallet (uniquement les nôtres — évite les conflits
    #    d'index avec les anciennes tables lors des runs successifs)
    from app.models.config import AuditLog
    print(">>> création tables...")
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=[
                    CompteUM.__table__,
                    TransactionUM.__table__,
                    ConversionUM.__table__,
                    EmissionUM.__table__,
                    AuditLog.__table__,
                ],
            )
        )

    ok = 0
    total = 8

    # Mock Request FastAPI pour l'émission télécom
    class _FakeRequest:
        def __init__(self, sig=None):
            self.headers = {"X-Operator-Signature": sig} if sig else {}

    print(">>> session ouverte")
    async with async_session_maker() as db:
        patient_id = uuid4()
        pharma_id = uuid4()
        med_id = uuid4()

        # 2. Création des comptes
        patient = await create_wallet(
            WalletCreateRequest(owner_id=patient_id, role="patient", public_id="UM-PAT-TEST01"), db)
        assert patient.convertible is False, "Le patient ne doit PAS être convertible"
        print(f"✅ Compte patient : {patient.public_id} (convertible={patient.convertible})")
        ok += 1

        pharma = await create_wallet(
            WalletCreateRequest(owner_id=pharma_id, role="pharmacie", public_id="UM-PHA-TEST01"), db)
        assert pharma.convertible is True, "La pharmacie DOIT être convertible"
        print(f"✅ Compte pharmacie : {pharma.public_id} (convertible={pharma.convertible})")
        ok += 1

        # 3. Émission télécom (opérateur MTN)
        emit = await telecom_emit(TelecomEmitRequest(
            operator="MTN", operator_key="test-key",
            patient_public_id="UM-PAT-TEST01",
            amount_um=5000, operator_tx_ref="MTN-REF-0001",
            msisdn="+2250700000000"), _FakeRequest(), None, db)
        print(f"✅ Émission MTN : {emit.message}")
        ok += 1

        # 4. Idempotence : même ref → rejet
        try:
            await telecom_emit(TelecomEmitRequest(
                operator="MTN", operator_key="test-key",
                patient_public_id="UM-PAT-TEST01",
                amount_um=5000, operator_tx_ref="MTN-REF-0001"), _FakeRequest(), None, db)
            print("❌ Idempotence échouée (double émission acceptée)")
        except Exception:
            print("✅ Idempotence : double émission rejetée (409)")
            ok += 1

        # 5. Crédit solidarité (diaspora)
        credit = await credit_wallet(
            CreditRequest(owner_id=patient_id, amount_um=2000, type="solidarite_credit"), None, db)
        assert credit.balance_after == 7000, f"Solde attendu 7000, obtenu {credit.balance_after}"
        print(f"✅ Crédit solidarité : +2000 UM → solde={credit.balance_after}")
        ok += 1

        # 6. Solde patient (UM/EUR/CFA)
        bal = await get_balance(patient_id, db)
        assert bal.balance_um == 7000
        assert bal.balance_cfa == 7000 * 655
        print(f"✅ Solde patient : {bal.balance_um} UM = {bal.balance_eur} EUR = {bal.balance_cfa} CFA")
        ok += 1

        # 7. Paiement patient → pharmacie (ordonnance QR)
        pay = await pay_wallet(PaymentRequest(
            from_owner_id=patient_id, to_owner_id=pharma_id,
            amount_um=3000, reference="ORD-2026-001",
            prescription_qr="QR-ORD-2026-001"), None, db)
        assert pay.from_balance_after == 4000
        assert pay.to_balance_after == 3000
        print(f"✅ Paiement pharmacie : 3000 UM → patient={pay.from_balance_after}, pharmacie={pay.to_balance_after}")
        ok += 1

        # 8. Paiement au-dessus du solde → refus
        try:
            await pay_wallet(PaymentRequest(
                from_owner_id=patient_id, to_owner_id=pharma_id, amount_um=99999), None, db)
            print("❌ Paiement insuffisant ACCEPTÉ (BUG)")
        except Exception as e:
            print(f"✅ Paiement insuffisant refusé : {getattr(e, 'detail', e)}")
            ok += 1

        # 9. Conversion pharmacie → CFA (prestataire convertible)
        conv = await convert_wallet(ConversionRequest(
            account_id=pharma.id, amount_um=1000, currency="CFA"), db)
        assert conv.amount_currency == 1000 * 655
        print(f"✅ Conversion pharmacie : 1000 UM → {conv.amount_currency} {conv.currency} [{conv.status}]")
        ok += 1

        # 10. Conversion patient → REFUS (non convertible)
        try:
            await convert_wallet(ConversionRequest(
                account_id=patient.id, amount_um=500, currency="CFA"), db)
            print("❌ Conversion patient ACCEPTÉE (BUG — non-convertible)")
        except Exception as e:
            print(f"✅ Conversion patient refusée : {getattr(e, 'detail', e)}")
            ok += 1

        # 11. Ledger patient
        ledger = await get_ledger(patient_id, limit=50, db=db)
        assert len(ledger.transactions) >= 3
        print(f"✅ Ledger patient : {len(ledger.transactions)} transactions")
        for t in ledger.transactions[:6]:
            print(f"   - {t.type.value}: {t.amount_um} UM [{t.status.value}]")
        ok += 1

    print()
    print(f"🎉 FLUX WALLET VALIDÉ : {ok}/{total + 3} vérifications passées")
    return 0 if ok == total + 3 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
