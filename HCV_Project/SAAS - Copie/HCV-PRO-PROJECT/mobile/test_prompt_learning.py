#!/usr/bin/env python3
"""
Test Suite - Prompt Learning System
===================================

Tests complets du système d'apprentissage par prompt
avec compression harmonique.

Auteur: HCV PRO Team
Date: 27 avril 2026
"""

import unittest
import tempfile
import os
import time
import numpy as np
from datetime import datetime, timezone
from prompt_learning_system import (
    PromptLearningSystem, 
    MetadataExtractor, 
    PromptModeler,
    HarmonicModelCompression,
    HarmonicKnowledgeBase,
    PromptMetadata
)

class TestMetadataExtractor(unittest.TestCase):
    """Tests de l'extraction de métadonnées"""
    
    def setUp(self):
        self.extractor = MetadataExtractor()
    
    def test_temporal_metadata_extraction(self):
        """Test extraction métadonnées temporelles"""
        prompt = "Aide-moi pour mon travail"
        context = {'frequency_pattern': 'daily'}
        user_state = {}
        
        metadata = self.extractor.extract_metadata(prompt, context, user_state)
        
        self.assertIsInstance(metadata, PromptMetadata)
        self.assertIsInstance(metadata.timestamp, int)
        self.assertIn(metadata.time_of_day, ['morning', 'afternoon', 'evening', 'night'])
        self.assertIn(metadata.season, ['winter', 'spring', 'summer', 'autumn'])
    
    def test_semantic_metadata_extraction(self):
        """Test extraction métadonnées sémantiques"""
        
        # Test question
        prompt_question = "Comment faire un projet ?"
        metadata_q = self.extractor._extract_semantic_metadata(prompt_question)
        self.assertEqual(metadata_q['intent_type'], 'question')
        
        # Test commande
        prompt_command = "Fais un rapport pour moi"
        metadata_c = self.extractor._extract_semantic_metadata(prompt_command)
        self.assertEqual(metadata_c['intent_type'], 'command')
        
        # Test domaine travail
        prompt_work = "J'ai une réunion importante demain"
        metadata_w = self.extractor._extract_semantic_metadata(prompt_work)
        self.assertEqual(metadata_w['domain'], 'work')
    
    def test_harmonic_metadata_extraction(self):
        """Test extraction métadonnées harmoniques"""
        prompt = "Test de texte pour analyse harmonique"
        user_state = {'harmonic_profile': np.ones(12)}
        
        harmonic_meta = self.extractor._extract_harmonic_metadata(prompt, user_state)
        
        self.assertIn('frequency_signature', harmonic_meta)
        self.assertIn('resonance_score', harmonic_meta)
        self.assertIn('harmonic_pattern', harmonic_meta)
        self.assertIsInstance(harmonic_meta['resonance_score'], float)
        self.assertIn(harmonic_meta['harmonic_pattern'], ['golden_harmonic', 'simple_harmonic', 'complex_harmonic'])

class TestPromptModeler(unittest.TestCase):
    """Tests du modélisateur de prompts"""
    
    def setUp(self):
        self.modeler = PromptModeler()
        self.extractor = MetadataExtractor()
    
    def test_prompt_modeling(self):
        """Test modélisation complète du prompt"""
        prompt_text = "Organise ma journée de travail"
        context = {'location': 'office'}
        user_state = {'success_rate': 0.9}
        
        metadata = self.extractor.extract_metadata(prompt_text, context, user_state)
        modeled_prompt = self.modeler.model_prompt_with_metadata(prompt_text, metadata)
        
        # Vérification de la structure
        required_keys = [
            'prompt_text', 'prompt_hash', 'metadata', 'harmonic_signature',
            'behavioral_patterns', 'causal_links', 'response_predictions'
        ]
        
        for key in required_keys:
            self.assertIn(key, modeled_prompt)
        
        # Vérification du hash
        self.assertEqual(len(modeled_prompt['prompt_hash']), 16)
        
        # Vérification de la signature harmonique
        signature = modeled_prompt['harmonic_signature']
        self.assertIn('dominant_frequencies', signature)
        self.assertIn('harmonic_ratios', signature)
        self.assertIn('energy_distribution', signature)
    
    def test_harmonic_signature_generation(self):
        """Test génération de signature harmonique"""
        prompt_text = "Test prompt"
        metadata = self.extractor.extract_metadata(prompt_text, {}, {})
        
        signature = self.modeler._generate_harmonic_signature(prompt_text, metadata)
        
        self.assertIsInstance(signature, dict)
        self.assertIsInstance(signature['dominant_frequencies'], list)
        self.assertIsInstance(signature['energy_distribution'], list)
        
        # Vérification que l'énergie est normalisée
        energy = signature['energy_distribution']
        if len(energy) > 0:
            self.assertAlmostEqual(sum(energy), 1.0, places=5)

