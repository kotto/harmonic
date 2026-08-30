#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verif_jacobson_thu_v0.py — PISTE JACOBSON/UNRUH × NOYAU ABC (THU V0)
=====================================================================
Vérification machine des 8 contrôles du dépôt DEPOT_JACOBSON_THU_V0.md.
Chaque nombre déposé est calculé par machine (leçon FORCE V1.2).

Contrôles et signatures attendues :
  C1  Chaîne de Jacobson : T_U·(dS/dA) = a·c²/(8πG) — le 8π émerge de
      2π (Unruh) × 4 (Bekenstein-Hawking).                        [EXACT]
  C2  T_Hawking(M_Pl) = T_Pl/(8π) ≠ T_Pl/ln φ — ratio 8π/ln φ ≈ 52.2.
      (Réfutation du rapprochement T* ↔ Hawking, déjà consignée.)  [RÉFUTATION confirmée]
  C3  Queue de Mittag-Leffler : E_α(−x) ~ x⁻¹/Γ(1−α) pour α=1/φ —
      loi de puissance, PAS e^(−x) (ratio > 1e6 à x=20).           [CONFIRMÉ]
  C4  Le noyau ABC est sans échelle : λ_eff(t) = −d ln K/dt ∝ t^(α−1)
      → ratio λ_eff(2t)/λ_eff(t) → 1/2 (exponentiel : 1) — aucun
      e^(−t/T_U) ; le pont direct V3 « K ∝ e^(−t/T_U) » est
      RÉFUTÉ tel qu'énoncé.                                        [RÉFUTATION confirmée]
  C5  Hurwitz : liminf_q q·||qα|| est MAXIMISÉ par α=1/φ à 1/√5
      ≈ 0.4472 — unicité de l'irrationalité maximale dans (0,1).    [CONFIRMÉ]
  C6  B(α) ne donne ni 1/(8π) ni κ = 8πG : κ n'émerge PAS de la
      normalisation du noyau (fixé par la limite newtonienne).     [RÉFUTATION confirmée]
  C7  Masse de Hawking dorée M_Pl·ln φ/(8π) ≈ 0.0191·M_Pl —
      calculée mais sans lien théorique identifié.                 [RÉFUTATION confirmée]
  C8  T_Unruh(a = gravité de surface c⁴/(4GM)) = T_Hawking(M)
      exactement, pour toute masse M.                              [EXACT]

Verdict déposé (voir DEPOT_JACOBSON_THU_V0.md) :
  · La chaîne thermodynamique Jacobson est EXACTE et re-vérifiée (C1, C8).
  · Le pont direct noyau ABC ↔ température d'Unruh est RÉFUTÉ (C3, C4) :
    le noyau est une loi de puissance SANS échelle — il ne peut pas
    encoder une température à lui seul.
  · α = 1/φ reste AXIOMATIQUE (Hurwitz, C5) — non dérivé d'Unruh.
  · κ = 8πG n'émerge pas de B(α) (C6) — fixé par la limite newtonienne.

