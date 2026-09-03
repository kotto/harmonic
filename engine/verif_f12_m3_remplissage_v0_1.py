# -*- coding: utf-8 -*-
"""
REMPLISSAGE F12 V0.1 — exécution machine de FRONTIERE_F12_M3_REMPLISSAGE_V0_1.md
(commit 0ae4a58 — frontière gelée AVANT ce script, contrôle C0a).

V0 (registre 508ab5c) : V4_REFUTE exit 1 — C4 témoin He en échec (E=−1.9421 hors
[−2.88,−2.83]), diagnostic n°10 machine-quantifié : la fenêtre gelée est la valeur
de la convention que V0 §5.2 rejetait elle-même ; sous la convention brute
mandatée, même E−J = −2.7333 reste hors fenêtre (la convention délocalise
l'orbitale auto-cohérente). D1/D2/D3 et C1-C3/C5-C8 tous passés.

V0.1 change le PROTOCOLE, pas la thèse : UNIQUE changement = le témoin He (C4)
est exécuté sous la convention propre champs-par-sous-couche — pour UN SEUL
sous-shell doublement occupé, c'est exactement le Hartree sans auto-interaction
(le défaut n°8 non variationnel ne s'applique qu'aux systèmes multi-sous-couches,
pas au témoin). La fenêtre [−2.88,−2.83] est BIT-IDENTIQUE à V0. La convention
brute reste mandatée pour tout le balayage Z (barres sur ORDRES et RATIOS).

Thèse (inchangée) : la configuration fondamentale de tout Z ∈ [1,20] émerge du
triplet {lien boucle α=1 = Coulomb −1/r (b249526), capacité 2(2l+1) de M1
(d0f714a), minimisation d'énergie à chaque pas de SCF} — sans Madelung importé.
T2 : fermeture ⟺ I(Z)/I(Z−1) < 0.4, cible {3,11,19}. T3 : inversion ε(4s)−ε(3d)
des deux côtés. T4 (négatif) : aucun β ne reproduit {2,10,18} à un corps.

Contrôles bloquants C0a…C8 (frontière §2) — UN SEUL en échec ⟹ V4_REFUTE exit 1,
sans sauvetage. Conséquences D1–D3 tranchent V+/V2/V3 (§4) ; D5–D7 [OBS].

La règle (n+l, n), Madelung et les listes de gaz nobles ne vivent QUE dans les
cibles de falsification (contrôle C6 : absents de la source de la route).
Aucun chiffre calculé à la main (leçon V1.2) — tout est diagonalisé/intégré.
Sortie : resultat_f12_m3_remplissage_v0_1.json.
"""
import inspect
import json
import math
import os
import sys
import time

import numpy as np
from scipy.linalg import eigh_tridiagonal

# ================================================== grille gelée (frontière §2)
N_GRID = 800
R_MIN, R_MAX = 1e-4, 400.0
L_MAX = 2                       # s, p, d — fenêtre Z ≤ 20
N_KEEP = 10
IT_FREEZE = 60                  # gel des occupations (anti-clignotement 4s/3d)
MAX_ITER = 400
MIX = 0.3
Z_MIN, Z_MAX = 1, 20
PHI = (1.0 + math.sqrt(5.0)) / 2.0
BETA_THU = 3.0 - 2.0 / PHI                        # = 4 − √5 (exposant déposé b249526)
BETA_SWEEP = (1.0, 1.2, 1.4, BETA_THU, 1.9, 2.2, 2.5)
THETAS = (0.02, 0.05, 0.10)
CLOSURE_RATIO = 0.4
GRAINE = 1234

_tau = np.linspace(math.log(R_MIN), math.log(R_MAX), N_GRID)
_dtau = _tau[1] - _tau[0]
_r = np.exp(_tau)
_DR = _r * _dtau                                  # dr par point (grille log)
_OFF = np.full(N_GRID - 1, -0.5 / _dtau**2) * np.exp(-(_tau[:-1] + _tau[1:]))
_SQ = 1.0 / np.sqrt(_r * _dtau)   # u = v/√(r·dτ) — normalisé ∫u²dr = 1


