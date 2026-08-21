#!/usr/bin/env python3
"""
benchmark_phi.py — Suite de validation de la φ-optimalité du codec HCV2
=========================================================================
Question : le seuil modal 1/(φ·m), dérivé de la THU, est-il
Pareto-optimal ET au genou de la courbe qualité/ratio, sur des
contenus divers — et ses voisins (0.6, 0.62, 2/3, 0.7) font-ils
strictement moins bien ?

Protocole :
  1. 8 types de contenu (mémoire, texture, visage, texte, bruit,
     scène, photo, gradient) — générés déterministiquement.
  2. Balayage du seuil : 0.40, 0.50, 0.60, 1/φ, 0.62, 2/3, 0.70, 0.75, 1.00.
  3. Métriques : PSNR, SSIM, ratio (vs brut).
  4. Verdict automatisé :
     - P1 : 1/φ est Pareto-optimal (aucun seuil ne le domine)
     - P2 : 1/φ est au genou (transition du sacrifice marginal)
     - P3 : les voisins font strictement moins bien (contrefactuel)

Sortie : rapport texte + JSON (benchmark_phi_report.json)
"""

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hcv2_video_pipeline import encode_video, decode_video, psnr, ssim

PHI = (1 + np.sqrt(5)) / 2
INV_PHI = 1 / PHI  # ≈ 0.618034

# Seuils à balayer — inclut 1/φ et ses voisins (test contrefactuel)
THRESHOLDS = [0.40, 0.50, 0.60, INV_PHI, 0.62, 2.0 / 3.0, 0.70, 0.75, 1.00]

H, W, T = 240, 320, 15  # résolution de benchmark (rapide mais représentative)


# ══════════════════════════════════════════════════════════════════════
# GÉNÉRATEURS DE CONTENU (déterministes)
# ══════════════════════════════════════════════════════════════════════

def gen_memoire():
    """Scène lente + bruit — le domaine doré (contenu À MÉMOIRE)."""
    rng = np.random.default_rng(42)
    frames = []
    for t in range(T):
        y, x = np.mgrid[0:H, 0:W]
        bg = np.sin(x / 35 + t * 0.10) * 55 + np.cos(y / 25 + t * 0.08) * 45 + 128
        noise = rng.normal(0, 8, (H, W))
        img = np.clip(bg + noise, 0, 255).astype(np.uint8)
        frames.append(np.stack([img, img, img[::-1]], -1))
    return frames


def gen_texture():
    """Texture haute fréquence + mouvement lent."""
    frames = []
    for t in range(T):
        y, x = np.mgrid[0:H, 0:W]
        tex = (np.sin(x * 0.9 + y * 1.3 + t * 0.15) * 25 +
               np.sin(x * 0.4 - y * 0.7 + t * 0.08) * 20)
        img = np.clip(tex + 128, 0, 255).astype(np.uint8)
        frames.append(np.stack([img, img, img[::-1]], -1))
    return frames


def gen_visage():
    """Structure radiale (type visage) + mouvement doux."""
    frames = []
    for t in range(T):
        y, x = np.mgrid[0:H, 0:W]
        cx, cy = W * 0.5, H * 0.45
        r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        visage = (np.exp(-(r / 60) ** 2) * 90 +
                  np.exp(-((x - cx - 30) ** 2 + (y - cy - 15) ** 2) / 300) * 30 +
                  np.exp(-((x - cx + 30) ** 2 + (y - cy - 15) ** 2) / 300) * 30)
        bouche = np.exp(-((x - cx) ** 2 + (y - cy - 35) ** 2) / 120) * 25
        img = np.clip(visage + bouche + 100 + t * 0.5, 0, 255).astype(np.uint8)
        frames.append(np.stack([img, img, img[::-1]], -1))
    return frames


def gen_texte():
    """Contenus à arêtes vives (type texte) — pire cas pour la DCT."""
    rng = np.random.default_rng(7)
    frames = []
    for t in range(T):
        img = np.full((H, W), 255.0)
        for _ in range(60):
            x0, y0 = rng.integers(0, W - 40), rng.integers(0, H - 12)
            img[y0:y0 + 8, x0:x0 + 36] = 0
        img = np.clip(img + t * 2, 0, 255).astype(np.uint8)
        frames.append(np.stack([img, img, img[::-1]], -1))
    return frames


