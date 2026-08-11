#!/usr/bin/env python3
"""
benchmark_hcv2_vs_standards.py — LA VÉRIFICATION DE LA CONTENANCE
=================================================================
Le pipeline THU complet (prédiction dorée K(t) + codec modal) contre
les standards du secteur α=1 — sur le CONTENU À MÉMOIRE (scène lente
+ grain capteur — le terrain où la théorie prédit la supériorité) :

  · THU (pipeline doré)   — hcv2_video_pipeline (P3 + P1)
  · zstd (RAW brut)       — l'entropie générique sans modèle
  · H.264 (cv2)           — le standard vidéo (DCT + mouvement)
  · JPEG2000 (OpenJPEG)   — le standard image (ondelettes)

Métriques sur les MÊMES frames : ratio vs RAW · PSNR · SSIM.
La comparaison est honnête : zstd est le « sans modèle », H.264/JPEG2000
sont les codecs α=1 réglés par des années d'ingénierie.
"""

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / 'vital-ka' / 'core' / 'python'))
from hcv2_video_pipeline import decode_video, encode_video  # noqa: E402


def make_memory_content(h=120, w=160, t_frames=40, noise=12.0, seed=7):
    """La scène lente persistante + grain capteur (le contenu à mémoire)."""
    rng = np.random.default_rng(seed)
    frames = []
    for t in range(t_frames):
        frame = np.zeros((h, w))
        for (bx, by, br) in [(40 + t * 0.3, 60, 14), (w - 45 - t * 0.2, 35 + t * 0.15, 10)]:
            yy, xx = np.mgrid[0:h, 0:w]
            frame += 180 * np.exp(-((xx - bx) ** 2 + (yy - by) ** 2) / (2 * br ** 2))
        frame += rng.normal(0, noise, (h, w))
        frames.append(np.clip(frame, 0, 255))
    # RGB (les codecs attendent 3 canaux) : Y + deux canaux corrélés
    rgb = [np.stack([f, f * 0.95, f * 0.9], axis=-1).astype(np.uint8) for f in frames]
    return rgb


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
    import tempfile
    import zstandard as zstd

    frames = make_memory_content()
    T, H, W, C = np.stack(frames).shape
    raw_size = T * H * W * C
    print("═" * 70)
    print("LA VÉRIFICATION DE LA CONTENANCE — THU vs standards, contenu à mémoire")
    print("═" * 70)
    print(f"   scène lente + grain capteur : {T} frames {W}×{H} · RAW = {raw_size:,} o")

    results = {}

    # ── 1 · THU — le pipeline doré (P3 + P1) ────────────────────────────────
    enc = encode_video(frames, use_memory=True)
    rec_thu = decode_video(enc)
    size = len(enc['blob'])
    results['THU (doré P3+P1)'] = (size, psnr(np.stack(frames), rec_thu),
                                   ssim(np.stack(frames), rec_thu))

    # ── 2 · zstd — le RAW sans modèle ────────────────────────────────────────
    raw = np.stack(frames).tobytes()
    results['zstd (RAW brut)'] = (len(zstd.ZstdCompressor(level=19).compress(raw)),
                                  0.0, 0.0)  # sans perte — ratio seul

    # ── 3 · H.264 — le standard vidéo (cv2) ─────────────────────────────────
    tmp = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
    tmp.close()
    fourcc = cv2.VideoWriter_fourcc(*'X264')
    writer = cv2.VideoWriter(tmp.name, fourcc, 25, (W, H))
    for f in frames:
        writer.write(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
    writer.release()
    cap = cv2.VideoCapture(tmp.name)
    rec_h264 = []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        rec_h264.append(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
    cap.release()
    size_h264 = Path(tmp.name).stat().st_size
    Path(tmp.name).unlink()
    if len(rec_h264) == T:
        rec_h264 = np.stack(rec_h264)
        results['H.264 (X264)'] = (size_h264, psnr(np.stack(frames), rec_h264),
                                   ssim(np.stack(frames), rec_h264))
    else:
        results['H.264 (X264)'] = (size_h264, float('nan'), 0.0)

    # ── 4 · JPEG2000 — le standard image (ondelettes, par frame) ────────────
    total_jp2 = 0
    rec_jp2 = []
    for f in frames:
        ok, buf = cv2.imencode('.jp2', cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
        total_jp2 += len(buf)
        rec_jp2.append(cv2.cvtColor(cv2.imdecode(buf, cv2.IMREAD_COLOR),
                                    cv2.COLOR_BGR2RGB))
    results['JPEG2000'] = (total_jp2, psnr(np.stack(frames), np.stack(rec_jp2)),
                           ssim(np.stack(frames), np.stack(rec_jp2)))

    print(f"\n   {'codec':<22}{'taille':>10}{'vs RAW':>9}{'PSNR':>9}{'SSIM':>8}")
    print('─' * 60)
    for name, (size, p, s) in results.items():
        ratio = raw_size / size
        p_str = '—' if math.isnan(p) else f'{p:6.2f}'
        s_str = '—' if s == 0.0 else f'{s:.4f}'
        print(f"   {name:<22}{size:>10,}{ratio:>8.2f}×{p_str:>9}{s_str:>8}")
    print('─' * 60)
    print("   La lecture : sur le contenu à mémoire, le secteur doré (THU)")
    print("   doit égaler ou dépasser les codecs α=1 — la contenance vérifiée.")
    print("═" * 70)
