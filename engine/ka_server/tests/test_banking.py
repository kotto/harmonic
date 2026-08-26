# -*- coding: utf-8 -*-
"""Tests du rapprochement bancaire KARE (passerelle Ecobank).

Couvre le plan de tests sandbox T1–T10 en mode simulateur (aucun réseau) :

  T1 · collecte Mobile Money réussie → émission UM
  T2 · collecte carte réussie → émission UM
  T3 · collecte échouée (fonds insuffisants) → aucune émission
  T4 · doublon (même Idempotency-Key) → une seule émission
  T5 · conversion prestataire → règlement XOF acquitté
  T6 · règlement échoué (compte clos) → UM dégelés
  T7 · plafond AML 5 000 UM/mois → rejet serveur
  T8 · rapprochement journalier → écart nul (adossement 1:1)
  T9 · webhook signé + rejeu idempotent
  T10· idempotence bancaire (un règlement rejoué ne duplique rien)

Lancement : python -m pytest ka_server/tests/test_banking.py -q  (depuis engine/)
"""

import os
import sys
import tempfile

import pytest

# ── Isolation des données + mode simulateur AVANT import du serveur ──
_TMP = tempfile.mkdtemp(prefix='ka_banking_test_')
os.environ['KA_BANKING_DIR'] = _TMP
os.environ['ECOBANK_MODE'] = 'simulator'
os.environ['KA_API_KEYS'] = 'test-banking-key-1234567890'

from ka_server.app import create_app  # noqa: E402
from ka_server.services import settlement  # noqa: E402
from ka_server.services.ecobank_gateway import get_ecobank_client, SimulatedEcobankClient  # noqa: E402

API_KEY = 'test-banking-key-1234567890'


@pytest.fixture(scope="module")
def app():
    return create_app()


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def _clean_state(app):
    """Repart d'un état vierge à chaque test (ledger + simulateur + rate-limit)."""
    settlement.reset_state()
    get_ecobank_client().reset()
    # Le rate-limit global (30 req/min/IP) s'applique aussi au test client :
    # on le vide entre les tests pour ne pas polluer les assertions avec des 429.
    store = getattr(app, 'ka_rate_limit_store', None)
    if store is not None:
        store.clear()
    yield


def _auth():
    return {'X-API-Key': API_KEY, 'Content-Type': 'application/json'}


def _idem(suffix):
    return f'test_{suffix}'


# ═════════════════════════════════════════════════════════════════════════════

def test_health_public(client):
    r = client.get('/api/banking/health')
    assert r.status_code == 200
    body = r.get_json()
    assert body['status'] == 'ok'
    assert body['gateway'] == 'ecobank-simulator'
    assert body['rate']['1_UM_CFA'] == 655


def test_auth_required(client):
    """Les endpoints d'écriture exigent une clé API (ou signature HMAC)."""
    r = client.post('/api/banking/conversion/request', json={
        'wallet_id': 'MED-1', 'amount_um': 1})
    assert r.status_code == 401


# ═══ T1 · Collecte Mobile Money réussie ═══
def test_T1_collect_momo_success(client):
    client.post('/api/banking/accounts', json={
        'wallet_id': 'PAT-1', 'role': 'patient'}, headers=_auth())
    r = client.post('/api/banking/collection/momo', json={
        'amount_fiat': 6550, 'currency': 'XOF', 'wallet_id': 'PAT-1',
        'phone': '77 123 45 67'}, headers={**_auth(), 'Idempotency-Key': _idem('t1')})
    assert r.status_code == 200
    col = r.get_json()['collection']
    assert col['status'] == 'settled'
    assert col['amount_um'] == 10  # 6550 XOF / 655 = 10 UM

    acc = client.get('/api/banking/accounts/PAT-1', headers=_auth()).get_json()
    assert acc['account']['balance_um'] == 10


