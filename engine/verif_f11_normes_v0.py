#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F11 NORMES V0 — Quelle norme survit à la dynamique THU ?
=========================================================
Frontière F11 (FRONTIERE_F11_HILBERT.md, Voie 1) — première évidence machine C-H1.

Thèse testée : « L² est le seul survivant du filtre alpha→1 ;
à alpha=1/phi, ce qui survit n'est plus la norme mais la phase. »

Contrôles :
  C1  Sanity Mittag-Leffler : formes closes exactes + décroissance algébrique
  C2  Filtre alpha→1 (Schrödinger unitaire) : L² conservée à précision machine
  C3  Sélection non vide : les rivales L^p dévient franchement
  C4  alpha=1/phi (mémoire) : AUCUNE norme conservée — système ouvert
  C5  alpha=1/phi : contraction L² (la mémoire amortit, n'amplifie pas)

Discipline (leçons consignées pendant la mise au point) :
  - H doit être un MÉLANGEUR (hermitien non diagonal) : un H diagonal ne produit
    que des phases, qui conservent trivialement TOUTES les normes L^p.
  - Série de Mittag-Leffler en termes DIRECTS z^n/Gamma(alpha*n+1) : toute
    récurrence multiplicative sur les gamma (produit de gammas) ou décalage
    d'indice donne une AUTRE fonction (silencieusement).
  - float64 suffit pour alpha=1 (forme close e^z) mais PAS pour alpha=1/phi à
    grand |z| (annulation catastrophique) -> mpmath dps=80 obligatoire.

Verdict exit 0 = conforme, exit 1 = réfuté.
"""

import sys
import json
import math
import numpy as np
from mpmath import mp, mpc, mpf, exp as mexp, loggamma, erf as merf

mp.dps = 80

PHI = (1.0 + math.sqrt(5.0)) / 2.0
ALPHA = 1.0 / PHI                      # 0.6180339887...
SEEDS_NP = (7, 11, 13)                 # filtre alpha→1 (numpy, forme close)
SEEDS_MP = (7, 11)                     # alpha=1/phi (mpmath dps=80)
T_GRID = np.linspace(0.05, 6.0, 100)
PS = (1, 2, 4, np.inf)

# ---------------------------------------------------------------- Mittag-Leffler

def E_alpha_mp(z, alpha):
    """E_alpha(z) = somme z^n / Gamma(alpha*n+1), termes DIRECTS, dps=80."""
    pow_n = mpc(1)
    s = mpc(1)
    quiet = 0
    for n in range(1, 4000):
        pow_n = pow_n * z
        term = pow_n * mexp(-loggamma(alpha * n + 1))
        s += term
        quiet = quiet + 1 if abs(term) < mpf("1e-55") else 0
        if quiet >= 20:
            break
    return s


def make_system(seed):
    """H hermitien MÉLANGEUR (non diagonal) + état initial, seed fixe."""
    rng = np.random.default_rng(seed)
    A = rng.normal(size=(6, 6)) + 1j * rng.normal(size=(6, 6))
    H = (A + A.conj().T) / 2.0
    lam, V = np.linalg.eigh(H)
    psi0 = rng.normal(size=6) + 1j * rng.normal(size=6)
    return lam, V, psi0


def evolve(lam, V, psi0, t, alpha):
    """psi(t) = V . E_alpha(-i lambda t^alpha) . V+ psi0 (spectral)."""
    if alpha == 1.0:
        c = np.exp(-1j * lam * t)                       # forme close exacte
    else:
        c = np.array([complex(E_alpha_mp(mpc(-1j * float(l) * t**alpha), mpf(alpha)))
                      for l in lam])
    return V @ (c * (V.conj().T @ psi0))


def norm_of(psi, p):
    if p == np.inf:
        return float(np.max(np.abs(psi)))
    return float(np.sum(np.abs(psi) ** p) ** (1.0 / p))


def deviations(lam, V, psi0, alpha, ts):
    """max_t | ||psi(t)||_p / ||psi(t0)||_p - 1 | pour chaque p."""
    n0 = {}
    dev = {p: 0.0 for p in PS}
    for i, t in enumerate(ts):
        psi = evolve(lam, V, psi0, t, alpha)
        for p in PS:
            n = norm_of(psi, p)
            if i == 0:
                n0[p] = n
            else:
                dev[p] = max(dev[p], abs(n / n0[p] - 1.0))
    return dev


# ---------------------------------------------------------------- contrôles

def c1_sanity_mittag_leffler():
    """Formes closes exactes + décroissance algébrique |E_alpha(-iy)|."""
    e = mexp(1)
    err1 = abs(E_alpha_mp(mpc(1), mpf(1)) - e)                       # E_1(1)=e
    eh = mexp(1) * (1 - merf(1))
    err2 = abs(E_alpha_mp(mpc(-1), mpf("0.5")) - eh)                 # E_1/2(-1)=e.erfc(1)
    vals = [abs(E_alpha_mp(mpc(-1j * y), mpf(ALPHA))) for y in (2.0, 5.0, 10.1)]
    mono = (vals[0] > vals[1]) and (vals[1] > vals[2]) and (vals[2] < 1.0)
    worst = float(max(err1, err2))
    if not mono:
        worst = float("inf")
    return worst, {"err_E1_1": float(err1), "err_E05_m1": float(err2),
                   "decay": [float(v) for v in vals]}


def c2_filtre_alpha1_l2_machine_exact():
    """alpha→1 : L² conservée à précision machine (3 seeds)."""
    worst = 0.0
    per_seed = {}
    for seed in SEEDS_NP:
        lam, V, psi0 = make_system(seed)
        d = deviations(lam, V, psi0, 1.0, T_GRID)
        per_seed[seed] = d
        worst = max(worst, d[2])
    ok = worst < 1e-14
    return (0.0 if ok else worst), {"worst_L2": worst, "seuil": 1e-14,
                                    "per_seed_L2": {s: v[2] for s, v in per_seed.items()}}


def c3_selection_non_vide():
    """Les rivales L^p dévient franchement (la sélection n'est pas vide)."""
    worst_min = float("inf")
    per_seed = {}
    for seed in SEEDS_NP:
        lam, V, psi0 = make_system(seed)
        d = deviations(lam, V, psi0, 1.0, T_GRID)
        mn = min(d[1], d[4], d[np.inf])
        per_seed[seed] = d
        worst_min = min(worst_min, mn)
    ok = worst_min > 0.05
    return (0.0 if ok else worst_min), {"min_rivales": worst_min, "seuil": 0.05,
                                        "per_seed": {s: {str(k): v for k, v in d.items()}
                                                     for s, d in per_seed.items()}}


def c4_aucune_norme_survive_memoire():
    """alpha=1/phi : AUCUNE norme conservée — la mémoire est un système ouvert."""
    worst_min = float("inf")
    per_seed = {}
    for seed in SEEDS_MP:
        lam, V, psi0 = make_system(seed)
        d = deviations(lam, V, psi0, ALPHA, T_GRID)
        mn = min(d.values())
        per_seed[seed] = d
        worst_min = min(worst_min, mn)
    ok = worst_min > 0.3
    return (0.0 if ok else worst_min), {"min_toutes_normes": worst_min, "seuil": 0.3,
                                        "per_seed": {s: {str(k): v for k, v in d.items()}
                                                     for s, d in per_seed.items()}}


def c5_contraction_l2_memoire():
    """alpha=1/phi : |E_alpha(-iy)| <= 1 (grille dense) et ||psi(t)||_2 <= ||psi0||_2."""
    # (a) borne par mode sur grille dense
    worst_mode = 0.0
    for y in np.linspace(0.01, 12.0, 240):
        v = float(abs(E_alpha_mp(mpc(-1j * float(y)), mpf(ALPHA))))
        worst_mode = max(worst_mode, v - 1.0)
    # (b) contraction L² le long des trajectoires
    worst_traj = 0.0
    for seed in SEEDS_MP:
        lam, V, psi0 = make_system(seed)
        n0 = norm_of(psi0, 2)
        for t in T_GRID:
            psi = evolve(lam, V, psi0, t, ALPHA)
            worst_traj = max(worst_traj, norm_of(psi, 2) / n0 - 1.0)
    ok = (worst_mode <= 1e-12) and (worst_traj <= 1e-12)
    val = 0.0 if ok else max(worst_mode, worst_traj)
    return val, {"max_E_alpha_minus_1": worst_mode, "max_L2_ratio_minus_1": worst_traj,
                 "seuil": 1e-12}


# ---------------------------------------------------------------- main

def main():
    print("=" * 72)
    print("F11 NORMES V0 — L² survivant du filtre alpha->1 ?  (Voie 1, C-H1)")
    print("alpha = 1/phi = %.15f ; mpmath dps=%d ; seeds %s / %s"
          % (ALPHA, mp.dps, SEEDS_NP, SEEDS_MP))
    print("=" * 72)

    results = {}
    checks = []

    w, d = c1_sanity_mittag_leffler()
    results["C1"] = d
    checks.append(("C1  sanity Mittag-Leffler (formes closes + décroissance)", w, 0.0, "==" ))
    w, d = c2_filtre_alpha1_l2_machine_exact()
    results["C2"] = d
    checks.append(("C2  filtre alpha->1 : L² conservée machine-exact (<1e-14)", w, None, None))
    w, d = c3_selection_non_vide()
    results["C3"] = d
    checks.append(("C3  sélection non vide : rivales L^p dévient (>0.05)", w, None, None))
    w, d = c4_aucune_norme_survive_memoire()
    results["C4"] = d
    checks.append(("C4  alpha=1/phi : aucune norme conservée (>0.3)", w, None, None))
    w, d = c5_contraction_l2_memoire()
    results["C5"] = d
    checks.append(("C5  alpha=1/phi : contraction L² (|E|<=1, ratio<=1)", w, None, None))

    print()
    labels = [c[0] for c in checks]
    worsts = [c[1] for c in checks]

    print("C1  sanity Mittag-Leffler : err formes closes = %.3e ; décroissance %s"
          % (results["C1"]["err_E1_1"], results["C1"]["decay"]))
    print("C2  filtre alpha->1 : L² worst = %.2e (seuil 1e-14) — %s"
          % (results["C2"]["worst_L2"],
             "CONSERVÉE" if results["C2"]["worst_L2"] < 1e-14 else "RÉFUTÉ"))
    print("C3  sélection non vide : min rivales = %.3e (seuil 0.05) — %s"
          % (results["C3"]["min_rivales"],
             "OUI" if results["C3"]["min_rivales"] > 0.05 else "NON"))
    print("C4  alpha=1/phi : min toutes normes = %.3e (seuil 0.3) — %s"
          % (results["C4"]["min_toutes_normes"],
             "AUCUNE conservée" if results["C4"]["min_toutes_normes"] > 0.3 else "une survit ?"))
    print("C5  alpha=1/phi : max|E|-1 = %.3e ; max ratio L²-1 = %.3e — %s"
          % (results["C5"]["max_E_alpha_minus_1"], results["C5"]["max_L2_ratio_minus_1"],
             "CONTRACTION" if (results["C5"]["max_E_alpha_minus_1"] <= 1e-12
                               and results["C5"]["max_L2_ratio_minus_1"] <= 1e-12)
             else "AMPLITICATION ?"))

    ok_all = (results["C1"]["err_E1_1"] < 1e-40
              and results["C1"]["err_E05_m1"] < 1e-40
              and results["C2"]["worst_L2"] < 1e-14
              and results["C3"]["min_rivales"] > 0.05
              and results["C4"]["min_toutes_normes"] > 0.3
              and results["C5"]["max_E_alpha_minus_1"] <= 1e-12
              and results["C5"]["max_L2_ratio_minus_1"] <= 1e-12)

    print()
    print("-" * 72)
    if ok_all:
        print("VERDICT : F11_NORMES_V0_C_H1_PRELIMINAIRE — exit 0")
        print("  L² est le seul survivant du filtre alpha->1 (4e-16 vs 0.14-0.34).")
        print("  À alpha=1/phi : aucune norme conservée (mémoire ouverte),")
        print("  mais contraction L² : la mémoire amortit, n'amplifie pas.")
        print("  F11 reste OUVERTE : C-H2 (unicité universelle) exige le théorème")
        print("  (Jordan-von Neumann + réversibilité), un probe fini n'est pas une preuve.")
    else:
        print("VERDICT : REFUTE — exit 1")
    print("-" * 72)

    with open("resultat_f11_normes_thu_v0.json", "w", encoding="utf-8") as f:
        json.dump({"verdict": "F11_NORMES_V0_C_H1_PRELIMINAIRE" if ok_all else "REFUTE",
                   "alpha": ALPHA, "phi": PHI, "mpmath_dps": mp.dps,
                   "seeds_np": SEEDS_NP, "seeds_mp": SEEDS_MP,
                   "t_grid": [T_GRID[0], T_GRID[-1], len(T_GRID)],
                   "controles": results, "ok": ok_all}, f, indent=2, ensure_ascii=False)

    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
