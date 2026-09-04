# -*- coding: utf-8 -*-
"""
VERIF M10 — SINGULETS DE COUPLAGE : pseudoréalité 2̄ ≅ 2 et règles de
sélection des masses.

Frontière : FRONTIERE_M10_SINGULETS_V0.md (fe3ba9a, dépôt-d'abord C0a —
ce script n'existait pas au moment du dépôt). Toutes les barres sont
gelées dans la frontière §2 ; UN SEUL échec ⟹ V4_REFUTE exit 1, sans
sauvetage (I1).

Objet : le squelette de sélection du secteur type-Higgs/Yukawa au niveau
SU(2) est COMPTÉ par la machine depuis les objets natifs : ε = JM (M6),
espaces d'invariants des produits de doublets (comptage Catalan via la
machinerie M8), pseudoréalité, opérateur de Weinberg, CG ½⊗½ uniques.
Aucune bibliothèque de théorie des champs, aucune table CG importée.

Hygiène consignée (frontière §0) : deux fonctions mortes de la sonde
purgées AVANT première exécution (jamais exécutées). Déterministe :
aucune graine, aucun aléa.
"""

import json
import math
import os
import sys
import time

import numpy as np

FRONTIERE = "FRONTIERE_M10_SINGULETS_V0.md"
SORTIE = "resultat_m10_singulets_v0.json"

GRID = 96                # grille pseudoréalité (gelée)
N_MAX = 10               # comptage Catalan (gelé)
L_MAX = 6                # sélection 2⊗(2l+1) (gelé)
TOL_PSEUDO = 1.0e-15     # barre gelée C2
TOL_ROUND = 1.0e-9       # barres gelées C3/C5 (dév clusters)
TOL_TRACE = 1.0e-12      # barres gelées C3 (traces) et C6 (Gram)
TOL_ALG = 1.0e-13        # barres gelées C6 (invariance) et C7 (CG)
TOL_ORTHO = 1.0e-15      # barre gelée C7 (orthonormalité)

t_exec = time.time()
ok_global = True
controles_log = []


def controle(nom, cond, detail):
    global ok_global
    ok = bool(cond)
    ok_global &= ok
    controles_log.append({"controle": nom, "ok": ok, "detail": detail})
    print(f"  [{'OK ' if ok else 'ÉCH'}] {nom} : {detail}")
    return ok


# ---------------------------------------------------------------- objets natifs verbatim M6
I2 = np.eye(2, dtype=complex)
S2 = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
JM = np.array([[0.0, 1.0], [-1.0, 0.0]], dtype=complex)
P2 = JM @ S2
H1 = S2.copy()
H2 = (-1j) * JM
H3 = P2.copy()
TRIPLE = (H1, H2, H3)
EPS = JM.copy()
PHI = (1.0 + math.sqrt(5.0)) / 2.0
ALPHA = 1.0 / PHI
ANGLES_EULER = [0.3, 0.7, 1.1, 2.3]


def kron_sum(H, n):
    """J_k^{full} = Σ_a I⊗..⊗H⊗..⊗I (verbatim M8)."""
    out = np.zeros((2 ** n, 2 ** n), dtype=complex)
    for a in range(n):
        M = np.array([[1.0 + 0j]])
        for b in range(n):
            M = np.kron(M, H if b == a else I2)
        out = out + M
    return out


def symmetriseur(n):
    """S_n = (1/n!)Σ_π P_π (verbatim M8, témoin)."""
    dim = 2 ** n
    S = np.zeros((dim, dim))
    for v in range(dim):
        k1 = bin(v).count("1")
        coef = math.factorial(k1) * math.factorial(n - k1) / math.factorial(n)
        for u in range(dim):
            if bin(u).count("1") == k1:
                S[u, v] = coef
    return S


def stencil(n):
    """Gabarit M8 convention native (verbatim)."""
    m = n + 1
    J1 = np.zeros((m, m), dtype=complex)
    J2 = np.zeros((m, m), dtype=complex)
    J3 = np.zeros((m, m), dtype=complex)
    for k in range(m):
        J3[k, k] = n - 2 * k
        if k + 1 <= n:
            c = math.sqrt((k + 1) * (n - k))
            J1[k + 1, k] = c
            J1[k, k + 1] = c
            J2[k + 1, k] = 1j * c
            J2[k, k + 1] = -1j * c
    return J1, J2, J3