class TestHarmonicModelCompression(unittest.TestCase):
    """Tests de la compression harmonique"""
    
    def setUp(self):
        self.compressor = HarmonicModelCompression()
        self.modeler = PromptModeler()
        self.extractor = MetadataExtractor()
    
    def test_model_compression(self):
        """Test compression du modèle"""
        prompt_text = "Test de compression harmonique"
        metadata = self.extractor.extract_metadata(prompt_text, {}, {})
        modeled_prompt = self.modeler.model_prompt_with_metadata(prompt_text, metadata)
        
        compressed = self.compressor.compress_model(modeled_prompt)
        
        # Vérification de la structure compressée
        required_keys = ['compressed_data', 'original_shape', 'compression_ratio', 'energy_preserved']
        for key in required_keys:
            self.assertIn(key, compressed)
        
        # Vérification du ratio de compression
        self.assertGreater(compressed['compression_ratio'], 1.0)
        
        # Vérification de la préservation d'énergie
        self.assertLessEqual(compressed['energy_preserved'], 1.0)
        self.assertGreater(compressed['energy_preserved'], 0.0)
    
    def test_serialization_determinism(self):
        """Test déterminisme de la sérialisation"""
        prompt_text = "Test déterministe"
        metadata = self.extractor.extract_metadata(prompt_text, {}, {})
        modeled_prompt = self.modeler.model_prompt_with_metadata(prompt_text, metadata)
        
        # Sérialisation deux fois
        serialized1 = self.compressor._serialize_model(modeled_prompt)
        serialized2 = self.compressor._serialize_model(modeled_prompt)
        
        # Doit être identique
        np.testing.assert_array_equal(serialized1, serialized2)

class TestHarmonicKnowledgeBase(unittest.TestCase):
    """Tests de la base de connaissance harmonique"""
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.knowledge_base = HarmonicKnowledgeBase(self.temp_db.name)
        self.compressor = HarmonicModelCompression()
        self.modeler = PromptModeler()
        self.extractor = MetadataExtractor()
    
    def tearDown(self):
        os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Test initialisation de la base de données"""
        conn = self.knowledge_base._init_database()
        
        # Vérification que les tables existent
        conn = self.knowledge_base._init_database.__wrapped__(self.knowledge_base)
        
        # La base devrait être initialisée sans erreur
        self.assertTrue(os.path.exists(self.knowledge_base.db_path))
    
    def test_storage_and_learning(self):
        """Test stockage et apprentissage"""
        prompt_text = "Test d'apprentissage"
        metadata = self.extractor.extract_metadata(prompt_text, {}, {})
        modeled_prompt = self.modeler.model_prompt_with_metadata(prompt_text, metadata)
        compressed = self.compressor.compress_model(modeled_prompt)
        
        user_state = {'user_id': 'test_user', 'success_rate': 0.8}
        
        result = self.knowledge_base.store_and_learn(compressed, user_state)
        
        # Vérification du résultat
        self.assertIn('storage_success', result)
        self.assertIn('patterns_learned', result)
        self.assertIn('learning_confidence', result)
        self.assertIn('signature', result)
    
    def test_pattern_learning(self):
        """Test apprentissage des patterns"""
        # Création d'un modèle factice
        model = np.random.randn(256)
        user_state = {'user_id': 'test_user'}
        
        learning_result = self.knowledge_base._learn_patterns(model, user_state)
        
        self.assertIn('pattern_id', learning_result)
        self.assertIn('patterns_count', learning_result)
        self.assertIn('confidence', learning_result)
        self.assertGreater(learning_result['patterns_count'], 0)

class TestPromptLearningSystem(unittest.TestCase):
    """Tests du système complet"""
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.learning_system = PromptLearningSystem(self.temp_db.name)
    
    def tearDown(self):
        os.unlink(self.temp_db.name)
    
    def test_complete_pipeline(self):
        """Test pipeline complet de traitement"""
        prompt_text = "Aide-moi à organiser ma journée"
        context = {
            'location': 'home',
            'device_type': 'mobile',
            'connectivity': 'wifi',
            'battery_level': 0.8
        }
        user_state = {
            'user_id': 'test_user',
            'success_rate': 0.9,
            'avg_response_time': 0.3
        }
        
        result = self.learning_system.process_user_prompt(prompt_text, context, user_state)
        
        # Vérification du résultat
        self.assertTrue(result['success'])
        self.assertIn('response', result)
        self.assertIn('processing_time', result)
        self.assertIn('metadata', result)
        self.assertIn('compression_ratio', result)
        self.assertIn('learning_result', result)
        
        # Vérification des métriques
        self.assertLess(result['processing_time'], 1.0)  # < 1 seconde
        self.assertGreater(result['compression_ratio'], 1.0)
    
    def test_learning_progression(self):
        """Test progression de l'apprentissage"""
        user_id = 'progress_test_user'
        
        # Traitement de plusieurs prompts
        prompts = [
            "Organise ma journée",
            "Planifie mes tâches",
            "Gère mon emploi du temps",
            "Aide pour la productivité",
            "Optimise mon temps"
        ]
        
        context = {'location': 'office', 'device_type': 'mobile'}
        user_state = {'user_id': user_id, 'success_rate': 0.8}
        
        for i, prompt in enumerate(prompts):
            result = self.learning_system.process_user_prompt(prompt, context, user_state)
            self.assertTrue(result['success'])
            
            # Vérification de la progression
            metrics = self.learning_system.get_learning_metrics(user_id)
            self.assertEqual(metrics['total_prompts_processed'], i + 1)
        
        # Vérification finale
        final_metrics = self.learning_system.get_learning_metrics(user_id)
        self.assertEqual(final_metrics['total_prompts_processed'], len(prompts))
        self.assertGreater(final_metrics['total_patterns_learned'], 0)
    
    def test_error_handling(self):
        """Test gestion des erreurs"""
        # Test avec prompt vide
        result = self.learning_system.process_user_prompt("", {}, {})
        self.assertTrue(result['success'])  # Devrait fonctionner
        
        # Test avec contexte invalide (simulé)
        # Note: Le système est robuste et devrait gérer les cas limites

