# -*- coding: utf-8 -*-
"""
FORCE V1.3 — exécution machine du dépôt DEPOT_FORCE_V1_3.md (28/08/2026, 16:57:46)

Physique + témoin (a)/(b) VERBATIM de V1.2 ; unique changement déposé : la barre (c)
passe de 1e23 (estimation mentale fausse de V1.2) à 1e100 (calculée par machine avant
gel : J₀_brut = 1.765841e+74 à a=0.1, 8.222839e+64 à a=0.2 — aucun débordement).

Le dépôt est FERMÉ et ANTÉRIEUR à ce script (contrôle C0a : mtime dépôt < mtime exécution).
Aucune lecture, barre ou verdict n'est modifiable ici — ce script ne fait qu'exécuter :

  Hypothèse [H] (dépôt §0) : le défaut de commutation du noyau K̂ est EXACTEMENT la
  diffusion fréquentielle de Jacobi–Anger × action diagonale, forme close sans paramètre :
    χ(ω₀,a,k) = √( Σ_{n≥1} Jₙ(a)²·(|K̂(ω₀+nk)−K̂(ω₀)|² + |K̂(ω₀−nk)−K̂(ω₀)|²) ) / (a·|K̂(ω₀)|)

  Famille A (forme close)  : 14 porteurs (Fibonacci×0,1 ∪ V0) @1e-9, dérive a=0,2 prédite,
                             gradient k ∈ {0.5, 2.0} prédit, G* reproduit @1e-8,
                             station argmax = ω₀ = 1,0 (verdict-porteuse)
  Famille B (fermeture)    : balayage composé {G*·c, G*/c, c/G*} vs registre ∪ {√2, π, e}
                             — lecture [OBS] SANS pouvoir de verdict (comparaisons multiples)
  Famille C (diagnostics)  : β_inf, β_sup, χ·ω₀ — trou D4 ouvert, aucun verdict

  Contrôles bloquants C0a…C7 (dépôt §3) — UN SEUL en échec ⟹ V4 REFUTE exit 1.

  Verdicts (dépôt §4) :
    V+  FORCE_FORME_FERMEE        (17/17 @1e-9 + G* @1e-8 + argmax = 1,0)     exit 0
    V2  FORCE_FORME_PARTIELLE     (forme OK, argmax ≠ 1,0)                    exit 0
    V3  REFUTE_FORCE_SANS_FORME   (≥ 1 lecture forme > 1e-9, G* compris)      exit 1
    V4  REFUTE                    (un contrôle bloquant en échec)             exit 1

Objets fermés O1–O10, interdictions I1–I5, honnêteté §6 : voir le dépôt.
Sortie : resultat_force_v1_3.json (toutes les lectures, y compris les quasi-échecs).
"""

import cmath
import json
import math
import os
import sys
import time

import numpy as np

# ================================================================== O1–O10 — objets fermés
PHI = (1.0 + math.sqrt(5.0)) / 2.0          # O1
ALPHA = 1.0 / PHI

N = 512                                      # O3
L = 20.0 * math.pi
D_OMEGA = 2.0 * math.pi / L                  # 0,1 — tous les modes sur bins entiers
NYQUIST = (N / 2) * D_OMEGA                  # 25,6

LEG_A = 0.4011522499939087                   # O4 — registre 27/08
IMPEDANCE = 2.492819122951908                # O4
D2_REGISTRE = 0.54518249                     # O4
ANCRE = 137.036031356                        # O4
CODATA = 137.035999177                       # O4
FACTEUR_OBS = 1.8324104102898406             # O4 — [OBS] 28/08
G_STAR = 0.3232880100102466                  # O9 — 17ᵉ objet (jaugage V0, 28/08)

TOL_FORME = 1.0e-9                           # O8 — famille A (relatif)
TOL_GSTAR = 1.0e-8                           # O8 — A4/C5
TOL_HIT = 1.0e-4                             # O8 — fermeture géométrique
TOL_HIT_PLUS = 2.355e-7                      # O8 — continuité
TOL_U1 = 1.0e-9                              # O8 — C6
TOL_C0B = 1.0e-15
TOL_C = 1.0e-12                              # O8 — contrôles C1–C4

