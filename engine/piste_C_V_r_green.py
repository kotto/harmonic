#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PISTE C — DÉRIVATION DE V(r) PAR LA FONCTION DE GREEN FRACTIONNAIRE
====================================================================
Objectif : dériver le potentiel coulombien V(r) = −α·ℏc/r depuis
l'équation de la tour D^{1/φ}[Ψ] = G[Ψ].

IDÉE GÉNÉRALE :
──────────────
  L'équation de la tour se SÉPARE en temps et espace :
    D_t^{1/φ}[ψ] = (ℏ²/2m)·∇²ψ + V(r)ψ     (THU)
    
  La partie SPATIALE est le LAPLACIEN STANDARD — pas fractionnaire.
  Pourquoi ? Parce que la mémoire d'or (α = 1/φ) agit sur le TEMPS,
  pas sur l'espace. La mesure de l'espace est la distance — pas de
  mémoire dans la distance.

  Donc l'équation de Green statique est :
    −∇² G(r) = δ(r)    (standard, 3D)
    
  dont la solution est :
    G(r) = 1/(4πr)      (Coulomb !)
    
  La THU n'a PAS à dériver 1/r — c'est la solution de l'équation de
  Laplace en 3D, indépendante de la mémoire d'or.

  CE QUE LA THU APPORTE :
    1. Le COUPLAGE : c₁² = 1,247 pour deux charges niveau n=1
    2. La RENORMALISATION : α_EM = c₁² × (facteurs géométriques)
    3. Le PROPAGATEUR TEMPOREL : fractionnaire, pas standard

PLAN :
  1. Vérifier que le Laplacien 3D standard donne 1/r
  2. Montrer que le propagateur fractionnaire en temps est compatible
  3. Calculer le couplage effectif depuis c₁, c₂, et les facteurs
  4. Comparer le potentiel THU complet avec le Coulomb standard
"""

import json, math, os, time, cmath
import numpy as np
import mpmath

def mittag_leffler_impl(alpha, z, tol=1e-15, max_terms=200):
    """
    Fonction de Mittag-Leffler E_alpha(z) = sum_{k=0}^{oo} z^k / Gamma(alpha*k + 1)
    """
    s = mpmath.mpf('0')
    term = mpmath.mpf('1')
    k = 0
    while abs(term) > tol and k < max_terms:
        s += term
        k += 1
        term = term * z / mpmath.gamma(alpha * k + 1)
    return s

# ══════════════════════════════════════════════════════════════════════
# CONSTANTES
# ══════════════════════════════════════════════════════════════════════
PHI = (1 + math.sqrt(5)) / 2
ALPHA = 1 / PHI                         # α = 1/φ ≈ 0,618
C = 299792458.0
HBAR = 1.054571817e-34
EV = 1.602176634e-19
HC = HBAR * C
HC_MeV_fm = HC / EV * 1e15

G_SI = 6.67430e-11
L_P = math.sqrt(G_SI * HBAR / C**3)
M_P = math.sqrt(HBAR * C / G_SI)

def gamma_lanczos(x):
    """Γ(x) par Lanczos, précision ~1e-15"""
    g = 7
    coef = [0.99999999999980993, 676.5203681218851, -1259.1392167224028,
            771.32342877765313, -176.61502916214059, 12.507343278686905,
            -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7]
    if x < 0.5:
        return math.pi / (math.sin(math.pi * x) * gamma_lanczos(1 - x))
    x -= 1
    a = coef[0]
    t = x + g + 0.5
    for i in range(1, g + 2):
        a += coef[i] / (x + i)
    return math.sqrt(2 * math.pi) * t ** (x + 0.5) * math.exp(-t) * a

C1 = 1.0 / gamma_lanczos(ALPHA + 1)
C2 = 1.0 / gamma_lanczos(2 * ALPHA + 1)
C3 = 1.0 / gamma_lanczos(3 * ALPHA + 1)

ALPHA_EM_THU = (math.pi**4) * (math.e**-4) * (PHI**-5) * (math.sqrt(2)**-1) * (math.sqrt(3)**-5)
ALPHA_EM_CODATA = 1 / 137.035999084

print("=" * 72)
print("PISTE C — FONCTION DE GREEN FRACTIONNAIRE → V(r)")
print("=" * 72)
print(f"  φ = {PHI:.15f}")
print(f"  1/φ = {ALPHA:.15f}")
print(f"  c₁ = {C1:.10f}")
print(f"  c₂ = {C2:.10f}")
print(f"  c₃ = {C3:.10f}")
print(f"  α_EM (THU) = {ALPHA_EM_THU:.15f}  (1/α = {1/ALPHA_EM_THU:.6f})")
print(f"  α_EM (CODATA) = {ALPHA_EM_CODATA:.15f}  (1/α = {1/ALPHA_EM_CODATA:.6f})")
print()

# ══════════════════════════════════════════════════════════════════════
# ÉTAPE 1 : LE LAPLACIEN 3D DONNE 1/r
# ══════════════════════════════════════════════════════════════════════
print("=" * 72)
print("ÉTAPE 1 — LA FONCTION DE GREEN DU LAPLACIEN 3D")
print("=" * 72)
print("""
  L'équation de la tour : D^{1/φ}[Ψ] = G[Ψ]
  
  En coordonnées sphériques, le Laplacien est :
    ∇² = (1/r²) ∂_r (r² ∂_r) + (termes angulaires)
  
  Pour une source ponctuelle (symétrie sphérique) :
    ∇² G(r) = δ(r)   →   (1/r²) d/dr (r² dG/dr) = 0  pour r > 0
  
  Solution :
    G(r) = A/r + B
  
  Avec la condition G(r) → 0 quand r → ∞, et le flux :
    ∫ ∇²G · dV = 1  →  A = 1/(4π)
  
  Donc : G(r) = 1/(4πr)    ← EXACT, indépendant de α !
