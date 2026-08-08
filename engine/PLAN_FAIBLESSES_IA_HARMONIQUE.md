# FAIBLESSES IDENTIFIÉES DE L'IA HARMONIQUE + PLAN DE RÉSOLUTION
**Date** : 08/08/2026 — **Auteur** : ZCode (audit des sessions de vérification)

Ce document consolide TOUTES les réserves formulées sur l'état de l'IA
harmonique (moteur ondulatoire + théorie) et propose un plan de résolution
priorisé, avec critères de succès mesurables pour chaque action.

---

## PARTIE A — INVENTAIRE DES FAIBLESSES (par gravité)

### A1. Fondation théorique — la numérologie ne tient pas (critique)
| # | Réserve (chiffrée) | Source |
|---|---|---|
| A1.1 | α : p = 0,0785 (calibration 2000 cibles) — non significatif au seuil 5 % ; p_eff ≈ 0,91 après correction pour ~30 observables (Bonferroni : 0,0017 requis) | `analyse_pvalue_harmonique.py` |
| A1.2 | Le treillis contient une expression de POIDS 15 (plus simple que la formule, poids 19) qui approxime α mieux (1,64e-7) — α n'est pas un point exceptionnel | idem |
| A1.3 | GAGUT = 6π⁵ : p = 0,70 — coïncidence banale ; une approximation 20× meilleure existe (9,1e-7) | idem |
| A1.4 | α est une approximation, pas une loi : écart 2,4e-7 vs barre d'erreur CODATA 1,5e-10 — les 3 derniers chiffres diffèrent mesurablement | vérification directe |
| A1.5 | Coefficients SEMF non dérivables de φ/π/e : précision requise ±0,05 % (aV ±1 % → RMS 26 MeV) vs maille du treillis 1-3 % — impossibilité mathématique | `analyse_sensibilite_semf.py` |

### A2. Cœur du moteur — l'encodage ondulatoire n'a JAMAIS été testé contre le hasard (critique)
| # | Réserve | Détail |
|---|---|---|
| A2.1 | Aucun test ne démontre que l'encode FNV-1a × φ-spacing + HRR bat un hash aléatoire sur des tâches de similarité sémantique | les 13 primitives sont une application d'HRR (Plate 1995) — connu, pas nouveau ; la question est : apportent-elles un signal mesurable ? |
| A2.2 | Les 60/60 de l'Arena V2 sont auto-référentiels : épreuves construites par nous, pas de benchmark externe reconnu (pas de MMLU, MATH, HumanEval, pas de classement LM Arena réel) | `arena_v2_ondulatoire.py` |

### A3. Cerveau conversationnel — confiance non calibrée (majeur)
| # | Réserve | Détail |
|---|---|---|
| A3.1 | Confiance non calibrée : les réponses poétisées partent avec confiance 0,5-0,9 sans source vérifiable ; pas de courbe calibration (confiance vs précision réelle) | `cerveau.py::_synthetiser` |
| A3.2 | Refus honnête partiel : le « je ne connais pas » existe (seuil 0,18) mais le reste du temps l'IA affirme ; le module physique est le SEUL avec frontières intégrées | `cerveau.py` |
| A3.3 | Synthèse poétisante : « les concepts qui vibrent ensemble appartiennent au même domaine » — le style masque l'absence de raisonnement | `cerveau.py::_poetiser` |
| A3.4 | Fragmentation des domaines : medical, entreprise, educal, maths, physique répondent chacun via des routes/contrats différents — pas de méta-routage unifié | `serveur.py` |

### A4. Performance mesurée (majeur)
| # | Réserve | Détail |
|---|---|---|
| A4.1 | GSM8K : 85,52 % (1128/1319) obtenu avec révision LLM DeepSeek sur TOUS les items ; sans LLM, la cascade fait 59/1319 (4,5 %) — dépendance massive au LLM externe | `benchmark_revision_tous.log` |
| A4.2 | Aucune validation hors-échantillon sur les benchmarks du moteur (la leçon de la session physique n'est pas appliquée à l'IA) | — |

