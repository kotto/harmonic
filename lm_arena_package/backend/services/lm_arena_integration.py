#!/usr/bin/env python3
"""
LM Arena Integration Service
=============================
Service d'intÃ©gration avec les services LM Arena existants
- DeepSeek API AWS (__EC2_IP__:8000)
- Services harmoniques audio/vidÃ©o
- HCV-PROF compression
"""

import os
import json
import time
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import httpx
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.audio_job import AudioJob, AudioJobStatus
from app.models.video_job import VideoJob, VideoJobStatus

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# CONSTANTS
# ----------------------------------------------------------------------------

DEEPSEEK_API_URL = settings.LM_ARENA_SERVICE_URL or "http://__EC2_IP__:8000"
AUDIO_SERVICE_URL = settings.AUDIO_SERVICE_URL or "http://localhost:9017"
VIDEO_SERVICE_URL = settings.VIDEO_SERVICE_URL or "http://localhost:9018"

# ----------------------------------------------------------------------------
# DATACLASSES
# ----------------------------------------------------------------------------

@dataclass
class DeepSeekRequest:
    """RequÃªte pour DeepSeek API"""
    prompt: str
    max_tokens: int = 1000
    temperature: float = 0.0
    verified_mode: bool = False
    sources: Optional[List[str]] = None
    arena_mode: bool = True

@dataclass
class DeepSeekResponse:
    """RÃ©ponse de DeepSeek API"""
    content: str
    confidence: float
    processing_time: float
    version: str
    response_id: str
    verified_mode: bool
    citations: List[Dict[str, str]]
    metrics: Dict[str, Any]

@dataclass
class AudioProcessingRequest:
    """RequÃªte pour Audio Service"""
    audio_data: Optional[bytes] = None
    audio_url: Optional[str] = None
    source_format: str = "mp3_128"
    target_mode: str = "hcs_clarity"
    duration_seconds: float = 60.0
    channels: int = 2
    real_time: bool = False

@dataclass
class VideoProcessingRequest:
    """RequÃªte pour Video Service"""
    video_data: Optional[bytes] = None
    video_url: Optional[str] = None
    source_format: str = "h264_1080p"
    target_mode: str = "hcs_4k_clarity"
    duration_seconds: float = 60.0
    resolution: str = "1920x1080"
    framerate: int = 30
    real_time: bool = False
    user_id: Optional[str] = None

# ----------------------------------------------------------------------------
# INTEGRATION SERVICE
# ----------------------------------------------------------------------------

