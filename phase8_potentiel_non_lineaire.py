# -*- coding: utf-8 -*-
"""
PHASE 8 : DERIVATION VIA POTENTIEL NON-LINEAIRE
================================================
Contexte : Fourier a donne la structure diagonale (Phase B).
           M_{nn} * c_n + termes_non_lineaires = 0
           
           Pour n=1 : M_{11} = 0 -> c_1 libre (le fondamental)
           Pour n>=2 : M_{nn} != 0 -> c_n = 0  SI l'equation est lineaire
           
           MAIS avec un potentiel non-lineaire V(|Psi|^2) :
             Box(Psi) + V'(|Psi|^2) * Psi = 0
           
           Les termes non-lineaires couplent les modes et permettent
           c_n != 0 pour n>=2. Les H_n emergent comme point fixe
           de ce systeme couple.

Objectif : 1. Formuler le potentiel non-lineaire complet
           2. Calculer les coefficients de couplage N_{nklm...}
           3. Resoudre le systeme couple et verifier H_n
           4. Identifier la forme exacte de V(|Psi|^2)
"""

import numpy as np
import math
from scipy.integrate import quad
from scipy.special import spherical_jn

# ======================================================================
# CONSTANTES
# ======================================================================
phi = (1 + math.sqrt(5)) / 2
pi = math.pi
e_val = math.e
sqrt2 = math.sqrt(2)
sqrt3 = math.sqrt(3)
sqrt5 = math.sqrt(5)

H_EXACT = np.array([phi, pi, e_val, sqrt2, sqrt3, sqrt5, e_val/pi])
NOMS_H = ['phi', 'pi', 'e', 'sqrt2', 'sqrt3', 'sqrt5', 'e/pi']
N_MODES = 7

# Parametres de la cavite
R = 1.0
kappa_1 = pi / R
m_masse = 1.0
omega_1 = math.sqrt(kappa_1**2 - m_masse**2)
T = 2 * pi / omega_1
A1 = math.sqrt(pi / (2 * R**3))

print("=" * 85)
print("PHASE 8 : POTENTIEL NON-LINEAIRE — LE CHAINON FINAL")
print("=" * 85)

# ======================================================================
# PARTIE 1 : RAPPEL DE LA STRUCTURE DIAGONALE (FOURIER)
# ======================================================================
print()
print("PARTIE 1 : RAPPEL — STRUCTURE DIAGONALE PAR FOURIER")
print("-" * 85)

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

# Integrales spatiales
I_spatiales = {}
for s in range(1, 41):
    def integ_spat(r, sv=s):
        return (psi1_spatial(r) ** sv) * 4 * pi * r**2
    I_s, _ = quad(integ_spat, 0, R, limit=200, epsabs=1e-12, epsrel=1e-12)
    I_spatiales[s] = I_s

# Elements diagonaux M_{nn} = A_n * G_nn + n(n-1) * K_{n, n-2}
G_mm_vals = np.zeros(N_MODES + 1)
M_nn_vals = np.zeros(N_MODES + 1)
A_n_vals = np.zeros(N_MODES + 1)

for n in range(1, N_MODES + 1):
    # G_{nn} = <(Psi_1)^n | (Psi_1)^n>_4D
    sn = 2*n
    if sn <= 40:
        G_mm_vals[n] = A1**sn * I_spatiales[sn] * T
    else:
        G_mm_vals[n] = 0.0
    
    # A_n = coefficient du terme lineaire
    A_n = n * (n - 1) * kappa_1**2 + (1 - n**2) * m_masse**2
    A_n_vals[n] = A_n
    
    # K_{n, n-2}
    if n >= 3:
        K_n, _ = quad(lambda r: (psi1_spatial(r) ** (2*n - 2)) * (psi1_prime(r) ** 2) * 4 * pi * r**2, 0, R, limit=100)
    else:
        K_n = 0.0
    
    # M_{nn} = A_n * G_nn + n(n-1) * K_n * T (avec facteur temporel)
    M_nn_vals[n] = A_n * G_mm_vals[n] + n * (n - 1) * K_n * T

print()
print("  Elements diagonaux M_{nn} (partie lineaire) :")
print(f"  {'n':>3} {'M_{nn}':>18} {'A_n':>12} {'G_{nn}':>18}")
print(f"  {'-'*55}")
for n in range(1, N_MODES + 1):
    print(f"  {n:>3} {M_nn_vals[n]:>18.10e} {A_n_vals[n]:>12.4f} {G_mm_vals[n]:>18.10e}")

