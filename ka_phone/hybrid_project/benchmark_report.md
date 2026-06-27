# Rapport Benchmark LM Arena — KA Hybrid

**Date :** 2026-06-11 12:25
**Questions :** 160
**Modele :** deepseek-chat (API) + Hologramme ABC 1024x1024

## Resume Global

| Metrique | Valeur |
|---|---|
| Questions traitees | 160 |
| Reponses verifiees | 147/160 (92%) |
| Via API DeepSeek | 135/160 (84%) |
| Hallucinations detectees | 73/160 (46%) |
| Tracabilite moyenne | 80.6% |
| Temps de reponse moyen | 2389ms |
| Faits moyens par requete | 133 |

## Performance par Domaine

| Domaine | Questions | Trace Moy. | Temps Moy. | Hallucinations |
|---|---|---|---|---|
| agriculture | 1 | 64% | 5273ms | 1 |
| cooking | 1 | 100% | 3500ms | 0 |
| cosmology | 1 | 33% | 3571ms | 1 |
| culture | 15 | 79% | 2711ms | 7 |
| economics | 1 | 50% | 2432ms | 1 |
| engineering | 1 | 100% | 3707ms | 0 |
| environment | 1 | 33% | 3117ms | 1 |
| general | 1 | 80% | 5047ms | 1 |
| geography | 20 | 87% | 2106ms | 5 |
| health | 10 | 71% | 3289ms | 6 |
| history | 20 | 84% | 2406ms | 9 |
| logic | 15 | 85% | 2605ms | 6 |
| math | 30 | 92% | 797ms | 5 |
| philosophy | 1 | 100% | 3089ms | 0 |
| physics | 1 | 100% | 3261ms | 0 |
| politics | 1 | 100% | 3993ms | 0 |
| programming | 10 | 68% | 2408ms | 7 |
| science | 30 | 71% | 3144ms | 23 |

## Distribution des Scores de Tracabilite

```
   0-10% | 1
  10-20% | 0
  20-30% | 1
  30-40% |#### 10
  40-50% | 1
  50-60% |########### 24
  60-70% |######### 20
  70-80% |### 7
  80-90% |#### 9
 90-100% | 0
    100% |######################################## 87

```

## Top 5 Questions (Meilleure Tracabilite)

- **100%** — Quelle est la capitale du Senegal ?
  Reponse : D'après ma connaissance externe (l'hologramme ne contient pas cette information), la capitale du Sénégal est Dakar....
- **100%** — Combien de continents y a-t-il ?
  Reponse : Selon mes connaissances générales, il y a généralement **7 continents** : Afrique, Amérique du Nord, Amérique du Sud, An...
- **100%** — Quelle est la capitale du Bresil ?
  Reponse : D'après ma connaissance externe (l'hologramme ne contient pas cette information), la capitale du Brésil est **Brasília**...
- **100%** — Ou se trouve le desert du Sahara ?
  Reponse : Le désert du Sahara se trouve principalement en Afrique du Nord. Il s'étend sur plusieurs pays, dont l'Algérie, le Maroc...
- **100%** — Quel ocean borde la cote ouest de l'Afrique ?
  Reponse : D'après ma connaissance externe (l'hologramme ne contient pas cette information), l'océan qui borde la côte ouest de l'A...

## Top 5 Questions (Plus Faible Tracabilite)

- **33%** — Qu'est-ce que l'hypertension ?
  Reponse : D'après ma base de connaissance principale (l'hologramme d'ondes universelles), je ne dispose d'aucune information spéci...
- **33%** — Qu'est-ce que le rechauffement climatique ?
  Reponse : Le réchauffement climatique désigne l'augmentation progressive de la température moyenne de la surface terrestre, princi...
- **33%** — Qu'est-ce que le Big Bang ?
  Reponse : Le Big Bang est le modèle cosmologique dominant décrivant l'origine de l'Univers. Selon cette théorie, l'Univers a comme...
- **25%** — Comment fonctionne la vaccination ?
  Reponse : Je ne dispose pas d'informations spécifiques sur la vaccination dans l'hologramme d'ondes universelles. 

Cependant, d'a...
- **0%** — Dans une course, je double le deuxieme. Quelle est ma position ?
  Reponse : Si tu doubles le deuxième, tu prends sa place, donc tu deviens **deuxième**....

## Configuration

- Hologramme : ABC 1024x1024, 961 patches
- Mapping : spatial + semantique (TF-IDF)
- Faits QuickFacts : 950
- LLM : DeepSeek API (deepseek-chat)
- Temperature : 0.3
- System prompt : contrainte stricte de non-invention
- Verification : couche 4 active

---

*Rapport genere automatiquement par benchmark_lm_arena.py*
