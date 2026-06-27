#!/usr/bin/env python3
"""
Test simple de l'algorithme SDI-PURE
"""

import sys
import os
import numpy as np
import time
import struct
import zlib

def compress_frame_simple(frame_data):
    """Compression simple d'une frame"""
    # Différences horizontales
    diff_h = np.diff(frame_data, axis=1)
    
    # Différences verticales
    diff_v = np.diff(frame_data, axis=0)
    
    # Sérialisation
    data = frame_data[0, 0].tobytes()  # Pixel de référence
    data += diff_h.astype(np.int16).tobytes()
    data += diff_v.astype(np.int16).tobytes()
    
    # Compression zlib
    compressed = zlib.compress(data, level=9)
    
    return compressed

def test_compression():
    """Test de compression"""
    
    print("=" * 70)
    print("TEST: COMPRESSION SIMPLE AVEC DIFFÉRENCES + ZLIB")
    print("=" * 70)
    print()
    
    # Paramètres
    width, height = 1920, 1080
    num_frames = 5
    
    print(f"Paramètres:")
    print(f"  Résolution: {width}x{height}")
    print(f"  Nombre de frames: {num_frames}")
    print()
    
    # Créer des frames de test (RGB 8-bit)
    print("Création des frames de test...")
    frames = []
    for i in range(num_frames):
        frame = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        frames.append(frame)
    
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
        compressed = compress_frame_simple(frame)
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
    
    # Résultat
    print("=" * 70)
    if ratio > 1:
        print(f"✓ SUCCÈS: Compression effective (ratio {ratio:.2f}:1)")
    else:
        print(f"✗ ÉCHEC: Expansion au lieu de compression (ratio {ratio:.2f}:1)")
    print("=" * 70)

if __name__ == '__main__':
    test_compression()
