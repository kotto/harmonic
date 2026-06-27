#!/usr/bin/env python3
"""
HCV PRO - API de Compression Réelle pour Interface Web
======================================================
API Flask pour connecter l'interface web avec le moteur de compression HCV PRO

🚀 Fonctionnalités :
- Compression réelle avec le package HCV PRO
- Upload de fichiers via HTTP
- Progression en temps réel
- Visualisation vidéo des particules
- Gestion des licences
- Historique des compressions

📡 Endpoints :
- POST /api/compress : Lancer une compression
- GET /api/status/:id : Statut d'une compression
- GET /api/results/:id : Résultats d'une compression
- POST /api/license : Activer une licence
- GET /api/stats : Statistiques globales
"""

import os
import sys
import json
import time
import threading
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import tempfile
import uuid

# Ajouter le répertoire mobile au path
mobile_dir = Path(__file__).parent.parent / "mobile"
sys.path.insert(0, str(mobile_dir))

try:
    from hcvpro_autonomous.bin.harmonic_autonomous_package import HarmonicAutonomousPackage
except ImportError:
    print("❌ Package HCV PRO non trouvé")
    sys.exit(1)

app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB max
UPLOAD_FOLDER = tempfile.mkdtemp()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# État global
compression_jobs = {}
package_instance = None
license_active = False

class CompressionJob:
    """Classe pour gérer un job de compression"""
    
    def __init__(self, job_id, file_path, mode, security_level, options):
        self.id = job_id
        self.file_path = file_path
        self.mode = mode
        self.security_level = security_level
        self.options = options
        self.status = 'pending'
        self.progress = 0
        self.start_time = None
        self.end_time = None
        self.original_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        self.compressed_size = None
        self.compression_ratio = None
        self.processing_time = None
        self.error_message = None
        self.output_path = None
        self.speed = 0
        self.current_ratio = 0
        
    def to_dict(self):
        """Convertir en dictionnaire pour JSON"""
        return {
            'id': self.id,
            'file_name': os.path.basename(self.file_path),
            'mode': self.mode,
            'security_level': self.security_level,
            'status': self.status,
            'progress': self.progress,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'original_size': self.original_size,
            'compressed_size': self.compressed_size,
            'compression_ratio': self.compression_ratio,
            'processing_time': self.processing_time,
            'error_message': self.error_message,
            'speed': self.speed,
            'current_ratio': self.current_ratio
        }

def initialize_package():
    """Initialise le package HCV PRO"""
    global package_instance, license_active
    
    try:
        package_instance = HarmonicAutonomousPackage()
        
        # Licence démo 48h
        demo_license = "eyJ2ZXJzaW9uIjogIjEuMC4wIiwgImNvbXBhbnkiOiAiREVNT19IQ1ZfUFJPXzQ4SCIsICJzdGFydF90aW1lIjogMTc3NzEyODYxNy41ODY1NTQ4LCAiZXhwaXJ5X3RpbWUiOiAxNzc3MzAxNDE3LjU4NjU1NDgsICJkdXJhdGlvbl9ob3VycyI6IDQ4LCAibWF4X2NvbXByZXNzaW9ucyI6IDEwMDAsICJjdXJyZW50X2NvbXByZXNzaW9ucyI6IDAsICJzZWN1cml0eV9sZXZlbCI6ICJxdWFudHVtX2hhcm1vbmljIiwgImZlYXR1cmVzIjogWyJjb21wcmVzc2lvbl9zZWN1cmUiLCAicXVhbnR1bV9lbmNyeXB0aW9uIiwgImludGVncml0eV9jaGVjayIsICJsaWNlbnNlX3ZhbGlkYXRpb24iLCAic2VjdXJpdHlfbW9uaXRvcmluZyIsICJhbnRpX3JldmVyc2VfZW5naW5lZXJpbmciLCAiZnVsbF9hcGlfYWNjZXNzIiwgInByaW9yaXR5X3N1cHBvcnQiXSwgImhhcmR3YXJlX2lkIjogIjI1ODA3ZjA2MzIyZjQxMzkiLCAibGljZW5zZV9pZCI6ICIyNDdhN2RhMWNlZWIwMWQ2MDg3YTliZWQ2NDJlMzA5MyIsICJzaWduYXR1cmUiOiAiMWU4NGI5NDM3ZjA0MDU2YzFlZWE1ODliNzRlZjU5NDQ5MmZiNzlmNTliNWE1MTlkMzhjY2Q5ZjliNjY1MDRkMSJ9"
        
        if package_instance.initialize(demo_license):
            license_active = True
            print("✅ Package HCV PRO initialisé avec licence démo")
            return True
        else:
            print("❌ Échec initialisation licence")
            return False
            
    except Exception as e:
        print(f"❌ Erreur initialisation package: {e}")
        return False

