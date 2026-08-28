# -*- coding: utf-8 -*-
"""
CHSH THU V0 — exécution machine du dépôt DEPOT_CHSH_THU_V0.md (28/08/2026)

Le dépôt est FERMÉ et ANTÉRIEUR à ce script (contrôle C0a : mtime dépôt < exécution).
Aucune lecture, barre ou verdict n'est modifiable ici — ce script ne fait qu'exécuter :

  Famille A (cohérence)    : état de Bell de la dyade (harmoniques 1 et 2 de Ψ₁),
                             settings déposés (0, π/2, π/4, −π/4),
                             S₀ contre la borne de Tsirelson 2√2 (barre 1e-9)
                             + triple route (machine 512×512, algèbre 2×2, cibles cos(a−b))
  Famille B (physique THU) : état noyau (K̂⊗K̂)|Φ+⟩ renormalisé,
                             prédiction analytique déposée S = 2√(1+ρ²),
                             ρ = 2|c₁c₂|/(|c₁|²+|c₂|²), c_i = K̂(ω_i)²
                             lecture machine Horodecki S_max = 2√(s₁²+s₂²) (SVD du tenseur T)
                             horizon déposé : 2 < S_max ≤ 2√2
  Témoin produit (C3)      : état séparable — S ≤ 2 (aucune fausse violation)

  Contrôles bloquants C0a…C6 (dépôt §3) — UN SEUL en échec ⟹ V4 REFUTE exit 1.

  Verdicts (dépôt §4) :
    V+  CHSH_THU_CONFORME               (A + B dans les barres)           exit 0
    V2  TSIRELSON_OK_MEMOIRE_DIVERGENTE (A ok, B divergente — consignée)  exit 0
    V3  REFUTE_TSIRELSON_NON_REPRODUIT  (A en échec)                      exit 1
    V4  REFUTE  (contrôle KO)                                             exit 1

Objets fermés O1–O8, interdictions I1–I5, honnêteté §6 : voir le dépôt.
Sortie : resultat_chsh_thu_v0.json (toutes les lectures, y compris les quasi-échecs).
"""

import cmath
import json
import math
import os
import sys
import time

import numpy as np

# ================================================================== O1–O8 — objets fermés
PHI = (1.0 + math.sqrt(5.0)) / 2.0          # O1
ALPHA = 1.0 / PHI                            # α = 1/φ

N = 512                                      # O3
L = 20.0 * math.pi
D_OMEGA = 2.0 * math.pi / L                  # 0,1 — harmoniques sur bins entiers
NYQUIST = (N / 2) * D_OMEGA                  # 25,6 > max|ω| = 2 : zéro fuite spectrale

TSIRELSON = 2.0 * math.sqrt(2.0)             # O8 — 2,8284271247461903
BORNE_CLASSIQUE = 2.0                        # O8
W0 = 1.0                                     # O5 — porteur ω₀ = 1, dyade {1, 2}

TOL_TSIRELSON = 1.0e-9                       # §1 — S₀ vs 2√2, chaque E vs cos(a−b)
TOL_HORODECKI = 1.0e-9                       # §1 — S_max vs analytique ; C6
TOL_ORTHONORM = 1.0e-12                      # §1 — C2 ; C1 ; C4
TOL_C5 = 1.0e-12                             # §3 — changement de treillis
TOL_C0B = 1.0e-15                            # §3 — fermeture algébrique

SETTINGS = (0.0, math.pi / 2.0, math.pi / 4.0, -math.pi / 4.0)  # (θ_A, θ_A′, θ_B, θ_B′) — déposés

RACINE = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.join(RACINE, "DEPOT_CHSH_THU_V0.md")
SORTIE = os.path.join(RACINE, "resultat_chsh_thu_v0.json")

t_exec = time.time()
controles = []


def controle(nom, ok, detail):
    controles.append({"controle": nom, "ok": bool(ok), "detail": detail})
    print(f"  [{'OK ' if ok else 'ÉCHEC'}] {nom} : {detail}")
    return bool(ok)