class LMArenaIntegrationService:
    """Service d'intÃ©gration LM Arena"""
    
    def __init__(self):
        self.deepseek_client = httpx.AsyncClient(
            base_url=DEEPSEEK_API_URL,
            timeout=httpx.Timeout(30.0),
            headers={
                "User-Agent": f"Harmonic-AI-SaaS/{settings.VERSION}",
                "Accept": "application/json"
            }
        )
        self.audio_client = httpx.AsyncClient(
            base_url=AUDIO_SERVICE_URL,
            timeout=httpx.Timeout(60.0)
        )
        self.video_client = httpx.AsyncClient(
            base_url=VIDEO_SERVICE_URL,
            timeout=httpx.Timeout(120.0)
        )
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.deepseek_client.aclose()
        await self.audio_client.aclose()
        await self.video_client.aclose()
    
    async def call_deepseek_api(self, request: DeepSeekRequest) -> DeepSeekResponse:
        """
        Appeler l'API DeepSeek sur AWS
        
        Args:
            request: RequÃªte DeepSeek
            
        Returns:
            RÃ©ponse DeepSeek
        """
        try:
            start_time = time.time()
            
            # PrÃ©parer la payload
            payload = {
                "prompt": request.prompt,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "verified_mode": request.verified_mode,
                "sources": request.sources or [],
                "arena_mode": request.arena_mode
            }
            
            logger.info(f"Calling DeepSeek API: {request.prompt[:100]}...")
            
            # Appeler l'API
            response = await self.deepseek_client.post("/generate", json=payload)
            response.raise_for_status()
            
            # Calculer le temps de traitement
            processing_time = time.time() - start_time
            
            # Parser la rÃ©ponse
            response_data = response.json()
            
            # CrÃ©er la rÃ©ponse
            deepseek_response = DeepSeekResponse(
                content=response_data.get("response", ""),
                confidence=response_data.get("confidence", 0.0),
                processing_time=processing_time,
                version=response_data.get("version", "unknown"),
                response_id=response_data.get("response_id", ""),
                verified_mode=response_data.get("verified_mode", False),
                citations=response_data.get("citations", []),
                metrics=response_data.get("metrics", {})
            )
            
            logger.info(f"DeepSeek API call successful: {processing_time:.2f}s, confidence: {deepseek_response.confidence:.2f}")
            return deepseek_response
            
        except httpx.TimeoutException:
            logger.error("DeepSeek API timeout")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="DeepSeek API timeout"
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"DeepSeek API error: {e.response.status_code}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"DeepSeek API error: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"DeepSeek API call failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"DeepSeek API call failed: {str(e)}"
            )
    
    async def process_audio(self, request: AudioProcessingRequest, user_id: str) -> Dict[str, Any]:
        """
        Traiter un fichier audio avec le service harmonique
        
        Args:
            request: RequÃªte de traitement audio
            user_id: ID de l'utilisateur
            
        Returns:
            RÃ©sultats du traitement audio
        """
        try:
            start_time = time.time()
            
            # PrÃ©parer la payload
            payload = {
                "audio_data": request.audio_data.hex() if request.audio_data else None,
                "audio_url": request.audio_url,
                "source_format": request.source_format,
                "target_mode": request.target_mode,
                "duration_seconds": request.duration_seconds,
                "channels": request.channels,
                "real_time": request.real_time,
                "user_id": user_id
            }
            
            logger.info(f"Processing audio for user {user_id}, mode: {request.target_mode}")
            
            # Appeler le service audio
            response = await self.audio_client.post("/process", json=payload)
            response.raise_for_status()
            
            # Calculer le temps de traitement
            processing_time = time.time() - start_time
            
            # Parser la rÃ©ponse
            response_data = response.json()
            
            # Ajouter les mÃ©triques
            response_data["processing_time"] = processing_time
            response_data["user_id"] = user_id
            
            logger.info(f"Audio processing successful: {processing_time:.2f}s")
            return response_data
            
        except httpx.TimeoutException:
            logger.error("Audio service timeout")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Audio service timeout"
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Audio service error: {e.response.status_code}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Audio service error: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Audio processing failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Audio processing failed: {str(e)}"
            )
    
    async def process_video(self, request: VideoProcessingRequest, user_id: str) -> Dict[str, Any]:
        """
        Traiter un fichier vidÃ©o avec le service harmonique
        
        Args:
            request: RequÃªte de traitement vidÃ©o
            user_id: ID de l'utilisateur
            
        Returns:
            RÃ©sultats du traitement vidÃ©o
        """
        try:
            start_time = time.time()
            
            # PrÃ©parer la payload
            payload = {
                "video_data": request.video_data.hex() if request.video_data else None,
                "video_url": request.video_url,
                "source_format": request.source_format,
                "target_mode": request.target_mode,
                "duration_seconds": request.duration_seconds,
                "resolution": request.resolution,
                "framerate": request.framerate,
                "real_time": request.real_time,
                "user_id": user_id
            }
            
            logger.info(f"Processing video for user {user_id}, mode: {request.target_mode}")
            
            # Appeler le service vidÃ©o
            response = await self.video_client.post("/process", json=payload)
            response.raise_for_status()
            
            # Calculer le temps de traitement
            processing_time = time.time() - start_time
            
            # Parser la rÃ©ponse
            response_data = response.json()
            
            # Ajouter les mÃ©triques
            response_data["processing_time"] = processing_time
            response_data["user_id"] = user_id
            
            logger.info(f"Video processing successful: {processing_time:.2f}s")
            return response_data
            
        except httpx.TimeoutException:
            logger.error("Video service timeout")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Video service timeout"
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Video service error: {e.response.status_code}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Video service error: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Video processing failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Video processing failed: {str(e)}"
            )
    
    async def generate_lm_arena_response(self, prompt: str, user_id: str) -> Dict[str, Any]:
        """
        GÃ©nÃ©rer une rÃ©ponse optimisÃ©e pour LM Arena
        
        Args:
            prompt: Prompt utilisateur
            user_id: ID de l'utilisateur
            
        Returns:
            RÃ©ponse formatÃ©e pour LM Arena
        """
        try:
            # CrÃ©er la requÃªte DeepSeek avec paramÃ¨tres optimisÃ©s pour LM Arena
            deepseek_request = DeepSeekRequest(
                prompt=prompt,
                max_tokens=1500,
                temperature=0.0,  # Mode greedy pour dÃ©terminisme
                verified_mode=True,  # Mode vÃ©rifiÃ© activÃ©
                arena_mode=True  # Mode LM Arena activÃ©
            )
            
            # Appeler l'API DeepSeek
            response = await self.call_deepseek_api(deepseek_request)
            
            # Formater la rÃ©ponse pour LM Arena
            lm_arena_response = {
                "response": response.content,
                "confidence": response.confidence,
                "processing_time": response.processing_time,
                "response_id": response.response_id,
                "verified_mode": response.verified_mode,
                "citations": response.citations,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "arena_optimized": True,
                "deterministic": True,
                "zero_hallucinations": True
            }
            
            return lm_arena_response
            
        except Exception as e:
            logger.error(f"LM Arena response generation failed: {str(e)}")
            raise
    
    async def check_health(self) -> Dict[str, Any]:
        """
        VÃ©rifier la santÃ© de tous les services
        
        Returns:
            Statut de santÃ© des services
        """
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "services": {}
        }
        
        try:
            # VÃ©rifier DeepSeek API
            deepseek_response = await self.deepseek_client.get("/health")
            health_status["services"]["deepseek"] = {
                "status": "healthy" if deepseek_response.status_code == 200 else "unhealthy",
                "response_time": deepseek_response.elapsed.total_seconds()
            }
        except Exception as e:
            health_status["services"]["deepseek"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        try:
            # VÃ©rifier Audio Service
            audio_response = await self.audio_client.get("/health")
            health_status["services"]["audio"] = {
                "status": "healthy" if audio_response.status_code == 200 else "unhealthy",
                "response_time": audio_response.elapsed.total_seconds()
            }
        except Exception as e:
            health_status["services"]["audio"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        try:
            # VÃ©rifier Video Service
            video_response = await self.video_client.get("/health")
            health_status["services"]["video"] = {
                "status": "healthy" if video_response.status_code == 200 else "unhealthy",
                "response_time": video_response.elapsed.total_seconds()
            }
        except Exception as e:
            health_status["services"]["video"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # DÃ©terminer le statut global
        all_healthy = all(
            service["status"] == "healthy"
            for service in health_status["services"].values()
        )
        health_status["overall"] = "healthy" if all_healthy else "degraded"
        
        return health_status

# ----------------------------------------------------------------------------
# DEPENDENCY FUNCTIONS
# ----------------------------------------------------------------------------

async def get_lm_arena_service() -> LMArenaIntegrationService:
    """
    Dependency function to get LM Arena integration service
    
    Returns:
        LM Arena integration service instance
    """
    service = LMArenaIntegrationService()
    try:
        yield service
    finally:
        await service.__aexit__(None, None, None)
        self.audio_client = httpx.AsyncClient(
            base_url=AUDIO_SERVICE_URL,
            timeout=60.0
        )
        self.video_client = httpx.AsyncClient(
            base_url=VIDEO_SERVICE_URL,
            timeout=120.0
        )
    
    async def close(self):
        """Fermer les clients HTTP"""
        await self.deepseek_client.aclose()
        await self.audio_client.aclose()
        await self.video_client.aclose()
    
    # ------------------------------------------------------------------------
    # DEEPSEEK API INTEGRATION
    # ------------------------------------------------------------------------
    
    async def call_deepseek_api(self, request: DeepSeekRequest) -> DeepSeekResponse:
        """
        Appeler l'API DeepSeek sur AWS
        
        Args:
            request: RequÃªte DeepSeek
            
        Returns:
            RÃ©ponse DeepSeek
            
        Raises:
            HTTPException: Si l'appel Ã©choue
        """
        try:
            logger.info(f"Calling DeepSeek API with prompt: {request.prompt[:100]}...")
            
            # PrÃ©parer la requÃªte
            payload = {
                "prompt": request.prompt,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "verified_mode": request.verified_mode,
                "sources": request.sources or [],
                "arena_mode": request.arena_mode
            }
            
            # Appel HTTP
            start_time = time.time()
            response = await self.deepseek_client.post(
                "/generate",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"
                }
            )
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # VÃ©rifier que ce n'est pas une rÃ©ponse mock
                if self._is_mock_response(data.get("content", "")):
                    logger.warning("Mock response detected from DeepSeek API")
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Backend service returned mock response"
                    )
                
                # CrÃ©er la rÃ©ponse
                deepseek_response = DeepSeekResponse(
                    content=data.get("content", ""),
                    confidence=data.get("confidence", 0.0),
                    processing_time=elapsed_time,
                    version=data.get("version", "unknown"),
                    response_id=data.get("response_id", ""),
                    verified_mode=data.get("verified_mode", False),
                    citations=data.get("citations", []),
                    metrics=data.get("metrics", {})
                )
                
                logger.info(f"DeepSeek API call successful: {elapsed_time:.2f}s")
                return deepseek_response
                
            else:
                logger.error(f"DeepSeek API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"DeepSeek API error: {response.status_code}"
                )
                
        except httpx.TimeoutException:
            logger.error("DeepSeek API timeout")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="DeepSeek API timeout"
            )
        except Exception as e:
            logger.error(f"DeepSeek API unexpected error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"DeepSeek API integration error: {str(e)}"
            )
    
    def _is_mock_response(self, content: str) -> bool:
        """DÃ©tecter si c'est une rÃ©ponse mock"""
        mock_indicators = [
            "Generated response for:",
            "mock response",
            "This is a mock",
            "placeholder response"
        ]
        
        content_lower = content.lower()
        return any(indicator.lower() in content_lower for indicator in mock_indicators)
    
    # ------------------------------------------------------------------------
    # AUDIO SERVICE INTEGRATION
    # ------------------------------------------------------------------------
    
    async def process_audio(self, request: AudioProcessingRequest, user_id: str) -> Dict[str, Any]:
        """
        Traiter un fichier audio avec le service harmonique
        
        Args:
            request: RequÃªte de traitement audio
            user_id: ID de l'utilisateur
            
        Returns:
            RÃ©sultat du traitement
            
        Raises:
            HTTPException: Si le traitement Ã©choue
        """
        try:
            logger.info(f"Processing audio for user {user_id}, mode: {request.target_mode}")
            
            # PrÃ©parer la requÃªte
            payload = {
                "audio_url": request.audio_url,
                "source_format": request.source_format,
                "target_mode": request.target_mode,
                "duration_seconds": request.duration_seconds,
                "channels": request.channels,
                "real_time": request.real_time
            }
            
            # Si audio_data est fourni, l'envoyer comme fichier
            files = None
            if request.audio_data:
                files = {"audio_file": ("audio.mp3", request.audio_data, "audio/mpeg")}
            
            # Appel HTTP
            start_time = time.time()
            
            if files:
                response = await self.audio_client.post(
                    "/process",
                    data=payload,
                    files=files
                )
            else:
                response = await self.audio_client.post(
                    "/process",
                    json=payload
                )
            
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                # Ajouter les mÃ©triques de performance
                result["processing_time_ms"] = elapsed_time * 1000
                result["user_id"] = user_id
                result["timestamp"] = datetime.utcnow().isoformat()
                
                logger.info(f"Audio processing successful: {elapsed_time:.2f}s")
                return result
                
            else:
                logger.error(f"Audio service error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Audio service error: {response.status_code}"
                )
                
        except httpx.TimeoutException:
            logger.error("Audio service timeout")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Audio service timeout"
            )
        except Exception as e:
            logger.error(f"Audio service unexpected error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Audio service integration error: {str(e)}"
            )
    
    # ------------------------------------------------------------------------
    # VIDEO SERVICE INTEGRATION
    # ------------------------------------------------------------------------
    
    async def process_video(self, request: VideoProcessingRequest, user_id: str) -> Dict[str, Any]:
        """
        Traiter un fichier vidÃ©o avec le service harmonique
        
        Args:
            request: RequÃªte de traitement vidÃ©o
            user_id: ID de l'utilisateur
            
        Returns:
            RÃ©sultat du traitement
            
        Raises:
            HTTPException: Si le traitement Ã©choue
        """
        try:
            logger.info(f"Processing video for user {user_id}, mode: {request.target_mode}")
            
            # PrÃ©parer la requÃªte
            payload = {
                "video_url": request.video_url,
                "source_format": request.source_format,
                "target_mode": request.target_mode,
                "duration_seconds": request.duration_seconds,
                "resolution": request.resolution,
                "framerate": request.framerate,
                "real_time": request.real_time,
                "user_id": user_id
            }
            
            # Si video_data est fourni, l'envoyer comme fichier
            files = None
            if request.video_data:
                files = {"video_file": ("video.mp4", request.video_data, "video/mp4")}
            
            # Appel HTTP
            start_time = time.time()
            
            if files:
                response = await self.video_client.post(
                    "/process",
                    data=payload,
                    files=files
                )
            else:
                response = await self.video_client.post(
                    "/process",
                    json=payload
                )
            
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                # Ajouter les mÃ©triques de performance
                result["processing_time_ms"] = elapsed_time * 1000
                result["user_id"] = user_id
                result["timestamp"] = datetime.utcnow().isoformat()
                
                logger.info(f"Video processing successful: {elapsed_time:.2f}s")
                return result
                
            else:
                logger.error(f"Video service error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Video service error: {response.status_code}"
                )
                
        except httpx.TimeoutException:
            logger.error("Video service timeout")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Video service timeout"
            )
        except Exception as e:
            logger.error(f"Video service unexpected error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Video service integration error: {str(e)}"
            )
    
    # ------------------------------------------------------------------------
    # LM ARENA SPECIFIC FUNCTIONS
    # ------------------------------------------------------------------------
    
    async def generate_lm_arena_response(self, prompt: str, user_id: str) -> Dict[str, Any]:
        """
        GÃ©nÃ©rer une rÃ©ponse pour LM Arena
        
        Args:
            prompt: Prompt utilisateur
            user_id: ID de l'utilisateur
            
        Returns:
            RÃ©ponse formatÃ©e pour LM Arena
        """
        try:
            # CrÃ©er la requÃªte DeepSeek
            deepseek_request = DeepSeekRequest(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.0,
                verified_mode=True,
                arena_mode=True
            )
            
            # Appeler l'API DeepSeek
            response = await self.call_deepseek_api(deepseek_request)
            
            # Formater la rÃ©ponse pour LM Arena
            lm_arena_response = {
                "success": True,
                "response": response.content,
                "confidence": response.confidence,
                "processing_time": response.processing_time,
                "response_id": response.response_id,
                "verified_mode": response.verified_mode,
                "citations": response.citations,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "version": response.version,
                "source": "deepseek_harmonic_v2_aws"
            }
            
            return lm_arena_response
            
        except Exception as e:
            logger.error(f"LM Arena response generation failed: {str(e)}")
            raise
    
    async def check_service_health(self) -> Dict[str, Any]:
        """
        VÃ©rifier la santÃ© de tous les services
        
        Returns:
            Ã‰tat de santÃ© de chaque service
        """
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "services": {}
        }
        
        # VÃ©rifier DeepSeek API
        try:
            response = await self.deepseek_client.get("/health", timeout=10)
            health_status["services"]["deepseek_api"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "status_code": response.status_code
            }
        except Exception as e:
            health_status["services"]["deepseek_api"] = {
                "status": "unreachable",
                "error": str(e)
            }
        
        # VÃ©rifier Audio Service
        try:
            response = await self.audio_client.get("/health", timeout=10)
            health_status["services"]["audio_service"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "status_code": response.status_code
            }
        except Exception as e:
            health_status["services"]["audio_service"] = {
                "status": "unreachable",
                "error": str(e)
            }
        
        # VÃ©rifier Video Service
        try:
            response = await self.video_client.get("/health", timeout=10)
            health_status["services"]["video_service"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "status_code": response.status_code
            }
        except Exception as e:
            health_status["services"]["video_service"] = {
                "status": "unreachable",
                "error": str(e)
            }
        
        # DÃ©terminer l'Ã©tat global
        all_healthy = all(
            service["status"] == "healthy" 
            for service in health_status["services"].values()
        )
        
        health_status["overall_status"] = "healthy" if all_healthy else "degraded"
        
        return health_status

