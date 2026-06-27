import math
import sys
sys.stdout.reconfigure(encoding='utf-8')

# H_n constants
phi = (1 + math.sqrt(5)) / 2
pi = math.pi
e = math.e
sqrt2 = math.sqrt(2)
sqrt3 = math.sqrt(3)
sqrt5 = math.sqrt(5)
e_over_pi = e / pi

print('=' * 70)
print('H_n Values')
print('=' * 70)
for i, v in [(1, phi), (2, pi), (3, e), (4, sqrt2), (5, sqrt3), (6, sqrt5), (7, e_over_pi)]:
    print(f'  H_{i} = {v:.10f}')

# 1. EM FORCE - Fine structure constant α
print()
print('=' * 70)
print('1. FORCE ELECTROMAGNETIQUE — Constante de structure fine α')
print('=' * 70)
alpha_harm = pi**4 * e**(-4) * phi**(-5) * sqrt2**(-1) * sqrt3**(-5)
alpha_meas = 0.0072973525693
print(f'  Formule : π⁴ · e⁻⁴ · φ⁻⁵ · √2⁻¹ · √3⁻⁵')
print(f'  α_harm = {alpha_harm:.12f}')
print(f'  α_meas = {alpha_meas:.12f} (CODATA 2022)')
print(f'  Erreur  = {abs(alpha_harm/alpha_meas - 1)*100:.8f}%')
print(f'  1/α     = {1/alpha_harm:.6f} (mesuré: 137.036)')

# 2. WEAK FORCE - sin²θ_W
print()
print('=' * 70)
print('2. FORCE NUCLEAIRE FAIBLE — Angle de Weinberg sin²θ_W')
print('=' * 70)
sin2W_harm = phi**3 * pi**(-4) * e**1 * sqrt2**5 * sqrt3**(-2)
sin2W_meas = 0.23121
print(f'  Formule : φ³ · π⁻⁴ · e¹ · √2⁵ · √3⁻²')
print(f'  sin²θ_W_harm = {sin2W_harm:.8f}')
print(f'  sin²θ_W_meas = {sin2W_meas} (PDG 2023)')
print(f'  Erreur = {abs(sin2W_harm/sin2W_meas - 1)*100:.8f}%')

# α_W at M_Z
alpha_w_harm = alpha_harm / sin2W_harm
print(f'  α_W = α / sin²θ_W = {alpha_w_harm:.6f}')
print(f'  1/α_W = {1/alpha_w_harm:.2f}')

# 3. STRONG FORCE - α_s
print()
print('=' * 70)
print('3. FORCE NUCLEAIRE FORTE — Constante de couplage α_s(M_Z)')
print('=' * 70)
alpha_s_meas = 0.1180
# Try many combinations
combos_s = [
    (phi**1 * pi**(-1) * e**1 * sqrt2**(-2) * sqrt3**2 * sqrt5**(-1), 'φ¹·π⁻¹·e¹·√2⁻²·√3²·√5⁻¹'),
    (phi**2 * pi**(-1) * e**(-1) * sqrt2**2 * sqrt3**(-1) * sqrt5**1, 'φ²·π⁻¹·e⁻¹·√2²·√3⁻¹·√5¹'),
    (phi**2 * pi**(-2) * e**1 * sqrt2**1 * sqrt3**2 * sqrt5**(-1), 'φ²·π⁻²·e¹·√2¹·√3²·√5⁻¹'),
    (phi**3 * pi**(-2) * e**(-1) * sqrt2**1 * sqrt3**(-1) * sqrt5**1, 'φ³·π⁻²·e⁻¹·√2¹·√3⁻¹·√5¹'),
    (phi**(-1) * pi**1 * e**(-2) * sqrt2**2 * sqrt3**2 * sqrt5**(-1), 'φ⁻¹·π¹·e⁻²·√2²·√3²·√5⁻¹'),
    (phi**2 * pi**(-2) * e**1 * sqrt2**(-1) * sqrt3**1 * sqrt5**1, 'φ²·π⁻²·e¹·√2⁻¹·√3¹·√5¹'),
    (phi**(-2) * pi**1 * e**(-1) * sqrt2**1 * sqrt3**(-1) * sqrt5**2, 'φ⁻²·π¹·e⁻¹·√2¹·√3⁻¹·√5²'),
    (phi**1 * pi**(-1) * e**(-1) * sqrt2**1 * sqrt3**2 * sqrt5**(-1), 'φ¹·π⁻¹·e⁻¹·√2¹·√3²·√5⁻¹'),
    (phi**(-1) * pi**1 * e**(-1) * sqrt2**(-1) * sqrt3**1 * sqrt5**2, 'φ⁻¹·π¹·e⁻¹·√2⁻¹·√3¹·√5²'),
    (phi**1 * pi**2 * e**(-3) * sqrt2**2 * sqrt3**(-2) * sqrt5**1, 'φ¹·π²·e⁻³·√2²·√3⁻²·√5¹'),
]
best_s = None
best_err_s = float('inf')
for val, name in combos_s:
    err = abs(val/alpha_s_meas - 1)*100
    print(f'  {name} = {val:.6f}  (cible: {alpha_s_meas})  erreur: {err:.4f}%')
    if err < best_err_s:
        best_err_s = err
        best_s = (name, val)

