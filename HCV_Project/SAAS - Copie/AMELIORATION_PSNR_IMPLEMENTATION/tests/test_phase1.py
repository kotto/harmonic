"""
🧪 Tests Unitaires - Phase 1
Tests complets pour valider l'implémentation Phase 1
"""

import unittest
import numpy as np
import sys
import os
from pathlib import Path

# Ajout du chemin src au PYTHONPATH
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from precision.extended_precision import ExtendedPrecision, KahanSummation, CompensatedSummation
from optimization.critical_optimization import CriticalOptimization, MemoryOptimizer
from core.harmonic_compression import HarmonicCompressor
from utils.psnr_calculator import PSNRCalculator


class TestExtendedPrecision(unittest.TestCase):
    """Tests pour le module de précision étendue"""
    
    def setUp(self):
        """Configuration des tests"""
        self.ep = ExtendedPrecision(128)
        self.test_signal = np.array([1.0, 2.0, 3.0, 4.0, 5.0], dtype=np.float64)
    
    def test_harmonic_constants(self):
        """Test des constantes harmoniques"""
        self.assertIn('phi', self.ep.harmonic_constants)
        self.assertIn('pi', self.ep.harmonic_constants)
        self.assertIn('e', self.ep.harmonic_constants)
        
        # Test de la valeur de phi
        phi = self.ep.harmonic_constants['phi']
        self.assertAlmostEqual(float(phi), 1.6180339887498948, places=10)
    
    def test_to_mp_conversion(self):
        """Test de conversion vers mpmath"""
        # Test avec float
        mp_val = self.ep.to_mp(3.14159)
        self.assertIsNotNone(mp_val)
        
        # Test avec numpy array
        mp_array = self.ep.to_mp(self.test_signal)
        self.assertEqual(len(mp_array), len(self.test_signal))
        
        # Test avec mpmath (devrait retourner la même valeur)
        mp_original = self.ep.to_mp(mp.mpf('2.718'))
        self.assertEqual(mp_original, mp.mpf('2.718'))
    
    def test_harmonic_projection(self):
        """Test de la projection harmonique"""
        coefficients = self.ep.harmonic_projection(self.test_signal)
        
        # Vérifier que nous avons 7 coefficients
        self.assertEqual(len(coefficients), 7)
        
        # Vérifier que tous les coefficients sont des nombres
        for name, coeff in coefficients.items():
            self.assertIsInstance(coeff, (int, float))
    
    def test_reconstruction(self):
        """Test de la reconstruction"""
        coefficients = self.ep.harmonic_projection(self.test_signal)
        reconstructed = self.ep.reconstruct_signal(coefficients, len(self.test_signal))
        
        # Vérifier la forme
        self.assertEqual(len(reconstructed), len(self.test_signal))
        
        # Vérifier le type
        self.assertEqual(reconstructed.dtype, np.float128)
    
    def test_kahan_summation(self):
        """Test de la sommation de Kahan"""
        # Test avec des valeurs qui causent des erreurs d'arrondi
        values = [1e-15, 1e15, -1e15, 1e-15]
        
        normal_sum = sum(values)
        kahan_sum = KahanSummation.kahan_sum(values)
        kahan_sum_128 = KahanSummation.kahan_sum_128(values)
        
        # La sommation de Kahan devrait être plus précise
        self.assertNotEqual(normal_sum, kahan_sum)
        self.assertNotEqual(normal_sum, kahan_sum_128)
    
    def test_compensated_summation(self):
        """Test de la sommation compensée"""
        terms = [(1.0, 2.0), (3.0, 4.0), (5.0, 6.0)]
        
        normal_sum = sum(coeff * val for coeff, val in terms)
        compensated_sum = CompensatedSummation.compensated_sum(terms)
        compensated_sum_128 = CompensatedSummation.compensated_sum_128(terms)
        
        # Vérifier que les résultats sont cohérents
        self.assertAlmostEqual(normal_sum, compensated_sum, places=10)
        self.assertAlmostEqual(normal_sum, compensated_sum_128, places=10)


