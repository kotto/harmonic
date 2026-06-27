# -*- coding: utf-8 -*-
"""
EXPLORATION APPROFONDIE : RATIO RESIDUEL ET 8e GENERATEUR
=========================================================
R = alpha_CODATA / alpha_entiers = 1.000000235503281

Objectifs :
  1. Comparer R a toutes les corrections QED connues
  2. Chercher l'expression de log(R) en base H_n
  3. Verifier les erreurs residuelles des 9 constantes (pattern commun ?)
  4. Tester si R ~ 1 + correction_physique
  5. Explorer les exposants demi-entiers (sqrt(H_n))
"""

import numpy as np
import math

phi = (1 + math.sqrt(5)) / 2
pi = math.pi
e_val = math.e
sqrt2 = math.sqrt(2)
sqrt3 = math.sqrt(3)
sqrt5 = math.sqrt(5)
e_over_pi = e_val / pi

H_EXACT = np.array([phi, pi, e_val, sqrt2, sqrt3, sqrt5, e_over_pi])
NOMS_H = ['phi', 'pi', 'e', 'sqrt2', 'sqrt3', 'sqrt5', 'e/pi']
LOGH = np.log(H_EXACT)

alpha_codata = 1 / 137.035999084
alpha_pred = pi**4 * e_val**(-4) * phi**(-5) * sqrt2**(-1) * sqrt3**(-5)
R = alpha_codata / alpha_pred

print("=" * 90)
print("EXPLORATION APPROFONDIE : LE RATIO RESIDUEL R")
print("=" * 90)

# ======================================================================
# PARTIE 1 : VALEUR PRECISE DE R
# ======================================================================
print()
print("PARTIE 1 : R ET SES VARIANTES")
print("-" * 90)
print(f"  R = alpha_CODATA / alpha_entiers = {R:.16f}")
print(f"  1 - R = {(1 - R):.3e}")
print(f"  (1-R) en ppb (parts per billion) = {(1 - R) * 1e9:.3f} ppb")
print(f"  R - 1 = {(R - 1):.3e}")
print(f"  (R-1) en ppb = {(R - 1) * 1e9:.3f} ppb")
print()
print(f"  log(R) = {math.log(R):.16e}")
print(f"  log(R) = {math.log(R)}  (notation standard)")

# ======================================================================
# PARTIE 2 : CORRECTIONS QED CONNUES
# ======================================================================
print()
print("PARTIE 2 : COMPARAISON AUX CORRECTIONS QED CONNUES")
print("-" * 90)

# Moment magnetique anormal de l'electron : a_e = (g-2)/2
# Schwinger (1948) : a_e = alpha/(2*pi) ~ 0.0011614
ae_schwinger = alpha_codata / (2 * pi)
ae_1loop = alpha_codata / (2 * pi)
ae_2loop = ae_1loop + (alpha_codata/pi)**2 * (-0.328478965579 + 1.181241456587 - 1.9098592)
ae_3loop = ae_2loop + (alpha_codata/pi)**3 * (1.181241456587)
# Valeur experimentale actuelle
a_e_exp = 0.00115965218059
a_e_theory = 0.001159652181643

print(f"  Correction Schwinger (1-loop) = alpha/(2*pi) = {ae_schwinger:.10e}")
print(f"  a_e experimental = {a_e_exp:.15f}")
print()
print(f"  Comparaison avec R :")
print(f"    1 + alpha/(2*pi)     = {1 + ae_schwinger:.16f}")
print(f"    1 + alpha/(2*pi) / R = {(1 + ae_schwinger) / R:.16f}")
print(f"    Erreur relative      = {abs(1 + ae_schwinger - R) / R * 100:.6f}%")
print()

# Correction du couplage EM avec echelle
# alpha(M_Z) ~ 1/127.954 (couplage a l'echelle electrofaible)
alpha_MZ = 1/127.954
R_vs_running = alpha_MZ / alpha_pred
print(f"  alpha(M_Z) = 1/127.954")
print(f"  R_running = alpha(M_Z) / alpha_pred = {R_vs_running:.16f}")
print(f"  alpha(M_Z) / alpha_CODATA = {alpha_MZ / alpha_codata:.16f}")
print()

