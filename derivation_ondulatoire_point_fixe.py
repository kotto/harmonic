# -*- coding: utf-8 -*-
"""
DERIVATION ONDULATOIRE : INTEGRALES 4D + POINT FIXE
====================================================
Etapes 1-3 de la derivation rigoureuse :
  1. Calculer les integrales de recouvrement 4D G_{mnpq}
  2. Resoudre le systeme algebrique par iteration de point fixe
  3. Verifier numeriquement que H_n est le point fixe unique

Principe : L'equation maitresse ondulatoire est R_phi[Psi] = 0
  ou R_phi[Psi] = Psi - N * Psi * exp(i * phi * |Psi|^2 / <|Psi|^2>)

En projetant sur (Psi_1)^m, on obtient le systeme algebrique :
  c_m = N * sum_{k=0}^{inf} (i*phi)^k/k! * S_m^{(k)}(c)
  
  ou S_m^{(k)} sont des contractions tensorielles des G_{mnpq} avec les c_n.
"""

import numpy as np
import math
from scipy.integrate import quad
from scipy.special import spherical_jn

# ======================================================================
# CONSTANTES FONDAMENTALES
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

print("=" * 85)
print("DERIVATION ONDULATOIRE : INTEGRALES 4D + POINT FIXE ALGEBRIQUE")
print("=" * 85)

# ======================================================================
# ETAPE 1 : CALCUL DES INTEGRALES DE RECOUVREMENT 4D
# ======================================================================
print()
print("=" * 85)
print("ETAPE 1 : CALCUL DES INTEGRALES DE RECOUVREMENT 4D")
print("=" * 85)

# Parametres de la cavite spherique
R = 1.0  # rayon de la cavite
kappa_1 = pi / R  # premier zero de j0
omega_1 = math.sqrt(kappa_1**2 - 1.0)  # relation de dispersion KG (m=1)
T = 2 * pi / omega_1  # periode temporelle
A1 = math.sqrt(pi / (2 * R**3))  # amplitude normalisee

print()
print(f"  Parametres de la cavite :")
print(f"    R = {R}")
print(f"    kappa_1 = pi/R = {kappa_1:.6f}")
print(f"    omega_1 = sqrt(kappa_1^2 - 1) = {omega_1:.6f}")
print(f"    T = 2*pi/omega_1 = {T:.6f}")
print(f"    A1 = sqrt(pi/(2*R^3)) = {A1:.6f}")

# L'onde maitresse : Psi_1(r,t) = A1 * j0(kappa_1 * r) * exp(-i * omega_1 * t)
# (Psi_1)^n = A1^n * [j0(kappa_1 * r)]^n * exp(-i * n * omega_1 * t)

print()
print("1.1 Separation espace-temps des integrales 4D :")
print()
print("    G_{m,n,p,q} = integrale_4D (Psi_1)^m * (Psi_1^*)^n * (Psi_1)^p * (Psi_1^*)^q")
print()
print("    = A1^{m+n+p+q} * I_spatiale(m+n+p+q) * I_temporelle(m-n+p-q)")
print()
print("    I_temporelle(k) = integrale_0^T exp(-i * k * omega_1 * t) dt")
print("                    = T * delta_{k,0}  (orthogonalite de Fourier)")
print()
print("    -> Seuls les termes avec m-n+p-q = 0 survivent !")
print("    -> Contrainte : m+p = n+q")
print()
print("    I_spatiale(s) = integrale_0^R [j0(kappa_1 * r)]^s * 4*pi*r^2 dr")

# Calcul des integrales spatiales I_s pour s = 1..20
print()
print("1.2 Calcul des integrales spatiales I_s :")
print(f"  {'s':>4} {'I_s (numerique)':>20} {'I_s / I_1':>15} {'I_s * 1e6':>15}")
print(f"  {'-'*60}")

I_spatiales = {}
for s in range(1, 29):
    def integrand_spatial(r, s_val=s):
        if r < 1e-15:
            return 4 * pi * r**2  # j0(0) = 1
        return (spherical_jn(0, kappa_1 * r) ** s_val) * 4 * pi * r**2
    
    I_s, err = quad(integrand_spatial, 0, R, limit=200, epsabs=1e-12, epsrel=1e-12)
    I_spatiales[s] = I_s
    ratio = I_s / I_spatiales[1] if 1 in I_spatiales else 0
    print(f"  {s:>4} {I_s:>20.12e} {ratio:>15.10f} {I_s*1e6:>15.10f}")

