#!/usr/bin/env python3
"""Test HTTP de bout en bout — KA Enterprise : données privées → livrables."""
import io
import json
import sys
import urllib.request
import urllib.error

BASE = 'http://127.0.0.1:8768'
KEY = ''

def call(path, method='GET', body=None, key=None, raw=False):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Content-Type', 'application/json')
    if key:
        req.add_header('X-API-Key', key)
    try:
        with urllib.request.urlopen(req) as r:
            content = r.read()
            if raw:
                return content, r.headers
            return json.loads(content) if content else None
    except urllib.error.HTTPError as e:
        return {'http_error': e.code, 'body': e.read().decode()[:200]}

# ── 1. Onboarding (secteur informatique, 1 hologramme filtré)
r = call('/api/enterprise/onboard', 'POST', {
    'name': 'Studio DataTest', 'email': 'dt@studio.fr',
    'description': "Nous gérons les données de nos clients avec un service informatique et de la data",
    'holograms': ['donnees et intelligence artificielle'],
})
assert 'tenant' in r and r['tenant'].get('api_key'), f"onboard KO: {r}"
KEY = r['tenant']['api_key']
dept = r['departments'][0]['id']
print(f"1. Onboarding OK — tenant {r['tenant']['name']}, dept {r['departments'][0]['sujet']} ({r['departments'][0]['facts']} faits)")

# ── 2. Ingestion de données privées (CSV clients + factures)
csv_text = "\n".join([
    'client_1 | Dupont SA | Paris | 450000',
    'client_2 | Martin & Fils | Lyon | 120500',
    'client_3 | Durand SARL | Marseille | 78000',
    'client_4 | Bernard Conseil | Lille | 234000',
    'client_5 | Petit Distribution | Nantes | 1500',
])
r = call(f'/api/enterprise/departments/{dept}/ingest', 'POST',
         {'text': csv_text, 'source': 'clients.csv'}, key=KEY)
assert r.get('facts_ingested') == 5, f"ingest KO: {r}"
print(f"2. Ingestion OK — {r['facts_ingested']} faits clients")

# ── 3. Question de données : liste
r = call(f'/api/enterprise/departments/{dept}/data', 'POST',
         {'question': 'liste des clients'}, key=KEY)
assert r.get('count') == 5, f"data liste KO: {r}"
assert r['rows'][0]['Colonne 1'] == 'client_1', f"ordre KO: {r['rows'][0]}"
print(f"3. Liste OK — {r['count']} lignes, colonnes {r['columns']}, 1ʳᵉ ligne {r['rows'][0]['Colonne 2']}")

# ── 4. Agrégats
r = call(f'/api/enterprise/departments/{dept}/data', 'POST',
         {'question': "quel est le chiffre d'affaires total"}, key=KEY)
assert abs(r['aggregates'][0]['valeur'] - 884000.0) < 1, f"somme KO: {r['aggregates']}"
r = call(f'/api/enterprise/departments/{dept}/data', 'POST',
         {'question': 'combien de clients avons-nous'}, key=KEY)
assert r['aggregates'][0]['valeur'] == 5, f"compte KO: {r['aggregates']}"
print(f"4. Agrégats OK — total 884000, compte 5")

# ── 5. Export Excel (.xlsx)
content, headers = call(f'/api/enterprise/departments/{dept}/export?question={urllib.parse.quote("liste des clients")}&format=xlsx',
                        key=KEY, raw=True)
assert content[:2] == b'PK', f"xlsx KO: {content[:8]}"
assert 'xlsx' in headers.get('Content-Disposition', ''), headers
print(f"5. Export xlsx OK — {len(content)} octets (ZIP PK), Content-Disposition: {headers['Content-Disposition']}")

# ── 6. Export CSV
content, _ = call(f'/api/enterprise/departments/{dept}/export?question={urllib.parse.quote("liste des clients")}&format=csv',
                  key=KEY, raw=True)
assert b'client_1' in content and b';' in content, f"csv KO: {content[:120]}"
print(f"6. Export csv OK — {len(content)} octets (séparateur ;)")

# ── 7. Composition de documents
r = call(f'/api/enterprise/departments/{dept}/compose', 'POST',
         {'brief': 'situation des clients', 'format': 'email',
          'objet': 'Point clientèle', 'destinataire': 'Direction'}, key=KEY)
assert 'texte' in r and 'Objet' in r['texte'] and 'Direction' in r['texte'], f"email KO: {r}"
print(f"7. Email OK ({r['facts_utilises']} faits) — « {r['texte'][:60]}… »")

r = call(f'/api/enterprise/departments/{dept}/compose', 'POST',
         {'brief': 'situation des clients', 'format': 'compte_rendu'}, key=KEY)
assert 'COMPTE-RENDU' in r['texte'] and 'PROCHAINES ÉTAPES' in r['texte']
print(f"   Compte-rendu OK")

# ── 8. Téléchargement .docx
content, headers = call(f'/api/enterprise/departments/{dept}/compose', 'POST',
                        {'brief': 'situation des clients', 'format': 'rapport', 'download': 'docx'},
                        key=KEY, raw=True)
assert content[:2] == b'PK', f"docx KO: {content[:8]}"
print(f"8. Téléchargement docx OK — {len(content)} octets")

# ── 9. Synthèse
r = call(f'/api/enterprise/departments/{dept}/summarize', 'POST', key=KEY)
assert r.get('facts') == 9 and 'clients.csv' in r.get('sources', {}), f"summarize KO: {r}"
print(f"9. Synthèse OK — {r['facts']} faits, sources {list(r['sources'])}")

# ── 10. Sécurité : sans clé → 401
r = call(f'/api/enterprise/departments/{dept}/data', 'POST', {'question': 'liste'})
assert r.get('http_error') == 401, f"401 KO: {r}"
print("10. Sécurité OK — 401 sans clé API")

print("\n✅ TOUS LES TESTS HTTP PASSENT")