# Corrections radiatives diverses
corrections = [
    ("R lui-meme", R, R/R),
    ("1 + alpha/(2*pi)", 1 + alpha_codata/(2*pi), (1 + alpha_codata/(2*pi))/R),
    ("1 + alpha/pi", 1 + alpha_codata/pi, (1 + alpha_codata/pi)/R),
    ("1 + alpha/(4*pi)", 1 + alpha_codata/(4*pi), (1 + alpha_codata/(4*pi))/R),
    ("1 + alpha^2/(2*pi)", 1 + alpha_codata**2/(2*pi), (1 + alpha_codata**2/(2*pi))/R),
    ("1 + alpha/(2*pi*phi)", 1 + alpha_codata/(2*pi*phi), (1 + alpha_codata/(2*pi*phi))/R),
    ("1 + alpha^2/pi", 1 + alpha_codata**2/pi, (1 + alpha_codata**2/pi)/R),
    ("exp(alpha/(2*pi))", math.exp(alpha_codata/(2*pi)), math.exp(alpha_codata/(2*pi))/R),
    ("exp(alpha/pi)", math.exp(alpha_codata/pi), math.exp(alpha_codata/pi)/R),
    ("exp(-alpha/pi)", math.exp(-alpha_codata/pi), math.exp(-alpha_codata/pi)/R),
    ("1 + alpha/(pi*sqrt2)", 1 + alpha_codata/(pi*sqrt2), (1 + alpha_codata/(pi*sqrt2))/R),
    ("1 + alpha/(pi*phi)", 1 + alpha_codata/(pi*phi), (1 + alpha_codata/(pi*phi))/R),
    ("1 + alpha*sqrt2/(2*pi)", 1 + alpha_codata*sqrt2/(2*pi), (1 + alpha_codata*sqrt2/(2*pi))/R),
    ("1 + 1/(2*pi*137)", 1 + 1/(2*pi*137.036), (1 + 1/(2*pi*137.036))/R),
]

print(f"  {'Correction':<35s} {'Valeur':<22s} {'Ratio/R':<22s} {'(Ratio-1)*1e9'}")
print(f"  {'-'*90}")
for nom, val, ratio in corrections:
    delta_ppb = (ratio - 1) * 1e9
    marker = " <--" if abs(delta_ppb) < 100 else ""
    print(f"  {nom:<35s} {val:<22.15f} {ratio:<22.15f} {delta_ppb:+.2f}{marker}")

# ======================================================================
# PARTIE 3 : log(R) DANS LA BASE H_n
# ======================================================================
print()
print("PARTIE 3 : log(R) DANS LA BASE DES LOG(H_n)")
print("-" * 90)

logR = math.log(R)
print(f"  log(R) = {logR:.16e}")
print()
print(f"  Exprimons log(R) comme combinaison de log(H_n) :")
print(f"  log(R) = sum e_n * log(H_n)")
print()

# Solution de norme minimale
LOGH_mat = LOGH.reshape(1, -1)
AAT = np.dot(LOGH_mat, LOGH_mat.T)[0, 0]
e_logR = (LOGH_mat.T @ np.array([[logR]])) / AAT
e_logR = e_logR.flatten()

print(f"  Coefficients de norme L2 minimale :")
for i, nom in enumerate(NOMS_H):
    print(f"    e_{nom:5s} = {e_logR[i]:+.10f}")
print()

# Testons si des combinaisons SIMPLES de H_n donnent R
print(f"  Test de combinaisons simples pour approcher R :")
print()

tests_simples = []
for i in range(7):
    # R = H_i^e_i -> e_i = log(R)/log(H_i)
    e_i = logR / LOGH[i]
    val = H_EXACT[i] ** e_i
    err = abs(val - R) / R * 1e9
    tests_simples.append((f"{NOMS_H[i]}^{e_i:+.6f}", val, err))
    
    # Demi-entiers : e_i = 0.5, -0.5, 1, -1, etc.
    for k in [-1, -0.5, 0.5, 1, 2]:
        val = H_EXACT[i] ** k
        err = abs(val - R) / R * 1e9
        tests_simples.append((f"{NOMS_H[i]}^{k:+.1f}", val, err))

# Combinaisons de 2 constantes
for i in range(7):
    for j in range(i+1, 7):
        for k1 in [-1, -0.5, 0.5, 1]:
            for k2 in [-1, -0.5, 0.5, 1]:
                val = (H_EXACT[i]**k1) * (H_EXACT[j]**k2)
                err = abs(val - R) / R * 1e9
                tests_simples.append((f"{NOMS_H[i]}^{k1:+.1f} * {NOMS_H[j]}^{k2:+.1f}", val, err))

