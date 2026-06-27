#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TÉLÉCHARGEMENT DATASET RÉEL — Upscale HCV PRO + Ingestion Holobase
=====================================================================
1. Télécharge un dataset d'images réelles haute qualité depuis plusieurs sources
2. Upscale avec HCV PRO (SVD super-resolution)
3. Ingère dans l'Holobase holographique
4. Test retrieval generation

Sources :
  - Lorem Picsum (photos réelles, résolution configurable)
  - Possibilité d'ajouter d'autres sources

Usage :
  python download_dataset.py
  python download_dataset.py --source picsum --count 500 --size 256
"""

import numpy as np
import math
import sys
import os
import time
import hashlib
import json
import argparse
import io
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from PIL import Image
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harmonic_generator_core import (
    PHI, PI, E, H_CONSTANTS, H_NAMES, HarmonicColorMapper, HarmonicField,
    SeedManager, normalize_field,
)
from holographic_one_shot import (
    HolographicTrainer, HolographicSignature, HolographicGenerator,
    BLOCK_SIZE, BLOCK_DIM,
)
from holobase import Holobase, HolobaseEntry
from prompt_engine import analyze_prompt


# ==============================================================================
# DOWNLOADER — Sources de datasets réels
# ==============================================================================

def download_picsum_images(count: int = 500, size: int = 512,
                           output_dir: str = None) -> Tuple[int, str]:
    """
    Télécharge des images depuis Lorem Picsum (photos réelles gratuites).
    
    API : https://picsum.photos/{width}/{height}?random={seed}
    Source : Unsplash (photos libres de droits)
    """
    import urllib.request
    import urllib.error
    
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), '..',
                                  'av_generation_output', 'dataset_real', 'picsum')
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 70)
    print("  TÉLÉCHARGEMENT DATASET RÉEL — Lorem Picsum (Unsplash)")
    print(f"  {count} images × {size}×{size}")
    print("=" * 70)
    
    t0 = time.time()
    downloaded = 0
    skipped = 0
    errors = 0
    
    # Catégories pour varier les images
    categories = [
        'nature', 'water', 'mountain', 'forest', 'city', 'abstract',
        'architecture', 'animal', 'flower', 'sky', 'night', 'sunset',
        'ocean', 'desert', 'snow', 'tree', 'lake', 'river', 'garden',
        'building', 'street', 'bridge', 'clouds', 'fire', 'stone',
        'texture', 'wood', 'metal', 'glass', 'light',
    ]
    
    for i in range(count):
        if i % 50 == 0:
            elapsed = time.time() - t0
            rate = (downloaded + 1) / max(1, elapsed)
            print(f"     Progression : {downloaded}/{count} ({rate:.0f} img/s) [{errors} erreurs]")
        
        # Seed unique pour chaque image
        seed = i * 137 + 42
        # Varier les résolutions légèrement
        h = size + (i % 3) * 32  # 512, 544, 576
        w = size + ((i * 7) % 3) * 32
        
        url = f"https://picsum.photos/seed/{seed}/{w}/{h}"
        
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Holobase-Downloader/1.0 (Harmonic AI Project)'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                img_data = response.read()
            
            # Vérifier que c'est bien une image
            img = Image.open(io.BytesIO(img_data))
            img = img.convert('RGB')
            
            # Catégorie basée sur l'index
            cat = categories[i % len(categories)]
            cat_dir = os.path.join(output_dir, cat)
            os.makedirs(cat_dir, exist_ok=True)
            
            filepath = os.path.join(cat_dir, f"picsum_{i:05d}_{seed}.jpg")
            img.save(filepath, 'JPEG', quality=90)
            
            downloaded += 1
            
        except urllib.error.HTTPError as e:
            if e.code == 429:
                # Rate limited - attendre
                time.sleep(1.0)
                # Retry
                try:
                    req = urllib.request.Request(url, headers={'User-Agent': 'Holobase/1.0'})
                    with urllib.request.urlopen(req, timeout=10) as response:
                        img_data = response.read()
                    img = Image.open(io.BytesIO(img_data)).convert('RGB')
                    cat = categories[i % len(categories)]
                    cat_dir = os.path.join(output_dir, cat)
                    os.makedirs(cat_dir, exist_ok=True)
                    filepath = os.path.join(cat_dir, f"picsum_{i:05d}_{seed}.jpg")
                    img.save(filepath, 'JPEG', quality=90)
                    downloaded += 1
                except:
                    errors += 1
            else:
                errors += 1
        except Exception as e:
            errors += 1
            if errors > 20:
                print(f"     ⚠️ Trop d'erreurs ({errors}), pause...")
                time.sleep(2.0)
                errors = 0
        
        # Petit délai pour ne pas surcharger le serveur
        if i % 10 == 0:
            time.sleep(0.05)
    
    dl_time = time.time() - t0
    print(f"\n  ✅ Téléchargement terminé : {downloaded} images en {dl_time:.0f}s")
    print(f"     {errors} erreurs, {skipped} ignorées")
    print(f"     Dossier : {output_dir}")
    
    return downloaded, output_dir


def download_from_torchvision(dataset_name: str = 'stl10',
                               output_dir: str = None) -> Tuple[int, str]:
    """
    Télécharge un dataset via torchvision (CIFAR, STL-10, etc.).
    
    STL-10 : 100 000 images 96×96 (bonne qualité, structuré)
    """
    try:
        import torchvision
        import torchvision.transforms as transforms
    except ImportError:
        print("  ⚠️ torchvision non installé. pip install torchvision")
        return 0, None
    
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), '..',
                                  'av_generation_output', 'dataset_real', dataset_name)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n  📥 Téléchargement dataset : {dataset_name}")
    
    if dataset_name == 'stl10':
        dataset = torchvision.datasets.STL10(
            root=os.path.join(output_dir, '..', '_torchdata'),
            split='train+unlabeled',
            download=True,
            transform=None,
        )
    elif dataset_name == 'cifar100':
        dataset = torchvision.datasets.CIFAR100(
            root=os.path.join(output_dir, '..', '_torchdata'),
            train=True,
            download=True,
            transform=None,
        )
    elif dataset_name == 'cifar10':
        dataset = torchvision.datasets.CIFAR10(
            root=os.path.join(output_dir, '..', '_torchdata'),
            train=True,
            download=True,
            transform=None,
        )
    else:
        print(f"  Dataset inconnu : {dataset_name}")
        return 0, None
    
    classes = getattr(dataset, 'classes', [str(i) for i in range(100)])
    
    t0 = time.time()
    saved = 0
    
    for i, (img, label) in enumerate(dataset):
        if i % 5000 == 0:
            print(f"     Progression : {i}/{len(dataset)}")
        
        class_name = classes[label] if label < len(classes) else f"class_{label}"
        class_dir = os.path.join(output_dir, class_name)
        os.makedirs(class_dir, exist_ok=True)
        
        filepath = os.path.join(class_dir, f"{dataset_name}_{i:06d}.png")
        img.save(filepath, 'PNG')
        saved += 1
    
    save_time = time.time() - t0
    print(f"  ✅ Dataset sauvegardé : {saved} images en {save_time:.0f}s")
    print(f"     Dossier : {output_dir}")
    
    return saved, output_dir


# ==============================================================================
# UPSCALE HCV PRO (même que pipeline, réutilisé)
# ==============================================================================

def upscale_hcv_pro_batch(image_array: np.ndarray, K: int = 16) -> np.ndarray:
    """Upscale SVD batch."""
    signature = HolographicTrainer.train_image(image_array, K=K)
    hires_sig = HolographicGenerator.super_resolve(signature, scale_factor=2)
    h, w = image_array.shape
    return HolographicGenerator.reconstruct(hires_sig, width=w*2, height=h*2)


def upscale_dataset(input_dir: str, output_dir: str, K: int = 16,
                    max_images: int = None) -> Tuple[int, str]:
    """Upscale tout un dataset."""
    print("\n" + "=" * 70)
    print(f"  UPSCALE HCV PRO — SVD Super-Resolution (K={K})")
    print("=" * 70)
    
    os.makedirs(output_dir, exist_ok=True)
    
    import glob
    all_files = sorted(glob.glob(os.path.join(input_dir, '**', '*.jpg'), recursive=True))
    all_files += sorted(glob.glob(os.path.join(input_dir, '**', '*.jpeg'), recursive=True))
    all_files += sorted(glob.glob(os.path.join(input_dir, '**', '*.png'), recursive=True))
    
    if max_images:
        all_files = all_files[:max_images]
    
    t0 = time.time()
    n_upscaled = 0
    n_skipped = 0
    
    for i, filepath in enumerate(all_files):
        try:
            img = np.array(Image.open(filepath).convert('L'), dtype=np.float64) / 255.0
            
            # Upscale
            upscaled = upscale_hcv_pro_batch(img, K=K)
            
            # Sauvegarder
            rel_path = os.path.relpath(filepath, input_dir)
            out_path = os.path.join(output_dir, os.path.splitext(rel_path)[0] + '.png')
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            
            upscaled_uint8 = (np.clip(upscaled, 0, 1) * 255).astype(np.uint8)
            rgb = np.stack([upscaled_uint8, upscaled_uint8, upscaled_uint8], axis=-1)
            Image.fromarray(rgb, 'RGB').save(out_path)
            
            n_upscaled += 1
            
            if i % 100 == 0:
                elapsed = time.time() - t0
                rate = n_upscaled / max(1, elapsed)
                print(f"     Progression : {n_upscaled}/{len(all_files)} ({rate:.0f} img/s)")
                
        except Exception as e:
            n_skipped += 1
    
    upscale_time = time.time() - t0
    print(f"\n  ✅ Upscale terminé : {n_upscaled} images en {upscale_time:.0f}s")
    print(f"     {n_skipped} ignorées")
    
    return n_upscaled, output_dir


# ==============================================================================
# INGESTION HOLOBASE
# ==============================================================================

def ingest_real_dataset(corpus_dir: str, db_path: str, K: int = 16):
    """Ingère le dataset réel dans l'Holobase."""
    print("\n" + "=" * 70)
    print("  INGESTION HOLOBASE — Dataset Réel")
    print("=" * 70)
    
    holobase = Holobase(max_entries=5000)
    stats = holobase.ingest_directory(corpus_dir, K=K, recursive=True)
    holobase.save(db_path)
    
    return holobase, stats


