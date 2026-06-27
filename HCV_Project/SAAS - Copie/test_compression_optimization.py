#!/usr/bin/env python3
"""
Test d'optimisation de compression pour atteindre < 11 MB
"""

import numpy as np
import cv2
from harmonic_codec_v16 import HCV16Writer
import time
import os

def test_compression_modes():
    print("🎯 TEST D'OPTIMISATION COMPRESSION")
    print("Objectif: < 11.31 MB pour la vidéo complète")
    print("=" * 50)
    
    source_video = "B3.mp4"
    test_frames = 50  # Test sur 50 frames pour extrapoler
    
    if not os.path.exists(source_video):
        print(f"❌ Fichier source non trouvé: {source_video}")
        return
    
    source_size_mb = os.path.getsize(source_video) / (1024 * 1024)
    print(f"📁 Source: {source_video} ({source_size_mb:.2f} MB)")
    print(f"🧪 Test sur {test_frames} frames")
    print()
    
    # Chargement des frames de test
    cap = cv2.VideoCapture(source_video)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"📊 Vidéo source:")
    print(f"   Résolution: {width}×{height}")
    print(f"   Frames totales: {total_frames}")
    print(f"   Durée: {total_frames/fps:.1f}s")
    print()
    
    frames = []
    for i in range(min(test_frames, total_frames)):
        ret, frame = cap.read()
        if not ret:
            break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_12bit = (frame_rgb.astype(np.uint16) << 4)
        frames.append(frame_12bit)
    
    cap.release()
    print(f"✅ {len(frames)} frames de test chargées")
    print()
    
    # Tests de différentes configurations
    configs = [
        {
            'name': 'LOSSLESS + ref_interval=30',
            'mode': 'LOSSLESS',
            'ref_interval': 30,
            'bit_depth': 12
        },
        {
            'name': 'LOSSLESS + ref_interval=60',
            'mode': 'LOSSLESS', 
            'ref_interval': 60,
            'bit_depth': 12
        },
        {
            'name': 'GRAIN_SYNTH + ref_interval=30',
            'mode': 'GRAIN_SYNTH',
            'ref_interval': 30,
            'bit_depth': 12
        },
        {
            'name': 'GRAIN_SYNTH + ref_interval=60',
            'mode': 'GRAIN_SYNTH',
            'ref_interval': 60,
            'bit_depth': 12
        },
        {
            'name': 'LOSSLESS + 10bit + ref_interval=60',
            'mode': 'LOSSLESS',
            'ref_interval': 60,
            'bit_depth': 10
        }
    ]
    
    results = []
    
    for config in configs:
        print(f"🧪 Test: {config['name']}")
        
        output_file = f"test_{config['name'].replace(' ', '_').replace('+', '').lower()}.hcv16"
        
        try:
            params = {
                'path': output_file,
                'mode': config['mode'],
                'bit_depth': config['bit_depth'],
                'width': width,
                'height': height,
                'fps': (int(fps), 1),
                'colorspace': 'BGR',
                'ref_interval': config['ref_interval'],
                'seq_id': 42
            }
            
            start_time = time.time()
            writer = HCV16Writer(**params)
            
            for i, frame in enumerate(frames):
                writer.add_frame(frame, i)
            
            file_size = writer.finalize()
            encoding_time = time.time() - start_time
            
            # Extrapolation pour la vidéo complète
            size_per_frame = file_size / len(frames)
            estimated_full_size = size_per_frame * total_frames
            estimated_full_mb = estimated_full_size / (1024 * 1024)
            
            result = {
                'config': config['name'],
                'test_size_mb': file_size / (1024 * 1024),
                'estimated_full_mb': estimated_full_mb,
                'encoding_time': encoding_time,
                'success': estimated_full_mb < source_size_mb
            }
            
            results.append(result)
            
            print(f"   Taille test: {result['test_size_mb']:.2f} MB")
            print(f"   Estimation complète: {result['estimated_full_mb']:.1f} MB")
            print(f"   Temps: {encoding_time:.1f}s")
            print(f"   Objectif atteint: {'✅' if result['success'] else '❌'}")
            
            # Nettoyage
            if os.path.exists(output_file):
                os.remove(output_file)
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            
        print()
    
    # Résumé des résultats
    print("📊 RÉSUMÉ DES RÉSULTATS")
    print("=" * 50)
    print(f"{'Configuration':<35} {'Taille estimée':<15} {'Objectif'}")
    print("-" * 65)
    
    successful_configs = []
    for result in results:
        status = "✅ OUI" if result['success'] else "❌ NON"
        print(f"{result['config']:<35} {result['estimated_full_mb']:.1f} MB{'':<8} {status}")
        if result['success']:
            successful_configs.append(result)
    
    print()
    
    if successful_configs:
        best = min(successful_configs, key=lambda x: x['estimated_full_mb'])
        print(f"🏆 MEILLEURE CONFIGURATION:")
        print(f"   {best['config']}")
        print(f"   Taille estimée: {best['estimated_full_mb']:.1f} MB")
        print(f"   Économie: {source_size_mb - best['estimated_full_mb']:.1f} MB")
        print(f"   Ratio: {source_size_mb / best['estimated_full_mb']:.2f}x")
        
        return best['config']
    else:
        print("❌ Aucune configuration n'atteint l'objectif < 11.31 MB")
        print("💡 Suggestions:")
        print("   - Réduire la résolution (downscale)")
        print("   - Utiliser un mode avec perte")
        print("   - Augmenter ref_interval à 120+")
        
        return None

if __name__ == "__main__":
    best_config = test_compression_modes()
    if best_config:
        print(f"\n🎯 Utilisez la configuration: {best_config}")
        print("   Pour encoder la vidéo complète avec ces paramètres optimaux.")