tests_simples.sort(key=lambda x: x[2])
print(f"  {'Expression':<45s} {'Valeur':<22s} {'Erreur (ppb)'}")
print(f"  {'-'*90}")
for expr, val, err in tests_simples[:15]:
    print(f"  {expr:<45s} {val:<22.15f} {err:.2f}")

# ======================================================================
# PARTIE 4 : ERREURS RESIDUELLES DES 9 CONSTANTES
# ======================================================================
print()
print("PARTIE 4 : ANALYSE CORRELEE DES ERREURS RESIDUELLES")
print("-" * 90)

constantes = {
    'alpha':       ([-5,  4, -4, -1, -5,  0,  0], 0.007297352569284),
    'm_mu/m_e':    ([-3,  3,  1,  2,  3,  0,  0], 206.7710),
    'm_tau/m_mu':  ([ 1,  3,  2, -1, -5,  0,  0], 16.8168),
    'm_c/m_u':     ([-1, -2,  5,  4,  5,  0,  0], 579.55),
    'm_t/m_c':     ([ 5,  3,  3, -5, -4,  0,  0], 135.69),
    'alpha_s':     ([ 1,  0,  0, -1, -1,  0,  0], 0.1180),
    'sin2_thetaW': ([-1, -1,  0,  0,  0,  0,  0], 0.23122),
    'gamma1':      ([ 1,  0,  4,  4,  0, -4,  0], 14.13473),
    'm_Higgs/v':   ([-1,  0, -1,  0,  0,  1,  0], 0.50853),
}

print(f"  {'Grandeur':<18s} {'Prediction':<18s} {'CODATA':<18s} {'Erreur (%)':<14s} {'Ratio R_i':<18s} {'log10(R_i-1)'}")
print(f"  {'-'*100}")

ratios_residuels = []
for nom, (exp_list, codata_val) in constantes.items():
    pred = np.prod(H_EXACT ** np.array(exp_list))
    err_pct = abs(pred - codata_val) / codata_val * 100
    R_i = codata_val / pred
    log_Ri_minus_1 = math.log10(abs(R_i - 1)) if abs(R_i - 1) > 1e-16 else -16
    ratios_residuels.append((nom, R_i, err_pct))
    print(f"  {nom:<18s} {pred:<18.10f} {codata_val:<18.10f} {err_pct:<14.6f} {R_i:<18.15f} {log_Ri_minus_1:+.2f}")

# Correlation entre les R_i
print()
print(f"  Comparaison des ratios residuels R_i = CODATA / prediction :")
print()
R_alpha = ratios_residuels[0][1]  # R pour alpha
for nom, R_i, err in ratios_residuels:
    ratio_with_alpha = R_i / R_alpha
    print(f"    R({nom}) / R(alpha) = {R_i / R_alpha:.15f}  ({'CORRELE' if abs(ratio_with_alpha - 1) < 0.01 else 'NON CORRELE'})")

# ======================================================================
# PARTIE 5 : HYPOTHESE DU 8e GENERATEUR
# ======================================================================
print()
print("PARTIE 5 : HYPOTHESE H1 - 8e GENERATEUR MANQUANT")
print("-" * 90)

# Si R = H_8^{e_8} avec e_8 entier
# H_8 = R^{1/e_8}
for e8 in [1, -1, 2, -2, 3, -3]:
    H8 = R ** (1/e8)
    print(f"  e_8 = {e8:+2d} : H_8 = {H8:.16f}")

print()
print(f"  H_8 avec e_8 = -1 : H_8 = {R**(-1):.16f}")
H8_inv = 1/R
print(f"    1 - H_8 = {1 - H8_inv:.3e}")
print(f"    (1 - H_8) * 1e7 = {(1 - H8_inv) * 1e7:.4f}")
print()

# Est-ce que H_8 est une combination connue de H_n ?
# H_8 est proche de 1, donc log(H_8) est petit
# Exprimons log(H_8) en base H_n
log_H8_inv = math.log(H8_inv)
AAT = np.dot(LOGH_mat, LOGH_mat.T)[0, 0]
sol_H8 = (LOGH_mat.T @ np.array([[log_H8_inv]])) / AAT
sol_H8 = sol_H8.flatten()

