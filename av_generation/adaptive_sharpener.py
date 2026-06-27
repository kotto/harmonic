#!/usr/bin/env python3
# coding: utf-8
"""
ADAPTIVE HARMONIC SHARPENER — Phase 1 Roadmap (0 nouveau paramètre)
======================================================================
Basé sur l'analyse IA experte du gap concurrentiel.

Le résidu R = A - Â_K est le complément orthogonal des K premiers modes SVD.
Il se décompose en 3 composantes distinctes :

  R_edges   : réponse forte au Laplacien → bords nets   → amplifié par √5
  R_texture : résidu après soustraction des bords → textures → amplifié par e
  R_grain   : hautes fréquences isotropes → grain organique → amplifié par e/π

Pondération adaptative par région :
  - Zones texturées (haute variance locale) → boost √5
  - Zones lisses (basse variance) → anti-ringing e
  - Détection automatique via LoG + variance locale

Gain estimé : acutance 0.066 → 0.12-0.15 (×2 supplémentaire)

Usage :
  python adaptive_sharpener.py --demo
  python adaptive_sharpener.py --image photo.jpg --compare
"""

import numpy as np, math, sys, os, time, argparse
from typing import Dict, Any, Tuple, Optional
from scipy.ndimage import gaussian_filter, gaussian_laplace, laplace, sobel, median_filter
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from harmonic_generator_core import (PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI, PHI_INV,
                                      H_CONSTANTS, H_NAMES, HarmonicColorMapper, normalize_field)
from holographic_one_shot import HolographicTrainer, HolographicGenerator, BLOCK_SIZE, BLOCK_DIM
from harmonic_sharpener import HarmonicSharpener


