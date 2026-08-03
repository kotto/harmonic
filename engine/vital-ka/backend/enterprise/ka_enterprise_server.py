"""
KA Enterprise Server — Application Professionnelle Complète
=============================================================

Serveur de production pour KA Enterprise avec :
- Authentification SSO + API Keys + RBAC
- Rate limiting par tenant
- Audit trail obligatoire
- Chiffrement AES-256 au repos
- Dashboard administrateur
- API REST documentée (OpenAPI)
- Interface d'administration

Démarrage :
  python ka_enterprise_server.py --port 8767 --host 0.0.0.0

Auteur : Équipe HarmoniqLLM
Date   : 2026-07-25
"""

import sys
import os
import io
import json
import time
import uuid
import hashlib
import base64
import secrets
import threading
import argparse
from pathlib import Path
from functools import wraps
from typing import Optional

import numpy as np

# Flask
try:
    from flask import Flask, request, jsonify, send_file, g, Response
    from flask_cors import CORS
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False
    print("⚠️ Flask non installé. pip install flask flask-cors")

# ═══════════════════════════════════════════════════════════════════════════════
# INIT — Moteur Enterprise + Extensions
# ═══════════════════════════════════════════════════════════════════════════════

from ka_enterprise_core import EnterpriseEngine
from ka_enterprise_extensions import (
    RBACManager, SSOManager, HologramVersioning,
    GDPRManager, WebhookManager, HologramExporter,
    MetricsTracker, RateLimiter, RateLimitExceeded,
    HologramEncryption, ROLES, EnterpriseUser,
)

# ── Moteur ─────────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).resolve().parent / "data" / "enterprise"
DATA_DIR.mkdir(parents=True, exist_ok=True)

engine = EnterpriseEngine(data_dir=str(DATA_DIR))
rbac = RBACManager(engine)
sso = SSOManager(engine, rbac)
versions = HologramVersioning(engine)
gdpr = GDPRManager(engine)
webhooks = WebhookManager(engine)
exporter = HologramExporter(engine)
metrics = MetricsTracker(engine)
limiter = RateLimiter(engine, default_limit=100, window_seconds=60)
crypto = HologramEncryption()

# ── Créer un admin par défaut si aucun utilisateur n'existe ────────────────────
if len(rbac.users) == 0 and len(engine.tenants) == 0:
    print("\n🔧 Premier démarrage — création du tenant et admin par défaut...")
    default_tenant = engine.create_tenant("Mon Entreprise", "admin@entreprise.com")
    default_user = rbac.create_user(
        "admin@entreprise.com", "Administrateur",
        default_tenant.id, role='admin',
        department_ids=list(default_tenant.departments.keys()),
    )
    print(f"   Tenant  : {default_tenant.name} (id={default_tenant.id})")
    print(f"   Admin   : {default_user.email}")
    print(f"   API Key : {default_tenant.api_key}")
    print(f"   Départements créés : {len(default_tenant.departments)}")
    print()

# ═══════════════════════════════════════════════════════════════════════════════
# FLASK APP
# ═══════════════════════════════════════════════════════════════════════════════

app = Flask(__name__)
if HAS_FLASK:
    CORS(app, resources={r"/api/*": {"origins": "*"}})

# ── Fichiers statiques (animations, documents) ────────────────────────────────

_ENGINE_DIR = Path(__file__).resolve().parent

@app.route('/animation_equation_maitresse.html')
def serve_animation_genese():
    return send_file(_ENGINE_DIR / 'animation_equation_maitresse.html')

@app.route('/animation_convergence_alpha.html')
def serve_animation_convergence():
    return send_file(_ENGINE_DIR / 'animation_convergence_alpha.html')

@app.route('/DOCUMENT_ALPHA_GRAND_PUBLIC.md')
def serve_document_alpha():
    return send_file(_ENGINE_DIR / 'DOCUMENT_ALPHA_GRAND_PUBLIC.md', mimetype='text/markdown')

@app.route('/README_DEPLOIEMENT_VPS.md')
def serve_readme_vps():
    return send_file(_ENGINE_DIR / 'deploy_vps' / 'README_DEPLOIEMENT_VPS.md',
                     mimetype='text/markdown')

# ═══════════════════════════════════════════════════════════════════════════════
# MIDDLEWARE — Sécurité
# ═══════════════════════════════════════════════════════════════════════════════

def require_auth(f):
    """Middleware : exige une authentification (SSO token ou API key)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        g.user = None
        g.tenant = None
        
        # 1. Vérifier le token SSO (Bearer)
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            g.user = sso.authenticate_with_token(token)
            if g.user:
                g.tenant = engine.get_tenant(g.user.tenant_id)
        
        # 2. Vérifier l'API key (header ou query param)
        if not g.user:
            api_key = request.headers.get('X-API-Key', request.args.get('api_key', ''))
            if api_key:
                # Chercher un utilisateur avec cette API key
                for u in rbac.users.values():
                    if u.api_key == api_key and u.is_active:
                        g.user = u
                        g.tenant = engine.get_tenant(u.tenant_id)
                        break
                # Chercher un tenant avec cette API key
                if not g.user:
                    g.tenant = engine.get_tenant_by_api_key(api_key)
        
        if not g.user and not g.tenant:
            return jsonify({'error': 'Authentification requise', 
                          'auth_methods': ['Bearer token (SSO)', 'X-API-Key header']}), 401
        
        # Audit log automatique
        g.request_id = hashlib.sha256(
            f"{request.method}:{request.path}:{time.time()}".encode()
        ).hexdigest()[:12]
        
        return f(*args, **kwargs)
    return decorated


def require_permission(permission: str):
    """Middleware : exige une permission RBAC spécifique."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if g.user and not rbac.can(g.user.id, permission):
                return jsonify({
                    'error': 'Permission refusée',
                    'required': permission,
                    'your_role': g.user.role,
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


def rate_limit(f):
    """Middleware : rate limiting par tenant."""
    @wraps(f)
    def decorated(*args, **kwargs):
        tenant_id = g.tenant.id if g.tenant else (g.user.tenant_id if g.user else 'anonymous')
        try:
            limiter.check(tenant_id)
        except RateLimitExceeded as e:
            return jsonify({
                'error': str(e),
                'retry_after_seconds': e.retry_after,
            }), 429
        return f(*args, **kwargs)
    return decorated


def audit_log(f):
    """Middleware : journalise automatiquement toutes les requêtes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        t0 = time.perf_counter()
        try:
            result = f(*args, **kwargs)
            elapsed = (time.perf_counter() - t0) * 1000
            tenant_id = g.tenant.id if g.tenant else (g.user.tenant_id if g.user else '?')
            metrics.record_query(tenant_id, elapsed, success=True)
            return result
        except Exception as e:
            elapsed = (time.perf_counter() - t0) * 1000
            tenant_id = g.tenant.id if g.tenant else (g.user.tenant_id if g.user else '?')
            metrics.record_query(tenant_id, elapsed, success=False)
            raise
    return decorated


# ═══════════════════════════════════════════════════════════════════════════════
# PAGES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    """Page d'accueil — redirige vers l'interface admin."""
    return '''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KA Enterprise — Administration</title>
        <style>
            *{margin:0;padding:0;box-sizing:border-box}
            body{font-family:'Inter',system-ui,sans-serif;background:#0a0a0f;color:#d4c8a0;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center}
            .card{background:#14141f;border:1px solid #2a2a3a;border-radius:16px;padding:40px;text-align:center;max-width:500px;margin:20px}
            h1{font-size:2rem;font-weight:700;background:linear-gradient(135deg,#c9a84c,#e6c860);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:12px}
            .btn{display:inline-block;padding:12px 24px;border-radius:8px;border:1px solid #c9a84c;color:#c9a84c;text-decoration:none;margin:8px;font-size:0.9rem;transition:all .3s}
            .btn:hover{background:rgba(201,168,76,0.1)}
            .btn-primary{background:#c9a84c;color:#0a0a0f;font-weight:600}
            .btn-primary:hover{background:#d4af37}
            .features{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:20px;text-align:left}
            .features div{background:rgba(255,255,255,0.02);padding:8px 12px;border-radius:6px;font-size:0.75rem;color:#888}
            .features div strong{color:#c9a84c;display:block;font-size:0.8rem}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🏢 KA Enterprise</h1>
            <p style="color:#888;margin-bottom:20px;">IA d\'Entreprise Harmonique — Zéro hallucination</p>
            <a href="/onboard" class="btn btn-primary" style="background:linear-gradient(135deg,#00d2a0,#00b894);border-color:#00d2a0">🚀 Créer mon environnement</a>
            <a href="/admin" class="btn btn-primary">📊 Dashboard Admin</a>
            <a href="/docs" class="btn">📖 API Documentation</a>
            <a href="/api/enterprise/info" class="btn">ℹ️ Infos Système</a>
            <div class="features">
                <div><strong>🔒 SSO + RBAC</strong>5 rôles, permissions</div>
                <div><strong>🧠 Hologrammes</strong>Étanches par département</div>
                <div><strong>📄 Ingestion</strong>PDF, DOCX, XLSX, CSV</div>
                <div><strong>🔐 AES-256</strong>Chiffrement au repos</div>
                <div><strong>📋 Audit</strong>SHA256, horodaté</div>
                <div><strong>⚡ 0 GPU</strong>CPU uniquement</div>
            </div>
        </div>
    </body>
    </html>
    '''


@app.route('/admin')
def admin_panel():
    """Interface d'administration complète."""
    return _admin_html()


@app.route('/docs')
def api_docs():
    """Documentation API."""
    from ka_enterprise_extensions import OPENAPI_SPEC
    return jsonify(OPENAPI_SPEC)


@app.route('/onboard')
def onboard_page():
    """Portail d'onboarding : l'entreprise décrit SON environnement →
    KA Enterprise propose les hologrammes à créer → déploiement VPS."""
    return _onboard_html()


# ═══════════════════════════════════════════════════════════════════════════════
# API — Tenants
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/enterprise/tenants', methods=['GET'])
@require_auth
@require_permission('tenant:read')
@rate_limit
@audit_log
def list_tenants():
    return jsonify({'tenants': engine.list_tenants()})


@app.route('/api/enterprise/tenants', methods=['POST'])
@require_auth
@require_permission('tenant:write')
@rate_limit
@audit_log
def create_tenant():
    data = request.get_json(force=True, silent=True) or {}
    name = data.get('name', '').strip()
    email = data.get('admin_email', '').strip()
    if not name:
        return jsonify({'error': 'name requis'}), 400
    tenant = engine.create_tenant(name, admin_email=email or f'admin@{name.lower().replace(" ","")}.com')
    return jsonify({'id': tenant.id, 'name': tenant.name, 'api_key': tenant.api_key}), 201


@app.route('/api/enterprise/tenants/<tenant_id>', methods=['DELETE'])
@require_auth
@require_permission('tenant:delete')
@rate_limit
@audit_log
def delete_tenant(tenant_id):
    if tenant_id not in engine.tenants:
        return jsonify({'error': 'Tenant non trouvé'}), 404
    del engine.tenants[tenant_id]
    engine._save_state()
    return jsonify({'deleted': tenant_id})


# ═══════════════════════════════════════════════════════════════════════════════
# API — Départements
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/enterprise/tenants/<tenant_id>/departments', methods=['GET'])
@require_auth
@require_permission('department:read')
@rate_limit
@audit_log
def list_departments(tenant_id):
    return jsonify({'departments': engine.list_departments(tenant_id)})


@app.route('/api/enterprise/tenants/<tenant_id>/departments', methods=['POST'])
@require_auth
@require_permission('department:create')
@rate_limit
@audit_log
def create_department(tenant_id):
    data = request.get_json(force=True, silent=True) or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'name requis'}), 400
    dept = engine.create_department(tenant_id, name)
    versions.commit(dept.id, 'Création initiale')
    return jsonify({'id': dept.id, 'name': dept.name, 'phase_offset': round(dept.phase_offset / 6.283185, 3)}), 201


