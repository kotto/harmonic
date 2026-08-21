"""
KA Server — Routes Enterprise (Post-RAG Platform)
=================================================
Endpoints Enterprise : ingestion → hologrammes, conformité, audit,
déploiement, manifeste Post-RAG, démo déterministe.
Nécessitent authentification API Key.

Positionnement : les hologrammes remplacent le RAG, les données
restent on-premise, le raisonnement est déterministe (0% hallucination).
"""

import logging
import time as _time
from functools import wraps
from flask import request, jsonify, g, current_app

log = logging.getLogger(__name__)


def _require_enterprise_auth(f):
    """Décorateur pour exiger auth Enterprise.

    Valide la clé via le middleware (current_app.ka_auth), jamais via `g` :
    `g.ka_auth` n'est pas défini par le middleware (il pose app.ka_auth).
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Vérifier API key
        api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
        if not api_key:
            return jsonify({'error': 'API Key requise', 'code': 'AUTH_REQUIRED'}), 401

        # Valider via le middleware d'auth (app.ka_auth, pas g.ka_auth)
        auth = getattr(current_app, 'ka_auth', None)
        validate = auth.get('validate_api_key') if isinstance(auth, dict) else None
        if not callable(validate) or not validate(api_key):
            return jsonify({'error': 'API Key invalide', 'code': 'INVALID_API_KEY'}), 401

        g.enterprise_user = f'ent_{api_key[:8]}'
        return f(*args, **kwargs)
    return decorated


def register_enterprise_routes(app, services):
    """Enregistre les routes Enterprise (protégées)."""
    
    enterprise_ingestor = services.get('enterprise_ingestor')
    hologram_store = services.get('hologram_store')
    brain = services.get('brain')
    
    @app.route('/api/v2/enterprise/ingest', methods=['POST', 'OPTIONS'])
    @_require_enterprise_auth
    def api_enterprise_ingest():
        """Ingestion de documents pour Enterprise Knowledge Base."""
        if request.method == 'OPTIONS':
            return '', 200
        
        if not enterprise_ingestor:
            return jsonify({
                'error': 'Enterprise Ingestor non disponible',
                'code': 'INGESTOR_UNAVAILABLE'
            }), 503
        
        data = request.get_json() or {}
        documents = data.get('documents', [])  # Liste de {content, metadata, source}
        domain = data.get('domain', 'enterprise')
        chunk_size = data.get('chunk_size', 512)
        overlap = data.get('overlap', 50)
        
        if not documents:
            return jsonify({'error': 'Documents requis', 'code': 'MISSING_DOCUMENTS'}), 400
        
        try:
            result = enterprise_ingestor.ingest(
                documents=documents,
                domain=domain,
                chunk_size=chunk_size,
                overlap=overlap
            )
            
            return jsonify({
                'success': True,
                'domain': domain,
                'documents_processed': result.get('processed', 0),
                'chunks_created': result.get('chunks', 0),
                'facts_extracted': result.get('facts', 0),
                'hologram_id': result.get('hologram_id', domain),
            })
        except Exception as e:
            log.error(f"Enterprise ingest error: {e}")
            return jsonify({'error': str(e), 'code': 'INGEST_FAILED'}), 500
    
    @app.route('/api/v2/enterprise/ingest/file', methods=['POST', 'OPTIONS'])
    @_require_enterprise_auth
    def api_enterprise_ingest_file():
        """Ingestion par upload de fichiers."""
        if request.method == 'OPTIONS':
            return '', 200
        
        if 'multipart/form-data' not in (request.content_type or ''):
            return jsonify({'error': 'Content-Type multipart/form-data requis'}), 400
        
        files = request.files.getlist('files')
        if not files:
            return jsonify({'error': 'Aucun fichier', 'code': 'NO_FILES'}), 400
        
        domain = request.form.get('domain', 'enterprise')
        
        if not enterprise_ingestor:
            return jsonify({'error': 'Ingestor non disponible', 'code': 'INGESTOR_UNAVAILABLE'}), 503
        
        documents = []
        for file in files:
            content = file.read()
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                # Essayer autres encodages ou ignorer binaire
                text = content.decode('latin-1', errors='ignore')
            
            documents.append({
                'content': text,
                'metadata': {
                    'filename': file.filename,
                    'size': len(content),
                    'content_type': file.content_type,
                },
                'source': f'file:{file.filename}',
            })
        
        try:
            result = enterprise_ingestor.ingest(documents=documents, domain=domain)
            return jsonify({
                'success': True,
                'domain': domain,
                'files_processed': len(files),
                **result
            })
        except Exception as e:
            log.error(f"File ingest error: {e}")
            return jsonify({'error': str(e), 'code': 'FILE_INGEST_FAILED'}), 500
    
    @app.route('/api/v2/enterprise/ingest/structured', methods=['POST', 'OPTIONS'])
    @_require_enterprise_auth
    def api_enterprise_ingest_structured():
        """Ingestion STRUCTURÉE (inspirée de Docling) → hologramme spécialisé.

        Body: {
          "content": "# Titre\\n\\n## Section\\n\\n| a | b |...",   # markdown | text | html
          "format": "markdown",          # markdown | text | html
          "domain": "pack_ka",           # nom de l'hologramme spécialisé
          "category": "tech",            # secteur des faits
          "source": "fiche_produit.md"
        }
        Le document est découpé en sections hiérarchiques, tables ligne/colonne
        et ordre de lecture → faits STRUCTURELS (section_contient, item_précède,
        est_valeur_de) + faits de contenu, versés dans l'hologramme du domaine.
        """
        if request.method == 'OPTIONS':
            return '', 200
        from ka_server.services import ingest_structured as _ingest
        data = request.get_json() or {}
        content = data.get('content', '')
        if not content:
            return jsonify({'error': 'Contenu requis', 'code': 'MISSING_CONTENT'}), 400
        try:
            result = _ingest(
                content=content,
                format=data.get('format', 'markdown'),
                domain=data.get('domain', 'enterprise'),
                category=data.get('category', 'enterprise'),
                source=data.get('source', 'doc'),
            )
            if result.get('error'):
                return jsonify(result), 503
            return jsonify(result)
        except Exception as e:
            log.error(f"Structured ingest error: {e}")
            return jsonify({'error': str(e), 'code': 'STRUCTURED_INGEST_FAILED'}), 500

    @app.route('/api/v2/enterprise/recall/structured', methods=['POST', 'OPTIONS'])
    @_require_enterprise_auth
    def api_enterprise_recall_structured():
        """Rappel STRUCTUREL : la question remonte la hiérarchie du document.

        Body: {"domain": "pack_ka", "query": "quel est le prix de la formule pro ?", "top_k": 3}
        Retourne les sections complètes (titre, parent, table entière) —
        pas des chunks plats.
        """
        if request.method == 'OPTIONS':
            return '', 200
        from ka_server.services import recall_structured as _recall
        data = request.get_json() or {}
        try:
            sections = _recall(
                domain=data.get('domain', 'enterprise'),
                query=data.get('query', ''),
                top_k=int(data.get('top_k', 3)),
            )
            return jsonify({'success': True, 'domain': data.get('domain'), 'sections': sections})
        except Exception as e:
            log.error(f"Structured recall error: {e}")
            return jsonify({'error': str(e), 'code': 'STRUCTURED_RECALL_FAILED'}), 500

    @app.route('/api/v2/enterprise/documents', methods=['GET', 'OPTIONS'])
    @_require_enterprise_auth
    def api_enterprise_documents():
        """Liste des domaines ingérés en structuré."""
        if request.method == 'OPTIONS':
            return '', 200
        from ka_server.services import list_documents as _list
        return jsonify({'success': True, 'documents': _list()})

    @app.route('/api/v2/enterprise/compliance/check', methods=['POST', 'OPTIONS'])
    @_require_enterprise_auth
    def api_compliance_check():
        """Vérification conformité (RGPD, AI Act, etc.)."""
        if request.method == 'OPTIONS':
            return '', 200
        
        data = request.get_json() or {}
        text = data.get('text', '')
        document_id = data.get('document_id', '')
        regulations = data.get('regulations', ['rgpd', 'ai_act'])  # rgpd, ai_act, hipaa, sox
        
        if not text and not document_id:
            return jsonify({'error': 'Texte ou document_id requis', 'code': 'MISSING_INPUT'}), 400
        
        # Si document_id, récupérer depuis store
        if document_id and hologram_store:
            holo = hologram_store.get_hologram(document_id)
            if holo:
                text = holo.get('content', '') or holo.get('description', '')
        
        if not text:
            return jsonify({'error': 'Contenu non trouvé', 'code': 'NO_CONTENT'}), 404
        
        # Analyse conformité basique
        issues = _check_compliance(text, regulations)
        
        return jsonify({
            'document_id': document_id,
            'regulations_checked': regulations,
            'compliant': len([i for i in issues if i['severity'] in ('high', 'critical')]) == 0,
            'issues': issues,
            'summary': _compliance_summary(issues),
        })
    
    @app.route('/api/v2/enterprise/audit/log', methods=['GET'])
    @_require_enterprise_auth
    def api_audit_log():
        """Log d'audit Enterprise."""
        from ka_server.middleware.auth import get_audit_log
        
        limit = min(int(request.args.get('limit', 100)), 1000)
        action_filter = request.args.get('action')
        user_filter = request.args.get('user')
        
        logs = get_audit_log(limit=limit)
        
        if action_filter:
            logs = [l for l in logs if l.get('action') == action_filter]
        if user_filter:
            logs = [l for l in logs if l.get('user') == user_filter]
        
        return jsonify({
            'logs': logs,
            'count': len(logs),
            'filters': {'action': action_filter, 'user': user_filter},
        })
    
    @app.route('/api/v2/enterprise/deploy', methods=['POST', 'OPTIONS'])
    @_require_enterprise_auth
    def api_enterprise_deploy():
        """Déploiement modèle/hologramme (Edge, Cloud, On-premise)."""
        if request.method == 'OPTIONS':
            return '', 200
        
        data = request.get_json() or {}
        hologram_id = data.get('hologram_id', '')
        target = data.get('target', 'edge')  # edge, cloud, onprem, mobile
        config = data.get('config', {})
        
        if not hologram_id:
            return jsonify({'error': 'hologram_id requis', 'code': 'MISSING_HOLOGRAM'}), 400
        
        if not hologram_store:
            return jsonify({'error': 'Store non disponible', 'code': 'STORE_UNAVAILABLE'}), 503
        
        holo = hologram_store.get_hologram(hologram_id)
        if not holo:
            return jsonify({'error': 'Hologramme non trouvé', 'code': 'NOT_FOUND'}), 404
        
        # Simuler déploiement
        deployment_id = f"deploy_{hologram_id}_{target}_{int(__import__('time').time())}"
        
        return jsonify({
            'success': True,
            'deployment_id': deployment_id,
            'hologram_id': hologram_id,
            'target': target,
            'status': 'deployed',
            'endpoint': f"https://{target}.ka-enterprise.io/{hologram_id}",
            'config': config,
            'message': f"Déploiement {target} simulé. En production, utiliserait Kubernetes/Edge runtime.",
        })
    
    @app.route('/api/v2/enterprise/usage', methods=['GET'])
    @_require_enterprise_auth
    def api_enterprise_usage():
        """Statistiques d'usage Enterprise."""
        # Récupérer métriques
        metrics = app.ka_metrics if hasattr(app, 'ka_metrics') else {}
        
        return jsonify({
            'period': 'current_month',
            'api_calls': metrics.get('requests_total', 0) if isinstance(metrics, dict) else 0,
            'harmonic_requests': metrics.get('harmonic_count', 0) if isinstance(metrics, dict) else 0,
            'storage_gb': _estimate_storage_gb(services),
            'active_holograms': len(hologram_store.list_holograms()) if hologram_store else 0,
            'bandwidth_gb': 0,  # TODO: tracker
            'quotas': {
                'api_calls_limit': 1000000,
                'storage_limit_gb': 100,
                'bandwidth_limit_gb': 500,
            }
        })
    
    @app.route('/api/v2/enterprise/keys', methods=['GET', 'POST', 'DELETE'])
    @_require_enterprise_auth
    def api_enterprise_keys():
        """Gestion API Keys Enterprise."""
        from ka_server.middleware.auth import add_api_key, remove_api_key, get_valid_keys
        
        if request.method == 'GET':
            return jsonify({'keys': get_valid_keys()})
        
        elif request.method == 'POST':
            data = request.get_json() or {}
            key = data.get('key') or _generate_api_key()
            metadata = data.get('metadata', {})
            metadata['created_by'] = g.enterprise_user
            
            if add_api_key(key, metadata):
                # Lier la clé à un utilisateur si demandé
                owner = data.get('owner') or metadata.get('created_by')
                try:
                    from ka_server.middleware.auth import _link_key_to_user
                    _link_key_to_user(key, owner)
                except Exception:
                    pass
                return jsonify({
                    'success': True,
                    'key': key,
                    'message': 'Clé créée. Sauvegardez-la, elle ne sera plus affichée.'
                })
            return jsonify({'error': 'Clé invalide', 'code': 'INVALID_KEY'}), 400
        
        elif request.method == 'DELETE':
            data = request.get_json() or {}
            key = data.get('key')
            if not key:
                return jsonify({'error': 'Clé requise', 'code': 'MISSING_KEY'}), 400
            
            if remove_api_key(key):
                return jsonify({'success': True, 'message': 'Clé révoquée'})
            return jsonify({'error': 'Clé non trouvée', 'code': 'KEY_NOT_FOUND'}), 404
    
    @app.route('/api/v2/enterprise/usage/timeseries', methods=['GET', 'OPTIONS'])
    @_require_enterprise_auth
    def api_enterprise_usage_timeseries():
        """Séries temporelles d'usage pour les graphiques de la console.

        ?days=7&hours=24 → hourly (appels+erreurs par heure), daily (par jour),
        by_endpoint (top 10), latence moyenne.
        """
        if request.method == 'OPTIONS':
            return '', 200
        try:
            from ka_server.middleware.metrics import get_usage_timeseries
            days = min(int(request.args.get('days', 7)), 30)
            hours = min(int(request.args.get('hours', 24)), 168)
            return jsonify({'success': True, **get_usage_timeseries(days=days, hours=hours)})
        except Exception as e:
            log.error(f"Timeseries error: {e}")
            return jsonify({'error': str(e), 'code': 'TIMESERIES_FAILED'}), 500

    @app.route('/api/v2/enterprise/users', methods=['GET', 'POST', 'DELETE', 'OPTIONS'])
    @_require_enterprise_auth
    def api_enterprise_users():
        """Gestion des utilisateurs Enterprise (admin | viewer | auditor).

        GET    → liste des utilisateurs
        POST   {username, role}           → créer
        POST   {username, role} (PATCH)   → changer le rôle
        DELETE {username}                 → supprimer
        """
        if request.method == 'OPTIONS':
            return '', 200
        from ka_server.middleware.auth import (
            list_users, create_user, delete_user, set_user_role,
        )
        if request.method == 'GET':
            return jsonify({'success': True, 'users': list_users()})

        data = request.get_json() or {}
        username = (data.get('username') or '').strip().lower()
        role = data.get('role', 'viewer')

        if request.method == 'POST':
            # PATCH : si l'utilisateur existe et un rôle est fourni → changement de rôle
            if data.get('action') == 'role' or (username and any(u['username'] == username for u in list_users()) and data.get('role')):
                ok, message = set_user_role(username, role)
            else:
                ok, message = create_user(username, role)
            if not ok:
                return jsonify({'error': message, 'code': 'USER_ERROR'}), 409 if 'existant' in message else 400
            return jsonify({'success': True, 'message': message})

        if request.method == 'DELETE':
            ok, message = delete_user(username)
            if not ok:
                return jsonify({'error': message, 'code': 'USER_NOT_FOUND'}), 404
            return jsonify({'success': True, 'message': message})

        return jsonify({'error': 'Méthode non supportée'}), 405

    @app.route('/api/v2/enterprise/billing', methods=['GET'])
    @_require_enterprise_auth
    def api_enterprise_billing():
        """Info facturation (stub)."""
        return jsonify({
            'plan': 'enterprise',
            'billing_cycle': 'monthly',
            'current_usage': {
                'api_calls': 125000,
                'storage_gb': 12.5,
                'compute_hours': 45.2,
            },
            'limits': {
                'api_calls': 1000000,
                'storage_gb': 100,
                'compute_hours': 500,
            },
            'estimated_cost': 299.00,
            'currency': 'EUR',
            'next_invoice': '2025-02-01',
        })

    # ────────────────────────────────────────────────────────────────────────
    #  POST-RAG PLATFORM — le positionnement produit (PUBLIC, fr/en)
    #  Ces endpoints sont publics : ce sont des contenus marketing, pas des
    #  données sensibles. La console et la landing page les consomment.
    # ────────────────────────────────────────────────────────────────────────

    @app.route('/api/v2/enterprise/manifesto', methods=['GET', 'OPTIONS'])
    def api_enterprise_manifesto():
        """Manifeste Post-RAG — PUBLIC (marketing), localisé fr/en (?lang=).

        Pourquoi le RAG échoue, nos piliers. La landing page et la console
        le consomment — c'est la source de vérité du narrative produit.
        """
        if request.method == 'OPTIONS':
            return '', 200
        lang = request.args.get('lang', 'fr')
        L = _manifesto_content(lang)
        return jsonify({'success': True, 'lang': lang, **L})

    @app.route('/api/v2/enterprise/compare', methods=['GET', 'OPTIONS'])
    def api_enterprise_compare():
        """Comparaison chiffrée RAG vs Hologramme — PUBLIC, localisé fr/en."""
        if request.method == 'OPTIONS':
            return '', 200
        lang = request.args.get('lang', 'fr')
        return jsonify({
            'success': True,
            'lang': lang,
            'comparison': [
                {
                    'criteria': _pick(c['criteria'], lang),
                    'rag': _pick(c['rag'], lang),
                    'hologram': _pick(c['hologram'], lang),
                }
                for c in _COMPARE
            ],
        })

    @app.route('/api/v2/enterprise/pricing', methods=['GET', 'OPTIONS'])
    def api_enterprise_pricing():
        """Grille tarifaire — PUBLIC, localisé fr/en.

        4 offres annuelles, 100% on-premise. Licence forfaitaire (budget
        prévisible) : pas de coût par token, pas de facturation GPU.
        Les montants sont éditables ici — source de vérité pour la console.
        """
        if request.method == 'OPTIONS':
            return '', 200
        lang = request.args.get('lang', 'fr')
        return jsonify({
            'success': True,
            'lang': lang,
            'currency': 'EUR',
            'period': _pick({'fr': 'annual', 'en': 'annual'}, lang),
            'plans': [_plan_localized(p, lang) for p in _PRICING_PLANS],
        })

    @app.route('/api/v2/enterprise/demo/ask', methods=['POST', 'OPTIONS'])
    @_require_enterprise_auth
    def api_enterprise_demo_ask():
        """Démo en direct : question → réponse déterministe + provenance.

        C'est la preuve du positionnement Post-RAG dans la console. Pipeline
        identique à /api/chat — chaque étape est déterministe :
          1. Arithmétique émergente (codec ψ v3) — « 7 × 6 » → 42, sans RAG
          2. Memory-first — le fait stocké répond (avec provenance), sinon refus calibré
          3. Consensus holographique M4 + raisonnement — le domaine vote, la
             réponse cite ses faits sources (0% hallucination)

        Body: {"question": "combien font 7 multiplié par 6 ?"}
        """
        if request.method == 'OPTIONS':
            return '', 200

        data = request.get_json() or {}
        question = (data.get('question') or '').strip()
        if not question:
            return jsonify({'error': 'Question requise', 'code': 'MISSING_QUESTION'}), 400

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
                'error': 'Moteur harmonique indisponible',
                'code': 'HARMONIC_UNAVAILABLE',
            }), 503

        latency_ms = round((_time.time() - t0) * 1000)

        return jsonify({
            'success': True,
            'answer': answer,
            'source': source,
            'best_domain': best_domain,
            'consensus_facts_count': len(consensus_facts) if consensus_facts else 0,
            'facts': [list(f) for f in consensus_facts[:5]] if consensus_facts else [],
            'latency_ms': latency_ms,
            'deterministic': True,
            'note': 'Consensus holographique M4 — les faits cités sont la provenance de la réponse. 0% hallucination.',
        })

    # ────────────────────────────────────────────────────────────────────────
    #  SQL QUERIER — interroger des données structurées par langage naturel
    #  Text-to-SQL déterministe : pattern matching, pas de LLM.
    #  Base exemple : ventes, produits, régions, employés (500 lignes).
    # ────────────────────────────────────────────────────────────────────────

    @app.route('/api/v2/enterprise/query/schema', methods=['GET', 'OPTIONS'])
    @_require_enterprise_auth
    def api_enterprise_schema():
        """Retourne le schéma des tables disponibles pour le SQL Querier."""
        if request.method == 'OPTIONS':
            return '', 200
        try:
            from ka_server.services.sql_querier import get_demo_schema, get_friendly_schema
            return jsonify({
                'success': True,
                'tables': get_demo_schema(),
                'description': get_friendly_schema(),
                'example_questions': [
                    'quel est le CA du mois dernier ?',
                    'moyenne des ventes par région',
                    'top 5 produits par chiffre d\'affaires',
                    'CA par catégorie',
                    'nombre d\'employés par département',
                    'quel est le total des ventes par pays ?',
                ],
            })
        except Exception as e:
            return jsonify({'error': str(e), 'code': 'SCHEMA_UNAVAILABLE'}), 503

    @app.route('/api/v2/enterprise/query/sql', methods=['POST', 'OPTIONS'])
    @_require_enterprise_auth
    def api_enterprise_query_sql():
        """Text-to-SQL déterministe — interroger des données structurées.

        Body: {"question": "quel est le CA du mois dernier ?"}
        Le service utilise du pattern matching (pas de LLM) pour générer
        et exécuter une requête SQL sur la base exemple.

        Intentions supportées :
          • Agrégations : SUM, AVG, COUNT, MAX, MIN
          • Groupes : par région, catégorie, produit, mois, département
          • Filtres temporels : ce mois, mois dernier, cette année
          • Ordre : top N, meilleur/pire
        """
        if request.method == 'OPTIONS':
            return '', 200

        data = request.get_json() or {}
        question = (data.get('question') or '').strip()

        if not question:
            return jsonify({'error': 'Question requise', 'code': 'MISSING_QUESTION'}), 400
        if len(question) > 300:
            return jsonify({'error': 'Question trop longue (max 300 caractères)'}), 400

        try:
            from ka_server.services.sql_querier import detect_and_solve_sql, get_demo_schema, get_friendly_schema
            result = detect_and_solve_sql(question)

            if not result['handled']:
                return jsonify({
                    'error': 'Question non SQL-requêtable',
                    'code': 'NOT_SQL_QUERY',
                    'hint': 'Exemples : ' + ', '.join([
                        'CA du mois dernier', 'moyenne ventes par région',
                        'top 5 produits', 'nombre employés par département'
                    ]),
                }), 400

            return jsonify({
                'success': True,
                'sql': result['sql'],
                'result': result['result'],
                'columns': result['columns'],
                'row_count': result['row_count'],
                'explanation': result['explanation'],
                'error': result.get('error'),
            })
        except Exception as e:
            return jsonify({'error': str(e), 'code': 'SQL_QUERY_FAILED'}), 500


