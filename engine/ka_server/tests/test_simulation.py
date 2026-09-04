# -*- coding: utf-8 -*-
"""Tests de la simulation multi-agents KARE (téléphones réels via internet).

Couvre :
  - Scénarios intégrés (consultation, diaspora, urgence)
  - Scénario personnalisé
  - Agents avec latence réseau et fiabilité
  - Endpoints API de simulation
  - Idempotence et reproductibilité

Lancement : python -m pytest ka_server/tests/test_simulation.py -q  (depuis engine/)
"""

import os
import sys
import tempfile

import pytest

# ── Isolation AVANT import du serveur ──
_TMP = tempfile.mkdtemp(prefix='ka_sim_test_')
os.environ['KA_BANKING_DIR'] = _TMP
os.environ['ECOBANK_MODE'] = 'simulator'
os.environ['KA_API_KEYS'] = 'test-banking-key-1234567890'

from ka_server.app import create_app  # noqa: E402
from ka_server.services import settlement  # noqa: E402
from ka_server.services.banking_gateway import get_payment_processor  # noqa: E402
from ka_server.services.simulation import (  # noqa: E402
    SimulationEngine, SimAgent, run_scenario, run_custom_scenario,
    list_scenarios, get_engine, list_results,
)

API_KEY = 'test-banking-key-1234567890'


@pytest.fixture(scope="module")
def app():
    return create_app()


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def _clean_state():
    """Repart d'un état vierge à chaque test."""
    settlement.reset_state()
    get_payment_processor().reset()
    # Réinitialiser le moteur
    from ka_server.services.simulation import _engine
    import ka_server.services.simulation as _sim
    _sim._engine = None
    yield


def _auth():
    return {'X-API-Key': API_KEY, 'Content-Type': 'application/json'}


# ══════════════════════════════════════════════════════════════════════════════
#  Tests unitaires du moteur
# ══════════════════════════════════════════════════════════════════════════════

def test_list_scenarios(client):
    """Les scénarios intégrés sont listés."""
    # Via l'API
    r = client.get('/api/banking/simulate/scenarios', headers=_auth())
    assert r.status_code == 200
    scenarios = r.get_json()['scenarios']
    names = [s['name'] for s in scenarios]
    assert 'consultation_transfrontaliere' in names
    assert 'aide_diaspora' in names
    assert 'reseau_soins_urgents' in names

    # Via la fonction
    assert len(list_scenarios()) >= 3


def test_consultation_scenario(client):
    """Scénario consultation transfrontalière Abidjan ↔ Paris."""
    summary = run_scenario("consultation_transfrontaliere", deterministic=True)
    assert summary['scenario_key'] == "consultation_transfrontaliere"
    assert summary['success'] == 8  # 8 étapes, toutes réussies
    assert summary['agents'] == 3

    # Vérifier les soldes : patient a payé, médecin et pharmacien ont reçu
    acc_pat = settlement.get_account('PAT-ABIDJAN')
    acc_med = settlement.get_account('MED-PARIS')
    acc_phm = settlement.get_account('PHM-ABIDJAN')
    # Patient avait 200, a payé 50 + 35 = 85 → solde 115
    assert acc_pat is not None
    assert acc_pat['balance_um'] == 115.0
    # Médecin a reçu 50, a converti 50 → balance 0, frozen 0 (consommé au règlement)
    assert acc_med['balance_um'] == 0.0
    assert acc_med['frozen_um'] == 0.0
    # Pharmacien a reçu 35
    assert acc_phm['balance_um'] == 35.0

    # Le rapprochement doit être équilibré
    from datetime import date
    today = date.today().isoformat()
    rec = settlement.reconcile(today)
    assert rec['balanced'] is True


def test_diaspora_scenario(client):
    """Scénario aide diaspora New York → Bamako."""
    summary = run_scenario("aide_diaspora", deterministic=True)
    assert summary['scenario_key'] == "aide_diaspora"
    assert summary['success'] == 10  # 10 étapes, toutes réussies
    # Vérifier que les conversions ont réussi
    acc_med = settlement.get_account('MED-BAMAKO')
    acc_phm = settlement.get_account('PHM-BAMAKO')
    # Les UM converties sont consommées (frozen=0, balance=0)
    assert acc_med['balance_um'] == 0.0
    assert acc_med['frozen_um'] == 0.0
    assert acc_phm['balance_um'] == 0.0
    assert acc_phm['frozen_um'] == 0.0
    # Patient a reçu 150, payé 40 + 25 = 65 → solde 85
    assert settlement.get_account('PAT-BAMAKO')['balance_um'] == 85.0


