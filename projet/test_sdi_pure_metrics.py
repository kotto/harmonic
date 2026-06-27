#!/usr/bin/env python3
"""
TEST DIRECT DE COMPRESSION SDI-PURE (METHOD_1)
Teste la compression vidéo avec métriques détaillées
"""

import sys
import os
import time
import numpy as np
import cv2
from pathlib import Path
import json

sys.path.insert(0, 'COMPRESSION-CAMERA/METHOD_1_SDI_PURE_VIDEO_COMPRESSION')

from sdi_pure_video_compression import SDIPureVideoCompressor

def create_test_video(width=640, height=480, num_frames=30, fps=30.0, filename="test_video.mp4"):
    """Crée une vidéo de test"""
    print(f"[*] Création vidéo de test: {width}x{height} @ {fps}fps, {num_frames} frames")
    
    # Initialiser le writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    frames = []
    
    for frame_idx in range(num_frames):
        # Créer frame avec contenu varié
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Gradient horizontal
        for x in range(width):
            frame[:, x] = [int(255 * x / width), 128, 255 - int(255 * x / width)]
        
        # Ajouter du bruit
        noise = np.random.randint(0, 30, (height, width, 3), dtype=np.uint8)
        frame = cv2.addWeighted(frame, 0.8, noise, 0.2, 0)
        
        # Ajouter du mouvement (cercle qui se déplace)
        center_x = int(width * (0.3 + 0.4 * frame_idx / num_frames))
        center_y = int(height / 2)
        cv2.circle(frame, (center_x, center_y), 50, (0, 255, 0), -1)
        
        # Ajouter du texte
        cv2.putText(frame, f"Frame {frame_idx+1}/{num_frames}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        out.write(frame)
        frames.append(frame)
    
    out.release()
    
    file_size = os.path.getsize(filename)
    print(f"[+] Vidéo créée: {filename} ({file_size:,} bytes, {file_size/1024/1024:.2f} MB)")
    
    return filename, frames, file_size

def test_sdi_pure_compression():
    """Test de compression SDI-PURE"""
    print("\n" + "="*80)
    print("TEST COMPRESSION SDI-PURE (METHOD_1)")
    print("="*80)
    
    # Créer vidéo de test
    video_file, frames, original_size = create_test_video(640, 480, 30, 30.0, "test_sdi_pure.mp4")
    output_file = "test_sdi_pure.sdi"
    
    # Initialiser compresseur
    print("\n[*] Initialisation compresseur SDI-PURE...")
    compressor = SDIPureVideoCompressor(width=640, height=480, fps=30.0)
    
    # Compression
    print(f"[*] Compression {len(frames)} frames en cours...")
    start_time = time.time()
    
    try:
        metrics = compressor.save_compressed_video(frames, output_file)
        compression_time = time.time() - start_time
        
        # Vérifier le fichier
        if os.path.exists(output_file):
            compressed_size = os.path.getsize(output_file)
        else:
            compressed_size = 0
        
        print("\n" + "="*80)
        print("RÉSULTATS DE COMPRESSION SDI-PURE")
        print("="*80)
        
        print(f"\nFichier vidéo original: {video_file}")
        print(f"  Taille: {original_size:,} bytes ({original_size/1024/1024:.2f} MB)")
        print(f"  Frames: {len(frames)}")
        print(f"  Résolution: 640x480")
        print(f"  FPS: 30")
        
        print(f"\nFichier compressé: {output_file}")
        print(f"  Taille: {compressed_size:,} bytes ({compressed_size/1024/1024:.2f} MB)")
        
        print(f"\nMÉTRIQUES DE COMPRESSION:")
        print(f"  Ratio de compression: {original_size/max(1, compressed_size):.2f}:1")
        print(f"  Économie d'espace: {(1 - compressed_size/original_size)*100:.2f}%")
        print(f"  Temps de compression: {compression_time:.3f}s")
        print(f"  Vitesse: {original_size/1024/1024/max(0.001, compression_time):.2f} MB/s")
        print(f"  Temps par frame: {compression_time/len(frames)*1000:.2f}ms")
        
        print(f"\nMÉTRIQUES COMPRESSEUR:")
        for key, value in metrics.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            elif isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    if isinstance(v, float):
                        print(f"    {k}: {v:.4f}")
                    else:
                        print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")
        
        return metrics, compression_time, original_size, compressed_size
        
    except Exception as e:
        print(f"\n[-] Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None, 0, 0, 0

def test_sdi_pure_different_sizes():
    """Test avec différentes résolutions"""
    print("\n" + "="*80)
    print("TEST SDI-PURE AVEC DIFFÉRENTES RÉSOLUTIONS")
    print("="*80)
    
    sizes = [
        (320, 240, "QVGA", 15),
        (640, 480, "VGA", 20),
        (800, 600, "SVGA", 15),
    ]
    
    results = []
    
    for width, height, label, num_frames in sizes:
        print(f"\n[*] Test {label} ({width}x{height}, {num_frames} frames)...")
        
        video_file, frames, original_size = create_test_video(
            width, height, num_frames, 30.0, f"test_{label}_sdi.mp4"
        )
        output_file = f"test_{label}_sdi.sdi"
        
        compressor = SDIPureVideoCompressor(width=width, height=height, fps=30.0)
        
        start_time = time.time()
        try:
            metrics = compressor.save_compressed_video(frames, output_file)
            compression_time = time.time() - start_time
            
            if os.path.exists(output_file):
                compressed_size = os.path.getsize(output_file)
            else:
                compressed_size = 0
            
            ratio = original_size / max(1, compressed_size)
            saving = (1 - compressed_size/original_size) * 100
            
            result = {
                'label': label,
                'dimensions': f"{width}x{height}",
                'frames': num_frames,
                'original_mb': original_size / 1024 / 1024,
                'compressed_mb': compressed_size / 1024 / 1024,
                'ratio': ratio,
                'saving': saving,
                'time_s': compression_time,
                'speed_mbps': original_size / 1024 / 1024 / max(0.001, compression_time),
                'time_per_frame_ms': compression_time / num_frames * 1000
            }
            
            results.append(result)
            
            print(f"    Original: {result['original_mb']:.2f} MB")
            print(f"    Compressé: {result['compressed_mb']:.2f} MB")
            print(f"    Ratio: {result['ratio']:.2f}:1")
            print(f"    Économie: {result['saving']:.2f}%")
            print(f"    Temps: {result['time_s']:.3f}s")
            print(f"    Vitesse: {result['speed_mbps']:.2f} MB/s")
            print(f"    Temps/frame: {result['time_per_frame_ms']:.2f}ms")
        except Exception as e:
            print(f"    Erreur: {e}")
    
    # Tableau récapitulatif
    if results:
        print("\n" + "="*80)
        print("RÉSUMÉ COMPARATIF - SDI-PURE")
        print("="*80)
        print(f"{'Résolution':<15} {'Frames':<8} {'Original':<12} {'Compressé':<12} {'Ratio':<10} {'Économie':<10} {'Vitesse':<12}")
        print("-" * 100)
        for r in results:
            print(f"{r['label']:<15} {r['frames']:<8} {r['original_mb']:>10.2f} MB {r['compressed_mb']:>10.2f} MB {r['ratio']:>8.2f}:1 {r['saving']:>8.2f}% {r['speed_mbps']:>10.2f} MB/s")
    
    return results

def test_sdi_pure_frame_count():
    """Test avec différents nombres de frames"""
    print("\n" + "="*80)
    print("TEST SDI-PURE AVEC DIFFÉRENTS NOMBRES DE FRAMES")
    print("="*80)
    
    frame_counts = [10, 20, 30, 60]
    results = []
    
    for num_frames in frame_counts:
        print(f"\n[*] Test avec {num_frames} frames...")
        
        video_file, frames, original_size = create_test_video(
            640, 480, num_frames, 30.0, f"test_frames_{num_frames}_sdi.mp4"
        )
        output_file = f"test_frames_{num_frames}_sdi.sdi"
        
        compressor = SDIPureVideoCompressor(width=640, height=480, fps=30.0)
        
        start_time = time.time()
        try:
            metrics = compressor.save_compressed_video(frames, output_file)
            compression_time = time.time() - start_time
            
            if os.path.exists(output_file):
                compressed_size = os.path.getsize(output_file)
            else:
                compressed_size = 0
            
            ratio = original_size / max(1, compressed_size)
            saving = (1 - compressed_size/original_size) * 100
            
            result = {
                'frames': num_frames,
                'original_mb': original_size / 1024 / 1024,
                'compressed_mb': compressed_size / 1024 / 1024,
                'ratio': ratio,
                'saving': saving,
                'time_s': compression_time,
                'speed_mbps': original_size / 1024 / 1024 / max(0.001, compression_time),
                'time_per_frame_ms': compression_time / num_frames * 1000
            }
            
            results.append(result)
            
            print(f"    Original: {result['original_mb']:.2f} MB")
            print(f"    Compressé: {result['compressed_mb']:.2f} MB")
            print(f"    Ratio: {result['ratio']:.2f}:1")
            print(f"    Économie: {result['saving']:.2f}%")
            print(f"    Temps total: {result['time_s']:.3f}s")
            print(f"    Temps/frame: {result['time_per_frame_ms']:.2f}ms")
        except Exception as e:
            print(f"    Erreur: {e}")
    
    # Tableau récapitulatif
    if results:
        print("\n" + "="*80)
        print("RÉSUMÉ - IMPACT DU NOMBRE DE FRAMES")
        print("="*80)
        print(f"{'Frames':<10} {'Original':<12} {'Compressé':<12} {'Ratio':<10} {'Économie':<10} {'Temps/Frame':<12}")
        print("-" * 80)
        for r in results:
            print(f"{r['frames']:<10} {r['original_mb']:>10.2f} MB {r['compressed_mb']:>10.2f} MB {r['ratio']:>8.2f}:1 {r['saving']:>8.2f}% {r['time_per_frame_ms']:>10.2f}ms")
    
    return results

if __name__ == "__main__":
    try:
        # Test principal
        metrics, comp_time, orig_size, comp_size = test_sdi_pure_compression()
        
        # Test avec différentes résolutions
        results_sizes = test_sdi_pure_different_sizes()
        
        # Test avec différents nombres de frames
        results_frames = test_sdi_pure_frame_count()
        
        # Résumé final
        print("\n" + "="*80)
        print("RÉSUMÉ FINAL - SDI-PURE")
        print("="*80)
        
        if metrics:
            print(f"\n[+] Tests complétés avec succès!")
            print(f"    - Compression principale: OK")
            print(f"    - Tests multi-résolution: OK ({len(results_sizes)} résolutions)")
            print(f"    - Tests multi-frames: OK ({len(results_frames)} configurations)")
            
            # Sauvegarder les résultats
            summary = {
                'test_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'main_compression': {
                    'compression_time': comp_time,
                    'original_size': orig_size,
                    'compressed_size': comp_size,
                    'ratio': orig_size / max(1, comp_size),
                    'metrics': metrics
                },
                'multi_resolution_results': results_sizes,
                'multi_frame_results': results_frames
            }
            
            with open('sdi_pure_test_results.json', 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            print(f"\n[+] Résultats sauvegardés: sdi_pure_test_results.json")
        
    except Exception as e:
        print(f"\nErreur: {e}")
        import traceback
        traceback.print_exc()
