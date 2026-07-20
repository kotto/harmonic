"""
🏢 Enterprise Server — Harmonic AI pour Entreprises
=====================================================
Serveur multi-tenant avec :
  - Authentification par token entreprise
  - Patterns de diagnostic personnalisés par tenant
  - Apprentissage continu (chaque bug résolu enrichit le tenant)
  - API REST complète
  - Dashboard web

Endpoints :
  POST /api/v2/enterprise/debug    — diagnostic
  POST /api/v2/enterprise/learn    — apprentissage
  GET  /api/v2/enterprise/stats    — statistiques du tenant
  GET  /api/v2/enterprise/patterns — patterns personnalisés
  POST /api/v2/enterprise/feedback — feedback (corrige un diagnostic)
"""

import sys, os, json, time, uuid, hashlib
from pathlib import Path
from typing import Dict
from collections import defaultdict
import logging

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from harmonic_ai_v2 import HarmonicAIv2, DebugResult

# ════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

PORT = int(os.environ.get("PORT", 8842))

# ════════════════════════════════════════════════════════════════
# IA GLOBALE (partagée, patterns de base)
# ════════════════════════════════════════════════════════════════

print("=" * 55)
print("  🏢 ENTERPRISE SERVER — Harmonic AI v2")
print("=" * 55)

_global_ai = HarmonicAIv2()

# ════════════════════════════════════════════════════════════════
# TENANTS (multi-entreprise)
# ════════════════════════════════════════════════════════════════

class TenantStore:
    def __init__(self):
        self.tenants: Dict[str, dict] = {}  # tenant_id → config
        self.patterns: Dict[str, Dict[str, list]] = {}  # tenant_id → {name: [symptoms]}
        self.history: Dict[str, list] = {}  # tenant_id → [diagnostics]
        self._load()
    
    def create(self, name: str) -> dict:
        tid = f"tenant_{uuid.uuid4().hex[:12]}"
        api_key = f"hk_{hashlib.sha256(f'{tid}{time.time()}'.encode()).hexdigest()[:24]}"
        self.tenants[tid] = {
            "tenant_id": tid, "name": name, "api_key": api_key,
            "created": time.time(), "requests": 0, "learned": 0
        }
        self.patterns[tid] = {}
        self.history[tid] = []
        self._save()
        return self.tenants[tid]
    
    def get(self, tenant_id: str) -> dict:
        return self.tenants.get(tenant_id)
    
    def validate(self, api_key: str) -> str:
        for tid, t in self.tenants.items():
            if t["api_key"] == api_key:
                return tid
        return ""
    
    def add_pattern(self, tenant_id: str, name: str, symptoms: list):
        if tenant_id not in self.patterns:
            self.patterns[tenant_id] = {}
        if name not in self.patterns[tenant_id]:
            self.patterns[tenant_id][name] = []
        self.patterns[tenant_id][name].extend(symptoms)
        self._save()
    
    def get_patterns(self, tenant_id: str) -> dict:
        return self.patterns.get(tenant_id, {})
    
    def add_history(self, tenant_id: str, entry: dict):
        if tenant_id not in self.history:
            self.history[tenant_id] = []
        self.history[tenant_id].append(entry)
        if len(self.history[tenant_id]) > 1000:
            self.history[tenant_id] = self.history[tenant_id][-1000:]
        self._save()
    
    def get_history(self, tenant_id: str, limit: int = 20) -> list:
        h = self.history.get(tenant_id, [])
        return h[-limit:]
    
    def get_stats(self, tenant_id: str) -> dict:
        t = self.tenants.get(tenant_id, {})
        h = self.history.get(tenant_id, [])
        return {
            "tenant": t.get("name", ""),
            "requests": t.get("requests", 0),
            "learned": t.get("learned", 0),
            "history_size": len(h),
            "custom_patterns": len(self.patterns.get(tenant_id, {})),
        }
    
    def _save(self):
        try:
            path = _ENGINE_DIR / "data" / "enterprise_tenants.json"
            data = {
                "tenants": self.tenants,
                "patterns": self.patterns,
                "history": {tid: h[-500:] for tid, h in self.history.items()},
            }
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            log.warning(f"Sauvegarde tenants ignorée: {e}")
    
    def _load(self):
        try:
            path = _ENGINE_DIR / "data" / "enterprise_tenants.json"
            if path.exists():
                with open(path, 'r') as f:
                    data = json.load(f)
                self.tenants = data.get("tenants", {})
                self.patterns = data.get("patterns", {})
                self.history = data.get("history", {})
                log.info(f"Tenants chargés: {len(self.tenants)}")
        except Exception:
            pass


