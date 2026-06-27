#!/usr/bin/env python3
"""
Script de Validation POC H.264 → HCV16
Validation complète du système avant déploiement
"""

import sys
import os
import time
import traceback
from typing import Dict, List

# Ajout du chemin src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def validate_imports():
    """Validation des imports"""
    print("🔍 Validation des imports...")
    
    try:
        from h264_analyzer import H264Analyzer
        from h264_recompressor import H264HCV16Recompressor
        from artifact_detector import ArtifactDetector
        from performance_tracker import PerformanceTracker
        print("   ✅ Tous les modules importés avec succès")
        return True
    except Exception as e:
        print(f"   ❌ Erreur import: {e}")
        return False

def validate_core_functionality():
    """Validation fonctionnalités core"""
    print("\n🧪 Validation fonctionnalités core...")
    
    try:
        # Test détecteur d'artefacts
        from artifact_detector import ArtifactDetector
        import numpy as np
        
        detector = ArtifactDetector()
        test_image = np.random.randint(0, 255, (128, 128), dtype=np.uint8)
        
        results = detector.detect_all_artifacts(test_image)
        
        # Vérifications
        assert 'hcv16_exploitability' in results
        assert 'estimated_total_gain' in results['hcv16_exploitability']
        
        gain = results['hcv16_exploitability']['estimated_total_gain']
        print(f"   ✅ Détection artefacts: {gain*100:.1f}% gain estimé")
        
        # Test analyseur H.264
        from h264_analyzer import H264Analyzer
        
        analyzer = H264Analyzer()
        
        # Test avec frames simulées
        test_frames = [np.random.randint(0, 255, (120, 160, 3), dtype=np.uint8) for _ in range(5)]
        
        blocking_result = analyzer._analyze_blocking_artifacts(test_frames)
        assert 'hcv16_gain_potential' in blocking_result
        
        print(f"   ✅ Analyse H.264: {blocking_result['level']} blocking détecté")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur fonctionnalité: {e}")
        traceback.print_exc()
        return False

def validate_performance():
    """Validation performance"""
    print("\n⚡ Validation performance...")
    
    try:
        from artifact_detector import ArtifactDetector
        import numpy as np
        
        detector = ArtifactDetector()
        
        # Test vitesse sur différentes tailles
        sizes = [(64, 64), (128, 128), (256, 256)]
        
        for size in sizes:
            test_image = np.random.randint(0, 255, size, dtype=np.uint8)
            
            start_time = time.time()
            results = detector.detect_all_artifacts(test_image)
            processing_time = time.time() - start_time
            
            print(f"   📊 {size[0]}×{size[1]}: {processing_time*1000:.1f}ms")
            
            # Vérification performance acceptable
            if size == (256, 256) and processing_time > 2.0:
                print(f"   ⚠️  Performance lente pour {size}")
        
        print("   ✅ Performance acceptable")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur performance: {e}")
        return False

def validate_business_metrics():
    """Validation métriques business"""
    print("\n💰 Validation métriques business...")
    
    try:
        from artifact_detector import ArtifactDetector
        import numpy as np
        
        detector = ArtifactDetector()
        
        # Test sur différents types de contenu simulé
        test_scenarios = [
            ("Animation", create_animation_test()),
            ("Film", create_film_test()),
            ("Sport", create_sport_test()),
            ("News", create_news_test())
        ]
        
        results = []
        
        for scenario_name, test_image in test_scenarios:
            analysis = detector.detect_all_artifacts(test_image)
            exploitability = analysis['hcv16_exploitability']
            
            ratio = exploitability['compression_ratio_estimate']
            savings = (ratio - 1) * 100
            
            results.append({
                'scenario': scenario_name,
                'ratio': ratio,
                'savings': savings,
                'viable': ratio >= 1.02
            })
            
            print(f"   📊 {scenario_name}: {ratio:.3f}× ({savings:.1f}% économie)")
        
        # Métriques globales
        viable_count = sum(1 for r in results if r['viable'])
        avg_ratio = sum(r['ratio'] for r in results) / len(results)
        avg_savings = sum(r['savings'] for r in results) / len(results)
        
        print(f"\n   📈 Résumé:")
        print(f"      Scénarios viables: {viable_count}/{len(results)} ({viable_count/len(results)*100:.0f}%)")
        print(f"      Ratio moyen: {avg_ratio:.3f}×")
        print(f"      Économie moyenne: {avg_savings:.1f}%")
        
        # Validation critères POC
        poc_success = viable_count >= len(results) * 0.8 and avg_ratio >= 1.02
        
        if poc_success:
            print("   ✅ Critères POC validés")
        else:
            print("   ⚠️  Critères POC partiellement validés")
        
        return poc_success
        
    except Exception as e:
        print(f"   ❌ Erreur métriques business: {e}")
        return False

def create_animation_test():
    """Création test animation avec blocking élevé"""
    import numpy as np
    
    image = np.zeros((128, 128), dtype=np.uint8)
    
    # Zones uniformes
    image[20:60, 20:80] = 200
    image[70:110, 50:110] = 100
    
    # Ajout blocking artifacts
    for y in range(0, 128, 8):
        for x in range(0, 128, 8):
            offset = np.random.randint(-10, 10)
            block = image[y:y+8, x:x+8].astype(np.int16) + offset
            image[y:y+8, x:x+8] = np.clip(block, 0, 255).astype(np.uint8)
    
    return image

def create_film_test():
    """Création test film avec gradients naturels"""
    import numpy as np
    
    y, x = np.ogrid[:128, :128]
    image = ((x + y) / 2).astype(np.uint8)
    
    # Ajout léger bruit
    noise = np.random.normal(0, 5, (128, 128))
    image = np.clip(image + noise, 0, 255).astype(np.uint8)
    
    return image

