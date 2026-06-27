#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST V4 — Compression Holographique HCV PRO avec 3 Améliorations
================================================================
V4 implémente simultanément :
  1. Pyramide holographique (2 niveaux : 8×8 + 16×16→downscale)
  2. DPCM inter-blocs (prédiction coefficients voisin gauche)
  3. Quantification vectorielle (K-means sur vecteurs de coefficients)

Objectif : +20-28 dB par rapport à V3 → cible 45-55 dB à 32:1

Usage :
  python test_hcv_compression_v4.py
"""

import numpy as np
import math, sys, os, time, struct, zlib
from typing import Dict, Any, Tuple, Optional
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from harmonic_processor import HBit, PHI, PI, E, HARMONIC_CONSTANTS, H_CONSTANT_NAMES


# ==============================================================================
# COMPRESSEUR HOLOGRAPHIQUE V4 — Pyramide + DPCM + VQ
# ==============================================================================

class HCVCompressorV4:
    """
    Compresseur holographique V4 avec trois améliorations :

    1. PYRAMIDE HOLOGRAPHIQUE :
       Niveau 0 : blocs 8×8  → SVD → K₀ coefficients (hautes fréquences)
       Niveau 1 : downscale 2× → blocs 8×8 → SVD → K₁ coefficients (basses fréquences)
       Reconstruction = upsample(niveau1) + résidu niveau0

    2. DPCM INTER-BLOCS :
       Les coefficients sont prédits à partir du bloc voisin gauche.
       Seul le résidu de prédiction est encodé → variance réduite → meilleure quantification.

    3. QUANTIFICATION VECTORIELLE (VQ) :
       Les vecteurs de K coefficients sont quantifiés par un dictionnaire
       appris via K-means (M centroïdes). Chaque bloc → 1 index uint8 ou uint16.
    """

    def __init__(self, K0: int = 4, K1: int = 2, vq_centroids: int = 256, block_size: int = 8):
        """
        Args:
            K0: composantes holographiques niveau 0 (pleine résolution)
            K1: composantes holographiques niveau 1 (downscale 2×)
            vq_centroids: nombre de centroïdes VQ (256 = 1 octet/bloc, 65536 = 2 octets)
            block_size: taille des blocs (8)
        """
        self.K0 = K0
        self.K1 = K1
        self.K_total = K0 + K1  # composantes totales par bloc
        self.vq_centroids = vq_centroids
        self.block_size = block_size
        self.dim = block_size * block_size  # 64

        # Hologrammes par niveau
        self.hologram0: Optional[np.ndarray] = None   # (K0, 64)
        self.hologram1: Optional[np.ndarray] = None   # (K1, 64)

        # Statistiques par niveau
        self.mean0 = self.std0 = 0.0
        self.mean1 = self.std1 = 0.0

        # Codebook VQ (dictionnaire de centroïdes)
        self.codebook: Optional[np.ndarray] = None  # (M, K_total)

        # DPCM : coefficients du bloc précédent (gauche)
        self._prev_coeffs: Optional[np.ndarray] = None

    # ========================================================================
    # PYRAMIDE HOLOGRAPHIQUE
    # ========================================================================

    def _train_level(self, image: np.ndarray, K: int) -> Tuple[np.ndarray, float, float, float]:
        """SVD adaptatif sur les blocs 8×8 d'une image (pleine résolution ou downscalée)."""
        H, W = image.shape
        bs = self.block_size
        n_h, n_w = H // bs, W // bs

        blocks = []
        for i in range(n_h):
            for j in range(n_w):
                b = image[i*bs:(i+1)*bs, j*bs:(j+1)*bs].flatten().astype(np.float64)
                blocks.append(b)
        blocks = np.array(blocks)
        blocks = np.nan_to_num(blocks, nan=0.0, posinf=1.0, neginf=0.0)
        blocks = np.clip(blocks, 0.0, 1.0)

        bmean = float(np.mean(blocks))
        bstd = float(np.std(blocks)) + 1e-12
        centered = (blocks - bmean) / bstd

        try:
            U, S, Vt = np.linalg.svd(centered, full_matrices=False)
        except np.linalg.LinAlgError:
            Vt = np.zeros((64, 64))
            for k in range(64):
                Vt[k] = np.cos((k + 1) * np.pi * np.arange(64) / 64)
                Vt[k] /= np.linalg.norm(Vt[k]) + 1e-12
            S = np.ones(64)

        hologram = Vt[:K, :].copy()
        for k in range(K):
            n = np.linalg.norm(hologram[k])
            if n > 1e-12:
                hologram[k] /= n

        total_e = np.sum(S ** 2)
        preserved_e = np.sum(S[:K] ** 2)
        energy = float(preserved_e / total_e) if total_e > 1e-12 else 1.0

        return hologram, bmean, bstd, energy

    def _encode_blocks(self, image: np.ndarray, hologram: np.ndarray,
                       bmean: float, bstd: float) -> np.ndarray:
        """Encode tous les blocs d'une image → coefficients."""
        H, W = image.shape
        bs = self.block_size
        n_h, n_w = H // bs, W // bs
        K = hologram.shape[0]
        coeffs = np.zeros((n_h, n_w, K), dtype=np.float64)

        for i in range(n_h):
            for j in range(n_w):
                b = image[i*bs:(i+1)*bs, j*bs:(j+1)*bs].flatten().astype(np.float64)
                centered = (b - bmean) / bstd
                coeffs[i, j] = np.dot(hologram, centered)

        return coeffs

    def _decode_blocks(self, coeffs: np.ndarray, hologram: np.ndarray,
                       bmean: float, bstd: float) -> np.ndarray:
        """Reconstruit l'image à partir des coefficients."""
        n_h, n_w, K = coeffs.shape
        bs = self.block_size
        image = np.zeros((n_h * bs, n_w * bs), dtype=np.float64)

        for i in range(n_h):
            for j in range(n_w):
                centered = np.dot(coeffs[i, j], hologram)
                block = centered * bstd + bmean
                image[i*bs:(i+1)*bs, j*bs:(j+1)*bs] = block.reshape(bs, bs)

        return np.clip(image, 0, 1)

    def _downscale(self, image: np.ndarray) -> np.ndarray:
        """Downscale 2× par moyenne de blocs 2×2."""
        H, W = image.shape
        h2, w2 = H // 2, W // 2
        # Pad si nécessaire
        if H % 2:
            image = np.pad(image, ((0, 1), (0, 0)), mode='edge')
        if W % 2:
            image = np.pad(image, ((0, 0), (0, 1)), mode='edge')
        return (image[0::2, 0::2] + image[0::2, 1::2] +
                image[1::2, 0::2] + image[1::2, 1::2]) / 4.0

    def _upscale(self, image: np.ndarray, target_shape: Tuple[int, int]) -> np.ndarray:
        """Upscale 2× par répétition."""
        H, W = target_shape
        h_small, w_small = image.shape
        up = np.repeat(np.repeat(image, 2, axis=0), 2, axis=1)
        return up[:H, :W]

    # ========================================================================
    # DPCM (Differential Pulse Code Modulation)
    # ========================================================================

    def _dpcm_encode(self, coeffs: np.ndarray) -> np.ndarray:
        """
        Encode les coefficients en DPCM : résidu = coeffs - prédiction(gauche).
        Retourne les résidus de même forme.
        """
        n_h, n_w, K = coeffs.shape
        residuals = np.zeros_like(coeffs)

        for i in range(n_h):
            for j in range(n_w):
                if j > 0:
                    prediction = coeffs[i, j-1]  # prédiction = bloc gauche
                elif i > 0:
                    prediction = coeffs[i-1, j]   # prédiction = bloc haut (première colonne)
                else:
                    prediction = np.zeros(K)       # premier bloc : pas de prédiction
                residuals[i, j] = coeffs[i, j] - prediction

        return residuals

    def _dpcm_decode(self, residuals: np.ndarray) -> np.ndarray:
        """Décode DPCM : coeffs = résidu + prédiction."""
        n_h, n_w, K = residuals.shape
        coeffs = np.zeros_like(residuals)

        for i in range(n_h):
            for j in range(n_w):
                if j > 0:
                    prediction = coeffs[i, j-1]
                elif i > 0:
                    prediction = coeffs[i-1, j]
                else:
                    prediction = np.zeros(K)
                coeffs[i, j] = residuals[i, j] + prediction

        return coeffs

    # ========================================================================
    # QUANTIFICATION VECTORIELLE (VQ / K-means)
    # ========================================================================

    def _train_codebook(self, vectors: np.ndarray) -> np.ndarray:
        """
        Apprend un dictionnaire de M centroïdes par K-means simplifié
        (initialisation aléatoire + 10 itérations Lloyd).
        """
        N, D = vectors.shape
        M = min(self.vq_centroids, N)  # pas plus de centroïdes que de vecteurs

        # Initialisation : M vecteurs aléatoires parmi les données
        indices = np.random.choice(N, M, replace=False)
        centroids = vectors[indices].copy().astype(np.float64)

        # Lloyd iterations
        for it in range(10):
            # Assignation
            distances = np.zeros((N, M))
            for m in range(M):
                diff = vectors - centroids[m]
                distances[:, m] = np.sum(diff ** 2, axis=1)
            assignments = np.argmin(distances, axis=1)

            # Mise à jour
            for m in range(M):
                cluster = vectors[assignments == m]
                if len(cluster) > 0:
                    centroids[m] = np.mean(cluster, axis=0)

        return centroids

    def _vq_encode(self, vectors: np.ndarray, codebook: np.ndarray) -> np.ndarray:
        """Encode des vecteurs → indices de centroïdes les plus proches."""
        N, D = vectors.shape
        M = codebook.shape[0]
        indices = np.zeros(N, dtype=np.uint16)

        # Recherche du plus proche voisin pour chaque vecteur
        for n in range(N):
            diff = codebook - vectors[n]
            dists = np.sum(diff ** 2, axis=1)
            indices[n] = np.argmin(dists)

        return indices

    def _vq_decode(self, indices: np.ndarray, codebook: np.ndarray) -> np.ndarray:
        """Décode des indices → vecteurs reconstruits."""
        return codebook[indices]

    # ========================================================================
    # COMPRESSION / DÉCOMPRESSION
    # ========================================================================

    def compress(self, image: np.ndarray) -> Tuple[bytes, Dict[str, Any]]:
        H, W = image.shape
        bs = self.block_size

        # Recadrer aux multiples de 16 (2× downscale puis 8× blocks)
        H_crop = (H // 16) * 16
        W_crop = (W // 16) * 16
        image = image[:H_crop, :W_crop]
        H, W = H_crop, W_crop

        t0 = time.perf_counter()

        # ---- Niveau 1 : downscale 2× (basses fréquences) ----
        t_train = time.perf_counter()
        image_down = self._downscale(image)
        self.hologram1, self.mean1, self.std1, e1 = self._train_level(image_down, self.K1)

        # Encodage niveau 1
        coeffs1 = self._encode_blocks(image_down, self.hologram1, self.mean1, self.std1)
        # Reconstruire niveau 1 → upscale → résidu niveau 0
        recon1 = self._decode_blocks(coeffs1, self.hologram1, self.mean1, self.std1)
        recon1_up = self._upscale(recon1, (H, W))
        residual0 = image - recon1_up  # résidu hautes fréquences

        # ---- Niveau 0 : SVD sur le résidu (hautes fréquences) ----
        self.hologram0, self.mean0, self.std0, e0 = self._train_level(residual0, self.K0)
        t_train = time.perf_counter() - t_train

        # Encodage niveau 0 (résidu hautes fréquences)
        coeffs0_raw = self._encode_blocks(residual0, self.hologram0, self.mean0, self.std0)

        # DPCM sur les coefficients des deux niveaux
        residual0_dpcm = self._dpcm_encode(coeffs0_raw)
        residual1_dpcm = self._dpcm_encode(coeffs1)

        # Concaténer les résidus DPCM pour VQ
        n_h0, n_w0 = residual0_dpcm.shape[0], residual0_dpcm.shape[1]
        n_h1, n_w1 = residual1_dpcm.shape[0], residual1_dpcm.shape[1]
        n_total_blocks = n_h0 * n_w0 + n_h1 * n_w1

        # Pack niveau 0 et niveau 1 ensembles pour VQ
        # On pad le niveau 1 à K_total composantes (K0+K1) avec des zéros
        vecs0 = residual0_dpcm.reshape(-1, self.K0)  # (N0, K0)
        vecs1_padded = np.zeros((n_h1 * n_w1, self.K_total), dtype=np.float64)
        vecs1_padded[:, :self.K1] = residual1_dpcm.reshape(-1, self.K1)
        vecs0_padded = np.zeros((n_h0 * n_w0, self.K_total), dtype=np.float64)
        vecs0_padded[:, :self.K0] = vecs0

        # Apprentissage du codebook VQ
        all_vecs = np.concatenate([vecs0_padded, vecs1_padded], axis=0)
        self.codebook = self._train_codebook(all_vecs)

        # Encodage VQ
        indices0 = self._vq_encode(vecs0_padded, self.codebook)
        indices1 = self._vq_encode(vecs1_padded, self.codebook)

        # Déterminer la taille d'index nécessaire
        M = self.codebook.shape[0]
        if M <= 256:
            index_dtype = np.uint8
            bytes_per_index = 1
        else:
            index_dtype = np.uint16
            bytes_per_index = 2
        indices0 = indices0.astype(index_dtype)
        indices1 = indices1.astype(index_dtype)

        # Packing binaire
        # Header struct (40 octets)
        header = struct.pack(
            '<4sIIBBBBHffffffffff',
            b'HCV4', H, W, self.K0, self.K1, bs, bs,
            M,
            self.mean0, self.std0,
            self.mean1, self.std1,
            e0, e1, 0.0, 0.0, 0.0, 0.0  # padding to match struct
        )

        # Hologrammes en float16
        holo0_f16 = self.hologram0.astype(np.float16).tobytes()
        holo1_f16 = self.hologram1.astype(np.float16).tobytes()

        # Codebook en float16
        cb_f16 = self.codebook.astype(np.float16).tobytes()

        # Indices VQ
        payload = indices0.tobytes() + indices1.tobytes()

        raw_bytes = header + holo0_f16 + holo1_f16 + cb_f16 + payload
        compressed = zlib.compress(raw_bytes, level=6)

        t_enc = time.perf_counter() - t0

        original_size = H * W
        compressed_size = len(compressed)

        # Ratio brut = 64/(K_total) pixels/bloc / octets par bloc
        # Avec VQ : chaque bloc → bytes_per_index octets
        ratio_brut = 64.0 / (bytes_per_index)  # indépendant de K avec VQ!

        header_size = 40 + (self.K0 + self.K1) * 64 * 2 + M * self.K_total * 2
        payload_raw = (n_h0 * n_w0 + n_h1 * n_w1) * bytes_per_index

        metadata = {
            'shape': (H, W),
            'K0': self.K0, 'K1': self.K1,
            'K_total': self.K_total,
            'VQ_M': M,
            'bytes_per_index': bytes_per_index,
            'energy0': round(e0 * 100, 2),
            'energy1': round(e1 * 100, 2),
            'original_size_bytes': original_size,
            'compressed_size_bytes': compressed_size,
            'ratio_brut': round(ratio_brut, 2),
            'ratio_effectif': round(original_size / compressed_size, 2),
            'time_train_ms': round(t_train * 1000, 2),
            'time_encode_ms': round(t_enc * 1000, 2),
            'header_size': header_size,
            'payload_raw': payload_raw,
            'n_blocks0': (n_h0, n_w0),
            'n_blocks1': (n_h1, n_w1),
        }

        return compressed, metadata

    def decompress(self, bitstream: bytes, metadata: Dict[str, Any]) -> Tuple[np.ndarray, float]:
        t0 = time.perf_counter()

        raw_bytes = zlib.decompress(bitstream)

        # Décoder header
        magic, H, W, K0, K1, bs, bs2, M = struct.unpack(
            '<4sIIBBBBH', raw_bytes[:18]
        )
        assert magic == b'HCV4'
        self.K0, self.K1 = K0, K1
        self.K_total = K0 + K1
        self.block_size = bs

        # Lire les statistiques (10 floats = 40 octets après les 18)
        floats = struct.unpack('<ffffffffff', raw_bytes[18:58])
        self.mean0, self.std0 = floats[0], floats[1]
        self.mean1, self.std1 = floats[2], floats[3]

        offset = 58

        # Hologramme niveau 0
        h0_size = K0 * 64 * 2
        holo0_f16 = np.frombuffer(raw_bytes[offset:offset+h0_size], dtype=np.float16)
        self.hologram0 = holo0_f16.reshape(K0, 64).astype(np.float64)
        offset += h0_size

        # Hologramme niveau 1
        h1_size = K1 * 64 * 2
        holo1_f16 = np.frombuffer(raw_bytes[offset:offset+h1_size], dtype=np.float16)
        self.hologram1 = holo1_f16.reshape(K1, 64).astype(np.float64)
        offset += h1_size

        # Codebook VQ
        cb_size = M * self.K_total * 2
        cb_f16 = np.frombuffer(raw_bytes[offset:offset+cb_size], dtype=np.float16)
        self.codebook = cb_f16.reshape(M, self.K_total).astype(np.float64)
        offset += cb_size

        # Indices VQ
        n_h0, n_w0 = metadata['n_blocks0']
        n_h1, n_w1 = metadata['n_blocks1']
        n_total = n_h0 * n_w0 + n_h1 * n_w1
        bytes_per_index = metadata['bytes_per_index']
        index_dtype = np.uint8 if bytes_per_index == 1 else np.uint16
        all_indices = np.frombuffer(raw_bytes[offset:offset + n_total * bytes_per_index], dtype=index_dtype)

        idx0 = all_indices[:n_h0 * n_w0]
        idx1 = all_indices[n_h0 * n_w0:]

        # Décodage VQ → résidus DPCM
        vecs0_padded = self._vq_decode(idx0, self.codebook)
        vecs1_padded = self._vq_decode(idx1, self.codebook)

        residual0_dpcm = vecs0_padded[:, :self.K0].reshape(n_h0, n_w0, self.K0)
        residual1_dpcm = vecs1_padded[:, :self.K1].reshape(n_h1, n_w1, self.K1)

        # Décodage DPCM → coefficients
        coeffs0 = self._dpcm_decode(residual0_dpcm)
        coeffs1 = self._dpcm_decode(residual1_dpcm)

        # Reconstruction niveau 1
        recon1 = self._decode_blocks(coeffs1, self.hologram1, self.mean1, self.std1)
        recon1_up = self._upscale(recon1, (H, W))

        # Reconstruction niveau 0 (résidu)
        residual0_recon = self._decode_blocks(coeffs0, self.hologram0, self.mean0, self.std0)

        # Image finale
        reconstructed = recon1_up + residual0_recon
        reconstructed = np.clip(reconstructed, 0, 1)

        t_dec = time.perf_counter() - t0
        return reconstructed, round(t_dec * 1000, 2)


# ==============================================================================
# METRIQUES
# ==============================================================================

def compute_psnr(original: np.ndarray, compressed: np.ndarray) -> float:
    o = original.astype(np.float64)
    c = compressed.astype(np.float64)
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


# ==============================================================================
# GENERATEUR PAYSAGE
# ==============================================================================

def generate_landscape_big(H: int, W: int) -> np.ndarray:
    y = np.linspace(0, 1, H).reshape(-1, 1)
    x = np.linspace(0, 1, W).reshape(1, -1)

    def perlin_like(h, w, octaves=5, seed=42):
        np.random.seed(seed)
        noise = np.zeros((h, w), dtype=np.float64)
        for o in range(octaves):
            scale = 2 ** o
            hs, ws = max(4, h // scale), max(4, w // scale)
            small = np.random.rand(hs, ws)
            layer = np.repeat(np.repeat(small, h // hs + 1, axis=0), w // ws + 1, axis=1)[:h, :w]
            noise += layer / (2 ** o)
        return (noise - noise.min()) / (noise.max() - noise.min() + 1e-12)

    terrain = perlin_like(H, W, octaves=5, seed=7)
    clouds = perlin_like(H, W, octaves=4, seed=13)

    sky = 0.4 + 0.5 * (1 - y)
    horizon = 0.55 + 0.15 * np.sin(x * 12) + 0.08 * terrain[:1, :]
    terrain_mask = (y > horizon).astype(np.float64)
    terrain_color = 0.3 + 0.4 * terrain
    lake_mask = ((y > 0.75) & (x < 0.45)).astype(np.float64)
    lake = 0.15 + 0.1 * terrain
    cloud_col = 0.7 + 0.3 * clouds
    cloud_mask = (y < 0.45).astype(np.float64)

    img = terrain_mask * terrain_color + (1 - terrain_mask) * sky
    img = img * (1 - lake_mask * 0.5) + lake_mask * lake * 0.5
    img = img * (1 - cloud_mask * 0.3) + cloud_mask * cloud_col * 0.3
    return np.clip(img, 0, 1).astype(np.float64)


# ==============================================================================
# TEST
# ==============================================================================

def run_test():
    print("=" * 75)
    print("  TEST V4 — Pyramide + DPCM + VQ")
    print("  Objectif : +20-28 dB par rapport à V3")
    print("=" * 75)

    resolutions = [
        ("512×512", 512, 512),
        ("960×540", 540, 960),
    ]

    # Configs à tester
    configs = [
        # (K0, K1, VQ_M, label)
        (4, 2, 256,   "K0=4,K1=2,VQ256"),
        (4, 2, 512,   "K0=4,K1=2,VQ512"),
        (6, 3, 512,   "K0=6,K1=3,VQ512"),
        (8, 4, 1024,  "K0=8,K1=4,VQ1k"),
    ]

    # Baseline V3 pour comparaison
    print("\n  --- BASELINE V3 (uint16, sans pyramide/DPCM/VQ) ---")
    sys.path.insert(0, os.path.dirname(__file__))
    from test_hcv_compression_v3 import HCVCompressorV3

    for res_name, H, W in resolutions:
        img = generate_landscape_big(H, W)
        print(f"\n  Paysage {res_name} :")
        for K_v3 in [4, 6, 8]:
            comp3 = HCVCompressorV3(K=K_v3, block_size=8)
            bs3, meta3 = comp3.compress(img)
            rec3, _ = comp3.decompress(bs3, meta3)
            psnr3 = compute_psnr(img, rec3)
            print(f"    V3 K={K_v3}: ratio {meta3['ratio_effectif']:.1f}x, PSNR {psnr3} dB")

    # Test V4
    print(f"\n\n{'='*75}")
    print("  TEST V4 — Pyramide Holographique + DPCM + VQ")
    print(f"  {'='*75}")

    for res_name, H, W in resolutions:
        img_full = generate_landscape_big(H, W)
        H_crop = (H // 16) * 16
        W_crop = (W // 16) * 16
        img = img_full[:H_crop, :W_crop]
        n_blocs_full = (H_crop//8) * (W_crop//8)
        n_blocs_down = ((H_crop//2)//8) * ((W_crop//2)//8)
        print(f"\n  Paysage {res_name} crop {H_crop}x{W_crop} ({H_crop*W_crop//1024} Ko, {n_blocs_full}+{n_blocs_down} blocs) :")
        print(f"  {'Config':<22s} {'Ratio':>7s} {'PSNR':>9s} {'vs V3':>9s} {'E0':>6s} {'E1':>6s} {'T.Enc':>7s} {'T.Dec':>7s} {'Hdr':>8s} {'Pay':>8s}")
        print(f"  {'-'*22} {'-'*7} {'-'*9} {'-'*9} {'-'*6} {'-'*6} {'-'*7} {'-'*7} {'-'*8} {'-'*8}")

        for K0, K1, VQ_M, label in configs:
            comp4 = HCVCompressorV4(K0=K0, K1=K1, vq_centroids=VQ_M, block_size=8)
            bs4, meta4 = comp4.compress(img)
            rec4, t_dec4 = comp4.decompress(bs4, meta4)
            psnr4 = compute_psnr(img, rec4)

            # PSNR V3 équivalent (même nombre total de coeffs K_total)
            K_total = K0 + K1
            comp3 = HCVCompressorV3(K=K_total, block_size=8)
            bs3, meta3 = comp3.compress(img)
            rec3, _ = comp3.decompress(bs3, meta3)
            psnr3 = compute_psnr(img, rec3)
            delta = psnr4 - psnr3 if psnr3 != float('inf') and psnr4 != float('inf') else 0

            delta_str = f"+{delta:.1f} dB" if delta > 0 else f"{delta:.1f} dB"
            print(f"  {label:<22s} {meta4['ratio_effectif']:6.2f}x {psnr4:8.2f} dB {delta_str:>9s} {meta4['energy0']:5.1f}% {meta4['energy1']:5.1f}% {meta4['time_encode_ms']/1000:6.2f}s {t_dec4/1000:6.2f}s {meta4['header_size']:>8d} {meta4['payload_raw']:>8d}")

    # Récapitulatif
    print(f"\n{'='*75}")
    print("  RÉCAPITULATIF — Gains V4 vs V3")
    print(f"  {'='*75}")
    print(f"  Pyramide : décompose basses/hautes fréquences → SVD sur chaque niveau")
    print(f"  DPCM     : prédiction spatiale coefficients → résidu de variance réduite")
    print(f"  VQ       : quantification vectorielle → 1 index/bloc au lieu de K×2 octets")
    print(f"  Ratio attendu : 64:1 avec VQ256 (1 octet/bloc) après zlib ~ 80:1")
    print()


if __name__ == "__main__":
    run_test()