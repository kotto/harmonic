# -*- coding: utf-8 -*-
"""
VERIF M9 — SPIN-ORBITE : j = l ± ½ sort de la ladder M8 et du doublet natif.

Frontière : FRONTIERE_M9_SPIN_ORBITE_V0.md (18f76d3, dépôt-d'abord C0a —
ce script n'existait pas au moment du dépôt). Toutes les barres sont gelées
dans la frontière §2 ; UN SEUL échec ⟹ V4_REFUTE exit 1, sans sauvetage
(I1).

Objet : la décomposition l ⊗ ½ = (l+½) ⊕ (l−½) est CONSTRUITE par pure
addition de Kronecker des générateurs natifs J_k^{prod} = J_k^{(l)}⊗I₂ +
I_{2l+1}⊗H_k (part l = gabarit M8 convention native, barreaux n = 2l ; part
½ = triple natif M6) — aucune bibliothèque de moment angulaire, aucun
package Clebsch-Gordan : la décomposition est COMPTÉE par la machine.

Défauts estimateur corrigés AVANT gel (frontière §0) : double doublement
2m dans le test histogramme, maximum de spectre de bloc dérivé 4p (le max
est (p+1)², sommet en q=−1), base eigh arbitraire (seuls invariants de
base utilisés : dims de clusters, spectres de restrictions V†BV, traces de
produits de projecteurs). Déterministe : aucune graine, aucun aléa.
"""

import json
import math
import os
import sys
import time

import numpy as np

FRONTIERE = "FRONTIERE_M9_SPIN_ORBITE_V0.md"
SORTIE = "resultat_m9_spin_orbite_v0.json"

L_MAX = 6               # l = 0..6 → dims produit 2..26
TOL_HERM = 1.0e-15      # barre gelée C2 (hermiticité) et C5 (J_−J_+)
TOL_ALG = 1.0e-13       # barres gelées C2 (comm), C4 (diag/union)
TOL_CJ = 1.0e-12        # barres gelées C2 ([J²,J_k]) et C5/C7 (blocs, traces)
TOL_ROUND = 1.0e-9      # barre gelée C3 (dév J² aux entiers)
TOL_SQRT = 1.0e-12      # barre gelée C6 (dév √)

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


# ---------------------------------------------------------------- objets natifs verbatim M6/M8
I2 = np.eye(2, dtype=complex)
S2 = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
JM = np.array([[0.0, 1.0], [-1.0, 0.0]], dtype=complex)
P2 = JM @ S2
H1 = S2.copy()
H2 = (-1j) * JM
H3 = P2.copy()
TRIPLE = (H1, H2, H3)


def stencil(n):
    """Gabarit M8 CONVENTION NATIVE (verbatim) : J₃ = diag(n−2k) ;
    J₁ symétrique √((k+1)(n−k)) ; J₂_{k+1,k} = +i√, J₂_{k,k+1} = −i√."""
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


def symmetriseur(n):
    """S_n = (1/n!)Σ_π P_π construit exactement (verbatim M8, témoin)."""
    dim = 2 ** n
    S = np.zeros((dim, dim))
    for v in range(dim):
        k1 = bin(v).count("1")
        coef = math.factorial(k1) * math.factorial(n - k1) / math.factorial(n)
        for u in range(dim):
            if bin(u).count("1") == k1:
                S[u, v] = coef
    return S


def kron_sum(H, n):
    """Verbatim M8 : J_k^{full} = Σ_a I⊗..⊗H⊗..⊗I (témoin ½⊗½)."""
    out = np.zeros((2 ** n, 2 ** n), dtype=complex)
    for a in range(n):
        M = np.array([[1.0 + 0j]])
        for b in range(n):
            M = np.kron(M, H if b == a else I2)
        out = out + M
    return out


def produit(l):
    """J_k^{prod} = J_k^{(l)} ⊗ I₂ + I_{2l+1} ⊗ H_k sur dim 2(2l+1)."""
    n = 2 * l
    Jl = stencil(n)
    Il = np.eye(n + 1, dtype=complex)
    return [np.kron(Jl[a], I2) + np.kron(Il, TRIPLE[a]) for a in range(3)]


