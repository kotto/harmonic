#!/usr/bin/env python3
"""
Test avec Vraie Vidéo
Test du système avec vos fichiers vidéo réels
"""

import os
import sys
import time
from pathlib import Path

# Ajout des chemins
sys.path.append('h264_hcv16_recompression/src')
sys.path.append('h264_hcv16_production/core')

def find_video_files():
    """Recherche fichiers vidéo dans le répertoire courant"""
    video_extensions = ['.mp4', '.avi', '.mkv', '.mov']
    video_files = []
    
    for ext in video_extensions:
        files = list(Path('.').glob(f'*{ext}'))
        video_files.extend(files)
    
    return [str(f) for f in video_files]

def analyze_real_video(video_path):
    """Analyse complète d'une vraie vidéo"""
    print(f"🎬 ANALYSE VIDÉO RÉELLE: {os.path.basename(video_path)}")
    print("="*60)
    
    try:
        from h264_analyzer import H264Analyzer
        
        analyzer = H264Analyzer()
        
        # Informations de base
        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
        print(f"📁 Taille fichier: {file_size_mb:.1f} MB")
        
        # Analyse complète
        print(f"\n📊 Analyse en cours...")
        start_time = time.time()
        
        analysis = analyzer.analyze_file(video_path, max_frames=50)
        
        analysis_time = time.time() - start_time
        print(f"⏱️ Temps d'analyse: {analysis_time:.1f}s")
        
        # Affichage résultats détaillés
        print(f"\n" + analyzer.generate_report())
        
        return analysis
        
    except Exception as e:
        print(f"❌ Erreur analyse: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_cascade_on_real_video(video_path, analysis):
    """Test cascade sur vraie vidéo"""
    print(f"\n🔄 TEST OPTIMISATION CASCADE")
    print("-"*40)
    
    try:
        from cascade_optimizer import CascadeOptimizer
        
        opportunities = analysis['hcv16_opportunities']
        estimated_ratio = opportunities['estimated_compression_ratio']
        
        print(f"📊 Ratio estimé direct: {estimated_ratio:.3f}×")
        
        if estimated_ratio < 1.03:
            print(f"⚠️ Gains limités attendus, cascade non recommandée")
            return None
        
        # Test cascade
        optimizer = CascadeOptimizer()
        output_file = video_path.replace(Path(video_path).suffix, '_cascade_optimized.hcv16')
        
        print(f"🚀 Lancement optimisation cascade...")
        start_time = time.time()
        
        results = optimizer.optimize_cascade(
            input_h264=video_path,
            output_hcv16=output_file,
            max_iterations=2  # Limité pour test rapide
        )
        
        processing_time = time.time() - start_time
        
        if results['success']:
            print(f"\n✅ OPTIMISATION RÉUSSIE !")
            print(f"   Temps traitement: {processing_time:.1f}s")
            print(f"   Itérations: {results['iterations_performed']}")
            print(f"   Ratio direct: {results['initial_estimated_ratio']:.3f}×")
            print(f"   Ratio cascade: {results['actual_final_ratio']:.3f}×")
            print(f"   Amélioration: +{results['cascade_improvement_percent']:.1f}%")
            print(f"   Fichier créé: {output_file}")
            print(f"   Recommandation: {results['recommendation']}")
            
            # Comparaison tailles
            original_size = results['original_size'] / (1024*1024)
            final_size = results['final_size'] / (1024*1024)
            savings = original_size - final_size
            
            print(f"\n💾 ÉCONOMIES:")
            print(f"   Taille originale: {original_size:.1f} MB")
            print(f"   Taille compressée: {final_size:.1f} MB")
            print(f"   Économie: {savings:.1f} MB ({(savings/original_size)*100:.1f}%)")
            
        else:
            print(f"❌ Optimisation échouée")
            
        return results
        
    except Exception as e:
        print(f"❌ Erreur cascade: {e}")
        return None

def test_simple_processor(video_path):
    """Test avec processeur simple"""
    print(f"\n⚡ TEST PROCESSEUR SIMPLE")
    print("-"*30)
    
    try:
        from simple_processor import SimpleProductionProcessor
        
        processor = SimpleProductionProcessor()
        processor.start()
        
        output_file = video_path.replace(Path(video_path).suffix, '_simple_compressed.hcv16')
        
        print(f"📤 Soumission job...")
        job_id = processor.submit_job(video_path, output_file)
        
        # Attente traitement
        print(f"⏳ Traitement en cours...")
        timeout = 60
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = processor.get_job_status(job_id)
            
            if status['status'] == 'completed':
                result = status['result']
                print(f"✅ Traitement réussi !")
                print(f"   Ratio: {result.compression_ratio:.3f}×")
                print(f"   Temps: {result.processing_time:.1f}s")
                print(f"   Fichier: {output_file}")
                break
            elif status['status'] == 'failed':
                print(f"❌ Traitement échoué")
                break
            
            time.sleep(1)
        
        processor.stop()
        
    except Exception as e:
        print(f"❌ Erreur processeur: {e}")

def interactive_video_test():
    """Test interactif avec sélection vidéo"""
    print("🎬 TEST INTERACTIF AVEC VRAIE VIDÉO")
    print("="*50)
    
    # Recherche fichiers vidéo
    video_files = find_video_files()
    
    if video_files:
        print(f"\n📁 Fichiers vidéo trouvés:")
        for i, file in enumerate(video_files, 1):
            size_mb = os.path.getsize(file) / (1024*1024)
            print(f"   {i}. {file} ({size_mb:.1f} MB)")
        
        print(f"   {len(video_files)+1}. Spécifier un autre fichier")
        
        try:
            choice = int(input(f"\nChoisissez un fichier (1-{len(video_files)+1}): "))
            
            if 1 <= choice <= len(video_files):
                video_path = video_files[choice-1]
            else:
                video_path = input("Chemin vers votre fichier vidéo: ").strip()
        except ValueError:
            video_path = input("Chemin vers votre fichier vidéo: ").strip()
    else:
        print(f"\n📁 Aucun fichier vidéo trouvé dans le répertoire courant")
        video_path = input("Chemin vers votre fichier vidéo: ").strip()
    
    if not os.path.exists(video_path):
        print(f"❌ Fichier non trouvé: {video_path}")
        return
    
    # Tests
    print(f"\n🎯 TESTS DISPONIBLES:")
    print(f"1. Analyse seule (rapide)")
    print(f"2. Analyse + Cascade (complet)")
    print(f"3. Analyse + Processeur simple")
    print(f"4. Tous les tests")
    
    try:
        test_choice = int(input("Votre choix (1-4): "))
    except ValueError:
        test_choice = 1
    
    # Analyse de base (toujours)
    analysis = analyze_real_video(video_path)
    
    if not analysis:
        print("❌ Impossible de continuer sans analyse")
        return
    
    # Tests selon choix
    if test_choice in [2, 4]:
        test_cascade_on_real_video(video_path, analysis)
    
    if test_choice in [3, 4]:
        test_simple_processor(video_path)
    
    print(f"\n🎉 Tests terminés !")
    print(f"📁 Vérifiez les fichiers de sortie créés")

def quick_video_test(video_path):
    """Test rapide avec fichier spécifique"""
    if not os.path.exists(video_path):
        print(f"❌ Fichier non trouvé: {video_path}")
        return
    
    print(f"⚡ TEST RAPIDE: {os.path.basename(video_path)}")
    
    # Analyse rapide
    analysis = analyze_real_video(video_path)
    
    if analysis:
        opportunities = analysis['hcv16_opportunities']
        ratio = opportunities['estimated_compression_ratio']
        
        if ratio >= 1.05:
            print(f"\n🚀 Gains intéressants détectés ({ratio:.3f}×)")
            print(f"💡 Recommandation: Tester optimisation cascade")
        else:
            print(f"\n⚠️ Gains limités ({ratio:.3f}×)")
            print(f"💡 Recommandation: Compression directe suffisante")

if __name__ == "__main__":
    print("🎬 TEST AVEC VRAIE VIDÉO H.264")
    print("="*40)
    
    if len(sys.argv) > 1:
        # Fichier spécifié en argument
        video_path = sys.argv[1]
        quick_video_test(video_path)
    else:
        # Mode interactif
        interactive_video_test()