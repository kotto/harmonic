# -*- coding: utf-8 -*-
"""
VERIF M6 — SU(2) NATIVE : l'algèbre de Pauli sort des objets déposés (MORT 6).

Frontière : FRONTIERE_M6_SU2_V0.md (1dc6fcf, dépôt-d'abord C0a — ce script
n'existait pas au moment du dépôt). Toutes les barres sont gelées dans la
frontière §2 ; UN SEUL échec ⟹ V4_REFUTE exit 1, sans sauvetage.

Objet : σ_x = deck S (échange de feuillets, M5), σ_y = −i·J (tangente Bateman,
M1 C3 ; le i est celui du noyau λ(ω)=(iω)^α D3D db00e3b O2/C10), σ_z = J·S.
Algèbre Pauli fermée bit-exact, lift demi-angle bateman(φ)²=bateman(2φ),
spinorité 2π→−I / 4π→+I, Casimir s(s+1)=3/4 ⟹ s=1/2.

Déterministe : aucune graine, aucun aléa.
"""

import cmath
import json
import math
import os
import sys
import time

import numpy as np
import mpmath as mp

mp.mp.dps = 40

FRONTIERE = "FRONTIERE_M6_SU2_V0.md"
SORTIE = "resultat_m6_su2_v0.json"

PHI = (1.0 + math.sqrt(5.0)) / 2.0
ALPHA = 1.0 / PHI
THETA = ALPHA * math.pi / 2.0
GRID = 720
RS = [0.5, 1.0, 2.0, 3.0, 25.6]
TOL_C = 1.0e-15
TOL_GEN = 1.0e-10

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


def bateman(th):
    """Verbatim M1 C3 : matrice de Bateman [[c,s],[-s,c]]."""
    c = math.cos(th)
    s = math.sin(th)
    return np.array([[c, s], [-s, c]], dtype=complex)


I2 = np.eye(2, dtype=complex)

print("=" * 78)
print("  M6 SU(2) NATIVE V0 — l'algèbre de Pauli sort des objets déposés")
print("=" * 78)

# ---------------------------------------------------------------- C0a — antériorité
age_ok = os.path.getmtime(FRONTIERE) < t_exec
controle("C0a antériorité : mtime(frontière) < début d'exécution",
         age_ok,
         f"frontière {time.strftime('%H:%M:%S', time.localtime(os.path.getmtime(FRONTIERE)))}"
         f" < exécution {time.strftime('%H:%M:%S', time.localtime(t_exec))}")

# ---------------------------------------------------------------- C1 — filiation M1 C3
R0 = bateman(0.0)
ec_R0 = float(np.max(np.abs(R0 - I2)))
phi_grid = np.array([math.pi * k / GRID for k in range(GRID)])
ec_det = max(abs(complex(np.linalg.det(bateman(ph))) - 1.0) for ph in phi_grid)
ec_trace = max(abs(float(np.trace(bateman(ph)).real) - 2.0 * math.cos(ph))
               for ph in phi_grid)
ec_unit = max(float(np.max(np.abs(bateman(ph).conj().T @ bateman(ph) - I2)))
              for ph in phi_grid)
ok_global &= controle("C1 filiation M1 C3 : R(0)=I bit-exact ; |det R(φ)−1| ≤ 1e-15 ; "
                      "|tr R(φ)−2cosφ| ≤ 1e-15 ; |R†R−I| ≤ 1e-15 (720 pts)",
                      ec_R0 == 0.0 and ec_det <= TOL_C and ec_trace <= TOL_C
                      and ec_unit <= TOL_C,
                      f"R(0)−I = {ec_R0!r} ; det = {ec_det!r} ; trace = {ec_trace!r} ; "
                      f"unitarité = {ec_unit!r}")

