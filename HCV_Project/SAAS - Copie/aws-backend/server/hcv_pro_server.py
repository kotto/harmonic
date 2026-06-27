#!/usr/bin/env python3
"""
HCV PRO Server — Serveur principal du projet HCV PRO
Intègre tous les codecs: Broadcast, Android Boost, Video Boost

Lancement:
  cd HCV-PRO-PROJECT
  python server/hcv_pro_server.py

Endpoints:
  GET  /                    → Site web HCV PRO
  POST /api/compress        → Compression broadcast (signal RAW/SDI)
  POST /api/demo            → Démo broadcast synthétique
  POST /api/android-boost   → Compression Android Boost (JPEG)
  POST /api/video-boost     → Compression vidéo (H264 via ffmpeg)
  POST /api/precompressed   → Compression fichiers précompressés (JPEG/PNG/WebP/GIF)
  GET  /api/history         → Historique des compressions
  GET  /api/health          → Statut du serveur
"""

import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

import sys
import base64
import mimetypes
import traceback
import tempfile
import uuid
from pathlib import Path
from datetime import datetime

import numpy as np
import cv2

from flask import Flask, request, jsonify, send_file, make_response

# Ajouter le dossier codecs au path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'codecs'))

from hcv_pro_codec import HCVProCodec, make_broadcast_frame
from hcv_android_boost_codec import HCVAndroidBoostCodec, make_android_photo, make_jpeg_from_array

app = Flask(__name__, static_folder=str(PROJECT_ROOT / 'web'))
history = []
media_registry = {}
jobs = {}


def run_job_async(job_id, func, *args, **kwargs):
    """Exécute une fonction en arrière-plan et met à jour le statut du job"""
    try:
        jobs[job_id]['status'] = 'running'
        jobs[job_id]['progress'] = 0
        result = func(*args, **kwargs)
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['result'] = result
        jobs[job_id]['progress'] = 100
    except Exception as e:
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['error'] = str(e)
        traceback.print_exc()


