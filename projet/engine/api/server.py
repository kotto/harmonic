"""
Serveur API REST — FastAPI pour le moteur harmonique complet.
==============================================================
"""

import os
import json
import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextlib import asynccontextmanager

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

logger = logging.getLogger(__name__)


# =========================================================================
# MODELS API (Pydantic)
# =========================================================================

class AnalyzeRequest(BaseModel):
    prompt: str

class AnalyzeResponse(BaseModel):
    category: str
    confidence: float
    signature: Dict[str, float]
    processing_time_ms: float

class GenerateRequest(BaseModel):
    prompt: str
    category: Optional[str] = "auto"
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    stream: bool = False

class GenerateResponse(BaseModel):
    content: str
    model: str
    provider: str
    category: str
    tokens_used: int
    latency_ms: float

class ExpandRequest(BaseModel):
    text: str
    category: str = "general"
    verified: bool = True

class ExpandResponse(BaseModel):
    original: str
    expanded: str
    expansion_ratio: float

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    user_id: Optional[str] = "anonymous"
    stream: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

class ChatResponse(BaseModel):
    content: str
    model: str
    category: str
    resonance_score: float
    tokens_used: int
    latency_ms: float
    session_id: str


# =========================================================================
# APPLICATION FASTAPI
# =========================================================================

