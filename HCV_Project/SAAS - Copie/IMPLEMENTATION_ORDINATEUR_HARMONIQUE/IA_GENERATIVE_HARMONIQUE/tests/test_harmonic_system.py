"""
🧪 TESTS INTÉGRÉS - SYSTÈME HARMONIQUE
Fichier: test_harmonic_system.py
Auteur: Équipe Harmonique
Date: 29 avril 2026
Description: Tests d'intégration complets pour l'IA générative harmonique
"""

import unittest
import pytest
import numpy as np
import tempfile
import shutil
from pathlib import Path
import json
import time
from unittest.mock import Mock, patch

# Import des modules harmoniques
from harmonic_neural_network import HarmonicNeuralNetwork, ActivationType, OptimizationType
from harmonic_code_generator import HarmonicCodeGenerator
from harmonic_memory_system import HarmonicMemorySystem, MemoryConfig, MemoryType, MemoryPriority
from harmonic_optimization_engine import HarmonicOptimizationEngine, OptimizationConfig, OptimizationTarget, OptimizationType as OptType
from harmonic_user_interface import HarmonicUI, UIConfig, ThemeType, UIType
from prompts.deterministic_ai_prompts import DeterministicPromptEngine
from prompts.claude_code_prompts import ClaudeCodeHarmonicEngine
from prompts.openai_codex_prompts import OpenAICodexHarmonicEngine
from prompts.gemma_4_prompts import Gemma4HarmonicEngine

# Constantes harmoniques universelles
PHI = 1.618033988749895
PI = 3.141592653589793
E = 2.718281828459045
SQRT2 = 1.414213562373095
SQRT3 = 1.732050807568877

class TestHarmonicConstants:
    """Tests des constantes harmoniques"""
    
    def test_phi_value(self):
        """Test de la valeur de phi"""
        assert abs(PHI - 1.618033988749895) < 1e-15
        assert PHI > 1.6 and PHI < 1.62
    
    def test_pi_value(self):
        """Test de la valeur de pi"""
        assert abs(PI - 3.141592653589793) < 1e-15
        assert PI > 3.14 and PI < 3.15
    
    def test_e_value(self):
        """Test de la valeur de e"""
        assert abs(E - 2.718281828459045) < 1e-15
        assert E > 2.71 and E < 2.72
    
    def test_sqrt2_value(self):
        """Test de la valeur de sqrt2"""
        assert abs(SQRT2 - 1.414213562373095) < 1e-15
        assert SQRT2 > 1.41 and SQRT2 < 1.42
    
    def test_sqrt3_value(self):
        """Test de la valeur de sqrt3"""
        assert abs(SQRT3 - 1.732050807568877) < 1e-15
        assert SQRT3 > 1.73 and SQRT3 < 1.74
    
    def test_harmonic_relationships(self):
        """Test des relations harmoniques"""
        # Test de la relation φ² = φ + 1
        assert abs(PHI**2 - PHI - 1) < 1e-15
        
        # Test de la relation π ≈ 3.14159
        assert abs(PI - 3.1415926535) < 1e-7
        
        # Test de la relation e ≈ 2.71828
        assert abs(E - 2.7182818284) < 1e-7

