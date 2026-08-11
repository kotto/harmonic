"""
KA Server — Routes Wave Compute (service SaaS de calcul harmonique)
===================================================================
Le service « quantum-like » : les 13 primitives du langage ondulatoire
exposées en HTTP — machine de Hilbert déterministe (ℂ⁵¹², ‖ψ‖ = 1).

  - /api/wave/status            → état du moteur (public)
  - /api/wave/encode            → monde → ψ
  - /api/wave/decode            → ψ → entité (plus proche voisin)
  - /api/wave/bind · unbind     → lier / délier (HRR)
  - /api/wave/superpose         → superposition (mémoire holographique)
  - /api/wave/resonate          → ⟨ψ|φ⟩ ∈ [−1, 1]
  - /api/wave/rotate · phase_shift · interfere · diffract · filter · emerge
  - /api/wave/memory/*          → mémoire holographique persistante
  - /api/wave/solve             → arithmétique émergente (résonance)
  - /api/wave/benchmark         → démos vérifiées en direct

Authentification : clé API (en-tête X-API-Key) + quota journalier par plan.
Plans : free 100 req/j · pro 5 000 req/j · enterprise 50 000 req/j.
"""

import json
import logging
import os
import secrets
import sys
import threading
import time
from datetime import date
from pathlib import Path

import numpy as np
from flask import request, jsonify

log = logging.getLogger(__name__)

# ── Moteur : le langage ondulatoire (vital-ka/core/python/wave_lang.py) ─────
_WAVE_DIR = Path(__file__).resolve().parent.parent.parent / 'vital-ka' / 'core' / 'python'
if str(_WAVE_DIR) not in sys.path:
    sys.path.insert(0, str(_WAVE_DIR))

from wave_lang import (  # noqa: E402
    HolographicMemory, bind, decode, diffract, emerge, encode, filter_wave,
    interfere, normalize, phase_shift, resonate, rotate, stats, superpose,
    unbind,
)

# ── Config des plans ─────────────────────────────────────────────────────────
PLANS = {
    'free':       {'daily_limit': 100,    'label': 'Découverte'},
    'pro':        {'daily_limit': 5_000,  'label': 'Professionnel'},
    'enterprise': {'daily_limit': 50_000, 'label': 'Entreprise'},
}
_DIM = 512  # ℂ⁵¹² — limite de Bekenstein

_mem_lock = threading.Lock()
_memory = None  # mémoire holographique (singleton process)
_fact_log = []  # triplets persistés [sujet, relation, objet]

_fs_lock = threading.Lock()


def _wave_dir() -> Path:
    """Répertoire de persistance (surchargeable par KA_SAAS_WAVE_DIR — tests).
    ATTENTION : Path('') = Path('.') — tester la chaîne AVANT de convertir."""
    raw = os.environ.get('KA_SAAS_WAVE_DIR', '')
    return Path(raw) if raw else Path(__file__).resolve().parent.parent.parent / 'data' / 'saas_wave'


def _keys_path() -> Path:
    return _wave_dir() / 'keys.json'


def _usage_path() -> Path:
    return _wave_dir() / 'usage.json'


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


def _get_memory() -> HolographicMemory:
    """Singleton mémoire holographique (persistée en JSON)."""
    global _memory, _fact_log
    with _mem_lock:
        if _memory is None:
            _memory = HolographicMemory(dim=_DIM)
            # Restaurer depuis la persistance
            path = _wave_dir() / 'memory.json'
            facts = _load_json(path, [])
            for f in facts:
                if len(f) == 3:
                    try:
                        _memory.store(encode(f[0], dim=_DIM), encode(f[1], dim=_DIM),
                                      encode(f[2], dim=_DIM))
                        _fact_log.append(list(f))
                    except Exception:
                        continue
        return _memory


def _persist_memory():
    """Sauvegarde les triplets de la mémoire (le ψ se re-encode de façon déterministe)."""
    path = _wave_dir() / 'memory.json'
    _save_json(path, _fact_log)


# ── Sérialisation des ondes ──────────────────────────────────────────────────

def _wave_to_json(psi) -> dict:
    """ψ → JSON : {dim, norm, energy, vec: [[re, im], ...]}."""
    psi = np.asarray(psi, dtype=np.complex128)
    return {
        'dim': int(psi.shape[0]),
        'norm': float(np.abs(psi).max() and np.linalg.norm(psi) or 0.0),
        'energy': float(np.sum(np.abs(psi) ** 2)),
        'vec': [[float(v.real), float(v.imag)] for v in psi],
    }


