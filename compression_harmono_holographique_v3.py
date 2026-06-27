#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compression Harmono-Holographique V3
=====================================
Optimisation PSNR via :
1. Blocs 8×8 (comme JPEG) + transformée harmonique par bloc
2. Quantification Lloyd-Max (optimale non-uniforme)
3. Tables de quantification holographiques (basées sur N_PSU)

Combine le meilleur de la V1 (PSNR 51 dB via coeffs par pixel)
et de la V2 (coefficients globaux, transformée, quantification adaptative).

Auteur : KOTTO Alain — 19 Juin 2026 (V3)
"""

import math
import struct
import zlib
import time
from typing import Tuple, Dict, Optional
from PIL import Image
import numpy as np

# ==============================================================================
# CONSTANTES HARMONIQUES
# ==============================================================================
phi = (1 + math.sqrt(5)) / 2
pi_val = math.pi
e_val = math.e
sqrt2 = math.sqrt(2)
sqrt3 = math.sqrt(3)
sqrt5 = math.sqrt(5)
e_sur_pi = e_val / pi_val

H = np.array([phi, pi_val, e_val, sqrt2, sqrt3, sqrt5, e_sur_pi], dtype=np.float64)
H_names = ['φ', 'π', 'e', '√2', '√3', '√5', 'e/π']

c = 299792458.0
hbar = 6.62607015e-34 / (2 * pi_val)
G = 6.67430e-11
l_P = math.sqrt(hbar * G / c**3)

def N_PSU(rayon_m: float) -> float:
    return 4 * rayon_m**2 / l_P**2

# ==============================================================================
# TRANSFORMÉE HARMONIQUE PAR BLOC
# ==============================================================================
BLOCK_SIZE = 8  # Comme JPEG

def transformer_bloc_harmonique(bloc: np.ndarray) -> np.ndarray:
    """
    Transformée harmonique pour un bloc 8×8.
    
    Projette le bloc sur 7 motifs harmoniques.
    Retourne 7 coefficients spectraux.
    
    Similaire à la DCT mais avec base {φ,π,e,√2,√3,√5,e/π}.
    """
    h, w = bloc.shape
    data_norm = bloc.astype(np.float64)
    if data_norm.max() > 0:
        data_norm = data_norm / 255.0
    
    coeffs = np.zeros(7, dtype=np.float64)
    
    # Motifs harmoniques 2D (produit tensoriel de cosinus)
    for n in range(7):
        # Fréquence spatiale pour l'harmonique n
        freq_n = (n + 1) * pi_val / BLOCK_SIZE  # Adapté à la taille du bloc
        
        # Matrice de base harmonique
        y, x = np.ogrid[:h, :w]
        motif = np.cos(freq_n * (x + 0.5) / w) * np.cos(freq_n * (y + 0.5) / h)
        motif *= H[n]  # Poids par le coefficient spectral
        
        # Projection : corrélation normalisée
        coeffs[n] = np.sum(data_norm * motif)
    
    return coeffs


def transformer_bloc_harmonique_inverse(coeffs: np.ndarray, h: int = BLOCK_SIZE, w: int = BLOCK_SIZE) -> np.ndarray:
    """Transformée inverse pour un bloc."""
    reconstruction = np.zeros((h, w), dtype=np.float64)
    
    for n in range(7):
        freq_n = (n + 1) * pi_val / BLOCK_SIZE
        y, x = np.ogrid[:h, :w]
        motif = np.cos(freq_n * (x + 0.5) / w) * np.cos(freq_n * (y + 0.5) / h)
        motif *= H[n]
        reconstruction += coeffs[n] * motif
    
    # Normalisation
    recon_min = reconstruction.min()
    recon_max = reconstruction.max()
    if recon_max > recon_min:
        reconstruction = (reconstruction - recon_min) / (recon_max - recon_min) * 255.0
    
    return np.clip(reconstruction, 0, 255)


# ==============================================================================
# QUANTIFICATION LLOYD-MAX
# ==============================================================================

def lloyd_max_quantizer(data: np.ndarray, n_levels: int, max_iter: int = 50) -> Tuple[np.ndarray, np.ndarray]:
    """
    Algorithme de Lloyd-Max pour quantification optimale non-uniforme.
    
    Minimise l'erreur quadratique moyenne pour n_levels niveaux de quantification.
    Retourne les niveaux de reconstruction et les frontières de décision.
    
    Args:
        data: données à quantifier (1D)
        n_levels: nombre de niveaux de quantification
        max_iter: nombre maximum d'itérations
    
    Returns:
        levels: niveaux de reconstruction
        boundaries: frontières de décision
    """
    data_sorted = np.sort(data)
    n = len(data_sorted)
    
    # Initialisation : niveaux uniformément espacés
    step = n // n_levels
    levels = np.array([data_sorted[min(i * step + step // 2, n - 1)]
                        for i in range(n_levels)], dtype=np.float64)
    
    for iteration in range(max_iter):
        # Étape 1 : frontières de décision (milieu entre niveaux adjacents)
        boundaries = np.zeros(n_levels + 1, dtype=np.float64)
        boundaries[0] = -np.inf
        boundaries[-1] = np.inf
        for i in range(1, n_levels):
            boundaries[i] = (levels[i-1] + levels[i]) / 2
        
        # Étape 2 : nouveaux niveaux = moyenne des données dans chaque région
        new_levels = np.zeros(n_levels, dtype=np.float64)
        for i in range(n_levels):
            mask = (data_sorted >= boundaries[i]) & (data_sorted < boundaries[i+1])
            region_data = data_sorted[mask]
            if len(region_data) > 0:
                new_levels[i] = np.mean(region_data)
            else:
                new_levels[i] = levels[i]  # Garder l'ancien niveau
        
        # Convergence
        if np.max(np.abs(new_levels - levels)) < 1e-10:
            break
        levels = new_levels
    
    return levels, boundaries


def quantifier_lloyd(coeffs_bloc: np.ndarray, levels: np.ndarray) -> np.ndarray:
    """Quantifie un bloc de coefficients avec les niveaux Lloyd-Max."""
    quantized = np.zeros_like(coeffs_bloc, dtype=np.int16)
    for n in range(len(coeffs_bloc)):
        # Trouver le niveau le plus proche
        idx = np.argmin(np.abs(levels - coeffs_bloc[n]))
        quantized[n] = idx
    return quantized


def dequantifier_lloyd(indices: np.ndarray, levels: np.ndarray) -> np.ndarray:
    """Déquantifie les indices en utilisant les niveaux Lloyd-Max."""
    return levels[indices]


# ==============================================================================
# TABLES DE QUANTIFICATION HOLOGRAPHIQUES
# ==============================================================================

def generer_table_quantification(n_psu: float, qualite: int = 50) -> np.ndarray:
    """
    Génère une table de quantification harmonique basée sur N_PSU.
    
    Principe : plus N_PSU est grand, plus on peut se permettre des pas fins.
    La qualité va de 1 (max compression) à 100 (max qualité).
    
    Retourne un array de 7 valeurs (pas de quantification par harmonique).
    """
    # Base : pas inversement proportionnel à H_n (les harmoniques fortes tolèrent plus de quantification)
    base_steps = 1.0 / H  # H_n plus grand → pas plus petit (plus de précision)
    base_steps = base_steps / base_steps.max()  # Normaliser à [0,1]
    
    # Ajustement holographique : N_PSU grand → pas plus petits
    log_n = math.log10(max(n_psu, 1))
    log_ref = math.log10(1.083e40)  # N_PSU du proton comme référence
    scale_holographique = log_ref / max(log_n, 1)
    
    # Ajustement qualité : qualité 1 → pas ×100, qualité 100 → pas ×0.01
    # Mapping qualité → facteur d'échelle
    if qualite <= 0:
        qualite = 1
    if qualite >= 100:
        facteur = 0.01  # Très haute qualité
    else:
        # Formule JPEG-like : q_scale = 5000/qualité pour qualité < 50, 200-2*qualité pour qualité >= 50
        if qualite < 50:
            facteur = 5000.0 / qualite / 100.0
        else:
            facteur = (200.0 - 2.0 * qualite) / 100.0
    
    q_table = base_steps * scale_holographique * facteur * 255.0
    return np.maximum(q_table, 1.0)  # Pas minimum de 1


# ==============================================================================
# ENCODEUR V3
# ==============================================================================

def encoder_image_v3(image_path: str, qualite: int = 50) -> Dict:
    """
    Encode une image avec les améliorations V3 :
    1. Blocs 8×8 + transformée harmonique par bloc
    2. Quantification Lloyd-Max par harmonique
    3. Table de quantification holographique
    """
    img = Image.open(image_path).convert('L')
    data = np.array(img, dtype=np.float64)
    hauteur, largeur = data.shape
    
    # Padding pour avoir des blocs entiers
    pad_h = (BLOCK_SIZE - hauteur % BLOCK_SIZE) % BLOCK_SIZE
    pad_w = (BLOCK_SIZE - largeur % BLOCK_SIZE) % BLOCK_SIZE
    if pad_h > 0 or pad_w > 0:
        data = np.pad(data, ((0, pad_h), (0, pad_w)), mode='edge')
    
    h_padded, w_padded = data.shape
    n_blocs_h = h_padded // BLOCK_SIZE
    n_blocs_w = w_padded // BLOCK_SIZE
    
    # N_PSU
    diagonale = math.sqrt(largeur**2 + hauteur**2)
    rayon_m = diagonale / 2 * 1e-4
    n_psu = N_PSU(rayon_m)
    
    # Table de quantification holographique
    q_table = generer_table_quantification(n_psu, qualite)
    
    # 1. Transformée par bloc
    all_coeffs = []
    for by in range(n_blocs_h):
        for bx in range(n_blocs_w):
            bloc = data[by*BLOCK_SIZE:(by+1)*BLOCK_SIZE, bx*BLOCK_SIZE:(bx+1)*BLOCK_SIZE]
            coeffs = transformer_bloc_harmonique(bloc)
            all_coeffs.append(coeffs)
    
    all_coeffs = np.array(all_coeffs, dtype=np.float64)  # (n_blocs, 7)
    
    # 2. Lloyd-Max : apprentissage des niveaux optimaux par harmonique
    lloyd_levels = []
    for n in range(7):
        coeffs_n = all_coeffs[:, n]
        n_levels = max(4, int(256 / q_table[n]))  # Nombre de niveaux dépend de la table Q
        n_levels = min(n_levels, 256)  # Limiter à 256 niveaux
        
        levels, boundaries = lloyd_max_quantizer(coeffs_n, n_levels)
        lloyd_levels.append(levels)
    
    # 3. Quantification Lloyd-Max
    coeffs_quant = np.zeros_like(all_coeffs, dtype=np.int16)
    for n in range(7):
        coeffs_quant[:, n] = quantifier_lloyd(all_coeffs[:, n], lloyd_levels[n])
    
    # 4. Encodage compact
    # Header : [largeur, hauteur, pad_h, pad_w, qualite, q_table:7×f8, n_blocs_h, n_blocs_w]
    header_data = struct.pack('>HHHHI', largeur, hauteur, pad_h, pad_w, qualite)
    header_data += struct.pack('>' + 'd'*7, *q_table)
    header_data += struct.pack('>HH', n_blocs_h, n_blocs_w)
    
    # Niveaux Lloyd-Max par harmonique
    for n in range(7):
        levels = lloyd_levels[n]
        header_data += struct.pack('>H', len(levels))  # Nombre de niveaux
        header_data += struct.pack('>' + 'd'*len(levels), *levels)
    
    # Coefficients quantifiés (différentiel pour compresser)
    body = coeffs_quant.astype(np.int16).tobytes()
    compressed = zlib.compress(header_data + body, level=9)
    
    taille_originale = data[:hauteur, :largeur].nbytes
    taille_compressee = len(compressed)
    
    return {
        'largeur': largeur,
        'hauteur': hauteur,
        'taille_originale': taille_originale,
        'taille_compressee': taille_compressee,
        'ratio_compression': taille_originale / taille_compressee,
        'qualite': qualite,
        'q_table': q_table,
        'lloyd_levels': lloyd_levels,
        'coeffs_quant': coeffs_quant,
        'n_blocs': (n_blocs_h, n_blocs_w),
        'pad': (pad_h, pad_w),
        'compressed_data': compressed,
        'N_PSU_surface': n_psu,
        'n_harmoniques': 7,
    }


# ==============================================================================
# DÉCODEUR V3
# ==============================================================================

def decoder_image_v3(resultat: Dict, sauvegarder: Optional[str] = None) -> np.ndarray:
    """Décode une image compressée V3."""
    data_bytes = zlib.decompress(resultat['compressed_data'])
    
    # Décodage header
    offset = 0
    largeur, hauteur, pad_h, pad_w, qualite = struct.unpack('>HHHHI', data_bytes[offset:offset+12])
    offset += 12
    
    q_table = np.array(struct.unpack('>' + 'd'*7, data_bytes[offset:offset+56]))
    offset += 56
    
    n_blocs_h, n_blocs_w = struct.unpack('>HH', data_bytes[offset:offset+4])
    offset += 4
    
    # Niveaux Lloyd-Max
    lloyd_levels = []
    for n in range(7):
        n_levels = struct.unpack('>H', data_bytes[offset:offset+2])[0]
        offset += 2
        levels = np.array(struct.unpack('>' + 'd'*n_levels, data_bytes[offset:offset+n_levels*8]))
        offset += n_levels * 8
        lloyd_levels.append(levels)
    
    # Coefficients quantifiés
    n_blocs = n_blocs_h * n_blocs_w
    coeffs_quant = np.frombuffer(data_bytes[offset:], dtype=np.int16).reshape(n_blocs, 7)
    
    # Déquantification
    coeffs = np.zeros_like(coeffs_quant, dtype=np.float64)
    for n in range(7):
        coeffs[:, n] = dequantifier_lloyd(coeffs_quant[:, n], lloyd_levels[n])
    
    # Transformée inverse par bloc
    h_total = n_blocs_h * BLOCK_SIZE
    w_total = n_blocs_w * BLOCK_SIZE
    reconstruction = np.zeros((h_total, w_total), dtype=np.float64)
    
    for idx, coeffs_bloc in enumerate(coeffs):
        by = idx // n_blocs_w
        bx = idx % n_blocs_w
        bloc_reconstruit = transformer_bloc_harmonique_inverse(coeffs_bloc)
        reconstruction[by*BLOCK_SIZE:(by+1)*BLOCK_SIZE,
                       bx*BLOCK_SIZE:(bx+1)*BLOCK_SIZE] = bloc_reconstruit
    
    # Enlever le padding
    reconstruction = reconstruction[:hauteur, :largeur]
    reconstruction = np.clip(reconstruction, 0, 255).astype(np.uint8)
    
    if sauvegarder:
        Image.fromarray(reconstruction).save(sauvegarder)
    
    return reconstruction


# ==============================================================================
# BENCHMARK V3
# ==============================================================================

def benchmark_compression_v3(image_path: str):
    """Benchmark V3 vs standards pour plusieurs qualités."""
    print("=" * 80)
    print("BENCHMARK V3 — Compression Harmono-Holographique")
    print("Blocs 8×8 + Transformée Harmonique + Lloyd-Max + Q-Table Holographique")
    print("=" * 80)
    print(f"  Image : {image_path}")
    print()
    
    img = Image.open(image_path).convert('L')
    data = np.array(img)
    hauteur, largeur = data.shape
    taille_originale = data.nbytes
    
    print(f"  Dimensions   : {largeur} × {hauteur}")
    print(f"  Taille brute : {taille_originale:,} octets ({taille_originale/1024:.1f} Ko)")
    print()
    
    # PNG et JPEG
    import io
    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    taille_png = buf.tell()
    
    print(f"  Références :")
    print(f"    PNG  (sans perte) : {taille_png:>8,} octets ({taille_originale/taille_png:5.1f}:1)")
    
    # Test pour plusieurs qualités
    print()
    print(f"  V3 — Compression harmonique par blocs :")
    print(f"  {'Qualité':>8s}  {'Taille':>10s}  {'Ratio':>8s}  {'PSNR':>8s}  {'Temps':>8s}")
    print(f"  {'-'*8}  {'-'*10}  {'-'*8}  {'-'*8}  {'-'*8}")
    
    best_result = None
    for qualite in [10, 25, 50, 75, 90]:
        debut = time.time()
        resultat = encoder_image_v3(image_path, qualite=qualite)
        duree = time.time() - debut
        
        img_decodee = decoder_image_v3(resultat)
        mse = np.mean((data.astype(np.float64) - img_decodee.astype(np.float64))**2)
        psnr = 20 * math.log10(255.0 / math.sqrt(mse)) if mse > 0 else float('inf')
        
        print(f"  {qualite:8d}  {resultat['taille_compressee']:>10,}  "
              f"{resultat['ratio_compression']:>7.1f}:1  {psnr:>7.2f} dB  {duree:>7.3f}s")
        
        if best_result is None or (psnr > 30 and resultat['ratio_compression'] > 2):
            best_result = resultat
            best_result['psnr'] = psnr
    
    # Sauvegarder la meilleure reconstruction
    if best_result:
        decoder_image_v3(best_result, image_path.replace('.', '_harmonique_v3.'))
        print()
        print(f"  Meilleure image sauvegardée : {image_path.replace('.', '_harmonique_v3.')}")
    
    print()
    print("=" * 80)
    print("TERMINÉ")
    print("=" * 80)


# ==============================================================================
# DÉMONSTRATION
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("COMPRESSION HARMONO-HOLOGRAPHIQUE V3")
    print("Blocs 8x8 + Lloyd-Max + Q-Table Holographique")
    print("=" * 70)
    print()
    print(f"  Coefficients spectraux Hₙ :")
    for i, (nom, val) in enumerate(zip(H_names, H)):
        print(f"    H{i+1} = {nom:<4s} = {val:.6f}")
    print()
    
    import sys
    if len(sys.argv) > 1:
        benchmark_compression_v3(sys.argv[1])
    else:
        print("  Création d'une image de test synthétique...")
        
        taille = 256
        x = np.linspace(0, 4 * pi_val, taille)
        y = np.linspace(0, 4 * pi_val, taille)
        X, Y = np.meshgrid(x, y)
        
        img_test = np.zeros((taille, taille), dtype=np.float64)
        for n, h_n in enumerate(H):
            img_test += h_n * np.sin((n + 1) * X) * np.cos((n + 1) * Y)
        
        img_test = (img_test - img_test.min()) / (img_test.max() - img_test.min()) * 255
        img_test = img_test.astype(np.uint8)
        
        test_path = "test_harmonique.png"
        Image.fromarray(img_test).save(test_path)
        print(f"  Image test créée : {test_path}")
        print()
        
        benchmark_compression_v3(test_path)