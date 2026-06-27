#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GÉNÉRATEUR D'IMAGES HARMONIQUES
=================================
Basé sur la Théorie Harmonique : Ψ = Σ Hₙ (Ψ₁)ⁿ

Transforme un champ harmonique en images visuelles structurées :
  - Textures procédurales infinies
  - Paysages abstraits harmoniques
  - Mandalas et figures géométriques
  - Effets cosmiques et nébuleuses
  - Art génératif basé sur les 7 constantes

Chaque seed produit une image unique et déterministe.
Les 7 couches Hₙ sont combinées en RGB avec pondérations ajustables.

Usage :
  python harmonic_image_generator.py --demo
  python harmonic_image_generator.py --seed "univers" --style cosmique --size 1024
  python harmonic_image_generator.py --batch 7 --palettes all
"""

import numpy as np
import math
import sys
import os
import argparse
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from PIL import Image

# Ajouter le chemin pour le core
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harmonic_generator_core import (
    HarmonicField, HarmonicColorMapper,
    PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI, PHI_INV,
    H_CONSTANTS, H_NAMES, H_ROLES_IMAGE,
    normalize_field, blend_fields,
    compute_harmonic_coherence, compute_symmetry_score,
    compute_golden_ratio_score, SeedManager,
    FREQUENCE_FONDAMENTALE, ANGLE_HARMONIQUE
)


class HarmonicImageGenerator:
    """
    Générateur d'images harmoniques complet.
    
    Pipeline :
      1. Seed → Ψ₁ (champ fondamental)
      2. Ψ₁ → 7 couches Hₙ (Ψ₁)ⁿ
      3. Couches → Ψ total (Σ)
      4. Ψ → RGB (mapping couleur harmonique)
      5. Post-processing optionnel
    """
    
    STYLES = list(HarmonicColorMapper.PALETTES.keys())
    DEFAULT_SIZE = 512
    
    def __init__(self, width: int = 512, height: int = 512, seed: int = 42):
        self.width = width
        self.height = height
        self.seed = seed
        self.field = HarmonicField(width=width, height=height, seed=seed, n_layers=7)
        self._cache = {}
    
    def generate(self, style: str = 'cosmique',
                 layer_weights: Optional[np.ndarray] = None,
                 color_mode: str = 'hsl') -> np.ndarray:
        """
        Génère une image harmonique RGB.
        
        Args:
            style: Palette ('cosmique', 'solaire', 'forest', 'ocean', 'aurore', 'crepuscule', 'galactique')
            layer_weights: Pondérations optionnelles des 7 couches [w1..w7]
            color_mode: 'hsl' (teinte+luminosité) ou 'multilayer' (couches colorées)
        
        Returns:
            Array RGB uint8 (height, width, 3)
        """
        psi = self.field.get_psi_total()
        
        if color_mode == 'multilayer':
            layers = self.field._layers or self.field.compute_layers()
            return HarmonicColorMapper.multi_layer_rgb(layers, palette=style)
        else:
            return HarmonicColorMapper.harmonic_hsl(
                psi, palette=style, layer_weights=layer_weights
            )
    
    def generate_with_depth(self, style: str = 'cosmique') -> Tuple[np.ndarray, np.ndarray]:
        """Génère une image RGB + une carte de profondeur."""
        psi = self.field.get_psi_total()
        rgb = HarmonicColorMapper.harmonic_hsl(psi, palette=style)
        depth = HarmonicColorMapper.depth_map(psi)
        return rgb, depth
    
    def change_seed(self, new_seed: int):
        """Change le seed et régénère le champ."""
        self.seed = new_seed
        self.field.regenerate(seed=new_seed)
        self._cache = {}
    
    def get_metrics(self) -> Dict[str, float]:
        """Retourne les métriques de qualité de l'image générée."""
        psi = self.field.get_psi_total()
        return {
            'coherence_harmonique': compute_harmonic_coherence(psi),
            'symetrie': compute_symmetry_score(psi),
            'score_dore': compute_golden_ratio_score(psi),
            'energie_totale': float(np.sum(psi**2)),
        }
    
    def get_layer_info(self) -> List[Dict[str, Any]]:
        """Informations détaillées sur chaque couche."""
        info = []
        for n in range(1, 8):
            contrib = self.field.get_layer_contribution(n)
            info.append({
                'couche': n,
                'constante': H_NAMES[n-1],
                'valeur': float(H_CONSTANTS[n-1]),
                'contribution': contrib,
                'role': H_ROLES_IMAGE[n-1],
            })
        return info