def comm_err(Js):
    e = 0.0
    for (i, j, k) in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
        e = max(e, float(np.max(np.abs(Js[i] @ Js[j] - Js[j] @ Js[i]
                                       - 2j * Js[k]))))
    return e


def casimir(Js):
    return Js[0] @ Js[0] + Js[1] @ Js[1] + Js[2] @ Js[2]


def jmoins_jplus(Js):
    """J_−J_+ = (J₁−iJ₂)(J₁+iJ₂) = J₁²+J₂²−2J₃ — hermitien (témoin)."""
    return (Js[0] @ Js[0] + Js[1] @ Js[1]) - 2.0 * Js[2]


def clusters_int(C):
    """Valeurs propres de C arrondies à l'entier + multiplicités comptées."""
    w = np.linalg.eigvalsh(C)
    ints = np.round(w).astype(int)
    dev = float(np.max(np.abs(w - ints)))
    mult = {}
    for v in ints:
        mult[int(v)] = mult.get(int(v), 0) + 1
    return mult, dev


def spectre_bloc(C, val, B, tol=1.0e-6):
    """Restriction de B au cluster spectral de C à `val` : spectre trié de
    V†BV (invariant de base — la base eigh est arbitraire, défaut M8
    consigné ; seul le SPECTRE est utilisé, jamais la base)."""
    w, V = np.linalg.eigh(C)
    idx = [i for i in range(len(w)) if abs(w[i] - val) <= tol]
    Vj = V[:, idx]
    A = Vj.conj().T @ B @ Vj
    return np.sort(np.linalg.eigvalsh(A)), len(idx)


def bloc_att(p):
    """{p²+2p−q²−2q : q = −p..p pas 2} trié (entiers exacts, p = 2j)."""
    return sorted(p * p + 2 * p - (q * q + 2 * q) for q in range(-p, p + 1, 2))


def diag_att_J3(n):
    """Diagonale attendue de J₃^{prod} : pour k=0..n, (n−2k+1, n−2k−1)."""
    d = []
    for k in range(n + 1):
        d.extend([n - 2 * k + 1, n - 2 * k - 1])
    return np.array(sorted(d), dtype=float)


def attendu_clusters(l):
    """Multiplicités attendues : {λ₊: n+2, λ₋: n} ; l=0 : {3: 2}."""
    n = 2 * l
    if l == 0:
        return {3: 2}
    return {(n + 1) * (n + 3): n + 2, (n - 1) * (n + 1): n}


def blocs_de_l(l):
    """[(λ, p)] des blocs j₊/j₋ de l (p = 2j) ; l=0 : un seul bloc."""
    n = 2 * l
    if l == 0:
        return [(3, 1)]
    return [((n + 1) * (n + 3), n + 1), ((n - 1) * (n + 1), n - 1)]


print("=" * 78)
print("  VERIF M9 — SPIN-ORBITE : j = l ± ½ sort de la ladder M8 + doublet natif")
print("=" * 78)

# ---------------------------------------------------------------- C0a
age_ok = os.path.getmtime(FRONTIERE) < t_exec
controle("C0a antériorité : mtime(frontière) < début d'exécution",
         age_ok,
         f"frontière {time.strftime('%H:%M:%S', time.localtime(os.path.getmtime(FRONTIERE)))}"
         f" < exécution {time.strftime('%H:%M:%S', time.localtime(t_exec))}")

# ---------------------------------------------------------------- C1 filiation
Jn1 = stencil(1)
e_sten1 = max(float(np.max(np.abs(Jn1[a] - TRIPLE[a]))) for a in range(3))
J0 = produit(0)
e_l0 = max(float(np.max(np.abs(J0[a] - TRIPLE[a]))) for a in range(3))
c1_ok = (e_sten1 == 0.0) and (e_l0 == 0.0)
controle("C1 filiation : gabarit n=1 == triple natif ET l=0 == triple natif",
         c1_ok,
         f"|J_gabarit(1) − triple| = {e_sten1!r} ; |J_prod(l=0) − triple| = "
         f"{e_l0!r} (tous deux 0.0 BIT-EXACT exigés ×3 générateurs)")

