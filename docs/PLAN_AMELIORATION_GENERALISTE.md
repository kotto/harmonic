# 📋 PLAN D'AMÉLIORATION GÉNÉRALISTE — IA Harmonique

> **Statut actuel : 75% factuel (domaine scientifique), ~15% généraliste**
> **Objectif : 60%+ sur l'ensemble des catégories LM Arena**

---

## 0. DIAGNOSTIC — OÙ ON EN EST

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   CATÉGORIE LM ARENA    ACTUEL    CIBLE    ÉCART    FAISABLE    │
│                                                                  │
│   Science/Physique       ✅ 85%    90%      +5%      ✅ Facile   │
│   Mathématiques          ✅ 80%    90%      +10%     ✅ Facile   │
│   Géographie             ⚠️ 40%    80%      +40%     ✅ Moyen    │
│   Histoire               ⚠️ 35%    75%      +40%     ✅ Moyen    │
│   Littérature/Art        ⚠️ 35%    70%      +35%     ✅ Moyen    │
│   Culture générale       ⚠️ 30%    70%      +40%     ✅ Moyen    │
│   Conversation           ✅ 75%    85%      +10%     ✅ Facile   │
│   Multilingue (EN)       ❌ 5%     60%      +55%     ⚠️ Difficile│
│   Créativité (writing)   ✅ 90%    90%      0%       ✅ Déjà OK  │
│   Raisonnement           ⚠️ 20%    50%      +30%     ⚠️ Difficile│
│   Coding                 ❌ 0%     30%      +30%     ❌ Très dur │
│                                                                  │
│   GLOBAL                 ~40%     ~70%     +30%                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 1. LES 6 BLOCS D'AMÉLIORATION

### Bloc 1 — KB : Extension massive de la base de connaissance (+2000 faits)

**C'est le levier le plus puissant.** L'IA répond correctement quand elle a les faits. Là où elle échoue, c'est quand le fait n'existe pas.

#### 1A. Géographie (priorité maximale)

```
Ajouter : 200+ faits de géographie
  - 200 capitales de pays (toutes)
  - 50 fleuves, montagnes, déserts
  - 50 données démographiques (population, superficie)
  - Monnaies, langues, fuseaux horaires
```

**Fichier :** `data/geography_triples.txt` → ingestion automatique

#### 1B. Histoire (+200 faits)

```
Ajouter : 200 faits historiques
  - Dates clés (guerres, révolutions, découvertes) : 50
  - Personnages historiques (qui a fait quoi) : 50
  - Civilisations (Rome, Grèce, Égypte, Chine) : 50
  - Événements 20e siècle : 50
```

#### 1C. Littérature/Art/Philosophie (+150 faits)

```
Ajouter : 150 faits culturels
  - Auteurs et œuvres majeures : 50
  - Courants artistiques : 30
  - Philosophes et concepts : 40
  - Musique/compositeurs : 30
```

#### 1D. Culture générale (+500 faits)

```
Ajouter : 500 faits variés
  - Sciences (déjà bon) : 100
  - Corps humain/santé : 100
  - Nature/animaux : 100
  - Technologies : 100
  - Sports, cuisine, divers : 100
```

#### 1E. Connaissances « conversationnelles » (+200 faits)

```
Ajouter : 200 faits pour la conversation
  - Proverbes, citations : 50
  - Définitions de concepts abstraits (liberté, justice...) : 50
  - Faits divers connus : 50
  - Auto-connaissance (qui est KA) : déjà fait
```

**Méthode :** Génération automatique par LLM externe (DeepSeek) → extraction de triplets → ingestion. Script existant : `expand_kb_v2.py`.

**Effort :** ~2 jours (principalement génération + nettoyage)
**Impact :** +30% sur géographie, histoire, littérature, culture

---

### Bloc 2 — Multilingue : Réponses en anglais

Actuellement, les questions EN reçoivent des réponses FR incohérentes. La détection de langue existe déjà (`detect_language()` dans `domain_detector.py`).

#### 2A. Templates de réponse EN

```
Ajouter dans response_composer.py :
  - _OPENINGS_EN, _ADDITIONS_EN, _CONCLUSIONS_EN
  - Templates par type (definition, mechanism, comparison) en EN
  - Salutations EN déjà faites dans domain_detector.py
```

#### 2B. Base de connaissance EN

