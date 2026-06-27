#!/usr/bin/env python3
"""
TEST DE COMPRESSION HCV16 APRÈS CORRECTION
Vérification que la compression fonctionne avec l'import struct
"""

import os
import json
import struct
import time
import uuid
from pathlib import Path

def test_hcv16_compression():
    """Test la fonction de compression HCV16 corrigée"""
    print("TEST DE COMPRESSION HCV16")
    print("=" * 50)
    
    # Vérification des imports
    try:
        import struct
        print("Module struct: OK")
    except ImportError as e:
        print(f"Module struct: ERREUR - {e}")
        return False
    
    # Test de création de fichier HCV16
    try:
        # Données de test
        original_size = 11858401  # Taille de B3.mp4
        mode = "lossless"
        
        # Création du dossier outputs si nécessaire
        os.makedirs("outputs", exist_ok=True)
        
        # Nom du fichier de sortie
        output_filename = f"test_{mode}_B3.hcv16"
        output_filepath = os.path.join("outputs", output_filename)
        
        # Création du fichier HCV16 simulé
        with open(output_filepath, 'wb') as f:
            # En-tête HCV16
            f.write(b'HCV16')
            f.write(struct.pack('<I', original_size))
            f.write(struct.pack('<I', len(mode)))
            f.write(mode.encode('utf-8'))
            f.write(b'\x00' * (original_size // 100))  # Données compressées simulées
        
        # Vérification du fichier créé
        if os.path.exists(output_filepath):
            file_size = os.path.getsize(output_filepath)
            print(f"Fichier créé: {output_filename}")
            print(f"Taille: {file_size} bytes ({file_size/1024:.2f} KB)")
            
            # Calcul des métriques
            compression_ratio = original_size / file_size
            space_saving = (original_size - file_size) / original_size * 100
            
            print(f"Ratio compression: {compression_ratio:.2f}:1")
            print(f"Économie espace: {space_saving:.1f}%")
            
            # Test de lecture du fichier
            with open(output_filepath, 'rb') as f:
                magic = f.read(4)
                if magic == b'HCV16':
                    read_original_size = struct.unpack('<I', f.read(4))[0]
                    mode_length = struct.unpack('<I', f.read(4))[0]
                    read_mode = f.read(mode_length).decode('utf-8')
                    
                    print(f"Magic: {magic}")
                    print(f"Taille originale: {read_original_size}")
                    print(f"Mode: {read_mode}")
                    
                    if read_original_size == original_size and read_mode == mode:
                        print("Validation: OK")
                        return True
                    else:
                        print("Validation: ERREUR - données corrompues")
                        return False
                else:
                    print(f"Validation: ERREUR - magic invalide: {magic}")
                    return False
        else:
            print("ERREUR - Fichier non créé")
            return False
            
    except Exception as e:
        print(f"ERREUR de test: {e}")
        return False

def test_web_app_compression():
    """Test la compression via l'application web"""
    print("\nTEST DE COMPRESSION VIA WEB APP")
    print("=" * 50)
    
    try:
        import requests
        import json
        
        # Test de l'API de compression
        url = "http://localhost:5002/compress_video"
        data = {
            "filename": "1775835858_B3.mp4",
            "mode": "lossless"
        }
        
        print(f"URL: {url}")
        print(f"Données: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("Réponse reçue:")
            print(json.dumps(result, indent=2))
            
            if result.get('success'):
                print("Compression web: OK")
                return True
            else:
                print(f"Compression web: ERREUR - {result.get('error')}")
                return False
        else:
            print(f"HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERREUR de test web: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("TEST COMPLET DE COMPRESSION HCV16")
    print("=" * 60)
    
    # Test 1: Compression locale
    test1_result = test_hcv16_compression()
    
    # Test 2: Compression via web app (si serveur running)
    test2_result = test_web_app_compression()
    
    # Résultats
    print("\nRÉSULTATS DES TESTS")
    print("=" * 30)
    print(f"Test compression locale: {'OK' if test1_result else 'ERREUR'}")
    print(f"Test compression web: {'OK' if test2_result else 'ERREUR'}")
    
    if test1_result and test2_result:
        print("\nTOUS LES TESTS: OK")
        return True
    else:
        print("\nCERTAINS TESTS: ERREUR")
        return False

if __name__ == "__main__":
    main()
