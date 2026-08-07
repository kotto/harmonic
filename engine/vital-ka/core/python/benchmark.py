"""
Benchmark Harmonic AI
=====================
Mesure la qualité du modèle sur 20 questions réparties en 4 catégories :
  - FACTUEL : réponses exactes attendues
  - RAISONNEMENT : chaînes logiques
  - CRÉATIVITÉ : métaphores et connexions
  - MULTILINGUE : questions en anglais

Usage: python benchmark.py
"""

import sys, os, time, json
from pathlib import Path
from typing import List, Dict, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harmonic_ai import HarmonicAI

# ═══════════════════════════════════════════════════════════════════
# QUESTIONS DE TEST
# ═══════════════════════════════════════════════════════════════════

BENCHMARK = {
    "factuel": [
        ("explique la lumiere", ["onde", "electromagnetique", "photons"]),
        ("qu est ce que la relativite", ["einstein", "gravitation", "espace"]),
        ("qu est ce que la gravite", ["courbure", "espace", "masse"]),
        ("explique la resonance", ["frequence", "amplifie", "ondes"]),
        ("qu est ce que la conscience", ["perception", "soi", "monde"]),
    ],
    "raisonnement": [
        ("pourquoi le coeur pompe le sang", ["sang", "oxygene", "organes"]),
        ("comment fonctionne la photosynthese", ["lumiere", "energie", "plante"]),
        ("pourquoi la terre est ronde", ["gravite", "planete", "forme"]),
    ],
    "creativite": [
        ("genere 3 metaphores", "metaphor"),
        ("genere un haiku", "haiku"),
        ("genere 3 connexions creatives", "create"),
    ],
    "multilingue": [
        ("what is light", ["wave", "electromagnetic", "photons"]),
        ("who discovered relativity", ["einstein", "gravitation"]),
        ("explain gravity", ["curvature", "spacetime", "mass"]),
    ],
}


def benchmark():
    print("=" * 60)
    print("HARMONIC AI — BENCHMARK")
    print("=" * 60)
    
    ai = HarmonicAI(use_memory=False)
    print(f"\nBase: {ai.stats['faits']} faits, {ai.stats['vocabulaire']} mots\n")
    
    results = {}
    total_score = 0
    total_tests = 0
    t0 = time.time()
    
    for category, tests in BENCHMARK.items():
        print(f"\n{'─' * 50}")
        print(f"  {category.upper()}")
        print(f"{'─' * 50}")
        cat_score = 0
        
        for test in tests:
            if category == "creativite":
                # Tests de créativité (qualitatifs)
                name, method = test
                if method == "metaphor":
                    result = ai.metaphor(3)
                    if result and len(result) > 0:
                        score = 1.0 if len(result) >= 2 else 0.5
                        print(f"  ✨ Métaphores ({len(result)}): {result[0][:80]}...")
                    else:
                        score = 0.3
                        print(f"  ✨ Métaphores: aucune générée")
                elif method == "haiku":
                    result = ai.haiku()
                    score = 1.0 if len(result) > 20 else 0.5
                    print(f"  🎯 Haïku: {result[:80]}")
                elif method == "create":
                    result = ai.create(3)
                    if result and len(result) > 0:
                        score = 1.0 if len(result) >= 2 else 0.5
                        print(f"  💡 Créations ({len(result)}): {result[0][:80]}..." if result else "  ❌ Aucune")
                    else:
                        score = 0.3
                        print(f"  💡 Créations: aucune")
                cat_score += score
                total_tests += 1
            else:
                # Tests factuels et raisonnement
                question, expected_keywords = test[0], test[1]
                response = ai.ask(question) if category != "raisonnement" else ai.reason(question)
                
                # Score basé sur la présence des mots-clés attendus
                found = sum(1 for kw in expected_keywords if kw.lower() in response.lower())
                score = found / len(expected_keywords)
                
                status = "✅" if score >= 0.6 else ("⚠️" if score >= 0.3 else "❌")
                print(f"  {status} {question[:50]:50s} | {found}/{len(expected_keywords)} mots | {response[:60]}...")
                
                cat_score += score
                total_tests += 1
        
        avg = cat_score / len(tests) * 100
        results[category] = round(avg, 1)
        print(f"  → {category}: {avg:.0f}%")
        total_score += cat_score
    
    elapsed = time.time() - t0
    
    print(f"\n{'=' * 60}")
    print(f"RÉSULTATS")
    print(f"{'=' * 60}")
    for cat, score in results.items():
        bar = "█" * int(score / 5) + "░" * (20 - int(score / 5))
        print(f"  {cat:15s} {bar} {score:.0f}%")
    
    overall = total_score / total_tests * 100
    print(f"\n  SCORE GLOBAL : {overall:.0f}%")
    print(f"  Temps total  : {elapsed:.1f}s")
    print(f"  Faits        : {ai.stats['faits']}")
    print(f"  Vocabulaire  : {ai.stats['vocabulaire']}")
    print(f"{'=' * 60}")
    
    return results


if __name__ == '__main__':
    benchmark()
