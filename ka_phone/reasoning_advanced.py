#!/usr/bin/env python3
r"""
KA-Next — RAISONNEMENT AVANCÉ (Auto-récurrence + Abduction)
===============================================================
Implémente deux mécanismes de raisonnement avancés basés sur
la méthodologie ondulatoire :

1. AUTO-RÉCURRENCE AVEC CONVERGENCE
   La sortie de l'étape 4 devient l'entrée de l'étape 2.
   La boucle continue jusqu'à ce que :
   - L'interférence avec le résultat stagne (Δ < ε)
   - Tous les faits disponibles soient épuisés
   - Un nouveau fait identique à un précédent soit détecté (cycle)

2. ABDUCTION PAR DÉPHASAGE φ
   Génère N hypothèses candidates par rotation de phase,
   puis sélectionne celle qui maximise l'interférence avec
   les faits existants. C'est l'équivalent ondulatoire de
   "trouver l'explication la plus probable".

Exemples :
  python reasoning_advanced.py --mode recurrence
  python reasoning_advanced.py --mode abduction
  python reasoning_advanced.py --mode all

Usage :
  python reasoning_advanced.py
"""

import sys, os, math, hashlib, time
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np

PHI = (1 + math.sqrt(5)) / 2

# ═══════════════════════════════════════════════════════════════════
# BASE DE CONNAISSANCES (pour les tests)
# ═══════════════════════════════════════════════════════════════════

KNOWLEDGE_BASE = [
    "La capitale du Mali est Bamako.",
    "Tombouctou est une ville du Mali.",
    "Tombouctou est célèbre pour ses manuscrits anciens.",
    "L'université de Sankoré se trouve à Tombouctou.",
    "Le Mali est un pays d'Afrique de l'Ouest.",
    "La capitale du Sénégal est Dakar.",
    "Dakar est une ville portuaire sur l'océan Atlantique.",
    "La capitale de la France est Paris.",
    "Paris est la ville la plus visitée au monde.",
    "Bamako est la plus grande ville du Mali.",
    "Le fleuve Niger traverse le Mali.",
    "Le Sénégal est un pays d'Afrique de l'Ouest.",
    "La Gambie est enclavée dans le Sénégal.",
    "Le Ghana est un pays d'Afrique de l'Ouest.",
    "La capitale du Ghana est Accra.",
]


def get_encoder():
    """Récupère le SpectralEncoder depuis l'ensemble holographique."""
    from holographic_ensemble import HolographicEnsemble
    ensemble = HolographicEnsemble()
    ensemble.build_all(force_rebuild=False)
    geo_holo = ensemble.holograms.get("geography")
    if geo_holo and geo_holo.spectral_encoder:
        return geo_holo.spectral_encoder
    return None


def interference(w1, w2) -> float:
    """Cos(θ) entre deux ondes."""
    kx1, ky1 = w1
    kx2, ky2 = w2
    dot = kx1*kx2 + ky1*ky2
    n1 = math.sqrt(kx1**2 + ky1**2)
    n2 = math.sqrt(kx2**2 + ky2**2)
    if n1 < 1e-10 or n2 < 1e-10:
        return 0.0
    return dot / (n1 * n2)


# ═══════════════════════════════════════════════════════════════════
# MODE 1 — AUTO-RÉCURRENCE AVEC CONVERGENCE
# ═══════════════════════════════════════════════════════════════════