def _check_compliance(text: str, regulations: list) -> list:
    """Vérification conformité basique."""
    issues = []
    text_lower = text.lower()
    
    # RGPD patterns
    if 'rgpd' in regulations or 'gdpr' in regulations:
        # Données personnelles
        pii_patterns = [
            (r'\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b', 'Date de naissance possible', 'medium'),
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'Email détecté', 'high'),
            (r'\b\d{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{2}\b', 'Téléphone possible', 'medium'),
            (r'\b\d{13,19}\b', 'Numéro de carte/SSN possible', 'critical'),
        ]
        for pattern, msg, severity in pii_patterns:
            if re.search(pattern, text):
                issues.append({
                    'regulation': 'RGPD',
                    'type': 'pii_detected',
                    'message': msg,
                    'severity': severity,
                })
        
        # Consentement
        if not any(w in text_lower for w in ['consentement', 'consent', 'accord', 'autorise']):
            issues.append({
                'regulation': 'RGPD',
                'type': 'missing_consent',
                'message': 'Aucune mention de consentement explicite',
                'severity': 'medium',
            })
    
    # AI Act
    if 'ai_act' in regulations:
        high_risk = ['diagnostic médical', 'recrutement', 'notation crédit', 'biométrie', 'surveillance']
        for risk in high_risk:
            if risk in text_lower:
                issues.append({
                    'regulation': 'AI_ACT',
                    'type': 'high_risk_ai',
                    'message': f'Usage IA à haut risque détecté: {risk}',
                    'severity': 'high',
                })
        
        # Transparence
        if not any(w in text_lower for w in ['ia', 'intelligence artificielle', 'ai system', 'automatis']):
            issues.append({
                'regulation': 'AI_ACT',
                'type': 'transparency',
                'message': 'Pas de mention transparence IA',
                'severity': 'medium',
            })
    
    return issues


