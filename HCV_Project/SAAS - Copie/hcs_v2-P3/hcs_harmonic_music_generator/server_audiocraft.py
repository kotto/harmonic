#!/usr/bin/env python3
"""
HCS AudioCraft Server - Serveur Web avec intégration Meta AudioCraft
Interface FastAPI pour la génération musicale HCS + AudioCraft
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

from hcs_audio_craft import HCSAudioCraft

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialisation FastAPI
app = FastAPI(
    title="HCS AudioCraft - Advanced Harmonic Music Generator",
    description="Génération IA de musique harmonique avec Meta AudioCraft/MusicGen",
    version="2.0.0"
)

# Configuration templates
templates = Jinja2Templates(directory="templates")

# Répertoire de sortie
OUTPUT_DIR = Path("generated_music")
OUTPUT_DIR.mkdir(exist_ok=True)

# Générateur HCS AudioCraft
hcs_audiocraft = HCSAudioCraft()

# Stockage des générations
generated_tracks = {}

@app.get("/", response_class=HTMLResponse)
async def home():
    """Page d'accueil"""
    return FileResponse("templates/index_audiocraft.html")

@app.post("/api/generate-audiocraft")
async def generate_music_audiocraft(
    description: str = Form("upbeat pop song with piano and drums"),
    style: str = Form("pop"),
    key: str = Form("C"),
    tempo: int = Form(120),
    duration: float = Form(30.0),
    use_hcs_enhancement: bool = Form(True),
    apply_mastering: bool = Form(True)
):
    """
    Génère une piste musicale avec HCS + AudioCraft
    """
    try:
        logger.info(f"Génération HCS-AudioCraft: {description[:50]}...")
        
        # Génération de la musique
        start_time = time.time()
        
        if use_hcs_enhancement:
            # Mode HCS + AudioCraft
            signal = hcs_audiocraft.generate_hcs_enhanced(
                description=description,
                style=style,
                key=key,
                tempo=tempo,
                duration=duration
            )
        else:
            # Mode AudioCraft pur
            import torch
            audio_craft = hcs_audiocraft.generate_with_audiocraft(description, duration)
            signal = audio_craft.numpy()
            if len(signal.shape) > 1:
                signal = np.mean(signal, axis=0)
        
        generation_time = time.time() - start_time
        
        # Analyse harmonique complète
        analysis = hcs_audiocraft.analyze_harmonic_content(signal)
        
        # Sauvegarde du fichier
        timestamp = int(time.time())
        filename = f"hcs_audiocraft_{style}_{timestamp}.wav"
        filepath = OUTPUT_DIR / filename
        
        hcs_audiocraft.save_audio(signal, str(filepath))
        
        # Stockage des informations
        track_id = f"track_{timestamp}"
        generated_tracks[track_id] = {
            "filename": filename,
            "filepath": str(filepath),
            "description": description,
            "style": style,
            "key": key,
            "tempo": tempo,
            "duration": duration,
            "use_hcs_enhancement": use_hcs_enhancement,
            "apply_mastering": apply_mastering,
            "generation_time": generation_time,
            "analysis": analysis,
            "file_size": os.path.getsize(filepath),
            "timestamp": timestamp,
            "model": "HCS-AudioCraft"
        }
        
        logger.info(f"Musique HCS-AudioCraft générée: {filename} ({generation_time:.2f}s)")
        
        return {
            "success": True,
            "track_id": track_id,
            "filename": filename,
            "description": description,
            "style": style,
            "key": key,
            "tempo": tempo,
            "duration": duration,
            "use_hcs_enhancement": use_hcs_enhancement,
            "apply_mastering": apply_mastering,
            "generation_time": generation_time,
            "file_size": os.path.getsize(filepath),
            "analysis": analysis,
            "model": "HCS-AudioCraft",
            "download_url": f"/api/download/{track_id}"
        }
        
    except Exception as e:
        logger.error(f"Erreur génération HCS-AudioCraft: {e}")
        raise HTTPException(status_code=500, detail=f"Génération échouée: {e}")

@app.post("/api/generate-description")
async def generate_from_description(
    description: str = Form("epic orchestral music with strings and brass"),
    duration: float = Form(30.0),
    use_hcs_enhancement: bool = Form(True)
):
    """
    Génère de la musique à partir d'une description textuelle
    """
    try:
        logger.info(f"Génération depuis description: {description[:50]}...")
        
        # Génération
        start_time = time.time()
        
        if use_hcs_enhancement:
            signal = hcs_audiocraft.generate_hcs_enhanced(
                description=description,
                style="classical",  # Par défaut pour descriptions
                key="C",
                tempo=120,
                duration=duration
            )
        else:
            import torch
            audio_craft = hcs_audiocraft.generate_with_audiocraft(description, duration)
            signal = audio_craft.numpy()
            if len(signal.shape) > 1:
                signal = np.mean(signal, axis=0)
        
        generation_time = time.time() - start_time
        
        # Analyse
        analysis = hcs_audiocraft.analyze_harmonic_content(signal)
        
        # Sauvegarde
        timestamp = int(time.time())
        filename = f"desc_{timestamp}.wav"
        filepath = OUTPUT_DIR / filename
        
        hcs_audiocraft.save_audio(signal, str(filepath))
        
        # Stockage
        track_id = f"track_{timestamp}"
        generated_tracks[track_id] = {
            "filename": filename,
            "filepath": str(filepath),
            "description": description,
            "style": "description-based",
            "key": "auto-detected",
            "tempo": analysis.get("tempo", 120),
            "duration": duration,
            "use_hcs_enhancement": use_hcs_enhancement,
            "generation_time": generation_time,
            "analysis": analysis,
            "file_size": os.path.getsize(filepath),
            "timestamp": timestamp,
            "model": "HCS-AudioCraft-Text"
        }
        
        return {
            "success": True,
            "track_id": track_id,
            "filename": filename,
            "description": description,
            "generation_time": generation_time,
            "file_size": os.path.getsize(filepath),
            "analysis": analysis,
            "download_url": f"/api/download/{track_id}"
        }
        
    except Exception as e:
        logger.error(f"Erreur génération description: {e}")
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
        "total": len(generated_tracks),
        "models": list(set(track.get("model", "unknown") for track in generated_tracks.values()))
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

