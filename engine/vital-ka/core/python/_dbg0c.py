# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from benchmark_gsm8k import load_gsm8k
from word_problem_state import normalize

p = load_gsm8k()[0]
print('RAW len:', len(p['question']))
print('RAW:', repr(p['question']))
q = normalize(p['question'])
print('NORM len:', len(q))
print('NORM:', repr(q))
