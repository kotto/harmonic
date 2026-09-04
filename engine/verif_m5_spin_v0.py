# -*- coding: utf-8 -*-
"""
VERIF M5 SPIN V0 — le spin comme objet demi-angle du lien (MORT 5 de la chaîne F12-M).

Frontière : FRONTIERE_M5_SPIN_V0.md (963693c, dépôt-d'abord C0a — ce script
n'existait pas au moment du dépôt). Toutes les barres sont gelées dans la
frontière §2 ; UN SEUL échec ⟹ V4_REFUTE exit 1, sans sauvetage.

Objet : le facteur 2 de la capacité 2(2l+1) (postulé M1 d0f714a) et la
signature fermionique, via le revêtement carré noyau→boucle :
poids mère λ(ω) = (iω)^α (D3D db00e3b O2/C10 verbatim), boucle = multiplication
site unique, Bateman R(θ) (M1 C3), σ(α) = e^{iπα} (M1 C4), zéro |1+σ| 720 pts
(M1 C2), tension (M1 C5). Route monodromie MORTE, consignée (C7).

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

FRONTIERE = "FRONTIERE_M5_SPIN_V0.md"
SORTIE = "resultat_m5_spin_v0.json"

t_exec = time.time()

# ---------------------------------------------------------------- constantes gelées (frontière §5, verbatim M1/D3D)
PHI = (1.0 + math.sqrt(5.0)) / 2.0
ALPHA = 1.0 / PHI
THETA = math.pi * ALPHA / 2.0            # M1 C0b — la boucle d'échange = 2θ = πα

N = 512
L = 20.0 * math.pi
D_OMEGA = 2.0 * math.pi / L              # 0,1 — harmoniques sur bins entiers
W0 = 1.0

TOL_C = 1.0e-12                          # contrôles généraux (grille)
TOL_PHASE = 1.0e-15                      # phases et fermetures fines
TOL_FIBRE = 1.0e-14                      # fibre du carré (S1)
GRID = 720                               # balayage complet de la famille σ
RS = [0.5, 1.0, 2.0, 3.0, 25.6]          # sondes de rayon gelées

mp.dps = 40


# ---------------------------------------------------------------- poids spectral unique (verbatim D3D O2/C10)
def lambda_weight(w, a=ALPHA):
    """(iω)^α, branche principale : ω^α·e^{+iπα/2} si ω>0, |ω|^α·e^{−iπα/2} si ω<0.

    C'est l'unique poids spectral de tout l'appareil (identité mère P30).
    Aucun autre objet spectral n'est autorisé : la boucle est son carré.
    """
    w = np.asarray(w, dtype=float)
    br = math.pi * a / 2.0
    lam = np.zeros(w.shape, dtype=complex)
    pos = w > 0
    neg = w < 0
    lam[pos] = np.power(w[pos], a) * np.exp(1j * br)
    lam[neg] = np.power(-w[neg], a) * np.exp(-1j * br)
    return lam


def bateman(theta):
    """Hamiltonien C3 verbatim — R(θ), det = 1, trace = 2cosθ, λ = e^{±iθ}."""
    c, s = math.cos(theta), math.sin(theta)
    return [[c, s], [-s, c]]


def construit_monde(n_points):
    """Modes de la dyade — amplitude 1 : vecteurs unitaires sous ⟨,⟩ = Σ·/N."""
    x_loc = np.arange(n_points) * (L / n_points)
    e1 = np.exp(1j * W0 * x_loc)
    e2 = np.exp(1j * 2.0 * W0 * x_loc)
    return x_loc, e1, e2


def norme2_mat(M, n_points):
    """O6 — norme à deux particules ‖M‖² = Σ|M_ij|²/N² (convention CHSH)."""
    return float(np.sum(np.abs(M) ** 2)) / (n_points * n_points)


def wrap(a):
    """angle dans (−π, π]."""
    return (a + math.pi) % (2.0 * math.pi) - math.pi


# ---------------------------------------------------------------- exécution
controles = []
consequences = []


def controle(nom, ok, detail):
    controles.append({"controle": nom, "ok": bool(ok), "detail": detail})
    print(f"  [{'OK ' if ok else 'ÉCHEC'}] {nom} : {detail}")
    return bool(ok)


print("=" * 74)
print("  M5 SPIN V0 — le facteur 2 et la signature fermionique par le revêtement carré")
print("=" * 74)
print()
print("[CONTRÔLES BLOQUANTS — frontière 963693c §2 : un seul échec ⟹ REFUTE exit 1]")

# ---------------------------------------------------------------- C0a — antériorité
mtime_front = os.path.getmtime(FRONTIERE)
c0a_ok = mtime_front < t_exec
ok_global = c0a_ok
ok_global &= controle("C0a antériorité : mtime(frontière) < début d'exécution", c0a_ok,
                      f"frontière {time.strftime('%H:%M:%S', time.localtime(mtime_front))} "
                      f"< exécution {time.strftime('%H:%M:%S', time.localtime(t_exec))}")

# ---------------------------------------------------------------- grille gelée (verbatim D3D O3)
W_GRID = np.where(np.arange(N) <= N // 2, np.arange(N), np.arange(N) - N).astype(float) * D_OMEGA
WG = lambda_weight(W_GRID)               # poids mère α=1/φ
LG = WG * WG                             # boucle α=1/φ — LG ≡ WG² (site unique C10)
WG1 = lambda_weight(W_GRID, 1.0)         # le MÊME poids, évalué au point α=1
LG1 = WG1 * WG1                          # boucle α=1 — (iω)² = −ω²
nz = W_GRID != 0.0
no_nyq = nz & (np.arange(N) != N // 2)   # appariement ±ω (Nyquist 25.6 sans vis-à-vis)

# ---------------------------------------------------------------- C1 — filiation C10
s1a = float(np.max(np.abs(LG1[nz] - (-(W_GRID[nz] ** 2)))))          # forme close −ω²
LG1m = lambda_weight(-W_GRID, 1.0) * lambda_weight(-W_GRID, 1.0)
s1b = float(np.max(np.abs(LG1[no_nyq] - LG1m[no_nyq])))              # boucle aveugle au signe
ok_global &= controle("C1 filiation C10 : forme close −ω² à α=1 (grille entière) et "
                      "boucle aveugle au signe LG1(w) == LG1(−w) (grille appariée)",
                      s1a < TOL_C and s1b < TOL_C,
                      f"forme close = {s1a!r} ; aveugle au signe = {s1b!r} (barre 1e-12)")

# ---------------------------------------------------------------- C2 — fibre du carré à α=1
e_fibre_max, e_sq_max = 0.0, 0.0
for r in RS:
    lp = complex(lambda_weight(np.array([r]), 1.0)[0])
    lm = complex(lambda_weight(np.array([-r]), 1.0)[0])
    e_fibre_max = max(e_fibre_max, abs(lm + lp))
    e_sq_max = max(e_sq_max, abs(lm * lm - lp * lp))
lp1 = complex(lambda_weight(np.array([1.0]), 1.0)[0])
lm1 = complex(lambda_weight(np.array([-1.0]), 1.0)[0])
ratio_a1 = lp1 / lm1
ok_global &= controle("C2 fibre du carré z↦z² à α=1 sur RS : |λ(−r)+λ(r)| ≤ 1e-14 ; "
                      "|λ(−r)²−λ(r)²| ≤ 1e-12 ; rapport des feuillets = −1 à ≤ 1e-15",
                      e_fibre_max < TOL_FIBRE and e_sq_max < TOL_C
                      and abs(ratio_a1 + 1.0) < TOL_PHASE,
                      f"max fibre = {e_fibre_max!r} ; max carré = {e_sq_max!r} ; "
                      f"rapport = {ratio_a1!r} (|ratio+1| = {abs(ratio_a1 + 1.0):.2e})")

# ---------------------------------------------------------------- C3 — coïncidence Bateman
R = bateman(THETA)
eig = np.linalg.eigvals(np.array(R, dtype=float))
eig_pos = complex(eig[0]) if eig[0].imag > 0 else complex(eig[1])
eig_neg = complex(eig[1]) if eig[0].imag > 0 else complex(eig[0])
lpf = complex(lambda_weight(np.array([1.0]))[0])
lmf = complex(lambda_weight(np.array([-1.0]))[0])
phase_feuille = lpf / abs(lpf)
ec_bat = max(abs(eig_pos - phase_feuille), abs(eig_neg - phase_feuille.conjugate()))
sigma_kms = cmath.exp(2j * THETA)                                            # route i : θ doublé (KMS C6)
sigma_bat = eig_pos * eig_pos                                                # route ii : Bateman carré (C3)
sigma_direct = complex(math.cos(ALPHA * math.pi), math.sin(ALPHA * math.pi)) # route iii
sigma_fibre = lpf / lmf                                                      # route iv : rapport des feuillets
PHI_M = (1 + mp.sqrt(5)) / 2
ALPHA_M = 1 / PHI_M
sigma_mp = mp.exp(1j * ALPHA_M * mp.pi)                                      # route mpmath dps40
ec_sigma = max(abs(sigma_kms - sigma_fibre), abs(sigma_bat - sigma_fibre),
               abs(sigma_direct - sigma_fibre),
               float(abs(sigma_direct - sigma_mp)))
ok_global &= controle("C3 coïncidence Bateman : eig(R(θ)) == phase de feuillet (2 branches) "
                      "et quadruple σ (θ doublé, Bateman², directe, mpmath dps40)",
                      ec_bat < TOL_PHASE and ec_sigma < TOL_PHASE,
                      f"Bateman-feuillet = {ec_bat:.2e} ; quadruple σ = {ec_sigma:.2e} "
                      "(barre 1e-15)")

# ---------------------------------------------------------------- C4 — demi-angle
d1 = np.angle(LG1[no_nyq]) - 2.0 * np.angle(WG1[no_nyq])
s4a = float(np.max(np.abs((d1 + math.pi) % (2.0 * math.pi) - math.pi)))
df = np.angle(LG[no_nyq]) - 2.0 * np.angle(WG[no_nyq])
s4b = float(np.max(np.abs((df + math.pi) % (2.0 * math.pi) - math.pi)))
ec_boucle = abs(2.0 * THETA - ALPHA * math.pi)                               # C0b verbatim (M1)
ratio_traversee = THETA / (2.0 * THETA)
ok_global &= controle("C4 demi-angle : |arg(boucle) − 2·arg(noyau)| ≤ 1e-14 sur grille aux "
                      "DEUX α ; 2θ − πα == 0.0 bit-exact ; ratio de traversée == 0.5 bit-exact",
                      s4a < 1.0e-14 and s4b < 1.0e-14 and ec_boucle == 0.0
                      and ratio_traversee == 0.5,
                      f"α=1 : {s4a!r} ; α=1/φ : {s4b!r} ; 2θ−πα = {ec_boucle!r} ; "
                      f"ratio = {ratio_traversee!r}")

# ---------------------------------------------------------------- C5 — contraste α=1/φ (doit tenir)
LGm = lambda_weight(-W_GRID) * lambda_weight(-W_GRID)
s5_max = float(np.max(np.abs(LG[no_nyq] - LGm[no_nyq])))
s5_r1 = abs(lmf * lmf - lpf * lpf)                                           # à |ω|=1 exact
s5_ferme = 2.0 * math.sin(ALPHA * math.pi)
ok_global &= controle("C5 contraste α=1/φ (doit tenir) : |LG(w)−LG(−w)| max > 1 ; "
                      "à |ω|=1 == 2·sin(πα) à ≤ 1e-15 ; σ²(1/φ) : |σ²−1| > 1 ET "
                      "|σ²+1| > 0.5 ; tension |1+σ(1/φ)|² > 1",
                      s5_max > 1.0 and abs(s5_r1 - s5_ferme) < TOL_PHASE
                      and abs(sigma_direct * sigma_direct - 1.0) > 1.0
                      and abs(sigma_direct * sigma_direct + 1.0) > 0.5
                      and abs(1.0 + sigma_direct) ** 2 > 1.0,
                      f"max = {s5_max!r} ; à |ω|=1 = {s5_r1!r} vs fermé {s5_ferme!r} ; "
                      f"|σ²−1| = {abs(sigma_direct * sigma_direct - 1.0):.6f} ; "
                      f"|σ²+1| = {abs(sigma_direct * sigma_direct + 1.0):.6f} ; "
                      f"tension = {(abs(1.0 + sigma_direct) ** 2)!r}")

# ---------------------------------------------------------------- C6 — zéro d'interférence et secteurs
gamma_grid = np.array([2.0 * math.pi * k / GRID for k in range(GRID)])
famille = np.array([abs(1.0 + cmath.exp(1j * g)) for g in gamma_grid])
argmin = int(np.argmin(famille))
val_min = float(famille[argmin])
nb_presque_zero = int(np.sum(famille < 1.0e-3))
sigma_a1 = cmath.exp(1j * math.pi)                                           # α = 1 : le signe fermionique
tension_a1 = 2.0 + 2.0 * math.cos(math.pi)                                   # α = 1 : 0.0 bit-exact
x, e1, e2 = construit_monde(N)
M_mm = np.outer(e1, e1)
psi_exclu = (M_mm - M_mm.T) / math.sqrt(2.0)                                 # secteur σ = −1, même-mode
psi_boson = (M_mm + M_mm.T) / math.sqrt(2.0)                                 # secteur σ = +1, même-mode
norm_exclu = math.sqrt(norme2_mat(psi_exclu, N))
norm_boson = math.sqrt(norme2_mat(psi_boson, N))
ok_global &= controle("C6 zéro d'interférence et secteurs : balayage 720 argmin == 360 "
                      "ET val ≤ 1e-15 ET 1 zéro ; σ(1) = −1 ≤ 1e-15 ; σ(1)² = +1 ≤ 1e-15 ; "
                      "tension α=1 == 0.0 bit-exact ; ‖Ψ_exclu‖ ≤ 1e-15 ; ‖Ψ_boson‖ = √2 ≤ 1e-12",
                      argmin == GRID // 2 and val_min < TOL_PHASE and nb_presque_zero == 1
                      and abs(sigma_a1 + 1.0) < TOL_PHASE
                      and abs(sigma_a1 * sigma_a1 - 1.0) < TOL_PHASE
                      and tension_a1 == 0.0
                      and norm_exclu < TOL_PHASE
                      and abs(norm_boson - math.sqrt(2.0)) < TOL_C,
                      f"argmin = γ[{argmin}] = {gamma_grid[argmin]!r} ; val = {val_min!r} ; "
                      f"zéros : {nb_presque_zero} ; |σ+1| = {abs(sigma_a1 + 1.0):.2e} ; "
                      f"|σ²−1| = {abs(sigma_a1 * sigma_a1 - 1.0):.2e} ; tension(α=1) = {tension_a1!r} ; "
                      f"‖Ψ_exclu‖ = {norm_exclu!r} ; ‖Ψ_boson‖ = {norm_boson!r}")

# ---------------------------------------------------------------- C7 — consignation route morte (monodromie)
mono_a1 = cmath.exp(2j * math.pi * 1.0)
mono_f = sigma_direct * sigma_direct                                         # e^{2πiα} à α=1/φ
ec_gap_half = abs(0.5 - ALPHA)
ok_global &= controle("C7 consignation route morte : |e^{2πi}−1| ≤ 1e-15 (triviale à α=1) ET "
                      "|e^{2πi/φ}+1| > 0.5 (non spinorielle à α=1/φ) ET "
                      "|1/2 − 1/φ| > 0.1 (α=1/2 hors points déposés)",
                      abs(mono_a1 - 1.0) < TOL_PHASE and abs(mono_f + 1.0) > 0.5
                      and ec_gap_half > 0.1,
                      f"|e^{{2πi}}−1| = {abs(mono_a1 - 1.0):.2e} ; |e^{{2πi/φ}}+1| = "
                      f"{abs(mono_f + 1.0):.6f} ; |1/2−1/φ| = {ec_gap_half!r}")

# ============================================================ conséquences (gelées frontière §3)
print()
print("[CONSÉQUENCES — D1/D2/D3]")

# D1 — dimension de fibre == 2 aux deux α (5/5 sur RS)
n_ok = 0
for a_val in (1.0, ALPHA):
    for r in RS:
        lp_ = complex(lambda_weight(np.array([r]), a_val)[0])
        lm_ = complex(lambda_weight(np.array([-r]), a_val)[0])
        if abs(lp_ - lm_) > 1.0e-30 and abs(lp_) > 0.0 and abs(lm_) > 0.0:
            n_ok += 1
d1_ok = n_ok == 2 * len(RS)
consequences.append({"consequence": "D1", "ok": bool(d1_ok),
                     "mesure": n_ok,
                     "detail": f"fibres à 2 valeurs distinctes non nulles : {n_ok}/10 "
                               "(5/5 aux deux α) — le facteur 2 est une dimension de fibre"})
print(f"  [{'OK ' if d1_ok else 'ÉCHEC'}] D1 : {consequences[-1]['detail']}")

# D2 — le deck du revêtement carré EST σ(α) ; à α=1 : −1 ; à α=1/φ : hors Z₂
d2_ok = (abs(ratio_a1 + 1.0) < TOL_PHASE
         and abs(sigma_fibre - sigma_direct) < TOL_PHASE
         and abs(sigma_direct * sigma_direct - 1.0) > 1.0
         and abs(sigma_direct * sigma_direct + 1.0) > 0.5
         and s1b < TOL_C)
consequences.append({"consequence": "D2", "ok": bool(d2_ok),
                     "mesure": f"deck(α=1) = {ratio_a1!r} ; deck(1/φ) = σ(1/φ) = "
                               f"{mp.nstr(sigma_mp, 30)}",
                     "detail": "le rapport d'échange déposé EST le deck du revêtement carré ; "
                               "à α=1 : −1 exactement (Z₂ fermionique) ; à α=1/φ : hors Z₂ "
                               "(braisage ouvert consigné, ni +1 ni −1)"})
print(f"  [{'OK ' if d2_ok else 'ÉCHEC'}] D2 : {consequences[-1]['detail']}")

# D3 — [MAPPING] 2(2l+1) pour l=0..6
caps = [2 * (2 * l + 1) for l in range(7)]
d3_ok = caps == [2, 6, 10, 14, 18, 22, 26]
consequences.append({"consequence": "D3", "ok": bool(d3_ok),
                     "mesure": caps,
                     "detail": "[MAPPING] 2(2l+1), l=0..6 == [2,6,10,14,18,22,26] — facteur 2 = "
                               "dimension de fibre (machine D1) ; (2l+1) dégénérescence des modes "
                               "de boucle NON dérivée, consignée"})
print(f"  [{'OK ' if d3_ok else 'ÉCHEC'}] D3 : {consequences[-1]['detail']}")

# ============================================================ verdict (échelle gelée frontière §4)
tous_c = all(c["ok"] for c in controles)
d_ok = d1_ok and d2_ok and d3_ok
if ok_global and d_ok:
    verdict = "V+ M5_SPIN_DEMI_ANGLE_FERME"
elif ok_global and not d_ok:
    verdict = "V2_M5_PARTIEL"
elif all(c["ok"] for c in controles[1:]):
    verdict = "V3_M5_INCOMPLET"
else:
    verdict = "V4_M5_REFUTE"

print()
print("=" * 74)
print(f"  VERDICT : {verdict}")
print("=" * 74)

resultat = {
    "campagne": "M5 SPIN V0 — le spin comme objet demi-angle du lien (revêtement carré noyau→boucle)",
    "frontiere": FRONTIERE,
    "frontiere_commit": "963693c",
    "verdict": verdict,
    "ok_global": bool(ok_global),
    "controles": controles,
    "consequences": consequences,
    "route_morte_consignee": "monodromie de (iω)^α : e^{2πiα}=1 trivial à α=1 ; angle 3.8832 "
                             "non spinoriel à α=1/φ ; e^{2πiα}=−1 ⟺ α=1/2 hors points déposés "
                             "(|1/2−1/φ| = 0.11803398874989479) — consignée avant gel, jamais gelée",
    "determinisme": "aucune graine, aucun aléa",
    "duree_s": round(time.time() - t_exec, 1),
}
with open(SORTIE, "w", encoding="utf-8") as f:
    json.dump(resultat, f, ensure_ascii=False, indent=1)
print(f"\nJSON écrit : {SORTIE}")

sys.exit(0 if (ok_global and d_ok) else 1)