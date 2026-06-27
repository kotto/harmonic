#!/usr/bin/env python3
"""
TEST DU HCV IMAGE CODEC
Solution professionnelle pour images YCbCr 4:2:2
"""

import sys
import os
import time
import json
import numpy as np

sys.path.insert(0, 'COMPRESSION-CAMERA/METHOD_2_SDI_LIKE_IMAGE_COMPRESSION')

from hcv_image_codec import HCVImageCodec

def create_test_image(h=480, w=640, bits=12):
    """Crée une image de test réaliste"""
    maxv = (1 << bits) - 1
    
    # Créer gradient + texture
    image = np.zeros((h, w, 3), dtype=np.uint16)
    
    for x in range(w):
        for y in range(h):
            # Gradient
            r = int(maxv * x / w)
            g = int(maxv * 0.5)
            b = int(maxv * (1 - x / w))
            
            # Ajouter texture
            texture = int(maxv * 0.1 * np.sin(x / 50) * np.cos(y / 50))
            
            image[y, x, 0] = np.clip(r + texture, 0, maxv)
            image[y, x, 1] = np.clip(g + texture, 0, maxv)
            image[y, x, 2] = np.clip(b + texture, 0, maxv)
    
    return image

def test_basic():
    """Test basique"""
    print("="*80)
    print("TEST 1: COMPRESSION BASIQUE (640x480, 12 bits)")
    print("="*80)
    
    print("\n[*] Création image...")
    image = create_test_image(h=480, w=640, bits=12)
    original_size = image.nbytes
    
    print(f"[+] Image: {image.shape}, dtype={image.dtype}, size={original_size:,} bytes")
    
    print("\n[*] Compression GRAIN_SYNTH...")
    codec = HCVImageCodec(mode='GRAIN_SYNTH', bit_depth=12, zstd_level=11)
    
    start = time.time()
    try:
        hci_data = codec.encode_image(image)
        comp_time = time.time() - start
        
        compressed_size = len(hci_data)
        metrics = codec.get_metrics(original_size, compressed_size, comp_time)
        
        print(f"\n[+] RÉSULTATS:")
        print(f"    Original: {metrics['original_size']:,} bytes ({metrics['original_size']/1024/1024:.2f} MB)")
        print(f"    Compressé: {metrics['compressed_size']:,} bytes ({metrics['compressed_size']/1024/1024:.2f} MB)")
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

def test_modes():
    """Test différents modes"""
    print("\n" + "="*80)
    print("TEST 2: COMPARAISON DES MODES")
    print("="*80)
    
    image = create_test_image(h=480, w=640, bits=12)
    original_size = image.nbytes
    
    modes = ['LOSSLESS', 'GRAIN_SYNTH']
    results = []
    
    for mode in modes:
        print(f"\n[*] Mode: {mode}")
        
        codec = HCVImageCodec(mode=mode, bit_depth=12, zstd_level=11)
        
        start = time.time()
        try:
            hci_data = codec.encode_image(image)
            comp_time = time.time() - start
            
            compressed_size = len(hci_data)
            metrics = codec.get_metrics(original_size, compressed_size, comp_time)
            
            results.append(metrics)
            
            print(f"    Ratio: {metrics['ratio']:.2f}:1")
            print(f"    Économie: {metrics['saving']:.2f}%")
            print(f"    Temps: {metrics['time_seconds']:.3f}s")
            
        except Exception as e:
            print(f"    Erreur: {e}")
    
    # Tableau
    if results:
        print("\n" + "="*80)
        print("RÉSUMÉ - MODES")
        print("="*80)
        print(f"{'Mode':<15} {'Ratio':<10} {'Économie':<10} {'Temps':<10}")
        print("-" * 50)
        for r in results:
            print(f"{r['mode']:<15} {r['ratio']:>8.2f}:1 {r['saving']:>8.2f}% {r['time_seconds']:>8.3f}s")
    
    return results

def test_resolutions():
    """Test différentes résolutions"""
    print("\n" + "="*80)
    print("TEST 3: DIFFÉRENTES RÉSOLUTIONS")
    print("="*80)
    
    resolutions = [
        (320, 240, "QVGA"),
        (640, 480, "VGA"),
        (1280, 720, "HD"),
    ]
    
    results = []
    
    for width, height, label in resolutions:
        print(f"\n[*] Test {label} ({width}x{height})...")
        
        image = create_test_image(h=height, w=width, bits=12)
        original_size = image.nbytes
        
        codec = HCVImageCodec(mode='GRAIN_SYNTH', bit_depth=12, zstd_level=11)
        
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
    print("TEST 4: DIFFÉRENTES PROFONDEURS DE BITS")
    print("="*80)
    
    bit_depths = [8, 10, 12, 14, 16]
    results = []
    
    for bits in bit_depths:
        print(f"\n[*] Test {bits} bits...")
        
        image = create_test_image(h=480, w=640, bits=bits)
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
        # Test basique
        result_basic = test_basic()
        
        # Test modes
        results_modes = test_modes()
        
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
            print(f"\n[+] RÉSULTATS PRINCIPAUX (640x480, 12 bits, GRAIN_SYNTH):")
            print(f"    Ratio: {result_basic['ratio']:.2f}:1")
            print(f"    Économie: {result_basic['saving']:.2f}%")
            print(f"    Vitesse: {result_basic['speed_mbps']:.2f} MB/s")
        
        # Sauvegarder
        summary = {
            'test_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'basic_test': result_basic,
            'modes_comparison': results_modes,
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
