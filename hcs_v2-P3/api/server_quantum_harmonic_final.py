# SERVEUR FINAL - APPROCHE RÉFÉRENCE CHROMATIQUE (IDÉE UTILISATEUR)

import os
import time
import logging
import tempfile
import uuid
import base64
import numpy as np
import cv2
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Configuration logging simple
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Handler simple pour éviter les erreurs
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Créer l'application FastAPI
app = FastAPI(title="HCS V2 - Quantum Harmonic Upscaler (Référence Chromatique)", version="2.0.0")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importer les fonctions de référence chromatique
from server_quantum_harmonic_reference import extract_reference_chromatic_profile, apply_reference_chromatic_profile

# Fonctions harmoniques
def _calibrate_channels_harmonic(frame):
    """Calibration harmonique des canaux RGB avec φ²"""
    try:
        phi_squared = 2.618
        calibrated = frame.copy().astype(np.float32)
        
        for i in range(3):
            channel_mean = np.mean(calibrated[:, :, i])
            target_mean = 128.0
            
            if channel_mean > 0:
                correction_factor = (target_mean / channel_mean) ** (1/phi_squared)
                correction_factor = np.clip(correction_factor, 0.5, 2.0)
                calibrated[:, :, i] *= correction_factor
        
        return calibrated.astype(np.uint8)
    except Exception as e:
        logger.warning(f"⚠️ Erreur calibration harmonique: {e}")
        return frame

def _apply_harmonic_filters(frame):
    """Application des filtres harmoniques"""
    try:
        filtered = cv2.bilateralFilter(frame, 9, 75, 75)
        filtered = cv2.GaussianBlur(filtered, (3, 3), 0.5)
        
        edges = cv2.Canny(filtered, 50, 150)
        edges = cv2.dilate(edges, None, iterations=1)
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
        
        result = cv2.addWeighted(filtered, 0.8, frame, 0.2, 0)
        result = cv2.addWeighted(result, 0.9, edges, 0.1, 0)
        
        return result
    except Exception as e:
        logger.warning(f"⚠️ Erreur filtres harmoniques: {e}")
        return frame

