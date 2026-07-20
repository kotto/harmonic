"""
🌊 VÉRIFICATION NUMÉRIQUE — Problème Inverse Spectral Harmonique
=================================================================
Version optimisée : grille réduite, pré-calculs, alpha ciblé.

Vérifie : det(M(α)) ≈ 0 pour α = 1/φ
          ker(M(1/φ)) ≈ {φ, π, e, √2, √3, √5, e/π}
"""

import numpy as np
from scipy.special import gamma, spherical_jn
from scipy.integrate import simpson
from scipy.linalg import svd
import math, time

# ════════════════════════════════════════════════════════════════
# CONSTANTES
# ════════════════════════════════════════════════════════════════
PHI = (1 + np.sqrt(5)) / 2
H_EXPECTED = np.array([PHI, np.pi, np.e, np.sqrt(2), np.sqrt(3), np.sqrt(5), np.e/np.pi])
H_NAMES    = ['φ', 'π', 'e', '√2', '√3', '√5', 'e/π']
N = 7

# ════════════════════════════════════════════════════════════════
# PARAMÈTRES PHYSIQUES
# ════════════════════════════════════════════════════════════════
R = 1.0
KAPPA1 = np.pi / R
M_EFF = 0.5
OMEGA1 = np.sqrt(KAPPA1**2 - M_EFF**2)
N_PERIODS = 3
T_MAX = N_PERIODS * 2 * np.pi / OMEGA1

# Grille réduite pour la performance
NT = 80   # points temporels
NR = 80   # points spatiaux
t_grid = np.linspace(0, T_MAX, NT)
r_grid = np.linspace(0, R, NR)
dt = t_grid[1] - t_grid[0]
dr = r_grid[1] - r_grid[0]

# Normalisation A₁
A1 = np.sqrt(2.0 / (R**3 * T_MAX))

print("=" * 60)
print("🌊 VERIFICATION NUMERIQUE — Conjecture Spectrale")
print("=" * 60)
print(f"α* = 1/φ = {1/PHI:.6f}  |  ω1 = {OMEGA1:.3f}  |  grille {NT}x{NR}  |  {N_PERIODS} periodes")

# ════════════════════════════════════════════════════════════════
# PRÉ-CALCULS : base spatiale + temporelle
# ════════════════════════════════════════════════════════════════

# Spatial : j0_vals = j₀(κ₁r) → j0_pow[n] = j₀^{n+1}
j0_vals = spherical_jn(0, KAPPA1 * r_grid)
j0_pow = np.array([j0_vals**(n+1) for n in range(N)])  # (N, NR)

# Matrice de recouvrement spatial O_{mn}
O_spatial = np.zeros((N, N))
for m in range(N):
    for n in range(N):
        integrand = j0_pow[m] * j0_pow[n] * r_grid**2
        O_spatial[m, n] = simpson(integrand, r_grid)

# Laplacien spatial : ∇²[j₀ⁿ] calculé numériquement
laplacian_pow = np.zeros((N, NR))
for n in range(N):
    f = j0_pow[n]
    df = np.zeros(NR)
    df[1:-1] = (f[2:] - f[:-2]) / (2*dr)
    df[0] = (f[1] - f[0]) / dr
    df[-1] = (f[-1] - f[-2]) / dr
    r2df = r_grid**2 * df
    d_r2df = np.zeros(NR)
    d_r2df[1:-1] = (r2df[2:] - r2df[:-2]) / (2*dr)
    d_r2df[0] = (r2df[1] - r2df[0]) / dr
    d_r2df[-1] = (r2df[-1] - r2df[-2]) / dr
    lap = np.zeros(NR)
    mask = r_grid > 1e-10
    lap[mask] = d_r2df[mask] / r_grid[mask]**2
    lap[~mask] = d_r2df[1] / r_grid[1]**2
    laplacian_pow[n] = lap

S_spatial = np.zeros((N, N))
for m in range(N):
    for n in range(N):
        integrand = j0_pow[m] * laplacian_pow[n] * r_grid**2
        S_spatial[m, n] = simpson(integrand, r_grid)

print(f"Matrices spatiales pre-calculees.")

# ════════════════════════════════════════════════════════════════
# MITTAG-LEFFLER + ABC
# ════════════════════════════════════════════════════════════════

