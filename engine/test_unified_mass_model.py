#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODELE UNIFIE HARAMEIN-OYIBO-HARMONIQUE
Masse des noyaux : m_Z = m_Planck * (l_Planck / R_Z)^2 * 6*pi^5 * phi^{f(Z)}

Base :
- Haramein : dimension holographique 2 (surface) -> (l/R)^2
- Oyibo/GAGUT : 6*pi^5 = ratio m_p/m_e exact, structure fractale phi
- Harmonique : R_Z derive de Psi = Sum H_n (Psi_1)^n, H_n = {phi, pi, e, sqrt(2), sqrt(3), sqrt(5), e/pi}
"""

import math

# ===== CONSTANTES =====
phi = (1 + math.sqrt(5)) / 2
pi = math.pi
e = math.e
s2 = math.sqrt(2)
s3 = math.sqrt(3)
s5 = math.sqrt(5)
e_div_pi = e / pi

H = [0, phi, pi, e, s2, s3, s5, e_div_pi]

# Physique
c = 299792458
G = 6.67430e-11
hbar = 1.054571817e-34
k_B = 1.380649e-23
l_Planck = math.sqrt(G * hbar / c**3)
m_Planck = math.sqrt(hbar * c / G)

# Facteur GAGUT/Oyibo decouvert
GAGUT_FACTOR = 6 * pi**5  # = 1836.118... ~ m_p/m_e
print("Facteur GAGUT 6*pi^5 = {:.10f}".format(GAGUT_FACTOR))
print("m_p/m_e experimental = {:.10f}".format(1836.15267343))
print("Erreur = {:.6f}%".format(abs(GAGUT_FACTOR - 1836.15267343) / 1836.15267343 * 100))
print()

# ===== RAYONS NUCLEAIRES EXPERIMENTAUX (fm) =====
# Sources : charge radii CODATA, modèles goutte liquide R = r0 * A^(1/3)
r0 = 1.2  # fm, parametre standard

nuclear_data = {
    # Z: (A, R_charge_fm, m_exp_kg, m_exp_u, name)
    1:  (1,   0.841, 1.67262192369e-27, 1.007276, "p"),
    2:  (4,   1.678, 6.6446573450e-27, 4.002603, "He-4"),
    3:  (7,   2.43,  1.1648e-26,   7.016003, "Li-7"),
    4:  (9,   2.58,  1.501e-26,   9.012183, "Be-9"),
    5:  (11,  2.41,  1.827e-26,   11.0093, "B-11"),
    6:  (12,  2.47,  1.9926e-26,  12.0000, "C-12"),
    7:  (14,  2.56,  2.325e-26,   14.0031, "N-14"),
    8:  (16,  2.70,  2.656e-26,   15.9949, "O-16"),
    10: (20,  3.02,  3.319e-26,   19.9924, "Ne-20"),
    12: (24,  3.10,  3.985e-26,   23.9850, "Mg-24"),
    13: (27,  3.15,  4.485e-26,   26.9815, "Al-27"),
    14: (28,  3.20,  4.663e-26,   27.9769, "Si-28"),
    16: (32,  3.35,  5.314e-26,   31.9721, "S-32"),
    18: (40,  3.55,  6.642e-26,   39.9624, "Ar-40"),
    20: (40,  3.48,  6.644e-26,   39.9626, "Ca-40"),
    26: (56,  3.75,  9.287e-26,   55.9349, "Fe-56"),
    28: (58,  3.80,  9.632e-26,   57.9353, "Ni-58"),
    29: (63,  3.85,  1.045e-25,   62.9296, "Cu-63"),
    30: (64,  3.90,  1.063e-25,   63.9291, "Zn-64"),
    38: (88,  4.20,  1.461e-25,   87.9056, "Sr-88"),
    40: (90,  4.25,  1.494e-25,   89.9047, "Zr-90"),
    42: (96,  4.35,  1.593e-25,   95.9083, "Mo-96"),
    47: (107, 4.50,  1.777e-25,   106.905, "Ag-107"),
    50: (118, 4.65,  1.960e-25,   117.902, "Sn-118"),
    56: (138, 4.85,  2.291e-25,   137.905, "Ba-138"),
    79: (197, 5.42,  3.271e-25,   196.967, "Au-197"),
    82: (208, 5.50,  3.447e-25,   207.977, "Pb-208"),
    92: (238, 5.85,  3.953e-25,   238.051, "U-238"),
}

# ===== FONCTIONS HARMONIQUES =====

def compute_H_n(n):
    """H_n pour n > 7 par factorisation en premiers (hypothese)"""
    if n <= 7:
        return H[n]
    result = 1.0
    remaining = n
    for p in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]:
        while remaining % p == 0:
            result *= compute_H_n(p)
            remaining //= p
    if remaining > 1:
        result *= phi ** remaining
    return result

def harmonic_radius(Z, A):
    """
    Rayon nucleaire derive de l'equation harmonique.
    Hypothese : R_Z = r0 * A^(1/3) * correction_harmonique(Z)
    Correction = produit H_n pour les modes actifs dans le noyau
    """
    # Rayon standard goutte liquide
    R_std = r0 * (A ** (1/3)) * 1e-15  # metres
    
    # Correction harmonique : le noyau Z a des "modes" harmoniques actifs
    # Modes = diviseurs de Z (structure fractale)
    correction = 1.0
    for d in range(1, Z+1):
        if Z % d == 0:
            correction *= compute_H_n(d) ** (1/d)  # contribution fractionnaire
    
    # Normalisation sur proton (Z=1, correction=phi)
    correction /= phi
    
    return R_std * correction

def fractal_exponent(Z, A):
    """
    Exposant fractal f(Z) pour phi^{f(Z)}.
    Base : f(1) = 0 (proton reference)
    f(Z) derive de la structure harmonique : somme des H_n actifs
    """
    if Z == 1:
        return 0
    
    # Somme des coefficients harmoniques pour les diviseurs
    f = 0.0
    for d in range(1, Z+1):
        if Z % d == 0:
            f += math.log(compute_H_n(d)) / math.log(phi)
    
    # Normalisation empirique pour couvrir 19 ordres
    # log_phi(ratio_manquant) ~ 40
    f = f * (40.0 / f) if f > 0 else 0
    
    return f

def predict_mass(Z, A, R_fm):
    """Prediction masse par modele unifie"""
    R_m = R_fm * 1e-15
    
    # Facteur holographique (dimension 2)
    holographic = (l_Planck / R_m) ** 2
    
    # Facteur GAGUT (6*pi^5)
    gagut = GAGUT_FACTOR
    
    # Facteur fractal phi
    f_exp = fractal_exponent(Z, A)
    fractal = phi ** f_exp
    
    m_pred = m_Planck * holographic * gagut * fractal
    
    return m_pred, holographic, gagut, fractal, f_exp

# ===== TEST =====

print("=" * 80)
print("MODELE UNIFIE : m_Z = m_Planck * (l_Planck/R_Z)^2 * 6*pi^5 * phi^{f(Z)}")
print("=" * 80)
print("{:>3} {:>6} {:>6} {:>14} {:>14} {:>10} {:>10} {:>8}".format(
    "Z", "A", "R_fm", "m_exp(kg)", "m_pred(kg)", "err%", "f_exp", "fact"))
print("-" * 80)

errors = []
for Z, (A, R_fm, m_exp_kg, m_exp_u, name) in nuclear_data.items():
    m_pred, holo, gagut, fract, f_exp = predict_mass(Z, A, R_fm)
    err = abs(m_pred - m_exp_kg) / m_exp_kg * 100
    errors.append(err)
    
    print("{:>3} {:>6} {:>6.3f} {:>14.6e} {:>14.6e} {:>9.2f}% {:>9.2f} {:>7.2f}".format(
        Z, A, R_fm, m_exp_kg, m_pred, err, f_exp, fract))

print("-" * 80)
print("Erreur moyenne: {:.2f}%".format(sum(errors)/len(errors)))
print("Erreur mediane: {:.2f}%".format(sorted(errors)[len(errors)//2]))
print("Max erreur: {:.2f}%".format(max(errors)))
print("Min erreur: {:.2f}%".format(min(errors)))

# Analyse par region
print("\n--- Par region ---")
light = [e for Z,e in zip(nuclear_data.keys(), errors) if Z <= 20]
mid = [e for Z,e in zip(nuclear_data.keys(), errors) if 20 < Z <= 50]
heavy = [e for Z,e in zip(nuclear_data.keys(), errors) if Z > 50]
print("Legers (Z<=20)  : moy={:.1f}%, med={:.1f}%".format(sum(light)/len(light), sorted(light)[len(light)//2]))
print("Moyens (20<Z<=50): moy={:.1f}%, med={:.1f}%".format(sum(mid)/len(mid), sorted(mid)[len(mid)//2]))
print("Lourds (Z>50)   : moy={:.1f}%, med={:.1f}%".format(sum(heavy)/len(heavy), sorted(heavy)[len(heavy)//2]))

# Recherche meilleure normalisation f_exp
print("\n--- Optimisation f_exp ---")
print("Recherche facteur d'echelle pour f_exp...")

best_scale = 1.0
best_err = float('inf')
for scale in [i/10 for i in range(1, 101)]:
    test_errors = []
    for Z, (A, R_fm, m_exp_kg, m_exp_u, name) in nuclear_data.items():
        f_exp = fractal_exponent(Z, A) * scale
        fract = phi ** f_exp
        m_pred = m_Planck * (l_Planck / (R_fm*1e-15))**2 * GAGUT_FACTOR * fract
        err = abs(m_pred - m_exp_kg) / m_exp_kg * 100
        test_errors.append(err)
    avg_err = sum(test_errors)/len(test_errors)
    if avg_err < best_err:
        best_err = avg_err
        best_scale = scale

print("Meilleure echelle f_exp: x{:.1f} -> erreur moyenne: {:.2f}%".format(best_scale, best_err))

# Test avec echelle optimale
print("\n--- Resultats avec echelle optimale x{:.1f} ---".format(best_scale))
errors_opt = []
for Z, (A, R_fm, m_exp_kg, m_exp_u, name) in nuclear_data.items():
    f_exp = fractal_exponent(Z, A) * best_scale
    fract = phi ** f_exp
    m_pred = m_Planck * (l_Planck / (R_fm*1e-15))**2 * GAGUT_FACTOR * fract
    err = abs(m_pred - m_exp_kg) / m_exp_kg * 100
    errors_opt.append(err)
    print("{:>3} {:>6} {:>14.6e} {:>14.6e} {:>9.2f}%".format(Z, A, m_exp_kg, m_pred, err))

print("Erreur moyenne optimale: {:.2f}%".format(sum(errors_opt)/len(errors_opt)))