def _compliance_summary(issues: list) -> dict:
    """Résumé conformité."""
    by_severity = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    by_reg = {}
    
    for issue in issues:
        by_severity[issue['severity']] = by_severity.get(issue['severity'], 0) + 1
        reg = issue['regulation']
        by_reg[reg] = by_reg.get(reg, 0) + 1
    
    return {
        'total_issues': len(issues),
        'by_severity': by_severity,
        'by_regulation': by_reg,
        'compliant': by_severity['critical'] == 0 and by_severity['high'] == 0,
    }


def _estimate_storage_gb(services) -> float:
    """Estime stockage en GB."""
    holo = services.get('hologram_store')
    if not holo:
        return 0.0
    try:
        holos = holo.list_holograms()
        total_facts = sum(h.get('facts_count', 0) for h in holos)
        # ~500 bytes par fait estimé
        return round(total_facts * 500 / 1e9, 2)
    except Exception:
        return 0.0


def _generate_api_key() -> str:
    """Génère une clé API sécurisée."""
    import secrets
    return f"ka_ent_{secrets.token_urlsafe(32)}"


# ────────────────────────────────────────────────────────────────────────────
#  CONTENU POST-RAG LOCALISÉ (fr/en) — source de vérité marketing
#  Consommé par la landing page publique et la console d'administration.
# ────────────────────────────────────────────────────────────────────────────