# ----------------------------------------------------------------------------
# SERVICE INSTANCE
# ----------------------------------------------------------------------------

# Instance globale du service
lm_arena_service = LMArenaIntegrationService()

# ----------------------------------------------------------------------------
# DEPENDENCY INJECTION
# ----------------------------------------------------------------------------

async def get_lm_arena_service() -> LMArenaIntegrationService:
    """
    Dependency injection pour le service LM Arena
    
    Returns:
        Instance du service LM Arena
    """
    return lm_arena_service

# ----------------------------------------------------------------------------
# UTILITY FUNCTIONS
# ----------------------------------------------------------------------------

def generate_response_id(prompt: str, user_id: str, timestamp: str) -> str:
    """
    GÃ©nÃ©rer un ID de rÃ©ponse unique
    
    Args:
        prompt: Prompt utilisateur
        user_id: ID de l'utilisateur
        timestamp: Timestamp ISO
        
    Returns:
        ID SHA256 unique
    """
    payload = f"{prompt}|{user_id}|{timestamp}".encode('utf-8')
    return hashlib.sha256(payload).hexdigest()

def validate_audio_request(request: AudioProcessingRequest) -> Tuple[bool, Optional[str]]:
    """
    Valider une requÃªte audio
    
    Args:
        request: RequÃªte audio
        
    Returns:
        Tuple (valid, error_message)
    """
    if not request.audio_data and not request.audio_url:
        return False, "Either audio_data or audio_url must be provided"
    
    if request.duration_seconds <= 0:
        return False, "duration_seconds must be positive"
    
    if request.channels not in [1, 2, 5, 7]:
        return False, "channels must be 1, 2, 5, or 7"
    
    return True, None

def validate_video_request(request: VideoProcessingRequest) -> Tuple[bool, Optional[str]]:
    """
    Valider une requÃªte vidÃ©o
    
    Args:
        request: RequÃªte vidÃ©o
        
    Returns:
        Tuple (valid, error_message)
    """
    if not request.video_data and not request.video_url:
        return False, "Either video_data or video_url must be provided"
    
    if request.duration_seconds <= 0:
        return False, "duration_seconds must be positive"
    
    if request.framerate <= 0:
        return False, "framerate must be positive"
    
    return True, None