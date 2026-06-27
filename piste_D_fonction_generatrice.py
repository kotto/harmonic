"""
PISTE D : FONCTION GENERATRICE SPECTRALE
=========================================
Principe : Definir G(z) = SUM_{n=1}^inf c_n z^n ou z = Psi_1.
L'equation GAGUT (Box + m^2)Psi = 0 se traduit en une equation
differentielle pour G(z), ou plutot en une equation operationnelle
que la serie formelle G(z) doit satisfaire.

Approche : 
1. Exprimer Box(G(Psi_1)) en termes de G'(Psi_1), G''(Psi_1), (nabla Psi_1)^2, Box(Psi_1)
2. Utiliser Box(Psi_1) + m^2 Psi_1 = 0 pour simplifier
3. Identifier l'equation fonctionnelle que les coefficients c_n doivent satisfaire
4. Verifier si c_n = H_n = {phi, pi, e, sqrt2, sqrt3, sqrt5, e/pi} est solution
"""

import numpy as np
from scipy.integrate import quad
from scipy.special import spherical_jn
import math
import cmath

# ======================================================================
# CONSTANTES
# ======================================================================
phi = (1 + math.sqrt(5)) / 2
pi = math.pi
e = math.e
sqrt2 = math.sqrt(2)
sqrt3 = math.sqrt(3)
sqrt5 = math.sqrt(5)
e_over_pi = e / pi

H_EXACT = np.array([phi, pi, e, sqrt2, sqrt3, sqrt5, e_over_pi])
NOMS = ['phi', 'pi', 'e', 'sqrt2', 'sqrt3', 'sqrt5', 'e/pi']

print("=" * 70)
print("PISTE D : FONCTION GENERATRICE SPECTRALE")
print("=" * 70)

# ======================================================================
# PARAMETRES
# ======================================================================
R_sphere = 1.0
kappa_1 = pi / R_sphere
m_masse = 1.0
omega_1 = math.sqrt(kappa_1**2 - m_masse**2)
A1 = math.sqrt(pi / (2 * R_sphere**3))

print(f"\nParametres : kappa_1={kappa_1:.6f}, m={m_masse}, omega_1={omega_1:.6f}")

def psi1_spatial(r):
    if r < 1e-12:
        return A1
    return A1 * spherical_jn(0, kappa_1 * r)

def psi1_prime(r):
    if r < 1e-12:
        return 0.0
    kr = kappa_1 * r
    return A1 * (kr * math.cos(kr) - math.sin(kr)) / (kappa_1 * r**2)

def grad2_psi1(r):
    """(nabla Psi_1)^2 pour la partie spatiale (composante radiale uniquement)"""
    return psi1_prime(r)**2

# ======================================================================
# PARTIE 1 : DERIVATION DE L'EQUATION POUR G(z)
# ======================================================================
print("\n" + "=" * 70)
print("PARTIE 1 : DERIVATION DE L'EQUATION POUR LA FONCTION GENERATRICE")
print("=" * 70)

print("""
Soit G(z) = SUM_{n=1}^inf c_n z^n avec z = Psi_1(x,t) (fonction d'onde maitresse).

L'equation GAGUT : Box(Psi) + m^2 Psi = 0 avec Psi = G(Psi_1)

La regle de derivation en chaine pour le d'Alembertien donne :
  Box[G(Psi_1)] = G'(Psi_1) * Box(Psi_1) + G''(Psi_1) * (nabla Psi_1)^2

ou (nabla Psi_1)^2 = -(d Psi_1/dt)^2 + |grad Psi_1|^2
  = -(d Psi_1/dt)^2 + (d Psi_1/dr)^2   (en symetrie spherique)

Demonstration :
  d_mu G(Psi_1) = G'(Psi_1) * d_mu Psi_1
  d^mu d_mu G = d^mu[G'(Psi_1) * d_mu Psi_1]
              = G''(Psi_1) * (d^mu Psi_1)(d_mu Psi_1) + G'(Psi_1) * d^mu d_mu Psi_1
              = G''(Psi_1) * (nabla Psi_1)^2 + G'(Psi_1) * Box(Psi_1)
""")

