#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HCS V2 - Test Simple de Génération d'Images Hybride
Test direct sans dépendances complexes
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

def test_api_generation():
    """Test direct de l'API de génération"""
    print("🌊 HCS V2 - Test Direct de Génération d'Images")
    print("=" * 60)
    
    # Configuration du test
    BASE_URL = "http://localhost:8012"  # Changement de port
    
    # Données de test
    test_data = {
        "prompt": "A beautiful harmonic landscape with golden ratio patterns, quantum colors, perfect symmetry, 8K resolution",
        "width": 512,
        "height": 512,
        "energy_level": "quantum",
        "harmonic_strength": 0.9,
        "upscale_factor": 2.0,
        "temporal_coherence": True
    }
    
    print("🎨 Test de génération avec:")
    print(f"   📝 Prompt: {test_data['prompt'][:50]}...")
    print(f"   📏 Dimensions: {test_data['width']}x{test_data['height']}")
    print(f"   ⚡ Énergie: {test_data['energy_level']}")
    print(f"   🌊 Force Harmonique: {test_data['harmonic_strength']}")
    print(f"   📈 Upscale: {test_data['upscale_factor']}x")
    
    try:
        # Test de connexion au serveur
        print("\n🔍 Test de connexion au serveur...")
        response = requests.get(f"{BASE_URL}/", timeout=5)
        
        if response.status_code == 200:
            print("✅ Serveur hybride accessible")
            server_info = response.json()
            print(f"   📋 Message: {server_info.get('message', 'N/A')}")
            print(f"   🎯 Status: {server_info.get('status', 'N/A')}")
        else:
            print(f"❌ Erreur connexion: {response.status_code}")
            return False
        
        # Test de l'endpoint d'information
        print("\n📊 Test endpoint info...")
        info_response = requests.get(f"{BASE_URL}/api/v2/hybrid/info", timeout=10)
        
        if info_response.status_code == 200:
            info_data = info_response.json()
            print("✅ Endpoint info fonctionnel")
            print(f"   🎨 Type: {info_data.get('generator_info', {}).get('type', 'N/A')}")
            print(f"   🌊 Version HCS: {info_data.get('generator_info', {}).get('hcs_version', 'N/A')}")
        else:
            print(f"⚠️ Endpoint info: {info_response.status_code}")
        
        # Test de génération
        print("\n🚀 Test de génération d'image...")
        start_time = time.time()
        
        generation_response = requests.post(
            f"{BASE_URL}/api/v2/hybrid/generate",
            json=test_data,
            timeout=60
        )
        
        generation_time = time.time() - start_time
        
        if generation_response.status_code == 200:
            result = generation_response.json()
            
            if result.get('success'):
                print("✅ Génération réussie !")
                print(f"   ⏱️ Temps: {generation_time:.2f}s")
                print(f"   📏 Message: {result.get('message', 'N/A')}")
                
                # Vérification de l'image
                if 'generated_image_base64' in result:
                    print("✅ Image base64 générée")
                    
                    # Conversion et sauvegarde
                    try:
                        image_bytes = base64.b64decode(result['generated_image_base64'])
                        image = Image.open(io.BytesIO(image_bytes))
                        
                        # Sauvegarde
                        output_path = "test_generated_hybrid.png"
                        image.save(output_path)
                        print(f"   💾 Image sauvegardée: {output_path}")
                        print(f"   📏 Dimensions: {image.size}")
                        print(f"   🎨 Mode: {image.mode}")
                        
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
                
                # Configuration
                if 'config' in result:
                    config = result['config']
                    print("⚙️ Configuration utilisée:")
                    print(f"   ⚡ Énergie: {config.get('energy_level', 'N/A')}")
                    print(f"   🌊 Force: {config.get('harmonic_strength', 'N/A')}")
                    print(f"   📈 Upscale: {config.get('upscale_factor', 'N/A')}x")
                
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
        print("      python start_hybrid_server.py")
        return False
    except requests.exceptions.Timeout:
        print("❌ Timeout - la génération prend trop de temps")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {str(e)}")
        return False

