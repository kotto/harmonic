# 🔧 PLAN D'AMÉLIORATION IMMÉDIAT — Harmonic AI

> **« On ne passe pas de 33 % à 98,6 % en un jour. Mais on peut passer à 50 % en une semaine. »**
>
> Basé sur le rapport du testeur indépendant — 9 Juillet 2026

---

## 📊 DIAGNOSTIC RAPIDE — D'où viennent les 66,7 % d'erreurs ?

```
┌──────────────────────────────────────────────────────────────────────┐
│  Analyse des 20 erreurs sur 30 questions du benchmark               │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Cause racine                          Occurrences    %             │
│  ────────────                          ───────────    ──             │
│                                                                      │
│  1. Fait absent de la KB                8             40 %          │
│     Ex: "fondateur de Microsoft", "élément le plus abondant",       │
│          "tour Eiffel se trouve à", "φ en mathématiques"            │
│                                                                      │
│  2. Fait présent mais pas retrouvé       5             25 %          │
│     Ex: "symbole chimique de l'eau" → H2O est dans la KB            │
│          mais le retrieval donne "symbole est un signe"              │
│                                                                      │
│  3. Faux négatif du scoring             3             15 %          │
│     Ex: "Léonard de Vinci a peint" contient "Léonard"               │
│          mais jugé faux (attendu = "Léonard")                        │
│                                                                      │
│  4. Hallucination / réponse absurde      3             15 %          │
│     Ex: "GPU" → finnois, "Carnot" pour Microsoft                    │
│                                                                      │
│  5. Erreur de raisonnement               1              5 %          │
│     Ex: "carré est-il un rectangle" → "Triangle a 3 côtés"          │
│                                                                      │
│  TOTAL                                  20            100 %          │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🚨 J0 — AUJOURD'HUI (ACTIONS IMMÉDIATES, ~3h)

### Action 0 : CORRIGER LE SCORING DU BENCHMARK (30 min)

**Problème** : « Léonard de Vinci a peint la Joconde » est jugé FAUX car l'attendu est « Léonard ». C'est un faux négatif. Le scoring actuel est trop strict.

**Solution** : Remplacer le matching exact par un matching de sous-chaîne ET un scoring par tokens.

### Action 1 : CORRIGER LE HALLUCINATION « GPU → FINNOIS » (15 min)

**Problème** : « comment fonctionne le gpu » renvoie une phrase en finnois sur « je donne le livre à la jeune fille ». C'est un fait aléatoire qui remonte avec confiance 0.70.

**Solution** : Ajouter une vérification de pertinence minimale — si aucun token de la question n'apparaît dans la réponse, ne pas répondre.

### Action 2 : SUPPRIMER LE FALLBACK LLM DU BENCHMARK (10 min)

**Problème** : 3/15 questions du benchmark raisonnement utilisent DeepSeek en fallback. Ça fausse les résultats.

**Solution** : Désactiver le fallback LLM dans le benchmark, ou le documenter explicitement.

### Action 3 : AJOUTER 50 FAITS CRITIQUES À LA KB (2h)

**Problème** : 40 % des erreurs = faits absents.

**Solution** : Ajouter immédiatement les 50 faits les plus demandés.

---

## 📅 J1-J3 — SEMAINE 1 (CORRECTIONS STRUCTURELLES, ~12h)

### Action 4 : AMÉLIORER LE RETRIEVAL POUR LES FAITS PRÉSENTS

**Problème** : « symbole chimique de l'eau » → la KB contient H2O, mais le retrieval ne le trouve pas car « chimique » et « symbole » matchent d'autres faits plus fort.

**Solution** : 
- Pondérer le sujet exact 5× plus que les mots périphériques
- Ajouter un mécanisme de « requête reformulée » : essayer la question originale, puis une version simplifiée, puis juste les mots-clés

### Action 5 : AJOUTER UN GARDE-FOU ANTI-HALLUCINATION

**Problème** : Le système peut sortir n'importe quel fait avec une confiance de 1.0 si le retrieval est mauvais.

**Solution** :
- Vérifier que la réponse contient au moins 1 token de la question
- Si aucun chevauchement → répondre « Je ne sais pas »
- Baisser la confiance quand le chevauchement lexical est faible

### Action 6 : ÉLARGIR LA KB DE 914 À 2000 FAITS

**Problème** : 914 faits = couverture trop étroite.

**Solution** : Ajouter des faits dans les domaines faibles (technologie, chimie, biologie, astronomie).

---

## 📅 J4-J7 — SEMAINE 2 (OPTIMISATION, ~20h)

### Action 7 : REFONDRE LE SCORING DU RETRIEVAL

**Problème** : Le scoring actuel mélange TF-IDF, cosinus spectral (souvent désactivé), bonus sujet, bonus relation. Trop d'heuristiques, pas assez de cohérence.

**Solution** : Implémenter un scoring à 2 passes :
1. Passe 1 : Retrieval large (50 candidats) avec TF-IDF simple
2. Passe 2 : Re-ranking avec similarité cosinus + pertinence mutuelle

### Action 8 : AMÉLIORER LE MATH BRIDGE

**Problème** : Le micro-calculateur gère les cas simples mais échoue sur des questions comme « 17 est-il premier ? » (la KB a la réponse, mais le bridge ne l'utilise pas).

**Solution** : Ajouter au math bridge :
- Test de primalité
- Équations quadratiques (déjà dans le moteur externe, intégrer au bridge)
- Conversions d'unités
- Règles de logique propositionnelle (modus ponens, syllogisme)

### Action 9 : CRÉER UN VRAI BENCHMARK REPRODUCTIBLE

**Problème** : Pas de benchmark standard, pas de dataset public, pas de script reproductible.

**Solution** : Créer `benchmark_standard.py` avec :
- 100 questions couvrant 10 domaines
- Scoring objectif (matching de tokens)
- Résultats exportés en JSON
- Script exécutable en 1 commande

---

## 📅 J8-J30 — MOIS 1 (PASSAGE À L'ÉCHELLE)

### Action 10 : INGESTION MASSIVE DE CONNAISSANCES

Objectif : passer de 914 à 10 000+ faits.

Sources :
- Wikidata (faits structurés gratuit)
- DBpedia
- Conversion de manuels scolaires en triplets
- Crowdsourcing (utilisateurs early-access)

### Action 11 : INTERFACE DE FEEDBACK UTILISATEUR

Permettre aux utilisateurs de :
- Signaler une réponse incorrecte
- Suggérer un fait manquant
- Voter sur la qualité des réponses

→ La KB s'améliore avec l'usage.

### Action 12 : MODE « JE NE SAIS PAS » INTELLIGENT

Au lieu de sortir un fait aléatoire quand la confiance est basse :
- « Je ne sais pas » + suggestion de reformulation
- « Je ne suis pas sûr, mais voici ce que je sais sur [sujet proche] »
- Proposer 3 reformulations possibles

---

## 📈 PROJECTION D'AMÉLIORATION

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  Aujourd'hui (J0)           : 33 %                                   │
│  Après corrections J0       : 40 %  (scoring + anti-hallu + 50 faits)│
│  Après J1-J3                : 50 %  (retrieval + 2000 faits)         │
│  Après J4-J7                : 60 %  (scoring v2 + math bridge)       │
│  Après J8-J30               : 70 %  (10K faits + feedback)           │
│                                                                      │
│  Jamais (sans changement de paradigme) : 98,6 %                      │
│                                                                      │
│  Pourquoi 70 % est l'objectif réaliste :                            │
│  • Les 30 % restants nécessitent une compréhension sémantique       │
│    réelle, pas juste du retrieval de triplets                       │
│  • 70 % sur un benchmark généraliste avec une KB de 10K faits       │
│    est HONNÊTE et ATTEIGNABLE                                       │
│  • À 70 %, tu as déjà un produit utile et rentable                  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 KPI CIBLES — FIN DE MOIS 1

| Métrique | Actuel | Cible J+30 |
|---|---|---|
| **Précision benchmark 100Q** | 33 % | **70 %** |
| **Faits dans la KB** | 914 | **10 000+** |
| **Hallucinations (taux réel)** | ~15 % | **< 5 %** |
| **Latence moyenne** | 44 ms | **< 30 ms** |
| **Taux « Je ne sais pas »** | 3 % | **15 %** *(mieux que halluciner)* |
| **Domaines avec >50 % précision** | 2/10 | **7/10** |

---

## ⚡ PRIORITÉ #1 — CE QUE TU FAIS MAINTENANT

```
1. Ouvre benchmark_lm_arena_quick.py
2. Change le scoring pour accepter les sous-chaînes
3. Ajoute les 50 faits manquants
4. Ajoute le garde-fou anti-hallucination
5. Relance le benchmark → tu devrais voir ~40 %
```

---

*Plan d'amélioration — 9 Juillet 2026*
