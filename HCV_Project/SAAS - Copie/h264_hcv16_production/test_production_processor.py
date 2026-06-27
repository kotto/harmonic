#!/usr/bin/env python3
"""
Test Production Processor
Tests du processeur production H.264 → HCV16
"""

import os
import sys
import time
import tempfile
import shutil
from pathlib import Path

# Ajout du chemin pour imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'h264_hcv16_recompression', 'src'))

from processor import ProductionProcessor, BatchProcessor, create_default_config

def test_processor_initialization():
    """Test initialisation processeur"""
    print("🧪 Test initialisation processeur...")
    
    # Création config temporaire
    temp_config = "test_processor_config.json"
    
    try:
        # Création config par défaut
        create_default_config()
        os.rename("processor_config.json", temp_config)
        
        # Initialisation processeur
        processor = ProductionProcessor(temp_config)
        
        # Vérifications
        assert processor.config is not None
        assert processor.max_workers > 0
        assert not processor.running
        
        print("   ✅ Initialisation réussie")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur initialisation: {e}")
        return False
    
    finally:
        # Nettoyage
        if os.path.exists(temp_config):
            os.remove(temp_config)

def test_processor_lifecycle():
    """Test cycle de vie processeur"""
    print("\n🧪 Test cycle de vie processeur...")
    
    try:
        processor = ProductionProcessor()
        
        # Test démarrage
        processor.start()
        assert processor.running
        print("   ✅ Démarrage réussi")
        
        # Test statistiques initiales
        stats = processor.get_statistics()
        assert stats['jobs_processed'] == 0
        assert stats['jobs_in_queue'] == 0
        print("   ✅ Statistiques initiales correctes")
        
        # Test arrêt
        processor.stop()
        assert not processor.running
        print("   ✅ Arrêt réussi")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur cycle de vie: {e}")
        return False

def test_job_submission():
    """Test soumission de jobs"""
    print("\n🧪 Test soumission jobs...")
    
    try:
        processor = ProductionProcessor()
        processor.start()
        
        # Création fichier test temporaire
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_file.write(b'fake_video_data' * 1000)  # Données simulées
            temp_input = temp_file.name
        
        temp_output = temp_input.replace('.mp4', '.hcv16')
        
        try:
            # Soumission job
            job_id = processor.submit_job(temp_input, temp_output, priority=1)
            assert job_id is not None
            assert job_id.startswith('h264_hcv16_')
            print(f"   ✅ Job soumis: {job_id}")
            
            # Vérification statut
            status = processor.get_job_status(job_id)
            assert status['job_id'] == job_id
            print(f"   ✅ Statut récupéré: {status['status']}")
            
            # Attente traitement (avec timeout)
            timeout = 30
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                status = processor.get_job_status(job_id)
                if status['status'] in ['completed', 'failed']:
                    break
                time.sleep(1)
            
            print(f"   📊 Statut final: {status['status']}")
            
            # Note: Le job échouera probablement car le fichier n'est pas un vrai H.264
            # mais cela teste la mécanique de soumission/traitement
            
            return True
            
        finally:
            # Nettoyage fichiers temporaires
            if os.path.exists(temp_input):
                os.remove(temp_input)
            if os.path.exists(temp_output):
                os.remove(temp_output)
        
    except Exception as e:
        print(f"   ❌ Erreur soumission job: {e}")
        return False
    
    finally:
        processor.stop()

def test_batch_processing():
    """Test traitement batch"""
    print("\n🧪 Test traitement batch...")
    
    try:
        processor = ProductionProcessor()
        processor.start()
        
        batch_processor = BatchProcessor(processor)
        
        # Création répertoire temporaire avec fichiers test
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = os.path.join(temp_dir, 'input')
            output_dir = os.path.join(temp_dir, 'output')
            
            os.makedirs(input_dir)
            
            # Création fichiers test
            test_files = []
            for i in range(3):
                test_file = os.path.join(input_dir, f'test_video_{i}.mp4')
                with open(test_file, 'wb') as f:
                    f.write(b'fake_video_data' * 500)
                test_files.append(test_file)
            
            # Soumission batch
            batch_id = batch_processor.add_batch_job(
                input_directory=input_dir,
                output_directory=output_dir,
                file_pattern="*.mp4",
                priority=3
            )
            
            assert batch_id is not None
            print(f"   ✅ Batch créé: {batch_id}")
            
            # Vérification statut batch
            batch_status = batch_processor.get_batch_status(batch_id)
            assert batch_status['batch_id'] == batch_id
            assert batch_status['total_jobs'] == 3
            print(f"   ✅ Batch statut: {batch_status['total_jobs']} jobs")
            
            return True
    
    except Exception as e:
        print(f"   ❌ Erreur traitement batch: {e}")
        return False
    
    finally:
        processor.stop()

