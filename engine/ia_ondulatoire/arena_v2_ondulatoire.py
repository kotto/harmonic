# -*- coding: utf-8 -*-
"""
arena_v2_ondulatoire.py — Benchmark Arena V2 (90 questions) sur le moteur
ondulatoire natif (ia_ondulatoire).

Volts :
  1. Multi-étapes (30) — les WORD_PROBLEMS du WaveWordProblemEngine,
     résolus par notre GSM8KOndulatoire (0 LLM)
  2. Fluidité (30)    — les FLUENCY_QUESTIONS, réponses du cerveau
     IaOndulatoire (phrases FR complètes)
  3. Code (30)        — HORS PÉRIMÈTRE : notre moteur génère des programmes
     ONDULATOIRES (pas du Python exécutable) — la génération de code reste à
     l'ancien écosystème (WaveAlgorithmLibrary). Documenté, non compté.

Usage : python arena_v2_ondulatoire.py
"""

from __future__ import annotations

import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if racine not in sys.path:
    sys.path.insert(0, racine)

from gsm8k import GSM8KOndulatoire          # noqa: E402
from cerveau import IaOndulatoire           # noqa: E402


def _is_fluent(text: str) -> bool:
    """Une réponse fluide : phrase FR complète, pas un nombre brut."""
    if not text or len(text) < 10:
        return False
    if re.fullmatch(r"[-+]?\d+([.,]\d+)?\s*", text.strip()):
        return False
    words = re.findall(r"[a-zA-Zà-ÿÀ-Ý]+", text)
    if len(words) >= 2:
        return True
    has_op = bool(re.search(r"[+×÷×*/−=-]", text))
    has_num = bool(re.search(r"\d", text))
    return has_op and has_num and len(text) >= 10


FLUENCY_QUESTIONS = [
    "Calcule 2 plus 3 fois 4", "racine carrée de 16", "combien font 15% de 200",
    "Calcule 2 puissance 10", "carré de 12", "valeur absolue de -9",
    "la moitié de 18", "écris une fonction factorielle",
    "écris une fonction qui calcule le pgcd", "génère une fonction fibonacci",
    "implémente une recherche binaire", "écris une fonction somme",
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


def multistep(verbose: bool = True) -> dict:
    from wave_word_problems import WORD_PROBLEMS
    s = GSM8KOndulatoire()
    passed = total = 0
    for question, expected, method in WORD_PROBLEMS:
        r = s.resoudre(question)
        ok = r["reponse_num"] is not None and abs(r["reponse_num"] - expected) < 1e-6
        passed += ok
        total += 1
        if verbose:
            mark = "✅" if ok else "❌"
            print(f"  {mark} [{method:<16}] {question[:48]:<50} → {r['reponse']}")
    return {"passed": passed, "total": total, "score": 100.0 * passed / total}


def fluidite(verbose: bool = True) -> dict:
    ia = IaOndulatoire(charger=False)
    passed = total = 0
    for q in FLUENCY_QUESTIONS:
        r = ia.poser(q)
        rep = r["response"]
        ok = _is_fluent(rep)
        passed += ok
        total += 1
        if verbose:
            mark = "✅" if ok else "❌"
            print(f"  {mark} {q[:44]:<46} → {rep[:55]}")
    return {"passed": passed, "total": total, "score": 100.0 * passed / total}


def principal() -> None:
    print("═" * 64)
    print("🌊 BENCHMARK ARENA V2 — moteur ondulatoire natif")
    print("═" * 64)
    t0 = time.time()
    m = multistep()
    print(f"  1. Multi-étapes (30) : {m['passed']}/{m['total']} "
          f"({m['score']:.1f} %) — GSM8KOndulatoire 0-LLM")
    print()
    f = fluidite()
    print(f"  2. Fluidité (30) : {f['passed']}/{f['total']} ({f['score']:.1f} %) "
          f"— IaOndulatoire")
    print()
    print("  3. Code (30) : NON COUVERT — le moteur génère des programmes")
    print("     ondulatoires, pas du Python exécutable (ancien écosystème)")
    print("═" * 64)
    print(f"  TOTAL : {m['passed'] + f['passed']}/60 · {time.time()-t0:.1f} s")
    print("═" * 64)


if __name__ == "__main__":
    principal()
