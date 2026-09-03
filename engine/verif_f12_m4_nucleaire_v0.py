# -*- coding: utf-8 -*-
"""
VERIF F12 — M4 : LES NOMBRES MAGIQUES NUCLÉAIRES V0
(FRONTIERE_F12_M4_NUCLEAIRE_V0.md, commit 8a27c74 — dépôt-d'abord C0a)

Cible : table nucléaire {2, 8, 20, 28, 50, 82, 126}, critère maître C-P6 :
« les deux tables de nombres magiques sortent du même couple, ou l'échec
est consigné par table ». Table atomique : fermée (M3 V0.1, a1048a1).

Échelle de verdict (gelée) :
  V+  M4_NUCLEAIRE_TRANCHES_CONSIGNÉES : C0a–C8 tous OK ET D1 ET D2 ET D4
  V2_PARTIEL   : un de D1/D2/D4 en échec partiel
  V3_INCOMPLET : contrôles OK, conséquence invérifiable (non déclenchable ici :
                 toutes les conséquences sont mesurées)
  V4_REFUTE    : UN SEUL contrôle en échec -> exit 1, aucun sauvetage

Historique estimateur (leçon V1.2 — le verif est bugable) :
  - 3 défauts de la campagne de sondes consignés dans la frontière (KeyError
    ensemble/N_KEEP, normalisation u fausse au premier essai, boucle lisant le
    nom au lieu de la clé) — corrigés AVANT tout gel, aucun ne touche la route.
  - Le présent verif réutilise la machinerie M3 (a1048a1) généralisée à V(r)
    quelconque : grille log symétrisée, spectre ENTIER (jamais select='i'),
    étiquette n = l+1+i, normalisation u = v/√(r·dτ).

Grille gelée : N=800, r∈[1e-4,400] log, L_MAX=6, N_KEEP=16, N_MAX=14,
familles EXP/YUK1/YUKPHI/GAUSS, BETAS (20,50,100,200,400),
MUS (0.5,1.0,1/φ,3.0), THETAS (0.02,0.05,0.10), capacité 2(2l+1), skip < 6 liés.
Tout est diagonalisé : aucun chiffre à la main.
"""
import json
import math
import os
import sys
import time

import numpy as np
from scipy.linalg import eigh_tridiagonal

# ---- constantes de la grille gelée (frontière §5) ----
PHI = (1.0 + math.sqrt(5.0)) / 2.0
ALPHA = 1.0 / PHI

N_GRID = 800
R_MIN, R_MAX = 1e-4, 400.0
N_KEEP = 16                            # ≥ N_MAX : chaque état de ensemble() doit exister
L_MAX = 6                              # 1i (l=6) requis pour viser 126
N_MAX = 14

BETAS = (20.0, 50.0, 100.0, 200.0, 400.0)
MUS = (0.5, 1.0, 1.0 / PHI, 3.0)
THETAS = (0.02, 0.05, 0.10)
POW_BETAS = (1.0, 1.2, 1.4, 4.0 - math.sqrt(5.0), 1.9, 2.2, 2.5)

# ---- la CIBLE vit ICI, HORS de la route (anti-rétro C4) ----
CIBLE_NUC = (2, 8, 20, 28, 50, 82, 126)
CIBLE_PERTURBEE = tuple(3 * z for z in CIBLE_NUC)     # cible ×3 (contrôle C4)


# ==== ROUTE-BEGIN ====
def bloc_energies(l, V, N=N_GRID, rmin=R_MIN, rmax=R_MAX, k=N_KEEP):
    """Niveaux du bloc l : grille log symétrisée (u = e^{τ/2} v),
    eigh_tridiagonal sur le spectre ENTIER (jamais select='i')."""
    tau = np.linspace(math.log(rmin), math.log(rmax), N)
    dtau = tau[1] - tau[0]
    r = np.exp(tau)
    diag = (1.0 / dtau**2 + l * (l + 1) / 2.0 + 0.125) / r**2 + V(r)
    off = np.full(N - 1, -0.5 / dtau**2) * np.exp(-(tau[:-1] + tau[1:]))
    evals = eigh_tridiagonal(diag, off, eigvals_only=True)
    return evals[:k]


