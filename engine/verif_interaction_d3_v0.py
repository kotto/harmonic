#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INTERACTION D3 V0 — la loi d'interaction entre canaux de jauge :
résonance de Bessel sous jauge commune. I₁₂ = Re[i^{−j}·Z_j].

EXÉCUTION du DÉPÔT du 28/08/2026 17:20 (DEPOT_INTERACTION_D3_V0.md) — dépôt fermé
jamais exécuté jusqu'à ce jour (audit du 03/09 : aucun script, aucun JSON existaient).
C0a : mtime du dépôt (28/08 17:20) < mtime d'exécution — antériorité ~5,7 jours.

Échelle de verdicts GELÉE (dépôt §3, non modifiable — I5) :
  V+ INTERACTION_FORME_FERMEE        exit 0  (contrôles OK ET C1–C6 dans la barre)
  V2 INTERACTION_FORME_PARTIELLE     exit 0  (C4 parité seule hors barre)
  V3 REFUTE_INTERACTION_SANS_FORME   exit 1  (≥1 parmi C1,C2,C3,C5,C6 hors barre)
  V4 REFUTE                          exit 1  (tout contrôle bloquant en échec)

Un seul échec (contrôle OU conséquence) ⟹ REFUTE — aucun sauvetage.
Tout estimateur est bugable : un bug d'estimateur consigné n'est pas une physique
réfutée (barres gelées inchangées, physique inchangée — leçon FORCE V1.1/V1.2/V1.3).

