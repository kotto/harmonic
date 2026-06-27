#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST DIRECT V2 — Compression Holographique HCV PRO avec Hologramme SVD
======================================================================
V2 amelioree : remplace les 7 ondes generiques par un hologramme
adaptatif entraine par SVD sur les blocs de l'image elle-meme.

Pipeline :
  1. Decouper l'image en blocs 8×8
  2. Construire la matrice de tous les blocs (N_blocs × 64)
  3. SVD → les K premieres composantes = l'hologramme (matrice K×64)
  4. Chaque bloc = K coefficients (projection sur l'hologramme)
  5. Ratio = 64/K (avant quantification/zlib)

Parametres testes :
  - K=8  (high)    → ratio ~8:1  brut
  - K=4  (medium)  → ratio ~16:1 brut
  - K=2  (low)     → ratio ~32:1 brut
  - K=32 (lossless)→ ratio ~2:1  brut

Usage :
  python test_hcv_compression_v2.py
"""

import numpy as np
import math, sys, os, time, struct, zlib
from typing import Dict, Any, Tuple, Optional

sys.path.insert(0, os.path.dirname(__file__))
from harmonic_processor import HBit, PHI, PI, E, HARMONIC_CONSTANTS, H_CONSTANT_NAMES


# ==============================================================================
# IMAGES DE TEST (identiques V1 pour comparaison)
# ==============================================================================

def create_test_images():
    """Cree des images synthetiques pour le test."""
    images = {}
    H, W = 256, 256

    # 1. Degrade
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

    # 5. Texture (sinusoide complexe)
    images['texture'] = (np.sin(X*30) * np.cos(Y*25) + np.sin((X+Y)*15) + 2) / 4

    # 6. Lena-like via superposition de gaussiennes (plus realiste)
    np.random.seed(123)
    lena = np.zeros((H, W))
    for _ in range(40):
        cx_ = np.random.uniform(0.15, 0.85) * W
        cy_ = np.random.uniform(0.15, 0.85) * H
        sx = np.random.uniform(20, 60)
        sy = np.random.uniform(20, 60)
        amp = np.random.uniform(0.3, 1.0)
        gauss = amp * np.exp(-((X*W - cx_)**2 / (2*sx**2) + (Y*H - cy_)**2 / (2*sy**2)))
        lena += gauss
    lena = (lena - lena.min()) / (lena.max() - lena.min() + 1e-12)
    images['gaussienne'] = lena

    return images


# ==============================================================================
# COMPRESSEUR HOLOGRAPHIQUE V2 — Hologramme adaptatif SVD
# ==============================================================================

class HCVCompressorV2:
    """
    Compresseur holographique V2 avec hologramme adaptatif SVD.

    Au lieu d'utiliser 7 ondes harmoniques generiques, on apprend
    un hologramme specifique a l'image par decomposition SVD de
    l'ensemble des blocs 8x8.

    L'hologramme = les K premieres composantes principales (K vecteurs
    propres de la covariance des blocs), qui forment une base optimale
    au sens de l'energie (minimise l'erreur de reconstruction L2).

    Parametres :
      - K : nombre de composantes de l'hologramme
        K=8  → haute qualite (ratio brut ~8:1)
        K=4  → qualite moyenne (ratio brut ~16:1)
        K=2  → basse qualite (ratio brut ~32:1)
        K=32 → quasi lossless (ratio brut ~2:1)
    """

    def __init__(self, K: int = 8, block_size: int = 8, quantize_bits: int = 16):
        self.K = K                      # Nombre de composantes holographiques
        self.block_size = block_size    # Taille des blocs (8x8 = 64 pixels)
        self.quantize_bits = quantize_bits  # Bits de quantification des coeffs
        self.dim = block_size * block_size  # 64

        # Hologramme (appris par SVD)
        self.hologram: Optional[np.ndarray] = None  # (K, 64)
        self.block_mean: Optional[float] = None
        self.block_std: Optional[float] = None

    def _train_hologram(self, image: np.ndarray) -> None:
        """
        Apprend l'hologramme adaptatif par SVD sur tous les blocs de l'image.

        Etape 1 : Decouper l'image en blocs 8x8
        Etape 2 : Centrer-reduire les blocs
        Etape 3 : SVD → les K premieres colonnes de V^T sont l'hologramme
        """
        H, W = image.shape
        bs = self.block_size

        n_h = H // bs
        n_w = W // bs

        # Etape 1 : Extraire tous les blocs
        blocks = []
        for i in range(n_h):
            for j in range(n_w):
                block = image[i*bs:(i+1)*bs, j*bs:(j+1)*bs].flatten().astype(np.float64)
                blocks.append(block)

        blocks = np.array(blocks)  # (N_blocs, 64)

        # Protection NaN/Inf
        blocks = np.nan_to_num(blocks, nan=0.0, posinf=1.0, neginf=0.0)
        blocks = np.clip(blocks, 0.0, 1.0)

        # Etape 2 : Centrer-reduire
        self.block_mean = float(np.mean(blocks))
        self.block_std = float(np.std(blocks)) + 1e-12
        blocks_centered = (blocks - self.block_mean) / self.block_std

        # Etape 3 : SVD
        # U : (N_blocs, N_blocs), S : (min(N_blocs,64),), Vt : (64, 64)
        # Vt contient les composantes principales (vecteurs propres de covariance)
        try:
            U, S, Vt = np.linalg.svd(blocks_centered, full_matrices=False)
        except np.linalg.LinAlgError:
            # Fallback : utiliser une base DCT (cosinus discrets) si SVD echoue
            Vt = np.zeros((64, 64))
            for k in range(64):
                Vt[k] = np.cos((k + 1) * np.pi * np.arange(64) / 64)
                Vt[k] /= np.linalg.norm(Vt[k]) + 1e-12
            S = np.ones(64)

        # L'hologramme = les K premieres lignes de Vt (K, 64)
        self.hologram = Vt[:self.K, :].copy()

        # Normaliser chaque vecteur de l'hologramme
        for k in range(self.K):
            n = np.linalg.norm(self.hologram[k])
            if n > 1e-12:
                self.hologram[k] /= n

        # Energie preservee par les K composantes
        total_energy = np.sum(S ** 2)
        preserved_energy = np.sum(S[:self.K] ** 2)
        self.energy_ratio = float(preserved_energy / total_energy) if total_energy > 1e-12 else 1.0

    def _encode_block(self, block_flat: np.ndarray) -> np.ndarray:
        """
        Encode un bloc → K coefficients par projection sur l'hologramme.
        """
        centered = (block_flat - self.block_mean) / self.block_std
        coeffs = np.dot(self.hologram, centered)  # (K,)
        return coeffs

    def _decode_block(self, coeffs: np.ndarray) -> np.ndarray:
        """
        Decode K coefficients → bloc 64 pixels.
        Reconstruction = moyenne + std * (coeffs @ hologram)
        """
        centered = np.dot(coeffs, self.hologram)  # (64,)
        block = centered * self.block_std + self.block_mean
        return block.reshape(self.block_size, self.block_size)

    def _quantize_coeffs(self, coeffs: np.ndarray) -> np.ndarray:
        """
        Quantifie les coefficients en entiers sur quantize_bits bits.
        """
        # Trouver les bornes par bloc ou globalement
        c_min = coeffs.min()
        c_max = coeffs.max()
        if c_max - c_min < 1e-12:
            return np.zeros_like(coeffs)

        levels = 2 ** self.quantize_bits
        # Quantification uniforme
        quantized = np.round((coeffs - c_min) / (c_max - c_min) * (levels - 1))
        # Dequantification
        dequantized = quantized / (levels - 1) * (c_max - c_min) + c_min
        return dequantized.astype(np.float64)

    def compress(self, image: np.ndarray) -> Tuple[bytes, Dict[str, Any]]:
        """
        Compresse une image avec HCV PRO V2 (SVD adaptatif).

        Retourne (bitstream, metadata).
        """
        H, W = image.shape
        bs = self.block_size

        t0 = time.perf_counter()

        # Etape 1 : Apprendre l'hologramme par SVD
        t_train_start = time.perf_counter()
        self._train_hologram(image)
        t_train = time.perf_counter() - t_train_start

        # Etape 2 : Encoder chaque bloc
        n_h = H // bs
        n_w = W // bs
        all_coeffs = []
        for i in range(n_h):
            for j in range(n_w):
                block = image[i*bs:(i+1)*bs, j*bs:(j+1)*bs].flatten().astype(np.float64)
                coeffs = self._encode_block(block)
                q_coeffs = self._quantize_coeffs(coeffs)
                all_coeffs.append(q_coeffs)

        all_coeffs = np.array(all_coeffs, dtype=np.float32)  # (N_blocs, K)

        # Etape 3 : Serialiser
        # On sauvegarde : hologram (K*64 float32), block_mean (float32), block_std (float32),
        #               all_coeffs (N_blocs*K float32)
        header = np.concatenate([
            self.hologram.flatten().astype(np.float32),       # K*64
            np.array([self.block_mean], dtype=np.float32),    # 1
            np.array([self.block_std], dtype=np.float32),     # 1
            np.array([n_h, n_w], dtype=np.float32),           # 2 (shape info)
        ])
        payload = all_coeffs.flatten().astype(np.float32)

        # zlib sur l'ensemble
        raw_bytes = header.tobytes() + payload.tobytes()
        compressed = zlib.compress(raw_bytes, level=6)

        t_enc = time.perf_counter() - t0

        original_size = H * W  # 8 bits par pixel grayscale
        compressed_size = len(compressed)

        # Ratio brut = 64/K (nombre de pixels par bloc / nombre de coeffs)
        ratio_brut = 64.0 / self.K

        metadata = {
            'shape': (H, W),
            'block_size': bs,
            'K': self.K,
            'n_blocks': (n_h, n_w),
            'energy_preserved': round(self.energy_ratio * 100, 2),
            'original_size_bytes': original_size,
            'compressed_size_bytes': compressed_size,
            'ratio_brut': round(ratio_brut, 2),
            'ratio_effectif': round(original_size / compressed_size, 2),
            'time_train_ms': round(t_train * 1000, 2),
            'time_encode_ms': round(t_enc * 1000, 2),
            'quantize_bits': self.quantize_bits,
        }

        return compressed, metadata

    def decompress(self, bitstream: bytes, metadata: Dict[str, Any]) -> Tuple[np.ndarray, float]:
        """
        Decompresse un flux HCV PRO V2.

        Retourne (image_reconstruite, temps_decodage_ms).
        """
        t0 = time.perf_counter()

        K = metadata['K']
        bs = metadata['block_size']
        n_h, n_w = metadata['n_blocks']
        H, W = metadata['shape']

        # Deserialiser
        raw_bytes = zlib.decompress(bitstream)

        # Header : hologram (K*64) + mean + std + shape
        hologram_size = K * 64
        header_floats = np.frombuffer(raw_bytes[:hologram_size * 4], dtype=np.float32)
        self.hologram = header_floats.reshape(K, 64)

        offset = hologram_size * 4
        self.block_mean = float(np.frombuffer(raw_bytes[offset:offset+4], dtype=np.float32)[0])
        offset += 4
        self.block_std = float(np.frombuffer(raw_bytes[offset:offset+4], dtype=np.float32)[0])
        offset += 4
        # Skip n_h, n_w (deja dans metadata)
        offset += 8

        # Payload : coefficients
        coeffs_floats = np.frombuffer(raw_bytes[offset:], dtype=np.float32)
        all_coeffs = coeffs_floats.reshape(-1, K)

        # Reconstruire chaque bloc
        reconstructed = np.zeros((H, W))
        idx = 0
        for i in range(n_h):
            for j in range(n_w):
                coeffs = all_coeffs[idx]
                block = self._decode_block(coeffs)
                reconstructed[i*bs:(i+1)*bs, j*bs:(j+1)*bs] = block
                idx += 1

        # Clamper dans [0, 1]
        reconstructed = np.clip(reconstructed, 0, 1)

        t_dec = time.perf_counter() - t0

        return reconstructed, round(t_dec * 1000, 2)


# ==============================================================================
# METRIQUES
# ==============================================================================

def compute_psnr(original: np.ndarray, compressed: np.ndarray) -> float:
    """Calcule le PSNR entre l'original et le compresse."""
    o = original.astype(np.float64)
    c = compressed.astype(np.float64)

    # Normaliser dans [0, 1]
    o_min, o_max = o.min(), o.max()
    c_min, c_max = c.min(), c.max()
    if o_max - o_min > 1e-12:
        o = (o - o_min) / (o_max - o_min)
    if c_max - c_min > 1e-12:
        c = (c - c_min) / (c_max - c_min)

    mse = np.mean((o - c) ** 2)
    if mse < 1e-12:
        return float('inf')
    return round(20 * math.log10(1.0 / math.sqrt(mse)), 2)


