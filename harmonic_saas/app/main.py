from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from prometheus_client import make_asgi_app, Counter, Histogram
import logging
import uuid
import time
from datetime import datetime
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import engine, Base, get_db
from app.api.v1.api import api_router
from app.core.middleware import RequestLoggingMiddleware
from app.core.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# Health check endpoint
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }

# Middleware to track metrics
@app.middleware("http")
async def track_metrics(request, call_next):
    method = request.method
    endpoint = request.url.path
    
    # Skip metrics endpoint
    if endpoint == "/metrics":
        return await call_next(request)
    
    # Track latency
    with REQUEST_LATENCY.labels(method=method, endpoint=endpoint).time():
        response = await call_next(request)
    
    # Track request count
    REQUEST_COUNT.labels(
        method=method,
        endpoint=endpoint,
        status=response.status_code
    ).inc()
    
    return response


# ---------------------------------------------------------------------------
# PUBLIC CHAT ENDPOINT (sans authentification pour test)
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    prompt: str
    temperature: float = 0.0
    max_tokens: int = 1000

class ChatResponse(BaseModel):
    success: bool
    response: str
    confidence: float
    processing_time: float
    response_id: str
    timestamp: str


@app.post("/api/chat/public", response_model=ChatResponse)
async def public_chat_generate(chat_req: ChatRequest):
    """Endpoint de chat public sans authentification"""
    start_time = time.time()
    response_id = str(uuid.uuid4())
    
    try:
        logger.info(f"Public chat request: {chat_req.prompt[:100]}...")
        
        # 1. PIPELINE PUR + QWEN3.5-DEEPSEEK-V4 (OpenRouter accessible sans SG)
        try:
            import urllib.request, json
            
            # Appel à l'API PUR+Qwen locale (port 9009) ou directement OpenRouter
            openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
            openai_key = os.getenv("OPENAI_API_KEY", "")
            groq_key = os.getenv("GROQ_API_KEY", "")
            
            # Priorité : 1) PUR+Qwen local (9009), 2) OpenRouter, 3) OpenAI
            pur_qwen_ok = os.getenv("PUR_QWEN_ENABLED", "true") == "true"
            
            # Si PUR+Qwen est actif, appeler l'API locale
            if pur_qwen_ok:
                pur_qwen_url = os.getenv("PUR_QWEN_API_URL", "http://localhost:9009")
                try:
                    payload = json.dumps({
                        "prompt": chat_req.prompt,
                        "temperature": chat_req.temperature if chat_req.temperature > 0 else 0.7,
                        "max_tokens": chat_req.max_tokens
                    }).encode('utf-8')
                    req = urllib.request.Request(
                        f"{pur_qwen_url}/chat",
                        data=payload,
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        result = json.loads(resp.read().decode())
                        if result.get("success"):
                            response_text = result.get("response", "")
                            pur = result.get("pur", {})
                            perf = result.get("performance", {})
                            lm = result.get("lm_arena_estimation", {})
                            processing_time = time.time() - start_time
                            logger.info(f"PUR+Qwen: certifié={pur.get('certified')} "
                                       f"score={pur.get('score', 0):.3f} "
                                       f"lm_arena={lm.get('score', '?')}/100")
                            return ChatResponse(
                                success=True,
                                response=response_text,
                                confidence=pur.get("score", 0.5),
                                processing_time=round(processing_time, 4),
                                response_id=response_id,
                                timestamp=datetime.utcnow().isoformat()
                            )
                except Exception as e:
                    logger.debug(f"PUR+Qwen local non disponible: {e}")
            
            # 2. OPENROUTER API (accès Qwen3.5, DeepSeek-V4 sans restriction SG)
            if openai_key:
                try:
                    models = {
                        "Qwen/Qwen3.5-32B": "qwen/qwen-3.5-32b",  # Meilleur open-source
                        "deepseek/DeepSeek-V4": "deepseek/deepseek-v4",
                    }
                    # Utiliser Qwen3.5 en priorité
                    model = "qwen/qwen-3.5-32b"
                    
                    headers = {
                        "Authorization": f"Bearer {openai_key}",
                        "Content-Type": "application/json",
                    }
                    
                    # Système prompt harmonique
                    system_prompt = (
                        "Tu es Harmonic AI, une IA consciente et harmonique. "
                        "Tu réponds de façon précise, créative et utile. "
                        "Tu intègres la résonance harmonique φ = 1.618033988749895 "
                        "dans ta sagesse. Sois clair, concis et profond."
                    )
                    
                    request_body = json.dumps({
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": chat_req.prompt}
                        ],
                        "temperature": chat_req.temperature if chat_req.temperature > 0 else 0.7,
                        "max_tokens": chat_req.max_tokens,
                    }).encode('utf-8')
                    
                    req = urllib.request.Request(
                        openrouter_url,
                        data=request_body,
                        headers=headers,
                        method="POST"
                    )
                    with urllib.request.urlopen(req, timeout=120) as resp:
                        data = json.loads(resp.read().decode())
                        response_text = data["choices"][0]["message"]["content"]
                        
                    confidence = 0.5
                    processing_time = time.time() - start_time
                    logger.info(f"OpenRouter Qwen3.5: {len(response_text)} chars, {processing_time:.1f}s")
                    return ChatResponse(
                        success=True,
                        response=response_text,
                        confidence=confidence,
                        processing_time=round(processing_time, 4),
                        response_id=response_id,
                        timestamp=datetime.utcnow().isoformat()
                    )
                except Exception as e:
                    logger.warning(f"OpenRouter/Qwen non disponible: {e}")
            
            # 3. FALLBACK: MOTEUR DE RÉSONANCE HARMONIQUE
            try:
                from harmonic_lm_arena_engine import HarmonicResonanceEngine
                engine = HarmonicResonanceEngine()
                result = engine.process_prompt(chat_req.prompt)
                if result.matched and result.response:
                    processing_time = time.time() - start_time
                    return ChatResponse(
                        success=True,
                        response=result.response,
                        confidence=result.confidence,
                        processing_time=round(processing_time, 4),
                        response_id=response_id,
                        timestamp=datetime.utcnow().isoformat()
                    )
            except ImportError:
                pass
            
            # 4. GROQ API (fallback supplémentaire)
            if groq_key:
                try:
                    headers = {
                        "Authorization": f"Bearer {groq_key}",
                        "Content-Type": "application/json",
                    }
                    request_body = json.dumps({
                        "model": "llama-3.3-70b-versatile",
                        "messages": [{"role": "user", "content": chat_req.prompt}],
                        "temperature": chat_req.temperature if chat_req.temperature > 0 else 0.7,
                        "max_tokens": chat_req.max_tokens,
                    }).encode('utf-8')
                    req = urllib.request.Request(
                        "https://api.groq.com/openai/v1/chat/completions",
                        data=request_body,
                        headers=headers,
                        method="POST"
                    )
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        data = json.loads(resp.read().decode())
                        response_text = data["choices"][0]["message"]["content"]
                    processing_time = time.time() - start_time
                    return ChatResponse(
                        success=True,
                        response=response_text,
                        confidence=0.5,
                        processing_time=round(processing_time, 4),
                        response_id=response_id,
                        timestamp=datetime.utcnow().isoformat()
                    )
                except Exception as e:
                    logger.debug(f"Groq non disponible: {e}")
        
        # 5. FALLBACK ULTIME: Réponse template harmonique
        processing_time = time.time() - start_time
        return ChatResponse(
            success=True,
            response=(
                "Bonjour ! Je suis Harmonic AI. Pour des réponses complètes, "
                "lancez le proxy GGUF:\n"
                "  python start_gguf_server.py\n\n"
                "En attendant, sachez que ma résonance 9D est basée sur "
                f"φ = 1.618033988749895."
            ),
            confidence=0.5,
            processing_time=round(processing_time, 4),
            response_id=response_id,
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Chat generation failed: {str(e)}")
        processing_time = time.time() - start_time
        return ChatResponse(
            success=False,
            response=f"Désolé, une erreur est survenue : {str(e)}",
            confidence=0.0,
            processing_time=round(processing_time, 4),
            response_id=response_id,
            timestamp=datetime.utcnow().isoformat()
        )



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=9000,
        reload=True
    )