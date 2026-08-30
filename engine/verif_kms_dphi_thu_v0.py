#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verif_kms_dphi_thu_v0.py — BRANCHER D^(1/φ) SUR LA PHASE DU VIDE (KMS/UNRUH)
==============================================================================
Suite directe de DEPOT_JACOBSON_THU_V0.md (pont noyau ∝ e^(−t/T_U) réfuté :
le noyau ABC est sans échelle). Nouvelle question : l'OPÉRATEUR D^(1/φ)
agissant sur la PHASE du vide d'un observateur accéléré produit-il le
facteur thermique de KMS à T_U = a/2π ?

Contrôles et signatures attendues :
  C1  KMS : G⁺_accéléré(Δτ + iβ) = G⁺_accéléré(Δτ), β = 2π/a — EXACT ;
      contre-contrôle : trajectoire inertielle NON périodique (l'effet
      Unruh est géométrique, porté par la trajectoire).          [EXACT]
  C2  Balance détaillée du détecteur : Ḟ(ω)/Ḟ(−ω) = e^(−βω) —
      le facteur de Boltzmann sort de la fonction de Wightman.   [EXACT]
  C3  Température = courbure du couplage : T·R = ħc/(2πk_B) =
      T_Pl·l_Pl/(2π), pour TOUT trou noir ET tout observateur de
      Rindler — invariant universel.                             [EXACT]
  C4  Transparence spectrale : D^α e^{iωτ} = ω^α·e^{iπα/2}·e^{iωτ} —
      gain de loi de puissance SANS échelle, phase CONSTANTE ∀ω ;
      la périodicité KMS est préservée POUR TOUT α ∈ (0,1].
      → α = 1/φ n'est PAS sélectionné par Unruh/KMS.     [NON-SÉLECTIF]
  C5  Réfutation spectrale : aucun β ne rend le spectre fractionnaire
      ω^{2/φ} planckien ni boltzmannien (erreur L2 min > 10 %).  [RÉFUTATION]
  C6  Signature déposée : déphasage mémoire Δφ_mem = π/(2φ) = 55.6197°,
      IDENTIQUE pour tous les modes KMS — tout futur pont THU→Unruh
      doit reproduire ce nombre.
      + réfutation numérologique : ratio angle d'or/Δφ_mem ≠ φ². [SIGNATURE]
  C7  Le facteur de Boltzmann EST une phase : e^{iω·iβ} = e^{−βω} —
      bit-exact (0.00e+00). Le branchement THU passe par la PHASE
      (Φ₂ = ∫k_μdx^μ), pas par le noyau ni par l'opérateur.      [EXACT]

