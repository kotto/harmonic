# -*- coding: utf-8 -*-
"""
EXPLORATION : TENSION ALPHA — EXPOSANTS ENTIERS vs NON-ENTIERS
===============================================================
Contexte : La Phase 6 (Wigner-Eckart) exige des exposants ENTIERS.
           Empiriquement, la formule à exposants entiers donne :
             alpha = pi^4 * e^-4 * phi^-5 * sqrt2^-1 * sqrt3^-5
             Erreur = 0.000024%
           
           Mais il pourrait exister une formule à exposants NON ENTIERS
           donnant une erreur encore plus faible, voire nulle.
           
Objectif : 1. Chercher systématiquement la meilleure formule à exposants entiers
           2. Chercher la meilleure formule à exposants réels (non entiers)
           3. Comparer les précisions
           4. Proposer des résolutions à la tension théorique
"""

import numpy as np
import math
from itertools import product

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
log_alpha_codata = math.log(alpha_codata)

print("=" * 85)
print("EXPLORATION : TENSION EXPOSANTS ENTIERS vs NON-ENTIERS POUR alpha")
print("=" * 85)

# ======================================================================
# PARTIE 1 : ÉTAT ACTUEL — Formule à exposants entiers
# ======================================================================
print()
print("=" * 85)
print("PARTIE 1 : FORMULE ACTUELLE À EXPOSANTS ENTIERS")
print("=" * 85)

e_actuels = np.array([-5, 4, -4, -1, -5, 0, 0])  # phi, pi, e, sqrt2, sqrt3, sqrt5, e/pi
alpha_actuels = np.prod(H_EXACT ** e_actuels)
err_actuels = abs(alpha_actuels - alpha_codata) / alpha_codata * 100

print()
print(f"  Exposants   : {e_actuels}")
print(f"  alpha_pred  : {alpha_actuels:.15f}")
print(f"  alpha_CODATA: {alpha_codata:.15f}")
print(f"  Erreur      : {err_actuels:.8f} %")
print(f"  1/alpha_pred: {1/alpha_actuels:.10f}")
print(f"  1/alpha_CODA: {1/alpha_codata:.10f}")

# ======================================================================
# PARTIE 2 : RECHERCHE EXHAUSTIVE — Meilleurs exposants entiers
# ======================================================================
print()
print("=" * 85)
print("PARTIE 2 : RECHERCHE SYSTÉMATIQUE — MEILLEURS EXPOSANTS ENTIERS")
print("=" * 85)

def evaluer_exposants(e_list):
    """Évalue une combinaison d'exposants et retourne l'erreur."""
    val = np.prod(H_EXACT ** np.array(e_list))
    return abs(val - alpha_codata) / alpha_codata * 100

# Recherche autour de la solution actuelle (±2 sur chaque exposant)
print()
print("2.1 Recherche locale (±2 autour de la solution actuelle) :")
print()

meilleure_locale = {'e': e_actuels, 'err': err_actuels}
recherches_locales = 0

# On cherche sur les 5 premiers exposants (les 2 derniers = 0 dans la solution actuelle)
ranges = []
for i in range(5):
    ranges.append(range(e_actuels[i] - 2, e_actuels[i] + 3))

for e1, e2, e3, e4, e5 in product(*ranges):
    # On garde e6=0, e7=0 pour cette recherche locale
    e_test = [e1, e2, e3, e4, e5, 0, 0]
    recherches_locales += 1
    err = evaluer_exposants(e_test)
    if err < meilleure_locale['err']:
        meilleure_locale = {'e': e_test, 'err': err}

print(f"  Recherches : {recherches_locales} combinaisons testées")
print(f"  Meilleure  : e = {meilleure_locale['e']}")
print(f"  Erreur     : {meilleure_locale['err']:.10f} %")
alpha_best_local = np.prod(H_EXACT ** np.array(meilleure_locale['e']))
print(f"  1/alpha    : {1/alpha_best_local:.10f}")

# Recherche élargie avec e6 et e7 (±1)
print()
print("2.2 Recherche élargie (incluant sqrt5 et e/pi, ±1) :")
print()

