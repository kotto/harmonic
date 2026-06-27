#!/usr/bin/env python3
"""
Test complet du projet HCS V2 avec upscaling quantique-harmonique
Validation de tous les composants et détection d'erreurs
"""

import sys
import os
import time
import numpy as np
from PIL import Image
import io
import base64
import logging

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Ajout des chemins
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def test_imports():
    """Test de tous les imports nécessaires"""
    logger.info("🔍 Test des imports...")
    
    try:
        # Test imports core
        from core.hybrid_compressor import HybridCompressor
        from core.k_factor_engine import KFactorEngine
        from core.webp_optimizer import WebPOptimizer
        from core.harmonic_upscaler import harmonic_upscaler_api
        logger.info("✅ Imports core réussis")
        
        # Test imports API
        from api.server_quantum_harmonic import app
        logger.info("✅ Import API réussi")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Erreur import: {e}")
        return False

def test_core_components():
    """Test des composants core"""
    logger.info("🔧 Test des composants core...")
    
    try:
        # Import local pour éviter les problèmes de portée
        from core.hybrid_compressor import HybridCompressor
        from core.k_factor_engine import KFactorEngine
        from core.webp_optimizer import WebPOptimizer
        
        # Test K-Factor Engine
        k_engine = KFactorEngine(k_factor=0.02)
        test_image = np.random.rand(100, 100, 3).astype(np.float32)
        k_compressed, k_meta = k_engine.compress_image(test_image)
        logger.info(f"✅ K-Factor Engine: ratio {k_meta.get('k_ratio', 0):.1f}:1")
        
        # Test WebP Optimizer
        webp_opt = WebPOptimizer(quality=95)
        webp_compressed, webp_meta = webp_opt.optimize_image(test_image)
        logger.info(f"✅ WebP Optimizer: ratio {webp_meta.get('webp_ratio', 0):.1f}:1")
        
        # Test Hybrid Compressor
        hybrid = HybridCompressor(k_factor=0.02, webp_quality=95)
        hybrid_compressed, hybrid_meta = hybrid.compress_image(test_image)
        logger.info(f"✅ Hybrid Compressor: ratio {hybrid_meta.get('hybrid_ratio', 0):.1f}:1")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur composants core: {e}")
        return False

def test_harmonic_upscaler():
    """Test de l'upscaler quantique-harmonique"""
    logger.info("🌊 Test de l'upscaler quantique-harmonique...")
    
    try:
        # Import local
        from core.harmonic_upscaler import harmonic_upscaler_api
        
        # Création d'une image de test
        test_image = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
        
        # Test upscale simple
        result = harmonic_upscaler_api.upscale_image(
            image_array=test_image,
            factor='2x',
            energy_level='standard'
        )
        
        if result['success']:
            logger.info(f"✅ Upscaling réussi: {test_image.shape} → {result['target_shape']}")
            logger.info(f"   Niveau de réalité: {result['reality_level_used']}")
            logger.info(f"   PSNR: {result['quality_metrics']['psnr']:.1f} dB")
            logger.info(f"   Temps: {result['processing_time']:.3f}s")
        else:
            logger.error(f"❌ Upscaling échoué: {result.get('error', 'Erreur inconnue')}")
            return False
        
        # Test analyse d'image
        analysis = harmonic_upscaler_api.analyze_image_for_upscaling(test_image)
        if analysis['success']:
            logger.info("✅ Analyse d'image réussie")
            logger.info(f"   Recommandation énergie: {analysis['recommendations']['energy_level']['recommended']}")
            logger.info(f"   Recommandation facteur: {analysis['recommendations']['upscale_factor']['recommended']}")
        else:
            logger.error(f"❌ Analyse échouée: {analysis.get('error', 'Erreur inconnue')}")
            return False
        
        # Test presets
        presets = harmonic_upscaler_api.get_available_presets()
        logger.info(f"✅ Presets disponibles: {len(presets['energy_levels'])} niveaux d'énergie")
        
        # Test info système
        system_info = harmonic_upscaler_api.get_system_info()
        logger.info(f"✅ Info système: {system_info['name']} v{system_info['version']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur upscaler: {e}")
        return False

def test_api_endpoints():
    """Test des endpoints API"""
    logger.info("🌐 Test des endpoints API...")
    
    try:
        # Import local
        from api.server_quantum_harmonic import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        # Test endpoint racine
        response = client.get("/")
        if response.status_code == 200:
            logger.info("✅ Endpoint racine OK")
        else:
            logger.error(f"❌ Endpoint racine: {response.status_code}")
            return False
        
        # Test health
        response = client.get("/api/v2/health")
        if response.status_code == 200:
            logger.info("✅ Health check OK")
        else:
            logger.error(f"❌ Health check: {response.status_code}")
            return False
        
        # Test upscale info
        response = client.get("/api/v2/upscale/info")
        if response.status_code == 200:
            logger.info("✅ Upscale info OK")
        else:
            logger.error(f"❌ Upscale info: {response.status_code}")
            return False
        
        # Test upscale presets
        response = client.get("/api/v2/upscale/presets")
        if response.status_code == 200:
            logger.info("✅ Upscale presets OK")
        else:
            logger.error(f"❌ Upscale presets: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test API: {e}")
        return False

