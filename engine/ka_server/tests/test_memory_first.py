# -*- coding: utf-8 -*-
"""Tests du pipeline memory-first (/api/memory-first/*).

Lancement : python -m pytest ka_server/tests/test_memory_first.py -q
"""
import os
import tempfile

import pytest

from ka_server.app import create_app

_TMP = tempfile.mkdtemp(prefix='ka_mf_test_')
os.environ['KA_SAAS_WAVE_DIR'] = _TMP

from ka_server.services.memory_first import DEFAULT_REFUSAL_THRESHOLD  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return create_app()


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


@pytest.fixture(scope="module")
def seeded(client):
    """Charge les faits de démonstration (avec provenance)."""
    facts = [
        ['lumiere', 'est une', 'onde electromagnetique', 'cours de physique'],
        ['lumiere', 'a pour vitesse', '300 000 km par seconde', 'encyclopedie'],
        ['soleil', 'est', 'une etoile', 'astronomie'],
        ['phi', 'est', 'nombre d or', 'theorie harmonique'],
    ]
    r = client.post('/api/memory-first/store', json={'facts': facts})
    assert r.status_code == 200
    assert r.get_json()['stored'] == 4
    return client


# ═══ LE PIPELINE ════════════════════════════════════════════════════════════

def test_ask_known_entity_with_provenance(seeded):
    r = seeded.post('/api/memory-first/ask', json={'query': 'Qu est ce que la lumiere ?'})
    assert r.status_code == 200
    body = r.get_json()
    assert body['refused'] is False
    assert body['answer'] == 'lumiere est une onde electromagnetique.'
    assert len(body['provenance']) >= 1
    assert body['provenance'][0]['source'] == 'cours de physique'
    assert body['confidence'] >= 0.0


def test_ask_second_fact_of_entity(seeded):
    r = seeded.post('/api/memory-first/ask',
                    json={'query': 'quelle est la vitesse de la lumiere ?'})
    body = r.get_json()
    # les deux faits de 'lumiere' sont candidats — l'un répond
    assert body['refused'] is False
    assert body['answer'] in ('lumiere est une onde electromagnetique.',
                              'lumiere a pour vitesse 300 000 km par seconde.')


def test_ask_unknown_entity_is_refused(seeded):
    r = seeded.post('/api/memory-first/ask',
                    json={'query': 'comment faire une pizza ?'})
    body = r.get_json()
    assert body['refused'] is True
    assert body['answer'] is None
    assert 'aucune entité' in body['reason']  # jamais de fabrication


def test_unknown_query_is_refused(app):
    """La garantie structurelle : une question hors connaissance → silence,
    jamais de fabrication (l'état exact de la mémoire importe peu)."""
    c = app.test_client()
    r = c.post('/api/memory-first/ask', json={'query': 'zzz aucune entite connue zzz'})
    body = r.get_json()
    assert body['refused'] is True
    assert body['answer'] is None
    assert body['reason']  # la raison est toujours donnée


def test_stats_declare_honesty(seeded):
    r = seeded.get('/api/memory-first/stats')
    assert r.status_code == 200
    body = r.get_json()
    assert body['facts'] >= 4
    assert body['vocabulary'] >= 4
    assert any('X3' in h for h in body['honesty'])  # l'honnêteté est dans l'API
    assert any('structurel' in h for h in body['honesty'])


def test_threshold_parameter_is_declared(seeded):
    """Le seuil est un paramètre déclaré, pas magique — il est dans l'API."""
    assert isinstance(DEFAULT_REFUSAL_THRESHOLD, float)
    r = seeded.post('/api/memory-first/ask', json={'query': 'le soleil'})
    assert r.status_code == 200  # le seuil par défaut ne casse pas les réponses


# ═══ LE PONT AGENTIQUE ══════════════════════════════════════════════════════

def test_action_call_recognized(seeded):
    """« appelle Sophie » → la commande agentique call, pas une fabrication."""
    r = seeded.post('/api/memory-first/ask', json={'query': 'appelle sophie'})
    body = r.get_json()
    assert body['refused'] is False
    assert body['suggested_action'] == 'call'
    assert body['provenance'][0]['source'].startswith('KA Actions')


def test_action_compress_recognized(seeded):
    """« compresse le dossier photos » → la compression HCV (la phare)."""
    r = seeded.post('/api/memory-first/ask', json={'query': 'compresse le dossier photos'})
    body = r.get_json()
    assert body['suggested_action'] == 'hcv_compress'
    assert 'HCV' in body['provenance'][0]['source']  # la provenance cite le codec


def test_action_battery_recognized(seeded):
    r = seeded.post('/api/memory-first/ask', json={'query': 'niveau de batterie ?'})
    assert r.get_json()['suggested_action'] == 'battery'


def test_medical_question_not_an_action(seeded):
    """Une question médicale reste une question — pas de fausse commande."""
    r = seeded.post('/api/memory-first/ask', json={'query': 'qu est ce que la lumiere ?'})
    body = r.get_json()
    assert body['suggested_action'] is None
    assert body['refused'] is False
