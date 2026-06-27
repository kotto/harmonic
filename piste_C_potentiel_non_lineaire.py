"""
PISTE C : POTENTIEL NON-LINEAIRE AVEC COUPLAGE INTER-MODES
==========================================================

Principe : Le potentiel V(|Psi|^2) = m^2|Psi|^2 + lambda_4|Psi|^4 + lambda_6|Psi|^6 + ...
contient des termes d'ordre superieur qui couplent les differentes puissances.

Equation complete :
  Box(Psi) + m^2 Psi + 2*lambda_4*|Psi|^2*Psi + 3*lambda_6*|Psi|^4*Psi + ... = 0

Avec Psi = SUM c_n Psi_1^n, les termes non-lineaires produisent des equations
couplees pour les c_n. On utilise les valeurs connues H_n = {phi, pi, e, sqrt2, ...}
pour DETERMINER les lambda_k.

But : Trouver les lambda_k tels que c_n = H_n soit solution du systeme.
"""

import numpy as np
from scipy.integrate import quad
from scipy.special import spherical_jn
import math

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
print("PISTE C : POTENTIEL NON-LINEAIRE AVEC COUPLAGE INTER-MODES")
print("=" * 70)

# ======================================================================
# PARAMETRES PHYSIQUES
# ======================================================================
R = 1.0
kappa_1 = pi / R
m_masse = 1.0
omega_1 = math.sqrt(kappa_1**2 - m_masse**2)
A1 = math.sqrt(pi / (2 * R**3))

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

# ======================================================================
# PARTIE 1 : TERMES LINEAIRES (RAPPEL)
# ======================================================================
print("\n" + "=" * 70)
print("PARTIE 1 : RAPPEL DES TERMES LINEAIRES")
print("=" * 70)

N = 7
M_lin = np.zeros(N)
G_diag = np.zeros(N)

for idx in range(N):
    n_val = idx + 1
    G_nn, _ = quad(lambda r: (psi1_spatial(r) ** (2*n_val)) * 4 * pi * r**2, 0, R, limit=100)
    G_diag[idx] = G_nn
    
    if n_val >= 3:
        K_n, _ = quad(lambda r: (psi1_spatial(r) ** (2*n_val - 2)) * (psi1_prime(r) ** 2) * 4 * pi * r**2, 0, R, limit=100)
    else:
        K_n = 0.0
    
    A_n = n_val * (n_val - 1) * kappa_1**2 + (1 - n_val**2) * m_masse**2
    M_lin[idx] = A_n * G_nn + n_val * (n_val - 1) * K_n
    print(f"  n={n_val}: M_lin[{idx}] = {M_lin[idx]:.4f}")

# ======================================================================
# PARTIE 2 : CALCUL DES ELEMENTS DE MATRICE NON-LINEAIRES
# ======================================================================
print("\n" + "=" * 70)
print("PARTIE 2 : ELEMENTS DE MATRICE NON-LINEAIRES")
print("=" * 70)

def I_nl(indices_list):
    """
    Integrale spatiale : int Psi_1^{sum(indices)} * 4*pi*r^2 dr
    """
    total_power = sum(indices_list)
    I, _ = quad(lambda r: (psi1_spatial(r) ** total_power) * 4 * pi * r**2, 0, R, limit=100)
    return I

print("\nTriplets (k,l,n) contribuant a l'equation pour chaque m :")
for m_val in range(1, 8):
    triplets = []
    for k in range(1, 8):
        for l in range(1, 8):
            n_val = m_val - k - l
            if 1 <= n_val <= 7:
                triplets.append((k, l, n_val))
    if len(triplets) <= 5:
        print(f"  m={m_val}: {len(triplets)} triplets -> {triplets}")
    else:
        print(f"  m={m_val}: {len(triplets)} triplets -> {triplets[:3]}...")

# ======================================================================
# PARTIE 3 : RESOLUTION DU SYSTEME NON-LINEAIRE
# ======================================================================
print("\n" + "=" * 70)
print("PARTIE 3 : RESOLUTION — DETERMINATION DES lambda")
print("=" * 70)

print("\nCalcul des sommes non-lineaires S_4[m] (terme quartique) :")

S4 = np.zeros(N)
for m_idx in range(N):
    m_val = m_idx + 1
    somme = 0.0
    for k in range(1, N+1):
        for l in range(1, N+1):
            n_val = m_val - k - l
            if 1 <= n_val <= N:
                I_val = I_nl([k, l, n_val, m_val])
                somme += H_EXACT[k-1] * H_EXACT[l-1] * H_EXACT[n_val-1] * I_val
    S4[m_idx] = somme

print(f"\n{'m':>3} {'M_lin * H_m':>18} {'S_4[m]':>18} {'-M_lin*H_m / S4':>18}")
print("-" * 60)
for m_idx in range(N):
    m_val = m_idx + 1
    M_H = M_lin[m_idx] * H_EXACT[m_idx]
    ratio = -M_H / S4[m_idx] if abs(S4[m_idx]) > 1e-15 else float('inf')
    print(f"{m_val:>3} {M_H:>18.6e} {S4[m_idx]:>18.6e} {ratio:>18.6f}")

