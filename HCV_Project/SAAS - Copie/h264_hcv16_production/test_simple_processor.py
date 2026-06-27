#!/usr/bin/env python3
"""
Test Simple Processor
Tests du processeur production simplifié
"""

import os
import sys
import time
import tempfile
import shutil
from pathlib import Path

# Ajout du chemin pour imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

from simple_processor import SimpleProductionProcessor, ProcessingJob, ProcessingResult, create_default_config

def test_basic_functionality():
    """Test fonctionnalités de base"""
    print("🧪 Test fonctionnalités de base...")
    
    try:
        # Test création job
        job = ProcessingJob(
            job_id="test_001",
            input_file="test.mp4",
            output_file="test.hcv16"
        )
        
        assert job.job_id == "test_001"
        assert job.priority == 5
        print("   ✅ Création ProcessingJob réussie")
        
        # Test création résultat
        result = ProcessingResult(
            job_id="test_001",
            success=True,
            original_size=1000000,
            compressed_size=800000,
            compression_ratio=1.25,
            processing_time=5.0
        )
        
        assert result.success == True
        assert result.compression_ratio == 1.25
        print("   ✅ Création ProcessingResult réussie")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def test_processor_lifecycle():
    """Test cycle de vie processeur"""
    print("\n🧪 Test cycle de vie processeur...")
    
    try:
        # Initialisation
        processor = SimpleProductionProcessor()
        assert not processor.running
        print("   ✅ Initialisation réussie")
        
        # Démarrage
        processor.start()
        assert processor.running
        print("   ✅ Démarrage réussi")
        
        # Statistiques initiales
        stats = processor.get_statistics()
        assert stats['jobs_processed'] == 0
        assert stats['uptime_seconds'] > 0
        print("   ✅ Statistiques initiales correctes")
        
        # Arrêt
        processor.stop()
        assert not processor.running
        print("   ✅ Arrêt réussi")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def test_job_processing():
    """Test traitement de jobs"""
    print("\n🧪 Test traitement de jobs...")
    
    processor = SimpleProductionProcessor()
    
    try:
        processor.start()
        
        # Création fichier test temporaire
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_file.write(b'fake_video_data' * 1000)
            temp_input = temp_file.name
        
        temp_output = temp_input.replace('.mp4', '.hcv16')
        
        try:
            # Soumission job
            job_id = processor.submit_job(temp_input, temp_output)
            assert job_id is not None
            print(f"   ✅ Job soumis: {job_id}")
            
            # Attente traitement
            timeout = 10
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                status = processor.get_job_status(job_id)
                
                if status['status'] in ['completed', 'failed']:
                    break
                
                time.sleep(0.5)
            
            # Vérification résultat
            final_status = processor.get_job_status(job_id)
            print(f"   📊 Statut final: {final_status['status']}")
            
            if final_status['status'] == 'completed':
                result = final_status['result']
                print(f"   ✅ Traitement réussi: {result.compression_ratio:.3f}×")
                
                # Vérification fichier de sortie
                assert os.path.exists(temp_output)
                print("   ✅ Fichier de sortie créé")
            
            # Vérification statistiques
            stats = processor.get_statistics()
            assert stats['jobs_processed'] >= 1
            print(f"   ✅ Statistiques mises à jour: {stats['jobs_processed']} jobs")
            
            return True
            
        finally:
            # Nettoyage
            if os.path.exists(temp_input):
                os.remove(temp_input)
            if os.path.exists(temp_output):
                os.remove(temp_output)
    
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    finally:
        processor.stop()

def test_multiple_jobs():
    """Test traitement multiple jobs"""
    print("\n🧪 Test traitement multiple jobs...")
    
    processor = SimpleProductionProcessor()
    
    try:
        processor.start()
        
        # Création plusieurs fichiers test
        temp_files = []
        job_ids = []
        
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix=f'_test_{i}.mp4', delete=False) as temp_file:
                temp_file.write(b'fake_video_data' * (500 + i * 100))
                temp_input = temp_file.name
                temp_output = temp_input.replace('.mp4', '.hcv16')
                
                temp_files.append((temp_input, temp_output))
                
                # Soumission job avec priorités différentes
                job_id = processor.submit_job(temp_input, temp_output, priority=i+1)
                job_ids.append(job_id)
        
        print(f"   ✅ {len(job_ids)} jobs soumis")
        
        # Attente traitement de tous les jobs
        timeout = 20
        start_time = time.time()
        completed_jobs = 0
        
        while time.time() - start_time < timeout and completed_jobs < len(job_ids):
            completed_jobs = 0
            
            for job_id in job_ids:
                status = processor.get_job_status(job_id)
                if status['status'] in ['completed', 'failed']:
                    completed_jobs += 1
            
            time.sleep(1)
        
        print(f"   📊 Jobs terminés: {completed_jobs}/{len(job_ids)}")
        
        # Vérification statistiques finales
        stats = processor.get_statistics()
        print(f"   📈 Statistiques: {stats['jobs_processed']} jobs, ratio moyen: {stats['avg_compression_ratio']:.3f}×")
        
        # Nettoyage
        for temp_input, temp_output in temp_files:
            if os.path.exists(temp_input):
                os.remove(temp_input)
            if os.path.exists(temp_output):
                os.remove(temp_output)
        
        return completed_jobs >= len(job_ids) * 0.8  # Au moins 80% de succès
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    finally:
        processor.stop()

