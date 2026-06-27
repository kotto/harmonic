#!/usr/bin/env python3
"""
Test direct de l'algorithme SDI-PURE avec signal YUV422 10-bit
"""

import sys
import os
import numpy as np
import cv2
import time

# Ajouter le chemin de METHOD_1
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'COMPRESSION-CAMERA', 'METHOD_1_SDI_PURE_VIDEO_COMPRESSION'))

from sdi_pure_video_compression import SDIPureVideoCompressor

def create_test_yuv422_10bit_frame(width=1920, height=1080):
    """Crée un frame YUV422 10-bit de test"""
    # Créer une image RGB de test
    image = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    
    # Convertir en YUV
    yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
    
    # Convertir en 10-bit
    yuv_10bit = yuv.astype(np.uint16) << 2
    
    return image, yuv_10bit

def test_sdi_pure_compression():
    """Test de compression SDI-PURE"""
    
    print("=" * 70)
    print("TEST DIRECT: ALGORITHME SDI-PURE AVEC YUV422 10-BIT")
    print("=" * 70)
    print()
    
    # Paramètres
    width, height = 1920, 1080
    fps = 30
    num_frames = 5
    
    print(f"Paramètres:")
    print(f"  Résolution: {width}x{height}")
    print(f"  Format: YUV422 10-bit")
    print(f"  Nombre de frames: {num_frames}")
    print()
    
    # Créer le compresseur
    compressor = SDIPureVideoCompressor(width, height, fps, bit_depth=10)
    
    # Créer des frames de test
    print("Création des frames de test...")
    frames = []
    for i in range(num_frames):
        image, yuv_10bit = create_test_yuv422_10bit_frame(width, height)
        frames.append(image)
    
    print(f"  {num_frames} frames créées")
    print()
    
    # Calculer la taille originale
    original_size = 0
    for frame in frames:
        original_size += frame.nbytes
    
    print(f"Taille originale (RGB 8-bit):")
    print(f"  Total: {original_size / (1024*1024):.2f} MB")
    print(f"  Par frame: {original_size / num_frames / (1024*1024):.2f} MB")
    print()
    
    # Compresser les frames
    print("Compression en cours...")
    start_time = time.time()
    
    compressed_frames = []
    for i, frame in enumerate(frames):
        print(f"  Frame {i+1}/{num_frames}...", end='', flush=True)
        compressed = compressor.compress_frame(frame)
        compressed_frames.append(compressed)
        print(f" OK ({len(compressed)} bytes)")
    
    compression_time = time.time() - start_time
    
    print()
    
    # Calculer la taille compressée
    compressed_size = sum(len(f) for f in compressed_frames)
    
    print(f"Taille compressée:")
    print(f"  Total: {compressed_size / (1024*1024):.2f} MB")
    print(f"  Par frame: {compressed_size / num_frames / (1024*1024):.2f} MB")
    print()
    
    # Métriques
    print("=" * 70)
    print("MÉTRIQUES DE COMPRESSION")
    print("=" * 70)
    
    ratio = original_size / max(1, compressed_size)
    space_saving = ((original_size - compressed_size) / original_size) * 100
    avg_time = compression_time / num_frames
    
    print(f"Ratio de compression: {ratio:.2f}:1")
    print(f"Économie d'espace: {space_saving:.1f}%")
    print(f"Temps total: {compression_time:.2f}s")
    print(f"Temps par frame: {avg_time:.2f}s")
    print(f"Taille originale: {original_size / (1024*1024):.2f} MB")
    print(f"Taille compressée: {compressed_size / (1024*1024):.2f} MB")
    print(f"Espace sauvé: {(original_size - compressed_size) / (1024*1024):.2f} MB")
    print()
    
    # Vérifier les métriques du compresseur
    print("Métriques du compresseur:")
    metrics = compressor.get_metrics()
    print(f"  Images traitées: {metrics['images_processed']}")
    print(f"  Ratio (compresseur): {metrics.get('compression_ratio', 0):.2f}:1")
    print(f"  Économie (compresseur): {metrics.get('space_saving', 0):.1f}%")
    print()
    
    # Résultat
    print("=" * 70)
    if ratio > 1:
        print(f"✓ SUCCÈS: Compression effective (ratio {ratio:.2f}:1)")
    else:
        print(f"✗ ÉCHEC: Expansion au lieu de compression (ratio {ratio:.2f}:1)")
    print("=" * 70)

if __name__ == '__main__':
    test_sdi_pure_compression()
