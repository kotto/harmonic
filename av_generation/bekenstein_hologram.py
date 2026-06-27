#!/usr/bin/env python3
# coding: utf-8
"""
BEKENSTEIN HOLOGRAM — Boundary + Residue Encoding (Piste 1+3)
===============================================================
Amélioration du PSNR (22 dB → cible 45-55 dB) par :
  Piste 1 : Frontière RAW (non compressée) → conditions aux bords exactes
  Piste 3 : Résidu harmonique compressé SVD K=8 → détails fins

Encodage :
  boundary = concat(top, bottom, left, right)             → 8192 o (256²)
  harmonic = solve_laplace_direct(boundary)                 → ∇²Ψ=0
  residue  = image - harmonic                               → hautes fréquences
  residue_svd = train_svd(residue, K=8)                     → ~4000 o
  Total    = 8192 + ~4000 ≈ 12 Ko (vs 139 Ko SVD global)

Décodage :
  boundary → solve_laplace → harmonic
  residue_svd → reconstruct → residue
  image = harmonic + residue

Comparaison :
  Stockage  : 12 Ko vs 139 Ko (SVD) → 11.6× plus compact
  PSNR visé : 45-55 dB (proche du SVD global 57 dB)
  Temps     : ~100ms (DST 2D 50ms + SVD résidu 50ms)

Usage :
  python bekenstein_hologram.py --demo
"""

import numpy as np, math, sys, os, time, argparse
from typing import Dict, Any, Tuple, Optional
from scipy.ndimage import gaussian_filter
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from harmonic_generator_core import (PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI, H_CONSTANTS,
                                      H_NAMES, HarmonicColorMapper, SeedManager, normalize_field)
from holographic_one_shot import HolographicTrainer, HolographicGenerator, BLOCK_SIZE, BLOCK_DIM
from harmonic_sharpener import HarmonicSharpener


# ==============================================================================
# BEKENSTEIN HOLOGRAM — Boundary + Residue (Pistes 1+3)
# ==============================================================================

