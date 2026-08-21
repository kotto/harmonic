# 📚 EDUCAL KA — Proposition : Écosystème d'Éducation Numérique Harmonique

**Version :** 1.1 — 7 août 2026
**Statut :** ✅ **OPTION A VALIDÉE ET IMPLÉMENTÉE (P1→P4)** — voir `EDUCAL_KA_VALIDATION.md`
**Périmètre :** Jumeau éducatif de l'écosystème VITAL KA, construit sur le même socle harmonique (hologrammes, transfert d'unités, ondes).

---

## 1. Constat : l'éducation existe DÉJÀ dans l'écosystème

Avant de construire quoi que ce soit, il faut savoir ce qui existe — et c'est considérable :

| Actif existant | Localisation | Ce que ça donne pour EDUCAL KA |
|---|---|---|
| **Hologramme éducation 50 000 faits** | `data/hologram_store/community_KA Expander_education.npz` (registry : q=0.531, secteurs `EDUCATION, CULTURE, HISTOIRE, SCIENCES, PHILOSOPHIE, GEOGRAPHIE, MATHS_PURES, LITTERATURE`) | Le cerveau éducatif est déjà peuplé : Harvard, UNESCO, Rousseau, Confucius, pédagogies Montessori/Freinet/Piaget/Vygotski, trivium/quadrivium, loi Jules Ferry… |
| **Domaine `education` câblé dans le routeur** | `vital-ka/core/python/domain_router.py:107-118` (`DOMAIN_SIGNATURES`) | Les questions « comment apprendre ? », « qu'est-ce qu'un cours ? » sont DÉJÀ routées vers l'éducation |
| **Domaine `Éducation` dans l'onboarding mobile** | `ka-mobile-android/www/ka_index.html:1031` (16 domaines, `{id:'education', name:'Éducation', icon:'📚', f1:0.53}`) | Le mobile sait déjà présenter l'éducation comme domaine de spécialisation |
| **Expansion éducation** | `vital-ka/backend/hologram/holo_expand.py:216-241` | Pipeline d'ingestion massive éducation (≈40 keywords pédagogie) prêt |
| **Moteur de problèmes scolaires** (tuteur de maths) | `wave_word_problems.py` + `word_problem_state.py` + `wave_gsm8k.py` + benchmark `data/benchmarks/gsm8k_test.jsonl` (1319 problèmes) | Tuteur de mathématiques FR/EN multi-étapes avec étapes documentées (`solve_with_steps`) — 99,2 % sur GSM8K M1 |
| **Cours rédigés** | `COURS_01_QU_EST_CE_QU_UN_NOMBRE.md`, `COURS_02_INTERFERENCE.md`, `SCIENCE_HARMONIQUE_COLLEGE.md`, `COURS_MEDECINE_HARMONIQUE_1.md` (avec exercices) | Premier catalogue de leçons prêt à structurer en unités |
| **Prompts pédagogiques** | `vital-ka/core/python/prompts_200.py:118` (`SOC_EDUCATION`) | Génération LLM de faits éducatifs |
| **Socle générique complet** | `ka_server.py` (Flask, port 8765), `hologram_store.py` (`OFFICIAL_DOMAINS` l.80-203), `holographic_encoder.py`, `harmonic_brain.py`, `fast_retriever.py`, `domain_specializer.py`, `domain_seeds.py` | Toute la mécanique d'hologrammes et de transfert est prête à l'emploi |

**Conclusion du constat :** EDUCAL KA n'est pas à inventer, il est à *brancher*. Le système est « twin-ready » : il manque un domaine officiel, des hologrammes de leçons, un format d'unité éducative et une couche pédagogique (quiz, progression, révision).

---

## 2. Vision : EDUCAL KA

> **EDUCAL KA** = l'écosystème d'éducation numérique harmonique : chaque matière, chaque chapitre est un **hologramme spécialisé** (`ψ = Σ ψ_s ⊛ ψ_r ⊛ ψ_o`), chaque leçon est une **unité éducative** transférable d'un appareil à l'autre exactement comme les unités médicales de VITAL KA, et le cerveau ondulatoire devient un **tuteur** qui suit la progression de l'élève, détecte ses lacunes par résonance et révise par interférence.