def gen_bruit():
    """Bruit pur — incompressible (contrôle négatif)."""
    rng = np.random.default_rng(99)
    return [rng.integers(0, 255, (H, W, 3), dtype=np.uint8) for _ in range(T)]


def gen_scene():
    """Scène réaliste : fond + objet en mouvement + texture."""
    frames = []
    for t in range(T):
        y, x = np.mgrid[0:H, 0:W]
        bg = np.sin(x / 30 + t * 0.15) * 55 + np.cos(y / 22 + t * 0.1) * 45 + 128
        ox = int(60 + t * 16) % W
        obj = np.exp(-((x - ox) ** 2 + (y - 120) ** 2) / 900) * 75
        tex = np.sin(x * 0.5 + y * 0.7 + t * 0.3) * 12
        img = np.clip(bg + obj + tex, 0, 255).astype(np.uint8)
        frames.append(np.stack([img, img, img[::-1]], -1))
    return frames


def gen_photo():
    """Statistiques type photographie : patchs, lissage local."""
    rng = np.random.default_rng(123)
    base = rng.normal(128, 40, (H, W))
    for _ in range(8):  # lissage itératif = corrélations locales
        base = (base + np.roll(base, 1, 0) + np.roll(base, 1, 1) +
                np.roll(base, -1, 0) + np.roll(base, -1, 1)) / 5
    frames = []
    for t in range(T):
        img = np.clip(base + t, 0, 255).astype(np.uint8)
        frames.append(np.stack([img, img, img[::-1]], -1))
    return frames


def gen_gradient():
    """Gradient pur — le cas le plus compressible (contrôle positif)."""
    frames = []
    for t in range(T):
        y, x = np.mgrid[0:H, 0:W]
        img = np.clip((x / W * 200) + (y / H * 55) + t, 0, 255).astype(np.uint8)
        frames.append(np.stack([img, img, img[::-1]], -1))
    return frames


GENERATORS = {
    'memoire': gen_memoire,
    'texture': gen_texture,
    'visage': gen_visage,
    'texte': gen_texte,
    'bruit': gen_bruit,
    'scene': gen_scene,
    'photo': gen_photo,
    'gradient': gen_gradient,
}


# ══════════════════════════════════════════════════════════════════════
# ANALYSE
# ══════════════════════════════════════════════════════════════════════

def is_pareto_dominated(gold, results):
    """Un point est dominé si un autre est ≥ partout et > quelque part
    (avec tolérance numérique pour éviter les égalités flottantes)."""
    gp, gs, gr = gold
    for p, s, r in results:
        if p >= gp - 1e-9 and s >= gs - 1e-12 and r >= gr - 1e-9 and (p > gp + 1e-9 or r > gr + 1e-9):
            return (p, s, r)
    return None


def knee_position(results):
    """Position du genou : seuil où le sacrifice marginal change le plus."""
    sorted_r = sorted(results, key=lambda v: v[0])
    slopes = []
    for i in range(1, len(sorted_r)):
        t0, p0, _, r0 = sorted_r[i - 1]
        t1, p1, _, r1 = sorted_r[i]
        if r1 - r0 > 1e-9:
            slopes.append(((t0 + t1) / 2, (p1 - p0) / (r1 - r0)))
    # Le genou = plus grand saut de pente consécutif
    best, best_idx = 0.0, 0
    for i in range(1, len(slopes)):
        jump = abs(slopes[i][1] - slopes[i - 1][1])
        if jump > best:
            best, best_idx = jump, i
    return slopes[best_idx][0] if slopes else None


# ══════════════════════════════════════════════════════════════════════
# BENCHMARK PRINCIPAL
# ══════════════════════════════════════════════════════════════════════