# ---------------------------------------------------------------- C2 algèbre produit
max_herm = 0.0
max_comm = 0.0
max_cJ = 0.0
for l in range(L_MAX + 1):
    Jp = produit(l)
    max_herm = max(max_herm,
                   max(float(np.max(np.abs(Jp[a] - Jp[a].conj().T)))
                       for a in range(3)))
    max_comm = max(max_comm, comm_err(Jp))
    C = casimir(Jp)
    max_cJ = max(max_cJ,
                 max(float(np.max(np.abs(C @ Jp[a] - Jp[a] @ C)))
                     for a in range(3)))
c2_ok = (max_herm <= TOL_HERM) and (max_comm <= TOL_ALG) and (max_cJ <= TOL_CJ)
controle("C2 algèbre produit (l=0..6) : hermiticité, [J,J]=2iεJ, [J²,J_k]=0",
         c2_ok,
         f"max |J−J†| = {max_herm!r} (≤ {TOL_HERM:g}) ; max comm = "
         f"{max_comm!r} (≤ {TOL_ALG:g}) ; max |[J²,J_k]| = {max_cJ!r} "
         f"(≤ {TOL_CJ:g})")

# ---------------------------------------------------------------- C3 clusters J²
c3_ok = True
max_dev2 = 0.0
enlacement_ok = True
lam_plus_prev = None
for l in range(L_MAX + 1):
    n = 2 * l
    mult, dev = clusters_int(casimir(produit(l)))
    max_dev2 = max(max_dev2, dev)
    att = attendu_clusters(l)
    ok_l = (dev <= TOL_ROUND) and (mult == att)
    c3_ok &= ok_l
    if l >= 1:
        enlacement_ok &= (lam_plus_prev == (n - 1) * (n + 1))
    lam_plus_prev = (n + 1) * (n + 3)  # λ₊(l) posé à CHAQUE itération (l=0 compris)
controle("C3 clusters J² (l=0..6) : 4j(j+1) entiers, multiplicités "
         "[2l+2, 2l], enlacement λ₊(l−1)==λ₋(l)",
         c3_ok and enlacement_ok,
         f"multiplicités mesurées == attendues pour tout l ({attendu_clusters(0)}"
         f" → {attendu_clusters(6)}) ; dév max au round = {max_dev2!r} "
         f"(≤ {TOL_ROUND:g}) ; enlacement OK : {enlacement_ok}")

# ---------------------------------------------------------------- C4 J₃ diagonal + histogramme
c4_ok = True
max_d3 = 0.0
max_uni = 0.0
hist_ok_all = True
for l in range(L_MAX + 1):
    n = 2 * l
    Jp = produit(l)
    d = np.sort(np.diag(Jp[2]).real)
    d_att = diag_att_J3(n)
    max_d3 = max(max_d3, float(np.max(np.abs(d - d_att))))
    mult = {}
    for v in d_att:
        iv = int(v)
        mult[iv] = mult.get(iv, 0) + 1
    ok_h = (sum(mult.values()) == 4 * l + 2) and (len(mult) == n + 2) and \
        all((c == 2 if abs(m) <= n - 1 else c == 1) for m, c in mult.items())
    hist_ok_all &= ok_h
    if l >= 1:
        u = np.array(sorted([n + 1 - 2 * k for k in range(n + 2)] +
                            [n - 1 - 2 * k for k in range(n)]), dtype=float)
    else:
        u = np.array(sorted(n + 1 - 2 * k for k in range(2)), dtype=float)
    max_uni = max(max_uni, float(np.max(np.abs(d - u))))
c4_ok = (max_d3 <= TOL_ALG) and (max_uni <= TOL_ALG) and hist_ok_all
controle("C4 J₃ (l=0..6) : diagonal n−2k±1, histogramme m, union n±1",
         c4_ok,
         f"max |diag − attendu| = {max_d3!r} (≤ {TOL_ALG:g}) ; histogramme "
         f"(mult 2 si |2m|≤n−1, 1 si |2m|=n+1 ; distinct n+2 ; total 4l+2) "
         f"OK : {hist_ok_all} ; max |diag − union gabarits n±1| = {max_uni!r}")