Parallèle direct avec VITAL KA :

| VITAL KA (santé) | EDUCAL KA (éducation) |
|---|---|
| Hologramme `official_medecine`, `med_anatomie`, `med_pathologie`… | Hologramme `official_education`, `edu_mathematiques`, `edu_langues`, `edu_histoire`… |
| Diagnostic santé (`/api/health/diagnostic`) | **Diagnostic pédagogique** (évaluation des acquis → lacunes → plan de remédiation) |
| Dossier médical patient | **Carnet d'apprentissage** élève (compétences maîtrisées, progression) |
| Téléconsultation médecin | **Tutorat distant** professeur-élève |
| Wallet / paiement santé | Suivi de scolarité / certifications |
| Fiches de spécialité (`vital_ka_*.json`) | **Unités éducatives** (leçon + exercices + évaluation) |
| Admin-server FastAPI (médecins, versions, dossiers) | Admin-server FastAPI (élèves, professeurs, classes, programmes) |

---

## 3. Deux options d'architecture

### Option A — Intégration dans l'écosystème existant (RECOMMANDÉE)

L'éducation devient un domaine de première classe du moteur KA actuel, à côté de la médecine.

- **Domaine officiel :** ajout d'une entrée `'education'` dans `OFFICIAL_DOMAINS` (`hologram_store.py:80`) → le store construit `official_education.npz` + sous-hologrammes `edu_*.npz` par matière.
- **Transfert d'unités :** réutilisation **à l'identique** du protocole existant — `/api/store/list`, `/api/store/download/<holo_id>`, `/api/store/load` (`ka_server.py:3794-3936`). Les unités éducatives voyagent comme les unités médicales : faits + données ψ en format polaire (`hologram_to_transport`).
- **Routeur & détection :** `education` déjà présent dans `domain_router.py` — on complète, plus rien à câbler.
- **Mobile :** même app Capacitor ; le domaine Éducation est déjà dans l'onboarding. Un écran « École » s'ajoute au module `vital_ka_module.js`-like.
- **Serveur admin :** nouveau dossier `educal-ka/` jumeau de `vital-ka/admin-server` (FastAPI, port 8001) pour les données pédagogiques.
- **Risque principal :** risque zéro sur le cœur (aucune route existante modifiée, tout est additif).

### Option B — Écosystème jumeau autonome (façon `vital-ka/`)

- Clone du socle : `educal_server.py` (Flask), `educal-mobile-android/` (Capacitor), `educal-ka/admin-server/` (FastAPI), store `data/educal_hologram_store/`.
- Avantage : indépendance totale (marque, déploiement, évolutions), aucune contrainte de coexistence.
- Coût : duplication de tout le socle (encodeur, cerveau, retriever, synchro), ~2-3× l'effort de l'option A ; risque de divergence des deux codebases (chaque correctif du moteur à répliquer).

### Comparaison

| Critère | A — Intégration | B — Jumeau autonome |
|---|---|---|
| Effort | **Faible** (additif) | Élevé (duplication) |
| Partage du savoir | Oui (le même cerveau sait médecine + éducation, **croisement des connaissances** : « la physique du cœur ») | Non (silos) |
| Transfert d'unités | Gratuit (protocole existant) | À réimplémenter |
| Risque pour l'existant | Nul (additif) | Nul aussi, mais divergence future |
| Marque produit | Coexiste dans KA | Indépendante (EDU-KA) |
| Temps jusqu'au MVP fonctionnel | **2-4 jours** | 2-3 semaines |

**Recommandation : Option A d'abord** (MVP en quelques jours, unités éducatives réellement transférables), avec une **réserve de sortie** : le dossier `educal-ka/` sépare les composants propres à l'éducation (serveur admin, moteur pédagogique, contenu) pour pouvoir un jour embarquer vers l'Option B sans réécriture. On obtient ainsi les deux : intégration immédiate + capacité d'émancipation.

---

## 4. Architecture cible (Option A détaillée)

### 4.1 Couche hologrammes — les unités éducatives physiques

