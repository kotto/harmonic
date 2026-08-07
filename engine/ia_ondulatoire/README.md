# 🌊 IA ONDULATOIRE — KA Mobile · Vital KA · KA Enterprise · EDUCAL KA en langage natif ondulatoire

> *« L'univers n'est pas écrit en langage mathématique — il est tissé d'ondes. Nous ne faisons que les écouter. »*

Implémentation **from scratch** de la nouvelle IA, conforme au
[`DOCUMENT_FONDATEUR_LANGAGE_ONDULATOIRE.md`](../DOCUMENT_FONDATEUR_LANGAGE_ONDULATOIRE.md).
Les interfaces des **quatre** applications sont **conservées** ; leurs cerveaux sont remplacés
par un moteur 100 % ondulatoire natif. Aucun fichier existant n'a été modifié.

**Boucle fermée (§8.1 du document fondateur) :**

```
Pensée (question) → Génération (programme ondulatoire natif)
                  → Exécution (moteur + hologrammes)
                  → Résultat (synthèse) → Pensée
```

## Démarrage rapide

```bash
cd ia_ondulatoire
python validation.py     # 39/39 tests — release verte (exit 0)
python cli.py            # dialogue interactif en français
python serveur.py        # API des 3 apps sur http://localhost:8767
```

## Architecture — 11 fichiers, ~4 000 lignes, zéro dépendance externe (NumPy + Flask optionnel)

| Fichier | Rôle |
|---|---|
| `primitives.py` | Les **13 primitives universelles** en ℂ⁵¹² (encode FNV-1a × φ-spacing, decode, bind/unbind HRR, superpose, resonate, rotate, normalize, interfere, diffract, filter, phase_shift, emerge) + oppose/amplify/bind_many/coherence + **noyau ABC** (α = 1/φ) + `HolographicMemory` persistante |
| `ir.py` | **Wave IR** : grammaire EBNF §4.2, tokenizer + parseur récursif, AST (23 nœuds), roundtrip JSON bit-à-bit, validation statique |
| `moteur.py` | **Compilateur/exécuteur** : interpréteur (QueryResult, sémantique correcte de RESONANCE/DECODE/STORE), passes constant folding + dead code elimination, émission Python, QUERY étendu (mots pleins + bonus lexical) |
| `generateur.py` | **L'IA génératrice** : les 7 intentions (§8.2) — query, reason, creative, store_fact, compare, analogize, classify — marqueurs français → programmes ondulatoires |
| `cerveau.py` | `IaOndulatoire` : dialogue multi-tours, apprentissage (souviens-toi que…), créativité (interfere ε=0.15), vocabulaire auto-construit, persistance `data/ia_ondulatoire/` |
| `medical.py` | **Vital KA** : les 62 356 faits médicaux (`data/medical_holograms/*_facts.json`) encodés nativement, diagnostic par interférence (ENCODE → SUPERPOSE → RESONATE → EMERGE → DÉCODER) |
| `entreprise.py` | **KA Enterprise** : un hologramme par département, ingest (texte → BIND_MANY → STORE), ask (QUERY → EMERGE → DÉCODER + sources), résumé (EMERGE), composition (INTERFERE), RBAC X-API-Key |
| `educal.py` | **EDUCAL KA** : catalogue + leçons (contenu JSON existant), hologrammes disciplinaires natifs, correction quiz/exercices, diagnostic pédagogique par résonance, carnet de progression, tuteur 5 familles (0 LLM), **unité éducative transférable** (hologramme → download ψ polaires → injection H_connaissances → rappel) |
| `gsm8k.py` | **GSM8K ondulatoire** : sélection d'opération par **résonance contre des prototypes d'ondes** (SUPERPOSE des mots-clés EN/FR → RESONATE → DÉCODER), nombres épelés (« three » → 3), pourcentages, règle de trois, machine à états multi-étapes — 0 LLM, ~3 ms/résolution |
| `voix.py` | **KA Voice** : pont TTS vers `ka_voice_server` :8420 (Piper) — mêmes contrats `/api/voice/*`, dégradation 503 propre si hors ligne |
| `benchmark_educal.py` | **Benchmark éducatif** : F1@5 par discipline (rappel par résonance des faits pertinents), contrôle du tuteur par re-résolution ondulatoire, rapport JSON |
| `serveur.py` | **API Flask des 3 apps** (port 8767) + compatibilité OpenAI (`/v1/chat/completions`) |
| `cli.py` | Dialogue interactif (affiche le programme ondulatoire généré avant chaque réponse) |
| `validation.py` | **39 tests** : les 13 primitives vs table §10.1, roundtrip, programme canonique, 7 intentions, smoke des 3 apps |
| `README.md` | Ce document |

