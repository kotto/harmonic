#!/usr/bin/env python3
"""
Production Processor
Processeur principal production pour recompression H.264 → HCV16
Version optimisée pour déploiement à grande échelle
"""

import os
import sys
import time
import json
import logging
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
from pathlib import Path
import queue
import hashlib

# Imports pour traitement vidéo
import cv2
import numpy as np

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

class ProductionProcessor:
    """Processeur production H.264 → HCV16 haute performance"""
    
    def __init__(self, config_file: str = "processor_config.json"):
        """
        Initialisation processeur production
        
        Args:
            config_file: Fichier configuration JSON
        """
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
        
        # Configuration threading
        self.max_workers = self.config.get('max_workers', multiprocessing.cpu_count())
        self.executor = None
        self.running = False
        
        # Monitoring
        self.performance_monitor = PerformanceMonitor()
        
        logger.info(f"Processeur initialisé avec {self.max_workers} workers")
    
    def _load_config(self, config_file: str) -> Dict:
        """Chargement configuration"""
        default_config = {
            'max_workers': multiprocessing.cpu_count(),
            'batch_size': 10,
            'temp_directory': '/tmp/h264_hcv16_processing',
            'output_quality': 95,
            'enable_gpu_acceleration': False,
            'monitoring_interval': 30,
            'max_file_size_mb': 5000,
            'supported_formats': ['.mp4', '.avi', '.mkv', '.mov'],
            'compression_strategies': {
                'auto': True,
                'decode': True,
                'bitstream': True,
                'hybrid': True
            }
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
                logger.info(f"Configuration chargée depuis {config_file}")
            except Exception as e:
                logger.warning(f"Erreur chargement config: {e}, utilisation config par défaut")
        
        # Création répertoire temporaire
        os.makedirs(default_config['temp_directory'], exist_ok=True)
        
        return default_config
    
    def start(self):
        """Démarrage du processeur"""
        if self.running:
            logger.warning("Processeur déjà en cours d'exécution")
            return
        
        self.running = True
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Démarrage thread principal de traitement
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        
        # Démarrage monitoring
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("Processeur production démarré")
    
    def stop(self):
        """Arrêt du processeur"""
        if not self.running:
            return
        
        self.running = False
        
        if self.executor:
            self.executor.shutdown(wait=True)
        
        logger.info("Processeur production arrêté")
    
    def submit_job(self, input_file: str, output_file: str, 
                   priority: int = 5, metadata: Dict = None) -> str:
        """
        Soumission job de traitement
        
        Args:
            input_file: Fichier H.264 d'entrée
            output_file: Fichier HCV16 de sortie
            priority: Priorité (1=haute, 10=basse)
            metadata: Métadonnées additionnelles
            
        Returns:
            job_id: Identifiant unique du job
        """
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
        
        # Ajout à la queue (priorité inversée pour PriorityQueue)
        self.job_queue.put((priority, time.time(), job))
        
        logger.info(f"Job soumis: {job_id} ({file_size_mb:.1f}MB)")
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
            'throughput_jobs_per_hour': (self.stats['jobs_processed'] / (uptime / 3600)) if uptime > 0 else 0,
            'performance_metrics': self.performance_monitor.get_metrics()
        }
    
    def _generate_job_id(self, input_file: str) -> str:
        """Génération ID unique pour job"""
        timestamp = str(time.time())
        file_hash = hashlib.md5(input_file.encode()).hexdigest()[:8]
        return f"h264_hcv16_{timestamp}_{file_hash}"
    
    def _processing_loop(self):
        """Boucle principale de traitement"""
        logger.info("Boucle de traitement démarrée")
        
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
                logger.error(f"Erreur dans boucle de traitement: {e}")
        
        logger.info("Boucle de traitement arrêtée")
    
    def _process_job(self, job: ProcessingJob) -> ProcessingResult:
        """
        Traitement d'un job individuel
        
        Args:
            job: Job à traiter
            
        Returns:
            ProcessingResult: Résultat du traitement
        """
        start_time = time.time()
        
        try:
            logger.info(f"Début traitement job {job.job_id}")
            
            # Import du recompresseur (lazy loading)
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'h264_hcv16_recompression', 'src'))
            from h264_recompressor import H264HCV16Recompressor
            
            # Initialisation recompresseur
            recompressor = H264HCV16Recompressor(
                temp_dir=os.path.join(self.config['temp_directory'], job.job_id)
            )
            
            # Recompression
            original_size, compressed_size, compression_ratio = recompressor.recompress(
                input_h264=job.input_file,
                output_hcv16=job.output_file,
                strategy="auto"
            )
            
            processing_time = time.time() - start_time
            
            # Calcul métriques qualité
            quality_metrics = self._calculate_quality_metrics(
                job.input_file, job.output_file, compression_ratio
            )
            
            # Mise à jour statistiques
            self._update_statistics(original_size, compressed_size, compression_ratio)
            
            result = ProcessingResult(
                job_id=job.job_id,
                success=True,
                original_size=original_size,
                compressed_size=compressed_size,
                compression_ratio=compression_ratio,
                processing_time=processing_time,
                quality_metrics=quality_metrics
            )
            
            logger.info(f"Job {job.job_id} terminé: {compression_ratio:.3f}× en {processing_time:.1f}s")
            
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
            
            logger.error(f"Erreur job {job.job_id}: {e}")
        
        # Ajout résultat à la queue
        self.result_queue.put(result)
        
        return result
    
    def _calculate_quality_metrics(self, input_file: str, output_file: str, 
                                 compression_ratio: float) -> Dict:
        """Calcul métriques de qualité"""
        try:
            # Métriques basiques
            input_size_mb = os.path.getsize(input_file) / (1024 * 1024)
            output_size_mb = os.path.getsize(output_file) / (1024 * 1024)
            savings_mb = input_size_mb - output_size_mb
            
            return {
                'input_size_mb': input_size_mb,
                'output_size_mb': output_size_mb,
                'savings_mb': savings_mb,
                'compression_ratio': compression_ratio,
                'savings_percent': ((compression_ratio - 1) * 100),
                'quality_score': min(100, compression_ratio * 50)  # Score approximatif
            }
            
        except Exception as e:
            logger.warning(f"Erreur calcul métriques qualité: {e}")
            return {'error': str(e)}
    
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
    
    def _monitoring_loop(self):
        """Boucle de monitoring performance"""
        logger.info("Monitoring démarré")
        
        while self.running:
            try:
                # Collecte métriques
                self.performance_monitor.collect_metrics()
                
                # Log statistiques périodiques
                if self.stats['jobs_processed'] > 0:
                    stats = self.get_statistics()
                    logger.info(
                        f"Stats: {stats['jobs_processed']} jobs, "
                        f"{stats['avg_compression_ratio']:.3f}× ratio moyen, "
                        f"{stats['total_savings_mb']:.1f}MB économisés"
                    )
                
                time.sleep(self.config['monitoring_interval'])
                
            except Exception as e:
                logger.error(f"Erreur monitoring: {e}")
        
        logger.info("Monitoring arrêté")