def etats(V, N=N_GRID, rmin=R_MIN, rmax=R_MAX):
    """(n,l) -> E, étiquette n = l+1+i."""
    E = {}
    for l in range(L_MAX + 1):
        ev = bloc_energies(l, V, N, rmin, rmax)
        for i, e in enumerate(ev):
            n = l + 1 + i
            if n <= N_MAX:
                E[(n, l)] = float(e)
    return E


def ensemble():
    return [(n, l) for n in range(1, N_MAX + 1) for l in range(min(L_MAX, n - 1) + 1)]


def cap(s, double=True):
    return (2 * (2 * s[1] + 1)) if double else (2 * s[1] + 1)


def nom(s):
    return f"{s[0]}{'spdfghi'[s[1]]}"


def remplissage(E, st, double=True):
    """Ordre par énergie, cumul Z, trou relatif vers la sous-couche suivante."""
    mesure = sorted(st, key=lambda s: E[s])
    Z, lignes = 0, []
    for i, s in enumerate(mesure):
        Z += cap(s, double)
        if i + 1 < len(mesure):
            dE = E[mesure[i + 1]] - E[s]
            rel = dE / abs(E[s]) if E[s] < 0 else float('inf')
        else:
            rel = float('inf')
        lignes.append((nom(s), Z, E[s], rel))
    return mesure, lignes


def couches(lignes, theta):
    return [z for (_, z, _, rel) in lignes if rel > theta]


def prefix_match(cl, ref):
    return sum(1 for a, b in zip(cl, ref) if a == b)


def V_yukawa(beta, mu, alpha=1.0):
    expo = 3.0 - 2.0 * alpha            # 1 à α=1 ; √5-4 à α=1/φ
    return lambda r: -beta * np.power(r, -expo) * np.exp(-mu * r)


def V_exp(beta, mu):
    return lambda r: -beta * np.exp(-mu * r)


def V_gauss(beta, mu):
    ell = 1.0 / mu
    return lambda r: -beta * np.exp(-0.5 * (r / ell) ** 2)


def V_pow(beta, expo):
    return lambda r: -beta * np.power(r, -expo)
# ==== ROUTE-END ====


FAMILLES = {
    "EXP":    lambda b, m: V_exp(b, m),
    "YUK1":   lambda b, m: V_yukawa(b, m, 1.0),
    "YUKPHI": lambda b, m: V_yukawa(b, m, ALPHA),
    "GAUSS":  lambda b, m: V_gauss(b, m),
}

ST = ensemble()
HERE = os.path.dirname(os.path.abspath(__file__))
FRONTIERE = os.path.join(HERE, "FRONTIERE_F12_M4_NUCLEAIRE_V0.md")
JSON_OUT = os.path.join(HERE, "resultat_f12_m4_nucleaire_v0.json")

# ---- barres gelées (frontière §0/§2, commit 8a27c74) ----
C1_ERR_BARRE = 5e-4
C1_DEGEN_BARRE = 1e-4
C2_BARRE = 1e-8
C6_BARRE = 1e-3

LIVRE_PAIRES_EXEC = 74
LIVRE_EXEC_THETA = 222
LIVRE_SKIPS_GEL = [("EXP", 20.0, 3.0, 1), ("EXP", 50.0, 3.0, 3),
                   ("YUK1", 20.0, 3.0, 3),
                   ("GAUSS", 20.0, 3.0, 1), ("GAUSS", 50.0, 3.0, 3),
                   ("GAUSS", 100.0, 3.0, 5)]        # (famille, β, μ, n_lie<6)
POW_EXEC_GEL = 21

N_T1_GEL = 49
N_28_GEL = 0
N_28_POW_GEL = 0
N_28_ANY_GEL = 77                        # D3 [OBS]

TEMOIN_CL = {0.02: [2, 8, 10, 20, 26, 40, 42, 52],
             0.05: [2, 8, 10, 20, 26, 40, 42, 52],
             0.10: [2, 8, 20, 26, 52, 76, 124, 148]}
TEMOIN_N_LIE = 38
TEMOIN_SOUS_COUCHES = [                  # (nom, Z, E) — bit-exact §0
    ("1s", 2, -12.361853911474865),
    ("2p", 8, -9.502016008249676),
    ("2s", 10, -7.896570023407332),
    ("3d", 20, -7.274633752315349),
    ("3p", 26, -6.11937352055374),
    ("4f", 40, -5.464658408113621),
    ("3s", 42, -5.011714775602838),
    ("4d", 52, -4.613926449951774),
    ("5g", 70, -3.9665175490208586),
    ("4p", 76, -3.7997658918069526),
    ("5f", 90, -3.3443109436814504),
    ("4s", 92, -3.0234478331815207),
]

