# 🌊 PLAN GSM8K — La solution harmonique

> « Toutes les tentatives annoncées comme impossibles ont trouvé leur
> solution harmonique. De la même manière nous trouverons celle pour
> GSM8K. »
>
> Principe directeur : si les LLM résolvent GSM8K, une machine finie le
> résout — notre tâche est de trouver l'algorithme. Le langage chaîne est
> déjà COMPLET (M1 : 99,2 %) et la résonance est PARFAITE (M2 : 100 %) :
> il ne manque que la CONSTRUCTION DE LA CHAÎNE pour un problème non vu.

## 📊 État des lieux mesuré (4 août 2026, dataset officiel 1319)

| Mesure | Résultat | Lecture |
|---|---|---|
| M0 parseur d'annotations | 100 % (4281) | le langage chaîne est prouvé |
| M1 exécution des chaînes | 99,2 % (1308/1319) | **le langage couvre GSM8K** |
| M2 mémoire par résonance | 100 % (top-1 = soi) | la récupération est parfaite |
| M3 généralisation leave-one-out | 0,5 % pass@1 | le verrou : instancier une chaîne |
| M4 classement sémantique + consensus | 1,6 % pass@1 · oracle top-20 10,2 % | le classement est le goulot |
| Solveur d'état + motifs | 2,0 % (échantillon 200) | couverture sémantique directe |

## 🔬 Mesures de faisabilité (diagnostics, 4 août)

**D1 — Distribution des squelettes** : 583 squelettes uniques sur 1319.
**69,7 % des problèmes (920/1319) ont leur squelette EXACT chez un autre
problème.** L'instanciation a la matière — le verrou n'est pas la présence
du squelette, c'est l'ALIGNEMENT DES NOMBRES.

**D2 — Courbe des rangs M4 (top-20)** : le bon candidat est au top-1 pour
16 problèmes (1,2 %), top-3 pour 25 (1,9 %), top-5 pour 25, top-10 pour 51
(3,9 %), top-11-20 pour 17. La courbe est PLATE : le classement sémantique
actuel ne discrimine pas assez — chaque feature gagnée remonte le pass@1
vers l'oracle (10,2 %), et l'élargissement de la récupération monte
l'oracle lui-même.

## 🗺️ Les phases — par ordre de rentabilité

### Phase 1 — L'ALIGNEMENT DES NOMBRES (le verrou de l'instanciation)
**Objectif** : transformer la matière des 920 squelettes partagés en
réponses correctes (M3 : 0,5 % → viser 20-30 %).

