#!/usr/bin/env python3
"""
LM Arena Submission Server — Harmonic AI
=========================================
Catégories : Mathématiques & Raisonnement

Architecture :
  - Moteur harmonique SOPC (déterministe, 0 hallucination) pour les maths
  - Fallback LLM externe pour les questions hors domaine
  - Routeur intelligent : confiance harmonique → fallback si nécessaire

Endpoints :
  GET  /health                          — Health check
  POST /generate                        — Génération de réponse
  POST /benchmark                       — Benchmark interne

Usage:
  python server.py --port 8000
"""

import sys
import os
import json
import time
import logging
import argparse
from typing import Dict, Any, Optional, List

# Ajout du chemin vers le moteur harmonique
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'projet', 'cerveau_harmonique_v1'))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from harmonic_math_engine import HarmonicMathEngine
from fallback_router import FallbackRouter
from response_refiner import ResponseRefiner
from harmonic_reasoner import HarmonicMultiStepReasoner

# =============================================================================
# CONFIGURATION
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger("lm-arena")

app = FastAPI(
    title="Harmonic AI — LM Arena Submission",
    description="Moteur harmonique SOPC pour mathématiques et raisonnement, avec fallback intelligent",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# MODÈLES DE DONNÉES
# =============================================================================

class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="Question ou prompt utilisateur")
    max_tokens: int = Field(512, ge=1, le=4096)
    temperature: float = Field(0.0, ge=0.0, le=2.0)
    top_p: float = Field(1.0, ge=0.0, le=1.0)
    category: Optional[str] = Field(None, description="Catégorie LM Arena (math, reasoning, etc.)")

class GenerateResponse(BaseModel):
    text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: str = Field(..., description="harmonic | fallback")
    time_ms: float
    metadata: Dict[str, Any] = {}

class HealthResponse(BaseModel):
    status: str
    version: str
    engine: str
    models_available: List[str]

class BenchmarkRequest(BaseModel):
    category: str = Field("math", description="math | reasoning | all")
    num_samples: int = Field(10, ge=1, le=100)

class BenchmarkResult(BaseModel):
    category: str
    num_samples: int
    accuracy: float
    avg_confidence: float
    avg_time_ms: float
    harmonic_ratio: float  # % traité par l'harmonique vs fallback
    details: List[Dict[str, Any]]

# =============================================================================
# INITIALISATION DES MOTEURS
# =============================================================================

logger.info("🔧 Initialisation du moteur harmonique...")
math_engine = HarmonicMathEngine()

logger.info("🔧 Initialisation du routeur de fallback...")
fallback_router = FallbackRouter()

logger.info("🔧 Initialisation du ResponseRefiner...")
response_refiner = ResponseRefiner()
logger.info(f"   Refiner enabled: {response_refiner.enabled}")

logger.info("🔧 Initialisation du HarmonicMultiStepReasoner...")
multi_step_reasoner = HarmonicMultiStepReasoner(math_engine)
logger.info(f"   Reasoner ready — 9 decomposition patterns, convergence by ABC")

logger.info("✅ Serveur LM Arena prêt")

# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Vérification de l'état du service."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        engine="Harmonic SOPC + Fallback",
        models_available=["harmonic-sopc", "fallback-deepseek"]
    )


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """
    Génère une réponse à un prompt.
    
    Stratégie :
    1. Analyse harmonique du prompt (signature 9D, cohérence)
    2. Si confiance >= seuil → réponse harmonique (déterministe, maths)
    3. Sinon → fallback LLM externe
    """
    t0 = time.time()
    
    try:
        # Étape 1 : Analyse harmonique
        analysis = math_engine.analyze(request.prompt)
        confidence = analysis.get("coherence", 0.0)
        domain = analysis.get("domain", "general")
        
        # Étape 2 : Pipeline de résolution
        if confidence >= math_engine.CONFIDENCE_THRESHOLD:
            # Réponse harmonique directe (trouvée dans la KB)
            result = math_engine.solve(request.prompt, analysis)
            source = "harmonic"
        else:
            # Étape 2a : Tentative de raisonnement multi-étapes
            multi_result = multi_step_reasoner.solve(request.prompt, analysis)
            multi_confidence = multi_result.get("confidence", 0.0)
            
            if multi_confidence >= math_engine.CONFIDENCE_THRESHOLD:
                # Résolu par décomposition harmonique
                result = multi_result
                source = "harmonic_multi_step"
                confidence = multi_confidence
                logger.info(f"🧩 Decomposed into {len(multi_result.get('steps', []))} sub-problems")
            else:
                # Fallback externe
                result = fallback_router.generate(
                    request.prompt, 
                    analysis=analysis,
                    max_tokens=request.max_tokens
                )
                source = "fallback"
        
        # Étape 2c : Refinement — reformuler pour fluidité humaine (sauf fallback)
        if source in ("harmonic", "harmonic_multi_step"):
            refined = response_refiner.refine(
                request.prompt, 
                result["text"], 
                domain=domain,
                force=True  # Toujours reformuler pour parler la langue des humains
            )
            if refined["refined"]:
                result["text"] = refined["text"]
                source = f"{source}_refined"
                logger.info(f"✨ Response refined for human fluency (domain={domain})")
            elif not response_refiner.enabled:
                source = f"{source}_raw"
                logger.info(f"📝 Response kept raw (refiner disabled)")
            else:
                source = f"{source}_raw"
                logger.warning(f"⚠️ Refinement failed — keeping original")
        
        # Re-vérification harmonique de la réponse fallback
        if source == "fallback":
            fallback_check = math_engine.analyze(result["text"])
            confidence = max(confidence, fallback_check.get("coherence", 0.0))
        
        time_ms = (time.time() - t0) * 1000
        
        return GenerateResponse(
            text=result["text"],
            confidence=round(confidence, 4),
            source=source,
            time_ms=round(time_ms, 2),
            metadata={
                "domain": domain,
                "harmonic_score": analysis.get("harmonic_score", 0.0),
                "euler_coherence": analysis.get("euler_coherence", 0.0),
                "resonance": analysis.get("resonance", 0.0),
            }
        )
    
    except Exception as e:
        logger.error(f"❌ Erreur génération: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/benchmark", response_model=BenchmarkResult)
async def benchmark(request: BenchmarkRequest):
    """
    Benchmark interne sur la catégorie spécifiée.
    """
    try:
        from benchmark_math import MathBenchmark
        bench = MathBenchmark(math_engine, fallback_router)
        result = bench.run(category=request.category, num_samples=request.num_samples)
        return BenchmarkResult(**result)
    except Exception as e:
        logger.error(f"❌ Erreur benchmark: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LM Arena Harmonic AI Server")
    parser.add_argument("--port", type=int, default=8000, help="Port du serveur")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host")
    args = parser.parse_args()
    
    logger.info(f"🚀 Démarrage sur {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")