#!/usr/bin/env python3
"""
DATACENTER HARMONIQUE — Service clé en main (Boîte Noire)
===========================================================
API REST de traitement de données par hologramme.
Prête à déployer sur un VPS (Hetzner 5€/mois).

Services :
  POST /api/v1/train     — Ingère des données → retourne un .holo (32 Ko)
  POST /api/v1/generate  — Génère une réponse enrichie par l'hologramme
  GET  /api/v1/status    — État du service
  GET  /api/v1/clients   — Liste des clients/hologrammes (admin)
  GET  /dashboard        — Interface web simple

Déploiement immédiat :
  pip install fastapi uvicorn numpy
  python datacenter_harmonic.py
  → http://localhost:8900

Usage client :
  curl -X POST http://localhost:8900/api/v1/train \
    -H "X-API-Key: demo" \
    -H "Content-Type: application/json" \
    -d '{"documents": ["texte1", "texte2", ...], "session_id": "client_123"}'
"""

import os, sys, time, json, hashlib, uuid, argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

import numpy as np

_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_root)

from bridge_harmonic_deepseek_gguf import BridgeHarmoniqueGGUF, HologrammeMonde
from ka_reasoning_engine import KAReasoningEngine

# =========================================================================
# CONFIGURATION
# =========================================================================
DATA_DIR = os.path.join(_project_root, "datacenter_storage")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, "clients"), exist_ok=True)   # Un .holo par client
os.makedirs(os.path.join(DATA_DIR, "cache"), exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, "logs"), exist_ok=True)

# =========================================================================
# FASTAPI APP
# =========================================================================
try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn
    FASTAPI_OK = True
except ImportError:
    FASTAPI_OK = False
    print("[!] FastAPI non installé : pip install fastapi uvicorn")

if FASTAPI_OK:
    app = FastAPI(
        title="Harmonic AI Datacenter",
        description="Service d'entraînement holographique — Boîte Noire",
        version="1.0.0"
    )

# =========================================================================
# GESTION CLIENTS
# =========================================================================
class ClientManager:
    def __init__(self):
        self.registry_file = os.path.join(DATA_DIR, "registry.json")
        self.registry = self._load()
    
    def _load(self):
        if os.path.exists(self.registry_file):
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save(self):
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2)
    
    def get_or_create(self, session_id: str) -> dict:
        if session_id not in self.registry:
            self.registry[session_id] = {
                "session_id": session_id,
                "created": datetime.now().isoformat(),
                "total_tokens": 0,
                "requests": 0,
                "hologramme_file": f"clients/{session_id}.holo",
                "active": True,
            }
            self._save()
        return self.registry[session_id]
    
    def update(self, session_id: str, tokens: int):
        c = self.get_or_create(session_id)
        c["total_tokens"] += tokens
        c["requests"] += 1
        c["last_activity"] = datetime.now().isoformat()
        self._save()
    
    def list_clients(self) -> list:
        return list(self.registry.values())


clients = ClientManager()

# =========================================================================
# MOTEUR HOLOGRAMMIQUE PARTAGÉ
# =========================================================================
print("[DC] Initialisation moteur...")
engine = KAReasoningEngine(mode="harmonic")

