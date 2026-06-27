#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST V1 ONDULATOIRE — Théorie des Interférences sur la base V1
===============================================================
Reprend la V1 (7 ondes harmoniques génériques : phi, pi, e, sqrt2, sqrt3, sqrt5, e/pi)
mais applique une VÉRITABLE théorie ondulatoire au lieu d'une simple projection.

Concepts explorés :
  1. Interférence holographique (amplitude + phase) → 14 scalaires/bloc
  2. Interférence croisée (termes φ_i ⊗ φ_j) → capture la structure non-linéaire
  3. Modulation de phase → onde de référence modulée par le bloc
  4. Reconstruction par rétro-propagation ondulatoire

Avantage clé de la V1 : ZÉRO header hologramme.
Les 7 ondes sont universelles (constantes harmoniques), connues du décodeur.
Ratio = 64/K sans coût de header → idéal pour le broadcast.

Usage :
  python test_hcv_v1_ondulatoire.py
"""

import numpy as np
import math, sys, os, time, struct, zlib
from typing import Dict, Any, Tuple, Optional

sys.path.insert(0, os.path.dirname(__file__))
from harmonic_processor import HBit, PHI, PI, E, HARMONIC_CONSTANTS, H_CONSTANT_NAMES, H_BIT_DIMENSION

# ==============================================================================
# COMPRESSEUR HOLOGRAPHIQUE V1 ONDULATOIRE
# ==============================================================================

class HCVCompressorV1Ondulatoire:
    """
    V1 améliorée par théorie ondulatoire.

    Au lieu de projeter linéairement le bloc sur 7 ondes (dot product → 7 scalaires),
    on calcule le PATRON D'INTERFÉRENCE HOLOGRAPHIQUE :
      - Amplitude de l'interférence onde_référence ⊗ bloc
      - Phase de l'interférence
      - Interférences croisées entre les ondes elles-mêmes (termes non-linéaires)

    Reconstruction par rétro-propagation ondulatoire (pas de projection linéaire).

    Modes disponibles :
      'projection'  : V1 classique (7 coefficients réels = dot product)
      'interference' : holographique (7 coeffs amplitude + 7 coeffs phase = 14 scalaires)
      'croisee'      : + interférences croisées (7 + 21 = 28 scalaires)
      'modulation'   : modulation de chaque onde par le bloc → 7 coeffs complexes
    """

    def __init__(self, mode: str = 'interference', block_size: int = 8):
        self.mode = mode
        self.block_size = block_size
        self.dim = block_size * block_size  # 64

        # Les 7 ondes de référence (périodiques sur la grille du bloc)
        self.ondes_ref = self._build_reference_waves()

        # Nombre de coefficients selon le mode
        if mode == 'projection':
            self.n_coeffs = H_BIT_DIMENSION  # 7
        elif mode == 'interference':
            self.n_coeffs = H_BIT_DIMENSION * 2  # 14 : amplitude + phase
        elif mode == 'croisee':
            self.n_cross = H_BIT_DIMENSION * (H_BIT_DIMENSION - 1) // 2  # 21
            self.n_coeffs = H_BIT_DIMENSION * 2 + self.n_cross  # 35
        elif mode == 'modulation':
            self.n_coeffs = H_BIT_DIMENSION * 2  # 14 : complexe

        self.ratio_brut = 64.0 / self.n_coeffs  # avant quantification

    def _build_reference_waves(self):
        """
        Construit les 7 ondes de référence harmoniques 2D (8×8).
        Chaque onde = cos(φ_k * π * (i+j) / 8) — oscillation spatiale.
        Normalisées pour former une base quasi-orthogonale.
        """
        ondes = []
        for k in range(H_BIT_DIMENSION):
            freq = HARMONIC_CONSTANTS[k] * PHI
            # Onde 2D : oscillation diagonale
            wave = np.zeros((self.block_size, self.block_size), dtype=np.float64)
            for i in range(self.block_size):
                for j in range(self.block_size):
                    # Fréquence spatiale modulée par la constante harmonique
                    phase = freq * (i + j) / self.block_size * 2 * PI
                    wave[i, j] = np.cos(phase)
            # Normaliser
            n = np.linalg.norm(wave)
            if n > 1e-12:
                wave /= n
            ondes.append(wave)
        return ondes  # liste de 7 arrays (8,8)

    def _encode_block_interference(self, block: np.ndarray) -> np.ndarray:
        """
        Encode un bloc → 14 coefficients (7 amplitudes + 7 phases)
        via interférence holographique.

        Pour chaque onde de référence R_k :
          I_k = Σ_{pixels} block(x,y) * R_k(x,y)            (amplitude = projection)
          Q_k = Σ_{pixels} block(x,y) * R_k_shifted(x,y)    (quadrature = onde déphasée π/2)
          amplitude_k = sqrt(I_k² + Q_k²)
          phase_k = atan2(Q_k, I_k)

        On encode amplitude et phase séparément.
        """
        block_flat = block.flatten().astype(np.float64)
        n_block = np.linalg.norm(block_flat)
        N_COEFFS_INTERF = H_BIT_DIMENSION * 2  # 14 fixed, independent of mode
        if n_block < 1e-12:
            return np.zeros(N_COEFFS_INTERF)

        block_norm = block_flat / n_block

        coeffs = np.zeros(N_COEFFS_INTERF)  # [amp_0..amp_6, phase_0..phase_6]
        for k in range(H_BIT_DIMENSION):
            Rk = self.ondes_ref[k].flatten()
            # Quadrature : onde déphasée de π/2 (sin au lieu de cos)
            # On reconstruit sin à partir de cos en shiftant d'un quart de période
            Rk_quad = np.roll(Rk, self.dim // 4)

            I_k = np.dot(block_norm, Rk)
            Q_k = np.dot(block_norm, Rk_quad)

            amp = math.sqrt(I_k**2 + Q_k**2)
            phase = math.atan2(Q_k, I_k)

            coeffs[k] = amp
            coeffs[H_BIT_DIMENSION + k] = phase

        return coeffs

    def _decode_block_interference(self, coeffs: np.ndarray) -> np.ndarray:
        """
        Décode 14 coefficients → bloc 8×8.
        Reconstruction = Σ_k amplitude_k * cos(onde_k + phase_k) / norm
        """
        # Extraire amplitude et phase
        amps = coeffs[:H_BIT_DIMENSION]
        phases = coeffs[H_BIT_DIMENSION:H_BIT_DIMENSION*2]

        reconstructed = np.zeros(self.dim, dtype=np.float64)
        for k in range(H_BIT_DIMENSION):
            Rk = self.ondes_ref[k].flatten()
            # Onde modulée : amplitude * cos(onde_réf + phase)
            Rk_mod = amps[k] * np.cos(np.arccos(np.clip(Rk, -1, 1)) + phases[k])
            reconstructed += Rk_mod

        # Normaliser
        n = np.linalg.norm(reconstructed)
        if n > 1e-12:
            reconstructed = reconstructed / n

        return reconstructed.reshape(self.block_size, self.block_size)

    def _encode_block_croisee(self, block: np.ndarray) -> np.ndarray:
        """
        Encode avec interférences croisées.
        En plus de amplitude+phase, on calcule les produits scalaires
        entre les ondes modulées → capture la structure non-linéaire.

        Coeffs = [amp_0..6, phase_0..6, cross_01, cross_02, ..., cross_56]
        Total = 7 + 7 + 21 = 35
        """
        # D'abord l'interférence de base
        base = self._encode_block_interference(block)

        # Interférences croisées
        cross = np.zeros(self.n_cross)
        idx = 0
        for i in range(H_BIT_DIMENSION):
            for j in range(i+1, H_BIT_DIMENSION):
                # Interférence entre onde i et onde j sur le bloc
                Ri = self.ondes_ref[i].flatten()
                Rj = self.ondes_ref[j].flatten()
                block_flat = block.flatten().astype(np.float64)
                n_b = np.linalg.norm(block_flat)
                if n_b > 1e-12:
                    block_flat = block_flat / n_b
                cross[idx] = np.dot(Ri * Rj, block_flat)  # terme d'interférence croisée
                idx += 1

        return np.concatenate([base, cross])

    def _decode_block_croisee(self, coeffs: np.ndarray) -> np.ndarray:
        """Décode avec interférences croisées."""
        base = self._decode_block_interference(coeffs[:H_BIT_DIMENSION*2])

        # Ajouter les contributions croisées
        cross = coeffs[H_BIT_DIMENSION*2:]
        base_flat = base.flatten()
        idx = 0
        for i in range(H_BIT_DIMENSION):
            for j in range(i+1, H_BIT_DIMENSION):
                Ri = self.ondes_ref[i].flatten()
                Rj = self.ondes_ref[j].flatten()
                base_flat += cross[idx] * (Ri * Rj)
                idx += 1

        n = np.linalg.norm(base_flat)
        if n > 1e-12:
            base_flat = base_flat / n
        return base_flat.reshape(self.block_size, self.block_size)

    def _encode_block_modulation(self, block: np.ndarray) -> np.ndarray:
        """
        Mode modulation : chaque onde de référence est MODULÉE par le bloc.
        On calcule le coefficient complexe c_k = |c_k| * e^{iφ_k}
        qui minimise ||block - Σ c_k * onde_k||² → solution des moindres carrés.

        C'est le produit scalaire complexe entre le bloc et l'onde complexe.
        """
        block_flat = block.flatten().astype(np.float64)
        n_b = np.linalg.norm(block_flat)
        if n_b < 1e-12:
            return np.zeros(self.n_coeffs)
        block_norm = block_flat / n_b

        coeffs = np.zeros(self.n_coeffs)  # [Re_0..6, Im_0..6]
        for k in range(H_BIT_DIMENSION):
            Rk = self.ondes_ref[k].flatten()
            Rk_quad = np.roll(Rk, self.dim // 4)

            # Coefficient complexe : projection sur l'onde complexe
            Re_k = np.dot(block_norm, Rk)
            Im_k = np.dot(block_norm, Rk_quad)

            coeffs[k] = Re_k
            coeffs[H_BIT_DIMENSION + k] = Im_k

        return coeffs

    def _decode_block_modulation(self, coeffs: np.ndarray) -> np.ndarray:
        """Décode coefficients complexes → bloc."""
        reconstructed = np.zeros(self.dim, dtype=np.float64)
        for k in range(H_BIT_DIMENSION):
            Rk = self.ondes_ref[k].flatten()
            Rk_quad = np.roll(Rk, self.dim // 4)
            reconstructed += coeffs[k] * Rk + coeffs[H_BIT_DIMENSION + k] * Rk_quad

        n = np.linalg.norm(reconstructed)
        if n > 1e-12:
            reconstructed = reconstructed / n
        return reconstructed.reshape(self.block_size, self.block_size)

    def _encode_simple_projection(self, block: np.ndarray) -> np.ndarray:
        """V1 classique : simple dot product sur les 7 ondes."""
        block_flat = block.flatten().astype(np.float64)
        n_b = np.linalg.norm(block_flat)
        if n_b < 1e-12:
            return np.zeros(H_BIT_DIMENSION)
        block_norm = block_flat / n_b

        coeffs = np.zeros(H_BIT_DIMENSION)
        for k in range(H_BIT_DIMENSION):
            Rk = self.ondes_ref[k].flatten()
            coeffs[k] = np.dot(block_norm, Rk)
        return coeffs

    def _decode_simple_projection(self, coeffs: np.ndarray) -> np.ndarray:
        """V1 classique : reconstruction linéaire."""
        reconstructed = np.zeros(self.dim, dtype=np.float64)
        for k in range(H_BIT_DIMENSION):
            Rk = self.ondes_ref[k].flatten()
            reconstructed += coeffs[k] * Rk
        n = np.linalg.norm(reconstructed)
        if n > 1e-12:
            reconstructed = reconstructed / n
        return reconstructed.reshape(self.block_size, self.block_size)

    def compress(self, image: np.ndarray) -> Tuple[bytes, Dict[str, Any]]:
        H, W = image.shape
        bs = self.block_size
        n_h, n_w = H // bs, W // bs
        n_total = n_h * n_w

        t0 = time.perf_counter()

        # Encoder tous les blocs
        all_coeffs = np.zeros((n_total, self.n_coeffs), dtype=np.float64)
        idx = 0
        for i in range(n_h):
            for j in range(n_w):
                block = image[i*bs:(i+1)*bs, j*bs:(j+1)*bs]
                if self.mode == 'projection':
                    c = self._encode_simple_projection(block)
                elif self.mode == 'interference':
                    c = self._encode_block_interference(block)
                elif self.mode == 'croisee':
                    c = self._encode_block_croisee(block)
                elif self.mode == 'modulation':
                    c = self._encode_block_modulation(block)
                all_coeffs[idx] = c
                idx += 1

        # Quantification uint16 (pas de header hologramme nécessaire !)
        c_min = float(all_coeffs.min())
        c_max = float(all_coeffs.max())
        if c_max - c_min < 1e-12:
            c_max = c_min + 1.0

        UINT16_MAX = 65535.0
        coeffs_norm = (all_coeffs - c_min) / (c_max - c_min)
        coeffs_uint16 = np.clip(np.round(coeffs_norm * UINT16_MAX), 0, 65535).astype(np.uint16)

        # Header minimal : 30 octets (pas d'hologramme !)
        header = struct.pack(
            '<4sIIBBBBff',  # 4+4+4+1+1+1+1+4+4 = 24
            b'HCVW',  # HCV Wave
            H, W,
            self.n_coeffs, bs,
            0, 0,  # padding
            c_min, c_max
        )
        payload = coeffs_uint16.tobytes()
        compressed = zlib.compress(header + payload, level=6)

        t_enc = time.perf_counter() - t0

        original_size = H * W
        compressed_size = len(compressed)

        # Ratio brut = 64/n_coeffs (pixels par bloc / coeffs par bloc)
        # Avec uint16 : 64/(n_coeffs * 2) en termes d'octets
        # Mais on parle de ratio de compression : taille_originale / taille_compressée
        ratio_brut_pixels = 64.0 / self.n_coeffs
        ratio_brut_bytes = 64.0 / (self.n_coeffs * 2)  # 1 pixel = 1 octet, 1 coeff = 2 octets

        metadata = {
            'shape': (H, W),
            'mode': self.mode,
            'n_coeffs': self.n_coeffs,
            'ratio_brut_coeffs': round(ratio_brut_pixels, 2),
            'ratio_brut_bytes': round(ratio_brut_bytes, 2),
            'ratio_effectif': round(original_size / compressed_size, 2),
            'original_size_bytes': original_size,
            'compressed_size_bytes': compressed_size,
            'time_encode_ms': round(t_enc * 1000, 2),
            'c_min': c_min,
            'c_max': c_max,
            'n_blocks': (n_h, n_w),
        }

        return compressed, metadata

    def decompress(self, bitstream: bytes, metadata: Dict[str, Any]) -> Tuple[np.ndarray, float]:
        t0 = time.perf_counter()

        raw_bytes = zlib.decompress(bitstream)

        magic, H, W, n_coeffs, bs, p1, p2, c_min, c_max = struct.unpack(
            '<4sIIBBBBff', raw_bytes[:24]
        )
        assert magic == b'HCVW'
        self.n_coeffs = n_coeffs
        self.block_size = bs
        n_h, n_w = metadata['n_blocks']
        n_total = n_h * n_w

        # Lire les coefficients uint16
        coeffs_uint16 = np.frombuffer(raw_bytes[24:], dtype=np.uint16)
        coeffs_norm = coeffs_uint16.astype(np.float64) / 65535.0
        coeffs = coeffs_norm * (c_max - c_min) + c_min
        coeffs = coeffs.reshape(n_total, self.n_coeffs)

        # Reconstruire
        reconstructed = np.zeros((H, W), dtype=np.float64)
        idx = 0
        for i in range(n_h):
            for j in range(n_w):
                c = coeffs[idx]
                if self.mode == 'projection':
                    block = self._decode_simple_projection(c)
                elif self.mode == 'interference':
                    block = self._decode_block_interference(c)
                elif self.mode == 'croisee':
                    block = self._decode_block_croisee(c)
                elif self.mode == 'modulation':
                    block = self._decode_block_modulation(c)
                reconstructed[i*bs:(i+1)*bs, j*bs:(j+1)*bs] = block
                idx += 1

        # Re-normaliser dans [0, 1] par bloc ou globalement
        r_min, r_max = reconstructed.min(), reconstructed.max()
        if r_max - r_min > 1e-12:
            reconstructed = (reconstructed - r_min) / (r_max - r_min)

        t_dec = time.perf_counter() - t0
        return np.clip(reconstructed, 0, 1), round(t_dec * 1000, 2)


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
# IMAGES DE TEST
# ==============================================================================

def create_all_images():
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

    cx, cy = W//2, H//2
    R = np.sqrt((X*W - cx)**2 + (Y*H - cy)**2) / W
    images['cercles'] = np.clip((np.sin(R * 20) + 1) / 2, 0, 1)

    images['texture_sinus'] = np.clip((np.sin(X*30) * np.cos(Y*25) + np.sin((X+Y)*15) + 2) / 4, 0, 1)

    np.random.seed(42)
    images['bruit'] = np.random.rand(H, W)

    # Portrait gaussien
    np.random.seed(123)
    portrait = np.zeros((H, W))
    for _ in range(40):
        cx_ = np.random.uniform(0.15, 0.85) * W
        cy_ = np.random.uniform(0.15, 0.85) * H
        sx = np.random.uniform(20, 60)
        sy = np.random.uniform(20, 60)
        amp = np.random.uniform(0.3, 1.0)
        portrait += amp * np.exp(-((X*W - cx_)**2 / (2*sx**2) + (Y*H - cy_)**2 / (2*sy**2)))
    images['gaussienne'] = np.clip((portrait - portrait.min()) / (portrait.max() - portrait.min() + 1e-12), 0, 1)

    return images


# ==============================================================================
# TEST PRINCIPAL
# ==============================================================================

def run_test():
    print("=" * 75)
    print("  TEST V1 ONDULATOIRE — Théorie des Interférences")
    print("  7 ondes harmoniques universelles — ZÉRO header hologramme")
    print("=" * 75)

    images = create_all_images()
    modes = ['projection', 'interference', 'modulation', 'croisee']

    all_summary = {}

    for mode in modes:
        comp = HCVCompressorV1Ondulatoire(mode=mode, block_size=8)
        print(f"\n{'='*70}")
        print(f"  MODE : {mode.upper()}  —  {comp.n_coeffs} coefficients/bloc")
        print(f"  Ratio brut coeffs : 64/{comp.n_coeffs} = {64.0/comp.n_coeffs:.1f}:1")
        print(f"  Ratio brut octets : 64/({comp.n_coeffs}×2) = {64.0/(comp.n_coeffs*2):.1f}:1")
        print(f"  {'Image':<16s} {'Ratio eff':>9s} {'PSNR':>9s} {'Comp(B)':>8s}")
        print(f"  {'-'*16} {'-'*9} {'-'*9} {'-'*8}")

        results = []
        for name, img in images.items():
            bs, meta = comp.compress(img)
            rec, t_dec = comp.decompress(bs, meta)
            psnr = compute_psnr(img, rec)

            results.append({
                'image': name,
                'ratio': meta['ratio_effectif'],
                'psnr': psnr,
                'comp_bytes': meta['compressed_size_bytes'],
            })
            psnr_str = f"{psnr:.2f} dB" if psnr != float('inf') else 'INF'
            print(f"  {name:<16s} {meta['ratio_effectif']:8.2f}x {psnr_str:>9s} {meta['compressed_size_bytes']:>8d}")

        avg_ratio = sum(r['ratio'] for r in results) / len(results)
        psnr_vals = [r['psnr'] for r in results if r['psnr'] != float('inf')]
        avg_psnr = sum(psnr_vals) / len(psnr_vals) if psnr_vals else float('inf')
        print(f"  {'-'*16} {'-'*9} {'-'*9}")
        print(f"  {'MOYENNE':<16s} {avg_ratio:8.2f}x {avg_psnr:8.2f} dB")

        all_summary[mode] = {'avg_ratio': avg_ratio, 'avg_psnr': avg_psnr, 'n_coeffs': comp.n_coeffs}

    # Comparaison finale
    print(f"\n\n{'='*75}")
    print("  COMPARAISON DES MODES ONDULATOIRES")
    print(f"  {'='*75}")
    print(f"\n  {'Mode':<16s} {'Coeffs':>7s} {'Brut oct':>8s} {'Ratio eff':>9s} {'PSNR moy':>9s}")
    print(f"  {'-'*16} {'-'*7} {'-'*8} {'-'*9} {'-'*9}")
    for mode in modes:
        s = all_summary[mode]
        brut = 64.0 / (s['n_coeffs'] * 2)
        psnr_str = f"{s['avg_psnr']:.2f} dB" if s['avg_psnr'] != float('inf') else 'INF'
        print(f"  {mode:<16s} {s['n_coeffs']:>7d} {brut:7.1f}x {s['avg_ratio']:8.2f}x {psnr_str:>9s}")

    print(f"\n  Rappel V1 originale (7 ondes, projection simple) : ~4.5 dB PSNR")
    print(f"  Rappel V2 SVD (base apprise, 64 coeffs header) : 58 dB à 50× (structuré)")
    print(f"  Objectif V1 ondulatoire : PSNR >> 4.5 dB sans header hologramme")
    print()


if __name__ == "__main__":
    run_test()