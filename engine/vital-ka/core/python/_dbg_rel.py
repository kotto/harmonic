# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from word_problem_state import WordProblemStateSolver, normalize, _split_sentences, detect_actions
from benchmark_gsm8k import load_gsm8k

for idx in (40, 77, 82, 91, 34):
    p = load_gsm8k()[idx]
    q = normalize(p['question'])
    r = WordProblemStateSolver().solve(q, use_compounds=True)
    print(f'--- #{idx} {p["question"][:75]}')
    print('    RES:', r)
    for s in _split_sentences(q):
        acts = detect_actions(s)
        if acts:
            print('    ', s[:70], '→', [(a['op'], a.get('obj'), a.get('val'),
                                        a.get('coeff'), a.get('delta'), a.get('ref'))
                                       for a in acts])
