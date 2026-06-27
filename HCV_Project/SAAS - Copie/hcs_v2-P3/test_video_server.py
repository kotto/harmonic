#!/usr/bin/env python3
"""
Test simple pour l'upload vidéo HCS V2
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import base64
import time
import logging

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisation FastAPI
app = FastAPI(
    title="HCS V2 Test API",
    description="Test simple pour upload vidéo",
    version="2.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
SUPPORTED_VIDEO_FORMATS = ['video/mp4', 'video/webm', 'video/avi', 'video/mov']

@app.get("/")
async def root():
    return {"message": "HCS V2 Test API - Video Upload"}

@app.get("/api/v2/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

@app.post("/api/v2/compress/video")
async def compress_video(file: UploadFile = File(...)):
    """
    Test simple d'upload vidéo
    """
    try:
        logger.info(f"Début compression vidéo: {file.filename}, taille: {file.size}, type: {file.content_type}")
        
        # Validation fichier
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Validation format vidéo
        if file.content_type not in SUPPORTED_VIDEO_FORMATS:
            logger.error(f"Format vidéo non supporté: {file.content_type}")
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported video format: {file.content_type}. Supported formats: {', '.join(SUPPORTED_VIDEO_FORMATS)}"
            )
        
        logger.info(f"Validation OK, lecture du fichier vidéo...")
        
        # Lecture vidéo
        video_data = await file.read()
        
        if not video_data:
            raise HTTPException(status_code=400, detail="Video file is empty")
        
        logger.info(f"Fichier vidéo lu: {len(video_data)} bytes")
        
        # Simulation de compression
        time.sleep(0.1)  # Simuler traitement
        
        # Créer une réponse simple
        response = {
            "success": True,
            "result_id": f"test_{int(time.time())}",
            "original_filename": file.filename,
            "original_size": len(video_data),
            "compressed_size": len(video_data) // 100,  # Simulation 100:1
            "compression_ratio": 100.0,
            "space_saved_percent": 99.0,
            "processing_time": 0.1,
            "content_type": "video",
            "format": "webp_video_simulation",
            "message": "Test upload vidéo réussi!"
        }
        
        logger.info(f"Vidéo traitée avec succès: {file.filename}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la compression vidéo: {str(e)}")
        logger.error(f"Type d'erreur: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Video compression failed: {str(e)}")

if __name__ == "__main__":
    import socket
    
    def find_free_port(start_port=8009, max_port=8099):
        for port in range(start_port, max_port + 1):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                continue
        raise RuntimeError(f"Aucun port disponible trouvé entre {start_port} et {max_port}")
    
    free_port = find_free_port()
    
    print(f"🚀 Démarrage HCS V2 Test API (Port {free_port})")
    print("=" * 50)
    print("📊 Configuration:")
    print(f"   Supported Formats: {', '.join(SUPPORTED_VIDEO_FORMATS)}")
    print()
    print("🌐 Endpoints:")
    print(f"   http://localhost:{free_port}/")
    print(f"   http://localhost:{free_port}/api/v2/compress/video")
    print(f"   http://localhost:{free_port}/api/v2/health")
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=free_port,
        reload=False,
        log_level="info"
    )
