#!/usr/bin/env python3
"""
HCV PRO Server — Backend Flask pour le site HCV PRO Broadcast Lossless
Intègre le codec hcv_pro_codec.py avec compression réelle
"""

import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

import sys
import json
import io
import base64
import tempfile
import traceback
import time
import math
from pathlib import Path
from datetime import datetime

import numpy as np
import cv2
import zstandard as zstd

from flask import Flask, request, jsonify, send_file

# Import du codec HCV PRO
sys.path.insert(0, str(Path(__file__).parent / 'COMPRESSION-SOLUTIONS'))
from hcv_pro_codec import HCVProCodec, make_broadcast_frame, psnr, ssim_simple, _separate
from hcv_android_boost_codec import HCVAndroidBoostCodec, make_android_photo, make_jpeg_from_array

app = Flask(__name__, static_folder='COMPRESSION-SOLUTIONS', static_url_path='/static')

UPLOAD_FOLDER = tempfile.gettempdir()
history = []

# ─── Routes statiques ──────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_file('COMPRESSION-SOLUTIONS/templates/hcv_pro.html')

# ─── API Compression ───────────────────────────────────────────────────────

@app.route('/api/compress', methods=['POST'])
def api_compress():
    """Compression réelle d'une image uploadée via le codec HCV PRO."""
    try:
        if 'file' not in request.files:
            return jsonify({'detail': 'Aucun fichier fourni'}), 400

        file = request.files['file']
        bit_depth = int(request.form.get('bit_depth', 12))
        maxval = (1 << bit_depth) - 1

        # Lire l'image
        file_bytes = file.read()
        source_size = len(file_bytes)
        nparr = np.frombuffer(file_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img_bgr is None:
            return jsonify({'detail': 'Impossible de décoder l\'image'}), 400

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        H, W = img_rgb.shape[:2]

        # Convertir en bit_depth
        frame = (img_rgb.astype(np.uint16) * maxval // 255).astype(np.uint16)
        raw_size = frame.nbytes

        # Compresser avec HCV PRO
        codec = HCVProCodec(mode='GRAIN_SYNTH', bit_depth=bit_depth)
        stats = codec.benchmark(frame, frame_idx=0)

        # Décoder pour l'image après
        compressed_data, _ = codec.encode_frame(frame, frame_idx=0)
        decoded = codec.decode_frame(compressed_data, frame_idx=0)

        # Convertir en images base64 pour affichage
        img_before_8 = (frame.astype(np.float32) / maxval * 255).astype(np.uint8)
        img_after_8 = (decoded.astype(np.float32) / maxval * 255).astype(np.uint8)

        _, buf_before = cv2.imencode('.png', cv2.cvtColor(img_before_8, cv2.COLOR_RGB2BGR))
        _, buf_after = cv2.imencode('.png', cv2.cvtColor(img_after_8, cv2.COLOR_RGB2BGR))

        b64_before = base64.b64encode(buf_before).decode()
        b64_after = base64.b64encode(buf_after).decode()

        psnr_val = stats['psnr_vs_original']
        ssim_val = stats['ssim_vs_original']

        result = {
            'filename': file.filename,
            'source_format': file.filename.rsplit('.', 1)[-1].upper() if '.' in file.filename else 'RAW',
            'source_size': source_size,
            'raw_size': raw_size,
            'compressed_size': stats['compressed_size'],
            'ratio_vs_source': round(source_size / stats['compressed_size'], 2) if stats['compressed_size'] > 0 else 0,
            'ratio_vs_raw': round(stats['ratio'], 2),
            'savings_vs_raw': round(stats['savings_pct'], 1),
            'psnr': 'Infinity' if psnr_val == float('inf') else round(psnr_val, 2),
            'ssim': round(ssim_val, 6),
            'max_pixel_diff': stats['max_pixel_diff'],
            'encode_ms': round(stats['time_ms'], 1),
            'bitexact_reproducible': stats['bitexact_reproducible'],
            'mode': 'GRAIN_SYNTH',
            'bit_depth': bit_depth,
            'resolution': f'{W}x{H}',
            'img_before': b64_before,
            'img_after': b64_after,
        }

        history.append({
            'filename': file.filename,
            'resolution': f'{W}x{H}',
            'mode': 'GRAIN_SYNTH',
            'ratio_vs_raw': result['ratio_vs_raw'],
            'savings_vs_raw': result['savings_vs_raw'],
            'timestamp': datetime.now().isoformat(),
        })

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'detail': str(e)}), 500


