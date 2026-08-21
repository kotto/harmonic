# Les 10 intentions — génération détaillée

Source : `DOCUMENT_FONDATEUR_LANGAGE_ONDULATOIRE.md` §8, implémentation
`vital-ka/core/python/wave_code_generator.py`.

## Détecteur d'intention (`WaveIntentDetector`)

- `detect_wave_intent(question) -> (intent, score)` — détecte l'une des 10 intentions par marqueurs
  lexicaux, retourne l'intention + un score de confiance.
- Hérite de `PatternDetector` : les patterns sont des listes de marqueurs par intention
  (voir le tableau ci-dessous).

## Les 10 générateurs

| Méthode | Intention | Marqueurs | Programme généré |
|---|---|---|---|
| `_make_query` | query | « qu'est-ce que », « explique », « définis » | `ENCODE question → QUERY FROM H → DECODE → RETURN` |
| `_make_reasoning` | reason | « pourquoi », « déduis », « donc » | `ENCODE → QUERY → SUPERPOSE → EMERGE → DECODE` |
| `_make_creative` | creative | « imagine », « crée », « et si » | `ENCODE a → ENCODE b → INTERFERE(a, b, ε) → DECODE` |
| `_make_store_fact` | store_fact | « souviens-toi », « mémorise » | `ENCODE sujet/relation/objet → BIND_MANY → STORE IN H → DECODE` |
| `_make_compare` | compare | « différence », « versus » | `ENCODE a → ENCODE b → RESONANCE → OPPOSE → DECODE` |
| `_make_analogy` | analogize | « comme », « analogie » | `ENCODE → BIND → UNBIND → DECODE` |
| `_make_sample` | sample | « échantillonne », « température », « top-k », « top-p » | `ENCODE → RESONANCE → DECODE(top_k) → RETURN` |
| `_make_tool_use` | tool_use | « utilise l'outil », « appelle », « exécute » | `ENCODE intention → ENCODE outil → BIND → DECODE → RETURN` |
| `_make_evaluate` | evaluate | « évalue », « perplexité », « qualité », « confiance » | `ENCODE q → ENCODE ref → RESONANCE → DECODE → RETURN` |
| `_generate_query_program` | classify | « catégorise », « type » | `ENCODE → RESONANCE` avec prototypes |

## Modules complémentaires associés

Les 3 nouvelles intentions s'appuient sur des modules domaines existants :

| Intention | Module associé | Classe/Fonction principale |
|---|---|---|
| `sample` | `wave_sampling.py` | `WaveSampler.sample(psi, temperature, top_p, top_k)` |
| `tool_use` | `wave_tool_use.py` | `WaveToolUse.resolve_and_execute(intention)` |
| `evaluate` | `wave_perplexity.py` | `coherence_perplexity(scores)`, `confidence(scores)`, `generation_quality(seq, vocab)` |

## Exemples de sorties

### query
```
ψ_q = ENCODE "Qu'est-ce que la lumière ?"
QUERY ψ_r = ψ_q FROM H_connaissances
reponse = DECODE(ψ_r)
RETURN reponse
```

### creative
```
ψ_a = ENCODE "pluie"
ψ_b = ENCODE "musique"
ψ_c = INTERFERE(ψ_a, ψ_b, 0.15)
poeme = DECODE(ψ_c)
RETURN poeme
```

### sample
```
ψ_contexte = ENCODE "Échantillonne avec température 0.8..."
ψ_question = ENCODE "créativité"
echantillon = DECODE(ψ_contexte, top_k=50)
RETURN echantillon
```

### tool_use
```
ψ_intention = ENCODE "Utilise l'outil calculer pour résoudre 2+2"
ψ_outil = ENCODE "calculer"
ψ_action = BIND(ψ_intention, ψ_outil)
resultat = DECODE(ψ_action)
RETURN resultat
```

### evaluate
```
ψ_q = ENCODE "Évalue la qualité de la réponse..."
ψ_ref = ENCODE "qualité"
coherence_score = RESONANCE(ψ_q, ψ_ref)
evaluation = DECODE(ψ_q, top_k=3)
RETURN coherence_score
```

### store_fact
```
ψ_s = ENCODE "la lumière"
ψ_r = ENCODE "est"
ψ_o = ENCODE "une onde électromagnétique"
ψ_fait = BIND_MANY(ψ_s, ψ_r, ψ_o)
STORE ψ_fait = ψ_fait IN H_connaissances
RETURN "fait mémorisé"
```

### compare
```
ψ_a = ENCODE "amour"
ψ_b = ENCODE "amitié"
similarite = RESONANCE(ψ_a, ψ_b)
ψ_diff = OPPOSE(ψ_a, ψ_b)
analyse = DECODE(ψ_diff)
RETURN analyse
```

## Extraction de concepts (`_extract_concepts`)

- Retire les mots-outils : articles, pronoms, formes du verbe être, mots interrogatifs.
- Retourne les entités porteuses de sens de la question.
- Utilisée par les générateurs pour choisir les arguments d'ENCODE.

## Parsing de fait (`_parse_fact`)

- Extrait `(sujet, relation, objet)` d'une phrase factuelle.
- Utilisée par `_make_store_fact` : si la phrase n'est pas analysable comme fait, l'intention
  retombe sur `query`.

## Sortie Python (`wave_to_python`)

`wave_to_python(program) -> str` émet un script Python équivalent utilisant les primitives
`wave_lang` (encode, bind, superpose, resonate, …) et les modules complémentaires
(wave_sampling, wave_tool_use, wave_perplexity). Chaque statement est émis par `_stmt_to_python`,
chaque expression par `_expr_to_python`. Le script est exécutable tel quel dans un environnement
avec `wave_lang` importable.

## Critères de validation (document fondateur §10.3)

| Test | Attendu |
|---|---|
| 10 intentions détectées | query, reason, creative, store_fact, compare, analogize, sample, tool_use, evaluate, classify |
| AST généré valide | 100 % |
| Roundtrip généré → re-parsé | identique |
| Compilation vers Python | exécutable |
| Sérialisation JSON | transmissible |
