#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
I4 V0 — la montée vers le terme continu −¼F² : le facteur ¼ sort des
identités de Bessel, jamais écrit à la main.

EXÉCUTION de la FRONTIÈRE I4 V0 (FRONTIERE_I4_V0.md, commit 459b5ba) —
cahier des charges gelé AVANT tout script (C0a, mtime faisant foi). La thèse
Q1–Q5 et les barres C0a–C10 / D1a–c / D2a–b / D3a–b sont celles du document,
non modifiables (I5).

Échelle de verdicts GELÉE (frontière §5, non modifiable) :
  V+ I4_MONTEE_QUART_FERMEE     exit 0  (contrôles OK ET D1(a–c) ET D2a ET D3a)
  V2 I4_QUART_SEUL              exit 0  (contrôles OK, D1 OK, D2a ou D3a hors barre)
  V3 REFUTE_I4_SANS_QUART       exit 1  (contrôles OK, ≥1 de D1 hors barre)
  V4 REFUTE                     exit 1  (tout contrôle bloquant en échec)

Un seul échec (contrôle OU conséquence) ⟹ REFUTE — aucun sauvetage.
Tout estimateur est bugable : un bug d'estimateur consigné n'est pas une
physique réfutée (barres gelées inchangées — leçon FORCE V1.1/V1.2/V1.3).
Lectures [OBS] : consignées, sans pouvoir de verdict.

CRITÈRE ANTI-RÉTRO-INGÉNIERIE (frontière §1, verbatim OUVERTURE §5) : le
facteur ¼ doit sortir des identités de Bessel (conséquence), jamais y entrer
(ingrédient). Le code ne contient QU'UN SEUL poids spectral : lambda_weight —
la boucle est son carré (loop_weight = λ_kernel², site unique de mise au
carré). Le formulaire fermé (a²k²/4)[…] n'apparaît QUE comme prédiction
falsifiée (D1b), construite sur les sommes S₂/A₂/V₂/W₂ MESURÉES (C3/C4) ;
la route machine (FFT, séries, sommes) ne contient AUCUN ¼, aucun terme
−¼F² écrit comme ingrédient — sinon non-émérgé → REFUTE du niveau visé.

Routes (frontière §7) : FFT (poids (iω)^α, branche principale) pour le noyau
et la boucle (α=1 via LG1 = WG1², α=1/φ via LG = WG²) ; série de Bessel O7
(parité J₋ₙ = (−1)ⁿJₙ) pour les sommes et les Z_j ; forme close Δₙ^loop(α=1)
= −(ω+nk)²+ω² lue dans le poids (polynôme exact, aucun reste de Taylor) ;
dérivées analytiques K̂′, L′ UNIQUEMENT pour les leads adiabatiques Q5
(objet falsifié — jamais route machine). Un seul poids spectral (C10).
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

# ----------------------------------------------------------------------------
# O7 — barres gelées (frontière §3 contrôles, §4 conséquences)
# ----------------------------------------------------------------------------
TOL_C0B = 1e-15
TOL_C1 = 1e-12        # K̂ double route
TOL_C2A = 1e-12       # Bessel série × récurrence
TOL_C2B = 1e-9        # identité paire J₀+2ΣJ₂ₖ=1
TOL_C3 = 1e-15        # identités Q1 (absolu)
TOL_C4 = 1e-12        # formulaire Q2 (relatif)
TOL_C5 = 1e-12        # réseau vs forme (relatif)
TOL_C6 = 1e-15        # silence impaire (absolu)
TOL_D1 = 1e-12        # montée exacte / forme famille (relatif)
TOL_D1C_BAS, TOL_D1C_HAUT = 0.95, 1.10   # limite adiabatique (ratio)

TRUNC_I4 = 20         # |n| ≤ 20 — sommes Z_j I4 (frontière §2)
M_ID = 40             # M = 40 — identités de Bessel (frontière §2)

