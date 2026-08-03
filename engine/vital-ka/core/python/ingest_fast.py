"""Ingestion rapide — extraction DeepSeek, sauvegarde checkpoint."""
import os, sys, time, json, requests
from pathlib import Path
import numpy as np

KEY = os.environ.get('DEEPSEEK_API_KEY', '')
if not KEY:
    for line in open(Path(__file__).parent / '.env'):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip().strip('"').strip("'")
    KEY = os.environ.get('DEEPSEEK_API_KEY', '')

OUTPUT = Path('data/bootstrapper_output/ingested_new.npz')
STATE = Path('data/bootstrapper_output/ingest_state.json')

# Reprendre
start_i = 0
all_facts = []
seen = set()
if STATE.exists():
    s = json.loads(STATE.read_text())
    start_i = s.get('line', 0)
    all_facts = s.get('facts', [])
    seen = set((f[0].lower(), f[1].lower(), f[2].lower()) for f in all_facts)
    print(f"Reprise: ligne {start_i}, {len(all_facts)} faits")

# Lignes
lines = []
for fname in ['wiki_fr_geography.txt','wiki_fr_science.txt','wiki_fr_history.txt',
              'wiki_en_geography.txt','wiki_en_science.txt','wiki_en_history.txt',
              'wiki_fr_general.txt','wiki_en_general.txt']:
    p = Path(f'../data/corpus/{fname}')
    if p.exists():
        for l in open(p, encoding='utf-8', errors='replace'):
            l = l.strip()
            if 70 < len(l) < 350:
                lines.append(l)

print(f"Corpus: {len(lines)} lignes | Départ: {start_i}")
t0 = time.time()
added = 0

for i in range(start_i, len(lines)):
    try:
        r = requests.post('https://api.deepseek.com/v1/chat/completions',
            headers={'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'},
            json={'model':'deepseek-chat','temperature':0.0,'max_tokens':300,
                  'messages':[{'role':'system','content':'Extract facts: subject|relation|object. One/line. No and/puis/->.'},
                              {'role':'user','content':f'Facts:\n{lines[i][:500]}'}]}, timeout=10)
        content = r.json()['choices'][0]['message']['content']
        for l2 in content.strip().split('\n'):
            parts = l2.strip().split('|')
            if len(parts) >= 3:
                s, r, o = parts[0].strip(), parts[1].strip(), parts[2].strip()
                if len(s)>=2 and len(r)>=2 and len(o)>=3:
                    if not any(x in r for x in [' puis ','->','>>']):
                        key = (s.lower(), r.lower(), o.lower())
                        if key not in seen:
                            seen.add(key)
                            all_facts.append((s, r, o, 'GENERAL'))
                            added += 1
    except: pass
    
    if (i+1) % 100 == 0:
        e = time.time()-t0
        rate = added/max(e,1)
        print(f"[{i+1}/{len(lines)}] +{added} ({rate:.0f}/s) total:{len(all_facts)}", flush=True)
        STATE.write_text(json.dumps({'line': i+1, 'facts': all_facts[-10000:]}))  # derniers 10K
        if len(all_facts) % 2000 == 0:
            np.savez(str(OUTPUT), facts=np.array(all_facts, dtype=object))
            print(f"  SAVED {len(all_facts)}", flush=True)
    
    time.sleep(0.03)

np.savez(str(OUTPUT), facts=np.array(all_facts, dtype=object))
print(f"\nDONE: {len(all_facts)} faits in {time.time()-t0:.0f}s")