def _wave_from_json(data) -> np.ndarray:
    """JSON → ψ (depuis {"vec": [[re, im], ...]})."""
    vec = data['vec']
    return np.array([complex(a, b) for a, b in vec], dtype=np.complex128)


def _resolve(item):
    """Résout une entrée : str → encode ; dict {"vec": ...} → onde."""
    if isinstance(item, str):
        return encode(item, dim=_DIM)
    if isinstance(item, dict) and 'vec' in item:
        return _wave_from_json(item)
    raise ValueError("entrée invalide — attendu un texte (encodé) ou un ψ sérialisé")


def _summary(psi) -> dict:
    """Résumé léger d'une onde (sans le vecteur complet)."""
    psi = np.asarray(psi, dtype=np.complex128)
    return {
        'dim': int(psi.shape[0]),
        'norm': float(np.linalg.norm(psi)),
        'energy': float(np.sum(np.abs(psi) ** 2)),
    }


# ── Clés API et quotas ───────────────────────────────────────────────────────

def create_key(email: str, plan: str = 'free', daily_limit: int = None) -> str:
    """Crée une clé API (utilisé par le CLI et les tests)."""
    if plan not in PLANS:
        raise ValueError(f"plan inconnu: {plan} — {list(PLANS)}")
    key = 'hwu_' + secrets.token_hex(16)
    keys = _load_json(_keys_path(), {})
    keys[email] = {
        'key': key,
        'plan': plan,
        'daily_limit': daily_limit or PLANS[plan]['daily_limit'],
        'created': time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    _save_json(_keys_path(), keys)
    return key


def _check_quota(key: str) -> tuple:
    """Vérifie le quota journalier. Retourne (ok, info)."""
    keys = _load_json(_keys_path(), {})
    email = next((e for e, k in keys.items() if k['key'] == key), None)
    if email is None:
        return False, {'error': 'Clé API invalide', 'code': 'INVALID_API_KEY'}
    info = keys[email]
    today = date.today().isoformat()
    usage = _load_json(_usage_path(), {})
    used = usage.get(key, {}).get(today, 0)
    limit = info['daily_limit']
    if used >= limit:
        return False, {
            'error': 'Quota journalier atteint', 'code': 'QUOTA_EXCEEDED',
            'used': used, 'limit': limit, 'reset': today,
        }
    usage.setdefault(key, {})[today] = used + 1
    _save_json(_usage_path(), usage)
    return True, {'used': used + 1, 'limit': limit, 'plan': info['plan'], 'email': email}


# ── Le blueprint ─────────────────────────────────────────────────────────────

def register_wave_routes(app, services):
    """Enregistre les routes du service de calcul harmonique."""

    # ── Garde : clé API + quota (sauf OPTIONS et /status) ──
    @app.before_request
    def _wave_quota_guard():
        if not request.path.startswith('/api/wave/'):
            return None
        if request.method == 'OPTIONS':
            return None
        if request.method == 'GET' and request.path == '/api/wave/status':
            return None
        key = request.headers.get('X-API-Key', '')
        if not key:
            return jsonify({'error': 'Clé API requise (X-API-Key)',
                            'code': 'NO_API_KEY'}), 401
        ok, info = _check_quota(key)
        if not ok:
            return jsonify(info), (429 if info.get('code') == 'QUOTA_EXCEEDED' else 401)
        request.ka_wave_quota = info
        return None

    # ═══ STATUS (public) ═══
    @app.route('/api/wave/status', methods=['GET', 'OPTIONS'])
    def api_wave_status():
        if request.method == 'OPTIONS':
            return '', 200
        mem = _get_memory()
        return jsonify({
            'service': 'harmonic-compute',
            'status': 'ok',
            'engine': 'wave_lang.py — machine de Hilbert déterministe',
            'space': 'ℂ⁵¹² (limite de Bekenstein)',
            'normalization': '‖ψ‖ = 1 — l\'information est dans la direction',
            'determinism': '100 % — même entrée, même ψ (FNV-1a + φ-spacing)',
            'primitives': ['encode', 'decode', 'bind', 'unbind', 'superpose',
                           'resonate', 'rotate', 'normalize', 'interfere',
                           'diffract', 'filter', 'phase_shift', 'emerge'],
            'memory': {'facts': mem.n_facts, 'energy': round(mem.energy, 6)},
            'plans': PLANS,
            'honesty': [
                'Ceci est un émulateur harmonique : mêmes opérations que la '
                'cinématique quantique (superposition, unitaires, résonance), '
                'déterministes — PAS un ordinateur quantique matériel',
                'E1 (dériver Schrödinger/Q depuis l\'équation mère) : porte ouverte',
                'Les coefficients de l\'équation mère ne sont pas {φ, π, e} (X1)',
            ],
        }), 200

    # ═══ ENCODE / DECODE ═══
    @app.route('/api/wave/encode', methods=['POST', 'OPTIONS'])
    def api_wave_encode():
        if request.method == 'OPTIONS':
            return '', 200
        data = request.get_json() or {}
        entity = (data.get('entity') or '').strip()
        if not entity:
            return jsonify({'error': 'Entité vide', 'code': 'EMPTY_ENTITY'}), 400
        try:
            psi = encode(entity, dim=_DIM)
            return jsonify({'entity': entity, 'wave': _wave_to_json(psi),
                            'stats': stats(psi)}), 200
        except Exception as e:
            log.exception("wave encode error")
            return jsonify({'error': str(e), 'code': 'WAVE_ENCODE_ERROR'}), 500

    @app.route('/api/wave/decode', methods=['POST', 'OPTIONS'])
    def api_wave_decode():
        if request.method == 'OPTIONS':
            return '', 200
        data = request.get_json() or {}
        try:
            psi = _resolve(data.get('wave') or data.get('entity'))
        except Exception as e:
            return jsonify({'error': str(e), 'code': 'BAD_WAVE'}), 400
        vocabulary = data.get('vocabulary') or []
        vocab = {v: encode(v, dim=_DIM) for v in vocabulary} if vocabulary else None
        try:
            results = decode(psi, vocabulary=vocab, top_k=int(data.get('top_k', 5)))
            return jsonify({'decoded': [{'entity': w, 'score': round(s, 6)}
                                        for w, s in results]}), 200
        except Exception as e:
            log.exception("wave decode error")
            return jsonify({'error': str(e), 'code': 'WAVE_DECODE_ERROR'}), 500

    # ═══ OPÉRATIONS BINAIRES ═══
    def _binary(route, op, extra=None):
        endpoint = 'api_wave_' + route.strip('/').replace('/', '_')

        @app.route(route, methods=['POST', 'OPTIONS'], endpoint=endpoint)
        def _handler():
            if request.method == 'OPTIONS':
                return '', 200
            data = request.get_json() or {}
            try:
                # a : entrée principale (str ou ψ) · b : optionnelle (opérations unaires)
                a = _resolve(data.get('a') or data.get('c'))
                b_val = data.get('b')
                b = _resolve(b_val) if b_val is not None else None
                kwargs = {k: data[k] for k in (extra or []) if k in data}
                psi = op(a, b, **kwargs)
                return jsonify({'wave': _wave_to_json(psi), 'summary': _summary(psi)}), 200
            except Exception as e:
                log.exception("wave op error %s", route)
                return jsonify({'error': str(e), 'code': 'WAVE_OP_ERROR'}), 500
        return _handler

    _binary('/api/wave/bind', bind)
    _binary('/api/wave/unbind', unbind)
    _binary('/api/wave/rotate', lambda a, b=None, **k: rotate(a, **k), extra=['angle'])
    _binary('/api/wave/interfere', interfere, extra=['epsilon'])
    _binary('/api/wave/diffract', lambda a, b=None, **k: diffract(a, **k), extra=['inverse'])
    _binary('/api/wave/phase_shift', lambda a, b=None, **k: phase_shift(a, **k), extra=['shift'])

    @app.route('/api/wave/filter', methods=['POST', 'OPTIONS'])
    def api_wave_filter():
        """Passe-bas / passe-haut sur le spectre du ψ (cutoff ∈ [0, 1])."""
        if request.method == 'OPTIONS':
            return '', 200
        data = request.get_json() or {}
        try:
            a = _resolve(data.get('a'))
        except Exception as e:
            return jsonify({'error': str(e), 'code': 'BAD_WAVE'}), 400
        mode = data.get('mode', 'lowpass')
        cutoff = float(data.get('cutoff', 0.5))
        spec = np.fft.fft(a)
        n = len(spec)
        idx = int(cutoff * n)
        if mode == 'lowpass':
            spec[idx:] = 0
        elif mode == 'highpass':
            spec[:idx] = 0
        else:
            return jsonify({'error': "mode ∈ {lowpass, highpass}",
                            'code': 'BAD_FILTER_MODE'}), 400
        psi = normalize(np.fft.ifft(spec))
        return jsonify({'wave': _wave_to_json(psi), 'mode': mode,
                        'cutoff': cutoff, 'summary': _summary(psi)}), 200

    # ═══ SUPERPOSE / RESONATE / EMERGE ═══
    @app.route('/api/wave/superpose', methods=['POST', 'OPTIONS'])
    def api_wave_superpose():
        if request.method == 'OPTIONS':
            return '', 200
        data = request.get_json() or {}
        items = data.get('items') or []
        if not items:
            return jsonify({'error': 'Aucun item', 'code': 'EMPTY_ITEMS'}), 400
        try:
            psis = [_resolve(i) for i in items]
            weights = data.get('weights')
            psi = superpose(*psis, weights=weights) if weights else superpose(*psis)
            return jsonify({'wave': _wave_to_json(psi), 'count': len(psis),
                            'summary': _summary(psi)}), 200
        except Exception as e:
            log.exception("wave superpose error")
            return jsonify({'error': str(e), 'code': 'WAVE_SUPERPOSE_ERROR'}), 500

    @app.route('/api/wave/resonate', methods=['POST', 'OPTIONS'])
    def api_wave_resonate():
        if request.method == 'OPTIONS':
            return '', 200
        data = request.get_json() or {}
        try:
            a = _resolve(data.get('a'))
            b = _resolve(data.get('b'))
        except Exception as e:
            return jsonify({'error': str(e), 'code': 'BAD_WAVE'}), 400
        s = float(resonate(a, b))
        return jsonify({'resonance': round(s, 6),
                        'interpretation': 'identique' if abs(s - 1.0) < 1e-9
                        else ('orthogonal' if abs(s) < 1e-9
                              else 'partiel' if s > 0.3
                              else 'faible')}), 200

    @app.route('/api/wave/emerge', methods=['POST', 'OPTIONS'])
    def api_wave_emerge():
        if request.method == 'OPTIONS':
            return '', 200
        data = request.get_json() or {}
        items = data.get('items') or []
        if not items:
            return jsonify({'error': 'Aucun item', 'code': 'EMPTY_ITEMS'}), 400
        try:
            psis = [_resolve(i) for i in items]
            psi = emerge(*psis, temperature=float(data.get('temperature', 0.5)))
            return jsonify({'wave': _wave_to_json(psi),
                            'summary': _summary(psi)}), 200
        except Exception as e:
            log.exception("wave emerge error")
            return jsonify({'error': str(e), 'code': 'WAVE_EMERGE_ERROR'}), 500

    # ═══ MÉMOIRE HOLOGRAPHIQUE ═══
    @app.route('/api/wave/memory/store', methods=['POST', 'OPTIONS'])
    def api_wave_memory_store():
        if request.method == 'OPTIONS':
            return '', 200
        data = request.get_json() or {}
        facts = data.get('facts') or []
        if not facts:
            return jsonify({'error': 'Aucun fait [[sujet, relation, objet]]',
                            'code': 'EMPTY_FACTS'}), 400
        mem = _get_memory()
        stored = []
        for f in facts:
            if len(f) < 3:
                continue
            try:
                mem.store(encode(f[0], dim=_DIM), encode(f[1], dim=_DIM),
                          encode(f[2], dim=_DIM))
                _fact_log.append([str(f[0]), str(f[1]), str(f[2])])
                stored.append(f)
            except Exception:
                continue
        _persist_memory()
        return jsonify({'stored': len(stored), 'total_facts': mem.n_facts,
                        'energy': round(mem.energy, 6)}), 200

    @app.route('/api/wave/memory/query', methods=['POST', 'OPTIONS'])
    def api_wave_memory_query():
        if request.method == 'OPTIONS':
            return '', 200
        data = request.get_json() or {}
        query = (data.get('query') or '').strip()
        if not query:
            return jsonify({'error': 'Requête vide', 'code': 'EMPTY_QUERY'}), 400
        mem = _get_memory()
        try:
            psi_q = encode(query, dim=_DIM)
            scores = mem.query_scores(psi_q)
            top = scores[:int(data.get('top_k', 5))]
            return jsonify({
                'query': query,
                'results': [{'fact_index': i, 'resonance': round(s, 6)} for i, s in top],
                'total_facts': mem.n_facts,
            }), 200
        except Exception as e:
            log.exception("wave memory query error")
            return jsonify({'error': str(e), 'code': 'WAVE_MEMORY_ERROR'}), 500

    @app.route('/api/wave/memory/stats', methods=['GET', 'OPTIONS'])
    def api_wave_memory_stats():
        if request.method == 'OPTIONS':
            return '', 200
        mem = _get_memory()
        return jsonify({'facts': mem.n_facts, 'energy': round(mem.energy, 6),
                        'mechanism': 'H = Σ ψ_fait — superposition, pas d\'écrasement',
                        'forget': 'noyau ABC (α = 1/φ) — t^{−0,618}'}), 200

    # ═══ ARITHMÉTIQUE ÉMERGENTE ═══
    @app.route('/api/wave/solve', methods=['POST', 'OPTIONS'])
    def api_wave_solve():
        if request.method == 'OPTIONS':
            return '', 200
        data = request.get_json() or {}
        expression = (data.get('expression') or '').strip()
        if not expression:
            return jsonify({'error': 'Expression vide', 'code': 'EMPTY_EXPRESSION'}), 400
        try:
            from ka_server.services.harmonic_v3 import get_harmonic_v3
            engine = get_harmonic_v3()
            if engine is None:
                return jsonify({'error': 'Moteur indisponible',
                                'code': 'ENGINE_UNAVAILABLE'}), 503
            return jsonify({'expression': expression,
                            'result': engine.solve(expression),
                            'method': 'émergence ondulatoire (Ψ_a·Ψ_b = Ψ_{a+b})'}), 200
        except Exception as e:
            log.exception("wave solve error")
            return jsonify({'error': str(e), 'code': 'WAVE_SOLVE_ERROR'}), 500

    # ═══ BENCHMARK EN DIRECT ═══
    @app.route('/api/wave/benchmark', methods=['GET', 'OPTIONS'])
    def api_wave_benchmark():
        if request.method == 'OPTIONS':
            return '', 200
        t0 = time.time()
        # 1 · Normalisation : ‖encode(x)‖ = 1
        psi = encode('test', dim=_DIM)
        norm_ok = abs(float(np.linalg.norm(psi)) - 1.0) < 1e-9
        # 2 · Résonance identité : resonate(a, a) = 1
        self_ok = abs(float(resonate(psi, psi)) - 1.0) < 1e-9
        # 3 · Bind/unbind : unbind(bind(a,b), b) ≈ a (récupération)
        a, b = encode('alpha', dim=_DIM), encode('beta', dim=_DIM)
        recovery = float(resonate(a, unbind(bind(a, b), b)))
        # 4 · Rotation : rotate(ψ, π) → résonance −1
        rot = float(resonate(psi, rotate(psi, np.pi)))
        # 5 · Apprentissage : 3 expositions → APPRIS (seuil doré ≈ 1,19)
        mem = _get_memory()
        mem.store(encode('test_sujet', dim=_DIM), encode('test_relation', dim=_DIM),
                  encode('test_objet', dim=_DIM))
        amp3 = float(np.linalg.norm(mem.memory))
        elapsed = (time.time() - t0) * 1000
        return jsonify({
            'elapsed_ms': round(elapsed, 2),
            'engine': 'wave_lang.py — ℂ⁵¹²',
            'results': {
                'normalization_‖encode(x)‖=1': {'value': round(float(np.linalg.norm(psi)), 9), 'pass': norm_ok},
                'resonance_identité_⟨a|a⟩=1': {'value': round(float(resonate(psi, psi)), 9), 'pass': self_ok},
                'bind_unbind_recovery': {'value': round(recovery, 6), 'pass': recovery >= 0.7},
                'rotate(ψ,π)→−1': {'value': round(rot, 6), 'pass': abs(rot + 1.0) < 1e-6},
            },
            'note': 'Démos vérifiées en direct — chaque affirmation est une commande.',
        }), 200


__all__ = ['register_wave_routes', 'create_key', 'PLANS']
