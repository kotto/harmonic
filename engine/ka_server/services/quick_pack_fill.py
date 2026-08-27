"""
Quick fill for empty packs (geographie, linguistique) using short LLM prompts.
"""
import sys, json, time, re, unicodedata, urllib.request
sys.path.insert(0, '/opt/ka-server')
from ka_server.services.okf_compiler import create_file, compile_wiki

PHI_API = 'http://localhost:8080'

def call_llm(prompt, timeout=60):
    payload = json.dumps({'question': prompt, 'system': 'Reponds UNIQUEMENT avec les faits. Format: sujet | relation | objet'}).encode()
    for ep in ['/phi/query', '/query']:
        try:
            req = urllib.request.Request(PHI_API + ep, data=payload, headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())['answer']
        except Exception:
            pass
    return None

def parse_facts(text):
    facts = []
    for line in text.splitlines():
        line = line.strip().lstrip('-*bull;').strip()
        if '|' in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3 and parts[0] and parts[1] and parts[2]:
                s = unicodedata.normalize('NFD', parts[0]).encode('ascii','ignore').decode().lower()
                r = unicodedata.normalize('NFD', parts[1]).encode('ascii','ignore').decode().lower()
                o = unicodedata.normalize('NFD', parts[2]).encode('ascii','ignore').decode().lower()
                if len(s) > 2:
                    facts.append((s, r, o))
    return facts

PACKS = {
    'geographie': [
        'capitale de la France',
        'capitale du Japon',
        'plus long fleuve du monde',
        'plus haut sommet du monde',
        'plus grand desert du monde',
        'capitale de l Italie',
        'capitale de l Espagne',
        'capitale de l Allemagne',
        'capitale du Bresil',
        'capitale du Canada',
        'capitale de la Chine',
        'capitale de l Inde',
        'capitale de la Russie',
        'capitale des Etats Unis',
        'capitale de l Egypte',
        'capitale du Senegal',
        'capitale de la RDC',
        'plus grand ocean du monde',
        'plus grand continent du monde',
        'plus petit continent du monde',
    ],
    'linguistique': [
        'langue francaise',
        'langue anglaise',
        'langue espagnole',
        'langue arabe',
        'langue mandarine',
        'qu est ce qu un phoneme',
        'qu est ce qu un morpheme',
        'qu est ce que la syntaxe',
        'qu est ce que la semantique',
    ],
}

for domain, questions in PACKS.items():
    print(f'\nPACK {domain}...')
    for q in questions:
        topic = q.split('est ce que')[-1].strip() if 'est ce que' in q else q
        prompt = 'Donne 3 faits sur ' + topic + ' au format: sujet | relation | objet'
        resp = call_llm(prompt, timeout=30)
        if resp:
            facts = parse_facts(resp)
            print(f'  {q:40s} -> {len(facts)} faits')
            if facts:
                cid = re.sub(r'[^a-z0-9_]', '_', topic[:30].lower()).strip('_')
                create_file(domain, cid, topic.capitalize(), facts, source='llm_quick_fill', overwrite=True)
        else:
            print(f'  {q:40s} -> LLM timeout')
    r = compile_wiki(action='quick_fill|' + domain)
    print(f'   Compilation: {sum(rr["facts"] for rr in r["results"].values())} faits')

print('\nQuick fill done.')