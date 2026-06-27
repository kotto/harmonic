"""
API locale de démonstration pour Harmonic AI
Fonctionne sans connexion internet stable
"""

from fastapi import FastAPI
from pydantic import BaseModel
import json
import time
from datetime import datetime
import hashlib
import uuid

app = FastAPI(
    title="Harmonic AI Local Demo API",
    description="API de démonstration locale pour développement avec connexion instable",
    version="1.0.0-local"
)

class GenerationRequest(BaseModel):
    prompt: str
    max_tokens: int = 100
    temperature: float = 0.0
    verified_mode: bool = False
    sources: list = []

class HealthResponse(BaseModel):
    status: str
    mode: str
    timestamp: str
    version: str

# Cache simple pour simuler le déterminisme
response_cache = {}

def generate_response_id(prompt: str, params: dict) -> str:
    """Générer un ID de réponse déterministe"""
    content = f"{prompt}:{json.dumps(params, sort_keys=True)}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]

def create_demo_response(prompt: str, max_tokens: int, verified_mode: bool = False, sources: list = None) -> dict:
    """Créer une réponse de démonstration réaliste"""
    
    if sources is None:
        sources = []
    
    # Types de réponses selon le prompt
    prompt_lower = prompt.lower()
    
    if "math" in prompt_lower or "+" in prompt or "=" in prompt:
        # Réponse mathématique
        response_text = "La réponse est 4. Ce calcul suit les règles arithmétiques standard."
        response_type = "math"
    elif "code" in prompt_lower or "python" in prompt_lower or "print" in prompt_lower:
        # Réponse de code
        response_text = "```python\nprint('Hello, Harmonic AI!')\n```\nCe code affiche un message de bienvenue."
        response_type = "code"
    elif "?" in prompt or "explain" in prompt_lower or "what" in prompt_lower:
        # Réponse explicative
        response_text = "Harmonic AI est une intelligence artificielle déterministe qui garantit 100% de reproductibilité et zéro hallucination grâce à des transformations mathématiques harmoniques."
        response_type = "explanation"
    else:
        # Réponse générale
        response_text = f"Je comprends votre requête: '{prompt[:50]}...'. Harmonic AI fournit des réponses fiables et vérifiables grâce à son architecture déterministe unique."
        response_type = "general"
    
    # Générer un ID de réponse
    params = {"max_tokens": max_tokens, "temperature": 0.0, "verified_mode": verified_mode}
    response_id = generate_response_id(prompt, params)
    
    # Ajouter des citations si en mode vérifié
    verified_sources = []
    if verified_mode:
        if sources:
            verified_sources = sources[:3]  # Limiter à 3 sources
        else:
            verified_sources = ["Harmonic AI Documentation v2.0", "Internal Knowledge Base"]
    
    return {
        "text": response_text,
        "tokens_generated": min(max_tokens, 150),
        "deterministic": True,
        "response_id": response_id,
        "model": "Qwen3.5-9B-DeepSeek-V4-Flash-BF16.gguf (local demo)",
        "type": response_type,
        "timestamp": datetime.now().isoformat(),
        "harmonic_transform": True,
        "zero_hallucination": True,
        "verified_mode": verified_mode,
        "citations": verified_sources
    }

@app.post("/generate", response_model=dict)
async def generate(request: GenerationRequest):
    """
    Endpoint de génération de texte
    Simule l'API Harmonic AI en local
    """
    start_time = time.time()
    
    # Vérifier si la réponse est en cache (simule le déterminisme)
    cache_key = f"{request.prompt}:{request.max_tokens}:{request.temperature}:{request.verified_mode}:{json.dumps(request.sources, sort_keys=True)}"
    
    if cache_key in response_cache:
        # Retourner la réponse mise en cache (déterminisme)
        response = response_cache[cache_key]
        response["cached"] = True
    else:
        # Générer une nouvelle réponse
        response = create_demo_response(
            request.prompt, 
            request.max_tokens,
            request.verified_mode,
            request.sources
        )
        response["cached"] = False
        
        # Mettre en cache pour les requêtes futures
        response_cache[cache_key] = response
    
    # Ajouter les métriques de performance
    response_time = time.time() - start_time
    response["response_time_ms"] = round(response_time * 1000, 2)
    
    # Éviter la division par zéro
    if response_time > 0:
        response["tokens_per_second"] = round(response["tokens_generated"] / response_time, 2)
    else:
        response["tokens_per_second"] = response["tokens_generated"] * 1000  # Valeur par défaut
    
    return response

@app.get("/health", response_model=HealthResponse)
async def health():
    """
    Endpoint de santé
    Vérifie que l'API fonctionne correctement
    """
    return {
        "status": "healthy",
        "mode": "local_demo",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0-local"
    }

@app.get("/info")
async def info():
    """
    Informations sur l'API locale
    """
    return {
        "name": "Harmonic AI Local Demo",
        "version": "1.0.0-local",
        "description": "API de démonstration locale pour développement avec connexion internet instable",
        "features": [
            "Déterminisme simulé (cache)",
            "Réponses réalistes selon le type de prompt",
            "Métriques de performance simulées",
            "Mode vérifié optionnel"
        ],
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "cache_size": len(response_cache)
    }

@app.get("/clear_cache")
async def clear_cache():
    """
    Effacer le cache des réponses
    """
    global response_cache
    cache_size = len(response_cache)
    response_cache = {}
    
    return {
        "action": "cache_cleared",
        "cache_size_before": cache_size,
        "cache_size_after": 0,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("Harmonic AI Local Demo API")
    print("=" * 60)
    print("Mode: Développement local (connexion instable)")
    print("URL: http://localhost:8001")
    print("Endpoints:")
    print("  - POST /generate     : Génération de texte")
    print("  - GET  /health       : Vérification santé")
    print("  - GET  /info         : Informations API")
    print("  - GET  /clear_cache  : Effacer le cache")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8001)