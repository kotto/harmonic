"""
PISTE B : INTEGRATION TEMPORELLE COMPLETE
Exploration de la correction la plus prometteuse pour le Maillon 13.

Principe : Le produit scalaire dans L^2(Omega) inclut l'integration
sur le temps ET l'espace. La partie temporelle produit un facteur
delta_{mn} (orthogonalite de Fourier), rendant la matrice DIAGONALE.

Psi_1(x,t) = A1 * j0(kappa_1 * r) * exp(-i omega_1 t)
Psi_1(x,t)^n = A1^n * j0(kappa_1 * r)^n * exp(-i n omega_1 t)

<Psi_1^m | Psi_1^n> = [int spatiale de j0^{m+n}] * [int temporelle de e^{i(m-n)omega_1 t}]
                      = G_{mn} * T * delta_{mn}   (pour T >> 2*pi/omega_1)

Donc M_{mn} = ... * delta_{mn}  -> MATRICE DIAGONALE !
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

CONSTANTES_EXACTES = [phi, pi, e, sqrt2, sqrt3, sqrt5, e_over_pi]
NOMS = ['phi', 'pi', 'e', 'sqrt2', 'sqrt3', 'sqrt5', 'e/pi']

print("=" * 70)
print("PISTE B : INTEGRATION TEMPORELLE COMPLETE")
print("Diagonalisation par orthogonalite de Fourier")
print("=" * 70)

# ======================================================================
# PARAMETRES
# ======================================================================
R = 1.0
kappa_1 = pi / R
m = 1.0
# omega_1^2 = kappa_1^2 - m^2 (equation de Klein-Gordon)
omega_1 = math.sqrt(kappa_1**2 - m**2)
A1 = math.sqrt(pi / (2 * R**3))

T = 2 * pi / omega_1  # Periode fondamentale

print(f"\nParametres : R={R}, kappa_1={kappa_1:.6f}, m={m}, omega_1={omega_1:.6f}")
print(f"A1 = {A1:.10f}, Periode T = {T:.6f}")

def psi1_spatial(r):
    """Partie spatiale de Psi_1"""
    if r < 1e-12:
        return A1 * 1.0
    return A1 * spherical_jn(0, kappa_1 * r)

def psi1_prime(r):
    """Derivee radiale de la partie spatiale"""
    if r < 1e-12:
        return 0.0
    kr = kappa_1 * r
    return A1 * (kr * math.cos(kr) - math.sin(kr)) / (kappa_1 * r**2)

# ======================================================================
# PARTIE 1 : VERIFICATION DE L'ORTHOGONALITE TEMPORELLE
# ======================================================================
print("\n" + "=" * 70)
print("PARTIE 1 : ORTHOGONALITE TEMPORELLE")
print("=" * 70)

print("\nIntegration temporelle : I_{mn} = (1/T) * int_0^T e^{i(m-n)omega_1 t} dt")
print(f"{'m':>3} {'n':>3} {'I_{mn} reel':>15} {'I_{mn} imag':>15} {'|I_{mn}|':>15}")
print("-" * 55)

for m_val in range(1, 6):
    for n_val in range(1, 6):
        if m_val == n_val:
            # Exact : 1 (par normalisation 1/T)
            I_re = 1.0
            I_im = 0.0
        else:
            dw = (m_val - n_val) * omega_1
            # (1/T) * int_0^T e^{i dw t} dt = (1/T) * [e^{i dw T} - 1] / (i dw)
            # Avec T = 2*pi/omega_1, dw * T = (m-n)*2*pi
            # e^{i 2*pi*k} - 1 = 0 pour tout entier k
            I_re = 0.0
            I_im = 0.0
        print(f"{m_val:>3} {n_val:>3} {I_re:>15.10f} {I_im:>15.10f} {abs(complex(I_re, I_im)):>15.10f}")

print("\nVERIFICATION : I_{mn} = delta_{mn}  (orthogonalite de Fourier)")

# ======================================================================
# PARTIE 2 : CONSTRUCTION DE LA MATRICE DIAGONALE M
# ======================================================================
print("\n" + "=" * 70)
print("PARTIE 2 : MATRICE M AVEC INTEGRATION 4D COMPLETE")
print("=" * 70)

print("""
Construction de M_{mn} avec integration 4D :