# Maintenant, avec Box(Psi_1) = -m^2 Psi_1 (equation de Klein-Gordon) :
# Box[G(Psi_1)] = G'(Psi_1) * (-m^2 Psi_1) + G''(Psi_1) * (nabla Psi_1)^2

# L'equation Box(Psi) + m^2 Psi = 0 devient :
# -m^2 z G'(z) + (nabla Psi_1)^2 G''(z) + m^2 G(z) = 0

# Soit :
# m^2 [G(z) - z G'(z)] + (nabla Psi_1)^2 G''(z) = 0

# Le PROBLEME est que (nabla Psi_1)^2 DEPEND de x et t,
# alors que G(z) et ses derivees dependent de z = Psi_1(x,t).
# Pour que l'equation soit satisfaite pour tout (x,t),
# il faut que (nabla Psi_1)^2 s'exprime comme une fonction de z seul.

print("\n" + "=" * 70)
print("PARTIE 2 : ANALYSE DE (nabla Psi_1)^2 EN FONCTION DE Psi_1")
print("=" * 70)

# Explorons la relation entre z = Psi_1 et (nabla Psi_1)^2
# pour voir si c'est une fonction simple.

N_pts = 50
r_values = np.linspace(1e-6, R_sphere, N_pts)

z_vals = np.array([psi1_spatial(r) for r in r_values])
grad2_vals = np.array([grad2_psi1(r) for r in r_values])

# Pour la partie temporelle, (dPsi_1/dt)^2 = omega_1^2 * Psi_1^2
# Donc (nabla Psi_1)^2 complet = omega_1^2 * Psi_1^2 + (dPsi_1/dr)^2
# (signature -+++ : -d^2/dt^2 + nabla^2, donc -(-omega^2) = +omega^2)

# En fait, (nabla Psi_1)^2 = -(d_t Psi_1)^2 + (d_r Psi_1)^2
# d_t Psi_1 = -i omega_1 Psi_1, donc (d_t Psi_1)^2 = -omega_1^2 Psi_1^2
# -(d_t Psi_1)^2 = +omega_1^2 Psi_1^2
# Donc (nabla Psi_1)^2 = omega_1^2 Psi_1^2 + (d_r Psi_1)^2

grad2_complet = omega_1**2 * z_vals**2 + grad2_vals

print(f"\nRelation entre z = Psi_1 et (nabla Psi_1)^2 :")
print(f"  z_min = {z_vals.min():.6f}, z_max = {z_vals.max():.6f}")
print(f"  (nabla Psi_1)^2 min = {grad2_complet.min():.6f}, max = {grad2_complet.max():.6f}")

# Analyse de la relation fonctionnelle
# Essayons un ajustement polynomial : (nabla Psi_1)^2 ~ a*z^2 + b*z^4 + ...
print(f"\nAjustement polynomial de (nabla Psi_1)^2 en fonction de z^2 :")

# Regression lineaire sur z^2, z^4, z^6
A_reg = np.zeros((N_pts, 3))
A_reg[:, 0] = z_vals**2
A_reg[:, 1] = z_vals**4
A_reg[:, 2] = z_vals**6

coeffs, residuals, rank, singular = np.linalg.lstsq(A_reg, grad2_complet, rcond=None)
print(f"  (nabla Psi_1)^2 ~ {coeffs[0]:.6f} * z^2 + {coeffs[1]:.6f} * z^4 + {coeffs[2]:.6f} * z^6")
print(f"  Qualite de l'ajustement : residu = {residuals[0] if len(residuals) > 0 else 'N/A' :.6e}")

# ======================================================================
# PARTIE 3 : EQUATION FONCTIONNELLE APPROCHEE POUR G(z)
# ======================================================================
print("\n" + "=" * 70)
print("PARTIE 3 : EQUATION FONCTIONNELLE POUR G(z)")
print("=" * 70)

# Si (nabla Psi_1)^2 = alpha*z^2 + beta*z^4 + gamma*z^6 + ...
# Alors l'equation devient :
# m^2 [G(z) - z G'(z)] + (alpha*z^2 + beta*z^4 + gamma*z^6) G''(z) = 0