# Normalisation : I_1 doit etre = 1 (Psi_1 normalisee)
print()
print(f"  Verification normalisation : I_1 = {I_spatiales[1]:.12e}")
print(f"    (Devrait etre ~1 car A1^2 * I_1 * T = 1)")

# Factor d'amplitude pour chaque integrale 4D
# G_{mnpq} = A1^{m+n+p+q} * I_spatiale(m+n+p+q) * T * delta(m-n+p-q, 0)
print()
print("1.3 Construction du tenseur G_{m,n,p,q} (elements non nuls) :")
print()

# On construit le tenseur pour m,n,p,q = 1..7
# Pour chaque quadruplet, m-n+p-q doit etre 0 -> m+p = n+q

G_tensor = np.zeros((N_MODES+1, N_MODES+1, N_MODES+1, N_MODES+1))

print(f"  Contrainte m+p = n+q filtre les elements non nuls :")
compte = 0
for m in range(1, N_MODES+1):
    for n in range(1, N_MODES+1):
        for p in range(1, N_MODES+1):
            for q in range(1, N_MODES+1):
                if m + p == n + q:
                    s_tot = m + n + p + q
                    if s_tot > 28:
                        continue
                    amplitude = A1**s_tot
                    I_s = I_spatiales[s_tot]
                    G_val = amplitude * I_s * T
                    G_tensor[m, n, p, q] = G_val
                    compte += 1

print(f"  Nombre d'elements non nuls : {compte} sur {7**4} = {compte}/{2401} = {compte/2401*100:.1f}%")
print()

# Afficher quelques exemples
exemples = [(1,1,1,1), (1,1,2,2), (1,2,2,1), (2,2,2,2), (1,1,3,3), (2,3,3,2)]
for m,n,p,q in exemples:
    print(f"  G({m},{n},{p},{q}) = {G_tensor[m,n,p,q]:.12e}")

print()
print("  Remarque : G_{m,n,p,q} est SYMETRIQUE par echange (m,n)<->(p,q)")
print("  et par echange (m,p)<->(n,q) grace a la condition m+p=n+q.")

# ======================================================================
# ETAPE 2 : CONSTRUCTION DU SYSTEME ALGEBRIQUE
# ======================================================================
print()
print("=" * 85)
print("ETAPE 2 : SYSTEME ALGEBRIQUE DU POINT FIXE")
print("=" * 85)

print()
print("2.1 Rappel de l'equation maitresse :")
print()
print("    R_phi[Psi] = Psi - N * Psi * exp(i * phi * |Psi|^2 / <|Psi|^2>) = 0")
print()
print("    ou Psi = sum_{n=1}^{7} c_n * (Psi_1)^n")
print()
print("2.2 Projection sur (Psi_1)^m :")
print()
print("    c_m = N * < (Psi_1)^m | Psi * exp(i * phi * |Psi|^2 / <|Psi|^2>) >_{4D}")
print()
print("    avec le developpement : exp(i*phi*X) = sum_{k=0}^{inf} (i*phi)^k/k! * X^k")
print("    et X = |Psi|^2 / <|Psi|^2>")

# Calcul de la norme <|Psi|^2> pour les H_n
def norme_carree(c_vec):
    """Calcule <|Psi|^2> = integrale_4D |sum c_n (Psi_1)^n|^2"""
    # <|Psi|^2> = sum_{m,n} c_m c_n^* <(Psi_1)^m | (Psi_1^*)^n>_4D
    # L'integrale temporelle donne delta_{m-n, 0} -> m=n
    # Donc <|Psi|^2> = sum_n |c_n|^2 * <(Psi_1)^n | (Psi_1^*)^n>
    norm2 = 0.0
    for n in range(1, N_MODES+1):
        # <(Psi_1)^n | (Psi_1^*)^n> = A1^{2n} * I_spatiale(2n) * T
        if 2*n <= 28:
            G_nn = A1**(2*n) * I_spatiales[2*n] * T
        else:
            G_nn = 0.0
        norm2 += abs(c_vec[n-1])**2 * G_nn
    return norm2

# Verifier la normalisation
norm2_H = norme_carree(H_EXACT)
print()
print(f"  <|Psi|^2> pour H_n = {norm2_H:.12e}")

# Calcul de la projection au premier ordre (k=0)
print()
print("2.3 Projection au premier ordre (k=0, terme constant) :")
print()
print("    Terme k=0 : <(Psi_1)^m | Psi> = sum_n c_n * G_{m,0,n,0}")
print("    ou G_{m,0,n,0} = <(Psi_1)^m | (Psi_1)^n>")
print()

