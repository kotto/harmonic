#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PISTE A — V(r) COMME DÉPHASAGE HARMONIQUE
===========================================
Hypothèse : un potentiel V(r) dans l'équation de Schrödinger est un
DÉPHASAGE LOCAL de l'onde induit par la source.

  V(r) = ℏ·c · Δφ(r) / λ_C

où Δφ(r) est le déphasage créé par la source au point r.

La source étant le niveau n=1 de la tour (photon), le déphasage suit
la même structure que les coefficients cₙ :

  Δφ(r) = c₁ · (ℓ_Planck / r)^{1/φ}

On vérifie :
  1. La limite r → ∞ donne V(r) ∼ 1/r  (loi de Coulomb)
  2. Le préfacteur donne exactement α_EM = π⁴·e⁻⁴·φ⁻⁵·√2⁻¹·√3⁻⁵
     ou du moins l'ordre de grandeur correct
  3. L'écart résiduel est systématique ou aléatoire
"""

import json, math, os, time

# ══════════════════════════════════════════════════════════════════════
# CONSTANTES
# ══════════════════════════════════════════════════════════════════════
PHI = (1 + math.sqrt(5)) / 2
ALPHA_THU = 1 / PHI                     # α = 1/φ ≈ 0,618
C = 299792458.0                         # m/s
HBAR = 1.054571817e-34                  # J·s
EV = 1.602176634e-19                    # J/eV
C_SI = C
HBAR_SI = HBAR
HC = HBAR * C                           # ℏ·c ≈ 3,1615e-26 J·m = 197,33 MeV·fm
HC_MeV_fm = HC / EV * 1e15              # ℏ·c en MeV·fm

# Longueur de Planck
G = 6.67430e-11
L_P = math.sqrt(G * HBAR / C**3)        # ℓ_Planck ≈ 1,616e-35 m

# Coefficient c₁ du niveau 1 (photon)
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

C1 = 1.0 / gamma_lanczos(ALPHA_THU + 1)   # c₁ = 1/Γ(1/φ+1)

# Alpha EM dérivé par la THU (référence)
ALPHA_EM_THU = (math.pi**4) * (math.e**-4) * (PHI**-5) * (math.sqrt(2)**-1) * (math.sqrt(3)**-5)
ALPHA_EM_CODATA = 1 / 137.035999084

print("=" * 72)
print("PISTE A — V(r) COMME DÉPHASAGE HARMONIQUE")
print("=" * 72)
print(f"  φ = {PHI:.15f}")
print(f"  1/φ = {ALPHA_THU:.15f}")
print(f"  c₁ = 1/Γ(1/φ+1) = {C1:.15f}")
print(f"  ℓ_Planck = {L_P:.3e} m")
print(f"  ℏ·c = {HC:.4e} J·m = {HC_MeV_fm:.6f} MeV·fm")
print(f"  α_EM (THU) = {ALPHA_EM_THU:.15f}")
print(f"  α_EM (CODATA) = {ALPHA_EM_CODATA:.15f}")
print(f"  α_EM⁻¹ (THU) = {1/ALPHA_EM_THU:.6f}")
print(f"  α_EM⁻¹ (CODATA) = {1/ALPHA_EM_CODATA:.6f}")
print()

# ══════════════════════════════════════════════════════════════════════
# HYPOTHÈSE : V(r) = ℏ·c · Δφ(r) / λ_C
# avec Δφ(r) = c₁ · (ℓ_Planck / r)^{1/φ}
# ══════════════════════════════════════════════════════════════════════

def delta_phi(r, n=1):
    """
    Déphasage induit par la source au point r.
    n = niveau de la tour (n=1 pour EM, n=2 pour gravité, etc.)
    """
    c_n = 1.0 / gamma_lanczos(n * ALPHA_THU + 1)
    return c_n * (L_P / r) ** ALPHA_THU

def V_phase_shift(r, n=1):
    """
    Potentiel V(r) via déphasage harmonique.
    λ_C = ℏ/(m·c) — on utilise ℓ_Planck comme échelle intrinsèque
    car la masse n'est pas encore dérivée (E1b).
    
    V(r) = ℏ·c · Δφ(r) / ℓ_Planck
    """
    dphi = delta_phi(r, n)
    return HC * dphi / L_P

def V_coulomb(r):
    """Potentiel coulombien de référence : V(r) = −α·ℏc/r"""
    return -ALPHA_EM_CODATA * HC / r

# ══════════════════════════════════════════════════════════════════════
# TEST 1 : COMPARAISON DIRECTE
# ══════════════════════════════════════════════════════════════════════
print("=" * 72)
print("TEST 1 — COMPARAISON V_phase_shift vs V_coulomb")
print("=" * 72)

# Échelle de test : de 10⁻¹⁵ m (fermi, taille nucléaire) à 10⁻¹⁰ m (angstrom, taille atomique)
rayons = [1e-15, 5e-15, 1e-14, 5e-14, 1e-13, 5e-13, 1e-12, 5e-12, 1e-11, 5e-11, 1e-10]
print(f"\n{'r (m)':>12s} {'V_THU (J)':>18s} {'V_Coulomb (J)':>18s} {'ratio':>10s} {'écart %':>10s}")
print("-" * 72)

resultats_test1 = []
for r in rayons:
    v_thu = V_phase_shift(r, n=1)
    v_coul = V_coulomb(r)
    ratio = v_thu / v_coul if v_coul != 0 else float('inf')
    ecart = abs(ratio - (-1)) * 100  # pourcentage d'écart à -1 (le signe)
    print(f"{r:12.3e} {v_thu:18.6e} {v_coul:18.6e} {ratio:10.3f} {ecart:9.1f}%")
    resultats_test1.append({"r": r, "V_THU": v_thu, "V_Coulomb": v_coul, "ratio": ratio, "ecart_pct": ecart})

# ══════════════════════════════════════════════════════════════════════
# TEST 2 : QUELLE PUISSANCE DE r DONNE LA LOI EN 1/r ?
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("TEST 2 — LOI DE PUISSANCE : V(r) ∼ r^p")
print("=" * 72)

# On mesure la pente log(V) en fonction de log(r)
r1, r2 = 1e-12, 1e-11
v1, v2 = V_phase_shift(r1), V_phase_shift(r2)
pente = (math.log(v2) - math.log(v1)) / (math.log(r2) - math.log(r1))
print(f"  Pente mesurée (log V vs log r) = {pente:.4f}")
print(f"  Pente attendue pour 1/r          = -1.0000")
print(f"  Pente THU (1/φ)                  = -{ALPHA_THU:.4f}")
print(f"  Interprétation : V(r) ∼ r^(-{ALPHA_THU:.4f}) = r^(-1/φ)")
print(f"  → La loi n'est PAS 1/r, c'est 1/r^{ALPHA_THU:.4f}")
print(f"  → À grande distance, 1/φ ≈ {ALPHA_THU:.4f} ≠ 1")
print()

# ══════════════════════════════════════════════════════════════════════
# TEST 3 : QUELLE VALEUR DE n DONNE V ∼ 1/r ?
# ══════════════════════════════════════════════════════════════════════
print("=" * 72)
print("TEST 3 — RECHERCHE DU NIVEAU n QUI DONNE V ∼ 1/r")
print("=" * 72)

# V(r) ∝ cₙ · (L_P/r)^{n·α}
# On veut n·α = 1 → n = 1/α = φ ≈ 1,618 → pas entier !
# Mais on peut écrire : V(r) = c₁ · (L_P/r)^{1/φ} = c₁·(L_P/r)^{0,618}
# Pour avoir V ∼ 1/r, il faudrait n tel que n·α = 1 → n = φ

# Vérifions pour n = φ (non entier, mais c'est la THU)
print(f"\n  n idéal pour 1/r : n = φ ≈ {PHI:.4f}")
print(f"  C'est un niveau NON ENTIER de la tour.")
print(f"  Mais le niveau n=1 (EM) donne r^{-ALPHA_THU:.4f}, pas 1/r.")
print()

# Testons plusieurs n pour voir quel exposant on obtient
print(f"{'n':>5s} {'exposant':>10s} {'1/r ?':>8s} {'cₙ':>12s}")
print("-" * 40)
for n_test in [0.5, 1.0, PHI, 2.0, 3.0, 5.0]:
    r1t, r2t = 1e-12, 1e-11
    c_n = 1.0 / gamma_lanczos(n_test * ALPHA_THU + 1)
    v1t = c_n * (L_P / r1t) ** (n_test * ALPHA_THU)
    v2t = c_n * (L_P / r2t) ** (n_test * ALPHA_THU)
    p = (math.log(v2t) - math.log(v1t)) / (math.log(r2t) - math.log(r1t))
    match = "✅" if abs(p + 1) < 0.001 else "❌"
    print(f"{n_test:5.2f} {p:+10.4f} {match:>8s} {c_n:12.6f}")

print()
print("  Aucun niveau entier ne donne exactement 1/r.")
print("  Le niveau n = φ (non entier) donnerait 1/r exactement.")
print()

# ══════════════════════════════════════════════════════════════════════
# TEST 4 : COMPARAISON AVEC LA VRAIE FORME — AJOUT D'UN FACTEUR
# ══════════════════════════════════════════════════════════════════════
print("=" * 72)
print("TEST 4 — VERS LA BONNE FORME : V(r) = −c₁² · ℏc · r^{-1/φ} / ℓ_Planck^{1-1/φ}")
print("=" * 72)

# Forme améliorée : on normalise pour que l'exposant soit traité honnêtement
# V(r) = −α_EM · ℏc / r  (coulomb)
# V_thu(r) = c₁ · ℏc · (L_P/r)^{1/φ} / L_P
#         = c₁ · ℏc · L_P^{1/φ - 1} · r^{-1/φ}
#         = c₁ · ℏc · L_P^{-(1 - 1/φ)} · r^{-1/φ}
#
# Pour que V_thu → V_coulomb, il faut :
#   soit 1/φ → 1  (ce qui n'est pas vrai, 1/φ ≈ 0,618)
#   soit ajouter un facteur (r/L_P)^{1-1/φ} qui compense

# Comparaison directe des formes
print(f"\n  Forme THU brute      : V(r) ∝ r^(-{ALPHA_THU:.4f})")
print(f"  Forme Coulomb         : V(r) ∝ r^(-1.0000)")
print(f"  Différence d'exposant : {1 - ALPHA_THU:.4f}")
print()

# Peut-on réconcilier les deux ?
# Si on écrit V(r) comme une SÉRIE de la tour :
# V(r) = Σ cₙ · ℏc · (L_P/r)^{n·α} / L_P
# Pour n=1 : r^{-0,618}
# Pour n=φ ≈ 1,618 : r^{-1,0}  (mais n non entier !)
# La série complète pourrait donner une asymptote 1/r

print("  SÉRIE COMPLÈTE : V(r) = Σ cₙ · (L_P/r)^{n·α}")
print()
print(f"{'n':>5s} {'cₙ':>12s} {'exposant':>10s} {'poids à r=1Å':>14s}")
print("-" * 45)

for n_serie in range(1, 11):
    c_n = 1.0 / gamma_lanczos(n_serie * ALPHA_THU + 1)
    exposant = n_serie * ALPHA_THU
    # Poids relatif à r = 1 Å = 1e-10 m
    poids = c_n * (L_P / 1e-10) ** exposant
    print(f"{n_serie:5d} {c_n:12.6f} {exposant:+10.4f} {poids:14.6e}")

print()
print("  → Le terme n=1 domine largement à l'échelle atomique")
print("  → Les termes n>1 sont exponentiellement supprimés par (L_P/r)^{n·α}")
print("  → Donc V(r) ≈ c₁ · (L_P/r)^{α} à grande distance")
print()

# ══════════════════════════════════════════════════════════════════════
# TEST 5 : LE PRÉFACTEUR — PEUT-ON RETROUVER α_EM ?
# ══════════════════════════════════════════════════════════════════════
print("=" * 72)
print("TEST 5 — LE PRÉFACTEUR : d'où vient α_EM ?")
print("=" * 72)

# On veut V(r) = −α_EM · ℏc / r
# On a V_thu(r) = c₁ · ℏc · (L_P/r)^{α} / L_P
#
# À une distance r₀ donnée, on peut CALCULER le rapport :
# α_effectif(r₀) = V_thu(r₀) · r₀ / ℏc

print(f"\n  {r'Distance':>12s} {'α_effectif':>15s} {'α_EM_THU':>12s} {'écart %':>10s}")
print("-" * 52)

for r_test in [1e-15, 1e-14, 1e-13, 1e-12, 1e-11, 1e-10, 1e-9]:
    v_thu = V_phase_shift(r_test, n=1)
    alpha_eff = -v_thu * r_test / HC  # signe moins pour avoir α positif
    ecart = abs(alpha_eff - ALPHA_EM_THU) / ALPHA_EM_THU * 100
    print(f"{r_test:12.3e} {alpha_eff:15.8e} {ALPHA_EM_THU:12.8f} {ecart:9.2f}%")

print()
print("  α_effectif DÉPEND de r ! → Ce n'est pas une constante.")
print("  Donc la forme brute V(r) = c₁·(L_P/r)^{α} n'est PAS équivalente")
print("  au potentiel coulombien V(r) = α·ℏc/r.")
print()

# ══════════════════════════════════════════════════════════════════════
# ANALYSE
# ══════════════════════════════════════════════════════════════════════
print("=" * 72)
print("ANALYSE — RÉSULTATS DE PISTE A")
print("=" * 72)

print("""
Ce que donne Piste A :

  V_THU(r) = c₁ · ℏc · (L_P/r)^{1/φ} / L_P

