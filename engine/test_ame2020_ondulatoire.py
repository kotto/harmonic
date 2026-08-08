# -*- coding: utf-8 -*-
"""
test_ame2020_ondulatoire.py — TEST PUBLICATION : TABLE COMPLETE AME2020
=======================================================================
La coquille harmonique HO 0-parametre (fermetures 2(n+1)(n+2), amplitude
hbar.omega/2 = 20.5.A^(-1/3), largeur sqrt(N)) a donne -35 % sur les 68
noyaux de la vallee de stabilite. Ici : test sur les ~3400 noyaux de la
table AME2020 (vallee + hors-vallee), avec 3 fenetres et 2 protocoles :

  PROTOCOLE A (coefficients de litterature, 0 fit) :
      SEMF(litt)  vs  SEMF(litt) + coquille HO

  PROTOCOLE B (CV 5-fold, SEMF RE-AJUSTEE a chaque pli) :
      SEMF(fit)   vs  SEMF(fit) + coquille HO
      -> la valeur ajoutee de la coquille par rapport au MEILLEUR SEMF
         possible (les coefficients absorbent ce qu'ils peuvent).

Source : https://www-nds.iaea.org/amdc/ame2020/mass_1.mas20.txt
Colonnes : N-Z, N, Z, A, EL, O, MASS EXCESS (keV), ...
BE (keV) = Z.ME_H + N.ME_n - ME_atom,  ME_H = 7288.97061, ME_n = 8071.31713
Validation : C-12 -> BE = 92161.7 keV ; Fe-56 -> 492254 keV.
"""

import math
import os
import re
import numpy as np

PHI = (1 + math.sqrt(5)) / 2
PI, E = math.pi, math.e
M_E_U = 5.48579909065e-4
M_P_U = M_E_U * 6 * PI ** 5
M_N_U = 1.00866491595
U_MEV = 931.49410242
ME_H = 7288.97061          # keV — mass excess de l'atome d'hydrogene
ME_N = 8071.31713          # keV — mass excess du neutron

# ----------------------------------------------------------------------
# Lecture de la table AME2020
# ----------------------------------------------------------------------
def lire_ame(chemin):
    """Parsing par tokens. La colonne 'origine' (vide la plupart du temps)
    decale les tokens : on cherche le PREMIER token flottant apres l'element."""
    Z, N, A, ME, extrap = [], [], [], [], []
    for ligne in open(chemin, encoding="latin-1"):
        t = ligne.split()
        if len(t) < 7:
            continue
        try:
            z, n, a = int(t[2]), int(t[1]), int(t[3])
        except ValueError:
            continue
        if z < 1 or a < 2 or n < 0 or n + z != a:
            continue
        me = None
        for tok in t[5:]:
            try:
                me = float(tok.rstrip("#"))
                break
            except ValueError:
                continue
        if me is None:
            continue
        Z.append(z)
        N.append(n)
        A.append(a)
        ME.append(me)
        extrap.append("#" in t[5] or "#" in t[6] or "#" in t[7])
    return (np.array(Z), np.array(N), np.array(A),
            np.array(ME), np.array(extrap, bool))


Z, N, A, ME, EXTRAP = lire_ame(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            "data/ame2020_mass.txt"))
# BE totale (keV) -> MeV
B_MEAS = (Z * ME_H + N * ME_N - ME) / 1000.0

# validations
for zz, nn, aa in ((6, 6, 12), (26, 30, 56), (82, 126, 208)):
    i = int(np.where((Z == zz) & (N == nn))[0][0])
    print(f"[validation] {aa} (Z={zz}, N={nn}) : BE = {B_MEAS[i]:8.1f} MeV"
          f"  (attendu : C-12 92.2 / Fe-56 492.3 / Pb-208 1636.4)")
print(f"[donnees] {len(Z)} noyaux AME2020 (dont {EXTRAP.sum()} extrapoles '#')\n")

