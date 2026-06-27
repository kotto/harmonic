"""
API REST — Serveur FastAPI pour le moteur harmonique complet.
==============================================================
Expose les fonctionnalites du moteur harmonique via API REST.

Endpoints:
    POST /api/analyze       → Analyse harmonique d'un prompt
    POST /api/classify      → Classification d'un prompt
    POST /api/generate      → Generation via LLM avec routage harmonique
    POST /api/chat          → Chat complet avec contexte et memoire
    POST /api/expand        → Expansion harmonique de contexte
    GET  /api/stats         → Statistiques du moteur
    GET  /api/health        → Health check
"""

from .server import HarmonicAPI, create_app, run_server

__all__ = ['HarmonicAPI', 'create_app', 'run_server']
