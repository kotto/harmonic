#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST DIRECT — Compression Holographique HCV PRO
=================================================
Validation de la compression holographique sur des images synthetiques.
Mesure du ratio de compression, PSNR, SSIM, et temps d'encodage/decodage.

Usage :
  python test_hcv_compression.py
"""

import numpy as np
import math, sys, os, time, random, struct, zlib
from typing import Dict, Any, Tuple
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(__file__))
from harmonic_processor import HBit, PHI, PI, E, HARMONIC_CONSTANTS, H_CONSTANT_NAMES

# ==============================================================================
# IMAGES DE TEST
# ==============================================================================

def create_test_images():
    """Cree des images synthetiques pour le test."""
    images = {}
    H, W = 256, 256
    
    # 1. Dégradé
    x = np.linspace(0, 1, W)
    y = np.linspace(0, 1, H)
    X, Y = np.meshgrid(x, y)
    images['degrade'] = (X + Y) / 2
    
    # 2. Cercles concentriques
    cx, cy = W//2, H//2
    R = np.sqrt((X*W - cx)**2 + (Y*H - cy)**2) / W
    images['cercles'] = (np.sin(R * 20) + 1) / 2
    
    # 3. Damier
    damier = np.zeros((H, W))
    for i in range(H):
        for j in range(W):
            damier[i, j] = ((i//16) + (j//16)) % 2
    images['damier'] = damier
    
    # 4. Bruit
    np.random.seed(42)
    images['bruit'] = np.random.rand(H, W)
    
    # 5. Lena-like (sinusoide complexe)
    images['texture'] = (np.sin(X*30) * np.cos(Y*25) + np.sin((X+Y)*15) + 2) / 4
    
    return images


# ==============================================================================
# COMPRESSEUR HOLOGRAPHIQUE HCV (version simplifiee pour validation)
# ==============================================================================

class HCVCompressor:
    """
    Compresseur holographique simplifie pour validation.
    
    Pipeline :
      1. Decouper l'image en blocs 8×8
      2. Pour chaque bloc, calculer les 7 coefficients harmoniques
      3. Quantifier et encoder
      4. Reconstruire par projection holographique inverse
    """
    
    def __init__(self, quality: str = 'high', block_size: int = 8):
        self.quality = quality
        self.block_size = block_size
        
        # Matrice de quantification (facteurs d'echelle par constante)
        if quality == 'lossless':
            self.q_scale = np.ones(7) * 0.5  # Quantification minimale
        elif quality == 'high':
            self.q_scale = np.array([1.0, 1.2, 1.5, 1.0, 1.5, 2.0, 1.0])
        elif quality == 'medium':
            self.q_scale = np.array([2.0, 2.5, 3.0, 2.0, 3.0, 4.0, 2.0])
        else:  # low
            self.q_scale = np.array([4.0, 5.0, 6.0, 4.0, 6.0, 8.0, 4.0])
    
    def _spectral_decompose(self, block: np.ndarray) -> np.ndarray:
        """
        Decomposition spectrale d'un bloc en 7 coefficients harmoniques.
        
        Pour chaque constante H_i, on mesure l'interference cosinus
        entre le bloc et l'onde harmonique correspondante.
        """
        # Aplatir le bloc et le normaliser
        flat = block.flatten().astype(np.float64)
        n = np.linalg.norm(flat)
        if n < 1e-12:
            return np.zeros(7)
        flat = flat / n
        
        coeffs = np.zeros(7)
        # Generer les ondes de reference pour chaque constante
        x = np.linspace(0, 1.0, len(flat))
        for i in range(7):
            freq = HARMONIC_CONSTANTS[i] * PHI
            # Onde harmonique de reference
            wave = np.cos(freq * 2 * PI * x)  # Partie reelle
            wave = wave / (np.linalg.norm(wave) + 1e-12)
            # Coefficient = projection du bloc sur l'onde
            coeffs[i] = np.dot(flat, wave)
        
        return coeffs
    
    def _spectral_reconstruct(self, coeffs: np.ndarray, block_shape: Tuple[int, int]) -> np.ndarray:
        """
        Reconstruction d'un bloc a partir de ses coefficients harmoniques.
        """
        H, W = block_shape
        flat_len = H * W
        x = np.linspace(0, 1.0, flat_len)
        
        reconstructed = np.zeros(flat_len)
        for i in range(7):
            freq = HARMONIC_CONSTANTS[i] * PHI
            wave = np.cos(freq * 2 * PI * x)
            reconstructed += coeffs[i] * wave
        
        # Denormaliser
        n = np.linalg.norm(reconstructed)
        if n > 1e-12:
            reconstructed = reconstructed / n
        
        return reconstructed.reshape(H, W)
    
    def _quantize(self, coeffs: np.ndarray) -> np.ndarray:
        """Quantification des coefficients."""
        return np.round(coeffs / self.q_scale) * self.q_scale
    
    def compress(self, image: np.ndarray) -> Tuple[bytes, Dict[str, Any]]:
        """
        Compresse une image avec HCV PRO.
        
        Retourne (bitstream, metadata).
        """
        H, W = image.shape
        bs = self.block_size
        
        t0 = time.perf_counter()
        
        # Nombre de blocs
        n_blocks_h = H // bs
        n_blocks_w = W // bs
        
        all_coeffs = []
        for i in range(n_blocks_h):
            for j in range(n_blocks_w):
                block = image[i*bs:(i+1)*bs, j*bs:(j+1)*bs]
                coeffs = self._spectral_decompose(block)
                q_coeffs = self._quantize(coeffs)
                all_coeffs.append(q_coeffs)
        
        all_coeffs = np.array(all_coeffs, dtype=np.float32)
        
        # Serialiser les coefficients
        raw_bytes = all_coeffs.tobytes()
        
        # Compression sans perte additionnelle (zlib)
        compressed = zlib.compress(raw_bytes, level=6)
        
        t_enc = time.perf_counter() - t0
        
        # Calculer la taille
        original_size = H * W * 1  # 8 bits par pixel (grayscale)
        compressed_size = len(compressed)
        
        metadata = {
            'shape': (H, W),
            'block_size': bs,
            'n_blocks': (n_blocks_h, n_blocks_w),
            'original_size_bytes': original_size,
            'compressed_size_bytes': compressed_size,
            'ratio': round(original_size / compressed_size, 2),
            'time_encode_ms': round(t_enc * 1000, 2),
            'quality': self.quality,
        }
        
        return compressed, metadata
    
    def decompress(self, bitstream: bytes, metadata: Dict[str, Any]) -> Tuple[np.ndarray, float]:
        """
        Decompresse un flux HCV PRO.
        
        Retourne (image_reconstruite, temps_decodage_ms).
        """
        t0 = time.perf_counter()
        
        H, W = metadata['shape']
        bs = metadata['block_size']
        n_h, n_w = metadata['n_blocks']
        
        # Deserialiser
        raw_bytes = zlib.decompress(bitstream)
        all_coeffs = np.frombuffer(raw_bytes, dtype=np.float32).reshape(-1, 7)
        
        # Reconstruire chaque bloc
        reconstructed = np.zeros((H, W))
        idx = 0
        for i in range(n_h):
            for j in range(n_w):
                coeffs = all_coeffs[idx]
                block = self._spectral_reconstruct(coeffs, (bs, bs))
                reconstructed[i*bs:(i+1)*bs, j*bs:(j+1)*bs] = block
                idx += 1
        
        # Normaliser dans [0, 1]
        r_min, r_max = reconstructed.min(), reconstructed.max()
        if r_max - r_min > 1e-12:
            reconstructed = (reconstructed - r_min) / (r_max - r_min)
        
        t_dec = time.perf_counter() - t0
        
        return reconstructed, round(t_dec * 1000, 2)


# ==============================================================================
# METRIQUES
# ==============================================================================

def compute_psnr(original: np.ndarray, compressed: np.ndarray) -> float:
    """Calcule le PSNR entre l'original et le compresse."""
    # Normaliser les deux images dans [0, 1]
    o = (original - original.min()) / (original.max() - original.min() + 1e-12)
    c = (compressed - compressed.min()) / (compressed.max() - compressed.min() + 1e-12)
    
    mse = np.mean((o - c) ** 2)
    if mse < 1e-12:
        return float('inf')
    return round(20 * math.log10(1.0 / math.sqrt(mse)), 2)


