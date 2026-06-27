#!/usr/bin/env python3
"""
TEST COMPRESSION METHOD_2 AVEC IMAGES RAW
Teste avec des données non-compressées pour voir la vraie performance
"""

import sys
import os
import time
import numpy as np
import cv2
import struct

sys.path.insert(0, 'COMPRESSION-CAMERA/METHOD_2_SDI_LIKE_IMAGE_COMPRESSION')

from sdi_pure_image_compression import SDIPureImageCompressor

def create_raw_image(width=640, height=480, filename="test_raw.raw"):
    """Crée une image RAW non-compressée"""
    print(f"[*] Création image RAW: {width}x{height}")
    
    # Créer image avec contenu varié
    image = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Gradient horizontal
    for x in range(width):
        image[:, x] = [int(255 * x / width), 128, 255 - int(255 * x / width)]
    
    # Ajouter du bruit
    noise = np.random.randint(0, 50, (height, width, 3), dtype=np.uint8)
    image = cv2.addWeighted(image, 0.8, noise, 0.2, 0)
    
    # Sauvegarder en RAW (pas de compression)
    with open(filename, 'wb') as f:
        f.write(image.tobytes())
    
    file_size = os.path.getsize(filename)
    print(f"[+] Image RAW créée: {filename} ({file_size:,} bytes)")
    return filename, file_size

def convert_raw_to_jpg(raw_file, width, height, jpg_file):
    """Convertit RAW en JPG pour traitement"""
    with open(raw_file, 'rb') as f:
        data = f.read()
    
    image = np.frombuffer(data, dtype=np.uint8).reshape((height, width, 3))
    cv2.imwrite(jpg_file, image)
    return jpg_file

def test_raw_compression():
    """Test de compression sur images RAW"""
    print("\n" + "="*80)
    print("TEST COMPRESSION METHOD_2 - IMAGES RAW")
    print("="*80)
    
    sizes = [
        (320, 240, "QVGA"),
        (640, 480, "VGA"),
        (800, 600, "SVGA"),
        (1024, 768, "XGA"),
    ]
    
    results = []
    
    for width, height, label in sizes:
        print(f"\n[*] Test {label} ({width}x{height})...")
        
        # Créer image RAW
        raw_file, raw_size = create_raw_image(width, height, f"test_{label}_raw.raw")
        
        # Convertir en JPG pour traitement
        jpg_file = f"test_{label}_raw.jpg"
        convert_raw_to_jpg(raw_file, width, height, jpg_file)
        jpg_size = os.path.getsize(jpg_file)
        
        # Compresser
        output_file = f"test_{label}_raw.sdi-img"
        compressor = SDIPureImageCompressor()
        
        start_time = time.time()
        try:
            metrics = compressor.save_compressed_image(jpg_file, output_file)
            compression_time = time.time() - start_time
            
            if os.path.exists(output_file):
                compressed_size = os.path.getsize(output_file)
            else:
                compressed_size = 0
            
            # Calculer ratios
            ratio_raw = raw_size / max(1, compressed_size)
            ratio_jpg = jpg_size / max(1, compressed_size)
            saving_raw = (1 - compressed_size/raw_size) * 100
            saving_jpg = (1 - compressed_size/jpg_size) * 100
            
            result = {
                'label': label,
                'dimensions': f"{width}x{height}",
                'raw_kb': raw_size / 1024,
                'jpg_kb': jpg_size / 1024,
                'compressed_kb': compressed_size / 1024,
                'ratio_raw': ratio_raw,
                'ratio_jpg': ratio_jpg,
                'saving_raw': saving_raw,
                'saving_jpg': saving_jpg,
                'time_ms': compression_time * 1000,
                'speed_kbps': raw_size / 1024 / max(0.001, compression_time)
            }
            
            results.append(result)
            
            print(f"    RAW: {result['raw_kb']:.2f} KB")
            print(f"    JPG: {result['jpg_kb']:.2f} KB")
            print(f"    Compressé: {result['compressed_kb']:.2f} KB")
            print(f"    Ratio (RAW→Compressé): {result['ratio_raw']:.2f}:1")
            print(f"    Ratio (JPG→Compressé): {result['ratio_jpg']:.2f}:1")
            print(f"    Économie (vs RAW): {result['saving_raw']:.2f}%")
            print(f"    Économie (vs JPG): {result['saving_jpg']:.2f}%")
            print(f"    Temps: {result['time_ms']:.1f}ms")
            print(f"    Vitesse: {result['speed_kbps']:.2f} KB/s")
            
        except Exception as e:
            print(f"    Erreur: {e}")
    
    # Tableau récapitulatif
    if results:
        print("\n" + "="*80)
        print("RÉSUMÉ COMPARATIF - IMAGES RAW")
        print("="*80)
        print(f"{'Résolution':<15} {'RAW':<12} {'JPG':<12} {'Compressé':<12} {'Ratio RAW':<12} {'Économie':<10}")
        print("-" * 90)
        for r in results:
            print(f"{r['label']:<15} {r['raw_kb']:>10.2f} KB {r['jpg_kb']:>10.2f} KB {r['compressed_kb']:>10.2f} KB {r['ratio_raw']:>10.2f}:1 {r['saving_raw']:>8.2f}%")
    
    return results

