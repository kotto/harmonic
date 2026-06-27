#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HCV PRO - Enterprise Web Interface
================================
Interface web sécurisée pour entreprise

🌐 Interface web moderne
🛡️ Sécurité renforcée
📊 Monitoring temps réel
🔐 Authentification JWT
"""

import os
import sys
import json
import hashlib
import jwt
import time
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for, session
from flask_cors import CORS
from functools import wraps
import threading
import uuid
from pathlib import Path

# Ajout des chemins des modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

try:
    from compressor import HCVCompressorSecure
except ImportError:
    print("❌ Module compresseur non trouvé")
    sys.exit(1)

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/web_interface.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HCVEnterpriseWeb:
    """
    Interface web entreprise HCV PRO
    Sécurité maximale et monitoring complet
    """
    
    def __init__(self):
        """Initialisation interface web sécurisée"""
        template_path = os.path.join(os.path.dirname(__file__), '..', '..', 'templates')
        self.app = Flask(__name__, template_folder=template_path)
        self.app.secret_key = self._generate_secret_key()
        
        # Configuration CORS
        CORS(self.app, methods=['GET', 'POST', 'PUT', 'DELETE'])
        
        # Initialisation compresseur
        try:
            self.compressor = HCVCompressorSecure()
            logger.info("✅ Compresseur HCV PRO initialisé")
        except Exception as e:
            logger.error(f"❌ Erreur initialisation compresseur: {e}")
            raise
        
        # Configuration sécurité
        self.setup_security_middleware()
        
        # Configuration routes
        self.setup_routes()
        
        # Monitoring
        self.compression_jobs = {}
        self.system_stats = {
            'total_jobs': 0,
            'completed_jobs': 0,
            'failed_jobs': 0,
            'start_time': datetime.now()
        }
        
        # Thread monitoring
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
    
    def _generate_secret_key(self):
        """Génération clé secrète sécurisée"""
        return hashlib.sha256(f"HCV_PRO_ENTERPRISE_{time.time()}_{uuid.uuid4()}".encode()).hexdigest()
    
    def setup_security_middleware(self):
        """Configuration middleware de sécurité"""
        
        @self.app.before_request
        def validate_request():
            """Validation des requêtes entrantes"""
            # Logging des requêtes
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            logger.info(f"📡 Requête: {request.method} {request.path} - IP: {client_ip}")
            
            # Rate limiting simple
            if request.endpoint not in ['static', 'login', 'health']:
                self._check_rate_limit(client_ip)
        
        @self.app.after_request
        def add_security_headers(response):
            """Ajout headers sécurité"""
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = "default-src 'self'"
            return response
    
    def _check_rate_limit(self, client_ip):
        """Vérification rate limiting"""
        # Implémentation simple - à améliorer avec Redis pour production
        if not hasattr(self, '_rate_limit_cache'):
            self._rate_limit_cache = {}
        
        now = time.time()
        if client_ip not in self._rate_limit_cache:
            self._rate_limit_cache[client_ip] = []
        
        # Nettoyage anciennes requêtes
        self._rate_limit_cache[client_ip] = [
            req_time for req_time in self._rate_limit_cache[client_ip] 
            if now - req_time < 3600  # 1 heure
        ]
        
        # Vérification limite (100 requêtes/heure)
        if len(self._rate_limit_cache[client_ip]) > 100:
            logger.warning(f"⚠️ Rate limit dépassé pour IP: {client_ip}")
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        self._rate_limit_cache[client_ip].append(now)
    
    def setup_routes(self):
        """Configuration des routes"""
        
        # Page principale
        @self.app.route('/')
        def index():
            """Page d'accueil entreprise"""
            try:
                if not self._is_authenticated():
                    return redirect(url_for('login'))
                
                return render_template('enterprise_dashboard.html')
            except Exception as e:
                logger.error(f"❌ Erreur page index: {e}")
                return f"Erreur: {str(e)}", 500
        
        # Page login
        @self.app.route('/login')
        def login():
            """Page d'authentification"""
            return '''
<!DOCTYPE html>
<html>
<head>
    <title>HCV PRO Enterprise - Login</title>
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #667eea, #764ba2); 
               display: flex; align-items: center; justify-content: center; min-height: 100vh; }
        .login { background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); 
                 width: 350px; text-align: center; }
        h1 { color: #333; margin-bottom: 2rem; }
        input { width: 100%; padding: 0.75rem; margin: 0.5rem 0; border: 2px solid #ddd; border-radius: 5px; }
        button { width: 100%; padding: 0.75rem; background: linear-gradient(135deg, #667eea, #764ba2); 
                color: white; border: none; border-radius: 5px; cursor: pointer; margin-top: 1rem; }
        .demo { background: #f8f9fa; padding: 1rem; border-radius: 5px; margin-top: 1rem; font-size: 0.85rem; }
    </style>
</head>
<body>
    <div class="login">
        <h1>🚀 HCV PRO Enterprise</h1>
        <form id="loginForm" onsubmit="login(event)">
            <input type="text" id="username" placeholder="Utilisateur" value="admin" required>
            <input type="password" id="password" placeholder="Mot de passe" value="HCV_PRO_2024_ENTERPRISE" required>
            <button type="submit">Se connecter</button>
        </form>
        <div class="demo">
            <strong>Demo:</strong><br>
            admin / HCV_PRO_2024_ENTERPRISE
        </div>
    </div>
    <script>
        function login(e) {
            e.preventDefault();
            fetch('/api/auth', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    username: document.getElementById('username').value,
                    password: document.getElementById('password').value
                })
            }).then(r => r.json()).then(data => {
                if(data.success) {
                    localStorage.setItem('hcv_token', data.token);
                    window.location.href = '/';
                } else {
                    alert('Erreur: ' + data.error);
                }
            });
        }
    </script>
</body>
</html>
            '''
        
        # Authentification
        @self.app.route('/api/auth', methods=['POST'])
        def authenticate():
            """Authentification JWT"""
            try:
                data = request.get_json()
                username = data.get('username')
                password = data.get('password')
                
                # Validation credentials
                if self._validate_credentials(username, password):
                    token = self._generate_jwt_token(username)
                    return jsonify({
                        'success': True,
                        'token': token,
                        'user_info': self._get_user_info(username)
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Identifiants invalides'
                    }), 401
                    
            except Exception as e:
                logger.error(f"❌ Erreur authentification: {e}")
                return jsonify({'success': False, 'error': 'Erreur serveur'}), 500
        
        # API Compression
        @self.app.route('/api/compress', methods=['POST'])
        @self._require_auth
        def compress_file():
            """API de compression sécurisée"""
            try:
                # Validation fichier
                if 'file' not in request.files:
                    return jsonify({'error': 'Aucun fichier fourni'}), 400
                
                file = request.files['file']
                if file.filename == '':
                    return jsonify({'error': 'Nom de fichier vide'}), 400
                
                # Récupération paramètres
                mode = request.form.get('mode', 'balanced')
                security_level = request.form.get('security_level', 'quantum_harmonic')
                
                # Création job ID
                job_id = str(uuid.uuid4())
                
                # Sauvegarde fichier temporaire
                temp_dir = tempfile.mkdtemp()
                input_path = os.path.join(temp_dir, file.filename)
                file.save(input_path)
                
                output_path = os.path.join(temp_dir, f"{file.filename}.hcvpro")
                
                # Création job
                job = {
                    'id': job_id,
                    'filename': file.filename,
                    'mode': mode,
                    'security_level': security_level,
                    'input_path': input_path,
                    'output_path': output_path,
                    'status': 'processing',
                    'start_time': datetime.now(),
                    'progress': 0,
                    'user': request.user
                }
                
                self.compression_jobs[job_id] = job
                self.system_stats['total_jobs'] += 1
                
                # Démarrage compression en arrière-plan
                compression_thread = threading.Thread(
                    target=self._process_compression_job,
                    args=(job_id,),
                    daemon=True
                )
                compression_thread.start()
                
                return jsonify({
                    'success': True,
                    'job_id': job_id,
                    'message': 'Compression démarrée'
                })
                
            except Exception as e:
                logger.error(f"❌ Erreur compression: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API Statut Job
        @self.app.route('/api/job/<job_id>', methods=['GET'])
        @self._require_auth
        def get_job_status(job_id):
            """Récupération statut job"""
            if job_id not in self.compression_jobs:
                return jsonify({'error': 'Job non trouvé'}), 404
            
            job = self.compression_jobs[job_id]
            return jsonify({
                'id': job['id'],
                'filename': job['filename'],
                'status': job['status'],
                'progress': job.get('progress', 0),
                'mode': job['mode'],
                'security_level': job['security_level'],
                'start_time': job['start_time'].isoformat(),
                'end_time': job.get('end_time', '').isoformat() if job.get('end_time') else '',
                'result': job.get('result', {}),
                'error': job.get('error', '')
            })
        
        # API Téléchargement
        @self.app.route('/api/download/<job_id>', methods=['GET'])
        @self._require_auth
        def download_result(job_id):
            """Téléchargement résultat compression"""
            if job_id not in self.compression_jobs:
                return jsonify({'error': 'Job non trouvé'}), 404
            
            job = self.compression_jobs[job_id]
            
            if job['status'] != 'completed':
                return jsonify({'error': 'Job non terminé'}), 400
            
            if not os.path.exists(job['output_path']):
                return jsonify({'error': 'Fichier résultat non trouvé'}), 404
            
            return send_file(
                job['output_path'],
                as_attachment=True,
                download_name=f"{job['filename']}.hcvpro"
            )
        
        # API Système
        @self.app.route('/api/system/info', methods=['GET'])
        @self._require_auth
        def get_system_info():
            """Informations système"""
            try:
                info = self.compressor.get_system_info()
                info['web_stats'] = self.system_stats
                info['active_jobs'] = len([j for j in self.compression_jobs.values() if j['status'] == 'processing'])
                return jsonify(info)
            except Exception as e:
                logger.error(f"❌ Erreur récupération infos système: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API Jobs
        @self.app.route('/api/jobs', methods=['GET'])
        @self._require_auth
        def list_jobs():
            """Liste des jobs"""
            try:
                jobs_list = []
                for job in self.compression_jobs.values():
                    jobs_list.append({
                        'id': job['id'],
                        'filename': job['filename'],
                        'status': job['status'],
                        'mode': job['mode'],
                        'security_level': job['security_level'],
                        'start_time': job['start_time'].isoformat(),
                        'progress': job.get('progress', 0)
                    })
                
                return jsonify({'jobs': jobs_list})
            except Exception as e:
                logger.error(f"❌ Erreur liste jobs: {e}")
                return jsonify({'error': str(e)}), 500
        
        # Health check
        @self.app.route('/health')
        def health_check():
            """Vérification santé système"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'uptime': str(datetime.now() - self.system_stats['start_time']),
                'active_jobs': len([j for j in self.compression_jobs.values() if j['status'] == 'processing'])
            })
    
    def _is_authenticated(self):
        """Vérification authentification"""
        token = request.headers.get('Authorization')
        if not token:
            return False
        
        try:
            token = token.replace('Bearer ', '')
            decoded = jwt.decode(token, self.app.secret_key, algorithms=['HS256'])
            return True
        except:
            return False
    
    def _require_auth(self, f):
        """Décorateur authentification requise"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not self._is_authenticated():
                return jsonify({'error': 'Authentification requise'}), 401
            
            # Ajout utilisateur à la requête
            token = request.headers.get('Authorization').replace('Bearer ', '')
            decoded = jwt.decode(token, self.app.secret_key, algorithms=['HS256'])
            request.user = decoded['username']
            
            return f(*args, **kwargs)
        return decorated_function
    
    def _validate_credentials(self, username, password):
        """Validation identifiants"""
        # Implémentation simple - adapter avec base de données entreprise
        valid_credentials = {
            'admin': 'HCV_PRO_2024_ENTERPRISE',
            'user': 'HCV_USER_2024',
            'demo': 'demo123'
        }
        
        return username in valid_credentials and valid_credentials[username] == password
    
    def _generate_jwt_token(self, username):
        """Génération token JWT"""
        payload = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=8),  # 8 heures
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, self.app.secret_key, algorithm='HS256')
    
    def _get_user_info(self, username):
        """Informations utilisateur"""
        users_info = {
            'admin': {'role': 'administrator', 'permissions': ['all']},
            'user': {'role': 'user', 'permissions': ['compress', 'download']},
            'demo': {'role': 'demo', 'permissions': ['compress']}
        }
        
        return users_info.get(username, {'role': 'unknown', 'permissions': []})
    
    def _process_compression_job(self, job_id):
        """Traitement job de compression"""
        job = self.compression_jobs[job_id]
        
        try:
            logger.info(f"🚀 Début compression job {job_id}: {job['filename']}")
            
            # Simulation progression
            for i in range(0, 101, 10):
                if job['status'] == 'cancelled':
                    return
                
                job['progress'] = i
                time.sleep(0.5)  # Simulation temps compression
            
            # Compression réelle
            result = self.compressor.compress_file(
                job['input_path'],
                job['output_path'],
                job['mode'],
                job['security_level']
            )
            
            if result.get('success'):
                job['status'] = 'completed'
                job['result'] = result
                self.system_stats['completed_jobs'] += 1
                logger.info(f"✅ Compression réussie job {job_id}")
            else:
                job['status'] = 'failed'
                job['error'] = result.get('error', 'Erreur inconnue')
                self.system_stats['failed_jobs'] += 1
                logger.error(f"❌ Échec compression job {job_id}: {job['error']}")
            
            job['end_time'] = datetime.now()
            
        except Exception as e:
            job['status'] = 'failed'
            job['error'] = str(e)
            job['end_time'] = datetime.now()
            self.system_stats['failed_jobs'] += 1
            logger.error(f"❌ Erreur traitement job {job_id}: {e}")
        
        finally:
            # Nettoyage fichiers temporaires après 1 heure
            threading.Timer(3600, self._cleanup_job_files, args=[job_id]).start()
    
    def _cleanup_job_files(self, job_id):
        """Nettoyage fichiers temporaires"""
        if job_id in self.compression_jobs:
            job = self.compression_jobs[job_id]
            
            try:
                # Suppression fichiers temporaires
                if os.path.exists(job['input_path']):
                    os.remove(job['input_path'])
                if os.path.exists(job['output_path']):
                    os.remove(job['output_path'])
                
                # Suppression répertoire temporaire
                temp_dir = os.path.dirname(job['input_path'])
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                
                logger.info(f"🧹 Nettoyage fichiers job {job_id}")
                
            except Exception as e:
                logger.error(f"❌ Erreur nettoyage job {job_id}: {e}")
            
            # Suppression job après 24 heures
            threading.Timer(86400, self._remove_job, args=[job_id]).start()
    
    def _remove_job(self, job_id):
        """Suppression job de la mémoire"""
        if job_id in self.compression_jobs:
            del self.compression_jobs[job_id]
            logger.info(f"🗑️ Job {job_id} supprimé de la mémoire")
    
    def _monitoring_loop(self):
        """Boucle monitoring système"""
        while True:
            try:
                # Nettoyage cache rate limiting
                if hasattr(self, '_rate_limit_cache'):
                    now = time.time()
                    for ip in list(self._rate_limit_cache.keys()):
                        self._rate_limit_cache[ip] = [
                            req_time for req_time in self._rate_limit_cache[ip]
                            if now - req_time < 3600
                        ]
                        
                        if not self._rate_limit_cache[ip]:
                            del self._rate_limit_cache[ip]
                
                time.sleep(300)  # Vérification toutes les 5 minutes
                
            except Exception as e:
                logger.error(f"❌ Erreur monitoring: {e}")
                time.sleep(60)
    
    def run(self, host='0.0.0.0', port=8080, debug=False):
        """Démarrage interface web"""
        logger.info(f"🚀 Démarrage interface web HCV PRO Enterprise sur {host}:{port}")
        
        # Création répertoires nécessaires
        os.makedirs('logs', exist_ok=True)
        os.makedirs('temp', exist_ok=True)
        
        self.app.run(host=host, port=port, debug=debug, threaded=True)

# Point d'entrée
if __name__ == "__main__":
    try:
        app = HCVEnterpriseWeb()
        app.run(host='0.0.0.0', port=8080, debug=False)
    except Exception as e:
        logger.error(f"❌ Erreur démarrage interface web: {e}")
        sys.exit(1)
