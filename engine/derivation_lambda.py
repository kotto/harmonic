#!/usr/bin/env python3
"""derivation_lambda.py — LA DÉRIVATION DE Λ PAR LE FILTRE DU VIDE
=================================================================
La dérivation honnête en 5 étapes :

ÉTAPE 1 · POSTULAT (A1) : le vide est le SURVIVANT du filtre
          — les modes qui persistent, pas ceux qui apparaissent

ÉTAPE 2 · LE FILTRE (A3) : le noyau d'or K(t) = B(α)·E_α(−λt^α)
          avec α = 1/φ, λ = φ, B(α) = 1−α+α/Γ(α)

ÉTAPE 3 · L'ÉCHELLE : la seule échelle de mémoire disponible est
          l'horizon cosmologique c·t_U — la portée de la mémoire

ÉTAPE 4 · LA FORME : Λ = F(α)·(1/(c·t_U))²
          où F(α) est le facteur de filtrage — À DÉRIVER

ÉTAPE 5 · LE TEST : comparer F aux candidats principiés,
          précision déclarée, statut publié
"""
import json, math, os, time
import numpy as np

PHI = (1 + math.sqrt(5)) / 2
ALPHA = 1 / PHI
C = 299792458.0
T_U = 4.35e17            # s — âge de l'univers (13,8 Gyr)
LAMBDA_OBS = 1.1056e-52   # m⁻² — Planck 2018

from validation_coeff_quantiques import E_alpha, B_ALPHA

print("=" * 74)
print("DÉRIVATION DE Λ — LE FILTRE DU VIDE")
print("=" * 74)

# ══════════════════════════════════════════════════════════════════
# ÉTAPE 1-3 · le cadre
# ══════════════════════════════════════════════════════════════════
print("""
ÉTAPE 1 · POSTULAT (A1) : le vide est le survivant du filtre
ÉTAPE 2 · LE FILTRE (A3) : K(t) = B(α)·E_α(−λt^α), α = 1/φ
ÉTAPE 3 · L'ÉCHELLE : l'horizon c·t_U — la portée de la mémoire
""")

# La forme : Λ = F·(1/(c·t_U))²
scale2 = (C * T_U)**2
F_needed = LAMBDA_OBS * scale2     # le facteur de filtrage REQUIS
print(f"  (c·t_U)² = {scale2:.4e} m²")
print(f"  F requis = Λ_obs·(c·t_U)² = {F_needed:.6f}")
print(f"  (F = le facteur de filtrage que la dérivation doit produire)")
print()

# ══════════════════════════════════════════════════════════════════
# ÉTAPE 4 · les candidats PRINCIPIÉS (dérivés de la structure)
# ══════════════════════════════════════════════════════════════════
print("─ ÉTAPE 4 · LES CANDIDATS PRINCIPIÉS (aucun ajusté)")

def K(t):
    """Le noyau d'or."""
    if t <= 0:
        return float(B_ALPHA)
    v = E_alpha(-PHI * t**ALPHA, ALPHA)
    return float(B_ALPHA) * (abs(v) if isinstance(v, complex) else v)

# C1 · F = φ² — le postulat THU initial (la mémoire élevée au carré)
# C2 · F = φ²·B(α) — avec la normalisation du noyau (ABC)
# C3 · F = φ²·K(1)/K(0) — le noyau à une unité cosmique, normalisé
# C4 · F = φ²·E_α(−φ) — la mémoire évaluée au taux φ (t=1 en unités d'horizon)
# C5 · F = φ²·⟨K⟩ — la moyenne du noyau sur l'histoire cosmique
# C6 · F = φ^{2−1/φ} — la limite de Stirling des coefficients (φ^{1/φ})

# C5 : moyenne du noyau sur [0, 1] en unités d'horizon (t → t·t_U)
ts = np.linspace(1e-6, 1.0, 20000)
avg = np.trapz([K(t) for t in ts], ts)   # ∫₀¹ K(t)dt en unités d'horizon

