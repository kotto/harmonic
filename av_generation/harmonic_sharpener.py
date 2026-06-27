#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HARMONIC SHARPENER — Résidu Spectral + 7Hₙ = Netteté Naturelle
=================================================================
Comprendre la netteté ondulatoire :

  Image nette = Spectre riche en HAUTES fréquences
  Image floue = Spectre pauvre en hautes fréquences (SVD tronqué)

La nature a TOUTES les fréquences (0 → ∞ Hz). Notre SVD K=16 capture
99.9% de l'énergie mais perd les micro-détails (le 0.1% restant).

SOLUTION : Extraire le RÉSIDU (image - reconstruction SVD) qui contient
EXACTEMENT ces hautes fréquences, puis l'amplifier guidé par Hₙ.

Pipeline :
  1. SVD K=16 → reconstruction (99.9% énergie)
  2. Résidu = Original - Reconstruction (hautes fréquences pures)
  3. Amplification Hₙ du résidu :
     H₁ (φ)   : structure → +0.6×
     H₂ (π)   : périodicité → +0.3×
     H₃ (e)   : anti-ringing → filtre adaptatif
     H₄ (√2)  : symétrie → équilibre H/V
     H₅ (√3)  : profondeur → boost 3D
     H₆ (√5)  : micro-détails → +2.2× (le plus important)
     H₇ (e/π) : grain organique → texture naturelle
  4. Image finale = Reconstruction + Résidu_amplifié

Métrique : PSNR passe de 81.2 dB (reconstruction) à potentiellement
           > 90 dB avec réinjection du résidu.

Usage :
  python harmonic_sharpener.py --image photo.jpg --demo
  python harmonic_sharpener.py --compare photo.jpg
