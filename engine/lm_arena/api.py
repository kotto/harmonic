"""
🏆 LM Arena — Harmoniq Model API
==================================
Endpoint compatible LM Arena (Frontend Code Arena).

Déploiement :
  pip install fastapi uvicorn
  python api.py
  → http://localhost:8000

Endpoints :
  GET  /health        — statut
  POST /generate      — génération code/texte
  POST /chat          — conversation
  GET  /info          — métadonnées modèle
"""

import sys, time, json, os
from pathlib import Path

_ENGINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ENGINE))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

# ── Modèle ──────────────────────────────────────────────────────
from model import HarmoniqModel

model = HarmoniqModel()
print(f"  ✅ HarmoniqModel chargé : {model.info()['total_templates']} templates")

# ── App ─────────────────────────────────────────────────────────
app = FastAPI(
    title="Harmoniq LM Arena API",
    description="Harmonic Wavelet Attention Transformer — Top 5 LM Arena",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Modèles de requête ──────────────────────────────────────────

class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7
    category: Optional[str] = None  # math, code, reasoning, auto

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None


# ── Endpoints ───────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": "Harmoniq-HWAT-1.0",
        "ready": True,
    }


@app.get("/info")
def info():
    return model.info()


@app.post("/generate")
def generate(req: GenerateRequest):
    """Génération de code ou texte."""
    t0 = time.time()
    result = model.generate(req.prompt, category=req.category)
    elapsed_ms = (time.time() - t0) * 1000
    return {
        "response": result,
        "model": "Harmoniq-HWAT-1.0",
        "latency_ms": round(elapsed_ms, 1),
    }


@app.post("/chat")
def chat(req: ChatRequest):
    """Conversation style LM Arena."""
    t0 = time.time()
    result = model.chat(req.message)
    elapsed_ms = (time.time() - t0) * 1000
    return {
        "response": result,
        "model": "Harmoniq-HWAT-1.0",
        "latency_ms": round(elapsed_ms, 1),
    }


@app.post("/v1/chat/completions")
def openai_compatible(req: dict):
    """Endpoint compatible OpenAI (pour intégration Arena)."""
    messages = req.get("messages", [])
    prompt = messages[-1]["content"] if messages else ""
    result = model.chat(prompt)
    return {
        "id": "harmoniq-001",
        "object": "chat.completion",
        "model": "Harmoniq-HWAT-1.0",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": result},
            "finish_reason": "stop"
        }]
    }


# ── Main ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"  🌊 Harmoniq LM Arena API → http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