Objets fermés : O1–O9 verbatim FORCE V1 (+ O11 déposé : couples, jauge commune,
forme close I₁₂ = Re[i^{−j}Z_j], §0-bis amendé : somme sur TOUTES les paires
résonnantes n,m ∈ [−11,11], Δ₀ automatiquement nul).
"""

import json
import math
import os
import sys
import time

import numpy as np

# ----------------------------------------------------------------------------
# O1 — φ, α = 1/φ
# ----------------------------------------------------------------------------
PHI = (1.0 + math.sqrt(5.0)) / 2.0
ALPHA = 1.0 / PHI
BRANCH = math.pi * ALPHA / 2.0        # πα/2 — structurel (branche principale O2)

# ----------------------------------------------------------------------------
# O3 — treillis (N=512, L=20π, Δω=0.1, Nyquist 25.6)
# ----------------------------------------------------------------------------
N = 512
L = 20.0 * math.pi
DOMEGA = 2.0 * math.pi / L            # 0.1
NYQUIST = (N / 2) * DOMEGA            # 25.6

# ----------------------------------------------------------------------------
# O4/O9 — registres fermés
# ----------------------------------------------------------------------------
GSTAR_REG = 0.3232880100102466        # 17ᵉ objet (JAUGAGE V0, forme testée FORCE V1.3)
D_REG = 0.032328801001024664          # D(0.1, k=1) — ancre A1 (reproduite F13 C2b)
J0_BRUT_REG = {0.1: 1.765841e+74, 0.2: 8.222839e+64}   # gel V1.3 §0 (machine 16:55:29)

# ----------------------------------------------------------------------------
# O7 — barres gelées (dépôt §1 contrôles, §0 conséquences)
# ----------------------------------------------------------------------------
TOL_C0B = 1e-15
TOL_C1 = 1e-12        # K̂ double route
TOL_C2A = 1e-12       # Bessel série × récurrence
TOL_C2B = 1e-9        # identité paire J₀+2ΣJ₂ₖ=1
TOL_C3 = 1e-12        # Jacobi–Anger ponctuel
TOL_C4 = 1e-12        # action propre
TOL_C5R = 1e-12       # continuité registre (relatif)
TOL_C6R = 1e-9        # aveuglement spot
# Conséquences (dépôt §0 table)
TOL_C1_RES = 1e-12    # C1 identité norme (relatif)
TOL_C2_RES = 1e-9     # C2 forme close (relatif à |I₁₂| ; absolu 1e-15 si nul)
TOL_C3_RES = 1e-15    # C3 résidu famille B (absolu)
TOL_C4_GOOD = 1e-12   # C4 bonne parité (absolu)
TOL_C4_WRONG = 1e-6   # C4 mauvaise parité (doit DÉPASSER)
TOL_C5_RES = 1e-9     # C5 aveuglement (absolu)
TOL_C6_RES = 1e-12    # C6 dégénérescence (relatif)

TRUNC = 11            # |n| ≤ 11 (J₁₂(0.1) ≈ 5e-25, invisible)

X = np.arange(N) * (L / N)
# Grille fréquentielle signée (O3) — contrôle C1
W_GRID = np.where(np.arange(N) <= N // 2, np.arange(N), np.arange(N) - N).astype(float) * DOMEGA


# ============================================================================
# Routes noyau (O2 — verbatim FORCE V1)
# ----------------------------------------------------------------------------
def lambda_weight(w):
    """(iω)^α, branche principale : ω^α·e^{+iπα/2} si ω>0, |ω|^α·e^{−iπα/2} si ω<0."""
    w = np.asarray(w, dtype=float)
    lam = np.zeros(w.shape, dtype=complex)
    pos = w > 0
    neg = w < 0
    lam[pos] = np.power(w[pos], ALPHA) * np.exp(1j * BRANCH)
    lam[neg] = np.power(-w[neg], ALPHA) * np.exp(-1j * BRANCH)
    return lam


def kernel(w):
    """K̂(ω) = φ/((iω)^α + φ), K̂(0)=1 — route complexe, forme close."""
    w = np.asarray(w, dtype=float)
    lam = lambda_weight(w)
    out = PHI / (lam + PHI)
    return np.where(w == 0.0, 1.0 + 0.0j, out)


def kernel_mod2(w):
    """|K̂(ω)|² forme réelle développée — route 2 du contrôle C1."""
    w = np.asarray(w, dtype=float)
    aw = np.abs(w)
    den = PHI * PHI + 2.0 * PHI * math.cos(BRANCH) * np.power(aw, ALPHA) \
        + np.power(aw, 2.0 * ALPHA)
    return (PHI * PHI) / den


K_GRID = kernel(np.where(np.arange(N) <= N // 2, np.arange(N), np.arange(N) - N) * DOMEGA)


def apply_kernel(psi):
    """Action propre diagonale du noyau sur la grille (route FFT, verbatim V1)."""
    return np.fft.ifft(K_GRID * np.fft.fft(psi))


# ----------------------------------------------------------------------------
# O7 Bessel — double route (série × récurrence corrigée, leçon V1.1 : parité)
# ----------------------------------------------------------------------------
def j_serie(n, x, terms=80):
    """Jₙ(x), n ≥ 0, par série Jₙ = Σ_m (−1)^m (x/2)^{2m+n}/(m!(m+n)!)."""
    total = 0.0
    for m in range(terms):
        num = (0.5 * x) ** (2 * m + n)
        den = math.factorial(m) * math.factorial(m + n)
        term = num / den
        total += term if m % 2 == 0 else -term
        if m >= n and term < 1e-300:
            break
    return total


def j_signed(n, x):
    """Jₙ pour n ∈ ℤ — parité corrigée J₋ₙ = (−1)ⁿ·Jₙ (FORCE V1.1)."""
    if n >= 0:
        return j_serie(n, x)
    return ((-1.0) ** n) * j_serie(-n, x)


def j_recurrence(x, n_max=40):
    """Route récurrence descendante (Miller), normalisée par J₀²+2ΣJₙ²=1."""
    jt = [0.0] * (n_max + 2)
    jt[n_max] = 1.0
    for n in range(n_max, 0, -1):
        jt[n - 1] = (2.0 * n / x) * jt[n] - jt[n + 1]
    s = jt[0] ** 2 + 2.0 * sum(jt[k] ** 2 for k in range(1, n_max + 1))
    c = 1.0 / math.sqrt(s)
    return {k: c * jt[k] for k in range(0, n_max + 1)}


def j0_brut(a, n_max=31):
    """J₀_brut = ∏_{n=1}^{31} (2n/a) — borne anti-débordement (V1.3 §0, machine 16:55:29)."""
    p = 1.0
    for n in range(1, n_max + 1):
        p *= (2.0 * n) / a
    return p


# ----------------------------------------------------------------------------
# Normes O5 (Parseval unitaire) et porteurs O6
# ----------------------------------------------------------------------------
def norm2(u):
    return float(np.real(np.vdot(u, u))) / N


def norm(u):
    return math.sqrt(norm2(u))


def inner(u, v):
    return complex(np.vdot(u, v)) / N


def carrier(w):
    return np.exp(1j * w * X) / math.sqrt(N)


# ----------------------------------------------------------------------------
# Défaut de rephasage modulé (voie machine « defaut » du V0, clonée à l'identique)
# ----------------------------------------------------------------------------
def canal(w, a, k, shift=0.0):
    """δ = K̂[e^{iθ}ψ] − e^{iθ}K̂[ψ] sur la grille (θ = a·cos(kx) + shift)."""
    psi = carrier(w)
    theta = a * np.cos(k * X) + shift
    kpsi = apply_kernel(psi)
    delta = apply_kernel(np.exp(1j * theta) * psi) - np.exp(1j * theta) * kpsi
    return delta, kpsi


def defaut_rel(w0, a, k, shift=0.0):
    """D_rel = ‖δ‖/‖K̂[ψ₀]‖ — la voie V0 clonée à l'identique."""
    delta, kpsi = canal(w0, a, k, shift)
    return norm(delta) / norm(kpsi)