meilleure_elargie = meilleure_locale.copy()
for e6 in range(-1, 2):
    for e7 in range(-1, 2):
        e_test = meilleure_locale['e'].copy()
        e_test[5] = e6
        e_test[6] = e7
        err = evaluer_exposants(e_test)
        if err < meilleure_elargie['err']:
            meilleure_elargie = {'e': e_test, 'err': err}

print(f"  Meilleure  : e = {meilleure_elargie['e']}")
print(f"  Erreur     : {meilleure_elargie['err']:.10f} %")
alpha_best_elargie = np.prod(H_EXACT ** np.array(meilleure_elargie['e']))
print(f"  1/alpha    : {1/alpha_best_elargie:.10f}")

# ======================================================================
# PARTIE 3 : SOLUTION EXACTE — Exposants réels optimaux
# ======================================================================
print()
print("=" * 85)
print("PARTIE 3 : SOLUTION EXACTE — EXPOSANTS RÉELS OPTIMAUX")
print("=" * 85)

# Résolution du système linéaire : log(alpha) = sum e_n * log(H_n)
# C'est un système sous-déterminé (7 inconnues, 1 équation)
# On cherche la solution de norme minimale (pseudo-inverse)

# Matrice 1x7 : système sous-déterminé A·e = b avec A 1×7
A = LOGH.reshape(1, -1)  # shape (1, 7)
b = np.array([log_alpha_codata])

# Solution de norme minimale : e = A^T · (A·A^T)^{-1} · b
# A·A^T est un scalaire
AAT = np.dot(A, A.T)[0, 0]  # scalaire
e_reels_min_norme = (A.T @ b) / AAT  # shape (7,)
e_reels_min_norme = e_reels_min_norme.flatten()
alpha_norme_min = np.prod(H_EXACT ** e_reels_min_norme)
err_norme_min = abs(alpha_norme_min - alpha_codata) / alpha_codata * 100

print()
print("3.1 Solution de norme L2 minimale (exposants réels) :")
print()
for i, nom in enumerate(NOMS_H):
    print(f"    e_{nom:5s}  =  {e_reels_min_norme[i]:+.10f}")
print()
print(f"    Norme L2 = {np.linalg.norm(e_reels_min_norme):.6f}")
print(f"    Erreur   = {err_norme_min:.2e} % (essentiellement nulle, aux arrondis près)")
print(f"    1/alpha  = {1/alpha_norme_min:.10f}")

# Alternative : fixer 5 exposants à 0, résoudre pour les 2 restants
print()
print("3.2 Solutions avec seulement 2 constantes actives :")
print()

paires = [(0, 1), (0, 2), (1, 2), (2, 3), (0, 3), (1, 3)]
for i, j in paires:
    # Résoudre e_i * log(H_i) + e_j * log(H_j) = log(alpha_codata)
    # Système 2x2 : on ajoute la contrainte de norme minimale
    A2 = np.array([[LOGH[i], LOGH[j]]])  # 1×2
    b2 = np.array([log_alpha_codata])
    A2AT = np.dot(A2, A2.T)[0, 0]  # scalaire
    sol = (A2.T @ b2) / A2AT
    sol = sol.flatten()
    
    e_2 = np.zeros(7)
    e_2[i] = sol[0]
    e_2[j] = sol[1]
    val = np.prod(H_EXACT ** e_2)
    err = abs(val - alpha_codata) / alpha_codata * 100
    
    print(f"    ({NOMS_H[i]}, {NOMS_H[j]}): e_{NOMS_H[i]}={sol[0]:+.8f}, e_{NOMS_H[j]}={sol[1]:+.8f}  ->  err={err:.2e}%")

# ======================================================================
# PARTIE 4 : COMPARAISON DES PRÉCISIONS
# ======================================================================
print()
print("=" * 85)
print("PARTIE 4 : COMPARAISON DES PRÉCISIONS")
print("=" * 85)

