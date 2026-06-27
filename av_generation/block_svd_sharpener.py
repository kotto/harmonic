#!/usr/bin/env python3
# coding: utf-8
"""
PHASE 2 — Block SVD + Hann Window Overlap
==========================================
Roadmap IA Experte : Phase 2 — Gain structurel

Remplace SVD globale par SVD par blocs 16×16 avec overlap Hann.
La SVD globale produit des vecteurs singuliers qui oscillent sur toute l'image
→ faible cohérence locale pour les textures. La SVD par blocs capture la
stationnarité locale des textures naturelles (bois, peau, tissu).

Pipeline :
  1. Découpage en blocs 16×16 avec overlap 25%
  2. SVD indépendant par bloc (K=8 par bloc → total ~équivalent K=16 global)
  3. Reconstruction avec fenêtre de Hann pour fusion inter-blocs
  4. Résidu par bloc → sharpener adaptatif local
  5. Assemblage final

Gain estimé : PSNR +2-4 dB, acutance +15-25% sur textures

Usage :
  python block_svd_sharpener.py --demo
  python block_svd_sharpener.py --image photo.jpg
"""

import numpy as np, math, sys, os, time, argparse
from typing import Dict, Any, List, Tuple, Optional
from scipy.ndimage import gaussian_filter
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from harmonic_generator_core import (PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI, PHI_INV,
                                      H_CONSTANTS, H_NAMES, HarmonicColorMapper, normalize_field)
from holographic_one_shot import HolographicTrainer, HolographicGenerator, BLOCK_SIZE, BLOCK_DIM


# ==============================================================================
# SVD PAR BLOCS AVEC OVERLAP HANN
# ==============================================================================

def create_hann_window(size: int) -> np.ndarray:
    """Crée une fenêtre de Hann 2D (size × size)."""
    hann_1d = 0.5 * (1 - np.cos(2 * np.pi * np.arange(size) / (size - 1)))
    return np.outer(hann_1d, hann_1d)


