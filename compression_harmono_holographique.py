#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compression Harmono-Holographique
==================================
Système de compression basé sur Ψ = Σ Hₙ · fⁿ.

Principe : toute donnée se décompose en 7 harmoniques pondérées
par les coefficients spectraux {φ, π, e, √2, √3, √5, e/π}.
La borne de compression est imposée par N_PSU = 4R²/l_P².

Auteur : KOTTO Alain — 19 Juin 2026
"""

import math
import struct
import zlib
import time
from typing import Tuple, List, Dict, Optional
from PIL import Image
import numpy as np

# ==============================================================================
# CONSTANTES HARMONIQUES
# ==============================================================================
phi = (1 + math.sqrt(5)) / 2
pi = math.pi
e = math.e
sqrt2 = math.sqrt(2)
sqrt3 = math.sqrt(3)
sqrt5 = math.sqrt(5)
e_sur_pi = e / pi

H = np.array([phi, pi, e, sqrt2, sqrt3, sqrt5, e_sur_pi], dtype=np.float64)
H_names = ['φ', 'π', 'e', '√2', '√3', '√5', 'e/π']

# Constantes physiques pour la borne holographique
c = 299792458.0
h = 6.62607015e-34
G = 6.67430e-11
hbar = h / (2 * pi)
l_P = math.sqrt(hbar * G / c**3)  # ~1.616e-35 m


def N_PSU(rayon_m: float) -> float:
    """Nombre d'unités de Planck Sphériques sur une surface sphérique."""
    return 4 * rayon_m**2 / l_P**2


# ==============================================================================
# ENCODEUR : Image → 7 coefficients spectraux
# ==============================================================================
def projeter_harmonique(data: np.ndarray) -> np.ndarray:
    """
    Projette les données sur la base des 7 harmoniques Hₙ.
    
    Pour chaque pixel/valeur x, on cherche les coefficients αₙ tels que :
    x ≈ Σ αₙ · Hₙ
    
    Retourne un tableau 7×... de coefficients spectraux.
    """
    # Normalisation des données
    data_flat = data.flatten().astype(np.float64)
    if data_flat.max() > 0:
        data_norm = data_flat / data_flat.max()
    else:
        data_norm = data_flat
    
    # Projection : pour chaque Hₙ, la corrélation donne le coefficient
    coeffs = np.zeros((7, len(data_flat)), dtype=np.float64)
    for n in range(7):
        # Coefficient spectral pour l'harmonique n
        coeffs[n] = data_norm * H[n] / H.sum()
    
    return coeffs


def compresser_coefficients(coeffs: np.ndarray, bits_par_coeff: int = 16) -> bytes:
    """
    Quantifie les coefficients spectraux et les compresse en bytes.
    
    Au lieu de stocker tous les pixels, on stocke 7 coefficients par pixel,
    quantifiés sur bits_par_coeff bits.
    """
    # Quantification
    max_val = 2**bits_par_coeff - 1
    coeffs_quant = np.round(coeffs * max_val).astype(np.uint16)
    
    # Compression zlib pour réduire encore
    data_bytes = coeffs_quant.tobytes()
    compressed = zlib.compress(data_bytes, level=9)
    
    return compressed


def encoder_image(image_path: str, bits_par_coeff: int = 16) -> Dict:
    """
    Encode une image en utilisant la compression harmono-holographique.
    
    Args:
        image_path: chemin vers l'image
        bits_par_coeff: bits par coefficient spectral (16 = haute qualité)
    
    Returns:
        Dictionnaire avec les données compressées et les métadonnées
    """
    img = Image.open(image_path).convert('L')  # Niveaux de gris
    data = np.array(img, dtype=np.float64)
    hauteur, largeur = data.shape
    
    # Projection harmonique
    coeffs = projeter_harmonique(data)
    
    # Compression
    compressed = compresser_coefficients(coeffs, bits_par_coeff)
    
    # Borne holographique
    diagonale = math.sqrt(largeur**2 + hauteur**2)
    rayon_image_m = diagonale / 2 * 1e-4  # ~0.1mm par pixel
    n_psu = N_PSU(rayon_image_m)
    
    taille_originale = data.nbytes
    taille_compressee = len(compressed)
    ratio = taille_originale / taille_compressee
    
    # Métriques de qualité (PSNR approximatif basé sur la quantification)
    bits_effectifs = bits_par_coeff * 7  # 7 coefficients
    psnr_estime = 6.02 * bits_effectifs / 8 + 1.76  # Formule pour quantification uniforme
    
    return {
        'largeur': largeur,
        'hauteur': hauteur,
        'taille_originale': taille_originale,
        'taille_compressee': taille_compressee,
        'ratio_compression': ratio,
        'bits_par_coeff': bits_par_coeff,
        'coefficients': coeffs,
        'compressed_data': compressed,
        'N_PSU_surface': n_psu,
        'borne_holographique': n_psu / (largeur * hauteur * 8),
        'psnr_estime': psnr_estime,
        'n_harmoniques': 7,
    }


