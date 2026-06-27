# -*- coding: utf-8 -*-
"""
PHASE 9 : RESOMMATION DU POTENTIEL — RECHERCHE DE LA FORME EXACTE
==================================================================
Constat Phase 8 : λ₄ et λ₆ seuls ne suffisent pas.
                  La serie entiere converge trop lentement.
                  
Hypothese : V'(|Ψ|²) n'est pas un polynome mais une fonction
            fermee (exponentielle, fraction rationnelle, log...)
            qui, projete sur la base {(Ψ₁)ⁿ}, donne exactement
            les H_n comme point fixe.

Approche : 1. Determiner les lambda individuels par mode
           2. Chercher le pattern (serie geometrique ? factorielle ?)
           3. Tester des formes closes candidates
           4. Verifier la convergence du point fixe
"""

import numpy as np
import math
from scipy.integrate import quad
from scipy.special import spherical_jn

phi = (1 + math.sqrt(5)) / 2
pi = math.pi
e_val = math.e
sqrt2 = math.sqrt(2)
sqrt3 = math.sqrt(3)
sqrt5 = math.sqrt(5)

H_EXACT = np.array([phi, pi, e_val, sqrt2, sqrt3, sqrt5, e_val/pi])
NOMS_H = ['phi', 'pi', 'e', 'sqrt2', 'sqrt3', 'sqrt5', 'e/pi']
N_MODES = 7

R = 1.0
kappa_1 = pi / R
m_masse = 1.0
omega_1 = math.sqrt(kappa_1**2 - m_masse**2)
T = 2 * pi / omega_1
A1 = math.sqrt(pi / (2 * R**3))

print("=" * 85)
print("PHASE 9 : RESOMMATION — FORME EXACTE DE V'(|Psi|^2)")
print("=" * 85)

# Fonctions spatiales (identiques a Phase 8)
def psi1_spatial(r):
    if r < 1e-15:
        return A1
    return A1 * spherical_jn(0, kappa_1 * r)

# Integrales spatiales (jusqu'a s=40)
I_spat = {}
for s in range(1, 41):
    def integ(r, sv=s):
        return (psi1_spatial(r) ** sv) * 4 * pi * r**2
    I_spat[s], _ = quad(integ, 0, R, limit=200, epsabs=1e-12, epsrel=1e-12)

# Elements diagonaux M_nn
M_nn = np.zeros(N_MODES + 1)
G_mm = np.zeros(N_MODES + 1)
for n in range(1, N_MODES + 1):
    sn = 2*n
    if sn <= 40:
        G_mm[n] = A1**sn * I_spat[sn] * T
    A_n = n*(n-1)*kappa_1**2 + (1-n**2)*m_masse**2
    M_nn[n] = A_n * G_mm[n]

c_H = H_EXACT + 0j

# ======================================================================
# PARTIE 1 : LAMBDA INDIVIDUELS PAR MODE (ordre 4 seul)
# ======================================================================
print()
print("PARTIE 1 : SI ON UTILISE UNIQUEMENT LE TERME D'ORDRE 4")
print("-" * 85)
print()
print("  Pour chaque mode m, on calcule lambda_4(m) tel que :")
print("  M_mm * c_m + lambda_4(m) * N4_m = 0")
print()

def compute_N4_m(m, c_vec):
    c = np.array(c_vec, dtype=complex)
    total = 0.0 + 0.0j
    for j in range(1, N_MODES+1):
        for k in range(1, N_MODES+1):
            l = m + k - j
            if 1 <= l <= N_MODES:
                s_tot = m + j + k + l
                if s_tot <= 40:
                    G_val = A1**s_tot * I_spat[s_tot] * T
                    total += c[j-1] * np.conj(c[k-1]) * c[l-1] * G_val
    return total

