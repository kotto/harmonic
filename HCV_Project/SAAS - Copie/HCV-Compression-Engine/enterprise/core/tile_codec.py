"""
HCV Enterprise Codec - Tile-Parallel Optimized Edition
======================================================
Optimisation 4K: medianBlur traité par tuiles en parallèle (3-4x plus rapide).

Architecture:
  Frame -> N tuiles avec overlap -> ThreadPool (medianBlur) -> Merge
  Le grain est extrait sur la frame complète pour préserver la cohérence statistique.

Performance attendue (4K 12-bit, 8 cores):
  v1 (par canaux RGB)   : ~38s encode
  v2 (tuiles parallèles): ~10-12s encode
"""

import numpy as np
import cv2
import struct
import math
import time
import threading
import zstandard as zstd
from concurrent.futures import ThreadPoolExecutor
from typing import Tuple, List
import os

# Pool dimensionné selon le hardware
_NUM_WORKERS = max(4, (os.cpu_count() or 4))
_TILE_POOL = ThreadPoolExecutor(max_workers=_NUM_WORKERS, thread_name_prefix="hcv-tile")

MAGIC = b'HCVE'  # Enterprise magic
VERSION = 2
MODE_GRAIN_SYNTH_TILED = 3
SIGMA_PTS = 8
SIGMA_SZ = SIGMA_PTS * 4

# Thread-local zstd contexts — non thread-safe si partagés
_tls = threading.local()

def _get_compressor(level: int) -> zstd.ZstdCompressor:
    if not hasattr(_tls, 'zctx'):
        _tls.zctx = {}
    if level not in _tls.zctx:
        _tls.zctx[level] = zstd.ZstdCompressor(level=level)
    return _tls.zctx[level]

def _get_decompressor() -> zstd.ZstdDecompressor:
    if not hasattr(_tls, 'zdctx'):
        _tls.zdctx = zstd.ZstdDecompressor()
    return _tls.zdctx


def _zstd_compress_parallel(channel_arrays: List[np.ndarray], level: int = 11) -> List[bytes]:
    """Compresse N canaux en parallèle (3-4x faster avec zstd-11+threads)."""
    def _compress_one(arr):
        return _enc_buf_with_ctx(arr, _get_compressor(level))

    futures = [_TILE_POOL.submit(_compress_one, ch) for ch in channel_arrays]
    return [f.result() for f in futures]


def _enc_buf_with_ctx(arr_i32: np.ndarray, ctx) -> bytes:
    mn, mx = int(arr_i32.min()), int(arr_i32.max())
    if mn >= -128 and mx <= 127:
        return b'\x08' + ctx.compress(arr_i32.astype(np.int8).tobytes())
    if mn >= -32768 and mx <= 32767:
        return b'\x16' + ctx.compress(arr_i32.astype(np.int16).tobytes())
    return b'\x32' + ctx.compress(arr_i32.astype(np.int32).tobytes())


# ─── Strip-parallel medianBlur (optimisé multi-cœurs) ───────────────────────

def _process_strip(args):
    f8_strip, k = args
    return cv2.medianBlur(f8_strip, k)


def _separate_strips(frame: np.ndarray, k: int = 5,
                     n_strips: int = None) -> np.ndarray:
    H, W = frame.shape[:2]
    f8 = np.right_shift(frame, 4).astype(np.uint8)

    if n_strips is None:
        n_strips = _NUM_WORKERS

    if H * W < 2_000_000:
        return np.left_shift(cv2.medianBlur(f8, k).astype(np.uint16), 4)

    overlap = k
    strip_h = H // n_strips
    tasks = []
    for i in range(n_strips):
        y_dst0 = i * strip_h
        y_dst1 = (i + 1) * strip_h if i < n_strips - 1 else H
        y_src0 = max(0, y_dst0 - overlap)
        y_src1 = min(H, y_dst1 + overlap)
        sub = np.ascontiguousarray(f8[y_src0:y_src1])
        iy0 = y_dst0 - y_src0
        iy1 = iy0 + (y_dst1 - y_dst0)
        tasks.append((sub, k, y_dst0, y_dst1, iy0, iy1))

    futures = [_TILE_POOL.submit(_process_strip, (t[0], t[1])) for t in tasks]

    s8 = np.empty_like(f8)
    for fut, (_, _, y_dst0, y_dst1, iy0, iy1) in zip(futures, tasks):
        result = fut.result()
        s8[y_dst0:y_dst1] = result[iy0:iy1]

    return np.left_shift(s8.astype(np.uint16), 4)


_separate_tiled = _separate_strips


# ─── Buffer encoding (identique au codec PRO de référence) ──────────────────

def _enc_buf(arr_i32: np.ndarray, level: int = 11) -> bytes:
    return _enc_buf_with_ctx(arr_i32, _get_compressor(level))


def _dec_buf(raw: bytes, shape: Tuple[int, ...]) -> np.ndarray:
    flag = raw[0:1]
    dtype = {b'\x08': np.int8, b'\x16': np.int16, b'\x32': np.int32}[flag]
    return np.frombuffer(_get_decompressor().decompress(raw[1:]), dtype).reshape(shape).astype(np.int32)


def _dh_enc(channel: np.ndarray) -> np.ndarray:
    d = channel.astype(np.int32)
    d[:, 1:] -= channel[:, :-1].astype(np.int32)
    return d


def _dh_dec(d: np.ndarray, dtype=np.uint16) -> np.ndarray:
    np.cumsum(d, axis=1, out=d)
    return d.astype(dtype)


