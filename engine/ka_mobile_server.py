#!/usr/bin/env python3
"""
KA MOBILE Server — Version autonome sans IA
=============================================
Ne lance que les endpoints de compression HCV2.
Pas de dépendance vers harmonic_ai, harmonic_brain, etc.
Idéal pour le déploiement serveur minimal.
"""
import os, sys
from pathlib import Path

# Ajouter le chemin du projet
ROOT = str(Path(__file__).resolve().parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _find_app_dir() -> Path:
    """Localise ka-mobile-android/ (racine du repo ou sous-dossier engine/)."""
    for candidate in (Path(ROOT) / 'ka-mobile-android',
                      Path(ROOT).parent / 'ka-mobile-android'):
        if (candidate / 'www' / 'ka_index.html').exists():
            return candidate
    return Path(ROOT) / 'ka-mobile-android'

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import json, time, io, base64, struct

app = Flask(__name__)
CORS(app)

# ── Imports légers (HCV2 seulement) ──
from ka_mobile_compress import KaMobileCompressor
_kc = None
def get_kc():
    global _kc
    if _kc is None:
        _kc = KaMobileCompressor()
    return _kc

# Lancer le ghost compressor en arrière-plan
try:
    from ka_background_compress import start_ghost
    start_ghost()
    log.info("  ✓ GhostCompressor actif")
except Exception as e:
    log.warning(f"  GhostCompressor non disponible: {e}")

# ══════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

@app.route('/api/health')
def health():
    return jsonify({
        'service': 'ka-mobile',
        'status': 'healthy',
        'version': '4.0.0',
        'timestamp': time.time(),
    })

@app.route('/api/hcv2/mobile', methods=['POST', 'OPTIONS'])
def api_mobile_compress():
    """Compression image ou vidéo avec le mode Mobile."""
    if request.method == 'OPTIONS':
        return '', 200
    if 'multipart/form-data' not in (request.content_type or ''):
        return jsonify({'error': 'multipart/form-data requis'}), 400
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'Fichier requis'}), 400
    data = file.read()
    filename = file.filename or 'file'
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    video_exts = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'm4v', 'mpeg', 'mpg', 'wmv', 'flv'}
    try:
        kc = get_kc()
        if ext in video_exts:
            result = kc.compress_video(data, filename)
        else:
            result = kc.compress_image(data)
        resp = {k: v for k, v in result.items() if k != 'blob'}
        return jsonify(resp)
    except Exception as e:
        log.error(f"Compression error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/hcv2/mobile/download', methods=['POST', 'OPTIONS'])
def api_mobile_download():
    """Téléchargement du fichier compressé."""
    if request.method == 'OPTIONS':
        return '', 200
    if 'multipart/form-data' not in (request.content_type or ''):
        return jsonify({'error': 'multipart/form-data requis'}), 400
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'Fichier requis'}), 400
    data = file.read()
    filename = file.filename or 'file'
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    video_exts = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'm4v', 'mpeg', 'mpg', 'wmv', 'flv'}
    try:
        kc = get_kc()
        if ext in video_exts:
            result = kc.compress_video(data, filename)
        else:
            result = kc.compress_image(data)
        if 'error' in result:
            return jsonify(result), 400
        blob = result.get('blob', b'')
        if not blob:
            return jsonify({'error': 'Aucune donnée'}), 500
        dl_name = result.get('download_name', f'compressed.{ext}')
        return jsonify({'download_b64': base64.b64encode(blob).decode(), 'download_name': dl_name})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/hcv2/view/<path:filename>')
