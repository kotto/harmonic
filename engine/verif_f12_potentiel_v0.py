# -*- coding: utf-8 -*-
"""
POTENTIEL F12 V0 — exécution machine de la MORT 2 de FRONTIERE_F12_TABLEAU_PERIODIQUE.md

La thèse (frontière §3, chaîne P20–P22) :

  P20 l'opérateur : le potentiel est la réponse du champ à une source ponctuelle à
      travers la boucle mémoire complète — D^α appliqué DEUX fois (aller-retour
      d'influence, le même double franchissement que la phase d'échange P14 de la
      MORT 1). La dérivée fractionnaire est l'inverse du noyau déposé :
        D^α = φ·K̂⁻¹ − φ,   symbole (iω)^α,
      et la boucle a le symbole (iω)^{2α}, dont la phase est EXACTEMENT
      σ = e^{iπα} — la MÊME boucle qui porte la statistique (MORT 1) porte le
      potentiel (MORT 2). Phase = e^{iπα}, amplitude = ordre 2α.
  P21 le scaling  : la fonction de Green de la boucle en d = 3 est celle du
      laplacien fractionnaire (−Δ)^α : Ĝ(ω) = |ω|^{−2α} ⟹
        G(r) = c(α)·r^{2α−3},   c(α) = Γ((3−2α)/2)/(4^α π^{3/2} Γ(α)).
      À α = 1 : G(r) = 1/(4πr) — Coulomb ET son préfacteur 1/(4π) RECOUVRÉS de la
      boucle, pas insérés. À α = 1/φ : exposant 2/φ − 3 = √5 − 4 = −1.7639320…(forme
      close, via l'identité bit-exacte 2/φ = √5 − 1).
  P22 la tension  : à α = 1/φ le potentiel s'écarte de Coulomb de l'exposant
      3−√5 = 0.7639 (plus raide) ; ratio V_THU/V_Coulomb = 4πc·r^{2α−2}. Lectures
      L′1/L′2 MIROIR de L1/L2 (Pauli) — MÊME discriminateur ex ante : quel ordre
      ferme la boucle de matière ?
        L′1 — la boucle de matière ferme à l'ordre plein (action Φ₂ = π) :
              Coulomb intact ; l'exposant fractionnaire vit aux échelles mémoire.
        L′2 — l'exposant 2α−3 s'applique à la matière : la spectroscopie atomique
              devrait le montrer — mort expérimentale ou régime nouveau.
      Aucun sauvetage (I5) : la tension est déposée, pas corrigée.

  Contrôles bloquants C0b…C6 — UN SEUL en échec ⟹ REFUTE exit 1.

  Verdicts :
    V+  POTENTIEL_BOUCLE_EXPOSANT_2ALPHA_MOINS_3     (tous contrôles)   exit 0
    V3  REFUTE_SCALING   (les pentes mesurées ne suivent pas 2α−3)       exit 1
    V4  REFUTE           (un contrôle bloquant en échec)                 exit 1

Objets fermés O1–O8. Barres pré-enregistrées : TOL_C = 1e-12 (identités fermées),
TOL_LATTICE = 5e-2 (pentes/amplitudes sur treillis — artefacts d'images consignés,
ajustement A·r^p + B avec fond libre).
Sortie : resultat_f12_potentiel_v0.json (toutes les lectures, y compris les quasi-échecs).
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
W_MIN, W_MAX = 3.0, 40.0                     # O3 — fenêtre radiale de mesure (pas d'images proches)

TOL_C = 1.0e-12                              # O7 — identités fermées
TOL_PHASE = 1.0e-15                          # O7 — phases
TOL_LATTICE = 5.0e-2                         # O7 — pentes/amplitudes treillis (pré-enregistré)
ALPHAS = (0.3, 0.5, ALPHA, 0.8, 1.0)         # O7 — 5 α, la machine doit suivre 2α−3 partout

mp.dps = 40                                  # route mpmath — dépôt à 30 chiffres


# ================================================================== noyau (O4 — deux routes, verbatim CHSH/FORCE)
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
    """O6 — c(α) = Γ((d−2α)/2)/(4^α π^{d/2} Γ(α)) : préfacteur de la fonction de
    Green de (−Δ)^α. À α=1, d=3 : 1/(4π) — le préfacteur de Coulomb DÉRIVÉ."""
    return math.gamma((d - 2.0 * alpha) / 2.0) / (4.0 ** alpha * math.pi ** (d / 2.0)
                                                  * math.gamma(alpha))


# ================================================================== exécution
t_exec = time.time()
controles = []


def controle(nom, ok, detail):
    controles.append({"controle": nom, "ok": bool(ok), "detail": detail})
    print(f"  [{'OK ' if ok else 'ÉCHEC'}] {nom} : {detail}")
    return bool(ok)


print("=" * 74)
print("  POTENTIEL F12 V0 — la boucle mémoire comme source du lien (MORT 2 de F12)")
print("=" * 74)
print()
print("[CONTRÔLES BLOQUANTS — frontière §4 : un seul échec ⟹ REFUTE exit 1]")
ok_global = True

# ------------------------------------------------------------------ C0b — fermeture algébrique
ec_phi = abs(PHI ** 2 - (PHI + 1.0))
ec_2sphi = abs(2.0 / PHI - (math.sqrt(5.0) - 1.0))
EXPOSANT = 2.0 * ALPHA - 3.0                                   # ≈ −1.7639320225002102
ec_expo = abs(EXPOSANT - (math.sqrt(5.0) - 4.0))
GAP = abs(EXPOSANT - (-1.0))                                   # écart à Coulomb = 3−√5
ec_gap = abs(GAP - (3.0 - math.sqrt(5.0)))
c0b_ok = (ec_phi < TOL_PHASE and ec_2sphi < TOL_PHASE and ec_expo < TOL_PHASE
          and ec_gap < TOL_PHASE)
ok_global &= controle("C0b fermeture algébrique : φ² = φ+1 ; 2/φ = √5−1 ; "
                      "exposant 2α−3 = √5−4 ; écart à Coulomb = 3−√5 (bit-près)",
                      c0b_ok,
                      f"écart φ² = {ec_phi:.1e} ; 2/φ−(√5−1) = {ec_2sphi:.1e} ; "
                      f"exposant−(√5−4) = {ec_expo:.1e} ; gap−(3−√5) = {ec_gap:.1e} ; "
                      f"exposant = {EXPOSANT:.16f}")

# ------------------------------------------------------------------ C1 — noyau double route
ec1 = max(abs(Khat(w) - Khat_real(w)) for w in (0.5, 1.0, 2.0, 3.7))
ok_global &= controle("C1 noyau double route (complexe vs réelle développée) "
                      "aux points {½, 1, 2, 3.7}", ec1 < TOL_C, f"écart max = {ec1:.2e}")

# ------------------------------------------------------------------ C2 — P20 : l'identité noyau-dérivée et la boucle
# D^α = φ·K̂⁻¹ − φ : la dérivée fractionnaire EST l'inverse du noyau déposé.
ec2_der = max(abs(PHI / Khat(w) - PHI - cmath.exp(ALPHA * cmath.log(1j * w)))
              for w in (0.5, 1.0, 2.0, 3.7))
# la boucle D^α∘D^α : symbole ((iω)^α)², phase = πα = la phase d'échange σ de la MORT 1
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

# ------------------------------------------------------------------ C3 — P21 : le scaling (route machine, 3D)
print(f"  … treillis {N3}³, fenêtre radiale [{W_MIN}, {W_MAX}], "
      f"ajustement A·r^p + B (fond d'images libre) — {len(ALPHAS)} valeurs de α")
freqs = 2.0 * math.pi * np.fft.fftfreq(N3, d=1.0)
KX, KY, KZ = np.meshgrid(freqs, freqs, freqs, indexing="ij")
KMAG = np.sqrt(KX * KX + KY * KY + KZ * KZ)
del KX, KY, KZ
IDX = np.indices((N3, N3, N3))
# rayon torique enveloppé : distance minimale au travers des images (coordonnée
# radiale correcte sur le tore — leçon run 2 : le rayon non enveloppé n'utilise
# que la moitié basse-index de chaque coquille)
DX = np.minimum(IDX[0], N3 - IDX[0]).astype(float)
DY = np.minimum(IDX[1], N3 - IDX[1]).astype(float)
DZ = np.minimum(IDX[2], N3 - IDX[2]).astype(float)
R = np.sqrt(DX ** 2 + DY ** 2 + DZ ** 2)
del IDX, DX, DY, DZ
WINDOW = (R >= W_MIN) & (R <= W_MAX)
BINS = np.arange(int(math.floor(W_MIN)) + 1, int(math.ceil(W_MAX)) + 1)
BIN_OF = np.rint(R).astype(int)


def mesure_pente(alpha):
    """Ĝ = |ω|^{−2α} (mode zéro retiré) → G(r) = IFFT → pentes et amplitudes."""
    Ghat = np.zeros((N3, N3, N3), dtype=complex)
    mask_k = KMAG > 0
    Ghat[mask_k] = KMAG[mask_k] ** (-2.0 * alpha)
    del mask_k
    G = np.fft.ifftn(Ghat).real
    del Ghat
    r_bins, g_bins = [], []
    for b in range(int(math.floor(W_MIN)) + 1, int(math.ceil(W_MAX)) + 1):
        sel = WINDOW & (np.abs(R - b) < 0.5)
        if np.any(sel):
            r_bins.append(float(b))
            g_bins.append(float(np.median(G[sel])))
    r_bins = np.array(r_bins)
    g_bins = np.array(g_bins)
    # (i) exposant libre : scan p ∈ cible ± 0.15, LSQ linéaire (A, B) sur (r^p, 1)
    cible = 2.0 * alpha - 3.0
    best_p = None
    for p in np.arange(cible - 0.15, cible + 0.15, 1.0e-4):
        base = np.vstack([r_bins ** p, np.ones_like(r_bins)]).T
        coef, res, _, _ = np.linalg.lstsq(base, g_bins, rcond=None)
        resid = float(np.sqrt(np.mean((base @ coef - g_bins) ** 2)))
        if best_p is None or resid < best_p[1]:
            best_p = (float(p), resid, coef)
    # (ii) amplitude à exposant THÉORIQUE fixé : A comparable à c(α)
    base = np.vstack([r_bins ** cible, np.ones_like(r_bins)]).T
    coef_fixe, _, _, _ = np.linalg.lstsq(base, g_bins, rcond=None)
    return {"alpha": alpha, "cible": cible, "p_libre": best_p[0],
            "residu_libre": best_p[1], "A_fixe": float(coef_fixe[0]),
            "B_fixe": float(coef_fixe[1]), "c_theorie": riesz_const(alpha),
            "r_bins": r_bins.tolist(), "g_bins": g_bins.tolist()}, G


lectures = {}
for a in ALPHAS:
    lec, _G = mesure_pente(a)
    lectures[a] = lec
    print(f"    α = {a:.6f} : cible 2α−3 = {lec['cible']:+.6f} ; p_libre = "
          f"{lec['p_libre']:+.6f} ; écart = {abs(lec['p_libre'] - lec['cible']):.4f} ; "
          f"residu = {lec['residu_libre']:.2e} ; A/c = {lec['A_fixe']/lec['c_theorie']:.4f}")

ec3 = max(abs(lectures[a]["p_libre"] - lectures[a]["cible"]) for a in ALPHAS)
ok_global &= controle("C3 P21 scaling machine : exposant mesuré (p_libre, fond libre) vs "
                      f"2α−3 pour α ∈ {ALPHAS} — barre {TOL_LATTICE:.0e} (pré-enregistrée)",
                      ec3 < TOL_LATTICE, f"écart max = {ec3:.4f}")

# ------------------------------------------------------------------ C4 — P21 : les constantes
ec4_coul = max(abs(lectures[1.0]["A_fixe"] - 1.0 / (4.0 * math.pi)) / (1.0 / (4.0 * math.pi)),
               abs(lectures[1.0]["B_fixe"]) / (1.0 / (4.0 * math.pi)))
c_theo_alpha = riesz_const(ALPHA)
ec4_alpha = abs(lectures[ALPHA]["A_fixe"] - c_theo_alpha) / c_theo_alpha
ec4_ligne = max(abs(lectures[a]["A_fixe"] - lectures[a]["c_theorie"]) / lectures[a]["c_theorie"]
                for a in ALPHAS)
ok_global &= controle("C4 P21 constantes : α=1 → A = 1/(4π) (le préfacteur de Coulomb "
                      "DÉRIVÉ de la boucle) ; α=1/φ → A = c(1/φ) ; toutes lignes A ≈ c(α) "
                      f"— barre {TOL_LATTICE:.0e}",
                      ec4_ligne < TOL_LATTICE,
                      f"|A−1/(4π)|/(1/4π) = {ec4_coul:.4f} ; |A−c(1/φ)|/c = {ec4_alpha:.4f} ; "
                      f"max sur 5 α = {ec4_ligne:.4f} ; c(1/φ) = {c_theo_alpha:.12f}")

# ------------------------------------------------------------------ C5 — P22 : la tension déposée
RATIO_R10 = 4.0 * math.pi * c_theo_alpha * 10.0 ** (2.0 * ALPHA - 2.0)   # V_THU/V_Coul(10)
ec5_gap = abs((EXPOSANT - (-1.0)) - (3.0 - math.sqrt(5.0)))
c5_ok = abs(EXPOSANT + 1.0) > 0.5 and ec5_gap < TOL_PHASE
ok_global &= controle("C5 P22 tension : à α=1/φ, exposant −1.7639 vs −1 — le potentiel "
                      "THU n'EST pas Coulomb (écart 3−√5, plus raide) ; lectures L′1/L′2 "
                      "miroir de L1/L2, même discriminateur (ordre de fermeture de la "
                      "boucle de matière) — consigné sans sauvetage",
                      c5_ok,
                      f"écart exposant = 3−√5 = {EXPOSANT + 1.0:.16f} ; "
                      f"V_THU/V_Coulomb(10) = {RATIO_R10:.6f} ; "
                      f"c(1/φ)·4π = {4.0 * math.pi * c_theo_alpha:.6f}")

# ------------------------------------------------------------------ C6 — témoins falsifiants
lin_x = np.array(ALPHAS)
lin_y = np.array([lectures[a]["p_libre"] for a in ALPHAS])
pente_ligne, intercept_ligne = np.polyfit(lin_x, lin_y, 1)
t_05 = abs(lectures[0.5]["p_libre"] - (-2.0))
t_03 = abs(lectures[0.3]["p_libre"] - (-2.4))
c6_ok = (abs(pente_ligne - 2.0) < 0.25 and t_05 < TOL_LATTICE and t_03 < TOL_LATTICE)
ok_global &= controle("C6 témoins falsifiants : la machine suit 2α−3 SUR TOUTE la ligne "
                      "(pente des pentes = 2, pas deux points accordés) ; α=0.5 → −2 ; "
                      "α=0.3 → −2.4",
                      c6_ok,
                      f"pente des pentes = {pente_ligne:.4f} (cible 2) ; intercept = "
                      f"{intercept_ligne:.4f} (cible −3) ; |p(0.5)−(−2)| = {t_05:.4f} ; "
                      f"|p(0.3)−(−2.4)| = {t_03:.4f}")

# ================================================================== verdict
print()
sig_mp = mp.exp(1j * (1 / ((1 + mp.sqrt(5)) / 2)) * mp.pi)
c_mp = mp.gamma((3 - 2 / ((1 + mp.sqrt(5)) / 2)) / 2) / (4 ** (1 / ((1 + mp.sqrt(5)) / 2))
                                                         * mp.pi ** (mp.mpf(3) / 2)
                                                         * mp.gamma(1 / ((1 + mp.sqrt(5)) / 2)))
deps = {
    "exposant_thu_2alpha_moins_3": repr(EXPOSANT),
    "exposant_forme_close_racine5_moins_4_mp30": mp.nstr(mp.sqrt(5) - 4, 30),
    "ecart_coulomb_3_moins_racine5_mp30": mp.nstr(3 - mp.sqrt(5), 30),
    "c_1_over_phi_mp30": mp.nstr(c_mp, 30),
    "c_1_over_phi_float": repr(c_theo_alpha),
    "c_alpha_1": repr(riesz_const(1.0)),
    "coulomb_1_sur_4pi": repr(1.0 / (4.0 * math.pi)),
    "A_mesure_alpha_1": repr(lectures[1.0]["A_fixe"]),
    "A_mesure_alpha_1_over_phi": repr(lectures[ALPHA]["A_fixe"]),
    "ratio_V_thu_sur_V_coulomb_r10": repr(RATIO_R10),
    "pentes_mesurees": {repr(a): {"cible": lectures[a]["cible"],
                                  "p_libre": lectures[a]["p_libre"],
                                  "A_fixe": lectures[a]["A_fixe"],
                                  "c_theorie": lectures[a]["c_theorie"]}
                        for a in ALPHAS},
}
for k, v in deps.items():
    if k != "pentes_mesurees":
        print(f"  [DÉPÔT] {k} = {v}")

verdict, code = ("POTENTIEL_BOUCLE_EXPOSANT_2ALPHA_MOINS_3", 0) if ok_global \
    else ("REFUTE", 1)
print()
print(f"VERDICT : {verdict} — exit {code}")
print(f"Résultat : resultat_f12_potentiel_v0.json ({time.time() - t_exec:.1f} s)")

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "resultat_f12_potentiel_v0.json"), "w", encoding="utf-8") as fh:
    json.dump({"verdict": verdict, "ok": bool(ok_global), "exit_code": code,
               "controles": controles, "depots": deps, "lectures": lectures},
              fh, ensure_ascii=False, indent=2)

sys.exit(code)
