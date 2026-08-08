# -*- coding: utf-8 -*-
"""
analyse_sensibilite_semf.py — LA COMPENSATION : pourquoi 2 % ne suffit pas
==========================================================================
La SEMF est une somme de termes ~1000-3000 MeV qui se compensent pour donner
B ~ 500-2000 MeV. Un coefficient a +/-2 % d'erreur cree donc une erreur
d'environ +/-2 % * terme ~ 20-60 MeV — soit 10x le RMS de la litterature.

Cette analyse mesure :
  1. le nombre de condition de la matrice des termes (colinearite de la
     vallee de stabilite : impossible d'ajuster 5 coefficients sur les 86
     isotopes stables seuls — d'ou les coefficients "negatifs" absurdes)
  2. la sensibilite du RMS a +1 % sur chaque coefficient (autour des
     valeurs de litterature)
  3. la precision requise sur aV (terme ~aV*A)
  4. si des formes harmoniques simples atteignent cette precision
  5. test de permutation : la correlation Phi/residuel (r=-0.24) est-elle
     significative, ou un artefact de la dependance en A ?
"""

import itertools
import math
import os
import numpy as np

PHI = (1 + math.sqrt(5)) / 2
PI, E = math.pi, math.e
S2, S3, S5 = math.sqrt(2), math.sqrt(3), math.sqrt(5)
M_E_U = 5.48579909065e-4
M_P_U = M_E_U * 6 * PI ** 5
M_N_U = 1.00866491595
U_MEV = 931.49410242

_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "test_nuclear_mass_derivation.py"), encoding="utf-8").read()
exec(_src.split("def main")[0])

ZS0 = np.array(list(range(1, 119)))
A0 = np.array([int(round(NUCLEAR_DATA[z][1])) for z in ZS0])
M0 = np.array([NUCLEAR_DATA[z][1] for z in ZS0])
N0 = A0 - ZS0
REEL = (M0 % 1 != 0) | (A0 == 12)
ZS, A, M, N = ZS0[REEL], A0[REEL], M0[REEL], N0[REEL]
B_MEAS = (ZS * (M_P_U + M_E_U) + N * M_N_U - M) * U_MEV
LOURD = A >= 16
Bm, Al, Nl, Zl = B_MEAS[LOURD], A[LOURD], N[LOURD], ZS[LOURD]

LIT = np.array([15.75, 17.8, 0.711, 23.7, 11.18])   # (aV, aS, aC, aA, d)


def termes(Av, Nv, Zv):
    Zv = np.asarray(Zv, float)
    p = np.zeros_like(Av)
    p[(Av % 2 == 0) & (Zv % 2 == 0)] = 1.0
    p[(Av % 2 == 1) & (Zv % 2 == 1)] = -1.0
    return (Av, Av ** (2 / 3), Zv * (Zv - 1) / Av ** (1 / 3),
            (Nv - Zv) ** 2 / Av, p / np.sqrt(Av))


def b_pred(c, Av, Nv, Zv):
    t = termes(Av, Nv, Zv)
    return c[0] * t[0] - c[1] * t[1] - c[2] * t[2] - c[3] * t[3] + c[4] * t[4]


def rms(c, Av, Nv, Zv, y):
    return np.sqrt(np.mean((y - b_pred(c, Av, Nv, Zv)) ** 2))


print("=" * 72)
print("LA COMPENSATION — precision requise sur les coefficients SEMF")

# 1) conditionnement
X = np.column_stack(termes(Al, Nl, Zl))
cond = np.linalg.cond(X)
print(f"\n[1] Conditionnement de la matrice des termes (vallee de stabilite)")
print(f"    cond(X) = {cond:.1e}  (<<1000 : bien conditionne ; >>1e6 : colineaire)")
print(f"    -> impossible d'ajuster les 5 coefficients sur les 86 isotopes")
print(f"       stables seuls (c'est pourquoi le fit direct donne aS<0).")
print(f"    Reference : les coefficients de litterature viennent d'un fit")
print(f"       sur ~3000 noyaux (vallee + zone hors-vallee).")