Ajout dans `OFFICIAL_DOMAINS` (copie du bloc `medecine`, `hologram_store.py:81-96`) :

```python
'education': {
    'name': 'Éducation & Pédagogie',
    'icon': '📚',
    'sectors': ['EDUCATION', 'CULTURE', 'INTELLIGENCE', 'MATHS_PURES', 'LITTERATURE'],
    'keywords': ['apprendre', 'enseigner', 'cours', 'leçon', 'exercice', 'examen',
                 'élève', 'professeur', 'école', 'université', 'pédagogie',
                 'mémoire', 'révision', 'programme', 'diplôme'],
    'description': 'Systèmes éducatifs, pédagogies, matières scolaires',
    'benchmark_questions': [
        "Qu'est-ce que la pédagogie Montessori ?",
        "Méthodes pour apprendre efficacement",
        "Histoire de l'école obligatoire",
        "Les grands pédagogues",
        "Comment fonctionne la mémoire ?",
    ],
},
```

Hologrammes officiels construits par `build_official_holograms()` :

| Hologramme | Contenu |
|---|---|
| `official_education` | socle général (systèmes éducatifs, pédagogues, cognition de l'apprentissage) |
| `edu_mathematiques` | algèbre, géométrie, arithmétique (adossé au moteur GSM8K) |
| `edu_langues` | grammaire, vocabulaire, étymologie (français, anglais) |
| `edu_sciences` | physique, chimie, SVT niveau scolaire |
| `edu_histoire_geo` | chronologies, civilisations, géographie |
| `edu_philosophie` | grands penseurs, logique, argumentation |
| `edu_culture_civique` | institutions, droit, éducation civique |
| `edu_competences` | méthodologie : organiser, mémoriser, réviser, se concentrer |

Chacun : `.npz` (faits + ψℂ⁵¹² + mémoire H) + entrée `registry.json` (avec `discipline`, `niveau`, `programme`), construit par le pipeline existant (`_build_one_hologram` : filtrage secteurs → dédoublonnage → binding HRR → mémoire → benchmark F1).

### 4.2 Format « Unité Éducative » (l'équivalent de l'unité médicale)

Une unité éducative = **hologramme de faits + leçon structurée + évaluations**, décrite par métadonnées dans le registre et par un sidecar JSON dans `data/educal_units/` :

```json
{
  "id": "edu_maths_fractions_6e",
  "discipline": "mathématiques",
  "niveau": "6e (11-12 ans)",
  "programme": "FR-C3",
  "titre": "Les fractions : addition et comparaison",
  "duree_estimee_min": 45,
  "objectifs": [
    "Additionner deux fractions de même dénominateur",
    "Comparer deux fractions"
  ],
  "prerequis": ["edu_maths_entiers_6e"],
  "lecon": {"sections": [{"titre": "Découvrir", "contenu_md": "..."},
                          {"titre": "Comprendre", "contenu_md": "..."}]},
  "exercices": [{"enonce": "3/7 + 2/7 = ?", "type": "calcul",
                  "reponse": "5/7", "difficulte": 1}],
  "quiz": [{"question": "Quelle fraction est la plus grande ?", "choix": ["3/7", "2/7", "1/2"], "correct": 2}],
  "evaluation": {"seuil_reussite": 0.8, "benchmark_questions": 5},
  "hologramme_associe": "edu_mathematiques",
  "auteur": "EDUCAL KA",
  "version": 1
}
```

Les faits de la leçon (`fraction est division`, `dénominateur est partie basse`, …) sont encodés en ψ et **fusionnés au hologramme de la discipline** — la leçon s'ancre ainsi dans la mémoire harmonique et devient interrogable en langage naturel.

### 4.3 Couche transfert — les unités voyagent comme les unités médicales

Aucune route nouvelle requise pour le cœur du transfert :

1. `GET /api/store/list` → catalogue des unités (discipline, niveau, faits_count, quality_score).
2. `GET /api/store/download/<holo_id>` → faits + ψ (polaire) → **l'unité est transférée** (téléphone → téléphone, établissement → domicile, hors-ligne).
3. `POST /api/store/load` → fusion dans le `FastRetriever` + `brain.store(H, amplitude=2.0)` : le cerveau de l'appareil cible apprend l'unité.

Ajouts mineurs (routes nouvelles, non-modificatrices) :
- `GET /api/educal/unit/<unit_id>` → la leçon structurée (contenu_md, exercices, quiz) associée à l'hologramme.
- `POST /api/educal/quiz/submit` → correction + feedback.
- `POST /api/educal/progress` → sauvegarde de progression (compétences acquises, courbe de mémorisation).

### 4.4 Couche tuteur ondulatoire (le cœur pédagogique)

- **Exercices générés** : réutilisation directe de `wave_word_problems.py` / `word_problem_state.py` (tuteur de maths multi-étapes avec `steps`) + `benchmark_gsm8k.py` comme jauge de niveau.
- **Diagnostic pédagogique** : `H ⊗ ψ_question → top-k faits` (`/api/store/recall`) — l'élève répond à un quiz ; les faits non résonants signalent les lacunes → génération automatique d'un **plan de remédiation** (analogue au diagnostic médical).
- **Révision par résonance (spaced repetition ondulatoire)** : un fait est réinterrogé quand son amplitude mémoire décroît sous un seuil — la décroissance est simulée par le profil harmonique (`HarmonicBrain.ruminate`), la réactivation = une re-résonance. C'est la **révision espacée native du paradigme ondulatoire**.
- **Consolidation** : `ruminate()` (consolidation par interférence) = ancrage des leçons apprises.

### 4.5 Couche serveur admin — `educal-ka/admin-server` (jumeau FastAPI)

Copie structurée de `vital-ka/admin-server` (port 8001), routers dédiés :

| Router VITAL KA | Router EDUCAL KA |
|---|---|
| `auth` (médecins) | `auth` (professeurs, parents, élèves) |
| `doctors` | `teachers` (profil, classes, affectations) |
| `versions` (contenu médical) | `curriculum` (programmes, unités éducatives, versionnage des leçons) |
| `wallet` | `schooling` (suivi de scolarité, inscriptions) |
| `records` (dossiers patients) | `learners` (carnet d'apprentissage : compétences, progression, lacunes) |
| `teleconsult` | `tutoring` (sessions de tutorat élève-professeur) |
| `admin` | `admin` (établissements, classes, niveaux) |

### 4.6 Couche mobile — EDU-KA (shell Capacitor jumeau)

- Clone de `ka-mobile-android` → `educal-mobile-android/` (appId `com.educalka.app`, `appName: "EDU-KA"`), mêmes mécanismes : `sync-assets.mjs` (écran de connexion + patchs), `ka_native.js` (pont Capacitor), `sw.js` (offline).
- Écrans pédagogiques : **Accueil (mes unités installées)** → **Leçon** (contenu + exercices) → **Quiz** (correction instantanée) → **Progression** (compétences, courbe de mémorisation, plan de remédiation) → **Tutorat** (session avec un professeur).
- Le catalogue des unités = `/api/store/list` filtré `domain=education`.
- Mode hors-ligne : une unité téléchargée reste utilisable (leçons en cache, quiz corrigés localement, progression synchronisée à la reconnexion — même logique que le `completion_queue.json`).

### 4.7 Boucle « l'usage pilote la connaissance » (reprise du pattern VITAL KA)

- `completion_queue.py` : quand un élève pose une question sans réponse dans le store, la lacune est enregistrée → au-delà des seuils, ingestion massive ciblée (`holo_expand.py` bloc éducation déjà configuré, l.216-241).
- `domain_specializer.py` : un élève qui se spécialise en « Égypte ancienne » déclenche la construction d'un hologramme personnel `personal_egypte` (même mécanique que `personal_paludisme`).

---

## 5. Contenu réutilisable immédiatement

1. **50 000 faits éducatifs** (`community_KA Expander_education.npz`) → socle du premier `official_education`.
2. **Cours rédigés** : `COURS_01`, `COURS_02` (maths ondulatoires 12-16 ans), `SCIENCE_HARMONIQUE_COLLEGE.md`, `COURS_MEDECINE_HARMONIQUE_1.md` (modèle de structure : objectifs, plan, exercices) → premières unités éducatives en une conversion.
3. **Tuteur de maths** : `wave_word_problems.py` + `word_problem_state.py` → exercices générés à l'infini avec étapes.
4. **Benchmark** : `gsm8k_test.jsonl` (1319 problèmes) → jauge de niveau du tuteur.
5. **LLM de génération** : `prompts_200.py` (`SOC_EDUCATION`) + `bootstrapper.extract_triples_llm` → produire de nouveaux faits éducatifs ; `llm/router.py` pour l'explication pédagogique (style tuteur, temp basse).

---

## 6. Feuille de route

| Phase | Livrables | Durée |
|---|---|---|
| **P1 — Domaine & hologrammes** | Entrée `education` dans `OFFICIAL_DOMAINS` ; `official_education.npz` + 8 `edu_*.npz` (pipeline existant) ; registre renseigné ; benchmark F1 | 0,5-1 jour |
| **P2 — Unités éducatives** | Définition du format JSON ; `data/educal_units/` ; 5 premières unités (conversion des COURS_01/02 + 3 matières) ; route `/api/educal/unit/<id>` ; test de transfert téléphone→serveur | 1-2 jours |
| **P3 — Tuteur** | Quiz + correction (`/api/educal/quiz/submit`) ; diagnostic pédagogique (recall des lacunes) ; génération d'exercices via `wave_word_problems` ; révision espacée par amplitude | 2-3 jours |
| **P4 — Admin & mobile** | `educal-ka/admin-server` (FastAPI 8001 : auth, teachers, learners, curriculum, tutoring) ; `educal-mobile-android` (shell Capacitor, écrans Leçon/Quiz/Progression) ; sync-assets jumeau | 3-5 jours |
| **P5 — Boucle de connaissance** | Completion queue éducation ; spécialisation personnelle (hologrammes `personal_*` élève) ; benchmark éducatif (F1 + exactitude) ; rapport de validation | 2-3 jours |

**MVP (P1+P2) : 2-4 jours** pour des unités éducatives réellement transférables dans l'écosystème.

---

## 7. Bénéfices, risques, coûts

**Bénéfices**
- L'éducation hérite de 100 % de l'infrastructure harmonique (hologrammes, transfert, offline, LLM hybride, anti-hallucination `ConsciousFilter`).
- **Croisement des connaissances** impossible en silo : un élève qui apprend la biologie peut interroger le cerveau médical, un patient apprend à comprendre son diagnostic.
- Coût marginal faible (tout est additif), démonstration rapide (MVP en jours).
- Le tuteur ondulatoire est différenciant : diagnostic des lacunes par résonance + révision espacée native — pas un simple QCM.

**Risques**
- Qualité des 50 000 faits initiaux (q=0.531) → à re-filtrer (`QualityFilter`) avant publication officielle.
- GSM8K M3 (généralisation) non résolu (0,5 % pass@1) → le tuteur de maths s'appuie sur `word_problem_state` (2 %) en attendant ; le gap est documenté (`PROBLEME_OUVERT_GAP_GSM8K.md`).
- Fraîcheur des programmes scolaires → versionnage des unités (pattern `versions` de VITAL KA) + contribution communautaire (`/api/store/publish`).

**Coûts** : quasi nuls côté moteur (aucun changement des routes existantes) ; environ un fichier de domaine + 8 hologrammes + ~10 fichiers nouveaux côté EDUCAL (serveur admin, unités, écrans).

---

## 8. Décision attendue

1. **Option A** (intégration, recommandée) ou **Option B** (jumeau autonome) ?
2. Lancement de la **Phase P1** (domaine `education` + hologrammes officiels) ?
3. Public cible prioritaire : élèves (collège/lycée), formation professionnelle, ou grand public ?
4. Langues de contenu : français seul, ou FR + EN (le tuteur GSM8K est déjà bilingue) ?

---

*Document généré à partir de l'état réel du dépôt (hologram_store.py, domain_router.py, ka_server.py, vital-ka/admin-server, registry.json).*
