#!/usr/bin/env python3
"""
Tests pour H.264 Analysis
Tests du système d'analyse H.264 → HCV16
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
import numpy as np
import cv2
from h264_analyzer import H264Analyzer
from artifact_detector import ArtifactDetector

class TestH264Analysis(unittest.TestCase):
    """Tests pour analyseur H.264"""
    
    def setUp(self):
        """Initialisation tests"""
        self.analyzer = H264Analyzer()
        self.detector = ArtifactDetector()
        
        # Création image test avec artefacts simulés
        self.test_image = self._create_test_image_with_artifacts()
        
    def _create_test_image_with_artifacts(self):
        """Création image test avec artefacts H.264 simulés"""
        # Image de base 256x256
        image = np.random.randint(100, 150, (256, 256), dtype=np.uint8)
        
        # Ajout artefacts de blocs 8x8
        for y in range(0, 256, 8):
            for x in range(0, 256, 8):
                # Variation légère par bloc
                block_offset = np.random.randint(-10, 10)
                block = image[y:y+8, x:x+8].astype(np.int16) + block_offset
                image[y:y+8, x:x+8] = np.clip(block, 0, 255).astype(np.uint8)
        
        # Ajout frontières de blocs
        for i in range(8, 256, 8):
            image[i, :] = np.clip(image[i, :].astype(np.int16) + 20, 0, 255).astype(np.uint8)  # Ligne horizontale
            image[:, i] = np.clip(image[:, i].astype(np.int16) + 20, 0, 255).astype(np.uint8)  # Ligne verticale
        
        return image
    
    def test_blocking_artifacts_detection(self):
        """Test détection artefacts de blocs"""
        print("\n🧪 Test détection blocking artifacts...")
        
        # Test avec image contenant des artefacts
        result = self.detector.detect_blocking_artifacts(self.test_image)
        
        # Vérifications
        self.assertIn('combined_score', result)
        self.assertIn('severity', result)
        self.assertIn('hcv16_gain_potential', result)
        
        # L'image test devrait avoir des artefacts détectables
        self.assertGreater(result['combined_score'], 0.1)
        
        print(f"   Score détecté: {result['combined_score']:.3f}")
        print(f"   Sévérité: {result['severity']}")
        print(f"   Gain HCV16: {result['hcv16_gain_potential']*100:.1f}%")
        
    def test_artifact_detector_complete(self):
        """Test détecteur complet d'artefacts"""
        print("\n🧪 Test détecteur complet...")
        
        # Analyse complète
        results = self.detector.detect_all_artifacts(self.test_image)
        
        # Vérifications structure
        expected_keys = [
            'blocking_artifacts', 'ringing_artifacts', 'mosquito_noise',
            'quantization_noise', 'motion_blur', 'compression_patterns',
            'hcv16_exploitability'
        ]
        
        for key in expected_keys:
            self.assertIn(key, results)
        
        # Vérification exploitabilité
        exploitability = results['hcv16_exploitability']
        self.assertIn('weighted_score', exploitability)
        self.assertIn('exploitability_level', exploitability)
        self.assertIn('estimated_total_gain', exploitability)
        
        print(f"   Exploitabilité: {exploitability['exploitability_level']}")
        print(f"   Score pondéré: {exploitability['weighted_score']:.3f}")
        print(f"   Gain estimé: {exploitability['estimated_total_gain']*100:.1f}%")
        
    def test_h264_analyzer_mock(self):
        """Test analyseur H.264 avec données simulées"""
        print("\n🧪 Test analyseur H.264 (simulation)...")
        
        # Création frames test
        test_frames = []
        for i in range(10):
            # Frame YUV simulée
            frame = np.random.randint(50, 200, (240, 320, 3), dtype=np.uint8)
            
            # Ajout artefacts progressifs
            if i > 0:
                # Similarité avec frame précédente (simulation compression temporelle)
                frame = (0.7 * test_frames[-1] + 0.3 * frame).astype(np.uint8)
            
            test_frames.append(frame)
        
        # Tests méthodes individuelles
        blocking_result = self.analyzer._analyze_blocking_artifacts(test_frames)
        motion_result = self.analyzer._analyze_motion_residuals(test_frames)
        quantization_result = self.analyzer._analyze_quantization_noise(test_frames)
        temporal_result = self.analyzer._analyze_temporal_patterns(test_frames)
        
        # Vérifications
        self.assertIn('level', blocking_result)
        self.assertIn('hcv16_gain_potential', blocking_result)
        
        self.assertIn('level', motion_result)
        self.assertIn('exploitability', motion_result)
        
        self.assertIn('grain_synthesis_applicable', quantization_result)
        
        self.assertIn('recommended_gop', temporal_result)
        
        print(f"   Blocking: {blocking_result['level']}")
        print(f"   Motion: {motion_result['level']}")
        print(f"   Quantization: {quantization_result['level']}")
        print(f"   GOP recommandé: {temporal_result['recommended_gop']}")
        
    def test_hcv16_opportunities_calculation(self):
        """Test calcul opportunités HCV16"""
        print("\n🧪 Test calcul opportunités HCV16...")
        
        # Données d'analyse simulées
        mock_analyses = {
            'blocking': {'hcv16_gain_potential': 0.08},
            'motion': {'hcv16_gain_potential': 0.12},
            'quantization': {'hcv16_gain_potential': 0.05},
            'temporal': {'hcv16_gain_potential': 0.06}
        }
        
        # Calcul opportunités
        opportunities = self.analyzer._calculate_hcv16_opportunities(mock_analyses)
        
        # Vérifications
        self.assertIn('estimated_compression_ratio', opportunities)
        self.assertIn('opportunity_level', opportunities)
        self.assertIn('poc_feasibility', opportunities)
        
        # Le ratio devrait être > 1.0
        ratio = opportunities['estimated_compression_ratio']
        self.assertGreater(ratio, 1.0)
        
        print(f"   Ratio estimé: {ratio:.3f}×")
        print(f"   Niveau: {opportunities['opportunity_level']}")
        print(f"   POC faisable: {opportunities['poc_feasibility']}")
        
    def test_performance_metrics(self):
        """Test métriques de performance"""
        print("\n🧪 Test métriques performance...")
        
        import time
        
        # Test vitesse détection artefacts
        start_time = time.time()
        
        for _ in range(10):
            self.detector.detect_blocking_artifacts(self.test_image)
        
        detection_time = (time.time() - start_time) / 10
        
        # Test vitesse analyse complète
        start_time = time.time()
        self.detector.detect_all_artifacts(self.test_image)
        complete_time = time.time() - start_time
        
        print(f"   Détection blocking: {detection_time*1000:.1f}ms")
        print(f"   Analyse complète: {complete_time*1000:.1f}ms")
        
        # Vérification performance acceptable
        self.assertLess(detection_time, 0.1)  # < 100ms
        self.assertLess(complete_time, 1.0)   # < 1s
        
    def test_edge_cases(self):
        """Test cas limites"""
        print("\n🧪 Test cas limites...")
        
        # Image uniforme (pas d'artefacts)
        uniform_image = np.full((128, 128), 128, dtype=np.uint8)
        result_uniform = self.detector.detect_all_artifacts(uniform_image)
        
        # Devrait détecter peu d'artefacts
        exploitability = result_uniform['hcv16_exploitability']
        self.assertLess(exploitability['weighted_score'], 0.3)
        
        # Image très bruitée
        noisy_image = np.random.randint(0, 255, (128, 128), dtype=np.uint8)
        result_noisy = self.detector.detect_all_artifacts(noisy_image)
        
        # Devrait détecter du bruit de quantification
        quant_noise = result_noisy['quantization_noise']
        self.assertGreater(quant_noise['combined_score'], 0.1)
        
        # Image très petite
        tiny_image = np.random.randint(0, 255, (16, 16), dtype=np.uint8)
        result_tiny = self.detector.detect_all_artifacts(tiny_image)
        
        # Ne devrait pas planter
        self.assertIsInstance(result_tiny, dict)
        
        print("   ✅ Tous les cas limites gérés")

