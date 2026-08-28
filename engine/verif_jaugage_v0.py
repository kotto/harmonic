# -*- coding: utf-8 -*-
"""
JAUGAGE V0 — exécution machine du dépôt DEPOT_JAUGAGE_V0.md (28/08/2026)

Le dépôt est FERMÉ et ANTÉRIEUR à ce script (contrôle C0a : mtime dépôt < mtime exécution).
Aucune lecture, barre ou verdict n'est modifiable ici — ce script ne fait qu'exécuter :

  Famille A (covariance)  : 36 profils α_{a,k}(x) = a·cos(kx),
                            A1 défaut D(a,k), A2 covariance α→α+θ₀ (TOL_COV=1e-9),
                            A3 linéarité de gradient χ_a(k)=D/a (doublement 0,1→0,2, 5 %)
                            + témoin négatif TN-A (régime 2→5 doit être détecté)
  Famille B (la force)    : G* = χ_{0,1}(k=1)/R_tour(½) contre 16 candidats fermés
                            × {G*/c, c/G*} = 32 lectures, barres 1e-4 / 2,355e-7
                            + témoin négatif TN-B (3 profils aléatoires, graines 27/28/29)
  Famille C (running)     : χ(ω₀) sur 5 porteurs, β_pred pente ln χ vs ln ω₀
                            — DIAGNOSTIQUE, puissance de verdict NULLE au V0 (dépôt §2)

  Contrôles bloquants C0a…C6 (dépôt §3) — UN SEUL en échec ⟹ V4 REFUTE exit 1.

  Verdicts (dépôt §4) :
    V+  JAUGAGE_COMPLET_CONFIRME            (hit ≤ 2,355e-7)               exit 0
    V2  JAUGAGE_CONFIRME_FORCE_CANDIDATE    (hit géométrique ≤ 1e-4)       exit 0
    V3  COVARIANCE_LOCALE_DERIVEE_FORCE_SANS_NOM (aucun hit)                exit 0
    V4  REFUTE  (contrôle KO, TN-A, A2 impossibilité, TN-B)                exit 1
    —   LIBERTE_LOCALE_ABSANTE  (A3 en échec : défaut non gradient-porté)  exit 1

Objets fermés O1–O7, interdictions I1–I5, honnêteté §6 : voir le dépôt.
Sortie : resultat_jaugage_v0.json (toutes les lectures, y compris les quasi-échecs).
"""

import cmath
import json
import math
import os
import sys
import time

import numpy as np

# ================================================================== O1–O7 — objets fermés
PHI = (1.0 + math.sqrt(5.0)) / 2.0          # O1
ALPHA = 1.0 / PHI                            # α = 1/φ

N = 512                                      # O3
L = 20.0 * math.pi
D_OMEGA = 2.0 * math.pi / L                  # 0,1 — tous les modes tombent sur des bins entiers
NYQUIST = (N / 2) * D_OMEGA                  # 25,6 > max|ω| = 20 : zéro fuite spectrale

LEG_A = 0.4011522499939087                   # O4 — |K̃(½)|² (registre 27/08)
IMPEDANCE = 2.492819122951908                # O4 — 1/|K̃(½)|²
D2_REGISTRE = 0.54518249                     # O4 — (1/π)∫₀^∞|K̃(ω)|²dω (registre 27/08)
ANCRE = 137.036031356                        # O4 — ancre 5-facteurs (coïncidence de compression)
CODATA = 137.035999177                       # O4 — α⁻¹ CODATA 2022
FACTEUR_OBS = 1.8324104102898406             # O4 — [OBS] 28/08 (α_W/α_EM ÷ impédance)

TOL_HIT = 1.0e-4                             # O7
TOL_HIT_PLUS = 2.355e-7                      # O7 — témoins de continuité e/π
TOL_COV = 1.0e-9                             # O7 — lecture A2
TOL_C0B = 1.0e-15
TOL_C1 = 1.0e-12
TOL_C2 = 1.0e-12
TOL_C4 = 1.0e-11
TOL_C5 = 1.0e-10
TOL_C6 = 1.0e-6
TOL_A3 = 0.05                                # barre A3 / TN-A (5 %)