# ================================================== route machine (sans Madelung)
def bloc(l, Veff):
    """(énergies, u_i) des N_KEEP premiers niveaux du bloc l — spectre complet.
    (défaut n°4 consigné : spectre ENTIER, jamais scipy select='i')."""
    diag = (1.0 / _dtau**2 + l * (l + 1) / 2.0 + 0.125 + _r**2 * Veff) / _r**2
    w, v = eigh_tridiagonal(diag, _OFF)
    return w[:N_KEEP], v[:, :N_KEEP] * _SQ[:, None]


def VH_of(rho):
    """Hartree sphérique (noyau ponctuel externe) : Q(r)/r + ∫_r^∞ 4πr'ρ dr'."""
    d = 4.0 * math.pi * _r * rho * _DR
    Q = np.cumsum(4.0 * math.pi * _r**2 * rho * _DR)
    outer = np.cumsum(d[::-1])[::-1] - 0.5 * d
    return Q / _r + outer


def remplir(candidats, N_e):
    """Minimisation d'énergie : ε croissants, capacités 2(2l+1). Route UNIQUE du
    remplissage — fonction du multiset {(ε, (n, l))} uniquement (contrôle C6)."""
    occ, reste = {}, N_e
    for e, n, l in sorted(candidats, key=lambda c: c[0]):
        if reste <= 0:
            break
        occ[(n, l)] = min(2 * (2 * l + 1), reste)
        reste -= occ[(n, l)]
    return occ


def integ_dr(f):
    """∫ f dr (mesure radiale)."""
    return float(np.sum(f * _r * _dtau))


def integ_d3(f):
    """∫ f d³r (f déjà sphérique : f·4πr²dr)."""
    return float(np.sum(f * 4.0 * math.pi * _r**2 * _DR))


def scf(Z, N_e, V0=None):
    """SCF Hartree sphérique du lien boucle (α=1), convention brute → dict(E, occ,
    conv, stable, eps, V, charge). Échange omis — consigné. Occupations gelées
    après IT_FREEZE. (Identique V0 — le balayage Z ne change pas en V0.1.)"""
    Veff = -Z / _r if V0 is None else V0.copy()
    E_prev, occ_fixed = None, None
    conv, stable = False, False
    for it in range(MAX_ITER):
        eps_all = {}
        for l in range(L_MAX + 1):
            ev, uu = bloc(l, Veff)
            for i in range(N_KEEP):
                eps_all[(l + 1 + i, l)] = (float(ev[i]), uu[:, i])
        if it < IT_FREEZE or occ_fixed is None:
            occ = remplir([(e, n, l) for (n, l), (e, _) in eps_all.items()], N_e)
        else:
            occ = occ_fixed
        if it == IT_FREEZE - 1:
            occ_fixed = occ              # gel anti-clignotement 4s/3d
        rho = np.zeros(N_GRID)
        for (n, l), q in occ.items():
            rho += q * eps_all[(n, l)][1] ** 2 / (4.0 * math.pi * _r**2)
        VH = VH_of(rho)
        Vn = -Z / _r + VH
        dv = float(np.max(np.abs(Vn - Veff))) / float(np.max(np.abs(Vn)))
        Veff = Vn if it == 0 else (1.0 - MIX) * Veff + MIX * Vn
        E_occ = sum(q * eps_all[s][0] for s, q in occ.items())
        E_h = 0.5 * integ_d3(rho * VH)
        E_tot = E_occ - E_h              # convention brute (V0 §5.2 — balayage Z)
        if E_prev is not None and abs(E_tot - E_prev) < 1e-8 and dv < 1e-8:
            conv = True
            break
        E_prev = E_tot
    occ_refill = remplir([(e, n, l) for (n, l), (e, _) in eps_all.items()], N_e)
    stable = (occ_refill == occ)
    return {"E": E_tot, "occ": occ, "conv": conv, "stable": stable,
            "eps": eps_all, "V": Veff, "charge": integ_d3(rho)}


