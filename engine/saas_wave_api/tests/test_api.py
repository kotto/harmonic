# -*- coding: utf-8 -*-
"""Tests du service FastAPI de calcul harmonique — contre un VRAI serveur uvicorn.

Lancement : python -m pytest saas_wave_api/tests -q  (depuis engine/)
Le test démarre uvicorn sur un port libre, parle en HTTP réel (urllib),
et utilise le SDK WaveClient de bout en bout.
"""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

import pytest

_TMP = tempfile.mkdtemp(prefix='hwu_api_test_')
os.environ['KA_SAAS_WAVE_DIR'] = _TMP  # persistance isolée

_ENGINE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def server():
    """Démarre uvicorn (vrai serveur), attend la disponibilité, puis l'arrête."""
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'saas_wave_api.main:app',
         '--host', '127.0.0.1', '--port', str(port), '--log-level', 'warning'],
        cwd=_ENGINE_DIR,
        env={**os.environ, 'KA_SAAS_WAVE_DIR': _TMP},
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f'http://127.0.0.1:{port}'
    # Attendre la disponibilité (max 30 s)
    for _ in range(60):
        try:
            with urllib.request.urlopen(base + '/v1/meta/status', timeout=2) as r:
                if r.status == 200:
                    break
        except Exception:
            time.sleep(0.5)
    else:
        proc.kill()
        pytest.fail('Serveur uvicorn non disponible après 30 s')
    yield base
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except Exception:
        proc.kill()


# ── transport HTTP minimal (stdlib) ──────────────────────────────────────────

def _call(base, path, body=None, api_key=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data,
                                 method='POST' if body is not None else 'GET')
    req.add_header('Content-Type', 'application/json')
    if api_key:
        req.add_header('X-API-Key', api_key)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


@pytest.fixture(scope="module")
def demo_key(server):
    _, body = _call(server, '/v1/auth/register', {'email': 'demo@api.test'})
    return body['api_key']


# ═══ SURFACE ════════════════════════════════════════════════════════════════

def test_landing_playground(server):
    with urllib.request.urlopen(server + '/', timeout=10) as resp:
        assert resp.status == 200
        assert 'Harmonic Compute' in resp.read().decode()


def test_openapi_docs(server):
    status, spec = _call(server, '/openapi.json')
    assert status == 200
    assert '/v1/wave/encode' in spec['paths']
    assert '/v1/auth/register' in spec['paths']


def test_status_public(server):
    status, body = _call(server, '/v1/meta/status')
    assert status == 200
    assert body['status'] == 'ok'
    assert len(body['primitives']) == 13
    assert body['space'] == 'ℂ⁵¹² (limite de Bekenstein)'


# ═══ AUTH & QUOTA ═══════════════════════════════════════════════════════════

def test_register_creates_free_key(server):
    status, body = _call(server, '/v1/auth/register', {'email': 'nouveau@api.test'})
    assert status == 200
    assert body['api_key'].startswith('hwu_')
    assert body['plan'] == 'free'
    assert body['daily_limit'] == 100


def test_requires_api_key(server):
    status, body = _call(server, '/v1/wave/encode', {'entity': 'lumiere'})
    assert status == 401
    assert body['detail']['code'] == 'NO_API_KEY'


def test_quota_exceeded_returns_429(server):
    from saas_wave_api.core.keys import create_key
    tiny = create_key('tiny@api.test', plan='free', daily_limit=2)
    for _ in range(2):
        status, _ = _call(server, '/v1/wave/encode', {'entity': 'x'}, api_key=tiny)
        assert status == 200
    status, body = _call(server, '/v1/wave/encode', {'entity': 'x'}, api_key=tiny)
    assert status == 429
    assert body['detail']['code'] == 'QUOTA_EXCEEDED'


# ═══ PRIMITIVES ═════════════════════════════════════════════════════════════

