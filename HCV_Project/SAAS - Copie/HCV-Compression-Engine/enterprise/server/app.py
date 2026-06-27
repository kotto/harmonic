"""
HCV Enterprise Server — Flask app intégrant codec + sécurité + UI.

Endpoints v2:
  GET  /                       → Dashboard UI
  GET  /api/v2/health          → Status + version
  GET  /api/v2/fingerprint     → Empreinte machine
  GET  /api/v2/license         → Status licence
  POST /api/v2/license/activate → Activer une licence
  POST /api/v2/compress        → Compression (auth requise)

Sécurité:
  - Vérif intégrité au démarrage (manifest.json)
  - Anti-debug optionnel (HCV_STRICT_ANTI_DEBUG=1)
  - Toutes les routes API protégées par licence active
"""

import os
import sys
import time
import io
import json
import secrets
from functools import wraps

import numpy as np
import cv2
from flask import Flask, request, jsonify, send_from_directory, send_file

# Path setup
HERE = os.path.dirname(os.path.abspath(__file__))
ENTERPRISE_ROOT = os.path.dirname(HERE)
PROJECT_ROOT = os.path.dirname(ENTERPRISE_ROOT)
sys.path.insert(0, ENTERPRISE_ROOT)
sys.path.insert(0, PROJECT_ROOT)

from core import HCVEnterpriseCodec
from security import (
    get_fingerprint, get_fingerprint_components,
    verify_license, load_license_from_file, LicenseError,
    FEATURE_PRO_CODEC, FEATURE_VIDEO_BOOST, FEATURE_4K_SUPPORT, FEATURE_8K_SUPPORT,
    secure_startup,
)

VERSION = '2.0.0'

# ── Configuration ────────────────────────────────────────────────────────────
SECRET = os.environ.get('HCV_LICENSE_SECRET', '').encode('utf-8')
DEMO_MODE = os.environ.get('HCV_DEMO_MODE', '1') == '1'
MAX_UPLOAD_MB = int(os.environ.get('HCV_MAX_UPLOAD_MB', '500'))
WEB_DIR = os.path.join(ENTERPRISE_ROOT, 'web')

# Global codec instance (réutilisé entre requêtes)
_codec = HCVEnterpriseCodec(bit_depth=12)

# ── Licence runtime ──────────────────────────────────────────────────────────
_active_license = None


def _try_load_license():
    """Charge et vérifie la licence courante (depuis fichier ou env)."""
    global _active_license

    if DEMO_MODE:
        # Mode démo : simule une licence active complète
        from security.license import License, FEATURE_ALL
        _active_license = License(
            customer_id=0,
            fingerprint=get_fingerprint(),
            expiry_ts=int(time.time()) + 30 * 86400,
            features=FEATURE_ALL,
        )
        return _active_license

    if not SECRET:
        return None

    raw = load_license_from_file()
    if not raw:
        return None
    try:
        _active_license = verify_license(raw, SECRET, get_fingerprint())
        return _active_license
    except LicenseError:
        _active_license = None
        return None


