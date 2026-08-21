#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de l'hypothese : m_Z = m_Planck / H_Z^2
avec H_Z derive depuis l'equation maitresse harmonique Psi = Sum H_n (Psi_1)^n
"""

import math

# ===== CONSTANTES FONDAMENTALES =====
phi = (1 + math.sqrt(5)) / 2
pi = math.pi
e = math.e
s2 = math.sqrt(2)
s3 = math.sqrt(3)
s5 = math.sqrt(5)
e_div_pi = e / pi

# Masse de Planck
m_Planck = 2.176434e-8  # kg

# Masse proton CODATA 2018
m_p_exp_kg = 1.67262192369e-27
m_p_exp_u = 1.007276466812

# ===== MASSES EXPERIMENTALES (kg) =====
known_masses_kg = {
    1: 1.67262192369e-27,      # proton (H-1)
    2: 3.3435837724e-27,       # deuteron (H-2)
    3: 5.007356755e-27,        # triton (H-3)
    4: 6.6446573450e-27,       # alpha (He-4)
    6: 1.9926468828e-26,       # C-12 (exact: 12 u par definition)
    8: 2.656014e-26,           # O-16
    26: 9.271487e-26,          # Fe-56 (plus lie)
    79: 3.270710e-25,          # Au-197
    92: 3.952961e-25,          # U-238
}

# ===== H_Z ACTUELS (H_1 a H_7 poses, H_8+ a deriver) =====
H_known = {
    1: phi,
    2: pi,
    3: e,
    4: s2,
    5: s3,
    6: s5,
    7: e_div_pi,
}

# Derivation naive H_n pour n>7 par factorisation
def compute_H_naive(n):
    if n in H_known:
        return H_known[n]
    result = 1.0
    remaining = n
    for p in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]:
        while remaining % p == 0:
            result *= H_known.get(p, compute_H_naive(p))
            remaining //= p
    if remaining > 1:
        result *= phi ** remaining
    return result


def test_hypothesis_mass_equals_planck_over_H2():
    print("=" * 70)
    print("TEST HYPOTHESE : m_Z = m_Planck / H_Z^2")
    print("=" * 70)
    print("m_Planck = {:.6e} kg".format(m_Planck))
    print("H_1 = phi = {:.6f}".format(phi))
    m_p_pred = m_Planck / phi**2
    print("m_p predit (Z=1) = {:.6e} kg".format(m_p_pred))
    print("m_p exp (Z=1)    = {:.6e} kg".format(m_p_exp_kg))
    err_p = abs(m_p_pred - m_p_exp_kg) / m_p_exp_kg * 100
    print("Erreur proton    = {:.3f}%".format(err_p))
    print()

    test_nuclei = [1, 2, 4, 6, 8, 26, 79, 92]
    print("{:>3} | {:>6} | {:>10} | {:>14} | {:>14} | {:>8}".format(
        "Z", "Noyau", "H_Z", "m_pred (kg)", "m_exp (kg)", "Erreur %"))
    print("-" * 70)

    max_err = 0
    nucleus_names = {1: "p", 2: "d", 4: "alpha", 6: "C-12", 8: "O-16", 26: "Fe-56", 79: "Au-197", 92: "U-238"}
    for Z in test_nuclei:
        H_Z = compute_H_naive(Z)
        m_pred = m_Planck / (H_Z ** 2)
        m_exp = known_masses_kg[Z]
        err_pct = abs(m_pred - m_exp) / m_exp * 100
        max_err = max(max_err, err_pct)
        name = nucleus_names[Z]
        print("{:>3} | {:>6} | {:>10.6f} | {:>14.6e} | {:>14.6e} | {:>7.2f}%".format(
            Z, name, H_Z, m_pred, m_exp, err_pct))

    print("-" * 70)
    print("Erreur maximale : {:.2f}%".format(max_err))
    print()

    if max_err < 1.0:
        print("SUCCES : Erreur < 1% - L'hypothese m = 1/H^2 tient pour ces noyaux")
        return True
    elif max_err < 10.0:
        print("PARTIEL : Erreur 1-10% - Piste prometteuse mais correction necessaire")
        return False
    else:
        print("ECHEC : Erreur > 10% - L'hypothese m = m_Planck/H^2 est fausse pour les noyaux")
        return False


def test_hypothesis_mass_proportional_to_Z_times_H():
    print("=" * 70)
    print("TEST HYPOTHESE ALTERNATIVE : m_Z proportional a Z x H_Z")
    print("=" * 70)

    test_nuclei = [1, 2, 4, 6, 8, 26, 79, 92]
    print("{:>3} | {:>6} | {:>10} | {:>14} | {:>14} | {:>8}".format(
        "Z", "Noyau", "ZxH_Z", "m_pred (kg)", "m_exp (kg)", "Erreur %"))
    print("-" * 70)

    max_err = 0
    nucleus_names = {1: "p", 2: "d", 4: "alpha", 6: "C-12", 8: "O-16", 26: "Fe-56", 79: "Au-197", 92: "U-238"}
    for Z in test_nuclei:
        H_Z = compute_H_naive(Z)
        m_pred = m_Planck * (Z * H_Z) / (1 * phi)
        m_exp = known_masses_kg[Z]
        err_pct = abs(m_pred - m_exp) / m_exp * 100
        max_err = max(max_err, err_pct)
        name = nucleus_names[Z]
        print("{:>3} | {:>6} | {:>10.6f} | {:>14.6e} | {:>14.6e} | {:>7.2f}%".format(
            Z, name, Z*H_Z, m_pred, m_exp, err_pct))

    print("-" * 70)
    print("Erreur maximale : {:.2f}%".format(max_err))
    return max_err < 10.0


def test_hypothesis_binding_energy():
    print("=" * 70)
    print("TEST : Energie de liaison = interference harmonique")
    print("=" * 70)
    print("A implementer : E_bind = -|Sum H_k Psi_1^k|^2")
    print()


if __name__ == "__main__":
    print("\nTEST MASSES HARMONIQUES - EQUATION MAITRESSE PSI = SUM H_n(PSI_1)^n\n")

    success1 = test_hypothesis_mass_equals_planck_over_H2()
    print()
    success2 = test_hypothesis_mass_proportional_to_Z_times_H()
    print()
    test_hypothesis_binding_energy()

    print("=" * 70)
    print("RESUME")
    print("=" * 70)
    print("m = m_Planck / H^2 : {}".format("OK" if success1 else "ECHEC"))
    print("m proportional a ZxH : {}".format("OK" if success2 else "ECHEC"))
    print()
    if not success1 and not success2:
        print("Aucune hypothese simple ne marche.")
        print("Prochaine etape : deriver H_Z depuis l'equation maitresse")
        print("avec conditions aux limites nucleaires (portee courte, saturation).")