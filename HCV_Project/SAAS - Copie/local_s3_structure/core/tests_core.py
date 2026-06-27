#!/usr/bin/env python3
"""
TESTS HARMONIC RESONANCE ENGINE - VALIDATION CORE
Tests rigoureux du moteur stable
Version: 1.0.0 - TESTS CORE
"""

import unittest
import time
import numpy as np
from harmonic_resonance_engine import (
    ENGINE,
    HarmonicResonanceEngine,
    ResonanceMetrics,
    HarmonicResponse
)

class TestHarmonicResonanceEngine(unittest.TestCase):
    """Tests complets du moteur de résonance - CRITIQUE"""
    
    def setUp(self):
        """Setup pour chaque test"""
        self.engine = ENGINE
    
    def test_engine_initialization(self):
        """Test initialisation moteur - CRITIQUE"""
        print("\n🧪 Test initialisation moteur...")
        
        # Test foundation connectée
        self.assertIsNotNone(self.engine.foundation, "Foundation non connectée")
        
        # Test harmoniques chargées
        self.assertEqual(len(self.engine.harmonics), 5, "Harmoniques incomplètes")
        
        # Test configuration
        self.assertIn('max_processing_time_ms', self.engine.engine_config)
        self.assertGreater(self.engine.engine_config['max_processing_time_ms'], 0)
        
        print("✅ Initialisation moteur validée")
    
    def test_apply_resonance(self):
        """Test application résonance - CRITIQUE"""
        print("\n🧪 Test application résonance...")
        
        # Test signal simple
        test_signal = np.array([1.0, 0.0, -1.0, 0.5, -0.5])
        
        # Application résonance
        resonated, metrics = self.engine.apply_resonance(test_signal)
        
        # Validation sortie
        self.assertIsNotNone(resonated, "Signal résoné None")
        self.assertIsNotNone(metrics, "Métriques None")
        
        # Validation métriques
        self.assertIsInstance(metrics, ResonanceMetrics, "Métriques type incorrect")
        self.assertGreater(metrics.confidence, 0, "Confiance invalide")
        self.assertGreater(metrics.processing_time_ms, 0, "Temps processing invalide")
        self.assertEqual(len(metrics.harmonics_used), 5, "Harmoniques utilisées incorrectes")
        
        print("✅ Application résonance validée")
    
    def test_generate_harmonic_response(self):
        """Test génération réponse harmonique - CRITIQUE"""
        print("\n🧪 Test génération réponse harmonique...")
        
        # Test prompt simple
        test_prompt = "Qu'est-ce que l'intelligence harmonique?"
        
        # Génération réponse
        response = self.engine.generate_harmonic_response(test_prompt)
        
        # Validation réponse
        self.assertIsInstance(response, HarmonicResponse, "Type réponse incorrect")
        self.assertIsNotNone(response.content, "Contenu None")
        self.assertIsNotNone(response.metrics, "Métriques None")
        self.assertEqual(response.foundation_version, "1.0.0", "Version foundation incorrecte")
        self.assertEqual(response.engine_version, "1.0.0", "Version engine incorrecte")
        
        # Validation contenu
        self.assertIn("🌊 RÉPONSE HARMONIQUE", response.content, "En-tête manquant")
        self.assertIn("PROMPT ORIGINAL", response.content, "Prompt non inclus")
        self.assertIn("HARMONIC SIGNATURE", response.content, "Signature manquante")
        
        print("✅ Génération réponse harmonique validée")
    
    def test_tokenization(self):
        """Test tokenisation - CRITIQUE"""
        print("\n🧪 Test tokenisation...")
        
        # Test phrase simple
        test_prompt = "Bonjour, monde harmonique!"
        tokens = self.engine._tokenize_prompt(test_prompt)
        
        # Validation tokens
        self.assertIsInstance(tokens, list, "Tokens doit être liste")
        self.assertGreater(len(tokens), 0, "Tokens vide")
        self.assertIn("bonjour", tokens, "Token 'bonjour' manquant")
        self.assertIn("monde", tokens, "Token 'monde' manquant")
        self.assertIn("harmonique", tokens, "Token 'harmonique' manquant")
        
        print("✅ Tokenisation validée")
    
    def test_tokens_to_signal(self):
        """Test conversion tokens en signal - CRITIQUE"""
        print("\n🧪 Test conversion tokens en signal...")
        
        # Test tokens
        tokens = ["test", "harmonic", "engine"]
        signal = self.engine._tokens_to_signal(tokens)
        
        # Validation signal
        self.assertIsInstance(signal, np.ndarray, "Signal doit être numpy array")
        self.assertEqual(len(signal), len(tokens), "Taille signal incorrecte")
        self.assertTrue(np.all(np.abs(signal) <= 1.0), "Signal non normalisé")
        
        print("✅ Conversion tokens en signal validée")
    
    def test_performance_requirements(self):
        """Test exigences performance - CRITIQUE"""
        print("\n🧪 Test exigences performance...")
        
        # Test temps réponse
        test_prompt = "Test performance rapide"
        start_time = time.time()
        response = self.engine.generate_harmonic_response(test_prompt)
        response_time = (time.time() - start_time) * 1000
        
        # Validation performance
        self.assertLess(response_time, 500, "Temps réponse trop lent")
        self.assertLess(response.metrics.processing_time_ms, 100, "Temps processing trop lent")
        
        print(f"✅ Performance validée ({response_time:.1f}ms)")
    
    def test_determinism(self):
        """Test déterminisme - CRITIQUE"""
        print("\n🧪 Test déterminisme...")
        
        # Test même prompt = même réponse
        test_prompt = "Test déterminisme harmonique"
        
        # Génération 1
        response1 = self.engine.generate_harmonic_response(test_prompt)
        time.sleep(0.01)  # Petite pause
        
        # Génération 2
        response2 = self.engine.generate_harmonic_response(test_prompt)
        
        # Validation déterminisme
        self.assertEqual(response1.content, response2.content, "Réponses non déterministes")
        self.assertEqual(response1.metrics.confidence, response2.metrics.confidence, "Confiances différentes")
        
        print("✅ Déterminisme validé")
    
    def test_engine_info(self):
        """Test informations moteur - CRITIQUE"""
        print("\n🧪 Test informations moteur...")
        
        info = self.engine.get_engine_info()
        
        # Validation structure
        self.assertIsInstance(info, dict, "Info doit être dict")
        self.assertIn("version", info, "Version manquante")
        self.assertIn("status", info, "Status manquant")
        self.assertIn("foundation", info, "Foundation info manquante")
        self.assertIn("config", info, "Config manquante")
        self.assertIn("capabilities", info, "Capabilities manquantes")
        
        # Validation valeurs
        self.assertEqual(info["version"], "1.0.0", "Version incorrecte")
        self.assertEqual(info["status"], "STABLE", "Status incorrect")
        
        print("✅ Informations moteur validées")

