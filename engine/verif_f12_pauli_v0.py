# -*- coding: utf-8 -*-
"""
PAULI F12 V0 — exécution machine de la MORT 1 de FRONTIERE_F12_TABLEAU_PERIODIQUE.md

La thèse (frontière §3, chaîne P12–P15) :

  P12 mécanisme  : la double occupation même-mode dans le secteur d'échange σ porte
                   l'amplitude (1+σ)·A/√2 — l'exclusion est le point σ = −1 d'une
                   famille d'interférence à un paramètre : destruction mutuelle des
                   deux histoires indiscernables (directe / échangée). L'exclusion
                   n'est pas un décret d'antisymétrie : c'est une interférence.
  P13 fermeture  : [K̂⊗K̂, P₁₂] = 0 — le noyau mémoire ne génère ni ne détruit la
                   phase d'échange ; la statistique vient de l'influence Φ₂,
                   pas de la dynamique.
  P14 la phase   : un échange = la boucle d'influence complète des deux mémoires =
                   DEUX franchissements de la référence (Hamiltonien C5 : un
                   franchissement = θ) = 2θ = πα, d'où  σ(α) = e^{iπα}.
                   Trois routes déposées convergent : KMS C6 (θ doublé), Bateman C3
                   (e^{iθ} carré), action directe (cos+i·sin).
                   À α = 1 : σ = −1 — le signe fermionique est RECOUVRÉ de la phase
                   mémoire déposée, pas postulé — et σ² = +1 (échange double = identité).
  P15 la tension : à α = 1/φ, σ = e^{iπ/φ} ⟹ |1+σ|² = 2+2cos(πα) ≠ 0 : l'interférence
                   seule n'exclut plus la double occupation. Deux lectures consignées :
                   L1 — la phase d'échange de la matière est l'action pleine Φ₂ = π
                        (Hamiltonien C4), indépendante de α : l'exclusion survit,
                        θ ne porte que les franges de référence. Prédiction ex ante :
                        σ mesuré = −1.
                   L2 — σ = e^{iπα} : l'exclusion à α = 1/φ exige un second mécanisme
                        (diffusion χ de la cohabitation — frontière M2).
                   Distinguo déposé ex ante : interférométrie d'échange sur particules
                   identiques. AUCUN sauvetage (I5) : la tension est déposée, pas corrigée.

  Contrôles bloquants C0b…C6 — UN SEUL en échec ⟹ REFUTE exit 1.

  Verdicts :
    V+  PAULI_MECANISME_INTERFERENCE_PHASE_DEPOSEE  (tous contrôles)        exit 0
    V3  REFUTE_MECANISME (C2/C6 : le zéro de la famille n'est pas en σ = −1) exit 1
    V4  REFUTE (un contrôle bloquant en échec)                              exit 1

Objets fermés O1–O8. Interdictions : I1 (aucun angle choisi à la main dans les
lectures — le balayage est complet), I5 (aucun sauvetage de la tension).
Sortie : resultat_f12_pauli_v0.json (toutes les lectures, y compris les quasi-échecs).
"""

import cmath
import json
import math
import os
import sys
import time

import numpy as np
from mpmath import mp, mpf

# ================================================================== O1–O8 — objets fermés
PHI = (1.0 + math.sqrt(5.0)) / 2.0          # O1
ALPHA = 1.0 / PHI                            # α = 1/φ

THETA = ALPHA * math.pi / 2.0                # O2 — θ = πα/2 (verbatim KMS C6)

N = 512                                      # O3 — verbatim CHSH O3
L = 20.0 * math.pi
D_OMEGA = 2.0 * math.pi / L                  # 0,1 — harmoniques sur bins entiers
W0 = 1.0                                     # O3 — porteur ω₀ = 1, dyade {1, 2}

TOL_C = 1.0e-12                              # O7 — contrôles généraux
TOL_PHASE = 1.0e-15                          # O7 — phases et fermetures fines
GRID = 720                                   # O7 — balayage complet de la famille σ

mp.dps = 40                                  # route mpmath — dépôt à 30 chiffres


# ================================================================== noyau (O4 — deux routes, verbatim CHSH O2)
def Khat(omega):
    """K̂(ω) = φ/((iω)^α + φ) — route complexe, branche principale. K̂(0) = 1."""
    if omega == 0.0:
        return complex(1.0, 0.0)
    z = 1j * omega
    return PHI / (cmath.exp(ALPHA * cmath.log(z)) + PHI)


def Khat_real(omega):
    """K̂ forme réelle développée (phase incluse) — route indépendante."""
    if omega == 0.0:
        return complex(1.0, 0.0)
    w = abs(omega)
    s = 1.0 if omega > 0.0 else -1.0
    wa = w ** ALPHA
    den = PHI + wa * math.cos(math.pi * ALPHA / 2.0) \
        + 1j * s * wa * math.sin(math.pi * ALPHA / 2.0)
    return PHI / den


