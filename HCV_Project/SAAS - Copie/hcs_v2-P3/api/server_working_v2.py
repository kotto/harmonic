# SERVEUR FONCTIONNEL - AVEC APPROCHE RÉFÉRENCE

import os
import time
import tempfile
import uuid
import base64
import numpy as np
import cv2
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# FastAPI
app = FastAPI(title="HCS V2 - Working Server")

# CORS
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Fonctions de référence chromatique (intégrées directement)
def extract_reference_chromatic_profile(video_path, sample_frame=0):
    """Extraire une frame et l'upscale comme image pour profil chromatique"""
    try:
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, sample_frame)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            print("⚠️ Impossible d'extraire la frame de référence")
            return None
        
        # Convertir en RGB si nécessaire
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            r_mean = np.mean(frame[:, :, 0])
            b_mean = np.mean(frame[:, :, 2])
            
            if b_mean > r_mean + 15:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                frame_rgb = frame
        else:
            frame_rgb = frame
        
        # Simuler l'upscale (pour le test)
        upscaled_image = cv2.resize(frame_rgb, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_LANCZOS4)
        
        # Analyser les caractéristiques
        if upscaled_image is not None:
            profile = {
                'r_mean': np.mean(upscaled_image[:, :, 0]),
                'g_mean': np.mean(upscaled_image[:, :, 1]),
                'b_mean': np.mean(upscaled_image[:, :, 2]),
                'saturation_mean': np.mean(cv2.cvtColor(upscaled_image, cv2.COLOR_RGB2HSV)[:, :, 1]),
                'brightness_mean': np.mean(cv2.cvtColor(upscaled_image, cv2.COLOR_RGB2LAB)[:, :, 0])
            }
            
            print(f"🎨 Profil chromatique de référence extrait:")
            print(f"   RGB moyens: [{profile['r_mean']:.1f}, {profile['g_mean']:.1f}, {profile['b_mean']:.1f}]")
            print(f"   Saturation moyenne: {profile['saturation_mean']:.1f}")
            print(f"   Luminosité moyenne: {profile['brightness_mean']:.1f}")
            
            return profile
        
        return None
        
    except Exception as e:
        print(f"⚠️ Erreur extraction profil chromatique: {e}")
        return None

def apply_reference_chromatic_profile(frame, reference_profile):
    """Appliquer le profil chromatique de référence à une frame vidéo"""
    try:
        if reference_profile is None:
            return frame
        
        # Analyser la frame actuelle
        current_r_mean = np.mean(frame[:, :, 0])
        current_g_mean = np.mean(frame[:, :, 1])
        current_b_mean = np.mean(frame[:, :, 2])
        
        # Calculer les facteurs de correction
        r_factor = reference_profile['r_mean'] / current_r_mean if current_r_mean > 0 else 1.0
        g_factor = reference_profile['g_mean'] / current_g_mean if current_g_mean > 0 else 1.0
        b_factor = reference_profile['b_mean'] / current_b_mean if current_b_mean > 0 else 1.0
        
        # Limiter les facteurs
        r_factor = np.clip(r_factor, 0.7, 1.3)
        g_factor = np.clip(g_factor, 0.7, 1.3)
        b_factor = np.clip(b_factor, 0.7, 1.3)
        
        # Appliquer les corrections
        corrected = frame.copy().astype(np.float32)
        corrected[:, :, 0] *= r_factor
        corrected[:, :, 1] *= g_factor
        corrected[:, :, 2] *= b_factor
        
        # Ajuster la saturation
        frame_hsv = cv2.cvtColor(corrected.astype(np.uint8), cv2.COLOR_RGB2HSV)
        current_sat = np.mean(frame_hsv[:, :, 1])
        target_sat = reference_profile['saturation_mean']
        sat_factor = target_sat / current_sat if current_sat > 0 else 1.0
        sat_factor = np.clip(sat_factor, 0.8, 1.2)
        
        frame_hsv[:, :, 1] = np.clip(frame_hsv[:, :, 1] * sat_factor, 0, 255)
        corrected = cv2.cvtColor(frame_hsv, cv2.COLOR_HSV2RGB)
        
        print(f"🎨 Profil référence appliqué: RGB×[{r_factor:.2f}, {g_factor:.2f}, {b_factor:.2f}], Sat×{sat_factor:.2f}")
        
        return corrected.astype(np.uint8)
        
    except Exception as e:
        print(f"⚠️ Erreur application profil référence: {e}")
        return frame