### A5. Données et intégration (modéré)
| # | Réserve | Détail |
|---|---|---|
| A5.1 | 32 masses factices (placeholders entiers) dans la table d'isotopes — corrigé pour la physique, mais l'audit des autres données (benchmarks, completion_queue, news_cache) reste à faire | audit session |
| A5.2 | Auth faible : /api/chat ouvert (CORS *), Enterprise avec clé démo par défaut ; pas de tests e2e systématiques des routes | `serveur.py` |
| A5.3 | Voix dépendante d'un serveur externe (Piper :8420) ; dégradation non testée | `voix.py` |
| A5.4 | Workspace chaotique : fichiers modifiés non commités, données volatiles (wave_resonance, news_cache…) | `git status` |

### A6. Physique — limites restantes (documentées, à durcir)
| # | Réserve | Détail |
|---|---|---|
| A6.1 | A<40 : amplitude ħω/2 trop forte (O-16 : 1,51 → 17,96 MeV) — SEMF elle-même invalide là | `test_ame2020_ondulatoire.py` |
| A6.2 | Q_α absolus superlourds non fiables (offset ~9,5 MeV vs AME) — seules les tendances relatives le sont | idem |
| A6.3 | Coquille HO : gain nul hors vallée (P=36 %) — signal limité à la vallée | idem |
| A6.4 | Prédiction île de stabilité sans fourchette chiffrée (incertitudes non quantifiées) | `test_ile_stabilite.py` |

---

## PARTIE B — PLAN DE RÉSOLUTION (3 phases, critères mesurables)

### PHASE 1 — Fondations honnêtes (la vérité sur le moteur)

**P1.1 — Test décisif : l'encodage ondulatoire bat-il le hasard ?**
- Protocole : tâches de similarité sémantique (paires synonymes/antonymes/neutres)
  encodées avec (a) encode FNV-1a×φ-spacing, (b) hash aléatoire, (c) TF-IDF simple.
- Métrique : AUC de la similarité cosinus vs vérité terrain ; permutation test (5000).
- **Critère de succès** : si AUC(ondulatoire) − AUC(hash) > 0,05 avec p < 0,01 → le
  langage ondulatoire apporte un signal réel (à publier). Sinon → documenter
  honnêtement que l'encodage est un hash décoratif et réorienter l'effort sur
  les modules métier (physique, maths, médical) qui, eux, sont validés.
- Livrable : `validation_encodage.py` + rapport.

**→ RÉSULTAT (08/08/2026) : RÉFUTÉ — AUCUN SIGNAL.**

```
75 synonymes · 72 antonymes · 120 neutres (français, 302 mots)
ONDULATOIRE  : cos syn +0.0013 | ant −0.0001 | neu +0.0041
               AUC(syn vs non-syn) = 0.4985  ← le hasard pur
HASH ALÉATOIRE : AUC = 0.5586 (bruit équivalent)
N-GRAMMES    : AUC = 0.4387 (aucune discrimination orthographique)

Permutation (5000) : p(AUC_ond > 0,5) = 0,523 — indistinguable du hasard
                     ΔAUC(ond − hash) = −0,060 ; p = 0,847
```

L'encode FNV-1a × φ-spacing ne porte **aucune information sémantique** :
deux mots différents sont quasi-orthogonaux (cos ≈ 0), quelle que soit leur
relation. Le squelette φ-espacé (Three-Gap) arrange des phases aléatoires —
il ne crée pas de similarité entre concepts. **Conséquence** : la valeur du
projet repose sur les modules validés par protocole (physique 0,004 %,
GSM8K 85,52 %, coquille HO, Arena 60/60) et sur la mécanique HRR
(bind/superpose/exact-match decode — Plate 1995), pas sur une sémantique
de l'encodage. Les revendications « les concepts qui vibrent ensemble »
sont à retirer des communications (A3.3 devient : synthèse factuelle).

**P1.2 — Calibration de la confiance**
- Protocole : 200 questions échantillonnées (identité, maths, physique, domaines),
  précision réelle vs confiance annoncée ; courbe de calibration + Brier score.
- **Critère** : Brier < 0,25 et recalage par isotonic/platt si écart > 0,1.
- Livrable : `validation_confiance.py` + recaleur intégré au cerveau.

**→ RÉSULTAT (08/08/2026) : CALIBRÉ après corrections.**