# Verification : la base n'est pas orthogonale !
print("  Matrice de recouvrement M_{mn} = <(Psi_1)^m | (Psi_1)^n> :")
mn_label = "m\\n"
print(f"  {mn_label:>6}", end="")
for n in range(1, N_MODES+1):
    print(f"{n:>12}", end="")
print()
print(f"  {'-'*90}")

for m in range(1, N_MODES+1):
    print(f"  {m:>6}", end="")
    for n in range(1, N_MODES+1):
        # Integrale temporelle : exp(-i*m*omega*t) * exp(-i*n*omega*t)
        # -> integre a 0 sur T sauf si m=n (mais attendez, c'est (Psi_1)^m * (Psi_1)^n)
        # (Psi_1)^m = A1^m * [j0]^m * exp(-i*m*omega*t)
        # (Psi_1)^n = A1^n * [j0]^n * exp(-i*n*omega*t)
        # Le produit temporel : exp(-i*(m+n)*omega*t) -> integre a 0 sur [0,T] sauf si m+n=0
        # m,n > 0 -> m+n > 0 -> l'integrale temporelle est NULLE !
        # ATTENTION : c'est <(Psi_1)^m | (Psi_1)^n> avec conjugue ?
        # Si on prend le produit scalaire standard : <f|g> = int f* g
        # <(Psi_1)^m | (Psi_1)^n> = int (Psi_1^*)^m * (Psi_1)^n
        # Partie temporelle : exp(+i*m*omega*t) * exp(-i*n*omega*t) = exp(i*(m-n)*omega*t)
        # Integre a 0 sur T sauf si m=n !
        # Donc la matrice est DIAGONALE grace a Fourier !
        if m == n:
            G_mn = A1**(2*m) * I_spatiales[2*m] * T
        else:
            G_mn = 0.0
        print(f"{G_mn:>12.6e}", end="")
    print()

print()
print("  La base est ORTHOGONALE grace a la separation temporelle !")
print("  <(Psi_1)^m | (Psi_1)^n> = delta_{m,n} * A1^{2m} * I_spatial(2m) * T")

# ======================================================================
# ETAPE 3 : ITERATION DE POINT FIXE
# ======================================================================
print()
print("=" * 85)
print("ETAPE 3 : ITERATION DE POINT FIXE ALGEBRIQUE")
print("=" * 85)

print()
print("3.1 Le systeme complet tronque a l'ordre K_max :")
print()
print("    c_m = N * sum_{k=0}^{K_max} (i*phi)^k/k! * sum_{n_1..n_k, p_1..p_k}")
print("          sum_j c_j * c_{n_1} c_{p_1}^* ... c_{n_k} c_{p_k}^*")
print("          * G(m, j, n_1+...+n_k, p_1+...+p_k) / (<|Psi|^2>)^k")
print()
print("    ou G(m, j, N_tot, P_tot) est le coefficient tensoriel apres")
print("    contraction des indices spatiaux.")

# Pour rendre le calcul traitable, on va tronquer au premier ordre non-trivial
# et supposer que la base est quasi-orthogonale (ce qui est vrai temporellement)

print()
print("3.2 Simplification : utilisation de l'orthogonalite temporelle")
print()
print("    La contrainte temporelle reduit considerablement le nombre")
print("    de termes. Pour chaque ordre k, seuls les termes satisfaisant")
print("    la conservation de la 'charge' temporelle survivent.")
print()
print("    Au premier ordre (k=0) : c_m = N * sum_n c_n * delta_{m,n} * G_nn")
print("    -> c_m = N * c_m * G_mm")
print("    -> N = 1/G_mm pour chaque m !")
print("    Le facteur N depend de m -> il faut un N unique.")
print("    Cela fixe une condition de CONSISTANCE.")

# Calcul des G_mm (normes des modes)
G_mm_vals = np.zeros(N_MODES+1)
for m in range(1, N_MODES+1):
    if 2*m <= 28:
        G_mm_vals[m] = A1**(2*m) * I_spatiales[2*m] * T
    else:
        G_mm_vals[m] = 0.0

print()
print("  Normes des modes G_mm = <(Psi_1)^m | (Psi_1)^m> :")
for m in range(1, N_MODES+1):
    print(f"    m={m}: G_mm = {G_mm_vals[m]:.12e}")

print()
print("  Condition de consistance au 1er ordre : N * G_mm = 1 pour tout m")
print("  C'est IMPOSSIBLE car G_mm varie avec m.")
print("  -> Le point fixe necessite les ordres superieurs (k>=1)")
print("  -> Les termes non-lineaires couplent les modes et restaurent")
print("     la consistance avec un N unique.")

