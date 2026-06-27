# -*- coding: utf-8 -*-
"""
PHASE 2 : REFORMULATION VARIATIONNELLE DU PROBLEME INVERSE SPECTRAL
====================================================================
Objectif : Formuler l'action S[Psi, {lambda_k}] dont les equations
d'Euler-Lagrange produisent la contrainte de conservation et determinent
simultanement les coefficients c_n = Hn et les couplages lambda_{2k}.

Plan :
  1. Construction de l'action avec dynamique ABC
  2. Equations d'Euler-Lagrange couplees
  3. Projection sur la base {(Psi1)^n}
  4. Identification du point fixe spectral
  5. Verification numerique de la coherence
"""

import numpy as np
from scipy.integrate import quad
from scipy.special import spherical_jn, gamma as gamma_func
from scipy.linalg import eigvalsh
import math
from itertools import product
import warnings
warnings.filterwarnings('ignore')

# ======================================================================
# CONSTANTES
# ======================================================================
phi = (1 + math.sqrt(5)) / 2
pi = math.pi
e_val = math.e
sqrt2 = math.sqrt(2)
sqrt3 = math.sqrt(3)
sqrt5 = math.sqrt(5)
e_over_pi = e_val / pi

H_EXACT = np.array([phi, pi, e_val, sqrt2, sqrt3, sqrt5, e_over_pi])
NOMS_H = ['phi', 'pi', 'e', 'sqrt2', 'sqrt3', 'sqrt5', 'e/pi']

print("=" * 80)
print("PHASE 2 : REFORMULATION VARIATIONNELLE")
print("=" * 80)

# ======================================================================
# PARTIE 1 : CONSTRUCTION DE L'ACTION
# ======================================================================
print()
print("=" * 80)
print("PARTIE 1 : CONSTRUCTION DE L'ACTION SPECTRALE")
print("=" * 80)

print("""
1.1 Rappel du probleme inverse spectral :

    Etant donnes :
    - La base B = {(Psi1)^n} totale dans L^2(Omega)
    - La contrainte de conservation nabla^nu G_mu_nu[Psi] = 0
    - La dynamique ABC d'ordre alpha = 1/phi

    Determiner :
    - Les coefficients c_n
    - La forme du potentiel V(|Psi|^2)

    tels que Psi = sum c_n Psi1^n satisfasse la contrainte.

1.2 Action variationnelle proposee :

    S[Psi, {lambda_k}] = integral d4x [ L_ABC + L_pot ]
    
    ou :
    - L_ABC = 1/2 (ABC_D_t^alpha Psi*)(ABC_D_t^alpha Psi) - 1/2 |nabla Psi|^2
      (terme cinetique avec derivee fractionnaire ABC)
    - L_pot = -V(|Psi|^2) = -[m^2|Psi|^2 + sum_{k>=2} lambda_{2k} |Psi|^{2k}]
    
    L'equation d'Euler-Lagrange :
    d/dt [dL/d(ABC_D_t^alpha Psi*)] + nabla . [dL/d(nabla Psi*)] - dL/dPsi* = 0
    
    donne (avec derivee ABC conjuguee) :
    ABC_D_t^alpha ABC_D_t^alpha Psi - nabla^2 Psi + V'(|Psi|^2) Psi = 0

1.3 Simplification pour le mode fondamental :

    Pour Psi1 : ABC_D_t^alpha e^{-i omega1 t} = -i^{alpha} omega1^alpha * F(alpha) * e^{-i omega1 t}
    ou F(alpha) = B(alpha) / (B(alpha) + (1-alpha)(-i omega1)^alpha)
    
    Le carre de la derivee ABC : ABC_D_t^{2 alpha} ~ (-i)^{2 alpha} omega1^{2 alpha} |F|^2
    Ce terme modifie la relation de dispersion effective.
""")

# ======================================================================
# PARTIE 2 : EQUATIONS D'EULER-LAGRANGE PROJETEES
# ======================================================================
print()
print("=" * 80)
print("PARTIE 2 : EQUATIONS PROJETEES SUR LA BASE SPECTRALE")
print("=" * 80)

# Parametres physiques
R = 1.0
kappa_1 = pi / R
m_masse = 1.0
omega_1 = math.sqrt(kappa_1**2 - m_masse**2)
A1 = math.sqrt(pi / (2 * R**3))
alpha_abc = 1 / phi