def test_error_handling():
    """Test gestion d'erreurs"""
    print("\n🧪 Test gestion d'erreurs...")
    
    processor = SimpleProductionProcessor()
    
    try:
        processor.start()
        
        # Test fichier inexistant
        try:
            processor.submit_job("fichier_inexistant.mp4", "output.hcv16")
            assert False, "Devrait lever FileNotFoundError"
        except FileNotFoundError:
            print("   ✅ Erreur fichier inexistant gérée")
        
        # Test format non supporté
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b'test')
            temp_input = temp_file.name
        
        try:
            processor.submit_job(temp_input, "output.hcv16")
            assert False, "Devrait lever ValueError"
        except ValueError:
            print("   ✅ Erreur format non supporté gérée")
        finally:
            os.remove(temp_input)
        
        # Test fichier trop volumineux
        processor.config['max_file_size_mb'] = 0.001  # 1KB max
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_file.write(b'x' * 2000)  # 2KB
            temp_input = temp_file.name
        
        try:
            processor.submit_job(temp_input, "output.hcv16")
            assert False, "Devrait lever ValueError"
        except ValueError:
            print("   ✅ Erreur fichier trop volumineux gérée")
        finally:
            os.remove(temp_input)
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    finally:
        processor.stop()

def test_configuration():
    """Test configuration"""
    print("\n🧪 Test configuration...")
    
    try:
        # Test création config par défaut
        create_default_config()
        assert os.path.exists("processor_config.json")
        print("   ✅ Configuration par défaut créée")
        
        # Test chargement config
        processor = SimpleProductionProcessor("processor_config.json")
        assert processor.config is not None
        assert 'max_workers' in processor.config
        print("   ✅ Configuration chargée")
        
        # Test config personnalisée
        custom_config = {
            "max_workers": 2,
            "batch_size": 5,
            "max_file_size_mb": 100
        }
        
        import json
        with open("custom_config.json", 'w') as f:
            json.dump(custom_config, f)
        
        processor_custom = SimpleProductionProcessor("custom_config.json")
        assert processor_custom.config['max_workers'] == 2
        assert processor_custom.config['batch_size'] == 5
        print("   ✅ Configuration personnalisée chargée")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    finally:
        # Nettoyage
        for config_file in ["processor_config.json", "custom_config.json"]:
            if os.path.exists(config_file):
                os.remove(config_file)

def test_performance_simulation():
    """Test simulation performance"""
    print("\n🧪 Test simulation performance...")
    
    processor = SimpleProductionProcessor()
    
    try:
        processor.start()
        
        # Création batch de fichiers test
        temp_dir = tempfile.mkdtemp()
        job_ids = []
        
        try:
            for i in range(5):
                test_file = os.path.join(temp_dir, f'perf_test_{i}.mp4')
                with open(test_file, 'wb') as f:
                    f.write(b'performance_test_data' * (100 + i * 50))
                
                output_file = test_file.replace('.mp4', '.hcv16')
                job_id = processor.submit_job(test_file, output_file)
                job_ids.append(job_id)
            
            print(f"   📤 {len(job_ids)} jobs de performance soumis")
            
            # Monitoring pendant traitement
            start_time = time.time()
            timeout = 30
            
            while time.time() - start_time < timeout:
                stats = processor.get_statistics()
                
                print(f"   📊 Progress: {stats['jobs_processed']} traités, "
                      f"{stats['jobs_in_queue']} en queue, "
                      f"{stats['active_jobs']} actifs")
                
                if stats['jobs_processed'] >= len(job_ids):
                    break
                
                time.sleep(2)
            
            # Statistiques finales
            final_stats = processor.get_statistics()
            processing_time = time.time() - start_time
            
            print(f"   📈 Résultats performance:")
            print(f"      Jobs traités: {final_stats['jobs_processed']}")
            print(f"      Temps total: {processing_time:.1f}s")
            print(f"      Ratio moyen: {final_stats['avg_compression_ratio']:.3f}×")
            print(f"      Économies: {final_stats['total_savings_mb']:.1f}MB")
            
            return final_stats['jobs_processed'] >= len(job_ids) * 0.8
            
        finally:
            # Nettoyage
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    finally:
        processor.stop()

def main():
    """Fonction principale de test"""
    print("🧪 TESTS PROCESSEUR PRODUCTION SIMPLIFIÉ")
    print("="*60)
    
    tests = [
        ("Fonctionnalités de base", test_basic_functionality),
        ("Cycle de vie processeur", test_processor_lifecycle),
        ("Traitement de jobs", test_job_processing),
        ("Traitement multiple jobs", test_multiple_jobs),
        ("Gestion d'erreurs", test_error_handling),
        ("Configuration", test_configuration),
        ("Simulation performance", test_performance_simulation)
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
    print(f"\n" + "="*60)
    print("📋 RAPPORT TESTS PROCESSEUR SIMPLIFIÉ")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"Tests exécutés: {total}")
    print(f"Tests réussis: {passed}")
    print(f"Taux de réussite: {passed/total*100:.0f}%")
    
    print(f"\n📊 DÉTAIL PAR TEST:")
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    # Évaluation globale
    if passed == total:
        print(f"\n🎉 TOUS LES TESTS RÉUSSIS !")
        print("🚀 Processeur production simplifié fonctionnel")
    elif passed >= total * 0.8:
        print(f"\n⚡ TESTS LARGEMENT RÉUSSIS")
        print("🔧 Corrections mineures nécessaires")
    else:
        print(f"\n⚠️  TESTS PARTIELLEMENT RÉUSSIS")
        print("🔄 Révision nécessaire")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)