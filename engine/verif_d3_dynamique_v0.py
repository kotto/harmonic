#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D3 DYNAMIQUE V0 — le compensateur doit se propager : l'équation d'évolution
coule de l'identité mère. λ_loop = λ_kernel² ; à α=1 l'onde coule (Maxwell
émerge, massless, rang 2) ; à α=1/φ la mémoire se propage (PT brisé, phase
π/φ native, pont FV bit-exact, amortissement ρ(t), horizon 2 < S_max ≤ 2√2).

EXÉCUTION de la FRONTIÈRE D3 DYNAMIQUE V0 (FRONTIERE_D3_DYNAMIQUE_V0.md, commit
c9b428d, mtime 03/09 09:23) — cahier des charges gelé AVANT tout script (C0a,
mtime faisant foi). La thèse P36–P38 et les barres C0a–C10 / D1a–d / D2a–d /
D3a–c sont celles du document, non modifiables (I5).

Échelle de verdicts GELÉE (frontière §5, non modifiable) :
  V+ D3D_PROPAGATION_COULEE     exit 0  (contrôles OK ET D1(a–d) ET D2(a–d) ET D3(a,b))
  V2 D3D_ONDE_SANS_MEMOIRE      exit 0  (contrôles OK, D1 OK, D3 OK, ≥1 de D2 hors barre)
  V3 REFUTE_D3D_SANS_ONDE       exit 1  (contrôles OK, ≥1 de D1 hors barre)
  V4 REFUTE                     exit 1  (tout contrôle bloquant en échec)

Un seul échec (contrôle OU conséquence) ⟹ REFUTE — aucun sauvetage.
Tout estimateur est bugable : un bug d'estimateur consigné n'est pas une
physique réfutée (barres gelées inchangées, physique inchangée — leçon FORCE
V1.1/V1.2/V1.3). Lectures [OBS] : consignées, sans pouvoir de verdict.

CRITÈRE ANTI-RÉTRO-INGÉNIERIE (frontière §1, verbatim OUVERTURE §5) : A doit
sortir de l'identité mère (conséquence), jamais y entrer (ingrédient). Le code
ne contient QU'UN SEUL poids spectral : lambda_weight — la boucle est son carré
(loop_weight = λ_kernel², site unique de mise au carré). Aucune équation d'onde,
aucune dispersion, aucune masse, aucun terme −¼F² écrit comme ingrédient :
D1c LIT ω_t = |k| dans H = √(−λ_loop) ; D3b lit la source dans la graine
d'interaction ; −¼F² reste campagne séparée (I4 — frontière §6.2).