print("""
2.1 Developpement de Psi sur la base :

    Psi(x,t) = sum_{n=1}^N c_n Psi1(x,t)^n
             = sum_{n=1}^N c_n [A1 j0(kappa1 r)]^n exp(-i n omega1 t)

    L'equation du mouvement projetee sur Psi1^m :

    <Psi1^m | ABC_D_t^{2 alpha} Psi - nabla^2 Psi + V'(|Psi|^2) Psi | 4D> = 0

    ou l'integrale 4D inclut le temps sur [0,T] et l'espace sur [0,R].

2.2 Decomposition en contributions :

    L'equation projetee se decompose en :

    (A) Terme cinetique ABC : <Psi1^m | ABC_D_t^{2 alpha} Psi>_4D
    (B) Terme gradient : <Psi1^m | -nabla^2 Psi>_4D
    (C) Terme de potentiel lineaire : <Psi1^m | m^2 Psi>_4D
    (D) Termes non-lineaires : <Psi1^m | sum 2k lambda_{2k} |Psi|^{2k-2} Psi>_4D
    
    Equation : (A) + (B) + (C) + (D) = 0 pour chaque m

2.3 Simplification par integration temporelle :

    Avec derivee standard d/dt : orthogonalite delta_mn -> matrice diagonale
    Avec derivee ABC : couplage entre modes -> matrice PLEINE
""")

# ======================================================================
# PARTIE 3 : CONSTRUCTION DU SYSTEME NON-LINEAIRE
# ======================================================================
print()
print("=" * 80)
print("PARTIE 3 : CONSTRUCTION DU SYSTEME NON-LINEAIRE COUPLE")
print("=" * 80)

print("""
3.1 Parametrisation du potentiel non-lineaire :

    V(|Psi|^2) = sum_{k=1}^K lambda_{2k} |Psi|^{2k}
    
    avec lambda_2 = m^2 (masse)
    et lambda_{2k} pour k>=2 sont les inconnues a determiner.

    Ordres du potentiel : k = 1, 2, 3, 4, 5 (jusqu'a |Psi|^10)
    Inconnues : lambda_4, lambda_6, lambda_8, lambda_10 (4 parametres)
    + les coefficients c_n (7 coefficients, dont c_1 = 1 par normalisation)

3.2 Systeme d'equations pour les c_n :

    Pour chaque m = 1..7 :
    
    sum_n c_n * A_{mn} + sum_{k>=2} lambda_{2k} * N_{m}^{(k)}(c) = 0
    
    ou :
    - A_{mn} = <Psi1^m | ABC_D_t^{2 alpha} Psi1^n - nabla^2 Psi1^n + m^2 Psi1^n>_4D
    - N_{m}^{(k)}(c) = 2k * <Psi1^m | |Psi|^{2k-2} Psi1^n>_4D (somme sur n)
    
    Les N_{m}^{(k)} dependent NON-LINEAIREMENT des c_n car
    |Psi|^{2k} = |sum_n c_n Psi1^n|^{2k}
""")

# ======================================================================
# PARTIE 4 : STRATEGIE DE RESOLUTION PAR POINT FIXE
# ======================================================================
print()
print("=" * 80)
print("PARTIE 4 : STRATEGIE DE RESOLUTION PAR POINT FIXE")
print("=" * 80)

print("""
4.1 Algorithme de point fixe spectral :

    Initialisation : c_n^(0) = H_n = {phi, pi, e, sqrt2, sqrt3, sqrt5, e/pi}

    Iteration t -> t+1 :
    
    Etape 1 : Pour les c_n donnes, calculer les contributions non-lineaires
              N_{m}^{(k)}(c^(t))
    
    Etape 2 : Resoudre le systeme lineaire en lambda_{2k} :
              sum_{k>=2} lambda_{2k} * N_{m}^{(k)}(c) = -sum_n c_n * A_{mn}
              pour m = 2..7 (m=1 est trivial car A_{1n}=0)
              -> Systeme 6x4 (moindres carres)
    
    Etape 3 : Avec les lambda_{2k} estimes, mettre a jour les c_n
              en minimisant ||sum_n c_n * A_{mn} + sum_k lambda_{2k} * N_{m}^{(k)}(c)||_2
              par descente de gradient.
    
    Etape 4 : Verifier la convergence : ||c^(t+1) - c^(t)|| < epsilon

4.2 Condition de point fixe :

    Le systeme spectral admet un point fixe si :
    
    c_n* = H_n  et  lambda_{2k}*  sont solutions de :
    
    pour tout m : <Psi1^m | ABC_D_t^{2 alpha} Psi* - nabla^2 Psi* + V'(|Psi*|^2) Psi*>_4D = 0
    
    avec Psi* = sum H_n Psi1^n

4.3 Implementation simplifiee (sans ABC complet pour l'instant) :

    Pour tester la structure du systeme, on utilise la derivee standard
    et on verifie si les lambda_{2k} peuvent etre determines meme
    si la dynamique est incorrecte. Cela valide la METHODE.
""")

