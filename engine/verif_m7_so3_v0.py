# -*- coding: utf-8 -*-
"""
VERIF M7 — SO(3) ADJOINT : la rotation géométrique sort du triple natif.

Frontière : FRONTIERE_M7_SO3_V0.md (0c6e762, dépôt-d'abord C0a — ce script
n'existait pas au moment du dépôt). Toutes les barres sont gelées dans la
frontière §2 ; UN SEUL échec ⟹ V4_REFUTE exit 1, sans sauvetage (I1).

Objet : R(U)_ij = ½·tr(H_i U H_j U†) construite UNIQUEMENT depuis le triple
natif M6 {S, −iJ, J·S}={σ_x, σ_y, σ_z}. Aucune formule de Rodrigues importée,
aucune bibliothèque de rotation, aucune exponentielle de matrice : exp(iφH)
est fermé depuis l'algèbre native H²=I (cosφ·I + i·sinφ·H). Thèses : Bateman
= exp(iφH2) bit-exact (M1=M6), image en SO(3), angle doublé 2φ (à θ=πα/2 :
2θ=πα, M1 C0b re-witness), noyau {±I} = centre = deck, géométrie préservée.

Déterministe : aucune graine, aucun aléa.
"""

import json
import math
import os
import sys
import time

import numpy as np
import mpmath as mp

mp.mp.dps = 40

FRONTIERE = "FRONTIERE_M7_SO3_V0.md"
SORTIE = "resultat_m7_so3_v0.json"

PHI = (1.0 + math.sqrt(5.0)) / 2.0
ALPHA = 1.0 / PHI
THETA = ALPHA * math.pi / 2.0
GRID = 720
ANGLES_EULER = [0.3, 0.7, 1.1, 2.3]
VECTEURS = [(1.0, 2.0, 3.0), (PHI, 1.0, 1.0 / PHI), (0.7, -1.3, 2.2)]
TOL_C = 1.0e-15
TOL_COMP = 1.0e-14  # barre gelée « composés » (C5, C7)
TOL_MP = mp.mpf("1e-35")

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

# Triple natif M6 verbatim
S = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
J = np.array([[0.0, 1.0], [-1.0, 0.0]], dtype=complex)
P = J @ S
H1 = S.copy()
H2 = (-1j) * J
H3 = P.copy()
TRIPLE = (H1, H2, H3)


def exp_iH(H, ph):
    """exp(iφH) fermé depuis l'algèbre native : H²=I ⟹ cosφ·I + i·sinφ·H."""
    return math.cos(ph) * I2 + 1j * math.sin(ph) * H


def adjoint(U):
    """R(U)_ij = ½ tr(H_i U H_j U†) — construite UNIQUEMENT depuis le triple natif."""
    R = np.empty((3, 3), dtype=complex)
    for i in range(3):
        for j in range(3):
            R[i, j] = 0.5 * np.trace(TRIPLE[i] @ U @ TRIPLE[j] @ U.conj().T)
    return R


phi_grid = np.array([math.pi * k / GRID for k in range(GRID)])
comps = [exp_iH(H1, a) @ exp_iH(H2, b) @ exp_iH(H3, c)
         for a in ANGLES_EULER for b in ANGLES_EULER for c in ANGLES_EULER]

print("=" * 78)
print("  M7 SO(3) ADJOINT V0 — la rotation géométrique sort du triple natif")
print("=" * 78)

# ---------------------------------------------------------------- C0a — antériorité
age_ok = os.path.getmtime(FRONTIERE) < t_exec
controle("C0a antériorité : mtime(frontière) < début d'exécution",
         age_ok,
         f"frontière {time.strftime('%H:%M:%S', time.localtime(os.path.getmtime(FRONTIERE)))}"
         f" < exécution {time.strftime('%H:%M:%S', time.localtime(t_exec))}")

