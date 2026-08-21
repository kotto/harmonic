#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CARTE COMPLÈTE DES PARTICULES — STRUCTURE MODULO 7 (T6)
==========================================================
Objectif : mapper TOUTES les particules connues (quarks, leptons, bosons,
Higgs) sur la structure modulo 7 : n = type (1..7) + k×7 (itération).

La masse est donnée par :
  m(n, k) = M_Pl × c_{n+7k} / f(n, k)
  
où f(n, k) est un facteur géométrique de l'ordre de 0.1..10.

On cherche pour chaque particule le (n, k) qui minimise |ln(f)|.
"""

import json, math, os, time

PHI = (1 + math.sqrt(5)) / 2
ALPHA = 1 / PHI

def gamma_lanczos(x):
    g = 7
    coef = [0.99999999999980993, 676.5203681218851, -1259.1392167224028,
            771.32342877765313, -176.61502916214059, 12.507343278686905,
            -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7]
    if x < 0.5:
        return math.pi / (math.sin(math.pi * x) * gamma_lanczos(1 - x))
    x -= 1
    a = coef[0]
    t = x + g + 0.5
    for i in range(1, g + 2):
        a += coef[i] / (x + i)
    return math.sqrt(2 * math.pi) * t ** (x + 0.5) * math.exp(-t) * a

def c(n):
    return 1.0 / gamma_lanczos(n * ALPHA + 1)

# Constantes
M_PL = 2.176434e-8  # kg
C = 299792458.0
EV_J = 1.602176634e-19
M_PL_EV = M_PL * C**2 / EV_J  # Masse de Planck en eV

# Particules connues (masse en eV, incertitude)
PARTICULES = {
    # Leptons
    "e (électron)": 0.511e6,
    "μ (muon)": 105.66e6,
    "τ (tau)": 1.777e9,
    "ν_e (neutrino e)": 0.1,        # < 1 eV approximatif
    "ν_μ (neutrino μ)": 0.17,
    "ν_τ (neutrino τ)": 18.0,
    
    # Quarks (masses de courant à 2 GeV)
    "u (up)": 2.3e6,
    "d (down)": 4.8e6,
    "s (strange)": 95e6,
    "c (charm)": 1.28e9,
    "b (bottom)": 4.18e9,
    "t (top)": 173.0e9,
    
    # Bosons
    "γ (photon)": 0.0,
    "g (gluon)": 0.0,
    "W±": 80.38e9,
    "Z⁰": 91.19e9,
    
    # Higgs
    "H (Higgs)": 125.1e9,
    
    # Baryons (pour test)
    "p (proton)": 938.272e6,
    "n (neutron)": 939.565e6,
}

N_TYPES = 7  # types modulo 7
MAX_ITER = 8  # itérations max

print("=" * 72)
print("CARTE COMPLÈTE DES PARTICULES — STRUCTURE MODULO 7")
print("=" * 72)
print(f"\n  Masse de Planck = {M_PL_EV:.4e} eV = {M_PL_EV/1e9:.4e} GeV")

# Recherche du meilleur (n, k) pour chaque particule
print(f"\n  {'Particule':>25s} {'Masse (eV)':>15s} {'n':>4s} {'type':>5s} {'k':>4s} {'cₙ':>12s} {'M_Pl·cₙ (eV)':>18s} {'f':>10s} {'|ln f|':>8s}")
print(f"  {'-'*102}")

results = []

for nom, masse in sorted(PARTICULES.items(), key=lambda x: x[1]):
    if masse == 0:
        print(f"  {nom:>25s} {masse:>15.1f} {'—':>4s} {'—':>5s} {'—':>4s} {'—':>12s} {'—':>18s} {'—':>10s} {'—':>8s}")
        results.append({"nom": nom, "masse": masse, "n": None, "type": None, "k": None, "cn": None, "f": None, "lnf": None})
        continue
    
    best = {"lnf": 1e6}
    for n_complet in range(1, N_TYPES + MAX_ITER * N_TYPES + 1):
        cn = c(n_complet)
        m_n = M_PL_EV * cn
        if m_n == 0:
            continue
        f = m_n / masse
        if f <= 0:
            continue
        lnf = abs(math.log(f))
        
        n_type = ((n_complet - 1) % 7) + 1
        k = (n_complet - 1) // 7
        
        if lnf < best["lnf"]:
            best = {"n": n_complet, "type": n_type, "k": k, "cn": cn, "m_n": m_n, "f": f, "lnf": lnf}
    
    if best["lnf"] < 1e5:
        print(f"  {nom:>25s} {masse:>15.4e} {best['n']:4d} {best['type']:5d} {best['k']:4d} {best['cn']:12.4e} {best['m_n']:18.4e} {best['f']:10.4f} {best['lnf']:8.4f}")
    else:
        print(f"  {nom:>25s} {masse:>15.4e} {'?':>4s} {'?':>5s} {'?':>4s} {'?':>12s} {'?':>18s} {'?':>10s} {'?':>8s}")
    
    results.append({"nom": nom, "masse": masse, **best})

print()

# ══════════════════════════════════════════════════════════════════════
# ANALYSE — CARTE PAR TYPE
# ══════════════════════════════════════════════════════════════════════
print("=" * 72)
print("CARTE PAR TYPE MODULO 7")
print("=" * 72)

for n_type in range(1, 8):
    print(f"\n  TYPE {n_type} :")
    for r in results:
        if r.get("type") == n_type:
            k = r.get("k", -1)
            nom = r["nom"]
            f = r.get("f", "?")
            if isinstance(f, float):
                print(f"    k={k} : {nom:>25s} (masse={r['masse']:.4e} eV, f={f:.4f})")
            elif r.get("n") is None:
                print(f"    —   : {nom:>25s} (masse={r['masse']:.4e} eV, sans niveau)")

# ══════════════════════════════════════════════════════════════════════
# PRÉDICTIONS
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("NIVEAUX SANS PARTICULE ASSIGNÉE (PRÉDICTIONS)")
print("=" * 72)

assignes = {r.get("n") for r in results if r.get("n") is not None}
print(f"\n  {'n':>4s} {'type':>5s} {'k':>4s} {'cₙ':>12s} {'M_Pl·cₙ':>18s} {'f cible':>10s}")
print(f"  {'-'*55}")
for n_complet in range(1, 50):
    if n_complet in assignes:
        continue
    cn = c(n_complet)
    m_n = M_PL_EV * cn
    n_type = ((n_complet - 1) % 7) + 1
    k = (n_complet - 1) // 7
    print(f"  {n_complet:4d} {n_type:5d} {k:4d} {cn:12.4e} {m_n:18.4e} {'—':>10s}")

# Sauvegarde
rapport = {
    "piste": "Carte complète des particules modulo 7",
    "resultats": [r for r in results],
    "conclusion": "La carte modulo 7 assigne les particules connues aux types 1-7 avec des itérations k. Les niveaux vides sont des prédictions de nouvelles particules.",
    "date": time.strftime("%Y-%m-%d %H:%M:%S")
}

chemin = os.path.join("data", "benchmarks", "carte_particules_T6_rapport.json")
os.makedirs(os.path.dirname(chemin), exist_ok=True)
with open(chemin, "w", encoding="utf-8") as f:
    json.dump(rapport, f, indent=2, ensure_ascii=False)
print(f"\nRapport : {chemin}")