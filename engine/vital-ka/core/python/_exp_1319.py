# -*- coding: utf-8 -*-
"""Axe 1 — VALIDATION sur les 1319 + anti-sur-apprentissage.

Le solveur d'état est SANS mémoire (0 paramètre, 0 retrieval) : le
leave-one-out « par famille » devient :

  1. pass@1 GLOBAL sur les 1319 (état + composés, consensus).
  2. SUR-APPRENTISSAGE : 100 premiers (réglage) vs 1219 suivants
     (jamais vus) — les motifs composés ont-ils été calés sur les 100 ?
  3. CONCENTRATION : les corrects viennent-ils de peu de squelettes
     (motifs sur-appris) ou sont-ils répartis structurellement ?
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from collections import Counter

from benchmark_gsm8k import load_gsm8k
from wave_gsm8k import _extract_final, GSM8KChainMemory
from word_problem_state import WordProblemStateSolver, solve_consensus

problems = load_gsm8k()
N = len(problems)
print('total problèmes :', N)

solver = WordProblemStateSolver()


def measure(label, fn, idxs):
    served = correct = refused = 0
    for i in idxs:
        exp = _extract_final(problems[i]['answer'])
        if exp is None:
            continue
        v = fn(problems[i]['question'])
        if v is None:
            refused += 1
            continue
        served += 1
        if abs(v - exp) < 1e-6:
            correct += 1
    n = max(1, len(idxs))
    print('%-44s pass@1 %.1f%% (%d) | servies %d | précision %.1f%% | refus %d'
          % (label, 100.0 * correct / n, correct, served,
             100.0 * correct / max(1, served), refused))
    return correct


def solve(q):
    r = solver.solve(q, use_compounds=True)
    return r[0] if r else None


def consensus(q):
    r = solve_consensus(q)
    return r[0] if r else None


all_idxs = list(range(N))
tune = list(range(100))
unseen = list(range(100, N))

print('\n=== 1. GLOBAL 1319 ===')
measure('état + composés [1319]', solve, all_idxs)

print('\n=== 2. SUR-APPRENTISSAGE (100 réglés vs 1219 jamais vus) ===')
measure('état + composés [100 réglés]', solve, tune)
measure('état + composés [1219 jamais vus]', solve, unseen)

print('\n=== 3. CONCENTRATION par squelette (corrects sur 1319) ===')
mem = GSM8KChainMemory()
mem.load()
correct_skeletons = Counter()
correct_by_person = Counter()
for i in all_idxs:
    exp = _extract_final(problems[i]['answer'])
    if exp is None:
        continue
    v = solve(problems[i]['question'])
    if v is not None and abs(v - exp) < 1e-6:
        sk = mem.patterns[i]['chain'].skeleton
        correct_skeletons[sk] += 1
print('squelettes distincts parmi les corrects : %d / %d corrects'
      % (len(correct_skeletons), sum(correct_skeletons.values())))
print('top squelettes des corrects :')
for sk, c in correct_skeletons.most_common(8):
    print('   %2d×  %s' % (c, sk[:70]))
