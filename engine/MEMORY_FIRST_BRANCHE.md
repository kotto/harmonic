# 🌿 BRANCHE memory-first-hybride — L'implémentation immédiate de l'architecture memory-first

**« Le LLM ne sait rien : il formule ce que la mémoire certifie, et se tait quand elle se tait. »**
**Date** : 11/08/2026 — **Auteur** : Univers-Holistique (Kotto Alain) — **Base** : `refondation-thu-2026`

---

## Ce qui est implémenté (vérifié — tests verts)

### 🧠 Le cœur — le pipeline memory-first (`ka_server/services/memory_first.py`)

```
ask(query) → {answer, provenance, confidence, refused, reason}

CONNAISSANCE : la mémoire dorée (HolographicMemory) — les faits (sujet,
              relation, objet) avec leur SOURCE (la provenance)
PONT         : le vocabulaire — LEXICAL, déterministe, exact
              (honnêteté X3 : le φ-spacing ne porte pas le sens)
DÉCISION     : refus STRUCTUREL — jamais de fabrication ; la confiance
              est RAPPORTÉE brute (frontière F6 : « le spectre s'apprend »)
LANGAGE      : la formulation depuis le fait stocké — pas le LLM
```

**Design honnête, calibré sur la réalité du moteur** : le bruit HRR (≈ 1/√512 ≈ 0,044) rend la discrimination inter-entités par résonance non fiable — donc la discrimination est **lexicale** (le vocabulaire), et la résonance est la **confiance intra-entité** (le max de deux sondes : sujet et objet). Les exclusions X3/F6 sont déclarées dans l'API, pas cachées.

### 🔌 Les routes (`ka_server/routes/memory_first.py`)

| Route | Fonction |
|---|---|
| `POST /api/memory-first/ask` | question → réponse avec provenance ou refus (raison donnée) |
| `POST /api/memory-first/store` | faits avec source — apprentissage O(1) |
| `GET /api/memory-first/stats` | faits, vocabulaire, seuil, honnêtetés déclarées |

### 🔗 L'intégration dans `/api/chat` — la mémoire répond AVANT le LLM

Dans la route principale du chat : la couche memory-first est appelée après l'arithmétique émergente et **avant** le LLM — si la mémoire répond (refused=False), la réponse revient avec `provenance` et `code: MEMORY_FIRST_ANSWER` ; le LLM n'est sollicité que quand la mémoire se tait. C'est l'architecture réelle : *le LLM formule, la mémoire certifie*.

### 🌊 Le SaaS (les services quantum-like profitent de l'approche)

| Endpoint | Fonction |
|---|---|
| `POST /v1/memory/ask` | **le RAG déterministe** : question → réponse avec provenance ou refus structurel |
| `POST /v1/memory/store_with_source` | faits avec source — la provenance du RAG |

### ⚡ Le pont agentique — KA, assistant personnel (fonctions du téléphone)

**KA est adapté à l'environnement memory-first** : les fonctions agentiques sont
des FAITS de la mémoire — le plugin natif `ka-actions` (Capacitor, Java) exécute,
la mémoire connaît et archive. L'`ask()` reconnaît les commandes et retourne
`suggested_action` (le téléphone exécute, la mémoire a la provenance).

| Action | Implémentation | Dépendance open-source |
|---|---|---|
| `call` · `sms` · `contacts` | ✅ plugin natif (Java + Intent/Telephony) | **non** — SDK Android |
| `diskSpace` · `battery` · `wifiInfo` | ✅ plugin natif | **non** — SDK Android |
| `openApp` · `listApps` · `deviceInfo` | ✅ plugin natif | **non** — SDK Android |
| `compress` (ZIP, background-compatible) | ✅ **ajouté** — `java.util.zip` (dossier/fichier → ZIP, ratio) | **non** — SDK Android embarque tout |
| Orchestration (reconnaître la commande) | ✅ `detect_action` dans `memory_first.py` (lexical, X3) | **non** — mémoire-d'abord |
| Exécution en background (WorkManager) | 📋 prochaine étape — `compress` est prête à y être branchée | **oui** — AndroidX WorkManager (open-source, standard Jetpack) |
| IA embarquée (raisonnement on-device) | 📋 option — la mémoire répond déjà ; le LLM embarqué reste un choix | **oui, si voulu** — Llama/Gemma/Phi via ExecuTorch/llama.cpp (open-source) |

