#!/usr/bin/env python3
"""
Test de compression en pur Python (sans numpy)
"""

import time
import zlib
import random

def compress_frame_pure_python(frame_data):
    """Compression simple d'une frame en pur Python"""
    # Calculer les différences
    height = len(frame_data)
    width = len(frame_data[0]) if height > 0 else 0
    channels = len(frame_data[0][0]) if width > 0 else 0
    
    # Sérialiser les données
    data = bytearray()
    
    # Pixel de référence
    for c in range(channels):
        data.append(frame_data[0][0][c])
    
    # Différences horizontales
    for y in range(height):
        for x in range(1, width):
            for c in range(channels):
                diff = frame_data[y][x][c] - frame_data[y][x-1][c]
                data.append(diff & 0xFF)
    
    # Différences verticales
    for y in range(1, height):
        for x in range(width):
            for c in range(channels):
                diff = frame_data[y][x][c] - frame_data[y-1][x][c]
                data.append(diff & 0xFF)
    
    # Compression zlib
    compressed = zlib.compress(bytes(data), level=9)
    
    return compressed

def create_test_frame(width, height, channels=3):
    """Crée une frame de test"""
    frame = []
    for y in range(height):
        row = []
        for x in range(width):
            pixel = tuple(random.randint(0, 255) for _ in range(channels))
            row.append(pixel)
        frame.append(row)
    return frame

def test_compression():
    """Test de compression"""
    
    print("=" * 70)
    print("TEST: COMPRESSION EN PUR PYTHON")
    print("=" * 70)
    print()
    
    # Paramètres
    width, height = 640, 480  # Résolution réduite pour test rapide
    num_frames = 3
    channels = 3
    
    print(f"Paramètres:")
    print(f"  Résolution: {width}x{height}")
    print(f"  Canaux: {channels}")
    print(f"  Nombre de frames: {num_frames}")
    print()
    
    # Créer des frames de test
    print("Création des frames de test...")
    frames = []
    for i in range(num_frames):
        frame = create_test_frame(width, height, channels)
        frames.append(frame)
    
    print(f"  {num_frames} frames créées")
    print()
    
    # Calculer la taille originale
    original_size = width * height * channels * num_frames
    
    print(f"Taille originale:")
    print(f"  Total: {original_size / (1024*1024):.2f} MB")
    print(f"  Par frame: {original_size / num_frames / (1024*1024):.2f} MB")
    print()
    
    # Compresser les frames
    print("Compression en cours...")
    start_time = time.time()
    
    compressed_frames = []
    for i, frame in enumerate(frames):
        print(f"  Frame {i+1}/{num_frames}...", end='', flush=True)
        compressed = compress_frame_pure_python(frame)
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