class TestHarmonicNeuralNetwork:
    """Tests du réseau neuronal harmonique"""
    
    def setup_method(self):
        """Configuration des tests"""
        self.network = HarmonicNeuralNetwork(
            layers=[64, 32, 16],
            activation=ActivationType.HARMONIC_SIGMOID,
            optimization=OptimizationType.PHI_ADAM
        )
    
    def test_network_initialization(self):
        """Test de l'initialisation du réseau"""
        assert len(self.network.layers) == 2
        assert self.network.layers[0].input_size == 64
        assert self.network.layers[1].input_size == 32
        assert self.network.layers[1].output_size == 16
    
    def test_forward_propagation(self):
        """Test de la propagation avant"""
        x = np.random.randn(10, 64)
        output = self.network.forward(x)
        
        assert output.shape == (10, 16)
        assert np.all(np.isfinite(output))
    
    def test_backward_propagation(self):
        """Test de la rétropropagation"""
        x = np.random.randn(5, 64)
        y = np.random.randn(5, 16)
        
        # Propagation avant
        output = self.network.forward(x)
        
        # Calcul du gradient
        gradient = (output - y) / y.shape[0]
        
        # Rétropropagation
        self.network.backward(gradient, 0.01)
        
        # Vérification que les poids ont été modifiés
        initial_weights = self.network.layers[0].neurons[0].weights.copy()
        self.network.forward(x)  # Nouvelle propagation pour mettre à jour les poids
        updated_weights = self.network.layers[0].neurons[0].weights
        
        assert not np.array_equal(initial_weights, updated_weights)
    
    def test_harmonic_optimization(self):
        """Test de l'optimisation harmonique"""
        # Données de test
        X = np.random.randn(100, 64)
        y = np.random.randn(100, 16)
        
        # Entraînement
        results = self.network.train_harmonic(X, y, epochs=10, learning_rate=0.01)
        
        assert 'training_time' in results
        assert 'final_loss' in results
        assert 'metrics' in results
        assert results['training_time'] > 0
        assert results['final_loss'] >= 0
        assert results['metrics']['harmonic_score'] >= 0
    
    def test_determinism(self):
        """Test du déterminisme du réseau"""
        x = np.array([[1.0, 2.0], [3.0, 4.0]])
        
        # Première exécution
        output1 = self.network.forward(x)
        
        # Deuxième exécution
        output2 = self.network.forward(x)
        
        # Les sorties doivent être identiques
        np.testing.assert_array_equal(output1, output2)
    
    def test_harmonic_constants_usage(self):
        """Test de l'utilisation des constantes harmoniques"""
        neuron = self.network.layers[0].neurons[0]
        
        assert hasattr(neuron, 'phi')
        assert hasattr(neuron, 'pi')
        assert hasattr(neuron, 'e')
        assert hasattr(neuron, 'sqrt2')
        assert hasattr(neuron, 'sqrt3')
        
        assert neuron.phi == PHI
        assert neuron.pi == PI
        assert neuron.e == E
        assert neuron.sqrt2 == SQRT2
        assert neuron.sqrt3 == SQRT3

class TestHarmonicCodeGenerator:
    """Tests du générateur de code harmonique"""
    
    def setup_method(self):
        """Configuration des tests"""
        self.generator = HarmonicCodeGenerator()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Nettoyage après les tests"""
        shutil.rmtree(self.temp_dir)
    
    def test_generator_initialization(self):
        """Test de l'initialisation du générateur"""
        assert self.generator is not None
        assert hasattr(self.generator, 'phi')
        assert hasattr(self.generator, 'pi')
        assert hasattr(self.generator, 'e')
        assert hasattr(self.generator, 'sqrt2')
        assert hasattr(self.generator, 'sqrt3')
    
    def test_code_generation(self):
        """Test de la génération de code"""
        from harmonic_code_generator import CodeRequirements
        
        requirements = CodeRequirements(
            service_name="TestService",
            description="Service de test harmonique",
            endpoints=[],
            database_schema={},
            business_logic=[],
            validation_rules=[]
        )
        
        generated_files = self.generator.generate_full_application(requirements, self.temp_dir)
        
        assert len(generated_files) > 0
        assert all(Path(file_path).exists() for file_path in generated_files.values())
    
    def test_harmonic_code_quality(self):
        """Test de la qualité du code généré"""
        from harmonic_code_generator import CodeRequirements
        
        requirements = CodeRequirements(
            service_name="QualityTest",
            description="Test de qualité harmonique",
            endpoints=[],
            database_schema={},
            business_logic=[],
            validation_rules=[]
        )
        
        generated_files = self.generator.generate_full_application(requirements, self.temp_dir)
        
        # Vérification que le code contient les constantes harmoniques
        for file_path in generated_files.values():
            with open(file_path, 'r') as f:
                content = f.read()
                
                # Le code généré doit contenir des références harmoniques
                assert 'phi' in content.lower() or 'pi' in content.lower()
                assert 'harmonic' in content.lower()
    
    def test_deterministic_generation(self):
        """Test de la génération déterministe"""
        from harmonic_code_generator import CodeRequirements
        
        requirements = CodeRequirements(
            service_name="DeterministicTest",
            description="Test de déterminisme",
            endpoints=[],
            database_schema={},
            business_logic=[],
            validation_rules=[]
        )
        
        # Génération deux fois
        generated_files1 = self.generator.generate_full_application(requirements, self.temp_dir)
        generated_files2 = self.generator.generate_full_application(requirements, self.temp_dir)
        
        # Les fichiers générés doivent être identiques
        for file_path1, file_path2 in zip(generated_files1.values(), generated_files2.values()):
            with open(file_path1, 'r') as f1, open(file_path2, 'r') as f2:
                content1 = f1.read()
                content2 = f2.read()
                assert content1 == content2