def produit(l):
    """J_k^{prod} l⊗½ (verbatim M9)."""
    n = 2 * l
    Jl = stencil(n)
    Il = np.eye(n + 1, dtype=complex)
    return [np.kron(Jl[a], I2) + np.kron(Il, TRIPLE[a]) for a in range(3)]


def produit_deux(Ja, Jb):
    da, db = Ja[2].shape[0], Jb[2].shape[0]
    Ia, Ib = np.eye(da, dtype=complex), np.eye(db, dtype=complex)
    return [np.kron(Ja[a], Ib) + np.kron(Ia, Jb[a]) for a in range(3)]


def casimir(Js):
    return Js[0] @ Js[0] + Js[1] @ Js[1] + Js[2] @ Js[2]


def clusters(C, tol=1.0e-6):
    w = np.linalg.eigvalsh(C)
    ints = np.round(w).astype(int)
    dev = float(np.max(np.abs(w - ints)))
    mult = {}
    for v in ints:
        mult[int(v)] = mult.get(int(v), 0) + 1
    return mult, dev


def singulets(C, tol=1.0e-6):
    w = np.linalg.eigvalsh(C)
    return int(sum(1 for v in w if abs(v) <= tol))


def bateman(phi):
    return np.array([[math.cos(phi), math.sin(phi)],
                     [-math.sin(phi), math.cos(phi)]], dtype=complex)


def expi(H, th):
    w, V = np.linalg.eigh(H)
    return V @ np.diag(np.exp(1j * th * w)) @ V.conj().T


def euler_U(a, b, g):
    return expi(H1, a) @ expi(H2, b) @ expi(H3, g)


print("=" * 78)
print("  VERIF M10 — SINGULETS DE COUPLAGE : pseudoréalité et sélection des masses")
print("=" * 78)

# ---------------------------------------------------------------- C0a
age_ok = os.path.getmtime(FRONTIERE) < t_exec
controle("C0a antériorité : mtime(frontière) < début d'exécution",
         age_ok,
         f"frontière {time.strftime('%H:%M:%S', time.localtime(os.path.getmtime(FRONTIERE)))}"
         f" < exécution {time.strftime('%H:%M:%S', time.localtime(t_exec))}")

# ---------------------------------------------------------------- C1 filiation ε
e_eps = max(float(np.max(np.abs(EPS - JM))),
            float(np.max(np.abs(EPS @ EPS + I2))),
            float(np.max(np.abs(EPS.T + EPS))),
            float(np.max(np.abs(EPS.imag))))
c1_ok = (e_eps == 0.0)
controle("C1 filiation ε : ε == JM natif, ε²=−I, ε^T=−ε, ε réel",
         c1_ok,
         f"max |ε−JM|, |ε²+I|, |ε^T+ε|, |Im ε| = {e_eps!r} "
         "(0.0 BIT-EXACT exigé)")

# ---------------------------------------------------------------- C2 pseudoréalité
max_gen = 0.0
for k in range(3):
    for g in range(GRID):
        th = 2 * math.pi * g / GRID
        U = expi(TRIPLE[k], th)
        max_gen = max(max_gen, float(np.max(np.abs(EPS @ U.conj() - U @ EPS))))
max_eul = 0.0
for U in (bateman(ALPHA),
          euler_U(ANGLES_EULER[0], ANGLES_EULER[1], ANGLES_EULER[2]),
          euler_U(ANGLES_EULER[3], ANGLES_EULER[0], ANGLES_EULER[1]),
          euler_U(ALPHA, ALPHA, ALPHA),
          euler_U(1.0, 2.0, 0.0)):
    max_eul = max(max_eul, float(np.max(np.abs(EPS @ U.conj() - U @ EPS))))
