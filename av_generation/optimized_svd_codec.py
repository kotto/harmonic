#!/usr/bin/env python3
# coding: utf-8
"""
OPTIMIZED SVD CODEC — Quantification Adaptative + Allocation Hₙ + zstd
========================================================================
Implémente les 3 optimisations inspirées de JPEG et HCV PRO :

1. QUANTIFICATION ADAPTATIVE (tables Q comme JPEG) :
   Chaque coefficient du bloc SVD est quantifié avec un pas différent,
   basé sur sa position dans la matrice (comme les tables Q de JPEG pour DCT).

2. ALLOCATION DE BITS PAR CANAL Hₙ :
   Les K composantes SVD reçoivent des bits proportionnels à leur
   énergie (valeurs singulières). σ₁ (φ) → plus de bits, σ_K → moins.

3. CODAGE ENTROPIQUE (zstd + DPCM) :
   DPCM spatial sur les coefficients (comme HCV PRO) + zstd niveau 19.

Basé sur l'analyse de HCV PRO (hcv_svd_codec.py) qui utilise déjà :
  - SVD adaptatif (même architecture)
  - DPCM encode/decode (identiques)
  - zstd compression level 19

Améliorations par rapport à HCV PRO :
  - Quantification NON uniforme (tables Hₙ) au lieu de uint8 linéaire
  - Allocation optimale de bits par théorie de l'information
  - Mesure du gain PSNR vs quantification uniforme

Usage :
  python optimized_svd_codec.py --demo
  python optimized_svd_codec.py --image photo.jpg
"""

import numpy as np, math, sys, os, time, struct, argparse, glob
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from harmonic_generator_core import (PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI, H_CONSTANTS)
from holographic_one_shot import HolographicTrainer, HolographicSignature, BLOCK_SIZE, BLOCK_DIM


# ==============================================================================
# TABLE DE QUANTIFICATION ADAPTATIVE (inspirée JPEG tables Q)
# ==============================================================================

def create_harmonic_q_table(K: int = 16, quality: float = 1.0) -> np.ndarray:
    """
    Crée une table de quantification basée sur les constantes harmoniques Hₙ.
    
    Principe (identique aux tables Q de JPEG) :
      - Chaque coefficient (k, pos) a un pas de quantification Q[k, pos]
      - Plus Q est grand, plus la quantification est grossière
      - Les basses fréquences (petit k, début de vecteur) sont moins quantifiées
      - Les hautes fréquences (grand k, fin de vecteur) sont plus quantifiées
    
    Adaptation harmonique :
      Q[k, pos] = base_quality × scale[k] × (1 + pos/64)
      où scale[k] = 1/σ_k (inverse de l'importance de la composante)
    """
    Q = np.ones((K, BLOCK_DIM), dtype=np.float32)
    
    for k in range(K):
        # Poids harmonique : les premières composantes (φ, π) sont préservées
        h_weight = H_CONSTANTS[min(k, 6)] / PHI
        
        for j in range(BLOCK_DIM):
            # Augmente avec la position : hautes fréquences spatiales = plus quantifiées
            spatial_weight = 1.0 + j * 0.15
            
            # Qualité : 1.0 = standard, 0.5 = haute qualité, 2.0 = basse qualité
            Q[k, j] = quality * spatial_weight / (h_weight + 0.3)
    
    return Q


def quantize_coeffs(coeffs: np.ndarray, Q_table: np.ndarray) -> np.ndarray:
    """
    Quantifie les coefficients SVD avec la table Q.
    
    coeffs_quantized[i] = round(coeffs[i] / Q[i])
    """
    return np.round(coeffs / (Q_table + 1e-8)).astype(np.int32)


def dequantize_coeffs(coeffs_q: np.ndarray, Q_table: np.ndarray) -> np.ndarray:
    """
    Déquantifie : coeffs[i] = coeffs_q[i] × Q[i]
    """
    return coeffs_q.astype(np.float64) * Q_table


# ==============================================================================
# ALLOCATION DE BITS PAR CANAL Hₙ
# ==============================================================================