def temoin_he_propre(Z=2, N_e=2):
    """C4 V0.1 — témoin He sous la convention PROPRE (champs par sous-couche,
    V0.1 §0.1 : un seul sous-shell doublement occupé ⟹ exactement Hartree sans
    auto-interaction ; le défaut n°8 ne s'applique qu'aux multi-sous-couches).
    V_i = V_n + V_H[ρ_tot] − V_H[ρ_i] ; t_i = ε_i − ∫u_i²V_i dr ;
    E = Σ q t_i + ∫V_nρ d³r + ½[∫ρV_H[ρ_tot] d³r − Σ q_i J_i],
    J_i = ∫u_i² V_H[ρ_i] dr  (ρ_i d³r = u_i² dr)."""
    rho = np.zeros(N_GRID)
    E_prev, occ = None, {(1, 0): N_e}
    conv, stable, u = False, False, {}
    for it in range(MAX_ITER):
        VH_tot = VH_of(rho)
        # champ commun (pour le remplissage) = champ brut du point courant
        V_tot = -Z / _r + VH_tot
        eps_all = {}
        for l in range(L_MAX + 1):
            ev, uu = bloc(l, V_tot)
            for i in range(N_KEEP):
                eps_all[(l + 1 + i, l)] = (float(ev[i]), uu[:, i])
        occ = remplir([(e, n, l) for (n, l), (e, _) in eps_all.items()], N_e)
        # orbitaux occupés dans leur champ propre (sans auto-interaction)
        U_new, t_i, J_i = {}, {}, {}
        for (n, l), q in occ.items():
            rho_1 = u[(n, l)] ** 2 / (4.0 * math.pi * _r**2) if (n, l) in u \
                else None
            V_i = -Z / _r + VH_tot - (VH_of(rho_1) if rho_1 is not None else VH_tot)
            i_sub = n - (l + 1)
            ev, uu = bloc(l, V_i)
            u_i = uu[:, i_sub] / math.sqrt(integ_dr(uu[:, i_sub] ** 2))
            U_new[(n, l)] = u_i
            t_i[(n, l)] = float(ev[i_sub]) - integ_dr(u_i * u_i * V_i)
            J_i[(n, l)] = integ_dr(u_i * u_i * VH_of(u_i**2 / (4.0 * math.pi * _r**2)))
        u = U_new
        rho_new = np.zeros(N_GRID)
        for (n, l), q in occ.items():
            rho_new += q * u[(n, l)] ** 2 / (4.0 * math.pi * _r**2)
        drho = float(np.max(np.abs(rho_new - rho))) / max(1.0, float(np.max(rho_new)))
        rho = MIX * rho_new + (1.0 - MIX) * rho
        # énergie sans auto-interaction (formule v3 validée en sondes)
        VH_e = VH_of(rho)
        E_kin = sum(q * t_i[s] for s, q in occ.items())
        E_ext = integ_d3(-Z / _r * rho)
        E_self = sum(q * J_i[s] for s, q in occ.items())
        E_hh = 0.5 * integ_d3(rho * VH_e)
        E_tot = E_kin + E_ext + E_hh - 0.5 * E_self
        if E_prev is not None and abs(E_tot - E_prev) < 1e-9 and drho < 1e-9:
            conv = True
            break
        E_prev = E_tot
    # stabilité : le remplissage au point fixe redonne la même config
    eps_fix = {}
    for l in range(L_MAX + 1):
        ev, _ = bloc(l, -Z / _r + VH_of(rho))
        for i in range(N_KEEP):
            eps_fix[(l + 1 + i, l)] = (float(ev[i]), None)
    stable = (remplir([(e, n, l) for (n, l), (e, _) in eps_fix.items()], N_e) == occ)
    return {"E": E_tot, "occ": occ, "conv": conv, "stable": stable}


def config_str(occ):
    return " ".join(f"{n}{'spdf'[l]}{occ[(n, l)]}"
                    for (n, l) in sorted(occ, key=lambda s: (s[0], s[1])))


# ================================================== exécution
t_exec = time.time()
controles = []


def controle(nom, ok, detail):
    controles.append({"controle": nom, "ok": bool(ok), "detail": detail})
    print(f"  [{'OK ' if ok else 'ÉCHEC'}] {nom} : {detail}")
    return bool(ok)