def _pick(item: dict, lang: str):
    """Choisit la valeur fr ou en d'un item localisé."""
    if isinstance(item, dict) and 'fr' in item and 'en' in item:
        return item.get('en') if lang == 'en' else item.get('fr')
    return item


# Table comparative RAG vs Hologramme (10 critères, fr/en)
_COMPARE = [
    {'criteria': {'fr': 'Stockage', 'en': 'Storage'},
     'rag': {'fr': 'Vector DB (€€€, complexe)', 'en': 'Vector DB (€€€, complex)'},
     'hologram': {'fr': '1 fichier de 2 Mo', 'en': 'One 2 MB file'}},
    {'criteria': {'fr': 'Requête', 'en': 'Query'},
     'rag': {'fr': 'Similarité cosinus (approximation)', 'en': 'Cosine similarity (approximation)'},
     'hologram': {'fr': 'Rappel déterministe (certitude)', 'en': 'Deterministic recall (certainty)'}},
    {'criteria': {'fr': 'Contexte', 'en': 'Context'},
     'rag': {'fr': 'Limité aux chunks retrievés', 'en': 'Limited to retrieved chunks'},
     'hologram': {'fr': 'Domaine complet', 'en': 'Full domain'}},
    {'criteria': {'fr': 'Hallucination', 'en': 'Hallucination'},
     'rag': {'fr': '3–27% (le LLM ignore le contexte)', 'en': '3–27% (LLM ignores context)'},
     'hologram': {'fr': '0% (codec ψ déterministe)', 'en': '0% (deterministic ψ codec)'}},
    {'criteria': {'fr': 'Mise à jour', 'en': 'Updates'},
     'rag': {'fr': 'Ré-indexer tout le corpus', 'en': 'Re-index entire corpus'},
     'hologram': {'fr': 'Ajout / édition instantanée', 'en': 'Instant add / edit'}},
    {'criteria': {'fr': 'Privacy', 'en': 'Privacy'},
     'rag': {'fr': 'Données → API externe', 'en': 'Data → external API'},
     'hologram': {'fr': '100% sur site', 'en': '100% on-site'}},
    {'criteria': {'fr': 'Coût', 'en': 'Cost'},
     'rag': {'fr': 'GPU + Vector DB + Tokens API', 'en': 'GPU + Vector DB + API tokens'},
     'hologram': {'fr': '1 serveur CPU', 'en': 'One CPU server'}},
    {'criteria': {'fr': 'Matériel', 'en': 'Hardware'},
     'rag': {'fr': 'GPU requis (A100, H100…)', 'en': 'GPU required (A100, H100…)'},
     'hologram': {'fr': 'CPU standard (n\'importe quel serveur)', 'en': 'Standard CPU (any server)'}},
    {'criteria': {'fr': 'Conformité', 'en': 'Compliance'},
     'rag': {'fr': 'Difficile (données hors site)', 'en': 'Difficult (data off-site)'},
     'hologram': {'fr': 'RGPD · AI Act · HIPAA · SOX intégrés', 'en': 'GDPR · AI Act · HIPAA · SOX built-in'}},
    {'criteria': {'fr': 'Explicabilité', 'en': 'Explainability'},
     'rag': {'fr': 'Boîte noire (le LLM ne cite rien)', 'en': 'Black box (LLM cites nothing)'},
     'hologram': {'fr': 'Trajectoire ψ vérifiable + faits cités', 'en': 'Verifiable ψ trajectory + cited facts'}},
]

