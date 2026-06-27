#!/usr/bin/env python3
"""
TEST SIMPLIFIÉ DU SERVEUR HCS API
Teste les algorithmes de compression du HCS Core Engine sans dépendances lourdes
"""

import sys
import os
import time
import numpy as np
import cv2
import struct
import zlib
import json

sys.path.insert(0, 'COMPRESSION-CAMERA/VERSION-SECURISEE')

# Importer seulement les méthodes statiques du HCS
from hcs_api_server import HCSCoreEngine

def create_test_image(width=640, height=480, filename="test_hcs_image.jpg"):
    """Crée une image de test"""
    print(f"[*] Création image de test: {width}x{height}")
    
    # Créer image avec contenu varié
    image = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Gradient horizontal
    for x in range(width):
        image[:, x] = [int(255 * x / width), 128, 255 - int(255 * x / width)]
    
    # Ajouter du bruit
    noise = np.random.randint(0, 30, (height, width, 3), dtype=np.uint8)
    image = cv2.addWeighted(image, 0.8, noise, 0.2, 0)
    
    # Ajouter des formes
    cv2.rectangle(image, (100, 100), (500, 500), (0, 255, 0), 3)
    cv2.circle(image, (width//2, height//2), 100, (255, 0, 0), 3)
    cv2.putText(image, "HCS TEST", (width//2-100, height//2), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
    
    cv2.imwrite(filename, image)
    file_size = os.path.getsize(filename)
    print(f"[+] Image créée: {filename} ({file_size:,} bytes)")
    return filename, file_size

def prepare_frame_data(image_path, width, height):
    """Prépare les données de frame pour le HCS"""
    # Charger l'image
    img = cv2.imread(image_path)
    img = cv2.resize(img, (width, height))
    
    # Convertir en RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Convertir en 16-bit
    img_16 = img_rgb.astype(np.uint16) * 257  # 8-bit to 16-bit
    
    # Extraire canaux
    R = img_16[:, :, 0].tobytes()
    G = img_16[:, :, 1].tobytes()
    B = img_16[:, :, 2].tobytes()
    Y = img_16[:, :, 0].tobytes()  # Utiliser R comme Y pour simplifier
    
    return {
        'R': R,
        'G': G,
        'B': B,
        'Y': Y
    }

def test_delta_h_compression():
    """Test de compression Delta-H"""
    print("\n" + "="*80)
    print("TEST 1: COMPRESSION DELTA-H (HCS Core)")
    print("="*80)
    
    # Créer image de test
    image_file, original_size = create_test_image(640, 480, "test_hcs_delta.jpg")
    
    # Préparer données
    frame_data = prepare_frame_data(image_file, 640, 480)
    
    print("\n[*] Compression Delta-H en cours...")
    start_time = time.time()
    
    try:
        # Compresser chaque canal
        cR = HCSCoreEngine.delta_h_encode(frame_data['R'], 640, 480)
        cG = HCSCoreEngine.delta_h_encode(frame_data['G'], 640, 480)
        cB = HCSCoreEngine.delta_h_encode(frame_data['B'], 640, 480)
        
        compression_time = time.time() - start_time
        
        # Calculer tailles
        original_channel_size = 640 * 480 * 2  # 16-bit
        compressed_size = len(cR) + len(cG) + len(cB)
        total_original = original_channel_size * 3
        
        ratio = total_original / max(1, compressed_size)
        saving = (1 - compressed_size/total_original) * 100
        
        print(f"\n[+] RÉSULTATS DELTA-H:")
        print(f"    Taille originale (3 canaux): {total_original:,} bytes ({total_original/1024/1024:.2f} MB)")
        print(f"    Taille compressée: {compressed_size:,} bytes ({compressed_size/1024/1024:.2f} MB)")
        print(f"    Ratio: {ratio:.2f}:1")
        print(f"    Économie: {saving:.2f}%")
        print(f"    Temps: {compression_time:.3f}s")
        print(f"    Vitesse: {total_original/1024/1024/max(0.001, compression_time):.2f} MB/s")
        
        # Vérifier décompression
        print(f"\n[*] Vérification décompression...")
        dR = HCSCoreEngine.delta_h_decode(cR, 640, 480)
        dG = HCSCoreEngine.delta_h_decode(cG, 640, 480)
        dB = HCSCoreEngine.delta_h_decode(cB, 640, 480)
        
        # Vérifier intégrité
        if dR == frame_data['R'] and dG == frame_data['G'] and dB == frame_data['B']:
            print(f"[+] Décompression: OK (lossless)")
            lossless = True
        else:
            print(f"[-] Décompression: ERREUR (données corrompues)")
            lossless = False
        
        return {
            'method': 'Delta-H',
            'original_size': total_original,
            'compressed_size': compressed_size,
            'ratio': ratio,
            'saving': saving,
            'time': compression_time,
            'speed_mbps': total_original/1024/1024/max(0.001, compression_time),
            'lossless': lossless
        }
        
    except Exception as e:
        print(f"\n[-] Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_different_resolutions():
    """Test avec différentes résolutions"""
    print("\n" + "="*80)
    print("TEST 2: COMPRESSION HCS AVEC DIFFÉRENTES RÉSOLUTIONS")
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
        
        image_file, _ = create_test_image(width, height, f"test_hcs_{label}.jpg")
        frame_data = prepare_frame_data(image_file, width, height)
        
        start_time = time.time()
        try:
            # Compression Delta-H
            cR = HCSCoreEngine.delta_h_encode(frame_data['R'], width, height)
            cG = HCSCoreEngine.delta_h_encode(frame_data['G'], width, height)
            cB = HCSCoreEngine.delta_h_encode(frame_data['B'], width, height)
            
            compression_time = time.time() - start_time
            
            original_size = width * height * 2 * 3
            compressed_size = len(cR) + len(cG) + len(cB)
            
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

def test_compression_efficiency():
    """Test d'efficacité de compression"""
    print("\n" + "="*80)
    print("TEST 3: ANALYSE D'EFFICACITÉ")
    print("="*80)
    
    # Créer images avec différents types de contenu
    test_cases = [
        ("gradient", "Image avec gradient lisse"),
        ("noise", "Image avec bruit aléatoire"),
        ("mixed", "Image mixte (gradient + bruit + formes)")
    ]
    
    results = []
    
    for case_type, description in test_cases:
        print(f"\n[*] Test: {description}")
        
        # Créer image spécifique
        width, height = 640, 480
        image = np.zeros((height, width, 3), dtype=np.uint8)
        
        if case_type == "gradient":
            # Gradient lisse
            for x in range(width):
                image[:, x] = [int(255 * x / width), 128, 255 - int(255 * x / width)]
        
        elif case_type == "noise":
            # Bruit aléatoire
            image = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        
        else:  # mixed
            # Gradient + bruit + formes
            for x in range(width):
                image[:, x] = [int(255 * x / width), 128, 255 - int(255 * x / width)]
            noise = np.random.randint(0, 30, (height, width, 3), dtype=np.uint8)
            image = cv2.addWeighted(image, 0.8, noise, 0.2, 0)
            cv2.rectangle(image, (100, 100), (500, 500), (0, 255, 0), 3)
            cv2.circle(image, (width//2, height//2), 100, (255, 0, 0), 3)
        
        # Sauvegarder
        filename = f"test_hcs_{case_type}.jpg"
        cv2.imwrite(filename, image)
        
        # Préparer données
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        img_16 = img_rgb.astype(np.uint16) * 257
        R = img_16[:, :, 0].tobytes()
        G = img_16[:, :, 1].tobytes()
        B = img_16[:, :, 2].tobytes()
        
        # Compresser
        start_time = time.time()
        cR = HCSCoreEngine.delta_h_encode(R, width, height)
        cG = HCSCoreEngine.delta_h_encode(G, width, height)
        cB = HCSCoreEngine.delta_h_encode(B, width, height)
        compression_time = time.time() - start_time
        
        original_size = width * height * 2 * 3
        compressed_size = len(cR) + len(cG) + len(cB)
        
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
    
    # Tableau récapitulatif
    if results:
        print("\n" + "="*80)
        print("RÉSUMÉ - EFFICACITÉ PAR TYPE DE CONTENU")
        print("="*80)
        print(f"{'Type':<15} {'Description':<30} {'Ratio':<10} {'Économie':<10}")
        print("-" * 70)
        for r in results:
            print(f"{r['type']:<15} {r['description']:<30} {r['ratio']:>8.2f}:1 {r['saving']:>8.2f}%")
    
    return results

if __name__ == "__main__":
    try:
        # Test Delta-H
        result_delta = test_delta_h_compression()
        
        # Test différentes résolutions
        results_sizes = test_different_resolutions()
        
        # Test efficacité
        results_efficiency = test_compression_efficiency()
        
        # Résumé final
        print("\n" + "="*80)
        print("RÉSUMÉ FINAL - HCS API SERVER")
        print("="*80)
        
        print(f"\n[+] Tests complétés avec succès!")
        
        if result_delta:
            print(f"\n[+] RÉSULTATS PRINCIPAUX (Delta-H):")
            print(f"    Ratio: {result_delta['ratio']:.2f}:1")
            print(f"    Économie: {result_delta['saving']:.2f}%")
            print(f"    Vitesse: {result_delta['speed_mbps']:.2f} MB/s")
            print(f"    Lossless: {result_delta['lossless']}")
        
        # Sauvegarder les résultats
        summary = {
            'test_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'delta_h': result_delta,
            'multi_resolution_results': results_sizes,
            'efficiency_results': results_efficiency
        }
        
        with open('hcs_api_server_test_results.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"\n[+] Résultats sauvegardés: hcs_api_server_test_results.json")
        
    except Exception as e:
        print(f"\nErreur: {e}")
        import traceback
        traceback.print_exc()
