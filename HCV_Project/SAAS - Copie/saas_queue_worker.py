#!/usr/bin/env python3
"""
Système de Queue distribué SAAS Harmonic Studio
Gestion multi instances GPU, file d'attente, distribution de travail
"""

import os
import time
import json
import uuid
import threading
import redis
from dataclasses import dataclass, asdict
from typing import Optional, Generator
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class GenerationJob:
    job_id: str
    user_id: str
    prompt: str
    duration: float
    camera: str
    status: JobStatus
    progress: int
    created_at: float
    started_at: Optional[float]
    completed_at: Optional[float]
    output_url: Optional[str]
    error: Optional[str]

class JobQueue:
    def __init__(self):
        self.redis = redis.Redis(
            host=os.environ.get('REDIS_HOST', 'localhost'),
            port=int(os.environ.get('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True
        )
        
        self.worker_id = str(uuid.uuid4())
        self.running = False
        self.current_job = None
        
        print(f"✅ Queue Worker initialisé")
        print(f"✅ Worker ID: {self.worker_id}")
    
    def submit_job(self, user_id: str, prompt: str, duration: float, camera: str = "fixed") -> str:
        """Soumet un nouveau travail de génération"""
        job_id = str(uuid.uuid4())
        
        job = GenerationJob(
            job_id = job_id,
            user_id = user_id,
            prompt = prompt,
            duration = duration,
            camera = camera,
            status = JobStatus.PENDING,
            progress = 0,
            created_at = time.time(),
            started_at = None,
            completed_at = None,
            output_url = None,
            error = None
        )
        
        self.redis.hset(f"job:{job_id}", mapping=asdict(job))
        self.redis.lpush("jobs:pending", job_id)
        self.redis.hincrby(f"user:{user_id}", "jobs_submitted", 1)
        
        print(f"✅ Job soumis: {job_id}")
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[dict]:
        """Récupère le statut d'un travail"""
        job_data = self.redis.hgetall(f"job:{job_id}")
        return job_data if job_data else None
    
    def cancel_job(self, job_id: str) -> bool:
        """Annule un travail en attente"""
        status = self.redis.hget(f"job:{job_id}", "status")
        if status == JobStatus.PENDING:
            self.redis.hset(f"job:{job_id}", "status", JobStatus.CANCELLED)
            return True
        return False
    
    def worker_loop(self) -> Generator[GenerationJob, None, None]:
        """Boucle principale du worker, rend les jobs à traiter"""
        self.running = True
        
        print(f"\n🎬 Worker {self.worker_id} démarré en attente de travaux")
        
        while self.running:
            # Récupère un job depuis la file d'attente
            job_data = self.redis.brpop("jobs:pending", timeout=1)
            
            if not job_data:
                continue
                
            _, job_id = job_data
            
            # Marque le job comme démarré
            self.redis.hset(f"job:{job_id}", mapping={
                "status": JobStatus.RUNNING,
                "started_at": time.time(),
                "worker_id": self.worker_id
            })
            
            self.redis.hincrby("stats", "jobs_started", 1)
            
            job_dict = self.redis.hgetall(f"job:{job_id}")
            job = GenerationJob(**job_dict)
            self.current_job = job
            
            print(f"\n▶️  Démarrage job: {job_id}")
            print(f"   Utilisateur: {job.user_id}")
            print(f"   Durée: {job.duration}s")
            print(f"   Prompt: {job.prompt[:60]}...")
            
            yield job
            
            self.current_job = None
    
    def update_progress(self, job_id: str, progress: int):
        """Met à jour la progression d'un travail"""
        self.redis.hset(f"job:{job_id}", "progress", progress)
    
    def complete_job(self, job_id: str, output_url: str):
        """Marque un travail comme terminé"""
        self.redis.hset(f"job:{job_id}", mapping={
            "status": JobStatus.COMPLETED,
            "completed_at": time.time(),
            "output_url": output_url,
            "progress": 100
        })
        
        self.redis.hincrby("stats", "jobs_completed", 1)
        print(f"✅ Job terminé: {job_id}")
    
    def fail_job(self, job_id: str, error: str):
        """Marque un travail comme échoué"""
        self.redis.hset(f"job:{job_id}", mapping={
            "status": JobStatus.FAILED,
            "completed_at": time.time(),
            "error": error
        })
        
        self.redis.hincrby("stats", "jobs_failed", 1)
        print(f"❌ Job échoué: {job_id} | {error}")
    
    def stop(self):
        """Arrête le worker proprement"""
        self.running = False
        print("\n✅ Worker arrêté")

# Singleton global
queue = JobQueue()

if __name__ == "__main__":
    # Test du système de queue
    print("="*70)
    print("🌀 HARMONIC STUDIO SAAS - QUEUE SYSTEM")
    print("="*70)
    
    # Exemple soumission job
    test_job_id = queue.submit_job(
        user_id="test_user_001",
        prompt="Un coucher de soleil sur l'océan",
        duration=30.0,
        camera="drone"
    )
    
    print(f"\nTest Job ID: {test_job_id}")
    print("\n✅ Système de queue prêt")