#!/usr/bin/env python3
"""
HCS Harmonic Music Generator - Serveur Web
Interface FastAPI pour la génération de musique harmonique
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os
import tempfile
import base64
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any

from harmonic_engine import HarmonicGenerator

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialisation FastAPI
app = FastAPI(
    title="HCS Harmonic Music Generator",
    description="Génération IA de musique harmonique basée sur les principes HCS",
    version="1.0.0"
)

# Configuration templates
templates = Jinja2Templates(directory="templates")

# Répertoire de sortie
OUTPUT_DIR = Path("generated_music")
OUTPUT_DIR.mkdir(exist_ok=True)

# Générateur harmonique
harmonic_gen = HarmonicGenerator()

# Stockage des générations
generated_tracks = {}

@app.get("/", response_class=HTMLResponse)
async def home():
    """Page d'accueil"""
    return FileResponse("templates/index.html")

@app.post("/api/generate")
async def generate_music(
    style: str = Form("pop"),
    key: str = Form("C"),
    tempo: int = Form(120),
    duration: float = Form(30.0),
    scale: str = Form("major")
):
    """
    Génère une piste musicale harmonique
    """
    try:
        logger.info(f"Génération musicale: style={style}, key={key}, tempo={tempo}, duration={duration}")
        
        # Génération de la musique
        start_time = time.time()
        signal = harmonic_gen.generate_full_track(style, key, tempo, duration)
        generation_time = time.time() - start_time
        
        # Analyse harmonique
        analysis = harmonic_gen.analyze_harmonics(signal)
        
        # Sauvegarde du fichier
        timestamp = int(time.time())
        filename = f"harmonic_{style}_{key}_{timestamp}.wav"
        filepath = OUTPUT_DIR / filename
        
        harmonic_gen.save_audio(signal, str(filepath))
        
        # Stockage des informations
        track_id = f"track_{timestamp}"
        generated_tracks[track_id] = {
            "filename": filename,
            "filepath": str(filepath),
            "style": style,
            "key": key,
            "tempo": tempo,
            "duration": duration,
            "scale": scale,
            "generation_time": generation_time,
            "analysis": analysis,
            "file_size": os.path.getsize(filepath),
            "timestamp": timestamp
        }
        
        logger.info(f"Musique générée: {filename} ({generation_time:.2f}s)")
        
        return {
            "success": True,
            "track_id": track_id,
            "filename": filename,
            "style": style,
            "key": key,
            "tempo": tempo,
            "duration": duration,
            "generation_time": generation_time,
            "file_size": os.path.getsize(filepath),
            "analysis": analysis,
            "download_url": f"/api/download/{track_id}"
        }
        
    except Exception as e:
        logger.error(f"Erreur génération musicale: {e}")
        raise HTTPException(status_code=500, detail=f"Génération échouée: {e}")

@app.get("/api/download/{track_id}")
async def download_track(track_id: str):
    """Télécharge une piste générée"""
    if track_id not in generated_tracks:
        raise HTTPException(status_code=404, detail="Piste non trouvée")
    
    track_info = generated_tracks[track_id]
    filepath = track_info["filepath"]
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    
    return FileResponse(
        filepath,
        media_type="audio/wav",
        filename=track_info["filename"]
    )

@app.get("/api/tracks")
async def list_tracks():
    """Liste toutes les pistes générées"""
    return {
        "tracks": generated_tracks,
        "total": len(generated_tracks)
    }

@app.get("/api/track/{track_id}")
async def get_track_info(track_id: str):
    """Informations détaillées sur une piste"""
    if track_id not in generated_tracks:
        raise HTTPException(status_code=404, detail="Piste non trouvée")
    
    return generated_tracks[track_id]