# Grille I4 gelée (frontière §2) :
A_ID = (0.1, 0.3, 0.5, 1.0, 1.3)                        # identités C3
A_SET = (0.1, 0.5, 1.0, 1.3)                            # formulaire C4/C5
K_SET = (0.1, 0.2, 0.5, 1.0)                            # k
W1_SET = (0.5, 1.0, 2.0)                                # ω₁
A_D1 = (0.1, 1.0)                                       # D1a
K_D1 = (0.1, 0.2)                                       # D1a
W1_D1 = (0.5, 1.0)                                      # D1a
A_ODD = (0.1, 1.0)                                      # familles impaires C6
K_ODD = (0.1, 0.5)                                      # familles impaires C6
J_ODD = (1, 3)                                          # familles impaires C6
W1_ADI = (1.0, 2.0)                                     # adiabatique C7/C8
K_ADI = (0.1, 0.2, 0.3)                                 # adiabatique C7/C8
A_ADI = 0.1                                             # adiabatique C7/C8
BAS_ADI, HAUT_ADI = 0.95, 1.05                          # barre C7/C8

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


def apply_loop1(psi):
    """L₁[ψ] — boucle α=1, poids LG1 = WG1² (route FFT, poids unique)."""
    return np.fft.ifft(LG1 * np.fft.fft(psi))

# ----------------------------------------------------------------------------
# I4 — somme de Bessel pures (route O7 uniquement — AUCUNE forme close ici)
# ----------------------------------------------------------------------------
def bessel_sums(j, a, M):
    """Sommes pures mesurées sur les paires résonnantes n = m+j, |n| ≤ M :
    S = Σ m(m+j)·JJ ; A = Σ m²(m+j)·JJ ; V = Σ m(m+j)²·JJ ; W = Σ m²(m+j)²·JJ.
    Ce sont LES OBJETS FALSIFIÉS de C3 — aucune identité n'est codée ici."""
    t = {n: j_signed(n, a) for n in range(-M, M + 1)}
    rg = [m for m in range(-M, M + 1) if abs(m + j) <= M]
    s = sum(m * (m + j) * t[m + j] * t[m] for m in rg)
    aa = sum(m * m * (m + j) * t[m + j] * t[m] for m in rg)
    vv = sum(m * (m + j) ** 2 * t[m + j] * t[m] for m in rg)
    ww = sum(m * m * (m + j) ** 2 * t[m + j] * t[m] for m in rg)
    return s, aa, vv, ww


def jtab(a, M=TRUNC_I4):
    return {n: j_signed(n, a) for n in range(-M, M + 1)}


# ----------------------------------------------------------------------------
# I4 — défauts de jauge et couplage (routes machine — FFT, poids unique)
# ----------------------------------------------------------------------------
def defauts(w1, k1, w2, k2, a, apply_op):
    """Défauts de jauge des deux canaux : δ_i = A[e^{iθ_i}ψ_i] − e^{iθ_i}A[ψ_i]."""
    psi1 = carrier(w1)
    psi2 = carrier(w2)
    th1 = a * np.cos(k1 * X)
    th2 = a * np.cos(k2 * X)
    l1 = apply_op(psi1)
    l2 = apply_op(psi2)
    d1 = apply_op(np.exp(1j * th1) * psi1) - np.exp(1j * th1) * l1
    d2 = apply_op(np.exp(1j * th2) * psi2) - np.exp(1j * th2) * l2
    return d1, d2


def i12_reseau(w1, k1, w2, k2, a, apply_op):
    """I₁₂ réseau = Re⟨δ₁,δ₂⟩ — graine INTERACTION (route FFT, poids unique)."""
    d1, d2 = defauts(w1, k1, w2, k2, a, apply_op)
    return inner(d1, d2).real


# ----------------------------------------------------------------------------
# I4 — forme close Δₙ^loop(α=1) LUE dans le poids (polynôme exact, tout k)
# ----------------------------------------------------------------------------
def delta_loop1(w, n, k):
    """Δₙ^loop(ω) = λ_loop(ω+nk) − λ_loop(ω) à α=1 — lu dans loop_weight ;
    à α=1 : −(ω+nk)²+ω² = −2ωnk−(nk)² (polynôme exact, aucun reste)."""
    return complex(loop_weight(w + n * k, 1.0) - loop_weight(w, 1.0))


