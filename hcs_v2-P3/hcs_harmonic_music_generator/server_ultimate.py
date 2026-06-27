#!/usr/bin/env python3
"""
HCS Ultimate Audio Server - Serveur Web pour la meilleure IA audio
Port 8023 : Interface ultime avec toutes les technologies
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
import json

# Import du moteur ultime
from ultimate_hcs_engine import UltimateHCSEngine

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialisation FastAPI
app = FastAPI(
    title="HCS Ultimate Audio Engine",
    description="La meilleure IA audio du marché - 192kHz/32-bit, 7.1.4 surround",
    version="4.0.0"
)

# Configuration templates
templates = Jinja2Templates(directory="templates")

# Répertoire de sortie
OUTPUT_DIR = Path("ultimate_music")
OUTPUT_DIR.mkdir(exist_ok=True)

# Moteur ultime
ultimate_engine = UltimateHCSEngine()

# Stockage des générations ultimes
ultimate_tracks = {}

@app.get("/", response_class=HTMLResponse)
async def home():
    """Page d'accueil ultime"""
    return FileResponse("templates/index_ultimate.html")

@app.post("/api/generate-ultimate")
async def generate_ultimate_music(
    description: str = Form("ultimate cinematic orchestral music with full orchestra, choirs, and advanced spatial processing"),
    style: str = Form("ultimate"),
    duration: float = Form(180.0),
    quality_preset: str = Form("ultra"),
    spatial_format: str = Form("7.1.4"),
    enable_multi_ai: bool = Form(True),
    enable_hcs_enhancement: bool = Form(True),
    enable_french_processing: bool = Form(False)
):
    """
    Génère de la musique avec le moteur ultime HCS
    """
    try:
        logger.info(f"🚀 Génération ultime: {style}, {duration}s, qualité {quality_preset}")
        
        # Configuration de génération
        generation_config = {
            'description': description,
            'style': style,
            'duration': duration,
            'quality_preset': quality_preset,
            'spatial_format': spatial_format,
            'enable_multi_ai': enable_multi_ai,
            'enable_hcs_enhancement': enable_hcs_enhancement,
            'enable_french_processing': enable_french_processing
        }
        
        # Génération ultime
        start_time = time.time()
        result = ultimate_engine.generate_ultimate_music(
            description=description,
            style=style,
            duration=duration,
            quality_preset=quality_preset
        )
        
        generation_time = time.time() - start_time
        
        if not result.get("success", False):
            raise Exception(result.get("error", "Erreur génération ultime"))
        
        # Sauvegarde du fichier ultime
        timestamp = int(time.time())
        filename = f"ultimate_{style}_{timestamp}.wav"
        filepath = OUTPUT_DIR / filename
        
        ultimate_engine.save_ultimate_audio(
            result["audio"], 
            str(filepath),
            format="wav",
            metadata={
                "generation_config": generation_config,
                "generation_time": generation_time,
                "quality_metrics": result.get("quality_metrics", {}),
                "technical_specs": result.get("technical_specs", {})
            }
        )
        
        # Stockage des informations
        track_id = f"ultimate_{timestamp}"
        ultimate_tracks[track_id] = {
            "filename": filename,
            "filepath": str(filepath),
            "description": description,
            "style": style,
            "duration": duration,
            "quality_preset": quality_preset,
            "spatial_format": spatial_format,
            "generation_config": generation_config,
            "generation_time": generation_time,
            "quality_metrics": result.get("quality_metrics", {}),
            "technical_specs": result.get("technical_specs", {}),
            "file_size": os.path.getsize(filepath),
            "timestamp": timestamp,
            "model": "HCS Ultimate Audio Engine",
            "version": "4.0.0"
        }
        
        logger.info(f"✅ Musique ultime générée: {filename} ({generation_time:.2f}s)")
        
        return {
            "success": True,
            "track_id": track_id,
            "filename": filename,
            "description": description,
            "style": style,
            "duration": duration,
            "quality_preset": quality_preset,
            "spatial_format": spatial_format,
            "generation_config": generation_config,
            "generation_time": generation_time,
            "file_size": os.path.getsize(filepath),
            "quality_metrics": result.get("quality_metrics", {}),
            "technical_specs": result.get("technical_specs", {}),
            "model": "HCS Ultimate Audio Engine",
            "version": "4.0.0",
            "download_url": f"/api/download/{track_id}"
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur génération ultime: {e}")
        raise HTTPException(status_code=500, detail=f"Génération ultime échouée: {e}")

@app.get("/api/download/{track_id}")
async def download_track(track_id: str):
    """Télécharge une piste ultime"""
    if track_id not in ultimate_tracks:
        raise HTTPException(status_code=404, detail="Piste ultime non trouvée")
    
    track_info = ultimate_tracks[track_id]
    filepath = track_info["filepath"]
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Fichier ultime non trouvé")
    
    return FileResponse(
        filepath,
        media_type="audio/wav",
        filename=track_info["filename"]
    )

@app.get("/api/tracks")
async def list_tracks():
    """Liste toutes les pistes ultimes"""
    return {
        "tracks": ultimate_tracks,
        "total": len(ultimate_tracks),
        "ultimate_styles": list(set(track.get("style", "unknown") for track in ultimate_tracks.values())),
        "quality_presets": list(set(track.get("quality_preset", "unknown") for track in ultimate_tracks.values())),
        "technical_specs": {
            "sample_rate": ultimate_engine.sample_rate,
            "bit_depth": ultimate_engine.bit_depth,
            "channels": ultimate_engine.ultimate_config['channels'],
            "spatial_format": ultimate_engine.ultimate_config['spatial_resolution'],
            "dynamic_range": ultimate_engine.ultimate_config['dynamic_range']
        }
    }

@app.get("/api/track/{track_id}")
async def get_track_info(track_id: str):
    """Informations détaillées sur une piste ultime"""
    if track_id not in ultimate_tracks:
        raise HTTPException(status_code=404, detail="Piste ultime non trouvée")
    
    return ultimate_tracks[track_id]

@app.delete("/api/track/{track_id}")
async def delete_track(track_id: str):
    """Supprime une piste ultime"""
    if track_id not in ultimate_tracks:
        raise HTTPException(status_code=404, detail="Piste ultime non trouvée")
    
    track_info = ultimate_tracks[track_id]
    filepath = track_info["filepath"]
    
    # Suppression du fichier
    if os.path.exists(filepath):
        os.remove(filepath)
    
    # Suppression des métadonnées
    del ultimate_tracks[track_id]
    
    logger.info(f"🗑️ Piste ultime supprimée: {track_id}")
    
    return {"success": True, "message": "Piste ultime supprimée"}

@app.get("/api/ultimate-styles")
async def get_ultimate_styles():
    """Styles ultimes disponibles"""
    return {
        "styles": {
            "ultimate": {
                "name": "Ultimate",
                "description": "Qualité maximale avec toutes les technologies",
                "characteristics": [
                    "192kHz/32-bit ultra HD",
                    "7.1.4 Dolby Atmos",
                    "Multi-IA fusion",
                    "HCS enhancement",
                    "120dB dynamique"
                ],
                "use_cases": ["Cinéma Hollywood", "Production musicale professionnelle", "Mastering ultime"]
            },
            "cinema": {
                "name": "Cinéma Épique",
                "description": "Orchestre cinématographique avec spatialisation 3D",
                "characteristics": ["Orchestre complet", "Chœurs puissants", "Spatial 7.1.4", "Mastering cinéma"],
                "use_cases": ["Films épique", "Bandes-annonces", "Documentaires"]
            },
            "electronic": {
                "name": "Électronique Ultime",
                "description": "Musique électronique avec synthèse avancée",
                "characteristics": ["Synthétiseurs avancés", "Basses profondes", "Effets spatiaux", "Rythmes complexes"],
                "use_cases": ["Musique de danse", "Ambient", "Expérimental"]
            },
            "orchestral": {
                "name": "Orchestral Professionnel",
                "description": "Musique orchestrale de niveau concert",
                "characteristics": ["Enregistrement orchestre", "Acoustique naturelle", "Dynamique étendue"],
                "use_cases": ["Musique classique", "Concert", "Opéra"]
            },
            "hybrid": {
                "name": "Hybrid Avancé",
                "description": "Fusion de tous les styles avec IA multi-moteurs",
                "characteristics": ["Multi-IA fusion", "Styles mélangés", "Innovation créative"],
                "use_cases": ["Projets expérimentaux", "Musique unique", "Création artistique"]
            }
        },
        "quality_presets": {
            "ultra": {
                "name": "Ultra Qualité",
                "description": "192kHz/32-bit, 7.1.4, 120dB dynamique",
                "target_use": "Cinéma Hollywood, Mastering professionnel"
            },
            "professional": {
                "name": "Professionnel",
                "description": "96kHz/24-bit, 5.1, 90dB dynamique",
                "target_use": "Production musicale, Broadcast"
            },
            "broadcast": {
                "name": "Broadcast",
                "description": "48kHz/24-bit, Stéréo, 60dB dynamique",
                "target_use": "Radio, Streaming, TV"
            },
            "standard": {
                "name": "Standard",
                "description": "44.1kHz/16-bit, Stéréo, 40dB dynamique",
                "target_use": "Usage général, Mobile"
            }
        },
        "spatial_formats": {
            "7.1.4": {
                "name": "Dolby Atmos 7.1.4",
                "description": "7.1 surround + 4 canaux hauteur",
                "speakers": "Front L/R, Center, Surround L/R, Back L/R, Height L/R, Top Front, Top Rear"
            },
            "5.1": {
                "name": "Surround 5.1",
                "description": "5 canaux surround + subwoofer",
                "speakers": "Front L/R, Center, Surround L/R, Subwoofer"
            },
            "stereo": {
                "name": "Stéréo",
                "description": "2 canaux traditionnels",
                "speakers": "Left, Right"
            }
        }
    }

@app.get("/api/analyze-ultimate/{track_id}")
async def ultimate_analysis(track_id: str):
    """Analyse ultime complète d'une piste"""
    if track_id not in ultimate_tracks:
        raise HTTPException(status_code=404, detail="Piste ultime non trouvée")
    
    track_info = ultimate_tracks[track_id]
    
    try:
        # Analyse ultime avec le moteur
        ultimate_analysis = ultimate_engine.calculate_ultimate_quality_metrics(
            track_info.get("audio", np.zeros((2, 48000 * 60)))  # Placeholder
        )
        
        return {
            "track_info": track_info,
            "ultimate_analysis": ultimate_analysis,
            "professional_standards": ultimate_analysis.get("professional_standards", {}),
            "technical_validation": validate_ultimate_specs(track_info),
            "quality_score": ultimate_analysis.get("quality_score", 0.0)
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur analyse ultime: {e}")
        return {
            "track_info": track_info,
            "basic_analysis": track_info.get("quality_metrics", {}),
            "error": str(e)
        }

@app.get("/api/engines-status")
async def get_engines_status():
    """Statut de tous les moteurs intégrés"""
    engines_status = {}
    
    for engine_name, engine in ultimate_engine.engines.items():
        engines_status[engine_name] = {
            "loaded": engine is not None,
            "type": type(engine).__name__ if engine else "Not loaded",
            "status": "Active" if engine else "Inactive"
        }
    
    return {
        "engines": engines_status,
        "total_engines": len(ultimate_engine.engines),
        "active_engines": sum(1 for e in ultimate_engine.engines.values() if e is not None),
        "ultimate_config": ultimate_engine.ultimate_config,
        "musical_knowledge": {
            "scales": len(ultimate_engine.musical_knowledge.get('scales', {})),
            "chords": len(ultimate_engine.musical_knowledge.get('chords', {})),
            "progressions": len(ultimate_engine.musical_knowledge.get('progressions', {})),
            "instruments": len(ultimate_engine.musical_knowledge.get('instruments', {})),
            "genres": len(ultimate_engine.musical_knowledge.get('genres', {}))
        }
    }

@app.get("/api/health")
async def health_check():
    """Vérification de santé du serveur ultime"""
    return {
        "status": "healthy",
        "generator": "HCS Ultimate Audio Engine",
        "version": "4.0.0",
        "sample_rate": ultimate_engine.sample_rate,
        "bit_depth": ultimate_engine.bit_depth,
        "channels": ultimate_engine.ultimate_config['channels'],
        "spatial_format": ultimate_engine.ultimate_config['spatial_resolution'],
        "quality_standard": "Ultra Professional",
        "available_tracks": len(ultimate_tracks),
        "output_directory": str(OUTPUT_DIR),
        "engines_loaded": len([e for e in ultimate_engine.engines.values() if e is not None])
    }

def validate_ultimate_specs(track_info: Dict) -> Dict:
    """Valide les spécifications ultimes"""
    validation = {
        "sample_rate_valid": track_info.get("technical_specs", {}).get("sample_rate") == ultimate_engine.sample_rate,
        "bit_depth_valid": track_info.get("technical_specs", {}).get("bit_depth") == ultimate_engine.bit_depth,
        "channels_valid": track_info.get("technical_specs", {}).get("channels") == ultimate_engine.ultimate_config['channels'],
        "spatial_format_valid": track_info.get("spatial_format") in ["7.1.4", "5.1", "stereo"],
        "quality_preset_valid": track_info.get("quality_preset") in ["ultra", "professional", "broadcast", "standard"]
    }
    
    validation["overall_valid"] = all(validation.values())
    
    return validation

# Montage des fichiers statiques
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    # Création des répertoires nécessaires
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    
    print("🚀 HCS Ultimate Audio Server Starting...")
    print("=" * 70)
    print(f"🎛️ Ultimate Configuration:")
    print(f"   Sample Rate: {ultimate_engine.sample_rate}Hz (Ultra HD)")
    print(f"   Bit Depth: {ultimate_engine.bit_depth}-bit (Maximum Precision)")
    print(f"   Channels: {ultimate_engine.ultimate_config['channels']} (7.1.4 Surround)")
    print(f"   Spatial Format: {ultimate_engine.ultimate_config['spatial_resolution']}")
    print(f"   Dynamic Range: {ultimate_engine.ultimate_config['dynamic_range']}dB")
    print(f"   Quality Standard: Ultra Professional")
    print(f"   Output Directory: {OUTPUT_DIR}")
    print(f"   Web Interface: http://localhost:8023")
    print(f"   API Documentation: http://localhost:8023/docs")
    print("=" * 70)
    
    uvicorn.run(app, host="0.0.0.0", port=8023)
