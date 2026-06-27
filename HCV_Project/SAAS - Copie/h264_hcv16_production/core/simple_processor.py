#!/usr/bin/env python3
"""
Simple Production Processor
Version simplifiée du processeur production sans dépendances complexes
"""

import os
import sys
import time
import json
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import queue
import hashlib

@dataclass
class ProcessingJob:
    """Job de traitement H.264 → HCV16"""
    job_id: str
    input_file: str
    output_file: str
    priority: int = 5
    metadata: Dict = None
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ProcessingResult:
    """Résultat de traitement"""
    job_id: str
    success: bool
    original_size: int
    compressed_size: int
    compression_ratio: float
    processing_time: float
    error_message: str = None
    quality_metrics: Dict = None

class SimpleProductionProcessor:
    """Processeur production H.264 → HCV16 simplifié"""
    
    def __init__(self, config_file: str = "processor_config.json"):
        """Initialisation processeur"""
        self.config = self._load_config(config_file)
        self.job_queue = queue.PriorityQueue()
        self.result_queue = queue.Queue()
        self.active_jobs = {}
        self.stats = {
            'jobs_processed': 0,
            'total_savings_mb': 0,
            'avg_compression_ratio': 0,
            'processing_start_time': time.time()
        }
        
        self.max_workers = self.config.get('max_workers', multiprocessing.cpu_count())
        self.executor = None
        self.running = False
        
        print(f"Processeur initialisé avec {self.max_workers} workers")
    
    def _load_config(self, config_file: str) -> Dict:
        """Chargement configuration"""
        default_config = {
            'max_workers': multiprocessing.cpu_count(),
            'batch_size': 10,
            'temp_directory': '/tmp/h264_hcv16_processing',
            'output_quality': 95,
            'monitoring_interval': 30,
            'max_file_size_mb': 5000,
            'supported_formats': ['.mp4', '.avi', '.mkv', '.mov']
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
                print(f"Configuration chargée depuis {config_file}")
            except Exception as e:
                print(f"Erreur chargement config: {e}, utilisation config par défaut")
        
        # Création répertoire temporaire
        os.makedirs(default_config['temp_directory'], exist_ok=True)
        
        return default_config
    
    def start(self):
        """Démarrage du processeur"""
        if self.running:
            print("Processeur déjà en cours d'exécution")
            return
        
        self.running = True
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Démarrage thread principal de traitement
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        
        print("Processeur production démarré")
    
    def stop(self):
        """Arrêt du processeur"""
        if not self.running:
            return
        
        self.running = False
        
        if self.executor:
            self.executor.shutdown(wait=True)
        
        print("Processeur production arrêté")
    
    def submit_job(self, input_file: str, output_file: str, 
                   priority: int = 5, metadata: Dict = None) -> str:
        """Soumission job de traitement"""
        # Validation fichier d'entrée
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Fichier non trouvé: {input_file}")
        
        # Vérification format supporté
        file_ext = Path(input_file).suffix.lower()
        if file_ext not in self.config['supported_formats']:
            raise ValueError(f"Format non supporté: {file_ext}")
        
        # Vérification taille fichier
        file_size_mb = os.path.getsize(input_file) / (1024 * 1024)
        if file_size_mb > self.config['max_file_size_mb']:
            raise ValueError(f"Fichier trop volumineux: {file_size_mb:.1f}MB")
        
        # Génération job_id unique
        job_id = self._generate_job_id(input_file)
        
        # Création job
        job = ProcessingJob(
            job_id=job_id,
            input_file=input_file,
            output_file=output_file,
            priority=priority,
            metadata=metadata or {}
        )
        
        # Ajout à la queue
        self.job_queue.put((priority, time.time(), job))
        
        print(f"Job soumis: {job_id} ({file_size_mb:.1f}MB)")
        return job_id
    
    def get_job_status(self, job_id: str) -> Dict:
        """Récupération statut d'un job"""
        if job_id in self.active_jobs:
            return {
                'status': 'processing',
                'job_id': job_id,
                'started_at': self.active_jobs[job_id]['started_at']
            }
        
        # Vérifier dans les résultats
        try:
            while True:
                result = self.result_queue.get_nowait()
                if result.job_id == job_id:
                    return {
                        'status': 'completed' if result.success else 'failed',
                        'job_id': job_id,
                        'result': result
                    }
                # Remettre le résultat dans la queue
                self.result_queue.put(result)
        except queue.Empty:
            pass
        
        return {'status': 'not_found', 'job_id': job_id}
    
    def get_statistics(self) -> Dict:
        """Récupération statistiques globales"""
        uptime = time.time() - self.stats['processing_start_time']
        
        return {
            'uptime_seconds': uptime,
            'jobs_processed': self.stats['jobs_processed'],
            'jobs_in_queue': self.job_queue.qsize(),
            'active_jobs': len(self.active_jobs),
            'total_savings_mb': self.stats['total_savings_mb'],
            'avg_compression_ratio': self.stats['avg_compression_ratio'],
            'throughput_jobs_per_hour': (self.stats['jobs_processed'] / (uptime / 3600)) if uptime > 0 else 0
        }
    
    def _generate_job_id(self, input_file: str) -> str:
        """Génération ID unique pour job"""
        timestamp = str(time.time())
        file_hash = hashlib.md5(input_file.encode()).hexdigest()[:8]
        return f"h264_hcv16_{timestamp}_{file_hash}"
    
    def _processing_loop(self):
        """Boucle principale de traitement"""
        print("Boucle de traitement démarrée")
        
        while self.running:
            try:
                # Récupération job avec timeout
                try:
                    priority, timestamp, job = self.job_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Soumission job au pool de threads
                future = self.executor.submit(self._process_job, job)
                
                # Tracking job actif
                self.active_jobs[job.job_id] = {
                    'job': job,
                    'future': future,
                    'started_at': time.time()
                }
                
                # Nettoyage jobs terminés
                self._cleanup_completed_jobs()
                
            except Exception as e:
                print(f"Erreur dans boucle de traitement: {e}")
        
        print("Boucle de traitement arrêtée")
    
    def _process_job(self, job: ProcessingJob) -> ProcessingResult:
        """Traitement d'un job individuel (simulation)"""
        start_time = time.time()
        
        try:
            print(f"Début traitement job {job.job_id}")
            
            # Simulation traitement
            time.sleep(1)  # Simulation temps de traitement
            
            # Calcul tailles simulées
            original_size = os.path.getsize(job.input_file)
            compression_ratio = 1.05 + (hash(job.job_id) % 20) / 100  # Ratio simulé 1.05-1.25
            compressed_size = int(original_size / compression_ratio)
            
            processing_time = time.time() - start_time
            
            # Création fichier de sortie simulé
            with open(job.output_file, 'wb') as f:
                f.write(b'simulated_hcv16_data' * (compressed_size // 20))
            
            # Mise à jour statistiques
            self._update_statistics(original_size, compressed_size, compression_ratio)
            
            result = ProcessingResult(
                job_id=job.job_id,
                success=True,
                original_size=original_size,
                compressed_size=compressed_size,
                compression_ratio=compression_ratio,
                processing_time=processing_time
            )
            
            print(f"Job {job.job_id} terminé: {compression_ratio:.3f}× en {processing_time:.1f}s")
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            result = ProcessingResult(
                job_id=job.job_id,
                success=False,
                original_size=0,
                compressed_size=0,
                compression_ratio=0,
                processing_time=processing_time,
                error_message=str(e)
            )
            
            print(f"Erreur job {job.job_id}: {e}")
        
        # Ajout résultat à la queue
        self.result_queue.put(result)
        
        return result
    
    def _update_statistics(self, original_size: int, compressed_size: int, 
                          compression_ratio: float):
        """Mise à jour statistiques globales"""
        self.stats['jobs_processed'] += 1
        
        savings_mb = (original_size - compressed_size) / (1024 * 1024)
        self.stats['total_savings_mb'] += savings_mb
        
        # Moyenne mobile du ratio de compression
        n = self.stats['jobs_processed']
        current_avg = self.stats['avg_compression_ratio']
        self.stats['avg_compression_ratio'] = ((current_avg * (n - 1)) + compression_ratio) / n
    
    def _cleanup_completed_jobs(self):
        """Nettoyage jobs terminés"""
        completed_jobs = []
        
        for job_id, job_info in self.active_jobs.items():
            if job_info['future'].done():
                completed_jobs.append(job_id)
        
        for job_id in completed_jobs:
            del self.active_jobs[job_id]

def create_default_config():
    """Création fichier configuration par défaut"""
    config = {
        "max_workers": multiprocessing.cpu_count(),
        "batch_size": 10,
        "temp_directory": "/tmp/h264_hcv16_processing",
        "output_quality": 95,
        "monitoring_interval": 30,
        "max_file_size_mb": 5000,
        "supported_formats": [".mp4", ".avi", ".mkv", ".mov"]
    }
    
    with open("processor_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("Configuration par défaut créée: processor_config.json")

if __name__ == "__main__":
    # Exemple d'utilisation
    print("🚀 Processeur Production H.264 → HCV16 (Simplifié)")
    print("="*50)
    
    # Création config par défaut si nécessaire
    if not os.path.exists("processor_config.json"):
        create_default_config()
    
    # Initialisation processeur
    processor = SimpleProductionProcessor()
    
    try:
        # Démarrage
        processor.start()
        
        # Exemple soumission job
        if len(sys.argv) > 1:
            input_file = sys.argv[1]
            output_file = sys.argv[2] if len(sys.argv) > 2 else f"{Path(input_file).stem}.hcv16"
            
            job_id = processor.submit_job(input_file, output_file)
            print(f"Job soumis: {job_id}")
            
            # Attente completion
            while True:
                status = processor.get_job_status(job_id)
                print(f"Statut: {status['status']}")
                
                if status['status'] in ['completed', 'failed']:
                    if status['status'] == 'completed':
                        result = status['result']
                        print(f"✅ Succès: {result.compression_ratio:.3f}× en {result.processing_time:.1f}s")
                    else:
                        print(f"❌ Échec: {status.get('error', 'Erreur inconnue')}")
                    break
                
                time.sleep(2)
        else:
            print("Usage: python simple_processor.py <input_file> [output_file]")
            print("Processeur en attente de jobs...")
            
            # Maintien en vie pour démonstration
            try:
                while True:
                    stats = processor.get_statistics()
                    print(f"Stats: {stats['jobs_processed']} jobs traités")
                    time.sleep(10)
            except KeyboardInterrupt:
                print("\nArrêt demandé...")
    
    finally:
        processor.stop()
        print("Processeur arrêté")