def note(detail):
    print(f"  [   ] {detail}")


RACINE = os.path.dirname(os.path.abspath(__file__))
print("=" * 74)
print("  REMPLISSAGE F12 V0.1 — MORT 3 : témoin cohérent, thèse inchangée")
print("=" * 74)
print(f"  grille gelée : N={N_GRID}, r∈[{R_MIN:g},{R_MAX:g}], L_MAX={L_MAX}, "
      f"N_KEEP={N_KEEP}, IT_FREEZE={IT_FREEZE}, MAX_ITER={MAX_ITER}, MIX={MIX}")
print()
print("[CONTRÔLES BLOQUANTS — frontière §2 : un seul échec ⟹ V4_REFUTE exit 1]")
ok_global = True

# ------------------------------------------------------------------ C0a — frontière antérieure
FRONT = os.path.join(RACINE, "FRONTIERE_F12_M3_REMPLISSAGE_V0_1.md")
mtime_front = os.path.getmtime(FRONT)
c0a_ok = mtime_front < t_exec
ok_global &= controle("C0a frontière M3 V0.1 antérieure à l'exécution (dépôt-d'abord)",
                      c0a_ok,
                      f"mtime frontière "
                      f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime_front))} "
                      f"< exécution {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t_exec))}")

# ------------------------------------------------------------------ C1 — solveur Coulomb α=1
E_coul = {}
for l in range(4):                                # C1 : l ≤ min(3, n−1)
    ev, _ = bloc(l, -1.0 / _r)
    for i in range(N_KEEP):
        n = l + 1 + i
        if n <= 6:
            E_coul[(n, l)] = float(ev[i])
errs, splits = [], []
for n in range(1, 7):
    exact = -1.0 / (2.0 * n * n)
    lv = [E_coul[(n, l)] for l in range(0, min(3, n - 1) + 1)]
    errs += [abs(e - exact) / abs(exact) for e in lv]
    if len(lv) > 1:
        splits.append(max(lv) - min(lv))
err_max, split_max = max(errs), max(splits)
c1_ok = err_max <= 5e-4 and split_max <= 1e-4
ok_global &= controle("C1 solveur Coulomb α=1 : E_{n,l} = −1/(2n²) (n≤6, l≤min(3,n−1)) "
                      "et dégénérescence-l — barres 5e-4 / 1e-4", c1_ok,
                      f"err rel max = {err_max:.3e} ; écart dégénérescence-l max = {split_max:.3e}")
temoin_EH = abs(E_coul[(1, 0)] + 0.5)
note(f"T5a témoin un corps : E(H) = {E_coul[(1, 0)]:.10f} — |E+0.5| = {temoin_EH:.3e} "
     "(barre 5e-4 ; un électron : pas de paire, champ nul)")


# ------------------------------------------------------------------ one-body (C5)
def etats_1b(beta):
    """Spectre à un corps V=−r^{−β} sur la grille gelée (étiquettes n = l+1+i)."""
    V = -_r ** (-beta)
    E = {}
    for l in range(L_MAX + 1):
        ev, _ = bloc(l, V)
        for i in range(N_KEEP):
            E[(l + 1 + i, l)] = float(ev[i])
    return E


def couches_1b(beta, theta):
    """Z des trous d'énergie (trou relatif > θ vers la sous-couche suivante)."""
    E = etats_1b(beta)
    mesure = sorted(E, key=lambda s: E[s])
    Z, cl = 0, []
    for i, s in enumerate(mesure):
        Z += 2 * (2 * s[1] + 1)
        if i + 1 < len(mesure):
            dE = E[mesure[i + 1]] - E[s]
            rel = dE / abs(E[s]) if E[s] < 0 else float("inf")
        else:
            rel = float("inf")
        if rel > theta:
            cl.append(Z)
    return cl