# ═══ T2 · Collecte carte réussie ═══
def test_T2_collect_card_success(client):
    client.post('/api/banking/accounts', json={
        'wallet_id': 'PAT-2', 'role': 'patient'}, headers=_auth())
    r = client.post('/api/banking/collection/card', json={
        'amount_fiat': 32750, 'currency': 'XOF', 'wallet_id': 'PAT-2',
        'card': {'number': '4111111111111111', 'exp': '12/27', 'cvv': '123'}},
        headers={**_auth(), 'Idempotency-Key': _idem('t2')})
    assert r.status_code == 200
    assert r.get_json()['collection']['status'] == 'settled'
    acc = client.get('/api/banking/accounts/PAT-2', headers=_auth()).get_json()
    assert acc['account']['balance_um'] == 50  # 32750 / 655


# ═══ T3 · Collecte échouée → aucune émission ═══
def test_T3_collect_failed_no_emission(client):
    client.post('/api/banking/accounts', json={
        'wallet_id': 'PAT-3', 'role': 'patient'}, headers=_auth())
    r = client.post('/api/banking/collection/momo', json={
        'amount_fiat': 6550, 'currency': 'XOF', 'wallet_id': 'PAT-3',
        'phone': '77 000 000 0000'},  # se termine par 0000 → fonds insuffisants
        headers={**_auth(), 'Idempotency-Key': _idem('t3')})
    assert r.status_code == 200
    assert r.get_json()['collection']['status'] == 'failed'
    acc = client.get('/api/banking/accounts/PAT-3', headers=_auth()).get_json()
    assert acc['account']['balance_um'] == 0  # aucune UM émise


# ═══ T4 · Doublon (même Idempotency-Key) → une seule émission ═══
def test_T4_idempotent_collection(client):
    client.post('/api/banking/accounts', json={
        'wallet_id': 'PAT-4', 'role': 'patient'}, headers=_auth())
    payload = {'amount_fiat': 13100, 'currency': 'XOF', 'wallet_id': 'PAT-4',
               'phone': '77 111 22 33'}
    for _ in range(2):  # rejeu de la même clé
        r = client.post('/api/banking/collection/momo', json=payload,
                        headers={**_auth(), 'Idempotency-Key': _idem('t4')})
        assert r.status_code == 200
    acc = client.get('/api/banking/accounts/PAT-4', headers=_auth()).get_json()
    assert acc['account']['balance_um'] == 20  # 13100/655, une seule fois


# ═══ T5 · Conversion prestataire → règlement XOF ═══
def test_T5_conversion_settled(client):
    settlement.upsert_account('MED-1', 'medecin', bank_account='PREST_MED-1')
    assert settlement.credit_um('MED-1', 100, tx_type='payment')['ok']
    r = client.post('/api/banking/conversion/request', json={
        'wallet_id': 'MED-1', 'amount_um': 10, 'currency': 'XOF'},
        headers=_auth())
    assert r.status_code == 200
    conv = r.get_json()['conversion']
    assert conv['status'] == 'requested'
    assert conv['amount_cfa'] == 6550

    r = client.post(f"/api/banking/conversion/{conv['id']}/execute", headers=_auth())
    assert r.status_code == 200
    body = r.get_json()
    assert body['conversion']['status'] == 'settled'
    assert body['bank']['status'] == 'settled'

    # Le compte fiduciaire a été débité, le compte prestataire crédité.
    bank = get_ecobank_client()
    assert bank.get_balance('PREST_MED-1') == 6550


# ═══ T6 · Règlement échoué (compte clos) → UM dégelés ═══
def test_T6_settlement_failed_unfreeze(client):
    settlement.upsert_account('MED-CLOSED', 'medecin', bank_account='CLOSED_001')
    assert settlement.credit_um('MED-CLOSED', 50, tx_type='payment')['ok']
    r = client.post('/api/banking/conversion/request', json={
        'wallet_id': 'MED-CLOSED', 'amount_um': 20, 'currency': 'XOF'},
        headers=_auth())
    conv = r.get_json()['conversion']
    # Gel : solde 30, gelé 20
    acc = settlement.get_account('MED-CLOSED')
    assert acc['balance_um'] == 30 and acc['frozen_um'] == 20

    r = client.post(f"/api/banking/conversion/{conv['id']}/execute", headers=_auth())
    assert r.status_code == 200
    assert r.get_json()['conversion']['status'] == 'failed'

    # Dégel : les UM sont rendus, rien n'est perdu.
    acc = settlement.get_account('MED-CLOSED')
    assert acc['balance_um'] == 50 and acc['frozen_um'] == 0


