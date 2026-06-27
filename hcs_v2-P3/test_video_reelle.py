#!/usr/bin/env python3
"""
Test de compression vidéo réelle avec métriques complètes
"""

import requests
import time
import os
import json
import base64
import tempfile
from typing import Dict, Any, List

def create_test_video():
    """Créer une vidéo de test réelle"""
    
    try:
        import cv2
        import numpy as np
        
        # Paramètres vidéo
        width, height = 1920, 1080
        fps = 30
        duration = 3  # secondes
        total_frames = fps * duration
        
        # Créer une vidéo avec contenu varié
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        temp_path = tempfile.mktemp(suffix='.mp4')
        
        out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))
        
        print(f"🎬 Création vidéo de test: {width}x{height}, {fps}fps, {duration}s")
        
        for frame_idx in range(total_frames):
            # Créer un frame avec contenu varié
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Fond dégradé
            for y in range(height):
                for x in range(width):
                    frame[y, x] = [
                        int(255 * (x / width)),
                        int(255 * (y / height)),
                        int(255 * ((x + y) / (width + height)))
                    ]
            
            # Ajouter des éléments animés
            t = frame_idx / fps
            
            # Cercle mobile
            center_x = int(width/2 + 200 * np.sin(2 * np.pi * t))
            center_y = int(height/2 + 150 * np.cos(2 * np.pi * t))
            cv2.circle(frame, (center_x, center_y), 50, (255, 255, 255), -1)
            
            # Rectangle rotatif
            rect_center = (width//2, height//2)
            rect_size = (100, 200)
            angle = frame_idx * 2  # Rotation
            rect = ((rect_center[0] - rect_size[0]//2, rect_center[1] - rect_size[1]//2), 
                    rect_size, angle)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            cv2.drawContours(frame, [box], 0, (0, 0, 255), 2)
            
            # Texte
            cv2.putText(frame, f"Frame {frame_idx+1}/{total_frames}", 
                       (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            
            # Ajouter du bruit pour réalisme
            noise = np.random.randint(0, 50, (height, width, 3), dtype=np.uint8)
            frame = cv2.add(frame, noise)
            
            out.write(frame)
        
        out.release()
        
        # Vérifier la taille
        file_size = os.path.getsize(temp_path)
        print(f"✅ Vidéo créée: {temp_path}")
        print(f"📊 Taille: {file_size / (1024*1024):.2f} MB")
        print(f"📊 Frames: {total_frames}")
        print(f"📊 Durée: {duration}s")
        
        return temp_path
        
    except ImportError:
        print("❌ OpenCV non disponible pour créer la vidéo")
        return None
    except Exception as e:
        print(f"❌ Erreur création vidéo: {e}")
        return None

def test_video_compression(video_path: str, api_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """Test complet de compression vidéo"""
    
    print(f"\n🎬 Test de compression vidéo: {os.path.basename(video_path)}")
    print("="*60)
    
    # Obtenir les métriques originales
    original_size = os.path.getsize(video_path)
    original_size_mb = original_size / (1024 * 1024)
    
    print(f"📊 Fichier original:")
    print(f"  📁 Taille: {original_size_mb:.2f} MB ({original_size:,} bytes)")
    print(f"  📂 Chemin: {video_path}")
    
    try:
        # Préparer le fichier pour l'upload
        with open(video_path, 'rb') as f:
            video_data = f.read()
        
        # Test 1: Compression standard (API existante)
        print(f"\n🎯 Test 1: Compression standard")
        print("-" * 40)
        
        start_time = time.time()
        
        files = {'file': (os.path.basename(video_path), video_data, 'video/mp4')}
        data = {'priority': 'balanced'}
        
        response = requests.post(f"{api_url}/api/video-compress", files=files, data=data)
        
        request_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('status') == 'success':
                data = result.get('data', {})
                
                print(f"✅ Compression standard réussie!")
                print(f"⏱️ Temps de requête: {request_time:.2f}s")
                print(f"📊 Ratio: {data.get('compression_ratio', 0):.1f}x")
                print(f"📊 Espace économisé: {data.get('space_saved_percent', 0):.1f}%")
                print(f"📊 Temps compression: {data.get('compression_time', 0):.2f}s")
                print(f"📊 Méthode: {data.get('method', 'unknown')}")
                print(f"📊 Codec: {data.get('codec', 'unknown')}")
                print(f"📊 Résolution: {data.get('original_resolution', 'unknown')} → {data.get('target_resolution', 'unknown')}")
                print(f"📊 FPS: {data.get('original_fps', 0):.1f} → {data.get('target_fps', 0):.1f}")
                
                standard_metrics = {
                    'success': True,
                    'ratio': data.get('compression_ratio', 0),
                    'space_saved': data.get('space_saved_percent', 0),
                    'compression_time': data.get('compression_time', 0),
                    'method': data.get('method', 'unknown'),
                    'request_time': request_time
                }
            else:
                print(f"❌ Erreur compression standard: {result.get('error', 'Erreur inconnue')}")
                standard_metrics = {'success': False, 'error': result.get('error')}
        else:
            print(f"❌ Erreur HTTP compression standard: {response.status_code}")
            standard_metrics = {'success': False, 'error': f'HTTP {response.status_code}'}
        
        # Test 2: Compression harmonique
        print(f"\n🎵 Test 2: Compression harmonique")
        print("-" * 40)
        
        start_time = time.time()
        
        files_harmonic = {'file': (os.path.basename(video_path), video_data, 'video/mp4')}
        data_harmonic = {'priority': 'balanced'}
        
        response_harmonic = requests.post(f"{api_url}/api/v3/harmonic-compress", 
                                      files=files_harmonic, data=data_harmonic)
        
        request_time_harmonic = time.time() - start_time
        
        if response_harmonic.status_code == 200:
            result_harmonic = response_harmonic.json()
            
            if result_harmonic.get('success'):
                print(f"✅ Compression harmonique réussie!")
                print(f"⏱️ Temps de requête: {request_time_harmonic:.2f}s")
                print(f"📊 Temps compression: {result_harmonic.get('compression_time', 0):.2f}s")
                print(f"📊 Frames compressées: {result_harmonic.get('frame_count', 0)}")
                print(f"📊 Méthode: {result_harmonic.get('method', 'unknown')}")
                print(f"📊 Version: {result_harmonic.get('version', 'unknown')}")
                print(f"📊 Constantes utilisées: {len(result_harmonic.get('harmonic_constants_used', []))}")
                
                # Métadonnées référence
                ref_metadata = result_harmonic.get('reference_metadata', {})
                print(f"\n📸 Référence:")
                print(f"  📐 Résolution: {ref_metadata.get('resolution', 'N/A')}")
                print(f"  🎨 Canaux: {ref_metadata.get('channels', 'N/A')}")
                print(f"  💡 Luminosité: {ref_metadata.get('brightness', 0):.2f}")
                print(f"  📊 Contraste: {ref_metadata.get('contrast', 0):.2f}")
                
                # Scores harmoniques
                harmonic_scores = result_harmonic.get('harmonic_scores', {})
                if harmonic_scores:
                    print(f"\n🎵 Scores harmoniques:")
                    print(f"  📊 Score harmonique: {harmonic_scores.get('reference_harmonic_score', 0):.3f}")
                    print(f"  💡 Luminosité moyenne: {harmonic_scores.get('mean_brightness', 0):.2f}")
                    print(f"  📊 Écart-type luminosité: {harmonic_scores.get('std_brightness', 0):.2f}")
                
                harmonic_metrics = {
                    'success': True,
                    'compression_time': result_harmonic.get('compression_time', 0),
                    'frame_count': result_harmonic.get('frame_count', 0),
                    'method': result_harmonic.get('method', 'unknown'),
                    'version': result_harmonic.get('version', 'unknown'),
                    'constants_count': len(result_harmonic.get('harmonic_constants_used', [])),
                    'reference_brightness': ref_metadata.get('brightness', 0),
                    'reference_contrast': ref_metadata.get('contrast', 0),
                    'harmonic_score': harmonic_scores.get('reference_harmonic_score', 0),
                    'request_time': request_time_harmonic
                }
            else:
                print(f"❌ Erreur compression harmonique: {result_harmonic.get('error', 'Erreur inconnue')}")
                harmonic_metrics = {'success': False, 'error': result_harmonic.get('error')}
        else:
            print(f"❌ Erreur HTTP compression harmonique: {response_harmonic.status_code}")
            harmonic_metrics = {'success': False, 'error': f'HTTP {response_harmonic.status_code}'}
        
        # Test 3: Démonstration complète
        print(f"\n🎭 Test 3: Démonstration complète (compression + reconstruction)")
        print("-" * 40)
        
        start_time_demo = time.time()
        
        files_demo = {'file': (os.path.basename(video_path), video_data, 'video/mp4')}
        data_demo = {'priority': 'balanced'}
        
        response_demo = requests.post(f"{api_url}/api/v3/harmonic-demo", 
                                   files=files_demo, data=data_demo)
        
        request_time_demo = time.time() - start_time_demo
        
        if response_demo.status_code == 200:
            result_demo = response_demo.json()
            
            if result_demo.get('success'):
                print(f"✅ Démonstration complète réussie!")
                print(f"⏱️ Temps total: {request_time_demo:.2f}s")
                print(f"📊 Méthode: {result_demo.get('method', 'unknown')}")
                
                # Compression
                compression = result_demo.get('compression', {})
                print(f"\n📼 Compression:")
                print(f"  ⏱️ Temps: {compression.get('time', 0):.2f}s")
                print(f"  📊 Frames: {compression.get('frames', 0)}")
                print(f"  💡 Qualité référence: {compression.get('reference_quality', 0):.2f}")
                
                # Reconstruction
                reconstruction = result_demo.get('reconstruction', {})
                print(f"\n🔄 Reconstruction:")
                print(f"  ⏱️ Temps: {reconstruction.get('time', 0):.2f}s")
                print(f"  📊 Frames: {reconstruction.get('frames', 0)}")
                print(f"  🎯 Score qualité: {reconstruction.get('quality_score', 0):.2f}")
                
                # Performance
                performance = result_demo.get('performance', {})
                print(f"\n📈 Performance:")
                print(f"  📊 Ratio compression: {performance.get('compression_ratio', 'N/A')}")
                print(f"  📈 Amélioration qualité: {performance.get('quality_improvement', 'N/A')}")
                print(f"  🎵 Enhancement harmonique: {performance.get('harmonic_enhancement', False)}")
                
                demo_metrics = {
                    'success': True,
                    'total_time': request_time_demo,
                    'compression_time': compression.get('time', 0),
                    'reconstruction_time': reconstruction.get('time', 0),
                    'compression_frames': compression.get('frames', 0),
                    'reconstruction_frames': reconstruction.get('frames', 0),
                    'quality_score': reconstruction.get('quality_score', 0),
                    'compression_ratio': performance.get('compression_ratio', 'N/A'),
                    'quality_improvement': performance.get('quality_improvement', 'N/A'),
                    'harmonic_enhancement': performance.get('harmonic_enhancement', False)
                }
            else:
                print(f"❌ Erreur démonstration: {result_demo.get('error', 'Erreur inconnue')}")
                demo_metrics = {'success': False, 'error': result_demo.get('error')}
        else:
            print(f"❌ Erreur HTTP démonstration: {response_demo.status_code}")
            demo_metrics = {'success': False, 'error': f'HTTP {response_demo.status_code}'}
        
        # Résumé comparatif
        print(f"\n📊 RÉSUMÉ COMPARATIF")
        print("="*60)
        
        print(f"📁 Fichier original: {original_size_mb:.2f} MB")
        
        if standard_metrics.get('success'):
            print(f"\n🎯 Compression Standard:")
            print(f"  ✅ Ratio: {standard_metrics['ratio']:.1f}x")
            print(f"  ⏱️ Temps: {standard_metrics['compression_time']:.2f}s")
            print(f"  📊 Espace économisé: {standard_metrics['space_saved']:.1f}%")
            print(f"  🔧 Méthode: {standard_metrics['method']}")
        
        if harmonic_metrics.get('success'):
            print(f"\n🎵 Compression Harmonique:")
            print(f"  ✅ Frames: {harmonic_metrics['frame_count']}")
            print(f"  ⏱️ Temps: {harmonic_metrics['compression_time']:.2f}s")
            print(f"  🎯 Score harmonique: {harmonic_metrics['harmonic_score']:.3f}")
            print(f"  💡 Luminosité référence: {harmonic_metrics['reference_brightness']:.2f}")
            print(f"  📊 Contraste référence: {harmonic_metrics['reference_contrast']:.2f}")
            print(f"  🔧 Méthode: {harmonic_metrics['method']}")
        
        if demo_metrics.get('success'):
            print(f"\n🎭 Démonstration Complète:")
            print(f"  ✅ Temps total: {demo_metrics['total_time']:.2f}s")
            print(f"  📊 Ratio: {demo_metrics['compression_ratio']}")
            print(f"  📈 Amélioration: {demo_metrics['quality_improvement']}")
            print(f"  🎯 Qualité: {demo_metrics['quality_score']:.2f}")
            print(f"  🎵 Enhancement: {demo_metrics['harmonic_enhancement']}")
        
        return {
            'original_size_mb': original_size_mb,
            'standard_metrics': standard_metrics,
            'harmonic_metrics': harmonic_metrics,
            'demo_metrics': demo_metrics
        }
        
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return {'error': str(e)}

def main():
    """Fonction principale"""
    
    print("🎬 Test de Compression Vidéo Réelle")
    print("="*60)
    
    # Vérifier si le serveur est actif
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code != 200:
            print("❌ Serveur HCS non disponible")
            return
        print("✅ Serveur HCS actif")
    except:
        print("❌ Impossible de se connecter au serveur HCS")
        print("📂 Veuillez démarrer le serveur: python api/harmonic_backend_simple.py")
        return
    
    # Créer une vidéo de test
    video_path = create_test_video()
    
    if not video_path:
        print("❌ Impossible de créer la vidéo de test")
        return
    
    try:
        # Lancer les tests
        results = test_video_compression(video_path)
        
        # Nettoyer
        if os.path.exists(video_path):
            os.unlink(video_path)
            print(f"\n🗑️ Fichier temporaire supprimé: {video_path}")
        
        # Conclusion
        print(f"\n🎉 TESTS TERMINÉS")
        print("="*60)
        
        if 'error' not in results:
            print("✅ Tests de compression vidéo réussis")
            
            # Recommandations
            print(f"\n📯 RECOMMANDATIONS:")
            
            if results.get('harmonic_metrics', {}).get('success'):
                print("🎵 Utiliser la compression harmonique pour:")
                print("  • Meilleure qualité préservée")
                print("  • Enhancement intelligent")
                print("  • Scores harmoniques détaillés")
            
            if results.get('demo_metrics', {}).get('success'):
                print("🎭 Utiliser la démonstration complète pour:")
                print("  • Compression + reconstruction")
                print("  • Métriques complètes")
                print("  • Validation qualité")
        else:
            print(f"❌ Erreur durant les tests: {results.get('error')}")
    
    except Exception as e:
        print(f"❌ Erreur générale: {e}")

if __name__ == "__main__":
    main()