def _to_json_serializable(obj):
    """Convertit les types NumPy et autres non-sérialisables en types Python natifs"""
    if isinstance(obj, dict):
        return {k: _to_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_json_serializable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    if isinstance(obj, (np.bool_)):
        return bool(obj)
    return obj


@app.before_request
def handle_preflight():
    """Gère les requêtes OPTIONS (CORS preflight)"""
    if request.method == 'OPTIONS':
        resp = make_response()
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, DELETE'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        resp.headers['Access-Control-Max-Age'] = '3600'
        return resp, 200


@app.errorhandler(404)
def handle_404(e):
    return jsonify({'detail': 'Endpoint non trouvé', 'status': 404}), 404


@app.errorhandler(500)
def handle_500(e):
    return jsonify({'detail': 'Erreur serveur interne', 'status': 500, 'error': str(e)}), 500


@app.after_request
def add_security_headers(response):

    """Ajoute des headers de sécurité pour protéger l'application."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    # ✅ SUPRIME TOTALEMENT LE CSP QU'AJOUTE APP RUNNER
    response.headers.pop('Content-Security-Policy', None)
    response.headers['Content-Security-Policy'] = "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:;"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response


def _guess_mime(path):
    mime_type, _ = mimetypes.guess_type(str(path))
    return mime_type or 'application/octet-stream'


def _register_media(path, mime_type=None):
    media_id = uuid.uuid4().hex
    media_registry[media_id] = {
        'path': str(path),
        'mime_type': mime_type or _guess_mime(path),
    }
    return f'/api/media/{media_id}'


@app.route('/')
def index():
    return send_file(str(PROJECT_ROOT / 'web' / 'templates' / 'hcv_pro.html'))


@app.route('/api/media/<media_id>')
def api_media(media_id):
    media = media_registry.get(media_id)
    if not media:
        return jsonify({'detail': 'Media introuvable'}), 404
    media_path = media['path']
    if not os.path.exists(media_path):
        media_registry.pop(media_id, None)
        return jsonify({'detail': 'Fichier média expiré'}), 404
    
    mime_type = media['mime_type']
    file_size = os.path.getsize(media_path)
    
    # Support Range Requests for video streaming (required for audio playback)
    range_header = request.headers.get('Range')
    if range_header:
        # Parse Range: bytes=start-end
        import re
        m = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if m:
            start = int(m.group(1))
            end = int(m.group(2)) if m.group(2) else file_size - 1
            end = min(end, file_size - 1)
            length = end - start + 1
            
            with open(media_path, 'rb') as f:
                f.seek(start)
                data = f.read(length)
            
            from flask import Response
            resp = Response(data, 206, mimetype=mime_type)
            resp.headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            resp.headers['Accept-Ranges'] = 'bytes'
            resp.headers['Content-Length'] = length
            return resp
    
    # Full file response with Accept-Ranges header
    from flask import Response
    with open(media_path, 'rb') as f:
        data = f.read()
    resp = Response(data, 200, mimetype=mime_type)
    resp.headers['Accept-Ranges'] = 'bytes'
    resp.headers['Content-Length'] = file_size
    return resp


@app.route('/api/compress', methods=['POST'])
def api_compress():
    try:
        if 'file' not in request.files:
            return jsonify({'detail': 'Aucun fichier fourni'}), 400
        file = request.files['file']
        bit_depth = int(request.form.get('bit_depth', 12))
        maxval = (1 << bit_depth) - 1

        file_bytes = file.read()
        source_size = len(file_bytes)
        nparr = np.frombuffer(file_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            return jsonify({'detail': 'Image non décodable'}), 400

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        H, W = img_rgb.shape[:2]
        frame = (img_rgb.astype(np.uint16) * maxval // 255).astype(np.uint16)

        codec = HCVProCodec(mode='GRAIN_SYNTH', bit_depth=bit_depth)
        stats = codec.benchmark(frame, frame_idx=0)
        compressed_data, _ = codec.encode_frame(frame, frame_idx=0)
        decoded = codec.decode_frame(compressed_data, frame_idx=0)
        
        # Write .hcab file for download
        temp_dir = Path(tempfile.gettempdir()) / 'hcv_pro_hcab'
        temp_dir.mkdir(exist_ok=True)
        hcab_path = str(temp_dir / f'{Path(file.filename).stem}_{uuid.uuid4().hex}.hcab')
        with open(hcab_path, 'wb') as f:
            f.write(compressed_data)
        stats['hcab_path'] = hcab_path

        img_before_8 = (frame.astype(np.float32) / maxval * 255).astype(np.uint8)
        img_after_8 = (decoded.astype(np.float32) / maxval * 255).astype(np.uint8)
        
        # Redimensionner pour réduire la taille (max 1024px pour éviter OOM sur les calculs PSNR/SSIM)
        max_dim = 1024
        h, w = img_before_8.shape[:2]
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            img_before_8 = cv2.resize(img_before_8, (new_w, new_h), interpolation=cv2.INTER_AREA)
            img_after_8 = cv2.resize(img_after_8, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # Limiter aussi la taille pour l'affichage (max 640px)
        display_max_dim = 640
        dh, dw = img_before_8.shape[:2]
        if max(dh, dw) > display_max_dim:
            dscale = display_max_dim / max(dh, dw)
            new_dw, new_dh = int(dw * dscale), int(dh * dscale)
            img_before_display = cv2.resize(img_before_8, (new_dw, new_dh), interpolation=cv2.INTER_AREA)
            img_after_display = cv2.resize(img_after_8, (new_dw, new_dh), interpolation=cv2.INTER_AREA)
        else:
            img_before_display = img_before_8
            img_after_display = img_after_8
        
        # Encoder en JPEG avec qualité moyenne pour réduire la taille
        _, buf_b = cv2.imencode('.jpg', cv2.cvtColor(img_before_display, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])
        _, buf_a = cv2.imencode('.jpg', cv2.cvtColor(img_after_display, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])

        psnr_val = stats['psnr_vs_original']
        result = {
            'filename': file.filename,
            'source_format': file.filename.rsplit('.', 1)[-1].upper() if '.' in file.filename else 'RAW',
            'source_size': source_size, 'raw_size': frame.nbytes,
            'compressed_size': stats['compressed_size'],
            'ratio_vs_source': round(source_size / stats['compressed_size'], 2) if stats['compressed_size'] > 0 else 0,
            'ratio_vs_raw': round(stats['ratio'], 2),
            'savings_vs_raw': round(stats['savings_pct'], 1),
            'psnr': 'Infinity' if psnr_val == float('inf') else round(psnr_val, 2),
            'ssim': round(stats['ssim_vs_original'], 6),
            'max_pixel_diff': stats['max_pixel_diff'],
            'encode_ms': round(stats['time_ms'], 1),
            'bitexact_reproducible': stats['bitexact_reproducible'],
            'mode': 'GRAIN_SYNTH', 'bit_depth': bit_depth,
            'resolution': f'{W}x{H}',
            'media_type': 'image',
            'img_before': base64.b64encode(buf_b).decode(),
            'img_after': base64.b64encode(buf_a).decode(),
            'img_format': 'jpeg',
            'hcab_url': _register_media(stats['hcab_path'], 'application/octet-stream'),
        }
        history.append({'filename': file.filename, 'resolution': f'{W}x{H}',
                        'mode': 'GRAIN_SYNTH', 'ratio_vs_raw': result['ratio_vs_raw'],
                        'savings_vs_raw': result['savings_vs_raw'],
                        'timestamp': datetime.now().isoformat()})
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'detail': str(e)}), 500


@app.route('/api/demo', methods=['POST'])
def api_demo():
    try:
        resolution = request.form.get('resolution', 'VGA')
        bit_depth = int(request.form.get('bit_depth', 12))
        maxval = (1 << bit_depth) - 1
        res_map = {'QVGA': (240, 320), 'VGA': (480, 640), 'SVGA': (600, 800)}
        H, W = res_map.get(resolution, (480, 640))

        frame = make_broadcast_frame(H, W, bit_depth)
        codec = HCVProCodec(mode='GRAIN_SYNTH', bit_depth=bit_depth)
        stats = codec.benchmark(frame, frame_idx=0)
        compressed_data, _ = codec.encode_frame(frame, frame_idx=0)
        decoded = codec.decode_frame(compressed_data, frame_idx=0)
        
        # Write .hcab file for download
        temp_dir = Path(tempfile.gettempdir()) / 'hcv_pro_hcab'
        temp_dir.mkdir(exist_ok=True)
        hcab_path = str(temp_dir / f'demo_{resolution}_{uuid.uuid4().hex}.hcab')
        with open(hcab_path, 'wb') as f:
            f.write(compressed_data)
        stats['hcab_path'] = hcab_path

        img_b8 = (frame.astype(np.float32) / maxval * 255).astype(np.uint8)
        img_a8 = (decoded.astype(np.float32) / maxval * 255).astype(np.uint8)
        # Redimensionner pour réduire la taille (max 1024px pour calculs, 640px pour affichage)
        max_dim = 1024
        h, w = img_b8.shape[:2]
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            img_b8 = cv2.resize(img_b8, (new_w, new_h), interpolation=cv2.INTER_AREA)
            img_a8 = cv2.resize(img_a8, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # Limiter aussi pour l'affichage
        display_max_dim = 640
        dh, dw = img_b8.shape[:2]
        if max(dh, dw) > display_max_dim:
            dscale = display_max_dim / max(dh, dw)
            new_dw, new_dh = int(dw * dscale), int(dh * dscale)
            img_b_display = cv2.resize(img_b8, (new_dw, new_dh), interpolation=cv2.INTER_AREA)
            img_a_display = cv2.resize(img_a8, (new_dw, new_dh), interpolation=cv2.INTER_AREA)
        else:
            img_b_display = img_b8
            img_a_display = img_a8
        
        # Encoder en JPEG avec qualité moyenne
        _, buf_b = cv2.imencode('.jpg', cv2.cvtColor(img_b_display, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])
        _, buf_a = cv2.imencode('.jpg', cv2.cvtColor(img_a_display, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])

        psnr_val = stats['psnr_vs_original']
        source_size = frame.nbytes
        result = {
            'filename': f'demo_{resolution}.broadcast', 'source_format': 'SDI 4:2:2',
            'source_size': source_size, 'raw_size': source_size,
            'compressed_size': stats['compressed_size'],
            'ratio_vs_source': round(source_size / stats['compressed_size'], 2) if stats['compressed_size'] > 0 else 0,
            'ratio_vs_raw': round(stats['ratio'], 2),
            'savings_vs_raw': round(stats['savings_pct'], 1),
            'psnr': 'Infinity' if psnr_val == float('inf') else round(psnr_val, 2),
            'ssim': round(stats['ssim_vs_original'], 6),
            'max_pixel_diff': stats['max_pixel_diff'],
            'encode_ms': round(stats['time_ms'], 1),
            'bitexact_reproducible': stats['bitexact_reproducible'],
            'mode': 'GRAIN_SYNTH', 'bit_depth': bit_depth, 'resolution': f'{W}x{H}',
            'media_type': 'image',
            'img_before': base64.b64encode(buf_b).decode(),
            'img_after': base64.b64encode(buf_a).decode(),
            'img_format': 'jpeg',
        }
        history.append({'filename': f'demo_{resolution}', 'resolution': f'{W}x{H}',
                        'mode': 'GRAIN_SYNTH', 'ratio_vs_raw': result['ratio_vs_raw'],
                        'savings_vs_raw': result['savings_vs_raw'],
                        'timestamp': datetime.now().isoformat()})
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'detail': str(e)}), 500


@app.route('/api/android-boost', methods=['POST'])
def api_android_boost():
    try:
        quality = request.form.get('quality', 'high')
        target_resolution = request.form.get('target_resolution', 'original')  # 'original', '4K', '8K'
        
        if quality not in ('ultra', 'high', 'balanced', 'compact'):
            quality = 'high'
        codec = HCVAndroidBoostCodec(quality=quality)

        if 'file' in request.files:
            file_bytes = request.files['file'].read()
            filename = request.files['file'].filename
            stats = codec.benchmark(jpeg_bytes=file_bytes, label=filename)
        else:
            res = request.form.get('resolution', 'VGA')
            res_map = {'QVGA': (240, 320), 'VGA': (480, 640), 'HD': (720, 960), '1MP': (800, 1200)}
            h, w = res_map.get(res, (480, 640))
            img_bgr = make_android_photo(h, w, seed=42)
            jpeg_bytes = make_jpeg_from_array(img_bgr, 85)
            file_bytes = jpeg_bytes
            filename = f'demo_android_{res}.jpg'
            stats = codec.benchmark(jpeg_bytes=jpeg_bytes, label=filename)

        # Images avant/après avec upscaling optionnel
        nparr = np.frombuffer(file_bytes, np.uint8)
        original_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        container, _ = codec.encode(jpeg_bytes=file_bytes)
        decoded_bgr, decode_stats = codec.decode(container, target_resolution=target_resolution)
        
        # Redimensionner pour affichage si nécessaire
        if decoded_bgr.shape[:2] != original_bgr.shape[:2]:
            decoded_bgr_display = cv2.resize(decoded_bgr, (original_bgr.shape[1], original_bgr.shape[0]),
                                             interpolation=cv2.INTER_LANCZOS4)
        else:
            decoded_bgr_display = decoded_bgr
        
        max_dim = 640
        oh, ow = original_bgr.shape[:2]
        if max(oh, ow) > max_dim:
            sc = max_dim / max(oh, ow)
            nw, nh = int(ow * sc), int(oh * sc)
            db, da = cv2.resize(original_bgr, (nw, nh)), cv2.resize(decoded_bgr_display, (nw, nh))
        else:
            db, da = original_bgr, decoded_bgr_display
        _, bb = cv2.imencode('.jpg', db, [cv2.IMWRITE_JPEG_QUALITY, 85])
        _, ba = cv2.imencode('.jpg', da, [cv2.IMWRITE_JPEG_QUALITY, 85])

        result = {
            'filename': filename, 'source_format': 'JPEG (Android)',
            'source_size': stats['source_size'], 'raw_size': stats['raw_size'],
            'compressed_size': stats['compressed_size'],
            'ratio_vs_source': stats['ratio_vs_source'], 'ratio_vs_raw': stats['ratio_vs_raw'],
            'savings_vs_source': stats['savings_vs_source'], 'savings_vs_raw': stats['savings_vs_raw'],
            'original_resolution': stats['original_resolution'],
            'downscaled_resolution': stats['downscaled_resolution'],
            'target_resolution': decode_stats.get('target_resolution', stats['original_resolution']),
            'scale_factor': stats['scale_factor'], 'pixel_reduction': stats['pixel_reduction'],
            'psnr': stats['psnr'], 'ssim': stats['ssim'],
            'max_pixel_diff': stats['max_pixel_diff'],
            'encode_ms': stats['encode_ms'], 'decode_ms': decode_stats.get('decode_ms', stats['decode_ms']),
            'bitexact_reproducible': stats['bitexact_reproducible'],
            'quality': quality, 'mode': 'ANDROID_BOOST',
            'img_before': base64.b64encode(bb).decode(),
            'img_after': base64.b64encode(ba).decode(),
            'img_format': 'jpeg',
        }
        history.append({'filename': filename, 'resolution': stats['original_resolution'],
                        'mode': f'ANDROID_BOOST ({quality})',
                        'ratio_vs_raw': stats['ratio_vs_raw'],
                        'savings_vs_raw': stats['savings_vs_raw'],
                        'timestamp': datetime.now().isoformat()})
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'detail': str(e)}), 500


def _calculate_video_psnr(source_path, restored_path, num_frames=10):
    """Calculate PSNR between source and restored video by comparing frames."""
    try:
        import subprocess
        import json
        
        # Get video info
        ffprobe = 'ffprobe'
        try:
            import imageio_ffmpeg
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            ffprobe = ffmpeg_path.replace('ffmpeg', 'ffprobe')
        except:
            pass
        
        # Extract frames from both videos and calculate PSNR
        psnr_values = []
        
        # Use ffmpeg to calculate PSNR directly
        cmd = [
            'ffmpeg', '-i', source_path, '-i', restored_path,
            '-lavfi', f'[0:v][1:v]scale2ref=w=iw:h=ih[ref][main];[main][ref]psnr',
            '-f', 'null', '-'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            output = result.stderr
            
            # Parse PSNR values from output
            import re
            psnr_matches = re.findall(r'PSNR y:(\d+\.?\d*)', output)
            if psnr_matches:
                psnr_values = [float(p) for p in psnr_matches]
        except:
            pass
        
        if psnr_values:
            avg_psnr = sum(psnr_values) / len(psnr_values)
            return round(avg_psnr, 2)
        else:
            return 'N/A'
    except Exception as e:
        print(f"PSNR calculation error: {e}")
        return 'N/A'


@app.route('/api/start-video-boost', methods=['POST'])
def api_start_video_boost():
    try:
        from hcv_video_boost_codec import HCVVideoBoost
        import threading
        
        quality = request.form.get('quality', 'high')
        audio_bitrate = int(request.form.get('audio_bitrate', '96'))
        target_resolution = request.form.get('target_resolution', 'original')
        
        if 'file' not in request.files:
            return jsonify({'detail': 'Aucun fichier vidéo'}), 400
        
        file = request.files['file']
        source_suffix = Path(file.filename or 'video.mp4').suffix or '.mp4'
        
        temp_dir = Path(tempfile.gettempdir()) / 'hcv_pro_videos'
        temp_dir.mkdir(exist_ok=True)
        
        tmp_name = str(temp_dir / f'source_{uuid.uuid4().hex}{source_suffix}')
        file.save(tmp_name)
        
        job_id = uuid.uuid4().hex
        jobs[job_id] = {
            'status': 'queued',
            'progress': 0,
            'result': None,
            'error': None,
            'created_at': datetime.now().isoformat()
        }
        
        # Lancer la compression en arrière-plan
        thread = threading.Thread(
            target=run_job_async,
            args=(job_id, _process_video_boost, tmp_name, quality, audio_bitrate, target_resolution, file.filename)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({'job_id': job_id, 'status': 'queued'})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'detail': str(e)}), 500


def _process_video_boost(tmp_name, quality, audio_bitrate, target_resolution, filename):
    """Fonction exécutée en arrière-plan pour la compression vidéo"""
    from hcv_video_boost_codec import HCVVideoBoost
    codec = HCVVideoBoost(quality=quality, audio_bitrate=audio_bitrate)
    out_path = tmp_name + '.hcvb'
    restored_path = tmp_name + '_restored.mp4'
    
    _, stats = codec.encode(tmp_name, out_path)
    _, decode_stats = codec.decode(out_path, restored_path, target_resolution=target_resolution)
    
    psnr = _calculate_video_psnr(tmp_name, restored_path)
    
    source_mime = _guess_mime(tmp_name) or 'video/mp4'
    
    result = {
        **stats,
        **decode_stats,
        'filename': filename,
        'source_format': Path(filename).suffix.lstrip('.').upper() if '.' in filename else 'VIDEO',
        'mode': f'VIDEO_BOOST ({quality})',
        'media_type': 'video',
        'psnr': psnr,
        'bitexact_reproducible': False,
        'video_before_url': _register_media(tmp_name, source_mime),
        'video_after_url': _register_media(restored_path, 'video/mp4'),
        'video_after_mime': 'video/mp4',
    }
    
    if os.path.exists(out_path):
        result['hcvb_url'] = _register_media(out_path, 'application/octet-stream')
    
    history.append({
        'filename': filename,
        'resolution': stats['original_resolution'],
        'mode': f'VIDEO_BOOST ({quality})',
        'ratio_vs_raw': stats['ratio_vs_source'],
        'savings_vs_raw': stats['savings_vs_source'],
        'timestamp': datetime.now().isoformat()
    })
    
    return result


@app.route('/api/job-status/<job_id>', methods=['GET'])
def api_job_status(job_id):
    if job_id not in jobs:
        return jsonify({'detail': 'Job introuvable'}), 404
    return jsonify(_to_json_serializable(jobs[job_id]))


@app.route('/api/video-boost', methods=['POST'])
def api_video_boost():
    try:
        from hcv_video_boost_codec import HCVVideoBoost
        quality = request.form.get('quality', 'high')
        audio_bitrate = int(request.form.get('audio_bitrate', '96'))  # kbps, défaut 96
        target_resolution = request.form.get('target_resolution', 'original')  # 'original', '1080p', '4K', '8K'
        
        if 'file' not in request.files:
            return jsonify({'detail': 'Aucun fichier vidéo'}), 400
        file = request.files['file']
        source_suffix = Path(file.filename or 'video.mp4').suffix or '.mp4'
        
        # Create temp files in a persistent directory
        temp_dir = Path(tempfile.gettempdir()) / 'hcv_pro_videos'
        temp_dir.mkdir(exist_ok=True)
        
        tmp_name = str(temp_dir / f'source_{uuid.uuid4().hex}{source_suffix}')
        file.save(tmp_name)
        
        codec = HCVVideoBoost(quality=quality, audio_bitrate=audio_bitrate)
        out_path = tmp_name + '.hcvb'
        restored_path = tmp_name + '_restored.mp4'
        
        print(f'[SERVER] Starting encode: tmp_name={tmp_name}')
        print(f'[SERVER] out_path={out_path}')
        print(f'[SERVER] audio_bitrate={audio_bitrate}k')
        
        _, stats = codec.encode(tmp_name, out_path)
        
        print(f'[SERVER] After encode - file exists: {os.path.exists(out_path)}')
        if os.path.exists(out_path):
            print(f'[SERVER] .hcvb file size: {os.path.getsize(out_path)} bytes')
        
        _, decode_stats = codec.decode(out_path, restored_path, target_resolution=target_resolution)
        
        # Calculate PSNR between source and restored video
        psnr = _calculate_video_psnr(tmp_name, restored_path)
        
        # Determine correct MIME type for source
        source_mime = file.mimetype or _guess_mime(tmp_name)
        if not source_mime or source_mime == 'application/octet-stream':
            source_mime = 'video/mp4'
        
        result = {
            **stats,
            **decode_stats,
            'filename': file.filename,
            'source_format': source_suffix.replace('.', '').upper() or 'VIDEO',
            'mode': f'VIDEO_BOOST ({quality})',
            'media_type': 'video',
            'psnr': psnr,
            'bitexact_reproducible': False,  # Video compression is lossy
            'video_before_url': _register_media(tmp_name, source_mime),
            'video_after_url': _register_media(restored_path, 'video/mp4'),
            'video_after_mime': 'video/mp4',
        }
        
        # Register .hcvb file if it exists
        if os.path.exists(out_path):
            result['hcvb_url'] = _register_media(out_path, 'application/octet-stream')
            print(f'[SERVER] ✓ Registered .hcvb: {out_path}')
        else:
            print(f'[SERVER] ✗ WARNING: .hcvb file not found: {out_path}')
            print(f'[SERVER] Directory contents: {os.listdir(os.path.dirname(out_path))}')
        
        # Don't delete out_path yet - keep it for download
        history.append({'filename': file.filename, 'resolution': stats['original_resolution'],
                        'mode': f'VIDEO_BOOST ({quality})',
                        'ratio_vs_raw': stats['ratio_vs_source'],
                        'savings_vs_raw': stats['savings_vs_source'],
                        'timestamp': datetime.now().isoformat()})
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'detail': str(e)}), 500


@app.route('/api/precompressed', methods=['POST'])
def api_precompressed():
    try:
        from hcv_universal_boost_codec import HCVUniversalBoost
        
        strategy = request.form.get('strategy', 'AUTO')
        target_resolution = request.form.get('target_resolution', 'original')  # 'original', '4K', '8K'
        
        if strategy not in ('AUTO', 'DIRECT', 'HYBRID', 'TRANSCODE'):
            strategy = 'AUTO'
        
        # Support démo sans fichier uploadé
        demo_format = request.form.get('demo_format')
        if demo_format and 'file' not in request.files:
            # Générer une image de démo
            h, w = 480, 640
            rng = np.random.RandomState(42)
            img_bgr = rng.randint(30, 225, (h, w, 3), dtype=np.uint8)
            # Ajouter un dégradé pour rendre l'image plus réaliste
            for y in range(h):
                img_bgr[y, :, 0] = np.clip(img_bgr[y, :, 0].astype(int) + y * 50 // h, 0, 255)
                img_bgr[y, :, 2] = np.clip(img_bgr[y, :, 2].astype(int) + (h - y) * 50 // h, 0, 255)
            if demo_format.upper() == 'PNG':
                _, file_bytes = cv2.imencode('.png', img_bgr)
                file_bytes = file_bytes.tobytes()
                filename = 'demo_precompressed.png'
            else:
                _, file_bytes = cv2.imencode('.jpg', img_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
                file_bytes = file_bytes.tobytes()
                filename = 'demo_precompressed.jpg'
        elif 'file' in request.files:
            file = request.files['file']
            file_bytes = file.read()
            filename = file.filename
        else:
            return jsonify({'detail': 'Aucun fichier fourni'}), 400
        
        # Map strategy to quality for the codec
        quality_map = {'AUTO': 'high', 'DIRECT': 'ultra', 'HYBRID': 'balanced', 'TRANSCODE': 'compact'}
        quality = quality_map.get(strategy, 'high')
        
        codec = HCVUniversalBoost(quality=quality)
        stats = codec.benchmark_image(file_bytes=file_bytes, label=filename)
        
        # Images avant/après avec upscaling optionnel
        nparr = np.frombuffer(file_bytes, np.uint8)
        original_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if original_bgr is None:
            return jsonify({'detail': 'Image non décodable'}), 400
        
        container, _ = codec.encode_image(file_bytes=file_bytes)
        decoded_bgr, decode_stats = codec.decode_image(container, target_resolution=target_resolution)
        
        # Redimensionner pour affichage si nécessaire
        if decoded_bgr.shape[:2] != original_bgr.shape[:2]:
            decoded_bgr_display = cv2.resize(decoded_bgr, (original_bgr.shape[1], original_bgr.shape[0]),
                                             interpolation=cv2.INTER_LANCZOS4)
        else:
            decoded_bgr_display = decoded_bgr
        
        # Redimensionner pour l'affichage si nécessaire
        max_dim = 640
        oh, ow = original_bgr.shape[:2]
        if max(oh, ow) > max_dim:
            sc = max_dim / max(oh, ow)
            nw, nh = int(ow * sc), int(oh * sc)
            db, da = cv2.resize(original_bgr, (nw, nh)), cv2.resize(decoded_bgr_display, (nw, nh))
        else:
            db, da = original_bgr, decoded_bgr_display
        
        _, bb = cv2.imencode('.jpg', db, [cv2.IMWRITE_JPEG_QUALITY, 85])
        _, ba = cv2.imencode('.jpg', da, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        result = {
            'filename': filename,
            'source_format': filename.rsplit('.', 1)[-1].upper() if '.' in filename else 'UNKNOWN',
            'source_size': stats['source_size'],
            'raw_size': stats.get('raw_size', stats['source_size']),
            'compressed_size': stats['compressed_size'],
            'ratio_vs_source': stats.get('ratio_vs_source', round(stats['source_size'] / stats['compressed_size'], 2)),
            'ratio_vs_raw': stats.get('ratio_vs_raw', round(stats.get('raw_size', stats['source_size']) / stats['compressed_size'], 2)),
            'savings_vs_source': stats.get('savings_vs_source', round((1 - stats['compressed_size'] / stats['source_size']) * 100, 1)),
            'savings_vs_raw': stats.get('savings_vs_raw', round((1 - stats['compressed_size'] / stats.get('raw_size', stats['source_size'])) * 100, 1)),
            'original_resolution': stats.get('original_resolution', f'{original_bgr.shape[1]}x{original_bgr.shape[0]}'),
            'downscaled_resolution': stats.get('downscaled_resolution', stats.get('original_resolution', f'{original_bgr.shape[1]}x{original_bgr.shape[0]}')),
            'target_resolution': decode_stats.get('target_resolution', stats.get('original_resolution', f'{original_bgr.shape[1]}x{original_bgr.shape[0]}')),
            'psnr': stats.get('psnr', 'N/A'),
            'ssim': stats.get('ssim', 'N/A'),
            'max_pixel_diff': stats.get('max_pixel_diff', 0),
            'encode_ms': stats.get('encode_ms', 0),
            'decode_ms': decode_stats.get('decode_ms', stats.get('decode_ms', 0)),
            'bitexact_reproducible': stats.get('bitexact_reproducible', True),
            'strategy': strategy,
            'recommended_strategy': stats.get('recommended_strategy', 'AUTO'),
            'mode': 'PRECOMPRESSED',
            'img_before': base64.b64encode(bb).decode(),
            'img_after': base64.b64encode(ba).decode(),
            'img_format': 'jpeg',
        }
        
        history.append({'filename': filename, 'resolution': f'{original_bgr.shape[1]}x{original_bgr.shape[0]}',
                        'mode': f'PRECOMPRESSED ({strategy})',
                        'ratio_vs_raw': result['ratio_vs_raw'],
                        'savings_vs_raw': result['savings_vs_raw'],
                        'timestamp': datetime.now().isoformat()})
        
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'detail': str(e)}), 500


@app.route('/api/decode-hcvb', methods=['POST'])
def api_decode_hcvb():
    """Decode a .hcvb file to MP4 with audio and return video URL."""
    try:
        from hcv_video_boost_codec import HCVVideoBoost
        if 'file' not in request.files:
            return jsonify({'detail': 'Aucun fichier .hcvb fourni'}), 400
        file = request.files['file']

        temp_dir = Path(tempfile.gettempdir()) / 'hcv_pro_videos'
        temp_dir.mkdir(exist_ok=True)

        hcvb_path = str(temp_dir / f'decode_{uuid.uuid4().hex}.hcvb')
        file.save(hcvb_path)

        restored_path = hcvb_path.replace('.hcvb', '_restored.mp4')
        hcvb_size = os.path.getsize(hcvb_path)

        codec = HCVVideoBoost()
        _, decode_stats = codec.decode(hcvb_path, restored_path)

        restored_size = os.path.getsize(restored_path) if os.path.exists(restored_path) else 0

        os.unlink(hcvb_path)

        result = {
            'filename': file.filename,
            'hcvb_size': hcvb_size,
            'restored_size': restored_size,
            'original_resolution': decode_stats.get('original_resolution', ''),
            'quality': decode_stats.get('quality', ''),
            'decode_time': decode_stats.get('decode_time', 0),
            'has_audio': decode_stats.get('has_audio', False),
            'audio_present': decode_stats.get('audio_present', False),
            'audio_method': decode_stats.get('audio_method', 'none'),
            'audio_codec': decode_stats.get('audio_codec'),
            'audio_bitrate': decode_stats.get('audio_bitrate'),
            'audio_channels': decode_stats.get('audio_channels'),
            'video_url': _register_media(restored_path, 'video/mp4'),
        }
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'detail': str(e)}), 500


@app.route('/api/download-hcvb/<media_id>')
def api_download_hcvb(media_id):
    """Download a .hcvb file with proper Content-Disposition header."""
    media = media_registry.get(media_id)
    if not media:
        return jsonify({'detail': 'Media introuvable'}), 404
    media_path = media['path']
    if not os.path.exists(media_path):
        return jsonify({'detail': 'Fichier expiré'}), 404
    filename = Path(media_path).name
    return send_file(media_path, mimetype='application/octet-stream',
                     as_attachment=True, download_name=filename)


@app.route('/api/history')
def api_history():
    return jsonify({'history': history})


@app.route('/api/health')
def api_health():
    return jsonify({'ok': True, 'codec': 'HCV PRO v1.0',
                    'methods': ['broadcast', 'android-boost', 'video-boost', 'universal-boost']})


@app.route('/api/status')
def api_status():
    """Status diagnostique complet du serveur"""
    status = {
        'running': True,
        'timestamp': datetime.now().isoformat(),
        'available_endpoints': [
            '/api/compress',
            '/api/demo',
            '/api/android-boost',
            '/api/video-boost',
            '/api/precompressed',
            '/api/decode-hcvb',
            '/api/history',
            '/api/health'
        ],
        'imports': {
            'HCVProCodec': 'OK',
            'HCVAndroidBoostCodec': 'OK'
        }
    }
    try:
        from hcv_video_boost_codec import HCVVideoBoost
        status['imports']['HCVVideoBoost'] = 'OK'
    except Exception as e:
        status['imports']['HCVVideoBoost'] = f'ERROR: {str(e)}'
    
    try:
        from hcv_universal_boost_codec import HCVUniversalBoost
        status['imports']['HCVUniversalBoost'] = 'OK'
    except Exception as e:
        status['imports']['HCVUniversalBoost'] = f'ERROR: {str(e)}'
    
    return jsonify(status)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    print()
    print('=' * 60)
    print('  HCV PRO — Plateforme de Compression Multimédia')
    print('=' * 60)
    print(f'  Serveur: http://localhost:{port}')
    print(f'  POST /api/compress        Broadcast (RAW/SDI)')
    print(f'  POST /api/demo            Démo broadcast')
    print(f'  POST /api/android-boost   Android Boost (JPEG)')
    print(f'  POST /api/video-boost     Video Boost (H264)')
    print(f'  POST /api/precompressed   Précompressés (JPEG/PNG/WebP/GIF)')
    print(f'  GET  /api/history         Historique')
    print('=' * 60)
    print()
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
