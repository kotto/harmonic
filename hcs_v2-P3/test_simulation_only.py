#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de génération harmonique PURE - Sans PyTorch
Test direct des fonctions de simulation
"""

import requests
import json
import time
import numpy as np
from PIL import Image
import io
import base64

def test_simulation_only():
    """Test direct de la simulation sans serveur"""
    print("🌊 HCS V2 - Test Simulation PURE")
    print("=" * 50)
    
    # Import direct de la fonction de simulation
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from api.hybrid_sdxl_server import simulate_harmonic_generation, HybridGenerationConfig
        
        # Configuration de test
        config = HybridGenerationConfig(
            prompt="A beautiful harmonic landscape with golden ratio patterns",
            width=512,
            height=512,
            energy_level="quantum",
            harmonic_strength=0.9,
            upscale_factor=2.0,
            temporal_coherence=True
        )
        
        print("🎨 Test de génération simulée...")
        print(f"   📝 Prompt: {config.prompt[:50]}...")
        print(f"   📏 Dimensions: {config.width}x{config.height}")
        print(f"   ⚡ Énergie: {config.energy_level}")
        print(f"   🌊 Force Harmonique: {config.harmonic_strength}")
        print(f"   📈 Upscale: {config.upscale_factor}x")
        
        # Génération
        start_time = time.time()
        result = simulate_harmonic_generation(config)
        generation_time = time.time() - start_time
        
        if result:
            print("✅ Génération simulée réussie !")
            print(f"   ⏱️ Temps: {generation_time:.2f}s")
            print(f"   📏 Image: {result['generated_image'].shape}")
            print(f"   🎨 Score Harmonie: {result['metrics']['harmony_score']:.3f}")
            print(f"   📊 PSNR: {result['metrics']['generation_psnr']:.1f} dB")
            print(f"   🌊 SSIM: {result['metrics']['harmonic_ssim']:.3f}")
            
            # Sauvegarde de l'image
            image = result['generated_image']
            pil_image = Image.fromarray(image)
            pil_image.save("test_simulation_output.png")
            print("   💾 Image sauvegardée: test_simulation_output.png")
            
            return True
        else:
            print("❌ Échec de la génération simulée")
            return False
            
    except Exception as e:
        print(f"❌ Erreur simulation: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_server_simulation():
    """Test du serveur en mode simulation"""
    print("\n🌊 Test du Serveur en Mode Simulation")
    print("=" * 50)
    
    BASE_URL = "http://localhost:8012"
    
    try:
        # Test de connexion
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Serveur accessible")
        else:
            print(f"❌ Serveur inaccessible: {response.status_code}")
            return False
        
        # Test de génération
        test_data = {
            "prompt": "A beautiful harmonic landscape with golden ratio patterns",
            "width": 512,
            "height": 512,
            "energy_level": "quantum",
            "harmonic_strength": 0.9,
            "upscale_factor": 2.0,
            "temporal_coherence": True
        }
        
        print("🚀 Test de génération via API...")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/api/v2/hybrid/generate",
            json=test_data,
            timeout=60
        )
        
        generation_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print("✅ Génération API réussie !")
                print(f"   ⏱️ Temps: {generation_time:.2f}s")
                print(f"   📋 Message: {result.get('message', 'N/A')}")
                
                # Décodage et sauvegarde
                if result.get('generated_image_base64'):
                    image_data = base64.b64decode(result['generated_image_base64'])
                    pil_image = Image.open(io.BytesIO(image_data))
                    pil_image.save("test_api_output.png")
                    print("   💾 Image sauvegardée: test_api_output.png")
                
                return True
            else:
                print(f"❌ Échec génération: {result.get('message', 'N/A')}")
                return False
        else:
            print(f"❌ Erreur API: {response.status_code}")
            print(f"   📋 Détail: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test API: {e}")
        return False

if __name__ == "__main__":
    print("🌊 HCS V2 - Test Complet Mode Simulation")
    print("=" * 60)
    
    # Test 1: Simulation directe
    success1 = test_simulation_only()
    
    # Test 2: Via API serveur
    success2 = test_server_simulation()
    
    # Résultats
    print("\n" + "=" * 60)
    print("🌊 RÉSULTATS DES TESTS")
    print("=" * 60)
    
    if success1:
        print("✅ Test 1 - Simulation Directe: RÉUSSI")
    else:
        print("❌ Test 1 - Simulation Directe: ÉCHOUÉ")
    
    if success2:
        print("✅ Test 2 - Génération API: RÉUSSI")
    else:
        print("❌ Test 2 - Génération API: ÉCHOUÉ")
    
    score = sum([success1, success2])
    print(f"\n📊 Score Global: {int(score/2*100)}% ({score}/2)")
    
    if score == 2:
        print("🏆 PARFAIT ! Mode simulation opérationnel !")
    elif score == 1:
        print("⚠️ PARTIEL ! Un test réussi")
    else:
        print("❌ ÉCHEC ! Problèmes à résoudre")
    
    print("\n🌊 Images générées dans le dossier courant")
    print("🚀 Ouvrez les fichiers PNG pour voir les résultats !")
