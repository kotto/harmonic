# -*- coding: utf-8 -*-
"""
POTENTIEL F12 V0.1 — exécution machine du dépôt DEPOT_F12_POTENTIEL_V0_1.md

V0 (consigné REFUTE exit 1, runs 1–3) : trois causes d'échec identifiées AVANT ce
dépôt — bug de signe dans le contrôle C5, fenêtre de mesure hors du régime continu
(sag tore au bord lointain), dégénérescence de l'ajustement 3-param. La thèse est
INTACTE (diagnostic déposé : rapports champ proche 0.94–0.99, pentes [3,12] : −1.768
vs −1.7639). V0.1 change le PROTOCOLE, pas la thèse — déposé avant exécution :

  P20 l'opérateur : D^α = φ·K̂⁻¹ − φ ; boucle = (iω)^{2α}, phase = πα = σ —
      la même boucle porte la statistique (MORT 1) et le lien (MORT 2).
  P21 le scaling  : G(r) = c(α)·r^{2α−3}, c(α) = Γ((3−2α)/2)/(4^α π^{3/2} Γ(α)).
      α=1 : 1/(4πr) — Coulomb + préfacteur recouvrés. α=1/φ : √5−4.
  P22 la tension  : écart à Coulomb = 3−√5 (plus raide) ; L′1/L′2 miroir de
      L1/L2, même discriminateur ex ante — consignée sans sauvetage.

  Mesure V0.1 (déposée §2) : fenêtre CONTINUE [3, 8] (r ≪ L/2π) ; exposant =
  pente log-log directe sur 6 coquilles ; amplitude = A à exposant THÉORIQUE
  fixé (A·r^{2α−3}+B, B absorbe la constante IR) ; sonde Δx = 0.75 en [OBS].

  Contrôles bloquants C0a…C6 — UN SEUL en échec ⟹ REFUTE exit 1.
  Barres pré-enregistrées (dépôt §2) : C3 < 5e-2 ; C4 < 1.0e-1 ; C6 < 2.5e-1
  (pente-des-pentes) et < 5e-2 (ancres).

  Verdicts :
    V+  POTENTIEL_BOUCLE_EXPOSANT_2ALPHA_MOINS_3   (tous contrôles)   exit 0
    V3  REFUTE_SCALING (pentes ≠ 2α−3 dans le régime continu)          exit 1
    V4  REFUTE (un contrôle bloquant en échec)                         exit 1

Objets fermés O1–O8. Sortie : resultat_f12_potentiel_v0_1.json.
"""

import cmath
import json
import math
import os
import sys
import time

import numpy as np
from mpmath import mp, mpf

# ================================================================== O1–O8 — objets fermés
PHI = (1.0 + math.sqrt(5.0)) / 2.0          # O1
ALPHA = 1.0 / PHI                            # α = 1/φ

THETA = ALPHA * math.pi / 2.0                # O2 — θ = πα/2 (verbatim KMS C6)

N3 = 192                                     # O3 — treillis 3D, pas Δx = 1, boîte L = 192
W_MIN, W_MAX = 3.0, 8.0                      # O3 — fenêtre CONTINUE [3, 8] (dépôt §2)

TOL_C = 1.0e-12                              # O7 — identités fermées
TOL_PHASE = 1.0e-15                          # O7 — phases
BARRE_PENTE = 5.0e-2                         # O7 — C3/C6 ancres (dépôt §2)
BARRE_AMP = 1.0e-1                           # O7 — C4 (dépôt §2, justifié §0)
BARRE_LIGNE = 2.5e-1                         # O7 — C6 pente-des-pentes (dépôt §2)
ALPHAS = (0.3, 0.5, ALPHA, 0.8, 1.0)         # O7 — 5 α, la machine suit 2α−3 partout

mp.dps = 40


# ================================================================== noyau (O4 — deux routes)
def Khat(omega):
    """K̂(ω) = φ/((iω)^α + φ) — route complexe, branche principale. K̂(0) = 1."""
    if omega == 0.0:
        return complex(1.0, 0.0)
    z = 1j * omega
    return PHI / (cmath.exp(ALPHA * cmath.log(z)) + PHI)


