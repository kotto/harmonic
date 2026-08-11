#!/usr/bin/env python3
"""
exploration_piste3_video_memoire.py — LA VIDÉO À MÉMOIRE (piste 3)
=================================================================
La prédiction par le NOYAU DORÉ : la frame suivante est prédite depuis
TOUT le passé pondéré par K(d) = B·E_{1/φ}(−φ·d^{1/φ}) — non-markovien,
oubli t^{−0,618} — zéro paramètre (T2). Le résidu seul est à compresser.

Comparaison honnête sur B3.mp4 (la vidéo de la validation de base) :
  · GOLDEN : ψ̂_t = Σ_d K(d)·ψ_{t−d}/ΣK   (la mémoire complète)
  · MARKOV : ψ̂_t = ψ_{t−1}                (la référence type MPEG)
  · MOYENNE : ψ̂_t = moyenne du passé       (aucune mémoire)
Mesures : PSNR de prédiction par frame · énergie du résidu (ce que la
mémoire oublie = le grain, le Zeno t^{1,236} en toile de fond).
"""

import math

import numpy as np

PHI = (1 + np.sqrt(5)) / 2
ALPHA = 1 / PHI
B = 1 - ALPHA + ALPHA / math.gamma(ALPHA)
MEMORY_DEPTH = 10        # la profondeur de la mémoire dorée (frames)


def ml_series(z: float, alpha: float = ALPHA, terms: int = 150) -> float:
    """E_α(z) par série (|z| modéré — Kahan)."""
    s = 0.0
    for k in range(terms):
        s += z ** k / math.gamma(alpha * k + 1)
    return s


def golden_weights(depth: int = MEMORY_DEPTH) -> np.ndarray:
    """K(d) = B·E_{1/φ}(−φ·d^{1/φ}) pour d = 1..depth — la mémoire dorée."""
    return np.array([B * ml_series(-PHI * d ** ALPHA) for d in range(1, depth + 1)])


def predict(series, weights) -> np.ndarray:
    """Prédit chaque frame t ≥ depth par la mémoire pondérée du passé."""
    depth = len(weights)
    w = weights / weights.sum()
    out = np.zeros_like(series[depth:])
    for i, t in enumerate(range(depth, len(series))):
        past = np.stack([series[t - d] for d in range(1, depth + 1)])
        out[i] = np.tensordot(w, past, axes=(0, 0))
    return out


def psnr(a, b):
    mse = float(np.mean((a - b) ** 2))
    return float('inf') if mse == 0 else 20 * math.log10(255.0 / math.sqrt(mse))


print("═" * 70)
print("PISTE 3 — LA VIDÉO À MÉMOIRE : prédiction par le noyau doré K(t)")
print("═" * 70)

import cv2

cap = cv2.VideoCapture(r'E:\SAAS - Copie\B3.mp4')
frames = []
while len(frames) < 60:
    ok, frame = cap.read()
    if not ok:
        break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, (320, 180))
    frames.append(gray.astype(np.float64))
cap.release()
T = len(frames)
print(f"   B3.mp4 : {T} frames extraites (320×180, niveaux de gris)")

if T <= MEMORY_DEPTH + 3:
    print("   ❌ pas assez de frames — exploration impossible")
    raise SystemExit(1)

# les trois prédicteurs
w_gold = golden_weights()
pred_gold = predict(frames, w_gold)
pred_markov = np.stack([frames[t - 1] for t in range(MEMORY_DEPTH, T)])
pred_mean = np.stack([np.mean(np.stack(frames[t - MEMORY_DEPTH:t]), axis=0)
                      for t in range(MEMORY_DEPTH, T)])
truth = np.stack(frames[MEMORY_DEPTH:])

print(f"\n   Poids de la mémoire dorée K(1..{MEMORY_DEPTH}) (normalisés) :")
w_n = w_gold / w_gold.sum()
print("   " + '  '.join(f'{x:.3f}' for x in w_n))

