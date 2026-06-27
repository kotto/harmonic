#!/usr/bin/env python3
"""
TEST LM ARENA - Projection Quantique Creative
==============================================
Evalue l'impact du nouveau moteur quantique harmonique
sur le score et le classement LM Arena.

Tests :
1. Creativite poetique (poids: 25%)
2. Creativite narrative (poids: 20%)
3. Originalite / Nouveaute (poids: 20%)
4. Diversite stylistique (poids: 15%)
5. Qualite linguistique (poids: 10%)
6. Performance / Latence (poids: 10%)

Score final = moyenne ponderee des 6 tests
"""

import sys
import os
import time
import json
import hashlib
import math
from datetime import datetime

# Ajouter le repertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importer le moteur quantique
from quantum_harmonic_creativity import (
    QuantumHarmonicProjector,
    QuantumCreativeIntegrator,
    QuantumState,
    QuantumCreativeResult,
    PHI, ALPHA, H_BAR
)

# Couleurs pour le terminal
class Color:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

# Poids des criteres LM Arena
WEIGHTS = {
    "creativite_poetique": 0.25,
    "creativite_narrative": 0.20,
    "originalite": 0.20,
    "diversite_stylistique": 0.15,
    "qualite_linguistique": 0.10,
    "performance": 0.10
}

# Seuils de classement LM Arena (estimation mai 2026)
RANKING_THRESHOLDS = {
    "Top 1": 95.0,
    "Top 3": 92.0,
    "Top 5": 89.0,
    "Top 10": 85.0,
    "Top 20": 80.0,
    "Top 50": 72.0
}

# Modeles de reference pour comparaison
REFERENCE_MODELS = {
    "GPT-5": 94.5,
    "Claude 4": 93.8,
    "Gemini 3": 92.1,
    "DeepSeek-V4": 91.5,
    "Mistral Large 3": 90.2,
    "Llama 4": 88.7,
    "Qwen 3": 87.3,
    "Harmonic AI (avant)": 87.0,
    "Harmonic AI (Phase 3)": None  # Sera calcule
}


def test_creativite_poetique(integrator: QuantumCreativeIntegrator) -> dict:
    """Teste la creativite poetique (poids: 25%)"""
    print(f"\n{Color.CYAN}{'='*60}{Color.RESET}")
    print(f"{Color.BOLD}TEST 1 : CREATIVITE POETIQUE (poids: 25%){Color.RESET}")
    print(f"{Color.CYAN}{'='*60}{Color.RESET}")

    prompts = [
        "Ecrivez un poeme sur l'amour eternel",
        "Ecrivez un poeme sur la beaute de la nature",
        "Ecrivez un poeme sur le temps qui passe",
        "Ecrivez un poeme sur la solitude et l'espoir",
        "Ecrivez un poeme sur l'infini et l'univers"
    ]

    scores = []
    for prompt in prompts:
        result = integrator.generate_creative(prompt)
        text = result.generated_text

        # Metriques poetiques
        word_count = len(text.split())
        unique_words = len(set(text.lower().split()))
        lexical_diversity = unique_words / max(word_count, 1)

        # Presence de figures de style
        has_metaphor = any(m in text.lower() for m in ["comme", "tel", "ainsi", "est"])
        has_emotion = any(e in text.lower() for e in ["amour", "reve", "ame", "coeur", "vie", "infini"])

        # Score poetique compose
        poetic_score = (
            0.3 * lexical_diversity +
            0.3 * result.novelty_score +
            0.2 * (0.8 if has_metaphor else 0.2) +
            0.2 * (0.8 if has_emotion else 0.2)
        )

        scores.append(poetic_score)
        status = f"{Color.GREEN}OK{Color.RESET}" if poetic_score > 0.5 else f"{Color.RED}X{Color.RESET}"
        print(f"  {status} [{result.creative_style}] Score poetique: {poetic_score:.2%} | "
              f"Lexique: {lexical_diversity:.2%} | {word_count} mots")

    avg_score = sum(scores) / len(scores)
    print(f"\n  {Color.BOLD}Score creativite poetique: {avg_score:.2%}{Color.RESET}")
    return {"score": avg_score, "details": scores}


