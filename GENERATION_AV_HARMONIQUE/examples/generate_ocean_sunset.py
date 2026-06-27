#!/usr/bin/env python3
"""
Exemple : Génération d'un coucher de soleil sur l'océan
=========================================================
Génère 5 secondes de vidéo HD + audio synchronisé.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from engine.harmonic_av_core import HarmonicAVGenerator


def main():
    print("=" * 60)
    print("GÉNÉRATION AV HARMONIQUE")
    print("Coucher de soleil sur l'océan")
    print("=" * 60)
    
    # Créer le générateur
    gen = HarmonicAVGenerator()
    
    prompt = "Un coucher de soleil magnifique sur l'océan calme avec des vagues douces"
    
    print(f"\nPrompt : {prompt}")
    print("Génération en cours...")
    
    # Durée courte pour la démo
    result = gen.generate_from_prompt(
        prompt=prompt,
        duration_seconds=5.0,
        fps=12,  # Basse résolution pour la démo
        sample_rate=22050,
        resolution=(640, 360)  # 360p pour la démo
    )
    
    # Afficher les métadonnées
    print(f"\n✅ Génération terminée !")
    print(f"   Durée : {result.duration_seconds}s")
    print(f"   Audio : {len(result.audio_samples)} samples à {result.sample_rate} Hz")
    print(f"   Vidéo : {len(result.video_frames)} frames à {result.fps} fps")
    print(f"   Résolution : {result.resolution[0]}×{result.resolution[1]}")
    print(f"   Résonance audio : {result.resonance_audio:.2%}")
    print(f"   Résonance vidéo : {result.resonance_video:.2%}")
    print(f"   Sync AV : {result.av_sync_quality:.2%}")
    print(f"   Type de scène : {result.scene_type}")
    print(f"   Humeur : {result.mood}")
    print(f"   Temps de calcul : {result.processing_time_ms:.1f} ms")
    
    # Afficher un warning sur la qualité
    if result.resolution[0] < 1920:
        print(f"\n⚠️ Résolution réduite pour la démonstration.")
        print(f"   Pour la pleine qualité, utilisez resolution=(1920, 1080)")
    
    # Sauvegarder dans un fichier JSON pour inspection
    import json
    output = {
        'metadata': result.to_dict(),
        'audio_preview': result.audio_samples[:100],  # 100 premiers échantillons
        'video_first_frame_colors': {
            'top_left': result.video_frames[0][0][0] if result.video_frames else None,
            'center': result.video_frames[0][len(result.video_frames[0])//2][len(result.video_frames[0][0])//2] if result.video_frames else None,
        }
    }
    
    with open('ocean_sunset_result.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n📁 Résultat sauvegardé dans : ocean_sunset_result.json")
    print(f"   (Les frames vidéo et samples audio complets sont en mémoire)")


if __name__ == "__main__":
    main()