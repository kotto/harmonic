#!/usr/bin/env python3
"""
Test de compression vidéo/audio réelle avec le backend HCS
"""

import requests
import base64
import json
import time
from pathlib import Path

def test_video_compression():
    """Test de compression vidéo réelle"""
    
    # Utiliser une vidéo de test existante
    video_path = "test_1080p_video.mp4"
    
    if not Path(video_path).exists():
        print(f"❌ Fichier vidéo non trouvé: {video_path}")
        return False
    
    print(f"🎬 Test compression vidéo: {video_path}")
    
    # Lire le fichier vidéo
    with open(video_path, 'rb') as f:
        video_data = f.read()
    
    print(f"📊 Taille originale: {len(video_data) / (1024*1024):.2f} MB")
    
    # Préparer la requête
    url = "http://localhost:8000/api/video-compress"
    files = {'file': (video_path, video_data, 'video/mp4')}
    data = {'priority': 'balanced', 'quality': 85}
    
    start_time = time.time()
    
    try:
        response = requests.post(url, files=files, data=data)
        request_time = time.time() - start_time
        
        print(f"⏱️ Temps de requête: {request_time:.2f}s")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('status') == 'success':
                data = result.get('data', {})
                
                print("✅ Compression vidéo réussie!")
                print(f"📊 Ratio: {data.get('compression_ratio', 0):.2f}x")
                print(f"📊 Espace économisé: {data.get('space_saved_percent', 0):.1f}%")
                print(f"📊 Temps compression: {data.get('compression_time', 0):.2f}s")
                print(f"📊 Méthode: {data.get('method', 'unknown')}")
                print(f"📊 Résolution: {data.get('original_resolution', 'unknown')} → {data.get('target_resolution', 'unknown')}")
                print(f"📊 FPS: {data.get('original_fps', 0):.1f} → {data.get('target_fps', 0):.1f}")
                print(f"📊 Bitrate: {data.get('bitrate', 'unknown')}")
                print(f"📊 Durée: {data.get('duration', 0):.2f}s")
                
                # Vérifier si les données compressées sont présentes
                if 'compressed_data' in data:
                    compressed_size = len(base64.b64decode(data['compressed_data']))
                    print(f"📊 Taille compressée: {compressed_size / (1024*1024):.2f} MB")
                
                return True
            else:
                print(f"❌ Erreur compression: {result.get('error', 'Erreur inconnue')}")
                return False
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            print(f"📊 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur requête: {e}")
        return False

def test_audio_compression():
    """Test de compression audio réelle"""
    
    # Créer un fichier audio de test (simulation)
    print("🎵 Test compression audio")
    
    # Simuler un fichier audio (en réalité, on utiliserait un vrai fichier)
    audio_data = b'\x00' * (1024 * 1024)  # 1MB de silence
    
    print(f"📊 Taille originale: {len(audio_data) / 1024:.2f} KB")
    
    # Préparer la requête
    url = "http://localhost:8000/api/audio-compress"
    files = {'file': ('test_audio.mp3', audio_data, 'audio/mpeg')}
    data = {'priority': 'balanced', 'quality': 85}
    
    start_time = time.time()
    
    try:
        response = requests.post(url, files=files, data=data)
        request_time = time.time() - start_time
        
        print(f"⏱️ Temps de requête: {request_time:.2f}s")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('status') == 'success':
                data = result.get('data', {})
                
                print("✅ Compression audio réussie!")
                print(f"📊 Ratio: {data.get('compression_ratio', 0):.2f}x")
                print(f"📊 Espace économisé: {data.get('space_saved_percent', 0):.1f}%")
                print(f"📊 Temps compression: {data.get('compression_time', 0):.2f}s")
                print(f"📊 Méthode: {data.get('method', 'unknown')}")
                print(f"📊 Bitrate: {data.get('bitrate', 'unknown')}")
                print(f"📊 Sample rate: {data.get('sample_rate', 'unknown')}")
                print(f"📊 Durée: {data.get('duration', 0):.2f}s")
                
                return True
            else:
                print(f"❌ Erreur compression: {result.get('error', 'Erreur inconnue')}")
                return False
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            print(f"📊 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur requête: {e}")
        return False

def main():
    """Fonction principale de test"""
    
    print("🚀 Test de compression vidéo/audio réelle")
    print("=" * 50)
    
    # Test de santé du serveur
    try:
        response = requests.get("http://localhost:8000/api/health")
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Serveur HCS: {health.get('status', 'unknown')}")
            print(f"✅ Compression disponible: {health.get('compression_available', False)}")
        else:
            print("❌ Serveur non disponible")
            return
    except:
        print("❌ Impossible de contacter le serveur")
        return
    
    print("\n" + "=" * 50)
    
    # Test vidéo
    video_success = test_video_compression()
    
    print("\n" + "=" * 50)
    
    # Test audio
    audio_success = test_audio_compression()
    
    print("\n" + "=" * 50)
    print("📊 RÉSULTATS FINAUX:")
    print(f"🎬 Compression vidéo: {'✅ SUCCÈS' if video_success else '❌ ÉCHEC'}")
    print(f"🎵 Compression audio: {'✅ SUCCÈS' if audio_success else '❌ ÉCHEC'}")
    
    if video_success and audio_success:
        print("🎉 TOUS LES TESTS RÉUSSIS!")
    else:
        print("⚠️ CERTAINS TESTS ONT ÉCHOUÉ")

if __name__ == "__main__":
    main()
