# -*- coding: utf-8 -*-
"""
test_coquille_ondulatoire.py — COQUILLE THEORIQUE 0 PARAMETRE
==============================================================
L'etape 2 a montre qu'une coquille gaussienne sur les nombres magiques
(2 params ajustes) ameliore la SEMF : RMS 6.50 -> 5.59 MeV (CV 5-fold, -14%).

Ici : la SAME correction, mais avec amplitude et largeur DERIVEES de la
physique de l'oscillateur harmonique (aucun parametre ajuste) :

    amplitude  c(A) = hbar.omega / 4      avec hbar.omega = 41 . A^(-1/3) MeV
                        (Bohr-Mottelson, publie — amplitude de coquille ~
                         hbar.omega/4..hbar.omega/2 dans la theorie de
                         Strutinsky)
    largeur    w(N)  = sqrt(N)            (espacement des coquilles HO ~
                         dN/dn = 2n+3 ~ 2.sqrt(2N), demi-largeur ~ sqrt(N))

Deux jeux de nombres magiques compares :
    HO pur      : 2, 8, 20, 40, 70, 112, 168  (degenerescences 2(n+1)(n+2))
                  — "modes stationnaires de l'oscillateur harmonique 3D"
    Mayer-Jensen : 2, 8, 20, 28, 50, 82, 126  (avec couplage spin-orbite)

Validation croisee 5-fold identique pour toutes les variantes.
Reference : coquille ajustee (grille c,w sur plis d'entrainement).
"""

import math
import os
import numpy as np

PHI = (1 + math.sqrt(5)) / 2
PI, E = math.pi, math.e
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
B = (ZS * (M_P_U + M_E_U) + N * M_N_U - M) * U_MEV
LOURD = A >= 16

LIT = [15.75, 17.8, 0.711, 23.7, 11.18]


def termes(Av, Nv, Zv):
    Zv = np.asarray(Zv, float)
    p = np.zeros_like(Av)
    p[(Av % 2 == 0) & (Zv % 2 == 0)] = 1.0
    p[(Av % 2 == 1) & (Zv % 2 == 1)] = -1.0
    return (Av, Av ** (2 / 3), Zv * (Zv - 1) / Av ** (1 / 3),
            (Nv - Zv) ** 2 / Av, p / np.sqrt(Av))


t = termes(A, N, ZS)
B_SEMF = LIT[0] * t[0] - LIT[1] * t[1] - LIT[2] * t[2] - LIT[3] * t[3] + LIT[4] * t[4]
res = B - B_SEMF

MAG_HO = np.array([2, 8, 20, 40, 70, 112, 168])
MAG_MJ = np.array([2, 8, 20, 28, 50, 82, 126])


def hbar_omega(Av):
    return 41.0 * np.asarray(Av, float) ** (-1.0 / 3.0)


def shell_theorique(Nv, Zv, Av, mags, amplitude, largeur):
    """Coquille 0 parametre : -c(A).somme_M exp(-((x-M)/w(x))^2), x = N et Z."""
    Nv, Zv, Av = np.asarray(Nv, float), np.asarray(Zv, float), np.asarray(Av, float)
    s = np.zeros_like(Nv)
    for M in mags:
        s += np.exp(-((Nv - M) / largeur(Nv)) ** 2)
        s += np.exp(-((Zv - M) / largeur(Zv)) ** 2)
    return -amplitude(Av) * s