# ----------------------------------------------------------------------
# Modeles
# ----------------------------------------------------------------------
LIT = [15.75, 17.8, 0.711, 23.7, 11.18]
MAG_HO = np.array([2, 8, 20, 40, 70, 112, 168])


def termes(Av, Nv, Zv):
    Zv = np.asarray(Zv, float)
    p = np.zeros_like(Av)
    p[(Av % 2 == 0) & (Zv % 2 == 0)] = 1.0
    p[(Av % 2 == 1) & (Zv % 2 == 1)] = -1.0
    return (Av, Av ** (2 / 3), Zv * (Zv - 1) / Av ** (1 / 3),
            (Nv - Zv) ** 2 / Av, p / np.sqrt(Av))


def b_semf(c, Av, Nv, Zv):
    t = termes(Av, Nv, Zv)
    return c[0] * t[0] - c[1] * t[1] - c[2] * t[2] - c[3] * t[3] + c[4] * t[4]


def shell_ho(Nv, Zv, Av):
    """Coquille harmonique 0 parametre (pre-registree le 08/08/2026)."""
    Nv, Zv, Av = np.asarray(Nv, float), np.asarray(Zv, float), np.asarray(Av, float)
    s = np.zeros_like(Nv)
    for Mm in MAG_HO:
        s += np.exp(-((Nv - Mm) / np.sqrt(np.maximum(Nv, 1))) ** 2)
        s += np.exp(-((Zv - Mm) / np.sqrt(np.maximum(Zv, 1))) ** 2)
    return -(20.5 * Av ** (-1.0 / 3.0)) * s     # hbar.omega/2, hbar.omega=41/A^(1/3)


def masse(B, Av, Nv, Zv):
    return Zv * (M_P_U + M_E_U) + Nv * M_N_U - B / U_MEV


def rms(y1, y2):
    return np.sqrt(np.mean((y1 - y2) ** 2))


# ----------------------------------------------------------------------
# Fenetres
# ----------------------------------------------------------------------
print("=" * 78)
print("PROTOCOLE A — coefficients de litterature (aucun ajustement)")
print("=" * 78)
for label, masque in (("TOUS les noyaux   ", A >= 2),
                      ("A>=16             ", A >= 16),
                      ("A>=40             ", A >= 40),
                      ("A>=56             ", A >= 56),
                      ("A>=40, experiment.", (A >= 40) & ~EXTRAP),
                      ("A>=56, experiment.", (A >= 56) & ~EXTRAP)):
    m = masque
    B0 = b_semf(LIT, A[m], N[m], Z[m])
    B1 = B0 + shell_ho(N[m], Z[m], A[m])
    r0, r1 = rms(B_MEAS[m], B0), rms(B_MEAS[m], B1)
    e0 = np.abs(masse(B0, A[m], N[m], Z[m]) - (A[m] + ME[m] / 1000 / U_MEV)) / (A[m]) * 100
    e1 = np.abs(masse(B1, A[m], N[m], Z[m]) - (A[m] + ME[m] / 1000 / U_MEV)) / (A[m]) * 100
    print(f"  {label}: n={m.sum():4d} | SEMF {r0:6.2f} -> +HO {r1:6.2f} MeV"
          f"  (-{(1 - r1 / r0) * 100:5.1f} %) | masses {e0.mean():.4f}% -> {e1.mean():.4f}%")