# ======================================================================
# ETAPE 3 (suite) : RESOLUTION ITERATIVE COMPLETE
# ======================================================================
print()
print("3.3 Resolution iterative du systeme complet (k=0,1,2) :")
print()

def compute_N_and_residual(c_vec, K_max=2):
    """
    Calcule le facteur N optimal et le residu du systeme pour un c donne.
    N est choisi pour minimiser le residu au sens des moindres carres.
    """
    c = np.array(c_vec, dtype=complex)
    norm2 = norme_carree(c)
    
    # Calcul de F_m = <(Psi_1)^m | Psi * exp(i*phi*|Psi|^2/<|Psi|^2>)>
    F = np.zeros(N_MODES, dtype=complex)
    
    for m in range(1, N_MODES+1):
        # Terme k=0 : <(Psi_1)^m | Psi>
        # = sum_j c_j * <(Psi_1)^m | (Psi_1)^j>
        # = c_m * G_mm (orthogonalite temporelle)
        F[m-1] = c[m-1] * G_mm_vals[m]
        
        if K_max >= 1:
            # Terme k=1 : i*phi * <(Psi_1)^m | Psi * |Psi|^2/<|Psi|^2> >
            # |Psi|^2 = sum_{a,b} c_a c_b^* (Psi_1)^a (Psi_1^*)^b
            # <(Psi_1)^m | Psi * |Psi|^2> = sum_{j,a,b} c_j c_a c_b^* 
            #   * <(Psi_1)^m | (Psi_1)^j (Psi_1)^a (Psi_1^*)^b>
            # Temporellement : exp(-i*j*omega*t) * exp(-i*a*omega*t) * exp(+i*b*omega*t)
            # -> integre a 0 sauf si j+a-b = m (car conjugue de (Psi_1)^m = (Psi_1^*)^m
            # donne exp(+i*m*omega*t))
            # Condition : m = j+a-b  -> b = j+a-m (doit etre > 0)
            term_k1 = 0.0 + 0.0j
            for j in range(1, N_MODES+1):
                for a_p in range(1, N_MODES+1):
                    b = j + a_p - m
                    if 1 <= b <= N_MODES:
                        # Coefficient spatial
                        s_tot = m + j + a_p + b
                        if s_tot > 28:
                            continue
                        G_val = A1**s_tot * I_spatiales[s_tot] * T
                        term_k1 += c[j-1] * c[a_p-1] * np.conj(c[b-1]) * G_val
            F[m-1] += 1j * phi * term_k1 / norm2
    
    # N optimal : minimise sum_m |c_m - N * F_m|^2
    # N = sum_m c_m^* F_m / sum_m |F_m|^2 (estimateur des moindres carres)
    num = np.sum(np.conj(c) * F)
    den = np.sum(np.abs(F)**2)
    if abs(den) < 1e-30:
        N = 1.0
    else:
        N = num / den
    
    # Residu
    residu = c - N * F
    err = np.linalg.norm(residu) / np.linalg.norm(c)
    
    return N, F, err

# Test avec les H_n
c_H = H_EXACT + 0j
N_H, F_H, err_H = compute_N_and_residual(c_H, K_max=2)
print(f"  Pour c = H_n (exact) :")
print(f"    N = {N_H:.10f}")
print(f"    Erreur relative = {err_H:.6e}")
print()

# Iteration de point fixe
print("3.4 Iteration de point fixe (methode de Newton simplifiee) :")
print()

def iteration_point_fixe(c_init, n_iter=50, lr=0.3, K_max=2):
    """Itere c_{n+1} = (1-lr)*c_n + lr*N*F(c_n)"""
    c = np.array(c_init, dtype=complex)
    erreurs = []
    
    for it in range(n_iter):
        N_val, F_val, err = compute_N_and_residual(c, K_max=K_max)
        erreurs.append(err)
        
        # Mise a jour
        c_new = N_val * F_val
        # Renormaliser pour eviter divergence
        c_new = c_new / np.linalg.norm(c_new) * np.linalg.norm(c)
        c = (1 - lr) * c + lr * c_new
        
        if it % 10 == 0 or it == n_iter-1:
            amplitudes = np.abs(c)
            ratio = amplitudes / H_EXACT if np.linalg.norm(H_EXACT) > 0 else np.zeros(N_MODES)
            print(f"    iter {it:>3d}: err={err:.6e}, |c|={np.round(amplitudes, 4)}, ratio/H={np.round(ratio, 4)}")
    
    return c, erreurs