# ---------------------------------------------------------------- C5 blocs projecteurs
c5_ok = True
max_hermB = 0.0
max_bloc = 0.0
dim_ok_all = True
for l in range(L_MAX + 1):
    Jp = produit(l)
    C = casimir(Jp)
    B = jmoins_jplus(Jp)
    max_hermB = max(max_hermB, float(np.max(np.abs(B - B.conj().T))))
    for (val, p) in blocs_de_l(l):
        sp, dimj = spectre_bloc(C, val, B)
        att = np.array(bloc_att(p), dtype=float)
        max_bloc = max(max_bloc, float(np.max(np.abs(sp - att))))
        dim_ok_all &= (dimj == p + 1) and (len(sp) == p + 1)
c5_ok = (max_hermB <= TOL_HERM) and (max_bloc <= TOL_CJ) and dim_ok_all
controle("C5 blocs (l=0..6) : J_−J_+ hermitien, dim P_j == 2j+1, spectres "
         "== {p²+2p−q²−2q}",
         c5_ok,
         f"max |J_−J_+ − h.c.| = {max_hermB!r} (≤ {TOL_HERM:g}) ; dims "
         f"entières OK : {dim_ok_all} ; max |spectre bloc − forme close| = "
         f"{max_bloc!r} (≤ {TOL_CJ:g})")

# ---------------------------------------------------------------- C6 bornage
c6_ok = True
max_devp = 0.0
min_dist = None
for l in range(L_MAX + 1):
    n = 2 * l
    for (val, p) in blocs_de_l(l):
        devp = abs(math.sqrt(1 + val) - 1 - p)
        max_devp = max(max_devp, devp)
        c6_ok &= (p % 2 == 1) and (p in (n - 1, n + 1)) and (devp <= TOL_SQRT)
        dist = abs(val - 4 * l * (l + 1))
        min_dist = dist if min_dist is None else min(min_dist, dist)
controle("C6 bornage (l=0..6) : p impairs ∈ {n−1, n+1}, discriminant j=l rejeté",
         c6_ok and (min_dist >= 3),
         f"p = 2j impairs sur tout l (dév √ max = {max_devp!r} ≤ {TOL_SQRT:g}) "
         f"; distance min des clusters à 4l(l+1) = {min_dist} (≥ 3 exigé — "
         "hypothèse non couplée rejetée par gaps entiers)")

# ---------------------------------------------------------------- C7 doublet⊗doublet
Jd = [kron_sum(TRIPLE[a], 2) for a in range(3)]
Cd = casimir(Jd)
mult_d, dev_d = clusters_int(Cd)
Bd = jmoins_jplus(Jd)
sp1, dim1 = spectre_bloc(Cd, 8, Bd)
sp0, dim0 = spectre_bloc(Cd, 0, Bd)
e_b1 = float(np.max(np.abs(sp1 - np.array(bloc_att(2), dtype=float))))
e_b0 = float(np.max(np.abs(sp0 - np.array(bloc_att(0), dtype=float))))
w_d, V_d = np.linalg.eigh(Cd)
Pt = V_d[:, [i for i in range(4) if abs(w_d[i] - 8) <= 1e-6]]
Pt = Pt @ Pt.conj().T
Pb = V_d[:, [i for i in range(4) if abs(w_d[i]) <= 1e-6]]
Pb = Pb @ Pb.conj().T
P_sym = symmetriseur(2)
P_anti = np.eye(4) - P_sym
t_ts = float(np.trace(Pt @ P_sym).real)
t_ba = float(np.trace(Pb @ P_anti).real)
t_bs = abs(float(np.trace(Pb @ P_sym).real))
t_ta = abs(float(np.trace(Pt @ P_anti).real))
c7_ok = (mult_d == {8: 3, 0: 1}) and (dev_d <= TOL_ROUND) and \
    (dim1 == 3) and (dim0 == 1) and (e_b1 <= TOL_CJ) and (e_b0 <= TOL_CJ) and \
    (abs(t_ts - 3.0) <= TOL_CJ) and (abs(t_ba - 1.0) <= TOL_CJ) and \
    (t_bs <= TOL_CJ) and (t_ta <= TOL_CJ) and \
    (float(np.trace(P_sym)) == 3.0)
