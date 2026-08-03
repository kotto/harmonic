"""Ingestion incrémentale 100K — Background avec checkpoints."""
import os, sys, time, json, requests
from pathlib import Path
import numpy as np

# Config
TARGET = 100000
CHECKPOINT_EVERY = 500
SAVE_EVERY = 2000
CORPUS_DIR = Path('../data/corpus')
OUTPUT = Path('data/bootstrapper_output/knowledge_base_100k_ingested.npz')
STATE_FILE = Path('data/bootstrapper_output/ingestion_state.json')

# Charger .env
env_path = Path(__file__).parent / '.env'
if not env_path.exists():
    env_path = Path('.env')
for line in open(env_path):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        os.environ[k.strip()] = v.strip().strip('"').strip("'")

KEY = os.environ.get('DEEPSEEK_API_KEY', '')
if not KEY:
    print("DEEPSEEK_API_KEY manquante")
    sys.exit(1)

# Charger état précédent
seen = set()
facts_list = []
lines_done = 0
if STATE_FILE.exists():
    state = json.loads(STATE_FILE.read_text())
    lines_done = state.get('lines_done', 0)
    facts_count = state.get('facts_count', 0)
    print(f"Reprise: {lines_done} lignes traitées, {facts_count} faits")

# Charger faits existants (déduplication)
kb_path = Path('data/bootstrapper_output/knowledge_base_clean_v2.npz')
if kb_path.exists():
    data = np.load(str(kb_path), allow_pickle=True)
    for f in data['facts']:
        s, r, o = str(f[0]).strip().lower(), str(f[1]).strip().lower(), str(f[2]).strip().lower()
        seen.add((s, r, o))
    print(f"KB existante: {len(seen)} faits (dédoublonnage)")

def extract(text):
    """Extrait des triplets via DeepSeek."""
    try:
        r = requests.post('https://api.deepseek.com/v1/chat/completions',
            headers={'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'},
            json={'model':'deepseek-chat','temperature':0.0,'max_tokens':350,
                  'messages':[{'role':'system','content':'Extract facts: subject | relation | object. One per line. NEVER use puis/and/->/>>.'},
                              {'role':'user','content':f'Extract facts:\n{text[:600]}'}]},
            timeout=12)
        content = r.json()['choices'][0]['message']['content']
        triples = []
        for line in content.strip().split('\n'):
            parts = line.strip().split('|')
            if len(parts) >= 3:
                s, r, o = parts[0].strip(), parts[1].strip(), parts[2].strip()
                if len(s)>=2 and len(r)>=2 and len(o)>=3:
                    if not any(x in r for x in [' puis ','->','>>',' and ',' puis','->']):
                        triples.append((s, r, o))
        return triples
    except Exception as e:
        return []

# Collecter lignes
lines = []
for fname in ['wiki_fr_geography.txt','wiki_fr_science.txt','wiki_fr_history.txt',
              'wiki_en_geography.txt','wiki_en_science.txt','wiki_en_history.txt',
              'wiki_fr_general.txt','wiki_en_general.txt']:
    path = CORPUS_DIR / fname
    if path.exists():
        for l in open(path, encoding='utf-8', errors='replace'):
            l = l.strip()
            if 60 < len(l) < 400:
                lines.append(l)

print(f"Corpus: {len(lines)} lignes")
print(f"Début ingestion — cible {TARGET} faits")
print("="*50)

t0 = time.time()
added = 0
errors = 0

for i, line in enumerate(lines):
    if i < lines_done:
        continue  # skip déjà traitées
    
    if len(seen) >= TARGET:
        break
    
    try:
        triples = extract(line)
        for s, r, o in triples:
            key = (s.lower().strip(), r.lower().strip(), o.lower().strip())
            if key not in seen:
                seen.add(key)
                facts_list.append((s, r, o, 'GENERAL'))
                added += 1
    except Exception as e:
        errors += 1
        if errors < 5:
            print(f"  Erreur L{i}: {e}")
    
    lines_done = i + 1
    
    # Progression
    if (i + 1) % 50 == 0:
        elapsed = time.time() - t0
        rate = added / max(elapsed, 1)
        eta = (TARGET - len(seen)) / max(rate, 0.01) / 60
        pct = len(seen) / TARGET * 100
        print(f"[{lines_done}/{len(lines)}] +{added} | total:{len(seen)} ({pct:.0f}%) | {rate:.0f}f/s | ETA {eta:.0f}min | err:{errors}")
    
    # Checkpoint
    if added > 0 and added % CHECKPOINT_EVERY == 0:
        STATE_FILE.write_text(json.dumps({
            'lines_done': lines_done,
            'facts_count': len(seen),
            'added_this_session': added,
            'elapsed_min': (time.time()-t0)/60
        }))
    
    # Sauvegarde intermédiaire
    if len(facts_list) >= SAVE_EVERY:
        if OUTPUT.exists():
            old = np.load(str(OUTPUT), allow_pickle=True)
            old_facts = [(str(f[0]),str(f[1]),str(f[2]),str(f[3])) for f in old['facts']]
        else:
            old_facts = []
        all_facts = old_facts + facts_list
        np.savez(str(OUTPUT), facts=np.array(all_facts, dtype=object))
        facts_list = []
        print(f"  💾 Sauvegardé: {len(all_facts)} faits")
    
    time.sleep(0.03)  # rate limit

# Sauvegarde finale
if facts_list:
    if OUTPUT.exists():
        old = np.load(str(OUTPUT), allow_pickle=True)
        old_facts = [(str(f[0]),str(f[1]),str(f[2]),str(f[3])) for f in old['facts']]
    else:
        old_facts = []
    all_facts = old_facts + facts_list
    np.savez(str(OUTPUT), facts=np.array(all_facts, dtype=object))

elapsed = time.time() - t0
print(f"\n{'='*50}")
print(f"TERMINÉ en {elapsed/60:.0f}min")
print(f"Total: {len(seen)} faits")
print(f"Ajoutés: {added}")
print(f"Erreurs: {errors}")
print(f"Sauvegardé: {OUTPUT}")
STATE_FILE.write_text(json.dumps({'lines_done': lines_done, 'facts_count': len(seen), 'done': True}))
