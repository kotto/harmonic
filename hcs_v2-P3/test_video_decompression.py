#!/usr/bin/env python3
"""
Script de test spécifique pour la décompression vidéo HCS V2
"""

import requests
import json
import os
import tempfile
import logging
import webbrowser
import numpy as np

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
    logger.error("❌ Serveur HCS V2 non trouvé")
    exit(1)

def create_test_video():
    """Crée une vidéo de test simple avec OpenCV"""
    try:
        import cv2
        
        # Créer une vidéo temporaire
        temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_video.close()
        
        # Paramètres vidéo
        width, height = 320, 240  # Plus petit pour test rapide
        fps = 10
        duration = 3  # 3 secondes
        total_frames = fps * duration
        
        # Créer vidéo avec OpenCV
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_video.name, fourcc, fps, (width, height))
        
        for i in range(total_frames):
            # Créer une frame simple
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Ajouter un cercle qui bouge
            center_x = int(width/2 + 50 * np.sin(2 * np.pi * i / total_frames))
            center_y = int(height/2 + 30 * np.cos(2 * np.pi * i / total_frames))
            
            cv2.circle(frame, (center_x, center_y), 20, (0, 255, 0), -1)
            cv2.circle(frame, (width - center_x, center_y), 15, (255, 0, 0), -1)
            
            # Ajouter du texte
            cv2.putText(frame, f'Frame {i+1}/{total_frames}', (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Ajouter un rectangle coloré
            cv2.rectangle(frame, (10, 50), (100, 80), (0, 0, 255), 2)
            
            out.write(frame)
        
        out.release()
        logger.info(f"Vidéo de test créée: {temp_video.name}")
        return temp_video.name
        
    except ImportError:
        logger.error("❌ OpenCV non disponible")
        return None
    except Exception as e:
        logger.error(f"❌ Erreur création vidéo: {e}")
        return None

def test_video_decompression():
    """Test spécifique de la décompression vidéo"""
    logger.info("🎬 Test de décompression vidéo...")
    
    test_video_path = create_test_video()
    
    if not test_video_path:
        logger.error("❌ Impossible de créer une vidéo de test")
        return False
    
    try:
        # 1. Compresser la vidéo
        with open(test_video_path, 'rb') as f:
            files = {'file': ('test_video.mp4', f, 'video/mp4')}
            
            logger.info("📤 Compression de la vidéo...")
            response = requests.post(VIDEO_ENDPOINT, files=files, timeout=120)
        
        if response.status_code != 200:
            logger.error(f"❌ Erreur compression: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
        
        result = response.json()
        result_id = result['result_id']
        logger.info(f"✅ Vidéo compressée - ID: {result_id}")
        logger.info(f"   Taille originale: {result['original_size']} bytes")
        logger.info(f"   Taille compressée: {result['compressed_size']} bytes")
        logger.info(f"   Ratio: {result['compression_ratio']:.1f}:1")
        
        # 2. Tester la décompression
        logger.info("📥 Test de décompression vidéo...")
        decompress_url = f"{API_BASE_URL}/api/v2/decompress/{result_id}"
        decompress_response = requests.get(decompress_url, timeout=30)
        
        if decompress_response.status_code == 200:
            logger.info("✅ Décompression vidéo réussie!")
            
            # Vérifier les en-têtes
            content_type = decompress_response.headers.get('content-type', '')
            content_length = decompress_response.headers.get('content-length', '0')
            disposition = decompress_response.headers.get('content-disposition', '')
            
            logger.info(f"   Content-Type: {content_type}")
            logger.info(f"   Content-Length: {content_length}")
            logger.info(f"   Content-Disposition: {disposition}")
            
            # Sauvegarder la vidéo décompressée
            decompressed_path = f"decompressed_video_{result_id}.mp4"
            with open(decompressed_path, 'wb') as f:
                f.write(decompress_response.content)
            
            logger.info(f"💾 Vidéo décompressée sauvegardée: {decompressed_path}")
            logger.info(f"   Taille: {len(decompress_response.content)} bytes")
            
            # 3. Tester le téléchargement
            logger.info("⬇️ Test de téléchargement vidéo...")
            download_url = f"{API_BASE_URL}/api/v2/download/{result_id}"
            download_response = requests.get(download_url, timeout=30)
            
            if download_response.status_code == 200:
                logger.info("✅ Téléchargement vidéo réussi!")
                
                # Sauvegarder le fichier compressé
                compressed_path = f"compressed_video_{result_id}.hcs"
                with open(compressed_path, 'wb') as f:
                    f.write(download_response.content)
                
                logger.info(f"💾 Fichier compressé sauvegardé: {compressed_path}")
                logger.info(f"   Taille: {len(download_response.content)} bytes")
                
            else:
                logger.error(f"❌ Erreur téléchargement: {download_response.status_code}")
                return False
            
            # 4. Créer une page HTML pour tester l'affichage
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Décompression Vidéo HCS V2</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .video-container {{ margin: 20px 0; }}
        .stats {{ background: #f0f0f0; padding: 10px; margin: 10px 0; }}
        video {{ max-width: 600px; }}
    </style>
</head>
<body>
    <h1>🎬 Test Décompression Vidéo HCS V2</h1>
    
    <div class="stats">
        <h2>📊 Statistiques</h2>
        <p><strong>ID:</strong> {result_id}</p>
        <p><strong>Taille originale:</strong> {result['original_size']} bytes</p>
        <p><strong>Taille compressée:</strong> {result['compressed_size']} bytes</p>
        <p><strong>Ratio:</strong> {result['compression_ratio']:.1f}:1</p>
    </div>
    
    <div class="video-container">
        <h2>📥 Vidéo Décompressée</h2>
        <video controls autoplay loop>
            <source src="{decompress_url}" type="video/mp4">
            Votre navigateur ne supporte pas la lecture vidéo.
        </video>
    </div>
    
    <div class="video-container">
        <h2>📊 Informations</h2>
        <p><strong>URL Décompression:</strong> <a href="{decompress_url}">{decompress_url}</a></p>
        <p><strong>URL Téléchargement:</strong> <a href="{download_url}">{download_url}</a></p>
    </div>
    
    <script>
        // Log des erreurs vidéo
        document.querySelector('video').addEventListener('error', function(e) {{
            console.error('Erreur vidéo:', e);
            console.error('Code erreur:', this.error ? this.error.code : 'Inconnu');
            console.error('Message:', this.error ? this.error.message : 'Inconnu');
        }});
        
        // Log de chargement réussi
        document.querySelector('video').addEventListener('loadeddata', function() {{
            console.log('Vidéo chargée avec succès');
        }});
    </script>
</body>
</html>
            """
            
            html_path = f"video_test_{result_id}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"🌐 Page HTML créée: {html_path}")
            
            # Ouvrir la page HTML
            file_url = f"file://{os.path.abspath(html_path)}"
            logger.info(f"🌐 Ouverture: {file_url}")
            webbrowser.open(file_url)
            
            return True
            
        else:
            logger.error(f"❌ Erreur décompression: {decompress_response.status_code}")
            logger.error(f"Response: {decompress_response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur test vidéo: {e}")
        return False
    finally:
        if test_video_path and os.path.exists(test_video_path):
            os.unlink(test_video_path)

if __name__ == "__main__":
    print("🧪 Test de décompression vidéo HCS V2")
    print("=" * 60)
    
    print(f"✅ Serveur trouvé sur le port {server_port}")
    
    # Test vidéo
    success = test_video_decompression()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Test de décompression vidéo réussi!")
        print("📁 Fichiers créés:")
        print("   - Vidéo décompressée: decompressed_video_*.mp4")
        print("   - Fichier compressé: compressed_video_*.hcs")
        print("   - Page test HTML: video_test_*.html")
        print("\n🌐 La page HTML s'ouvrira automatiquement pour tester l'affichage")
    else:
        print("❌ Le test de décompression vidéo a échoué")
        print("Vérifiez les logs du serveur pour plus de détails")
