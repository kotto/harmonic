# -*- coding: utf-8 -*-
"""Vérification ciblée des 2 nouveaux templates (indices du diagnostic)."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from benchmark_gsm8k import load_gsm8k
from wave_gsm8k import _extract_final
from word_problem_state import WordProblemStateSolver

problems = load_gsm8k()
solver = WordProblemStateSolver()
for i in (6, 33):
    q = problems[i]['question']
    exp = _extract_final(problems[i]['answer'])
    r = solver.solve(q, use_compounds=False)
    print('[%d] attente=%s' % (i, exp))
    print('    %s' % q)
    if r is None:
        print('    → REFUS')
    else:
        print('    → %s | %s' % (r[0], ' | '.join(r[1][-2:])))
