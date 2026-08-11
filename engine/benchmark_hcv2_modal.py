#!/usr/bin/env python3
"""benchmark_hcv2_modal.py — le protocole honnête du codec modal HCV2.

Mesure sur de VRAIES images (architecture, paysage, macro) : ratio vs
fichier ET vs RAW, PSNR, SSIM, masse de Parseval retenue. Zéro paramètre
ajusté — le seuil 1/(φ·m) et la chaîne cₙ sont des théorèmes.

Usage : python benchmark_hcv2_modal.py
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent / 'vital-ka' / 'core' / 'python'))
from hcv2_modal_codec import benchmark  # noqa: E402

IMAGES = [
    r'E:\SAAS - Copie\COMPRESSION-CAMERA\METHOD_2_SDI_LIKE_IMAGE_COMPRESSION\architecture_photo.png',
    r'E:\SAAS - Copie\COMPRESSION-CAMERA\METHOD_2_SDI_LIKE_IMAGE_COMPRESSION\landscape_natural.png',
    r'E:\SAAS - Copie\COMPRESSION-CAMERA\METHOD_2_SDI_LIKE_IMAGE_COMPRESSION\macro_photography.png',
]

print("═" * 72)
print("HCV2 PISTE 1 — LE CODEC MODAL HARMONIQUE (troncature dorée + chaîne cₙ)")
print("═" * 72)
print(f"{'image':<24}{'ratio/fichier':>14}{'ratio/RAW':>12}{'PSNR':>9}{'SSIM':>8}{'masse':>8}")
print('─' * 72)
for path in IMAGES:
    name = Path(path).stem
    img = np.array(Image.open(path).convert('RGB'))
    file_bytes = Path(path).stat().st_size
    r = benchmark(img, file_bytes)
    print(f"{name:<24}{r.ratio_file:>12.2f}×{r.ratio_raw:>10.2f}×"
          f"{r.psnr:>9.2f}{r.ssim:>8.4f}{r.mass_kept:>8.3f}")

print('─' * 72)
print("Références de la base SDI (les mesures honnêtes de l'ancien projet) :")
print("   B3 (10 frames, H.264)   : 8,51× @ 51,22 dB")
print("   Contenu broadcast optim. : 15,17× (lossless bit-à-bit, PSNR ∞)")
print("═" * 72)
