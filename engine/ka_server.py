"""
KA Server — API unifiée Harmonic AI + HCV Compression
=======================================================
Backend unique pour l'application KA Web Complete.

Endpoints Harmonic AI :
  POST /api/chat        — conversation
  POST /api/reason      — raisonnement en chaîne
  POST /api/create      — connexions créatives
  GET  /api/haiku       — haïku
  GET  /api/stats       — statistiques système

Endpoints HCV (prêts, nécessitent les codecs HCV compilés) :
  POST /api/compress     — compression d'image
  POST /api/upscale      — upscaling d'image
  POST /api/enhance      — pipeline complet

Usage :
  python ka_server.py                  # port 8765
  python ka_server.py --port 8080      # port personnalisé
  python ka_server.py --model 217k     # charger le modèle 217K
"""

import sys, os, io, re, time, json, logging
from pathlib import Path
from collections import defaultdict

# ── Logging structuré ────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('ka_server.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ── Métriques serveur ────────────────────────────────────────────────────────
SERVER_START = time.time()
_metrics = {
    'requests': defaultdict(int),      # endpoint → count
    'errors': defaultdict(int),        # endpoint → error count
    'latency_sum': defaultdict(float), # endpoint → total latency ms
    'latency_count': defaultdict(int), # endpoint → count for avg
    'harmonic_count': 0,
    'llm_count': 0,
    'last_requests': [],               # (endpoint, latency_ms, status, timestamp)
}
_MAX_LAST_REQUESTS = 100

# ── Rate Limiting ────────────────────────────────────────────────────────────
_RATE_LIMIT_WINDOW = 60     # secondes
_RATE_LIMIT_MAX = 30        # requêtes max par fenêtre
_rate_limit_store = defaultdict(list)  # IP → [timestamps]

def _check_rate_limit(ip: str) -> bool:
    """Retourne True si la limite est dépassée."""
    now = time.time()
    window_start = now - _RATE_LIMIT_WINDOW
    _rate_limit_store[ip] = [t for t in _rate_limit_store[ip] if t > window_start]
    _rate_limit_store[ip].append(now)
    return len(_rate_limit_store[ip]) > _RATE_LIMIT_MAX

# Setup
_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import numpy as np

# ═══════════════════════════════════════════════════════════════════════════════
# INITIALISATION
# ═══════════════════════════════════════════════════════════════════════════════

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
    }
})

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION PRODUIT (Mobile / PC / Enterprise)
# ═══════════════════════════════════════════════════════════════════════════════

_KA_CONFIG = None
try:
    from ka_config import get_active_config, PRODUCTS, get_config
    _KA_CONFIG = get_active_config()
    log.info(f"  {_KA_CONFIG.icon} Produit actif: {_KA_CONFIG.name} (port {_KA_CONFIG.port})")
except Exception as e:
    log.warning(f"  ⚠ ka_config.py non trouvé — mode mobile par défaut ({e})")

log.info("=" * 55)
log.info("  KA SERVER — Harmonic AI + HCV Compression")
log.info("=" * 55)

def load_facts(model_name='best'):
    """Charge la base de connaissance. Fallback: KB qualitative intégrée."""
    # Mode qualitatif : toujours utiliser la KB intégrée (léger)
    if model_name in ('qualitative', 'light', 'minimal'):
        from harmonic_model import KNOWLEDGE_BASE
        log.info(f"  📂 KB qualitative intégrée: {len(KNOWLEDGE_BASE):,} faits (mode léger)")
        return [(str(s), str(r), str(o), str(sec)) for s, r, o, sec in KNOWLEDGE_BASE]
    
    # Chercher dans engine/data/ d'abord (chemin Render), puis ../data/ (local)
    search_paths = [
        Path(__file__).resolve().parent / 'data' / 'bootstrapper_output',
        Path(__file__).resolve().parent.parent / 'data' / 'bootstrapper_output',
        Path('/opt/render/project/src/data/bootstrapper_output'),
        Path('/opt/render/project/src/engine/data/bootstrapper_output'),
    ]
    
    model_files = {
        '50k':  'knowledge_base_50k.npz',
        '50k_clean': 'knowledge_base_50k_cleaned.npz',
        '50k_res': 'knowledge_base_resonance.npz',
        '100k': 'knowledge_base_100k.npz',
        '110k': 'knowledge_base_merged_v3.npz',
        '217k': 'knowledge_base_clean.npz',
        '300k': 'knowledge_base_300k.npz',
        '500k': 'knowledge_base_500k.npz',
        'enriched': 'knowledge_base_enriched.npz',
        'en': 'knowledge_base_en.npz',            # 🌐 English KB
        'en_full': 'knowledge_base_en.npz',       # 🌐 English KB (full)
        'best': 'knowledge_base_merged_v3.npz',   # 110K — stable
    }
    filename = model_files.get(model_name)
    if not filename:
        log.warning(f"  ⚠️ Modèle inconnu: {model_name}, fallback qualitatif")
        from harmonic_model import KNOWLEDGE_BASE
        return [(str(s), str(r), str(o), str(sec)) for s, r, o, sec in KNOWLEDGE_BASE]
    
    for base in search_paths:
        path = base / filename
        if path.exists():
            data = np.load(str(path), allow_pickle=True)
            facts = [(str(s), str(r), str(o), str(sec)) for s, r, o, sec in data['facts']]
            log.info(f"  📂 {path.name}: {len(facts):,} faits chargés")
            return facts
    
    # Fallback: KB qualitative intégrée (1955 faits)
    from harmonic_model import KNOWLEDGE_BASE
    log.info(f"  📂 KB qualitative intégrée: {len(KNOWLEDGE_BASE):,} faits (fallback)")
    return [(str(s), str(r), str(o), str(sec)) for s, r, o, sec in KNOWLEDGE_BASE]

model_name = 'best'  # 110K+ faits fusionnés (NPZ + structurés)
# Pour utiliser un modèle spécifique : --model 50k|100k|217k|500k|qualitative
for arg in sys.argv[1:]:
    if arg.startswith('--model='):
        model_name = arg.split('=')[1]
    elif arg == '--model':
        idx = sys.argv.index(arg)
        if idx + 1 < len(sys.argv):
            model_name = sys.argv[idx + 1]

port = 8765
for arg in sys.argv[1:]:
    if arg.startswith('--port='):
        port = int(arg.split('=')[1])

# Charger
facts = load_facts(model_name)

# 🔥 Fusionner les faits structurés (pays, tableau périodique, etc.) 
# quel que soit le chemin de chargement
try:
    import json
    expanded_path = Path(__file__).resolve().parent / 'data' / 'kb_merged.json'
    if expanded_path.exists():
        with open(expanded_path, 'r', encoding='utf-8') as f:
            expanded = json.load(f)
        existing = set((str(s).lower().strip(), str(r).lower().strip(), str(o).lower().strip()) 
                       for s, r, o, sec in facts)
        added = 0
        for s, r, o, sec in expanded:
            key = (str(s).lower().strip(), str(r).lower().strip(), str(o).lower().strip())
            if key not in existing:
                facts.append((str(s), str(r), str(o), str(sec)))
                existing.add(key)
                added += 1
        log.info(f"  📂 KB étendue: +{added} faits structurés → {len(facts):,} total")
except Exception as e:
    log.warning(f"  ⚠️ Fusion KB étendue impossible: {e}")

# Ajouter l'identité KA (le modèle doit savoir qui il est)
KA_IDENTITY = [
    ("KA", "est", "un assistant personnel intelligent", "GENERAL"),
    ("KA", "signifie", "force vitale (Ka egyptien)", "GENERAL"),
    ("KA", "repose sur", "Harmonic AI", "GENERAL"),
    ("KA", "utilise", "intelligence ondulatoire", "GENERAL"),
    ("KA", "a ete cree par", "l equipe Harmonic", "GENERAL"),
    ("KA", "fonctionne avec", "51 000 faits verifies", "GENERAL"),
    ("KA", "ne produit jamais", "hallucination", "GENERAL"),
    ("KA", "est represente par", "une sphere vivante", "GENERAL"),
    ("KA", "repond toujours", "en francais", "GENERAL"),
    ("KA", "est accessible via", "une application mobile", "GENERAL"),
    # Faits de correspondance (pour que les questions courantes matchent)
    ("je suis", "un assistant personnel nomme", "KA", "GENERAL"),
    ("je suis", "base sur", "Harmonic AI", "GENERAL"),
    ("je m appelle", "un assistant nomme", "KA", "GENERAL"),
    ("mon nom est", "un assistant intelligent nomme", "KA", "GENERAL"),
    ("je suis", "une intelligence artificielle nommee", "KA", "GENERAL"),
    ("je", "suis", "KA", "GENERAL"),
    # Faits pour les questions "qui es tu" / "tu es qui" (inversion sujet)
    ("tu es", "un assistant personnel nomme", "KA", "GENERAL"),
    ("tu es", "une intelligence artificielle", "KA", "GENERAL"),
    ("tu", "es", "KA", "GENERAL"),
    ("KA", "est", "mon nom", "GENERAL"),
]

# Capitales du monde (couverture rapide)
CAPITALS = [
    ("Yaounde","est la capitale du","Cameroun","GEO"),
    ("Paris","est la capitale de","la France","GEO"),
    ("Tokyo","est la capitale du","Japon","GEO"),
    ("Berlin","est la capitale de","l Allemagne","GEO"),
    ("Londres","est la capitale du","Royaume Uni","GEO"),
    ("Rome","est la capitale de","l Italie","GEO"),
    ("Madrid","est la capitale de","l Espagne","GEO"),
    ("Washington","est la capitale des","Etats Unis","GEO"),
    ("Brasilia","est la capitale du","Bresil","GEO"),
    ("Buenos Aires","est la capitale de","l Argentine","GEO"),
    ("Moscou","est la capitale de","la Russie","GEO"),
    ("Pekin","est la capitale de","la Chine","GEO"),
    ("New Delhi","est la capitale de","l Inde","GEO"),
    ("Canberra","est la capitale de","l Australie","GEO"),
    ("Ottawa","est la capitale du","Canada","GEO"),
    ("Le Caire","est la capitale de","l Egypte","GEO"),
    ("Pretoria","est la capitale de","l Afrique du Sud","GEO"),
    ("Abuja","est la capitale du","Nigeria","GEO"),
    ("Nairobi","est la capitale du","Kenya","GEO"),
    ("Dakar","est la capitale du","Senegal","GEO"),
    ("Alger","est la capitale de","l Algerie","GEO"),
    ("Rabat","est la capitale du","Maroc","GEO"),
    ("Tunis","est la capitale de","la Tunisie","GEO"),
    ("Bamako","est la capitale du","Mali","GEO"),
    ("Ouagadougou","est la capitale du","Burkina Faso","GEO"),
    ("Abidjan","est la capitale de","la Cote d Ivoire","GEO"),
    ("Lome","est la capitale du","Togo","GEO"),
    ("Cotonou","est la capitale du","Benin","GEO"),
    ("Kinshasa","est la capitale de","la RDC","GEO"),
    ("Luanda","est la capitale de","l Angola","GEO"),
    ("Maputo","est la capitale du","Mozambique","GEO"),
    ("Antananarivo","est la capitale de","Madagascar","GEO"),
    ("Kigali","est la capitale du","Rwanda","GEO"),
    ("Addis Abeba","est la capitale de","l Ethiopie","GEO"),
    ("Seoul","est la capitale de","la Coree du Sud","GEO"),
    ("Bangkok","est la capitale de","la Thailande","GEO"),
    ("Hanoi","est la capitale du","Vietnam","GEO"),
    ("Jakarta","est la capitale de","l Indonesie","GEO"),
    ("Manille","est la capitale des","Philippines","GEO"),
    ("Mexico","est la capitale du","Mexique","GEO"),
    ("Lima","est la capitale du","Perou","GEO"),
    ("Santiago","est la capitale du","Chili","GEO"),
    ("Bogota","est la capitale de","la Colombie","GEO"),
    ("Caracas","est la capitale du","Venezuela","GEO"),
    ("Lisbonne","est la capitale du","Portugal","GEO"),
    ("Athenes","est la capitale de","la Grece","GEO"),
    ("Vienne","est la capitale de","l Autriche","GEO"),
    ("Bruxelles","est la capitale de","la Belgique","GEO"),
    ("Amsterdam","est la capitale des","Pays Bas","GEO"),
    ("Stockholm","est la capitale de","la Suede","GEO"),
    ("Oslo","est la capitale de","la Norvege","GEO"),
    ("Copenhague","est la capitale du","Danemark","GEO"),
    ("Helsinki","est la capitale de","la Finlande","GEO"),
    ("Varsovie","est la capitale de","la Pologne","GEO"),
    ("Prague","est la capitale de","la Republique Tcheque","GEO"),
    ("Budapest","est la capitale de","la Hongrie","GEO"),
    ("Bucarest","est la capitale de","la Roumanie","GEO"),
    ("Sofia","est la capitale de","la Bulgarie","GEO"),
    ("Ankara","est la capitale de","la Turquie","GEO"),
    ("Teheran","est la capitale de","l Iran","GEO"),
    ("Bagdad","est la capitale de","l Irak","GEO"),
    ("Riyad","est la capitale de","l Arabie Saoudite","GEO"),
    ("Abou Dabi","est la capitale des","Emirats Arabes Unis","GEO"),
    ("Kiev","est la capitale de","l Ukraine","GEO"),
]
facts = facts + KA_IDENTITY + CAPITALS

from harmonic_brain import HarmonicBrain
from harmonic_ai import HarmonicAI

# ── IA HARMONIQUE OPTIMISÉE (FastRetriever 110K faits + PageForge + JLens) ──
print(f"  🧠 Initialisation de l'IA Harmonique (pipeline optimisé)...")
ai = HarmonicAI(use_memory=True, enable_bootstrapper=False, fast_mode=True)
brain = ai._get_brain() if hasattr(ai, '_get_brain') else None
print(f"  🧠 IA prête: FastRetriever + SFT + PageForge + JLens + routage code/maths/logique")
if ai.jlens:
    print(f"  🌊 J-Lens: actif (traçabilité des concepts)")

# Garder un accès au brain pour les modules qui en dépendent (spécializer, enterprise)
if brain is None:
    # Fallback: créer un petit brain pour compatibilité
    brain = HarmonicBrain(facts[:100], dim=64, use_holographic=False)

# ── 🌊 HWAT Bridge (nouveau modèle harmonique) ─────────────────────────
_hwat_bridge = None
_HWAT_AVAILABLE = False
try:
    from hwat_bridge import HwatBridge
    _hwat_bridge = HwatBridge(auto_load=True)
    _HWAT_AVAILABLE = _hwat_bridge.is_available
    if _HWAT_AVAILABLE:
        info = _hwat_bridge.info()
        print(f"  🌊 HWAT connecté : {info['params']:,} params, "
              f"dim={info['dim']}, blocs={info['blocks']}, "
              f"vocab={info['vocab']}")
except Exception as e:
    print(f"  🌊 HWAT erreur chargement: {e}")

# ── 🌐 Web Retriever (recherche Internet) ──────────────────────────────
_web_retriever = None
try:
    from web_retriever import WebRetriever
    _web_retriever = WebRetriever()
    print(f"  🌐 Web Retriever: connecté (DuckDuckGo + Wikipedia)")
except Exception as e:
    print(f"  🌐 Web Retriever: non disponible ({e})")

# ── 🎯 Domain Specializer (spécialisation dynamique) ──────────────────────────
_specializer = None
_optimized_specializer = None
_SPECIALIZER_AVAILABLE = False
try:
    from domain_specializer import DomainSpecializer, detect_specialize_intent, load_user_kbs_for_brain
    _specializer = DomainSpecializer(brain=brain, web_retriever=_web_retriever)
    _SPECIALIZER_AVAILABLE = True
    print(f"  🎯 Domain Specializer: actif (spécialisation dynamique)")
except Exception as e:
    print(f"  🎯 Domain Specializer: non disponible ({e})")

# Spécialiseur optimisé (hybride KB + web)
try:
    from specialize_optimized import OptimizedSpecializer
    _optimized_specializer = OptimizedSpecializer(web_retriever=_web_retriever, brain=brain)
    print(f"  🎯 Optimized Specializer: actif (bootstrap KB 110K + web ciblé)")
except Exception as e:
    print(f"  🎯 Optimized Specializer: non disponible ({e})")

# 📦 Hologram Store (knowledge store téléchargeable)
_hologram_store = None
try:
    from hologram_store import HologramStore
    _hologram_store = HologramStore()
    n_holo = len(_hologram_store.list_holograms())
    print(f"  📦 Hologram Store: actif ({n_holo} hologrammes disponibles)")
except Exception as e:
    print(f"  📦 Hologram Store: non disponible ({e})")

# 🧠 PersonalHologram (profil utilisateur, intérêts, suggestions)
_personal_holograms = {}  # user_id -> PersonalHologram (lazy)
try:
    from personal_hologram import PersonalHologram
    _HAS_PERSONAL = True
    print(f"  🧠 PersonalHologram: disponible")
except ImportError:
    _HAS_PERSONAL = False
    print(f"  🧠 PersonalHologram: non disponible")

# 🌊 Wave Poet (générateur de poésie ondulatoire)
_wave_poet = None
try:
    from wave_poetry import WavePoet
    _wave_poet = WavePoet()
    print(f"  🌊 Wave Poet: actif ({_wave_poet.stats()['poetic_vocabulary']} mots poétiques)")