def zj_alpha1(j, w1, k1, w2, k2, a, M=TRUNC_I4):
    """Z_j^loop(α=1) = Σ_m J_{m+j}J_m·conj(Δ_{m+j}(ω₁))·Δ_m(ω₂) — paires
    résonnantes n = m+j (forme close §0-bis INTERACTION, route poids)."""
    t = jtab(a, M)
    total = 0.0 + 0.0j
    for m in range(-M, M + 1):
        n = m + j
        if abs(n) > M:
            continue
        total += t[n] * t[m] * np.conj(delta_loop1(w1, n, k1)) * delta_loop1(w2, m, k2)
    return total


def forme_z2(a, k, w1, w2):
    """PRÉDICTION falsifiée (Q2) : Z₂ = k²[4ω₁ω₂·S₂ + 2k(ω₁A₂ + ω₂V₂) + k²W₂]
    avec les sommes MESURÉES (bessel_sums) — le ¼ n'apparaît que via C3,
    jamais dans cette route. Développée : (a²k²/4)[4ω₁ω₂+2k(ω₂−ω₁)+k²(a²−1)]."""
    s2, a2, v2, w2s = bessel_sums(2, a, TRUNC_I4)
    return k * k * (4.0 * w1 * w2 * s2 + 2.0 * k * (w1 * a2 + w2 * v2) + k * k * w2s)


# ----------------------------------------------------------------------------
# I4 — leads adiabatiques Q5 (route FALSIFIÉE — dérivées analytiques du poids)
# ----------------------------------------------------------------------------
def cpow(w, b):
    """(iω)^b scalaire, branche principale — MÊME branche que lambda_weight
    (route d'évaluation pour les dérivées falsifiées, pas un second poids)."""
    s = 1.0 if w >= 0 else -1.0
    ph = s * math.pi * b / 2.0
    return abs(w) ** b * complex(math.cos(ph), math.sin(ph))


def lam_prime(w, al):
    """λ′(ω) = iα(iω)^{α−1} — dérivée analytique du poids mère."""
    return 1j * al * cpow(w, al - 1)


def kd_an(w):
    """K̂′(ω) = −φ·λ′/(λ+φ)² (α=1/φ) — lead falsifié C7 uniquement."""
    lam = cpow(w, ALPHA)
    return -PHI * lam_prime(w, ALPHA) / (lam + PHI) ** 2


def ld_an(w):
    """L′(ω) = 2λλ′ (dérivée de λ_loop = λ², α=1/φ) — lead falsifié C8."""
    lam = cpow(w, ALPHA)
    return 2.0 * lam * lam_prime(w, ALPHA)

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
    """mtime(FRONTIERE_I4) < heure d'exécution — antériorité du cahier des charges."""
    front = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "FRONTIERE_I4_V0.md")
    mt = os.path.getmtime(front)
    t_exec = time.time()
    RESULTATS["depots"]["c0a"] = {
        "frontiere_mtime": mt, "exec_time": t_exec,
        "anteriorite_s": t_exec - mt,
        "frontiere_iso": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mt)),
        "exec_iso": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t_exec)),
        "provenance": "commit 459b5ba (frontière gelée avant tout script)",
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
    """(a) série × récurrence (+ parité J₋ₙ) ; (b) identité paire J₀+2ΣJ₂ₖ=1."""
    pire_a = 0.0
    for a in (0.1, 0.2):
        rec = j_recurrence(a)
        for n in range(0, TRUNC_I4 + 1):
            pire_a = max(pire_a, abs(j_serie(n, a) - rec[n]))
            pire_a = max(pire_a, abs(j_signed(-n, a) - ((-1.0) ** n) * rec[n]))
    ok_a = pire_a <= TOL_C2A
    pire_b = 0.0
    for a in (0.1, 0.2):
        s = j_serie(0, a) + 2.0 * sum(j_serie(2 * k, a) for k in range(1, 16))
        pire_b = max(pire_b, abs(s - 1.0))
    ok_b = pire_b <= TOL_C2B
    return (ok_a and ok_b), pire_a, pire_b