def test_image_processing():
    """Test complet du traitement d'image"""
    logger.info("🖼️ Test complet du traitement d'image...")
    
    try:
        # Import local
        from core.hybrid_compressor import HybridCompressor
        from core.harmonic_upscaler import harmonic_upscaler_api
        
        # Création d'une image de test complexe
        h, w = 300, 400
        test_image = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Ajout de patterns
        x = np.arange(w)
        y = np.arange(h)
        X, Y = np.meshgrid(x, y)
        
        test_image[:, :, 0] = (128 + 64 * np.sin(X/100)).astype(np.uint8)
        test_image[:, :, 1] = (128 + 48 * np.cos(Y/75)).astype(np.uint8)
        test_image[:, :, 2] = (128 + 56 * np.sin(X/200) * np.cos(Y/100)).astype(np.uint8)
        
        # Test compression
        hybrid = HybridCompressor()
        compressed, comp_meta = hybrid.compress_image(test_image)
        logger.info(f"✅ Compression: {comp_meta.get('hybrid_ratio', 0):.1f}:1")
        
        # Test upscaling
        result = harmonic_upscaler_api.upscale_image(
            image_array=test_image,
            target_size=(h*2, w*2),
            energy_level='high'
        )
        
        if result['success']:
            logger.info(f"✅ Upscaling: {test_image.shape} → {result['target_shape']}")
            logger.info(f"   Qualité: PSNR={result['quality_metrics']['psnr']:.1f} dB")
            logger.info(f"   Efficacité: {result['efficiency_metrics']['ops_per_second']:.2e} ops/s")
        else:
            logger.error(f"❌ Upscaling échoué: {result.get('error')}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur traitement image: {e}")
        return False

def test_performance():
    """Test de performance"""
    logger.info("⚡ Test de performance...")
    
    try:
        # Import local
        from core.harmonic_upscaler import harmonic_upscaler_api
        
        # Test avec différentes tailles d'image
        sizes = [(100, 100), (200, 200), (400, 400)]
        energy_levels = ['economy', 'standard', 'high']
        
        for h, w in sizes:
            for energy in energy_levels:
                test_image = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
                
                start_time = time.time()
                result = harmonic_upscaler_api.upscale_image(
                    image_array=test_image,
                    factor='2x',
                    energy_level=energy
                )
                processing_time = time.time() - start_time
                
                if result['success']:
                    logger.info(f"✅ {h}x{w} @ {energy}: {processing_time:.3f}s")
                else:
                    logger.warning(f"⚠️ {h}x{w} @ {energy}: échec")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur performance: {e}")
        return False

def check_file_structure():
    """Vérification de la structure des fichiers"""
    logger.info("📁 Vérification de la structure...")
    
    required_files = [
        'core/__init__.py',
        'core/hybrid_compressor.py',
        'core/k_factor_engine.py',
        'core/webp_optimizer.py',
        'core/harmonic_upscaler.py',
        'api/server_quantum_harmonic.py',
        'frontend/quantum_upscaler.html',
        'requirements.txt'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        logger.error(f"❌ Fichiers manquants: {missing_files}")
        return False
    else:
        logger.info("✅ Structure des fichiers OK")
        return True

def generate_test_report():
    """Génère un rapport de test"""
    logger.info("📊 Génération du rapport de test...")
    
    report = {
        'timestamp': time.time(),
        'tests': {
            'imports': test_imports(),
            'file_structure': check_file_structure(),
            'core_components': test_core_components(),
            'harmonic_upscaler': test_harmonic_upscaler(),
            'api_endpoints': test_api_endpoints(),
            'image_processing': test_image_processing(),
            'performance': test_performance()
        }
    }
    
    # Calcul du score global
    passed = sum(report['tests'].values())
    total = len(report['tests'])
    score = (passed / total) * 100
    
    report['summary'] = {
        'total_tests': total,
        'passed_tests': passed,
        'failed_tests': total - passed,
        'success_rate': score
    }
    
    # Affichage du rapport
    logger.info("\n" + "="*60)
    logger.info("📊 RAPPORT DE TEST COMPLET")
    logger.info("="*60)
    
    for test_name, result in report['tests'].items():
        status = "✅" if result else "❌"
        logger.info(f"{status} {test_name.replace('_', ' ').title()}")
    
    logger.info("-"*60)
    logger.info(f"📈 Score global: {score:.1f}% ({passed}/{total})")
    
    if score >= 90:
        logger.info("🎉 EXCELLENT: Le projet est prêt pour la production!")
    elif score >= 70:
        logger.info("✅ BON: Le projet fonctionne avec quelques limitations")
    else:
        logger.warning("⚠️ ATTENTION: Le projet nécessite des corrections")
    
    logger.info("="*60)
    
    return report

def main():
    """Fonction principale de test"""
    logger.info("🚀 DÉMARRAGE DES TESTS COMPLETS HCS V2")
    logger.info("Test du projet avec upscaling quantique-harmonique")
    logger.info("="*60)
    
    try:
        report = generate_test_report()
        
        # Sauvegarde du rapport
        import json
        with open('test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info("📄 Rapport sauvegardé dans 'test_report.json'")
        
        return report['summary']['success_rate'] >= 70
        
    except Exception as e:
        logger.error(f"❌ Erreur durant les tests: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