# ═══ T7 · Plafond AML 5 000 UM/mois ═══
def test_T7_aml_limit(client):
    # Un crédit de solidarité au-delà du plafond est refusé côté serveur.
    settlement.upsert_account('PAT-7', 'patient')
    res = settlement.credit_um('PAT-7', 6000)  # > 5000
    assert res['ok'] is False and 'AML' in res['error']

    # Une collecte diaspora qui ferait dépasser le plafond est rejetée sans appel bancaire.
    r = client.post('/api/banking/collection/momo', json={
        'amount_fiat': 655 * 6000, 'currency': 'XOF', 'wallet_id': 'PAT-7',
        'phone': '77 000 00 00'}, headers={**_auth(), 'Idempotency-Key': _idem('t7')})
    assert r.get_json()['collection']['status'] == 'rejected'


# ═══ T8 · Rapprochement journalier → écart nul ═══
def test_T8_reconciliation_balanced(client):
    from datetime import date
    today = date.today().isoformat()
    client.post('/api/banking/accounts', json={
        'wallet_id': 'PAT-8', 'role': 'patient'}, headers=_auth())
    client.post('/api/banking/collection/momo', json={
        'amount_fiat': 65500, 'currency': 'XOF', 'wallet_id': 'PAT-8',
        'phone': '77 444 55 66'}, headers={**_auth(), 'Idempotency-Key': _idem('t8')})

    r = client.get(f'/api/banking/reconciliation/{today}', headers=_auth())
    assert r.status_code == 200
    rec = r.get_json()['reconciliation']
    assert rec['balanced'] is True
    assert rec['ledger_collects'] == rec['bank_collects'] == 65500
    assert rec['ecart_collects'] == 0


# ═══ T9 · Webhook signé + rejeu ═══
def test_T9_webhook(client):
    import hashlib
    import hmac
    payload = b'{"reference":"KARE_coll_x","status":"settled"}'
    sig = hmac.new(b'simulator-secret', payload, hashlib.sha256).hexdigest()

    for _ in range(2):  # rejeu du même webhook
        r = client.post('/api/banking/webhook/ecobank', data=payload,
                        content_type='application/json',
                        headers={'X-Ecobank-Signature': sig})
        assert r.status_code == 200
        assert r.get_json()['received'] is True

    # Mauvaise signature → refusé.
    r = client.post('/api/banking/webhook/ecobank', data=payload,
                    content_type='application/json',
                    headers={'X-Ecobank-Signature': 'mauvais'})
    assert r.status_code == 401


# ═══ T10 · Idempotence bancaire (règlement rejoué) ═══
def test_T10_bank_settlement_idempotent(client):
    settlement.upsert_account('MED-10', 'medecin', bank_account='PREST_MED-10')
    assert settlement.credit_um('MED-10', 100, tx_type='payment')['ok']
    r = client.post('/api/banking/conversion/request', json={
        'wallet_id': 'MED-10', 'amount_um': 5, 'currency': 'XOF'}, headers=_auth())
    conv_id = r.get_json()['conversion']['id']

    # Exécution rejouée deux fois → le règlement n'est compté qu'une seule fois.
    client.post(f'/api/banking/conversion/{conv_id}/execute', headers=_auth())
    r = client.post(f'/api/banking/conversion/{conv_id}/execute', headers=_auth())
    assert r.status_code == 400  # état déjà settled → invalide

    bank = get_ecobank_client()
    assert bank.get_balance('PREST_MED-10') == 3275  # 5 UM * 655, une seule fois


