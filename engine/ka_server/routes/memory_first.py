"""
KA Server — Routes Memory-First (l'architecture memory-first)
=============================================================
Le LLM ne sait rien : il formule ce que la mémoire certifie, et se tait
quand elle se tait.

  POST /api/memory-first/ask    → {answer, provenance, confidence, refused, reason}
  POST /api/memory-first/store  → stocke des faits avec SOURCE (provenance)
  GET  /api/memory-first/stats  → faits, vocabulaire, seuil, honnêtetés
"""

import logging

from flask import jsonify, request

log = logging.getLogger(__name__)


def register_memory_first_routes(app, services):
    """Enregistre les routes memory-first (provenance + refus structurel)."""
    from ka_server.services.memory_first import ask, stats, store_fact

    @app.route('/api/memory-first/ask', methods=['POST', 'OPTIONS'])
    def api_memory_first_ask():
        if request.method == 'OPTIONS':
            return '', 200
        data = request.get_json() or {}
        query = (data.get('query') or '').strip()
        if not query:
            return jsonify({'error': 'Requête vide', 'code': 'EMPTY_QUERY'}), 400
        try:
            result = ask(query, threshold=data.get('threshold'))
            return jsonify(result), 200
        except Exception as e:
            log.exception('memory-first ask error')
            return jsonify({'error': str(e), 'code': 'MEMORY_FIRST_ERROR'}), 500

    @app.route('/api/memory-first/store', methods=['POST', 'OPTIONS'])
    def api_memory_first_store():
        if request.method == 'OPTIONS':
            return '', 200
        data = request.get_json() or {}
        facts = data.get('facts') or []
        stored = 0
        for f in facts:
            if len(f) < 3:
                continue
            store_fact(str(f[0]), str(f[1]), str(f[2]),
                       source=str(f[3]) if len(f) > 3 else '')
            stored += 1
        return jsonify({'stored': stored,
                        'mechanism': 'apprentissage O(1) — un fait = une onde'}), 200

    @app.route('/api/memory-first/stats', methods=['GET', 'OPTIONS'])
    def api_memory_first_stats():
        if request.method == 'OPTIONS':
            return '', 200
        return jsonify(stats()), 200


__all__ = ['register_memory_first_routes']
