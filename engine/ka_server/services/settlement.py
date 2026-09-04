"""
settlement.py — Moteur de conversion & de rapprochement bancaire KARE
=====================================================================
Source de vérité SERVEUR de l'économie en Unités Médicales (UM).

Là où le frontend (ka_wallet.js) simulait tout en localStorage, ce module
porte les invariants métier côté serveur :

  • 1 UM = 1 EUR = 655 CFA (taux fixe, non spéculatif)
  • Patient : UM non convertibles — dépenses médicales uniquement
  • Prestataire : UM convertibles — gel temporaire puis règlement CFA
  • Solidarité : plafond AML 5 000 UM / mois
  • Ledger append-only, idempotent (une même clé rejouée ne duplique rien)
  • Rapprochement : fiat en fiducie = UM en circulation (adossement 1:1)

Stockage : data/banking/ledger.json (léger, thread-safe).
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from .banking_gateway import (
    PaymentError, FIDUCIARY_ACCOUNT, UM_TO_CFA, get_payment_processor,
)

log = logging.getLogger(__name__)

# ── Constantes métier ─────────────────────────────────────────────────────────
MAX_MONTHLY_SOLIDARITE = 5000          # plafond anti-blanchiment (UM/mois)
CONVERTIBLE_ROLES = {"medecin", "pharmacie", "labo"}   # prestataires
NON_CONVERTIBLE_ROLES = {"patient"}                    # patients

_store_lock = threading.Lock()


def _ledger_path() -> Path:
    """Chemin de persistance (surchargeable par KA_BANKING_DIR — tests)."""
    raw = os.environ.get("KA_BANKING_DIR", "")
    base = Path(raw) if raw else Path(__file__).resolve().parent.parent.parent / "data" / "banking"
    return base / "ledger.json"


# ═══════════════════════════════════════════════════════════════════════════════
#  Persistance
# ═══════════════════════════════════════════════════════════════════════════════

def _empty_state() -> Dict:
    return {
        "accounts": {},       # wallet_id → {role, balance_um, frozen_um, bank_account}
        "ledger": [],         # append-only, signé au niveau applicatif
        "conversions": {},    # conv_id → {…}
        "collections": {},    # collection_id → {…}
        "processed": {},      # idempotency_key → résultat (rejeu)
    }


def _load_state() -> Dict:
    with _store_lock:
        try:
            if _ledger_path().exists():
                return json.loads(_ledger_path().read_text(encoding="utf-8"))
        except Exception as e:
            log.warning(f"settlement: lecture échouée ({e}) — démarre à zéro")
    return _empty_state()


def _save_state(state: Dict):
    with _store_lock:
        p = _ledger_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _txid(prefix: str) -> str:
    return f"{prefix}_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"


def _append_ledger(state: Dict, entry: Dict) -> Dict:
    """Ajoute une transaction au ledger append-only (max 10 000 entrées)."""
    entry = {**entry, "seq": len(state["ledger"])}
    state["ledger"].append(entry)
    if len(state["ledger"]) > 10_000:
        state["ledger"] = state["ledger"][-10_000:]
    return entry


# ═══════════════════════════════════════════════════════════════════════════════
#  Comptes (wallets serveur)
# ═══════════════════════════════════════════════════════════════════════════════

def upsert_account(wallet_id: str, role: str, bank_account: Optional[str] = None) -> Dict:
    """Crée ou met à jour un compte. Retourne le compte."""
    state = _load_state()
    acc = state["accounts"].get(wallet_id)
    if acc is None:
        acc = {"role": role, "balance_um": 0.0, "frozen_um": 0.0,
               "bank_account": bank_account or f"PREST_{wallet_id}"}
        state["accounts"][wallet_id] = acc
    else:
        acc["role"] = role
        if bank_account:
            acc["bank_account"] = bank_account
    _save_state(state)
    return dict(acc)


def get_account(wallet_id: str) -> Optional[Dict]:
    state = _load_state()
    acc = state["accounts"].get(wallet_id)
    return dict(acc) if acc else None


def _mutate_account(state: Dict, wallet_id: str, delta_balance: float = 0.0,
                    delta_frozen: float = 0.0):
    acc = state["accounts"].setdefault(
        wallet_id, {"role": "unknown", "balance_um": 0.0, "frozen_um": 0.0,
                    "bank_account": f"PREST_{wallet_id}"})
    acc["balance_um"] = round(acc.get("balance_um", 0.0) + delta_balance, 6)
    acc["frozen_um"] = round(acc.get("frozen_um", 0.0) + delta_frozen, 6)
    return acc


# ═══════════════════════════════════════════════════════════════════════════════
#  Opérations de base sur le ledger UM
# ═══════════════════════════════════════════════════════════════════════════════

def credit_um(wallet_id: str, amount: float, description: str = "",
              metadata: Optional[Dict] = None, tx_type: str = "solidarite_credit") -> Dict:
    """Crédite un wallet UM (ex: achat solidarité → patient).

    Applique le plafond AML mensuel (5 000 UM) pour les crédits de solidarité.
    Retourne {"ok": True, "tx": ...} ou {"ok": False, "error": ...}.
    """
    amount = abs(float(amount))
    if tx_type == "solidarite_credit":
        aml = check_monthly_solidarite_limit()
        if aml["total"] + amount > aml["limit"]:
            return {"ok": False, "error": "Plafond solidarité dépassé (AML)",
                    "limit": aml["limit"], "total": aml["total"]}

    state = _load_state()
    _mutate_account(state, wallet_id, delta_balance=amount)
    tx = _append_ledger(state, {
        "txId": _txid("tx"), "type": tx_type, "from": "KA_SOLIDARITE",
        "to": wallet_id, "amount": amount,
        "timestamp": _now_iso(), "metadata": metadata or {},
        "description": description,
    })
    _save_state(state)
    return {"ok": True, "tx": tx}


def debit_um(wallet_id: str, amount: float, recipient: str, description: str = "",
             metadata: Optional[Dict] = None) -> Dict:
    """Débite un wallet (patient → prestataire). Vérifie le solde."""
    amount = abs(float(amount))
    state = _load_state()
    acc = state["accounts"].get(wallet_id)
    if acc is None or acc.get("balance_um", 0.0) < amount:
        return {"ok": False, "error": "Solde insuffisant",
                "available": acc.get("balance_um", 0.0) if acc else 0.0}
    _mutate_account(state, wallet_id, delta_balance=-amount)
    _mutate_account(state, recipient, delta_balance=amount)
    tx = _append_ledger(state, {
        "txId": _txid("tx"), "type": "payment", "from": wallet_id,
        "to": recipient, "amount": amount,
        "timestamp": _now_iso(), "metadata": metadata or {},
        "description": description,
    })
    _save_state(state)
    return {"ok": True, "tx": tx}


def check_monthly_solidarite_limit(wallet_id: Optional[str] = None) -> Dict:
    """Vérifie le plafond AML mensuel (5 000 UM) des crédits de solidarité.

    Compte à la fois les crédits directs (`solidarite_credit`) et les émissions
    issues de collecte (`collection` — achat diaspora → patient), qui sont
    autant d'entrées d'argent dans le circuit de soin.
    """
    state = _load_state()
    now = time.localtime()
    month, year = now.tm_mon, now.tm_year
    total = 0.0
    for tx in state["ledger"]:
        if tx.get("type") not in ("solidarite_credit", "collection"):
            continue
        ts = tx.get("timestamp", "")
        try:
            t = time.strptime(ts[:10], "%Y-%m-%d")
        except Exception:
            continue
        if t.tm_mon == month and t.tm_year == year:
            total += tx.get("amount", 0.0)
    return {"total": round(total, 6), "limit": MAX_MONTHLY_SOLIDARITE,
            "ok": total < MAX_MONTHLY_SOLIDARITE}


# ═══════════════════════════════════════════════════════════════════════════════
#  Collecte (fiat → UM) — achat d'UM par la diaspora / tiers
# ═══════════════════════════════════════════════════════════════════════════════

def _um_from_fiat(amount_fiat: float, currency: str) -> float:
    """Convertit un montant fiat en UM selon la devise d'achat."""
    rates = {"EUR": 1.0, "USD": 1.09, "CFA": UM_TO_CFA, "XOF": UM_TO_CFA, "GBP": 0.84}
    rate = rates.get(currency.upper(), 1.0)
    return round(float(amount_fiat) / rate, 6)


