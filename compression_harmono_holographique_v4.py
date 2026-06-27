#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compression Harmono-Holographique V4
=====================================
Combine le meilleur des versions précédentes :
- Approche V1 : 7 coeffs PAR PIXEL (PSNR 51 dB, quasi sans perte)
- Quantification Lloyd-Max (optimale non-uniforme)
- Q-table holographique (pas de quantification basé sur N_PSU)

Résultat attendu : PSNR > 40 dB avec ratio de compression > 5:1

Auteur : KOTTO Alain — 19 Juin 2026 (V4)
"""

import math, struct, zlib, time
from typing import Tuple, Dict, Optional
from PIL import Image
import numpy as np

# Constantes harmoniques
phi = (1 + math.sqrt(5)) / 2
pi_val = math.pi
e_val = math.e
sqrt2 = math.sqrt(2)
sqrt3 = math.sqrt(3)
sqrt5 = math.sqrt(5)
e_sur_pi = e_val / pi_val

H = np.array([phi, pi_val, e_val, sqrt2, sqrt3, sqrt5, e_sur_pi], dtype=np.float64)
H_names = ['φ', 'π', 'e', '√2', '√3', '√5', 'e/π']
H_sum = H.sum()

c_light = 299792458.0
hbar = 6.62607015e-34 / (2 * pi_val)
G = 6.67430e-11
l_P = math.sqrt(hbar * G / c_light**3)

def N_PSU(rayon_m): return 4 * rayon_m**2 / l_P**2

# ==============================================================================
# APPROCHE V1 AMÉLIORÉE : 7 coeffs par pixel (quasi-lossless)
# ==============================================================================
def projeter_harmonique_v4(data: np.ndarray) -> np.ndarray:
    """
    Projection V1 améliorée : chaque pixel est décomposé en 7 composantes.
    pixel ≈ Σ (H[n]/H_sum) * pixel  →  coeff[n] = pixel * H[n]/H_sum
    
    Cette décomposition est EXACTE (Σ H[n]/H_sum = 1).
    """
    data_flat = data.flatten().astype(np.float64)
    n_pixels = len(data_flat)
    coeffs = np.zeros((7, n_pixels), dtype=np.float64)
    for n in range(7):
        coeffs[n] = data_flat * H[n] / H_sum
    return coeffs

def reconstruire_v4(coeffs: np.ndarray) -> np.ndarray:
    """Reconstruction exacte : Σ coeffs[n] = pixel original."""
    return np.sum(coeffs, axis=0)

# ==============================================================================
# LLOYD-MAX
# ==============================================================================
def lloyd_max_quantizer(data: np.ndarray, n_levels: int, max_iter: int = 50):
    data_sorted = np.sort(data)
    n = len(data_sorted)
    step = n // n_levels
    levels = np.array([data_sorted[min(i * step + step // 2, n - 1)]
                       for i in range(n_levels)], dtype=np.float64)
    
    for _ in range(max_iter):
        boundaries = np.zeros(n_levels + 1, dtype=np.float64)
        boundaries[0], boundaries[-1] = -np.inf, np.inf
        for i in range(1, n_levels):
            boundaries[i] = (levels[i-1] + levels[i]) / 2
        
        new_levels = np.zeros(n_levels, dtype=np.float64)
        for i in range(n_levels):
            mask = (data_sorted >= boundaries[i]) & (data_sorted < boundaries[i+1])
            region_data = data_sorted[mask]
            new_levels[i] = np.mean(region_data) if len(region_data) > 0 else levels[i]
        
        if np.max(np.abs(new_levels - levels)) < 1e-10:
            break
        levels = new_levels
    
    return levels, boundaries

def quantifier_lloyd(coeffs_1d: np.ndarray, levels: np.ndarray) -> np.ndarray:
    indices = np.zeros(len(coeffs_1d), dtype=np.int16)
    for i in range(len(coeffs_1d)):
        indices[i] = np.argmin(np.abs(levels - coeffs_1d[i]))
    return indices

def dequantifier_lloyd(indices: np.ndarray, levels: np.ndarray) -> np.ndarray:
    return levels[indices]

# ==============================================================================
# Q-TABLE HOLOGRAPHIQUE
# ==============================================================================
def generer_table_quantification(n_psu: float, qualite: int = 50) -> np.ndarray:
    base_steps = 1.0 / H
    base_steps = base_steps / base_steps.max()
    log_n = math.log10(max(n_psu, 1))
    log_ref = math.log10(1.083e40)
    scale_holographique = log_ref / max(log_n, 1)
    
    if qualite >= 100:
        facteur = 0.01
    elif qualite < 50:
        facteur = 5000.0 / qualite / 100.0
    else:
        facteur = (200.0 - 2.0 * qualite) / 100.0
    
    q_table = base_steps * scale_holographique * facteur * 255.0
    return np.maximum(q_table, 1.0)

# ==============================================================================
# ENCODEUR V4
# ==============================================================================
def encoder_image_v4(image_path: str, qualite: int = 50) -> Dict:
    img = Image.open(image_path).convert('L')
    data = np.array(img, dtype=np.float64)
    hauteur, largeur = data.shape
    
    diagonale = math.sqrt(largeur**2 + hauteur**2)
    rayon_m = diagonale / 2 * 1e-4
    n_psu = N_PSU(rayon_m)
    q_table = generer_table_quantification(n_psu, qualite)
    
    # Projection harmonique (V1)
    coeffs = projeter_harmonique_v4(data)  # (7, n_pixels)
    
    # Lloyd-Max par harmonique
    lloyd_levels = []
    coeffs_quant = np.zeros_like(coeffs, dtype=np.int16)
    for n in range(7):
        n_levels = max(4, int(256 / q_table[n]))
        n_levels = min(n_levels, 256)
        levels, _ = lloyd_max_quantizer(coeffs[n], n_levels)
        lloyd_levels.append(levels)
        coeffs_quant[n] = quantifier_lloyd(coeffs[n], levels)
    
    # Encodage header + body
    header = struct.pack('>HHHI', largeur, hauteur, qualite, int(math.log10(max(n_psu, 1))))
    header += struct.pack('>' + 'd'*7, *q_table)
    for n in range(7):
        levels = lloyd_levels[n]
        header += struct.pack('>H', len(levels))
        header += struct.pack('>' + 'd'*len(levels), *levels)
    
    body = coeffs_quant.astype(np.int16).tobytes()
    compressed = zlib.compress(header + body, level=9)
    
    taille_originale = data.nbytes
    taille_compressee = len(compressed)
    
    return {
        'largeur': largeur, 'hauteur': hauteur,
        'taille_originale': taille_originale,
        'taille_compressee': taille_compressee,
        'ratio_compression': taille_originale / taille_compressee,
        'qualite': qualite, 'q_table': q_table,
        'lloyd_levels': lloyd_levels,
        'coeffs_quant': coeffs_quant,
        'compressed_data': compressed,
        'N_PSU_surface': n_psu,
    }

# ==============================================================================
# DÉCODEUR V4
# ==============================================================================
def decoder_image_v4(resultat: Dict, sauvegarder: Optional[str] = None) -> np.ndarray:
    data_bytes = zlib.decompress(resultat['compressed_data'])
    offset = 0
    
    largeur, hauteur, qualite, _ = struct.unpack('>HHHI', data_bytes[offset:offset+10])
    offset += 10
    q_table = np.array(struct.unpack('>' + 'd'*7, data_bytes[offset:offset+56]))
    offset += 56
    
    lloyd_levels = []
    for _ in range(7):
        n_levels = struct.unpack('>H', data_bytes[offset:offset+2])[0]
        offset += 2
        levels = np.array(struct.unpack('>' + 'd'*n_levels, data_bytes[offset:offset+n_levels*8]))
        offset += n_levels * 8
        lloyd_levels.append(levels)
    
    n_pixels = hauteur * largeur
    coeffs_quant = np.frombuffer(data_bytes[offset:offset + n_pixels * 7 * 2], dtype=np.int16)
    coeffs_quant = coeffs_quant.reshape(7, n_pixels)
    
    coeffs = np.zeros_like(coeffs_quant, dtype=np.float64)
    for n in range(7):
        coeffs[n] = dequantifier_lloyd(coeffs_quant[n], lloyd_levels[n])
    
    reconstruction = reconstruire_v4(coeffs)
    reconstruction = np.clip(reconstruction, 0, 255).astype(np.uint8).reshape(hauteur, largeur)
    
    if sauvegarder:
        Image.fromarray(reconstruction).save(sauvegarder)
    return reconstruction

# ==============================================================================
# BENCHMARK
# ==============================================================================
def benchmark_compression_v4(image_path: str):
    print("=" * 80)
    print("BENCHMARK V4 — Compression Harmono-Holographique")
    print("V1 (per-pixel) + Lloyd-Max + Q-Table Holographique")
    print("=" * 80)
    print(f"  Image : {image_path}")
    print()
    
    img = Image.open(image_path).convert('L')
    data = np.array(img)
    hauteur, largeur = data.shape
    taille_originale = data.nbytes
    
    print(f"  Dimensions   : {largeur} × {hauteur}")
    print(f"  Taille brute : {taille_originale:,} octets")
    print()
    
    import io
    buf = io.BytesIO(); img.save(buf, format='PNG', optimize=True); taille_png = buf.tell()
    
    # JPEG qualité 85
    buf_jpg = io.BytesIO(); img.save(buf_jpg, format='JPEG', quality=85, optimize=True); taille_jpg = buf_jpg.tell()
    
    print(f"  Références :")
    print(f"    PNG              : {taille_png:>8,} octets ({taille_originale/taille_png:.1f}:1)")
    print(f"    JPEG (qualité 85): {taille_jpg:>8,} octets ({taille_originale/taille_jpg:.1f}:1)")
    print()
    
    print(f"  V4 — Compression harmonique per-pixel + Lloyd-Max :")
    print(f"  {'Qualité':>8s}  {'Taille':>9s}  {'Ratio':>7s}  {'PSNR':>7s}  {'Temps':>7s}")
    print(f"  {'-'*8}  {'-'*9}  {'-'*7}  {'-'*7}  {'-'*7}")
    
    for qualite in [10, 25, 50, 75, 90]:
        debut = time.time()
        resultat = encoder_image_v4(image_path, qualite=qualite)
        duree = time.time() - debut
        
        img_decodee = decoder_image_v4(resultat)
        mse = np.mean((data.astype(np.float64) - img_decodee.astype(np.float64))**2)
        psnr = 20 * math.log10(255.0 / math.sqrt(mse)) if mse > 0 else float('inf')
        
        print(f"  {qualite:8d}  {resultat['taille_compressee']:>9,}  "
              f"{resultat['ratio_compression']:>6.1f}:1  {psnr:>6.2f} dB  {duree:>6.3f}s")
    
    print()
    print("=" * 80)
    print("TERMINÉ")
    print("=" * 80)

if __name__ == "__main__":
    print("=" * 70)
    print("COMPRESSION HARMONO-HOLOGRAPHIQUE V4")
    print("=" * 70)
    print()
    
    import sys
    if len(sys.argv) > 1:
        benchmark_compression_v4(sys.argv[1])
    else:
        taille = 256
        x = np.linspace(0, 4 * pi_val, taille)
        y = np.linspace(0, 4 * pi_val, taille)
        X, Y = np.meshgrid(x, y)
        img_test = np.zeros((taille, taille), dtype=np.float64)
        for n, h_n in enumerate(H):
            img_test += h_n * np.sin((n+1) * X) * np.cos((n+1) * Y)
        img_test = (img_test - img_test.min()) / (img_test.max() - img_test.min()) * 255
        img_test = img_test.astype(np.uint8)
        test_path = "test_harmonique.png"
        Image.fromarray(img_test).save(test_path)
        print(f"  Image test créée : {test_path}")
        print()
        benchmark_compression_v4(test_path)