class TestHarmonicMemorySystem:
    """Tests du système de mémoire harmonique"""
    
    def setup_method(self):
        """Configuration des tests"""
        self.config = MemoryConfig(
            max_entries=100,
            max_working_memory=10,
            cache_size=50,
            persistence_enabled=False  # Désactivé pour les tests
        )
        self.memory = HarmonicMemorySystem(self.config)
    
    def test_memory_initialization(self):
        """Test de l'initialisation de la mémoire"""
        assert self.memory is not None
        assert hasattr(self.memory, 'phi')
        assert hasattr(self.memory, 'pi')
        assert hasattr(self.memory, 'e')
        assert hasattr(self.memory, 'sqrt2')
        assert hasattr(self.memory, 'sqrt3')
    
    def test_memory_storage(self):
        """Test du stockage en mémoire"""
        content = "Test content harmonique"
        
        entry_id = self.memory.store(
            content=content,
            memory_type=MemoryType.EPISODIC,
            priority=MemoryPriority.HIGH
        )
        
        assert entry_id is not None
        assert len(entry_id) > 0
        
        # Vérification que l'entrée a été stockée
        retrieved_entry = self.memory.get(entry_id)
        assert retrieved_entry is not None
        assert retrieved_entry.content == content
    
    def test_memory_retrieval(self):
        """Test de la récupération de mémoire"""
        # Stockage de plusieurs entrées
        contents = [
            "Content 1 - φ optimized",
            "Content 2 - π precise",
            "Content 3 - e efficient",
            "Content 4 - √2 stable",
            "Content 5 - √3 balanced"
        ]
        
        entry_ids = []
        for content in contents:
            entry_id = self.memory.store(content=content)
            entry_ids.append(entry_id)
        
        # Récupération
        results = self.memory.retrieve("φ", limit=5)
        
        assert len(results) > 0
        assert all(hasattr(result, 'id') for result in results)
    
    def test_harmonic_scoring(self):
        """Test du scoring harmonique"""
        content = "High quality harmonic content"
        
        entry_id = self.memory.store(
            content=content,
            memory_type=MemoryType.SEMANTIC,
            priority=MemoryPriority.CRITICAL
        )
        
        entry = self.memory.get(entry_id)
        
        assert entry.harmonic_score > 0
        assert entry.harmonic_score <= 1.0
    
    def test_memory_statistics(self):
        """Test des statistiques de mémoire"""
        stats = self.memory.get_statistics()
        
        assert 'total_entries' in stats
        assert 'type_distribution' in stats
        assert 'priority_distribution' in stats
        assert 'average_harmonic_score' in stats
        assert 'working_memory_usage' in stats
        assert 'cache_usage' in stats
        
        assert stats['total_entries'] >= 0
        assert 0 <= stats['average_harmonic_score'] <= 1.0
    
    def test_deterministic_memory(self):
        """Test du déterminisme de la mémoire"""
        content = "Deterministic test content"
        
        # Stockage
        entry_id1 = self.memory.store(content=content)
        
        # Récupération multiple fois
        results = []
        for _ in range(5):
            result = self.memory.get(entry_id1)
            results.append(result)
        
        # Tous les résultats doivent être identiques
        for i in range(1, len(results)):
            assert results[i].content == results[0].content
            assert results[i].harmonic_score == results[0].harmonic_score