def api_hcv2_view(filename):
    """Décompression transparente à la volée."""
    from ka_background_compress import WATCHED_DIR, THUMBS_DIR
    safe_path = os.path.normpath(os.path.join(WATCHED_DIR, filename))
    if not safe_path.startswith(os.path.normpath(WATCHED_DIR)):
        return jsonify({'error': 'Chemin invalide'}), 403
    for compressed_ext in ('.hcvm', '.hcv2'):
        compressed_path = safe_path + compressed_ext
        if os.path.exists(compressed_path):
            try:
                with open(compressed_path, 'rb') as f:
                    blob = f.read()
                if compressed_ext == '.hcvm':
                    import hcv2_modal_codec as modal
                    import numpy as np
                    from PIL import Image
                    rec_img = modal.decode(blob)
                    rec_img = np.clip(rec_img, 0, 255).astype(np.uint8)
                    img = Image.fromarray(rec_img)
                    buf = io.BytesIO()
                    img.save(buf, format='JPEG', quality=92)
                    buf.seek(0)
                    return Response(buf.getvalue(), mimetype='image/jpeg')
                elif compressed_ext == '.hcv2':
                    thumb_path = os.path.join(THUMBS_DIR, os.path.basename(safe_path) + '.jpg')
                    if os.path.exists(thumb_path):
                        return send_file(thumb_path, mimetype='image/jpeg')
                    import struct as st
                    with open(compressed_path, 'rb') as f:
                        hdr = f.read(12)
                    T, H, W = st.unpack_from('III', hdr[:12])
                    from PIL import Image as PILImage
                    thumb = PILImage.new('RGB', (min(W, 320), min(H, 240)), (30, 30, 40))
                    buf = io.BytesIO()
                    thumb.save(buf, format='JPEG', quality=70)
                    buf.seek(0)
                    return Response(buf.getvalue(), mimetype='image/jpeg')
            except Exception as e:
                log.error(f"View error: {e}")
                if os.path.exists(safe_path):
                    return send_file(safe_path)
                return jsonify({'error': str(e)}), 500
    if os.path.exists(safe_path):
        return send_file(safe_path)
    return jsonify({'error': 'Fichier introuvable'}), 404

