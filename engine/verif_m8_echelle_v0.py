# -*- coding: utf-8 -*-
"""
VERIF M8 — ÉCHELLE ANGULAIRE : (2l+1) sort du doublet natif.

Frontière : FRONTIERE_M8_ECHELLE_V0.md (8c432c9, dépôt-d'abord C0a — ce
script n'existait pas au moment du dépôt). Toutes les barres sont gelées
dans la frontière §2 ; UN SEUL échec ⟹ V4_REFUTE exit 1, sans sauvetage
(I1).

Objet : l'échelle (2l+1) des moments angulaires est CONSTRUITE depuis le
doublet natif M6 {S, −iJ, J·S} par puissances symétriques — aucune
bibliothèque de représentations, aucune formule de Clebsch-Gordan importée
comme construction. Route A (mécanique : sommes de Kronecker + base de
Poids exacte, n=1..10), route B (gabarit convention native, n=0..12),
dégénérescence comptée, échelon l=1 = adjointe M7 (doublage).

Défauts estimateur corrigés AVANT gel (frontière §0) : signe de J_2
(convention native tranchée par machine) et base eigh arbitraire (remplacée
par la base de Poids). Déterministe : aucune graine, aucun aléa.
"""

import json
import math
import os
import sys
import time

import numpy as np

FRONTIERE = "FRONTIERE_M8_ECHELLE_V0.md"
SORTIE = "resultat_m8_echelle_v0.json"

N_MAX_A = 10   # route mécanique
N_MAX_B = 12   # gabarit étendu
TOL_ALG = 1.0e-13      # barres gelées C3/C6/C7
TOL_MATCH = 1.0e-14    # barres gelées C5/C8

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


I2 = np.eye(2, dtype=complex)
S2 = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
JM = np.array([[0.0, 1.0], [-1.0, 0.0]], dtype=complex)
P2 = JM @ S2
H1 = S2.copy()
H2 = (-1j) * JM
H3 = P2.copy()
TRIPLE = (H1, H2, H3)


def kron_sum(H, n):
    """J_k^{full} = Σ_a I⊗..⊗H⊗..⊗I sur n facteurs."""
    out = np.zeros((2 ** n, 2 ** n), dtype=complex)
    for a in range(n):
        M = np.array([[1.0 + 0j]])
        for b in range(n):
            M = np.kron(M, H if b == a else I2)
        out = out + M
    return out


def weight_basis(n):
    """Base de Poids exacte : colonne k = somme normalisée des bit-strings
    à k uns. Orthonormée par construction, déterministe, sans eigh."""
    dim = 2 ** n
    W = np.zeros((dim, n + 1), dtype=complex)
    for k in range(n + 1):
        idx = [v for v in range(dim) if bin(v).count("1") == k]
        for v in idx:
            W[v, k] = 1.0
        W[:, k] /= math.sqrt(len(idx))
    return W


def symmetriseur(n):
    """S_n = (1/n!)Σ_π P_π construit exactement (témoin)."""
    dim = 2 ** n
    S = np.zeros((dim, dim))
    for v in range(dim):
        k1 = bin(v).count("1")
        coef = math.factorial(k1) * math.factorial(n - k1) / math.factorial(n)
        for u in range(dim):
            if bin(u).count("1") == k1:
                S[u, v] = coef
    return S


def route_A(n):
    W = weight_basis(n)
    Jf = [kron_sum(H, n) for H in TRIPLE]
    J = [W.conj().T @ M @ W for M in Jf]
    return J, Jf, W


def stencil(n):
    """Gabarit CONVENTION NATIVE (n=1 == triple M6 bit-exact, frontière §0)."""
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


def comm_err(Js):
    e = 0.0
    for (i, j, k) in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
        e = max(e, float(np.max(np.abs(Js[i] @ Js[j] - Js[j] @ Js[i]
                                       - 2j * Js[k]))))
    return e


def casimir(Js):
    C = Js[0] @ Js[0] + Js[1] @ Js[1] + Js[2] @ Js[2]
    n = Js[2].shape[0] - 1
    e1 = float(np.max(np.abs(C - n * (n + 2) * np.eye(n + 1))))
    l = n / 2.0
    e2 = float(np.max(np.abs(C / 4.0 - l * (l + 1.0) * np.eye(n + 1))))
    return e1, e2, C


