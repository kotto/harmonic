"""
ecobank_gateway.py — Passerelle bancaire Ecobank (monnaie électronique)
=======================================================================
Client unique d'accès à Ecobank pour l'émission d'unités médicales (UM)
adossées 1:1 (1 UM = 1 EUR = 655 CFA) et la conversion UM → CFA (XOF).

Deux implémentations, une seule interface `EcobankClient` :

  • `SimulatedEcobankClient` — simulateur déterministe (mode bac à sable
    local, AUCUN appel réseau). C'est lui qui tourne par défaut tant que
    l'accès au sandbox Ecobank n'a pas été fourni. Il permet de dérouler
    le plan de tests T1–T10 dès aujourd'hui.
  • `RealEcobankClient` — client HTTP réel (OAuth2 client_credentials +
    signature HMAC + retry idempotent). Les URL et endpoints sont
    configurables par variables d'environnement car le portail développeur
    Ecobank n'est pas crawlable publiquement : on ne devine pas les chemins,
    on les remplit une fois le kit sandbox obtenu.

Choix du mode : `ECOBANK_MODE = simulator | live` (défaut : simulator).

Toutes les opérations d'écriture sont idempotentes : une même
`idempotency_key` rejouée retourne le même résultat, jamais de double
collecte / double règlement (exigence de la licence e-money).

Stockage du simulateur : data/banking/simulator.json (léger, thread-safe).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger(__name__)

# ── Constantes métier ─────────────────────────────────────────────────────────
UM_TO_CFA = 655
FIDUCIARY_ACCOUNT = "FIDUCIE_KARE"  # compte de cantonnement (fiat collecté)

_store_lock = threading.Lock()


def _data_dir() -> Path:
    """Répertoire de persistance (surchargeable par KA_BANKING_DIR — tests)."""
    raw = os.environ.get("KA_BANKING_DIR", "")
    return Path(raw) if raw else Path(__file__).resolve().parent.parent.parent / "data" / "banking"


# ═══════════════════════════════════════════════════════════════════════════════
#  Modèle de résultat
# ═══════════════════════════════════════════════════════════════════════════════

class EcobankError(Exception):
    """Erreur remontée par la passerelle bancaire (transport, refus, timeout)."""

    def __init__(self, message: str, code: str = "ECOBANK_ERROR", retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def _payment_ref(prefix: str) -> str:
    """Référence bancaire unique et monotone."""
    return f"{prefix}_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8].upper()}"


def _payment_result(ref: str, status: str, amount: float, currency: str,
                    fee: float = 0.0, raw: Optional[Dict] = None) -> Dict:
    """Forme canonique d'un résultat d'opération bancaire."""
    return {
        "ref": ref,               # référence banque (à stocker dans le ledger)
        "status": status,         # settled | failed | pending
        "amount": round(float(amount), 2),
        "currency": currency,
        "fee": round(float(fee), 2),
        "raw": raw or {},
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  Interface abstraite
# ═══════════════════════════════════════════════════════════════════════════════

class EcobankClient:
    """Contrat de la passerelle bancaire (implémenté par simulateur et réel)."""

    name = "ecobank"

    # ── Collecte (fiat → UM) ────────────────────────────────────────────────
    def collect_momo(self, amount: float, currency: str, phone: str,
                     reference: str, idempotency_key: str) -> Dict:
        raise NotImplementedError

    def collect_card(self, amount: float, currency: str, card: Dict,
                     reference: str, idempotency_key: str) -> Dict:
        raise NotImplementedError

    # ── Règlement (UM → CFA vers le prestataire) ───────────────────────────
    def settle(self, amount: float, currency: str, to_account: str,
               reference: str, idempotency_key: str) -> Dict:
        raise NotImplementedError

    # ── Rapprochement ──────────────────────────────────────────────────────
    def get_statement(self, date_iso: str) -> List[Dict]:
        """Relevé des mouvements bancaires d'une journée (collectes + règlements)."""
        raise NotImplementedError

    def get_balance(self, account: str, currency: str = "XOF") -> float:
        raise NotImplementedError

    # ── Webhook ────────────────────────────────────────────────────────────
    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Vérifie l'authenticité d'un callback Ecobank (HMAC-SHA256)."""
        raise NotImplementedError


# ═══════════════════════════════════════════════════════════════════════════════
#  Simulateur bancaire (mode bac à sable local)
# ═══════════════════════════════════════════════════════════════════════════════

class SimulatedEcobankClient(EcobankClient):
    """Banc simulé déterministe — déroule T1–T10 sans réseau.

    Injections d'échec (pour les tests) :
      • numéro Mobile Money terminant par `0000` → collecte échoue (fonds insuffisants)
      • compte de règlement `CLOSED_*`            → règlement échoue
    """

    name = "ecobank-simulator"

    def __init__(self, data_dir: Optional[Path] = None):
        self._dir = Path(data_dir) if data_dir else _data_dir()
        self._path = self._dir / "simulator.json"
        self._idempotency: Dict[str, Dict] = {}
        self._ensure_state()

    # ── Persistance ──────────────────────────────────────────────────────────
    def _empty_state(self) -> Dict:
        return {
            "accounts": {FIDUCIARY_ACCOUNT: 1_000_000_000.0},  # fiat en fiducie
            "statements": [],   # mouvements datés (collecte / règlement)
            "ops": {},          # idempotency_key → résultat (rejeu)
        }

    def _ensure_state(self):
        self._dir.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._save(self._empty_state())

    def _load(self) -> Dict:
        with _store_lock:
            try:
                return json.loads(self._path.read_text(encoding="utf-8"))
            except Exception:
                return self._empty_state()

    def _save(self, state: Dict):
        with _store_lock:
            self._path.write_text(
                json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    def reset(self):
        """Vide l'état du simulateur (tests)."""
        self._save(self._empty_state())
        self._idempotency = {}

    def _apply(self, idempotency_key: str, fn) -> Dict:
        """Garde idempotence : rejoue le résultat si la clé a déjà été traitée."""
        state = self._load()
        if idempotency_key in state.get("ops", {}):
            return state["ops"][idempotency_key]
        result = fn(state)
        state["ops"][idempotency_key] = result
        self._save(state)
        return result

    def _append_statement(self, state: Dict, entry: Dict):
        state.setdefault("statements", []).append(entry)

    # ── Implémentation du contrat ────────────────────────────────────────────
    def collect_momo(self, amount, currency, phone, reference, idempotency_key):
        def _do(state):
            if (phone or "").replace(" ", "").endswith("0000"):
                return _payment_result(reference, "failed", amount, currency,
                                       raw={"reason": "insufficient_funds"})
            state["accounts"][FIDUCIARY_ACCOUNT] = state["accounts"].get(
                FIDUCIARY_ACCOUNT, 0.0) + float(amount)
            self._append_statement(state, {
                "date": time.strftime("%Y-%m-%d"),
                "type": "collect",
                "method": "momo",
                "amount": float(amount),
                "currency": currency,
                "ref": reference,
                "status": "settled",
            })
            return _payment_result(reference, "settled", amount, currency,
                                   fee=round(float(amount) * 0.015, 2))
        return self._apply(idempotency_key, _do)

    def collect_card(self, amount, currency, card, reference, idempotency_key):
        def _do(state):
            state["accounts"][FIDUCIARY_ACCOUNT] = state["accounts"].get(
                FIDUCIARY_ACCOUNT, 0.0) + float(amount)
            self._append_statement(state, {
                "date": time.strftime("%Y-%m-%d"),
                "type": "collect",
                "method": "card",
                "amount": float(amount),
                "currency": currency,
                "ref": reference,
                "status": "settled",
            })
            return _payment_result(reference, "settled", amount, currency,
                                   fee=round(float(amount) * 0.025, 2))
        return self._apply(idempotency_key, _do)

    def settle(self, amount, currency, to_account, reference, idempotency_key):
        def _do(state):
            if (to_account or "").startswith("CLOSED_"):
                return _payment_result(reference, "failed", amount, currency,
                                       raw={"reason": "account_closed"})
            state["accounts"][FIDUCIARY_ACCOUNT] = state["accounts"].get(
                FIDUCIARY_ACCOUNT, 0.0) - float(amount)
            state["accounts"][to_account] = state["accounts"].get(to_account, 0.0) + float(amount)
            self._append_statement(state, {
                "date": time.strftime("%Y-%m-%d"),
                "type": "settle",
                "amount": float(amount),
                "currency": currency,
                "to_account": to_account,
                "ref": reference,
                "status": "settled",
            })
            return _payment_result(reference, "settled", amount, currency)
        return self._apply(idempotency_key, _do)

    def get_statement(self, date_iso):
        state = self._load()
        return [s for s in state.get("statements", []) if s.get("date") == date_iso]

    def get_balance(self, account, currency="XOF"):
        state = self._load()
        return float(state.get("accounts", {}).get(account, 0.0))

    def verify_webhook(self, payload, signature):
        # Simulateur : le secret est fixe, la signature est re-vérifiable.
        secret = os.environ.get("ECOBANK_WEBHOOK_SECRET", "simulator-secret")
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature or "")