class TestCriticalOptimization(unittest.TestCase):
    """Tests pour le module d'optimisation critique"""
    
    def setUp(self):
        """Configuration des tests"""
        self.ep = ExtendedPrecision(128)
        self.optimizer = CriticalOptimization(self.ep)
        self.test_signal = np.random.randn(1000).astype(np.float64)
    
    def test_optimized_dot_product_64(self):
        """Test du produit scalaire optimisé 64-bit"""
        harmonic = 1.6180339887498948
        
        # Comparaison avec numpy.dot
        numpy_result = np.dot(self.test_signal, harmonic)
        optimized_result = self.optimizer.optimized_dot_product_64(self.test_signal, harmonic)
        
        # Les résultats devraient être très proches
        self.assertAlmostEqual(numpy_result, optimized_result, places=10)
    
    def test_optimized_dot_product_128(self):
        """Test du produit scalaire optimisé 128-bit"""
        harmonic = 1.6180339887498948
        
        result = self.optimizer.optimized_dot_product_128(self.test_signal, harmonic)
        
        # Vérifier le type
        self.assertEqual(result.dtype, np.float128)
        
        # Vérifier que c'est un nombre valide
        self.assertFalse(np.isnan(result))
        self.assertFalse(np.isinf(result))
    
    def test_optimized_harmonic_projection(self):
        """Test de la projection harmonique optimisée"""
        coefficients = self.optimizer.optimized_harmonic_projection(self.test_signal)
        
        # Vérifier que nous avons 7 coefficients
        self.assertEqual(len(coefficients), 7)
        
        # Vérifier que tous les coefficients sont valides
        for name, coeff in coefficients.items():
            self.assertFalse(np.isnan(coeff))
            self.assertFalse(np.isinf(coeff))
    
    def test_optimized_coefficient_computation(self):
        """Test du calcul optimisé des coefficients"""
        coefficients = self.optimizer.optimized_coefficient_computation(self.test_signal)
        
        # Vérifier que nous avons 7 coefficients
        self.assertEqual(len(coefficients), 7)
        
        # Vérifier que tous les coefficients sont valides
        for name, coeff in coefficients.items():
            self.assertIsInstance(coeff, (int, float))
            self.assertFalse(np.isnan(coeff))
            self.assertFalse(np.isinf(coeff))
    
    def test_optimized_reconstruction(self):
        """Test de la reconstruction optimisée"""
        coefficients = self.optimizer.optimized_harmonic_projection(self.test_signal)
        reconstructed = self.optimizer.optimized_reconstruction(coefficients, len(self.test_signal))
        
        # Vérifier la forme
        self.assertEqual(len(reconstructed), len(self.test_signal))
        
        # Vérifier le type
        self.assertEqual(reconstructed.dtype, np.float128)
        
        # Vérifier que tous les valeurs sont valides
        self.assertFalse(np.any(np.isnan(reconstructed)))
        self.assertFalse(np.any(np.isinf(reconstructed)))
    
    def test_memory_optimization(self):
        """Test de l'optimisation mémoire"""
        large_signal = np.random.randn(10000)
        
        chunks = MemoryOptimizer.memory_efficient_processing(large_signal, chunk_size=1024)
        
        # Vérifier que nous avons des chunks
        self.assertGreater(len(chunks), 0)
        
        # Vérifier que la taille totale est préservée
        total_size = sum(len(chunk) for chunk in chunks)
        self.assertEqual(total_size, len(large_signal))
    
    def test_benchmark_optimization(self):
        """Test du benchmark d'optimisation"""
        stats = self.optimizer.benchmark_optimization(self.test_signal, iterations=10)
        
        # Vérifier que nous avons les statistiques attendues
        required_keys = ['standard_time', 'optimized_time', 'speedup', 'iterations_per_second']
        for key in required_keys:
            self.assertIn(key, stats)
        
        # Vérifier que l'accélération est positive
        self.assertGreater(stats['speedup'], 0)