# ---------------------------------------------------------------- C1 — filiation M6/M1
ec_sq = max(float(np.max(np.abs(Ha @ Ha - I2))) for Ha in TRIPLE)
ec_fam = max(float(np.max(np.abs(exp_iH(H2, ph) - bateman(ph)))) for ph in phi_grid)
ok_global &= controle("C1 filiation M6/M1 : |H_a²−I| = 0.0 bit-exact (triple natif) ; "
                      "|exp(iφH2)−bateman(φ)| = 0.0 bit-exact sur 720 pts",
                      ec_sq == 0.0 and ec_fam == 0.0,
                      f"H_a²−I = {ec_sq!r} ; exp(iφH2)−bateman(φ) = {ec_fam!r} — "
                      "la famille déposée M1 EST le sous-groupe à un paramètre du triple M6")

# ---------------------------------------------------------------- C2 — adjoint réelle
ec_imag_fam = max(float(np.max(np.abs(adjoint(bateman(ph)).imag))) for ph in phi_grid)
ec_imag_comp = max(float(np.max(np.abs(adjoint(U).imag))) for U in comps)
ok_global &= controle("C2 adjoint réelle : max|R.imag| ≤ 1e-15 sur famille 720 pts "
                      "ET 64 composés Euler",
                      ec_imag_fam <= TOL_C and ec_imag_comp <= TOL_C,
                      f"famille = {ec_imag_fam!r} ; composés = {ec_imag_comp!r}")

# ---------------------------------------------------------------- C3 — image et axes
ec_R11 = max(abs(float(adjoint(bateman(ph))[1, 1].real) - 1.0) for ph in phi_grid)
ec_off = max(max(abs(float(adjoint(bateman(ph))[1, 0].real)),
                 abs(float(adjoint(bateman(ph))[0, 1].real)),
                 abs(float(adjoint(bateman(ph))[1, 2].real)),
                 abs(float(adjoint(bateman(ph))[2, 1].real))) for ph in phi_grid)
ec_bloc = 0.0
for ph in phi_grid:
    R = adjoint(bateman(ph))
    bloc = np.array([[R[0, 0].real, R[0, 2].real],
                     [R[2, 0].real, R[2, 2].real]])
    ref = np.array([[math.cos(2.0 * ph), -math.sin(2.0 * ph)],
                    [math.sin(2.0 * ph), math.cos(2.0 * ph)]])  # convention UσU† gelée §0
    ec_bloc = max(ec_bloc, float(np.max(np.abs(bloc - ref))))
e2 = np.array([0.0, 1.0, 0.0])
ec_axe = max(float(np.max(np.abs(adjoint(bateman(ph)) @ e2 - e2))) for ph in phi_grid)
ec_axes3 = 0.0
for a in range(3):
    ea = np.zeros(3)
    ea[a] = 1.0
    for ph in phi_grid[::8]:
        R = adjoint(exp_iH(TRIPLE[a], ph))
        ec_axes3 = max(ec_axes3, float(np.max(np.abs(R @ ea - ea))))
ok_global &= controle("C3 image et axes : |R[1,1]−1| ≤ 1e-15 ; hors bloc = 0.0 bit-exact ; "
                      "|bloc − [[cos2φ,−sin2φ],[sin2φ,cos2φ]]| ≤ 1e-15 (convention "
                      "UσU† gelée §0, machine arbitre du signe) ; |R·e_2−e_2| ≤ 1e-15 ; "
                      "3 axes natifs ≤ 1e-15",
                      ec_R11 <= TOL_C and ec_off == 0.0 and ec_bloc <= TOL_C
                      and ec_axe <= TOL_C and ec_axes3 <= TOL_C,
                      f"R[1,1] = {ec_R11!r} ; hors bloc = {ec_off!r} ; bloc = {ec_bloc!r} ; "
                      f"axe e_2 = {ec_axe!r} ; 3 axes = {ec_axes3!r}")

# ---------------------------------------------------------------- C4 — noyau
R_pi = adjoint(bateman(math.pi))
ec_Rpi = float(np.max(np.abs(R_pi - np.eye(3))))
ec_moins = max(float(np.max(np.abs(adjoint(-U) - adjoint(U)))) for U in comps)
ec_deck = max(float(np.max(np.abs(bateman(ph + math.pi) + bateman(ph))))
              for ph in phi_grid[::8])
