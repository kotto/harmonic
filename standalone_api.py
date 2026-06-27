 t#!/usr/bin/env python3
"""Standalone Harmonic AI SaaS API server.
Provides endpoints for the frontend dashboard.
Usage: python standalone_api.py
Starts on port 9000."""
import json, os, uuid, time, logging
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("harmonic-api")

# Import du projecteur quantique creatif
try:
    from quantum_harmonic_creativity import QuantumCreativeIntegrator
    QUANTUM_AVAILABLE = True
    quantum_creative = QuantumCreativeIntegrator()
    logger.info("Projecteur quantique creatif initialise pour l'API.")
except ImportError:
    QUANTUM_AVAILABLE = False
    quantum_creative = None
    logger.warning("Module quantum_harmonic_creativity non disponible pour l'API.")

# Import du moteur harmonique
try:
    from harmonic_lm_arena_engine import HarmonicResonanceEngine
    harmonic_engine = HarmonicResonanceEngine()
    logger.info("Moteur harmonique initialise pour l'API.")
except ImportError:
    harmonic_engine = None
    logger.warning("Module harmonic_lm_arena_engine non disponible pour l'API.")

app = FastAPI(title="Harmonic AI SaaS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- In-memory storage ----
audio_jobs_db = []
video_jobs_db = []

# ---- Models ----
class ProcessingRequest(BaseModel):
    processing_mode: str = "hcs_clarity"
    duration_seconds: float = 60.0
    job_name: Optional[str] = "New Job"
    source_format: Optional[str] = "mp3_128"
    channels: Optional[int] = 2

class ChatRequest(BaseModel):
    prompt: str
    max_tokens: int = 2048  # Augmente pour LM Arena (reponses longues)
    temperature: float = 0.0  # Sera adaptee automatiquement par categorie

# ---- Health ----
@app.get("/health")
@app.get("/api/v1/chat/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Harmonic AI SaaS",
        "version": "1.0.0",
        "database": "connected (in-memory)"
    }

@app.get("/")
async def root():
    return {
        "message": "Harmonic AI SaaS API",
        "docs": "/docs",
        "health": "/health"
    }

# ---- Status (stats) ----
@app.get("/api/v1/chat/status")
async def get_status():
    audio_count = len(audio_jobs_db)
    video_count = len(video_jobs_db)
    return {
        "user_id": "demo_user",
        "timestamp": datetime.utcnow().isoformat(),
        "usage_metrics": {
            "total_audio_minutes": audio_count * 1,
            "total_video_minutes": video_count * 1,
            "usage_percent": min(audio_count * 5 + video_count * 10, 100),
            "plan": "Pro"
        },
        "recent_audio_jobs": [
            {"job_id": j["id"], "status": j["status"], "processing_mode": j["processing_mode"],
             "name": j["name"], "created_at": j["created_at"]}
            for j in audio_jobs_db[-5:]
        ],
        "recent_video_jobs": [
            {"job_id": j["id"], "status": j["status"], "processing_mode": j["processing_mode"],
             "name": j["name"], "created_at": j["created_at"]}
            for j in video_jobs_db[-5:]
        ],
        "service_status": {
            "deepseek_api": "healthy (AWS)",
            "audio_service": "healthy (local)",
            "video_service": "healthy (local)"
        }
    }

# ---- Chat / Generate ----
@app.post("/api/v1/chat/generate")
@app.post("/api/v1/generate")
async def generate_chat(req: ChatRequest):
    return {
        "success": True,
        "response": f"This is a demo response from Harmonic AI.\n\nYou asked: \"{req.prompt}\"\n\nThis is running in standalone mode. Connect the real DeepSeek backend at __EC2_IP__:8000 for full functionality.",
        "confidence": 0.99,
        "processing_time": 0.5,
        "response_id": str(uuid.uuid4()),
        "verified_mode": True,
        "citations": [],
        "user_id": "demo_user",
        "timestamp": datetime.utcnow().isoformat()
    }

# ---- Audio processing ----
@app.post("/api/v1/chat/audio/process")
async def process_audio(
    file: Optional[UploadFile] = File(None),
    processing_mode: str = Form("hcs_clarity"),
    duration_seconds: float = Form(60.0),
    job_name: Optional[str] = Form(None)
):
    job_id = str(uuid.uuid4())
    job = {
        "id": job_id,
        "job_id": job_id,
        "name": job_name or (file.filename if file else f"Audio Job #{len(audio_jobs_db)+1}"),
        "status": "pending",
        "processing_mode": processing_mode,
        "created_at": datetime.utcnow().isoformat(),
        "user_id": "demo_user",
        "processing_time_ms": None,
        "quality_improvement": None,
        "error_message": None
    }
    audio_jobs_db.append(job)
    logger.info(f"Audio job created: {job_id}")
    return {
        "success": True,
        "job_id": job_id,
        "status": "pending",
        "processing_mode": processing_mode,
        "estimated_processing_time": "2-5 minutes",
        "user_id": "demo_user",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/chat/audio/jobs")
async def get_audio_jobs():
    return audio_jobs_db

@app.get("/api/v1/chat/audio/jobs/{job_id}")
async def get_audio_job(job_id: str):
    for j in audio_jobs_db:
        if j["id"] == job_id or j.get("job_id") == job_id:
            return j
    raise HTTPException(404, "Audio job not found")

# ---- Video processing ----
@app.post("/api/v1/chat/video/process")
async def process_video(
    file: Optional[UploadFile] = File(None),
    processing_mode: str = Form("hcs_4k_clarity"),
    duration_seconds: float = Form(60.0),
    job_name: Optional[str] = Form(None)
):
    job_id = str(uuid.uuid4())
    job = {
        "id": job_id,
        "job_id": job_id,
        "name": job_name or (file.filename if file else f"Video Job #{len(video_jobs_db)+1}"),
        "status": "pending",
        "processing_mode": processing_mode,
        "created_at": datetime.utcnow().isoformat(),
        "user_id": "demo_user",
        "processing_time_ms": None,
        "quality_improvement": None,
        "error_message": None
    }
    video_jobs_db.append(job)
    logger.info(f"Video job created: {job_id}")
    return {
        "success": True,
        "job_id": job_id,
        "status": "pending",
        "processing_mode": processing_mode,
        "estimated_processing_time": "5-15 minutes",
        "user_id": "demo_user",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/chat/video/jobs")
async def get_video_jobs():
    return video_jobs_db

@app.get("/api/v1/chat/video/jobs/{job_id}")
async def get_video_job(job_id: str):
    for j in video_jobs_db:
        if j["id"] == job_id or j.get("job_id") == job_id:
            return j
    raise HTTPException(404, "Video job not found")

# ---- Generate (non-chat) ----
@app.post("/api/v1/generate")
async def generate_text(req: ChatRequest):
    return await generate_chat(req)

# ---- Quantum Creative Generation (Phase 3) ----
class QuantumCreativeRequest(BaseModel):
    prompt: str
    count: int = 1
    deterministic_seed: Optional[str] = None

@app.post("/api/v1/quantum/creative")
async def quantum_creative_generate(req: QuantumCreativeRequest):
    """Genere du texte creatif via projection quantique harmonique."""
    if not QUANTUM_AVAILABLE or quantum_creative is None:
        raise HTTPException(503, "Projection quantique non disponible")
    
    start_time = time.time()
    
    if req.count > 1:
        results = quantum_creative.generate_multiple(req.prompt, count=min(req.count, 10))
    else:
        results = [quantum_creative.generate_creative(req.prompt, deterministic_seed=req.deterministic_seed)]
    
    processing_time = (time.time() - start_time) * 1000
    
    return {
        "success": True,
        "prompt": req.prompt,
        "generations": [
            {
                "text": r.generated_text,
                "style": r.creative_style,
                "metaphor": r.metaphor,
                "novelty_score": round(r.novelty_score, 4),
                "harmonic_resonance": round(r.harmonic_resonance, 4),
                "quantum_entropy": round(r.quantum_entropy, 4),
                "processing_time_ms": round(r.processing_time_ms, 2)
            }
            for r in results
        ],
        "count": len(results),
        "total_processing_time_ms": round(processing_time, 2),
        "quantum_available": True,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/quantum/stats")
async def quantum_creative_stats():
    """Statistiques du projecteur quantique creatif."""
    if not QUANTUM_AVAILABLE or quantum_creative is None:
        raise HTTPException(503, "Projection quantique non disponible")
    return {
        "success": True,
        "stats": quantum_creative.get_stats(),
        "timestamp": datetime.utcnow().isoformat()
    }

# ---- Harmonic Engine (Phase 1 & 2) ----
class HarmonicProcessRequest(BaseModel):
    prompt: str

@app.post("/api/v1/harmonic/process")
async def harmonic_process(req: HarmonicProcessRequest):
    """Traite un prompt via le moteur de resonance harmonique."""
    if harmonic_engine is None:
        raise HTTPException(503, "Moteur harmonique non disponible")
    
    start_time = time.time()
    result = harmonic_engine.process(req.prompt)
    processing_time = (time.time() - start_time) * 1000
    
    return {
        "success": True,
        "prompt": req.prompt,
        "matched": result.matched,
        "pattern_id": result.pattern_id,
        "pattern_name": result.pattern_name,
        "category": result.category,
        "resonance_score": round(result.resonance_score, 4),
        "k_factor": round(result.k_factor, 4),
        "response": result.response,
        "processing_time_ms": round(result.processing_time_ms, 2),
        "cache_hit": result.cache_hit,
        "harmonic_signature": result.harmonic_signature.to_dict(),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/harmonic/stats")
async def harmonic_engine_stats():
    """Statistiques du moteur harmonique."""
    if harmonic_engine is None:
        raise HTTPException(503, "Moteur harmonique non disponible")
    return {
        "success": True,
        "stats": harmonic_engine.get_stats(),
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("  Harmonic AI SaaS - Standalone API Server")
    print("=" * 60)
    print(f"  Frontend: lm_arena_package/frontend/index.html")
    print(f"  API:      http://localhost:9000")
    print(f"  Docs:     http://localhost:9000/docs")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=9000)