# ================================================================== treillis et dyade (O3, verbatim CHSH)
def construit_monde(n_points):
    """Modes de la dyade — amplitude 1 : vecteurs unitaires sous ⟨,⟩ = Σ·/N."""
    x_loc = np.arange(n_points) * (L / n_points)
    e1 = np.exp(1j * W0 * x_loc)
    e2 = np.exp(1j * 2.0 * W0 * x_loc)
    return x_loc, e1, e2


def norme2_mat(M, n_points):
    """O6 — norme à deux particules ‖M‖² = Σ|M_ij|²/N² (convention CHSH)."""
    return float(np.sum(np.abs(M) ** 2)) / (n_points * n_points)


def applique_noyau_2axes(M, khat_w):
    """K̂⊗K̂ appliqué par FFT sur chaque aile (axes 0 = particule A, 1 = particule B)."""
    tmp = np.fft.ifft(khat_w[:, None] * np.fft.fft(M, axis=0), axis=0)
    return np.fft.ifft(khat_w[None, :] * np.fft.fft(tmp, axis=1), axis=1)


def bateman(theta):
    """Hamiltonien C3 verbatim — R(θ), det = 1, trace = 2cosθ, λ = e^{±iθ}."""
    c, s = math.cos(theta), math.sin(theta)
    return [[c, s], [-s, c]]


# ================================================================== exécution
t_exec = time.time()
controles = []


def controle(nom, ok, detail):
    controles.append({"controle": nom, "ok": bool(ok), "detail": detail})
    print(f"  [{'OK ' if ok else 'ÉCHEC'}] {nom} : {detail}")
    return bool(ok)


print("=" * 74)
print("  PAULI F12 V0 — l'exclusion comme interférence, la phase e^{iπα} (MORT 1 de F12)")
print("=" * 74)
print()
print("[CONTRÔLES BLOQUANTS — frontière §4 : un seul échec ⟹ REFUTE exit 1]")
ok_global = True

# ------------------------------------------------------------------ C0b — fermeture algébrique
ec_phi = abs(PHI ** 2 - (PHI + 1.0))
ec_boucle = abs(2.0 * THETA - ALPHA * math.pi)   # la boucle d'échange = phase mémoire doublée
c0b_ok = ec_phi < TOL_PHASE and ec_boucle == 0.0
ok_global &= controle("C0b fermeture algébrique : φ² = φ+1 ; boucle = 2θ = πα (bit-exact)",
                      c0b_ok, f"écart φ² = {ec_phi:.1e} ; écart 2θ−πα = {ec_boucle:.1e}")

# ------------------------------------------------------------------ C1 — noyau double route
ec1 = max(abs(Khat(w) - Khat_real(w)) for w in (1.0, 2.0, 0.5, ALPHA))
ok_global &= controle("C1 noyau double route (complexe vs réelle développée) "
                      "aux points {1, 2, ½, 1/φ}", ec1 < TOL_C, f"écart max = {ec1:.2e}")

# ------------------------------------------------------------------ C2 — P12 : le mécanisme (famille d'interférence)
x, e1, e2 = construit_monde(N)
M_mm = np.outer(e1, e1)                          # double occupation même-mode ω₀
M_dm = np.outer(e1, e2)                          # occupation modes distincts

gamma_grid = np.array([2.0 * math.pi * k / GRID for k in range(GRID)])
famille = np.array([abs(1.0 + cmath.exp(1j * g)) for g in gamma_grid])
argmin = int(np.argmin(famille))
val_min = float(famille[argmin])
nb_presque_zero = int(np.sum(famille < 1.0e-3))  # unicité du zéro (le voisin le plus
                                                 # proche vaut 2·sin(π/GRID) ≈ 8.7e-3)
