#!/usr/bin/env python3
"""
VÉRIFICATION DES CALCULS HCS CORE ENGINE
Test honnête avec données réalistes (pas juste des gradients)
"""

import sys
import os
import time
import struct
import zlib
import json
import random

sys.path.insert(0, 'COMPRESSION-CAMERA/VERSION-SECURISEE')

from hcs_api_server import HCSCoreEngine

def create_realistic_data(width, height, noise_level=0.3):
    """
    Crée des données réalistes simulant une vraie image.
    Mélange gradient + bruit + zones de détail.
    """
    data = bytearray()
    random.seed(42)  # Reproductible
    
    for y in range(height):
        for x in range(width):
            # Base: gradient diagonal
            base = int(65535 * (x + y) / (width + height))
            
            # Ajouter du bruit réaliste (simulant texture photo)
            noise = int(random.gauss(0, 65535 * noise_level))
            
            # Zones de détail (bords, textures)
            edge = 0
            if 100 < x < 110 or 200 < y < 210:
                edge = random.randint(-5000, 5000)
            
            val = max(0, min(65535, base + noise + edge))
            data.extend(struct.pack('<H', val))
    
    return bytes(data)

def verify_lossless(original, compressed, width, height):
    """Vérifie que la décompression est parfaitement lossless"""
    decompressed = HCSCoreEngine.delta_h_decode(compressed, width, height)
    
    if decompressed == original:
        return True, 0
    
    # Compter les différences
    orig_vals = struct.unpack(f'<{width*height}H', original)
    dec_vals = struct.unpack(f'<{width*height}H', decompressed)
    
    diffs = sum(1 for a, b in zip(orig_vals, dec_vals) if a != b)
    max_diff = max(abs(a - b) for a, b in zip(orig_vals, dec_vals))
    
    return False, {'diff_count': diffs, 'max_diff': max_diff, 'total_pixels': width*height}

def test_realistic():
    """Test avec données réalistes"""
    print("="*80)
    print("VÉRIFICATION DES CALCULS - DONNÉES RÉALISTES")
    print("="*80)
    
    width, height = 640, 480
    
    noise_levels = [
        (0.0, "Gradient pur (0% bruit)"),
        (0.05, "Très peu de bruit (5%)"),
        (0.10, "Bruit léger (10%)"),
        (0.20, "Bruit modéré (20%)"),
        (0.30, "Bruit réaliste photo (30%)"),
        (0.50, "Bruit fort (50%)"),
    ]
    
    results = []
    
    for noise, description in noise_levels:
        print(f"\n[*] Test: {description}")
        
        # Créer données
        original = create_realistic_data(width, height, noise)
        original_size = len(original)
        
        # Compression
        start = time.time()
        compressed = HCSCoreEngine.delta_h_encode(original, width, height)
        comp_time = time.time() - start
        
        compressed_size = len(compressed)
        ratio = original_size / max(1, compressed_size)
        saving = (1 - compressed_size / original_size) * 100
        
        # Vérification lossless
        is_lossless, diff_info = verify_lossless(original, compressed, width, height)
        
        result = {
            'noise': noise,
            'description': description,
            'original_bytes': original_size,
            'compressed_bytes': compressed_size,
            'ratio': ratio,
            'saving': saving,
            'time_ms': comp_time * 1000,
            'lossless': is_lossless
        }
        results.append(result)
        
        print(f"    Original:   {original_size:>10,} bytes ({original_size/1024:.1f} KB)")
        print(f"    Compressé:  {compressed_size:>10,} bytes ({compressed_size/1024:.1f} KB)")
        print(f"    Ratio:      {ratio:.2f}:1")
        print(f"    Économie:   {saving:.2f}%")
        print(f"    Temps:      {comp_time*1000:.1f}ms")
        print(f"    Lossless:   {'✅' if is_lossless else '❌'}")
        if not is_lossless:
            print(f"    Erreurs:    {diff_info}")
    
    return results