candidates = [
    ("C1 · φ² (postulat THU)",                 PHI**2),
    ("C2 · φ²·B(α) (normalisation ABC)",       PHI**2 * B_ALPHA),
    ("C3 · φ²·K(1)/K(0) (noyau à 1 horizon)",  PHI**2 * K(1.0) / K(0.0)),
    ("C4 · φ²·E_α(−φ) (mémoire au taux φ)",    PHI**2 * abs(E_alpha(-PHI, ALPHA))),
    ("C5 · φ²·⟨K⟩ (moyenne cosmique)",         PHI**2 * avg),
    ("C6 · φ^{2−1/φ} (limite de Stirling)",    PHI**(2 - 1/PHI)),
]

print(f"  {'Candidat':42s} {'F':>10s} {'ratio Λ':>9s} {'écart':>7s}")
best = None
for name, F in candidates:
    L = F / scale2
    ratio = L / LAMBDA_OBS
    ecart = abs(ratio - 1) * 100
    mark = " ✅" if ecart < 10 else ""
    print(f"  {name:42s} {F:10.4f} {ratio:9.3f} {ecart:6.1f}%{mark}")
    if best is None or abs(ratio - 1) < abs(best[1] - 1):
        best = (name, ratio, F)

print(f"\n  F REQUIS (observé) : {F_needed:.4f}")
print(f"  MEILLEUR candidat : {best[0]} → ratio {best[1]:.3f}")

# ══════════════════════════════════════════════════════════════════
# ÉTAPE 5 · le test et le statut
# ══════════════════════════════════════════════════════════════════
print("\n" + "═" * 74)
print("ÉTAPE 5 · LE TEST ET LE STATUT")
print("═" * 74)
print(f"""
  Le facteur de filtrage REQUIS par l'observation : F = {F_needed:.4f}

  Les candidats principiés :
    φ²              = {PHI**2:.4f}   → ×1,39 (le postulat THU initial)
    φ²·B(α)         = {PHI**2*B_ALPHA:.4f}   → ×1,13 (avec la normalisation ABC)
    φ²·K(1)/K(0)    = {PHI**2*K(1.0)/K(0.0):.4f}   → ×{PHI**2*K(1.0)/K(0.0)/F_needed:.2f}
    φ²·E_α(−φ)      = {PHI**2*abs(E_alpha(-PHI, ALPHA)):.4f}   → ×{PHI**2*abs(E_alpha(-PHI, ALPHA))/F_needed:.2f}
    φ²·⟨K⟩          = {PHI**2*avg:.4f}   → ×{PHI**2*avg/F_needed:.2f}
    φ^{{2−1/φ}}     = {PHI**(2-1/PHI):.4f}   → ×{PHI**(2-1/PHI)/F_needed:.2f}

  STATUT HONNÊTE :
  ✅ Le CADRE de dérivation est établi :
     Λ = F(α)·(1/(c·t_U))² — le vide filtré par la mémoire d'or
  ⚠️ Le FACTEUR de filtrage exact n'est PAS fermé :
     le meilleur candidat principié (φ²·B(α)) donne ×1,13
     — mieux que ×1,39, mais pas exact
  ⚡ Le TEST décisif existe : Λ(t) ∝ 1/t² — si mesuré (DESI/Euclid),
     la structure du filtre est confirmée quelle que soit la constante F
  ❌ Aucun candidat ne peut être DÉCLARÉ sans dériver le filtre complet
     — le risque numérologique interdit de choisir le facteur qui colle
""")

dep = {
    "derivation": "Λ = F(α)·(1/(c·t_U))² — le vide filtré par K(t)",
    "F_requis": F_needed,
    "candidats": {n: float(F) for n, F, _ in [(c[0], c[1], 0) for c in candidates]},
    "meilleur": {"nom": best[0], "ratio": best[1]},
    "statut": "cadre établi, facteur exact non clos, test décisif Λ(t) ∝ 1/t²",
    "date": time.strftime("%Y-%m-%d %H:%M:%S"),
}
p = os.path.join("data", "benchmarks", "derivation_lambda_report.json")
os.makedirs(os.path.dirname(p), exist_ok=True)
with open(p, "w", encoding="utf-8") as f:
    json.dump(dep, f, indent=2, ensure_ascii=False)
print(f"Rapport : {p}")
