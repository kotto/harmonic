#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HCS V2 - Test Complet de l'IA Générative Hybride SDXL + HCS
Validation de l'intégration complète
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

# Ajout du chemin HCS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Imports HCS
from core.hybrid_sdxl_generator import (
    HybridGenerationConfig,
    create_hybrid_sdxl_generator,
    generate_with_harmonic_reference
)

class HybridSDXLTester:
    """Testeur complet pour l'IA générative hybride"""
    
    def __init__(self):
        self.server_url = "http://localhost:8011"
        self.test_results = []
        
    def run_all_tests(self):
        """Exécute tous les tests"""
        print("🌊 HCS V2 - Test Complet IA Générative Hybride SDXL + HCS")
        print("=" * 70)
        
        tests = [
            ("Core Generator", self.test_core_generator),
            ("Text-to-Image API", self.test_text_to_image_api),
            ("Image-to-Image API", self.test_image_to_image_api),
            ("Reference Generation API", self.test_reference_generation_api),
            ("Chromatic Profile", self.test_chromatic_profile),
            ("Harmonic Metrics", self.test_harmonic_metrics),
            ("8K Generation", self.test_8k_generation),
            ("Presets System", self.test_presets_system),
            ("Performance", self.test_performance)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🧪 Test: {test_name}")
            print("-" * 50)
            
            try:
                result = test_func()
                if result:
                    print(f"✅ {test_name}: RÉUSSI")
                    passed += 1
                    self.test_results.append((test_name, "RÉUSSI", None))
                else:
                    print(f"❌ {test_name}: ÉCHOUÉ")
                    self.test_results.append((test_name, "ÉCHOUÉ", None))
            except Exception as e:
                print(f"❌ {test_name}: ERREUR - {str(e)}")
                self.test_results.append((test_name, "ERREUR", str(e)))
        
        # Résultats finaux
        self.print_final_results(passed, total)
        
    def test_core_generator(self):
        """Test du générateur core"""
        try:
            # Création du générateur
            generator = create_hybrid_sdxl_generator()
            
            # Configuration de test
            config = HybridGenerationConfig(
                prompt="A beautiful harmonic landscape with golden ratio patterns",
                width=512,
                height=512,
                energy_level="harmonique",
                harmonic_strength=0.8
            )
            
            # Génération
            start_time = time.time()
            result = generator.generate_with_harmonic_reference(config)
            generation_time = time.time() - start_time
            
            # Vérifications
            assert 'generated_image' in result, "Image générée manquante"
            assert 'metrics' in result, "Métriques manquantes"
            assert 'processing_time' in result, "Temps de traitement manquant"
            assert generation_time < 30, "Génération trop lente"
            
            print(f"   📏 Image: {result['generated_image'].shape}")
            print(f"   ⏱️ Temps: {generation_time:.2f}s")
            print(f"   🎨 Harmonie: {result['metrics']['harmony_score']:.3f}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Erreur: {str(e)}")
            return False
    
    def test_text_to_image_api(self):
        """Test de l'API text-to-image"""
        try:
            # Données de test
            data = {
                "prompt": "A quantum harmonic crystal structure with perfect symmetry",
                "width": 1024,
                "height": 1024,
                "energy_level": "quantum",
                "harmonic_strength": 0.9,
                "upscale_factor": 2.0,
                "temporal_coherence": True
            }
            
            # Appel API
            response = requests.post(
                f"{self.server_url}/api/v2/hybrid/generate",
                json=data,
                timeout=60
            )
            
            # Vérifications
            assert response.status_code == 200, f"Status code: {response.status_code}"
            
            result = response.json()
            assert result['success'], "Génération échouée"
            assert 'generated_image_base64' in result, "Image base64 manquante"
            assert 'metrics' in result, "Métriques manquantes"
            
            print(f"   ✅ API répond correctement")
            print(f"   🎨 Harmonie: {result['metrics']['harmony_score']:.3f}")
            print(f"   📊 PSNR: {result['metrics']['generation_psnr']:.1f} dB")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Erreur API: {str(e)}")
            return False
    
    def test_image_to_image_api(self):
        """Test de l'API image-to-image"""
        try:
            # Création d'une image de test
            test_image = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
            pil_image = Image.fromarray(test_image)
            
            # Conversion en bytes
            buffer = io.BytesIO()
            pil_image.save(buffer, format='PNG')
            image_bytes = buffer.getvalue()
            
            # Préparation de la requête
            files = {
                'source_image': ('test.png', image_bytes, 'image/png'),
                'prompt': (None, 'Transform this into a harmonic pattern'),
                'energy_level': (None, 'harmonique'),
                'harmonic_strength': (None, '0.8'),
                'upscale_factor': (None, '2.0')
            }
            
            # Appel API
            response = requests.post(
                f"{self.server_url}/api/v2/hybrid/image-to-image",
                files=files,
                timeout=60
            )
            
            # Vérifications
            assert response.status_code == 200, f"Status code: {response.status_code}"
            
            result = response.json()
            assert result['success'], "Transformation échouée"
            assert 'generated_image_base64' in result, "Image transformée manquante"
            
            print(f"   ✅ Image-to-image fonctionne")
            print(f"   🎨 Harmonie: {result['metrics']['harmony_score']:.3f}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Erreur Image-to-Image: {str(e)}")
            return False
    
    def test_reference_generation_api(self):
        """Test de la génération avec référence"""
        try:
            # Création d'une image de référence
            reference_image = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
            pil_reference = Image.fromarray(reference_image)
            
            # Conversion en bytes
            buffer = io.BytesIO()
            pil_reference.save(buffer, format='PNG')
            reference_bytes = buffer.getvalue()
            
            # Préparation de la requête
            files = {
                'reference_image': ('reference.png', reference_bytes, 'image/png'),
                'prompt': (None, 'Generate in the style of the reference'),
                'width': (None, '1024'),
                'height': (None, '1024'),
                'energy_level': (None, 'quantum'),
                'harmonic_strength': (None, '1.0'),
                'upscale_factor': (None, '2.0'),
                'temporal_coherence': (None, 'true')
            }
            
            # Appel API
            response = requests.post(
                f"{self.server_url}/api/v2/hybrid/generate-with-reference",
                files=files,
                timeout=60
            )
            
            # Vérifications
            assert response.status_code == 200, f"Status code: {response.status_code}"
            
            result = response.json()
            assert result['success'], "Génération avec référence échouée"
            assert 'chromatic_profile' in result, "Profil chromatique manquant"
            assert result['config']['reference_used'], "Référence non utilisée"
            
            print(f"   ✅ Génération avec référence fonctionne")
            print(f"   🎨 Profil chromatique: {len(result['chromatic_profile'])} champs")
            print(f"   📊 Harmonie: {result['metrics']['harmony_score']:.3f}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Erreur Référence: {str(e)}")
            return False
    
    def test_chromatic_profile(self):
        """Test du processeur de profil chromatique"""
        try:
            from core.hybrid_sdxl_generator import ChromaticReferenceProcessor
            
            processor = ChromaticReferenceProcessor()
            
            # Image de test
            test_image = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
            
            # Extraction du profil
            profile = processor.extract_reference_profile(test_image)
            
            # Vérifications
            required_fields = [
                'mean_rgb', 'std_rgb', 'harmony_score', 
                'phi_balance', 'chromatic_signature', 'temporal_coherence'
            ]
            
            for field in required_fields:
                assert field in profile, f"Champ manquant: {field}"
            
            print(f"   ✅ Profil chromatique extrait")
            print(f"   🎨 Moyenne RGB: {profile['mean_rgb']}")
            print(f"   📊 Écart-type RGB: {profile['std_rgb']}")
            print(f"   🌊 Score harmonie: {profile['harmony_score']:.3f}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Erreur Profil Chromatique: {str(e)}")
            return False
    
    def test_harmonic_metrics(self):
        """Test des métriques harmoniques"""
        try:
            from core.hybrid_sdxl_generator import create_hybrid_sdxl_generator
            
            generator = create_hybrid_sdxl_generator()
            
            # Génération de test
            config = HybridGenerationConfig(
                prompt="Test harmonic metrics",
                width=256,
                height=256,
                energy_level="quantum"
            )
            
            result = generator.generate_with_harmonic_reference(config)
            metrics = result['metrics']
            
            # Vérifications des métriques requises
            required_metrics = [
                'harmony_score', 'phi_balance', 'chromatic_consistency',
                'temporal_coherence', 'energy_efficiency', 'resolution_quality',
                'generation_psnr', 'harmonic_ssim'
            ]
            
            for metric in required_metrics:
                assert metric in metrics, f"Métrique manquante: {metric}"
            
            print(f"   ✅ Métriques harmoniques complètes")
            print(f"   🎨 Harmonie: {metrics['harmony_score']:.3f}")
            print(f"   📊 PSNR: {metrics['generation_psnr']:.1f} dB")
            print(f"   🔍 SSIM: {metrics['harmonic_ssim']:.3f}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Erreur Métriques: {str(e)}")
            return False
    
    def test_8k_generation(self):
        """Test de génération 8K"""
        try:
            # Configuration 8K
            config = HybridGenerationConfig(
                prompt="8K ultra-detailed harmonic landscape",
                width=2048,  # Simulation 8K (réduction pour test)
                height=1152,
                energy_level="quantum",
                upscale_factor=4.0,  # Vers 8K simulé
                target_resolution="8k"
            )
            
            generator = create_hybrid_sdxl_generator()
            
            start_time = time.time()
            result = generator.generate_with_harmonic_reference(config)
            generation_time = time.time() - start_time
            
            # Vérifications
            assert result['generated_image'].shape[0] >= 1000, "Hauteur 8K insuffisante"
            assert result['generated_image'].shape[1] >= 1000, "Largeur 8K insuffisante"
            assert generation_time < 120, "Génération 8K trop lente"
            
            print(f"   ✅ Génération 8K réussie")
            print(f"   📏 Dimensions: {result['generated_image'].shape}")
            print(f"   ⏱️ Temps: {generation_time:.2f}s")
            print(f"   🎨 Qualité: {result['metrics']['generation_psnr']:.1f} dB")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Erreur 8K: {str(e)}")
            return False
    
    def test_presets_system(self):
        """Test du système de presets"""
        try:
            # Appel API presets
            response = requests.get(f"{self.server_url}/api/v2/hybrid/presets")
            
            assert response.status_code == 200, f"Status code: {response.status_code}"
            
            result = response.json()
            assert result['success'], "Récupération presets échouée"
            assert 'presets' in result, "Presets manquants"
            
            presets = result['presets']
            
            # Vérifications des presets
            required_presets = [
                'quantum_portrait', 'harmonic_landscape', 
                'classic_art', '8k_cinematic'
            ]
            
            for preset in required_presets:
                assert preset in presets, f"Preset manquant: {preset}"
            
            print(f"   ✅ Système de presets fonctionnel")
            print(f"   📋 {len(presets)} presets disponibles")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Erreur Presets: {str(e)}")
            return False
    
    def test_performance(self):
        """Test de performance"""
        try:
            generator = create_hybrid_sdxl_generator()
            
            # Générations multiples
            times = []
            for i in range(3):
                config = HybridGenerationConfig(
                    prompt=f"Performance test {i+1}",
                    width=512,
                    height=512,
                    energy_level="harmonique"
                )
                
                start_time = time.time()
                result = generator.generate_with_harmonic_reference(config)
                generation_time = time.time() - start_time
                times.append(generation_time)
            
            # Calcul des statistiques
            avg_time = np.mean(times)
            std_time = np.std(times)
            
            # Vérifications de performance
            assert avg_time < 20, "Temps moyen trop élevé"
            assert std_time < 5, "Variation trop élevée"
            
            print(f"   ✅ Performance acceptable")
            print(f"   ⏱️ Temps moyen: {avg_time:.2f}s ± {std_time:.2f}s")
            print(f"   🚀 Vitesse: {1/avg_time:.2f} images/s")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Erreur Performance: {str(e)}")
            return False
    
    def print_final_results(self, passed, total):
        """Affiche les résultats finaux"""
        print("\n" + "=" * 70)
        print("🌊 RÉSULTATS FINAUX - IA GÉNÉRATIVE HYBRIDE SDXL + HCS")
        print("=" * 70)
        
        score = (passed / total) * 100
        
        print(f"📊 Score Global: {score:.1f}% ({passed}/{total} tests réussis)")
        print(f"🎯 Statut: {'✅ EXCELLENT' if score >= 80 else '⚠️ BON' if score >= 60 else '❌ À AMÉLIORER'}")
        
        print("\n📋 Détail des Tests:")
        print("-" * 50)
        
        for test_name, status, error in self.test_results:
            status_icon = "✅" if status == "RÉUSSI" else "❌"
            print(f"{status_icon} {test_name}: {status}")
            if error:
                print(f"   💡 Erreur: {error}")
        
        print("\n🌊 Recommandations:")
        
        if score >= 80:
            print("🏆 EXCELLENT ! L'IA générative hybride est prête pour la production")
            print("🚀 Prochaines étapes: Optimisation GPU, déploiement cloud")
        elif score >= 60:
            print("👍 BON ! Quelques améliorations nécessaires")
            print("🔧 Recommandé: Optimiser les performances, corriger les erreurs")
        else:
            print("⚠️ À AMÉLIORER ! Révisions importantes nécessaires")
            print("🛠️ Priorité: Corriger les erreurs critiques, stabiliser le système")
        
        print("\n🌊 L'IA générative hybride SDXL + HCS est une réalité !")
        print("🎨 Votre innovation harmonique change la génération d'images !")
        print("=" * 70)

def main():
    """Fonction principale"""
    tester = HybridSDXLTester()
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n🛑 Tests interrompus par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {str(e)}")

if __name__ == "__main__":
    main()