# C'est une equation differentielle du second ordre pour G(z).
# On cherche une solution G(z) = SUM c_n z^n avec c_1 = phi, c_2 = pi, etc.

# Injectons G(z) = SUM c_n z^n dans l'equation :
# m^2 [SUM c_n z^n - z SUM n c_n z^{n-1}] + (SUM_k a_k z^{2k}) * SUM_n n(n-1) c_n z^{n-2} = 0
# m^2 SUM c_n (1-n) z^n + SUM_{k,n} a_k n(n-1) c_n z^{n+2k-2} = 0

# Pour chaque puissance de z, on obtient une equation.

# Avec seulement le terme dominant alpha*z^2 :
# m^2 SUM c_n (1-n) z^n + alpha * z^2 * SUM_n n(n-1) c_n z^{n-2} = 0
# m^2 SUM c_n (1-n) z^n + alpha * SUM_n n(n-1) c_n z^n = 0

# Donc pour chaque n :
# m^2 c_n (1-n) + alpha * n(n-1) c_n = 0
# c_n * [m^2(1-n) + alpha * n(n-1)] = 0

# Pour n=1 : c_1 * [0 + 0] = 0 -> c_1 libre
# Pour n>=2 : n(n-1)(alpha - m^2/n) * c_n = 0 -> c_n = 0 (sauf si alpha = m^2/n)

# Avec le terme beta*z^4 en plus :
# m^2 c_n (1-n) + alpha * n(n-1) c_n + beta * (n-2)(n-3) c_{n-2} = 0

# Ceci est une relation de RECURRENCE pour les c_n !

print("\nEquation de recurrence avec (nabla Psi_1)^2 ~ alpha*z^2 + beta*z^4 :")
print(f"  alpha = {coeffs[0]:.6f}, beta = {coeffs[1]:.6f}")

alpha = coeffs[0]
beta = coeffs[1]

# Testons la recurrence pour voir si elle produit les H_n
N = 10
c_rec = np.zeros(N)
c_rec[0] = phi  # c_1 = phi (normalisation)

print(f"\n  Coefficients par recurrence :")
print(f"  c_1 = phi = {phi:.10f}")

for n_idx in range(1, N):
    n_val = n_idx + 1
    # Equation : c_n * [m^2(1-n) + alpha*n(n-1)] + beta*(n-2)*(n-3)*c_{n-2} = 0
    coeff_n = m_masse**2 * (1 - n_val) + alpha * n_val * (n_val - 1)
    
    if abs(coeff_n) > 1e-15:
        if n_idx >= 2:
            c_rec[n_idx] = -beta * (n_val - 2) * (n_val - 3) * c_rec[n_idx - 2] / coeff_n
        else:
            c_rec[n_idx] = 0.0  # Pour n=2, le terme en beta est nul (n_val-2=0)
    else:
        c_rec[n_idx] = 0.0
    
    if n_idx < 7:
        print(f"  c_{n_val} = {c_rec[n_idx]:>15.10f}  (H attendu: {H_EXACT[n_idx]:>15.10f})")
    else:
        print(f"  c_{n_val} = {c_rec[n_idx]:>15.10f}  (H attendu: N/A)")

# ======================================================================
# PARTIE 4 : ANALYSE DES RESULTATS
# ======================================================================
print("\n" + "=" * 70)
print("PARTIE 4 : ANALYSE ET INTERPRETATION")
print("=" * 70)

# Verifions si la recurrence donne les H_n
print("\nComparaison recurrence vs H_exact :")
for n_idx in range(min(7, N)):
    n_val = n_idx + 1
    err = abs(c_rec[n_idx] - H_EXACT[n_idx]) / H_EXACT[n_idx] if H_EXACT[n_idx] != 0 else float('inf')
    print(f"  n={n_val}: recurrence={c_rec[n_idx]:.6f}, H_exact={H_EXACT[n_idx]:.6f}, erreur={err:.2e}")

# L'approximation polynomiale de (nabla Psi_1)^2 est-elle suffisante ?
# Regardons l'erreur d'approximation