def run_poc_validation():
    """Validation POC avec métriques business"""
    print("\n" + "="*60)
    print("🚀 VALIDATION POC H.264 → HCV16")
    print("="*60)
    
    analyzer = H264Analyzer()
    detector = ArtifactDetector()
    
    # Simulation sur différents types de contenu
    test_scenarios = [
        ("Animation", "Contenu avec blocking élevé"),
        ("Film", "Contenu avec motion blur"),
        ("Sport", "Contenu avec artefacts temporels"),
        ("News", "Contenu avec quantization noise")
    ]
    
    results = []
    
    for scenario_name, description in test_scenarios:
        print(f"\n📊 Scénario: {scenario_name} ({description})")
        
        # Génération image test spécialisée
        if scenario_name == "Animation":
            test_image = create_animation_artifacts()
        elif scenario_name == "Film":
            test_image = create_film_artifacts()
        elif scenario_name == "Sport":
            test_image = create_sport_artifacts()
        else:  # News
            test_image = create_news_artifacts()
        
        # Analyse
        artifacts = detector.detect_all_artifacts(test_image)
        exploitability = artifacts['hcv16_exploitability']
        
        # Métriques business
        ratio = exploitability['compression_ratio_estimate']
        savings_percent = (ratio - 1) * 100
        
        results.append({
            'scenario': scenario_name,
            'ratio': ratio,
            'savings': savings_percent,
            'level': exploitability['exploitability_level'],
            'poc_viable': ratio >= 1.02
        })
        
        print(f"   Ratio: {ratio:.3f}× ({savings_percent:.1f}% économie)")
        print(f"   Niveau: {exploitability['exploitability_level']}")
        print(f"   POC viable: {'✅ OUI' if ratio >= 1.02 else '❌ NON'}")
    
    # Résumé final
    print(f"\n" + "="*60)
    print("📈 RÉSUMÉ VALIDATION POC")
    print("="*60)
    
    viable_count = sum(1 for r in results if r['poc_viable'])
    avg_ratio = sum(r['ratio'] for r in results) / len(results)
    avg_savings = sum(r['savings'] for r in results) / len(results)
    
    print(f"Scénarios viables: {viable_count}/{len(results)} ({viable_count/len(results)*100:.0f}%)")
    print(f"Ratio moyen: {avg_ratio:.3f}×")
    print(f"Économie moyenne: {avg_savings:.1f}%")
    
    # Estimation business
    if avg_ratio >= 1.05:
        business_potential = "EXCELLENT"
    elif avg_ratio >= 1.03:
        business_potential = "BON"
    elif avg_ratio >= 1.02:
        business_potential = "MODÉRÉ"
    else:
        business_potential = "FAIBLE"
    
    print(f"Potentiel business: {business_potential}")
    
    # Recommandation
    if viable_count >= len(results) * 0.8:
        recommendation = "🚀 LANCER DÉVELOPPEMENT COMPLET"
    elif viable_count >= len(results) * 0.5:
        recommendation = "⚡ OPTIMISER ET RELANCER TESTS"
    else:
        recommendation = "🔄 REVOIR APPROCHE TECHNIQUE"
    
    print(f"Recommandation: {recommendation}")
    
    return results