print(f"  log(H_8) (e_8=-1) = {log_H8_inv:.16e}")
print(f"  C'est proportionnel a la solution de norme min :")
for i, nom in enumerate(NOMS_H):
    print(f"    e_{nom:5s} = {sol_H8[i]:+.10f}")

# ======================================================================
# PARTIE 6 : RECHERCHE DE CORRECTIONS COMBINATOIRES
# ======================================================================
print()
print("PARTIE 6 : R EXPRIME AVEC DES EXPOSANTS DEMI-ENTIERS")
print("-" * 90)

# Est-ce que R = produit(H_n^{k_n}) avec k_n demi-entiers ?
# On cherche les k_n dans {-3, -2.5, -2, -1.5, -1, -0.5, 0, 0.5, 1, 1.5, 2, 2.5, 3}
print(f"  Test systematique des exposants demi-entiers (±3 max) :")

from itertools import product as itertools_product

half_ints = [-2, -1.5, -1, -0.5, 0, 0.5, 1, 1.5, 2]
best_half = {'expr': '', 'val': 0, 'err': float('inf')}

# Limiter la recherche pour eviter l'explosion combinatoire
# On fixe les 4 derniers exposants a 0, on cherche sur les 3 premiers
for k1, k2, k3 in itertools_product(half_ints, repeat=3):
    val = H_EXACT[0]**k1 * H_EXACT[1]**k2 * H_EXACT[2]**k3
    err = abs(val - R)
    if err < best_half['err']:
        best_half = {'expr': f"phi^{k1:+.1f} * pi^{k2:+.1f} * e^{k3:+.1f}", 
                     'val': val, 'err': err}

print(f"  Meilleure approximation (3 premieres constantes) :")
print(f"    {best_half['expr']:<45s} = {best_half['val']:.16f}")
print(f"    Erreur absolue = {best_half['err']:.2e}")
print(f"    Erreur relative = {abs(best_half['val'] - R) / R * 1e9:.2f} ppb")
print()

# Et si R = sqrt(1 + quelque chose) ?
# R^2 - 1 = ?
R2_minus_1 = R**2 - 1
print(f"  R^2 - 1 = {R2_minus_1:.16e}")
print(f"  (R^2 - 1) / (2 * alpha/(2*pi)) = {R2_minus_1 / (2 * alpha_codata / (2*pi)):.8f}")
print(f"  Est-ce que R = sqrt(1 + alpha/pi) ?")
test_sqrt = math.sqrt(1 + alpha_codata/pi)
print(f"    sqrt(1 + alpha/pi) = {test_sqrt:.16f}")
print(f"    Ratio = {test_sqrt / R:.16f}")

# ======================================================================
# PARTIE 7 : SYNTHESE
# ======================================================================
print()
print("=" * 90)
print("SYNTHESE DES DECOUVERTES")
print("=" * 90)

print()
print(f"  R = alpha_CODATA / alpha_entiers = {R:.16f}")
print(f"  R - 1 = {R - 1:.3e} = {(R - 1) * 1e9:.2f} ppb")
print()
print(f"  OBSERVATION CLE #1 : R - 1 = {R - 1:.3e}")
print(f"  alpha/(2*pi)        = {alpha_codata/(2*pi):.3e}")
print(f"  Ratio (R-1) / (alpha/(2*pi)) = {(R-1) / (alpha_codata/(2*pi)):.6f}")
print()
print(f"  OBSERVATION CLE #2 : Les 9 constantes ont des R_i differents ->")
print(f"  l'erreur n'est PAS une correction multiplicative universelle.")
print(f"  Chaque constante a son propre residu.")
print()
print(f"  OBSERVATION CLE #3 : Le 8e generateur (si e_8 = -1) vaudrait H_8 = {1/R:.16f}")
print(f"  C'est remarquablement proche de 1 (ecart = {1 - 1/R:.3e})")
print()
print(f"  HYPOTHESE LA PLUS PLAUSIBLE :")
print(f"  alpha_entiers est la valeur NUE (sans corrections radiatives).")
print(f"  alpha_CODATA est la valeur HABILLEE (avec corrections QED).")
print(f"  Le ratio R = 1.0000002355... est le facteur d'habillage QED.")
print(f"  Il devrait etre calculable perturbationnement en QED.")
print(f"  Si c'est vrai, alors alpha_nu = alpha_pred predit la constante")
print(f"  de couplage electromagnetique fondamentale avant renormalisation.")
print()
print("=" * 90)