```
Ajouter 100+ faits en anglais dans les domaines clés :
  - "paris", "is the capital of", "France", "GEOGRAPHY"
  - "einstein", "discovered", "relativity", "PHYSICS"
  - "shakespeare", "wrote", "Hamlet", "LITERATURE"
```

#### 2C. Routage langue dans le pipeline

```
Dans harmonic_ai.ask() :
  if detect_language(question) == 'en':
      utiliser templates EN
      chercher faits EN d'abord
      réponse en EN
```

**Effort :** ~3 jours
**Impact :** +50% sur multilingue

---

### Bloc 3 — Grammaire et formatage des réponses

Les réponses actuelles sont souvent grammaticalement pauvres : `tokyo se définit comme Japon` au lieu de `Tokyo est la capitale du Japon`.

#### 3A. Détection de la RELATION attendue

```
Quand la question est "Quelle est la capitale de X ?"
  → La réponse attendue est "Y est la capitale de X"
  → Le fait dans la KB est (Y, est la capitale de, X)
  → Template : "{sujet_fait} est la capitale de {objet_fait}"

Quand la question est "Qui a [verbe] X ?"
  → Réponse attendue : "C'est [sujet] qui a [verbe] [objet]"
  → Template : "C'est {sujet} qui {relation} {objet}"
```

#### 3B. Capitalisation et accents

```
Fonction simple à ajouter :
  def format_response(text):
      # Capitaliser début de phrase
      # Capitaliser noms propres (Paris, Tokyo, Einstein)
      # Corriger accents manquants
      # Remplacer "C'est tokyo" → "C'est Tokyo"
```

#### 3C. Variété dans les réponses

```
Pour la même question posée différemment :
  "capitale du Japon" → "Tokyo est la capitale du Japon."
  "Quelle est la capitale du Japon ?" → "La capitale du Japon est Tokyo."
  "Japon capitale" → "Tokyo."

  → Utiliser 3-4 templates différents selon le type de question
```

**Effort :** ~2 jours
**Impact :** +15% qualité perçue (même avec les mêmes faits)

---

### Bloc 4 — Raisonnement multi-étapes

Actuellement, le raisonnement est limité à 1-2 sauts dans le graphe de connaissances.

#### 4A. Chaînes de raisonnement

```
Ajouter dans reasoning_engine.py :
  - Détection de questions "pourquoi" → remonter la chaîne causale
  - Détection de questions "comment" → décrire la séquence
  - Utiliser find_paths avec profondeur 3 au lieu de 2
```

#### 4B. Raisonnement par analogie

```
Ajouter :
  - "Quelle est la différence entre A et B ?"
    → Trouver faits sur A, faits sur B, comparer
  - "En quoi A et B se ressemblent-ils ?"
    → Trouver attributs communs
```

**Effort :** ~3 jours
**Impact :** +25% sur raisonnement

---

### Bloc 5 — Conversation multi-tours

Le contexte de conversation existe déjà (`conversation.py`) mais est mal utilisé.

#### 5A. Mémoire de conversation améliorée

```
Problème actuel : "virus difference bacterie" reçoit le contexte "lumière"
  → Le contexte est injecté même quand il n'est pas pertinent

Solution :
  - Ne PAS injecter le contexte pour une nouvelle question complète
  - Injecter UNIQUEMENT pour les vrais follow-ups ("et pourquoi ?", "et comment ?")
  - Déjà implémenté dans _enrich_with_context() mais le seuil est trop bas
  → Augmenter le seuil de détection de follow-up
```

#### 5B. Suivi de thème

```
Quand l'utilisateur pose une série de questions sur le même sujet :
  Q1: "Parle-moi de Einstein"
  Q2: "Qu'a-t-il découvert ?" → détecter "il" → réfère à Einstein
  Q3: "Et quand ?" → détecter "Et" → follow-up sur la dernière réponse
```

**Effort :** ~2 jours
**Impact :** +20% sur conversation

---

### Bloc 6 — Créativité texte long

L'IA génère déjà des haïkus, métaphores, connexions créatives. Mais pour le « writing » de LM Arena, il faut du texte plus long.

#### 6A. Génération de paragraphes

```
Ajouter à response_composer.py :
  - Mode "essai" : 3-5 paragraphes sur un sujet
  - Mode "histoire courte" : structure narrative
  - Mode "poème" : déjà existant (haiku), ajouter sonnet, vers libres
```

#### 6B. Style variable