# ==============================================================================
# DÉCODEUR : 7 coefficients spectraux → Image
# ==============================================================================
def decompresser_coefficients(compressed: bytes, shape: Tuple[int, int],
                               bits_par_coeff: int = 16) -> np.ndarray:
    """Décompresse les coefficients spectraux depuis les bytes."""
    data_bytes = zlib.decompress(compressed)
    max_val = 2**bits_par_coeff - 1
    
    n_pixels = shape[0] * shape[1]
    expected_size = 7 * n_pixels * 2  # 7 coeffs × uint16
    
    coeffs_quant = np.frombuffer(data_bytes, dtype=np.uint16)
    coeffs_quant = coeffs_quant[:7 * n_pixels].reshape(7, n_pixels)
    
    coeffs = coeffs_quant.astype(np.float64) / max_val
    return coeffs


def decoder_coefficients(coeffs: np.ndarray, shape: Tuple[int, int]) -> np.ndarray:
    """
    Reconstruit les données à partir des coefficients spectraux.
    
    data_reconstruit ≈ Σ αₙ · Hₙ (dénormalisé)
    """
    hauteur, largeur = shape
    n_pixels = hauteur * largeur
    
    # Reconstruction : somme pondérée des harmoniques
    data_norm = np.zeros(n_pixels, dtype=np.float64)
    for n in range(7):
        data_norm += coeffs[n, :n_pixels] * H[n]
    
    # Dénormalisation : on suppose max=255 pour du 8-bit
    data_reconstruit = data_norm * 255.0 / data_norm.max() if data_norm.max() > 0 else data_norm
    data_reconstruit = np.clip(data_reconstruit, 0, 255).astype(np.uint8)
    
    return data_reconstruit.reshape(hauteur, largeur)


def decoder_image(resultat_encodage: Dict, sauvegarder: Optional[str] = None) -> np.ndarray:
    """
    Décode une image à partir des données compressées.
    
    Args:
        resultat_encodage: dictionnaire retourné par encoder_image()
        sauvegarder: chemin optionnel pour sauvegarder l'image décodée
    
    Returns:
        Array numpy de l'image reconstruite
    """
    shape = (resultat_encodage['hauteur'], resultat_encodage['largeur'])
    coeffs = decompresser_coefficients(
        resultat_encodage['compressed_data'],
        shape,
        resultat_encodage['bits_par_coeff']
    )
    
    img_reconstruite = decoder_coefficients(coeffs, shape)
    
    if sauvegarder:
        Image.fromarray(img_reconstruite).save(sauvegarder)
    
    return img_reconstruite


