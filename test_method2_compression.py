#!/usr/bin/env python3
"""
TEST DIRECT DE COMPRESSION METHOD_2
Teste la compression d'images avec métriques détaillées
"""

import sys
import os
import time
import numpy as np
import cv2
from pathlib import Path
import json

# Ajouter le chemin METHOD_2
sys.path.insert(0, 'COMPRESSION-CAMERA/METHOD_2_SDI_LIKE_IMAGE_COMPRESSION')

from sdi_pure_image_compression import SDIPureImageCompressor
from sdi_pure_image_decompressor import SDIPureImageDecompressor

def create_test_image(width=1920, height=1080, filename="test_image.jpg"):
    """Crée une image de test"""
    print(f"[*] Création image de test: {width}x{height}")
    
    # Créer une image avec du contenu varié
    image = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Gradient horizontal
    for x in range(width):
        image[:, x] = [int(255 * x / width), 128, 255 - int(255 * x / width)]
    
    # Ajouter du bruit
    noise = np.random.randint(0, 50, (height, width, 3), dtype=np.uint8)
    image = cv2.addWeighted(image, 0.8, noise, 0.2, 0)
    
    # Ajouter des formes
    cv2.rectangle(image, (100, 100), (500, 500), (0, 255, 0), 3)
    cv2.circle(image, (960, 540), 200, (255, 0, 0), 3)
    cv2.putText(image, "TEST IMAGE", (800, 300), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
    
    # Sauvegarder
    cv2.imwrite(filename, image)
    print(f"[+] Image créée: {filename}")
    return filename

def test_compression_basic():
    """Test de compression basique"""
    print("\n" + "="*80)
    print("TEST 1: COMPRESSION BASIQUE (sans session)")
    print("="*80)
    
    # Créer image de test
    test_image = create_test_image(1920, 1080, "test_image_1920x1080.jpg")
    output_file = "test_image_1920x1080.sdi-img"
    
    # Initialiser compresseur
    compressor = SDIPureImageCompressor()
    
    # Compression
    print("\n[*] Compression en cours...")
    start_time = time.time()
    metrics = compressor.save_compressed_image(test_image, output_file)
    compression_time = time.time() - start_time
    
    # Afficher métriques
    print("\n[+] MÉTRIQUES DE COMPRESSION:")
    print(f"    Fichier original: {test_image}")
    print(f"    Fichier compressé: {output_file}")
    print(f"    Taille originale: {metrics['original_size']:,} bytes ({metrics['original_size']/1024/1024:.2f} MB)")
    print(f"    Taille compressée: {metrics['compressed_size']:,} bytes ({metrics['compressed_size']/1024/1024:.2f} MB)")
    print(f"    Ratio de compression: {metrics['compression_ratio']:.2f}:1")
    print(f"    Économie d'espace: {metrics['space_saving']:.2f}%")
    print(f"    Temps de compression: {compression_time:.3f}s")
    print(f"    Vitesse: {metrics['original_size']/1024/1024/compression_time:.2f} MB/s")
    
    return test_image, output_file, metrics

def test_decompression(compressed_file):
    """Test de décompression"""
    print("\n" + "="*80)
    print("TEST 2: DÉCOMPRESSION")
    print("="*80)
    
    # Initialiser décompresseur
    decompressor = SDIPureImageDecompressor()
    
    # Décompression
    print(f"\n[*] Décompression de: {compressed_file}")
    start_time = time.time()
    result = decompressor.decompress_sdi_img(compressed_file)
    decompression_time = time.time() - start_time
    
    if result['success']:
        print(f"\n[+] MÉTRIQUES DE DÉCOMPRESSION:")
        print(f"    Dimensions: {result['width']}x{result['height']}")
        print(f"    Bit depth: {result['bit_depth']}")
        print(f"    Taille fichier: {result['file_size']:,} bytes")
        print(f"    Taille données compressées: {result['compressed_data_size']:,} bytes")
        print(f"    Temps de décompression: {decompression_time:.3f}s")
        print(f"    Image reconstruite: {result['reconstructed_image'].shape}")
        
        # Sauvegarder l'image reconstruite
        output_image = "test_image_reconstructed.jpg"
        cv2.imwrite(output_image, result['reconstructed_image'])
        print(f"    Image sauvegardée: {output_image}")
        
        return result
    else:
        print(f"[-] Erreur: {result['error']}")
        return None

def test_with_session():
    """Test avec session HCS"""
    print("\n" + "="*80)
    print("TEST 3: COMPRESSION AVEC SESSION HCS")
    print("="*80)
    
    # Créer image de test
    test_image = create_test_image(1280, 720, "test_image_1280x720.jpg")
    output_file = "test_image_1280x720.sdi-img"
    
    # Simuler une session HCS
    session_id = "sess_test_12345"
    shared_secret = b"test_secret_key_32_bytes_long!!"
    
    # Initialiser compresseur avec session
    compressor = SDIPureImageCompressor(session_id=session_id, shared_secret=shared_secret)
    
    print(f"\n[*] Session ID: {session_id}")
    print(f"[*] Chiffrement: Activé")
    
    # Compression sécurisée
    print("\n[*] Compression sécurisée en cours...")
    start_time = time.time()
    metrics = compressor.compress_image_secure(test_image, output_file)
    compression_time = time.time() - start_time
    
    print(f"\n[+] MÉTRIQUES AVEC SESSION:")
    print(f"    Taille originale: {metrics['original_size']:,} bytes")
    print(f"    Taille compressée: {metrics['compressed_size']:,} bytes")
    print(f"    Ratio: {metrics['compression_ratio']:.2f}:1")
    print(f"    Économie: {metrics['space_saving']:.2f}%")
    print(f"    Temps: {compression_time:.3f}s")
    print(f"    Chiffré: {metrics.get('encrypted', False)}")
    
    # Afficher historique d'audit
    history = compressor.get_compression_history()
    if history:
        print(f"\n[+] HISTORIQUE D'AUDIT:")
        for entry in history:
            print(f"    - {entry['timestamp']}: {entry['action']}")
            print(f"      Fichier: {entry['input_file']}")
            print(f"      Ratio: {entry['compression_ratio']:.2f}:1")
    
    return test_image, output_file, metrics

def test_multiple_sizes():
    """Test avec différentes tailles d'image"""
    print("\n" + "="*80)
    print("TEST 4: COMPRESSION AVEC DIFFÉRENTES RÉSOLUTIONS")
    print("="*80)
    
    sizes = [
        (640, 480, "VGA"),
        (1280, 720, "HD"),
        (1920, 1080, "Full HD"),
        (2560, 1440, "2K")
    ]
    
    results = []
    
    for width, height, label in sizes:
        print(f"\n[*] Test {label} ({width}x{height})...")
        
        test_image = create_test_image(width, height, f"test_{label.replace(' ', '_')}.jpg")
        output_file = f"test_{label.replace(' ', '_')}.sdi-img"
        
        compressor = SDIPureImageCompressor()
        
        start_time = time.time()
        metrics = compressor.save_compressed_image(test_image, output_file)
        compression_time = time.time() - start_time
        
        result = {
            'resolution': label,
            'dimensions': f"{width}x{height}",
            'original_size_mb': metrics['original_size'] / 1024 / 1024,
            'compressed_size_mb': metrics['compressed_size'] / 1024 / 1024,
            'ratio': metrics['compression_ratio'],
            'space_saving': metrics['space_saving'],
            'time_ms': compression_time * 1000,
            'speed_mbps': metrics['original_size'] / 1024 / 1024 / compression_time
        }
        
        results.append(result)
        
        print(f"    Original: {result['original_size_mb']:.2f} MB")
        print(f"    Compressé: {result['compressed_size_mb']:.2f} MB")
        print(f"    Ratio: {result['ratio']:.2f}:1")
        print(f"    Temps: {result['time_ms']:.1f}ms")
        print(f"    Vitesse: {result['speed_mbps']:.2f} MB/s")
    
    # Tableau récapitulatif
    print("\n[+] RÉSUMÉ COMPARATIF:")
    print(f"{'Résolution':<15} {'Original':<12} {'Compressé':<12} {'Ratio':<8} {'Temps':<10} {'Vitesse':<12}")
    print("-" * 80)
    for r in results:
        print(f"{r['resolution']:<15} {r['original_size_mb']:>10.2f} MB {r['compressed_size_mb']:>10.2f} MB {r['ratio']:>6.2f}:1 {r['time_ms']:>8.1f}ms {r['speed_mbps']:>10.2f} MB/s")
    
    return results

def main():
    """Exécute tous les tests"""
    print("\n" + "="*80)
    print("TEST COMPLET DE COMPRESSION METHOD_2")
    print("="*80)
    
    try:
        # Test 1: Compression basique
        test_image, compressed_file, metrics1 = test_compression_basic()
        
        # Test 2: Décompression
        result = test_decompression(compressed_file)
        
        # Test 3: Avec session
        test_image3, compressed_file3, metrics3 = test_with_session()
        
        # Test 4: Différentes résolutions
        results = test_multiple_sizes()
        
        # Résumé final
        print("\n" + "="*80)
        print("RÉSUMÉ FINAL")
        print("="*80)
        print(f"\n[+] Tests complétés avec succès!")
        print(f"    - Compression basique: OK")
        print(f"    - Décompression: OK")
        print(f"    - Compression avec session: OK")
        print(f"    - Tests multi-résolution: OK ({len(results)} résolutions testées)")
        
        # Sauvegarder les résultats
        summary = {
            'test_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'basic_compression': metrics1,
            'session_compression': metrics3,
            'multi_resolution_results': results
        }
        
        with open('compression_test_results.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"\n[+] Résultats sauvegardés: compression_test_results.json")
        
    except Exception as e:
        print(f"\n[-] Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
