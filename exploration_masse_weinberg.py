#!/usr/bin/env python3
r"""
EXPLORATION NUMÉRIQUE — Rapport de masse muon/électron et sin²θ_W
==================================================================
Cherche des combinaisons de φ, π, e, √2, √3 avec exposants
ENTIERS (ou rationnels simples) qui reproduisent les valeurs
expérimentales.

Usage :
  python exploration_masse_weinberg.py
"""

import math
import itertools
import numpy as np

PHI = (1 + math.sqrt(5)) / 2
PI = math.pi
E = math.e
SQ2 = math.sqrt(2)
SQ3 = math.sqrt(3)

# Cibles expérimentales
TARGET_MU_OVER_ME = 206.7682827    # CODATA 2018
TARGET_SIN2_W = 0.2229              # sin²θ_W à l'échelle m_Z (PDG 2022)
TARGET_ALPHA = 1 / 137.035999084   # CODATA 2018


def evaluate(exponents, constants='all'):
    """Évalue φ^a · π^b · e^c · √2^d · √3^e pour exposants donnés."""
    result = 1.0
    if 'all' in constants or 'phi' in constants:
        result *= PHI ** exponents.get('phi', 0)
    if 'all' in constants or 'pi' in constants:
        result *= PI ** exponents.get('pi', 0)
    if 'all' in constants or 'e' in constants:
        result *= E ** exponents.get('e', 0)
    if 'all' in constants or 'sq2' in constants:
        result *= SQ2 ** exponents.get('sq2', 0)
    if 'all' in constants or 'sq3' in constants:
        result *= SQ3 ** exponents.get('sq3', 0)
    return result


def search_combinations(target, tolerance=0.01, max_abs_exponent=10, step=1):
    """
    Recherche brute : φ^a · π^b · e^c · √2^d · √3^e
    avec a,b,c,d,e entiers dans [-max_abs_exponent, max_abs_exponent].
    """
    results = []
    exponents_range = range(-max_abs_exponent, max_abs_exponent + 1, step)
    
    for a in exponents_range:
        for b in exponents_range:
            for c in exponents_range:
                for d in exponents_range:
                    for e_val in exponents_range:
                        val = evaluate({'phi': a, 'pi': b, 'e': c, 'sq2': d, 'sq3': e_val})
                        if val <= 0:
                            continue
                        error = abs(val - target) / target
                        if error < tolerance:
                            results.append({
                                'exponents': {'φ': a, 'π': b, 'e': c, '√2': d, '√3': e_val},
                                'value': val,
                                'error': error,
                                'err_pct': error * 100,
                            })
    
    return sorted(results, key=lambda x: x['error'])[:20]


def search_ratio(target, tolerance=0.01, max_exp=8):
    """
    Recherche améliorée : combinaisons de puissances ET de rapports.
    
    Formes testées :
      φ^a · π^b / (e^c · √2^d · √3^e)
      φ^a · e^b / (π^c · √2^d · √3^e)
      π^a · e^b / (φ^c · √2^d · √3^e)
      etc.
    """
    results = []
    
    for num_const in [['phi', 'pi'], ['phi', 'e'], ['pi', 'e']]:
        for den_const in [['phi', 'pi'], ['phi', 'e'], ['pi', 'e']]:
            if set(num_const) == set(den_const):
                continue
            
            for a in range(-max_exp, max_exp + 1):
                for b in range(-max_exp, max_exp + 1):
                    for c in range(-max_exp, max_exp + 1):
                        for d in range(-max_exp, max_exp + 1):
                            for sq2_exp in range(-3, 4):
                                for sq3_exp in range(-3, 4):
                                    num = evaluate({num_const[0]: a, num_const[1]: b})
                                    den = evaluate({den_const[0]: c, den_const[1]: d, 'sq2': sq2_exp, 'sq3': sq3_exp})
                                    if den == 0:
                                        continue
                                    val = num / den * (SQ2 ** sq2_exp) * (SQ3 ** sq3_exp)
                                    if val <= 0:
                                        continue
                                    error = abs(val - target) / target
                                    if error < tolerance:
                                        results.append({
                                            'value': val,
                                            'error': error,
                                            'err_pct': error * 100,
                                        })
    
    return sorted(results, key=lambda x: x['error'])[:20]


def search_alpha_related(target, alpha=TARGET_ALPHA, tolerance=0.01):
    """
    Recherche des combinaisons du type :
      (π^a · φ^b · e^c) / α^d
      α · π^a · φ^b
      etc.
    
    Beaucoup de rapports de masses sont liés à α.
    """
    results = []
    
    for a in range(-8, 9):
        for b in range(-8, 9):
            for c in range(-8, 9):
                for d in range(-3, 4):
                    for sq2_exp in range(-3, 4):
                        for sq3_exp in range(-3, 4):
                            val = (PI**a) * (PHI**b) * (E**c) * (SQ2**sq2_exp) * (SQ3**sq3_exp)
                            if d > 0:
                                val *= (1/alpha) ** d
                            elif d < 0:
                                val /= (1/alpha) ** abs(d)
                            
                            if val <= 0:
                                continue
                            error = abs(val - target) / target
                            if error < tolerance:
                                results.append({
                                    'formula': f"φ^{b}·π^{a}·e^{c}·(1/α)^{d}·√2^{sq2_exp}·√3^{sq3_exp}",
                                    'value': val,
                                    'error': error,
                                    'err_pct': error * 100,
                                })
    
    return sorted(results, key=lambda x: x['error'])[:30]