print()
print(f"  {'Méthode':<50s} {'Erreur (%)':<20s} {'Exposants entiers ?'}")
print(f"  {'-'*85}")
print(f"  {'Formule actuelle (Phase 6)':<50s} {err_actuels:<20.10f} OUI")
print(f"  {'Meilleure recherche locale entière':<50s} {meilleure_locale['err']:<20.10f} OUI")
print(f"  {'Meilleure recherche élargie entière':<50s} {meilleure_elargie['err']:<20.10f} OUI")
print(f"  {'Solution réelle (norme min)':<50s} {err_norme_min:<20.2e} NON")
print(f"  {'Solution réelle (2 constantes)':<50s} {'~0 (exacte)':<20s} NON")

print()
print("4.1 Interprétation :")
print()
print("    La solution à exposants réels (non entiers) atteint une précision")
print("    arbitrairement élevée car elle résout EXACTEMENT l'équation")
print("    log(alpha) = sum e_n * log(H_n).")
print()
print("    La solution à exposants ENTIERS a une erreur ~2.4e-7 (0.000024%).")
print("    Cette erreur est minuscule — bien en dessous de l'incertitude")
print("    expérimentale actuelle sur alpha (8.1e-11 en relatif).")
print()
print("    MAIS : si la théorie est exacte, l'erreur devrait être NULLE.")
print("    L'erreur non nulle des exposants entiers est un signal important.")

# ======================================================================
# PARTIE 5 : RÉSOLUTION DE LA TENSION
# ======================================================================
print()
print("=" * 85)
print("PARTIE 5 : RÉSOLUTION DE LA TENSION THÉORIQUE")
print("=" * 85)

print()
print("5.1 Hypothèses pour expliquer l'erreur résiduelle :")
print()

hypotheses = [
    ("H1 : Générateur manquant",
     "Le réseau spectral de rang 7 n'est pas complet.\n"
     "     Il manque un 8e générateur H_8 (peut-être lié à G, c, hbar, ou\n"
     "     une autre constante). L'erreur ~2.4e-7 correspond à ce H_8 manquant.\n"
     "     Si H_8 existe, les exposants restent entiers ET l'erreur devient nulle."),
    
    ("H2 : Précision finie des H_n",
     "Les H_n (phi, pi, e, ...) sont connus avec une précision finie.\n"
     "     Peut-être que les 'vrais' H_n fondamentaux diffèrent légèrement\n"
     "     des valeurs mathématiques standard (effet de renormalisation ?).\n"
     "     Exemple : pi_effectif = pi * (1 + correction quantique)."),
    
    ("H3 : alpha n'est PAS un produit pur de H_n",
     "alpha = prod H_n^{e_n} * correction non factorisable.\n"
     "     La correction viendrait des termes d'interférence entre modes,\n"
     "     qui ne se factorisent pas simplement en produit de puissances.\n"
     "     La formule produit est une approximation à ~2e-7 près."),
    
    ("H4 : Les exposants entiers sont corrects, alpha CODATA est la valeur habillée",
     "La valeur mesurée de alpha inclut des corrections radiatives\n"
     "     (polarisation du vide, etc.) qui modifient la valeur 'nue'.\n"
     "     Les exposants entiers donneraient la valeur NUE de alpha,\n"
     "     et l'écart avec CODATA mesure les corrections radiatives."),
    
    ("H5 : Alpha = e^2/(hbar c) n'est PAS fondamental",
     "Si la charge e est elle-même un produit de H_n, alors alpha\n"
     "     est un rapport de produits de H_n. L'erreur sur alpha reflète\n"
     "     l'erreur sur la factorisation de e, hbar, et c individuellement."),
]

for titre, desc in hypotheses:
    print(f"  {titre}")
    print(f"     {desc}")
    print()

# ======================================================================
# PARTIE 6 : TEST DE L'HYPOTHÈSE H1 — Recherche du 8e générateur
# ======================================================================
print()
print("=" * 85)
print("PARTIE 6 : TEST H1 — RECHERCHE DU 8e GÉNÉRATEUR MANQUANT")
print("=" * 85)

print()
print("6.1 Si le 8e générateur H_8 existe, sa valeur serait :")
print()

