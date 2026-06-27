#!/usr/bin/env python3
"""TEST V4 sur contenu structuré — où VQ devrait exceller."""
import numpy as np
import math, sys, os, time

sys.path.insert(0, os.path.dirname(__file__))
from test_hcv_compression_v4 import HCVCompressorV4, compute_psnr
from test_hcv_compression_v3 import HCVCompressorV3
from test_hcv_photorealiste import generate_portrait

def create_struct_images():
    H, W = 256, 256
    x = np.linspace(0, 1, W)
    y = np.linspace(0, 1, H)
    X, Y = np.meshgrid(x, y)
    images = {}
    images['degrade'] = np.clip((X + Y) / 2, 0, 1)
    damier = np.zeros((H, W))
    for i in range(H):
        for j in range(W):
            damier[i, j] = ((i//16) + (j//16)) % 2
    images['damier'] = damier
    images['cercles'] = np.clip((np.sin(np.sqrt((X*W-W//2)**2 + (Y*H-H//2)**2) / W * 20) + 1) / 2, 0, 1)
    images['texture_sinus'] = np.clip((np.sin(X*30) * np.cos(Y*25) + np.sin((X+Y)*15) + 2) / 4, 0, 1)
    images['portrait'] = generate_portrait(H, W)
    return images

def run():
    print("=" * 70)
    print("  TEST V4 sur CONTENU STRUCTURÉ")
    print("  Pyramide + DPCM + VQ — objectif PSNR > 40 dB à ratio > 30×")
    print("=" * 70)

    images = create_struct_images()

    configs = [
        (4, 2, 256, "K0=4,K1=2,VQ256"),
        (6, 3, 512, "K0=6,K1=3,VQ512"),
        (4, 2, 512, "K0=4,K1=2,VQ512"),
    ]

    for K0, K1, VQ_M, label in configs:
        K_total = K0 + K1
        print(f"\n{'='*70}")
        print(f"  {label}  (K_total={K_total})")
        print(f"  {'Image':<16s} {'V3 ratio':>8s} {'V3 PSNR':>9s} {'V4 ratio':>8s} {'V4 PSNR':>9s} {'Δ PSNR':>9s} {'Δ Ratio':>9s}")
        print(f"  {'-'*16} {'-'*8} {'-'*9} {'-'*8} {'-'*9} {'-'*9} {'-'*9}")

        for name, img in images.items():
            # V3 baseline
            comp3 = HCVCompressorV3(K=K_total, block_size=8)
            bs3, meta3 = comp3.compress(img)
            rec3, _ = comp3.decompress(bs3, meta3)
            psnr3 = compute_psnr(img, rec3)

            # V4
            comp4 = HCVCompressorV4(K0=K0, K1=K1, vq_centroids=VQ_M, block_size=8)
            bs4, meta4 = comp4.compress(img)
            rec4, _ = comp4.decompress(bs4, meta4)
            psnr4 = compute_psnr(img, rec4)

            d_psnr = psnr4 - psnr3 if psnr3 != float('inf') and psnr4 != float('inf') else (0 if psnr3 == psnr4 else 999)
            d_ratio = meta4['ratio_effectif'] - meta3['ratio_effectif']

            psnr3_str = f"{psnr3:.1f} dB" if psnr3 != float('inf') else 'INF'
            psnr4_str = f"{psnr4:.1f} dB" if psnr4 != float('inf') else 'INF'
            dpsnr_str = f"+{d_psnr:.1f} dB" if d_psnr > 0 else f"{d_psnr:.1f} dB"
            dratio_str = f"+{d_ratio:.1f}x" if d_ratio > 0 else f"{d_ratio:.1f}x"

            print(f"  {name:<16s} {meta3['ratio_effectif']:7.2f}x {psnr3_str:>9s} {meta4['ratio_effectif']:7.2f}x {psnr4_str:>9s} {dpsnr_str:>9s} {dratio_str:>9s}")

    # Résumé
    print(f"\n{'='*70}")
    print("  RÉSUMÉ — V4 sur Contenu Structuré")
    print(f"  {'='*70}")
    print(f"  La VQ devrait exceller car les vecteurs de coefficients sont")
    print(f"  naturellement clusterisés (peu de patterns distincts).")
    print(f"  Ratio attendu : ~64:1 brut VQ256 + zlib → 30-50× effectif")
    print()

if __name__ == "__main__":
    run()