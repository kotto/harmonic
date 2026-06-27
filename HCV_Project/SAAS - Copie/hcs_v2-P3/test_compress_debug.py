#!/usr/bin/env python3
"""Test pour debuguer la compression"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Import des modules...")
    from core.hybrid_compressor import HybridCompressor
    from PIL import Image
    import numpy as np
    import io
    print("OK - Modules importés")
    
    # Créer une image de test
    print("\nCréation image test...")
    img_array = np.random.rand(100, 100, 3).astype(np.float32)
    print(f"Image shape: {img_array.shape}")
    
    # Compresser
    print("\nCompression...")
    compressor = HybridCompressor(k_factor=0.02, webp_quality=95)
    compressed_data, metadata = compressor.compress_image(img_array)
    
    print(f"\n=== RÉSULTATS ===")
    print(f"Type: {type(compressed_data)}")
    print(f"Taille: {len(compressed_data)} bytes")
    print(f"Premiers 30 bytes: {compressed_data[:30]}")
    print(f"Header (4 bytes): {compressed_data[:4]}")
    
    # Vérifier format
    if compressed_data[:4] == b'RIFF':
        print("Header RIFF détecté (WebP)")
    elif compressed_data[:4] == b'\x89PNG':
        print("Header PNG détecté")
    elif compressed_data[:2] == b'\xff\xd8':
        print("Header JPEG détecté")
    else:
        print(f"Header inconnu: {compressed_data[:10]}")
    
    # Essayer de charger
    print("\nTentative chargement...")
    try:
        img = Image.open(io.BytesIO(compressed_data))
        print(f"Format détecté: {img.format}")
        print(f"Taille: {img.size}")
        print(f"Mode: {img.mode}")
    except Exception as e:
        print(f"ERREUR chargement: {e}")
        
except Exception as e:
    print(f"ERREUR: {e}")
    import traceback
    traceback.print_exc()
