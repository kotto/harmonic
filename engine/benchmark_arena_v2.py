"""
🌊 Benchmark Arena V2 — 90 questions « arène réelle »
=======================================================

Le benchmark qui mesure ce que les arènes réelles testent :
  30 multi-étapes + 30 code (assertions exécutées) + 30 fluidité.

| Domaine | Source | Vérification |
|---------|--------|--------------|
| Multi-étapes (30) | wave_word_problems.WORD_PROBLEMS | résultat exact |
| Code (30) | wave_algorithms.HUMANEVAL_PROBLEMS | assertions EXÉCUTÉES |
| Fluidité (30) | réponses du pipeline via WaveResponse | phrase FR complète |

Usage :
    python benchmark_arena_v2.py
"""

from __future__ import annotations

import sys
import os
import time
import re
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wave_word_problems import WaveWordProblemEngine, WORD_PROBLEMS
from wave_algorithms import WaveAlgorithmLibrary, HUMANEVAL_PROBLEMS
from wave_pipeline import WavePipeline
from wave_response import WaveResponse


# ═══════════════════════════════════════════════════════════════════════════════
# 1. MULTI-ÉTAPES (30)
# ═══════════════════════════════════════════════════════════════════════════════

def run_multistep(verbose: bool = True) -> Dict:
    engine = WaveWordProblemEngine()
    passed, total = 0, 0
    for question, expected, method in WORD_PROBLEMS[:30]:
        r = engine.solve(question)
        ok = r is not None and abs(r.result - expected) < 1e-6
        passed += ok
        total += 1
        if verbose:
            mark = '✅' if ok else '❌'
            print(f"  {mark} [{method:<16}] {question[:52]:<54} "
                  f"→ {r.result if r else 'AUCUN'}")
    return {'passed': passed, 'total': total,
            'score': 100.0 * passed / total}


# ═══════════════════════════════════════════════════════════════════════════════
# 2. CODE (30) — assertions exécutées
# ═══════════════════════════════════════════════════════════════════════════════

def run_code(verbose: bool = True) -> Dict:
    lib = WaveAlgorithmLibrary()
    results = lib.verify_humaneval()
    names = list(HUMANEVAL_PROBLEMS.keys())[:30]
    passed, total = 0, 0
    for name in names:
        ok, p, t = results.get(name, (False, 0, 0))
        passed += ok
        total += 1
        if verbose:
            mark = '✅' if ok else '❌'
            prob = HUMANEVAL_PROBLEMS[name]
            print(f"  {mark} [{prob['op']:<22}] {prob['description']:<40} "
                  f"assertions {p}/{t}")
    return {'passed': passed, 'total': total,
            'score': 100.0 * passed / total}


# ═══════════════════════════════════════════════════════════════════════════════
# 3. FLUIDITÉ (30) — phrases complètes
# ═══════════════════════════════════════════════════════════════════════════════

FLUENCY_QUESTIONS = [
    "Calcule 2 plus 3 fois 4",
    "racine carrée de 16",
    "combien font 15% de 200",
    "Calcule 2 puissance 10",
    "carré de 12",
    "valeur absolue de -9",
    "la moitié de 18",
    "écris une fonction factorielle",
    "écris une fonction qui calcule le pgcd",
    "génère une fonction fibonacci",
    "implémente une recherche binaire",
    "écris une fonction somme",
    "Un train roule à 80 km/h pendant 3 heures. Quelle distance ?",
    "Marie achète 3 pommes à 2 euros chacune. Combien paie-t-elle ?",
    "Si 3 ouvriers construisent 3 murs en 3 jours, combien de murs 6 ouvriers ?",
    "10 personnes se serrent la main. Combien de poignées ?",
    "Combien de secondes dans 2 heures ?",
    "120 euros partagés entre 4 personnes. Combien chacun ?",
    "Un prix de 50 euros augmente de 10%. Quel est le nouveau prix ?",
    "Un manteau de 120 euros avec 50% de solde. Quel est le prix final ?",
    "Un nénuphar double chaque jour, il couvre l'étang en 48 jours, quand la moitié ?",
    "Qu'est-ce que la lumière ?",
    "Souviens-toi que la Terre tourne autour du Soleil",
    "Quelle est la différence entre l'amour et l'amitié ?",
    "Imagine un mélange entre la pluie et la musique",
    "Échantillonne avec température 0.8 sur la créativité",
    "Évalue la qualité de la réponse : le ciel est bleu",
    "Pourquoi le ciel est-il bleu ?",
    "Si il pleut alors le sol est mouillé. Il pleut. Que conclure ?",
    "Combien font 7 fois 8 ?",
]


def _is_fluent(text: str) -> bool:
    """Une réponse fluide : phrase FR complète, pas un nombre brut."""
    if not text or len(text) < 10:
        return False
    # Ne doit pas être qu'un nombre
    if re.fullmatch(r'[-+]?\d+([.,]\d+)?\s*', text.strip()):
        return False
    # Doit contenir des mots OU une expression mathématique complète ("X × Y = Z")
    words = re.findall(r'[a-zA-Zà-ÿÀ-Ý]+', text)
    if len(words) >= 2:
        return True
    # Expression symbolique : au moins un symbole d'opération + un résultat
    has_op = bool(re.search(r'[+×÷×*/−=-]', text))
    has_num = bool(re.search(r'\d', text))
    return has_op and has_num and len(text) >= 10


def run_fluency(verbose: bool = True) -> Dict:
    pipeline = WavePipeline()
    responder = WaveResponse()
    passed, total = 0, 0
    for q in FLUENCY_QUESTIONS[:30]:
        r = pipeline.run(q)
        resp = responder.synthesize(r)
        ok = _is_fluent(resp)
        passed += ok
        total += 1
        if verbose:
            mark = '✅' if ok else '❌'
            print(f"  {mark} {q[:50]:<52} → {resp[:70]}")
    return {'passed': passed, 'total': total,
            'score': 100.0 * passed / total}


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 65)
    print("  🌊 BENCHMARK ARENA V2 — 90 questions « arène réelle »")
    print("=" * 65)

    verbose = '--quiet' not in sys.argv

    print("\n── 1. MULTI-ÉTAPES (30) ──")
    ms = run_multistep(verbose)
    print("\n── 2. CODE (30) — assertions exécutées ──")
    cd = run_code(verbose)
    print("\n── 3. FLUIDITÉ (30) — phrases complètes ──")
    fl = run_fluency(verbose)

    total_p = ms['passed'] + cd['passed'] + fl['passed']
    total_n = ms['total'] + cd['total'] + fl['total']

    print(f"\n{'═' * 65}")
    print(f"  📊 BILAN ARENA V2")
    print(f"  Multi-étapes : {ms['passed']}/{ms['total']} ({ms['score']:.1f}%)")
    print(f"  Code         : {cd['passed']}/{cd['total']} ({cd['score']:.1f}%)")
    print(f"  Fluidité     : {fl['passed']}/{fl['total']} ({fl['score']:.1f}%)")
    print(f"  GLOBAL       : {total_p}/{total_n} ({100*total_p/total_n:.1f}%)")
    print(f"{'═' * 65}")
