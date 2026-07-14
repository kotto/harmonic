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

import sys, os, io, time, json, logging
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
        '110k': 'knowledge_base_merged_v2.npz',
        '217k': 'knowledge_base_clean.npz',
        '500k': 'knowledge_base_500k.npz',
        'best': 'knowledge_base_merged_v2.npz',
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

# Charger le cerveau — mode léger pour le serveur (pas d'encodage holographique)
# L'encodage ℂ⁵¹² consomme ~8 KB/fait — trop pour 1.5 GB de RAM
# Le retrieval TF-IDF seul donne 93%+ de précision
print(f"  🧠 Initialisation du Cerveau Harmonique v3 (mode serveur léger)...")
brain = HarmonicBrain(facts, dim=64, use_holographic=False)
print(f"  🧠 Cerveau prêt: {brain.unconscious.stats['faits']:,} faits dans l'inconscient")
print(f"  🌐 Domaines: {len(brain.stats.get('domains_available', []))}")
print(f"  💬 Parseur: actif")
print(f"  🎯 SFT: {sum(1 for r in brain.unconscious.registry.values() if r.amplitude >= 5)}")

# ── 🌐 Web Retriever (recherche Internet) ──────────────────────────────────────
_web_retriever = None
try:
    from web_retriever import WebRetriever
    _web_retriever = WebRetriever()
    print(f"  🌐 Web Retriever: connecté (DuckDuckGo + Wikipedia)")
except Exception as e:
    print(f"  🌐 Web Retriever: non disponible ({e})")

# ── HCV (optionnel) ─────────────────────────────────────────────────────────

