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

import sys, os, io, time, json
from pathlib import Path

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
CORS(app)

print("=" * 55)
print("  KA SERVER — Harmonic AI + HCV Compression")
print("=" * 55)

# ── Chargement du modèle Harmonic ──────────────────────────────────────────

def load_facts(model_name='best'):
    """Charge la base de connaissance."""
    model_files = {
        '50k':  '../data/bootstrapper_output/knowledge_base_50k.npz',
        '217k': '../data/bootstrapper_output/knowledge_base_clean.npz',
        '500k': '../data/bootstrapper_output/knowledge_base_500k.npz',
        'best': '../data/bootstrapper_output/knowledge_base_50k.npz',
    }
    path = model_files.get(model_name, model_files['best'])
    if not Path(path).exists():
        print(f"  [!] Fichier introuvable: {path}")
        return None
    data = np.load(str(path), allow_pickle=True)
    facts = [(str(s), str(r), str(o), str(sec)) for s, r, o, sec in data['facts']]
    print(f"  📂 {Path(path).name}: {len(facts):,} faits chargés")
    return facts

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
if facts is None:
    print("  [!] Impossible de charger les faits. Démarrage en mode dégradé.")
    facts = []

from harmonic_ai import HarmonicAI
from reasoning_engine import ReasoningEngine

ai = HarmonicAI(enable_bootstrapper=True)
if facts:
    ai.model.knowledge_base = facts[:30000]  # 30K pour démarrage rapide
    ai.model.rebuild_waves()
ai.engine = ReasoningEngine(ai.model)

print(f"  🧠 Harmonic AI: {len(ai.model.knowledge_base):,} faits, {len(ai.model.w2i):,} mots")
print(f"  🔄 Bootstrapper: {'actif' if ai.bootstrapper else 'inactif'}")
print(f"  💬 Mémoire conversation: {ai.conversation.max_messages} messages")

# ── HCV (optionnel) ─────────────────────────────────────────────────────────

hcv_available = False
try:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'HCV-Compression-Engine'))
    from codecs.hcv_android_boost_codec import HCVAndroidBoostCodec
    from mobile.upscaler import HCVUpscaler
    hcv_available = True
    print("  📦 HCV Compression: disponible")
except ImportError:
    print("  📦 HCV Compression: non disponible (codecs à restaurer)")

print(f"  🌐 Serveur: http://localhost:{port}")
print("=" * 55)

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
    
    # Injecter le contexte si fourni
    if context:
        message = f"{context}\n{message}"
    
    t0 = time.time()
    response = ai.ask(message)
    latency_ms = (time.time() - t0) * 1000
    
    confidence = ai._confidence_score(response, message)
    source = 'harmonic' if confidence >= 0.35 else 'llm'
    
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
    return jsonify(s)


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
    codec = HCVAndroidBoostCodec(preset='balanced')
    try:
        compressed, ratio = codec.compress(input_data)
        return jsonify({
            'original_size': original_size,
            'compressed_size': len(compressed),
            'ratio': round(ratio, 1),
            'saved_percent': round((1 - 1/max(ratio, 1)) * 100, 1),
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
    upscaled = upscaler.upscale(img, factor=scale)
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
    codec = HCVAndroidBoostCodec(preset='balanced')
    upscaler = HCVUpscaler()
    
    try:
        # 1. Compresser
        compressed, ratio = codec.compress(input_data)
        # 2. Décompresser
        decompressed = codec.decompress(compressed)
        # 3. Upscaler
        img = cv2.imdecode(np.frombuffer(decompressed, np.uint8), cv2.IMREAD_COLOR)
        upscaled = upscaler.upscale(img, factor=2)
        _, buffer = cv2.imencode('.jpg', upscaled, [cv2.IMWRITE_JPEG_QUALITY, 90])
        
        return send_file(io.BytesIO(buffer), mimetype='image/jpeg')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMARRAGE
# ═══════════════════════════════════════════════════════════════════════════════

SERVER_START = time.time()

if __name__ == '__main__':
    print(f"\n✨ KA Server prêt sur http://localhost:{port}")
    print(f"   /api/chat     — conversation")
    print(f"   /api/reason   — raisonnement")
    print(f"   /api/create   — créativité")
    print(f"   /api/haiku    — haïku")
    print(f"   /api/stats    — statistiques")
    print(f"   /api/health   — santé du serveur")
    if hcv_available:
        print(f"   /api/compress — compression HCV")
        print(f"   /api/upscale  — upscaling")
        print(f"   /api/enhance  — pipeline complet")
    print()
    app.run(host='0.0.0.0', port=port, debug=False)