@app.delete("/api/track/{track_id}")
async def delete_track(track_id: str):
    """Supprime une piste"""
    if track_id not in generated_tracks:
        raise HTTPException(status_code=404, detail="Piste non trouvée")
    
    track_info = generated_tracks[track_id]
    filepath = track_info["filepath"]
    
    # Suppression du fichier
    if os.path.exists(filepath):
        os.remove(filepath)
    
    # Suppression des métadonnées
    del generated_tracks[track_id]
    
    logger.info(f"Piste supprimée: {track_id}")
    
    return {"success": True, "message": "Piste supprimée"}

@app.get("/api/analyze/{track_id}")
async def analyze_track(track_id: str):
    """Analyse harmonique détaillée d'une piste"""
    if track_id not in generated_tracks:
        raise HTTPException(status_code=404, detail="Piste non trouvée")
    
    track_info = generated_tracks[track_id]
    
    # Analyse approfondie avec librosa
    try:
        import librosa
        
        # Charger l'audio
        y, sr = librosa.load(track_info["filepath"])
        
        # Analyse spectrale
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
        tempo_estimated, beats = librosa.beat.beat_track(y=y, sr=sr)
        
        # Analyse harmonique
        harmonic, percussive = librosa.effects.hpss(y)
        
        analysis = {
            "chroma": chroma.tolist(),
            "spectral_centroids": spectral_centroids.tolist(),
            "estimated_tempo": float(tempo_estimated),
            "beat_frames": beats.tolist(),
            "harmonic_ratio": float(np.mean(harmonic**2) / (np.mean(harmonic**2) + np.mean(percussive**2))),
            "key_detection": {
                "dominant_chroma": int(np.argmax(np.mean(chroma, axis=1))),
                "chroma_profile": np.mean(chroma, axis=1).tolist()
            }
        }
        
        return {
            "track_info": track_info,
            "advanced_analysis": analysis
        }
        
    except ImportError:
        # Fallback si librosa n'est pas disponible
        return {
            "track_info": track_info,
            "basic_analysis": track_info["analysis"]
        }

@app.get("/api/styles")
async def get_available_styles():
    """Styles musicaux disponibles"""
    return {
        "styles": {
            "pop": {
                "name": "Pop",
                "description": "Musique pop avec accords simples et mélodies entraînantes",
                "characteristics": ["Accords majeurs", "Mélodies accrocheuses", "Structure 4/4"]
            },
            "jazz": {
                "name": "Jazz",
                "description": "Musique jazz avec harmonies complexes et improvisations",
                "characteristics": ["Accords étendus", "Swing rythmique", "Improvisation"]
            },
            "classical": {
                "name": "Classique",
                "description": "Musique classique avec structures harmoniques traditionnelles",
                "characteristics": ["Progressions classiques", "Forme sonate", "Harmonie tonale"]
            },
            "electronic": {
                "name": "Électronique",
                "description": "Musique électronique avec synthèse harmonique",
                "characteristics": ["Synthétiseurs", "Basses profondes", "Rythmes programmés"]
            }
        },
        "scales": {
            "major": "Majeure",
            "minor": "Mineure", 
            "pentatonic": "Pentatonique",
            "blues": "Blues",
            "chromatic": "Chromatique"
        },
        "keys": list(harmonic_gen.fundamental_freqs.keys())
    }

@app.get("/api/health")
async def health_check():
    """Vérification de santé du serveur"""
    return {
        "status": "healthy",
        "generator": "HCS Harmonic Music Generator",
        "version": "1.0.0",
        "sample_rate": harmonic_gen.sample_rate,
        "available_tracks": len(generated_tracks),
        "output_directory": str(OUTPUT_DIR)
    }

# Montage des fichiers statiques
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    # Création des répertoires nécessaires
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    
    print("🎵 HCS Harmonic Music Generator Starting...")
    print("=" * 50)
    print(f"📊 Configuration:")
    print(f"   Sample Rate: {harmonic_gen.sample_rate}Hz")
    print(f"   Output Directory: {OUTPUT_DIR}")
    print(f"   Available Styles: pop, jazz, classical, electronic")
    print(f"   Web Interface: http://localhost:8020")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8020)