print(f'\n  Meilleure : {best_s[0]} = {best_s[1]:.6f}  erreur: {best_err_s:.4f}%')

# 4. GRAVITATIONAL CONSTANT G
print()
print('=' * 70)
print('4. CONSTANTE GRAVITATIONNELLE G — Couplage gravitationnel α_G')
print('=' * 70)
G_meas = 6.67430e-11
# α_G = G·m_p²/(ℏc) dimensionless, where m_p = 0.938 GeV/c²
# M_Pl = sqrt(ℏc/G) ≈ 1.2209e19 GeV/c²
# ℏc ≈ 197.327 MeV·fm = 1.97327e-16 GeV·m
# Actually: ℏc = 0.1973269804 GeV·fm (yes, that's odd)
# Let's use: ℏ = 6.582119569e-25 GeV·s, c = 2.99792458e23 fm/s
# ℏc = 197.3269804 MeV·fm = 1.973269804e-16 GeV·m
# More standard: M_Pl = 1.220890e19 GeV, so G = ℏc / M_Pl²
hbar_c = 1.053571817e-34 * 2.99792458e8  # J·s × m/s
hbar_c_GeV_cm = 0.1973269804  # GeV·fm = 1e-15 GeV·m
# Actually let's use the known conversion:
# G = 6.70883e-39 GeV^{-2} in natural units (ℏ=c=1)
# α_G = G·m_p²/(ℏc) where m_p = 0.938272 GeV
# α_G = (6.70883e-39) * (0.938272)² = 5.904e-39
alpha_G_val = 5.904e-39
print(f'  G (SI)  = {G_meas:.5e} m³/(kg·s²)')
print(f'  α_G = G·m_p²/(ℏc) ≈ {alpha_G_val:.3e} (couplage gravitationnel dimensionless)')
print(f'  1/α_G ≈ {1/alpha_G_val:.3e}')

# Try to express α_G in H_n (EXTREMELY small, needs large negative exponents)
print(f'\n  Recherche expression harmonique pour α_G...')
combos_G = [
    (phi**(-80) * pi**(-40) * e**(-30), 'φ⁻⁸⁰·π⁻⁴⁰·e⁻³⁰'),
    (phi**(-78) * pi**(-39) * e**(-29), 'φ⁻⁷⁸·π⁻³⁹·e⁻²⁹'),
    (phi**(-76) * pi**(-38) * e**(-28) * sqrt2**(-10) * sqrt3**(-10), 'φ⁻⁷⁶·π⁻³⁸·e⁻²⁸·√2⁻¹⁰·√3⁻¹⁰'),
    (phi**(-77) * pi**(-38) * e**(-29) * sqrt2**(-5) * sqrt3**(-5), 'φ⁻⁷⁷·π⁻³⁸·e⁻²⁹·√2⁻⁵·√3⁻⁵'),
    (phi**(-75) * pi**(-37) * e**(-28) * sqrt2**(-8) * sqrt3**(-8) * sqrt5**(-5), 'φ⁻⁷⁵·π⁻³⁷·e⁻²⁸·√2⁻⁸·√3⁻⁸·√5⁻⁵'),
    (phi**(-79) * pi**(-39) * e**(-30) * sqrt2**(-3) * sqrt3**(-3), 'φ⁻⁷⁹·π⁻³⁹·e⁻³⁰·√2⁻³·√3⁻³'),
    (phi**(-77) * pi**(-38) * e**(-30) * sqrt2**(-6) * sqrt3**(-4) * sqrt5**(-3), 'φ⁻⁷⁷·π⁻³⁸·e⁻³⁰·√2⁻⁶·√3⁻⁴·√5⁻³'),
    (phi**(-74) * pi**(-36) * e**(-27) * sqrt2**(-12) * sqrt3**(-12), 'φ⁻⁷⁴·π⁻³⁶·e⁻²⁷·√2⁻¹²·√3⁻¹²'),
]
best_G = None
best_err_G = float('inf')
for val, name in combos_G:
    err = abs(val/alpha_G_val - 1)*100
    print(f'  {name} = {val:.4e}  (cible: {alpha_G_val:.3e})  erreur: {err:.4f}%')
    if err < best_err_G:
        best_err_G = err
        best_G = (name, val)