def c3_identites_quart():
    """Identités Q1 (le ¼ vit dans la famille paire) — sommes MESURÉES vs
    valeurs closes, 5 valeurs de a. Les valeurs closes ne vivent qu'ICI
    (contrôle d'identité) — jamais dans une route de couplage."""
    cles = {"S2": lambda a: (bessel_sums(2, a, M_ID)[0], a * a / 4.0),
            "A2": lambda a: (bessel_sums(2, a, M_ID)[1], -a * a / 4.0),
            "V2": lambda a: (bessel_sums(2, a, M_ID)[2], a * a / 4.0),
            "W2": lambda a: (bessel_sums(2, a, M_ID)[3], (a ** 4 - a * a) / 4.0),
            "S1": lambda a: (bessel_sums(1, a, M_ID)[0], 0.0),
            "S3": lambda a: (bessel_sums(3, a, M_ID)[0], 0.0),
            "W1": lambda a: (bessel_sums(1, a, M_ID)[3], 0.0)}
    pire = 0.0
    depot = {}
    for a in A_ID:
        ligne = {}
        for nom, f in cles.items():
            mes, ferme = f(a)
            ecart = abs(mes - ferme)
            pire = max(pire, ecart)
            ligne[nom] = {"mesure": mes, "close": ferme, "ecart": ecart}
        depot[str(a)] = ligne
    RESULTATS["depots"]["identites_quart"] = depot
    return pire <= TOL_C3, pire


def c4_formulaire_z2():
    """Formulaire Q2 : Z₂^zj(α=1, route poids) vs forme close (sommes MESURÉES)
    — 48 lignes (a ∈ A_SET, k ∈ K_SET, ω₁ ∈ W1_SET, ω₂ = ω₁+2k)."""
    pire = 0.0
    for a in A_SET:
        for k in K_SET:
            for w1 in W1_SET:
                w2 = w1 + 2.0 * k
                zj = zj_alpha1(2, w1, k, w2, k, a)
                zf = forme_z2(a, k, w1, w2)
                pire = max(pire, rel(zj, zf))
    return pire <= TOL_C4, pire


def c5_reseau_vs_forme():
    """Réseau vs forme : Re⟨δ₁,δ₂⟩ (route FFT, LG1) = −forme/N — 48 lignes.
    Le pont /N est la leçon V1.2 (norme vs amplitude), 3e occurrence."""
    pire = 0.0
    for a in A_SET:
        for k in K_SET:
            for w1 in W1_SET:
                w2 = w1 + 2.0 * k
                i12 = i12_reseau(w1, k, w2, k, a, apply_loop1)
                ref = -forme_z2(a, k, w1, w2).real / N
                pire = max(pire, rel(i12, ref))
    return pire <= TOL_C5, pire


def c6_silence_impaire():
    """Silence Q3 : familles impaires (j=1,3) exactement muettes à α=1 —
    |Re I₁₂| ≤ barre sur 8 lignes (le couplage est purement quadratique)."""
    pire = 0.0
    for j in J_ODD:
        for a in A_ODD:
            for k in K_ODD:
                w1 = 1.0
                w2 = w1 + j * k
                i12 = i12_reseau(w1, k, w2, k, a, apply_loop1)
                pire = max(pire, abs(i12))
    return pire <= TOL_C6, pire


def c7_adiabatique_noyau():
    """Adiabatique noyau Q5 : ratio I₁₂/(−k²S₂·Re[conj K̂′(ω₁)]·K̂′(ω₂)/N)
    — lead conjugué (conjugaison sur canal 1), pont /N (leçon V1.2 : le lead
    prédit Z₂ au niveau amplitude, le réseau mesure au niveau norme)."""
    pire_hors = 0.0
    ratios = {}
    s2m = bessel_sums(2, A_ADI, TRUNC_I4)[0]
    for w1 in W1_ADI:
        for k in K_ADI:
            w2 = w1 + 2.0 * k
            i12 = i12_reseau(w1, k, w2, k, A_ADI, apply_kernel)
            lead = s2m * (np.conj(kd_an(w1)) * kd_an(w2)).real * k * k
            r = i12 / (-lead / N)
            ratios[f"w1={w1},k={k}"] = r
            pire_hors = max(pire_hors, abs(r - 1.0))
    ok = all(BAS_ADI <= r <= HAUT_ADI for r in ratios.values())
    RESULTATS["depots"]["ratios_c7"] = {k: float(v) for k, v in ratios.items()}
    return ok, pire_hors, ratios


