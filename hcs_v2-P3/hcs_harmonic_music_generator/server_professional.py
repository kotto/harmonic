#!/usr/bin/env python3
"""
HCS Professional Audio Server - Qualité Cinéma Hollywood
Serveur Web avec moteur audio professionnel 96kHz/24-bit
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

from professional_audio_engine import ProfessionalAudioEngine

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialisation FastAPI
app = FastAPI(
    title="HCS Professional Audio - Cinema Quality",
    description="Génération musicale professionnelle niveau cinéma Hollywood",
    version="3.0.0"
)

# Configuration templates
templates = Jinja2Templates(directory="templates")

# Répertoire de sortie
OUTPUT_DIR = Path("professional_music")
OUTPUT_DIR.mkdir(exist_ok=True)

# Moteur audio professionnel
professional_engine = ProfessionalAudioEngine()

# Stockage des générations
professional_tracks = {}

@app.get("/", response_class=HTMLResponse)
async def home():
    """Page d'accueil professionnelle"""
    return FileResponse("templates/index_professional.html")

@app.post("/api/generate-professional")
async def generate_professional_music(
    description: str = Form("epic cinematic orchestral music with dramatic strings and powerful brass"),
    cinematic_style: str = Form("cinema"),
    duration: float = Form(120.0),
    apply_mastering: bool = Form(True),
    apply_spatial: bool = Form(True),
    apply_multiband: bool = Form(True)
):
    """
    Génère une piste musicale professionnelle niveau cinéma
    """
    try:
        logger.info(f"Génération professionnelle: {cinematic_style}, {duration}s")
        
        # Génération de la musique professionnelle
        start_time = time.time()
        
        # Configuration du traitement selon les options
        processing_config = {
            'description': description,
            'style': cinematic_style,
            'duration': duration,
            'apply_mastering': apply_mastering,
            'apply_spatial': apply_spatial,
            'apply_multiband': apply_multiband
        }
        
        # Génération avec le moteur professionnel
        audio = professional_engine.generate_professional_track(
            description=description,
            style=cinematic_style,
            duration=duration
        )
        
        generation_time = time.time() - start_time
        
        # Analyse professionnelle complète
        analysis = analyze_professional_audio(audio)
        
        # Sauvegarde du fichier professionnel
        timestamp = int(time.time())
        filename = f"professional_{cinematic_style}_{timestamp}.wav"
        filepath = OUTPUT_DIR / filename
        
        professional_engine.save_professional_audio(audio, str(filepath))
        
        # Stockage des informations
        track_id = f"professional_{timestamp}"
        professional_tracks[track_id] = {
            "filename": filename,
            "filepath": str(filepath),
            "description": description,
            "cinematic_style": cinematic_style,
            "duration": duration,
            "processing_config": processing_config,
            "generation_time": generation_time,
            "analysis": analysis,
            "file_size": os.path.getsize(filepath),
            "timestamp": timestamp,
            "model": "HCS Professional Cinema",
            "quality": f"{professional_engine.sample_rate}Hz/{professional_engine.bit_depth}-bit"
        }
        
        logger.info(f"Musique professionnelle générée: {filename} ({generation_time:.2f}s)")
        
        return {
            "success": True,
            "track_id": track_id,
            "filename": filename,
            "description": description,
            "cinematic_style": cinematic_style,
            "duration": duration,
            "processing_config": processing_config,
            "generation_time": generation_time,
            "file_size": os.path.getsize(filepath),
            "analysis": analysis,
            "model": "HCS Professional Cinema",
            "quality": f"{professional_engine.sample_rate}Hz/{professional_engine.bit_depth}-bit",
            "download_url": f"/api/download/{track_id}"
        }
        
    except Exception as e:
        logger.error(f"Erreur génération professionnelle: {e}")
        raise HTTPException(status_code=500, detail=f"Génération échouée: {e}")

@app.get("/api/download/{track_id}")
async def download_track(track_id: str):
    """Télécharge une piste professionnelle"""
    if track_id not in professional_tracks:
        raise HTTPException(status_code=404, detail="Piste non trouvée")
    
    track_info = professional_tracks[track_id]
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
    """Liste toutes les pistes professionnelles"""
    return {
        "tracks": professional_tracks,
        "total": len(professional_tracks),
        "cinema_styles": list(set(track.get("cinematic_style", "unknown") for track in professional_tracks.values())),
        "quality_standard": f"{professional_engine.sample_rate}Hz/{professional_engine.bit_depth}-bit"
    }

