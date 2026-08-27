"""
KA Server — Routes Tools
=========================
Endpoints pour les outils : analyse document, traduction, idées.

Routes :
    POST /api/tools/document/analyze  — Analyse et résumé de document
    POST /api/tools/translate          — Traduction de texte
    POST /api/tools/ideas              — Créer une idée
    GET  /api/tools/ideas              — Lister les idées
    GET  /api/tools/ideas/<id>         — Détail d'une idée
    PUT  /api/tools/ideas/<id>         — Modifier une idée
    DELETE /api/tools/ideas/<id>       — Supprimer une idée
"""

import logging
from flask import request, jsonify

log = logging.getLogger(__name__)


def register_tools_routes(app, services):
    """Enregistre les routes outils."""

    # Récupérer les services
    tools_svc = services.get('tools')
    harmonic_ai = services.get('harmonic_ai')

    # ═══════════════════════════════════════════════════════════════════
    # 1. 📄 ANALYSE DOCUMENT
    # ═══════════════════════════════════════════════════════════════════
    @app.route('/api/tools/document/analyze', methods=['POST', 'OPTIONS'])
    def api_document_analyze():
        """Analyse et résume un document uploadé."""
        if request.method == 'OPTIONS':
            return '', 200

        if 'multipart/form-data' not in (request.content_type or ''):
            return jsonify({'error': 'Content-Type doit être multipart/form-data',
                           'code': 'INVALID_CONTENT_TYPE'}), 400

        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'Aucun fichier fourni', 'code': 'NO_FILE'}), 400

        file_data = file.read()
        if len(file_data) == 0:
            return jsonify({'error': 'Fichier vide', 'code': 'EMPTY_FILE'}), 400

        if len(file_data) > 50 * 1024 * 1024:  # 50 Mo max
            return jsonify({'error': 'Fichier trop volumineux (max 50 Mo)',
                           'code': 'FILE_TOO_LARGE'}), 413

        filename = file.filename or 'document.txt'

        try:
            result = tools_svc.analyze_document(file_data, filename)
            return jsonify(result), 200 if result.get('success') else 422
        except Exception as e:
            log.error(f"Document analyze error: {e}")
            return jsonify({'error': str(e), 'code': 'ANALYZE_ERROR'}), 500

    # ═══════════════════════════════════════════════════════════════════
    # 2. 🌐 TRADUCTION
    # ═══════════════════════════════════════════════════════════════════
    @app.route('/api/tools/translate', methods=['POST', 'OPTIONS'])
    def api_translate():
        """Traduit un texte dans une langue cible."""
        if request.method == 'OPTIONS':
            return '', 200

        data = request.get_json(silent=True) or {}
        text = (data.get('text') or '').strip()
        target = (data.get('target') or 'en').strip().lower()
        source = (data.get('source') or '').strip().lower() or None

        if not text:
            return jsonify({'error': 'Texte requis', 'code': 'EMPTY_TEXT'}), 400

        if len(text) > 10000:
            return jsonify({'error': 'Texte trop long (max 10 000 caractères)',
                           'code': 'TEXT_TOO_LONG'}), 413

        try:
            result = tools_svc.translate(text, target, source)
            return jsonify(result), 200 if result.get('success') else 422
        except Exception as e:
            log.error(f"Translate error: {e}")
            return jsonify({'error': str(e), 'code': 'TRANSLATE_ERROR'}), 500

    # ═══════════════════════════════════════════════════════════════════
    # 3. 💡 IDÉES
    # ═══════════════════════════════════════════════════════════════════
    @app.route('/api/tools/ideas', methods=['GET', 'POST', 'OPTIONS'])
    def api_ideas():
        """Liste ou crée des idées."""
        if request.method == 'OPTIONS':
            return '', 200

        if request.method == 'GET':
            # Paramètres de filtrage
            search = request.args.get('search', '')
            tag = request.args.get('tag', '')
            page = max(1, int(request.args.get('page', 1)))
            per_page = min(50, max(1, int(request.args.get('per_page', 20))))

            try:
                result = tools_svc.list_ideas(search=search, tag=tag,
                                               page=page, per_page=per_page)
                return jsonify(result), 200
            except Exception as e:
                log.error(f"Ideas list error: {e}")
                return jsonify({'error': str(e), 'code': 'LIST_ERROR'}), 500

        # POST — créer une idée
        data = request.get_json(silent=True) or {}
        title = (data.get('title') or '').strip()
        body = (data.get('body') or '').strip()
        tags = data.get('tags', [])

        if not title:
            return jsonify({'error': 'Le titre est requis', 'code': 'MISSING_TITLE'}), 400

        try:
            result = tools_svc.create_idea(title, body, tags)
            return jsonify(result), 201 if result.get('success') else 422
        except Exception as e:
            log.error(f"Idea create error: {e}")
            return jsonify({'error': str(e), 'code': 'CREATE_ERROR'}), 500

    @app.route('/api/tools/ideas/<idea_id>', methods=['GET', 'PUT', 'DELETE', 'OPTIONS'])
    def api_idea_detail(idea_id):
        """Détail, modification ou suppression d'une idée."""
        if request.method == 'OPTIONS':
            return '', 200

        if request.method == 'GET':
            try:
                result = tools_svc.get_idea(idea_id)
                status = 200 if result.get('success') else 404
                return jsonify(result), status
            except Exception as e:
                log.error(f"Idea get error: {e}")
                return jsonify({'error': str(e), 'code': 'GET_ERROR'}), 500

        if request.method == 'PUT':
            data = request.get_json(silent=True) or {}
            title = data.get('title')
            body = data.get('body')
            tags = data.get('tags')

            try:
                result = tools_svc.update_idea(idea_id, title, body, tags)
                return jsonify(result), 200 if result.get('success') else 404
            except Exception as e:
                log.error(f"Idea update error: {e}")
                return jsonify({'error': str(e), 'code': 'UPDATE_ERROR'}), 500

        if request.method == 'DELETE':
            try:
                result = tools_svc.delete_idea(idea_id)
                return jsonify(result), 200 if result.get('success') else 404
            except Exception as e:
                log.error(f"Idea delete error: {e}")
                return jsonify({'error': str(e), 'code': 'DELETE_ERROR'}), 500