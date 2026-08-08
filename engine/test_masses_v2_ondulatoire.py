# -*- coding: utf-8 -*-
"""
test_masses_v2_ondulatoire.py — DERIVATION CORRIGEE DES 118 MASSES
==================================================================
Corrections structurelles (diagnostic 08/08/2026) :

  1. BASE : m_p = m_e * 6*pi^5 (GAGUT, verifie a 0.0019 %), plus m_e pour
     chaque Z (les masses CODATA sont ATOMIQUES : protons+neutrons+electrons).
  2. STRUCTURE : m = Z.m_p + N.m_n + Z.m_e - B(A,Z) — l'equation mere doit
     predire l'ENERGIE DE LIAISON B (~1 % de la masse) :
        B = aV.A - aS.A^(2/3) - aC.Z(Z-1)/A^(1/3) - aA.(N-Z)^2/A +/- d/A^(1/2)

  REFERENCE : SEMF de litterature (6 parametres publies, ajustes sur ~3000
  noyaux) -> RMS ~3 MeV sur B. Notre modele harmonique : 0 parametre ajuste.

  ANTI-NUMEROLOGIE : la recherche exhaustive de produits des 7 constantes
  trouve TOUJOURS un accord exact (artefact de densite de treillis). Le test
  honnete = les formes SIMPLES (<=3 facteurs, petits exposants) tiennent-elles
  a quelques % ? Et le RMS B du modele est-il comparable au SEMF ajuste ?
"""

import itertools
import math
import os
import numpy as np

PHI = (1 + math.sqrt(5)) / 2
PI, E = math.pi, math.e
S2, S3, S5 = math.sqrt(2), math.sqrt(3), math.sqrt(5)

M_E_U = 5.48579909065e-4
GAGUT = 6 * PI ** 5
M_P_U = M_E_U * GAGUT             # proton derive (GAGUT)
M_N_U = 1.00866491595
U_MEV = 931.49410242
ALPHA_TH = PI ** 4 * E ** -4 * PHI ** -5 * S2 ** -1 * S3 ** -5
HC_MEV_FM = 197.3269804
R0_FM = 1.25

SEMF = dict(aV=15.75, aS=17.8, aC=0.711, aA=23.7, d=11.18)

# ----------------------------------------------------------------------
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "test_nuclear_mass_derivation.py"), encoding="utf-8").read()
exec(_src.split("def main")[0])

ZS = np.array(list(range(1, 119)))
A = np.array([int(round(NUCLEAR_DATA[z][1])) for z in ZS])
M_U = np.array([NUCLEAR_DATA[z][1] for z in ZS])
N = A - ZS
# FILTRE : la table contient 32 masses factices arrondies a l'entier
# (Po=209.000, Og=294.000, ... placeholders). On ne garde que les masses
# reellement mesurees (non entieres) + C-12 (definition de l'unite).
REEL = (M_U % 1 != 0) | (A == 12)
print(f"[donnees] {REEL.sum()} masses CODATA reelles sur 118 "
      f"(les {118 - REEL.sum()} autres sont des placeholders dans la table)")
ZS, A, M_U, N = ZS[REEL], A[REEL], M_U[REEL], N[REEL]
# energie de liaison NUCLEAIRE mesuree : atome - Z.m_p - N.m_n - Z.m_e
B_MEAS = (ZS * (M_P_U + M_E_U) + N * M_N_U - M_U) * U_MEV


def termes_bw(Av, Nv, Zv):
    Zv = np.asarray(Zv, dtype=float)
    t_vol = Av
    t_sur = Av ** (2.0 / 3.0)
    t_cou = Zv * (Zv - 1) / Av ** (1.0 / 3.0)
    t_asy = (Nv - Zv) ** 2 / Av
    p = np.zeros_like(Av)
    p[(Av % 2 == 0) & (Zv % 2 == 0)] = 1.0
    p[(Av % 2 == 1) & (Zv % 2 == 1)] = -1.0
    return t_vol, t_sur, t_cou, t_asy, p / np.sqrt(Av)


def b_semf(c, Av, Nv, Zv):
    t1, t2, t3, t4, t5 = termes_bw(Av, Nv, Zv)
    return c["aV"] * t1 - c["aS"] * t2 - c["aC"] * t3 - c["aA"] * t4 + c["d"] * t5


def masse(B, Av, Nv, Zv):
    return Zv * (M_P_U + M_E_U) + Nv * M_N_U - B / U_MEV


