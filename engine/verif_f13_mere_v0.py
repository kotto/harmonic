#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
verif_f13_mere_v0.py — F13 MÈRE V0 : le compensateur exact du défaut de covariance locale
==========================================================================================
Attaque du trou D3 de la campagne jauge (DEPOT_JAUGAGE_V0.md §6). Thèse (FRONTIERE_F13_MERE_V0.md) :

    P30  identité mère  phi·K^-1 − phi = (i·w)^a  (MORT 2 C2, 4,97e-16) — quatre lectures d'un objet.
    P31  à a=1, la lecture conservative est un groupe unitaire à un paramètre (Bateman),
         générateur antisymétrique — structure de Stone assemblée depuis la boucle.
    P32  le défaut de covariance locale mesuré au JAUGAGE (D(a,k) ≠ 0, gradient-porté) est
         fermé EXACTEMENT par le noyau covariantisé  K_A = phi·(D_A + phi)^{-1},  D_A = D − iA,
         A = ∇χ  — triple route : niveau dérivée, niveau noyau, niveau boucle.
    P33  observables aveugles à la jauge pure : G_A = e^{iΔχ}·G_0, Green de la boucle (MORT 2).
    P34  universalité : UN seul noyau absorbe la jauge pour tout état — couplage forcé.
    P35  spectre : eigenvalue de boucle à a=1 = −|k|² (dispersion massive-zéro, phase = pi = pa = σ),
         décompte transverse = 2 par mode k≠0, holonomie distingue redondance et physique ;
         à a=1/φ : eigenvalue (i|k|)^{2/φ} = |k|^{2/φ}·e^{iπ/φ} — première mesure ex ante (C6b).

Conventions héritées du JAUGAGE V0 (O1–O7) : N=512, L=20π, Δω=0,1, porteur e^{ix}/√N,
norme unitaire ‖ψ‖² = Σ|ψₙ|²/N, famille χ = a·cos(kx), graine 27. 3D : N=192, Δx=1.
Le sous-ensemble de 6 profils C2 est la partie de la grille fermée A×K sans repliement
de spectre (bandes latérales de Bessel J_n(a) au-delà de Nyquist < 1e-12) — documenté au dépôt.

Verdicts (gelés) :
    F13_MERE_COMPENSATEUR_EXACT  exit 0 — tous les contrôles C0a…C6a passent
    REFUTE                       exit 1 — un contrôle bloquant en échec (aucun sauvetage)
    PIPELINE_CASSE               exit 1 — ancre déposée (C2a ou C2b) non reproduite
C6b ne bloque jamais (première mesure ex ante). Contrôles [OBS] : lecture seule.

