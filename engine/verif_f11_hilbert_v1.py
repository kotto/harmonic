#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F11 HILBERT V1 — Voie 2 : par plan en TOUTE dimension + fermeture globale
==========================================================================
Suite de verif_f11_hilbert_v0 (C-H2, dim. finie). Deux théorèmes, une matrice.

THÉORÈME A (Voie 2a — TOUTE dimension, sans complétude, sans spectre) :
  Soit E un espace réel (dimension quelconque) muni d'une structure par plans
  P_k ≅ ℝ², J la rotation de 90° sur chaque plan (J² = −I), et ‖·‖ une norme
  invariante sous R(nθ) = cos(nθ)·I + sin(nθ)·J pour tout n ∈ ℤ, avec θ/π
  irrationnel. Alors :
    (a) sur CHAQUE plan, ‖x‖ = c_k·|x_k|₂ (arène euclidienne par plan) ;
    (b) j = R(π/2) est dans la clôture du groupe (j² = −I, isométrie) → ℂ émerge.
  Preuve (locale, sans équivalence globale des normes) :
    1. R(nθ)|_{P_x} = rot(nθ) : le groupe agit dans le plan de x seulement ;
    2. {nθ mod 2π} dense (Kronecker — θ/π = 1/(2φ) irrationnel) ;
    3. la restriction ν = ‖·‖|_{P_x} est une norme sur ℝ² donc continue
       (équivalence des normes EN DIMENSION 2 — légitime, local) ;
    4. montée stroboscopique→cercle SANS hypothèse de dimension :
       ‖(e^{in_kθ} − e^{iφ})x‖ = |e^{in_kθ} − e^{iφ}|·‖x‖ → 0 (scalaire × x) ;
    5. ν invariante sous SO(2) planaire ⟹ ν = c·|·|₂ (transitivité sur le cercle). ∎
  → L'objection « dimension infinie » de V0 (pas 3 global) DISSOUT : l'argument
  ne vit que dans un plan de dimension 2.

THÉORÈME B (C-H2 global, dimension finie — trois entrées, toutes nécessaires) :
  ‖·‖ norme sur ℂⁿ (vu réel, 2n) telle que
    (i)   invariance sous le cercle central {R(φ)} (mémoire, α = 1/φ) ;
    (ii)  invariance sous e^{−iHt} pour TOUT hermitien H admissible
          (universalité de la limite α→1 — le mélangeur n'est pas fixé par la
          théorie, la classe couvre tous les systèmes) ;
    (iii) loi du parallélogramme (Jordan–von Neumann).
  Alors ‖x‖ = c·|x|₂ — la norme de Hilbert, au scalaire près.
  Preuve : (iii) ⟹ B symétrique définie positive, ‖x‖² = B(x,x) ;
    (i) ⟺ j anti-auto-adjoint pour B ⟺ ‖x‖² = Re(z†Mz), M hermitienne ≥ 0
    (les blocs [[Re M, −Im M],[Im M, Re M]] commutent avec j₂ : aucune
    contrainte de plus — (i) dit exactement « M hermitienne ») ;
    (ii) ⟹ S commute avec O_H(t) ∀t, ∀H ⟹ [M, H] = 0 ∀H admissible ⟹
    M = cI (la classe est assez riche : tous les hermitiens) ⟹ c > 0. ∎
  Contre-exemples (matrice de falsifiabilité, C5) : chaque entrée omise laisse
  survivre une norme non hilbertienne — un SEUL mélangeur ne sélectionne rien
  (wℓ² dans la base propre de ce H survit) : c'est l'UNIVERSALITÉ de la classe
  qui ferme l'arène.

AUTO-CORRECTION V0 CONSIGNÉE :
  V0-C3 testait des orthogonales aléatoires — c'est le filtre (ii) α→1, PAS la
  rotation Bateman seule. Sous la seule rotation, la famille F(rayons)
  (ℓ^p de rayons plans) survit en dimension ≥ 4 : le théorème V0 (PAR PLAN)
  reste vrai, mais la lecture globale exige (ii)+(iii). Consigné en C3/C5.

