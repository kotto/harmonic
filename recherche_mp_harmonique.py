#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recherche Systematique : Expression Harmonique Exacte de m_p/m_e
================================================================
Objectif : trouver m_p/m_e = Π H_n^α_n avec exposants entiers
et erreur < 0.01%, pour completer le pont N_PSU ↔ H_n.

Approche : recherche exhaustive sur l'espace des exposants entiers
{φ, π, e, √2, √3, √5, e/π} avec contraintes de parcimonie.

Auteur : KOTTO Alain — 19 Juin 2026
"""

import math
import itertools
from typing import List, Tuple, Dict

# ==============================================================================
# CONSTANTES
# ==============================================================================
phi = (1 + math.sqrt(5)) / 2
pi = math.pi
e = math.e
sqrt2 = math.sqrt(2)
sqrt3 = math.sqrt(3)
sqrt5 = math.sqrt(5)
e_sur_pi = e / pi

H = {
    'φ': phi, 'π': pi, 'e': e,
    '√2': sqrt2, '√3': sqrt3, '√5': sqrt5, 'e/π': e_sur_pi
}

LOGS = {k: math.log(v) for k, v in H.items()}

# Masse du proton / masse de l'electron
# Source : CODATA 2022
m_p_me_target = 1836.15267343
log_target = math.log(m_p_me_target)

# ==============================================================================
# STRATEGIE 1 : Recherche exhaustive avec contraintes de parcimonie
# ==============================================================================
print("=" * 80)
print("RECHERCHE SYSTEMATIQUE : m_p/m_e = Π H_n^α_n")
print("=" * 80)
print(f"\nm_p / m_e = {m_p_me_target:.8f}")
print(f"log(m_p/m_e) = {log_target:.6f}")
print()

def compute_error(exponents: Dict[str, int]) -> Tuple[float, float]:
    """Calcule le produit et l'erreur en %."""
    prod = 1.0
    for name, exp in exponents.items():
        if exp != 0:
            prod *= H[name] ** exp
    error = abs(prod - m_p_me_target) / m_p_me_target * 100
    return prod, error

# ==============================================================================
# STRATEGIE 1A : Approche resume — trouver les exposants par regression
# ==============================================================================
print("STRATEGIE 1A : Approximation par log-residus")
print("-" * 60)

# On decompose log(m_p/m_e) sur la base des logs des H_n
# log(target) = Σ α_n * log(H_n)
# On cherche les α_n entiers

# Contributions de chaque H_n a log(target)
for name, log_h in LOGS.items():
    ratio = log_target / log_h
    nearest_int = round(ratio)
    contribution = nearest_int * log_h
    residue = log_target - contribution
    print(f"  {name:<6s}  log={log_h:.6f}  target/log={ratio:8.3f}  nearest={nearest_int:4d}  contrib={contribution:8.4f}  residu={residue:8.4f}")

print()

# ==============================================================================
# STRATEGIE 1B : Recherche exhaustive a 2 variables
# ==============================================================================
print("STRATEGIE 1B : Recherche exhaustive a 2 symboles dominants")
print("-" * 60)

best_2 = []
for a in range(-5, 25):
    for b in range(-15, 15):
        approx = a * LOGS['φ'] + b * LOGS['π']
        # Completer avec e, √2, √3, √5, e/π pour le residu
        residual = log_target - approx
        
        # Tester chaque symbole seul pour le residu
        for name3, log3 in LOGS.items():
            if name3 not in ['φ', 'π']:
                c = round(residual / log3)
                approx3 = approx + c * log3
                residual3 = log_target - approx3
                
                for name4, log4 in LOGS.items():
                    if name4 not in ['φ', 'π', name3]:
                        d = round(residual3 / log4)
                        approx4 = approx3 + d * log4
                        residual4 = log_target - approx4
                        
                        for name5, log5 in LOGS.items():
                            if name5 not in ['φ', 'π', name3, name4]:
                                e_int = round(residual4 / log5)
                                
                                exp_dict = {'φ': a, 'π': b, name3: c, name4: d, name5: e_int}
                                for k in LOGS:
                                    if k not in exp_dict:
                                        exp_dict[k] = 0
                                
                                prod, err = compute_error(exp_dict)
                                if err < 0.5:
                                    best_2.append((err, exp_dict, prod))

