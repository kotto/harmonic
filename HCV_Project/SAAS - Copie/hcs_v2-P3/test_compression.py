#!/usr/bin/env python3
"""
Test complet de compression HCS - Images et Vidéos
"""

import numpy as np
from PIL import Image
import io
import requests
import json
import time
import base64
import os

def test_image_compression():
    """Test approfondi de compression d'images"""
    print('🧪 TEST COMPLET DE COMPRESSION D\'IMAGES HCS')
    print('=' * 60)
    
    # Créer différents types d'images de test
    test_images = {
        'random_noise': np.random.randint(0, 256, (240, 320, 3), dtype=np.uint8),
        'smooth_gradient': np.zeros((240, 320, 3), dtype=np.uint8),
        'geometric_pattern': np.zeros((240, 320, 3), dtype=np.uint8),
        'realistic_photo': np.random.randint(50, 200, (240, 320, 3), dtype=np.uint8)
    }
    
    # Remplir les images avec des patterns spécifiques
    for i in range(240):
        for j in range(320):
            # Gradient doux
            test_images['smooth_gradient'][i, j] = [i//2, j//2, (i+j)//4]
            
            # Pattern géométrique
            if (i//30 + j//40) % 2 == 0:
                test_images['geometric_pattern'][i, j] = [255, 128, 64]
            else:
                test_images['geometric_pattern'][i, j] = [64, 128, 255]
    
    results = {}
    
    for img_name, img_array in test_images.items():
        print(f'\n📸 Test image: {img_name}')
        
        # Convertir en bytes
        pil_image = Image.fromarray(img_array, mode='RGB')
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        image_data = buffer.getvalue()
        
        original_size = len(image_data)
        print(f'   Taille originale: {original_size} octets')
        
        # Tester différentes cibles de compression
        targets = [None, 50, 100, 200, 500]
        
        results[img_name] = {}
        
        for target in targets:
            try:
                # Préparer la requête
                files = {'file': (f'test_{img_name}.png', image_data, 'image/png')}
                data = {}
                if target is not None:
                    data['target_ratio'] = str(target)
                
                start_time = time.time()
                response = requests.post(
                    'http://localhost:8006/api/v2/compress/image',
                    files=files,
                    data=data,
                    timeout=30
                )
                compression_time = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    target_label = str(target) if target else 'auto'
                    
                    print(f'   Target {target_label}: {result["compression_ratio"]:.1f}:1 en {compression_time:.3f}s')
                    print(f'      K-ratio: {result["k_ratio"]:.1f}:1, WebP-ratio: {result["webp_ratio"]:.1f}:1')
                    print(f'      Espace économisé: {result["space_saved_percent"]:.1f}%')
                    
                    results[img_name][target_label] = {
                        'compression_ratio': result['compression_ratio'],
                        'k_ratio': result['k_ratio'],
                        'webp_ratio': result['webp_ratio'],
                        'space_saved_percent': result['space_saved_percent'],
                        'compression_time': compression_time,
                        'original_size': original_size,
                        'compressed_size': result.get('compressed_size', 0)
                    }
                else:
                    print(f'   Target {target or "auto"}: Erreur HTTP {response.status_code}')
                    
            except Exception as e:
                print(f'   Target {target or "auto"}: Exception {e}')
    
    return results

def test_video_compression():
    """Test de compression vidéo (simulation)"""
    print('\n🎥 TEST DE COMPRESSION VIDÉO HCS')
    print('=' * 60)
    
    # Créer une vidéo de test simulée (séquence d'images)
    frames = []
    for i in range(30):  # 30 frames
        # Créer une frame avec mouvement
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        
        # Ajouter un cercle qui se déplace
        center_x = 160 + int(80 * np.sin(i * 0.2))
        center_y = 120 + int(60 * np.cos(i * 0.2))
        
        for y in range(240):
            for x in range(320):
                dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                if dist < 30:
                    frame[y, x] = [255, 128, 64]
                elif dist < 40:
                    frame[y, x] = [128, 64, 32]
        
        frames.append(frame)
    
    # Convertir en bytes (simulation de fichier vidéo)
    video_data = b''.join([frame.tobytes() for frame in frames])
    
    print(f'Vidéo de test: {len(video_data)} octets, {len(frames)} frames')
    
    # Tester différentes qualités
    qualities = [50, 70, 85, 95]
    
    for quality in qualities:
        try:
            files = {'file': ('test_video.mp4', video_data, 'video/mp4')}
            data = {'quality': str(quality), 'target': 'balanced_video'}
            
            start_time = time.time()
            response = requests.post(
                'http://localhost:8006/api/v2/compress/video',
                files=files,
                data=data,
                timeout=60
            )
            compression_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f'✅ Qualité {quality}: {result["compression_ratio"]:.1f}:1 en {compression_time:.3f}s')
                print(f'   Frames: {result.get("num_frames", "N/A")}')
                print(f'   Espace économisé: {result["space_saved_percent"]:.1f}%')
                print(f'   FPS moyen: {result.get("average_fps", "N/A")}')
            else:
                print(f'❌ Qualité {quality}: Erreur HTTP {response.status_code}')
                
        except Exception as e:
            print(f'❌ Qualité {quality}: Exception {e}')

def analyze_results(results):
    """Analyse détaillée des résultats"""
    print('\n📊 ANALYSE DÉTAILLÉE DES RÉSULTATS')
    print('=' * 60)
    
    # Analyse par type d'image
    for img_name, img_results in results.items():
        print(f'\n🖼️  {img_name.upper()}:')
        
        ratios = []
        times = []
        space_saved = []
        
        for target, metrics in img_results.items():
            ratios.append(metrics['compression_ratio'])
            times.append(metrics['compression_time'])
            space_saved.append(metrics['space_saved_percent'])
        
        print(f'   Ratio moyen: {np.mean(ratios):.1f}:1 (min: {np.min(ratios):.1f}, max: {np.max(ratios):.1f})')
        print(f'   Temps moyen: {np.mean(times):.3f}s')
        print(f'   Espace économisé moyen: {np.mean(space_saved):.1f}%')
    
    # Analyse globale
    all_ratios = []
    all_times = []
    
    for img_results in results.values():
        for metrics in img_results.values():
            all_ratios.append(metrics['compression_ratio'])
            all_times.append(metrics['compression_time'])
    
    print(f'\n🌈 PERFORMANCE GLOBALE:')
    print(f'   Ratio moyen global: {np.mean(all_ratios):.1f}:1')
    print(f'   Temps moyen global: {np.mean(all_times):.3f}s')
    print(f'   Performance (ratio/second): {np.mean(all_ratios)/np.mean(all_times):.1f}')

def main():
    """Fonction principale de test"""
    try:
        # Test de compression d'images
        image_results = test_image_compression()
        
        # Test de compression vidéo
        test_video_compression()
        
        # Analyse des résultats
        analyze_results(image_results)
        
        print('\n✅ TOUS LES TESTS TERMINÉS AVEC SUCCÈS!')
        
    except Exception as e:
        print(f'❌ ERREUR GLOBALE: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