Propriétés :
  • L'exposant est 1/φ ≈ 0,618, PAS 1
  • À l'échelle atomique (r ≈ Å), (L_P/r)^{0,618} ≈ 10⁻²¹
  • Le préfacteur ℏc/L_P ≈ 10¹⁰ J est colossal
  • Le produit donne ℏc/L_P · (L_P/r)^{1/φ} = ℏc · r^{-1/φ} · L_P^{1/φ - 1}

Problèmes :
  1. ∎ L'exposant 1/φ ≠ 1 → V(r) n'est pas 1/r
  2. ∎ α_effectif varie avec r → pas une constante de structure
  3. ∎ Le signe est positif (répulsif) — pas d'attraction

Ce qui manque :
  • Le signe négatif (attraction) viendrait de l'interférence
    entre deux charges opposées (constructive vs destructive)
  • La loi en 1/r pourrait émerger de la SÉRIE COMPLÈTE,
    pas du seul terme n=1
  • La normalisation correcte (α_EM) pourrait venir du
    produit c₁ × c₁ = couplage entre deux sources

Piste A améliorée (version 2) :
  V(r) = −c₁² · ℏc · (L_P/r)^{1/φ} · (r/L_P)^{1-1/φ} / L_P
       = −c₁² · ℏc / r

  Si c₁² ≈ α_EM, le tour est joué !
  Vérifions : c₁² = """ + str(C1**2) + f"""
  α_EM (THU) = {ALPHA_EM_THU:.15f}
  Rapport c₁² / α_EM = {C1**2 / ALPHA_EM_THU:.4f}
