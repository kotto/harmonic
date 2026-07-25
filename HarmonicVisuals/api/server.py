"""
HarmonicVisuals API — Serveur REST
===================================
Démarrage: python -m api.server --port 8800
Endpoints:
  POST /api/generate/geometric  → Mode A
  POST /api/generate/realistic  → Mode B
  POST /api/generate/hybrid     → Mode Hybride
  POST /api/generate/video      → Vidéo
  GET  /api/stats               → Statistiques
  POST /api/dictionary/build    → Construire dictionnaire
"""
import sys, os, io, time, base64
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))

try:
    from flask import Flask, request, jsonify, send_file
    from flask_cors import CORS
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

import numpy as np
from PIL import Image

from harmonic_visuals import HarmonicVisuals

app = Flask(__name__)
if HAS_FLASK: CORS(app)

hv = HarmonicVisuals()

@app.route('/api/generate/geometric', methods=['POST'])
def gen_geometric():
    d = request.get_json(force=True, silent=True) or {}
    prompt = d.get('prompt', 'abstract pattern')
    w, h = d.get('width', 512), d.get('height', 512)
    iters = d.get('iterations', 1)
    img = hv.generate_geometric(prompt, w, h, iters)
    return _image_response(img)

@app.route('/api/generate/hybrid', methods=['POST'])
def gen_hybrid():
    d = request.get_json(force=True, silent=True) or {}
    prompt = d.get('prompt', 'scene')
    w, h = d.get('width', 512), d.get('height', 512)
    img = hv.generate_hybrid(prompt, w, h)
    return _image_response(img)

@app.route('/api/generate/video', methods=['POST'])
def gen_video():
    d = request.get_json(force=True, silent=True) or {}
    prompt = d.get('prompt', 'flow')
    dur = d.get('duration', 3.0)
    fps = d.get('fps', 12)
    w, h = d.get('width', 256), d.get('height', 256)
    frames = hv.generate_video(prompt, dur, fps, w, h)
    return jsonify({'frames': len(frames), 'duration': dur, 'fps': fps})

@app.route('/api/pipeline', methods=['POST'])
def pipeline():
    d = request.get_json(force=True, silent=True) or {}
    result = hv.pipeline(
        prompt=d.get('prompt', 'test'),
        mode=d.get('mode', 'geometric'),
        width=d.get('width', 512), height=d.get('height', 512),
        upscale=d.get('upscale'), compress=d.get('compress', True),
    )
    img = result.pop('image')
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format='PNG')
    return jsonify({**result, 'image_base64': base64.b64encode(buf.getvalue()).decode()})

@app.route('/api/stats', methods=['GET'])
def stats():
    return jsonify(hv.info)

def _image_response(img):
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--port', type=int, default=8800)
    p.add_argument('--host', default='0.0.0.0')
    args = p.parse_args()
    print(f'🎨 HarmonicVisuals API → http://{args.host}:{args.port}')
    app.run(host=args.host, port=args.port, debug=False, threaded=True)