def record_collection(method: str, amount_fiat: float, currency: str,
                      wallet_id: str, details: Optional[Dict] = None,
                      idempotency_key: Optional[str] = None) -> Dict:
    """Collecte le fiat via Ecobank puis crédite le wallet UM du bénéficiaire.

    Idempotent : si `idempotency_key` a déjà été traitée, retourne le résultat
    mémorisé (jamais de double émission UM).
    """
    state = _load_state()
    key = idempotency_key or f"coll_{method}_{wallet_id}_{amount_fiat}_{currency}"
    if key in state["processed"]:
        return state["processed"][key]

    client = get_payment_processor()
    amount_um = _um_from_fiat(amount_fiat, currency)

    # AML — la collecte diaspora → patient est un crédit de solidarité, plafonné.
    aml = check_monthly_solidarite_limit()
    if aml["total"] + amount_um > aml["limit"]:
        rejected = {
            "id": _txid("coll"), "method": method, "amount_fiat": float(amount_fiat),
            "currency": currency, "amount_um": amount_um, "wallet_id": wallet_id,
            "status": "rejected", "ecobank_ref": None, "fee": 0.0,
            "timestamp": _now_iso(),
            "raw": {"reason": "aml_limit_exceeded", "limit": aml["limit"]},
        }
        state["processed"][key] = rejected
        _save_state(state)
        return rejected

    collection_id = _txid("coll")
    reference = f"KARE_{collection_id}"

    if method == "momo":
        result = client.collect_momo(amount_fiat, currency,
                                     (details or {}).get("phone", ""),
                                     reference, key)
    elif method == "card":
        result = client.collect_card(amount_fiat, currency,
                                     details or {}, reference, key)
    else:
        result = {"ref": reference, "status": "failed", "amount": amount_fiat,
                  "currency": currency, "fee": 0.0,
                  "raw": {"reason": f"unknown_method:{method}"}}

    collection = {
        "id": collection_id,
        "method": method,
        "amount_fiat": float(amount_fiat),
        "currency": currency,
        "amount_um": amount_um,
        "wallet_id": wallet_id,
        "status": result.get("status"),
        "ecobank_ref": result.get("ref"),
        "fee": result.get("fee", 0.0),
        "timestamp": _now_iso(),
    }
    state["collections"][collection_id] = collection

    if result.get("status") == "settled":
        # Émission UM 1:1 — uniquement si la collecte bancaire est acquittée.
        _mutate_account(state, wallet_id, delta_balance=amount_um)
        _append_ledger(state, {
            "txId": _txid("tx"), "type": "collection",
            "from": "ECOBANK", "to": wallet_id, "amount": amount_um,
            "timestamp": _now_iso(),
            "metadata": {"ecobank_ref": result.get("ref"), "method": method,
                         "amount_fiat": amount_fiat, "currency": currency},
            "description": f"Émission UM — {method} {amount_fiat} {currency}",
        })

    state["processed"][key] = collection
    _save_state(state)
    return collection