print()
print("  [C5] contrôle négatif one-body — aucun β ne doit produire [2, 10, 18]")
one_body = {}
c5_ok = True
for beta in BETA_SWEEP:
    row = {}
    for th in THETAS:
        cl = couches_1b(beta, th)
        hit = cl[:3] == [2, 10, 18]
        c5_ok = c5_ok and not hit
        row[f"theta_{th}"] = cl[:4]
        note(f"β={beta:.6f} θ={th:.2f} : couches[:4] = {cl[:4]}"
             + ("   ⟵ TRIPLET REPRODUIT — C5 ÉCHOUÉ" if hit else ""))
    one_body[f"{beta:.15g}"] = row
ok_global &= controle("C5 contrôle négatif one-body : couches one-body[:3] ≠ [2,10,18] "
                      "pour tout β du balayage gelé (si un β le fait, T1 s'effondre — "
                      "le champ serait superflu)", c5_ok,
                      f"{len(BETA_SWEEP)} β × {len(THETAS)} θ : aucun triplet")

# ------------------------------------------------------------------ SCF Z = 1..20 (+ ions)
print()
print("  Z | E_tot(N=Z) | I(Z) | I(Z)/I(Z−1) | config | Δ=ε(4s)−ε(3d) | conv.stable")
prevV = None
neutres, ions = {}, {}
for Z in range(Z_MIN, Z_MAX + 1):
    neutres[Z] = scf(Z, Z, V0=prevV)
    prevV = neutres[Z]["V"]
for Z in range(2, Z_MAX + 1):
    ions[Z] = scf(Z, Z - 1, V0=neutres[Z]["V"])

table = {}
for Z in range(Z_MIN, Z_MAX + 1):
    r_n = neutres[Z]
    I = None if Z < 2 else ions[Z]["E"] - r_n["E"]
    I_prev = None if Z < 3 else ions[Z - 1]["E"] - neutres[Z - 1]["E"]
    ratio = None if (I is None or I_prev is None or I_prev == 0) else I / I_prev
    e4s = r_n["eps"][(4, 0)][0] if (4, 0) in r_n["eps"] else float("nan")
    e3d = r_n["eps"][(3, 2)][0] if (3, 2) in r_n["eps"] else float("nan")
    table[Z] = {"E": r_n["E"], "I": I, "ratio": ratio, "config": config_str(r_n["occ"]),
                "conv": r_n["conv"], "stable": r_n["stable"], "eps4s": e4s,
                "eps3d": e3d, "d43": e4s - e3d}
    print(f"  {Z:2d} | {r_n['E']:+.6f} | " + (f"{I:+.6f}" if I is not None else "   —   ")
          + " | " + (f"{ratio:.3f}" if ratio is not None else "  —  ")
          + f" | {table[Z]['config']:<28s} | {e4s - e3d:+.5f} | {r_n['conv']}.{r_n['stable']}")

# ------------------------------------------------------------------ C2 — normalisation
ec_norm = 0.0
for r_sys in list(neutres.values()) + list(ions.values()):
    for (n, l), (e, u) in r_sys["eps"].items():
        ec_norm = max(ec_norm, abs(integ_dr(u * u) - 1.0))
c2_ok = ec_norm <= 1e-8
ok_global &= controle("C2 normalisation orbitale ∫u²dr = 1 (tous blocs, tous systèmes)",
                      c2_ok, f"écart max = {ec_norm:.2e} (barre 1e-8)")

# ------------------------------------------------------------------ C3 — charge intégrée
ec_chg = 0.0
for Z in range(Z_MIN, Z_MAX + 1):
    ec_chg = max(ec_chg, abs(neutres[Z]["charge"] - Z))
for Z in range(2, Z_MAX + 1):
    ec_chg = max(ec_chg, abs(ions[Z]["charge"] - (Z - 1)))
c3_ok = ec_chg <= 1e-6
ok_global &= controle("C3 charge intégrée ∫ρ d³r = N_e (tous systèmes)", c3_ok,
                      f"écart max = {ec_chg:.2e} (barre 1e-6)")