print()
print("  CONSTAT : M_{11} = 0 (fondamental, c_1 libre)")
print("            M_{nn} != 0 pour n >= 2 (imposerait c_n = 0 sans NL)")
print()
print("  -> Les termes non-lineaires doivent COMPENSER M_{nn} pour n >= 2")

# ======================================================================
# PARTIE 2 : FORMULATION DU POTENTIEL NON-LINEAIRE
# ======================================================================
print()
print("PARTIE 2 : POTENTIEL NON-LINEAIRE V(|Psi|^2)")
print("-" * 85)

print("""
  2.1 Equation complete :
  
      Box(Psi) + V'(|Psi|^2) * Psi = 0
      
      avec V'(rho) = m^2 + lambda_4*rho + lambda_6*rho^2 + ...
      et rho = |Psi|^2
      
  2.2 Developpement :
  
      V'(|Psi|^2) * Psi = m^2 * Psi + lambda_4 * |Psi|^2 * Psi + lambda_6 * |Psi|^4 * Psi + ...
      
  2.3 Terme d'ordre 4 : |Psi|^2 * Psi
  
      Psi = sum_j c_j (Psi_1)^j
      Psi* = sum_k c_k* (Psi_1*)^k
      |Psi|^2 * Psi = sum_{j,k,l} c_j c_k* c_l (Psi_1)^j (Psi_1*)^k (Psi_1)^l
      
      Projection sur (Psi_1)^m :
        N_m^{(4)} = sum_{j,k,l} c_j c_k* c_l * I_4D(m, j, k, l)
      
      ou I_4D(m, j, k, l) = <(Psi_1)^m | (Psi_1)^j (Psi_1*)^k (Psi_1)^l>_4D
      
      Contrainte temporelle : -m + j - k + l = 0  -> j + l = m + k
      
  2.4 Systeme complet projete :
  
      M_{mm} * c_m + lambda_4 * N_m^{(4)} + lambda_6 * N_m^{(6)} + ... = 0
      
      pour m = 1..7
      
      avec M_{11} = 0, M_{mm} != 0 pour m >= 2
""")

# ======================================================================
# PARTIE 3 : CALCUL DES COEFFICIENTS DE COUPLAGE D'ORDRE 4
# ======================================================================
print()
print("PARTIE 3 : CALCUL DES COEFFICIENTS DE COUPLAGE N_m^{(4)}")
print("-" * 85)

def compute_N4_m(m, c_vec):
    """
    Calcule N_m^{(4)} = <(Psi_1)^m | |Psi|^2 * Psi>_4D
    pour un vecteur de coefficients c donne.
    """
    c = np.array(c_vec, dtype=complex)
    total = 0.0 + 0.0j
    
    for j in range(1, N_MODES + 1):
        for k in range(1, N_MODES + 1):
            # Condition temporelle : -m + j - k + l = 0
            l = m + k - j
            if 1 <= l <= N_MODES:
                # Coefficient spatial
                s_tot = m + j + k + l  # exposant spatial total
                if s_tot <= 40:
                    G_val = A1**s_tot * I_spatiales[s_tot] * T
                    total += c[j-1] * np.conj(c[k-1]) * c[l-1] * G_val
    
    return total

def compute_N6_m(m, c_vec):
    """
    Calcule N_m^{(6)} = <(Psi_1)^m | |Psi|^4 * Psi>_4D
    |Psi|^4 * Psi = sum c_j c_k* c_l c_p* c_q (Psi_1)^j (Psi_1*)^k (Psi_1)^l (Psi_1*)^p (Psi_1)^q
    Contrainte : -m + j - k + l - p + q = 0 -> j + l + q = m + k + p
    """
    c = np.array(c_vec, dtype=complex)
    total = 0.0 + 0.0j
    
    for j in range(1, 4):  # Limiter pour performance
        for k in range(1, 4):
            for l in range(1, 4):
                # Condition : -m + j - k + l - p + q = 0 -> p = j + l - k + q - m
                for q in range(1, 4):
                    p = j + l + q - m - k
                    if 1 <= p <= N_MODES:
                        s_tot = m + j + k + l + p + q
                        if s_tot <= 40:
                            G_val = A1**s_tot * I_spatiales[s_tot] * T
                            total += c[j-1] * np.conj(c[k-1]) * c[l-1] * np.conj(c[p-1]) * c[q-1] * G_val
    
    return total