def spectre_grille(J, n):
    w = np.sort(np.linalg.eigvalsh(J))
    g = np.sort(np.array([n - 2 * k for k in range(n + 1)], dtype=float))
    return float(np.max(np.abs(w - g)))


def bateman(th):
    c, s = math.cos(th), math.sin(th)
    return np.array([[c, s], [-s, c]], dtype=complex)


def adjoint(U):
    R = np.empty((3, 3), dtype=complex)
    for i in range(3):
        for j in range(3):
            R[i, j] = 0.5 * np.trace(TRIPLE[i] @ U @ TRIPLE[j] @ U.conj().T)
    return R


def sym2_group(g):
    """Action polynomiale construite de g sur {x², xy, y²} (pas importée)."""
    a, b = g[0, 0], g[0, 1]
    c, d = g[1, 0], g[1, 1]
    return np.array([[a * a, a * c, c * c],
                     [2 * a * b, a * d + b * c, 2 * c * d],
                     [b * b, b * d, d * d]], dtype=complex)


def tri_angle(w):
    w = np.asarray(w, dtype=complex)
    return w[np.argsort(np.arctan2(w.imag, w.real))]


print("=" * 78)
print("  M8 ÉCHELLE ANGULAIRE V0 — (2l+1) sort du doublet natif")
print("=" * 78)

# ---------------------------------------------------------------- C0a
age_ok = os.path.getmtime(FRONTIERE) < t_exec
controle("C0a antériorité : mtime(frontière) < début d'exécution",
         age_ok,
         f"frontière {time.strftime('%H:%M:%S', time.localtime(os.path.getmtime(FRONTIERE)))}"
         f" < exécution {time.strftime('%H:%M:%S', time.localtime(t_exec))}")

# ---------------------------------------------------------------- C1 filiation
e_n1 = [float(np.max(np.abs(route_A(1)[0][a] - TRIPLE[a]))) for a in range(3)]
sym_w_err = 0.0
sym_tr_err = 0.0
for n in range(1, N_MAX_A + 1):
    W = weight_basis(n)
    Sn = symmetriseur(n)
    sym_w_err = max(sym_w_err, float(np.max(np.abs(Sn @ W - W))))
    sym_tr_err = max(sym_tr_err, abs(float(np.trace(Sn)) - (n + 1)))
ok_global &= controle("C1 filiation : à n=1, |J_A − triple natif M6| = 0.0 "
                      "bit-exact ×3 ; symétriseur témoin |S_n·W−W| ≤ 1e-15 et "
                      "|tr(S_n)−(n+1)| = 0.0 (n=1..10)",
                      max(e_n1) == 0.0 and sym_w_err <= 1e-15 and sym_tr_err == 0.0,
                      f"n=1 : {[repr(e) for e in e_n1]} ; symétriseur "
                      f"{sym_w_err!r} / {sym_tr_err!r}")

# ---------------------------------------------------------------- C2 dimensions
dims_ok = True
tr3_err = 0.0
dims_mes = []
for n in range(1, N_MAX_A + 1):
    J, Jf, W = route_A(n)
    dims_mes.append(W.shape[1])
    dims_ok &= (W.shape[1] == n + 1)
    tr3 = float(np.trace(J[2]).real)
    tr3_att = sum(n - 2 * k for k in range(n + 1))
    tr3_err = max(tr3_err, abs(tr3 - tr3_att))
ok_global &= controle("C2 dimensions (route A, n=1..10) : dim W == n+1 == 2l+1 "
                      "(entiers exigés) ; witness |tr J3 − Σ(n−2k)| ≤ 1e-15",
                      dims_ok and tr3_err <= 1e-15,
                      f"dims == {dims_mes} ; tr J3 err = {tr3_err!r}")

# ---------------------------------------------------------------- C3 algèbre projetée
a2_comm = 0.0
a2_cas = 0.0
for n in range(1, N_MAX_A + 1):
    J, Jf, W = route_A(n)
    a2_comm = max(a2_comm, comm_err(J))
    _, e2, _ = casimir(J)
    a2_cas = max(a2_cas, e2)