A_GRID = [0.1, 0.2, 0.5, 1.0, 2.0, 5.0]      # 6 amplitudes fermées
K_GRID = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]     # 6 gradients fermés (bins 1,5,10,20,50,100)
W0_GRID_C = [0.1, 0.5, 1.0, 2.0, 10.0]       # Famille C (bins 1,5,10,20,100)
THETAS = [math.pi / 3.0, math.pi / 2.0]      # angles de test A2 (arbitraires — I1)
TN_SEEDS = [27, 28, 29]                      # témoin négatif TN-B (27 = graine campagne jauge)
TN_WITNESSES = [0.1, 1.0, 10.0]              # témoins TN-A
K_REF = 1.0
A_REF = 0.1

RACINE = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.join(RACINE, "DEPOT_JAUGAGE_V0.md")
SORTIE = os.path.join(RACINE, "resultat_jaugage_v0.json")

t_exec = time.time()
controles = []       # (nom, ok, detail)
famille_A1 = []      # 36 lectures D(a,k)
famille_A2 = []      # 72 lectures D(a,k ; α+θ₀)
chi_table = []       # table χ_a(k) 6×6
tn_a = []            # 3 témoins discriminants
famille_B = []       # 32 lectures
tn_b = []            # 3 profils aléatoires
famille_C = []       # 5 lectures χ(ω₀) + β_pred


def controle(nom, ok, detail):
    controles.append({"controle": nom, "ok": bool(ok), "detail": detail})
    print(f"  [{'OK ' if ok else 'ÉCHEC'}] {nom} : {detail}")
    return bool(ok)


def note(nom, detail):
    print(f"  [   ] {nom} : {detail}")


# ================================================================== noyaux (O2 — deux routes)
def Khat(omega):
    """K̂(ω) = φ/((iω)^α + φ) — route complexe, branche principale. K̂(0) = 1."""
    if omega == 0.0:
        return complex(1.0, 0.0)
    z = 1j * omega
    return PHI / (cmath.exp(ALPHA * cmath.log(z)) + PHI)


def Khat_real(omega):
    """K̂ forme réelle développée (phase incluse) — route indépendante pour C1."""
    if omega == 0.0:
        return complex(1.0, 0.0)
    w = abs(omega)
    s = 1.0 if omega > 0.0 else -1.0
    wa = w ** ALPHA
    den = PHI + wa * math.cos(math.pi * ALPHA / 2.0) \
        + 1j * s * wa * math.sin(math.pi * ALPHA / 2.0)
    return PHI / den


def Ktilde_complex(omega):
    """K̃(ω) = (iω)^{α−1}/((iω)^α + φ) — noyau de mémoire (route validée 27/08)."""
    z = 1j * omega
    return cmath.exp((ALPHA - 1.0) * cmath.log(z)) / (cmath.exp(ALPHA * cmath.log(z)) + PHI)


def Ktilde2_real(omega):
    """|K̃(ω)|² forme réelle (ω > 0) — identique à l'assaut 27/08, validée 2,8e-17."""
    num = omega ** (2.0 * ALPHA - 2.0)
    den = omega ** (2.0 * ALPHA) \
        + 2.0 * PHI * math.cos(math.pi * ALPHA / 2.0) * omega ** ALPHA + PHI ** 2
    return num / den


