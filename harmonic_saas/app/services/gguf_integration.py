#!/usr/bin/env python3
"""
Service d'intégration GGUF Harmonique
========================================
Connecte le serveur GGUF Harmonique (start_gguf_server.py) à l'API SAAS
Harmonic AI. Remplace l'appel distant à l'API DeepSeek AWS par un appel
local au proxy GGUF harmonique avec résonance 9D.

Architecture:
    Chat Request → SAAS API → GGUF Integration Service → GGUF Proxy (localhost)
                                   ↓
                           Résonance 9D + Mémoire ABC
                                   ↓
    Chat Response ← SAAS API ← GGUF Integration Service ← GGUF Proxy

Usage:
    # Dans main.py ou tout endpoint de chat :
    from app.services.gguf_integration import GGUFIntegrationService
    
    service = GGUFIntegrationService()
    response = await service.chat("Explique la relativité")
"""

import os
import json
import time
import uuid
import logging
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Constantes harmoniques
PHI = 1.618033988749895

# URL par défaut du proxy GGUF
DEFAULT_GGUF_URL = os.getenv("GGUF_SERVICE_URL", "http://localhost:8080")
GGUF_API_KEY = os.getenv("GGUF_API_KEY", "")

# Timeouts
TIMEOUT_SECONDS = 120.0  # Génération LLM longue


@dataclass
class GGUFResponse:
    """Réponse normalisée du service GGUF."""
    success: bool
    response: str
    confidence: float = 0.85
    processing_time: float = 0.0
    response_id: str = ""
    category: str = "general"
    resonance_score: float = 0.0
    signature_9d: List[float] = field(default_factory=lambda: [0.0] * 9)
    model: str = "harmonic-gguf"
    error: Optional[str] = None


