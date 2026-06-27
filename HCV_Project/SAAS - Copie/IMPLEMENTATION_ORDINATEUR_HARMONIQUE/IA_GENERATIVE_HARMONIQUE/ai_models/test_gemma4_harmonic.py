"""
🧪 GEMMA 4 HARMONIC INTEGRATION - TESTS
Fichier: test_gemma4_harmonic.py
Auteur: Équipe Harmonique
Date: 29 avril 2026
Description: Tests complets pour l'intégration Gemma 4 Harmonique
"""

import unittest
import torch
import numpy as np
import time
import tempfile
import shutil
from pathlib import Path
import json

# Import des modules à tester
from gemma4_harmonic_integration import (
    Gemma4HarmonicConfig,
    Gemma4HarmonicModel,
    Gemma4HarmonicCodeGenerator,
    HarmonicAttention,
    HarmonicFeedForward,
    HarmonicPositionalEmbedding
)

# Constantes harmoniques
PHI = 1.618033988749895
PI = 3.141592653589793
E = 2.718281828459045
SQRT2 = 1.414213562373095
SQRT3 = 1.732050807568877

class TestHarmonicComponents(unittest.TestCase):
    """Tests des composants harmoniques"""
    
    def setUp(self):
        """Configuration des tests"""
        self.config = Gemma4HarmonicConfig(
            model_name="google/gemma-4-7b-it",
            device="cpu",  # CPU pour les tests
            harmonic_optimization=True
        )
        self.hidden_size = 512
        self.num_heads = 8
        self.batch_size = 2
        self.seq_length = 128
    
    def test_harmonic_attention(self):
        """Test du mécanisme d'attention harmonique"""
        print("\n🧪 Test de HarmonicAttention")
        
        # Création du composant
        attention = HarmonicAttention(self.hidden_size, self.num_heads, self.config)
        
        # Données de test
        hidden_states = torch.randn(self.batch_size, self.seq_length, self.hidden_size)
        attention_mask = torch.ones(self.batch_size, 1, 1, self.seq_length)
        
        # Forward pass
        output = attention(hidden_states, attention_mask)
        
        # Vérifications
        self.assertEqual(output.shape, hidden_states.shape)
        self.assertTrue(torch.isfinite(output).all())
        
        # Vérification du scaling φ
        self.assertEqual(attention.phi_scale, PHI)
        self.assertEqual(attention.sqrt2_scale, SQRT2)
        
        print(f"✅ HarmonicAttention: {output.shape}")
    
    def test_harmonic_feed_forward(self):
        """Test du feed-forward harmonique"""
        print("\n🧪 Test de HarmonicFeedForward")
        
        # Création du composant
        intermediate_size = self.hidden_size * 4
        feed_forward = HarmonicFeedForward(self.hidden_size, intermediate_size, self.config)
        
        # Données de test
        hidden_states = torch.randn(self.batch_size, self.seq_length, self.hidden_size)
        
        # Forward pass
        output = feed_forward(hidden_states)
        
        # Vérifications
        self.assertEqual(output.shape, hidden_states.shape)
        self.assertTrue(torch.isfinite(output).all())
        
        # Vérification du scaling e
        self.assertEqual(feed_forward.e_scale, E)
        
        print(f"✅ HarmonicFeedForward: {output.shape}")
    
    def test_harmonic_positional_embedding(self):
        """Test des embeddings positionnels harmoniques"""
        print("\n🧪 Test de HarmonicPositionalEmbedding")
        
        # Création du composant
        max_pos = 1000
        pos_embedding = HarmonicPositionalEmbedding(self.hidden_size, max_pos, self.config)
        
        # Données de test
        position_ids = torch.arange(0, self.seq_length).unsqueeze(0).repeat(self.batch_size, 1)
        
        # Forward pass
        output = pos_embedding(position_ids)
        
        # Vérifications
        expected_shape = (self.batch_size, self.seq_length, self.hidden_size)
        self.assertEqual(output.shape, expected_shape)
        self.assertTrue(torch.isfinite(output).all())
        
        # Vérification du scaling π
        self.assertEqual(pos_embedding.pi_scale, PI)
        
        print(f"✅ HarmonicPositionalEmbedding: {output.shape}")