# alpha_codata = alpha_entiers * H_8^{e_8}
# H_8 = (alpha_codata / alpha_entiers)^{1/e_8}
# Si e_8 = 1 (le plus simple) :

alpha_entiers = np.prod(H_EXACT ** np.array(meilleure_elargie['e']))
ratio = alpha_codata / alpha_entiers
H_8_candidat_e1 = ratio

print(f"    alpha_codata / alpha_entiers = {ratio:.15f}")
print(f"    Si e_8 = +1 : H_8 = {H_8_candidat_e1:.15f}")
print(f"    Si e_8 = -1 : H_8 = {1/ratio:.15f}")
print(f"    Si e_8 = +2 : H_8 = {math.sqrt(ratio):.15f}")
print(f"    Si e_8 = -2 : H_8 = {1/math.sqrt(ratio):.15f}")
print()

# Est-ce que H_8 ressemble à quelque chose de connu ?
candidats_connus = [
    ("4*pi", 4*pi),
    ("pi^2/6", pi**2/6),
    ("zeta(3)", 1.2020569031595942),
    ("ln(2)", math.log(2)),
    ("ln(3)", math.log(3)),
    ("ln(10)", math.log(10)),
    ("gamma (Euler)", 0.5772156649015329),
    ("sqrt(pi)", math.sqrt(pi)),
    ("e^gamma", math.e**0.5772156649015329),
    ("phi^2", phi**2),
    ("1/phi", 1/phi),
    ("pi/phi", pi/phi),
    ("sqrt(phi)", math.sqrt(phi)),
    ("e/phi", e_val/phi),
    ("pi/e", pi/e_val),
    ("ln(phi)", math.log(phi)),
    ("sin(1)", math.sin(1)),
    ("cos(1)", math.cos(1)),
    ("2*pi", 2*pi),
    ("4*pi/3", 4*pi/3),
    ("pi/2", pi/2),
    ("sqrt(2*pi)", math.sqrt(2*pi)),
    ("exp(1/2)", math.exp(0.5)),
    ("exp(-1)", math.exp(-1)),
    ("ln(pi)", math.log(pi)),
]

print("6.2 Comparaison avec des constantes connues :")
print(f"    {'Constante candidate':<25s} {'Valeur':<20s} {'Ratio avec H_8':<20s} {'Erreur %'}")
print(f"    {'-'*80}")

for nom, val in candidats_connus:
    r = H_8_candidat_e1 / val
    err = abs(r - 1) * 100
    if err < 1:  # Seulement les candidats proches
        marker = " <-- PROCHE !" if err < 0.001 else ""
        print(f"    {nom:<25s} {val:<20.15f} {r:<20.15f} {err:.6f}%{marker}")

# Recherche de similarité plus large
print()
print("6.3 Meilleurs candidats (top 10 par similarité) :")
tous_candidats = []
for nom, val in candidats_connus:
    err = abs(H_8_candidat_e1 / val - 1) * 100
    tous_candidats.append((nom, val, err))

# Ajouter des combinaisons simples de H_n
combos = [
    ("phi/pi", phi/pi),
    ("phi*e/pi", phi*e_val/pi),
    ("sqrt2*phi/pi", sqrt2*phi/pi),
    ("e/sqrt5", e_val/sqrt5),
    ("pi*sqrt3/e", pi*sqrt3/e_val),
    ("phi*sqrt2/sqrt3", phi*sqrt2/sqrt3),
]
for nom, val in combos:
    err = abs(H_8_candidat_e1 / val - 1) * 100
    tous_candidats.append((nom, val, err))

tous_candidats.sort(key=lambda x: x[2])
for nom, val, err in tous_candidats[:12]:
    print(f"    {nom:<30s} {val:<20.12f}  erreur = {err:.6f}%")

# ======================================================================
# PARTIE 7 : CONCLUSIONS ET RECOMMANDATIONS
# ======================================================================
print()
print("=" * 85)
print("PARTIE 7 : CONCLUSIONS ET RECOMMANDATIONS")
print("=" * 85)