Contrôles :
  C1  Bateman ∀α + identification cercle central R(φ) = realrep(e^{iφ}·I)
  C2  Densité stroboscopique→cercle, indépendance de dimension (N = 4, 16, 64)
  C3  Théorème A : invariance cercle de la famille F ; euclidénisation PAR
      PLAN exacte (N = 4, 16, 64) ; défaut parallélogramme global ≠ 0 (F ≠ ℓ²)
  C4  Filtre α→1 : cohérence du générateur réel ; classe de 12 mélanges ;
      ℓ² passe ∀H, chaque rivale échoue sur ≥ 1 H
  C5  Matrice de falsifiabilité (les 3 entrées nécessaires, motif exact)
  C6  Sonde complétude : Σ cₙ → E_{1/φ}(1) (Cauchy) ; c₀₀ dense dans ℓ² ;
      la complétude TOTALE reste ouverte (consigné)

Verdict exit 0 = conforme, exit 1 = réfuté.
"""

import sys
import json
import math
import cmath
import numpy as np
from mpmath import mp, mpf, gamma as mp_gamma

PHI = (1.0 + math.sqrt(5.0)) / 2.0
ALPHA = 1.0 / PHI
THETA = math.pi * ALPHA / 2.0            # 55.6231° = 90/φ degrés
N_ORBIT = 2000
TOL_EXACT = 1e-12
TOL_FAIL = 0.02
K_H = 12                                  # mélanges de la classe (universalité)
N_GRID = (4, 16, 64)                      # indépendance de dimension (Th. A)


# ----------------------------------------------------------------- outils

def realrep(U):
    """Matrice complexe n×n → réelle 2n×2n, coordonnées entrelacées
    (Re z_0, Im z_0, ..., Re z_{n-1}, Im z_{n-1}). Isomorphisme d'algèbres."""
    n = U.shape[0]
    R = np.zeros((2 * n, 2 * n))
    R[0::2, 0::2] = U.real
    R[0::2, 1::2] = -U.imag
    R[1::2, 0::2] = U.imag
    R[1::2, 1::2] = U.real
    return R


def hermitian(n, seed):
    """Hermitienne gaussienne générique P + iQ (P sym., Q antisym.)."""
    rng = np.random.default_rng(seed)
    A = rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))
    return (A + A.conj().T) / 2.0


def unitary_flow(H, t):
    """e^{−iHt} par diagonalisation (H hermitienne)."""
    lam, V = np.linalg.eigh(H)
    return (V * np.exp(-1j * lam * t)) @ V.conj().T


def radii(x, n):
    """Rayons plans r_k = |z_k| (coordonnées entrelacées)."""
    return np.linalg.norm(x.reshape(n, 2), axis=1)


def para_defect(nf, x, y):
    """Défaut de parallélogramme normalisé : |D(x,y)| / (‖x‖²+‖y‖²)."""
    nx, ny = nf(x) ** 2, nf(y) ** 2
    d = nf(x + y) ** 2 + nf(x - y) ** 2 - 2 * nx - 2 * ny
    return abs(d) / (nx + ny)


# ------------------------------------------------------- familles de normes

def make_norms(n, H1):
    """Candidats sur ℝ^{2n}. Retour : dict nom → (norme, tags)."""
    V1 = np.linalg.eigh(H1)[1]
    W1 = realrep(V1.conj().T)                 # base propre de H1 (réelle)
    cw = 1.0 / (np.arange(n) + 1.0)           # poids 1/(k+1)

    def r(x):
        return radii(x, n)

    def nF1(x):
        return float(np.sum(r(x)))

    def nF15(x):
        return float(np.sum(r(x) ** 1.5) ** (1.0 / 1.5))

    def nF2(x):
        return float(np.sqrt(np.sum(r(x) ** 2)))

    def nF4(x):
        return float(np.sum(r(x) ** 4) ** 0.25)

    def nFmax(x):
        return float(np.max(r(x)))

    def nWQ2mode(x):
        return float(np.sqrt(np.sum(cw * r(x) ** 2)))

    def nWQ2H(x):
        v = W1 @ x
        return float(np.sqrt(np.sum(cw * radii(v, n) ** 2)))

    def nL1modH(x):
        v = W1 @ x
        return float(np.sum(radii(v, n)))

    def nAniso(x):
        e = x.reshape(n, 2)
        return float(np.sqrt(np.sum(1.5 * e[:, 0] ** 2 + 0.7 * e[:, 1] ** 2)))

    return {
        "L2":            (nF2,       {"cercle": True,  "quad": True}),
        "F1_rayons":     (nF1,       {"cercle": True,  "quad": False}),
        "F1.5_rayons":   (nF15,      {"cercle": True,  "quad": False}),
        "F4_rayons":     (nF4,       {"cercle": True,  "quad": False}),
        "Fmax_rayons":   (nFmax,     {"cercle": True,  "quad": False}),
        "wL2_modes":     (nWQ2mode,  {"cercle": True,  "quad": True}),
        "wL2_baseH1":    (nWQ2H,     {"cercle": True,  "quad": True}),
        "L1_modules_H1": (nL1modH,   {"cercle": True,  "quad": False}),
        "aniso_quad":    (nAniso,    {"cercle": False, "quad": True}),
    }