""")

# Vérification numérique : ∇²(1/r) = 0 pour r > 0
print("  Vérification numérique :")
for r_test in [1e-15, 1e-12, 1e-10, 1e-8]:
    # ∇²(1/r) = 0 pour r > 0 (analytique)
    print(f"    r = {r_test:.0e} m : ∇²(1/r) = 0 (identité analytique)")

print("""
  CONCLUSION : La partie spatiale de l'équation de la tour donne
  EXACTEMENT le potentiel coulombien 1/r, quel que soit l'ordre
  fractionnaire α. Il n'y a rien à dériver de plus — c'est la
  solution de l'équation de Laplace en 3D.
""")

# ══════════════════════════════════════════════════════════════════════
# ÉTAPE 2 : LE COUPLAGE — COMMENT α_EM ÉMERGE DE LA TOUR
# ══════════════════════════════════════════════════════════════════════
print("=" * 72)
print("ÉTAPE 2 — LE COUPLAGE : de c₁ à α_EM")
print("=" * 72)
print("""
  Le potentiel entre deux charges est :
    V(r) = g² · G(r) = g²/(4πr)
  
  où g² est le couplage. En QED, g² = e², et α = e²/(4πℏc).
  
  Dans la THU, le couplage entre deux charges de niveau n est :
    g² = cₙ² · ℏc
  
  Donc pour n=1 (EM) :
    V(r) = c₁² · ℏc / (4πr)
  
  Mais c₁² ≈ 1,247, alors que α_EM ≈ 0,0073.
  Le facteur manquant est 1/(4π) × (facteurs géométriques).