def create_animation_artifacts():
    """Création artefacts typiques animation"""
    image = np.zeros((256, 256), dtype=np.uint8)
    
    # Zones uniformes avec frontières nettes (typique animation)
    image[50:100, 50:150] = 200  # Zone claire
    image[120:200, 80:180] = 100  # Zone sombre
    
    # Ajout blocking artifacts forts
    for y in range(0, 256, 8):
        for x in range(0, 256, 8):
            block_offset = np.random.randint(-15, 15)
            block = image[y:y+8, x:x+8].astype(np.int16) + block_offset
            image[y:y+8, x:x+8] = np.clip(block, 0, 255).astype(np.uint8)
    
    return image

def create_film_artifacts():
    """Création artefacts typiques film"""
    # Gradient naturel avec motion blur
    y, x = np.ogrid[:256, :256]
    image = ((x + y) / 2).astype(np.uint8)
    
    # Ajout motion blur horizontal
    kernel = np.zeros((1, 7))
    kernel[0, :] = 1/7
    image = cv2.filter2D(image, -1, kernel)
    
    return image.astype(np.uint8)

def create_sport_artifacts():
    """Création artefacts typiques sport"""
    # Texture complexe avec mouvement
    image = np.random.randint(80, 180, (256, 256), dtype=np.uint8)
    
    # Ajout patterns temporels (simulation mouvement rapide)
    for i in range(0, 256, 4):
        image[i:i+2, :] = np.roll(image[i:i+2, :], 2, axis=1)
    
    return image

def create_news_artifacts():
    """Création artefacts typiques news"""
    # Image avec quantization noise uniforme
    image = np.full((256, 256), 128, dtype=np.uint8)
    
    # Ajout bruit de quantification
    noise = np.random.normal(0, 8, (256, 256))
    image = np.clip(image + noise, 0, 255)
    
    return image.astype(np.uint8)

if __name__ == '__main__':
    print("🧪 LANCEMENT TESTS H.264 → HCV16 POC")
    print("="*50)
    
    # Tests unitaires
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Validation POC
    run_poc_validation()
    
    print("\n✅ TESTS TERMINÉS")