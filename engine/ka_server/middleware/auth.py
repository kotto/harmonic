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
    
    # Amorcer les clés depuis l'environnement / fichier local (sinon set vide
    # → aucun endpoint protégé ne serait accessible). Sources :
    #   1. variable d'env KA_API_KEYS (clés séparées par des virgules)
    #   2. fichier ka_api_keys.json {"keys": ["..."]} à côté du serveur
    _seed_api_keys()
    _load_users()
    
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


def _seed_api_keys():
    """Charge les clés API au démarrage (env KA_API_KEYS + fichier ka_api_keys.json)."""
    import json
    from pathlib import Path

    env_keys = os.environ.get('KA_API_KEYS', '')
    for k in [k.strip() for k in env_keys.split(',') if k.strip()]:
        add_api_key(k, {'user_id': 'env'})

    keys_file = Path(__file__).resolve().parent.parent / 'ka_api_keys.json'
    if keys_file.exists():
        try:
            with open(keys_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for k in data.get('keys', []):
                add_api_key(str(k).strip(), {'user_id': 'file'})
        except Exception as e:
            log.error(f"Erreur lecture ka_api_keys.json : {e}")

    if _VALID_API_KEYS:
        log.info(f"  🔑 {len(_VALID_API_KEYS)} clé(s) API chargée(s) (env/fichier)")


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


# ── Gestion des utilisateurs Enterprise ──────────────────────────────────────
# Registre : username → {role: admin|viewer|auditor, created_at, keys: [masquées]}
_USERS: dict = {}
_USERS_FILE = None


def _users_file_path():
    global _USERS_FILE
    if _USERS_FILE is None:
        from pathlib import Path
        _USERS_FILE = Path(__file__).resolve().parent.parent / 'ka_enterprise_users.json'
    return _USERS_FILE


def _load_users():
    """Charge le registre utilisateurs au démarrage."""
    import json
    p = _users_file_path()
    if p.exists():
        try:
            with open(p, 'r', encoding='utf-8') as f:
                _USERS.update(json.load(f))
            log.info(f"  👤 {len(_USERS)} utilisateur(s) Enterprise chargé(s)")
        except Exception as e:
            log.error(f"Erreur lecture utilisateurs : {e}")


def _save_users():
    import json
    try:
        with open(_users_file_path(), 'w', encoding='utf-8') as f:
            json.dump(_USERS, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.error(f"Erreur écriture utilisateurs : {e}")


def list_users() -> list:
    """Liste les utilisateurs (rôle, date de création, clés liées)."""
    import time as _t
    out = []
    for username, info in _USERS.items():
        out.append({
            'username': username,
            'role': info.get('role', 'viewer'),
            'created_at': info.get('created_at'),
            'age_days': round((_t.time() - info.get('created_at', _t.time())) / 86400, 1),
            'keys': info.get('keys', []),
        })
    return out


def create_user(username: str, role: str = 'viewer') -> tuple:
    """Crée un utilisateur. Retourne (ok, message)."""
    import time as _t
    username = (username or '').strip().lower()
    if not username or len(username) < 2:
        return False, 'Nom d\'utilisateur invalide (min 2 caractères)'
    if role not in ('admin', 'viewer', 'auditor'):
        return False, 'Rôle invalide (admin, viewer, auditor)'
    if username in _USERS:
        return False, 'Utilisateur déjà existant'
    _USERS[username] = {'role': role, 'created_at': _t.time(), 'keys': []}
    _save_users()
    _audit("USER_CREATED", 'system', username)
    return True, f'Utilisateur « {username} » créé (rôle {role})'


def delete_user(username: str) -> tuple:
    """Supprime un utilisateur. Retourne (ok, message)."""
    username = (username or '').strip().lower()
    if username not in _USERS:
        return False, 'Utilisateur non trouvé'
    del _USERS[username]
    _save_users()
    _audit("USER_DELETED", 'system', username)
    return True, f'Utilisateur « {username} » supprimé'


def set_user_role(username: str, role: str) -> tuple:
    """Change le rôle d'un utilisateur. Retourne (ok, message)."""
    username = (username or '').strip().lower()
    if username not in _USERS:
        return False, 'Utilisateur non trouvé'
    if role not in ('admin', 'viewer', 'auditor'):
        return False, 'Rôle invalide'
    _USERS[username]['role'] = role
    _save_users()
    _audit("USER_ROLE_CHANGED", 'system', f'{username}→{role}')
    return True, f'Rôle de « {username} » → {role}'


def _link_key_to_user(key: str, username: str):
    """Attribue une clé à un utilisateur (au moment de la création de la clé)."""
    username = (username or '').strip().lower()
    if username in _USERS and key:
        mask = f"{key[:8]}...{key[-4:]}"
        if mask not in _USERS[username]['keys']:
            _USERS[username]['keys'].append(mask)
            _save_users()


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