def c8_adiabatique_boucle():
    """Adiabatique boucle α=1/φ Q5 : ratio I₁₂/(−k²S₂·Re[conj L′(ω₁)]·L′(ω₂)/N)
    — lead conjugué, pont /N (leçon V1.2), route réseau FFT (poids LG)."""
    pire_hors = 0.0
    ratios = {}
    s2m = bessel_sums(2, A_ADI, TRUNC_I4)[0]
    for w1 in W1_ADI:
        for k in K_ADI:
            w2 = w1 + 2.0 * k
            i12 = i12_reseau(w1, k, w2, k, A_ADI, apply_loop)
            lead = s2m * (np.conj(ld_an(w1)) * ld_an(w2)).real * k * k
            r = i12 / (-lead / N)
            ratios[f"w1={w1},k={k}"] = r
            pire_hors = max(pire_hors, abs(r - 1.0))
    ok = all(BAS_ADI <= r <= HAUT_ADI for r in ratios.values())
    RESULTATS["depots"]["ratios_c8"] = {k: float(v) for k, v in ratios.items()}
    return ok, pire_hors, ratios


def c9_no_wrap():
    """|ω ± nk| ≤ Nyquist pour toute lecture (grilles C4/C5, D1, C6, C7/C8)."""
    familles = []
    for k in K_SET:
        for w1 in W1_SET:
            familles.append((w1, k, w1 + 2.0 * k))
    for k in K_D1:
        for w1 in W1_D1:
            familles.append((w1, k, w1 + 2.0 * k))
    for j in J_ODD:
        for k in K_ODD:
            familles.append((1.0, k, 1.0 + j * k))
    for k in K_ADI:
        for w1 in W1_ADI:
            familles.append((w1, k, w1 + 2.0 * k))
    pire = 0.0
    for (w1, k, w2) in familles:
        for n in range(-TRUNC_I4, TRUNC_I4 + 1):
            pire = max(pire, abs(w1 + n * k), abs(w2 + n * k))
    RESULTATS["depots"]["c9_pire_argument"] = pire
    return pire <= NYQUIST, pire


def c10_filiation():
    """λ_loop = λ_kernel² bit-exact — grille O3 (α=1/φ et α=1) + set scalaires
    I4 ; un seul poids spectral dans le code (structurel, anti-rétro)."""
    ok_grid = bool(np.array_equal(LG, WG * WG)) and bool(np.array_equal(LG1, WG1 * WG1))
    pts = [0.5, 1.0, 1.3, 2.0, 3.0, 4.0, 22.0]
    ok_pts = True
    for w in pts:
        for al in (ALPHA, 1.0):
            lw = loop_weight(w, al)
            lw2 = lambda_weight(w, al) * lambda_weight(w, al)
            ok_pts = ok_pts and lw == lw2
    return (ok_grid and ok_pts), ok_grid, ok_pts


# ----------------------------------------------------------------------------
# CONSÉQUENCES FALSIFIABLES (frontière §4)
# ----------------------------------------------------------------------------
def d1a_montee_exacte():
    """D1a — montée exacte : I₁₂/(−𝔽₁𝔽₂/N) = 1 + k²(a²+3)/(4ω₁ω₂), 8 lignes.
    𝔽_i = a·k·ω_i (force du mode de jauge sur le porteur) — définition Q4."""
    pire = 0.0
    lignes = {}
    for a in A_D1:
        for k in K_D1:
            for w1 in W1_D1:
                w2 = w1 + 2.0 * k
                i12 = i12_reseau(w1, k, w2, k, a, apply_loop1)
                f1 = a * k * w1
                f2 = a * k * w2
                r = i12 / (-f1 * f2 / N)
                pred = 1.0 + k * k * (a * a + 3.0) / (4.0 * w1 * w2)
                e = rel(r, pred)
                pire = max(pire, e)
                lignes[f"a={a},k={k},w1={w1}"] = {"ratio": r, "pred": pred, "rel": e}
    RESULTATS["depots"]["d1a_lignes"] = lignes
    return pire <= TOL_D1, pire