def create_mandala(field: HarmonicField, radius: float = 0.8,
                   n_petals: int = 12, style: str = 'cosmique') -> np.ndarray:
    """
    Crée un mandala harmonique à partir du champ fondamental.
    
    Le mandala est une figure circulaire où les pétales suivent φ (n_petals=φ*7≈12).
    """
    psi = field.get_psi_total()
    h, w = psi.shape
    
    cx, cy = w / 2, h / 2
    max_r = min(w, h) / 2 * radius
    
    # Grille polaire
    Y, X = np.ogrid[:h, :w]
    X = X - cx
    Y = Y - cy
    R = np.sqrt(X**2 + Y**2)
    theta = np.arctan2(Y, X) % (2 * PI)
    
    # Masque circulaire
    mask = R <= max_r
    
    # Modulation par le nombre de pétales (basé sur φ)
    petal_mod = np.abs(np.cos(theta * n_petals / 2))
    
    # Créer l'image mandala
    mandala = np.zeros((h, w), dtype=np.float64)
    mandala[mask] = np.abs(psi[mask]) * petal_mod[mask] * (1 - R[mask] / max_r)
    
    # Normaliser
    mandala = mandala / (np.max(mandala) + 1e-12)
    
    # Conversion RGB
    config = HarmonicColorMapper.PALETTES.get(style, HarmonicColorMapper.PALETTES['cosmique'])
    
    rgb = np.zeros((h, w, 3), dtype=np.float64)
    for i in range(h):
        for j in range(w):
            if mask[i, j]:
                val = mandala[i, j]
                hue = (val * PHI + theta[i, j] / (2*PI) * 0.3 + config['hue_shift']) % 1.0
                sat = 0.6 + val * config['sat_boost'] * 0.4
                lum = 0.2 + val * 0.6
                r, g, b_val = [int(c * 255) for c in __import__('colorsys').hls_to_rgb(hue, lum, sat)]
                rgb[i, j] = [r, g, b_val]
    
    return np.clip(rgb, 0, 255).astype(np.uint8)


def create_nebula(field: HarmonicField, style: str = 'cosmique',
                  stars_density: float = 0.001) -> np.ndarray:
    """
    Crée un effet de nébuleuse cosmique.
    
    Ajoute des étoiles (points brillants) basées sur π et √5.
    """
    psi = field.get_psi_total()
    h, w = psi.shape
    np.random.seed(field.seed + 999)
    
    # Base nébuleuse
    rgb = HarmonicColorMapper.harmonic_hsl(psi, palette=style)
    rgb_float = rgb.astype(np.float64) / 255.0
    
    # Ajouter des étoiles (points lumineux aléatoires corrélés au champ)
    star_mask = np.random.random((h, w)) < stars_density
    # Les étoiles plus brillantes là où le champ est fort
    star_intensity = np.abs(psi) * np.random.random((h, w))
    star_intensity[~star_mask] = 0
    
    # Ajouter la lueur des étoiles
    for _ in range(3):  # Étalement gaussien approximé
        from scipy.ndimage import gaussian_filter
        star_glow = gaussian_filter(star_intensity, sigma=1.5)
    else:
        # Fallback sans scipy
        star_glow = star_intensity
    
    # Ajouter au RGB
    for c in range(3):
        rgb_float[:, :, c] += star_glow * 0.5
    
    rgb_float = np.clip(rgb_float, 0, 1)
    return (rgb_float * 255).astype(np.uint8)


