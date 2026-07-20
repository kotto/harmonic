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
    resolver,     # Résoluteur Universel Harmonique
    datacenter,   # Datacenter Holographique
    hpc,          # HPC / Calcul Scientifique
    knowledge,    # Base de Connaissances
    reasoning,    # Raisonnement Conscient
    code,         # Code Intelligent
    wave,         # Wave & Créativité
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat & LM Arena"])
api_router.include_router(audio.router, prefix="/audio", tags=["Audio Processing"])
api_router.include_router(video.router, prefix="/video", tags=["Video Processing"])
api_router.include_router(subscription.router, prefix="/subscription", tags=["Subscription & Billing"])
api_router.include_router(resolver.router, prefix="/resolver", tags=["Resolver"])
api_router.include_router(datacenter.router, prefix="/datacenter", tags=["Datacenter Holographique"])
api_router.include_router(hpc.router, prefix="/hpc", tags=["HPC / Calcul Scientifique"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["Base de Connaissances"])
api_router.include_router(reasoning.router, prefix="/reasoning", tags=["Raisonnement Conscient"])
api_router.include_router(code.router, prefix="/code", tags=["Code Intelligent"])
api_router.include_router(wave.router, prefix="/wave", tags=["Wave & Créativité"])