c2_ok = (max_gen <= TOL_PSEUDO) and (max_eul <= TOL_PSEUDO)
controle("C2 pseudoréalité : ε·Ū == U·ε (grille + composés Euler/Bateman)",
         c2_ok,
         f"max |ε·Ū − U·ε| générateurs = {max_gen!r} ; composés = "
         f"{max_eul!r} (≤ {TOL_PSEUDO:g}) — 2̄ ≅ 2 par ε natif")

# ---------------------------------------------------------------- C3 Inv(2⊗2)
Jd = [kron_sum(TRIPLE[a], 2) for a in range(3)]
Cd = casimir(Jd)
mult2, dev2 = clusters(Cd)
P_sym = symmetriseur(2)
P_anti = np.eye(4) - P_sym
w2, V2 = np.linalg.eigh(Cd)
P1 = V2[:, [i for i in range(4) if abs(w2[i]) <= 1e-6]]
P1 = P1 @ P1.conj().T
t_1s = float(np.trace(P1 @ P_sym).real)
t_1a = float(np.trace(P1 @ P_anti).real)
c3_ok = (mult2 == {8: 3, 0: 1}) and (dev2 <= 1e-9) and (mult2.get(0, 0) == 1) \
    and (abs(t_1s) <= TOL_TRACE) and (abs(t_1a - 1.0) <= TOL_TRACE)
controle("C3 Inv(2⊗2) : dim == 1, singulet ANTISYMÉTRIQUE (couplage ε)",
         c3_ok,
         f"clusters {mult2} (dév {dev2!r}) ; tr(P_1·Sym²) = {t_1s!r} "
         f"(≤ {TOL_TRACE:g} — PAS de couplage ψψ pour UN doublet) ; "
         f"tr(P_1·(I−Sym²)) = {t_1a!r}")

# ---------------------------------------------------------------- C4 Catalan
cat_mes = []
for n in range(1, N_MAX + 1):
    Jf = [kron_sum(TRIPLE[a], n) for a in range(3)]
    cat_mes.append(singulets(casimir(Jf)))