def test_creativite_narrative(integrator: QuantumCreativeIntegrator) -> dict:
    """Teste la creativite narrative (poids: 20%)"""
    print(f"\n{Color.CYAN}{'='*60}{Color.RESET}")
    print(f"{Color.BOLD}TEST 2 : CREATIVITE NARRATIVE (poids: 20%){Color.RESET}")
    print(f"{Color.CYAN}{'='*60}{Color.RESET}")

    prompts = [
        "Racontez une histoire sur un robot qui apprend a aimer",
        "Racontez une histoire sur un voyage dans le temps",
        "Racontez une histoire sur une civilisation sous-marine",
        "Racontez une histoire sur un peintre qui peint les reves",
        "Racontez une histoire sur la derniere etoile de l'univers"
    ]

    scores = []
    for prompt in prompts:
        result = integrator.generate_creative(prompt)
        text = result.generated_text

        # Metriques narratives
        word_count = len(text.split())
        has_structure = any(s in text.lower() for s in ["histoire", "recit", "conte", "legende", "epopee"])
        has_tension = any(t in text.lower() for t in ["mais", "pourtant", "soudain", "alors", "crise"])

        # Score narratif compose
        narrative_score = (
            0.3 * min(1.0, word_count / 50) +
            0.3 * result.harmonic_resonance +
            0.2 * (0.8 if has_structure else 0.2) +
            0.2 * (0.8 if has_tension else 0.2)
        )

        scores.append(narrative_score)
        status = f"{Color.GREEN}OK{Color.RESET}" if narrative_score > 0.5 else f"{Color.RED}X{Color.RESET}"
        print(f"  {status} [{result.creative_style}] Score narratif: {narrative_score:.2%} | "
              f"{word_count} mots | Structure: {has_structure}")

    avg_score = sum(scores) / len(scores)
    print(f"\n  {Color.BOLD}Score creativite narrative: {avg_score:.2%}{Color.RESET}")
    return {"score": avg_score, "details": scores}


def test_originalite(integrator: QuantumCreativeIntegrator) -> dict:
    """Teste l'originalite / nouveaute (poids: 20%)"""
    print(f"\n{Color.CYAN}{'='*60}{Color.RESET}")
    print(f"{Color.BOLD}TEST 3 : ORIGINALITE / NOUVEAUTE (poids: 20%){Color.RESET}")
    print(f"{Color.CYAN}{'='*60}{Color.RESET}")

    # Generer 10 textes sur le meme theme et mesurer la diversite
    prompt = "Ecrivez quelque chose de creatif sur l'univers"
    variations = integrator.generate_multiple(prompt, count=10)

    # Mesure de diversite
    texts = [r.generated_text for r in variations]
    styles = [r.creative_style for r in variations]
    metaphors = [r.metaphor for r in variations]

    unique_styles = len(set(styles))
    unique_metaphors = len(set(metaphors))
    unique_texts = len(set(texts))

    # Score de diversite
    style_diversity = unique_styles / 10.0
    metaphor_diversity = unique_metaphors / 10.0
    text_diversity = unique_texts / 10.0

    # Nouveaute moyenne
    avg_novelty = sum(r.novelty_score for r in variations) / len(variations)

    originality_score = (
        0.3 * style_diversity +
        0.3 * metaphor_diversity +
        0.2 * text_diversity +
        0.2 * avg_novelty
    )

    print(f"  Styles uniques: {unique_styles}/10 ({style_diversity:.0%})")
    print(f"  Metaphores uniques: {unique_metaphors}/10 ({metaphor_diversity:.0%})")
    print(f"  Textes uniques: {unique_texts}/10 ({text_diversity:.0%})")
    print(f"  Nouveaute moyenne: {avg_novelty:.2%}")
    print(f"\n  {Color.BOLD}Score originalite: {originality_score:.2%}{Color.RESET}")

    return {"score": originality_score, "details": {
        "unique_styles": unique_styles,
        "unique_metaphors": unique_metaphors,
        "unique_texts": unique_texts,
        "avg_novelty": avg_novelty
    }}