def d1b_forme_famille():
    """D1b — forme famille : I₁₂ = −(a²k²/4N)[4ω₁ω₂ + k²(a²+3)]. La forme
    close (avec le ¼) est la PRÉDICTION falsifiée — la route réseau ne
    contient aucun ¼ ; le pont C3 (identité mesurée) la légitime."""
    pire = 0.0
    lignes = {}
    for a in A_D1:
        for k in K_D1:
            for w1 in W1_D1:
                w2 = w1 + 2.0 * k
                i12 = i12_reseau(w1, k, w2, k, a, apply_loop1)
                pred = -(a * a * k * k / 4.0) * (4.0 * w1 * w2 + k * k * (a * a + 3.0)) / N
                e = rel(i12, pred)
                pire = max(pire, e)
                lignes[f"a={a},k={k},w1={w1}"] = {"i12": i12, "pred": pred, "rel": e}
    RESULTATS["depots"]["d1b_lignes"] = lignes
    return pire <= TOL_D1, pire


def d1c_limite_adiabatique():
    """D1c — limite adiabatique : ratio I₁₂/(−𝔽₁𝔽₂/N) ∈ [0.95, 1.10] à k ≤ 0.2
    (bande gelée D1c, frontière §4 — DISTINCTE de la bande C7/C8 [0.95, 1.05] ;
    écart maximal mesuré aux sondes : 8.9e-2 à k=0.2, ω₁=0.5)."""
    pire_hors = 0.0
    lignes = {}
    for a in A_D1:
        for k in K_D1:
            for w1 in W1_D1:
                w2 = w1 + 2.0 * k
                i12 = i12_reseau(w1, k, w2, k, a, apply_loop1)
                f1 = a * k * w1
                f2 = a * k * w2
                r = i12 / (-f1 * f2 / N)
                lignes[f"a={a},k={k},w1={w1}"] = r
                pire_hors = max(pire_hors, abs(r - 1.0))
    ok = all(TOL_D1C_BAS <= r <= TOL_D1C_HAUT for r in lignes.values())
    RESULTATS["depots"]["d1c_ratios"] = {k: float(v) for k, v in lignes.items()}
    return ok, pire_hors


def d2a_structure_paire():
    """D2a — les familles impaires sont exactement muettes (= C6) : le
    couplage est purement quadratique — signature −¼F², pas −F."""
    return c6_silence_impaire()


def d2b_canal_orthogonal():
    """[OBS] D2b — les parties Im⟨δ₁,δ₂⟩ des familles impaires : à α=1, Z_j
    réel ⟹ ⟨δ₁,δ₂⟩ = i^{−j}Z_j/N est imaginaire pur, Im⟨δ₁,δ₂⟩ =
    −sin(πj/2)·Re Z_j/N ≠ 0 (j=1 → −Re Z₁/N ; j=3 → +Re Z₃/N) : canal
    orthogonal, non-observable dans I₁₂."""
    lignes = {}
    for j in J_ODD:
        for a in A_ODD:
            for k in K_ODD:
                w1 = 1.0
                w2 = w1 + j * k
                d1, d2 = defauts(w1, k, w2, k, a, apply_loop1)
                im = inner(d1, d2).imag
                zj = zj_alpha1(j, w1, k, w2, k, a)
                pred = -math.sin(math.pi * j / 2.0) * zj.real / N
                lignes[f"j={j},a={a},k={k}"] = {
                    "im_reseau": im, "pred_im": pred,
                    "rel": rel(im, pred)}
    obs("d2b_canal_orthogonal", lignes,
        "Im⟨δ₁,δ₂⟩ = −sin(πj/2)·Re Z_j/N ≠ 0 — non-observable I₁₂ (frontière §4 D2b)")


def d3a_montee_generique():
    """D3a — noyau et boucle α=1/φ : le ratio adiabatique tend vers 1
    (= C7 ET C8) — la structure conj(W′₁)W′₂ tient hors α=1."""
    ok_c7, _, _ = c7_adiabatique_noyau()
    ok_c8, _, _ = c8_adiabatique_boucle()
    return ok_c7 and ok_c8


