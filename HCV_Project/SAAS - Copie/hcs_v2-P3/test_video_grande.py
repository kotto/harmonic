#!/usr/bin/env python3
"""
Test de compression vidéo grande taille avec métriques détaillées
"""

import requests
import time
import os
import json
import tempfile

def create_large_video():
    """Créer une vidéo plus grande pour les tests"""
    
    try:
        import cv2
        import numpy as np
        
        # Vidéo plus grande et plus longue
        width, height = 1280, 720
        fps = 25
        frames = 75  # 3 secondes
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        temp_path = tempfile.mktemp(suffix='.mp4')
        
        out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))
        
        print(f"🎬 Création vidéo grande: {width}x{height}, {fps}fps, {frames} frames")
        
        for i in range(frames):
            # Frame complexe avec plusieurs éléments
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Fond dégradé animé
            t = i / frames
            for y in range(height):
                for x in range(width):
                    frame[y, x] = [
                        int(128 + 127 * np.sin(2 * np.pi * t + x/100)),
                        int(128 + 127 * np.cos(2 * np.pi * t + y/100)),
                        int(128 + 127 * np.sin(2 * np.pi * t + (x+y)/200))
                    ]
            
            # Plusieurs formes mobiles
            # Cercles
            for j in range(3):
                cx = int(width/2 + 200 * np.sin(2 * np.pi * t + j * 2*np.pi/3))
                cy = int(height/2 + 150 * np.cos(2 * np.pi * t + j * 2*np.pi/3))
                cv2.circle(frame, (cx, cy), 30 + j*10, (255, 255, 255), -1)
            
            # Rectangle rotatif
            rect_center = (width//2, height//2)
            rect_size = (150, 80)
            angle = i * 3
            rect = ((rect_center[0] - rect_size[0]//2, rect_center[1] - rect_size[1]//2), 
                    rect_size, angle)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            cv2.drawContours(frame, [box], 0, (0, 255, 0), 3)
            
            # Lignes diagonales
            cv2.line(frame, (0, 0), (width, height), (255, 0, 0), 2)
            cv2.line(frame, (width, 0), (0, height), (0, 0, 255), 2)
            
            # Texte
            cv2.putText(frame, f"Frame {i+1}/{frames}", 
                       (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            
            # Ajouter du bruit réaliste
            noise = np.random.randint(0, 30, (height, width, 3), dtype=np.uint8)
            frame = cv2.add(frame, noise)
            
            out.write(frame)
        
        out.release()
        
        file_size = os.path.getsize(temp_path)
        print(f"✅ Vidéo grande créée: {os.path.basename(temp_path)}")
        print(f"📊 Taille: {file_size / (1024*1024):.2f} MB")
        print(f"📊 Frames: {frames}")
        print(f"📊 Durée: {frames/fps:.1f}s")
        
        return temp_path
        
    except Exception as e:
        print(f"❌ Erreur création vidéo: {e}")
        return None

def test_compression_complete(video_path):
    """Test complet avec toutes les métriques"""
    
    print(f"\n🎬 Test complet: {os.path.basename(video_path)}")
    print("="*60)
    
    original_size = os.path.getsize(video_path)
    original_size_mb = original_size / (1024 * 1024)
    
    print(f"📊 Fichier original:")
    print(f"  📁 Taille: {original_size_mb:.2f} MB ({original_size:,} bytes)")
    
    try:
        with open(video_path, 'rb') as f:
            video_data = f.read()
        
        # Test 1: Compression harmonique seule
        print(f"\n🎵 Test 1: Compression Harmonique")
        print("-" * 40)
        
        start_time = time.time()
        
        files = {'file': (os.path.basename(video_path), video_data, 'video/mp4')}
        data = {'priority': 'balanced'}
        
        response = requests.post(
            "http://localhost:8000/api/v3/harmonic-compress",
            files=files,
            data=data
        )
        
        request_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print(f"✅ Compression harmonique réussie!")
                print(f"⏱️ Temps requête: {request_time:.2f}s")
                print(f"⏱️ Temps compression: {result.get('compression_time', 0):.2f}s")
                print(f"📊 Frames compressées: {result.get('frame_count', 0)}")
                print(f"🎯 Méthode: {result.get('method', 'unknown')}")
                print(f"📈 Version: {result.get('version', 'unknown')}")
                print(f"📊 Package size: {result.get('package_size', 0)} bytes")
                
                # Métadonnées détaillées
                ref_metadata = result.get('reference_metadata', {})
                print(f"\n📸 Métadonnées Référence:")
                print(f"  📐 Résolution: {ref_metadata.get('resolution', 'N/A')}")
                print(f"  🎨 Canaux: {ref_metadata.get('channels', 'N/A')}")
                print(f"  💡 Luminosité: {ref_metadata.get('brightness', 0):.2f}")
                print(f"  📊 Contraste: {ref_metadata.get('contrast', 0):.2f}")
                print(f"  📏 Type: {ref_metadata.get('dtype', 'N/A')}")
                
                # Scores harmoniques
                harmonic_scores = result.get('harmonic_scores', {})
                if harmonic_scores:
                    print(f"\n🎵 Scores Harmoniques:")
                    print(f"  📊 Score harmonique: {harmonic_scores.get('reference_harmonic_score', 0):.4f}")
                    print(f"  💡 Luminosité moyenne: {harmonic_scores.get('mean_brightness', 0):.2f}")
                    print(f"  📊 Écart-type luminosité: {harmonic_scores.get('std_brightness', 0):.2f}")
                
                # Calculer ratio de compression estimé
                compressed_size_estimate = result.get('package_size', 0)
                if compressed_size_estimate > 0:
                    ratio = original_size / compressed_size_estimate
                    space_saved = (1 - compressed_size_estimate / original_size) * 100
                    print(f"\n📈 Compression Estimée:")
                    print(f"  📊 Ratio: {ratio:.1f}x")
                    print(f"  💾 Espace économisé: {space_saved:.1f}%")
                
                compression_result = result
            else:
                print(f"❌ Erreur compression: {result.get('error', 'Erreur inconnue')}")
                compression_result = None
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            compression_result = None
        
        # Test 2: Démonstration complète
        print(f"\n🎭 Test 2: Démonstration Complète")
        print("-" * 40)
        
        start_time_demo = time.time()
        
        response_demo = requests.post(
            "http://localhost:8000/api/v3/harmonic-demo",
            files=files,
            data=data
        )
        
        request_time_demo = time.time() - start_time_demo
        
        if response_demo.status_code == 200:
            result_demo = response_demo.json()
            
            if result_demo.get('success'):
                print(f"✅ Démonstration complète réussie!")
                print(f"⏱️ Temps total: {request_time_demo:.2f}s")
                print(f"🎯 Méthode: {result_demo.get('method', 'unknown')}")
                
                # Détails compression
                compression = result_demo.get('compression', {})
                print(f"\n📼 Détails Compression:")
                print(f"  ⏱️ Temps: {compression.get('time', 0):.2f}s")
                print(f"  📊 Frames: {compression.get('frames', 0)}")
                print(f"  💡 Qualité référence: {compression.get('reference_quality', 0):.2f}")
                
                # Détails reconstruction
                reconstruction = result_demo.get('reconstruction', {})
                print(f"\n🔄 Détails Reconstruction:")
                print(f"  ⏱️ Temps: {reconstruction.get('time', 0):.2f}s")
                print(f"  📊 Frames: {reconstruction.get('frames', 0)}")
                print(f"  🎯 Score qualité: {reconstruction.get('quality_score', 0):.3f}")
                
                # Performance globale
                performance = result_demo.get('performance', {})
                print(f"\n📈 Performance Globale:")
                print(f"  📊 Ratio compression: {performance.get('compression_ratio', 'N/A')}")
                print(f"  📈 Amélioration qualité: {performance.get('quality_improvement', 'N/A')}")
                print(f"  🎵 Enhancement harmonique: {performance.get('harmonic_enhancement', False)}")
                print(f"  ⏱️ Temps total: {performance.get('total_time', 0):.2f}s")
                
                # Analyse harmonique
                harmonic_analysis = result_demo.get('harmonic_analysis', {})
                if harmonic_analysis:
                    print(f"\n🎵 Analyse Harmonique Détaillée:")
                    print(f"  📊 Score harmonique: {harmonic_analysis.get('harmonic_score', 0):.4f}")
                    print(f"  💡 Luminosité moyenne: {harmonic_analysis.get('mean_brightness', 0):.2f}")
                    print(f"  📊 Écart-type luminosité: {harmonic_analysis.get('std_brightness', 0):.2f}")
                    print(f"  ⚡ Énergie gradient: {harmonic_analysis.get('gradient_energy', 0):.2f}")
                
                demo_result = result_demo
            else:
                print(f"❌ Erreur démonstration: {result_demo.get('error', 'Erreur inconnue')}")
                demo_result = None
        else:
            print(f"❌ Erreur HTTP: {response_demo.status_code}")
            demo_result = None
        
        # Résumé final
        print(f"\n📊 RÉSUMÉ COMPLET")
        print("="*60)
        print(f"📁 Fichier original: {original_size_mb:.2f} MB")
        
        if compression_result:
            print(f"\n🎵 Compression Harmonique:")
            print(f"  ✅ Statut: SUCCÈS")
            print(f"  ⏱️ Temps: {compression_result.get('compression_time', 0):.2f}s")
            print(f"  📊 Frames: {compression_result.get('frame_count', 0)}")
            print(f"  🎯 Score harmonique: {harmonic_scores.get('reference_harmonic_score', 0):.4f}")
        
        if demo_result:
            print(f"\n🎭 Démonstration Complète:")
            print(f"  ✅ Statut: SUCCÈS")
            print(f"  ⏱️ Temps total: {demo_result.get('performance', {}).get('total_time', 0):.2f}s")
            print(f"  📊 Ratio: {demo_result.get('performance', {}).get('compression_ratio', 'N/A')}")
            print(f"  📈 Amélioration: {demo_result.get('performance', {}).get('quality_improvement', 'N/A')}")
            print(f"  🎯 Qualité: {demo_result.get('reconstruction', {}).get('quality_score', 0):.3f}")
        
        return {
            'original_size_mb': original_size_mb,
            'compression_success': compression_result is not None,
            'demo_success': demo_result is not None
        }
        
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return {'error': str(e)}

def main():
    """Fonction principale"""
    
    print("🎬 Test Compression Vidéo Grande Taille")
    print("="*60)
    
    # Vérifier serveur
    try:
        response = requests.get("http://localhost:8000/api/v3/health", timeout=5)
        if response.status_code == 200:
            print("✅ Serveur HCS actif")
        else:
            print("❌ Serveur HCS non disponible")
            return
    except:
        print("❌ Impossible de se connecter au serveur")
        return
    
    # Créer vidéo grande
    video_path = create_large_video()
    
    if not video_path:
        print("❌ Impossible de créer la vidéo")
        return
    
    try:
        # Lancer test complet
        results = test_compression_complete(video_path)
        
        # Nettoyer
        if os.path.exists(video_path):
            os.unlink(video_path)
            print(f"\n🗑️ Fichier supprimé: {os.path.basename(video_path)}")
        
        # Conclusion
        print(f"\n🎉 TESTS TERMINÉS")
        print("="*60)
        
        if 'error' not in results:
            if results.get('compression_success') and results.get('demo_success'):
                print("🎉 TOUS LES TESTS RÉUSSIS!")
                print("🎯 Système harmonique parfaitement opérationnel")
                print(f"📊 Fichier testé: {results.get('original_size_mb', 0):.2f} MB")
            elif results.get('compression_success') or results.get('demo_success'):
                print("⚠️ TESTS PARTIELLEMENT RÉUSSIS")
            else:
                print("❌ TESTS EN ÉCHEC")
        else:
            print(f"❌ Erreur: {results.get('error')}")
    
    except Exception as e:
        print(f"❌ Erreur générale: {e}")

if __name__ == "__main__":
    main()
