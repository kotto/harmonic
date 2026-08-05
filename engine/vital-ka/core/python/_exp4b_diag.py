# -*- coding: utf-8 -*-
"""Diagnostic Exp 4b — phrases non actionnées des problèmes refusés."""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

from benchmark_gsm8k import load_gsm8k
from word_problem_state import (WordProblemStateSolver, normalize,
                                _split_sentences, detect_action)

solver = WordProblemStateSolver()
problems = load_gsm8k()[:100]

for idx, p in enumerate(problems):
    q = normalize(p['question'])
    if solver.solve(q, use_compounds=True) is not None:
        continue
    print(f'--- #{idx} {p["question"][:100]}')
    for s in _split_sentences(q):
        if re.search(r'\b(how many|how much|what is|what are|what was|what did|how far|how long|how old)\b', s):
            print(f'   [Q] {s}')
        elif detect_action(s) is None:
            print(f'   [?] {s}')
