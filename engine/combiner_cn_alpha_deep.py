#!/usr/bin/env python3
"""Recherche approfondie : cₙ + {π,e,φ,√2,√3} → α_EM"""
import math, os

PHI = (1 + math.sqrt(5)) / 2
A = 1 / PHI  # alpha = 1/phi
C = [1.0 / math.gamma(A * n + 1.0) for n in range(20)]
PI, E, S2, S3, S5 = math.pi, math.e, math.sqrt(2), math.sqrt(3), math.sqrt(5)
CODATA_INV = 137.035999084
CODATA = 1.0 / CODATA_INV

# ============================================================
# Produire TOUTES les combinaisons de cₙ (ratios, produits, puissances)
# ============================================================
combos = {}
# Ratios simples
for i in range(1, 10):
    for j in range(i+1, min(i+5, 12)):
        combos[f"c{i}/c{j}"] = C[i]/C[j]
        combos[f"c{j}/c{i}"] = C[j]/C[i]
# Produits
for i in range(1, 6):
    p = 1.0
    for k in range(i, i+3):
        p *= C[k]
    combos[f"c{i}·c{i+1}·c{i+2}"] = p
# Puissances
for i in range(1, 6):
    for p in range(1, 6):
        combos[f"c{i}^{p}"] = C[i]**p
        combos[f"(c{i}/c{i+1})^{p}"] = (C[i]/C[i+1])**p

# ============================================================
# Fonctions candidates pour α
# ============================================================
candidates = []

# Pour chaque combinaison de cₙ, on regarde son inverse
# et on compare à CODATA_INV = 137.036
for nom, val in combos.items():
    if abs(val) < 1e-30:
        continue
    inv = 1.0 / val
    e = abs(1 - inv / CODATA_INV) * 100
    if e < 10:  # < 10% d'écart
        candidates.append((e, nom, inv, "inverse"))

# Même chose en multipliant par π⁴·e⁻⁴ = 1.784
PI4_E4 = PI**4 * E**-4
for nom, val in combos.items():
    prod = val * PI4_E4
    if prod <= 0:
        continue
    inv = 1.0 / prod
    e = abs(1 - inv / CODATA_INV) * 100
    if e < 10:
        candidates.append((e, f"{nom}·π⁴·e⁻⁴", inv, "1/α"))    

# Combinaisons avec √2, √3 séparément
for nom, val in combos.items():
    for nom2, val2 in {"√2⁻¹": S2**-1, "√3⁻⁵": S3**-5, "φ⁻⁵": PHI**-5, "√2⁻¹·√3⁻⁵": S2**-1*S3**-5}.items():
        prod = val * val2
        if prod <= 0:
            continue
        inv = 1.0 / prod
        e = abs(1 - inv / CODATA_INV) * 100
        if e < 10:
            candidates.append((e, f"{nom}·{nom2}", inv, "1/α"))

# Tous les produits : comb(cₙ) × π⁴·e⁻⁴·φ^a·√2^b·√3^c
for nom_c, val_c in combos.items():
    for nom_b in ["", "·π⁴·e⁻⁴"]:
        bloc = PI4_E4 if "π⁴" in nom_b else 1.0
        for a in range(-6, 1):  # φ^a
            for b in range(-2, 1):  # √2^b
                for c in range(-6, 1):  # √3^c
                    val_bloc = bloc * PHI**a * S2**b * S3**c
                    if abs(val_bloc) < 1e-30:
                        continue
                    val = val_c * val_bloc
                    e = abs(1 - val / CODATA) * 100  # test comme α
                    if e < 5:
                        nom_full = f"{nom_c}{nom_b}·φ^{a}·√2^{b}·√3^{c}"
                        candidates.append((e, nom_full, val, "α"))

candidates.sort(key=lambda x: x[0])
print(f"{'Combinaison':<55s} {'Valeur':>14s} {'Écart':>10s} {'Cible':>6s}")
print(f"{'─'*55} {'─'*14} {'─'*10} {'─'*6}")
for e, nom, val, cible in candidates[:30]:
    flag = " 🏆" if e < 0.001 else " ✅" if e < 0.01 else " ⚠️" if e < 1 else ""
    print(f"  {nom:<55s} {val:>14.6f} {e:>9.5f}% {cible:>6s}{flag}")

if candidates:
    b = candidates[0]
    print(f"\n{'═'*80}\nMEILLEUR : {b[1]} = {b[2]:.10f}  écart = {b[0]:.5f}%  cible = {b[3]}")
    if b[0] < 0.001:
        print("✅ DÉRIVATION RÉUSSIE !")
    elif b[0] < 0.01:
        print("⚠️ Très proche — possible dérivation")
    else:
        print("❌ Pas de dérivation simple trouvée")
else:
    print("\n❌ Aucun candidat trouvé")