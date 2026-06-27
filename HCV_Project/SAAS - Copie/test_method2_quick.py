#!/usr/bin/env python3
"""
TEST RAPIDE DE COMPRESSION METHOD_2
Version simplifiée pour tester les performances
"""

import sys
import os
import time
import numpy as np
import cv2
from pathlib import Path

sys.path.insert(0, 'COMPRESSION-CAMERA/METHOD_2_SDI_LIKE_IMAGE_COMPRESSION')

from sdi_pure_image_compression import SDIPureImageCompressor

def create_small_test_image(width=640, height=480, filename="test_small.jpg"):
    """Crée une petite image de test"""
    print(f"[*] Création image: {width}x{height}")
    
    # Image simple avec gradient
    image = np.zeros((height, width, 3), dtype=np.uint8)
    for x in range(width):
        image[:, x] = [int(255 * x / width), 128, 255 - int(255 * x / width)]
    
    cv2.imwrite(filename, image)
    file_size = os.path.getsize(filename)
    print(f"[+] Image créée: {filename} ({file_size:,} bytes)")
    return filename, file_size

def test_compression_quick():
    """Test rapide de compression"""
    print("\n" + "="*80)
    print("TEST RAPIDE DE COMPRESSION METHOD_2")
    print("="*80)
    
    # Créer image petite
    test_image, original_size = create_small_test_image(640, 480, "test_quick.jpg")
    output_file = "test_quick.sdi-img"
    
    # Initialiser compresseur
    print("\n[*] Initialisation compresseur...")
    compressor = SDIPureImageCompressor()
    
    # Compression
    print("[*] Compression en cours...")
    start_time = time.time()
    
    try:
        metrics = compressor.save_compressed_image(test_image, output_file)
        compression_time = time.time() - start_time
        
        # Vérifier le fichier
        if os.path.exists(output_file):
            compressed_size = os.path.getsize(output_file)
        else:
            compressed_size = 0
        
        print("\n" + "="*80)
        print("RÉSULTATS DE COMPRESSION")
        print("="*80)
        print(f"\nFichier original: {test_image}")
        print(f"  Taille: {original_size:,} bytes ({original_size/1024:.2f} KB)")
        
        print(f"\nFichier compressé: {output_file}")
        print(f"  Taille: {compressed_size:,} bytes ({compressed_size/1024:.2f} KB)")
        
        print(f"\nMÉTRIQUES:")
        print(f"  Ratio de compression: {original_size/max(1, compressed_size):.2f}:1")
        print(f"  Économie d'espace: {(1 - compressed_size/original_size)*100:.2f}%")
        print(f"  Temps de compression: {compression_time:.3f}s")
        print(f"  Vitesse: {original_size/1024/max(0.001, compression_time):.2f} KB/s")
        
        print(f"\nMÉTRIQUES COMPRESSEUR:")
        for key, value in metrics.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            else:
                print(f"  {key}: {value}")
        
        return metrics
        
    except Exception as e:
        print(f"\n[-] Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_compression_sizes():
    """Test avec plusieurs tailles"""
    print("\n" + "="*80)
    print("TEST AVEC DIFFÉRENTES TAILLES")
    print("="*80)
    
    sizes = [
        (320, 240, "QVGA"),
        (640, 480, "VGA"),
        (800, 600, "SVGA"),
    ]
    
    results = []
    
    for width, height, label in sizes:
        print(f"\n[*] Test {label} ({width}x{height})...")
        
        test_image, original_size = create_small_test_image(width, height, f"test_{label}.jpg")
        output_file = f"test_{label}.sdi-img"
        
        compressor = SDIPureImageCompressor()
        
        start_time = time.time()
        try:
            metrics = compressor.save_compressed_image(test_image, output_file)
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
                'original_kb': original_size / 1024,
                'compressed_kb': compressed_size / 1024,
                'ratio': ratio,
                'saving': saving,
                'time_ms': compression_time * 1000,
                'speed_kbps': original_size / 1024 / max(0.001, compression_time)
            }
            
            results.append(result)
            
            print(f"    Original: {result['original_kb']:.2f} KB")
            print(f"    Compressé: {result['compressed_kb']:.2f} KB")
            print(f"    Ratio: {result['ratio']:.2f}:1")
            print(f"    Économie: {result['saving']:.2f}%")
            print(f"    Temps: {result['time_ms']:.1f}ms")
            print(f"    Vitesse: {result['speed_kbps']:.2f} KB/s")
        except Exception as e:
            print(f"    Erreur: {e}")
    
    # Tableau récapitulatif
    if results:
        print("\n" + "="*80)
        print("RÉSUMÉ COMPARATIF")
        print("="*80)
        print(f"{'Résolution':<15} {'Original':<12} {'Compressé':<12} {'Ratio':<10} {'Économie':<10} {'Temps':<10}")
        print("-" * 80)
        for r in results:
            print(f"{r['label']:<15} {r['original_kb']:>10.2f} KB {r['compressed_kb']:>10.2f} KB {r['ratio']:>8.2f}:1 {r['saving']:>8.2f}% {r['time_ms']:>8.1f}ms")
    
    return results

if __name__ == "__main__":
    try:
        # Test rapide
        metrics = test_compression_quick()
        
        # Test avec différentes tailles
        results = test_compression_sizes()
        
        print("\n" + "="*80)
        print("TESTS COMPLÉTÉS")
        print("="*80)
        
    except Exception as e:
        print(f"\nErreur: {e}")
        import traceback
        traceback.print_exc()