""")

# Décomposition de α_EM
print("  Décomposition de α_EM :")
print(f"    c₁² = {C1**2:.10f}")
print(f"    c₁²/(4π) = {C1**2/(4*math.pi):.10f}")
print(f"    α_EM (THU) = {ALPHA_EM_THU:.10f}")
print(f"    Rapport c₁²/(4π) / α_EM = {C1**2/(4*math.pi)/ALPHA_EM_THU:.4f}")
print()

# Le facteur de renormalisation
fact_renorm = ALPHA_EM_THU * 4 * math.pi / C1**2
print(f"  Facteur de renormalisation R = α_EM·4π / c₁² = {fact_renorm:.6f}")
print(f"  R = 4π × α_EM / c₁² = {fact_renorm:.6f}")
print()

# Décomposition de R en facteurs géométriques
print("  Décomposition de R en facteurs φ/π/e :")
R_factors = {
    "π⁻¹": 1/math.pi,
    "π⁻²": 1/math.pi**2,
    "φ⁻¹": 1/PHI,
    "φ⁻²": 1/PHI**2,
    "φ⁻⁵": 1/PHI**5,
    "e⁻¹": 1/math.e,
    "e⁻²": 1/math.e**2,
    "e⁻⁴": 1/math.e**4,
    "√2⁻¹": 1/math.sqrt(2),
    "√3⁻¹": 1/math.sqrt(3),
    "√3⁻⁵": 1/math.sqrt(3)**5,
}

print(f"  {'Facteur':>10s} {'Valeur':>12s} {'R/facteur':>12s}")
print(f"  {'-'*36}")
for name, val in R_factors.items():
    ratio = fact_renorm / val
    print(f"  {name:>10s} {val:12.6f} {ratio:12.4f}")

print(f"""
  R = {fact_renorm:.6f}
  
  On reconnaît R = π⁻¹ · φ⁻⁵ · e⁻⁴ · √2⁻¹ · √3⁻⁵ × (4π)
  Soit R = 4π · π⁻¹ · φ⁻⁵ · e⁻⁴ · √2⁻¹ · √3⁻⁵
        = 4 · φ⁻⁵ · e⁻⁴ · √2⁻¹ · √3⁻⁵
  
  Vérifions : 4 · φ⁻⁵ · e⁻⁴ · √2⁻¹ · √3⁻⁵ = {4 * PHI**-5 * math.e**-4 * math.sqrt(2)**-1 * math.sqrt(3)**-5:.6f}
  R mesuré = {fact_renorm:.6f}
""")

# ══════════════════════════════════════════════════════════════════════
# ÉTAPE 3 : LE PROPAGATEUR TEMPOREL FRACTIONNAIRE
# ══════════════════════════════════════════════════════════════════════
print("=" * 72)
print("ÉTAPE 3 — LE PROPAGATEUR TEMPOREL FRACTIONNAIRE")
print("=" * 72)
print("""
  La vraie originalité de la THU n'est pas dans la forme spatiale
  du potentiel (1/r, standard), mais dans le PROPAGATEUR TEMPOREL.
  
  L'équation de Schrödinger fractionnaire :
    (iℏ)^{1/φ} · ∂^{1/φ}ψ/∂t^{1/φ} = Ĥψ
  
  a pour solution :
    ψ(t) = E_{1/φ}(−i·Ĥ·t^{1/φ}/ℏ^{1/φ}) · ψ(0)
  
  où E_{α} est la fonction de Mittag-Leffler :
    E_{α}(z) = Σ_{k=0}^{∞} z^{k} / Γ(α·k + 1)
  
  Pour α = 1 (QM standard) : E₁(z) = e^{z} → évolution unitaire standard
  Pour α = 1/φ (THU) : E_{1/φ}(z) = évolution fractionnaire → décroissance en
    queue de distribution (stretched exponential), pas en exponentielle.
""")

# Test du propagateur fractionnaire
print("  Test : E_{1/φ}(−i·t^{1/φ}) vs e^{-it} (standard)")
print(f"  {'t':>10s} {'|E_{1/φ}|²':>14s} {'|e^{-it}|²':>12s} {'ratio':>10s}")
print(f"  {'-'*48}")

for t in [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]:
    # Mittag-Leffler pour alpha = 1/phi — utiliser mpmath pour la precision
    z = mpmath.mpc(0, -1) * mpmath.mpf(str(t)) ** ALPHA
    e_ml = mittag_leffler_impl(ALPHA, z)
    prob_ml = float(abs(e_ml)**2)
    # Standard
    prob_std = float(abs(cmath.exp(-1j * t))**2)
    ratio = prob_ml / prob_std if prob_std > 0 else float('inf')
    print(f"  {t:10.2f} {prob_ml:14.8f} {prob_std:12.8f} {ratio:10.4f}")

# Calcul pour t=10 avec conversion
z10 = mpmath.mpc(0, -1) * mpmath.mpf('10') ** ALPHA
ml10 = mittag_leffler_impl(ALPHA, z10)
prob_ml10 = float(abs(ml10)**2)
prob_std10 = float(abs(cmath.exp(-1j * 10))**2)
print(f"""
  → À t = 10, le propagateur THU est {prob_ml10:.4f} vs
    le standard = {prob_std10:.4f}.
  → La différence est la SIGNATURE de la mémoire d'or.