# ==============================================================================
# BENCHMARK
# ==============================================================================
def benchmark_compression(image_path: str) -> Dict:
    """
    Compare la compression harmono-holographique avec les standards.
    """
    print("=" * 80)
    print("BENCHMARK — Compression Harmono-Holographique")
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
    
    # PNG (compression sans perte standard)
    import io
    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    taille_png = buf.tell()
    
    # JPEG (compression avec perte standard)
    buf_jpg = io.BytesIO()
    img.save(buf_jpg, format='JPEG', quality=85, optimize=True)
    taille_jpg = buf_jpg.tell()
    
    # Notre compression harmonique
    print("  Compression harmono-holographique...")
    for bits in [16, 12, 8, 6, 4]:
        debut = time.time()
        resultat = encoder_image(image_path, bits_par_coeff=bits)
        duree = time.time() - debut
        ratio = resultat['ratio_compression']
        print(f"    {bits:2d} bits/coeff → {resultat['taille_compressee']:>8,} octets "
              f"({ratio:5.1f}:1) en {duree:.3f}s")
    
    print()
    print(f"  Comparaison :")
    print(f"    PNG  (sans perte) : {taille_png:>8,} octets ({taille_originale/taille_png:5.1f}:1)")
    print(f"    JPEG (qualité 85) : {taille_jpg:>8,} octets ({taille_originale/taille_jpg:5.1f}:1)")
    
    # Notre meilleur résultat (12 bits)
    resultat_12 = encoder_image(image_path, bits_par_coeff=12)
    print(f"    HARM (12 bits)    : {resultat_12['taille_compressee']:>8,} octets "
          f"({resultat_12['ratio_compression']:5.1f}:1)")
    
    # Borne holographique
    diagonale = math.sqrt(largeur**2 + hauteur**2)
    rayon = diagonale / 2 * 1e-4
    n_psu = N_PSU(rayon)
    bits_holographiques = n_psu
    ratio_holographique = taille_originale * 8 / bits_holographiques
    
    print()
    print(f"  Borne holographique :")
    print(f"    N_PSU(surface)    = {n_psu:.2e}")
    print(f"    Ratio maximal      = 1 bit par PSU → compression ×{ratio_holographique:.2e}")
    print(f"    Notre ratio actuel = ×{resultat_12['ratio_compression']:.1f}")
    print(f"    Marge restante     = ×{ratio_holographique / resultat_12['ratio_compression']:.2e}")
    print()
    
    # Sauvegarde de l'image décodée
    img_decodee = decoder_image(resultat_12, image_path.replace('.', '_harmonique.'))
    
    # Calcul du PSNR réel
    mse = np.mean((data.astype(np.float64) - img_decodee.astype(np.float64))**2)
    if mse > 0:
        psnr = 20 * math.log10(255.0 / math.sqrt(mse))
    else:
        psnr = float('inf')
    
    print(f"  Qualité (12 bits/coeff) :")
    print(f"    PSNR réel = {psnr:.2f} dB")
    print(f"    PSNR estimé = {resultat_12['psnr_estime']:.2f} dB")
    print()
    
    return {
        'png_ratio': taille_originale / taille_png,
        'jpg_ratio': taille_originale / taille_jpg,
        'harm_ratio': resultat_12['ratio_compression'],
        'harm_psnr': psnr,
        'borne_holographique': ratio_holographique,
        'marge': ratio_holographique / resultat_12['ratio_compression'],
    }


# ==============================================================================
# DÉMONSTRATION
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("COMPRESSION HARMONO-HOLOGRAPHIQUE")
    print("Ψ = Σ Hₙ · fⁿ → Compression par projection spectrale")
    print("=" * 70)
    print()
    print(f"  Coefficients spectraux Hₙ :")
    for i, (nom, val) in enumerate(zip(H_names, H)):
        print(f"    H{i+1} = {nom:<4s} = {val:.6f}")
    print()
    print(f"  l_P = {l_P:.4e} m")
    print(f"  N_PSU(proton) = {N_PSU(0.841e-15):.4e}")
    print()
    
    # Test avec une image de test si fournie en argument
    import sys
    if len(sys.argv) > 1:
        results = benchmark_compression(sys.argv[1])
    else:
        print("  Aucune image fournie. Usage : python compression_harmono_holographique.py image.png")
        print()
        print("  Création d'une image de test synthétique...")
        
        # Créer une image test : dégradé + sinusoïde
        taille = 256
        x = np.linspace(0, 4*pi, taille)
        y = np.linspace(0, 4*pi, taille)
        X, Y = np.meshgrid(x, y)
        
        # Mélange harmonique : φ·sin + π·sin(2x) + e·sin(3x) + ...
        img_test = np.zeros((taille, taille), dtype=np.float64)
        for n, h_n in enumerate(H):
            img_test += h_n * np.sin((n+1) * X) * np.cos((n+1) * Y)
        
        # Normaliser à 0-255
        img_test = (img_test - img_test.min()) / (img_test.max() - img_test.min()) * 255
        img_test = img_test.astype(np.uint8)
        
        test_path = "test_harmonique.png"
        Image.fromarray(img_test).save(test_path)
        print(f"  Image test créée : {test_path}")
        print()
        
        results = benchmark_compression(test_path)
    
    print("=" * 70)
    print("TERMINÉ")
    print("=" * 70)