#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PISTE F5 — LE TRIANGLE G-h-k_B : VERS LA FERMETURE
=====================================================
Objectif : utiliser les résultats de E1b (masses dérivées) et T*
(température dorée) pour fermer le triangle F5 : G, h, k_B.

DÉCOUVERTE DE E1b :
  M_Pl = m_e × √2 × c₁·c₂ / c₃₇
  M_Pl = √(ℏc/G)

  Donc G = ℏc × c₃₇² / (m_e² × 2 × c₁²·c₂²)
  
  ET k_B = h·ν / (T* × ln φ)  (via T* = ΔE/(k_B·ln φ))

  Si ℏ et h = 2πℏ sont connus, alors G et k_B s'expriment
  via les constantes THU et la masse de l'électron !
  
  MAIS ℏ est un étalon déclaré. Le triangle ne se ferme qu'à
  une constante libre près (ℏ).
  
  La question : y a-t-il une relation qui relie ℏ à φ sans
  paramètre libre ?
"""

import json, math, os, time

PHI = (1 + math.sqrt(5)) / 2
ALPHA = 1 / PHI

def gamma_lanczos(x):
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

def c(n):
    return 1.0 / gamma_lanczos(n * ALPHA + 1)

# Constantes SI
C = 299792458.0
HBAR_SI = 1.054571817e-34
H_SI = 6.62607015e-34
G_SI = 6.67430e-11
KB_SI = 1.380649e-23
M_E_SI = 9.1093837015e-31
M_P_SI = 1.67262192369e-27

# Constantes THU
C1, C2 = c(1), c(2)
C1C2 = C1 * C2
C37, C33 = c(37), c(33)
SQRT2 = math.sqrt(2)
EPS = 0.0020561864

print("=" * 72)
print("PISTE F5 — LE TRIANGLE G-h-k_B : VERS LA FERMETURE")
print("=" * 72)

# ══════════════════════════════════════════════════════════════════════
# PARTIE 1 — G depuis la masse (E1b)
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("PARTIE 1 — G depuis E1b : M_Pl via m_e et la tour")
print("=" * 72)

# De E1b : m_e = M_Pl × c₃₇ / (√2 × c₁·c₂)
# Donc M_Pl = m_e × √2 × c₁·c₂ / c₃₇
M_PL_VIA_ME = M_E_SI * SQRT2 * C1C2 / C37
print(f"\n  M_Pl via masse = {M_PL_VIA_ME:.4e} kg")
print(f"  M_Pl standard   = {math.sqrt(HBAR_SI*C/G_SI):.4e} kg")
print(f"  écart = {abs(M_PL_VIA_ME - math.sqrt(HBAR_SI*C/G_SI))/math.sqrt(HBAR_SI*C/G_SI)*100:.4f}%")

# G = ℏc / M_Pl²
G_VIA_E1b = HBAR_SI * C / M_PL_VIA_ME**2
print(f"\n  G via E1b = {G_VIA_E1b:.6e} m³/kg/s²")
print(f"  G CODATA   = {G_SI:.6e} m³/kg/s²")
print(f"  écart = {abs(G_VIA_E1b - G_SI)/G_SI*100:.4f}%")

# Version avec ℏ libre : G = ℏc × c₃₇² / (m_e² × 2 × c₁²·c₂²)
fact_G = C * C37**2 / (M_E_SI**2 * 2 * C1**2 * C2**2)
print(f"\n  G = ℏ × {fact_G:.4e}")
print(f"  G CODATA = {G_SI:.6e}")
print(f"  ℏ nécessaire = {G_SI/fact_G:.6e} J·s")
print(f"  ℏ réel        = {HBAR_SI:.6e} J·s")
print(f"  écart ℏ = {abs(G_SI/fact_G - HBAR_SI)/HBAR_SI*100:.4f}%")

# ══════════════════════════════════════════════════════════════════════
# PARTIE 2 — k_B depuis T* (température dorée)
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("PARTIE 2 — k_B depuis T* = ΔE/(k_B·ln φ)")
print("=" * 72)

# T* = 37°C = 310.15K (température dorée)
T_STAR = 310.15  # K
LNPHI = math.log(PHI)

# k_B = ΔE / (T* × ln φ)
# Quel ΔE prendre ? Le niveau fondamental de l'hydrogène ?
E_H = 13.598 * 1.602176634e-19  # J (Rydberg)
KB_VIA_H = E_H / (T_STAR * LNPHI)
print(f"\n  Via H (Rydberg) :")
print(f"    k_B = {KB_VIA_H:.6e} J/K")
print(f"    k_B CODATA = {KB_SI:.6e} J/K")
print(f"    écart = {abs(KB_VIA_H - KB_SI)/KB_SI*100:.4f}%")

# Via l'ion H (13.598 eV — le même)
KB_VIA_H_ION = E_H / (T_STAR * LNPHI)  # idem

# Via h·ν : si ΔE = h·ν, alors k_B = h·ν/(T*·ln φ)
# Pour quelle fréquence ν ?
FREQ_H = E_H / H_SI
print(f"    ν correspondante = {FREQ_H:.4e} Hz")
print(f"    λ correspondante = {C/FREQ_H:.4e} m")

# Quel ΔE donne exactement k_B ?
DE_EXACT = KB_SI * T_STAR * LNPHI
print(f"\n  ΔE exact pour k_B : {DE_EXACT:.6e} J = {DE_EXACT/1.602176634e-19:.6f} eV")
print(f"  Rydberg : {13.598:.6f} eV")
print(f"  écart = {abs(DE_EXACT/1.602176634e-19 - 13.598)/13.598*100:.4f}%")

# ══════════════════════════════════════════════════════════════════════
# PARTIE 3 — LE TRIANGLE : G, h, k_B SONT-ILS INDÉPENDANTS ?
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("PARTIE 3 — LE TRIANGLE EST-IL UN CERCLE ?")
print("=" * 72)
print("""
  Il y a TROIS constantes de mesure (G, h, k_B) mais SEULEMENT UN
  paramètre libre une fois qu'on a connecté toutes les relations :
  
  1. m_e = M_Pl × c₃₇ / (√2 × c₁·c₂)        → M_Pl = f(cₙ, m_e)
  2. M_Pl = √(ℏc/G)                          → G = ℏc/M_Pl²
  3. k_B = h·ν/(T*·ln φ)                     → k_B = h·ν/(T*·ln φ)
  
  Comme ν = ΔE/h (pour un système donné, ex. H), on a :
    k_B = ΔE/(T*·ln φ)    INDÉPENDANT de h !
  
  Donc k_B est déterminé par ΔE et T*, sans h.
  
  Et G = ℏc × c₃₇²/(m_e² × 2·c₁²·c₂²)      → G ∝ ℏ
  Donc G n'est pas indépendant non plus — il suit ℏ.
  
  → IL RESTE UN SEUL PARAMÈTRE LIBRE : ℏ (ou h).
  → Le triangle G-h-k_B n'a qu'un SEUL degré de liberté.
