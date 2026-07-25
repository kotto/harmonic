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
    
    return jsonify({
        'question': result.question,
        'answer': result.answer,
        'confidence': result.confidence,
        'sources': result.sources,
        'department': result.department,
        'response_id': result.response_id,
        'elapsed_ms': result.elapsed_ms,
        'admitted_uncertainty': result.admitted_uncertainty,
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
    return jsonify(engine.get_dashboard())


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
<div class="header"><h1>🏢 KA Enterprise — Administration</h1><span id="clock"></span></div>
<div class="container">
  <div class="tabs">
    <div class="tab active" onclick="switchTab('dashboard')">📊 Dashboard</div>
    <div class="tab" onclick="switchTab('tenants')">🏢 Tenants</div>
    <div class="tab" onclick="switchTab('departments')">🧠 Départements</div>
    <div class="tab" onclick="switchTab('ingest')">📤 Ingestion</div>
    <div class="tab" onclick="switchTab('query')">🔍 Requêtes</div>
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