def afficher_stage(titre, m_pred, B_pred=None, masque=None):
    msk = np.ones(len(ZS), bool) if masque is None else masque
    ec = np.abs(m_pred - M_U) / M_U * 100.0
    print(f"  {titre}")
    if B_pred is not None:
        rms = np.sqrt(np.mean((B_MEAS - B_pred)[msk] ** 2))
        print(f"    RMS B        : {rms:6.3f} MeV  (SEMF litterature : ~3 MeV)"
              f"  [n={msk.sum()}]")
    print(f"    ecart moyen   : {ec[msk].mean():8.4f} %   ecart max : {ec[msk].max():8.4f} %")
    print(f"    < 0.1% : {(ec[msk] < 0.1).sum():3d}   < 1% : {(ec[msk] < 1).sum():3d}"
          f"   < 5% : {(ec[msk] < 5).sum():3d}   /{msk.sum()}")
    return ec


MASQ_LOURD = A >= 16          # le SEMF n'est pas valide pour A < 16 (H..N)

print("=" * 78)
print("DERIVATION CORRIGEE — m = Z.(m_p + m_e) + N.m_n - B(A,Z)")
print(f"m_p = m_e * 6*pi^5 = {M_P_U:.6f} u (CODATA 1.0072765)  [GAGUT verifie]")
print(f"alpha harmonique = {ALPHA_TH:.10f} (CODATA 0.0072973526)")
print("=" * 78)

# ----------------------------------------------------------------------
print("\n[ETAPE 0] Bases (bornes)")
afficher_stage("m = A*u", A * 1.0)
afficher_stage("m = Z.m_p + N.m_n + Z.m_e (sans liaison)", ZS * (M_P_U + M_E_U) + N * M_N_U)

# ----------------------------------------------------------------------
print("\n[ETAPE 1a] SEMF LITTERATURE (6 params publies)")
B_lit = b_semf(SEMF, A, N, ZS)
m_lit = masse(B_lit, A, N, ZS)
print(f"  aV={SEMF['aV']} aS={SEMF['aS']} aC={SEMF['aC']} aA={SEMF['aA']} d={SEMF['d']}")
afficher_stage("SEMF litterature -> masses", m_lit, B_lit)
afficher_stage("SEMF litterature, A>=16 uniquement", m_lit, B_lit, MASQ_LOURD)

# ----------------------------------------------------------------------
print("\n[ETAPE 1b] Formes HARMONIQUES SIMPLES de (phi, pi, e)")
print("           contrainte de simplicite : |a|+|b|+|c| <= 5, |exp| <= 4")
print("           (la recherche exhaustive trouverait 0.00% partout : densite")
print("            de treillis — on ne garde que les formes simples)")


def formes_simples(cible, max_exp=4, poids_max=5):
    best, dans_3pc, dans_5pc, total = [], 0, 0, 0
    for a in range(-max_exp, max_exp + 1):
        for b in range(-max_exp, max_exp + 1):
            for c in range(-max_exp, max_exp + 1):
                if abs(a) + abs(b) + abs(c) > poids_max or abs(a) + abs(b) + abs(c) == 0:
                    continue
                v = PHI ** a * PI ** b * E ** c
                err = abs(v - cible) / cible * 100.0
                total += 1
                if err < 3:
                    dans_3pc += 1
                if err < 5:
                    dans_5pc += 1
                best.append((err, (a, b, c), v))
    best.sort(key=lambda t: t[0])
    return best[:4], dans_3pc, dans_5pc, total


aC_th = (3.0 / 5.0) * ALPHA_TH * HC_MEV_FM / R0_FM
print(f"\n  aC derive (3/5).alpha_h.hbar.c/r0 = {aC_th:.4f} MeV"
      f" (litt. {SEMF['aC']} | ecart {abs(aC_th - SEMF['aC']) / SEMF['aC'] * 100:.2f} %)")

FORME = {}
for nom, cible in (("aV", SEMF["aV"]), ("aS", SEMF["aS"]),
                   ("aA", SEMF["aA"]), ("d", SEMF["d"])):
    top, n3, n5, tot = formes_simples(cible)
    FORME[nom] = top[0]
    ligne = f"  {nom} cible {cible:6.3f} : "
    for err, exp, v in top[:3]:
        ligne += f"{v:6.3f} ({err:5.2f} %) [phi^{exp[0]} pi^{exp[1]} e^{exp[2]}]   "
    print(ligne)
    print(f"       (parmi {tot} formes simples : {n3} a <3%, {n5} a <5%)")