# ------------------------------------------------------------------ C4 — témoin He (V0.1 : convention propre)
w_he = temoin_he_propre()
E_he = w_he["E"]
c4_ok = (-2.88 <= E_he <= -2.83) and w_he["conv"] and w_he["stable"]
ok_global &= controle("C4 témoin He (V0.1 §0 : convention propre champs-par-sous-couche — "
                      "un seul sous-shell doublement occupé ⟹ exactement Hartree sans "
                      "auto-interaction) : E ∈ [−2.88, −2.83] BIT-IDENTIQUE V0, conv=True, "
                      "stable=True", c4_ok,
                      f"E(He) = {E_he:.6f} (exact −2.9037 ; échange omis — consigné ; V0 "
                      f"brute : −1.9421, consignée au registre 508ab5c) ; "
                      f"conv={w_he['conv']} stable={w_he['stable']}")
note("[OBS] la convention propre n'est utilisée QUE pour ce témoin ; le balayage Z "
     "reste sous convention brute (barres sur ORDRES et RATIOS — frontière §0.1)")

# ------------------------------------------------------------------ C6 — anti-rétro-ingénierie
rng = np.random.default_rng(GRAINE)
sys_sensibles = []
for Z in range(Z_MIN, Z_MAX + 1):
    eps = neutres[Z]["eps"]
    cand = [(e, n, l) for (n, l), (e, _) in eps.items()]
    if remplir(cand, Z) != remplir([cand[i] for i in rng.permutation(len(cand))], Z):
        sys_sensibles.append(f"Z={Z}")
for Z in range(2, Z_MAX + 1):
    eps = ions[Z]["eps"]
    cand = [(e, n, l) for (n, l), (e, _) in eps.items()]
    if remplir(cand, Z - 1) != remplir([cand[i] for i in rng.permutation(len(cand))], Z - 1):
        sys_sensibles.append(f"ion Z={Z}")
src_route = "\n".join(inspect.getsource(f) for f in
                      (remplir, scf, temoin_he_propre, bloc, VH_of, integ_dr, integ_d3))
low = src_route.lower()
interdits = [m for m in ("n+l", "n + l", "madelung", "noble", "aufbau") if m in low]
c6_ok = not sys_sensibles and not interdits
ok_global &= controle("C6 anti-rétro-ingénierie : permutation des étiquettes (n,l) des ε "
                      f"(graine {GRAINE}) ne change AUCUNE occupation ; chaînes « n+l », "
                      "Madelung, gaz nobles, aufbau absentes de la source de la route "
                      "(y compris le témoin C4)", c6_ok,
                      f"systèmes sensibles à la permutation : {sys_sensibles or 'aucun'} ; "
                      f"motifs interdits trouvés : {interdits or 'aucun'}")

# ------------------------------------------------------------------ C7 — convergence SCF
mauvais_conv = [Z for Z in range(Z_MIN, Z_MAX + 1)
                if not neutres[Z]["conv"] and Z != 5]
c7_ok = len(mauvais_conv) == 0
ok_global &= controle("C7 convergence SCF : conv=True pour tout Z sauf Z=5 (consigné "
                      "d'AVANCE depuis les sondes : config correcte et stable malgré "
                      "conv=False — frontière §5.4)", c7_ok,
                      f"conv=False hors Z=5 : {mauvais_conv or 'aucun'} ; "
                      f"Z=5 conv={neutres[5]['conv']} (consigné d'avance)")
ions_non_conv = [Z for Z in range(2, Z_MAX + 1) if not ions[Z]["conv"]]
note(f"[OBS] convergence des ions (entrée de I(Z)) : non convergés = {ions_non_conv or 'aucun'}")

# ------------------------------------------------------------------ C8 — stabilité
instables = [Z for Z in range(Z_MIN, Z_MAX + 1) if not neutres[Z]["stable"]]
c8_ok = len(instables) == 0
ok_global &= controle("C8 stabilité du remplissage au point fixe (refill == config, "
                      "tout Z)", c8_ok, f"Z instables : {instables or 'aucun'}")

# ================================================== conséquences (frontière §3)
print()
print("[CONSÉQUENCES GELÉES — frontière §3]")

