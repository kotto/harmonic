#!/usr/bin/env python3
"""
Script de test simple pour valider les corrections de décompression vidéo
"""

import requests
import json
import os
import tempfile
import logging

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_server_port():
    """Trouve le port du serveur HCS V2 en cours d'exécution"""
    for port in range(8008, 8100):
        try:
            response = requests.get(f"http://localhost:{port}/api/v2/health", timeout=2)
            if response.status_code == 200:
                logger.info(f"Serveur trouvé sur le port {port}")
                return port
        except requests.exceptions.ConnectionError:
            continue
    return None

def test_video_decompression_simple():
    """Test simple de décompression vidéo"""
    server_port = find_server_port()
    
    if not server_port:
        logger.error("❌ Serveur HCS V2 non trouvé")
        return False
    
    API_BASE_URL = f"http://localhost:{server_port}"
    
    logger.info("🧪 Test simple de décompression vidéo")
    logger.info(f"   Port: {server_port}")
    
    # Créer une vidéo de test très simple
    test_video_data = b"FAKE_VIDEO_DATA_FOR_TESTING" * 1000  # ~27KB
    
    try:
        # 1. Compresser la vidéo
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            f.write(test_video_data)
            f.flush()
            
            with open(f.name, 'rb') as video_file:
                files = {'file': ('test_video.mp4', video_file, 'video/mp4')}
                
                logger.info("📤 Compression vidéo...")
                response = requests.post(f"{API_BASE_URL}/api/v2/compress/video", files=files, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"❌ Erreur compression: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
        
        result = response.json()
        result_id = result['result_id']
        logger.info(f"✅ Vidéo compressée - ID: {result_id}")
        
        # 2. Tester la décompression
        decompress_url = f"{API_BASE_URL}/api/v2/decompress/{result_id}"
        logger.info(f"📥 Test décompression: {decompress_url}")
        
        decompress_response = requests.get(decompress_url, timeout=30)
        
        if decompress_response.status_code == 200:
            logger.info("✅ Décompression réussie!")
            
            # Vérifier les en-têtes
            content_type = decompress_response.headers.get('content-type', '')
            content_length = decompress_response.headers.get('content-length', '0')
            disposition = decompress_response.headers.get('content-disposition', '')
            
            logger.info(f"   Content-Type: {content_type}")
            logger.info(f"   Content-Length: {content_length}")
            logger.info(f"   Content-Disposition: {disposition}")
            logger.info(f"   Taille réponse: {len(decompress_response.content)} bytes")
            
            # Sauvegarder pour vérification
            with open(f"test_decompressed_{result_id}.mp4", 'wb') as f:
                f.write(decompress_response.content)
            
            logger.info(f"💾 Fichier sauvegardé: test_decompressed_{result_id}.mp4")
            
            return True
            
        else:
            logger.error(f"❌ Erreur décompression: {decompress_response.status_code}")
            logger.error(f"Response: {decompress_response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur test: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Test simple de décompression vidéo HCS V2")
    print("=" * 50)
    
    success = test_video_decompression_simple()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Test de décompression vidéo réussi!")
        print("📁 Fichier créé: test_decompressed_*.mp4")
        print("✅ Les corrections devraient résoudre les erreurs 500")
    else:
        print("❌ Le test a échoué")
        print("Vérifiez les logs du serveur pour plus de détails")
