"""
core.keys — clés API et quotas journaliers (service SaaS)
=========================================================
Plans : free 100 req/j · pro 5 000 req/j · enterprise 50 000 req/j.
Persistance : data/saas_wave/keys.json + usage.json (JSON, thread-safe).
"""

import json
import secrets
import threading
import time
from datetime import date
from pathlib import Path

from fastapi import Header, HTTPException

from .engine import data_dir

PLANS = {
    'free':       {'daily_limit': 100,    'label': 'Découverte'},
    'pro':        {'daily_limit': 5_000,  'label': 'Professionnel'},
    'enterprise': {'daily_limit': 50_000, 'label': 'Entreprise'},
}

_fs_lock = threading.Lock()


def _keys_path() -> Path:
    return data_dir() / 'keys.json'


def _usage_path() -> Path:
    return data_dir() / 'usage.json'

def _load_json(path: Path, default):
    with _fs_lock:
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            return default


def _save_json(path: Path, data):
    with _fs_lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def create_key(email: str, plan: str = 'free', daily_limit: int | None = None) -> str:
    """Crée une clé API. Retourne la clé existante si l'email est déjà enregistré."""
    if plan not in PLANS:
        raise ValueError(f"plan inconnu: {plan} — {list(PLANS)}")
    keys = _load_json(_keys_path(), {})
    if email in keys:
        return keys[email]['key']
    key = 'hwu_' + secrets.token_hex(16)
    keys[email] = {
        'key': key, 'plan': plan,
        'daily_limit': daily_limit or PLANS[plan]['daily_limit'],
        'created': time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    _save_json(_keys_path(), keys)
    return key


def _consume(key: str) -> dict:
    """Consomme 1 requête du quota. Retourne {'ok': True, ...} ou lève 401/429."""
    keys = _load_json(_keys_path(), {})
    email = next((e for e, k in keys.items() if k['key'] == key), None)
    if email is None:
        raise HTTPException(status_code=401, detail={
            'error': 'Clé API invalide', 'code': 'INVALID_API_KEY'})
    info = keys[email]
    today = date.today().isoformat()
    usage = _load_json(_usage_path(), {})
    used = usage.get(key, {}).get(today, 0)
    limit = info['daily_limit']
    if used >= limit:
        raise HTTPException(status_code=429, detail={
            'error': 'Quota journalier atteint', 'code': 'QUOTA_EXCEEDED',
            'used': used, 'limit': limit, 'reset': today})
    usage.setdefault(key, {})[today] = used + 1
    _save_json(_usage_path(), usage)
    return {'used': used + 1, 'limit': limit, 'plan': info['plan'], 'email': email}


async def require_key(x_api_key: str = Header(default='')) -> dict:
    """Dependency FastAPI : vérifie la clé et consomme le quota."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail={
            'error': 'Clé API requise (X-API-Key)', 'code': 'NO_API_KEY'})
    return _consume(x_api_key)