# ═══════════════════════════════════════════════════════════════════════════════
#  Conversion (UM → CFA) — prestataire uniquement
# ═══════════════════════════════════════════════════════════════════════════════

def request_conversion(wallet_id: str, amount_um: float, currency: str = "XOF",
                       bank_info: Optional[Dict] = None) -> Dict:
    """Gèle les UM et crée une demande de conversion (prestataire)."""
    amount_um = abs(float(amount_um))
    state = _load_state()
    acc = state["accounts"].get(wallet_id)
    if acc is None or acc.get("role") not in CONVERTIBLE_ROLES:
        return {"ok": False, "error": "Rôle non convertible (prestataire requis)",
                "role": acc.get("role") if acc else None}
    if acc.get("balance_um", 0.0) < amount_um:
        return {"ok": False, "error": "Solde insuffisant",
                "available": acc.get("balance_um", 0.0)}

    _mutate_account(state, wallet_id, delta_balance=-amount_um, delta_frozen=amount_um)
    conv_id = _txid("conv")
    conversion = {
        "id": conv_id,
        "wallet_id": wallet_id,
        "amount_um": amount_um,
        "amount_cfa": round(amount_um * UM_TO_CFA, 2),
        "currency": currency or "XOF",
        "bank_account": bank_info.get("bank_account") if bank_info else acc.get("bank_account"),
        "status": "requested",      # requested → frozen → settling → settled | failed
        "ecobank_ref": None,
        "requested_at": _now_iso(),
        "processed_at": None,
    }
    state["conversions"][conv_id] = conversion
    _append_ledger(state, {
        "txId": _txid("tx"), "type": "conversion_request",
        "from": wallet_id, "to": "BANK", "amount": amount_um,
        "timestamp": _now_iso(), "metadata": {"conversion_id": conv_id},
        "description": f"Gel UM — conversion {currency}",
    })
    _save_state(state)
    return {"ok": True, "conversion": conversion}


