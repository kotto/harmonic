#!/usr/bin/env python3
"""
Integration Tests - Tests complets HCS V2
Validation K=0.02 + WebP en conditions réelles
"""

import pytest
import numpy as np
import requests
import time
import os
import sys
from pathlib import Path

# Ajout du chemin racine
sys.path.append(str(Path(__file__).parent.parent))

from core.hybrid_compressor import HybridCompressor
from core.k_factor_engine import KFactorEngine
from core.webp_optimizer import WebPOptimizer

class TestHCSIntegration:
    """Suite de tests d'intégration HCS V2"""
    
    @pytest.fixture
    def compressor(self):
        """Fixture compresseur hybride"""
        return HybridCompressor(k_factor=0.02, webp_quality=95)
    
    @pytest.fixture
    def sample_images(self):
        """Fixture images de test variées"""
        return {
            'gradient': self._create_gradient_image(480, 640),
            'noise': np.random.rand(480, 640, 3).astype(np.float32),
            'uniform': np.ones((480, 640, 3)) * 0.5,
            'checkerboard': self._create_checkerboard(480, 640),
            'natural': self._create_natural_image(480, 640)
        }
    
    def _create_gradient_image(self, height, width):
        """Crée une image gradient"""
        x = np.linspace(0, 1, width)
        y = np.linspace(0, 1, height)
        X, Y = np.meshgrid(x, y)
        
        R = X
        G = Y
        B = (X + Y) / 2
        
        return np.stack([R, G, B], axis=2)
    
    def _create_checkerboard(self, height, width):
        """Crée une image échiquier"""
        checkerboard = np.zeros((height, width, 3))
        block_size = 32
        
        for i in range(0, height, block_size):
            for j in range(0, width, block_size):
                if ((i // block_size) + (j // block_size)) % 2 == 0:
                    checkerboard[i:i+block_size, j:j+block_size] = 1.0
        
        return checkerboard
    
    def _create_natural_image(self, height, width):
        """Crée une image simulant un contenu naturel"""
        # Base bleue (ciel)
        image = np.zeros((height, width, 3))
        image[:, :, 2] = 0.8  # Bleu
        
        # Ajout de "nuages"
        for _ in range(5):
            x = np.random.randint(0, width)
            y = np.random.randint(0, height // 2)
            radius = np.random.randint(20, 50)
            
            Y, X = np.ogrid[:height, :width]
            mask = (X - x)**2 + (Y - y)**2 <= radius**2
            
            image[mask] += np.random.rand(3) * 0.3
        
        # Ajout de "terrain" vert
        image[height//2:, :, 1] = 0.6  # Vert
        
        return np.clip(image, 0, 1)
    
    def test_k_factor_guarantee(self, compressor):
        """Test garantie K=0.02"""
        k_engine = compressor.k_engine
        
        # Test multiple images
        for i in range(10):
            test_image = np.random.rand(480, 640, 3).astype(np.float32)
            
            compressed, metadata = k_engine.compress_image(test_image)
            
            # Validation garantie
            assert metadata['guarantee_met'], f"Garantie K non respectée pour image {i}"
            assert metadata['actual_ratio'] >= 45, f"Ratio trop bas: {metadata['actual_ratio']}"
            assert metadata['actual_ratio'] <= 55, f"Ratio trop haut: {metadata['actual_ratio']}"
    
    def test_webp_optimization(self, compressor):
        """Test optimisation WebP"""
        webp_opt = compressor.webp_optimizer
        
        test_image = np.random.rand(480, 640, 3).astype(np.float32)
        
        webp_data, metadata = webp_opt.optimize_image(test_image)
        
        # Validation WebP
        assert metadata['compression_ratio'] > 1, "WebP doit compresser"
        assert metadata['space_saved_percent'] > 0, "WebP doit économiser de l'espace"
        assert len(webp_data) > 0, "WebP doit produire des données"
        assert metadata['format'] == 'webp', "Format doit être WebP"
    
    def test_hybrid_compression_ratios(self, compressor, sample_images):
        """Test ratios de compression hybride"""
        results = {}
        
        for name, image in sample_images.items():
            compressed_data, metadata = compressor.compress_image(image)
            results[name] = metadata
        
        # Validation ratios
        for name, metadata in results.items():
            # Ratio minimum K=0.02
            assert metadata['k_ratio'] >= 45, f"Ratio K trop bas pour {name}"
            assert metadata['k_ratio'] <= 55, f"Ratio K trop haut pour {name}"
            
            # Ratio WebP additionnel
            assert metadata['webp_ratio'] > 1, f"WebP ne compresse pas pour {name}"
            
            # Ratio hybride total
            assert metadata['hybrid_ratio'] > 50, f"Ratio hybride trop bas pour {name}"
            
            # Garantie K respectée
            assert metadata['k_guarantee_met'], f"Garantie K non respectée pour {name}"
        
        # Analyse des résultats
        ratios = [r['hybrid_ratio'] for r in results.values()]
        avg_ratio = np.mean(ratios)
        
        # Validation performance moyenne
        assert avg_ratio > 100, f"Ratio moyen trop bas: {avg_ratio}"
        
        print(f"\n📊 Résultats par type d'image:")
        for name, metadata in results.items():
            print(f"   {name:12s} → {metadata['hybrid_ratio']:6.1f}:1 ({metadata['optimization_level']})")
        print(f"   Moyenne: → {avg_ratio:6.1f}:1")
    
    def test_performance_requirements(self, compressor):
        """Test exigences de performance"""
        test_image = np.random.rand(1920, 1080, 3).astype(np.float32)
        
        # Test temps de traitement
        start_time = time.time()
        compressed_data, metadata = compressor.compress_image(test_image)
        processing_time = time.time() - start_time
        
        # Validation performance
        assert processing_time < 0.5, f"Traitement trop lent: {processing_time:.3f}s"
        assert metadata['fps_estimate'] >= 2, f"FPS trop bas: {metadata['fps_estimate']}"
        
        # Test mémoire (approximatif)
        assert len(compressed_data) < test_image.nbytes, "Compression doit réduire la taille"
    
    def test_adaptive_optimization(self, compressor):
        """Test optimisation adaptative"""
        test_image = np.random.rand(480, 640, 3).astype(np.float32)
        
        # Test différents ratios cibles
        target_ratios = [100, 200, 500, 1000]
        
        for target in target_ratios:
            compressed_data, metadata = compressor.compress_image(test_image, target_ratio=target)
            
            # Validation atteinte cible (90% de tolérance)
            assert metadata['target_achieved'], f"Cible {target} non atteinte"
            assert metadata['hybrid_ratio'] >= target * 0.9, f"Ratio insuffisant pour cible {target}"
    
    def test_batch_compression(self, compressor):
        """Test compression par lot"""
        batch_images = [np.random.rand(480, 640, 3).astype(np.float32) for _ in range(10)]
        
        results = compressor.compress_batch(batch_images)
        
        # Validation lot
        assert len(results) == len(batch_images), "Taille lot incorrecte"
        
        successful = sum(1 for r in results if r['success'])
        assert successful == len(batch_images), "Toutes les images devraient réussir"
        
        # Validation ratios individuels
        for result in results:
            if result['success']:
                metadata = result['metadata']
                assert metadata['hybrid_ratio'] > 50, "Ratio lot trop bas"
    
    def test_api_integration(self):
        """Test intégration API (simulation)"""
        # Simulation de requête API
        test_image = np.random.rand(480, 640, 3).astype(np.float32)
        
        # Simulation endpoint compression
        compressor = HybridCompressor()
        compressed_data, metadata = compressor.compress_image(test_image)
        
        # Validation format réponse API
        api_response = {
            "success": True,
            "result_id": "test_001",
            "original_size": test_image.nbytes,
            "compressed_size": len(compressed_data),
            "compression_ratio": metadata['hybrid_ratio'],
            "space_saved_percent": metadata['space_saved_percent'],
            "processing_time": metadata['total_time'],
            "k_ratio": metadata['k_ratio'],
            "webp_ratio": metadata['webp_ratio'],
            "format": "webp"
        }
        
        # Validation structure réponse
        assert api_response['success'] is True
        assert api_response['compression_ratio'] > 50
        assert api_response['space_saved_percent'] > 0
        assert api_response['format'] == 'webp'
    
    def test_error_handling(self, compressor):
        """Test gestion des erreurs"""
        # Test image vide
        with pytest.raises(ValueError, match="Image vide"):
            compressor.compress_image(None)
        
        # Test image invalide
        with pytest.raises(TypeError, match="numpy array"):
            compressor.compress_image("not_an_array")
        
        # Test K-factor invalide
        with pytest.raises(ValueError, match="entre 0.001 et 0.1"):
            KFactorEngine(k_factor=0.5)
    
    def test_statistics_tracking(self, compressor):
        """Test suivi des statistiques"""
        # Réinitialiser statistiques
        compressor.reset_stats()
        
        # Traiter quelques images
        for _ in range(5):
            test_image = np.random.rand(480, 640, 3).astype(np.float32)
            compressor.compress_image(test_image)
        
        # Validation statistiques
        stats = compressor.get_stats()
        
        assert stats['total_processed'] == 5, "Nombre traité incorrect"
        assert stats['total_hybrid_ratio'] > 0, "Ratio moyen incorrect"
        assert stats['total_time'] > 0, "Temps moyen incorrect"
        assert stats['average_fps'] > 0, "FPS moyen incorrect"
    
    def test_content_analysis(self, compressor):
        """Test analyse de contenu"""
        # Images de complexité différente
        simple_image = np.ones((480, 640, 3)) * 0.5
        complex_image = np.random.rand(480, 640, 3)
        
        # Compression et analyse
        _, simple_meta = compressor.compress_image(simple_image)
        _, complex_meta = compressor.compress_image(complex_image)
        
        # Validation analyse
        assert simple_meta['content_type'] in ['simple', 'moderate']
        assert complex_meta['content_type'] in ['moderate', 'complex']
        
        # Le contenu simple devrait avoir un meilleur ratio
        assert simple_meta['hybrid_ratio'] >= complex_meta['hybrid_ratio'] * 0.8

def run_integration_tests():
    """Exécute tous les tests d'intégration"""
    print("🧪 DÉMARRAGE TESTS INTÉGRATION HCS V2")
    print("=" * 60)
    
    # Initialisation
    test_suite = TestHCSIntegration()
    compressor = HybridCompressor()
    sample_images = {
        'gradient': test_suite._create_gradient_image(480, 640),
        'noise': np.random.rand(480, 640, 3).astype(np.float32),
        'uniform': np.ones((480, 640, 3)) * 0.5,
        'checkerboard': test_suite._create_checkerboard(480, 640),
        'natural': test_suite._create_natural_image(480, 640)
    }
    
    tests_passed = 0
    tests_total = 0
    
    # Exécution des tests
    test_methods = [
        ("Garantie K=0.02", lambda: test_suite.test_k_factor_guarantee(compressor)),
        ("Optimisation WebP", lambda: test_suite.test_webp_optimization(compressor)),
        ("Ratios Hybrides", lambda: test_suite.test_hybrid_compression_ratios(compressor, sample_images)),
        ("Performance", lambda: test_suite.test_performance_requirements(compressor)),
        ("Optimisation Adaptative", lambda: test_suite.test_adaptive_optimization(compressor)),
        ("Compression Lot", lambda: test_suite.test_batch_compression(compressor)),
        ("Intégration API", lambda: test_suite.test_api_integration()),
        ("Gestion Erreurs", lambda: test_suite.test_error_handling(compressor)),
        ("Statistiques", lambda: test_suite.test_statistics_tracking(compressor)),
        ("Analyse Contenu", lambda: test_suite.test_content_analysis(compressor))
    ]
    
    for test_name, test_func in test_methods:
        tests_total += 1
        try:
            test_func()
            print(f"✅ {test_name}: PASSÉ")
            tests_passed += 1
        except Exception as e:
            print(f"❌ {test_name}: ÉCHOUÉ - {e}")
    
    # Résultats finaux
    print(f"\n📊 RÉSULTATS TESTS:")
    print(f"   Tests passés: {tests_passed}/{tests_total}")
    print(f"   Taux succès: {tests_passed/tests_total*100:.1f}%")
    
    if tests_passed == tests_total:
        print("🎉 TOUS LES TESTS RÉUSSIS - HCS V2 PRÊT !")
    else:
        print("⚠️  CERTAINS TESTS ONT ÉCHOUÉ - VÉRIFICATION NÉCESSAIRE")
    
    return tests_passed == tests_total

if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)