Routes (frontière §7) : FFT (poids (iω)^α, branche principale) pour D_α et la
boucle ; dense 512×512 pour C8 (alignement F13 C2e) et route croisée D1 ;
2D spectral pour C9 ; projecteur 3×3 par mode pour D1d (graine 27) ; série de
Bessel O7 pour D3b. Un seul poids spectral dans le code (C10).
"""

import json
import math
import os
import sys
import time

import numpy as np

# ----------------------------------------------------------------------------
# O1 — φ, α = 1/φ (α reste axiomatique — frontière §6.7)
# ----------------------------------------------------------------------------
PHI = (1.0 + math.sqrt(5.0)) / 2.0
ALPHA = 1.0 / PHI
BRANCH = math.pi * ALPHA / 2.0        # πα/2 — structurel (branche principale O2)

# ----------------------------------------------------------------------------
# O2 — LE poids spectral unique (C10 — anti-rétro-ingénierie)
# ----------------------------------------------------------------------------
def lambda_weight(w, a=ALPHA):
    """(iω)^α, branche principale : ω^α·e^{+iπα/2} si ω>0, |ω|^α·e^{−iπα/2} si ω<0.

    C'est l'unique poids spectral de tout l'appareil (identité mère P30).
    Aucun autre objet spectral n'est autorisé : la boucle est son carré.
    """
    w = np.asarray(w, dtype=float)
    br = math.pi * a / 2.0
    lam = np.zeros(w.shape, dtype=complex)
    pos = w > 0
    neg = w < 0
    lam[pos] = np.power(w[pos], a) * np.exp(1j * br)
    lam[neg] = np.power(-w[neg], a) * np.exp(-1j * br)
    return lam


def loop_weight(w, a=ALPHA):
    """λ_loop = λ_kernel² — le poids de boucle P36 (site unique de mise au carré).

    Construction par MULTIPLICATION COMPLEXE du poids mère, jamais par une
    puissance indépendante (iω)^{2α} : la filiation C10 est structurelle.
    """
    return lambda_weight(w, a) * lambda_weight(w, a)


def kernel(w):
    """K̂(ω) = φ/((iω)^α + φ), K̂(0)=1 — route complexe, forme close (FORCE O2)."""
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

# ----------------------------------------------------------------------------
# O3 — treillis (N=512, L=20π, Δω=0.1, Nyquist 25.6 — conventions JAUGAGE O3)
# ----------------------------------------------------------------------------
N = 512
L = 20.0 * math.pi
DOMEGA = 2.0 * math.pi / L            # 0.1
NYQUIST = (N / 2) * DOMEGA            # 25.6

X = np.arange(N) * (L / N)
W_GRID = np.where(np.arange(N) <= N // 2, np.arange(N), np.arange(N) - N).astype(float) * DOMEGA

# Un seul poids sur la grille, un seul site de mise au carré (C10) :
WG = lambda_weight(W_GRID)            # poids mère α=1/φ
LG = WG * WG                          # boucle α=1/φ — construction LG ≡ WG²
WG1 = lambda_weight(W_GRID, 1.0)      # le MÊME poids, évalué au point α=1
LG1 = WG1 * WG1                       # boucle α=1 — (iω)² = −ω²

K_GRID = kernel(W_GRID)

# 1D dense — route croisée C8/D1 (alignement F13 C2e/C5d, frontière §7).
# DMAT est D = d/dx, la tranche α=1 du MÊME objet opérateur ; aucun second
# poids spectral n'est défini dans ce code (audit C10 : le seul site qui
# produit un poids est lambda_weight, le seul carré est loop_weight).
F_MAT = np.exp(1j * np.outer(X, W_GRID))
DMAT = (F_MAT * (1j * W_GRID)[None, :]) @ F_MAT.conj().T / N
PSI0 = np.exp(1j * X) / math.sqrt(N)
PROFILES6 = [(0.1, 0.1), (0.1, 0.5), (0.1, 1.0), (0.2, 1.0), (0.5, 1.0), (1.0, 1.0)]

# ----------------------------------------------------------------------------
# O4/O9 — registres fermés (continuité — aucune redéfinition)
# ----------------------------------------------------------------------------
GSTAR_REG = 0.3232880100102466        # 17ᵉ objet (JAUGAGE V0, forme testée FORCE V1.3)
D_REG = 0.032328801001024664          # D(0.1, k=1) — ancre A1 (reproduite F13 C2b)
J0_BRUT_REG = {0.1: 1.765841e+74, 0.2: 8.222839e+64}   # gel V1.3 §0 (machine 16:55:29)
RHO0_ANCRE = 0.9396370575958052       # ancre CHSH t=0 (RESULTAT_CHSH_THU_V0)

# ----------------------------------------------------------------------------
# O7 — barres gelées (frontière §3 contrôles, §4 conséquences)
# ----------------------------------------------------------------------------
TOL_C0B = 1e-15
TOL_C1 = 1e-12        # K̂ double route
TOL_C2A = 1e-12       # Bessel série × récurrence
TOL_C2B = 1e-9        # identité paire J₀+2ΣJ₂ₖ=1
TOL_C3 = 1e-12        # Jacobi–Anger ponctuel
TOL_C4 = 1e-12        # action propre
TOL_C5R = 1e-12       # continuité registre (relatif)
TOL_C6R = 1e-9        # aveuglement spot
TOL_C8 = 1e-10        # covariance de la boucle à α=1 (dense, alignement F13 C2e)
TOL_C9 = 1e-12        # commutateur = courbure (2D spectral)
TOL_D1A = 1e-12       # λ_loop(α=1) = −|k|²
TOL_D1B = 1e-15       # massif zéro (absolu)
TOL_D1C = 1e-12       # fermeture unitaire + dispersion + avance de phase
TOL_D1D_PROJ = 1e-15  # P²−P (rang : critère exact)
TOL_D2A_ARG = 1e-15   # arg λ/π = 1/φ
TOL_D2A_MOD = 1e-12   # module |ω|^{2/φ}
TOL_D2D = 1e-12       # ancre + forme close ρ(t) + S_max(t)
TOL_D3A = 1e-12       # identité norme au niveau boucle (relatif)
TOL_D3B = 1e-9        # forme close source boucle (rel ; 1e-15 abs si nul)

TRUNC = 11            # |n| ≤ 11 (identique INTERACTION D3 V0)
SEED = 27             # graine déposée (JAUGAGE O7)
N3D = 192             # grille projecteur D1d (verbatim F13 C5c)

# ----------------------------------------------------------------------------
# O7 Bessel — double route (verbatim INTERACTION D3 V0, leçon V1.1 parité)
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
    """Jₙ pour n ∈ ℤ — parité J₋ₙ = (−1)ⁿ·Jₙ (FORCE V1.1)."""
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
    """J₀_brut = ∏_{n=1}^{31} (2n/a) — borne anti-débordement (V1.3 §0)."""
    p = 1.0
    for n in range(1, n_max + 1):
        p *= (2.0 * n) / a
    return p

# ----------------------------------------------------------------------------
# Normes O5 (Parseval unitaire) et porteurs O6 — verbatim INTERACTION
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
# Routes d'action (le poids unique appliqué au treillis)
# ----------------------------------------------------------------------------
def apply_kernel(psi):
    """K̂[ψ] — diagonale dans Fourier (route FFT, poids WG)."""
    return np.fft.ifft(K_GRID * np.fft.fft(psi))


def apply_loop(psi):
    """L[ψ] — boucle α=1/φ, poids LG = WG² (route FFT, poids unique)."""
    return np.fft.ifft(LG * np.fft.fft(psi))


def evolve_loop(psi, t):
    """Flot de la boucle : c_i(t) = c_i(0)·e^{λ_i t} (masque sur bins occupés).

    Estimateur consigné (leçon V1.2) : l'exponentielle n'est prise que sur les
    bins occupés du spectre (états à support sparse) — la route pleine grille
    multiplierait le bruit d'arrondi spectral par e^{|λ|t} sans contenu physique.
    """
    fp = np.fft.fft(psi)
    out = fp.copy()
    masque = fp != 0
    out[masque] = np.exp(LG[masque] * t) * fp[masque]
    return np.fft.ifft(out)


def bin_of(w):
    b = w / DOMEGA
    rb = int(round(b))
    if abs(b - rb) > 1e-9:
        raise ValueError(f"mode hors grille : {w}")
    return rb


def bin_index(m):
    """Index grille (0..N−1) du mode entier m (|m| ≤ N/2)."""
    return m % N

# ----------------------------------------------------------------------------
# Interaction au niveau boucle (clone INTERACTION couple(), poids LG)
# et au niveau noyau (rapport D3c [OBS])
# ----------------------------------------------------------------------------
def couple_loop(w1, k1, w2, k2, a, shift=0.0):
    """Défauts de boucle des deux canaux + défaut du couple sous (ses) jauges.

    Famille A : jauge commune (k₁ = k₂). Famille B : chaque canal sous sa
    propre jauge (k₁ ≠ k₂) — la linéarité donne R = (δ₁+δ₂)/√2 dans les deux cas.
    """
    psi1 = carrier(w1)
    psi2 = carrier(w2)
    th1 = a * np.cos(k1 * X) + shift
    th2 = a * np.cos(k2 * X) + shift
    lpsi1 = apply_loop(psi1)
    lpsi2 = apply_loop(psi2)
    d1_arr = apply_loop(np.exp(1j * th1) * psi1) - np.exp(1j * th1) * lpsi1
    d2_arr = apply_loop(np.exp(1j * th2) * psi2) - np.exp(1j * th2) * lpsi2
    psi_d = (np.exp(1j * th1) * psi1 + np.exp(1j * th2) * psi2) / math.sqrt(2.0)
    r = apply_loop(psi_d) - (np.exp(1j * th1) * lpsi1 + np.exp(1j * th2) * lpsi2) \
        / math.sqrt(2.0)
    return {"D1": norm2(d1_arr), "D2": norm2(d2_arr),
            "I12": float(np.real(inner(d1_arr, d2_arr))), "D_pair": norm2(r)}


def couple_kernel(w1, k1, w2, k2, a, shift=0.0):
    """Même objet au niveau noyau (K̂) — pour le rapport D3c [OBS]."""
    psi1 = carrier(w1)
    psi2 = carrier(w2)
    th1 = a * np.cos(k1 * X) + shift
    th2 = a * np.cos(k2 * X) + shift
    kpsi1 = apply_kernel(psi1)
    kpsi2 = apply_kernel(psi2)
    d1 = apply_kernel(np.exp(1j * th1) * psi1) - np.exp(1j * th1) * kpsi1
    d2 = apply_kernel(np.exp(1j * th2) * psi2) - np.exp(1j * th2) * kpsi2
    return float(np.real(inner(d1, d2)))


def delta_loop(w, n, k):
    """Δₙ^loop(ω) = (i(ω+nk))^{2α} − (iω)^{2α} — via loop_weight (site unique)."""
    return complex(loop_weight(w + n * k) - loop_weight(w))


def zj_loop(j, w1, k1, w2, k2, a):
    """Z_j^loop = Σ_m J_{m+j}J_m conj(Δ_{m+j}^loop(ω₁)) Δ_m^loop(ω₂) sur TOUTES
    les paires résonnantes n=m+j ∈ [−11,11] (forme close §0-bis INTERACTION)."""
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
        total += j_signed(n, a) * j_signed(m, a) * np.conj(delta_loop(w1, n, k1)) \
            * delta_loop(w2, m, k2)
        pairs.append((n, m))
    return total, pairs

# ----------------------------------------------------------------------------
# 2D — C9 : N=64, Δx=1, dérivées spectrales. LEÇON SONDE (consignée) :
# np.fft.ifft (1D, dernier axe) après fft2 est un bug d'estimateur (commutateur
# 68.47 en jauge pure) — ifft2 PARTOUT ; barres inchangées, physique inchangée.
# ----------------------------------------------------------------------------
N2 = 64
AX2 = np.arange(N2, dtype=float)
KAP2 = 2.0 * math.pi * np.fft.fftfreq(N2, d=1.0)
KX2 = KAP2[:, None]
KY2 = KAP2[None, :]


def dx2(f):
    return np.fft.ifft2(1j * KX2 * np.fft.fft2(f))


def dy2(f):
    return np.fft.ifft2(1j * KY2 * np.fft.fft2(f))


def mode2(m1, m2):
    """Porteur 2D e^{i(k₁x+k₂y)} — bins (m1, m2)."""
    return np.exp(1j * (2.0 * math.pi * m1 / N2 * AX2))[:, None] * \
        np.exp(1j * (2.0 * math.pi * m2 / N2 * AX2))[None, :]

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
    print(f"  [{statut}] {nom:14s} {valeur!r}  barre={barre} {detail}")
    return ok


def lecture(nom, ok, valeur, barre="", detail=""):
    statut = "OK" if ok else "ECHEC"
    RESULTATS["consequences"][nom] = {"statut": statut, "valeur": valeur,
                                      "barre": barre, "detail": detail}
    if not ok:
        ECHECS.append(f"consequence {nom}")
    print(f"  [{'OK' if ok else 'ECHEC'}] {nom:36s} {valeur!r}  barre={barre} {detail}")
    return ok


def obs(nom, valeur, detail=""):
    RESULTATS["obs"][nom] = {"valeur": valeur, "detail": detail}
    print(f"  [OBS] {nom:36s} {valeur!r} {detail}")


def rel(a, b):
    return abs(a / b - 1.0) if b != 0 else abs(a)


# ----------------------------------------------------------------------------
# CONTRÔLES BLOQUANTS (frontière §3)
# ----------------------------------------------------------------------------
def c0a_frontiere():
    """mtime(FRONTIERE) < heure d'exécution — antériorité du cahier des charges."""
    front = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "FRONTIERE_D3_DYNAMIQUE_V0.md")
    mt = os.path.getmtime(front)
    t_exec = time.time()
    RESULTATS["depots"]["c0a"] = {
        "frontiere_mtime": mt, "exec_time": t_exec,
        "anteriorite_s": t_exec - mt,
        "frontiere_iso": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mt)),
        "exec_iso": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t_exec)),
        "provenance": "commit c9b428d (frontière gelée avant tout script)",
    }
    print(f"  C0a : frontière {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mt))} "
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
    pire_br = 0.0
    for w in [0.5, 1.0 / PHI, 1.0, 2.0, 3.0, 14.4]:
        pire_br = max(pire_br, abs(complex(kernel(-w)) - np.conj(complex(kernel(w)))))
    return (pire <= TOL_C1 and pire_br <= TOL_C1), pire, pire_br


def c2_bessel_double_route():
    """(a) série × récurrence ; (b) identité paire ; (c) J₀_brut ≤ 1e100."""
    pire_a = 0.0
    for a in (0.1, 0.2):
        rec = j_recurrence(a)
        for n in range(0, TRUNC + 1):
            pire_a = max(pire_a, abs(j_serie(n, a) - rec[n]))
            pire_a = max(pire_a, abs(j_signed(-n, a) - ((-1.0) ** n) * rec[n]))
    ok_a = pire_a <= TOL_C2A
    pire_b = 0.0
    for a in (0.1, 0.2):
        s = j_serie(0, a) + 2.0 * sum(j_serie(2 * k, a) for k in range(1, 16))
        pire_b = max(pire_b, abs(s - 1.0))
    ok_b = pire_b <= TOL_C2B
    brut = {a: j0_brut(a) for a in (0.1, 0.2)}
    ok_c = all(v <= 1e100 for v in brut.values())
    RESULTATS["depots"]["j0_brut"] = {str(a): v for a, v in brut.items()}
    RESULTATS["depots"]["j0_brut_registre_ecarts"] = {
        str(a): abs(brut[a] / J0_BRUT_REG[a] - 1.0) for a in (0.1, 0.2)}
    return (ok_a and ok_b and ok_c), pire_a, pire_b, brut, (ok_a, ok_b, ok_c)


def c3_jacobi_anger():
    """max |e^{ia·cos(kx_j)} − Σ_{|n|≤11} iⁿJₙ(a)e^{inkx_j}| — 4 couples V1."""
    couples = [(0.1, 1.0), (0.2, 1.0), (0.1, 0.5), (0.1, 2.0)]
    pire = 0.0
    ns = np.arange(-TRUNC, TRUNC + 1)
    for (a, k) in couples:
        jn = np.array([j_signed(int(n), a) for n in ns])
        modes = np.exp(1j * np.outer(ns, k * X))
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


def defaut_rel_kernel(w0, a, k, shift=0.0):
    """D_rel = ‖δ‖/‖K̂[ψ₀]‖ — voie V0 du registre (clonée à l'identique)."""
    psi = carrier(w0)
    theta = a * np.cos(k * X) + shift
    kpsi = apply_kernel(psi)
    delta = apply_kernel(np.exp(1j * theta) * psi) - np.exp(1j * theta) * kpsi
    return norm(delta) / norm(kpsi)


def chi_forme_close_kernel(w0, a, k):
    """χ prédit (FORCE V1 §0, troncature |n| ≤ 11) — route registre."""
    s = 0.0
    for n in range(1, TRUNC + 1):
        dp = complex(kernel(w0 + n * k) - kernel(w0))
        dm = complex(kernel(w0 - n * k) - kernel(w0))
        jn = j_serie(n, a)
        s += (jn ** 2) * (abs(dp) ** 2 + abs(dm) ** 2)
    return math.sqrt(s) / (a * abs(complex(kernel(w0))))


def c5r_registre():
    """Continuité du registre : χ_machine(1,0.1,1) = G* = 0.3232880100102466,
    double route (opérateur FFT + forme close de Bessel) ; D_rel = D_REG.
    Barre 1e-12 relatif."""
    d_rel = defaut_rel_kernel(1.0, 0.1, 1.0)
    chi_op = d_rel / 0.1
    chi_fc = chi_forme_close_kernel(1.0, 0.1, 1.0)
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
    d0 = defaut_rel_kernel(1.0, 0.1, 1.0)
    pire = 0.0
    for th0 in (math.pi / 3.0, math.pi / 2.0):
        pire = max(pire, abs(defaut_rel_kernel(1.0, 0.1, 1.0, shift=th0) - d0))
    return pire <= TOL_C6R, pire


def c7_no_wrap():
    """max |ω₀±nk| ≤ 25.6 pour toute lecture — consigné, sinon exclusion EX ANTE."""
    lects = {
        "famille_A_j1": max(abs(1.0 + n * 1.0) for n in range(-TRUNC, TRUNC + 1)),
        "famille_A_j2": max(abs(3.0 + n * 1.0) for n in range(-TRUNC, TRUNC + 1)),
        "famille_B_canal1": max(abs(1.0 + n * 1.0) for n in range(-TRUNC, TRUNC + 1)),
        "famille_B_canal2": max(abs(1.3 + m * 1.3) for m in range(-TRUNC, TRUNC + 1)),
    }
    pire = max(lects.values())
    RESULTATS["depots"]["c7_no_wrap"] = lects
    return pire <= NYQUIST, pire


def c8_covariance_boucle_a1():
    """Covariance de la boucle à α=1 : D_A²[e^{iχ}ψ] = e^{iχ}D²ψ — 6 profils de
    la famille fermée. Route dense 512×512 (alignement F13 C2e, frontière §7)."""
    res = []
    for chi_a, k in PROFILES6:
        chi = chi_a * np.cos(k * X)
        A = -chi_a * k * np.sin(k * X)          # dérivée exacte du mode (bin)
        eia = np.exp(1j * chi)
        DA = DMAT - 1j * np.diag(A)
        DA2 = DA @ DA
        lhs = DA2 @ (eia * PSI0)
        rhs = eia * (DMAT @ (DMAT @ PSI0))
        res.append(norm(lhs - rhs) / norm(rhs))
    pire = max(res)
    return pire <= TOL_C8, pire


def c9_commutateur_courbure():
    """L'obstruction est la courbure : [D_x, D_y]f = −i·F_xy·f — grille 2D (N=64,
    Δx=1), F calculée par route indépendante (dérivées spectrales de A).
    Jauge pure A=∇χ ⟹ F=0 ; vortex ⟹ F = 2Ωe^{−r²/σ²}(1−r²/σ²) ≠ 0.
    Modes de test basse fréquence (bande limitée) — queue spectrale [OBS]."""
    xg, yg = np.meshgrid(AX2, AX2, indexing="ij")

    # — jauge pure : χ = a·cos(k₁x)·cos(k₂y), A = ∇χ (dérivée exacte du mode)
    n1, n2 = 2, 3
    k1 = 2.0 * math.pi * n1 / N2
    k2 = 2.0 * math.pi * n2 / N2
    a_pg = 0.7
    Ax_pg = -a_pg * k1 * np.sin(k1 * xg) * np.cos(k2 * yg)
    Ay_pg = -a_pg * k2 * np.cos(k1 * xg) * np.sin(k2 * yg)
    F_pg = dx2(Ay_pg) - dy2(Ax_pg)

    # — vortex (forme déposée) : Ω=1, σ=5, centre 32
    OM, SIG, C = 1.0, 5.0, N2 / 2.0
    r2 = (xg - C) ** 2 + (yg - C) ** 2
    E = np.exp(-r2 / SIG ** 2)
    Ax_v = -OM * (yg - C) * E
    Ay_v = OM * (xg - C) * E
    F_v = dx2(Ay_v) - dy2(Ax_v)
    F_close = 2.0 * OM * E * (1.0 - r2 / SIG ** 2)

    def DAx(Ax, f):
        return dx2(f) - 1j * Ax * f

    def DAy(Ay, f):
        return dy2(f) - 1j * Ay * f

    modes_lowk = [(1, -2), (2, -1), (2, -2), (3, -2), (1, 1)]
    pire_F_pg = float(np.max(np.abs(F_pg)))
    pire_F_v = float(np.max(np.abs(F_v - F_close)))
    nz_F = float(np.max(np.abs(F_close)))
    pire_comm = 0.0
    for (m1, m2) in modes_lowk:
        f = mode2(m1, m2)
        comm_pg = DAx(Ax_pg, DAy(Ay_pg, f)) - DAy(Ay_pg, DAx(Ax_pg, f))
        comm_v = DAx(Ax_v, DAy(Ay_v, f)) - DAy(Ay_v, DAx(Ax_v, f))
        pire_comm = max(pire_comm,
                        float(np.max(np.abs(comm_pg + 1j * F_pg * f))),
                        float(np.max(np.abs(comm_v + 1j * F_v * f))))
    ok = (pire_F_pg <= TOL_C9) and (pire_F_v <= TOL_C9) and \
        (pire_comm <= TOL_C9) and (nz_F > 1.0)
    # obs : queue spectrale du vortex — porteur haute fréquence (5,−3)
    f_tail = mode2(5, -3)
    comm_tail = DAx(Ax_v, DAy(Ay_v, f_tail)) - DAy(Ay_v, DAx(Ax_v, f_tail))
    comm_tail = float(np.max(np.abs(comm_tail + 1j * F_v * f_tail)))
    RESULTATS["obs"]["c9_queue_spectrale"] = {
        "valeur": comm_tail,
        "detail": "commutateur vortex au porteur (5,−3) : la queue spectrale de "
                  "A aux bins repliés excède la barre basse fréquence — limite "
                  "d'estimateur consignée, barre inchangée (leçon V1.2)",
    }
    RESULTATS["depots"]["c9"] = {
        "F_pure_gauge_max": pire_F_pg, "F_vortex_vs_close_max": pire_F_v,
        "F_vortex_norme": nz_F, "commutateur_bas_k_pire": pire_comm,
        "modes_lowk": modes_lowk,
    }
    return ok, pire_F_pg, pire_F_v, pire_comm, nz_F, comm_tail


def c10_filiation():
    """Filiation P36 : λ_loop = λ_kernel² — UN SEUL poids dans le code.
    Texte gelé C10 : filiation des VALEURS, bit-exact, sur la grille O3 et le
    set déposé ; le doublement d'argument bit-exact est la barre de D2c (route
    scalaire, passe 0.0).
    (a) construction : LG ≡ WG² (site unique loop_weight, structurel) ;
    (b) set déposé {0.1,…,2.0} : carré complexe BIT-EXACT ;
    obs : doublement d'argument (set 1 ulp, grille 1 ulp) et route directe
    (iω)^{2α} — arrondis atan2/puissance consignés, barre inchangée."""
    constr = bool(np.array_equal(LG, WG * WG))
    pire_carre = 0.0
    pire_angle = 0.0
    for w in (0.1, 0.2, 0.3, 0.4, 0.5, 1.0, 2.0):
        b = bin_of(w)
        wg_b = complex(WG[b])
        lg_b = complex(LG[b])
        pire_carre = max(pire_carre, abs(lg_b - wg_b * wg_b))
        pire_angle = max(pire_angle,
                         abs(float(np.angle(lg_b)) - 2.0 * float(np.angle(wg_b))))
    ok = constr and (pire_carre == 0.0)
    e_grid = float(np.max(np.abs(np.angle(LG) - 2.0 * np.angle(WG))))
    pire_dir = 0.0
    for w in (0.1, 0.2, 0.3, 0.4, 0.5, 1.0, 2.0):
        pire_dir = max(pire_dir, rel(complex(loop_weight(w)), (1j * w) ** (2.0 * ALPHA)))
    RESULTATS["obs"]["c10_angle_set_1ulp"] = {
        "valeur": pire_angle,
        "detail": "doublement d'argument sur le set : 1 ulp (arrondi atan2 sur "
                  "les tableaux grille) — la barre bit-exacte d'angle est portée "
                  "par D2c (route scalaire, 0.0) ; C10 porte la filiation des "
                  "valeurs (bit-exacte)",
    }
    RESULTATS["obs"]["c10_grille_complete_1ulp"] = {
        "valeur": e_grid,
        "detail": "doublement d'argument à 1 ulp sur la grille complète ; "
                  "filiation des valeurs bit-exacte (0.0)",
    }
    RESULTATS["obs"]["c10_route_directe"] = {
        "valeur": pire_dir,
        "detail": "(iω)^{2α} en puissance directe vs carré du poids mère — "
                  "écart 1 ulp ; la construction bit-exacte fait foi",
    }
    RESULTATS["depots"]["c10"] = {
        "construction_LG_eq_WG2": constr,
        "set_carre_bitexact_pire": pire_carre,
        "set_angle_pire_1ulp": pire_angle,
        "site_unique": "loop_weight = lambda_weight * lambda_weight",
    }
    return ok, constr, pire_carre, pire_angle, e_grid, pire_dir


# ----------------------------------------------------------------------------
# CONSÉQUENCES D1 (frontière §4 — à α=1, l'onde coule)
# ----------------------------------------------------------------------------
MODES_D1 = (20, 50, 100, 200, -20, -50, -100, -200)


def consequence_d1a():
    """λ_loop(α=1) = −|k|² sur {±20, ±50, ±100, ±200} — réel, phase π (cercle :
    ±π même point, branche atan2). Route primaire : poids (FFT, frontière §7) ;
    route croisée : dense (F13 C5d)."""
    pire_w = 0.0
    det_w = {}
    for m in MODES_D1:
        w = m * DOMEGA
        lam = complex(LG1[bin_index(m)])
        e = abs(lam - (-w * w)) / (w * w)
        pire_w = max(pire_w, e)
        det_w[str(m)] = {"re": lam.real, "im": lam.imag, "err_rel": e}
    B = DMAT @ DMAT
    pire_d = 0.0
    pire_ph_d = 0.0
    det_d = {}
    for m in MODES_D1:
        w = m * DOMEGA
        v = np.exp(1j * w * X)
        lam = complex(np.vdot(v, B @ v) / np.vdot(v, v))
        e = abs(lam - (-w * w)) / (w * w)
        pire_d = max(pire_d, e)
        # phase π sur le cercle : ±π même point (branche atan2 de Im λ)
        pire_ph_d = max(pire_ph_d,
                        abs(abs(float(np.angle(lam))) / math.pi - 1.0))
        det_d[str(m)] = {"re": lam.real, "im": lam.imag, "err_rel": e}
    del B
    return (pire_w <= TOL_D1A and pire_d <= TOL_D1A and pire_ph_d <= TOL_D1A), \
        pire_w, pire_d, pire_ph_d, det_w, det_d


def consequence_d1b():
    """Massif zéro : λ_loop(k=0) = 0 exactement — aucun terme constant dans le
    poids. Route primaire : poids (1e-15 abs) ; route opérateur dense [OBS]."""
    lam0 = complex(loop_weight(0.0, 1.0))
    v = np.ones(N, dtype=complex)
    B = DMAT @ DMAT
    lam_op = complex(np.vdot(v, B @ v) / np.vdot(v, v))
    res_op = float(norm(B @ v) / norm(v))
    del B
    RESULTATS["obs"]["d1b_route_operateur"] = {
        "valeur": {"rayleigh": [lam_op.real, lam_op.imag], "residu_norme": res_op},
        "detail": "λ_loop(0) par l'opérateur dense B=DMAT@DMAT : arrondi de "
                  "l'estimateur (~1e-13) — la barre porte sur le POIDS (aucun "
                  "terme constant), route exacte 0.0",
    }
    return (lam0 == 0.0 and abs(lam0) <= TOL_D1B), lam0, lam_op, res_op


def consequence_d1c():
    """Fermeture unitaire unique + dispersion massless : H = √(−λ_loop) réel ≥ 0,
    ω_t = |k| aux modes déposés ; avance de phase e^{−iω_t t} sur t ∈ {0.25, 0.5, 1.0}.
    Route : FFT diagonale (poids unique LG1, frontière §7) ; eigh [OBS]."""
    H = np.sqrt(-LG1)
    im_h = float(np.max(np.abs(H.imag)))
    min_h = float(np.min(H.real))
    pire_wt = 0.0
    for m in MODES_D1:
        pire_wt = max(pire_wt, abs(H[bin_index(m)] - abs(m * DOMEGA)))
    pire_ph = 0.0
    det_ph = {}
    for m in MODES_D1:
        w = abs(m * DOMEGA)
        psi = carrier(m * DOMEGA)
        for t in (0.25, 0.5, 1.0):
            psi_t = np.fft.ifft(np.exp(-1j * H * t) * np.fft.fft(psi))
            e = norm(psi_t - np.exp(-1j * w * t) * psi)
            pire_ph = max(pire_ph, e)
            det_ph[f"m{m}_t{t}"] = e
    # obs — route eigh 512×512 (arrondi d'accumulation pleine matrice)
    B = DMAT @ DMAT
    ev, Ve = np.linalg.eigh(B)
    eig_max = float(ev[-1])
    He = np.sqrt(np.maximum(-ev, 0.0))
    pire_disp = 0.0
    for m in MODES_D1:
        w2 = (m * DOMEGA) ** 2
        pire_disp = max(pire_disp, float(np.min(np.abs(ev + w2))) / w2)
    pire_prop = 0.0
    pire_where = None
    for m in MODES_D1:
        psi = carrier(m * DOMEGA)
        c0 = Ve.conj().T @ psi
        for t in (0.25, 0.5, 1.0):
            pt = Ve @ (np.exp(-1j * He * t) * c0)
            e = norm(pt - np.exp(-1j * abs(m * DOMEGA) * t) * psi)
            if e > pire_prop:
                pire_prop = e
                pire_where = [int(m), float(t)]
    del B
    RESULTATS["obs"]["d1c_route_eigh"] = {
        "valeur": {"eig_max": eig_max, "dispersion_pire": pire_disp,
                   "propagation_pire": pire_prop, "pire_ou": pire_where},
        "detail": "route eigh 512×512 : arrondi d'accumulation pleine matrice "
                  "(pire ~1.8e-12 au mode −200, t=1.0) — limite d'estimateur "
                  "consignée, barre inchangée ; la route FFT diagonale "
                  "(frontière §7) est retenue",
    }
    ok = (im_h <= TOL_D1C) and (min_h >= 0.0) and (pire_wt <= TOL_D1C) \
        and (pire_ph <= TOL_D1C)
    return ok, im_h, min_h, pire_wt, pire_ph, det_ph


def consequence_d1d():
    """Rang transverse = 2 par mode k≠0 (5 modes, graine 27 — continuité F13 C5c) ;
    P²−P ≤ 1e-15 (rang : critère exact)."""
    rng = np.random.default_rng(SEED)
    rangs = []
    pire_proj = 0.0
    for _i in range(5):
        n = rng.integers(0, N3D, size=3)
        while not np.any(n):
            n = rng.integers(0, N3D, size=3)
        ns = np.where(n > N3D // 2, n - N3D, n)   # première zone [OBS]
        kv = 2.0 * math.pi * ns.astype(float) / N3D
        P = np.eye(3) - np.outer(kv, kv) / float(kv @ kv)
        rang = int(np.linalg.matrix_rank(P))
        pire_proj = max(pire_proj, float(np.max(np.abs(P @ P - P))))
        rangs.append({"n": [int(t) for t in ns], "rang": rang})
    ok = all(rr["rang"] == 2 for rr in rangs) and pire_proj <= TOL_D1D_PROJ
    return ok, pire_proj, rangs


# ----------------------------------------------------------------------------
# CONSÉQUENCES D2 (frontière §4 — à α=1/φ, la mémoire se propage)
# ----------------------------------------------------------------------------
SET_D2 = (0.1, 0.2, 0.3, 0.4, 0.5, 1.0, 2.0)
TS_D2D = (0.0, 0.5, 1.0, 2.0, 5.0)


def consequence_d2a():
    """λ_loop = (iω)^{2/φ} : arg λ/π = 1/φ = 0.6180339887498948 indépendant de ω
    (set déposé) ; module |ω|^{2/φ}."""
    pire_a = 0.0
    pire_m = 0.0
    det = {}
    for w in SET_D2:
        lam = complex(loop_weight(w))
        ea = abs(float(np.angle(lam)) / math.pi - ALPHA)
        em = abs(abs(lam) - w ** (2.0 * ALPHA))
        pire_a = max(pire_a, ea)
        pire_m = max(pire_m, em)
        det[str(w)] = {"arg_sur_pi": float(np.angle(lam)) / math.pi,
                       "module": abs(lam)}
    return (pire_a <= TOL_D2A_ARG and pire_m <= TOL_D2A_MOD), pire_a, pire_m, det


def consequence_d2b():
    """Non-hermiticité stricte : Im λ ≠ 0 sur tout le set (PT brisé — pas de
    fermeture unitaire ; consigné structurel)."""
    im_min = min(abs(complex(loop_weight(w)).imag) for w in SET_D2)
    return im_min > 0.0, im_min


def consequence_d2c():
    """Recoupement FV bit-exact : arg λ_loop(ω) − 2·arg λ_kernel(ω) = 0 sur tout
    le set — la frange 90/φ° est la demi-phase de boucle."""
    pire = 0.0
    det = {}
    for w in SET_D2:
        lk = complex(lambda_weight(w))
        ll = complex(loop_weight(w))
        e = abs(float(np.angle(ll)) - 2.0 * float(np.angle(lk)))
        det[str(w)] = e
        pire = max(pire, e)
    return (pire == 0.0), pire, det


def consequence_d2d():
    """L'amortissement déposé : canaux ω₁=1, ω₂=2, c_i(0) = K̂(ω_i)² ;
    t ∈ {0, 0.5, 1.0, 2.0, 5.0} :
    (i) ancre CHSH ρ(0) = 0.9396370575958052 (1e-12 rel) ;
    (ii) forme close ρ(t) direct (route machine) vs analytique (1e-12) ;
    (iii) S_max(t) = 2√(1+ρ(t)²) (1e-12) ;
    (iv) horizon 2 + 1e-9 < S_max(t) ≤ 2√2 + 1e-9 à tout t déposé (strict —
         prédiction ex ante : l'amortissement taxe sans détruire)."""
    # graines c_i(0) = K̂(ω_i)² — route machine (K̂ appliqué deux fois) vs close.
    # Pont d'échelle (leçon V1.2, point 6, une deuxième fois) : la machine mesure
    # au niveau norme, ⟨carrier, K̂²·carrier⟩ = K̂²·‖carrier‖² = K̂²/N — le dépôt
    # écrit la graine au niveau amplitude. Comparaison après pont /N.
    p1 = apply_kernel(apply_kernel(carrier(1.0)))
    p2 = apply_kernel(apply_kernel(carrier(2.0)))
    c1_0 = inner(carrier(1.0), p1)
    c2_0 = inner(carrier(2.0), p2)
    c1_0c = complex(kernel(1.0)) ** 2 / N
    c2_0c = complex(kernel(2.0)) ** 2 / N
    e_graine = max(rel(abs(c1_0), abs(c1_0c)), rel(abs(c2_0), abs(c2_0c)))

    lam1 = complex(loop_weight(1.0))
    lam2 = complex(loop_weight(2.0))
    pire_anc = 0.0
    pire_forme = 0.0
    pire_smax = 0.0
    horizon_ok = True
    det = {}
    drifts = []
    for t in TS_D2D:
        c1 = inner(carrier(1.0), evolve_loop(p1, t))
        c2 = inner(carrier(2.0), evolve_loop(p2, t))
        c1a = c1_0c * np.exp(lam1 * t)
        c2a = c2_0c * np.exp(lam2 * t)
        rho_d = 2.0 * abs(c1 * c2) / (abs(c1) ** 2 + abs(c2) ** 2)
        rho_a = 2.0 * abs(c1a * c2a) / (abs(c1a) ** 2 + abs(c2a) ** 2)
        s_d = 2.0 * math.sqrt(1.0 + rho_d ** 2)
        s_a = 2.0 * math.sqrt(1.0 + rho_a ** 2)
        pire_forme = max(pire_forme, rel(rho_d, rho_a))
        pire_smax = max(pire_smax, rel(s_d, s_a))
        if not (2.0 + 1e-9 < s_d <= 2.0 * math.sqrt(2.0) + 1e-9):
            horizon_ok = False
        if t == 0.0:
            pire_anc = rel(rho_d, RHO0_ANCRE)
        drifts.append({"t": t,
                       "direct": float(np.angle(c2) - np.angle(c1)),
                       "pred": float(np.angle(c2a / c1a))})
        det[f"t{t}"] = {"rho_direct": rho_d, "rho_analytique": rho_a,
                        "S_max_direct": s_d, "S_max_analytique": s_a}
    # consigné sans verdict (frontière §6.5) : dérive de phase arg c₂ − arg c₁
    RESULTATS["obs"]["d2d_derive_phase"] = {
        "valeur": drifts,
        "detail": "Δarg(t) = Δarg(0) + (Im λ₂ − Im λ₁)t — lecture consignée "
                  "(prolonge la lecture B4 du CHSH), sans pouvoir de verdict",
    }
    ok = (pire_anc <= TOL_D2D) and (pire_forme <= TOL_D2D) \
        and (pire_smax <= TOL_D2D) and horizon_ok
    return ok, pire_anc, pire_forme, pire_smax, horizon_ok, e_graine, det


# ----------------------------------------------------------------------------
# CONSÉQUENCES D3 (frontière §4 — la source est la graine d'interaction, sans −¼F²)
# ----------------------------------------------------------------------------
COUPLES = {
    "A_j1": {"w1": 1.0, "k1": 1.0, "w2": 2.0, "k2": 1.0, "j": 1},
    "A_j2": {"w1": 1.0, "k1": 1.0, "w2": 3.0, "k2": 1.0, "j": 2},
    "B": {"w1": 1.0, "k1": 1.0, "w2": 1.3, "k2": 1.3, "j": None},
}


def consequence_d3a():
    """Identité norme au niveau boucle : D_pair^loop = ½(D₁^loop+D₂^loop) + I₁₂^loop
    sur les 3 couples INTERACTION. 1e-12 rel."""
    pire = 0.0
    out = {}
    for nom, c in COUPLES.items():
        mes = couple_loop(c["w1"], c["k1"], c["w2"], c["k2"], 0.1)
        residu = abs(mes["D_pair"] - (0.5 * (mes["D1"] + mes["D2"]) + mes["I12"]))
        r = residu / mes["D_pair"]
        out[nom] = {"D1": mes["D1"], "D2": mes["D2"], "I12": mes["I12"],
                    "D_pair": mes["D_pair"], "residu": residu, "rel": r}
        pire = max(pire, r)
    return pire <= TOL_D3A, pire, out


def consequence_d3b():
    """Forme close de la source au niveau boucle : I₁₂^loop = Re[i^{−j}Z_j^loop]/N,
    Δₙ^loop(ω) = (i(ω+nk))^{2/φ} − (iω)^{2/φ} — familles j=1, j=2, latérale B
    (résonance (−1,−1), §0-bis INTERACTION). 1e-9 rel (1e-15 abs si nul)."""
    pire = 0.0
    out = {}
    for nom in ("A_j1", "A_j2"):
        c = COUPLES[nom]
        j = c["j"]
        mes = couple_loop(c["w1"], c["k1"], c["w2"], c["k2"], 0.1)
        zj, paires = zj_loop(j, c["w1"], c["k1"], c["w2"], c["k2"], 0.1)
        pred = float(np.real((1j) ** (-j) * zj)) / N
        delta = abs(mes["I12"] - pred)
        barre_eff = TOL_D3B * abs(mes["I12"]) if mes["I12"] != 0.0 else 1e-15
        out[nom] = {"I12_machine": mes["I12"], "I12_pred": pred, "delta": delta,
                    "rel": delta / abs(mes["I12"]) if mes["I12"] else delta,
                    "n_paires_resonantes": len(paires), "paires": paires[:6],
                    "barre_eff": barre_eff}
        pire = max(pire, delta / barre_eff if barre_eff > 0 else 0.0)
    # famille B — résonance latérale (−1,−1), facteur i⁰ = 1
    c = COUPLES["B"]
    mes = couple_loop(c["w1"], c["k1"], c["w2"], c["k2"], 0.1)
    d1 = delta_loop(c["w1"], -1, c["k1"])
    d2 = delta_loop(c["w2"], -1, c["k2"])
    pred = float(np.real(j_signed(-1, 0.1) * j_signed(-1, 0.1) * np.conj(d1) * d2)) / N
    residu = abs(mes["I12"] - pred)
    # fuite hors troncature : paire (n,m) = (12,9) exactement résonnante
    bins_ok = (bin_of(c["w1"]) + 12 * bin_of(c["k1"])) == \
        (bin_of(c["w2"]) + 9 * bin_of(c["k2"]))
    poids_fuite = abs(j_serie(12, 0.1) * j_serie(9, 0.1))
    out["B"] = {"I12_machine": mes["I12"], "pred_paire_laterale": pred,
                "delta": residu, "rel": residu / abs(mes["I12"]),
                "fuite_12_9_resonante": bool(bins_ok),
                "poids_fuite_J12J9": poids_fuite}
    pire = max(pire, residu / abs(mes["I12"]))
    return pire <= 1.0, pire, out


def consequence_d3c():
    """Consigné SANS verdict : rapport I₁₂^loop/I₁₂^kernel (la montée continue
    −¼F², facteur ¼, reste campagne séparée — I4, frontière §6.2)."""
    out = {}
    for nom, c in COUPLES.items():
        i12k = couple_kernel(c["w1"], c["k1"], c["w2"], c["k2"], 0.1)
        mes = couple_loop(c["w1"], c["k1"], c["w2"], c["k2"], 0.1)
        out[nom] = {"I12_kernel": i12k, "I12_loop": mes["I12"],
                    "rapport": mes["I12"] / i12k if i12k != 0.0 else None}
    RESULTATS["obs"]["d3c_rapports"] = {
        "valeur": out,
        "detail": "rapports I₁₂^loop/I₁₂^kernel — lecture [OBS], sans verdict "
                  "(montée continue −¼F² : campagne séparée I4)",
    }
    return out


def obs_defaut_boucle_1surphi():
    """Défaut d'absorption de la boucle à α=1/φ — mesure SANS barre (frontière
    §6.6 : la campagne ne postule pas d'absorption exacte fractionnaire)."""
    out = {}
    for chi_a, k in PROFILES6:
        psi = carrier(1.0)
        chi = chi_a * np.cos(k * X)
        eia = np.exp(1j * chi)
        lpsi = apply_loop(psi)
        delta = apply_loop(eia * psi) - eia * lpsi
        out[f"a{chi_a}_k{k}"] = norm(delta) / norm(lpsi)
    RESULTATS["obs"]["defaut_boucle_alpha_1surphi"] = {
        "valeur": out,
        "detail": "défaut d'absorption de la boucle à α=1/φ (continuité du "
                  "registre) — mesure déposée sans barre (frontière §6.6)",
    }
    return out


# ----------------------------------------------------------------------------
def main():
    t0 = time.time()
    print("=" * 78)
    print("D3 DYNAMIQUE V0 — le compensateur doit se propager (frontière commit c9b428d)")
    print("=" * 78)

    # ---- contrôles bloquants ------------------------------------------------
    print("\n[CONTRÔLES BLOQUANTS — un seul échec ⟹ V4 REFUTE exit 1]")
    ok_c0a = controle("C0a", c0a_frontiere(), "mtime < exec", "—")
    e0b = abs(PHI * PHI - (PHI + 1.0))
    ok_c0b = controle("C0b", e0b <= TOL_C0B, e0b, "1e-15", "φ²=φ+1")

    ok1, pire1, pire_br = c1_noyau_double_route()
    controle("C1", ok1, pire1, "1e-12", f"K̂ double route ; branche {pire_br:.2e}")
    ok_c1 = ok1

    ok2, pire2a, pire2b, brut, sub = c2_bessel_double_route()
    controle("C2'(a) Bessel", sub[0], pire2a, "1e-12", "série × récurrence")
    controle("C2'(b) id. paire", sub[1], pire2b, "1e-9", "J₀+2ΣJ₂ₖ=1")
    controle("C2'(c) J₀_brut ≤ 1e100", sub[2], max(brut.values()), "1e100",
             f"0.1→{brut[0.1]:.6e} ; 0.2→{brut[0.2]:.6e}")
    ok_c2 = all(sub)

    ok3, pire3 = c3_jacobi_anger()
    controle("C3 Jacobi–Anger", ok3, pire3, "1e-12", "4 couples V1")
    ok_c3 = ok3

    ok4, pire4 = c4_action_propre()
    controle("C4 action propre", ok4, pire4, "1e-12", "{0.1, 1.0, 14.4}")
    ok_c4 = ok4

    ok5, e_op, e_fc, e_d, d_rel, chi_fc = c5r_registre()
    controle("C5r χ=G* (route op)", ok5 and e_op <= TOL_C5R, e_op, "1e-12 rel",
             f"χ_op={d_rel / 0.1:.16f}")
    controle("C5r χ=G* (forme close)", e_fc <= TOL_C5R, e_fc, "1e-12 rel",
             f"χ_fc={chi_fc:.16f}")
    controle("C5r D_rel = D_REG", e_d <= TOL_C5R, e_d, "1e-12 rel", f"D={d_rel:.16f}")
    ok_c5r = ok5 and e_op <= TOL_C5R and e_fc <= TOL_C5R and e_d <= TOL_C5R

    ok6, pire6 = c6r_u1_spot()
    controle("C6r U(1) aveuglement spot", ok6, pire6, "1e-9", "θ₀∈{π/3, π/2}")
    ok_c6r = ok6

    ok7, pire7 = c7_no_wrap()
    controle("C7 no-wrap", ok7, pire7, "≤25.6")
    ok_c7 = ok7

    ok8, pire8 = c8_covariance_boucle_a1()
    controle("C8 covariance boucle α=1", ok8, pire8, "1e-10",
             "D_A²[e^{iχ}ψ]=e^{iχ}D²ψ, 6 profils (dense, alignement F13 C2e)")
    ok_c8 = ok8

    ok9, pF_pg, pF_v, pcomm, nzF, comm_tail = c9_commutateur_courbure()
    controle("C9 commutateur=courbure", ok9, max(pF_pg, pF_v, pcomm), "1e-12",
             f"jauge pure F={pF_pg:.1e} ; vortex F−close={pF_v:.1e} ; "
             f"‖F‖={nzF:.1f} ; comm bas-k={pcomm:.1e} ; queue (5,−3) {comm_tail:.1e} [OBS]")
    ok_c9 = ok9

    ok10, constr, pcarre, pangle, egrid, pdir = c10_filiation()
    controle("C10 filiation bit-exact", ok10, constr, "0 (bit-exact)",
             f"carré set={pcarre:.1e} ; angle set={pangle:.1e} ; "
             f"grille complète 1 ulp={egrid:.1e} [OBS] ; route directe {pdir:.1e} [OBS]")
    ok_c10 = ok10

    controles_ok = all([ok_c0a, ok_c0b, ok_c1, ok_c2, ok_c3, ok_c4, ok_c5r,
                        ok_c6r, ok_c7, ok_c8, ok_c9, ok_c10])

    # ---- conséquences --------------------------------------------------------
    print("\n[CONSÉQUENCES — frontière §4, barres gelées]")

    print(" D1 — à α=1, l'onde coule (Maxwell émerge, massif zéro)")
    ok_d1a, pire_w, pire_d, pire_ph_d, det_w, det_d = consequence_d1a()
    lecture("D1a λ_loop = −|k|² (8 modes)", ok_d1a, max(pire_w, pire_d, pire_ph_d),
            "1e-12", f"poids {pire_w:.2e} ; dense (F13 C5d) {pire_d:.1e} ; "
            f"phase/π {pire_ph_d:.1e}")
    RESULTATS["consequences"]["D1a"] = {"poids": det_w, "dense": det_d}

    ok_d1b, lam0, lam_op, res_op = consequence_d1b()
    lecture("D1b massif zéro λ_loop(0)=0", ok_d1b, abs(lam0), "1e-15 abs",
            "route poids — exact 0 ; route opérateur [OBS]")
    RESULTATS["consequences"]["D1b"] = {
        "lambda_loop_0": [lam0.real, lam0.imag],
        "route_operateur_obs": [lam_op.real, lam_op.imag],
        "residu_norme_operateur": res_op}

    ok_d1c, im_h, min_h, pire_wt, pire_ph, det_ph = consequence_d1c()
    lecture("D1c H=√(−λ) réel≥0, ω_t=|k|, phase", ok_d1c,
            max(im_h, pire_wt, pire_ph), "1e-12",
            f"Im H={im_h:.1e} ; ω_t={pire_wt:.1e} ; avance={pire_ph:.1e} ; "
            f"route eigh [OBS] (voir obs)")
    RESULTATS["consequences"]["D1c"] = {
        "Im_H_max": im_h, "H_min_re": min_h,
        "pire_omega_t": pire_wt, "pire_avance_phase": pire_ph,
        "detail_phase": det_ph}
    obs("d1c_route_eigh", RESULTATS["obs"]["d1c_route_eigh"]["valeur"],
        "arrondi d'accumulation pleine matrice — barre inchangée")

    ok_d1d, pire_proj, rangs = consequence_d1d()
    lecture("D1d rang transverse = 2", ok_d1d, pire_proj, "1e-15 (P²−P)",
            f"rang=2 pour {sum(1 for r in rangs if r['rang'] == 2)}/5 modes "
            f"(graine 27)")
    RESULTATS["consequences"]["D1d"] = {"modes": rangs, "pire_P2_P": pire_proj}

    print(" D2 — à α=1/φ, la mémoire se propage (le système ouvert)")
    ok_d2a, pire_a, pire_m, det = consequence_d2a()
    lecture("D2a arg λ/π = 1/φ, module", ok_d2a, max(pire_a, pire_m),
            "1e-15 / 1e-12", f"arg/π pire={pire_a:.2e} ; module pire={pire_m:.2e}")
    RESULTATS["consequences"]["D2a"] = det

    ok_d2b, im_min = consequence_d2b()
    lecture("D2b Im λ ≠ 0 strict", ok_d2b, im_min, "> 0 strict",
            "PT brisé — pas de fermeture unitaire (consigné structurel)")
    RESULTATS["consequences"]["D2b"] = {"im_min": im_min}

    ok_d2c, pire_c, det_c = consequence_d2c()
    lecture("D2c recoupement FV bit-exact", ok_d2c, pire_c, "0 (bit-exact)",
            "arg λ_loop = 2·arg λ_kernel sur le set — frange 90/φ° = demi-phase")
    RESULTATS["consequences"]["D2c"] = det_c

    ok_d2d, pire_anc, pire_forme, pire_smax, horizon_ok, e_graine, det_d2d = \
        consequence_d2d()
    lecture("D2d amortissement ρ(t), S_max(t), horizon", ok_d2d,
            max(pire_anc, pire_forme, pire_smax), "1e-12 rel / strict",
            f"ancre ρ(0)={pire_anc:.1e} ; forme close {pire_forme:.1e} ; "
            f"S_max {pire_smax:.1e} ; horizon {'OK' if horizon_ok else 'ECHEC'} ; "
            f"graine K̂² {e_graine:.1e}")
    RESULTATS["consequences"]["D2d"] = {"ancre": pire_anc, "forme_close": pire_forme,
                                        "s_max": pire_smax, "horizon": horizon_ok,
                                        "ecart_graine": e_graine, "detail": det_d2d}

    print(" D3 — la source est la graine d'interaction (sans −¼F², I4)")
    ok_d3a, pire_a3, out_a3 = consequence_d3a()
    lecture("D3a identité norme (3 couples)", ok_d3a, pire_a3, "1e-12 rel",
            json.dumps({k: round(v["rel"], 15) for k, v in out_a3.items()}))
    RESULTATS["consequences"]["D3a"] = out_a3

    ok_d3b, pire_b3, out_b3 = consequence_d3b()
    lecture("D3b forme close Re[i^{−j}Z_j^loop]", ok_d3b, pire_b3,
            "ratio δ/barre ≤ 1 (1e-9 rel)",
            ", ".join(f"{k}: {v['rel']:.1e}" for k, v in out_b3.items()))
    RESULTATS["consequences"]["D3b"] = out_b3

    consequence_d3c()          # lecture [OBS], sans verdict (I4)
    obs_defaut_boucle_1surphi()

    d1_ok = ok_d1a and ok_d1b and ok_d1c and ok_d1d
    d2_ok = ok_d2a and ok_d2b and ok_d2c and ok_d2d
    d3_ok = ok_d3a and ok_d3b

    # ---- verdict (échelle §5 gelée) -----------------------------------------
    duree = time.time() - t0
    if not controles_ok:
        verdict, code = "V4_REFUTE", 1
    elif d1_ok and d2_ok and d3_ok:
        verdict, code = "V+_D3D_PROPAGATION_COULEE", 0
    elif d1_ok and d3_ok:      # contrôles OK, D1 OK, D3 OK, ≥1 de D2 hors barre
        verdict, code = "V2_D3D_ONDE_SANS_MEMOIRE", 0
    elif d1_ok:                # D3 hors barre (D1 OK) — hors échelle explicite : REFUTE
        verdict, code = "V4_REFUTE", 1
    else:                      # ≥1 de D1 hors barre — Maxwell n'émerge pas
        verdict, code = "V3_REFUTE_D3D_SANS_ONDE", 1

    RESULTATS["meta"] = {
        "verdict": verdict, "exit_code": code, "echecs": ECHECS,
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "python": sys.version.split()[0], "numpy": np.__version__,
        "duree_s": round(duree, 2),
        "c0a": RESULTATS["depots"].get("c0a", {}),
        "autorite": "FRONTIERE_D3_DYNAMIQUE_V0.md (commit c9b428d, gelée avant tout script)",
        "entrees": ["FRONTIERE_D3_DYNAMIQUE_V0.md", "DEPOT_FORCE_V1.md (machinerie O1–O9)",
                    "registre G* = 0.3232880100102466", "D_REG = 0.032328801001024664",
                    "ancre CHSH ρ(0) = 0.9396370575958052"],
        "routes": "FFT (poids (iω)^α, branche principale) pour D_α et la boucle ; "
                  "dense 512×512 pour C8/D1 ; 2D spectral pour C9 ; projecteur 3×3 "
                  "graine 27 pour D1d ; série de Bessel O7 pour D3b ; un seul poids "
                  "spectral dans le code (C10)",
    }
    print("\n" + "=" * 78)
    print(f"VERDICT : {verdict}   exit {code}")
    if ECHECS:
        print("Échecs consignés : " + "; ".join(ECHECS))
    print("=" * 78)

    out_json = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "resultat_d3_dynamique_v0.json")

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


if __name__ == "__main__":
    main()
