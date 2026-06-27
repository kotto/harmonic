import os
import tempfile
import cv2
import numpy as np
from server_quantum_harmonic_reference import extract_reference_chromatic_profile

print("Test minimal référence chromatique...")

# Test avec une vidéo existante
video_path = "test_video.mp4"  # À remplacer avec votre vidéo

if os.path.exists(video_path):
    print(f"Test avec: {video_path}")
    profile = extract_reference_chromatic_profile(video_path, sample_frame=0)
    
    if profile:
        print("✅ Profil extrait:")
        print(f"   RGB: [{profile['r_mean']:.1f}, {profile['g_mean']:.1f}, {profile['b_mean']:.1f}]")
        print(f"   Saturation: {profile['saturation_mean']:.1f}")
        print(f"   Luminosité: {profile['brightness_mean']:.1f}")
    else:
        print("❌ Échec extraction profil")
else:
    print(f"❌ Fichier non trouvé: {video_path}")
    print("Créez un fichier test_video.mp4 ou modifiez le chemin")

print("Test terminé")