# ---------------------------------------------------------------- contrôles

def c1_bateman_et_cercle_central():
    """Bateman ∀α (V0) + R(φ) = realrep(e^{iφ}I) : le cercle mémoir est central."""
    worst = 0.0
    detail = {}
    for a in (0.3, 0.5, ALPHA, 0.8, 0.95):
        th = math.pi * a / 2.0
        R = realrep(cmath.exp(1j * th) * np.eye(3))
        det = float(np.linalg.det(R))
        # multiset des valeurs propres comparé trié (l'ordre d'eigvals n'est
        # pas garanti — leçon : jamais ev[0] vs cible en position fixe)
        ev = np.sort_complex(np.linalg.eigvals(R))
        tgt = cmath.exp(1j * th)
        tgt_arr = np.sort_complex(np.array(
            [tgt, np.conj(tgt)] * 3, dtype=complex))
        err_ev = float(np.max(np.abs(ev - tgt_arr)))
        err_orth = float(np.linalg.norm(R.T @ R - np.eye(6), ord=2))
        w = max(abs(det - 1.0), err_ev, err_orth)
        detail[a] = {"det": det, "err_eigen": float(err_ev), "err_orth": err_orth}
        worst = max(worst, w)
    return worst, detail


def c2_densite_independante_dimension():
    """Stroboscopique → cercle, SANS hypothèse de dimension :
    ‖R(n*θ) − j‖₂ (opérateur) = |e^{in*θ} − i| = 2|sin(Δ/2)| identique ∀N."""
    ang = np.array([(n * THETA) % (2 * math.pi) for n in range(1, N_ORBIT + 1)])
    ang_s = np.sort(ang)
    gaps = np.diff(np.concatenate([ang_s, [ang_s[0] + 2 * math.pi]]))
    cov_const = float(np.max(gaps)) * N_ORBIT / (2 * math.pi)
    dist_j = np.abs(((ang - math.pi / 2 + math.pi) % (2 * math.pi)) - math.pi)
    n_star = int(np.argmin(dist_j)) + 1
    delta = float(dist_j.min())
    theo = 2.0 * abs(math.sin((n_star * THETA - math.pi / 2) / 2.0))
    ops = {}
    for N in N_GRID:
        Rn = realrep(cmath.exp(1j * n_star * THETA) * np.eye(N))
        J = realrep(1j * np.eye(N))
        ops[N] = float(np.linalg.norm(Rn - J, 2))
    spread = max(ops.values()) - min(ops.values())
    err_theo = max(abs(v - theo) for v in ops.values())
    ok = (cov_const <= 8.0) and (delta <= 2 * math.pi / 200.0) \
        and (spread < 1e-14) and (err_theo < 1e-12)
    val = 0.0 if ok else max(cov_const - 8.0, delta, spread, err_theo)
    return val, {"theta_sur_pi": THETA / math.pi, "cible": 1.0 / (2 * PHI),
                 "constante_couverture": cov_const, "n_proche_j": n_star,
                 "dist_j": delta, "norme_operateur_par_N": ops,
                 "theorique_2sin": theo, "spread_entre_N": spread,
                 "err_vs_theorie": err_theo}


