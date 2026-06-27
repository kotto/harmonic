#!/usr/bin/env python3
"""
HCS Cinematic Sound Server - Serveur de bruitages cinématographiques
Interface web pour générer des bruitages cinéma haute qualité
"""

from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json

from cinematic_sound_designer import CinematicSoundDesigner

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialisation FastAPI
app = FastAPI(
    title="HCS Cinematic Sound Server",
    description="Génération de bruitages cinématographiques haute qualité",
    version="1.0.0"
)

# Configuration
OUTPUT_DIR = Path("cinematic_sounds")
OUTPUT_DIR.mkdir(exist_ok=True)

# Designer sonore cinématographique
sound_designer = CinematicSoundDesigner()

# Stockage des générations
cinematic_tracks = {}

@app.get("/", response_class=HTMLResponse)
async def home():
    """Page d'accueil design sonore cinématographique"""
    return FileResponse("templates/index_cinematic.html")

@app.post("/api/generate-cinematic-sound")
async def generate_cinematic_sound(
    category: str = Form(...),
    sound_type: str = Form(...),
    duration: float = Form(5.0),
    intensity: float = Form(0.5),
    spatial_front_center: float = Form(0.4),
    spatial_front_left: float = Form(0.3),
    spatial_front_right: float = Form(0.3),
    spatial_lfe: float = Form(0.2),
    spatial_rear_left: float = Form(0.2),
    spatial_rear_right: float = Form(0.2),
    apply_saturation: bool = Form(True),
    apply_reverb: bool = Form(True),
    custom_params: Optional[str] = Form(None)
):
    """
    Génère un son cinématographique de haute qualité
    """
    try:
        logger.info(f"🎬 Génération sonore cinéma: {category}/{sound_type}")
        
        start_time = time.time()
        
        # Préparation des paramètres
        parameters = {
            'intensity': intensity,
            'spatial': {
                'front_center': spatial_front_center,
                'front_left': spatial_front_left,
                'front_right': spatial_front_right,
                'lfe': spatial_lfe,
                'rear_left': spatial_rear_left,
                'rear_right': spatial_rear_right
            },
            'saturation': 0.7 if apply_saturation else 0.0,
            'reverb': 0.5 if apply_reverb else 0.0
        }
        
        # Ajout des paramètres personnalisés
        if custom_params:
            try:
                custom_dict = json.loads(custom_params)
                parameters.update(custom_dict)
            except:
                logger.warning("Paramètres personnalisés invalides")
        
        # Génération du son cinématographique
        audio = sound_designer.generate_cinematic_sound(
            category=category,
            sound_type=sound_type,
            duration=duration,
            parameters=parameters
        )
        
        generation_time = time.time() - start_time
        
        # Sauvegarde du fichier
        timestamp = int(time.time())
        filename = f"cinematic_{category}_{sound_type}_{timestamp}.wav"
        filepath = OUTPUT_DIR / filename
        
        sound_designer.save_cinematic_sound(audio, str(filepath))
        
        # Stockage des informations
        track_id = f"cinematic_{timestamp}"
        cinematic_tracks[track_id] = {
            "filename": filename,
            "filepath": str(filepath),
            "category": category,
            "sound_type": sound_type,
            "duration": duration,
            "parameters": parameters,
            "generation_time": generation_time,
            "file_size": os.path.getsize(filepath),
            "timestamp": timestamp,
            "model": "HCS Cinematic Sound Designer",
            "version": "1.0.0",
            "technical_specs": {
                "sample_rate": sound_designer.sample_rate,
                "bit_depth": sound_designer.bit_depth,
                "channels": sound_designer.channels,
                "spatial_format": "5.1 surround"
            }
        }
        
        logger.info(f"✅ Son cinématographique généré: {filename} ({generation_time:.2f}s")
        
        return {
            "success": True,
            "track_id": track_id,
            "filename": filename,
            "category": category,
            "sound_type": sound_type,
            "duration": duration,
            "parameters": parameters,
            "generation_time": generation_time,
            "file_size": os.path.getsize(filepath),
            "technical_specs": cinematic_tracks[track_id]["technical_specs"],
            "model": "HCS Cinematic Sound Designer",
            "download_url": f"/api/download/{track_id}"
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur génération sonore cinéma: {e}")
        raise HTTPException(status_code=500, detail=f"Génération échouée: {e}")

@app.get("/api/download/{track_id}")
async def download_track(track_id: str):
    """Télécharge un son cinématographique"""
    if track_id not in cinematic_tracks:
        raise HTTPException(status_code=404, detail="Son cinématographique non trouvé")
    
    track_info = cinematic_tracks[track_id]
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
    """Liste tous les sons cinématographiques"""
    return {
        "tracks": cinematic_tracks,
        "total": len(cinematic_tracks),
        "categories": list(set(track.get("category", "unknown") for track in cinematic_tracks.values())),
        "technical_specs": {
            "sample_rate": sound_designer.sample_rate,
            "bit_depth": sound_designer.bit_depth,
            "channels": sound_designer.channels,
            "spatial_format": "5.1 surround"
        }
    }

@app.get("/api/track/{track_id}")
async def get_track_info(track_id: str):
    """Informations détaillées sur un son cinématographique"""
    if track_id not in cinematic_tracks:
        raise HTTPException(status_code=404, detail="Son cinématographique non trouvé")
    
    return cinematic_tracks[track_id]

@app.delete("/api/track/{track_id}")
async def delete_track(track_id: str):
    """Supprime un son cinématographique"""
    if track_id not in cinematic_tracks:
        raise HTTPException(status_code=404, detail="Son cinématographique non trouvé")
    
    track_info = cinematic_tracks[track_id]
    filepath = track_info["filepath"]
    
    # Suppression du fichier
    if os.path.exists(filepath):
        os.remove(filepath)
    
    # Suppression des métadonnées
    del cinematic_tracks[track_id]
    
    logger.info(f"🗑️ Son cinématographique supprimé: {track_id}")
    
    return {"success": True, "message": "Son cinématographique supprimé"}

@app.get("/api/available-sounds")
async def get_available_sounds():
    """Retourne tous les sons cinématographiques disponibles"""
    available_sounds = sound_designer.list_available_sounds()
    
    # Ajout de descriptions détaillées
    sound_descriptions = {
        'ambient': {
            'name': 'Ambiances',
            'description': 'Environnements sonores immersifs',
            'use_cases': ['Scènes d\'extérieur', 'Arrière-plans', 'Mise en place'],
            'examples': ['Forêt', 'Océan', 'Ville', 'Espace']
        },
        'effects': {
            'name': 'Effets Spéciaux',
            'description': 'Effets sonores dramatiques',
            'use_cases': ['Scènes d\'action', 'Transitions', 'Moments clés'],
            'examples': ['Explosions', 'Impacts', 'Whoosh', 'Téléportation']
        },
        'foley': {
            'name': 'Foley',
            'description': 'Bruits de mouvements et interactions',
            'use_cases': ['Personnages', 'Objets', 'Actions quotidiennes'],
            'examples': ['Pas', 'Vêtements', 'Portes', 'Équipement']
        },
        'creatures': {
            'name': 'Créatures',
            'description': 'Êtres vivants et monstres',
            'use_cases': ['Personnages non-humains', 'Monstres', 'Animaux'],
            'examples': ['Dragon', 'Alien', 'Robot', 'Insecte']
        },
        'vehicles': {
            'name': 'Véhicules',
            'description': 'Moyens de transport et machines',
            'use_cases': ['Scènes de poursuite', 'Déplacements', 'Ambiances urbaines'],
            'examples': ['Vaisseau spatial', 'Voiture', 'Hélicoptère', 'Char']
        },
        'technology': {
            'name': 'Technologie',
            'description': 'Interfaces et systèmes électroniques',
            'use_cases': ['Sci-fi', 'Futuriste', 'Laboratoires'],
            'examples': ['Ordinateur', 'Hologramme', 'Scanner', 'Alarme']
        },
        'weapons': {
            'name': 'Armes',
            'description': 'Armes et effets de combat',
            'use_cases': ['Scènes de combat', 'Tirs', 'Impacts d\'armes'],
            'examples': ['Laser', 'Plasma', 'Lance-roquettes', 'Épée']
        },
        'nature': {
            'name': 'Nature',
            'description': 'Phénomènes naturels et météo',
            'use_cases': ['Scènes extérieures', 'Météo', 'Catastrophes'],
            'examples': ['Vent', 'Pluie', 'Orage', 'Feu']
        }
    }
    
    # Ajout des descriptions aux catégories
    enhanced_sounds = {}
    for category, sounds in available_sounds.items():
        enhanced_sounds[category] = {
            'sounds': sounds,
            'description': sound_descriptions.get(category, {}).get('description', ''),
            'use_cases': sound_descriptions.get(category, {}).get('use_cases', []),
            'examples': sound_descriptions.get(category, {}).get('examples', [])
        }
    
    return {
        "categories": enhanced_sounds,
        "total_categories": len(available_sounds),
        "total_sounds": sum(len(sounds) for sounds in available_sounds.values()),
        "presets": sound_designer.presets
    }

@app.get("/api/cinematic-presets")
async def get_cinematic_presets():
    """Retourne les presets cinématographiques"""
    return {
        "presets": sound_designer.presets,
        "total": len(sound_designer.presets),
        "categories": {
            "action": ["explosion_large", "impact_metal", "whoosh_fast"],
            "ambient": ["forest_night", "ocean_storm", "space_station"],
            "sci_fi": ["spaceship_bridge", "alien_communication", "power_core"],
            "horror": ["creepy_cave", "monster_growl", "door_creak"]
        }
    }

@app.post("/api/generate-from-preset")
async def generate_from_preset(
    preset_name: str = Form(...),
    duration: float = Form(5.0),
    variation: float = Form(0.1)
):
    """
    Génère un son à partir d'un preset cinématographique
    """
    try:
        if preset_name not in sound_designer.presets:
            raise HTTPException(status_code=404, detail="Preset non trouvé")
        
        preset = sound_designer.presets[preset_name]
        
        logger.info(f"🎬 Génération depuis preset: {preset_name}")
        
        # Application de variation
        parameters = preset['parameters'].copy()
        for key, value in parameters.items():
            if isinstance(value, (int, float)):
                parameters[key] = value * (1 + variation * 0.2)
        
        # Génération
        audio = sound_designer.generate_cinematic_sound(
            category=preset['category'],
            sound_type=preset['type'],
            duration=duration,
            parameters=parameters
        )
        
        # Sauvegarde
        timestamp = int(time.time())
        filename = f"preset_{preset_name}_{timestamp}.wav"
        filepath = OUTPUT_DIR / filename
        
        sound_designer.save_cinematic_sound(audio, str(filepath))
        
        # Stockage
        track_id = f"preset_{timestamp}"
        cinematic_tracks[track_id] = {
            "filename": filename,
            "filepath": str(filepath),
            "preset_name": preset_name,
            "category": preset['category'],
            "sound_type": preset['type'],
            "duration": duration,
            "parameters": parameters,
            "variation": variation,
            "file_size": os.path.getsize(filepath),
            "timestamp": timestamp,
            "model": "HCS Cinematic Sound Designer",
            "download_url": f"/api/download/{track_id}"
        }
        
        logger.info(f"✅ Son preset généré: {filename}")
        
        return {
            "success": True,
            "track_id": track_id,
            "filename": filename,
            "preset_name": preset_name,
            "duration": duration,
            "variation": variation,
            "download_url": f"/api/download/{track_id}"
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur génération preset: {e}")
        raise HTTPException(status_code=500, detail=f"Génération preset échouée: {e}")

@app.get("/api/health")
async def health_check():
    """Vérification de santé du serveur cinématographique"""
    return {
        "status": "healthy",
        "server": "HCS Cinematic Sound Server",
        "version": "1.0.0",
        "sample_rate": sound_designer.sample_rate,
        "bit_depth": sound_designer.bit_depth,
        "channels": sound_designer.channels,
        "spatial_format": "5.1 surround",
        "quality_standard": "Cinematic",
        "available_tracks": len(cinematic_tracks),
        "output_directory": str(OUTPUT_DIR),
        "supported_categories": list(sound_designer.sound_categories.keys())
    }

# Montage des fichiers statiques
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    # Création des répertoires nécessaires
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    
    print("🎬 HCS Cinematic Sound Server Starting...")
    print("=" * 60)
    print(f"🎛️ Cinematic Configuration:")
    print(f"   Sample Rate: {sound_designer.sample_rate}Hz (Ultra HD)")
    print(f"   Bit Depth: {sound_designer.bit_depth}-bit (Professional)")
    print(f"   Channels: {sound_designer.channels} (5.1 Surround)")
    print(f"   Spatial Format: 5.1 Surround")
    print(f"   Quality Standard: Cinematic")
    print(f"   Output Directory: {OUTPUT_DIR}")
    print(f"   Web Interface: http://localhost:8026")
    print(f"   API Documentation: http://localhost:8026/docs")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8026)
