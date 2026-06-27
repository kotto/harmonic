#!/usr/bin/env python3
"""
Script de test final pour la compression vidéo HCS V2
"""

import requests
import json
import tempfile
import os

def find_server_port():
    """Trouve le port du serveur"""
    for port in range(8008, 8100):
        try:
            response = requests.get(f'http://localhost:{port}/api/v2/health', timeout=2)
            if response.status_code == 200:
                return port
        except:
            continue
    return None

def test_final_video():
    """Test final de la compression vidéo"""
    server_port = find_server_port()
    if not server_port:
        print('❌ Serveur non trouvé')
        return
    
    print(f'🚀 Test final sur le port {server_port}')
    
    # Créer un fichier vidéo très simple
    test_data = b'FAKE_VIDEO_MP4_HEADER' + b'\x00' * 1000  # ~1KB
    
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        f.write(test_data)
        test_file = f.name
    
    try:
        # Test avec le content-type le plus simple
        with open(test_file, 'rb') as video_file:
            files = {
                'file': ('simple_test.mp4', video_file, 'video/mp4')
            }
            
            print("📤 Envoi de la vidéo...")
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
            
            if decompress_response.status_code == 200:
                print("✅ Décompression réussie!")
                print(f"Taille: {len(decompress_response.content)} bytes")
                print(f"Content-Type: {decompress_response.headers.get('content-type', 'N/A')}")
                
                # Sauvegarder
                with open(f"final_test_decompressed_{result_id}.mp4", 'wb') as f:
                    f.write(decompress_response.content)
                print(f"💾 Fichier sauvegardé: final_test_decompressed_{result_id}.mp4")
                
                return True
            else:
                print(f"❌ Erreur décompression: {decompress_response.status_code}")
                print(f"Response: {decompress_response.text}")
        else:
            print(f"❌ Erreur compression: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Exception: {e}")
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)
    
    return False

if __name__ == "__main__":
    print("🧪 Test Final Compression Vidéo HCS V2")
    print("=" * 50)
    
    success = test_final_video()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Test final réussi!")
        print("✅ La compression et décompression vidéo fonctionnent")
    else:
        print("❌ Le test final a échoué")
        print("📋 Vérifiez les logs du serveur pour le diagnostic")