def print_results(title, results, target):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"  Cible : {target:.10f}")
    print(f"{'='*70}")
    
    if not results:
        print("  Aucun résultat trouvé.")
        return
    
    for i, r in enumerate(results[:10]):
        print(f"\n  #{i+1} — Valeur : {r['value']:.10f}  Erreur : {r['err_pct']:.6f}%")
        if 'exponents' in r:
            exp = r['exponents']
            formula = f"      φ^{exp.get('φ',0)} · π^{exp.get('π',0)} · e^{exp.get('e',0)} · √2^{exp.get('√2',0)} · √3^{exp.get('√3',0)}"
            print(formula)
        elif 'formula' in r:
            print(f"      {r['formula']}")


if __name__ == "__main__":
    print("=" * 74)
    print("  EXPLORATION NUMÉRIQUE — Masses & Weinberg")
    print("=" * 74)
    
    # ═══════════════════════════════════════════════════════════════════
    # 1. Rapport de masse muon/électron
    # ═══════════════════════════════════════════════════════════════════
    print("\n\n[RECHERCHE 1] Rapport de masse m_μ / m_e ≈ 206.768")
    print("-" * 60)
    
    # Recherche combinatoire pure
    res1 = search_combinations(TARGET_MU_OVER_ME, tolerance=0.05, max_abs_exponent=6)
    print_results("Combinaison φ^a · π^b · e^c · √2^d · √3^e", res1, TARGET_MU_OVER_ME)
    
    # Recherche avec α
    res1b = search_alpha_related(TARGET_MU_OVER_ME, tolerance=0.05)
    print_results("Combinaison avec 1/α", res1b, TARGET_MU_OVER_ME)
    
    # ═══════════════════════════════════════════════════════════════════
    # 2. Angle de Weinberg sin²θ_W
    # ═══════════════════════════════════════════════════════════════════
    print("\n\n[RECHERCHE 2] sin²θ_W ≈ 0.223 (échelle m_Z)")
    print("-" * 60)
    
    res2 = search_combinations(TARGET_SIN2_W, tolerance=0.05, max_abs_exponent=6)
    print_results("Combinaison φ^a · π^b · e^c · √2^d · √3^e", res2, TARGET_SIN2_W)
    
    # Recherche trigonométrique
    print("\n  --- Recherche trigonométrique ---")
    for angle_exp in [1, 2, 3, 4]:
        # sin(π/k) ?
        for k in range(1, 20):
            val = math.sin(PI / k) ** 2
            error = abs(val - TARGET_SIN2_W) / TARGET_SIN2_W
            if error < 0.1:
                print(f"  sin²(π/{k}) = {val:.6f}  (erreur: {error*100:.3f}%)")
        
        # sin(φ/k) ?
        for k in range(1, 20):
            val = math.sin(PHI / k) ** 2
            error = abs(val - TARGET_SIN2_W) / TARGET_SIN2_W
            if error < 0.1:
                print(f"  sin²(φ/{k}) = {val:.6f}  (erreur: {error*100:.3f}%)")
    
    # φ/(π^k) ?
    for k in range(1, 6):
        val = PHI / (PI ** k)
        error = abs(val - TARGET_SIN2_W) / TARGET_SIN2_W
        if error < 0.2:
            print(f"  φ/π^{k} = {val:.6f}  (erreur: {error*100:.3f}%)")
    
    for k in range(1, 6):
        val = 1.0 / (PHI ** k)
        error = abs(val - TARGET_SIN2_W) / TARGET_SIN2_W
        if error < 0.2:
            print(f"  1/φ^{k} = {val:.6f}  (erreur: {error*100:.3f}%)")
    
    # α lié ?
    val = TARGET_ALPHA
    error = abs(val - TARGET_SIN2_W) / TARGET_SIN2_W
    if error < 0.2:
        print(f"  α = {val:.6f}  (erreur: {error*100:.3f}%)")
    
    val = TARGET_ALPHA * PI
    error = abs(val - TARGET_SIN2_W) / TARGET_SIN2_W
    if error < 0.2:
        print(f"  α·π = {val:.6f}  (erreur: {error*100:.3f}%)")
    
    # sin²θ_W = (1 - 1/(π·φ)) ?
    val = 1.0 - 1.0/(PI * PHI)
    error = abs(val - TARGET_SIN2_W) / TARGET_SIN2_W
    print(f"\n  1 - 1/(π·φ) = {val:.6f}  (erreur: {error*100:.3f}%)")
    
    # sin²θ_W = 1/(4φ) ?
    val = 1.0 / (4 * PHI)
    error = abs(val - TARGET_SIN2_W) / TARGET_SIN2_W
    print(f"  1/(4φ) = {val:.6f}  (erreur: {error*100:.3f}%)")
    
    # ═══════════════════════════════════════════════════════════════════
    # 3. Récapitulatif des meilleures formules
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n\n{'='*70}")
    print("  RÉCAPITULATIF — Meilleures formules trouvées")
    print(f"{'='*70}")
    print(f"""
    RAPPORT m_μ/m_e ≈ 206.768 :
      Les meilleures combinaisons seront listées ci-dessus.
      Hypothèse : lié à α via 1/α = 137.036.
      Testé : α·3π/2 ?, φ^k·α ?, etc.
    
    sin²θ_W ≈ 0.223 :
      Hypothèse : angle de mélange géométrique.
      Testé : sin²(π/k), sin²(φ/k), φ/π^k, 1/φ^k, α·π, 1-1/(π·φ), 1/(4φ).
""")