def d3b_pas_de_formulaire_hors_alpha1():
    """[OBS] D3b — le ratio C7/C8 s'écarte de 1 à k fini : pas de formulaire
    polynomial hors α=1 — la fermeture −¼F² est la tranche α=1."""
    ecart_max = 0.0
    for dep in ("ratios_c7", "ratios_c8"):
        for r in RESULTATS["depots"][dep].values():
            ecart_max = max(ecart_max, abs(r - 1.0))
    obs("d3b_pas_de_formule_hors_alpha1", ecart_max,
        "écart max |ratio−1| à k=0.3 — mémoire α=1/φ ne ferme pas en formulaire")


def obs_pont_norme():
    """[OBS] pont /N (leçon V1.2, 3e occurrence) : réseau = forme close ÷ N."""
    a, k, w1 = 0.1, 0.1, 1.0
    w2 = w1 + 2.0 * k
    i12 = i12_reseau(w1, k, w2, k, a, apply_loop1)
    z = zj_alpha1(2, w1, k, w2, k, a)
    zf = forme_z2(a, k, w1, w2)
    obs("pont_norme_N", {
        "i12_reseau": i12, "-re_zj": -z.real, "-re_zj_sur_n": -z.real / N,
        "forme_close": zf, "rapport_reseau_forme": i12 / (-z.real),
        "un_sur_n": 1.0 / N},
        "I₁₂^réseau = −Re Z₂/N — pont amplitude→norme structurel (V1.2)")


# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------
def main():
    t0 = time.time()
    print("=" * 78)
    print("I4 V0 — la montée vers −¼F² : le ¼ sort des identités de Bessel")
    print("=" * 78)

    # ---- contrôles bloquants (frontière §3) ---------------------------------
    print("\n-- Contrôles bloquants --")
    ok_c0a = controle("C0a", c0a_frontiere(), "mtime < exec", "—")
    e0b = abs(PHI * PHI - (PHI + 1.0))
    ok_c0b = controle("C0b", e0b <= TOL_C0B, e0b, TOL_C0B)
    ok_c1_v, c1v, c1br = c1_noyau_double_route()
    ok_c1 = controle("C1", ok_c1_v, max(c1v, c1br), TOL_C1)
    ok_c2_v, c2a, c2b = c2_bessel_double_route()
    ok_c2 = controle("C2", ok_c2_v, [c2a, c2b], f"{TOL_C2A}/{TOL_C2B}")
    ok_c3_v, c3v = c3_identites_quart()
    ok_c3 = controle("C3", ok_c3_v, c3v, TOL_C3, "identités Q1 : le ¼ vit dans j=2")
    ok_c4_v, c4v = c4_formulaire_z2()
    ok_c4 = controle("C4", ok_c4_v, c4v, TOL_C4, "Z₂ zj vs forme (sommes mesurées), 48 lignes")
    ok_c5_v, c5v = c5_reseau_vs_forme()
    ok_c5 = controle("C5", ok_c5_v, c5v, TOL_C5, "réseau = −forme/N, 48 lignes")
    ok_c6_v, c6v = c6_silence_impaire()
    ok_c6 = controle("C6", ok_c6_v, c6v, TOL_C6, "silence impaire j=1,3, 8 lignes")
    ok_c7_v, c7v, _ = c7_adiabatique_noyau()
    ok_c7 = controle("C7", ok_c7_v, c7v, "[0.95, 1.05]", "ratio adiabatique noyau, 6 lignes")
    ok_c8_v, c8v, _ = c8_adiabatique_boucle()
    ok_c8 = controle("C8", ok_c8_v, c8v, "[0.95, 1.05]", "ratio boucle 1/φ, 6 lignes")
    ok_c9_v, c9v = c9_no_wrap()
    ok_c9 = controle("C9", ok_c9_v, c9v, f"≤ {NYQUIST}", "no-wrap grille I4")
    ok_c10_v, c10g, c10p = c10_filiation()
    ok_c10 = controle("C10", ok_c10_v, [c10g, c10p], "0 (bit-exact)",
                      "filiation λ_loop=λ_kernel², poids unique")

    controles_ok = all([ok_c0a, ok_c0b, ok_c1, ok_c2, ok_c3, ok_c4, ok_c5,
                        ok_c6, ok_c7, ok_c8, ok_c9, ok_c10])

    # ---- conséquences (frontière §4) ----------------------------------------
    print("\n-- Conséquences falsifiables --")
    ok_d1a_v, d1av = d1a_montee_exacte()
    ok_d1a = lecture("D1a_montee_exacte", ok_d1a_v, d1av, TOL_D1,
                     "I₁₂/(−𝔽₁𝔽₂/N) = 1 + k²(a²+3)/(4ω₁ω₂), 8 lignes")
    ok_d1b_v, d1bv = d1b_forme_famille()
    ok_d1b = lecture("D1b_forme_famille", ok_d1b_v, d1bv, TOL_D1,
                     "I₁₂ = −(a²k²/4N)[4ω₁ω₂ + k²(a²+3)]")
    ok_d1c_v, d1cv = d1c_limite_adiabatique()
    ok_d1c = lecture("D1c_limite_adiabatique", ok_d1c_v, d1cv,
                     f"[{BAS_ADI}, {HAUT_ADI}]", "ratio → 1 à k ≤ 0.2, 8 lignes")
    ok_d2a_v, d2av = d2a_structure_paire()
    ok_d2a = lecture("D2a_structure_paire", ok_d2a_v, d2av, TOL_C6,
                     "impaire muette ⟹ couplage quadratique (−¼F², pas −F)")
    d2b_canal_orthogonal()
    ok_d3a = lecture("D3a_montee_generique", ok_c7 and ok_c8, [c7v, c8v],
                     "[0.95, 1.05]", "noyau + boucle 1/φ : lead conjugué tient")
    d3b_pas_de_formulaire_hors_alpha1()
    obs_pont_norme()

    d1_ok = ok_d1a and ok_d1b and ok_d1c

    # ---- verdict (échelle §5 gelée) -----------------------------------------
    duree = time.time() - t0
    if not controles_ok:
        verdict, code = "V4_REFUTE", 1
    elif d1_ok and ok_d2a and ok_d3a:
        verdict, code = "V+_I4_MONTEE_QUART_FERMEE", 0
    elif d1_ok:
        verdict, code = "V2_I4_QUART_SEUL", 0
    else:
        verdict, code = "V3_REFUTE_I4_SANS_QUART", 1

    RESULTATS["meta"] = {
        "verdict": verdict, "exit_code": code, "echecs": ECHECS,
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "python": sys.version.split()[0], "numpy": np.__version__,
        "duree_s": round(duree, 2),
        "c0a": RESULTATS["depots"].get("c0a", {}),
        "autorite": "FRONTIERE_I4_V0.md (commit 459b5ba, gelée avant tout script)",
        "entrees": ["FRONTIERE_I4_V0.md", "OUVERTURE_D3_DYNAMIQUE_V0.md (§6.2)",
                    "DEPOT_INTERACTION_D3_V0.md (§5 : graine ≠ −¼F²)",
                    "RESULTAT_INTERACTION_D3_V0.md (I₁₂ = Re[i^{−j}Z_j]/N)",
                    "leçon V1.2 (pont norme /N — 3e occurrence)"],
        "routes": "FFT (poids (iω)^α, branche principale) pour noyau et boucle "
                  "(α=1 via LG1=WG1², α=1/φ via LG=WG²) ; série de Bessel O7 pour "
                  "les sommes et Z_j ; forme close Δₙ^loop(α=1) lue dans le poids ; "
                  "dérivées analytiques pour les leads Q5 (objet falsifié) ; un seul "
                  "poids spectral dans le code (C10) — aucun ¼ dans la route machine",
    }
    print("\n" + "=" * 78)
    print(f"VERDICT : {verdict}   exit {code}")
    if ECHECS:
        print("Échecs consignés : " + "; ".join(ECHECS))
    print("=" * 78)

    out_json = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "resultat_i4_v0.json")

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