def require_feature(feature: int):
    """Décorateur Flask : refuse si la licence n'a pas la feature."""
    def deco(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not _active_license:
                return jsonify({'error': 'No active license'}), 401
            if _active_license.is_expired():
                return jsonify({'error': 'License expired'}), 401
            if not _active_license.has_feature(feature):
                return jsonify({'error': 'Feature not licensed'}), 403
            return fn(*args, **kwargs)
        return wrapped
    return deco


# ── Flask app ────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder=None)
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_MB * 1024 * 1024


@app.route('/')
def index():
    return send_file(os.path.join(WEB_DIR, 'index.html'))


@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(WEB_DIR, filename)


# ── Health & metadata ────────────────────────────────────────────────────────
@app.route('/api/v2/health')
def health():
    return jsonify({
        'status': 'ok',
        'version': VERSION,
        'license_active': _active_license is not None,
        'demo_mode': DEMO_MODE,
    })


@app.route('/api/v2/fingerprint')
def fingerprint():
    return jsonify({
        'fingerprint': get_fingerprint(),
        'components': get_fingerprint_components(),
    })


# ── License management ───────────────────────────────────────────────────────
@app.route('/api/v2/license')
def license_status():
    if not _active_license:
        return jsonify({'active': False})
    return jsonify({
        'active': True,
        'customer_id': _active_license.customer_id,
        'expires': time.strftime('%Y-%m-%d', time.localtime(_active_license.expiry_ts)),
        'days_remaining': _active_license.days_remaining(),
        'features': _active_license.features,
    })


@app.route('/api/v2/license/activate', methods=['POST'])
def license_activate():
    if DEMO_MODE:
        return jsonify({'success': True, 'note': 'Demo mode — license already active'})

    if not SECRET:
        return jsonify({'success': False, 'error': 'Server secret not configured'}), 500

    data = request.get_json(silent=True) or {}
    key = (data.get('key') or '').strip()
    if not key:
        return jsonify({'success': False, 'error': 'Empty key'}), 400

    try:
        lic = verify_license(key, SECRET, get_fingerprint())
    except LicenseError as e:
        return jsonify({'success': False, 'error': str(e)}), 400

    # Persist license to disk
    lic_path = os.environ.get('HCV_LICENSE_FILE', 'license.key')
    with open(lic_path, 'w') as f:
        f.write(key)

    global _active_license
    _active_license = lic
    return jsonify({'success': True, 'days_remaining': lic.days_remaining()})


# ── Compression ──────────────────────────────────────────────────────────────
@app.route('/api/v2/compress', methods=['POST'])
@require_feature(FEATURE_PRO_CODEC)
def compress():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    bit_depth = int(request.form.get('bit_depth', 8))
    zstd_level = int(request.form.get('zstd_level', 11))

    # Decode upload as image
    blob = file.read()
    arr = np.frombuffer(blob, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
    if img is None:
        return jsonify({'error': 'Could not decode file as image'}), 400

    # Ensure RGB and proper bit depth
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    if img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Convert to bit_depth
    if bit_depth > 8:
        # 8-bit input → upshift to bit_depth
        shift = bit_depth - 8
        frame = (img.astype(np.uint16) << shift)
    else:
        frame = img.astype(np.uint16)

    # 4K/8K feature gating
    h, w = frame.shape[:2]
    if h * w > 8_000_000 and not _active_license.has_feature(FEATURE_4K_SUPPORT):
        return jsonify({'error': '4K resolution requires upgraded license'}), 403
    if h * w > 33_000_000 and not _active_license.has_feature(FEATURE_8K_SUPPORT):
        return jsonify({'error': '8K resolution requires upgraded license'}), 403

    # Encode
    codec = HCVEnterpriseCodec(bit_depth=bit_depth, zstd_level=zstd_level)
    compressed, stats = codec.encode_frame(frame)

    return jsonify({
        'codec': 'enterprise',
        'resolution': stats['resolution'],
        'original_size': stats['original_size'],
        'compressed_size': stats['compressed_size'],
        'ratio': stats['ratio'],
        'savings_pct': stats['savings_pct'],
        'time_ms': stats['time_ms'],
        'speed_mbps': stats['speed_mbps'],
        'workers': stats['workers'],
        'mode': stats['mode'],
    })


# ── Startup ──────────────────────────────────────────────────────────────────
def initialize():
    """Init sécurité + chargement licence."""
    manifest_path = os.path.join(ENTERPRISE_ROOT, 'manifest.json')
    try:
        secure_startup(manifest_path=manifest_path if os.path.exists(manifest_path) else None,
                       package_root=ENTERPRISE_ROOT)
    except Exception as e:
        print(f'[Security] Integrity check failed: {e}', file=sys.stderr)
        if os.environ.get('HCV_STRICT_INTEGRITY') == '1':
            sys.exit(1)

    _try_load_license()
    if _active_license:
        print(f'[License] Active — customer={_active_license.customer_id}, '
              f'days_left={_active_license.days_remaining()}')
    else:
        print('[License] No active license (set HCV_LICENSE_FILE or HCV_LICENSE_KEY)')


initialize()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8088))
    print(f'\n🚀 HCV Enterprise v{VERSION} listening on http://0.0.0.0:{port}\n')
    app.run(host='0.0.0.0', port=port, debug=False)