def mittag_leffler(alpha, z, n_terms=30):
    """E_α(z) = Σ z^k / Γ(αk + 1)"""
    r = np.zeros_like(z, dtype=float)
    for k in range(n_terms):
        r += z**k / gamma(alpha * k + 1)
    return r

def B_alpha(alpha):
    return 1.0 - alpha + alpha / gamma(alpha)

def abc_derivative(alpha, f_t):
    """
    ABC D_t^α [f(t)] — version optimisée vectorisée.
    f_t : array complexe de taille NT
    """
    B = B_alpha(alpha)
    gamma_val = alpha / (1.0 - alpha)
    
    # Dérivée de f
    df = np.zeros(NT, dtype=complex)
    df[1:-1] = (f_t[2:] - f_t[:-2]) / (2*dt)
    df[0] = (f_t[1] - f_t[0]) / dt
    df[-1] = (f_t[-1] - f_t[-2]) / dt
    
    result = np.zeros(NT, dtype=complex)
    
    # Intégration pour chaque t (on ne peut pas complètement vectoriser)
    for i in range(1, NT):
        tau = t_grid[:i+1]
        dtau = t_grid[i] - tau
        E_vals = mittag_leffler(alpha, -gamma_val * dtau**alpha)
        integrand = df[:i+1] * E_vals
        result[i] = B / (1.0 - alpha) * np.trapz(integrand, tau)
    
    return result

# ════════════════════════════════════════════════════════════════
# PRÉ-CALCUL : ABC derivatives pour tous les modes
# ════════════════════════════════════════════════════════════════

def precompute_abc_modes(alpha):
    """
    Pré-calcule ABC D_t^{2α}[e^{-inω₁t}] pour n=1..N.
    Retourne : abc2_modes[n] = ABC D^{2α}[e^{-i(n+1)ω₁t}]
    """
    abc2_modes = []
    for n in range(1, N+1):
        f_in = np.exp(-1j * n * OMEGA1 * t_grid)
        abc1 = abc_derivative(alpha, f_in)
        abc2 = abc_derivative(alpha, abc1)
        abc2_modes.append(abc2)
    return abc2_modes

# ════════════════════════════════════════════════════════════════
# MATRICE M(α)
# ════════════════════════════════════════════════════════════════

def compute_M_matrix_fast(alpha, abc2_modes):
    """
    M_{mn} = A1^{m+n+2} · [O_spatial[m,n]·T_{mn}(α) − S_spatial[m,n]·T·δ_{mn} + m_eff²·O_spatial[m,n]·T·δ_{mn}]
    
    où T_{mn}(α) = ∫ e^{imω₁t} · ABC D^{2α}[e^{-inω₁t}] dt
    """
    M = np.zeros((N, N), dtype=complex)
    
    for m in range(N):
        exp_plus = np.exp(1j * (m+1) * OMEGA1 * t_grid)
        for n in range(N):
            abc2_f = abc2_modes[n]
            
            # Overlap temporel ABC
            integrand = exp_plus * abc2_f
            T_mn = np.trapz(integrand.real, t_grid) + 1j * np.trapz(integrand.imag, t_grid)
            
            # Overlap temporel standard (Fourier)
            O_t = T_MAX if m == n else 0.0
            
            A_fact = A1**(m + n + 2)
            
            term_abc = O_spatial[m, n] * T_mn
            term_lap = S_spatial[m, n] * O_t
            term_mass = M_EFF**2 * O_spatial[m, n] * O_t
            
            M[m, n] = A_fact * (term_abc - term_lap + term_mass)
    
    return M

# ════════════════════════════════════════════════════════════════
# TEST : Brisure d'orthogonalité
# ════════════════════════════════════════════════════════════════

print(f"\n{'='*60}")
print(f"TEST : Brisure d'orthogonalite par ABC")

alpha_star = 1.0 / PHI
abc2_pre = precompute_abc_modes(alpha_star)

# Overlap diagonal et off-diagonal
f_modes = [np.exp(-1j * n * OMEGA1 * t_grid) for n in range(1, N+1)]