best_2.sort(key=lambda x: x[0])
print(f"  Top 20 combinaisons (erreur < 0.5%) :")
print(f"  {'Err %':>8s}  {'φ':>4s}  {'π':>4s}  {'e':>4s}  {'√2':>4s}  {'√3':>4s}  {'√5':>4s}  {'e/π':>4s}  {'Valeur':>14s}")
print(f"  {'-'*8}  {'-'*4}  {'-'*4}  {'-'*4}  {'-'*4}  {'-'*4}  {'-'*4}  {'-'*4}  {'-'*14}")

for i, (err_pct, exp_dict, prod) in enumerate(best_2[:20]):
    vals = [exp_dict.get(k, 0) for k in ['φ', 'π', 'e', '√2', '√3', '√5', 'e/π']]
    print(f"  {err_pct:7.4f}%  {vals[0]:4d}  {vals[1]:4d}  {vals[2]:4d}  {vals[3]:4d}  {vals[4]:4d}  {vals[5]:4d}  {vals[6]:4d}  {prod:14.6f}")

print()

# ==============================================================================
# STRATEGIE 2 : Recherche avec le ratio m_p/m_e connu
# ==============================================================================
print("STRATEGIE 2 : Verification des expressions candidates avec m_e = reference")
print("-" * 60)

# m_e = 0.511 MeV est la reference dans le modele harmonique
# Les masses sont calculees par rapport a m_e
# On cherche m_p/m_e, donc m_p = m_e * (m_p/m_e)_harm

# L'expression la plus simple trouvee : φ^18 · π^(-1)
# Verifions-la
mp_me_candidate_1 = phi**18 * pi**(-1)
err_1 = abs(mp_me_candidate_1 - m_p_me_target) / m_p_me_target * 100

print(f"  Candidat 1 : φ^18 · π^(-1)")
print(f"    Valeur  = {mp_me_candidate_1:.6f}")
print(f"    Cible   = {m_p_me_target:.6f}")
print(f"    Erreur  = {err_1:.6f}%")
print()

# Amelioration : φ^18 · π^(-1) · e^(0) · √2^(0) · √3^(0) · √5^(0)
# L'ecart est de 0.215%. On peut corriger avec un petit facteur.
# Quelle puissance de quel H_n donne un facteur ~1.00215 ?
# φ^ε = 1.00215 → ε = log(1.00215)/log(φ) = 0.00447
# π^ε = 1.00215 → ε = log(1.00215)/log(π) = 0.00188
# Trop petit pour un exposant entier.
# 
# On va chercher des combinaisons a 3-4 symboles.

# ==============================================================================
# STRATEGIE 3 : Recherche exhaustive complete (6 symboles, exposants bornes)
# ==============================================================================
print("STRATEGIE 3 : Recherche exhaustive 4 symboles")
print("-" * 60)

