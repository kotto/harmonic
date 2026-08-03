"""
🌊 Benchmark Raisonnement — Les 7 types émergents, mesurés
=============================================================

Le gap raisonnement (1% annoncé, non mesurable) devient mesurable :
30 questions vérifiables par mot-clé dans la conclusion.

| Type | Questions | Vérification |
|------|-----------|--------------|
| Syllogisme | 6 | la conclusion contient le prédicat attendu |
| Modus Ponens | 5 | la conclusion contient la conséquence |
| Transitivité | 5 | la conclusion relie le 1er sujet au dernier objet |
| Contradiction | 4 | méthode == 'contradiction' |
| Induction | 4 | méthode == 'induction' et pattern trouvé |
| Abduction | 4 | la cause attendue est choisie |
| Analogie | 2 | méthode == 'analogie' (détection) |

Usage :
    python benchmark_raisonnement.py
"""

from __future__ import annotations

import sys
import os
import time
from typing import List, Dict, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wave_reasoning_v2 import WaveReasoningEngine


# ═══════════════════════════════════════════════════════════════════════════════
# LES 30 QUESTIONS
# ═══════════════════════════════════════════════════════════════════════════════

# (prémisses, question, type attendu, mot-clé attendu dans la conclusion)
RAISONNEMENT_TESTS: List[Tuple[List[str], str, str, str]] = [
    # ── Syllogismes (6) ──
    (["Socrate est un homme", "Tous les hommes sont mortels"], "",
     "syllogisme", "mortel"),
    (["Rex est un chien", "Tous les chiens aboient"], "",
     "syllogisme", "aboie"),
    (["Titi est un oiseau", "Tous les oiseaux ont des plumes"], "",
     "syllogisme", "plume"),
    (["Tom est un chat", "Tous les chats aiment le poisson"], "",
     "syllogisme", "poisson"),
    (["Paris est une ville", "Toutes les villes ont des habitants"], "",
     "syllogisme", "habitant"),
    (["Platon est un philosophe", "Tous les philosophes aiment la sagesse"], "",
     "syllogisme", "sagesse"),
    # ── Modus Ponens (5) ──
    (["Si il pleut alors le sol est mouillé", "il pleut"], "",
     "modus_ponens", "mouillé"),
    (["Si on appuie sur le bouton alors la lumière s'allume", "on appuie sur le bouton"], "",
     "modus_ponens", "s'allume"),
    (["Si l'eau gèle alors elle devient solide", "l'eau gèle"], "",
     "modus_ponens", "solide"),
    (["Si on étudie alors on réussit", "on étudie"], "",
     "modus_ponens", "réussit"),
    (["Si le feu brûle alors il y a de la fumée", "le feu brûle"], "",
     "modus_ponens", "fumée"),
    # ── Transitivité (5) ──
    (["Alice est la mère de Bob", "Bob est le père de Claire"], "",
     "transitivite", "claire"),
    (["Le chat est plus grand que la souris", "la souris est plus grande que la fourmi"], "",
     "transitivite", "fourmi"),
    (["A est avant B", "B est avant C"], "",
     "transitivite", "c"),
    (["X est lié à Y", "Y est lié à Z"], "",
     "transitivite", "z"),
    (["La terre tourne autour du soleil", "le soleil est au centre du système"], "",
     "transitivite", "système"),
    # ── Contradictions (4) ──
    (["le ciel est bleu", "le ciel n'est pas bleu"], "",
     "contradiction", ""),
    (["la terre est ronde", "la terre n'est pas ronde"], "",
     "contradiction", ""),
    (["l'eau bout à 100 degrés", "l'eau ne bout pas à 100 degrés"], "",
     "contradiction", ""),
    (["le chat est un animal", "le chat n'est pas un animal"], "",
     "contradiction", ""),
    # ── Inductions (4) ──
    (["le corbeau 1 est noir", "le corbeau 2 est noir", "le corbeau 3 est noir"], "",
     "induction", "corbeau"),
    (["le cygne 1 est blanc", "le cygne 2 est blanc", "le cygne 3 est blanc"], "",
     "induction", "cygne"),
    (["la voiture 1 roule", "la voiture 2 roule", "la voiture 3 roule"], "",
     "induction", "voiture"),
    (["l'oiseau 1 vole", "l'oiseau 2 vole", "l'oiseau 3 vole"], "",
     "induction", "oiseau"),
    # ── Abductions (4) ──
    (["le sol est mouillé"], "Pourquoi le sol est-il mouillé ?",
     "abduction", "plu"),
    (["il y a de la fumée"], "Pourquoi y a-t-il de la fumée ?",
     "abduction", "feu"),
    (["la route est enneigée"], "Pourquoi la route est-elle enneigée ?",
     "abduction", "neig"),
    (["le verre est cassé"], "Pourquoi le verre est-il cassé ?",
     "abduction", "tomb"),
    # ── Analogies (2, détection de méthode) ──
    (["roue est à vélo", "voile est à bateau"],
     "roue est à vélo ce que voile est à ?", "analogie", "bateau"),
    (["aile est à oiseau", "nageoire est à poisson"],
     "aile est à oiseau ce que nageoire est à ?", "analogie", "poisson"),
]