def create_geometric_pattern(field: HarmonicField, pattern: str = 'hexagonal') -> np.ndarray:
    """
    Crée un motif géométrique structuré.
    
    Patterns :
      - 'hexagonal' : grille hexagonale basée sur √3
      - 'square' : grille carrée basée sur √2
      - 'triangular' : grille triangulaire basée sur √3
      - 'voronoi' : cellules de Voronoï harmoniques
    """
    psi = field.get_psi_total()
    h, w = psi.shape
    
    Y, X = np.ogrid[:h, :w]
    X = X / w * 2 - 1
    Y = Y / h * 2 - 1
    
    if pattern == 'hexagonal':
        # Grille hexagonale basée sur √3
        spacing = 0.15 * SQRT3
        hex1 = np.cos(X * PI / spacing) + np.cos((X * 0.5 + Y * SQRT3/2) * PI / spacing) + \
               np.cos((X * 0.5 - Y * SQRT3/2) * PI / spacing)
        pattern_field = hex1 / 3
    elif pattern == 'square':
        spacing = 0.2 * SQRT2
        pattern_field = np.cos(X * PI / spacing) * np.cos(Y * PI / spacing)
    elif pattern == 'triangular':
        spacing = 0.15 * SQRT3
        pattern_field = np.cos(X * 2*PI / spacing) + \
                        np.cos((-X*0.5 + Y*SQRT3/2) * 2*PI / spacing) + \
                        np.cos((-X*0.5 - Y*SQRT3/2) * 2*PI / spacing)
        pattern_field = pattern_field / 3
    elif pattern == 'voronoi':
        # Voronoï simplifié : points aléatoires + distance
        np.random.seed(field.seed)
        n_cells = 30
        points_x = np.random.uniform(-1, 1, n_cells)
        points_y = np.random.uniform(-1, 1, n_cells)
        pattern_field = np.ones((h, w)) * 999.0
        for px, py in zip(points_x, points_y):
            dist = np.sqrt((X - px)**2 + (Y - py)**2)
            pattern_field = np.minimum(pattern_field, dist)
        pattern_field = 1.0 - pattern_field / np.max(pattern_field)
    else:
        pattern_field = psi
    
    # Combiner avec le champ harmonique
    combined = psi * 0.4 + pattern_field * 0.6
    combined = combined / (np.max(np.abs(combined)) + 1e-12)
    
    return HarmonicColorMapper.harmonic_hsl(combined, palette='solaire')


def save_as_png(rgb: np.ndarray, filepath: str):
    """Sauvegarde l'image en PNG."""
    img = Image.fromarray(rgb, 'RGB')
    img.save(filepath)
    return filepath


# ==============================================================================
# DÉMONSTRATIONS
# ==============================================================================