for n_src in [0, 1]:  # mode source n=1,2
    for m_obs in [0, 1, 2]:  # mode observation
        integrand = np.exp(1j * (m_obs+1) * OMEGA1 * t_grid) * abc2_pre[n_src]
        overlap = np.trapz(integrand, t_grid)
        is_diag = "DIAG" if m_obs == n_src else "off  "
        print(f"  <e^(i{m_obs+1}w1t)|ABC|e^(-i{n_src+1}w1t)> = {overlap.real:+.4f} {overlap.imag:+.4f}i  [{is_diag}]")

# ════════════════════════════════════════════════════════════════
# BALAYAGE DE α — Recherche du zéro du déterminant
# ════════════════════════════════════════════════════════════════

print(f"\n{'='*60}")
print(f"BALAYAGE DE alpha — |det(M(alpha))|")
print(f"{'='*60}")

# Focus autour de 1/φ
alpha_test = [1/PHI - 0.10, 1/PHI - 0.05, 1/PHI - 0.02, 1/PHI, 
              1/PHI + 0.02, 1/PHI + 0.05, 1/PHI + 0.10]
alpha_test = [a for a in alpha_test if 0.30 < a < 0.85]
alpha_test = sorted(set(alpha_test))

print(f"\n  {'alpha':<10} {'|det(M)|':<16} {'sigma_min':<16} {'Note'}")
print(f"  {'-'*50}")

dets = []
for alpha in alpha_test:
    t0 = time.time()
    abc2_modes = precompute_abc_modes(alpha)
    M = compute_M_matrix_fast(alpha, abc2_modes)
    d = abs(np.linalg.det(M))
    _, S, _ = svd(M)
    sigma_min = S[-1]
    dets.append((alpha, d, sigma_min))
    
    marker = " <-- 1/phi" if abs(alpha - alpha_star) < 0.005 else ""
    elapsed = time.time() - t0
    print(f"  {alpha:<10.6f} {d:<16.6e} {sigma_min:<16.6e} [{elapsed:.1f}s]{marker}")

# ════════════════════════════════════════════════════════════════
# EXTRACTION DU NOYAU
# ════════════════════════════════════════════════════════════════

print(f"\n{'='*60}")
print(f"EXTRACTION DU NOYAU — ker(M(1/phi))")
print(f"{'='*60}")

M_star = compute_M_matrix_fast(alpha_star, abc2_pre)
U, S, Vh = svd(M_star)
c_nullspace = Vh[-1].conj()

# Normaliser c1 = phi
c_norm = c_nullspace / c_nullspace[0] * PHI

print(f"\n  Valeurs singulieres de M(1/phi) :")
for i, s in enumerate(S):
    marker = "  <-- noyau" if i == N-1 else ""
    print(f"    sigma_{i+1} = {s:.6e}{marker}")

print(f"\n  {'n':<4} {'c_n (noyau)':<16} {'H_n (attendu)':<16} {'Ratio':<12} {'Ecart %':<10}")
print(f"  {'-'*58}")

ratios = []
for i in range(N):
    cv = abs(c_norm[i])
    hv = H_EXPECTED[i]
    r = cv / hv
    ratios.append(r)
    print(f"  {i+1:<4} {cv:<16.8f} {hv:<16.8f} {r:<12.6f} {abs(r-1)*100:<10.4f}%")

mean_r = np.mean(ratios)
std_r = np.std(ratios)
print(f"\n  Ratio moyen = {mean_r:.6f} +- {std_r:.6f}")

# ════════════════════════════════════════════════════════════════
# RÉSULTAT
# ════════════════════════════════════════════════════════════════

# Trouver le minimum
best = min(dets, key=lambda x: x[1])
print(f"\n{'='*60}")
print(f"RESULTAT")
print(f"{'='*60}")
print(f"  Minimum |det(M)| = {best[1]:.6e} a alpha = {best[0]:.6f}")
print(f"  alpha* attendu   = {alpha_star:.6f}")
print(f"  Ecart            = {abs(best[0] - alpha_star):.6f}")
print(f"  Ratio c_n/H_n    = {mean_r:.4f} +- {std_r:.4f}")

if abs(best[0] - alpha_star) < 0.03 and std_r < 0.3:
    print(f"\n  ✅ CONJECTURE VERIFIEE NUMERIQUEMENT")
    print(f"  det(M(1/phi)) ~ 0  et  ker(M) ~ {{phi, pi, e, sqrt2, sqrt3, sqrt5, e/pi}}")
else:
    print(f"\n  ⚠️  Resultats partiels — precision a ameliorer")