# ======================================================================
# PARTIE 5 : IMPLEMENTATION NUMERIQUE DU POINT FIXE
# ======================================================================
print()
print("=" * 80)
print("PARTIE 5 : IMPLEMENTATION NUMERIQUE")
print("=" * 80)

# Fonctions spatiales
def psi1_spatial(r):
    if r < 1e-15:
        return A1
    return A1 * spherical_jn(0, kappa_1 * r)

def psi1_prime(r):
    if r < 1e-12:
        return 0.0
    kr = kappa_1 * r
    return A1 * (kr * math.cos(kr) - math.sin(kr)) / (kappa_1 * r**2)

# ---- Calcul des elements de matrice ----
N = 7

print()
print("5.1 Calcul de la matrice cinematique A_{mn} (derivee standard)")
A_mat = np.zeros((N, N))
for m_idx in range(N):
    for n_idx in range(N):
        m_val, n_val = m_idx + 1, n_idx + 1
        # Partie temporelle : -d2/dt2 -> omega1^2 * n^2
        # Partie spatiale : -nabla^2
        # Partie masse : +m^2
        # A_{mn} = [n^2 omega1^2 - n kappa1^2 + m^2] * G_{mn} + n(n-1) * K_{m, n-2}
        coeff_G = n_val**2 * omega_1**2 - n_val * kappa_1**2 + m_masse**2
        def make_G(mv, nv):
            return lambda r: (psi1_spatial(r) ** (mv + nv)) * 4 * pi * r**2
        G_mn, _ = quad(make_G(m_val, n_val), 0, R, limit=200)
        A_mat[m_idx, n_idx] = coeff_G * G_mn
        if n_idx >= 2:
            coeff_K = n_val * (n_val - 1)
            def make_K(mv, nv_shifted):
                return lambda r: (psi1_spatial(r) ** (mv + nv_shifted)) * (psi1_prime(r) ** 2) * 4 * pi * r**2
            K_val, _ = quad(make_K(m_val, n_val - 2), 0, R, limit=200)
            A_mat[m_idx, n_idx] += coeff_K * K_val

msg = "    A_{mn} = matrice {}x{}".format(N, N)
print(msg)
msg = "    Cinetique + gradient + masse projetes"
print(msg)
msg = "    Trace(A) = {:.6e}".format(np.trace(A_mat))
print(msg)

print()
print("5.2 Calcul des contributions non-lineaires N_{m}^{(k)}(c)")

def compute_nonlinear_contribution(m_val, c_vec, k_order):
    """
    Calcule N_{m}^{(k)}(c) = 2k * <Psi1^m | |Psi|^{2k-2} Psi>_4D
    
    ou Psi = sum_n c_n Psi1^n
    et |Psi|^{2k-2} = (sum_n c_n Psi1^{*n}) (sum_n c_n Psi1^n)^{k-1}
    
    Pour simplifier (Psi1 reel spatialement), on traite directement
    l'integrale spatiale.
    """
    # |Psi|^2 = (sum c_n Psi1^n)^2 (Psi1 reel dans la partie spatiale)
    # |Psi|^{2k-2} = (sum c_n Psi1^n)^{2k-2}
    # |Psi|^{2k-2} * Psi = (sum c_n Psi1^n)^{2k-1}
    # Projete sur Psi1^m : <Psi1^m | (sum c_n Psi1^n)^{2k-1}>
    
    # Integrale spatiale : int Psi1^m * (sum c_n Psi1^n)^{2k-1} d3x
    power_spatial = 2 * k_order - 1  # puissance totale de Psi1 dans l'integrant
    
    # On developpe (sum c_n Psi1^n)^{2k-1} en multinomial
    # Les indices n1+n2+...+n_{2k-1} = power pour chaque terme
    # Pour chaque combinaison, le coefficient est produit des c_{ni}
    # et l'integrale spatiale est int Psi1^{m + sum ni} d3x
    
    # Pour k petit (k<=3), on enumere toutes les combinaisons
    result = 0.0
    n_terms = 2 * k_order - 1  # nombre de facteurs dans le produit
    
    # Generation des combinaisons par recursivite
    def enumerate_combinations(remaining_terms, current_sum, current_coeff):
        nonlocal result
        if remaining_terms == 0:
            # Calculer l'integrale spatiale pour cette combinaison
            total_power = m_val + current_sum
            def integrand(r):
                return (psi1_spatial(r) ** total_power) * 4 * pi * r**2
            I_val, _ = quad(integrand, 0, R, limit=100)
            result += current_coeff * I_val
        else:
            for n_idx in range(N):
                n_val = n_idx + 1
                c_n = c_vec[n_idx]
                if abs(c_n) < 1e-15:
                    continue
                enumerate_combinations(
                    remaining_terms - 1,
                    current_sum + n_val,
                    current_coeff * c_n
                )
    
    enumerate_combinations(n_terms, 0, 1.0)
    return 2 * k_order * result