Sortie : exit 0 ssi les 8 contrôles matchent leurs signatures.
"""

import math
import os
import time
import json

try:
    import mpmath as mp
    mp.mp.dps = 60
    HAVE_MP = True
except ImportError:
    HAVE_MP = False

PHI = (1.0 + math.sqrt(5.0)) / 2.0
ALPHA = 1.0 / PHI  # ≈ 0.6180339887498949
HBAR = 1.054571817e-34
C = 299792458.0
G = 6.67430e-11
KB = 1.380649e-23
M_SUN = 1.98892e30
# Masse et température de Planck (définitions CODATA, gravitational)
M_PL = math.sqrt(HBAR * C / G)
T_PL = math.sqrt(HBAR * C**5 / (G * KB**2))

results = []


def record(cid, label, value, expected, ok, note=""):
    results.append({"id": cid, "controle": label, "valeur": value,
                    "attendu": expected, "ok": bool(ok), "note": note})
    status = "OK " if ok else "FAIL"
    print(f"  [{status}] {cid} · {label}")
    print(f"         valeur   = {value}")
    print(f"         attendu  = {expected}" + (f"   ({note})" if note else ""))


# ---------------------------------------------------------------------
# Mittag-Leffler E_α(−x) par série en haute précision
# ---------------------------------------------------------------------
def mittag_leffler_neg(alpha, x):
    """E_α(−x) = Σ (−x)^k / Γ(αk+1) — précision ET bornes adaptatives.

    Les termes croissent jusqu'à k0 ≈ x^(1/α)/α (magnitude e^P avec
    P = k·ln x − lnΓ(αk+1)) puis décroissent LENTEMENT (Stirling) :
    il faut itérer bien au-delà de k0 et couvrir P chiffres de
    cancellation. On estime P et k_fin par Stirling en flottant,
    puis on somme en précision étendue avec arrêt anticipé.
    """
    if not HAVE_MP:
        raise RuntimeError("mpmath requis")

    def nat_exp(k):
        return k * math.log(x) - math.lgamma(alpha * k + 1.0) if k else 0.0

    # Pic de magnitude et point de convergence (termes < e^(−90))
    exp_peak, k_end = 0.0, 6000
    for k in range(1, 6001):
        e = nat_exp(k)
        exp_peak = max(exp_peak, e)
        if k > 10 and e < -90.0 and e < nat_exp(k - 1):
            k_end = k + 60
            break

    old_dps = mp.mp.dps
    mp.mp.dps = min(int(exp_peak / math.log(10)) + 50, 3000)
    try:
        a_mp = mp.mpf(alpha)
        x_mp = mp.mpf(x)
        s = mp.mpf(1)
        for k in range(1, k_end + 1):
            term = (-x_mp) ** k / mp.gamma(a_mp * k + 1)
            s += term
            if k > 10 and abs(term) < abs(s) * mp.mpf(10) ** (-40):
                break
        return float(s)
    finally:
        mp.mp.dps = old_dps


# =====================================================================
print("=" * 70)
print("PISTE JACOBSON/UNRUH × NOYAU ABC — THU V0 (vérification machine)")
print("=" * 70)
t0 = time.time()

# ---------------------------------------------------------------------
# C1 — Chaîne de Jacobson : le 8π émerge de 2π (Unruh) × 4 (Bekenstein)
# ---------------------------------------------------------------------
print("\n─ C1 · Chaîne de Jacobson (δQ = T_U dS sur horizon de Rindler)")
# Unités naturelles (ħ = c = k_B = 1) : T_U = a/2π, dS = dA/4
lhs_nat = (1.0 / (2.0 * math.pi)) * (1.0 / 4.0)   # T_U·(dS/dA) pour a = 1
rhs_nat = 1.0 / (8.0 * math.pi)
ok1_nat = abs(lhs_nat - rhs_nat) < 1e-18
# SI : T_U·(dS/dA) = a·c²/(8πG) pour a = 1 m/s²
tu = HBAR * 1.0 / (2.0 * math.pi * C * KB)                 # K par (m/s²)
dsda = KB * C**3 / (4.0 * G * HBAR)                        # J/(m²·K)
lhs_si = tu * dsda
rhs_si = C**2 / (8.0 * math.pi * G)
rel1 = abs(lhs_si - rhs_si) / rhs_si
ok1_si = rel1 < 1e-12
record("C1", "T_U·dS/dA = a·c²/(8πG)", f"{rel1:.2e} (rel.)", "< 1e-12",
       ok1_nat and ok1_si,
       f"nat {lhs_nat:.12f} = {rhs_nat:.12f} ; SI {lhs_si:.4e} = {rhs_si:.4e}")

# ---------------------------------------------------------------------
# C2 — T_Hawking(M_Pl) = T_Pl/(8π) ≠ T_Pl/ln φ
# ---------------------------------------------------------------------
print("\n─ C2 · Rapprochement T* doré ↔ Hawking (réfutation consignée)")
ratio_c2 = (T_PL / math.log(PHI)) / (T_PL / (8.0 * math.pi))  # = 8π/ln φ
th_mpl = HBAR * C**3 / (8.0 * math.pi * G * M_PL * KB)
ok2 = abs(ratio_c2 - 8.0 * math.pi / math.log(PHI)) < 1e-12 and ratio_c2 > 50
record("C2", "ratio (T_Pl/lnφ) / (T_Pl/8π) = 8π/lnφ", f"{ratio_c2:.6f}",
       f"8π/lnφ = {8.0*math.pi/math.log(PHI):.6f} ≠ 1", ok2,
       f"T_Hawking(M_Pl) = {th_mpl:.4e} K ; T_Pl/lnφ = {T_PL/math.log(PHI):.4e} K")

# ---------------------------------------------------------------------
# C3 — Queue de Mittag-Leffler : loi de puissance, pas exponentielle
# ---------------------------------------------------------------------
print("\n─ C3 · Queue de E_α(−x) pour α = 1/φ (loi de puissance)")
x1, x2 = 20.0, 40.0
E1 = mittag_leffler_neg(ALPHA, x1)
E2 = mittag_leffler_neg(ALPHA, x2)
slope = math.log(E1 / E2) / math.log(x2 / x1)          # asymptote : 1
amp1 = x1 * E1                                          # asymptote : 1/Γ(1−α)
gam_1ma = float(mp.gamma(1 - ALPHA))                    # Γ(1−1/φ) = Γ(0.382)
tail_ref = 1.0 / gam_1ma
ratio_exp = E1 / math.exp(-x1)                          # vs e^(−x)
ok3 = (abs(slope - 1.0) < 0.05) and (abs(amp1 - tail_ref) / tail_ref < 0.03) \
      and (ratio_exp > 1e6)
record("C3", f"E_α(−20)·20 / (1/Γ(1−α))", f"{amp1/tail_ref:.5f}", "≈ 1 (±3 %)",
       ok3,
       f"pente {slope:.4f} → 1 ; Γ(1−α) = {gam_1ma:.4f} ; "
       f"E_α(−20)/e^(−20) = {ratio_exp:.2e} ≫ 1 → PAS exponentiel")

# ---------------------------------------------------------------------
# C4 — Noyau ABC sans échelle : λ_eff ∝ t^(α−1), aucun e^(−t/T_U)
# ---------------------------------------------------------------------
print("\n─ C4 · Pont direct K(t) ∝ e^(−t/T_U) (conjecture V3, réfutée)")
# K(t) = B(α)·E_α(−φ·t^α)  (α/(1−α) = φ — coefficient de l'équation mère)
KARG = PHI
def K_log(t):
    return math.log(mittag_leffler_neg(ALPHA, KARG * t ** ALPHA))
tA = 10.0
h = 1e-4
lam_t = -(K_log(tA + h) - K_log(tA - h)) / (2 * h)
lam_2t = -(K_log(2 * tA + h) - K_log(2 * tA - h)) / (2 * h)
ratio_c4 = lam_2t / lam_t
# exponentielle : ratio = 1 ; loi de puissance λ_eff ≈ α/t : ratio → 1/2
ok4 = 0.35 < ratio_c4 < 0.7 and abs(ratio_c4 - 1.0) > 0.2
record("C4", "λ_eff(2t)/λ_eff(t)", f"{ratio_c4:.4f}",
       "≠ 1 (exponentiel) ; ≈ 1/2 (λ_eff ∝ 1/t)", ok4,
       "λ_eff ∝ t^(α−1) → SANS échelle → aucun T_U encodable dans K seul")

# ---------------------------------------------------------------------
# C5 — Hurwitz : liminf_q q·||qα|| maximisé par α = 1/φ à 1/√5
# ---------------------------------------------------------------------
print("\n─ C5 · Irrationalité maximale (Hurwitz 1891)")
def markov_liminf(alpha, qmax=1500, qmin=100):
    """min_{q∈[qmin,qmax]} q·||qα|| — approximation du liminf.

    Le liminf est asymptotique : il est atteint le long des dénominateurs
    des réduites (Fibonacci pour 1/φ). On exclut les petits q (q<qmin),
    sinon q=1 domine le min fini et masque la convergence vers 1/√5.
    """
    best = float("inf")
    for q in range(qmin, qmax + 1):
        d = abs(q * alpha - round(q * alpha))
        v = q * d
        if v < best:
            best = v
    return best

cands = {"1/φ": 1.0 / PHI, "1/√2": 1.0 / math.sqrt(2.0),
         "1/π": 1.0 / math.pi, "1/e": 1.0 / math.e}
infs = {k: markov_liminf(v) for k, v in cands.items()}
s_1phi = infs["1/φ"]
hurwitz_bound = 1.0 / math.sqrt(5.0)
ok5 = abs(s_1phi - hurwitz_bound) < 1e-4 and all(
    s_1phi > v + 1e-3 for k, v in infs.items() if k != "1/φ")
record("C5", "liminf_q q·||qα|| pour α = 1/φ", f"{s_1phi:.6f}",
       f"1/√5 = {hurwitz_bound:.6f} (maximum possible)", ok5,
       "; ".join(f"{k}: {v:.6f}" for k, v in infs.items()))

# ---------------------------------------------------------------------
# C6 — κ = 8πG n'émerge pas de B(α)
# ---------------------------------------------------------------------
print("\n─ C6 · Émergence de κ = 8πG depuis B(α) (réfutée)")
b_std = float(1 - ALPHA + ALPHA / mp.gamma(ALPHA))   # normalisation A.-B. analytique
b_repo = 0.8506508083                                # normalisation dépôt (Σ K = 1)
d1 = abs(b_std - 1.0 / (8.0 * math.pi))
d2 = abs(b_repo - 1.0 / (8.0 * math.pi))
d3 = abs(b_std * 8.0 * math.pi - 1.0)
ok6 = d1 > 10 * (1.0 / (8.0 * math.pi)) and d2 > 10 * (1.0 / (8.0 * math.pi)) \
      and d3 > 1.0
record("C6", "B(1/φ) vs 1/(8π)", f"B_AB = {b_std:.6f}, B_dépôt = {b_repo:.6f}",
       "aucun ≠ 1/(8π) ≈ 0.0398", ok6,
       f"κ = 8πG est fixé par la limite newtonienne, PAS par B(α) "
       f"(B_AB×8π = {b_std*8.0*math.pi:.4f} ≠ 1)")

# ---------------------------------------------------------------------
# C7 — Masse de Hawking dorée (sans lien)
# ---------------------------------------------------------------------
print("\n─ C7 · M_Hawking = M_Pl·lnφ/(8π) (calculé, sans lien)")
m_gold_rel = math.log(PHI) / (8.0 * math.pi)          # en unités de M_Pl
m_gold_kg = m_gold_rel * M_PL
ok7 = abs(m_gold_rel - 0.019146) < 1e-4
record("C7", "M_Pl·lnφ/(8π) / M_Pl", f"{m_gold_rel:.6f}", "≈ 0.019146", ok7,
       f"M = {m_gold_kg:.3e} kg — aucun lien théorique identifié (honnête)")

# ---------------------------------------------------------------------
# C8 — T_Unruh(a = c⁴/4GM) = T_Hawking(M), exactement
# ---------------------------------------------------------------------
print("\n─ C8 · Unruh au bord de l'horizon = Hawking")
worst = 0.0
for mtest in (1.0, 10.0, 1e6):
    M = mtest * M_SUN
    a_sg = C**4 / (4.0 * G * M)                        # gravité de surface
    t_u = HBAR * a_sg / (2.0 * math.pi * C * KB)
    t_h = HBAR * C**3 / (8.0 * math.pi * G * M * KB)
    worst = max(worst, abs(t_u / t_h - 1.0))
ok8 = worst < 1e-12
record("C8", "max |T_U/T_H − 1| sur M ∈ {1, 10, 1e6} M☉", f"{worst:.2e}",
       "< 1e-12", ok8,
       "l'observateur accéléré au bord de l'horizon voit exactement "
       "la température de Hawking")

# =====================================================================
print("\n" + "=" * 70)
n_ok = sum(1 for r in results if r["ok"])
print(f"BILAN : {n_ok}/{len(results)} contrôles conformes aux signatures attendues")
print("=" * 70)
for r in results:
    print(f"  {'✅' if r['ok'] else '❌'} {r['id']} · {r['controle']}")

verdict = {
    "depot": "DEPOT_JACOBSON_THU_V0",
    "verdict": "JACOBSON_V0_CHAINE_EXACTE_PONT_DIRECT_REFUTE",
    "controles_ok": n_ok,
    "controles_total": len(results),
    "resume": [
        "C1, C8 : chaîne thermodynamique de Jacobson EXACTE (8π = 2π×4)",
        "C2, C7 : rapprochements T*/Hawking réfutés (8π/lnφ = 52.23)",
        "C3, C4 : noyau ABC sans échelle (loi de puissance) — pont direct "
        "K ∝ e^(−t/T_U) RÉFUTÉ tel qu'énoncé",
        "C5 : α = 1/φ maximise sup_q q·||qα|| à 1/√5 (Hurwitz) — axiomatique, "
        "non dérivé d'Unruh",
        "C6 : κ = 8πG n'émerge pas de B(α) — fixé par la limite newtonienne"
    ],
    "date": time.strftime("%Y-%m-%d %H:%M:%S"),
    "duree_s": round(time.time() - t0, 1),
}
p = os.path.join("resultat_jacobson_thu_v0.json")
json.dump({"verdict": verdict, "controles": results},
          open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"\nRésultat : {p}")
print(f"Sortie : {'0 (conforme)' if n_ok == len(results) else '1 (ÉCHEC)'}")
raise SystemExit(0 if n_ok == len(results) else 1)