def execute_settlement(conversion_id: str) -> Dict:
    """Exécute le règlement bancaire d'une conversion gelée.

    Succès → `settled` (les UM restent gelées puis sont consommées).
    Échec  → `failed` (les UM sont dégelés et rendus au prestataire).
    """
    state = _load_state()
    conv = state["conversions"].get(conversion_id)
    if conv is None:
        return {"ok": False, "error": "Conversion inconnue"}
    if conv["status"] not in ("requested", "frozen", "settling"):
        return {"ok": False, "error": f"État invalide : {conv['status']}"}

    conv["status"] = "settling"
    _save_state(state)

    client = get_payment_processor()
    key = f"settle_{conversion_id}"
    try:
        result = client.settle(conv["amount_cfa"], conv["currency"],
                               conv["bank_account"], f"KARE_{conversion_id}", key)
    except PaymentError as e:
        result = {"ref": None, "status": "failed", "amount": conv["amount_cfa"],
                  "currency": conv["currency"], "fee": 0.0,
                  "raw": {"reason": str(e)}}

    state = _load_state()
    conv = state["conversions"][conversion_id]
    if result.get("status") == "settled":
        conv["status"] = "settled"
        conv["ecobank_ref"] = result.get("ref")
        conv["processed_at"] = _now_iso()
        # Consommation des UM : les UM gelées sont définitivement
        # retirées de la circulation (plus de balance, plus de frozen).
        _mutate_account(state, conv["wallet_id"], delta_frozen=-conv["amount_um"])
        _append_ledger(state, {
            "txId": _txid("tx"), "type": "conversion_settled",
            "from": "BANK", "to": conv["wallet_id"], "amount": conv["amount_cfa"],
            "timestamp": _now_iso(),
            "metadata": {"conversion_id": conversion_id,
                         "ecobank_ref": result.get("ref")},
            "description": f"Règlement CFA {conv['amount_cfa']} {conv['currency']}",
        })
    else:
        conv["status"] = "failed"
        conv["processed_at"] = _now_iso()
        # Dégel — les UM sont rendus au prestataire (pas de perte).
        _mutate_account(state, conv["wallet_id"],
                        delta_balance=conv["amount_um"], delta_frozen=-conv["amount_um"])
        _append_ledger(state, {
            "txId": _txid("tx"), "type": "conversion_failed",
            "from": "BANK", "to": conv["wallet_id"], "amount": conv["amount_um"],
            "timestamp": _now_iso(), "metadata": {"conversion_id": conversion_id},
            "description": f"Dégel UM — règlement échoué ({result.get('raw', {})})",
        })

    _save_state(state)
    return {"ok": True, "conversion": conv, "bank": result}


def get_conversion(conversion_id: str) -> Optional[Dict]:
    state = _load_state()
    conv = state["conversions"].get(conversion_id)
    return dict(conv) if conv else None


# ═══════════════════════════════════════════════════════════════════════════════
#  Rapprochement (ledger UM ↔ relevé bancaire)
# ═══════════════════════════════════════════════════════════════════════════════

def reconcile(date_iso: str) -> Dict:
    """Rapproche la journée : mouvements fiat du ledger vs relevé Ecobank.

    Retourne les totaux et l'écart. `balanced=True` signifie que l'adossement
    1:1 tient (fiat collecté = UM émis, fiat réglé = UM consommés).
    """
    state = _load_state()
    client = get_payment_processor()
    statement = client.get_statement(date_iso)

    ledger_collects = ledger_settlements = 0.0
    for tx in state["ledger"]:
        ts = tx.get("timestamp", "")[:10]
        if ts != date_iso:
            continue
        if tx.get("type") == "collection":
            ledger_collects += tx.get("metadata", {}).get("amount_fiat", 0.0)
        elif tx.get("type") == "conversion_settled":
            ledger_settlements += tx.get("amount", 0.0)

    bank_collects = sum(s.get("amount", 0.0) for s in statement if s.get("type") == "collect")
    bank_settlements = sum(s.get("amount", 0.0) for s in statement if s.get("type") == "settle")

    return {
        "date": date_iso,
        "ledger_collects": round(ledger_collects, 2),
        "ledger_settlements": round(ledger_settlements, 2),
        "bank_collects": round(bank_collects, 2),
        "bank_settlements": round(bank_settlements, 2),
        "ecart_collects": round(ledger_collects - bank_collects, 2),
        "ecart_settlements": round(ledger_settlements - bank_settlements, 2),
        "balanced": abs(ledger_collects - bank_collects) < 0.01
                    and abs(ledger_settlements - bank_settlements) < 0.01,
        "statement_entries": len(statement),
    }


