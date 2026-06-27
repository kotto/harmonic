#!/usr/bin/env python3
"""
🌊 TEST MODÈLE HARMONIQUE PUR
Seulement le modèle déterministe harmonique
"""

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from harmonic_response_generator_simple import HarmonicResponseGenerator

app = FastAPI(title="Harmonic Pur Test")

# Instance du modèle harmonique
harmonic = HarmonicResponseGenerator()

class GenerationRequest(BaseModel):
    prompt: str

class GenerationResponse(BaseModel):
    content: str
    determinism_score: float
    processing_time: float
    harmony_score: float
    elegance_factor: float

@app.post("/generate")
async def generate_text(request: GenerationRequest):
    """Génération harmonique pure"""
    result = harmonic.generate_response(request.prompt)
    
    return GenerationResponse(
        content=result['content'],
        determinism_score=result['determinism_level'],
        processing_time=result['processing_time'],
        harmony_score=result['harmony_score'],
        elegance_factor=result['elegance_factor']
    )

@app.get("/health")
async def health():
    return {"status": "healthy", "model": "harmonic_pure"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