def compress_file_real(job):
    """Compression réelle du fichier"""
    try:
        job.status = 'running'
        job.start_time = datetime.now()
        
        # Générer le chemin de sortie
        output_path = os.path.join(
            app.config['UPLOAD_FOLDER'], 
            f"{os.path.basename(job.file_path)}.hcvpro"
        )
        job.output_path = output_path
        
        # Effectuer la compression réelle
        result = package_instance.compress_file(job.file_path, output_path)
        
        if 'error' in result:
            job.status = 'failed'
            job.error_message = result['error']
        else:
            job.status = 'completed'
            job.compressed_size = result['compressed_size']
            job.compression_ratio = result['ratio']
            job.processing_time = result['processing_time_ms']
        
        job.end_time = datetime.now()
        job.progress = 100
        
    except Exception as e:
        job.status = 'failed'
        job.error_message = str(e)
        job.end_time = datetime.now()
        print(f"❌ Erreur compression {job.id}: {e}")

def simulate_compression_progress(job):
    """Simulation de progression pour la visualisation"""
    if job.status != 'running':
        return
    
    # Simuler la progression
    duration = get_compression_duration(job.mode, job.original_size)
    start_time = time.time()
    
    while job.status == 'running' and job.progress < 100:
        elapsed = time.time() - start_time
        progress = min((elapsed / duration) * 100, 100)
        
        job.progress = progress
        job.speed = calculate_speed(job, elapsed * 1000)
        job.current_ratio = calculate_current_ratio(progress, job.mode)
        
        time.sleep(0.1)  # Update every 100ms

def get_compression_duration(mode, file_size):
    """Calcule la durée de compression estimée"""
    base_durations = {
        'ultra_fast': 0.5,
        'balanced': 2.0,
        'max_quality': 5.0,
        'quantum': 8.0
    }
    
    base_duration = base_durations.get(mode, 2.0)
    size_factor = min(file_size / (1024 * 1024), 10)  # Max 10x for large files
    
    return base_duration * (1 + size_factor * 0.1)

def calculate_speed(job, elapsed_ms):
    """Calcule la vitesse de compression"""
    if elapsed_ms == 0:
        return 0
    
    processed_bytes = (job.original_size * job.progress) / 100
    speed_mbs = (processed_bytes / (1024 * 1024)) / (elapsed_ms / 1000)
    return round(speed_mbs, 2)

def calculate_current_ratio(progress, mode):
    """Calcule le ratio de compression actuel"""
    max_ratios = {
        'ultra_fast': 100,
        'balanced': 300,
        'max_quality': 500,
        'quantum': 1000
    }
    
    max_ratio = max_ratios.get(mode, 300)
    return round((max_ratio * progress / 100), 1)

