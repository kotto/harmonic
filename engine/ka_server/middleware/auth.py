"""
KA Server — Middleware Auth & Sécurité
=======================================
Authentification, API keys, audit log, chiffrement.
"""

import os
import logging
from functools import wraps
from flask import request, jsonify, g

log = logging.getLogger(__name__)

# Clés API valides (en mémoire, persistées via Enterprise)
_VALID_API_KEYS = set()
_AUDIT_LOG = []
_MAX_AUDIT_LOG = 1000


def register_auth_middleware(app):
    """Enregistre les middleware d'authentification."""
    
    @app.before_request
    def _auth_check():
        g.authenticated = False
        g.user_id = 'anonymous'
        g.api_key_used = None
        
        # Vérifier API Key (Enterprise)
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key in _VALID_API_KEYS:
            g.authenticated = True
            g.user_id = f'api_{api_key[:8]}'
            g.api_key_used = api_key
            _audit(f"API_KEY_AUTH", g.user_id, request.path)
            return
        
        # Vérifier Authorization Bearer token
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            if token in _VALID_API_KEYS:
                g.authenticated = True
                g.user_id = f'bearer_{token[:8]}'
                g.api_key_used = token
                _audit(f"BEARER_AUTH", g.user_id, request.path)
                return
        
        # Pour les endpoints publics, continuer sans auth
        # Les endpoints protégés vérifieront avec @require_auth
    
    # Exposer fonctions utilitaires
    app.ka_auth = {
        'add_api_key': add_api_key,
        'remove_api_key': remove_api_key,
        'validate_api_key': validate_api_key,
        'get_audit_log': get_audit_log,
    }


def require_auth(f):
    """Décorateur pour exiger authentification sur un endpoint."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not g.get('authenticated', False):
            return jsonify({
                'error': 'Authentification requise',
                'code': 'AUTH_REQUIRED'
            }), 401
        return f(*args, **kwargs)
    return decorated


def require_api_key(f):
    """Décorateur pour exiger API key valide."""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
        if not api_key or not validate_api_key(api_key):
            return jsonify({
                'error': 'Clé API invalide ou manquante',
                'code': 'INVALID_API_KEY'
            }), 401
        return f(*args, **kwargs)
    return decorated


def add_api_key(key: str, metadata: dict = None) -> bool:
    """Ajoute une clé API valide."""
    if key and len(key) >= 16:
        _VALID_API_KEYS.add(key)
        _audit("API_KEY_ADDED", metadata.get('user_id') if metadata else 'system', key[:8])
        return True
    return False


def remove_api_key(key: str) -> bool:
    """Révoque une clé API."""
    if key in _VALID_API_KEYS:
        _VALID_API_KEYS.remove(key)
        _audit("API_KEY_REVOKED", 'system', key[:8])
        return True
    return False


def validate_api_key(key: str) -> bool:
    """Valide une clé API."""
    return key in _VALID_API_KEYS


def get_valid_keys() -> list:
    """Retourne la liste des clés valides (masquées)."""
    return [f"{k[:8]}...{k[-4:]}" for k in _VALID_API_KEYS]


def _audit(action: str, user: str, resource: str):
    """Enregistre un événement d'audit."""
    import time
    _AUDIT_LOG.append({
        'timestamp': time.time(),
        'action': action,
        'user': user,
        'resource': resource,
        'ip': request.headers.get('X-Forwarded-For', request.remote_addr) if request else 'system'
    })
    if len(_AUDIT_LOG) > _MAX_AUDIT_LOG:
        _AUDIT_LOG[:] = _AUDIT_LOG[-_MAX_AUDIT_LOG:]


def get_audit_log(limit: int = 100) -> list:
    """Retourne les derniers événements d'audit."""
    return _AUDIT_LOG[-limit:]


# ── Chiffrement données (AES-GCM) ────────────────────────────────────────────
def encrypt_data(data: bytes, key: bytes) -> dict:
    """Chiffre des données avec AES-GCM."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        import os
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        return {
            'ciphertext': ciphertext.hex(),
            'nonce': nonce.hex(),
            'algorithm': 'AES-GCM-256'
        }
    except ImportError:
        log.warning("cryptography non installé — chiffrement désactivé")
        return None
    except Exception as e:
        log.error(f"Erreur chiffrement: {e}")
        return None


def decrypt_data(encrypted: dict, key: bytes) -> bytes:
    """Déchiffre des données AES-GCM."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aesgcm = AESGCM(key)
        nonce = bytes.fromhex(encrypted['nonce'])
        ciphertext = bytes.fromhex(encrypted['ciphertext'])
        return aesgcm.decrypt(nonce, ciphertext, None)
    except Exception as e:
        log.error(f"Erreur déchiffrement: {e}")
        return None