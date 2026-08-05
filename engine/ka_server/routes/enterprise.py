"""
KA Server — Routes Enterprise
==============================
Endpoints Enterprise: ingestion, conformité, audit, déploiement.
Nécessitent authentification API Key.
"""

import logging
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


import re  # Pour compliance check