def test_real_photo_simulation():
    """Simule une vraie photo avec haute entropie"""
    print("\n" + "="*80)
    print("VÉRIFICATION - SIMULATION PHOTO RÉELLE")
    print("="*80)
    
    width, height = 640, 480
    random.seed(123)
    
    # Simuler 3 canaux R, G, B comme une vraie photo
    channels = {}
    for ch_name in ['R', 'G', 'B']:
        data = bytearray()
        for y in range(height):
            for x in range(width):
                # Mélange complexe simulant une photo
                base = int(32768 + 16384 * (
                    0.3 * (x / width) +
                    0.3 * (y / height) +
                    0.2 * ((x * y) % 256) / 256 +
                    0.2 * random.random()
                ))
                # Bruit gaussien réaliste
                noise = int(random.gauss(0, 3000))
                val = max(0, min(65535, base + noise))
                data.extend(struct.pack('<H', val))
        channels[ch_name] = bytes(data)
    
    # Compresser chaque canal
    total_original = 0
    total_compressed = 0
    all_lossless = True
    
    print(f"\n[*] Compression 3 canaux (R, G, B) - {width}x{height}")
    
    for ch_name, ch_data in channels.items():
        original_size = len(ch_data)
        
        start = time.time()
        compressed = HCSCoreEngine.delta_h_encode(ch_data, width, height)
        comp_time = time.time() - start
        
        compressed_size = len(compressed)
        ratio = original_size / max(1, compressed_size)
        
        # Vérification lossless
        is_lossless, _ = verify_lossless(ch_data, compressed, width, height)
        all_lossless = all_lossless and is_lossless
        
        total_original += original_size
        total_compressed += compressed_size
        
        print(f"    Canal {ch_name}: {original_size/1024:.1f} KB → {compressed_size/1024:.1f} KB (ratio {ratio:.2f}:1) {'✅' if is_lossless else '❌'} {comp_time*1000:.1f}ms")
    
    total_ratio = total_original / max(1, total_compressed)
    total_saving = (1 - total_compressed / total_original) * 100
    
    print(f"\n[+] TOTAL 3 CANAUX:")
    print(f"    Original:   {total_original:>10,} bytes ({total_original/1024/1024:.2f} MB)")
    print(f"    Compressé:  {total_compressed:>10,} bytes ({total_compressed/1024/1024:.2f} MB)")
    print(f"    Ratio:      {total_ratio:.2f}:1")
    print(f"    Économie:   {total_saving:.2f}%")
    print(f"    Lossless:   {'✅' if all_lossless else '❌'}")
    
    return {
        'total_original': total_original,
        'total_compressed': total_compressed,
        'ratio': total_ratio,
        'saving': total_saving,
        'lossless': all_lossless
    }

def test_worst_case():
    """Test pire cas: données purement aléatoires"""
    print("\n" + "="*80)
    print("VÉRIFICATION - PIRE CAS (DONNÉES ALÉATOIRES)")
    print("="*80)
    
    width, height = 640, 480
    random.seed(999)
    
    # Données purement aléatoires
    data = bytearray()
    for _ in range(width * height):
        data.extend(struct.pack('<H', random.randint(0, 65535)))
    original = bytes(data)
    
    original_size = len(original)
    
    start = time.time()
    compressed = HCSCoreEngine.delta_h_encode(original, width, height)
    comp_time = time.time() - start
    
    compressed_size = len(compressed)
    ratio = original_size / max(1, compressed_size)
    saving = (1 - compressed_size / original_size) * 100
    
    is_lossless, diff_info = verify_lossless(original, compressed, width, height)
    
    print(f"\n[*] Données 100% aléatoires ({width}x{height})")
    print(f"    Original:   {original_size:>10,} bytes ({original_size/1024:.1f} KB)")
    print(f"    Compressé:  {compressed_size:>10,} bytes ({compressed_size/1024:.1f} KB)")
    print(f"    Ratio:      {ratio:.2f}:1")
    print(f"    Économie:   {saving:.2f}%")
    print(f"    Temps:      {comp_time*1000:.1f}ms")
    print(f"    Lossless:   {'✅' if is_lossless else '❌'}")
    
    return {
        'original': original_size,
        'compressed': compressed_size,
        'ratio': ratio,
        'saving': saving,
        'lossless': is_lossless
    }

if __name__ == "__main__":
    try:
        # Test réaliste avec différents niveaux de bruit
        results_noise = test_realistic()
        
        # Test simulation photo réelle
        result_photo = test_real_photo_simulation()
        
        # Test pire cas
        result_worst = test_worst_case()
        
        # Résumé final honnête
        print("\n" + "="*80)
        print("RÉSUMÉ FINAL - VÉRIFICATION HONNÊTE")
        print("="*80)
        
        print(f"\n{'Type de contenu':<35} {'Ratio':<12} {'Économie':<12} {'Lossless':<10}")
        print("-" * 75)
        for r in results_noise:
            print(f"{r['description']:<35} {r['ratio']:>8.2f}:1  {r['saving']:>8.2f}%   {'✅' if r['lossless'] else '❌'}")
        
        print(f"{'Simulation photo réelle (3ch)':<35} {result_photo['ratio']:>8.2f}:1  {result_photo['saving']:>8.2f}%   {'✅' if result_photo['lossless'] else '❌'}")
        print(f"{'Pire cas (100% aléatoire)':<35} {result_worst['ratio']:>8.2f}:1  {result_worst['saving']:>8.2f}%   {'✅' if result_worst['lossless'] else '❌'}")
        
        # Sauvegarder
        summary = {
            'test_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'noise_tests': results_noise,
            'photo_simulation': result_photo,
            'worst_case': result_worst
        }
        with open('hcs_verification_results.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"\n[+] Résultats sauvegardés: hcs_verification_results.json")
        
    except Exception as e:
        print(f"\nErreur: {e}")
        import traceback
        traceback.print_exc()
