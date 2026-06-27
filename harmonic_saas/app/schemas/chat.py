#!/usr/bin/env python3
"""
Chat Schemas - LM Arena Integration
====================================
Schémas Pydantic pour les endpoints de chat et intégration LM Arena
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

# ----------------------------------------------------------------------------
# ENUMS
# ----------------------------------------------------------------------------

class ChatMessageRole(str, Enum):
    """Rôle des messages dans une conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatResponseStatus(str, Enum):
    """Statut des réponses de chat"""
    SUCCESS = "success"
    ERROR = "error"
    PROCESSING = "processing"

# ----------------------------------------------------------------------------
# REQUEST SCHEMAS
# ----------------------------------------------------------------------------

class ChatMessage(BaseModel):
    """Message individuel dans une conversation"""
    role: ChatMessageRole
    content: str
    timestamp: Optional[datetime] = None
    
    @validator('timestamp', pre=True, always=True)
    def set_timestamp(cls, v):
        return v or datetime.utcnow()

class ChatRequest(BaseModel):
    """Requête pour générer une réponse de chat"""
    prompt: str = Field(..., min_length=1, max_length=10000, description="Prompt utilisateur")
    conversation_id: Optional[str] = Field(None, description="ID de conversation existante")
    max_tokens: int = Field(default=1000, ge=1, le=10000, description="Nombre maximum de tokens")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="Température de génération")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-p sampling")
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Pénalité de fréquence")
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Pénalité de présence")
    verified_mode: bool = Field(default=True, description="Mode vérifié avec citations")
    sources: Optional[List[str]] = Field(None, description="Sources pour vérification")
    arena_mode: bool = Field(default=True, description="Mode optimisé pour LM Arena")
    
    @validator('prompt')
    def validate_prompt(cls, v):
        if not v.strip():
            raise ValueError("Prompt cannot be empty or whitespace only")
        return v.strip()
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if v == 0.0 and cls.arena_mode:
            # LM Arena recommande temperature=0 pour la reproductibilité
            return 0.0
        return v

class AudioProcessingRequest(BaseModel):
    """Requête pour le traitement audio"""
    audio_data: Optional[bytes] = Field(None, description="Données audio binaires")
    audio_url: Optional[str] = Field(None, description="URL du fichier audio")
    source_format: str = Field(default="mp3_128", description="Format source")
    processing_mode: str = Field(default="hcs_clarity", description="Mode de traitement")
    target_profile: Optional[str] = Field(None, description="Profil cible")
    duration_seconds: float = Field(default=60.0, ge=0.1, le=3600.0, description="Durée en secondes")
    channels: int = Field(default=2, ge=1, le=16, description="Nombre de canaux")
    enhance_clarity: bool = Field(default=True, description="Amélioration de la clarté")
    spatial_enhancement: bool = Field(default=False, description="Amélioration spatiale")
    dynamic_range_boost: bool = Field(default=False, description="Boost de la dynamique")
    vintage_restoration: bool = Field(default=False, description="Restauration vintage")
    real_time: bool = Field(default=False, description="Traitement en temps réel")
    
    @validator('audio_data', 'audio_url')
    def validate_audio_source(cls, v, values):
        if not values.get('audio_data') and not values.get('audio_url'):
            raise ValueError("Either audio_data or audio_url must be provided")
        return v

class VideoProcessingRequest(BaseModel):
    """Requête pour le traitement vidéo"""
    video_data: Optional[bytes] = Field(None, description="Données vidéo binaires")
    video_url: Optional[str] = Field(None, description="URL du fichier vidéo")
    source_format: str = Field(default="h264_1080p", description="Format source")
    processing_mode: str = Field(default="hcs_4k_clarity", description="Mode de traitement")
    target_resolution: Optional[str] = Field(None, description="Résolution cible")
    duration_seconds: float = Field(default=60.0, ge=0.1, le=3600.0, description="Durée en secondes")
    resolution: str = Field(default="1920x1080", description="Résolution source")
    framerate: int = Field(default=30, ge=1, le=240, description="Framerate source")
    enable_hdr: bool = Field(default=False, description="Activer HDR")
    frame_interpolation: bool = Field(default=False, description="Interpolation de frames")
    continuous_generation: bool = Field(default=False, description="Génération continue")
    real_time: bool = Field(default=False, description="Traitement en temps réel")
    
    @validator('video_data', 'video_url')
    def validate_video_source(cls, v, values):
        if not values.get('video_data') and not values.get('video_url'):
            raise ValueError("Either video_data or video_url must be provided")
        return v

# ----------------------------------------------------------------------------
# RESPONSE SCHEMAS
# ----------------------------------------------------------------------------

class Citation(BaseModel):
    """Citation d'une source"""
    source: str = Field(..., description="Source de la citation")
    text: str = Field(..., description="Texte cité")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiance dans la citation")
    timestamp: Optional[datetime] = Field(None, description="Timestamp de la source")

class ChatResponse(BaseModel):
    """Réponse de chat générée"""
    success: bool = Field(..., description="Succès de la génération")
    response: str = Field(..., description="Réponse générée")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiance dans la réponse")
    processing_time: float = Field(..., ge=0.0, description="Temps de traitement en secondes")
    response_id: str = Field(..., description="ID unique de la réponse")
    verified_mode: bool = Field(..., description="Mode vérifié utilisé")
    citations: List[Citation] = Field(default=[], description="Citations des sources")
    user_id: str = Field(..., description="ID de l'utilisateur")
    timestamp: datetime = Field(..., description="Timestamp de la réponse")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Métadonnées supplémentaires")
    
    @validator('timestamp', pre=True, always=True)
    def set_timestamp(cls, v):
        return v or datetime.utcnow()