def Khat_real(omega):
    """K̂ forme réelle développée (phase incluse) — route indépendante."""
    if omega == 0.0:
        return complex(1.0, 0.0)
    w = abs(omega)
    s = 1.0 if omega > 0.0 else -1.0
    wa = w ** ALPHA
    den = PHI + wa * math.cos(math.pi * ALPHA / 2.0) \
        + 1j * s * wa * math.sin(math.pi * ALPHA / 2.0)
    return PHI / den


def riesz_const(alpha, d=3):
    """O6 — c(α) = Γ((d−2α)/2)/(4^α π^{d/2} Γ(α)). À α=1, d=3 : 1/(4π)."""
    return math.gamma((d - 2.0 * alpha) / 2.0) / (4.0 ** alpha * math.pi ** (d / 2.0)
                                                  * math.gamma(alpha))


# ================================================================== exécution
t_exec = time.time()
controles = []


def controle(nom, ok, detail):
    controles.append({"controle": nom, "ok": bool(ok), "detail": detail})
    print(f"  [{'OK ' if ok else 'ÉCHEC'}] {nom} : {detail}")
    return bool(ok)


def note(detail):
    print(f"  [   ] {detail}")


print("=" * 74)
print("  POTENTIEL F12 V0.1 — protocole corrigé déposé, thèse inchangée (MORT 2 de F12)")
print("=" * 74)
print()
print("[CONTRÔLES BLOQUANTS — dépôt §2 : un seul échec ⟹ REFUTE exit 1]")
ok_global = True

# ------------------------------------------------------------------ C0a — dépôt antérieur
RACINE = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.join(RACINE, "DEPOT_F12_POTENTIEL_V0_1.md")
mtime_depot = os.path.getmtime(DEPOT)
c0a_ok = mtime_depot < t_exec
ok_global &= controle("C0a dépôt V0.1 antérieur à l'exécution", c0a_ok,
                      f"mtime dépôt {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime_depot))} "
                      f"< exécution {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t_exec))}")

# ------------------------------------------------------------------ C0b — fermeture algébrique
ec_phi = abs(PHI ** 2 - (PHI + 1.0))
ec_2sphi = abs(2.0 / PHI - (math.sqrt(5.0) - 1.0))
EXPOSANT = 2.0 * ALPHA - 3.0                                   # ≈ −1.7639320225002102
ec_expo = abs(EXPOSANT - (math.sqrt(5.0) - 4.0))
GAP = abs(EXPOSANT + 1.0)                                      # écart à Coulomb = 3−√5
ec_gap = abs(GAP - (3.0 - math.sqrt(5.0)))
c0b_ok = (ec_phi < TOL_PHASE and ec_2sphi < TOL_PHASE and ec_expo < TOL_PHASE
          and ec_gap < TOL_PHASE)
ok_global &= controle("C0b fermeture algébrique : φ² = φ+1 ; 2/φ = √5−1 ; "
                      "exposant 2α−3 = √5−4 ; écart à Coulomb |2α−3+1| = 3−√5 (bit-près)",
                      c0b_ok,
                      f"écart φ² = {ec_phi:.1e} ; 2/φ−(√5−1) = {ec_2sphi:.1e} ; "
                      f"exposant−(√5−4) = {ec_expo:.1e} ; gap−(3−√5) = {ec_gap:.1e} ; "
                      f"exposant = {EXPOSANT:.16f}")

# ------------------------------------------------------------------ C1 — noyau double route
ec1 = max(abs(Khat(w) - Khat_real(w)) for w in (0.5, 1.0, 2.0, 3.7))
ok_global &= controle("C1 noyau double route (complexe vs réelle développée) "
                      "aux points {½, 1, 2, 3.7}", ec1 < TOL_C, f"écart max = {ec1:.2e}")