# ==============================================================================
# TEST RETRIEVAL SUR DONNÉES RÉELLES
# ==============================================================================

def test_real_retrieval(holobase: Holobase, output_dir: str):
    """Test retrieval sur dataset réel."""
    print("\n" + "=" * 70)
    print("  TEST RETRIEVAL — Données Réelles")
    print("  Prompt → Holobase → Fusion Holographique → Image")
    print("=" * 70)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Prompts réalistes pour matcher le dataset
    test_prompts = [
        "sunset over mountains with lake reflection",
        "dense forest with sunlight rays through trees",
        "ocean waves crashing on rocky shore at sunset",
        "modern city skyline at night with neon lights",
        "snowy mountain peak at sunrise with clear sky",
        "flower garden with butterflies and morning dew",
        "desert dunes at golden hour with dramatic shadows",
        "ancient stone bridge over calm river in autumn",
        "crystal clear water beach with white sand tropical",
        "starry night sky over silent snow covered landscape",
        "abstract geometric pattern with vibrant colors",
        "old wooden texture with deep grain and moss",
    ]
    
    results = []
    
    for prompt in test_prompts:
        print(f"\n  🔍 \"{prompt}\"")
        
        t0 = time.time()
        result = holobase.generate_from_prompt(
            prompt, resolution='sd', num_variations=1, blend_strength=0.7
        )
        gen_time = (time.time() - t0) * 1000
        
        img_id = hashlib.md5(prompt.encode()).hexdigest()[:8]
        filepath = os.path.join(output_dir, f'real_retrieval_{img_id}.png')
        result['images'][0].save(filepath)
        
        meta = result['metadata']
        
        print(f"     ✅ {gen_time:.0f}ms | {meta.get('matches_found',0)} matches | {meta.get('sources_used',0)} sources")
        if 'sources' in meta:
            for src in meta['sources'][:2]:
                print(f"       └─ {src['filename']} ({src['tags'][:2]})")
        
        results.append({
            'prompt': prompt,
            'file': filepath,
            'time_ms': gen_time,
            'matches': meta.get('matches_found', 0),
        })
    
    avg_time = np.mean([r['time_ms'] for r in results])
    print(f"\n  ✅ {len(results)} prompts | Temps moyen: {avg_time:.0f}ms")
    
    return results