def test_urgence_scenario(client):
    """Scénario réseau de soins urgents — 7 agents."""
    summary = run_scenario("reseau_soins_urgents", deterministic=True)
    assert summary['scenario_key'] == "reseau_soins_urgents"
    assert summary['agents'] == 7
    assert summary['success'] == 19  # 19 étapes, toutes réussies
    assert summary['fail'] == 0


def test_custom_scenario(client):
    """Scénario personnalisé avec agents et étapes définis."""
    agents = [
        {"wallet_id": "PAT-CUST", "role": "patient", "name": "Patient Test",
         "location": "Abidjan", "latency_min_ms": 10, "latency_max_ms": 50,
         "reliability": 1.0},
        {"wallet_id": "MED-CUST", "role": "medecin", "name": "Dr. Test",
         "location": "Paris", "latency_min_ms": 10, "latency_max_ms": 50,
         "reliability": 1.0, "bank_account": "BANK_CUST"},
    ]
    steps = [
        {"action": "create_account", "wallet_id": "PAT-CUST"},
        {"action": "create_account", "wallet_id": "MED-CUST"},
        {"action": "credit", "wallet_id": "PAT-CUST", "amount_um": 100},
        {"action": "debit", "wallet_id": "PAT-CUST", "target": "MED-CUST",
         "amount_um": 30, "description": "Consultation"},
        {"action": "conversion", "wallet_id": "MED-CUST", "amount_um": 30},
    ]
    summary = run_custom_scenario("Test", "Test personnalisé", agents, steps)
    assert summary['success'] == 5
    assert summary['fail'] == 0
    assert settlement.get_account('PAT-CUST')['balance_um'] == 70
    assert settlement.get_account('MED-CUST')['balance_um'] == 0


def test_custom_scenario_via_api(client):
    """Scénario personnalisé via l'API."""
    body = {
        "name": "API Test",
        "description": "Test via API",
        "agents": [
            {"wallet_id": "PAT-API", "role": "patient", "name": "Patient API",
             "location": "Dakar", "latency_min_ms": 10, "latency_max_ms": 30,
             "reliability": 1.0},
        ],
        "steps": [
            {"action": "create_account", "wallet_id": "PAT-API"},
            {"action": "credit", "wallet_id": "PAT-API", "amount_um": 50},
        ],
    }
    r = client.post('/api/banking/simulate', json=body, headers=_auth())
    assert r.status_code == 200
    data = r.get_json()
    assert data['success'] is True
    assert data['summary']['success'] == 2
    assert settlement.get_account('PAT-API')['balance_um'] == 50


def test_engine_agent_reliability():
    """Un agent avec fiabilité 0 échoue toujours."""
    engine = SimulationEngine()
    agent = SimAgent("TEST-0", "patient", "Test", "Test", 10, 20, 0.0)
    engine.agents = {agent.wallet_id: agent}
    # Tentative de crédit sur un compte inexistant → doit échouer
    # (car l'agent n'est pas enregistré sur le serveur)
    with pytest.raises(Exception):
        agent.simulate_reliability()  # 0% de chance de succès
    # En fait, 0.0 reliability = toujours raise TimeoutError
    with pytest.raises(TimeoutError):
        agent.simulate_reliability()


def test_engine_offline_agent():
    """Un agent hors-ligne ne peut pas communiquer."""
    engine = SimulationEngine()
    agent = SimAgent("TEST-OFF", "patient", "Test", "Test", 10, 20, 1.0)
    agent.online = False
    with pytest.raises(ConnectionError, match="hors-ligne"):
        agent.simulate_latency()


def test_results_persistence():
    """Les résultats de simulation sont persistés."""
    # Reset
    import ka_server.services.simulation as _sim
    _sim._engine = None
    # Lancer une simulation
    run_scenario("consultation_transfrontaliere")
    results = list_results()
    assert len(results) >= 1
    assert results[-1]['scenario_key'] == "consultation_transfrontaliere"


def test_engine_status_api(client):
    """L'API de statut retourne l'état de la simulation."""
    r = client.get('/api/banking/simulate/status')
    # Statut public (pas d'auth requise pour le polling)
    assert r.status_code == 200
    data = r.get_json()
    assert 'running' in data
    assert 'summary' in data


def test_simulation_summary_format():
    """Le format du résumé de simulation est cohérent."""
    engine = SimulationEngine()
    summary = engine.summary()
    assert isinstance(summary, dict)
    assert 'scenario' in summary
    assert 'agents' in summary
    assert 'events' in summary
    assert 'success' in summary
    assert 'fail' in summary
    assert 'running' in summary


# ══════════════════════════════════════════════════════════════════════════════
#  Tests de l'intégration Sonic ID (empreinte sonore pseudo-aléatoire)
# ══════════════════════════════════════════════════════════════════════════════