# ---------------------------------------------------------------- C2 — générateurs natifs
S = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
J = np.array([[0.0, 1.0], [-1.0, 0.0]], dtype=complex)
P = J @ S
h = 1.0e-5
J_num = (bateman(h) - bateman(-h)) / (2.0 * h)
ec_J = float(np.max(np.abs(J_num - J)))
ec_S2 = float(np.max(np.abs(S @ S - I2)))
ec_J2 = float(np.max(np.abs(J @ J + I2)))
ec_P2 = float(np.max(np.abs(P @ P - I2)))
ec_ptr = float(abs(np.trace(P).real) + abs(np.trace(P).imag))
P_ref = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
ec_P = float(np.max(np.abs(P - P_ref)))
ok_global &= controle("C2 générateurs natifs : écart(J numérique, J analytique) ≤ 1e-10 ; "
                      "S²−I = 0.0, J²+I = 0.0, P²−I = 0.0 bit-exacts ; tr = 0.0 bit-exacts ; "
                      "P == diag(1,−1) bit-exact",
                      ec_J <= TOL_GEN and ec_S2 == 0.0 and ec_J2 == 0.0
                      and ec_P2 == 0.0 and ec_ptr == 0.0 and ec_P == 0.0,
                      f"J num−J = {ec_J!r} (barre 1e-10) ; S²−I = {ec_S2!r} ; "
                      f"J²+I = {ec_J2!r} ; P²−I = {ec_P2!r} ; P−diag(1,−1) = {ec_P!r}")

# ---------------------------------------------------------------- C3 — algèbre Pauli
H1 = S.copy()
H2 = (-1j) * J
H3 = P.copy()


def comm(A, B):
    return A @ B - B @ A


def antic(A, B):
    return A @ B + B @ A


ec_herm = max(float(np.max(np.abs(Ha - Ha.conj().T))) for Ha in (H1, H2, H3))
ec_sq = max(float(np.max(np.abs(Ha @ Ha - I2))) for Ha in (H1, H2, H3))
ec_com = max(float(np.max(np.abs(comm(H1, H2) - 2j * H3))),
             float(np.max(np.abs(comm(H2, H3) - 2j * H1))),
             float(np.max(np.abs(comm(H3, H1) - 2j * H2))))
ec_anti_diag = max(float(np.max(np.abs(antic(Ha, Ha) - 2.0 * I2)))
                   for Ha in (H1, H2, H3))
ec_anti_off = max(float(np.max(np.abs(antic(H1, H2)))),
                  float(np.max(np.abs(antic(H1, H3)))),
                  float(np.max(np.abs(antic(H2, H3)))))
ec_tr = max(abs(float(np.trace(Ha).real)) + abs(float(np.trace(Ha).imag))
            for Ha in (H1, H2, H3))
ok_global &= controle("C3 algèbre Pauli bit-exacte : hermiticité, H_a²−I, "
                      "[H1,H2]−2iH3 / [H2,H3]−2iH1 / [H3,H1]−2iH2, {H_a,H_a}−2I, "
                      "{H_a,H_b} (a≠b), |tr H_a| — tous ≤ 1e-15",
                      ec_herm <= TOL_C and ec_sq <= TOL_C and ec_com <= TOL_C
                      and ec_anti_diag <= TOL_C and ec_anti_off <= TOL_C
                      and ec_tr <= TOL_C,
                      f"herm = {ec_herm!r} ; carrés = {ec_sq!r} ; commutateurs = {ec_com!r} ; "
                      f"anticomm diag = {ec_anti_diag!r} ; anticomm off = {ec_anti_off!r} ; "
                      f"traces = {ec_tr!r}")

# ---------------------------------------------------------------- C4 — lift demi-angle
ec_U2 = max(float(np.max(np.abs(bateman(ph) @ bateman(ph) - bateman(2.0 * ph))))
            for ph in phi_grid)
ec_upi = float(np.max(np.abs(bateman(math.pi) + I2)))
ec_u2pi = float(np.max(np.abs(bateman(2.0 * math.pi) - I2)))
ec_central = max(
    float(np.max(np.abs((-I2 @ Ha) - (Ha @ -I2)))) for Ha in (H1, H2, H3))
ok_global &= controle("C4 lift demi-angle : |bateman(φ)²−bateman(2φ)| ≤ 1e-15 (720 pts) ; "
                      "|bateman(π)+I| ≤ 1e-15 ; |bateman(2π)−I| ≤ 1e-15 ; "
                      "centralité de −I = 0.0 bit-exacte",
                      ec_U2 <= TOL_C and ec_upi <= TOL_C and ec_u2pi <= TOL_C
                      and ec_central == 0.0,
                      f"lift = {ec_U2!r} ; 2π→−I : {ec_upi!r} ; 4π→+I : {ec_u2pi!r} ; "
                      f"centralité = {ec_central!r}")