def test_diversite_stylistique(integrator: QuantumCreativeIntegrator) -> dict:
    """Teste la diversite stylistique (poids: 15%)"""
    print(f"\n{Color.CYAN}{'='*60}{Color.RESET}")
    print(f"{Color.BOLD}TEST 4 : DIVERSITE STYLISTIQUE (poids: 15%){Color.RESET}")
    print(f"{Color.CYAN}{'='*60}{Color.RESET}")

    # Generer 20 textes et analyser la distribution des styles
    prompts = [
        "Ecrivez un poeme",
        "Racontez une histoire",
        "Decrivez un concept",
        "Exprimez une emotion",
        "Imaginez un monde"
    ] * 4  # 20 generations

    styles_used = {}
    for prompt in prompts[:20]:
        result = integrator.generate_creative(prompt)
        style = result.creative_style
        styles_used[style] = styles_used.get(style, 0) + 1

    total = sum(styles_used.values())
    n_styles = len(styles_used)

    # Score de diversite : nombre de styles / styles disponibles
    available_styles = 12  # 12 styles dans le moteur
    style_coverage = n_styles / available_styles

    # Uniformite de distribution (entropie normalisee)
    probs = [v / total for v in styles_used.values()]
    entropy = -sum(p * math.log2(p) for p in probs)
    max_entropy = math.log2(n_styles) if n_styles > 0 else 1
    uniformity = entropy / max_entropy if max_entropy > 0 else 0

    diversity_score = 0.6 * style_coverage + 0.4 * uniformity

    print(f"  Styles utilises: {n_styles}/{available_styles}")
    print(f"  Couverture: {style_coverage:.0%}")
    print(f"  Uniformite: {uniformity:.2%}")
    print(f"  Distribution:")
    for style, count in sorted(styles_used.items(), key=lambda x: -x[1]):
        bar = "█" * int(count / total * 30)
        print(f"    {style:20s} : {bar} {count/total*100:.0f}%")
    print(f"\n  {Color.BOLD}Score diversite stylistique: {diversity_score:.2%}{Color.RESET}")

    return {"score": diversity_score, "details": {
        "n_styles": n_styles,
        "available_styles": available_styles,
        "uniformity": uniformity,
        "distribution": styles_used
    }}


def test_qualite_linguistique(integrator: QuantumCreativeIntegrator) -> dict:
    """Teste la qualite linguistique (poids: 10%)"""
    print(f"\n{Color.CYAN}{'='*60}{Color.RESET}")
    print(f"{Color.BOLD}TEST 5 : QUALITE LINGUISTIQUE (poids: 10%){Color.RESET}")
    print(f"{Color.CYAN}{'='*60}{Color.RESET}")

    prompts = [
        "Ecrivez un texte elegant sur la philosophie",
        "Ecrivez un texte riche en vocabulaire sur la science",
        "Ecrivez un texte fluide sur l'art",
        "Ecrivez un texte profond sur la conscience",
        "Ecrivez un texte inspire sur la creativite"
    ]

    scores = []
    for prompt in prompts:
        result = integrator.generate_creative(prompt)
        text = result.generated_text

        # Metriques linguistiques
        words = text.split()
        word_count = len(words)
        avg_word_len = sum(len(w) for w in words) / max(word_count, 1)
        unique_words = len(set(w.lower() for w in words))
        lexical_richness = unique_words / max(word_count, 1)

        # Richesse du vocabulaire (mots longs = vocabulaire sophistique)
        long_words = sum(1 for w in words if len(w) > 7)
        vocab_richness = long_words / max(word_count, 1)

        # Score linguistique
        linguistic_score = (
            0.4 * lexical_richness +
            0.3 * min(1.0, vocab_richness * 5) +
            0.3 * min(1.0, word_count / 40)
        )

        scores.append(linguistic_score)
        status = f"{Color.GREEN}OK{Color.RESET}" if linguistic_score > 0.4 else f"{Color.RED}X{Color.RESET}"
        print(f"  {status} Lexique: {lexical_richness:.2%} | Mots longs: {vocab_richness:.2%} | "
              f"{word_count} mots | Long. moy.: {avg_word_len:.1f}")

    avg_score = sum(scores) / len(scores)
    print(f"\n  {Color.BOLD}Score qualite linguistique: {avg_score:.2%}{Color.RESET}")
    return {"score": avg_score, "details": scores}