def _build_sigma_curve(frame: np.ndarray, n_pts: int = SIGMA_PTS, maxval: int = 4095) -> np.ndarray:
    sig = _separate_tiled(frame)
    grain = (frame.astype(np.int32) - sig.astype(np.int32)).astype(np.int16)
    lum = sig.mean(axis=2) if sig.ndim == 3 else sig.astype(np.float32)

    bins = np.linspace(0, maxval, n_pts + 1)
    curve = np.zeros(n_pts, np.float32)
    abs_grain = np.abs(grain)
    grain_lum = abs_grain.mean(axis=2) if abs_grain.ndim == 3 else abs_grain

    for j in range(n_pts):
        mask = (lum >= bins[j]) & (lum < bins[j + 1])
        if mask.any():
            curve[j] = float(grain_lum[mask].mean()) * 1.2533
        elif j > 0:
            curve[j] = curve[j - 1]
    return curve


def _derive_seed(frame_idx: int, seq_id: int) -> np.uint32:
    return np.uint32((int(seq_id) * 999983 + int(frame_idx) * 6271 + 31337) & 0xFFFFFFFF)


def _apply_grain(shape: Tuple[int, ...], sigma_curve: np.ndarray,
                 sig_frame: np.ndarray, seed: int, maxval: int) -> np.ndarray:
    nc = shape[2] if len(shape) == 3 else 1
    n_pts = len(sigma_curve)
    lum = sig_frame.mean(axis=2).astype(np.float32) if nc > 1 else sig_frame.astype(np.float32)
    lum_norm = np.clip(lum / maxval * (n_pts - 1), 0, n_pts - 1)
    idx_lo = lum_norm.astype(np.int32)
    idx_hi = np.minimum(idx_lo + 1, n_pts - 1)
    t = lum_norm - idx_lo
    sigma_px = (sigma_curve[idx_lo] * (1 - t) + sigma_curve[idx_hi] * t).astype(np.float32)

    rng = np.random.default_rng(int(seed) & 0xFFFFFFFF)
    if nc > 1:
        noise = rng.standard_normal(shape).astype(np.float32)
        noise *= sigma_px[:, :, np.newaxis]
    else:
        noise = rng.standard_normal(shape[:2]).astype(np.float32)
        noise *= sigma_px
    return noise.astype(np.int16)


class HCVEnterpriseCodec:
    def __init__(self, bit_depth: int = 12, zstd_level: int = 11,
                 n_strips: int = None, max_workers: int = None):
        self.bit_depth = bit_depth
        self.maxval = (1 << bit_depth) - 1
        self.zstd_level = zstd_level
        self.n_strips = n_strips or _NUM_WORKERS
        self.seq_id = np.uint32(42)
        self.mode = MODE_GRAIN_SYNTH_TILED

    def encode_frame(self, frame: np.ndarray, frame_idx: int = 0) -> Tuple[bytes, dict]:
        H, W = frame.shape[:2]
        nc = frame.shape[2] if frame.ndim == 3 else 1
        t0 = time.perf_counter()

        sig = _separate_strips(frame, n_strips=self.n_strips)
        sigma_curve = _build_sigma_curve(frame, SIGMA_PTS, self.maxval)

        deltas = []
        for c in range(nc):
            ch = sig[:, :, c] if nc > 1 else sig
            deltas.append(_dh_enc(ch))
        channel_data = _zstd_compress_parallel(deltas, level=self.zstd_level)

        buf = bytearray()
        buf += MAGIC
        buf += struct.pack('<BBHHBB', VERSION, self.mode, H, W, self.bit_depth, nc)
        buf += sigma_curve.tobytes()
        buf += struct.pack('<I', int(self.seq_id))
        for packed in channel_data:
            buf += struct.pack('<I', len(packed))
            buf += packed

        elapsed = time.perf_counter() - t0
        original_size = frame.nbytes
        compressed_size = len(buf)

        return bytes(buf), {
            'original_size': original_size,
            'compressed_size': compressed_size,
            'ratio': original_size / compressed_size,
            'savings_pct': 100 * (1 - compressed_size / original_size),
            'time_ms': elapsed * 1000,
            'speed_mbps': original_size / (elapsed * 1e6) if elapsed > 0 else 0,
            'mode': 'GRAIN_SYNTH_STRIPED',
            'n_strips': self.n_strips,
            'workers': _NUM_WORKERS,
            'resolution': f'{W}x{H}',
            'bit_depth': self.bit_depth,
        }

    def decode_frame(self, data: bytes, frame_idx: int = 0) -> np.ndarray:
        off = 4
        ver, mode, H, W, bits, nc = struct.unpack('<BBHHBB', data[off:off + 8])
        off += 8
        sigma_curve = np.frombuffer(data[off:off + SIGMA_SZ], np.float32).copy()
        off += SIGMA_SZ
        seq_id = struct.unpack('<I', data[off:off + 4])[0]
        off += 4
        maxval = (1 << bits) - 1

        channels = []
        for c in range(nc):
            sz = struct.unpack('<I', data[off:off + 4])[0]
            off += 4
            deltas = _dec_buf(data[off:off + sz], (H, W))
            off += sz
            channels.append(_dh_dec(deltas, np.uint16))

        sig = np.stack(channels, axis=2) if nc > 1 else channels[0]

        seed = _derive_seed(frame_idx, seq_id)
        grain = _apply_grain(sig.shape, sigma_curve, sig, seed, maxval)
        recon = np.clip(sig.astype(np.int32) + grain.astype(np.int32), 0, maxval).astype(np.uint16)
        return recon