def note(nom, detail):
    print(f"  [   ] {nom} : {detail}")


# ================================================================== noyau (O2 — deux routes, verbatim jaugage V0)
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


# ================================================================== treillis et dyade (O3–O5)
def construit_grille_frequence(n_points):
    m_bins = np.arange(n_points)
    return np.where(m_bins <= n_points // 2, m_bins, m_bins - n_points).astype(float) * D_OMEGA


def construit_monde(n_points):
    """Treillis et modes de la dyade — amplitude 1 : vecteurs unitaires sous ⟨,⟩ = Σ·/N."""
    x_loc = np.arange(n_points) * (L / n_points)
    e1 = np.exp(1j * W0 * x_loc)
    e2 = np.exp(1j * 2.0 * W0 * x_loc)
    return x_loc, e1, e2


def norme(v, n_points):
    """O4 — norme unitaire ‖ψ‖² = Σ|ψₙ|²/N (Parseval)."""
    return math.sqrt(float(np.sum(np.abs(v) ** 2)) / n_points)


def inner(a, b, n_points):
    """O4 — ⟨a,b⟩ = Σ conj(aₙ)·bₙ / N."""
    return complex(np.sum(np.conj(a) * b) / n_points)


def proj(e_vec, n_points):
    """Projecteur |e⟩⟨e| sous ⟨,⟩ = Σ·/N : P·v = e·⟨e,v⟩."""
    return np.outer(e_vec, np.conj(e_vec)) / n_points


def observables_pleins(e1, e2, n_points):
    """Z, X, Y incrustés dans le treillis (N×N) — route machine."""
    P1 = proj(e1, n_points)
    P2 = proj(e2, n_points)
    E12 = np.outer(e1, np.conj(e2)) / n_points   # |φ₁⟩⟨φ₂|
    E21 = np.outer(e2, np.conj(e1)) / n_points   # |φ₂⟩⟨φ₁|
    Z = P1 - P2
    X = E12 + E21
    Y = -1j * E12 + 1j * E21
    return {"Z": Z, "X": X, "Y": Y}


def A_plein(theta, obs):
    """O7 — A(θ) = cosθ·Z + sinθ·X (valeurs propres ±1 sur la dyade)."""
    return math.cos(theta) * obs["Z"] + math.sin(theta) * obs["X"]


def A_2x2(theta):
    """Même observable en algèbre 2×2 — route analytique."""
    return np.array([[math.cos(theta), math.sin(theta)],
                     [math.sin(theta), -math.cos(theta)]], dtype=complex)


def attente_E(M, A, B, n_points):
    """E = ⟨Φ|A⊗B|Φ⟩ = Σ conj(M)·(A·M·Bᵀ) / N² — jamais de matrice N²×N²."""
    AMB = A @ M @ B.T
    return complex(np.sum(np.conj(M) * AMB) / (n_points * n_points))


def attente_E_2x2(c1, c2, A2, B2):
    """E en algèbre 2×2 pour Ψ = c₁|00⟩ + c₂|11⟩ — route analytique fermée."""
    Psi = np.diag([complex(c1), complex(c2)])
    return complex(np.sum(np.conj(Psi) * (A2 @ Psi @ B2.T)))


def chsh(E_ab, E_ab2, E_a2b, E_a2b2):
    """S = E(a,b) + E(a,b′) + E(a′,b) − E(a′,b′)."""
    return E_ab + E_ab2 + E_a2b - E_a2b2


def tenseur_T(M, obs, n_points):
    """T_ij = ⟨Φ|Σ_i⊗Σ_j|Φ⟩ pour i,j ∈ {X,Y,Z} — route machine."""
    noms = ["X", "Y", "Z"]
    T = np.zeros((3, 3), dtype=complex)
    for i, si in enumerate(noms):
        for j, sj in enumerate(noms):
            T[i, j] = attente_E(M, obs[si], obs[sj], n_points)
    return T


def horodecki_S_max(T):
    """O8 — S_max = 2√(s₁²+s₂²), s = valeurs singulières de T (SVD, triées)."""
    s = np.linalg.svd(T, compute_uv=False)
    return 2.0 * math.sqrt(float(s[0]) ** 2 + float(s[1]) ** 2), [float(v) for v in s]


def applique_noyau_2axes(M, khat_w):
    """K̂⊗K̂ appliqué par FFT sur chaque aile (axes 0 = x_A, 1 = x_B)."""
    tmp = np.fft.ifft(khat_w[:, None] * np.fft.fft(M, axis=0), axis=0)
    return np.fft.ifft(khat_w[None, :] * np.fft.fft(tmp, axis=1), axis=1)


def S_zero_machine(n_points):
    """Famille A complète à taille N donnée — S₀ route machine (utilisé aussi par C5)."""
    _, e1, e2 = construit_monde(n_points)
    obs = observables_pleins(e1, e2, n_points)
    M = (np.outer(e1, e1) + np.outer(e2, e2)) / math.sqrt(2.0)
    ta, ta2, tb, tb2 = SETTINGS
    E1 = attente_E(M, A_plein(ta, obs), A_plein(tb, obs), n_points)
    E2 = attente_E(M, A_plein(ta, obs), A_plein(tb2, obs), n_points)
    E3 = attente_E(M, A_plein(ta2, obs), A_plein(tb, obs), n_points)
    E4 = attente_E(M, A_plein(ta2, obs), A_plein(tb2, obs), n_points)
    return chsh(E1, E2, E3, E4)


# ================================================================== T0 — ANTÉRIORITÉ ET CONTRÔLES
print("=" * 74)
print("  CHSH THU V0 — la non-localité dans le formalisme dérivé (dépôt fermé du 28/08/2026)")
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

pts_noyau = [1.0, 2.0, 0.5, ALPHA]
ec1 = max(abs(Khat(w) - Khat_real(w)) for w in pts_noyau)
ok_global &= controle("C1 noyau double route (complexe vs réelle développée) aux points {1, 2, ½, 1/φ}",
                      ec1 < TOL_ORTHONORM, f"écart max = {ec1:.2e}")

x, e1, e2 = construit_monde(N)
n2_orth = abs(inner(e1, e2, N))
n1_err = abs(norme(e1, N) - 1.0)
n2_err = abs(norme(e2, N) - 1.0)
obs = observables_pleins(e1, e2, N)
M_bell = (np.outer(e1, e1) + np.outer(e2, e2)) / math.sqrt(2.0)
nbell_err = abs(math.sqrt(float(np.sum(np.abs(M_bell) ** 2)) / (N * N)) - 1.0)
c2_max = max(n2_orth, n1_err, n2_err, nbell_err)
ok_global &= controle("C2 orthonormalité de la dyade et norme de |Φ+⟩",
                      c2_max < TOL_ORTHONORM,
                      f"|⟨φ₁,φ₂⟩| = {n2_orth:.2e} ; ‖φ_i‖−1 max = {max(n1_err, n2_err):.2e} ; "
                      f"‖Φ+⟩−1 = {nbell_err:.2e}")

omega_grid = construit_grille_frequence(N)
KHAT_W = np.array([Khat(w) for w in omega_grid])


def applique_noyau(v):
    """K̂[ψ] = IFFT(K̂(ω)·FFT(ψ)) — convention numpy 1/N incluse."""
    return np.fft.ifft(KHAT_W * np.fft.fft(v))


errs_eig = []
for idx, (e_i, w_i) in enumerate([(e1, W0), (e2, 2.0 * W0)]):
    errs_eig.append(norme(applique_noyau(e_i) - Khat(w_i) * e_i, N))
ec4 = max(errs_eig)
ok_global &= controle("C4 le noyau agit en valeurs propres exactes sur les harmoniques "
                      "(route FFT vs forme close)",
                      ec4 < TOL_ORTHONORM,
                      f"‖K̂[φ₁]−K̂(1)·φ₁‖ = {errs_eig[0]:.2e} ; ‖K̂[φ₂]−K̂(2)·φ₂‖ = {errs_eig[1]:.2e}")

# ================================================================== FAMILLE A — REPRODUCTION DE LA MQ
print()
print("[FAMILLE A — |Φ+⟩ de la dyade : S₀ contre la borne de Tsirelson 2√2]")
ta, ta2, tb, tb2 = SETTINGS
Aa, Aa2 = A_plein(ta, obs), A_plein(ta2, obs)
Bb, Bb2 = A_plein(tb, obs), A_plein(tb2, obs)

E_machine = [attente_E(M_bell, Aa, Bb, N), attente_E(M_bell, Aa, Bb2, N),
             attente_E(M_bell, Aa2, Bb, N), attente_E(M_bell, Aa2, Bb2, N)]
E_cibles = [math.cos(ta - tb), math.cos(ta - tb2),
            math.cos(ta2 - tb), math.cos(ta2 - tb2)]          # O8 — cibles fermées cos(a−b)
Aa2m, Aa2m2 = A_2x2(ta), A_2x2(ta2)
Bb2m, Bb2m2 = A_2x2(tb), A_2x2(tb2)
c_bell = 1.0 / math.sqrt(2.0)
E_2x2 = [attente_E_2x2(c_bell, c_bell, Aa2m, Bb2m), attente_E_2x2(c_bell, c_bell, Aa2m, Bb2m2),
         attente_E_2x2(c_bell, c_bell, Aa2m2, Bb2m), attente_E_2x2(c_bell, c_bell, Aa2m2, Bb2m2)]

S0_machine = float(chsh(*E_machine).real)
S0_2x2 = float(chsh(*E_2x2).real)
S0_cible = float(chsh(*[complex(v) for v in E_cibles]).real)
for k, (em, e2x2, ec_) in enumerate(zip(E_machine, E_2x2, E_cibles)):
    note(f"E{['(a,b)', '(a,b′)', '(a′,b)', '(a′,b′)'][k]}",
         f"machine = {em.real:+.15f} ; 2×2 = {e2x2.real:+.15f} ; cible cos = {ec_:+.15f}")
ecA = max(abs(S0_machine - TSIRELSON), abs(S0_2x2 - TSIRELSON), abs(S0_cible - TSIRELSON),
          max(abs(E_machine[k].real - E_cibles[k]) for k in range(4)))
A_ok = (ecA < TOL_TSIRELSON) and (S0_machine > BORNE_CLASSIQUE)
note("A1/A2 — S₀ triple route",
     f"machine = {S0_machine:.15f} ; 2×2 = {S0_2x2:.15f} ; cible = {S0_cible:.15f} ; "
     f"2√2 = {TSIRELSON:.15f} ; écart max = {ecA:.2e} ; S₀ > 2 : {S0_machine > BORNE_CLASSIQUE} "
     f"→ {'le formalisme dérivé VIOLE la borne classique et atteint Tsirelson' if A_ok else 'ÉCHEC FAMILLE A'}")

# ================================================================== TÉMOIN PRODUIT + C6
M_prod = np.outer(e1, e1)
E_prod = [attente_E(M_prod, Aa, Bb, N), attente_E(M_prod, Aa, Bb2, N),
          attente_E(M_prod, Aa2, Bb, N), attente_E(M_prod, Aa2, Bb2, N)]
S_prod = float(chsh(*E_prod).real)
ok_global &= controle("C3 témoin produit (φ₁⊗φ₁, mêmes settings) : aucune fausse violation",
                      S_prod <= BORNE_CLASSIQUE + TOL_TSIRELSON,
                      f"S_prod = {S_prod:.15f} ≤ 2 + 1e-9 (cible analytique √2 ≈ {math.sqrt(2.0):.15f})")

T_bell = tenseur_T(M_bell, obs, N)
S_max_bell, s_bell = horodecki_S_max(T_bell)
ec6 = abs(S_max_bell - TSIRELSON)
ok_global &= controle("C6 Horodecki (route T/SVD) sur |Φ+⟩ pur redonne 2√2",
                      ec6 < TOL_HORODECKI,
                      f"S_max = {S_max_bell:.15f} ; valeurs singulières = {s_bell} ; écart = {ec6:.2e}")

# ================================================================== FAMILLE B — DYNAMIQUE DE MÉMOIRE
print()
print("[FAMILLE B — état noyau (K̂⊗K̂)|Φ+⟩ : l'intrication sous la mémoire ABC]")
khat1, khat2 = Khat(W0), Khat(2.0 * W0)
c1_raw = khat1 ** 2
c2_raw = khat2 ** 2
norme_K_theo = math.sqrt(abs(c1_raw) ** 2 + abs(c2_raw) ** 2)

M_K_brut = applique_noyau_2axes(M_bell, KHAT_W)
norme_K_machine = math.sqrt(float(np.sum(np.abs(M_K_brut) ** 2)) / (N * N))
M_K = M_K_brut / norme_K_machine

rho = 2.0 * abs(c1_raw) * abs(c2_raw) / (abs(c1_raw) ** 2 + abs(c2_raw) ** 2)
S_analytique = 2.0 * math.sqrt(1.0 + rho ** 2)

T_K = tenseur_T(M_K, obs, N)
S_max_K, s_K = horodecki_S_max(T_K)

S_settings_K = float(chsh(attente_E(M_K, Aa, Bb, N), attente_E(M_K, Aa, Bb2, N),
                          attente_E(M_K, Aa2, Bb, N), attente_E(M_K, Aa2, Bb2, N)).real)

note("B1 coefficients fermés",
     f"K̂(1) = {abs(khat1):.12f}·e^({math.atan2(khat1.imag, khat1.real):+.12f}·i) ; "
     f"K̂(2) = {abs(khat2):.12f}·e^({math.atan2(khat2.imag, khat2.real):+.12f}·i)")
note("norme post-noyau (avant renormalisation)",
     f"machine = {norme_K_machine:.12f} ; forme close √(|c₁|²+|c₂|²) = {norme_K_theo:.12f} ; "
     f"écart = {abs(norme_K_machine - norme_K_theo):.2e}")
note("B2 prédiction analytique déposée",
     f"ρ = {rho:.12f} → S_analytique = 2√(1+ρ²) = {S_analytique:.12f}")
note("B3 lecture machine Horodecki",
     f"S_max = {S_max_K:.12f} ; valeurs singulières = {s_K}")
ecB = abs(S_max_K - S_analytique)
horizon_ok = (BORNE_CLASSIQUE + TOL_TSIRELSON) < S_max_K <= (TSIRELSON + TOL_TSIRELSON)
B_ok = (ecB < TOL_HORODECKI) and horizon_ok
note("barres B",
     f"|S_max − S_analytique| = {ecB:.2e} (barre 1e-9) ; horizon 2 < S_max ≤ 2√2 : "
     f"{horizon_ok} → {'la mémoire ABC amortit la violation SANS la détruire, conforme à la forme close' if B_ok else 'DIVERGENCE (V2)'}")
note("B4 lecture informative SANS verdict",
     f"S aux settings V0 sur l'état noyau = {S_settings_K:.12f} "
     f"(l'optimum n'est plus aux angles de |Φ+⟩)")

# ================================================================== C5 — CHANGEMENT DE TREILLIS
S0_1024 = float(S_zero_machine(1024).real)
ec5 = abs(S0_1024 - S0_machine)
ok_global &= controle("C5 changement de treillis N = 512 → 1024 (invariance — sommes racines-de-l'unité)",
                      ec5 < TOL_C5, f"S₀(1024) = {S0_1024:.15f} ; écart = {ec5:.2e}")

# ================================================================== VERDICT
print()
print("=" * 74)
if not ok_global:
    verdict, code = "V4 — REFUTE", 1
    raison = "un contrôle bloquant est en échec (dépôt §3 : aucun sauvetage)"
elif not A_ok:
    verdict, code = "V3 — REFUTE_TSIRELSON_NON_REPRODUIT", 1
    raison = ("le formalisme dérivé ne produit pas la violation quantique : "
              "la chaîne Hilbert/Born prétendue dérivée est prise en défaut")
elif B_ok:
    verdict, code = "V+ — CHSH_THU_CONFORME", 0
    raison = ("Tsirelson reproduit (A) et la mémoire ABC amortit l'intrication "
              "conformément à la forme close déposée, sans détruire la non-localité (B)")
else:
    verdict, code = "V2 — TSIRELSON_OK_MEMOIRE_DIVERGENTE", 0
    raison = ("Tsirelson reproduit (A) mais la lecture mémoire B s'écarte de la prédiction "
              "analytique déposée ou de l'horizon — divergence consignée telle quelle")

print(f"  VERDICT : {verdict}")
print(f"  RAISON  : {raison}")
print(f"  SORTIE  : exit {code}")
print("=" * 74)

# ================================================================== JSON — toutes les lectures (I3)


def cplx(z):
    return {"abs": abs(z), "arg": math.atan2(z.imag, z.real), "re": z.real, "im": z.imag}


resultat = {
    "depot": "DEPOT_CHSH_THU_V0.md",
    "date_execution": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t_debut)),
    "c0a": {"mtime_depot": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime_depot)),
            "mtime_execution": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t_debut)),
            "ok": bool(c0a_ok)},
    "objets_fermes": {"phi": PHI, "alpha": ALPHA, "N": N, "L": L, "delta_omega": D_OMEGA,
                      "nyquist": NYQUIST, "tsirelson": TSIRELSON, "borne_classique": BORNE_CLASSIQUE,
                      "settings": list(SETTINGS), "tol_tsirelson": TOL_TSIRELSON,
                      "tol_horodecki": TOL_HORODECKI, "tol_orthonorm": TOL_ORTHONORM, "tol_c5": TOL_C5},
    "controles": controles,
    "famille_A": {"E_machine": [float(v.real) for v in E_machine],
                  "E_2x2": [float(v.real) for v in E_2x2],
                  "E_cibles_cos": E_cibles,
                  "S0_machine": S0_machine, "S0_2x2": S0_2x2, "S0_cible": S0_cible,
                  "ecart_max_A": float(ecA), "A_ok": bool(A_ok)},
    "temoin_produit": {"S_prod": S_prod, "cible_analytique": math.sqrt(2.0)},
    "c6_horodecki_pur": {"S_max": S_max_bell, "valeurs_singulieres": s_bell},
    "famille_B": {"Khat_1": cplx(khat1), "Khat_2": cplx(khat2),
                  "c1": cplx(c1_raw), "c2": cplx(c2_raw),
                  "norme_post_noyau_avant_renormalisation_machine": norme_K_machine,
                  "norme_post_noyau_forme_close": norme_K_theo,
                  "rho": float(rho), "S_analytique": float(S_analytique),
                  "S_max_machine": float(S_max_K), "valeurs_singulieres": s_K,
                  "ecart_B": float(ecB), "horizon_ok": bool(horizon_ok), "B_ok": bool(B_ok),
                  "S_settings_V0_sur_etat_noyau_sans_verdict": S_settings_K},
    "c5_changement_treillis": {"S0_N1024": S0_1024, "ecart": float(ec5)},
    "verdict": {"nom": verdict, "raison": raison, "exit_code": code},
}
with open(SORTIE, "w", encoding="utf-8") as f:
    json.dump(resultat, f, ensure_ascii=False, indent=2)
print(f"Résultat consigné : {SORTIE}")

sys.exit(code)
