"""
KA Server — Routes Harmonic AI v3
==================================
Endpoints pour l'intelligence ondulatoire unifiée :
  - /api/harmonic/status   → état du moteur 3-espaces
  - /api/harmonic/ask      → QA + arithmétique émergente
  - /api/harmonic/solve    → arithmétique émergente dédiée
  - /api/harmonic/facts    → ingérer des faits (triplets)
  - /api/harmonic/coherence→ détection de contradiction
"""

import logging
from flask import request, jsonify

log = logging.getLogger(__name__)


def register_harmonic_routes(app, services):
    """Enregistre les routes Harmonic v3."""
    
    @app.route('/api/harmonic/status', methods=['GET', 'OPTIONS'])
    def api_harmonic_status():
        if request.method == 'OPTIONS':
            return '', 200
        try:
            from ka_server.services.harmonic_v3 import get_harmonic_v3, is_available
            engine = get_harmonic_v3()
            return jsonify({
                'engine': 'harmonic_v3',
                'architecture': '3-espaces (Phase + Log + Kuramoto + Champ)',
                'available': is_available(),
                'facts': engine.stats['facts'] if engine else 0,
                'emergence_ops': engine.stats['emergence'] if engine else 0,
                'coherence': engine.coherence() if engine else None,
                'principles': [
                    "L'addition ÉMERGE : Ψ_a·Ψ_b = Ψ_{a+b} (0 fait stocké)",
                    "La négation est PHYSIQUE : Ψ + (-Ψ) = 0",
                    "La logique SYNCHRONISE : dθ/dt = ΣK sin(Δθ)",
                    "GSM8K : 89.7% (gap 2.7pts vs patterns mémorisés)",
                ],
            }), 200
        except Exception as e:
            log.exception("harmonic status error")
            return jsonify({'error': str(e), 'code': 'HARMONIC_STATUS_ERROR'}), 500
    
    @app.route('/api/harmonic/solve', methods=['POST', 'OPTIONS'])
    def api_harmonic_solve():
        """Résout une expression arithmétique par ÉMERGENCE."""
        if request.method == 'OPTIONS':
            return '', 200
        data = request.get_json() or {}
        expression = data.get('expression', '').strip()
        if not expression:
            return jsonify({'error': 'Expression vide', 'code': 'EMPTY_EXPRESSION'}), 400
        
        try:
            from ka_server.services.harmonic_v3 import get_harmonic_v3
            engine = get_harmonic_v3()
            if engine is None:
                return jsonify({'error': 'Moteur indisponible', 'code': 'ENGINE_UNAVAILABLE'}), 503
            
            result = engine.solve(expression)
            return jsonify({
                'expression': expression,
                'result': result,
                'method': 'emergence_ondulatoire',
                'facts_stored': 0,  # l'arithmétique n'est JAMAIS stockée
                'coherence': engine.coherence(),
            }), 200
        except Exception as e:
            log.exception("harmonic solve error")
            return jsonify({'error': str(e), 'code': 'HARMONIC_SOLVE_ERROR'}), 500
    
    @app.route('/api/harmonic/ask', methods=['POST', 'OPTIONS'])
    def api_harmonic_ask():
        """QA par inférence Kuramoto + arithmétique."""
        if request.method == 'OPTIONS':
            return '', 200
        data = request.get_json() or {}
        question = data.get('question', '').strip()
        candidates = data.get('candidates', [])
        if not question:
            return jsonify({'error': 'Question vide', 'code': 'EMPTY_QUESTION'}), 400
        
        try:
            from ka_server.services.harmonic_v3 import get_harmonic_v3, process_harmonic
            engine = get_harmonic_v3()
            if engine is None:
                return jsonify({'error': 'Moteur indisponible', 'code': 'ENGINE_UNAVAILABLE'}), 503
            
            # Arithmétique d'abord
            processed = process_harmonic(question, candidates)
            if processed.get('handled'):
                return jsonify(processed), 200
            
            # Sinon QA Kuramoto
            if candidates:
                results = engine.ask(question, candidates, steps=500)
                return jsonify({
                    'question': question,
                    'results': [{'candidate': c, 'score': s, 'verdict': v}
                                for c, s, v in results],
                    'method': 'kuramoto_synchronization',
                    'coherence': engine.coherence(),
                }), 200
            
            return jsonify({'question': question, 'results': [],
                            'note': 'Fournir des candidats pour la QA factuelle'}), 200
        except Exception as e:
            log.exception("harmonic ask error")
            return jsonify({'error': str(e), 'code': 'HARMONIC_ASK_ERROR'}), 500
    
    @app.route('/api/harmonic/facts', methods=['POST', 'OPTIONS'])
    def api_harmonic_facts():
        """Ingère des faits (triplets) dans les 3 espaces."""
        if request.method == 'OPTIONS':
            return '', 200
        data = request.get_json() or {}
        facts = data.get('facts', [])  # [[sujet, relation, objet], ...]
        if not facts:
            return jsonify({'error': 'Aucun fait', 'code': 'EMPTY_FACTS'}), 400
        
        try:
            from ka_server.services.harmonic_v3 import get_harmonic_v3
            engine = get_harmonic_v3()
            if engine is None:
                return jsonify({'error': 'Moteur indisponible', 'code': 'ENGINE_UNAVAILABLE'}), 503
            
            ingested = 0
            for fact in facts:
                if len(fact) >= 3:
                    engine.ingest(fact[0], fact[1], fact[2])
                    ingested += 1
            
            return jsonify({
                'ingested': ingested,
                'total_facts': engine.stats['facts'],
                'method': '3_espaces (ℂ⁵¹² + [0,L] + S¹)',
            }), 200
        except Exception as e:
            log.exception("harmonic facts error")
            return jsonify({'error': str(e), 'code': 'HARMONIC_FACTS_ERROR'}), 500
    
    @app.route('/api/harmonic/coherence', methods=['GET', 'OPTIONS'])
    def api_harmonic_coherence():
        """Détecte la cohérence / contradiction de la base."""
        if request.method == 'OPTIONS':
            return '', 200
        try:
            from ka_server.services.harmonic_v3 import get_harmonic_v3
            engine = get_harmonic_v3()
            if engine is None:
                return jsonify({'error': 'Moteur indisponible', 'code': 'ENGINE_UNAVAILABLE'}), 503
            
            r = engine.coherence()
            return jsonify({
                'coherence': r,
                'interpretation': 'cohérent' if r > 0.7 else 'CONTRADICTION (frustration)',
                'mechanism': 'r → 0 = verre de spin frustré ; r → 1 = système de croyances cohérent',
            }), 200
        except Exception as e:
            log.exception("harmonic coherence error")
            return jsonify({'error': str(e), 'code': 'HARMONIC_COHERENCE_ERROR'}), 500