**Verdict open-source** : les fonctions du téléphone (appeler, SMS, contacts,
espace, batterie, wifi, compression ZIP) sont **natives — aucune dépendance
open-source nécessaire** (le SDK Android les embarque). L'open-source n'est
nécessaire que pour : (1) le **background** (WorkManager — le standard
Jetpack), (2) éventuellement un **LLM embarqué** (aligné avec la philosophie
on-device), (3) les formats exotiques de compression (7z/xz — Apache Commons
Compress), si le besoin existe.

### ✅ Tests (tous verts)

```
ka_server/tests/test_memory_first.py    → 6/6   (provenance, refus, honnêteté)
saas_wave_api/tests/test_api.py         → 15/15 (dont /v1/memory/ask)
ka_server/tests/test_wave_api.py        → 14/14 (régression)
ka_server/tests/test_server_basic.py    → 9/9   (régression — dont /api/chat)
```

### 📚 Le corpus KA dans la mémoire (avec provenance)

`ka_server/tools/seed_memory_first.py` — charge les 14 fichiers `data/vital_ka_*.json`
(91 faits, 8 sources déclarées : KA diseases · OMS 2024 · WHO Maternal · WHO/ICRC
Trauma/ATLS/AHA BLS · WHO HIV/TB · SAM · IMCI · mhGAP) :

```
python -m ka_server.tools.seed_memory_first     # tout le corpus (91 faits)
```

**Le chat mémoire-d'abord vérifié sur le corpus réel** (`smoke_memory_first_medical.py`) :

| Question | Réponse | Source |
|---|---|---|
| « arret cardiaque » | ✅ la conduite BLS | WHO/ICRC, ATLS, AHA BLS 2024 |
| « paludisme » · « traitement du paludisme » | ✅ la conduite | KA diseases |
| « hemorragie » | ✅ HPP — massage, appel | WHO Maternal 2024 |
| « la tuberculose » | ✅ dépistage TB | WHO HIV/TB 2024 |
| « comment reconnaitre une fracture ? » | ✅ immobilisation | ATLS |
| « recette de pizza » | ❌ **refus** — jamais de fabrication | — |

**Deux bugs réels attrapés par le smoke test** (et corrigés) :
1. **Interblocage de restauration** — `_get_memory()` tenait le verrou et
   appelait `_store` qui le ré-acquérait (verrou non réentrant) : refactor en
   `_ensure_memory_unlocked()` + `_store_unlocked()` ;
2. **Matcher trop étroit** — sous-chaîne dans un seul sens + accents :
   « hémorragie » vs « hemorragie » ; corrigé par la normalisation sans
   accents et le double sens (l'entité dans la requête OU la requête dans
   l'entité) ; le seuil de refus est passé à −0,05 (l'ancrage lexical est
   la récupération — la résonance est la confiance rapportée, F6).

---

## Les prochaines étapes (documentées, pas faites à l'aveugle)

| Étape | Produit | Contenu |
|---|---|---|
| 1 · **La provenance dans le chat mobile** | KA Mobile (`www/ka_index.html` ~l.1010) | Afficher la ligne « source » sous la réponse quand `data.provenance` est présent ; afficher le refus (la machine qui se tait) — le conteneur du chat doit être exploré avant l'édition |
| 2 · **La vue audit Enterprise** | KA Enterprise (`ka_server/static/enterprise.html`) | Le journal des réponses avec provenance + le compteur de refus — l'audit comme produit |
| 3 · **Le MaaS durci** | SaaS | Isolation multi-tenant (une mémoire par client), quotas mémoire, plans de rétention avec l'oubli doré (t^−0,618 — GDPR par design) |
| 4 · **Le corpus médical/KA** | Vital KA | Charger les faits du corpus (définitions, conduites d'urgence) avec source — le savoir certifié du chat |
| 5 · **La confiance apprise** | Vital KA | La frontière F6 : l'encodeur appris (spectre appris) qui améliore la confiance au lieu de la rapporter brute |

---

## Les bornes (inchangées, publiées)

- **X3** : le pont sémantique est lexical — le φ-spacing ne porte pas le sens ;
- **F6** : la confiance est rapportée brute — le spectre s'apprend ;
- **T\* / Zeno** : les tests de la ressource — les services tiennent sans eux (computationnels), le récit gagne tout avec eux ;
- Le LLM n'est pas remplacé : il est repositionné — couche langage.

---

*Branche memory-first-hybride — FIN — le cœur est en place et testé (6+15+14+9 tests verts), l'intégration chat est réelle (la mémoire répond avant le LLM), le SaaS profite de l'approche (/v1/memory/ask), et les étapes UI (mobile, Enterprise) sont documentées pour ne pas être faites à l'aveugle*