class TestHarmonicOptimizationEngine:
    """Tests du moteur d'optimisation harmonique"""
    
    def setup_method(self):
        """Configuration des tests"""
        self.config = OptimizationConfig(
            max_iterations=50,  # Réduit pour les tests
            population_size=10,
            parallel_workers=2
        )
        self.engine = HarmonicOptimizationEngine(self.config)
    
    def test_engine_initialization(self):
        """Test de l'initialisation du moteur"""
        assert self.engine is not None
        assert hasattr(self.engine, 'phi')
        assert hasattr(self.engine, 'pi')
        assert hasattr(self.engine, 'e')
        assert hasattr(self.engine, 'sqrt2')
        assert hasattr(self.engine, 'sqrt3')
    
    def test_optimization_targets(self):
        """Test de l'optimisation des cibles"""
        targets = [
            OptimizationTarget(
                name="phi_target",
                current_value=1.0,
                target_value=PHI,
                optimization_type=OptType.PHI_PERFORMANCE
            ),
            OptimizationTarget(
                name="pi_target",
                current_value=3.0,
                target_value=PI,
                optimization_type=OptType.PI_PRECISION
            )
        ]
        
        result = self.engine.optimize_targets(targets)
        
        assert result is not None
        assert result.improvement >= 0
        assert result.harmonic_score >= 0
        assert result.iterations > 0
        assert result.optimization_time > 0
    
    def test_harmonic_optimization(self):
        """Test de l'optimisation harmonique complète"""
        targets = [
            OptimizationTarget(
                name="harmonic_full",
                current_value=1.0,
                target_value=PHI,
                optimization_type=OptType.HARMONIC_FULL
            )
        ]
        
        result = self.engine.optimize_harmonic_full(targets)
        
        assert result is not None
        assert result.improvement > 0
        assert result.harmonic_score > 0
    
    def test_parallel_optimization(self):
        """Test de l'optimisation parallèle"""
        target_groups = [
            [OptimizationTarget("target1", 1.0, PHI)],
            [OptimizationTarget("target2", 2.0, PI)]
        ]
        
        results = self.engine.optimize_parallel(target_groups)
        
        assert len(results) == 2
        assert all(result.improvement >= 0 for result in results)
    
    def test_optimization_statistics(self):
        """Test des statistiques d'optimisation"""
        # Exécution d'une optimisation pour avoir des données
        targets = [OptimizationTarget("test", 1.0, PHI)]
        self.engine.optimize_targets(targets)
        
        stats = self.engine.get_optimization_report()
        
        assert 'summary' in stats
        assert 'statistics' in stats
        assert 'global_metrics' in stats
        assert 'recommendations' in stats
        
        assert stats['summary']['total_optimizations'] >= 1

class TestHarmonicUI:
    """Tests de l'interface utilisateur harmonique"""
    
    def setup_method(self):
        """Configuration des tests"""
        self.config = UIConfig(
            ui_type=UIType.COMMAND_LINE,  # Pour les tests
            theme=ThemeType.HARMONIC_FULL,
            auto_refresh=False,  # Désactivé pour les tests
            show_advanced_options=False
        )
        self.ui = HarmonicUI(self.config)
    
    def test_ui_initialization(self):
        """Test de l'initialisation de l'interface"""
        assert self.ui is not None
        assert hasattr(self.ui, 'phi')
        assert hasattr(self.ui, 'pi')
        assert hasattr(self.ui, 'e')
        assert hasattr(self.ui, 'sqrt2')
        assert hasattr(self.ui, 'sqrt3')
    
    def test_theme_application(self):
        """Test de l'application du thème"""
        theme = self.ui.theme
        
        assert theme is not None
        assert hasattr(theme, 'colors')
        assert hasattr(theme, 'typography')
        assert hasattr(theme, 'spacing')
        assert hasattr(theme, 'animations')
        
        # Vérification des couleurs harmoniques
        colors = theme.colors
        assert 'primary' in colors
        assert 'secondary' in colors
        assert 'accent' in colors
        assert 'background' in colors
        assert 'surface' in colors
        assert 'text' in colors
    
    def test_visualizer_creation(self):
        """Test de la création du visualiseur"""
        visualizer = self.ui.visualizer
        
        assert visualizer is not None
        assert hasattr(visualizer, 'phi')
        assert hasattr(visualizer, 'pi')
        assert hasattr(visualizer, 'e')
        assert hasattr(visualizer, 'sqrt2')
        assert hasattr(visualizer, 'sqrt3')
    
    def test_state_management(self):
        """Test de la gestion de l'état"""
        initial_state = self.ui.get_state()
        
        # Ajout d'une notification
        self.ui.add_notification("Test notification", "info")
        
        updated_state = self.ui.get_state()
        
        assert len(updated_state['notifications']) > len(initial_state['notifications'])
        
        # Mise à jour de l'état
        self.ui.update_state('test_key', 'test_value')
        
        final_state = self.ui.get_state()
        assert final_state['test_key'] == 'test_value'
    
    def test_harmonic_visualizations(self):
        """Test des visualisations harmoniques"""
        # Données de test
        metrics_data = {
            'timestamps': [f"2023-{i:02d}" for i in range(10)],
            'phi_performance': [PHI + 0.1 * np.sin(i) for i in range(10)],
            'pi_precision': [PI + 0.01 * np.cos(i) for i in range(10)],
            'e_efficiency': [E + 0.2 * np.sin(i/2) for i in range(10)],
            'harmonic_score': [0.973 + 0.05 * np.cos(i/3) for i in range(10)]
        }
        
        # Test du tableau de bord
        fig1 = self.ui.visualizer.create_performance_dashboard(metrics_data)
        assert fig1 is not None
        
        # Test du radar harmonique
        scores = {
            'phi_performance': 0.95,
            'pi_precision': 0.92,
            'e_efficiency': 0.88,
            'sqrt2_stability': 0.96,
            'sqrt3_balance': 0.91
        }
        
        fig2 = self.ui.visualizer.create_harmonic_radar(scores)
        assert fig2 is not None
        
        # Test de la progression d'optimisation
        iterations = list(range(1, 51))
        scores_progress = [0.5 + 0.4 * (1 - np.exp(-i/20)) for i in iterations]
        
        fig3 = self.ui.visualizer.create_optimization_progress(iterations, scores_progress)
        assert fig3 is not None