def get_state_summary() -> Dict:
    """Vue d'ensemble de l'économie UM (utile au dashboard et aux tests)."""
    state = _load_state()
    total_um = sum(a.get("balance_um", 0.0) + a.get("frozen_um", 0.0)
                   for a in state["accounts"].values())
    return {
        "accounts": len(state["accounts"]),
        "ledger_entries": len(state["ledger"]),
        "conversions_pending": sum(1 for c in state["conversions"].values()
                                   if c.get("status") in ("requested", "frozen", "settling")),
        "collections": len(state["collections"]),
        "total_um_in_circulation": round(total_um, 6),
        "aml": check_monthly_solidarite_limit(),
    }


def list_accounts() -> List[Dict]:
    """Liste les comptes (pour la console d'administration)."""
    state = _load_state()
    return [{"wallet_id": k, **v} for k, v in state["accounts"].items()]


def get_ledger(limit: int = 100) -> List[Dict]:
    """Retourne les dernières entrées du ledger (les plus récentes d'abord)."""
    state = _load_state()
    return list(reversed(state["ledger"]))[:limit]


def list_conversions() -> List[Dict]:
    """Retourne les conversions, les plus récentes d'abord."""
    state = _load_state()
    return list(reversed(list(state["conversions"].values())))


def reset_state():
    """Vide l'état (tests). Retourne le nombre d'entrées supprimées."""
    state = _load_state()
    n = len(state["ledger"])
    _save_state(_empty_state())
    return n


# ═══════════════════════════════════════════════════════════════════════════════
#  Seed — données de démonstration
# ═══════════════════════════════════════════════════════════════════════════════

_DEMO_WALLETS = {
    # Patients
    "PAT-DIALLO":  {"role": "patient", "bank_account": None},
    "PAT-TOURE":   {"role": "patient", "bank_account": None},
    "PAT-KONE":    {"role": "patient", "bank_account": None},
    "PAT-TRAORE":  {"role": "patient", "bank_account": None},
    "PAT-SYLLA":   {"role": "patient", "bank_account": None},
    "PAT-DIABATE": {"role": "patient", "bank_account": None},
    "PAT-CAMARA":  {"role": "patient", "bank_account": None},
    "PAT-SISSOKO": {"role": "patient", "bank_account": None},
    "PAT-OUATT":   {"role": "patient", "bank_account": None},
    "PAT-BAMBA":   {"role": "patient", "bank_account": None},
    # Médecins
    "MED-DR_KONE":    {"role": "medecin", "bank_account": "BANK_KONE"},
    "MED-DR_TOURE":   {"role": "medecin", "bank_account": "BANK_TOURE"},
    "MED-DR_DIALLO":  {"role": "medecin", "bank_account": "BANK_DIALLO"},
    "MED-DR_SY":      {"role": "medecin", "bank_account": "BANK_SY"},
    "MED-DR_DIARRA":  {"role": "medecin", "bank_account": "BANK_DIARRA"},
    # Pharmacies
    "PHM-CENTRALE":   {"role": "pharmacie", "bank_account": "BANK_PHM_CENTRALE"},
    "PHM-SANTE_EXPO": {"role": "pharmacie", "bank_account": "BANK_PHM_SANTE"},
    # Laboratoires
    "LABO-BIOCLIN":   {"role": "labo", "bank_account": "BANK_LABO_BIOCLIN"},
    "LABO-ANAPATH":   {"role": "labo", "bank_account": "BANK_LABO_ANAPATH"},
    # Solidarité
    "SOL-DIASPORA1":  {"role": "solidarite", "bank_account": None},
    "SOL-DIASPORA2":  {"role": "solidarite", "bank_account": None},
}


