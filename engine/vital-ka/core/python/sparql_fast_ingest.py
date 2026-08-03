"""
SPARQL Fast Ingestion — 25 requêtes ciblées, LIMIT réduit
===========================================================
Extrait des faits réels de Wikidata via SPARQL,
fusionne avec les 110K existants.
"""
import json, urllib.request, urllib.parse, time, logging, sys, numpy as np
from collections import defaultdict
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger()

sys.path.insert(0, str(Path(__file__).parent))

SPARQL = 'https://query.wikidata.org/sparql'
UA = 'HarmonicAI/3.3 (research)'

QUERIES = {
    'countries_capitals': 'SELECT ?item ?itemLabel ?capital ?capitalLabel WHERE { ?item wdt:P31 wd:Q3624078. ?item wdt:P36 ?capital. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". } } LIMIT 250',
    'countries_population': 'SELECT ?item ?itemLabel ?pop WHERE { ?item wdt:P31 wd:Q3624078. ?item wdt:P1082 ?pop. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". } } LIMIT 250',
    'countries_continent': 'SELECT ?item ?itemLabel ?continent ?continentLabel WHERE { ?item wdt:P31 wd:Q3624078. ?item wdt:P30 ?continent. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". } } LIMIT 250',
    'cities_country': 'SELECT ?city ?cityLabel ?country ?countryLabel WHERE { ?city wdt:P31 wd:Q515. ?city wdt:P17 ?country. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". } } LIMIT 400',
    'rivers_length': 'SELECT ?river ?riverLabel ?length WHERE { ?river wdt:P31 wd:Q4022. ?river wdt:P2043 ?length. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". } } LIMIT 200',
    'mountains_height': 'SELECT ?mountain ?mountainLabel ?height WHERE { ?mountain wdt:P31 wd:Q8502. ?mountain wdt:P2044 ?height. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". } } LIMIT 200',
    'chemical_symbols': 'SELECT ?elem ?elemLabel ?sym WHERE { ?elem wdt:P31 wd:Q11344. ?elem wdt:P246 ?sym. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". } } LIMIT 150',
    'chemical_number': 'SELECT ?elem ?elemLabel ?num WHERE { ?elem wdt:P31 wd:Q11344. ?elem wdt:P1086 ?num. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". } } LIMIT 150',
    'discoverers': 'SELECT ?person ?personLabel ?discovery ?discoveryLabel WHERE { ?person wdt:P61 ?discovery. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". } } LIMIT 300',
    'inventors': 'SELECT ?person ?personLabel ?invention ?inventionLabel WHERE { ?person wdt:P61 ?invention. ?invention wdt:P31 wd:Q1428153. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". } } LIMIT 200',
    'historical_events': 'SELECT ?event ?eventLabel ?date WHERE { ?event wdt:P31 wd:Q1190554. ?event wdt:P585 ?date. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". } } LIMIT 300',
    'monarchs': 'SELECT ?person ?personLabel ?country ?countryLabel ?start ?end WHERE { ?person wdt:P39 wd:Q116. ?person wdt:P27 ?country. OPTIONAL { ?person wdt:P580 ?start. } OPTIONAL { ?person wdt:P582 ?end. } SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". } } LIMIT 200',
    'battles': 'SELECT ?battle ?battleLabel ?date ?war ?warLabel WHERE { ?battle wdt:P31 wd:Q178561. OPTIONAL { ?battle wdt:P585 ?date. } OPTIONAL { ?battle wdt:P361 ?war. } SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". } } LIMIT 200',
    'painters_works': 'SELECT ?painter ?painterLabel ?work ?workLabel WHERE { ?painter wdt:P106 wd:Q1028181. ?work wdt:P170 ?painter. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". } } LIMIT 400',
    'writers_books': 'SELECT ?writer ?writerLabel ?book ?bookLabel WHERE { ?writer wdt:P106 wd:Q36180. ?book wdt:P50 ?writer. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". } } LIMIT 400',
    'films_directors': 'SELECT ?film ?filmLabel ?director ?directorLabel ?year WHERE { ?film wdt:P31 wd:Q11424. ?film wdt:P57 ?director. OPTIONAL { ?film wdt:P577 ?year. } SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". } } LIMIT 400',
    'music_composers': 'SELECT ?composer ?composerLabel ?work ?workLabel WHERE { ?composer wdt:P106 wd:Q36834. ?work wdt:P86 ?composer. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". } } LIMIT 200',
    'animals_family': 'SELECT ?animal ?animalLabel ?family ?familyLabel WHERE { ?animal wdt:P31 wd:Q16521. ?animal wdt:P177 ?family. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". } } LIMIT 300',
    'plants_family': 'SELECT ?plant ?plantLabel ?family ?familyLabel WHERE { ?plant wdt:P31 wd:Q756. ?plant wdt:P177 ?family. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". } } LIMIT 300',
    'buildings_architect': 'SELECT ?building ?buildingLabel ?architect ?architectLabel ?year WHERE { ?building wdt:P84 ?architect. OPTIONAL { ?building wdt:P571 ?year. } SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". } } LIMIT 300',
    'companies_founded': 'SELECT ?company ?companyLabel ?year ?country ?countryLabel WHERE { ?company wdt:P31 wd:Q4830453. OPTIONAL { ?company wdt:P571 ?year. } OPTIONAL { ?company wdt:P17 ?country. } SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". } } LIMIT 200',
    'universities': 'SELECT ?uni ?uniLabel ?country ?countryLabel ?year WHERE { ?uni wdt:P31 wd:Q3918. ?uni wdt:P17 ?country. OPTIONAL { ?uni wdt:P571 ?year. } SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". } } LIMIT 200',
    'nobel_prizes': 'SELECT ?person ?personLabel ?year WHERE { ?person wdt:P166 wd:Q7191. ?person p:P166 ?stmt. ?stmt pq:P585 ?year. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". } } LIMIT 300',
    'astronomical_objects': 'SELECT ?obj ?objLabel ?type ?typeLabel WHERE { ?obj wdt:P31 wd:Q6999. ?obj wdt:P31 ?type. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". } } LIMIT 200',
}