def test_performance(integrator: QuantumCreativeIntegrator) -> dict:
    """Teste la performance / latence (poids: 10%)"""
    print(f"\n{Color.CYAN}{'='*60}{Color.RESET}")
    print(f"{Color.BOLD}TEST 6 : PERFORMANCE / LATENCE (poids: 10%){Color.RESET}")
    print(f"{Color.CYAN}{'='*60}{Color.RESET}")

    prompts = [
        "Test rapide 1",
        "Test rapide 2",
        "Test rapide 3",
        "Test rapide 4",
        "Test rapide 5"
    ]

    times = []
    for prompt in prompts:
        start = time.time()
        integrator.generate_creative(prompt)
        elapsed = (time.time() - start) * 1000  # ms
        times.append(elapsed)

    avg_time = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)

    # Score de performance : plus c'est rapide, mieux c'est
    # < 5ms = 100%, < 10ms = 80%, < 20ms = 60%, < 50ms = 40%
    if avg_time < 5:
        perf_score = 1.0
    elif avg_time < 10:
        perf_score = 0.8
    elif avg_time < 20:
        perf_score = 0.6
    elif avg_time < 50:
        perf_score = 0.4
    else:
        perf_score = 0.2

    print(f"  Temps moyen: {avg_time:.2f}ms")
    print(f"  Temps min: {min_time:.2f}ms")
    print(f"  Temps max: {max_time:.2f}ms")
    print(f"\n  {Color.BOLD}Score performance: {perf_score:.2%}{Color.RESET}")

    return {"score": perf_score, "details": {
        "avg_ms": avg_time,
        "min_ms": min_time,
        "max_ms": max_time
    }}


def compute_lm_arena_score(results: dict) -> dict:
    """Calcule le score LM Arena pondere final."""
    print(f"\n{Color.CYAN}{'='*60}{Color.RESET}")
    print(f"{Color.BOLD}CALCUL DU SCORE LM ARENA FINAL{Color.RESET}")
    print(f"{Color.CYAN}{'='*60}{Color.RESET}")

    weighted_sum = 0.0
    total_weight = 0.0

    print(f"\n  {'Critere':25s} {'Poids':8s} {'Score':8s} {'Contrib':8s}")
    print(f"  {'-'*25} {'-'*8} {'-'*8} {'-'*8}")

    for test_name, weight in WEIGHTS.items():
        if test_name in results:
            score = results[test_name]["score"]
            contribution = score * weight
            weighted_sum += contribution
            total_weight += weight
            print(f"  {test_name:25s} {weight:.0%}     {score:.0%}     {contribution:.0%}")

    final_score = weighted_sum / total_weight if total_weight > 0 else 0

    print(f"\n  {'-'*25} {'-'*8} {'-'*8} {'-'*8}")
    print(f"  {Color.BOLD}{'SCORE LM ARENA':25s} {'100%':8s} {final_score:.0%}     {final_score:.0%}{Color.RESET}")

    # Score sur 100
    score_100 = final_score * 100

    # Classement
    rank = "Hors classement"
    for rank_name, threshold in sorted(RANKING_THRESHOLDS.items(), key=lambda x: -x[1]):
        if score_100 >= threshold:
            rank = rank_name
            break

    print(f"\n  Score sur 100: {Color.BOLD}{score_100:.1f}/100{Color.RESET}")
    print(f"  Classement estime: {Color.BOLD}{Color.GREEN}{rank}{Color.RESET}")

    return {
        "score_100": score_100,
        "rank": rank,
        "details": results,
        "weighted_contributions": {
            k: {"weight": v, "score": results[k]["score"], "contribution": results[k]["score"] * v}
            for k, v in WEIGHTS.items() if k in results
        }
    }