PORTEURS = [0.1, 0.2, 0.3, 0.5, 0.8, 1.0, 1.3, 2.0, 2.1, 3.4, 5.5, 8.9, 10.0, 14.4]  # O6
N_TRUNC = 11                                 # O6/O7 — J₁₂(0,1) ≈ 5e-25, invisible
A_SWEEP = 0.1                                # O10
K_SWEEP = 1.0
A_DRIFT = 0.2                                # O10 — A2 (la dérive prédite)
K_GRID_A = [0.5, 2.0]                        # O10 — A3 (le gradient prédit)
THETAS = [math.pi / 3.0, math.pi / 2.0]      # C6 — angles arbitraires (I1)

RACINE = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.join(RACINE, "DEPOT_FORCE_V1_3.md")
SORTIE = os.path.join(RACINE, "resultat_force_v1_3.json")

t_debut = time.time()
controles = []
famille_A = []       # 17 lectures forme close
famille_B = []       # balayage composé [OBS]


def controle(nom, ok, detail):
    controles.append({"controle": nom, "ok": bool(ok), "detail": detail})
    print(f"  [{'OK ' if ok else 'ÉCHEC'}] {nom} : {detail}")
    return bool(ok)


def note(nom, detail):
    print(f"  [   ] {nom} : {detail}")


# ================================================================== noyau (O2 — verbatim jaugage V0)
def Khat(omega):
    """K̂(ω) = φ/((iω)^α + φ) — route complexe, branche principale. K̂(0) = 1."""
    if omega == 0.0:
        return complex(1.0, 0.0)
    z = 1j * omega
    return PHI / (cmath.exp(ALPHA * cmath.log(z)) + PHI)


def Khat_real(omega):
    """K̂ forme réelle développée (phase incluse) — route indépendante pour C1."""
    if omega == 0.0:
        return complex(1.0, 0.0)
    w = abs(omega)
    s = 1.0 if omega > 0.0 else -1.0
    wa = w ** ALPHA
    den = PHI + wa * math.cos(math.pi * ALPHA / 2.0) \
        + 1j * s * wa * math.sin(math.pi * ALPHA / 2.0)
    return PHI / den