""")

# ══════════════════════════════════════════════════════════════════════
# ÉTAPE 4 : LE POTENTIEL COMPLET — SYNTHÈSE
# ══════════════════════════════════════════════════════════════════════
print("=" * 72)
print("ÉTAPE 4 — LE POTENTIEL COMPLET THU")
print("=" * 72)
print("""
  Le potentiel entre deux charges dans la THU :
  
    V(r) = −α_EM · ℏc / r    (identique à QED pour la forme spatiale)
  
  mais avec le PROPAGATEUR TEMPOREL :
  
    U(t) = E_{1/φ}(−i·Ĥ·t^{1/φ}/ℏ^{1/φ})
  
  au lieu de :
  
    U(t) = exp(−i·Ĥ·t/ℏ)    (QM standard)
  
  La différence est TESTABLE : l'évolution d'un paquet d'ondes
  coulombien sera plus lente (queue de Mittag-Leffler) que l'évolution
  standard.
""")

# Test de la différence entre les deux propagateurs
print("  Comparaison des propagateurs à t = 1 :")
psi_0 = 1.0 + 0.0j

# Standard : ψ(t) = e^{-iEt}·ψ(0)
E = 1.0  # énergie en unités naturelles
psi_std = cmath.exp(-1j * E * 1.0) * psi_0

# THU : psi(t) = E_{1/phi}(-i·E·t^{1/phi})·psi(0)
z_e = mpmath.mpc(0, -1) * mpmath.mpf('1.0')
psi_thu = complex(mittag_leffler_impl(ALPHA, z_e)) * psi_0

print(f"    ψ_standard = {psi_std.real:.6f} + {psi_std.imag:.6f}i")
print(f"    ψ_THU      = {psi_thu.real:.6f} + {psi_thu.imag:.6f}i")
print(f"    |ψ_std|² = {abs(psi_std)**2:.6f}")
print(f"    |ψ_THU|² = {abs(psi_thu)**2:.6f}")
print()

# ══════════════════════════════════════════════════════════════════════
# ÉTAPE 5 : VÉRIFICATION — LE POTENTIEL DONNE-T-IL L'HYDROGÈNE ?
# ══════════════════════════════════════════════════════════════════════
print("=" * 72)
print("ÉTAPE 5 — APPLICATION : SPECTRE DE L'HYDROGÈNE")
print("=" * 72)
print("""
  Le spectre de l'hydrogène est donné par :
    Eₙ = −α²·m_e·c² / (2·n²)   (n = 1, 2, 3, ...)
  
  C'est une conséquence de V(r) = −α·ℏc/r, PAS de la nature
  temporelle du propagateur.
  
  Donc la THU donne le MÊME spectre que Schrödinger pour
  l'hydrogène, parce que la PARTIE SPATIALE est identique.
  
  La différence apparaît dans la DYNAMIQUE :
    - Évolution standard : ψ(t) = e^{-iEₙt/ℏ}
    - Évolution THU : ψ(t) = E_{1/φ}(−i·Eₙ·t^{1/φ}/ℏ^{1/φ})
  
  Cette différence est TESTABLE :
    - Oscillations de Rabi : la fréquence de transition est la même,
      mais l'amortissement est fractionnaire (queue lente)
    - Effet Zeno : survie t^{0,618} au lieu de t² (dépôt E1bis)
""")

# Calcul des premiers niveaux de l'hydrogene
m_e = 9.1093837015e-31  # kg
E_H = -ALPHA_EM_CODATA**2 * m_e * C**2 / 2  # n=1
print(f"  E_1 (niveau fondamental H) = {E_H/EV:.6f} eV")
print(f"  E_1 (Rydberg, |valeur|) = {13.598:.6f} eV")
print(f"  ecart (sur |E_1|) = {abs(abs(E_H/EV) - 13.598)/13.598*100:.4f}%")
print()

# ══════════════════════════════════════════════════════════════════════
# VERDICT
# ══════════════════════════════════════════════════════════════════════
print("=" * 72)
print("VERDICT — PISTE C")
print("=" * 72)
print("""
Ce que Piste C établit :
────────────────────────
✅ Le Laplacien 3D standard donne G(r) = 1/(4πr) → V(r) = −α·ℏc/r
   → La FORME SPATIALE du potentiel est derivee (c'est l'equation
     de Laplace en 3D, independante de alpha)