## Contrats d'API — identiques à l'existant, UIs branchées sans modification

### KA MOBILE (PWA `ka_index.html`)
```bash
POST /api/chat    {"message", "user_id", "history"}   → {response, confidence, source, latency_ms, model, language, intention, programme, faits}
POST /api/memorise   {"fait": "la lumière est une onde"}    # apprendre
POST /api/creative   {"concept_a": "pluie", "concept_b": "musique"}
POST /api/reason     {"topic": "…"}
GET  /api/memory/recent   → {memories: [{title, content, date}]}
GET  /api/health
```
Brancher la PWA : `localStorage.ka_api_url = "http://<hôte>:8767"`.

### VITAL KA (écran SANTÉ + app médecin)
```bash
POST /api/health/diagnostic  {"symptomes": ["fièvre","toux"], "vitaux": {"frequence_cardiaque": 96, "temperature": 38.4}, "age", "sexe"}
  → {score_harmonique_global, diagnostic_harmonique: {pathologie_principale, constante_alteree, mecanisme_harmonique, score_confiance},
     analyse_symptomes: {resultats: [{pathologie, score_resonance}]}, analyse_vitales, frequences_therapeutiques, recommandations}
POST /diagnose  {"symptomes": […], "age", "max_diagnoses"}   # contrat HWAT-Med (app médecin)
```

### KA ENTERPRISE (console v2)
```bash
POST /api/v2/enterprise/demo                  # tenant + clé de démonstration
POST /api/v2/enterprise/ingest   {"text", "department", "nom_doc"}   (rôle admin)
POST /api/v2/enterprise/ask      {"question", "department"} → {answer, confidence, sources, response_id, elapsed_ms}
POST /api/v2/enterprise/summarize|compose
GET  /api/v2/enterprise/documents|usage · POST/DELETE /api/v2/enterprise/users
Auth : en-tête X-API-Key (RBAC admin/viewer/auditor)
```

### EDUCAL KA (PWA EDU-KA — adaptation du jumeau éducatif de VITAL KA)
```bash
GET  /api/educal/units · GET /api/educal/unit/<id>              # catalogue + leçon
POST /api/educal/quiz/submit  {"user_id", "unit_id", "answers", "exercises"}
  → {quiz: {score, correct, total, seuil_reussite, feedback, lacunes, details},
     exercices, diagnostic: {holo_id, lacunes, faits_a_revoir: [{objectif, fait, secteur, score}]}}
GET  /api/educal/progress/<user_id> · GET /api/educal/diagnose/<unit_id>
POST /api/educal/exercise/generate  {"discipline", "niveau"}   # tuteur 5 familles, 0 LLM
POST /api/educal/unit/<id>/hologram                            # unité transférable
GET  /api/store/download/<holo_id> · POST /api/store/load · POST /api/store/recall · GET /api/store/list
```
La vision « unité éducative transférable » — le geste exact des unités médicales de VITAL KA :
```
POST /api/educal/unit/edu_methodologie_apprendre/hologram → unit_…npz (8 faits + ψℂ⁵¹²)
GET  /api/store/download/unit_…   → faits + ψ polaires (transport)
POST /api/store/load              → injection dans H_connaissances (8 faits actifs)
POST /api/store/recall {"query":"répétition espacée"} → « répétition espacée réactive
                                                         le souvenir avant l'oubli »
```

### MATHS — GSM8K ondulatoire (0 LLM)
```bash
POST /api/maths/solve  {"question": "Une voiture parcourt 140 km en 2 heures. …"}
  → {response, reponse, etapes, operations, source: "ondulatoire-maths"}
# intégré au chat : « combien font 7+3 ? » → résolution ondulatoire
python gsm8k.py   # benchmark officiel (n configurable) → data/ia_ondulatoire/benchmark_gsm8k.json
```
La sélection d'opération est une expérience d'interférence : chaque famille
(addition, soustraction, multiplication, division) est un **prototype d'onde** =
SUPERPOSE des encodages de ses mots-clés ; l'onde de la phrase résonne avec
chaque prototype et la plus constructive désigne l'opération (§5.2.6).