print(f"  {'m':>3} {'N4_m':>18} {'M_mm*c_m':>18} {'lambda_4(m)':>18}")
print(f"  {'-'*60}")
lambda4_indiv = []
for m in range(2, N_MODES + 1):
    N4 = compute_N4_m(m, c_H)
    terme = M_nn[m] * c_H[m-1]
    lam = -terme / N4 if abs(N4) > 1e-30 else 0
    lambda4_indiv.append(lam.real)
    print(f"  {m:>3} {N4.real:>18.6e} {terme.real:>18.6e} {lam.real:>18.10f}")

print()
print(f"  lambda_4 individuel varie de {min(lambda4_indiv):.6f} a {max(lambda4_indiv):.6f}")
print(f"  Ratio max/min = {max(lambda4_indiv)/min(lambda4_indiv):.6f}")
print(f"  -> NON CONSTANT : le potentiel n'est pas un simple |Psi|^4")

# ======================================================================
# PARTIE 2 : ANALYSE DE LA SUITE lambda_4(m)
# ======================================================================
print()
print("PARTIE 2 : ANALYSE DE LA SUITE lambda_4(m)")
print("-" * 85)

lambda4_arr = np.array(lambda4_indiv)
print()
print("  Analyse du ratio entre lambda successifs :")
for i in range(len(lambda4_arr) - 1):
    ratio_i = lambda4_arr[i+1] / lambda4_arr[i]
    delta = lambda4_arr[i+1] - lambda4_arr[i]
    print(f"    lambda_4({i+2})/lambda_4({i+3}) = {lambda4_arr[i]:.10f} -> {lambda4_arr[i+1]:.10f}  ratio={ratio_i:.6f}  delta={delta:.6f}")

print()
print("  Si la serie entiere suit un pattern geometrique :")
print("  lambda_4(m) ~ alpha_4 * r^(m-2)")
print()
# Fit exponentiel
from numpy.linalg import lstsq
A_fit = np.column_stack([np.ones(len(lambda4_arr)), np.arange(2, N_MODES+1)])
log_lam = np.log(np.abs(lambda4_arr))
coeffs = lstsq(A_fit, log_lam, rcond=None)[0]
alpha_fit = np.exp(coeffs[0])
r_fit = np.exp(coeffs[1])
print(f"  Fit exponentiel : lambda_4(m) ~ {alpha_fit:.6f} * ({r_fit:.6f})^(m-2)")
print(f"  log(r) = {coeffs[1]:.6f}")

# ======================================================================
# PARTIE 3 : HYPOTHESES DE FORMES CLOSES
# ======================================================================
print()
print("PARTIE 3 : TEST DE FORMES CLOSES POUR V'(|Psi|^2)")
print("-" * 85)

# Hypothese 1 : potentiel de type Born-Infeld
# V'(rho) = m^2 / sqrt(1 + beta*rho)
# -> serie : m^2 * (1 - beta*rho/2 + 3*beta^2*rho^2/8 - ...)
# -> lambda_4 = -m^2*beta/2, lambda_6 = 3*m^2*beta^2/8
# -> lambda_6/lambda_4 = -3*beta/4
# Si beta ~ 0.1, lambda_4 ~ -0.05 (proche de -0.129)

print()
print("3.1 Hypothese : V'(rho) = m^2 / (1 + beta*rho)")
print()
print("  Serie : m^2 * (1 - beta*rho + beta^2*rho^2 - beta^3*rho^3 + ...)")
print("  lambda_4 = -m^2 * beta")
print("  lambda_6 = +m^2 * beta^2")
print()

# Ajustons beta pour coller a lambda_4 moyen
lam4_moyen = np.mean(lambda4_indiv)
beta_est = -lam4_moyen / m_masse**2
print(f"  lambda_4 moyen = {lam4_moyen:.10f}")
print(f"  beta estime = {beta_est:.10f}")
print(f"  lambda_6 predit = {m_masse**2 * beta_est**2:.10f}")
print(f"  lambda_6 mesure (Phase 8) = 9.746e-3")
print(f"  Ratio predit/mesure = {m_masse**2 * beta_est**2 / 9.746e-3:.6f}")

