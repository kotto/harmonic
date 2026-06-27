#!/usr/bin/env python3
"""
Test API Phase 2 - Validation des endpoints v2
"""

import requests
import base64
import json
import time
from pathlib import Path

def test_phase2_api():
    """Test des API endpoints Phase 2"""
    
    print("🚀 Test API Phase 2 - Ultimate Compression")
    print("=" * 50)
    
    # Test health endpoint
    try:
        response = requests.get("http://localhost:8000/api/v2/health")
        if response.status_code == 200:
            health = response.json()
            print("✅ Health check Phase 2:")
            print(f"   Status: {health.get('status')}")
            print(f"   Phase: {health.get('phase')}")
            print(f"   Version: {health.get('version')}")
            print(f"   Ultimate mode: {health.get('ultimate_mode')}")
            print(f"   Target ratio: {health.get('target_ratio')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test stats endpoint
    try:
        response = requests.get("http://localhost:8000/api/v2/stats")
        if response.status_code == 200:
            stats = response.json()
            print("\n📊 Stats Phase 2:")
            print(f"   Status: {stats.get('status')}")
            print(f"   Phase: {stats.get('phase')}")
            print(f"   System type: {stats.get('system_type')}")
            print(f"   Features: {len(stats.get('features', []))} available")
        else:
            print(f"❌ Stats check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Stats check error: {e}")
    
    # Test compression vidéo avec API v2
    video_path = "test_1080p_video.mp4"
    if Path(video_path).exists():
        print(f"\n🎬 Test compression vidéo API v2: {video_path}")
        
        with open(video_path, 'rb') as f:
            video_data = f.read()
        
        original_size_mb = len(video_data) / (1024 * 1024)
        print(f"📊 Taille originale: {original_size_mb:.2f} MB")
        
        # Test endpoint v2
        url = "http://localhost:8000/api/v2/video-compress"
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
                    
                    ratio = data.get('compression_ratio', 0)
                    space_saved = data.get('space_saved_percent', 0)
                    comp_time = data.get('compression_time', 0)
                    method = data.get('method', 'unknown')
                    phase = data.get('phase', 'unknown')
                    target_achieved = data.get('target_achieved', False)
                    
                    print(f"✅ Compression API v2 réussie!")
                    print(f"📊 Ratio: {ratio:.1f}x")
                    print(f"📊 Espace économisé: {space_saved:.1f}%")
                    print(f"📊 Temps compression: {comp_time:.2f}s")
                    print(f"📊 Méthode: {method}")
                    print(f"📊 Phase: {phase}")
                    print(f"🎯 Objectif 176x atteint: {'✅ OUI' if target_achieved else '❌ NON'}")
                    
                    # Afficher détails techniques
                    print(f"\n🔧 Détails techniques:")
                    print(f"📊 Résolution: {data.get('original_resolution')} → {data.get('target_resolution')}")
                    print(f"📊 FPS: {data.get('original_fps'):.1f} → {data.get('target_fps'):.1f}")
                    print(f"📊 Codec: {data.get('codec')}")
                    print(f"📊 Qualité JPEG: {data.get('jpeg_quality')}")
                    
                    if ratio >= 176:
                        print(f"\n🎉 OBJECTIF 176:1 ATTEINT: {ratio:.1f}x!")
                        return True
                    else:
                        print(f"\n⚠️ Objectif manqué: {ratio:.1f}x < 176x")
                        return False
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
    else:
        print(f"❌ Fichier vidéo non trouvé: {video_path}")
        return False

def main():
    """Fonction principale"""
    
    print("🚀 Test API Phase 2 - Ultimate Compression")
    print("=" * 60)
    
    success = test_phase2_api()
    
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS FINAUX:")
    print(f"🎬 API Phase 2: {'✅ SUCCÈS' if success else '❌ ÉCHEC'}")
    
    if success:
        print("🎉 API Phase 2 opérationnelle!")
        print("🚀 Prête pour Phase 3: Déploiement!")
    else:
        print("⚠️ API Phase 2 nécessite ajustements")

if __name__ == "__main__":
    main()