# ---------------------------------------------------------------- C5 — appartenance SU(2)
U_neg = bateman(-0.7)
U_pos = bateman(0.7)
ec_dag = float(np.max(np.abs(U_pos.conj().T - U_neg)))
A = (-bateman(0.3)) @ (-bateman(1.1))
ec_groupe = float(np.max(np.abs(A - bateman(1.4))))
ok_global &= controle("C5 appartenance SU(2) : |U†U−I| ≤ 1e-15 (720 pts) ; |det U−1| ≤ 1e-15 ; "
                      "|U(0.7)†−U(−0.7)| ≤ 1e-15 ; |(−U(0.3))·(−U(1.1))−U(1.4)| ≤ 1e-15",
                      ec_unit <= TOL_C and ec_det <= TOL_C and ec_dag <= TOL_C
                      and ec_groupe <= TOL_C,
                      f"unitarité = {ec_unit!r} ; det = {ec_det!r} ; U†=U(−φ) : {ec_dag!r} ; "
                      f"groupe {chr(123)}±U(φ){chr(125)} : {ec_groupe!r}")

# ---------------------------------------------------------------- C6 — Casimir
cas = (H1 @ H1 + H2 @ H2 + H3 @ H3) / 4.0
ec_cas = float(np.max(np.abs(cas - 0.75 * I2)))
PHI_M = (1 + mp.sqrt(5)) / 2
ALPHA_M = 1 / PHI_M
s_root = mp.findroot(lambda s: s * (s + 1) - mp.mpf(3) / 4, mp.mpf("0.5"))
ec_s = abs(s_root - mp.mpf("0.5"))
Sz = P / 2.0
vals = np.linalg.eigvalsh(Sz)
ec_vals = max(abs(vals[0] + 0.5), abs(vals[1] - 0.5))
ok_global &= controle("C6 Casimir : |(H1²+H2²+H3²)/4 − (3/4)I| ≤ 1e-15 ; racine de "
                      "s(s+1)=3/4 == 0.5 (mpmath dps40) ; eig(S_z) == {−1/2, +1/2} ≤ 1e-15",
                      ec_cas <= TOL_C and ec_s < mp.mpf("1e-30") and ec_vals <= TOL_C,
                      f"Casimir = {ec_cas!r} ; s = {mp.nstr(s_root, 20)} "
                      f"(écart {mp.nstr(ec_s, 5)}) ; eig(S_z) = {vals!r}, écart {ec_vals!r}")

# ---------------------------------------------------------------- C7 — cohérence M5 + consignation


def lambda_weight(w, a=1.0):
    """Verbatim D3D db00e3b O2/C10 : (iω)^α branche principale (α=1 ici)."""
    return np.power(1j * w, a)


ec_fibre = 0.0
fibre_ok = 0
for r in RS:
    lp = complex(lambda_weight(r))
    lm = complex(lambda_weight(-r))
    ec_fibre = max(ec_fibre, abs(lp - 1j * r), abs(lm + 1j * r))
    if abs(lp + lm) <= TOL_C and abs(lp - lm) >= 1.0:
        fibre_ok += 1
sigma_a1 = cmath.exp(1j * math.pi)
ec_sig = abs(sigma_a1 + 1.0)
vals_S = np.linalg.eigvalsh(S)
ec_eigS = max(abs(vals_S[0] + 1.0), abs(vals_S[1] - 1.0))
ok_global &= controle("C7 cohérence M5 + consignation : fibre α=1 bit-exacte "
                      "(|λ(r)∓i·r| = 0.0 exigé) sur RS ; fibres à 2 valeurs == 5/5 "
                      "(|λ(r)+λ(−r)| ≤ 1e-15 ET |λ(r)−λ(−r)| ≥ 1.0, condition gelée "
                      "post-correction) ; |σ(1)+1| ≤ 1e-15 ; eig(S) == {−1,+1} ≤ 1e-15",
                      ec_fibre == 0.0 and fibre_ok == 5 and ec_sig <= TOL_C
                      and ec_eigS <= TOL_C,
                      f"fibre bit-exacte : {ec_fibre!r} ; fibres : {fibre_ok}/5 ; "
                      f"|σ(1)+1| = {ec_sig!r} ; eig(S) = {vals_S!r} (écart {ec_eigS!r})")