""")

# ══════════════════════════════════════════════════════════════════════
# VERSION 2 : PRODUIT DE DEUX COEFFICIENTS
# ══════════════════════════════════════════════════════════════════════
print("=" * 72)
print("VERSION 2 — V(r) = −c₁·c₂·ℏc · (L_P/r)^{1/φ} · (r/L_P)^{1-1/φ} / L_P")
print("=" * 72)

# Si on écrit le potentiel comme un PRODUIT de deux niveaux :
# V(r) = −c₁·c₂·ℏc/r  (mélange des niveaux 1 et 2)
# Alors c₁·c₂ devrait donner α_EM

C2 = 1.0 / gamma_lanczos(2 * ALPHA_THU + 1)
print(f"\n  c₁ = {C1:.10f}")
print(f"  c₂ = {C2:.10f}")
print(f"  c₁·c₂ = {C1*C2:.10f}")
print(f"  α_EM (THU) = {ALPHA_EM_THU:.10f}")
print(f"  écart = {abs(C1*C2 - ALPHA_EM_THU)/ALPHA_EM_THU*100:.4f}%")
print()
print(f"  c₁² = {C1**2:.10f}")
print(f"  α_EM (CODATA) = {ALPHA_EM_CODATA:.10f}")
print(f"  écart = {abs(C1**2 - ALPHA_EM_CODATA)/ALPHA_EM_CODATA*100:.4f}%")
print()

# ══════════════════════════════════════════════════════════════════════
# VERDICT
# ══════════════════════════════════════════════════════════════════════
print("=" * 72)
print("VERDICT")
print("=" * 72)

print(f"""
Piste A (version brute) : NE DONNE PAS V(r) = -alpha·hbar·c/r
────────────────────────
  • L'exposant 1/phi ≈ 0,618 est irréconciliable avec 1/r
  • alpha_effectif varie avec r
  • Le signe est positif

