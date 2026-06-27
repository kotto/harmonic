#!/usr/bin/env python3
"""
TEST COMPLET DU HARMONIC CODEC V16
Teste l'implémentation réelle du codec professionnel
"""

import sys
import os
import time
import json
import numpy as np

# Importer le codec
from harmonic_codec_v16 import (
    HCV16Writer, HCV16Reader, make_frame, make_sequence, 
    make_audio, psnr, ssim, snr_audio
)

def test_basic_compression():
    """Test basique de compression"""
    print("="*80)
    print("TEST 1: COMPRESSION BASIQUE")
    print("="*80)
    
    # Créer une frame de test
    print("\n[*] Création frame de test (640x480, 12 bits)...")
    frame = make_frame(h=480, w=640, bits=12, noise_pct=0.01)
    original_size = frame.nbytes
    
    print(f"[+] Frame créée: {frame.shape}, dtype={frame.dtype}, size={original_size:,} bytes")
    
    # Encoder
    print("\n[*] Compression en cours...")
    output_file = "test_hcv16_basic.hcv16"
    
    start_time = time.time()
    try:
        writer = HCV16Writer(output_file, mode='GRAIN_SYNTH', 
                            bit_depth=12, width=640, height=480, fps=(24, 1))
        writer.add_frame(frame, 0)
        file_size = writer.finalize()
        compression_time = time.time() - start_time
        
        # Calculer métriques
        ratio = original_size / max(1, file_size)
        saving = (1 - file_size / original_size) * 100
        
        print(f"\n[+] RÉSULTATS COMPRESSION:")
        print(f"    Taille originale: {original_size:,} bytes ({original_size/1024/1024:.2f} MB)")
        print(f"    Taille compressée: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        print(f"    Ratio: {ratio:.2f}:1")
        print(f"    Économie: {saving:.2f}%")
        print(f"    Temps: {compression_time:.3f}s")
        print(f"    Vitesse: {original_size/1024/1024/max(0.001, compression_time):.2f} MB/s")
        
        # Décoder et vérifier
        print(f"\n[*] Décodage et vérification...")
        reader = HCV16Reader(output_file)
        reader.open()
        
        decoded_frame = reader.decode_frame(0)
        
        # Calculer PSNR et SSIM
        psnr_val = psnr(frame, decoded_frame, maxval=4095)
        ssim_val = ssim(frame, decoded_frame, maxval=4095)
        
        print(f"    PSNR: {psnr_val:.2f} dB")
        print(f"    SSIM: {ssim_val:.6f}")
        
        # Vérifier lossless
        if np.array_equal(frame, decoded_frame):
            print(f"    Lossless: ✅ Parfait (bit-à-bit identique)")
            lossless = True
        else:
            diff = np.abs(frame.astype(np.int32) - decoded_frame.astype(np.int32))
            max_diff = np.max(diff)
            mean_diff = np.mean(diff)
            print(f"    Lossless: ❌ Différences détectées")
            print(f"      Max diff: {max_diff}")
            print(f"      Mean diff: {mean_diff:.2f}")
            lossless = False
        
        return {
            'method': 'HCV16 Basic',
            'original_size': original_size,
            'compressed_size': file_size,
            'ratio': ratio,
            'saving': saving,
            'time': compression_time,
            'speed_mbps': original_size/1024/1024/max(0.001, compression_time),
            'psnr': psnr_val,
            'ssim': ssim_val,
            'lossless': lossless
        }
        
    except Exception as e:
        print(f"\n[-] Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_sequence_compression():
    """Test compression de séquence"""
    print("\n" + "="*80)
    print("TEST 2: COMPRESSION DE SÉQUENCE (10 frames)")
    print("="*80)
    
    # Créer séquence
    print("\n[*] Création séquence de test (10 frames, 640x480, 12 bits)...")
    frames = make_sequence(n=10, h=480, w=640, bits=12, fps=24, noise_pct=0.01)
    
    total_original = sum(f.nbytes for f in frames)
    print(f"[+] Séquence créée: {len(frames)} frames, total {total_original:,} bytes")
    
    # Encoder
    print("\n[*] Compression séquence en cours...")
    output_file = "test_hcv16_sequence.hcv16"
    
    start_time = time.time()
    try:
        writer = HCV16Writer(output_file, mode='GRAIN_SYNTH',
                            bit_depth=12, width=640, height=480, fps=(24, 1))
        
        for i, frame in enumerate(frames):
            writer.add_frame(frame, i)
        
        file_size = writer.finalize()
        compression_time = time.time() - start_time
        
        # Calculer métriques
        ratio = total_original / max(1, file_size)
        saving = (1 - file_size / total_original) * 100
        
        print(f"\n[+] RÉSULTATS COMPRESSION SÉQUENCE:")
        print(f"    Taille originale: {total_original:,} bytes ({total_original/1024/1024:.2f} MB)")
        print(f"    Taille compressée: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        print(f"    Ratio: {ratio:.2f}:1")
        print(f"    Économie: {saving:.2f}%")
        print(f"    Temps total: {compression_time:.3f}s")
        print(f"    Temps/frame: {compression_time/len(frames)*1000:.1f}ms")
        print(f"    Vitesse: {total_original/1024/1024/max(0.001, compression_time):.2f} MB/s")
        
        # Décoder et vérifier
        print(f"\n[*] Décodage séquence...")
        reader = HCV16Reader(output_file)
        reader.open()
        
        all_lossless = True
        total_psnr = 0
        total_ssim = 0
        
        for i in range(len(frames)):
            decoded = reader.decode_frame(i)
            psnr_val = psnr(frames[i], decoded, maxval=4095)
            ssim_val = ssim(frames[i], decoded, maxval=4095)
            
            total_psnr += psnr_val
            total_ssim += ssim_val
            
            if not np.array_equal(frames[i], decoded):
                all_lossless = False
        
        avg_psnr = total_psnr / len(frames)
        avg_ssim = total_ssim / len(frames)
        
        print(f"    PSNR moyen: {avg_psnr:.2f} dB")
        print(f"    SSIM moyen: {avg_ssim:.6f}")
        print(f"    Lossless: {'✅' if all_lossless else '❌'}")
        
        return {
            'method': 'HCV16 Sequence',
            'frames': len(frames),
            'original_size': total_original,
            'compressed_size': file_size,
            'ratio': ratio,
            'saving': saving,
            'time': compression_time,
            'time_per_frame_ms': compression_time/len(frames)*1000,
            'speed_mbps': total_original/1024/1024/max(0.001, compression_time),
            'psnr': avg_psnr,
            'ssim': avg_ssim,
            'lossless': all_lossless
        }
        
    except Exception as e:
        print(f"\n[-] Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_different_modes():
    """Test différents modes de compression"""
    print("\n" + "="*80)
    print("TEST 3: COMPARAISON DES MODES")
    print("="*80)
    
    frame = make_frame(h=480, w=640, bits=12, noise_pct=0.01)
    original_size = frame.nbytes
    
    modes = ['LOSSLESS', 'GRAIN_SYNTH', 'SIGNAL_ONLY']
    results = []
    
    for mode in modes:
        print(f"\n[*] Test mode: {mode}")
        
        output_file = f"test_hcv16_{mode}.hcv16"
        
        start_time = time.time()
        try:
            writer = HCV16Writer(output_file, mode=mode,
                                bit_depth=12, width=640, height=480, fps=(24, 1))
            writer.add_frame(frame, 0)
            file_size = writer.finalize()
            compression_time = time.time() - start_time
            
            ratio = original_size / max(1, file_size)
            saving = (1 - file_size / original_size) * 100
            
            # Décoder
            reader = HCV16Reader(output_file)
            reader.open()
            decoded = reader.decode_frame(0)
            
            psnr_val = psnr(frame, decoded, maxval=4095)
            ssim_val = ssim(frame, decoded, maxval=4095)
            lossless = np.array_equal(frame, decoded)
            
            result = {
                'mode': mode,
                'original_size': original_size,
                'compressed_size': file_size,
                'ratio': ratio,
                'saving': saving,
                'time_ms': compression_time * 1000,
                'psnr': psnr_val,
                'ssim': ssim_val,
                'lossless': lossless
            }
            results.append(result)
            
            print(f"    Ratio: {ratio:.2f}:1")
            print(f"    Économie: {saving:.2f}%")
            print(f"    PSNR: {psnr_val:.2f} dB")
            print(f"    SSIM: {ssim_val:.6f}")
            print(f"    Lossless: {'✅' if lossless else '❌'}")
            
        except Exception as e:
            print(f"    Erreur: {e}")
    
    # Tableau comparatif
    if results:
        print("\n" + "="*80)
        print("RÉSUMÉ COMPARATIF - MODES")
        print("="*80)
        print(f"{'Mode':<15} {'Ratio':<10} {'Économie':<10} {'PSNR':<10} {'SSIM':<12} {'Lossless':<10}")
        print("-" * 80)
        for r in results:
            print(f"{r['mode']:<15} {r['ratio']:>8.2f}:1 {r['saving']:>8.2f}% {r['psnr']:>8.2f} dB {r['ssim']:>10.6f} {'✅' if r['lossless'] else '❌'}")
    
    return results

def test_different_resolutions():
    """Test différentes résolutions"""
    print("\n" + "="*80)
    print("TEST 4: DIFFÉRENTES RÉSOLUTIONS")
    print("="*80)
    
    resolutions = [
        (320, 240, "QVGA"),
        (640, 480, "VGA"),
        (1280, 720, "HD"),
        (1920, 1080, "Full HD"),
    ]
    
    results = []
    
    for width, height, label in resolutions:
        print(f"\n[*] Test {label} ({width}x{height})...")
        
        frame = make_frame(h=height, w=width, bits=12, noise_pct=0.01)
        original_size = frame.nbytes
        
        output_file = f"test_hcv16_{label}.hcv16"
        
        start_time = time.time()
        try:
            writer = HCV16Writer(output_file, mode='GRAIN_SYNTH',
                                bit_depth=12, width=width, height=height, fps=(24, 1))
            writer.add_frame(frame, 0)
            file_size = writer.finalize()
            compression_time = time.time() - start_time
            
            ratio = original_size / max(1, file_size)
            saving = (1 - file_size / original_size) * 100
            
            # Décoder
            reader = HCV16Reader(output_file)
            reader.open()
            decoded = reader.decode_frame(0)
            
            psnr_val = psnr(frame, decoded, maxval=4095)
            ssim_val = ssim(frame, decoded, maxval=4095)
            lossless = np.array_equal(frame, decoded)
            
            result = {
                'label': label,
                'dimensions': f"{width}x{height}",
                'original_mb': original_size / 1024 / 1024,
                'compressed_mb': file_size / 1024 / 1024,
                'ratio': ratio,
                'saving': saving,
                'time_ms': compression_time * 1000,
                'psnr': psnr_val,
                'ssim': ssim_val,
                'lossless': lossless
            }
            results.append(result)
            
            print(f"    Original: {result['original_mb']:.2f} MB")
            print(f"    Compressé: {result['compressed_mb']:.2f} MB")
            print(f"    Ratio: {result['ratio']:.2f}:1")
            print(f"    Économie: {result['saving']:.2f}%")
            print(f"    Temps: {result['time_ms']:.1f}ms")
            print(f"    Lossless: {'✅' if lossless else '❌'}")
            
        except Exception as e:
            print(f"    Erreur: {e}")
    
    # Tableau comparatif
    if results:
        print("\n" + "="*80)
        print("RÉSUMÉ COMPARATIF - RÉSOLUTIONS")
        print("="*80)
        print(f"{'Résolution':<15} {'Original':<12} {'Compressé':<12} {'Ratio':<10} {'Économie':<10} {'Lossless':<10}")
        print("-" * 90)
        for r in results:
            print(f"{r['label']:<15} {r['original_mb']:>10.2f} MB {r['compressed_mb']:>10.2f} MB {r['ratio']:>8.2f}:1 {r['saving']:>8.2f}% {'✅' if r['lossless'] else '❌'}")
    
    return results

if __name__ == "__main__":
    try:
        # Test basique
        result_basic = test_basic_compression()
        
        # Test séquence
        result_sequence = test_sequence_compression()
        
        # Test modes
        results_modes = test_different_modes()
        
        # Test résolutions
        results_resolutions = test_different_resolutions()
        
        # Résumé final
        print("\n" + "="*80)
        print("RÉSUMÉ FINAL - HARMONIC CODEC V16")
        print("="*80)
        
        print(f"\n[+] Tests complétés avec succès!")
        
        if result_basic:
            print(f"\n[+] RÉSULTATS PRINCIPAUX (1 frame):")
            print(f"    Ratio: {result_basic['ratio']:.2f}:1")
            print(f"    Économie: {result_basic['saving']:.2f}%")
            print(f"    PSNR: {result_basic['psnr']:.2f} dB")
            print(f"    SSIM: {result_basic['ssim']:.6f}")
            print(f"    Lossless: {'✅' if result_basic['lossless'] else '❌'}")
        
        if result_sequence:
            print(f"\n[+] RÉSULTATS SÉQUENCE (10 frames):")
            print(f"    Ratio: {result_sequence['ratio']:.2f}:1")
            print(f"    Économie: {result_sequence['saving']:.2f}%")
            print(f"    Temps/frame: {result_sequence['time_per_frame_ms']:.1f}ms")
            print(f"    Vitesse: {result_sequence['speed_mbps']:.2f} MB/s")
            print(f"    Lossless: {'✅' if result_sequence['lossless'] else '❌'}")
        
        # Sauvegarder résultats
        summary = {
            'test_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'basic_test': result_basic,
            'sequence_test': result_sequence,
            'modes_comparison': results_modes,
            'resolutions_comparison': results_resolutions
        }
        
        with open('harmonic_codec_v16_test_results.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"\n[+] Résultats sauvegardés: harmonic_codec_v16_test_results.json")
        
    except Exception as e:
        print(f"\nErreur: {e}")
        import traceback
        traceback.print_exc()