best_4 = []
# Balayage systematique : φ et π dominants, e, √2, √3, √5, e/π ajustent
for a in range(10, 25):  # φ dominant (~18)
    for b in range(-10, 5):  # π (~ -1)
        approx_phi_pi = a * LOGS['φ'] + b * LOGS['π']
        residual = log_target - approx_phi_pi
        
        # Ajouter e
        c = round(residual / LOGS['e'])
        approx_3 = approx_phi_pi + c * LOGS['e']
        residual_3 = log_target - approx_3
        
        # Ajouter √2, √3, √5
        for d in range(-8, 9, 2):
            approx_4 = approx_3 + d * LOGS['√2']
            residual_4 = log_target - approx_4
            
            e_int = round(residual_4 / LOGS['√3'])
            approx_5 = approx_4 + e_int * LOGS['√3']
            residual_5 = log_target - approx_5
            
            f = round(residual_5 / LOGS['√5'])
            approx_6 = approx_5 + f * LOGS['√5']
            residual_6 = log_target - approx_6
            
            g = round(residual_6 / LOGS['e/π'])
            
            exp_dict = {'φ': a, 'π': b, 'e': c, '√2': d, '√3': e_int, '√5': f, 'e/π': g}
            prod, err = compute_error(exp_dict)
            
            # Ne garder que les solutions avec des exposants raisonnables
            # (pas de |exposant| > 10 pour les symboles secondaires)
            if (err < 0.2 and abs(c) <= 10 and abs(d) <= 8 and 
                abs(e_int) <= 8 and abs(f) <= 8 and abs(g) <= 8):
                best_4.append((err, exp_dict, prod))

best_4.sort(key=lambda x: x[0])

print(f"  Top 30 combinaisons (erreur < 0.2%) :")
print(f"  {'Err %':>8s}  {'φ':>4s}  {'π':>4s}  {'e':>4s}  {'√2':>4s}  {'√3':>4s}  {'√5':>4s}  {'e/π':>4s}  {'Valeur':>14s}  {'Somme |exp|':>10s}")
print(f"  {'-'*8}  {'-'*4}  {'-'*4}  {'-'*4}  {'-'*4}  {'-'*4}  {'-'*4}  {'-'*4}  {'-'*14}  {'-'*10}")

for i, (err_pct, exp_dict, prod) in enumerate(best_4[:30]):
    vals = [exp_dict.get(k, 0) for k in ['φ', 'π', 'e', '√2', '√3', '√5', 'e/π']]
    somme_abs = sum(abs(v) for v in vals)
    print(f"  {err_pct:7.4f}%  {vals[0]:4d}  {vals[1]:4d}  {vals[2]:4d}  {vals[3]:4d}  {vals[4]:4d}  {vals[5]:4d}  {vals[6]:4d}  {prod:14.6f}  {somme_abs:10d}")

print()

# ==============================================================================
# STRATEGIE 4 : Analyser les meilleures solutions pour trouver des motifs
# ==============================================================================
print("STRATEGIE 4 : Analyse des invariants dans les meilleures solutions")
print("-" * 60)

# Analysons les combinaisons a, b qui marchent le mieux
# Quel pattern emerge de φ et π ?

phi_contributions = {}
pi_contributions = {}

for err_pct, exp_dict, prod in best_4[:50]:
    a = exp_dict['φ']
    b = exp_dict['π']
    key = (a, b)
    if (a, b) not in phi_contributions:
        phi_contributions[(a, b)] = []
    phi_contributions[(a, b)].append(err_pct)

# Trier par erreur minimale pour chaque (a,b)
phi_best = sorted(phi_contributions.items(), key=lambda x: min(x[1]))

print("  Meilleurs couples (φ^a, π^b) :")
for (a, b), errs in phi_best[:15]:
    min_err = min(errs)
    n_solutions = len(errs)
    print(f"    φ^{a:2d} · π^{b:2d}  →  erreur min = {min_err:.4f}%  ({n_solutions} solutions)")

print()

# ==============================================================================
# STRATEGIE 5 : Tester la solution la plus elegante
# ==============================================================================
print("STRATEGIE 5 : Analyse de la solution la plus elegante")
print("-" * 60)

# Le pattern qui emerge :
# φ^18 · π^(-1) deja excellent (0.21%)
# On va chercher : φ^a · π^b · e^c · √2^d · √3^e · √5^f
# avec contrainte de "beaute" : exposants petits (< 5 pour symboles secondaires)

best_elegant = []
for err_pct, exp_dict, prod in best_4:
    vals = [exp_dict.get(k, 0) for k in ['φ', 'π', 'e', '√2', '√3', '√5', 'e/π']]
    secondary_sum = sum(abs(v) for v in vals[2:])  # somme |e| + |√2| + |√3| + |√5| + |e/π|
    if secondary_sum <= 8:  # contrainte de beaute
        best_elegant.append((err_pct, exp_dict, prod, secondary_sum))

