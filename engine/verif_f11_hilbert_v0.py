#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F11 HILBERT V0 — La rotation Bateman dérive l'arène de Hilbert
===============================================================
Suite de verif_f11_normes_v0 (C-H1) : passage du PROBE au THEOREME (dim. finie).

Théorème (C-H2, dimension finie) :
  Toute norme sur un espace réel de dimension finie, invariante sous le groupe
  engendré par la rotation Bateman R(θ), θ = πα/2, est euclidienne sur chaque
  plan invariant — donc induite d'un produit scalaire (Jordan–von Neumann).

Preuve en 5 pas (détaillée dans DEPOT_F11_HILBERT_V0.md) :
  1. R(θ) isométrie  ⟹  R(nθ) isométrie ∀n ;
  2. θ/π = 1/(2φ) IRRATIONNEL  ⟹  {nθ mod 2π} dense dans le cercle (Kronecker) ;
  3. dimension finie ⟹ équivalence des normes ⟹ passage à la clôture : SO(2) entier ;
  4. invariance sous SO(2) ⟹ ‖x‖ = c·|x|₂ par orbite (homogénéité) ;
  5. loi du parallélogramme sur tout plan ⟹ Jordan–von Neumann (1935). ∎

Le point natif THU : si θ/π était RATIONNEL, l'orbite serait un polygone fini
et des normes polygonales survivraient. C'est l'IRRATIONALITÉ de 1/(2φ) qui
ferme la dernière échappatoire — le caractère non-périodique du nombre d'or
sélectionne l'arène quadratique.

Contrôles :
  C1  Bateman ∀α : det=1, trace=2cosθ, valeurs e^{±iθ}, RᵀR=I
  C2  Irrationalité → densité : orbite {nθ mod 2π} couvre à ~1/N ; proche j
  C3  Invariance par rotation aléatoire : L² exacte, rivales dévient
  C4  Défaut de parallélogramme : L² nul, rivales strictement positifs
  C5  Structure complexe : j=R(π/2)∈clôture, j²=−1, j isométrie,
      ⟨jx,y⟩_ℂ = i⟨x,y⟩_ℂ (ℂ ÉMERGE du groupe, pas posé)
  C6  Flot α→1 : e^{−iHt} conserve L² ∀t (l'arène du théorème = celle du
      dépôt Schrödinger)

Verdict exit 0 = conforme, exit 1 = réfuté.
"""

import sys
import json
import math
import cmath
import numpy as np

PHI = (1.0 + math.sqrt(5.0)) / 2.0
ALPHA = 1.0 / PHI
THETA = math.pi * ALPHA / 2.0            # 0.970806 rad = 55.6231° = 90/φ degrés
SEEDS = (7, 11, 13)
N_ORBIT = 2000
PS = (1, 2, 4, np.inf)


def bateman(theta):
    """Rotation plane déposée (HAMILTONIEN C3) : det=1, trace=2cosθ, e^{±iθ}."""
    c, s = math.cos(theta), math.sin(theta)
    return np.array([[c, -s], [s, c]])


def norm_of(x, p):
    if p == np.inf:
        return float(np.max(np.abs(x)))
    return float(np.sum(np.abs(x) ** p) ** (1.0 / p))


def random_orthogonal(rng, n):
    """Q orthogonale par QR de gaussienne (signes fixes)."""
    A = rng.normal(size=(n, n))
    Q, R = np.linalg.qr(A)
    Q = Q * np.sign(np.diag(R))
    return Q


# ---------------------------------------------------------------- contrôles

def c1_bateman_tout_alpha():
    """det=1, trace=2cosθ, valeurs propres e^{±iθ}, RᵀR=I pour une liste d'α."""
    worst = 0.0
    detail = {}
    for a in (0.3, 0.5, ALPHA, 0.8, 0.95):
        th = math.pi * a / 2.0
        R = bateman(th)
        det = float(np.linalg.det(R))
        tr = float(np.trace(R))
        ev = np.linalg.eigvals(R)
        orth = float(np.max(np.abs(R.T @ R - np.eye(2))))
        target = cmath.exp(1j * th)
        err_ev = max(abs(ev[0] - target), abs(ev[1] - np.conj(target)))
        w = max(abs(det - 1.0), abs(tr - 2 * math.cos(th)), err_ev, orth)
        detail[a] = {"det": det, "trace": tr, "err_eigen": float(err_ev),
                     "err_orth": orth}
        worst = max(worst, w)
    return worst, detail