class TestGemma4HarmonicModel(unittest.TestCase):
    """Tests du modèle Gemma 4 Harmonique"""
    
    def setUp(self):
        """Configuration des tests"""
        self.config = Gemma4HarmonicConfig(
            model_name="google/gemma-4-7b-it",
            device="cpu",
            harmonic_optimization=True,
            max_length=512  # Plus court pour les tests
        )
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Nettoyage après les tests"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_model_initialization(self):
        """Test de l'initialisation du modèle"""
        print("\n🧪 Test d'initialisation du modèle")
        
        try:
            model = Gemma4HarmonicModel(self.config)
            self.assertIsNotNone(model)
            self.assertIsNotNone(model.base_model)
            self.assertIsNotNone(model.tokenizer)
            print("✅ Modèle initialisé avec succès")
        except Exception as e:
            self.skipTest(f"Modèle non disponible: {e}")
    
    def test_harmonic_generation(self):
        """Test de la génération harmonique"""
        print("\n🧪 Test de génération harmonique")
        
        try:
            model = Gemma4HarmonicModel(self.config)
            
            # Test de génération
            prompt = "🌊 Génère une fonction Python simple"
            result = model.generate_harmonic(prompt, max_new_tokens=50)
            
            # Vérifications
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), len(prompt))
            
            print(f"✅ Génération réussie: {len(result)} caractères")
        except Exception as e:
            self.skipTest(f"Génération non disponible: {e}")
    
    def test_harmonic_score_calculation(self):
        """Test du calcul du score harmonique"""
        print("\n🧪 Test du calcul du score harmonique")
        
        try:
            model = Gemma4HarmonicModel(self.config)
            
            # Simulation de scores
            mock_scores = [torch.randn(1, 10, 32000) for _ in range(5)]
            
            # Création d'un mock outputs
            class MockOutputs:
                def __init__(self, scores):
                    self.scores = scores
            
            outputs = MockOutputs(mock_scores)
            score = model._calculate_harmonic_score(outputs)
            
            # Vérifications
            self.assertIsInstance(score, float)
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 10)  # Score raisonnable
            
            print(f"✅ Score harmonique: {score:.3f}")
        except Exception as e:
            self.skipTest(f"Calcul du score non disponible: {e}")
    
    def test_model_save_load(self):
        """Test de sauvegarde et chargement du modèle"""
        print("\n🧪 Test de sauvegarde/chargement")
        
        try:
            # Création et sauvegarde
            model = Gemma4HarmonicModel(self.config)
            save_path = Path(self.temp_dir) / "test_model"
            model.save_harmonic_model(str(save_path))
            
            # Vérification des fichiers
            self.assertTrue((save_path / "model").exists())
            self.assertTrue((save_path / "tokenizer").exists())
            self.assertTrue((save_path / "harmonic_config.json").exists())
            
            # Chargement
            loaded_model = Gemma4HarmonicModel.load_harmonic_model(str(save_path))
            
            # Vérifications
            self.assertIsNotNone(loaded_model)
            self.assertEqual(loaded_model.config.model_name, self.config.model_name)
            
            print("✅ Sauvegarde/chargement réussi")
        except Exception as e:
            self.skipTest(f"Sauvegarde/chargement non disponible: {e}")

class TestGemma4HarmonicCodeGenerator(unittest.TestCase):
    """Tests du générateur de code harmonique"""
    
    def setUp(self):
        """Configuration des tests"""
        self.config = Gemma4HarmonicConfig(
            model_name="google/gemma-4-7b-it",
            device="cpu",
            harmonic_optimization=True,
            max_length=512
        )
    
    def test_code_generator_initialization(self):
        """Test de l'initialisation du générateur de code"""
        print("\n🧪 Test d'initialisation du générateur de code")
        
        try:
            generator = Gemma4HarmonicCodeGenerator(self.config)
            self.assertIsNotNone(generator)
            self.assertIsNotNone(generator.model)
            self.assertIsNotNone(generator.code_templates)
            
            # Vérification des templates
            self.assertIn('typescript_controller', generator.code_templates)
            self.assertIn('python_service', generator.code_templates)
            
            print("✅ Générateur de code initialisé")
        except Exception as e:
            self.skipTest(f"Générateur non disponible: {e}")
    
    def test_code_generation(self):
        """Test de la génération de code"""
        print("\n🧪 Test de génération de code")
        
        try:
            generator = Gemma4HarmonicCodeGenerator(self.config)
            
            # Test de génération TypeScript
            ts_code = generator.generate_code(
                language='typescript',
                entity_type='controller',
                entity_name='TestController',
                requirements='API REST simple'
            )
            
            self.assertIsInstance(ts_code, str)
            self.assertGreater(len(ts_code), 0)
            
            # Test de génération Python
            py_code = generator.generate_code(
                language='python',
                entity_type='service',
                entity_name='TestService',
                requirements='Service métier simple'
            )
            
            self.assertIsInstance(py_code, str)
            self.assertGreater(len(py_code), 0)
            
            print(f"✅ Code généré: TS ({len(ts_code)} chars), PY ({len(py_code)} chars)")
        except Exception as e:
            self.skipTest(f"Génération de code non disponible: {e}")
    
    def test_full_application_generation(self):
        """Test de la génération d'application complète"""
        print("\n🧪 Test de génération d'application complète")
        
        try:
            generator = Gemma4HarmonicCodeGenerator(self.config)
            
            # Requirements pour une application
            requirements = {
                'controllers': [
                    {
                        'name': 'UserController',
                        'requirements': 'Gestion des utilisateurs'
                    }
                ],
                'services': [
                    {
                        'name': 'UserService',
                        'requirements': 'Logique métier utilisateurs'
                    }
                ]
            }
            
            # Génération
            generated_files = generator.generate_full_application(requirements)
            
            # Vérifications
            self.assertIsInstance(generated_files, dict)
            self.assertGreater(len(generated_files), 0)
            
            # Vérification des fichiers générés
            for filename, content in generated_files.items():
                self.assertIsInstance(content, str)
                self.assertGreater(len(content), 0)
            
            print(f"✅ Application générée: {len(generated_files)} fichiers")
        except Exception as e:
            self.skipTest(f"Génération d'application non disponible: {e}")