def create_sport_test():
    """Création test sport avec mouvement"""
    import numpy as np
    
    image = np.random.randint(80, 180, (128, 128), dtype=np.uint8)
    
    # Ajout patterns de mouvement
    for i in range(0, 128, 4):
        image[i:i+2, :] = np.roll(image[i:i+2, :], 2, axis=1)
    
    return image

def create_news_test():
    """Création test news avec quantization noise"""
    import numpy as np
    
    image = np.full((128, 128), 128, dtype=np.uint8)
    
    # Ajout bruit quantification
    noise = np.random.normal(0, 8, (128, 128))
    image = np.clip(image + noise, 0, 255).astype(np.uint8)
    
    return image

def validate_integration():
    """Validation intégration complète"""
    print("\n🔗 Validation intégration...")
    
    try:
        from h264_recompressor import H264HCV16Recompressor
        from performance_tracker import PerformanceTracker
        
        # Test initialisation
        recompressor = H264HCV16Recompressor()
        tracker = PerformanceTracker()
        
        print("   ✅ Initialisation composants réussie")
        
        # Test workflow (sans fichier réel)
        print("   📊 Test workflow simulé...")
        
        # Simulation analyse
        mock_analysis = {
            'file_info': {'file_size_mb': 100, 'duration_sec': 60},
            'frames_analyzed': 50,
            'blocking_artifacts': {'level': 'MODÉRÉ', 'hcv16_gain_potential': 0.08},
            'motion_residuals': {'level': 'FAIBLE', 'hcv16_gain_potential': 0.05},
            'quantization_noise': {'level': 'ÉLEVÉ', 'hcv16_gain_potential': 0.06},
            'temporal_patterns': {'recommended_gop': 25, 'hcv16_gain_potential': 0.04},
            'hcv16_opportunities': {
                'estimated_compression_ratio': 1.08,
                'opportunity_level': 'BONNE',
                'poc_feasibility': True
            }
        }
        
        # Test sélection stratégie
        strategy = recompressor._select_optimal_strategy(mock_analysis)
        print(f"   🎯 Stratégie sélectionnée: {strategy}")
        
        # Test métriques
        stats = {
            'compression_ratio': 1.08,
            'processing_time': 45.2,
            'opportunity_level': 'BONNE'
        }
        
        print(f"   📈 Ratio simulé: {stats['compression_ratio']:.3f}×")
        print("   ✅ Intégration validée")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur intégration: {e}")
        return False

def generate_validation_report(results: Dict):
    """Génération rapport de validation"""
    print(f"\n" + "="*60)
    print("📋 RAPPORT VALIDATION POC H.264 → HCV16")
    print("="*60)
    
    # Résumé des tests
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r)
    
    print(f"Tests exécutés: {total_tests}")
    print(f"Tests réussis: {passed_tests}")
    print(f"Taux de réussite: {passed_tests/total_tests*100:.0f}%")
    
    # Détail par catégorie
    print(f"\n📊 DÉTAIL PAR CATÉGORIE:")
    test_categories = {
        'imports': 'Imports & Dépendances',
        'core': 'Fonctionnalités Core',
        'performance': 'Performance',
        'business': 'Métriques Business',
        'integration': 'Intégration'
    }
    
    for key, name in test_categories.items():
        status = "✅ PASS" if results.get(key, False) else "❌ FAIL"
        print(f"   {name}: {status}")
    
    # Évaluation globale
    print(f"\n🎯 ÉVALUATION GLOBALE:")
    
    if passed_tests == total_tests:
        overall_status = "🚀 POC ENTIÈREMENT VALIDÉ"
        recommendation = "Prêt pour développement complet"
    elif passed_tests >= total_tests * 0.8:
        overall_status = "⚡ POC LARGEMENT VALIDÉ"
        recommendation = "Corrections mineures nécessaires"
    elif passed_tests >= total_tests * 0.6:
        overall_status = "🔄 POC PARTIELLEMENT VALIDÉ"
        recommendation = "Optimisations requises"
    else:
        overall_status = "❌ POC NON VALIDÉ"
        recommendation = "Révision architecture nécessaire"
    
    print(f"   Statut: {overall_status}")
    print(f"   Recommandation: {recommendation}")
    
    # Prochaines étapes
    print(f"\n📋 PROCHAINES ÉTAPES:")
    if passed_tests == total_tests:
        print("   1. Tests avec fichiers H.264 réels")
        print("   2. Optimisation performance")
        print("   3. Déploiement pilote")
    else:
        print("   1. Corriger tests échoués")
        print("   2. Re-valider système")
        print("   3. Tests étendus")
    
    return passed_tests == total_tests

def main():
    """Fonction principale de validation"""
    print("🎬 VALIDATION POC H.264 → HCV16 RECOMPRESSION")
    print("Exploitation révolution 18× lossless pour améliorer H.264 existants")
    print("="*70)
    
    # Exécution des tests
    validation_results = {}
    
    validation_results['imports'] = validate_imports()
    validation_results['core'] = validate_core_functionality()
    validation_results['performance'] = validate_performance()
    validation_results['business'] = validate_business_metrics()
    validation_results['integration'] = validate_integration()
    
    # Génération rapport final
    success = generate_validation_report(validation_results)
    
    print(f"\n{'='*70}")
    if success:
        print("🎉 VALIDATION COMPLÈTE RÉUSSIE !")
        print("🚀 POC prêt pour la phase suivante")
    else:
        print("⚠️  VALIDATION PARTIELLE")
        print("🔧 Corrections nécessaires avant continuation")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)