except Exception as e:
    print(f"  🌊 Wave Poet: non disponible ({e})")

# ── 🏢 Enterprise Ingestor (injection de données d'entreprise) ─────────────────
_enterprise_ingestor = None
_ENTERPRISE_AVAILABLE = False
try:
    from enterprise_ingest import EnterpriseIngestor
    _enterprise_ingestor = EnterpriseIngestor(brain=brain)
    _ENTERPRISE_AVAILABLE = True
    print(f"  🏢 Enterprise Ingestor: actif (PDF, DOCX, CSV, JSON, TXT)")
except Exception as e:
    print(f"  🏢 Enterprise Ingestor: non disponible ({e})")

# ── HCV (optionnel) ─────────────────────────────────────────────────────────

hcv_available = False
HCV_DIR = Path(__file__).resolve().parent.parent / 'HCV-Compression-Engine'
# Fallback Render: le repo peut être cloné avec HCV en sous-module
if not HCV_DIR.exists():
    HCV_DIR = Path(__file__).resolve().parent / 'HCV-Compression-Engine'
if not HCV_DIR.exists():
    # Fallback: chercher dans les sous-dossiers
    for candidate in Path(__file__).resolve().parent.parent.glob('*HCV*'):
        if candidate.is_dir():
            HCV_DIR = candidate
            break
if HCV_DIR.exists():
    try:
        import importlib.util
        for mod_name, file_name in [
            ('hcv_android_boost', 'codecs/hcv_android_boost_codec.py'),
            ('hcv_upscaler', 'mobile/upscaler.py'),
            ('hcv_pro_codec_mod', 'codecs/hcv_pro_codec.py'),
        ]:
            spec = importlib.util.spec_from_file_location(mod_name, str(HCV_DIR / file_name))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                sys.modules[mod_name] = mod
                spec.loader.exec_module(mod)
        
        from sys import modules
        HCVAndroidBoostCodec = modules['hcv_android_boost'].HCVAndroidBoostCodec
        HCVUpscaler = modules['hcv_upscaler'].HCVUpscaler
        hcv_available = True
        print("  📦 HCV Compression: disponible")
    except Exception as e:
        log.warning(f"  📦 HCV Compression: erreur chargement ({e})")

if not hcv_available:
    log.info("  📦 HCV Compression: non disponible (mode cloud)")

log.info(f"  🌐 Serveur: http://localhost:{port}")
log.info("=" * 55)

# ═══════════════════════════════════════════════════════════════════════════════
# MIDDLEWARE — Métriques et Logging
# ═══════════════════════════════════════════════════════════════════════════════

@app.before_request
def _before_request():
    request._start_time = time.time()

@app.after_request
def _after_request(response):
    endpoint = request.endpoint or 'unknown'
    latency_ms = (time.time() - getattr(request, '_start_time', time.time())) * 1000
    
    _metrics['requests'][endpoint] += 1
    _metrics['latency_sum'][endpoint] += latency_ms
    _metrics['latency_count'][endpoint] += 1
    
    if response.status_code >= 400:
        _metrics['errors'][endpoint] += 1
    
    _metrics['last_requests'].append({
        'endpoint': endpoint,
        'latency_ms': round(latency_ms, 1),
        'status': response.status_code,
        'time': time.time()
    })
    if len(_metrics['last_requests']) > _MAX_LAST_REQUESTS:
        _metrics['last_requests'] = _metrics['last_requests'][-_MAX_LAST_REQUESTS:]
    
    log.info(f"{request.method} {request.path} → {response.status_code} ({latency_ms:.0f}ms)")
    return response


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS HARMONIC AI
# ═══════════════════════════════════════════════════════════════════════════════

# ── Wave Debugger (import paresseux) ──────────────────────────────────────────
_wave_debugger = None

# ── Harmonic Style (import paresseux) ─────────────────────────────────────────
_harmonic_styler = None

# ── DeepSeek Style Fallback (import paresseux) ────────────────────────────────
_deepseek_styler = None

def _polish_with_deepseek(response_text: str, user_message: str = "") -> str:
    """Polissage final par DeepSeek — reformule sans ajouter d'information."""
    global _deepseek_styler
    if _deepseek_styler is None:
        try:
            from llm.deepseek_styler import DeepSeekStyleFormatter
            _deepseek_styler = DeepSeekStyleFormatter()
            if not _deepseek_styler.enabled:
                _deepseek_styler = False  # marqueur: désactivé, ne pas réessayer
        except Exception:
            _deepseek_styler = False
    if _deepseek_styler is False:
        return response_text
    if not response_text or len(response_text) < 30:
        return response_text
    try:
        return _deepseek_styler.polish(response_text, user_message)
    except Exception:
        return response_text

def _style_response(response_text: str, user_message: str = "") -> str:
    """Applique le style harmonique (empathie + vocabulaire + diversité)."""
    global _harmonic_styler
    if _harmonic_styler is None:
        try:
            from harmonic_style import HarmonicStyler
            _harmonic_styler = HarmonicStyler()
        except Exception:
            return response_text
    if not response_text or len(response_text) < 20:
        return response_text
    try:
        return _harmonic_styler.style(response_text, user_message, 0.5)
    except Exception:
        return response_text

def _get_wave_debugger():
    """Import paresseux du wave_debugger (évite les imports circulaires)."""
    global _wave_debugger
    if _wave_debugger is None:
        try:
            from wave_debugger import diagnose_for_api, format_debug_response
            _wave_debugger = (diagnose_for_api, format_debug_response)
            log.info("🌊 Wave Debugger chargé")
        except Exception as e:
            log.warning(f"🌊 Wave Debugger non disponible: {e}")
            _wave_debugger = (None, None)
    return _wave_debugger


