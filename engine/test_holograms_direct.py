# -*- coding: utf-8 -*-
"""Test direct des hologrammes médicaux via l'API."""
import json, time, urllib.request

BASE = 'http://127.0.0.1:8010'

def call(endpoint, payload):
    req = urllib.request.Request(
        f'{BASE}{endpoint}',
        data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json'})
    t0 = time.time()
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read()), (time.time() - t0) * 1000

# ── Tests de routage ──
tests = [
    ("fièvre toux fatigue", "auto"),
    ("paludisme enfant fièvre", "auto"),
    ("diabète hypertension", "auto"),
    ("vaccination calendrier enfant", "auto"),
    ("douleur thoracique urgence", "auto"),
    ("dépression anxiété", "auto"),
    ("interaction paracétamol amoxicilline", "auto"),
    ("grossesse allaitement", "auto"),
    ("malnutrition enfant kwashiorkor", "auto"),
    ("plante feuille paludisme tisane", "auto"),
]

print("=" * 70)
print("🧪 TESTS DE ROUTAGE SPECTRAL (domaine auto)")
print("=" * 70)
for query, dom in tests:
    try:
        data, ms = call('/hologram/query', {'domain': dom, 'query': query, 'top_k': 3})
        routes = [f"{r['secteur']}({r['score']:.2f})" for r in data['routes'][:3]] if 'routes' in data else 'n/a'
        top = data['results'][0] if data['results'] else None
        print(f"Q: {query}")
        print(f"  → domaine: {data['domain']} | routes: {routes} | {len(data['results'])} résultats | {ms:.0f}ms")
        if top:
            print(f"  → top: [{top['score']:.2f}] {top['sujet']} {top['relation']} {str(top['objet'])[:60]}")
    except Exception as e:
        print(f"Q: {query} → ERREUR: {e}")
    print()

# ── Tests pièges ──
print("=" * 70)
print("🧨 TESTS PIÈGES (limites du système)")
print("=" * 70)
edge_cases = [
    ("football mercato transfert", "auto", "hors-sujet"),
    ("", "auto", "requête vide"),
    ("paludisme", "PHARMACIE", "domaine forcé"),
    ("xyzabc", "auto", "mots inexistants"),
    ("paludisme", "DOMAINE_INEXISTANT", "domaine invalide"),
]
for query, dom, label in edge_cases:
    try:
        data, ms = call('/hologram/query', {'domain': dom, 'query': query, 'top_k': 3})
        print(f"[{label}] Q='{query}' dom={dom}")
        print(f"  → domaine: {data['domain']} | {len(data['results'])} résultats | {ms:.0f}ms")
        for r in data['results'][:2]:
            print(f"    • [{r['score']:.2f}] ({r['secteur']}) {r['content'][:70]}")
    except Exception as e:
        print(f"[{label}] Q='{query}' dom={dom} → ERREUR: {str(e)[:120]}")
    print()

# ── Latence ──
print("=" * 70)
print("⏱️  BENCHMARK LATENCE (20 requêtes identiques)")
print("=" * 70)
lat = []
for i in range(20):
    _, ms = call('/hologram/query', {'domain': 'auto', 'query': 'paludisme fièvre traitement', 'top_k': 5})
    lat.append(ms)
lat.sort()
print(f"  min: {lat[0]:.0f}ms | médiane: {lat[10]:.0f}ms | max: {lat[-1]:.0f}ms | moy: {sum(lat)/len(lat):.0f}ms")
