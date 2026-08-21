#!/usr/bin/env python3
"""Post-processing du modèle transvertical V2 + évaluation rapide."""
import sys, re, torch
sys.path.insert(0, 'E:\\SAAS - Copie\\engine')
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel
from codec_binding import encoder_operations_v2, decoder_trames

NUM_RE = re.compile(r'(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s*(%)?', re.IGNORECASE)

def extraire_pcts(question):
    """Extrait les pourcentages du texte : 60% -> 0.6"""
    pcts = []
    for m in NUM_RE.finditer(question):
        if m.group(2):
            pcts.append(float(m.group(1).replace(',', '')) / 100.0)
    return pcts

def ops2seq_post(pred, question):
    """Parse la prédiction avec post-processing :
    1. Garde les 2 premières ops
    2. Convertit les pourcentages
    """
    OM = {'MUL':'MULTIPLY','SUB':'SUBTRACT','ADD':'ADD','DIV':'DIVIDE','INIT':'INIT'}
    pcts = extraire_pcts(question)
    ops = []
    count = 0
    for token in pred.replace('\n',' ').split():
        if count >= 2: break
        m = re.match(r'(INIT|MUL|SUB|ADD|DIV)\(([^)]+)\)', token.strip())
        if not m: continue
        op, v = m.group(1), m.group(2)
        try: v = float(v)
        except: continue
        
        # Conversion pourcentage : si la valeur match un % dans le texte
        for pct in pcts:
            if abs(v - pct * 100) < 1e-6:  # 60 dans le texte, 0.6 dans l'op ?
                v = pct
                if op in ('SUB', 'ADD'):
                    op = 'MUL'  # "60% de" = MUL(0.6)
                break
        
        mapped = OM.get(op)
        if not mapped: continue
        count += 1
        if mapped=='INIT': ops.append({'op':'INIT','value':v})
        elif mapped=='MULTIPLY': ops.append({'op':'MULTIPLY','multiplier':v})
        elif mapped=='DIVIDE': ops.append({'op':'DIVIDE','divisor':v})
        elif mapped=='SUBTRACT': ops.append({'op':'SUBTRACT','value':v})
        elif mapped=='ADD': ops.append({'op':'ADD','value':v})
    return ops

# Charger le modèle
print('Chargement du modèle transvertical V2...')
tok = AutoTokenizer.from_pretrained('google/flan-t5-small')
base = AutoModelForSeq2SeqLM.from_pretrained('google/flan-t5-small', low_cpu_mem_usage=True)
model = PeftModel.from_pretrained(base, 'data/t5_transvertical_v2/final')
model.eval()
print('✓ Modèle chargé')

tests = [
    ('John has 20 apples. He gives 8 away. How many left?', 12.0),
    ('There are 5 boxes. Each box has 12 eggs. How many eggs total?', 60.0),
    ('A baker makes 30 croissants. She sells 12. How many remain?', 18.0),
    ('A store has 150 customers. 60% buy something. How many buy?', 90.0),
    ('A train travels 10 miles per hour for 3 hours. How far does it go?', 30.0),
    ('John has 500 dollars. He spends 20% on clothes. How much does he spend?', 100.0),
    ('A pizza has 8 slices. 3 people share it equally. How many slices each?', 8/3),
    ('A recipe needs 6 cups. Each cup weighs 120 grams. How many grams?', 720.0),
    ('A farmer has 48 apples. He puts them in bags of 6. How many bags?', 8.0),
    ('A store had 200 customers. 120 bought something. How many did not buy?', 80.0),
]

ok = 0
for q, exp in tests:
    inp = 'translate to operations: ' + q
    inputs = tok(inp, return_tensors='pt', max_length=256, truncation=True)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=64, num_beams=1)
    pred = tok.decode(out[0], skip_special_tokens=True)
    ops = ops2seq_post(pred, q)
    got = None
    if ops:
        try: got = decoder_trames(encoder_operations_v2(ops, True, True, False, True))
        except: pass
    good = got is not None and abs(got - exp) < 1e-6
    ok += good
    print(f'  {"✅" if good else "❌"} got={got:.2f} exp={exp:.2f} | {[o["op"] for o in ops]} | {pred[:60]}')

print(f'\nScore : {ok}/{len(tests)}')