class TestPromptEngines:
    """Tests des moteurs de prompts"""
    
    def test_deterministic_engine(self):
        """Test du moteur déterministe"""
        engine = DeterministicPromptEngine()
        
        assert engine is not None
        assert len(engine.get_available_prompts()) > 0
        
        # Test d'exécution d'un prompt
        variables = {
            'language': 'typescript',
            'service_name': 'TestService',
            'framework': 'nestjs'
        }
        
        result = engine.execute_prompt('harmonic_code_generation', variables)
        
        assert result is not None
        assert 'execution_time' in result
        assert 'determinism_score' in result
        assert 'harmonic_score' in result
        assert 'processed_response' in result
    
    def test_claude_engine(self):
        """Test du moteur Claude"""
        engine = ClaudeCodeHarmonicEngine()
        
        assert engine is not None
        assert len(engine.get_available_prompts()) > 0
        
        # Test d'exécution
        variables = {
            'language': 'typescript',
            'service_name': 'ClaudeTest',
            'framework': 'nestjs'
        }
        
        result = engine.execute_claude_prompt('harmonic_code_generation', variables)
        
        assert result is not None
        assert 'execution_time' in result
        assert 'determinism_score' in result
        assert 'harmonic_score' in result
        assert 'processed_response' in result
    
    def test_openai_engine(self):
        """Test du moteur OpenAI"""
        engine = OpenAICodexHarmonicEngine()
        
        assert engine is not None
        assert len(engine.get_available_prompts()) > 0
        
        # Test d'exécution
        variables = {
            'language': 'typescript',
            'service_name': 'OpenAITest',
            'framework': 'nestjs'
        }
        
        result = engine.execute_codex_prompt('harmonic_code_generation', variables)
        
        assert result is not None
        assert 'execution_time' in result
        assert 'determinism_score' in result
        assert 'harmonic_score' in result
        assert 'processed_response' in result
    
    def test_gemma_engine(self):
        """Test du moteur Gemma"""
        engine = Gemma4HarmonicEngine()
        
        assert engine is not None
        assert len(engine.get_available_prompts()) > 0
        
        # Test d'exécution
        variables = {
            'language': 'typescript',
            'service_name': 'GemmaTest',
            'framework': 'nestjs'
        }
        
        result = engine.execute_gemma_prompt('harmonic_code_generation', variables)
        
        assert result is not None
        assert 'execution_time' in result
        assert 'determinism_score' in result
        assert 'harmonic_score' in result
        assert 'processed_response' in result