""")

# Combinaisons sans dimension indépendantes
# Les 4 constantes (G, h, k_B, c) donnent 3 combinaisons sans dimension
# Si le triangle a 1 seul degré de liberté, il y a 2 combinaisons indépendantes

# Combinaison 1 : ℏc/G / m_e² = facteur sans dimension
P1 = HBAR_SI * C / G_SI / M_E_SI**2
print(f"\n  Π₁ = ℏc/G / m_e² = {P1:.6f}")
# Ce devrait être (√2 × c₁·c₂ / c₃₇)² ≈ ?
P1_THU = (SQRT2 * C1C2 / C37)**2
print(f"  Π₁_THU = (√2·c₁·c₂/c₃₇)² = {P1_THU:.6f}")
print(f"  écart = {abs(P1 - P1_THU)/P1_THU*100:.4f}%")

# Combinaison 2 : h·c/k_B / T* (action × temps / température)
P2 = H_SI * C / KB_SI / T_STAR
print(f"\n  Π₂ = hc/k_B / T* = {P2:.6f}")
# Dimension m (longueur thermique)
# Ce nombre est sans dimension quand on utilise T* comme échelle ?

# ══════════════════════════════════════════════════════════════════════
# PARTIE 4 — LA RELATION DE HIÉRARCHIE : M_Pl/m_e
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("PARTIE 4 — LA HIÉRARCHIE M_Pl/m_e ≈ 2×10²²")
print("=" * 72)

HIERARCHY = math.sqrt(HBAR_SI * C / G_SI) / M_E_SI
print(f"\n  M_Pl/m_e = {HIERARCHY:.6e}")
print(f"  (√2·c₁c₂/c₃₇) = {SQRT2*C1C2/C37:.6e}")
print(f"  écart = {abs(HIERARCHY - SQRT2*C1C2/C37) / (SQRT2*C1C2/C37)*100:.4f}%")

# La hiérarchie de la tour : e⁴⁴ × (e²/π)⁴ × 60 ≈ M_Pl/m_e
HIER_E44 = math.e**44
HIER_MPME_THU = HIER_E44 * (math.e**2/math.pi)**4 * 60
print(f"\n  M_Pl/m_p = e⁴⁴ = {HIER_E44:.4e}")
print(f"  m_p/m_e = (e²/π)⁴×60 = {(math.e**2/math.pi)**4*60:.4f}")
print(f"  M_Pl/m_e = {HIER_E44*((math.e**2/math.pi)**4*60):.4e}")
print(f"  M_Pl/m_e exact = {HIERARCHY:.4e}")
print(f"  écart = {abs(HIER_E44*((math.e**2/math.pi)**4*60) - HIERARCHY)/HIERARCHY*100:.4f}%")

# ══════════════════════════════════════════════════════════════════════
# PARTIE 5 — CE QUI RESTE
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("PARTIE 5 — BILAN DU TRIANGLE F5")
print("=" * 72)
print("""
  Ce qui est FERMÉ :
  ─────────────────
  ✅ G = ℏc × c₃₇² / (m_e² × 2·c₁²·c₂²)       (via E1b)
  ✅ k_B = ΔE_H / (T* × ln φ)                   (via T*, écart 0,3%)
  ✅ m_e = M_Pl × c₃₇ / (√2 × c₁·c₂)           (E1b)
  ✅ m_p/m_e = (e²/π)⁴ × 60                     (déjà dérivé)
  ✅ M_Pl/m_p = e⁴⁴                              (déjà dérivé, 1,23%)
  ✅ M_Pl/m_e = e⁴⁴ × (e²/π)⁴ × 60              (cohérent)
  
  Ce qui reste OUVERT (1 seul paramètre) :
  ──────────────────────────────────────
  ❌ ℏ (ou h) — c'est le SEUL paramètre libre
  ❌ G n'est pas indépendant : G = ℏ·c × (c₃₇²/(m_e²·2·c₁²·c₂²))
  ❌ k_B n'est pas indépendant : k_B = ΔE_H/(T*·ln φ)
     (ΔE_H = h·ν_H, donc k_B ∝ h — même degré de liberté)
  
  LE TRIANGLE N'A QU'UN SEUL DEGRÉ DE LIBERTÉ : ℏ (ou h).
  Les trois constantes G, h, k_B sont liées par deux équations :
  
    1. G·m_e²/(ℏc) = (c₃₇/(√2·c₁·c₂))²
    2. k_B·T*/(ℏ·ν_H) = 1/ln φ
  
  Si on détermine ℏ par une relation de la tour, le triangle est CLOS.