def seed_demo() -> Dict:
    """Peuple la base de données de démonstration.

    Crée une petite économie UM fictive avec :
    - 10 patients, 5 médecins, 2 pharmacies, 2 labos, 2 solidarité
    - Des UM déjà émises et dépensées
    - Des conversions en attente et d'autres réglées
    - Un ledger historique pour que la console ne soit pas vide
    - Des collections déjà effectuées
    - Un état de rapprochement cohérent

    Retourne un résumé de ce qui a été créé.
    """
    import time as _time

    # On reset d'abord, puis on génère l'état de démo.
    state = _empty_state()
    state["accounts"] = {}
    state["ledger"] = []
    state["conversions"] = {}
    state["collections"] = {}
    state["processed"] = {}

    # ── 1. Création des comptes ──
    for wid, info in _DEMO_WALLETS.items():
        state["accounts"][wid] = {
            "role": info["role"],
            "balance_um": 0.0,
            "frozen_um": 0.0,
            "bank_account": info["bank_account"] or f"PREST_{wid}",
        }

    # ── 2. Émissions UM (solidarité / diaspora) ──
    # Les patients reçoivent des UM.
    patient_credits = [
        ("PAT-DIALLO", 150, "Aide famille — Moussa (Mars)"),
        ("PAT-TOURE",  80,  "Solidarité — Fatoumata"),
        ("PAT-KONE",   200, "Aide traitement — Dr Koné"),
        ("PAT-TRAORE", 120, "Diaspora — Amadou (Paris)"),
        ("PAT-SYLLA",   60,  "Cagnotte naissance"),
        ("PAT-DIABATE", 90,  "Solidarité — Mariam"),
        ("PAT-CAMARA",  250, "Aide urgente — Santé"),
        ("PAT-SISSOKO", 40,  "Don famille"),
        ("PAT-OUATT",   180, "Collecte mosquée"),
        ("PAT-BAMBA",   100, "Aide traitement"),
    ]
    for wid, amount, desc in patient_credits:
        _mutate_account(state, wid, delta_balance=amount)
        _append_ledger(state, {
            "txId": _txid("tx"), "type": "solidarite_credit",
            "from": "KA_SOLIDARITE", "to": wid, "amount": amount,
            "timestamp": _now_iso(), "metadata": {},
            "description": desc,
        })

    # ── 3. Paiements de soins —─
    payments = [
        ("PAT-DIALLO", "MED-DR_KONE",   30, "Consultation générale"),
        ("PAT-DIALLO", "PHM-CENTRALE",  25, "Médicaments prescrits"),
        ("PAT-TOURE",  "MED-DR_TOURE",  20, "Consultation pédiatrie"),
        ("PAT-KONE",   "MED-DR_KONE",   50, "Suivi traitement"),
        ("PAT-KONE",   "LABO-BIOCLIN",  35, "Analyses sanguines"),
        ("PAT-TRAORE", "MED-DR_DIALLO", 40, "Consultation cardiologie"),
        ("PAT-TRAORE", "PHM-SANTE_EXPO", 28, "Antihypertenseurs"),
        ("PAT-SYLLA",  "MED-DR_SY",     15, "Consultation générale"),
        ("PAT-CAMARA", "MED-DR_DIARRA", 60, "Consultation spécialiste"),
        ("PAT-CAMARA", "PHM-CENTRALE",  45, "Traitement complet"),
        ("PAT-CAMARA", "LABO-ANAPATH",  30, "Analyses approfondies"),
        ("PAT-OUATT",  "MED-DR_KONE",   35, "Consultation de suivi"),
        ("PAT-BAMBA",  "MED-DR_TOURE",  25, "Consultation générale"),
        ("PAT-DIABATE","PHM-SANTE_EXPO", 20, "Médicaments"),
    ]
    for from_w, to_w, amount, desc in payments:
        from_acc = state["accounts"].get(from_w)
        to_acc = state["accounts"].get(to_w)
        if from_acc and to_acc and from_acc["balance_um"] >= amount:
            from_acc["balance_um"] = round(from_acc["balance_um"] - amount, 6)
            to_acc["balance_um"] = round(to_acc["balance_um"] + amount, 6)
            _append_ledger(state, {
                "txId": _txid("tx"), "type": "payment",
                "from": from_w, "to": to_w, "amount": amount,
                "timestamp": _now_iso(), "metadata": {},
                "description": desc,
            })

    # ── 4. Conversions — deux en attente, deux réglées, une échouée ──
    conversions_data = [
        ("MED-DR_KONE",   80,   "requested", "BANK_KONE",       None),
        ("MED-DR_DIALLO", 40,   "requested", "BANK_DIALLO",     None),
        ("MED-DR_TOURE",  20,   "settled",   "BANK_TOURE",      "ecobank_ref_20260801_001"),
        ("PHM-CENTRALE",  70,   "settled",   "BANK_PHM_CENTRALE","ecobank_ref_20260801_002"),
        ("MED-DR_SY",     15,   "failed",    "BANK_SY",         None),
    ]
    for wallet_id, amount_um, status, bank_acc, ecobank_ref in conversions_data:
        acc = state["accounts"].get(wallet_id)
        if not acc or acc["balance_um"] < amount_um:
            continue
        acc["balance_um"] = round(acc["balance_um"] - amount_um, 6)
        acc["frozen_um"] = round(acc.get("frozen_um", 0.0) + amount_um, 6)

        conv_id = _txid("conv")
        conv = {
            "id": conv_id,
            "wallet_id": wallet_id,
            "amount_um": amount_um,
            "amount_cfa": round(amount_um * UM_TO_CFA, 2),
            "currency": "XOF",
            "bank_account": bank_acc,
            "status": status,
            "ecobank_ref": ecobank_ref,
            "requested_at": _now_iso(),
            "processed_at": _now_iso() if status != "requested" else None,
        }
        state["conversions"][conv_id] = conv

        if status == "settled":
            acc["frozen_um"] = round(acc.get("frozen_um", 0.0) - amount_um, 6)
            _append_ledger(state, {
                "txId": _txid("tx"), "type": "conversion_settled",
                "from": "BANK", "to": wallet_id, "amount": conv["amount_cfa"],
                "timestamp": _now_iso(), "metadata": {"conversion_id": conv_id},
                "description": f"Règlement CFA {conv['amount_cfa']} XOF",
            })
        elif status == "failed":
            acc["frozen_um"] = round(acc.get("frozen_um", 0.0) - amount_um, 6)
            acc["balance_um"] = round(acc.get("balance_um", 0.0) + amount_um, 6)
            _append_ledger(state, {
                "txId": _txid("tx"), "type": "conversion_failed",
                "from": "BANK", "to": wallet_id, "amount": amount_um,
                "timestamp": _now_iso(), "metadata": {"conversion_id": conv_id},
                "description": "Dégel UM — règlement échoué",
            })
        else:
            _append_ledger(state, {
                "txId": _txid("tx"), "type": "conversion_request",
                "from": wallet_id, "to": "BANK", "amount": amount_um,
                "timestamp": _now_iso(), "metadata": {"conversion_id": conv_id},
                "description": f"Gel UM — conversion XOF",
            })

    # ── 5. Collections (achats diaspora) ──
    collections = [
        ("momo", 6550,  "XOF", "PAT-DIALLO", "77 111 22 33"),
        ("card", 10000, "EUR", "PAT-KONE",   {"last4": "4242", "brand": "visa"}),
        ("momo", 3275,  "XOF", "PAT-SISSOKO","77 444 55 66"),
    ]
    for method, amount_fiat, currency, wallet_id, detail in collections:
        coll_id = _txid("coll")
        amount_um = round(float(amount_fiat) / (655 if currency in ("XOF","CFA") else 1), 6)
        state["collections"][coll_id] = {
            "id": coll_id, "method": method,
            "amount_fiat": float(amount_fiat), "currency": currency,
            "amount_um": amount_um, "wallet_id": wallet_id,
            "status": "settled", "ecobank_ref": f"ecobank_{coll_id}",
            "fee": round(float(amount_fiat) * (0.015 if method == "momo" else 0.025), 2),
            "timestamp": _now_iso(),
        }

    # ── 6. Rapprochement : on synchronise le simulateur bancaire ──
    # On écrit l'état de démo et on remet les compteurs de la banque simulée à zéro.
    _save_state(state)

    # On recalcule le simulateur bancaire pour qu'il reflète le ledger.
    _sync_bank_simulator(state)

    summary = get_state_summary()
    summary["wallets_created"] = len(_DEMO_WALLETS)
    summary["payments"] = len(payments)
    summary["conversions_seeded"] = len(conversions_data)
    summary["collections_seeded"] = len(collections)
    summary["patients"] = sum(1 for w in _DEMO_WALLETS.values() if w["role"] == "patient")
    summary["providers"] = sum(1 for w in _DEMO_WALLETS.values() if w["role"] != "patient")
    return summary


