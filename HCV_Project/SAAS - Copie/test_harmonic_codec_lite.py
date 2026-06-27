#!/usr/bin/env python3
"""
TEST LÉGER DU HARMONIC CODEC V16
Version optimisée pour mémoire limitée
"""

import sys
import os
import time
import json
import numpy as np

from harmonic_codec_v16 import HCV16Writer, HCV16Reader, psnr, ssim

def create_simple_frame(h=240, w=320, bits=12, noise_pct=0.01):
    """Crée une frame simple sans utiliser make_frame"""
    maxv = (1 << bits) - 1
    
    # Créer gradient
    img = np.zeros((h, w, 3), dtype=np.float32)
    for x in range(w):
        img[:, x, 0] = maxv * x / w  # R
        img[:, x, 1] = maxv * 0.5    # G
        img[:, x, 2] = maxv * (1 - x / w)  # B
    
    # Ajouter bruit
    np.random.seed(42)
    grain = np.random.normal(0, maxv * noise_pct, (h, w, 3))
    
    return np.clip(img + grain, 0, maxv).astype(np.uint16)

def test_basic():
    """Test basique"""
    print("="*80)
    print("TEST 1: COMPRESSION BASIQUE (320x240)")
    print("="*80)
    
    print("\n[*] Création frame...")
    frame = create_simple_frame(h=240, w=320, bits=12, noise_pct=0.01)
    original_size = frame.nbytes
    
    print(f"[+] Frame: {frame.shape}, dtype={frame.dtype}, size={original_size:,} bytes")
    
    print("\n[*] Compression...")
    output_file = "test_hcv16_lite.hcv16"
    
    start = time.time()
    try:
        writer = HCV16Writer(output_file, mode='GRAIN_SYNTH',
                            bit_depth=12, width=320, height=240, fps=(24, 1))
        writer.add_frame(frame, 0)
        file_size = writer.finalize()
        comp_time = time.time() - start
        
        ratio = original_size / max(1, file_size)
        saving = (1 - file_size / original_size) * 100
        
        print(f"\n[+] RÉSULTATS:")
        print(f"    Original: {original_size:,} bytes ({original_size/1024:.1f} KB)")
        print(f"    Compressé: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        print(f"    Ratio: {ratio:.2f}:1")
        print(f"    Économie: {saving:.2f}%")
        print(f"    Temps: {comp_time:.3f}s")
        print(f"    Vitesse: {original_size/1024/max(0.001, comp_time):.1f} KB/s")
        
        print(f"\n[*] Décodage...")
        reader = HCV16Reader(output_file)
        reader.open()
        decoded = reader.decode_frame(0)
        
        # Vérifier lossless
        if np.array_equal(frame, decoded):
            print(f"    Lossless: ✅ Parfait")
            lossless = True
        else:
            diff = np.abs(frame.astype(np.int32) - decoded.astype(np.int32))
            max_diff = np.max(diff)
            mean_diff = np.mean(diff)
            print(f"    Lossless: ❌ Différences")
            print(f"      Max diff: {max_diff}")
            print(f"      Mean diff: {mean_diff:.2f}")
            lossless = False
        
        return {
            'original': original_size,
            'compressed': file_size,
            'ratio': ratio,
            'saving': saving,
            'time': comp_time,
            'lossless': lossless
        }
        
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
        (160, 120, "QQVGA"),
        (320, 240, "QVGA"),
        (640, 480, "VGA"),
    ]
    
    results = []
    
    for width, height, label in resolutions:
        print(f"\n[*] Test {label} ({width}x{height})...")
        
        frame = create_simple_frame(h=height, w=width, bits=12, noise_pct=0.01)
        original_size = frame.nbytes
        
        output_file = f"test_hcv16_{label}.hcv16"
        
        start = time.time()
        try:
            writer = HCV16Writer(output_file, mode='GRAIN_SYNTH',
                                bit_depth=12, width=width, height=height, fps=(24, 1))
            writer.add_frame(frame, 0)
            file_size = writer.finalize()
            comp_time = time.time() - start
            
            ratio = original_size / max(1, file_size)
            saving = (1 - file_size / original_size) * 100
            
            # Décoder
            reader = HCV16Reader(output_file)
            reader.open()
            decoded = reader.decode_frame(0)
            lossless = np.array_equal(frame, decoded)
            
            result = {
                'label': label,
                'dimensions': f"{width}x{height}",
                'original_kb': original_size / 1024,
                'compressed_kb': file_size / 1024,
                'ratio': ratio,
                'saving': saving,
                'time_ms': comp_time * 1000,
                'lossless': lossless
            }
            results.append(result)
            
            print(f"    Original: {result['original_kb']:.1f} KB")
            print(f"    Compressé: {result['compressed_kb']:.1f} KB")
            print(f"    Ratio: {result['ratio']:.2f}:1")
            print(f"    Économie: {result['saving']:.2f}%")
            print(f"    Lossless: {'✅' if lossless else '❌'}")
            
        except Exception as e:
            print(f"    Erreur: {e}")
    
    # Tableau
    if results:
        print("\n" + "="*80)
        print("RÉSUMÉ - RÉSOLUTIONS")
        print("="*80)
        print(f"{'Résolution':<15} {'Original':<12} {'Compressé':<12} {'Ratio':<10} {'Économie':<10} {'Lossless':<10}")
        print("-" * 80)
        for r in results:
            print(f"{r['label']:<15} {r['original_kb']:>10.1f} KB {r['compressed_kb']:>10.1f} KB {r['ratio']:>8.2f}:1 {r['saving']:>8.2f}% {'✅' if r['lossless'] else '❌'}")
    
    return results

