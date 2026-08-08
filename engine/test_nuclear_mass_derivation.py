#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DERIVATION DES 118 MASSES NUCLEAIRES DEPUIS Psi = Somme Hn (Psi1)^n
Calcul exact avec ecart CODATA en %
"""

import math

# ============================================================
# CONSTANTES FONDAMENTALES (CODATA 2018)
# ============================================================
phi = (1 + math.sqrt(5)) / 2
pi = math.pi
e = math.e
s2 = math.sqrt(2)
s3 = math.sqrt(3)
s5 = math.sqrt(5)
e_div_pi = e / pi

# Physique
c = 299792458
G = 6.67430e-11
hbar = 1.054571817e-34
l_Planck = math.sqrt(G * hbar / c**3)
m_Planck = math.sqrt(hbar * c / G)
u_kg = 1.66053906660e-27  # 1 u en kg

# Facteur GAGUT/Oyibo : m_p/m_e = 6*pi^5
GAGUT_FACTOR = 6 * pi**5

# ============================================================
# 7 CONSTANTES HARMONIQUES H1..H7
# ============================================================
H = [0, phi, pi, e, s2, s3, s5, e_div_pi]

_H_cache = {}


def compute_H(n):
    """H_n par factorisation en premiers. Multiplicatif : H_{ab} = H_a*H_b.
    Pour premier p > 7 : H_p = phi^p (continuation analytique)."""
    if n <= 7:
        return H[n]
    if n in _H_cache:
        return _H_cache[n]
    result = 1.0
    remaining = n
    for p in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
              53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113]:
        if p * p > remaining:
            break
        while remaining % p == 0:
            if p <= 7:
                result *= H[p]
            else:
                result *= phi ** p
            remaining //= p
    if remaining > 1:
        if remaining <= 7:
            result *= H[remaining]
        else:
            result *= phi ** remaining
    _H_cache[n] = result
    return result


def divisors(n):
    divs = []
    for i in range(1, int(math.sqrt(n)) + 1):
        if n % i == 0:
            divs.append(i)
            if i != n // i:
                divs.append(n // i)
    return divs


NUCLEAR_DATA = {
    1: (1, 1.00782503223, "H"), 2: (4, 4.00260325413, "He"), 3: (7, 7.0160034366, "Li"),
    4: (9, 9.0121831, "Be"), 5: (11, 11.0093054, "B"), 6: (12, 12.0000000, "C"),
    7: (14, 14.0030740048, "N"), 8: (16, 15.99491461957, "O"), 9: (19, 18.998403163, "F"),
    10: (20, 19.9924401762, "Ne"), 11: (23, 22.9897692820, "Na"), 12: (24, 23.985041700, "Mg"),
    13: (27, 26.9815385, "Al"), 14: (28, 27.9769265, "Si"), 15: (31, 30.973761998, "P"),
    16: (32, 31.97207117, "S"), 17: (35, 34.96885268, "Cl"), 18: (40, 39.9623831225, "Ar"),
    19: (39, 38.96370668, "K"), 20: (40, 39.96259086, "Ca"), 21: (45, 44.955908, "Sc"),
    22: (48, 47.9479463, "Ti"), 23: (51, 50.9439595, "V"), 24: (52, 51.9405075, "Cr"),
    25: (55, 54.9380451, "Mn"), 26: (56, 55.9349375, "Fe"), 27: (59, 58.9331950, "Co"),
    28: (58, 57.9353429, "Ni"), 29: (63, 62.9295975, "Cu"), 30: (64, 63.9291422, "Zn"),
    31: (69, 68.9255736, "Ga"), 32: (74, 73.9211778, "Ge"), 33: (75, 74.9215965, "As"),
    34: (80, 79.9165213, "Se"), 35: (79, 78.9183371, "Br"), 36: (84, 83.911507, "Kr"),
    37: (85, 84.9117897, "Rb"), 38: (88, 87.9056122, "Sr"), 39: (89, 88.9058483, "Y"),
    40: (90, 89.9047044, "Zr"), 41: (93, 92.9063781, "Nb"), 42: (98, 97.9054082, "Mo"),
    43: (98, 97.9072, "Tc"), 44: (102, 101.9043493, "Ru"), 45: (103, 102.905504, "Rh"),
    46: (106, 105.903483, "Pd"), 47: (107, 106.905097, "Ag"), 48: (114, 113.9033585, "Cd"),
    49: (115, 114.903878, "In"), 50: (118, 117.901609, "Sn"), 51: (121, 120.9038157, "Sb"),
    52: (128, 127.904461, "Te"), 53: (127, 126.904473, "I"), 54: (132, 131.904154, "Xe"),
    55: (133, 132.90545196, "Cs"), 56: (138, 137.905247, "Ba"), 57: (139, 138.906353, "La"),
    58: (140, 139.905439, "Ce"), 59: (141, 140.907653, "Pr"), 60: (142, 141.907723, "Nd"),
    61: (145, 144.9127, "Pm"), 62: (152, 151.919732, "Sm"), 63: (153, 152.921230, "Eu"),
    64: (158, 157.924103, "Gd"), 65: (159, 158.925346, "Tb"), 66: (164, 163.929174, "Dy"),
    67: (165, 164.930322, "Ho"), 68: (166, 165.930293, "Er"), 69: (169, 168.934213, "Tm"),
    70: (174, 173.938862, "Yb"), 71: (175, 174.940772, "Lu"), 72: (180, 179.946549, "Hf"),
    73: (181, 180.947995, "Ta"), 74: (182, 181.948206, "W"), 75: (185, 184.952956, "Re"),
    76: (192, 191.961479, "Os"), 77: (193, 192.962924, "Ir"), 78: (195, 194.964774, "Pt"),
    79: (197, 196.966568, "Au"), 80: (202, 201.970626, "Hg"), 81: (205, 204.974427, "Tl"),
    82: (208, 207.976652, "Pb"), 83: (209, 208.980399, "Bi"), 84: (209, 209.0, "Po"),
    85: (210, 210.0, "At"), 86: (222, 222.0, "Rn"), 87: (223, 223.0, "Fr"),
    88: (226, 226.0, "Ra"), 89: (227, 227.0, "Ac"), 90: (232, 232.038055, "Th"),
    91: (231, 231.035884, "Pa"), 92: (238, 238.050788, "U"), 93: (237, 237.0, "Np"),
    94: (244, 244.0, "Pu"), 95: (243, 243.0, "Am"), 96: (247, 247.0, "Cm"),
    97: (247, 247.0, "Bk"), 98: (251, 251.0, "Cf"), 99: (252, 252.0, "Es"),
    100: (257, 257.0, "Fm"), 101: (258, 258.0, "Md"), 102: (259, 259.0, "No"),
    103: (266, 266.0, "Lr"), 104: (267, 267.0, "Rf"), 105: (270, 270.0, "Db"),
    106: (271, 271.0, "Sg"), 107: (270, 270.0, "Bh"), 108: (277, 277.0, "Hs"),
    109: (278, 278.0, "Mt"), 110: (281, 281.0, "Ds"), 111: (282, 282.0, "Rg"),
    112: (285, 285.0, "Cn"), 113: (286, 286.0, "Nh"), 114: (289, 289.0, "Fl"),
    115: (290, 290.0, "Mc"), 116: (293, 293.0, "Lv"), 117: (294, 294.0, "Ts"),
    118: (294, 294.0, "Og"),
}


def shell_correction(A, Z, N):
    magic = {2, 8, 20, 28, 50, 82, 126}
    delta = 0.0
    for n in [Z, N, A]:
        if n in magic:
            delta += 0.02
    return 1.0 + delta


def harmonic_radius_correction(A, Z, N):
    """Xi(A,Z) = (1/phi) * produit_{d|A} H_d^(1/d) * shell_correction"""
    prod = 1.0
    for d in divisors(A):
        prod *= compute_H(d) ** (1.0 / d)
    prod /= phi
    prod *= shell_correction(A, Z, N)
    return prod


def r0_harmonic():
    return l_Planck * phi**6 / (GAGUT_FACTOR ** (1 / 3))


def nuclear_radius(A, Z, N):
    return r0_harmonic() * (A ** (1 / 3)) * harmonic_radius_correction(A, Z, N)


def holographic_factor(R):
    return (l_Planck / R) ** 2


def phase(n):
    return (2 * pi * n * phi) % (2 * pi)


def phi_factor(A, Z, N):
    import cmath
    active = set(divisors(A) + divisors(Z) + divisors(N))
    psi_sum = 0.0 + 0.0j
    for n in active:
        psi_sum += compute_H(n) * cmath.exp(1j * phase(n))
    return abs(psi_sum) ** 2


def predict_mass(A, Z, N):
    R = nuclear_radius(A, Z, N)
    m_kg = m_Planck * holographic_factor(R) * GAGUT_FACTOR * phi_factor(A, Z, N)
    return m_kg / u_kg


def main():
    print("=" * 90)
    print("DERIVATION DES 118 MASSES DEPUIS Psi = Somme Hn (Psi1)^n")
    print("Equation close : m = m_Planck (l_Planck/R)^2 6pi^5 |Somme H_n e^{i theta_n}|^2")
    print("=" * 90)
    errors = []
    for Z in range(1, 119):
        A, m_CODATA_u, sym = NUCLEAR_DATA[Z]
        N = A - Z
        m_pred_u = predict_mass(A, Z, N)
        err_pct = abs(m_pred_u - m_CODATA_u) / m_CODATA_u * 100
        errors.append(err_pct)
        print(f"Z={Z:>3} {sym:>3} A={A:>4} m_CODATA={m_CODATA_u:>10.6f} "
              f"m_HARM={m_pred_u:>10.6f} ecart={err_pct:>8.4f}%")
    print("-" * 90)
    print(f"Ecart moyen  : {sum(errors)/len(errors):.4f} %")
    print(f"Ecart median : {sorted(errors)[len(errors)//2]:.4f} %")
    print(f"Ecart max    : {max(errors):.4f} %")
    print(f"Ecart min    : {min(errors):.4f} %")
    print(f"< 0.1 % : {sum(1 for e in errors if e < 0.1)}/118")
    print(f"< 1 %   : {sum(1 for e in errors if e < 1.0)}/118")
    print(f"< 5 %   : {sum(1 for e in errors if e < 5.0)}/118")

    print("\n--- Nombres magiques (Phi) ---")
    magic = [2, 8, 20, 28, 50, 82, 126]
    for Z in range(1, 119):
        A, _, _ = NUCLEAR_DATA[Z]
        N = A - Z
        P = phi_factor(A, Z, N)
        if Z in magic or N in magic or A in magic:
            print(f"  Z={Z:3d} N={N:3d} A={A:3d} Phi={P:.4f}")


if __name__ == "__main__":
    main()