# ═════════════════════════════════════════════════════════════════════════════
#  Extension — paiement de soin, solidarité, lectures (console)
# ═════════════════════════════════════════════════════════════════════════════

def test_payment_patient_to_provider(client):
    """Paiement d'un soin : débite le patient, crédite le prestataire."""
    settlement.upsert_account('PAT-P', 'patient')
    settlement.upsert_account('MED-P', 'medecin')
    assert settlement.credit_um('PAT-P', 100, tx_type='collection')['ok']

    r = client.post('/api/banking/payment', json={
        'wallet_id': 'PAT-P', 'recipient': 'MED-P', 'amount_um': 30,
        'description': 'Consultation'}, headers=_auth())
    assert r.status_code == 200
    assert r.get_json()['tx']['type'] == 'payment'

    assert settlement.get_account('PAT-P')['balance_um'] == 70
    assert settlement.get_account('MED-P')['balance_um'] == 30


def test_payment_insufficient_funds(client):
    """Paiement refusé si solde insuffisant."""
    settlement.upsert_account('PAT-I', 'patient')
    r = client.post('/api/banking/payment', json={
        'wallet_id': 'PAT-I', 'recipient': 'MED-I', 'amount_um': 10}, headers=_auth())
    assert r.status_code == 400
    assert r.get_json()['code'] == 'INSUFFICIENT_FUNDS'


def test_solidarite_credit_and_aml(client):
    """Crédit de solidarité direct + plafond AML."""
    settlement.upsert_account('PAT-S', 'patient')
    r = client.post('/api/banking/solidarite/credit', json={
        'wallet_id': 'PAT-S', 'amount_um': 100, 'description': 'Aide'}, headers=_auth())
    assert r.status_code == 200
    assert settlement.get_account('PAT-S')['balance_um'] == 100

    # Dépassement du plafond → rejet.
    r = client.post('/api/banking/solidarite/credit', json={
        'wallet_id': 'PAT-S', 'amount_um': 5000}, headers=_auth())
    assert r.status_code == 400
    assert r.get_json()['code'] == 'AML_LIMIT'


def test_read_endpoints_for_console(client):
    """Endpoints de lecture utilisés par la console d'administration."""
    settlement.upsert_account('PAT-R', 'patient', bank_account='PREST_PAT-R')
    settlement.credit_um('PAT-R', 10, tx_type='collection')

    r = client.get('/api/banking/accounts-list', headers=_auth())
    assert r.status_code == 200
    assert any(a['wallet_id'] == 'PAT-R' for a in r.get_json()['accounts'])

    r = client.get('/api/banking/ledger?limit=5', headers=_auth())
    assert r.status_code == 200
    assert isinstance(r.get_json()['entries'], list)

    r = client.get('/api/banking/conversions', headers=_auth())
    assert r.status_code == 200
    assert isinstance(r.get_json()['conversions'], list)


def test_banking_console_page_served(client):
    """La console d'administration est servie."""
    r = client.get('/banking/console')
    assert r.status_code == 200
    assert b'Console bancaire' in r.data or b'KARE' in r.data


# ══════════════════════════════════════════════════════════════════════════════
#  Seed / Reset / Scenario
# ══════════════════════════════════════════════════════════════════════════════