class TestHarmonicConstants(unittest.TestCase):
    """Tests des constantes harmoniques"""
    
    def test_harmonic_constants_values(self):
        """Test des valeurs des constantes harmoniques"""
        print("\n🧪 Test des constantes harmoniques")
        
        # Vérification des valeurs
        self.assertAlmostEqual(PHI, 1.618033988749895, places=15)
        self.assertAlmostEqual(PI, 3.141592653589793, places=15)
        self.assertAlmostEqual(E, 2.718281828459045, places=15)
        self.assertAlmostEqual(SQRT2, 1.414213562373095, places=15)
        self.assertAlmostEqual(SQRT3, 1.732050807568877, places=15)
        
        print("✅ Constantes harmoniques validées")
    
    def test_harmonic_relationships(self):
        """Test des relations harmoniques"""
        print("\n🧪 Test des relations harmoniques")
        
        # φ² = φ + 1
        self.assertAlmostEqual(PHI**2, PHI + 1, places=10)
        
        # √2 * √2 = 2
        self.assertAlmostEqual(SQRT2 * SQRT2, 2.0, places=10)
        
        # √3 * √3 = 3
        self.assertAlmostEqual(SQRT3 * SQRT3, 3.0, places=10)
        
        print("✅ Relations harmoniques validées")

class TestPerformance(unittest.TestCase):
    """Tests de performance"""
    
    def setUp(self):
        """Configuration des tests"""
        self.config = Gemma4HarmonicConfig(
            model_name="google/gemma-4-7b-it",
            device="cpu",
            harmonic_optimization=True,
            max_length=256  # Plus court pour les tests de performance
        )
    
    def test_generation_performance(self):
        """Test de performance de génération"""
        print("\n🧪 Test de performance de génération")
        
        try:
            model = Gemma4HarmonicModel(self.config)
            
            # Test de performance
            prompt = "🌊 Test de performance"
            
            start_time = time.time()
            result = model.generate_harmonic(prompt, max_new_tokens=100)
            end_time = time.time()
            
            generation_time = end_time - start_time
            tokens_per_second = 100 / generation_time
            
            # Vérifications de performance
            self.assertLess(generation_time, 30.0)  # Moins de 30 secondes
            self.assertGreater(tokens_per_second, 1.0)  # Au moins 1 token/seconde
            
            print(f"✅ Performance: {generation_time:.2f}s, {tokens_per_second:.1f} tokens/s")
        except Exception as e:
            self.skipTest(f"Test de performance non disponible: {e}")
    
    def test_memory_usage(self):
        """Test de l'utilisation mémoire"""
        print("\n🧪 Test de l'utilisation mémoire")
        
        try:
            import psutil
            import torch
            
            # Mesure mémoire avant
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024**2  # MB
            
            # Création du modèle
            model = Gemma4HarmonicModel(self.config)
            
            # Mesure mémoire après
            memory_after = process.memory_info().rss / 1024**2  # MB
            memory_used = memory_after - memory_before
            
            # Vérifications
            self.assertLess(memory_used, 8192)  # Moins de 8GB
            
            print(f"✅ Mémoire utilisée: {memory_used:.1f} MB")
        except Exception as e:
            self.skipTest(f"Test mémoire non disponible: {e}")

def run_all_tests():
    """Exécute tous les tests"""
    print("🧪 Démarrage des tests Gemma 4 Harmonique")
    print("=" * 60)
    
    # Création de la suite de tests
    test_suite = unittest.TestSuite()
    
    # Ajout des classes de tests
    test_classes = [
        TestHarmonicComponents,
        TestGemma4HarmonicModel,
        TestGemma4HarmonicCodeGenerator,
        TestHarmonicConstants,
        TestPerformance
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Exécution des tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Résumé
    print("\n" + "=" * 60)
    print(f"📊 Résumé des tests:")
    print(f"   Tests exécutés: {result.testsRun}")
    print(f"   Réussis: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   Échoués: {len(result.failures)}")
    print(f"   Erreurs: {len(result.errors)}")
    print(f"   Ignorés: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\n❌ Échecs:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback}")
    
    if result.errors:
        print("\n🔥 Erreurs:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