ok_global &= controle("C4 noyau : |R(bateman(π))−I₃| ≤ 1e-15 ; |R(−U)−R(U)| = 0.0 "
                      "bit-exact (64 composés) ; |bateman(φ+π)+bateman(φ)| ≤ 1e-15",
                      ec_Rpi <= TOL_C and ec_moins == 0.0 and ec_deck <= TOL_C,
                      f"R(bateman(π))−I₃ = {ec_Rpi!r} ; R(−U)−R(U) = {ec_moins!r} ; "
                      f"fibre {chr(123)}U,−U{chr(125)} = {ec_deck!r}")

# ---------------------------------------------------------------- C5 — homomorphisme et SO(3)
ec_homo = 0.0
for U in comps:
    U1 = exp_iH(H1, ANGLES_EULER[1])
    U2 = exp_iH(H3, ANGLES_EULER[2])
    UV = U1 @ U2
    ec_homo = max(ec_homo, float(np.max(np.abs(adjoint(UV) - adjoint(U1) @ adjoint(U2)))))
    ec_homo = max(ec_homo, float(np.max(np.abs(adjoint(U @ U1) - adjoint(U) @ adjoint(U1)))))
ec_orth_fam = max(float(np.max(np.abs(adjoint(bateman(ph)).real.T @ adjoint(bateman(ph)).real
                                      - np.eye(3)))) for ph in phi_grid)
ec_orth_comp = max(float(np.max(np.abs(adjoint(U).real.T @ adjoint(U).real - np.eye(3))))
                   for U in comps)
ec_det_fam = max(abs(float(np.linalg.det(adjoint(bateman(ph)).real)) - 1.0) for ph in phi_grid)
ec_det_comp = max(abs(float(np.linalg.det(adjoint(U).real)) - 1.0) for U in comps)
ok_global &= controle("C5 homomorphisme et SO(3) : |R(UV)−R(U)R(V)| ≤ 1e-15 ; "
                      "|R·Rᵀ−I₃| ≤ 1e-15 famille ET ≤ 1e-14 composés ; "
                      "|det R−1| ≤ 1e-15 famille ET ≤ 1e-14 composés",
                      ec_homo <= TOL_C and ec_orth_fam <= TOL_C and ec_orth_comp <= TOL_COMP
                      and ec_det_fam <= TOL_C and ec_det_comp <= TOL_COMP,
                      f"homo = {ec_homo!r} ; orth famille = {ec_orth_fam!r} / "
                      f"composés = {ec_orth_comp!r} (barre 1e-14) ; "
                      f"det famille = {ec_det_fam!r} / composés = {ec_det_comp!r} "
                      "(barre 1e-14)")

# ---------------------------------------------------------------- C6 — angle doublé
ec_tr = max(abs(float(np.trace(adjoint(bateman(ph))).real) - (1.0 + 2.0 * math.cos(2.0 * ph)))
            for ph in phi_grid)
ec_2t = abs(2.0 * THETA - ALPHA * math.pi)
tr_theta = float(np.trace(adjoint(bateman(THETA))).real)
ec_tr_theta = abs(tr_theta - (1.0 + 2.0 * math.cos(ALPHA * math.pi)))

PHI_M = (1 + mp.sqrt(5)) / 2
ALPHA_M = 1 / PHI_M
th_m = ALPHA_M * mp.pi / 2
U_m = mp.matrix([[mp.cos(th_m), mp.sin(th_m)], [-mp.sin(th_m), mp.cos(th_m)]])
SX = mp.matrix([[0, 1], [1, 0]])
X = SX * U_m * SX * U_m.conjugate().transpose()
R11 = (X[0, 0] + X[1, 1]) / 2
ref_mp = mp.cos(ALPHA_M * mp.pi)
ec_mp = abs(R11 - ref_mp)
Y = U_m * U_m.conjugate().transpose()
tr_contr = (Y[0, 0] + Y[1, 1]) / 2  # témoin tr(UU†)/2 = 1 (frontière §0 S7)
ok_global &= controle("C6 angle doublé : |tr R(U(φ))−(1+2cos 2φ)| ≤ 1e-15 (720 pts) ; "
                      "2θ−πα = 0.0 bit-exact (M1 C0b) ; |tr R(U(θ))−(1+2cos πα)| ≤ 1e-15 ; "
                      "mpmath dps40 : |R₁₁(U(θ))−cos(πα)| ≤ 1e-35",
                      ec_tr <= TOL_C and ec_2t == 0.0 and ec_tr_theta <= TOL_C
                      and ec_mp <= TOL_MP,
                      f"trace = {ec_tr!r} ; 2θ−πα = {ec_2t!r} ; tr R(U(θ)) = {tr_theta!r} "
                      f"(écart {ec_tr_theta!r}) ; mpmath = {mp.nstr(ec_mp, 5)} ; "
                      f"témoin tr(UU†)/2 = {mp.nstr(tr_contr, 30)}")

