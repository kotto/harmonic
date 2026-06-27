#!/usr/bin/env python3
"""
QualityCompressor - Mode haute qualite pour usage professionnel
===============================================================
Cible : ratio <= 50:1 avec PSNR >= 30 dB sur images naturelles.
Standard broadcast (UIT-R BT.1888) : PSNR >= 35 dB.

Pipeline :
  1. Legere reduction spatiale K (~2:1) au lieu de K=0.02 (~50:1)
  2. HarmonicEncoder haute qualite (quality=85) -> ~25:1
  3. Total: 2 x 25 = ~50:1, PSNR ~32-38 dB

Modes disponibles :
  'broadcast'  : PSNR >= 35 dB, ratio ~15:1   (Netflix, TV broadcast)
  'pro'        : PSNR >= 30 dB, ratio ~50:1   (archivage professionnel)
  'preview'    : PSNR >= 25 dB, ratio ~150:1  (thumbnails, previews)
  'archive'    : ratio => 300:1, PSNR best-effort (stockage froid)
  'custom'     : parametres libres
"""

import numpy as np
import time
import logging
import struct
import io
from typing import Tuple, Dict, Any, Optional
from .harmonic_encoder import HarmonicEncoder, psnr as calc_psnr

logger = logging.getLogger(__name__)

# Pre-sets professionnels
QUALITY_PRESETS = {
    'broadcast': {
        'spatial_k': 0.70,   # reduction lineaire 70% -> ratio ~2:1 surface
        'enc_quality': 90,
        'min_psnr': 35.0,
        'target_ratio': 15.0,
        'description': 'Broadcast TV/OTT (PSNR >= 35 dB, ratio ~15:1)',
    },
    'pro': {
        'spatial_k': 0.45,   # ~5:1 spatial
        'enc_quality': 85,
        'min_psnr': 30.0,
        'target_ratio': 50.0,
        'description': 'Pro archivage (PSNR >= 30 dB, ratio ~50:1)',
    },
    'preview': {
        'spatial_k': 0.25,
        'enc_quality': 65,
        'min_psnr': 25.0,
        'target_ratio': 150.0,
        'description': 'Preview/CDN (PSNR >= 25 dB, ratio ~150:1)',
    },
    'archive': {
        'spatial_k': 0.14,   # K=0.02 equivalent
        'enc_quality': 50,
        'min_psnr': 15.0,
        'target_ratio': 500.0,
        'description': 'Cold storage (ratio ~500:1, perte acceptable)',
    },
}

QUALITY_MAGIC = b'HCQ\x01'  # Harmonic Codec Quality v1


def _resize_array(image: np.ndarray, scale: float) -> np.ndarray:
    """
    Redimensionne une image par interpolation bicubique (scipy).
    scale: facteur lineaire (ex: 0.5 = moitie de la taille)
    """
    if abs(scale - 1.0) < 0.01:
        return image.copy()
    H, W = image.shape[:2]
    nH = max(4, int(H * scale))
    nW = max(4, int(W * scale))

    try:
        from scipy.ndimage import zoom
        if len(image.shape) == 3:
            result = zoom(image, (scale, scale, 1.0), order=3, prefilter=False)
        else:
            result = zoom(image, (scale, scale), order=3, prefilter=False)
        return np.clip(result, 0.0, 1.0).astype(np.float32)
    except ImportError:
        # Fallback PIL
        from PIL import Image as PILImage
        pil = PILImage.fromarray((image * 255).astype(np.uint8))
        pil = pil.resize((nW, nH), PILImage.LANCZOS)
        return np.array(pil, dtype=np.float32) / 255.0