def reasoning_recurrent(question: str, knowledge_base: list,
                        encoder, max_hops: int = 10,
                        convergence_threshold: float = 0.01) -> dict:
    """
    Raisonnement auto-récurrent avec critère de convergence.

    Algorithme :
      Ψ_current = Ψ_question
      HOPS_VUS = {}
      POUR hop = 0..MAX:
        FAIT = argmax(f ∈ KB \ HOPS_VUS) |interférence(Ψ_current, Ψ_f)|
        SI FAIT déjà vu → cycle détecté, arrêt
        HOPS_VUS.ajouter(FAIT)
        NOUVEAU_SCORE = interference(Ψ_current, FAIT)
        SI |NOUVEAU_SCORE - ANCIEN_SCORE| < ε → convergence, arrêt
        Ψ_current = (Ψ_current + Ψ_fait) / 2
        ANCIEN_SCORE = NOUVEAU_SCORE
    """
    q_wave = encoder(question)
    facts_encoded = [(f, encoder(f)) for f in knowledge_base]

    lines = [
        f"RAISONNEMENT AUTO-RÉCURRENT",
        f"{'=' * 50}",
        f"Question : {question[:120]}",
        f"Hops maximum : {max_hops} | Seuil convergence : {convergence_threshold}",
        f"",
    ]

    current_wave = q_wave
    seen_indices = set()
    chain = []
    prev_score = None
    converged = False
    stopped_by_cycle = False

    for hop in range(max_hops):
        # Trouver le meilleur fait non encore vu
        best_idx = -1
        best_interf = 0.0
        best_wave = None

        for i, (fact_text, fact_wave) in enumerate(facts_encoded):
            if i in seen_indices:
                continue
            interf = interference(current_wave, fact_wave)
            if abs(interf) > abs(best_interf):
                best_interf = interf
                best_idx = i
                best_wave = fact_wave

        if best_idx < 0:
            lines.append(f"  Saut {hop} : plus de faits disponibles.")
            break

        best_text = facts_encoded[best_idx][0]

        # Détection de cycle
        seen_texts = set()
        for h, t, s in chain:
            key = t[:60]
            if key == best_text[:60]:
                stopped_by_cycle = True
                lines.append(f"  Saut {hop} : CYCLE DÉTECTÉ — fait déjà vu au saut {h}.")
                break
        if stopped_by_cycle:
            break

        # Vérification de convergence
        if prev_score is not None:
            delta = abs(abs(best_interf) - abs(prev_score))
            if delta < convergence_threshold:
                converged = True
                lines.append(f"  Saut {hop} : CONVERGENCE (Δ={delta:.4f} < {convergence_threshold})")
                # Ajouter le fait quand même pour le contexte
                seen_indices.add(best_idx)
                chain.append((hop, best_text, best_interf))
                break

        # Ajouter le fait
        seen_indices.add(best_idx)
        chain.append((hop, best_text, best_interf))
        prev_score = best_interf

        lines.append(f"  Saut {hop} : '{best_text[:90]}' (interf: {best_interf:+.3f})")

        # Substitution : moyenne
        current_wave = (
            (current_wave[0] + best_wave[0]) / 2,
            (current_wave[1] + best_wave[1]) / 2
        )

    # Conclusion
    lines.append(f"")
    lines.append(f"[Résultat]")
    lines.append(f"  Hops effectués : {len(chain)}")
    lines.append(f"  Convergence    : {'✓' if converged else '✗ (max hops atteint)'}")
    lines.append(f"  Cycle détecté  : {'✓' if stopped_by_cycle else '✗'}")
    lines.append(f"  Fait final      : {chain[-1][1][:120] if chain else 'Aucun'}")
    lines.append(f"  Score final     : {abs(chain[-1][2]):.2%}" if chain else "")

    return {
        "text": "\n".join(lines),
        "chain": chain,
        "converged": converged,
        "stopped_by_cycle": stopped_by_cycle,
        "hops": len(chain),
    }


# ═══════════════════════════════════════════════════════════════════
# MODE 2 — ABDUCTION PAR DÉPHASAGE φ
# ═══════════════════════════════════════════════════════════════════