def compute_ssim(original: np.ndarray, compressed: np.ndarray) -> float:
    """Calcule le SSIM simplifie entre l'original et le compresse."""
    o = original.astype(np.float64)
    c = compressed.astype(np.float64)

    o_min, o_max = o.min(), o.max()
    c_min, c_max = c.min(), c.max()
    if o_max - o_min > 1e-12:
        o = (o - o_min) / (o_max - o_min)
    if c_max - c_min > 1e-12:
        c = (c - c_min) / (c_max - c_min)

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
    print("=" * 75)
    print("  TEST DIRECT V2 — Compression Holographique HCV PRO (SVD Adaptatif)")
    print("  Hologramme appris par SVD sur les blocs 8x8 de l'image")
    print("=" * 75)

    images = create_test_images()
    qualites = [
        ('K=32 (quasi-lossless)', 32),
        ('K=8  (high)', 8),
        ('K=4  (medium)', 4),
        ('K=2  (low)', 2),
    ]

    all_summary = []

    for qual_name, K in qualites:
        print(f"\n  {'='*65}")
        print(f"  HOLOGRAMME : {qual_name} — Ratio brut = 64/{K} = {64/K:.1f}:1")
        print(f"  {'='*65}")

        compressor = HCVCompressorV2(K=K, block_size=8, quantize_bits=16)
        results = []

        for name, img in images.items():
            bitstream, meta = compressor.compress(img)
            reconstructed, t_dec = compressor.decompress(bitstream, meta)
            psnr = compute_psnr(img, reconstructed)
            ssim = compute_ssim(img, reconstructed)

            results.append({
                'image': name,
                'ratio_brut': meta['ratio_brut'],
                'ratio_eff': meta['ratio_effectif'],
                'psnr': psnr,
                'ssim': ssim,
                't_train_ms': meta['time_train_ms'],
                't_enc_ms': meta['time_encode_ms'],
                't_dec_ms': t_dec,
                'energy': meta['energy_preserved'],
                'orig_bytes': meta['original_size_bytes'],
                'comp_bytes': meta['compressed_size_bytes'],
            })

        # Tableau
        header_fmt = f"  {'Image':<12s} {'Ratio eff':>9s} {'PSNR':>9s} {'SSIM':>8s} {'Energie':>8s} {'T.Enc(ms)':>10s} {'T.Dec(ms)':>10s}"
        sep = f"  {'-'*12} {'-'*9} {'-'*9} {'-'*8} {'-'*8} {'-'*10} {'-'*10}"
        print(f"\n{header_fmt}")
        print(sep)

        for r in results:
            psnr_str = f"{r['psnr']} dB" if r['psnr'] != float('inf') else 'INF'
            print(f"  {r['image']:<12s} {r['ratio_eff']:8.2f}x {psnr_str:>9s} {r['ssim']:8.4f} {r['energy']:7.1f}% {r['t_enc_ms']:10.2f} {r['t_dec_ms']:10.2f}")

        # Moyennes
        avg_ratio = sum(r['ratio_eff'] for r in results) / len(results)
        avg_psnr_vals = [r['psnr'] for r in results if r['psnr'] != float('inf')]
        avg_psnr = sum(avg_psnr_vals) / len(avg_psnr_vals) if avg_psnr_vals else 0
        avg_energy = sum(r['energy'] for r in results) / len(results)

        print(sep)
        print(f"  {'MOYENNE':<12s} {avg_ratio:8.2f}x {avg_psnr:8.2f} dB {avg_energy:7.1f}%")

        all_summary.append({
            'K': K,
            'qual_name': qual_name,
            'avg_ratio': avg_ratio,
            'avg_psnr': avg_psnr,
            'avg_energy': avg_energy,
            'ratio_brut': 64/K,
        })

    # Resume comparatif final
    print(f"\n\n{'='*75}")
    print("  RESUME COMPARATIF V2 (SVD) vs V1 (7 ondes generiques)")
    print(f"  {'='*75}")
    print(f"\n  {'Qualite':<25s} {'Ratio eff':>9s} {'PSNR':>9s} {'Energie':>8s} {'vs V1 PSNR':>12s}")
    print(f"  {'-'*25} {'-'*9} {'-'*9} {'-'*8} {'-'*12}")
    # V1 reference values from context: ~4.5 dB with ratio 271x
    for s in all_summary:
        v1_ref = "~4.5 dB (V1)"
        print(f"  {s['qual_name']:<25s} {s['avg_ratio']:8.2f}x {s['avg_psnr']:8.2f} dB {s['avg_energy']:7.1f}% {v1_ref:>12s}")

    print(f"\n  {'='*75}")
    print("  CONCLUSION")
    print(f"  {'='*75}")
    print(f"  La V2 (SVD adaptatif) apprend un hologramme specifique a chaque image.")
    print(f"  Les K composantes principales capturent la structure des blocs bien mieux")
    print(f"  que 7 ondes generiques. Le PSNR devrait etre nettement superieur a V1.")
    print(f"  Le compromis ratio/qualite est controle par K (nombre de composantes).")
    print()


if __name__ == "__main__":
    run_tests()