CAP_DOUBLE_FALSE = [1, 4, 5, 8, 13, 14]
CAP_DOUBLE_TRUE = [2, 8, 10, 16, 26, 28]

SEQ_COULOMB = [2, 10, 28, 60, 110, 182, 280]
SEQ_YUKPHI = [2, 8, 18, 32, 50, 52, 58, 68]
SEQ_GAUSS = [2, 8, 20, 40, 70, 112, 168, 210]

TEMOIN_T1_SEQ = [2, 8, 20, 26, 52, 76, 124]
D5_SEQ = [2, 8, 10, 20, 26, 28, 42]

# motifs interdits dans la source de la route (anti-rétro C4)
MOTIFS_INTERDITS = ["28", "50", "82", "126", "MAGIQUE", "CIBLE", "cible",
                    "2, 8, 20"]


def scan_motifs_route():
    src = open(os.path.abspath(__file__), encoding="utf-8").read()
    a = src.index("# ==== ROUTE-BEGIN ====")
    b = src.index("# ==== ROUTE-END ====")
    route = src[a:b]
    presentes = [m for m in MOTIFS_INTERDITS if m in route]
    return (len(presentes) == 0), presentes


def passe_grille(cible, cible_any):
    """La route complète sur la grille : diagonalisations, remplissage,
    fermetures. La cible n'entre QUE dans le comptage des correspondances."""
    n_t1 = n_28 = n_any = 0
    n_exec = 0
    skips = []
    t1_cfg = []
    fermetures = {}
    best_pm, best_desc = 0, None
    for fam, gen in FAMILLES.items():
        for b in BETAS:
            for m in MUS:
                E = etats(gen(b, m))
                n_lie = len([s for s in ST if E[s] < 0])
                if n_lie < 6:
                    skips.append((fam, b, m, n_lie))
                    continue
                n_exec += 1
                _, lignes = remplissage(E, ST)
                for th in THETAS:
                    clt = couches(lignes, th)
                    fermetures[f"{fam}|{b}|{m}|{th}"] = clt
                    pm = prefix_match(clt, cible)
                    if pm > best_pm:
                        best_pm, best_desc = pm, f"{fam} β={b} μ={m} θ={th} → {clt[:8]}"
                    if clt[:3] == list(cible[:3]):
                        n_t1 += 1
                        t1_cfg.append((fam, b, m, th, clt[:7]))
                    if clt[:4] == list(cible[:4]):
                        n_28 += 1
                    if any(z in clt for z in cible_any):
                        n_any += 1
    return dict(n_t1=n_t1, n_28=n_28, n_any=n_any, n_exec=n_exec, skips=skips,
                t1_cfg=t1_cfg, fermetures=fermetures, best_pm=best_pm,
                best_desc=best_desc)