def reasoning_abduction(observation: str, knowledge_base: list,
                        encoder, num_hypotheses: int = 5,
                        phase_steps: int = 7) -> dict:
    """
    Abduction par déphasage φ : génère N hypothèses candidates
    en faisant tourner l'onde de l'observation dans l'espace de phase,
    puis sélectionne l'hypothèse qui maximise l'interférence avec
    les faits connus.

    Algorithme :
      1. Ψ_obs = encoder(observation)
      2. POUR chaque angle de rotation θ = k × φ × π / K (k=0..K-1):
           Ψ_hyp = Ψ_obs × e^(iθ)  (rotation de θ dans le plan)
           chercher le fait le plus proche de Ψ_hyp
           → hypothèse candidate
      3. Évaluer chaque hypothèse : score = interférence avec TOUS les faits
      4. Retourner l'hypothèse de score maximal

    Exemple :
      Observation : "Tombouctou est une ville historique"
      Hypothèses générées par déphasage :
        θ=0°    → "Tombouctou est une ville du Mali" (résonance max)
        θ=93°   → "L'université de Sankoré se trouve à Tombouctou"
        θ=186°  → "La capitale du Mali est Bamako"
        ...
      Meilleure hypothèse : celle qui explique le mieux l'observation
    """
    q_wave = encoder(observation)
    facts_encoded = [(f, encoder(f)) for f in knowledge_base]

    lines = [
        f"ABDUCTION PAR DÉPHASAGE φ",
        f"{'=' * 50}",
        f"Observation : {observation[:120]}",
        f"Hypothèses générées : {phase_steps} | Évaluation sur {len(knowledge_base)} faits",
        f"",
    ]

    # Générer les hypothèses par rotation de phase
    hypotheses = []
    for k in range(phase_steps):
        theta = k * PHI * math.pi / phase_steps  # Rotation par φ
        # Rotation dans le plan complexe : z' = z × e^(iθ)
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        hyp_kx = q_wave[0] * cos_t - q_wave[1] * sin_t
        hyp_ky = q_wave[0] * sin_t + q_wave[1] * cos_t
        hyp_wave = (hyp_kx, hyp_ky)

        # Trouver le fait le plus proche de cette hypothèse
        best_fact = None
        best_interf = 0.0
        for fact_text, fact_wave in facts_encoded:
            interf = interference(hyp_wave, fact_wave)
            if abs(interf) > abs(best_interf):
                best_interf = interf
                best_fact = fact_text

        hypotheses.append({
            "theta_deg": round(math.degrees(theta), 1),
            "hypothesis_wave": hyp_wave,
            "best_fact": best_fact,
            "best_interference": best_interf,
        })

    # Dédupliquer les hypothèses
    seen_facts = set()
    unique_hyps = []
    for h in hypotheses:
        key = h["best_fact"][:60] if h["best_fact"] else ""
        if key and key not in seen_facts:
            seen_facts.add(key)
            unique_hyps.append(h)

    # Évaluer chaque hypothèse : score = interférence moyenne avec TOUS les faits
    for h in unique_hyps:
        if h["best_fact"] is None:
            h["global_score"] = 0.0
            continue
        scores = []
        for fact_text, fact_wave in facts_encoded:
            hyp_fact_wave = encoder(h["best_fact"])
            interf = interference(hyp_fact_wave, fact_wave)
            scores.append(interf)
        h["global_score"] = float(np.mean([abs(s) for s in scores]) if scores else 0.0)

    # Trier par score global décroissant
    unique_hyps.sort(key=lambda x: -x["global_score"])

    # Afficher les hypothèses
    lines.append("Hypothèses générées par déphasage φ :")
    lines.append("")
    for i, h in enumerate(unique_hyps[:num_hypotheses]):
        bar = "█" * int(h["global_score"] * 20) + "░" * (20 - int(h["global_score"] * 20))
        lines.append(f"  [{i+1}] θ={h['theta_deg']:6.1f}° [{bar}] score={h['global_score']:.3f}")
        lines.append(f"      → {h['best_fact'][:100]}")
        lines.append("")

    best_hypothesis = unique_hyps[0] if unique_hyps else None

    if best_hypothesis:
        lines.append(f"[Meilleure hypothèse]")
        lines.append(f"  {best_hypothesis['best_fact']}")
        lines.append(f"  Score global : {best_hypothesis['global_score']:.3f}")
        lines.append(f"  Angle de déphasage : {best_hypothesis['theta_deg']:.1f}° (φ × {best_hypothesis['theta_deg']/PHI/180:.2f})")

    return {
        "text": "\n".join(lines),
        "hypotheses": unique_hyps,
        "best_hypothesis": best_hypothesis,
    }


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Raisonnement avancé")
    p.add_argument("--mode", type=str, default="all",
                   choices=["recurrence", "abduction", "all"])
    args = p.parse_args()

    enc = get_encoder()
    if not enc:
        print("SpectralEncoder non disponible. Lancez expand_ensemble.py d'abord.")
        sys.exit(1)

    print("=" * 70)
    print("  RAISONNEMENT AVANCÉ — Auto-récurrence + Abduction")
    print(f"  Encodeur spectral : {enc.word_count} mots")
    print("=" * 70)

    if args.mode in ("recurrence", "all"):
        print(f"\n{'#' * 70}")
        print(f"  MODE 1 : AUTO-RÉCURRENCE AVEC CONVERGENCE")
        print(f"{'#' * 70}")

        question = "Quelle est la capitale du pays où se trouve Tombouctou ?"
        result = reasoning_recurrent(
            question, KNOWLEDGE_BASE, enc.encode,
            max_hops=10, convergence_threshold=0.03
        )
        print(result["text"])

    if args.mode in ("abduction", "all"):
        print(f"\n{'#' * 70}")
        print(f"  MODE 2 : ABDUCTION PAR DÉPHASAGE φ")
        print(f"{'#' * 70}")

        observation = "Tombouctou est une ville historique du Sahara"
        result = reasoning_abduction(
            observation, KNOWLEDGE_BASE, enc.encode,
            num_hypotheses=5, phase_steps=8
        )
        print(result["text"])

        # Second exemple d'abduction
        print(f"\n{'─' * 70}")
        print(f"  Second exemple : observation incomplète")
        print(f"{'─' * 70}")
        observation2 = "Dakar est une ville côtière"
        result2 = reasoning_abduction(
            observation2, KNOWLEDGE_BASE, enc.encode,
            num_hypotheses=3, phase_steps=6
        )
        print(result2["text"])

    print(f"\n{'=' * 70}")
    print("  FIN")
    print("=" * 70)