# ------------------------------------------------------------------ C2 — P20 : l'identité noyau-dérivée et la boucle
ec2_der = max(abs(PHI / Khat(w) - PHI - cmath.exp(ALPHA * cmath.log(1j * w)))
              for w in (0.5, 1.0, 2.0, 3.7))
sig_loop = cmath.exp(2.0 * ALPHA * cmath.log(1j * 1.3))
sig_direct = complex(math.cos(ALPHA * math.pi), math.sin(ALPHA * math.pi))
ec2_phase = abs(cmath.phase(sig_loop) - ALPHA * math.pi)
ec2_sigma = abs(sig_loop / abs(sig_loop) - sig_direct)
ok_global &= controle("C2 P20 opérateur : |φK̂⁻¹ − φ − (iω)^α| ≈ 0 (la dérivée est "
                      "l'inverse du noyau déposé) ; phase de la boucle = πα = σ — "
                      "la même boucle porte la statistique (M1) et le lien (M2)",
                      ec2_der < TOL_C and ec2_phase < TOL_PHASE and ec2_sigma < TOL_PHASE,
                      f"identité max = {ec2_der:.2e} ; |phase−πα| = {ec2_phase:.2e} ; "
                      f"|σ_boucle − σ_MORT1| = {ec2_sigma:.2e}")

# ------------------------------------------------------------------ treillis partagé
freqs = 2.0 * math.pi * np.fft.fftfreq(N3, d=1.0)
KX, KY, KZ = np.meshgrid(freqs, freqs, freqs, indexing="ij")
KMAG = np.sqrt(KX * KX + KY * KY + KZ * KZ)
del KX, KY, KZ
IDX = np.indices((N3, N3, N3))
DXi = np.minimum(IDX[0], N3 - IDX[0]).astype(float)
DYi = np.minimum(IDX[1], N3 - IDX[1]).astype(float)
DZi = np.minimum(IDX[2], N3 - IDX[2]).astype(float)
R = np.sqrt(DXi ** 2 + DYi ** 2 + DZi ** 2)
del IDX, DXi, DYi, DZi
COQUILLES = [3, 4, 5, 6, 7, 8]                 # dépôt §2 — fenêtre continue [3, 8]


def mesure_green(alpha, n=N3, dx=1.0):
    """Ĝ = |ω|^{−2α} (mode zéro retiré) → G(r) ; médiane par coquille (r physiques)."""
    Ghat = np.zeros((n, n, n), dtype=complex)
    freqs_k = 2.0 * math.pi * np.fft.fftfreq(n, d=dx)
    KXl, KYl, KZl = np.meshgrid(freqs_k, freqs_k, freqs_k, indexing="ij")
    KMAGl = np.sqrt(KXl ** 2 + KYl ** 2 + KZl ** 2)
    del KXl, KYl, KZl
    nz = KMAGl > 0
    Ghat[nz] = KMAGl[nz] ** (-2.0 * alpha)
    del KMAGl, nz
    G = np.fft.ifftn(Ghat).real / dx ** 3   # normalisation (1/(2π)³)∫ — ifftn porte dx³
    del Ghat
    # rayon torique enveloppé, en unités physiques
    AX = np.indices((n, n, n))
    RX = np.minimum(AX[0], n - AX[0]).astype(float) * dx
    RY = np.minimum(AX[1], n - AX[1]).astype(float) * dx
    RZ = np.minimum(AX[2], n - AX[2]).astype(float) * dx
    Rphys = np.sqrt(RX ** 2 + RY ** 2 + RZ ** 2)
    del AX, RX, RY, RZ
    g_bins = []
    for b in COQUILLES:
        sel = np.abs(Rphys - b) < 0.5
        g_bins.append(float(np.median(G[sel])))
    del Rphys
    return np.array(g_bins, dtype=float), G


print(f"  … treillis {N3}³, fenêtre continue [{W_MIN:.0f}, {W_MAX}] — "
      f"{len(ALPHAS)} valeurs de α, pente log-log directe")