# ----------------------------------------------------------------------
print("\n" + "=" * 78)
print("PROTOCOLE B — CV 5-fold, SEMF RE-AJUSTEE (avec et sans coquille)")
print("=" * 78)
for label, masque in (("A>=40, experiment.", (A >= 40) & ~EXTRAP),
                      ("A>=56, experiment.", (A >= 56) & ~EXTRAP),
                      ("TOUS, experiment. ", (A >= 2) & ~EXTRAP)):
    m = masque
    idx = np.where(m)[0]
    rng = np.random.default_rng(11)
    rng.shuffle(idx)
    folds = np.array_split(idx, 5)
    rA, rB = [], []
    for k in range(5):
        val, tr = folds[k], np.concatenate([f for i, f in enumerate(folds) if i != k])
        # matrice de design AVEC les signes SEMF : [A, -A^(2/3), -C, -Asym, pair]
        T = termes(A[tr], N[tr], Z[tr])
        X = np.column_stack((T[0], -T[1], -T[2], -T[3], T[4]))
        y = B_MEAS[tr]
        cA, *_ = np.linalg.lstsq(X, y, rcond=None)                    # SEMF seule
        cB, *_ = np.linalg.lstsq(X, y - shell_ho(N[tr], Z[tr], A[tr]), rcond=None)
        B0 = b_semf(cA, A[val], N[val], Z[val])
        B1 = b_semf(cB, A[val], N[val], Z[val]) + shell_ho(N[val], Z[val], A[val])
        rA.append(rms(B_MEAS[val], B0))
        rB.append(rms(B_MEAS[val], B1))
    rA, rB = np.array(rA), np.array(rB)
    print(f"  {label}: n={m.sum():4d} | SEMF(fit) {rA.mean():6.2f}"
          f" -> +HO {rB.mean():6.2f} MeV  (-{(1 - rB.mean() / rA.mean()) * 100:5.1f} %)")
    # bootstrap au niveau NOYAUX (residus apparies)
    rng2 = np.random.default_rng(3)
    resA, resB = [], []
    for k in range(5):
        val = folds[k]
        T = termes(A[tr], N[tr], Z[tr])
        X = np.column_stack((T[0], -T[1], -T[2], -T[3], T[4]))
        cA, *_ = np.linalg.lstsq(X, B_MEAS[tr], rcond=None)
        cB, *_ = np.linalg.lstsq(X, B_MEAS[tr] - shell_ho(N[tr], Z[tr], A[tr]), rcond=None)
        resA.append(B_MEAS[val] - b_semf(cA, A[val], N[val], Z[val]))
        resB.append(B_MEAS[val] - (b_semf(cB, A[val], N[val], Z[val])
                                   + shell_ho(N[val], Z[val], A[val])))
    resA = np.concatenate(resA)
    resB = np.concatenate(resB)
    n = len(resA)
    diff = []
    for _ in range(3000):
        b = rng2.choice(n, size=n, replace=True)
        diff.append(np.sqrt(np.mean(resA[b] ** 2)) - np.sqrt(np.mean(resB[b] ** 2)))
    diff = np.array(diff)
    print(f"      bootstrap (noyaux) : IC95 [{np.percentile(diff, 2.5):.3f}, "
          f"{np.percentile(diff, 97.5):.3f}] MeV | P(>0) = {(diff > 0).mean() * 100:.1f} %")

# ----------------------------------------------------------------------
print("\n[Complement] gain par region (A>=40 experiment., litterature)")
m = (A >= 40) & ~EXTRAP
B0 = b_semf(LIT, A[m], N[m], Z[m])
B1 = B0 + shell_ho(N[m], Z[m], A[m])
r0, r1 = np.abs(B_MEAS[m] - B0), np.abs(B_MEAS[m] - B1)
for reg, sel in (("vallee |N-Z|<=8        ", np.abs(N[m] - Z[m]) <= 8),
                 ("proche |N-Z|<=20       ", np.abs(N[m] - Z[m]) <= 20),
                 ("loin   |N-Z|>20        ", np.abs(N[m] - Z[m]) > 20),
                 ("N>=90 (deforme potent.)", N[m] >= 90)):
    if sel.sum() == 0:
        continue
    print(f"  {reg}: n={sel.sum():4d} | SEMF {r0[sel].mean():6.2f}"
          f" -> +HO {r1[sel].mean():6.2f} MeV  (-{(1 - r1[sel].mean() / r0[sel].mean()) * 100:5.1f} %)")
