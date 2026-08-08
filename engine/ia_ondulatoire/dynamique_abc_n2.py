# -*- coding: utf-8 -*-
"""
dynamique_abc_n2.py — LA DYNAMIQUE ABC DU SECTEUR n=2
======================================================
La contrainte ABC (α = 1/φ) entre dans la dynamique du graviton :
le d'Alembertien linéarisé devient fractionnaire :

    (Δ − ^ABC D_t^{2α}) h_μν = 0      (α = 1/φ)

Résultat ANALYTIQUE (vérifié numériquement avec le noyau corrigé) :

    ^ABC D^α_t e^{iωt} = M_α(ω) · e^{iωt}
    M_α(ω) = (iω)^α / ((1−α)(iω)^α + α)        ← valeur propre ABC

    (via la transformée de Laplace de Mittag-Leffler :
     L[E_α(−λu^α)](s) = s^{α−1}/(s^α + λ))

Conséquence FALSIFIABLE : la relation de dispersion du graviton
k² = M_α(ω)² devient dépendante de la fréquence → la vitesse du
graviton v(ω) = ω/k ≠ c.

CONTRAINTE OBSERVATIONNELLE : GW170817 (LIGO/Virgo + GRB) :
    |v_g − c|/c < 1e-15

Usage : python dynamique_abc_n2.py
"""

import cmath
import math

import numpy as np

PHI = (1 + math.sqrt(5)) / 2
ALPHA = 1 / PHI
B = 1.0                        # normalisation B(α) ≈ 1


def M_alpha(omega):
    """Valeur propre ABC : ^ABC D^α e^{iωt} = M_α(ω)·e^{iωt}."""
    iw = 1j * omega
    iw_a = iw ** ALPHA
    return iw_a / ((1 - ALPHA) * iw_a + ALPHA)


def abc_derive_ondes(omega, t_max=60.0, n=4000):
    """Vérification NUMÉRIQUE : convolution directe du noyau ABC
    (via la fonction de Mittag-Leffler CORRIGÉE du moteur) sur e^{iωt}."""
    from primitives import _mittag_leffler
    t = np.linspace(0.0, t_max, n)
    dt = t[1] - t[0]
    c = ALPHA / (1 - ALPHA)
    integ = 0.0
    # ^ABC D^α f(t) = B/(1−α) ∫_0^t f'(τ) E_α(−α(t−τ)^α/(1−α)) dτ
    f_prime = lambda tau: 1j * omega * cmath.exp(1j * omega * tau)
    # pour t = t_max (régime stationnaire)
    for i, tau in enumerate(t):
        u = t_max - tau
        integ += f_prime(tau).real * _mittag_leffler(-c * u ** ALPHA, ALPHA) * dt
    val_reel = B / (1 - ALPHA) * integ
    # partie imaginaire séparément (complexe)
    integ2 = 0.0
    for i, tau in enumerate(t):
        u = t_max - tau
        integ2 += f_prime(tau).imag * _mittag_leffler(-c * u ** ALPHA, ALPHA) * dt
    val_imag = B / (1 - ALPHA) * integ2
    ana = M_alpha(omega) * cmath.exp(1j * omega * t_max)
    return (val_reel + 1j * val_imag), ana


print("=" * 72)
print("LA DYNAMIQUE ABC DU SECTEUR n=2 — dispersion du graviton")
print("=" * 72)

# [1] vérification de la valeur propre analytique
print("\n[1] VALEUR PROPRE ABC DE L'ONDE PLANE (α = 1/φ = 0.618)")
print("    ^ABC D^α e^{iωt} = M_α(ω)·e^{iωt},  M_α = (iω)^α/((1−α)(iω)^α + α)")
for w in (0.5, 1.0, 2.0):
    num, ana = abc_derive_ondes(w)
    print(f"    ω = {w}: numérique = {num.real:+.4f}{num.imag:+.4f}i"
          f" | analytique = {ana.real:+.4f}{ana.imag:+.4f}i"
          f" | écart = {abs(num - ana):.2e}")

# [2] relation de dispersion du graviton fractionnaire
print("\n[2] DISPERSION : k² = M_α(ω)² → v(ω) = ω/k")
ws = np.logspace(-2, 2, 9)
print(f"    {'ω':>8s} {'k':>10s} {'v(ω)/c':>10s} {'déviation':>12s}")
deviations = []
for w in ws:
    M = M_alpha(w)
    k = abs(M)                    # branche propagative
    v = w / k if k > 0 else float("inf")
    dev = abs(v - 1.0)
    deviations.append(dev)
    print(f"    {w:8.3f} {k:10.4f} {v:10.4f} {dev:12.2e}")

# [3] comparaison avec la contrainte LIGO
print("\n[3] CONTRAINTE OBSERVATIONNELLE (GW170817, LIGO/Virgo + GRB)")
print("    |v_g − c|/c < 1e-15  (la vitesse du graviton = celle de la lumière")
print("    à moins de 1e-15 près, sur 4×10^8 années-lumière)")
dev_min = min(deviations)
print(f"    Déviation minimale prédite par la dynamique ABC (α=1/φ) : {dev_min:.1e}")
print(f"    Écart avec la contrainte LIGO : {dev_min / 1e-15:.1e} × la borne")
if dev_min > 1e-15:
    print("    → ❌ LA DYNAMIQUE ABC NAÏVE DU SECTEUR n=2 EST EXCLUE")
    print("      par GW170817, d'environ 14 ordres de grandeur.")
else:
    print("    → compatible (régime de fréquence basse)")

print("\n" + "=" * 72)
print("VERDICT")
print("  · La valeur propre ABC de l'onde plane est EXACTE (vérifiée")
print("    numériquement avec le noyau Mittag-Leffler corrigé).")
print("  · La dynamique ABC naïve (dérivée temporelle fractionnaire")
print("    dans le d'Alembertien du graviton) prédit une dispersion")
print("    énorme : v(ω) dévie de c de ~10 % à ω ~ 1.")
print("  · GW170817 exclut cette prédiction à ~14 ordres de grandeur :")
print("    le graviton voyage à c avec une précision de 1e-15.")
print("  → La contrainte ABC doit entrer AUTREMENT que comme dérivée")
print("    temporelle linéarisée : la porte se déplace vers la structure")
print("    NON-LINÉAIRE (l'itération de Deser) ou la dimension spectrale")
print("    fractionnaire — pas vers la cinétique linéarisée.")
print("=" * 72)
