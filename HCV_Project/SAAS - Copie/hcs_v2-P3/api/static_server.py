#!/usr/bin/env python3
"""
Static File Server for HCS V2
Sert les fichiers frontend avec le bon chemin
"""

import os
import sys
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

# Ajout du chemin parent
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

app = FastAPI()

# Servir les fichiers statiques du frontend
frontend_path = os.path.join(parent_dir, "frontend")
if os.path.exists(frontend_path):
    app.mount("/frontend", StaticFiles(directory=frontend_path), name="frontend")
    print(f"Frontend static files mounted from: {frontend_path}")
else:
    print(f"Warning: Frontend directory not found at {frontend_path}")

# Route racine vers index.html
@app.get("/")
async def read_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))

@app.get("/dashboard")
async def read_dashboard():
    return FileResponse(os.path.join(frontend_path, "dashboard.html"))

# Health check
@app.get("/health")
async def health():
    return {"status": "ok", "message": "Static server running"}

if __name__ == "__main__":
    print("🚀 Démarrage Static File Server pour HCS V2")
    print("=" * 50)
    print("📁 Frontend: http://localhost:8001/frontend/")
    print("📊 Dashboard: http://localhost:8001/dashboard")
    print("🏠 Accueil: http://localhost:8001/")
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,  # Port différent pour éviter les conflits
        log_level="info"
    )
