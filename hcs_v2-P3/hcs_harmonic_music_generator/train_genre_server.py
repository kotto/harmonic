#!/usr/bin/env python3
"""
HCS Genre Training Server - Serveur pour entraînement de genres
Interface web pour entraîner des IA sur des genres spécifiques
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import tempfile
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any
import json

from genre_trainer import HCSGenreTrainer

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialisation FastAPI
app = FastAPI(
    title="HCS Genre Training Server",
    description="Entraînement d'IA sur genres musicaux spécifiques",
    version="1.0.0"
)

# Configuration
TRAINING_DIR = Path("genre_training")
TRAINING_DIR.mkdir(exist_ok=True)

# Stockage des entraînements
training_sessions = {}
active_trainers = {}

@app.get("/", response_class=HTMLResponse)
async def home():
    """Page d'accueil entraînement de genre"""
    return FileResponse("templates/train_genre.html")

@app.post("/api/start-training")
async def start_genre_training(
    genre_name: str = Form(...),
    dataset_description: str = Form(""),
    training_epochs: int = Form(50),
    batch_size: int = Form(32)
):
    """
    Démarre l'entraînement sur un genre spécifique
    """
    try:
        logger.info(f"🎵 Début entraînement genre: {genre_name}")
        
        # Création du trainer
        trainer = HCSGenreTrainer(genre_name)
        
        # Configuration de l'entraînement
        training_config = {
            'genre_name': genre_name,
            'dataset_description': dataset_description,
            'training_epochs': training_epochs,
            'batch_size': batch_size,
            'start_time': time.time()
        }
        
        # Stockage
        session_id = f"training_{genre_name}_{int(time.time())}"
        training_sessions[session_id] = {
            'session_id': session_id,
            'genre_name': genre_name,
            'config': training_config,
            'status': 'waiting_for_data',
            'progress': 0,
            'current_epoch': 0,
            'total_epochs': training_epochs
        }
        
        active_trainers[session_id] = trainer
        
        logger.info(f"✅ Session d'entraînement créée: {session_id}")
        
        return {
            "success": True,
            "session_id": session_id,
            "genre_name": genre_name,
            "status": "waiting_for_data",
            "config": training_config
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur démarrage entraînement: {e}")
        raise HTTPException(status_code=500, detail=f"Démarrage échoué: {e}")

@app.post("/api/upload-dataset/{session_id}")
async def upload_dataset(
    session_id: str,
    files: list[UploadFile] = File(...),
    file_patterns: Optional[str] = Form("*.wav,*.mp3,*.flac")
):
    """
    Upload des fichiers audio pour l'entraînement
    """
    try:
        if session_id not in training_sessions:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        
        session = training_sessions[session_id]
        trainer = active_trainers[session_id]
        
        logger.info(f"📁 Upload dataset pour {session['genre_name']}: {len(files)} fichiers")
        
        # Création du répertoire temporaire
        temp_dir = TRAINING_DIR / f"temp_{session_id}"
        temp_dir.mkdir(exist_ok=True)
        
        uploaded_files = []
        
        for file in files:
            try:
                # Sauvegarde du fichier
                file_path = temp_dir / file.filename
                with open(file_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)
                
                uploaded_files.append(str(file_path))
                logger.info(f"✅ Fichier uploadé: {file.filename}")
                
            except Exception as e:
                logger.warning(f"⚠️ Erreur upload {file.filename}: {e}")
                continue
        
        # Chargement du dataset
        if uploaded_files:
            session['status'] = 'loading_data'
            session['uploaded_files'] = len(uploaded_files)
            
            # Chargement des données
            training_data = trainer.load_genre_dataset(str(temp_dir))
            
            session['status'] = 'data_loaded'
            session['dataset_info'] = {
                'num_files': len(training_data['features']),
                'avg_duration': sum(meta['duration'] for meta in training_data['metadata']) / len(training_data['metadata'])
            }
            
            logger.info(f"✅ Dataset chargé: {len(training_data['features'])} exemples")
        
        return {
            "success": True,
            "session_id": session_id,
            "uploaded_files": len(uploaded_files),
            "dataset_info": session.get('dataset_info', {}),
            "status": session['status']
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur upload dataset: {e}")
        raise HTTPException(status_code=500, detail=f"Upload échoué: {e}")

@app.post("/api/analyze-patterns/{session_id}")
async def analyze_patterns(session_id: str):
    """
    Analyse les patterns du genre
    """
    try:
        if session_id not in training_sessions:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        
        session = training_sessions[session_id]
        trainer = active_trainers[session_id]
        
        logger.info(f"🔍 Analyse patterns {session['genre_name']}")
        
        session['status'] = 'analyzing_patterns'
        
        # Analyse des patterns
        genre_knowledge = trainer.analyze_genre_patterns()
        
        session['status'] = 'patterns_analyzed'
        session['genre_knowledge'] = genre_knowledge
        
        logger.info(f"✅ Patterns analysés pour {session['genre_name']}")
        
        return {
            "success": True,
            "session_id": session_id,
            "genre_knowledge": genre_knowledge,
            "status": session['status']
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur analyse patterns: {e}")
        raise HTTPException(status_code=500, detail=f"Analyse échouée: {e}")

@app.post("/api/train-model/{session_id}")
async def train_model(session_id: str):
    """
    Entraîne le modèle sur les patterns analysés
    """
    try:
        if session_id not in training_sessions:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        
        session = training_sessions[session_id]
        trainer = active_trainers[session_id]
        
        logger.info(f"🧠 Entraînement modèle {session['genre_name']}")
        
        session['status'] = 'training'
        
        # Simulation d'entraînement (remplacer par vrai entraînement)
        total_epochs = session['total_epochs']
        
        for epoch in range(total_epochs):
            session['current_epoch'] = epoch + 1
            session['progress'] = (epoch + 1) / total_epochs * 100
            
            # Simulation de temps d'entraînement
            time.sleep(0.1)
            
            logger.info(f"🔄 Epoch {epoch + 1}/{total_epochs} - {session['progress']:.1f}%")
        
        # Sauvegarde du modèle
        model_path = TRAINING_DIR / f"models_{session_id}"
        trainer.save_genre_model(str(model_path))
        
        session['status'] = 'training_completed'
        session['model_path'] = str(model_path)
        
        logger.info(f"✅ Entraînement complété pour {session['genre_name']}")
        
        return {
            "success": True,
            "session_id": session_id,
            "status": session['status'],
            "model_path": str(model_path),
            "training_time": time.time() - session['config']['start_time']
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur entraînement: {e}")
        raise HTTPException(status_code=500, detail=f"Entraînement échoué: {e}")

@app.post("/api/test-generation/{session_id}")
async def test_generation(
    session_id: str,
    duration: float = Form(30.0),
    variation: float = Form(0.1)
):
    """
    Teste la génération avec le modèle entraîné
    """
    try:
        if session_id not in training_sessions:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        
        session = training_sessions[session_id]
        trainer = active_trainers[session_id]
        
        logger.info(f"🎵 Test génération {session['genre_name']}")
        
        # Génération test
        generated_audio = trainer.generate_genre_music(duration=duration, variation=variation)
        
        # Sauvegarde du test
        test_filename = f"test_{session['genre_name']}_{int(time.time())}.wav"
        test_path = TRAINING_DIR / test_filename
        
        import soundfile as sf
        sf.write(str(test_path), generated_audio.T, trainer.sample_rate)
        
        logger.info(f"✅ Test généré: {test_filename}")
        
        return {
            "success": True,
            "session_id": session_id,
            "test_filename": test_filename,
            "test_path": str(test_path),
            "duration": duration,
            "variation": variation,
            "download_url": f"/api/download-test/{test_filename}"
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur test génération: {e}")
        raise HTTPException(status_code=500, detail=f"Test échoué: {e}")

@app.get("/api/download-test/{filename}")
async def download_test(filename: str):
    """Télécharge un fichier de test"""
    test_path = TRAINING_DIR / filename
    
    if not test_path.exists():
        raise HTTPException(status_code=404, detail="Fichier de test non trouvé")
    
    return FileResponse(
        test_path,
        media_type="audio/wav",
        filename=filename
    )

@app.get("/api/sessions")
async def list_sessions():
    """Liste toutes les sessions d'entraînement"""
    return {
        "sessions": training_sessions,
        "total": len(training_sessions),
        "active_sessions": len([s for s in training_sessions.values() if s['status'] not in ['completed', 'failed']])
    }

@app.get("/api/session/{session_id}")
async def get_session_info(session_id: str):
    """Informations détaillées sur une session"""
    if session_id not in training_sessions:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    return training_sessions[session_id]

@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Supprime une session d'entraînement"""
    if session_id not in training_sessions:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    session = training_sessions[session_id]
    
    # Nettoyage des fichiers
    temp_dir = TRAINING_DIR / f"temp_{session_id}"
    if temp_dir.exists():
        import shutil
        shutil.rmtree(temp_dir)
    
    # Suppression des données
    del training_sessions[session_id]
    if session_id in active_trainers:
        del active_trainers[session_id]
    
    logger.info(f"🗑️ Session supprimée: {session_id}")
    
    return {"success": True, "message": "Session supprimée"}

@app.get("/api/available-genres")
async def get_available_genres():
    """Retourne les genres disponibles pour l'entraînement"""
    
    genres = {
        "jazz": {
            "name": "Jazz",
            "description": "Musique jazz avec improvisation et swing",
            "characteristics": ["Improvisation", "Swing rhythm", "Complex harmony", "Blue notes"],
            "typical_instruments": ["Piano", "Saxophone", "Trumpet", "Double bass", "Drums"],
            "tempo_range": "60-200 BPM",
            "key_features": ["7th chords", "ii-V-I progressions", "Syncopation"]
        },
        "classical": {
            "name": "Classical",
            "description": "Musique classique orchestrale et de chambre",
            "characteristics": ["Complex orchestration", "Formal structure", "Dynamic contrast", "Acoustic instruments"],
            "typical_instruments": ["Violin", "Cello", "Piano", "Flute", "Orchestra"],
            "tempo_range": "40-180 BPM",
            "key_features": ["Sonata form", "Counterpoint", "Modulation", "Orchestration"]
        },
        "rock": {
            "name": "Rock",
            "description": "Musique rock avec guitares et batterie puissante",
            "characteristics": ["Electric guitars", "Strong drums", "4/4 time", "Power chords"],
            "typical_instruments": ["Electric guitar", "Bass guitar", "Drums", "Vocals"],
            "tempo_range": "80-160 BPM",
            "key_features": ["Power chords", "Backbeat", "Guitar riffs", "Verse-chorus structure"]
        },
        "electronic": {
            "name": "Electronic",
            "description": "Musique électronique avec synthétiseurs et beats",
            "characteristics": ["Synthesizers", "Electronic drums", "Sequencing", "Sound design"],
            "typical_instruments": ["Synthesizer", "Drum machine", "Sampler", "Sequencer"],
            "tempo_range": "90-180 BPM",
            "key_features": ["Synthesis", "Sampling", "Sequencing", "Effects processing"]
        },
        "pop": {
            "name": "Pop",
            "description": "Musique pop entraînante et commerciale",
            "characteristics": ["Catchy melodies", "Simple harmony", "Danceable rhythm", "Radio-friendly"],
            "typical_instruments": ["Vocals", "Piano", "Guitar", "Bass", "Drums"],
            "tempo_range": "80-140 BPM",
            "key_features": ["Verse-chorus", "Hook", "Simple harmony", "Catchy rhythm"]
        },
        "hip_hop": {
            "name": "Hip Hop",
            "description": "Musique hip hop avec beats et rap",
            "characteristics": ["Rhythmic beats", "Rap vocals", "Sampling", "Bass emphasis"],
            "typical_instruments": ["Drum machine", "Sampler", "Turntables", "Synthesizer"],
            "tempo_range": "70-120 BPM",
            "key_features": ["Sampling", "Looping", "Beat making", "Rhyme patterns"]
        },
        "blues": {
            "name": "Blues",
            "description": "Musique blues avec progression 12 barres",
            "characteristics": ["12-bar progression", "Blue notes", "Call and response", "Guitar focus"],
            "typical_instruments": ["Electric guitar", "Harmonica", "Bass", "Drums", "Piano"],
            "tempo_range": "60-120 BPM",
            "key_features": ["12-bar blues", "Blue notes", "Shuffle rhythm", "Bending"]
        },
        "country": {
            "name": "Country",
            "description": "Musique country avec guitares acoustiques et storytelling",
            "characteristics": ["Acoustic instruments", "Storytelling", "Twang", "Simple harmony"],
            "typical_instruments": ["Acoustic guitar", "Fiddle", "Steel guitar", "Bass", "Drums"],
            "tempo_range": "60-140 BPM",
            "key_features": ["I-IV-V progression", "Storytelling", "Twang", "Simple structure"]
        },
        "metal": {
            "name": "Metal",
            "description": "Musique metal heavy avec guitares saturées",
            "characteristics": ["Distorted guitars", "Heavy drums", "Power vocals", "Complex rhythms"],
            "typical_instruments": ["Electric guitar", "Bass guitar", "Double bass drums", "Vocals"],
            "tempo_range": "100-200 BPM",
            "key_features": ["Distortion", "Power chords", "Double bass drumming", "Complex rhythms"]
        },
        "folk": {
            "name": "Folk",
            "description": "Musique folk traditionnelle et acoustique",
            "characteristics": ["Acoustic instruments", "Traditional melodies", "Storytelling", "Simple harmony"],
            "typical_instruments": ["Acoustic guitar", "Banjo", "Fiddle", "Mandolin", "Vocals"],
            "tempo_range": "60-140 BPM",
            "key_features": ["Traditional scales", "Storytelling", "Acoustic sound", "Simple structure"]
        }
    }
    
    return {
        "genres": genres,
        "total": len(genres),
        "recommended_for_training": ["jazz", "electronic", "rock", "pop", "classical"]
    }

@app.get("/api/health")
async def health_check():
    """Vérification de santé du serveur d'entraînement"""
    return {
        "status": "healthy",
        "server": "HCS Genre Training Server",
        "version": "1.0.0",
        "active_sessions": len([s for s in training_sessions.values() if s['status'] not in ['completed', 'failed']]),
        "total_sessions": len(training_sessions),
        "training_directory": str(TRAINING_DIR),
        "supported_genres": ["jazz", "classical", "rock", "electronic", "pop", "hip_hop", "blues", "country", "metal", "folk"]
    }

# Montage des fichiers statiques
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    # Création des répertoires nécessaires
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    
    print("🎵 HCS Genre Training Server Starting...")
    print("=" * 60)
    print(f"🎛️ Training Configuration:")
    print(f"   Supported Genres: 10")
    print(f"   Training Directory: {TRAINING_DIR}")
    print(f"   Web Interface: http://localhost:8025")
    print(f"   API Documentation: http://localhost:8025/docs")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8025)
