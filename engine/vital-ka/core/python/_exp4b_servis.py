# -*- coding: utf-8 -*-
"""Exp 4b — les problèmes NOUVELLEMENT servis et leur écart vs attendu."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from benchmark_gsm8k import load_gsm8k
from word_problem_state import WordProblemStateSolver, solve_consensus, normalize
from wave_gsm8k import _extract_final

solver = WordProblemStateSolver()
problems = load_gsm8k()[:100]

print('=== Servis (état+composés) — valeur vs attendu ===')
for idx, p in enumerate(problems):
    exp = _extract_final(p['answer'])
    if exp is None:
        continue
    q = normalize(p['question'])
    r = solver.solve(q, use_compounds=True)
    if r is None:
        continue
    ok = abs(r[0] - exp) < 1e-6
    print(f"{'OK ' if ok else 'FAUX'} #{idx} got={r[0]:<10} exp={exp:<10} {p['question'][:80]}")
