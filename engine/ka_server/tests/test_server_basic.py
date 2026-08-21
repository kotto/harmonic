# -*- coding: utf-8 -*-
"""Tests de base du KA Server modulaire (app factory, config produit, auth).

Lancement : python -m pytest ka_server/tests -q  (depuis engine/)
"""
import pytest

from ka_server.app import create_app


@pytest.fixture(scope="module")
def app():
    """Instance Flask partagée (build coûteux : services + faits)."""
    return create_app()


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


# ── App factory ──────────────────────────────────────────────────────────────

def test_app_builds_and_health_ok(client):
    """L'app se construit et /api/health répond healthy."""
    r = client.get('/api/health')
    assert r.status_code == 200
    body = r.get_json()
    assert body['status'] == 'healthy'
    assert body['service'] == 'ka-server'


def test_health_detailed_reports_services(client):
    r = client.get('/api/health/detailed')
    assert r.status_code == 200
    assert 'services' in r.get_json()


def test_index_route_returns_product(app, client):
    """La route racine expose la config produit active."""
    r = client.get('/')
    assert r.status_code == 200
    body = r.get_json()
    assert body['status'] == 'running'
    assert body['product'] == app.config['KA_CONFIG'].product


# ── Config produit branchée (régression fix) ────────────────────────────────

def test_ka_config_is_injected(app):
    """KA_CONFIG doit être injecté dans app.config (sinon 0 fait + config morte)."""
    cfg = app.config.get('KA_CONFIG')
    assert cfg is not None
    assert cfg.product in ('mobile', 'pc', 'enterprise')


def test_services_config_is_product_dict(app):
    """services['config'] doit être un dict produit (lue par rate limit, faits)."""
    config = app.ka_services['config']
    assert isinstance(config, dict)
    assert config.get('product') in ('mobile', 'pc', 'enterprise')
    assert config.get('name')


# ── Auth Enterprise (régression fix : validation réellement exécutée) ───────

def test_enterprise_auth_rejects_missing_key(client):
    r = client.post('/api/v2/enterprise/ingest', json={'documents': []})
    assert r.status_code == 401


def test_enterprise_auth_rejects_invalid_key(client):
    r = client.post(
        '/api/v2/enterprise/ingest',
        json={'documents': []},
        headers={'X-API-Key': 'cle-invalide'},
    )
    assert r.status_code == 401
    assert r.get_json()['code'] == 'INVALID_API_KEY'


def test_enterprise_auth_accepts_valid_key(app, client):
    """Une clé valide passe l'auth (validation exécutée via app.ka_auth)."""
    app.ka_auth['add_api_key']('test-valid-key-1234567890', {'user_id': 'test'})
    r = client.post(
        '/api/v2/enterprise/ingest',
        json={'documents': []},
        headers={'X-API-Key': 'test-valid-key-1234567890'},
    )
    assert r.status_code != 401  # atteint la logique métier (400 = docs manquants)


def test_auth_seed_from_env(monkeypatch, app):
    """Les clés sont amorcées depuis l'environnement au register (régression fix)."""
    from ka_server.middleware import auth as auth_module
    monkeypatch.setenv('KA_API_KEYS', 'env-key-one-1234567890, env-key-two-1234567890')
    auth_module._VALID_API_KEYS.clear()
    auth_module._seed_api_keys()
    assert 'env-key-one-1234567890' in auth_module._VALID_API_KEYS
    assert 'env-key-two-1234567890' in auth_module._VALID_API_KEYS
