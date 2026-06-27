#!/usr/bin/env python3
"""
Script de test pour les compressions réelles HCS V2
"""

import requests
import json
import os
import tempfile
import logging
import numpy as np
from PIL import Image
import io

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
    logger.error("❌ Serveur HCS V2 non trouvé. Démarrez-le d'abord avec: python -m api.server_8008")
    API_BASE_URL = None
    IMAGE_ENDPOINT = None
    VIDEO_ENDPOINT = None

def create_test_image():
    """Crée une image de test réelle"""
    # Créer une image avec des motifs variés
    width, height = 800, 600
    image = Image.new('RGB', (width, height))
    
    # Ajouter des motifs pour tester la compression
    pixels = []
    for y in range(height):
        for x in range(width):
            # Créer un dégradé avec du bruit
            r = int(255 * (x / width))
            g = int(255 * (y / height))
            b = int(255 * ((x + y) / (width + height)))
            
            # Ajouter du bruit pour complexifier
            if (x + y) % 10 == 0:
                r = (r + 128) % 256
                g = (g + 128) % 256
                b = (b + 128) % 256
            
            pixels.append((r, g, b))
    
    image.putdata(pixels)
    
    # Sauvegarder temporairement
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        image.save(f.name, 'PNG')
        return f.name

def create_test_video():
    """Crée une vidéo de test simple avec OpenCV"""
    try:
        import cv2
        
        # Créer une vidéo temporaire
        temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_video.close()
        
        # Paramètres vidéo
        width, height = 640, 480
        fps = 30
        duration = 2  # 2 secondes
        total_frames = fps * duration
        
        # Créer vidéo avec OpenCV
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_video.name, fourcc, fps, (width, height))
        
        for i in range(total_frames):
            # Créer une frame avec des motifs changeants
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Ajouter des cercles qui bougent
            center_x = int(width/2 + 200 * np.sin(2 * np.pi * i / total_frames))
            center_y = int(height/2 + 150 * np.cos(2 * np.pi * i / total_frames))
            
            cv2.circle(frame, (center_x, center_y), 50, (0, 255, 0), -1)
            cv2.circle(frame, (width - center_x, center_y), 30, (255, 0, 0), -1)
            cv2.circle(frame, (center_x, height - center_y), 40, (0, 0, 255), -1)
            
            # Ajouter du texte
            cv2.putText(frame, f'Frame {i}/{total_frames}', (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            out.write(frame)
        
        out.release()
        return temp_video.name
        
    except ImportError:
        logger.error("❌ OpenCV non disponible pour créer une vidéo de test")
        return None

def test_real_image_compression():
    """Test la compression réelle d'image"""
    logger.info("🖼️ Test de compression d'image réelle...")
    
    test_image_path = create_test_image()
    
    try:
        with open(test_image_path, 'rb') as f:
            files = {'file': ('test_image.png', f, 'image/png')}
            
            logger.info("Envoi de l'image pour compression réelle...")
            response = requests.post(IMAGE_ENDPOINT, files=files, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✅ Compression image réussie!")
            logger.info(f"Ratio: {result.get('compression_ratio', 'N/A'):.1f}:1")
            logger.info(f"Taille originale: {result.get('original_size', 0)} bytes")
            logger.info(f"Taille compressée: {result.get('compressed_size', 0)} bytes")
            logger.info(f"Espace économisé: {result.get('space_saved_percent', 0):.1f}%")
            return True
        else:
            logger.error(f"❌ Erreur compression image: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur test image: {e}")
        return False
    finally:
        if os.path.exists(test_image_path):
            os.unlink(test_image_path)

def test_real_video_compression():
    """Test la compression réelle de vidéo"""
    logger.info("🎬 Test de compression vidéo réelle...")
    
    test_video_path = create_test_video()
    
    if not test_video_path:
        logger.error("❌ Impossible de créer une vidéo de test")
        return False
    
    try:
        with open(test_video_path, 'rb') as f:
            files = {'file': ('test_video.mp4', f, 'video/mp4')}
            
            logger.info("Envoi de la vidéo pour compression réelle...")
            response = requests.post(VIDEO_ENDPOINT, files=files, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✅ Compression vidéo réussie!")
            logger.info(f"Ratio: {result.get('compression_ratio', 'N/A'):.1f}:1")
            logger.info(f"Frames traitées: {result.get('sample_frames_processed', 0)}")
            logger.info(f"Résolution: {result.get('metadata', {}).get('resolution', 'N/A')}")
            logger.info(f"FPS: {result.get('average_fps', 0):.1f}")
            return True
        else:
            logger.error(f"❌ Erreur compression vidéo: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur test vidéo: {e}")
        return False
    finally:
        if test_video_path and os.path.exists(test_video_path):
            os.unlink(test_video_path)

if __name__ == "__main__":
    print("🧪 Test des compressions RÉELLES HCS V2")
    print("=" * 60)
    
    if not server_port:
        print("\n❌ Serveur HCS V2 non trouvé")
        print("📝 Démarrez le serveur avec:")
        print("   cd hcs_v2")
        print("   python -m api.server_8008")
        exit(1)
    
    print(f"✅ Serveur trouvé sur le port {server_port}")
    
    # Test compression image réelle
    print("\n🖼️ Test compression IMAGE réelle...")
    image_success = test_real_image_compression()
    
    # Test compression vidéo réelle
    print("\n🎬 Test compression VIDÉO réelle...")
    video_success = test_real_video_compression()
    
    # Résultats finaux
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS FINAUX:")
    print(f"   Compression image: {'✅ SUCCÈS' if image_success else '❌ ÉCHEC'}")
    print(f"   Compression vidéo: {'✅ SUCCÈS' if video_success else '❌ ÉCHEC'}")
    
    if image_success and video_success:
        print("\n🎉 Toutes les compressions réelles fonctionnent!")
        print(f"🌐 Interface web: http://localhost:{server_port}/hcs_dashboard_v2")
    else:
        print("\n⚠️ Certains tests ont échoué. Vérifiez les logs.")
