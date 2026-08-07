"""
🌊 MODÈLE NON-LINÉAIRE COMPLET — Vérification GAGUT + ABC
===========================================================
Équation : ABC D_t^{2α} Ψ − ∇²Ψ + m²Ψ + g|Ψ|²Ψ = 0
avec Ψ = Σ cₙ (Ψ₁)ⁿ

Vérifie s'il existe g tel que cₙ = Hₙ = {φ, π, e, √2, √3, √5, e/π}
satisfait le système projeté.
"""

import numpy as np
from scipy.special import gamma, spherical_jn
from scipy.integrate import simpson
from scipy.linalg import svd
import math, time
from itertools import product

# ════════════════════════════════════════════════════════════
# CONSTANTES
# ════════════════════════════════════════════════════════════
PHI = (1 + np.sqrt(5)) / 2
PI  = np.pi
E   = np.e
SQ2 = np.sqrt(2)
SQ3 = np.sqrt(3)
SQ5 = np.sqrt(5)
E_OVER_PI = E / PI

H_EXPECTED = np.array([PHI, PI, E, SQ2, SQ3, SQ5, E_OVER_PI])
H_NAMES    = ['φ', 'π', 'e', '√2', '√3', '√5', 'e/π']
N = 7

ALPHA = 1.0 / PHI

# ════════════════════════════════════════════════════════════
# PARAMÈTRES PHYSIQUES
# ════════════════════════════════════════════════════════════
R = 1.0
KAPPA1 = PI / R
M_EFF = 0.5
OMEGA1 = np.sqrt(KAPPA1**2 - M_EFF**2)
T_PERIOD = 2 * PI / OMEGA1
N_PERIODS = 4
T_MAX = N_PERIODS * T_PERIOD

NT = 100
NR = 100
t_grid = np.linspace(0, T_MAX, NT)
r_grid = np.linspace(0, R, NR)
dt = t_grid[1] - t_grid[0]
dr = r_grid[1] - r_grid[0]

A1 = np.sqrt(2.0 / (R**3 * T_MAX))

print("=" * 65)
print("🌊 MODELE NON-LINEAIRE — ABC + GAGUT (|Ψ|²Ψ)")
print("=" * 65)
print(f"α = 1/φ = {ALPHA:.6f}  |  ω₁ = {OMEGA1:.3f}  |  grille {NT}×{NR}")
print(f"H attendus = [{', '.join(f'{h:.4f}' for h in H_EXPECTED)}]")

# ════════════════════════════════════════════════════════════
# PRÉ-CALCULS SPATIAUX
# ════════════════════════════════════════════════════════════

j0_vals = spherical_jn(0, KAPPA1 * r_grid)
MAX_POWER = N * 3  # a+b+d+m max ≈ 28 → on prend 21 pour la sécurité

# S_p = ∫₀^R j₀^p(κ₁r) · r² dr  pour p = 1..MAX_POWER
S_spatial = np.zeros(MAX_POWER + 1)
for p in range(1, MAX_POWER + 1):
    integrand = j0_vals**p * r_grid**2
    S_spatial[p] = simpson(integrand, r_grid)

# Laplacien : LAP_{m,d} = ∫ j₀ᵐ · ∇²[j₀ᵈ] · r² dr
# Pré-calculer ∇²[j₀ᵈ] pour d = 1..N
laplacian_pow = np.zeros((N, NR))
for d in range(N):
    f = j0_vals**(d+1)
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
    laplacian_pow[d] = lap

LAP_spatial = np.zeros((N, N))
for m in range(N):
    for d in range(N):
        integrand = j0_vals**(m+1) * laplacian_pow[d] * r_grid**2
        LAP_spatial[m, d] = simpson(integrand, r_grid)

print(f"Matrices spatiales : S_p (p=1..{MAX_POWER}), LAP (7×7) ✓")

# ════════════════════════════════════════════════════════════
# OPÉRATEUR ABC (version optimisée)
# ════════════════════════════════════════════════════════════

def mittag_leffler(alpha, z, n_terms=30):
    r = np.zeros_like(z, dtype=float)
    for k in range(n_terms):
        r += z**k / gamma(alpha * k + 1)
    return r

def B_alpha(alpha):
    return 1.0 - alpha + alpha / gamma(alpha)