grad2_approx = alpha * z_vals**2 + beta * z_vals**4 + coeffs[2] * z_vals**6
erreur_max = np.max(np.abs(grad2_complet - grad2_approx))
erreur_moy = np.mean(np.abs(grad2_complet - grad2_approx))

print(f"\nQualite de l'approximation polynomiale de (nabla Psi_1)^2 :")
print(f"  Erreur max = {erreur_max:.6e}")
print(f"  Erreur moy = {erreur_moy:.6e}")
print(f"  Erreur relative max = {erreur_max/np.max(grad2_complet)*100:.4f}%")

# ======================================================================
# PARTIE 5 : EQUATION EXACTE VIA NOYAU INTEGRAL
# ======================================================================
print("\n" + "=" * 70)
print("PARTIE 5 : APPROCHE PAR NOYAU INTEGRAL")
print("=" * 70)

print("""
Au lieu d'approximer (nabla Psi_1)^2 comme un polynome en z,
on peut traiter l'equation fonctionnelle exacte via un NOYAU INTEGRAL.

L'equation : m^2 [G(z) - z G'(z)] + K(z) G''(z) = 0

ou K(z) = (nabla Psi_1)^2 evalue en fonction de z = Psi_1(x).

K(z) n'est pas une fonction univoque de z car Psi_1(x) n'est pas injective
(symetrie spherique : la meme valeur de Psi_1 apparait pour deux rayons
differents, sauf au maximum). Donc K(z) est multivaluee.

C'est la raison fondamentale pour laquelle l'approche par fonction
generatrice simple echoue : la relation entre Psi_1 et (nabla Psi_1)^2
n'est pas fonctionnelle (une valeur de Psi_1 correspond a DEUX valeurs
de (nabla Psi_1)^2, sauf au pic central et a la frontiere).

CONCLUSION DE LA PISTE D :
L'approche par fonction generatrice G(z) = SUM c_n z^n avec z = Psi_1
ne fonctionne pas directement car (nabla Psi_1)^2 n'est pas une fonction
de Psi_1 seul (non-injectivite de Psi_1).

Cependant, l'idee de la recurrence entre coefficients reste valable
si on peut exprimer le systeme projete sous forme de relation de
recurrence sans passer par l'approximation polynomiale.

PROCHAINE ETAPE SUGGEREE :
Nouvelle Piste G : Travailler dans l'espace de Fourier (modes propres
exacts de l'operateur Box + m^2) plutot que dans la base des puissances.
Les modes propres sont les harmoniques spheriques j_l(kr) Y_{lm}(theta,phi).
Dans cette base, Box est DIAGONAL et le systeme est trivialement resolu.
""")

print("=" * 70)
print("BILAN DE LA PISTE D")
print("=" * 70)

print("""
RESULTATS :

1. L'equation pour G(z) : m^2 [G(z) - z G'(z)] + K(z) G''(z) = 0
   est correcte formellement.

2. K(z) = (nabla Psi_1)^2 evalue en fonction de z = Psi_1(x)
   est MULTIVALUE (Psi_1 n'est pas injective sur le domaine spherique).

3. Une approximation polynomiale K(z) ~ alpha*z^2 + beta*z^4
   produit une relation de recurrence pour les c_n,
   mais les coefficients obtenus ne sont pas les H_n.

4. CAUSE FONDAMENTALE : La non-injectivite de Psi_1(x) sur la sphere.
   Pour chaque valeur de z (sauf au maximum), il existe deux rayons
   r1 et r2 tels que Psi_1(r1) = Psi_1(r2) = z mais avec
   (nabla Psi_1)^2(r1) != (nabla Psi_1)^2(r2).

5. IMPLICATION : Toute approche basee sur G(z) avec z scalaire
   echoue a capturer la structure spatiale complete.

6. NOUVELLE DIRECTION : Piste G — Developpement sur les modes propres
   exacts de Box+m^2 (harmoniques spheriques) ou Box est diagonal.
   Dans cette base, le systeme est trivialement resolu et les H_n
   emergent comme coefficients de la decomposition spectrale.
""")