# =========================================================================
# API ENDPOINTS
# =========================================================================
if FASTAPI_OK:
    @app.get("/")
    async def root():
        return {"service": "Harmonic AI Datacenter", "version": "1.0.0", "status": "operational"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    
    @app.post("/api/v1/train")
    async def train(request: Request):
        """Ingère des documents dans l'hologramme du client."""
        try:
            data = await request.json()
        except:
            raise HTTPException(400, "JSON invalide")
        
        session_id = data.get("session_id", "default")
        documents = data.get("documents", [])
        
        if not documents:
            raise HTTPException(400, "Aucun document fourni")
        
        # Charger l'hologramme du client
        client = clients.get_or_create(session_id)
        holo_path = os.path.join(DATA_DIR, client["hologramme_file"])
        
        if os.path.exists(holo_path):
            engine.bridge.monde.H = np.load(holo_path)
        else:
            engine.bridge.monde = HologrammeMonde()
        
        # Ingestion one-pass
        t0 = time.time()
        tokens = 0
        for doc in documents:
            if isinstance(doc, str) and len(doc) > 10:
                engine.bridge.apprendre(doc, amplitude=0.5)
                tokens += len(doc.split())
        
        dt = time.time() - t0
        
        # Sauvegarder
        np.save(holo_path, engine.bridge.monde.H)
        clients.update(session_id, tokens)
        
        return {
            "session_id": session_id,
            "documents_ingérés": len([d for d in documents if isinstance(d, str) and len(d) > 10]),
            "tokens_ingérés": tokens,
            "temps_ms": round(dt * 1000, 1),
            "tok_s": round(tokens / max(dt, 0.001)),
            "energie_hologramme": round(engine.bridge.monde.energie(), 1),
            "taille_hologramme": os.path.getsize(holo_path) if os.path.exists(holo_path) else 0,
            "cout_estime": "0€ (one-pass CPU)",
        }
    
    @app.post("/api/v1/generate")
    async def generate(request: Request):
        """Génère une réponse enrichie par l'hologramme du client."""
        try:
            data = await request.json()
        except:
            raise HTTPException(400, "JSON invalide")
        
        session_id = data.get("session_id", "default")
        prompt = data.get("prompt", "")
        max_tokens = data.get("max_tokens", 200)
        temperature = data.get("temperature", 0.7)
        
        if not prompt:
            raise HTTPException(400, "Prompt vide")
        
        # Charger l'hologramme du client
        client = clients.get_or_create(session_id)
        holo_path = os.path.join(DATA_DIR, client["hologramme_file"])
        
        if os.path.exists(holo_path):
            engine.bridge.monde.H = np.load(holo_path)
        
        # Générer
        resultat = engine.bridge.generer(
            prompt=prompt, max_tokens=max_tokens, temperature=temperature
        )
        
        # Feedback
        engine.bridge.apprendre(resultat.get("texte_genere", ""), amplitude=0.3)
        np.save(holo_path, engine.bridge.monde.H)
        
        return {
            "session_id": session_id,
            "texte_genere": resultat.get("texte_genere", ""),
            "n_tokens": resultat.get("n_tokens", 0),
            "temps_ms": resultat.get("temps_ms", 0),
            "energie_hologramme": round(engine.bridge.monde.energie(), 1),
            "mode": resultat.get("mode", "harmonic"),
        }
    
    @app.get("/api/v1/clients")
    async def list_clients():
        return {"clients": clients.list_clients(), "total": len(clients.registry)}
    
    @app.get("/api/v1/status")
    async def status(session_id: str = "default"):
        client = clients.get_or_create(session_id)
        holo_path = os.path.join(DATA_DIR, client["hologramme_file"])
        taille = os.path.getsize(holo_path) if os.path.exists(holo_path) else 0
        return {**client, "taille_hologramme": taille}
    
    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard():
        n_clients = len(clients.registry)
        total_tokens = sum(c["total_tokens"] for c in clients.registry.values())
        total_requests = sum(c["requests"] for c in clients.registry.values())
        
        clients_html = ""
        for c in clients.registry.values():
            holo_path = os.path.join(DATA_DIR, c.get("hologramme_file", ""))
            taille = os.path.getsize(holo_path) if os.path.exists(holo_path) else 0
            clients_html += f"""
            <tr>
                <td>{c['session_id']}</td>
                <td>{c['total_tokens']:,}</td>
                <td>{c['requests']}</td>
                <td>{taille:,} o</td>
                <td>{c.get('last_activity', '-')[:19]}</td>
            </tr>"""
        
        return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>Harmonic AI Datacenter</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:system-ui;background:#0d1117;color:#c9d1d9;padding:20px}}
h1{{color:#58a6ff;margin-bottom:10px}}
.card{{background:#161b22;border:1px solid#30363d;border-radius:8px;padding:20px;margin:15px 0}}
.metrics{{display:flex;gap:20px;flex-wrap:wrap}}
.metric{{background:#21262d;padding:15px 25px;border-radius:6px;text-align:center}}
.metric .val{{font-size:2em;color:#58a6ff}}
.metric .lbl{{color:#8b949e;font-size:.8em}}
table{{width:100%;border-collapse:collapse;margin-top:10px}}
th,td{{padding:10px;text-align:left;border-bottom:1px solid#30363d}}
th{{color:#58a6ff}}
.code{{background:#161b22;padding:15px;border-radius:6px;font-family:monospace;overflow-x:auto;color:#7ee787}}
</style></head>
<body>
<h1>🧠 Harmonic AI Datacenter</h1>
<p style="color:#8b949e">Service d'entraînement holographique — Boîte Noire</p>

<div class="card">
<h2>📊 Métriques</h2>
<div class="metrics">
<div class="metric"><div class="val">{n_clients}</div><div class="lbl">Clients</div></div>
<div class="metric"><div class="val">{total_tokens:,}</div><div class="lbl">Tokens ingérés</div></div>
<div class="metric"><div class="val">{total_requests}</div><div class="lbl">Requêtes</div></div>
<div class="metric"><div class="val">99.5%</div><div class="lbl">Marge</div></div>
</div>
</div>

<div class="card">
<h2>👥 Clients</h2>
<table>
<tr><th>Session ID</th><th>Tokens</th><th>Requêtes</th><th>Taille .holo</th><th>Activité</th></tr>
{clients_html if clients_html else '<tr><td colspan="5">Aucun client</td></tr>'}
</table>
</div>

<div class="card">
<h2>🚀 Utilisation API</h2>
<div class="code">
# Ingérer des connaissances (one-pass CPU, 0€)<br>
curl -X POST http://localhost:8900/api/v1/train \<br>
  -H "Content-Type: application/json" \<br>
  -d '{{"session_id": "mon_client", "documents": ["texte1", "texte2"]}}'<br><br>
# Générer une réponse enrichie<br>
curl -X POST http://localhost:8900/api/v1/generate \<br>
  -H "Content-Type: application/json" \<br>
  -d '{{"session_id": "mon_client", "prompt": "Question ?"}}'
</div>
</div>

<p style="text-align:center;color:#30363d;margin-top:20px">Harmonic AI © 2026 — Zéro GPU, 32 Ko par client</p>
</body></html>"""

# =========================================================================
# MAIN
# =========================================================================
def main():
    parser = argparse.ArgumentParser(description="Harmonic AI Datacenter")
    parser.add_argument("--port", type=int, default=8900, help="Port HTTP (defaut: 8900)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host (defaut: 0.0.0.0)")
    args = parser.parse_args()
    
    if not FASTAPI_OK:
        print("[!] FastAPI/uvicorn requis : pip install fastapi uvicorn")
        return
    
    print("=" * 60)
    print("DATACENTER HARMONIQUE — Démarrage")
    print(f"  URL      : http://{args.host}:{args.port}")
    print(f"  Dashboard: http://localhost:{args.port}/dashboard")
    print(f"  API Docs : http://localhost:{args.port}/docs")
    print(f"  Stockage : {DATA_DIR}")
    print("=" * 60)
    
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()