# Initialiser les tenants
tenants = TenantStore()

# Tenant démo par défaut
if not tenants.tenants:
    demo = tenants.create("Demo Company")
    log.info(f"Tenant démo créé: {demo['tenant_id']} (clé: {demo['api_key'][:8]}...)")
    # Ajouter des patterns personnalisés pour le tenant démo
    tenants.add_pattern(demo["tenant_id"], "Bug Métier Paiement", [
        "le paiement est refusé sans raison",
        "double débit sur la carte bancaire",
        "le montant affiché ne correspond pas au panier",
        "payment declined but amount still charged",
        "invoice total mismatch after discount applied",
    ])


# ════════════════════════════════════════════════════════════════
# MIDDLEWARE — Auth
# ════════════════════════════════════════════════════════════════

def require_tenant(f):
    """Décorateur qui valide l'API key du tenant."""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get("X-API-Key", "") or request.args.get("api_key", "")
        tenant_id = tenants.validate(api_key)
        if not tenant_id:
            return jsonify({"error": "API key invalide. Utilisez X-API-Key header."}), 401
        request.tenant_id = tenant_id
        return f(*args, **kwargs)
    return wrapper


# ════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ════════════════════════════════════════════════════════════════

@app.route('/api/v2/enterprise/debug', methods=['POST'])
@require_tenant
def debug():
    """
    Diagnostic de bug — endpoint principal.
    
    Body: {
        "symptom": "NullPointerException when...",
        "language": "auto",        // "fr", "en", "auto"
        "context": "code snippet"  // optionnel
    }
    """
    data = request.get_json(force=True, silent=True) or {}
    symptom = data.get("symptom", "").strip()
    
    if not symptom:
        return jsonify({"error": "Champ 'symptom' requis"}), 422
    
    tid = request.tenant_id
    t = tenants.get(tid)
    t["requests"] = t.get("requests", 0) + 1
    
    t0 = time.time()
    
    # 1. Diagnostic standard (encodeur génératif)
    result = _global_ai.debug(symptom)
    
    # 2. Enrichir avec les patterns personnalisés du tenant
    custom = tenants.get_patterns(tid)
    if custom:
        # Vérifier si un pattern custom matche mieux
        psi = _global_ai.encoder.encode(symptom)
        best_custom = None
        best_score = 0
        for name, syms in custom.items():
            for sym in syms:
                s = _global_ai.encoder.interference(psi, _global_ai.encoder.encode(sym))
                if s > best_score:
                    best_score = s
                    best_custom = name
        
        if best_custom and best_score > result.confidence * 1.2:
            result.interference_type = f"[{t['name']}] {best_custom}"
            result.confidence = float(best_score)
            result.learning_applied = True
    
    latency_ms = (time.time() - t0) * 1000
    
    # Historique
    tenants.add_history(tid, {
        "time": time.time(),
        "symptom": symptom[:100],
        "diagnosis": result.interference_type,
        "confidence": result.confidence,
        "latency_ms": latency_ms,
    })
    
    return jsonify({
        "diagnosis": result.interference_type,
        "confidence": round(result.confidence, 3),
        "explanation": result.explanation,
        "strategy": result.strategy,
        "action": result.action,
        "learning_applied": result.learning_applied,
        "latency_ms": round(latency_ms, 1),
        "tenant": t["name"],
    })


