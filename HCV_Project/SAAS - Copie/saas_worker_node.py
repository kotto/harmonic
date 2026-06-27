#!/usr/bin/env python3
"""
Node Worker GPU SAAS Harmonic Studio
Exécute les travaux de génération vidéo sur les instances GPU
Se connecte à la queue centrale et traite les jobs
"""

import os
import time
import threading
import boto3
from saas_queue_worker import queue, JobStatus
from deepseek_continuous_movie_generator import ContinuousMovieGenerator, Scene
from deepseek_harmonic_patch import DeepseekHarmonicPatcher

S3_OUTPUT_BUCKET = "harmonic-studio-outputs"
s3 = boto3.client('s3')

class WorkerNode:
    def __init__(self):
        self.generator = None
        self.running = False
        
    def initialize_model(self):
        """Initialise Deepseek Harmonique une seule fois au démarrage"""
        print("\n🔧 Chargement modèle Deepseek Harmonique...")
        
        patcher = DeepseekHarmonicPatcher()
        model, tokenizer = patcher.load_model_from_s3()
        model = patcher.apply_harmonic_transformation(model)
        
        self.generator = ContinuousMovieGenerator(model, tokenizer)
        self.generator.start()
        
        print("✅ Modèle chargé et prêt")
    
    def process_job(self, job):
        """Traite un travail de génération"""
        try:
            print(f"\n▶️  Traitement job {job.job_id}")
            
            output_filename = f"{job.job_id}.mov"
            
            # Génération vidéo
            self.generator.generate_full_movie([
                Scene(
                    description=job.prompt,
                    duration=job.duration,
                    camera=job.camera
                )
            ], output_filename)
            
            # Upload sur S3
            print(f"📤 Upload sur S3: {output_filename}")
            s3.upload_file(output_filename, S3_OUTPUT_BUCKET, output_filename)
            
            # Génère URL signée valable 7 jours
            output_url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': S3_OUTPUT_BUCKET, 'Key': output_filename},
                ExpiresIn=604800
            )
            
            # Supprime le fichier local
            os.remove(output_filename)
            
            queue.complete_job(job.job_id, output_url)
            print(f"✅ Job {job.job_id} terminé avec succès")
            
        except Exception as e:
            queue.fail_job(job.job_id, str(e))
            print(f"❌ Job {job.job_id} échoué: {str(e)}")
    
    def run(self):
        """Boucle principale du worker"""
        self.running = True
        
        print("="*70)
        print("🌀 HARMONIC STUDIO SAAS - GPU WORKER NODE")
        print("="*70)
        
        # Initialise le modèle en arrière plan
        init_thread = threading.Thread(target=self.initialize_model, daemon=True)
        init_thread.start()
        
        # Attend que le modèle soit prêt et traite les jobs
        while self.running:
            if not self.generator:
                time.sleep(1)
                continue
            
            for job in queue.worker_loop():
                self.process_job(job)
    
    def stop(self):
        self.running = False
        self.generator.stop()
        queue.stop()
        print("\n✅ Worker arrêté")

if __name__ == "__main__":
    worker = WorkerNode()
    
    try:
        worker.run()
    except KeyboardInterrupt:
        worker.stop()