print(f'\n  Meilleure : α_G ≈ {best_G[0]} = {best_G[1]:.4e}  erreur: {best_err_G:.4f}%')
if best_G:
    print(f'  G ≈ (ℏc/m_p²) × ({best_G[0]}) ≈ {alpha_G_val:.3e}')

# 5. Force ratio: F_EM / F_Grav
print()
print('=' * 70)
print('5. RAPPORT Force_EM / Force_Gravité (proton-proton)')
print('=' * 70)
f_em_grav = alpha_harm / alpha_G_val
print(f'  F_EM / F_Grav = α / α_G = {f_em_grav:.4e}')
print(f'  (ordre de grandeur classique : ~10³⁶)')

# Express in H_n
combos_fg = [
    (phi**20 * pi**15 * e**10 * sqrt2**5 * sqrt3**5, 'φ²⁰·π¹⁵·e¹⁰·√2⁵·√3⁵'),
    (phi**25 * pi**18 * e**12 * sqrt2**8 * sqrt3**8, 'φ²⁵·π¹⁸·e¹²·√2⁸·√3⁸'),
    (phi**22 * pi**16 * e**11 * sqrt2**6 * sqrt3**6 * sqrt5**2, 'φ²²·π¹⁶·e¹¹·√2⁶·√3⁶·√5²'),
    (phi**24 * pi**17 * e**11 * sqrt2**7 * sqrt3**7, 'φ²⁴·π¹⁷·e¹¹·√2⁷·√3⁷'),
    (phi**18 * pi**14 * e**9 * sqrt2**8 * sqrt3**4, 'φ¹⁸·π¹⁴·e⁹·√2⁸·√3⁴'),
]
best_fg = None
best_err_fg = float('inf')
for val, name in combos_fg:
    ratio = val / f_em_grav
    print(f'  {name} = {val:.4e}  rapport à F_EM/F_Grav: {ratio:.4f}')
    err = abs(ratio - 1)*100
    if err < best_err_fg:
        best_err_fg = err
        best_fg = (name, val, ratio)

if best_fg:
    print(f'\n  Meilleure expression : F_EM/F_Grav ≈ {best_fg[0]}')

# 6. Force ratio: F_Forte / F_Faible
print()
print('=' * 70)
print('6. RAPPORT Force_Forte / Force_Faible')
print('=' * 70)
# At M_Z scale
alpha_s_best = best_s[1] if best_s else 0.118
ratio_s_w_mz = alpha_s_best / alpha_w_harm
print(f'  À l''échelle M_Z : α_s / α_W = {ratio_s_w_mz:.4f}')

# Find best match for α_s
if best_s:
    print(f'  Avec α_s_harm = {best_s[0]} = {best_s[1]:.6f}')
    print(f'  F_Forte / F_Faible = α_s_harm / α_W_harm = {alpha_s_best / alpha_w_harm:.4f}')

# Express F_Forte/F_Faible in H_n
ratio_sw = alpha_s_best / alpha_w_harm
combos_sw = [
    (phi**(-2) * pi**1 * e**3 * sqrt2**(-1) * sqrt3**4, 'φ⁻²·π¹·e³·√2⁻¹·√3⁴'),
    (phi**(-1) * pi**2 * e**2 * sqrt2**(-1) * sqrt3**3, 'φ⁻¹·π²·e²·√2⁻¹·√3³'),
    (phi**0 * pi**2 * e**2 * sqrt2**0 * sqrt3**3, 'φ⁰·π²·e²·√2⁰·√3³'),
    (phi**(-1) * pi**1 * e**3 * sqrt2**0 * sqrt3**3, 'φ⁻¹·π¹·e³·√2⁰·√3³'),
]
for val, name in combos_sw:
    print(f'  {name} = {val:.4f}')
    if val > 0:
        print(f'    ratio to α_s/α_W: {val/ratio_sw:.4f}')