@app.route('/api/demo', methods=['POST'])
def api_demo():
    """Démo avec frame broadcast synthétique."""
    try:
        resolution = request.form.get('resolution', 'VGA')
        bit_depth = int(request.form.get('bit_depth', 12))
        maxval = (1 << bit_depth) - 1

        res_map = {
            'QVGA': (240, 320),
            'VGA': (480, 640),
            'SVGA': (600, 800),
            'HD': (720, 1280),
        }
        H, W = res_map.get(resolution, (480, 640))

        # Générer frame broadcast
        frame = make_broadcast_frame(H, W, bit_depth)
        raw_size = frame.nbytes

        # Compresser
        codec = HCVProCodec(mode='GRAIN_SYNTH', bit_depth=bit_depth)
        stats = codec.benchmark(frame, frame_idx=0)

        # Décoder pour affichage
        compressed_data, _ = codec.encode_frame(frame, frame_idx=0)
        decoded = codec.decode_frame(compressed_data, frame_idx=0)

        # Images base64
        img_before_8 = (frame.astype(np.float32) / maxval * 255).astype(np.uint8)
        img_after_8 = (decoded.astype(np.float32) / maxval * 255).astype(np.uint8)

        _, buf_before = cv2.imencode('.png', cv2.cvtColor(img_before_8, cv2.COLOR_RGB2BGR))
        _, buf_after = cv2.imencode('.png', cv2.cvtColor(img_after_8, cv2.COLOR_RGB2BGR))

        b64_before = base64.b64encode(buf_before).decode()
        b64_after = base64.b64encode(buf_after).decode()

        psnr_val = stats['psnr_vs_original']
        ssim_val = stats['ssim_vs_original']

        # Source size = raw size pour les démos
        source_size = raw_size

        result = {
            'filename': f'demo_{resolution}.broadcast',
            'source_format': 'SDI 4:2:2',
            'source_size': source_size,
            'raw_size': raw_size,
            'compressed_size': stats['compressed_size'],
            'ratio_vs_source': round(source_size / stats['compressed_size'], 2) if stats['compressed_size'] > 0 else 0,
            'ratio_vs_raw': round(stats['ratio'], 2),
            'savings_vs_raw': round(stats['savings_pct'], 1),
            'psnr': 'Infinity' if psnr_val == float('inf') else round(psnr_val, 2),
            'ssim': round(ssim_val, 6),
            'max_pixel_diff': stats['max_pixel_diff'],
            'encode_ms': round(stats['time_ms'], 1),
            'bitexact_reproducible': stats['bitexact_reproducible'],
            'mode': 'GRAIN_SYNTH',
            'bit_depth': bit_depth,
            'resolution': f'{W}x{H}',
            'img_before': b64_before,
            'img_after': b64_after,
        }

        history.append({
            'filename': f'demo_{resolution}',
            'resolution': f'{W}x{H}',
            'mode': 'GRAIN_SYNTH',
            'ratio_vs_raw': result['ratio_vs_raw'],
            'savings_vs_raw': result['savings_vs_raw'],
            'timestamp': datetime.now().isoformat(),
        })

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'detail': str(e)}), 500


@app.route('/api/history')
def api_history():
    return jsonify({'history': history})


# ─── API Android Boost ─────────────────────────────────────────────────────

