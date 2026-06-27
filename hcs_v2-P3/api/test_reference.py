# TEST SIMPLE - APPROCHE RÉFÉRENCE CHROMATIQUE

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

# Logging simple
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# FastAPI
app = FastAPI(title="Test Référence Chromatique")

# CORS
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Importer les fonctions de référence
try:
    from server_quantum_harmonic_reference import extract_reference_chromatic_profile, apply_reference_chromatic_profile
    logger.info("✅ Module référence chromatique importé")
except Exception as e:
    logger.error(f"❌ Erreur import module: {e}")
    extract_reference_chromatic_profile = None
    apply_reference_chromatic_profile = None

@app.post("/test-reference")
async def test_reference_endpoint(file: UploadFile = File(...)):
    """Test simple de l'approche référence chromatique"""
    try:
        logger.info(f"🎬 Test référence: {file.filename}")
        
        # Validation
        if not file.content_type or not file.content_type.startswith("video/"):
            raise HTTPException(status_code=400, detail="Format vidéo requis")
        
        # Sauvegarde
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, file.filename)
        
        with open(video_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"✅ Fichier sauvegardé: {video_path}")
        
        # Test extraction profil
        if extract_reference_chromatic_profile:
            logger.info("🎨 Test extraction profil chromatique...")
            profile = extract_reference_chromatic_profile(video_path, sample_frame=0)
            
            if profile:
                logger.info(f"✅ Profil extrait: RGB=[{profile['r_mean']:.1f}, {profile['g_mean']:.1f}, {profile['b_mean']:.1f}]")
                logger.info(f"   Saturation: {profile['saturation_mean']:.1f}")
                logger.info(f"   Luminosité: {profile['brightness_mean']:.1f}")
                
                # Test application sur une frame
                cap = cv2.VideoCapture(video_path)
                ret, frame = cap.read()
                cap.release()
                
                if ret and apply_reference_chromatic_profile:
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
                    
                    # Application profil
                    corrected_frame = apply_reference_chromatic_profile(frame_rgb, profile)
                    logger.info(f"✅ Profil appliqué: {corrected_frame.shape}")
                    
                    # Encodage test
                    _, buffer = cv2.imencode('.jpg', corrected_frame)
                    jpg_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    # Nettoyage
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    
                    return JSONResponse(content={
                        "success": True,
                        "message": "Test référence chromatique réussi",
                        "profile": profile,
                        "test_image_base64": jpg_base64
                    })
            
            logger.error("❌ Échec extraction profil")
            return JSONResponse(content={
                "success": False,
                "message": "Échec extraction profil chromatique"
            }, status_code=500)
        
        else:
            logger.error("❌ Module référence non disponible")
            return JSONResponse(content={
                "success": False,
                "message": "Module référence non disponible"
            }, status_code=500)
            
    except Exception as e:
        logger.error(f"❌ Erreur test: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Test Référence Chromatique - HCS V2", "status": "ready"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010, log_level="INFO")
