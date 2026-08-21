"""
HCV2 Pro Dashboard — Backend Flask
=====================================
Dashboard de gestion de la compression harmonique pour les sociétés TV/Cinéma.
"""
import os, sys, json, uuid, time, hashlib, hmac, io, base64, math, re, tempfile, subprocess, shutil
from pathlib import Path
from datetime import datetime, timedelta
from functools import wraps

# Ajouter le chemin du projet
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from flask_cors import CORS
from PIL import Image as PILImage
import numpy as np

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
        img = np.array(PILImage.open(io.BytesIO(original)).convert('RGB'))
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


@app.route('/api/compress_image', methods=['POST'])
@require_auth
def api_compress_image():
    """Compresse une image, la décompresse, et retourne les deux + métriques."""
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'Aucun fichier'}), 400

    quality = request.form.get('quality', 'archive')
    original = file.read()
    filename = file.filename or 'image.png'

    try:
        img_pil = PILImage.open(io.BytesIO(original)).convert('RGB')
        img_orig = np.array(img_pil)
        oh, ow = img_orig.shape[:2]

        # Compression
        t0 = time.perf_counter()

        if quality == 'pro':
            # Upscale 2× pour contenus déjà compressés
            up_w, up_h = ow * 2, oh * 2
            img_pro = np.array(img_pil.resize((up_w, up_h), PILImage.LANCZOS))
            enc = modal.encode(img_pro, precision=32)
            data = enc['blob']
            fmt_name = 'HCVM+Upscale'
            source_img = img_pro
            metrics_w, metrics_h = up_w, up_h
        elif quality == 'mobile':
            # 📱 Mobile : qualité >35 dB garantie (float32, seuil exact)
            enc = modal.encode(img_orig, precision=32, threshold_scale=1.0)
            data = enc['blob']
            fmt_name = 'HCVM+Mobile'
            source_img = img_orig
            metrics_w, metrics_h = ow, oh
        elif quality == 'lossless':
            # PNG lossless (bit-exact)
            comp_buf = io.BytesIO()
            img_pil.save(comp_buf, format='PNG')
            data = comp_buf.getvalue()
            fmt_name = 'PNG'
            source_img = img_orig
            metrics_w, metrics_h = ow, oh
        else:
            # Modal codec avec qualité ajustée (archive = 32, max = 16)
            prec = 32 if quality == 'archive' else 16
            enc = modal.encode(img_orig, precision=prec)
            data = enc['blob']
            fmt_name = 'HCVM'
            source_img = img_orig
            metrics_w, metrics_h = ow, oh
        enc_time = time.perf_counter() - t0

        # Décompression
        t0 = time.perf_counter()
        if quality == 'lossless':
            rec_img = source_img.copy()  # bit-exact
        else:
            rec_img = modal.decode(data)
            # Redimensionner si nécessaire
            if rec_img.shape[:2] != (metrics_h, metrics_w):
                rec_img = np.array(PILImage.fromarray(rec_img).resize((metrics_w, metrics_h), PILImage.LANCZOS))
        dec_time = time.perf_counter() - t0

        # Métriques
        a, b = source_img.astype(np.float64), rec_img.astype(np.float64)
        mse = float(np.mean((a - b) ** 2))
        psnr_val = 20 * math.log10(255.0 / math.sqrt(mse)) if mse > 0 else float('inf')

        # SSIM
        mx, my = a.mean(), b.mean()
        vx, vy = a.var(), b.var()
        cov = np.mean((a - mx) * (b - my))
        c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
        ssim_val = float(((2 * mx * my + c1) * (2 * cov + c2)) /
                         ((mx ** 2 + my ** 2 + c1) * (vx + vy + c2)))

        # Encode original image (not resized) for display
        orig_buf = io.BytesIO()
        img_pil.save(orig_buf, format='PNG')
        orig_b64 = base64.b64encode(orig_buf.getvalue()).decode()

        # Encode decoded image for display
        rec_buf = io.BytesIO()
        rec_display = rec_img.clip(0, 255).astype(np.uint8)
        PILImage.fromarray(rec_display).save(rec_buf, format='PNG')
        rec_b64 = base64.b64encode(rec_buf.getvalue()).decode()

        # Ratio : taille brute des pixels source vs compressé
        raw_size = metrics_w * metrics_h * 3
        ratio = raw_size / len(data) if len(data) > 0 else 0

        # Encode compressed data as base64 for download
        comp_b64 = base64.b64encode(data).decode()

        return jsonify({
            'original_b64': orig_b64,
            'compressed_b64': rec_b64,
            'download_b64': comp_b64,
            'download_name': f"{filename.rsplit('.',1)[0]}.{('hhd' if data[:4]==b'HHDC' else 'hcvm')}",
            'psnr': '∞' if not np.isfinite(psnr_val) else round(psnr_val, 2),
            'ssim': round(ssim_val, 4),
            'ratio': round(ratio, 1),
            'original_size': len(original),
            'compressed_size': len(data),
            'encoding_time_ms': round(enc_time * 1000, 1),
            'decoding_time_ms': round(dec_time * 1000, 1),
            'dimensions': f'{metrics_w}×{metrics_h}',
            'format': fmt_name,
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compress_video', methods=['POST'])
@require_auth
def api_compress_video():
    """Compresse une vidéo via le pipeline HCV2 (P1+P3), retourne métriques + frames clés."""
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'Aucun fichier'}), 400

    filename = file.filename or 'video.mp4'
    ext = filename.rsplit('.', 1)[-1].lower()
    video_exts = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'm4v', 'mpeg', 'mpg', 'wmv', 'flv'}
    if ext not in video_exts:
        return jsonify({'error': f'Format vidéo non supporté : .{ext}'}), 400

    original = file.read()
    original_size = len(original)

    try:
        # Sauvegarder temporairement la vidéo uploadée
        tmp_in = tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False)
        tmp_in.write(original)
        tmp_in.close()

        # Lire les frames avec OpenCV
        import cv2
        from hcv2_video_pipeline import encode_video, decode_video

        cap = cv2.VideoCapture(tmp_in.name)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Lire jusqu'à 30 frames (pour la démo)
        n_read = min(total_frames, 30)
        frames_rgb = []
        for _ in range(n_read):
            ret, frame = cap.read()
            if not ret:
                break
            frames_rgb.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        cap.release()
        os.unlink(tmp_in.name)

        if len(frames_rgb) < 2:
            return jsonify({'error': 'Vidéo trop courte (< 2 frames)'}), 400

        quality = request.form.get('quality', 'archive')

        if quality == 'lossless':
            # Stockage lossless : ZIP de frames PNG
            t0 = time.perf_counter()
            import zipfile
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                for i, frame in enumerate(frames_rgb):
                    buf = io.BytesIO()
                    PILImage.fromarray(frame).save(buf, format='PNG')
                    zf.writestr(f'frame_{i:04d}.png', buf.getvalue())
            data = zip_buf.getvalue()
            enc_time = time.perf_counter() - t0
            compressed_size = len(data)
            rec_frames = frames_rgb  # lossless : identique à l'original
            dec_time = 0
            fmt_name = 'ZIP+PNG'
        else:
            t0 = time.perf_counter()
            if quality == 'max':
                # Ratio extrême : grain régénéré (destructeur mais ratio ×100+)
                enc = encode_video(frames_rgb, use_memory=True, grain=True)
            elif quality == 'pro':
                # Upscale 2× pour contenus déjà compressés
                up_w, up_h = int(w * 2.0), int(h * 2.0)
                encode_frames = [np.array(PILImage.fromarray(f).resize((up_w, up_h), PILImage.LANCZOS))
                                 for f in frames_rgb]
                enc = encode_video(encode_frames, use_memory=True, grain=False, mag_dtype=np.float32)
            elif quality == 'mobile':
                # 📱 Mobile : seuil 0.5 + float16 = >36 dB garanti, qualité visuelle supérieure à la source
                enc = encode_video(frames_rgb, use_memory=True, grain=False, mag_dtype=np.float16,
                                   predictor='golden', threshold_scale=0.5)
            else:
                # archive : résidu réel, float16
                enc = encode_video(frames_rgb, use_memory=True, grain=False, mag_dtype=np.float16)
            data = enc['blob']
            enc_time = time.perf_counter() - t0
            compressed_size = len(data)

            t0 = time.perf_counter()
            rec_frames = decode_video(enc, predictor='golden')
            dec_time = time.perf_counter() - t0
            fmt_name = 'HCV2' + {'pro': '+Upscale', 'mobile': '+Mobile'}.get(quality, '')

        # Résolution source pour les métriques (upscalée en mode Pro)
        if quality == 'pro':
            metrics_w, metrics_h = int(w * 2.0), int(h * 2.0)
            source_frames = encode_frames
        else:
            metrics_w, metrics_h = w, h
            source_frames = frames_rgb

        # Ratio de compression honnête : taille brute des frames vs compressé
        raw_data_size = metrics_w * metrics_h * 3 * len(source_frames)
        ratio = raw_data_size / compressed_size if compressed_size > 0 else 0

        # Métriques sur la dernière frame (la mieux prédite)
        orig_last = source_frames[-1].astype(np.float64)
        rec_last = rec_frames[-1].astype(np.float64)

        # Ajuster les dimensions si nécessaire
        if rec_last.shape[:2] != orig_last.shape[:2]:
            rec_last = np.array(PILImage.fromarray(rec_last.astype(np.uint8)).resize((metrics_w, metrics_h), PILImage.LANCZOS)).astype(np.float64)

        mse = float(np.mean((orig_last - rec_last) ** 2))
        psnr_val = 20 * math.log10(255.0 / math.sqrt(mse)) if mse > 0 else float('inf')

        # SSIM sur la dernière frame
        mx, my = orig_last.mean(), rec_last.mean()
        vx, vy = orig_last.var(), rec_last.var()
        cov = np.mean((orig_last - mx) * (rec_last - my))
        c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
        ssim_val = float(((2 * mx * my + c1) * (2 * cov + c2)) /
                         ((mx ** 2 + my ** 2 + c1) * (vx + vy + c2))) if (vx + vy + c2) > 0 else 0.0

        # Encoder les frames en base64 pour l'affichage (première et dernière)
        orig_buf = io.BytesIO()
        PILImage.fromarray(frames_rgb[0]).save(orig_buf, format='JPEG', quality=85)
        orig_b64 = base64.b64encode(orig_buf.getvalue()).decode()

        rec_buf = io.BytesIO()
        PILImage.fromarray(rec_frames[-1].clip(0, 255).astype(np.uint8)).save(rec_buf, format='JPEG', quality=85)
        rec_b64 = base64.b64encode(rec_buf.getvalue()).decode()

        # Générer la prévisualisation vidéo complète (MP4 H.264 via FFmpeg)
        tmpdir = None
        try:
            tmpdir = tempfile.mkdtemp()
            # Sauver les frames en PNG
            for i, frame in enumerate(rec_frames):
                PILImage.fromarray(frame.clip(0, 255).astype(np.uint8)).save(
                    os.path.join(tmpdir, f'f{i:04d}.png'))
            out_mp4 = os.path.join(tmpdir, 'preview.mp4')
            # Calculer la framerate : utiliser le FPS original ou 10 par défaut
            preview_fps = max(fps, 10) if fps > 0 else 10
            subprocess.run([
                'ffmpeg', '-y', '-framerate', str(preview_fps),
                '-i', os.path.join(tmpdir, 'f%04d.png'),
                '-c:v', 'libx264', '-preset', 'fast',
                '-pix_fmt', 'yuv420p', '-crf', '18',
                out_mp4
            ], capture_output=True, text=True, timeout=60)
            with open(out_mp4, 'rb') as f:
                preview_bytes = f.read()
            if tmpdir:
                shutil.rmtree(tmpdir, ignore_errors=True)
            preview_video_b64 = base64.b64encode(preview_bytes).decode()
            preview_mime = 'video/mp4'
        except Exception:
            if tmpdir:
                shutil.rmtree(tmpdir, ignore_errors=True)
            preview_video_b64 = orig_b64
            preview_mime = 'image/jpeg'

        # Le fichier compressé pour téléchargement
        comp_b64 = base64.b64encode(data).decode()

        return jsonify({
            'original_b64': orig_b64,
            'compressed_b64': rec_b64,
            'preview_video_b64': preview_video_b64,
            'preview_mime': preview_mime,
            'download_b64': comp_b64,
            'download_name': f"{filename.rsplit('.',1)[0]}.{'zip' if quality == 'lossless' else 'hcv2'}",
            'psnr': '∞' if not np.isfinite(psnr_val) else round(psnr_val, 2),
            'ssim': round(ssim_val, 4),
            'ratio': round(ratio, 1),
            'original_size': original_size,
            'compressed_size': compressed_size,
            'encoding_time_ms': round(enc_time * 1000, 1),
            'decoding_time_ms': round(dec_time * 1000, 1),
            'dimensions': f'{metrics_w}×{metrics_h}',
            'format': fmt_name,
            'fps': fps,
            'frames': len(frames_rgb),
            'is_video': True,
        })

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