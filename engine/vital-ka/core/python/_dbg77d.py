# -*- coding: utf-8 -*-
import re, sys
sys.stdout.reconfigure(encoding='utf-8')
from benchmark_gsm8k import load_gsm8k
from word_problem_state import normalize, _split_sentences

q = normalize(load_gsm8k()[77]['question'])
q_sent = q
pat = re.compile(
    r'difference in the amount of\s+'
    r'(?:([a-z]+)\s+([a-z]+)\s+and\s+([a-z]+)'
    r'|([a-z]+)\s+and\s+([a-z]+)\s+([a-z]+))')
m = pat.search(q_sent)
print('match:', m.groups() if m else None)