class TestResonanceMetrics(unittest.TestCase):
    """Tests métriques de résonance - COMPLÉMENTAIRES"""
    
    def test_metrics_structure(self):
        """Test structure métriques - CRITIQUE"""
        print("\n🧪 Test structure métriques...")
        
        # Test création métriques
        metrics = ResonanceMetrics(
            confidence=0.95,
            processing_time_ms=50.0,
            harmonics_used=[1, 2, 3, 4, 5],
            resonance_strength=0.999,
            determinism_score=0.999,
            naturalness_score=0.90,
            coherence_score=0.95
        )
        
        # Validation champs
        self.assertEqual(metrics.confidence, 0.95, "Confiance incorrecte")
        self.assertEqual(metrics.processing_time_ms, 50.0, "Temps processing incorrect")
        self.assertEqual(len(metrics.harmonics_used), 5, "Harmoniques utilisées incorrectes")
        
        print("✅ Structure métriques validée")

def run_core_validation():
    """Exécuter validation complète core"""
    print("🌊 VALIDATION COMPLÈTE HARMONIC RESONANCE ENGINE")
    print("=" * 80)
    print("📋 Tests: Validation moteur stable")
    print("🚨 Règle: Core stable après validation")
    print("=" * 80)
    
    # Créer suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Ajouter tous les tests
    suite.addTests(loader.loadTestsFromTestCase(TestHarmonicResonanceEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestResonanceMetrics))
    
    # Exécuter tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Résultat
    print("\n" + "=" * 80)
    if result.wasSuccessful():
        print("✅ TOUS LES TESTS CORE PASSÉS - MOTEUR VALIDÉ")
        print("🚀 PRÊT POUR APPLICATIONS")
        print("🌊 STATUT: STABLE - EXTENSIONS ADDITIVES SEULEMENT")
        return True
    else:
        print("❌ TESTS CORE ÉCHOUÉS - CORRECTIONS REQUISES")
        print(f"❌ Échecs: {len(result.failures)}")
        print(f"❌ Erreurs: {len(result.errors)}")
        return False

if __name__ == "__main__":
    success = run_core_validation()
    exit(0 if success else 1)