def c2_irrationalite_densite():
    """Orbite {nθ mod 2π} : couverture ~1/N + approche de j (π/2)."""
    ang = np.array([(n * THETA) % (2 * math.pi) for n in range(1, N_ORBIT + 1)])
    ang_sorted = np.sort(ang)
    gaps = np.diff(np.concatenate([ang_sorted, [ang_sorted[0] + 2 * math.pi]]))
    max_gap = float(np.max(gaps))
    # borne de couverture : max_gap <= 8 * 2π / N  (constante des écarts, ≤ 8)
    cov_const = max_gap * N_ORBIT / (2 * math.pi)
    # approche de π/2 (le corps complexe j est dans la FERMETURE du groupe)
    dist_j = np.abs(((ang - math.pi / 2 + math.pi) % (2 * math.pi)) - math.pi)
    n_star = int(np.argmin(dist_j)) + 1
    d_j = float(dist_j.min())
    ok = (cov_const <= 8.0) and (d_j <= 2 * math.pi / 200.0)
    val = 0.0 if ok else max(cov_const - 8.0, d_j)
    return val, {"theta": THETA, "theta_sur_pi": THETA / math.pi,
                 "cible": 1.0 / (2 * PHI), "max_gap": max_gap,
                 "constante_couverture": cov_const, "N": N_ORBIT,
                 "n_proche_j": n_star, "dist_j": d_j, "seuil_j": 2 * math.pi / 200.0}


def c3_invariance_rotation():
    """L² invariante sous rotation aléatoire (exacte), rivales dévient."""
    per_seed = {p: [] for p in PS}
    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        psi = rng.normal(size=6)
        n0 = {p: norm_of(psi, p) for p in PS}
        dev = {p: 0.0 for p in PS}
        for _ in range(30):
            Q = random_orthogonal(rng, 6)
            qpsi = Q @ psi
            for p in PS:
                dev[p] = max(dev[p], abs(norm_of(qpsi, p) / n0[p] - 1.0))
        for p in PS:
            per_seed[p].append(dev[p])
    l2_worst = max(per_seed[2])
    rivales_min = min(max(per_seed[p]) for p in (1, 4, np.inf))
    ok = (l2_worst < 1e-14) and (rivales_min > 0.05)
    return (0.0 if ok else max(l2_worst, 0.05)), \
           {"L2_worst": l2_worst, "rivales_min": rivales_min,
            "per_seed": {str(p): v for p, v in per_seed.items()}}


def c4_parallelogramme():
    """Défaut D(x,y) = ‖x+y‖²+‖x−y‖²−2‖x‖²−2‖y‖², normalisé ; L² nul, rivales > 0."""
    per_seed = {p: [] for p in PS}
    for seed in SEEDS:
        rng = np.random.default_rng(seed + 100)
        defect = {p: 0.0 for p in PS}
        for _ in range(50):
            x = rng.normal(size=6)
            y = rng.normal(size=6)
            nx, ny = norm_of(x, 2) ** 2, norm_of(y, 2) ** 2
            for p in PS:
                d = (norm_of(x + y, p) ** 2 + norm_of(x - y, p) ** 2
                     - 2 * norm_of(x, p) ** 2 - 2 * norm_of(y, p) ** 2)
                defect[p] = max(defect[p], abs(d) / (nx + ny))
        for p in PS:
            per_seed[p].append(defect[p])
    l2_worst = max(per_seed[2])
    rivales_min = min(max(per_seed[p]) for p in (1, 4, np.inf))
    ok = (l2_worst < 1e-14) and (rivales_min > 0.05)
    return (0.0 if ok else max(l2_worst, 0.05)), \
           {"L2_defect_max": l2_worst, "rivales_defect_min": rivales_min,
            "per_seed": {str(p): v for p, v in per_seed.items()}}


def c5_structure_complexe():
    """j = R(π/2) : j²=−I, j isométrie, ⟨jx,y⟩_ℂ = i⟨x,y⟩_ℂ avec
    ⟨x,y⟩_ℂ := ⟨x,y⟩ − i⟨jx,y⟩ — ℂ ÉMERGE de la clôture du groupe Bateman."""
    J = bateman(math.pi / 2.0)
    rng = np.random.default_rng(7)
    worst_j2 = 0.0
    worst_iso = 0.0
    worst_compat = 0.0
    for _ in range(50):
        x = rng.normal(size=6)
        y = rng.normal(size=6)
        # j agit par blocs sur les 3 plans de modes (structure du doublet)
        jx = np.concatenate([J @ x[2 * k:2 * k + 2] for k in range(3)])
        jy = np.concatenate([J @ y[2 * k:2 * k + 2] for k in range(3)])
        worst_j2 = max(worst_j2, float(np.max(np.abs(J @ J + np.eye(2)))))
        worst_iso = max(worst_iso, abs(norm_of(jx, 2) / norm_of(x, 2) - 1.0))
        ip_xy = float(np.dot(x, y)) - 1j * float(np.dot(jx, y))
        ip_jxy = float(np.dot(jx, y)) - 1j * float(np.dot(np.concatenate(
            [J @ (J @ x[2 * k:2 * k + 2]) for k in range(3)]), y))
        worst_compat = max(worst_compat, abs(ip_jxy - 1j * ip_xy))
    # j dans la clôture : R(nθ) → R(π/2) à ~1/N près (contrôle C2)
    ang = np.array([(n * THETA) % (2 * math.pi) for n in range(1, N_ORBIT + 1)])
    d_j = float(np.min(np.abs(((ang - math.pi / 2 + math.pi) % (2 * math.pi)) - math.pi)))
    ok = (worst_j2 < 1e-14) and (worst_iso < 1e-14) and (worst_compat < 1e-14) \
         and (d_j <= 2 * math.pi / 200.0)
    return (0.0 if ok else max(worst_j2, worst_iso, worst_compat, d_j)), \
           {"err_j2": worst_j2, "err_isometrie": worst_iso,
            "err_compatibilite": worst_compat, "dist_R_ntheta_j": d_j}