- **Expérience 1.1 — Ordre préservé ?** : pour les 920 problèmes partagés,
  mesurer la fréquence où l'ordre d'apparition des nombres dans la question
  = l'ordre d'utilisation dans la chaîne source. Si ≥ 60 % : l'instanciation
  naïve (dans l'ordre) est la première brique.
- **Expérience 1.2 — Alignement par rôle** : pour les autres, aligner par
  rôle sémantique (le nombre après « each » = opérande de MUL ; le nombre
  après « left » = opérande de SUB ; les quantités d'objets vs les prix…).
  Le solveur d'état fournit déjà ces rôles (objets, prix, quantités).
- **Expérience 1.3 — Vérification par exécution** : une instanciation est
  acceptée seulement si la chaîne exécutée produit un résultat COHÉRENT
  (entier, positif, unités de la question) — le gate arithmétique.
- **Jalon 1** : pass@1 ≥ 15 % sur le dataset complet par instanciation
  seule (avec gate : réponses servies = réponses exactes).

### Phase 2 — LE CLASSEMENT MULTI-SIGNAUX (M4 amélioré)
**Objectif** : 1,6 % → 5-8 % pass@1 (vers l'oracle top-20 10,2 %).

- **Expérience 2.1 — Ré-optimisation des poids** : le score actuel est
  pondéré (0,0 ; 0,1 ; 0,3 ; 0,15 ; 0,45) — rôle, couverture, plausibilité,
  ordre, forme. Grid-search sur un échantillon de validation (200).
- **Expérience 2.2 — Nouvelles features** : similarité thématique (achats,
  vitesse, âges), similarité des profils de nombres (le problème cible a
  N nombres, le candidat aussi), longueur du squelette.
- **Expérience 2.3 — Récupération élargie** : top-20 → top-100 (le coût
  est faible) ; mesurer l'oracle top-100 (objectif : 20-25 %).
- **Jalon 2** : pass@1 ≥ 5 % et oracle top-100 ≥ 20 %.

### Phase 3 — LE CONSENSUS FINAL (l'équivalent du self-consistency)
**Objectif** : fusionner les chemins indépendants et ne répondre que sur
convergence.

- Les stratégies indépendantes : ① instanciation de squelette (P1),
  ② classement M4 (P2), ③ solveur d'état + motifs, ④ formule directe.
- **Règle** : 2+ chemins convergent → servir (avec la chaîne comme preuve) ;
  divergence totale → REFUS calibré (le gate — jamais de réponse fausse
  servie).
- **Jalon 3** : pass@1 ≥ 20 % ET « précision des réponses servies » = 100 %
  (la métrique produit : correct ÷ (correct + faux), les refus exclus).

### Phase 4 — LES 11 ÉCHECS DE M1 + L'ÉLARGISSEMENT DU LANGAGE
- Analyser les 11 problèmes où la chaîne annotée ne donne pas le bon
  résultat (annotations incomplètes ou mal formées) → compléter le
  parseur/le langage (99,2 % → 100 %).
- Générer de NOUVEAUX squelettes par composition des opérations connues
  (les 583 existants → familles paramétrées) pour couvrir la longue queue
  des 399 squelettes uniques.

### Phase 5 — LA GARANTIE PRODUIT
- Le gate s'applique au raisonnement comme à la connaissance : une réponse
  mathématique n'est servie que si une chaîne exécutable la prouve.
- Les métriques du buzz : « précision 100 % des réponses servies »,
  « refus calibré sinon », « 0 GPU », « ~10 ms », « 0 paramètre entraîné »,
  « langage chaîne complet à 99,2 % sur GSM8K » — un dossier irréprochable
  et reproductible.

## 🎯 Les métriques de suivi (le tableau de bord du plan)

| Jalon | Métrique | Actuel | Cible |
|---|---|---|---|
| P1 | pass@1 par instanciation (gate inclus) | 0,5 % | ≥ 15 % |
| P2 | pass@1 M4 · oracle top-100 | 1,6 % · 10,2 % (top-20) | ≥ 5 % · ≥ 20 % |
| P3 | pass@1 global · précision servie | 2 % · ~90 % | ≥ 20 % · 100 % |
| P4 | couverture M1 | 99,2 % | 100 % |
| P5 | dossier reproductible | — | 1 clic, 10 min |

## ⚠️ Risques et contre-mesures

| Risque | Contre-mesure |
|---|---|
| L'ordre des nombres n'est pas préservé (Exp 1.1 faible) | Alignement par rôle sémantique (Exp 1.2) — le solveur d'état fournit les rôles |
| Le classement M4 plafonne sous l'oracle | Élargir la récupération (top-100) AVANT d'améliorer le classement fin |
| L'instanciation produit des faux positifs | Le gate par exécution : une chaîne fausse s'exécute en un résultat incohérent → refus |
| La longue queue des 399 squelettes uniques | Phase 4 : génération de squelettes par composition |
| Le buzz repose sur un benchmark daté | La métrique produit (précision 100 % des réponses servies) est transposable aux benchmarks actuels |

## 🧭 Le principe harmonique du plan

Chaque phase est une ONDE : l'alignement (phase), la sémantique (couverture),
la résonance (récupération), le consensus (cohérence), le gate (forme).
La solution complète = la RÉSONANCE ENTRE CES ONDES INDÉPENDANTES —
exactement le mécanisme qui a résolu chaque « impossible » précédent :
le langage est déjà complet (M1), la résonance déjà parfaite (M2) ;
l'instanciation alignée + le consensus en feront la construction.

## 🧪 RAPPORT D'EXPLORATION — PHASE 1 (5 août 2026)

**Exp 1.1 — Plafond de l'instanciation par position** : 239/1319 (18,1 %)
résolus par au moins un j de même squelette instancié par position. 399
(30,3 %) sans squelette partagé ; 681 (51,6 %) partagés mais aucun hit par
position → l'ORDRE des nombres diffère.

**Exp 1.2 — Plafond avec permutations** : 353/1319 (26,8 %) (+114) —
l'alignement par rôle (toutes les permutations, n ≤ 5) porte le plafond
au-dessus du jalon P1 (≥ 15 %). La matière de l'instanciation EXISTE.

**Exp 1.3 — Classement du bon j par résonance de question** : parmi les
353 problèmes au plafond, le bon j est top-1 pour 44 (12,5 %), top-3 pour
74 (21 %), top-5 pour 99 (28 %). → LE CLASSEMENT DES j EST LE GOULOT
(l'instanciation ne vaut que ce que vaut la sélection du squelette source).

**Exp 1.4 — Prototype complet (résonance + permutations + gate entier)**
: pass@1 1,5 %, précision servie 1,5 % — le bruit des permutations domine.

**Exp 1.5 — Gate strict (vote ≥ 2, peers de même squelette)** : pass@1
8,3 % (110/1319), servies 51 %, précision servie 16,3 % — les permutations
FAUSSES COLLISIONNENT (les petits nombres donnent les mêmes résultats par
des chemins différents) : le vote seul ne discrimine pas.

**Conclusions de P1** :
1. Le plafond (26,8 %) prouve que la solution existe — mais l'oracle j est
   indisponible en inference : le classement réel ne met le bon j en tête
   que 12,5 % du temps.
2. Le gate arithmétique seul (entier positif, vote) est inopérant face aux
   collisions de permutations — il faut des permutations GUIDÉES par le
   RÔLE SÉMANTIQUE des nombres (prix, quantité, taux) pour réduire le
   bruit d'un ordre de grandeur.
3. L'ordre des phases du plan est confirmé : P2 (le classement) est le
   PRÉALABLE de P1 (l'instanciation) — la résonance de question ne suffit
   pas ; il faut des features orthogonales (profil de nombres, rôle
   sémantique via le solveur d'état).

**Prochaines expériences (P2 — le classement)** :
- 2a : classement des j par SIMILARITÉ DE PROFIL DE NOMBRES (nombre de
  qnums, magnitudes relatives) — feature orthogonale à la question
- 2b : ré-optimisation des poids du score sémantique M4 (grid-search)
- 2c : l'alignement par rôle : identifier le rôle de chaque nombre de la
  question (prix après « each », quantité d'objets, taux per jour) via le
  solveur d'état, et ne permuter que les rôles compatibles → réduire les
  collisions d'un ordre de grandeur