def abc_derivative_vec(alpha, f_t):
    """ABC D_t^α [f(t)] — vectorisé où possible."""
    B = B_alpha(alpha)
    gv = alpha / (1.0 - alpha)
    
    df = np.zeros(NT, dtype=complex)
    df[1:-1] = (f_t[2:] - f_t[:-2]) / (2*dt)
    df[0] = (f_t[1] - f_t[0]) / dt
    df[-1] = (f_t[-1] - f_t[-2]) / dt
    
    result = np.zeros(NT, dtype=complex)
    for i in range(1, NT):
        tau = t_grid[:i+1]
        dtau = t_grid[i] - tau
        E_vals = mittag_leffler(alpha, -gv * dtau**alpha)
        integrand = df[:i+1] * E_vals
        result[i] = B / (1.0 - alpha) * np.trapezoid(integrand, tau)
    return result

# Pré-calcul ABC pour les 7 modes
print("Calcul ABC D^{2α} pour les 7 modes...", end=" ", flush=True)
t0 = time.time()

abc2_modes = []
for n in range(1, N+1):
    f_in = np.exp(-1j * n * OMEGA1 * t_grid)
    abc1 = abc_derivative_vec(ALPHA, f_in)
    abc2 = abc_derivative_vec(ALPHA, abc1)
    abc2_modes.append(abc2)

# Matrice temporelle ABC : T_{m,d} = ∫ e^{+imω₁t} · ABC^{2α}[e^{-idω₁t}] dt
T_abc = np.zeros((N, N), dtype=complex)
for m in range(N):
    exp_plus = np.exp(1j * (m+1) * OMEGA1 * t_grid)
    for d in range(N):
        integrand = exp_plus * abc2_modes[d]
        T_abc[m, d] = (np.trapezoid(integrand.real, t_grid) + 
                       1j * np.trapezoid(integrand.imag, t_grid))

print(f"✓ ({time.time()-t0:.1f}s)")

# ════════════════════════════════════════════════════════════
# MATRICE LINÉAIRE L(α)
# ════════════════════════════════════════════════════════════

# L_{m,d} = ⟨(Ψ₁)ᵐ | ABC D^{2α} − ∇² + m² | (Ψ₁)ᵈ⟩
# = A₁^{m+d} [S_{m+d} · T_{m,d}(α) − LAP_{m,d} · T·δ_{m,d} + m²·S_{m+d} · T·δ_{m,d}]

L_matrix = np.zeros((N, N), dtype=complex)
for m in range(N):
    for d in range(N):
        A_fact = A1**(m + d + 2)
        S_ov = S_spatial[m + d + 2]  # +2 car m,d 0-indexed, et on veut les puissances réelles
        O_t = T_MAX if m == d else 0.0
        
        term_abc = S_ov * T_abc[m, d]
        term_lap = LAP_spatial[m, d] * O_t
        term_mass = M_EFF**2 * S_ov * O_t
        
        L_matrix[m, d] = A_fact * (term_abc - term_lap + term_mass)

print(f"\nMatrice linéaire L (conditionnement = {np.linalg.cond(L_matrix):.1e})")

# ════════════════════════════════════════════════════════════
# TENSEUR NON-LINÉAIRE N
# ════════════════════════════════════════════════════════════

# L'équation pour le mode m :
# Σ_d c_d L_{m,d} + g · Σ_{a,b,d} c_a c_b* c_d · N_{m, a, b, d} = 0
#
# où N_{m,a,b,d} = A₁^{a+b+d+m+2} · S_{a+b+d+m+2} · T  (si a-b+d = m, sinon 0)
# (car la sélection temporelle impose a-b+d = m pour la survie de l'intégrale)

print("Construction du tenseur non-linéaire N...", end=" ", flush=True)
t0 = time.time()

# Dictionnaire pour un accès rapide : N_tensor[(m,a,b,d)] = valeur
N_tensor = {}
non_zero_count = 0

for m, a, b, d in product(range(N), repeat=4):
    if a - b + d == m:  # sélection temporelle
        power = (a+1) + (b+1) + (d+1) + (m+1)  # puissances réelles = indices+1
        if power <= MAX_POWER:
            A_fact = A1**power
            N_val = A_fact * S_spatial[power] * T_MAX
            N_tensor[(m, a, b, d)] = N_val
            non_zero_count += 1

print(f"✓ ({time.time()-t0:.1f}s) — {non_zero_count} éléments non-nuls")

# ════════════════════════════════════════════════════════════
# VÉRIFICATION : Hₙ est-il solution ?
# ════════════════════════════════════════════════════════════