class GGUFIntegrationService:
    """
    Service d'intégration entre l'API SAAS et le proxy GGUF Harmonique.
    
    Fonctionnalités :
    - Chat avec résonance harmonique 9D
    - Fallback automatique (mode démo si GGUF indisponible)
    - Cache de résonance pour requêtes récurrentes
    - Compatible avec le format OpenAI
    """
    
    def __init__(self, gguf_url: str = DEFAULT_GGUF_URL):
        self.gguf_url = gguf_url.rstrip("/")
        self._client = None
        self._cache = {}
        self._stats = {
            "total_calls": 0,
            "gguf_calls": 0,
            "fallback_calls": 0,
            "cache_hits": 0,
            "avg_latency_ms": 0.0,
        }
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Crée ou retourne le client HTTP."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=TIMEOUT_SECONDS,
                headers={
                    "Content-Type": "application/json",
                    **({"Authorization": f"Bearer {GGUF_API_KEY}"} if GGUF_API_KEY else {})
                }
            )
        return self._client
    
    async def chat(self, prompt: str, 
                   temperature: Optional[float] = None,
                   max_tokens: int = 1000,
                   use_resonance: bool = True,
                   category: Optional[str] = None) -> GGUFResponse:
        """
        Envoie une requête de chat au proxy GGUF harmonique.
        
        Args:
            prompt: Question utilisateur
            temperature: Créativité (None = auto selon catégorie)
            max_tokens: Tokens max à générer
            use_resonance: Activer la résonance 9D
            category: Catégorie harmonique (auto si None)
        
        Returns:
            GGUFResponse avec contenu, résonance, signature
        """
        t0 = time.time()
        self._stats["total_calls"] += 1
        response_id = str(uuid.uuid4())
        
        # Cache simple (même prompt = même catégorie)
        cache_key = f"{prompt[:100]}|{category or 'auto'}|{use_resonance}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if time.time() - cached["timestamp"] < 60:  # Cache 60s
                self._stats["cache_hits"] += 1
                cached["response"].processing_time = time.time() - t0
                return cached["response"]
        
        try:
            client = await self._get_client()
            
            # Construire la requête au format OpenAI
            payload = {
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "harmonic_resonance": use_resonance,
                "model": "harmonic-gguf",
            }
            if temperature is not None:
                payload["temperature"] = temperature
            if category:
                payload["category"] = category
            
            # Appel au proxy GGUF
            resp = await client.post(
                f"{self.gguf_url}/v1/chat/completions",
                json=payload
            )
            
            if resp.status_code != 200:
                logger.warning(f"GGUF proxy returned {resp.status_code}: {resp.text[:200]}")
                return await self._fallback(prompt, category, t0, response_id)
            
            data = resp.json()
            self._stats["gguf_calls"] += 1
            
            # Extraire le contenu
            content = ""
            choices = data.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")
            
            # Extraire les métadonnées harmoniques
            harmonic = data.get("harmonic_resonance", {})
            resonance_score = harmonic.get("resonance_score", 0.0)
            signature_9d = harmonic.get("signature_9d", [0.0] * 9)
            detected_category = harmonic.get("category", category or "general")
            model = data.get("model", "harmonic-gguf")
            
            # Construire la réponse
            result = GGUFResponse(
                success=True,
                response=content or "Désolé, je n'ai pas pu générer de réponse.",
                confidence=min(0.99, 0.7 + resonance_score * 0.3),
                processing_time=round(time.time() - t0, 3),
                response_id=response_id,
                category=detected_category,
                resonance_score=resonance_score,
                signature_9d=signature_9d,
                model=model,
            )
            
            # Mettre en cache
            self._cache[cache_key] = {
                "response": result,
                "timestamp": time.time()
            }
            
            # Stats
            elapsed_ms = (time.time() - t0) * 1000
            n = self._stats["total_calls"]
            self._stats["avg_latency_ms"] = (
                self._stats["avg_latency_ms"] * (n - 1) + elapsed_ms
            ) / n
            
            return result
            
        except httpx.ConnectError:
            logger.warning(f"GGUF proxy indisponible sur {self.gguf_url}")
            return await self._fallback(prompt, category, t0, response_id)
        except httpx.TimeoutException:
            logger.warning(f"GGUF proxy timeout après {TIMEOUT_SECONDS}s")
            return await self._fallback(prompt, category, t0, response_id)
        except Exception as e:
            logger.error(f"Erreur GGUF integration: {e}")
            return await self._fallback(prompt, category, t0, response_id)
    
    async def _fallback(self, prompt: str, category: Optional[str],
                        t0: float, response_id: str) -> GGUFResponse:
        """
        Fallback harmonique local quand le proxy GGUF est indisponible.
        
        Utilise la compréhension harmonique locale (sans LLM) pour
        générer une réponse de qualité même hors-ligne.
        """
        self._stats["fallback_calls"] += 1
        
        try:
            # Essayer le module de compréhension harmonique
            from app.services.harmonic_comprehension import HarmonicComprehensionModule
            hcm = HarmonicComprehensionModule()
            result = hcm.process(
                prompt=prompt,
                session_id="gguf-fallback",
                temperature=0.7,
                max_tokens=1000,
                use_llm=False  # Mode local seulement
            )
            content = result.get("response", "")
            confidence = result.get("confidence", 0.7)
        except Exception:
            # Fallback ultime: template harmonique
            content = self._generate_fallback_response(prompt, category)
            confidence = 0.6
        
        return GGUFResponse(
            success=True,
            response=content,
            confidence=confidence,
            processing_time=round(time.time() - t0, 3),
            response_id=response_id,
            category=category or "general",
            resonance_score=0.5,
            model="harmonic-fallback",
        )
    
    def _generate_fallback_response(self, prompt: str, category: Optional[str]) -> str:
        """Génère une réponse template quand aucun LLM n'est disponible."""
        # Détection simple de catégorie
        p = prompt.lower()
        
        if "phi" in p or "nombre d'or" in p or "harmonie" in p:
            return (
                f"Le nombre d'or φ = {PHI:.6f} est au cœur de la résonance harmonique. "
                f"Il apparaît dans la nature (coquilles, fleurs), l'art (Parthénon, Mona Lisa), "
                f"et maintenant dans l'architecture de l'IA. "
                f"Le GGUF Harmonizer permet à tout modèle de résonner à φ."
            )
        elif category == "mathematical" or any(w in p for w in ["calcul", "math"]):
            return (
                f"Analyse mathématique de «{prompt[:60]}»... "
                f"Le proxy GGUF harmonique n'est pas connecté. "
                f"Lancez: python start_gguf_server.py --model 9b\n\n"
                f"En attendant, sachez que φ = {PHI:.6f} est la constante "
                f"la plus irrationnelle, ce qui en fait le meilleur choix "
                f"pour éviter les résonances parasites en IA."
            )
        elif category == "creative" or any(w in p for w in ["poeme", "art", "musique"]):
            return (
                f"La créativité harmonique pulse à la fréquence de φ. "
                f"«{prompt[:60]}» — quelle belle invitation à la résonance ! "
                f"Le GGUF Harmonizer amplifie la dimension créative (score 3/9). "
                f"Pour des générations réelles, connectez le proxy GGUF."
            )
        else:
            return (
                f"Bonjour ! Je suis Harmonic AI, propulsé par le GGUF Harmonizer. "
                f"Ma résonance 9D est active, mais le modèle LLM n'est pas connecté.\n\n"
                f"Pour activer l'IA réelle:\n"
                f"  python start_gguf_server.py --model 9b\n\n"
                f"En mode local, je peux vous parler de φ = {PHI:.6f}, "
                f"de résonance harmonique, et de l'architecture 9D."
            )
    
    async def classify(self, prompt: str) -> Dict[str, Any]:
        """Classification 9D via le proxy GGUF."""
        try:
            client = await self._get_client()
            resp = await client.get(
                f"{self.gguf_url}/harmonic/signature",
                params={"prompt": prompt[:500]}
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        
        # Fallback: classification locale rapide
        from engine.llm.gguf_harmonizer import GGUFHarmonicInjector
        injector = GGUFHarmonicInjector()
        sig = injector._quick_signature_9d(prompt)
        category = injector._detect_category(prompt)
        
        return {
            "signature_9d": sig,
            "category": category,
            "dimensions": {
                "phi": sig[0], "alpha": sig[1],
                "reasoning": sig[2], "creative": sig[3],
                "math": sig[4], "factual": sig[5],
                "code": sig[6], "emotion": sig[7], "temporal": sig[8],
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé du proxy GGUF."""
        status = {
            "gguf_proxy": "unknown",
            "model": "unknown",
            "latency_ms": 0,
            "harmonic_resonance": False,
            "memory_active": False,
        }
        
        try:
            client = await self._get_client()
            t0 = time.time()
            resp = await client.get(f"{self.gguf_url}/health")
            elapsed_ms = (time.time() - t0) * 1000
            
            if resp.status_code == 200:
                data = resp.json()
                status.update({
                    "gguf_proxy": "healthy",
                    "model": data.get("model", "unknown"),
                    "latency_ms": round(elapsed_ms, 1),
                    "harmonic_resonance": data.get("harmonic", False),
                    "memory_active": data.get("memory_active", False),
                })
        except Exception as e:
            status["gguf_proxy"] = f"unavailable: {str(e)}"
        
        return status
    
    def get_stats(self) -> Dict[str, Any]:
        """Statistiques du service d'intégration."""
        return {
            **self._stats,
            "cache_size": len(self._cache),
            "gguf_url": self.gguf_url,
        }
    
    async def close(self):
        """Ferme le client HTTP."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# Instance singleton pour l'application
_gguf_service: Optional[GGUFIntegrationService] = None


def get_gguf_service() -> GGUFIntegrationService:
    """Retourne l'instance singleton du service GGUF."""
    global _gguf_service
    if _gguf_service is None:
        _gguf_service = GGUFIntegrationService()
    return _gguf_service
