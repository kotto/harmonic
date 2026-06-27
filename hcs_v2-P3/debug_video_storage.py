#!/usr/bin/env python3
"""
Script de debug amélioré pour diagnostiquer les problèmes vidéo
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
    """Trouve le port du serveur"""
    for port in range(8008, 8100):
        try:
            response = requests.get(f'http://localhost:{port}/api/v2/health', timeout=2)
            if response.status_code == 200:
                print(f'Serveur trouvé sur le port {port}')
                return port
        except:
            continue
    return None

def test_video_upload_detailed():
    """Test détaillé de l'upload vidéo"""
    server_port = find_server_port()
    if not server_port:
        print('Serveur non trouvé')
        return
    
    # Créer une vidéo MP4 valide très simple
    print("Création d'une vidéo MP4 de test...")
    
    # Créer un fichier MP4 minimaliste
    mp4_header = b'\x00\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00\x00mp42isom\x00\x00\x00\x00\x00mp41\x00\x00\x00\x00'
    mp4_data = mp4_header + b'FAKE_VIDEO_DATA' * 100  # ~1KB
    
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        f.write(mp4_data)
        f.flush()
        test_file = f.name
    
    print(f"Fichier de test créé: {test_file}")
    print(f"Taille: {os.path.getsize(test_file)} bytes")
    
    try:
        # Test avec différents content-types
        content_types = [
            'video/mp4',
            'video/webm', 
            'video/avi',
            'video/quicktime'
        ]
        
        for content_type in content_types:
            print(f"\n--- Test avec content-type: {content_type} ---")
            
            with open(test_file, 'rb') as video_file:
                files = {
                    'file': ('test_video.mp4', video_file, content_type)
                }
                
                response = requests.post(
                    f'http://localhost:{server_port}/api/v2/compress/video', 
                    files=files, 
                    timeout=30
                )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                result_id = result['result_id']
                print(f"✅ Succès! ID: {result_id}")
                
                # Test décompression
                decompress_response = requests.get(
                    f'http://localhost:{server_port}/api/v2/decompress/{result_id}', 
                    timeout=10
                )
                print(f"Décompression status: {decompress_response.status_code}")
                
                if decompress_response.status_code == 200:
                    print("✅ Décompression réussie!")
                else:
                    print(f"❌ Erreur décompression: {decompress_response.text}")
                
                break  # Sortir si succès
            else:
                print(f"❌ Erreur: {response.text}")
        
    except Exception as e:
        print(f"❌ Exception: {e}")
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)

if __name__ == "__main__":
    print("🔍 Debug détaillé de l'upload vidéo HCS V2")
    print("=" * 50)
    test_video_upload_detailed()
