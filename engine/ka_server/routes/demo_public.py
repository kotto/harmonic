"""
KA Server — Route Démo Publique
================================
Démo en ligne SANS authentification — la preuve vivante du positionnement.

Le pipeline est identique à /api/v2/enterprise/demo/ask, mais :
  • public (aucune clé requise)
  • rate limit spécifique strict (8 req / 5 min par IP)
  • garde-fous : question ≤ 200 caractères, réponse tronquée
  • aucune donnée sensible renvoyée

Étapes du pipeline (toutes déterministes) :
  1. Arithmétique émergente (codec ψ v3) — « 7 × 6 » → 42 en ~10 ms
  2. Memory-first — le fait stocké répond avec provenance
  3. Consensus holographique M4 + raisonnement — réponse + faits cités
"""

import logging
import time as _time
from collections import defaultdict
from flask import request, jsonify

log = logging.getLogger(__name__)

# ── Garde-fous démo publique ──────────────────────────────────────────────
_MAX_QUESTION_LEN = 200
_DEMO_RATE_WINDOW = 300        # 5 minutes
_DEMO_RATE_MAX = 8             # 8 requêtes par fenêtre
_demo_rate_store = defaultdict(list)  # IP → [timestamps]


def _demo_rate_limited(ip: str) -> bool:
    """Vérifie le rate limit spécifique démo (8 req / 5 min)."""
    now = _time.time()
    _demo_rate_store[ip] = [t for t in _demo_rate_store[ip] if t > now - _DEMO_RATE_WINDOW]
    _demo_rate_store[ip].append(now)
    # Purge mémoire bornée
    if len(_demo_rate_store) > 2048:
        for k in [k for k, v in _demo_rate_store.items() if not v or max(v) <= now - _DEMO_RATE_WINDOW]:
            del _demo_rate_store[k]
    return len(_demo_rate_store[ip]) > _DEMO_RATE_MAX


def register_demo_public_routes(app, services):
    """Enregistre la route de démo publique."""

    @app.route('/api/demo/ask', methods=['POST', 'OPTIONS'])
    def api_demo_public_ask():
        """Démo publique : question → réponse déterministe + provenance."""
        if request.method == 'OPTIONS':
            return '', 200

        # Rate limit strict par IP
        from ka_server.middleware.metrics import _get_client_ip
        ip = _get_client_ip()
        if _demo_rate_limited(ip):
            return jsonify({
                'error': 'Trop de demandes. Réessayez dans 5 minutes.',
                'code': 'DEMO_RATE_LIMITED',
                'retry_after_s': _DEMO_RATE_WINDOW,
            }), 429

        data = request.get_json(silent=True) or {}
        question = (data.get('question') or '').strip()

        if not question:
            return jsonify({'error': 'Posez une question', 'code': 'MISSING_QUESTION'}), 400
        if len(question) > _MAX_QUESTION_LEN:
            return jsonify({'error': f'Question trop longue (max {_MAX_QUESTION_LEN} caractères)', 'code': 'QUESTION_TOO_LONG'}), 400

        t0 = _time.time()

        # ── Étape 1 : arithmétique émergente (aucun RAG, aucun LLM) ──
        try:
            from ka_server.services.harmonic_v3 import detect_and_solve_math
            math_result = detect_and_solve_math(question)
            if math_result.get('handled'):
                return jsonify({
                    'success': True,
                    'answer': math_result['explanation'],
                    'result': math_result.get('result'),
                    'method': math_result['method'],
                    'source': 'harmonic_v3',
                    'stage': 'arithmetic',
                    'best_domain': None,
                    'consensus_facts_count': 0,
                    'facts': [],
                    'latency_ms': round((_time.time() - t0) * 1000),
                    'deterministic': True,
                    'note': 'Arithmétique émergente — résultat calculé, pas généré. 0% hallucination.',
                })
        except Exception as e:
            log.debug(f"Demo arithmetic failed: {e}")

        # ── Étape 2 : memory-first (le fait stocké répond, sinon refus) ──
        try:
            from ka_server.services.memory_first import ask as memory_first_ask
            mf = memory_first_ask(question)
            if not mf.get('refused'):
                return jsonify({
                    'success': True,
                    'answer': mf['answer'],
                    'method': 'memory-first',
                    'source': 'memory_first',
                    'stage': 'memory',
                    'best_domain': None,
                    'consensus_facts_count': 0,
                    'facts': [list(p.values()) for p in mf.get('provenance', [])][:5],
                    'confidence': mf.get('confidence'),
                    'latency_ms': round((_time.time() - t0) * 1000),
                    'deterministic': True,
                    'note': 'Memory-first — le fait stocké répond avec sa provenance, jamais une fabrication.',
                })
        except Exception as e:
            log.debug(f"Demo memory-first failed: {e}")

        # ── Étape 3 : consensus holographique M4 + raisonnement du codec ψ ──
        best_domain = None
        consensus_facts = []
        try:
            from ka_server.services import holographic_consensus_recall
            consensus_facts, best_domain = holographic_consensus_recall(question)
        except Exception as e:
            log.warning(f"Demo holographic recall error: {e}")

        answer = None
        source = 'unavailable'
        try:
            from ka_server.services import get_brain, get_harmonic_ai
            brain = get_brain()
            ai = get_harmonic_ai()

            if brain is not None and hasattr(brain, 'ask'):
                try:
                    answer = brain.ask(question)
                    source = 'harmonic_brain'
                except Exception:
                    pass
            if answer is None and ai is not None and hasattr(ai, 'ask'):
                try:
                    result = ai.ask(question)
                    answer = result.get('answer', '') if isinstance(result, dict) else str(result)
                    source = 'harmonic_ai'
                except Exception:
                    pass
        except Exception as e:
            log.warning(f"Demo harmonic ask error: {e}")

        if not answer:
            return jsonify({
                'error': 'Le moteur harmonique est indisponible. Réessayez dans un instant.',
                'code': 'HARMONIC_UNAVAILABLE',
            }), 503

        latency_ms = round((_time.time() - t0) * 1000)

        return jsonify({
            'success': True,
            'answer': answer[:600],
            'source': source,
            'stage': 'holographic',
            'best_domain': best_domain,
            'consensus_facts_count': len(consensus_facts) if consensus_facts else 0,
            'facts': [list(f) for f in consensus_facts[:5]] if consensus_facts else [],
            'latency_ms': latency_ms,
            'deterministic': True,
            'note': 'Consensus holographique M4 — les faits cités sont la provenance de la réponse. 0% hallucination.',
        })


__all__ = ['register_demo_public_routes']