class BekensteinHologram:
    """
    Hologramme Bekenstein optimisé PSNR.
    
    Stratégie : Frontière RAW (précise) + Résidu SVD (compressé).
    """
    
    def __init__(self, K_residue: int = 8):
        self.K_residue = K_residue
    
    def encode(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Encode : frontière brute + résidu harmonique compressé.
        """
        H, W = image.shape
        
        # --- Piste 1 : Frontière RAW (8 Ko, sans perte) ---
        top = image[0, :].copy()
        bottom = image[-1, :].copy()
        left = image[:, 0].copy()
        right = image[:, -1].copy()
        boundary_raw = np.concatenate([top, bottom, left, right])
        
        # --- Résoudre Laplace depuis la frontière ---
        boundary_data = {
            'top': top, 'bottom': bottom, 'left': left, 'right': right,
            'source_shape': (H, W),
            # coins implicites dans les bords
            'corners': np.array([image[0,0], image[0,-1], image[-1,-1], image[-1,0]]),
        }
        harmonic = self._solve_laplace_direct(boundary_data)
        
        # --- Piste 3 : Résidu compressé ---
        residue = image - harmonic
        # Normaliser le résidu pour la compression (centré, faible amplitude)
        residue_mean = float(np.mean(residue))
        residue_std = float(np.std(residue)) + 1e-8
        residue_norm = (residue - residue_mean) / residue_std
        
        # SVD sur le résidu normalisé
        sig_residue = HolographicTrainer.train_image(residue_norm, K=self.K_residue)
        
        # Métriques
        mse_residue = np.mean(residue ** 2)
        energy_image = np.sum(image ** 2)
        energy_residue = np.sum(residue ** 2)
        
        boundary_bytes = boundary_raw.nbytes
        residue_bytes = sig_residue.hologram.nbytes + sig_residue.coefficients.nbytes
        total_bytes = boundary_bytes + residue_bytes
        
        return {
            'boundary_raw': boundary_raw,
            'boundary_len': len(boundary_raw),
            'residue_signature': sig_residue,
            'residue_mean': residue_mean,
            'residue_std': residue_std,
            'source_shape': (H, W),
            'corners': boundary_data['corners'],
            'metrics': {
                'boundary_bytes': boundary_bytes,
                'residue_bytes': residue_bytes,
                'total_bytes': total_bytes,
                'compression_ratio': (H * W * 8) / max(1, total_bytes),
                'energy_residue_pct': float(energy_residue / (energy_image + 1e-12) * 100),
                'residue_mse': float(mse_residue),
            },
        }
    
    def _solve_laplace_direct(self, boundary_data: Dict[str, Any]) -> np.ndarray:
        """
        Résout ∇²Ψ=0 avec DST 2D (noyau de Green).
        """
        H, W = boundary_data['source_shape']
        top = boundary_data['top']
        bottom = boundary_data['bottom']
        left = boundary_data['left']
        right = boundary_data['right']
        corners = boundary_data['corners']
        
        image = np.zeros((H, W), dtype=np.float64)
        image[0, :] = top
        image[-1, :] = bottom
        image[:, 0] = left
        image[:, -1] = right
        image[0, 0] = corners[0]
        image[0, -1] = corners[1]
        image[-1, -1] = corners[2]
        image[-1, 0] = corners[3]
        
        # Interpolation bilinéaire initiale
        y_ramp = np.linspace(0, 1, H).reshape(-1, 1)
        x_ramp = np.linspace(0, 1, W).reshape(1, -1)
        interior = (
            top.reshape(1,-1) * (1-y_ramp) + bottom.reshape(1,-1) * y_ramp +
            left.reshape(-1,1) * (1-x_ramp) + right.reshape(-1,1) * x_ramp
        ) / 2
        image[1:-1, 1:-1] = interior[1:-1, 1:-1]
        
        # DST 2D du résidu intérieur
        interior_only = image[1:-1, 1:-1].copy()
        dst_coeffs = self._dst2d(interior_only)
        
        h_inner, w_inner = interior_only.shape
        i_idx = np.arange(1, h_inner+1).reshape(-1, 1)
        j_idx = np.arange(1, w_inner+1).reshape(1, -1)
        eigenvalues = -(np.pi**2) * (i_idx**2 / H**2 + j_idx**2 / W**2)
        inv_eig = np.where(np.abs(eigenvalues) > 1e-12, 1.0/eigenvalues, 0.0)
        solution_interior = self._idst2d(dst_coeffs * inv_eig)
        
        image[1:-1, 1:-1] = solution_interior
        image[0, :], image[-1, :] = top, bottom
        image[:, 0], image[:, -1] = left, right
        image[0, 0], image[0, -1] = corners[0], corners[1]
        image[-1, -1], image[-1, 0] = corners[2], corners[3]
        
        return np.clip(image, 0, 1)
    
    def _dst2d(self, x):
        h, w = x.shape
        n_rows = np.arange(1, h+1).reshape(-1, 1)
        k_rows = np.arange(1, h+1).reshape(1, -1)
        S_h = np.sin(np.pi * n_rows * k_rows / (h+1))
        n_cols = np.arange(1, w+1).reshape(-1, 1)
        k_cols = np.arange(1, w+1).reshape(1, -1)
        S_w = np.sin(np.pi * n_cols * k_cols / (w+1))
        return S_h @ x @ S_w.T
    
    def _idst2d(self, x):
        h, w = x.shape
        return self._dst2d(x) * (4.0 / ((h+1)*(w+1)))
    
    def decode(self, hologram_data: Dict[str, Any]) -> np.ndarray:
        """
        Décode : Laplace(frontière) + Reconstruction(résidu SVD).
        """
        H, W = hologram_data['source_shape']
        boundary_raw = hologram_data['boundary_raw']
        corners = hologram_data['corners']
        sig_residue = hologram_data['residue_signature']
        residue_mean = hologram_data['residue_mean']
        residue_std = hologram_data['residue_std']
        
        # 1. Reconstruire la frontière
        idx = 0
        top = boundary_raw[idx:idx+W]; idx += W
        bottom = boundary_raw[idx:idx+W]; idx += W
        left = boundary_raw[idx:idx+H]; idx += H
        right = boundary_raw[idx:idx+H]
        
        boundary_data = {
            'top': top, 'bottom': bottom, 'left': left, 'right': right,
            'source_shape': (H, W), 'corners': corners,
        }
        
        # 2. Solution harmonique
        harmonic = self._solve_laplace_direct(boundary_data)
        
        # 3. Reconstruire le résidu depuis SVD
        residue_norm = HolographicGenerator.reconstruct(sig_residue, width=W, height=H)
        if residue_norm.shape != harmonic.shape:
            residue_norm = np.array(Image.fromarray(
                (residue_norm*255).astype(np.uint8)
            ).resize((W, H), Image.LANCZOS), dtype=np.float64)/255.0
        residue = residue_norm * residue_std + residue_mean
        
        # 4. Image finale
        image = harmonic + residue
        return np.clip(image, 0, 1)
    
    def compute_psnr(self, original: np.ndarray, decoded: np.ndarray) -> float:
        mse = np.mean((original - decoded) ** 2)
        return 10 * math.log10(1.0/(mse + 1e-12)) if mse > 0 else 999


# ==============================================================================
# COMPARAISON RAPIDE
# ==============================================================================

def demo_bekenstein_v2():
    print("═" * 70)
    print("  BEKENSTEIN V2 — Frontière RAW + Résidu SVD (Pistes 1+3)")
    print("═" * 70)
    
    out_dir = os.path.join(os.path.dirname(__file__), '..',
                           'av_generation_output', 'bekenstein_v2')
    os.makedirs(out_dir, exist_ok=True)
    
    from harmonic_generator_core import HarmonicField, HarmonicColorMapper
    from harmonic_image_generator import save_as_png
    
    # Image test
    print("\n  [1] Image test 256×256...")
    field = HarmonicField(width=256, height=256, seed=12345)
    psi = field.get_psi_total()
    H,W=psi.shape
    x=np.linspace(-1,1,W); y=np.linspace(-1,1,H)
    X,Y=np.meshgrid(x,y); R=np.sqrt(X**2+Y**2); theta=np.arctan2(Y,X)
    psi += 0.2*np.sin(X*40*SQRT5)*np.cos(Y*40*SQRT5) + 0.1*np.sin(R*30+theta*12)
    psi = normalize_field(psi)
    image = (psi+1)/2
    rgb = HarmonicColorMapper.harmonic_hsl(psi, palette='cosmique')
    save_as_png(rgb, os.path.join(out_dir, '01_original.png'))
    
    # Bekenstein V2
    print("\n  [2] Encodage Bekenstein V2 (frontière RAW + résidu SVD K=8)...")
    bh = BekensteinHologram(K_residue=8)
    t0=time.time()
    holo = bh.encode(image)
    enc_time = (time.time()-t0)*1000
    m=holo['metrics']
    print(f"    Encode: {enc_time:.0f}ms")
    print(f"    Frontière: {m['boundary_bytes']:,} o | Résidu SVD: {m['residue_bytes']:,} o")
    print(f"    Total stockage: {m['total_bytes']:,} o | Ratio: {m['compression_ratio']:.1f}×")
    print(f"    Energie résidu: {m['energy_residue_pct']:.2f}%")
    
    # Décodage
    print("\n  [3] Décodage...")
    t0=time.time()
    decoded = bh.decode(holo)
    dec_time = (time.time()-t0)*1000
    
    # Comparer avec SVD
    print("\n  [4] Comparaison SVD standard...")
    t0=time.time()
    sig = HolographicTrainer.train_image(image, K=16)
    recon_svd = HolographicGenerator.reconstruct(sig)
    if recon_svd.shape!=image.shape:
        recon_svd=np.array(Image.fromarray((recon_svd*255).astype(np.uint8)).resize((W,H),Image.LANCZOS),dtype=np.float64)/255.0
    svd_time=(time.time()-t0)*1000
    
    psnr_bek = bh.compute_psnr(image, decoded)
    psnr_svd = bh.compute_psnr(image, recon_svd)
    
    svd_bytes = sig.hologram.nbytes + sig.coefficients.nbytes
    bek_bytes = m['total_bytes']
    
    hs=HarmonicSharpener(K=16)
    m_svd=hs.analyze_sharpness(recon_svd)
    m_bek=hs.analyze_sharpness(decoded)
    m_orig=hs.analyze_sharpness(image)
    
    print(f"""
{'='*60}
COMPARAISON BEKENSTEIN V2 vs SVD
{'='*60}
{'':<20s} {'SVD K=16':>12s} {'Bek V2':>12s} {'Ratio':>10s}
PSNR (dB)     {psnr_svd:12.1f} {psnr_bek:12.1f} {psnr_bek/max(1,psnr_svd):10.2f}x
Stockage (o)  {svd_bytes:12,} {bek_bytes:12,} {svd_bytes/max(1,bek_bytes):10.1f}x
Acutance      {m_svd['acutance']:12.4f} {m_bek['acutance']:12.4f}
Temps (ms)    {svd_time:12.0f} {dec_time:12.0f}
""")
    
    # Sauvegarder
    for name, arr in [('original', image), ('svd_recon', recon_svd), ('bekenstein_v2', decoded)]:
        u8=(np.clip(arr,0,1)*255).astype(np.uint8)
        Image.fromarray(np.stack([u8]*3,-1),'RGB').save(os.path.join(out_dir, f'02_{name}.png'))
    
    print(f"  ✅ Fichiers: {out_dir}/")
    for f in sorted(os.listdir(out_dir)):
        print(f"    {f}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--image', type=str, default=None)
    args = parser.parse_args()
    
    if args.image:
        img = np.array(Image.open(args.image).convert('L'), dtype=np.float64)/255.0
        bh = BekensteinHologram(K_residue=8)
        holo = bh.encode(img)
        decoded = bh.decode(holo)
        out = args.image.replace('.', '_bekv2.')
        u8=(np.clip(decoded,0,1)*255).astype(np.uint8)
        Image.fromarray(np.stack([u8]*3,-1),'RGB').save(out)
        print(f"PSNR: {bh.compute_psnr(img,decoded):.1f} dB → {out}")
    else:
        demo_bekenstein_v2()