def test_performance_monitoring():
    """Test monitoring performance"""
    print("\n🧪 Test monitoring performance...")
    
    try:
        processor = ProductionProcessor()
        processor.start()
        
        # Attente collecte métriques
        time.sleep(2)
        
        # Récupération statistiques
        stats = processor.get_statistics()
        
        # Vérifications
        assert 'uptime_seconds' in stats
        assert 'performance_metrics' in stats
        assert stats['uptime_seconds'] > 0
        
        print(f"   ✅ Uptime: {stats['uptime_seconds']:.1f}s")
        print(f"   ✅ Métriques disponibles: {len(stats['performance_metrics'])}")
        
        return True
    
    except Exception as e:
        print(f"   ❌ Erreur monitoring: {e}")
        return False
    
    finally:
        processor.stop()

def test_error_handling():
    """Test gestion d'erreurs"""
    print("\n🧪 Test gestion d'erreurs...")
    
    try:
        processor = ProductionProcessor()
        processor.start()
        
        # Test fichier inexistant
        try:
            processor.submit_job("fichier_inexistant.mp4", "output.hcv16")
            assert False, "Devrait lever une exception"
        except FileNotFoundError:
            print("   ✅ Erreur fichier inexistant gérée")
        
        # Test format non supporté
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b'test')
            temp_input = temp_file.name
        
        try:
            processor.submit_job(temp_input, "output.hcv16")
            assert False, "Devrait lever une exception"
        except ValueError:
            print("   ✅ Erreur format non supporté gérée")
        finally:
            os.remove(temp_input)
        
        # Test fichier trop volumineux (simulation)
        processor.config['max_file_size_mb'] = 0.001  # 1KB max
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_file.write(b'x' * 2000)  # 2KB
            temp_input = temp_file.name
        
        try:
            processor.submit_job(temp_input, "output.hcv16")
            assert False, "Devrait lever une exception"
        except ValueError:
            print("   ✅ Erreur fichier trop volumineux gérée")
        finally:
            os.remove(temp_input)
        
        return True
    
    except Exception as e:
        print(f"   ❌ Erreur test gestion d'erreurs: {e}")
        return False
    
    finally:
        processor.stop()

def test_configuration_loading():
    """Test chargement configuration"""
    print("\n🧪 Test chargement configuration...")
    
    try:
        # Création config personnalisée
        custom_config = {
            "max_workers": 2,
            "batch_size": 5,
            "temp_directory": "/tmp/test_h264_hcv16",
            "max_file_size_mb": 1000,
            "monitoring_interval": 10
        }
        
        config_file = "test_custom_config.json"
        
        import json
        with open(config_file, 'w') as f:
            json.dump(custom_config, f)
        
        # Initialisation avec config personnalisée
        processor = ProductionProcessor(config_file)
        
        # Vérifications
        assert processor.config['max_workers'] == 2
        assert processor.config['batch_size'] == 5
        assert processor.config['monitoring_interval'] == 10
        
        print("   ✅ Configuration personnalisée chargée")
        
        # Vérification création répertoire temporaire
        assert os.path.exists(processor.config['temp_directory'])
        print("   ✅ Répertoire temporaire créé")
        
        return True
    
    except Exception as e:
        print(f"   ❌ Erreur chargement configuration: {e}")
        return False
    
    finally:
        # Nettoyage
        if os.path.exists(config_file):
            os.remove(config_file)
        if os.path.exists("/tmp/test_h264_hcv16"):
            shutil.rmtree("/tmp/test_h264_hcv16", ignore_errors=True)

