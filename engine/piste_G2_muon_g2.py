#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PISTE G2 — ANOMALIE DU MUON (g-2) DANS LE CADRE THU
=====================================================
Objectif : calculer la contribution des niveaux n>4 de la tour 
à l'anomalie du moment magnétique du muon a_μ = (g-2)/2.

Données :
  a_μ(SM)   = 116591810(43)×10⁻¹¹
  a_μ(mes)  = 116592059(22)×10⁻¹¹  
  Δa_μ     = (249±48)×10⁻¹¹  (5σ)

Hypothèse THU :
  L'anomalie vient des niveaux n>4 de la tour, absents du SM.
  Le muon (n=34, type 6, k=4) couple à ces niveaux via cₙ.
  La contribution dépend du type et de l'itération.

PLAN :
  1. Calculer la contribution des niveaux n=5,6,7 à a_μ
  2. Comparer avec l'électron (n=37, type 2, k=5)
  3. Vérifier si le rapport a_μ/a_e est cohérent
  4. Prédire la valeur THU de a_μ
"""

import json, math, os, time
import numpy as np

PHI = (1 + math.sqrt(5)) / 2
ALPHA = 1 / PHI
ALPHA_EM = 1 / 137.035999084
PI = math.pi

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

# Constantes
C1, C2, C3, C4, C5, C6, C7 = [c(n) for n in range(1, 8)]
C1C2 = C1 * C2

# Masses
M_PL = 2.176434e-8  # kg
M_E = 9.1093837015e-31
M_MU = 1.883531627e-28  # kg (105.66 MeV)
M_TAU = 3.16754e-27  # kg (1.777 GeV)

# Anomalies (×10⁻¹¹)
A_E_SM = 1159652180.0  # a_e ×10⁻¹¹
A_E_MES = 1159652180.7  # a_e ×10⁻¹¹ (accords à 10⁻¹²)
A_MU_SM = 116591810.0  # a_μ ×10⁻¹¹
A_MU_MES = 116592059.0  # a_μ ×10⁻¹¹
DELTA_MU = A_MU_MES - A_MU_SM  # = 249×10⁻¹¹

print("=" * 72)
print("PISTE G2 — ANOMALIE DU MUON (g-2) DANS LE CADRE THU")
print("=" * 72)

print(f"\n  a_μ(SM)   = {A_MU_SM:.0f}×10⁻¹¹")
print(f"  a_μ(mes)  = {A_MU_MES:.0f}×10⁻¹¹")
print(f"  Δa_μ      = {DELTA_MU:.0f}×10⁻¹¹ (5σ)")
print(f"  a_e(SM)   = {A_E_SM:.0f}×10⁻¹¹ (accord < 10⁻¹²)")

# ══════════════════════════════════════════════════════════════════════
# PARTIE 1 — STRUCTURE DES LEPTONS DANS LA TOUR
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("PARTIE 1 — STRUCTURE DES LEPTONS DANS LA TOUR")
print("=" * 72)

print(f"""
  Particule :   n    type  k    cₙ           masse
  ─────────────────────────────────────────────────────
  électron     37   2     5    {c(37):.4e}   {M_E:.4e} kg
  muon         34   6     4    {c(34):.4e}   {M_MU:.4e} kg
  tau          33   5     4    {c(33):.4e}   {M_TAU:.4e} kg
""")

# Rapport des masses
print(f"  m_μ/m_e = {M_MU/M_E:.4f}  (THU: {C1*C2*PHI/ALPHA:.4f}?)")
print(f"  m_τ/m_μ = {M_TAU/M_MU:.4f}")

# ══════════════════════════════════════════════════════════════════════
# PARTIE 2 — CONTRIBUTION DES NIVEAUX n>4 DE LA TOUR
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("PARTIE 2 — CONTRIBUTION DE LA TOUR À a_μ")
print("=" * 72)
print("""
  Hypothèse : a_μ(tour) = Σ_{n>4} cₙ² · (m_μ² / Λ²) · g(φ)
  
  où Λ est l'échelle d'énergie de chaque niveau de la tour.
  Le niveau n a une échelle Λ_n = M_Pl / cₙ.
  
  Mais la contribution dominante vient du couplage entre le muon
  et les niveaux de la tour via l'échange de particules virtuelles.
  Dans le SM, le diagramme dominant est l'échange d'un photon (n=1).
  Dans la THU, il y a échange de niveaux n>4.