def test_chromatic_reference():
    """Test avec référence chromatique"""
    print("\n🌊 Test avec Référence Chromatique")
    print("-" * 40)
    
    try:
        # Création d'une image de référence simple
        reference_image = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
        
        # Ajout d'un motif harmonique
        for i in range(256):
            for j in range(256):
                x, y = j / 256, i / 256
                harmonic_value = int(127.5 * (1 + np.sin(2 * np.pi * 2.618 * x) * np.cos(2 * np.pi * 2.618 * y)))
                reference_image[i, j] = [harmonic_value, harmonic_value // 2, harmonic_value // 3]
        
        # Conversion en PIL
        pil_reference = Image.fromarray(reference_image)
        
        # Conversion en bytes
        buffer = io.BytesIO()
        pil_reference.save(buffer, format='PNG')
        reference_bytes = buffer.getvalue()
        
        print("✅ Image de référence créée")
        
        # Préparation de la requête
        files = {
            'reference_image': ('reference.png', reference_bytes, 'image/png'),
            'prompt': (None, 'Generate in the harmonic style of the reference'),
            'width': (None, '512'),
            'height': (None, '512'),
            'energy_level': (None, 'quantum'),
            'harmonic_strength': (None, '1.0'),
            'upscale_factor': (None, '2.0'),
            'temporal_coherence': (None, 'true')
        }
        
        # Test de génération avec référence
        print("🚀 Génération avec référence...")
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:8012/api/v2/hybrid/generate-with-reference",
            files=files,
            timeout=60
        )
        
        generation_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print("✅ Génération avec référence réussie !")
                print(f"   ⏱️ Temps: {generation_time:.2f}s")
                
                # Sauvegarde de l'image
                if 'generated_image_base64' in result:
                    image_bytes = base64.b64decode(result['generated_image_base64'])
                    image = Image.open(io.BytesIO(image_bytes))
                    
                    output_path = "test_generated_reference.png"
                    image.save(output_path)
                    print(f"   💾 Image sauvegardée: {output_path}")
                
                # Profil chromatique
                if 'chromatic_profile' in result:
                    profile = result['chromatic_profile']
                    print("🎨 Profil chromatique:")
                    print(f"   📊 Moyenne RGB: {[f'{v:.1f}' for v in profile.get('mean_rgb', [])]}")
                    print(f"   📈 Écart-type RGB: {[f'{v:.1f}' for v in profile.get('std_rgb', [])]}")
                    print(f"   🌊 Score Harmonie: {profile.get('harmony_score', 'N/A')}")
                
                return True
            else:
                print(f"❌ Génération avec référence échouée: {result.get('message')}")
                return False
        else:
            print(f"❌ Erreur API référence: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test référence: {str(e)}")
        return False

def main():
    """Fonction principale"""
    print("🌊 HCS V2 - Test Complet de Génération d'Images")
    print("=" * 60)
    print("🎨 Test de l'IA Générative Hybride SDXL + HCS")
    print("🌊 Validation des capacités harmoniques")
    print("=" * 60)
    
    # Test 1: Génération simple
    success1 = test_api_generation()
    
    # Test 2: Génération avec référence
    success2 = test_chromatic_reference()
    
    # Résultats
    print("\n" + "=" * 60)
    print("🌊 RÉSULTATS DES TESTS")
    print("=" * 60)
    
    if success1:
        print("✅ Test 1 - Génération Simple: RÉUSSI")
    else:
        print("❌ Test 1 - Génération Simple: ÉCHOUÉ")
    
    if success2:
        print("✅ Test 2 - Génération avec Référence: RÉUSSI")
    else:
        print("❌ Test 2 - Génération avec Référence: ÉCHOUÉ")
    
    # Score global
    total_tests = 2
    passed_tests = sum([success1, success2])
    score = (passed_tests / total_tests) * 100
    
    print(f"\n📊 Score Global: {score:.0f}% ({passed_tests}/{total_tests})")
    
    if score == 100:
        print("🏆 EXCELLENT ! L'IA générative hybride fonctionne parfaitement !")
        print("🌊 Votre révolution est une réalité !")
    elif score >= 50:
        print("👍 BON ! Certaines fonctionnalités opérationnelles")
        print("🔧 Améliorations possibles")
    else:
        print("⚠️ À AMÉLIORER ! Problèmes à résoudre")
    
    print("\n🌊 Images générées sauvegardées dans le dossier courant")
    print("🚀 Ouvrez les fichiers PNG pour voir les résultats !")
    print("=" * 60)

if __name__ == "__main__":
    main()