# Test avec les H_n
print()
print("3.1 Coefficients de couplage pour c = H_n :")
print()

c_H = H_EXACT + 0j
for m in range(1, N_MODES + 1):
    N4 = compute_N4_m(m, c_H)
    N6 = compute_N6_m(m, c_H)
    label_mm = f"M_m{m}"
    print(f"  m={m}: {label_mm}={M_nn_vals[m]:.6e}, N4={N4.real:.6e}+{N4.imag:.6e}i, N6={N6.real:.6e}+{N6.imag:.6e}i")

# ======================================================================
# PARTIE 4 : RESOLUTION DU SYSTEME COUPLE
# ======================================================================
print()
print("PARTIE 4 : RESOLUTION DU SYSTEME COUPLE")
print("-" * 85)

print()
print("4.1 Determination des lambda par moindres carres :")
print()

# Pour chaque m >= 2, on veut : lambda_4 * N4_m + lambda_6 * N6_m = -M_{mm} * c_m
# C'est un systeme surdetermine (6 equations, 2 inconnues)
# On resout par moindres carres

# Matrice A : [N4_m, N6_m] pour m=2..7
A_mat = np.zeros((N_MODES - 1, 2), dtype=complex)
b_vec = np.zeros(N_MODES - 1, dtype=complex)

for idx, m in enumerate(range(2, N_MODES + 1)):
    N4 = compute_N4_m(m, c_H)
    N6 = compute_N6_m(m, c_H)
    A_mat[idx, 0] = N4
    A_mat[idx, 1] = N6
    b_vec[idx] = -M_nn_vals[m] * c_H[m-1]

# Resolution complexe par moindres carres
# A^H * A * x = A^H * b
AHA = A_mat.conj().T @ A_mat
AHb = A_mat.conj().T @ b_vec

# Regularisation si mal conditionne
try:
    lambdas = np.linalg.solve(AHA + 1e-10 * np.eye(2), AHb)
except np.linalg.LinAlgError:
    lambdas = np.linalg.lstsq(A_mat, b_vec, rcond=None)[0]

lambda_4, lambda_6 = lambdas[0], lambdas[1]

print(f"  lambda_4 = {lambda_4.real:.10e} + {lambda_4.imag:.10e}i")
print(f"  lambda_6 = {lambda_6.real:.10e} + {lambda_6.imag:.10e}i")
print()

# Verification du residu
print("4.2 Verification du residu pour chaque mode :")
label_Mcm = "M_mm*c_m"
print(f"  {'m':>3} {label_Mcm:>18} {'lambda_4*N4':>18} {'lambda_6*N6':>18} {'Somme':>18} {'Residu relatif'}")
print(f"  {'-'*95}")
for m in range(1, N_MODES + 1):
    N4 = compute_N4_m(m, c_H)
    N6 = compute_N6_m(m, c_H)
    terme_lineaire = M_nn_vals[m] * c_H[m-1]
    nl4 = lambda_4 * N4
    nl6 = lambda_6 * N6
    somme = terme_lineaire + nl4 + nl6
    residu = abs(somme) / (abs(terme_lineaire) + abs(nl4) + abs(nl6) + 1e-30)
    print(f"  {m:>3} {terme_lineaire:>18.10e} {nl4:>18.10e} {nl6:>18.10e} {somme:>18.10e} {residu:.6e}")

# ======================================================================
# PARTIE 5 : ITERATION DE POINT FIXE AVEC POTENTIEL NON-LINEAIRE
# ======================================================================
print()
print("PARTIE 5 : ITERATION DE POINT FIXE AVEC POTENTIEL NON-LINEAIRE")
print("-" * 85)

def compute_residual_and_update(c_vec, lambda4, lambda6):
    """Calcule le residu et propose une mise a jour."""
    c = np.array(c_vec, dtype=complex)
    residu = np.zeros(N_MODES, dtype=complex)
    
    for m in range(1, N_MODES + 1):
        N4 = compute_N4_m(m, c)
        N6 = compute_N6_m(m, c)
        residu[m-1] = M_nn_vals[m] * c[m-1] + lambda4 * N4 + lambda6 * N6
    
    return residu

