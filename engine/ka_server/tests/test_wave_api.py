# -*- coding: utf-8 -*-
"""Tests du service SaaS de calcul harmonique (/api/wave/*).

Lancement : python -m pytest ka_server/tests/test_wave_api.py -q  (depuis engine/)
"""
import os
import sys
import tempfile

import pytest

from ka_server.app import create_app

# Répertoire de persistance isolé pour les tests
_TMP = tempfile.mkdtemp(prefix='ka_wave_test_')
os.environ['KA_SAAS_WAVE_DIR'] = _TMP

from ka_server.routes.wave import create_key  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return create_app()


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


@pytest.fixture(scope="module")
def demo_key():
    """Clé plan free (100 req/j) pour les tests fonctionnels."""
    return create_key('demo@test.local', plan='free')


@pytest.fixture(scope="module")
def tiny_key():
    """Clé à quota minuscule pour le test 429."""
    return create_key('tiny@test.local', plan='free', daily_limit=2)


def _h(key):
    return {'X-API-Key': key, 'Content-Type': 'application/json'}


# ═══ PUBLIC ═════════════════════════════════════════════════════════════════

def test_status_is_public(client):
    r = client.get('/api/wave/status')
    assert r.status_code == 200
    body = r.get_json()
    assert body['status'] == 'ok'
    assert body['space'] == 'ℂ⁵¹² (limite de Bekenstein)'
    assert len(body['primitives']) == 13
    assert 'honesty' in body  # l'honnêteté fait partie de l'API


def test_playground_page_served(client):
    r = client.get('/wave')
    assert r.status_code == 200
    assert b'Harmonic Compute' in r.data


# ═══ AUTH & QUOTA ═══════════════════════════════════════════════════════════

def test_requires_api_key(client):
    r = client.post('/api/wave/encode', json={'entity': 'lumiere'})
    assert r.status_code == 401
    assert r.get_json()['code'] == 'NO_API_KEY'


def test_invalid_api_key(client):
    r = client.post('/api/wave/encode', json={'entity': 'lumiere'},
                    headers=_h('hwu_invalide'))
    assert r.status_code == 401
    assert r.get_json()['code'] == 'INVALID_API_KEY'


def test_quota_exceeded_returns_429(client, tiny_key):
    for _ in range(2):  # quota = 2
        r = client.post('/api/wave/encode', json={'entity': 'x'},
                        headers=_h(tiny_key))
        assert r.status_code == 200
    r = client.post('/api/wave/encode', json={'entity': 'x'}, headers=_h(tiny_key))
    assert r.status_code == 429
    assert r.get_json()['code'] == 'QUOTA_EXCEEDED'


# ═══ LES PRIMITIVES ═════════════════════════════════════════════════════════

def test_encode_norm_one(client, demo_key):
    r = client.post('/api/wave/encode', json={'entity': 'lumiere'}, headers=_h(demo_key))
    assert r.status_code == 200
    body = r.get_json()
    assert body['wave']['dim'] == 512
    assert abs(body['wave']['norm'] - 1.0) < 1e-6  # ‖encode(x)‖ = 1


def test_resonate_identity_is_one(client, demo_key):
    r = client.post('/api/wave/resonate', json={'a': 'chat', 'b': 'chat'},
                    headers=_h(demo_key))
    assert r.status_code == 200
    assert abs(r.get_json()['resonance'] - 1.0) < 1e-6


def test_bind_unbind_recovery(client, demo_key):
    """Valeur de référence : unbind(bind(a,b), b) → récupération ≥ 0,7."""
    r_bind = client.post('/api/wave/bind', json={'a': 'alpha', 'b': 'beta'},
                         headers=_h(demo_key))
    c = r_bind.get_json()['wave']
    r_unbind = client.post('/api/wave/unbind', json={'c': c, 'b': 'beta'},
                           headers=_h(demo_key))
    r_rec = client.post('/api/wave/resonate',
                        json={'a': 'alpha', 'b': r_unbind.get_json()['wave']},
                        headers=_h(demo_key))
    assert r_rec.status_code == 200
    assert r_rec.get_json()['resonance'] >= 0.7


def test_superpose_norm_one(client, demo_key):
    r = client.post('/api/wave/superpose',
                    json={'items': ['chat', 'chien', 'oiseau']}, headers=_h(demo_key))
    assert r.status_code == 200
    assert abs(r.get_json()['summary']['norm'] - 1.0) < 1e-6


def test_rotate_pi_antiresonates(client, demo_key):
    r = client.post('/api/wave/rotate', json={'a': 'chat', 'angle': 3.141592653589793},
                    headers=_h(demo_key))
    w = r.get_json()['wave']
    r2 = client.post('/api/wave/resonate', json={'a': w, 'b': 'chat'}, headers=_h(demo_key))
    assert abs(r2.get_json()['resonance'] + 1.0) < 1e-4  # rotate(ψ, π) → −1


def test_filter_lowpass_keeps_norm(client, demo_key):
    r = client.post('/api/wave/filter',
                    json={'a': 'signal complexe', 'mode': 'lowpass', 'cutoff': 0.5},
                    headers=_h(demo_key))
    assert r.status_code == 200
    assert abs(r.get_json()['summary']['norm'] - 1.0) < 1e-6


# ═══ MÉMOIRE HOLOGRAPHIQUE ══════════════════════════════════════════════════

def test_memory_store_and_query(client, demo_key):
    facts = [['lumiere', 'est une', 'onde electromagnetique'],
             ['chat', 'aime', 'poisson']]
    r = client.post('/api/wave/memory/store', json={'facts': facts}, headers=_h(demo_key))
    assert r.status_code == 200
    assert r.get_json()['stored'] == 2

    r = client.post('/api/wave/memory/query',
                    json={'query': 'Qu\'est-ce que la lumiere ?', 'top_k': 2},
                    headers=_h(demo_key))
    assert r.status_code == 200
    results = r.get_json()['results']
    assert len(results) >= 1
    assert results[0]['resonance'] > 0  # la mémoire répond


# ═══ ARITHMÉTIQUE ÉMERGENTE ═════════════════════════════════════════════════

def test_solve_arithmetic(client, demo_key):
    """Le moteur résout les opérations simples (les chaînes mixtes sont une frontière)."""
    r = client.post('/api/wave/solve', json={'expression': '12 * 7'},
                    headers=_h(demo_key))
    assert r.status_code == 200
    assert r.get_json()['result'] == 84


# ═══ BENCHMARK EN DIRECT ════════════════════════════════════════════════════

def test_benchmark_all_pass(client, demo_key):
    r = client.get('/api/wave/benchmark', headers=_h(demo_key))
    assert r.status_code == 200
    body = r.get_json()
    for name, res in body['results'].items():
        assert res['pass'] is True, f"{name} a échoué : {res}"