def test_modes():
    """Test différents modes"""
    print("\n" + "="*80)
    print("TEST 3: DIFFÉRENTS MODES")
    print("="*80)
    
    frame = create_simple_frame(h=240, w=320, bits=12, noise_pct=0.01)
    original_size = frame.nbytes
    
    modes = ['LOSSLESS', 'GRAIN_SYNTH', 'SIGNAL_ONLY']
    results = []
    
    for mode in modes:
        print(f"\n[*] Mode: {mode}")
        
        output_file = f"test_hcv16_{mode}.hcv16"
        
        start = time.time()
        try:
            writer = HCV16Writer(output_file, mode=mode,
                                bit_depth=12, width=320, height=240, fps=(24, 1))
            writer.add_frame(frame, 0)
            file_size = writer.finalize()
            comp_time = time.time() - start
            
            ratio = original_size / max(1, file_size)
            saving = (1 - file_size / original_size) * 100
            
            # Décoder
            reader = HCV16Reader(output_file)
            reader.open()
            decoded = reader.decode_frame(0)
            lossless = np.array_equal(frame, decoded)
            
            result = {
                'mode': mode,
                'original': original_size,
                'compressed': file_size,
                'ratio': ratio,
                'saving': saving,
                'time_ms': comp_time * 1000,
                'lossless': lossless
            }
            results.append(result)
            
            print(f"    Ratio: {ratio:.2f}:1")
            print(f"    Économie: {saving:.2f}%")
            print(f"    Lossless: {'✅' if lossless else '❌'}")
            
        except Exception as e:
            print(f"    Erreur: {e}")
    
    # Tableau
    if results:
        print("\n" + "="*80)
        print("RÉSUMÉ - MODES")
        print("="*80)
        print(f"{'Mode':<15} {'Ratio':<10} {'Économie':<10} {'Lossless':<10}")
        print("-" * 50)
        for r in results:
            print(f"{r['mode']:<15} {r['ratio']:>8.2f}:1 {r['saving']:>8.2f}% {'✅' if r['lossless'] else '❌'}")
    
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
        
        frame = create_simple_frame(h=240, w=320, bits=bits, noise_pct=0.01)
        original_size = frame.nbytes
        
        output_file = f"test_hcv16_{bits}bit.hcv16"
        
        start = time.time()
        try:
            writer = HCV16Writer(output_file, mode='GRAIN_SYNTH',
                                bit_depth=bits, width=320, height=240, fps=(24, 1))
            writer.add_frame(frame, 0)
            file_size = writer.finalize()
            comp_time = time.time() - start
            
            ratio = original_size / max(1, file_size)
            saving = (1 - file_size / original_size) * 100
            
            # Décoder
            reader = HCV16Reader(output_file)
            reader.open()
            decoded = reader.decode_frame(0)
            lossless = np.array_equal(frame, decoded)
            
            result = {
                'bits': bits,
                'original_kb': original_size / 1024,
                'compressed_kb': file_size / 1024,
                'ratio': ratio,
                'saving': saving,
                'time_ms': comp_time * 1000,
                'lossless': lossless
            }
            results.append(result)
            
            print(f"    Original: {result['original_kb']:.1f} KB")
            print(f"    Compressé: {result['compressed_kb']:.1f} KB")
            print(f"    Ratio: {result['ratio']:.2f}:1")
            print(f"    Économie: {result['saving']:.2f}%")
            print(f"    Lossless: {'✅' if lossless else '❌'}")
            
        except Exception as e:
            print(f"    Erreur: {e}")
    
    # Tableau
    if results:
        print("\n" + "="*80)
        print("RÉSUMÉ - PROFONDEURS DE BITS")
        print("="*80)
        print(f"{'Bits':<8} {'Original':<12} {'Compressé':<12} {'Ratio':<10} {'Économie':<10} {'Lossless':<10}")
        print("-" * 75)
        for r in results:
            print(f"{r['bits']:<8} {r['original_kb']:>10.1f} KB {r['compressed_kb']:>10.1f} KB {r['ratio']:>8.2f}:1 {r['saving']:>8.2f}% {'✅' if r['lossless'] else '❌'}")
    
    return results

if __name__ == "__main__":
    try:
        # Test basique
        result_basic = test_basic()
        
        # Test résolutions
        results_res = test_resolutions()
        
        # Test modes
        results_modes = test_modes()
        
        # Test bit depths
        results_bits = test_bit_depths()
        
        # Résumé final
        print("\n" + "="*80)
        print("RÉSUMÉ FINAL - HARMONIC CODEC V16")
        print("="*80)
        
        print(f"\n[+] Tests complétés!")
        
        if result_basic:
            print(f"\n[+] RÉSULTATS PRINCIPAUX (320x240, 12 bits):")
            print(f"    Ratio: {result_basic['ratio']:.2f}:1")
            print(f"    Économie: {result_basic['saving']:.2f}%")
            print(f"    Vitesse: {result_basic['original']/1024/max(0.001, result_basic['time']):.1f} KB/s")
            print(f"    Lossless: {'✅' if result_basic['lossless'] else '❌'}")
        
        # Sauvegarder
        summary = {
            'test_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'basic_test': result_basic,
            'resolutions': results_res,
            'modes': results_modes,
            'bit_depths': results_bits
        }
        
        with open('harmonic_codec_v16_lite_results.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"\n[+] Résultats: harmonic_codec_v16_lite_results.json")
        
    except Exception as e:
        print(f"\nErreur: {e}")
        import traceback
        traceback.print_exc()