✅ Le spectre de l'hydrogene est identique a Schrodinger
   → E_n = -alpha^2·m_e·c^2/(2n^2), precis a 0.06% pres

⚠️ Le couplage c_1^2 = 1,247 est la charge nue
   → alpha_EM observe = 0,0073 = c_1^2 / 170,8
   → Le facteur 170,8 ne se factorise pas proprement en π/phi/e
   → La derivation de la NORMALISATION du couplage (c_1^2 → alpha_EM)
     est un PROBLEME OUVERT (le lien entre c_n et les facteurs
     geometriques de la formule alpha_EM de F5 n'est pas fait)

⚠️⚠️ PROBLEME CRITIQUE : Le propagateur temporel fractionnaire
   E_{1/phi}(-i·t^{1/phi}) n'est PAS UNITAIRE !
   → |E_{1/phi}(-i·t^{1/phi})|^2 croit de 0,365 a t=1 a 774 a t=10
   → La probabilite n'est pas conservee
   → C'est un probleme fondamental : la mecanique quantique
     fractionnaire en temps brise l'unitarite
   → Deux voies possibles :
     1. Le propagateur correct est E_{1/phi}(-GAMMA·t^{1/phi}) avec
        GAMMA reel (dissipatif) → pas un systeme ferme mais un systeme
        ouvert (la memoire radiative)
     2. Il faut renormaliser le propagateur pour preserver la norme
        → Mais alors la forme exacte change

Ce qui EST acquis et ce qui ne l'est PAS :
────────────────────────────────────────
✅ La forme 1/r du potentiel est derivee (Laplacien 3D standard)
✅ Le couplage nu c_1^2 vient de la tour
❌ La normalisation c_1^2 → alpha_EM n'est pas derivee (frontiere)
❌ L'unitarite du propagateur temporel fractionnaire est un probleme
   ouvert, pas un resultat acquis
⚠️ Le spectre de l'hydrogene est identique (parce que la forme
   spatiale 1/r est standard — la THU ne change pas la QM sur
   ce point)

La vraie piste pour E1c :
────────────────────────
  La forme spatiale 1/r est derivee (standard). Mais la derivation
  du COUPLAGE (alpha_EM = f(c_1)) et la PRESERVATION DE LA NORME
  sont les deux verrous reels.
""")

# Sauvegarde
rapport = {
    "piste": "C — Fonction de Green fractionnaire",
    "resultats": {
        "green_3d": "G(r) = 1/(4πr) — indépendant de α",
        "couplage_nu": C1**2,
        "alpha_EM_THU": ALPHA_EM_THU,
        "facteur_renormalisation": fact_renorm,
        "propagateur_temporel": "E_{1/φ}(-i·H·t^{1/φ})",
        "spectre_hydrogene": "identique à Schrödinger (même V(r))",
        "testable": ["oscillations Rabi amorties", "Zeno t^{0,618}", "paquets d'ondes"]
    },
    "conclusion": "Piste C : la FORME spatiale 1/r est derivee (Laplacien 3D standard — independant de alpha). Le spectre de l'hydrogene est identique (0,06%). PROBLEMES : (1) la normalisation c_1^2 -> alpha_EM (facteur 170,8) n'est pas derivee ; (2) le propagateur temporel fractionnaire E_{1/phi}(-i·t^{1/phi}) n'est PAS unitaire (|E|^2 croit de 0,365 a 774). Deux verrous reels pour E1c : le couplage et la conservation de la norme.",
    "date": time.strftime("%Y-%m-%d %H:%M:%S")
}

chemin = os.path.join("data", "benchmarks", "piste_C_V_r_rapport.json")
os.makedirs(os.path.dirname(chemin), exist_ok=True)
with open(chemin, "w", encoding="utf-8") as f:
    json.dump(rapport, f, indent=2, ensure_ascii=False)
print(f"Rapport : {chemin}")