def chi_forme_close(w0, a, k):
    """χ prédit (FORCE V1 §0, fréquences signées, troncature |n| ≤ 11)."""
    s = 0.0
    for n in range(1, TRUNC + 1):
        dp = complex(kernel(w0 + n * k) - kernel(w0))
        dm = complex(kernel(w0 - n * k) - kernel(w0))
        jn = j_serie(n, a)
        s += (jn ** 2) * (abs(dp) ** 2 + abs(dm) ** 2)
    return math.sqrt(s) / (a * abs(complex(kernel(w0))))


# ----------------------------------------------------------------------------
# Interaction : δ₁, δ₂, D_pair, I₁₂ (route machine FFT)
# ----------------------------------------------------------------------------
def couple(w1, k1, w2, k2, a, shift=0.0):
    """Défauts des deux canaux + défaut du couple sous (ses) jauges.

    Famille A : jauge commune (k₁ = k₂). Famille B : chaque canal sous sa propre
    jauge (k₁ ≠ k₂) — la linéarité donne R = (δ₁+δ₂)/√2 dans les deux cas.
    """
    psi1 = carrier(w1)
    psi2 = carrier(w2)
    th1 = a * np.cos(k1 * X) + shift
    th2 = a * np.cos(k2 * X) + shift
    kpsi1 = apply_kernel(psi1)
    kpsi2 = apply_kernel(psi2)
    d1_arr = apply_kernel(np.exp(1j * th1) * psi1) - np.exp(1j * th1) * kpsi1
    d2_arr = apply_kernel(np.exp(1j * th2) * psi2) - np.exp(1j * th2) * kpsi2
    psi_d = (np.exp(1j * th1) * psi1 + np.exp(1j * th2) * psi2) / math.sqrt(2.0)
    r = apply_kernel(psi_d) - (np.exp(1j * th1) * kpsi1 + np.exp(1j * th2) * kpsi2) \
        / math.sqrt(2.0)
    d1 = norm2(d1_arr)
    d2 = norm2(d2_arr)
    i12 = float(np.real(inner(d1_arr, d2_arr)))
    d_pair = norm2(r)
    return {"D1": d1, "D2": d2, "I12": i12, "D_pair": d_pair}


# ----------------------------------------------------------------------------
# Forme close — scan exact des collisions de bins (§0 et §0-bis)
# ----------------------------------------------------------------------------
def bin_of(w):
    b = w / DOMEGA
    rb = int(round(b))
    if abs(b - rb) > 1e-9:
        raise ValueError(f"mode hors grille : {w}")
    return rb


def delta_closed(w, n, k):
    """Δₙ(ω) = K̂(ω+nk) − K̂(ω) — fréquences signées, branche principale."""
    return complex(kernel(w + n * k) - kernel(w))


def scan_resonances(w1, k1, w2, k2, a):
    """⟨δ₁,δ₂⟩ forme close : Σ_{n,m} i^{m−n} JₙJₘ conj(Δₙ(ω₁))Δₘ(ω₂)·δ_grid,
    restreint aux collisions EXACTES de bins dans |n|,|m| ≤ 11 (Kronecker).
    Retourne (total, paires) — paires = [(n, m, facteur i^{m−n})]."""
    b1, kb1 = bin_of(w1), bin_of(k1)
    b2, kb2 = bin_of(w2), bin_of(k2)
    total = 0.0 + 0.0j
    pairs = []
    for n in range(-TRUNC, TRUNC + 1):
        for m in range(-TRUNC, TRUNC + 1):
            if b1 + n * kb1 != b2 + m * kb2:
                continue
            d1 = complex(kernel(w1 + n * k1) - kernel(w1))
            d2 = complex(kernel(w2 + m * k2) - kernel(w2))
            fac = (1j) ** (m - n)
            total += fac * j_signed(n, a) * j_signed(m, a) * np.conj(d1) * d2
            pairs.append({"n": n, "m": m, "facteur": str(fac)})
    return total, pairs


def z_j(j, w1, k1, w2, k2, a):
    """Z_j = Σ_m J_{m+j}J_m conj(Δ_{m+j}(ω₁))Δ_m(ω₂) sur TOUTES les paires
    résonnantes n=m+j ∈ [−11,11] (forme close complète, §0-bis)."""
    b1, kb1 = bin_of(w1), bin_of(k1)
    b2, kb2 = bin_of(w2), bin_of(k2)
    total = 0.0 + 0.0j
    pairs = []
    for m in range(-TRUNC, TRUNC + 1):
        n = m + j
        if abs(n) > TRUNC:
            continue
        if b1 + n * kb1 != b2 + m * kb2:
            continue
        d1 = complex(kernel(w1 + n * k1) - kernel(w1))
        d2 = complex(kernel(w2 + m * k2) - kernel(w2))
        total += j_signed(n, a) * j_signed(m, a) * np.conj(d1) * d2
        pairs.append((n, m))
    return total, pairs