def main():
    t0 = time.time()
    run_start = time.time()
    print("VERIF F12 — M4 NOMBRES MAGIQUES NUCLÉAIRES V0 "
          "(frontière gelée 8a27c74, dépôt-d'abord)")
    print(f"cible nucléaire : {list(CIBLE_NUC)} ; cible perturbée (C4) : {list(CIBLE_PERTURBEE)}")
    controles = {}
    cons = {}

    # ---------- C0a : antériorité du dépôt ----------
    mt = os.path.getmtime(FRONTIERE)
    controles["C0a"] = dict(
        ok=bool(mt < run_start), mesure=mt, barre=f"< {run_start}",
        detail="getmtime(FRONTIERE_F12_M4_NUCLEAIRE_V0.md) < début d'exécution")

    # ---------- C1 : solveur Coulomb α=1 ----------
    E0 = etats(V_yukawa(1.0, 0.0, 1.0))
    errs, splits = [], []
    for n in range(1, 7):
        exact = -1.0 / (2.0 * n * n)
        lvals = [E0[(n, l)] for l in range(0, min(L_MAX, n - 1) + 1)]
        errs += [abs(e - exact) / abs(exact) for e in lvals]
        if len(lvals) > 1:
            splits.append(max(lvals) - min(lvals))
    err_max, degen_max = max(errs), max(splits)
    controles["C1"] = dict(
        ok=bool(err_max <= C1_ERR_BARRE and degen_max <= C1_DEGEN_BARRE),
        mesure=[err_max, degen_max], barre=[C1_ERR_BARRE, C1_DEGEN_BARRE],
        detail="Coulomb α=1, n≤6, l≤6 : err rel E=-1/(2n²) et dégénérescence-l")

    # ---------- C2 : normalisation u = v/√(r·dτ) ----------
    tau = np.linspace(math.log(R_MIN), math.log(R_MAX), N_GRID)
    dtau = tau[1] - tau[0]
    r = np.exp(tau)
    diag = (1.0 / dtau**2 + 6 * 7 / 2.0 + 0.125) / r**2 + (-np.exp(-r))
    off = np.full(N_GRID - 1, -0.5 / dtau**2) * np.exp(-(tau[:-1] + tau[1:]))
    _, vecs = eigh_tridiagonal(diag, off)
    u0 = vecs[:, 0] / np.sqrt(r * dtau)
    nrm = math.sqrt(float(np.sum(u0 * u0 * r * dtau)))
    controles["C2"] = dict(
        ok=bool(abs(nrm - 1.0) <= C2_BARRE), mesure=nrm, barre=C2_BARRE,
        detail="∫u²dr=1, bloc l=6, fond, V=-e^{-r} (convention M3 a1048a1)")

    # ---------- C3 : livre de la grille + comptages T1/T2 (passe gelée) ----------
    print("\n[C3] passe de grille (cible gelée) …")
    g1 = passe_grille(CIBLE_NUC, (28,))
    livre_ok = (g1["n_exec"] == LIVRE_PAIRES_EXEC
                and 3 * g1["n_exec"] == LIVRE_EXEC_THETA
                and g1["skips"] == LIVRE_SKIPS_GEL)
    # famille puissance (complétude M2)
    n_28_pow, pow_exec = 0, 0
    for b in POW_BETAS:
        E = etats(V_pow(b, b))
        if len([s for s in ST if E[s] < 0]) < 6:
            continue
        _, lignes = remplissage(E, ST)
        for th in THETAS:
            pow_exec += 1
            if couches(lignes, th)[:4] == [2, 8, 20, 28]:
                n_28_pow += 1
    livre_ok = livre_ok and (pow_exec == POW_EXEC_GEL)
    controles["C3"] = dict(
        ok=bool(livre_ok),
        mesure=dict(paires_exec=g1["n_exec"], exec_theta=3 * g1["n_exec"],
                    skips=g1["skips"], pow_exec=pow_exec),
        barre=dict(paires_exec=LIVRE_PAIRES_EXEC, exec_theta=LIVRE_EXEC_THETA,
                   skips=LIVRE_SKIPS_GEL, pow_exec=POW_EXEC_GEL),
        detail="livre de grille : comptages et skips == déposés (égalité exacte)")
    print(f"    paires exécutées {g1['n_exec']}/80 → {3*g1['n_exec']} configs θ ; "
          f"skips {[(f, b, m, nl) for (f, b, m, nl) in g1['skips']]}")
    print(f"    POW exécutées {pow_exec}/21 ; N_28_POW = {n_28_pow}")

    # ---------- C4 : anti-rétro-ingénierie ----------
    print("[C4] passe de grille (cible perturbée ×3) …")
    g2 = passe_grille(CIBLE_PERTURBEE, CIBLE_PERTURBEE)
    identiques = (g2["fermetures"] == g1["fermetures"])
    motifs_ok, motifs_pres = scan_motifs_route()
    controles["C4"] = dict(
        ok=bool(identiques and motifs_ok and g2["n_t1"] == 0),
        mesure=dict(fermetures_bit_identiques=identiques,
                    motifs_absents=motifs_ok, motifs_presents=motifs_pres,
                    n_t1_perturbe=g2["n_t1"]),
        barre="fermetures bit-identiques ; motifs interdits absents de la route",
        detail="la route ne lit JAMAIS la cible : ré-exécution complète avec la "
               "cible ×3 → mêmes fermetures bit à bit, correspondances effondrées")
    print(f"    fermetures bit-identiques : {identiques} ; motifs absents : {motifs_ok} "
          f"({motifs_pres}) ; N_T1 (cible ×3) = {g2['n_t1']}")

    # ---------- C5 : contrôle négatif (doit tenir) ----------
    _, lignes_c = remplissage(E0, ST)
    seq_coulomb = couches(lignes_c, 0.05)
    c5_ok = (seq_coulomb[:2] == [2, 10] and seq_coulomb[1] != 8)
    controles["C5"] = dict(
        ok=bool(c5_ok), mesure=seq_coulomb[:7],
        barre="2e fermeture == 10 ≠ 8 (Coulomb ≠ nucléaire dès la 2e fermeture)",
        detail="contrôle négatif : la table nucléaire ne sort pas du régime long-range")

    # ---------- témoin gelé (sert à C6/C8/D1) ----------
    Vw = V_exp(20.0, 0.5)
    Ew = etats(Vw)
    mesure_w, lignes_w = remplissage(Ew, ST)
    n_lie_w = len([s for s in ST if Ew[s] < 0])
    cl_tem = {th: couches(lignes_w, th) for th in THETAS}

    # ---------- C6 : convergence N=800 vs N=1600 ----------
    E16 = etats(Vw, N=1600)
    devs = []
    for s in mesure_w[:12]:
        if s in E16 and E16[s] < 0:
            devs.append(abs(E16[s] - Ew[s]) / abs(Ew[s]))
    conv_max = max(devs)
    controles["C6"] = dict(
        ok=bool(conv_max <= C6_BARRE), mesure=conv_max, barre=C6_BARRE,
        detail=f"convergence sur les 12 premières sous-couches du témoin (n devs={len(devs)})")

    # ---------- C7 : témoin capacité ----------
    Ecap = etats(V_yukawa(100.0, 1.0))
    _, lf = remplissage(Ecap, ST, double=False)
    _, lt = remplissage(Ecap, ST, double=True)
    seq_f = [z for (_, z, _, _) in lf[:6]]
    seq_t = [z for (_, z, _, _) in lt[:6]]
    controles["C7"] = dict(
        ok=bool(seq_f == CAP_DOUBLE_FALSE and seq_t == CAP_DOUBLE_TRUE
                and seq_f != seq_t),
        mesure=dict(double_false=seq_f, double_true=seq_t),
        barre=dict(double_false=CAP_DOUBLE_FALSE, double_true=CAP_DOUBLE_TRUE),
        detail="le facteur de capacité 2 est structurel (séquences == déposées et ≠)")

    # ---------- C8 : témoin EXP β=20 μ=0.5 bit-identique au §0 ----------
    sous = [(nm, z, e) for (nm, z, e, _) in lignes_w[:12]]
    c8_ok = (sous == TEMOIN_SOUS_COUCHES
             and all(cl_tem[th][:8] == TEMOIN_CL[th] for th in THETAS)
             and n_lie_w == TEMOIN_N_LIE)
    controles["C8"] = dict(
        ok=bool(c8_ok),
        mesure=dict(sous_couches=sous, fermetures={str(t): cl_tem[t][:8] for t in THETAS},
                    n_lie=n_lie_w),
        barre=dict(sous_couches=TEMOIN_SOUS_COUCHES, fermetures=TEMOIN_CL,
                   n_lie=TEMOIN_N_LIE),
        detail="témoin EXP β=20 μ=0.5 : 12 sous-couches, fermetures 3 θ, n_lie — bit-près")

    # ---------- conséquences ----------
    wit_in_t1 = any(f == "EXP" and b == 20.0 and m == 0.5 and th == 0.10
                    and sq == TEMOIN_T1_SEQ for (f, b, m, th, sq) in g1["t1_cfg"])
    cons["D1"] = dict(ok=bool(g1["n_t1"] == N_T1_GEL and wit_in_t1),
                      mesure=dict(n_t1=g1["n_t1"], temoin_dans_t1=wit_in_t1),
                      detail="N_T1==49 ET témoin ∈ T1 (séquence [2,8,20,26,52,76,124])")
    cons["D2"] = dict(ok=bool(g1["n_28"] == N_28_GEL and n_28_pow == N_28_POW_GEL),
                      mesure=dict(n_28=g1["n_28"], n_28_pow=n_28_pow),
                      detail="N_28==0 ET N_28_POW==0 — consignation C-P6 du rang 4")
    cons["D3"] = dict(ok=bool(g1["n_any"] == N_28_ANY_GEL), obs=True,
                      mesure=g1["n_any"],
                      detail="[OBS] 28 apparaît quelque part dans 77 configs, jamais en rang 4")
    Eg = etats(V_gauss(100.0, 0.5))
    _, lg = remplissage(Eg, ST)
    seq_gauss = couches(lg, 0.02)
    Ed = etats(V_yukawa(200.0, 0.5, ALPHA))
    _, ld = remplissage(Ed, ST)
    seq_yukphi = couches(ld, 0.02)
    d4_ok = (seq_coulomb[:7] == SEQ_COULOMB and seq_yukphi[:8] == SEQ_YUKPHI
             and seq_gauss[:8] == SEQ_GAUSS)
    cons["D4"] = dict(ok=bool(d4_ok),
                      mesure=dict(coulomb=seq_coulomb[:7], yukphi=seq_yukphi[:8],
                                  gauss=seq_gauss[:8]),
                      detail="trois séquences de régime == déposées (bit à bit)")
    E50 = etats(V_exp(50.0, PHI))
    _, l50 = remplissage(E50, ST)
    d5_seq = couches(l50, 0.02)
    cons["D5"] = dict(ok=bool(d5_seq[:7] == D5_SEQ), obs=True,
                      mesure=d5_seq[:8],
                      detail="[OBS] μ=φ exactement (hors grille gelée) : EXP β=50 → "
                             "[2,8,10,20,26,28,42] aux θ=0.02/0.05 — 28 en 6e position")

    # ---------- verdict ----------
    ordre = ["C0a", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]
    tous_ok = all(controles[c]["ok"] for c in ordre)
    if not tous_ok:
        verdict = "V4_REFUTE"
    elif cons["D1"]["ok"] and cons["D2"]["ok"] and cons["D4"]["ok"]:
        verdict = "V+ M4_NUCLEAIRE_TRANCHES_CONSIGNÉES"
    else:
        verdict = "V2_PARTIEL"
    exit_code = 1 if verdict == "V4_REFUTE" else 0

    duree = time.time() - t0
    print("\n" + "=" * 72)
    for c in ordre:
        print(f"  {c}: {'OK ' if controles[c]['ok'] else 'ÉCHEC'} — {controles[c]['detail']}")
    for d in ["D1", "D2", "D3", "D4", "D5"]:
        obs = " [OBS]" if cons[d].get("obs") else ""
        print(f"  {d}{obs}: {'OK ' if cons[d]['ok'] else 'ÉCHEC'} — {cons[d]['detail']}")
    print("=" * 72)
    print(f"VERDICT : {verdict}  (exit {exit_code})")
    print(f"(durée {duree:.1f} s ; déterministe, aucune graine)")

    resultat = dict(
        campagne="F12-M4 NUCLEAIRE V0",
        frontiere="FRONTIERE_F12_M4_NUCLEAIRE_V0.md (commit 8a27c74, dépôt-d'abord C0a)",
        date=time.strftime("%Y-%m-%d %H:%M:%S"),
        verdict=verdict, exit_code=exit_code, duree_s=round(duree, 1),
        cible_nucleaire=list(CIBLE_NUC),
        grille=dict(N_GRID=N_GRID, R_MIN=R_MIN, R_MAX=R_MAX, L_MAX=L_MAX,
                    N_KEEP=N_KEEP, N_MAX=N_MAX, BETAS=list(BETAS),
                    MUS=[round(m, 6) for m in MUS], THETAS=list(THETAS),
                    POW_BETAS=list(POW_BETAS), capacite="2(2l+1)", skip="<6 liés"),
        controles=controles,
        consequences=cons,
        comptages=dict(n_t1=g1["n_t1"], n_28=g1["n_28"], n_28_pow=n_28_pow,
                       n_28_any=g1["n_any"], meilleur_prefixe=g1["best_pm"],
                       meilleur_prefixe_desc=g1["best_desc"],
                       configs_t1=[[f, b, round(m, 6), th, sq]
                                   for (f, b, m, th, sq) in g1["t1_cfg"]],
                       n_t1_perturbe=g2["n_t1"]),
    )
    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(resultat, f, ensure_ascii=False, indent=1)
    print(f"JSON : {JSON_OUT}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
