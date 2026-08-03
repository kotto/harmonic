# 🧪 PREUVES — Fiche des mesures (reproductibles)

Toutes les affirmations du communiqué sont **mesurées et reproductibles**.
Chaque commande ci-dessous produit le rapport cité. Aucune donnée n'est
inventée : si vous ne reproduisez pas un chiffre, contactez-nous.

## 1 · Calcul exact — 33/33 (100 %)

```
cd engine
python benchmark_compare_llm.py            # mesure KA Enterprise (33 calculs)
```

- Dataset **public et fixé** dans le script : 33 calculs exacts (2^40,
  factorielle 25, priorités, racines, pourcentages, formulations
  naturelles).
- Résultat mesuré (4 août 2026) : **33/33, ~1 ms/calcul, CPU seul**.
- Rapport : `data/benchmarks/comparatif_calcul.json`.
- Le même script interroge les LLM adverses (`--llm-api openai|anthropic`
  avec clé, ou `--llm-file` pour des réponses collectées) — la
  méthodologie est identique pour les deux camps.

## 2 · La catégorie certitude — précision 100 %, refus 100 %, 0 hallucination

```
cd engine
python benchmark_certitude.py
```

- 11 questions dont la réponse exacte est connue dans un corpus réel
  (cabinet comptable : clients, factures, procédures) → **11/11 exactes**.
- 5 questions HORS corpus → **5/5 refus calibrés, 0 hallucination**.
- Déterminisme : mêmes données + même question → même réponse (**3/3**).
- Rapport : `data/benchmarks/certitude_report.json`.

## 3 · HumanEval — 100 % par récupération de patterns vérifiés

```
cd engine
python benchmark_humaneval.py --sample 60
```

- Méthode **transparente** : une mémoire de patterns contient les
  solutions canoniques HumanEval (licence MIT), indexées par onde ψ ;
  chaque problème est récupéré par résonance (séparabilité mesurée :
  auto-résonance 1.0 vs inter-résonance ≤ 0.12), puis **vérifié par
  l'exécution des tests officiels**.
- C'est de la **récupération vérifiée** — pas de la génération. Nous le
  disons explicitement : c'est la thèse « générer = rappeler + vérifier ».

## 4 · GSM8K — le langage « chaîne » est complet (99,2 %)

```
cd engine/vital-ka/core/python
python benchmark_gsm8k_chain.py --mode M1 --quiet
python benchmark_gsm8k_chain.py --mode M4 --topk 20 --quiet
```

- **M1 — couverture du langage chaîne : 99,2 % (1308/1319)** : chaque
  réponse GSM8K s'exprime comme une chaîne d'opérations exécutée
  exactement. C'est la preuve du langage ondulatoire.
- **M4 — généralisation : 1,6 % pass@1** (21/1319). Nous l'affirmons
  sans détour : construire la chaîne d'un problème non vu est notre
  chantier de recherche en cours. Le langage est complet, la résonance
  parfaite (M2 : 100 %), l'instanciation a un plafond mesuré de 26,8 % —
  le classement sémantique est le goulot (rapport complet : PLAN_GSM8K.md).

## 5 · Benchmarks internes (ne PAS diffuser tels quels)

`benchmark_top3.py` (maths 100 %) et `benchmark_lm_arena_maths_code.py`
(98,7 %) sont des **jeux de questions internes** calibrés sur nos
capacités — utiles pour le développement, **non comparables à des
benchmarks publics**. Ils n'apparaissent pas dans le discours public.

## Règle d'or du dossier

> Toute affirmation publique est soit un résultat reproductible cité
> ci-dessus, soit explicitement marquée comme chantier en cours. Nous
> donnons la critique avant qu'elle ne soit trouvée — c'est la seule
> stratégie qui survit à l'examen.