# Hypothèses d'abduction (causes candidates)
ABDUCTION_HYPOTHESES: Dict[str, List[str]] = {
    "le sol est mouillé": ["il a plu toute la nuit",
                           "un arroseur automatique fonctionne",
                           "on a lavé la voiture devant la maison"],
    "il y a de la fumée": ["un feu de cheminée brûle",
                           "quelqu'un fume à côté",
                           "la voisine fait griller de la viande"],
    "la route est enneigée": ["il a neigé cette nuit",
                              "un camion a renversé de la farine",
                              "des travaux ont laissé du gravier"],
    "le verre est cassé": ["quelque chose est tombé dessus",
                           "le chat a sauté sur la table",
                           "le verre était trop fragile"],
}


# ═══════════════════════════════════════════════════════════════════════════════
# EXÉCUTION
# ═══════════════════════════════════════════════════════════════════════════════

def run_benchmark(verbose: bool = True) -> Dict:
    """Exécute le benchmark de raisonnement."""
    engine = WaveReasoningEngine()
    results = []
    t0 = time.perf_counter()

    for premises, question, expected_type, keyword in RAISONNEMENT_TESTS:
        # Abduction : fournir les hypothèses
        if expected_type == 'abduction':
            hypotheses = ABDUCTION_HYPOTHESES.get(premises[0], [])
            r = engine.abduction(premises[0], hypotheses)
        else:
            r = engine.solve(premises, question)

        # Vérification
        ok = False
        if expected_type == 'abduction':
            ok = (keyword in r.conclusion.lower() or
                  any(keyword in h for h in
                      ABDUCTION_HYPOTHESES.get(premises[0], [])
                      if h in r.conclusion.lower()))
        elif expected_type == 'analogie':
            ok = r.method == 'analogie'
        elif expected_type == 'contradiction':
            ok = r.method == 'contradiction'
        elif expected_type == 'induction':
            ok = r.method == 'induction' and keyword in r.conclusion.lower()
        else:
            # Types structurés : la superposition n'est pas une inférence
            ok = (keyword in r.conclusion.lower() and
                  r.method != 'superposition')

        results.append((premises, expected_type, r, ok))

        if verbose:
            mark = '✅' if ok else '❌'
            print(f"  {mark} [{expected_type:<13}] "
                  f"{premises[0][:35]:<38} → {r.conclusion[:45]}")

    elapsed = (time.perf_counter() - t0) * 1000
    passed = sum(1 for _, _, _, ok in results if ok)
    total = len(results)

    # Par type
    by_type: Dict[str, Tuple[int, int]] = {}
    for premises, etype, r, ok in results:
        t, n = by_type.get(etype, (0, 0))
        by_type[etype] = (t + (1 if ok else 0), n + 1)

    return {
        'passed': passed,
        'total': total,
        'score': 100.0 * passed / total,
        'time_ms': elapsed,
        'by_type': {k: f"{v[0]}/{v[1]}" for k, v in by_type.items()},
    }


if __name__ == "__main__":
    print("=" * 65)
    print("  🌊 BENCHMARK RAISONNEMENT — Les 7 types émergents")
    print("=" * 65)
    print()

    stats = run_benchmark(verbose=True)

    print(f"\n{'─' * 65}")
    print(f"  📊 SCORE : {stats['passed']}/{stats['total']} "
          f"({stats['score']:.1f}%) — {stats['time_ms']:.1f} ms")
    print(f"  Par type : {stats['by_type']}")
    print("=" * 65)