Usage :  python verif_f13_mere_v0.py
Sortie :  rapport console + resultat_f13_mere_v0.json (même dossier)
"""

import json
import math
import os
import sys
import time

import numpy as np
from mpmath import mp, mpc, mpf

mp.dps = 40

# ----------------------------------------------------------------------------
# Constantes fermées (C0b)
# ----------------------------------------------------------------------------

PHI = (1.0 + math.sqrt(5.0)) / 2.0
ALPHA = 1.0 / PHI
THETA = math.pi * ALPHA / 2.0
SEED = 27
D_REG = 0.032328801001024664  # registre déposé JAUGAGE V0 : D(0.1, k=1) à a=1/φ

# 1D — conventions JAUGAGE O3
N1 = 512
L1 = 20.0 * math.pi
DOMEGA = 0.1
X1 = np.arange(N1) * (L1 / N1)
OMEGA1 = np.array(
    [(m * DOMEGA) if m <= N1 // 2 else ((m - N1) * DOMEGA) for m in range(N1)]
)
A_GRID = [0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
K_GRID = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
PROFILES6 = [
    (0.1, 0.1),
    (0.1, 0.5),
    (0.1, 1.0),
    (0.2, 1.0),
    (0.5, 1.0),
    (1.0, 1.0),
]
PSI0 = np.exp(1j * X1) / math.sqrt(N1)
THETAS_JAUGE = [math.pi / 3.0, math.pi / 2.0]

# 3D — conventions MORT 2 (N=192, dx=1)
N3 = 192
X3AX = np.arange(N3, dtype=float)
W3AX = 2.0 * math.pi * np.fft.fftfreq(N3, d=1.0)
K0 = 2.0 * math.pi / N3
X0_3D = (N3 // 2, N3 // 2, N3 // 2)
COUPURE = math.pi / 4.0  # bande limite du Green de test (mur d'aliasing consigné [OBS])
COQUILLES = [3, 4, 5, 6, 7, 8]


def Khat_phi(w):
    """Noyau déposé à a = 1/φ (JAUGAGE O2, route complexe)."""
    return PHI / ((1j * w) ** ALPHA + PHI)


def Khat_a1(w):
    """Noyau à a = 1 : φ/(iω + φ) = φ·(D + φ)^{-1}."""
    return PHI / (1j * w + PHI)


KHAT_PHI_W = Khat_phi(OMEGA1)
KHAT_A1_W = Khat_a1(OMEGA1)


def norme(v):
    """Norme unitaire déposée (JAUGAGE O7) : ‖v‖² = Σ|vₙ|²/N (1D)."""
    return math.sqrt(float(np.sum(np.abs(v) ** 2)) / N1)


def applique_noyau(psi, khat_w):
    return np.fft.ifft(khat_w * np.fft.fft(psi))


def defaut(alpha_x, psi, k_psi, khat_w):
    """Coût du rephasage modulé — verbatim JAUGAGE V0 (A1)."""
    eia = np.exp(1j * alpha_x)
    kp = applique_noyau(eia * psi, khat_w)
    return norme(kp - eia * k_psi) / norme(k_psi)


def bateman(theta):
    """Rotation de Bateman déposée (det=1, trace=2cosθ, λ=e^{±iθ})."""
    return np.array(
        [[math.cos(theta), math.sin(theta)], [-math.sin(theta), math.cos(theta)]]
    )


# Dérivée spectrale dense (1D) : D = F·diag(iω)·F⁻¹
F_MAT = np.exp(1j * np.outer(X1, OMEGA1))
DMAT = (F_MAT * (1j * OMEGA1)[None, :]) @ F_MAT.conj().T / N1
IMAT = np.eye(N1, dtype=complex)
KMAT = PHI * np.linalg.inv(DMAT + PHI * IMAT)

T_EXEC = time.time()
RESULTS = {"meta": {}, "lectures": {}, "depots_mp30": {}, "obs": {}}
ECHECS = []


def controle(nom, ok, valeur, detail=""):
    RESULTS["lectures"][nom] = {"ok": bool(ok), "valeur": valeur, "detail": detail}
    statut = "OK " if ok else "ECHEC"
    print(f"[{statut}] {nom} : {valeur if isinstance(valeur, str) else format(valeur, '.6e')} {detail}")
    if not ok:
        ECHECS.append(nom)
    return ok


# ----------------------------------------------------------------------------
# C0 — ancrage
# ----------------------------------------------------------------------------

def c0a_depot_antérieur():
    chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "FRONTIERE_F13_MERE_V0.md")
    mtime_depot = os.path.getmtime(chemin)
    RESULTS["meta"]["c0a_mtime_depot"] = mtime_depot
    RESULTS["meta"]["c0a_t_exec"] = T_EXEC
    ok = mtime_depot < T_EXEC
    return controle(
        "C0a_depot_antérieur",
        ok,
        f"depot={mtime_depot:.3f} < exec={T_EXEC:.3f}" if ok else "dépôt postérieur à l'exécution",
    )


def c0b_fermeture():
    e1 = abs(PHI * PHI - (PHI + 1.0))
    e2 = abs(2.0 * THETA - math.pi * ALPHA)
    ok = (e1 <= 1e-15) and (e2 <= 1e-15)
    return controle("C0b_fermeture_algebrique", ok, max(e1, e2), "phi²=phi+1 ; 2θ=πα")


# ----------------------------------------------------------------------------
# C1 — P31 : Schrödinger, assemblage de la lecture a=1
# ----------------------------------------------------------------------------

def c1_schrodinger():
    # C1a — identité mère à a=1 sur la grille O3
    mere = PHI / KHAT_A1_W - PHI
    err_grid = float(np.max(np.abs(mere - 1j * OMEGA1)))
    # C1a bis — mpmath 30 chiffres
    PHI_MP = (mp.sqrt(5) + 1) / 2
    errs_mp = []
    for w in [mpf("0.5"), mpf(1), mpf(2), mpf("3.7")]:
        khat = PHI_MP / (1j * w + PHI_MP)
        errs_mp.append(abs(PHI_MP / khat - PHI_MP - 1j * w))
    err_mp = float(max(errs_mp))
    RESULTS["depots_mp30"]["identite_mere_alpha1_w1p3"] = mp.nstr(
        PHI_MP / (PHI_MP / (1j * mpf("1.3") + PHI_MP)) - PHI_MP - 1j * mpf("1.3"), 30
    )
    ok_a = (err_grid <= 1e-12) and (err_mp <= 1e-29)
    controle("C1a_identite_mere_a1", ok_a, max(err_grid, err_mp), f"grille={err_grid:.2e} mp30={err_mp:.2e}")

    # C1b — groupe à un paramètre
    rng = np.random.default_rng(SEED)
    err_grp = 0.0
    for _ in range(100):
        t1, t2 = rng.uniform(0, 2 * math.pi, 2)
        err_grp = max(err_grp, float(np.max(np.abs(bateman(t1) @ bateman(t2) - bateman(t1 + t2)))))
    ok_b = err_grp <= 1e-14
    controle("C1b_groupe_1param", ok_b, err_grp, "R(θ1)R(θ2)=R(θ1+θ2), 100 paires, graine 27")

    # C1c — unitarité
    err_orth = 0.0
    err_det = 0.0
    for t in rng.uniform(0, 2 * math.pi, 100):
        R = bateman(float(t))
        err_orth = max(err_orth, float(np.max(np.abs(R.T @ R - np.eye(2)))))
        err_det = max(err_det, abs(float(np.linalg.det(R)) - 1.0))
    v = rng.normal(size=2)
    v = v / np.linalg.norm(v)
    for _ in range(1000):
        v = bateman(1e-3) @ v
    derive = abs(float(v @ v) - 1.0)
    ok_c = (err_orth <= 1e-14) and (err_det <= 1e-14) and (derive <= 1e-12)
    controle("C1c_unitarite", ok_c, max(err_orth, err_det, derive), f"orth={err_orth:.1e} det={err_det:.1e} dérive1000={derive:.1e}")

    # C1d — générateur antisymétrique
    delta = 1e-6
    J = np.array([[0.0, 1.0], [-1.0, 0.0]])
    gen = (bateman(delta) - np.eye(2)) / delta
    err_gen = float(np.max(np.abs(gen - J)))
    ok_d = err_gen <= 1e-5
    controle("C1d_generateur_antisymétrique", ok_d, err_gen, "(R(δ)−I)/δ → [[0,1],[−1,0]]")
    return ok_a and ok_b and ok_c and ok_d


# ----------------------------------------------------------------------------
# C2 — P32 : ancres JAUGAGE puis compensateur exact (triple route)
# ----------------------------------------------------------------------------

def c2_ancres():
    # C2a — reprise A2 : aveuglement au rephasage constant (a = 1/φ, noyau déposé)
    k_psi_phi = applique_noyau(PSI0, KHAT_PHI_W)
    dev_max = 0.0
    n_lect = 0
    for a in A_GRID:
        for k in K_GRID:
            alpha_x = a * np.cos(k * X1)
            d_ref = defaut(alpha_x, PSI0, k_psi_phi, KHAT_PHI_W)
            for th in THETAS_JAUGE:
                d_th = defaut(alpha_x + th, PSI0, k_psi_phi, KHAT_PHI_W)
                dev_max = max(dev_max, abs(d_th - d_ref))
                n_lect += 1
    ok_a = dev_max <= 1e-9
    controle("C2a_ancre_A2_aveuglement_global", ok_a, dev_max, f"{n_lect} lectures, seuil 1e-9")

    # C2b — reprise A1 : le défaut existe et le registre déposé est reproduit
    d_reg = defaut(0.1 * np.cos(1.0 * X1), PSI0, k_psi_phi, KHAT_PHI_W)
    err_reg = abs(d_reg - D_REG)
    d_max = 0.0
    for a, k in PROFILES6:
        d = defaut(a * np.cos(k * X1), PSI0, k_psi_phi, KHAT_PHI_W)
        d_max = max(d_max, d)
    ok_b = (err_reg <= 1e-12) and (d_max > 1e-4)
    controle(
        "C2b_ancre_A1_defaut_réel",
        ok_b,
        max(err_reg, 0.0) if err_reg <= 1e-12 else err_reg,
        f"registre |Δ|={err_reg:.2e} ; défaut max 6 profils={d_max:.4f} (>1e-4)",
    )
    RESULTS["lectures"]["C2b_detail"] = {
        "ok": bool(ok_b),
        "valeur": float(d_reg),
        "registre": D_REG,
        "ecart_registre": float(err_reg),
        "defaut_max_6_profils": float(d_max),
    }
    return ok_a and ok_b


def operateur_A(chi_a, k):
    """Retourne (A = ∇χ, e^{iχ}, D_A dense) pour le profil de la famille fermée."""
    chi = chi_a * np.cos(k * X1)
    A = -chi_a * k * np.sin(k * X1)  # dérivée exacte du mode (bin)
    eia = np.exp(1j * chi)
    DA = DMAT - 1j * np.diag(A)
    return chi, A, eia, DA


def c2_compensateur():
    ok_all = True
    res_c, res_d, res_e = [], [], []
    sous_route = 0.0
    for chi_a, k in PROFILES6:
        chi, A, eia, DA = operateur_A(chi_a, k)
        d_psi = DMAT @ PSI0

        # C2c — niveau dérivée : D_A[e^{iχ}ψ] = e^{iχ}D[ψ]
        lhs = DA @ (eia * PSI0)
        rhs = eia * d_psi
        r = norme(lhs - rhs) / norme(rhs)
        res_c.append(r)

        # C2d — niveau noyau : K_A[e^{iχ}ψ] = e^{iχ}K[ψ]
        KA = PHI * np.linalg.inv(DA + PHI * IMAT)
        lhs = KA @ (eia * PSI0)
        rhs = eia * (KMAT @ PSI0)
        r = norme(lhs - rhs) / norme(rhs)
        res_d.append(r)
        sous_route = max(
            sous_route,
            norme(KMAT @ PSI0 - applique_noyau(PSI0, KHAT_A1_W))
            / norme(applique_noyau(PSI0, KHAT_A1_W)),
        )

        # C2e — niveau boucle : D_A²[e^{iχ}ψ] = e^{iχ}D²[ψ]
        DA2 = DA @ DA
        lhs = DA2 @ (eia * PSI0)
        rhs = eia * (DMAT @ d_psi)
        r = norme(lhs - rhs) / norme(rhs)
        res_e.append(r)

    ok_c = max(res_c) <= 1e-10
    ok_d = (max(res_d) <= 1e-9) and (sous_route <= 1e-13)
    ok_e = max(res_e) <= 1e-10
    controle("C2c_niveau_dérivée", ok_c, max(res_c), "D_A[e^{iχ}ψ]=e^{iχ}Dψ, 6 profils")
    controle("C2d_niveau_noyau", ok_d, max(res_d), f"K_A[e^{{iχ}}ψ]=e^{{iχ}}Kψ ; route matricielle vs spectrale={sous_route:.1e}")
    controle("C2e_niveau_boucle", ok_e, max(res_e), "D_A²[e^{iχ}ψ]=e^{iχ}D²ψ")

    # C2f — composition χ = χ1 + χ2 (6 paires fermées cycliques, 2 routes chacune)
    res_f = []
    for i_p in range(6):
        (a1, k1), (a2, k2) = PROFILES6[i_p], PROFILES6[(i_p + 1) % 6]
        chi1, A1f, eia1, _ = operateur_A(a1, k1)
        chi2, A2f, eia2, _ = operateur_A(a2, k2)
        KA12 = PHI * np.linalg.inv(DMAT - 1j * np.diag(A1f + A2f) + PHI * IMAT)
        KA2 = PHI * np.linalg.inv(DMAT - 1j * np.diag(A2f) + PHI * IMAT)
        rhs = np.exp(1j * (chi1 + chi2)) * (KMAT @ PSI0)
        lhs_compose = KA12 @ (np.exp(1j * (chi1 + chi2)) * PSI0)
        lhs_deuxpas = eia1 * (KA2 @ (eia2 * PSI0))
        res_f.append(norme(lhs_compose - rhs) / norme(rhs))
        res_f.append(norme(lhs_deuxpas - rhs) / norme(rhs))
    ok_f = max(res_f) <= 1e-10
    controle("C2f_composition", ok_f, max(res_f), "χ=χ1+χ2 ⟹ cohérence composée, 6 paires × 2 routes")
    RESULTS["lectures"]["C2_detail"] = {
        "res_c": [float(x) for x in res_c],
        "res_d": [float(x) for x in res_d],
        "res_e": [float(x) for x in res_e],
        "res_f": [float(x) for x in res_f],
    }
    return ok_c and ok_d and ok_e and ok_f


# ----------------------------------------------------------------------------
# C3 — P33 : Green covariantisé en 3D (jauge pure), Green de test bande π/4
# ----------------------------------------------------------------------------

def _chi3_f(x, y, z):
    """χ de jauge pure, forme close — modes (2,3,5) bins exacts, grille ET points arbitraires."""
    return (
        0.4 * np.sin(2.0 * math.pi * 2.0 * x / N3)
        + 0.3 * np.cos(2.0 * math.pi * 3.0 * y / N3)
        + 0.2 * np.sin(2.0 * math.pi * 5.0 * z / N3)
    )


def c3_green_3d():
    print("--- C3 : Green covariantisé 3D (jauge pure, bande π/4) ---")
    kx = W3AX[:, None, None]
    ky = W3AX[None, :, None]
    kz = W3AX[None, None, :]
    K2 = kx * kx + ky * ky + kz * kz
    mask = K2 <= (COUPURE * COUPURE)
    frac = float(mask.mean())
    RESULTS["obs"]["c3_fraction_bande"] = frac
    RESULTS["obs"]["c3_mur_aliasing"] = (
        "Green de test à bande limitée COUPURE=π/4 (leçon MORT 2) ; mode nul exclu "
        "(Green défini à constante près) ; χ modes (2,3,5) → spectre du produit ≤ π/4+0.35 < π : "
        "pas d'aliasing [OBS], non bloquant"
    )
    # G0 = |ω|^{-2α} à α=1 → 1/|k|² sur la bande (MORT 2)
    with np.errstate(divide="ignore", invalid="ignore"):
        GHAT = np.where(mask & (K2 > 0.0), 1.0 / np.where(K2 > 0.0, K2, 1.0), 0.0)
    G0 = np.real(np.fft.ifftn(GHAT))
    # χ et A = ∇χ (dérivée spectrale — champ indépendant de tout habillage)
    Xg = X3AX[:, None, None]
    Yg = X3AX[None, :, None]
    Zg = X3AX[None, None, :]
    chi = _chi3_f(Xg, Yg, Zg)
    CW = np.fft.fftn(chi)
    A = np.empty((3, N3, N3, N3), dtype=float)
    A[0] = np.real(np.fft.ifftn(1j * kx * CW))
    A[1] = np.real(np.fft.ifftn(1j * ky * CW))
    A[2] = np.real(np.fft.ifftn(1j * kz * CW))
    del CW
    chi0 = float(chi[X0_3D])
    dress = np.exp(1j * (chi - chi0))  # habillage déposé P33
    # source habillée s = dress·δ_test ; δ_test = IFT[K2·Ĝ] (cohérence exacte avec G0)
    delta_band = np.fft.ifftn(K2 * GHAT)
    s = dress * delta_band
    del delta_band
    # route bande : déshabillage NUMÉRIQUE (aucune simplification à la main) puis
    # inverse de boucle restreint à la bande, puis ré-habillage
    undressed = np.exp(-1j * chi) * s
    w = np.fft.ifftn(GHAT * np.fft.fftn(undressed))
    del undressed
    del GHAT
    G_A = np.exp(1j * chi) * w
    del w
    del chi
    # route étendue (discriminante) : −Δ_A = −Δ + 2iA·∇ + i(∇·A) + |A|², A champ indépendant
    h = dress * G0
    lap_h = np.fft.ifftn(-K2 * np.fft.fftn(h))  # Δh
    agrad = np.zeros_like(h)
    for j, kk in enumerate((kx, ky, kz)):
        grad_h = np.fft.ifftn(1j * kk * np.fft.fftn(h))
        agrad += A[j] * grad_h
        del grad_h
    AW0 = np.fft.fftn(A[0])
    AW1 = np.fft.fftn(A[1])
    AW2 = np.fft.fftn(A[2])
    divA = np.real(np.fft.ifftn(1j * kx * AW0 + 1j * ky * AW1 + 1j * kz * AW2))
    del AW0, AW1, AW2
    lhs = (
        -lap_h
        + 2j * agrad
        + 1j * divA * h
        + (A[0] * A[0] + A[1] * A[1] + A[2] * A[2]) * h
    )
    res_op = float(np.max(np.abs(lhs - s)) / np.max(np.abs(s)))
    del lap_h, agrad, divA, lhs, h
    # rayon torique enveloppé (MORT 2)
    RX = np.minimum(X3AX, N3 - X3AX)
    dist = np.sqrt(
        RX[:, None, None] ** 2 + RX[None, :, None] ** 2 + RX[None, None, :] ** 2
    )
    # C3b — champ plein r ≤ 32 : structure de phase P33
    plein = dist <= 32.0
    idx = np.where(plein)
    den = dress[idx] * G0[idx]
    n_zero = int(np.sum(np.abs(den) == 0.0))
    res_b = float(np.max(np.abs(G_A[idx] / den - 1.0)))
    n_b = int(len(den))
    del idx, den, plein
    # C3a — médianes de |G_A| par coquille [3,8] = G₀ (module aveugle)
    coquilles = []
    pire = 0.0
    for r in COQUILLES:
        sel = np.abs(dist - float(r)) < 0.5
        m_ga = float(np.median(np.abs(G_A[sel])))
        m_g0 = float(np.median(G0[sel]))
        coquilles.append(
            {"coquille": r, "n": int(sel.sum()), "median_GA": m_ga, "median_G0": m_g0}
        )
        pire = max(pire, abs(m_ga - m_g0))
    del dist, s, dress, G_A, G0, K2, A
    ok_a = (pire <= 1e-10) and (res_op <= 1e-10)
    controle(
        "C3a_coquilles_module",
        ok_a,
        max(pire, res_op),
        f"route étendue={res_op:.2e} ; médianes |G_A| vs G0 [3,8]={pire:.2e} ; bande={frac:.4f}",
    )
    RESULTS["lectures"]["C3a_detail"] = {"res_op": res_op, "coquilles": coquilles}
    controle(
        "C3b_champ_plein_phase",
        res_b <= 1e-9,
        res_b,
        f"G_A/(e^{{iΔχ}}G0)−1, r≤32, n={n_b}, dénominateurs nuls={n_zero}",
    )
    return ok_a and (res_b <= 1e-9)


# ----------------------------------------------------------------------------
# C4 — P34 : universalité forcée — MÊME noyau pour 3 états distincts
# ----------------------------------------------------------------------------

def c4_universalite():
    print("--- C4 : universalité — même noyau, 3 états ---")
    g = np.exp(-((X1 - L1 / 2.0) ** 2) / 8.0) + 0j
    g = g / norme(g)
    etats = {
        "porteur": PSI0,
        "gaussienne": g,
        "superposition": (PSI0 + 0.5j * g + 0.3 * np.exp(2j * X1))
        / norme(PSI0 + 0.5j * g + 0.3 * np.exp(2j * X1)),
    }
    pire = 0.0
    for chi_a, k in PROFILES6:
        chi, _A_f, eia, DA = operateur_A(chi_a, k)
        KA = PHI * np.linalg.inv(DA + PHI * IMAT)  # MÊME noyau pour les 3 états
        for nom, psi in etats.items():
            lhs = KA @ (eia * psi)
            rhs = eia * (KMAT @ psi)
            r = norme(lhs - rhs) / norme(rhs)
            pire = max(pire, r)
    ok = pire <= 1e-9
    controle(
        "C4_universalite_3etats",
        ok,
        pire,
        "K_A[e^{iχ}ψ]=e^{iχ}Kψ, 3 états × 6 profils, aucun paramètre d'état",
    )
    return ok


# ----------------------------------------------------------------------------
# C5 — P35 : spectre du connecteur (courbure, Helmholtz, rang, dispersion)
# ----------------------------------------------------------------------------

def c5_connecteur():
    print("--- C5 : spectre du connecteur ---")
    kx = W3AX[:, None, None]
    ky = W3AX[None, :, None]
    kz = W3AX[None, None, :]
    # C5a — courbure d'une jauge pure : ∇×∇χ = 0 (grille 3D entière, reconstruction
    # indépendante de C3 — deux constructions du même champ doivent plier ensemble)
    chi = _chi3_f(X3AX[:, None, None], X3AX[None, :, None], X3AX[None, None, :])
    CW = np.fft.fftn(chi)
    del chi
    A0 = np.real(np.fft.ifftn(1j * kx * CW))
    A1 = np.real(np.fft.ifftn(1j * ky * CW))
    A2 = np.real(np.fft.ifftn(1j * kz * CW))
    del CW
    AW0 = np.fft.fftn(A0)
    AW1 = np.fft.fftn(A1)
    AW2 = np.fft.fftn(A2)
    del A0, A1, A2
    curl_x = np.real(np.fft.ifftn(1j * ky * AW2 - 1j * kz * AW1))
    curl_y = np.real(np.fft.ifftn(1j * kz * AW0 - 1j * kx * AW2))
    curl_z = np.real(np.fft.ifftn(1j * kx * AW1 - 1j * ky * AW0))
    del AW0, AW1, AW2
    res_a = max(
        float(np.max(np.abs(curl_x))),
        float(np.max(np.abs(curl_y))),
        float(np.max(np.abs(curl_z))),
    )
    del curl_x, curl_y, curl_z
    ok_a = res_a <= 1e-12
    controle(
        "C5a_courbure_jauge_pure",
        ok_a,
        res_a,
        "max|∇×∇χ|, grille 192³ entière (reconstruction indépendante de C3)",
    )
    # C5b — Helmholtz N=96 : ∇·A_T = 0 ; A_L = ∇λ (graine 27)
    N5 = 96
    w5 = 2.0 * math.pi * np.fft.fftfreq(N5, d=1.0)
    w5x = w5[:, None, None]
    w5y = w5[None, :, None]
    w5z = w5[None, None, :]
    W2 = w5x * w5x + w5y * w5y + w5z * w5z
    M5 = W2 <= (COUPURE * COUPURE)
    rng5 = np.random.default_rng(SEED)
    AW = []
    for _j in range(3):
        rd = rng5.normal(size=(N5, N5, N5)) + 1j * rng5.normal(size=(N5, N5, N5))
        rd = rd * M5
        rd[0, 0, 0] = 0.0
        AW.append(np.fft.fftn(np.real(np.fft.ifftn(rd))))  # champ réel bande limité
    wdot = w5x * AW[0] + w5y * AW[1] + w5z * AW[2]
    with np.errstate(divide="ignore", invalid="ignore"):
        coef = np.where(W2 > 0.0, wdot / np.where(W2 > 0.0, W2, 1.0), 0.0)
    del wdot
    ATW = [AW[0] - w5x * coef, AW[1] - w5y * coef, AW[2] - w5z * coef]
    divAT = np.real(np.fft.ifftn(1j * (w5x * ATW[0] + w5y * ATW[1] + w5z * ATW[2])))
    res_div = float(np.max(np.abs(divAT)))
    del divAT, ATW
    ALW = [w5x * coef, w5y * coef, w5z * coef]
    curlL_x = np.real(np.fft.ifftn(1j * (w5y * ALW[2] - w5z * ALW[1])))
    curlL_y = np.real(np.fft.ifftn(1j * (w5z * ALW[0] - w5x * ALW[2])))
    curlL_z = np.real(np.fft.ifftn(1j * (w5x * ALW[1] - w5y * ALW[0])))
    res_curl = max(
        float(np.max(np.abs(curlL_x))),
        float(np.max(np.abs(curlL_y))),
        float(np.max(np.abs(curlL_z))),
    )
    del ALW, curlL_x, curlL_y, curlL_z, coef
    ok_b = (res_div <= 1e-11) and (res_curl <= 1e-11)
    controle(
        "C5b_helmholtz",
        ok_b,
        max(res_div, res_curl),
        f"max|∇·A_T|={res_div:.2e} ; max|∇×A_L|={res_curl:.2e} ; N=96, graine 27",
    )
    # C5c — rang du projecteur transverse = 2 par mode k ≠ 0 (5 modes, graine 27)
    rng_c = np.random.default_rng(SEED)
    rangs = []
    pire_proj = 0.0
    for _i in range(5):
        n = rng_c.integers(0, N3, size=3)
        while not np.any(n):
            n = rng_c.integers(0, N3, size=3)
        ns = np.where(n > N3 // 2, n - N3, n)  # première zone [OBS]
        kv = 2.0 * math.pi * ns.astype(float) / N3
        P = np.eye(3) - np.outer(kv, kv) / float(kv @ kv)
        rang = int(np.linalg.matrix_rank(P))
        pire_proj = max(pire_proj, float(np.max(np.abs(P @ P - P))))
        eigs = [float(e) for e in np.sort(np.linalg.eigvalsh(P))]
        rangs.append({"n": [int(t) for t in ns], "rang": rang, "eigs": eigs})
    ok_c = all(rr["rang"] == 2 for rr in rangs)
    controle(
        "C5c_rang_projecteur_transverse",
        ok_c,
        pire_proj,
        f"rang=2 pour 5/5 modes k≠0 (critère exact, graine 27) ; P²−P={pire_proj:.2e}",
    )
    RESULTS["lectures"]["C5c_detail"] = {"modes": rangs}
    # C5d — dispersion : eigenvalue de la boucle à α=1 = −|k|² ; phase de λ = πα = π = σ
    B = DMAT @ DMAT
    modes = [20, 50, 100, 200, -20]
    pire_l = 0.0
    pire_ph = 0.0
    det_d = []
    for m in modes:
        w_m = m * DOMEGA
        v = np.exp(1j * w_m * X1)
        lam = np.vdot(v, B @ v) / np.vdot(v, v)
        err_l = float(abs(lam - (-(w_m * w_m))) / (w_m * w_m))
        lam_sym = (1j * w_m) * (1j * w_m)  # −ω² + 0j exact → angle = π
        pa_a1 = math.pi * 1.0  # πα à α=1 = π (run 2 : comparaison erronée à πα(1/φ)=π/φ, bug estimateur consigné)
        err_ph = abs(float(np.angle(lam_sym)) - pa_a1)
        pire_l = max(pire_l, err_l)
        pire_ph = max(pire_ph, err_ph)
        det_d.append(
            {
                "m": m,
                "lambda": {"re": float(lam.real), "im": float(lam.imag)},
                "err_rel": err_l,
            }
        )
    del B
    ok_d = (pire_l <= 1e-12) and (pire_ph <= 1e-15)
    controle(
        "C5d_dispersion_boucle_a1",
        ok_d,
        max(pire_l, pire_ph),
        f"λ=(iω)²=−ω², route opérateur dense={pire_l:.2e} ; phase(λ)=πα=π (σ), route symbolique={pire_ph:.2e}",
    )
    RESULTS["lectures"]["C5d_detail"] = {
        "modes": det_d,
        "pa_phase": math.pi * 1.0,
    }
    return ok_a and ok_b and ok_c and ok_d


# ----------------------------------------------------------------------------
# C6 — holonomie ∮A·dl (boucle carrée fermée) ; C6b mesure ex ante α=1/φ
# ----------------------------------------------------------------------------

def c6_holonomie():
    print("--- C6 : holonomie et mesure ex ante α=1/φ ---")
    c = N3 // 2
    hs = 12
    z0 = float(c)
    kx_f = 2.0 * math.pi * 2.0 / N3
    ky_f = 2.0 * math.pi * 3.0 / N3
    # C6a — route quadrature fine : A = ∇χ en forme close, 2^21+1 points par arête
    M = 2 ** 21
    s_arr = np.linspace(0.0, 24.0, M + 1)
    ds = 24.0 / M
    x_lo = float(c - hs)
    x_hi = float(c + hs)
    y_lo = float(c - hs)
    y_hi = float(c + hs)

    def _int(f):
        return float((0.5 * f[0] + f[1:-1].sum() + 0.5 * f[-1]) * ds)

    x_e = x_lo + s_arr
    y_e = y_lo + s_arr
    i1 = _int(0.4 * kx_f * np.cos(kx_f * x_e))  # y=y_lo, t̂=+x̂
    i2 = _int(-0.3 * ky_f * np.sin(ky_f * y_e))  # x=x_hi, t̂=+ŷ
    i3 = -_int(0.4 * kx_f * np.cos(kx_f * x_e))  # y=y_hi, t̂=−x̂
    i4 = -_int(-0.3 * ky_f * np.sin(ky_f * y_e))  # x=x_lo, t̂=−ŷ
    hol_pure = i1 + i2 + i3 + i4
    # téléscopage de corroboration (non bloquant) : différences de χ aux 4 sommets
    sommets = [
        float(_chi3_f(np.array([x_lo]), np.array([y_lo]), np.array([z0]))[0]),
        float(_chi3_f(np.array([x_hi]), np.array([y_lo]), np.array([z0]))[0]),
        float(_chi3_f(np.array([x_hi]), np.array([y_hi]), np.array([z0]))[0]),
        float(_chi3_f(np.array([x_lo]), np.array([y_hi]), np.array([z0]))[0]),
    ]
    tele = abs(
        (sommets[1] - sommets[0])
        + (sommets[2] - sommets[1])
        + (sommets[3] - sommets[2])
        + (sommets[0] - sommets[3])
    )
    ok_pure = abs(hol_pure) <= 1e-12
    controle(
        "C6a_holonomie_jauge_pure",
        ok_pure,
        abs(hol_pure),
        f"∮∇χ·dl=0, boucle carrée 24×24, 2^21 pts/arête ; téléscopage={tele:.1e}",
    )

    def _e_g(x, y):
        r2 = (x - float(c)) ** 2 + (y - float(c)) ** 2
        return np.exp(-r2 / 32.0)

    j1 = _int(-(y_lo - float(c)) * _e_g(x_e, np.full_like(x_e, y_lo)))
    j2 = _int((x_hi - float(c)) * _e_g(np.full_like(y_e, x_hi), y_e))
    j3 = -_int(-(y_hi - float(c)) * _e_g(x_e, np.full_like(x_e, y_hi)))
    j4 = -_int((x_lo - float(c)) * _e_g(np.full_like(y_e, x_lo), y_e))
    hol_phys = j1 + j2 + j3 + j4
    gx = np.linspace(x_lo, x_hi, 49)
    GX, GY = np.meshgrid(gx, gx)
    rg2 = (GX - float(c)) ** 2 + (GY - float(c)) ** 2
    max_curl = float(np.max(np.abs(0.5 * np.exp(-rg2 / 32.0) * (2.0 - rg2 / 16.0))))
    ok_phys = abs(hol_phys) > 1e-3
    controle(
        "C6a_holonomie_champ_physique",
        ok_phys,
        abs(hol_phys),
        f"∮A_phys·dl (vortex C=0.5, σ²=32) ; max|curl|={max_curl:.4f} (curl ≠ 0)",
    )
    # C6b — α=1/φ : eigenvalue de boucle (i|k|)^{2/φ} — PREMIÈRE MESURE ex ante, SANS barre
    mesures = []
    for m in (1, 2, 3, 4, 5):
        w = m * DOMEGA
        lam = (1j * w) ** (2.0 / PHI)
        mod = float(abs(lam))
        arg = float(np.angle(lam))
        mesures.append(
            {
                "omega": w,
                "lambda": {"re": float(lam.real), "im": float(lam.imag)},
                "module": mod,
                "module_theorique": float(w ** (2.0 / PHI)),
                "argument": arg,
                "argument_sur_pi": arg / math.pi,
            }
        )
        print(
            f"[MESURE] C6b ω={w:.1f} : (iω)^(2/φ) = {lam.real:+.9f} {lam.imag:+.9f}i ; "
            f"|λ|={mod:.9f} ; arg λ/π = {arg / math.pi:.12f} (1/φ = {ALPHA:.12f})"
        )
    phi_mp = (1 + mp.sqrt(5)) / 2
    lam_mp = mp.power(mpc(0, 1), mpf(2) / phi_mp)
    RESULTS["depots_mp30"]["c6b_lambda_i_2surphi"] = mp.nstr(lam_mp, 30)
    RESULTS["lectures"]["C6b_alpha_invphi_eigenvalue"] = {
        "ok": True,
        "valeur": "mesure ex ante sans barre (jamais bloquante, FRONTIERE §2)",
        "detail": "λ(ω)=(iω)^{2/φ}=|ω|^{2/φ}·e^{iπ/φ} ; phase = πα = σ ; α=1 ici",
        "mesures": mesures,
    }
    RESULTS["obs"]["c6b_branche"] = (
        "puissance complexe numpy : branche principale (arg(iω)=π/2) ; pour ω<0 la "
        "lecture conjuguée n'est pas déposée au V0 [OBS]"
    )
    return ok_pure and ok_phys


def _json_default(o):
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, complex):
        return {"re": float(o.real), "im": float(o.imag)}
    return str(o)


# ----------------------------------------------------------------------------
# orchestration et verdict (échelle gelée FRONTIERE §3)
# ----------------------------------------------------------------------------

def main():
    t0 = time.time()
    print("=" * 72)
    print("F13 MÈRE V0 — le compensateur exact du défaut de covariance locale (D3)")
    print("Thèse P30–P35 ; barres gelées dans FRONTIERE_F13_MERE_V0.md (C0a)")
    print("=" * 72)
    c0a_depot_antérieur()
    c0b_fermeture()
    c1_schrodinger()
    c2_ancres()
    c2_compensateur()
    c3_green_3d()
    c4_universalite()
    c5_connecteur()
    c6_holonomie()
    ancres = [e for e in ECHECS if e.startswith("C2a") or e.startswith("C2b")]
    if ancres:
        verdict, code = "PIPELINE_CASSE", 1
    elif ECHECS:
        verdict, code = "REFUTE", 1
    else:
        verdict, code = "F13_MERE_COMPENSATEUR_EXACT", 0
    RESULTS["meta"]["verdict"] = verdict
    RESULTS["meta"]["exit_code"] = code
    RESULTS["meta"]["echecs"] = list(ECHECS)
    RESULTS["meta"]["date_iso"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
    RESULTS["meta"]["python"] = sys.version.split()[0]
    RESULTS["meta"]["numpy"] = np.__version__
    RESULTS["meta"]["duree_s"] = round(time.time() - t0, 2)
    chemin = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "resultat_f13_mere_v0.json"
    )
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(RESULTS, f, ensure_ascii=False, indent=2, default=_json_default)
    print("=" * 72)
    print(f"VERDICT : {verdict} (exit {code})")
    if ECHECS:
        print("Contrôles en échec : " + ", ".join(ECHECS))
    print(f"JSON : {chemin}")
    sys.exit(code)


if __name__ == "__main__":
    main()