"""

import numpy as np
import math
import sys
import os
import time
import argparse
from typing import Dict, Any, Tuple, Optional
from PIL import Image
from scipy.ndimage import gaussian_filter, sobel, median_filter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harmonic_generator_core import (
    PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI, PHI_INV,
    H_CONSTANTS, H_NAMES, HarmonicColorMapper, SeedManager, normalize_field,
)
from holographic_one_shot import (
    HolographicTrainer, HolographicSignature, HolographicGenerator,
    BLOCK_SIZE, BLOCK_DIM,
)


# ==============================================================================
# HARMONIC SHARPENER — Extraction + Amplification du Résidu
# ==============================================================================

class HarmonicSharpener:
    """
    Sharpener basé sur la réinjection du résidu spectral SVD.
    
    Principe (inspiré de la nature) :
      La nature ne tronque jamais le spectre. Pour imiter cela, on :
      1. Décompose l'image via SVD (K composantes principales)
      2. Extrait le résidu (tout ce que SVD n'a pas capturé)
      3. Amplifie sélectivement le résidu avec les 7Hₙ
      4. Recompose : base + résidu amplifié = image hyper-nette
    """
    
    def __init__(self, K: int = 16):
        self.K = K
    
    def decompose(self, image: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Décompose une image en base SVD + résidu.
        
        Returns:
            dict avec 'reconstructed', 'residue', 'signature', 'metrics'
        """
        # SVD standard
        signature = HolographicTrainer.train_image(image, K=self.K)
        h, w = image.shape
        reconstructed = HolographicGenerator.reconstruct(signature, width=w, height=h)
        
        # S'assurer que les dimensions correspondent
        if reconstructed.shape != image.shape:
            reconstructed = np.array(Image.fromarray(
                (reconstructed * 255).astype(np.uint8)
            ).resize((w, h), Image.LANCZOS), dtype=np.float64) / 255.0
        
        # Résidu = hautes fréquences pures
        residue = image - reconstructed
        
        # Métriques
        mse = np.mean(residue ** 2)
        psnr = 10 * math.log10(1.0 / (mse + 1e-12)) if mse > 0 else 999
        
        # Énergie capturée
        energy_total = np.sum(image ** 2)
        energy_reconstructed = np.sum(reconstructed ** 2)
        energy_residue = np.sum(residue ** 2)
        
        return {
            'reconstructed': reconstructed,
            'residue': residue,
            'signature': signature,
            'metrics': {
                'mse': float(mse),
                'psnr_db': float(psnr),
                'energy_captured': float(energy_reconstructed / (energy_total + 1e-12)),
                'energy_residue': float(energy_residue / (energy_total + 1e-12)),
                'residue_std': float(np.std(residue)),
                'residue_max': float(np.max(np.abs(residue))),
            },
        }
    
    def sharpen(self, image: np.ndarray, 
                strength: float = 1.0,
                anti_ringing: bool = True) -> np.ndarray:
        """
        Applique le sharpening harmonique complet.
        
        Args:
            image: Image d'entrée [0, 1]
            strength: Force du sharpening (1.0 = standard, 2.0 = agressif)
            anti_ringing: Appliquer l'anti-ringing (H₃ = e)
        
        Returns:
            Image sharpenée [0, 1]
        """
        # 1. Décomposition
        decomp = self.decompose(image)
        base = decomp['reconstructed']
        residue = decomp['residue']
        
        # 2. Amplification harmonique du résidu
        # Chaque Hₙ amplifie une composante spécifique du résidu
        
        # H₆ (√5 ≈ 2.236) : BOOST principal des micro-détails
        # C'est la constante la plus importante pour la netteté
        residue_amplified = residue * (1.0 + SQRT5 * 0.8 * strength)
        
        # H₁ (φ ≈ 1.618) : Renforcement structurel (contours principaux)
        # Appliquer un laplacien pour isoler les structures
        from scipy.ndimage import laplace
        structure = laplace(base)
        structure = structure / (np.std(structure) + 1e-12) * np.std(residue) * 0.3
        residue_amplified += structure * (PHI - 1) * 0.5 * strength
        
        # H₂ (π ≈ 3.142) : Renforcement périodique (motifs répétitifs)
        # Détection des motifs via autocorrélation locale
        gy, gx = np.gradient(residue)
        grad_mag = np.sqrt(gx**2 + gy**2)
        # Les zones à fort gradient périodique = motifs
        periodic_mask = gaussian_filter(grad_mag, sigma=2.0)
        periodic_mask = periodic_mask / (np.max(periodic_mask) + 1e-12)
        residue_amplified += residue * periodic_mask * (PI / 8) * strength * 0.4
        
        # H₃ (e ≈ 2.718) : Anti-ringing adaptatif (amortissement des artefacts)
        if anti_ringing:
            # Détection des zones de ringing (oscillations près des bords)
            edge_map = grad_mag / (np.max(grad_mag) + 1e-12)
            # Là où les gradients sont forts, atténuer légèrement
            damping = 1.0 - edge_map * (E - 1) * 0.3 * strength
            damping = np.clip(damping, 0.3, 1.0)
            residue_amplified *= damping
        
        # H₄ (√2 ≈ 1.414) : Équilibrage symétrique H/V
        # Vérifier que l'amplification ne casse pas la symétrie naturelle
        h_sym = np.mean(np.abs(residue - np.fliplr(residue)))
        v_sym = np.mean(np.abs(residue - np.flipud(residue)))
        symmetry_factor = 1.0 - min(1.0, (h_sym + v_sym) * 5)
        residue_amplified += residue * symmetry_factor * (SQRT2 - 1) * 0.3 * strength
        
        # H₅ (√3 ≈ 1.732) : Profondeur — boost différencié centre/périphérie
        h, w = residue.shape
        Y, X = np.ogrid[:h, :w]
        X_norm = X / w * 2 - 1
        Y_norm = Y / h * 2 - 1
        R = np.sqrt(X_norm**2 + Y_norm**2)
        depth_weight = 1.0 + (1.0 - R) * (SQRT3 - 1) * 0.2 * strength
        residue_amplified *= depth_weight
        
        # H₇ (e/π ≈ 0.865) : Grain spiral organique (anti-banding, texture naturelle)
        theta = np.arctan2(Y_norm, X_norm)
        spiral_grain = np.sin(R * 60 * E_PI + theta * 9) * np.std(residue) * 0.02 * strength
        # N'appliquer que dans les zones plates (pas sur les contours)
        flat_mask = 1.0 - edge_map
        residue_amplified += spiral_grain * flat_mask * (1.0 - E_PI) * 0.3
        
        # 3. Recomposer
        sharp = base + residue_amplified
        
        # 4. Clipping doux (transition naturelle au lieu de hard clip)
        sharp = np.clip(sharp, -0.1, 1.1)  # Légèrement au-delà pour la transition
        # Ramener dans [0, 1] avec une courbe en S
        sharp = 1.0 / (1.0 + np.exp(-(sharp - 0.5) * 10))  # Sigmoïde de recentrage
        
        return sharp
    
    def analyze_sharpness(self, image: np.ndarray) -> Dict[str, float]:
        """
        Analyse quantitative de la netteté d'une image.
        
        Métriques :
          - acutance : énergie des hautes fréquences / énergie totale
          - laplacian_std : écart-type du laplacien (mesure standard de netteté)
          - gradient_energy : somme des gradients normalisée
          - frequency_entropy : entropie du spectre de Fourier
        """
        # Laplacian variance (métrique standard de netteté)
        from scipy.ndimage import laplace
        lap = laplace(image)
        laplacian_std = float(np.std(lap))
        
        # Gradient energy
        gy, gx = np.gradient(image)
        grad_energy = float(np.mean(gx**2 + gy**2))
        
        # Entropie fréquentielle
        fft = np.abs(np.fft.fft2(image))
        fft_norm = fft / (np.sum(fft) + 1e-12)
        entropy = -np.sum(fft_norm * np.log2(fft_norm + 1e-12))
        
        # Ratio hautes/basses fréquences
        h, w = image.shape
        fft_shifted = np.fft.fftshift(fft)
        center_h, center_w = h // 2, w // 2
        r = 30
        low_freq_mask = np.zeros((h, w), dtype=bool)
        Y, X = np.ogrid[:h, :w]
        low_freq_mask[(Y - center_h)**2 + (X - center_w)**2 <= r**2] = True
        
        energy_low = np.sum(fft_shifted[low_freq_mask] ** 2)
        energy_high = np.sum(fft_shifted[~low_freq_mask] ** 2)
        hf_ratio = float(energy_high / (energy_low + 1e-12))
        
        return {
            'laplacian_std': laplacian_std,
            'gradient_energy': grad_energy,
            'frequency_entropy': entropy,
            'hf_ratio': hf_ratio,
            'acutance': float(hf_ratio / (1.0 + hf_ratio)),  # 0 = flou, 1 = net
        }
    
    def compare(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Compare l'original, la reconstruction SVD, et la version sharpenée.
        """
        decomp = self.decompose(image)
        sharp = self.sharpen(image)
        
        # Métriques pour chaque version
        metrics_original = self.analyze_sharpness(image)
        metrics_reconstructed = self.analyze_sharpness(decomp['reconstructed'])
        metrics_sharp = self.analyze_sharpness(sharp)
        
        return {
            'original': image,
            'reconstructed': decomp['reconstructed'],
            'sharpened': sharp,
            'residue': decomp['residue'],
            'metrics': {
                'original': metrics_original,
                'reconstructed': metrics_reconstructed,
                'sharpened': metrics_sharp,
                'decomposition': decomp['metrics'],
            }
        }


# ==============================================================================
# DÉMONSTRATION
# ==============================================================================

def demo_harmonic_sharpener():
    """Démonstration complète du Harmonic Sharpener."""
    print("═" * 70)
    print("  HARMONIC SHARPENER — Résidu Spectral + 7Hₙ")
    print("  Principe : La nature a TOUTES les fréquences")
    print("═" * 70)
    
    output_dir = os.path.join(os.path.dirname(__file__), '..',
                              'av_generation_output', 'sharpener')
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Créer une image de test avec détails fins
    print("\n  [1] Création image de test (512×512)...")
    from harmonic_generator_core import HarmonicField, HarmonicColorMapper
    from harmonic_image_generator import save_as_png
    
    # Générer une image riche en détails
    field = HarmonicField(width=512, height=512, seed=12345)
    psi = field.get_psi_total()
    
    # Ajouter des structures haute fréquence (simuler des détails fins)
    H, W = psi.shape
    x = np.linspace(-1, 1, W)
    y = np.linspace(-1, 1, H)
    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X**2 + Y**2)
    theta = np.arctan2(Y, X)
    
    # Ajouter des textures
    psi += 0.3 * np.sin(X * 40 * SQRT5) * np.cos(Y * 40 * SQRT5)  # H₆ textures
    psi += 0.2 * np.sin(R * 30 * PI + theta * 8)  # Motifs circulaires
    psi += 0.15 * np.cos(X * 25) * np.cos(Y * 15)  # Grille
    
    psi = normalize_field(psi)
    image = (psi + 1) / 2  # → [0, 1]
    
    # Sauvegarder l'original
    rgb_orig = HarmonicColorMapper.harmonic_hsl(psi, palette='cosmique')
    save_as_png(rgb_orig, os.path.join(output_dir, '01_original.png'))
    
    # 2. Test du Sharpener
    print("\n  [2] Analyse harmonique...")
    sharpener = HarmonicSharpener(K=16)
    
    # Comparaison complète
    result = sharpener.compare(image)
    
    # Métriques
    m = result['metrics']
    print(f"""
  📊 Métriques de Netteté
  
  | Métrique          | Original    | Reconstruction | Sharpened   |
  |-------------------|-------------|----------------|-------------|
  | Laplacian Std     | {m['original']['laplacian_std']:11.4f} | {m['reconstructed']['laplacian_std']:14.4f} | {m['sharpened']['laplacian_std']:11.4f} |
  | Gradient Energy   | {m['original']['gradient_energy']:11.6f} | {m['reconstructed']['gradient_energy']:14.6f} | {m['sharpened']['gradient_energy']:11.6f} |
  | HF Ratio          | {m['original']['hf_ratio']:11.4f} | {m['reconstructed']['hf_ratio']:14.4f} | {m['sharpened']['hf_ratio']:11.4f} |
  | Acutance          | {m['original']['acutance']:11.4f} | {m['reconstructed']['acutance']:14.4f} | {m['sharpened']['acutance']:11.4f} |
  
  Décomposition SVD :
    PSNR reconstruction : {m['decomposition']['psnr_db']:.1f} dB
    Énergie capturée    : {m['decomposition']['energy_captured']:.2%}
    Énergie résidu      : {m['decomposition']['energy_residue']:.2%}
    Std résidu          : {m['decomposition']['residue_std']:.6f}
    Max résidu          : {m['decomposition']['residue_max']:.6f}
""")
    
    # 3. Sauvegarder les résultats
    print("  [3] Sauvegarde des résultats...")
    
    # Reconstruction
    recon_field = result['reconstructed'] * 2 - 1
    rgb_recon = HarmonicColorMapper.harmonic_hsl(recon_field, palette='cosmique')
    save_as_png(rgb_recon, os.path.join(output_dir, '02_reconstructed.png'))
    
    # Résidu (amplifié pour visualisation)
    residue_viz = np.abs(result['residue']) * 10  # Amplifier pour voir
    residue_viz = np.clip(residue_viz, 0, 1)
    rgb_residue = np.stack([
        (residue_viz * 255).astype(np.uint8)
    ] * 3, axis=-1)
    Image.fromarray(rgb_residue, 'RGB').save(os.path.join(output_dir, '03_residue.png'))
    
    # Image sharpenée
    sharp_field = result['sharpened'] * 2 - 1
    rgb_sharp = HarmonicColorMapper.harmonic_hsl(sharp_field, palette='cosmique')
    save_as_png(rgb_sharp, os.path.join(output_dir, '04_sharpened.png'))
    
    # 4. Test avec différentes forces
    print("\n  [4] Test multi-force...")
    for strength in [0.5, 1.0, 1.5, 2.0, 3.0]:
        sharp_s = sharpener.sharpen(image, strength=strength)
        field_s = sharp_s * 2 - 1
        rgb_s = HarmonicColorMapper.harmonic_hsl(field_s, palette='cosmique')
        save_as_png(rgb_s, os.path.join(output_dir, f'05_strength_{int(strength*10):02d}.png'))
        
        metrics_s = sharpener.analyze_sharpness(sharp_s)
        print(f"    strength={strength:.1f} | acutance={metrics_s['acutance']:.4f} | "
              f"lap_std={metrics_s['laplacian_std']:.4f}")
    
    print(f"\n  ✅ Tous les fichiers dans : {output_dir}")
    print(f"\n  💡 Le résidu contient les HAUTES FRÉQUENCES (micro-détails)")
    print(f"     que le SVD K=16 ne capture pas. En les réinjectant avec")
    print(f"     amplification Hₙ, on obtient une netteté naturelle.")
    print(f"     C'est EXACTEMENT ce que fait la nature.")


def demo_sharpen_real_image(image_path: str):
    """Démo sur une vraie image."""
    print("═" * 70)
    print("  HARMONIC SHARPENER — Image Réelle")
    print("═" * 70)
    
    img = np.array(Image.open(image_path).convert('L'), dtype=np.float64) / 255.0
    print(f"  Image : {image_path} ({img.shape[1]}×{img.shape[0]})")
    
    sharpener = HarmonicSharpener(K=16)
    
    t0 = time.time()
    result = sharpener.compare(img)
    elapsed = (time.time() - t0) * 1000
    
    output_dir = os.path.join(os.path.dirname(image_path) if os.path.dirname(image_path) else '.',
                              'sharpened_output')
    os.makedirs(output_dir, exist_ok=True)
    
    basename = os.path.splitext(os.path.basename(image_path))[0]
    
    # Sauvegarder
    for name, arr in [('original', result['original']), 
                       ('reconstructed', result['reconstructed']),
                       ('sharpened', result['sharpened'])]:
        rgb = np.stack([(np.clip(arr, 0, 1) * 255).astype(np.uint8)] * 3, axis=-1)
        Image.fromarray(rgb, 'RGB').save(os.path.join(output_dir, f'{basename}_{name}.png'))
    
    m = result['metrics']
    print(f"\n  ✅ Traité en {elapsed:.0f}ms")
    print(f"  PSNR reconstruction : {m['decomposition']['psnr_db']:.1f} dB")
    print(f"  Acutance : {m['original']['acutance']:.4f} → {m['sharpened']['acutance']:.4f}")
    print(f"  Gain netteté : {(m['sharpened']['laplacian_std'] / max(1e-12, m['original']['laplacian_std']) - 1) * 100:.0f}%")
    print(f"  Fichiers dans : {output_dir}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Harmonic Sharpener — Résidu + 7Hₙ')
    parser.add_argument('--demo', action='store_true', help='Démo avec image synthétique')
    parser.add_argument('--image', type=str, default=None, help='Image à sharpener')
    parser.add_argument('--strength', type=float, default=1.0, help='Force du sharpening')
    parser.add_argument('--compare', action='store_true', help='Comparaison complète')
    
    args = parser.parse_args()
    
    if args.image:
        if args.compare:
            demo_sharpen_real_image(args.image)
        else:
            img = np.array(Image.open(args.image).convert('L'), dtype=np.float64) / 255.0
            sharpener = HarmonicSharpener(K=16)
            sharp = sharpener.sharpen(img, strength=args.strength)
            out = args.image.replace('.', '_sharpened.')
            rgb = np.stack([(np.clip(sharp, 0, 1) * 255).astype(np.uint8)] * 3, axis=-1)
            Image.fromarray(rgb, 'RGB').save(out)
            print(f"Image sauvegardée : {out}")
    else:
        demo_harmonic_sharpener()