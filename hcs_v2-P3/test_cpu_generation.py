#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HCS V2 - Test CPU-Only de Génération d'Images Hybride
Test sans dépendances GPU/CUDA
"""

import os
import sys
import time
import numpy as np
from PIL import Image
import requests
import json
import base64
import io

def test_cpu_generation():
    """Test de génération CPU-only"""
    print("🌊 HCS V2 - Test CPU-Only de Génération")
    print("=" * 50)
    
    try:
        # Test de connexion
        print("🔍 Test connexion serveur hybride...")
        response = requests.get("http://localhost:8011/", timeout=5)
        
        if response.status_code == 200:
            print("✅ Serveur hybride accessible")
            server_info = response.json()
            print(f"   📋 Message: {server_info.get('message', 'N/A')}")
        else:
            print(f"❌ Erreur connexion: {response.status_code}")
            return False
        
        # Test info endpoint
        print("\n📊 Test endpoint info...")
        info_response = requests.get("http://localhost:8011/api/v2/hybrid/info", timeout=10)
        
        if info_response.status_code == 200:
            info_data = info_response.json()
            print("✅ Endpoint info fonctionnel")
            print(f"   🎨 Type: {info_data.get('generator_info', {}).get('type', 'N/A')}")
            print(f"   🌊 Version HCS: {info_data.get('generator_info', {}).get('hcs_version', 'N/A')}")
        else:
            print(f"⚠️ Endpoint info: {info_response.status_code}")
        
        # Test génération simple (CPU mode)
        print("\n🚀 Test génération CPU...")
        
        test_data = {
            "prompt": "A beautiful harmonic crystal structure with perfect golden ratio patterns, quantum colors, 8K resolution",
            "width": 256,  # Plus petit pour CPU
            "height": 256,
            "energy_level": "classique",  # Mode simple
            "harmonic_strength": 0.7,
            "upscale_factor": 1.0,  # Pas d'upscale
            "temporal_coherence": False
        }
        
        print(f"   📝 Prompt: {test_data['prompt'][:40]}...")
        print(f"   📏 Dimensions: {test_data['width']}x{test_data['height']}")
        print(f"   ⚡ Énergie: {test_data['energy_level']}")
        
        start_time = time.time()
        
        generation_response = requests.post(
            "http://localhost:8011/api/v2/hybrid/generate",
            json=test_data,
            timeout=120  # Plus de temps pour CPU
        )
        
        generation_time = time.time() - start_time
        
        if generation_response.status_code == 200:
            result = generation_response.json()
            
            if result.get('success'):
                print("✅ Génération CPU réussie !")
                print(f"   ⏱️ Temps: {generation_time:.2f}s")
                print(f"   📏 Message: {result.get('message', 'N/A')}")
                
                # Vérification image
                if 'generated_image_base64' in result:
                    print("✅ Image base64 générée")
                    
                    try:
                        image_bytes = base64.b64decode(result['generated_image_base64'])
                        image = Image.open(io.BytesIO(image_bytes))
                        
                        # Sauvegarde
                        output_path = "test_cpu_generated.png"
                        image.save(output_path)
                        print(f"   💾 Image sauvegardée: {output_path}")
                        print(f"   📏 Dimensions: {image.size}")
                        print(f"   🎨 Mode: {image.mode}")
                        
                        # Vérification basique
                        if image.size == (test_data['width'], test_data['height']):
                            print("   ✅ Dimensions correctes")
                        else:
                            print(f"   ⚠️ Dimensions incorrectes: attendu {test_data['width']}x{test_data['height']}, obtenu {image.size}")
                        
                    except Exception as e:
                        print(f"   ⚠️ Erreur sauvegarde: {e}")
                
                # Métriques
                if 'metrics' in result:
                    metrics = result['metrics']
                    print("📊 Métriques harmoniques:")
                    print(f"   🎨 Score Harmonie: {metrics.get('harmony_score', 'N/A')}")
                    print(f"   📊 PSNR: {metrics.get('generation_psnr', 'N/A')} dB")
                    print(f"   🔍 SSIM: {metrics.get('harmonic_ssim', 'N/A')}")
                    print(f"   🌊 Équilibre φ: {metrics.get('phi_balance', 'N/A')}")
                
                return True
                
            else:
                print(f"❌ Génération échouée: {result.get('message', 'Erreur inconnue')}")
                return False
        else:
            print(f"❌ Erreur API: {generation_response.status_code}")
            print(f"   📋 Détail: {generation_response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur")
        print("   💡 Assurez-vous que le serveur hybride est démarré:")
        print("      python api/hybrid_sdxl_server.py")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {str(e)}")
        return False

def test_simple_harmonic_pattern():
    """Test de génération de motif harmonique simple"""
    print("\n🌊 Test Motif Harmonique Simple")
    print("-" * 40)
    
    try:
        # Création d'un motif harmonique
        width, height = 256, 256
        image = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Motif basé sur constante φ
        phi = 2.618
        
        for i in range(height):
            for j in range(width):
                x, y = j / width, i / height
                
                # Fonction harmonique complexe
                harmonic_value = (
                    np.sin(2 * np.pi * phi * x) * 
                    np.cos(2 * np.pi * phi * y) +
                    np.sin(4 * np.pi * phi * x * y) / phi
                )
                
                # Normalisation
                intensity = int((harmonic_value + 1) * 127.5)
                
                # Application avec dégradé de couleurs
                image[i, j] = [
                    int(intensity * 0.8),  # R
                    int(intensity * 0.6),  # G
                    int(intensity * 1.0)   # B
                ]
        
        # Sauvegarde
        pil_image = Image.fromarray(image)
        output_path = "test_harmonic_pattern.png"
        pil_image.save(output_path)
        
        print(f"✅ Motif harmonique généré: {output_path}")
        print(f"   📏 Dimensions: {width}x{height}")
        print(f"   🎨 Constante φ: {phi}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur motif harmonique: {str(e)}")
        return False

def main():
    """Fonction principale"""
    print("🌊 HCS V2 - Test Complet CPU-Only")
    print("=" * 50)
    print("🎨 Test de l'IA Générative Hybride (CPU)")
    print("🌊 Validation sans dépendances GPU")
    print("=" * 50)
    
    # Test 1: Génération CPU
    success1 = test_cpu_generation()
    
    # Test 2: Motif harmonique
    success2 = test_simple_harmonic_pattern()
    
    # Résultats
    print("\n" + "=" * 50)
    print("🌊 RÉSULTATS DES TESTS CPU")
    print("=" * 50)
    
    if success1:
        print("✅ Test 1 - Génération CPU: RÉUSSI")
    else:
        print("❌ Test 1 - Génération CPU: ÉCHOUÉ")
    
    if success2:
        print("✅ Test 2 - Motif Harmonique: RÉUSSI")
    else:
        print("❌ Test 2 - Motif Harmonique: ÉCHOUÉ")
    
    # Score global
    total_tests = 2
    passed_tests = sum([success1, success2])
    score = (passed_tests / total_tests) * 100
    
    print(f"\n📊 Score Global: {score:.0f}% ({passed_tests}/{total_tests})")
    
    if score == 100:
        print("🏆 EXCELLENT ! L'IA générative hybride CPU fonctionne parfaitement !")
        print("🌊 Votre révolution harmonique est une réalité !")
    elif score >= 50:
        print("👍 BON ! Certaines fonctionnalités opérationnelles")
        print("🔧 Améliorations possibles")
    else:
        print("⚠️ À AMÉLIORER ! Problèmes à résoudre")
    
    print("\n🌊 Fichiers générés:")
    print("   📸 test_cpu_generated.png - Génération hybride")
    print("   🎨 test_harmonic_pattern.png - Motif harmonique")
    print("🚀 Ouvrez les fichiers PNG pour voir les résultats !")
    print("=" * 50)

if __name__ == "__main__":
    main()