def test_sonic_emit_credit_event(client):
    """Un événement de crédit génère une empreinte sonore unique."""
    summary = run_scenario("consultation_transfrontaliere", deterministic=True)
    engine = get_engine()
    sim_data = engine.to_dict()

    # Vérifier que les événements de crédit ont un sonic_id
    credit_events = [e for e in sim_data["events"] if e["action"] == "credit"]
    assert len(credit_events) > 0
    for ev in credit_events:
        assert ev["sonic_id"] is not None, f"Crédit sans sonic_id : {ev}"
        assert ev["sonic_id"].startswith("/api/sonic-id/")
        assert ev["sonic_variant"] in ("mobile", "care", "default")
        assert ev["tx_id"] is not None
        # Le tx_id est encodé dans l'URL
        assert ev["tx_id"] in ev["sonic_id"]


def test_sonic_emit_debit_event(client):
    """Un événement de débit (paiement) génère une empreinte sonore."""
    summary = run_scenario("consultation_transfrontaliere", deterministic=True)
    engine = get_engine()
    sim_data = engine.to_dict()

    debit_events = [e for e in sim_data["events"] if e["action"] == "debit"]
    assert len(debit_events) > 0
    for ev in debit_events:
        assert ev["sonic_id"] is not None, f"Débit sans sonic_id : {ev}"
        assert ev["tx_id"] is not None
        assert ev["tx_id"] in ev["sonic_id"]


def test_sonic_emit_conversion_event(client):
    """Un événement de conversion génère une empreinte sonore."""
    summary = run_scenario("consultation_transfrontaliere", deterministic=True)
    engine = get_engine()
    sim_data = engine.to_dict()

    conv_events = [e for e in sim_data["events"] if e["action"] == "conversion"]
    assert len(conv_events) > 0
    for ev in conv_events:
        assert ev["sonic_id"] is not None, f"Conversion sans sonic_id : {ev}"
        assert ev["tx_id"] is not None
        # Le sonic_id contient le conv_id dans l'URL
        assert ev["tx_id"] in ev["sonic_id"]


def test_sonic_deterministic(client):
    """Le même tx_id produit toujours la même empreinte sonore (déterministe)."""
    # L'API Sonic ID est déterministe : sonic_id_wav(tx_id, variant) retourne
    # toujours les mêmes bytes pour le même identifiant.
    # Ce test vérifie que deux appels HTTP avec le même tx_id retournent le même WAV.
    summary = run_scenario("consultation_transfrontaliere", deterministic=True)
    engine = get_engine()
    sim_data = engine.to_dict()
    sonic_events = [e for e in sim_data["events"] if e["sonic_id"]]
    assert len(sonic_events) > 0

    # Prendre le premier événement, appeler l'API deux fois
    ev = sonic_events[0]
    r1 = client.get(ev["sonic_id"], headers=_auth())
    r2 = client.get(ev["sonic_id"], headers=_auth())
    assert r1.status_code == 200
    assert r2.status_code == 200
    # Les deux WAV doivent être identiques byte-à-byte
    assert r1.data == r2.data, "Le même sonic_id doit produire le même WAV"

    # Vérifier avec un autre tx_id que les sons sont différents
    if len(sonic_events) > 1:
        ev2 = sonic_events[1]
        r3 = client.get(ev2["sonic_id"], headers=_auth())
        # Les deux WAV doivent être différents (tx_id différents)
        assert r1.data != r3.data, "Deux tx_id différents doivent produire des WAV différents"


def test_sonic_variant_by_role():
    """Le variant sonore dépend du rôle de l'agent."""
    from ka_server.services.simulation import ROLE_SONIC_VARIANT

    assert ROLE_SONIC_VARIANT["patient"] == "mobile"
    assert ROLE_SONIC_VARIANT["medecin"] == "care"
    assert ROLE_SONIC_VARIANT["pharmacie"] == "mobile"
    assert ROLE_SONIC_VARIANT["labo"] == "care"
    assert ROLE_SONIC_VARIANT["solidarite"] == "default"


def test_sonic_wav_generated(client):
    """L'API Sonic ID retourne un WAV valide pour un tx_id de simulation."""
    summary = run_scenario("consultation_transfrontaliere", deterministic=True)
    engine = get_engine()
    sim_data = engine.to_dict()

    # Prendre le premier événement avec sonic_id
    sonic_events = [e for e in sim_data["events"] if e["sonic_id"]]
    if not sonic_events:
        return

    ev = sonic_events[0]
    # Appeler l'API Sonic ID avec le tx_id
    r = client.get(ev["sonic_id"], headers=_auth())
    assert r.status_code == 200
    assert r.content_type == "audio/wav"
    assert len(r.data) > 100  # WAV non vide
    assert r.data[:4] == b"RIFF"  # Entête WAV valide
    assert r.headers.get("X-Sonic-Duration") is not None
    assert r.headers.get("X-Sonic-Variant") is not None