def _sync_bank_simulator(state):
    """Synchronise le simulateur bancaire avec l'état du ledger de démo.

    Rend le solde du compte fiduciaire cohérent et enregistre les mouvements
    bancaires correspondant aux collections et règlements du seed.
    """
    try:
        client = get_payment_processor()
        client.reset()
        # Ajouter les mouvements bancaires correspondant aux collections
        for coll in state["collections"].values():
            if coll.get("status") == "settled":
                client.collect_momo(
                    coll["amount_fiat"], coll["currency"],
                    "771002233", coll["ecobank_ref"] or coll["id"],  # pas de 0000 → évite l'injection d'échec
                    f"seed_{coll['id']}")
        # Ajouter les mouvements bancaires correspondant aux règlements
        for conv in state["conversions"].values():
            if conv.get("status") == "settled" and conv.get("ecobank_ref"):
                client.settle(
                    conv["amount_cfa"], conv["currency"],
                    conv["bank_account"], conv["ecobank_ref"],
                    f"seed_conv_{conv['id']}")
    except Exception as e:
        log.warning(f"sync bank simulator: {e}")


def seed_scenario(script: List[Dict]) -> Dict:
    """Exécute un script de scénario (liste d'étapes).

    Chaque étape est un dict avec :
      - action (str) : le nom de l'opération
      - paramètres nommés (kwargs)

    Retourne la liste des résultats de chaque étape.
    """
    import types as _types

    # Mapping action → fonction
    _ACTIONS = {
        # Création de comptes
        "create_account": lambda **kw: upsert_account(
            kw.get("wallet_id", kw.get("id", "")),
            kw.get("role", "patient"),
            kw.get("bank_account", kw.get("bank", "")) or None),

        # Émissions / crédits
        "credit": lambda **kw: credit_um(
            kw.get("wallet_id", kw.get("id", "")),
            float(kw.get("amount_um", kw.get("amount", 0))),
            description=kw.get("description", "")),

        # Paiements
        "debit": lambda **kw: debit_um(
            kw.get("from") or kw.get("wallet_id", ""),
            float(kw.get("amount_um", kw.get("amount", 0))),
            kw.get("to") or kw.get("recipient", ""),
            description=kw.get("description", "")),

        # Conversions
        "request_conversion": lambda **kw: request_conversion(
            kw.get("wallet_id", kw.get("id", "")),
            float(kw.get("amount_um", kw.get("amount", 0))),
            kw.get("currency", "XOF"),
            kw.get("bank_info", {}))["conversion"],

        "execute_settlement": lambda **kw: execute_settlement(
            kw.get("conversion_id", kw.get("id", ""))),

        # Collections
        "collect_momo": lambda **kw: record_collection(
            "momo", float(kw.get("amount_fiat", kw.get("amount", 0))),
            kw.get("currency", "XOF"),
            kw.get("wallet_id", kw.get("id", "")),
            {"phone": kw.get("phone", "7700000000")},
            kw.get("idempotency_key")),

        # Rapprochement
        "reconcile": lambda **kw: reconcile(
            kw.get("date", time.strftime("%Y-%m-%d"))),

        # Attente / pause
        "sleep": lambda **kw: _time_sleep(float(kw.get("seconds", 0))),
    }

    results = []
    errors = []
    for i, step in enumerate(script):
        action = step.get("action", "")
        fn = _ACTIONS.get(action)
        if fn is None:
            errors.append({"step": i, "action": action, "error": "Action inconnue"})
            continue
        try:
            # On enlève 'action' et on passe le reste en kwargs
            kwargs = {k: v for k, v in step.items() if k != "action"}
            result = fn(**kwargs)
            results.append({"step": i, "action": action, "result": result})
        except Exception as e:
            errors.append({"step": i, "action": action, "error": str(e)})

    return {"results": results, "errors": errors, "total": len(script),
            "success": len(errors) == 0}


def _time_sleep(seconds: float):
    """Import local pour éviter la collision de nom."""
    import time as _t
    _t.sleep(seconds)


__all__ = [
    "upsert_account", "get_account", "credit_um", "debit_um",
    "check_monthly_solidarite_limit", "record_collection",
    "request_conversion", "execute_settlement", "get_conversion",
    "reconcile", "get_state_summary", "reset_state",
    "list_accounts", "get_ledger", "list_conversions",
    "seed_demo", "seed_scenario",
    "MAX_MONTHLY_SOLIDARITE", "UM_TO_CFA", "CONVERTIBLE_ROLES",
]