def demo_image_generator():
    """Démonstration du générateur d'images harmoniques."""
    print("=" * 70)
    print("  GÉNÉRATEUR D'IMAGES HARMONIQUES")
    print("  Ψ = Σ Hₙ (Ψ₁)ⁿ → Images Structurées")
    print("=" * 70)
    
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'av_generation_output')
    os.makedirs(output_dir, exist_ok=True)
    
    gen = HarmonicImageGenerator(width=512, height=512, seed=42)
    
    # 1. Générer une image avec chaque palette
    print(f"\n  [1] Génération avec 7 palettes (512×512)...")
    for style in HarmonicColorMapper.PALETTES:
        rgb = gen.generate(style=style, color_mode='hsl')
        filepath = os.path.join(output_dir, f'harmonic_{style}.png')
        save_as_png(rgb, filepath)
        metrics = gen.get_metrics()
        print(f"    ✓ {style:<12s} → {filepath}")
        print(f"      Cohérence: {metrics['coherence_harmonique']:.3f} | Symétrie: {metrics['symetrie']:.3f}")
        gen.change_seed(gen.seed + 1)
    
    # 2. Mandala
    print(f"\n  [2] Génération d'un Mandala harmonique...")
    gen.change_seed(12345)
    mandala_rgb = create_mandala(gen.field, n_petals=13, style='aurore')
    filepath = os.path.join(output_dir, 'harmonic_mandala.png')
    save_as_png(mandala_rgb, filepath)
    print(f"    ✓ Mandala (13 pétales d'or) → {filepath}")
    
    # 3. Motif géométrique
    print(f"\n  [3] Génération de motifs géométriques...")
    patterns = ['hexagonal', 'square', 'triangular']
    for pattern in patterns:
        gen.change_seed(7777 + patterns.index(pattern))
        geo_rgb = create_geometric_pattern(gen.field, pattern=pattern)
        filepath = os.path.join(output_dir, f'harmonic_geo_{pattern}.png')
        save_as_png(geo_rgb, filepath)
        print(f"    ✓ Motif {pattern:<12s} → {filepath}")
    
    # 4. Variations de seed (même style)
    print(f"\n  [4] 7 Variations cosmiques (seeds différents)...")
    gen.change_seed(1)
    for i in range(7):
        seed = SeedManager.compose_seed(42, i + 1, 0)
        gen.change_seed(seed)
        rgb = gen.generate(style='cosmique', color_mode='multilayer')
        filepath = os.path.join(output_dir, f'harmonic_cosmic_v{i+1}.png')
        save_as_png(rgb, filepath)
        print(f"    ✓ Variation {i+1} (seed={seed}) → {filepath}")
    
    # 5. Rapport détaillé
    gen.change_seed(42)
    print(f"\n{'='*70}")
    print("  RAPPORT HARMONIQUE (seed=42, style=cosmique)")
    print(f"{'='*70}")
    
    print(f"\n  Couches harmoniques :")
    for info in gen.get_layer_info():
        bar = '█' * int(info['contribution'] * 40)
        print(f"    H{info['couche']} {info['constante']:<12s} : {info['contribution']:6.2%}  {bar}")
        print(f"      → {info['role']}")
    
    metrics = gen.get_metrics()
    print(f"\n  Métriques globales :")
    for k, v in metrics.items():
        print(f"    {k:<30s} : {v:.4f}")
    
    print(f"\n  ✅ Toutes les images sauvegardées dans : {output_dir}")


def demo_single_seed():
    """Génère une seule image à partir d'un seed texte."""
    import hashlib
    
    prompts = [
        "galaxie spirale cosmique",
        "jardin de fleurs fractales",
        "océan de lumière dorée",
        "forêt de cristaux géométriques",
        "aurore boréale sur un lac",
        "cathédrale de lumière",
        "univers parallèle vibrant",
    ]
    
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'av_generation_output')
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 70)
    print("  GÉNÉRATION PAR PROMPT TEXTE")
    print("=" * 70)
    
    palettes = list(HarmonicColorMapper.PALETTES.keys())
    
    for i, prompt in enumerate(prompts):
        seed = SeedManager.text_to_seed(prompt)
        style = palettes[i % len(palettes)]
        
        gen = HarmonicImageGenerator(width=512, height=512, seed=seed)
        rgb = gen.generate(style=style)
        
        safe_name = hashlib.md5(prompt.encode()).hexdigest()[:8]
        filepath = os.path.join(output_dir, f'prompt_{safe_name}.png')
        save_as_png(rgb, filepath)
        
        print(f"  [{i+1}] \"{prompt}\"")
        print(f"       seed={seed}, style={style} → {filepath}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Générateur d\'Images Harmoniques')
    parser.add_argument('--demo', action='store_true', help='Démonstration complète')
    parser.add_argument('--prompts', action='store_true', help='Génération par prompts texte')
    parser.add_argument('--seed', type=str, default=None, help='Seed ou texte')
    parser.add_argument('--style', type=str, default='cosmique', help='Palette de couleur')
    parser.add_argument('--size', type=int, default=512, help='Taille en pixels')
    parser.add_argument('--output', type=str, default=None, help='Fichier de sortie')
    
    args = parser.parse_args()
    
    if args.prompts:
        demo_single_seed()
    elif args.seed and args.output:
        seed = SeedManager.text_to_seed(args.seed) if not args.seed.isdigit() else int(args.seed)
        gen = HarmonicImageGenerator(width=args.size, height=args.size, seed=seed)
        rgb = gen.generate(style=args.style)
        save_as_png(rgb, args.output)
        print(f"Image sauvegardée : {args.output}")
    else:
        demo_image_generator()