class PerformanceMonitor:
    """Moniteur de performance système"""
    
    def __init__(self):
        self.metrics_history = []
        self.max_history = 100
    
    def collect_metrics(self):
        """Collecte métriques système"""
        try:
            import psutil
            
            metrics = {
                'timestamp': time.time(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage_percent': psutil.disk_usage('/').percent,
                'load_average': os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0
            }
            
            self.metrics_history.append(metrics)
            
            # Limitation historique
            if len(self.metrics_history) > self.max_history:
                self.metrics_history.pop(0)
                
        except ImportError:
            # psutil non disponible
            pass
        except Exception as e:
            logger.warning(f"Erreur collecte métriques: {e}")
    
    def get_metrics(self) -> Dict:
        """Récupération métriques actuelles"""
        if not self.metrics_history:
            return {}
        
        latest = self.metrics_history[-1]
        
        # Calcul moyennes sur dernières mesures
        recent_metrics = self.metrics_history[-10:]
        
        avg_cpu = sum(m.get('cpu_percent', 0) for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.get('memory_percent', 0) for m in recent_metrics) / len(recent_metrics)
        
        return {
            'current_cpu_percent': latest.get('cpu_percent', 0),
            'current_memory_percent': latest.get('memory_percent', 0),
            'avg_cpu_percent': avg_cpu,
            'avg_memory_percent': avg_memory,
            'disk_usage_percent': latest.get('disk_usage_percent', 0),
            'load_average': latest.get('load_average', 0)
        }

class BatchProcessor:
    """Processeur batch pour traitement en lot"""
    
    def __init__(self, processor: ProductionProcessor):
        self.processor = processor
        self.batch_jobs = []
    
    def add_batch_job(self, input_directory: str, output_directory: str, 
                     file_pattern: str = "*.mp4", priority: int = 5):
        """
        Ajout job batch pour traitement répertoire
        
        Args:
            input_directory: Répertoire source
            output_directory: Répertoire destination
            file_pattern: Pattern fichiers à traiter
            priority: Priorité des jobs
        """
        from glob import glob
        
        # Création répertoire de sortie
        os.makedirs(output_directory, exist_ok=True)
        
        # Recherche fichiers correspondants
        search_pattern = os.path.join(input_directory, file_pattern)
        input_files = glob(search_pattern)
        
        batch_id = f"batch_{int(time.time())}"
        job_ids = []
        
        for input_file in input_files:
            # Génération nom fichier de sortie
            input_name = Path(input_file).stem
            output_file = os.path.join(output_directory, f"{input_name}.hcv16")
            
            # Soumission job individuel
            job_id = self.processor.submit_job(
                input_file=input_file,
                output_file=output_file,
                priority=priority,
                metadata={'batch_id': batch_id}
            )
            
            job_ids.append(job_id)
        
        batch_info = {
            'batch_id': batch_id,
            'job_ids': job_ids,
            'total_jobs': len(job_ids),
            'created_at': time.time()
        }
        
        self.batch_jobs.append(batch_info)
        
        logger.info(f"Batch {batch_id} créé avec {len(job_ids)} jobs")
        return batch_id
    
    def get_batch_status(self, batch_id: str) -> Dict:
        """Récupération statut batch"""
        batch_info = None
        for batch in self.batch_jobs:
            if batch['batch_id'] == batch_id:
                batch_info = batch
                break
        
        if not batch_info:
            return {'error': 'Batch non trouvé'}
        
        # Vérification statut de chaque job
        job_statuses = []
        completed_jobs = 0
        failed_jobs = 0
        
        for job_id in batch_info['job_ids']:
            status = self.processor.get_job_status(job_id)
            job_statuses.append(status)
            
            if status['status'] == 'completed':
                completed_jobs += 1
            elif status['status'] == 'failed':
                failed_jobs += 1
        
        progress_percent = (completed_jobs / batch_info['total_jobs']) * 100
        
        return {
            'batch_id': batch_id,
            'total_jobs': batch_info['total_jobs'],
            'completed_jobs': completed_jobs,
            'failed_jobs': failed_jobs,
            'progress_percent': progress_percent,
            'status': 'completed' if completed_jobs == batch_info['total_jobs'] else 'processing',
            'job_statuses': job_statuses
        }

def create_default_config():
    """Création fichier configuration par défaut"""
    config = {
        "max_workers": multiprocessing.cpu_count(),
        "batch_size": 10,
        "temp_directory": "/tmp/h264_hcv16_processing",
        "output_quality": 95,
        "enable_gpu_acceleration": False,
        "monitoring_interval": 30,
        "max_file_size_mb": 5000,
        "supported_formats": [".mp4", ".avi", ".mkv", ".mov"],
        "compression_strategies": {
            "auto": True,
            "decode": True,
            "bitstream": True,
            "hybrid": True
        },
        "logging": {
            "level": "INFO",
            "file": "h264_hcv16_processor.log",
            "max_size_mb": 100,
            "backup_count": 5
        }
    }
    
    with open("processor_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("Configuration par défaut créée: processor_config.json")

if __name__ == "__main__":
    # Exemple d'utilisation
    print("🚀 Processeur Production H.264 → HCV16")
    print("="*50)
    
    # Création config par défaut si nécessaire
    if not os.path.exists("processor_config.json"):
        create_default_config()
    
    # Initialisation processeur
    processor = ProductionProcessor()
    
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
            print("Usage: python processor.py <input_file> [output_file]")
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