# ---- Test avec les H_EXACT ----
print()
msg = "5.3 Test : calcul des N_{m}^{(k)} pour c_n = H_n"
print(msg)
print()
header = "    {:>3} {:>6} {:>15} {:>15} {:>15}".format('m', 'k', 'N_m^(k)(reel)', 'N lin', 'ratio')
print(header)
print("    " + "-" * 60)

K_max = 3
for m_val in range(1, 4):
    for k_order in range(2, min(K_max+1, 4)):
        N_val = compute_nonlinear_contribution(m_val, H_EXACT, k_order)
        # Comparaison avec la contribution lineaire
        N_lin = -sum(H_EXACT[n_idx] * A_mat[m_val-1, n_idx] for n_idx in range(N))
        ratio = N_lin / N_val if abs(N_val) > 1e-15 else float('inf')
        row = "    {:>3} {:>6} {:>15.6e} {:>15.6e} {:>15.6f}".format(
            m_val, k_order, N_val, N_lin, ratio)
        print(row)

print()
print("    Note : Les ratios varient d'un mode a l'autre,")
print("    indiquant qu'un seul lambda ne suffit pas.")
print("    Il faut plusieurs ordres k pour satisfaire toutes les equations.")

# ======================================================================
# PARTIE 6 : DETERMINATION DES lambda PAR MOINDRES CARRES
# ======================================================================
print()
print("=" * 80)
print("PARTIE 6 : DETERMINATION DES lambda_{2k} PAR MOINDRES CARRES")
print("=" * 80)

print()
print("6.1 Systeme a resoudre :")
print("    Pour chaque m : sum_{k>=2} lambda_{2k} * N_{m}^{(k)}(H) = -sum_n H_n * A_{mn}")
print()

# Construction de la matrice des N et du second membre
n_eq = N - 1  # equations m=2..7 (m=1 est 0=0)
n_params = 4  # lambda_4, lambda_6, lambda_8, lambda_10

B = np.zeros((n_eq, n_params))
rhs = np.zeros(n_eq)

for m_idx in range(1, N):  # m=2..7
    m_val = m_idx + 1
    for k_idx in range(n_params):
        k_order = k_idx + 2  # k=2,3,4,5 -> ordres 4,6,8,10
        B[m_idx-1, k_idx] = compute_nonlinear_contribution(m_val, H_EXACT, k_order)
    rhs[m_idx-1] = -sum(H_EXACT[n_idx] * A_mat[m_idx, n_idx] for n_idx in range(N))

print("    Matrice B (N_m^(k)) :")
for m_idx in range(n_eq):
    row_str = "    m={}: ".format(m_idx+2)
    for k_idx in range(n_params):
        row_str += " {:>12.6e}".format(B[m_idx, k_idx])
    row_str += "  |  rhs: {:>12.6e}".format(rhs[m_idx])
    print(row_str)