# ---------------------------------------------------------------- C7 — géométrie
ec_norm = 0.0
ec_scal = 0.0
v1 = np.array(VECTEURS[0]) / math.sqrt(14.0)
v2 = np.array(VECTEURS[1]) / math.sqrt(PHI * PHI + 1.0 + 1.0 / (PHI * PHI))
v3 = np.array(VECTEURS[2])
for v in (v1, v2, v3):
    for U in (bateman(THETA), comps[0], comps[21], comps[63]):
        R = adjoint(U).real
        w = R @ v
        ec_norm = max(ec_norm, abs(float(w @ w) - float(v @ v)))
        for base in (v1, v2, v3):
            ec_scal = max(ec_scal, abs(float(w @ (R @ base)) - float(v @ base)))
ok_global &= controle("C7 géométrie préservée : |‖Rv‖²−‖v‖²| ≤ 1e-14 et "
                      "|(Rv)·(Rw)−v·w| ≤ 1e-14 sur les témoins gelés §0 "
                      "(v=(1,2,3)/√14, (φ,1,1/φ)/√(φ²+1+φ⁻²), (0.7,−1.3,2.2) ; "
                      "U ∈ {bateman(θ), composés 0, 21, 63})",
                      ec_norm <= TOL_COMP and ec_scal <= TOL_COMP,
                      f"normes = {ec_norm!r} ; produits scalaires = {ec_scal!r}")

# ---------------------------------------------------------------- D1 — noyau = centre = deck
d1_ok = (ec_moins == 0.0) and (ec_Rpi <= TOL_C) and (ec_deck <= TOL_C)
d1_mesure = {"R_moins_U_moins_R_U": ec_moins,
             "R_bateman_pi_moins_I3": ec_Rpi,
             "bateman_phi_plus_pi_plus_bateman_phi": ec_deck}
d_ok = d1_ok
print(f"  [{'OK ' if d1_ok else 'ÉCH'}] D1 : le noyau est le centre est le deck — "
      f"R(−U)=R(U) bit-exact ({ec_moins!r}), R(bateman(π))=I₃ ({ec_Rpi!r}), "
      f"bateman(φ+π)=−bateman(φ) ({ec_deck!r}) — la signature fermionique "
      "(σ(1)=−1, centre M6 D2) est EXACTEMENT la fibre du recouvrement SU(2)→SO(3) ; "
      "ruban de Dirac en forme machine (2π→−I persiste, 4π→+I)")

# ---------------------------------------------------------------- D2 — M1 = M6
d2_ok = (ec_sq == 0.0) and (ec_fam == 0.0)
d2_mesure = {"triple_H2_moins_I": ec_sq, "exp_iH2_moins_bateman": ec_fam}
d_ok &= d2_ok
print(f"  [{'OK ' if d2_ok else 'ÉCH'}] D2 : M1 et M6 sont le même objet — "
      f"exp(iφH2)=bateman(φ) bit-exact ({ec_fam!r}, 720 pts), triple H_a²=I "
      f"bit-exact ({ec_sq!r}) ; la machinerie n'a jamais contenu d'objet étranger")

# ---------------------------------------------------------------- D3 — [MAPPING] doublage unique
caps = [2 * (2 * l + 1) for l in range(7)]
d3_ok = (ec_2t == 0.0) and (ec_tr <= TOL_C) and (ec_tr_theta <= TOL_C) \
    and (ec_mp <= TOL_MP) and caps == [2, 6, 10, 14, 18, 22, 26]
