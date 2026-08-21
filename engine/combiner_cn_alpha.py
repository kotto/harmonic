#!/usr/bin/env python3
"""Recherche : combiner cₙ + {π,e,φ,√2,√3} → α = π⁴·e⁻⁴·φ⁻⁵·√2⁻¹·√3⁻⁵"""
import math, os, time

PHI = (1 + math.sqrt(5)) / 2
ALPHA = 1 / PHI
PI, E = math.pi, math.e
SQRT2, SQRT3 = math.sqrt(2), math.sqrt(3)
TARGET = 137.035999084        # 1/α_CODATA
ALPHA_CODATA = 1.0 / TARGET   # 0,007297352569

# Coefficients cₙ
C = [1.0 / math.gamma(ALPHA * n + 1.0) for n in range(20)]

# Formule de référence
alpha_ref = PI**4 * E**-4 * PHI**-5 * SQRT2**-1 * SQRT3**-5
print(f"α référence = π⁴·e⁻⁴·φ⁻⁵·√2⁻¹·√3⁻⁵")
print(f"  1/α = {1/alpha_ref:.6f}  (CODATA: {TARGET})")
print(f"  précision = {abs(1/alpha_ref - TARGET)/TARGET*100:.6f}%\n")

# ============================================================
# Blocs de constantes (produits partiels de la formule)
blocs = {
    "π⁴·e⁻⁴·√2⁻¹·√3⁻⁵": PI**4 * E**-4 * SQRT2**-1 * SQRT3**-5,
    "π⁴·e⁻⁴·φ⁻⁵·√2⁻¹":  PI**4 * E**-4 * PHI**-5 * SQRT2**-1,
    "π⁴·e⁻⁴·φ⁻⁵·√3⁻⁵": PI**4 * E**-4 * PHI**-5 * SQRT3**-5,
    "π⁴·e⁻⁴·√2⁻¹":     PI**4 * E**-4 * SQRT2**-1,
    "π⁴·e⁻⁴·√3⁻⁵":     PI**4 * E**-4 * SQRT3**-5,
    "φ⁻⁵·√2⁻¹·√3⁻⁵":   PHI**-5 * SQRT2**-1 * SQRT3**-5,
    "π⁴·e⁻⁴":           PI**4 * E**-4,
    "π⁴":               PI**4,
    "e⁻⁴":              E**-4,
    "φ⁻⁵":              PHI**-5,
    "√2⁻¹":             SQRT2**-1,
    "√3⁻⁵":             SQRT3**-5,
}

# Bases = fonctions des cₙ
bases = {
    "c₁":      C[1],
    "c₂":      C[2],
    "c₃":      C[3],
    "c₁·c₂":      C[1]*C[2],
    "c₁/c₂":      C[1]/C[2],
    "c₂/c₃":      C[2]/C[3],
    "c₁·c₂·c₃":   C[1]*C[2]*C[3],
    "c₁²":         C[1]**2,
    "c₂²":         C[2]**2,
    "(c₁/c₂)²":    (C[1]/C[2])**2,
    "(c₁/c₂)³":    (C[1]/C[2])**3,
    "1/c₁":        1.0/C[1],
    "1/c₂":        1.0/C[2],
    "c₁/(c₂·c₃)":  C[1]/(C[2]*C[3]),
}

print(f"{'Combinaison':<45s} {'Valeur α':>12s} {'Écart':>8s} {'Cible':>6s}")
print(f"{'─'*45} {'─'*12} {'─'*8} {'─'*6}")

resultats = []
for nom_b, val_b in bases.items():
    for nom_bloc, val_bloc in blocs.items():
        val = val_b * val_bloc
        inv = 1.0/val

        # Test comme α (doit donner 0.00729735)
        ea = abs(val - ALPHA_CODATA) / ALPHA_CODATA * 100
        # Test comme 1/α (doit donner 137.036)
        ei = abs(inv - TARGET) / TARGET * 100

        pire = min(ea, ei)
        if pire < 5:
            cible = "α" if ea < ei else "1/α"
            affi = val if ea < ei else inv
            resultats.append((pire, f"{nom_b}·{nom_bloc}", affi, cible))

if not resultats:
    print("  Aucun candidat < 5% d'écart trouvé.")
else:
    resultats.sort(key=lambda x: x[0])
    for ecart, nom, val, cible in resultats[:30]:
        flag = " 🏆" if ecart < 0.01 else " ✅" if ecart < 1 else " ⚠️"
        print(f"  {nom:<45s} {val:>12.6f} {ecart:>7.4f}% {cible:>6s}{flag}")

    best = resultats[0]
    print(f"\n{'═'*78}")
    print(f"MEILLEUR CANDIDAT : {best[1]}")
    print(f"  Valeur = {best[2]:.10f}")
    print(f"  Écart  = {best[0]:.6f}%")
    print(f"  Cible  = {best[3]}")
    print(f"  Statut = {'✅ DÉRIVATION TROUVÉE' if best[0] < 0.01 else '❌ NON DERIVÉ (écart > 0.01%)'}")
    print(f"{'═'*78}")

    # Rapport texte
    chemin = f"data/benchmarks/combiner_cn_alpha_{time.strftime('%Y%m%d_%H%M%S')}.txt"
    os.makedirs("data/benchmarks", exist_ok=True)
    with open(chemin, "w") as f:
        f.write(f"alpha_ref_formula = π⁴·e⁻⁴·φ⁻⁵·√2⁻¹·√3⁻⁵\n")
        f.write(f"alpha_ref        = {alpha_ref:.15f}\n")
        f.write(f"1/alpha_ref      = {1/alpha_ref:.10f}\n")
        f.write(f"1/alpha_CODATA   = {TARGET:.10f}\n")
        f.write(f"precision        = {abs(1/alpha_ref-TARGET)/TARGET*100:.6f}%\n\n")
        f.write(f"best_candidate   = {best[1]}\n")
        f.write(f"best_value       = {best[2]:.10f}\n")
        f.write(f"best_ecart       = {best[0]:.6f}%\n")
        f.write(f"statut           = {'DERIVE' if best[0] < 0.01 else 'NON_DERIVE'}\n")
    print(f"Rapport : {chemin}")