# ----------------------------------------------------------------------------
# Appareil de verdict
# ----------------------------------------------------------------------------
RESULTATS = {"controles": {}, "consequences": {}, "depots": {}, "obs": {}}
ECHECS = []


def controle(nom, ok, valeur, barre="", detail=""):
    statut = "OK" if ok else "ECHEC"
    RESULTATS["controles"][nom] = {"statut": statut, "valeur": valeur,
                                   "barre": barre, "detail": detail}
    if not ok:
        ECHECS.append(f"controle {nom}")
    print(f"  [{statut}] {nom:12s} {valeur!r}  barre={barre} {detail}")
    return ok


def lecture(nom, ok, valeur, barre="", detail=""):
    statut = "OK" if ok else "ECHEC"
    RESULTATS["consequences"][nom] = {"statut": statut, "valeur": valeur,
                                      "barre": barre, "detail": detail}
    if not ok:
        ECHECS.append(f"consequence {nom}")
    print(f"  [{'OK' if ok else 'ECHEC'}] {nom:28s} {valeur!r}  barre={barre} {detail}")
    return ok


def rel(a, b):
    return abs(a / b - 1.0) if b != 0 else abs(a)


# ----------------------------------------------------------------------------
# CONTRÔLES BLOQUANTS (dépôt §1 — verbatim V1.3)
# ----------------------------------------------------------------------------
def c0a_depot():
    depot = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "DEPOT_INTERACTION_D3_V0.md")
    mt = os.path.getmtime(depot)
    t_exec = time.time()
    RESULTATS["depots"]["c0a"] = {
        "depot_mtime": mt, "exec_time": t_exec,
        "anteriorite_s": t_exec - mt,
        "depot_iso": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mt)),
        "exec_iso": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t_exec)),
    }
    print(f"  C0a : dépôt {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mt))} "
          f"< exécution (antériorité {t_exec - mt:.0f} s)")
    return mt < t_exec


def c0b_verification():
    """φ² = φ+1"""
    ecart = abs(PHI * PHI - (PHI + 1.0))
    return ecart <= TOL_C0B, ecart


def c1_noyau_double_route():
    """K̂ route complexe vs forme réelle développée — grille O3 + {½, 1/φ, 1, 2}."""
    pts = list(W_GRID) + [0.5, 1.0 / PHI, 1.0, 2.0]
    pire = 0.0
    for w in pts:
        kc = complex(kernel(w))
        ecart = abs(abs(kc) ** 2 - float(kernel_mod2(w)))
        pire = max(pire, ecart)
    # cohérence de branche : K̂(−ω) = conj(K̂(ω))
    pire_br = 0.0
    for w in [0.5, 1.0 / PHI, 1.0, 2.0, 3.0, 14.4]:
        pire_br = max(pire_br, abs(complex(kernel(-w)) - np.conj(complex(kernel(w)))))
    return (pire <= TOL_C1 and pire_br <= TOL_C1), pire, pire_br


def c2_bessel_double_route():
    """(a) série × récurrence corrigée ; (b) identité paire ; (c) J₀_brut ≤ 1e100."""
    pire_a = 0.0
    pire = 0.0
    for a in (0.1, 0.2):
        rec = j_recurrence(a)
        for n in range(0, TRUNC + 1):
            ecart = abs(j_serie(n, a) - rec[n])
            pire = max(pire, ecart)
            ecart_neg = abs(j_signed(-n, a) - ((-1.0) ** n) * rec[n])
            pire = max(pire, ecart_neg)
    ok_a = pire <= TOL_C2A
    # (b) identité paire J₀ + 2Σ_{k≥1} J₂ₖ = 1
    pire_b = 0.0
    for a in (0.1, 0.2):
        s = j_serie(0, a) + 2.0 * sum(j_serie(2 * k, a) for k in range(1, 16))
        pire_b = max(pire_b, abs(s - 1.0))
    ok_b = pire_b <= TOL_C2B
    # (c) J₀_brut calculé par machine (leçon V1.2) — valeurs déposées V1.3 §0
    brut = {a: j0_brut(a) for a in (0.1, 0.2)}
    ok_c = all(v <= 1e100 for v in brut.values())
    RESULTATS["depots"]["j0_brut"] = {str(a): v for a, v in brut.items()}
    RESULTATS["depots"]["j0_brut_registre_ecarts"] = {
        str(a): abs(brut[a] / J0_BRUT_REG[a] - 1.0) for a in (0.1, 0.2)}
    return (ok_a and ok_b and ok_c), pire, pire_b, brut, (ok_a, ok_b, ok_c)