@app.route('/api/android-boost', methods=['POST'])
def api_android_boost():
    """Compression Android Boost: JPEG → Downscale Lanczos → H264 Intra → zstd."""
    try:
        quality = request.form.get('quality', 'high')
        if quality not in ('ultra', 'high', 'balanced', 'compact'):
            quality = 'high'

        codec = HCVAndroidBoostCodec(quality=quality)

        if 'file' in request.files:
            file = request.files['file']
            file_bytes = file.read()
            filename = file.filename
            stats = codec.benchmark(jpeg_bytes=file_bytes, label=filename)
        else:
            # Demo mode: générer une photo Android simulée
            res = request.form.get('resolution', 'VGA')
            res_map = {
                'QVGA': (240, 320), 'VGA': (480, 640),
                'HD': (720, 960), '1MP': (800, 1200),
            }
            h, w = res_map.get(res, (480, 640))
            img_bgr = make_android_photo(h, w, seed=42)
            jpeg_bytes = make_jpeg_from_array(img_bgr, 85)
            filename = f'demo_android_{res}.jpg'
            stats = codec.benchmark(jpeg_bytes=jpeg_bytes, label=filename)

        # Générer images avant/après pour affichage
        # Recharger l'original
        if 'file' in request.files:
            nparr = np.frombuffer(file_bytes, np.uint8)
        else:
            nparr = np.frombuffer(jpeg_bytes, np.uint8)
        original_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Encoder + décoder pour l'image après
        if 'file' in request.files:
            container, _ = codec.encode(jpeg_bytes=file_bytes)
        else:
            container, _ = codec.encode(jpeg_bytes=jpeg_bytes)
        decoded_bgr, _ = codec.decode(container)

        # Redimensionner decoded si nécessaire
        if decoded_bgr.shape[:2] != original_bgr.shape[:2]:
            decoded_bgr = cv2.resize(decoded_bgr,
                (original_bgr.shape[1], original_bgr.shape[0]),
                interpolation=cv2.INTER_LANCZOS4)

        # Limiter la taille des images base64 (max 640px côté long)
        max_dim = 640
        oh, ow = original_bgr.shape[:2]
        if max(oh, ow) > max_dim:
            scale = max_dim / max(oh, ow)
            new_w, new_h = int(ow * scale), int(oh * scale)
            disp_before = cv2.resize(original_bgr, (new_w, new_h))
            disp_after = cv2.resize(decoded_bgr, (new_w, new_h))
        else:
            disp_before = original_bgr
            disp_after = decoded_bgr

        _, buf_before = cv2.imencode('.png', disp_before)
        _, buf_after = cv2.imencode('.png', disp_after)
        b64_before = base64.b64encode(buf_before).decode()
        b64_after = base64.b64encode(buf_after).decode()

        result = {
            'filename': filename,
            'source_format': 'JPEG (Android)',
            'source_size': stats['source_size'],
            'raw_size': stats['raw_size'],
            'compressed_size': stats['compressed_size'],
            'ratio_vs_source': stats['ratio_vs_source'],
            'ratio_vs_raw': stats['ratio_vs_raw'],
            'savings_vs_source': stats['savings_vs_source'],
            'savings_vs_raw': stats['savings_vs_raw'],
            'original_resolution': stats['original_resolution'],
            'downscaled_resolution': stats['downscaled_resolution'],
            'scale_factor': stats['scale_factor'],
            'pixel_reduction': stats['pixel_reduction'],
            'psnr': stats['psnr'],
            'ssim': stats['ssim'],
            'max_pixel_diff': stats['max_pixel_diff'],
            'encode_ms': stats['encode_ms'],
            'decode_ms': stats['decode_ms'],
            'bitexact_reproducible': stats['bitexact_reproducible'],
            'quality': quality,
            'mode': 'ANDROID_BOOST',
            'pipeline': 'JPEG → Downscale Lanczos → H264 Intra → zstd L19',
            'img_before': b64_before,
            'img_after': b64_after,
        }

        history.append({
            'filename': filename,
            'resolution': stats['original_resolution'],
            'mode': f'ANDROID_BOOST ({quality})',
            'ratio_vs_raw': stats['ratio_vs_raw'],
            'savings_vs_raw': stats['savings_vs_raw'],
            'timestamp': datetime.now().isoformat(),
        })

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'detail': str(e)}), 500


@app.route('/api/health')
def api_health():
    return jsonify({'ok': True, 'status': 'running', 'codec': 'HCV PRO v1.0'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))

    print()
    print('╔════════════════════════════════════════════════════════════╗')
    print('║  🎬 HCV PRO — Codec d\'Archivage Broadcast Lossless        ║')
    print('║  Pipeline: Grain Sep → Delta-H → Adaptive Pack → zstd     ║')
    print('╚════════════════════════════════════════════════════════════╝')
    print()
    print(f'  ✅ Serveur Flask: http://localhost:{port}')
    print(f'  📊 Codec HCV PRO chargé (GRAIN_SYNTH, 12-bit)')
    print(f'  🔌 POST /api/compress       — Compression image (Broadcast)')
    print(f'  🔌 POST /api/demo           — Démo broadcast synthétique')
    print(f'  🔌 POST /api/android-boost  — Compression Android Boost (JPEG)')
    print(f'  🔌 GET  /api/history        — Historique')
    print()
    print('  💡 Ctrl+C pour arrêter')
    print()

    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