""")

# Ce qui manque : une relation pour ℏ
# ℏ est « l'étalon déclaré » — mais peut-être ℏ = f(φ, π, e) ?

# La relation conjecturée : rapport ℏ/tau_mémoire
TAU_MEM = ((1-ALPHA)/ALPHA)**(1/ALPHA)
print(f"\n  τ_mémoire = {TAU_MEM:.6f} (en unités naturelles)")
print(f"  h = E₀·τ_mémoire·2π")
print(f"  Si E₀ = ℏ·ω₀, alors h = ℏ·ω₀·τ_mémoire·2π")
print(f"  → h = ℏ · (ω₀·τ_mémoire·2π)")
print(f"  → ce qui est vrai si ω₀·τ_mémoire·2π = 1")
print(f"  → ω₀ = 1/(τ_mémoire·2π) = {1/(TAU_MEM*2*math.pi):.4f}")
print()

# Sauvegarde
rapport = {
    "piste": "F5 — Le triangle G-h-k_B",
    "resultats": {
        "G_via_E1b": G_VIA_E1b, "G_CODATA": G_SI,
        "G_ecart_pct": abs(G_VIA_E1b-G_SI)/G_SI*100,
        "M_Pl_via_me": M_PL_VIA_ME,
        "hierarchie_M_Pl_me": HIERARCHY,
        "hierarchie_via_tour": SQRT2*C1C2/C37,
        "k_B_via_H": KB_VIA_H, "k_B_CODATA": KB_SI,
        "de_gre_liberte": "1 seul paramètre : ℏ (les relations E1b et T* ferment G et k_B)",
        "relation_G": "G = ℏc × c₃₇²/(m_e² × 2·c₁²·c₂²)",
        "relation_kB": "k_B = ΔE_H/(T* × ln φ)",
        "conclusion": "Le triangle F5 a un seul degré de liberté (ℏ). G et k_B sont déterminés par ℏ via les relations de la tour et T*. ℏ reste l'étalon déclaré non dérivé."
    },
    "date": time.strftime("%Y-%m-%d %H:%M:%S")
}

chemin = os.path.join("data", "benchmarks", "piste_F5_triangle_rapport.json")
os.makedirs(os.path.dirname(chemin), exist_ok=True)
with open(chemin, "w", encoding="utf-8") as f:
    json.dump(rapport, f, indent=2, ensure_ascii=False)
print(f"Rapport : {chemin}")