class HarmonicAPI:
    """
    Application API REST pour le moteur harmonique.
    
    Usage:
        api = HarmonicAPI()
        api.run(host="0.0.0.0", port=8000)
    """
    
    def __init__(self):
        if not FASTAPI_AVAILABLE:
            raise ImportError(
                "FastAPI non installe. "
                "Installez avec: pip install fastapi uvicorn"
            )
        
        self.engine = None
        self.llm = None
        self.memories = {}       # {"session_id": ConversationMemory}
        self.profiles = {}       # {"user_id": UserProfile}
        self.vector_store = None
        self.long_term = None
        
        self.app = FastAPI(
            title="Harmonic AI API",
            description="API du moteur de resonances cognitives harmoniques",
            version="1.0.0",
        )
        
        self._setup_cors()
        self._setup_routes()
    
    def _setup_cors(self):
        """Configure CORS pour tous les domaines."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _init_components(self):
        """Initialisation lazy des composants."""
        if self.engine is None:
            from ..harmonic_engine import HarmonicResonanceEngine
            self.engine = HarmonicResonanceEngine()
            logger.info("Moteur harmonique initialise")
        
        if self.llm is None:
            from ..llm import HarmonicLLM
            self.llm = HarmonicLLM()
            logger.info("Routeur LLM initialise")
        
        if self.vector_store is None:
            from ..semantic import VectorStore
            self.vector_store = VectorStore()
            logger.info("Vector store initialise")
        
        if self.long_term is None:
            from ..memory import LongTermMemory
            self.long_term = LongTermMemory()
            logger.info("Memoire long-terme initialisee")
    
    def _get_or_create_memory(self, session_id: str):
        """Recupere ou cree une memoire de conversation."""
        if session_id not in self.memories:
            from ..memory import ConversationMemory
            self.memories[session_id] = ConversationMemory(session_id=session_id)
        return self.memories[session_id]
    
    def _get_or_create_profile(self, user_id: str):
        """Recupere ou cree un profil utilisateur."""
        if user_id not in self.profiles:
            from ..memory import UserProfile
            self.profiles[user_id] = UserProfile(user_id=user_id)
        return self.profiles[user_id]
    
    def _setup_routes(self):
        app = self.app
        
        @app.get("/api/health")
        async def health():
            return {
                "status": "ok",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "engine_loaded": self.engine is not None,
            }
        
        @app.post("/api/analyze", response_model=AnalyzeResponse)
        async def analyze(req: AnalyzeRequest):
            self._init_components()
            start = time.time()
            
            sig = self.engine.analyze(req.prompt)
            cat, conf = self.engine.classify(req.prompt)
            
            latency = (time.time() - start) * 1000
            
            return AnalyzeResponse(
                category=cat,
                confidence=round(conf, 4),
                signature=sig.to_dict(),
                processing_time_ms=round(latency, 2),
            )
        
        @app.post("/api/classify")
        async def classify(req: AnalyzeRequest):
            self._init_components()
            
            sig = self.engine.analyze(req.prompt)
            cat, conf = self.engine.classify(req.prompt)
            
            return {
                "prompt": req.prompt,
                "category": cat,
                "confidence": round(conf, 4),
                "signature": sig.to_dict(),
                "vector": [round(v, 4) for v in sig.vector_7d],
            }
        
        @app.post("/api/generate", response_model=GenerateResponse)
        async def generate(req: GenerateRequest):
            self._init_components()
            start = time.time()
            
            # Auto-detect category
            category = req.category
            if category == "auto":
                cat, conf = self.engine.classify(req.prompt)
                category = cat if conf > 0.15 else "general"
            
            # Build config
            config = None
            if req.model or req.temperature is not None or req.max_tokens is not None:
                from ..llm import LLMConfig
                config = LLMConfig(
                    model=req.model or "auto",
                    temperature=req.temperature or 0.7,
                    max_tokens=req.max_tokens or 2048,
                    system_prompt=req.system_prompt,
                )
            
            # Generate
            resp = self.llm.generate(req.prompt, category, config)
            latency = (time.time() - start) * 1000
            
            return GenerateResponse(
                content=resp.content,
                model=resp.model,
                provider=resp.provider,
                category=category,
                tokens_used=resp.usage.get("total_tokens", 0),
                latency_ms=round(latency, 2),
            )
        
        @app.post("/api/expand", response_model=ExpandResponse)
        async def expand(req: ExpandRequest):
            self._init_components()
            
            expanded = self.engine.expand(req.text, req.category, req.verified)
            
            return ExpandResponse(
                original=req.text,
                expanded=expanded,
                expansion_ratio=round(len(expanded) / max(len(req.text), 1), 2),
            )
        
        @app.post("/api/chat", response_model=ChatResponse)
        async def chat(req: ChatRequest):
            self._init_components()
            start = time.time()
            
            session_id = req.user_id
            memory = self._get_or_create_memory(session_id)
            profile = self._get_or_create_profile(req.user_id)
            
            # Ajouter les messages a la memoire
            for msg in req.messages:
                if msg.role == "user":
                    sig = self.engine.analyze(msg.content)
                    cat, conf = self.engine.classify(msg.content)
                    memory.add("user", msg.content, category=cat, resonance_score=conf)
            
            # Dernier message utilisateur
            last_user_msg = next(
                (m.content for m in reversed(req.messages) if m.role == "user"),
                ""
            )
            
            if not last_user_msg:
                raise HTTPException(status_code=400, detail="Aucun message utilisateur")
            
            # Auto-classify
            cat, conf = self.engine.classify(last_user_msg)
            category = cat if conf > 0.15 else "general"
            
            # Build config with user preferences
            from ..llm import LLMConfig
            user_config = profile.get_optimized_config()
            config = LLMConfig(
                temperature=req.temperature or user_config.get("temperature", 0.7),
                max_tokens=req.max_tokens or user_config.get("max_tokens", 2048),
                system_prompt=f"Contexte conversation: {memory.get_context()[:500]}...",
            )
            
            # Generate
            resp = self.llm.generate(last_user_msg, category, config)
            latency = (time.time() - start) * 1000
            
            # Ajouter la reponse a la memoire
            resonance = conf if conf > 0 else 0.5
            memory.add("assistant", resp.content, category=category, resonance_score=resonance)
            
            # Enregistrer l'interaction
            profile.record_interaction(category, resonance_score=resonance, model=resp.model, latency_ms=latency)
            
            # Memoire long-terme
            self.long_term.remember(
                f"User {req.user_id} asked about {category}: {last_user_msg[:100]}",
                category=category,
                importance=resonance,
                resonance_score=resonance,
            )
            
            return ChatResponse(
                content=resp.content,
                model=resp.model,
                category=category,
                resonance_score=round(resonance, 4),
                tokens_used=resp.usage.get("total_tokens", 0),
                latency_ms=round(latency, 2),
                session_id=session_id,
            )
        
        @app.get("/api/stats")
        async def get_stats():
            self._init_components()
            
            return {
                "engine": self.engine.get_stats() if self.engine else {},
                "llm": self.llm.get_stats() if self.llm else {},
                "vector_store": self.vector_store.get_stats() if self.vector_store else {},
                "long_term_memory": self.long_term.get_stats() if self.long_term else {},
                "active_sessions": len(self.memories),
                "active_profiles": len(self.profiles),
                "available_api_keys": self.llm.available_keys if self.llm else {},
            }
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
        """Lance le serveur API."""
        import uvicorn
        logger.info(f"Demarrage API Harmonique sur http://{host}:{port}")
        uvicorn.run(self.app, host=host, port=port, reload=reload)


# =========================================================================
# FONCTIONS DE DEMARRAGE RAPIDE
# =========================================================================

def create_app() -> FastAPI:
    """Cree et retourne l'application FastAPI."""
    api = HarmonicAPI()
    api._init_components()
    return api.app


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Lance le serveur API directement."""
    api = HarmonicAPI()
    api._init_components()
    api.run(host=host, port=port)