Verdict déposé : DEPOT_KMS_DPHI_THU_V0.md
Sortie : exit 0 ssi les 7 contrôles matchent leurs signatures.
"""

import cmath
import json
import math
import time

PHI = (1.0 + math.sqrt(5.0)) / 2.0
ALPHA = 1.0 / PHI                    # ≈ 0.6180339887498949
HBAR = 1.054571817e-34
C = 299792458.0
G = 6.67430e-11
KB = 1.380649e-23
M_SUN = 1.98892e30
M_PL = math.sqrt(HBAR * C / G)
T_PL = math.sqrt(HBAR * C**5 / (G * KB**2))
L_PL = math.sqrt(HBAR * G / C**3)

results = []


def record(cid, label, value, expected, ok, note=""):
    results.append({"id": cid, "controle": label, "valeur": value,
                    "attendu": expected, "ok": bool(ok), "note": note})
    status = "OK " if ok else "FAIL"
    print(f"  [{status}] {cid} · {label}")
    print(f"         valeur   = {value}")
    print(f"         attendu  = {expected}" + (f"   ({note})" if note else ""))


print("=" * 70)
print("BRANCHER D^(1/φ) SUR LA PHASE DU VIDE — KMS/UNRUH (vérification machine)")
print("=" * 70)
t0 = time.time()

# =====================================================================
# C1 — KMS : périodicité en temps imaginaire (accéléré) vs inertiel
# =====================================================================
print("\n─ C1 · Périodicité de KMS (accéléré) et contre-contrôle inertielle")
A_ACC = 1.0
BETA = 2.0 * math.pi / A_ACC          # période de KMS, unités ħ = c = k_B = 1
EPS = 1e-6


def G_acc(dt):
    """Fonction de Wightman, scalaire massless 4D, trajectoire de Rindler
    (Takagi 1986) : G⁺(Δτ) = −(a/4π)² / sinh²[(a(Δτ − iε))/2]."""
    return -(A_ACC / (4.0 * math.pi))**2 / cmath.sinh(0.5 * A_ACC * (dt - 1j * EPS))**2


def G_inert(dt):
    """Trajectoire inertielle (co-localisée) : G⁺ = −1/(4π²(Δτ − iε)²)."""
    return -1.0 / (4.0 * math.pi**2) / (dt - 1j * EPS)**2


taus = [0.7, 1.7, 3.1]
worst_kms = max(abs(G_acc(t + 1j * BETA) - G_acc(t)) / abs(G_acc(t)) for t in taus)
worst_inert = max(abs((G_inert(t + 1j * BETA) - G_inert(t)) / G_inert(t)) for t in taus)
half = abs(G_acc(1.0 + 1j * BETA / 2.0) / G_acc(1.0))   # ≠ 1 : la période est β, pas β/2
ok1 = worst_kms < 1e-9 and worst_inert > 0.1 and abs(half - 1.0) > 0.1
record("C1", "accéléré périodique (iβ) / inertiel NON périodique",
       f"KMS rel. {worst_kms:.2e} ; inertiel rel. {worst_inert:.3f}",
       "KMS < 1e-9 ; inertiel ≫ tol (≈ 0.98)", ok1,
       f"demi-période : |G(τ+iβ/2)/G(τ)| = {half:.4f} ≠ 1 → période = β exactement")

# =====================================================================
# C2 — Balance détaillée : Ḟ(ω)/Ḟ(−ω) = e^(−βω)
# =====================================================================
print("\n─ C2 · Balance détaillée du détecteur à deux niveaux")


def rate(w, beta):
    """Taux de réponse SIGNÉ (forme fermée standard — Takagi 1986, eq. 3.22) :
    Ḟ(ω) = ω/(2π(e^{βω}−1)) pour ω > 0 (excitation) ;
    Ḟ(ω) = |ω|/(2π(1−e^{−β|ω|})) pour ω < 0 (désexcitation, forme stable).
    La branche est choisie sur le ω SIGNÉ — abs ne porte que la magnitude."""
    u = abs(w)
    if w > 0:
        return u / (2.0 * math.pi * math.expm1(beta * u))
    return u / (2.0 * math.pi * (-math.expm1(-beta * u)))


max_log = 0.0
for w in (0.5, 1.0, 2.0, 5.0):
    ratio = rate(w, BETA) / rate(-w, BETA)
    max_log = max(max_log, abs(math.log(ratio) + BETA * w))
ok2 = max_log < 1e-12
record("C2", "max |ln(Ḟ(ω)/Ḟ(−ω)) + βω|", f"{max_log:.2e}", "< 1e-12", ok2,
       "Ḟ(ω)/Ḟ(−ω) = e^(−βω) : le détecteur voit un bain de Planck à T_U = a/2π")

# =====================================================================
# C3 — Température = courbure du couplage : T·R = ħc/(2πk_B)
# =====================================================================
print("\n─ C3 · Loi T·R = constante (trous noirs ET Rindler)")
TR_CONST = HBAR * C / (2.0 * math.pi * KB)      # K·m
worst_tr = 0.0
for mtest in (1.0, 10.0, 1e6):
    M = mtest * M_SUN
    r_s = 2.0 * G * M / C**2                    # rayon de Schwarzschild
    r_circ = 2.0 * r_s                          # rayon du cercle de couplage (c²/a_sg)
    t_h = HBAR * C**3 / (8.0 * math.pi * G * M * KB)
    worst_tr = max(worst_tr, abs(t_h * r_circ / TR_CONST - 1.0))
for r_test in (1.0, 1e3, 1e26):
    a_obs = C**2 / r_test                       # accélération correspondante
    t_u = HBAR * a_obs / (2.0 * math.pi * C * KB)
    worst_tr = max(worst_tr, abs(t_u * r_test / TR_CONST - 1.0))
tr_planck = T_PL * L_PL / (2.0 * math.pi) / TR_CONST - 1.0
ok3 = worst_tr < 1e-12 and abs(tr_planck) < 1e-15
record("C3", "max |T·R/(ħc/2πk_B) − 1| (3 BH + 3 Rindler)", f"{worst_tr:.2e}",
       "< 1e-12", ok3,
       f"T·R = ħc/(2πk_B) = {TR_CONST:.4e} K·m = T_Pl·l_Pl/(2π) "
       f"(écart Planck {tr_planck:.1e}) → la température EST la courbure du couplage")

# =====================================================================
# C4 — Transparence spectrale de D^α : gain loi de puissance, phase constante
# =====================================================================
print("\n─ C4 · Transparence de D^(1/φ) : eigenvalues (iω)^α, KMS préservé ∀α")
worst_law, worst_phase = 0.0, 0.0
for w in (2.0, 4.0, 8.0, 16.0):   # ω=1 exclu : log ω = 0 (loi de puissance indéfinie)
    lam = (1j * w)**ALPHA
    worst_law = max(worst_law, abs(math.log(abs(lam)) / math.log(w) - ALPHA))
    ph = cmath.phase(lam)
    worst_phase = max(worst_phase, abs(ph - ALPHA * math.pi / 2.0))
# périodicité KMS préservée pour α ∈ {0.5, 1/φ, 0.9} : D^αF reste 2π-périodique
N_MODES = 4000
worst_per = 0.0
for alpha_t in (0.5, ALPHA, 0.9):
    for x in (0.7, 2.3, 4.9):
        s1 = sum(n**-2.0 * (1j * n)**alpha_t * cmath.exp(1j * n * x)
                 for n in range(1, N_MODES + 1))
        s2 = sum(n**-2.0 * (1j * n)**alpha_t * cmath.exp(1j * n * (x + 2.0 * math.pi))
                 for n in range(1, N_MODES + 1))
        worst_per = max(worst_per, abs(s2 - s1) / max(abs(s1), 1e-300))
ok4 = worst_law < 1e-12 and worst_phase < 1e-12 and worst_per < 1e-9
record("C4", "D^α : pente log|λ|/logω − α ; phase − πα/2 ; périodicité",
       f"loi {worst_law:.1e} ; phase {worst_phase:.1e} ; KMS {worst_per:.1e}",
       "tous < tolérances", ok4,
       "λ(ω) = ω^α·e^{iπα/2} SANS échelle ; KMS préservé pour TOUT α → "
       "α = 1/φ n'est PAS sélectionné par Unruh/KMS (consigné)")

# =====================================================================
# C5 — Réfutation : aucun β ne rend ω^{2/φ} thermique
# =====================================================================
print("\n─ C5 · Le spectre fractionnaire n'est ni planckien ni boltzmannien")
GRID = [0.2 * (6.25)**(i / 60.0) for i in range(61)]     # ω ∈ [0.2, 1.25]
MODEL = [w**(2.0 * ALPHA) for w in GRID]                  # ancré à 1 en ω = 1


def shape_err(kind, beta):
    """Erreur L2 relative du spectre thermique vs modèle fractionnaire ancré."""
    num = den = 0.0
    for w, m in zip(GRID, MODEL):
        if kind == "planck":
            f = 1.0 / math.expm1(beta * w)
            f1 = 1.0 / math.expm1(beta)
        else:  # boltzmann, ancré : e^{−β(ω−1)}
            f = math.exp(-beta * (w - 1.0))
            f1 = 1.0
        f_n = f / f1
        num += (f_n - m)**2
        den += m**2
    return math.sqrt(num / den)


def golden_min(kind, lo=-4.0, hi=4.0, iters=120):
    gr = (math.sqrt(5.0) - 1.0) / 2.0
    a_, b_ = lo, hi
    c_ = b_ - gr * (b_ - a_)
    d_ = a_ + gr * (b_ - a_)
    for _ in range(iters):
        if shape_err(kind, math.exp(c_)) < shape_err(kind, math.exp(d_)):
            b_, d_ = d_, c_
        else:
            a_, c_ = c_, d_
        c_ = b_ - gr * (b_ - a_)
        d_ = a_ + gr * (b_ - a_)
    return shape_err(kind, math.exp((a_ + b_) / 2.0)), math.exp((a_ + b_) / 2.0)


err_p, beta_p = golden_min("planck")
err_b, beta_b = golden_min("boltz")
ok5 = err_p > 0.10 and err_b > 0.10
record("C5", "erreur L2 min (Planck, Boltzmann)", f"{err_p:.3f} (β*={beta_p:.3f}) ; "
       f"{err_b:.3f} (β*={beta_b:.3f})",
       "les deux > 0.10", ok5,
       "aucun β ne rend ω^{2/φ} thermique — même verdict structurel que "
       "JACOBSON V0, côté opérateur")

# =====================================================================
# C6 — Signature déposée : déphasage mémoire uniforme π/(2φ)
# =====================================================================
print("\n─ C6 · Signature : Δφ_mem = π/(2φ) — constante, identique ∀ modes KMS")
dphi = ALPHA * math.pi / 2.0
dphi_deg = math.degrees(dphi)
golden_angle = 2.0 * math.pi * (1.0 - 1.0 / PHI)          # 2π/φ² ≈ 137.5078°
ratio_ga = golden_angle / dphi
# indépendance du mode : arg[(iω)^α] = πα/2 pour tout ω — déjà mesuré en C4
ok6 = abs(dphi - math.pi / (2.0 * PHI)) < 1e-15 and abs(ratio_ga - PHI**2) > 0.05
record("C6", "Δφ_mem = πα/2 = π/(2φ)", f"{dphi:.6f} rad = {dphi_deg:.4f}°",
       f"{math.pi/(2.0*PHI):.6f} rad ; ratio angle d'or/Δφ = {ratio_ga:.4f} ≠ φ² = {PHI**2:.4f}",
       ok6,
       "déphasage UNIFORME sur tous les modes KMS — signature déposée ; "
       "numérologie angle d'or réfutée (écart 5.6 %)")

# =====================================================================
# C7 — Le facteur de Boltzmann EST une phase : e^{iω·iβ} = e^{−βω}
# =====================================================================
print("\n─ C7 · Boltzmann = phase évaluée en temps imaginaire (bit-exact)")
worst_c7 = 0.0
worst_split = 0.0
for w, b in ((1.0, 2.0 * math.pi), (2.5, 3.0), (0.7, 0.5)):
    thermal_via_phase = cmath.exp(1j * w * (1j * b))       # la phase sur le cercle
    worst_c7 = max(worst_c7, abs(thermal_via_phase - math.exp(-w * b)))
    # poids mémoire × poids thermique se MULTIPLIENT (sans se mélanger) :
    w_mem = abs((1j * w)**ALPHA)                           # gain de mémoire
    product = w_mem * math.exp(-w * b)
    worst_split = max(worst_split, abs(product - w**ALPHA * math.exp(-w * b)))
ok7 = worst_c7 == 0.0 and worst_split < 1e-15
record("C7", "max |e^{iω·iβ} − e^{−βω}| et split mémoire×thermique",
       f"{worst_c7:.1e} ; {worst_split:.1e}", "0.00e+00 bit-exact ; split ≤ 1e-15 (1 ulp)", ok7,
       "le facteur thermique est la PHASE du vide sur le cercle imaginaire — "
       "porte native THU (Φ₂ = ∫k_μdx^μ) ; poids mémoire et poids thermique "
       "se multiplient, ∀α")

# =====================================================================
print("\n" + "=" * 70)
n_ok = sum(1 for r in results if r["ok"])
print(f"BILAN : {n_ok}/{len(results)} contrôles conformes aux signatures attendues")
print("=" * 70)
for r in results:
    print(f"  {'✅' if r['ok'] else '❌'} {r['id']} · {r['controle']}")

verdict = {
    "depot": "DEPOT_KMS_DPHI_THU_V0",
    "verdict": "KMS_DPHI_V0_CONFORME_PONT_PHASE_ORDRE_NON_SELECTIONNE",
    "controles_ok": n_ok,
    "controles_total": len(results),
    "resume": [
        "C1 : KMS périodique pour l'accéléré (β = 2π/a), NON pour l'inertiel — "
        "l'effet Unruh est géométrique (porté par la trajectoire)",
        "C2 : balance détaillée Ḟ(ω)/Ḟ(−ω) = e^(−βω) exacte — bain de Planck",
        "C3 : T·R = ħc/(2πk_B) = T_Pl·l_Pl/(2π) — invariant universel, "
        "la température EST la courbure du couplage",
        "C4 : D^(1/φ) transparent (λ = ω^α·e^{iπα/2}) — KMS préservé ∀α : "
        "α = 1/φ NON sélectionné par Unruh (consigné)",
        "C5 : aucun β ne rend ω^{2/φ} planckien/boltzmannien (erreurs "
        f"{err_p:.2f} / {err_b:.2f}) — pont spectral RÉFUTÉ",
        "C6 : signature déposée Δφ_mem = π/(2φ) = 55.6197°, uniforme ∀ modes "
        "KMS ; numérologie angle d'or réfutée",
        "C7 : e^{iω·iβ} = e^{−βω} bit-exact — le facteur de Boltzmann est une "
        "PHASE ; le pont THU passe par Φ₂ = ∫k_μdx^μ, pas par le noyau"
    ],
    "date": time.strftime("%Y-%m-%d %H:%M:%S"),
    "duree_s": round(time.time() - t0, 1),
}
with open("resultat_kms_dphi_thu_v0.json", "w", encoding="utf-8") as fh:
    json.dump({"verdict": verdict, "controles": results}, fh,
              indent=2, ensure_ascii=False)
print(f"\nRésultat : resultat_kms_dphi_thu_v0.json")
print(f"Sortie : {'0 (conforme)' if n_ok == len(results) else '1 (ÉCHEC)'}")
raise SystemExit(0 if n_ok == len(results) else 1)
