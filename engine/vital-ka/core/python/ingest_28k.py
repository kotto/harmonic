"""Ingestion massive 28K faits via DeepSeek."""
import os, sys, time, requests
from pathlib import Path
import numpy as np

# Charger .env
for line in open(Path(__file__).parent / '.env'):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        key, val = line.split('=', 1)
        os.environ[key.strip()] = val.strip().strip('"').strip("'")

KEY = os.environ.get('DEEPSEEK_API_KEY', '')
if not KEY:
    print("DEEPSEEK_API_KEY non trouvée")
    sys.exit(1)

t0 = time.time()
new_facts, seen, added, calls = [], set(), 0, 0
TARGET = 28000

# Collecter les lignes
lines = []
corpus_dir = Path(__file__).parent / '..' / 'data' / 'corpus'
for fname in ['wiki_fr_geography.txt','wiki_fr_science.txt','wiki_en_geography.txt','wiki_en_science.txt',
              'wiki_fr_history.txt','wiki_en_history.txt','wiki_fr_general.txt','wiki_en_general.txt']:
    path = corpus_dir / fname
    if path.exists():
        for l in open(path, encoding='utf-8', errors='replace'):
            l = l.strip()
            if 80 < len(l) < 300:
                lines.append(l)

lines.sort(key=len)
print(f'{len(lines)} lignes, objectif {TARGET} faits')

for line in lines:
    if added >= TARGET:
        break
    try:
        r = requests.post('https://api.deepseek.com/v1/chat/completions',
            headers={'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'},
            json={'model':'deepseek-chat','temperature':0.0,'max_tokens':300,
                  'messages':[{'role':'system','content':'Extract facts: subject | relation | object. One per line. Short. No and/puis/->.'},
                              {'role':'user','content':line[:500]}]}, timeout=10)
        content = r.json()['choices'][0]['message']['content']
        for l2 in content.strip().split('\n'):
            parts = l2.strip().split('|')
            if len(parts) >= 3:
                s,r,o = parts[0].strip(),parts[1].strip(),parts[2].strip()
                if len(s)>=2 and len(r)>=2 and len(o)>=3:
                    if not any(x in r for x in [' puis ','->','>>',' and ']):
                        key = (s.lower(),r.lower(),o.lower())
                        if key not in seen:
                            new_facts.append((s,r,o,'GENERAL'))
                            seen.add(key)
                            added += 1
        calls += 1
        if calls % 500 == 0:
            e = time.time() - t0
            rate = added / max(e, 1)
            eta = (TARGET - added) / max(rate, 0.1) / 60
            print(f'[{calls}c] +{added}/{TARGET} ({rate:.0f}/s) ETA {eta:.0f}min', flush=True)
            np.savez(Path(__file__).parent / 'data' / 'bootstrapper_output' / 'new_facts_28k.npz',
                     facts=np.array(new_facts, dtype=object))
        time.sleep(0.02)
    except Exception as e:
        if calls < 3:
            print(f'Erreur: {e}')

elapsed = time.time() - t0
print(f'\nFini: {elapsed/60:.0f}min | +{added} faits')
out = Path(__file__).parent / 'data' / 'bootstrapper_output' / 'new_facts_28k.npz'
np.savez(str(out), facts=np.array(new_facts, dtype=object))
print(f'Sauvegardé: {out} ({len(new_facts)} faits)')
