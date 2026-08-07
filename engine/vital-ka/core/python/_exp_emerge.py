# -*- coding: utf-8 -*-
"""Exp 4 — ÉMERGENCE PAS-À-PAS (mécanisme C, sans retrieval de squelette).

Le solveur d'état simule le récit étape par étape : chaque phrase non
interrogative est une ACTION locale sur l'état (init/add/sub/rate/…),
chaque étape est vérifiée, la question finale lit l'état. AUCUNE
récupération de squelette d'un autre problème.

Mesures (mêmes 100 problèmes, leave-one-out sans objet) :
  état seul, état+composés, consensus multi-plans
puis localisation des refus (échantillon d'énoncés non résolus).
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from wave_gsm8k import _extract_final
from benchmark_gsm8k import load_gsm8k
from word_problem_state import (WordProblemStateSolver, solve_consensus,
                                normalize)

problems = load_gsm8k()[:100]
solver = WordProblemStateSolver()


def measure(label, fn, show_refusals=5):
    served = correct = refused = 0
    ex_refus = []
    for p in problems:
        exp = _extract_final(p['answer'])
        if exp is None:
            continue
        v = fn(p['question'])
        if v is None:
            refused += 1
            if len(ex_refus) < show_refusals:
                ex_refus.append(p['question'][:95])
            continue
        served += 1
        if abs(v - exp) < 1e-6:
            correct += 1
    print('%-46s pass@1 %.1f%% (%d) | servies %d | précision servie %.1f%% | refus %d'
          % (label, 100.0 * correct / len(problems), correct, served,
             100.0 * correct / max(1, served), refused))
    if ex_refus:
        print('   refus type :')
        for r in ex_refus:
            print('    -', r)
    return correct, served, refused


print('=== PASS@1 (100) — ÉMERGENCE PAS-À-PAS (aucun retrieval) ===')
c1, s1, r1 = measure('état seul (simulation)',
                     lambda q: (lambda r: r[0] if r else None)(
                         solver.solve(q, use_compounds=False)))
c2, s2, r2 = measure('état + motifs composés',
                     lambda q: (lambda r: r[0] if r else None)(
                         solver.solve(q, use_compounds=True)))
c3, s3, r3 = measure('consensus multi-plans (vote 3 stratégies)',
                     lambda q: (lambda r: r[0] if r else None)(
                         solve_consensus(q)))

# ── Localisation : où les phrases échappent au détecteur d'actions ──────────
print('\n=== LOCALISATION des refus ===')
no_action = no_read = 0
ex_no_action = []
for p in problems:
    q = normalize(p['question'])
    if solver.solve(q, use_compounds=True) is not None:
        continue
    from word_problem_state import _split_sentences, detect_action
    acted = sum(1 for s in _split_sentences(q)
                if not __import__('re').search(
                    r'\b(how many|how much|what is|what are)\b', s)
                and detect_action(s) is not None)
    if acted == 0:
        no_action += 1
        if len(ex_no_action) < 5:
            ex_no_action.append(p['question'][:95])
    else:
        no_read += 1
print('refus avec 0 phrase actionnée : %d | avec actions mais question illisible : %d'
      % (no_action, no_read))
for r in ex_no_action:
    print('   -', r)
