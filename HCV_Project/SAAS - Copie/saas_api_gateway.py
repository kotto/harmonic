#!/usr/bin/env python3
"""
API Gateway SAAS Harmonic Studio
Gestion utilisateurs, authentification, crédits, API publique
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import jwt
import time
import uuid
import os
from datetime import datetime, timedelta
from saas_queue_worker import queue, GenerationJob, JobStatus

app = FastAPI(title="Harmonic Studio SAAS API")

security = HTTPBearer()

# Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'harmonic-studio-super-secret-key-2026')
CREDITS_PER_MINUTE = 1.0

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    prompt: str
    duration: float
    camera: str = "fixed"

class User:
    def __init__(self, user_id: str, email: str, credits: float = 10.0):
        self.user_id = user_id
        self.email = email
        self.credits = credits
        self.created_at = time.time()
        self.api_key = str(uuid.uuid4())
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "email": self.email,
            "credits": self.credits,
            "api_key": self.api_key
        }

# Base de données temporaire (à remplacer par PostgreSQL)
users = {}
api_keys = {}

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    api_key = credentials.credentials
    
    if api_key not in api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide"
        )
    
    user_id = api_keys[api_key]
    return users[user_id]

@app.post("/api/v1/generate")
async def generate_video(request: GenerateRequest, user: User = Depends(get_current_user)):
    """Soumet une demande de génération vidéo"""
    
    # Vérification crédits suffisants
    required_credits = request.duration * CREDITS_PER_MINUTE / 60
    
    if user.credits < required_credits:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Crédits insuffisants. Besoin de {required_credits:.2f} crédits, disponible: {user.credits:.2f}"
        )
    
    # Débit crédits immédiatement
    user.credits -= required_credits
    
    # Soumet le travail à la queue
    job_id = queue.submit_job(
        user_id = user.user_id,
        prompt = request.prompt,
        duration = request.duration,
        camera = request.camera
    )
    
    return {
        "job_id": job_id,
        "status": JobStatus.PENDING,
        "credits_used": required_credits,
        "credits_remaining": user.credits,
        "estimated_time": request.duration * 1.2
    }

@app.get("/api/v1/status/{job_id}")
async def get_job_status(job_id: str, user: User = Depends(get_current_user)):
    """Récupère le statut d'un travail"""
    job = queue.get_job_status(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Travail non trouvé")
    
    if job['user_id'] != user.user_id:
        raise HTTPException(status_code=403, detail="Accès interdit")
    
    return job

@app.get("/api/v1/user/profile")
async def get_user_profile(user: User = Depends(get_current_user)):
    """Profil utilisateur et crédits restants"""
    return {
        "user_id": user.user_id,
        "email": user.email,
        "credits": user.credits
    }

@app.post("/api/v1/auth/create_user")
async def create_user(email: str):
    """Crée un nouvel utilisateur"""
    user_id = str(uuid.uuid4())
    user = User(user_id, email)
    
    users[user_id] = user
    api_keys[user.api_key] = user_id
    
    return {
        "user_id": user_id,
        "api_key": user.api_key,
        "credits": 10.0
    }

def run_gateway():
    print("\n🌐 Démarrage API Gateway Harmonic Studio SAAS")
    print("✅ API disponible sur http://localhost:8000")
    print("✅ Documentation Swagger sur http://localhost:8000/docs")
    
    # Créer un utilisateur test par défaut
    test_user = User("demo_user", "demo@harmonic.studio", credits=100.0)
    users[test_user.user_id] = test_user
    api_keys[test_user.api_key] = test_user.user_id
    
    print(f"\n✅ Utilisateur Demo créé:")
    print(f"   API KEY: {test_user.api_key}")
    print(f"   Crédits: {test_user.credits}")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    run_gateway()