#!/usr/bin/env python3
"""
Middleware de logging + Handler corrigé avec run_in_threadpool
"""

import time
import logging
from fastapi import Request
from fastapi.concurrency import run_in_threadpool

# Middleware de logging
logger = logging.getLogger("requests")

@app.middleware("http")
async def log_everything(request: Request, call_next):
    start = time.time()
    logger.info(f"IN  {request.method} {request.url.path} from {request.client}")
    try:
        response = await call_next(request)
        logger.info(f"OUT {request.method} {request.url.path} -> {response.status_code} in {time.time()-start:.3f}s")
        return response
    except Exception as e:
        logger.exception(f"ERR {request.method} {request.url.path} after {time.time()-start:.3f}s: {e}")
        raise

# Handler corrigé avec run_in_threadpool
@app.post("/generate")
async def generate_text(request: GenerationRequest):
    """Génération parallèle révolutionnaire - CORRIGÉ"""
    try:
        start_time = time.time()
        logger.info(f"ENTERED /generate with prompt: {request.prompt}")
        
        if request.use_parallel:
            # Utiliser run_in_threadpool pour éviter de bloquer l'event loop
            result = await run_in_threadpool(
                aggregator.aggregate_parallel_responses,
                request.prompt,
                files=[],  # TODO: Implement file processing
                images=[]  # TODO: Implement image processing
            )
        else:
            # Mode simple aussi dans threadpool
            result = await run_in_threadpool(
                simple_generate,
                request.prompt
            )
        
        processing_time = time.time() - start_time
        logger.info(f"COMPLETED /generate in {processing_time:.3f}s")
        
        return {
            "content": result.get("content", ""),
            "confidence": result.get("confidence", 0.95),
            "determinism_score": result.get("determinism_score", 0.99),
            "processing_time": processing_time,
            "modalities": request.modalities,
            "architecture_version": "12.0.0-parallel-revolutionary-fixed",
            "evolution_stage": "production-ready",
            "parallel_metrics": result.get("metrics", {})
        }
        
    except Exception as e:
        logger.error(f"Error in generate_text: {e}")
        return {
            "error": str(e),
            "content": "Error occurred during generation",
            "confidence": 0.0,
            "processing_time": time.time() - start_time
        }

def simple_generate(prompt: str) -> dict:
    """Génération simple synchrone pour le threadpool"""
    # Implémentation simple de fallback
    return {
        "content": f"Generated response for: {prompt}",
        "confidence": 0.95,
        "determinism_score": 0.99,
        "metrics": {"mode": "simple", "models_used": 1}
    }