def c3_jacobi_anger():
    """max |e^{ia·cos(kx_j)} − Σ_{|n|≤11} iⁿJₙ(a)e^{inkx_j}| — 4 couples V1."""
    couples = [(0.1, 1.0), (0.2, 1.0), (0.1, 0.5), (0.1, 2.0)]
    pire = 0.0
    ns = np.arange(-TRUNC, TRUNC + 1)
    for (a, k) in couples:
        jn = np.array([j_signed(int(n), a) for n in ns])
        modes = np.exp(1j * np.outer(ns, k * X))          # (23, N)
        rhs = ((1j) ** ns)[:, None] * jn[:, None] * modes
        lhs = np.exp(1j * a * np.cos(k * X))
        pire = max(pire, float(np.max(np.abs(lhs - rhs.sum(axis=0)))))
    return pire <= TOL_C3, pire


def c4_action_propre():
    """K̂[e^{iω₀x}] = K̂(ω₀)·e^{iω₀x} sur {0.1, 1.0, 14.4}."""
    pire = 0.0
    for w0 in (0.1, 1.0, 14.4):
        psi = carrier(w0)
        ecart = norm(apply_kernel(psi) - complex(kernel(w0)) * psi) / norm(psi)
        pire = max(pire, ecart)
    return pire <= TOL_C4, pire


def c5r_registre():
    """Continuité du registre : χ_machine(1,0.1,1) = G* = 0.3232880100102466,
    double route (opérateur FFT + forme close de Bessel). Barre 1e-12 relatif."""
    d_rel = defaut_rel(1.0, 0.1, 1.0)
    chi_op = d_rel / 0.1
    chi_fc = chi_forme_close(1.0, 0.1, 1.0)
    e_op = abs(chi_op / GSTAR_REG - 1.0)
    e_fc = abs(chi_fc / GSTAR_REG - 1.0)
    e_d = abs(d_rel / D_REG - 1.0)
    RESULTATS["depots"]["c5r"] = {
        "D_rel_route": d_rel, "D_REG": D_REG, "ecart_D": e_d,
        "chi_operateur": chi_op, "chi_forme_close": chi_fc,
        "GSTAR": GSTAR_REG, "ecart_op": e_op, "ecart_fc": e_fc,
    }
    return (e_op <= TOL_C5R and e_fc <= TOL_C5R and e_d <= TOL_C5R), \
        e_op, e_fc, e_d, d_rel, chi_fc


def c6r_u1_spot():
    """Aveuglement U(1) spot : D(θ+θ₀) = D(θ), θ₀ ∈ {π/3, π/2} (a=0.1, k=1, ω₀=1)."""
    d0 = defaut_rel(1.0, 0.1, 1.0)
    pire = 0.0
    for th0 in (math.pi / 3.0, math.pi / 2.0):
        pire = max(pire, abs(defaut_rel(1.0, 0.1, 1.0, shift=th0) - d0))
    return pire <= TOL_C6R, pire


def c7_no_wrap():
    """max |ω₀+nk| ≤ 25.6 pour toute lecture — consigné, sinon exclusion EX ANTE."""
    lects = {
        "famille_A_j1": max(abs(1.0 + n * 1.0) for n in range(-TRUNC, TRUNC + 1)),
        "famille_A_j2": max(abs(3.0 + n * 1.0) for n in range(-TRUNC, TRUNC + 1)),
        "famille_B_canal1": max(abs(1.0 + n * 1.0) for n in range(-TRUNC, TRUNC + 1)),
        "famille_B_canal2": max(abs(1.3 + m * 1.3) for m in range(-TRUNC, TRUNC + 1)),
    }
    pire = max(lects.values())
    RESULTATS["depots"]["c7_no_wrap"] = lects
    return pire <= NYQUIST, pire


# ----------------------------------------------------------------------------
# CONSÉQUENCES C1–C6 (dépôt §0, barres gelées)
# ----------------------------------------------------------------------------
COUPLES = {
    "A_j1": {"w1": 1.0, "k1": 1.0, "w2": 2.0, "k2": 1.0, "j": 1},
    "A_j2": {"w1": 1.0, "k1": 1.0, "w2": 3.0, "k2": 1.0, "j": 2},
    "B": {"w1": 1.0, "k1": 1.0, "w2": 1.3, "k2": 1.3, "j": None},
}


def consequence_c1_identite():
    """D_pair = ½(D₁+D₂) + Re⟨δ₁,δ₂⟩ sur les 3 couples (identité norme). 1e-12 rel."""
    pire = 0.0
    out = {}
    for nom, c in COUPLES.items():
        mes = couple(c["w1"], c["k1"], c["w2"], c["k2"], 0.1)
        residu = abs(mes["D_pair"] - (0.5 * (mes["D1"] + mes["D2"]) + mes["I12"]))
        rel_err = residu / mes["D_pair"]
        out[nom] = {"D1": mes["D1"], "D2": mes["D2"], "I12": mes["I12"],
                    "D_pair": mes["D_pair"], "residu": residu, "rel": rel_err}
        pire = max(pire, rel_err)
    return pire <= TOL_C1_RES, pire, out