@app.route('/api/hcv2/stats')
def api_hcv2_stats():
    """Statistiques du pipeline de compression."""
    try:
        from ka_background_compress import get_ghost
        ghost = get_ghost()
        s = ghost.stats()
        return jsonify({
            'files_count': s.get('files_count', 0),
            'total_original_mb': round(s.get('total_original_bytes', 0) / (1024**2), 1),
            'total_compressed_mb': round(s.get('total_compressed_bytes', 0) / (1024**2), 1),
            'saved_mb': round((s.get('total_original_bytes', 0) - s.get('total_compressed_bytes', 0)) / (1024**2), 1),
            'avg_ratio': round(s.get('total_original_bytes', 0) / max(s.get('total_compressed_bytes', 0), 1), 1) if s.get('total_compressed_bytes', 0) > 0 else 0,
            'projection': s.get('projection', {}),
            'free_space_gb': s.get('free_space_gb', 0),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/hcv2/gallery')
def api_hcv2_gallery():
    """Liste les médias disponibles."""
    from ka_background_compress import WATCHED_DIR, THUMBS_DIR
    from pathlib import Path
    items = []
    seen = set()
    for ext in ('*.hcvm', '*.hcv2'):
        for f in sorted(Path(WATCHED_DIR).rglob(ext), key=lambda p: p.stat().st_mtime, reverse=True):
            if not f.is_file():
                continue
            rel = os.path.relpath(str(f), WATCHED_DIR)
            stat = f.stat()
            base_name = f.stem
            is_video = f.suffix == '.hcv2'
            thumb_path = f'hcv2/view/thumb/{base_name}.jpg'
            original_rel = rel.rsplit('.', 1)[0]
            items.append({
                'name': base_name, 'path': original_rel,
                'size': stat.st_size, 'is_video': is_video,
                'compressed': True, 'thumbnail': thumb_path,
                'modified': stat.st_mtime,
            })
            seen.add(base_name)
    image_exts = ('*.jpg', '*.jpeg', '*.png', '*.heic', '*.webp', '*.gif')
    video_exts = ('*.mp4', '*.avi', '*.mov', '*.mkv')
    for ext in image_exts + video_exts:
        for f in sorted(Path(WATCHED_DIR).rglob(ext), key=lambda p: p.stat().st_mtime, reverse=True):
            if not f.is_file() or f.stem in seen:
                continue
            rel = os.path.relpath(str(f), WATCHED_DIR)
            stat = f.stat()
            is_video = f.suffix.lower() in ('.mp4', '.avi', '.mov', '.mkv')
            thumb_path = f'hcv2/view/thumb/{f.name}.jpg'
            items.append({
                'name': f.name, 'path': rel.replace('\\', '/'),
                'size': stat.st_size, 'is_video': is_video,
                'compressed': False, 'thumbnail': thumb_path,
                'modified': stat.st_mtime,
            })
    return jsonify({'items': items, 'count': len(items), 'watch_dir': os.path.basename(WATCHED_DIR)})

@app.route('/api/hcv2/compress_now', methods=['POST'])
def api_hcv2_compress_now():
    """Force une passe de compression immédiate."""
    try:
        from ka_background_compress import get_ghost
        ghost = get_ghost()
        n = ghost.compress_now()
        s = ghost.stats()
        return jsonify({'processed': n, 'files_count': s.get('files_count', 0)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/storage/optimize-batch', methods=['POST', 'OPTIONS'])
def api_storage_optimize_batch():
    """Analyse un lot de fichiers et estime le gain de compression."""
    if request.method == 'OPTIONS':
        return '', 200
    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': 'Aucun fichier'}), 400
    try:
        kc = get_kc()
        video_exts = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'm4v', 'mpeg', 'mpg', 'wmv', 'flv'}
        total_original = 0
        total_after = 0
        results = []
        for f in files:
            data = f.read()
            filename = f.filename or 'file'
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            total_original += len(data)
            try:
                if ext in video_exts:
                    r = kc.compress_video(data, filename)
                else:
                    r = kc.compress_image(data)
                compressed = r.get('compressed_size', len(r.get('blob', b'')))
                estimated_after = compressed if compressed > 0 else len(data)
            except Exception:
                estimated_after = len(data)
            total_after += estimated_after
            results.append({
                'filename': filename,
                'original_size': len(data),
                'estimated_after': estimated_after,
                'estimated_saved': len(data) - estimated_after,
                'estimated_ratio': round(len(data) / max(estimated_after, 1), 1),
                'media_type': 'video' if ext in video_exts else 'image',
            })
        return jsonify({
            'n_files': len(results),
            'total_original': total_original,
            'total_saved': total_original - total_after,
            'total_estimated_after': total_after,
            'files': results,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/tts', methods=['POST', 'OPTIONS'])
def api_tts():
    """Synthèse vocale via Piper."""
    if request.method == 'OPTIONS':
        return '', 200
    data = request.get_json() or {}
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'Texte requis'}), 400
    if len(text) > 5000:
        return jsonify({'error': 'Texte trop long'}), 413
    voice = data.get('voice', 'fr_FR')
    try:
        import subprocess, tempfile
        # Chercher le modèle Piper
        model_dir = os.path.join(ROOT, 'models', 'voice', 'piper')
        model_path = os.path.join(model_dir, f'{voice}.onnx')
        if not os.path.exists(model_path):
            # Essayer le mapping
            PIPER_VOICES = {
                'fr_FR': 'fr_FR-siwis-medium',
                'en_US': 'en_US-lessac-medium',
            }
            voice_id = PIPER_VOICES.get(voice, voice)
            model_path = os.path.join(model_dir, f'{voice_id}.onnx')
        if not os.path.exists(model_path):
            return jsonify({'error': f'Modèle vocal non trouvé'}), 503
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        tmp.close()
        subprocess.run(['piper', '--model', model_path, '--output-raw'],
                       input=text.encode('utf-8'),
                       stdout=subprocess.PIPE, timeout=30)
        # Fallback : essayer via python piper
        try:
            import piper
            # Utiliser piper-tts
            pass
        except ImportError:
            pass
        return jsonify({'error': 'Piper pas disponible sur cette instance'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    """Page d'accueil — sert l'application KA MOBILE."""
    frontend_path = _find_app_dir() / 'www' / 'ka_index.html'
    if frontend_path.exists():
        return send_file(str(frontend_path))
    return jsonify({
        'service': 'KA MOBILE',
        'version': '4.0.0',
        'endpoints': {
            'health': '/api/health',
            'compress': '/api/hcv2/mobile',
            'stats': '/api/hcv2/stats',
            'gallery': '/api/hcv2/gallery',
            'tts': '/api/voice/tts',
        }
    })

@app.route('/<path:filename>')
def static_files(filename):
    """Sert les fichiers statiques (JS, CSS, etc.)"""
    app_dir = _find_app_dir()
    frontend_path = app_dir / 'www' / filename
    if frontend_path.exists() and frontend_path.is_file():
        return send_file(str(frontend_path))
    # Rediriger vers l'index pour les routes SPA
    frontend_index = app_dir / 'www' / 'ka_index.html'
    if frontend_index.exists():
        return send_file(str(frontend_index))
    return jsonify({'error': 'Not found'}), 404

# ══════════════════════════════════════════════════════════════════════
# DÉMARRAGE
# ══════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8765))
    print(f"🚀 KA MOBILE Server — http://0.0.0.0:{port}")
    print(f"   Compression HCV2 | Ghost mode | Sans IA")
    app.run(host='0.0.0.0', port=port, debug=False)