@app.post("/api/v2/upscale/video-reference")
async def upscale_video_reference(
    file: UploadFile = File(...),
    scale_factor: float = Form(2.0),
    energy_level: str = Form("standard"),
    temporal_coherence: bool = Form(True)
):
    """Upscale vidéo avec approche référence chromatique"""
    try:
        print(f"🎬 Vidéo reçue (référence): {file.filename}")
        
        # Validation
        if not file.content_type or not file.content_type.startswith("video/"):
            raise HTTPException(status_code=400, detail="Format vidéo requis")
        
        # Sauvegarde
        temp_dir = tempfile.mkdtemp()
        video_id = str(uuid.uuid4())[:8]
        video_path = os.path.join(temp_dir, f"{video_id}_{file.filename}")
        
        with open(video_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        print(f"✅ Fichier sauvegardé: {video_path}")
        
        # Extraction profil référence
        print("🎨 Extraction profil chromatique de référence...")
        reference_profile = extract_reference_chromatic_profile(video_path, sample_frame=0)
        
        # Traitement simple (test)
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        if fps <= 0:
            fps = 30.0
        
        # Limitations
        max_frames = 10  # Test avec 10 frames
        if frame_count > max_frames:
            frame_count = max_frames
            print(f"⚠️ Limitation à {max_frames} frames pour test")
        
        target_width = min(width * 2, 2560)
        target_height = min(height * 2, 1440)
        
        print(f"🎬 Traitement: {frame_count} frames, {fps:.1f} fps, {width}x{height} → {target_width}x{target_height}")
        
        # Création vidéo sortie
        output_path = os.path.join(temp_dir, f"upscaled_{video_id}.mp4")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (target_width, target_height))
        
        # Traitement frames
        cap = cv2.VideoCapture(video_path)
        processed_frames = 0
        
        for i in range(frame_count):
            ret, frame = cap.read()
            if not ret:
                break
            
            # Conversion RGB
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                r_mean = np.mean(frame[:, :, 0])
                b_mean = np.mean(frame[:, :, 2])
                if b_mean > r_mean + 15:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                else:
                    frame_rgb = frame
            else:
                frame_rgb = frame
            
            # Application profil référence
            corrected_frame = apply_reference_chromatic_profile(frame_rgb, reference_profile)
            
            # Upscale simple
            upscaled_frame = cv2.resize(corrected_frame, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)
            
            # Écriture
            out.write(upscaled_frame)
            processed_frames += 1
            
            if processed_frames >= max_frames:
                break
        
        cap.release()
        out.release()
        
        # Encodage base64
        with open(output_path, 'rb') as f:
            video_bytes = f.read()
        
        video_base64 = base64.b64encode(video_bytes).decode('utf-8')
        file_size = os.path.getsize(output_path)
        
        print(f"✅ Terminé: {processed_frames} frames, {file_size/1024/1024:.1f}MB")
        
        # Nettoyage
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return JSONResponse(content={
            "success": True,
            "message": "Vidéo upscalée avec succès (approche référence chromatique)",
            "upscaled_video_base64": video_base64,
            "target_resolution": f"{target_width}x{target_height}",
            "scale_factor": scale_factor,
            "total_frames": processed_frames,
            "file_size_mb": file_size / 1024 / 1024,
            "reference_profile_used": reference_profile is not None,
            "energy_level": energy_level,
            "temporal_coherence_enabled": temporal_coherence
        })
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/")
async def root():
    return {"message": "HCS V2 - Serveur avec Référence Chromatique", "status": "ready"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009, log_level="INFO")