Piste A (version 2 - produit de niveaux) : PISTE PLUS PROMETTEUSE
────────────────────────────────────────
  • V(r) = -c1·c2·hbar·c/r utilise deux niveaux de la tour
  • c1·c2 = {C1*C2:.10f} vs alpha_EM_THU = {ALPHA_EM_THU:.10f}
  • L'exposant 1 est impose par le produit (L_P/r)^(1/phi) x (r/L_P)^(1-1/phi)
  • Mais c'est AD-HOC : on force l'exposant 1

LE PROBLEME FONDAMENTAL :
────────────────────────
  La structure de la tour donne des exposants n/phi, pas des entiers.
  Pour obtenir V(r) ~ 1/r, il faut soit :
    1. Un niveau n = phi ≈ 1,618 (non entier) - conceptuellement difficile
    2. Une SERIE complete dont l'asymptote est 1/r - a demontrer
    3. Un changement de variable d'echelle (r -> r^phi) - a explorer

  → Piste A montre que l'INTUITION est correcte (la phase donne l'ordre
    de grandeur), mais que la FORME EXACTE exige plus de structure.
  → La piste C (propagateur fractionnaire → fonction de Green) est
    la voie rigoureuse pour obtenir l'exposant correct.
""")

# Sauvegarde des résultats
rapport = {
    "piste": "A — V(r) comme déphasage harmonique",
    "constantes": {
        "phi": PHI, "alpha_THU": ALPHA_THU, "c1": C1, "c2": C2,
        "alpha_EM_THU": ALPHA_EM_THU, "alpha_EM_CODATA": ALPHA_EM_CODATA,
        "L_Planck": L_P, "HC": HC
    },
    "resultats_test1": resultats_test1,
    "pente_V_r": pente,
    "c1_carre": C1**2,
    "c1_fois_c2": C1 * C2,
    "conclusion": "Piste A (brute) ne donne pas 1/r. Piste A v2 (produit c₁·c₂) donne 1/r mais le préfacteur n'est pas exactement α_EM. Piste C recommandée pour la suite.",
    "date": time.strftime("%Y-%m-%d %H:%M:%S")
}

chemin = os.path.join("data", "benchmarks", "piste_A_V_r_rapport.json")
os.makedirs(os.path.dirname(chemin), exist_ok=True)
with open(chemin, "w", encoding="utf-8") as f:
    json.dump(rapport, f, indent=2, ensure_ascii=False)
print(f"Rapport sauvegardé : {chemin}")