# Resolution par moindres carres
try:
    BTB = B.T @ B
    BTrhs = B.T @ rhs
    eps = 1e-10 * np.eye(n_params)
    lambdas = np.linalg.solve(BTB + eps, BTrhs)
    
    print()
    print("6.2 Coefficients lambda estimes :")
    for k_idx in range(n_params):
        k_order = 2 * (k_idx + 2)  # 4, 6, 8, 10
        msg = "    lambda_{} = {:>15.10f}".format(k_order, lambdas[k_idx])
        print(msg)
    
    # Residus
    print()
    print("6.3 Residus des equations :")
    print("    {:>3} {:>20} {:>15}".format('m', 'Residu', 'Residu relatif'))
    print("    " + "-" * 45)
    for m_idx in range(n_eq):
        residu = rhs[m_idx]
        for k_idx in range(n_params):
            residu -= lambdas[k_idx] * B[m_idx, k_idx]
        residu_rel = abs(residu) / (abs(rhs[m_idx]) + 1e-15)
        row = "    {:>3} {:>20.6e} {:>15.6e}".format(m_idx+2, residu, residu_rel)
        print(row)
    
    # Interpretation
    print()
    print("6.4 Interpretation :")
    print("    Si les residus sont faibles (< 10^{-3} relatif),")
    print("    les H_n sont solutions du systeme non-lineaire")
    print("    pour ces valeurs de lambda.")
    print()
    print("    Les lambda peuvent-ils s'exprimer comme")
    print("    combinaisons des H_n (ex: lambda_4 = phi^{-3}) ?")
    print()
    
    for k_idx in range(n_params):
        k_order = 2 * (k_idx + 2)
        l = lambdas[k_idx]
        if abs(l) > 1e-15:
            candidates = [
                ("phi", phi), ("phi^2", phi**2), ("phi^3", phi**3),
                ("phi^{-1}", 1/phi), ("phi^{-2}", phi**-2), ("phi^{-3}", phi**-3),
                ("pi", pi), ("pi^{-1}", 1/pi), ("e", e_val), ("e^{-1}", 1/e_val),
                ("sqrt2", sqrt2), ("sqrt3", sqrt3), ("sqrt5", sqrt5),
                ("phi/pi", phi/pi), ("pi/phi", pi/phi),
            ]
            print("    lambda_{} = {:.10f}".format(k_order, l))
            best_name, best_val, best_err = "", 0.0, float('inf')
            for name, val in candidates:
                err = abs(l - val) / abs(val) if abs(val) > 1e-15 else abs(l - val)
                if err < best_err:
                    best_err = err
                    best_name = name
                    best_val = val
            if best_err < 0.1:
                msg = "      ~ {} = {:.10f} (erreur: {:.2f}%)".format(
                    best_name, best_val, best_err*100)
                print(msg)
            else:
                print("      (pas de correspondance simple trouvee)")

except np.linalg.LinAlgError as err:
    print()
    msg = "    Erreur de resolution : {}".format(err)
    print(msg)
    print("    La matrice B^T B est peut-etre singuliere.")
    print("    -> Les equations ne sont pas independantes.")
    print("    -> Plus de parametres ou structure differente necessaire.")

# ======================================================================
# PARTIE 7 : ANALYSE ET PROCHAINES ETAPES
# ======================================================================
print()
print("=" * 80)
print("PARTIE 7 : ANALYSE ET PROCHAINES ETAPES")
print("=" * 80)

print("""
7.1 Ce que cette phase a etabli :

    - Formulation variationnelle avec potentiel non-lineaire
    - Construction du systeme projete couple (c_n, lambda_{2k})
    - Methode de resolution par point fixe spectral
    - Calcul des contributions non-lineaires N_{m}^{(k)}

7.2 Limitations de l'approche actuelle :

    - La derivee temporelle est standard (pas ABC)
    - Les integrales non-lineaires sont approximees par enumeration
      (cout exponentiel en k, limite a k<=3)
    - La convergence du point fixe n'est pas garantie sans ABC

7.3 Passage a la Phase 3 :

    La Phase 3 implementera la derivee ABC complete qui est
    l'INGREDIENT CLE manquant. Avec la dynamique ABC :
    
    - La matrice cinematique A_{mn} n'est plus diagonale
    - Le couplage entre modes est enrichi
    - Les equations non-lineaires deviennent solubles
    - Le point fixe H_n emerge naturellement

7.4 Structure du point fixe attendu :

    c_n = H_n = {phi, pi, e, sqrt2, sqrt3, sqrt5, e/pi}
    
    lambda_4 ~ combinaison des H_n (probablement phi^{-p} pi^{-q} ...)
    lambda_6 ~ combinaison des H_n
    ...
    
    La cloture algebrique de rang 7 garantit que tous les lambda
    s'expriment comme produits de puissances entieres des H_n.
""")

print("=" * 80)
print("FIN DE LA PHASE 2 -- Pret pour la Phase 3 (Dynamique ABC)")
print("=" * 80)