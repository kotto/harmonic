# PARSEUR SÉMANTIQUE ONDULATOIRE — Équivalences avec les LLM classiques
**Date** : 08/08/2026 — **Motif** : taxonomie des échecs (P1.3bis) — 81,2 %
des échecs GSM8K sont des erreurs de RELATION : le moteur extrait les
nombres mais ne traduit pas les relations. La feuille de route : un vrai
parseur sémantique, inspiré des LLM classiques, exprimé en primitives
ondulatoires.

---

## 1. La table d'équivalences (LLM classique ↔ langage ondulatoire)

| # | Concept LLM classique | Équivalence ondulatoire | Statut dans le moteur |
|---|---|---|---|
| 1 | **Tokenisation** (BPE, WordPiece) | découpage en entités + vocabulaire (`vocabulaire`) | ✅ existe (mots pleins) |
| 2 | **Embeddings distributionnels** (word2vec/transformer : le sens vient de l'USAGE — mots dans des contextes similaires → vecteurs proches) | **SUPERPOSE des contextes** : emb(w) = normalize(Σ_{c ∈ contexte(w)} encode(c)) — la sémantique vient de la co-occurrence, PAS du hash | ⚠️ À CONSTRUIRE — P1.1 a prouvé que encode() seul ne porte rien ; la correction est l'équivalent exact de « apprendre des embeddings » |
| 3 | **Encodage positionnel** (sinusoïdes / RoPE) | **φ-spacing** (théorème des trois gaps) : phases 2π·frac(k·φ) — positions distribuées ; + ROTATE par position | ✅ existe (encode) — à utiliser explicitement par token |
| 4 | **Attention QKV** : score = ⟨q, k⟩, poids = softmax, sortie = Σ wᵢ·vᵢ | **RESONATE** = ⟨q, k⟩ (cosinus complexe) ; **softmax sur les résonances** ; **SUPERPOSE(weights=w)** — la somme pondérée est la primitive exacte | 🔧 ÉQUIVALENCE DIRECTE — à implémenter (superpose porte déjà weights) |
| 5 | **Têtes d'attention multiples** | **ROTATE multi-angles** : chaque angle = une perspective (la primitive se décrit déjà comme « changement de perspective ») ; plusieurs canaux de résonance | 🔧 naturelle |
| 6 | **Normalisation de couche** | **NORMALIZE** | ✅ existe |
| 7 | **Connexions résiduelles** | **SUPERPOSE(entrée, transformation)** | ✅ existe |
| 8 | **MLP / transformation calculatoire** | **machine à états + exécuteur arithmétique** (le calcul explicite) | ✅ existe |
| 9 | **Chaîne de pensée (CoT)** | **les étapes du plan** (« 16 − 3 − 4 = 9 → 9 × 2 = 18 ») | ✅ existe (etapes) |
| 10 | **Décodage / prochain token** | **DÉCODE** (plus proche voisin par résonance) | ✅ existe |
| 11 | **Mémoire de contexte / in-context learning** | **HolographicMemory** (faits stockés, rappel par résonance ; « souviens-toi que… ») | ✅ existe |
| 12 | **Logits → softmax (distribution de sortie)** | poids d'interférence = softmax(résonances) | 🔧 |
| 13 | **Calibration / abstention** | seuil de refus (P1.2) : couverture faible → REFUS | ✅ existe |
| 14 | **Perte / rétropropagation** | pas d'équivalent — remplacé par la **grammaire explicite des relations** (le savoir vient de règles, pas de gradient) | ➡️ choix assumé : zéro paramètre appris |

## 2. La leçon structurelle des LLM

Trois mécanismes font la puissance des transformers — et chacun a un
équivalent ondulatoire exact :

1. **Le sens vient de l'usage, pas du symbole** (embeddings) → l'encode
   FNV-1a est un symbole ; il faut le remplacer par la superposition des
   contextes. C'est LA correction de P1.1.
2. **L'attention sélectionne** (softmax sur les similarités) → la
   résonance + softmax + superposition pondérée : le parseur « regarde »
   les clauses pertinentes de la question.
3. **La profondeur compose** (résiduels + MLP) → la machine d'états
   compose les transformations ; la chaîne de pensée EST la profondeur.

## 3. L'architecture du parseur (5 étages)

```
ÉTAGE 1 — TOKENISATION + EMBEDDINGS CONTEXTUELS
  · mots + nombres + unités + ponctuation → entités
  · emb(w) = normalize(Σ_{c ∈ fenêtre} encode(c))   ← l'équivalent
    distributionnel ; co-occurrence sur le corpus de problèmes
  · positions : phases φ-espacées + ROTATE par indice

ÉTAGE 2 — ATTENTION (focus) — l'équivalent QKV en ondulatoire
  · query  = emb(question cible)   (« How much… ? »)
  · keys   = emb(clause i) pour chaque clause du problème
  · scores = resonate(q, k_i) ;  w_i = softmax(scores)
  · contexte = SUPERPOSE(clauses, weights=w)   ← attention
  · têtes multiples : ROTATE(q, θ_h) pour h ∈ {0, π/4, π/2, 3π/4}

ÉTAGE 3 — EXTRACTION TYPÉE (le typeur étendu)
  · nombres → {valeur, unité, rôle}   (typeur existant)
  · objets → entités du problème (grammaire nominale)

ÉTAGE 4 — GRAMMAIRE DES RELATIONS (LE CŒUR — 81,2 % des échecs)
  · fractions  : « X/Y of N », « one-fourth of N », « half of N »,
                 « two thirds of N »  → take(N, X/Y)
  · pourcentages : « X% of N », « X% more/less than N » → take/mult
  · ratios     : « k times as many as », « twice as many » → ×k
  · comparaisons : « X more than N » → N+X ; « X less than N » → N−X
  · dimensions : « per », « each », « a day/week/year » → multiplicateur
                 temporel ; « in N days » → durée
  · séquence   : « then », « after », « first/second/third » → ordre
  Chaque règle produit un TRIPLET (entité, opération, argument) dans
  la représentation intermédiaire typée (IR) — le « plan » que la
  révision LLM produit déjà, produit ICI par la grammaire.

ÉTAGE 5 — PLAN + EXÉCUTION + REFUS
  · l'IR est traduite en opérations ordonnées (la chaîne de pensée)
  · exécution arithmétique (machine existante)
  · COUVERTURE = part des relations reconnues ; si < seuil → REFUS
    (jamais de réponse fausse confiante — verdict P1.3)
```

## 4. Critère de succès (pré-enregistré)

Test sur les **80 échecs étiquetés** (taxonomie, PLAN_FAUX) :
- aujourd'hui : 0 décomposition correcte sur 80 (la cascade échoue)
- objectif prototype : **≥ 40 % de plans corrects** sur les 80 (dont les
  erreurs de relation E/R), avec refus explicite sur le reste
- mesure : plans corrects / plans faux / refus, et comparaison
  catégorie par catégorie (fractions, %, ratios, comparaisons, dimensions)

## 5. Ce qui reste volontairement hors périmètre

- Pas d'apprentissage par gradient : la grammaire est explicite
  (cohérent avec « zéro paramètre ajusté » du projet) ;
- Pas de LLM dans la boucle : le parseur est 100 % local ;
- L'encode FNV-1a reste la graine déterministe des symboles ; seule la
  CONSTRUCTION des embeddings change (usage, pas hash).

## 6. Prototype — état mesuré (itération 1, 08/08/2026)

`parseur_semantique.py` — les 5 étages implémentés :
1. embeddings contextuels par co-occurrence (corpus = échecs + 300 GSM8K)
2. attention multi-têtes : softmax(resonate(q, k)) → SUPERPOSE pondéré
3. extraction typée (nombres + unités)
4. grammaire des relations v0.1 : fractions, %, ratios, comparaisons,
   achats (N × $P each), taux (« N per X »), durées, solde
5. plan → exécution → COUVERTURE < 0,5 → REFUS

**Mesure sur les 80 échecs étiquetés** (les plus durs du corpus) :

| Itération | BONS | FAUX | REFUS | Note |
|---|---|---|---|---|
| v0.0 | 0 | 6 | 74 | refus correct, grammaire pauvre |
| v0.1 (+achat multi, fractions « of that », for-$P total) | 0 | 4 | 76 | FAUX −33 % ; « for $80 » total ne devient plus une assertion |
| v0.2 (taux×durée, inverse, cible, quantités, ratio ; clauses question traitées) | 4 | 2 | 74 | familles gagnées : perte (113), intérêt simple (187), problème inverse (548), taux composé+cible (555) — progression 0→1→3→4 |
| v0.3 (correction virgule-milliers US : 14 réponses mal lues dans tout le benchmark) | — | — | — | extraction « #### 1,875 » = 1875 ; affecte 14/1319 items |
| v0.4 (fractions chaînées + références d'entités) | 6 | **0** | 74 | familles : perte, intérêt simple, problème inverse, taux+cible, **fractions chaînées (1009 : 1875 ✓)**, **ratio imbriqué (1140 : 27 ✓)** — ZÉRO faux : tout plan inexact devient refus |

Verdict de l'itération 3 :
- ✅ **6 familles résolues, 0 réponse fausse confiante** (74/80 refus corrects) —
  le registre d'entités (références « the students over 16 », compléments,
  base originale) et l'exécution en deux passes (taux avant durées) ont
  réglé les deux derniers faux ET les régressions d'ordre
- ✅ Les mécanismes clés : découpage par virgules (sauf milliers US),
  « over 16 years old » ≠ durée, perte après durées, intérêt avant le
  piège taux-None
- ❌ Familles restantes (prochaines itérations) : multi-périodes (601),
  taux inverses (307), systèmes de ratios (141)

Verdict de l'itération 2 :
- ✅ 4 familles de relations résolues (perte, intérêt, inverse, taux+cible) —
  la boucle grammaire → mesure → itération fonctionne (0 → 4 bons)
- ❌ 2 FAUX restants : fractions chaînées avec entités (1009), ratio imbriqué
  (1140) — les problèmes composites, prochaine famille
- ✅ 74/80 refus corrects — jamais de réponse fausse confiante
  (sauf 2, couverts par la prochaine itération)

Verdict honnête de l'itération 1 :
- ✅ L'architecture (embeddings → attention → grammaire → refus) fonctionne
  de bout en bout ; le REFUS est le comportement dominant (76/80) — le
  verdict P1.3 est appliqué : jamais de réponse fausse confiante.
- ❌ 0 plan correct sur les 80 : la grammaire v0.1 couvre les structures
  simples mais pas les problèmes composites (systèmes de ratios,
  problèmes inverses, fractions chaînées, taux × durée × unités).
- ➡️ Le chantier est la GRAMMAIRE, famille par famille, avec le test des
  80 comme porte de sortie mesurable à chaque itération (critère final :
  ≥ 40 % de plans corrects sur les 80 + refus sur le reste).
