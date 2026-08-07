# ──────────────────────────────────────────────
# TEST BOUT-EN-BOUT — L'écosystème Vital Ka complet
# ──────────────────────────────────────────────
# Simule le cycle de vie COMPLET d'un patient, de la diaspora à la pharmacie :
#
#   💝 Diaspora achète UM → 👤 Patient crédité
#   📡 Opérateur MTN émet UM → 👤 Patient crédité
#   🩺 Médecin crée le dossier → 📁 Dossier accessible par QR
#   🩺 Médecin encaisse des honoraires → 💳 Patient débité, médecin crédité
#   👤 Patient paie la pharmacie → 🏪 Pharmacie créditée
#   🏪 Pharmacie convertit en CFA → 💶 Demande de conversion
#   📋 Ledger complet et auditable
#
# Usage : python -m tests.test_ecosysteme_bout_en_bout
import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_TEST_DB = ROOT / "tests" / "test_ecosysteme.db"
if _TEST_DB.exists():
    _TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB.as_posix()}"
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("MINIO_ACCESS_KEY", "minioadmin")
os.environ.setdefault("MINIO_SECRET_KEY", "changeme")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-prod")
os.environ.setdefault("TELECOM_SECRET", "test-telecom-secret")

from unittest.mock import patch
from sqlalchemy.ext.asyncio import create_async_engine as _real_create
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.types import TypeDecorator, String


class SQLiteUUID(TypeDecorator):
    impl = String(36)
    cache_ok = True
    def process_bind_param(self, v, d): return str(v) if v else None
    def process_result_value(self, v, d):
        from uuid import UUID
        return UUID(v) if v else None


def _sqlite_engine(url, **kwargs):
    for k in ('pool_size', 'max_overflow', 'pool_pre_ping', 'pool_recycle', 'echo'):
        kwargs.pop(k, None)
    return _real_create(url, poolclass=StaticPool, **kwargs)


with patch("sqlalchemy.ext.asyncio.create_async_engine", _sqlite_engine), \
     patch("sqlalchemy.dialects.postgresql.UUID", SQLiteUUID), \
     patch("sqlalchemy.dialects.postgresql.JSONB", SQLiteJSON):
    from app.core.database import Base, engine, async_session_maker
    from app.models import (
        CompteUM, TransactionUM, ConversionUM, EmissionUM,
        MedicalRecord,
    )
    from app.models.config import AuditLog
    from app.models.teleconsult import TeleconsultSession
    from app.schemas.wallet import (
        WalletCreateRequest, CreditRequest, PaymentRequest,
        TelecomEmitRequest, ConversionRequest,
    )
    from app.schemas.record import MedicalRecordCreate, MedicalRecordUpdate
    from app.schemas.teleconsult import TeleconsultLinkRequest, TeleconsultAcceptRequest
    from app.api.v1.wallet import (
        create_wallet, credit_wallet, pay_wallet, get_balance,
        convert_wallet, get_ledger,
    )
    from app.api.v1.telecom import telecom_emit
    from app.api.v1.records import create_record, get_record, update_record
    from app.api.v1.teleconsult import create_link, get_session, accept_session


class _FakeRequest:
    def __init__(self, sig=None):
        self.headers = {"X-Operator-Signature": sig} if sig else {}