class TestIntegration:
    """Tests d'intégration complets"""
    
    def setup_method(self):
        """Configuration des tests d'intégration"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Configuration de tous les composants
        self.memory_config = MemoryConfig(
            max_entries=100,
            persistence_enabled=False
        )
        self.memory = HarmonicMemorySystem(self.memory_config)
        
        self.optimization_config = OptimizationConfig(
            max_iterations=20,
            population_size=5
        )
        self.optimization = HarmonicOptimizationEngine(self.optimization_config)
        
        self.network = HarmonicNeuralNetwork(
            layers=[32, 16, 8],
            activation=ActivationType.HARMONIC_SIGMOID
        )
        
        self.generator = HarmonicCodeGenerator()
    
    def teardown_method(self):
        """Nettoyage après les tests"""
        shutil.rmtree(self.temp_dir)
        self.memory.close()
        self.optimization.close()
    
    def test_end_to_end_workflow(self):
        """Test du workflow de bout en bout"""
        # 1. Stockage en mémoire
        content = "Test content for end-to-end workflow"
        memory_id = self.memory.store(content, MemoryType.EPISODIC)
        
        # 2. Récupération depuis la mémoire
        retrieved = self.memory.retrieve("Test", limit=1)
        assert len(retrieved) > 0
        
        # 3. Optimisation
        targets = [OptimizationTarget("test", 1.0, PHI)]
        opt_result = self.optimization.optimize_targets(targets)
        assert opt_result.improvement >= 0
        
        # 4. Entraînement du réseau neuronal
        X = np.random.randn(10, 32)
        y = np.random.randn(10, 8)
        train_result = self.network.train_harmonic(X, y, epochs=5)
        assert train_result['training_time'] > 0
        
        # 5. Génération de code
        from harmonic_code_generator import CodeRequirements
        requirements = CodeRequirements(
            service_name="IntegrationTest",
            description="Test d'intégration"
        )
        
        # Mock de la génération pour éviter les dépendances externes
        with patch.object(self.generator, 'generate_full_application') as mock_generate:
            mock_generate.return_value = {"test.py": "test code"}
            code_files = self.generator.generate_full_application(requirements, self.temp_dir)
        
        assert len(code_files) > 0
    
    def test_harmonic_constants_integration(self):
        """Test de l'intégration des constantes harmoniques"""
        # Vérification que tous les composants utilisent les mêmes constantes
        components = [
            self.memory,
            self.optimization,
            self.network,
            self.generator
        ]
        
        for component in components:
            assert hasattr(component, 'phi')
            assert component.phi == PHI
            assert hasattr(component, 'pi')
            assert component.pi == PI
            assert hasattr(component, 'e')
            assert component.e == E
            assert hasattr(component, 'sqrt2')
            assert component.sqrt2 == SQRT2
            assert hasattr(component, 'sqrt3')
            assert component.sqrt3 == SQRT3
    
    def test_determinism_across_components(self):
        """Test du déterminisme à travers tous les composants"""
        # Test de la mémoire
        content = "Determinism test content"
        memory_id1 = self.memory.store(content)
        memory_id2 = self.memory.store(content)
        
        entry1 = self.memory.get(memory_id1)
        entry2 = self.memory.get(memory_id2)
        
        # Les scores harmoniques doivent être cohérents
        assert abs(entry1.harmonic_score - entry2.harmonic_score) < 0.1
        
        # Test du réseau neuronal
        x = np.array([[1.0, 2.0]])
        output1 = self.network.forward(x)
        output2 = self.network.forward(x)
        
        np.testing.assert_array_equal(output1, output2)
    
    def test_performance_benchmarks(self):
        """Test des benchmarks de performance"""
        import time
        
        # Benchmark de la mémoire
        start_time = time.time()
        for i in range(100):
            self.memory.store(f"Content {i}")
        memory_time = time.time() - start_time
        
        # Benchmark du réseau neuronal
        x = np.random.randn(10, 32)
        start_time = time.time()
        for _ in range(10):
            self.network.forward(x)
        network_time = time.time() - start_time
        
        # Benchmark de l'optimisation
        targets = [OptimizationTarget("perf", 1.0, PHI)]
        start_time = time.time()
        self.optimization.optimize_targets(targets)
        opt_time = time.time() - start_time
        
        # Vérification des performances
        assert memory_time < 1.0  # 100 opérations en < 1s
        assert network_time < 0.5  # 10 propagations en < 0.5s
        assert opt_time < 5.0     # 1 optimisation en < 5s
        
        print(f"Performance benchmarks:")
        print(f"  Memory (100 ops): {memory_time:.3f}s")
        print(f"  Network (10 forward): {network_time:.3f}s")
        print(f"  Optimization (1 target): {opt_time:.3f}s")

# Test runner
if __name__ == "__main__":
    # Configuration des tests
    pytest.main([__file__], verbosity=2)