c2a_ok = (argmin == GRID // 2) and (val_min < TOL_PHASE) and (nb_presque_zero == 1)

psi_exclu = (M_mm - M_mm.T) / math.sqrt(2.0)     # secteur σ = −1, même-mode
norm_exclu = math.sqrt(norme2_mat(psi_exclu, N))
psi_boson = (M_mm + M_mm.T) / math.sqrt(2.0)     # secteur σ = +1, même-mode
norm_boson = math.sqrt(norme2_mat(psi_boson, N))
c2b_ok = norm_exclu < TOL_PHASE and abs(norm_boson - math.sqrt(2.0)) < TOL_C
ok_global &= controle("C2 P12 mécanisme : zéro de |1+σ| UNIQUEMENT en σ = −1 "
                      f"(balayage {GRID} points, unicité) ; amplitude même-mode : "
                      "σ=−1 → 0, σ=+1 → √2 (bunching)",
                      c2a_ok and c2b_ok,
                      f"argmin = γ[{argmin}] = {gamma_grid[argmin]:.6f} rad "
                      f"(π = {math.pi:.6f}) ; val min = {val_min:.2e} ; "
                      f"zéros < 1e-3 : {nb_presque_zero} ; ‖Ψ_exclu‖ = {norm_exclu:.2e} ; "
                      f"‖Ψ_boson‖ = {norm_boson:.6f} (√2 = {math.sqrt(2.0):.6f})")

# ------------------------------------------------------------------ C3 — P13 : [K̂⊗K̂, P₁₂] = 0
rng = np.random.default_rng(79)
M_rand = rng.normal(size=(N, N)) + 1j * rng.normal(size=(N, N))
omega_grid = np.array([m if m <= N // 2 else m - N for m in range(N)],
                      dtype=float) * D_OMEGA
KHAT_W = np.array([Khat(float(w)) for w in omega_grid])
ec3 = float(np.max(np.abs(applique_noyau_2axes(M_rand.T, KHAT_W)
                          - applique_noyau_2axes(M_rand, KHAT_W).T)))
# et sur le bloc dyade 4×4 : K₂ = diag(K̂₁², K̂₁K̂₂, K̂₂K̂₁, K̂₂²), P la permutation d'échange
K1, K2v = Khat(W0), Khat(2.0 * W0)
bloc_K2 = np.diag([K1 * K1, K1 * K2v, K2v * K1, K2v * K2v])
P_ex = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=complex)
ec3_bloc = float(np.max(np.abs(bloc_K2 @ P_ex - P_ex @ bloc_K2)))
ok_global &= controle("C3 P13 fermeture : ‖K̂⊗K̂[Mᵀ] − (K̂⊗K̂[M])ᵀ‖ = 0 (M aléatoire 512²) "
                      "et [K₂, P₁₂] = 0 sur le bloc dyade",
                      ec3 < TOL_PHASE and ec3_bloc < TOL_PHASE,
                      f"écart max M aléatoire = {ec3:.2e} ; bloc dyade = {ec3_bloc:.1e} ; "
                      f"K̂(1)² = {K1*K1:.12f} ; K̂(1)K̂(2) = {K1*K2v:.12f} ; K̂(2)² = {K2v*K2v:.12f}")

# ------------------------------------------------------------------ C4 — P14 : la phase, triple route
sigma_kms = cmath.exp(2j * THETA)                       # route i : θ doublé (KMS C6)
R = bateman(THETA)
eig = np.linalg.eigvals(np.array(R, dtype=float))       # route ii : Bateman C3 numérique
eig_pos = complex(eig[0]) if eig[0].imag > 0 else complex(eig[1])
sigma_bat = eig_pos * eig_pos
sigma_direct = complex(math.cos(ALPHA * math.pi), math.sin(ALPHA * math.pi))  # route iii
ec4_routes = max(abs(sigma_kms - sigma_direct), abs(sigma_bat - sigma_direct))

PHI_M = (1 + mp.sqrt(5)) / 2                            # route mpmath — dépôt 30 chiffres
ALPHA_M = 1 / PHI_M
sigma_mp = mp.exp(1j * ALPHA_M * mp.pi)
ec4_mp = float(abs(sigma_direct - sigma_mp))

sigma_a1 = cmath.exp(1j * math.pi)                       # α = 1 : le signe fermionique
ec4_a1 = abs(sigma_a1 - complex(-1.0, 0.0))
sigma_a1_sq = sigma_a1 * sigma_a1
ec4_a1_sq = abs(sigma_a1_sq - complex(1.0, 0.0))

sigma_sq = sigma_direct * sigma_direct                   # α = 1/φ : braisage ouvert
ec4_sq = abs(sigma_sq - complex(1.0, 0.0))
c4_ok = (ec4_routes < TOL_PHASE and ec4_mp < TOL_PHASE and ec4_a1 < TOL_PHASE
         and ec4_a1_sq < TOL_PHASE and ec4_sq > 1.0)
ok_global &= controle("C4 P14 phase σ(α) = e^{iπα} : triple route déposée (θ doublé = "
                      "Bateman carré = action directe ≤ 1e-15, mpmath ≤ 1e-15) ; "
                      "α=1 : σ = −1 et σ² = +1 ; α=1/φ : σ² ≠ +1 (braisage ouvert, consigné)",
                      c4_ok,
                      f"routes {ec4_routes:.2e} ; mp {ec4_mp:.2e} ; "
                      f"|σ(1)−(−1)| = {ec4_a1:.2e} ; |σ(1)²−1| = {ec4_a1_sq:.2e} ; "
                      f"|σ(1/φ)²−1| = {ec4_sq:.6f}")

# ------------------------------------------------------------------ C5 — P15 : la tension déposée
tension_close = 2.0 + 2.0 * math.cos(ALPHA * math.pi)            # route close
tension_compl = abs(1.0 + sigma_direct) ** 2                     # route complexe
ec5 = abs(tension_close - tension_compl)
psi_tension = (M_mm + sigma_direct * M_mm.T) / math.sqrt(2.0)    # l'objet dyade réel
survie_tension = norme2_mat(psi_tension, N)                      # ‖Ψ‖² = |1+σ|²/2
tension_a1_close = 2.0 + 2.0 * math.cos(math.pi)                 # α = 1 : 0.0 bit-exact
c5_ok = (ec5 < TOL_PHASE and tension_close > 1.0
         and abs(tension_a1_close) == 0.0)
ok_global &= controle("C5 P15 tension : |1+σ(1/φ)|² = 2+2cos(πα) ≠ 0 (l'interférence "
                      "seule n'exclut plus) ; α=1 : 0.0 bit-exact (exclusion recouvrée)",
                      c5_ok,
                      f"close = {tension_close:.12f} ; complexe = {tension_compl:.12f} ; "
                      f"écart routes = {ec5:.2e} ; ‖Ψ_σ‖² dyade = {survie_tension:.12f} "
                      f"(= tension/2) ; α=1 : {tension_a1_close:.1e} (bit-exact)")

# ------------------------------------------------------------------ C6 — témoins falsifiants
t_mm_p = abs(1.0 + 1.0) ** 2                                     # (i) σ=+1 : bunching
t_gen = abs(1.0 + cmath.exp(1j * 0.7)) ** 2                      # (ii) σ générique
t_gen_close = 2.0 + 2.0 * math.cos(0.7)
psi_dm_a = (M_dm - M_dm.T) / math.sqrt(2.0)                      # (iii) modes distincts
norm_dm_a = math.sqrt(norme2_mat(psi_dm_a, N))                   # doit survivre = 1
psi_dm_s = (M_dm + M_dm.T) / math.sqrt(2.0)
norm_dm_s = math.sqrt(norme2_mat(psi_dm_s, N))
c6_ok = (abs(t_mm_p - 4.0) < TOL_PHASE
         and abs(t_gen - t_gen_close) < TOL_PHASE and t_gen > 0.5
         and abs(norm_dm_a - 1.0) < TOL_C and abs(norm_dm_s - 1.0) < TOL_C)
ok_global &= controle("C6 témoins : σ=+1 → |1+σ|²=4 (bunching, non-exclu) ; σ générique "
                      "(γ=0.7) → non nul ; modes distincts : secteur antisymétrique ET "
                      "symétrique = 1 (l'exclusion ne tue que la cohabitation — "
                      "condition du remplissage M3)",
                      c6_ok,
                      f"|1+σ|²(σ=+1) = {t_mm_p:.1f} ; |1+σ|²(γ=0.7) = {t_gen:.6f} vs "
                      f"close {t_gen_close:.6f} ; ‖Ψ_dm^A‖ = {norm_dm_a:.12f} ; "
                      f"‖Ψ_dm^S‖ = {norm_dm_s:.12f}")

# ================================================================== verdict
print()
deps = {
    "sigma_1_over_phi_mp30": mp.nstr(sigma_mp, 30),
    "sigma_1_over_phi_float": repr(sigma_direct),
    "sigma_carre_1_over_phi": repr(sigma_sq),
    "sigma_alpha_1": repr(sigma_a1),
    "tension_1_plus_sigma_carre": repr(tension_close),
    "survie_dyade_norme2": survie_tension,
    "ecart_sigma2_moins_1": ec4_sq,
    "bunching_sigma_plus_1": t_mm_p,
}
for k, v in deps.items():
    print(f"  [DÉPÔT] {k} = {v}")

verdict, code = ("PAULI_MECANISME_INTERFERENCE_PHASE_DEPOSEE", 0) if ok_global \
    else ("REFUTE", 1)
print()
print(f"VERDICT : {verdict} — exit {code}")
print(f"Résultat : resultat_f12_pauli_v0.json ({time.time() - t_exec:.1f} s)")

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "resultat_f12_pauli_v0.json"), "w", encoding="utf-8") as fh:
    json.dump({"verdict": verdict, "ok": bool(ok_global), "exit_code": code,
               "controles": controles, "depots": deps,
               "grille": {"points": GRID, "argmin_index": argmin,
                          "val_min": val_min, "zeros_uniques": nb_presque_zero}},
              fh, ensure_ascii=False, indent=2)

sys.exit(code)