```
Ajouter :
  - Style "académique" : formel, précis
  - Style "vulgarisation" : simple, analogies
  - Style "poétique" : métaphores, rythme
  → Détecter le style demandé dans la question
```

**Effort :** ~3 jours
**Impact :** +10% sur writing (déjà bon à 90%)

---

## 2. CALENDRIER

```
SEMAINE 1 (Jours 1-7) : KB + Multilingue
  ✅ Bloc 1A : Géographie (+200 faits) — 2j
  ✅ Bloc 1B : Histoire (+200 faits) — 1j
  ✅ Bloc 1C-D : Lit/Art/Culture (+650 faits) — 2j
  ✅ Bloc 2A-B : Templates EN + KB EN — 2j
  → Objectif : +40% sur géo/histoire/lit

SEMAINE 2 (Jours 8-14) : Grammaire + Raisonnement
  ✅ Bloc 1E : Faits conversationnels (+200) — 1j
  ✅ Bloc 3 : Grammaire/formatage — 2j
  ✅ Bloc 4 : Raisonnement multi-étapes — 3j
  ✅ Bloc 2C : Routage langue — 1j
  → Objectif : +15% qualité perçue, +25% raisonnement

SEMAINE 3 (Jours 15-21) : Conversation + Créativité
  ✅ Bloc 5 : Conversation multi-tours — 2j
  ✅ Bloc 6 : Créativité texte long — 3j
  ✅ Tests intensifs — 2j
  → Objectif : +20% conversation, +10% writing

SEMAINE 4 (Jours 22-30) : Tests + Soumission
  ✅ Tests LM Arena simulés (100 questions) — 3j
  ✅ Corrections finales — 2j
  ✅ Préparation soumission LM Arena — 2j
  → Objectif : score global > 70%
```

---

## 3. RESSOURCES NÉCESSAIRES

| Ressource | Disponible ? | Action |
|-----------|-------------|--------|
| LLM pour génération de faits | ✅ DeepSeek API | Utiliser `expand_kb_v2.py` |
| Corpus géographie | ❌ | Générer via LLM |
| Corpus histoire | ❌ | Générer via LLM |
| Corpus littérature | ❌ | Générer via LLM |
| Traductions EN | ❌ | Générer via LLM ou traduire les faits FR |
| Testeurs humains | ❌ | Faire des tests automatisés |

---

## 4. MÉTRIQUES DE SUCCÈS

```
Le plan est réussi si :

  ✅ "What is the capital of Japan?" → "Tokyo is the capital of Japan."
  ✅ "Qui a peint la Joconde ?" → "Léonard de Vinci a peint la Joconde."
  ✅ "Quand a eu lieu la Révolution française ?" → "En 1789."
  ✅ "Pourquoi le ciel est-il bleu ?" → explication causale multi-étapes
  ✅ "Raconte-moi une histoire sur un chat" → texte créatif 100+ mots
  ✅ "Quelle est la différence entre..." → comparaison structurée
  ✅ Follow-up contextuel : "Et quand ?" → utilise le contexte
  ✅ Benchmark global > 70%

Actuellement : 4/8 critères validés (capitales, dates, pourquoi, différence)
À faire : multilingue, histoire créative, follow-up contextuel
```

---

## 5. CE QUI NE SERA PAS FAIT (limites assumées)

```
❌ Coding : nécessiterait un interpréteur Python intégré → trop lourd
❌ Actualités : nécessiterait une connexion internet → hors-scope
❌ Mathématiques avancées (calcul intégral, équations différentielles)
   → SymPy peut le faire mais l'intégration est complexe
❌ Images / multimodal → infrastructure inexistante
❌ Voix / audio → existe (phi_diffusion_engine.py) mais pas pour LM Arena

Ces limitations seront COMMUNIQUÉES dans la description du modèle
sur LM Arena. L'IA sera positionnée comme :
  "Expert sciences et culture générale. Pas de coding, pas d'actualités."
```

---

## 6. IMPLÉMENTATION PRIORITAIRE (à faire maintenant)

Si on ne peut faire qu'UNE chose maintenant, c'est le **Bloc 1** (extension KB) car :
- C'est le plus simple (génération automatique)
- C'est le plus impactant (touche 4 catégories LM Arena)
- C'est le moins risqué (pas de changement d'architecture)

**Commande immédiate suggérée :** Générer 500 faits de géographie + histoire via LLM, les ingérer, et relancer le benchmark.