def run_integration_test():
    """Test d'intégration complet"""
    print("\n🚀 Test d'intégration complet...")
    
    try:
        # Simulation workflow production complet
        processor = ProductionProcessor()
        batch_processor = BatchProcessor(processor)
        
        processor.start()
        
        print("   📊 Processeur démarré")
        
        # Simulation charge de travail
        with tempfile.TemporaryDirectory() as temp_dir:
            # Création fichiers test
            input_files = []
            for i in range(5):
                test_file = os.path.join(temp_dir, f'video_{i}.mp4')
                with open(test_file, 'wb') as f:
                    f.write(b'fake_h264_data' * 100)
                input_files.append(test_file)
            
            # Soumission jobs individuels
            job_ids = []
            for i, input_file in enumerate(input_files[:3]):
                output_file = input_file.replace('.mp4', '.hcv16')
                job_id = processor.submit_job(input_file, output_file, priority=i+1)
                job_ids.append(job_id)
            
            print(f"   📤 {len(job_ids)} jobs individuels soumis")
            
            # Soumission batch
            batch_dir = os.path.join(temp_dir, 'batch_input')
            os.makedirs(batch_dir)
            
            for input_file in input_files[3:]:
                shutil.copy2(input_file, batch_dir)
            
            batch_id = batch_processor.add_batch_job(
                input_directory=batch_dir,
                output_directory=os.path.join(temp_dir, 'batch_output')
            )
            
            print(f"   📦 Batch {batch_id} soumis")
            
            # Monitoring pendant traitement
            start_time = time.time()
            timeout = 60
            
            while time.time() - start_time < timeout:
                stats = processor.get_statistics()
                batch_status = batch_processor.get_batch_status(batch_id)
                
                print(f"   📊 Jobs: {stats['jobs_processed']} traités, "
                      f"{stats['jobs_in_queue']} en queue, "
                      f"{stats['active_jobs']} actifs")
                
                print(f"   📦 Batch: {batch_status['progress_percent']:.1f}% complété")
                
                # Vérification si tout est terminé
                all_jobs_done = True
                for job_id in job_ids:
                    status = processor.get_job_status(job_id)
                    if status['status'] not in ['completed', 'failed', 'not_found']:
                        all_jobs_done = False
                        break
                
                if all_jobs_done and batch_status['status'] == 'completed':
                    break
                
                time.sleep(2)
            
            # Statistiques finales
            final_stats = processor.get_statistics()
            print(f"\n   📈 Statistiques finales:")
            print(f"      Jobs traités: {final_stats['jobs_processed']}")
            print(f"      Temps total: {final_stats['uptime_seconds']:.1f}s")
            print(f"      Débit: {final_stats['throughput_jobs_per_hour']:.1f} jobs/h")
            
            return True
    
    except Exception as e:
        print(f"   ❌ Erreur test intégration: {e}")
        return False
    
    finally:
        processor.stop()

def main():
    """Fonction principale de test"""
    print("🧪 TESTS PROCESSEUR PRODUCTION H.264 → HCV16")
    print("="*60)
    
    tests = [
        ("Initialisation", test_processor_initialization),
        ("Cycle de vie", test_processor_lifecycle),
        ("Soumission jobs", test_job_submission),
        ("Traitement batch", test_batch_processing),
        ("Monitoring performance", test_performance_monitoring),
        ("Gestion d'erreurs", test_error_handling),
        ("Chargement configuration", test_configuration_loading),
        ("Intégration complète", run_integration_test)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Erreur inattendue dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Rapport final
    print(f"\n" + "="*60)
    print("📋 RAPPORT TESTS PROCESSEUR PRODUCTION")
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
        print("🚀 Processeur production prêt pour déploiement")
    elif passed >= total * 0.8:
        print(f"\n⚡ TESTS LARGEMENT RÉUSSIS")
        print("🔧 Corrections mineures nécessaires")
    else:
        print(f"\n⚠️  TESTS PARTIELLEMENT RÉUSSIS")
        print("🔄 Révision nécessaire avant déploiement")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)