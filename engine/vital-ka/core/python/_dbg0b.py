# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from word_problem_state import normalize, _split_sentences, detect_actions
from benchmark_gsm8k import load_gsm8k

p = load_gsm8k()[0]
q = normalize(p['question'])
sents = _split_sentences(q)
s2 = sents[1]
print('S2 repr:', repr(s2))
for a in detect_actions(s2):
    print('  action:', a)
