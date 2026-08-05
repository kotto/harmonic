# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from word_problem_state import (WordProblemStateSolver, normalize)
from benchmark_gsm8k import load_gsm8k

p = load_gsm8k()[77]
q = normalize(p['question'])
r = WordProblemStateSolver().solve(q, use_compounds=True)
print('RESULT:', r)
# essai sans composés
r2 = WordProblemStateSolver().solve(q, use_compounds=False)
print('sans composés:', r2)