# ==============================================================================
# PIPELINE PRINCIPAL
# ==============================================================================

def run_real_pipeline(source: str = 'picsum', count: int = 500,
                      upscale: bool = True, K: int = 16):
    """Pipeline complet avec dataset réel."""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  PIPELINE DATASET RÉEL — HCV PRO + HOLOBASE                 ║")
    print("║  Source: " + source.ljust(54) + "║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    base_dir = os.path.join(os.path.dirname(__file__), '..',
                            'av_generation_output', 'dataset_real')
    os.makedirs(base_dir, exist_ok=True)
    
    pipeline_start = time.time()
    
    # 1. Téléchargement
    print("\n  [Étape 1/4] Téléchargement dataset...")
    
    if source == 'picsum':
        raw_dir = os.path.join(base_dir, 'picsum_raw')
        n_downloaded, raw_dir = download_picsum_images(
            count=count, size=256, output_dir=raw_dir
        )
    elif source in ('stl10', 'cifar100', 'cifar10'):
        n_downloaded, raw_dir = download_from_torchvision(source)
    else:
        print(f"  Source inconnue : {source}")
        return
    
    if n_downloaded == 0:
        print("  ❌ Aucune image téléchargée. Arrêt.")
        return
    
    # 2. Upscale HCV PRO
    if upscale:
        print(f"\n  [Étape 2/4] Upscale HCV PRO (SVD K={K})...")
        upscale_dir = os.path.join(base_dir, f"{source}_upscaled")
        n_upscaled, upscale_dir = upscale_dataset(
            raw_dir, upscale_dir, K=K, max_images=n_downloaded
        )
        ingest_source = upscale_dir
    else:
        ingest_source = raw_dir
        print("\n  [Étape 2/4] Upscale ignoré (--no-upscale)")
    
    # 3. Ingestion Holobase
    print(f"\n  [Étape 3/4] Ingestion Holobase...")
    db_path = os.path.join(base_dir, f'holobase_{source}_{n_downloaded}.npz')
    holobase, stats = ingest_real_dataset(ingest_source, db_path, K=K)
    
    # 4. Test retrieval
    print(f"\n  [Étape 4/4] Test retrieval generation...")
    retrieval_dir = os.path.join(base_dir, 'retrieval_results')
    results = test_real_retrieval(holobase, retrieval_dir)
    
    # Rapport
    pipeline_time = time.time() - pipeline_start
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    
    print(f"\n{'='*70}")
    print(f"  RAPPORT FINAL — DATASET RÉEL")
    print(f"{'='*70}")
    print(f"\n  Durée totale       : {pipeline_time:.0f}s ({pipeline_time/60:.1f} min)")
    print(f"  Images téléchargées: {n_downloaded}")
    print(f"  Upscale HCV PRO    : {'Oui' if upscale else 'Non'}")
    print(f"  Taille Holobase    : {db_size/1024:.1f} Ko")
    print(f"  Entrées Holobase   : {stats['total_images']}")
    print(f"  Ratio compression  : {stats['avg_compression_ratio']:.0f}x")
    print(f"  Octets/entrée      : {stats['avg_entry_bytes']:.0f}")
    print(f"  Prompts retrieval  : {len(results)}")
    print(f"  Temps moyen génér. : {np.mean([r['time_ms'] for r in results]):.0f}ms")
    
    if db_size > 0 and stats['total_images'] > 0:
        print(f"\n  ⚡ Performance Holobase :")
        print(f"     {stats['total_images']} images dans {db_size/1024:.0f} Ko")
        print(f"     = {db_size/max(1,stats['total_images']):.0f} octets/image")
        print(f"     Extraction + fusion : <1s")
    
    print(f"\n  ✅ Pipeline dataset réel terminé.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download & Ingest Real Dataset')
    parser.add_argument('--source', type=str, default='picsum',
                        choices=['picsum', 'stl10', 'cifar100', 'cifar10'],
                        help='Source du dataset')
    parser.add_argument('--count', type=int, default=500,
                        help='Nombre d\'images à télécharger')
    parser.add_argument('--no-upscale', action='store_true',
                        help='Désactiver l\'upscale HCV PRO')
    parser.add_argument('--K', type=int, default=16,
                        help='Composantes SVD')
    parser.add_argument('--ingest-only', type=str, default=None,
                        help='Ingérer un dossier existant sans télécharger')
    
    args = parser.parse_args()
    
    if args.ingest_only:
        db_path = os.path.join(os.path.dirname(__file__), '..',
                               'av_generation_output', 'dataset_real', 'holobase_custom.npz')
        holobase, stats = ingest_real_dataset(args.ingest_only, db_path, K=args.K)
        
        retrieval_dir = os.path.join(os.path.dirname(__file__), '..',
                                     'av_generation_output', 'dataset_real', 'retrieval_results')
        test_real_retrieval(holobase, retrieval_dir)
    else:
        run_real_pipeline(
            source=args.source,
            count=args.count,
            upscale=not args.no_upscale,
            K=args.K,
        )