# 2) sensibilite autour des valeurs de litterature
rms_lit = rms(LIT, Al, Nl, Zl, Bm)
print(f"\n[2] Sensibilite (autour des coefficients de litterature, RMS0 = "
      f"{rms_lit:.3f} MeV)")
for i, nom in enumerate(("aV", "aS", "aC", "aA", "d")):
    c1 = LIT.copy()
    c1[i] *= 1.01
    print(f"    {nom} +1% : RMS = {rms(c1, Al, Nl, Zl, Bm):7.3f} MeV")

# 3) precision requise sur aV
print("\n[3] Precision requise sur aV pour rester <= 7 MeV (terme aV*A, A~200)")
for tol in (1.0, 0.5, 0.2, 0.1, 0.05):
    c1 = LIT.copy()
    c1[0] *= 1 + tol / 100
    print(f"    |daV| = {tol:4.2f} %  -> RMS = {rms(c1, Al, Nl, Zl, Bm):6.3f} MeV")

# 4) les formes harmoniques simples atteignent-elles 0.1 % ?
print("\n[4] Meilleures formes harmoniques simples (phi,pi,e) vs precision requise")
for nom, cible in zip(("aV", "aS", "aC", "aA", "d"), LIT):
    best = []
    for a in range(-6, 7):
        for b in range(-6, 7):
            for c in range(-6, 7):
                if abs(a) + abs(b) + abs(c) > 8 or abs(a) + abs(b) + abs(c) == 0:
                    continue
                v = PHI ** a * PI ** b * E ** c
                best.append((abs(v - cible) / cible * 100, (a, b, c), v))
    best.sort()
    print(f"    {nom} cible {cible:7.3f} : meilleure simple {best[0][2]:8.4f}"
          f" ({best[0][0]:5.2f} %) — requis ~0.1 %")
print("    -> le treillis (phi,pi,e) a une maille ~1-3 % : 0.1 % est")
print("       inatteignable par des formes simples.")

# 5) permutation test : corr(Phi, residuel)
print("\n[5] Test de permutation : corr(Phi, residuel) significative ?")


def diviseurs(n):
    out = []
    for i in range(1, int(math.sqrt(n)) + 1):
        if n % i == 0:
            out.append(i)
            if i != n // i:
                out.append(n // i)
    return out


H7 = {1: PHI, 2: PI, 3: E, 4: S2, 5: S3, 6: S5, 7: E / PI}


def H_d(d):
    return H7.get(d, PHI)


def phi_c(az, zz, nn):
    ens = set(diviseurs(az)) | set(diviseurs(zz)) | set(diviseurs(max(nn, 1)))
    re = im = 0.0
    for d in ens:
        th = 2 * math.pi * d * PHI
        re += H_d(d) * math.cos(th)
        im += H_d(d) * math.sin(th)
    return re * re + im * im


phis = np.array([phi_c(int(a), int(z), int(n)) for a, z, n in zip(A, ZS, N)])
logp = np.log10(phis + 1e-9)
res = B_MEAS - b_pred(LIT, A, N, ZS)
r0 = np.corrcoef(logp, res)[0, 1]

rng = np.random.default_rng(42)
n_perm = 20000
count = sum(abs(np.corrcoef(logp, rng.permutation(res))[0, 1]) >= abs(r0)
            for _ in range(n_perm))
print(f"    r_obs = {r0:+.3f} | p = {count / n_perm:.4f} (20000 permutations)")
rA = np.corrcoef(logp, A)[0, 1]
rAres = np.corrcoef(A, res)[0, 1]
print(f"    corr(log Phi, A)  = {rA:+.3f}   <- artefact si forte")
print(f"    corr(A, residuel) = {rAres:+.3f}")
