# VERSION NETTOYÉE - APPROCHE RÉFÉRENCE CHROMATIQUE

import os
import time
import logging
import numpy as np
import cv2
from fastapi import HTTPException
from fastapi.responses import JSONResponse

# Importer les fonctions de référence chromatique
from server_quantum_harmonic_reference import extract_reference_chromatic_profile, apply_reference_chromatic_profile

# Configuration du logging
logger = logging.getLogger(__name__)

# Fonctions harmoniques existantes (simplifiées)
def _calibrate_channels_harmonic(frame):
    """Calibration harmonique des canaux RGB avec φ²"""
    try:
        # Constante harmonique φ² ≈ 2.618
        phi_squared = 2.618
        
        calibrated = frame.copy().astype(np.float32)
        
        # Calibration basée sur la constante harmonique
        for i in range(3):
            channel_mean = np.mean(calibrated[:, :, i])
            target_mean = 128.0  # Valeur cible neutre
            
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
        # Filtre bilatéral pour préserver les contours
        filtered = cv2.bilateralFilter(frame, 9, 75, 75)
        
        # Léger flou gaussien pour harmoniser
        filtered = cv2.GaussianBlur(filtered, (3, 3), 0.5)
        
        # Renforcement des contours
        edges = cv2.Canny(filtered, 50, 150)
        edges = cv2.dilate(edges, None, iterations=1)
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
        
        # Combinaison harmonique
        result = cv2.addWeighted(filtered, 0.8, frame, 0.2, 0)
        result = cv2.addWeighted(result, 0.9, edges, 0.1, 0)
        
        return result
    except Exception as e:
        logger.warning(f"⚠️ Erreur filtres harmoniques: {e}")
        return frame

# Endpoint principal d'upscale vidéo avec approche référence
async def upscale_video_with_reference(
    video_path: str,
    scale_factor: float = 2.0,
    energy_level: str = "standard",
    temporal_coherence: bool = True,
    video_id: str = "default"
):
    """Upscale vidéo avec approche de référence chromatique"""
    
    try:
        start_time = time.time()
        logger.info(f"🎬 Début upscale vidéo avec référence: {video_path}")
        
        # Importer les composants nécessaires
        from core.harmonic_computer import HarmonicComputer, HarmonicVideoProcessor
        
        # Initialisation
        logger.info("🌊 Initialisation de l'ordinateur harmonique...")
        harmonic_computer = HarmonicComputer(enable_opencl=True, max_workers=2)
        video_processor = HarmonicVideoProcessor(harmonic_computer)
        
        # Détection dimensions et limitation
        import cv2
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
        
        # Limitation résolution
        max_width = 2560
        max_height = 1440
        
        if width > max_width or height > max_height:
            scale_factor = min(max_width / width, max_height / height)
            width = int(width * scale_factor)
            height = int(height * scale_factor)
            logger.warning(f"⚠️ Résolution réduite à: {width}x{height}")
        
        # Limitation frames
        max_frames = 30
        if frame_count > max_frames:
            logger.warning(f"⚠️ Limitation à {max_frames} frames")
            frame_count = max_frames
        
        target_width = min(width * 2, max_width)
        target_height = min(height * 2, max_height)
        
        logger.info(f"🎬 Infos: {frame_count} frames, {fps:.2f} fps, {width}x{height} → {target_width}x{target_height}")
        
        # Extraction profil chromatique de référence (IDÉE UTILISATEUR)
        logger.info("🎨 Extraction profil chromatique de référence...")
        reference_profile = extract_reference_chromatic_profile(video_path, sample_frame=0)
        
        # Upscaling parallèle
        logger.info("🚀 Lancement upscaling harmonique...")
        upscaled_frames = video_processor.process_video_parallel(
            video_path=video_path,
            target_resolution=(target_width, target_height),
            energy_level=energy_level
        )
        
        # Limiter frames si nécessaire
        if len(upscaled_frames) > max_frames:
            upscaled_frames = upscaled_frames[:max_frames]
        
        # Création vidéo finale
        temp_dir = os.path.dirname(video_path)
        output_video_path = os.path.join(temp_dir, f"upscaled_{video_id}.mp4")
        
        # Codec MP4V compatible
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (target_width, target_height))
        
        # Traitement frames avec approche référence
        previous_frame = None
        valid_frames = []
        
        for i, frame in enumerate(upscaled_frames):
            try:
                if frame is None or frame.size == 0:
                    continue
                
                logger.info(f"🎬 Traitement frame {i}: {frame.shape}")
                
                # Détection BGR/RGB
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    r_mean = np.mean(frame[:, :, 0])
                    b_mean = np.mean(frame[:, :, 2])
                    
                    if b_mean > r_mean + 15:
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        logger.info("🎨 BGR→RGB converti")
                    else:
                        frame_rgb = frame
                else:
                    frame_rgb = frame
                
                # Application profil chromatique de référence (IDÉE UTILISATEUR)
                frame_corrected = apply_reference_chromatic_profile(frame_rgb, reference_profile)
                
                # Calibration harmonique
                calibrated_frame = _calibrate_channels_harmonic(frame_corrected)
                
                # Filtres harmoniques
                enhanced_frame = _apply_harmonic_filters(calibrated_frame)
                
                # Lissage temporel
                if i > 0 and previous_frame is not None:
                    alpha = 0.2
                    enhanced_frame = cv2.addWeighted(enhanced_frame, alpha, previous_frame, 1-alpha, 0)
                    logger.info(f"🎬 Lissage temporel: alpha={alpha}")
                
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
        
        # Vérification fichier
        if not os.path.exists(output_video_path):
            raise HTTPException(status_code=500, detail="Échec création vidéo")
        
        file_size = os.path.getsize(output_video_path)
        processing_time = time.time() - start_time
        
        logger.info(f"✅ Upscaling terminé: {len(valid_frames)} frames, {file_size/1024/1024:.1f}MB, {processing_time:.1f}s")
        
        # Lecture et encodage base64
        with open(output_video_path, 'rb') as f:
            video_bytes = f.read()
        
        import base64
        video_base64 = base64.b64encode(video_bytes).decode('utf-8')
        
        # Nettoyage
        harmonic_computer.stop()
        
        return {
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
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur upscale vidéo: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upscaling: {str(e)}")

logger.info("🎨 Module d'upscale vidéo avec référence chromatique chargé")