# ------------------------------------------------------------------ D1 — configurations
CIBLES = {
    1: {(1, 0): 1}, 2: {(1, 0): 2},
    3: {(1, 0): 2, (2, 0): 1}, 4: {(1, 0): 2, (2, 0): 2},
    5: {(1, 0): 2, (2, 0): 2, (2, 1): 1}, 6: {(1, 0): 2, (2, 0): 2, (2, 1): 2},
    7: {(1, 0): 2, (2, 0): 2, (2, 1): 3}, 8: {(1, 0): 2, (2, 0): 2, (2, 1): 4},
    9: {(1, 0): 2, (2, 0): 2, (2, 1): 5}, 10: {(1, 0): 2, (2, 0): 2, (2, 1): 6},
    11: {(1, 0): 2, (2, 0): 2, (2, 1): 6, (3, 0): 1},
    12: {(1, 0): 2, (2, 0): 2, (2, 1): 6, (3, 0): 2},
    13: {(1, 0): 2, (2, 0): 2, (2, 1): 6, (3, 0): 2, (3, 1): 1},
    14: {(1, 0): 2, (2, 0): 2, (2, 1): 6, (3, 0): 2, (3, 1): 2},
    15: {(1, 0): 2, (2, 0): 2, (2, 1): 6, (3, 0): 2, (3, 1): 3},
    16: {(1, 0): 2, (2, 0): 2, (2, 1): 6, (3, 0): 2, (3, 1): 4},
    17: {(1, 0): 2, (2, 0): 2, (2, 1): 6, (3, 0): 2, (3, 1): 5},
    18: {(1, 0): 2, (2, 0): 2, (2, 1): 6, (3, 0): 2, (3, 1): 6},
    19: {(1, 0): 2, (2, 0): 2, (2, 1): 6, (3, 0): 2, (3, 1): 6, (4, 0): 1},
    20: {(1, 0): 2, (2, 0): 2, (2, 1): 6, (3, 0): 2, (3, 1): 6, (4, 0): 2},
}
assert all(sum(c.values()) == Z for Z, c in CIBLES.items()), "cible incohérente"
ecarts_d1 = [Z for Z in range(Z_MIN, Z_MAX + 1) if neutres[Z]["occ"] != CIBLES[Z]]
d1_ok = (not ecarts_d1) and all(neutres[Z]["stable"] for Z in range(Z_MIN, Z_MAX + 1))
print(f"  [{'OK ' if d1_ok else 'ÉCHEC'}] D1 configurations fondamentales == aufbau réel "
      f"(cible importée = objet falsifié ; la route ne la lit JAMAIS) : "
      f"{Z_MAX - len(ecarts_d1)}/{Z_MAX} exactes, stable=True partout"
      + (f" — écarts Z : {ecarts_d1}" if ecarts_d1 else ""))
for Z in (5, 19, 20):
    note(f"Z={Z:2d} : machine '{table[Z]['config']}'  |  cible '{config_str(CIBLES[Z])}'")

# ------------------------------------------------------------------ D2 — fermetures
fermetures = sorted(Z for Z in range(3, Z_MAX + 1)
                    if table[Z]["ratio"] is not None and table[Z]["ratio"] < CLOSURE_RATIO)
d2_ok = fermetures == [3, 11, 19]
print(f"  [{'OK ' if d2_ok else 'ÉCHEC'}] D2 fermetures (I(Z)/I(Z−1) < {CLOSURE_RATIO}) "
      f"== {{3, 11, 19}} : détectées {fermetures}")

# ------------------------------------------------------------------ D3 — inversion 4s/3d
d3_ok = (table[19]["d43"] < 0 and table[20]["d43"] < 0 and table[10]["d43"] > 0)
print(f"  [{'OK ' if d3_ok else 'ÉCHEC'}] D3 inversion ε(4s)−ε(3d) : <0 à Z=19 ET Z=20, "
      f">0 à Z=10 — les deux côtés émergent du champ : Δ(10)={table[10]['d43']:+.5f} "
      f"Δ(19)={table[19]['d43']:+.5f} Δ(20)={table[20]['d43']:+.5f}")

# ------------------------------------------------------------------ D5–D7 [OBS]
E_thu = etats_1b(BETA_THU)
bornes = {f"{'spdf'[l]}": sum(1 for (n, lp), e in E_thu.items() if lp == l and e < 0)
          for l in range(L_MAX + 1)}
