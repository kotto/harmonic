#!/usr/bin/env python3
"""
Interface Web Harmonic Studio
Version parallèle dédiée - Sans modifier l'intégration actuelle
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import threading
import json
from deepseek_harmonic_patch import DeepseekHarmonicPatcher
from deepseek_continuous_movie_generator import Scene

app = FastAPI(title="Harmonic Studio")

# Initialisation système en arrière plan
generator = None
init_thread = None

class SceneRequest(BaseModel):
    description: str
    duration: float = 30.0
    camera: str = "fixed"

@app.on_event("startup")
async def startup_event():
    global generator, init_thread
    def init_system():
        global generator
        model, tokenizer, generator = DeepseekHarmonicPatcher().run_full_process()
    init_thread = threading.Thread(target=init_system, daemon=True)
    init_thread.start()

@app.get("/", response_class=HTMLResponse)
async def get_interface():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Harmonic Studio</title>
    <meta charset="utf-8">
    <style>
        * { margin:0; padding:0; box-sizing:border-box; font-family: system-ui; }
        body { background:#0a0a0f; color:#fff; min-height:100vh; }
        .container { max-width:1400px; margin:0 auto; padding:40px 20px; }
        .header { text-align:center; margin-bottom:60px; }
        .logo { font-size:42px; font-weight:700; background:linear-gradient(135deg, #7928ca, #ff0080); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:10px; }
        .subtitle { color:#888; font-size:16px; }
        .prompt_area { margin-bottom:40px; }
        textarea { width:100%; height:120px; background:#121218; border:1px solid #2a2a35; border-radius:12px; padding:20px; color:#fff; font-size:16px; resize:none; margin-bottom:20px; }
        .controls { display:grid; grid-template-columns: 1fr 1fr 200px; gap:20px; margin-bottom:30px; }
        input { background:#121218; border:1px solid #2a2a35; border-radius:8px; padding:14px; color:#fff; }
        button { background:linear-gradient(135deg, #7928ca, #ff0080); border:none; border-radius:12px; padding:16px 32px; color:#fff; font-size:16px; font-weight:600; cursor:pointer; }
        .status { background:#121218; border-radius:12px; padding:24px; margin-top:40px; }
        .status_line { display:flex; justify-content:space-between; padding:12px 0; border-bottom:1px solid #1f1f28; }
        .progress { height:6px; background:#1f1f28; border-radius:3px; margin-top:20px; overflow:hidden; }
        .progress_bar { height:100%; background:linear-gradient(90deg, #7928ca, #ff0080); width:0%; transition:width 0.3s; }
        .preview { margin-top:40px; border-radius:12px; overflow:hidden; aspect-ratio:16/9; background:#000; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">HARMONIC STUDIO</div>
            <div class="subtitle">Générateur de Films Illimité 8K 192kHz</div>
        </div>

        <div class="prompt_area">
            <textarea id="prompt" placeholder="Décrivez la scène que vous voulez générer..."></textarea>
            
            <div class="controls">
                <input type="number" id="duration" value="30" placeholder="Durée en secondes">
                <input type="text" id="camera" value="fixed" placeholder="Mouvement caméra">
                <button onclick="generate()">🎬 GÉNÉRER</button>
            </div>
        </div>

        <div class="status">
            <div class="status_line">
                <span>État système</span>
                <span id="status_text">Initialisation...</span>
            </div>
            <div class="status_line">
                <span>Progression</span>
                <span id="progress_text">0%</span>
            </div>
            <div class="progress">
                <div class="progress_bar" id="progress_bar"></div>
            </div>
        </div>

        <div class="preview">
            <video id="video_player" controls style="width:100%; height:100%; display:none;"></video>
        </div>
    </div>

    <script>
        async function check_status() {
            const res = await fetch('/api/status')
            const data = await res.json()
            document.getElementById('status_text').textContent = data.status
            
            if(data.progress) {
                document.getElementById('progress_bar').style.width = data.progress + '%'
                document.getElementById('progress_text').textContent = data.progress + '%'
            }
        }
        
        async function generate() {
            const prompt = document.getElementById('prompt').value
            const duration = parseFloat(document.getElementById('duration').value)
            const camera = document.getElementById('camera').value
            
            await fetch('/api/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({description: prompt, duration: duration, camera: camera})
            })
        }
        
        setInterval(check_status, 1000)
    </script>
</body>
</html>
    """

@app.get("/api/status")
async def get_status():
    if not generator:
        return {"status": "Chargement du modèle en cours...", "progress": None}
    return {"status": "Prêt", "progress": 0}

@app.post("/api/generate")
async def generate_scene(scene: SceneRequest):
    if not generator:
        return {"error": "Système pas prêt"}
    
    def generate_background():
        generator.play_scene(Scene(
            description=scene.description,
            duration=scene.duration,
            camera=scene.camera
        ))
    
    threading.Thread(target=generate_background, daemon=True).start()
    return {"status": "ok"}

def run_interface():
    # Fix encodage UTF8 Windows
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    
    print("\nDemarrage Interface Web Harmonic Studio")
    print("Interface disponible sur http://localhost:7860")
    print("Version parallele dediee, sans modifier l'integration actuelle")
    uvicorn.run(app, host="0.0.0.0", port=7860, log_level="error")

if __name__ == "__main__":
    run_interface()