# -*- coding: utf-8 -*-
"""
test_ile_stabilite.py — v2 : PREDICTION EX-ANTE CORRIGEE (artefacts geres)
==========================================================================
Corrections par rapport a v1 :
  1. S_2n decroit avec N : le max au bord de grille (N=150) est un artefact.
     -> on cherche les MAXIMA LOCAUX (S_2n(N) > S_2n(N-2) et > S_2n(N+2))
        et le max sur N in [160,198] (loin des bords).
  2. Le modele sur-lie les superlourds de ~9.5 MeV (offset systematique) :
     les valeurs ABSOLUES de Q_alpha ne sont pas fiables -> on valide et
     predit les TENDANCES RELATIVES (courbes S_2n(N) et dQ_alpha).
  3. Validation : comparaison relative modele vs AME2020 sur Z=104..118.
  4. Prediction Z=119..126 : N* de max S_2n, et confrontation des deux
     candidats de fermeture : N=168 (HO, ce modele) vs N=184 (Mayer-Jensen).
"""

import math
import os
import numpy as np

M_E_U = 5.48579909065e-4
M_P_U = M_E_U * 6 * math.pi ** 5
M_N_U = 1.00866491595
ME_H = 7288.97061
ME_N = 8071.31713

MAG_HO = np.array([2, 8, 20, 40, 70, 112, 168, 240])
LIT = [15.75, 17.8, 0.711, 23.7, 11.18]
B_HE4 = 28.296


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
    Nv, Zv, Av = np.asarray(Nv, float), np.asarray(Zv, float), np.asarray(Av, float)
    s = np.zeros_like(Nv)
    for Mm in MAG_HO:
        s += np.exp(-((Nv - Mm) / np.sqrt(np.maximum(Nv, 1))) ** 2)
        s += np.exp(-((Zv - Mm) / np.sqrt(np.maximum(Zv, 1))) ** 2)
    return -(20.5 * Av ** (-1.0 / 3.0)) * s


def b_model(c, Nv, Zv):
    Av = np.asarray(Nv) + np.asarray(Zv)
    return b_semf(c, Av, Nv, Zv) + shell_ho(Nv, Zv, Av)


# donnees AME2020
Z0, N0, A0, ME0 = [], [], [], []
for ligne in open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "data/ame2020_mass.txt"), encoding="latin-1"):
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
    Z0.append(z); N0.append(n); A0.append(a); ME0.append(me)
Z0, N0, A0, ME0 = (np.array(x) for x in (Z0, N0, A0, ME0))
B0 = (Z0 * ME_H + N0 * ME_N - ME0) / 1000.0
m = (A0 >= 40) & (A0 <= 260) & (np.abs(N0 - Z0) <= 40)
T = termes(A0[m], N0[m], Z0[m])
X = np.column_stack((T[0], -T[1], -T[2], -T[3], T[4]))
FIT, *_ = np.linalg.lstsq(X, B0[m], rcond=None)


def courbes(z, nmin=140, nmax=200):
    """S_2n et Q_alpha du modele sur [nmin, nmax] pour un Z donne."""
    ns = np.arange(nmin, nmax + 1)
    b = np.array([b_model(LIT, np.array([n]), np.array([z]))[0] for n in ns])
    s2n = b[2:] - b[:-2]
    qa = np.array([b_model(LIT, np.array([n]), np.array([z]))[0]
                   - b_model(LIT, np.array([n - 2]), np.array([z - 2]))[0] - B_HE4
                   for n in ns])
    return ns, b, s2n, qa


def max_local(x):
    """Indices des maxima locaux stricts."""
    return [i for i in range(1, len(x) - 1) if x[i] > x[i - 1] and x[i] > x[i + 1]]


print("=" * 78)
print("ILE DE STABILITE v2 — maxima locaux de S_2n, tendances relatives")
print("=" * 78)

# ---- validation relative : modele vs AME sur Z=104..118 ----
print("\n[1] VALIDATION RELATIVE : S_2n(N) modele vs AME2020 (Z=104..118)")
ds = []
for z in range(104, 119):
    ame = {int(n): b for n, b in zip(N0, B0) if Z0[np.where(N0 == n)[0][0]] == z} if False else {}
    # S_2n AME pour ce Z
    s2_ame = {}
    for i in range(len(Z0)):
        if Z0[i] != z or N0[i] < 141:
            continue
        n = N0[i]
        j = np.where((Z0 == z) & (N0 == n - 2))[0]
        if len(j):
            s2_ame[n] = B0[i] - B0[j[0]]
    if len(s2_ame) < 4:
        continue
    ns = np.array(sorted(s2_ame))
    s2m = np.array([s2_ame[n] for n in ns])
    ns2, b, s2n, qa = courbes(z)
    # interpolation du modele sur les N AME
    s2p = np.array([float(s2n[np.where(ns2[2:] == n)[0][0]]) if n in ns2[2:] else np.nan
                    for n in ns])
    ok = ~np.isnan(s2p)
    if ok.sum() >= 4:
        d = np.abs(s2p[ok] - s2m[ok])
        corr = np.corrcoef(s2p[ok], s2m[ok])[0, 1]
        ds.append((z, d.mean(), corr, ok.sum()))
        print(f"  Z={z:3d}: |dS_2n| moyen = {d.mean():5.2f} MeV"
              f" | corr(S_2n modele, S_2n AME) = {corr:+.2f} (n={ok.sum()})")
dA = [x[1] for x in ds]
print(f"  -> ecart moyen global : {np.mean(dA):.2f} MeV | correlation moyenne :"
      f" {np.mean([x[2] for x in ds]):+.2f}")

# ---- prediction Z=119..126 ----
print("\n[2] PREDICTION Z=119..126 : N* (max S_2n sur N in [160,198])")
print("    et comparaison des fermetures N=168 (HO) vs N=184 (MJ)")
for z in range(119, 127):
    ns, b, s2n, qa = courbes(z)
    # max sur [160,198]
    sel = (ns[2:] >= 160) & (ns[2:] <= 198)
    nstar = ns[2:][sel][np.argmax(s2n[sel])]
    s168 = s2n[np.where(ns[2:] == 168)[0][0]]
    s184 = s2n[np.where(ns[2:] == 184)[0][0]]
    loc = max_local(s2n)
    nloc = [int(ns[2:][i]) for i in loc if 152 <= ns[2:][i] <= 198]
    print(f"  Z={z:3d}: N*={int(nstar):3d} (S_2n={s2n[np.where(ns[2:] == nstar)[0][0]]:5.2f})"
          f" | S_2n(168)={s168:5.2f}  S_2n(184)={s184:5.2f}"
          f" | max locaux : {nloc}")

# ---- comparaison des deux candidats d'ile ----
print("\n[3] Les deux candidats d'ile : fermeture N=168 (HO) vs N=184 (MJ)")
print("    signature : S_2n(168)-S_2n(166) vs S_2n(184)-S_2n(182) (positif =")
print("    stabilisation par la fermeture)")
for z in (114, 118, 120, 122, 124, 126):
    ns, b, s2n, qa = courbes(z)
    g168 = s2n[np.where(ns[2:] == 168)[0][0]] - s2n[np.where(ns[2:] == 166)[0][0]]
    g184 = s2n[np.where(ns[2:] == 184)[0][0]] - s2n[np.where(ns[2:] == 182)[0][0]]
    print(f"  Z={z:3d}: gain HO 168 : {g168:+5.2f} MeV | gain MJ 184 : {g184:+5.2f} MeV"
          f"  -> {'HO' if g168 > g184 else 'MJ'}")