# ═══════════════════════════════════════════════════════════════════════════════
#  Client réel (OAuth2 + HMAC + retry idempotent)
# ═══════════════════════════════════════════════════════════════════════════════

class RealEcobankClient(EcobankClient):
    """Client HTTP Ecobank réel.

    ⚠️ Les chemins d'API ne sont PAS codés en dur ici : le portail développeur
    Ecobank n'est pas accessible publiquement (login requis). Chaque endpoint
    est lu depuis l'environnement, à remplir une fois le kit sandbox obtenu.

    Variables d'environnement attendues :
      ECOBANK_API_BASE_URL      → ex: https://api-sandbox.ecobank.com
      ECOBANK_TOKEN_URL         → ex: /oauth/token
      ECOBANK_CLIENT_ID         → identifiant client OAuth2
      ECOBANK_CLIENT_SECRET     → secret client OAuth2
      ECOBANK_MERCHANT_ID       → identifiant commerçant (EcobankPay)
      ECOBANK_COLLECT_MOMO_PATH → ex: /v1/collections/momo
      ECOBANK_COLLECT_CARD_PATH → ex: /v1/collections/card
      ECOBANK_SETTLE_PATH       → ex: /v1/settlements
      ECOBANK_WEBHOOK_SECRET    → secret de signature des callbacks
    """

    name = "ecobank-live"

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self._base = (os.environ.get("ECOBANK_API_BASE_URL") or "").rstrip("/")
        self._token_url = os.environ.get("ECOBANK_TOKEN_URL", "/oauth/token")
        self._client_id = os.environ.get("ECOBANK_CLIENT_ID", "")
        self._client_secret = os.environ.get("ECOBANK_CLIENT_SECRET", "")
        self._merchant = os.environ.get("ECOBANK_MERCHANT_ID", "")
        self._timeout = timeout
        self._max_retries = max_retries
        self._token = None
        self._token_expiry = 0.0

    def _configured(self) -> bool:
        return bool(self._base and self._client_id and self._client_secret)

    def _require_configured(self):
        if not self._configured():
            raise EcobankError(
                "Client Ecobank non configuré — renseignez ECOBANK_API_BASE_URL, "
                "ECOBANK_CLIENT_ID, ECOBANK_CLIENT_SECRET. En attendant, utilisez "
                "ECOBANK_MODE=simulator.", code="ECOBANK_NOT_CONFIGURED")

    # ── HTTP (requests si dispo, sinon urllib) ─────────────────────────────
    def _post(self, path: str, body: Dict, headers: Optional[Dict] = None) -> Dict:
        payload = json.dumps(body).encode("utf-8")
        hdrs = {"Content-Type": "application/json", **(headers or {})}
        try:
            import requests
            r = requests.post(self._base + path, data=payload, headers=hdrs,
                              timeout=self._timeout)
            return self._parse_response(r.status_code, r.text)
        except ImportError:
            import urllib.request
            req = urllib.request.Request(self._base + path, data=payload,
                                         headers=hdrs, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    return self._parse_response(resp.status, resp.read().decode())
            except urllib.error.HTTPError as e:
                return self._parse_response(e.code, e.read().decode())

    def _parse_response(self, status: int, text: str) -> Dict:
        try:
            data = json.loads(text) if text else {}
        except Exception:
            data = {}
        if status >= 400:
            raise EcobankError(
                f"Ecobank HTTP {status}: {data.get('message', text[:200])}",
                code="ECOBANK_HTTP_ERROR",
                retryable=status in (408, 429, 500, 502, 503, 504))
        return data

    # ── OAuth2 client_credentials (avec cache) ─────────────────────────────
    def _access_token(self) -> str:
        self._require_configured()
        if self._token and time.time() < self._token_expiry:
            return self._token
        token = self._post(self._token_url, {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        })
        self._token = token.get("access_token", "")
        self._token_expiry = time.time() + int(token.get("expires_in", 3600)) - 60
        return self._token

    # ── Signature + retry idempotent ───────────────────────────────────────
    def _call(self, path: str, body: Dict, idempotency_key: str) -> Dict:
        self._require_configured()
        body = {**body, "merchantId": self._merchant}
        raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        signature = hmac.new(self._client_secret.encode(), raw, hashlib.sha256).hexdigest()
        headers = {
            "Authorization": f"Bearer {self._access_token()}",
            "Idempotency-Key": idempotency_key,
            "X-Signature": signature,
        }
        last: Optional[EcobankError] = None
        for attempt in range(self._max_retries):
            try:
                return self._post(path, body, headers)
            except EcobankError as e:
                if not e.retryable or attempt == self._max_retries - 1:
                    raise
                last = e
                time.sleep(min(2 ** attempt, 8))  # backoff exponentiel plafonné
        raise last if last else EcobankError("Échec après retries")

    # ── Contrat ────────────────────────────────────────────────────────────
    def collect_momo(self, amount, currency, phone, reference, idempotency_key):
        path = os.environ.get("ECOBANK_COLLECT_MOMO_PATH", "/v1/collections/momo")
        data = self._call(path, {
            "amount": float(amount), "currency": currency, "phone": phone,
            "reference": reference,
        }, idempotency_key)
        return _payment_result(reference, data.get("status", "pending"),
                               amount, currency, raw=data)

    def collect_card(self, amount, currency, card, reference, idempotency_key):
        path = os.environ.get("ECOBANK_COLLECT_CARD_PATH", "/v1/collections/card")
        data = self._call(path, {
            "amount": float(amount), "currency": currency, "card": card,
            "reference": reference,
        }, idempotency_key)
        return _payment_result(reference, data.get("status", "pending"),
                               amount, currency, raw=data)

    def settle(self, amount, currency, to_account, reference, idempotency_key):
        path = os.environ.get("ECOBANK_SETTLE_PATH", "/v1/settlements")
        data = self._call(path, {
            "amount": float(amount), "currency": currency,
            "fromAccount": FIDUCIARY_ACCOUNT, "toAccount": to_account,
            "reference": reference,
        }, idempotency_key)
        return _payment_result(reference, data.get("status", "pending"),
                               amount, currency, raw=data)

    def get_statement(self, date_iso):
        self._require_configured()
        path = os.environ.get("ECOBANK_STATEMENT_PATH", "/v1/statements")
        return self._call(path, {"date": date_iso},
                          f"stmt_{date_iso}").get("items", [])

    def get_balance(self, account, currency="XOF"):
        self._require_configured()
        path = os.environ.get("ECOBANK_BALANCE_PATH", "/v1/accounts/balance")
        return float(self._call(path, {"account": account, "currency": currency},
                                f"bal_{account}_{currency}").get("balance", 0.0))

    def verify_webhook(self, payload, signature):
        secret = os.environ.get("ECOBANK_WEBHOOK_SECRET", "")
        if not secret:
            return False
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature or "")


# ═══════════════════════════════════════════════════════════════════════════════
#  Factory
# ═══════════════════════════════════════════════════════════════════════════════

_client: Optional[EcobankClient] = None


def get_ecobank_client() -> EcobankClient:
    """Retourne le client bancaire actif (singleton).

    `ECOBANK_MODE=live` → client réel ; sinon → simulateur local.
    Surchargeable pour les tests via `set_ecobank_client()`.
    """
    global _client
    if _client is None:
        mode = os.environ.get("ECOBANK_MODE", "simulator").lower()
        if mode in ("live", "prod", "production"):
            _client = RealEcobankClient()
        else:
            _client = SimulatedEcobankClient()
        log.info(f"  🏦 Passerelle bancaire : {_client.name}")
    return _client


def set_ecobank_client(client: EcobankClient):
    """Injecte un client (tests / injection de dépendance)."""
    global _client
    _client = client


__all__ = [
    "EcobankClient", "EcobankError", "SimulatedEcobankClient", "RealEcobankClient",
    "get_ecobank_client", "set_ecobank_client", "UM_TO_CFA", "FIDUCIARY_ACCOUNT",
]
