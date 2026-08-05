# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from word_problem_state import (normalize, _split_sentences, detect_actions,
                                _persons, _PRONOUNS)
from benchmark_gsm8k import load_gsm8k

p = load_gsm8k()[77]
q = normalize(p['question'])
sents = _split_sentences(q)
state = {}
mults = []
rels = []
rates = []
money = 0.0
current_person = None
last_obj = None

for sent in sents:
    acts = detect_actions(sent, last_person=current_person, last_obj=last_obj)
    print('S:', sent[:70])
    for a in acts:
        print('   ', a)
    if not acts:
        continue
    action = acts[0]
    op = action['op']
    person = action.get('person')
    obj = action['obj']
    val = action.get('val', 0.0)
    if person:
        current_person = person
    if obj:
        last_obj = obj
    key = (person, obj) if obj else None
    if op == 'init' and key:
        state[key] = val
    elif op == 'set_mult' and action.get('obj2') is not None:
        mults.append((person, obj, val, action['obj2'], action.get('ref_obj')))
    elif op == 'rel' and action.get('obj'):
        rels.append((person, obj, action.get('ref'), obj,
                     action.get('coeff', 1.0), action.get('delta', 0.0)))
    for extra in acts[1:]:
        eop = extra['op']
        if eop == 'set_mult' and extra.get('obj2'):
            mults.append((extra.get('person'), extra['obj'], extra['val'],
                          extra['obj2'], extra.get('ref_obj')))
        elif eop == 'init' and extra.get('obj'):
            ek = (extra.get('person'), extra['obj'])
            if ek not in state:
                state[ek] = extra['val']

print('state:', state)
print('mults:', mults)
print('rels:', rels)

for _ in range(6):
    progress = False
    for person, obj, val, ref, ref_obj in mults:
        base_obj = ref_obj or obj
        key = (person, obj)
        base = state.get((ref, base_obj), None)
        if base is None and state.get(key) is not None and val != 0:
            state[(ref, base_obj)] = state[key] / val
            progress = True
            continue
        if base is None:
            continue
        if abs(state.get(key, 0.0) - base * val) > 1e-9:
            state[key] = base * val
            progress = True
    for person, obj, ref, ref_obj, coeff, delta in rels:
        b = state.get((ref, ref_obj), None)
        if b is None:
            continue
        akey = (person, obj)
        v = coeff * b + delta
        if abs(state.get(akey, float('inf')) - v) > 1e-9:
            state[akey] = v
            progress = True
    if not progress:
        break
print('état après résolution:', state)