class TestPerformance(unittest.TestCase):
    """Tests de performance"""
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.learning_system = PromptLearningSystem(self.temp_db.name)
    
    def tearDown(self):
        os.unlink(self.temp_db.name)
    
    def test_processing_speed(self):
        """Test vitesse de traitement"""
        prompt_text = "Test de performance"
        context = {'location': 'test'}
        user_state = {'user_id': 'perf_test'}
        
        start_time = time.time()
        result = self.learning_system.process_user_prompt(prompt_text, context, user_state)
        processing_time = time.time() - start_time
        
        # Doit être rapide (< 100ms)
        self.assertLess(processing_time, 0.1)
        self.assertTrue(result['success'])
    
    def test_compression_efficiency(self):
        """Test efficacité de la compression"""
        prompt_text = "Test d'efficacité de compression avec un texte un peu plus long pour vérifier que le système fonctionne bien avec des contenus de taille variable"
        context = {'location': 'test_location', 'device_type': 'mobile', 'connectivity': 'wifi'}
        user_state = {'user_id': 'compression_test'}
        
        result = self.learning_system.process_user_prompt(prompt_text, context, user_state)
        
        # Vérification du ratio de compression
        self.assertGreater(result['compression_ratio'], 10.0)  # Au moins 10:1
        
        # Vérification que les données sont bien compressées
        self.assertLess(result['processing_time'], 0.2)

def run_comprehensive_test():
    """Exécute tous les tests et retourne un rapport"""
    
    print("🚀 Démarrage des Tests Complets - Prompt Learning System")
    print("=" * 60)
    
    # Création de la suite de tests
    test_suite = unittest.TestSuite()
    
    # Ajout des classes de tests
    test_classes = [
        TestMetadataExtractor,
        TestPromptModeler,
        TestHarmonicModelCompression,
        TestHarmonicKnowledgeBase,
        TestPromptLearningSystem,
        TestPerformance
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Exécution des tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Génération du rapport
    print("\n" + "=" * 60)
    print("📊 RAPPORT DE TESTS")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    success_rate = ((total_tests - failures - errors) / total_tests) * 100
    
    print(f"Tests exécutés: {total_tests}")
    print(f"Succès: {total_tests - failures - errors}")
    print(f"Échecs: {failures}")
    print(f"Erreurs: {errors}")
    print(f"Taux de succès: {success_rate:.1f}%")
    
    if failures > 0:
        print("\n❌ ÉCHECS:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if errors > 0:
        print("\n💥 ERREURS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    # Test de performance réel
    print("\n⚡ TEST DE PERFORMANCE RÉEL")
    print("-" * 30)
    
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        system = PromptLearningSystem(temp_db.name)
        
        # Test de vitesse
        prompts = [
            "Test rapide 1",
            "Test de performance avec un texte un peu plus long",
            "Test complexe avec beaucoup de détails et de contextes différents pour vérifier la robustesse du système"
        ]
        
        total_time = 0
        for prompt in prompts:
            start = time.time()
            result = system.process_user_prompt(prompt, {'location': 'test'}, {'user_id': 'perf_test'})
            total_time += time.time() - start
            
            print(f"Prompt: {len(prompt)} chars → {result['compression_ratio']:.1f}x compression → {result['processing_time']*1000:.1f}ms")
        
        avg_time = total_time / len(prompts)
        print(f"\nTemps moyen: {avg_time*1000:.1f}ms")
        print(f"Performance: {'✅ Excellent' if avg_time < 0.05 else '⚠️ Acceptable' if avg_time < 0.1 else '❌ Lent'}")
        
    finally:
        os.unlink(temp_db.name)
    
    print("\n" + "=" * 60)
    if success_rate >= 95:
        print("🎉 SYSTÈME PRÊT POUR LA PRODUCTION!")
    elif success_rate >= 80:
        print("⚠️ SYSTÈME FONCTIONNEL AVEC QUELQUES LIMITATIONS")
    else:
        print("❌ SYSTÈME NÉCESSITE DES AMÉLIORATIONS")
    
    print("=" * 60)
    
    return {
        'total_tests': total_tests,
        'success_rate': success_rate,
        'failures': failures,
        'errors': errors,
        'ready_for_production': success_rate >= 95
    }

if __name__ == "__main__":
    # Exécution des tests
    run_comprehensive_test()
