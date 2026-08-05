# -*- coding: utf-8 -*-
"""Test d'intégration : ingestion structurée type Docling via l'API Enterprise."""
import logging
logging.disable(logging.CRITICAL)

MD = """# Pack KA Entreprise

Le Pack KA Entreprise déploie l'IA harmonique dans votre système d'information. Il transforme vos documents en hologrammes spécialisés.

## Formules et tarifs

| Formule | Prix / mois | Documents | Hologrammes |
|---------|-------------|-----------|-------------|
| Starter | 99 € | 1 000 | 1 |
| Pro | 299 € | 10 000 | 5 |
| Entreprise | 899 € | illimité | 20 |

## Sécurité

La sécurité utilise le chiffrement AES-256. Les données restent dans votre réseau.

- Chiffrement au repos
- Chiffrement en transit
- Journal d'audit complet
"""

pass_count = 0
fail_count = 0


def check(name, cond, detail=""):
    global pass_count, fail_count
    ok = bool(cond)
    if ok:
        pass_count += 1
    else:
        fail_count += 1
    print(("✅ " if ok else "❌ ") + name + (("  [" + str(detail) + "]") if detail else ""))


from ka_server.app import create_app
app = create_app()
app.config['TESTING'] = True
# Ajouter une clé API pour l'auth Enterprise
app.ka_auth['add_api_key']('test-cle-enterprise')
c = app.test_client()
H = {'X-API-Key': 'test-cle-enterprise', 'Content-Type': 'application/json'}

# ── 1. Ingestion structurée ──
r = c.post('/api/v2/enterprise/ingest/structured', headers=H,
           json={'content': MD, 'format': 'markdown', 'domain': 'pack_ka',
                 'category': 'tech', 'source': 'fiche_produit.md'})
d = r.get_json()
check("ingest : HTTP 200", r.status_code == 200, r.status_code)
check("ingest : success", d.get('success') is True)
check("ingest : hologramme créé", d.get('hologram_id') == 'pack_ka', d.get('hologram_id'))
check("ingest : 40 faits (ce document)", d.get('facts') == 40, d.get('facts'))
check("ingest : faits structurels", d.get('structural_facts', 0) >= 15, d.get('structural_facts'))
check("ingest : faits de table", d.get('table_facts', 0) >= 12, d.get('table_facts'))
check("ingest : document structuré (sections)", d.get('document', {}).get('sections'), len(d.get('document', {}).get('sections', [])))
check("ingest : schema harmonique", d.get('document', {}).get('schema_name') == 'HarmoniqueDocument')

# ── 2. Rappel structurel ──
r = c.post('/api/v2/enterprise/recall/structured', headers=H,
           json={'domain': 'pack_ka', 'query': 'quel est le prix de la formule pro ?', 'top_k': 2})
d = r.get_json()
check("recall : HTTP 200", r.status_code == 200)
check("recall : section Formules trouvée", d.get('sections') and d['sections'][0]['section'] == 'Formules et tarifs',
      [s['section'] for s in d.get('sections', [])])
check("recall : table complète rendue", d.get('sections') and '299 €' in d['sections'][0]['content'])
check("recall : parent hiérarchique", d.get('sections') and d['sections'][0]['parent'] == 'Pack KA Entreprise')

# ── 3. Liste des documents ──
r = c.get('/api/v2/enterprise/documents', headers=H)
d = r.get_json()
check("documents : listé", d.get('documents') and d['documents'][0]['domain'] == 'pack_ka')

# ── 4. Auth requise ──
r = c.post('/api/v2/enterprise/ingest/structured', json={'content': 'x'})
check("auth : 401 sans clé", r.status_code == 401)

# ── 5. Contenu manquant ──
r = c.post('/api/v2/enterprise/ingest/structured', headers=H, json={})
check("contenu manquant : 400", r.status_code == 400)

print(f"\n═══════ RÉSULTAT INTÉGRATION : {pass_count} ✅ / {fail_count} ❌ ═══════")
import sys
sys.exit(1 if fail_count else 0)
