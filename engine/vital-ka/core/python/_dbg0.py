# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from word_problem_state import normalize, _split_sentences, detect_actions
from benchmark_gsm8k import load_gsm8k

p = load_gsm8k()[0]
print('Q:', p['question'][:130])
q = normalize(p['question'])
for s in _split_sentences(q):
    print(' S:', s[:110])
    for a in detect_actions(s):
        print('    ', a)