# ======================================================================
# PARTIE 4 : OPTIMISATION — TROUVER LES lambda OPTIMAUX
# ======================================================================
print("\n" + "=" * 70)
print("PARTIE 4 : OPTIMISATION DES COEFFICIENTS lambda")
print("=" * 70)

print("\nCalcul des sommes S_6[m] (terme sextique) :")
S6 = np.zeros(N)
for m_idx in range(N):
    m_val = m_idx + 1
    somme = 0.0
    for k in range(1, N+1):
        for l in range(1, N+1):
            for p in range(1, N+1):
                for q in range(1, N+1):
                    n_val = m_val - k - l - p - q
                    if 1 <= n_val <= N:
                        I_val = I_nl([k, l, p, q, n_val, m_val])
                        somme += (H_EXACT[k-1] * H_EXACT[l-1] * H_EXACT[p-1] * 
                                 H_EXACT[q-1] * H_EXACT[n_val-1] * I_val)
    S6[m_idx] = somme

# Moindres carres
A = np.zeros((N, 2))
b = np.zeros(N)

for m_idx in range(N):
    A[m_idx, 0] = S4[m_idx]
    A[m_idx, 1] = S6[m_idx]
    b[m_idx] = -M_lin[m_idx] * H_EXACT[m_idx]

ATA = A.T @ A
ATb = A.T @ b

try:
    lambdas = np.linalg.solve(ATA, ATb)
    lambda_4_opt = lambdas[0]
    lambda_6_opt = lambdas[1]
    
    print(f"\nCoefficients optimaux (moindres carres) :")
    print(f"  lambda_4 = {lambda_4_opt:.10f}")
    print(f"  lambda_6 = {lambda_6_opt:.10f}")
    
    # Verification
    print(f"\nVerification des equations (proches de 0) :")
    print(f"{'m':>3} {'Residu':>20} {'Erreur rel.':>15}")
    print("-" * 45)
    for m_idx in range(N):
        residu = M_lin[m_idx] * H_EXACT[m_idx] + lambda_4_opt * S4[m_idx] + lambda_6_opt * S6[m_idx]
        erreur_rel = abs(residu) / (abs(M_lin[m_idx] * H_EXACT[m_idx]) + 1e-15)
        print(f"{m_idx+1:>3} {residu:>20.6e} {erreur_rel:>15.6e}")
        
except np.linalg.LinAlgError as err:
    print(f"\nErreur de resolution : {err}")
    print("La matrice A^T A est peut-etre singuliere.")
    lambda_4_opt = 0
    lambda_6_opt = 0

# ======================================================================
# PARTIE 5 : ANALYSE
# ======================================================================
print("\n" + "=" * 70)
print("PARTIE 5 : ANALYSE DES RESULTATS")
print("=" * 70)

if lambda_4_opt != 0:
    print(f"\nlambda_4 = {lambda_4_opt:.10f}")
    print(f"lambda_6 = {lambda_6_opt:.10f}")

    # Rapport lambda_6 / lambda_4
    if abs(lambda_4_opt) > 1e-15:
        rapport = lambda_6_opt / lambda_4_opt
        print(f"\nRapport lambda_6 / lambda_4 = {rapport:.6f}")
        print(f"  = {rapport/phi:.4f} * phi")
        print(f"  = {rapport/pi:.4f} * pi")
        print(f"  = {rapport/e:.4f} * e")

    print("\nHypotheses pour lambda_4 :")
    candidates = {
        'phi^-1': 1/phi, 'phi^-2': phi**-2, 'phi^-3': phi**-3, 'phi^-4': phi**-4,
        '1/pi': 1/pi, '1/e': 1/e, '1/(phi*pi)': 1/(phi*pi), '1/(phi*e)': 1/(phi*e)
    }
    for name, val in candidates.items():
        err = abs(lambda_4_opt - val) / abs(val) if abs(val) > 1e-15 else float('inf')
        print(f"  lambda_4 ~ {name:>15} = {val:>15.10f}  (erreur: {err*100:.3f}%)")

print("\n" + "=" * 70)
print("CONCLUSION DE LA PISTE C")
print("=" * 70)
print("""
Si les ratios ci-dessus sont constants a travers les modes (m=1..7),
cela signifie qu'un seul lambda_4 suffit a satisfaire TOUTES les equations.
C'est une signature forte d'auto-coherence.

Si les ratios varient, cela indique que des termes d'ordre superieur
(lambda_6, lambda_8, ...) sont necessaires.

Si les lambda optimaux s'expriment comme combinaisons simples des H_n
(ex: lambda_4 = phi^{-3}), la structure est fermee et auto-consistante :
  Les H_n determinent les lambda.
  Les lambda determinent les H_n.
  -> Point fixe du systeme spectral.
""")