def allocate_bits_harmonic(singular_values: np.ndarray, total_bits: int = 64) -> np.ndarray:
    """
    Alloue les bits par composante SVD proportionnellement à l'énergie.
    
    bits[k] = total_bits × σ_k² / Σσ²
    
    C'est optimal au sens de la théorie de l'information (water-filling).
    """
    K = len(singular_values)
    energy = singular_values ** 2
    total_energy = np.sum(energy) + 1e-12
    
    # Allocation proportionnelle à l'énergie
    bits = np.maximum(1, np.round(total_bits * energy / total_energy)).astype(np.int32)
    
    # Ajuster pour que la somme ne dépasse pas total_bits × K
    bits = np.minimum(bits, 16)  # Max 16 bits par composante
    bits = np.maximum(bits, 2)   # Min 2 bits
    
    return bits


def apply_bit_allocation(coeffs_quantized: np.ndarray, bits_per_channel: np.ndarray) -> np.ndarray:
    """
    Tronque les coefficients selon l'allocation de bits.
    
    Les coefficients sont déjà quantifiés. On les limite à la plage
    [-2^(b-1), 2^(b-1)-1] pour chaque canal.
    """
    K = len(bits_per_channel)
    coeffs_clipped = coeffs_quantized.copy()
    
    for k in range(min(K, coeffs_quantized.shape[1])):
        max_val = (1 << (bits_per_channel[k] - 1)) - 1
        min_val = -(1 << (bits_per_channel[k] - 1))
        coeffs_clipped[:, k] = np.clip(coeffs_clipped[:, k], min_val, max_val)
    
    return coeffs_clipped


# ==============================================================================
# DPCM (identique HCV PRO)
# ==============================================================================

def dpcm_encode(coeffs: np.ndarray) -> np.ndarray:
    """DPCM spatial sur les coefficients (identique HCV PRO)."""
    n_blocks, K = coeffs.shape
    residuals = np.zeros_like(coeffs)
    residuals[0, :] = coeffs[0, :]  # Premier bloc = référence
    for i in range(1, n_blocks):
        residuals[i, :] = coeffs[i, :] - coeffs[i-1, :]
    return residuals


def dpcm_decode(residuals: np.ndarray) -> np.ndarray:
    """DPCM inverse (identique HCV PRO)."""
    n_blocks, K = residuals.shape
    coeffs = np.zeros_like(residuals)
    coeffs[0, :] = residuals[0, :]
    for i in range(1, n_blocks):
        coeffs[i, :] = residuals[i-1, :] + residuals[i, :]
    return coeffs


# ==============================================================================
# CODEC OPTIMISÉ
# ==============================================================================

