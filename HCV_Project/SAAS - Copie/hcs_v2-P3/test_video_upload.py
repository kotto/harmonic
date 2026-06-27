#!/usr/bin/env python3
"""
Script de test pour l'upload vidéo HCS V2
"""

import requests
import json
import os
import tempfile
import logging
import socket

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
    VIDEO_ENDPOINT = f"{API_BASE_URL}/api/v2/compress/video"
else:
    logger.error("❌ Serveur HCS V2 non trouvé. Démarrez-le d'abord avec: python -m api.server_8008")
    API_BASE_URL = None
    VIDEO_ENDPOINT = None

def create_test_video():
    """Crée un fichier vidéo de test factice"""
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        # Créer un contenu factice qui simule une vidéo
        fake_video_content = b"FAKE_VIDEO_CONTENT_FOR_TESTING_HCS_COMPRESSION" * 1000
        f.write(fake_video_content)
        return f.name

def test_video_upload():
    """Test l'upload vidéo"""
    logger.info("Création d'une vidéo de test...")
    test_video_path = create_test_video()
    
    try:
        logger.info(f"Test avec le fichier: {test_video_path}")
        
        # Préparation du fichier pour l'upload
        with open(test_video_path, 'rb') as f:
            files = {'file': ('test_video.mp4', f, 'video/mp4')}
            
            logger.info("Envoi de la requête d'upload vidéo...")
            response = requests.post(
                VIDEO_ENDPOINT,
                files=files,
                timeout=30
            )
        
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✅ Upload vidéo réussi!")
            logger.info(f"Résultat: {json.dumps(result, indent=2)}")
            return True
        else:
            logger.error(f"❌ Erreur lors de l'upload: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error("❌ Impossible de se connecter au serveur. Assurez-vous que le serveur tourne sur localhost:8008")
        return False
    except Exception as e:
        logger.error(f"❌ Erreur inattendue: {e}")
        return False
    finally:
        # Nettoyage
        if os.path.exists(test_video_path):
            os.unlink(test_video_path)
            logger.info("Fichier de test supprimé")

def test_api_health():
    """Test la santé de l'API"""
    if not API_BASE_URL:
        return False
        
    try:
        logger.info("Vérification de la santé de l'API...")
        response = requests.get(f"{API_BASE_URL}/api/v2/health", timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ API est en bonne santé")
            return True
        else:
            logger.error(f"❌ API non disponible: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error("❌ Impossible de se connecter à l'API")
        return False
    except Exception as e:
        logger.error(f"❌ Erreur lors du check santé: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Test de l'upload vidéo HCS V2")
    print("=" * 50)
    
    # Vérifier si le serveur est trouvé
    if not server_port:
        print("\n❌ Serveur HCS V2 non trouvé sur les ports 8008-8099")
        print("📝 Démarrez le serveur avec:")
        print("   cd hcs_v2")
        print("   python -m api.server_8008")
        print("\n💡 Le serveur trouvera automatiquement un port disponible.")
        exit(1)
    
    print(f"✅ Serveur trouvé sur le port {server_port}")
    
    # Test santé API
    if not test_api_health():
        print("\n❌ Le serveur ne répond pas correctement.")
        exit(1)
    
    # Test upload vidéo
    print("\n🎬 Test de l'upload vidéo...")
    success = test_video_upload()
    
    if success:
        print(f"\n✅ Tous les tests sont passés avec succès sur le port {server_port}!")
        print(f"🌐 Interface web: http://localhost:{server_port}/hcs_dashboard_v2")
    else:
        print("\n❌ Des tests ont échoué. Vérifiez les logs du serveur.")