lectures = {}
for a in ALPHAS:
    g_bins, G = mesure_green(a)
    c = riesz_const(a)
    cible = 2.0 * a - 3.0
    pente = float(np.polyfit(np.log(np.array(COQUILLES, dtype=float)),
                             np.log(np.array(g_bins)), 1)[0])
    base = np.vstack([np.array(COQUILLES, dtype=float) ** cible,
                      np.ones(len(COQUILLES))]).T
    coef, _, _, _ = np.linalg.lstsq(base, np.array(g_bins), rcond=None)
    lec = {"alpha": a, "cible": cible, "pente": pente, "ecart": abs(pente - cible),
           "A_fixe": float(coef[0]), "B_fixe": float(coef[1]), "c_theorie": c,
           "sur_c": float(coef[0]) / c, "g_bins": g_bins.tolist() if hasattr(g_bins, "tolist") else g_bins}
    lectures[a] = lec
    print(f"    α = {a:.6f} : cible 2α−3 = {lec['cible']:+.6f} ; pente = "
          f"{lec['pente']:+.6f} ; écart = {lec['ecart']:.4f} ; A/c = {lec['sur_c']:.4f}")

ec3 = max(lectures[a]["ecart"] for a in ALPHAS)
ok_global &= controle("C3 P21 scaling (dépôt §2) : pente log-log directe sur la fenêtre "
                      f"continue [3, 8] vs 2α−3 pour α ∈ {ALPHAS} — barre {BARRE_PENTE:.0e}",
                      ec3 < BARRE_PENTE, f"écart max = {ec3:.4f}")

# ------------------------------------------------------------------ C4 — P21 : les constantes
ec4 = max(abs(lectures[a]["sur_c"] - 1.0) for a in ALPHAS)
ok_global &= controle("C4 P21 constantes (dépôt §2) : A (exposant théorique fixé, B libre) "
                      "vs c(α) — α=1 → 1/(4π) recouvré ; barre 1.0e-1 "
                      "(systématiques BZ/IR consignées, dépôt §0)",
                      ec4 < BARRE_AMP,
                      f"max |A/c − 1| = {ec4:.4f} ; α=1 : A = {lectures[1.0]['A_fixe']:.6f} "
                      f"vs 1/(4π) = {1.0/(4.0*math.pi):.6f} ; α=1/φ : A = "
                      f"{lectures[ALPHA]['A_fixe']:.6f} vs c = {lectures[ALPHA]['c_theorie']:.6f}")

# ------------------------------------------------------------------ [OBS] sonde de convergence Δx = 0.75
print("  [OBS] sonde de convergence (sans pouvoir de verdict) : Δx = 0.75, N = 256")
for a in (ALPHA, 1.0):
    g2, _ = mesure_green(a, n=256, dx=0.75)
    c = riesz_const(a)
    cible = 2.0 * a - 3.0
    base = np.vstack([np.array(COQUILLES, dtype=float) ** cible,
                      np.ones(len(COQUILLES))]).T
    coef, _, _, _ = np.linalg.lstsq(base, g2, rcond=None)
    note(f"α = {a:.6f} : A(Δx=0.75)/c = {float(coef[0])/c:.4f} "
         f"(vs {lectures[a]['sur_c']:.4f} à Δx = 1)")

# ------------------------------------------------------------------ C5 — P22 : la tension déposée (signe corrigé)
RATIO_R10 = 4.0 * math.pi * riesz_const(ALPHA) * 10.0 ** (2.0 * ALPHA - 2.0)
c5_ok = abs(GAP - (3.0 - math.sqrt(5.0))) < TOL_PHASE and GAP > 0.5
ok_global &= controle("C5 P22 tension (signe corrigé, dépôt §2) : |2α−3+1| = 3−√5 "
                      "bit-exact, > 0.5 — le potentiel THU n'EST pas Coulomb à α=1/φ ; "
                      "lectures L′1/L′2 miroir de L1/L2, même discriminateur ex ante "
                      "(ordre de fermeture de la boucle de matière) — sans sauvetage",
                      c5_ok,
                      f"3−√5 = {GAP:.16f} ; exposant = {EXPOSANT:.16f} ; "
                      f"V_THU/V_Coulomb(10) = {RATIO_R10:.6f}")