async def main() -> int:
    from uuid import uuid4

    print("╔" + "═" * 62 + "╗")
    print("║  🌊 TEST BOUT-EN-BOUT — Écosystème Vital Ka                    ║")
    print("╚" + "═" * 62 + "╝")

    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(
            c, tables=[CompteUM.__table__, TransactionUM.__table__,
                       ConversionUM.__table__, EmissionUM.__table__,
                       AuditLog.__table__, MedicalRecord.__table__,
                       TeleconsultSession.__table__]))

    # Acteurs (walletIds locaux comme sur les téléphones)
    PATIENT = "PAT-AWA123"
    PHARMACIE = "PHA-DAKAR01"
    MEDECIN = "MED-DIOP01"
    SOLIDARITE = "SOL-PARIS77"
    ok = 0
    total = 14

    async with async_session_maker() as db:
        # ── 1. Création des comptes (comme les apps au premier lancement) ──
        await create_wallet(WalletCreateRequest(owner_id=PATIENT, role="patient", public_id="UM-PAT-AWA123"), db)
        await create_wallet(WalletCreateRequest(owner_id=PHARMACIE, role="pharmacie", public_id="UM-PHA-DAKAR01"), db)
        await create_wallet(WalletCreateRequest(owner_id=MEDECIN, role="medecin", public_id="UM-MED-DIOP01"), db)
        await create_wallet(WalletCreateRequest(owner_id=SOLIDARITE, role="solidarite", public_id="UM-SOL-PARIS77"), db)
        print("✅ 4 comptes créés (patient, pharmacie, médecin, solidarité)")
        ok += 1

        # ── 2. La diaspora achète 2000 UM pour Awa ──
        credit = await credit_wallet(CreditRequest(
            owner_id=PATIENT, amount_um=2000, type="solidarite_credit",
            reference="SOL-REF-001", metadata={"from": SOLIDARITE}), None, db)
        assert credit.balance_after == 2000
        print(f"✅ Diaspora → +2000 UM (tx {credit.tx_id}) — solde {credit.balance_after}")
        ok += 1

        # ── 3. L'opérateur MTN émet 5000 UM (achat mobile money) ──
        emit = await telecom_emit(TelecomEmitRequest(
            operator="MTN", operator_key="test-key",
            patient_public_id="UM-PAT-AWA123", amount_um=5000,
            operator_tx_ref="MTN-AWA-0001", msisdn="+2250700000000"), _FakeRequest(), None, db)
        bal = await get_balance(PATIENT, db)
        assert bal.balance_um == 7000
        print(f"✅ MTN émission → +5000 UM — solde {bal.balance_um} UM = {bal.balance_cfa} CFA")
        ok += 1

        # ── 4. Le médecin crée le dossier médical d'Awa ──
        record = await create_record(MedicalRecordCreate(
            patient_id=PATIENT,
            profile={"name": "Awa Diop", "age": 34, "blood": "O+"},
            allergies=["pénicilline"],
            antecedents=["paludisme 2024"],
        ), None, db)
        print(f"✅ Dossier créé : {record.profile['name']} — allergie pénicilline notée")
        ok += 1

        # ── 5. Le médecin encaisse 3000 UM d'honoraires ──
        pay_doc = await pay_wallet(PaymentRequest(
            from_owner_id=PATIENT, to_owner_id=MEDECIN,
            amount_um=3000, reference="HON-CONSULT-001"), None, db)
        assert pay_doc.from_balance_after == 4000
        assert pay_doc.to_balance_after == 3000
        print(f"✅ Honoraires médecin : patient {pay_doc.from_balance_after} UM, médecin {pay_doc.to_balance_after} UM")
        ok += 1

        # ── 6. Le patient paie la pharmacie 1500 UM (ordonnance) ──
        pay_ph = await pay_wallet(PaymentRequest(
            from_owner_id=PATIENT, to_owner_id=PHARMACIE,
            amount_um=1500, reference="ORD-2026-001",
            prescription_qr="ORD-2026-001-QR"), None, db)
        assert pay_ph.from_balance_after == 2500
        assert pay_ph.to_balance_after == 1500
        print(f"✅ Paiement pharmacie : patient {pay_ph.from_balance_after} UM, pharmacie {pay_ph.to_balance_after} UM")
        ok += 1

        # ── 7. Le médecin complète le dossier (ordonnance prescrite) ──
        updated = await update_record(PATIENT, MedicalRecordUpdate(
            medications=[{"name": "Artéméther", "dosage": "80mg", "duration": "3j"}],
            ordonnances=[{"id": "ORD-2026-001", "diagnosis": "Paludisme"}],
        ), None, db)
        assert updated.medications[0]["name"] == "Artéméther"
        print(f"✅ Dossier complété : {len(updated.medications)} médicament, 1 ordonnance")
        ok += 1

        # ── 8. La pharmacie convertit 1000 UM en CFA ──
        conv = await convert_wallet(ConversionRequest(
            account_id=PHARMACIE, amount_um=1000, currency="CFA",
            bank_info={"iban": "CI0080-1234", "holder": "Pharmacie Dakar"}), db)
        assert conv.amount_currency == 655000
        print(f"✅ Conversion pharmacie : 1000 UM → {conv.amount_currency} CFA (gel en attente)")
        ok += 1

        # ── 9. Vérification : le patient ne peut PAS convertir (non-convertible) ──
        try:
            await convert_wallet(ConversionRequest(account_id=PATIENT, amount_um=500, currency="EUR"), db)
            print("❌ Patient a converti (BUG — non-convertible)")
        except Exception as e:
            print(f"✅ Patient non-convertible respecté : {getattr(e, 'detail', e)}")
            ok += 1

        # ── 10. Ledger global auditable ──
        led = await get_ledger(PATIENT, limit=50, db=db)
        txs = led.transactions
        types = sorted(set(t.type.value for t in txs))
        assert len(txs) >= 3
        print(f"✅ Ledger patient : {len(txs)} transactions — types: {', '.join(types)}")
        for t in txs[:4]:
            print(f"     {t.type.value:>22} : {t.amount_um:>5.0f} UM [{t.status.value}]")
        ok += 1

        # ── 11. TÉLÉCONSULTATION : le patient génère un lien pour son médecin ──
        link = await create_link(TeleconsultLinkRequest(
            patient_id=PATIENT,
            patient_name="Awa Diop",
            doctor_name="Dr Kouadio (Paris)",
            amount_um=2500,
        ), None, db)
        assert link.ttl_minutes == 30
        assert link.token
        print(f"✅ Lien généré : {link.link} (valable {link.ttl_minutes} min)")
        ok += 1

        # ── 12. Le médecin (à l'étranger) clique sur le lien → valide la session ──
        session = await get_session(link.token, db)
        assert session.patient_name == "Awa Diop"
        assert session.status.value == "pending"
        print(f"✅ Médecin valide le lien : patient={session.patient_name}, statut={session.status.value}")
        ok += 1

        # ── 13. Le médecin s'identifie et accepte ──
        accepted = await accept_session(link.token, TeleconsultAcceptRequest(
            doctor_name="Dr Kouadio",
            doctor_license="PAR-12345",
            doctor_wallet_id=MEDECIN,
        ), None, db)
        assert accepted.status.value == "accepted"
        print(f"✅ Médecin identifié : {accepted.doctor_name}, statut={accepted.status.value}")
        ok += 1

        # ── 14. Lien expiré → rejet (token inconnu) ──
        try:
            await get_session("token_inexistant_123", db)
            print("❌ Lien inconnu ACCEPTÉ (BUG)")
        except Exception as e:
            print(f"✅ Lien inconnu rejeté : {getattr(e, 'detail', e)}")
            ok += 1

    print()
    print(f"🎉 ÉCOSYSTÈME VALIDÉ : {ok}/{total} vérifications")

    await engine.dispose()
    if _TEST_DB.exists():
        try: _TEST_DB.unlink()
        except OSError: pass
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
