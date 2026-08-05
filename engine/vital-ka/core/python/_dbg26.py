# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from word_problem_state import WordProblemStateSolver, normalize, _split_sentences
from benchmark_gsm8k import load_gsm8k

p = load_gsm8k()[26]
print('Q:', p['question'][:120])
q = normalize(p['question'])
r = WordProblemStateSolver().solve(q, use_compounds=True)
print('RÉSULTAT:', r)
print()
for s in _split_sentences(q):
    from word_problem_state import detect_actions
    print('  S:', s[:90])
    for a in detect_actions(s):
        print('     ', a)