def consequence_c2_forme_close():
    """I₁₂_machine = Re[i^{−j}Z_j]/N, familles j ∈ {1,2}. 1e-9 rel (1e-15 abs si nul)."""
    pire = 0.0
    out = {}
    for nom in ("A_j1", "A_j2"):
        c = COUPLES[nom]
        j = c["j"]
        mes = couple(c["w1"], c["k1"], c["w2"], c["k2"], 0.1)
        zj, paires = z_j(j, c["w1"], c["k1"], c["w2"], c["k2"], 0.1)
        # forme close = Re[i^{-j}·Z_j] / N  (le /N vient de l'inner product : ⟨,⟩ = vdot/N)
        pred = float(np.real((1j) ** (-j) * zj)) / N
        delta = abs(mes["I12"] - pred)
        barre_eff = TOL_C2_RES * abs(mes["I12"]) if mes["I12"] != 0.0 else 1e-15
        out[nom] = {"I12_machine": mes["I12"], "I12_pred": pred, "delta": delta,
                    "Z_j": {"re": float(np.real(zj)), "im": float(np.imag(zj))},
                    "n_paires_resonantes": len(paires), "paires": paires[:6],
                    "barre_eff": barre_eff}
        pire = max(pire, delta / barre_eff if barre_eff > 0 else 0.0)
    return pire <= 1.0, pire, out


def consequence_c3_famille_b():
    """Résidu hors forme close (famille B, incluant la résonance latérale (−1,−1),
    facteur i⁰ = 1 — §0-bis) : |I₁₂ − Re[J₋₁² conj(Δ₋₁(ω₁))Δ₋₁(ω₂)]/N| < 1e-15.
    Fuite bande principale prédite : (n,m) = (12,9), poids J₁₂·J₉ < 1e-24."""
    c = COUPLES["B"]
    mes = couple(c["w1"], c["k1"], c["w2"], c["k2"], 0.1)
    total, paires = scan_resonances(c["w1"], c["k1"], c["w2"], c["k2"], 0.1)
    # la prédiction déposée : la paire latérale unique (−1,−1), facteur i⁰ = 1, /N
    d1 = complex(kernel(c["w1"] - c["k1"]) - kernel(c["w1"]))
    d2 = complex(kernel(c["w2"] - c["k2"]) - kernel(c["w2"]))
    pred = float(np.real(j_signed(-1, 0.1) * j_signed(-1, 0.1) * np.conj(d1) * d2)) / N
    residu = abs(mes["I12"] - pred)
    # fuite hors troncature : paire (n,m) = (12,9) exactement résonnante
    bins_ok = (bin_of(c["w1"]) + 12 * bin_of(c["k1"])) == (bin_of(c["w2"]) + 9 * bin_of(c["k2"]))
    poids_fuite = abs(j_serie(12, 0.1) * j_serie(9, 0.1))
    RESULTATS["depots"]["c3"] = {
        "I12_machine": mes["I12"], "pred_paire_laterale": pred, "residu": residu,
        "paires_resonantes_troncature": paires, "fuite_12_9_resonante": bins_ok,
        "poids_fuite_J12J9": poids_fuite,
    }
    ok_residu = residu < TOL_C3_RES
    ok_fuite = poids_fuite < 1e-24
    return (ok_residu and poids_fuite < 1e-24), residu, pred, poids_fuite, bins_ok


def consequence_c4_parite():
    """j=1 : |I₁₂−Im Z₁/N| ≤ 1e-12 ET |I₁₂−Re Z₁/N| > 1e-6 ;
    j=2 : |I₁₂+Re Z₂/N| ≤ 1e-12 ET |I₁₂−Re Z₂/N| > 1e-6."""
    out = {}
    ok_all = True
    for nom, j in (("A_j1", 1), ("A_j2", 2)):
        c = COUPLES[nom]
        mes = couple(c["w1"], c["k1"], c["w2"], c["k2"], 0.1)
        zj, _paires = z_j(j, c["w1"], c["k1"], c["w2"], c["k2"], 0.1)
        im_z = float(np.imag(zj)) / N
        re_z = float(np.real(zj)) / N
        if j == 1:
            bon, mauvais = im_z, re_z
        else:
            bon, mauvais = -re_z, re_z
        e_bon = abs(mes["I12"] - bon)
        e_mauvais = abs(mes["I12"] - mauvais)
        ok = (e_bon <= TOL_C4_GOOD) and (e_mauvais > TOL_C4_WRONG)
        out[nom] = {"I12": mes["I12"], "bonne_parite": bon, "mauvaise_parite": mauvais,
                    "ecart_bon": e_bon, "ecart_mauvais": e_mauvais, "ok": ok}
        if not ok:
            ECHECS.append(f"consequence C4 {nom}")
        RESULTATS["consequences"][f"C4_{nom}"] = out[nom]
        print(f"  [{'OK' if ok else 'ECHEC'}] C4 parité {nom:8s} écart_bon={e_bon:.3e} "
              f"(≤{TOL_C4_GOOD:.0e}) écart_mauvais={e_mauvais:.3e} (>{TOL_C4_WRONG:.0e})")
    ok_all = all(v["ok"] for v in out.values())
    return ok_all, out


