---
name: wave-ir-compiler
description: >-
  Compiler, analyser et exécuter des programmes ondulatoires via le Wave IR (AST) et le compilateur
  harmonique. Utilise ce skill dès que l'utilisateur veut parser du code ondulatoire, manipuler un AST,
  sérialiser en JSON (to_json/from_json), valider un programme, appliquer les passes d'optimisation
  (constant folding, dead code elimination, operator fusion, memory pool), compiler vers Python,
  exécuter un programme ondulatoire, vérifier un roundtrip parse→print, ou parle de Wave IR, AST,
  wave_ir, wave_compiler, nœuds Bind/Encode/Query, hologrammes — même sans le dire explicitement.
---

# Wave IR & Compilateur — d'un programme ondulatoire au résultat exécuté

Le **Wave IR** est la représentation intermédiaire entre le code source ondulatoire (texte) et le
backend d'exécution (NumPy aujourd'hui, FPGA demain). Le **compilateur** applique 4 passes
d'optimisation puis exécute.

```
Code source ondulatoire ──parse──▶ AST (Wave IR) ──compile──▶ AST optimisé ──execute──▶ résultat
        wave_ir.parse()              validate()              4 passes            env
```

Implémentations : `vital-ka/core/python/wave_ir.py` (~900 lignes, 23 nœuds) et
`vital-ka/core/python/wave_compiler.py` (~600 lignes). Pour les importer, ajouter au `sys.path` les
3 dossiers suivants (ensemble minimal vérifié) : `vital-ka/core/python`, `vital-ka/backend/hologram`
(holographic_encoder), `vital-ka/backend/inference` (prompt_parser).

## Quand utiliser ce skill

- L'utilisateur fournit du code ondulatoire (texte) et veut le valider, l'optimiser ou l'exécuter.
- Il faut inspecter/transformer un AST (visite, remplacement de nœuds), le sérialiser en JSON pour
  le réseau, ou le désérialiser.
- Il faut expliquer ce que font les passes d'optimisation ou diagnostiquer un programme qui ne
  s'exécute pas (variables non définies, redéfinitions, erreurs de type).
- Il faut générer un programme en code ondulatoire programmatiquement (make_fact, make_query, …).

## Pipeline standard

```python
from wave_ir import parse, validate, to_json, from_json, Program
from wave_compiler import WaveCompiler

source = '''
ψ_q = ENCODE "Qu'est-ce que la lumière ?"
QUERY ψ_r = ψ_q FROM H_connaissances
reponse = DECODE(ψ_r)
RETURN reponse
'''

# 1. Parser
program = parse(source)                     # → Program (AST)

# 2. Valider (variables non définies, redéfinitions)
errors = validate(program)
assert not errors, errors

# 3. Sérialiser / transmettre (roundtrip parfait)
json_str = to_json(program)                 # AST → JSON
program2 = from_json(json_str)              # JSON → AST
assert to_json(program2) == json_str        # bit à bit

# 4. Compiler (4 passes d'optimisation)
compiler = WaveCompiler()
result = compiler.compile(program)          # CompileResult (ast optimisé + stats)
# result.stats contient les compteurs de chaque passe (ex. folds, dead_code, fusions…)

# 5. Exécuter (avec les hologrammes nécessaires)
env = compiler.execute(program, holograms={"H_connaissances": ma_mémoire})
# env contient les variables du programme (env["reponse"] = …)
```

## Les 4 passes d'optimisation

1. **Constant Folding** — les `ENCODE` de chaînes constantes sont pré-calculés et partagés
   (`ENCODE "lumiere"` ne se calcule qu'une fois, même répété).
2. **Dead Code Elimination** — supprime les variables assignées mais jamais utilisées.
3. **Operator Fusion** — `BIND(BIND(a,b), c)` → `BIND_MANY(a,b,c)` (3 FFT + 1 IFFT au lieu de 2 IFFT) ;
   fusion de `NORMALIZE(ENCODE(x))`, `SUPERPOSE`, `INTERFERE`, `EMERGE`, `OPPOSE`, `AMPLIFY`, `FILTER`.
4. **Memory Pool** — 16 buffers complexes pré-alloués réutilisés (≈48 % de réutilisation mesurée).

## Exécution avec hologrammes

`QUERY … FROM H_nom` a besoin de l'hologramme correspondant dans `holograms={...}` :

```python
from wave_lang import HolographicMemory, encode
mem = HolographicMemory()
mem.store(encode("lumière"), encode("est"), encode("une onde électromagnétique"))
env = compiler.execute(program, holograms={"H_connaissances": mem})
```

Sans hologramme fourni, l'exécution échoue proprement : il faut alors soit le créer, soit remplacer
`QUERY` par des opérations directes (`resonate` sur un vocabulaire).

## Construire des programmes sans texte

Le module `wave_ir` expose des constructeurs prêts à l'emploi :

| Fonction | Programme généré |
|---|---|
| `make_fact(sujet, relation, obj)` | `STORE ψ_fait = BIND_MANY(...) IN H` |
| `make_query(question, hologram="H_connaissances")` | `ENCODE → QUERY → DECODE → RETURN` |
| `make_reasoning(premise_a, premise_b, conclusion_var)` | `ENCODE → QUERY → SUPERPOSE → EMERGE → DECODE` |
| `make_creativity(concept_a, concept_b, epsilon=0.15)` | `ENCODE → INTERFERE → DECODE` |

## Manipulation d'AST

- `walk(node, visitor)` — visite tous les nœuds (analyse, comptage).
- `map_nodes(node, transform)` — construit un nouvel AST avec les nœuds transformés.
- Chaque nœud (`Encode`, `Bind`, `Assign`, `Query`, …) expose `to_dict()`, `children()`, `to_wave()`.
- Les 23 nœuds (5 statements, 18 expressions) sont détaillés dans `references/ast.md`.

## Vérifications à toujours faire

1. **Roundtrip** : `to_json(parse(print(program))) == to_json(program)` — la sortie doit être
   identique bit à bit (le document fondateur l'exige).
2. **Validation** : `validate()` doit retourner une liste vide.
3. **Reproductibilité** : deux exécutions du même programme avec les mêmes hologrammes donnent le
   même résultat (tout est déterministe).
4. **Benchmark** : `benchmark(compiler, program, n_runs=100)` mesure le gain des passes
   (référence doc : forward pass attention 8464 ms → 261 ms float64 → 169 ms float32).

## Erreurs fréquentes

- `QUERY` sans hologramme dans `holograms={}` → fournir la mémoire ou le vocabulaire.
- Variable utilisée avant `Assign` → `validate()` le signale ; corriger le programme source.
- Oublier `RETURN` → le programme n'expose pas de résultat ; l'ajouter.
- Chaînes non échappées dans le source (guillemets imbriqués) → utiliser l'autre délimiteur
  `'...'` ou `"..."` pour l'expression.
