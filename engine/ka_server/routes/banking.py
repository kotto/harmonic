"""
banking.py — Routes bancaires KARE (Ecobank)
=============================================
Endpoints serveur de l'économie en Unités Médicales (UM) :
émission (collecte fiat → UM) et conversion (UM → CFA / XOF).

Authentification : clé API (X-API-Key) OU signature HMAC-SHA256 du corps
(X-Signature, secret partagé KA_BANKING_SECRET — privilégié pour le mobile).
Le webhook Ecobank est authentifié par HMAC (ECOBANK_WEBHOOK_SECRET).

Idempotence : en-tête `Idempotency-Key` — une même clé rejouée ne duplique
jamais une collecte ni une émission UM.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import threading
import time
from functools import wraps

from flask import request, jsonify

from ..middleware.auth import validate_api_key
from ..services import settlement as settle

log = logging.getLogger(__name__)


# ── Auth : clé API OU signature HMAC du corps ────────────────────────────────

def _require_banking_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. Signature HMAC du corps (secret partagé) — privilégié pour le mobile.
        secret = os.environ.get("KA_BANKING_SECRET", "")
        if secret:
            sig = request.headers.get("X-Signature", "")
            body = request.get_data()
            expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
            if sig and hmac.compare_digest(expected, sig):
                return f(*args, **kwargs)
        # 2. Clé API (X-API-Key ou Bearer) — cohérent avec /api/wave et enterprise.
        api_key = (request.headers.get("X-API-Key") or
                   request.headers.get("Authorization", "").replace("Bearer ", ""))
        if api_key and validate_api_key(api_key):
            return f(*args, **kwargs)
        return jsonify({"error": "Authentification requise", "code": "AUTH_REQUIRED"}), 401
    return decorated


def _idem_key() -> str:
    return (request.headers.get("Idempotency-Key") or "").strip()


# ── Blueprint ─────────────────────────────────────────────────────────────────

def register_banking_routes(app, services):
    """Enregistre les routes bancaires KARE."""

    # ═══ SANTÉ (public) ═══
    @app.route('/api/banking/health', methods=['GET', 'OPTIONS'])
    def api_banking_health():
        """État de la passerelle bancaire (mode simulateur / live)."""
        if request.method == 'OPTIONS':
            return '', 200
        from ..services.ecobank_gateway import get_ecobank_client, UM_TO_CFA
        client = get_ecobank_client()
        return jsonify({
            "service": "kare-banking",
            "status": "ok",
            "gateway": client.name,
            "rate": {"1_UM": "1 EUR", "1_UM_CFA": UM_TO_CFA, "currency": "XOF"},
            "invariant": "fiat en fiducie = UM en circulation (adossement 1:1)",
            "summary": settle.get_state_summary(),
        }), 200

    # ═══ COMPTES ═══
    @app.route('/api/banking/accounts', methods=['POST', 'OPTIONS'])
    @_require_banking_auth
    def api_banking_accounts():
        """Crée/met à jour un compte (wallet serveur)."""
        if request.method == 'OPTIONS':
            return '', 200
        data = request.get_json() or {}
        wallet_id = (data.get("wallet_id") or "").strip()
        role = (data.get("role") or "patient").strip()
        if not wallet_id:
            return jsonify({"error": "wallet_id requis", "code": "MISSING_WALLET"}), 400
        acc = settle.upsert_account(wallet_id, role, data.get("bank_account"))
        return jsonify({"success": True, "account": acc}), 200

    @app.route('/api/banking/accounts/<wallet_id>', methods=['GET', 'OPTIONS'])
    @_require_banking_auth
    def api_banking_account(wallet_id):
        """Solde et statut d'un compte."""
        if request.method == 'OPTIONS':
            return '', 200
        acc = settle.get_account(wallet_id)
        if not acc:
            return jsonify({"error": "Compte inconnu", "code": "ACCOUNT_NOT_FOUND"}), 404
        return jsonify({"wallet_id": wallet_id, "account": acc,
                        "aml": settle.check_monthly_solidarite_limit(wallet_id)}), 200

    @app.route('/api/banking/accounts-list', methods=['GET', 'OPTIONS'])
    @_require_banking_auth
    def api_banking_accounts_list():
        """Liste tous les comptes (console d'administration)."""
        if request.method == 'OPTIONS':
            return '', 200
        return jsonify({"success": True, "accounts": settle.list_accounts()}), 200

    # ═══ SOLIDARITÉ (crédit direct → patient) ═══
    @app.route('/api/banking/solidarite/credit', methods=['POST', 'OPTIONS'])
    @_require_banking_auth
    def api_solidarite_credit():
        """Crédite un patient (solidarité) — plafonné AML 5 000 UM/mois."""
        if request.method == 'OPTIONS':
            return '', 200
        data = request.get_json() or {}
        wallet_id = (data.get("wallet_id") or "").strip()
        amount = data.get("amount_um")
        if not wallet_id or not amount:
            return jsonify({"error": "wallet_id, amount_um requis",
                            "code": "MISSING_FIELDS"}), 400
        result = settle.credit_um(wallet_id, float(amount),
                                  description=data.get("description", ""))
        if not result.get("ok"):
            return jsonify({"error": result.get("error"),
                            "limit": result.get("limit"),
                            "total": result.get("total"),
                            "code": "AML_LIMIT"}), 400
        return jsonify({"success": True, "tx": result["tx"]}), 200

    # ═══ COLLECTE (fiat → UM) ═══
    @app.route('/api/banking/collection/momo', methods=['POST', 'OPTIONS'])
    @_require_banking_auth
    def api_collection_momo():
        """Collecte Mobile Money → émission UM au bénéficiaire."""
        if request.method == 'OPTIONS':
            return '', 200
        data = request.get_json() or {}
        amount = data.get("amount_fiat")
        wallet_id = (data.get("wallet_id") or "").strip()
        phone = (data.get("phone") or "").strip()
        if not amount or not wallet_id or not phone:
            return jsonify({"error": "amount_fiat, wallet_id, phone requis",
                            "code": "MISSING_FIELDS"}), 400
        result = settle.record_collection(
            "momo", float(amount), data.get("currency", "XOF"),
            wallet_id, {"phone": phone}, _idem_key())
        return jsonify({"success": result.get("status") == "settled", "collection": result}), 200

    @app.route('/api/banking/collection/card', methods=['POST', 'OPTIONS'])
    @_require_banking_auth
    def api_collection_card():
        """Collecte carte bancaire → émission UM au bénéficiaire."""
        if request.method == 'OPTIONS':
            return '', 200
        data = request.get_json() or {}
        amount = data.get("amount_fiat")
        wallet_id = (data.get("wallet_id") or "").strip()
        card = data.get("card")
        if not amount or not wallet_id or not card:
            return jsonify({"error": "amount_fiat, wallet_id, card requis",
                            "code": "MISSING_FIELDS"}), 400
        result = settle.record_collection(
            "card", float(amount), data.get("currency", "XOF"),
            wallet_id, {"card": card}, _idem_key())
        return jsonify({"success": result.get("status") == "settled", "collection": result}), 200

    # ═══ PAIEMENT (patient → prestataire, en UM) ═══
    @app.route('/api/banking/payment', methods=['POST', 'OPTIONS'])
    @_require_banking_auth
    def api_payment():
        """Règle un soin : débite le patient, crédite le prestataire (UM)."""
        if request.method == 'OPTIONS':
            return '', 200
        data = request.get_json() or {}
        wallet_id = (data.get("wallet_id") or data.get("from") or "").strip()
        recipient = (data.get("recipient") or data.get("to") or "").strip()
        amount = data.get("amount_um") or data.get("amount")
        if not wallet_id or not recipient or not amount:
            return jsonify({"error": "wallet_id, recipient, amount_um requis",
                            "code": "MISSING_FIELDS"}), 400
        result = settle.debit_um(
            wallet_id, float(amount), recipient,
            description=data.get("description", ""),
            metadata=data.get("metadata"))
        if not result.get("ok"):
            return jsonify({"error": result.get("error"),
                            "available": result.get("available"),
                            "code": "INSUFFICIENT_FUNDS"}), 400
        return jsonify({"success": True, "tx": result["tx"]}), 200

    # ═══ CONVERSION (UM → CFA) ═══
    @app.route('/api/banking/conversion/request', methods=['POST', 'OPTIONS'])
    @_require_banking_auth
    def api_conversion_request():
        """Demande de conversion UM → CFA (prestataire). Gèle les UM."""
        if request.method == 'OPTIONS':
            return '', 200
        data = request.get_json() or {}
        wallet_id = (data.get("wallet_id") or "").strip()
        amount = data.get("amount_um")
        if not wallet_id or not amount:
            return jsonify({"error": "wallet_id, amount_um requis",
                            "code": "MISSING_FIELDS"}), 400
        result = settle.request_conversion(
            wallet_id, float(amount), data.get("currency", "XOF"), data.get("bank_info"))
        if not result.get("ok"):
            return jsonify({"error": result.get("error"),
                            "role": result.get("role"),
                            "available": result.get("available"),
                            "code": "CONVERSION_REJECTED"}), 400
        return jsonify({"success": True, "conversion": result["conversion"]}), 200

    @app.route('/api/banking/conversion/<conversion_id>/execute', methods=['POST', 'OPTIONS'])
    @_require_banking_auth
    def api_conversion_execute(conversion_id):
        """Exécute le règlement bancaire d'une conversion gelée."""
        if request.method == 'OPTIONS':
            return '', 200
        result = settle.execute_settlement(conversion_id)
        if not result.get("ok"):
            return jsonify({"error": result.get("error"), "code": "SETTLEMENT_ERROR"}), 400
        return jsonify({"success": result["conversion"]["status"] == "settled",
                        "conversion": result["conversion"],
                        "bank": result["bank"]}), 200

    @app.route('/api/banking/conversion/<conversion_id>', methods=['GET', 'OPTIONS'])
    @_require_banking_auth
    def api_conversion_status(conversion_id):
        """Statut d'une conversion."""
        if request.method == 'OPTIONS':
            return '', 200
        conv = settle.get_conversion(conversion_id)
        if not conv:
            return jsonify({"error": "Conversion inconnue", "code": "NOT_FOUND"}), 404
        return jsonify({"conversion": conv}), 200

    # ═══ WEBHOOK ECOBANK ═══
    @app.route('/api/banking/webhook/ecobank', methods=['POST', 'OPTIONS'])
    def api_ecobank_webhook():
        """Callback de statut Ecobank (collecte / règlement).

        Authentifié par HMAC-SHA256 (ECOBANK_WEBHOOK_SECRET), pas par clé API.
        Reçu un paiement asynchrone : ici on acquitte / annule côté ledger.
        """
        if request.method == 'OPTIONS':
            return '', 200
        from ..services.ecobank_gateway import get_ecobank_client
        client = get_ecobank_client()
        sig = request.headers.get("X-Ecobank-Signature", "")
        if not client.verify_webhook(request.get_data(), sig):
            return jsonify({"error": "Signature webhook invalide", "code": "BAD_SIGNATURE"}), 401
        payload = request.get_json(force=True, silent=True) or {}
        log.info(f"Webhook Ecobank reçu: {payload.get('reference')} → {payload.get('status')}")
        # La machine d'état complète (acquittement des règlements en attente)
        # sera branchée ici une fois le format exact du callback fourni par Ecobank.
        return jsonify({"received": True,
                        "reference": payload.get("reference"),
                        "status": payload.get("status")}), 200

    # ═══ RAPPROCHEMENT ═══
    @app.route('/api/banking/reconciliation/<date_iso>', methods=['GET', 'OPTIONS'])
    @_require_banking_auth
    def api_reconciliation(date_iso):
        """Rapprochement journalier : ledger UM ↔ relevé bancaire."""
        if request.method == 'OPTIONS':
            return '', 200
        return jsonify({"success": True, "reconciliation": settle.reconcile(date_iso)}), 200

    @app.route('/api/banking/summary', methods=['GET', 'OPTIONS'])
    @_require_banking_auth
    def api_banking_summary():
        """Vue d'ensemble de l'économie UM."""
        if request.method == 'OPTIONS':
            return '', 200
        return jsonify({"success": True, "summary": settle.get_state_summary()}), 200

    # ═══ LECTURES (console d'administration) ═══
    @app.route('/api/banking/ledger', methods=['GET', 'OPTIONS'])
    @_require_banking_auth
    def api_banking_ledger():
        """Dernières entrées du ledger (append-only)."""
        if request.method == 'OPTIONS':
            return '', 200
        limit = min(int(request.args.get('limit', 100)), 1000)
        return jsonify({"success": True, "entries": settle.get_ledger(limit)}), 200

    @app.route('/api/banking/conversions', methods=['GET', 'OPTIONS'])
    @_require_banking_auth
    def api_banking_conversions():
        """Liste des conversions (toutes, les plus récentes d'abord)."""
        if request.method == 'OPTIONS':
            return '', 200
        return jsonify({"success": True, "conversions": settle.list_conversions()}), 200

    # ═══ SEED / RESET (bac à sable) ═══
    @app.route('/api/banking/seed', methods=['POST', 'OPTIONS'])
    @_require_banking_auth
    def api_banking_seed():
        """Peuple la base de données de démonstration (21 comptes, ledger, conversions)."""
        if request.method == 'OPTIONS':
            return '', 200
        summary = settle.seed_demo()
        return jsonify({"success": True, "summary": summary}), 200

    @app.route('/api/banking/reset', methods=['POST', 'OPTIONS'])
    @_require_banking_auth
    def api_banking_reset():
        """Vide toutes les données (remet à zéro)."""
        if request.method == 'OPTIONS':
            return '', 200
        n = settle.reset_state()
        try:
            from ..services.ecobank_gateway import get_ecobank_client as _g
            _g().reset()
        except Exception:
            pass
        return jsonify({"success": True, "ledger_entries_deleted": n}), 200

    @app.route('/api/banking/scenario', methods=['POST', 'OPTIONS'])
    @_require_banking_auth
    def api_banking_scenario():
        """Exécute un script de scénario (liste d'étapes).

        Body: {
          "steps": [
            {"action": "create_account", "wallet_id": "...", "role": "patient"},
            {"action": "credit", "wallet_id": "...", "amount_um": 100},
            {"action": "debit", "from": "...", "to": "...", "amount_um": 30},
            {"action": "request_conversion", "wallet_id": "...", "amount_um": 30},
            {"action": "execute_settlement", "conversion_id": null},
            {"action": "reconcile", "date": "today"}
          ]
        }

        Les actions supportées :
          create_account, credit, debit, request_conversion, execute_settlement,
          collect_momo, reconcile, sleep
        """
        if request.method == 'OPTIONS':
            return '', 200
        data = request.get_json() or {}
        steps = data.get("steps", [])
        if not steps:
            return jsonify({"error": "Aucune étape", "code": "MISSING_STEPS"}), 400
        result = settle.seed_scenario(steps)
        status = 200 if result["success"] else 400
        return jsonify({"success": result["success"], "scenario": result}), status

    # ═══ SIMULATION MULTI-AGENTS (téléphones réels via internet) ═══
    @app.route('/api/banking/simulate/scenarios', methods=['GET', 'OPTIONS'])
    @_require_banking_auth
    def api_simulate_scenarios():
        """Liste les scénarios de simulation disponibles."""
        if request.method == 'OPTIONS':
            return '', 200
        try:
            from ..services.simulation import list_scenarios
            scenarios = list_scenarios()
            return jsonify({"success": True, "scenarios": scenarios}), 200
        except Exception as e:
            return jsonify({"error": str(e), "code": "SIMULATION_ERROR"}), 500

    @app.route('/api/banking/simulate', methods=['POST', 'OPTIONS'])
    @_require_banking_auth
    def api_simulate():
        """Lance une simulation multi-agents (téléphones réels via internet).

        Body (scénario intégré) :
          {"scenario": "consultation_transfrontaliere"}

        Body (scénario personnalisé) :
          {
            "name": "Mon scénario",
            "description": "...",
            "agents": [
              {"wallet_id": "PAT-EX", "role": "patient", "name": "Exemple",
               "location": "Ville", "latency_min_ms": 50, "latency_max_ms": 200,
               "reliability": 0.95, "bank_account": "BANK_EX"}
            ],
            "steps": [
              {"action": "create_account", "wallet_id": "PAT-EX"},
              {"action": "credit", "wallet_id": "PAT-EX", "amount_um": 100}
            ]
          }

        Options :
          async=false (défaut) : attend la fin, retourne le résumé
          async=true          : lance en arrière-plan, retourne immédiatement
        """
        if request.method == 'OPTIONS':
            return '', 200
        data = request.get_json() or {}
        async_mode = data.get("async", False)

        try:
            from ..services.simulation import get_engine, run_scenario, run_custom_scenario

            if "scenario" in data and isinstance(data["scenario"], str):
                # Scénario intégré
                scenario_name = data["scenario"]
                if async_mode:
                    thread = threading.Thread(
                        target=run_scenario,
                        args=(scenario_name,),
                        kwargs={"reset_first": data.get("reset", True)},
                        daemon=True)
                    thread.start()
                    return jsonify({
                        "success": True, "async": True,
                        "message": f"Simulation « {scenario_name} » lancée en arrière-plan",
                        "status_url": "/api/banking/simulate/status",
                    }), 200
                else:
                    summary = run_scenario(
                        scenario_name,
                        reset_first=data.get("reset", True))
                    engine = get_engine()
                    return jsonify({
                        "success": True, "async": False,
                        "summary": summary,
                        "simulation": engine.to_dict(),
                    }), 200
            else:
                # Scénario personnalisé
                name = data.get("name", "Personnalisé")
                description = data.get("description", "")
                agents = data.get("agents", [])
                steps = data.get("steps", [])
                if not agents or not steps:
                    return jsonify({"error": "agents et steps requis",
                                    "code": "MISSING_FIELDS"}), 400
                if async_mode:
                    thread = threading.Thread(
                        target=run_custom_scenario,
                        args=(name, description, agents, steps),
                        kwargs={"reset_first": data.get("reset", True)},
                        daemon=True)
                    thread.start()
                    return jsonify({
                        "success": True, "async": True,
                        "message": f"Simulation « {name} » lancée en arrière-plan",
                        "status_url": "/api/banking/simulate/status",
                    }), 200
                else:
                    summary = run_custom_scenario(
                        name, description, agents, steps,
                        reset_first=data.get("reset", True))
                    engine = get_engine()
                    return jsonify({
                        "success": True, "async": False,
                        "summary": summary,
                        "simulation": engine.to_dict(),
                    }), 200
        except Exception as e:
            log.exception("simulation error")
            return jsonify({"error": str(e), "code": "SIMULATION_ERROR"}), 500

    @app.route('/api/banking/simulate/status', methods=['GET', 'OPTIONS'])
    def api_simulate_status():
        """Statut de la simulation en cours (pour polling)."""
        if request.method == 'OPTIONS':
            return '', 200
        try:
            from ..services.simulation import get_engine
            engine = get_engine()
            return jsonify({
                "success": True,
                "running": engine._running if hasattr(engine, '_running') else False,
                "summary": engine.summary() if hasattr(engine, 'summary') else {},
                "events": engine.to_dict().get("events", []) if hasattr(engine, 'to_dict') else [],
            }), 200
        except Exception as e:
            return jsonify({"error": str(e), "code": "SIMULATION_ERROR"}), 500


__all__ = ["register_banking_routes"]
