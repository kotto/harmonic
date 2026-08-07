#!/usr/bin/env python3
"""Test HTTP de bout en bout — Chaînon D Enterprise (auto-apprentissage)."""
import json
import time
import urllib.request
import urllib.error

BASE = 'http://127.0.0.1:8768'
KEY = ''


def call(path, method='GET', body=None, key=None):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Content-Type', 'application/json')
    if key:
        req.add_header('X-API-Key', key)
    try:
        with urllib.request.urlopen(req) as r:
            content = r.read()
            return json.loads(content) if content else None
    except urllib.error.HTTPError as e:
        return {'http_error': e.code, 'body': e.read().decode()[:200]}


# ── 1. Onboarding : un département « pharmacologie » (seed Wikipedia réel)
r = call('/api/enterprise/onboard', 'POST', {
    'name': 'Pharma Test', 'email': 'pharma@test.fr',
    'description': "laboratoire pharmaceutique avec un service pharmacologie",
    'secteur': 'sante', 'holograms': ['pharmacologie'],
})
assert 'tenant' in r, f"onboard KO: {r}"
KEY = r['tenant']['api_key']
dept = r['departments'][0]
print(f"1. Onboarding OK — {dept['sujet']}: {dept['facts']} faits seed "
      f"({dept['couverture'].get('couverture')})")
assert dept['facts'] > 0, 'seed vide'

# ── 2. Trois questions SANS réponse → seuil sujet atteint → complétion auto
Q = 'quelle est la couleur des martiens ?'
confiances = []
for i in range(1, 4):
    r = call(f'/api/enterprise/departments/{dept["id"]}/ask', 'POST',
             {'question': Q}, key=KEY)
    assert 'answer' in r, f"ask KO: {r}"
    confiances.append(round(r['confidence'], 2))
    print(f"2.{i} ask → confiance {r['confidence']:.2f} | "
          f"incertitude admise: {r['admitted_uncertainty']}")
    time.sleep(1.0)

print(f"   confiances: {confiances}")

# ── 3. La complétion tourne en arrière-plan → vérifier le rapport
print("3. attente de la complétion en arrière-plan…")
time.sleep(10)
r = call('/api/enterprise/completions/status', key=KEY)
assert 'rapports' in r, f"status KO: {r}"
print(f"   file: {r['file']}")
if r['rapports']:
    rep = r['rapports'][0]
    print(f"   rapport: +{rep['facts_ajoutes']} faits ({rep['source']}), "
          f"couverture {rep['couverture_avant']} → {rep['couverture_apres']}")
    assert rep['facts_ajoutes'] > 0, 'complétion vide'
else:
    print("   (aucun rapport — la complétion n'a pas fini ou pas été déclenchée)")

# ── 4. Une question du SUJET répond-elle mieux maintenant ?
time.sleep(2)
r = call(f'/api/enterprise/departments/{dept["id"]}/ask', 'POST',
         {'question': 'quels sont les effets secondaires des medicaments ?'}, key=KEY)
print(f"4. question sujet → confiance {r['confidence']:.2f} | {r['answer'][:90]}…")

# ── 5. /completions/run (traite les sujets restés en attente)
r = call('/api/enterprise/completions/run', 'POST', key=KEY)
print(f"5. run → {r}")

print('\n✅ TEST CHAÎNON D HTTP TERMINÉ')