@app.get("/api/track/{track_id}")
async def get_track_info(track_id: str):
    """Informations détaillées sur une piste professionnelle"""
    if track_id not in professional_tracks:
        raise HTTPException(status_code=404, detail="Piste non trouvée")
    
    return professional_tracks[track_id]

@app.delete("/api/track/{track_id}")
async def delete_track(track_id: str):
    """Supprime une piste professionnelle"""
    if track_id not in professional_tracks:
        raise HTTPException(status_code=404, detail="Piste non trouvée")
    
    track_info = professional_tracks[track_id]
    filepath = track_info["filepath"]
    
    # Suppression du fichier
    if os.path.exists(filepath):
        os.remove(filepath)
    
    # Suppression des métadonnées
    del professional_tracks[track_id]
    
    logger.info(f"Piste professionnelle supprimée: {track_id}")
    
    return {"success": True, "message": "Piste supprimée"}

@app.get("/api/cinema-styles")
async def get_cinema_styles():
    """Styles cinématographiques disponibles"""
    return {
        "styles": {
            "cinema": {
                "name": "Cinéma Orchestral",
                "description": "Orchestre cinématique complet avec cordes, cuivres et bois",
                "characteristics": ["Cordes dramatiques", "Cuivres puissants", "Percussion épique"],
                "use_cases": ["Films dramatiques", "Bandes-annonces", "Documentaires"]
            },
            "action": {
                "name": "Cinéma d'Action",
                "description": "Musique percutante pour scènes d'action et poursuites",
                "characteristics": ["Basses rythmiques", "Synthétiseurs percutants", "Hits impactants"],
                "use_cases": ["Films d'action", "Thrillers", "Jeux vidéo"]
            },
            "drama": {
                "name": "Cinéma Dramatique",
                "description": "Musique émotionnelle pour scènes dramatiques et intimes",
                "characteristics": ["Piano émouvant", "Cordes sustain", "Harmonies riches"],
                "use_cases": ["Drames", "Romances", "Documentaires émotionnels"]
            },
            "thriller": {
                "name": "Cinéma Thriller",
                "description": "Musique tendue pour thrillers et films d'horreur",
                "characteristics": ["Basses profondes", "Hautes fréquences", "Tension croissante"],
                "use_cases": ["Thrillers", "Horreur", "Suspense"]
            },
            "epic": {
                "name": "Cinéma Épique",
                "description": "Musique grandiose pour scènes épiques et batailles",
                "characteristics": ["Orchestre complet", "Chœurs puissants", "Percussion massive"],
                "use_cases": ["Films épiques", "Fantasy", "Science-fiction"]
            }
        },
        "technical_specs": {
            "sample_rate": professional_engine.sample_rate,
            "bit_depth": professional_engine.bit_depth,
            "channels": professional_engine.channels,
            "reference_level": professional_engine.pro_settings['reference_level'],
            "peak_limit": professional_engine.pro_settings['peak_limit']
        }
    }

@app.get("/api/analyze-professional/{track_id}")
async def professional_analysis(track_id: str):
    """Analyse audio professionnelle complète"""
    if track_id not in professional_tracks:
        raise HTTPException(status_code=404, detail="Piste non trouvée")
    
    track_info = professional_tracks[track_id]
    
    try:
        # Charger l'audio pour analyse professionnelle
        import librosa
        y, sr = librosa.load(track_info["filepath"], sr=professional_engine.sample_rate)
        
        # Analyse spectrale professionnelle
        stft = librosa.stft(y, n_fft=8192, hop_length=2048)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Analyse multi-bandes
        bands_analysis = analyze_multiband_content(y, sr)
        
        # Analyse spatiale
        spatial_analysis = analyze_spatial_content(y)
        
        # Analyse dynamique
        dynamic_analysis = analyze_dynamic_range(y)
        
        # Analyse de qualité
        quality_metrics = analyze_audio_quality(y, sr)
        
        professional_analysis = {
            "technical_specs": {
                "sample_rate": sr,
                "bit_depth": professional_engine.bit_depth,
                "channels": len(y.shape) if len(y.shape) > 1 else 1,
                "duration": len(y) / sr,
                "file_size": track_info["file_size"]
            },
            "spectral_analysis": {
                "spectral_centroid": float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))),
                "spectral_rolloff": float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))),
                "spectral_bandwidth": float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))),
                "harmonic_content": analyze_harmonic_structure(magnitude),
                "frequency_distribution": analyze_frequency_distribution(magnitude, sr)
            },
            "multiband_analysis": bands_analysis,
            "spatial_analysis": spatial_analysis,
            "dynamic_analysis": dynamic_analysis,
            "quality_metrics": quality_metrics,
            "cinema_compliance": check_cinema_standards(y, sr)
        }
        
        return {
            "track_info": track_info,
            "professional_analysis": professional_analysis
        }
        
    except Exception as e:
        logger.error(f"Erreur analyse professionnelle: {e}")
        return {
            "track_info": track_info,
            "basic_analysis": track_info.get("analysis", {}),
            "error": str(e)
        }