def test_compression_efficiency():
    """Analyse l'efficacité de compression"""
    print("\n" + "="*80)
    print("ANALYSE D'EFFICACITÉ")
    print("="*80)
    
    # Créer une image avec différents types de contenu
    print("\n[*] Création image de test avec contenu varié...")
    
    width, height = 800, 600
    image = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Zone 1: Gradient lisse (compressible)
    for x in range(width // 3):
        image[:, x] = [int(255 * x / (width // 3)), 128, 128]
    
    # Zone 2: Bruit aléatoire (peu compressible)
    image[:, width//3:2*width//3] = np.random.randint(0, 256, (height, width//3, 3), dtype=np.uint8)
    
    # Zone 3: Motif répétitif (très compressible)
    for y in range(height):
        for x in range(2*width//3, width):
            if (x + y) % 10 < 5:
                image[y, x] = [255, 255, 255]
            else:
                image[y, x] = [0, 0, 0]
    
    # Sauvegarder
    test_file = "test_efficiency.jpg"
    cv2.imwrite(test_file, image)
    original_size = os.path.getsize(test_file)
    
    print(f"[+] Image créée: {test_file} ({original_size:,} bytes)")
    
    # Compresser
    output_file = "test_efficiency.sdi-img"
    compressor = SDIPureImageCompressor()
    
    print("[*] Compression en cours...")
    start_time = time.time()
    metrics = compressor.save_compressed_image(test_file, output_file)
    compression_time = time.time() - start_time
    
    compressed_size = os.path.getsize(output_file)
    
    print(f"\n[+] RÉSULTATS:")
    print(f"    Original: {original_size:,} bytes ({original_size/1024:.2f} KB)")
    print(f"    Compressé: {compressed_size:,} bytes ({compressed_size/1024:.2f} KB)")
    print(f"    Ratio: {original_size/max(1, compressed_size):.2f}:1")
    print(f"    Économie: {(1 - compressed_size/original_size)*100:.2f}%")
    print(f"    Temps: {compression_time:.3f}s")
    print(f"    Vitesse: {original_size/1024/max(0.001, compression_time):.2f} KB/s")

if __name__ == "__main__":
    try:
        # Test RAW
        results = test_raw_compression()
        
        # Test efficacité
        test_compression_efficiency()
        
        print("\n" + "="*80)
        print("TESTS COMPLÉTÉS")
        print("="*80)
        
    except Exception as e:
        print(f"\nErreur: {e}")
        import traceback
        traceback.print_exc()
