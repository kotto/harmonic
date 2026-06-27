#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compression Harmono-Holographique V2
=====================================
Améliorations vs V1 :
1. Coefficients GLOBAUX (7 pour l'image entière) au lieu de 7 par pixel
2. Transformée harmonique (DCT-like avec base {φ,π,e,√2,√3,√5,e/π})
3. Quantificateur holographique adaptatif basé sur N_PSU

Principe : Ψ = Σ Hₙ · fⁿ
Chaque image est une cavité résonante. Les 7 harmoniques encodent
toute sa structure. Le nombre de bits alloués dépend de N_PSU.

Auteur : KOTTO Alain — 19 Juin 2026 (V2)
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

c = 299792458.0
hbar = 6.62607015e-34 / (2 * pi)
G = 6.67430e-11
l_P = math.sqrt(hbar * G / c**3)


def N_PSU(rayon_m: float) -> float:
    return 4 * rayon_m**2 / l_P**2


# ==============================================================================
# AMÉLIORATION 1 : COEFFICIENTS GLOBAUX
# ==============================================================================
def transformer_harmonique(data: np.ndarray) -> np.ndarray:
    """
    Transformée harmonique globale.
    
    Au lieu de 7 coefficients par pixel (comme la V1), on extrait
    7 coefficients pour l'IMAGE ENTIÈRE — comme un spectre musical.
    
    La transformée projette l'image sur 7 "notes" harmoniques.
    Chaque note est une matrice de la taille de l'image, dont les
    valeurs sont les H_n multipliées par une phase spatiale.
    
    Returns:
        Array de forme (7,) — 7 coefficients spectraux globaux
    """
    hauteur, largeur = data.shape
    data_norm = data.astype(np.float64) / 255.0  # Normaliser à [0,1]
    
    # Fréquence fondamentale de l'image (cavité)
    diagonale = math.sqrt(largeur**2 + hauteur**2)
    rayon = diagonale / 2
    f0 = 1.0 / rayon  # Fréquence spatiale fondamentale
    
    # Pour chaque harmonique, créer un motif spatial et calculer la corrélation
    y, x = np.ogrid[:hauteur, :largeur]
    centre_y, centre_x = hauteur / 2, largeur / 2
    r = np.sqrt((x - centre_x)**2 + (y - centre_y)**2)  # Distance au centre
    theta = np.arctan2(y - centre_y, x - centre_x)
    
    coeffs_globaux = np.zeros(7, dtype=np.float64)
    
    for n in range(7):
        # Motif harmonique : H_n module une onde spatiale de fréquence (n+1)·f0
        motif = H[n] * np.cos((n+1) * f0 * r) * np.cos((n+1) * theta)
        motif_norm = motif / (np.abs(motif).max() + 1e-10)
        
        # Coefficient = corrélation entre l'image normalisée et le motif
        coeffs_globaux[n] = np.sum(data_norm * motif_norm) / (hauteur * largeur)
    
    return coeffs_globaux


def transformer_harmonique_inverse(coeffs_globaux: np.ndarray, shape: Tuple[int, int]) -> np.ndarray:
    """
    Transformée harmonique inverse.
    
    Reconstruit l'image à partir des 7 coefficients spectraux globaux.
    Ψ = Σ Hₙ · fⁿ → Image = Σ coeff[n] · motif[n]
    """
    hauteur, largeur = shape
    diagonale = math.sqrt(largeur**2 + hauteur**2)
    rayon = diagonale / 2
    f0 = 1.0 / rayon
    
    y, x = np.ogrid[:hauteur, :largeur]
    centre_y, centre_x = hauteur / 2, largeur / 2
    r = np.sqrt((x - centre_x)**2 + (y - centre_y)**2)
    theta = np.arctan2(y - centre_y, x - centre_x)
    
    reconstruction = np.zeros((hauteur, largeur), dtype=np.float64)
    
    for n in range(7):
        motif = H[n] * np.cos((n+1) * f0 * r) * np.cos((n+1) * theta)
        motif_norm = motif / (np.abs(motif).max() + 1e-10)
        reconstruction += coeffs_globaux[n] * motif_norm
    
    # Normaliser à [0,255]
    recon_min = reconstruction.min()
    recon_max = reconstruction.max()
    if recon_max > recon_min:
        reconstruction = (reconstruction - recon_min) / (recon_max - recon_min) * 255.0
    reconstruction = np.clip(reconstruction, 0, 255).astype(np.uint8)
    
    return reconstruction


# ==============================================================================
# AMÉLIORATION 2 : QUANTIFICATEUR HOLOGRAPHIQUE ADAPTATIF
# ==============================================================================
def quantifier_holographique(coeffs: np.ndarray, n_psu: float,
                              bits_max: int = 16, bits_min: int = 4) -> Tuple[np.ndarray, int]:
    """
    Quantifie les coefficients en fonction du N_PSU de l'image.
    
    Principe : plus N_PSU est grand, plus on peut allouer de bits par coefficient.
    C'est l'équivalent de la quantification adaptative JPEG, mais basée sur
    le principe holographique.
    
    Args:
        coeffs: coefficients spectraux globaux (7,)
        n_psu: nombre d'unités de Planck Sphériques sur la surface de l'image
        bits_max: bits maximum par coefficient
        bits_min: bits minimum par coefficient
    
    Returns:
        Coefficients quantifiés et nombre de bits utilisés
    """
    # Bits alloués proportionnellement à log_phi(N_PSU)
    # Pour le proton : N≈10^40 → log_phi≈191 → bits≈16
    # Pour une image 256×256 : N≈10^66 → log_phi≈318 → bits≈16 (max)
    log_n = math.log(n_psu) / math.log(phi)  # log_phi(N_PSU)
    
    # Mapping : log_n ∈ [0, 600] → bits ∈ [bits_min, bits_max]
    log_min = 100   # N_PSU minimal (~10^48, cavité microscopique)
    log_max = 600   # N_PSU maximal (~10^288, univers)
    
    bits = int(bits_min + (bits_max - bits_min) * (log_n - log_min) / (log_max - log_min))
    bits = max(bits_min, min(bits_max, bits))
    
    # Quantification
    max_val = 2**bits - 1
    coeffs_norm = (coeffs - coeffs.min()) / (coeffs.max() - coeffs.min() + 1e-10)
    coeffs_quant = np.round(coeffs_norm * max_val).astype(np.uint16)
    
    return coeffs_quant, bits


def dequantifier_holographique(coeffs_quant: np.ndarray, bits: int,
                                coeffs_min: float, coeffs_max: float) -> np.ndarray:
    """Déquantifie les coefficients."""
    max_val = 2**bits - 1
    coeffs_norm = coeffs_quant.astype(np.float64) / max_val
    coeffs = coeffs_norm * (coeffs_max - coeffs_min) + coeffs_min
    return coeffs


# ==============================================================================
# ENCODEUR V2
# ==============================================================================
def encoder_image_v2(image_path: str) -> Dict:
    """
    Encode une image avec les 3 améliorations :
    1. Coefficients globaux (7 pour l'image entière)
    2. Transformée harmonique
    3. Quantificateur holographique adaptatif
    """
    img = Image.open(image_path).convert('L')
    data = np.array(img, dtype=np.float64)
    hauteur, largeur = data.shape
    
    # Calcul de N_PSU
    diagonale = math.sqrt(largeur**2 + hauteur**2)
    rayon_m = diagonale / 2 * 1e-4
    n_psu = N_PSU(rayon_m)
    
    # 1+2. Transformée harmonique → 7 coefficients globaux
    coeffs_globaux = transformer_harmonique(data)
    
    # 3. Quantification holographique adaptative
    coeffs_quant, bits = quantifier_holographique(coeffs_globaux, n_psu)
    coeffs_min = coeffs_globaux.min()
    coeffs_max = coeffs_globaux.max()
    
    # Encodage compact
    # Format : [largeur:2, hauteur:2, bits:1, coeff_min:8, coeff_max:8, log10_n_psu:8, 7×uint16]
    log10_n_psu = math.log10(n_psu) if n_psu > 0 else 0.0
    header = struct.pack('>HHBddd', largeur, hauteur, bits, coeffs_min, coeffs_max, log10_n_psu)
    body = coeffs_quant.tobytes()
    compressed = zlib.compress(header + body, level=9)
    
    taille_originale = data.nbytes
    taille_compressee = len(compressed)
    ratio = taille_originale / taille_compressee
    
    # Métadonnées pour le décodeur
    return {
        'largeur': largeur,
        'hauteur': hauteur,
        'taille_originale': taille_originale,
        'taille_compressee': taille_compressee,
        'ratio_compression': ratio,
        'bits_utilises': bits,
        'coeffs_globaux': coeffs_globaux,
        'coeffs_quant': coeffs_quant,
        'coeffs_min': coeffs_min,
        'coeffs_max': coeffs_max,
        'compressed_data': compressed,
        'N_PSU_surface': n_psu,
        'n_harmoniques': 7,
    }


# ==============================================================================
# DÉCODEUR V2
# ==============================================================================
def decoder_image_v2(resultat_encodage: Dict, sauvegarder: Optional[str] = None) -> np.ndarray:
    """
    Décode une image à partir des données compressées V2.
    """
    compressed = resultat_encodage['compressed_data']
    data_bytes = zlib.decompress(compressed)
    
    # Décodage du header
    header_size = 2 + 2 + 1 + 8 + 8 + 8  # largeur, hauteur, bits, min, max, log10_n_psu
    header = data_bytes[:header_size]
    largeur, hauteur, bits = struct.unpack('>HHB', header[:5])
    coeffs_min, coeffs_max, _ = struct.unpack('>ddd', header[5:header_size])
    
    # Décodage des coefficients
    coeffs_quant = np.frombuffer(data_bytes[header_size:], dtype=np.uint16)
    coeffs_quant = coeffs_quant[:7]
    
    # Déquantification
    coeffs = dequantifier_holographique(coeffs_quant, bits, coeffs_min, coeffs_max)
    
    # Transformée inverse
    img_reconstruite = transformer_harmonique_inverse(coeffs, (hauteur, largeur))
    
    if sauvegarder:
        Image.fromarray(img_reconstruite).save(sauvegarder)
    
    return img_reconstruite


# ==============================================================================
# BENCHMARK V2
# ==============================================================================
def benchmark_compression_v2(image_path: str) -> Dict:
    """
    Benchmark de la compression V2 vs standards.
    """
    print("=" * 80)
    print("BENCHMARK V2 — Compression Harmono-Holographique")
    print("7 coefficients GLOBAUX + Transformée Harmonique + Quantif. Holographique")
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
    
    # PNG
    import io
    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    taille_png = buf.tell()
    
    # JPEG
    buf_jpg = io.BytesIO()
    img.save(buf_jpg, format='JPEG', quality=85, optimize=True)
    taille_jpg = buf_jpg.tell()
    
    # Notre compression V2
    print("  Compression V2 (7 coeffs globaux)...")
    debut = time.time()
    resultat = encoder_image_v2(image_path)
    duree = time.time() - debut
    
    print(f"    Bits utilisés      : {resultat['bits_utilises']}")
    print(f"    Taille compressée  : {resultat['taille_compressee']:,} octets "
          f"({resultat['ratio_compression']:.1f}:1) en {duree:.3f}s")
    print(f"    N_PSU(surface)     : {resultat['N_PSU_surface']:.2e}")
    print(f"    7 coeffs globaux   : {resultat['coeffs_globaux']}")
    print()
    
    print(f"  Comparaison :")
    print(f"    PNG  (sans perte) : {taille_png:>8,} octets ({taille_originale/taille_png:5.1f}:1)")
    print(f"    JPEG (qualité 85) : {taille_jpg:>8,} octets ({taille_originale/taille_jpg:5.1f}:1)")
    print(f"    HARM V2           : {resultat['taille_compressee']:>8,} octets "
          f"({resultat['ratio_compression']:5.1f}:1)")
    
    # Sauvegarde et PSNR
    img_decodee = decoder_image_v2(resultat, image_path.replace('.', '_harmonique_v2.'))
    mse = np.mean((data.astype(np.float64) - img_decodee.astype(np.float64))**2)
    psnr = 20 * math.log10(255.0 / math.sqrt(mse)) if mse > 0 else float('inf')
    
    print()
    print(f"  Qualité :")
    print(f"    PSNR = {psnr:.2f} dB")
    
    # Ratio de compression par harmonique (combien de bytes par coeff)
    bytes_par_coeff = resultat['taille_compressee'] / 7
    print(f"    Bytes par coeff    = {bytes_par_coeff:.1f}")
    print(f"    Bits par coeff     = {bytes_par_coeff * 8:.1f}")
    print()
    
    # Vérification : les 7 coeffs pèsent ~100 octets, le reste est le header
    taille_header_estimee = 2 + 2 + 1 + 8 + 8 + 8  # 29 octets
    taille_payload = resultat['taille_compressee'] - taille_header_estimee
    print(f"    Taille header      ≈ {taille_header_estimee} octets")
    print(f"    Taille payload     ≈ {taille_payload} octets")
    print()
    
    return {
        'png_ratio': taille_originale / taille_png,
        'jpg_ratio': taille_originale / taille_jpg,
        'harm_v2_ratio': resultat['ratio_compression'],
        'harm_v2_psnr': psnr,
        'bits_utilises': resultat['bits_utilises'],
        'coeffs_globaux': resultat['coeffs_globaux'],
        'taille_compressee': resultat['taille_compressee'],
    }


# ==============================================================================
# DÉMONSTRATION
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("COMPRESSION HARMONO-HOLOGRAPHIQUE V2")
    print("3 améliorations : global, transformée, quantif. adaptative")
    print("=" * 70)
    print()
    print(f"  Coefficients spectraux Hₙ :")
    for i, (nom, val) in enumerate(zip(H_names, H)):
        print(f"    H{i+1} = {nom:<4s} = {val:.6f}")
    print()
    
    import sys
    if len(sys.argv) > 1:
        results = benchmark_compression_v2(sys.argv[1])
    else:
        print("  Création d'une image de test synthétique...")
        
        taille = 256
        x = np.linspace(0, 4*pi, taille)
        y = np.linspace(0, 4*pi, taille)
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
        
        results = benchmark_compression_v2(test_path)
    
    print("=" * 70)
    print("TERMINÉ")
    print("=" * 70)