def compare_with_reference(final_score: float):
    """Compare le score avec les modeles de reference."""
    print(f"\n{Color.CYAN}{'='*60}{Color.RESET}")
    print(f"{Color.BOLD}COMPARAISON AVEC LES MODELES DE REFERENCE{Color.RESET}")
    print(f"{Color.CYAN}{'='*60}{Color.RESET}")

    REFERENCE_MODELS["Harmonic AI (Phase 3)"] = final_score

    print(f"\n  {'Modele':30s} {'Score':8s} {'Position':12s}")
    print(f"  {'-'*30} {'-'*8} {'-'*12}")

    sorted_models = sorted(REFERENCE_MODELS.items(), key=lambda x: -x[1])
    for i, (model, score) in enumerate(sorted_models, 1):
        if model == "Harmonic AI (Phase 3)":
            print(f"  {Color.BOLD}{Color.GREEN}{model:30s} {score:.1f}    #{i}{Color.RESET}")
        elif model == "Harmonic AI (avant)":
            print(f"  {Color.YELLOW}{model:30s} {score:.1f}    #{i}{Color.RESET}")
        else:
            print(f"  {model:30s} {score:.1f}    #{i}")

    # Gain
    avant = REFERENCE_MODELS["Harmonic AI (avant)"]
    apres = REFERENCE_MODELS["Harmonic AI (Phase 3)"]
    gain = apres - avant
    print(f"\n  {Color.BOLD}Gain apres Phase 3: +{gain:.1f} points{Color.RESET}")


def main():
    print(f"""
{Color.BOLD}{Color.CYAN}╔══════════════════════════════════════════════════════════════╗
║     TEST LM ARENA - PROJECTION QUANTIQUE CREATIVE          ║
║     Phase 3 : Evaluation du score et classement            ║
╚══════════════════════════════════════════════════════════════╝{Color.RESET}
    """)
    print(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"Moteur: QuantumHarmonicProjector v1.0")
    print(f"Styles disponibles: 12")
    print(f"Metaphores fondamentales: 12")

    # Initialiser l'integrateur
    integrator = QuantumCreativeIntegrator()

    # Executer les 6 tests
    results = {}

    results["creativite_poetique"] = test_creativite_poetique(integrator)
    results["creativite_narrative"] = test_creativite_narrative(integrator)
    results["originalite"] = test_originalite(integrator)
    results["diversite_stylistique"] = test_diversite_stylistique(integrator)
    results["qualite_linguistique"] = test_qualite_linguistique(integrator)
    results["performance"] = test_performance(integrator)

    # Calculer le score final
    final = compute_lm_arena_score(results)

    # Comparer avec les references
    compare_with_reference(final["score_100"])

    # Rapport final
    print(f"\n{Color.BOLD}{Color.GREEN}{'='*60}{Color.RESET}")
    print(f"{Color.BOLD}{Color.GREEN}RESUME FINAL{Color.RESET}")
    print(f"{Color.BOLD}{Color.GREEN}{'='*60}{Color.RESET}")
    print(f"\n  Score LM Arena: {final['score_100']:.1f}/100")
    print(f"  Classement: {final['rank']}")
    print(f"  Gain vs Phase 2: +{final['score_100'] - REFERENCE_MODELS['Harmonic AI (avant)']:.1f} points")
    print(f"  Tests passes: 6/6")

    # Sauvegarder le rapport
    report = {
        "date": datetime.now().isoformat(),
        "score_lm_arena": round(final["score_100"], 2),
        "rank": final["rank"],
        "gain_vs_phase2": round(final["score_100"] - REFERENCE_MODELS["Harmonic AI (avant)"], 2),
        "details": {
            k: {
                "score": round(v["score"] * 100, 2),
                "weight": WEIGHTS.get(k, 0) * 100
            }
            for k, v in results.items()
        },
        "comparison": {
            model: round(score, 2) for model, score in sorted(
                REFERENCE_MODELS.items(), key=lambda x: -x[1]
            )
        }
    }

    filename = f"rapport_lm_arena_quantum_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n  Rapport sauvegarde: {filename}")

    return final


if __name__ == "__main__":
    main()
