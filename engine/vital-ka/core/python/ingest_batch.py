"""Ingestion batch 5× plus rapide — 5 phrases par appel DeepSeek."""
import os, time, json, requests
from pathlib import Path
import numpy as np

BASE = Path(__file__).parent
os.chdir(str(BASE))

# Charger clé API (env var ou .env)
KEY = os.environ.get('DEEPSEEK_API_KEY', '')
if not KEY:
    env_path = BASE / '.env'
    if env_path.exists():
        try:
            for line in env_path.read_text(encoding='utf-8').strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ[k.strip()] = v.strip().strip('"').strip("'")
        except:
            pass
    KEY = os.environ.get('DEEPSEEK_API_KEY', '')

if not KEY:
    print("DEEPSEEK_API_KEY non trouvée. Définis-la dans l'environnement ou .env")
    exit(1)
OUT = BASE / 'data' / 'bootstrapper_output' / 'ingested_batch.npz'
STATE = BASE / 'data' / 'bootstrapper_output' / 'ingest_batch_state.json'
CORPUS = BASE.parent / 'data' / 'corpus'

BATCH_SIZE = 5
TARGET = 28000

# Reprendre
all_facts, seen, start_batch = [], set(), 0
if OUT.exists():
    d = np.load(str(OUT), allow_pickle=True)
    all_facts = [(str(f[0]),str(f[1]),str(f[2]),str(f[3])) for f in d['facts']]
    seen = set((f[0].lower(),f[1].lower(),f[2].lower()) for f in all_facts)
    if STATE.exists():
        s = json.loads(STATE.read_text())
        start_batch = s.get('batch', 0)
    print(f'REPRISE: {len(all_facts)} faits, batch {start_batch}')

# Charger lignes
lines = []
for fn in ['wiki_fr_geography.txt','wiki_fr_science.txt','wiki_fr_history.txt',
           'wiki_en_geography.txt','wiki_en_science.txt','wiki_en_history.txt',
           'wiki_fr_general.txt','wiki_en_general.txt']:
    p = CORPUS / fn
    if p.exists():
        for l in open(p, encoding='utf-8', errors='replace'):
            l = l.strip()
            if 70 < len(l) < 350:
                lines.append(l)

# Grouper en batches
batches = [lines[i:i+BATCH_SIZE] for i in range(0, len(lines), BATCH_SIZE)]
print(f'{len(lines)} lignes → {len(batches)} batches de {BATCH_SIZE}')

t0 = time.time()
added = 0
errors = 0

for bi in range(start_batch, len(batches)):
    if len(all_facts) >= TARGET:
        break
    
    batch = batches[bi]
    batch_text = '\n'.join(f'{j+1}. {l}' for j, l in enumerate(batch))
    prompt = f'Extract facts: subject|relation|object. One per line. No puis/->/and.\n\n{batch_text}'
    
    try:
        r = requests.post('https://api.deepseek.com/v1/chat/completions',
            headers={'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'},
            json={'model':'deepseek-chat','temperature':0,'max_tokens':500,
                  'messages':[{'role':'system','content':'Extract facts: subject|relation|object. One/line. NEVER use puis/and/->/>> in relation.'},
                              {'role':'user','content':prompt}]}, timeout=15)
        
        for l2 in r.json()['choices'][0]['message']['content'].strip().split('\n'):
            parts = l2.strip().split('|')
            if len(parts) >= 3:
                s, r, o = parts[0].strip(), parts[1].strip(), parts[2].strip()
                if len(s)>=2 and len(r)>=2 and len(o)>=3:
                    if not any(x in r for x in [' puis ','->','>>']):
                        k = (s.lower(), r.lower(), o.lower())
                        if k not in seen:
                            seen.add(k)
                            all_facts.append((s, r, o, 'GENERAL'))
                            added += 1
    except Exception as e:
        errors += 1
        if errors <= 3:
            print(f'  ERR batch {bi}: {e}')
    
    # Progression
    if (bi+1) % 100 == 0:
        e = time.time() - t0
        rate = added / max(e, 1)
        eta = (TARGET - len(all_facts)) / max(rate, 0.1) / 60
        print(f'[B{bi+1}/{len(batches)}] +{added} ({rate:.0f}f/s) total:{len(all_facts)} ETA:{eta:.0f}min ERR:{errors}', flush=True)
        STATE.write_text(json.dumps({'batch': bi+1, 'facts': len(all_facts), 'added': added}))
        np.savez(str(OUT), facts=np.array(all_facts, dtype=object))
    
    time.sleep(0.05)  # rate limit léger

e = time.time() - t0
np.savez(str(OUT), facts=np.array(all_facts, dtype=object))
print(f'\nDONE: +{added} en {e/60:.0f}min | Total: {len(all_facts)} | Rate: {added/max(e,1)*60:.0f}f/min')
STATE.write_text(json.dumps({'batch': len(batches), 'facts': len(all_facts), 'done': True}))