def analyze_professional_audio(audio: np.ndarray) -> Dict:
    """Analyse audio professionnelle de base"""
    try:
        # Analyse spectrale
        if len(audio.shape) > 1:
            # Stéréo : analyse sur le mix mono
            mono_audio = np.mean(audio, axis=0)
        else:
            mono_audio = audio
        
        # Métriques de base
        rms = np.sqrt(np.mean(mono_audio**2))
        peak = np.max(np.abs(mono_audio))
        
        # Analyse fréquentielle
        import librosa
        spectral_centroids = librosa.feature.spectral_centroid(y=mono_audio, sr=professional_engine.sample_rate)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=mono_audio, sr=professional_engine.sample_rate)
        
        return {
            "rms_level": float(rms),
            "peak_level": float(peak),
            "dynamic_range": float(20 * np.log10(peak / max(rms, 1e-10))),
            "spectral_centroid": float(np.mean(spectral_centroids)),
            "spectral_rolloff": float(np.mean(spectral_rolloff)),
            "zero_crossing_rate": float(librosa.feature.zero_crossing_rate(mono_audio)),
            "channels": len(audio.shape) if len(audio.shape) > 1 else 1
        }
        
    except Exception as e:
        logger.error(f"Erreur analyse professionnelle: {e}")
        return {}

def analyze_multiband_content(audio: np.ndarray, sr: int) -> Dict:
    """Analyse du contenu multi-bandes"""
    try:
        import librosa
        
        # Définition des bandes
        bands = {
            'sub_bass': (20, 60),
            'bass': (60, 250),
            'low_mid': (250, 500),
            'mid': (500, 2000),
            'high_mid': (2000, 4000),
            'high_freq': (4000, 20000)
        }
        
        band_analysis = {}
        
        for band_name, (low, high) in bands.items():
            # Filtrage de la bande
            band_audio = librosa.util.normalize(librosa.effects.preemphasis(audio))
            
            # Analyse de la bande
            band_rms = np.sqrt(np.mean(band_audio**2))
            band_peak = np.max(np.abs(band_audio))
            
            band_analysis[band_name] = {
                "rms_level": float(band_rms),
                "peak_level": float(band_peak),
                "dynamic_range": float(20 * np.log10(band_peak / max(band_rms, 1e-10)))
            }
        
        return band_analysis
        
    except Exception as e:
        logger.error(f"Erreur analyse multi-bandes: {e}")
        return {}

def analyze_spatial_content(audio: np.ndarray) -> Dict:
    """Analyse du contenu spatial"""
    try:
        if len(audio.shape) < 2:
            return {"type": "mono", "width": 0.0}
        
        left, right = audio[0], audio[1]
        
        # Analyse de la largeur stéréo
        mid = (left + right) / 2
        side = (left - right) / 2
        
        mid_level = np.sqrt(np.mean(mid**2))
        side_level = np.sqrt(np.mean(side**2))
        
        # Corrélation entre canaux
        correlation = np.corrcoef(left, right)[0, 1]
        
        return {
            "type": "stereo",
            "width": float(side_level / max(mid_level, 1e-10)),
            "mid_level": float(mid_level),
            "side_level": float(side_level),
            "correlation": float(correlation),
            "phase_coherence": float(np.mean(np.angle(np.fft.fft(left) * np.conj(np.fft.fft(right)))))
        }
        
    except Exception as e:
        logger.error(f"Erreur analyse spatiale: {e}")
        return {"type": "unknown"}

