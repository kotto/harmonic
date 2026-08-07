# -*- coding: utf-8 -*-
"""Axe 5 — DIAGNOSTIC de la structuration : où échoue le solveur d'état ?

Classifie les 1319 en correct / faux / refusé (état seul, 0 composés),
puis échantillonne les échecs pour cibler le parser à slots :
  - Refus : aucun pattern ne tire, ou pas de valeur finale.
  - Faux  : un pattern tire mais la valeur servie est fausse.
"""
import sys
import time
sys.stdout.reconfigure(encoding='utf-8')

from benchmark_gsm8k import load_gsm8k
from wave_gsm8k import _extract_final
from word_problem_state import WordProblemStateSolver, _split_sentences, detect_actions

problems = load_gsm8k()
N = len(problems)
print('total :', N)
t0 = time.time()

solver = WordProblemStateSolver()
stats = {'correct': [], 'wrong': [], 'refused': []}
for i, p in enumerate(problems):
    exp = _extract_final(p['answer'])
    if exp is None:
        continue
    r = solver.solve(p['question'], use_compounds=False)
    if r is None:
        stats['refused'].append(i)
    elif abs(r[0] - exp) < 1e-6:
        stats['correct'].append(i)
    else:
        stats['wrong'].append(i)

print('CORRECT : %d | FAUX : %d | REFUSÉ : %d (%.0f s)'
      % (len(stats['correct']), len(stats['wrong']), len(stats['refused']),
         time.time() - t0))

# ── Refus : y a-t-il au moins UNE action détectée par phrase ? ───────────────
no_act = no_final = 0
examples = []
for i in stats['refused']:
    acts_total = 0
    for sent in _split_sentences(problems[i]['question']):
        acts_total += len(detect_actions(sent))
    if acts_total == 0:
        no_act += 1
    else:
        no_final += 1
        if len(examples) < 12:
            examples.append((i, acts_total))
print('REFUS : aucune action détectée : %d | actions oui mais pas de valeur : %d'
      % (no_act, no_final))
print('  Échantillon (actions détectées mais refus) :')
for i, n_act in examples:
    print('  [%d] %d actions | attente=%s' % (i, n_act,
          _extract_final(problems[i]['answer'])))
    print('      %s' % problems[i]['question'][:140])

# ── Faux : la valeur servie est-elle un nombre de l'énoncé ? ─────────────────
import re
num_in_q = 0
ex_wrong = []
for i in stats['wrong']:
    q = problems[i]['question'].lower()
    nums = set(float(m.group(0).replace(',', '')) for m in
               re.finditer(r'\d+(?:[.,]\d+)?', q))
    r = solver.solve(problems[i]['question'], use_compounds=False)
    if r is None:
        continue
    v = r[0]
    if any(abs(v - n) < 1e-6 for n in nums):
        num_in_q += 1
    if len(ex_wrong) < 10:
        ex_wrong.append((i, v, _extract_final(problems[i]['answer'])))
print()
print('FAUX : valeur servie = un nombre de l’énoncé (motif sur-tiré) : %d/%d'
      % (num_in_q, len(stats['wrong'])))
print('  Échantillon :')
for i, v, e in ex_wrong:
    print('  [%d] servi=%s attente=%s' % (i, v, e))
    print('      %s' % problems[i]['question'][:140])
print('durée totale : %.0f s' % (time.time() - t0))