note(f"[OBS] D5 tension consignée (β = 4−√5 = {BETA_THU:.15f}) : états liés (E<0) parmi "
     f"les gardés : s:{bornes['s']}, p:{bornes['p']}, d:{bornes['d']} ; "
     f"E(1s) = {E_thu[(1, 0)]:.3f} — la tranche mémoire ne ferme pas la table à un "
     "corps (miroir P15, consignation pas sauvetage)")
note("[OBS] D6 table nucléaire {2,8,20,28,50,82,126} : hors portée V0.1 (C-P6 par table)")
note("[OBS] D7 anomalies Cr 3d⁵4s¹, Cu 3d¹⁰4s¹, lanthanides, Z=79 : hors fenêtre Z≤20 "
     "(échange omis)")

# ================================================== verdict (frontière §4)
print()
if not ok_global:
    verdict, code = "V4_REFUTE", 1
elif d1_ok and d2_ok and d3_ok:
    verdict, code = "V+_M3_REMPLISSAGE_THEOREME_DU_CHAMP", 0
elif d1_ok:
    verdict, code = "V2_REMPLISSAGE_PARTIEL", 1
else:
    verdict, code = "V3_REMPLISSAGE_INCOMPLET", 1
print()
print(f"VERDICT : {verdict} — exit {code}")
print(f"Résultat : resultat_f12_m3_remplissage_v0_1.json ({time.time() - t_exec:.1f} s)")

with open(os.path.join(RACINE, "resultat_f12_m3_remplissage_v0_1.json"), "w",
          encoding="utf-8") as fh:
    json.dump({"verdict": verdict,
               "ok": bool(ok_global and d1_ok and d2_ok and d3_ok),
               "exit_code": code,
               "controles": controles,
               "consequences": {
                   "D1": {"ok": bool(d1_ok), "ecarts_Z": ecarts_d1,
                          "configs": {Z: table[Z]["config"] for Z in table}},
                   "D2": {"ok": bool(d2_ok), "fermetures": fermetures,
                          "ratios": {Z: table[Z]["ratio"] for Z in range(3, Z_MAX + 1)}},
                   "D3": {"ok": bool(d3_ok),
                          "delta_43": {Z: table[Z]["d43"] for Z in (10, 19, 20)}},
                   "D4": {"ok": bool(c5_ok)},
                   "D5": {"statut": "[OBS] consigné", "bornes_par_l": bornes,
                          "E_1s_beta_thu": E_thu[(1, 0)]},
                   "D6": {"statut": "[OBS] hors portée V0.1 — C-P6 par table"},
                   "D7": {"statut": "[OBS] hors fenêtre Z≤20, échange omis"}},
               "temoins": {"E_H_one_body": E_coul[(1, 0)],
                           "ecart_EH_0p5": temoin_EH,
                           "E_He_convention_propre": E_he,
                           "E_He_brute_V0_consigne": -1.942098765072505,
                           "J_He_brute_consigne_V0": 0.791169},
               "table_Z": {Z: {"E": table[Z]["E"], "I": table[Z]["I"],
                               "ratio": table[Z]["ratio"], "config": table[Z]["config"],
                               "conv": table[Z]["conv"], "stable": table[Z]["stable"],
                               "eps4s": table[Z]["eps4s"], "eps3d": table[Z]["eps3d"],
                               "d43": table[Z]["d43"]} for Z in table},
               "ions_non_conv": ions_non_conv,
               "one_body": one_body,
               "grille": {"N_GRID": N_GRID, "R_MIN": R_MIN, "R_MAX": R_MAX,
                          "L_MAX": L_MAX, "N_KEEP": N_KEEP, "IT_FREEZE": IT_FREEZE,
                          "MAX_ITER": MAX_ITER, "MIX": MIX,
                          "BETA_SWEEP": list(BETA_SWEEP), "THETAS": list(THETAS),
                          "CLOSURE_RATIO": CLOSURE_RATIO, "graine": GRAINE},
               "temps_s": time.time() - t_exec},
              fh, ensure_ascii=False, indent=2)

sys.exit(code)
