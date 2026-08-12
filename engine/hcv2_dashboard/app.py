"""
HCV2 Pro Dashboard — Backend Flask
=====================================
Dashboard de gestion de la compression harmonique pour les sociétés TV/Cinéma.
"""
import os, sys, json, uuid, time, hashlib, hmac, io, base64
from pathlib import Path
from datetime import datetime, timedelta
from functools import wraps

# Ajouter le chemin du projet
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from flask_cors import CORS
import numpy as np
from PIL import Image

# Import conditionnel du codec
try:
    from multimodal.harmonic_codec import HarmonicCodec
    from multimodal.harmonic_database import HarmonicDatabase
    from multimodal.build_dict import build_dictionary
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'vital-ka' / 'core' / 'python'))
    import hcv2_modal_codec as modal
    _HAVE_CODEC = True
except ImportError:
    _HAVE_CODEC = False

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'hcv2-pro-secret-key-change-in-production')
CORS(app)

# Configuration
DATA_DIR = Path(os.environ.get('DATA_DIR', str(Path(__file__).resolve().parent / 'data')))
USERS_FILE = DATA_DIR / 'users.json'
JOBS_FILE = DATA_DIR / 'jobs.json'
KEYS_FILE = DATA_DIR / 'api_keys.json'
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Dictionnaire broadcast
DICT_PATH = Path(os.environ.get('DICT_PATH', 
    str(Path(__file__).resolve().parent.parent / 'dictionaries' / 'broadcast.hdb')))

# Utilisateurs par défaut
DEFAULT_USERS = {
    'admin': {'password': 'admin123', 'role': 'admin', 'quota': 10_000_000_000_000},
    'demo': {'password': 'demo123', 'role': 'user', 'quota': 1_000_000_000_000},
}

def load_json(path, default=None):
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return default or {}

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def init_data():
    if not USERS_FILE.exists():
        save_json(USERS_FILE, DEFAULT_USERS)
    if not JOBS_FILE.exists():
        save_json(JOBS_FILE, [])
    if not KEYS_FILE.exists():
        save_json(KEYS_FILE, {})

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            if request.is_json:
                return jsonify({'error': 'Non authentifié'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    @wraps(f)
    @require_auth
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            return jsonify({'error': 'Accès refusé'}), 403
        return f(*args, **kwargs)
    return decorated

def get_usage_stats():
    jobs = load_json(JOBS_FILE, [])
    total_jobs = len(jobs)
    total_original = sum(j.get('original_size', 0) for j in jobs)
    total_compressed = sum(j.get('compressed_size', 0) for j in jobs)
    total_saved = total_original - total_compressed
    avg_ratio = total_original / total_compressed if total_compressed > 0 else 0
    return {
        'total_jobs': total_jobs,
        'total_original': total_original,
        'total_compressed': total_compressed,
        'total_saved': total_saved,
        'avg_ratio': round(avg_ratio, 1),
        'saved_percent': round(total_saved / total_original * 100, 1) if total_original > 0 else 0,
    }

# ─── Routes ───────────────────────────────────────────────────────────

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    users = load_json(USERS_FILE, DEFAULT_USERS)
    username = request.form.get('username')
    password = request.form.get('password')
    user = users.get(username)
    if user and user['password'] == password:
        session['user'] = username
        session['role'] = user.get('role', 'user')
        session['quota'] = user.get('quota', 0)
        return redirect(url_for('dashboard'))
    return render_template('login.html', error='Identifiants incorrects')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@require_auth
def dashboard():
    stats = get_usage_stats()
    jobs = load_json(JOBS_FILE, [])[-20:]  # 20 derniers jobs
    return render_template('dashboard.html', stats=stats, jobs=jobs, user=session.get('user'))

@app.route('/api/compress', methods=['POST'])
@require_auth
def api_compress():
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'Aucun fichier'}), 400
    
    quality = request.form.get('quality', 'archive')
    original = file.read()
    original_size = len(original)
    filename = file.filename or 'fichier'
    
    # Vérifier le quota
    user = session['user']
    users = load_json(USERS_FILE, DEFAULT_USERS)
    quota = users.get(user, {}).get('quota', 0)
    jobs = load_json(JOBS_FILE, [])
    user_usage = sum(j.get('original_size', 0) for j in jobs if j.get('user') == user)
    if user_usage + original_size > quota:
        return jsonify({'error': 'Quota dépassé'}), 402
    
    try:
        img = np.array(Image.open(io.BytesIO(original)).convert('RGB'))
        db = HarmonicDatabase()
        if DICT_PATH.exists():
            db.load(str(DICT_PATH))
        hc = HarmonicCodec(db, use_hcv=True, quality=100)
        
        t0 = time.perf_counter()
        if quality == 'lossless':
            data = hc.encode_full(img)
            fmt = 'HHDC'
        elif quality == 'max':
            data = modal.encode(img)['blob']
            fmt = 'HCVM'
        elif quality == 'pro':
            data, _ = hc.encode_select(img, min_psnr=30.0)
            fmt = 'HCVM' if data[:4] == b'HCVM' else 'HHDC'
        else:
            data, _ = hc.encode_select(img, min_psnr=20.0)
            fmt = 'HCVM' if data[:4] == b'HCVM' else 'HHDC'
        enc_time = time.perf_counter() - t0
        
        compressed_size = len(data)
        ratio = original_size / compressed_size if compressed_size > 0 else 0
        
        # Sauvegarder le job
        job_id = str(uuid.uuid4())[:8]
        job = {
            'id': job_id, 'user': user, 'filename': filename,
            'original_size': original_size, 'compressed_size': compressed_size,
            'ratio': round(ratio, 1), 'format': fmt, 'quality': quality,
            'time': round(enc_time, 3), 'timestamp': datetime.now().isoformat(),
        }
        jobs.append(job)
        save_json(JOBS_FILE, jobs)
        
        # Retourner le fichier compressé
        output = io.BytesIO(data); output.seek(0)
        resp = send_file(output, mimetype='application/octet-stream',
                        as_attachment=True,
                        download_name=f"{filename.rsplit('.',1)[0]}.{fmt.lower()}")
        resp.headers['X-Job-ID'] = job_id
        resp.headers['X-Ratio'] = str(round(ratio, 1))
        resp.headers['X-Format'] = fmt
        resp.headers['X-Time'] = str(round(enc_time, 3))
        return resp
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
@require_auth
def api_stats():
    stats = get_usage_stats()
    user = session['user']
    jobs = load_json(JOBS_FILE, [])
    user_jobs = [j for j in jobs if j.get('user') == user]
    user_usage = sum(j.get('original_size', 0) for j in user_jobs)
    quota = session.get('quota', 0)
    stats['user_jobs'] = len(user_jobs)
    stats['user_usage'] = user_usage
    stats['quota'] = quota
    stats['quota_percent'] = round(user_usage / quota * 100, 1) if quota > 0 else 0
    return jsonify(stats)

