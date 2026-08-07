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
    tenants.add_pattern(demo["tenant_id"], "Bug Métier Paiement", [
        "le paiement est refusé sans raison",
        "double débit sur la carte bancaire",
        "le montant affiché ne correspond pas au panier",
        "payment declined but amount still charged",
        "invoice total mismatch after discount applied",
    ])

# ── 🧠 Harmoniq Enterprise Holograms ──────────────────────────
_enterprise_holograms = None
_HOLOGRAMS_READY = False
try:
    from enterprise_holograms import EnterpriseHolograms
    _enterprise_holograms = EnterpriseHolograms()
    # Vérifier si des hologrammes existent déjà
    router_path = _enterprise_holograms.holograms_dir / "router.json"
    if router_path.exists():
        _enterprise_holograms._ready = True
        _HOLOGRAMS_READY = True
        import json
        with open(router_path) as f:
            r = json.load(f)
        log.info(f"🧠 Hologrammes entreprise: {len(r['domains'])} domaines chargés")
    else:
        log.info("🧠 Hologrammes entreprise: non entraînés (lancez .train_all())")
except Exception as e:
    log.info(f"🧠 Hologrammes entreprise: non disponibles ({e})")


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
# 📤 UPLOAD & INGESTION — Construction de l'hologramme entreprise
# ════════════════════════════════════════════════════════════════

import re as _re
from werkzeug.utils import secure_filename

UPLOAD_DIR = _ENGINE_DIR / "data" / "enterprise_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {'txt', 'log', 'md', 'csv', 'json', 'xml', 'py', 'js', 'ts', 
                      'java', 'go', 'rs', 'rb', 'swift', 'kt', 'cs', 'cpp', 'h',
                      'html', 'css', 'yaml', 'yml', 'toml', 'cfg', 'ini', 'env',
                      'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(filepath: str, filename: str) -> str:
    """Extrait le texte d'un fichier selon son type."""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if ext == 'pdf':
        try:
            import PyPDF2
            text = ""
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
            return text
        except ImportError:
            return "[PDF nécessite PyPDF2] Contenu binaire non extrait."
    
    if ext == 'docx':
        try:
            import docx
            doc = docx.Document(filepath)
            return "\n".join(p.text for p in doc.paragraphs)
        except ImportError:
            return "[DOCX nécessite python-docx] Contenu binaire non extrait."
    
    # Fichiers texte
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return ""