class AdaptiveHarmonicSharpener:
    """
    Sharpener adaptatif avec décomposition LoG du résidu.
    
    Implémente la Phase 1 de la roadmap IA experte :
      - Segmentation automatique bords / textures / grain
      - Amplification différentielle par constante harmonique
      - Carte de pondération locale basée variance + spectre
    """
    
    def __init__(self, K: int = 16):
        self.K = K
        self.base_sharpener = HarmonicSharpener(K=K)
    
    def decompose_residue(self, residue: np.ndarray, 
                           sigma_edge: float = 1.0,
                           sigma_texture: float = 0.5) -> Dict[str, np.ndarray]:
        """
        Décompose le résidu en composantes bords, textures, grain.
        
        Utilise Laplacian of Gaussian (LoG) pour séparer les types de résidu.
        
        Args:
            residue: Résidu SVD (image - reconstruction)
            sigma_edge: σ pour détection de bords (LoG)
            sigma_texture: σ pour détection de textures
        
        Returns:
            dict avec 'edges', 'texture', 'grain'
        """
        # 1. Laplacian of Gaussian pour détection multi-échelle
        log_response = gaussian_laplace(residue, sigma=sigma_edge)
        log_abs = np.abs(log_response)
        
        # Seuil adaptatif basé sur la distribution du LoG
        threshold_edge = np.percentile(log_abs, 85)  # top 15% = bords
        
        # 2. Masque des bords
        edge_mask = log_abs >= threshold_edge
        R_edges = residue * edge_mask
        
        # 3. Résidu sans les bords
        R_non_edges = residue - R_edges
        
        # 4. Composante texture (moyennes fréquences)
        # Lisser le résidu non-bords → ce qui reste après lissage = texture
        R_smooth = gaussian_filter(R_non_edges, sigma=sigma_texture)
        R_texture = R_non_edges - R_smooth  # moyennes fréquences
        
        # 5. Composante grain (hautes fréquences isotropes)
        R_grain = R_non_edges - R_texture  # ou R_smooth
        
        return {
            'edges': R_edges,
            'texture': R_texture,
            'grain': R_grain,
            'edge_mask': edge_mask.astype(np.float64),
            'log_response': log_response,
        }
    
    def compute_adaptive_weights(self, image: np.ndarray, residue: np.ndarray,
                                  block_size: int = 16) -> np.ndarray:
        """
        Calcule une carte de poids adaptative par région.
        
        Pour chaque bloc local :
          - Variance élevée (texture) → poids fort (√5)
          - Variance faible (zone lisse) → anti-ringing (e)
          - HF ratio élevé → boost supplémentaire
        
        Returns:
            weight_map (H, W) avec poids d'amplification par pixel
        """
        H, W = image.shape
        weight_map = np.ones((H, W), dtype=np.float64)
        
        # Paramètres adaptatifs
        TEXTURE_VAR_THRESHOLD = 0.001  # Seuil de variance pour "texturé"
        
        for y in range(0, H, block_size):
            for x in range(0, W, block_size):
                y_end = min(y + block_size, H)
                x_end = min(x + block_size, W)
                
                block = image[y:y_end, x:x_end]
                res_block = residue[y:y_end, x:x_end]
                
                # Variance locale
                local_var = float(np.var(block))
                
                # Spectre du résidu local (via FFT)
                if res_block.size >= 16:
                    res_fft = np.abs(np.fft.fft2(res_block))
                    ny, nx = res_fft.shape
                    hf_energy = np.sum(res_fft[ny//4:, :] ** 2) + np.sum(res_fft[:, nx//4:] ** 2)
                    lf_energy = np.sum(res_fft[:ny//4, :nx//4] ** 2)
                    hf_ratio = hf_energy / (lf_energy + 1e-8)
                else:
                    hf_ratio = 0.5
                
                # Poids harmonique adaptatif
                if local_var > TEXTURE_VAR_THRESHOLD:
                    # Zone texturée → √5 pour micro-détails
                    alpha = SQRT5 * np.tanh(hf_ratio * 3) * 0.8
                else:
                    # Zone lisse → e pour anti-ringing (éviter artefacts)
                    alpha = E * np.exp(-hf_ratio * 2) * 0.3
                
                weight_map[y:y_end, x:x_end] = 1.0 + alpha
        
        return weight_map
    
    def sharpen_adaptive(self, image: np.ndarray, strength: float = 1.0,
                          anti_ringing: bool = True) -> np.ndarray:
        """
        Sharpening adaptatif complet : décomposition LoG + poids régionaux.
        
        Pipeline :
          1. SVD reconstruction + résidu
          2. Décomposition LoG → bords, textures, grain
          3. Carte de poids adaptative par région
          4. Amplification différentielle avec 7Hₙ
          5. Reconstruction
        """
        # 1. SVD
        sig = HolographicTrainer.train_image(image, K=self.K)
        h, w = image.shape
        base = HolographicGenerator.reconstruct(sig, width=w, height=h)
        if base.shape != image.shape:
            from PIL import Image as PILImage
            base = np.array(PILImage.fromarray(
                (base * 255).astype(np.uint8)
            ).resize((w, h), PILImage.LANCZOS), dtype=np.float64) / 255.0
        
        residue = image - base
        
        # 2. Décomposition LoG du résidu
        decomp = self.decompose_residue(residue, 
                                         sigma_edge=1.0, 
                                         sigma_texture=0.5)
        
        # 3. Carte de poids adaptative
        weight_map = self.compute_adaptive_weights(image, residue, block_size=16)
        
        # 4. Amplification différentielle par composante
        R_amplified = np.zeros_like(residue)
        
        # H₆ (√5 ≈ 2.236) : BOOST des bords nets
        R_amplified += decomp['edges'] * (1.0 + SQRT5 * 0.9 * strength)
        
        # H₃ (e ≈ 2.718) : Amplification textures (moyennes fréquences)
        R_amplified += decomp['texture'] * (1.0 + E * 0.4 * strength)
        
        # H₇ (e/π ≈ 0.865) : Grain organique (anti-banding)
        R_amplified += decomp['grain'] * (1.0 + (1.0 - E_PI) * 0.3 * strength)
        
        # 5. Appliquer la carte de poids régionale
        R_amplified *= weight_map
        
        # 6. Anti-ringing adaptatif (H₃)
        if anti_ringing:
            gy, gx = np.gradient(base)
            edge_strength = np.sqrt(gx**2 + gy**2)
            edge_strength = edge_strength / (np.max(edge_strength) + 1e-12)
            # Damping exponentiel près des bords forts
            damping = 1.0 - edge_strength * (E - 1) * 0.25 * strength
            damping = np.clip(damping, 0.4, 1.0)
            R_amplified *= damping
        
        # 7. Reconstruction finale
        sharp = base + R_amplified
        
        # Clipping sigmoïde (transition naturelle)
        sharp = np.clip(sharp, -0.05, 1.05)
        sharp = 1.0 / (1.0 + np.exp(-(sharp - 0.5) * 12))
        
        return sharp
    
    def compare_all(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Compare : original, SVD reconstruction, sharpener simple, sharpener adaptatif.
        """
        sig = HolographicTrainer.train_image(image, K=self.K)
        h, w = image.shape
        base = HolographicGenerator.reconstruct(sig, width=w, height=h)
        
        # Sharpener simple (ancien)
        simple_sharp = self.base_sharpener.sharpen(image, strength=1.0)
        
        # Sharpener adaptatif (nouveau)
        adaptive_sharp = self.sharpen_adaptive(image, strength=1.0)
        
        # Métriques
        metrics = {}
        for name, arr in [('original', image), ('svd_base', base),
                           ('simple_sharp', simple_sharp), ('adaptive_sharp', adaptive_sharp)]:
            metrics[name] = self.base_sharpener.analyze_sharpness(arr)
        
        return {
            'svd_base': base,
            'simple_sharp': simple_sharp,
            'adaptive_sharp': adaptive_sharp,
            'metrics': metrics,
            'signature': sig,
        }


# ==============================================================================
# DEMO
# ==============================================================================

def demo_adaptive():
    print("═" * 70)
    print("  ADAPTIVE HARMONIC SHARPENER — Phase 1 Roadmap IA Experte")
    print("  LoG Decomposition + Adaptive Weights + 7Hn Differential")
    print("═" * 70)
    
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'adaptive_sharpener')
    os.makedirs(out_dir, exist_ok=True)
    
    # Image test riche en textures (générée procéduralement avec détails fins)
    from harmonic_generator_core import HarmonicField, HarmonicColorMapper
    from harmonic_image_generator import save_as_png
    
    print("\n  [1] Création image de test avec textures variées...")
    field = HarmonicField(width=512, height=512, seed=12345)
    psi = field.get_psi_total()
    
    H, W = psi.shape
    x = np.linspace(-1, 1, W)
    y = np.linspace(-1, 1, H)
    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X**2 + Y**2)
    theta = np.arctan2(Y, X)
    
    # Ajouter des textures haute fréquence variées
    psi += 0.25 * np.sin(X * 50 * SQRT5) * np.cos(Y * 50 * SQRT5)
    psi += 0.15 * np.sin(R * 40 + theta * 12)
    psi += 0.10 * np.cos(X * 30) * np.cos(Y * 20)
    psi = normalize_field(psi)
    
    image = (psi + 1) / 2
    rgb = HarmonicColorMapper.harmonic_hsl(psi, palette='cosmique')
    save_as_png(rgb, os.path.join(out_dir, '01_original.png'))
    
    # Test comparatif
    print("\n  [2] Comparaison : Simple vs Adaptatif...")
    sharpener = AdaptiveHarmonicSharpener(K=16)
    result = sharpener.compare_all(image)
    
    m = result['metrics']
    print(f"""
  📊 Métriques Comparatives

  | Version          | Acutance | Laplacian Std | HF Ratio | Gradient Energy |
  |------------------|----------|---------------|----------|-----------------|
  | Original         | {m['original']['acutance']:8.4f} | {m['original']['laplacian_std']:13.4f} | {m['original']['hf_ratio']:8.4f} | {m['original']['gradient_energy']:15.6f} |
  | SVD Base         | {m['svd_base']['acutance']:8.4f} | {m['svd_base']['laplacian_std']:13.4f} | {m['svd_base']['hf_ratio']:8.4f} | {m['svd_base']['gradient_energy']:15.6f} |
  | Simple Sharpener | {m['simple_sharp']['acutance']:8.4f} | {m['simple_sharp']['laplacian_std']:13.4f} | {m['simple_sharp']['hf_ratio']:8.4f} | {m['simple_sharp']['gradient_energy']:15.6f} |
  | Adaptive Sharp   | {m['adaptive_sharp']['acutance']:8.4f} | {m['adaptive_sharp']['laplacian_std']:13.4f} | {m['adaptive_sharp']['hf_ratio']:8.4f} | {m['adaptive_sharp']['gradient_energy']:15.6f} |
""")
    
    # Calculer les gains
    gain_simple = (m['simple_sharp']['laplacian_std'] / max(1e-12, m['original']['laplacian_std']) - 1) * 100
    gain_adaptive = (m['adaptive_sharp']['laplacian_std'] / max(1e-12, m['original']['laplacian_std']) - 1) * 100
    gain_vs_simple = (m['adaptive_sharp']['laplacian_std'] / max(1e-12, m['simple_sharp']['laplacian_std']) - 1) * 100
    
    print(f"  Gain Simple vs Original   : {gain_simple:+.0f}%")
    print(f"  Gain Adaptive vs Original : {gain_adaptive:+.0f}%")
    print(f"  Gain Adaptive vs Simple   : {gain_vs_simple:+.0f}%")
    
    # Sauvegarder
    print("\n  [3] Sauvegarde des résultats...")
    for name, arr in [('svd_base', result['svd_base']),
                       ('simple_sharp', result['simple_sharp']),
                       ('adaptive_sharp', result['adaptive_sharp'])]:
        u8 = (np.clip(arr, 0, 1) * 255).astype(np.uint8)
        Image.fromarray(np.stack([u8]*3, axis=-1), 'RGB').save(
            os.path.join(out_dir, f'02_{name}.png'))
    
    # Visualiser la décomposition du résidu
    sig = HolographicTrainer.train_image(image, K=16)
    base = HolographicGenerator.reconstruct(sig, width=512, height=512)
    residue = image - base
    decomp = sharpener.decompose_residue(residue)
    
    for name in ['edges', 'texture', 'grain']:
        viz = np.abs(decomp[name]) * 15
        viz = np.clip(viz, 0, 1)
        u8 = (viz * 255).astype(np.uint8)
        Image.fromarray(np.stack([u8]*3, axis=-1), 'RGB').save(
            os.path.join(out_dir, f'03_residue_{name}.png'))
    
    print(f"\n  ✅ Fichiers dans : {out_dir}/")
    for f in sorted(os.listdir(out_dir)):
        print(f"    {f}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Adaptive Harmonic Sharpener')
    parser.add_argument('--demo', action='store_true', help='Démo')
    parser.add_argument('--image', type=str, default=None, help='Image à sharpener')
    parser.add_argument('--compare', action='store_true', help='Comparaison complète')
    args = parser.parse_args()
    
    if args.image:
        img = np.array(Image.open(args.image).convert('L'), dtype=np.float64) / 255.0
        sharpener = AdaptiveHarmonicSharpener(K=16)
        
        if args.compare:
            result = sharpener.compare_all(img)
            out_dir = os.path.join(os.path.dirname(args.image) or '.', 'adaptive_output')
            os.makedirs(out_dir, exist_ok=True)
            for name, arr in [('original', img), ('simple_sharp', result['simple_sharp']),
                               ('adaptive_sharp', result['adaptive_sharp'])]:
                u8 = (np.clip(arr,0,1)*255).astype(np.uint8)
                Image.fromarray(np.stack([u8]*3,-1),'RGB').save(
                    os.path.join(out_dir, f'{name}.png'))
            
            m = result['metrics']
            for k in ['original','simple_sharp','adaptive_sharp']:
                print(f"{k}: acutance={m[k]['acutance']:.4f} lap_std={m[k]['laplacian_std']:.4f}")
        else:
            sharp = sharpener.sharpen_adaptive(img)
            out = args.image.replace('.', '_adaptive.')
            u8 = (np.clip(sharp,0,1)*255).astype(np.uint8)
            Image.fromarray(np.stack([u8]*3,-1),'RGB').save(out)
            print(f"Image sauvegardée : {out}")
    else:
        demo_adaptive()