@app.route('/api/jobs')
@require_auth
def api_jobs():
    jobs = load_json(JOBS_FILE, [])
    user = session['user']
    limit = request.args.get('limit', 50, int)
    if session.get('role') != 'admin':
        jobs = [j for j in jobs if j.get('user') == user]
    return jsonify(jobs[-limit:])

@app.route('/api/keys', methods=['GET', 'POST'])
@require_auth
def api_keys():
    keys = load_json(KEYS_FILE, {})
    user = session['user']
    if request.method == 'POST':
        key = hmac.new(os.urandom(32), f"{user}:{time.time()}".encode(), hashlib.sha256).hexdigest()[:32]
        keys[key] = {'user': user, 'created': datetime.now().isoformat(), 'active': True}
        save_json(KEYS_FILE, keys)
        return jsonify({'key': key})
    user_keys = {k: v for k, v in keys.items() if v.get('user') == user or session.get('role') == 'admin'}
    return jsonify(user_keys)

@app.route('/api/keys/<key>', methods=['DELETE'])
@require_auth
def api_delete_key(key):
    keys = load_json(KEYS_FILE, {})
    if key in keys:
        del keys[key]
        save_json(KEYS_FILE, keys)
    return jsonify({'success': True})

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'ok', 'version': '1.0',
        'codec': 'available' if _HAVE_CODEC else 'unavailable',
        'dictionary': DICT_PATH.exists(),
        'jobs': len(load_json(JOBS_FILE, [])),
    })

# ─── Administration ───────────────────────────────────────────────────

@app.route('/admin')
@require_admin
def admin():
    users = load_json(USERS_FILE, DEFAULT_USERS)
    jobs = load_json(JOBS_FILE, [])
    return render_template('admin.html', users=users, jobs=jobs, stats=get_usage_stats())

@app.route('/api/admin/users', methods=['GET', 'POST'])
@require_admin
def admin_users():
    users = load_json(USERS_FILE, DEFAULT_USERS)
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        if username in users:
            return jsonify({'error': 'Utilisateur existe déjà'}), 400
        users[username] = {
            'password': data.get('password', 'changeme'),
            'role': data.get('role', 'user'),
            'quota': int(data.get('quota', 1_000_000_000_000)),
        }
        save_json(USERS_FILE, users)
        return jsonify({'success': True})
    return jsonify({k: {**v, 'password': '***'} for k, v in users.items()})

if __name__ == '__main__':
    init_data()
    port = int(os.environ.get('PORT', 8765))
    print(f"🚀 HCV2 Pro Dashboard — http://0.0.0.0:{port}")
    print(f"   Identifiants : admin / admin123")
    app.run(host='0.0.0.0', port=port, debug=True)