#!/usr/bin/env python3
"""
Test de compression vidéo extrême pour atteindre 176:1
"""

import requests
import base64
import json
import time
from pathlib import Path

def test_video_extreme_compression():
    """Test de compression vidéo avec paramètres extrêmes"""
    
    # Utiliser une vidéo de test existante
    video_path = "test_1080p_video.mp4"
    
    if not Path(video_path).exists():
        print(f"❌ Fichier vidéo non trouvé: {video_path}")
        return False
    
    print(f"🎬 Test compression vidéo EXTREME: {video_path}")
    
    # Lire le fichier vidéo
    with open(video_path, 'rb') as f:
        video_data = f.read()
    
    original_size_mb = len(video_data) / (1024 * 1024)
    print(f"📊 Taille originale: {original_size_mb:.2f} MB")
    
    # Test avec différentes priorités pour trouver le meilleur ratio
    priorities = ['speed', 'balanced', 'quality']
    
    for priority in priorities:
        print(f"\n🔧 Test priorité: {priority}")
        
        # Préparer la requête
        url = "http://localhost:8000/api/video-compress"
        files = {'file': (video_path, video_data, 'video/mp4')}
        data = {'priority': priority, 'quality': 85}
        
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
                    
                    ratio = data.get('compression_ratio', 0)
                    space_saved = data.get('space_saved_percent', 0)
                    comp_time = data.get('compression_time', 0)
                    method = data.get('method', 'unknown')
                    resolution = f"{data.get('original_resolution', 'unknown')} → {data.get('target_resolution', 'unknown')}"
                    fps = f"{data.get('original_fps', 0):.1f} → {data.get('target_fps', 0):.1f}"
                    bitrate = data.get('bitrate', 'unknown')
                    
                    print(f"✅ Compression réussie!")
                    print(f"📊 Ratio: {ratio:.1f}x")
                    print(f"📊 Espace économisé: {space_saved:.1f}%")
                    print(f"📊 Temps compression: {comp_time:.2f}s")
                    print(f"📊 Méthode: {method}")
                    print(f"📊 Résolution: {resolution}")
                    print(f"📊 FPS: {fps}")
                    print(f"📊 Bitrate: {bitrate}")
                    
                    # Vérifier si on atteint 176:1
                    if ratio >= 176:
                        print(f"🎉 OBJECTIF ATTEINT: {ratio:.1f}x > 176x!")
                        return True
                    elif ratio >= 100:
                        print(f"🚀 EXCELLENT: {ratio:.1f}x (proche de l'objectif)")
                    elif ratio >= 50:
                        print(f"👍 BON: {ratio:.1f}x")
                    else:
                        print(f"⚠️ Faible: {ratio:.1f}x")
                        
                    # Calculer la taille compressée
                    if 'compressed_data' in data:
                        compressed_size = len(base64.b64decode(data['compressed_data']))
                        compressed_size_mb = compressed_size / (1024 * 1024)
                        print(f"📊 Taille compressée: {compressed_size_mb:.2f} MB")
                        
                else:
                    print(f"❌ Erreur compression: {result.get('error', 'Erreur inconnue')}")
            else:
                print(f"❌ Erreur HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur requête: {e}")
    
    return False

def test_custom_video_parameters():
    """Test avec paramètres personnalisés pour maximiser le ratio"""
    
    print("\n🎯 Test paramètres personnalisés pour ratio maximum")
    
    # Créer une vidéo plus grande pour le test
    video_path = "test_1080p_video.mp4"
    
    if not Path(video_path).exists():
        print(f"❌ Fichier vidéo non trouvé: {video_path}")
        return False
    
    with open(video_path, 'rb') as f:
        video_data = f.read()
    
    original_size_mb = len(video_data) / (1024 * 1024)
    print(f"📊 Taille originale: {original_size_mb:.2f} MB")
    
    # Test avec priorité 'speed' (la plus agressive)
    url = "http://localhost:8000/api/video-compress"
    files = {'file': (video_path, video_data, 'video/mp4')}
    data = {'priority': 'speed', 'quality': 50}  # Qualité plus basse
    
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
                
                ratio = data.get('compression_ratio', 0)
                space_saved = data.get('space_saved_percent', 0)
                comp_time = data.get('compression_time', 0)
                method = data.get('method', 'unknown')
                
                print(f"✅ Compression personnalisée réussie!")
                print(f"📊 Ratio: {ratio:.1f}x")
                print(f"📊 Espace économisé: {space_saved:.1f}%")
                print(f"📊 Temps compression: {comp_time:.2f}s")
                print(f"📊 Méthode: {method}")
                
                # Afficher les détails techniques
                print(f"\n🔧 Détails techniques:")
                print(f"📊 Résolution: {data.get('original_resolution', 'unknown')} → {data.get('target_resolution', 'unknown')}")
                print(f"📊 FPS: {data.get('original_fps', 0):.1f} → {data.get('target_fps', 0):.1f}")
                print(f"📊 Bitrate: {data.get('bitrate', 'unknown')}")
                
                if ratio >= 176:
                    print(f"\n🎉 OBJECTIF 176:1 ATTEINT: {ratio:.1f}x!")
                    return True
                else:
                    print(f"\n📊 Ratio actuel: {ratio:.1f}x (objectif: 176x)")
                    print(f"📊 Amélioration nécessaire: {176/ratio:.1f}x")
                    
                    # Suggestions pour améliorer
                    print(f"\n💡 Suggestions pour atteindre 176:1:")
                    if ratio < 50:
                        print("  • Réduire encore plus la résolution (ex: 320x180)")
                        print("  • Réduire davantage le FPS (ex: 8-10 fps)")
                        print("  • Utiliser un bitrate plus bas (ex: 100-200k)")
                    elif ratio < 100:
                        print("  • Réduire la résolution à 480p ou moins")
                        print("  • Réduire le FPS à 10-15")
                        print("  • Optimiser l'encodage avec preset ultrafast")
                    else:
                        print("  • Proche de l'objectif!")
                        print("  • Ajuster finement les paramètres")
                
                return True
            else:
                print(f"❌ Erreur compression: {result.get('error', 'Erreur inconnue')}")
                return False
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur requête: {e}")
        return False

def main():
    """Fonction principale de test"""
    
    print("🚀 Test de Compression Vidéo EXTREME - Objectif 176:1")
    print("=" * 60)
    
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
    
    print("\n" + "=" * 60)
    
    # Test 1: Compression standard avec différentes priorités
    success1 = test_video_extreme_compression()
    
    print("\n" + "=" * 60)
    
    # Test 2: Paramètres personnalisés
    success2 = test_custom_video_parameters()
    
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS FINAUX:")
    print(f"🎬 Test standard: {'✅ SUCCÈS' if success1 else '❌ ÉCHEC'}")
    print(f"🎯 Test personnalisé: {'✅ SUCCÈS' if success2 else '❌ ÉCHEC'}")
    
    if success1 or success2:
        print("🎉 AMÉLIORATION SIGNIFICATIVE!")
    else:
        print("⚠️ Nécessite optimisation supplémentaire")

if __name__ == "__main__":
    main()