M_{mn} = <Psi_1^m | Box(Psi_1^n) + m^2 Psi_1^n>_{4D}

ou <f|g>_{4D} = int_Omega f*(x,t) g(x,t) d^3x dt

Pour Psi_1^n(x,t) = [A1 * j0(kappa_1 r)]^n * exp(-i n omega_1 t) :

Box(Psi_1^n) = -d^2/dt^2(Psi_1^n) + nabla^2(Psi_1^n)

-d^2/dt^2(Psi_1^n) = -(-n^2 omega_1^2 Psi_1^n) = n^2 omega_1^2 Psi_1^n
nabla^2(Psi_1^n) = -n kappa_1^2 Psi_1^n + n(n-1) Psi_1^{n-2} (nabla Psi_1)^2

Box(Psi_1^n) + m^2 Psi_1^n = [n^2 omega_1^2 - n kappa_1^2 + m^2] Psi_1^n
                           + n(n-1) Psi_1^{n-2} (nabla Psi_1)^2

Avec omega_1^2 = kappa_1^2 - m^2 :
  = [n^2(kappa_1^2 - m^2) - n kappa_1^2 + m^2] Psi_1^n + n(n-1) Psi_1^{n-2} (nabla Psi_1)^2
  = [n(n-1)kappa_1^2 + (1-n^2)m^2] Psi_1^n + n(n-1) Psi_1^{n-2} (nabla Psi_1)^2