def ingest_file_to_patterns(content: str, filename: str, tenant_id: str) -> dict:
    """
    Analyse le contenu d'un fichier et crée des patterns personnalisés.
    
    Stratégies par type de fichier :
      - Logs → extraction d'erreurs
      - Code → patterns d'exception, null safety, concurrence
      - Docs → extraction de vocabulaire métier
      - CSV/JSON → patterns de données
    """
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    stats = {"patterns_created": 0, "symptoms_found": 0, "filename": filename}
    
    # ── LOGS : extraction d'erreurs ──
    if ext in ('log', 'txt'):
        error_lines = _re.findall(r'(?i)(error|exception|fail|crash|panic|fatal|warn)[^\n]{10,200}', content)
        patterns = defaultdict(list)
        for line in error_lines:
            line_lower = line.lower()
            if any(kw in line_lower for kw in ['null', 'undefined', 'none', 'missing', 'not found']):
                patterns["Absence Fréquence"].append(line[:120])
            elif any(kw in line_lower for kw in ['timeout', 'overload', 'exceed', 'limit', 'rate limit']):
                patterns["Saturation"].append(line[:120])
            elif any(kw in line_lower for kw in ['race', 'deadlock', 'concurrent', 'lock', 'mutex']):
                patterns["Collision Phase"].append(line[:120])
            elif any(kw in line_lower for kw in ['memory', 'leak', 'heap', 'oom', 'out of memory']):
                patterns["Onde Fantome"].append(line[:120])
            elif any(kw in line_lower for kw in ['cache', 'stale', 'outdated', 'expired', 'session']):
                patterns["Déphasage Temporel"].append(line[:120])
            elif any(kw in line_lower for kw in ['injection', 'xss', 'csrf', 'sanitize', 'validate', 'escape']):
                patterns["Résonance Parasite"].append(line[:120])
            elif any(kw in line_lower for kw in ['slow', 'performance', 'bottleneck', 'latency', 'timeout']):
                patterns["Interférence Multiple"].append(line[:120])
            elif any(kw in line_lower for kw in ['regression', 'broke', 'was working', 'update', 'deploy']):
                patterns["Résonance Forcée"].append(line[:120])
            else:
                patterns["Exception Technique"].append(line[:120])
        
        for name, syms in patterns.items():
            if syms:
                tenants.add_pattern(tenant_id, f"📄 {filename}: {name}", syms[:30])
                stats["patterns_created"] += 1
                stats["symptoms_found"] += len(syms[:30])
    
    # ── CODE SOURCE : patterns structurels ──
    elif ext in ('py', 'js', 'ts', 'java', 'go', 'rs', 'rb', 'swift', 'kt', 'cs', 'cpp', 'h'):
        code_patterns = {
            "🔒 Null Safety": [
                r'NullPointerException', r'NullReference', r'NoneType', r'undefined is not',
                r'cannot read propert', r'Optional\.empty', r'\.nil\b', r'null\s*!',
            ],
            "🔄 Concurrency": [
                r'race condition', r'deadlock', r'ConcurrentModification', r'synchronized',
                r'@GuardedBy', r'Lock\(', r'Mutex', r'Semaphore', r'thread-safe',
            ],
            "💧 Resource Leak": [
                r'memory leak', r'out of memory', r'Heap.*exceed', r'close\(\)',
                r'dispose\(\)', r'try-with-resources', r'context manager', r'defer\s+',
            ],
            "🛡️ Error Handling": [
                r'catch\s*\(', r'except\s+', r'rescue\s+', r'panic\(', r'throw\s+new',
                r'raise\s+', r'\.onError', r'\.catchError',
            ],
            "🔐 Input Safety": [
                r'sanitize', r'validate', r'escape', r'SQL injection', r'XSS', r'CSRF',
                r'prepared\s*statement', r'input\.check',
            ],
        }
        for pattern_name, regexes in code_patterns.items():
            symptoms = set()
            for regex in regexes:
                matches = _re.findall(regex, content, _re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple): match = match[0]
                    idx = content.find(str(match))
                    ctx = content[max(0,idx-40):min(len(content),idx+60)].replace('\n',' ')
                    symptoms.add(f"{pattern_name}: {ctx.strip()[:120]}")
            if symptoms:
                tenants.add_pattern(tenant_id, f"📄 {filename}: {pattern_name}", list(symptoms)[:20])
                stats["patterns_created"] += 1
                stats["symptoms_found"] += min(len(symptoms), 20)
    
    # ── DOCS / MD / JSON : vocabulaire métier ──
    elif ext in ('md', 'json', 'csv', 'yaml', 'yml', 'xml', 'html'):
        # Extraction de termes techniques (mots en camelCase, snake_case, termes > 8 lettres)
        tech_terms = _re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b|\b[a-z]+_[a-z]+_[a-z]+\b|\b[A-Z]{2,8}\b', content)
        if tech_terms:
            unique_terms = list(set(tech_terms))[:100]
            # Créer un pattern "Vocabulaire Métier" avec ces termes
            tenants.add_pattern(tenant_id, f"📄 {filename}: Vocabulaire Métier", unique_terms)
            stats["patterns_created"] += 1
            stats["symptoms_found"] += len(unique_terms)
        
        # JSON/CSV : extraire les clés comme concepts
        if ext in ('json', 'csv'):
            try:
                if ext == 'json':
                    data = json.loads(content)
                    if isinstance(data, dict):
                        keys = list(data.keys())[:50]
                        tenants.add_pattern(tenant_id, f"📄 {filename}: Structure", 
                                          [f"champ: {k}" for k in keys])
                        stats["patterns_created"] += 1
                        stats["symptoms_found"] += len(keys)
                elif ext == 'csv':
                    header = content.split('\n')[0] if '\n' in content else ''
                    cols = [c.strip() for c in header.split(',') if c.strip()]
                    if cols:
                        tenants.add_pattern(tenant_id, f"📄 {filename}: Colonnes",
                                          [f"colonne: {c}" for c in cols[:30]])
                        stats["patterns_created"] += 1
                        stats["symptoms_found"] += len(cols[:30])
            except Exception:
                pass
    
    # ── PDF / DOCX : déjà extrait en texte, analyser comme logs ──
    elif ext in ('pdf', 'docx'):
        # Analyser comme des logs/docs
        error_lines = _re.findall(r'(?i)(error|exception|bug|issue|problem|fail|crash)[^\n]{10,200}', content)
        if error_lines:
            tenants.add_pattern(tenant_id, f"📄 {filename}: Erreurs", error_lines[:30])
            stats["patterns_created"] += 1
            stats["symptoms_found"] += min(len(error_lines), 30)
    
    return stats