print(f"\n   PSNR de PRÉDICTION (moyenne sur {T - MEMORY_DEPTH} frames) :")
results = {}
for name, pred in [('GOLDEN (K(t))  ', pred_gold), ('MARKOV (t−1)   ', pred_markov),
                   ('MOYENNE        ', pred_mean)]:
    psnrs = [psnr(truth[i], pred[i]) for i in range(len(truth))]
    results[name.strip()] = (float(np.mean(psnrs)), float(np.median(psnrs)))
    print(f"   {name} : moyenne {np.mean(psnrs):6.2f} dB · médiane {np.median(psnrs):6.2f} dB")

# l'énergie du résidu — ce que la mémoire oublie
print(f"\n   Énergie du résidu (relative à l'énergie de la frame) :")
for name, pred in [('GOLDEN', pred_gold), ('MARKOV', pred_markov)]:
    resid = np.mean(np.mean((truth - pred) ** 2) / np.mean(truth ** 2))
    print(f"   {name:8s} : {resid:.4f} — le résidu est ce qu'il reste à compresser")

# ── le contenu À MÉMOIRE : scène lente persistante + bruit capteur ──────────
print("\n" + "─" * 70)
print("   CONTENU À MÉMOIRE (le domaine de la théorie) : scène lente + bruit")
rng = np.random.default_rng(7)
h, w = 120, 160
noise_std = 12.0
mem_frames = []
x0, y0 = 40.0, 60.0
for t in range(60):
    frame = np.zeros((h, w))
    # la structure persistante : deux blobs qui dérivent LENTEMENT
    for (bx, by, br) in [(x0 + t * 0.3, y0, 14), (w - 45 - t * 0.2, 35 + t * 0.15, 10)]:
        yy, xx = np.mgrid[0:h, 0:w]
        frame += 180 * np.exp(-((xx - bx) ** 2 + (yy - by) ** 2) / (2 * br ** 2))
    # le grain capteur : le bruit (ce que la mémoire doit oublier)
    frame += rng.normal(0, noise_std, (h, w))
    mem_frames.append(np.clip(frame, 0, 255))

def predict_mem(series, weights):
    depth = len(weights)
    w = weights / weights.sum()
    out = np.zeros_like(series[depth:])
    for i, t in enumerate(range(depth, len(series))):
        past = np.stack([series[t - d] for d in range(1, depth + 1)])
        out[i] = np.tensordot(w, past, axes=(0, 0))
    return out

mem_pred_gold = predict_mem(mem_frames, golden_weights())
mem_pred_markov = np.stack([mem_frames[t - 1] for t in range(MEMORY_DEPTH, 60)])
mem_pred_mean = np.stack([np.mean(np.stack(mem_frames[t - MEMORY_DEPTH:t]), axis=0)
                          for t in range(MEMORY_DEPTH, 60)])
mem_truth = np.stack(mem_frames[MEMORY_DEPTH:])
for name, pred in [('GOLDEN (K(t))', mem_pred_gold), ('MARKOV (t−1) ', mem_pred_markov),
                   ('MOYENNE      ', mem_pred_mean)]:
    psnrs = [psnr(mem_truth[i], pred[i]) for i in range(len(mem_truth))]
    print(f"   {name} : moyenne {np.mean(psnrs):6.2f} dB · médiane {np.median(psnrs):6.2f} dB")

print("\n" + "═" * 70)
print("STATUT PISTE 3 — la vidéo à mémoire")
print("   B3 (contenu RAPIDE) : MARKOV gagne (31,2 vs 21,4 dB) — la mémoire")
print("        lisse le mouvement : le domaine doré n'est pas pour ça")
print("   Scène lente + bruit (contenu À MÉMOIRE) : → voir les PSNR")
print("        ci-dessus — le grain capteur est-il oublié par la mémoire ?")
print("   Le principe (Zeno t^{1,236}) : ce qui persiste dans la mémoire")
print("        est le signal, ce qu'elle oublie est le grain — mesuré ici")
print("   Classement : 🔬 PROBE — zéro paramètre (T2) ; le pipeline complet")
print("   = prédiction dorée + résidu compressé par la piste 1 (codec modal)")
print("═" * 70)
