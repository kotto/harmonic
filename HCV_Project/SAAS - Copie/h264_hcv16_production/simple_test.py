#!/usr/bin/env python3
"""
Test Simple du Processeur Production
Test basique sans dépendances complexes
"""

import os
import sys
import time

# Ajout du chemin
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

def test_basic_import():
    """Test import basique"""
    print("🧪 Test import basique...")
    
    try:
        # Test import des classes principales
        from processor import ProcessingJob, ProcessingResult
        print("   ✅ Import ProcessingJob et ProcessingResult réussi")
        
        # Test création job
        job = ProcessingJob(
            job_id="test_job",
            input_file="test.mp4",
            output_file="test.hcv16"
        )
        
        assert job.job_id == "test_job"
        assert job.priority == 5  # valeur par défaut
        assert job.metadata == {}
        print("   ✅ Création ProcessingJob réussie")
        
        # Test création résultat
        result = ProcessingResult(
            job_id="test_job",
            success=True,
            original_size=1000000,
            compressed_size=800000,
            compression_ratio=1.25,
            processing_time=10.5
        )
        
        assert result.success == True
        assert result.compression_ratio == 1.25
        print("   ✅ Création ProcessingResult réussie")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur import: {e}")
        return False

def test_processor_class():
    """Test classe ProductionProcessor"""
    print("\n🧪 Test classe ProductionProcessor...")
    
    try:
        from processor import ProductionProcessor
        print("   ✅ Import ProductionProcessor réussi")
        
        # Test initialisation sans config
        processor = ProductionProcessor()
        
        assert processor.config is not None
        assert processor.max_workers > 0
        assert not processor.running
        print("   ✅ Initialisation basique réussie")
        
        # Test méthodes de base
        stats = processor.get_statistics()
        assert 'jobs_processed' in stats
        assert 'uptime_seconds' in stats
        print("   ✅ Méthodes de base fonctionnelles")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur classe ProductionProcessor: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_creation():
    """Test création configuration"""
    print("\n🧪 Test création configuration...")
    
    try:
        from processor import create_default_config
        print("   ✅ Import create_default_config réussi")
        
        # Création config
        create_default_config()
        
        assert os.path.exists("processor_config.json")
        print("   ✅ Fichier configuration créé")
        
        # Vérification contenu
        import json
        with open("processor_config.json", 'r') as f:
            config = json.load(f)
        
        assert 'max_workers' in config
        assert 'supported_formats' in config
        print("   ✅ Configuration valide")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur création config: {e}")
        return False
    
    finally:
        # Nettoyage
        if os.path.exists("processor_config.json"):
            os.remove("processor_config.json")

def test_batch_processor():
    """Test BatchProcessor"""
    print("\n🧪 Test BatchProcessor...")
    
    try:
        from processor import ProductionProcessor, BatchProcessor
        print("   ✅ Import BatchProcessor réussi")
        
        # Initialisation
        processor = ProductionProcessor()
        batch_processor = BatchProcessor(processor)
        
        assert batch_processor.processor is processor
        assert batch_processor.batch_jobs == []
        print("   ✅ Initialisation BatchProcessor réussie")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur BatchProcessor: {e}")
        return False

def test_performance_monitor():
    """Test PerformanceMonitor"""
    print("\n🧪 Test PerformanceMonitor...")
    
    try:
        from processor import PerformanceMonitor
        print("   ✅ Import PerformanceMonitor réussi")
        
        # Initialisation
        monitor = PerformanceMonitor()
        
        assert monitor.metrics_history == []
        assert monitor.max_history == 100
        print("   ✅ Initialisation PerformanceMonitor réussie")
        
        # Test collecte métriques
        monitor.collect_metrics()
        
        # Test récupération métriques
        metrics = monitor.get_metrics()
        assert isinstance(metrics, dict)
        print("   ✅ Collecte métriques fonctionnelle")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur PerformanceMonitor: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 TESTS SIMPLES PROCESSEUR PRODUCTION")
    print("="*50)
    
    tests = [
        ("Import basique", test_basic_import),
        ("Classe ProductionProcessor", test_processor_class),
        ("Création configuration", test_config_creation),
        ("BatchProcessor", test_batch_processor),
        ("PerformanceMonitor", test_performance_monitor)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'-'*20} {test_name} {'-'*20}")
        
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            results.append((test_name, False))
    
    # Rapport final
    print(f"\n" + "="*50)
    print("📋 RAPPORT TESTS SIMPLES")
    print("="*50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"Tests exécutés: {total}")
    print(f"Tests réussis: {passed}")
    print(f"Taux de réussite: {passed/total*100:.0f}%")
    
    print(f"\n📊 DÉTAIL:")
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    if passed == total:
        print(f"\n🎉 TOUS LES TESTS SIMPLES RÉUSSIS !")
        print("🚀 Classes de base fonctionnelles")
    else:
        print(f"\n⚠️  CERTAINS TESTS ÉCHOUÉS")
        print("🔧 Vérification nécessaire")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)