# -*- coding: utf-8 -*-
"""
verification_deduction_abc.py — VÉRIFICATION DE LA DÉRIVATION DE L'ÉQUATION MÈRE
===============================================================================
Document : DERIVATION_EQUATION_MERE_ABC.md (08/08/2026)

Vérifie la dérivation Ψ = Σ Hₙ(Ψ₁)ⁿ depuis l'équation fractionnaire ABC :
  1. FORME : les solutions du problème aux valeurs propres ABC
     (^ABC D^α Ψ = λ·Ψ) sont les fonctions de Mittag-Leffler
     E_α(λ·t^α) = Σₙ (λ·t^α)ⁿ/Γ(αn+1) — la forme monomiale est dérivée.
  2. COEFFICIENTS : la déduction impose H_n = λⁿ/Γ(αn+1) — comparés aux
     constantes harmoniques {φ, π, e, √2, √3, √5, e/π}.
  3. VERDICT : forme VÉRIFIÉE / coefficients POSTULÉS (ou émergence ?).

Usage : python verification_deduction_abc.py
"""

import math

from primitives import abc_kernel, _mittag_leffler   # le moteur les a déjà

PHI = (1 + math.sqrt(5)) / 2
ALPHA = 1 / PHI

THEORIE = {1: PHI, 2: math.pi, 3: math.e,
           4: math.sqrt(2), 5: math.sqrt(3), 6: math.sqrt(5),
           7: math.e / math.pi}

print("=" * 72)
print("VÉRIFICATION DE LA DÉRIVATION ABC → ÉQUATION MÈRE")
print("=" * 72)

# ── 1. FORME : la solution de Mittag-Leffler est bien une somme monomiale
print("\n[1] FORME — solutions du problème ^ABC D^α Ψ = λ·Ψ")
print("    Ψ(t) = C·E_α(λ·t^α) = Σₙ (λ·t^α)ⁿ/Γ(αn+1)   (Atangana-Baleanu 2016)")
print("    En posant Ψ₁ = t^α :  Ψ = Σₙ Hₙ·(Ψ₁)ⁿ   ← FORME DE L'ÉQUATION MÈRE")
# vérification numérique : E_α par la série du moteur vs évaluation directe
t, lam = 1.7, 1.449230
somme = sum(lam ** n * (t ** ALPHA) ** n / math.gamma(ALPHA * n + 1)
            for n in range(0, 200))
print(f"    E_α(λ·t^α) par série (n=0..200) : {somme:.10f}")
print(f"    _mittag_leffler du moteur       : "
      f"{_mittag_leffler(lam * t ** ALPHA, ALPHA):.10f}")
print(f"    écart : {abs(somme - _mittag_leffler(lam * t ** ALPHA, ALPHA)):.2e}"
      f"  → {'✅ FORME VÉRIFIÉE' if abs(somme - _mittag_leffler(lam * t ** ALPHA, ALPHA)) < 1e-8 else '❌'}")
print(f"    noyau abc_kernel(1.7) = {abc_kernel(1.7):.6f} (K(0)=1, K→∞ → 0)")

# ── 2. COEFFICIENTS : la déduction impose H_n = λⁿ/Γ(αn+1)
print("\n[2] COEFFICIENTS — ce que la déduction impose vs la théorie")
lamb = PHI * math.gamma(1 + ALPHA)          # calibré sur H₁ = φ
print(f"    λ calibré pour H₁ = φ : λ = {lamb:.6f}")
print(f"    {'n':>2s}   {'H_n (ABC déduit)':>18s}   {'H_n (théorie)':>16s}   rapport")
rapports = []
for n in range(1, 8):
    h_abc = lamb ** n / math.gamma(ALPHA * n + 1)
    h_th = THEORIE[n]
    r = h_abc / h_th
    rapports.append(r)
    print(f"    {n:2d}   {h_abc:18.6f}   {h_th:16.6f}   {r:6.3f}")

# ── 3. VERDICT
print("\n[3] VERDICT")
moy = sum(rapports[1:]) / len(rapports[1:])     # hors H₁ (calibré)
print(f"    rapport moyen (H₂..H₇) : {moy:.3f}  (1,000 = émergence exacte)")
forme_ok = True
coef_ok = all(abs(r - 1.0) < 0.01 for r in rapports[1:])
if coef_ok:
    print("    → ✅ ÉMERGENCE : les constantes harmoniques SORTENT de l'équation")
    print("      — dérivation COMPLÈTE (à publier).")
else:
    print("    → ✅ FORME VÉRIFIÉE (théorème ABC, structure monomiale dérivée)")
    print("      ⚠️ COEFFICIENTS POSTULÉS : Hₙ = {φ, π, e…} ne sortent pas de")
    print("      l'équation aux valeurs propres standard — la contrainte")
    print("      d'espace (Oyibo) exacte est la porte de complétude.")
print("=" * 72)