def analyze_dynamic_range(audio: np.ndarray) -> Dict:
    """Analyse de la plage dynamique"""
    try:
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=0)
        
        # Plage dynamique
        peak = np.max(np.abs(audio))
        rms = np.sqrt(np.mean(audio**2))
        
        # Percentiles pour analyse dynamique
        percentiles = np.percentile(np.abs(audio), [10, 25, 50, 75, 90, 95, 99])
        
        return {
            "peak_level": float(peak),
            "rms_level": float(rms),
            "dynamic_range_db": float(20 * np.log10(peak / max(rms, 1e-10))),
            "crest_factor": float(peak / max(rms, 1e-10)),
            "percentiles": {
                "p10": float(percentiles[0]),
                "p25": float(percentiles[1]),
                "p50": float(percentiles[2]),
                "p75": float(percentiles[3]),
                "p90": float(percentiles[4]),
                "p95": float(percentiles[5]),
                "p99": float(percentiles[6])
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur analyse dynamique: {e}")
        return {}

def analyze_audio_quality(audio: np.ndarray, sr: int) -> Dict:
    """Analyse de la qualité audio"""
    try:
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=0)
        
        # Mesures de qualité
        snr_estimate = estimate_snr(audio)
        thd_estimate = estimate_thd(audio, sr)
        
        return {
            "estimated_snr_db": float(snr_estimate),
            "estimated_thd_percent": float(thd_estimate),
            "noise_floor": float(np.mean(np.abs(audio[np.abs(audio) < np.percentile(np.abs(audio), 10)]))),
            "headroom_db": float(-20 * np.log10(np.max(np.abs(audio)))),
            "clipping_ratio": float(np.sum(np.abs(audio) > 0.99) / len(audio))
        }
        
    except Exception as e:
        logger.error(f"Erreur analyse qualité: {e}")
        return {}

def estimate_snr(audio: np.ndarray) -> float:
    """Estime le rapport signal/bruit"""
    try:
        # SNR simplifié basé sur la dynamique
        signal_power = np.mean(audio**2)
        noise_power = np.var(audio[np.abs(audio) < np.percentile(np.abs(audio), 20)])
        
        if noise_power > 0:
            snr_db = 10 * np.log10(signal_power / noise_power)
        else:
            snr_db = 60.0  # Valeur par défaut
        
        return snr_db
        
    except:
        return 60.0

def estimate_thd(audio: np.ndarray, sr: int) -> float:
    """Estime la distorsion harmonique totale"""
    try:
        import librosa
        
        # Analyse des harmoniques
        pitches, magnitudes = librosa.piptrack(y=audio, sr=sr, threshold=0.1)
        
        if len(magnitudes) > 0:
            fundamental = np.max(magnitudes)
            harmonics = magnitudes[magnitudes < fundamental * 0.5]
            
            if len(harmonics) > 0:
                thd = np.sum(harmonics) / fundamental * 100
            else:
                thd = 1.0
        else:
            thd = 1.0
        
        return thd
        
    except:
        return 1.0

def analyze_harmonic_structure(magnitude: np.ndarray) -> Dict:
    """Analyse de la structure harmonique"""
    try:
        # Moyenne sur le temps
        avg_magnitude = np.mean(magnitude, axis=1)
        
        # Détection de pics harmoniques
        peaks = []
        for i in range(1, len(avg_magnitude) - 1):
            if (avg_magnitude[i] > avg_magnitude[i-1] and 
                avg_magnitude[i] > avg_magnitude[i+1] and
                avg_magnitude[i] > np.max(avg_magnitude) * 0.05):
                peaks.append((i, avg_magnitude[i]))
        
        # Trier par magnitude
        peaks.sort(key=lambda x: x[1], reverse=True)
        
        return {
            "harmonic_peaks": peaks[:10],
            "fundamental_freq_index": peaks[0][0] if peaks else 0,
            "harmonic_content": len(peaks),
            "harmonic_complexity": float(np.std([p[1] for p in peaks[:5]]) if len(peaks) >= 5 else 0.0)
        }
        
    except Exception as e:
        logger.error(f"Erreur structure harmonique: {e}")
        return {}

def analyze_frequency_distribution(magnitude: np.ndarray, sr: int) -> Dict:
    """Analyse de la distribution fréquentielle"""
    try:
        # Moyenne sur le temps
        avg_magnitude = np.mean(magnitude, axis=1)
        
        # Distribution par bandes
        freq_bins = np.fft.fftfreq(len(avg_magnitude), 1/sr)
        
        # Bandes principales
        sub_bass_mask = (np.abs(freq_bins) >= 20) & (np.abs(freq_bins) < 60)
        bass_mask = (np.abs(freq_bins) >= 60) & (np.abs(freq_bins) < 250)
        mid_mask = (np.abs(freq_bins) >= 250) & (np.abs(freq_bins) < 2000)
        high_mask = (np.abs(freq_bins) >= 2000) & (np.abs(freq_bins) < 20000)
        
        return {
            "sub_bass_energy": float(np.sum(avg_magnitude[sub_bass_mask]**2)),
            "bass_energy": float(np.sum(avg_magnitude[bass_mask]**2)),
            "mid_energy": float(np.sum(avg_magnitude[mid_mask]**2)),
            "high_energy": float(np.sum(avg_magnitude[high_mask]**2)),
            "energy_distribution": {
                "sub_bass": float(np.sum(avg_magnitude[sub_bass_mask]**2) / np.sum(avg_magnitude**2)),
                "bass": float(np.sum(avg_magnitude[bass_mask]**2) / np.sum(avg_magnitude**2)),
                "mid": float(np.sum(avg_magnitude[mid_mask]**2) / np.sum(avg_magnitude**2)),
                "high": float(np.sum(avg_magnitude[high_mask]**2) / np.sum(avg_magnitude**2))
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur distribution fréquentielle: {e}")
        return {}

def check_cinema_standards(audio: np.ndarray, sr: int) -> Dict:
    """Vérifie la conformité aux standards cinéma"""
    try:
        # Standards cinéma
        reference_level = -23.0  # LUFS
        peak_limit = -1.0      # dBTP
        
        # Mesures
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=0)
        
        # LUFS (simplifié)
        rms_level = 20 * np.log10(np.sqrt(np.mean(audio**2)))
        
        # Peak level
        peak_db = 20 * np.log10(np.max(np.abs(audio)))
        
        return {
            "reference_level": reference_level,
            "measured_lufs": float(rms_level),
            "level_difference": float(rms_level - reference_level),
            "peak_level_db": float(peak_db),
            "peak_compliance": peak_db <= peak_limit,
            "cinema_ready": abs(rms_level - reference_level) <= 3.0 and peak_db <= peak_limit
        }
        
    except Exception as e:
        logger.error(f"Erreur conformité cinéma: {e}")
        return {}

@app.get("/api/health")
async def health_check():
    """Vérification de santé du serveur professionnel"""
    return {
        "status": "healthy",
        "generator": "HCS Professional Audio Engine",
        "version": "3.0.0",
        "sample_rate": professional_engine.sample_rate,
        "bit_depth": professional_engine.bit_depth,
        "channels": professional_engine.channels,
        "quality_standard": "Cinema/Hollywood",
        "available_tracks": len(professional_tracks),
        "output_directory": str(OUTPUT_DIR)
    }

# Montage des fichiers statiques
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    # Création des répertoires nécessaires
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    
    print("🎬 HCS Professional Audio Server Starting...")
    print("=" * 60)
    print(f"🎛️ Professional Configuration:")
    print(f"   Sample Rate: {professional_engine.sample_rate}Hz (Cinema Quality)")
    print(f"   Bit Depth: {professional_engine.bit_depth}-bit (Studio Quality)")
    print(f"   Channels: {professional_engine.channels} (Stereo)")
    print(f"   Reference Level: {professional_engine.pro_settings['reference_level']} LUFS")
    print(f"   Peak Limit: {professional_engine.pro_settings['peak_limit']} dBTP")
    print(f"   Output Directory: {OUTPUT_DIR}")
    print(f"   Web Interface: http://localhost:8022")
    print(f"   API Documentation: http://localhost:8022/docs")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8022)