# Test 1 : initialisation avec H_n (point fixe connu)
print()
print("  Test 1 : Initialisation avec H_n :")
c_final1, errs1 = iteration_point_fixe(c_H, n_iter=30, lr=0.3, K_max=2)
print()

# Test 2 : initialisation aleatoire
print("  Test 2 : Initialisation aleatoire :")
np.random.seed(42)
c_random = np.random.rand(N_MODES) * 5 + 1
c_final2, errs2 = iteration_point_fixe(c_random, n_iter=50, lr=0.2, K_max=2)
print()

# Test 3 : initialisation uniforme
print("  Test 3 : Initialisation uniforme (tous 1) :")
c_uniform = np.ones(N_MODES)
c_final3, errs3 = iteration_point_fixe(c_uniform, n_iter=50, lr=0.2, K_max=2)
print()

# Test 4 : initialisation lineaire
print("  Test 4 : Initialisation lineaire (1,2,3,4,5,6,7) :")
c_linear = np.arange(1, N_MODES+1, dtype=float)
c_final4, errs4 = iteration_point_fixe(c_linear, n_iter=50, lr=0.2, K_max=2)

# ======================================================================
# ETAPE 4 : VERIFICATION DE L'UNICITE
# ======================================================================
print()
print("=" * 85)
print("ETAPE 4 : VERIFICATION DE L'UNICITE DU POINT FIXE")
print("=" * 85)

print()
print("4.1 Comparaison des points fixes obtenus :")
print()

def comparer_avec_H(c_vec, nom):
    """Compare un vecteur avec H_n apres normalisation."""
    c = np.abs(c_vec)
    # Normaliser pour que c[0] = phi (H_1)
    c_norm = c / c[0] * H_EXACT[0]
    erreur = np.linalg.norm(c_norm - H_EXACT) / np.linalg.norm(H_EXACT)
    return c_norm, erreur

for nom, c_final in [("H_n init", c_final1), ("Random init", c_final2), 
                       ("Uniform init", c_final3), ("Linear init", c_final4)]:
    c_norm, err = comparer_avec_H(c_final, nom)
    print(f"  {nom:<15s}: |c| = {np.round(np.abs(c_final), 4)}")
    print(f"  {'':15s}  ratio/H = {np.round(c_norm / H_EXACT, 4)}")
    print(f"  {'':15s}  erreur relative = {err:.6e}")
    print()

# ======================================================================
# SYNTHESE
# ======================================================================
print()
print("=" * 85)
print("SYNTHESE DES RESULTATS")
print("=" * 85)

print()
print("  ETAT DE LA DERIVATION ONDULATOIRE :")
print()
print("  1. Integrales 4D : CALCULEES (231 elements non nuls sur 2401)")
print("     - Base {(Psi_1)^n} est ORTHOGONALE (Fourier)")
print("     - Integrales spatiales I_s pour s=1..28")
print()
print("  2. Systeme algebrique : CONSTRUIT (K_max=2 : ordres k=0,1)")
print("     - N calcule par moindres carres a chaque iteration")
print()
print("  3. Iteration : RESULTAT NEGATIF IMPORTANT")
print("     - H_n n'est PAS un point fixe du systeme tronque a K_max=2")
print("     - Toutes les initialisations divergent vers ZERO")
print("     - L'operateur R_phi tronque est TROP SIMPLE")
print()
print("  4. Analyse : POURQUOI CA NE MARCHE PAS")
print("     - Au 1er ordre (k=0) : c_m = N * c_m * G_mm")
print("       -> N devrait etre different pour chaque mode")
print("     - Le terme k=1 (non-lineaire) est INSUFFISANT pour")
print("       compenser et creer un point fixe non-trivial")
print("     - Il faut soit :")
print("       a) Inclure les ordres superieurs (k=2,3,...)")
print("       b) Repenser l'operateur R_phi (autre forme d'auto-interference)")
print("       c) Ajouter un potentiel V(|Psi|^2) explicite")
print()
print("  PROCHAINES ETAPES :")
print("    1. Inclure le terme k=2 (ordre phi^2/2)")
print("    2. Tester d'autres operateurs d'auto-interference")
print("    3. Coupler avec un potentiel non-lineaire V(|Psi|^2)")
print("    4. Verifier si un point fixe non-trivial emerge")

print("=" * 85)
print("FIN DE L'IMPLEMENTATION")
print("=" * 85)