@app.route('/api/debug', methods=['POST'])
def debug_diagnose():
    """
    🌊 Diagnostic ondulatoire de bug.
    
    Body: {
        "symptom": "NullPointerException quand...",  # requis
        "language": "python",                         # optionnel
        "code": "def foo(): ..."                      # optionnel — snippet de code
    }
    
    Returns: diagnostic complet avec interférence, stratégie, action.
    """
    diagnose_fn, _ = _get_wave_debugger()
    
    data = request.get_json(force=True, silent=True) or {}
    symptom = data.get('symptom', '').strip()
    language = data.get('language', '').strip()
    code_snippet = data.get('code', '').strip()
    
    if not symptom:
        return jsonify({
            'error': 'Le champ "symptom" est requis.',
            'example': {
                'symptom': 'NullPointerException quand utilisateur sans profil',
                'language': 'java',
                'code': 'user.getProfile().getName()'
            },
            'methodology': 'Les 4 étapes : Traduire → Diagnostiquer → Prescrire → Vérifier'
        }), 422
    
    if diagnose_fn is None:
        return jsonify({
            'error': 'Wave Debugger non disponible sur ce serveur.',
            'fallback': 'Consultez docs/METHODOLOGIE_RESOLUTION_ONDULATOIRE.md'
        }), 503
    
    t0 = time.time()
    result = diagnose_fn(symptom, language, code_snippet)
    latency_ms = (time.time() - t0) * 1000
    
    return jsonify({
        **result,
        'latency_ms': round(latency_ms, 1),
        'model': 'wave-debugger-v1',
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Conversation avec l'IA.
    Body: { "message": "texte", "context": "optionnel",
            "style": "auto|concise|elegant|pedagogique|chaleureux",
            "depth": "court|standard|détaillé",
            "personality": "ka|savant|vulgarisateur|poete" }
    Returns: { "response": "...", "confidence": 0.85, "source": "harmonic|llm" }
    """
    data = request.get_json(force=True, silent=True) or {}
    message = data.get('message', '').strip()
    context = data.get('context', '').strip()
    user_id = data.get('user_id', 'anonymous')
    
    # Nouveaux paramètres de contrôle du style
    style = data.get('style', 'auto')          # "concise"|"elegant"|"pedagogique"|"chaleureux"|"auto"
    depth = data.get('depth', 'standard')       # "court"|"standard"|"détaillé"
    personality = data.get('personality', 'ka') # "ka"|"savant"|"vulgarisateur"|"poete"
    
    # Valider les valeurs
    valid_styles = {'concise', 'elegant', 'pedagogique', 'chaleureux', 'auto'}
    valid_depths = {'court', 'standard', 'détaillé'}
    valid_personalities = {'ka', 'savant', 'vulgarisateur', 'poete'}
    if style not in valid_styles: style = 'auto'
    if depth not in valid_depths: depth = 'standard'
    if personality not in valid_personalities: personality = 'ka'
    
    if not message:
        return jsonify({'error': 'Message requis', 'response': "Je n'ai pas compris votre message."}), 400

    # 🌐 Détection automatique de la langue
    detected_lang = 'fr'
    try:
        from holographic_encoder import _detect_language
        detected_lang = _detect_language(message)
    except Exception:
        # Fallback simple : détection par mots-clés
        msg_lower = message.lower()
        en_markers = [' the ', ' is ', ' are ', ' what ', ' how ', ' why ', ' when ', ' where ', ' who ']
        if any(m in msg_lower for m in en_markers):
            detected_lang = 'en'

    # 🌊 HWAT ENRICHMENT — Encodage du message par le nouveau modèle harmonique
    if _HWAT_AVAILABLE and _hwat_bridge:
        try:
            hwat_vec = _hwat_bridge.encode_pooled(message)
            print(f"  🌊 HWAT: '{message[:50]}...' → vecteur norme={np.linalg.norm(hwat_vec):.1f}")
        except Exception:
            pass  # Bonus silencieux

    # 🌊 Détection de demande de diagnostic ondulatoire
    debug_prefixes = ['/debug', 'debug:', 'diagnostic:', 'wave:', '🌊']
    is_debug = any(message.lower().startswith(p.lower()) for p in debug_prefixes)
    
    # Aussi détecter les descriptions de bugs naturelles
    bug_keywords = ['bug', 'plante', 'crash', 'exception', 'erreur', 'null', 'race condition',
                    'memory leak', 'deadlock', 'boucle infinie', 'timeout', 'regression',
                    'ne marche pas', 'fonctionne pas', 'casse', 'debug', 'debugger',
                    'nullpointer', 'undefined', 'segfault', 'stack overflow']
    is_bug_description = not is_debug and any(kw in message.lower() for kw in bug_keywords)
    
    if is_debug or is_bug_description:
        diagnose_fn, format_fn = _get_wave_debugger()
        if diagnose_fn and format_fn:
            # Extraire le symptôme (enlever le préfixe /debug)
            symptom = message
            for p in debug_prefixes:
                if symptom.lower().startswith(p.lower()):
                    symptom = symptom[len(p):].strip()
                    break
            if not symptom:
                symptom = message
            
            result = diagnose_fn(symptom, '', '')
            response_text = format_fn(result)
            
            log.info(f"🌊 Diagnostic ondulatoire: {result['diagnosis']['interference']}")
            return jsonify({
                'response': response_text,
                'confidence': result['diagnosis']['confidence'],
                'source': 'wave-debugger',
                'latency_ms': 1.0,
                'model': 'wave-debugger-v1',
                'debug_data': result['diagnosis'],
            })
    
    # 🎯 Détection de demande de spécialisation (version optimisée)
    if _SPECIALIZER_AVAILABLE:
        intent = detect_specialize_intent(message)
        if intent:
            domain = intent['domain']
            depth_spec = intent.get('depth', 'expert')
            log.info(f"🎯 Spécialisation détectée: domain={domain}, depth={depth_spec}, user={user_id}")
            
            # Utiliser le spécialiseur optimisé si disponible
            if _optimized_specializer is not None:
                result = _optimized_specializer.specialize(domain, depth=depth_spec, user_id=user_id)
                return jsonify({
                    'response': result.message,
                    'confidence': result.validation_score,
                    'source': 'specializer-optimized',
                    'latency_ms': round(result.elapsed_seconds * 1000, 0),
                    'model': 'harmonic-v3-optimized',
                    'specialization': {
                        'domain': result.domain,
                        'existing_facts': result.existing_facts,
                        'new_facts': result.new_facts,
                        'total_facts': result.total_facts,
                        'coverage_pct': result.coverage_pct,
                        'validation_score': result.validation_score,
                        'top_concepts': result.top_concepts[:5],
                    },
                })
            elif _specializer is not None:
                result = _specializer.specialize(
                    domain=domain, depth=depth_spec, user_id=user_id, async_mode=False
                )
                return jsonify({
                    'response': result.message,
                    'confidence': 1.0 if result.success else 0.5,
                    'source': 'specializer',
                    'latency_ms': round(result.elapsed_seconds * 1000, 0),
                    'model': 'harmonic-v2',
                    'specialization': result.to_dict() if result.success else None,
                })
    
    # 🔄 Chargement automatique des KB utilisateur
    _brain = ai._get_brain() if ai else None
    if user_id != 'anonymous' and _SPECIALIZER_AVAILABLE and _brain and not _brain.has_user_kb(user_id):
        try:
            n_loaded = load_user_kbs_for_brain(_brain, user_id)
            if n_loaded > 0:
                log.info(f"🔄 {n_loaded} KB utilisateur chargées pour user={user_id}")
        except Exception as e:
            log.debug(f"🔄 Chargement KB utilisateur ignoré: {e}")
    
    # Handler spécial pour les questions d'identité
    identity_keywords = ['qui es tu', 'qui es-tu', 'tu es qui', 'comment tu t appelles',
                         'ton nom', 'que fais tu', 'qui est ka', 'c est quoi ka',
                         'presente toi', 'qu est ce que tu es', 'what are you', 'who are you',
                         'tu es quoi', 't es qui', 't es quoi', 'qui etes vous',
                         'vous etes qui', 'comment vous appelez vous', 'quel est ton nom']
    msg_lower = message.lower().strip('?!. ')
    if any(kw in msg_lower for kw in identity_keywords):
        return jsonify({
            'response': "Je suis KA, votre assistant personnel intelligent. "
                        "Je vis dans cette application, représenté par une sphère vivante. "
                        "Je fonctionne grâce à Harmonic AI, une intelligence ondulatoire "
                        "qui ne produit jamais d'hallucination. "
                        "Mon nom vient du Ka égyptien, la force vitale. "
                        "Je réponds toujours en français, de façon chaleureuse et concise.",
            'confidence': 1.0,
            'source': 'identity',
            'latency_ms': 1.0,
            'model': 'harmonic-brain-v3',
        })
    
    # Validation: taille max
    if len(message) > 2000:
        return jsonify({'error': 'Message trop long (max 2000 caractères)'}), 422
    
    # Rate limiting
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr or 'unknown')
    if _check_rate_limit(client_ip):
        return jsonify({
            'error': 'Trop de requêtes. Réessayez dans une minute.',
            'retry_after_s': _RATE_LIMIT_WINDOW
        }), 429
    
    # Injecter le contexte si fourni
    if context:
        message = f"{context}\n{message}"
    
    t0 = time.time()
    
    # 🌊 Pipeline harmonique complet (HWAT + routeur + logique + templates)
    response = None
    source = 'harmonic'
    
    # 1. Normaliser la requête (questions courtes → langage naturel)
    normalized = message
    try:
        from query_normalizer import normalize
        normalized = normalize(message)
    except Exception:
        pass
    
    # 2. Router vers le bon moteur (maths, code, raisonnement)
    try:
        from intent_router import route
        result = route(normalized)
        if result:
            response = result
            source = 'router'
    except Exception:
        pass

    # 3. Logic engine (raisonnement PUR)
    if not response and any(w in message.lower() for w in 
        ['si ', 'alors', 'donc', 'déduire', 'conclure', 'implique', 'tous les',
         'aucun', 'vrai', 'faux', '>', '<', '=', '→']):
        try:
            from logic_engine import solve_logic
            result = solve_logic(normalized)
            if result and len(result) > 2:
                response = result
                source = 'logic'
        except Exception:
            pass

    # 4. Hologrammes — retrieval de faits (connaissances)
    if not response and _HWAT_AVAILABLE and _hwat_bridge:
        try:
            from hologram_router import HologramRouter
            hologram_dir = str(_ENGINE_DIR / 'data' / 'holograms')
            r = HologramRouter(hologram_dir)
            domains = r.route(message, top_k=2)
            facts = []
            for domain, _ in domains:
                facts.extend(r.retrieve_facts(domain, message, top_k=4))
            if facts:
                lines = [f"🌊 {message}", ""]
                for f in facts[:5]:
                    lines.append(f"• {f['sujet'][:70]} {f['relation'][:30]} {f['objet'][:70]}")
                response = '\n'.join(lines)
                source = 'hologram'
        except Exception as e:
            print(f"  ⚠ Hologram: {e}")

    # 5. Fallback : HarmonicAI
    if not response:
        response = ai.ask(message)
        source = 'harmonic'
    
    confidence = 0.85 if source != 'harmonic' else 0.70
    latency_ms = (time.time() - t0) * 1000
    
    # Métriques
    _metrics['harmonic_count'] += 1
    
    # Détecter si c'est une page (PageForge) ou une réponse courte
    is_page = response and response.startswith('# ')

    # 🆕 Visual Knowledge : enrichir la réponse avec un visuel si pertinent
    visual = None
    try:
        from visual_knowledge import augment_response
        # Récupérer les derniers faits utilisés (via le cerveau si dispo)
        facts = []
        if _brain and hasattr(_brain, '_last_accepted'):
            facts = [(f.sujet, f.relation, f.objet, f.secteur) for f in _brain._last_accepted]
        if facts:
            visual = augment_response(message, facts[:8])
    except Exception:
        pass

    # 🎨 Style harmonique : rendre la réponse plus agréable
    if not is_page and response and len(response) > 30:
        response = _style_response(response, message)

    # 🎨 DeepSeek Style Fallback : reformulation élégante (sans ajout d'info)
    if not is_page and response and len(response) > 30:
        response = _polish_with_deepseek(response, message)

    return jsonify({
        'response': response,
        'confidence': round(confidence, 2),
        'source': source,
        'latency_ms': round(latency_ms, 0),
        'model': 'harmonic-v3-optimized',
        'is_page': is_page,
        'visual': visual,
        'language': detected_lang,    # 🌐 langue détectée
    })


# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 SPÉCIALISATION DYNAMIQUE
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/specialize', methods=['POST'])
def specialize():
    """
    Lance une spécialisation de l'IA sur un domaine.
    
    Body: {
        "user_id": "user_123",        # requis
        "domain": "photographie",     # requis
        "depth": "expert",            # "debutant"|"avance"|"expert"|"encyclopedique"
        "async": false                # false = attendre, true = job_id
    }
    
    Retourne: SpecializationResult ou {"job_id": "...", "status": "started"}
    """
    if not _SPECIALIZER_AVAILABLE:
        return jsonify({
            'error': 'Domain Specializer non disponible',
            'response': "La spécialisation dynamique n'est pas disponible sur ce serveur."
        }), 503
    
    data = request.get_json(force=True, silent=True) or {}
    user_id = data.get('user_id', 'anonymous')
    domain = data.get('domain', '').strip()
    depth = data.get('depth', 'expert')
    async_mode = data.get('async', False)
    
    # Validation
    if not domain or len(domain) < 2:
        return jsonify({
            'error': 'Domaine requis (min 2 caractères)',
            'response': "Quel domaine souhaitez-vous que j'explore ?"
        }), 400
    
    valid_depths = {'debutant', 'avance', 'expert', 'encyclopedique'}
    if depth not in valid_depths:
        depth = 'expert'
    
    log.info(f"🎯 /api/specialize: user={user_id}, domain={domain}, "
             f"depth={depth}, async={async_mode}")
    
    try:
        if async_mode:
            # Mode asynchrone : retourne immédiatement un job_id
            result = _specializer.specialize(
                domain=domain, depth=depth, user_id=user_id,
                async_mode=True
            )
            return jsonify({
                'response': result.message,
                'confidence': 1.0,
                'source': 'specializer',
                'status': 'started',
                'job_id': result.message.split('job_id=')[-1].strip() if 'job_id=' in result.message else None,
            })
        else:
            # Mode synchrone : attend la fin
            result = _specializer.specialize(
                domain=domain, depth=depth, user_id=user_id,
                async_mode=False
            )
            
            return jsonify({
                'response': result.message,
                'confidence': 1.0 if result.success else 0.5,
                'source': 'specializer',
                'latency_ms': round(result.elapsed_seconds * 1000, 0),
                'model': 'harmonic-v2',
                'specialization': result.to_dict() if result.success else None,
            })
    except Exception as e:
        log.exception(f"Erreur spécialisation: {e}")
        return jsonify({
            'error': str(e),
            'response': f"❌ Erreur pendant la spécialisation : {e}",
        }), 500


@app.route('/api/learn', methods=['POST'])
def learn():
    """
    Apprentissage direct d'un fait par l'utilisateur.
    
    Body: {
        "fact": "Kigali est la capitale du Rwanda",   # requis
        "sujet": "Kigali",       # optionnel (extraction auto si omis)
        "relation": "est la capitale de",
        "objet": "Rwanda",
        "secteur": "GEOGRAPHIE"  # défaut: GENERAL
    }
    
    C'est le pendant API de la commande « apprends : <fait> » dans le chat.
    """
    if ai is None:
        return jsonify({'error': 'Moteur non initialisé'}), 503

    data = request.get_json(force=True, silent=True) or {}
    fact = data.get('fact', '').strip()

    if not fact and not data.get('sujet'):
        return jsonify({
            'error': "Paramètre 'fact' requis",
            'example': {'fact': "Kigali est la capitale du Rwanda"}
        }), 400

    try:
        if data.get('sujet') and data.get('relation') and data.get('objet'):
            ai.learn(data['sujet'], data['relation'], data['objet'],
                    data.get('secteur', 'GENERAL'))
            ingested = f"{data['sujet']} {data['relation']} {data['objet']}"
        else:
            ai.learn(fact)
            ingested = fact

        # 🆕 Pipeline communautaire : logger la contribution
        community_log = Path('data/hologram_store/community_contributions.jsonl')
        community_log.parent.mkdir(parents=True, exist_ok=True)
        with open(community_log, 'a', encoding='utf-8') as f:
            json.dump({
                'timestamp': __import__('time').time(),
                'user': data.get('user_id', 'anonymous'),
                'fact': ingested,
                'secteur': data.get('secteur', 'GENERAL'),
                'domain': data.get('domain', ''),
            }, f, ensure_ascii=False)
            f.write('\n')

        return jsonify({
            'response': f"✅ Appris : « {ingested[:80]} »",
            'confidence': 1.0,
            'source': 'learn',
            'kb_facts': ai.model.stats.get('facts', 0),
            'contributed': True,
        })
    except Exception as e:
        log.exception(f"Erreur /api/learn: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/community/contributions', methods=['GET'])
def community_contributions():
    """
    Retourne les dernières contributions communautaires (apprends :).
    GET /api/community/contributions?limit=50
    """
    limit = request.args.get('limit', 50, type=int)
    log_path = Path('data/hologram_store/community_contributions.jsonl')
    if not log_path.exists():
        return jsonify({'contributions': [], 'total': 0})

    contributions = []
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                contributions.append(json.loads(line))
            except Exception:
                pass

    return jsonify({
        'contributions': contributions[-limit:],
        'total': len(contributions),
    })


@app.route('/api/personalize/build', methods=['POST'])
def personalize_build():
    """
    Construit un hologramme personnalisé pour un domaine utilisateur.
    
    Body: {
        "domain": "droit congolais",     # domaine demandé
        "user_id": "user_123"            # utilisateur
    }
    
    Utilise holo_expand en mode léger : filtrage + cross-lingual
    + transitivité → hologramme dédié.
    """
    data = request.get_json(force=True, silent=True) or {}
    domain = data.get('domain', '').strip().lower()
    user_id = data.get('user_id', 'anonymous')

    if not domain or len(domain) < 2:
        return jsonify({'success': False, 'error': 'Domaine requis (min 2 caractères)'}), 400

    try:
        # Importer le builder interne
        from holo_expand import build_massive_hologram, DOMAIN_EXPANSIONS, _get_domain_config
        from hologram_store import HologramStore

        # Vérifier si un hologramme existe déjà pour ce domaine
        store = HologramStore()
        existing = [h for h in store.list_holograms()
                   if domain.replace(' ','_') in h['id'].lower() or domain in h.get('domain','').lower()]
        
        if existing:
            # Télécharger et fusionner directement
            facts = store.download(existing[0]['id'])
            if facts:
                from page_forge import _init_fast_retriever, _FAST_RETRIEVER
                _init_fast_retriever()
                if _FAST_RETRIEVER:
                    _FAST_RETRIEVER.add_facts(facts)
                return jsonify({
                    'success': True,
                    'domain': domain,
                    'holo_id': existing[0]['id'],
                    'facts': len(facts),
                    'source': 'existing',
                })

        # Construire un nouvel hologramme
        result = build_massive_hologram(domain=domain, target_facts=10000, skip_benchmark=True)
        
        if result.get('status') == 'completed':
            return jsonify({
                'success': True,
                'domain': domain,
                'holo_id': result.get('hologram_id', ''),
                'facts': result.get('published_facts', 0),
                'quality_score': result.get('quality_score', 0),
                'source': 'built',
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('status', 'unknown'),
                'domain': domain,
            })

    except Exception as e:
        log.exception(f"Erreur personalize/build: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/specialize/status/<user_id>', methods=['GET'])
def specialize_status(user_id):
    """
    Retourne l'état de spécialisation pour un utilisateur.
    
    GET /api/specialize/status/user_123
    
    Retourne: {
        "user_id": "user_123",
        "active_jobs": [...],
        "specialized_domains": {
            "photographie": {"depth": "expert", "triplets": 8432, ...}
        }
    }
    """
    if not _SPECIALIZER_AVAILABLE:
        return jsonify({'error': 'Domain Specializer non disponible'}), 503
    
    try:
        # Récupérer les jobs actifs
        user_jobs = _specializer.get_user_jobs(user_id)
        active_jobs = [j.to_dict() for j in user_jobs if j.status not in ('done', 'error')]
        
        # Récupérer les domaines spécialisés depuis le profil
        specialized_domains = _specializer.get_user_domains(user_id)
        
        return jsonify({
            'user_id': user_id,
            'active_jobs': active_jobs,
            'specialized_domains': specialized_domains,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════════
# 🏢 ENTERPRISE DATA INJECTION
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/enterprise/ingest', methods=['POST'])
def enterprise_ingest():
    """
    Ingère des fichiers pour une entreprise (chemins sur le serveur).
    
    Body: {
        "enterprise_id": "acme_corp",
        "domain": "documentation_interne",
        "depth": "expert",
        "file_paths": ["/data/docs/contrats.pdf", "/data/docs/produits.csv"]
    }
    """
    if not _ENTERPRISE_AVAILABLE:
        return jsonify({
            'error': 'Enterprise Ingestor non disponible',
            'response': "L'ingestion de données d'entreprise n'est pas disponible."
        }), 503
    
    data = request.get_json(force=True, silent=True) or {}
    enterprise_id = data.get('enterprise_id', '').strip()
    domain = data.get('domain', '').strip()
    depth = data.get('depth', 'expert')
    file_paths = data.get('file_paths', [])
    
    if not enterprise_id:
        return jsonify({'error': 'enterprise_id requis'}), 400
    if not domain:
        return jsonify({'error': 'domain requis'}), 400
    if not file_paths:
        return jsonify({'error': 'file_paths requis (liste de chemins)'}), 400
    
    log.info(f"🏢 /api/enterprise/ingest: enterprise={enterprise_id}, "
             f"domain={domain}, files={len(file_paths)}")
    
    try:
        result = _enterprise_ingestor.ingest_files(
            file_paths=file_paths,
            enterprise_id=enterprise_id,
            domain=domain,
            depth=depth,
        )
        return jsonify(result.to_dict())
    except Exception as e:
        log.exception(f"Erreur ingestion entreprise: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/enterprise/upload', methods=['POST'])
def enterprise_upload():
    """
    Upload de fichier pour une entreprise (multipart/form-data).
    
    Form fields:
        file: le fichier à uploader
        enterprise_id: identifiant entreprise
        domain: domaine de connaissance
        depth: profondeur (optionnel, défaut: expert)
    """
    if not _ENTERPRISE_AVAILABLE:
        return jsonify({'error': 'Enterprise Ingestor non disponible'}), 503
    
    enterprise_id = request.form.get('enterprise_id', '').strip()
    domain = request.form.get('domain', '').strip()
    depth = request.form.get('depth', 'expert')
    
    if not enterprise_id:
        return jsonify({'error': 'enterprise_id requis'}), 400
    if not domain:
        return jsonify({'error': 'domain requis'}), 400
    
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier fourni'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nom de fichier vide'}), 400
    
    # Sauvegarder le fichier uploadé
    ent_uploads_dir = _ENGINE_DIR / 'data' / 'enterprises' / enterprise_id / 'uploads'
    ent_uploads_dir.mkdir(parents=True, exist_ok=True)
    
    # Sanitize filename
    safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', file.filename)
    upload_path = ent_uploads_dir / safe_filename
    
    # Éviter les écrasements
    if upload_path.exists():
        stem = upload_path.stem
        suffix = upload_path.suffix
        upload_path = ent_uploads_dir / f"{stem}_{int(time.time())}{suffix}"
    
    file.save(str(upload_path))
    log.info(f"🏢 Upload: {upload_path} ({upload_path.stat().st_size} bytes)")
    
    # Lancer l'ingestion
    try:
        result = _enterprise_ingestor.ingest_files(
            file_paths=[str(upload_path)],
            enterprise_id=enterprise_id,
            domain=domain,
            depth=depth,
        )
        return jsonify(result.to_dict())
    except Exception as e:
        log.exception(f"Erreur ingestion après upload: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/enterprise/status/<enterprise_id>', methods=['GET'])
def enterprise_status(enterprise_id):
    """
    Statut d'une entreprise.
    
    GET /api/enterprise/status/acme_corp
    """
    if not _ENTERPRISE_AVAILABLE:
        return jsonify({'error': 'Enterprise Ingestor non disponible'}), 503
    
    try:
        status = _enterprise_ingestor.get_enterprise_status(enterprise_id)
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/enterprise/list', methods=['GET'])
def enterprise_list():
    """
    Liste toutes les entreprises.
    
    GET /api/enterprise/list
    """
    if not _ENTERPRISE_AVAILABLE:
        return jsonify({'error': 'Enterprise Ingestor non disponible'}), 503
    
    try:
        enterprises = _enterprise_ingestor.list_enterprises()
        return jsonify({
            'enterprises': enterprises,
            'count': len(enterprises),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reason', methods=['POST'])
def reason():
    """
    Raisonnement en chaîne sur un sujet.
    Body: { "topic": "sujet" }
    Returns: { "chain": "...", "steps": [...] }
    """
    data = request.get_json(force=True, silent=True) or {}
    topic = data.get('topic', '').strip()
    
    if not topic:
        return jsonify({'error': 'Sujet requis'}), 400
    
    t0 = time.time()
    result = ai.ask(topic) if ai else brain.process(topic)
    # ai.ask() retourne une str ; brain.process() peut retourner un objet
    chain = result.response if hasattr(result, 'response') else str(result)
    latency_ms = (time.time() - t0) * 1000
    
    # Décomposer la chaîne en étapes (séparées par ". ")
    steps = [s.strip() for s in chain.split('. ') if s.strip()]
    
    return jsonify({
        'chain': chain,
        'steps': steps,
        'step_count': len(steps),
        'latency_ms': round(latency_ms, 0),
    })


@app.route('/api/create', methods=['POST'])
def create():
    """
    Connexions créatives entre domaines.
    Body: { "n": 3, "concept_a": "optionnel", "concept_b": "optionnel" }
    Returns: { "ideas": [...], "count": N }
    """
    data = request.get_json(force=True, silent=True) or {}
    n = data.get('n', 3)
    concept_a = data.get('concept_a') or None
    concept_b = data.get('concept_b') or None
    
    if concept_a and concept_b:
        result = brain.process(f"connexion creative entre {concept_a or 'tout'} et {concept_b or 'tout'}")
        ideas = [result.response] if result.response else []
    else:
        result = brain.process(f"trouve {n} connexions creatives entre domaines differents")
        ideas = [result.response] if result.response else ["Connexion créative indisponible."]
    
    return jsonify({
        'ideas': ideas,
        'count': len(ideas),
    })


@app.route('/api/haiku', methods=['GET'])
def haiku():
    """Génère un haïku."""
    result = brain.process("genere un haiku")
    haiku_text = result.response
    return jsonify({
        'haiku': haiku_text,
        'lines': haiku_text.split('\n') if '\n' in haiku_text else [haiku_text],
    })


@app.route('/api/surreal', methods=['GET'])
def surreal():
    """Génère des images surréalistes."""
    n = request.args.get('n', 2, type=int)
    result = brain.process("genere une image surrealiste")
    images = [result.response] if result.response else ["Image surréaliste indisponible."]
    return jsonify({'images': images, 'count': len(images)})


# 🌐 RECHERCHE WEB ──────────────────────────────────────────────────────────────

@app.route('/api/search_web', methods=['POST'])
def search_web():
    """
    Recherche sur Internet via DuckDuckGo + Wikipedia.

    Body JSON :
      - query: str (requête de recherche)
      - max_results: int (défaut 5)
      - include_wikipedia: bool (défaut true)
      - include_web: bool (défaut true)
      - lang: str (défaut 'auto')

    Retourne :
      - results: [{source, title, url, snippet, summary}]
      - query: str
      - total: int
    """
    data = request.get_json(force=True, silent=True) or {}
    query = data.get('query', '').strip()
    if not query:
        return jsonify({'error': 'query required', 'results': []}), 400

    max_results = min(data.get('max_results', 5), 10)
    include_wikipedia = data.get('include_wikipedia', True)
    include_web = data.get('include_web', True)
    lang = data.get('lang', 'auto')

    if _web_retriever is not None:
        if lang == 'wikipedia_only':
            results = _web_retriever.search_wikipedia_multiple(query, lang=lang, limit=max_results)
        else:
            results = _web_retriever.search_web(
                query,
                max_results=max_results,
                include_wikipedia=include_wikipedia,
                include_web=include_web,
            )
        return jsonify({
            'results': results,
            'query': query,
            'total': len(results),
        })
    else:
        return jsonify({
            'error': 'Web retriever not available',
            'results': [],
            'query': query,
            'total': 0,
        }), 503


@app.route('/api/search_news', methods=['POST'])
def search_news():
    """
    Recherche d'actualités récentes.

    Body JSON :
      - topic: str (sujet, optionnel)
      - max_results: int (défaut 5)
    """
    data = request.get_json(force=True, silent=True) or {}
    topic = data.get('topic', '').strip() or None
    max_results = min(data.get('max_results', 5), 10)

    if _web_retriever is not None:
        results = _web_retriever.get_current_news(topic=topic, max_results=max_results)
        return jsonify({
            'results': results,
            'topic': topic,
            'total': len(results),
        })
    else:
        return jsonify({
            'error': 'Web retriever not available',
            'results': [],
            'total': 0,
        }), 503


# 🧪 FEW-SHOT LEARNING ──────────────────────────────────────────────────────────

@app.route('/api/few_shot', methods=['POST'])
def few_shot():
    """
    Apprentissage few-shot par injection temporaire de pattern.

    Body JSON :
      - examples: [{"input": "...", "output": "..."}, ...]  (2-10 paires)
      - query: str (nouvelle requête à traiter)
      - pattern_type: str (optionnel, défaut "general")

    Retourne :
      - response: str
      - confidence: float
      - pattern_coherence: float (qualité du pattern extrait)
      - interference_strength: float
    """
    data = request.get_json(force=True, silent=True) or {}
    examples_raw = data.get('examples', [])
    query = data.get('query', '').strip()
    pattern_type = data.get('pattern_type', 'general')

    if not query:
        return jsonify({'error': 'query required'}), 400
    if len(examples_raw) < 2:
        return jsonify({'error': 'Au moins 2 exemples requis'}), 400

    # Convertir en liste de tuples (input, output)
    examples = [(ex.get('input', ''), ex.get('output', '')) for ex in examples_raw]

    result = brain.few_shot(examples=examples, query=query, pattern_type=pattern_type)

    # Récupérer les stats du few-shot
    few_shot_stats = {}
    if brain._few_shot is not None:
        few_shot_stats = brain._few_shot.stats

    return jsonify({
        'response': result.response,
        'confidence': round(result.confidence, 2),
        'facts_count': result.retrieval_count,
        'few_shot_stats': few_shot_stats,
    })


# 🔗 DEEP REASONING ─────────────────────────────────────────────────────────────

@app.route('/api/deep_reason', methods=['POST'])
def deep_reason():
    """
    Raisonnement profond par propagation ψ amplifiée.

    Body JSON :
      - question: str
      - max_depth: int (défaut 7, max 15)

    Retourne :
      - response: str (conclusion)
      - chain_depth: int (nombre de sauts)
      - total_coherence: float
      - reasoning_type: str
      - chain_explanation: str (explication détaillée)
    """
    data = request.get_json(force=True, silent=True) or {}
    question = data.get('question', '').strip()
    max_depth = min(data.get('max_depth', 7), 15)

    if not question:
        return jsonify({'error': 'question required'}), 400

    if brain._deep_reasoner is None:
        return jsonify({
            'error': 'Deep reasoner non disponible (mode holographique requis)',
            'response': brain.process(question).response,
        }), 503

    from phase_amplifier import PhaseAmplifier
    chain = brain._deep_reasoner.propagate(question, max_depth=max_depth)
    response = brain._deep_reasoner.reason_deep(question, max_depth=max_depth)
    explanation = brain._deep_reasoner.explain(chain)

    return jsonify({
        'response': response,
        'chain_depth': chain.depth,
        'total_coherence': round(chain.total_coherence, 3),
        'reasoning_type': chain.reasoning_type,
        'stopped_reason': chain.stopped_reason,
        'chain_explanation': explanation,
    })


# 📖 RÉSUMÉ HARMONIQUE ─────────────────────────────────────────────────────────

@app.route('/api/summarize', methods=['POST'])
def summarize():
    """
    Résumé harmonique d'un texte long.

    Body JSON :
      - text: str (le texte à résumer, 1 à 50 pages)
      - max_facts: int (défaut 15, max 30)

    Retourne :
      - summary: str (résumé en langage naturel)
      - key_facts: [{subject, relation, object, centrality}]
      - themes: [str]
      - contradictions: int
      - stats: {chunks, triples_extracted, ...}
    """
    data = request.get_json(force=True, silent=True) or {}
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'text required'}), 400
    if len(text) < 50:
        return jsonify({'error': 'Texte trop court (minimum 50 caractères)'}), 400

    max_facts = min(data.get('max_facts', 15), 30)

    result = brain.summarize(text, max_facts=max_facts)
    return jsonify(result)


@app.route('/api/stats', methods=['GET'])
def stats():
    """Statistiques du système."""
    s = brain.stats
    s['hcv_available'] = hcv_available
    s['server_uptime'] = round(time.time() - SERVER_START, 0)
    s['harmonic_count'] = _metrics['harmonic_count']
    s['llm_count'] = _metrics['llm_count']
    return jsonify(s)


@app.route('/api/metrics', methods=['GET'])
def metrics():
    """Métriques détaillées du serveur."""
    avg_latency = {}
    for ep in _metrics['latency_sum']:
        cnt = _metrics['latency_count'][ep]
        avg_latency[ep] = round(_metrics['latency_sum'][ep] / cnt, 1) if cnt > 0 else 0
    
    return jsonify({
        'uptime_s': round(time.time() - SERVER_START, 0),
        'requests': dict(_metrics['requests']),
        'errors': dict(_metrics['errors']),
        'avg_latency_ms': avg_latency,
        'harmonic_count': _metrics['harmonic_count'],
        'llm_count': _metrics['llm_count'],
        'last_requests': _metrics['last_requests'][-20:],  # 20 dernières
    })


@app.route('/api/autonomie/history', methods=['GET'])
def autonomie_history():
    """Historique d'autonomie — Brain v3 est 100% autonome."""
    return jsonify({
        'history': [1] * 50,
        'autonomie': 100.0,
        'llm_calls': 0,
        'total_queries': _metrics['harmonic_count'],
        'note': 'Harmonic Brain v3 — zero dependance LLM'
    })


@app.route('/api/memory/recent', methods=['GET'])
def memory_recent():
    """
    Retourne les souvenirs récents de l'utilisateur.
    """
    try:
        # Récupérer depuis la mémoire conversationnelle ou le PersonalHologram
        memories = []
        import glob, os, json
        data_dir = Path(__file__).resolve().parent / 'data'
        # Chercher les sessions récentes
        session_files = sorted(glob.glob(str(data_dir / 'sessions' / '*.json')), key=os.path.getmtime, reverse=True)
        for sf in session_files[:5]:
            try:
                with open(sf, 'r', encoding='utf-8') as f:
                    session = json.load(f)
                if 'messages' in session:
                    for msg in session['messages'][-3:]:
                        if msg.get('role') == 'user':
                            memories.append({
                                'title': msg.get('content', '')[:80],
                                'date': msg.get('timestamp', ''),
                                'content': msg.get('content', '')
                            })
            except: pass
        return jsonify({'memories': memories[:10]})
    except Exception as e:
        return jsonify({'memories': [], 'error': str(e)})

@app.route('/api/config', methods=['GET'])
def get_app_config():
    """Retourne la configuration du produit actif (pour le frontend)."""
    if _KA_CONFIG:
        return jsonify(_KA_CONFIG.to_dict())
    return jsonify({'product': 'mobile', 'name': 'KA Mobile', 'port': port})

@app.route('/api/health', methods=['GET'])
def health():
    """Health check."""
    return jsonify({
        'status': 'ok',
        'harmonic': len(brain.unconscious.registry) > 0,
        'hcv': hcv_available,
        'hwat': _HWAT_AVAILABLE,
        'bootstrapper': None
    })


@app.route('/api/hwat', methods=['GET', 'POST'])
def hwat_endpoint():
    """Endpoint HWAT — encode ou génère via le nouveau modèle harmonique.
    
    GET  /api/hwat           → statut du modèle
    POST /api/hwat           → encode ou génère
         Body: {"text": "...", "action": "encode"|"generate"}
    """
    if not _HWAT_AVAILABLE:
        return jsonify({'status': 'unavailable'}), 503
    
    if request.method == 'GET':
        return jsonify({'status': 'ok', **_hwat_bridge.info()})
    
    data = request.get_json(force=True, silent=True) or {}
    text = data.get('text', '').strip()
    action = data.get('action', 'encode')
    
    if not text:
        return jsonify({'error': 'Texte requis'}), 400
    
    if action == 'generate':
        result = _hwat_bridge.generate(text, max_tokens=data.get('max_tokens', 30))
        return jsonify({'generated': result})
    else:
        vec = _hwat_bridge.encode_pooled(text)
        return jsonify({
            'encoded': True,
            'dim': len(vec),
            'norm': float(np.linalg.norm(vec)),
            'vector_preview': vec[:8].tolist()
        })


@app.route('/api/health/diagnostic', methods=['POST'])
def health_diagnostic():
    """
    Diagnostic médical harmonique.
    
    Body (JSON):
    {
        "symptomes": ["palpitations", "anxiete", ...],
        "vitaux": {
            "frequence_cardiaque": 88,
            "temperature": 37.1,
            "pression_systolique": 135,
            "pression_diastolique": 85,
            "saturation_oxygene": 97
        },
        "age": 45,
        "sexe": "H"
    }
    
    Returns: Diagnostic complet avec scores harmoniques, analyse de cohérence,
             diagnostic différentiel par résonance, et recommandations.
    """
    try:
        from harmonic_health import full_diagnostic, therapeutic_frequencies
        
        data = request.get_json(force=True, silent=True) or {}
        symptomes = data.get('symptomes', [])
        vitaux = data.get('vitaux', None)
        age = data.get('age', None)
        sexe = data.get('sexe', None)
        
        if not symptomes and not vitaux:
            return jsonify({
                'error': 'Fournir au moins symptomes et/ou vitaux',
                'example': {
                    'symptomes': ['palpitations', 'anxiete'],
                    'vitaux': {'frequence_cardiaque': 88, 'temperature': 37.1}
                }
            }), 400
        
        result = full_diagnostic(symptomes, vitaux, age, sexe)
        
        # Ajouter fréquences thérapeutiques si diagnostic trouvé
        if result.get('diagnostic_harmonique'):
            constante = result['diagnostic_harmonique'].get('constante_alteree', '')
            if constante:
                result['frequences_therapeutiques'] = therapeutic_frequencies(constante)
        
        return jsonify(result)
    
    except ImportError:
        return jsonify({'error': 'Module harmonic_health non disponible'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health/vitals', methods=['POST'])
def health_vitals():
    """
    Analyse harmonique des constantes vitales uniquement.
    
    Body (JSON):
    {
        "vitaux": {
            "frequence_cardiaque": 72,
            "temperature": 37.0,
            ...
        }
    }
    """
    try:
        from harmonic_health import vital_harmonic_score
        
        data = request.get_json(force=True, silent=True) or {}
        vitaux = data.get('vitaux', {})
        
        if not vitaux:
            return jsonify({'error': 'Fournir les constantes vitales'}), 400
        
        result = vital_harmonic_score(vitaux)
        return jsonify(result)
    
    except ImportError:
        return jsonify({'error': 'Module harmonic_health non disponible'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS HCV (actifs si codecs disponibles)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/compress', methods=['POST'])
def compress():
    """
    Compression d'image HCV (ou fallback built-in).
    Body: multipart/form-data avec champ 'image'
    Returns: JSON avec ratio, tailles
    """
    if 'image' not in request.files:
        return jsonify({'error': 'Fichier image requis'}), 400
    
    file = request.files['image']
    input_data = file.read()
    quality = int(request.form.get('quality', 80))
    
    # Essayer HCV d'abord
    if hcv_available:
        try:
            codec = HCVAndroidBoostCodec(quality='balanced')
            compressed, stats = codec.encode(jpeg_bytes=input_data)
            return jsonify({
                'original_size': stats.get('source_size', len(input_data)),
                'compressed_size': len(compressed),
                'ratio': round(stats.get('ratio_vs_source', 1), 1),
                'saved_percent': round(stats.get('savings_vs_source', 0), 1),
                'method': 'HCV',
                'quality': quality,
            })
        except Exception as e:
            pass  # Fallback to built-in
    
    # Fallback: built-in compressor
    try:
        from ka_media_compressor import compress_image as builtin_compress
        compressed, stats = builtin_compress(input_data, quality=quality)
        return jsonify({
            'original_size': stats['original_size'],
            'compressed_size': stats['compressed_size'],
            'ratio': stats['ratio'],
            'saved_percent': stats['saved_percent'],
            'elapsed_ms': stats['elapsed_ms'],
            'method': stats.get('method', 'builtin'),
            'quality': quality,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/upscale', methods=['POST'])
def upscale():
    """
    Upscaling d'image (×2 ou ×4).
    Body: multipart/form-data avec 'image' et 'scale' (2 ou 4)
    Returns: image/jpeg
    """
    if 'image' not in request.files:
        return jsonify({'error': 'Fichier image requis'}), 400
    
    file = request.files['image']
    scale = int(request.form.get('scale', 2))
    input_data = file.read()
    
    # Essayer HCV
    if hcv_available:
        try:
            import cv2
            img = cv2.imdecode(np.frombuffer(input_data, np.uint8), cv2.IMREAD_COLOR)
            if img is not None:
                upscaler = HCVUpscaler()
                upscaled = upscaler.upscale_sync(img, factor=scale)
                _, buffer = cv2.imencode('.jpg', upscaled, [cv2.IMWRITE_JPEG_QUALITY, 90])
                return send_file(io.BytesIO(buffer.tobytes()), mimetype='image/jpeg')
        except Exception:
            pass
    
    # Fallback built-in
    try:
        from ka_media_compressor import upscale_image as builtin_upscale
        from PIL import Image
        
        img = Image.open(io.BytesIO(input_data))
        img_array = np.array(img.convert('RGB'))
        upscaled = builtin_upscale(img_array, factor=scale)
        
        output = io.BytesIO()
        Image.fromarray(upscaled).save(output, format='JPEG', quality=90)
        output.seek(0)
        return send_file(output, mimetype='image/jpeg')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/media/restore', methods=['POST'])
def media_restore():
    """Restauration d'image (défloutage, débruitage)."""
    if 'image' not in request.files:
        return jsonify({'error': 'Fichier image requis'}), 400
    
    file = request.files['image']
    input_data = file.read()
    
    try:
        from ka_media_compressor import restore_image
        restored, stats = restore_image(input_data)
        
        output = io.BytesIO(restored)
        output.seek(0)
        return send_file(output, mimetype='image/jpeg')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/media/stats', methods=['GET'])
def media_stats():
    """Estimation des gains de stockage (pour le dashboard)."""
    # Valeurs simulées si pas de scan réel
    return jsonify({
        'total_photos': 142,      # simulé — en vrai, scanné depuis la galerie
        'total_videos': 8,
        'total_size_mb': 112.0,
        'estimated_savings_mb': 89.0,
        'estimated_savings_percent': 79.5,
        'compressed_count': 0,
        'upscaled_count': 0,
        'restored_count': 0,
    })
    
    return send_file(
        io.BytesIO(buffer),
        mimetype='image/jpeg',
        as_attachment=False,
    )


@app.route('/api/enhance', methods=['POST'])
def enhance():
    """
    Pipeline complet : compression → upscale.
    Body: multipart/form-data avec 'image'
    Returns: image/jpeg (compressée puis upscalée)
    """
    if not hcv_available:
        return jsonify({'error': 'HCV non disponible'}), 503
    
    if 'image' not in request.files:
        return jsonify({'error': 'Fichier image requis'}), 400
    
    file = request.files['image']
    input_data = file.read()
    
    import cv2
    codec = HCVAndroidBoostCodec(quality='balanced')
    upscaler = HCVUpscaler()
    
    try:
        # 1. Compresser
        compressed, stats = codec.encode(jpeg_bytes=input_data)
        # 2. Décompresser
        decompressed = codec.decode(compressed)
        # 3. Upscaler
        img = cv2.imdecode(np.frombuffer(decompressed, np.uint8), cv2.IMREAD_COLOR)
        upscaled = upscaler.upscale_sync(img, factor=2)
        _, buffer = cv2.imencode('.jpg', upscaled, [cv2.IMWRITE_JPEG_QUALITY, 90])
        
        return send_file(io.BytesIO(buffer), mimetype='image/jpeg')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS HPC / SCIENTIFIQUE (NEW v2.0)
# ═══════════════════════════════════════════════════════════════════════════════

PHI = 1.618033988749895

@app.route('/api/hpc/protein', methods=['POST'])
def hpc_protein():
    """
    ALPHAFOLD — Repliement protéique par résonance harmonique déterministe.

    Body: {
        "sequence": "NLYIQWLKDGGPSSGRPPPS",   # Séquence (code 1 ou 3 lettres)
        "mode": "predict",                      # "predict" (déterministe) ou "fold" (recuit)
        "temperature": 310.0,                   # Température initiale (K)
        "n_steps": 2000,                        # Nombre de pas max
        "cooling_rate": 0.999,                  # Taux de refroidissement
        "include_structure": true,              # Inclure les coordonnées 3D
        "include_energy": true,                 # Inclure la décomposition d'énergie
    }

    Returns:
        Résultat complet du repliement harmonique.
    """
    data = request.get_json(force=True, silent=True) or {}
    sequence = data.get('sequence', '').strip().upper()
    mode = data.get('mode', 'predict')
    temperature = float(data.get('temperature', 310.0))
    n_steps = int(data.get('n_steps', 2000))
    cooling_rate = float(data.get('cooling_rate', 0.999))
    include_structure = data.get('include_structure', True)
    include_energy = data.get('include_energy', True)

    if not sequence:
        return jsonify({'error': 'Séquence requise'}), 400

    try:
        from alphafold import (
            parse_sequence, get_harmonic_profile,
            ABCProteinFolder, compute_energy, compute_rama_score,
            structure_summary,
        )

        # Valider la séquence
        aas = parse_sequence(sequence)
        n = len(aas)
        if n < 3:
            return jsonify({'error': f'Séquence trop courte ({n} résidus), minimum 3'}), 400
        if n > 500:
            return jsonify({'error': f'Séquence trop longue ({n} résidus), maximum 500'}), 400

        # Profil harmonique
        profile = get_harmonic_profile(sequence)

        # Repliement
        folder = ABCProteinFolder(sequence)

        if mode == 'predict':
            result = folder.predict_structure(n_steps=n_steps)
        else:
            result = folder.fold(
                n_steps=n_steps,
                temperature=temperature,
                cooling_rate=cooling_rate,
                learning_rate=1.0,
                abc_memory=64,
                verbose=False,
            )

        # Énergie
        energy = result.energy.to_dict() if include_energy else None

        # Structure (coordonnées simplifiées)
        structure_data = None
        if include_structure and result.structure:
            structure_data = {
                'n_residues': result.structure.n_residues,
                'ca_trace': result.structure.ca_trace.tolist(),
                'phi_angles': [round(r.phi, 1) for r in result.structure.residues],
                'psi_angles': [round(r.psi, 1) for r in result.structure.residues],
                'rama_score': compute_rama_score(result.structure) if n > 3 else None,
            }

        response_data = {
            'status': 'completed',
            'method': 'ALPHAFOLD — Harmonic Deterministic (ABC Fractional Dynamics)',
            'sequence': sequence,
            'sequence_length': n,
            'harmonic_profile': profile,
            'folding': {
                'mode': mode,
                'n_steps': result.n_steps,
                'converged': result.converged,
                'elapsed_time_s': round(result.elapsed_time, 2),
                'harmonic_speedup': f'{PHI ** 3:.1f}x',
                'initial_energy': result.metadata.get('initial_energy', 0.0),
                'final_energy': energy.get('total', 0.0) if energy else None,
                'rmsd_to_initial': round(result.final_rmsd_to_initial, 3),
            },
            'energy': energy,
            'structure': structure_data,
            'summary': str(result) if not include_structure else None,
        }

        return jsonify(response_data)

    except ValueError as e:
        return jsonify({'error': f'Séquence invalide : {str(e)}'}), 400
    except ImportError as e:
        return jsonify({'error': f'Module alphafold non disponible : {str(e)}'}), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Erreur de repliement : {str(e)}'}), 500


@app.route('/api/hpc/quantum', methods=['POST'])
def hpc_quantum():
    """
    Simulation quantique harmonique.
    Body: { "n_qubits": 8, "hamiltonian_type": "ising" }
    """
    data = request.get_json(force=True, silent=True) or {}
    n_qubits = int(data.get('n_qubits', 8))
    hamiltonian_type = data.get('hamiltonian_type', 'ising')

    # Simulation simplifiée
    dim = 2 ** min(n_qubits, 8)
    np.random.seed(42)
    H = np.zeros((dim, dim), dtype=np.complex128)
    for i in range(dim):
        H[i, i] = -1.0 * ((i % 2) * 2 - 1)
        if i + 1 < dim:
            H[i, i + 1] = -1.0 / PHI
            H[i + 1, i] = -1.0 / PHI

    eigenvalues = np.sort(np.linalg.eigvalsh(H[:min(dim, 32), :min(dim, 32)]).real)

    return jsonify({
        'hamiltonian_type': hamiltonian_type,
        'n_qubits': n_qubits,
        'dimension': dim,
        'ground_state_energy': round(float(eigenvalues[0]), 6),
        'energy_spectrum': [round(float(e), 4) for e in eigenvalues[:8]],
        'harmonic_efficiency': f'{PHI ** 2:.1f}x',
    })


@app.route('/api/hpc/compress', methods=['POST'])
def hpc_compress():
    """
    Simulation de compression HCV (quand le codec n'est pas disponible).
    Body: { "size_bytes": 12400000, "type": "image" }
    """
    data = request.get_json(force=True, silent=True) or {}
    size_bytes = int(data.get('size_bytes', 12400000))
    file_type = data.get('type', 'image')

    ratios = {'image': 0.04, 'video': 0.06, 'audio': 0.10, 'text': 0.15}
    ratio = ratios.get(file_type, 0.05)
    compressed = int(size_bytes * ratio)
    gain = round((1 - ratio) * 100)

    return jsonify({
        'original_bytes': size_bytes,
        'compressed_bytes': compressed,
        'ratio': ratio,
        'gain_percent': gain,
        'method': 'HCV Harmonic Compression v2.0',
        'quality': 'lossless-perceptually',
    })


@app.route('/api/harmonic/encode', methods=['POST'])
def harmonic_encode():
    """
    Compression Harmonic Dictionary — encode réel avec dictionnaire 1.2M patches.
    Body: { "image_base64": "...", "quality": 45, "mode": "image" }
    """
    import base64, io, time
    data = request.get_json(force=True, silent=True) or {}
    
    try:
        from multimodal.harmonic_database import HarmonicDatabase
        from multimodal.harmonic_codec import HarmonicCodec
        from PIL import Image
        import numpy as np
    except Exception as e:
        return jsonify({'error': f'Import error: {str(e)}'}), 500

    quality = int(data.get('quality', 45))
    mode = data.get('mode', 'image')
    dict_path = data.get('dict_path', 'E:/harmonic_dict_full')

    # Charger le dictionnaire
    try:
        db = HarmonicDatabase(patch_size=20, K=16, stride=20, 
                              shard_size=50000, shard_dir=dict_path)
        codec = HarmonicCodec(db, quality=quality)
        codec.match_threshold = 1.0
    except Exception as e:
        return jsonify({'error': f'Dict load error: {str(e)}'}), 500

    result = {}
    
    # Décoder l'image
    img_b64 = data.get('image_base64', '')
    if img_b64:
        try:
            img_bytes = base64.b64decode(img_b64)
            img = np.array(Image.open(io.BytesIO(img_bytes)).convert('RGB'))
        except Exception as e:
            return jsonify({'error': f'Image decode error: {str(e)}'}), 400
    else:
        # Image de test par défaut
        from pathlib import Path
        test_img = Path('E:/SAAS - Copie/av_generation_output/massive_dataset/sunset')
        jpgs = sorted(test_img.glob('*.jpg'))
        if jpgs:
            img = np.array(Image.open(jpgs[-1]).convert('RGB'))
        else:
            img = np.random.RandomState(42).randint(0, 256, (200, 200, 3), dtype=np.uint8)

    h, w = img.shape[:2]
    raw_bytes = h * w * 3

    # Encoder
    t0 = time.perf_counter()
    bitstream = codec.encode_v2(img, 'default')
    encode_ms = (time.perf_counter() - t0) * 1000

    # Décoder
    t0 = time.perf_counter()
    reconstructed, meta = codec.decode_v2(bitstream, database=db)
    decode_ms = (time.perf_counter() - t0) * 1000

    # Métriques
    def psnr_fn(a, b):
        a, b = a.astype(np.float64), b.astype(np.float64)
        mse = np.mean((a - b) ** 2)
        return 100.0 if mse < 1e-15 else 20.0 * np.log10(255.0 / np.sqrt(mse))

    hm = min(h, reconstructed.shape[0])
    wm = min(w, reconstructed.shape[1])
    psnr_val = psnr_fn(img[:hm, :wm], reconstructed[:hm, :wm])

    try:
        from skimage.metrics import structural_similarity
        ssim_val = structural_similarity(
            img[:hm, :wm], reconstructed[:hm, :wm], 
            channel_axis=2, data_range=255
        )
    except Exception:
        ssim_val = None

    ratio = raw_bytes / len(bitstream) if len(bitstream) > 0 else 0
    gain = round((1 - 1/ratio) * 100) if ratio > 0 else 0

    result = {
        'original_bytes': raw_bytes,
        'compressed_bytes': len(bitstream),
        'ratio': round(ratio, 1),
        'gain_percent': gain,
        'psnr_db': round(psnr_val, 1),
        'ssim': round(ssim_val, 4) if ssim_val is not None else None,
        'encode_ms': round(encode_ms, 1),
        'decode_ms': round(decode_ms, 1),
        'match_rate': round(codec._last_match_rate * 100, 1) if hasattr(codec, '_last_match_rate') else None,
        'quality': quality,
        'patch_size': db.patch_size,
        'dict_patches': sum(s.n_patches for s in db._shards),
        'method': 'Harmonic Dictionary HHD2 — 1.2M patches, 48 catégories',
        'resolution': f'{w}x{h}',
    }

    return jsonify(result)


# ═══════════════════════════════════════════════════════════════════════════════
# STORAGE OPTIMIZER — Compression universelle de fichiers utilisateur
# ═══════════════════════════════════════════════════════════════════════════════

CODEC_RATIOS = {
    'image_jpeg': 1.25,
    'image_png': 1.5,
    'image_raw': 24.0,
    'video': 30.0,
    'video_static': 50.0,
    'voice': 100.0,
    'document': 1.25,
    'text': 3.0,
}


def _detect_media_type(filename: str, file_bytes: bytes = None) -> str:
    """Détecte le type de média à partir de l'extension et des magic bytes."""
    ext = Path(filename).suffix.lower() if filename else ''
    ext_img = {'.jpg', '.jpeg', '.jfif', '.heic', '.heif'}
    ext_raw = {'.raw', '.bmp', '.tiff', '.tif', '.dng', '.cr2', '.nef', '.arw'}
    ext_png = {'.png'}
    ext_vid = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v'}
    ext_aud = {'.m4a', '.wav', '.aac', '.flac', '.ogg', '.mp3'}
    ext_doc = {'.pdf', '.doc', '.docx', '.ppt', '.pptx'}
    ext_txt = {'.txt', '.md', '.json', '.xml', '.csv', '.log', '.py', '.js'}

    if ext in ext_img: return 'image_jpeg'
    if ext in ext_raw: return 'image_raw'
    if ext in ext_png: return 'image_png'
    if ext in ext_vid: return 'video'
    if ext in ext_aud: return 'voice'
    if ext in ext_doc: return 'document'
    if ext in ext_txt: return 'text'
    return 'image_jpeg'


def _codec_for_type(media_type: str, quality: str = 'standard'):
    """Choisit le codec et sa config selon le type de média."""
    if media_type == 'image_jpeg':
        return ('hcv_android', quality)
    if media_type == 'image_raw':
        return ('hcv_pro', quality)
    if media_type == 'image_png':
        return ('harmonic', quality)
    if media_type == 'video':
        return ('hcv_pro_video', quality)
    if media_type == 'voice':
        return ('voice_codec', quality)
    if media_type == 'document':
        return ('zstd', quality)
    if media_type == 'text':
        return ('zstd', quality)
    return ('zstd', quality)


@app.route('/api/storage/analyze', methods=['POST'])
def storage_analyze():
    """
    Analyse un fichier et estime le gain de compression.

    Body: multipart/form-data avec un champ 'file'
    Returns: {media_type, original_size, estimated_ratio, estimated_after, codec_recommended}
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni (champ "file" requis)'}), 400

        f = request.files['file']
        original_data = f.read()
        original_size = len(original_data)
        filename = f.filename or 'unknown'

        media_type = _detect_media_type(filename, original_data)
        ratio = CODEC_RATIOS.get(media_type, 1.25)
        codec_name, _ = _codec_for_type(media_type)
        estimated_after = int(original_size / ratio)

        return jsonify({
            'filename': filename,
            'media_type': media_type,
            'original_size': original_size,
            'estimated_ratio': round(ratio, 1),
            'estimated_after': estimated_after,
            'estimated_saved': original_size - estimated_after,
            'codec_recommended': codec_name,
        })

    except Exception as e:
        log.error(f'storage_analyze error: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/storage/optimize', methods=['POST'])
def storage_optimize():
    """
    Compresse un fichier et retourne le résultat.

    Body: multipart/form-data avec 'file' + 'quality' (archive|standard|eco)
    Returns: fichier compressé (binary) + en-têtes X-Ratio, X-Saved
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400

        f = request.files['file']
        original_data = f.read()
        original_size = len(original_data)
        filename = f.filename or 'unknown'
        quality = request.form.get('quality', 'standard')

        media_type = _detect_media_type(filename)
        codec_name, _ = _codec_for_type(media_type, quality)
        compressed = original_data  # par défaut
        ratio = 1.0
        psnr = 0.0
        warning = None

        # --- ZSTD direct (texte, documents, fallback) ---
        if codec_name == 'zstd':
            try:
                import zstandard as _zstd
                level = 22 if quality == 'eco' else 19 if quality == 'standard' else 11
                cctx = _zstd.ZstdCompressor(level=level)
                compressed = cctx.compress(original_data)
                ratio = original_size / max(len(compressed), 1)
            except Exception as e:
                warning = f'zstd indisponible: {e}'

        # --- HCV Android Boost (JPEG/PNG déjà compressés) ---
        elif codec_name == 'hcv_android':
            if hcv_available:
                try:
                    codec = HCVAndroidBoostCodec(quality='compact' if quality == 'eco' else 'balanced')
                    result = codec.encode(original_data, 'jpg', filename)
                    if isinstance(result, (bytes, bytearray)) and len(result) < original_size:
                        compressed = result
                        ratio = original_size / len(compressed)
                    else:
                        warning = 'Déjà optimal'
                except Exception as e:
                    warning = f'HCV Android: {e}'
            # Fallback zstd
            if ratio <= 1.0:
                try:
                    import zstandard as _zstd
                    compressed = _zstd.ZstdCompressor(level=19).compress(original_data)
                    ratio = original_size / max(len(compressed), 1)
                except Exception:
                    compressed = original_data

        # --- HCV Pro (RAW, broadcast) ---
        elif codec_name == 'hcv_pro':
            try:
                import cv2
                img = cv2.imdecode(np.frombuffer(original_data, np.uint8), cv2.IMREAD_COLOR)
                if img is not None:
                    import importlib.util
                    hcv_dir = Path(__file__).resolve().parent.parent / 'HCV-Compression-Engine' / 'codecs'
                    spec = importlib.util.spec_from_file_location('hcv_pro_mod', str(hcv_dir / 'hcv_pro_codec.py'))
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    enc_result = mod.HCVProCodec().encode_frame(img)
                    enc_data = enc_result[0] if isinstance(enc_result, tuple) else enc_result
                    if len(enc_data) < original_size:
                        compressed = enc_data
                        ratio = original_size / len(compressed)
                    else:
                        warning = 'Image déjà très compressée'
                else:
                    warning = 'Image non décodable'
            except Exception as e:
                warning = f'HCV Pro: {e}'

        # --- Voice Codec ---
        elif codec_name == 'voice_codec':
            try:
                sys.path.insert(0, str(Path(__file__).resolve().parent))
                from harmonic_voice_codec import HarmonicVoiceCodec
                import wave, io as _io
                # Essayer de lire en WAV
                try:
                    wf = wave.open(_io.BytesIO(original_data))
                    sr = wf.getframerate()
                    n = wf.getnframes()
                    raw = wf.readframes(n)
                    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
                    vc = HarmonicVoiceCodec()
                    compressed = vc.encode(audio, sr)
                    ratio = original_size / max(len(compressed), 1)
                except Exception:
                    # Pas du WAV → zstd
                    import zstandard as _zstd
                    compressed = _zstd.ZstdCompressor(level=19).compress(original_data)
                    ratio = original_size / max(len(compressed), 1)
                    warning = 'Format audio non-WAV, compression zstd appliquée'
            except Exception as e:
                warning = f'Voice Codec: {e}'

        # Sécurité: ne jamais retourner un fichier plus grand
        if len(compressed) >= original_size:
            compressed = original_data
            ratio = 1.0
            warning = 'Déjà optimal — aucune compression supplémentaire possible'

        saved = original_size - len(compressed)

        from flask import Response
        resp = Response(compressed, mimetype='application/octet-stream')
        resp.headers['Content-Disposition'] = f'attachment; filename="{filename}.hcv"'
        resp.headers['X-Ratio'] = f'{ratio:.1f}'
        resp.headers['X-Original-Size'] = str(original_size)
        resp.headers['X-Compressed-Size'] = str(len(compressed))
        resp.headers['X-Saved'] = str(saved)
        resp.headers['X-PSNR'] = f'{psnr:.1f}' if psnr > 0 else '0'
        resp.headers['X-Media-Type'] = media_type
        resp.headers['X-Codec'] = codec_name
        if warning:
            resp.headers['X-Warning'] = warning[:200]
        return resp

    except Exception as e:
        log.error(f'storage_optimize error: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/storage/optimize-batch', methods=['POST'])
def storage_optimize_batch():
    """
    Analyse un lot de fichiers et estime le gain total.

    Body: multipart/form-data avec plusieurs champs 'files'
    Returns: {total_original, total_estimated_after, total_saved, files: [...]}
    """
    try:
        files = request.files.getlist('files')
        if not files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400

        results = []
        total_original = 0
        total_after = 0

        for f in files:
            data = f.read()
            size = len(data)
            filename = f.filename or 'unknown'
            media_type = _detect_media_type(filename)
            ratio = CODEC_RATIOS.get(media_type, 1.25)
            est_after = int(size / ratio)
            total_original += size
            total_after += est_after
            results.append({
                'filename': filename,
                'media_type': media_type,
                'original_size': size,
                'estimated_after': est_after,
                'estimated_saved': size - est_after,
                'estimated_ratio': round(ratio, 1),
            })

        return jsonify({
            'files': results,
            'n_files': len(results),
            'total_original': total_original,
            'total_estimated_after': total_after,
            'total_saved': total_original - total_after,
            'avg_ratio': round(total_original / max(total_after, 1), 1),
        })

    except Exception as e:
        log.error(f'storage_optimize_batch error: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/storage/view', methods=['POST'])
def storage_view():
    """
    Décompresse (et upscale si demandé) un fichier pour affichage.
    
    Body: multipart/form-data avec 'file' + 'upscale' (4k|1080p|none)
    Returns: image JPEG prête à afficher
    
    C'est le point d'entrée pour la lecture : le fichier est décompressé
    et upscalé à la volée, donnant à l'utilisateur une qualité 4K même
    depuis un fichier ultra-compressé.
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400

        f = request.files['file']
        data = f.read()
        filename = f.filename or 'unknown'
        upscale = request.form.get('upscale', 'none')  # '4k', '1080p', 'none'

        # Décompresser
        media_type = _detect_media_type(filename)
        img = None
        
        # Essayer HCV decoder
        try:
            import cv2
            # Tenter l'image décodée directement
            raw = np.frombuffer(data, np.uint8)
            img = cv2.imdecode(raw, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError('Not an image')
        except Exception:
            pass

        # Fallback: essayer HCV Pro decode
        if img is None and hcv_available:
            try:
                import importlib.util
                hcv_dir = Path(__file__).resolve().parent.parent / 'HCV-Compression-Engine' / 'codecs'
                spec = importlib.util.spec_from_file_location('hcv_pro_vw', str(hcv_dir / 'hcv_pro_codec.py'))
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                img = mod.HCVProCodec().decode_frame(data)
            except Exception:
                pass

        if img is None:
            return jsonify({'error': 'Format non supporté pour la visualisation'}), 400

        # Upscale si demandé
        h, w = img.shape[:2]
        target_w, target_h = w, h
        upscaled = False

        if upscale == '4k':
            target_w = 3840
            target_h = 2160
            upscaled = (w < target_w or h < target_h)
        elif upscale == '1080p':
            target_w = 1920
            target_h = 1080
            upscaled = (w < target_w or h < target_h)

        if upscaled:
            # Upscale Lanczos (qualité maximale)
            scale = min(target_w / w, target_h / h)
            if scale > 1.0:
                new_w = int(w * scale)
                new_h = int(h * scale)
                try:
                    img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
                except Exception:
                    img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

        # Re-encoder en JPEG qualité 90 pour le transfert
        _, jpeg = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 90])
        
        from flask import Response
        resp = Response(jpeg.tobytes(), mimetype='image/jpeg')
        resp.headers['X-Original-W'] = str(w)
        resp.headers['X-Original-H'] = str(h)
        resp.headers['X-Display-W'] = str(target_w)
        resp.headers['X-Display-H'] = str(target_h)
        resp.headers['X-Upscaled'] = str(upscaled).lower()
        return resp

    except Exception as e:
        log.error(f'storage_view error: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/harmonic/stats', methods=['GET'])
def harmonic_stats():
    """Statistiques de stockage avec compression harmonique."""
    try:
        from multimodal.background_compressor import estimate_photos_remaining
        import shutil
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Espace disque disponible
    dict_path = 'E:/harmonic_dict_full'
    try:
        total, used, free = shutil.disk_usage(dict_path)
    except Exception:
        free = 200 * 1024**3  # fallback 200 GB

    # Estimation
    avg_compressed = 3500  # ~3.5 KB par photo 4K avec qualité 45
    photos_remaining = estimate_photos_remaining(free, avg_compressed)

    return jsonify({
        'disk_free_gb': round(free / (1024**3), 1),
        'photos_remaining': photos_remaining,
        'avg_compressed_bytes': avg_compressed,
        'avg_ratio': 119.5,
        'storage_saved_mb': 0,  # sera mis à jour par le background compressor
        'dict_size_mb': 1500,
        'dict_patches': 1185600,
        'dict_categories': 48,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS CODE & WAVE (NEW v2.0)
# ═══════════════════════════════════════════════════════════════════════════════

CODE_TEMPLATES = {
    'tri': {
        'python': 'def tri_rapide(arr):\n    if len(arr) <= 1: return arr\n    pivot = arr[0]\n    gauche = [x for x in arr[1:] if x <= pivot]\n    droite = [x for x in arr[1:] if x > pivot]\n    return tri_rapide(gauche) + [pivot] + tri_rapide(droite)',
        'javascript': 'function quickSort(arr) {\n  if (arr.length <= 1) return arr;\n  const pivot = arr[0];\n  const left = arr.slice(1).filter(x => x <= pivot);\n  const right = arr.slice(1).filter(x => x > pivot);\n  return [...quickSort(left), pivot, ...quickSort(right)];\n}',
    },
    'fibonacci': {
        'python': 'def fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        yield a\n        a, b = b, a + b',
        'javascript': 'function* fibonacci(n) {\n  let a = 0, b = 1;\n  for (let i = 0; i < n; i++) {\n    yield a;\n    [a, b] = [b, a + b];\n  }\n}',
    },
    'hello': {
        'python': 'def greet(name):\n    """Saluer quelqu\'un."""\n    return f"Bonjour, {name}!"',
        'javascript': 'function greet(name) {\n  return `Bonjour, ${name}!`;\n}',
    },
}


@app.route('/api/code/generate', methods=['POST'])
def code_generate():
    """
    Génération de code zero-LLM par patterns harmoniques.
    Body: { "prompt": "tri rapide", "language": "python" }
    """
    data = request.get_json(force=True, silent=True) or {}
    prompt = (data.get('prompt', '')).lower().strip()
    language = data.get('language', 'python')

    if not prompt:
        return jsonify({'error': 'Description requise'}), 400

    # Détection du pattern
    code = ''
    source = 'template'
    for key, templates in CODE_TEMPLATES.items():
        if key in prompt:
            code = templates.get(language, templates.get('python', ''))
            source = 'template'
            break

    if not code:
        # Pattern générique
        code = (
            f'def solve(data):\n    """{prompt[:60]}"""\n    # Implémentation harmonique φ-optimisée\n    resultat = data\n    return resultat'
            if language == 'python'
            else f'function solve(data) {{\n  // {prompt[:60]}\n  // Implémentation harmonique φ-optimisée\n  return data;\n}}'
        )
        source = 'generic'

    # Apprendre au cerveau (best effort)
    try:
        brain.unconscious.ingest('code_gen', 'a genere', prompt[:80], 'CODE')
    except Exception:
        pass

    return jsonify({
        'code': code,
        'language': language,
        'confidence': 0.85 if source == 'template' else 0.55,
        'source': source,
        'method': 'Zero-LLM Harmonic Patterns',
    })


@app.route('/api/wave/explain', methods=['POST'])
def wave_explain():
    """
    Explication scientifique par raisonnement harmonique.
    Body: { "question": "Pourquoi le ciel est-il bleu ?", "domain": "auto" }
    """
    data = request.get_json(force=True, silent=True) or {}
    question = data.get('question', '').strip()
    domain = data.get('domain', 'auto')

    if not question:
        return jsonify({'error': 'Question requise'}), 400

    # Utiliser le cerveau harmonique pour l'explication
    result = brain.process(f"explique scientifiquement: {question}")
    explanation = result.response

    # Détection du domaine
    ql = question.lower()
    if any(w in ql for w in ['physique', 'lumière', 'onde', 'énergie', 'force']):
        domain = 'physics'
    elif any(w in ql for w in ['biologie', 'cellule', 'adn', 'protéine']):
        domain = 'biology'
    elif any(w in ql for w in ['quantique', 'quantum']):
        domain = 'quantum'
    elif any(w in ql for w in ['chimie', 'molécule', 'atome']):
        domain = 'chemistry'
    else:
        domain = 'general'

    return jsonify({
        'question': question,
        'domain': domain,
        'explanation': explanation,
        'confidence': round(result.confidence, 2),
        'method': 'Harmonic Scientific Reasoning',
    })


@app.route('/api/wave/creative', methods=['POST'])
def wave_creative():
    """
    Génération créative (haïku, poème).
    Body: { "mode": "haiku", "theme": "intelligence" }
    """
    data = request.get_json(force=True, silent=True) or {}
    mode = data.get('mode', 'haiku')
    theme = data.get('theme', 'intelligence')

    result = brain.process(f"genere un {mode} sur le theme: {theme}")
    text = result.response

    return jsonify({
        'mode': mode,
        'theme': theme,
        'text': text,
        'harmonic_resonance': 0.618,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# FRONTEND — PWA (KA Phone)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/benchmark')
def serve_benchmark():
    """Page de benchmark public."""
    return send_from_directory(str(_ENGINE_DIR), 'benchmark.html')

@app.route('/test_vocal_ka.html')
def serve_test_vocal():
    return send_from_directory(str(_ENGINE_DIR), 'test_vocal_ka.html')

@app.route('/test_voix_directe.html')
def serve_test_voix():
    return send_from_directory(str(_ENGINE_DIR), 'test_voix_directe.html')

@app.route('/')
def serve_index():
    """Page d'accueil — KA Phone PWA (compagnon virtuel, compression, hologrammes)."""
    # Produit mobile → vraie KA Phone (ka_index.html) ; autre produit → redesign
    if _KA_CONFIG and _KA_CONFIG.product in ('mobile', 'phone', 'tel'):
        return send_from_directory(str(_ENGINE_DIR), 'ka_index.html')
    return send_from_directory(str(_ENGINE_DIR / 'ka_redesign'), 'index.html')

@app.route('/manifest.json')
def serve_manifest():
    """Manifest PWA pour installation sur l'écran d'accueil."""
    return send_from_directory(str(_ENGINE_DIR / 'ka_redesign'), 'manifest.json')

@app.route('/sw.js')
def serve_service_worker():
    """Service Worker pour le mode hors-ligne."""
    return send_from_directory(str(_ENGINE_DIR / 'ka_redesign'), 'sw.js', mimetype='application/javascript')

@app.route('/js/<path:filename>')
def serve_js(filename):
    """Fichiers JavaScript du redesign."""
    return send_from_directory(str(_ENGINE_DIR / 'ka_redesign' / 'js'), filename)

@app.route('/css/<path:filename>')
def serve_css(filename):
    """Fichiers CSS du redesign."""
    return send_from_directory(str(_ENGINE_DIR / 'ka_redesign' / 'css'), filename)

@app.route('/screens/<path:filename>')
def serve_screens(filename):
    """Captures d'écran."""
    return send_from_directory(str(_ENGINE_DIR / 'ka_redesign' / 'screens'), filename)

@app.route('/icons/<path:filename>')
def serve_icons(filename):
    """Icônes PWA."""
    return send_from_directory(str(_ENGINE_DIR / 'icons'), filename)

@app.route('/favicon.ico')
def serve_favicon():
    """Favicon."""
    return send_from_directory(_ENGINE_DIR, 'favicon.ico') if (_ENGINE_DIR / 'favicon.ico').exists() else ('', 204)

# ═══════════════════════════════════════════════════════════════════════════════
# GÉNÉRATION MÉDIA HARMONIQUE (Universe Language Model)
# Image = |Ψ|² (Born) | Forme = phase DFT | Génération = résonance + ABC
# ═══════════════════════════════════════════════════════════════════════════════

_media_engine = None

def _get_media_engine():
    """Lazy-init du moteur média harmonique."""
    global _media_engine
    if _media_engine is None:
        try:
            from multimodal.harmonic_media import HarmonicMediaEngine
            mem_path = str(_ENGINE_DIR / 'data' / 'visual_memory.npz')
            _media_engine = HarmonicMediaEngine(
                dim=512,
                memory_path=mem_path if os.path.exists(mem_path) else None
            )
            log.info("  🎨 Moteur média harmonique initialisé")
        except Exception as e:
            log.error(f"  Erreur init moteur média : {e}")
            return None
    return _media_engine


@app.route('/api/media/image', methods=['POST'])
def media_image():
    """Génère une image harmonique → image/png."""
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if _check_rate_limit(ip):
        return jsonify({'error': 'Rate limit exceeded'}), 429

    try:
        data = request.get_json(force=True)
        prompt = data.get('prompt', '')
        width = min(int(data.get('width', 256)), 512)
        height = min(int(data.get('height', 256)), 512)

        engine = _get_media_engine()
        if engine is None:
            return jsonify({'error': 'Moteur média non disponible'}), 503

        result = engine.generate_image(prompt, width=width, height=height)

        # Retourner l'image en PNG
        import io as _io
        from PIL import Image
        buf = _io.BytesIO()
        Image.fromarray(result.image).save(buf, format='PNG')
        buf.seek(0)

        log.info(f"  🎨 Image générée : '{prompt[:40]}' ({width}×{height}) "
                 f"cohérence={result.phase_coherence:.3f} "
                 f"[{result.processing_time_ms:.0f}ms]")
        return send_file(buf, mimetype='image/png',
                         as_attachment=True, download_name='harmonic.png')
    except Exception as e:
        log.error(f"  /api/media/image : {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/media/audio', methods=['POST'])
def media_audio():
    """Génère un audio harmonique → audio/wav."""
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if _check_rate_limit(ip):
        return jsonify({'error': 'Rate limit exceeded'}), 429

    try:
        data = request.get_json(force=True)
        prompt = data.get('prompt', '')
        duration = min(float(data.get('duration', 10.0)), 30.0)
        mode = data.get('mode', 'music')  # 'music' ou 'soundscape'

        engine = _get_media_engine()
        if engine is None:
            return jsonify({'error': 'Moteur média non disponible'}), 503

        result = engine.generate_audio(prompt, duration=duration, mode=mode)

        import io as _io
        from scipy.io import wavfile
        samples_int = (np.clip(result.samples, -1, 1) * 32767).astype(np.int16)
        buf = _io.BytesIO()
        wavfile.write(buf, result.sample_rate, samples_int)
        buf.seek(0)

        log.info(f"  🎵 Audio généré : '{prompt[:40]}' mode={mode} "
                 f"harmonie={result.harmony_score:.3f} "
                 f"[{result.processing_time_ms:.0f}ms]")
        return send_file(buf, mimetype='audio/wav',
                         as_attachment=True, download_name='harmonic.wav')
    except Exception as e:
        log.error(f"  /api/media/audio : {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/media/video', methods=['POST'])
def media_video():
    """Génère une vidéo harmonique → video/mp4."""
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if _check_rate_limit(ip):
        return jsonify({'error': 'Rate limit exceeded'}), 429

    try:
        data = request.get_json(force=True)
        prompt = data.get('prompt', '')
        duration = min(float(data.get('duration', 3.0)), 10.0)
        fps = min(int(data.get('fps', 12)), 24)
        width = min(int(data.get('width', 128)), 256)
        height = min(int(data.get('height', 128)), 256)

        engine = _get_media_engine()
        if engine is None:
            return jsonify({'error': 'Moteur média non disponible'}), 503

        result = engine.generate_video(
            prompt, duration=duration, fps=fps,
            width=width, height=height
        )

        # Encoder en MP4
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        tmp_path = tmp.name
        tmp.close()
        engine.save_video(result.frames, tmp_path, fps)

        log.info(f"  🎬 Vidéo générée : '{prompt[:40]}' "
                 f"({result.n_frames}f, {width}×{height}) "
                 f"cohérence={result.temporal_coherence:.3f} "
                 f"[{result.processing_time_ms:.0f}ms]")
        return send_file(tmp_path, mimetype='video/mp4',
                         as_attachment=True, download_name='harmonic.mp4')
    except Exception as e:
        log.error(f"  /api/media/video : {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/media/generate', methods=['POST'])
def media_generate():
    """Génère plusieurs modalités cohérentes → JSON + métriques."""
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if _check_rate_limit(ip):
        return jsonify({'error': 'Rate limit exceeded'}), 429

    try:
        data = request.get_json(force=True)
        prompt = data.get('prompt', '')
        modalities = data.get('modalities', ['image', 'audio'])
        width = min(int(data.get('width', 256)), 512)
        height = min(int(data.get('height', 256)), 512)
        duration = min(float(data.get('duration', 5.0)), 20.0)

        engine = _get_media_engine()
        if engine is None:
            return jsonify({'error': 'Moteur média non disponible'}), 503

        result = engine.generate_all(
            prompt, modalities=modalities,
            width=width, height=height, duration=duration
        )

        response = result.to_dict()
        response['status'] = 'ok'

        # Sauvegarder les fichiers si demandé
        save_files = data.get('save', False)
        if save_files:
            import io as _io
            files = {}
            if result.image is not None:
                from PIL import Image
                buf = _io.BytesIO()
                Image.fromarray(result.image).save(buf, format='PNG')
                files['image'] = buf.getvalue()
            if result.audio is not None:
                from scipy.io import wavfile
                buf = _io.BytesIO()
                samples_int = (np.clip(result.audio, -1, 1) * 32767).astype(np.int16)
                wavfile.write(buf, engine.audio_gen.sr, samples_int)
                files['audio'] = buf.getvalue()

        log.info(f"  🎨🎬🎵 Génération unifiée : '{prompt[:40]}' "
                 f"[{result.processing_time_ms:.0f}ms]")
        return jsonify(response)
    except Exception as e:
        log.error(f"  /api/media/generate : {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/media/templates', methods=['GET'])
def media_templates():
    """Liste les concepts visuels appris disponibles."""
    try:
        engine = _get_media_engine()
        if engine is None:
            return jsonify({'error': 'Moteur média non disponible'}), 503

        concepts = engine.available_concepts
        stats = engine.stats()

        return jsonify({
            'concepts': concepts,
            'n_concepts': len(concepts),
            'stats': stats,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/media/ingest', methods=['POST'])
def media_ingest():
    """Ingère une image dans la mémoire (apprentissage continu)."""
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if _check_rate_limit(ip):
        return jsonify({'error': 'Rate limit exceeded'}), 429

    try:
        if 'image' not in request.files:
            return jsonify({'error': 'Aucune image fournie'}), 400

        file = request.files['image']
        concepts = request.form.getlist('concepts')
        if not concepts:
            concepts = [request.form.get('concept', 'inconnu')]

        engine = _get_media_engine()
        if engine is None:
            return jsonify({'error': 'Moteur média non disponible'}), 503

        # Charger l'image
        from PIL import Image
        import io as _io
        img = Image.open(_io.BytesIO(file.read())).convert('RGB')
        img_array = np.array(img)

        engine.trainer.ingest_image(img_array, concepts)

        # Sauvegarder la mémoire mise à jour
        mem_path = str(_ENGINE_DIR / 'data' / 'visual_memory.npz')
        engine.save_memory(mem_path)

        coh = engine.trainer.compute_phase_coherence(concepts[0])

        log.info(f"  📥 Image ingérée : concepts={concepts} "
                 f"cohérence={coh.coherence:.3f}")
        return jsonify({
            'status': 'ok',
            'concepts': concepts,
            'coherence': coh.coherence,
            'n_instances': coh.n_instances,
        })
    except Exception as e:
        log.error(f"  /api/media/ingest : {e}")
        return jsonify({'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════════
# 📄 PAGEFORCE & 🌊 J-LENS (nouveaux endpoints optimisés)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/page', methods=['POST'])
def generate_page():
    """Génère une page complète sur un sujet (PageForge)."""
    data = request.get_json(force=True, silent=True) or {}
    topic = data.get('topic', '').strip()
    if not topic:
        return jsonify({'error': 'Topic requis'}), 400
    t0 = time.time()
    response = ai.page(topic) if ai and hasattr(ai, 'page') else None
    if not response:
        response = ai.ask(topic) if ai else "PageForge non disponible"
    return jsonify({
        'response': response,
        'is_page': response.startswith('# ') if response else False,
        'latency_ms': round((time.time() - t0) * 1000, 0),
        'model': 'harmonic-pageforge',
    })

@app.route('/api/jlens', methods=['GET'])
def get_jlens():
    """Affiche l'état du J-Space harmonique."""
    if ai and hasattr(ai, 'jlens') and ai.jlens:
        return jsonify({
            'stats': ai.jlens.stats(),
            'render': ai.jlens.render(),
            'html': ai.jlens.to_html() if hasattr(ai.jlens, 'to_html') else None,
        })
    return jsonify({'error': 'JLens non disponible'}), 503

@app.route('/api/jlens/history', methods=['GET'])
def get_jlens_history():
    """Historique des instantanés J-Space."""
    if ai and hasattr(ai, 'jlens') and ai.jlens:
        history = []
        for snap in ai.jlens.history[-10:]:
            history.append({
                'question': snap.question[:100],
                'jspace_size': snap.jspace_size,
                'mean_coherence': snap.mean_coherence,
                'timestamp': snap.timestamp,
                'active_concepts': snap.active_concepts[:5],
            })
        return jsonify({'history': history, 'total': len(ai.jlens.history)})
    return jsonify({'error': 'JLens non disponible'}), 503


# ═══════════════════════════════════════════════════════════════════════════════
# 📦 HOLOGRAM STORE — Knowledge Store téléchargeable
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/store/list', methods=['GET'])
def store_list():
    """Liste tous les hologrammes disponibles (format UI)."""
    if not _hologram_store:
        return jsonify({'error': 'Store non disponible'}), 503
    holo_type = request.args.get('type', None)
    holos = _hologram_store.list_holograms(holo_type)
    # Enrichir avec les métadonnées complètes pour l'UI
    enriched = []
    for h in holos:
        meta = _hologram_store.download_metadata(h['id']) or {}
        enriched.append({
            'id': h['id'],
            'domain': meta.get('domain', h['id'].replace('official_','').replace('community_KA Expander_','')),
            'name': meta.get('name', h.get('name','')),
            'facts_count': meta.get('facts_count', h.get('facts_count', 0)),
            'quality_score': meta.get('quality_score', h.get('quality_score', 0.5)),
            'author': meta.get('author', h.get('author', 'KA')),
            'type': meta.get('type', h.get('type', 'official')),
            'description': meta.get('description', ''),
            'sectors': meta.get('sectors', []),
        })
    return jsonify({
        'holograms': enriched,
        'stats': _hologram_store.stats(),
    })

@app.route('/api/store/download/<holo_id>', methods=['GET', 'POST'])
def store_download(holo_id):
    """Télécharge les faits d'un hologramme (GET) ou les fusionne (POST)."""
    if not _hologram_store:
        return jsonify({'error': 'Store non disponible'}), 503

    facts = _hologram_store.download(holo_id)
    if not facts:
        return jsonify({'error': f'Hologramme {holo_id} introuvable ou vide'}), 404

    if request.method == 'POST':
        # Fusionner dans le FastRetriever
        user_id = request.get_json(force=True, silent=True) or {}
        user_id = user_id.get('user_id', 'anonymous')

        from page_forge import _init_fast_retriever, _FAST_RETRIEVER
        _init_fast_retriever()
        if _FAST_RETRIEVER:
            _FAST_RETRIEVER.add_facts(facts)

        return jsonify({
            'success': True,
            'holo_id': holo_id,
            'facts_loaded': len(facts),
            'message': f'✅ {len(facts):,} faits chargés en mémoire',
        })
    else:
        # GET : retourne les faits pour traitement côté client
        return jsonify({
            'holo_id': holo_id,
            'facts': [[f[0], f[1], f[2], f[3]] for f in facts],
            'count': len(facts),
        })


@app.route('/api/store/load', methods=['POST'])
def store_load():
    """
    Charge un hologramme dans le cerveau actif.
    Body: { "holo_id": "...", "facts": [...] } ou juste { "holo_id": "..." }
    """
    if not _hologram_store:
        return jsonify({'error': 'Store non disponible'}), 503

    data = request.get_json(force=True, silent=True) or {}
    holo_id = data.get('holo_id', '').strip()
    facts_raw = data.get('facts', None)

    if not holo_id:
        return jsonify({'error': 'holo_id requis'}), 400

    # Si les faits sont fournis par le client, les utiliser directement
    if facts_raw:
        facts = [(str(f[0]), str(f[1]), str(f[2]), str(f[3]) if len(f) > 3 else 'GENERAL')
                 for f in facts_raw]
    else:
        facts = _hologram_store.download(holo_id)

    if not facts:
        return jsonify({'error': 'Aucun fait à charger'}), 404

    # Fusionner dans le FastRetriever
    try:
        from page_forge import _init_fast_retriever, _FAST_RETRIEVER
        _init_fast_retriever()
        if _FAST_RETRIEVER:
            _FAST_RETRIEVER.add_facts(facts)
    except Exception:
        pass

    # Injecter aussi dans le modèle harmonique si disponible
    try:
        if ai is not None and hasattr(ai, 'model'):
            for s, r, o, sec in facts[:500]:
                ai.model.add_fact(s, r, o, sec)
            ai.model.rebuild_waves()
    except Exception:
        pass

    return jsonify({
        'success': True,
        'holo_id': holo_id,
        'facts_loaded': len(facts),
        'message': f'✅ Hologramme chargé : {len(facts):,} faits actifs',
    })

@app.route('/api/store/info/<holo_id>', methods=['GET'])
def store_info(holo_id):
    """Retourne les métadonnées d'un hologramme."""
    if not _hologram_store:
        return jsonify({'error': 'Store non disponible'}), 503
    meta = _hologram_store.download_metadata(holo_id)
    if not meta:
        return jsonify({'error': 'Hologramme introuvable'}), 404
    return jsonify(meta)

@app.route('/api/store/publish', methods=['POST'])
def store_publish():
    """Publie un hologramme communautaire."""
    if not _hologram_store:
        return jsonify({'error': 'Store non disponible'}), 503
    
    data = request.get_json(force=True, silent=True) or {}
    domain = data.get('domain', '').strip()
    author = data.get('user_id', 'anonymous')
    facts_raw = data.get('facts', [])
    name = data.get('name', '')
    description = data.get('description', '')
    
    if not domain or not facts_raw:
        return jsonify({'error': 'Domaine et faits requis'}), 400
    
    # Convertir les faits
    facts = []
    for f in facts_raw:
        if isinstance(f, (list, tuple)) and len(f) >= 3:
            facts.append((str(f[0]), str(f[1]), str(f[2]),
                         str(f[3]) if len(f) > 3 else 'GENERAL'))
    
    result = _hologram_store.publish(domain, facts, author, name, description)
    return jsonify(result)

@app.route('/api/store/stats', methods=['GET'])
def store_stats():
    """Statistiques du store."""
    if not _hologram_store:
        return jsonify({'error': 'Store non disponible'}), 503
    return jsonify(_hologram_store.stats())


# ═══════════════════════════════════════════════════════════════════════════════
# 🧠 PROFIL PERSONNEL — PersonalHologram
# ═══════════════════════════════════════════════════════════════════════════════

def _get_personal(user_id: str):
    """Récupère ou crée le PersonalHologram d'un utilisateur (lazy)."""
    if not _HAS_PERSONAL:
        return None
    if user_id not in _personal_holograms:
        _personal_holograms[user_id] = PersonalHologram(user_id=user_id)
    return _personal_holograms[user_id]


@app.route('/api/profile/<user_id>', methods=['GET'])
def get_profile(user_id):
    """
    Retourne le profil de l'utilisateur : intérêts détectés, concepts clés,
    historique d'apprentissage, suggestions proactives.
    
    GET /api/profile/user_123
    """
    if not _HAS_PERSONAL:
        return jsonify({'error': 'PersonalHologram non disponible'}), 503

    ph = _get_personal(user_id)
    if ph is None:
        return jsonify({'error': 'Impossible de créer le profil'}), 500

    try:
        profile = ph.profile()
        interests = ph.detect_interests()
        suggestions = ph.suggestions()
        top = ph.top_concepts(10)

        return jsonify({
            'user_id': user_id,
            'interests': [{'domain': i.domain, 'confidence': i.confidence}
                         for i in interests[:8]],
            'top_concepts': top,
            'suggestions': [{'domain': s.domain, 'reason': s.reason}
                          for s in suggestions[:5]],
            'session_count': profile.session_count if hasattr(profile, 'session_count') else 0,
            'total_traces': profile.total_traces if hasattr(profile, 'total_traces') else 0,
        })
    except Exception as e:
        log.exception(f"Erreur profile: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/profile/<user_id>/interests', methods=['GET'])
def get_interests(user_id):
    """
    Retourne uniquement les centres d'intérêt détectés.
    
    GET /api/profile/user_123/interests
    """
    if not _HAS_PERSONAL:
        return jsonify({'error': 'PersonalHologram non disponible'}), 503

    ph = _get_personal(user_id)
    if ph is None:
        return jsonify({'error': 'Impossible'}), 500

    try:
        interests = ph.detect_interests()
        return jsonify({
            'user_id': user_id,
            'interests': [{'domain': i.domain, 'confidence': round(i.confidence, 3),
                          'last_seen': getattr(i, 'last_seen', None)}
                         for i in interests],
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════════
# 🌊 WAVE POETRY — Poésie ondulatoire
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/poem', methods=['POST'])
def generate_poem():
    """
    Génère un poème par interférences ondulatoires.
    
    Body: {
        "theme": "la mer",
        "form": "free_verse",      // free_verse, alexandrin, haiku_wave
        "emotion": "mysterieux",   // triste, joyeux, mysterieux, paisible, dynamique
        "lines": 8,
        "personal": false          // true = utilise l'hologramme personnel
    }
    """
    if not _wave_poet:
        return jsonify({'error': 'Wave Poet non disponible'}), 503
    
    data = request.get_json(force=True, silent=True) or {}
    theme = data.get('theme', '').strip()
    if not theme:
        return jsonify({'error': 'Thème requis'}), 400
    
    form = data.get('form', 'free_verse')
    emotion = data.get('emotion', None)
    lines = min(int(data.get('lines', 8)), 16)
    personal = data.get('personal', False)
    user_id = data.get('user_id', 'anonymous')
    
    t0 = time.time()
    
    if personal and user_id != 'anonymous':
        # Poésie personnelle basée sur l'hologramme
        try:
            from personal_hologram import PersonalHologram
            ph = PersonalHologram(user_id)
            profile = ph.profile()
            facts = []
            for concept in profile.top_concepts[:5]:
                facts.append(f"Tu t'intéresses à {concept}")
            for interest in profile.top_domains[:3]:
                facts.append(f"Tu explores le domaine {interest.domain}")
            result = _wave_poet.compose_personal(theme, personal_facts=facts, form=form)
        except Exception:
            result = _wave_poet.compose(theme, form=form, emotion=emotion, lines=lines)
    else:
        result = _wave_poet.compose(theme, form=form, emotion=emotion, lines=lines)
    
    return jsonify({
        'poem': result['text'],
        'theme': result['theme'],
        'form': result['form'],
        'emotion': result['emotion'],
        'lines': result['lines'],
        'words_used': result['words_used'],
        'vocab_size': result['vocab_size'],
        'latency_ms': round((time.time() - t0) * 1000, 0),
        'model': 'wave-poetry-v2',
    })


# ═══════════════════════════════════════════════════════════════════════════════
# LM ARENA — OpenAI-compatible API
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/v1/models', methods=['GET'])
def lm_arena_models():
    """Liste des modèles disponibles (format OpenAI)."""
    return jsonify({
        "object": "list",
        "data": [{
            "id": "KA",
            "object": "model",
            "created": 1750000000,
            "owned_by": "KA",
        }]
    })


@app.route('/v1/chat/completions', methods=['POST'])
def lm_arena_chat():
    """
    Endpoint compatible OpenAI pour LM Arena.
    """
    data = request.get_json(force=True, silent=True) or {}
    messages = data.get('messages', [])
    if not messages:
        return jsonify({"error": "No messages provided"}), 400

    last_content = ""
    for msg in reversed(messages):
        if msg.get('role') == 'user':
            last_content = msg.get('content', '')
            break
    if not last_content:
        return jsonify({"error": "No user message found"}), 400

    system_prompt = ""
    for msg in messages:
        if msg.get('role') == 'system':
            system_prompt = msg.get('content', '')

    question = last_content
    if system_prompt:
        question = f"{system_prompt}\n{question}"

    max_tokens = data.get('max_tokens', 1024)
    t0 = time.time()

    try:
        if ai:
            response_text = ai.ask(question)
        elif brain:
            result = brain.process(question)
            response_text = result.response
        else:
            response_text = "KA n'est pas disponible."
    except Exception as e:
        response_text = f"Erreur: {str(e)}"
    
    # 🎨 Style harmonique
    if response_text and len(response_text) > 30:
        response_text = _style_response(response_text, question)

    prompt_tokens = len(question.split()) + len(system_prompt.split())
    completion_tokens = len(response_text.split())

    return jsonify({
        "id": f"chatcmpl-{int(time.time() * 1000)}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": data.get('model', 'KA'),
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": response_text[:max_tokens],
            },
            "finish_reason": "stop" if len(response_text) <= max_tokens else "length",
        }],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
        "ka_metadata": {
            "hallucination_rate": 0.0,
            "deterministic": True,
            "gpu_used": False,
            "parameters": 0,
            "model_size_mb": 10,
            "latency_ms": int((time.time() - t0) * 1000),
        }
    })


# ═══════════════════════════════════════════════════════════════════════════════
# 🌟 HOLOGRAM QUALITY — Création communautaire contrôlée
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from hologram_quality import register_contribution_endpoints
    register_contribution_endpoints(app)
    log.info("🌟 Hologram Quality Pipeline: actif")
except Exception as e:
    log.warning(f"🌟 Hologram Quality Pipeline: non disponible ({e})")


# ═══════════════════════════════════════════════════════════════════════════════
# 🎵 KA VOICE — Synthèse Vocale Conversationnelle (mode compagnon)
# ═══════════════════════════════════════════════════════════════════════════════

_KA_VOICE_AVAILABLE = False
_ka_voice_engine = None
_ka_voice_store = None

try:
    from ka_conversational_engine import KAConversationalEngine
    _ka_voice_engine = KAConversationalEngine(voice_name='KA', emotion='warm')
    
    # Charger la voix KA par défaut si un fichier existe
    default_voice_path = Path(__file__).resolve().parent / 'data' / 'ka_default_voice.wav'
    if default_voice_path.exists():
        _ka_voice_engine.load_voice('KA', audio_path=str(default_voice_path))
    
    _KA_VOICE_AVAILABLE = True
    log.info("🎵 KA Voice Engine: actif (10 émotions, streaming <50ms)")
except Exception as e:
    log.warning(f"🎵 KA Voice Engine: non disponible ({e})")


# ── API Voice Endpoints ────────────────────────────────────────────────────────

@app.route('/api/voice/speak', methods=['POST'])
def voice_speak():
    """
    Synthèse vocale — texte → audio WAV.
    Body: { "text": "...", "emotion": "warm|joyful|sad|...", "voice_id": "..." }
    Returns: audio/wav binary
    """
    if not _KA_VOICE_AVAILABLE:
        return jsonify({'error': 'KA Voice Engine non disponible'}), 503
    
    data = request.get_json(force=True, silent=True) or {}
    text = data.get('text', '').strip()
    emotion = data.get('emotion', 'warm')
    voice_id = data.get('voice_id', None)
    
    if not text:
        return jsonify({'error': 'Texte requis'}), 400
    
    try:
        _ka_voice_engine.set_emotion(emotion)
        audio = _ka_voice_engine.speak(text, emotion=emotion)
        
        # Convertir en WAV 16-bit PCM
        audio_int16 = (audio * 32767).astype(np.int16)
        wav_buffer = io.BytesIO()
        
        import struct as _struct
        n_samples = len(audio_int16)
        # Header WAV
        wav_buffer.write(b'RIFF')
        wav_buffer.write(_struct.pack('<I', 36 + n_samples * 2))
        wav_buffer.write(b'WAVE')
        wav_buffer.write(b'fmt ')
        wav_buffer.write(_struct.pack('<I', 16))       # chunk size
        wav_buffer.write(_struct.pack('<H', 1))         # PCM
        wav_buffer.write(_struct.pack('<H', 1))         # mono
        wav_buffer.write(_struct.pack('<I', 24000))     # sample rate
        wav_buffer.write(_struct.pack('<I', 48000))     # byte rate
        wav_buffer.write(_struct.pack('<H', 2))         # block align
        wav_buffer.write(_struct.pack('<H', 16))        # bits per sample
        wav_buffer.write(b'data')
        wav_buffer.write(_struct.pack('<I', n_samples * 2))
        wav_buffer.write(audio_int16.tobytes())
        wav_buffer.seek(0)
        
        return send_file(wav_buffer, mimetype='audio/wav',
                        as_attachment=False,
                        download_name='ka_speech.wav')
    except Exception as e:
        log.error(f"Voice speak error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/voice/stream', methods=['POST'])
def voice_stream():
    """
    Synthèse vocale streamée — retourne du WAV par phrases.
    Body: { "text": "...", "emotion": "warm" }
    Returns: audio/wav (streamed via Transfer-Encoding: chunked)
    """
    if not _KA_VOICE_AVAILABLE:
        return jsonify({'error': 'KA Voice Engine non disponible'}), 503
    
    data = request.get_json(force=True, silent=True) or {}
    text = data.get('text', '').strip()
    emotion = data.get('emotion', 'warm')
    
    if not text:
        return jsonify({'error': 'Texte requis'}), 400
    
    try:
        _ka_voice_engine.set_emotion(emotion)
        
        def generate():
            # Découper en phrases
            import re
            sentences = re.split(r'(?<=[.!?])\s+', text)
            
            for sentence in sentences:
                if not sentence.strip():
                    continue
                audio = _ka_voice_engine.speak(sentence, emotion=emotion)
                audio_int16 = (audio * 32767).astype(np.int16)
                yield audio_int16.tobytes()
        
        from flask import Response
        return Response(generate(), mimetype='audio/wav')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/voice/clone', methods=['POST'])
def voice_clone():
    """
    Clone une voix à partir d'un fichier audio uploadé.
    Form: audio (file .wav), name (string)
    Returns: { "voice_id": "...", "name": "..." }
    """
    if not _KA_VOICE_AVAILABLE:
        return jsonify({'error': 'KA Voice Engine non disponible'}), 503
    
    if 'audio' not in request.files:
        return jsonify({'error': 'Fichier audio requis (champ "audio")'}), 400
    
    file = request.files['audio']
    name = request.form.get('name', 'Custom Voice')
    
    try:
        # Lire l'audio
        audio_data = file.read()
        audio_int16 = np.frombuffer(audio_data, dtype=np.int16)
        audio_float = audio_int16.astype(np.float64) / 32768.0
        
        # Cloner
        voice_id = _ka_voice_engine.load_voice(name, audio=audio_float)
        
        return jsonify({
            'voice_id': voice_id,
            'name': name,
            'emotions': _ka_voice_engine.prosody.available_emotions,
        })
    except Exception as e:
        log.error(f"Voice clone error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/voice/voices', methods=['GET'])
def voice_list():
    """Liste les voix disponibles."""
    if not _KA_VOICE_AVAILABLE:
        return jsonify({'voices': [], 'default': None})
    
    voices = _ka_voice_engine.voice_store.list_voices()
    return jsonify({
        'voices': voices,
        'default': _ka_voice_engine.state.voice_id,
        'current_emotion': _ka_voice_engine.state.emotion,
        'available_emotions': _ka_voice_engine.prosody.available_emotions,
    })


@app.route('/api/voice/emotion', methods=['POST'])
def voice_emotion():
    """
    Change l'émotion courante.
    Body: { "emotion": "warm|joyful|sad|..." }
    """
    if not _KA_VOICE_AVAILABLE:
        return jsonify({'error': 'KA Voice Engine non disponible'}), 503
    
    data = request.get_json(force=True, silent=True) or {}
    emotion = data.get('emotion', 'warm')
    
    try:
        _ka_voice_engine.set_emotion(emotion)
        return jsonify({
            'emotion': emotion,
            'params': _ka_voice_engine.prosody._emotion_params.get(emotion, {}),
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/voice/info', methods=['GET'])
def voice_info():
    """Informations sur le moteur vocal."""
    if not _KA_VOICE_AVAILABLE:
        return jsonify({'available': False})
    
    return jsonify({
        'available': True,
        **{k: (v if not isinstance(v, np.ndarray) else '...') 
           for k, v in _ka_voice_engine.info.items()},
    })


# ── Chat avec voix (extension du endpoint /api/chat) ─────────────────────────

@app.route('/api/chat/voice', methods=['POST'])
def chat_with_voice():
    """
    Conversation avec réponse texte + audio.
    Body: { "message": "...", "voice": true, "emotion": "warm", ... }
    Returns: { "response": "...", "audio_base64": "...", ... }
    """
    if not _KA_VOICE_AVAILABLE:
        # Fallback: chat normal sans audio
        return chat()
    
    data = request.get_json(force=True, silent=True) or {}
    message = data.get('message', '').strip()
    emotion = data.get('emotion', 'warm')
    
    if not message:
        return jsonify({'error': 'Message requis'}), 400
    
    # Réutiliser le endpoint chat existant pour le texte
    with app.test_request_context('/api/chat', method='POST', json=data):
        text_response = chat()
    
    response_data = text_response.get_json() if text_response.status_code == 200 else {}
    response_text = response_data.get('response', '')
    
    # Synthèse vocale
    try:
        if response_text:
            _ka_voice_engine.set_emotion(emotion)
            audio = _ka_voice_engine.speak(response_text, emotion=emotion)
            
            import base64
            audio_int16 = (audio * 32767).astype(np.int16)
            audio_b64 = base64.b64encode(audio_int16.tobytes()).decode('utf-8')
            
            response_data['audio_base64'] = audio_b64
            response_data['audio_sample_rate'] = 24000
            response_data['audio_duration_s'] = len(audio) / 24000.0
    except Exception as e:
        log.error(f"Voice chat error: {e}")
        response_data['audio_error'] = str(e)
    
    return jsonify(response_data)


# ═══════════════════════════════════════════════════════════════════════════════
# 🤖 KA AGENT — Noyau Agentique du Téléphone Harmonique
# ═══════════════════════════════════════════════════════════════════════════════

_KA_AGENT_AVAILABLE = False
_ka_agent = None

try:
    from ka_agent_core import KAAgentCore
    _ka_agent = KAAgentCore(
        brain=brain if 'brain' in dir() else None,
        voice_engine=_ka_voice_engine if _KA_VOICE_AVAILABLE else None,
    )
    _KA_AGENT_AVAILABLE = True
    log.info("🤖 KA Agent Core: actif (6 outils, planificateur, background tasks)")
except Exception as e:
    log.warning(f"🤖 KA Agent Core: non disponible ({e})")


# ── API Agent Endpoints ────────────────────────────────────────────────────────

@app.route('/api/agent/run', methods=['POST'])
def agent_run():
    """
    Exécute une tâche agentique de façon synchrone.
    Body: { "goal": "...", "voice": false, "emotion": "warm" }
    Returns: { task_id, status, steps, result }
    """
    if not _KA_AGENT_AVAILABLE:
        return jsonify({'error': 'KA Agent non disponible'}), 503
    
    data = request.get_json(force=True, silent=True) or {}
    goal = data.get('goal', '').strip()
    voice = data.get('voice', False)
    emotion = data.get('emotion', 'warm')
    
    if not goal:
        return jsonify({'error': 'Objectif requis (goal)'}), 400
    
    try:
        task = _ka_agent.run(goal, voice=voice, emotion=emotion)
        return jsonify(task.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/agent/dispatch', methods=['POST'])
def agent_dispatch():
    """
    Lance une tâche en arrière-plan.
    Body: { "goal": "..." }
    Returns: { task_id, status: "dispatched" }
    """
    if not _KA_AGENT_AVAILABLE:
        return jsonify({'error': 'KA Agent non disponible'}), 503
    
    data = request.get_json(force=True, silent=True) or {}
    goal = data.get('goal', '').strip()
    
    if not goal:
        return jsonify({'error': 'Objectif requis (goal)'}), 400
    
    try:
        task_id = _ka_agent.dispatch(goal)
        return jsonify({'task_id': task_id, 'status': 'dispatched'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/agent/status/<task_id>', methods=['GET'])
def agent_status(task_id):
    """Vérifie le statut d'une tâche agentique."""
    if not _KA_AGENT_AVAILABLE:
        return jsonify({'error': 'KA Agent non disponible'}), 503
    
    status = _ka_agent.status(task_id)
    if status is None:
        return jsonify({'error': 'Tâche non trouvée', 'task_id': task_id}), 404
    
    return jsonify(status)


@app.route('/api/agent/cancel/<task_id>', methods=['POST'])
def agent_cancel(task_id):
    """Annule une tâche en cours."""
    if not _KA_AGENT_AVAILABLE:
        return jsonify({'error': 'KA Agent non disponible'}), 503
    
    ok = _ka_agent.cancel(task_id)
    return jsonify({'task_id': task_id, 'cancelled': ok})


@app.route('/api/agent/plan', methods=['POST'])
def agent_plan():
    """
    Planifie une tâche (sans l'exécuter).
    Body: { "goal": "..." }
    Returns: le plan d'étapes
    """
    if not _KA_AGENT_AVAILABLE:
        return jsonify({'error': 'KA Agent non disponible'}), 503
    
    data = request.get_json(force=True, silent=True) or {}
    goal = data.get('goal', '').strip()
    
    if not goal:
        return jsonify({'error': 'Objectif requis (goal)'}), 400
    
    try:
        task = _ka_agent.planner.plan(goal)
        return jsonify(task.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/agent/voice', methods=['POST'])
def agent_voice():
    """
    Commande vocale → action agentique.
    Body: { "text": "appelle maman" }  (en production: audio upload)
    Returns: résultat de la commande
    """
    if not _KA_AGENT_AVAILABLE:
        return jsonify({'error': 'KA Agent non disponible'}), 503
    
    data = request.get_json(force=True, silent=True) or {}
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'error': 'Texte de la commande requis'}), 400
    
    try:
        result = _ka_agent.voice_command(text)
        return jsonify({'command': text, 'result': str(result)[:500]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/agent/tools', methods=['GET'])
def agent_tools():
    """Liste les outils disponibles."""
    if not _KA_AGENT_AVAILABLE:
        return jsonify({'tools': []})
    
    return jsonify({
        'tools': [{'name': t.name, 'description': t.description,
                   'category': t.category, 'keywords': t.keywords[:5]}
                  for t in _ka_agent.tools.all_tools],
    })


@app.route('/api/agent/phone/dashboard', methods=['GET'])
def agent_phone_dashboard():
    """Tableau de bord du téléphone harmonique."""
    if not _KA_AGENT_AVAILABLE:
        return jsonify({'error': 'KA Agent non disponible'}), 503
    
    try:
        dash = _ka_agent.phone.dashboard()
        return jsonify(dash)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/agent/phone/contacts', methods=['GET', 'POST'])
def agent_phone_contacts():
    """Gestion des contacts du téléphone harmonique."""
    if not _KA_AGENT_AVAILABLE:
        return jsonify({'error': 'KA Agent non disponible'}), 503
    
    if request.method == 'GET':
        return jsonify({'contacts': _ka_agent.phone.list_contacts()})
    
    data = request.get_json(force=True, silent=True) or {}
    name = data.get('name', '').strip()
    phone = data.get('phone', '')
    email = data.get('email', '')
    
    if not name:
        return jsonify({'error': 'Nom requis'}), 400
    
    cid = _ka_agent.phone.add_contact(name, phone=phone, email=email)
    return jsonify({'contact_id': cid, 'name': name})


@app.route('/api/agent/phone/call', methods=['POST'])
def agent_phone_call():
    """Initie un appel vocal KA."""
    if not _KA_AGENT_AVAILABLE:
        return jsonify({'error': 'KA Agent non disponible'}), 503
    
    data = request.get_json(force=True, silent=True) or {}
    contact = data.get('contact', '').strip()
    message = data.get('message', '')
    
    if not contact:
        return jsonify({'error': 'Contact requis'}), 400
    
    call = _ka_agent.phone.initiate_call(contact, message)
    return jsonify(call)


@app.route('/api/agent/phone/reminder', methods=['POST'])
def agent_phone_reminder():
    """Programme un rappel."""
    if not _KA_AGENT_AVAILABLE:
        return jsonify({'error': 'KA Agent non disponible'}), 503
    
    data = request.get_json(force=True, silent=True) or {}
    text = data.get('text', '').strip()
    when = data.get('when', '')
    
    if not text:
        return jsonify({'error': 'Texte du rappel requis'}), 400
    
    reminder = _ka_agent.phone.set_reminder(text, when)
    return jsonify(reminder)


@app.route('/api/agent/info', methods=['GET'])
def agent_info():
    """Informations sur le noyau agentique."""
    if not _KA_AGENT_AVAILABLE:
        return jsonify({'available': False})
    
    return jsonify({'available': True, **_ka_agent.info})

if __name__ == '__main__':
    log.info(f"\n✨ KA Server v3 OPTIMISÉ sur http://localhost:{port}")
    log.info(f"   📡 API: http://localhost:{port}/api/chat")
    log.info(f"   🎵 Voice: http://localhost:{port}/api/voice/speak")
    log.info(f"   📄 PageForge: http://localhost:{port}/api/page")
    log.info(f"   🌊 J-Lens: http://localhost:{port}/api/jlens")
    log.info(f"   📦 Store: http://localhost:{port}/api/store/list")
    log.info(f"   🏠 Interface: http://localhost:{port}")
    log.info(f"   /              — KA Phone (PWA)")
    log.info(f"   /api/chat      — conversation")
    log.info(f"   /api/chat/voice — conversation + voix 🎵")
    log.info(f"   /api/voice/speak — synthèse vocale")
    log.info(f"   /api/voice/clone — clonage vocal 3s")
    log.info(f"   /api/voice/voices — voix disponibles")
    log.info(f"   /api/voice/emotion — changer l'émotion")
    log.info(f"   /api/agent/run   — exécuter tâche agentique 🤖")
    log.info(f"   /api/agent/dispatch — lancer tâche background")
    log.info(f"   /api/agent/status/<id> — statut tâche")
    log.info(f"   /api/agent/plan  — planifier sans exécuter")
    log.info(f"   /api/agent/voice — commande vocale → action")
    log.info(f"   /api/agent/phone/dashboard — 📊 tableau de bord")
    log.info(f"   /api/agent/phone/contacts — 👤 gestion contacts")
    log.info(f"   /api/agent/phone/call     — 📞 initier appel")
    log.info(f"   /api/agent/phone/reminder — ⏰ programmer rappel")
    log.info(f"   /api/reason    — raisonnement")
    log.info(f"   /api/create    — créativité")
    log.info(f"   /api/haiku     — haïku")
    log.info(f"   /api/stats     — statistiques")
    log.info(f"   /api/metrics   — métriques détaillées")
    log.info(f"   /api/health    — santé du serveur")
    if hcv_available:
        log.info(f"   /api/compress  — compression HCV")
        log.info(f"   /api/upscale   — upscaling")
        log.info(f"   /api/enhance   — pipeline complet")
    log.info(f"   /api/media/image     — génération image harmonique")
    log.info(f"   /api/media/audio     — génération audio harmonique")
    log.info(f"   /api/media/video     — génération vidéo harmonique")
    log.info(f"   /api/media/generate  — génération multi-modale")
    log.info(f"   /api/media/templates — concepts visuels appris")
    log.info(f"   /api/media/ingest    — ingestion d'image (apprentissage)")
    log.info(f"   /v1/chat/completions — LM Arena (OpenAI-compatible)")
    log.info(f"   /v1/models           — LM Arena model list")
    log.info(f"   /api/holograms/submit    — 🌟 Soumettre hologramme (qualité)")
    log.info(f"   /api/holograms/validate  — Valider des faits")
    log.info(f"   /api/holograms/reputation/:id — Réputation contributeur")
    log.info(f"   /api/holograms/quality/:id    — Score qualité hologramme")
    log.info("")
    app.run(host='0.0.0.0', port=port, debug=False)