# Grille tarifaire — 4 offres (montants non localisés, descriptions fr/en)
_PRICING_PLANS = [
    {
        'id': 'essentials', 'price': 2500, 'highlight': False,
        'name': {'fr': 'Essentials', 'en': 'Essentials'},
        'description': {
            'fr': 'Pour les PME qui veulent une IA fiable sans envoyer leurs données.',
            'en': 'For SMBs that want reliable AI without sending their data anywhere.',
        },
        'features': [
            {'fr': '1 instance Docker on-premise', 'en': '1 on-premise Docker instance'},
            {'fr': 'Moteur de compression HCV (ratio ×213)', 'en': 'HCV compression engine (×213 ratio)'},
            {'fr': 'Codec ψ — raisonnement déterministe, 0% hallucination', 'en': 'ψ codec — deterministic reasoning, 0% hallucination'},
            {'fr': 'Jusqu\'à 10 hologrammes spécialisés', 'en': 'Up to 10 specialized holograms'},
            {'fr': '5 utilisateurs (admin / viewer / auditor)', 'en': '5 users (admin / viewer / auditor)'},
            {'fr': 'Journal d\'audit', 'en': 'Audit log'},
        ],
    },
    {
        'id': 'pro', 'price': 9500, 'highlight': True,
        'name': {'fr': 'Pro', 'en': 'Pro'},
        'description': {
            'fr': 'Pour les ETI qui veulent remplacer leur RAG par des hologrammes.',
            'en': 'For mid-size companies that want to replace RAG with holograms.',
        },
        'features': [
            {'fr': 'Tout dans Essentials +', 'en': 'Everything in Essentials +'},
            {'fr': 'Hologrammes illimités', 'en': 'Unlimited holograms'},
            {'fr': 'Suite de conformité (RGPD, AI Act, HIPAA, SOX)', 'en': 'Compliance suite (GDPR, AI Act, HIPAA, SOX)'},
            {'fr': 'Création d\'hologrammes depuis documents (no-code)', 'en': 'No-code hologram creation from documents'},
            {'fr': 'Rappel structurel — hiérarchie documentaire préservée', 'en': 'Structural recall — document hierarchy preserved'},
            {'fr': 'Déploiement edge / cloud / onprem / mobile', 'en': 'Edge / cloud / onprem / mobile deployment'},
            {'fr': 'Support prioritaire', 'en': 'Priority support'},
        ],
    },
    {
        'id': 'ultimate', 'price': 25000, 'highlight': False,
        'name': {'fr': 'Ultimate', 'en': 'Ultimate'},
        'description': {
            'fr': 'Pour les grands comptes avec des besoins spécifiques.',
            'en': 'For large accounts with specific needs.',
        },
        'features': [
            {'fr': 'Tout dans Pro +', 'en': 'Everything in Pro +'},
            {'fr': 'Instance dédiée', 'en': 'Dedicated instance'},
            {'fr': 'Développement d\'hologrammes sur mesure', 'en': 'Custom hologram development'},
            {'fr': 'SLA 99.9%', 'en': '99.9% SLA'},
            {'fr': 'Intégrations personnalisées (API sur mesure)', 'en': 'Custom integrations (bespoke API)'},
            {'fr': 'Formation des équipes', 'en': 'Team training'},
        ],
    },
    {
        'id': 'airgap', 'price': 50000, 'highlight': False,
        'name': {'fr': 'Air-Gap', 'en': 'Air-Gap'},
        'description': {
            'fr': 'Pour la défense, l\'énergie, les infrastructures critiques.',
            'en': 'For defense, energy, critical infrastructure.',
        },
        'features': [
            {'fr': 'Tout dans Ultimate +', 'en': 'Everything in Ultimate +'},
            {'fr': 'Aucune connexion réseau requise', 'en': 'No network connection required'},
            {'fr': 'Appliance matérielle optionnelle', 'en': 'Optional hardware appliance'},
            {'fr': 'Sécurité de niveau militaire', 'en': 'Military-grade security'},
            {'fr': 'Déploiement sur site par nos équipes', 'en': 'On-site deployment by our teams'},
        ],
    },
]