def consequence_c5_aveuglement():
    """D_pair(θ+c) = D_pair(θ), c ∈ {π/3, π/2}, les 3 couples + dégénéré. 1e-9."""
    pire = 0.0
    out = {}
    for nom, c in list(COUPLES.items()) + [("C6_degene", {"w1": 1.0, "k1": 1.0, "w2": 1.0, "k2": 1.0})]:
        d0 = couple(c["w1"], c["k1"], c["w2"], c["k2"], 0.1)["D_pair"]
        for th0 in (math.pi / 3.0, math.pi / 2.0):
            ds = couple(c["w1"], c["k1"], c["w2"], c["k2"], 0.1, shift=th0)["D_pair"]
            e = abs(ds - d0)
            out[f"{nom}_theta{round(th0, 4)}"] = e
            pire = max(pire, e)
    return pire <= TOL_C5_RES, pire, out


def consequence_c6_degenerescence():
    """Canaux identiques (ω₁=ω₂=1) : I₁₂ = D₁ et D_pair = 2D₁. 1e-12 rel."""
    mes = couple(1.0, 1.0, 1.0, 1.0, 0.1)
    e_i = abs(mes["I12"] / mes["D1"] - 1.0)
    e_p = abs(mes["D_pair"] / (2.0 * mes["D1"]) - 1.0)
    return (e_i <= TOL_C6_RES and e_p <= TOL_C6_RES), e_i, e_p, mes


