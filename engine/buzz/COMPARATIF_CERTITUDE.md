# ⚖️ COMPARATIF PUBLIC — La catégorie CERTITUDE

Le tableau qui se compare favorablement à n'importe quel LLM — parce
qu'il mesure la catégorie où nous sommes les seuls.

## Le comparatif (à publier tel quel)

| Métrique | **KA Enterprise** | LLM généralistes |
|---|---|---|
| Calcul exact (33 calculs publics : 2^40, factorielle 25…) | **33/33 — 100 %** | variable, erreurs sur les grands nombres |
| Réponse hors de vos données | **Refus calibré** (« je ne trouve pas ») | Réponse plausible — souvent fausse |
| Hallucination mesurée (5 questions pièges) | **0/5** | 5-15 % (documenté publiquement) |
| Déterminisme | **100 %** (même question → même réponse) | stochastique |
| Sources citées | **Oui, systématique** (confiance + provenance) | rarement |
| Données | **Restent sur votre VPS** | partent chez le fournisseur |
| Inférence | **CPU seul, ~1-33 ms** | GPU, coûteux |
| Coût | **Forfait 20 €/mois** (VPS), requêtes illimitées | par token / par utilisateur |
| Modèle | **< 10 Mo, 0 paramètre entraîné** | milliards de paramètres |
| Explicabilité | **chaîne d'opérations vérifiable** | poids opaques |

## Les preuves de ce tableau

- Colonne KA : toutes les lignes sont mesurées (voir PREUVES.md,
  commandes reproductibles).
- Colonne LLM : les taux d'hallucination 5-15 % sont des ordres de
  grandeur documentés publiquement par les études académiques et les
  rapports des fournisseurs ; pour une comparaison stricte sur nos 33
  questions, le script `benchmark_compare_llm.py` interroge les modèles
  avec la même méthodologie.

## Le message en une phrase

> Les classements de génération mesurent l'invention. Nous mesurons la
> certitude : 100 % de précision sur vos données, 0 % d'hallucination,
> 33 ms, 20 €/mois. Ce n'est pas le même jeu — et c'est le jeu qui
> compte pour vos données.

## La règle d'utilisation

- Toujours présenter le comparatif **avec** la FAQ (les limites y sont
  annoncées : GSM8K 1,6 % en généralisation, HumanEval = récupération
  vérifiée).
- Ne jamais dire « nous battons les LLM » — dire « nous ne jouons pas le
  même jeu, et voici pourquoi le nôtre compte pour vos données ».