class QualityCompressor:
    """
    Compresseur haute qualite pour services professionnels.
    Combine reduction spatiale douce + HarmonicEncoder haute qualite.

    Usage:
        qc = QualityCompressor(mode='pro')
        data, meta = qc.compress(image)      # image: float32 [0,1] (H,W,3)
        restored, meta = qc.decompress(data) # restored: float32 [0,1] (H,W,3)

        # Avec validation PSNR automatique :
        data, meta = qc.compress(image, validate_psnr=True)
        print(meta['psnr_db'], meta['psnr_ok'])
    """

    def __init__(self, mode: str = 'pro',
                 spatial_k: Optional[float] = None,
                 enc_quality: Optional[int] = None):
        """
        Args:
            mode: 'broadcast'|'pro'|'preview'|'archive'|'custom'
            spatial_k: Override facteur de reduction spatiale (custom uniquement)
            enc_quality: Override qualite HarmonicEncoder (custom uniquement)
        """
        if mode not in QUALITY_PRESETS and mode != 'custom':
            raise ValueError(f"Mode inconnu: {mode}. Valides: {list(QUALITY_PRESETS)}")

        self.mode = mode

        if mode == 'custom':
            if spatial_k is None or enc_quality is None:
                raise ValueError("mode='custom' requiert spatial_k et enc_quality")
            self.spatial_k = float(spatial_k)
            self.enc_quality = int(enc_quality)
            self.min_psnr = 0.0
            self.target_ratio = (1.0 / max(1e-6, spatial_k ** 2)) * \
                                 HarmonicEncoder(enc_quality).estimate_ratio_from_quality()
        else:
            preset = QUALITY_PRESETS[mode]
            self.spatial_k = float(spatial_k or preset['spatial_k'])
            self.enc_quality = int(enc_quality or preset['enc_quality'])
            self.min_psnr = preset['min_psnr']
            self.target_ratio = preset['target_ratio']

        self._encoder = HarmonicEncoder(quality=self.enc_quality)
        logger.info(f"QualityCompressor[{mode}]: spatial_k={self.spatial_k:.2f}, "
                    f"enc_quality={self.enc_quality}, target_ratio~{self.target_ratio:.0f}:1")

    def compress(self, image: np.ndarray,
                 validate_psnr: bool = False) -> Tuple[bytes, Dict[str, Any]]:
        """
        Compresse une image en mode haute qualite.

        Args:
            image: (H, W, 3) float32 [0, 1]
            validate_psnr: Si True, decompresse et mesure le PSNR reel

        Returns:
            (bytes, meta)
        """
        t0 = time.time()
        H, W = image.shape[:2]
        original_bytes = image.nbytes

        # 1. Reduction spatiale douce
        if self.spatial_k < 0.99:
            reduced = _resize_array(image, self.spatial_k)
        else:
            reduced = image

        rH, rW = reduced.shape[:2]
        spatial_ratio = (H * W) / (rH * rW)

        # 2. Encodage harmonique haute qualite
        enc_bytes, enc_meta = self._encoder.encode(reduced)

        # 3. Encapsulation avec header original (pour decompression correcte)
        buf = io.BytesIO()
        buf.write(QUALITY_MAGIC)
        buf.write(struct.pack('<HHHHBf',
                               H, W,       # dimensions originales
                               rH, rW,     # dimensions reduites
                               self.enc_quality,
                               self.spatial_k))
        buf.write(struct.pack('<I', len(enc_bytes)))
        buf.write(enc_bytes)
        final_bytes = buf.getvalue()

        elapsed = time.time() - t0
        final_size = len(final_bytes)
        total_ratio = original_bytes / final_size

        meta = {
            'mode': self.mode,
            'compressor': 'QualityCompressor',
            'original_shape': image.shape,
            'reduced_shape': reduced.shape,
            'spatial_k': self.spatial_k,
            'enc_quality': self.enc_quality,
            'spatial_ratio': spatial_ratio,
            'enc_ratio': enc_meta['compression_ratio'],
            'total_ratio': total_ratio,
            'original_bytes': original_bytes,
            'final_bytes': final_size,
            'space_saved_pct': (1 - final_size / original_bytes) * 100,
            'compress_time_ms': elapsed * 1000,
            'fps': 1.0 / elapsed if elapsed > 0 else 0,
            'target_ratio': self.target_ratio,
            'target_met': total_ratio >= self.target_ratio * 0.8,
            'psnr_db': None,
            'psnr_ok': None,
        }

        # Validation PSNR optionnelle
        if validate_psnr:
            restored, _ = self.decompress(final_bytes)
            p = calc_psnr(image, restored)
            meta['psnr_db'] = p
            meta['psnr_ok'] = p >= self.min_psnr
            meta['psnr_min_required'] = self.min_psnr
            logger.info(f"PSNR={p:.1f} dB (min={self.min_psnr:.1f}) ratio={total_ratio:.1f}:1")

        return final_bytes, meta

    def decompress(self, data: bytes) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Decompresse depuis le format QualityCompressor.

        Returns:
            (image_float32 [0,1], meta)
        """
        t0 = time.time()
        buf = io.BytesIO(data)
        magic = buf.read(4)
        if magic != QUALITY_MAGIC:
            raise ValueError(f"Magic invalide: {magic!r}")

        H, W, rH, rW, enc_quality, spatial_k = struct.unpack('<HHHHBf', buf.read(13))
        enc_size = struct.unpack('<I', buf.read(4))[0]
        enc_bytes = buf.read(enc_size)

        # 1. Decodage harmonique
        dec = HarmonicEncoder(quality=enc_quality)
        reduced = dec.decode(enc_bytes)

        # 2. Upscale vers dimensions originales
        if rH != H or rW != W:
            restored = _resize_array(reduced, H / rH)
            # Trim/pad exact
            restored = restored[:H, :W]
        else:
            restored = reduced

        elapsed = time.time() - t0
        meta = {
            'original_shape': (H, W, 3),
            'reduced_shape': (rH, rW, 3),
            'spatial_k': spatial_k,
            'enc_quality': enc_quality,
            'decompress_time_ms': elapsed * 1000,
        }
        return np.clip(restored, 0.0, 1.0).astype(np.float32), meta

    @classmethod
    def describe_presets(cls) -> Dict[str, str]:
        """Retourne la description de tous les presets."""
        return {k: v['description'] for k, v in QUALITY_PRESETS.items()}

    def auto_tune(self, image: np.ndarray,
                  target_psnr: float = 33.0,
                  max_ratio: float = 50.0) -> 'QualityCompressor':
        """
        Trouve automatiquement les meilleurs parametres pour atteindre
        un compromis PSNR/ratio cible.

        Args:
            image: Image de reference (petit echantillon suffit)
            target_psnr: PSNR minimum desire
            max_ratio: Ratio maximum tolere

        Returns:
            Nouveau QualityCompressor avec parametres optimaux
        """
        best_qc = None
        best_score = -1.0

        # Grille de recherche
        for sk in [0.9, 0.7, 0.5, 0.35, 0.25]:
            for eq in [95, 90, 85, 80, 75]:
                qc = QualityCompressor(mode='custom', spatial_k=sk, enc_quality=eq)
                try:
                    data, meta = qc.compress(image, validate_psnr=True)
                    p = meta.get('psnr_db', 0)
                    r = meta['total_ratio']
                    if p is None:
                        continue
                    if p >= target_psnr and r <= max_ratio:
                        score = p / 10.0 + r / max_ratio
                        if score > best_score:
                            best_score = score
                            best_qc = (sk, eq)
                except Exception:
                    continue

        if best_qc:
            sk, eq = best_qc
            logger.info(f"auto_tune: optimal spatial_k={sk}, enc_quality={eq}")
            return QualityCompressor(mode='custom', spatial_k=sk, enc_quality=eq)
        else:
            logger.warning("auto_tune: aucun preset satisfaisant trouve, retour mode 'pro'")
            return QualityCompressor(mode='pro')


class QualityVideoCompressor:
    """
    Version video du QualityCompressor.
    Compresse/decompresse des sequences de frames.
    """

    def __init__(self, mode: str = 'pro'):
        self.qc = QualityCompressor(mode=mode)
        self.mode = mode

    def compress_frames(self, frames, max_workers: Optional[int] = None) -> Tuple[list, Dict]:
        """
        Compresse une liste de frames.

        Args:
            frames: liste de (H, W, 3) float32 [0, 1]
            max_workers: threads paralleles

        Returns:
            (list_of_bytes, stats)
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import os

        n = len(frames)
        workers = max_workers or min(16, (os.cpu_count() or 4) + 2)
        results = [None] * n
        t0 = time.time()

        def _enc(idx, frame):
            data, meta = self.qc.compress(frame)
            return idx, data, meta

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_enc, i, f): i for i, f in enumerate(frames)}
            for fut in as_completed(futures):
                idx, data, meta = fut.result()
                results[idx] = (data, meta)

        elapsed = time.time() - t0
        total_bytes = sum(len(r[0]) for r in results if r)
        raw_bytes = sum(f.nbytes for f in frames)
        ratio = raw_bytes / total_bytes if total_bytes else 0
        fps = n / elapsed if elapsed > 0 else 0

        stats = {
            'n_frames': n,
            'mode': self.mode,
            'total_ratio': ratio,
            'fps_compression': fps,
            'elapsed_s': elapsed,
            'raw_mb': raw_bytes / 1024**2,
            'compressed_kb': total_bytes / 1024,
        }
        return results, stats

    def decompress_frames(self, compressed_list) -> list:
        """
        Decompresse une liste de (bytes, meta).
        Returns liste de np.ndarray float32 [0,1].
        """
        return [self.qc.decompress(item[0])[0] for item in compressed_list if item]


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("=== QualityCompressor test ===")

    # Image naturelle simulee
    img = np.random.rand(720, 1280, 3).astype(np.float32) * 0.7 + 0.15

    print("\nPresets disponibles:")
    for name, desc in QualityCompressor.describe_presets().items():
        print(f"  {name:12s}: {desc}")

    print("\nBenchmark par preset:")
    print(f"  {'Mode':<12} {'Ratio':>8} {'PSNR':>8} {'Temps':>8} {'OK?'}")
    print("  " + "-" * 52)

    for mode in ['broadcast', 'pro', 'preview', 'archive']:
        qc = QualityCompressor(mode=mode)
        data, meta = qc.compress(img, validate_psnr=True)
        r = meta['total_ratio']
        p = meta['psnr_db'] or 0.0
        t = meta['compress_time_ms']
        ok = "[OK]" if meta.get('psnr_ok') else "[--]"
        print(f"  {mode:<12} {r:>7.1f}:1 {p:>7.1f}dB {t:>6.0f}ms {ok}")

    print("\n=== Done ===")
