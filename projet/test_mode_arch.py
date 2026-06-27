#!/usr/bin/env python3
"""
Test du mode ARCH (haute compression) pour atteindre < 11 MB
"""

import numpy as np
import cv2
from harmonic_codec_v16 import HCV16Writer
import time
import os

def test_arch_mode():
    print("🏛️ TEST MODE ARCH (HAUTE COMPRESSION)")
    print("=" * 45)
    
    source_video = "B3.mp4"
    test_frames = 30  # Test sur 30 frames pour estimation
    
    if not os.path.exists(source_video):
        print(f"❌ Fichier source non trouvé: {source_video}")
        return
    
    source_size_mb = os.path.getsize(source_video) / (1024 * 1024)
    print(f"📁 Source: {source_video} ({source_size_mb:.2f} MB)")
    print(f"🎯 Objectif: < {source_size_mb:.2f} MB")
    print()
    
    # Chargement des frames de test
    cap = cv2.VideoCapture(source_video)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"📊 Vidéo source:")
    print(f"   Résolution: {width}×{height} ({'Vertical' if height > width else 'Horizontal'})")
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
    
    # Configurations ARCH à tester
    arch_configs = [
        {
            'name': 'ARCH Mode 1 (GRAIN_SYNTH + ref_interval=120)',
            'mode': 'GRAIN_SYNTH',  # Utilise zstd-19
            'ref_interval': 120,
            'bit_depth': 12
        },
        {
            'name': 'ARCH Mode 2 (SIGNAL_ONLY + ref_interval=120)', 
            'mode': 'SIGNAL_ONLY',  # Utilise zstd-19 + séparation signal
            'ref_interval': 120,
            'bit_depth': 12
        },
        {
            'name': 'ARCH Mode 3 (GRAIN_SYNTH + ref_interval=240)',
            'mode': 'GRAIN_SYNTH',
            'ref_interval': 240,
            'bit_depth': 10  # Réduction bit depth
        },
        {
            'name': 'ARCH Mode 4 (SIGNAL_ONLY + ref_interval=240)',
            'mode': 'SIGNAL_ONLY',
            'ref_interval': 240,
            'bit_depth': 10
        }
    ]
    
    results = []
    
    for config in arch_configs:
        print(f"🧪 Test: {config['name']}")
        
        output_file = f"test_arch_{len(results)+1}.hcv16"
        
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
                'frames_for_model': frames[:5] if config['mode'] == 'GRAIN_SYNTH' else None,  # Pour sigma_curve
                'seq_id': 42
            }
            
            start_time = time.time()
            writer = HCV16Writer(**params)
            
            for i, frame in enumerate(frames):
                writer.add_frame(frame, i)
                if (i + 1) % 10 == 0:
                    print(f"   Frame {i+1}/{len(frames)} encodée...")
            
            file_size = writer.finalize()
            encoding_time = time.time() - start_time
            
            # Extrapolation pour la vidéo complète
            size_per_frame = file_size / len(frames)
            
            # Estimation plus précise basée sur la répartition I/P frames
            i_frames_in_test = (len(frames) // config['ref_interval']) + 1
            p_frames_in_test = len(frames) - i_frames_in_test
            
            if i_frames_in_test > 0 and p_frames_in_test > 0:
                # Estimation des tailles I vs P
                avg_i_size = file_size * 0.7 / i_frames_in_test  # 70% pour I-frames
                avg_p_size = file_size * 0.3 / p_frames_in_test  # 30% pour P-frames
                
                # Extrapolation complète
                total_i_frames = (total_frames // config['ref_interval']) + 1
                total_p_frames = total_frames - total_i_frames
                
                estimated_full_size = (total_i_frames * avg_i_size) + (total_p_frames * avg_p_size)
            else:
                estimated_full_size = size_per_frame * total_frames
            
            estimated_full_mb = estimated_full_size / (1024 * 1024)
            
            result = {
                'config': config['name'],
                'mode': config['mode'],
                'ref_interval': config['ref_interval'],
                'bit_depth': config['bit_depth'],
                'test_size_mb': file_size / (1024 * 1024),
                'estimated_full_mb': estimated_full_mb,
                'encoding_time': encoding_time,
                'fps_encoding': len(frames) / encoding_time,
                'success': estimated_full_mb < source_size_mb
            }
            
            results.append(result)
            
            print(f"   Taille test: {result['test_size_mb']:.2f} MB")
            print(f"   Estimation complète: {result['estimated_full_mb']:.1f} MB")
            print(f"   Vitesse: {result['fps_encoding']:.1f} fps")
            print(f"   Objectif atteint: {'✅' if result['success'] else '❌'}")
            
            # Nettoyage
            if os.path.exists(output_file):
                os.remove(output_file)
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            
        print()
    
    # Résumé des résultats
    print("📊 RÉSUMÉ MODES ARCH")
    print("=" * 50)
    print(f"{'Configuration':<45} {'Taille':<12} {'Objectif'}")
    print("-" * 70)
    
    successful_configs = []
    for result in results:
        status = "✅ OUI" if result['success'] else "❌ NON"
        print(f"{result['config']:<45} {result['estimated_full_mb']:.1f} MB{'':<5} {status}")
        if result['success']:
            successful_configs.append(result)
    
    print()
    
    if successful_configs:
        best = min(successful_configs, key=lambda x: x['estimated_full_mb'])
        print(f"🏆 MEILLEUR MODE ARCH:")
        print(f"   Configuration: {best['config']}")
        print(f"   Mode: {best['mode']}")
        print(f"   Ref interval: {best['ref_interval']}")
        print(f"   Bit depth: {best['bit_depth']}")
        print(f"   Taille estimée: {best['estimated_full_mb']:.1f} MB")
        print(f"   Économie: {source_size_mb - best['estimated_full_mb']:.1f} MB")
        print(f"   Vitesse encodage: {best['fps_encoding']:.1f} fps")
        
        return best
    else:
        print("❌ Aucun mode ARCH n'atteint l'objectif < 11.31 MB")
        
        # Affichage du meilleur résultat même s'il n'atteint pas l'objectif
        if results:
            best_attempt = min(results, key=lambda x: x['estimated_full_mb'])
            print()
            print(f"💡 MEILLEURE TENTATIVE:")
            print(f"   {best_attempt['config']}")
            print(f"   Taille: {best_attempt['estimated_full_mb']:.1f} MB")
            print(f"   Réduction: {((source_size_mb - best_attempt['estimated_full_mb']) / source_size_mb * 100):.1f}%")
        
        return None

if __name__ == "__main__":
    result = test_arch_mode()
    if result:
        print(f"\n🎯 MODE ARCH OPTIMAL TROUVÉ !")
        print(f"   Utilisez: mode='{result['mode']}', ref_interval={result['ref_interval']}, bit_depth={result['bit_depth']}")
    else:
        print(f"\n⚠️  Objectif < 11 MB très difficile à atteindre avec HCV16 lossless")
        print(f"   HCV16 est optimisé pour la qualité, pas la compression maximale")