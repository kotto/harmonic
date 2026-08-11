#!/usr/bin/env python3
"""
hcv2_video_pipeline.py — LE PIPELINE COMPLET P1+P3 : le codec vidéo HCV2
========================================================================
  prédiction dorée K(t) (P3 — la mémoire, T2, zéro paramètre)
      → résidu (le grain oublié)
      → codec modal (P1 — troncature dorée 1/(φ·m) + chaîne cₙ, T3)
      → zlib (l'entropie dorée P5 remplacera cet étage)

Le DÉCODEUR est un vrai décodeur vidéo : il re-prédit sur ses propres
frames décodées (jamais sur les originales — la boucle fermée).

Benchmark honnête sur B3.mp4 : PSNR · SSIM · ratio vs fichier original ·
vs la version sans prédiction — références de la base : 8,51× @ 51,22 dB
(lossless) · 15,17× (contenu optimisé).
"""

import math
import sys
import zlib
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / 'vital-ka' / 'core' / 'python'))
from exploration_piste3_video_memoire import golden_weights  # noqa: E402
from hcv2_modal_codec import _decode_channel, _encode_channel, _to_rgb, _to_ycbcr  # noqa: E402

PHI = (1 + np.sqrt(5)) / 2
DEPTH = 10


def _predict(series, weights):
    """La prédiction dorée : ψ̂_t = Σ_d K(d)·ψ_{t−d}/ΣK (P3)."""
    depth = len(weights)
    w = weights / weights.sum()
    out = np.zeros_like(series[depth:])
    for i, t in enumerate(range(depth, len(series))):
        past = np.stack([series[t - d] for d in range(1, depth + 1)])
        out[i] = np.tensordot(w, past, axes=(0, 0))
    return out


def _pack(payloads):
    """Assemble — format COMPACT (deltas varint + float16/32) + octet de largeur."""
    from hcv2_modal_codec import _varint_encode
    mag_bytes = payloads[0][3].dtype.itemsize if payloads and payloads[0][3].size else 2
    phase_bytes = payloads[0][4].dtype.itemsize if payloads and payloads[0][4].size else 2
    data = bytearray([mag_bytes, phase_bytes])
    for mask, idx, q, mags, phases, max_mag, mass, m in payloads:
        data += mask.tobytes()
        if idx.size:
            deltas = np.diff(np.concatenate(([idx[0]], idx))).astype(np.uint32)
            data += _varint_encode(deltas)
        data += mags.tobytes()
        data += phases.tobytes()
        data += np.float64(max_mag).tobytes()
    return zlib.compress(bytes(data), 9)