@app.route('/api/v2/enterprise/learn', methods=['POST'])
@require_tenant
def learn():
    """
    Apprentissage d'un nouveau cas.
    
    Body: {
        "symptom": "description du bug",
        "diagnosis": "Onde Fantome",   // diagnostic correct (vérifié)
        "category": "custom"           // "standard" ou "custom"
    }
    """
    data = request.get_json(force=True, silent=True) or {}
    symptom = data.get("symptom", "").strip()
    diagnosis = data.get("diagnosis", "").strip()
    category = data.get("category", "custom")
    
    if not symptom or not diagnosis:
        return jsonify({"error": "Champs 'symptom' et 'diagnosis' requis"}), 422
    
    tid = request.tenant_id
    t = tenants.get(tid)
    
    if category == "custom":
        # Ajouter comme pattern personnalisé du tenant
        tenants.add_pattern(tid, diagnosis, [symptom])
    
    # Apprentissage global
    result = _global_ai.learn(symptom, diagnosis)
    
    t["learned"] = t.get("learned", 0) + 1
    tenants._save()
    
    return jsonify({
        "status": "learned",
        "symptom": symptom[:80],
        "diagnosis": diagnosis,
        "total_learned": result["total_learned"],
        "tenant_learned": t["learned"],
    })


@app.route('/api/v2/enterprise/stats', methods=['GET'])
@require_tenant
def stats():
    """Statistiques du tenant + globales."""
    tid = request.tenant_id
    return jsonify({
        "tenant": tenants.get_stats(tid),
        "global": _global_ai.get_stats(),
        "recent": tenants.get_history(tid, limit=10),
    })


@app.route('/api/v2/enterprise/patterns', methods=['GET'])
@require_tenant
def get_patterns():
    """Liste les patterns du tenant."""
    tid = request.tenant_id
    patterns = tenants.get_patterns(tid)
    return jsonify({
        "tenant": tenants.get(tid)["name"],
        "custom_patterns": {name: len(syms) for name, syms in patterns.items()},
        "standard_patterns": list(_global_ai.patterns.keys()),
        "learned_patterns": list(_global_ai.learned_patterns.keys()),
    })


@app.route('/api/v2/enterprise/feedback', methods=['POST'])
@require_tenant
def feedback():
    """
    Feedback : corrige un diagnostic incorrect.
    Le système APPREND de son erreur.
    
    Body: {
        "symptom": "description du bug",
        "predicted": "diagnostic donné par l'IA",
        "correct": "diagnostic correct"
    }
    """
    data = request.get_json(force=True, silent=True) or {}
    symptom = data.get("symptom", "").strip()
    predicted = data.get("predicted", "").strip()
    correct = data.get("correct", "").strip()
    
    if not symptom or not correct:
        return jsonify({"error": "Champs requis"}), 422
    
    tid = request.tenant_id
    
    # Apprendre la correction
    _global_ai.learn(symptom, correct)
    tenants.add_pattern(tid, correct, [symptom])
    
    return jsonify({
        "status": "corrected",
        "symptom": symptom[:80],
        "was": predicted,
        "now": correct,
        "message": "✅ Correction apprise. Le système ne fera plus cette erreur."
    })


@app.route('/api/v2/enterprise/tenant', methods=['POST'])
def create_tenant():
    """Crée un nouveau tenant (sans auth)."""
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Nom d'entreprise requis"}), 422
    
    tenant = tenants.create(name)
    return jsonify(tenant)


@app.route('/api/v2/enterprise/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "version": "v2",
        "tenants": len(tenants.tenants),
        "uptime": time.time() - _global_ai.abc._cache.get("_start", time.time()),
    })


# ════════════════════════════════════════════════════════════════
# FRONTEND DASHBOARD
# ════════════════════════════════════════════════════════════════

@app.route('/')
def dashboard():
    """Dashboard entreprise."""
    return send_from_directory(
        str(_ENGINE_DIR / "www"),
        "enterprise_dashboard.html"
    )


@app.route('/www/<path:filename>')
def serve_static(filename):
    return send_from_directory(str(_ENGINE_DIR / "www"), filename)


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    log.info(f"🌐 Serveur Enterprise: http://localhost:{PORT}")
    log.info(f"💡 Dashboard: http://localhost:{PORT}/")
    log.info(f"🔑 Tenants: {len(tenants.tenants)}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
