# -*- coding: utf-8 -*-
"""Test du pipeline docling_harmonique — ingestion structurée type Docling."""
import logging
logging.disable(logging.CRITICAL)

from docling_harmonique import (
    parse_markdown, parse_text, parse_document, holomorphize,
    recall_structured, build_hologram, DocumentHarmonique,
)

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

## Déploiement

```
docker compose up -d
```
Le déploiement nécessite Docker et un serveur Linux.
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


# ═══ 1. PARSE MARKDOWN ═══
doc = parse_markdown(MD, source='fiche_produit.md', name='pack_ka')
check("métadonnées : titre + langue fr", doc.metadata['title'] == 'Pack KA Entreprise' and doc.metadata['language'] == 'fr')
check("1 section racine (#)", len(doc.sections) == 1 and doc.sections[0].text == 'Pack KA Entreprise', [s.text for s in doc.sections])
children = doc.sections[0].children
check("3 sections enfants (##)", len(children) == 3, [c.text for c in children])
check("enfants : Formules, Sécurité, Déploiement", [c.text for c in children] == ['Formules et tarifs', 'Sécurité', 'Déploiement'])
sec_formules = children[0]
sec_securite = children[1]
sec_deploiement = children[2]
check("section Formules : item table", len(sec_formules.items) == 1 and sec_formules.items[0].label == 'table')
table = sec_formules.items[0]
check("table : 4 lignes (en-tête + 3)", len(table.children) == 4, len(table.children))
check("table : en-têtes corrects", table.meta.get('headers') == ['Formule', 'Prix / mois', 'Documents', 'Hologrammes'])
check("table : cellule (1,0) = Starter", table.children[1].children[0].text == 'Starter')
check("section Sécurité : liste + paragraphe", any(i.label == 'list_item' for i in sec_securite.items), [i.label for i in sec_securite.items])
check("section Déploiement : item code", any(i.label == 'code' for i in sec_deploiement.items))
check("items plats conservés", len(doc.items) > 0)
check("export JSON lossless", '"schema_name": "HarmoniqueDocument"' in doc.export_json())
check("export markdown conserve les titres", '## Formules et tarifs' in doc.to_markdown())

# ═══ 2. HOLOMORPHISE ═══
facts = holomorphize(doc, secteur='tech', domain='pack_ka')
struct = [f for f in facts if f[1] in ('section_est_sous', 'section_contient', 'item_précède')]
tables = [f for f in facts if f[1] in ('est_valeur_de', 'est_colonne_de')]
check("faits totaux générés", len(facts) >= 25, len(facts))
check("faits structurels (hiérarchie + ordre)", len(struct) >= 8, len(struct))
check("faits de table", len(tables) >= 8, len(tables))
check("hiérarchie : Formules est sous Pack KA", any(f[0] == 'Formules et tarifs' and f[2] == 'Pack KA Entreprise' for f in struct))
check("table : 299 € est valeur de Prix / mois", any(f[0] == '299 €' and f[2] == 'Prix / mois' for f in tables))
check("table : Starter lié à la table", any(f[0] == 'Starter' and f[2] == 'Formule' for f in tables))
check("triplets contenu : AES-256", any('AES-256' in f[0] for f in facts))
check("pas de doublons", len(facts) == len({(f[0].lower(), f[1], f[2].lower()) for f in facts}))

# ═══ 3. RAPPEL STRUCTUREL ═══
q1 = recall_structured(doc, 'quel est le prix de la formule pro ?', top_k=1)
check("recall : question prix → section Formules", q1 and q1[0]['section'] == 'Formules et tarifs', q1[0]['section'] if q1 else None)
check("recall : contient la table complète", q1 and '299 €' in q1[0]['content'])
q2 = recall_structured(doc, 'comment sécuriser les données ?', top_k=1)
check("recall : question sécurité → section Sécurité", q2 and q2[0]['section'] == 'Sécurité', q2[0]['section'] if q2 else None)
q3 = recall_structured(doc, 'de quoi le déploiement a-t-il besoin ?', top_k=1)
check("recall : déploiement → section Déploiement", q3 and q3[0]['section'] == 'Déploiement', q3[0]['section'] if q3 else None)

# ═══ 4. PARSE TEXT (heuristique majuscules) ═══
TXT = """RAPPORT MENSUEL

Le chiffre d'affaires augmente de 12 pour cent.

SÉCURITÉ
Les accès sont journalisés.
"""
d2 = parse_text(TXT, source='rapport.txt')
check("parse_text : titre détecté (MAJUSCULES)", d2.metadata['title'] == 'RAPPORT MENSUEL')
check("parse_text : section SÉCURITÉ", any(s.text == 'SÉCURITÉ' for s in d2.sections))

# ═══ 5. build_hologram (store factice) ═══
class FakeStore:
    def __init__(self):
        self.created = []
        self.facts = []
    def create_hologram(self, **kw):
        self.created.append(kw)
    def add_facts(self, holo_id, facts):
        self.facts = facts

fs = FakeStore()
info = build_hologram(doc, fs, domain='Pack KA')
check("build_hologram : hologramme créé", fs.created and fs.created[0]['name'] == 'Pack KA')
check("build_hologram : faits ajoutés au store", len(fs.facts) == len(facts), len(facts))
check("build_hologram : rapport complet", info['sections'] == 1 and info['items'] > 0)

print(f"\n═══════ RÉSULTAT : {pass_count} ✅ / {fail_count} ❌ ═══════")
import sys
sys.exit(1 if fail_count else 0)