# Routes API
@app.route('/api/compress', methods=['POST'])
def start_compression():
    """Démarre une compression"""
    try:
        if not license_active:
            return jsonify({'error': 'Licence non active'}), 401
        
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nom de fichier vide'}), 400
        
        # Sauvegarder le fichier
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Récupérer les paramètres
        mode = request.form.get('mode', 'balanced')
        security_level = request.form.get('security_level', 'quantum_harmonic')
        options = {
            'integrity_check': request.form.get('integrity_check', 'true').lower() == 'true',
            'parallel_processing': request.form.get('parallel_processing', 'true').lower() == 'true',
            'auto_optimize': request.form.get('auto_optimize', 'false').lower() == 'true',
            'video_preview': request.form.get('video_preview', 'true').lower() == 'true'
        }
        
        # Créer le job
        job_id = str(uuid.uuid4())
        job = CompressionJob(job_id, file_path, mode, security_level, options)
        compression_jobs[job_id] = job
        
        # Démarrer la compression en arrière-plan
        threading.Thread(target=compress_file_real, args=(job,), daemon=True).start()
        threading.Thread(target=simulate_compression_progress, args=(job,), daemon=True).start()
        
        return jsonify({
            'job_id': job_id,
            'status': 'started',
            'message': 'Compression démarrée'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<job_id>', methods=['GET'])
def get_compression_status(job_id):
    """Récupère le statut d'une compression"""
    if job_id not in compression_jobs:
        return jsonify({'error': 'Job non trouvé'}), 404
    
    job = compression_jobs[job_id]
    return jsonify(job.to_dict())

@app.route('/api/results/<job_id>', methods=['GET'])
def get_compression_results(job_id):
    """Récupère les résultats d'une compression"""
    if job_id not in compression_jobs:
        return jsonify({'error': 'Job non trouvé'}), 404
    
    job = compression_jobs[job_id]
    
    if job.status != 'completed':
        return jsonify({'error': 'Compression non terminée'}), 400
    
    # Retourner le fichier compressé
    if job.output_path and os.path.exists(job.output_path):
        return send_file(job.output_path, as_attachment=True, download_name=os.path.basename(job.output_path))
    else:
        return jsonify({'error': 'Fichier de sortie non trouvé'}), 404

@app.route('/api/license', methods=['POST'])
def activate_license():
    """Active une licence"""
    try:
        license_key = request.json.get('license_key')
        
        if not license_key:
            return jsonify({'error': 'Clé de licence requise'}), 400
        
        # Initialiser le package avec la nouvelle licence
        if package_instance and package_instance.initialize(license_key):
            license_active = True
            return jsonify({
                'status': 'activated',
                'message': 'Licence activée avec succès'
            })
        else:
            return jsonify({'error': 'Licence invalide'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Récupère les statistiques globales"""
    total_jobs = len(compression_jobs)
    running_jobs = len([j for j in compression_jobs.values() if j.status == 'running'])
    completed_jobs = len([j for j in compression_jobs.values() if j.status == 'completed'])
    
    # Calculer le ratio moyen
    completed_with_ratio = [j for j in compression_jobs.values() if j.status == 'completed' and j.compression_ratio]
    avg_ratio = sum(j.compression_ratio for j in completed_with_ratio) / len(completed_with_ratio) if completed_with_ratio else 0
    
    return jsonify({
        'total_jobs': total_jobs,
        'running_jobs': running_jobs,
        'completed_jobs': completed_jobs,
        'avg_compression_ratio': round(avg_ratio, 1),
        'license_active': license_active,
        'package_info': package_instance.get_package_info() if package_instance else None
    })

@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """Liste tous les jobs"""
    jobs_list = [job.to_dict() for job in compression_jobs.values()]
    return jsonify(jobs_list)

@app.route('/api/jobs/<job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Supprime un job"""
    if job_id not in compression_jobs:
        return jsonify({'error': 'Job non trouvé'}), 404
    
    job = compression_jobs[job_id]
    
    # Supprimer les fichiers
    try:
        if os.path.exists(job.file_path):
            os.remove(job.file_path)
        if job.output_path and os.path.exists(job.output_path):
            os.remove(job.output_path)
    except Exception as e:
        print(f"⚠️ Erreur suppression fichiers: {e}")
    
    # Supprimer le job
    del compression_jobs[job_id]
    
    return jsonify({'message': 'Job supprimé avec succès'})

@app.route('/api/health', methods=['GET'])
def health_check():
    """Vérifie l'état de l'API"""
    return jsonify({
        'status': 'healthy',
        'license_active': license_active,
        'package_loaded': package_instance is not None,
        'active_jobs': len([j for j in compression_jobs.values() if j.status == 'running'])
    })

# Route principale pour tester
@app.route('/')
def index():
    """Page de test de l'API"""
    return jsonify({
        'message': 'HCV PRO Compression API',
        'version': '1.0.0',
        'endpoints': [
            'POST /api/compress - Démarrer une compression',
            'GET /api/status/<id> - Statut d\'une compression',
            'GET /api/results/<id> - Télécharger les résultats',
            'POST /api/license - Activer une licence',
            'GET /api/stats - Statistiques globales',
            'GET /api/jobs - Lister tous les jobs',
            'DELETE /api/jobs/<id> - Supprimer un job',
            'GET /api/health - Vérifier l\'état'
        ]
    })

if __name__ == '__main__':
    print("🚀 Démarrage de l'API HCV PRO...")
    
    # Initialiser le package
    if initialize_package():
        print("✅ API prête !")
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        print("❌ Échec démarrage API")
        sys.exit(1)
