#!/usr/bin/env python3
"""
HCS Simple Music Server - Version légère pour démarrage rapide
Génération musicale de base sans dépendances lourdes
"""

from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import time
import logging
from pathlib import Path
import json
import numpy as np

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialisation FastAPI
app = FastAPI(
    title="HCS Simple Music Server",
    description="Génération musicale légère",
    version="1.0.0"
)

# Configuration
OUTPUT_DIR = Path("simple_music")
OUTPUT_DIR.mkdir(exist_ok=True)

# Stockage des générations
music_tracks = {}

class SimpleMusicGenerator:
    """Générateur musical simple sans dépendances lourdes"""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.styles = {
            'electronic': self.generate_electronic,
            'ambient': self.generate_ambient,
            'classical': self.generate_classical,
            'jazz': self.generate_jazz,
            'rock': self.generate_rock,
            'cinematic': self.generate_cinematic
        }
    
    def generate_electronic(self, duration: float, params: dict) -> np.ndarray:
        """Génère musique électronique"""
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Bass line
        bass_freq = 55 * (2 ** (np.random.randint(0, 3) / 12))  # A1, Bb1, B1
        bass = np.sin(2 * np.pi * bass_freq * t) * 0.3
        
        # Kick drum
        kick_pattern = np.zeros(samples)
        kick_interval = int(self.sample_rate * 0.5)  # Kick every 0.5s
        for i in range(0, samples, kick_interval):
            kick_envelope = np.exp(-20 * np.linspace(0, 0.1, min(kick_interval, samples - i)))
            kick_pattern[i:i+len(kick_envelope)] = kick_envelope * 0.5
        
        # Arpeggio
        arp_freqs = [440, 554, 659, 880]  # A4, C#5, E5, A5
        arp_pattern = np.zeros(samples)
        arp_interval = int(self.sample_rate * 0.125)  # 8th notes
        for i, freq in enumerate(arp_freqs):
            start = i * arp_interval
            if start < samples:
                length = min(arp_interval, samples - start)
                arp_pattern[start:start+length] = np.sin(2 * np.pi * freq * t[start:start+length]) * 0.2
        
        # Mix
        music = bass + kick_pattern + arp_pattern
        
        return music
    
    def generate_ambient(self, duration: float, params: dict) -> np.ndarray:
        """Génère musique ambient"""
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Pad sounds
        pad1 = np.sin(2 * np.pi * 110 * t) * 0.2  # A2
        pad2 = np.sin(2 * np.pi * 165 * t) * 0.15  # E3
        pad3 = np.sin(2 * np.pi * 220 * t) * 0.1   # A3
        
        # Slow modulation
        modulation = 1 + 0.3 * np.sin(2 * np.pi * 0.2 * t)
        
        # Mix with modulation
        music = (pad1 + pad2 + pad3) * modulation
        
        return music
    
    def generate_classical(self, duration: float, params: dict) -> np.ndarray:
        """Génère musique classique simplifiée"""
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Simple chord progression
        chords = [
            [261.63, 329.63, 392.00],  # C major
            [293.66, 369.99, 440.00],  # D minor
            [329.63, 415.30, 493.88],  # E minor
            [261.63, 329.63, 392.00]   # C major
        ]
        
        music = np.zeros(samples)
        chord_duration = duration / len(chords)
        
        for i, chord in enumerate(chords):
            start = int(i * chord_duration * self.sample_rate)
            end = int((i + 1) * chord_duration * self.sample_rate)
            
            if start < samples:
                chord_t = t[start:end]
                for freq in chord:
                    chord_note = np.sin(2 * np.pi * freq * chord_t) * 0.15
                    music[start:end] += chord_note
        
        return music
    
    def generate_jazz(self, duration: float, params: dict) -> np.ndarray:
        """Génère musique jazz simplifiée"""
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Walking bass line
        bass_notes = [82.41, 87.31, 98.00, 110.00]  # E2, F2, G2, A2
        bass_pattern = np.zeros(samples)
        note_duration = int(self.sample_rate * 0.25)  # Quarter notes
        
        for i in range(0, samples, note_duration):
            note_idx = (i // note_duration) % len(bass_notes)
            freq = bass_notes[note_idx]
            end = min(i + note_duration, samples)
            bass_pattern[i:end] = np.sin(2 * np.pi * freq * t[i:end]) * 0.3
        
        # Simple piano chords
        piano_chords = [
            [261.63, 329.63, 392.00],  # C major
            [293.66, 369.99, 440.00],  # D minor
            [349.23, 440.00, 523.25],  # F major
            [329.63, 415.30, 493.88],  # E minor
        ]
        
        piano_pattern = np.zeros(samples)
        chord_duration = int(self.sample_rate * 1.0)  # 1 second per chord
        
        for i, chord in enumerate(piano_chords):
            start = i * chord_duration
            end = min(start + chord_duration, samples)
            if start < samples:
                chord_t = t[start:end]
                for freq in chord:
                    piano_pattern[start:end] += np.sin(2 * np.pi * freq * chord_t) * 0.1
        
        # Mix
        music = bass_pattern + piano_pattern
        
        return music
    
    def generate_rock(self, duration: float, params: dict) -> np.ndarray:
        """Génère musique rock simplifiée"""
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Power chords
        power_chords = [
            [82.41, 123.47],  # E2 + B2
            [98.00, 146.83],  # G2 + D3
            [110.00, 164.81], # A2 + E3
            [98.00, 146.83],  # G2 + D3
        ]
        
        guitar_pattern = np.zeros(samples)
        chord_duration = int(self.sample_rate * 0.5)  # Half second per chord
        
        for i, chord in enumerate(power_chords):
            start = i * chord_duration
            end = min(start + chord_duration, samples)
            if start < samples:
                chord_t = t[start:end]
                for freq in chord:
                    guitar_pattern[start:end] += np.sin(2 * np.pi * freq * chord_t) * 0.25
        
        # Drum pattern
        kick_pattern = np.zeros(samples)
        snare_pattern = np.zeros(samples)
        
        # Kick on beats 1 and 3
        kick_interval = int(self.sample_rate * 1.0)
        for i in range(0, samples, kick_interval):
            kick_envelope = np.exp(-50 * np.linspace(0, 0.05, min(kick_interval//2, samples - i)))
            kick_pattern[i:i+len(kick_envelope)] = kick_envelope * 0.4
        
        # Snare on beats 2 and 4
        snare_start = int(self.sample_rate * 0.5)
        for i in range(snare_start, samples, kick_interval):
            snare_envelope = np.exp(-100 * np.linspace(0, 0.03, min(kick_interval//2, samples - i)))
            snare_pattern[i:i+len(snare_envelope)] = snare_envelope * 0.3
        
        # Mix
        music = guitar_pattern + kick_pattern + snare_pattern
        
        return music
    
    def generate_cinematic(self, duration: float, params: dict) -> np.ndarray:
        """Génère musique cinématographique simplifiée"""
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Orchestra strings (simplified)
        strings = np.sin(2 * np.pi * 220 * t) * 0.15  # A3
        strings += np.sin(2 * np.pi * 330 * t) * 0.1   # E4
        
        # Brass (simplified)
        brass = np.sin(2 * np.pi * 110 * t) * 0.2     # A2
        
        # Percussion (timpani-like)
        percussion = np.zeros(samples)
        hit_interval = int(self.sample_rate * 2.0)  # Hit every 2 seconds
        for i in range(0, samples, hit_interval):
            hit_envelope = np.exp(-10 * np.linspace(0, 0.5, min(hit_interval, samples - i)))
            percussion[i:i+len(hit_envelope)] = hit_envelope * 0.3
        
        # Slow crescendo
        crescendo = np.linspace(0.5, 1.0, samples)
        
        # Mix
        music = (strings + brass + percussion) * crescendo
        
        return music
    
    def generate_music(self, style: str, duration: float, params: dict = None) -> np.ndarray:
        """Génère musique selon le style"""
        if style not in self.styles:
            raise ValueError(f"Style non supporté: {style}")
        
        if params is None:
            params = {}
        
        return self.styles[style](duration, params)

# Générateur musical
music_generator = SimpleMusicGenerator()

@app.get("/", response_class=HTMLResponse)
async def home():
    """Page d'accueil simple"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>HCS Simple Music Server</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f0f0f0; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
            h1 { color: #333; text-align: center; }
            .form-group { margin: 20px 0; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            select, input, button { width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 5px; }
            button { background: #007bff; color: white; cursor: pointer; }
            button:hover { background: #0056b3; }
            .result { margin: 20px 0; padding: 15px; background: #e8f5e8; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎵 HCS Simple Music Server</h1>
            <p>Génération musicale légère - Styles disponibles: Electronic, Ambient, Classical, Jazz, Rock, Cinematic</p>
            
            <form id="musicForm">
                <div class="form-group">
                    <label for="style">Style Musical:</label>
                    <select id="style" name="style">
                        <option value="electronic">Electronic</option>
                        <option value="ambient">Ambient</option>
                        <option value="classical">Classical</option>
                        <option value="jazz">Jazz</option>
                        <option value="rock">Rock</option>
                        <option value="cinematic">Cinematic</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="duration">Durée (secondes):</label>
                    <input type="number" id="duration" name="duration" value="10" min="1" max="60">
                </div>
                
                <div class="form-group">
                    <label for="tempo">Tempo (BPM):</label>
                    <input type="number" id="tempo" name="tempo" value="120" min="60" max="200">
                </div>
                
                <button type="submit">🎵 Générer Musique</button>
            </form>
            
            <div id="result"></div>
        </div>
        
        <script>
            document.getElementById('musicForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData(e.target);
                const resultDiv = document.getElementById('result');
                
                resultDiv.innerHTML = '<p>⏳ Génération en cours...</p>';
                
                try {
                    const response = await fetch('/api/generate-music', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        resultDiv.innerHTML = `
                            <div class="result">
                                <h3>✅ Musique générée!</h3>
                                <p><strong>Style:</strong> ${data.style}</p>
                                <p><strong>Durée:</strong> ${data.duration}s</p>
                                <p><strong>Tempo:</strong> ${data.tempo} BPM</p>
                                <p><strong>Fichier:</strong> ${data.filename}</p>
                                <p><strong>Taille:</strong> ${(data.file_size / 1024).toFixed(1)} KB</p>
                                <p><strong>Temps:</strong> ${data.generation_time.toFixed(2)}s</p>
                                <a href="${data.download_url}" download>📥 Télécharger</a>
                            </div>
                        `;
                    } else {
                        resultDiv.innerHTML = `<div class="result" style="background: #ffe8e8;">❌ Erreur: ${data.error}</div>`;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `<div class="result" style="background: #ffe8e8;">❌ Erreur: ${error.message}</div>`;
                }
            });
        </script>
    </body>
    </html>
    """

@app.post("/api/generate-music")
async def generate_music(
    style: str = Form(...),
    duration: float = Form(10.0),
    tempo: int = Form(120)
):
    """
    Génère une musique simple
    """
    try:
        logger.info(f"🎵 Génération musique: {style}, {duration}s, {tempo} BPM")
        
        start_time = time.time()
        
        # Paramètres
        params = {'tempo': tempo}
        
        # Génération musicale
        audio = music_generator.generate_music(style, duration, params)
        
        generation_time = time.time() - start_time
        
        # Sauvegarde
        timestamp = int(time.time())
        filename = f"simple_{style}_{timestamp}.wav"
        filepath = OUTPUT_DIR / filename
        
        # Sauvegarde WAV simple
        import wave
        with wave.open(str(filepath), 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(music_generator.sample_rate)
            
            # Normalisation et conversion
            audio_normalized = np.clip(audio / np.max(np.abs(audio)) * 0.8, -1, 1)
            audio_int16 = (audio_normalized * 32767).astype(np.int16)
            wav_file.writeframes(audio_int16.tobytes())
        
        # Stockage
        track_id = f"simple_{timestamp}"
        music_tracks[track_id] = {
            "filename": filename,
            "filepath": str(filepath),
            "style": style,
            "duration": duration,
            "tempo": tempo,
            "generation_time": generation_time,
            "file_size": os.path.getsize(filepath),
            "timestamp": timestamp,
            "download_url": f"/api/download/{track_id}"
        }
        
        logger.info(f"✅ Musique générée: {filename} ({generation_time:.2f}s)")
        
        return {
            "success": True,
            "track_id": track_id,
            "filename": filename,
            "style": style,
            "duration": duration,
            "tempo": tempo,
            "generation_time": generation_time,
            "file_size": os.path.getsize(filepath),
            "download_url": f"/api/download/{track_id}"
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur génération musique: {e}")
        raise HTTPException(status_code=500, detail=f"Génération échouée: {e}")

@app.get("/api/download/{track_id}")
async def download_track(track_id: str):
    """Télécharge une musique"""
    if track_id not in music_tracks:
        raise HTTPException(status_code=404, detail="Musique non trouvée")
    
    track_info = music_tracks[track_id]
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
    """Liste toutes les musiques"""
    return {
        "tracks": music_tracks,
        "total": len(music_tracks),
        "styles": list(music_generator.styles.keys())
    }

@app.delete("/api/track/{track_id}")
async def delete_track(track_id: str):
    """Supprime une musique"""
    if track_id not in music_tracks:
        raise HTTPException(status_code=404, detail="Musique non trouvée")
    
    track_info = music_tracks[track_id]
    filepath = track_info["filepath"]
    
    if os.path.exists(filepath):
        os.remove(filepath)
    
    del music_tracks[track_id]
    
    logger.info(f"🗑️ Musique supprimée: {track_id}")
    
    return {"success": True, "message": "Musique supprimée"}

@app.get("/api/health")
async def health_check():
    """Vérification de santé"""
    return {
        "status": "healthy",
        "server": "HCS Simple Music Server",
        "version": "1.0.0",
        "sample_rate": music_generator.sample_rate,
        "available_styles": list(music_generator.styles.keys()),
        "total_tracks": len(music_tracks),
        "output_directory": str(OUTPUT_DIR)
    }

if __name__ == "__main__":
    print("🎵 HCS Simple Music Server Starting...")
    print("=" * 50)
    print(f"🎛️ Simple Configuration:")
    print(f"   Sample Rate: {music_generator.sample_rate}Hz")
    print(f"   Available Styles: {', '.join(music_generator.styles.keys())}")
    print(f"   Output Directory: {OUTPUT_DIR}")
    print(f"   Web Interface: http://localhost:8025")
    print(f"   API Documentation: http://localhost:8025/docs")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8025)