def compute_ssim(original: np.ndarray, compressed: np.ndarray) -> float:
    """Calcule le SSIM simplifie entre l'original et le compresse."""
    o = (original - original.min()) / (original.max() - original.min() + 1e-12)
    c = (compressed - compressed.min()) / (compressed.max() - compressed.min() + 1e-12)
    
    mu_o = np.mean(o)
    mu_c = np.mean(c)
    sigma_o = np.var(o)
    sigma_c = np.var(c)
    sigma_oc = np.mean((o - mu_o) * (c - mu_c))
    
    C1 = (0.01) ** 2
    C2 = (0.03) ** 2
    
    ssim = ((2 * mu_o * mu_c + C1) * (2 * sigma_oc + C2)) / \
           ((mu_o**2 + mu_c**2 + C1) * (sigma_o + sigma_c + C2))
    
    return round(ssim, 4)


# ==============================================================================
# DEMONSTRATION
# ==============================================================================

def run_tests():
    print("=" * 70)
    print("  TEST DIRECT — Compression Holographique HCV PRO")
    print("  Validation sur 5 images synthetiques (256x256)")
    print("=" * 70)
    
    images = create_test_images()
    
    # Tester en qualite 'high' et 'medium'
    for quality in ['high', 'medium', 'low']:
        print(f"\n  {'='*60}")
        print(f"  QUALITE : {quality.upper()}")
        print(f"  {'='*60}")
        
        compressor = HCVCompressor(quality=quality, block_size=8)
        
        results = []
        for name, img in images.items():
            bitstream, meta = compressor.compress(img)
            reconstructed, t_dec = compressor.decompress(bitstream, meta)
            psnr = compute_psnr(img, reconstructed)
            ssim = compute_ssim(img, reconstructed)
            
            results.append({
                'image': name,
                'ratio': meta['ratio'],
                'psnr': psnr,
                'ssim': ssim,
                't_enc_ms': meta['time_encode_ms'],
                't_dec_ms': t_dec,
                'orig_bytes': meta['original_size_bytes'],
                'comp_bytes': meta['compressed_size_bytes'],
            })
        
        # Tableau
        print(f"\n  {'Image':<12s} {'Ratio':>7s} {'PSNR':>8s} {'SSIM':>8s} {'T.Enc(ms)':>10s} {'T.Dec(ms)':>10s} {'Orig':>8s} {'Comp':>8s}")
        print(f"  {'-'*12} {'-'*7} {'-'*8} {'-'*8} {'-'*10} {'-'*10} {'-'*8} {'-'*8}")
        
        total_ratio = 0
        total_psnr = 0
        for r in results:
            if r['psnr'] == float('inf'):
                psnr_str = 'INF'
            else:
                psnr_str = f"{r['psnr']} dB"
            print(f"  {r['image']:<12s} {r['ratio']:7.2f}x {psnr_str:>8s} {r['ssim']:8.4f} {r['t_enc_ms']:10.2f} {r['t_dec_ms']:10.2f} {r['orig_bytes']:>8d} {r['comp_bytes']:>8d}")
            total_ratio += r['ratio']
            total_psnr += r['psnr'] if r['psnr'] != float('inf') else 99
        
        avg_ratio = total_ratio / len(results)
        avg_psnr = total_psnr / len(results)
        
        print(f"  {'-'*12} {'-'*7} {'-'*8} {'-'*8} {'-'*10} {'-'*10} {'-'*8} {'-'*8}")
        print(f"  {'MOYENNE':<12s} {avg_ratio:7.2f}x {avg_psnr:8.2f} dB")
    
    # Test special : compression lossless (haute qualite extreme)
    print(f"\n  {'='*60}")
    print(f"  TEST SPECIAL : Bloc unique (1x1 bloc = image entiere)")
    print(f"  {'='*60}")
    
    big_block_compressor = HCVCompressor(quality='lossless', block_size=256)
    
    for name, img in images.items():
        # Redimensionner a 256x256 si necessaire
        if img.shape != (256, 256):
            continue
        bitstream, meta = big_block_compressor.compress(img)
        reconstructed, t_dec = big_block_compressor.decompress(bitstream, meta)
        psnr = compute_psnr(img, reconstructed)
        print(f"  {name:<12s} : Ratio {meta['ratio']:.1f}x, PSNR {psnr} dB, Taille {meta['original_size_bytes']}->{meta['compressed_size_bytes']} octets")


if __name__ == "__main__":
    run_tests()