# ------------------------------------------------------------------ C6 — témoins falsifiants
lin_x = np.array(ALPHAS)
lin_y = np.array([lectures[a]["pente"] for a in ALPHAS])
pente_ligne, intercept_ligne = np.polyfit(lin_x, lin_y, 1)
t_05 = abs(lectures[0.5]["pente"] - (-2.0))
t_03 = abs(lectures[0.3]["pente"] - (-2.4))
c6_ok = (abs(pente_ligne - 2.0) < BARRE_LIGNE
         and t_05 < BARRE_PENTE and t_03 < BARRE_PENTE)
ok_global &= controle("C6 témoins falsifiants (dépôt §2) : la machine suit 2α−3 SUR TOUTE "
                      "la ligne (pente des pentes = 2) ; ancres α=0.5 → −2, α=0.3 → −2.4",
                      c6_ok,
                      f"pente des pentes = {pente_ligne:.4f} (cible 2) ; intercept = "
                      f"{intercept_ligne:.4f} (cible −3) ; |p(0.5)−(−2)| = {t_05:.4f} ; "
                      f"|p(0.3)−(−2.4)| = {t_03:.4f}")

# ================================================================== verdict
print()
sig_mp = mp.exp(1j * (1 / ((1 + mp.sqrt(5)) / 2)) * mp.pi)
expo_mp = 2 / ((1 + mp.sqrt(5)) / 2) - 3
c_mp = mp.gamma((3 - 2 / ((1 + mp.sqrt(5)) / 2)) / 2) / (
    4 ** (1 / ((1 + mp.sqrt(5)) / 2)) * mp.pi ** (mp.mpf(3) / 2)
    * mp.gamma(1 / ((1 + mp.sqrt(5)) / 2)))
deps = {
    "exposant_thu_2alpha_moins_3": repr(EXPOSANT),
    "exposant_forme_close_racine5_moins_4_mp30": mp.nstr(expo_mp, 30),
    "ecart_coulomb_3_moins_racine5_mp30": mp.nstr(3 - mp.sqrt(5), 30),
    "c_1_over_phi_mp30": mp.nstr(c_mp, 30),
    "c_1_over_phi_float": repr(riesz_const(ALPHA)),
    "c_alpha_1_1_sur_4pi": repr(riesz_const(1.0)),
    "A_mesure_alpha_1": repr(lectures[1.0]["A_fixe"]),
    "A_mesure_alpha_1_over_phi": repr(lectures[ALPHA]["A_fixe"]),
    "ratio_V_thu_sur_V_coulomb_r10": repr(4.0 * math.pi * riesz_const(ALPHA)
                                          * 10.0 ** (2.0 * ALPHA - 2.0)),
    "pentes_mesurees": {repr(a): {"cible": lectures[a]["cible"],
                                  "pente": lectures[a]["pente"],
                                  "ecart": lectures[a]["ecart"],
                                  "A_sur_c": lectures[a]["sur_c"]}
                        for a in ALPHAS},
}
for k, v in deps.items():
    if k != "pentes_mesurees":
        print(f"  [DÉPÔT] {k} = {v}")

verdict, code = ("POTENTIEL_BOUCLE_EXPOSANT_2ALPHA_MOINS_3", 0) if ok_global \
    else ("REFUTE", 1)
print()
print(f"VERDICT : {verdict} — exit {code}")
print(f"Résultat : resultat_f12_potentiel_v0_1.json ({time.time() - t_exec:.1f} s)")

with open(os.path.join(RACINE, "resultat_f12_potentiel_v0_1.json"), "w",
          encoding="utf-8") as fh:
    json.dump({"verdict": verdict, "ok": bool(ok_global), "exit_code": code,
               "controles": controles, "depots": deps, "lectures": lectures},
              fh, ensure_ascii=False, indent=2)

sys.exit(code)