def test_seed_demo_creates_accounts(client):
    """Le seed crée une économie de démonstration complète."""
    r = client.post('/api/banking/seed', headers=_auth())
    assert r.status_code == 200
    s = r.get_json()['summary']
    assert s['wallets_created'] == 21
    assert s['patients'] == 10
    assert s['providers'] == 11
    assert s['payments'] > 0
    assert s['ledger_entries'] > 0
    assert s['conversions_seeded'] == 5
    assert s['collections_seeded'] == 3

    # Vérifier que le ledger a des entrées de tout type
    ledger = client.get('/api/banking/ledger', headers=_auth()).get_json()['entries']
    types = set(e['type'] for e in ledger)
    assert 'solidarite_credit' in types
    assert 'payment' in types
    assert 'conversion_request' in types
    assert 'conversion_settled' in types
    assert 'conversion_failed' in types

    # Vérifier que le simulateur bancaire est synchronisé
    bank = get_ecobank_client()
    assert isinstance(bank, SimulatedEcobankClient)
    # Les comptes des conversions réglées existent dans le simulateur
    # (BANK_TOURE = 20 UM * 655 = 13100 XOF, BANK_PHM_CENTRALE = 70 * 655 = 45850 XOF)
    assert bank.get_balance('BANK_TOURE', 'XOF') == 13100.0
    assert bank.get_balance('BANK_PHM_CENTRALE', 'XOF') == 45850.0
    bank = get_ecobank_client()
    assert bank.get_balance('BANK_KONE') == 0.0  # compte de prestataire, pas fiduciaire


def test_seed_is_idempotent(client):
    """Deux seeds de suite : le deuxième remplace proprement le premier."""
    r1 = client.post('/api/banking/seed', headers=_auth())
    r2 = client.post('/api/banking/seed', headers=_auth())
    assert r2.status_code == 200
    # Le deuxième seed a reset puis repeuplé → état cohérent
    assert r2.get_json()['summary']['ledger_entries'] > 0


def test_reset_clears_everything(client):
    """Reset après seed → tout vide."""
    client.post('/api/banking/seed', headers=_auth())
    r = client.post('/api/banking/reset', headers=_auth())
    assert r.status_code == 200
    assert r.get_json()['ledger_entries_deleted'] > 0
    summary = client.get('/api/banking/summary', headers=_auth()).get_json()['summary']
    assert summary['accounts'] == 0
    assert summary['ledger_entries'] == 0


def test_scenario_full_walkthrough(client):
    """Scénario complet : création → crédit → paiement → conversion → règlement."""
    steps = [
        {"action": "create_account", "wallet_id": "PAT-SC", "role": "patient"},
        {"action": "create_account", "wallet_id": "MED-SC", "role": "medecin",
         "bank_account": "BANK_MED_SC"},
        {"action": "credit", "wallet_id": "PAT-SC", "amount_um": 200,
         "description": "Aide test"},
        {"action": "debit", "from": "PAT-SC", "to": "MED-SC", "amount_um": 50,
         "description": "Consultation test"},
        {"action": "request_conversion", "wallet_id": "MED-SC", "amount_um": 50},
    ]
    r = client.post('/api/banking/scenario', json={"steps": steps}, headers=_auth())
    assert r.status_code == 200, r.get_json()
    sc = r.get_json()['scenario']
    assert sc['total'] == 5
    assert sc['success'] is True

    # Vérifier l'état final
    assert settlement.get_account('PAT-SC')['balance_um'] == 150
    assert settlement.get_account('MED-SC')['balance_um'] == 0
    assert settlement.get_account('MED-SC')['frozen_um'] == 50

    # Récupérer l'ID de conversion généré et exécuter le règlement
    conversions = settlement.list_conversions()
    conv_id = conversions[0]['id']
    r2 = client.post('/api/banking/scenario', json={"steps": [
        {"action": "execute_settlement", "conversion_id": conv_id},
        {"action": "reconcile"},
    ]}, headers=_auth())
    assert r2.status_code == 200
    assert settlement.get_conversion(conv_id)['status'] == 'settled'


def test_scenario_unknown_action(client):
    """Action inconnue → erreur mais pas de crash."""
    r = client.post('/api/banking/scenario', json={"steps": [
        {"action": "unknown_action", "foo": "bar"},
    ]}, headers=_auth())
    assert r.status_code == 400
    assert len(r.get_json()['scenario']['errors']) == 1


def test_scenario_empty_steps(client):
    """Script vide → 400."""
    r = client.post('/api/banking/scenario', json={"steps": []}, headers=_auth())
    assert r.status_code == 400