def test_encode_norm_one(server, demo_key):
    status, body = _call(server, '/v1/wave/encode', {'entity': 'lumiere'}, demo_key)
    assert status == 200
    wave = body['wave']
    assert wave['dim'] == 512
    assert abs(wave['norm'] - 1.0) < 1e-6


def test_resonate_identity(server, demo_key):
    status, body = _call(server, '/v1/wave/resonate', {'a': 'chat', 'b': 'chat'}, demo_key)
    assert status == 200
    assert abs(body['resonance'] - 1.0) < 1e-6


def test_bind_unbind_recovery(server, demo_key):
    _, b1 = _call(server, '/v1/wave/bind', {'a': 'alpha', 'b': 'beta'}, demo_key)
    _, b2 = _call(server, '/v1/wave/unbind', {'c': b1['wave'], 'b': 'beta'}, demo_key)
    _, b3 = _call(server, '/v1/wave/resonate', {'a': 'alpha', 'b': b2['wave']}, demo_key)
    assert b3['resonance'] >= 0.7


def test_superpose_rotate_filter(server, demo_key):
    _, s = _call(server, '/v1/wave/superpose', {'items': ['a', 'b', 'c']}, demo_key)
    assert abs(s['summary']['norm'] - 1.0) < 1e-6
    _, r1 = _call(server, '/v1/wave/rotate',
                  {'a': 'chat', 'angle': 3.141592653589793}, demo_key)
    _, r2 = _call(server, '/v1/wave/resonate', {'a': r1['wave'], 'b': 'chat'}, demo_key)
    assert abs(r2['resonance'] + 1.0) < 1e-4
    _, f = _call(server, '/v1/wave/filter',
                 {'a': 'signal complexe', 'mode': 'lowpass', 'cutoff': 0.5}, demo_key)
    assert abs(f['summary']['norm'] - 1.0) < 1e-6


def test_memory_store_query(server, demo_key):
    _, s = _call(server, '/v1/memory/store',
                 {'facts': [['lumiere', 'est une', 'onde electromagnetique'],
                            ['chat', 'aime', 'poisson']]}, demo_key)
    assert s['stored'] == 2
    _, q = _call(server, '/v1/memory/query',
                 {'query': 'Qu\'est-ce que la lumiere ?', 'top_k': 2}, demo_key)
    assert q['results'][0]['resonance'] > 0


def test_solve_arithmetic(server, demo_key):
    status, body = _call(server, '/v1/wave/solve', {'expression': '12 * 7'}, demo_key)
    assert status == 200
    assert body['result'] == 84


def test_benchmark_all_pass(server, demo_key):
    status, body = _call(server, '/v1/meta/benchmark', api_key=demo_key)
    assert status == 200
    for name, res in body['results'].items():
        assert res['pass'] is True, f"{name} a échoué : {res}"


# ═══ SDK — bout en bout ══════════════════════════════════════════════════════

def test_sdk_end_to_end(server, demo_key):
    """Le SDK WaveClient parle au vrai serveur : la boucle complète du SaaS."""
    from saas_wave_api.sdk.wave_client import WaveClient

    client = WaveClient(base_url=server, api_key=demo_key)
    st = client.status()
    assert st['status'] == 'ok'

    e = client.encode('lumiere')
    assert abs(e['wave']['norm'] - 1.0) < 1e-6

    r = client.resonate('chat', 'chat')
    assert abs(r['resonance'] - 1.0) < 1e-6

    c = client.bind('alpha', 'beta')
    rec = client.unbind(c['wave'], 'beta')
    r2 = client.resonate('alpha', rec['wave'])
    assert r2['resonance'] >= 0.7

    client.memory_store([['soleil', 'est une', 'etoile']])
    q = client.memory_query('Qu\'est-ce que le soleil ?')
    assert q['results'][0]['resonance'] > 0

    s = client.solve('12 * 7')
    assert s['result'] == 84
