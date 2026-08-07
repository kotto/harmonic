# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from word_problem_state import WordProblemStateSolver, normalize
from benchmark_gsm8k import load_gsm8k

p = load_gsm8k()[0]
q = normalize(p['question'])
r = WordProblemStateSolver().solve(q, use_compounds=True)
print('RÉSULTAT:', r)