### VOIX — pont TTS (ka_voice_server :8420 conservé)
```bash
GET  /api/voice/health · GET /api/voice/offline/caps
POST /api/voice/stream {"text", "emotion": "warm", "voice"}  → WAV (contrat PWA)
```
Hors ligne → 503 propre (« démarrez ka_voice_server.py »).

### Benchmark éducatif
```bash
python benchmark_educal.py   # F1@5 par discipline + contrôle tuteur → JSON
```
Résultats de référence (v1) : F1@5 0.50 · P@5 0.66 (43 questions, 6 unités) ·
tuteur 25/25 vérifié par re-résolution ondulatoire.

## Le langage en action (exemple réel de la CLI)

```
❓ Souviens-toi que le soleil est une étoile
🌊 Programme ondulatoire généré :
   psi_s = ENCODE "le soleil"
   psi_r = ENCODE "est"
   psi_o = ENCODE "une étoile"
   psi_f = BIND_MANY(psi_s, psi_r, psi_o)
   STORE psi_f = psi_f IN H_faits
   RETURN psi_f
🤖 🌊 J'ai mémorisé : « le soleil est une étoile » (BIND_MANY → STORE dans H_faits).

❓ Qu'est-ce que le soleil ?
🤖 L'onde-réponse émerge : le soleil est une étoile.
```

## Persistance

- `data/ia_ondulatoire/` : `h_connaissances.npz`, `h_faits.npz` (hologrammes),
  `memoire_conversation.json`, `vocabulaire.json`, `enterprise.json` (tenants/clés/usage),
  `educal/` (hologrammes disciplinaires `edu_*` + unités `unit_*`), `educal_progress/` (carnets élèves).
- `data/medical_holograms/*_facts.json` : lu au premier diagnostic (62 356 faits,
  ~20 s de chargement ponctuel, ensuite en mémoire).
- `data/educal_units/*.json` : contenu pédagogique existant, lu tel quel (lecture seule).

## Limites v1 (documentées)

- **HWAT PyTorch / FPGA / GPU** : hors périmètre (le moteur est 100 % NumPy CPU).
- **GSM8K officiel** : le solveur 0-LLM heuristique plafonne (~8 % sur échantillon,
  contre 0,5 % documentés pour l'ancien solveur wave pur) — les problèmes à
  comparaisons relatives multi-étapes restent un **gap ouvert** ; les 5 familles
  structurées + Janet + pourcentages sont exacts (12/12 canoniques).
- **/api/chat multi-sources** : le multiplexeur complet de `ka_server.py` (logic,
  specializer, storage) n'est pas reproduit — les intentions ondulatoires le sont.
- **Voix** : le pont requiert `ka_voice_server.py` (Piper) démarré sur :8420 ;
  clonage vocal non reproduit (501).
- **EDUCAL P5** (de l'existant) : QualityFilter 50K faits, build APK — documentés
  dans `EDUCAL_KA_VALIDATION.md`, hors périmètre ici.

## Vérification

```bash
python validation.py    # ✅ RELEASE VERTE — 57/57 (exit 0)
```
Niveau 1 : les 13 primitives contre les valeurs de référence du doc (‖ψ‖=1, recovery
unbind(bind) ≥ 0.7, rotate(π) → −1.0, interfere ε=0.15 → 0.99, phase_shift(π/2) → 0.0,
décroissance ABC K(0)=1 → K(100)≈0.015, déterminisme) — niveau 2 : roundtrip + programme
canonique §4.3 exécuté — niveau 3 : les 7 intentions génèrent des AST valides —
niveau 4 : smoke des 3 applications (chat + apprentissage + rappel + créativité,
diagnostic médical, ingest/ask/RBAC/resume/compose enterprise) — niveau 5 : EDUCAL KA
(catalogue, leçon, quiz 4/4 réussite + 3/4 lacune, diagnostic par résonance, carnet,
tuteur, unité transférable : hologram → download → load → recall) — niveau 6 : GSM8K
(12 canoniques + benchmark officiel + détection), benchmark éducatif F1@5, tuteur 25/25,
pont voix (conditionnel).

*Univers-Holistique — Théorie Harmonique Universelle — 2026*