# ================================================================== treillis (O3, O5)
m_bins = np.arange(N)
omega_grid = np.where(m_bins <= N // 2, m_bins, m_bins - N).astype(float) * D_OMEGA
x = np.arange(N) * (L / N)

KHAT_W = np.array([Khat(w) for w in omega_grid])


def norme(v):
    """O5 — norme unitaire ‖ψ‖² = Σ|ψₙ|²/N (Parseval)."""
    return math.sqrt(float(np.sum(np.abs(v) ** 2)) / N)


def applique_noyau(psi):
    """K̂[ψ] = IFFT(K̂(ω)·FFT(ψ)) — filtre fréquentiel, convention numpy 1/N incluse."""
    return np.fft.ifft(KHAT_W * np.fft.fft(psi))


def defaut(alpha_x, psi, k_psi):
    """Jaugage V0 cloné verbatim — D = ‖K̂[e^{iα}ψ] − e^{iα}·K̂[ψ]‖ / ‖K̂[ψ]‖."""
    eia = np.exp(1j * alpha_x)
    return norme(applique_noyau(eia * psi) - eia * k_psi) / norme(k_psi)


# ================================================================== O7 — Bessel (deux routes)
def bessel_J(n, a):
    """O7 — Jₙ(a) par série Jₙ = Σ_m (−1)ᵐ (a/2)^{2m+n}/(m!(m+n)!)."""
    h = a / 2.0
    t = h ** n / math.factorial(n)
    s = t
    sign = -1.0
    m = 0
    while abs(t) > 1.0e-32 and m < 300:
        m += 1
        t *= (h * h) / (m * (m + n))
        s += sign * t
        sign = -sign
    return s


def bessel_table_recurrence(n_max, a):
    """Route indépendante C2′ (verbatim V1.1) — Miller descendant Jₙ₋₁ = (2n/a)Jₙ − Jₙ₊₁,
    amorce d'ordre 1, facteur de normalisation figé AVANT toute mutation de la table.
    Changement déposé V1.2 (c) : retourne (table, J₀_brut) où J₀_brut est la valeur
    AVANT normalisation (V1.1 enregistrait à tort la valeur post-normalisation)."""
    J = {n_max + 1: 0.0, n_max: 1.0}
    for n in range(n_max, 0, -1):
        J[n - 1] = (2.0 * n / a) * J[n] - J[n + 1]
    J0_brut = J[0]  # valeur brute avant normalisation — déposé V1.2 (c)
    facteur = bessel_J(0, a) / J[0]  # figé AVANT mutation — le correctif déposé V1.1
    for n in range(0, n_max + 1):
        J[n] *= facteur
    return J, J0_brut


# ================================================================== §0 — la forme close
def chi_pred(w0, a, k):
    """Dépôt §0 — χ(ω₀,a,k) = √(Σₙ Jₙ²(|Δ₊|²+|Δ₋|²))/(a|K̂(ω₀)|), fréquences signées."""
    K0 = Khat(w0)
    s = 0.0
    for n in range(1, N_TRUNC + 1):
        Jn = bessel_J(n, a)
        d_p = abs(Khat(w0 + n * k) - K0) ** 2
        d_m = abs(Khat(w0 - n * k) - K0) ** 2
        s += Jn * Jn * (d_p + d_m)
    return math.sqrt(s) / (a * abs(K0))


def chi_machine(w0, a, k):
    """Voie machine (verbatim jaugage V0) : χ = D(a·cos(kx))/a sur le porteur e^{iω₀x}."""
    psi = np.exp(1j * w0 * x) / math.sqrt(N)
    kpsi = applique_noyau(psi)
    return defaut(a * np.cos(k * x), psi, kpsi) / a


# ================================================================== T0 — ANTÉRIORITÉ ET CONTRÔLES
print("=" * 74)
print("  FORCE V1.3 — barre (c) calculée par machine, fermeture du guichet 2 (dépôt du 28/08/2026)")
print("=" * 74)

mtime_depot = os.path.getmtime(DEPOT)
c0a_ok = mtime_depot < t_debut
print()
print("[CONTRÔLES BLOQUANTS — dépôt §3 : un seul échec ⟹ V4 REFUTE exit 1]")
ok_global = controle("C0a dépôt antérieur à l'exécution", c0a_ok,
                     f"mtime dépôt {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime_depot))} "
                     f"< exécution {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t_debut))}")

ec0b = abs(PHI ** 2 - (PHI + 1.0))
ok_global &= controle("C0b fermeture algébrique φ² = φ+1", ec0b < TOL_C0B, f"écart = {ec0b:.1e}")

ec1 = max(abs(Khat(w) - Khat_real(w)) for w in list(omega_grid) + [0.5, ALPHA, 1.0, 2.0])
ok_global &= controle("C1 K̂ : route complexe vs forme réelle développée "
                      "(grille O3 entière + {½, 1/φ, 1, 2})", ec1 < TOL_C, f"écart max = {ec1:.2e}")

ec2 = 0.0
S_max_dev = 0.0
J_rec0_raw_max = 0.0
for a_c2 in (A_SWEEP, A_DRIFT):
    J_rec, J0_brut = bessel_table_recurrence(N_TRUNC + 20, a_c2)
    J_rec0_raw_max = max(J_rec0_raw_max, J0_brut)  # (c) VRAI brut ∏(2n/a) ≤ 1e23
    for n in range(0, N_TRUNC + 1):
        js = bessel_J(n, a_c2)
        if abs(js) >= 1.0e-10:
            ec2 = max(ec2, abs(J_rec[n] - js) / abs(js))
    S = J_rec[0] + 2.0 * sum(J_rec[2 * k] for k in range(1, 6))  # (b) V1.2 : J₀+2ΣJ₂ₖ = 1
    S_max_dev = max(S_max_dev, abs(S - 1.0))
ok_global &= controle("C2′ Bessel double route : (a) série vs récurrence corrigée ≤ 1e-12 ; "
                      "(b) identité PAIRE J₀+2ΣJ₂ₖ = 1 ≤ 1e-9 (parité J₋ₙ=(−1)ⁿJₙ, dépôt V1.2 §0) ; "
                      "(c) J₀ brut ∏(2n/a) ≤ 1e100 (calculé : 1.765841e+74 @a=0.1 — dépôt V1.3 §0)",
                      ec2 < TOL_C and S_max_dev < TOL_U1 and J_rec0_raw_max <= 1.0e100,
                      f"(a) écart max = {ec2:.2e} ; (b) max|S_pair−1| = {S_max_dev:.2e} ; "
                      f"(c) J₀ brut max = {J_rec0_raw_max:.3e}")

ec3 = 0.0
for a_c3, k_c3 in [(A_SWEEP, K_SWEEP), (A_DRIFT, K_SWEEP), (A_SWEEP, 0.5), (A_SWEEP, 2.0)]:
    Jn_c3 = {n: bessel_J(n, a_c3) for n in range(0, N_TRUNC + 1)}
    for j in range(N):
        xj = float(x[j])
        cible = cmath.exp(1j * a_c3 * math.cos(k_c3 * xj))
        somme = complex(Jn_c3[0], 0.0)
        for n in range(1, N_TRUNC + 1):
            somme += (1j ** n) * Jn_c3[n] * 2.0 * math.cos(n * k_c3 * xj)
        ec3 = max(ec3, abs(cible - somme))
ok_global &= controle("C3 Jacobi–Anger PONCTUEL sur le treillis "
                      "(4 couples (a,k), résidu max sur 512 points chacun)", ec3 < TOL_C,
                      f"écart max = {ec3:.2e}")

ec4 = 0.0
for w0_c4 in (0.1, 1.0, 14.4):
    psi_c4 = np.exp(1j * w0_c4 * x) / math.sqrt(N)
    ec4 = max(ec4, norme(applique_noyau(psi_c4) - Khat(w0_c4) * psi_c4))
ok_global &= controle("C4 action propre du noyau sur 3 porteurs {0.1, 1.0, 14.4}",
                      ec4 < TOL_C, f"‖K̂[ψ] − K̂(ω₀)ψ‖ max = {ec4:.2e}")

chi_ref = chi_machine(1.0, A_SWEEP, K_SWEEP)
ec5 = abs(chi_ref - G_STAR) / G_STAR
ok_global &= controle("C5 reproduction de la voie V0 : χ_machine(1, 0.1, 1) = G* registre O9",
                      ec5 < TOL_GSTAR,
                      f"χ_machine = {chi_ref:.16f} ; registre = {G_STAR} ; écart relatif = {ec5:.2e}")

psi0_u1 = np.exp(1j * 1.0 * x) / math.sqrt(N)
kpsi0_u1 = applique_noyau(psi0_u1)
D_ref_u1 = defaut(A_SWEEP * np.cos(K_SWEEP * x), psi0_u1, kpsi0_u1)
ec6 = max(abs(defaut(A_SWEEP * np.cos(K_SWEEP * x) + th, psi0_u1, kpsi0_u1) - D_ref_u1)
          for th in THETAS)
ok_global &= controle("C6 U(1) aveuglement spot (θ₀ ∈ {π/3, π/2}, a=0.1, k=1, ω₀=1)",
                      ec6 < TOL_U1, f"dérive max = {ec6:.2e}")

no_wrap_ok = True
for w0_c7 in PORTEURS:
    for n_c7 in range(1, N_TRUNC + 1):
        if max(abs(w0_c7 + n_c7 * K_SWEEP), abs(w0_c7 - n_c7 * K_SWEEP)) > NYQUIST:
            no_wrap_ok = False
for k_c7 in K_GRID_A:
    for n_c7 in range(1, N_TRUNC + 1):
        if max(abs(1.0 + n_c7 * k_c7), abs(1.0 - n_c7 * k_c7)) > NYQUIST:
            no_wrap_ok = False
ok_global &= controle("C7 no-wrap : |ω₀ ± n·k| ≤ Nyquist 25,6 pour toute lecture famille A "
                      "(max = 25,4 au porteur 14,4)", no_wrap_ok, "aucun mode wrapé — dépôt §3 C7")

# ================================================================== FAMILLE A — LA FORME CLOSE
print()
print("[FAMILLE A — la forme close §0 : diffusion fréquentielle du noyau (17 lectures @1e-9)]")
for w0 in PORTEURS:
    cm = chi_machine(w0, A_SWEEP, K_SWEEP)
    cp = chi_pred(w0, A_SWEEP, K_SWEEP)
    rel = abs(cm - cp) / cp
    mw = max(max(abs(w0 + n * K_SWEEP), abs(w0 - n * K_SWEEP)) for n in range(1, N_TRUNC + 1))
    famille_A.append({"lecture": f"chi({w0:g}, 0.1, 1)", "w0": w0, "a": A_SWEEP, "k": K_SWEEP,
                      "chi_machine": float(cm), "chi_pred": float(cp),
                      "ecart_relatif": float(rel), "barre": TOL_FORME,
                      "ok": bool(rel <= TOL_FORME), "max_freq": float(mw)})
    print(f"  ω₀ = {w0:5g}  χ_machine = {cm:.12f}  χ_pred = {cp:.12f}  "
          f"écart = {rel:.2e}  {'✓' if rel <= TOL_FORME else '✗ DIVERGENCE'}")

cm_drift = chi_machine(1.0, A_DRIFT, K_SWEEP)
cp_drift = chi_pred(1.0, A_DRIFT, K_SWEEP)
rel_drift = abs(cm_drift - cp_drift) / cp_drift
famille_A.append({"lecture": "chi(1, 0.2, 1)", "w0": 1.0, "a": A_DRIFT, "k": K_SWEEP,
                  "chi_machine": float(cm_drift), "chi_pred": float(cp_drift),
                  "ecart_relatif": float(rel_drift), "barre": TOL_FORME,
                  "ok": bool(rel_drift <= TOL_FORME),
                  "max_freq": float(max(max(abs(1.0 + n * K_SWEEP), abs(1.0 - n * K_SWEEP))
                                        for n in range(1, N_TRUNC + 1)))})
print(f"  A2 dérive prédite : χ_machine(1, 0.2, 1) = {cm_drift:.12f} ; "
      f"χ_pred = {cp_drift:.12f} ; écart = {rel_drift:.2e} — "
      f"la dérive V0 (barre 5 %) devient une prédiction exacte")

for k_a3 in K_GRID_A:
    cm_k = chi_machine(1.0, A_SWEEP, k_a3)
    cp_k = chi_pred(1.0, A_SWEEP, k_a3)
    rel_k = abs(cm_k - cp_k) / cp_k
    famille_A.append({"lecture": f"chi(1, 0.1, {k_a3:g})", "w0": 1.0, "a": A_SWEEP, "k": k_a3,
                      "chi_machine": float(cm_k), "chi_pred": float(cp_k),
                      "ecart_relatif": float(rel_k), "barre": TOL_FORME,
                      "ok": bool(rel_k <= TOL_FORME),
                      "max_freq": float(max(max(abs(1.0 + n * k_a3), abs(1.0 - n * k_a3))
                                            for n in range(1, N_TRUNC + 1)))})
    print(f"  A3 k = {k_a3:g}      : χ_machine = {cm_k:.12f}  χ_pred = {cp_k:.12f}  "
          f"écart = {rel_k:.2e}  {'✓' if rel_k <= TOL_FORME else '✗ DIVERGENCE'}")

cp_gstar = chi_pred(1.0, A_SWEEP, K_SWEEP)
ec_gstar = abs(cp_gstar - G_STAR) / G_STAR
gstar_ok = ec_gstar <= TOL_GSTAR
note("A4 G* par la forme close",
     f"χ_pred(1, 0.1, 1) = {cp_gstar:.16f} ; registre O9 = {G_STAR} ; "
     f"écart relatif = {ec_gstar:.2e} — barre {TOL_GSTAR:.0e} → "
     f"{'REPRODUIT' if gstar_ok else 'DIVERGENCE'}")

chi_sweep = [r["chi_machine"] for r in famille_A[:14]]
i_max = max(range(len(PORTEURS)), key=lambda i: chi_sweep[i])
w0_max = PORTEURS[i_max]
station_ok = (w0_max == 1.0)
note("A5 la station (verdict-porteuse)",
     f"argmax χ sur la grille O6 = ω₀ = {w0_max} (χ = {chi_sweep[i_max]:.12f}) — "
     f"déposé : ω₀ = 1.0 → {'CONFIRMÉ' if station_ok else 'STATION DÉPLACÉE (V2, consignée)'}")

# ================================================================== FAMILLE B — FERMETURE COMPOSÉE ([OBS])
registre = [("D₂", D2_REGISTRE), ("|K̃(½)|²", LEG_A), ("impédance", IMPEDANCE),
            ("φ", PHI), ("φ²", PHI ** 2), ("1/φ", ALPHA), ("√5", math.sqrt(5.0)),
            ("2φ", 2.0 * PHI), ("2", 2.0), ("5", 5.0), ("1/5", 0.2),
            ("F₁₀", 55.0), ("L₁₀", 123.0), ("e^{1/φ}", math.exp(ALPHA)),
            ("e^{−1/φ}", math.exp(-ALPHA)), ("ancre", ANCRE), ("1/ancre", 1.0 / ANCRE),
            ("facteur [OBS]", FACTEUR_OBS)]
cibles = registre + [("√2", math.sqrt(2.0)), ("π", math.pi), ("e", math.e)]

print()
print("[FAMILLE B — fermeture composée du registre : lecture [OBS], AUCUN pouvoir de verdict]")
n_hits = 0
for nom_c, c in registre:
    for forme, val in (("G*·c", G_STAR * c), ("G*/c", G_STAR / c), ("c/G*", c / G_STAR)):
        for nom_t, t in cibles:
            eps = min(abs(val / t - 1.0), abs(t / val - 1.0))
            barre = TOL_HIT_PLUS if nom_t in ("√2", "π", "e") else TOL_HIT
            hit = eps <= barre
            if hit:
                n_hits += 1
            famille_B.append({"compose": forme.replace("c", nom_c), "forme": forme,
                              "valeur": float(val), "cible": nom_t, "cible_valeur": float(t),
                              "ecart_min": float(eps), "barre": barre, "hit": bool(hit)})
print(f"  {n_hits} hit(s) sur {len(famille_B)} lectures composées "
      f"(barres 1e-4 / 2,355e-7 — comparaisons multiples : hits = [OBS], I5-B)")
for h in famille_B:
    if h["hit"]:
        print(f"  >>> [OBS] {h['compose']} = {h['valeur']:.10f} vs {h['cible']} = "
              f"{h['cible_valeur']:.10f} ; écart = {h['ecart_min']:.2e}")

phi_sur_5 = PHI / 5.0
ec_head = min(abs(phi_sur_5 / G_STAR - 1.0), abs(G_STAR / phi_sur_5 - 1.0))
note("tête de liste déposée : φ/5 vs G*",
     f"φ/5 = {phi_sur_5:.16f} ; G* = {G_STAR:.16f} ; écart = {ec_head:.4e} — "
     f"prédit ex ante ≈ 9,86e-4 > 1e-4 → "
     f"{'MANQUÉ CONFIRMÉ (quasi-échec honorifique consigné)' if ec_head > TOL_HIT else 'HIT INATTENDU'}")

# ================================================================== FAMILLE C — DIAGNOSTICS
def pente_ln(points):
    xs = [math.log(w) for w, _ in points]
    ys = [math.log(c) for _, c in points]
    xm = sum(xs) / len(xs)
    ym = sum(ys) / len(ys)
    return sum((xi - xm) * (yi - ym) for xi, yi in zip(xs, ys)) / sum((xi - xm) ** 2 for xi in xs)


sweep = [(r["w0"], r["chi_machine"]) for r in famille_A[:14]]
low = [(w, c) for w, c in sweep if w < 1.0]
high = [(w, c) for w, c in sweep if w > 1.0]
beta_inf = pente_ln(low)
beta_sup = pente_ln(high)
table_w = [{"w0": w, "chi": c, "chi_fois_w0": w * c} for w, c in sweep]

print()
print("[FAMILLE C — diagnostics sans verdict (trou D4 ouvert, dépôt §2)]")
print("  " + "  ".join(f"ω₀={w:g}: χ·ω₀={w * c:.6f}" for w, c in sweep))
note("β_inf (porteurs < 1) et β_sup (porteurs > 1)",
     f"β_inf = {beta_inf:+.6f} ({len(low)} porteurs) ; β_sup = {beta_sup:+.6f} ({len(high)} porteurs) "
     f"— dictionnaire μ↔ω toujours absent (trou D4) : consigné SANS pouvoir de verdict")

# ================================================================== VERDICT
print()
print("=" * 74)
forme_echecs = [r for r in famille_A if not r["ok"]]
if not ok_global:
    verdict, code = "V4 — REFUTE", 1
    raison = "un contrôle bloquant est en échec (dépôt §3 : aucun sauvetage)"
elif forme_echecs or not gstar_ok:
    verdict, code = "V3 — REFUTE_FORCE_SANS_FORME", 1
    if forme_echecs:
        pire = min(forme_echecs, key=lambda r: r["ecart_relatif"])
        raison = (f"la forme close §0 est réfutée : pire lecture {pire['lecture']} "
                  f"(écart {pire['ecart_relatif']:.2e} > {TOL_FORME:.0e}) — "
                  "le défaut n'est PAS la diffusion fréquentielle du noyau")
    else:
        raison = (f"la forme close ne reproduit pas G* : écart {ec_gstar:.2e} > "
                  f"{TOL_GSTAR:.0e} — REFUTE (dépôt §4)")
elif not station_ok:
    verdict, code = "V2 — FORCE_FORME_PARTIELLE", 0
    raison = (f"la forme close tient (17/17 @1e-9, G* reproduit à {ec_gstar:.2e}) "
              f"mais la station a bougé : argmax = ω₀ = {w0_max}")
else:
    verdict, code = "V+ — FORCE_FORME_FERMEE", 0
    raison = ("la force du rephasage modulé EST la diffusion fréquentielle du noyau : "
              "17/17 lectures @1e-9, G* reproduit par la forme close, station ω₀ = 1 confirmée")
print(f"  VERDICT : {verdict}")
print(f"  RAISON  : {raison}")
print(f"  SORTIE  : exit {code}")
print("=" * 74)

# ================================================================== JSON — toutes les lectures (I3)
resultat = {
    "depot": "DEPOT_FORCE_V1.md",
    "date_execution": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t_debut)),
    "c0a": {"mtime_depot": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime_depot)),
            "mtime_execution": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t_debut)),
            "ok": bool(c0a_ok)},
    "objets_fermes": {"phi": PHI, "alpha": ALPHA, "N": N, "L": L, "delta_omega": D_OMEGA,
                      "nyquist": NYQUIST, "D2": D2_REGISTRE, "leg_a": LEG_A,
                      "impedance": IMPEDANCE, "ancre": ANCRE, "codata": CODATA,
                      "facteur_obs": FACTEUR_OBS, "G_star_registre": G_STAR,
                      "porteurs": PORTEURS, "n_trunc": N_TRUNC,
                      "tol_forme": TOL_FORME, "tol_gstar": TOL_GSTAR,
                      "tol_hit": TOL_HIT, "tol_hit_plus": TOL_HIT_PLUS},
    "controles": controles,
    "famille_A": {"lectures": famille_A,
                  "gstar": {"chi_pred": float(cp_gstar), "chi_machine": float(chi_ref),
                            "registre": G_STAR, "ecart_relatif": float(ec_gstar),
                            "ok": bool(gstar_ok)},
                  "station": {"argmax_w0": float(w0_max), "chi_max": float(chi_sweep[i_max]),
                              "attendu": 1.0, "ok": bool(station_ok)}},
    "famille_B": {"lectures": famille_B, "n_hits": n_hits,
                  "tete_de_liste_phi_sur_5": {"phi_sur_5": float(phi_sur_5),
                                              "G_star": G_STAR, "ecart": float(ec_head),
                                              "barre": TOL_HIT,
                                              "verdict": "[OBS] manqué confirmé — quasi-échec honorifique"}},
    "famille_C": {"beta_inf": float(beta_inf), "beta_sup": float(beta_sup),
                  "chi_fois_w0": table_w,
                  "puissance_verdict": "aucune (trou D4 — dictionnaire μ↔ω absent, dépôt §2)"},
    "verdict": {"nom": verdict, "raison": raison, "exit_code": code},
}
with open(SORTIE, "w", encoding="utf-8") as f:
    json.dump(resultat, f, ensure_ascii=False, indent=2)
print(f"Résultat consigné : {SORTIE}")

sys.exit(code)
