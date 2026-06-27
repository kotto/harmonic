#!/usr/bin/env python3
"""
API Router Configuration
========================
Configuration des routes API pour le dashboard SaaS Harmonic AI
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    chat,
    audio,
    video,
    subscription,
    resolver  # Résoluteur Universel Harmonique
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat & LM Arena"])
api_router.include_router(audio.router, prefix="/audio", tags=["Audio Processing"])
api_router.include_router(video.router, prefix="/video", tags=["Video Processing"])
api_router.include_router(subscription.router, prefix="/subscription", tags=["Subscription & Billing"])
api_router.include_router(resolver.router, tags=["Resolver - Résolution Universelle Harmonique"])
