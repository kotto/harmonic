#!/usr/bin/env python3
"""
Script de test pour le pipeline vidéo quantique-harmonique
Crée une vidéo de test et lance l'upscaling
"""

import cv2
import numpy as np
import os
import sys

def create_test_video(output_path: str = "test_video.mp4", duration: int = 5, fps: int = 30):
    """Crée une vidéo de test avec des patterns intéressants"""
    
    print(f"🎬 Création vidéo de test: {output_path}")
    print(f"📊 Durée: {duration}s @ {fps} fps")
    
    # Configuration
    width, height = 640, 480
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    total_frames = duration * fps
    
    for frame_idx in range(total_frames):
        # Création de patterns animés
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Temps normalisé
        t = frame_idx / fps
        
        # Pattern 1: Cercles harmoniques
        center_x, center_y = width // 2, height // 2
        for i in range(3):
            radius = 50 + i * 30 + 20 * np.sin(2 * np.pi * t / 2)
            color = [
                int(128 + 127 * np.sin(2 * np.pi * t / 3 + i * 2 * np.pi / 3)),
                int(128 + 127 * np.cos(2 * np.pi * t / 3 + i * 2 * np.pi / 3)),
                int(128 + 127 * np.sin(2 * np.pi * t / 4 + i * 2 * np.pi / 3))
            ]
            cv2.circle(frame, (center_x, center_y), int(radius), color, -1)
        
        # Pattern 2: Ondes mobiles
        for y in range(0, height, 20):
            for x in range(0, width, 20):
                wave = np.sin(2 * np.pi * (x / 100 + t)) * np.cos(2 * np.pi * (y / 100 + t * 0.5))
                intensity = int((wave + 1) * 127)
                frame[y:y+10, x:x+10] = [intensity, intensity // 2, 255 - intensity]
        
        # Pattern 3: Texte animé
        text = f"Frame {frame_idx:04d}"
        cv2.putText(frame, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Pattern 4: Mouvement brownien simulé
        if frame_idx > 0:
            # Ajout de "bruit" cohérent pour simuler le mouvement
            noise = np.random.normal(0, 5, (height, width, 3))
            frame = np.clip(frame.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        
        out.write(frame)
        
        # Progression
        if frame_idx % 30 == 0:
            progress = (frame_idx / total_frames) * 100
            print(f"📈 Création vidéo: {progress:.1f}%")
    
    out.release()
    print(f"✅ Vidéo de test créée: {output_path}")
    return output_path

def test_video_upscaler():
    """Test complet du pipeline vidéo"""
    
    print("🚀 TEST DU PIPELINE VIDÉO QUANTIQUE-HARMONIQUE")
    print("=" * 60)
    
    # 1. Création vidéo de test
    test_video_path = create_test_video(
        output_path="test_quantum_video.mp4",
        duration=3,  # 3 secondes pour test rapide
        fps=15      # 15 fps pour accélérer
    )
    
    if not os.path.exists(test_video_path):
        print("❌ Échec de création de la vidéo de test")
        return False
    
    # 2. Import du pipeline vidéo
    try:
        from core.quantum_harmonic_video_upscaler import QuantumHarmonicVideoUpscaler
        print("✅ Pipeline vidéo importé avec succès")
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    
    # 3. Lancement du test
    try:
        video_upscaler = QuantumHarmonicVideoUpscaler()
        
        print("\n🌊 Lancement de l'upscaling vidéo...")
        results = video_upscaler.upscale_video(
            video_path=test_video_path,
            target_resolution="1080p",  # 1080p pour test rapide
            energy_level="standard",
            output_path="test_upscaled_video"
        )
        
        if results:
            print(f"\n🎉 Test réussi! {len(results)} frames upscalées")
            
            # Vérification des fichiers de sortie
            output_files = [
                "test_upscaled_video/frames/frame_000000.png",
                "test_upscaled_video/upscaled_video.mp4",
                "test_upscaled_video/video_upscaling_report.json"
            ]
            
            print("\n📁 Fichiers générés:")
            for file_path in output_files:
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    print(f"  ✅ {file_path} ({size} bytes)")
                else:
                    print(f"  ❌ {file_path} (manquant)")
            
            return True
        else:
            print("❌ Aucun résultat généré")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Point d'entrée principal"""
    print("🎬 QUANTUM HARMONIC VIDEO UPSCALER - TEST SUITE")
    print("=" * 60)
    
    # Vérification des dépendances
    try:
        import cv2
        import numpy as np
        print("✅ Dépendances OK")
    except ImportError as e:
        print(f"❌ Dépendance manquante: {e}")
        print("Installez avec: pip install opencv-python numpy")
        return
    
    # Lancement du test
    success = test_video_upscaler()
    
    if success:
        print("\n🎉 TEST VIDÉO TERMINÉ AVEC SUCCÈS!")
        print("\n📊 Prochaines étapes:")
        print("  1. Examiner les frames upscalées dans test_upscaled_video/frames/")
        print("  2. Lire le rapport dans test_upscaled_video/video_upscaling_report.json")
        print("  3. Jouer la vidéo upscalée: test_upscaled_video/upscaled_video.mp4")
        print("  4. Adapter les paramètres pour vos vidéos")
    else:
        print("\n❌ TEST ÉCHOUÉ")
        print("Vérifiez les erreurs ci-dessus et réessayez")

if __name__ == "__main__":
    main()