```
200 questions (50 maths · 30 physique · 20 identité · 101 hors-domaine)
AVANT corrections : ECE = 0,437 | bin [0,4-0,6[ : précision 3,3 % —
   la boucle générique AFFIRMAIT à confiance ~0,5 sur l'inconnu.

Corrections appliquées (cerveau.py + physique.py) :
  · REFUS_SEUIL = 0,65 : le refus devient le comportement par défaut
  · un refus porte confiance 0,0 (plus la confiance périmée)
  · salutations complétées (chemin rapide)
  · détection physique : frontières de mots + règle élément+chiffre supprimée
    (« étoiles », « miles », « E=mc2 », « Formule 1 » ne déclenchent plus)
  · 7 tests de régression ajoutés (validation_physique.py 28/28)

APRÈS : ECE(assertions) = 0,056 (< 0,15) | Brier = 0,015
        refus hors-domaine = 100 % (cible 100 %)
        connus assertés = 98 % | précision comportementale = 99,5 %
```

**P1.3 — Benchmarks hors-échantillon**
- GSM8K : split train/test (la révision LLM et les patrons doivent être évalués
  sur le test seul) ; rapports avec intervalle (bootstrap).
- Arena V2 : CV 5-fold sur les épreuves ; publication des logs.
- **Critère** : chaque chiffre publié avec IC 95 % ; le 85,52 % re-mesuré
  hors-échantillon.

**→ RÉSULTAT (08/08/2026) : LE 85,52 % EST IN-SAMPLE — le transfert est nul.**

```
analyse_gsm8k_ic.py (rapport → data/ia_ondulatoire/benchmark_gsm8k_ic.json)

IC du chiffre publié (révision LLM TOUS) :
   85,65 %  IC95 [83,66 ; 87,56]   (block bootstrap, 131 blocs de 10)
   → chiffre PRÉCIS mais IN-SAMPLE : patrons + révision développés sur GSM8K

Re-mesure 0-LLM par item (1319, bootstrap per-item 5000) :
   4,47 %  IC95 [3,41 ; 5,61]
   Stabilité : 1ère moitié 6,22 % → 2e moitié 2,73 % (test ordonné par
   difficulté — la cascade ne tient que sur les items faciles)
   Par moteur : resonance 2,4 % (740) · patrons 8,0 % (462) ·
                machine_etats 3,4 % (117)
   Échecs : 1258 VALEUR FAUSSE sur 1260 — le chemin maths AFFIRME
   TOUJOURS, il ne refuse jamais (à corriger : refus à basse confiance)

TRANSFERT (le vrai hors-échantillon, 0 ajustement) :
   SVAMP (300 items, anglais) : 0,00 %  IC95 [0,00 ; 0,00]
   GSM8K TRAIN (60 items)     : 3,33 %  IC95 [0,00 ; 8,33]

VERDICT : la cascade 0-LLM ne transfère à AUCUNE nouvelle distribution ;
le 85,52 % publié repose entièrement sur la révision LLM et sur les
45 patrons taillés sur GSM8K. Action requise : refus à basse confiance
dans le chemin maths + mesure systématique en transfert avant toute
revendication.
```

**P1.4 — Audit des données**
- Script qui liste placeholders/valeurs arrondies/JSON invalides dans
  data/benchmarks, data/hologram_store, completion_queue.
- **Critère** : rapport d'audit 0 anomalie bloquante.

### PHASE 2 — Cœur renforcé (l'IA qui refuse et cite)

**P2.1 — Refus honnête généralisé**
- Tout sujet hors domaine appris → réponse « Je ne sais pas encore (confiance X) —
  dis-moi « souviens-toi que… » », systématiquement, sans poétisation.
- **Critère** : sur 100 questions hors-domaines, 100 % de refus explicites.

**P2.2 — Synthèse factuelle (poésie optionnelle)**
- `_synthetiser` produit d'abord une phrase factuelle vérifiable ; la poésie
  devient un mode désactivable (paramètre `style`).
- **Critère** : chaque réponse contient ≥ 1 fait issu des hologrammes/calculs.

**P2.3 — Méta-cerveau : routage unifié**
- Un contrat de réponse unique (response, confiance, source, faits, limites)
  pour les 6 chemins : identité, maths, physique, médical, entreprise, éducal.
- **Critère** : un script teste les 6 chemins avec le même schéma JSON.

