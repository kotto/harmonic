#!/usr/bin/env python3
"""Évaluation rapide du modèle transvertical V2 sur 2 problèmes."""
import sys, re, torch, time
sys.path.insert(0, 'E:\\SAAS - Copie\\engine')
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel
from codec_binding import encoder_operations_v2, decoder_trames

torch.set_num_threads(1)
t0 = time.time()
tok = AutoTokenizer.from_pretrained('google/flan-t5-small')
base = AutoModelForSeq2SeqLM.from_pretrained('google/flan-t5-small', low_cpu_mem_usage=True)
model = PeftModel.from_pretrained(base, 'data/t5_transvertical_v2/final')
model.eval()
print(f'Chargé en {time.time()-t0:.1f}s')

def ops2seq(pred):
    OM = {'MUL':'MULTIPLY','SUB':'SUBTRACT','ADD':'ADD','DIV':'DIVIDE','INIT':'INIT'}
    ops = []
    for token in pred.replace('\n',' ').split():
        m = re.match(r'(INIT|MUL|SUB|ADD|DIV)\(([^)]+)\)', token.strip())
        if not m: continue
        op, v = m.group(1), m.group(2)
        try: v = float(v)
        except: continue
        mapped = OM.get(op)
        if not mapped: continue
        if mapped=='INIT': ops.append({'op':'INIT','value':v})
        elif mapped=='MULTIPLY': ops.append({'op':'MULTIPLY','multiplier':v})
        elif mapped=='DIVIDE': ops.append({'op':'DIVIDE','divisor':v})
        elif mapped=='SUBTRACT': ops.append({'op':'SUBTRACT','value':v})
        elif mapped=='ADD': ops.append({'op':'ADD','value':v})
    return ops

tests = [
    ('John has 20 apples. He gives 8 away. How many left?', 12.0),
    ('There are 5 boxes. Each box has 12 eggs. How many eggs total?', 60.0),
]

for q, exp in tests:
    t1 = time.time()
    inp = 'translate to operations: ' + q
    inputs = tok(inp, return_tensors='pt', max_length=256, truncation=True)
    with torch.no_grad(): out = model.generate(**inputs, max_new_tokens=64, num_beams=1)
    pred = tok.decode(out[0], skip_special_tokens=True)
    ops = ops2seq(pred)
    got = None
    if ops:
        try: got = decoder_trames(encoder_operations_v2(ops, True, True, False, True))
        except: pass
    good = got is not None and abs(got - exp) < 1e-6
    print(f'{{\"✅\" if good else \"❌\"}} got={got} exp={exp} | {pred[:60]} | {time.time()-t1:.1f}s')

print(f'Total: {time.time()-t0:.1f}s')