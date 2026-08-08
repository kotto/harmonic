# -*- coding: utf-8 -*-
"""
analyse_30_observables.py — LES 30 OBSERVABLES SOUMISES AU PROTOCOLE
====================================================================
Le document fondateur revendique ~30 observables prédites par les H_n
« sans paramètre libre », avec un p < 10⁻⁵⁰ postulé.

Ce script applique le protocole qui a tranché pour α et GAGUT :
  1. valeur de la formule vs CODATA → écart relatif ET écart en σ
     (σ = écart / incertitude expérimentale — « dans l'incertitude »
     signifie σ ≤ 3)
  2. p-valeur par CALIBRATION : fraction de 2000 cibles aléatoires dont
     la meilleure approximation par le treillis est aussi bonne que
     celle de la formule (le p de α = 0,0785)
  3. CORRECTION DE BONFERRONI : avec 30 essais, la significativité
     individuelle exige p < 0,05/30 = 0,00167

Usage : python analyse_30_observables.py
"""

import itertools
import math
import sys

import numpy as np

sys.path.insert(0, ".")
from analyse_pvalue_harmonique import (construire_treillis,      # noqa: E402
                                       meilleure_approximation)

PHI = (1 + math.sqrt(5)) / 2
PI = math.pi
E = math.e
S2, S3, S5 = math.sqrt(2), math.sqrt(3), math.sqrt(5)

# (nom, formule, valeur CODATA, incertitude CODATA)
OBSERVABLES = [
    ("α (structure fine)", PI ** 4 * E ** -4 * PHI ** -5 * S2 ** -1 * S3 ** -5,
     0.0072973525693, 1.1e-12),
    ("α_S(M_Z) (couplage fort)", 2 * PHI ** 2 / (3 * S3 * PI * E),
     0.1180, 0.0009),
    ("sin² θ_W (Weinberg)", S3 * S5 ** 3 / (2 * PHI * PI ** 2 * E),
     0.22343, 0.00044),
    ("m_μ/m_e (muon/électron)", PHI ** -3 * PI ** 3 * E * S2 ** 2 * S3 ** 3,
     206.7682830, 0.0000046),
    ("m_τ/m_μ (tau/muon)", PHI * PI ** 3 * E ** 2 * S2 ** -1 * S3 ** -5,
     16.817, 0.005),
    ("m_H/v (Higgs/vev)", 2 * PHI * S2 / 9,
     0.50849, 0.00057),
    ("λ (auto-couplage Higgs)", PHI ** -1 * PI * E * S2 ** -3 * S3 * S5 ** -4,
     0.12879, 0.00070),
]

# treillis (espace large, comme l'analyse de α)
logs, poids = construire_treillis(8, 6)

print("=" * 78)
print("LES 30 OBSERVABLES — protocole anti-numérologie (α : p=0,0785)")
print("=" * 78)
print(f"{'Observable':26s} {'formule':>14s} {'CODATA':>14s} {'écart':>10s} "
      f"{'σ':>8s} {'p-calb':>8s}")

rng = np.random.default_rng(2026)
lo, hi = logs[0], logs[-1]
cibles_alea = np.exp(rng.uniform(lo, hi, 2000))
bests = np.array([meilleure_approximation(logs, t) for t in cibles_alea])

resultats = []
for nom, formule, codata, inc in OBSERVABLES:
    err_rel = abs(formule - codata) / codata
    sigma = err_rel / (inc / codata)
    # p par calibration : fraction des cibles aléatoires aussi bien
    # approximées que la formule
    dl = abs(math.log(formule / codata))
    p_cal = (bests <= dl).mean()
    resultats.append((nom, err_rel, sigma, p_cal))
    print(f"{nom:26s} {formule:14.6g} {codata:14.6g} {err_rel:10.2e} "
          f"{sigma:8.1f} {p_cal:8.4f}")

print("\n" + "=" * 78)
print("VERDICTS :")
print(f"  Seuil Bonferroni (30 essais) : p < 0,00167")
for nom, err, sigma, p_cal in resultats:
    dans = "✅ dans l'incertitude" if sigma <= 3 else "❌ HORS incertitude"
    signif = "SIGNIFICATIF" if p_cal < 0.00167 else "compatible hasard"
    print(f"  {nom:26s}: {sigma:7.1f} σ ({dans}) | p = {p_cal:.4f} ({signif})")
n_signif = sum(1 for _, _, _, p in resultats if p < 0.00167)
print(f"\n  Observables significatives à Bonferroni : {n_signif}/{len(resultats)}")
print(f"  Attendu sous hasard pur : ~{len(resultats) * 0.00167:.2f}")
print("=" * 78)
