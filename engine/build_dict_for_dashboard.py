#!/usr/bin/env python3
"""build_dict_for_dashboard.py — Construit le dictionnaire pour le dashboard HCV2."""
import sys, os, tempfile, shutil
from pathlib import Path
import numpy as np
from PIL import Image

# Ajouter le projet au path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from multimodal.build_dict import build_dictionary

# Générer un corpus synthétique varié pour le dictionnaire
def generer_corpus(n_images=30, dest_dir="dictionaries/corpus"):
    os.makedirs(dest_dir, exist_ok=True)
    rng = np.random.default_rng(42)
    for i in range(n_images):
        h, w = 128, 128  # Plus petit pour éviter les problèmes mémoire
        img = np.ones((h, w, 3), dtype=np.uint8) * 128
        t = i % 5
        yy, xx = np.mgrid[:h, :w]
        if t == 0:  # Portrait
            cx, cy = w//2, h//2
            face = ((xx-cx)/40)**2 + ((yy-cy)/50)**2 < 1
            img[face] = (240, 210, 180)
        elif t == 1:  # Paysage
            img[yy < h//2] = (135, 190, 235)
            img[yy >= h//2] = (100, 130, 100)
        elif t == 2:  # Texture damier
            for y in range(0, h, 8):
                for x in range(0, w, 8):
                    if (x//8 + y//8) % 2 == 0:
                        img[y:y+8, x:x+8] = (200, 200, 200)
        elif t == 3:  # Texte
            img = np.ones((h, w, 3), dtype=np.uint8) * 255
            for y in range(0, h, 10):
                img[y:y+1, :] = 0
        elif t == 4:  # Grain
            img = np.ones((h, w, 3), dtype=np.uint8) * 60
            img += rng.integers(-15, 15, (h, w, 3), dtype=np.int16).clip(0, 255).astype(np.uint8)
        
        Image.fromarray(img).save(os.path.join(dest_dir, f"img_{i:04d}.png"))
    
    print(f"Corpus : {n_images} images générées dans {dest_dir}")
    return dest_dir

print("=" * 78)
print("CONSTRUCTION DU DICTIONNAIRE HARMONIQUE POUR LE DASHBOARD")
print("=" * 78)

# 1. Générer le corpus
corpus = generer_corpus(50, "dictionaries/corpus")

# 2. Construire le dictionnaire
output = "dictionaries/broadcast.hdb"
print(f"\nConstruction du dictionnaire vers {output}...")
print("(Cette opération peut prendre plusieurs minutes)")

try:
    db = build_dictionary(
        corpus_dir=corpus,
        output_path=output,
        patch_size=16,
        K=8,
        quality='balanced',
        max_images=50,
        verbose=True,
    )
    print(f"\n✅ Dictionnaire créé : {output}")
    print(f"   {db.size()} patches")
except Exception as e:
    print(f"\n❌ Erreur : {e}")
    # Fallback: dictionnaire minimal
    print("\nCréation d'un dictionnaire minimal de secours...")
    from multimodal.harmonic_database import HarmonicDatabase
    db = HarmonicDatabase()
    from multimodal.build_dict import extract_patches
    # Extraire des patches du corpus
    for img_file in list(Path(corpus).glob("*.png"))[:10]:
        img = np.array(Image.open(img_file).convert('RGB'))
        patches = extract_patches(img, 16, 8)
        for p in patches:
            db.add(p)
    db.build_index()
    db.save(output)
    print(f"✅ Dictionnaire minimal créé : {output} ({db.size()} patches)")

# Nettoyage
# shutil.rmtree(corpus)  # Décommenter pour nettoyer

print(f"\nVérification : le fichier existe ? {Path(output).exists()} ({Path(output).stat().st_size if Path(output).exists() else 0} octets)")
print("\nRedémarrez le dashboard pour utiliser le nouveau dictionnaire.")