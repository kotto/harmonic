"""
KA Server — Routes Hologram Store
==================================
Endpoints pour le magasin d'hologrammes (téléchargement, listing, info).
"""

import logging
from flask import request, jsonify, send_file
import io

log = logging.getLogger(__name__)


def register_store_routes(app, services):
    """Enregistre les routes du Hologram Store."""
    
    hologram_store = services.get('hologram_store')
    
    @app.route('/api/store/holograms', methods=['GET'])
    def api_store_list():
        """Liste tous les hologrammes disponibles."""
        if not hologram_store:
            return jsonify({
                'error': 'Hologram Store non disponible',
                'code': 'STORE_UNAVAILABLE'
            }), 503
        
        try:
            holos = hologram_store.list_holograms()
            
            # Filtres optionnels
            category = request.args.get('category')
            if category:
                holos = [h for h in holos if h.get('category') == category]
            
            search = request.args.get('search', '').lower()
            if search:
                holos = [h for h in holos if search in h.get('id', '').lower() 
                         or search in h.get('description', '').lower()]
            
            # Pagination
            page = max(1, int(request.args.get('page', 1)))
            per_page = min(50, int(request.args.get('per_page', 20)))
            total = len(holos)
            start = (page - 1) * per_page
            end = start + per_page
            
            return jsonify({
                'holograms': holos[start:end],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                },
                'categories': list(set(h.get('category', 'general') for h in holos))
            })
        except Exception as e:
            log.error(f"Store list error: {e}")
            return jsonify({'error': str(e), 'code': 'LIST_FAILED'}), 500
    
    @app.route('/api/store/holograms/<holo_id>', methods=['GET'])
    def api_store_get(holo_id):
        """Détails d'un hologramme."""
        if not hologram_store:
            return jsonify({'error': 'Store non disponible', 'code': 'STORE_UNAVAILABLE'}), 503
        
        try:
            holo = hologram_store.get_hologram(holo_id)
            if not holo:
                return jsonify({'error': 'Hologramme non trouvé', 'code': 'NOT_FOUND'}), 404
            
            return jsonify(holo)
        except Exception as e:
            log.error(f"Store get error: {e}")
            return jsonify({'error': str(e), 'code': 'GET_FAILED'}), 500
    
    @app.route('/api/store/holograms/<holo_id>/download', methods=['GET'])
    def api_store_download(holo_id):
        """Télécharge un hologramme (format .holo ou .wave)."""
        if not hologram_store:
            return jsonify({'error': 'Store non disponible', 'code': 'STORE_UNAVAILABLE'}), 503
        
        format = request.args.get('format', 'wave')  # 'wave' ou 'holo'
        
        try:
            data = hologram_store.download(holo_id, format=format)
            if not data:
                return jsonify({'error': 'Hologramme non trouvé', 'code': 'NOT_FOUND'}), 404
            
            ext = '.wave' if format == 'wave' else '.holo'
            filename = f"{holo_id}{ext}"
            
            output = io.BytesIO(data)
            output.seek(0)
            return send_file(
                output,
                mimetype='application/octet-stream',
                as_attachment=True,
                download_name=filename
            )
        except Exception as e:
            log.error(f"Store download error: {e}")
            return jsonify({'error': str(e), 'code': 'DOWNLOAD_FAILED'}), 500
    
    @app.route('/api/store/holograms/<holo_id>/recall', methods=['POST'])
    def api_store_recall(holo_id):
        """Rappel holographique sur un hologramme spécifique."""
        if not hologram_store:
            return jsonify({'error': 'Store non disponible', 'code': 'STORE_UNAVAILABLE'}), 503
        
        data = request.get_json() or {}
        query = data.get('query', '')
        top_k = min(int(data.get('top_k', 10)), 50)
        
        if not query:
            return jsonify({'error': 'Query requise', 'code': 'MISSING_QUERY'}), 400
        
        try:
            if not hologram_store.has_wave_format(holo_id):
                return jsonify({
                    'error': 'Hologramme non compatible rappel holographique',
                    'code': 'INCOMPATIBLE_FORMAT'
                }), 400
            
            results = hologram_store.recall(holo_id, query, top_k=top_k)
            
            return jsonify({
                'hologram_id': holo_id,
                'query': query,
                'results': [
                    {'subject': s, 'relation': r, 'object': o, 'sector': sec, 'score': float(score)}
                    for s, r, o, sec, score in results
                ],
                'count': len(results)
            })
        except Exception as e:
            log.error(f"Store recall error: {e}")
            return jsonify({'error': str(e), 'code': 'RECALL_FAILED'}), 500
    
    @app.route('/api/store/categories', methods=['GET'])
    def api_store_categories():
        """Liste les catégories disponibles."""
        if not hologram_store:
            return jsonify({'error': 'Store non disponible', 'code': 'STORE_UNAVAILABLE'}), 503
        
        try:
            holos = hologram_store.list_holograms()
            categories = {}
            for h in holos:
                cat = h.get('category', 'general')
                categories[cat] = categories.get(cat, 0) + 1
            
            return jsonify({
                'categories': [
                    {'name': k, 'count': v} for k, v in sorted(categories.items(), key=lambda x: -x[1])
                ]
            })
        except Exception as e:
            log.error(f"Store categories error: {e}")
            return jsonify({'error': str(e), 'code': 'CATEGORIES_FAILED'}), 500
    
    @app.route('/api/store/stats', methods=['GET'])
    def api_store_stats():
        """Statistiques du store."""
        if not hologram_store:
            return jsonify({'error': 'Store non disponible', 'code': 'STORE_UNAVAILABLE'}), 503
        
        try:
            holos = hologram_store.list_holograms()
            total_facts = sum(h.get('facts_count', 0) for h in holos)
            wave_compatible = sum(1 for h in holos if h.get('has_wave_format', False))
            
            return jsonify({
                'total_holograms': len(holos),
                'total_facts': total_facts,
                'wave_compatible': wave_compatible,
                'categories': len(set(h.get('category', 'general') for h in holos)),
            })
        except Exception as e:
            log.error(f"Store stats error: {e}")
            return jsonify({'error': str(e), 'code': 'STATS_FAILED'}), 500