def c3_theoreme_A_par_plan():
    """(a) famille F invariante sous le cercle échantillonné ;
    (b) euclidénisation PAR PLAN exacte, N = 4, 16, 64 ;
    (c) défaut parallélogramme GLOBAL : seules les quadratiques sont nulles."""
    phis = [math.pi * j / 12.0 for j in range(1, 12)]
    phis += [(n * THETA) % (2 * math.pi) for n in (1, 7, 43, 610, 1500)]
    per_N = {}
    worst_inv = 0.0
    worst_plan = 0.0
    para = {}
    for N in N_GRID:
        H1 = hermitian(N, 7)
        norms = make_norms(N, H1)
        rng = np.random.default_rng(20 + N)
        xs = [rng.normal(size=2 * N) for _ in range(6)]
        # (a) invariance sous le cercle
        for name, (nf, tags) in norms.items():
            if not tags["cercle"]:
                continue
            n0 = [nf(x) for x in xs]
            for phi in phis:
                g = realrep(cmath.exp(1j * phi) * np.eye(N))
                for x, m0 in zip(xs, n0):
                    worst_inv = max(worst_inv, abs(nf(g @ x) / m0 - 1.0))
        # (b) euclidénisation par plan : F restreinte à P_k = c_k|x_k|₂
        for name, (nf, tags) in norms.items():
            if not tags["cercle"]:
                continue
            for k in range(0, N, max(1, N // 4)):
                e1 = np.zeros(2 * N)
                e1[2 * k] = 1.0
                c_k = nf(e1)
                for _ in range(6):
                    u = rng.normal(size=2)
                    x = np.zeros(2 * N)
                    x[2 * k:2 * k + 2] = u
                    rk = float(np.linalg.norm(u))
                    worst_plan = max(worst_plan, abs(nf(x) / (c_k * rk) - 1.0))
        # (c) parallélogramme global (au moins au N le plus grand)
        if N == N_GRID[-1]:
            for name, (nf, tags) in norms.items():
                d = 0.0
                for _ in range(50):
                    x = rng.normal(size=2 * N)
                    y = rng.normal(size=2 * N)
                    d = max(d, para_defect(nf, x, y))
                para[name] = d
    quad_ok = all(para[n] < TOL_EXACT for n in ("L2", "wL2_modes", "wL2_baseH1",
                                                "aniso_quad"))
    nonquad_min = min(para[n] for n in ("F1_rayons", "F1.5_rayons", "F4_rayons",
                                        "Fmax_rayons", "L1_modules_H1"))
    ok = (worst_inv < TOL_EXACT) and (worst_plan < TOL_EXACT) \
        and quad_ok and (nonquad_min > 0.05)
    val = 0.0 if ok else max(worst_inv, worst_plan, 0.05 - nonquad_min)
    return val, {"invariance_cercle_worst": worst_inv,
                 "euclidianisation_par_plan_worst": worst_plan,
                 "N_grid": list(N_GRID),
                 "parallelogramme": para, "nonquad_min": nonquad_min}


def c4_filtre_alpha1_classe():
    """Générateur réel cohérent + classe de K_H mélanges : ℓ² passe ∀H,
    chaque rivale échoue sur au moins un H (universalité = le verrou)."""
    n = 8
    Hs = [hermitian(n, 101 + s) for s in range(K_H)]
    # cohérence du générateur réel : (E(t)−E(−t))/2t ≈ realrep(−iH)
    B = realrep(-1j * Hs[0])
    t = 1e-5
    gen_err = float(np.max(np.abs(
        (realrep(unitary_flow(Hs[0], t)) - realrep(unitary_flow(Hs[0], -t)))
        / (2 * t) - B)))
    gaps = []
    for H in Hs:
        lam = np.linalg.eigvalsh(H)
        gaps.append(float(np.min(np.diff(np.sort(lam)))))
    min_gap = min(gaps)
    norms = make_norms(n, Hs[0])
    ts = np.linspace(0.05, 6.0, 25)
    rng = np.random.default_rng(30)
    xs = [rng.normal(size=2 * n) for _ in range(5)]
    dev = {name: 0.0 for name in norms}
    for H in Hs:
        for t_ in ts:
            G = realrep(unitary_flow(H, t_))
            for name, (nf, tags) in norms.items():
                if name == "L2":
                    continue
                for x in xs:
                    dev[name] = max(dev[name],
                                    abs(nf(G @ x) / nf(x) - 1.0))
    l2 = 0.0
    for H in Hs:
        for t_ in ts:
            G = realrep(unitary_flow(H, t_))
            for x in xs:
                l2 = max(l2, abs(np.linalg.norm(G @ x) / np.linalg.norm(x) - 1.0))
    # leçon : dev est copié sur tous les candidats, donc contient L2 (le
    # survivant attendu, sauté dans la boucle) — le min des RIVALES doit
    # l'exclure explicitement, sinon le témoin lui-même fait échouer C4
    rivals_min = min(v for k, v in dev.items() if k != "L2")
    ok = (gen_err < 1e-8) and (min_gap > 1e-6) and (l2 < 1e-14) \
        and (rivals_min > TOL_FAIL)
    val = 0.0 if ok else max(gen_err, l2, TOL_FAIL - rivals_min)
    return val, {"err_generateur": gen_err, "min_ecart_spectral": min_gap,
                 "K_H": K_H, "L2_worst": l2, "rivales_min": rivals_min,
                 "dev_par_candidat": dev}


def c5_matrice_falsifiabilite():
    """Motif exact : (i) cercle / (ii) son H / (ii) classe / (iii) parallélogramme.
    Chaque entrée omise laisse survivre une norme non hilbertienne."""
    n = 8
    H1 = hermitian(n, 7)
    Hs = [hermitian(n, 101 + s) for s in range(K_H)]
    norms = make_norms(n, H1)
    ts = np.linspace(0.05, 6.0, 25)
    phis = [math.pi * j / 12.0 for j in range(1, 12)]
    rng = np.random.default_rng(40)
    xs = [rng.normal(size=2 * n) for _ in range(5)]
    tab = {}
    for name, (nf, tags) in norms.items():
        # (i) cercle central
        dc = 0.0
        for phi in phis:
            g = realrep(cmath.exp(1j * phi) * np.eye(n))
            for x in xs:
                dc = max(dc, abs(nf(g @ x) / nf(x) - 1.0))
        # (ii) son propre H (H1)
        do = 0.0
        for t_ in ts:
            G = realrep(unitary_flow(H1, t_))
            for x in xs:
                do = max(do, abs(nf(G @ x) / nf(x) - 1.0))
        # (ii) classe complète
        dcl = 0.0
        for H in Hs:
            for t_ in ts:
                G = realrep(unitary_flow(H, t_))
                for x in xs:
                    dcl = max(dcl, abs(nf(G @ x) / nf(x) - 1.0))
        # (iii) parallélogramme
        dp = 0.0
        for _ in range(50):
            x = rng.normal(size=2 * n)
            y = rng.normal(size=2 * n)
            dp = max(dp, para_defect(nf, x, y))
        tab[name] = {"cercle": dc, "son_H": do, "classe": dcl, "parallelogramme": dp}
    # motif attendu (seuils : passe < 1e-12, échec > TOL_FAIL)
    motif = {
        "L2":            dict(cercle=True,  son_H=True,  classe=True,  para=True),
        "F1_rayons":     dict(cercle=True,  son_H=False, classe=False, para=False),
        "F1.5_rayons":   dict(cercle=True,  son_H=False, classe=False, para=False),
        "F4_rayons":     dict(cercle=True,  son_H=False, classe=False, para=False),
        "Fmax_rayons":   dict(cercle=True,  son_H=False, classe=False, para=False),
        "wL2_modes":     dict(cercle=True,  son_H=False, classe=False, para=True),
        "wL2_baseH1":    dict(cercle=True,  son_H=True,  classe=False, para=True),
        "L1_modules_H1": dict(cercle=True,  son_H=True,  classe=False, para=False),
        "aniso_quad":    dict(cercle=False, son_H=False, classe=False, para=True),
    }
    ok = True
    worst = 0.0
    for name, m in motif.items():
        t = tab[name]
        checks = [
            (t["cercle"] < 1e-12) == m["cercle"],
            (t["son_H"] < 1e-12) == m["son_H"],
            (t["classe"] < 1e-12) == m["classe"],
            (t["parallelogramme"] < 1e-12) == m["para"],
        ]
        if not all(checks):
            ok = False
            worst = max(worst, 1.0)
    return (0.0 if ok else 1.0), {"tableau": tab, "motif_attendu": motif}


def c6_sonde_completude():
    """(a) les coefficients mères cₙ = 1/Γ(n/φ+1) sont sommables : Σcₙ = E_{1/φ}(1),
    suites partielles de Cauchy ; (b) c₀₀ est dense dans ℓ² (troncations).
    La complétude TOTALE reste une exigence non dérivée — consigné."""
    mp.dps = 40
    phi_mp = mpf(1 + math.sqrt(5)) / 2
    inv_phi = 1 / phi_mp
    S_inf = mpf(0)
    n = 0
    while True:
        term = 1 / mp_gamma(n / inv_phi + 1)
        if term < mpf(10) ** (-38):
            break
        S_inf += term
        n += 1
        if n > 400:
            break
    S30 = mpf(0)
    S60 = mpf(0)
    for k in range(0, 61):
        term = 1 / mp_gamma(k / inv_phi + 1)
        if k <= 30:
            S30 += term
        S60 += term
    err30 = abs(S30 - S_inf)
    err60 = abs(S60 - S_inf)
    # (b) densité de c₀₀ dans ℓ² : résidus de troncation décroissants → 0
    rng = np.random.default_rng(50)
    x = rng.normal(size=512)
    x /= np.linalg.norm(x)
    resid = []
    for k in (8, 64, 256):
        resid.append(float(np.linalg.norm(x[k:]) / np.linalg.norm(x)))
    decroissant = all(resid[i] > resid[i + 1] for i in range(len(resid) - 1))
    ok = (err30 < mpf(10) ** (-16)) and (err60 < mpf(10) ** (-34)) \
        and decroissant and (resid[-1] < 0.75)
    val = 0.0 if ok else 1.0
    return val, {"E_1_sur_phi_de_1": float(S_inf), "err_S30": float(err30),
                 "err_S60": float(err60), "residus_troncature": resid,
                 "note": "complétude totale : ouverte (consignée)"}


# ------------------------------------------------------------------- main

def main():
    print("=" * 72)
    print("F11 HILBERT V1 — Voie 2 : par plan en TOUTE dimension + fermeture")
    print("θ = πα/2 = %.6f rad ; θ/π = %.12f ; 1/(2φ) = %.12f"
          % (THETA, THETA / math.pi, 1 / (2 * PHI)))
    print("=" * 72)

    w1, d1 = c1_bateman_et_cercle_central()
    w2, d2 = c2_densite_independante_dimension()
    w3, d3 = c3_theoreme_A_par_plan()
    w4, d4 = c4_filtre_alpha1_classe()
    w5, d5 = c5_matrice_falsifiabilite()
    w6, d6 = c6_sonde_completude()

    print()
    print("C1  Bateman ∀α + cercle central : worst = %.3e" % w1)
    print("C2  densité (toute dim.)  : couverture %.2f (≤8) ; n*=%d, dist j = %.3e"
          % (d2["constante_couverture"], d2["n_proche_j"], d2["dist_j"]))
    print("     ‖R(n*θ)−j‖ op.       : théorie %.3e ; spread entre N = %.1e ;"
          " err théorie %.1e" % (d2["theorique_2sin"], d2["spread_entre_N"],
                                 d2["err_vs_theorie"]))
    print("C3  Théorème A            : invariance cercle %.1e ; par plan %.1e"
          " (N = 4,16,64)" % (d3["invariance_cercle_worst"],
                              d3["euclidianisation_par_plan_worst"]))
    print("     parallélogramme      : quadratiques nulles ; non-quad min = %.3f"
          % d3["nonquad_min"])
    print("C4  classe α→1 (K=%d)      : générateur %.1e ; L² %.1e ; rivales min %.3f"
          % (d4["K_H"], d4["err_generateur"], d4["L2_worst"], d4["rivales_min"]))
    print("C5  matrice falsifiabilité : motif %s"
          % ("CONFORME" if w5 == 0.0 else "REFUTE"))
    print("C6  sonde complétude      : E_{1/φ}(1) = %.12f ; err S30 = %.1e ;"
          " résidus %s" % (d6["E_1_sur_phi_de_1"], d6["err_S30"],
                           ["%.3f" % r for r in d6["residus_troncature"]]))

    ok = (w1 < 1e-14) and (w2 == 0.0) and (w3 == 0.0) and (w4 == 0.0) \
        and (w5 == 0.0) and (w6 == 0.0)

    print()
    print("-" * 72)
    if ok:
        print("VERDICT : F11_HILBERT_V1_VOIE2A_PAR_PLAN_TOUTE_DIMENSION — exit 0")
        print("  Théorème A : la mémoire (angle d'or) ferme chaque plan — en")
        print("  TOUTE dimension, sans complétude ni spectre. j émerge, ℂ émerge.")
        print("  Théorème B : mémoire (cercle) + universalité du mélangeur (α→1)")
        print("  + parallélogramme ⟹ arène de Hilbert unique (dim. finie).")
        print("  Reste ouvert (consigné) : théorème B en dim. infinie (commutant")
        print("  fonctionnel-analytique), complétude totale, spectral (Voie 3).")
    else:
        print("VERDICT : REFUTE — exit 1")
    print("-" * 72)

    with open("resultat_f11_hilbert_v1.json", "w", encoding="utf-8") as f:
        json.dump({"verdict": "F11_HILBERT_V1_VOIE2A_PAR_PLAN_TOUTE_DIMENSION"
                   if ok else "REFUTE",
                   "alpha": ALPHA, "theta": THETA,
                   "theta_sur_pi": THETA / math.pi,
                   "controles": {"C1": d1, "C2": d2, "C3": d3, "C4": d4,
                                 "C5": d5, "C6": d6},
                   "ok": ok},
                  f, indent=2, ensure_ascii=False, default=float)

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
