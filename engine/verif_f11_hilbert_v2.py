#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F11 HILBERT V2 — Voie 3 spectrale (C-H3) : le couple déposé ferme l'arène
=========================================================================
Suite de verif_f11_hilbert_v1 (Voie 2a fermée). Cahier des charges :
FRONTIERE_F11_HILBERT.md §3 Voie 3 et §4 C-H3 (fort) :
  « déduire le théorème spectral (valeurs propres réelles, états propres
  complets) depuis la mémoire d'or, sans postuler Hilbert ».
Falsifiabilité §4 : si une structure non-hilbertienne est aussi stable, F11
est réfutée — le script teste AUSSI ce critère (C3/C5).

OBJETS DÉPOSÉS (aucun réinventé — anti-circularité) :
  • noyau mémoire  K̂(ω) = φ/((iω)^α + φ), α = 1/φ, K̂(0) = 1, branche
    principale  [FORCE V1.3 O2, verbatim jaugage V0]
  • évolution Zeno E_{1/φ}(iEt^{1/φ}/ℏ)  [DEPOT_E1bis_ZENO_FRACTIONNAIRE]
  • poids mémoire (iω)^α = ω^α·e^{iθ}, θ = πα/2 = 0.9708 rad — non-hermitien,
    PT brisé, SYSTÈME OUVERT  [DEPOT_HAMILTONIEN_ABC_THU_V0 C1/C2]
  • modulation position e^{ia·kx} — l'unitaire dont le défaut de commutation
    avec K̂ est EXACTEMENT la diffusion fréquentielle χ  [FORCE V1.3 §0]
  • flot unitaire e^{−iHt}, H hermitien quelconque (classe α→1, V1-C4)
  • phase d'influence Φ₂ = seul branchement compatible  [KMS DPHI ; HAMILTONIEN
    ABC V0 : noyau ❌, opérateur spectral ❌, hamiltonien fermé ❌]

THÈSE T1 — Le calcul fonctionnel de la mémoire d'or est SPECTRAL :
  U(t) = E_{1/φ}((i/ħ)Ĥt^{1/φ}) satisfait
    U(t) = Σ_k E_{1/φ}(iλ_k t^{1/φ}/ℏ) · P_k
  sur toute base propre de Ĥ (ħ = 1). Machine : série matricielle DIRECTE
  Σ_n (iĤt^α)ⁿ/Γ(nα+1) (mpmath dps 50, AUCUNE diagonalisation, AUCUN produit
  scalaire — anti-circularité) vs résolution spectrale de ĥ : concordance,
  et le mapping spectral spec(f(Ĥ)) = f(spec(Ĥ)) est vérifié sur multiset trié.
  Étendue honnête : Ĥ hermitien diagonalisable, dimension finie. Jordan
  (non-normaux) et dimension infinie : ouverts — consignés.

THÈSE T2 — Critère spectral d'isométrie : |λ| = 1.
  Une norme d'arène ℓ^p est invariante sous U(t) ⟺ |E_{1/φ}(iλt^{1/φ})| = 1
  pour toute valeur propre λ. Machine :
    (a) α = 1/φ : AUCUNE arène ℓ^p n'est conservée (le module s'écarte de 1
        — conséquence spectrale de arg(iω)^α = θ ≠ 0, HAMILTONIEN ABC C1) ;
    (b) α = 1 : U(t) = e^{iλt}, |e^{iλt}| = 1 — TOUTES les ℓ^p survivent.
        FALSIFICATEUR réalisé et consigné : à α = 1 la sélection n'existe pas.
        La sélection n'existe QUE parce que α = 1/φ < 1 (système ouvert).