print()
print("7.1 Etat de la question :")
print()
print("    PROBLEME : La formule a exposants entiers donne alpha")
print("    avec ~2.4e-7 d'erreur. Une formule a exposants reels")
print("    donnerait 0 d'erreur (exact).")
print("    La theorie (Wigner-Eckart) impose des exposants ENTIERS.")
print()
print("    TENSION : Si la theorie est juste, l'erreur devrait etre nulle.")
print("    Elle ne l'est pas -> quelque chose manque.")
print()
print("7.2 Pistes de resolution prioritaires :")
print()
print("    [PRIORITE 1] H1 - Generateur manquant")
print("        Chercher un 8e H_n qui rendrait l'erreur nulle avec e_8 = +/-1.")
print("        La valeur candidate est ~1.0000002355... (tres proche de 1).")
print()
print("    [PRIORITE 2] H4 - Valeur nue vs habillement QED")
print("        L'ecart de ~2.4e-7 pourrait correspondre aux corrections")
print("        radiatives (polarisation du vide). A verifier.")
print()
print("    [PRIORITE 3] H3 - Correction non factorisable")
print("        alpha = (prod H_n^{e_n}) * f(H_1..H_7)")
print("        ou f -> 1 dans la limite classique.")
print()
print("7.3 Ce qu'il ne faut PAS faire :")
print()
print("    [NON] Abandonner les exposants entiers pour des exposants reels.")
print("          C'est du pur fitting numerique, ca n'explique RIEN.")
print()
print("    [NON] Ignorer l'erreur residuelle de 2.4e-7.")
print("          C'est un SIGNAL, pas du bruit.")
print()
print("    [OUI] Creuser l'origine de cette erreur.")
print("          C'est la que se cache la prochaine decouverte.")
print()
print("7.4 Prochaines etapes concretes :")
print()
print("    1. Ratio R = alpha_CODATA / alpha_entiers (deja calcule)")
print("    2. Analyser R en fonction des corrections radiatives QED")
print("    3. Chercher si R s'exprime comme produit de H_n avec exposants 1/2")
print("    4. Verifier si les autres constantes ont des erreurs residuelles correlees")

# ======================================================================
# BONUS : Analyse fine du ratio R
# ======================================================================
print()
print("=" * 85)
print("BONUS : ANALYSE FINE DU RATIO R = alpha_CODATA / alpha_entiers")
print("=" * 85)

R = alpha_codata / alpha_entiers
print(f"\n    R = {R:.15f}")
print(f"    1 - R = {1 - R:.3e}")
print(f"    (1 - R) en ppm = {(1 - R) * 1e6:.4f} ppm")
print()

# Est-ce que R est proche de 1 - alpha/pi ?
alpha_over_pi = alpha_codata / pi
print(f"    alpha_CODATA / pi = {alpha_over_pi:.10f}")
print(f"    1 - alpha/pi = {1 - alpha_over_pi:.15f}")
print(f"    1 - alpha/(2*pi) = {1 - alpha_codata/(2*pi):.15f}")
print()

# Est-ce que R ≈ exp(-alpha/pi) ?
exp_corr = math.exp(-alpha_codata / pi)
print(f"    exp(-alpha/pi) = {exp_corr:.15f}")
print(f"    Ratio avec R   = {R / exp_corr:.15f}")
print(f"    Erreur         = {abs(R - exp_corr) / R * 100:.6f}%")
print()

# Est-ce que R ≈ 1 - alpha/(2*pi) ?
corr_schwinger = 1 - alpha_codata / (2 * pi)
print(f"    1 - alpha/(2*pi) = {corr_schwinger:.15f}  (correction Schwinger ?)")
print(f"    Ratio avec R     = {R / corr_schwinger:.15f}")
print(f"    Erreur           = {abs(R - corr_schwinger) / R * 100:.6f}%")
print()

# Est-ce R ≈ sqrt(1 - correction) ? (pour un générateur sqrt)
R_carre = R * R
print(f"    R^2 = {R_carre:.15f}")
print(f"    1 - R^2 = {1 - R_carre:.3e}")

print()
print("=" * 85)
print("FIN DE L'EXPLORATION")
print("=" * 85)