class TestHarmonicCompressor(unittest.TestCase):
    """Tests pour le compresseur harmonique"""
    
    def setUp(self):
        """Configuration des tests"""
        self.compressor = HarmonicCompressor(precision_bits=128)
        self.test_signal = np.random.randn(1000).astype(np.float64)
    
    def test_encode_decode_roundtrip(self):
        """Test du cycle complet encodage/décodage"""
        # Encodage
        compressed = self.compressor.encode(self.test_signal)
        
        # Vérification des données compressées
        self.assertIn('coefficients', compressed)
        self.assertIn('high_precision', compressed)
        self.assertIn('metadata', compressed)
        
        # Décodage
        reconstructed = self.compressor.decode(compressed)
        
        # Vérification du signal reconstruit
        self.assertEqual(reconstructed.shape, self.test_signal.shape)
        self.assertFalse(np.any(np.isnan(reconstructed)))
        self.assertFalse(np.any(np.isinf(reconstructed)))
    
    def test_compression_stats(self):
        """Test des statistiques de compression"""
        compressed = self.compressor.encode(self.test_signal)
        stats = self.compressor.get_compression_stats()
        
        # Vérification des statistiques
        required_keys = ['original_size', 'compressed_size', 'compression_ratio', 'encoding_time']
        for key in required_keys:
            self.assertIn(key, stats)
        
        # Vérification des valeurs
        self.assertGreater(stats['original_size'], 0)
        self.assertGreater(stats['compressed_size'], 0)
        self.assertGreater(stats['compression_ratio'], 0)
        self.assertGreater(stats['encoding_time'], 0)
    
    def test_psnr_calculation(self):
        """Test du calcul PSNR"""
        compressed = self.compressor.encode(self.test_signal)
        reconstructed = self.compressor.decode(compressed)
        
        psnr = self.compressor.calculate_psnr(self.test_signal, reconstructed)
        
        # Le PSNR doit être un nombre valide
        self.assertIsInstance(psnr, (int, float))
        self.assertFalse(np.isnan(psnr))
        self.assertGreaterEqual(psnr, 0)  # PSNR ne peut pas être négatif
    
    def test_ssim_calculation(self):
        """Test du calcul SSIM"""
        compressed = self.compressor.encode(self.test_signal)
        reconstructed = self.compressor.decode(compressed)
        
        ssim = self.compressor.calculate_ssim(self.test_signal, reconstructed)
        
        # Le SSIM doit être un nombre valide entre 0 et 1
        self.assertIsInstance(ssim, (int, float))
        self.assertFalse(np.isnan(ssim))
        self.assertGreaterEqual(ssim, 0)
        self.assertLessEqual(ssim, 1)
    
    def test_error_handling(self):
        """Test de la gestion des erreurs"""
        # Signal vide
        with self.assertRaises(ValueError):
            self.compressor.encode(np.array([]))
        
        # Type incorrect
        with self.assertRaises(ValueError):
            self.compressor.encode("not an array")
        
        # Données compressées invalides
        with self.assertRaises(ValueError):
            self.compressor.decode("not a dict")
        
        with self.assertRaises(ValueError):
            self.compressor.decode({})
    
    def test_benchmark_compression(self):
        """Test du benchmark de compression"""
        stats = self.compressor.benchmark_compression(self.test_signal, iterations=5)
        
        # Vérification des statistiques
        required_keys = ['iterations', 'avg_psnr', 'avg_ssim', 'avg_compression_ratio']
        for key in required_keys:
            self.assertIn(key, stats)
        
        # Vérification des valeurs
        self.assertEqual(stats['iterations'], 5)
        self.assertGreater(stats['avg_psnr'], 0)
        self.assertGreaterEqual(stats['avg_ssim'], 0)
        self.assertLessEqual(stats['avg_ssim'], 1)
        self.assertGreater(stats['avg_compression_ratio'], 0)


class TestPSNRCalculator(unittest.TestCase):
    """Tests pour le calculateur PSNR"""
    
    def setUp(self):
        """Configuration des tests"""
        self.calculator = PSNRCalculator()
        self.test_signal = np.random.randn(1000).astype(np.float64)
        self.perfect_signal = self.test_signal.copy()
        self.noisy_signal = self.test_signal + np.random.randn(1000) * 0.1
    
    def test_perfect_reconstruction(self):
        """Test avec reconstruction parfaite"""
        psnr = self.calculator.calculate_psnr(self.test_signal, self.perfect_signal)
        
        # PSNR devrait être infini pour une reconstruction parfaite
        self.assertEqual(psnr, float('inf'))
    
    def test_noisy_reconstruction(self):
        """Test avec reconstruction bruitée"""
        psnr = self.calculator.calculate_psnr(self.test_signal, self.noisy_signal)
        
        # PSNR doit être un nombre fini et positif
        self.assertIsInstance(psnr, (int, float))
        self.assertFalse(np.isnan(psnr))
        self.assertFalse(np.isinf(psnr))
        self.assertGreater(psnr, 0)
    
    def test_harmonic_metrics(self):
        """Test des métriques harmoniques"""
        result = self.calculator.calculate_psnr_harmonic(self.test_signal, self.noisy_signal)
        
        # Vérification des clés
        required_keys = ['psnr', 'psnr_db', 'quality_level', 'harmonic_metrics']
        for key in required_keys:
            self.assertIn(key, result)
        
        # Vérification des métriques harmoniques
        harmonic_metrics = result['harmonic_metrics']
        required_harmonic_keys = ['spectral_error', 'spectral_correlation', 'relative_entropy', 'harmonic_fidelity']
        for key in required_harmonic_keys:
            self.assertIn(key, harmonic_metrics)
    
    def test_batch_calculation(self):
        """Test du calcul batch"""
        originals = [self.test_signal] * 3
        reconstructed_list = [self.perfect_signal, self.noisy_signal, self.perfect_signal]
        
        results = self.calculator.batch_calculate_psnr(originals, reconstructed_list)
        
        # Vérification des résultats
        self.assertEqual(len(results), 3)
        
        # Le premier et le troisième devraient être parfaits
        self.assertEqual(results[0]['psnr'], float('inf'))
        self.assertEqual(results[2]['psnr'], float('inf'))
        
        # Le deuxième devrait être fini
        self.assertFalse(np.isinf(results[1]['psnr']))
    
    def test_error_handling(self):
        """Test de la gestion des erreurs"""
        # Formes incompatibles
        with self.assertRaises(ValueError):
            self.calculator.calculate_psnr(self.test_signal, self.test_signal[:500])
        
        # Valeurs invalides
        invalid_signal = np.array([np.inf, 1, 2, 3])
        with self.assertRaises(ValueError):
            self.calculator.calculate_psnr(invalid_signal, self.test_signal)
        
        nan_signal = np.array([np.nan, 1, 2, 3])
        with self.assertRaises(ValueError):
            self.calculator.calculate_psnr(nan_signal, self.test_signal)