@app.route('/api/v2/enterprise/upload', methods=['POST'])
@require_tenant
def upload_files():
    """
    📤 Upload de fichiers pour construire l'hologramme entreprise.
    
    Accepte : PDF, DOCX, TXT, LOG, MD, CSV, JSON, code source (py, js, java, etc.)
    Max : 10 fichiers par requête, 10 Mo par fichier.
    
    L'IA analyse chaque fichier, extrait les patterns, et construit
    l'hologramme personnalisé de l'entreprise.
    """
    tid = request.tenant_id
    
    if 'files' not in request.files:
        return jsonify({"error": "Aucun fichier. Utilisez le champ 'files' (multipart)."}), 422
    
    files = request.files.getlist('files')
    if not files:
        return jsonify({"error": "Liste de fichiers vide."}), 422
    
    results = []
    total_patterns = 0
    total_symptoms = 0
    
    # Créer un dossier par tenant
    tenant_dir = UPLOAD_DIR / tid
    tenant_dir.mkdir(exist_ok=True)
    
    for file in files:
        if file.filename == '':
            continue
        
        if not allowed_file(file.filename):
            results.append({"filename": file.filename, "status": "skipped", 
                          "reason": "Type non supporté"})
            continue
        
        filename = secure_filename(file.filename)
        filepath = tenant_dir / f"{int(time.time())}_{filename}"
        
        try:
            file.save(str(filepath))
            
            # Extraire le texte
            content = extract_text_from_file(str(filepath), filename)
            
            if not content or len(content) < 10:
                results.append({"filename": filename, "status": "empty", 
                              "reason": "Fichier vide ou illisible"})
                continue
            
            # Ingérer dans les patterns
            stats = ingest_file_to_patterns(content, filename, tid)
            total_patterns += stats["patterns_created"]
            total_symptoms += stats["symptoms_found"]
            
            results.append({
                "filename": filename,
                "status": "ingested",
                "size_kb": len(content) // 1024,
                "patterns_created": stats["patterns_created"],
                "symptoms_found": stats["symptoms_found"],
            })
            
        except Exception as e:
            results.append({"filename": filename, "status": "error", "reason": str(e)})
    
    # Stats globales du tenant après ingestion
    tenant_stats = tenants.get_stats(tid)
    
    return jsonify({
        "status": "completed",
        "files_processed": len(results),
        "total_patterns_created": total_patterns,
        "total_symptoms_ingested": total_symptoms,
        "tenant_patterns_total": tenant_stats.get("custom_patterns", 0),
        "details": results,
        "message": f"✅ {total_patterns} nouveaux patterns créés. L'IA connaît maintenant votre contexte."
    })


@app.route('/api/v2/enterprise/upload/status', methods=['GET'])
@require_tenant
def upload_status():
    """Statut de l'hologramme entreprise (patterns créés par uploads)."""
    tid = request.tenant_id
    custom = tenants.get_patterns(tid)
    
    uploaded_patterns = {k: len(v) for k, v in custom.items() if k.startswith("📄")}
    manual_patterns = {k: len(v) for k, v in custom.items() if not k.startswith("📄")}
    
    return jsonify({
        "tenant": tenants.get(tid)["name"],
        "uploaded_patterns": len(uploaded_patterns),
        "uploaded_symptoms": sum(uploaded_patterns.values()),
        "manual_patterns": len(manual_patterns),
        "manual_symptoms": sum(manual_patterns.values()),
        "total_hologram_entries": sum(len(v) for v in custom.values()),
        "files_uploaded": len(uploaded_patterns),
    })

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
# API HARMONIQ HOLOGRAMS
# ════════════════════════════════════════════════════════════════

@app.route('/api/v2/enterprise/holograms/status', methods=['GET'])
def holograms_status():
    """Statut des hologrammes entreprise."""
    if _enterprise_holograms is None:
        return jsonify({'status': 'unavailable', 'reason': 'Module non chargé'})
    return jsonify(_enterprise_holograms.info())


@app.route('/api/v2/enterprise/holograms/train', methods=['POST'])
def holograms_train():
    """Lance l'entraînement des hologrammes."""
    if _enterprise_holograms is None:
        return jsonify({'error': 'Module non disponible'}), 503

    data = request.get_json(force=True, silent=True) or {}
    min_faits = data.get('min_facts', 5)
    max_domaines = data.get('max_domains', 10)

    try:
        results = _enterprise_holograms.train_all(
            min_faits=min_faits, max_domaines=max_domaines)
        return jsonify({
            'status': 'trained',
            'domains': len(results),
            'list': list(results.keys()),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v2/enterprise/holograms/ask', methods=['POST'])
def holograms_ask():
    """Interroge les hologrammes entreprise."""
    if not _HOLOGRAMS_READY:
        return jsonify({'error': 'Hologrammes non entraînés'}), 503

    data = request.get_json(force=True, silent=True) or {}
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'error': 'Question requise'}), 400

    result = _enterprise_holograms.ask(question)
    return jsonify(result)


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    log.info(f"🌐 Serveur Enterprise: http://localhost:{PORT}")
    log.info(f"💡 Dashboard: http://localhost:{PORT}/")
    log.info(f"🔑 Tenants: {len(tenants.tenants)}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
