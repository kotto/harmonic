# Wave IR — les 23 nœuds de l'AST

Source : `DOCUMENT_FONDATEUR_LANGAGE_ONDULATOIRE.md` §6, implémentation `vital-ka/core/python/wave_ir.py`.

## Statements (5)

| Nœud | Champs | Exemple source |
|---|---|---|
| `Program` | `body: List[Statement]` | racine de tout AST |
| `Assign` | `name: str, expr: Expr` | `ψ_q = ENCODE "..."` |
| `Store` | `name: str, expr: Expr, target: str` | `STORE ψ_f = BIND_MANY(...) IN H_connaissances` |
| `Query` | `name: str, expr: Expr, target: str` | `QUERY ψ_r = ψ_q FROM H_connaissances` |
| `Return` | `expr: Expr` | `RETURN reponse` |

## Expressions (18)

| Nœud | Champs |
|---|---|
| `Encode` | `value: str` |
| `Decode` | `expr: Expr` |
| `Bind` | `a: Expr, b: Expr` |
| `Unbind` | `a: Expr, b: Expr` |
| `Superpose` | `exprs: List[Expr]` |
| `Resonance` | `a: Expr, b: Expr` |
| `Rotate` | `expr: Expr, angle: number` |
| `Normalize` | `expr: Expr` |
| `Interfere` | `a: Expr, b: Expr, epsilon?: number` |
| `Diffract` | `expr: Expr, inverse?: bool` |
| `FilterLP` | `expr: Expr, cutoff: number` |
| `FilterHP` | `expr: Expr, cutoff: number` |
| `FilterBP` | `expr: Expr, low: number, high: number` |
| `PhaseShift` | `expr: Expr, shift: number` |
| `Emerge` | `exprs: List[Expr], temperature?: number` |
| `Oppose` | `a: Expr, b: Expr` |
| `Amplify` | `expr: Expr, component: Expr, boost?: number` |
| `BindMany` | `exprs: List[Expr]` |
| `Var` | `name: str` |
| `Literal` | `value: number` |
| `StringLit` | `value: str` |

## API publique (`wave_ir.py`)

| Fonction | Rôle |
|---|---|
| `parse(source: str) -> Program` | Parser EBNF complet (tokenizer + descente récursive) |
| `to_json(node, indent=2) -> str` | Sérialisation JSON (protocole réseau natif) |
| `from_json(data: str|dict) -> Node` | Désérialisation (roundtrip parfait) |
| `validate(node) -> List[str]` | Détecte variables non définies, redéfinitions, erreurs |
| `walk(node, visitor)` | Visite tous les nœuds |
| `map_nodes(node, transform) -> Node` | Transforme l'AST en profondeur |
| `make_fact(sujet, relation, obj) -> Program` | Constructeur STORE |
| `make_query(question, hologram="H_connaissances") -> Program` | Constructeur question |
| `make_reasoning(a, b, var="ψ_conclusion") -> Program` | Constructeur raisonnement |
| `make_creativity(a, b, epsilon=0.15) -> Program` | Constructeur créativité |

Chaque nœud hérite de `Node` : `to_dict()`, `children()`, `to_wave()` (re-génération du texte source),
`__repr__` (pretty-print).

## Grammaire EBNF (rappel)

```
program     ::= statement*
statement   ::= ID '=' expr
              | 'STORE' ID '=' expr 'IN' ID
              | 'QUERY' ID '=' expr 'FROM' ID
              | 'RETURN' expr
expr        ::= 'ENCODE' string
              | 'DECODE' expr
              | 'BIND' '(' expr ',' expr ')'
              | 'UNBIND' '(' expr ',' expr ')'
              | 'SUPERPOSE' '(' expr (',' expr)* ')'
              | 'RESONANCE' '(' expr ',' expr ')'
              | 'ROTATE' '(' expr ',' number ')'
              | 'NORMALIZE' '(' expr ')'
              | 'INTERFERE' '(' expr ',' expr (',' number)? ')'
              | 'DIFFRACT' '(' expr (',' bool)? ')'
              | 'FILTER_LP' '(' expr ',' number ')'
              | 'FILTER_HP' '(' expr ',' number ')'
              | 'FILTER_BP' '(' expr ',' number ',' number ')'
              | 'PHASE_SHIFT' '(' expr ',' number ')'
              | 'EMERGE' '(' expr (',' expr)* (',' number)? ')'
              | 'OPPOSE' '(' expr ',' expr ')'
              | 'AMPLIFY' '(' expr ',' expr (',' number)? ')'
              | 'BIND_MANY' '(' expr (',' expr)* ')'
              | ID | number | string
string      ::= '"' [^"]* '"' | "'" [^']* "'"
ID          ::= [a-zA-Z_][a-zA-Z0-9_]*
```

## Compilateur (`wave_compiler.py`)

| API | Rôle |
|---|---|
| `WaveCompiler(dim=512, pool_size=16)` | Compilateur + exécuteur |
| `compile(program) -> CompileResult` | Applique les 4 passes, expose l'AST optimisé + stats |
| `execute(program, holograms={}, memory_pool=True) -> env` | Exécute et retourne l'environnement de variables |
| `MemoryPool(dim, size=16)` | Pool de buffers (acquire/release/stats) |
| `benchmark(compiler, program, n_runs=100)` | Mesure le temps d'exécution |
| `wave_to_python(program) -> str` | Émission de code Python équivalent (aussi dans wave_code_generator) |

### Les 4 passes en détail

1. **Constant Folding** — `ENCODE "constante"` pré-calculé une fois, partagé entre toutes les
   occurrences. Compteur `folds`.
2. **Dead Code Elimination** — variables assignées jamais lues → supprimées. Compteur `dead_code`.
3. **Operator Fusion** — fusionne `BIND*` → `BIND_MANY` (3 FFT + 1 IFFT), `SUPERPOSE`, `INTERFERE`,
   `EMERGE`, `OPPOSE`, `AMPLIFY`, `FILTER` ; fusions intégrées `_fused_bind`, `_fused_unbind`,
   `_fused_bind_many`, `_fused_superpose`, `_fused_interfere`, `_fused_emerge`, `_fused_oppose`,
   `_fused_amplify`, `_fused_filter`. Compteur `fusions`.
4. **Memory Pool** — buffers pré-alloués ; mesuré : 48 % de réutilisation sur un programme de
   8 opérations.

### Benchmark de référence (attention, doc §7.2)

| Implémentation | Temps (L=256, D=1024, H=16) | Speedup |
|---|---|---|
| Expansion 4D naïve | 8 464 ms | 1x |
| Matmul cos/sin float64 | 261 ms | 32x |
| Matmul cos/sin float32 | 169 ms | 50x |

(Forward pass 125M : 101 s → 2.3 s sur CPU via `cos(φi−φj) = cos φi·cos φj + sin φi·sin φj`.)