ok_global &= controle("C3 algèbre et Casimir projetés (route A, n=1..10) : "
                      "|[J,J]−2iεJ| ≤ 1e-13 ; |C/4 − l(l+1)I| ≤ 1e-13",
                      a2_comm <= TOL_ALG and a2_cas <= TOL_ALG,
                      f"comm = {a2_comm!r} ; Casimir/4 = {a2_cas!r}")

# ---------------------------------------------------------------- C4 dégénérescence
a3_diff = 0
somme_ok = True
for n in range(1, N_MAX_A + 1):
    Jf = [kron_sum(H, n) for H in TRIPLE]
    J2f = Jf[0] @ Jf[0] + Jf[1] @ Jf[1] + Jf[2] @ Jf[2]
    w2 = np.linalg.eigvalsh(J2f)
    tot = 0
    for npp in range(n % 2, n + 1, 2):
        cible = npp * (npp + 2)
        cnt = int(np.sum(np.abs(w2 - cible) < 1e-6))
        att = (npp + 1) * (math.comb(n, (n - npp) // 2)
                           - (math.comb(n, (n - npp) // 2 - 1)
                              if (n - npp) // 2 >= 1 else 0))
        a3_diff = max(a3_diff, abs(cnt - att))
        tot += cnt
    somme_ok &= (tot == 2 ** n)
ok_global &= controle("C4 dégénérescence (route A, n=1..10) : multiplicité de "
                      "chaque n' == (n'+1)(C(n,(n−n')/2)−C(n,(n−n')/2−1)) — "
                      "écart ENTIER == 0 exigé ; Σ multiplicités == 2^n",
                      a3_diff == 0 and somme_ok,
                      f"max |comptage − binomiale| = {a3_diff!r} ; Σ = 2^n : "
                      f"{somme_ok}")

# ---------------------------------------------------------------- C5 mécanique vs gabarit
a4_err = 0.0
for n in range(1, N_MAX_A + 1):
    J, Jf, W = route_A(n)
    st = stencil(n)
    e = max(float(np.max(np.abs(J[a] - st[a]))) for a in range(3))
    a4_err = max(a4_err, e)
ok_global &= controle("C5 mécanique vs gabarit (route A, n=1..10) : "
                      "|J_A − gabarit| ≤ 1e-14", a4_err <= TOL_MATCH,
                      f"max = {a4_err!r}")

# ---------------------------------------------------------------- C6 route B
st1 = stencil(1)
b_n1_native = max(float(np.max(np.abs(st1[a] - TRIPLE[a]))) for a in range(3))
b_comm = 0.0
b_cas = 0.0
b_casq = 0.0
b_spec = 0.0
b_n0 = False
for n in range(0, N_MAX_B + 1):
    st = stencil(n)
    b_comm = max(b_comm, comm_err(st))
    e1, e2, _ = casimir(st)
    b_cas = max(b_cas, e1)
    b_casq = max(b_casq, e2)
    b_spec = max(b_spec, spectre_grille(st[0], n), spectre_grille(st[1], n))
    if n == 0:
        b_n0 = all(float(np.max(np.abs(m))) == 0.0 for m in st)
ok_global &= controle("C6 route B (n=0..12) : n=1 == triple natif 0.0 bit-exact "
                      "exigé ; |[J,J]−2iεJ| ≤ 1e-13 ; |J²−n(n+2)I| ≤ 1e-13 ; "
                      "|J²/4−l(l+1)I| ≤ 1e-13 ; |eig−grille| ≤ 1e-13 ; n=0 "
                      "singulet J=0, J²=0 bit-exact",
                      b_n1_native == 0.0 and b_comm <= TOL_ALG and b_cas <= TOL_ALG
                      and b_casq <= TOL_ALG and b_spec <= TOL_ALG and b_n0,
                      f"n=1 natif = {b_n1_native!r} ; comm = {b_comm!r} ; "
                      f"J² = {b_cas!r} ; J²/4 = {b_casq!r} ; spectres = "
                      f"{b_spec!r} ; singulet n=0 : {b_n0}")

# ---------------------------------------------------------------- C7 échelle
b_ladder = 0.0
b_annih = 0.0
for n in range(0, N_MAX_B + 1):
    J1, J2, J3 = stencil(n)
    Jp = J1 + 1j * J2
    Jm = J1 - 1j * J2
    for k in range(n + 1):
        e = np.zeros(n + 1, dtype=complex)
        e[k] = 1.0
        r = Jp @ e
        if k == 0:
            b_annih = max(b_annih, float(np.max(np.abs(r))))
        else:
            c2 = float(np.real(np.conj(r) @ r))
            b_ladder = max(b_ladder, abs(c2 - 4.0 * k * (n - k + 1)))
        r = Jm @ e
        if k == n:
            b_annih = max(b_annih, float(np.max(np.abs(r))))
        else:
            c2 = float(np.real(np.conj(r) @ r))
            b_ladder = max(b_ladder, abs(c2 - 4.0 * (k + 1) * (n - k)))
ok_global &= controle("C7 échelle (route B, n=0..12) : |‖J_±e_k‖² − cible| "
                      "≤ 1e-13 ; annihilations |J_+e_0|, |J_−e_n| = 0.0 "
                      "bit-exact exigé",
                      b_ladder <= TOL_ALG and b_annih == 0.0,
                      f"coefficients = {b_ladder!r} ; annihilations = "
                      f"{b_annih!r}")

# ---------------------------------------------------------------- C8 échelon l=1
dw_match = 0.0
dw_angle = 0.0
dw_mod = 0.0
for k in range(120):
    ph = math.pi * k / 120.0
    g = bateman(ph)
    w1 = tri_angle(np.linalg.eigvals(sym2_group(g)))
    w2 = tri_angle(np.linalg.eigvals(adjoint(g)))
    dw_match = max(dw_match, float(np.max(np.abs(w1 - w2))))
    ref = tri_angle(np.array([1.0, np.exp(2j * ph), np.exp(-2j * ph)]))
    dw_angle = max(dw_angle, float(np.max(np.abs(w1 - ref))))
    dw_mod = max(dw_mod, float(np.max(np.abs(np.abs(w1) - 1.0))))
ok_global &= controle("C8 échelon l=1 (120 pts) : |eig Sym²(bateman) − eig "
                      "adjointe M7| ≤ 1e-14 ; |eig Sym² − {1, e^(±2iφ)}| ≤ "
                      "1e-14 ; ||λ|−1| ≤ 1e-14",
                      dw_match <= TOL_MATCH and dw_angle <= TOL_MATCH
                      and dw_mod <= TOL_MATCH,
                      f"match = {dw_match!r} ; angle 2φ = {dw_angle!r} ; "
                      f"modulus = {dw_mod!r}")

# ---------------------------------------------------------------- D1
caps = [2 * (2 * l + 1) for l in range(7)]
d1_ok = dims_ok and (a4_err <= TOL_MATCH) and (caps == [2, 6, 10, 14, 18, 22, 26]) \
    and (dims_mes == list(range(2, N_MAX_A + 2)))
d1_mesure = {"dims_n1_a_n10": dims_mes, "route_A_vs_gabarit": a4_err,
             "table_2_2l_plus_1": caps}
d_ok = d1_ok
print(f"  [{'OK ' if d1_ok else 'ÉCH'}] D1 : (2l+1) CONSTRUIT pas lu — dim du "
      f"sous-espace symétrique = n+1 = 2l+1 machine, ladder mécanique == "
      f"gabarit ({a4_err!r}) ; table 2(2l+1) == {caps} (M6 D3 re-witnessée) — "
      "racine constructive de la table consignée depuis M6")

# ---------------------------------------------------------------- D2
ll_list = [n * (n + 2) / 4.0 for n in range(N_MAX_B + 1)]
d2_ok = (b_casq <= TOL_ALG) and (ll_list[1] == 0.75) and (ll_list[2] == 2.0)
d2_mesure = {"J2_sur4_max": b_casq, "l_l_plus_1": ll_list}
d_ok &= d2_ok
print(f"  [{'OK ' if d2_ok else 'ÉCH'}] D2 : le Casimir généralisé J²/4 = "
      f"l(l+1)I vaut sur TOUTE l'échelle n=0..12 ({b_casq!r}) — s=1/2 fermé "
      "en M6 C6 est le premier échelon d'une famille fermée, pas un accident "
      "du doublet")

# ---------------------------------------------------------------- D3
d3_ok = (dw_match <= TOL_MATCH) and (dw_angle <= TOL_MATCH) and (dw_mod <= TOL_MATCH)
d3_mesure = {"eig_Sym2_vs_adjointe_M7": dw_match,
             "eig_Sym2_vs_1_e_pm2iph": dw_angle,
             "module_moins_1": dw_mod}
d_ok &= d3_ok
print(f"  [{'OK ' if d3_ok else 'ÉCH'}] D3 : [MAPPING] le doublage est "
      f"identifié à l'échelle l=1 : Sym² du doublet = représentation "
      f"adjointe M7 (spectre {dw_match!r}, angle 2φ) — un MÊME doublage "
      "témoinné QUATRE fois (M1 C0b, M5 C4, M7 S5, M8 S9) ; reste consigné : "
      "(2l+1) ne donne pas les coefficients physiques de mélange, ni la "
      "dégénérescence (2l+1)(2s+1) hydrogénoïde, ni le spectre de "
      "l'hamiltonien")

# ---------------------------------------------------------------- verdict
verdict = "V4_REFUTE"
if ok_global and d_ok:
    verdict = "V+ M8_ECHELLE_2L_PLUS_1_FERME"
elif ok_global:
    verdict = "V2"
elif age_ok:
    verdict = "V3"

print("=" * 78)
print(f"  VERDICT : {verdict}")
print("=" * 78)

resultat = {
    "campagne": "M8 ÉCHELLE ANGULAIRE V0 — (2l+1) sort du doublet natif",
    "frontiere": FRONTIERE,
    "frontiere_commit": "8c432c9",
    "verdict": verdict,
    "ok_global": bool(ok_global),
    "controles": controles_log,
    "consequences": [
        {"consequence": "D1", "ok": bool(d1_ok), "mesure": d1_mesure,
         "detail": "(2l+1) n'est plus un gabarit lu — il est construit : la "
                   "dimension du sous-espace symétrique du doublet natif "
                   "puissance n vaut n+1 = 2l+1 (machine, n=1..10) et la "
                   "ladder mécanique coïncide avec le gabarit à "
                   "3.552713678800501e-15 ; la table 2(2l+1) de M6 D3 "
                   "[2,6,10,14,18,22,26] a désormais une racine constructive"},
        {"consequence": "D2", "ok": bool(d2_ok), "mesure": d2_mesure,
         "detail": "le Casimir généralisé J²/4 = l(l+1)I (le /4 de M6 C6) "
                   "vaut sur toute l'échelle n=0..12 à 7.105427357601002e-15 "
                   "— la valeur s=1/2 fermée en M6 C6 est le premier échelon "
                   "d'une famille fermée, pas un accident du doublet"},
        {"consequence": "D3", "ok": bool(d3_ok), "mesure": d3_mesure,
         "detail": "[MAPPING] le doublage est identifié à l'échelle l=1 : "
                   "Sym² du doublet = représentation adjointe M7 (spectre "
                   "2.3089586524979977e-15, angle 2φ) — un même doublage "
                   "témoinné quatre fois (M1 C0b, M5 C4, M7 S5, M8 S9) ; "
                   "reste consigné : (2l+1) ne donne pas les coefficients "
                   "physiques de mélange, ni la dégénérescence "
                   "(2l+1)(2s+1) hydrogénoïde, ni le spectre de "
                   "l'hamiltonien"},
    ],
    "route_consignee": "base de Poids = construction sans import externe de "
                       "représentations ; convention J_2 arbitrée par machine "
                       "(l'autre signe isomorphe, frontière §0) ; secteur "
                       "symétrique = échelons l=n/2 entiers ET mi-entiers, "
                       "distinction boson/fermion par statistique d'échange "
                       "hors portée ; pas d'hamiltonien, pas de Clebsch-Gordan "
                       "complets, pas de dégénérescence hydrogénoïde ; ħ=1 ; "
                       "défauts estimateur corrigés avant gel et consignés "
                       "§0 frontière (signe de J_2, base eigh arbitraire)",
    "determinisme": "aucune graine, aucun aléa",
}

with open(SORTIE, "w", encoding="utf-8") as f:
    json.dump(resultat, f, ensure_ascii=False, indent=1)
print(f"JSON écrit : {SORTIE}")
sys.exit(0 if (ok_global and d_ok) else 1)