best_elegant.sort(key=lambda x: (x[3], x[0]))  # trier par beaute puis erreur

print(f"  Solutions elegantes (|e|+|√2|+|√3|+|√5|+|e/π| ≤ 8) :")
print(f"  {'Err %':>8s}  {'φ':>4s}  {'π':>4s}  {'e':>4s}  {'√2':>4s}  {'√3':>4s}  {'√5':>4s}  {'e/π':>4s}  {'Valeur':>14s}  {'Σ|sec|':>8s}")
print(f"  {'-'*8}  {'-'*4}  {'-'*4}  {'-'*4}  {'-'*4}  {'-'*4}  {'-'*4}  {'-'*4}  {'-'*14}  {'-'*8}")

for i, (err_pct, exp_dict, prod, sec_sum) in enumerate(best_elegant[:20]):
    vals = [exp_dict.get(k, 0) for k in ['φ', 'π', 'e', '√2', '√3', '√5', 'e/π']]
    print(f"  {err_pct:7.4f}%  {vals[0]:4d}  {vals[1]:4d}  {vals[2]:4d}  {vals[3]:4d}  {vals[4]:4d}  {vals[5]:4d}  {vals[6]:4d}  {prod:14.6f}  {sec_sum:8d}")

print()

# ==============================================================================
# STRATEGIE 6 : Verification croisee avec m_P
# ==============================================================================
print("STRATEGIE 6 : Verification croisee m_p → N_PSU")
print("-" * 60)

# Si on a m_p/m_e en H_n, alors :
# m_p = m_e * Π H_n^α_n
# N_PSU(proton) = 64 * (m_P / m_p)^2
# = 64 * m_P^2 / (m_e^2 * Π H_n^(2α_n))
# m_P^2 est deja en H_n (Etape 6 de l'exploration)
# Donc N_PSU(proton) = 64 * (Π H_n^β_n) / (m_e^2 * Π H_n^(2α_n))
# = (64/m_e^2) * Π H_n^(β_n - 2α_n)

# Prenons le meilleur candidat elegant
if best_elegant:
    best_candidate = best_elegant[0]
    err_pct, exp_dict, prod, sec_sum = best_candidate
    
    print(f"  Meilleur candidat : m_p/m_e = {prod:.6f} (erreur {err_pct:.4f}%)")
    print(f"  Exposants : {exp_dict}")
    print()
    
    # m_P en exposants H_n (demi-exposants de m_P^2)
    H_mP = {'φ': -26.0, 'π': -11.5, 'e': -0.5, '√2': 1.0, '√3': -1.5, '√5': -0.5}
    
    # N_PSU(proton) = 64 * m_P^2 / m_p^2
    # En log : log(N_PSU) = log(64) + 2*log(m_P) - 2*log(m_p)
    log_64 = math.log(64)
    log_mP = sum(H_mP[k] * LOGS[k] for k in ['φ', 'π', 'e', '√2', '√3', '√5'])
    log_mp = sum(exp_dict[k] * LOGS[k] for k in exp_dict if k != 'e/π' and exp_dict[k] != 0) + math.log(9.1093837015e-31)  # m_e
    
    log_N_PSU = log_64 + 2 * log_mP - 2 * log_mp
    
    N_PSU_pred = math.exp(log_N_PSU)
    N_PSU_actual = 4 * (0.841e-15)**2 / (1.616255e-35)**2
    
    print(f"  N_PSU(proton) predit  = {N_PSU_pred:.4e}")
    print(f"  N_PSU(proton) reel    = {N_PSU_actual:.4e}")
    print(f"  Erreur                = {abs(N_PSU_pred - N_PSU_actual) / N_PSU_actual * 100:.6f}%")

print()
print("=" * 80)
print("RECHERCHE TERMINEE")
print("=" * 80)