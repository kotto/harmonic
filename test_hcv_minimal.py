#!/usr/bin/env python3
"""
TEST MINIMAL HCV IMAGE CODEC
Évite les problèmes OpenBLAS en utilisant des images plus petites
"""

import sys
import os
import time
import json
import struct

sys.path.insert(0, 'COMPRESSION-CAMERA/METHOD_2_SDI_LIKE_IMAGE_COMPRESSION')

# Désactiver OpenBLAS
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'

import numpy as np
from hcv_image_codec import HCVImageCodec

def create_simple_image(h=240, w=320, bits=12):
    """Crée une image très simple pour éviter les problèmes mémoire"""
    maxv = (1 << bits) - 1
    
    # Image simple: gradient horizontal
    image = np.zeros((h, w, 3), dtype=np.uint16)
    
    for x in range(w):
        val = int(maxv * x / w)
        image[:, x, 0] = val      # R
        image[:, x, 1] = maxv // 2  # G
        image[:, x, 2] = maxv - val  # B
    
    return image

def test_basic():
    """Test basique minimal"""
    print("="*80)
    print("TEST 1: COMPRESSION BASIQUE (320x240, 12 bits)")
    print("="*80)
    
    print("\n[*] Création image simple...")
    image = create_simple_image(h=240, w=320, bits=12)
    original_size = image.nbytes
    
    print(f"[+] Image: {image.shape}, dtype={image.dtype}, size={original_size:,} bytes")
    
    print("\n[*] Initialisation codec GRAIN_SYNTH...")
    try:
        codec = HCVImageCodec(mode='GRAIN_SYNTH', bit_depth=12, zstd_level=11)
        print("[+] Codec initialisé")
    except Exception as e:
        print(f"[-] Erreur initialisation: {e}")
        return None
    
    print("\n[*] Compression...")
    start = time.time()
    try:
        hci_data = codec.encode_image(image)
        comp_time = time.time() - start
        
        compressed_size = len(hci_data)
        metrics = codec.get_metrics(original_size, compressed_size, comp_time)
        
        print(f"\n[+] RÉSULTATS:")
        print(f"    Original: {metrics['original_size']:,} bytes ({metrics['original_size']/1024:.2f} KB)")
        print(f"    Compressé: {metrics['compressed_size']:,} bytes ({metrics['compressed_size']/1024:.2f} KB)")
        print(f"    Ratio: {metrics['ratio']:.2f}:1")
        print(f"    Économie: {metrics['saving']:.2f}%")
        print(f"    Temps: {metrics['time_seconds']:.3f}s")
        print(f"    Vitesse: {metrics['speed_mbps']:.2f} MB/s")
        
        print("\n[*] Décodage...")
        decoded = codec.decode_image(hci_data)
        print(f"    Décodé: {decoded.shape}")
        
        return metrics
        
    except Exception as e:
        print(f"[-] Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_resolutions():
    """Test différentes résolutions"""
    print("\n" + "="*80)
    print("TEST 2: DIFFÉRENTES RÉSOLUTIONS")
    print("="*80)
    
    resolutions = [
        (240, 320, "QVGA"),
        (480, 640, "VGA"),
        (720, 1280, "HD"),
    ]
    
    results = []
    codec = HCVImageCodec(mode='GRAIN_SYNTH', bit_depth=12, zstd_level=11)
    
    for width, height, label in resolutions:
        print(f"\n[*] Test {label} ({width}x{height})...")
        
        image = create_simple_image(h=height, w=width, bits=12)
        original_size = image.nbytes
        
        start = time.time()
        try:
            hci_data = codec.encode_image(image)
            comp_time = time.time() - start
            
            compressed_size = len(hci_data)
            metrics = codec.get_metrics(original_size, compressed_size, comp_time)
            
            result = {
                'label': label,
                'dimensions': f"{width}x{height}",
                'original_mb': metrics['original_size'] / 1024 / 1024,
                'compressed_mb': metrics['compressed_size'] / 1024 / 1024,
                'ratio': metrics['ratio'],
                'saving': metrics['saving'],
                'time_ms': metrics['time_seconds'] * 1000,
                'speed_mbps': metrics['speed_mbps']
            }
            results.append(result)
            
            print(f"    Original: {result['original_mb']:.2f} MB")
            print(f"    Compressé: {result['compressed_mb']:.2f} MB")
            print(f"    Ratio: {result['ratio']:.2f}:1")
            print(f"    Économie: {result['saving']:.2f}%")
            print(f"    Temps: {result['time_ms']:.1f}ms")
            
        except Exception as e:
            print(f"    Erreur: {e}")
    
    # Tableau
    if results:
        print("\n" + "="*80)
        print("RÉSUMÉ - RÉSOLUTIONS")
        print("="*80)
        print(f"{'Résolution':<15} {'Original':<12} {'Compressé':<12} {'Ratio':<10} {'Économie':<10}")
        print("-" * 75)
        for r in results:
            print(f"{r['label']:<15} {r['original_mb']:>10.2f} MB {r['compressed_mb']:>10.2f} MB {r['ratio']:>8.2f}:1 {r['saving']:>8.2f}%")
    
    return results

def test_bit_depths():
    """Test différentes profondeurs de bits"""
    print("\n" + "="*80)
    print("TEST 3: DIFFÉRENTES PROFONDEURS DE BITS")
    print("="*80)
    
    bit_depths = [8, 10, 12, 14, 16]
    results = []
    
    for bits in bit_depths:
        print(f"\n[*] Test {bits} bits...")
        
        image = create_simple_image(h=240, w=320, bits=bits)
        original_size = image.nbytes
        
        codec = HCVImageCodec(mode='GRAIN_SYNTH', bit_depth=bits, zstd_level=11)
        
        start = time.time()
        try:
            hci_data = codec.encode_image(image)
            comp_time = time.time() - start
            
            compressed_size = len(hci_data)
            metrics = codec.get_metrics(original_size, compressed_size, comp_time)
            
            result = {
                'bits': bits,
                'original_mb': metrics['original_size'] / 1024 / 1024,
                'compressed_mb': metrics['compressed_size'] / 1024 / 1024,
                'ratio': metrics['ratio'],
                'saving': metrics['saving'],
                'time_ms': metrics['time_seconds'] * 1000
            }
            results.append(result)
            
            print(f"    Original: {result['original_mb']:.2f} MB")
            print(f"    Compressé: {result['compressed_mb']:.2f} MB")
            print(f"    Ratio: {result['ratio']:.2f}:1")
            print(f"    Économie: {result['saving']:.2f}%")
            
        except Exception as e:
            print(f"    Erreur: {e}")
    
    # Tableau
    if results:
        print("\n" + "="*80)
        print("RÉSUMÉ - PROFONDEURS DE BITS")
        print("="*80)
        print(f"{'Bits':<8} {'Original':<12} {'Compressé':<12} {'Ratio':<10} {'Économie':<10}")
        print("-" * 60)
        for r in results:
            print(f"{r['bits']:<8} {r['original_mb']:>10.2f} MB {r['compressed_mb']:>10.2f} MB {r['ratio']:>8.2f}:1 {r['saving']:>8.2f}%")
    
    return results

if __name__ == "__main__":
    try:
        print("\n" + "="*80)
        print("HCV IMAGE CODEC - TEST MINIMAL")
        print("="*80)
        
        # Test basique
        result_basic = test_basic()
        
        # Test résolutions
        results_res = test_resolutions()
        
        # Test bit depths
        results_bits = test_bit_depths()
        
        # Résumé final
        print("\n" + "="*80)
        print("RÉSUMÉ FINAL - HCV IMAGE CODEC")
        print("="*80)
        
        print(f"\n[+] Tests complétés!")
        
        if result_basic:
            print(f"\n[+] RÉSULTATS PRINCIPAUX (320x240, 12 bits, GRAIN_SYNTH):")
            print(f"    Ratio: {result_basic['ratio']:.2f}:1")
            print(f"    Économie: {result_basic['saving']:.2f}%")
            print(f"    Vitesse: {result_basic['speed_mbps']:.2f} MB/s")
        
        # Sauvegarder
        summary = {
            'test_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'basic_test': result_basic,
            'resolutions': results_res,
            'bit_depths': results_bits
        }
        
        with open('hcv_image_codec_results.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"\n[+] Résultats: hcv_image_codec_results.json")
        
    except Exception as e:
        print(f"\nErreur: {e}")
        import traceback
        traceback.print_exc()