# ----------------------------------------------------------------------------
def main():
    t0 = time.time()
    print("=" * 78)
    print("INTERACTION D3 V0 — résonance de Bessel sous jauge commune (dépôt 28/08 17:20)")
    print("=" * 78)

    # ---- contrôles bloquants -------------------------------------------------
    print("\n[CONTRÔLES BLOQUANTS — un seul échec ⟹ V4 REFUTE exit 1]")
    ok_c0a = controle("C0a", c0a_depot(), "mtime < exec", "—")
    ok_c0b = controle("C0b", abs(PHI * PHI - (PHI + 1.0)) <= TOL_C0B,
                      abs(PHI * PHI - (PHI + 1.0)), "1e-15", "φ²=φ+1")
    ok_c1 = True
    ok1, pire1, pire_br = c1_noyau_double_route()
    controle("C1", ok1, pire1, "1e-12", f"K̂ double route ; branche {pire_br:.2e}")
    ok_c1 = ok1
    ok2, pire2a, pire2b, brut, sub = c2_bessel_double_route()
    controle("C2'(a) Bessel série×récurrence", sub[0], pire2a, "1e-12")
    controle("C2'(b) identité paire J₀+2ΣJ₂ₖ=1", sub[1], pire2b, "1e-9")
    controle("C2'(c) J₀_brut ≤ 1e100", sub[2], max(brut.values()), "1e100",
             f"0.1→{brut[0.1]:.6e} ; 0.2→{brut[0.2]:.6e}")
    ok_c2 = all(sub)
    ok3, pire3 = c3_jacobi_anger()
    controle("C3 Jacobi–Anger ponctuel", ok3, pire3, "1e-12", "4 couples V1")
    ok_c3c = ok3
    ok4, pire4 = c4_action_propre()
    controle("C4 action propre", ok4, pire4, "1e-12", "{0.1, 1.0, 14.4}")
    ok_c4c = ok4
    e_op, e_fc, e_d, d_rel, chi_fc = None, None, None, None, None
    ok5, e_op, e_fc, e_d, d_rel, chi_fc = c5r_registre()
    chi_op = d_rel / 0.1   # chi = D_rel / a (a=0.1 dans l'ancre)
    controle("C5r χ_machine=G* (route op)", ok5 and e_op <= TOL_C5R, e_op, "1e-12 rel",
             f"χ_op={chi_op:.16f}")
    controle("C5r χ forme close = G*", e_fc <= TOL_C5R, e_fc, "1e-12 rel",
             f"χ_fc={chi_fc:.16f}")
    controle("C5r D_rel = D_REG", e_d <= TOL_C5R, e_d, "1e-12 rel", f"D={d_rel:.16f}")
    ok_c5r = ok5 and e_fc <= TOL_C5R and e_d <= TOL_C5R
    ok6, pire6 = c6r_u1_spot()
    controle("C6r U(1) aveuglement spot", ok6, pire6, "1e-9", "θ₀∈{π/3, π/2}")
    ok_c6r = ok6
    ok7, pire7 = c7_no_wrap()
    controle("C7 no-wrap", ok7, pire7, "≤25.6")
    ok_c7 = ok7

    controles_ok = all([ok_c0a, ok_c0b, ok_c1, ok_c2, ok_c3c, ok_c4c, ok_c5r, ok_c6r,
                        ok_c7])

    # ---- conséquences --------------------------------------------------------
    print("\n[CONSÉQUENCES — dépôt §0, barres gelées]")
    ok_C1, pire_C1, out_C1 = consequence_c1_identite()
    lecture("C1 identité norme (3 couples)", ok_C1, pire_C1, "1e-12 rel",
            json.dumps({k: round(v["rel"], 15) for k, v in out_C1.items()}))
    RESULTATS["consequences"]["C1"] = out_C1

    ok_C2, ratio_C2, out_C2 = consequence_c2_forme_close()
    lecture("C2 forme close Re[i^{−j}Z_j] j=1,2", ok_C2, ratio_C2, "ratio δ/barre ≤ 1",
            f"paires résonnantes : " + ", ".join(
                f"{k}:{v['n_paires_resonantes']}" for k, v in out_C2.items()))
    RESULTATS["consequences"]["C2"] = out_C2

    ok_C3, residu_B, pred_B, poids_fuite, bins_ok = consequence_c3_famille_b()
    lecture("C3 résidu famille B < 1e-15", ok_C3, residu_B, "1e-15 abs",
            f"prédit latérale (−1,−1) = {pred_B:.6e} ; fuite (12,9) poids {poids_fuite:.2e} ; résonnante={bins_ok}")
    RESULTATS["consequences"]["C3"] = RESULTATS["depots"]["c3"]

    ok_C4, out_C4 = consequence_c4_parite()

    ok_C5, pire_C5, out_C5 = consequence_c5_aveuglement()
    lecture("C5 aveuglement D_pair(θ+c)=D_pair(θ)", ok_C5, pire_C5, "1e-9",
            "3 couples + dégénéré × {π/3, π/2}")
    RESULTATS["consequences"]["C5"] = out_C5

    ok_C6, e_i6, e_p6, mes6 = consequence_c6_degenerescence()
    lecture("C6 dégénérescence I₁₂=D₁, D_pair=2D₁", ok_C6, max(e_i6, e_p6), "1e-12 rel",
            f"I₁₂/D₁−1={e_i6:.2e} ; D_pair/2D₁−1={e_p6:.2e}")
    RESULTATS["consequences"]["C6"] = {"ecart_I12_D1": e_i6, "ecart_Dpair_2D1": e_p6,
                                       "mesures": mes6}

    cons_forme = [ok_C1, ok_C2, ok_C3, ok_C5, ok_C6]     # C1–C3, C5, C6
    cons_ok = ok_C1 and ok_C2 and ok_C3 and ok_C4 and ok_C5 and ok_C6

    # ---- verdict (échelle §3 gelée) -----------------------------------------
    duree = time.time() - t0
    if not controles_ok:
        verdict, code = "V4_REFUTE", 1
    elif cons_ok:
        verdict, code = "V+_INTERACTION_FORME_FERMEE", 0
    elif ok_C1 and ok_C2 and ok_C3 and ok_C5 and ok_C6 and not ok_C4:
        verdict, code = "V2_INTERACTION_FORME_PARTIELLE", 0
    else:
        verdict, code = "V3_REFUTE_INTERACTION_SANS_FORME", 1

    RESULTATS["meta"] = {
        "verdict": verdict, "exit_code": code, "echecs": ECHECS,
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "python": sys.version.split()[0], "numpy": np.__version__,
        "duree_s": round(duree, 2),
        "c0a": RESULTATS["depots"].get("c0a", {}),
        "deposit": "DEPOT_INTERACTION_D3_V0.md (28/08/2026 17:20, jamais exécuté avant ce jour)",
    }
    print("\n" + "=" * 78)
    print(f"VERDICT : {verdict}   exit {code}")
    if ECHECS:
        print("Échecs consignés : " + "; ".join(ECHECS))
    print("=" * 78)

    out_json = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "resultat_interaction_d3_v0.json")

    def _default(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.bool_,)):
            return bool(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, complex):
            return [o.real, o.imag]
        return str(o)

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(RESULTATS, f, ensure_ascii=False, indent=2, default=_default)
    sys.exit(code)


# --- corrections de lisibilité du main (facteur i^{−j}, dépôt §0) -------------
if __name__ == "__main__":
    main()