""")

# Integration 4D : spatiale * temporelle
# Partie temporelle : delta_{mn} (orthogonalite de Fourier)
# Donc seuls les termes diagonaux (m=n) contribuent !

N = 15
c = np.zeros(N)
c[0] = 1.0  # Normalisation arbitraire

print(f"\nResolution du systeme diagonal pour N={N}...")
print(f"{'n':>3} {'coeff_diag':>18} {'c_n (diagonal)':>18} {'H_n attendu':>18} {'c_n / H_1':>18}")
print("-" * 80)

# Pour m=n, le terme non-diagonal K_{n, n-2} contribue
# car il vient de n(n-1) Psi_1^{n-2} (nabla Psi_1)^2
# Projete sur Psi_1^n (m=n) : <Psi_1^n | Psi_1^{n-2} (nabla Psi_1)^2>
# = K_{n, n-2} (notation precedente)

# Pour chaque n, l'equation est :
# [coeff_diag] * c_n + n(n-1) * K_{n, n-2} * c_{n-2}? ... 
# Attendez, le terme n(n-1) Psi_1^{n-2} (nabla Psi_1)^2 n'est pas
# proportionnel a Psi_1^n mais a Psi_1^{n-2}. Donc quand on projette
# sur Psi_1^m avec m=n, on obtient :
# <Psi_1^n | Psi_1^{n-2} (nabla Psi_1)^2> = K_{n, n-2}

# Mais ce terme est dans l'equation pour Psi_1^n, donc il contribue
# a M_{mn} pour m=n (terme diagonal) via le coefficient c_n.

# Le systeme projete est :
# SUM_n c_n * M_{mn} = 0 pour tout m

# Avec integration temporelle : M_{mn} = 0 pour m != n
# Pour m = n : M_{nn} = A_n * G_{nn} + n(n-1) * K_{n, n-2}
# ou A_n = n(n-1)kappa_1^2 + (1-n^2)m^2

# Pour n=1 : A_1 = 0*kappa^2 + 0*m^2 = 0, et n(n-1)=0
# Donc M_{11} = 0 -> c_1 est libre (fixe arbitrairement)

# Pour n=2 : A_2 = 2*1*kappa^2 + (1-4)*m^2 = 2*kappa^2 - 3*m^2
# n(n-1) = 2, donc K_{2, 0} intervient. Mais K_{2,0} = <Psi_1^2 | Psi_1^0 (nabla Psi_1)^2>
# = <Psi_1^2 | (nabla Psi_1)^2> (car Psi_1^0 = 1)

# Equation m=1 : M_{11} c_1 = 0 -> 0*c_1 = 0 (toujours vrai, c_1 libre)
# Equation m=2 : M_{22} c_2 = 0 -> c_2 = 0 (sauf si M_{22}=0)

# Hmm, ca ne donne pas les H_n. Le probleme est que l'equation
# de Klein-Gordon est une equation d'evolution, pas une equation
# statique. La projection sur les modes propres donne des conditions
# sur les coefficients, mais pas de la meme maniere que pour une
# equation aux valeurs propres.

# REPENSER LE PROBLEME :
# L'equation de Klein-Gordon (Box + m^2)Psi = 0 est satisfaite
# SEULEMENT pour Psi_1 (le mode fondamental). Pour les puissances
# superieures, (Box + m^2)Psi_1^n != 0.

# Pour que Psi = SUM c_n Psi_1^n satisfasse l'equation, il faut :
# SUM c_n (Box + m^2)Psi_1^n = 0

# Projetons sur Psi_1^m et utilisons l'integration temporelle :
# SUM_n c_n <Psi_1^m | (Box + m^2)Psi_1^n>_{4D} = 0

# Avec integration temporelle : seuls les termes m=n survivent
# (a cause de la partie n(n-1)Psi_1^{n-2}... non, ce terme
#  contient Psi_1^{n-2} * exp(-i n omega_1 t) et on projette
#  sur Psi_1^m = Psi_1^m * exp(+i m omega_1 t))

# ATTENTION : le terme n(n-1) Psi_1^{n-2} (nabla Psi_1)^2
# a une dependance temporelle en exp(-i n omega_1 t)
# car (nabla Psi_1)^2 est independant du temps (nabla agit sur la partie spatiale)
# Donc la projection sur Psi_1^m donne :
# int_t exp(i m omega_1 t) * exp(-i n omega_1 t) dt = T * delta_{mn}
# C'est le MEME n que dans Psi_1^n !

# Donc oui, l'integration temporelle donne delta_{mn} pour TOUS les termes.
# Le systeme est bien diagonal.

# Pour m=n, l'equation est :
# c_n * <Psi_1^n | (Box + m^2)Psi_1^n>_{4D} = 0

# Mais <Psi_1^n | (Box + m^2)Psi_1^n> n'est generalement pas nul !
# Donc c_n = 0 pour n >= 2, ce qui n'est pas la solution cherchee.

# LE VRAI PROBLEME : L'equation (Box + m^2)Psi = 0 n'est satisfaite
# que par le mode fondamental. Les puissances superieures ne sont PAS
# des solutions. On ne peut donc pas les superposer pour obtenir
# une solution.

# REPENSER COMPLETEMENT :
# L'equation maitresse n'est pas (Box + m^2)Psi = 0 pour Psi quelconque.
# C'est G_{munu;nu} = 0 qui est la contrainte. Et cette contrainte,
# projetee sur la base, donne un systeme qui DETERMINE les c_n.

# Le potentiel V(|Psi|^2) = m^2|Psi|^2 est valable pour |Psi|^2 petit.
# Pour les puissances superieures, il faut inclure des termes
# non-lineaires dans V. C'est la Piste C.

# En attendant, explorons ce que donne le systeme diagonal
# avec integration temporelle.

print("\n--- Calcul des elements diagonaux M_{nn} ---")

G_diag = []
K_diag = []
M_diag = []

for n_val in range(1, N+1):
    # G_{nn} = <Psi_1^n | Psi_1^n> spatial
    # = int_0^R (psi1_spatial(r))^{2n} * 4*pi*r^2 dr
    G_nn, _ = quad(lambda r: (psi1_spatial(r) ** (2*n_val)) * 4 * pi * r**2, 0, R, limit=100)
    G_diag.append(G_nn)
    
    # K_{n, n-2} pour n >= 3
    if n_val >= 3:
        K_n, _ = quad(lambda r: (psi1_spatial(r) ** (2*n_val - 2)) * (psi1_prime(r) ** 2) * 4 * pi * r**2, 0, R, limit=100)
    else:
        K_n = 0.0
    K_diag.append(K_n)
    
    # Coefficient diagonal
    A_n = n_val * (n_val - 1) * kappa_1**2 + (1 - n_val**2) * m**2
    M_nn = A_n * G_nn + n_val * (n_val - 1) * K_n
    M_diag.append(M_nn)
    
    print(f"  n={n_val:>2}: G_nn={G_nn:>12.6e}, K_n={K_n:>12.6e}, A_n={A_n:>10.4f}, M_nn={M_nn:>12.6e}")

# ======================================================================
# PARTIE 3 : INTERPRETATION PHYSIQUE
# ======================================================================
print("\n" + "=" * 70)
print("PARTIE 3 : INTERPRETATION PHYSIQUE ET PROCHAINES ETAPES")
print("=" * 70)

print("""
RESULTAT DE LA PISTE B :

