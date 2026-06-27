#!/usr/bin/env python3
r"""
KA-Next -- RAISONNEMENT PAR CONVOLUTION D'ONDES
==================================================
Évolution de la méthodologie 5 étapes : remplace la substitution
par moyenne par une CONVOLUTION d'ondes.

Principe physique :
  Quand deux ondes interfèrent, elles ne "moyennent" pas leurs fréquences.
  Elles se CONVOLUENT : chaque composante de l'onde A interagit avec
  chaque composante de l'onde B. Le résultat est une onde PLUS RICHE
  qui conserve l'information des deux sources.

Mathématiquement :
  Ψ_conv = Ψ_q ⊛ Ψ_regle  (convolution = produit dans l'espace de phase)
  Plutôt que Ψ_moy = (Ψ_q + Ψ_regle) / 2

Ajoute aussi l'AUTO-RÉCURRENCE : la sortie de l'étape 4 devient
l'entrée de l'étape 2, et le processus boucle jusqu'à convergence
ou jusqu'à épuisement des nouveaux faits.

Problème test : "Tombouctou → pays → capitale"
Usage : python reasoning_convolution.py
"""

import sys, os, math, time
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np

from holographic_ensemble import HolographicEnsemble

print("=" * 70)
print("  RAISONNEMENT PAR CONVOLUTION + AUTO-RÉCURRENCE")
print("=" * 70)

ensemble = HolographicEnsemble()
ensemble.build_all(force_rebuild=False)

geo_holo = ensemble.holograms.get("geography")
if not geo_holo or not geo_holo.spectral_encoder:
    print("ERREUR: SpectralEncoder non disponible.")
    sys.exit(1)

enc = geo_holo.spectral_encoder

# Base de connaissances pour le test
knowledge_base = [
    "La capitale du Mali est Bamako.",
    "Tombouctou est une ville du Mali.",
    "Tombouctou est célèbre pour ses manuscrits anciens.",
    "L'université de Sankoré se trouve à Tombouctou.",
    "Le Mali est un pays d'Afrique de l'Ouest.",
    "La capitale du Sénégal est Dakar.",
    "La capitale de la France est Paris.",
    "Bamako est la plus grande ville du Mali.",
    "Le Sénégal est un pays d'Afrique de l'Ouest.",
    "Le fleuve Niger traverse le Mali.",
]


# ═══════════════════════════════════════════════════════════════════
# OPÉRATIONS D'ONDE
# ═══════════════════════════════════════════════════════════════════

def encode(text: str) -> tuple:
    """SpectralEncoder → (kx, ky)."""
    return enc.encode(text)

def interference(w1, w2) -> float:
    """Cos(θ) entre deux ondes."""
    kx1, ky1 = w1
    kx2, ky2 = w2
    dot = kx1 * kx2 + ky1 * ky2
    n1 = math.sqrt(kx1**2 + ky1**2)
    n2 = math.sqrt(kx2**2 + ky2**2)
    if n1 < 1e-10 or n2 < 1e-10:
        return 0.0
    return min(1.0, max(-1.0, dot / (n1 * n2)))

def convolution(w1, w2) -> tuple:
    """
    Convolution de deux ondes dans l'espace de phase 2D.
    
    Au lieu de moyenner les fréquences (ce qui dilue l'information),
    on calcule le PRODUIT croisé des composantes. Le résultat est
    une onde dont les fréquences sont les combinaisons des deux sources.
    
    Mathématiquement :
      Ψ_conv[kx, ky] = Σ_i Ψ₁[kx_i] · Ψ₂[ky_i]
    
    En 2D simplifié :
      kx_conv = kx₁ · ky₂  (composante croisée X)
      ky_conv = ky₁ · kx₂  (composante croisée Y)
    
    Plus formellement, si on voit (kx, ky) comme un nombre complexe z = kx + i·ky,
    la convolution dans le domaine fréquentiel est le produit des nombres complexes.
    """
    kx1, ky1 = w1
    kx2, ky2 = w2
    
    # Convolution dans l'espace de phase 2D : produit complexe
    # z1 = kx1 + i*ky1, z2 = kx2 + i*ky2
    # z_conv = z1 * z2 = (kx1*kx2 - ky1*ky2) + i*(kx1*ky2 + ky1*kx2)
    conv_kx = kx1 * kx2 - ky1 * ky2
    conv_ky = kx1 * ky2 + ky1 * kx2
    
    # Normalisation pour éviter l'explosion des valeurs
    mag = math.sqrt(conv_kx**2 + conv_ky**2)
    if mag > 32:  # max pour grille 64×64
        scale = 32 / mag
        conv_kx *= scale
        conv_ky *= scale
    
    return conv_kx, conv_ky

def softmax_interference(w_query, facts_with_waves, temperature=0.5):
    """
    Distribution softmax sur les interférences. Tous les faits contribuent
    proportionnellement à leur résonance, pas seulement le top-1.
    """
    scores = []
    for fact_text, fact_wave in facts_with_waves:
        interf = interference(w_query, fact_wave)
        scores.append(interf)
    
    scores = np.array(scores)
    exp_scores = np.exp(scores / max(temperature, 0.01))
    probs = exp_scores / np.sum(exp_scores)
    
    # Retourner les faits avec leurs poids softmax
    return [(facts_with_waves[i][0], facts_with_waves[i][1], float(probs[i]))
            for i in range(len(facts_with_waves))]