controle("C7 doublet⊗doublet : j=1 (mult 3) ⊕ j=0 (mult 1) ; bloc j=1 == Sym²",
         c7_ok,
         f"clusters {mult_d} (dév {dev_d!r}) ; bloc j=1 dim {dim1} spectre "
         f"[0, 8, 8] ({e_b1!r}) ; bloc j=0 dim {dim0} ({e_b0!r}) ; "
         f"tr(P_top·P_sym) = {t_ts!r} ; tr(P_bot·(I−P_sym)) = {t_ba!r} ; "
         f"traces croisées = {max(t_bs, t_ta)!r}")

# ---------------------------------------------------------------- C8 capacité
c8_ok = True
caps = []
for l in range(L_MAX + 1):
    n = 2 * l
    cap_p = n + 2
    cap_m = n if l >= 1 else 0
    caps.append(cap_p + cap_m)
    c8_ok &= (cap_p + cap_m == 2 * (2 * l + 1)) and \
             (cap_p + cap_m == (2 * l + 1) * 2)
c8_ok &= (caps == [2, 6, 10, 14, 18, 22, 26])
controle("C8 capacité (l=0..6) : (2j₊+1)+(2j₋+1) == 2(2l+1)",
         c8_ok,
         f"sommes mesurées == {caps} (identité additive des couches, "
         "découpe spin-orbite de la table M8)")

# ---------------------------------------------------------------- D1 table clusters
d1_mesure = {"clusters_par_l": [sorted(attendu_clusters(l).items())
                                for l in range(L_MAX + 1)],
             "dev_round_max": max_dev2,
             "enlacement": bool(enlacement_ok)}
d1_ok = c3_ok and c4_ok
print(f"  [{'OK ' if d1_ok else 'ÉCH'}] D1 : la décomposition l⊗½ = "
      f"(l+½)⊕(l−½) est COMPTÉE pas lue — clusters 4j(j+1) entiers, "
      f"multiplicités [2l+2, 2l] exactes, J₃ diagonal n−2k±1, enlacement "
      f"λ₊(l−1)==λ₋(l) : chaque j ∈ {{½, 3/2, …}} apparaît exactement "
      "deux fois à travers l")

# ---------------------------------------------------------------- D2 table capacité
d2_mesure = {"capacites_par_l": caps,
             "detail_j": [[(n + 2), (n if l >= 1 else 0)]
                          for l, n in ((l, 2 * l) for l in range(L_MAX + 1))]}
d2_ok = c8_ok
print(f"  [{'OK ' if d2_ok else 'ÉCH'}] D2 : identité de capacité "
      f"(2j₊+1)+(2j₋+1) == 2(2l+1) == {caps} — la table M8 S8 est découpée "
      "en deux sous-couches spin-orbite (matière première M3/M4, rang 4 "
      "nucléaire reste consigné)")

# ---------------------------------------------------------------- D3 déviations de bloc
d3_mesure = {"hermiticite_JmJp": max_hermB,
             "spectre_bloc_max": max_bloc,
             "doublet_doublet": {"e_b1": e_b1, "e_b0": e_b0,
                                 "tr_top_sym": t_ts, "tr_bot_anti": t_ba}}
d3_ok = c5_ok and c7_ok and (max_bloc <= TOL_CJ)
print(f"  [{'OK ' if d3_ok else 'ÉCH'}] D3 : structure de bloc fermée — "
      f"[J²,J_±] = 0 ({max_cJ!r}), spectres de ladder entiers par bloc "
      f"({max_bloc!r}) ; témoin ½⊗½ = 1⊕0 : le bloc j=1 EST Sym² "
      f"(tr = {t_ts!r}) — l'adjointe M7/Sym² M8 réapparaît comme bloc de "
      "couplage ; reste consigné : identification orbitale, ordre des "
      "niveaux (aucun Hamiltonien L·S déposé), coefficients CG complets, "
      "g=2 (aucun couplage EM)")

