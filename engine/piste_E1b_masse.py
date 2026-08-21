#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PISTE E1b — LA MASSE ABSOLUE : DE LA TOUR AU kg
==================================================
Objectif : dériver la masse de l'électron (et du proton) en kg 
depuis la tour et les constantes dérivées.

ÉTAT :
  ✅ Rapport m_p/m_e = (e²/π)⁴ × 60          (0,00027%) 
  ✅ Hiérarchie M_Pl/m_p = e⁴⁴                (1,23%)
  ✅ c₃₇ ≈ 5,88×10⁻²³ ≈ m_e/M_Pl × √2        (≈ 1,40×)
  ✅ c₃₃ ≈ 1,24×10⁻¹⁹ ≈ m_p/M_Pl × φ         (≈ 1,62×)
  ❌ m_e en kg non dérivé (l'échelle absolue)
  
HYPOTHÈSE :
  m = M_Pl × cₙ / f     où f ∈ {√2, φ, ...}
  Les indices n (33, 37) sont déterminés par les nombres quantiques.
  Le facteur f est la correction géométrique pour chaque particule.

PLAN :
  1. Reproduire les ordres de grandeur : cₙ, M_Pl, m_e, m_p
  2. Trouver les n exacts pour chaque particule
  3. Calculer les facteurs f exacts (corrections géométriques)
  4. Chercher le motif : pourquoi n=33,37 ?
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
    """Coefficient de la tour pour le niveau n"""
    return 1.0 / gamma_lanczos(n * ALPHA + 1)

C = 299792458.0
HBAR = 1.054571817e-34
EV = 1.602176634e-19
G_SI = 6.67430e-11

M_PL = math.sqrt(HBAR * C / G_SI)    # ≈ 2,176×10⁻⁸ kg
M_E = 9.1093837015e-31                # kg
M_P = 1.67262192369e-27               # kg

print("=" * 72)
print("PISTE E1b — LA MASSE ABSOLUE : DE LA TOUR AU kg")
print("=" * 72)

# ══════════════════════════════════════════════════════════════════════
# PARTIE 1 — CARTE DES ORDRES DE GRANDEUR
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("PARTIE 1 — CARTE DES ORDRES DE GRANDEUR")
print("=" * 72)

print(f"\n  M_Pl = {M_PL:.4e} kg")
print(f"  m_e  = {M_E:.4e} kg")
print(f"  m_p  = {M_P:.4e} kg")
print(f"  m_e/M_Pl = {M_E/M_PL:.4e}")
print(f"  m_p/M_Pl = {M_P/M_PL:.4e}")
print()

# Trouver le n autour duquel cₙ ≈ m_e/M_Pl
print("  RECHERCHE : n tel que cₙ ≈ m_e/M_Pl")
print(f"  {'n':>4s} {'cₙ':>18s} {'m_e/M_Pl':>14s} {'ratio':>10s}")
print(f"  {'-'*48}")
for n in range(30, 45):
    cn = c(n)
    ratio = cn / (M_E / M_PL)
    if 0.5 < ratio < 3:
        print(f"  {n:4d} {cn:18.6e} {M_E/M_PL:14.4e} {ratio:10.4f}")

print(f"\n  RECHERCHE : n tel que cₙ ≈ m_p/M_Pl")
print(f"  {'n':>4s} {'cₙ':>18s} {'m_p/M_Pl':>14s} {'ratio':>10s}")
print(f"  {'-'*48}")
for n in range(28, 45):
    cn = c(n)
    ratio = cn / (M_P / M_PL)
    if 0.5 < ratio < 3:
        print(f"  {n:4d} {cn:18.6e} {M_P/M_PL:14.4e} {ratio:10.4f}")

# ══════════════════════════════════════════════════════════════════════
# PARTIE 2 — FACTEURS DE CORRECTION EXACTS
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("PARTIE 2 — FACTEURS DE CORRECTION EXACTS")
print("=" * 72)

# Électron : m_e = M_Pl × c₃₇ / f_e
c37 = c(37)
f_e = M_PL * c37 / M_E
print(f"\n  ÉLECTRON (n=37) :")
print(f"    c₃₇ = {c37:.10e}")
print(f"    M_Pl × c₃₇ = {M_PL * c37:.4e} kg")
print(f"    m_e réel = {M_E:.4e} kg")
print(f"    f_e = M_Pl × c₃₇ / m_e = {f_e:.6f}")
print(f"    f_e ≈ √2 = {math.sqrt(2):.6f} ? écart = {abs(f_e - math.sqrt(2))/math.sqrt(2)*100:.3f}%")
print(f"    f_e ≈ φ = {PHI:.6f} ? écart = {abs(f_e - PHI)/PHI*100:.3f}%")
print(f"    f_e ≈ e/π = {math.e/math.pi:.6f} ? écart = {abs(f_e - math.e/math.pi)/(math.e/math.pi)*100:.3f}%")
print(f"    f_e ≈ 1/ALPHA = {1/ALPHA:.6f} ? écart = {abs(f_e - 1/ALPHA)/(1/ALPHA)*100:.3f}%")
print()

# Proton : m_p = M_Pl × c₃₃ / f_p
c33 = c(33)
f_p = M_PL * c33 / M_P
print(f"  PROTON (n=33) :")
print(f"    c₃₃ = {c33:.10e}")
print(f"    M_Pl × c₃₃ = {M_PL * c33:.4e} kg")
print(f"    m_p réel = {M_P:.4e} kg")
print(f"    f_p = M_Pl × c₃₃ / m_p = {f_p:.6f}")
print(f"    f_p ≈ φ = {PHI:.6f} ? écart = {abs(f_p - PHI)/PHI*100:.3f}%")
print(f"    f_p ≈ √2 = {math.sqrt(2):.6f} ? écart = {abs(f_p - math.sqrt(2))/math.sqrt(2)*100:.3f}%")
print(f"    f_p ≈ π/2 = {math.pi/2:.6f} ? écart = {abs(f_p - math.pi/2)/(math.pi/2)*100:.3f}%")
print(f"    f_p ≈ e/√φ = {math.e/math.sqrt(PHI):.6f} ? écart = {abs(f_p - math.e/math.sqrt(PHI))/(math.e/math.sqrt(PHI))*100:.3f}%")
print()

# Rapport m_p/m_e
RATIO_PE_EXACT = M_P / M_E
RATIO_PE_THU = (math.e**2 / math.pi)**4 * 60
print(f"  RAPPORT m_p/m_e :")
print(f"    Exact = {RATIO_PE_EXACT:.6f}")
print(f"    THU   = {RATIO_PE_THU:.6f}")
print(f"    écart = {abs(RATIO_PE_THU - RATIO_PE_EXACT)/RATIO_PE_EXACT*100:.6f}%")
print()

# Vérification de la cohérence : f_p/f_e doit égaler (c₃₃/c₃₇) × (m_e/m_p)
print(f"  COHÉRENCE : f_p/f_e = {f_p/f_e:.6f}")
print(f"    (c₃₃/c₃₇) × (m_e/m_p) = {c33/c37 * M_E/M_P:.6f}")
print()

# ══════════════════════════════════════════════════════════════════════
# PARTIE 3 — RECHERCHE DU MOTIF DANS LES n
# ══════════════════════════════════════════════════════════════════════
print("=" * 72)
print("PARTIE 3 — MOTIF DANS LES INDICES n")
print("=" * 72)
print("""
  Pourquoi n=33 pour le proton et n=37 pour l'électron ?
  
  Peut-être : n = f(nombres quantiques) ou
             n = position dans le cycle modulo 7 de la tour ?
""")

# Modulo 7
print(f"  33 mod 7 = {33 % 7}")
print(f"  37 mod 7 = {37 % 7}")
print(f"  Différence 37-33 = {37-33} = 4")
print()

# Autres hypothèses sur n
# n ≈ 2/α = 2φ ≈ 3.236? Non, les n sont bien 33 et 37.
# n ≈ (masse en unités naturelles)?
# n ≈ 1/(m/M_Pl)? Non, m_e/M_Pl ≈ 4e-23, n ≈ 37.

# Relation entre n et les constantes
print(f"  nₑ = 37 : nₑ × α = {37 * ALPHA:.4f}")
print(f"  nₚ = 33 : nₚ × α = {33 * ALPHA:.4f}")
print(f"  (nₑ - nₚ) × α = {(37-33) * ALPHA:.4f}")

# Vérification : n × α donne-t-il un nombre rond ?
for n_test in [33, 37]:
    val = n_test * ALPHA
    print(f"  n={n_test}: n·1/φ = {val:.6f} = {val:.0f} + {val - math.floor(val):.6f}")
print()

# Proximité avec des entiers ou des constantes
print(f"  nₑ = 37 : nₑ·α = {37*ALPHA:.4f} ≈ φ²·{37*ALPHA/PHI**2:.4f}")
print(f"  nₚ = 33 : nₚ·α = {33*ALPHA:.4f} ≈ √3·{33*ALPHA/math.sqrt(3):.4f}")
print()

# ══════════════════════════════════════════════════════════════════════
# PARTIE 4 — VERS LA SOLUTION
# ══════════════════════════════════════════════════════════════════════
print("=" * 72)
print("PARTIE 4 — SYNTHÈSE : LA MASSE EN TROIS ÉTAGES")
print("=" * 72)
print("""
  ÉTAGE 1 — La tour donne les RAPPORTS sans dimension :
    c₃₃ = 1/Γ(33/φ+1) ≈ 1,24×10⁻¹⁹  (ordre du proton)
    c₃₇ = 1/Γ(37/φ+1) ≈ 5,88×10⁻²³  (ordre de l'électron)
    
  ÉTAGE 2 — M_Pl donne l'ÉCHELLE absolue :
    M_Pl = √(ℏc/G) ≈ 2,176×10⁻⁸ kg
    Mais G (donc M_Pl) est une FRONTIÈRE (F5)
    
  ÉTAGE 3 — Le facteur géométrique f relie les deux :
    m_e = M_Pl × c₃₇ / f_e    avec f_e ≈ """ + f"{f_e:.4f}" + f"""
    m_p = M_Pl × c₃₃ / f_p    avec f_p ≈ {f_p:.4f}
""")

# Vérification : m_e prédite avec √2
m_e_pred = M_PL * c37 / math.sqrt(2)
print(f"  TEST : m_e = M_Pl × c₃₇/√2 = {m_e_pred:.4e} kg")
print(f"         m_e exact = {M_E:.4e} kg")
print(f"         écart = {abs(m_e_pred - M_E)/M_E*100:.3f}%")

m_p_pred = M_PL * c33 / PHI
print(f"  TEST : m_p = M_Pl × c₃₃/φ = {m_p_pred:.4e} kg")
print(f"         m_p exact = {M_P:.4e} kg")
print(f"         écart = {abs(m_p_pred - M_P)/M_P*100:.3f}%")

# Amélioration : chercher le facteur exact
print(f"""
  Pour fermer E1b, il faut :
    1. ✅ Dériver le rapport m_p/m_e (déjà fait : (e²/π)⁴×60, 0,00027%)
    2. ✅ Associer chaque particule à un niveau n (33, 37 — approximatif)
    3. ❌ Dériver n en fonction des nombres quantiques (spin, charge, ...)
    4. ❌ Dériver le facteur géométrique f (√2 pour e⁻, φ pour p⁺)
    5. ❌ Dériver G (ou ℏ) pour fixer l'échelle absolue → M_Pl
    
  → E1b est FERMABLE pour les RAPPORTS, mais OUVERT pour l'ÉCHELLE.
  → La HIÉRARCHIE (M_Pl/m_e ≈ φ¹⁰⁷) donne l'ordre, pas l'exactitude.
  → Prochaine étape : Deriver f_e et f_p exactement depuis les constantes.
""")

# Sauvegarde
rapport = {
    "piste": "E1b — La masse absolue : de la tour au kg",
    "resultats": {
        "M_Pl": M_PL, "m_e": M_E, "m_p": M_P,
        "m_e_sur_M_Pl": M_E/M_PL, "m_p_sur_M_Pl": M_P/M_PL,
        "n_e": 37, "c37": c37, "f_e": f_e,
        "n_p": 33, "c33": c33, "f_p": f_p,
        "m_e_pred_v2": m_e_pred, "ecart_e_pred": abs(m_e_pred-M_E)/M_E*100,
        "m_p_pred_phi": m_p_pred, "ecart_p_pred": abs(m_p_pred-M_P)/M_P*100,
        "rapport_m_p_m_e_THU": RATIO_PE_THU,
        "conclusion": "E1b est partiellement fermé : les rapports m_p/m_e sont dérivés (0,00027%), les ordres c₃₃/c₃₇ correspondent. L'échelle absolue (M_Pl) et les facteurs f restent à dériver."
    },
    "date": time.strftime("%Y-%m-%d %H:%M:%S")
}

chemin = os.path.join("data", "benchmarks", "piste_E1b_masse_rapport.json")
os.makedirs(os.path.dirname(chemin), exist_ok=True)
with open(chemin, "w", encoding="utf-8") as f:
    json.dump(rapport, f, indent=2, ensure_ascii=False)
print(f"Rapport : {chemin}")