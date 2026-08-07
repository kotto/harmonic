# -*- coding: utf-8 -*-
"""Axe 2 — ÉMERGENCE PAS-À-PAS : solveur d'état en LOO strict sur les 1319.

Le solveur d'état est le candidat 0 paramètre / 0 retrieval. Il n'a
jamais été mesuré proprement sur les 1319 (seulement les 100 réglés :
15 % mais sur-apprentissage, et 19 corrects en pass@1 partiel).

Mêmes métriques que la mémoire (Axe 1b, 1.4 % / 19 corrects) :
  - ÉTAT PUR  : WordProblemStateSolver().solve(use_compounds=False)
                — l'émergence pas-à-pas, sans motifs composés ni vote.
  - CONSENSUS : solve_consensus() — état + composés + directe, vote.
"""
import sys
import time
sys.stdout.reconfigure(encoding='utf-8')

from benchmark_gsm8k import load_gsm8k
from wave_gsm8k import _extract_final
from word_problem_state import WordProblemStateSolver, solve_consensus

problems = load_gsm8k()
N = len(problems)
print('total :', N)
t0 = time.time()

solver = WordProblemStateSolver()


def mesure(nom, fn):
    served = correct = refused = 0
    t = time.time()
    for i, p in enumerate(problems):
        exp = _extract_final(p['answer'])
        if exp is None:
            continue
        v = fn(p['question'])
        if v is None:
            refused += 1
            continue
        served += 1
        if abs(v[0] - exp) < 1e-6:
            correct += 1
    print('%s : pass@1 %.1f%% (%d) | servies %d | précision servie %.1f%% '
          '| refus %d | (%.0f s)'
          % (nom, 100.0 * correct / N, correct, served,
             100.0 * correct / max(1, served), refused, time.time() - t))
    return correct


mesure('ÉTAT PUR  ', lambda q: solver.solve(q, use_compounds=False))
mesure('CONSENSUS ', solve_consensus)
print('durée totale : %.0f s' % (time.time() - t0))