# ---------------------------------------------------------------- D1 — s = 1/2 par machine
d1_ok = ec_cas <= TOL_C and ec_s < mp.mpf("1e-30") and ec_vals <= TOL_C
d1_mesure = {"casimir_ecart": ec_cas, "s_racine": float(s_root), "eig_sz": [float(v) for v in vals]}
d_ok = d1_ok
print(f"  [{'OK ' if d1_ok else 'ÉCH'}] D1 : le spin du lien vaut UN DEMI — Casimir "
      f"(1/4)Σσ²=(3/4)I bit-exact, racine s(s+1)=3/4 == 0.5, eig(S_z)={{−1/2,+1/2}}")

# ---------------------------------------------------------------- D2 — l'échange EST le centre
d2_ok = ec_eigS <= TOL_C and ec_sig <= TOL_C and ec_central == 0.0 \
    and ec_upi <= TOL_C
d2_mesure = {"eig_S": [float(v) for v in vals_S],
             "sigma_1": [complex(sigma_a1).real, complex(sigma_a1).imag],
             "centralite_moins_I": ec_central,
             "U_pi_plus_I": ec_upi}
d_ok &= d2_ok
print(f"  [{'OK ' if d2_ok else 'ÉCH'}] D2 : la signature d'échange EST le centre — "
      f"eig(S)={vals_S!r}, σ(1)={sigma_a1!r}, −I central (0.0), U(π)=−I")

# ---------------------------------------------------------------- D3 — [MAPPING] dimension
caps = [2 * (2 * l + 1) for l in range(7)]
d3_ok = caps == [2, 6, 10, 14, 18, 22, 26]
d_ok &= d3_ok
print(f"  [{'OK ' if d3_ok else 'ÉCH'}] D3 : [MAPPING] dimension 2 = dimension de fibre "
      f"M5 (5/5 ré-witness C7) ; 2(2l+1) l=0..6 == {caps} ; (2l+1) NON dérivé, consigné")

# ---------------------------------------------------------------- verdict
verdict = "V4_REFUTE"
if ok_global and d_ok:
    verdict = "V+ M6_SU2_NATIVE_PAULI_FERME"
elif ok_global:
    verdict = "V2"
elif age_ok:
    verdict = "V3"

print("=" * 78)
print(f"  VERDICT : {verdict}")
print("=" * 78)

resultat = {
    "campagne": "M6 SU(2) NATIVE V0 — l'algèbre de Pauli sort des objets déposés",
    "frontiere": FRONTIERE,
    "frontiere_commit": "1dc6fcf",
    "verdict": verdict,
    "ok_global": bool(ok_global),
    "controles": controles_log,
    "consequences": [
        {"consequence": "D1", "ok": bool(d1_ok), "mesure": d1_mesure,
         "detail": "le spin du lien vaut UN DEMI : Casimir (1/4)Σσ²=(3/4)I bit-exact, "
                   "racine s(s+1)=3/4 == 0.5 (mpmath dps40), eig(S_z)={−1/2,+1/2}"},
        {"consequence": "D2", "ok": bool(d2_ok), "mesure": d2_mesure,
         "detail": "la signature d'échange EST le centre : eig(S)={−1,+1}, σ(1)=−1, "
                   "−I central, U(π)=−I — Z₂ du revêtement = centre de SU(2)"},
        {"consequence": "D3", "ok": bool(d3_ok), "mesure": caps,
         "detail": "[MAPPING] dimension 2 = dimension de fibre M5 (5/5) ; 2(2l+1), "
                   "l=0..6 == [2,6,10,14,18,22,26] ; (2l+1) NON dérivé, consigné"},
    ],
    "route_consignee": "SO(3) géométrique non construite (un seul axe natif exp(φJ)) ; "
                       "g=2 hors portée ; j non dérivé (M4 a73c116) ; sl(2,R) split vs "
                       "su(2) compacte : le i qui compactifie est celui du noyau "
                       "λ(ω)=(iω)^α — consigné avant gel, jamais gelé",
    "determinisme": "aucune graine, aucun aléa",
}

with open(SORTIE, "w", encoding="utf-8") as f:
    json.dump(resultat, f, ensure_ascii=False, indent=1)
print(f"JSON écrit : {SORTIE}")
sys.exit(0 if (ok_global and d_ok) else 1)