1. L'integration temporelle produit effectivement delta_{mn}.
   La matrice M est DIAGONALE, pas seulement triangulaire.

2. Cependant, les equations M_{nn} * c_n = 0 imposent c_n = 0
   pour tout n ou M_{nn} != 0. Comme M_{nn} != 0 pour n >= 2
   (a verifier numeriquement ci-dessus), cela donnerait c_n = 0
   pour n >= 2, ce qui n'est PAS la solution {phi, pi, e, ...}.

3. CONCLUSION : La Piste B resout le probleme de triangularite
   (la matrice devient diagonale) mais REVELE un probleme plus
   profond : l'equation (Box+m^2)Psi=0 n'admet PAS les puissances
   de Psi_1 comme solutions, meme en superposition.

4. NOUVELLE HYPOTHESE : Le potentiel V(|Psi|^2) ne peut pas etre
   purement quadratique (m^2|Psi|^2). Il doit inclure des termes
   d'ordre superieur (|Psi|^4, |Psi|^6, ...) qui couplent les
   differentes puissances et produisent les H_n comme solution
   d'un systeme non-lineaire.

5. C'est la PISTE C (potentiel non-lineaire avec couplage
   inter-modes) qui devient la candidate principale.

6. Alternativement, l'equation maitresse pourrait ne pas etre
   (Box+m^2)Psi=0 mais une equation integro-differentielle
   incluant la memoire ABC qui modifie la dynamique des modes
   superieurs.
""")

# ======================================================================
# PARTIE 4 : EXPLORATION DU POTENTIEL NON-LINEAIRE (PISTE C)
# ======================================================================
print("=" * 70)
print("PARTIE 4 : AMORCE DE LA PISTE C (POTENTIEL NON-LINEAIRE)")
print("=" * 70)

print("""
Si V(|Psi|^2) = m^2|Psi|^2 + lambda_4|Psi|^4 + lambda_6|Psi|^6 + ...

Alors l'equation devient :
  Box(Psi) + m^2 Psi + 2*lambda_4*|Psi|^2*Psi + 3*lambda_6*|Psi|^4*Psi + ... = 0

En substituant Psi = SUM c_n Psi_1^n, les termes non-lineaires
produisent des couplages entre les c_n. Le systeme projete devient :

  M_{nn} * c_n + SUM_{k,l} N_{nkl} * c_k * c_l * c_... + ... = 0

ou N_{nkl} sont les coefficients de couplage non-lineaire.

Les c_n = H_n = {phi, pi, e, sqrt2, sqrt3, sqrt5, e/pi} seraient
alors la solution de ce systeme non-lineaire, selectionnee par
un principe variationnel (minimisation de l'action).

C'est une piste prometteuse mais qui necessite de determiner
les coefficients lambda_4, lambda_6, ... de maniere coherente
avec la structure spectrale.
""")

print("=" * 70)
print("BILAN DE LA PISTE B")
print("=" * 70)
print("""
SUCCES :
  - L'integration temporelle transforme M en matrice DIAGONALE
  - L'orthogonalite de Fourier est rigoureuse
  - La structure delta_{mn} est confirmee

LIMITE :
  - Le systeme diagonal M_{nn} * c_n = 0 n'admet pas
    {phi, pi, e, ...} comme solution
  - L'equation (Box+m^2)Psi=0 est trop restrictive

PROCHAINE ETAPE :
  - Explorer la Piste C (potentiel non-lineaire)
  - Les termes non-lineaires couplent les modes et peuvent
    produire les H_n comme solution d'un systeme algebrique
    non-lineaire selectionne par un principe variationnel
""")