@app.route('/api/enterprise/departments/<department_id>', methods=['DELETE'])
@require_auth
@require_permission('department:delete')
@rate_limit
@audit_log
def delete_department(department_id):
    if department_id not in engine.departments:
        return jsonify({'error': 'Département non trouvé'}), 404
    del engine.departments[department_id]
    engine._save_state()
    return jsonify({'deleted': department_id})


# ═══════════════════════════════════════════════════════════════════════════════
# API — Ingestion
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/enterprise/departments/<department_id>/ingest', methods=['POST'])
@require_auth
@require_permission('hologram:ingest')
@rate_limit
@audit_log
def ingest_documents(department_id):
    """Ingère du texte ou des fichiers dans un hologramme départemental."""
    if department_id not in engine.departments:
        return jsonify({'error': 'Département non trouvé'}), 404
    
    # Vérifier que l'utilisateur a accès à ce département
    if g.user and g.user.department_ids and department_id not in g.user.department_ids:
        return jsonify({'error': 'Accès non autorisé à ce département'}), 403
    
    if request.is_json:
        data = request.get_json(force=True)
        text = data.get('text', '').strip()
        source = data.get('source', 'api')
        if not text:
            return jsonify({'error': 'text requis'}), 400
        count = engine.ingest_text(department_id, text, source=source)
    elif request.files:
        count = 0
        for key in request.files:
            file = request.files[key]
            # Sauvegarder temporairement
            tmp_path = engine.data_dir / f"_tmp_{uuid.uuid4().hex[:8]}_{file.filename}"
            file.save(str(tmp_path))
            try:
                c = engine.ingest_file(department_id, str(tmp_path))
                count += c
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()
    else:
        return jsonify({'error': 'Envoyez du JSON {text} ou un fichier (multipart)'}), 400
    
    # Commit automatique
    versions.commit(department_id, f'Ingestion API: {count} faits')
    
    return jsonify({
        'department_id': department_id,
        'facts_ingested': count,
        'total_facts': engine.departments[department_id].fact_count,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# API — Requêtes
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/enterprise/departments/<department_id>/ask', methods=['POST'])
@require_auth
@require_permission('hologram:query')
@rate_limit
@audit_log
def ask_department(department_id):
    """Interroge l'hologramme d'un département."""
    data = request.get_json(force=True, silent=True) or {}
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'error': 'question requise'}), 400
    
    # Vérifier accès département
    if g.user and g.user.department_ids and department_id not in g.user.department_ids:
        return jsonify({'error': 'Accès non autorisé à ce département'}), 403
    
    user_id = g.user.id if g.user else 'api_key'
    result = engine.ask(question, department_id, user_id=user_id)
    
    # Notifier si confiance faible
    if result.confidence < 0.3:
        webhooks.notify('low_confidence', 
                       f"Confiance {result.confidence:.2f}: {question[:80]}",
                       department_id)

    # ⚡ Gate → chaînon D : auto-apprentissage piloté par l'usage — la
    # question est enregistrée (refus calibré ou confiance faible) ; aux
    # seuils (facette 2× / sujet 3×), la complétion se déclenche
    # (Wikipedia + facettes manquantes, couverture recalculée).
    try:
        from enterprise_completion import should_register_miss
        if should_register_miss(result):
            from completion_queue import register_miss
            miss = register_miss(question, sujet=engine.departments[department_id].name)
            if miss.get('triggered'):
                from enterprise_completion import complete_department_background
                complete_department_background(engine, department_id,
                                               engine.departments[department_id].name,
                                               facettes=[miss['facette']])
    except Exception:
        pass
    
    return jsonify({
        'question': result.question,
        'answer': result.answer,
        'confidence': float(result.confidence),
        'sources': result.sources,
        'department': result.department,
        'response_id': result.response_id,
        'elapsed_ms': result.elapsed_ms,
        'admitted_uncertainty': bool(result.admitted_uncertainty),
    })


@app.route('/api/enterprise/tenants/<tenant_id>/ask', methods=['POST'])
@require_auth
@require_permission('hologram:query')
@rate_limit
@audit_log
def ask_cross_department(tenant_id):
    """Interroge TOUS les départements d'un tenant."""
    data = request.get_json(force=True, silent=True) or {}
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'error': 'question requise'}), 400
    
    results = engine.ask_cross_department(question, tenant_id)
    return jsonify({
        'question': question,
        'results': [{
            'department': r.department,
            'confidence': r.confidence,
            'answer': r.answer[:200],
            'sources': r.sources,
        } for r in results],
    })


# ═══════════════════════════════════════════════════════════════════════════════
# API — Données privées → LIVRABLES (Excel, textes, synthèse)
# ═══════════════════════════════════════════════════════════════════════════════

def _check_dept_access(department_id) -> Optional[Response]:
    """Vérifie l'existence et l'accès au département (None si OK)."""
    if department_id not in engine.departments:
        return jsonify({'error': 'Département non trouvé'}), 404
    if g.user and g.user.department_ids and department_id not in g.user.department_ids:
        return jsonify({'error': 'Accès non autorisé à ce département'}), 403
    return None


@app.route('/api/enterprise/departments/<department_id>/data', methods=['POST'])
@require_auth
@require_permission('hologram:query')
@rate_limit
@audit_log
def data_query(department_id):
    """
    Question de DONNÉES : répond sur les données privées du département avec
    un tableau (colonnes/lignes) + agrégats (compte, somme, moyenne, min, max).
    Body: { "question": "liste des clients / chiffre d'affaires total / …" }
    """
    data = request.get_json(force=True, silent=True) or {}
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'error': 'question requise'}), 400
    err = _check_dept_access(department_id)
    if err:
        return err
    try:
        from enterprise_deliverables import query_data
        return jsonify(query_data(engine, department_id, question))
    except Exception as e:
        return jsonify({'error': f'Données: {e}'}), 500


