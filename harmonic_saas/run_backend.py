#!/usr/bin/env python3
"""Script de lancement du backend FastAPI avec SQLite"""
import os
import sys
import uvicorn

# Configuration pour SQLite
os.environ["DATABASE_URL"] = "sqlite:///./harmonic_saas.db"
os.environ["JWT_SECRET_KEY"] = "dev-secret-key-harmonic-ai-2026"
os.environ["BACKEND_CORS_ORIGINS"] = '["http://localhost:8080","http://localhost:3000","http://localhost:9000"]'

if __name__ == "__main__":
    print("=" * 60)
    print("  HARMONIC AI SAAS - Backend API")
    print("=" * 60)
    print(f"  Mode base de donnÃ©es : SQLite")
    print(f"  API disponible sur    : http://localhost:9000")
    print(f"  Documentation API     : http://localhost:9000/docs")
    print(f"  Backend DeepSeek AWS  : http://__EC2_IP__:8000")
    print("=" * 60)
    print()
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=9000,
        reload=True,
        log_level="info"
    )