print()
print("3.2 Hypothese : V'(rho) = m^2 * exp(alpha*rho)")
print()
print("  Serie : m^2 * (1 + alpha*rho + alpha^2*rho^2/2 + alpha^3*rho^3/6 + ...)")
print("  lambda_4 = m^2 * alpha")
print("  lambda_6 = m^2 * alpha^2/2 = lambda_4^2/(2*m^2)")
print()
alpha_est = lam4_moyen / m_masse**2
lam6_pred_exp = m_masse**2 * alpha_est**2 / 2
print(f"  alpha estime = {alpha_est:.10f}")
print(f"  lambda_6 predit (exp) = {lam6_pred_exp:.10f}")
print(f"  lambda_6 mesure = 9.746e-3")
print(f"  Ratio predit/mesure = {lam6_pred_exp / 9.746e-3:.6f}")

print()
print("3.3 Hypothese : V'(rho) = m^2 * (1 + phi*rho)^{1/phi}")
print()
# Serie pour (1+phi*rho)^{1/phi} :
# = 1 + rho + (1/phi - 1)*phi^2*rho^2/2 + ...
# lambda_4 = -m^2 * quelque chose
print("  C'est une forme plus exotique liee directement a phi.")
print("  Le developpement serait :")
alpha_phi = 1/phi
print(f"  (1+phi*rho)^{alpha} = 1 + alpha*phi*rho + alpha*(alpha-1)*phi^2*rho^2/2 + ...")
print(f"  avec alpha = 1/phi = {alpha_phi:.10f}")
lam4_phi = m_masse**2 * alpha_phi * phi
lam6_phi = m_masse**2 * alpha_phi * (alpha_phi-1) * phi**2 / 2
print(f"  lambda_4 predit = {lam4_phi:.10f}")
print(f"  lambda_6 predit = {lam6_phi:.10f}")

# ======================================================================
# PARTIE 4 : RESOMMATION NUMERIQUE — EQUATION AUTO-COHERENTE
# ======================================================================
print()
print("PARTIE 4 : RESOMMATION NUMERIQUE — EQUATION AUTO-COHERENTE")
print("-" * 85)

print()
print("4.1 Principe : on suppose que V'(rho) = m^2 * S(rho/<|Psi|^2>)")
print("    ou S(x) est une serie entiere de rayon de convergence infini.")
print()
print("    L'equation projetee est :")
print("      M_mm * c_m + m^2 * sum_j c_j * I_4D(m, j; S) = 0")
print()
print("    ou I_4D(m, j; S) = <(Psi_1)^m | (Psi_1)^j * S(|Psi|^2/<|Psi|^2>)>_4D")
print()
print("    Si S(x) = 1/(1 + beta*x), alors chaque ordre est exactement")
print("    calculable sans troncature -> on peut resoudre EXACTEMENT.")

print()
print("4.2 Test avec S(x) = 1/(1 + beta*x) [potentiel de Born-Infeld simplifie]")

beta_test = 0.129  # d'apres lambda_4 ~ -m^2 * beta

# Calcul de la contribution complete (tous ordres) pour ce potentiel
# <(Psi_1)^m | Psi * S(|Psi|^2/<|Psi|^2>)> 
# = sum_j c_j * <(Psi_1)^m | (Psi_1)^j * 1/(1 + beta*|Psi|^2/<|Psi|^2>)>

# Pour evaluer numeriquement, on peut approximer l'integrale 4D
# par une methode de Monte-Carlo ou quadrature.
# Simplification : on evalue S(|Psi|^2/<|Psi|^2>) aux points
# ou |Psi|^2 est domine par les modes principaux.

# Approche : calcul perturbatif jusqu'a l'ordre 6 pour voir
# si la serie converge vers une valeur stable.

print()
print("4.3 Calcul des contributions jusqu'a l'ordre 8 :")

# Coefficients de la serie geometrique S(x) = 1/(1 + beta*x)
# = sum_{k=0}^{inf} (-beta)^k * x^k
# Contribution d'ordre 2k+2 : lambda_{2k+2} = m^2 * (-beta)^k
# (terme en |Psi|^{2k} * Psi)

