import sys, re, torch, numpy as np
sys.path.insert(0, 'E:\\SAAS - Copie\\engine')
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel

NUM_RE = re.compile(r'(\d+(?:\.\d+)?)\s*(%)?', re.IGNORECASE)

# Tester le contexte
q = 'John invited 20 people. Each will eat 2 hot dogs. He already has 4 left over. Packs contain 6 and cost 2 each.'
nums = [(m.start(), m.group(1), m.group(2)) for m in NUM_RE.finditer(q)]
print('Nombres dans le texte:')
for i, (pos, val, pct) in enumerate(nums):
    ctx = q[max(0,pos-80):pos+20].lower()
    print(f'  [{i}] val={val} pct={pct} ctx="...{ctx[-50:]}..."')
    # Vérifier les règles
    if 'left over' in ctx: print(f'       → contient "left over"')
    if 'packs contain' in ctx: print(f'       → contient "packs contain"')
    if 'each' in ctx: print(f'       → contient "each"')
    if 'gives' in ctx: print(f'       → contient "gives"')