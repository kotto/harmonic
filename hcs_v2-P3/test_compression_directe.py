#!/usr/bin/env python3
"""
Test de compression vidéo direct avec métriques complètes
"""

import requests
import base64
import json
import time
import os

def test_compression_video():
    """Test de compression vidéo direct"""
    
    video_path = 'test_1080p_video.mp4'
    
    if os.path.exists(video_path):
        print(f'🎬 Test compression vidéo: {video_path}')
        
        # Obtenir taille originale
        original_size = os.path.getsize(video_path)
        original_size_mb = original_size / (1024 * 1024)
        print(f'📊 Taille originale: {original_size_mb:.2f} MB')
        
        # Préparer upload
        with open(video_path, 'rb') as f:
            video_data = f.read()
        
        # Test API
        url = 'http://localhost:8000/api/video-compress'
        files = {'file': (video_path, video_data, 'video/mp4')}
        data = {'priority': 'balanced', 'quality': 85}
        
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
                    jpeg_quality = data.get('jpeg_quality', 0)
                    
                    compressed_size = original_size / ratio
                    compressed_size_mb = compressed_size / (1024 * 1024)
                    
                    print(f'✅ Compression réussie!')
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
                    print(f'📊 Qualité JPEG: {jpeg_quality}')
                    
                    if ratio >= 176:
                        print(f'🎉 OBJECTIF 176:1 ATTEINT: {ratio:.1f}x!')
                    else:
                        print(f'⚠️ Objectif manqué: {ratio:.1f}x < 176x')
                        print(f'📊 Marge amélioration: {176/ratio:.1f}x nécessaire')
                    
                    # Métriques supplémentaires
                    print(f'')
                    print(f'📈 Métriques supplémentaires:')
                    print(f'📊 Réduction taille: {(1 - compressed_size/original_size)*100:.1f}%')
                    print(f'📊 Efficacité temps: {original_size_mb/comp_time:.1f} MB/s')
                    print(f'📊 Ratio qualité/poids: {ratio/comp_time:.1f}x/s')
                    
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
                print(f'📊 Response: {response.text}')
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            print(f'❌ Erreur requête: {e}')
            return {'success': False, 'error': str(e)}
    else:
        print(f'❌ Fichier vidéo non trouvé: {video_path}')
        return {'success': False, 'error': 'Fichier non trouvé'}

def main():
    """Fonction principale"""
    
    print("🚀 Test Compression Vidéo Directe")
    print("=" * 50)
    
    result = test_compression_video()
    
    print("")
    print("=" * 50)
    print("📊 RÉSULTATS FINAUX:")
    
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
