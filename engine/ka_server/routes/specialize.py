"""
KA Server — Routes Specialize (Spécialisation Domaine)
=======================================================
Endpoints pour créer/spécialiser des hologrammes de domaine.
"""

import logging
import re
from flask import request, jsonify

log = logging.getLogger(__name__)


def register_specialize_routes(app, services):
    """Enregistre les routes de spécialisation."""
    
    specializer = services.get('specializer')
    optimized_specializer = services.get('optimized_specializer')
    hf_specializer = services.get('hf_specializer')  # 🤗
    web_retriever = services.get('web_retriever')
    brain = services.get('brain')
    hologram_store = services.get('hologram_store')
    
    @app.route('/api/specialize', methods=['POST', 'OPTIONS'])
    def api_specialize():
        """Crée/spécialise un hologramme sur un domaine."""
        if request.method == 'OPTIONS':
            return '', 200
        
        data = request.get_json() or {}
        domain = data.get('domain', '').strip()
        user_kbs = data.get('user_kbs', [])
        force_refresh = data.get('force_refresh', False)
        mode = data.get('mode', 'auto').lower()
        use_optimized = data.get('use_optimized', True)  # retrocompatibilité
        
        if not domain:
            return jsonify({'error': 'Domaine requis', 'code': 'MISSING_DOMAIN'}), 400
        
        # Vérifier si hologramme existe déjà
        if hologram_store and mode != 'huggingface':
            existing = hologram_store.get_hologram(domain)
            if existing and not force_refresh:
                return jsonify({
                    'success': True,
                    'domain': domain,
                    'status': 'exists',
                    'hologram': existing,
                    'message': f"Hologramme '{domain}' existe déjà. Utilisez force_refresh=true pour recréer."
                })
        
        # Mode HuggingFace explicite
        if mode == 'huggingface' and hf_specializer:
            try:
                log.info(f"  🤗 Spécialisation HF pour '{domain}'")
                result = hf_specializer(domain)
                return jsonify(_format_specialize_result(result, domain, 'huggingface'))
            except Exception as e:
                log.error(f"HF specialize failed: {e}")
                return jsonify({'error': f"HF specialize failed: {e}", 'code': 'HF_FAILED'}), 500
        
        # Modes existants…
        
        # Utiliser OptimizedSpecializer si dispo
        if use_optimized and optimized_specializer:
            try:
                result = optimized_specializer.specialize(domain, user_kbs=user_kbs)
                return jsonify(_format_specialize_result(result, domain, 'optimized'))
            except Exception as e:
                log.warning(f"Optimized specialize failed: {e}")
        
        # Fallback DomainSpecializer
        if specializer:
            try:
                result = specializer.specialize(domain, user_kbs=user_kbs)
                return jsonify(_format_specialize_result(result, domain, 'standard'))
            except Exception as e:
                log.warning(f"Standard specialize failed: {e}")
        
        # Fallback web_retriever direct
        if web_retriever:
            try:
                result = _specialize_with_web_retriever(web_retriever, domain, user_kbs)
                return jsonify(_format_specialize_result(result, domain, 'web_only'))
            except Exception as e:
                log.warning(f"Web retriever specialize failed: {e}")
        
        return jsonify({
            'error': 'Spécialisation non disponible',
            'code': 'SPECIALIZE_UNAVAILABLE'
        }), 503
    
    @app.route('/api/specialize/intent', methods=['POST', 'OPTIONS'])
    def api_specialize_intent():
        """Détecte l'intention de spécialisation dans un message."""
        if request.method == 'OPTIONS':
            return '', 200
        
        data = request.get_json() or {}
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Message requis', 'code': 'MISSING_MESSAGE'}), 400
        
        # Détection regex
        from ka_server.services.harmonic_ai import _SPECIALIZE_RE
        match = _SPECIALIZE_RE.match(message)
        
        if match:
            domain = match.group(1).strip()
            return jsonify({
                'is_specialize_intent': True,
                'domain': domain,
                'original_message': message,
                'confidence': 0.95,
            })
        
        # Mots-clés faible confiance
        keywords = ['spécialise', 'expert', 'hologramme', 'domaine', 'deviens']
        found = [k for k in keywords if k in message.lower()]
        
        return jsonify({
            'is_specialize_intent': len(found) > 0,
            'domain': None,
            'original_message': message,
            'confidence': 0.3 if found else 0.0,
            'keywords_found': found,
        })
    
    @app.route('/api/specialize/status/<domain>', methods=['GET'])
    def api_specialize_status(domain):
        """Status d'une spécialisation en cours ou terminée."""
        if not hologram_store:
            return jsonify({'error': 'Store non disponible'}), 503
        
        holo = hologram_store.get_hologram(domain)
        if not holo:
            return jsonify({
                'domain': domain,
                'status': 'not_found',
                'exists': False
            })
        
        return jsonify({
            'domain': domain,
            'status': 'completed',
            'exists': True,
            'hologram': holo,
            'facts_count': holo.get('facts_count', 0),
            'has_wave_format': holo.get('has_wave_format', False),
            'created_at': holo.get('created_at'),
            'updated_at': holo.get('updated_at'),
        })
    
    @app.route('/api/specialize/list', methods=['GET'])
    def api_specialize_list():
        """Liste tous les hologrammes spécialisés."""
        if not hologram_store:
            return jsonify({'error': 'Store non disponible'}), 503
        
        try:
            holos = hologram_store.list_holograms()
            specialized = [h for h in holos if h.get('category') == 'specialized' or 'specialized' in h.get('tags', [])]
            
            return jsonify({
                'specialized_holograms': specialized,
                'count': len(specialized),
            })
        except Exception as e:
            log.error(f"List specialized failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/specialize/optimize', methods=['POST', 'OPTIONS'])
    def api_specialize_optimize():
        """Optimise un hologramme existant (compression, pruning)."""
        if request.method == 'OPTIONS':
            return '', 200
        
        data = request.get_json() or {}
        domain = data.get('domain', '').strip()
        target_facts = data.get('target_facts', 1000)
        
        if not domain:
            return jsonify({'error': 'Domaine requis'}), 400
        
        if not hologram_store:
            return jsonify({'error': 'Store non disponible'}), 503
        
        holo = hologram_store.get_hologram(domain)
        if not holo:
            return jsonify({'error': 'Hologramme non trouvé', 'code': 'NOT_FOUND'}), 404
        
        # TODO: Implémenter optimisation réelle
        return jsonify({
            'domain': domain,
            'status': 'optimization_not_implemented',
            'current_facts': holo.get('facts_count', 0),
            'target_facts': target_facts,
        })


def _specialize_with_web_retriever(web_retriever, domain: str, user_kbs: list) -> dict:
    """Spécialisation basique avec WebRetriever seul."""
    try:
        # Recherche web
        results = web_retriever.search(domain, max_results=10)
        
        # Construire faits basiques
        facts = []
        for r in results[:5]:
            content = r.get('content', '')
            url = r.get('url', '')
            if content:
                facts.append((domain, 'a_pour_source', url, 'web', 0.8))
                # Extraire phrases clés
                sentences = re.split(r'[.!?]+', content)
                for s in sentences[:3]:
                    s = s.strip()
                    if len(s) > 20:
                        facts.append((domain, 'contient', s[:200], 'web', 0.6))
        
        return {
            'domain': domain,
            'facts': facts,
            'sources': [r.get('url') for r in results],
            'fact_count': len(facts),
        }
    except Exception as e:
        return {'domain': domain, 'facts': [], 'error': str(e)}


def _format_specialize_result(result: dict, domain: str, method: str) -> dict:
    """Formate le résultat de spécialisation."""
    if not result:
        return {
            'success': False,
            'domain': domain,
            'method': method,
            'error': 'Aucun résultat'
        }
    
    success = result.get('success', True)
    facts = result.get('facts', [])
    fact_count = result.get('fact_count', len(facts))
    
    response = {
        'success': success,
        'domain': domain,
        'method': method,
        'facts_created': fact_count,
        'facts_sample': facts[:10] if facts else [],
        'sources': result.get('sources', []),
        'hologram_id': result.get('hologram_id', domain),
        'message': f"Spécialisation '{domain}' terminée: {fact_count} faits créés" if success else result.get('error', 'Échec'),
    }
    
    # Ajouter champs supplémentaires (huggingface, etc.)
    for extra in ('datasets_found', 'source_name', 'inference_facts'):
        if extra in result:
            response[extra] = result[extra]
    
    return response