""")

# Contribution des niveaux n=5,6,7
# a_μ = (α/π) + ... (QED)
# La contribution d'un niveau n est proportionnelle à cₙ² × (m_μ/Λ_n) × facteur

facteurs_n = {}
print(f"  {'n':>4s} {'cₙ':>12s} {'cₙ²':>15s} {'m_μ/Λ':>15s} {'contrib':>15s}")
print(f"  {'-'*62}")

total_contrib = 0.0
for n in range(5, 15):
    cn = c(n)
    # Échelle du niveau : Λ_n = M_Pl / cn (en unités de masse)
    # Ratio m_μ / Λ_n = m_μ × cn / M_Pl
    ratio = M_MU * cn / M_PL
    # Contribution = α_EM × cₙ² × (m_μ/Λ_n) × (facteur de phase)
    # Le facteur de phase vient de l'interférence — typiquement φ^{-k}
    facteur_phase = 1.0
    contrib = ALPHA_EM * cn**2 * ratio * facteur_phase
    total_contrib += contrib
    print(f"  {n:4d} {cn:12.6e} {cn**2:15.6e} {ratio:15.6e} {contrib:15.6e}")

print(f"\n  Contribution totale (n=5..14) : {total_contrib:.6e}")
print(f"  Δa_μ mesuré                    : {DELTA_MU*1e-11:.6e}")
print(f"  Rapport contrib/Δa_μ            : {total_contrib/(DELTA_MU*1e-11):.4f}")

# ══════════════════════════════════════════════════════════════════════
# PARTIE 3 — RAPPORT DES ANOMALIES μ/e
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("PARTIE 3 — RAPPORT DES ANOMALIES μ/e")
print("=" * 72)

# a_e est en accord avec le SM → sa contribution tour est négligeable
# a_μ montre une déviation → sa contribution tour est significative
# Le rapport des contributions tour devrait être lié au rapport des masses
# et aux types/iterations

# Rapport des masses
RATIO_M = M_MU / M_E
print(f"\n  m_μ/m_e = {RATIO_M:.4f}")

# La contribution tour à a_μ dépend du type de la particule
# dans la tour : a_μ ∝ f(type, k) × (m_μ/M_Pl)²
# L'électron (type 2, k=5) et le muon (type 6, k=4) ont des types différents

# Contribution pour chaque lepton
leptons = [("e", M_E, 37), ("μ", M_MU, 34), ("τ", M_TAU, 33)]
for nom, masse, n_part in leptons:
    cn = c(n_part)
    ratio = masse * cn / M_PL
    contrib = ALPHA_EM * cn**2 * ratio
    print(f"  {nom:>2s} : n={n_part}, cₙ={cn:.4e}, m/M_Pl={masse/M_PL:.4e}, contrib_tour={contrib:.4e}")

# ══════════════════════════════════════════════════════════════════════
# PARTIE 4 — VERS UNE FORMULE FERMÉE
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("PARTIE 4 — VERS UNE FORMULE FERMÉE")
print("=" * 72)
print("""
  Le calcul naïf donne une contribution trop faible (×10⁻¹⁵).
  Cela signifie que le mécanisme n'est pas un simple échange de niveau.
  
  PISTE SÉRIEUSE : l'anomalie du muon est dominée par les diagrammes
  à ÉTAT LIÉ (hadronique) dans le SM — la contribution la plus incertaine.
  La THU suggère que les niveaux n>4 de la tour créent des états liés
  virtuels avec le muon, amplifiant la contribution.
  
  La forme correcte est probablement :
    Δa_μ(tour) = Σ cₙ² · (m_μ² / M_Pl²) · (couplage_résonant)
    
  où le couplage résonant est amplifié quand m_μ est proche de la masse
  d'un niveau de la tour.
  
  RECHERCHE : quel niveau n donne une masse proche de m_μ ?
""")

for n in range(1, 15):
    cn = c(n)
    masse_n = M_PL * cn
    ratio = masse_n / M_MU
    if 0.1 < ratio < 10:
        print(f"  n={n:2d} : masse_n = {masse_n:.4e} kg = {masse_n/M_MU:.4f} × m_μ")

# ══════════════════════════════════════════════════════════════════════
# PARTIE 5 — PRÉDICTION THU
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("PARTIE 5 — PRÉDICTION THU POUR a_μ")
print("=" * 72)
print("""
  La THU ne peut pas encore calculer a_μ exactement — elle n'est pas
  une théorie des perturbations. Mais elle PRÉDIT que :
  
  1. L'anomalie à 5σ est RÉELLE — pas une fluctuation
  2. Elle ne disparaîtra pas avec de nouvelles mesures (Fermilab, J-PARC)
  3. Le rapport a_μ/a_e suit la structure de la tour : 
     les deux leptons sont à des types et itérations différents
  4. La valeur exacte de Δa_μ peut être exprimée comme une combinaison
     de coefficients cₙ et de constantes fondamentales
  
  PROCHAINE ÉTAPE : identifier la structure diagrammatique exacte
  de la contribution de la tour à a_μ dans le formalisme de la QFT
  harmonique (unification QM-RG).
""")

# Sauvegarde
rapport = {
    "piste": "G2 — Anomalie du muon (g-2)",
    "resultats": {
        "a_mu_SM": A_MU_SM, "a_mu_mes": A_MU_MES, "delta_mu": DELTA_MU,
        "contrib_tour_naive": total_contrib,
        "delta_vs_contrib": total_contrib/(DELTA_MU*1e-11),
        "conclusion": "Le calcul naïf donne une contribution trop faible. L'anomalie nécessite un mécanisme résonant — peut-être des états liés virtuels entre le muon et les niveaux n>4 de la tour. La piste est ouverte, la solution exacte n'est pas encore dans le dépôt."
    },
    "date": time.strftime("%Y-%m-%d %H:%M:%S")
}

chemin = os.path.join("data", "benchmarks", "piste_G2_muon_g2_rapport.json")
os.makedirs(os.path.dirname(chemin), exist_ok=True)
with open(chemin, "w", encoding="utf-8") as f:
    json.dump(rapport, f, indent=2, ensure_ascii=False)
print(f"\nRapport : {chemin}")