THÈSE T3 — Le couple déposé ferme l'arène (commutant trivial) :
  K̂ est diagonal en FRÉQUENCE ([K̂, e^{iωt}] = 0 exactement) : la mémoire
  SÉLECTIONNE la base de fréquences. La modulation e^{ia·kx} (dépôt FORCE,
  a·k·L = 2πφ — la même irrationalité) est diagonale en POSITION.
    • commutant du flot fréquentiel seul : dim N (tous les circulants) —
      un seul opérateur ne sélectionne rien (écho de V1-C5) ;
    • commutant du COUPLE {e^{iωt}, e^{ia·kx}} : TRIVIAL (dim 1, S = cI)
      ⟹ la seule forme quadratique invariante sous les deux familles est
      ‖x‖² = c·Σ|x|² : L², sans postuler Hilbert (C-H3 partiel : le spectre
      du couple impose l'arène).
  → Symétrique spectral exact du Théorème B de V1 : mémoire + influence.

C6 — Retour physique (dépôt Zeno) : 1 − P(t) = c₂·t^{2/φ}(1 + O(t^{2/φ})),
  c₂ = 2/Γ(2/φ+1) − 1/Γ(1/φ+1)² — exposant ET coefficient machine, sans
  cancellation. CORRECTION DE THÉORIE (leçon run 2, la machine a raison) :
  |E_{1/φ}(iξ)|² est PAIRE en ξ — E(iξ) = A(ξ²) + iξ·B(ξ²), les termes
  impairs entrent AU CARRÉ dans |E|², donc 1 − P = c₂ξ² + c₄ξ⁴ + ⋯ sans
  terme ξ³ ; la correction relative est O(ξ²) = O(t^{2/φ}), PAS O(t^{1/φ})
  comme annoncé d'abord — et le rapport d'erreurs successifs tend vers
  2^{−2/φ} = 2^{−2α} = 0.4247 (mesuré 0.4249). La théorie se corrige
  devant le nombre, jamais l'inverse.

Contrôles :
  C1  Série matricielle ML directe (mpmath) vs résolution spectrale ;
      mapping spectral sur multiset trié ; complétude V V† = I
  C2  Rayon spectral d'arène : ‖U‖_{ℓ^p→ℓ^p} = max_k |E_{1/φ}(iλ_k t^α)|
      (p = 1, 2, 4, ∞ — quatre routes indépendantes)
  C3  α = 1/φ : contraction stricte dans toute arène ℓ^p (vecteurs de base
      inclus) ; α = 1 : toutes les arènes survivent (falsificateur consigné)
  C4  Commutants : dim(flot fréquentiel seul) = N ; dim(couple) = 1 ;
      générateur = cI ; défaut [K̂, modulation] ≠ 0 (χ, machine)
  C5  Matrice de falsifiabilité : 4 normes × 4 colonnes (flot, modulation,
      couple, K̂ seul) — motif exact, seul L2 passe le couple
  C6  Zeno : c₂ + ordre t^{1/φ} machine

Sortie : verdict exit 0 (conforme) / exit 1 (réfuté) + resultat_f11_hilbert_v2.json
Leçon (FORCE V1.2) : tout nombre déposé est calculé par machine, ici.
"""

import cmath
import json
import math
import sys

import numpy as np
from mpmath import mp, mpf, gamma as mgamma, mpc as mpmath_mpc

mp.dps = 50

# ------------------------------------------------------------------ constantes
PHI = (1.0 + math.sqrt(5.0)) / 2.0          # φ
ALPHA = 1.0 / PHI                            # α = 1/φ ≈ 0.6180339887498948
THETA = math.pi * ALPHA / 2.0                # θ = πα/2 = 0.970806 rad
N = 32                                       # dimension du treillis (pair)
N_MAX = 220                                  # troncature séries (dps 50)

PHI_M, ALPHA_M = mpf(PHI), mpf(1) / mpf(PHI)


def mpmc(z):
    """float/complex/mpf/mpc → mpmath mpc (idempotent)."""
    if isinstance(z, mp.mpc):
        return z
    if isinstance(z, mp.mpf):
        return mp.mpc(z, mpf(0))
    if isinstance(z, complex):
        return mp.mpc(float(z.real), float(z.imag))
    return mp.mpc(float(z), 0.0)


# ------------------------------------------------------------------ Mittag-Leffler
def ml_series(z, alpha=ALPHA_M, n_max=N_MAX):
    """E_α(z) = Σ_{n≥0} zⁿ/Γ(αn+1) — termes DIRECTS, mpmath dps 50.
    Leçon (E1bis/ZENO) : jamais de représentation intégrale ni de produit
    gamma ; |z| ≤ 7.3 ici, la cancellation maximale (~e^20) laisse > 40
    chiffres significatifs à dps 50."""
    s = mpf(1)
    term = mpf(1)
    for n in range(1, n_max + 1):
        # récurrence : term_n = term_{n-1} · z · Γ(α(n−1)+1)/Γ(αn+1)
        term = term * z * mgamma(alpha * (n - 1) + 1) / mgamma(alpha * n + 1)
        s += term
        if abs(term) < mpf(10) ** (-45):
            break
    return s


def ml_matrix(Z_np, alpha=ALPHA_M, n_max=N_MAX):
    """Σ_n Zⁿ/Γ(αn+1) sur MATRICE mpmath — voie directe : aucune
    diagonalisation, aucun produit scalaire (anti-circularité T1)."""
    d = Z_np.shape[0]
    Zm = mp.matrix([[mpmc(Z_np[i, j]) for j in range(d)] for i in range(d)])
    S = mp.eye(d)
    term = mp.eye(d)
    for n in range(1, n_max + 1):
        # récurrence par RAPPORT GAMMA (leçon run 2 : term/Γ(αn+1) cumulatif
        # donnait Zⁿ/∏Γ(αk+1) — garbage 1e+02 ; chaque terme doit être
        # Zⁿ/Γ(αn+1), donc on multiplie par Γ(α(n−1)+1)/Γ(αn+1))
        term = term * Zm * mgamma(alpha * (n - 1) + 1) / mgamma(alpha * n + 1)
        S += term
        if max(abs(term[i, j]) for i in range(d) for j in range(d)) < mpf(10) ** (-45):
            break
    return S


# ------------------------------------------------------------------ noyau déposé (O2 verbatim FORCE)
def Khat(omega):
    """K̂(ω) = φ/((iω)^α + φ) — branche principale, K̂(0) = 1 [FORCE V1.3 O2]."""
    if omega == 0.0:
        return complex(1.0, 0.0)
    z = 1j * omega
    return PHI / (cmath.exp(ALPHA * cmath.log(z)) + PHI)


# ------------------------------------------------------------------ treillis
F_UNIT = np.fft.fft(np.eye(N)) / math.sqrt(N)            # FFT unitaire
OMEGAS = np.array([m if m <= N // 2 else m - N for m in range(N)],
                  dtype=float) * (2 * math.pi / N)        # fréquences signées
KHAT_W = np.array([Khat(float(m if m <= N // 2 else m - N))
                   for m in range(N)])                    # K̂ sur ω SGNÉ du treillis
MODU = np.diag(np.exp(2j * math.pi * PHI * np.arange(N)))  # modulation e^{ia·kx}
KF_POS = F_UNIT.conj().T @ np.diag(KHAT_W) @ F_UNIT       # K̂ en base de position


# ------------------------------------------------------------------ contrôles

def c1_calcul_fonctionnel_spectral():
    """T1 : série matricielle ML directe (aucune diagonalisation) vs résolution
    spectrale + mapping spectral sur multiset trié + complétude V·V† = I."""
    rng = np.random.default_rng(41)
    lam = np.sort(rng.uniform(0.2, 3.0, size=8))
    Q, _ = np.linalg.qr(rng.normal(size=(8, 8)) + 1j * rng.normal(size=(8, 8)))
    H = Q @ np.diag(lam.astype(complex)) @ Q.conj().T
    t_grid = (0.25, 1.0, 2.0, 4.0)
    worst_direct = 0.0
    worst_map = 0.0
    err_complete = 0.0
    for t in t_grid:
        Z = (1j * H) * (t ** ALPHA)
        # voie directe : série matricielle mpmath (Z^n / Γ(nα+1)) — aucun spectre
        S = ml_matrix(Z)
        U_direct = np.array([[complex(S[i, j]) for j in range(8)]
                             for i in range(8)])
        # voie spectrale : eigh puis calcul fonctionnel sur les valeurs propres
        ev, V = np.linalg.eigh(H)
        U_spec = V @ np.diag([complex(ml_series(mpmc(1j * float(l) * (t ** ALPHA))))
                              for l in ev]) @ V.conj().T
        worst_direct = max(worst_direct, float(np.max(np.abs(U_direct - U_spec))))
        # mapping spectral : spec(voie directe) vs {E_α(iλ_k t^α)} (multiset trié)
        # — leçon V1 : jamais ev[0] vs cible en position fixe
        ev_direct = np.sort_complex(np.linalg.eigvals(U_direct))
        tgt = np.sort_complex(np.array(
            [complex(ml_series(mpmc(1j * float(l) * (t ** ALPHA)))) for l in lam],
            dtype=complex))
        worst_map = max(worst_map, float(np.max(np.abs(ev_direct - tgt))))
        # complétude de la base propre : V·V† = I
        err_complete = max(err_complete, float(np.max(np.abs(V @ V.conj().T
                                                             - np.eye(8)))))
    ok = (worst_direct < 1e-12) and (worst_map < 1e-12) and (err_complete < 1e-12)
    val = 0.0 if ok else max(worst_direct, worst_map, err_complete)
    return val, {"err_serie_directe_vs_spectrale_worst": worst_direct,
                 "err_mapping_spectral_worst": worst_map,
                 "err_completude_VVdagger": err_complete,
                 "t_grid": list(t_grid), "n_modes": 8,
                 "note": "voie directe = série matricielle, aucun produit scalaire"}


def ml_scalar(lam, t):
    """|E_{1/φ}(iλt^{1/φ})| — module du facteur modal (voie mpmath)."""
    return abs(complex(ml_series(mpmc(1j * lam * (t ** ALPHA)))))


def norme_op_l4(U, iters=400):
    """Norme d'opérateur ℓ⁴→ℓ⁴ par puissance itérée sur (U†U)² — route
    indépendante de la SVD (p = 2) et des sommes (p = 1, ∞).
    Leçon run 2 : v†(U†U)²v converge vers σ_max⁴ — il faut DEUX racines
    (une seule donnait σ², écart 2e-01)."""
    A = U.conj().T @ U
    M = A @ A
    v = np.ones(U.shape[0], dtype=complex) / math.sqrt(U.shape[0])
    for _ in range(iters):
        w = M @ v
        nw = np.linalg.norm(w)
        if nw == 0:
            return 0.0
        v = w / nw
    return float(np.sqrt(np.sqrt(np.real(np.vdot(v, M @ v)))))


def c2_rayon_spectral_arene():
    """T2 : ‖U‖_{ℓ^p→ℓ^p} = max_k |E_{1/φ}(iλ_k t^{1/φ})| pour p = 1, 2, 4, ∞
    (opérateur diagonal : la norme d'arène est le max des modules — quatre
    routes numériques indépendantes doivent le confirmer)."""
    rng = np.random.default_rng(42)
    lam = np.sort(rng.uniform(0.2, 3.0, size=6))
    t_grid = (0.25, 1.0, 2.0, 4.0)
    worst = 0.0
    detail = {}
    for t in t_grid:
        diag_u = np.array([complex(ml_series(mpmc(1j * float(l) * (t ** ALPHA))))
                           for l in lam])
        U = np.diag(diag_u)
        rho_modal = float(np.max(np.abs(diag_u)))
        routes = {
            "p1": float(np.max(np.sum(np.abs(U), axis=0))),
            "p2_svd": float(np.linalg.svd(U, compute_uv=False)[0]),
            "p4_puissance": norme_op_l4(U),
            "pinf": float(np.max(np.abs(U))),
        }
        detail[f"t={t}"] = {"rho_modal": rho_modal,
                            **{k: v for k, v in routes.items()}}
        for v in routes.values():
            worst = max(worst, abs(v - rho_modal))
    ok = worst < 1e-12
    val = 0.0 if ok else worst
    return val, {"ecart_routes_vs_modal_worst": worst, "detail": detail,
                 "note": "critère spectral d'isométrie : rayon = max|E(iλt^α)|"}


def c3_memoire_nue_et_falsificateur_alpha1():
    """T2a : α = 1/φ — AUCUNE arène ℓ^p n'est conservée (vecteurs de base
    inclus : dev = max_k ||E_k| − 1| exactement). T2b — α = 1 : TOUTES les
    arènes survivent (falsificateur du cahier des charges §4, réalisé)."""
    rng = np.random.default_rng(43)
    lam = np.sort(rng.uniform(0.2, 3.0, size=6))
    t = 1.0
    xs = [rng.normal(size=6) + 1j * rng.normal(size=6) for _ in range(20)]
    xs += [np.eye(6, dtype=complex)[k] for k in range(6)]     # vecteurs de base
    dev_a, dev_b = {}, {}
    for p, key in ((1, "p1"), (2, "p2"), (4, "p4"), (np.inf, "pinf")):
        U_a = np.diag([complex(ml_series(mpmc(1j * float(l) * (t ** ALPHA))))
                       for l in lam])
        U_b = np.diag([cmath.exp(1j * float(l) * t) for l in lam])
        wa = max(abs(np.linalg.norm(U_a @ x, ord=p) / np.linalg.norm(x, ord=p)
                     - 1.0) for x in xs)
        wb = max(abs(np.linalg.norm(U_b @ x, ord=p) / np.linalg.norm(x, ord=p)
                     - 1.0) for x in xs)
        dev_a[key] = float(wa)
        dev_b[key] = float(wb)
    contraction_stricte = all(v > 1e-4 for v in dev_a.values())
    alpha1_unitaire = all(v < 1e-12 for v in dev_b.values())
    ok = contraction_stricte and alpha1_unitaire
    val = 0.0 if ok else 1.0
    return val, {"dev_arene_alpha_1surphi": dev_a,
                 "dev_arene_alpha_1": dev_b,
                 "contraction_stricte_alpha_1surphi": contraction_stricte,
                 "falsificateur_alpha_1_toutes_les_arenes": alpha1_unitaire,
                 "note": "la sélection n'existe QUE parce que α = 1/φ < 1 "
                         "(système ouvert, HAMILTONIEN ABC C1)"}


def c4_commutant_couple():
    """T3 : commutant du flot fréquentiel seul = dim N (circulants) ;
    commutant du COUPLE {e^{iωt}, modulation e^{ia·kx}} = TRIVIAL (dim 1,
    S = cI). Défaut [K̂, modulation] ≠ 0 mesuré (χ, machine)."""
    t0 = 0.7
    U_w = np.diag(np.exp(1j * OMEGAS * t0))              # flot fréquentiel
    # commutant de U_w : S circulants ⟺ S = F†·diag(c)·F — contrainte
    # supplémentaire [S, MODU] = 0 paramétrée sur c (leçon V1 : exclure
    # explicitement ce qui n'est pas une rivale ; ici le paramétrage est exact)
    M = np.zeros((N * N, N), dtype=complex)
    for k in range(N):
        E = np.zeros((N, N), dtype=complex)
        E[k, k] = 1.0
        Sk = F_UNIT.conj().T @ E @ F_UNIT
        M[:, k] = (Sk @ MODU - MODU @ Sk).reshape(-1)
    sv = np.linalg.svd(M, compute_uv=False)
    rang = int(np.sum(sv > 1e-10))
    dim_couple = N - rang
    dim_flot_seul = N          # tous les circulants (phases de U_w distinctes)
    # générateur du commutant du couple → doit être c·I (trivialité)
    _, _, Vt = np.linalg.svd(M)
    c = Vt[-1].conj()
    S = F_UNIT.conj().T @ np.diag(c) @ F_UNIT
    S = S * (N / np.trace(S))
    ecart_identite = float(np.linalg.norm(S - np.eye(N), ord="fro"))
    # écarts de phases (pas de dégénérescence accidentelle)
    arg_w = np.sort((OMEGAS * t0) % (2 * math.pi))
    gap_w = float(np.min(np.diff(arg_w)))
    arg_m = np.sort((2 * math.pi * PHI * np.arange(N)) % (2 * math.pi))
    gap_m = float(np.min(np.diff(arg_m)))
    # défaut du couple déposé : [K̂, modulation] ≠ 0 (FORCE : c'est χ) et
    # [K̂, flot fréquentiel] = 0 exactement (la mémoire choisit la fréquence)
    defect_couple = float(np.linalg.norm(KF_POS @ MODU - MODU @ KF_POS, ord="fro")
                          / np.linalg.norm(KF_POS, ord="fro"))
    defect_flot = float(np.linalg.norm(np.diag(KHAT_W) @ U_w - U_w @ np.diag(KHAT_W),
                                       ord="fro"))
    ok = (dim_couple == 1) and (ecart_identite < 1e-8) and (gap_w > 1e-3) \
        and (gap_m > 1e-3) and (defect_couple > 0.05) and (defect_flot < 1e-12)
    val = 0.0 if ok else 1.0
    return val, {"dim_commutant_flot_frequence": dim_flot_seul,
                 "dim_commutant_couple": dim_couple,
                 "ecart_generateur_vs_identite": ecart_identite,
                 "min_ecart_phase_flot": gap_w, "min_ecart_phase_modulation": gap_m,
                 "defaut_Khat_modulation": defect_couple,
                 "defaut_Khat_flot": defect_flot,
                 "note": "le flot seul laisse dim N ; le couple laisse dim 1 (cI) — "
                         "et le défaut de K̂ sous modulation est la diffusion χ "
                         "(FORCE), ici mesurée sur la modulation pure"}


def c5_matrice_falsifiabilite():
    """4 normes × 4 colonnes : flot fréquentiel, modulation, COUPLE, K̂ seul.
    Motif attendu (exact) :
      L2           : flot ✔ modulation ✔ couple ✔  | K̂ ✘ (contraction stricte)
      wL2_omega    : flot ✔ modulation ✘ couple ✘  | K̂ ✘
      wL2_position : flot ✘ modulation ✔ couple ✘  | K̂ ✘
      generique    : tout ✘                        | K̂ ✘
    Le couple ne laisse que L² ; K̂ seul ne laisse RIEN (T2a métrique).
    Leçon run 2 (témoins dégénérés corrigés) : (i) ‖F†x‖ ≡ ‖x‖ — une norme
    « dans une autre base unitaire » sans poids est IDENTIQUEMENT L² ;
    (ii) une norme pondérée DIAGONALE dans la base propre d'un unitaire
    diagonal est automatiquement conservée par lui — le témoin « générique »
    canonique passait la modulation gratuitement. Les témoins remplacés :
    poids non uniformes en base canonique (position), et poids dans une
    TROISIÈME base unitaire aléatoire (invariante sous aucun des deux)."""
    rng = np.random.default_rng(45)
    t0 = 0.7
    U_w = F_UNIT.conj().T @ np.diag(np.exp(1j * OMEGAS * t0)) @ F_UNIT
    w_omega = np.abs(KHAT_W) ** 2                    # poids en base fréquence
    w_pos = 1.0 + 0.5 * rng.random(N)                # poids canonique (position)
    Qg, _ = np.linalg.qr(rng.normal(size=(N, N)) + 1j * rng.normal(size=(N, N)))
    w_g3 = 1.0 + 0.5 * rng.random(N)                 # poids 3e base unitaire

    def nL2(x):
        return float(np.linalg.norm(x))

    def nWomega(x):
        xf = np.fft.fft(x) / math.sqrt(N)
        return float(np.sqrt(np.sum(w_omega * np.abs(xf) ** 2)))

    def nWposition(x):
        # poids non uniformes en base canonique : conservée par la modulation
        # (diagonale unitaire dans SA propre base) mais pas par le flot
        # (circulant) — contrairement au ‖ifft(x)·√N‖ du run 2, qui était
        # identiquement L² (F unitaire) et donc un témoin dégénéré.
        return float(np.sqrt(np.sum(w_pos * np.abs(x) ** 2)))

    def nWgen(x):
        # poids dans une troisième base unitaire aléatoire : conservée par
        # AUCUN des deux (ni le flot fréquentiel, ni la modulation n'y sont
        # diagonaux) — le run 2 la plaçait dans la base canonique, où la
        # modulation diagonale la conservait gratuitement.
        xg = Qg.conj().T @ x
        return float(np.sqrt(np.sum(w_g3 * np.abs(xg) ** 2)))

    norms = {"L2": nL2, "wL2_omega": nWomega, "wL2_position": nWposition,
             "generique": nWgen}

    def dev(nf, G, xs):
        w = 0.0
        for x in xs:
            n0 = nf(x)
            w = max(w, abs(nf(G @ x) / n0 - 1.0))
        return float(w)

    xs = [rng.normal(size=N) + 1j * rng.normal(size=N) for _ in range(8)]
    tab = {}
    for name, nf in norms.items():
        d_flot = dev(nf, U_w, xs)
        d_modu = dev(nf, MODU, xs)
        d_couple = max(d_flot, d_modu)
        d_khat = dev(nf, KF_POS, xs)
        tab[name] = {"flot_frequence": d_flot, "modulation": d_modu,
                     "couple": d_couple, "Khat_seul": d_khat}
    motif = {
        "L2":           (True,  True,  True,  False),
        "wL2_omega":    (True,  False, False, False),
        "wL2_position": (False, True,  False, False),
        "generique":    (False, False, False, False),
    }
    conforme = True
    for name, ex in motif.items():
        passe = tuple(tab[name][c] < 1e-12 for c in
                      ("flot_frequence", "modulation", "couple", "Khat_seul"))
        conforme &= (passe == ex)
    # contrastes : les poids ne sont PAS uniformes (sinon wℓ² ≡ L² — leçon
    # run 2 : un témoin dégénéré valide son propre contrôle à vide)
    contraste_w = float(np.max(w_omega) / np.min(w_omega))
    contraste_wpos = float(np.max(w_pos) / np.min(w_pos))
    conforme &= contraste_w > 1.05
    conforme &= contraste_wpos > 1.05
    ok = bool(conforme)
    val = 0.0 if ok else 1.0
    return val, {"tableau": tab,
                 "motif_attendu": {k: list(v) for k, v in motif.items()},
                 "contraste_poids_K": contraste_w,
                 "contraste_poids_position": contraste_wpos,
                 "note": "le couple {flot fréquentiel, modulation} ne laisse que "
                         "L² ; K̂ seul (contraction) ne laisse rien"}


def c6_zeno_coefficient():
    """C6 — 1 − P(t) = c₂·t^{2/φ}·(1 + O(t^{2/φ})), c₂ = 2/Γ(2/φ+1) −
    1/Γ(1/φ+1)² (mpmath, sans cancellation). CORRECTION DE THÉORIE (run 2) :
    |E(iξ)|² est paire en ξ (termes impairs de E entrés au carré dans |E|²)
    ⟹ pas de terme ξ³, la correction relative est O(ξ²) = O(t^{2/φ}) —
    l'annonce initiale O(t^{1/φ}) était FAUSSE ; le rapport d'erreurs
    successifs tend vers 2^{−2/φ} = 2^{−2α} = 0.4247 (mesuré 0.4249)."""
    c2 = 2 / mgamma(2 * ALPHA_M + 1) - 1 / mgamma(ALPHA_M + 1) ** 2
    ts = (1e-2, 2e-2, 4e-2)
    y = []
    for t in ts:
        P = abs(ml_series(mpmc(1j * mpf(t) ** ALPHA_M))) ** 2   # mpmath, exact
        y.append(1.0 - float(P))                                # zéro de cancellation 1e-3 : sain
    c2_num = [yy / (float(t) ** (2 * float(ALPHA_M))) for t, yy in zip(ts, y)]
    errs = [c / float(c2) - 1.0 for c in c2_num]
    ratios = (errs[0] / errs[1], errs[1] / errs[2]) if all(e != 0 for e in errs) \
        else (float("nan"), float("nan"))
    ratio_theo = 2.0 ** (-2 * float(ALPHA_M))
    ok = (abs(errs[0]) < 0.05) and all(abs(r - ratio_theo) < 0.1 for r in ratios)
    val = 0.0 if ok else max(abs(errs[0]), 1.0)
    return val, {"c2_machine": float(c2),
                 "c2_extraits": c2_num, "errs_relatifs": errs,
                 "ratios_err": ratios, "ratio_theorie_2_moins_2alpha": ratio_theo,
                 "note": "c₂ > 0 : la mémoire ACCÉLÈRE la décroissance (Zeno "
                         "inhibé) — dépôt E1bis ; parité de |E(iξ)|² ⟹ correction "
                         "O(t^{2/φ}), rapport → 2^{−2α} (leçon : la machine "
                         "corrige la théorie, jamais l'inverse)"}


# ------------------------------------------------------------------- main

def main():
    print("=" * 72)
    print("F11 HILBERT V2 — Voie 3 spectrale (C-H3) : le couple déposé ferme l'arène")
    print("α = 1/φ = %.15f ; θ = πα/2 = %.6f rad ; N = %d" % (ALPHA, THETA, N))
    print("=" * 72)

    w1, d1 = c1_calcul_fonctionnel_spectral()
    w2, d2 = c2_rayon_spectral_arene()
    w3, d3 = c3_memoire_nue_et_falsificateur_alpha1()
    w4, d4 = c4_commutant_couple()
    w5, d5 = c5_matrice_falsifiabilite()
    w6, d6 = c6_zeno_coefficient()

    print()
    print("C1 calcul fonctionnel spectral : direct vs spectrale %.1e ; mapping %.1e ;"
          " complétude %.1e" % (d1["err_serie_directe_vs_spectrale_worst"],
                                d1["err_mapping_spectral_worst"],
                                d1["err_completude_VVdagger"]))
    print("C2 rayon spectral d'arène   : écart routes vs modal worst %.1e" % w2)
    print("C3 mémoire nue / α = 1      : contraction stricte %s (dev min %.3f) ;"
          " falsificateur α=1 : %s"
          % (d3["contraction_stricte_alpha_1surphi"],
             min(d3["dev_arene_alpha_1surphi"].values()),
             d3["falsificateur_alpha_1_toutes_les_arenes"]))
    print("C4 commutant                : flot seul dim %d ; COUPLE dim %d ;"
          " générateur vs I : %.1e ; [K̂,modu] %.3f ; [K̂,flot] %.1e"
          % (d4["dim_commutant_flot_frequence"], d4["dim_commutant_couple"],
             d4["ecart_generateur_vs_identite"], d4["defaut_Khat_modulation"],
             d4["defaut_Khat_flot"]))
    print("C5 matrice falsifiabilité   : motif %s (contraste w_ω = %.2f)"
          % ("CONFORME" if w5 == 0.0 else "REFUTE", d5["contraste_poids_K"]))
    print("C6 Zeno 2/φ                 : c₂ = %.12f ; err rel %.2e ;"
          " ratio err %.4f (théo 2^{−2α} = %.4f)"
          % (d6["c2_machine"], abs(d6["errs_relatifs"][0]), d6["ratios_err"][0],
             d6["ratio_theorie_2_moins_2alpha"]))

    ok = (w1 == 0.0) and (w2 == 0.0) and (w3 == 0.0) and (w4 == 0.0) \
        and (w5 == 0.0) and (w6 == 0.0)

    print()
    print("-" * 72)
    if ok:
        print("VERDICT : F11_HILBERT_V2_VOIE3_SPECTRALE_COUPLE_COMMUTANT_TRIVIAL — exit 0")
        print("  T1 : le calcul fonctionnel de la mémoire d'or est spectral")
        print("       (série directe = résolution spectrale, sans arène postulée).")
        print("  T2 : isométrie ⟺ |λ| = 1 — la mémoire nue ne conserve AUCUNE arène ;")
        print("       à α = 1 toutes les ℓ^p survivent (falsificateur consigné).")
        print("  T3 : le couple déposé {flot fréquentiel, modulation} a un commutant")
        print("       TRIVIAL ⟹ L² seule forme quadratique invariante — sans")
        print("       postuler Hilbert.")
        print("  Reste ouvert (consigné) : T3 en dimension infinie, Jordan")
        print("       (non-normaux), complétude totale.")
    else:
        print("VERDICT : REFUTE — exit 1")
    print("-" * 72)

    with open("resultat_f11_hilbert_v2.json", "w", encoding="utf-8") as f:
        json.dump({"verdict": "F11_HILBERT_V2_VOIE3_SPECTRALE_COUPLE_COMMUTANT_TRIVIAL"
                   if ok else "REFUTE",
                   "alpha": ALPHA, "theta": THETA, "N": N,
                   "controles": {"C1": d1, "C2": d2, "C3": d3, "C4": d4,
                                 "C5": d5, "C6": d6},
                   "ok": ok},
                  f, indent=2, ensure_ascii=False, default=float)

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