# Endpoint principal avec approche référence
@app.post("/api/v2/upscale/video-reference")
async def upscale_video_with_reference(
    file: UploadFile = File(...),
    scale_factor: float = Form(2.0),
    energy_level: str = Form("standard"),
    temporal_coherence: bool = Form(True)
):
    """Upscale vidéo avec approche de référence chromatique (IDÉE UTILISATEUR)"""
    try:
        logger.info(f"🎬 Vidéo reçue (référence): {file.filename}")
        logger.info(f"🎯 Paramètres: scale={scale_factor}, energy={energy_level}, temporal={temporal_coherence}")
        
        # Validation
        if not file.content_type or not file.content_type.startswith("video/"):
            raise HTTPException(status_code=400, detail="Format de fichier non supporté")
        
        # Sauvegarde
        temp_dir = tempfile.mkdtemp()
        video_id = str(uuid.uuid4())[:8]
        video_path = os.path.join(temp_dir, f"{video_id}_{file.filename}")
        
        with open(video_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"✅ Fichier sauvegardé: {video_path}")
        
        # Traitement principal
        start_time = time.time()
        
        # Importer composants
        from core.harmonic_computer import HarmonicComputer, HarmonicVideoProcessor
        
        # Initialisation
        logger.info("🌊 Initialisation ordinateur harmonique...")
        harmonic_computer = HarmonicComputer(enable_opencl=True, max_workers=2)
        video_processor = HarmonicVideoProcessor(harmonic_computer)
        
        # Détection dimensions
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Impossible de lire la vidéo")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        if fps <= 0:
            fps = 30.0
        
        # Limitations
        max_width = 2560
        max_height = 1440
        max_frames = 30
        
        if width > max_width or height > max_height:
            scale = min(max_width / width, max_height / height)
            width = int(width * scale)
            height = int(height * scale)
            logger.warning(f"⚠️ Résolution réduite: {width}x{height}")
        
        if frame_count > max_frames:
            frame_count = max_frames
            logger.warning(f"⚠️ Frames limitées: {frame_count}")
        
        target_width = min(width * 2, max_width)
        target_height = min(height * 2, max_height)
        
        logger.info(f"🎬 Traitement: {frame_count} frames, {fps:.1f} fps, {width}x{height} → {target_width}x{target_height}")
        
        # Extraction profil chromatique (IDÉE UTILISATEUR)
        logger.info("🎨 Extraction profil chromatique de référence...")
        reference_profile = extract_reference_chromatic_profile(video_path, sample_frame=0)
        
        # Upscaling parallèle
        logger.info("🚀 Lancement upscaling harmonique...")
        upscaled_frames = video_processor.process_video_parallel(
            video_path=video_path,
            target_resolution=(target_width, target_height),
            energy_level=energy_level
        )
        
        # Limiter frames
        if len(upscaled_frames) > max_frames:
            upscaled_frames = upscaled_frames[:max_frames]
        
        # Création vidéo finale
        output_path = os.path.join(temp_dir, f"upscaled_{video_id}.mp4")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (target_width, target_height))
        
        # Traitement frames avec approche référence
        previous_frame = None
        valid_frames = []
        
        for i, frame in enumerate(upscaled_frames):
            try:
                if frame is None or frame.size == 0:
                    continue
                
                logger.info(f"🎬 Frame {i}: {frame.shape}")
                
                # Détection BGR/RGB
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    r_mean = np.mean(frame[:, :, 0])
                    b_mean = np.mean(frame[:, :, 2])
                    
                    if b_mean > r_mean + 15:
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        logger.info("🎨 BGR→RGB")
                    else:
                        frame_rgb = frame
                else:
                    frame_rgb = frame
                
                # Application profil référence (IDÉE UTILISATEUR)
                frame_corrected = apply_reference_chromatic_profile(frame_rgb, reference_profile)
                
                # Calibration harmonique
                calibrated_frame = _calibrate_channels_harmonic(frame_corrected)
                
                # Filtres harmoniques
                enhanced_frame = _apply_harmonic_filters(calibrated_frame)
                
                # Lissage temporel
                if i > 0 and previous_frame is not None:
                    alpha = 0.2
                    enhanced_frame = cv2.addWeighted(enhanced_frame, alpha, previous_frame, 1-alpha, 0)
                
                previous_frame = enhanced_frame.copy()
                valid_frames.append(enhanced_frame)
                
                # Écriture
                out.write(enhanced_frame)
                
                # GC
                if i % 5 == 0:
                    import gc
                    gc.collect()
                    
            except Exception as e:
                logger.warning(f"⚠️ Erreur frame {i}: {e}")
                continue
        
        out.release()
        harmonic_computer.stop()
        
        # Vérification
        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="Échec création vidéo")
        
        # Encodage base64
        with open(output_path, 'rb') as f:
            video_bytes = f.read()
        
        video_base64 = base64.b64encode(video_bytes).decode('utf-8')
        file_size = os.path.getsize(output_path)
        processing_time = time.time() - start_time
        
        logger.info(f"✅ Terminé: {len(valid_frames)} frames, {file_size/1024/1024:.1f}MB, {processing_time:.1f}s")
        
        # Nettoyage
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return JSONResponse(content={
            "success": True,
            "message": "Vidéo upscalée avec succès (approche référence chromatique)",
            "upscaled_video_base64": video_base64,
            "target_resolution": f"{target_width}x{target_height}",
            "scale_factor": scale_factor,
            "total_frames": len(valid_frames),
            "total_processing_time": processing_time,
            "processing_fps": len(valid_frames) / processing_time if processing_time > 0 else 0,
            "file_size_mb": file_size / 1024 / 1024,
            "reference_profile_used": reference_profile is not None,
            "energy_level": energy_level,
            "temporal_coherence_enabled": temporal_coherence
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur upscale: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upscaling: {str(e)}")
    finally:
        try:
            if 'temp_dir' in locals():
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass

# Endpoint de test
@app.get("/api/v2/health")
async def health_check():
    """Vérification santé du serveur"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "approach": "reference_chromatique",
        "timestamp": time.time()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009, log_level="INFO")
