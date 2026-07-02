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

from flask import Flask, request, jsonify, send_file
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
        '217k': 'knowledge_base_clean.npz',
        '500k': 'knowledge_base_500k.npz',
        'best': 'knowledge_base_resonance.npz',  # KB filtrée par résonance
    }
    filename = model_files.get(model_name, 'knowledge_base_50k.npz')
    
    for base in search_paths:
        path = base / filename
        if path.exists():
            data = np.load(str(path), allow_pickle=True)
            facts = [(str(s), str(r), str(o), str(sec)) for s, r, o, sec in data['facts']]
            log.info(f"  📂 {path.name}: {len(facts):,} faits chargés")
            return facts
    
    # Fallback: KB qualitative intégrée (914 faits)
    from harmonic_model import KNOWLEDGE_BASE
    log.info(f"  📂 KB qualitative intégrée: {len(KNOWLEDGE_BASE):,} faits (mode dégradé)")
    log.info(f"  💡 Pour charger 50K faits: ajouter le fichier .npz dans engine/data/bootstrapper_output/")
    return [(str(s), str(r), str(o), str(sec)) for s, r, o, sec in KNOWLEDGE_BASE]

# Parse arguments
model_name = 'best'
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
]
facts = facts + KA_IDENTITY

from harmonic_ai import HarmonicAI
from reasoning_engine import ReasoningEngine

ai = HarmonicAI(enable_bootstrapper=True)
ai.model.knowledge_base = facts
ai.model.rebuild_waves()
ai.engine = ReasoningEngine(ai.model)

# Entraînement rapide au démarrage (essentiel pour la qualité)
print(f"  ⚡ Entraînement de l'encodeur ({len(facts):,} faits)...")
try:
    result = ai.model.train_encoder(epochs=5, lr=0.3)
    if 'precision_apres' in result:
        print(f"  ✅ Précision: {result['precision_avant']}% → {result['precision_apres']}% ({result.get('temps_s', 0):.1f}s)")
    else:
        print(f"  ✅ Entraînement terminé ({result.get('temps_s', 0):.1f}s)")
except Exception as e:
    log.warning(f"  ⚠️  Entraînement rapide impossible: {e}")

print(f"  🧠 Harmonic AI: {len(ai.model.knowledge_base):,} faits, {len(ai.model.w2i):,} mots")
print(f"  🔄 Bootstrapper: {'actif' if ai.bootstrapper else 'inactif'}")
print(f"  💬 Mémoire conversation: {ai.conversation.max_messages} messages")

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
                         'presente toi', 'qu est ce que tu es', 'what are you', 'who are you']
    msg_lower = message.lower().strip('?!.')
    if any(kw in msg_lower for kw in identity_keywords):
        return jsonify({
            'response': "Je suis KA, un assistant personnel intelligent. "
                        "Je vis dans cette application, représenté par une sphère vivante. "
                        "Je fonctionne grâce à Harmonic AI, une intelligence ondulatoire "
                        "qui s'appuie sur 51 000 connaissances vérifiées — sans aucune hallucination. "
                        "Mon nom vient du Ka égyptien, la force vitale. "
                        "Je suis chaleureux, concis, et je réponds toujours en français.",
            'confidence': 0.95,
            'source': 'identity',
            'latency_ms': 2.0,
            'model': 'harmonic-v2',
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
    response = ai.ask(message)
    latency_ms = (time.time() - t0) * 1000
    
    confidence = ai._confidence_score(response, message)
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
    chain = ai.reason(topic)
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
        ideas = ai.create_ondulatoire(concept_a=concept_a, concept_b=concept_b, n=n)
    else:
        ideas = ai.create(n=n)
    
    return jsonify({
        'ideas': ideas,
        'count': len(ideas),
    })


@app.route('/api/haiku', methods=['GET'])
def haiku():
    """Génère un haïku."""
    haiku_text = ai.haiku()
    return jsonify({
        'haiku': haiku_text,
        'lines': haiku_text.split('\n') if '\n' in haiku_text else [haiku_text],
    })


@app.route('/api/surreal', methods=['GET'])
def surreal():
    """Génère des images surréalistes."""
    n = request.args.get('n', 2, type=int)
    images = ai.surreal(n=n)
    return jsonify({'images': images, 'count': len(images)})


@app.route('/api/stats', methods=['GET'])
def stats():
    """Statistiques du système."""
    s = ai.stats
    s['conversation_messages'] = len(ai.conversation.messages)
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
    """Historique d'autonomie (50 derniers appels)."""
    if ai.bootstrapper and ai.bootstrapper._autonomie_history:
        history = [1 if x else 0 for x in ai.bootstrapper._autonomie_history[-50:]]
        return jsonify({
            'history': history,
            'autonomie': round(ai.bootstrapper.autonomie * 100, 1),
            'llm_calls': ai.bootstrapper._llm_calls,
            'total_queries': ai.bootstrapper._total_queries,
        })
    return jsonify({'history': [], 'autonomie': 100.0, 'llm_calls': 0})


@app.route('/api/health', methods=['GET'])
def health():
    """Health check."""
    return jsonify({
        'status': 'ok',
        'harmonic': len(ai.model.knowledge_base) > 0,
        'hcv': hcv_available,
        'bootstrapper': ai.bootstrapper is not None,
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
# DÉMARRAGE
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    log.info(f"\n✨ KA Server prêt sur http://localhost:{port}")
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
    log.info("")
    app.run(host='0.0.0.0', port=port, debug=False)