# ================================================================== treillis (O3, O5, O6)
m_bins = np.arange(N)
omega_grid = np.where(m_bins <= N // 2, m_bins, m_bins - N).astype(float) * D_OMEGA
x = np.arange(N) * (L / N)

KHAT_W = np.array([Khat(w) for w in omega_grid])


def norme(v):
    """O5 — norme unitaire ‖ψ‖² = Σ|ψₙ|²/N (Parseval)."""
    return math.sqrt(float(np.sum(np.abs(v) ** 2)) / N)


def applique_noyau(psi):
    """K̂[ψ] = IFFT(K̂(ω)·FFT(ψ)) — filtre fréquentiel, convention numpy 1/N incluse."""
    return np.fft.ifft(KHAT_W * np.fft.fft(psi))


def defaut(alpha_x, psi, k_psi):
    """A1 — D = ‖K̂[e^{iα}ψ] − e^{iα}·K̂[ψ]‖ / ‖K̂[ψ]‖ : le coût du rephasage modulé."""
    eia = np.exp(1j * alpha_x)
    return norme(applique_noyau(eia * psi) - eia * k_psi) / norme(k_psi)


# ================================================================== D_p — route quadrature verbatim 27/08 (contrôle C6)
def Dp(p, xlo, xhi, n):
    """D_p par Simpson en espace ln (w = e^x) — intégrande |K̃(w)|^p·w. (Route 27/08.)"""
    h = (xhi - xlo) / n
    s = 0.0
    for i in range(n + 1):
        w = math.exp(xlo + i * h)
        val = (abs(Ktilde_complex(w)) ** p) * w
        if i == 0 or i == n:
            s += val
        elif i % 2 == 1:
            s += 4.0 * val
        else:
            s += 2.0 * val
    return s * h / 3.0 / math.pi


# ================================================================== T0 — ANTÉRIORITÉ ET CONTRÔLES
print("=" * 74)
print("  JAUGAGE V0 — le prix du rephasage modulé (dépôt fermé du 28/08/2026)")
print("=" * 74)

t_debut = time.time()
mtime_depot = os.path.getmtime(DEPOT)
c0a_ok = mtime_depot < t_debut
print()
print("[CONTRÔLES BLOQUANTS — dépôt §3 : un seul échec ⟹ V4 REFUTE exit 1]")
ok_global = controle("C0a dépôt antérieur à l'exécution", c0a_ok,
                     f"mtime dépôt {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime_depot))} "
                     f"< exécution {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t_debut))}")

ec0b = abs(PHI ** 2 - (PHI + 1.0))
ok_global &= controle("C0b fermeture algébrique φ² = φ+1", ec0b < TOL_C0B, f"écart = {ec0b:.1e}")

ec1 = max(abs(Khat(w) - Khat_real(w)) for w in list(omega_grid) + [0.5, ALPHA, 1.0])
ok_global &= controle("C1 K̂ : route complexe vs forme réelle développée "
                      "(grille O3 entière + {½, 1/φ, 1})", ec1 < TOL_C1, f"écart max = {ec1:.2e}")

ec2 = abs(PHI + 1.0 / PHI - math.sqrt(5.0))
c2_ok = ec2 < TOL_C2
ok_global &= controle("C2 transparence du mode ½ : φ + φ⁻¹ = √5", c2_ok,
                      f"écart = {ec2:.1e} → réponse tour unitaire R_tour(½) = 1")

note("C3 ancre CODATA 2022", f"α⁻¹ = {CODATA} (consignée, distincte de l'ancre)")
controles.append({"controle": "C3 ancre CODATA 2022", "ok": True, "detail": f"α⁻¹ = {CODATA}"})

T0 = math.pi ** 4 * math.exp(-4.0) * PHI ** (-5.0) * 2.0 ** (-0.5) * 3.0 ** (-2.5)
ec4 = abs(1.0 / T0 - ANCRE) / ANCRE
ok_global &= controle("C4 ancre 5-facteurs reproduite (T0) — statut coïncidence de compression",
                      ec4 < TOL_C4, f"1/T0 = {1.0 / T0:.12f} ; écart {ec4:.2e} (relatif)")

leg_a_c = abs(Ktilde_complex(0.5)) ** 2
leg_a_r = Ktilde2_real(0.5)
ec5 = max(abs(leg_a_c - LEG_A), abs(leg_a_r - LEG_A), abs(leg_a_c - leg_a_r))
ok_global &= controle("C5 impédance |K̃(½)|² double route", ec5 < TOL_C5,
                      f"complexe = {leg_a_c:.16f} ; réel = {leg_a_r:.16f} ; "
                      f"registre = {LEG_A} ; écart max = {ec5:.2e}")

d2_40 = Dp(2.0, -40.0, 40.0, 40000)
d2_60 = Dp(2.0, -60.0, 60.0, 60000)
d2_80 = Dp(2.0, -80.0, 80.0, 80000)
stab_d2 = abs(d2_80 - d2_60) / max(1.0, abs(d2_80))
ec6 = abs(d2_80 - D2_REGISTRE)
ok_global &= controle("C6 D₂ réintégrée (1/π)∫₀^∞|K̃|²dω — route 27/08, reproductibilité croisée",
                      ec6 < TOL_C6,
                      f"D₂ = {d2_80:.8f} ; registre = {D2_REGISTRE} ; écart = {ec6:.2e} ; "
                      f"stabilité [-40,40]/[-60,60]/[-80,80] = {stab_d2:.1e}")

# ================================================================== FAMILLE A — COVARIANCE
print()
print("[FAMILLE A — 36 profils α_{a,k}(x) = a·cos(kx) : le coût du rephasage modulé]")
psi0 = np.exp(1j * 1.0 * x) / math.sqrt(N)       # O6 — porteur ω₀ = 1 (bin 10)
kpsi0 = applique_noyau(psi0)

for a in A_GRID:
    for k in K_GRID:
        D = defaut(a * np.cos(k * x), psi0, kpsi0)
        famille_A1.append({"a": a, "k": k, "D": float(D)})
note("A1 défaut de commutation D(a,k)", f"36 lectures consignées ; "
     f"min = {min(r['D'] for r in famille_A1):.6e} (a=0,1), "
     f"max = {max(r['D'] for r in famille_A1):.6f} (a=5)")

max_dev_a2 = 0.0
for a in A_GRID:
    for k in K_GRID:
        D_ref = next(r["D"] for r in famille_A1 if r["a"] == a and r["k"] == k)
        for th in THETAS:
            D_th = defaut(a * np.cos(k * x) + th, psi0, kpsi0)
            dev = abs(D_th - D_ref)
            max_dev_a2 = max(max_dev_a2, dev)
            famille_A2.append({"a": a, "k": k, "theta0": th, "D": float(D_th),
                               "deviation": float(dev)})
a2_ok = max_dev_a2 < TOL_COV
note("A2 aveuglement au rephasage constant (θ₀ ∈ {π/3, π/2})",
     f"72 lectures ; dérive max = {max_dev_a2:.2e} — barre TOL_COV = {TOL_COV:.0e} "
     f"→ {'POSSEDE le U(1) global exact' if a2_ok else 'IMPOSSIBILITÉ (linéarité en échec)'}")

chi_table = [{"a": r["a"], "k": r["k"], "chi": r["D"] / r["a"]} for r in famille_A1]
drifts_a3 = {}
for k in K_GRID:
    chi_lo = next(r["chi"] for r in chi_table if r["a"] == 0.1 and r["k"] == k)
    chi_hi = next(r["chi"] for r in chi_table if r["a"] == 0.2 and r["k"] == k)
    drifts_a3[k] = abs(chi_hi - chi_lo) / chi_lo
a3_ok = all(d < TOL_A3 for d in drifts_a3.values())
note("A3 linéarité de gradient (dérive au doublement 0,1→0,2)",
     "; ".join(f"k={k:g}: {d:.2e}" for k, d in drifts_a3.items())
     + f" — barre 5 % → {'la réponse est une fonction propre du gradient' if a3_ok else 'DÉFAUT NON GRADIENT-PORTÉ'}")

for k in TN_WITNESSES:
    chi_2 = next(r["chi"] for r in chi_table if r["a"] == 2.0 and r["k"] == k)
    chi_5 = next(r["chi"] for r in chi_table if r["a"] == 5.0 and r["k"] == k)
    d_big = abs(chi_5 - chi_2) / chi_2
    tn_a.append({"k": k, "derive_2_vers_5": float(d_big), "detectee": bool(d_big > TOL_A3)})
tn_a_ok = sum(t["detectee"] for t in tn_a) >= 2
note("TN-A pouvoir discriminant (régime non linéaire 2→5 doit dépasser 5 %)",
     "; ".join(f"k={t['k']:g}: {t['derive_2_vers_5']:.3f}{' ✓' if t['detectee'] else ' ✗'}" for t in tn_a)
     + f" → {'la lecture A3 discrimine' if tn_a_ok else 'LECTURE A3 VIDE'}")

# ================================================================== FAMILLE B — LA FORCE
print()
print("[FAMILLE B — G* = χ_{0,1}(k=1)/R_tour(½) contre 16 candidats fermés (32 lectures)]")
R_tour = 1.0 if c2_ok else None
g_star = None
if R_tour is not None:
    chi_ref = next(r["chi"] for r in chi_table if r["a"] == A_REF and r["k"] == K_REF)
    g_star = chi_ref / R_tour
    note("G* mesuré", f"χ_{{0,1}}(k=1) = {chi_ref:.8f} ; R_tour(½) = {R_tour:.1f} → G* = {g_star:.8f}")

    candidats = [
        ("1/D₂", 1.8342481982500942, TOL_HIT, True),
        ("D₂", D2_REGISTRE, TOL_HIT, True),
        ("impédance 1/|K̃(½)|²", IMPEDANCE, TOL_HIT, True),
        ("|K̃(½)|²", LEG_A, TOL_HIT, True),
        ("φ", PHI, TOL_HIT, True),
        ("φ²", PHI ** 2, TOL_HIT, True),
        ("1/φ", ALPHA, TOL_HIT, True),
        ("√5", math.sqrt(5.0), TOL_HIT, True),
        ("2φ", 2.0 * PHI, TOL_HIT, True),
        ("F₁₀", 55.0, TOL_HIT, True),
        ("L₁₀", 123.0, TOL_HIT, True),
        ("e^{1/φ}", math.exp(ALPHA), TOL_HIT_PLUS, False),
        ("e^{−1/φ}", math.exp(-ALPHA), TOL_HIT_PLUS, False),
        ("facteur [OBS] 28/08", FACTEUR_OBS, TOL_HIT_PLUS, False),
        ("ancre 5-facteurs", ANCRE, TOL_HIT_PLUS, False),
        ("1/ancre", 1.0 / ANCRE, TOL_HIT_PLUS, False),
    ]
    for nom, val, barre, geometrique in candidats:
        eps_dir = abs(g_star / val - 1.0)
        eps_inv = abs(val / g_star - 1.0)
        ecart = min(eps_dir, eps_inv)
        hit = ecart <= barre
        famille_B.append({"candidat": nom, "valeur": val, "G*_sur_c": float(g_star / val),
                          "c_sur_G*": float(val / g_star), "ecart_min": float(ecart),
                          "barre": barre, "geometrique": geometrique, "hit": bool(hit)})
        if hit:
            print(f"  >>> HIT — {nom} = {val:.10f} ; écart = {ecart:.2e} ≤ {barre:.1e}")
    n_hit = sum(1 for c in famille_B if c["hit"])
    print(f"  {n_hit}/16 candidats touchés (32 lectures consignées)")

    # --- témoin négatif TN-B : spécificité du hit (graines 27/28/29)
    for seed in TN_SEEDS:
        rng = np.random.default_rng(seed)
        ks = rng.choice(np.array(K_GRID), size=4, replace=False)
        us = rng.uniform(1.0, 10.0, 4)
        ths = rng.uniform(0.0, 2.0 * math.pi, 4)
        alpha_r = np.zeros(N, dtype=complex)
        for j in range(4):
            alpha_r += 0.1 * us[j] * np.cos(ks[j] * x + ths[j])
        G_r = defaut(alpha_r, psi0, kpsi0) / A_REF
        hits_r = []
        for c in famille_B:
            if c["hit"]:
                e_r = min(abs(G_r / c["valeur"] - 1.0), abs(c["valeur"] / G_r - 1.0))
                if e_r <= c["barre"]:
                    hits_r.append(c["candidat"])
        tn_b.append({"graine": seed, "k_j": [float(v) for v in ks], "u_j": [float(v) for v in us],
                     "theta_j": [float(v) for v in ths], "G_r": float(G_r),
                     "candidats_touches": hits_r})
    tn_b_ok = True
    if any(c["hit"] for c in famille_B):
        pire = max(sum(1 for r in tn_b if c["candidat"] in r["candidats_touches"])
                   for c in famille_B if c["hit"])
        tn_b_ok = pire <= 1
    note("TN-B spécificité (3 profils aléatoires, graines 27/28/29)",
         "; ".join(f"graine {r['graine']}: G_r = {r['G_r']:.6f}, "
                   f"{len(r['candidats_touches'])} hit(s) commun(s)" for r in tn_b)
         + f" → {'spécifique au gradient simple' if tn_b_ok else 'HIT NON SPÉCIFIQUE'}")
else:
    note("Famille B", "bloquée — C2 KO, verdict V4 de toute façon")
    tn_b_ok = False

# ================================================================== FAMILLE C — RUNNING (diagnostique)
print()
print("[FAMILLE C — running : χ(ω₀) sur 5 porteurs, β_pred — DIAGNOSTIQUE, aucun verdict (dépôt §2)]")
for w0 in W0_GRID_C:
    psi_w = np.exp(1j * w0 * x) / math.sqrt(N)
    chi_w = defaut(A_REF * np.cos(K_REF * x), psi_w, applique_noyau(psi_w))
    famille_C.append({"omega0": w0, "chi": float(chi_w)})
    print(f"  ω₀ = {w0:4g}  →  χ = {chi_w:.8f}")

xs = [math.log(r["omega0"]) for r in famille_C]
ys = [math.log(r["chi"]) for r in famille_C]
xm = sum(xs) / len(xs)
ym = sum(ys) / len(ys)
beta_pred = sum((xi - xm) * (yi - ym) for xi, yi in zip(xs, ys)) \
    / sum((xi - xm) ** 2 for xi in xs)
signe = "+" if beta_pred > 0 else "-"
d_plus = (beta_pred > 0) and (0.1 <= abs(beta_pred) <= 2.0)
d_moins = (beta_pred < 0) and (0.1 <= abs(beta_pred) <= 2.0)
note("β_pred (pente ln χ vs ln ω₀)",
     f"β_pred = {beta_pred:+.6f} ; signe {signe} ; "
     f"sous D+ (ω↑⇔μ↑, tripartition attend signe > 0) : "
     f"{'accord' if d_plus else 'désaccord'} ; sous D− (ω↑⇔μ↓) : "
     f"{'accord' if d_moins else 'désaccord'} — dictionnaire μ↔ω absent (trou D4), "
     f"lecture consignée SANS pouvoir de verdict")

# ================================================================== VERDICT
print()
print("=" * 74)
if not ok_global:
    verdict, code = "V4 — REFUTE", 1
    raison = "un contrôle bloquant est en échec (dépôt §3 : aucun sauvetage)"
elif not tn_a_ok:
    verdict, code = "V4 — REFUTE", 1
    raison = "TN-A : la lecture A3 est vide (le régime non linéaire n'est pas détecté)"
elif not a2_ok:
    verdict, code = "V4 — REFUTE", 1
    raison = "A2 en échec : impossibilité signal (aucun opérateur linéaire ne peut l'échouer) — pipeline cassé"
elif not tn_b_ok:
    verdict, code = "V4 — REFUTE", 1
    raison = "TN-B : le hit n'est pas spécifique au gradient simple"
elif not a3_ok:
    verdict, code = "LIBERTE_LOCALE_ABSANTE", 1
    raison = "A3 en échec : le défaut n'est pas gradient-porté, pas de structure de compensateur"
elif any(c["hit"] for c in famille_B):
    hits_plus = [c for c in famille_B if c["hit"] and c["barre"] == TOL_HIT_PLUS]
    hits_geo = [c for c in famille_B if c["hit"] and c["barre"] == TOL_HIT]
    if hits_plus:
        verdict, code = "V+ — JAUGAGE_COMPLET_CONFIRME", 0
        raison = "hit ≤ 2,355e-7 : " + ", ".join(c["candidat"] for c in hits_plus)
    elif hits_geo:
        verdict, code = "V2 — JAUGAGE_CONFIRME_FORCE_CANDIDATE", 0
        raison = "hit géométrique ≤ 1e-4 : " + ", ".join(c["candidat"] for c in hits_geo)
    else:  # hit sur témoin e/π entre 1e-4 et 2,355e-7 : continuité, pas V2
        verdict, code = "V3 — COVARIANCE_LOCALE_DERIVEE_FORCE_SANS_NOM", 0
        raison = "hit hors barres géométriques (témoin de continuité) : " \
            + ", ".join(c["candidat"] for c in famille_B if c["hit"])
else:
    verdict, code = "V3 — COVARIANCE_LOCALE_DERIVEE_FORCE_SANS_NOM", 0
    raison = "la covariance locale est dérivée (A2+A3) mais la force ne porte aucun nom fermé (0/16)"

print(f"  VERDICT : {verdict}")
print(f"  RAISON  : {raison}")
print(f"  SORTIE  : exit {code}")
print("=" * 74)

# ================================================================== JSON — toutes les lectures (I3)
resultat = {
    "depot": "DEPOT_JAUGAGE_V0.md",
    "date_execution": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t_debut)),
    "c0a": {"mtime_depot": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime_depot)),
            "mtime_execution": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t_debut)),
            "ok": bool(c0a_ok)},
    "objets_fermes": {"phi": PHI, "alpha": ALPHA, "N": N, "L": L, "delta_omega": D_OMEGA,
                      "nyquist": NYQUIST, "leg_a": LEG_A, "impedance": IMPEDANCE,
                      "D2": D2_REGISTRE, "ancre": ANCRE, "codata": CODATA,
                      "facteur_obs": FACTEUR_OBS,
                      "tol_hit": TOL_HIT, "tol_hit_plus": TOL_HIT_PLUS, "tol_cov": TOL_COV},
    "controles": controles,
    "famille_A": {"lectures_A1": famille_A1, "lectures_A2": famille_A2,
                  "max_deviation_A2": float(max_dev_a2), "A2_ok": bool(a2_ok),
                  "chi_table": chi_table, "drifts_A3": {f"{k:g}": float(d) for k, d in drifts_a3.items()},
                  "A3_ok": bool(a3_ok), "tn_A": tn_a, "TN_A_ok": bool(tn_a_ok)},
    "famille_B": {"G_star": None if g_star is None else float(g_star),
                  "R_tour_demi": R_tour, "lectures": famille_B,
                  "tn_B": tn_b, "TN_B_ok": bool(tn_b_ok)},
    "famille_C": {"lectures": famille_C, "beta_pred": float(beta_pred),
                  "signe": signe,
                  "dictionnaire_D_plus": {"accorde": bool(d_plus), "hypothese": "ω↑ ⇔ μ↑ (criblage)"},
                  "dictionnaire_D_moins": {"accorde": bool(d_moins), "hypothese": "ω↑ ⇔ μ↓"},
                  "puissance_verdict": "aucune au V0 (dépôt §2 — dictionnaire μ↔ω absent, trou D4)"},
    "verdict": {"nom": verdict, "raison": raison, "exit_code": code},
}
with open(SORTIE, "w", encoding="utf-8") as f:
    json.dump(resultat, f, ensure_ascii=False, indent=2)
print(f"Résultat consigné : {SORTIE}")

sys.exit(code)