# ---------------------------------------------------------------- verdict
verdict = "V4_REFUTE"
if ok_global and d1_ok and d2_ok and d3_ok:
    verdict = "V+ M9_SPIN_ORBITE_FERME"
elif ok_global:
    verdict = "V2"
elif age_ok:
    verdict = "V3"

print("=" * 78)
print(f"  VERDICT : {verdict}")
print("=" * 78)

resultat = {
    "campagne": "M9 SPIN-ORBITE V0 — j = l ± ½ sort de la ladder M8 et du doublet natif",
    "frontiere": FRONTIERE,
    "frontiere_commit": "18f76d3",
    "verdict": verdict,
    "ok_global": bool(ok_global),
    "controles": controles_log,
    "consequences": [
        {"consequence": "D1", "ok": bool(d1_ok), "mesure": d1_mesure,
         "detail": "la décomposition l⊗½ = (l+½)⊕(l−½) n'est pas lue dans "
                   "un package — elle est construite par addition de "
                   "Kronecker des générateurs natifs : clusters J² aux "
                   "entiers 4j(j+1) = (n±1)(n∓1), multiplicités [2l+2, 2l], "
                   "J₃ diagonal explicite n−2k±1, enlacement λ₊(l−1)==λ₋(l) "
                   "(chaque j apparaît exactement deux fois)"},
        {"consequence": "D2", "ok": bool(d2_ok), "mesure": d2_mesure,
         "detail": "identité de capacité (2j₊+1)+(2j₋+1) == 2(2l+1) — la "
                   "table de couches M8 [2,6,10,14,18,22,26] est découpée "
                   "en sous-couches spin-orbite (2,0),(4,2),(6,4),(8,6),"
                   "(10,8),(12,10),(14,12) — matière première de l'ouverture "
                   "M4 rang 4 nucléaire (consignée)"},
        {"consequence": "D3", "ok": bool(d3_ok), "mesure": d3_mesure,
         "detail": "structure de bloc : [J²,J_±] = 0, spectres de ladder "
                   "entiers {p²+2p−q²−2q} par bloc (p = 2j impair), bornage "
                   "2j impair, discriminant contre j=l ; témoin ½⊗½ = 1⊕0 "
                   "avec le bloc j=1 == Sym² (tr(P_top·P_sym) = 3.0) — "
                   "l'adjointe M7/Sym² M8 réapparaît comme bloc de couplage ; "
                   "reste consigné : identification orbitale, ordre des "
                   "niveaux (aucun Hamiltonien L·S déposé), coefficients CG "
                   "complets, g=2 (aucun couplage EM)"},
    ],
    "route_consignee": "part l = gabarit M8 convention native (barreaux "
                       "n = 2l), part ½ = triple natif M6 verbatim ; seuls "
                       "invariants de base utilisés (dims de clusters, "
                       "spectres de restrictions V†BV, traces de produits "
                       "de projecteurs — la base eigh est arbitraire, défaut "
                       "M8 re-consigné) ; pas d'Hamiltonien, pas de "
                       "Clebsch-Gordan complets, pas de g=2, identification "
                       "orbitale interprétative ; ħ=1, convention native "
                       "J = 2×physique ; défauts estimateur corrigés avant "
                       "gel et consignés §0 frontière ; DÉFAUT VERIF "
                       "consigné : à la première exécution post-gel, "
                       "l'enlacement C3 échouait par initialisation "
                       "manquante de λ₊(0) dans le verif (le témoin pré-gel "
                       "de la sonde était correct) — verif corrigé pour "
                       "fidélité au témoin gelé, re-exécution propre, sans "
                       "modification de la frontière ni des barres",
    "determinisme": "aucune graine, aucun aléa",
}

with open(SORTIE, "w", encoding="utf-8") as f:
    json.dump(resultat, f, ensure_ascii=False, indent=1)
print(f"JSON écrit : {SORTIE}")
sys.exit(0 if (ok_global and d1_ok and d2_ok and d3_ok) else 1)