class TestIntegration(unittest.TestCase):
    """Tests d'intégration complets"""
    
    def setUp(self):
        """Configuration des tests"""
        self.compressor = HarmonicCompressor(precision_bits=128)
        self.psnr_calc = PSNRCalculator()
        
        # Signal de test complexe
        np.random.seed(42)
        self.test_signal = (
            np.sin(np.linspace(0, 10*np.pi, 1000)) + 
            0.5 * np.sin(np.linspace(0, 20*np.pi, 1000)) +
            np.random.randn(1000) * 0.1
        ).astype(np.float64)
    
    def test_full_pipeline(self):
        """Test du pipeline complet"""
        # Compression
        compressed = self.compressor.encode(self.test_signal)
        
        # Décompression
        reconstructed = self.compressor.decode(compressed)
        
        # Évaluation
        psnr_result = self.psnr_calc.calculate_psnr_harmonic(self.test_signal, reconstructed)
        
        # Vérifications
        self.assertGreater(psnr_result['psnr'], 0)
        self.assertIn('quality_level', psnr_result)
        self.assertIn('harmonic_metrics', psnr_result)
        
        # Le pipeline devrait fonctionner sans erreurs
        self.assertFalse(np.any(np.isnan(reconstructed)))
        self.assertFalse(np.any(np.isinf(reconstructed)))
    
    def test_quality_improvement(self):
        """Test de l'amélioration de qualité"""
        # Compression avec précision standard
        compressor_64 = HarmonicCompressor(precision_bits=64)
        compressed_64 = compressor_64.encode(self.test_signal)
        reconstructed_64 = compressor_64.decode(compressed_64)
        psnr_64 = self.psnr_calc.calculate_psnr(self.test_signal, reconstructed_64)
        
        # Compression avec précision étendue
        compressed_128 = self.compressor.encode(self.test_signal)
        reconstructed_128 = self.compressor.decode(compressed_128)
        psnr_128 = self.psnr_calc.calculate_psnr(self.test_signal, reconstructed_128)
        
        # La précision étendue devrait donner un meilleur PSNR
        if psnr_64 != float('inf') and psnr_128 != float('inf'):
            self.assertGreater(psnr_128, psnr_64)
    
    def test_performance_consistency(self):
        """Test de la cohérence des performances"""
        # Multiple runs
        psnr_values = []
        
        for _ in range(5):
            compressed = self.compressor.encode(self.test_signal)
            reconstructed = self.compressor.decode(compressed)
            psnr = self.psnr_calc.calculate_psnr(self.test_signal, reconstructed)
            psnr_values.append(psnr)
        
        # Les résultats devraient être cohérents
        if all(p != float('inf') for p in psnr_values):
            std_psnr = np.std(psnr_values)
            self.assertLess(std_psnr, 1.0)  # Écart-type < 1 dB


def run_tests():
    """Exécute tous les tests"""
    print("🧪 EXÉCUTION DES TESTS PHASE 1")
    print("="*60)
    
    # Création de la suite de tests
    test_suite = unittest.TestSuite()
    
    # Ajout des classes de tests
    test_classes = [
        TestExtendedPrecision,
        TestCriticalOptimization,
        TestHarmonicCompressor,
        TestPSNRCalculator,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Exécution
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Résumé
    print(f"\n📊 RÉSUMÉ DES TESTS:")
    print(f"   Tests exécutés: {result.testsRun}")
    print(f"   Succès: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   Échecs: {len(result.failures)}")
    print(f"   Erreurs: {len(result.errors)}")
    
    if result.wasSuccessful():
        print(f"   ✅ TOUS LES TESTS RÉUSSIS!")
    else:
        print(f"   ❌ CERTAINS TESTS ONT ÉCHOUÉ")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