# ----------------------------------------------------------------------
print("\n[ETAPE 1c] SEMF HARMONIQUE (0 parametre ajuste, formes simples)")
coef_h = dict(aV=FORME["aV"][2], aS=FORME["aS"][2], aC=aC_th,
              aA=FORME["aA"][2], d=FORME["d"][2])
print(f"  aV={coef_h['aV']:.4f} aS={coef_h['aS']:.4f} aC={coef_h['aC']:.4f}"
      f" aA={coef_h['aA']:.4f} d={coef_h['d']:.4f}")
B_har = b_semf(coef_h, A, N, ZS)
m_har = masse(B_har, A, N, ZS)
afficher_stage("SEMF harmonique -> masses", m_har, B_har)
afficher_stage("SEMF harmonique, A>=16", m_har, B_har, MASQ_LOURD)

# ----------------------------------------------------------------------
print("\n[ETAPE 2] + correction de coquille (grille, 2 params : c, w)")
MAGIQUES = [2, 8, 20, 28, 50, 82, 126]


def coquille(x, c, w):
    s = np.zeros_like(np.asarray(x, dtype=float))
    for M in MAGIQUES:
        s += np.exp(-((x - M) / w) ** 2)
    return -c * s


res_lit = B_MEAS - B_lit
mel = (1e30, None)
for c in np.arange(0.0, 4.0, 0.1):
    for w in np.arange(1.0, 9.0, 0.5):
        r = res_lit - coquille(N, c, w) - coquille(ZS, c, w)
        m = np.sqrt(np.mean(r[MASQ_LOURD] ** 2))
        if m < mel[0]:
            mel = (m, (c, w))
rms_shell, (c_s, w_s) = mel
B_shell = B_lit + coquille(N, c_s, w_s) + coquille(ZS, c_s, w_s)
m_shell = masse(B_shell, A, N, ZS)
print(f"  c={c_s:.1f} MeV, w={w_s:.1f} (grille) ")
afficher_stage("SEMF + coquille -> masses", m_shell, B_shell)
afficher_stage("SEMF + coquille, A>=16", m_shell, B_shell, MASQ_LOURD)

# ----------------------------------------------------------------------
print("\n[ETAPE 3] Nombres magiques : signature dans le residuel SEMF")
r = B_MEAS - B_lit
for grp, sel in (("Z magiques", np.isin(ZS, MAGIQUES)),
                 ("N magiques", np.isin(N, MAGIQUES)),
                 ("non magiques", ~np.isin(ZS, MAGIQUES) & ~np.isin(N, MAGIQUES))):
    rr = np.abs(r[sel & MASQ_LOURD])
    print(f"  {grp:13s} : |residuel| moyen = {rr.mean():6.3f} MeV (n={sel.sum():3d})")

# ----------------------------------------------------------------------
print("\n[ETAPE 4] Equation mere dans B : correlation Phi / residuel SEMF")


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


def phi_corrige(az, zz, nn):
    ens = set(diviseurs(az)) | set(diviseurs(zz)) | set(diviseurs(max(nn, 1)))
    re = im = 0.0
    for d in ens:
        th = 2 * math.pi * d * PHI
        re += H_d(d) * math.cos(th)
        im += H_d(d) * math.sin(th)
    return re * re + im * im


phis = np.array([phi_corrige(int(A[i]), int(ZS[i]), int(N[i])) for i in range(len(ZS))])
for nom, rv in (("residuel", r), ("|residuel|", np.abs(r))):
    corr = np.corrcoef(np.log10(phis + 1e-9), rv)[0, 1]
    print(f"  corr log10(Phi) vs {nom:10s} : r = {corr:+.3f}")

print("\n" + "=" * 78)
print("SYNTHESE (A>=16, ou le SEMF est valide)")
for nom, Bp, mp in (("Litterature (6 params)", B_lit, m_lit),
                    ("Harmonique (0 param)  ", B_har, m_har),
                    ("+ coquille (2 params) ", B_shell, m_shell)):
    rms = np.sqrt(np.mean((B_MEAS - Bp)[MASQ_LOURD] ** 2))
    ec = np.abs(mp - M_U) / M_U * 100.0
    print(f"  {nom}: RMS B = {rms:6.3f} MeV | ecart moyen masses = {ec[MASQ_LOURD].mean():6.4f} %")
print("=" * 78)
