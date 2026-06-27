#!/usr/bin/env python3
"""
CONFIGURATION METHOD_2 POUR HCS API SERVER
Endpoints et configuration pour intégrer METHOD_2 au serveur HCS
"""

from fastapi import APIRouter, Depends, Request, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional
import os
import logging
from hcs_integration import HCSMethod2Adapter

logger = logging.getLogger(__name__)

# Adaptateur global
adapter = HCSMethod2Adapter()

# Router pour les endpoints METHOD_2
method2_router = APIRouter(prefix="/api/method2", tags=["method2"])


@method2_router.post("/compress")
async def compress_image(
    request: Request,
    file: UploadFile = File(...),
    session_id: str = None
):
    """
    Endpoint de compression d'image
    Intégration avec authentification HCS
    """
    try:
        # Vérification de la session (à intégrer avec require_auth du HCS)
        if not session_id:
            return JSONResponse(
                status_code=400,
                content={"error": "session_id requis"}
            )
        
        # Sauvegarde temporaire du fichier
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # Compression
        output_path = temp_path.replace('.', '_compressed.')
        metrics = adapter.compress_with_session(session_id, temp_path, output_path)
        
        # Nettoyage
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return JSONResponse(content=metrics)
    
    except Exception as e:
        logger.error(f"Erreur compression: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@method2_router.post("/decompress")
async def decompress_image(
    request: Request,
    file: UploadFile = File(...),
    session_id: str = None
):
    """
    Endpoint de décompression d'image
    Intégration avec authentification HCS
    """
    try:
        if not session_id:
            return JSONResponse(
                status_code=400,
                content={"error": "session_id requis"}
            )
        
        # Sauvegarde temporaire
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # Décompression
        result = adapter.decompress_with_session(session_id, temp_path)
        
        # Nettoyage
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        # Conversion image en base64 si succès
        if result.get('success') and 'reconstructed_image' in result:
            import cv2
            import base64
            import io
            from PIL import Image
            
            img = result['reconstructed_image']
            pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            buffer = io.BytesIO()
            pil_img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            result['image_base64'] = f"data:image/png;base64,{img_base64}"
            del result['reconstructed_image']  # Trop volumineux pour JSON
        
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"Erreur décompression: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@method2_router.get("/audit/{session_id}")
async def get_audit_log(session_id: str, request: Request):
    """
    Récupère l'historique d'audit pour une session
    """
    try:
        audit_log = adapter.get_session_audit_log(session_id)
        return JSONResponse(content=audit_log)
    except Exception as e:
        logger.error(f"Erreur audit: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@method2_router.post("/session/{session_id}/cleanup")
async def cleanup_session(session_id: str, request: Request):
    """
    Nettoie les ressources d'une session
    """
    try:
        success = adapter.cleanup_session(session_id)
        return JSONResponse(content={
            "session_id": session_id,
            "cleaned": success
        })
    except Exception as e:
        logger.error(f"Erreur cleanup: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# Configuration pour intégration dans hcs_api_server.py
def setup_method2_routes(app):
    """
    Ajoute les routes METHOD_2 à l'application FastAPI HCS
    
    Usage dans hcs_api_server.py:
    from method2_hcs_config import setup_method2_routes
    setup_method2_routes(app)
    """
    app.include_router(method2_router)
    logger.info("Routes METHOD_2 ajoutées au serveur HCS")