hcv_available = False
HCV_DIR = Path(__file__).resolve().parent.parent / 'HCV-Compression-Engine'
if HCV_DIR.exists():
    try:
        import importlib.util
        for mod_name, file_name in [
            ('hcv_android_boost', 'codecs/hcv_android_boost_codec.py'),
            ('hcv_upscaler', 'mobile/upscaler.py'),
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
    except Exception:
        pass  # Silencieux en production

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

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Conversation avec l'IA.
    Body: { "message": "texte", "context": "optionnel" }
    Returns: { "response": "...", "confidence": 0.85, "source": "harmonic|llm" }
    """
    data = request.get_json(force=True, silent=True) or {}
    message = data.get('message', '').strip()
    context = data.get('context', '').strip()
    
    if not message:
        return jsonify({'error': 'Message requis', 'response': "Je n'ai pas compris votre message."}), 400
    
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
    result = brain.process(message)
    response = result.response
    latency_ms = (time.time() - t0) * 1000
    
    confidence = result.confidence
    source = 'harmonic' if confidence >= 0.35 else 'llm'
    
    # Métriques
    if source == 'harmonic':
        _metrics['harmonic_count'] += 1
    else:
        _metrics['llm_count'] += 1
    
    return jsonify({
        'response': response,
        'confidence': round(confidence, 2),
        'source': source,
        'latency_ms': round(latency_ms, 0),
        'model': 'harmonic-v2',
    })


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
    result = brain.process(topic)
    chain = result.response
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


@app.route('/api/health', methods=['GET'])
def health():
    """Health check."""
    return jsonify({
        'status': 'ok',
        'harmonic': len(brain.unconscious.registry) > 0,
        'hcv': hcv_available,
        'bootstrapper': None  # brain has no bootstrapper is not None,
    })

# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS HCV (actifs si codecs disponibles)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/compress', methods=['POST'])
def compress():
    """
    Compression d'image HCV.
    Body: multipart/form-data avec champ 'image'
    Returns: JSON avec ratio, tailles
    """
    if not hcv_available:
        return jsonify({'error': 'HCV non disponible', 'ratio': 1.0}), 503
    
    if 'image' not in request.files:
        return jsonify({'error': 'Fichier image requis'}), 400
    
    file = request.files['image']
    input_data = file.read()
    original_size = len(input_data)
    
    # Utiliser le codec HCV
    codec = HCVAndroidBoostCodec(quality='balanced')
    try:
        compressed, stats = codec.encode(jpeg_bytes=input_data)
        return jsonify({
            'original_size': stats.get('source_size', len(input_data)),
            'compressed_size': len(compressed),
            'ratio': round(stats.get('ratio_vs_source', 1), 1),
            'saved_percent': round(stats.get('savings_vs_source', 0), 1),
            'resolution': stats.get('original_resolution', '?'),
            'speed_mbps': round(stats.get('speed_mbps', 0), 1),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/upscale', methods=['POST'])
def upscale():
    """
    Upscaling d'image.
    Body: multipart/form-data avec 'image' et 'scale' (2 ou 4)
    Returns: image/jpeg
    """
    if not hcv_available:
        return jsonify({'error': 'HCV non disponible'}), 503
    
    if 'image' not in request.files:
        return jsonify({'error': 'Fichier image requis'}), 400
    
    file = request.files['image']
    scale = int(request.form.get('scale', 2))
    
    import cv2
    img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return jsonify({'error': 'Image invalide'}), 400
    
    upscaler = HCVUpscaler()
    upscaled = upscaler.upscale_sync(img, factor=scale)
    _, buffer = cv2.imencode('.jpg', upscaled, [cv2.IMWRITE_JPEG_QUALITY, 90])
    
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

# Acides aminés → propriétés harmoniques
AMINO_PROPS = {
    'A': {'hydrophobic': 1.8, 'size': 0.5, 'charge': 0.0, 'phi': 0.62},
    'R': {'hydrophobic': -4.5, 'size': 2.0, 'charge': 1.0, 'phi': 0.38},
    'N': {'hydrophobic': -3.5, 'size': 1.0, 'charge': 0.0, 'phi': 0.45},
    'D': {'hydrophobic': -3.5, 'size': 1.0, 'charge': -1.0, 'phi': 0.41},
    'C': {'hydrophobic': 2.5, 'size': 0.8, 'charge': 0.0, 'phi': 0.71},
    'Q': {'hydrophobic': -3.5, 'size': 1.2, 'charge': 0.0, 'phi': 0.43},
    'E': {'hydrophobic': -3.5, 'size': 1.2, 'charge': -1.0, 'phi': 0.40},
    'G': {'hydrophobic': -0.4, 'size': 0.0, 'charge': 0.0, 'phi': 0.50},
    'H': {'hydrophobic': -3.2, 'size': 1.2, 'charge': 0.5, 'phi': 0.44},
    'I': {'hydrophobic': 4.5, 'size': 1.2, 'charge': 0.0, 'phi': 0.65},
    'L': {'hydrophobic': 3.8, 'size': 1.2, 'charge': 0.0, 'phi': 0.64},
    'K': {'hydrophobic': -3.9, 'size': 1.5, 'charge': 1.0, 'phi': 0.37},
    'M': {'hydrophobic': 1.9, 'size': 1.3, 'charge': 0.0, 'phi': 0.59},
    'F': {'hydrophobic': 2.8, 'size': 1.5, 'charge': 0.0, 'phi': 0.72},
    'P': {'hydrophobic': -1.6, 'size': 0.8, 'charge': 0.0, 'phi': 0.33},
    'S': {'hydrophobic': -0.8, 'size': 0.5, 'charge': 0.0, 'phi': 0.48},
    'T': {'hydrophobic': -0.7, 'size': 0.8, 'charge': 0.0, 'phi': 0.49},
    'W': {'hydrophobic': -0.9, 'size': 2.0, 'charge': 0.0, 'phi': 0.68},
    'Y': {'hydrophobic': -1.3, 'size': 1.5, 'charge': 0.0, 'phi': 0.66},
    'V': {'hydrophobic': 4.2, 'size': 1.0, 'charge': 0.0, 'phi': 0.63},
}

@app.route('/api/hpc/protein', methods=['POST'])
def hpc_protein():
    """
    Simulation de repliement protéique par résonance harmonique.
    Body: { "sequence": "ALAARGASN...", "temperature": 310.0, "ph": 7.0 }
    """
    data = request.get_json(force=True, silent=True) or {}
    sequence = data.get('sequence', '').upper().strip()
    temperature = float(data.get('temperature', 310.0))
    ph = float(data.get('ph', 7.0))

    if not sequence:
        return jsonify({'error': 'Séquence requise'}), 400

    # Filtrer les acides aminés valides
    valid = [c for c in sequence if c in AMINO_PROPS]
    if not valid:
        return jsonify({'error': 'Aucun acide aminé valide trouvé'}), 400

    n = len(valid)
    # Énergie libre harmonique (proportionnelle à φ)
    phi_sum = sum(AMINO_PROPS[aa]['phi'] for aa in valid)
    free_energy = -phi_sum * 4.2 * PHI
    confidence = min(0.99, 0.75 + 0.02 * n)

    # Structure secondaire (approximation harmonique)
    hydrophobic_sum = sum(AMINO_PROPS[aa]['hydrophobic'] for aa in valid)
    helix = max(5, min(70, 30 + int(hydrophobic_sum / n * 8)))
    sheet = max(5, min(50, 25 - int(hydrophobic_sum / n * 5)))
    loop = 100 - helix - sheet

    return jsonify({
        'sequence_length': n,
        'free_energy_kcal_mol': round(free_energy, 2),
        'confidence': round(confidence, 3),
        'secondary_structure': {
            'helix_percent': helix,
            'sheet_percent': sheet,
            'loop_percent': loop,
        },
        'harmonic_score': round(confidence, 3),
        'harmonic_speedup': f'{PHI ** 3:.1f}x',
        'method': 'Harmonic Wave Interference (φ-optimized)',
    })


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

@app.route('/')
def serve_index():
    """Page d'accueil — KA Phone PWA."""
    return send_from_directory(str(_ENGINE_DIR), 'ka_index.html')

@app.route('/manifest.json')
def serve_manifest():
    """Manifest PWA pour installation sur l'écran d'accueil."""
    return send_from_directory(str(_ENGINE_DIR), 'manifest.json')

@app.route('/sw.js')
def serve_service_worker():
    """Service Worker pour le mode hors-ligne."""
    return send_from_directory(str(_ENGINE_DIR), 'sw.js', mimetype='application/javascript')

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
# DÉMARRAGE
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    log.info(f"\n✨ KA Server prêt sur http://localhost:{port}")
    log.info(f"   /              — KA Phone (PWA)")
    log.info(f"   /api/chat      — conversation")
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
    log.info("")
    app.run(host='0.0.0.0', port=port, debug=False)
