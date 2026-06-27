#!/usr/bin/env python3
"""
Test compression vidéo avec priorité SPEED
"""

import requests
import time
import os

def test_speed_priority():
    """Test avec priorité speed"""
    
    video_path = 'test_1080p_video.mp4'
    
    if os.path.exists(video_path):
        print('🎬 Test compression vidéo (priorité SPEED)')
        
        original_size = os.path.getsize(video_path)
        original_size_mb = original_size / (1024 * 1024)
        print(f'📊 Taille originale: {original_size_mb:.2f} MB')
        
        with open(video_path, 'rb') as f:
            video_data = f.read()
        
        # Test avec priorité speed
        url = 'http://localhost:8000/api/video-compress'
        files = {'file': (video_path, video_data, 'video/mp4')}
        data = {'priority': 'speed', 'quality': 85}
        
        start_time = time.time()
        
        try:
            response = requests.post(url, files=files, data=data)
            request_time = time.time() - start_time
            
            print(f'⏱️ Temps de requête: {request_time:.2f}s')
            print(f'📊 Status: {response.status_code}')
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == 'success':
                    data = result.get('data', {})
                    
                    ratio = data.get('compression_ratio', 0)
                    space_saved = data.get('space_saved_percent', 0)
                    comp_time = data.get('compression_time', 0)
                    method = data.get('method', 'unknown')
                    original_res = data.get('original_resolution', 'unknown')
                    target_res = data.get('target_resolution', 'unknown')
                    original_fps = data.get('original_fps', 0)
                    target_fps = data.get('target_fps', 0)
                    codec = data.get('codec', 'unknown')
                    
                    compressed_size = original_size / ratio
                    compressed_size_mb = compressed_size / (1024 * 1024)
                    
                    print(f'✅ Compression SPEED réussie!')
                    print(f'📊 Ratio: {ratio:.1f}x')
                    print(f'📊 Espace économisé: {space_saved:.1f}%')
                    print(f'📊 Temps compression: {comp_time:.2f}s')
                    print(f'📊 Taille compressée: {compressed_size_mb:.3f} MB')
                    print(f'📊 Méthode: {method}')
                    print(f'📊 Codec: {codec}')
                    print(f'')
                    print(f'🔧 Détails techniques:')
                    print(f'📊 Résolution: {original_res} → {target_res}')
                    print(f'📊 FPS: {original_fps:.1f} → {target_fps:.1f}')
                    
                    if ratio >= 176:
                        print(f'🎉 OBJECTIF 176:1 ATTEINT: {ratio:.1f}x!')
                    else:
                        print(f'⚠️ Objectif manqué: {ratio:.1f}x < 176x')
                        print(f'📊 Marge amélioration: {176/ratio:.1f}x nécessaire')
                    
                    return {
                        'success': True,
                        'ratio': ratio,
                        'original_size_mb': original_size_mb,
                        'compressed_size_mb': compressed_size_mb,
                        'compression_time': comp_time,
                        'method': method,
                        'codec': codec,
                        'target_achieved': ratio >= 176
                    }
                    
                else:
                    print(f'❌ Erreur compression: {result.get("error", "Erreur inconnue")}')
                    return {'success': False, 'error': result.get('error')}
            else:
                print(f'❌ Erreur HTTP: {response.status_code}')
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            print(f'❌ Erreur requête: {e}')
            return {'success': False, 'error': str(e)}
    else:
        print(f'❌ Fichier vidéo non trouvé: {video_path}')
        return {'success': False, 'error': 'Fichier non trouvé'}

def main():
    """Fonction principale"""
    
    print("🚀 Test Compression Vidéo - Priority SPEED")
    print("=" * 50)
    
    result = test_speed_priority()
    
    print("")
    print("=" * 50)
    print("📊 RÉSULTATS SPEED:")
    
    if result.get('success'):
        print(f"✅ Test réussi")
        print(f"📊 Ratio: {result.get('ratio', 0):.1f}x")
        print(f"📊 Taille: {result.get('original_size_mb', 0):.2f} MB → {result.get('compressed_size_mb', 0):.3f} MB")
        print(f"📊 Temps: {result.get('compression_time', 0):.2f}s")
        print(f"📊 Méthode: {result.get('method', 'unknown')}")
        print(f"🎯 Objectif 176x: {'✅ ATTEINT' if result.get('target_achieved') else '❌ MANQUÉ'}")
    else:
        print(f"❌ Test échoué: {result.get('error', 'Erreur inconnue')}")

if __name__ == "__main__":
    main()