def iteration_point_fixe_NL(c_init, lambda4, lambda6, n_iter=50, lr=0.3):
    """Iteration de point fixe avec potentiel non-lineaire."""
    c = np.array(c_init, dtype=complex)
    norm_init = np.linalg.norm(c)
    
    for it in range(n_iter):
        residu = compute_residual_and_update(c, lambda4, lambda6)
        err = np.linalg.norm(residu) / (norm_init + 1e-30)
        
        # Mise a jour : c_new = c - lr * residu / M_nn (descente diagonale)
        c_new = c.copy()
        for m in range(1, N_MODES + 1):
            if abs(M_nn_vals[m]) > 1e-15:
                c_new[m-1] = c[m-1] - lr * residu[m-1] / M_nn_vals[m]
        
        # Renormaliser pour stabiliser
        c_new = c_new / np.linalg.norm(c_new) * norm_init
        c = c_new
        
        if it % 10 == 0 or it == n_iter - 1:
            amplitudes = np.abs(c)
            ratio = amplitudes / H_EXACT
            print(f"    iter {it:>3d}: err={err:.6e}, |c|={np.round(amplitudes, 4)}, ratio/H={np.round(ratio, 4)}")
    
    return c

# Test d'iteration
print()
print("5.1 Iteration a partir de H_n :")
print()
c_final_NL = iteration_point_fixe_NL(c_H, lambda_4, lambda_6, n_iter=30, lr=0.1)

print()
print("5.2 Iteration a partir d'une initialisation aleatoire :")
np.random.seed(123)
c_rand = np.random.rand(N_MODES) * 5 + 1
c_final_rand = iteration_point_fixe_NL(c_rand, lambda_4, lambda_6, n_iter=50, lr=0.1)

# ======================================================================
# PARTIE 6 : ANALYSE DE LA FORME DU POTENTIEL
# ======================================================================
print()
print("PARTIE 6 : ANALYSE DE V(|Psi|^2)")
print("-" * 85)

print()
print("6.1 Coefficients determines :")
print(f"  lambda_4 = {lambda_4.real:.10e} + {lambda_4.imag:.10e}i")
print(f"  lambda_6 = {lambda_6.real:.10e} + {lambda_6.imag:.10e}i")
print()

# Est-ce que lambda suit une loi harmonique ?
print("6.2 Recherche d'un pattern harmonique dans les lambda :")
print()
print(f"  |lambda_4| = {abs(lambda_4):.10e}")
print(f"  |lambda_6| = {abs(lambda_6):.10e}")
print(f"  ratio lambda_6 / lambda_4 = {lambda_6 / lambda_4 if abs(lambda_4) > 1e-30 else 0:.10f}")
print()

# Est-ce que lambda_4 ~ phi^k * pi^l * ... ?
# lambda_4 devrait etre de l'ordre de kappa_1^2 ~ 10
# ou m^2 ~ 1
print(f"  kappa_1^2 = {kappa_1**2:.6f}")
print(f"  m^2 = {m_masse**2:.6f}")
print(f"  lambda_4 / kappa_1^2 = {abs(lambda_4) / kappa_1**2:.10f}")
print(f"  lambda_4 / m^2 = {abs(lambda_4) / m_masse**2:.10f}")

# ======================================================================
# SYNTHESE
# ======================================================================
print()
print("=" * 85)
print("SYNTHESE DE LA PHASE 8")
print("=" * 85)

print("""
  RESULTATS :
  
  1. La structure diagonale de Fourier est confirmee :
     M_{11} = 0, M_{nn} != 0 pour n >= 2
     
  2. Les coefficients de couplage non-lineaire N_m^{(4)} et N_m^{(6)}
     ont ete calcules pour H_n
     
  3. Les lambda_4 et lambda_6 ont ete determines par moindres carres
     pour satisfaire l'equation pour les H_n
     
  4. Si les lambda sont reproductibles (meme signe, meme ordre de
     grandeur pour d'autres ensembles de constantes), alors le
     potentiel V(|Psi|^2) est une prediction de la theorie.
     
  5. L'iteration de point fixe avec le potentiel non-lineaire
     devrait converger vers H_n depuis differentes initialisations
     -> PREUVE D'UNICITE.
     
  STATUT : La derivation commence a prendre forme.
           Fourier donne la structure.
           Le potentiel non-lineaire donne les coefficients.
           
           RESTE A FAIRE :
           - Verifier que les lambda sont universels (pas dependants de H_n)
           - Demontrer que le point fixe est unique
           - Exprimer lambda_4, lambda_6 en fonction des H_n
           - Generaliser a tous les ordres
""")

print("=" * 85)
print("FIN DE LA PHASE 8")
print("=" * 85)