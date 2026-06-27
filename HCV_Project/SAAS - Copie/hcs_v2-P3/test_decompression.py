#!/usr/bin/env python3
"""
Script de test pour la décompression et le téléchargement HCS V2
"""

import requests
import json
import os
import tempfile
import logging
import webbrowser
from urllib.parse import urljoin

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

# Configuration API (dynamique)
server_port = find_server_port()
if server_port:
    API_BASE_URL = f"http://localhost:{server_port}"
    IMAGE_ENDPOINT = f"{API_BASE_URL}/api/v2/compress/image"
    VIDEO_ENDPOINT = f"{API_BASE_URL}/api/v2/compress/video"
else:
    logger.error("❌ Serveur HCS V2 non trouvé")
    exit(1)

def create_test_image():
    """Crée une image de test simple"""
    from PIL import Image
    import numpy as np
    
    # Créer une image simple
    width, height = 400, 300
    image = Image.new('RGB', (width, height), color='blue')
    
    # Ajouter du texte
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    draw.text((50, 50), "HCS V2 Test", fill='white', font=font)
    draw.text((50, 80), "Compression Test", fill='white', font=font)
    
    # Sauvegarder temporairement
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        image.save(f.name, 'PNG')
        return f.name

def test_decompression_and_download():
    """Test la décompression et le téléchargement"""
    logger.info("🔄 Test de décompression et téléchargement...")
    
    # 1. Compresser une image
    test_image_path = create_test_image()
    
    try:
        with open(test_image_path, 'rb') as f:
            files = {'file': ('test_image.png', f, 'image/png')}
            
            logger.info("📤 Compression de l'image...")
            response = requests.post(IMAGE_ENDPOINT, files=files, timeout=60)
        
        if response.status_code != 200:
            logger.error(f"❌ Erreur compression: {response.status_code}")
            return False
        
        result = response.json()
        result_id = result['result_id']
        logger.info(f"✅ Image compressée - ID: {result_id}")
        
        # 2. Tester la décompression
        logger.info("📥 Test de décompression...")
        decompress_url = f"{API_BASE_URL}/api/v2/decompress/{result_id}"
        decompress_response = requests.get(decompress_url, timeout=30)
        
        if decompress_response.status_code == 200:
            logger.info("✅ Décompression réussie!")
            
            # Sauvegarder l'image décompressée
            decompressed_path = f"decompressed_{result_id}.png"
            with open(decompressed_path, 'wb') as f:
                f.write(decompress_response.content)
            
            logger.info(f"💾 Image décompressée sauvegardée: {decompressed_path}")
            
            # Ouvrir dans le navigateur
            file_url = f"file://{os.path.abspath(decompressed_path)}"
            logger.info(f"🌐 URL locale: {file_url}")
            
        else:
            logger.error(f"❌ Erreur décompression: {decompress_response.status_code}")
            logger.error(f"Response: {decompress_response.text}")
            return False
        
        # 3. Tester le téléchargement
        logger.info("⬇️ Test de téléchargement...")
        download_url = f"{API_BASE_URL}/api/v2/download/{result_id}"
        download_response = requests.get(download_url, timeout=30)
        
        if download_response.status_code == 200:
            logger.info("✅ Téléchargement réussi!")
            
            # Sauvegarder le fichier compressé
            compressed_path = f"compressed_{result_id}.webp"
            with open(compressed_path, 'wb') as f:
                f.write(download_response.content)
            
            logger.info(f"💾 Fichier compressé sauvegardé: {compressed_path}")
            
            # Afficher les tailles
            original_size = result['original_size']
            compressed_size = len(download_response.content)
            ratio = original_size / compressed_size if compressed_size > 0 else 0
            
            logger.info(f"📊 Taille originale: {original_size} bytes")
            logger.info(f"📊 Taille compressée: {compressed_size} bytes")
            logger.info(f"📊 Ratio: {ratio:.1f}:1")
            
        else:
            logger.error(f"❌ Erreur téléchargement: {download_response.status_code}")
            logger.error(f"Response: {download_response.text}")
            return False
        
        # 4. Ouvrir l'interface web
        dashboard_url = f"{API_BASE_URL}/hcs_dashboard_v2"
        logger.info(f"🌐 Ouverture du dashboard: {dashboard_url}")
        webbrowser.open(dashboard_url)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test: {e}")
        return False
    finally:
        if os.path.exists(test_image_path):
            os.unlink(test_image_path)

if __name__ == "__main__":
    print("🧪 Test de décompression et téléchargement HCS V2")
    print("=" * 60)
    
    print(f"✅ Serveur trouvé sur le port {server_port}")
    
    # Test complet
    success = test_decompression_and_download()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Tous les tests de décompression/téléchargement réussis!")
        print("📁 Fichiers créés:")
        print("   - Image décompressée: decompressed_*.png")
        print("   - Fichier compressé: compressed_*.webp")
        print(f"🌐 Dashboard: http://localhost:{server_port}/hcs_dashboard_v2")
    else:
        print("❌ Certains tests ont échoué. Vérifiez les logs.")
