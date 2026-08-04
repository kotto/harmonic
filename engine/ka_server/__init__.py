"""
KA Server — API unifiée Harmonic AI + HCV Compression
=======================================================
Backend modulaire pour l'application KA (Mobile/PC/Enterprise).

Architecture :
  ka_server/
  ├── __init__.py           # Point d'entrée, création app Flask
  ├── routes/               # Endpoints API par domaine
  │   ├── __init__.py
  │   ├── chat.py           # /api/chat, /api/chat/voice
  │   ├── media.py          # /api/compress, /api/upscale, /api/enhance
  │   ├── agent.py          # /api/agent/*
  │   ├── enterprise.py     # /api/v2/enterprise/*
  │   ├── health.py         # /api/health/*
  │   ├── store.py          # /api/store/*
  │   ├── voice.py          # /api/voice/*
  │   ├── code.py           # /api/code/*
  │   ├── specialize.py     # /api/specialize/*
  │   └── system.py         # /api/health, /api/stats, /api/metrics
  ├── services/             # Services métier réutilisables
  │   ├── __init__.py
  │   ├── harmonic_ai.py    # Wrapper HarmonicAI + brain
  │   ├── hcv_codec.py      # Codec HCV (WASM + fallback serveur)
  │   ├── voice_engine.py   # Piper TTS + Vosk STT
  │   ├── hologram_store.py # HologramStore wrapper
  │   ├── specializer.py    # DomainSpecializer + OptimizedSpecializer
  │   └── web_retriever.py  # WebRetriever wrapper
  ├── middleware/           # Middleware Flask
  │   ├── __init__.py
  │   ├── metrics.py        # Métriques, logging, rate limiting
  │   └── auth.py           # Auth, API keys, audit
  └── models/               # Modèles de données partagés
      ├── __init__.py
      └── config.py         # Config produit (depuis ka_config)

Usage :
  from ka_server import create_app
  app = create_app()
  app.run(port=8765)
"""

from .app import create_app

__all__ = ['create_app']
__version__ = '4.0.0'