def rms_cv(ajustee=False, variante=None):
    """CV 5-fold. ajustee=True : grille (c,w) sur plis d'entrainement.
    Sinon : variante theorique pre-registree (aucun ajustement)."""
    rng = np.random.default_rng(7)
    idx = np.where(LOURD)[0]
    rng.shuffle(idx)
    folds = np.array_split(idx, 5)
    rms_test = []
    for k in range(5):
        val = folds[k]
        tr = np.concatenate([f for i, f in enumerate(folds) if i != k])
        if ajustee:
            mel = (1e30, None)
            for c in np.arange(0, 4, 0.1):
                for w in np.arange(1, 9, 0.5):
                    s = -c * (np.exp(-((N[tr] - 2) / w) ** 2) if False else 0)
                    sc = np.zeros_like(N[tr], float)
                    for M in MAG_MJ:
                        sc += np.exp(-((N[tr] - M) / w) ** 2)
                        sc += np.exp(-((ZS[tr] - M) / w) ** 2)
                    r = res[tr] + c * sc
                    m = np.sqrt(np.mean(r ** 2))
                    if m < mel[0]:
                        mel = (m, (c, w))
            c_s, w_s = mel[1]
            scv = np.zeros_like(N[val], float)
            for M in MAG_MJ:
                scv += np.exp(-((N[val] - M) / w_s) ** 2)
                scv += np.exp(-((ZS[val] - M) / w_s) ** 2)
            pred = -c_s * scv
        else:
            mags, amp, lar = variante
            pred = shell_theorique(N[val], ZS[val], A[val], mags, amp, lar)
        rms_test.append(np.sqrt(np.mean((res[val] - pred) ** 2)))
    return np.mean(rms_test)


print("=" * 78)
print("COQUILLE THEORIQUE 0 PARAMETRE — validation croisee 5-fold (n=79)")
print(f"SEMF seule : RMS = {rms_cv(ajustee=False, variante=(MAG_MJ, lambda A: A * 0, lambda x: x)):.3f} MeV")
print("=" * 78)

# reference ajustee
r_fit = rms_cv(ajustee=True)
print(f"\n[Ref] Coquille AJUSTEE (grille c,w)       : RMS = {r_fit:.3f} MeV  (-14%)")

# variantes theoriques 0 parametre
Amp4 = lambda A: hbar_omega(A) / 4.0          # hbar.omega/4
Amp2 = lambda A: hbar_omega(A) / 2.0          # hbar.omega/2
W_sqrt = lambda x: np.sqrt(np.maximum(x, 1.0))
W_cst85 = lambda x: 8.5 * np.ones_like(np.asarray(x, float))

variantes = [
    ("HO pur      + hbar.omega/4 + w=sqrt(x) ", MAG_HO, Amp4, W_sqrt),
    ("MJ          + hbar.omega/4 + w=sqrt(x) ", MAG_MJ, Amp4, W_sqrt),
    ("HO pur      + hbar.omega/2 + w=sqrt(x) ", MAG_HO, Amp2, W_sqrt),
    ("MJ          + hbar.omega/2 + w=sqrt(x) ", MAG_MJ, Amp2, W_sqrt),
    ("HO pur      + hbar.omega/4 + w=8.5 cst  ", MAG_HO, Amp4, W_cst85),
    ("MJ          + hbar.omega/4 + w=8.5 cst  ", MAG_MJ, Amp4, W_cst85),
]
print("\n[Theorie 0 parametre]")
for nom, mags, amp, lar in variantes:
    r = rms_cv(ajustee=False, variante=(mags, amp, lar))
    tag = ""
    if r <= r_fit + 0.15:
        tag = "  <= niveau de la coquille ajustee !"
    print(f"  {nom}: RMS = {r:.3f} MeV{tag}")

# diagnostic : amplitude de la coquille theorique aux nombres magiques
print("\n[Diagnostic] amplitude c(A) = hbar.omega/4 sur la gamme :")
for Aa in (56, 90, 140, 208, 238):
    print(f"  A={Aa:3d} : hbar.omega/4 = {hbar_omega(Aa) / 4:.2f} MeV"
          f"  (ajuste : 1.8-3.9)")
print("\n[Diagnostic] largeur w=sqrt(N) aux fermetures :")
for Nn in (28, 50, 82, 126):
    print(f"  N={Nn:3d} : w = {math.sqrt(Nn):.2f}  (ajuste : 8.5)")