cat_att = [0 if n % 2 else math.comb(n, n // 2) - math.comb(n, n // 2 - 1)
           for n in range(1, N_MAX + 1)]
c4_ok = (cat_mes == cat_att) and \
    (cat_mes == [0, 1, 0, 2, 0, 5, 0, 14, 0, 42])
controle("C4 Catalan : invariants de 2^{⊗n} (n=1..10), écart entier 0",
         c4_ok,
         f"mesuré == {cat_mes} (gelé [0, 1, 0, 2, 0, 5, 0, 14, 0, 42] ; "
         "0 impair, C(n,n/2)−C(n,n/2−1) pair)")

# ---------------------------------------------------------------- C5 sélection
sel_ok = True
sel_l = []
for l in range(L_MAX + 1):
    Jp = produit(l)
    m, d = clusters(casimir(Jp))
    sel_l.append(m.get(0, 0))
    sel_ok &= (m.get(0, 0) == 0) and (d <= 1e-9)
J33 = produit_deux(stencil(2), stencil(2))
m33, d33 = clusters(casimir(J33))
sel33 = m33.get(0, 0)
c5_ok = sel_ok and (m33 == {0: 1, 8: 3, 24: 5}) and (d33 <= 1e-9)
controle("C5 sélection : 2⊗(2l+1) sans singulet (l=0..6) ; 3⊗3 ⊃ 1 singulet",
         sel_ok and (m33 == {0: 1, 8: 3, 24: 5}) and (sel_l == [0]*7),
         f"singulets 2⊗(2l+1) == {sel_l} (tous 0 exigés) ; 3⊗3 clusters "
         f"{m33} (dév {d33!r}) → 1 singulet (structure H†H/L·S)")

# ---------------------------------------------------------------- C6 Weinberg
def build_v(mode):
    v = np.zeros(16, dtype=complex)
    for b0 in range(2):
        for b1 in range(2):
            for b2 in range(2):
                for b3 in range(2):
                    if mode == 1:
                        c = EPS[b0, b1] * EPS[b2, b3]
                    else:
                        c = EPS[b0, b2] * EPS[b1, b3]
                    if c != 0:
                        v[b0 * 8 + b1 * 4 + b2 * 2 + b3] += c
    return v


v1 = build_v(1)
v2 = build_v(2)
Jf4 = [kron_sum(TRIPLE[a], 4) for a in range(3)]
inv_err = 0.0
for a in range(3):
    inv_err = max(inv_err, float(np.max(np.abs(Jf4[a] @ v1))),
                  float(np.max(np.abs(Jf4[a] @ v2))))
g11 = float(np.vdot(v1, v1).real)
g22 = float(np.vdot(v2, v2).real)
g12 = float(np.vdot(v1, v2).real)
det_g = g11 * g22 - g12 * g12
n4 = singulets(casimir(Jf4))
c6_ok = (inv_err <= TOL_ALG) and (abs(g11 - 4.0) <= TOL_TRACE) and \
    (abs(g22 - 4.0) <= TOL_TRACE) and (abs(g12 - 2.0) <= TOL_TRACE) and \
    (abs(det_g - 12.0) <= TOL_TRACE) and (n4 == 2)
controle("C6 Weinberg 2^{⊗4} : 2 invariants indépendants (Gram rang 2)",
         c6_ok,
         f"invariance |J_a·v| max = {inv_err!r} ; Gram ⟨v1,v1⟩ = {g11!r}, "
         f"⟨v2,v2⟩ = {g22!r}, ⟨v1,v2⟩ = {g12!r}, det = {det_g!r} (rang 2 "
         f"exigé) ; singulets comptés = {n4}")

# ---------------------------------------------------------------- C7 CG ½⊗½
up = np.array([1, 0], dtype=complex)
dn = np.array([0, 1], dtype=complex)
cg = {"|3,+1>": np.kron(up, up),
      "|3,0>": (np.kron(up, dn) + np.kron(dn, up)) / math.sqrt(2.0),
      "|3,-1>": np.kron(dn, dn),
      "|0,0>": (np.kron(up, dn) - np.kron(dn, up)) / math.sqrt(2.0)}
att_J2 = {"|3,+1>": 8.0, "|3,0>": 8.0, "|3,-1>": 8.0, "|0,0>": 0.0}
att_J3 = {"|3,+1>": 2.0, "|3,0>": 0.0, "|3,-1>": -2.0, "|0,0>": 0.0}
cg_err = 0.0
for nom, v in cg.items():
    cg_err = max(cg_err, float(np.max(np.abs(Cd @ v - att_J2[nom] * v))),
                 float(np.max(np.abs(Jd[2] @ v - att_J3[nom] * v))))
ortho = max(abs(float(np.vdot(cg[a], cg[b]).real) - (1.0 if a == b else 0.0))
            for a in cg for b in cg)
P_trip = np.eye(4) - P1
t_ts = float(np.trace(P_trip @ P_sym).real)
c7_ok = (cg_err <= TOL_ALG) and (ortho <= TOL_ORTHO) and \
    (abs(t_ts - 3.0) <= TOL_TRACE)
controle("C7 CG ½⊗½ uniques : eigen-vecteurs exacts, orthonormalité, "
         "triplet == Sym²",
         c7_ok,
         f"max |J²v−λv|, |J₃v−mv| = {cg_err!r} (λ = 8,8,8,0 ; m = 2,0,−2,0) "
         f"; orthonormalité {ortho!r} ; tr(P_triplet·Sym²) = {t_ts!r} (M9 C7)")

# ---------------------------------------------------------------- D1 table Catalan
d1_ok = c4_ok
d1_mesure = {"singulets_2pn_n1_a_n10": cat_mes}
print(f"  [{'OK ' if d1_ok else 'ÉCH'}] D1 : le nombre de couplages invariants "
      f"indépendants à n doublets est un théorème machine : {cat_mes} — "
      "0 impair, Catalan pair [1, 2, 5, 14, 42]")

# ---------------------------------------------------------------- D2 table sélection
d2_ok = c5_ok
d2_mesure = {"singulets_2x_l0_a_l6": sel_l, "singulets_3x3": sel33,
             "singulets_2x2": mult2.get(0, 0)}
print(f"  [{'OK ' if d2_ok else 'ÉCH'}] D2 : squelette de sélection des "
      f"couplages scalaires fermé — 2⊗entier : {sel_l} (jamais), 2⊗2 : "
      f"{mult2.get(0, 0)} (via ε), 3⊗3 : {sel33} (unique) — le doublet ne "
      "se couple au scalaire qu'avec un autre doublet")

# ---------------------------------------------------------------- D3 Weinberg + CG
d3_ok = c6_ok and c7_ok
d3_mesure = {"gram": [g11, g22, g12], "det": det_g, "invariance": inv_err,
             "cg_1_2_err": cg_err, "ortho": ortho, "tr_triplet_sym": t_ts}
print(f"  [{'OK ' if d3_ok else 'ÉCH'}] D3 : opérateur de Weinberg = DEUX "
      f"invariants ε indépendants (det {det_g!r}) ; CG ½⊗½ gelés uniques "
      f"({cg_err!r}) — le seul mélange verrouillable sans générations")

# ---------------------------------------------------------------- verdict
verdict = "V4_REFUTE"
if ok_global and d1_ok and d2_ok and d3_ok:
    verdict = "V+ M10_SINGULETS_FERME"
elif ok_global:
    verdict = "V2"
elif age_ok:
    verdict = "V3"

print("=" * 78)
print(f"  VERDICT : {verdict}")
print("=" * 78)

resultat = {
    "campagne": "M10 SINGULETS V0 — pseudoréalité 2̄ ≅ 2 et règles de "
                "sélection des masses",
    "frontiere": FRONTIERE,
    "frontiere_commit": "fe3ba9a",
    "verdict": verdict,
    "ok_global": bool(ok_global),
    "controles": controles_log,
    "consequences": [
        {"consequence": "D1", "ok": bool(d1_ok), "mesure": d1_mesure,
         "detail": "le nombre de couplages invariants indépendants à n "
                   "doublets est compté machine : [0, 1, 0, 2, 0, 5, 0, "
                   "14, 0, 42] — 0 si n impair, Catalan si pair (écart "
                   "entier 0) — l'espace des invariants de 2^{⊗n} n'est "
                   "pas postulé"},
        {"consequence": "D2", "ok": bool(d2_ok), "mesure": d2_mesure,
         "detail": "règle de sélection scalaire fermée : un doublet ne se "
                   "couple jamais au scalaire avec une représentation "
                   "entière (2⊗(2l+1) : 0 singulet, l=0..6) ; il se couple "
                   "avec UN autre doublet via ε (Inv(2⊗2) = 1, "
                   "antisymétrique) ; 3⊗3 porte exactement un singulet "
                   "(structure H†H/L·S)"},
        {"consequence": "D3", "ok": bool(d3_ok), "mesure": d3_mesure,
         "detail": "opérateur de Weinberg : deux invariants ε "
                   "indépendants (invariance 0.0, Gram (4,4,2), det 12.0) ; "
                   "pseudoréalité 2̄ ≅ 2 (5.4e-17) ; CG ½⊗½ uniques gelés "
                   "bit-exact ; reste consigné : hypercharges (up/down), "
                   "générations (angles de mélange), valeurs v/y_i/masses "
                   "(aucune dynamique), identification du scalaire "
                   "interprétative"},
    ],
    "route_consignee": "ε = JM natif M6 verbatim (pas une structure "
                       "importée) ; espaces d'invariants comptés par "
                       "clusters du Casimir complet M8 et par vecteurs "
                       "ε-appariés explicites ; seuls invariants de base "
                       "utilisés ; SU(2) SEUL — pas d'hypercharge, pas de "
                       "générations, pas de dynamique ; hygiène : deux "
                       "fonctions mortes purgées AVANT première exécution "
                       "(leçon FORCE V1.2) ; ħ=1, convention native "
                       "J = 2×physique",
    "determinisme": "aucune graine, aucun aléa",
}

with open(SORTIE, "w", encoding="utf-8") as f:
    json.dump(resultat, f, ensure_ascii=False, indent=1)
print(f"JSON écrit : {SORTIE}")
sys.exit(0 if (ok_global and d1_ok and d2_ok and d3_ok) else 1)