print(f"\n{'='*65}")
print(f"VÉRIFICATION : Hₙ satisfait-il le système ?")
print(f"{'='*65}")

c = H_EXPECTED.astype(complex)

# Partie linéaire : F_m = Σ_d c_d · L_{m,d}
F_linear = L_matrix @ c

# Partie non-linéaire : G_m = Σ_{a,b,d} c_a c_b* c_d · N_{m,a,b,d}
F_nonlinear = np.zeros(N, dtype=complex)
for (m, a, b, d), N_val in N_tensor.items():
    F_nonlinear[m] += c[a] * np.conj(c[b]) * c[d] * N_val

# Ratio : pour quel g a-t-on F_linear + g · F_nonlinear = 0 ?
# g_m = -F_linear[m] / F_nonlinear[m] pour chaque mode m
g_per_mode = np.zeros(N, dtype=complex)
for m in range(N):
    if abs(F_nonlinear[m]) > 1e-30:
        g_per_mode[m] = -F_linear[m] / F_nonlinear[m]

print(f"\n  {'Mode':<6} {'F_linear':<18} {'F_nonlinear':<18} {'g = -F_lin/F_nl':<20} {'|g|':<12}")
print(f"  {'-'*70}")
for m in range(N):
    fl = F_linear[m]
    fn = F_nonlinear[m]
    gm = g_per_mode[m]
    print(f"  {m+1:<6} {fl.real:+.4e}{fl.imag:+.4e}i  {fn.real:+.4e}{fn.imag:+.4e}i  {gm.real:+.4e}{gm.imag:+.4e}i  {abs(gm):.4e}")

# Le couplage g doit être le MÊME pour tous les modes
# → vérifier la cohérence des g_m
g_values = g_per_mode[~np.isnan(g_per_mode) & (np.abs(g_per_mode) < 1e30)]
if len(g_values) > 0:
    g_mean = np.mean(g_values)
    g_std = np.std(g_values)
    g_cv = g_std / (abs(g_mean) + 1e-30)
    
    print(f"\n  g_moyen = {g_mean.real:.6e} + {g_mean.imag:.6e}i")
    print(f"  g_std   = {g_std:.4e}")
    print(f"  CV      = {g_cv:.4f} (coefficient de variation)")
    
    # Résidu avec g = g_mean
    residual = F_linear + g_mean * F_nonlinear
    res_norm = np.linalg.norm(residual)
    rel_res = res_norm / (np.linalg.norm(F_linear) + 1e-30)
    
    print(f"\n  ||F_linear + g·F_nonlinear|| = {res_norm:.4e}")
    print(f"  Résidu relatif              = {rel_res:.4e}")
    
    # ════════════════════════════════════════════════════════
    # SCORE
    # ════════════════════════════════════════════════════════
    print(f"\n{'='*65}")
    print(f"RÉSULTAT")
    print(f"{'='*65}")
    
    if g_cv < 0.5 and rel_res < 0.1:
        print(f"\n  ✅✅ CONJECTURE VÉRIFIÉE !")
        print(f"  Hₙ = {{φ,π,e,√2,√3,√5,e/π}} EST solution de :")
        print(f"  ABC D^{{2α}}Ψ − ∇²Ψ + m²Ψ + g|Ψ|²Ψ = 0")
        print(f"  avec g ≈ {g_mean.real:.4f}")
        print(f"  CV = {g_cv:.4f} (cohérence des modes)")
        print(f"  Résidu = {rel_res:.2e}")
    elif g_cv < 1.0 and rel_res < 0.3:
        print(f"\n  ✅ CONJECTURE PLAUSIBLE")
        print(f"  Hₙ est approximativement solution (CV={g_cv:.2f}, résidu={rel_res:.2e})")
        print(f"  La précision peut être améliorée avec plus de périodes/points")
    else:
        print(f"\n  ⚠️  CONJECTURE NON VÉRIFIÉE dans ce modèle")
        print(f"  CV = {g_cv:.2f} (trop élevé — les g_m ne sont pas cohérents)")
        print(f"  Résidu = {rel_res:.2e}")
        print(f"  → Le modèle |Ψ|²Ψ seul est insuffisant")
        print(f"  → Besoin d'un potentiel V(|Ψ|²) plus riche")
else:
    print(f"\n  ⚠️  Impossible de calculer g — F_nonlinear est nul ou NaN")