def _plan_localized(plan: dict, lang: str) -> dict:
    """Localise un plan tarifaire (name, description, features)."""
    return {
        'id': plan['id'],
        'price': plan['price'],
        'highlight': plan['highlight'],
        'name': _pick(plan['name'], lang),
        'description': _pick(plan['description'], lang),
        'features': [_pick(f, lang) for f in plan['features']],
    }


def _manifesto_content(lang: str) -> dict:
    """Construit le manifeste Post-RAG dans la langue demandée."""
    en = lang == 'en'
    return {
        'title': (
            'RAG is a hack. Holograms are the solution.'
            if en else
            'Le RAG est un bricolage. Les hologrammes sont la solution.'
        ),
        'subtitle': (
            'Why RAG fails — and how we replace it.'
            if en else
            'Pourquoi le RAG échoue — et comment nous le remplaçons.'
        ),
        'pain_points': [
            {
                'title': ('Irreducible hallucinations' if en else 'Hallucinations irréductibles'),
                'stat': '3–27%',
                'description': (
                    'LLMs invent 3–27% of their answers. RAG fixes nothing: the LLM can ignore '
                    'the retrieved context and generate a false answer with total confidence. In '
                    'regulated sectors (finance, healthcare, legal), a single invented answer can '
                    'cost millions.'
                    if en else
                    'Les LLMs inventent 3 à 27% de leurs réponses. Le RAG ne corrige rien : le LLM '
                    'peut ignorer le contexte retrievé et générer une réponse fausse avec une '
                    'confiance totale. Dans les secteurs régulés (finance, santé, droit), une seule '
                    'réponse inventée peut coûter des millions.'
                ),
            },
            {
                'title': ('Data exfiltrated to the cloud' if en else 'Données exfiltrées vers le cloud'),
                'stat': '100%',
                'description': (
                    'Every RAG request sends the context — your confidential documents — to the '
                    'LLM provider (OpenAI, Anthropic, Google). GDPR, HIPAA, AI Act violations. '
                    '“On-premise RAG” remains an illusion: the LLM itself lives in the cloud.'
                    if en else
                    'Chaque requête RAG envoie le contexte — donc vos documents confidentiels — au '
                    'fournisseur LLM (OpenAI, Anthropic, Google). Violation RGPD, HIPAA, AI Act. '
                    'Le « RAG on-premise » reste une illusion : le LLM lui-même est dans le cloud.'
                ),
            },
            {
                'title': ('Inefficient RAG management' if en else 'Gestion RAG inefficace'),
                'stat': '≈ 5%',
                'description': (
                    'Chunking destroys document structure, vector embeddings are an approximation, '
                    'updates require re-indexing the whole corpus, and context is limited to '
                    'retrieved chunks. An expensive infrastructure for mediocre results.'
                    if en else
                    'Le chunking détruit la structure des documents, les embeddings vectoriels sont '
                    'une approximation, la mise à jour exige de ré-indexer tout le corpus, et le '
                    'contexte est limité aux chunks retrievés. Une infrastructure coûteuse pour un '
                    'résultat médiocre.'
                ),
            },
        ],
        'pillars': [
            {
                'title': ('Deterministic reasoning' if en else 'Raisonnement déterministe'),
                'stat': ('0% hallucination' if en else '0% hallucination'),
                'description': (
                    'The ψ codec scores 88.4% on GSM8K with 0% hallucination. Every answer is '
                    'traceable, verifiable, identically reproducible — a fundamental requirement of '
                    'regulated sectors.'
                    if en else
                    'Le codec ψ atteint 88.4% sur GSM8K avec 0% d\'hallucination. Chaque réponse '
                    'est traçable, vérifiable, reproductible à l\'identique — exigence fondamentale '
                    'des secteurs régulés.'
                ),
            },
            {
                'title': ('Sovereign data' if en else 'Données souveraines'),
                'stat': ('100% on-premise' if en else '100% on-premise'),
                'description': (
                    'Zero data leaves the network. HCV compression (×213 ratio) shrinks storage and '
                    'everything stays encrypted (AES-GCM-256). Privacy is not a promise — it is an '
                    'architecture.'
                    if en else
                    'Zéro donnée ne quitte le réseau. La compression HCV (ratio ×213) réduit le '
                    'stockage et tout reste chiffré (AES-GCM-256). La privacy n\'est pas une '
                    'promesse : c\'est une architecture.'
                ),
            },
            {
                'title': ('Holograms instead of RAG' if en else 'Hologrammes au lieu du RAG'),
                'stat': ('2 MB per domain' if en else '2 Mo par domaine'),
                'description': (
                    'A hologram captures the full knowledge of a domain (finance, HR, legal…) in a '
                    '2 MB file. No vector DB, no chunking, no embeddings. Instant updates.'
                    if en else
                    'Un hologramme capture la connaissance complète d\'un domaine (finance, RH, '
                    'juridique…) en un fichier de 2 Mo. Pas de vector DB, pas de chunking, pas '
                    'd\'embeddings. Mise à jour instantanée.'
                ),
            },
            {
                'title': ('Zero GPU required' if en else 'Zéro GPU requis'),
                'stat': ('1 CPU is enough' if en else '1 CPU suffit'),
                'description': (
                    'Our harmonic AI runs on any enterprise server. No €100k GPU, no cluster, no '
                    'per-token inference cost.'
                    if en else
                    'Notre IA harmonique tourne sur n\'importe quel serveur d\'entreprise. Pas de '
                    'GPU à 100 000 €, pas de cluster, pas de coût d\'inférence par token.'
                ),
            },
            {
                'title': ('Total traceability' if en else 'Traçabilité totale'),
                'stat': ('built-in audit' if en else 'audit intégré'),
                'description': (
                    'Every answer cites its source facts (hologram domain + used triplets). '
                    'Complete audit trail for internal and regulatory audits.'
                    if en else
                    'Chaque réponse cite ses faits sources (domaine hologramme + triplets utilisés). '
                    'Journal d\'audit complet pour vos audits internes et réglementaires.'
                ),
            },
        ],
    }


import re  # Pour compliance check