# 7. LEPTONS
print()
print('=' * 70)
print('7. LEPTONS — Hiérarchie des masses e, μ, τ')
print('=' * 70)
m_e, m_mu, m_tau = 0.511, 105.66, 1776.86
print(f'  Masses mesurées (MeV) : e={m_e}, μ={m_mu}, τ={m_tau}')
mu_e_h = phi**(-3) * pi**3 * e**1 * sqrt2**2 * sqrt3**3
tau_mu_h = phi**1 * pi**3 * e**2 * sqrt2**(-1) * sqrt3**(-5)
tau_e_h = mu_e_h * tau_mu_h
print(f'  m_μ/m_e  = φ⁻³·π³·e¹·√2²·√3³  = {mu_e_h:.4f}  (mes: {m_mu/m_e:.4f})  err: {abs(mu_e_h/(m_mu/m_e)-1)*100:.6f}%')
print(f'  m_τ/m_μ  = φ¹·π³·e²·√2⁻¹·√3⁻⁵ = {tau_mu_h:.4f}  (mes: {m_tau/m_mu:.4f})  err: {abs(tau_mu_h/(m_tau/m_mu)-1)*100:.6f}%')
print(f'  m_τ/m_e  = φ²·π³·e⁵·√2⁻²·√3⁻¹ = {tau_e_h:.4f}  (mes: {m_tau/m_e:.4f})  err: {abs(tau_e_h/(m_tau/m_e)-1)*100:.6f}%')
# Back-calculate masses
m_mu_h = m_e * mu_e_h
m_tau_h = m_e * tau_e_h
print(f'  m_μ harmonic = {m_mu_h:.2f} MeV (mes: {m_mu})')
print(f'  m_τ harmonic = {m_tau_h:.2f} MeV (mes: {m_tau})')

# 8. QUARKS
print()
print('=' * 70)
print('8. QUARKS — Hiérarchie des masses u, d, s, c, b, t')
print('=' * 70)
m_u, m_d, m_s, m_c, m_b, m_t = 2.2, 4.7, 96, 1275, 4180, 173000
print(f'  Masses mesurées (MeV) : u={m_u}, d={m_d}, s={m_s}, c={m_c}, b={m_b}, t={m_t}')
c_u_h = phi**(-1) * pi**(-2) * e**5 * sqrt2**4 * sqrt3**5
t_c_h = phi**5 * pi**3 * e**3 * sqrt2**(-5) * sqrt3**(-4)
c_u_meas = m_c / m_u
t_c_meas = m_t / m_c
print(f'  m_c/m_u  = φ⁻¹·π⁻²·e⁵·√2⁴·√3⁵  = {c_u_h:.4f}  (mes: {c_u_meas:.4f})  err: {abs(c_u_h/c_u_meas-1)*100:.6f}%')
print(f'  m_t/m_c  = φ⁵·π³·e³·√2⁻⁵·√3⁻⁴  = {t_c_h:.4f}  (mes: {t_c_meas:.4f})  err: {abs(t_c_h/t_c_meas-1)*100:.6f}%')

# Search s/d and b/s
sd_meas = m_s / m_d  # ≈ 20.43
bs_meas = m_b / m_s  # ≈ 43.54
print(f'\n  m_s/m_d mesuré = {sd_meas:.2f}, m_b/m_s mesuré = {bs_meas:.2f}')
print(f'  Recherche expressions harmoniques...')

combos_sd = [
    (phi**3 * pi**2 * e**(-2) * sqrt2**1 * sqrt3**2, 'φ³·π²·e⁻²·√2¹·√3²'),
    (phi**2 * pi**2 * e**(-2) * sqrt2**2 * sqrt3**2, 'φ²·π²·e⁻²·√2²·√3²'),
    (phi**(-1) * pi**2 * e**(-1) * sqrt2**3 * sqrt3**1 * sqrt5**1, 'φ⁻¹·π²·e⁻¹·√2³·√3¹·√5¹'),
    (phi**1 * pi**2 * e**(-1) * sqrt2**1 * sqrt3**2 * sqrt5**(-1), 'φ¹·π²·e⁻¹·√2¹·√3²·√5⁻¹'),
    (phi**2 * pi**1 * e**(-1) * sqrt2**2 * sqrt3**2 * sqrt5**(-1), 'φ²·π¹·e⁻¹·√2²·√3²·√5⁻¹'),
    (phi**(-3) * pi**3 * e**(-1) * sqrt2**2 * sqrt3**2 * sqrt5**(-1), 'φ⁻³·π³·e⁻¹·√2²·√3²·√5⁻¹'),
    (phi**4 * pi**1 * e**(-2) * sqrt2**3 * sqrt3**3 * sqrt5**(-1), 'φ⁴·π¹·e⁻²·√2³·√3³·√5⁻¹'),
]
for val, name in combos_sd:
    err = abs(val/sd_meas - 1)*100
    print(f'    {name} = {val:.4f}  erreur: {err:.4f}%')

