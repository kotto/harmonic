"""
Harmonic Dictionary Builder
============================
Construit un dictionnaire harmonique à partir d'un corpus d'images.

Usage:
    python build_dict.py --corpus ./images/ --output ./dict.hdb --patch_size 16 --K 8
    python build_dict.py --corpus ./images/ --quality fast    # mode rapide
    python build_dict.py --corpus ./images/ --quality deep    # mode qualité maximale

Le dictionnaire entraîné peut ensuite être chargé par HarmonicCodec pour
une compression optimale (IDs au lieu de patches bruts).
"""

import sys
import os
import argparse
import time
import math
from pathlib import Path
import numpy as np

_ENGINE_DIR = Path(__file__).resolve().parent.parent
if str(_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_ENGINE_DIR))

from multimodal.harmonic_database import HarmonicDatabase


def discover_images(corpus_dir: str, extensions: set = None) -> list:
    """Découvre toutes les images dans un répertoire (récursif)."""
    if extensions is None:
        extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.gif'}
    
    images = []
    corpus = Path(corpus_dir)
    if not corpus.exists():
        raise FileNotFoundError(f"Répertoire introuvable: {corpus_dir}")
    
    for ext in extensions:
        images.extend(corpus.rglob(f'*{ext}'))
        images.extend(corpus.rglob(f'*{ext.upper()}'))
    
    return sorted(set(images))


def load_image(path: Path, max_size: int = 2048) -> np.ndarray:
    """Charge une image en RGB uint8, redimensionnée si > max_size."""
    try:
        import cv2
        img = cv2.imread(str(path))
        if img is None:
            return None
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    except ImportError:
        try:
            from PIL import Image
            img = np.array(Image.open(path).convert('RGB'))
        except Exception:
            return None
    
    H, W = img.shape[:2]
    if max(H, W) > max_size:
        scale = max_size / max(H, W)
        new_h, new_w = int(H * scale), int(W * scale)
        try:
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        except:
            img = np.array(Image.fromarray(img).resize((new_w, new_h), Image.LANCZOS))
    
    return img


def build_dictionary(
    corpus_dir: str,
    output_path: str = None,
    patch_size: int = 16,
    K: int = 8,
    stride: int = None,
    shard_size: int = 50000,
    quality: str = 'balanced',
    max_images: int = None,
    verbose: bool = True,
) -> HarmonicDatabase:
    """
    Construit un dictionnaire harmonique.
    
    Args:
        corpus_dir: répertoire d'images
        output_path: chemin de sauvegarde (optionnel)
        patch_size: taille des patches
        K: nombre de coefficients DFT
        stride: pas entre patches (défaut: patch_size // 2 pour qualité, patch_size pour rapide)
        shard_size: patches max par shard
        quality: 'fast', 'balanced', 'deep'
        max_images: nombre max d'images (None = toutes)
        verbose: afficher la progression
    
    Returns:
        HarmonicDatabase entraînée
    """
    if stride is None:
        stride = patch_size if quality == 'fast' else max(patch_size // 2, 4)
    
    t0 = time.perf_counter()
    
    # Découvrir les images
    images = discover_images(corpus_dir)
    if not images:
        raise ValueError(f"Aucune image trouvée dans {corpus_dir}")
    
    if max_images:
        images = images[:max_images]
    
    if verbose:
        print(f"📂 {len(images)} images trouvées dans {corpus_dir}")
        print(f"🔧 patch_size={patch_size} K={K} stride={stride} quality={quality}")
    
    # Créer la database
    db = HarmonicDatabase(
        patch_size=patch_size,
        K=K,
        stride=stride,
        shard_size=shard_size,
        shard_dir=output_path + '.shards' if output_path else None,
    )
    
    total_patches = 0
    total_images_ok = 0
    
    for idx, img_path in enumerate(images):
        try:
            img = load_image(img_path)
            if img is None:
                continue
            
            H, W = img.shape[:2]
            ps = patch_size
            st = stride
            
            # Extraire le concept du nom du fichier/dossier
            concept = img_path.parent.name if img_path.parent.name != corpus_dir else 'default'
            
            # Ingérer les patches
            n_patches = 0
            for y in range(0, H - ps + 1, st):
                for x in range(0, W - ps + 1, st):
                    patch = img[y:y+ps, x:x+ps].copy()
                    db.ingest(patch, concept=concept)
                    n_patches += 1
            
            total_patches += n_patches
            total_images_ok += 1
            
            if verbose and (idx + 1) % max(1, len(images) // 10) == 0:
                elapsed = time.perf_counter() - t0
                print(f"  [{idx+1}/{len(images)}] {total_patches:,} patches "
                      f"({total_patches/max(elapsed,0.01):.0f} patches/s)")
        
        except Exception as e:
            if verbose:
                print(f"  ⚠️ {img_path.name}: {e}")
    
    # Flush le buffer d'ingestion
    db.flush()
    
    elapsed = time.perf_counter() - t0
    
    if verbose:
        print(f"\n✅ Dictionnaire construit en {elapsed:.1f}s")
        print(f"   {total_images_ok} images → {total_patches:,} patches")
        print(f"   {len(db._shards)} shards")
        print(f"   {total_patches/max(elapsed, 0.01):.0f} patches/s")
    
    # Sauvegarder
    if output_path:
        db.save(output_path)
        if verbose:
            size_mb = os.path.getsize(output_path) / (1024*1024)
            print(f"   Sauvegardé: {output_path} ({size_mb:.1f} MB)")
    
    return db


def main():
    parser = argparse.ArgumentParser(
        description='Harmonic Dictionary Builder — Construit un dictionnaire de patches',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python build_dict.py --corpus ./photos/ --output ./dict.hdb
  python build_dict.py --corpus ./images/ --quality fast --max-images 100
  python build_dict.py --corpus ./dataset/ --patch-size 32 --K 16 --quality deep
        """
    )
    parser.add_argument('--corpus', required=True, help='Répertoire d\'images')
    parser.add_argument('--output', default='./harmonic_dict.hdb', help='Fichier de sortie')
    parser.add_argument('--patch-size', type=int, default=16, help='Taille des patches (défaut: 16)')
    parser.add_argument('--K', type=int, default=8, help='Coefficients DFT (défaut: 8)')
    parser.add_argument('--stride', type=int, default=None, help='Pas entre patches')
    parser.add_argument('--shard-size', type=int, default=50000, help='Patches par shard')
    parser.add_argument('--quality', choices=['fast', 'balanced', 'deep'], default='balanced',
                       help='Qualité du dictionnaire')
    parser.add_argument('--max-images', type=int, default=None, help='Nombre max d\'images')
    parser.add_argument('--quiet', action='store_true', help='Mode silencieux')
    
    args = parser.parse_args()
    
    build_dictionary(
        corpus_dir=args.corpus,
        output_path=args.output,
        patch_size=args.patch_size,
        K=args.K,
        stride=args.stride,
        shard_size=args.shard_size,
        quality=args.quality,
        max_images=args.max_images,
        verbose=not args.quiet,
    )


if __name__ == '__main__':
    main()