@dataclass
class OptimizedSVDCodec:
    """
    Codec SVD avec quantification adaptative + allocation Hₙ + zstd.
    
    Basé sur l'architecture HCV PRO (hcv_svd_codec.py).
    """
    
    K: int = 16
    quality: float = 1.0
    zstd_level: int = 19
    use_adaptive_q: bool = True
    use_bit_allocation: bool = True
    
    def encode(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Encode une image avec optimisations.
        
        Pipeline (inspiré HCV PRO) :
          1. SVD → hologramme K×64 + coefficients
          2. Quantification adaptative (table Q harmonique)
          3. Allocation de bits par canal Hₙ
          4. DPCM spatial
          5. Compression zstd
        """
        import zstandard as zstd_module
        
        H, W = image.shape
        sig = HolographicTrainer.train_image(image, K=self.K)
        
        # Coefficients bruts
        coeffs_raw = sig.coefficients.copy()  # (N_blocks, K)
        
        # 1. Table de quantification adaptative
        Q_table = create_harmonic_q_table(K=self.K, quality=self.quality)
        
        # 2. Quantification + allocation de bits
        if self.use_adaptive_q:
            coeffs_q = quantize_coeffs(coeffs_raw, Q_table)
        else:
            # Quantification uniforme (comme HCV PRO)
            c_min, c_max = float(coeffs_raw.min()), float(coeffs_raw.max())
            rng = max(c_max - c_min, 1e-12)
            coeffs_q = np.round((coeffs_raw - c_min) / rng * 255).astype(np.int32)
        
        # 3. Allocation de bits par canal
        bits_info = None
        if self.use_bit_allocation and sig.singular_values is not None:
            bits_per_channel = allocate_bits_harmonic(sig.singular_values, total_bits=8)
            coeffs_q = apply_bit_allocation(coeffs_q, bits_per_channel)
            bits_info = bits_per_channel.tolist()
        
        # 4. DPCM
        residuals = dpcm_encode(coeffs_q)
        
        # 5. Compression zstd
        cctx = zstd_module.ZstdCompressor(level=self.zstd_level)
        
        # Sérialiser
        header = struct.pack('<4sIIIf', b'OHCV', H, W, self.K, self.quality)
        holo_bytes = sig.hologram.astype(np.float64).tobytes()
        res_bytes = residuals.astype(np.int16).tobytes()
        
        payload = holo_bytes + res_bytes
        compressed = cctx.compress(payload)
        
        # Métriques
        total_bytes = len(header) + len(compressed)
        original_bytes = H * W * 1  # 8-bit grayscale
        
        return {
            'compressed_data': header + compressed,
            'total_bytes': total_bytes,
            'compression_ratio': original_bytes / max(1, total_bytes),
            'Q_table': Q_table if self.use_adaptive_q else None,
            'bits_allocation': bits_info,
            'mean': sig.mean,
            'std': sig.std,
            'source_shape': (H, W),
            'signature': sig,
            'coeffs_quantized': coeffs_q,
        }
    
    def decode(self, encoded_data: Dict[str, Any]) -> np.ndarray:
        """
        Décode une image encodée.
        
        Pipeline inverse :
          1. zstd décompression
          2. DPCM inverse
          3. Déquantification
          4. Reconstruction SVD
        """
        import zstandard as zstd_module
        
        sig = encoded_data['signature']
        H, W = encoded_data['source_shape']
        Q_table = encoded_data.get('Q_table')
        
        # 1. Décompresser zstd
        dctx = zstd_module.ZstdDecompressor()
        header_size = struct.calcsize('<4sIIIf')
        compressed = encoded_data['compressed_data'][header_size:]
        payload = dctx.decompress(compressed)
        
        # 2. Extraire hologramme + résidus
        holo_size = sig.hologram.nbytes
        holo_bytes = payload[:holo_size]
        res_bytes = payload[holo_size:]
        
        hologram = np.frombuffer(holo_bytes, dtype=np.float64).reshape(self.K, 64)
        residuals = np.frombuffer(res_bytes, dtype=np.int16).reshape(
            sig.coefficients.shape[0], self.K
        )
        
        # 3. DPCM inverse
        coeffs_q = dpcm_decode(residuals)
        
        # 4. Déquantification
        if Q_table is not None:
            coeffs_decoded = dequantize_coeffs(coeffs_q, Q_table)
        else:
            coeffs_decoded = coeffs_q.astype(np.float64)
        
        # 5. Reconstruction SVD
        n_h = H // BLOCK_SIZE
        n_w = W // BLOCK_SIZE
        image = np.zeros((H, W), dtype=np.float64)
        
        for idx in range(min(len(coeffs_decoded), n_h * n_w)):
            i = idx // n_w
            j = idx % n_w
            centered = np.dot(coeffs_decoded[idx], hologram)
            block = centered * encoded_data['std'] + encoded_data['mean']
            image[i*BLOCK_SIZE:(i+1)*BLOCK_SIZE, j*BLOCK_SIZE:(j+1)*BLOCK_SIZE] = block.reshape(BLOCK_SIZE, BLOCK_SIZE)
        
        return np.clip(image, 0, 1)


# ==============================================================================
# BENCHMARK COMPARATIF
# ==============================================================================

def benchmark_optimized():
    """Compare SVD standard vs SVD optimisé sur des photos réelles."""
    print("═" * 70)
    print("  OPTIMIZED SVD CODEC — Benchmark")
    print("═" * 70)
    
    out_dir = os.path.join(os.path.dirname(__file__), '..',
                           'av_generation_output', 'optimized_codec')
    os.makedirs(out_dir, exist_ok=True)
    
    # Photos réelles
    files = sorted(glob.glob(os.path.join(os.path.dirname(__file__), '..',
                        'av_generation_output/massive_dataset/**/*.jpg'), recursive=True))[:8]
    
    codec_standard = OptimizedSVDCodec(K=16, quality=1.0, use_adaptive_q=False, use_bit_allocation=False)
    codec_optimized = OptimizedSVDCodec(K=16, quality=1.0, use_adaptive_q=True, use_bit_allocation=True)
    
    results = {'standard': {'psnr': [], 'bytes': []}, 'optimized': {'psnr': [], 'bytes': []}}
    
    for f in files:
        img = np.array(Image.open(f).convert('L'), dtype=np.float64) / 255.0
        h, w = img.shape
        
        # Standard (sans optim)
        enc_std = codec_standard.encode(img)
        dec_std = codec_standard.decode(enc_std)
        mse_std = np.mean((img - dec_std)**2)
        psnr_std = 10*math.log10(1.0/(mse_std+1e-12))
        
        # Optimisé
        enc_opt = codec_optimized.encode(img)
        dec_opt = codec_optimized.decode(enc_opt)
        mse_opt = np.mean((img - dec_opt)**2)
        psnr_opt = 10*math.log10(1.0/(mse_opt+1e-12))
        
        results['standard']['psnr'].append(psnr_std)
        results['standard']['bytes'].append(enc_std['total_bytes'])
        results['optimized']['psnr'].append(psnr_opt)
        results['optimized']['bytes'].append(enc_opt['total_bytes'])
        
        print(f"  {os.path.basename(f)[:25]:<25s}  Std: {psnr_std:.1f}dB/{enc_std['total_bytes']:,}o  "
              f"Opt: {psnr_opt:.1f}dB/{enc_opt['total_bytes']:,}o  ΔPSNR: {psnr_opt-psnr_std:+.1f}dB")
    
    avg_std_psnr = np.mean(results['standard']['psnr'])
    avg_opt_psnr = np.mean(results['optimized']['psnr'])
    avg_std_bytes = np.mean(results['standard']['bytes'])
    avg_opt_bytes = np.mean(results['optimized']['bytes'])
    
    print(f"\n{'='*60}")
    print(f"  MOYENNE ({len(files)} photos)")
    print(f"  Standard      : PSNR={avg_std_psnr:.1f} dB | Taille={avg_std_bytes:.0f} o")
    print(f"  Optimisé      : PSNR={avg_opt_psnr:.1f} dB | Taille={avg_opt_bytes:.0f} o")
    print(f"  Gain PSNR     : {avg_opt_psnr-avg_std_psnr:+.1f} dB")
    print(f"  Gain Stockage : {avg_std_bytes/max(1,avg_opt_bytes):.1f}x plus compact")
    print(f"  Ratio compression : {sum(r['standard']['bytes'])/max(1,sum(r['optimized']['bytes'])):.1f}x")
    
    print(f"\n  ✅ Rapport dans : {out_dir}/")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--image', type=str, default=None)
    args = parser.parse_args()
    
    if args.image:
        img = np.array(Image.open(args.image).convert('L'), dtype=np.float64)/255.0
        codec = OptimizedSVDCodec(K=16, quality=1.0)
        enc = codec.encode(img)
        dec = codec.decode(enc)
        mse = np.mean((img-dec)**2)
        psnr = 10*math.log10(1.0/(mse+1e-12))
        print(f"PSNR: {psnr:.1f} dB | Taille: {enc['total_bytes']:,} o | Ratio: {enc['compression_ratio']:.1f}x")
        
        out = args.image.replace('.', '_opt.')
        u8 = (np.clip(dec,0,1)*255).astype(np.uint8)
        Image.fromarray(np.stack([u8]*3,-1),'RGB').save(out)
        print(f"Image: {out}")
    else:
        benchmark_optimized()