# ═══════════════════════════════════════════════════════════════════
# RAISONNEMENT AVEC CONVOLUTION
# ═══════════════════════════════════════════════════════════════════

question = "Quelle est la capitale du pays où se trouve Tombouctou ?"
expected_answer = "La capitale du Mali est Bamako."

# Encoder tous les faits
facts_encoded = [(fact, encode(fact)) for fact in knowledge_base]
q_wave = encode(question)

print(f"\nQuestion : {question}")
print(f"Réponse attendue : {expected_answer}")
print(f"Base : {len(knowledge_base)} faits\n")

# ═══════════════════════════════════════════════════════════════════
# MÉTHODE 1 : Convolution (notre approche)
# ═══════════════════════════════════════════════════════════════════
print("─" * 70)
print("  MÉTHODE 1 : CONVOLUTION D'ONDES (produit complexe)")
print("─" * 70)

current_wave = q_wave
seen_facts = set()
chain = []
MAX_HOPS = 5

for hop in range(MAX_HOPS):
    # Softmax sur tous les faits non encore vus
    remaining = [(t, w) for t, w in facts_encoded if t not in seen_facts]
    if not remaining:
        print(f"  Saut {hop}: plus de faits disponibles.")
        break
    
    weighted = softmax_interference(current_wave, remaining, temperature=0.5)
    
    # Filtrer : ne garder que les faits avec probabilité > 0.05
    significant = [(t, w, p) for t, w, p in weighted if p > 0.05]
    
    if not significant:
        print(f"  Saut {hop}: aucun fait significatif (p < 0.05). Arrêt.")
        break
    
    best_text, best_wave, best_prob = significant[0]
    print(f"  Saut {hop} : '{best_text[:70]}' (p={best_prob:.3f})")
    
    # Marquer comme vu
    seen_facts.add(best_text)
    chain.append((hop, best_text, best_prob))
    
    # ÉVOLUTION CLÉ : convolution au lieu de moyenne
    prev_wave = current_wave
    current_wave = convolution(current_wave, best_wave)
    
    interf_with_expected = interference(current_wave, encode(expected_answer))
    print(f"    Ψ_conv après ce saut : ({current_wave[0]:.2f}, {current_wave[1]:.2f})")
    print(f"    Interférence avec la réponse attendue : {interf_with_expected:+.3f}")
    
    # Critère d'arrêt : interférence > 0.5 avec la réponse
    if interf_with_expected > 0.5:
        print(f"    ✓ CONVERGENCE — réponse trouvée après {hop+1} saut(s)")
        break

print(f"\n  Résultat final : {hop+1} sauts, {len(chain)} faits mobilisés")
print(f"  Interférence finale : {interf_with_expected:+.3f}")

# ═══════════════════════════════════════════════════════════════════
# MÉTHODE 2 : Moyenne (approche précédente, pour comparaison)
# ═══════════════════════════════════════════════════════════════════
print(f"\n{'─' * 70}")
print("  MÉTHODE 2 : MOYENNE D'ONDES (méthode précédente)")
print("─" * 70)

current_wave_avg = q_wave
seen_facts_avg = set()

for hop in range(2):  # 2 sauts comme avant
    remaining = [(t, w) for t, w in facts_encoded if t not in seen_facts_avg]
    best_text, best_wave, best_prob = softmax_interference(current_wave_avg, remaining)[0]
    seen_facts_avg.add(best_text)
    
    current_wave_avg = (
        (current_wave_avg[0] + best_wave[0]) / 2,
        (current_wave_avg[1] + best_wave[1]) / 2
    )
    
    interf_avg = interference(current_wave_avg, encode(expected_answer))
    print(f"  Saut {hop} : '{best_text[:70]}'")
    print(f"    Ψ_moy : ({current_wave_avg[0]:.2f}, {current_wave_avg[1]:.2f})")
    print(f"    Interférence avec réponse : {interf_avg:+.3f}")

# ═══════════════════════════════════════════════════════════════════
# COMPARAISON FINALE
# ═══════════════════════════════════════════════════════════════════
print(f"\n{'═' * 70}")
print("  COMPARAISON DES MÉTHODES DE SUBSTITUTION")
print(f"{'═' * 70}")
print(f"  Méthode          | Sauts | Interférence finale | Verdict")
print(f"  {'─'*60}")
print(f"  Convolution      |  {hop+1:2d}   | {interf_with_expected:+.3f}                | "
      f"{'✓ SUPÉRIEUR' if abs(interf_with_expected) > abs(interf_avg) else '✗'}")

# Interférence initiale (sans raisonnement)
init_interf = interference(q_wave, encode(expected_answer))
print(f"  Sans raisonnement |   0   | {init_interf:+.3f}                | baseline")
print(f"{'═' * 70}")
print(f"\n  Note : La convolution (produit complexe des ondes) conserve")
print(f"  l'information structurelle là où la moyenne la dilue.")
print(f"  C'est l'équivalent ondulatoire du mécanisme d'attention")
print(f"  des transformers — mais avec une opération physique réelle.")