**P2.4 — Auth + tests e2e**
- Clé API optionnelle sur /api/chat (X-API-Key), CORS configurable.
- `tests_e2e.py` : les ~25 routes avec asserts (réponses 200/400/422 attendues).
- **Critère** : 25/25 routes testées, échec → exit non nul.

**→ RÉSULTAT (08/08/2026) : 37/37 routes OK + auth vérifiée.**

```
· KA_API_KEY (env) : /api/chat exige X-API-Key → 401 sans/mauvaise clé
  (vérifié 401/401/200 sur port frais)
· KA_CORS_ORIGINS (env) : origines configurables (défaut *)
· BUG TROUVÉ PAR LES TESTS : la route /api/maths/solve n'était JAMAIS
  enregistrée (décorateur collé dans un commentaire, ligne 557) — restaurée
· BUG TROUVÉ : /api/educal/quiz/submit → 500 sur entrées mal formées
  (robustesse : validation → 400)
· tests_e2e.py blindé : port aléatoire (évite les serveurs périmés qui
  traînent — double bind Windows détecté et nettoyé)
· Bilan : 37/37 routes (chat, memorise, creative, reason, mémoire,
  physique ×7, vital, enterprise ×6, educal ×4, maths ×2, voix ×2,
  store, personalize, 404)
```

### PHASE 3 — Validation externe (le monde)

**P3.1 — Échantillons de benchmarks publics**
- 30 items MMLU-fr (raisonnement), 10 problèmes MATH, 5 exercices HumanEval
  (syntaxe Python) — évaluation honnête du moteur 0 LLM.
- **Critère** : rapport public avec scores bruts, même faibles.

**→ RÉSULTAT (08/08/2026) : SCORES BRUTS PUBLIÉS — moteur calibré qui refuse.**

```
benchmark_externe.py — aucun ajustement, cerveau complet (0 LLM)

MMLU-fr style (30) : correct 0 · faux 3 · refus 27  (taux de réponse 10 %)
   — le moteur ne traite PAS le format à choix multiples
   — les 3 faux : passages via le chemin maths (fractions/décimales :
     « 2/3 + 1/6 », « 0,25 × 0,4 ») — faiblesse réelle du solveur
MATH (10)          : correct 0 · faux 0 · refus 10  (100 % de refus calibrés)
HumanEval (5)      : correct 0 · faux 1 · refus 4   — AUCUNE capacité de code
   (le moteur n'exécute pas Python — frontière honnête documentée)

LECTURE : les refus sont le comportement calibré (P1.2) — l'IA ne devine
pas. Un auditeur externe mesurerait exactement ces scores. Le chemin
« réponse » (maths) reste limité à l'arithmétique simple de type GSM8K.
```

**P3.2 — Prédiction physique pré-enregistrée**
- Fourchette chiffrée de l'île de stabilité : S_2n(Z=119-126, N) ± incertitudes
  (bootstrap sur les résidus), déposée datée et signée.
- **Critère** : document daté avec fourchette + protocole de falsification.

**P3.3 — Rapport de publication du moteur**
- `PUBLICATION_IA_HARMONIQUE.md` : statut VÉRIFIÉ / RÉFUTÉ / NON TESTÉ de chaque
  capacité (13 primitives, 7 intentions, GSM8K, Arena, physique, voix, PWA),
  avec les scripts de reproduction.
- **Critère** : chaque ligne du rapport = une commande reproductible.

---

## PARTIE C — PRIORITÉS ET HONNÊTETÉ

1. **P1.1 est le test qui décide de tout** : si l'encodage ondulatoire ne bat
   pas le hasard, le cœur « langage ondulatoire » est un hash décoratif — la
   valeur du projet bascule alors vers les modules validés (physique 0,004 %,
   GSM8K 85,52 %, coquille HO) et l'architecture HRR documentée comme telle.
2. **P1.2/P1.3 sont non négociables** : aucune IA ne peut être présentée comme
   fiable sans confiance calibrée ni benchmark hors-échantillon.
3. **La numérologie (A1) n'est PAS réparable par plus de calculs** : α/GAGUT
   restent des curiosités documentées ; le seul chemin vers une preuve serait
   une prédiction ex-ante pré-enregistrée (P3.2 est le modèle).
4. Chaque action a un critère mesurable — aucune « amélioration » sans chiffre.