class AudioProcessingResponse(BaseModel):
    """Réponse de traitement audio"""
    success: bool = Field(..., description="Succès du traitement")
    job_id: str = Field(..., description="ID du job de traitement")
    status: str = Field(..., description="Statut du job")
    processing_mode: str = Field(..., description="Mode de traitement utilisé")
    quality_improvement: Optional[float] = Field(None, ge=0.0, le=100.0, description="Amélioration de qualité (%)")
    processing_time_ms: Optional[float] = Field(None, ge=0.0, description="Temps de traitement en ms")
    result_url: Optional[str] = Field(None, description="URL du résultat")
    error_message: Optional[str] = Field(None, description="Message d'erreur")
    estimated_processing_time: Optional[float] = Field(None, description="Temps estimé en secondes")
    message: Optional[str] = Field(None, description="Message informatif")
    created_at: Optional[str] = Field(None, description="Date de création")
    completed_at: Optional[str] = Field(None, description="Date de complétion")

class VideoProcessingResponse(BaseModel):
    """Réponse de traitement vidéo"""
    success: bool = Field(..., description="Succès du traitement")
    job_id: str = Field(..., description="ID du job de traitement")
    status: str = Field(..., description="Statut du job")
    processing_mode: str = Field(..., description="Mode de traitement utilisé")
    upscale_factor: Optional[float] = Field(None, ge=1.0, le=16.0, description="Facteur d'upscaling")
    hdr_enabled: Optional[bool] = Field(None, description="HDR activé")
    processing_time_ms: Optional[float] = Field(None, ge=0.0, description="Temps de traitement en ms")
    result_url: Optional[str] = Field(None, description="URL du résultat")
    error_message: Optional[str] = Field(None, description="Message d'erreur")
    estimated_processing_time: Optional[float] = Field(None, description="Temps estimé en secondes")
    message: Optional[str] = Field(None, description="Message informatif")
    created_at: Optional[str] = Field(None, description="Date de création")
    completed_at: Optional[str] = Field(None, description="Date de complétion")

# ----------------------------------------------------------------------------
# SESSION SCHEMAS
# ----------------------------------------------------------------------------

class ChatSession(BaseModel):
    """Session de chat"""
    id: str = Field(..., description="ID de la session")
    user_id: str = Field(..., description="ID de l'utilisateur")
    title: Optional[str] = Field(None, description="Titre de la session")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: datetime = Field(..., description="Date de mise à jour")
    message_count: int = Field(default=0, description="Nombre de messages")
    last_message: Optional[str] = Field(None, description="Dernier message")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Métadonnées")

class ConversationHistory(BaseModel):
    """Historique de conversation"""
    conversation_id: str = Field(..., description="ID de la conversation")
    messages: List[ChatMessage] = Field(..., description="Messages de la conversation")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: datetime = Field(..., description="Date de mise à jour")
    summary: Optional[str] = Field(None, description="Résumé de la conversation")

# ----------------------------------------------------------------------------
# METRICS SCHEMAS
# ----------------------------------------------------------------------------

class ProcessingMetrics(BaseModel):
    """Métriques de traitement"""
    job_id: str = Field(..., description="ID du job")
    service_type: str = Field(..., description="Type de service (audio/video/chat)")
    processing_time_ms: float = Field(..., ge=0.0, description="Temps de traitement")
    quality_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Score de qualité")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="Taux de succès")
    error_count: int = Field(default=0, description="Nombre d'erreurs")
    timestamp: datetime = Field(..., description="Timestamp des métriques")

class UsageMetrics(BaseModel):
    """Métriques d'utilisation"""
    user_id: str = Field(..., description="ID de l'utilisateur")
    date: str = Field(..., description="Date des métriques")
    audio_minutes: float = Field(default=0.0, description="Minutes audio traitées")
    video_minutes: float = Field(default=0.0, description="Minutes vidéo traitées")
    api_calls: int = Field(default=0, description="Nombre d'appels API")
    total_cost: float = Field(default=0.0, description="Coût total")
    subscription_tier: str = Field(..., description="Niveau d'abonnement")

# ----------------------------------------------------------------------------
# HEALTH SCHEMAS
# ----------------------------------------------------------------------------

class ServiceHealth(BaseModel):
    """Santé d'un service"""
    service: str = Field(..., description="Nom du service")
    status: str = Field(..., description="Statut (healthy/unhealthy/unreachable)")
    response_time_ms: Optional[float] = Field(None, description="Temps de réponse")
    status_code: Optional[int] = Field(None, description="Code de statut HTTP")
    error: Optional[str] = Field(None, description="Message d'erreur")
    timestamp: datetime = Field(..., description="Timestamp du check")

class HealthStatus(BaseModel):
    """Statut de santé global"""
    timestamp: datetime = Field(..., description="Timestamp du check")
    overall_status: str = Field(..., description="Statut global")
    services: Dict[str, ServiceHealth] = Field(..., description="Santé des services")

# ----------------------------------------------------------------------------
# ERROR SCHEMAS
# ----------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    """Réponse d'erreur"""
    success: bool = Field(False, description="Succès de l'opération")
    error: str = Field(..., description="Message d'erreur")
    error_code: Optional[str] = Field(None, description="Code d'erreur")
    details: Optional[Dict[str, Any]] = Field(None, description="Détails de l'erreur")
    timestamp: datetime = Field(..., description="Timestamp de l'erreur")
    
    @validator('timestamp', pre=True, always=True)
    def set_timestamp(cls, v):
        return v or datetime.utcnow()