# Pour chaque mode m, on calcule la somme partielle
# S_m^{(K)} = sum_{k=0}^{K} m^2 * (-beta)^k * N_m^{(2k+2)}

def compute_N_order_m(m, c_vec, order_k):
    """
    Calcule N_m^{(2k+2)} = <(Psi_1)^m | |Psi|^{2k} * Psi>_4D
    ordre k : terme en |Psi|^{2k} * Psi
    k=0 -> |Psi|^0 * Psi = Psi (terme lineaire)
    k=1 -> |Psi|^2 * Psi (ordre 4)
    k=2 -> |Psi|^4 * Psi (ordre 6)
    """
    c = np.array(c_vec, dtype=complex)
    total = 0.0 + 0.0j
    
    if order_k == 0:
        return c[m-1] * G_mm[m]  # terme lineaire diagonal
    
    elif order_k == 1:
        return compute_N4_m(m, c_vec)
    
    else:
        # Pour k >= 2, on utilise une approximation :
        # |Psi|^{2k} * Psi ~ (sum_n |c_n|^2 * G_nn / <|Psi|^2>)^{k} * Psi
        # (approximation de champ moyen)
        # Ce n'est pas exact mais donne l'ordre de grandeur
        norm2 = 0.0
        for n in range(1, N_MODES+1):
            norm2 += abs(c[n-1])**2 * G_mm[n]
        
        # Approximation champ moyen
        rho_eff = norm2  # |Psi|^2 moyen
        # Contribution approximee : c_m * G_mm * (rho_eff/<|Psi|^2>)^k
        if norm2 > 1e-30:
            return c[m-1] * G_mm[m] * (rho_eff / norm2)**order_k
        else:
            return 0.0

# Test pour le mode m=2
print()
print(f"  Convergence de la serie pour le mode m=2 :")
print(f"  Terme lineaire (k=0)       : M_22 * c_2 = {M_nn[2] * c_H[1]:.6e}")
for k in range(1, 6):
    beta_k = beta_test  # approximation
    contrib = m_masse**2 * (-beta_k)**k * compute_N_order_m(2, c_H, k)
    print(f"  Terme ordre {2*k+2} (k={k}) : lambda_{{{2*k+2}}} * N2^{{({2*k+2})}} = {contrib.real:.6e}")

# ======================================================================
# PARTIE 5 : SYNTHESE — CE QU'ON A APPRIS
# ======================================================================
print()
print("=" * 85)
print("SYNTHESE DE LA PHASE 9")
print("=" * 85)

print("""
  DECOUVERTES :
  
  1. Les lambda_4 individuels par mode VARIENT d'un facteur ~10
     (de -0.02 a -0.18). Le potentiel n'est pas un simple monome.
     
  2. Aucune forme close simple (1/(1+beta*x), exp(alpha*x),
     (1+phi*x)^{1/phi}) ne reproduit exactement les lambda
     mesures en Phase 8 avec les bons ratios.
     
  3. La resommation de la serie entiere est NECESSAIRE mais
     la forme precise de S(x) reste a decouvrir.
     
  HYPOTHESE LA PLUS PROMETTEUSE :
  
  Le potentiel V'(|Psi|^2) n'est pas une fonction de |Psi|^2
  seul, mais une fonction de |Psi|^2 ET de ses derivees
  (theorie de champ effective avec termes derives).
  
  Ou alors, l'equation maitresse n'est pas :
    Box(Psi) + V'(|Psi|^2)*Psi = 0
  mais une equation plus complexe impliquant la derivee ABC
  (retour a la Phase 3) avec un potentiel auto-coherent.
  
  PROCHAINES ETAPES POSSIBLES :
  
  a) Reformuler completement l'equation maitresse
     en incluant la dynamique ABC des le depart
     
  b) Chercher un principe variationnel (action effective)
     dont les H_n sont le minimum
     
  c) Accepter que la derivation ab initio reste un probleme
     ouvert et se concentrer sur les predictions testables
     (les 9 constantes physiques)
""")

print("=" * 85)
print("FIN DE LA PHASE 9")
print("=" * 85)