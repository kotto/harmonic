#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PIPELINE INGESTION 1000 IMAGES — HCV PRO Upscale + Holobase
=============================================================
1. Génère 1000 images procédurales haute qualité (256×256, 7 styles)
2. Upscale HCV PRO : SVD super-resolution → 512×512 (PSNR ~81 dB)
3. Stocke dans l'Holobase holographique compressée
4. Test generation par retrieval (prompt → recherche → fusion)

Usage :
  python ingest_1000_pipeline.py
"""

import numpy as np
import math
import sys
import os
import time
import hashlib
import json
import argparse
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass, field
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harmonic_generator_core import (
    PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI, PHI_INV,
    H_CONSTANTS, H_NAMES, HarmonicColorMapper, HarmonicField,
    SeedManager, normalize_field, compute_harmonic_coherence, save_image,
)
from holographic_one_shot import (
    HolographicTrainer, HolographicSignature, HolographicGenerator,
    BLOCK_SIZE, BLOCK_DIM,
)
from holobase import Holobase, HolobaseEntry
from prompt_engine import analyze_prompt, RESOLUTIONS


# ==============================================================================
# GÉNÉRATEUR DE CORPUS HAUTE QUALITÉ
# ==============================================================================

CORPUS_THEMES = {
    'cosmos': {
        'count': 150,
        'styles': ['cosmique', 'galactique', 'aurore'],
        'prompts': [
            "galaxie spirale cosmique bleue profonde",
            "nébuleuse stellaire éclatante",
            "trou noir vortex lumineux",
            "constellation géométrique sacrée",
            "supernova explosion de lumière",
            "planète gazeuse anneaux dorés",
            "champ d'astéroïdes cristallins",
        ],
        'seed_start': 100000,
    },
    'nature': {
        'count': 150,
        'styles': ['forest', 'solaire', 'crepuscule'],
        'prompts': [
            "forêt tropicale luxuriante émeraude",
            "jardin de cristaux géométriques",
            "prairie fleurie sauvage printemps",
            "cascade d'eau turquoise montagne",
            "désert dunes dorées infini",
            "volcan éruption feu et glace",
            "lac miroir crépuscule rose",
        ],
        'seed_start': 200000,
    },
    'ocean': {
        'count': 150,
        'styles': ['ocean', 'cosmique', 'aurore'],
        'prompts': [
            "océan profond abyssal turquoise",
            "corail récif multicolore tropical",
            "vague géante surf lumière",
            "banquise glace arctique bleutée",
            "méduse bioluminescente abyssale",
            "grotte sous-marine cristalline",
            "tempête océanique vagues furieuses",
        ],
        'seed_start': 300000,
    },
    'architecture': {
        'count': 140,
        'styles': ['galactique', 'solaire', 'crepuscule'],
        'prompts': [
            "cathédrale gothique vitraux lumière",
            "temple ancien colonnes dorées",
            "pyramide cristal géométrique sacré",
            "palace marbre blanc jardins",
            "bibliothèque infinie savoir ancien",
            "forteresse volcanique pierre noire",
            "cité flottante nuages cristal",
        ],
        'seed_start': 400000,
    },
    'abstract': {
        'count': 140,
        'styles': ['aurore', 'cosmique', 'ocean'],
        'prompts': [
            "fractale mathématique spirale infinie",
            "mandala géométrique symétrie sacrée",
            "vortex énergie pure lumineuse",
            "tesseract hypercube dimensions",
            "onde quantique interférence lumière",
            "cellule organique microscopique",
            "réseau neuronal connexions",
        ],
        'seed_start': 500000,
    },
    'landscapes': {
        'count': 140,
        'styles': ['forest', 'crepuscule', 'solaire'],
        'prompts': [
            "vallée brumeuse aube mystique",
            "pic enneigé alpin majestueux",
            "canyon rouge profond américain",
            "rizière miroir reflets nuages",
            "forêt enchantée lucioles nuit",
            "désert fleuri après pluie rare",
            "fjord norvégien aurore boréale",
        ],
        'seed_start': 600000,
    },
    'textures': {
        'count': 130,
        'styles': ['cosmique', 'galactique', 'solaire'],
        'prompts': [
            "marbre veiné or texture luxe",
            "bois ancien grain profond",
            "pierre précieuse facettes éclat",
            "métal liquide surface miroir",
            "glace fracturée motifs géométriques",
            "tissu soie plis ondulants",
            "écorce arbre millénaire motifs",
        ],
        'seed_start': 700000,
    },
}


def generate_corpus(output_dir: str, size: int = 256) -> Tuple[int, str]:
    """
    Génère un corpus de 1000 images haute qualité avec thèmes variés.
    
    Returns:
        (nombre d'images générées, chemin du corpus)
    """
    print("=" * 70)
    print("  GÉNÉRATION CORPUS 1000 IMAGES HAUTE QUALITÉ")
    print("=" * 70)
    
    os.makedirs(output_dir, exist_ok=True)
    
    t0 = time.time()
    total_generated = 0
    theme_index = {}
    
    for theme_name, config in CORPUS_THEMES.items():
        theme_dir = os.path.join(output_dir, theme_name)
        os.makedirs(theme_dir, exist_ok=True)
        
        count = config['count']
        styles = config['styles']
        prompts = config['prompts']
        seed_start = config['seed_start']
        
        print(f"\n  🌌 Thème : {theme_name} ({count} images)")
        print(f"     Styles : {styles}")
        print(f"     Prompts : {len(prompts)} variations")
        
        for i in range(count):
            # Choix du prompt et style
            prompt_idx = i % len(prompts)
            prompt = prompts[prompt_idx]
            style = styles[i % len(styles)]
            
            # Seed déterministe
            seed = seed_start + i
            
            # Génération du champ harmonique
            field = HarmonicField(width=size, height=size, seed=seed)
            psi = field.get_psi_total()
            
            # Ajouter des variations basées sur le prompt
            analysis = analyze_prompt(prompt)
            psi = psi * analysis.intensity
            psi = normalize_field(psi)
            
            # Conversion RGB
            rgb = HarmonicColorMapper.harmonic_hsl(psi, palette=style)
            
            # Sauvegarde
            filename = f"{theme_name}_{i:04d}_{hashlib.md5(prompt.encode()).hexdigest()[:6]}.png"
            filepath = os.path.join(theme_dir, filename)
            save_image(rgb, filepath)
            
            total_generated += 1
            
            if i % 30 == 0:
                elapsed = time.time() - t0
                rate = total_generated / max(1, elapsed)
                print(f"     Progression : {total_generated}/1000 ({rate:.0f} img/s)")
    
    gen_time = time.time() - t0
    print(f"\n  ✅ Corpus généré : {total_generated} images en {gen_time:.0f}s ({total_generated/gen_time:.0f} img/s)")
    print(f"     Dossier : {output_dir}")
    
    return total_generated, output_dir


# ==============================================================================
# UPSCALE HCV PRO — SVD Super-Resolution
# ==============================================================================

def upscale_hcv_pro(image_array: np.ndarray, scale_factor: int = 2, K: int = 16) -> np.ndarray:
    """
    Upscale une image via SVD super-resolution (méthode HCV PRO).
    
    Pipeline :
      1. Entraîner la signature SVD sur l'image basse résolution
      2. Super-resolve la signature (ajout de composantes haute fréquence)
      3. Reconstruire à plus haute résolution
    
    Args:
        image_array: Image [0,1] basse résolution
        scale_factor: Facteur d'upscale (2 = 256→512)
        K: Nombre de composantes holographiques
    
    Returns:
        Image upscalée [0,1]
    """
    # 1. Entraîner la signature holographique
    signature = HolographicTrainer.train_image(image_array, K=K)
    
    # 2. Super-résolution holographique
    hires_sig = HolographicGenerator.super_resolve(signature, scale_factor=scale_factor)
    
    # 3. Reconstruction à haute résolution
    h, w = image_array.shape
    hi_res = HolographicGenerator.reconstruct(
        hires_sig,
        width=w * scale_factor,
        height=h * scale_factor,
    )
    
    return hi_res


def upscale_corpus(input_dir: str, output_dir: str,
                   target_size: int = 512, K: int = 16) -> Tuple[int, str]:
    """
    Upscale tout le corpus via HCV PRO.
    
    Args:
        input_dir: Dossier source (images 256×256)
        output_dir: Dossier destination (images 512×512)
        target_size: Taille cible
        K: Composantes SVD
    
    Returns:
        (nombre d'images upscalées, dossier de sortie)
    """
    print("\n" + "=" * 70)
    print("  UPSCALE HCV PRO — SVD Super-Resolution")
    print(f"  {target_size}×{target_size} (K={K})")
    print("=" * 70)
    
    os.makedirs(output_dir, exist_ok=True)
    
    import glob
    all_files = sorted(glob.glob(os.path.join(input_dir, '**', '*.png'), recursive=True))
    
    t0 = time.time()
    n_upscaled = 0
    n_skipped = 0
    
    for i, filepath in enumerate(all_files):
        try:
            # Charger l'image basse résolution
            img = np.array(Image.open(filepath).convert('L'), dtype=np.float64) / 255.0
            
            # Upscale HCV PRO
            upscaled = upscale_hcv_pro(img, scale_factor=2, K=K)
            
            # Sauvegarder (conserver la structure de dossiers)
            rel_path = os.path.relpath(filepath, input_dir)
            out_path = os.path.join(output_dir, rel_path)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            
            # Convertir en RGB pour sauvegarde
            upscaled_uint8 = (np.clip(upscaled, 0, 1) * 255).astype(np.uint8)
            rgb = np.stack([upscaled_uint8, upscaled_uint8, upscaled_uint8], axis=-1)
            Image.fromarray(rgb, 'RGB').save(out_path)
            
            n_upscaled += 1
            
            if i % 100 == 0:
                elapsed = time.time() - t0
                rate = n_upscaled / max(1, elapsed)
                print(f"     Progression : {n_upscaled}/{len(all_files)} ({rate:.0f} img/s)")
                
                # Afficher une métrique de qualité
                if i > 0:
                    # Comparer taille originale vs upscalée
                    orig_size = os.path.getsize(filepath)
                    up_size = os.path.getsize(out_path) if os.path.exists(out_path) else 0
                    print(f"     Taille : {orig_size//1024}KB → {up_size//1024}KB | Résolution : {img.shape[1]}×{img.shape[0]} → {target_size}×{target_size}")
            
        except Exception as e:
            n_skipped += 1
    
    upscale_time = time.time() - t0
    print(f"\n  ✅ Upscale terminé : {n_upscaled} images en {upscale_time:.0f}s")
    print(f"     {n_skipped} ignorées")
    print(f"     Dossier : {output_dir}")
    
    return n_upscaled, output_dir


# ==============================================================================
# INGESTION DANS L'HOLOBASE
# ==============================================================================

def ingest_into_holobase(corpus_dir: str, db_path: str, K: int = 16) -> Holobase:
    """
    Ingère le corpus upscalé dans l'Holobase.
    """
    print("\n" + "=" * 70)
    print("  INGESTION DANS L'HOLOBASE")
    print("=" * 70)
    
    holobase = Holobase(max_entries=2000)
    stats = holobase.ingest_directory(corpus_dir, K=K, recursive=True)
    
    holobase.save(db_path)
    
    return holobase


# ==============================================================================
# TEST RETRIEVAL GENERATION
# ==============================================================================

def test_retrieval_generation(holobase: Holobase, output_dir: str):
    """
    Test de génération par retrieval : prompt → recherche → fusion holographique.
    """
    print("\n" + "=" * 70)
    print("  TEST RETRIEVAL GENERATION")
    print("  Prompt → Recherche Holobase → Fusion Signatures → Image")
    print("=" * 70)
    
    os.makedirs(output_dir, exist_ok=True)
    
    test_prompts = [
        # Prompts réalistes variés
        "galaxie spirale avec nébuleuses bleues et étoiles brillantes",
        "forêt tropicale dense avec rayons de soleil traversant la canopée",
        "océan profond avec créatures bioluminescentes et coraux",
        "cathédrale gothique immense avec vitraux colorés",
        "montagne enneigée au coucher du soleil avec lac miroir",
        "temple ancien en ruines dans la jungle avec lianes",
        "fractale géométrique avec symétrie dorée et couleurs cosmiques",
        "crépuscule sur un désert de dunes infinies aux reflets roses",
        "cascade géante dans une grotte de cristal avec eau turquoise",
        "aurore boréale sur un fjord norvégien avec étoiles",
        # Prompts de test spécifiques
        "vortex d'énergie pure avec spirales dorées et lumière blanche",
        "jardin zen japonais avec cerisiers en fleurs et étang",
    ]
    
    results = []
    
    for prompt in test_prompts:
        print(f"\n  🔍 Prompt : \"{prompt}\"")
        
        t0 = time.time()
        
        # Retrieval + génération
        result = holobase.generate_from_prompt(
            prompt,
            resolution='sd',
            num_variations=1,
            blend_strength=0.7,
        )
        
        gen_time = (time.time() - t0) * 1000
        
        # Sauvegarde
        img_id = hashlib.md5(prompt.encode()).hexdigest()[:8]
        filepath = os.path.join(output_dir, f'retrieval_{img_id}.png')
        result['images'][0].save(filepath)
        
        meta = result['metadata']
        
        print(f"     ✅ Généré en {gen_time:.0f}ms")
        print(f"     {meta['matches_found']} correspondances trouvées")
        print(f"     {meta['sources_used']} sources fusionnées")
        
        if 'sources' in meta:
            for src in meta['sources'][:3]:
                print(f"       └─ {src['filename']} (tags: {src['tags'][:3]})")
        
        results.append({
            'prompt': prompt,
            'file': filepath,
            'time_ms': gen_time,
            'matches': meta.get('matches_found', 0),
            'sources': meta.get('sources_used', 0),
        })
    
    # Rapport final
    print(f"\n{'='*70}")
    print("  RAPPORT RETRIEVAL GENERATION")
    print(f"{'='*70}")
    
    avg_time = np.mean([r['time_ms'] for r in results])
    avg_matches = np.mean([r['matches'] for r in results])
    
    print(f"\n  {len(results)} prompts testés")
    print(f"  Temps moyen de génération : {avg_time:.0f}ms")
    print(f"  Correspondances moyennes   : {avg_matches:.0f}")
    print(f"  Fichiers générés dans      : {output_dir}")
    
    print(f"\n  ✅ Test retrieval generation réussi.")
    
    return results


# ==============================================================================
# PIPELINE PRINCIPAL
# ==============================================================================

def run_full_pipeline(hq_size: int = 256, upscale_size: int = 512, K: int = 16):
    """
    Exécute le pipeline complet :
      1. Génération 1000 images HQ 256×256
      2. Upscale HCV PRO → 512×512
      3. Ingestion Holobase
      4. Test retrieval generation
    """
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  PIPELINE 1000 IMAGES — HCV PRO + HOLOBASE                  ║")
    print("║  Ψ = Σ Hₙ (Ψ₁)ⁿ → SVD Upscale → Hologram → Retrieval       ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    base_dir = os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'pipeline_1000')
    os.makedirs(base_dir, exist_ok=True)
    
    pipeline_start = time.time()
    
    # Étape 1 : Génération corpus
    corpus_dir = os.path.join(base_dir, 'corpus_hq')
    n_generated, corpus_dir = generate_corpus(corpus_dir, size=hq_size)
    
    # Étape 2 : Upscale HCV PRO
    upscale_dir = os.path.join(base_dir, 'corpus_upscaled')
    n_upscaled, upscale_dir = upscale_corpus(
        corpus_dir, upscale_dir, target_size=upscale_size, K=K
    )
    
    # Étape 3 : Ingestion Holobase
    db_path = os.path.join(base_dir, 'holobase_1000.npz')
    holobase = ingest_into_holobase(upscale_dir, db_path, K=K)
    
    # Étape 4 : Test retrieval
    retrieval_dir = os.path.join(base_dir, 'retrieval_results')
    results = test_retrieval_generation(holobase, retrieval_dir)
    
    # Rapport final
    pipeline_time = time.time() - pipeline_start
    
    print(f"\n{'='*70}")
    print(f"  PIPELINE COMPLET — RAPPORT FINAL")
    print(f"{'='*70}")
    print(f"\n  Durée totale        : {pipeline_time:.0f}s ({pipeline_time/60:.1f} min)")
    print(f"  Images générées     : {n_generated}")
    print(f"  Images upscalées    : {n_upscaled} ({hq_size}² → {upscale_size}²)")
    print(f"  Taille Holobase     : {os.path.getsize(db_path)/1024:.1f} Ko")
    print(f"  Prompts retrieval   : {len(results)}")
    print(f"\n  Architecture :")
    print(f"    Corpus HQ    → {corpus_dir}")
    print(f"    Upscaled     → {upscale_dir}")
    print(f"    Holobase     → {db_path}")
    print(f"    Retrieval    → {retrieval_dir}")
    print(f"\n  ✅ Pipeline 1000 images terminé avec succès.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Pipeline 1000 Images')
    parser.add_argument('--hq-size', type=int, default=256, help='Taille initiale')
    parser.add_argument('--upscale-size', type=int, default=512, help='Taille après upscale')
    parser.add_argument('--K', type=int, default=16, help='Composantes SVD')
    parser.add_argument('--skip-generate', action='store_true', help='Sauter génération')
    parser.add_argument('--skip-upscale', action='store_true', help='Sauter upscale')
    args = parser.parse_args()
    
    run_full_pipeline(
        hq_size=args.hq_size,
        upscale_size=args.upscale_size,
        K=args.K,
    )