RELATION_MAP = {
    'capital': ('a pour capitale', 'GEOGRAPHIE'),
    'pop': ('a une population de', 'GEOGRAPHIE'),
    'continent': ('est situe sur le continent', 'GEOGRAPHIE'),
    'country': ('est situe en', 'GEOGRAPHIE'),
    'length': ('a une longueur de', 'GEOGRAPHIE'),
    'height': ('a une altitude de', 'GEOGRAPHIE'),
    'sym': ('a pour symbole chimique', 'SCIENCES'),
    'num': ('a pour numero atomique', 'SCIENCES'),
    'discovery': ('a decouvert', 'SCIENCES'),
    'invention': ('a invente', 'SCIENCES'),
    'discoverer': ('a ete decouvert par', 'SCIENCES'),
    'date': ('a eu lieu en', 'HISTOIRE'),
    'year': ('a ete cree en', 'HISTOIRE'),
    'start': ('a debute en', 'HISTOIRE'),
    'end': ('a pris fin en', 'HISTOIRE'),
    'war': ('fait partie de la guerre', 'HISTOIRE'),
    'work': ('a cree', 'CULTURE'),
    'book': ('a ecrit', 'CULTURE'),
    'film': ('a realise', 'CULTURE'),
    'director': ('a pour realisateur', 'CULTURE'),
    'painter': ('a peint', 'CULTURE'),
    'writer': ('a ecrit', 'CULTURE'),
    'composer': ('a compose', 'CULTURE'),
    'family': ('appartient a la famille', 'BIOLOGIE'),
    'architect': ('a pour architecte', 'CULTURE'),
    'building': ('a ete construit en', 'CULTURE'),
    'company': ('a ete fondee en', 'ECONOMIE'),
    'uni': ('a ete fondee en', 'CULTURE'),
    'planet': ('a pour decouvreur', 'SCIENCES'),
    'obj': ('est un objet astronomique', 'SCIENCES'),
    'type': ('est de type', 'SCIENCES'),
}

def fetch_sparql(query):
    url = f'{SPARQL}?format=json&query={urllib.parse.quote(query)}'
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        log.warning(f'  skip: {e}')
        return None

all_triples = []
t0 = time.time()

for name, query in QUERIES.items():
    log.info(f'{name}...')
    data = fetch_sparql(query)
    if not data:
        continue
    
    bindings = data.get('results', {}).get('bindings', [])
    count = 0
    
    for b in bindings:
        label_keys = [k for k in b if k.endswith('Label') and not k.startswith('_')]
        if not label_keys:
            continue
        sujet = b[label_keys[0]].get('value', '')
        if not sujet or len(sujet) < 2:
            continue
        
        for key in b:
            if key in label_keys:
                continue
            val = b[key].get('value', '')
            if not val or len(str(val)) < 1:
                continue
            
            rel_key = key.replace('Label', '').lower()
            relation = rel_key.replace('_', ' ')
            secteur = 'GENERAL'
            for kw, (rel, sec) in RELATION_MAP.items():
                if kw in rel_key:
                    relation = rel
                    secteur = sec
                    break
            
            val_str = str(val)
            if val_str.startswith('http'):
                continue
            if val_str.startswith('+') and 'T' in val_str:
                val_str = val_str.split('T')[0].lstrip('+')
            
            all_triples.append((sujet, relation, val_str, secteur))
            count += 1
    
    log.info(f'  +{count} (total: {len(all_triples):,})')
    time.sleep(0.3)

elapsed = time.time() - t0
log.info(f'Done: {len(all_triples):,} faits en {elapsed:.0f}s')

# Dedup
seen = set()
unique = []
sectors = defaultdict(int)
for s, r, o, sec in all_triples:
    key = (s.lower().strip()[:80], r.lower().strip()[:80], str(o).lower().strip()[:80])
    if key not in seen:
        seen.add(key)
        unique.append((s, r, o, sec))
        sectors[sec] += 1

log.info(f'Unique: {len(unique):,}')

# Merge with 110K
log.info('Merging with 110K...')
d = np.load('data/bootstrapper_output/knowledge_base_100k.npz', allow_pickle=True)
for f in d['facts']:
    s, r, o, sec = str(f[0]), str(f[1]), str(f[2]), str(f[3])
    key = (s.lower().strip()[:80], r.lower().strip()[:80], o.lower().strip()[:80])
    if key not in seen:
        seen.add(key)
        unique.append((s, r, o, sec))
        sectors[sec] += 1

log.info(f'Merged: {len(unique):,}')

# Save
np.savez_compressed('data/bootstrapper_output/knowledge_base_merged_v3.npz',
    facts=np.array(unique, dtype=object))

print(f'\n=== knowledge_base_merged_v3.npz : {len(unique):,} faits ===')
for sec, n in sorted(sectors.items(), key=lambda x: -x[1])[:15]:
    print(f'  {sec:25} {n:>8,}')
print(f'  {"TOTAL":25} {len(unique):>8,}')