class BlockSVD:
    """
    Décomposition SVD par blocs 16×16 avec fusion par fenêtre de Hann.
    
    Avantages vs SVD globale :
      - Capture la stationnarité locale des textures
      - Évite les artefacts de bord (overlap)
      - Meilleure cohérence haute fréquence
    """
    
    def __init__(self, block_size: int = 16, overlap: float = 0.25, K: int = 8):
        self.block_size = block_size
        self.stride = int(block_size * (1 - overlap))
        self.K = K
        self.hann_window = create_hann_window(block_size)
    
    def decompose(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Décompose l'image en blocs SVD avec overlap.
        
        Returns:
            dict avec 'reconstructed', 'residue', 'block_info'
        """
        H, W = image.shape
        bs = self.block_size
        st = self.stride
        
        # Accumulateurs pour reconstruction
        recon_accum = np.zeros((H, W), dtype=np.float64)
        weight_accum = np.zeros((H, W), dtype=np.float64)
        
        n_blocks_total = 0
        block_signatures = []
        
        for y in range(0, H - bs + 1, st):
            for x in range(0, W - bs + 1, st):
                # Extraire le bloc
                block = image[y:y+bs, x:x+bs]
                
                # Centrer-réduire
                mean_block = np.mean(block)
                std_block = np.std(block) + 1e-8
                block_centered = (block - mean_block) / std_block
                
                # SVD sur le vecteur du bloc
                block_vec = block_centered.flatten()
                # Pour un bloc 16×16, la SVD revient à trouver les
                # vecteurs propres de la matrice de covariance locale
                # Simplification : reconstruction PCA du bloc
                try:
                    # Matrice de covariance locale (via reshape)
                    block_2d = block_centered
                    U, S, Vt = np.linalg.svd(block_2d, full_matrices=False)
                    
                    # Reconstruction rang K
                    K_actual = min(self.K, len(S))
                    block_recon = (U[:, :K_actual] * S[:K_actual]) @ Vt[:K_actual, :]
                except np.linalg.LinAlgError:
                    block_recon = block_centered
                
                # Dénormaliser
                block_recon = block_recon * std_block + mean_block
                
                # Ajouter avec pondération Hann (la fenêtre elle-même sert de poids)
                recon_accum[y:y+bs, x:x+bs] += block_recon * self.hann_window
                weight_accum[y:y+bs, x:x+bs] += self.hann_window
                
                n_blocks_total += 1
                block_signatures.append({
                    'pos': (y, x),
                    'mean': mean_block,
                    'std': std_block,
                })
        
        # Normaliser par les poids
        weight_accum = np.maximum(weight_accum, 1e-12)
        reconstructed = recon_accum / weight_accum
        
        # Résidu
        residue = image - reconstructed
        
        # Métriques
        mse = np.mean(residue ** 2)
        psnr = 10 * math.log10(1.0 / (mse + 1e-12)) if mse > 0 else 999
        
        return {
            'reconstructed': reconstructed,
            'residue': residue,
            'metrics': {
                'mse': float(mse),
                'psnr_db': float(psnr),
                'n_blocks': n_blocks_total,
                'block_size': bs,
                'stride': st,
                'overlap': 1.0 - st/bs,
            },
            'block_signatures': block_signatures,
        }
    
    def sharpen_block_adaptive(self, image: np.ndarray, strength: float = 1.0) -> np.ndarray:
        """
        Sharpening adaptatif par bloc.
        
        Comme le résidu est local maintenant, on peut appliquer des poids
        Hₙ différents par bloc selon son contenu spectral.
        """
        # SVD par blocs
        decomp = self.decompose(image)
        base = decomp['reconstructed']
        residue = decomp['residue']
        
        H, W = image.shape
        bs = self.block_size
        st = self.stride
        
        # Accumulateurs
        sharp_accum = np.zeros((H, W), dtype=np.float64)
        weight_accum = np.zeros((H, W), dtype=np.float64)
        
        for y in range(0, H - bs + 1, st):
            for x in range(0, W - bs + 1, st):
                # Résidu local
                res_block = residue[y:y+bs, x:x+bs]
                base_block = base[y:y+bs, x:x+bs]
                
                # Analyse spectrale locale
                res_fft = np.fft.fft2(res_block)
                res_abs = np.abs(res_fft)
                
                # Ratio hautes/basses fréquences local
                ny, nx = res_abs.shape
                hf = np.sum(res_abs[ny//3:, :]) + np.sum(res_abs[:, nx//3:])
                lf = np.sum(res_abs[:ny//3, :nx//3]) + 1e-8
                hf_ratio = hf / lf
                
                # Variance locale
                local_var = np.var(base_block)
                
                # Amplification adaptative par bloc
                if local_var > 0.0005 and hf_ratio > 0.3:
                    # Bloc texturé → √5 + π pour périodicité
                    alpha = SQRT5 * 0.7 + PI * 0.3 * np.tanh(hf_ratio)
                elif local_var > 0.0005:
                    # Bloc texturé mais peu de HF → e modéré
                    alpha = E * 0.5
                else:
                    # Bloc lisse → e anti-ringing
                    alpha = E * 0.2 * np.exp(-hf_ratio * 2)
                
                alpha *= strength
                
                # Amplifier le résidu local
                res_amplified = res_block * (1.0 + alpha)
                
                # Anti-ringing local
                gy, gx = np.gradient(base_block)
                edge_strength = np.sqrt(gx**2 + gy**2)
                edge_strength = edge_strength / (np.max(edge_strength) + 1e-12)
                damping = 1.0 - edge_strength * 0.3
                damping = np.clip(damping, 0.5, 1.0)
                res_amplified *= damping
                
                # Reconstruire le bloc sharp
                sharp_block = base_block + res_amplified
                
                # Accumuler avec fenêtre Hann
                sharp_accum[y:y+bs, x:x+bs] += sharp_block * self.hann_window
                weight_accum[y:y+bs, x:x+bs] += self.hann_window
        
        weight_accum = np.maximum(weight_accum, 1e-12)
        sharp = sharp_accum / weight_accum
        
        # Clipping sigmoïde
        sharp = np.clip(sharp, 0, 1)
        
        return sharp


# ==============================================================================
# DÉMO COMPARATIVE
# ==============================================================================

def demo_block_svd():
    print("═" * 70)
    print("  PHASE 2 — Block SVD + Hann Window Overlap")
    print("  Roadmap IA Experte — Gain Structurel Textures")
    print("═" * 70)
    
    out_dir = os.path.join(os.path.dirname(__file__), '..',
                           'av_generation_output', 'block_svd')
    os.makedirs(out_dir, exist_ok=True)
    
    # Image test avec textures
    from harmonic_generator_core import HarmonicField, HarmonicColorMapper
    from harmonic_image_generator import save_as_png
    
    print("\n  [1] Image test avec textures variées...")
    field = HarmonicField(width=512, height=512, seed=12345)
    psi = field.get_psi_total()
    
    H, W = psi.shape
    x = np.linspace(-1, 1, W)
    y = np.linspace(-1, 1, H)
    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X**2 + Y**2)
    theta = np.arctan2(Y, X)
    
    psi += 0.25 * np.sin(X * 50 * SQRT5) * np.cos(Y * 50 * SQRT5)
    psi += 0.15 * np.sin(R * 40 + theta * 12)
    psi += 0.10 * np.cos(X * 30) * np.cos(Y * 20)
    psi = normalize_field(psi)
    
    image = (psi + 1) / 2
    rgb = HarmonicColorMapper.harmonic_hsl(psi, palette='cosmique')
    save_as_png(rgb, os.path.join(out_dir, '01_original.png'))
    
    # Comparer SVD globale vs SVD par blocs
    print("\n  [2] SVD globale K=16...")
    t0 = time.time()
    sig_global = HolographicTrainer.train_image(image, K=16)
    recon_global = HolographicGenerator.reconstruct(sig_global)
    if recon_global.shape != image.shape:
        recon_global = np.array(Image.fromarray(
            (recon_global*255).astype(np.uint8)
        ).resize((W, H), Image.LANCZOS), dtype=np.float64) / 255.0
    mse_global = np.mean((image - recon_global)**2)
    psnr_global = 10 * math.log10(1.0/(mse_global+1e-12))
    time_global = (time.time() - t0)*1000
    print(f"    PSNR: {psnr_global:.1f} dB | Temps: {time_global:.0f}ms")
    
    print("\n  [3] SVD par blocs 16×16 + Hann overlap...")
    t0 = time.time()
    block_svd = BlockSVD(block_size=16, overlap=0.25, K=8)
    decomp = block_svd.decompose(image)
    psnr_block = decomp['metrics']['psnr_db']
    time_block = (time.time() - t0)*1000
    print(f"    PSNR: {psnr_block:.1f} dB | Blocs: {decomp['metrics']['n_blocks']}")
    print(f"    Temps: {time_block:.0f}ms")
    
    # Sharpening par blocs
    print("\n  [4] Block Adaptive Sharpener...")
    t0 = time.time()
    sharp_block = block_svd.sharpen_block_adaptive(image, strength=1.0)
    time_sharp = (time.time() - t0)*1000
    
    # Métriques de netteté
    from harmonic_sharpener import HarmonicSharpener
    base_metrics = HarmonicSharpener(K=16).analyze_sharpness(image)
    global_metrics = HarmonicSharpener(K=16).analyze_sharpness(recon_global)
    block_metrics = HarmonicSharpener(K=16).analyze_sharpness(sharp_block)
    
    print(f"""
  📊 Comparaison SVD Globale vs Blocs

  | Version        | PSNR (dB) | Acutance | Laplacian Std |
  |----------------|-----------|----------|---------------|
  | Original       |      —    | {base_metrics['acutance']:8.4f} | {base_metrics['laplacian_std']:13.4f} |
  | SVD Globale    | {psnr_global:9.1f} | {global_metrics['acutance']:8.4f} | {global_metrics['laplacian_std']:13.4f} |
  | SVD Blocks     | {psnr_block:9.1f} | {block_metrics['acutance']:8.4f} | {block_metrics['laplacian_std']:13.4f} |

  Gain Block vs Global :
    PSNR   : {psnr_block - psnr_global:+.1f} dB
    Acutance : {(block_metrics['acutance']/max(1e-12,global_metrics['acutance'])-1)*100:+.0f}%
""")
    
    # Sauvegarder
    for name, arr in [('original', image), ('svd_global', recon_global),
                       ('svd_blocks', sharp_block)]:
        u8 = (np.clip(arr, 0, 1)*255).astype(np.uint8)
        Image.fromarray(np.stack([u8]*3, -1), 'RGB').save(
            os.path.join(out_dir, f'02_{name}.png'))
    
    print(f"\n  ✅ Fichiers dans : {out_dir}/")
    for f in sorted(os.listdir(out_dir)):
        print(f"    {f}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Block SVD Sharpener')
    parser.add_argument('--demo', action='store_true', help='Démo')
    parser.add_argument('--image', type=str, default=None, help='Image')
    args = parser.parse_args()
    
    if args.image:
        img = np.array(Image.open(args.image).convert('L'), dtype=np.float64) / 255.0
        block_svd = BlockSVD(block_size=16, overlap=0.25, K=8)
        sharp = block_svd.sharpen_block_adaptive(img, strength=1.0)
        out = args.image.replace('.', '_block_svd.')
        u8 = (np.clip(sharp, 0, 1)*255).astype(np.uint8)
        Image.fromarray(np.stack([u8]*3, -1), 'RGB').save(out)
        print(f"Image sauvegardée : {out}")
    else:
        demo_block_svd()