@app.route('/api/enterprise/departments/<department_id>/export', methods=['GET'])
@require_auth
@require_permission('hologram:query')
@rate_limit
@audit_log
def export_deliverable(department_id):
    """
    Télécharge le livrable Excel (.xlsx — feuilles Données + Résumé) ou CSV
    de la question posée. Query params: question=…&format=xlsx|csv
    """
    question = request.args.get('question', '').strip()
    fmt = request.args.get('format', 'xlsx').lower()
    if not question:
        return jsonify({'error': 'question requise (?question=…)'}), 400
    err = _check_dept_access(department_id)
    if err:
        return err
    try:
        from enterprise_deliverables import build_excel, export_csv, query_data, _slug
        if fmt == 'csv':
            data = query_data(engine, department_id, question)
            bio = io.BytesIO(export_csv(data).encode('utf-8-sig'))
            filename = f"{_slug(question)}_{fmt}.csv"
            return send_file(bio, mimetype='text/csv', as_attachment=True,
                             download_name=filename)
        bio, filename = build_excel(engine, department_id, question)
        return send_file(bio, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': f'Export: {e}'}), 500


@app.route('/api/enterprise/departments/<department_id>/compose', methods=['POST'])
@require_auth
@require_permission('hologram:query')
@rate_limit
@audit_log
def compose_doc(department_id):
    """
    Prépare un TEXTE structuré depuis les données privées :
    email, rapport, compte_rendu, lettre, note.
    Body: { "brief": "…", "format": "rapport", "objet": "…",
            "destinataire": "…", "download": "docx"|"txt"|null }
    """
    data = request.get_json(force=True, silent=True) or {}
    brief = data.get('brief', '').strip()
    if not brief:
        return jsonify({'error': 'brief requis'}), 400
    err = _check_dept_access(department_id)
    if err:
        return err
    try:
        from enterprise_deliverables import compose_document, document_to_docx, _slug
        doc = compose_document(engine, department_id, brief,
                               doc_format=data.get('format', 'rapport'),
                               destinataire=data.get('destinataire') or None,
                               objet=data.get('objet') or None)
        download = data.get('download')
        if download in ('docx', 'txt'):
            bio, name = document_to_docx(doc['texte'], f"{doc['format']}_{_slug(brief)}")
            if download == 'txt' or name.endswith('.txt'):
                bio = io.BytesIO(doc['texte'].encode('utf-8'))
                name = f"{doc['format']}_{_slug(brief)}.txt"
            mime = ('application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    if name.endswith('.docx') else 'text/plain')
            return send_file(bio, mimetype=mime, as_attachment=True, download_name=name)
        return jsonify(doc)
    except Exception as e:
        return jsonify({'error': f'Composition: {e}'}), 500


@app.route('/api/enterprise/departments/<department_id>/summarize', methods=['POST'])
@require_auth
@require_permission('hologram:query')
@rate_limit
@audit_log
def summarize_doc(department_id):
    """Synthèse du savoir d'un département (données + sources)."""
    err = _check_dept_access(department_id)
    if err:
        return err
    try:
        from enterprise_deliverables import summarize_department
        return jsonify(summarize_department(engine, department_id))
    except Exception as e:
        return jsonify({'error': f'Synthèse: {e}'}), 500


# ═══════════════════════════════════════════════════════════════════════════════
# MCP — agents spécialisés (Model Context Protocol, streamable HTTP)
# ═══════════════════════════════════════════════════════════════════════════════

_mcp_session = None


def _mcp_session_get():
    global _mcp_session
    if _mcp_session is None:
        from mcp.mcp_protocol import McpSession
        from mcp.mcp_tools import tools_provider, tool_executor
        _mcp_session = McpSession(tools_provider, tool_executor)
    return _mcp_session


@app.route('/mcp', methods=['POST'])
@require_auth
@rate_limit
@audit_log
def mcp_endpoint():
    """
    Point d'entrée MCP (streamable HTTP) : initialize, tools/list, tools/call.
    Authentifié par la clé API du tenant (X-API-Key / Bearer SSO).
    """
    body = request.get_json(force=True, silent=True)
    if not body:
        return jsonify({'jsonrpc': '2.0', 'id': None,
                        'error': {'code': -32700,
                                  'message': 'Corps JSON-RPC requis'}}), 400
    ctx = {'engine': engine, 'tenant': g.tenant, 'user': g.user,
           'data_dir': DATA_DIR}
    try:
        response = _mcp_session_get().handle(body, ctx)
    except Exception as e:
        return jsonify({'jsonrpc': '2.0', 'id': body.get('id'),
                        'error': {'code': -32603, 'message': f'Erreur interne: {e}'}}), 500
    if response is None:
        return '', 202  # notification acceptée
    if 'text/event-stream' in request.headers.get('Accept', ''):
        from mcp.mcp_protocol import sse_response
        return Response(sse_response(response), mimetype='text/event-stream')
    return jsonify(response)


@app.route('/mcp/agents', methods=['GET'])
@require_auth
@rate_limit
def mcp_agents_list():
    """Catalogue des agents spécialisés + démonstration du routage (concours)."""
    from mcp.mcp_agents import agents_list, route_agent
    result = agents_list()
    question = request.args.get('question', '').strip()
    if question:
        result['routage'] = {'question': question,
                             'agent_gagnant': route_agent(question)}
    return jsonify(result)


# ═══════════════════════════════════════════════════════════════════════════════
# CHAÎNON D — auto-apprentissage piloté par l'usage
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/enterprise/completions/status', methods=['GET'])
@require_auth
@rate_limit
def completions_status():
    """État du chaînon D : file d'attente des questions sans réponse +
    derniers rapports de complétion (couverture avant/après)."""
    from enterprise_completion import status
    return jsonify(status())


@app.route('/api/enterprise/completions/run', methods=['POST'])
@require_auth
@require_permission('hologram:ingest')
@rate_limit
@audit_log
def completions_run():
    """Traite les sujets en attente : complétion en arrière-plan."""
    from enterprise_completion import run_pending
    return jsonify(run_pending(engine))


# ═══════════════════════════════════════════════════════════════════════════════
# API — Audit & Dashboard & Metrics
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/enterprise/audit', methods=['GET'])
@require_auth
@require_permission('audit:read')
@audit_log
def get_audit():
    tenant_id = request.args.get('tenant_id')
    dept_id = request.args.get('department_id')
    limit = int(request.args.get('limit', 50))
    return jsonify({'audit_log': engine.get_audit_log(tenant_id, dept_id, limit)})


@app.route('/api/enterprise/dashboard', methods=['GET'])
@require_auth
@rate_limit
@audit_log
def dashboard():
    data = engine.get_dashboard()
    # 🎯 Complétude par facettes de chaque département (hologramme)
    try:
        from facet_coverage import coverage_texts
        detail = []
        for dep in engine.departments.values():
            facts = engine.facts.get(dep.id, [])
            texts = [f.text for f in facts]
            cov = {'couverture': 0.0, 'manquantes': []}
            if texts:
                cov = coverage_texts(texts, dep.name)
            detail.append({
                'id': dep.id,
                'name': dep.name,
                'tenant_id': dep.tenant_id,
                'fact_count': dep.fact_count,
                'couverture': round(float(cov.get('couverture', 0.0)), 3),
                'facettes_manquantes': cov.get('manquantes', []),
            })
        data['departments_detail'] = detail
    except Exception:
        data['departments_detail'] = []
    return jsonify(data)


# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 ONBOARDING — l'entreprise décrit SON environnement → hologrammes
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/enterprise/onboard/analyze', methods=['POST'])
def onboard_analyze():
    """
    Analyse la description de l'environnement → domaines d'activité
    détectés avec les hologrammes (départements) proposés.

    Body: { "description": "...", "secteur": "optionnel" }
    """
    data = request.get_json(force=True, silent=True) or {}
    description = data.get('description', '').strip()
    secteur = data.get('secteur') or None
    if not description or len(description) < 20:
        return jsonify({'error': 'Décrivez votre environnement (au moins 20 caractères)'}), 400
    try:
        from enterprise_onboard import analyze_environment
        return jsonify(analyze_environment(description, secteur))
    except Exception as e:
        return jsonify({'error': f'Analyse: {e}'}), 500


@app.route('/api/enterprise/onboard', methods=['POST'])
def onboard_create():
    """
    Crée l'environnement complet : tenant + départements (hologrammes)
    avec seed initial (web ou corpus hors-ligne) — l'entreprise peut
    immédiatement poser des questions, avant même d'ingérer ses documents.

    Body: { "name": "...", "email": "...", "description": "...",
            "secteur": "optionnel", "holograms": ["sujet1", ...] }
    """
    data = request.get_json(force=True, silent=True) or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    description = data.get('description', '').strip()
    if not name or not email or not description:
        return jsonify({'error': 'name, email et description requis'}), 400
    try:
        from enterprise_onboard import create_environment
        result = create_environment(engine, name, email, description,
                                    data.get('secteur') or None,
                                    holograms=data.get('holograms') or None)
        if 'error' in result:
            return jsonify(result), 500
        # Clé API du tenant → l'entreprise accède immédiatement au dashboard
        tenant = engine.get_tenant(result['tenant']['id'])
        if tenant:
            result['tenant']['api_key'] = tenant.api_key
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Onboarding: {e}'}), 500



@app.route('/api/enterprise/metrics', methods=['GET'])
@require_auth
@require_permission('audit:read')
def get_metrics():
    accept = request.headers.get('Accept', '')
    if 'prometheus' in accept or request.args.get('format') == 'prometheus':
        return Response(metrics.prometheus_format(), mimetype='text/plain')
    return jsonify(metrics.get_metrics())


# ═══════════════════════════════════════════════════════════════════════════════
# API — Utilisateurs (RBAC)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/enterprise/users', methods=['GET'])
@require_auth
@require_permission('user:list')
@audit_log
def list_users():
    tenant_id = request.args.get('tenant_id')
    return jsonify({'users': rbac.list_users(tenant_id)})


@app.route('/api/enterprise/users', methods=['POST'])
@require_auth
@require_permission('user:create')
@audit_log
def create_user():
    data = request.get_json(force=True, silent=True) or {}
    email = data.get('email', '').strip()
    name = data.get('name', '').strip()
    role = data.get('role', 'user')
    tenant_id = data.get('tenant_id', '')
    dept_ids = data.get('department_ids', [])
    
    if not email:
        return jsonify({'error': 'email requis'}), 400
    
    user = rbac.create_user(email, name, tenant_id, role=role, department_ids=dept_ids)
    return jsonify({'id': user.id, 'email': user.email, 'role': user.role, 'api_key': user.api_key}), 201


# ═══════════════════════════════════════════════════════════════════════════════
# API — Hologrammes (versioning, export, merge)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/enterprise/departments/<department_id>/versions', methods=['GET'])
@require_auth
@require_permission('hologram:query')
@audit_log
def get_versions(department_id):
    return jsonify({'versions': versions.history(department_id)})


@app.route('/api/enterprise/departments/<department_id>/rollback', methods=['POST'])
@require_auth
@require_permission('hologram:ingest')
@audit_log
def rollback_department(department_id):
    data = request.get_json(force=True, silent=True) or {}
    ver = data.get('version', 1)
    ok = versions.rollback(department_id, ver)
    return jsonify({'department_id': department_id, 'rolled_back_to': ver, 'success': ok})


@app.route('/api/enterprise/departments/<department_id>/export', methods=['GET'])
@require_auth
@require_permission('hologram:export')
@audit_log
def export_department(department_id):
    path = exporter.export(department_id, str(engine.data_dir / f"export_{department_id}.npz"))
    return send_file(path, as_attachment=True, download_name=f"hologram_{department_id}.npz")


@app.route('/api/enterprise/departments/merge', methods=['POST'])
@require_auth
@require_permission('hologram:ingest')
@audit_log
def merge_departments():
    data = request.get_json(force=True, silent=True) or {}
    a = data.get('department_a')
    b = data.get('department_b')
    name = data.get('new_name')
    merged_id = exporter.merge(a, b, name)
    return jsonify({'merged_id': merged_id})


# ═══════════════════════════════════════════════════════════════════════════════
# API — Vérification d'étanchéité
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/enterprise/verify-seal', methods=['POST'])
@require_auth
@require_permission('department:read')
@audit_log
def verify_seal():
    data = request.get_json(force=True, silent=True) or {}
    a = data.get('department_a')
    b = data.get('department_b')
    return jsonify(engine.verify_seal(a, b))


# ═══════════════════════════════════════════════════════════════════════════════
# API — Info système
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/enterprise/info', methods=['GET'])
def info():
    return jsonify({
        'version': '4.0.0',
        'product': 'KA Enterprise',
        'tenants': len(engine.tenants),
        'departments': len(engine.departments),
        'total_facts': sum(d.fact_count for d in engine.departments.values()),
        'users': len(rbac.users),
        'audit_entries': len(engine.audit_log),
        'encryption': 'AES-256-CBC',
        'sso_available': True,
        'rbac_roles': list(ROLES.keys()),
        'uptime_seconds': time.time() - metrics._start_time if hasattr(metrics, '_start_time') else 0,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# PORTAL ONBOARDING — l'entreprise décrit son environnement → hologrammes
# ═══════════════════════════════════════════════════════════════════════════════

def _onboard_html():
    return r'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KA Enterprise — Créer mon environnement</title>
<style>
:root{--bg:#0a0a0f;--surface:#14141f;--border:#2a2a3a;--gold:#c9a84c;--text:#d4c8a0;--muted:#888;--green:#00d2a0;--red:#e74c3c;--accent:#6c5ce7}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
.header{background:var(--surface);border-bottom:1px solid var(--border);padding:16px 24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
.header h1{font-size:1.2rem;color:var(--gold)}.header a{color:var(--muted);text-decoration:none;font-size:.75rem}.header a:hover{color:var(--gold)}
.container{max-width:860px;margin:0 auto;padding:24px}
.stepper{display:flex;gap:0;margin-bottom:24px;border:1px solid var(--border);border-radius:10px;overflow:hidden}
.step{flex:1;padding:10px 6px;text-align:center;font-size:.68rem;color:var(--muted);background:var(--surface);border-right:1px solid var(--border)}
.step:last-child{border-right:none}.step b{display:block;font-size:.8rem;color:var(--text);margin-bottom:2px}
.step.done{color:var(--green)}.step.done b{color:var(--green)}.step.active{background:rgba(201,168,76,.08)}
.step.active b{color:var(--gold)}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:16px}
.card h2{font-size:1rem;color:var(--gold);margin-bottom:6px}.card p.sub{font-size:.75rem;color:var(--muted);margin-bottom:16px}
label{display:block;font-size:.7rem;color:var(--muted);margin:10px 0 4px;text-transform:uppercase;letter-spacing:.05em}
input,textarea,select{padding:10px;border:1px solid var(--border);border-radius:6px;background:var(--bg);color:var(--text);font:inherit;font-size:.85rem;width:100%}
input:focus,textarea:focus,select:focus{outline:none;border-color:var(--gold)}
textarea{resize:vertical;min-height:110px}
.row{display:flex;gap:10px}.row>*{flex:1}
.btn{padding:11px 22px;border-radius:8px;border:1px solid var(--border);background:var(--surface);color:var(--text);cursor:pointer;font:inherit;font-size:.8rem;font-weight:600;transition:all .2s}
.btn:hover{border-color:var(--gold)}
.btn-p{background:linear-gradient(135deg,#c9a84c,#e6c860);color:#0a0a0f;border:none}
.btn-p:hover{filter:brightness(1.1)}
.btn-g{background:linear-gradient(135deg,#00d2a0,#00b894);color:#0a0a0f;border:none}
.btn-g:hover{filter:brightness(1.1)}
.btn:disabled{opacity:.4;cursor:not-allowed}
.chip{display:inline-block;padding:6px 12px;border:1px solid var(--border);border-radius:20px;font-size:.7rem;color:var(--muted);cursor:pointer;margin:3px;transition:all .2s;background:var(--bg)}
.chip:hover{border-color:var(--gold);color:var(--gold)}
.sector-box{border:1px solid var(--border);border-radius:10px;padding:14px;margin-bottom:12px;background:rgba(255,255,255,.02)}
.sector-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.sector-head strong{color:var(--text);font-size:.85rem}
.score{padding:2px 10px;border-radius:12px;font-size:.65rem;font-weight:700;background:rgba(201,168,76,.15);color:var(--gold)}
.holo{display:flex;align-items:flex-start;gap:10px;padding:8px 10px;border:1px solid var(--border);border-radius:8px;margin:6px 0;background:var(--bg)}
.holo input{margin-top:3px;width:16px;height:16px;accent-color:var(--green);cursor:pointer}
.holo .t{font-size:.8rem;color:var(--text);font-weight:600}
.holo .d{font-size:.68rem;color:var(--muted);margin-top:2px}
.holo .tag{margin-left:auto;font-size:.6rem;color:var(--green);white-space:nowrap;padding-top:2px}
table{width:100%;border-collapse:collapse;font-size:.75rem}
th,td{padding:8px 10px;text-align:left;border-bottom:1px solid var(--border)}
th{color:var(--gold);font-weight:600;font-size:.65rem;text-transform:uppercase}
.cov{font-weight:700}
.cov.good{color:var(--green)}.cov.mid{color:var(--gold)}.cov.bad{color:var(--red)}
.keybox{display:flex;gap:8px;align-items:center;background:var(--bg);border:1px dashed var(--border);border-radius:8px;padding:10px;margin:8px 0}
.keybox code{flex:1;font-family:monospace;font-size:.75rem;color:var(--green);word-break:break-all}
.copy-btn{padding:6px 12px;border:1px solid var(--border);border-radius:6px;background:var(--surface);color:var(--gold);cursor:pointer;font-size:.7rem}
.copy-btn:hover{border-color:var(--gold)}
code.inline{background:var(--bg);border:1px solid var(--border);padding:2px 6px;border-radius:4px;font-size:.72rem;font-family:monospace;color:var(--gold)}
pre{background:#0d0d16;border:1px solid var(--border);border-radius:8px;padding:12px;font-size:.72rem;line-height:1.5;overflow-x:auto;color:#9fd8b0;margin:8px 0}
.qr{display:none}
.answer{background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:14px;margin-top:10px;font-size:.85rem;line-height:1.55}
.answer .q{color:var(--gold);font-weight:600;margin-bottom:6px}
.hidden{display:none}
.err{color:var(--red);font-size:.8rem;margin-top:8px}
.ok{color:var(--green);font-size:.8rem;margin-top:8px}
#loading{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(10,10,15,.85);display:none;align-items:center;justify-content:center;z-index:99;flex-direction:column;gap:14px}
.spinner{width:40px;height:40px;border:3px solid var(--border);border-top-color:var(--gold);border-radius:50%;animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
#loading div{color:var(--gold);font-size:.85rem}
</style>
</head>
<body>
<div class="header">
  <h1>🏢 KA Enterprise — Créer mon environnement</h1>
  <a href="/">← Retour à l'accueil</a>
</div>

<div id="loading"><div class="spinner"></div><div>Analyse ondulatoire en cours…</div></div>

<div class="container">
  <div class="stepper">
    <div class="step active" id="st1"><b>1</b>Mon entreprise</div>
    <div class="step" id="st2"><b>2</b>Mon environnement</div>
    <div class="step" id="st3"><b>3</b>Hologrammes</div>
    <div class="step" id="st4"><b>4</b>Création</div>
    <div class="step" id="st5"><b>5</b>Déploiement VPS</div>
  </div>

  <!-- ══════════ ÉTAPE 1 : IDENTITÉ ══════════ -->
  <div class="card" id="panel1">
    <h2>1 · Qui êtes-vous ?</h2>
    <p class="sub">Ces informations créent votre espace entreprise (tenant) sécurisé.</p>
    <label>Nom de l'entreprise</label>
    <input id="f-name" placeholder="Ex : Clinique Harmonie">
    <label>Secteur d'activité (facultatif — l'analyse le détecte aussi)</label>
    <select id="f-secteur">
      <option value="">— Je ne sais pas, détectez-le —</option>
      <option value="sante">Santé & Médical</option>
      <option value="juridique">Droit & Juridique</option>
      <option value="finance">Finance & Assurance</option>
      <option value="informatique">Informatique & Tech</option>
      <option value="industrie">Industrie & Production</option>
      <option value="rh">Ressources Humaines</option>
      <option value="commerce">Commerce & Distribution</option>
      <option value="education">Éducation & Formation</option>
      <option value="energie">Énergie & Environnement</option>
      <option value="agriculture">Agriculture & Agroalimentaire</option>
      <option value="transport">Transport & Logistique</option>
      <option value="immobilier">Immobilier & Construction</option>
    </select>
    <label>Email administrateur</label>
    <input id="f-email" type="email" placeholder="admin@monentreprise.fr">
    <div style="margin-top:16px"><button class="btn btn-p" onclick="nextStep(2)">Continuer →</button></div>
  </div>

  <!-- ══════════ ÉTAPE 2 : ENVIRONNEMENT ══════════ -->
  <div class="card hidden" id="panel2">
    <h2>2 · Décrivez votre environnement</h2>
    <p class="sub">KA Enterprise analyse votre description et propose les hologrammes (départements) à créer — chaque hologramme est un savoir ondulatoire prêt à répondre, étanche par département.</p>
    <label>Description de votre environnement (activités, services, métiers…)</label>
    <textarea id="f-desc" placeholder="Ex : Nous sommes une clinique privée avec un service de pharmacie, des laboratoires d'analyses et un pôle administratif..."></textarea>
    <div style="margin-top:8px">
      <span class="chip" onclick="useExample(0)">🏥 Clinique privée + pharmacie + labos</span>
      <span class="chip" onclick="useExample(1)">⚖️ Cabinet d'avocats — droit des affaires</span>
      <span class="chip" onclick="useExample(2)">💻 Éditeur SaaS + infrastructure cloud</span>
      <span class="chip" onclick="useExample(3)">🏭 Usine de fabrication + qualité + maintenance</span>
      <span class="chip" onclick="useExample(4)">🏪 Commerce en ligne + marketing + service client</span>
    </div>
    <div class="row" style="margin-top:16px">
      <button class="btn" onclick="nextStep(1)">← Retour</button>
      <button class="btn btn-g" onclick="analyzeEnv()">🔍 Analyser mon environnement</button>
    </div>
    <div id="analyze-err" class="err"></div>
  </div>

  <!-- ══════════ ÉTAPE 3 : HOLOGRAMMES PROPOSÉS ══════════ -->
  <div class="card hidden" id="panel3">
    <h2>3 · Vos hologrammes proposés</h2>
    <p class="sub">Domaines détectés dans votre environnement — décochez ce qui ne vous concerne pas. Chaque hologramme sera <b style="color:var(--green)">enrichi automatiquement</b> pour répondre dès la création.</p>
    <div id="sectors"></div>
    <div class="row" style="margin-top:16px">
      <button class="btn" onclick="nextStep(2)">← Retour</button>
      <button class="btn btn-p" onclick="createEnv()">🚀 Créer mon environnement</button>
    </div>
    <div id="create-err" class="err"></div>
  </div>

  <!-- ══════════ ÉTAPE 4 : CRÉATION ══════════ -->
  <div class="card hidden" id="panel4">
    <h2>4 · Votre environnement est prêt 🎉</h2>
    <div id="created"></div>
    <div class="card" style="margin-top:14px;background:rgba(0,210,160,.04);border-color:rgba(0,210,160,.3)">
      <h2>⚡ Testez-le immédiatement</h2>
      <p class="sub">Vos hologrammes répondent déjà. Posez une question à un département :</p>
      <div class="row">
        <select id="t-dept"></select>
        <input id="t-question" placeholder="Ex : Quels sont les points clés du diagnostic clinique ?">
      </div>
      <button class="btn btn-g" onclick="testAsk()" style="margin-top:10px">🔍 Poser la question</button>
      <div id="t-answer" class="answer hidden"></div>
    </div>
    <div style="margin-top:16px;display:flex;gap:10px;flex-wrap:wrap">
      <button class="btn btn-p" onclick="nextStep(5)">🐳 Déployer sur mon VPS →</button>
      <a class="btn" href="/admin">📊 Ouvrir le dashboard admin</a>
    </div>
  </div>

  <!-- ══════════ ÉTAPE 5 : VPS ══════════ -->
  <div class="card hidden" id="panel5">
    <h2>5 · Hébergez votre environnement sur votre VPS</h2>
    <p class="sub">KA Enterprise s'installe en 2 minutes sur n'importe quel VPS (Ubuntu 22.04+, 2 vCPU / 4 Go RAM suffisent — CPU uniquement, aucun GPU). Vos hologrammes, vos données et votre clé API restent <b style="color:var(--gold)">chez vous</b>.</p>
    <label>1 · Copiez le dossier <code class="inline">deploy_vps/</code> sur votre VPS (scp)</label>
    <pre id="cmd-1">scp -r deploy_vps root@VOTRE_VPS:/opt/ka-enterprise</pre>
    <button class="copy-btn" onclick="copyCmd('cmd-1')">📋 Copier</button>
    <label>2 · Lancer l'installation</label>
    <pre id="cmd-2">cd /opt/ka-enterprise && bash deploy_vps.sh</pre>
    <button class="copy-btn" onclick="copyCmd('cmd-2')">📋 Copier</button>
    <label>3 · Accéder à votre environnement</label>
    <pre id="cmd-3">http://VOTRE_VPS:8767/onboard    → nouveaux environnements
http://VOTRE_VPS:8767/admin      → dashboard (clé API ci-dessus)</pre>
    <button class="copy-btn" onclick="copyCmd('cmd-3')">📋 Copier</button>
    <div style="margin-top:14px;font-size:.75rem;color:var(--muted);line-height:1.6">
      💾 <b style="color:var(--text)">Données persistantes :</b> le script monte le volume <code class="inline">~/ka-enterprise-data</code> — vos tenants, hologrammes et clés survivent aux redémarrages et mises à jour.<br>
      🔐 <b style="color:var(--text)">Sécurité :</b> SSO + API Keys, RBAC, chiffrement AES-256 au repos, audit trail obligatoire, rate limiting.<br>
      📖 Détails complets : <a href="/README_DEPLOIEMENT_VPS.md" style="color:var(--gold)">README_DEPLOIEMENT_VPS.md</a>
    </div>
    <div style="margin-top:16px;display:flex;gap:10px">
      <button class="btn" onclick="nextStep(4)">← Retour</button>
      <a class="btn btn-p" href="/">🏠 Terminer</a>
    </div>
  </div>
</div>

<script>
const EXAMPLES = [
  "Nous sommes une clinique privée avec un service de pharmacie, des laboratoires d'analyses biologiques et un pôle administratif qui gère les dossiers patients et le personnel soignant.",
  "Cabinet d'avocats spécialisé en droit des affaires, droit du travail et conformité réglementaire, avec gestion de contentieux pour les PME.",
  "Nous développons des logiciels SaaS, gérons l'infrastructure cloud et la cybersécurité de nos clients, avec une équipe data et intelligence artificielle.",
  "Usine de fabrication industrielle avec lignes de production, contrôle qualité certifié ISO 9001 et maintenance préventive des machines.",
  "Commerce en ligne avec boutique physique, marketing multi-canaux, gestion des stocks et service client.",
];
let analysis = null;   // résultat de l'analyse
let created = null;    // résultat de la création
let apiKey = '';

function $(id){ return document.getElementById(id); }
function nextStep(n){
  for (let i=1;i<=5;i++){ $('panel'+i).classList.toggle('hidden', i!==n); $('st'+i).classList.toggle('active', i===n); $('st'+i).classList.toggle('done', i<n); }
  window.scrollTo({top:0, behavior:'smooth'});
}
function useExample(i){ $('f-desc').value = EXAMPLES[i]; }

async function api(path, opts={}){
  const h = opts.headers || {};
  if (apiKey) h['X-API-Key'] = apiKey;
  const r = await fetch('/api/enterprise' + path, {...opts, headers:{...h, 'Content-Type':'application/json'}});
  return r.json();
}

async function analyzeEnv(){
  const desc = $('f-desc').value.trim();
  if (desc.length < 20){ $('analyze-err').textContent = 'Décrivez votre environnement (au moins 20 caractères).'; return; }
  $('analyze-err').textContent = '';
  $('loading').style.display = 'flex';
  const r = await api('/onboard/analyze', {method:'POST', body:JSON.stringify({description:desc, secteur:$('f-secteur').value})});
  $('loading').style.display = 'none';
  if (r.error){ $('analyze-err').textContent = 'Erreur: ' + r.error; return; }
  analysis = r;
  renderSectors(r);
  nextStep(3);
}

function renderSectors(r){
  const box = $('sectors');
  if (!r.secteurs.length){ box.innerHTML = '<div style="color:var(--muted);font-size:.8rem">'+(r.message||'Aucun secteur reconnu.')+'</div>'; return; }
  box.innerHTML = r.secteurs.map(s=>`
    <div class="sector-box">
      <div class="sector-head"><strong>${s.label}</strong><span class="score">détecté · score ${s.score}</span></div>
      ${s.holograms.map(h=>`
        <div class="holo">
          <input type="checkbox" checked data-sujet="${h.sujet.replace(/"/g,'&quot;')}">
          <div><div class="t">🧠 ${h.sujet}</div><div class="d">${h.description}</div></div>
          <span class="tag">🌐 prêt à répondre</span>
        </div>`).join('')}
    </div>`).join('');
}

async function createEnv(){
  const name = $('f-name').value.trim();
  const email = $('f-email').value.trim();
  if (!name || !email){ $('create-err').textContent = 'Nom de l\'entreprise et email requis (étape 1).'; nextStep(1); return; }
  const sujets = [...document.querySelectorAll('#sectors input[type=checkbox]:checked')].map(c=>c.dataset.sujet);
  if (!sujets.length){ $('create-err').textContent = 'Sélectionnez au moins un hologramme.'; return; }
  $('create-err').textContent = '';
  $('loading').style.display = 'flex';
  $('loading').querySelector('div').textContent = 'Création des hologrammes ondulatoires…';
  const r = await api('/onboard', {method:'POST', body:JSON.stringify({
    name, email, description:$('f-desc').value.trim(), secteur:$('f-secteur').value, holograms:sujets,
  })});
  $('loading').style.display = 'none';
  $('loading').querySelector('div').textContent = 'Analyse ondulatoire en cours…';
  if (r.error){ $('create-err').textContent = 'Erreur: ' + r.error; return; }
  created = r;
  apiKey = r.tenant.api_key || '';
  renderCreated(r);
  nextStep(4);
}

function renderCreated(r){
  const depts = r.departments || [];
  const covCls = c => c >= 0.6 ? 'good' : (c >= 0.3 ? 'mid' : 'bad');
  const rows = depts.map(d=>{
    const c = d.couverture && d.couverture.couverture != null ? d.couverture.couverture : 0;
    return `<tr>
      <td><strong>${d.sujet}</strong></td>
      <td>${d.secteur}</td>
      <td>${d.facts}</td>
      <td class="cov ${covCls(c)}">${(c*100).toFixed(0)}%</td>
    </tr>`;
  }).join('');
  const seeded = depts.filter(d=>d.facts>0).length;
  $('created').innerHTML = `
    <div class="keybox">
      <div style="font-size:.65rem;color:var(--muted);min-width:90px">🔑 Votre clé API</div>
      <code id="api-key">${r.tenant.api_key || ''}</code>
      <button class="copy-btn" onclick="copyKey()">📋 Copier</button>
    </div>
    <p style="font-size:.75rem;color:var(--muted);margin-bottom:10px">Utilisez cette clé dans le dashboard admin (champ « API Key » en haut à droite) ou dans vos intégrations (header <code class="inline">X-API-Key</code>).</p>
    <table>
      <thead><tr><th>Hologramme (département)</th><th>Secteur</th><th>Faits</th><th>Couverture</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
    ${seeded===0 ? '<p class="ok" style="margin-top:10px">⚠ Les faits s\'enrichissent en arrière-plan — ingérez vos documents (onglet Ingestion du dashboard) pour compléter.</p>' : ''}
    <p style="font-size:.7rem;color:var(--muted);margin-top:10px">La couverture mesure la complétude des facettes (symptômes, causes, protocoles…) de chaque hologramme — <span style="color:var(--gold)">plus vous ingérez, plus elle monte</span>.</p>
    <div style="margin-top:12px">
      <div style="font-size:.7rem;color:var(--muted);margin-bottom:6px">📊 <b style="color:var(--text)">Formatage des données</b> — générez immédiatement un Excel de ce département (liste + agrégats, feuille Résumé) :</div>
      ${depts.map(d=>`<button class="btn" style="font-size:.7rem;padding:6px 12px;margin:3px" onclick="demoExcel('${d.id}','${d.sujet}')">📊 Excel : ${d.sujet}</button>`).join('')}
    </div>`;
  const sel = $('t-dept');
  sel.innerHTML = depts.map(d=>`<option value="${d.id}">${d.sujet}</option>`).join('');
}

async function testAsk(){
  const dept = $('t-dept').value;
  const q = $('t-question').value.trim();
  if (!dept || !q) return;
  const r = await api(`/departments/${dept}/ask`, {method:'POST', body:JSON.stringify({question:q})});
  const a = $('t-answer');
  a.classList.remove('hidden');
  a.innerHTML = r.error
    ? `<div class="q">${q}</div><div style="color:var(--red)">${r.error}</div>`
    : `<div class="q">${r.question}</div>
       <div>${r.answer}</div>
       <div style="font-size:.68rem;color:var(--muted);margin-top:8px">Confiance : ${(r.confidence*100).toFixed(0)}% · département ${r.department} · ${r.elapsed_ms}ms</div>`;
}

function copyKey(){
  const k = $('api-key').textContent.trim();
  navigator.clipboard.writeText(k).catch(()=>{});
  const b = event.target; b.textContent = '✅ Copié'; setTimeout(()=>b.textContent='📋 Copier', 1500);
}
function copyCmd(id){
  const txt = $(id).textContent;
  navigator.clipboard.writeText(txt).catch(()=>{});
  const b = event.target; b.textContent = '✅ Copié'; setTimeout(()=>b.textContent='📋 Copier', 1500);
}
async function demoExcel(id, sujet){
  const url = `/api/enterprise/departments/${id}/export?question=${encodeURIComponent('liste des informations sur ' + sujet)}&format=xlsx`;
  const r = await fetch(url, {headers: apiKey ? {'X-API-Key': apiKey} : {}});
  if (!r.ok) return alert('Erreur — le département doit contenir des données ingérées.');
  const blob = await r.blob();
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'apercu_' + sujet.replace(/\W+/g,'_') + '.xlsx';
  a.click();
}
</script>
</body>
</html>'''


# ═══════════════════════════════════════════════════════════════════════════════
# INTERFACE ADMIN HTML
# ═══════════════════════════════════════════════════════════════════════════════

def _admin_html():
    return r'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KA Enterprise — Administration</title>
<style>
:root{--bg:#0a0a0f;--surface:#14141f;--border:#2a2a3a;--gold:#c9a84c;--text:#d4c8a0;--muted:#888;--green:#00d2a0;--red:#e74c3c;--accent:#6c5ce7}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
.header{background:var(--surface);border-bottom:1px solid var(--border);padding:16px 24px;display:flex;justify-content:space-between;align-items:center}
.header h1{font-size:1.2rem;color:var(--gold)}.header span{font-size:.75rem;color:var(--muted)}
.container{max-width:1400px;margin:0 auto;padding:24px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}
.grid-4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px}
.card h3{font-size:.9rem;color:var(--gold);margin-bottom:12px}
.card h4{font-size:.8rem;color:var(--text);margin:8px 0 4px}
.stat{text-align:center}.stat .val{font-size:1.8rem;font-weight:700;color:var(--gold)}.stat .lbl{font-size:.65rem;color:var(--muted);margin-top:4px}
.btn{padding:8px 16px;border-radius:6px;border:1px solid var(--border);background:var(--surface);color:var(--text);cursor:pointer;font:inherit;font-size:.75rem}
.btn:hover{border-color:var(--gold)}.btn-p{background:var(--gold);color:#000;font-weight:600}
table{width:100%;border-collapse:collapse;font-size:.75rem}
th,td{padding:8px 12px;text-align:left;border-bottom:1px solid var(--border)}
th{color:var(--gold);font-weight:600;font-size:.7rem;text-transform:uppercase}
td{color:var(--text)}.badge{padding:2px 8px;border-radius:10px;font-size:.6rem;font-weight:600}
.badge-admin{background:rgba(201,168,76,.2);color:var(--gold)}.badge-user{background:rgba(108,92,231,.2);color:var(--accent)}.badge-green{background:rgba(0,210,160,.2);color:var(--green)}.badge-red{background:rgba(231,76,60,.2);color:var(--red)}
.tabs{display:flex;gap:0;margin-bottom:16px;border-bottom:1px solid var(--border)}
.tab{padding:10px 20px;cursor:pointer;color:var(--muted);font-size:.8rem;border-bottom:2px solid transparent;transition:all .2s}
.tab:hover{color:var(--text)}.tab.active{color:var(--gold);border-bottom-color:var(--gold)}
.panel{display:none}.panel.active{display:block}
input,textarea,select{padding:10px;border:1px solid var(--border);border-radius:6px;background:var(--bg);color:var(--text);font:inherit;font-size:.8rem;width:100%}input:focus,textarea:focus{outline:none;border-color:var(--gold)}
.form-row{display:flex;gap:8px;margin-bottom:8px}
pre{background:var(--bg);padding:12px;border-radius:6px;font-size:.7rem;color:var(--muted);overflow-x:auto;max-height:200px}
</style>
</head>
<body>
<div class="header"><h1>🏢 KA Enterprise — Administration</h1><div style="display:flex;align-items:center;gap:8px"><input id="api-key-input" placeholder="🔑 API Key tenant" style="width:230px;font-size:.7rem;padding:6px 10px"><span id="clock"></span></div></div>
<div class="container">
  <div class="tabs">
    <div class="tab active" onclick="switchTab('dashboard')">📊 Dashboard</div>
    <div class="tab" onclick="switchTab('tenants')">🏢 Tenants</div>
    <div class="tab" onclick="switchTab('departments')">🧠 Départements</div>
    <div class="tab" onclick="switchTab('ingest')">📤 Ingestion</div>
    <div class="tab" onclick="switchTab('query')">🔍 Requêtes</div>
    <div class="tab" onclick="switchTab('docs')">📊 Données & Docs</div>
    <div class="tab" onclick="switchTab('audit')">📋 Audit</div>
    <div class="tab" onclick="switchTab('users')">👥 Utilisateurs</div>
  </div>

  <!-- Dashboard -->
  <div class="panel active" id="dashboard">
    <div class="grid-4" id="dash-stats"></div>
    <div class="grid" style="margin-top:16px">
      <div class="card"><h3>Top Départements</h3><div id="dash-top-depts"></div></div>
      <div class="card"><h3>Dernières Requêtes</h3><div id="dash-last-queries"></div></div>
    </div>
    <div class="card" style="margin-top:16px">
      <h3>🎯 Couverture des hologrammes (complétude des facettes)</h3>
      <table id="dash-cov"><thead><tr><th>Département</th><th>Faits</th><th>Couverture</th><th>Facettes manquantes</th></tr></thead><tbody></tbody></table>
    </div>
  </div>

  <!-- Tenants -->
  <div class="panel" id="tenants">
    <div class="card" style="margin-bottom:16px">
      <h3>Créer un Tenant</h3>
      <div class="form-row"><input id="new-tenant-name" placeholder="Nom de l'entreprise"><input id="new-tenant-email" placeholder="Email admin"></div>
      <button class="btn btn-p" onclick="createTenant()">Créer</button>
    </div>
    <div class="card"><h3>Tenants</h3><table id="tenants-table"><thead><tr><th>ID</th><th>Nom</th><th>Email</th><th>Dépts</th><th>API Key</th></tr></thead><tbody></tbody></table></div>
  </div>

  <!-- Départements -->
  <div class="panel" id="departments">
    <div class="card" style="margin-bottom:16px">
      <h3>Créer un Département</h3>
      <div class="form-row">
        <select id="dept-tenant"><option value="">Sélectionner un tenant</option></select>
        <input id="new-dept-name" placeholder="Nom du département">
      </div>
      <button class="btn btn-p" onclick="createDepartment()">Créer</button>
    </div>
    <div class="card"><h3>Départements</h3><table id="depts-table"><thead><tr><th>ID</th><th>Nom</th><th>Tenant</th><th>Faits</th><th>Phase Offset</th><th>Actions</th></tr></thead><tbody></tbody></table></div>
  </div>

  <!-- Ingestion -->
  <div class="panel" id="ingest">
    <div class="card">
      <h3>Ingérer des documents</h3>
      <div class="form-row">
        <select id="ingest-dept"><option value="">Département cible</option></select>
        <input id="ingest-source" placeholder="Source (ex: rapport.pdf)">
      </div>
      <textarea id="ingest-text" rows="6" placeholder="Collez le texte à ingérer..."></textarea>
      <div style="margin-top:8px;display:flex;gap:8px">
        <button class="btn btn-p" onclick="ingestText()">📝 Ingérer le texte</button>
        <input type="file" id="ingest-file" style="display:none" onchange="ingestFile()">
        <button class="btn" onclick="document.getElementById('ingest-file').click()">📁 Choisir un fichier</button>
      </div>
      <div id="ingest-result" style="margin-top:8px;font-size:.75rem"></div>
    </div>
  </div>

  <!-- Requêtes -->
  <div class="panel" id="query">
    <div class="card">
      <h3>Interroger un département</h3>
      <div class="form-row">
        <select id="query-dept"><option value="">Département</option></select>
      </div>
      <textarea id="query-text" rows="3" placeholder="Votre question..."></textarea>
      <button class="btn btn-p" onclick="askDepartment()" style="margin-top:8px">🔍 Interroger</button>
      <div id="query-result" style="margin-top:12px"></div>
    </div>
  </div>

  <!-- Données & Documents -->
  <div class="panel" id="docs">
    <div class="card" style="margin-bottom:16px">
      <h3>📊 Données privées → Excel</h3>
      <div class="form-row">
        <select id="data-dept"><option value="">Département</option></select>
        <input id="data-question" placeholder="Ex : liste des clients / chiffre d'affaires total / moyenne des montants…">
      </div>
      <div style="display:flex;gap:8px;margin-top:8px">
        <button class="btn btn-p" onclick="dataPreview()">🔍 Aperçu</button>
        <button class="btn" onclick="dataExport('xlsx')">⬇️ Excel (.xlsx)</button>
        <button class="btn" onclick="dataExport('csv')">⬇️ CSV (.csv)</button>
      </div>
      <div id="data-preview" style="margin-top:10px"></div>
    </div>

    <div class="card" style="margin-bottom:16px">
      <h3>✍️ Préparer un texte</h3>
      <div class="form-row">
        <select id="comp-dept"><option value="">Département</option></select>
        <select id="comp-format">
          <option value="rapport">Rapport</option>
          <option value="email">Email</option>
          <option value="compte_rendu">Compte-rendu</option>
          <option value="lettre">Lettre</option>
          <option value="note">Note interne</option>
        </select>
      </div>
      <div class="form-row">
        <input id="comp-objet" placeholder="Objet (facultatif)">
        <input id="comp-dest" placeholder="Destinataire (facultatif)">
      </div>
      <textarea id="comp-brief" rows="3" placeholder="De quoi doit parler le document ? Ex : situation des clients du mois"></textarea>
      <div style="display:flex;gap:8px;margin-top:8px">
        <button class="btn btn-p" onclick="composeDoc()">✍️ Préparer</button>
        <button class="btn" onclick="composeDownload('docx')">⬇️ .docx</button>
        <button class="btn" onclick="composeDownload('txt')">⬇️ .txt</button>
      </div>
      <pre id="comp-preview" style="margin-top:10px;white-space:pre-wrap;max-height:280px"></pre>
    </div>

    <div class="card">
      <h3>🧠 Synthèse du département</h3>
      <div class="form-row">
        <select id="sum-dept"><option value="">Département</option></select>
        <button class="btn btn-p" onclick="summarizeDoc()">🧠 Synthétiser</button>
      </div>
      <pre id="sum-preview" style="margin-top:10px;white-space:pre-wrap;max-height:220px"></pre>
    </div>

    <div class="card">
      <h3>🔄 Auto-apprentissage (chaînon D)</h3>
      <p class="sub" style="font-size:.7rem">Les questions restées sans réponse sont enregistrées ; aux seuils (facette 2×, sujet 3×), l'enrichissement se déclenche automatiquement — Wikipedia + facettes manquantes, couverture recalculée. L'usage pilote la connaissance.</p>
      <div style="display:flex;gap:8px;align-items:center">
        <button class="btn btn-p" onclick="completionsRun()">▶ Traiter les complétions en attente</button>
        <button class="btn" onclick="completionsStatus()">🔄 Actualiser</button>
      </div>
      <pre id="comp-status" style="margin-top:10px;white-space:pre-wrap;max-height:200px"></pre>
    </div>
  </div>

  <!-- Audit -->
  <div class="panel" id="audit">
    <div class="card"><h3>Journal d'Audit</h3><table id="audit-table"><thead><tr><th>Heure</th><th>Utilisateur</th><th>Question</th><th>Confiance</th><th>Response ID</th></tr></thead><tbody></tbody></table></div>
  </div>

  <!-- Utilisateurs -->
  <div class="panel" id="users">
    <div class="card" style="margin-bottom:16px">
      <h3>Créer un Utilisateur</h3>
      <div class="form-row">
        <input id="new-user-email" placeholder="Email"><input id="new-user-name" placeholder="Nom">
      </div>
      <div class="form-row">
        <select id="new-user-role"><option value="admin">Admin</option><option value="manager">Manager</option><option value="user" selected>Utilisateur</option><option value="auditor">Auditeur</option><option value="readonly">Lecture seule</option></select>
        <select id="new-user-tenant"><option value="">Tenant</option></select>
      </div>
      <button class="btn btn-p" onclick="createUser()">Créer</button>
    </div>
    <div class="card"><h3>Utilisateurs</h3><table id="users-table"><thead><tr><th>ID</th><th>Email</th><th>Nom</th><th>Rôle</th><th>Depts</th><th>API Key</th></tr></thead><tbody></tbody></table></div>
  </div>
</div>

<script>
const API = '/api/enterprise';
let token = '';

async function api(path, opts={}) {
  const h = opts.headers || {};
  if (token) h['Authorization'] = 'Bearer ' + token;
  const r = await fetch(API + path, {...opts, headers: {...h, 'Content-Type':'application/json'}});
  return r.json();
}

function switchTab(id) {
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
  document.querySelector(`.tab[onclick*="${id}"]`).classList.add('active');
  document.getElementById(id).classList.add('active');
  if (id==='dashboard') loadDashboard();
  if (id==='tenants') loadTenants();
  if (id==='departments') loadDepartments();
  if (id==='ingest') loadDeptSelect('ingest-dept');
  if (id==='query') loadDeptSelect('query-dept');
  if (id==='docs') { loadDeptSelect('data-dept'); loadDeptSelect('comp-dept'); loadDeptSelect('sum-dept'); }
  if (id==='audit') loadAudit();
  if (id==='users') loadUsers();
}

async function loadDashboard() {
  const d = await api('/dashboard');
  document.getElementById('dash-stats').innerHTML = `
    <div class="stat"><div class="val">${d.tenants||0}</div><div class="lbl">Tenants</div></div>
    <div class="stat"><div class="val">${d.departments||0}</div><div class="lbl">Départements</div></div>
    <div class="stat"><div class="val">${d.total_facts||0}</div><div class="lbl">Faits</div></div>
    <div class="stat"><div class="val">${(d.avg_confidence*100).toFixed(0)}%</div><div class="lbl">Confiance moy.</div></div>`;
  if (d.top_departments) {
    document.getElementById('dash-top-depts').innerHTML = d.top_departments.slice(0,10).map(d=>
      `<div style="padding:4px 0;border-bottom:1px solid rgba(255,255,255,.03)"><strong>${d.name}</strong> — ${d.facts} faits</div>`).join('');
  }
  const covBody = document.querySelector('#dash-cov tbody');
  if (covBody && d.departments_detail) {
    const pct = c => (c*100).toFixed(0)+'%';
    const cls = c => c >= 0.6 ? 'badge-green' : (c >= 0.3 ? 'badge-admin' : 'badge-red');
    covBody.innerHTML = d.departments_detail.map(x=>
      `<tr><td><strong>${x.name}</strong></td><td>${x.fact_count}</td>
       <td><span class="badge ${cls(x.couverture)}">${pct(x.couverture)}</span></td>
       <td>${(x.facettes_manquantes||[]).slice(0,3).join(', ') || '—'}</td></tr>`).join('');
  }
}

async function loadTenants() {
  const data = await api('/tenants');
  const tbody = document.querySelector('#tenants-table tbody');
  tbody.innerHTML = (data.tenants||[]).map(t=>
    `<tr><td>${t.id}</td><td><strong>${t.name}</strong></td><td>${t.admin_email}</td><td>${t.departments}</td><td style="font-family:monospace;font-size:.65rem">${t.api_key||'N/A'}</td></tr>`).join('');
  loadDeptSelect('dept-tenant');
  loadDeptSelect('new-user-tenant');
}

async function loadDepartments() {
  const data = await api('/tenants');
  let all = [];
  for (const t of (data.tenants||[])) {
    const d = await api(`/tenants/${t.id}/departments`);
    all.push(...(d.departments||[]).map(d=>({...d,tenant_name:t.name})));
  }
  document.querySelector('#depts-table tbody').innerHTML = all.map(d=>
    `<tr><td>${d.id}</td><td><strong>${d.name}</strong></td><td>${d.tenant_name}</td><td>${d.fact_count}</td><td>${d.phase_offset}τ</td>
    <td><button class="btn" onclick="exportDept('${d.id}')">📥</button></td></tr>`).join('');
}

async function loadAudit() {
  const data = await api('/audit?limit=50');
  document.querySelector('#audit-table tbody').innerHTML = (data.audit_log||[]).map(e=>
    `<tr><td>${e.timestamp}</td><td>${e.user}</td><td>${e.question}</td><td>${(e.confidence*100).toFixed(0)}%</td><td style="font-family:monospace;font-size:.6rem">${e.response_id}</td></tr>`).join('');
}

async function loadUsers() {
  const data = await api('/users');
  document.querySelector('#users-table tbody').innerHTML = (data.users||[]).map(u=>
    `<tr><td>${u.id}</td><td>${u.email}</td><td>${u.name}</td><td><span class="badge badge-${u.role==='admin'?'admin':'user'}">${u.role}</span></td><td>${u.departments}</td><td style="font-family:monospace;font-size:.6rem">${u.api_key||''}</td></tr>`).join('');
}

async function loadDeptSelect(selId) {
  const sel = document.getElementById(selId); if(!sel) return;
  const tenants = await api('/tenants');
  let html = '<option value="">Sélectionner...</option>';
  for (const t of (tenants.tenants||[])) {
    try {
      const d = await api(`/tenants/${t.id}/departments`);
      for (const dept of (d.departments||[])) {
        html += `<option value="${dept.id}">${dept.name} (${t.name})</option>`;
      }
    } catch(e){}
  }
  sel.innerHTML = html;
}

function fmtNum(v){ return (typeof v==='number') ? v.toLocaleString('fr-FR') : (v??''); }

async function dataPreview() {
  const dept = document.getElementById('data-dept').value;
  const q = document.getElementById('data-question').value.trim();
  if(!dept||!q) return alert('Département et question requis');
  const r = await api(`/departments/${dept}/data`, {method:'POST', body:JSON.stringify({question:q})});
  const box = document.getElementById('data-preview');
  if (r.error) { box.innerHTML = `<span style="color:var(--red)">${r.error}</span>`; return; }
  const head = r.columns.map(c=>`<th>${c}</th>`).join('');
  const rows = r.rows.slice(0,50).map(row=>`<tr>${r.columns.map(c=>`<td>${fmtNum(row[c])}</td>`).join('')}</tr>`).join('');
  const aggs = (r.aggregates||[]).map(a=>`<span class="badge badge-admin" style="margin-right:6px">${a.libelle} : ${fmtNum(a.valeur)}</span>`).join('');
  box.innerHTML = `
    <div style="font-size:.7rem;color:var(--muted);margin-bottom:6px">${r.count} lignes · mode « ${r.mode} » · ${r.facts_utilises} faits utilisés</div>
    ${aggs}
    <table style="margin-top:8px"><thead><tr>${head}</tr></thead>
    <tbody>${rows || '<tr><td style="color:var(--muted)">Aucune donnée</td></tr>'}</tbody></table>
    ${r.count>50 ? `<div style="font-size:.65rem;color:var(--muted);margin-top:4px">… ${r.count-50} lignes supplémentaires dans le fichier Excel</div>` : ''}`;
}

async function dataExport(fmt) {
  const dept = document.getElementById('data-dept').value;
  const q = document.getElementById('data-question').value.trim();
  if(!dept||!q) return alert('Département et question requis');
  const h = {}; if (token) h['Authorization'] = 'Bearer ' + token;
  const r = await fetch(`/api/enterprise/departments/${dept}/export?question=${encodeURIComponent(q)}&format=${fmt}`, {headers:h});
  if (!r.ok) return alert('Erreur export: ' + (await r.text()).slice(0,120));
  const blob = await r.blob();
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = fmt==='xlsx' ? 'donnees.xlsx' : 'donnees.csv';
  a.click();
}

async function composeDoc() {
  const dept = document.getElementById('comp-dept').value;
  const brief = document.getElementById('comp-brief').value.trim();
  if(!dept||!brief) return alert('Département et sujet requis');
  const r = await api(`/departments/${dept}/compose`, {method:'POST', body:JSON.stringify({
    brief,
    format: document.getElementById('comp-format').value,
    objet: document.getElementById('comp-objet').value.trim(),
    destinataire: document.getElementById('comp-dest').value.trim()})});
  document.getElementById('comp-preview').textContent = r.error ? r.error : r.texte;
}

async function composeDownload(fmt) {
  const dept = document.getElementById('comp-dept').value;
  const brief = document.getElementById('comp-brief').value.trim();
  if(!dept||!brief) return alert('Département et sujet requis');
  const h = {'Content-Type':'application/json'};
  if (token) h['Authorization'] = 'Bearer ' + token;
  const r = await fetch(`/api/enterprise/departments/${dept}/compose`, {method:'POST', headers:h, body:JSON.stringify({
    brief,
    format: document.getElementById('comp-format').value,
    objet: document.getElementById('comp-objet').value.trim(),
    destinataire: document.getElementById('comp-dest').value.trim(),
    download: fmt})});
  if (!r.ok) return alert('Erreur: ' + (await r.text()).slice(0,120));
  const blob = await r.blob();
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'document.' + fmt;
  a.click();
}

async function summarizeDoc() {
  const dept = document.getElementById('sum-dept').value;
  if(!dept) return alert('Département requis');
  const r = await api(`/departments/${dept}/summarize`, {method:'POST'});
  document.getElementById('sum-preview').textContent = r.error
    ? r.error
    : r.resume + '\n\nSources : ' + Object.keys(r.sources||{}).join(', ');
}

async function completionsStatus() {
  const r = await api('/completions/status');
  document.getElementById('comp-status').textContent = JSON.stringify(r, null, 2);
}

async function completionsRun() {
  const r = await api('/completions/run', {method:'POST'});
  alert('Complétions lancées : ' + (r.lances || 0) + (r.error ? ' (' + r.error + ')' : ''));
  setTimeout(completionsStatus, 2000);
}

async function createTenant() {
  const name = document.getElementById('new-tenant-name').value.trim();
  const email = document.getElementById('new-tenant-email').value.trim();
  if(!name) return alert('Nom requis');
  const r = await api('/tenants', {method:'POST', body:JSON.stringify({name, admin_email:email})});
  alert(r.id ? 'Tenant créé ! API Key: '+r.api_key : 'Erreur: '+JSON.stringify(r));
  loadTenants(); loadDashboard();
}

async function createDepartment() {
  const tid = document.getElementById('dept-tenant').value;
  const name = document.getElementById('new-dept-name').value.trim();
  if(!tid||!name) return alert('Tenant et nom requis');
  const r = await api(`/tenants/${tid}/departments`, {method:'POST', body:JSON.stringify({name})});
  alert(r.id ? 'Département créé !' : 'Erreur');
  loadDepartments(); loadDashboard();
}

async function ingestText() {
  const dept = document.getElementById('ingest-dept').value;
  const text = document.getElementById('ingest-text').value.trim();
  const source = document.getElementById('ingest-source').value.trim() || 'api';
  if(!dept||!text) return alert('Département et texte requis');
  const r = await api(`/departments/${dept}/ingest`, {method:'POST', body:JSON.stringify({text, source})});
  document.getElementById('ingest-result').innerHTML = r.facts_ingested
    ? `<span style="color:var(--green)">✅ ${r.facts_ingested} faits ingérés (total: ${r.total_facts})</span>`
    : `<span style="color:var(--red)">Erreur: ${JSON.stringify(r)}</span>`;
  loadDepartments(); loadDashboard();
}

async function ingestFile() {
  const dept = document.getElementById('ingest-dept').value;
  const file = document.getElementById('ingest-file').files[0];
  if(!dept||!file) return;
  const fd = new FormData(); fd.append('file', file);
  const h = {}; if(token) h['Authorization'] = 'Bearer '+token;
  const r = await fetch(API+`/departments/${dept}/ingest`, {method:'POST', headers:h, body:fd});
  const data = await r.json();
  document.getElementById('ingest-result').innerHTML = data.facts_ingested
    ? `<span style="color:var(--green)">✅ ${data.facts_ingested} faits ingérés depuis ${file.name}</span>`
    : `<span style="color:var(--red)">Erreur</span>`;
}

async function askDepartment() {
  const dept = document.getElementById('query-dept').value;
  const q = document.getElementById('query-text').value.trim();
  if(!dept||!q) return;
  const r = await api(`/departments/${dept}/ask`, {method:'POST', body:JSON.stringify({question:q})});
  document.getElementById('query-result').innerHTML = `
    <div style="background:var(--bg);padding:12px;border-radius:8px">
      <div style="font-weight:600;margin-bottom:8px">${r.question}</div>
      <div style="color:var(--gold);margin-bottom:4px">${r.answer}</div>
      <div style="font-size:.7rem;color:var(--muted)">Confiance: ${(r.confidence*100).toFixed(0)}% | Dept: ${r.department} | ${r.elapsed_ms}ms</div>
      ${r.sources.length ? '<div style="font-size:.65rem;color:var(--muted);margin-top:4px">Sources: '+r.sources.join(', ')+'</div>' : ''}
    </div>`;
}

async function createUser() {
  const email = document.getElementById('new-user-email').value.trim();
  const name = document.getElementById('new-user-name').value.trim();
  const role = document.getElementById('new-user-role').value;
  const tid = document.getElementById('new-user-tenant').value;
  if(!email) return alert('Email requis');
  const r = await api('/users', {method:'POST', body:JSON.stringify({email, name, role, tenant_id:tid})});
  alert(r.id ? 'Utilisateur créé ! API Key: '+r.api_key : 'Erreur');
  loadUsers();
}

async function exportDept(id) { window.open(API+`/departments/${id}/export`); }

// 🔑 API Key tenant — collée ici, elle donne accès aux données du tenant
const savedKey = localStorage.getItem('ka_api_key') || '';
if (savedKey) { token = savedKey; document.getElementById('api-key-input').value = savedKey; }
document.getElementById('api-key-input').addEventListener('change', e => {
  token = e.target.value.trim();
  localStorage.setItem('ka_api_key', token);
  loadDashboard(); loadTenants();
});

// Init
setInterval(()=>document.getElementById('clock').textContent=new Date().toLocaleString('fr-FR'),1000);
loadDashboard();
</script>
</body>
</html>'''


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMARRAGE
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='KA Enterprise Server')
    parser.add_argument('--port', type=int, default=8767)
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    
    print("=" * 60)
    print("  🏢 KA Enterprise Server v4.0")
    print("=" * 60)
    print(f"  Port        : {args.port}")
    print(f"  Dashboard   : http://localhost:{args.port}/admin")
    print(f"  API Docs    : http://localhost:{args.port}/docs")
    print(f"  API Info    : http://localhost:{args.port}/api/enterprise/info")
    print(f"  Tenants     : {len(engine.tenants)}")
    print(f"  Users       : {len(rbac.users)}")
    print(f"  Sécurité    : SSO, RBAC, AES-256, Rate Limit, Audit")
    print("=" * 60)
    
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)