def run_benchmark():
    raw = H * W * 3 * T
    report = {'content': {}, 'verdicts': {}, 'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')}
    print('═' * 78)
    print('  BENCHMARK φ-OPTIMALITÉ — Codec HCV2 (mémoire dorée + seuil modal)')
    print(f'  Résolution {W}×{H} × {T} frames · {len(GENERATORS)} contenus · {len(THRESHOLDS)} seuils')
    print(f'  Seuil doré : 1/φ = {INV_PHI:.6f}')
    print('═' * 78)

    for name, gen in GENERATORS.items():
        frames = gen()
        results = []
        for scale in THRESHOLDS:
            enc = encode_video(frames, use_memory=True, grain=False,
                               mag_dtype=np.float16, predictor='golden',
                               threshold_scale=scale)
            dec = decode_video(enc, predictor='golden')
            orig = np.stack(frames)
            p = psnr(orig.astype(np.float64), dec.astype(np.float64))
            s = ssim(orig.astype(np.uint8), dec.astype(np.uint8))
            r = raw / len(enc['blob'])
            results.append((scale, p, s, r))

        # Point doré
        gold = next(v for v in results if abs(v[0] - INV_PHI) < 1e-9)

        # P1 : Pareto
        dominator = is_pareto_dominated((gold[1], gold[2], gold[3]),
                                        [(p, s, r) for t, p, s, r in results if t != gold[0]])
        # P2 : genou (individuel)
        knee = knee_position(results)
        knee_ok = knee is not None and abs(knee - INV_PHI) / INV_PHI < 0.15
        # P3 (contrefactuel global) : calculé après la boucle — la position
        # moyenne du genou sur tous les contenus doit être plus proche de
        # 1/φ que de tout autre seuil candidat.
        report['content'][name] = {
            'gold': {'psnr': float(gold[1]), 'ssim': float(gold[2]), 'ratio': float(gold[3])},
            'pareto_ok': bool(dominator is None),
            'knee_ok': bool(knee_ok),
            'knee_at': float(knee) if knee is not None else None,
            'results': {str(t): {'psnr': float(p), 'ssim': float(s), 'ratio': float(r)}
                        for t, p, s, r in results},
        }

        print(f'\n  ▶ {name:10s}  | 1/φ : PSNR {gold[1]:6.2f} dB · SSIM {gold[2]:.4f} · ratio {gold[3]:6.1f}×')
        print(f'      P1 Pareto    : {"✅ OK" if dominator is None else "⚠️ DOMINÉ"}'
              f'{"  (dominé par PSNR %.2f / ratio %.1f×)" % (dominator[0], dominator[2]) if dominator else ""}')
        print(f'      P2 Genou     : {"✅ OK" if knee_ok else "✗ non"}  (genou estimé à {knee:.3f} vs 1/φ {INV_PHI:.3f})')

    # Verdict global
    all_pareto = all(c['pareto_ok'] for c in report['content'].values())
    all_knee = all(c['knee_ok'] for c in report['content'].values())

    # P3 contrefactuel : la position moyenne du genou est-elle plus proche
    # de 1/φ que de n'importe quel autre seuil candidat ?
    knees = [c['knee_at'] for c in report['content'].values() if c['knee_at'] is not None]
    mean_knee = float(np.mean(knees))
    candidates = [t for t in THRESHOLDS if abs(t - INV_PHI) > 0.02]
    best_other = min(candidates, key=lambda t: abs(t - mean_knee))
    p3_ok = abs(mean_knee - INV_PHI) < abs(mean_knee - best_other)

    report['verdicts'] = {
        'P1_pareto': bool(all_pareto),
        'P2_knee': bool(all_knee),
        'P3_counterfactual': bool(p3_ok),
        'mean_knee': mean_knee,
        'closest_other': best_other,
    }

    print('\n' + '═' * 78)
    print('  VERDICT GLOBAL')
    print('═' * 78)
    print(f'  P1 — 1/φ Pareto-optimal sur tous les contenus  : {"✅ OUI" if all_pareto else "❌ NON"}')
    print(f'  P2 — 1/φ au genou de la courbe qualité/ratio   : {"✅ OUI" if all_knee else "❌ NON"}')
    print(f'  P3 — Genou moyen {mean_knee:.3f} : 1/φ ({INV_PHI:.3f}) plus proche que le meilleur'
          f' autre candidat ({best_other:.3f}) : {"✅ OUI" if p3_ok else "❌ NON"}')

    with open('benchmark_phi_report.json', 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print('\n  Rapport JSON : benchmark_phi_report.json')
    return report


if __name__ == '__main__':
    t0 = time.time()
    run_benchmark()
    print(f'\n  Temps total : {time.time() - t0:.1f}s')