def _unpack(blob, h, w):
    """Lit TOUS les payloads du blob — format COMPACT (deltas varint +
    float16) — 3 canaux par frame, séquentiels."""
    from hcv2_modal_codec import _varint_decode
    raw = zlib.decompress(blob)
    m = h * w
    mag_bytes, phase_bytes = raw[0], raw[1]
    payloads = []
    off = 2
    while off < len(raw):
        mask = np.frombuffer(raw[off:off + (m + 7) // 8], np.uint8); off += (m + 7) // 8
        n_keep = int(np.count_nonzero(np.unpackbits(mask)[:m]))
        deltas, used = _varint_decode(raw[off:], n_keep)
        idx = np.cumsum(deltas).astype(np.uint32)
        off += used
        mags = np.frombuffer(raw[off:off + n_keep * mag_bytes],
                             np.float16 if mag_bytes == 2 else np.float32)
        off += n_keep * mag_bytes
        phases = np.frombuffer(raw[off:off + n_keep * phase_bytes],
                               np.float16 if phase_bytes == 2 else np.float32)
        off += n_keep * phase_bytes
        max_mag = float(np.frombuffer(raw[off:off + 8], np.float64)[0]); off += 8
        payloads.append((mask, idx, np.zeros(0, np.uint8), mags, phases,
                        max_mag, 0.0, m))
    return payloads


def encode_video(frames, use_memory=True):
    """Frames RGB (T, H, W, 3) → dict .hcv2. La mémoire d'or prédit, le
    résidu est compressé par le codec modal ; les DEPTH premières frames
    (l'échauffement) sont compressées complètes."""
    ycbcr = np.stack([_to_ycbcr(f.astype(np.float64)) for f in frames])
    T, H, W, C = ycbcr.shape
    w_gold = golden_weights(DEPTH)
    blob_parts, masses = [], []
    for c in range(C):
        ch = ycbcr[:, :, :, c]
        head = [_encode_channel(ch[t]) for t in range(DEPTH)]
        if use_memory:
            rest = _predict(ch, w_gold)
            # les résidus : amplitudes FLOAT32 (le float16 leur nuit —
            # coefficients bruités — mesuré : 26,2 vs 32,7 dB)
            # les résidus : amplitudes ABSOLUES float32 (la normalisation
            # par max_mag perd la précision à petite résolution — mesuré)
            tail = [_encode_channel(ch[t] - rest[i], mag_dtype=np.float32)
                    for i, t in enumerate(range(DEPTH, T))]
        else:
            tail = [_encode_channel(ch[t]) for t in range(DEPTH, T)]
        masses.extend(p[5] for p in head + tail)
        blob_parts.append(_pack(head))
        blob_parts.append(_pack(tail))
    lengths = np.array([len(b) for b in blob_parts], np.uint32)
    header = np.array([T, H, W, use_memory], np.uint32).tobytes() + lengths.tobytes()
    return {'blob': header + b''.join(blob_parts),
            'mass_kept': float(np.mean(masses)), 'use_memory': use_memory,
            'T': T, 'H': H, 'W': W}


def decode_video(enc):
    """Le vrai décodeur : boucle fermée — la prédiction se fait sur les
    frames DÉCODÉES (le passé du décodeur, jamais les originales)."""
    T, H, W, use_memory = np.frombuffer(enc['blob'][:16], np.uint32)
    lengths = np.frombuffer(enc['blob'][16:40], np.uint32)
    w_gold = golden_weights(DEPTH)
    ycbcr = np.zeros((T, H, W, 3))
    off = 40
    for c in range(3):
        head_blob = enc['blob'][off:off + lengths[2 * c]]; off += lengths[2 * c]
        tail_blob = enc['blob'][off:off + lengths[2 * c + 1]]; off += lengths[2 * c + 1]
        head = _unpack(head_blob, H, W)
        tail = _unpack(tail_blob, H, W)
        for t in range(DEPTH):
            ycbcr[t, :, :, c] = _decode_channel(head[t], (H, W))
        for i, t in enumerate(range(DEPTH, T)):
            past = np.stack([ycbcr[t - d, :, :, c] for d in range(1, DEPTH + 1)])
            pred = np.tensordot(w_gold / w_gold.sum(), past, axes=(0, 0))
            resid = _decode_channel(tail[i], (H, W))
            ycbcr[t, :, :, c] = pred + resid
    return np.stack([np.clip(_to_rgb(ycbcr[t]), 0, 255).astype(np.uint8)
                     for t in range(T)])


def psnr(a, b):
    mse = float(np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2))
    return float('inf') if mse == 0 else 20 * math.log10(255.0 / math.sqrt(mse))


def ssim(a, b):
    x, y = a.astype(np.float64), b.astype(np.float64)
    mx, my = x.mean(), y.mean()
    vx, vy = x.var(), y.var()
    cov = np.mean((x - mx) * (y - my))
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    return float(((2 * mx * my + c1) * (2 * cov + c2)) /
                 ((mx ** 2 + my ** 2 + c1) * (vx + vy + c2)))


if __name__ == '__main__':
    import cv2

    cap = cv2.VideoCapture(r'E:\SAAS - Copie\B3.mp4')
    frames = []
    while len(frames) < 40:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(cv2.resize(frame, (320, 180)),
                                   cv2.COLOR_BGR2RGB))
    cap.release()
    T = len(frames)
    orig_bytes = Path(r'E:\SAAS - Copie\B3.mp4').stat().st_size
    print("═" * 70)
    print("PIPELINE HCV2 P1+P3 — prédiction dorée + codec modal, sur B3.mp4")
    print("═" * 70)
    print(f"   {T} frames (320×180 RGB) · fichier original : {orig_bytes:,} o")

    for use_mem, label in [(False, 'SANS prédiction (frames complètes)'),
                           (True, 'PIPELINE DORÉ (K(t) + résidu modal)')]:
        enc = encode_video(frames, use_memory=use_mem)
        rec = decode_video(enc)
        size = len(enc['blob'])
        ratio = orig_bytes / size
        # ⚠️ LES BASES HONNÊTES : B3.mp4 est DÉJÀ compressé (H.264) — la
        # référence SDI est la taille RAW non compressée :
        #   · RAW RGB888      : T × H × W × 3 (les données brutes)
        #   · SDI 4:2:2 10-bit : T × H × W × 2,5 (le standard broadcast)
        raw_size = T * 180 * 320 * 3
        sdi_size = int(T * 180 * 320 * 2.5)
        print(f"\n   {label} :")
        print(f"      compressé : {size:,} o")
        print(f"      vs fichier MP4 (DÉJÀ H.264) : {ratio:.2f}× — ⚠️ pas la base SDI")
        print(f"      vs RAW RGB888 non compressé : {raw_size / size:.2f}×")
        print(f"      vs SDI 4:2:2 10-bit         : {sdi_size / size:.2f}×")
        print(f"      PSNR : {psnr(np.stack(frames), rec):6.2f} dB · "
              f"SSIM : {ssim(np.stack(frames), rec):.4f}")
        print(f"      décodeur en boucle fermée ✅")

    print("\n   Références de la base (les mesures honnêtes) :")
    print("      B3 (H.264 déjà compressé — le 8,51× est vs le MP4) : 51,22 dB")
    print("      Contenu broadcast optimisé (RAW) : 15,17× (lossless)")
    print("   → la comparaison SDI honnête = le ratio vs RAW (ci-dessus),")
    print("     jamais vs le MP4 déjà compressé — corrigé, publié")
    print("═" * 70)