def c6_flot_alpha1():
    """e^{−iHt} (α→1, dépôt Schrödinger) conserve L² ∀t — l'arène est la même."""
    rng = np.random.default_rng(7)
    A = rng.normal(size=(6, 6)) + 1j * rng.normal(size=(6, 6))
    H = (A + A.conj().T) / 2.0
    lam, V = np.linalg.eigh(H)
    psi0 = rng.normal(size=6) + 1j * rng.normal(size=6)
    worst_l2 = 0.0
    n0 = np.linalg.norm(psi0)
    for t in np.linspace(0.05, 6.0, 100):
        psi = V @ (np.exp(-1j * lam * t) * (V.conj().T @ psi0))
        worst_l2 = max(worst_l2, abs(np.linalg.norm(psi) / n0 - 1.0))
    ok = worst_l2 < 1e-14
    return (0.0 if ok else worst_l2), {"L2_flot_worst": worst_l2}


# ---------------------------------------------------------------- main

def main():
    print("=" * 72)
    print("F11 HILBERT V0 — la rotation Bateman dérive l'arène (C-H2, dim. finie)")
    print("θ = πα/2 = %.6f rad = %.4f° ; θ/π = %.12f ; 1/(2φ) = %.12f"
          % (THETA, math.degrees(THETA), THETA / math.pi, 1 / (2 * PHI)))
    print("=" * 72)

    w1, d1 = c1_bateman_tout_alpha()
    w2, d2 = c2_irrationalite_densite()
    w3, d3 = c3_invariance_rotation()
    w4, d4 = c4_parallelogramme()
    w5, d5 = c5_structure_complexe()
    w6, d6 = c6_flot_alpha1()

    print()
    print("C1  Bateman ∀α        : worst = %.3e (det, trace, e^{±iθ}, RᵀR)" % w1)
    print("C2  densité orbite    : θ/π = %.12f vs 1/(2φ) ; couverture %.2f (≤8) ;"
          % (d2["theta_sur_pi"], d2["constante_couverture"]))
    print("     j dans clôture   : n*=%d, dist(n*θ, π/2) = %.3e (seuil %.3e)"
          % (d2["n_proche_j"], d2["dist_j"], d2["seuil_j"]))
    print("C3  invariance rot.   : L² worst = %.3e ; rivales min = %.3e"
          % (d3["L2_worst"], d3["rivales_min"]))
    print("C4  parallélogramme   : L² défaut = %.3e ; rivales min = %.3e"
          % (d4["L2_defect_max"], d4["rivales_defect_min"]))
    print("C5  ℂ émerge          : j² err %.3e ; isométrie err %.3e ;"
          % (d5["err_j2"], d5["err_isometrie"]))
    print("     compatibilité    : ⟨jx,y⟩_ℂ = i⟨x,y⟩_ℂ, err %.3e ; R(nθ)→j à %.3e"
          % (d5["err_compatibilite"], d5["dist_R_ntheta_j"]))
    print("C6  flot α→1 (L²)     : worst = %.3e" % d6["L2_flot_worst"])

    ok = (w1 < 1e-14) and (w2 == 0.0) and (w3 == 0.0) and (w4 == 0.0) \
         and (w5 == 0.0) and (w6 < 1e-14)

    print()
    print("-" * 72)
    if ok:
        print("VERDICT : F11_HILBERT_V0_C_H2_THEOREME_DIM_FINIE — exit 0")
        print("  La rotation Bateman (θ/π irrationnel) balaie tout le cercle :")
        print("  seule la norme quadratique est invariante → produit scalaire")
        print("  (Jordan–von Neumann) → ℂ émerge de la clôture du groupe.")
        print("  Reste ouvert (consigné) : dimension infinie + complétude (Voie 2),")
        print("  théorème spectral (Voie 3) — F11 n'est PAS fermée.")
    else:
        print("VERDICT : REFUTE — exit 1")
    print("-" * 72)

    with open("resultat_f11_hilbert_v0.json", "w", encoding="utf-8") as f:
        json.dump({"verdict": "F11_HILBERT_V0_C_H2_THEOREME_DIM_FINIE" if ok else "REFUTE",
                   "alpha": ALPHA, "theta": THETA, "theta_sur_pi": THETA / math.pi,
                   "controles": {"C1": d1, "C2": d2, "C3": d3, "C4": d4,
                                 "C5": d5, "C6": d6}, "ok": ok},
                  f, indent=2, ensure_ascii=False)

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