combos_bs = [
    (phi**3 * pi**2 * e**(-1) * sqrt2**1 * sqrt3**1 * sqrt5**1, 'φ³·π²·e⁻¹·√2¹·√3¹·√5¹'),
    (phi**2 * pi**2 * e**(-1) * sqrt2**2 * sqrt3**2 * sqrt5**1, 'φ²·π²·e⁻¹·√2²·√3²·√5¹'),
    (phi**4 * pi**2 * e**(-2) * sqrt2**2 * sqrt3**2, 'φ⁴·π²·e⁻²·√2²·√3²'),
    (phi**1 * pi**2 * e**(-1) * sqrt2**4 * sqrt3**1 * sqrt5**1, 'φ¹·π²·e⁻¹·√2⁴·√3¹·√5¹'),
    (phi**(-1) * pi**2 * e**1 * sqrt2**3 * sqrt3**0 * sqrt5**1, 'φ⁻¹·π²·e¹·√2³·√3⁰·√5¹'),
    (pi**2 * sqrt2**3 * sqrt3**1 * sqrt5**1, 'π²·√2³·√3¹·√5¹'),
]
for val, name in combos_bs:
    err = abs(val/bs_meas - 1)*100
    print(f'    {name} = {val:.4f}  erreur: {err:.4f}%')

# Summary table
print()
print('=' * 70)
print('RÉSUMÉ — EXPRESSIONS HARMONIQUES DES FORCES ET PARTICULES')
print('=' * 70)
print(f'''
FORCE ELECTROMAGNETIQUE :
  α = π⁴·e⁻⁴·φ⁻⁵·√2⁻¹·√3⁻⁵
    = {alpha_harm:.10f} (err: {abs(alpha_harm/alpha_meas - 1)*100:.6f}%)

FORCE NUCLEAIRE FAIBLE :
  sin²θ_W = φ³·π⁻⁴·e¹·√2⁵·√3⁻²
          = {sin2W_harm:.8f} (err: {abs(sin2W_harm/sin2W_meas - 1)*100:.6f}%)
  α_W = α/sin²θ_W = {alpha_w_harm:.6f}

FORCE NUCLEAIRE FORTE :
  α_s = {best_s[0]} = {best_s[1]:.6f} (err: {best_err_s:.4f}%)

CONSTANTE GRAVITATIONNELLE :
  α_G ≈ {best_G[0]} ≈ {best_G[1]:.4e} (err: {best_err_G:.4f}%)
  G = (ℏc/m_p²) × α_G ≈ {(hbar_c_GeV_cm / (0.938272**2)) * best_G[1]:.5e} {''if best_G else ''}GeV⁻²

RAPPORTS DE FORCES :
  F_EM / F_Gravité ≈ {f_em_grav:.3e}
  F_Forte / F_Faible ≈ {ratio_s_w_mz:.4f}

LEPTONS :
  m_μ/m_e = φ⁻³·π³·e¹·√2²·√3³ = {mu_e_h:.4f} (err: {abs(mu_e_h/(m_mu/m_e)-1)*100:.4f}%)
  m_τ/m_μ = φ¹·π³·e²·√2⁻¹·√3⁻⁵ = {tau_mu_h:.4f} (err: {abs(tau_mu_h/(m_tau/m_mu)-1)*100:.4f}%)

QUARKS :
  m_c/m_u = φ⁻¹·π⁻²·e⁵·√2⁴·√3⁵ = {c_u_h:.4f} (err: {abs(c_u_h/c_u_meas-1)*100:.4f}%)
  m_t/m_c = φ⁵·π³·e³·√2⁻⁵·√3⁻⁴ = {t_c_h:.4f} (err: {abs(t_c_h/t_c_meas-1)*100:.4f}%)
''')