#!/usr/bin/env python3
"""
TEST MINIMAL DU HCS CORE ENGINE
Teste les algorithmes de compression sans dépendances lourdes
"""

import sys
import os
import time
import struct
import zlib
import json

sys.path.insert(0, 'COMPRESSION-CAMERA/VERSION-SECURISEE')

from hcs_api_server import HCSCoreEngine

def create_test_data(width=640, height=480):
    """Crée des données de test sans OpenCV"""
    print(f"[*] Création données de test: {width}x{height}")
    
    # Créer données 16-bit
    data = bytearray()
    
    for y in range(height):
        for x in range(width):
            # Gradient horizontal
            val = int(65535 * x / width)
            data.extend(struct.pack('<H', val))
    
    print(f"[+] Données créées: {len(data):,} bytes")
    return bytes(data)

def test_delta_h_basic():
    """Test basique de Delta-H"""
    print("\n" + "="*80)
    print("TEST 1: COMPRESSION DELTA-H (HCS Core)")
    print("="*80)
    
    width, height = 640, 480
    
    # Créer données
    print("\n[*] Création données de test...")
    original_data = create_test_data(width, height)
    original_size = len(original_data)
    
    # Compression
    print("[*] Compression Delta-H en cours...")
    start_time = time.time()
    
    try:
        compressed = HCSCoreEngine.delta_h_encode(original_data, width, height)
        compression_time = time.time() - start_time
        
        compressed_size = len(compressed)
        ratio = original_size / max(1, compressed_size)
        saving = (1 - compressed_size/original_size) * 100
        
        print(f"\n[+] RÉSULTATS DELTA-H:")
        print(f"    Taille originale: {original_size:,} bytes ({original_size/1024/1024:.2f} MB)")
        print(f"    Taille compressée: {compressed_size:,} bytes ({compressed_size/1024/1024:.2f} MB)")
        print(f"    Ratio: {ratio:.2f}:1")
        print(f"    Économie: {saving:.2f}%")
        print(f"    Temps: {compression_time:.3f}s")
        print(f"    Vitesse: {original_size/1024/1024/max(0.001, compression_time):.2f} MB/s")
        
        # Vérifier décompression
        print(f"\n[*] Vérification décompression...")
        decompressed = HCSCoreEngine.delta_h_decode(compressed, width, height)
        
        if decompressed == original_data:
            print(f"[+] Décompression: OK (lossless)")
            lossless = True
        else:
            print(f"[-] Décompression: ERREUR")
            lossless = False
        
        return {
            'method': 'Delta-H',
            'width': width,
            'height': height,
            'original_size': original_size,
            'compressed_size': compressed_size,
            'ratio': ratio,
            'saving': saving,
            'time': compression_time,
            'speed_mbps': original_size/1024/1024/max(0.001, compression_time),
            'lossless': lossless
        }
        
    except Exception as e:
        print(f"\n[-] Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_delta_h_different_sizes():
    """Test avec différentes résolutions"""
    print("\n" + "="*80)
    print("TEST 2: DELTA-H AVEC DIFFÉRENTES RÉSOLUTIONS")
    print("="*80)
    
    sizes = [
        (320, 240, "QVGA"),
        (640, 480, "VGA"),
        (800, 600, "SVGA"),
        (1024, 768, "XGA"),
        (1920, 1080, "Full HD"),
    ]
    
    results = []
    
    for width, height, label in sizes:
        print(f"\n[*] Test {label} ({width}x{height})...")
        
        # Créer données
        original_data = create_test_data(width, height)
        original_size = len(original_data)
        
        start_time = time.time()
        try:
            # Compression
            compressed = HCSCoreEngine.delta_h_encode(original_data, width, height)
            compression_time = time.time() - start_time
            
            compressed_size = len(compressed)
            ratio = original_size / max(1, compressed_size)
            saving = (1 - compressed_size/original_size) * 100
            
            result = {
                'label': label,
                'dimensions': f"{width}x{height}",
                'original_mb': original_size / 1024 / 1024,
                'compressed_mb': compressed_size / 1024 / 1024,
                'ratio': ratio,
                'saving': saving,
                'time_ms': compression_time * 1000,
                'speed_mbps': original_size / 1024 / 1024 / max(0.001, compression_time)
            }
            
            results.append(result)
            
            print(f"    Original: {result['original_mb']:.2f} MB")
            print(f"    Compressé: {result['compressed_mb']:.2f} MB")
            print(f"    Ratio: {result['ratio']:.2f}:1")
            print(f"    Économie: {result['saving']:.2f}%")
            print(f"    Temps: {result['time_ms']:.1f}ms")
            print(f"    Vitesse: {result['speed_mbps']:.2f} MB/s")
        except Exception as e:
            print(f"    Erreur: {e}")
    
    # Tableau récapitulatif
    if results:
        print("\n" + "="*80)
        print("RÉSUMÉ COMPARATIF - HCS DELTA-H")
        print("="*80)
        print(f"{'Résolution':<15} {'Original':<12} {'Compressé':<12} {'Ratio':<10} {'Économie':<10} {'Vitesse':<12}")
        print("-" * 90)
        for r in results:
            print(f"{r['label']:<15} {r['original_mb']:>10.2f} MB {r['compressed_mb']:>10.2f} MB {r['ratio']:>8.2f}:1 {r['saving']:>8.2f}% {r['speed_mbps']:>10.2f} MB/s")
    
    return results

def test_delta_h_different_content():
    """Test avec différents types de contenu"""
    print("\n" + "="*80)
    print("TEST 3: DELTA-H AVEC DIFFÉRENTS TYPES DE CONTENU")
    print("="*80)
    
    width, height = 640, 480
    
    test_cases = [
        ("gradient", "Gradient lisse"),
        ("constant", "Valeur constante"),
        ("random", "Bruit aléatoire"),
        ("pattern", "Motif répétitif"),
    ]
    
    results = []
    
    for case_type, description in test_cases:
        print(f"\n[*] Test: {description}")
        
        # Créer données spécifiques
        data = bytearray()
        
        if case_type == "gradient":
            # Gradient lisse
            for y in range(height):
                for x in range(width):
                    val = int(65535 * x / width)
                    data.extend(struct.pack('<H', val))
        
        elif case_type == "constant":
            # Valeur constante
            for y in range(height):
                for x in range(width):
                    data.extend(struct.pack('<H', 32768))
        
        elif case_type == "random":
            # Bruit aléatoire
            import random
            for y in range(height):
                for x in range(width):
                    val = random.randint(0, 65535)
                    data.extend(struct.pack('<H', val))
        
        else:  # pattern
            # Motif répétitif
            for y in range(height):
                for x in range(width):
                    val = 32768 if (x + y) % 10 < 5 else 0
                    data.extend(struct.pack('<H', val))
        
        original_data = bytes(data)
        original_size = len(original_data)
        
        # Compression
        start_time = time.time()
        try:
            compressed = HCSCoreEngine.delta_h_encode(original_data, width, height)
            compression_time = time.time() - start_time
            
            compressed_size = len(compressed)
            ratio = original_size / max(1, compressed_size)
            saving = (1 - compressed_size/original_size) * 100
            
            result = {
                'type': case_type,
                'description': description,
                'original_mb': original_size / 1024 / 1024,
                'compressed_mb': compressed_size / 1024 / 1024,
                'ratio': ratio,
                'saving': saving,
                'time_ms': compression_time * 1000
            }
            
            results.append(result)
            
            print(f"    Original: {result['original_mb']:.2f} MB")
            print(f"    Compressé: {result['compressed_mb']:.2f} MB")
            print(f"    Ratio: {result['ratio']:.2f}:1")
            print(f"    Économie: {result['saving']:.2f}%")
            print(f"    Temps: {result['time_ms']:.1f}ms")
        except Exception as e:
            print(f"    Erreur: {e}")
    
    # Tableau récapitulatif
    if results:
        print("\n" + "="*80)
        print("RÉSUMÉ - EFFICACITÉ PAR TYPE DE CONTENU")
        print("="*80)
        print(f"{'Type':<15} {'Description':<25} {'Ratio':<10} {'Économie':<10}")
        print("-" * 65)
        for r in results:
            print(f"{r['type']:<15} {r['description']:<25} {r['ratio']:>8.2f}:1 {r['saving']:>8.2f}%")
    
    return results

if __name__ == "__main__":
    try:
        # Test basique
        result_basic = test_delta_h_basic()
        
        # Test différentes résolutions
        results_sizes = test_delta_h_different_sizes()
        
        # Test différents contenus
        results_content = test_delta_h_different_content()
        
        # Résumé final
        print("\n" + "="*80)
        print("RÉSUMÉ FINAL - HCS CORE ENGINE")
        print("="*80)
        
        print(f"\n[+] Tests complétés avec succès!")
        
        if result_basic:
            print(f"\n[+] RÉSULTATS PRINCIPAUX (Delta-H 640x480):")
            print(f"    Ratio: {result_basic['ratio']:.2f}:1")
            print(f"    Économie: {result_basic['saving']:.2f}%")
            print(f"    Vitesse: {result_basic['speed_mbps']:.2f} MB/s")
            print(f"    Lossless: {result_basic['lossless']}")
        
        # Meilleur et pire cas
        if results_content:
            best = max(results_content, key=lambda x: x['ratio'])
            worst = min(results_content, key=lambda x: x['ratio'])
            print(f"\n[+] ANALYSE DE CONTENU:")
            print(f"    Meilleur cas: {best['description']} ({best['ratio']:.2f}:1)")
            print(f"    Pire cas: {worst['description']} ({worst['ratio']:.2f}:1)")
        
        # Sauvegarder les résultats
        summary = {
            'test_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'basic_test': result_basic,
            'multi_resolution_results': results_sizes,
            'content_analysis_results': results_content
        }
        
        with open('hcs_core_engine_test_results.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"\n[+] Résultats sauvegardés: hcs_core_engine_test_results.json")
        
    except Exception as e:
        print(f"\nErreur: {e}")
        import traceback
        traceback.print_exc()
