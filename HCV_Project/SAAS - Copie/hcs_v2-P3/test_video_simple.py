#!/usr/bin/env python3
"""
Test simple de compression vidéo avec métriques
"""

import requests
import time
import os
import json
import tempfile

def create_simple_video():
    """Créer une vidéo simple pour les tests"""
    
    try:
        import cv2
        import numpy as np
        
        # Vidéo très simple
        width, height = 640, 480
        fps = 10
        frames = 30
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        temp_path = tempfile.mktemp(suffix='.mp4')
        
        out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))
        
        for i in range(frames):
            # Frame simple avec dégradé
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Dégradé de couleur
            for y in range(height):
                for x in range(width):
                    frame[y, x] = [
                        int(255 * (i / frames)),
                        int(255 * (x / width)),
                        int(255 * (y / height))
                    ]
            
            # Ajouter un cercle mobile
            center_x = int(width/2 + 100 * (i / frames))
            center_y = int(height/2)
            cv2.circle(frame, (center_x, center_y), 30, (255, 255, 255), -1)
            
            out.write(frame)
        
        out.release()
        
        file_size = os.path.getsize(temp_path)
        print(f"✅ Vidéo simple créée: {os.path.basename(temp_path)}")
        print(f"📊 Taille: {file_size / 1024:.2f} KB")
        print(f"📊 Frames: {frames}")
        
        return temp_path
        
    except Exception as e:
        print(f"❌ Erreur création vidéo: {e}")
        return None

def test_compression_simple(video_path):
    """Test simple de compression"""
    
    print(f"\n🎬 Test compression: {os.path.basename(video_path)}")
    print("="*50)
    
    original_size = os.path.getsize(video_path)
    print(f"📊 Taille originale: {original_size / 1024:.2f} KB")
    
    try:
        # Lire le fichier
        with open(video_path, 'rb') as f:
            video_data = f.read()
        
        # Test compression harmonique
        print(f"\n🎵 Test compression harmonique...")
        
        start_time = time.time()
        
        files = {'file': (os.path.basename(video_path), video_data, 'video/mp4')}
        data = {'priority': 'balanced'}
        
        response = requests.post(
            "http://localhost:8000/api/v3/harmonic-compress",
            files=files,
            data=data
        )
        
        request_time = time.time() - start_time
        
        print(f"📊 Status: {response.status_code}")
        print(f"⏱️ Temps requête: {request_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print(f"✅ Compression réussie!")
                print(f"🎯 Méthode: {result.get('method', 'unknown')}")
                print(f"⏱️ Temps compression: {result.get('compression_time', 0):.2f}s")
                print(f"📊 Frames: {result.get('frame_count', 0)}")
                print(f"📊 Version: {result.get('version', 'unknown')}")
                
                # Métadonnées
                ref_metadata = result.get('reference_metadata', {})
                print(f"\n📸 Référence:")
                print(f"  📐 Résolution: {ref_metadata.get('resolution', 'N/A')}")
                print(f"  💡 Luminosité: {ref_metadata.get('brightness', 0):.2f}")
                print(f"  📊 Contraste: {ref_metadata.get('contrast', 0):.2f}")
                
                # Scores harmoniques
                harmonic_scores = result.get('harmonic_scores', {})
                if harmonic_scores:
                    print(f"\n🎵 Scores harmoniques:")
                    print(f"  📊 Score: {harmonic_scores.get('reference_harmonic_score', 0):.3f}")
                    print(f"  💡 Luminosité: {harmonic_scores.get('mean_brightness', 0):.2f}")
                    print(f"  📊 Écart-type: {harmonic_scores.get('std_brightness', 0):.2f}")
                
                return True
            else:
                print(f"❌ Erreur: {result.get('error', 'Erreur inconnue')}")
                return False
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            print(f"📊 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return False

def test_demo_complete(video_path):
    """Test démonstration complète"""
    
    print(f"\n🎭 Test démonstration complète...")
    print("="*50)
    
    try:
        with open(video_path, 'rb') as f:
            video_data = f.read()
        
        start_time = time.time()
        
        files = {'file': (os.path.basename(video_path), video_data, 'video/mp4')}
        data = {'priority': 'balanced'}
        
        response = requests.post(
            "http://localhost:8000/api/v3/harmonic-demo",
            files=files,
            data=data
        )
        
        request_time = time.time() - start_time
        
        print(f"📊 Status: {response.status_code}")
        print(f"⏱️ Temps total: {request_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print(f"✅ Démonstration réussie!")
                print(f"🎯 Méthode: {result.get('method', 'unknown')}")
                
                # Compression
                compression = result.get('compression', {})
                print(f"\n📼 Compression:")
                print(f"  ⏱️ Temps: {compression.get('time', 0):.2f}s")
                print(f"  📊 Frames: {compression.get('frames', 0)}")
                
                # Reconstruction
                reconstruction = result.get('reconstruction', {})
                print(f"\n🔄 Reconstruction:")
                print(f"  ⏱️ Temps: {reconstruction.get('time', 0):.2f}s")
                print(f"  📊 Frames: {reconstruction.get('frames', 0)}")
                print(f"  🎯 Qualité: {reconstruction.get('quality_score', 0):.2f}")
                
                # Performance
                performance = result.get('performance', {})
                print(f"\n📈 Performance:")
                print(f"  📊 Ratio: {performance.get('compression_ratio', 'N/A')}")
                print(f"  📈 Amélioration: {performance.get('quality_improvement', 'N/A')}")
                print(f"  🎵 Enhancement: {performance.get('harmonic_enhancement', False)}")
                
                return True
            else:
                print(f"❌ Erreur: {result.get('error', 'Erreur inconnue')}")
                return False
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            print(f"📊 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return False

def main():
    """Fonction principale"""
    
    print("🎬 Test Simple de Compression Vidéo")
    print("="*50)
    
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
    
    # Créer vidéo simple
    video_path = create_simple_video()
    
    if not video_path:
        print("❌ Impossible de créer la vidéo")
        return
    
    try:
        # Tests
        success1 = test_compression_simple(video_path)
        success2 = test_demo_complete(video_path)
        
        # Nettoyer
        if os.path.exists(video_path):
            os.unlink(video_path)
            print(f"\n🗑️ Fichier supprimé: {os.path.basename(video_path)}")
        
        # Résultats
        print(f"\n🎉 RÉSULTATS")
        print("="*50)
        print(f"🎵 Compression harmonique: {'✅ SUCCÈS' if success1 else '❌ ÉCHEC'}")
        print(f"🎭 Démonstration complète: {'✅ SUCCÈS' if success2 else '❌ ÉCHEC'}")
        
        if success1 and success2:
            print(f"\n🎉 TOUS LES TESTS RÉUSSIS!")
            print(f"🎯 Système harmonique opérationnel")
        elif success1 or success2:
            print(f"\n⚠️ TESTS PARTIELLEMENT RÉUSSIS")
        else:
            print(f"\n❌ TOUS LES TESTS EN ÉCHEC")
    
    except Exception as e:
        print(f"❌ Erreur générale: {e}")

if __name__ == "__main__":
    main()