d3_mesure = {"deux_theta_moins_pi_alpha": ec_2t,
             "tr_R_U_theta": tr_theta,
             "ecart_tr_moins_1_plus_2cos_pi_alpha": ec_tr_theta,
             "R11_dps40": mp.nstr(R11, 30),
             "cos_pi_alpha_dps40": mp.nstr(ref_mp, 30),
             "ecart_mpmath": float(ec_mp),
             "caps_2l_plus_1": caps}
d_ok &= d3_ok
print(f"  [{'OK ' if d3_ok else 'ÉCH'}] D3 : [MAPPING] le doublage est unique — "
      f"2θ−πα = {ec_2t!r} (M1 C0b re-witness), tr R(U(θ)) = {tr_theta!r} = 1+2cos(πα), "
      f"mpmath dps40 ({mp.nstr(ec_mp, 5)}) ; doublage noyau→boucle (M5, ratio 0.5) = "
      f"doublage spinor→rotation (M7), témoinné trois fois (M1 C0b, M5 C4, M7 S5) ; "
      f"2(2l+1) == {caps}, (2l+1) NON dérivé, consigné")

# ---------------------------------------------------------------- verdict
verdict = "V4_REFUTE"
if ok_global and d_ok:
    verdict = "V+ M7_SO3_ADJOINT_FERME"
elif ok_global:
    verdict = "V2"
elif age_ok:
    verdict = "V3"

print("=" * 78)
print(f"  VERDICT : {verdict}")
print("=" * 78)

resultat = {
    "campagne": "M7 SO(3) ADJOINT V0 — la rotation géométrique sort du triple natif",
    "frontiere": FRONTIERE,
    "frontiere_commit": "0c6e762",
    "verdict": verdict,
    "ok_global": bool(ok_global),
    "controles": controles_log,
    "consequences": [
        {"consequence": "D1", "ok": bool(d1_ok), "mesure": d1_mesure,
         "detail": "le noyau est le centre est le deck : R(−U)=R(U) bit-exact (64 "
                   "composés), R(bateman(π))=I₃, bateman(φ+π)=−bateman(φ) — la "
                   "signature fermionique (σ(1)=−1, centre M6 D2) est EXACTEMENT la "
                   "fibre du recouvrement SU(2)→SO(3) ; deux tours du spinor = un "
                   "tour de l'espace, ruban de Dirac en forme machine"},
        {"consequence": "D2", "ok": bool(d2_ok), "mesure": d2_mesure,
         "detail": "M1 et M6 sont le même objet : exp(iφH2) = bateman(φ) bit-exact "
                   "(720 pts) et triple H_a²=I bit-exact — la famille déposée en M1 "
                   "C3 est le sous-groupe à un paramètre du triple natif M6"},
        {"consequence": "D3", "ok": bool(d3_ok), "mesure": d3_mesure,
         "detail": "[MAPPING] le doublage est unique : 2θ−πα = 0.0 bit-exact (M1 C0b "
                   "re-witness), tr R(U(θ)) = 1+2cos(πα) = 0.27525021983904013, "
                   "mpmath dps40 confirmé — le doublage noyau→boucle (M5, ratio 0.5) "
                   "et le doublage spinor→rotation (M7) sont le MÊME doublage, "
                   "témoinné trois fois (M1 C0b, M5 C4, M7 S5) ; table 2(2l+1) "
                   "inchangée, (2l+1) NON dérivé, consigné"},
    ],
    "route_consignee": "Rodrigues NON importé (angle témoinné par le bloc 2×2 natif et "
                       "par la trace, C6) ; surjectivité topologique SU(2)→SO(3) testée "
                       "sur la grille d'Euler 4³=64, non démontrée ; quaternions réels "
                       "NON construits ; R³ = espace du triple natif (trois axes H_a), "
                       "pas d'espace physique déposé ; g=2 hors portée ; j non dérivé "
                       "(M4 a73c116) ; (2l+1) non dérivé ; ħ=1 (convention M1) ; défaut "
                       "estimateur corrigé avant gel : signe du bloc 2×2, convention "
                       "native UσU† tranchée par machine (frontière §0)",
    "determinisme": "aucune graine, aucun aléa",
}

with open(SORTIE, "w", encoding="utf-8") as f:
    json.dump(resultat, f, ensure_ascii=False, indent=1)
print(f"JSON écrit : {SORTIE}")
sys.exit(0 if (ok_global and d_ok) else 1)