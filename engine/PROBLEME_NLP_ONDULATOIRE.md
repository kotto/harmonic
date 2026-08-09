# Problème : Traduction Langage Naturel → Programme Ondulatoire pour le Raisonnement Mathématique

## Contexte

Nous construisons un système de raisonnement mathématique basé sur la **Théorie Harmonique Universelle (THU)**, où toute computation est exprimée comme des opérations sur des ondes dans ℂ⁵¹².

L'architecture est **bicouche** :

### Couche 1 : Noyau Mathématique Ondulatoire (PROUVÉ)
- **PhaseEncoder** : addition/soustraction par rotation de phase. 4000/4000 opérations exactes vérifiées.
- **LogEncoder** : multiplication/division sur grille logarithmique 16384 points. Couvre [e⁻⁵⁰, e⁵⁰].
- **HRR** (Holographic Reduced Representations) : `bind(ψ_a, ψ_b)` = convolution circulaire (réversible), `unbind(ψ_bound, ψ_key)` ≈ ψ_value, `superpose(ψ₁, ψ₂, ...)` = mémoire holographique.
- **AlgebriqueReasoner** : équations avec dépendances et évaluation lazy. Résout correctement cross-multiplication et rate×time.
- **Filtre Dynamique** : noyau ABC K(t) = B(α)·E_α(-αt^α/(1-α)) avec α = 1/φ ≈ 0.618. Zéro paramètre libre (α est une constante fondamentale). Agit comme GATE : élimine le bruit narratif, ne garde que le contenu mathématique.

Ce noyau est **vérifié et stable**.

### Couche 2 : Traducteur NLP Langage Naturel → Opérations Ondulatoires (BLOQUÉ)
Ce module doit convertir un problème en langage naturel (ex: "John has 5 apples. Mary has 3 times as many.") en une séquence d'opérations ondulatoires exécutables :
```
HAS("john", "apples", 5)
TIMES_AS_MANY("mary", 3)  → résolu en : mary.apples = john.apples × 3
QUERY("mary", "apples")   → 15
```

## Le Plafond

Sur le benchmark GSM8K (problèmes mathématiques de niveau primaire/collège, 200 problèmes de test) :

| Approche NLP testée | Accuracy |
|---------------------|----------|
| Règles regex manuelles (15 règles) | 1.0% |
| Filtre harmonique statique (multi-filtres) | 0.5% |
| Filtre dynamique ABC (α=1/φ) | 0.5% |
| k-NN structurel (recherche par similarité d'ondes) | 0.5% |
| Data mining grammatical (721 règles extraites) | 2.5% |
| MiniLM (22M params) + Régression Logistique | 2.5% |
| T5-small fine-tuné (LoRA, 344K params entraînables) | 3.6% |

**Plafond : ~2-3%.** Sur 15 exemples « jouets » soigneusement choisis, toutes les approches atteignent 100%. L'écart 100% → 2.5% révèle que les exemples jouets ne sont pas représentatifs du vrai GSM8K.

## Diagnostic

Le goulot d'étranglement n'est pas la **détection d'opération** (MiniLM classifie correctement le TYPE d'opération : HAS, GAIN, LOSE, MULT, DIV, TIMES_AS_MANY, CROSS_MULT à 58% sur 4037 phrases d'entraînement). Le goulot est l'**extraction des paramètres** :

Pour exécuter `HAS(entity, object, value)`, il faut extraire DE LA PHRASE :
- **entity** : qui possède ? ("John", "Mary", "the bakery")  
- **object** : quoi ? ("apples", "cookies", "dollars")
- **value** : combien ? (5, 10, 3)

La résolution actuelle est purement heuristique :
- Entité : premier mot capitalisé → "John" ✅, mais "A bakery" → entité = None ❌
- Objet : dernier nom commun avant le nombre → "apples" dans "has 5 apples" ✅, mais "pencils" dans "each box has 5 pencils" → objet = "box" ❌ (devrait être "pencils")
- Valeur : premier nombre dans la phrase → 5 ✅, mais "3 times as many" → valeur = 3, or ce 3 est un MULTIPLICATEUR, pas une valeur absolue ❌
- Coréférence : "He buys 3 more" → He = John ✅ (via last_entity), mais "They sell 9 loaves" → They = bakery ❌ (le filtre à pronoms bloque "They")

Ces heuristiques fonctionnent pour les 15 exemples jouets (100%) mais s'effondrent sur les vrais problèmes GSM8K où :
- Les entités sont implicites ("A bakery", "There are 6 boxes")
- Les objets changent entre les phrases ("loaves" → "bread")
- Les nombres ont des rôles différents (valeur absolue vs multiplicateur vs taux)
- La coréférence traverse 3+ phrases

## Contrainte Architecturale

Le traducteur NLP doit produire des **opérations ondulatoires**, pas des calculs directs. La sortie doit être :
```
HAS(entity="john", object="apples", value=5)
GAIN(entity="john", value=3)  -- l'objet est implicite (last_object)
TIMES_AS_MANY(entity="mary", multiplier=3)  -- la référence est implicite (autre entité avec même objet)
```

Ces opérations sont ensuite exécutées par la machine ondulatoire :
```python
ψ_state = superpose(
    bind(bind(encode("john"), encode("apples")), encode("5")),
    bind(bind(encode("mary"), encode("apples")), encode("15")),
)
answer = unbind(ψ_state, bind(encode("mary"), encode("apples")))  # → 15
```

## Question

Comment extraire de manière robuste les paramètres (entity, object, value, role) d'une phrase de problème mathématique pour les traduire en opérations ondulatoires, sachant que :

1. Le module doit rester **léger** (le noyau ondulatoire fait le calcul lourd, le NLP est un compilateur)
2. On dispose de **1101 problèmes d'entraînement** annotés avec leurs chaînes d'opérations `<<a+b=c>>`
3. L'extraction par motifs (regex, règles) plafonne à ~2.5%
4. L'extraction par similarité (k-NN, MiniLM cosine) plafonne aussi à ~2.5%
5. La piste « entraîner un T5-small » donne 3.6% mais le modèle génère des opérations syntaxiquement correctes et mathématiquement fausses (5×3=20)

L'approche doit être compatible avec l'architecture modulaire : le NLP est un **compilateur** (langage humain → langage ondulatoire) interchangeable sans toucher au noyau mathématique.

## Fichiers Clés (dans le workspace)

- `engine/compilateur_thu.py` — compilateur THU complet (GATE + grammaire + MiniLM + exécution)
- `engine/raisonneur_ondulatoire.py` — HRR reasoner + pipeline algébrique
- `engine/wave_lang.py` — 13 primitives ondulatoires (encode, bind, unbind, superpose, resonate...)
- `engine/encodage_phase.py` — PhaseEncoder (addition/soustraction par rotation de phase)
- `engine/encodage_logarithmique.py` — LogEncoder (multiplication/division)
- `engine/filtre_dynamique.py` — Filtre ABC (noyau de Mittag-Leffler, α=1/φ)
- `engine/train_minilm_operations.py` — Entraînement MiniLM pour classification d'opérations
- `engine/extraire_grammaire.py` — Data mining grammatical (721 règles extraites)
- `engine/data/benchmarks/gsm8k_test.jsonl` — 1319 problèmes GSM8K avec annotations `<<...>>`