@app.get("/api/models")
async def get_available_models():
    """Modèles disponibles"""
    return {
        "models": {
            "hcs_audiocraft": {
                "name": "HCS AudioCraft",
                "description": "Combinaison HCS + Meta AudioCraft",
                "features": ["Génération harmonique", "Enhancement HCS", "Mastering", "Compression"],
                "quality": "Professionnelle"
            },
            "audiocraft_pure": {
                "name": "AudioCraft Pur",
                "description": "Meta AudioCraft sans enhancement",
                "features": ["Génération IA", "Haute qualité", "Multiple styles"],
                "quality": "Élevée"
            },
            "hcs_pure": {
                "name": "HCS Pur",
                "description": "Génération harmonique pure",
                "features": ["Séries harmoniques", "Algorithmes HCS", "Optimisation temporelle"],
                "quality": "Expérimentale"
            }
        },
        "current_model": "HCS AudioCraft",
        "device": hcs_audiocraft.device,
        "sample_rate": hcs_audiocraft.sample_rate
    }

@app.get("/api/analyze-advanced/{track_id}")
async def advanced_analysis(track_id: str):
    """Analyse harmonique avancée"""
    if track_id not in generated_tracks:
        raise HTTPException(status_code=404, detail="Piste non trouvée")
    
    track_info = generated_tracks[track_id]
    
    try:
        # Charger l'audio pour analyse approfondie
        import librosa
        y, sr = librosa.load(track_info["filepath"])
        
        # Analyse spectrale avancée
        stft = librosa.stft(y, n_fft=4096, hop_length=1024)
        magnitude = np.abs(stft)
        
        # Analyse harmonique détaillée
        harmonic_analysis = hcs_audiocraft.analyze_harmonic_content(y)
        
        # Analyse temporelle
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
        
        # Analyse tonale
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        key_estimation = np.argmax(np.mean(chroma, axis=1))
        
        # Analyse spectrale
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        
        # Analyse harmonique/pércussive
        harmonic, percussive = librosa.effects.hpss(y)
        
        advanced_analysis = {
            "temporal_analysis": {
                "tempo": float(tempo),
                "beat_frames": beats.tolist(),
                "onset_frames": onset_frames.tolist(),
                "beat_strength": float(np.mean(librosa.onset.onset_strength(y=y, sr=sr)))
            },
            "tonal_analysis": {
                "estimated_key": int(key_estimation),
                "key_name": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"][key_estimation],
                "chroma_profile": np.mean(chroma, axis=1).tolist(),
                "tonal_centroid": float(np.mean(spectral_centroids)),
                "modulation_detection": float(np.std(np.mean(chroma, axis=1)))
            },
            "spectral_analysis": {
                "spectral_centroids": spectral_centroids.tolist(),
                "spectral_rolloff": spectral_rolloff.tolist(),
                "spectral_bandwidth": spectral_bandwidth.tolist(),
                "spectral_flux": float(np.mean(np.diff(magnitude, axis=1))),
                "zero_crossing_rate": float(librosa.feature.zero_crossing_rate(y))
            },
            "harmonic_analysis": harmonic_analysis,
            "source_separation": {
                "harmonic_ratio": float(np.mean(harmonic**2) / (np.mean(harmonic**2) + np.mean(percussive**2))),
                "percussive_ratio": float(np.mean(percussive**2) / (np.mean(harmonic**2) + np.mean(percussive**2)))
            }
        }
        
        return {
            "track_info": track_info,
            "advanced_analysis": advanced_analysis
        }
        
    except Exception as e:
        logger.error(f"Erreur analyse avancée: {e}")
        return {
            "track_info": track_info,
            "basic_analysis": track_info.get("analysis", {}),
            "error": str(e)
        }

@app.get("/api/health")
async def health_check():
    """Vérification de santé du serveur"""
    return {
        "status": "healthy",
        "generator": "HCS AudioCraft",
        "version": "2.0.0",
        "device": hcs_audiocraft.device,
        "sample_rate": hcs_audiocraft.sample_rate,
        "audiocraft_available": hcs_audiocraft.musicgen_model is not None,
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
    
    print("🎵 HCS AudioCraft Starting...")
    print("=" * 50)
    print(f"📊 Configuration:")
    print(f"   Device: {hcs_audiocraft.device}")
    print(f"   Sample Rate: {hcs_audiocraft.sample_rate}Hz")
    print(f"   AudioCraft: {'✅' if hcs_audiocraft.musicgen_model else '❌'}")
    print(f"   Output Directory: {OUTPUT_DIR}")
    print(f"   Web Interface: http://localhost:8021")
    print(f"   API Documentation: http://localhost:8021/docs")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8021)
