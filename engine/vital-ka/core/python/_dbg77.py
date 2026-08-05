# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from word_problem_state import (normalize, _split_sentences, detect_actions,
                                _persons, _clean_obj)
from benchmark_gsm8k import load_gsm8k

p = load_gsm8k()[77]
q = normalize(p['question'])
print('Q:', repr(q))
sents = _split_sentences(q)
print('nb phrases:', len(sents))
for s in sents:
    print(' S:', repr(s[:90]))
    for a in detect_actions(s):
        print('    ', a)
print('persons:', _persons(q))
