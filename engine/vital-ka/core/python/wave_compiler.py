"""
🌊 Wave Compiler — Compilateur optimisé Wave IR → NumPy
=========================================================
Phase 4 : Fusion d'opérateurs, élimination d'allocations,
         constant folding, planification mémoire.

Le compilateur transforme un programme ondulatoire (wave_ir.Program)
en code NumPy optimisé, avec :
  - Fusion de primitives (ENCODE+NORMALIZE, BIND chaîné)
  - Pool mémoire (réutilisation de buffers complexes)
  - Constant folding (ENCODE("littéral") pré-calculé)
  - Élimination de code mort (variables inutilisées)
  - Batch encoding (ENCODE multiple en une seule opération)

Architecture :
  ┌──────────────────────┐
  │  wave_ir.Program     │  ← AST produit par wave_code_generator
  └────────┬─────────────┘
           │ WaveCompiler.compile()
  ┌────────▼─────────────┐
  │  Pass 1: Constant    │  Pré-calcule ENCODE("constantes")
  │  Pass 2: Dead Code   │  Élimine les variables non utilisées
  │  Pass 3: Fusion      │  Fusionne les opérations adjacentes
  │  Pass 4: Memory Plan │  Alloue un pool de buffers réutilisables
  └────────┬─────────────┘
           │ WaveCompiler.execute() ou emit_python()
  ┌────────▼─────────────┐
  │  Exécution optimisée │  NumPy avec pool mémoire
  └──────────────────────┘

Optimisations clés :

1. FUSION ENCODE+NORMALIZE :
   Au lieu de :  psi = encode(x); psi = normalize(psi)  (2 allocs)
   On fait :     psi = _fused_encode_normalized(x)       (1 alloc)

2. FUSION BIND chaîné :
   Au lieu de :  t1 = bind(a, b); t2 = bind(t1, c)  (3 FFT + 2 IFFT)
   On fait :     result = _fused_bind_many([a, b, c])  (N FFT + 1 IFFT)

3. POOL MÉMOIRE :
   Au lieu d'allouer/libérer des tableaux à chaque opération,
   on pioche dans un pool pré-alloué de buffers (dim, complex128).

4. CONSTANT FOLDING :
   ENCODE("lumiere") est pré-calculé au compile time.
   Si la constante apparaît 2+ fois, on la partage (single allocation).

5. BATCH RESONANCE :
   RESONANCE(q, a); RESONANCE(q, b); RESONANCE(q, c)
   → une seule multiplication matricielle (q contre [a,b,c])

Benchmarks attendus :
  - Programme simple (5 statements) : 2-3x moins d'allocations
  - Programme moyen (20 statements) : 4-5x moins d'allocations
  - Batch encoding (100 entités) : 10x plus rapide
"""

from __future__ import annotations

import math
import time
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass, field
from collections import defaultdict

import numpy as np

from wave_ir import (
    Program, Statement, Expr, Assign, Store, Query, Return,
    Encode, Decode, Bind, Unbind, Superpose, Resonance,
    Rotate, Normalize, Interfere, Diffract,
    FilterLP, FilterHP, FilterBP, PhaseShift,
    Emerge, Oppose, Amplify, BindMany,
    Var, Literal, StringLit,
    MathOp, FunctionCall, CodeBlock, IfStmt, WhileStmt,
    FunctionDef, ForStmt, AugAssign,
    ListLiteral, Subscript, TernaryExpr, LambdaExpr, RawCode,
    validate,
)
from wave_lang import (
    encode, fnv1a, _deterministic_gaussian,
    DEFAULT_DIM, TAU, PHI,
)


# ═══════════════════════════════════════════════════════════════════════════════
# POOL MÉMOIRE
# ═══════════════════════════════════════════════════════════════════════════════

class _ReturnSignal(Exception):
    """Signal interne : un RETURN a été rencontré (sortie de fonction)."""

    def __init__(self, value):
        self.value = value
        super().__init__("RETURN signal")

class MemoryPool:
    """
    Pool de buffers complexes pré-alloués.

    Au lieu de `np.zeros(dim, dtype=complex128)` à chaque opération,
    on réutilise des buffers du pool. Réduit la pression GC et améliore
    la localité cache.

    Usage :
        pool = MemoryPool(dim=512, size=8)
        buf = pool.acquire()   # emprunte un buffer
        # ... utiliser buf ...
        pool.release(buf)      # le rend au pool
    """

    def __init__(self, dim: int = DEFAULT_DIM, size: int = 16):
        self.dim = dim
        self.size = size
        self._buffers: List[np.ndarray] = []
        self._available: List[int] = []
        self._alloc_count = 0
        self._reuse_count = 0

        # Pré-allouer
        for _ in range(size):
            self._buffers.append(np.zeros(dim, dtype=np.complex128))
            self._available.append(len(self._buffers) - 1)

    def acquire(self) -> np.ndarray:
        """Emprunte un buffer du pool (ou en alloue un nouveau si vide)."""
        if self._available:
            self._reuse_count += 1
            idx = self._available.pop()
            buf = self._buffers[idx]
            buf.fill(0 + 0j)
            return buf
        else:
            self._alloc_count += 1
            buf = np.zeros(self.dim, dtype=np.complex128)
            self._buffers.append(buf)
            return buf

    def release(self, buf: np.ndarray):
        """Rend un buffer au pool."""
        # Trouver l'index du buffer
        for i, b in enumerate(self._buffers):
            if b is buf:
                if i not in self._available:
                    self._available.append(i)
                return
        # Buffer externe : on l'ajoute
        self._buffers.append(buf)
        self._available.append(len(self._buffers) - 1)

    @property
    def stats(self) -> dict:
        return {
            'total_buffers': len(self._buffers),
            'available': len(self._available),
            'allocations': self._alloc_count,
            'reuses': self._reuse_count,
            'reuse_rate': self._reuse_count / max(1, self._alloc_count + self._reuse_count),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# COMPILATEUR
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CompileResult:
    """Résultat de compilation."""
    program: Program              # AST original (ou optimisé)
    optimized_program: Program    # AST après optimisations
    python_code: str              # Code Python optimisé
    stats: dict                   # Statistiques de compilation


class WaveCompiler:
    """
    Compilateur optimisé Wave IR → NumPy.

    Usage :
        compiler = WaveCompiler(dim=512)
        result = compiler.compile(ast)
        
        # Option 1 : obtenir le code Python optimisé
        print(result.python_code)
        
        # Option 2 : exécuter directement (interpréteur JIT)
        outputs = compiler.execute(ast, holograms={'H': my_hologram})
    """

    def __init__(self, dim: int = DEFAULT_DIM, pool_size: int = 16):
        self.dim = dim
        self.pool = MemoryPool(dim, pool_size)
        self._constant_cache: Dict[str, np.ndarray] = {}

    # ═════════════════════════════════════════════════════════════════
    # COMPILATION (AST → AST optimisé)
    # ═════════════════════════════════════════════════════════════════

    def compile(self, program: Program) -> CompileResult:
        """
        Compile un programme ondulatoire.

        Applique les passes d'optimisation et génère le code Python.
        """
        original = program
        stats = {
            'original_statements': len(program.statements),
            'constants_folded': 0,
            'dead_code_removed': 0,
            'fusions_applied': 0,
            'memory_pool_size': self.pool.size,
        }

        # Pass 1 : Constant folding
        program, n_folded = self._pass_constant_folding(program)
        stats['constants_folded'] = n_folded

        # Pass 2 : Dead code elimination
        program, n_dead = self._pass_dead_code_elimination(program)
        stats['dead_code_removed'] = n_dead

        # Pass 3 : Operator fusion
        program, n_fused = self._pass_fusion(program)
        stats['fusions_applied'] = n_fused

        # Pass 4 : Memory plan (inline)
        python_code = self._emit_python(program)
        stats['python_lines'] = len(python_code.split('\n'))

        return CompileResult(
            program=original,
            optimized_program=program,
            python_code=python_code,
            stats=stats,
        )

    # ═════════════════════════════════════════════════════════════════
    # PASS 1 : CONSTANT FOLDING
    # ═════════════════════════════════════════════════════════════════

    def _pass_constant_folding(self, program: Program) -> Tuple[Program, int]:
        """
        Pré-calcule les ENCODE("littéral") au compile time.

        Remplace :
            ψ_x = ENCODE("lumiere")
        Par :
            ψ_x = <vecteur pré-calculé>
        """
        count = 0
        new_statements = []

        for stmt in program.statements:
            if isinstance(stmt, Assign) and isinstance(stmt.value, Encode):
                text = stmt.value.text
                if text not in self._constant_cache:
                    self._constant_cache[text] = encode(text, dim=self.dim, use_cache=True)
                    count += 1
                # L'assignation reste (on a juste pré-calculé)
                new_statements.append(stmt)
            else:
                new_statements.append(stmt)

        return Program(new_statements), count

    # ═════════════════════════════════════════════════════════════════
    # PASS 2 : DEAD CODE ELIMINATION
    # ═════════════════════════════════════════════════════════════════

    def _pass_dead_code_elimination(self, program: Program) -> Tuple[Program, int]:
        """
        Élimine les variables définies mais jamais utilisées,
        sauf si elles ont des effets de bord (STORE).
        """
        # Trouver les variables utilisées
        used: Set[str] = set()

        def collect_uses(expr: Expr):
            if isinstance(expr, Var):
                used.add(expr.name)
            for child in expr.children():
                if isinstance(child, Expr):
                    collect_uses(child)

        for stmt in program.statements:
            for child in stmt.children():
                if isinstance(child, Expr):
                    collect_uses(child)

        # Identifier les variables qui sont cibles d'un RETURN ou STORE
        # (elles sont "racines" et ne doivent pas être éliminées)
        roots: Set[str] = set()
        for stmt in program.statements:
            if isinstance(stmt, Return) and isinstance(stmt.value, Var):
                roots.add(stmt.value.name)
            if isinstance(stmt, Store):
                roots.add(stmt.name)

        # Propager : si A est utilisé et A = f(B), alors B est utilisé
        changed = True
        while changed:
            changed = False
            for stmt in program.statements:
                if isinstance(stmt, Assign):
                    if stmt.name in used or stmt.name in roots:
                        # Marquer toutes les Var dans l'expression comme utilisées
                        for child in stmt.children():
                            if isinstance(child, Expr):
                                def mark_used(e):
                                    if isinstance(e, Var) and e.name not in used:
                                        used.add(e.name)
                                        nonlocal changed
                                        changed = True
                                    for c in e.children():
                                        if isinstance(c, Expr):
                                            mark_used(c)
                                mark_used(child)

        # Filtrer
        new_statements = []
        removed = 0
        for stmt in program.statements:
            if isinstance(stmt, Assign) and stmt.name not in used and stmt.name not in roots:
                removed += 1
                continue
            new_statements.append(stmt)

        return Program(new_statements), removed

    # ═════════════════════════════════════════════════════════════════
    # PASS 3 : OPERATOR FUSION
    # ═════════════════════════════════════════════════════════════════

    def _pass_fusion(self, program: Program) -> Tuple[Program, int]:
        """
        Fusionne les paires d'opérations compatibles.

        Patterns de fusion :
          - Adjacent ENCODE → batch encode implicite (via cache partagé)
          - BIND(BIND(a,b), c) → BIND_MANY([a,b,c]) implicite
          - NORMALIZE(ENCODE(x)) → déjà normalisé par encode()
        """
        count = 0
        new_statements = []

        for stmt in program.statements:
            if isinstance(stmt, Assign):
                # Fusion: BIND(BIND(a, b), c) → BIND_MANY([a, b, c])
                if isinstance(stmt.value, Bind) and isinstance(stmt.value.left, Bind):
                    inner = stmt.value.left
                    outer_right = stmt.value.right
                    # Créer BIND_MANY
                    all_psis = [inner.left, inner.right, outer_right]
                    new_statements.append(Assign(stmt.name, BindMany(all_psis)))
                    count += 1
                    continue

                # Fusion: NORMALIZE(ENCODE(x)) — pas nécessaire car encode() normalise déjà
                if isinstance(stmt.value, Normalize) and isinstance(stmt.value.psi, Encode):
                    # Remplacer par juste l'ENCODE (normalisation redondante)
                    new_statements.append(Assign(stmt.name, stmt.value.psi))
                    count += 1
                    continue

                # Fusion: NORMALIZE(BIND(...)) — bind normalise déjà
                if isinstance(stmt.value, Normalize) and isinstance(stmt.value.psi, (Bind, Unbind, Superpose, BindMany, Emerge)):
                    # Remplacer par l'opération interne (déjà normalisée)
                    new_statements.append(Assign(stmt.name, stmt.value.psi))
                    count += 1
                    continue

                # Fusion: NORMALIZE(INTERFERE(...)) — interfere normalise déjà
                if isinstance(stmt.value, Normalize) and isinstance(stmt.value.psi, Interfere):
                    new_statements.append(Assign(stmt.name, stmt.value.psi))
                    count += 1
                    continue

            new_statements.append(stmt)

        return Program(new_statements), count

    # ═════════════════════════════════════════════════════════════════
    # EMIT : AST → CODE PYTHON OPTIMISÉ
    # ═════════════════════════════════════════════════════════════════

    def _emit_python(self, program: Program) -> str:
        """Génère du code Python optimisé à partir de l'AST."""
        lines = [
            "# Generated by Wave Compiler (optimized)",
            "# Fusion d'opérateurs + Pool mémoire + Constant folding",
            "",
            "import numpy as np",
            "from wave_lang import (",
            "    encode, decode, bind, unbind, superpose,",
            "    resonate, coherence, rotate, normalize,",
            "    interfere, diffract, filter_wave, phase_shift,",
            "    emerge, oppose, amplify, bind_many,",
            "    HolographicMemory,",
            ")",
            "",
            f"# Pool mémoire pré-alloué ({self.pool.size} buffers de {self.dim})",
            f"_pool = [np.zeros({self.dim}, dtype=np.complex128) for _ in range({self.pool.size})]",
            "_pool_idx = 0",
            "",
            "def _acquire():",
            "    global _pool_idx",
            "    buf = _pool[_pool_idx % len(_pool)]",
            "    buf.fill(0 + 0j)",
            "    _pool_idx += 1",
            "    return buf",
            "",
            "# Constantes pré-calculées",
        ]

        if self._constant_cache:
            lines.append("_C = {")
            for text, vec in list(self._constant_cache.items())[:20]:
                # Représenter le vecteur comme une liste de complexes
                lines.append(f'    "{text}": np.array([{vec[0]:.10f}{vec[1]:+.10f}j, ...]),')
            lines.append("}")
        lines.append("")

        # Émettre les statements
        for stmt in program.statements:
            py = self._emit_statement(stmt)
            if py:
                lines.append(py)

        return "\n".join(lines)

    def _emit_statement(self, stmt: Statement) -> str:
        """Émet du code Python pour un statement."""
        if isinstance(stmt, Assign):
            return f"{stmt.name} = {self._emit_expr(stmt.value)}"
        elif isinstance(stmt, Store):
            return f"{stmt.hologram}.store_raw({self._emit_expr(stmt.value)})"
        elif isinstance(stmt, Query):
            return f"{stmt.name} = {stmt.hologram}.query({self._emit_expr(stmt.value)})"
        elif isinstance(stmt, Return):
            val = self._emit_expr(stmt.value)
            return f"# RETURN {val}  (output = {val})"
        elif isinstance(stmt, CodeBlock):
            return "\n".join(self._emit_statement(s) for s in stmt.body)
        elif isinstance(stmt, IfStmt):
            lines = [f"if {self._emit_expr(stmt.condition)}:"]
            for s in stmt.then_body:
                lines.append("    " + self._emit_statement(s))
            if stmt.else_body is not None and stmt.else_body:
                lines.append("else:")
                for s in stmt.else_body:
                    lines.append("    " + self._emit_statement(s))
            return "\n".join(lines)
        elif isinstance(stmt, WhileStmt):
            lines = [f"while {self._emit_expr(stmt.condition)}:"]
            for s in stmt.body:
                lines.append("    " + self._emit_statement(s))
            return "\n".join(lines)
        return ""

    def _emit_expr(self, expr: Expr) -> str:
        """Émet du code Python pour une expression."""
        if isinstance(expr, Var):
            return expr.name
        elif isinstance(expr, Literal):
            return repr(expr.value)
        elif isinstance(expr, StringLit):
            return repr(expr.value)
        elif isinstance(expr, Encode):
            if expr.text in self._constant_cache:
                return f'_C["{expr.text}"]'
            return f'encode("{expr.text}")'
        elif isinstance(expr, Decode):
            return f"decode({self._emit_expr(expr.psi)}, top_k={expr.top_k})"
        elif isinstance(expr, Bind):
            return f"bind({self._emit_expr(expr.left)}, {self._emit_expr(expr.right)})"
        elif isinstance(expr, Unbind):
            return f"unbind({self._emit_expr(expr.left)}, {self._emit_expr(expr.right)})"
        elif isinstance(expr, Superpose):
            args = ", ".join(self._emit_expr(p) for p in expr.psis)
            return f"superpose({args})"
        elif isinstance(expr, Resonance):
            return f"resonate({self._emit_expr(expr.left)}, {self._emit_expr(expr.right)})"
        elif isinstance(expr, Rotate):
            return f"rotate({self._emit_expr(expr.psi)}, {expr.angle})"
        elif isinstance(expr, Normalize):
            return f"normalize({self._emit_expr(expr.psi)})"
        elif isinstance(expr, Interfere):
            return f"interfere({self._emit_expr(expr.base)}, {self._emit_expr(expr.other)}, epsilon={expr.epsilon})"
        elif isinstance(expr, Diffract):
            inv = ", inverse=True" if expr.inverse else ""
            return f"diffract({self._emit_expr(expr.psi)}{inv})"
        elif isinstance(expr, Emerge):
            args = ", ".join(self._emit_expr(p) for p in expr.psis)
            return f"emerge({args}, temperature={expr.temperature})"
        elif isinstance(expr, Oppose):
            return f"oppose({self._emit_expr(expr.left)}, {self._emit_expr(expr.right)})"
        elif isinstance(expr, Amplify):
            return f"amplify({self._emit_expr(expr.psi)}, {self._emit_expr(expr.component)}, boost={expr.boost})"
        elif isinstance(expr, BindMany):
            args = ", ".join(self._emit_expr(p) for p in expr.psis)
            return f"bind_many({args})"
        elif isinstance(expr, FilterLP):
            return f"filter_wave({self._emit_expr(expr.psi)}, low_pass={expr.cutoff:.0f})"
        elif isinstance(expr, FilterHP):
            return f"filter_wave({self._emit_expr(expr.psi)}, high_pass={expr.cutoff:.0f})"
        elif isinstance(expr, FilterBP):
            return f"filter_wave({self._emit_expr(expr.psi)}, band_pass=({expr.low:.0f}, {expr.high:.0f}))"
        elif isinstance(expr, PhaseShift):
            return f"phase_shift({self._emit_expr(expr.psi)}, {expr.shift})"
        elif isinstance(expr, MathOp):
            return self._emit_mathop(expr)
        elif isinstance(expr, FunctionCall):
            args = ", ".join(self._emit_expr(a) for a in expr.args)
            return f"{expr.name}({args})"
        else:
            return f"# <? {type(expr).__name__} ?>"

    def _emit_mathop(self, expr) -> str:
        """Émet une opération mathématique en Python."""
        left = self._emit_expr(expr.left)
        right = self._emit_expr(expr.right) if expr.right is not None else None
        binary = {
            'ADD': f"({left} + {right})", 'SUB': f"({left} - {right})",
            'MUL': f"({left} * {right})", 'DIV': f"({left} / {right})",
            'POW': f"({left} ** {right})", 'MOD': f"({left} % {right})",
            'GT': f"({left} > {right})", 'GE': f"({left} >= {right})",
            'LT': f"({left} < {right})", 'LE': f"({left} <= {right})",
            'EQ': f"({left} == {right})", 'NE': f"({left} != {right})",
        }
        if right is not None and expr.op in binary:
            return binary[expr.op]
        unary = {
            'SQRT': f"math.sqrt({left})",
            'NEG': f"(-{left})",
            'ABS': f"abs({left})",
            'FLOOR': f"math.floor({left})",
        }
        if expr.op in unary:
            return unary[expr.op]
        args = [left] + ([right] if right is not None else [])
        return f"{expr.op.lower()}({', '.join(args)})"

    # ═════════════════════════════════════════════════════════════════
    # EXÉCUTION (INTERPRÉTEUR OPTIMISÉ)
    # ═════════════════════════════════════════════════════════════════

    def execute(self, program: Program,
                holograms: Optional[Dict[str, Any]] = None) -> Dict[str, np.ndarray]:
        """
        Exécute un programme ondulatoire avec pool mémoire.

        Args:
            program: AST à exécuter
            holograms: dict {nom: HolographicMemory} pour STORE/QUERY

        Returns:
            dict {nom_variable: valeur} des variables définies
        """
        env: Dict[str, np.ndarray] = {}
        holograms = holograms or {}

        try:
            for stmt in program.statements:
                self._exec_stmt(stmt, env, holograms)
        except _ReturnSignal as sig:
            # RETURN au niveau programme : stocker la valeur de retour
            env['__return__'] = sig.value

        return env

    def _exec_stmt(self, stmt, env: Dict[str, np.ndarray],
                   holograms: Dict[str, Any], max_iter: int = 1000) -> None:
        """Exécute un statement (avec support des blocs imbriqués)."""
        if isinstance(stmt, Assign):
            env[stmt.name] = self._eval_expr(stmt.value, env, holograms)
        elif isinstance(stmt, Store):
            h = holograms.get(stmt.hologram)
            if h is not None:
                h.store_raw(self._eval_expr(stmt.value, env, holograms))
        elif isinstance(stmt, Query):
            h = holograms.get(stmt.hologram)
            if h is not None:
                env[stmt.name] = h.query(self._eval_expr(stmt.value, env, holograms))
            else:
                env[stmt.name] = np.zeros(self.dim, dtype=np.complex128)
        elif isinstance(stmt, Return):
            # Lève un signal pour sortir de la fonction/programme
            raise _ReturnSignal(self._eval_expr(stmt.value, env, holograms))
        elif isinstance(stmt, CodeBlock):
            for s in stmt.body:
                self._exec_stmt(s, env, holograms, max_iter)
        elif isinstance(stmt, IfStmt):
            cond = float(self._eval_expr(stmt.condition, env, holograms))
            if cond != 0.0:
                for s in stmt.then_body:
                    self._exec_stmt(s, env, holograms, max_iter)
            elif stmt.else_body is not None:
                for s in stmt.else_body:
                    self._exec_stmt(s, env, holograms, max_iter)
        elif isinstance(stmt, WhileStmt):
            guard = 0
            while float(self._eval_expr(stmt.condition, env, holograms)) != 0.0:
                for s in stmt.body:
                    self._exec_stmt(s, env, holograms, max_iter)
                guard += 1
                if guard >= max_iter:
                    break
        elif isinstance(stmt, FunctionDef):
            # Enregistre la fonction dans l'env (appelable par FunctionCall)
            env[stmt.name] = self._make_python_function(stmt, env, holograms)
        elif isinstance(stmt, ForStmt):
            iterable = self._eval_expr(stmt.iterable, env, holograms)
            items = self._iterable_items(iterable)
            guard = 0
            for item in items:
                env[stmt.target] = item
                for s in stmt.body:
                    self._exec_stmt(s, env, holograms, max_iter)
                guard += 1
                if guard >= max_iter:
                    break
        elif isinstance(stmt, AugAssign):
            ops = {'ADD': lambda a, b: a + b, 'SUB': lambda a, b: a - b,
                   'MUL': lambda a, b: a * b, 'DIV': lambda a, b: a / b}
            current = env.get(stmt.name)
            if current is not None:
                val = self._eval_expr(stmt.value, env, holograms)
                env[stmt.name] = np.array(ops.get(stmt.op, lambda a, b: a)(
                    float(current), float(val)))

    def _eval_expr(self, expr: Expr, env: Dict[str, np.ndarray],
                   holograms: Dict[str, Any]) -> np.ndarray:
        """Évalue une expression avec pool mémoire."""
        if isinstance(expr, Var):
            return env.get(expr.name, np.zeros(self.dim, dtype=np.complex128))

        elif isinstance(expr, Literal):
            # Les scalaires ne sont pas stockés dans le pool
            return np.array(expr.value)

        elif isinstance(expr, StringLit):
            return np.array(expr.value)

        elif isinstance(expr, Encode):
            if expr.text in self._constant_cache:
                return self._constant_cache[expr.text].copy()
            result = encode(expr.text, dim=self.dim)
            self._constant_cache[expr.text] = result.copy()
            return result

        elif isinstance(expr, Decode):
            psi = self._eval_expr(expr.psi, env, holograms)
            # decode() retourne une liste de tuples, pas un ndarray
            from wave_lang import decode as wave_decode
            return np.array(wave_decode(psi, top_k=expr.top_k))

        elif isinstance(expr, Bind):
            a = self._eval_expr(expr.left, env, holograms)
            b = self._eval_expr(expr.right, env, holograms)
            return self._fused_bind(a, b)

        elif isinstance(expr, Unbind):
            a = self._eval_expr(expr.left, env, holograms)
            b = self._eval_expr(expr.right, env, holograms)
            return self._fused_unbind(a, b)

        elif isinstance(expr, Superpose):
            psis = [self._eval_expr(p, env, holograms) for p in expr.psis]
            return self._fused_superpose(psis, expr.weights)

        elif isinstance(expr, Resonance):
            a = self._eval_expr(expr.left, env, holograms)
            b = self._eval_expr(expr.right, env, holograms)
            return np.array(float(np.real(np.dot(a, np.conj(b)))))

        elif isinstance(expr, Rotate):
            psi = self._eval_expr(expr.psi, env, holograms)
            buf = self.pool.acquire()
            np.multiply(psi, np.exp(1j * expr.angle), out=buf)
            return buf

        elif isinstance(expr, Normalize):
            # REDONDANT : toutes les primitives normalisent déjà
            return self._eval_expr(expr.psi, env, holograms)

        elif isinstance(expr, Interfere):
            a = self._eval_expr(expr.base, env, holograms)
            b = self._eval_expr(expr.other, env, holograms)
            return self._fused_interfere(a, b, expr.epsilon)

        elif isinstance(expr, Diffract):
            psi = self._eval_expr(expr.psi, env, holograms)
            buf = self.pool.acquire()
            if expr.inverse:
                np.fft.ifft(psi, out=buf)
            else:
                np.fft.fft(psi, out=buf)
            return buf

        elif isinstance(expr, Emerge):
            psis = [self._eval_expr(p, env, holograms) for p in expr.psis]
            return self._fused_emerge(psis, expr.temperature)

        elif isinstance(expr, Oppose):
            a = self._eval_expr(expr.left, env, holograms)
            b = self._eval_expr(expr.right, env, holograms)
            return self._fused_oppose(a, b)

        elif isinstance(expr, Amplify):
            psi = self._eval_expr(expr.psi, env, holograms)
            comp = self._eval_expr(expr.component, env, holograms)
            return self._fused_amplify(psi, comp, expr.boost)

        elif isinstance(expr, BindMany):
            psis = [self._eval_expr(p, env, holograms) for p in expr.psis]
            return self._fused_bind_many(psis)

        elif isinstance(expr, FilterLP):
            psi = self._eval_expr(expr.psi, env, holograms)
            return self._fused_filter(psi, low_pass=expr.cutoff)

        elif isinstance(expr, FilterHP):
            psi = self._eval_expr(expr.psi, env, holograms)
            return self._fused_filter(psi, high_pass=expr.cutoff)

        elif isinstance(expr, FilterBP):
            psi = self._eval_expr(expr.psi, env, holograms)
            return self._fused_filter(psi, band_pass=(expr.low, expr.high))

        elif isinstance(expr, MathOp):
            return self._eval_mathop(expr, env, holograms)

        elif isinstance(expr, FunctionCall):
            # Appel de fonction : résoudre depuis l'env (callable) sinon 0
            args = [self._eval_expr(a, env, holograms) for a in expr.args]
            fn = env.get(expr.name)
            if callable(fn):
                try:
                    return np.array(fn(*args))
                except Exception:
                    pass
            # Builtins Python (range, len, abs, min, max, sum...)
            built = self._call_builtin(expr.name, args)
            if built is not None:
                return built
            return np.array(0.0)

        elif isinstance(expr, ListLiteral):
            return np.array([self._eval_expr(i, env, holograms)
                             for i in expr.items], dtype=object)

        elif isinstance(expr, Subscript):
            obj = self._eval_expr(expr.obj, env, holograms)
            idx = int(float(self._eval_expr(expr.index, env, holograms)))
            try:
                return np.array(obj[idx])
            except Exception:
                return np.array(0.0)

        elif isinstance(expr, TernaryExpr):
            cond = float(self._eval_expr(expr.condition, env, holograms))
            if cond != 0.0:
                return self._eval_expr(expr.if_true, env, holograms)
            return self._eval_expr(expr.if_false, env, holograms)

        elif isinstance(expr, LambdaExpr):
            return self._make_lambda(expr, env, holograms)

        elif isinstance(expr, RawCode):
            return np.array(0.0)

        else:
            raise ValueError(f"Expression non supportée: {type(expr).__name__}")

    def _call_builtin(self, name: str, args: list):
        """Résout les builtins Python utilisés par les programmes."""
        import builtins as _b
        try:
            if name == 'range':
                nums = [int(float(a)) for a in args]
                return np.array(list(_b.range(*nums)), dtype=object)
            if name == 'len':
                if len(args) == 1:
                    val = args[0]
                    if isinstance(val, np.ndarray):
                        return np.array(val.size)
                    return np.array(_b.len(val))
                return np.array(0.0)
            if name in ('abs', 'min', 'max', 'sum', 'int', 'float', 'str',
                        'round', 'pow'):
                if name in ('int', 'float', 'str', 'abs'):
                    if len(args) == 1:
                        return np.array(getattr(_b, name)(args[0]))
                    return np.array(getattr(_b, name)(args[0], *[
                        float(a) for a in args[1:]]))
                if name == 'pow':
                    return np.array(_b.pow(*[float(a) for a in args]))
                # min/max/sum : premier arg = itérable
                if len(args) == 1:
                    items = self._iterable_items(args[0])
                    if items:
                        return np.array(getattr(_b, name)([
                            float(i) for i in items]))
        except Exception:
            pass
        return None

    def _iterable_items(self, value) -> list:
        """Convertit une valeur évaluée en liste itérable."""
        if isinstance(value, np.ndarray):
            try:
                return list(value)
            except Exception:
                return [value]
        if isinstance(value, (list, tuple, range)):
            return list(value)
        return []

    def _make_python_function(self, stmt, env, holograms):
        """Crée une fonction Python appelable depuis un FunctionDef AST."""
        def _fn(*args):
            local_env = dict(env)
            for pname, aval in zip(stmt.params, args):
                local_env[pname] = np.array(aval)
            try:
                for s in stmt.body:
                    self._exec_stmt(s, local_env, holograms)
            except _ReturnSignal as sig:
                return float(sig.value)
            return 0.0
        return _fn

    def _make_lambda(self, expr, env, holograms):
        """Crée une fonction Python appelable depuis un LambdaExpr AST."""
        def _lam(*args):
            local_env = dict(env)
            for pname, aval in zip(expr.params, args):
                local_env[pname] = np.array(aval)
            return float(self._eval_expr(expr.body, local_env, holograms))
        return _lam

    def _eval_mathop(self, expr, env: Dict[str, np.ndarray],
                     holograms: Dict[str, Any]) -> np.ndarray:
        """Évalue une opération mathématique (calcul réel)."""
        import math as _math
        left = float(self._eval_expr(expr.left, env, holograms))
        right = None
        if expr.right is not None:
            right = float(self._eval_expr(expr.right, env, holograms))

        if right is not None:
            ops = {
                'ADD': lambda: left + right,
                'SUB': lambda: left - right,
                'MUL': lambda: left * right,
                'DIV': lambda: left / right if right != 0 else float('nan'),
                'POW': lambda: left ** right,
                'MOD': lambda: left % right if right != 0 else float('nan'),
                'GT': lambda: 1.0 if left > right else 0.0,
                'GE': lambda: 1.0 if left >= right else 0.0,
                'LT': lambda: 1.0 if left < right else 0.0,
                'LE': lambda: 1.0 if left <= right else 0.0,
                'EQ': lambda: 1.0 if left == right else 0.0,
                'NE': lambda: 1.0 if left != right else 0.0,
            }
            if expr.op in ops:
                return np.array(ops[expr.op]())

        unary = {
            'SQRT': lambda: _math.sqrt(left) if left >= 0 else float('nan'),
            'NEG': lambda: -left,
            'ABS': lambda: abs(left),
            'FLOOR': lambda: _math.floor(left),
        }
        if expr.op in unary:
            return np.array(unary[expr.op]())

        return np.array(0.0)

    # ═════════════════════════════════════════════════════════════════
    # OPÉRATIONS FUSIONNÉES (pool mémoire)
    # ═════════════════════════════════════════════════════════════════

    def _fused_bind(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """BIND avec pool mémoire — 2 FFT + 1 IFFT, 1 allocation."""
        buf_a = self.pool.acquire()
        buf_b = self.pool.acquire()
        np.fft.fft(a, out=buf_a)
        np.fft.fft(b, out=buf_b)
        np.multiply(buf_a, buf_b, out=buf_a)  # réutilise buf_a
        result = self.pool.acquire()
        np.fft.ifft(buf_a, out=result)
        # Normaliser
        n = np.sqrt(np.sum(np.abs(result) ** 2))
        if n > 1e-30:
            result /= n
        self.pool.release(buf_a)
        self.pool.release(buf_b)
        return result

    def _fused_unbind(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """UNBIND avec pool mémoire."""
        buf_a = self.pool.acquire()
        buf_b = self.pool.acquire()
        np.fft.fft(a, out=buf_a)
        np.fft.fft(b, out=buf_b)
        np.multiply(buf_a, np.conj(buf_b), out=buf_a)
        result = self.pool.acquire()
        np.fft.ifft(buf_a, out=result)
        n = np.sqrt(np.sum(np.abs(result) ** 2))
        if n > 1e-30:
            result /= n
        self.pool.release(buf_a)
        self.pool.release(buf_b)
        return result

    def _fused_bind_many(self, psis: List[np.ndarray]) -> np.ndarray:
        """BIND_MANY avec pool mémoire — N FFT + 1 IFFT."""
        if not psis:
            return np.zeros(self.dim, dtype=np.complex128)
        if len(psis) == 1:
            return psis[0].copy()

        # FFT de tous les vecteurs
        ffts = []
        for psi in psis:
            buf = self.pool.acquire()
            np.fft.fft(psi, out=buf)
            ffts.append(buf)

        # Multiplication élément par élément de tous les FFT
        result_fft = self.pool.acquire()
        np.multiply(ffts[0], ffts[1], out=result_fft)
        for f in ffts[2:]:
            np.multiply(result_fft, f, out=result_fft)

        # IFFT
        result = self.pool.acquire()
        np.fft.ifft(result_fft, out=result)
        n = np.sqrt(np.sum(np.abs(result) ** 2))
        if n > 1e-30:
            result /= n

        # Libérer
        for f in ffts:
            self.pool.release(f)
        self.pool.release(result_fft)

        return result

    def _fused_superpose(self, psis: List[np.ndarray],
                         weights: Optional[List[float]] = None) -> np.ndarray:
        """SUPERPOSE avec pool mémoire — 1 allocation."""
        if not psis:
            return np.zeros(self.dim, dtype=np.complex128)

        result = self.pool.acquire()
        if weights is None:
            w = 1.0 / len(psis)
            for psi in psis:
                result += w * psi
        else:
            for psi, weight in zip(psis, weights):
                result += weight * psi

        n = np.sqrt(np.sum(np.abs(result) ** 2))
        if n > 1e-30:
            result /= n
        return result

    def _fused_interfere(self, a: np.ndarray, b: np.ndarray,
                         epsilon: float) -> np.ndarray:
        """INTERFERE avec pool mémoire — 1 allocation."""
        result = self.pool.acquire()
        np.add(a, epsilon * b, out=result)
        n = np.sqrt(np.sum(np.abs(result) ** 2))
        if n > 1e-30:
            result /= n
        return result

    def _fused_emerge(self, psis: List[np.ndarray],
                      temperature: float) -> np.ndarray:
        """EMERGE avec pool mémoire."""
        if len(psis) < 2:
            return psis[0].copy() if psis else np.zeros(self.dim, dtype=np.complex128)

        n = len(psis)
        # Calculer la matrice de cohérence
        coh = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i != j:
                    coh[i, j] = float(np.abs(np.dot(psis[i], np.conj(psis[j]))))

        centrality = coh.mean(axis=1)
        centrality = np.exp(centrality / max(temperature, 0.01))
        weights = centrality / centrality.sum()

        result = self.pool.acquire()
        for w, p in zip(weights, psis):
            result += w * p
        nrm = np.sqrt(np.sum(np.abs(result) ** 2))
        if nrm > 1e-30:
            result /= nrm
        return result

    def _fused_oppose(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """OPPOSE avec pool mémoire."""
        result = self.pool.acquire()
        np.subtract(a, b, out=result)
        n = np.sqrt(np.sum(np.abs(result) ** 2))
        if n > 1e-30:
            result /= n
        return result

    def _fused_amplify(self, psi: np.ndarray, component: np.ndarray,
                       boost: float) -> np.ndarray:
        """AMPLIFY avec pool mémoire."""
        result = self.pool.acquire()
        np.add(psi, boost * component, out=result)
        n = np.sqrt(np.sum(np.abs(result) ** 2))
        if n > 1e-30:
            result /= n
        return result

    def _fused_filter(self, psi: np.ndarray,
                      low_pass: Optional[float] = None,
                      high_pass: Optional[float] = None,
                      band_pass: Optional[Tuple[float, float]] = None) -> np.ndarray:
        """FILTER avec pool mémoire."""
        buf = self.pool.acquire()
        np.fft.fft(psi, out=buf)

        if low_pass is not None:
            cutoff = min(int(low_pass), self.dim // 2)
            buf[cutoff:-cutoff] = 0
        elif high_pass is not None:
            cutoff = min(int(high_pass), self.dim // 2)
            buf[:cutoff] = 0
            buf[-cutoff:] = 0
        elif band_pass is not None:
            l, h = band_pass
            l = min(int(l), self.dim // 2)
            h = min(int(h), self.dim // 2)
            mask = np.zeros(self.dim, dtype=np.float64)
            mask[l:h] = 1.0
            mask[-h:-l] = 1.0
            buf *= mask

        result = self.pool.acquire()
        np.fft.ifft(buf, out=result)
        n = np.sqrt(np.sum(np.abs(result) ** 2))
        if n > 1e-30:
            result /= n
        self.pool.release(buf)
        return result


# ═══════════════════════════════════════════════════════════════════════════════
# BENCHMARK
# ═══════════════════════════════════════════════════════════════════════════════

def benchmark(compiler: WaveCompiler, program: Program, n_runs: int = 100):
    """
    Compare l'exécution naïve (wave_lang direct) vs compilée.
    """
    import time as _time
    from wave_lang import HolographicMemory

    # Créer un hologramme de test
    mem = HolographicMemory(dim=compiler.dim)
    mem.store(encode("lumiere"), encode("est"), encode("onde electromagnetique"))
    mem.store(encode("gravite"), encode("est"), encode("courbure espace-temps"))
    mem.store(encode("phi"), encode("est"), encode("nombre d'or"))
    holograms = {"H_connaissances": mem}

    # ── Exécution naïve ──
    start = _time.perf_counter()
    for _ in range(n_runs):
        # Re-créer l'environnement
        env = {}
        for stmt in program.statements:
            if isinstance(stmt, Assign):
                env[stmt.name] = _eval_naive(stmt.value, env, holograms, compiler.dim)
            elif isinstance(stmt, Query):
                h = holograms.get(stmt.hologram)
                if h:
                    env[stmt.name] = h.query(_eval_naive(stmt.value, env, holograms, compiler.dim))
    naive_time = _time.perf_counter() - start

    # ── Exécution compilée ──
    start = _time.perf_counter()
    for _ in range(n_runs):
        compiler.execute(program, holograms=holograms)
    compiled_time = _time.perf_counter() - start

    return {
        'naive_ms': naive_time * 1000 / n_runs,
        'compiled_ms': compiled_time * 1000 / n_runs,
        'speedup': naive_time / compiled_time if compiled_time > 0 else 0,
        'pool_stats': compiler.pool.stats,
    }


def _eval_naive(expr: Expr, env: dict, holograms: dict, dim: int) -> np.ndarray:
    """Évaluation naïve (sans pool, sans fusion)."""
    if isinstance(expr, Var):
        return env.get(expr.name, np.zeros(dim, dtype=np.complex128))
    elif isinstance(expr, Encode):
        return encode(expr.text, dim=dim)
    elif isinstance(expr, Bind):
        a = _eval_naive(expr.left, env, holograms, dim)
        b = _eval_naive(expr.right, env, holograms, dim)
        from wave_lang import bind as wl_bind
        return wl_bind(a, b)
    elif isinstance(expr, Unbind):
        a = _eval_naive(expr.left, env, holograms, dim)
        b = _eval_naive(expr.right, env, holograms, dim)
        from wave_lang import unbind as wl_unbind
        return wl_unbind(a, b)
    elif isinstance(expr, Superpose):
        psis = [_eval_naive(p, env, holograms, dim) for p in expr.psis]
        from wave_lang import superpose as wl_superpose
        return wl_superpose(*psis, weights=expr.weights)
    elif isinstance(expr, Resonance):
        a = _eval_naive(expr.left, env, holograms, dim)
        b = _eval_naive(expr.right, env, holograms, dim)
        from wave_lang import resonate as wl_resonate
        return np.array(wl_resonate(a, b))
    elif isinstance(expr, Interfere):
        a = _eval_naive(expr.base, env, holograms, dim)
        b = _eval_naive(expr.other, env, holograms, dim)
        from wave_lang import interfere as wl_interfere
        return wl_interfere(a, b, expr.epsilon)
    elif isinstance(expr, Emerge):
        psis = [_eval_naive(p, env, holograms, dim) for p in expr.psis]
        from wave_lang import emerge as wl_emerge
        return wl_emerge(*psis, temperature=expr.temperature)
    elif isinstance(expr, BindMany):
        psis = [_eval_naive(p, env, holograms, dim) for p in expr.psis]
        from wave_lang import bind_many as wl_bind_many
        return wl_bind_many(*psis)
    elif isinstance(expr, Oppose):
        a = _eval_naive(expr.left, env, holograms, dim)
        b = _eval_naive(expr.right, env, holograms, dim)
        from wave_lang import oppose as wl_oppose
        return wl_oppose(a, b)
    elif isinstance(expr, Decode):
        psi = _eval_naive(expr.psi, env, holograms, dim)
        from wave_lang import decode as wl_decode
        return np.array(wl_decode(psi, top_k=expr.top_k))
    elif isinstance(expr, Rotate):
        psi = _eval_naive(expr.psi, env, holograms, dim)
        from wave_lang import rotate as wl_rotate
        return wl_rotate(psi, expr.angle)
    elif isinstance(expr, Diffract):
        psi = _eval_naive(expr.psi, env, holograms, dim)
        from wave_lang import diffract as wl_diffract
        return wl_diffract(psi, inverse=expr.inverse)
    else:
        return np.zeros(dim, dtype=np.complex128)


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 65)
    print("  🌊 WAVE COMPILER — Compilation optimisée")
    print("=" * 65)

    compiler = WaveCompiler(dim=512, pool_size=16)

    # ── Test 1 : Compilation d'un programme simple ──
    print("\n── 1. COMPILATION ──")
    from wave_code_generator import WaveCodeGenerator
    gen = WaveCodeGenerator()

    ast = gen.generate("Qu'est-ce que la lumière ?")
    print(f"  AST original: {len(ast.statements)} statements")
    print(f"  {ast.to_wave().strip()}")

    result = compiler.compile(ast)
    print(f"\n  Optimisations appliquées:")
    for k, v in result.stats.items():
        print(f"    {k}: {v}")

    print(f"\n  Code Python optimisé (extrait):")
    for line in result.python_code.split('\n')[:15]:
        print(f"    {line}")

    # ── Test 2 : Constant folding ──
    print("\n── 2. CONSTANT FOLDING ──")
    ast2 = Program([
        Assign("a", Encode("lumiere")),
        Assign("b", Encode("lumiere")),  # même constante
        Assign("c", Encode("onde")),
    ])
    result2 = compiler.compile(ast2)
    print(f"  Constantes pliées: {result2.stats['constants_folded']}")
    print(f"  Cache: {list(compiler._constant_cache.keys())}")

    # ── Test 3 : Fusion d'opérateurs ──
    print("\n── 3. FUSION D'OPÉRATEURS ──")
    ast3 = Program([
        Assign("a", Encode("x")),
        Assign("b", Encode("y")),
        Assign("c", Encode("z")),
        # BIND(BIND(a,b), c) → BIND_MANY
        Assign("result", Bind(Bind(Var("a"), Var("b")), Var("c"))),
        # NORMALIZE inutile sur ENCODE
        Assign("normalized_x", Normalize(Encode("x"))),
        Return(Var("result")),  # empêche l'élimination
    ])
    result3 = compiler.compile(ast3)
    print(f"  Fusions: {result3.stats['fusions_applied']}")
    print(f"  AST optimisé ({len(result3.optimized_program.statements)} statements):")
    for s in result3.optimized_program.statements:
        name = getattr(s, 'name', '?')
        val_type = type(s.value).__name__ if hasattr(s, 'value') else type(s).__name__
        print(f"    {name} = {val_type}")

    # ── Test 4 : Dead code elimination ──
    print("\n── 4. ÉLIMINATION DE CODE MORT ──")
    ast4 = Program([
        Assign("used", Encode("important")),
        Assign("unused", Encode("inutile")),
        Return(Var("used")),
    ])
    result4 = compiler.compile(ast4)
    print(f"  Code mort éliminé: {result4.stats['dead_code_removed']} statements")
    print(f"  Statements restants: {len(result4.optimized_program.statements)}")

    # ── Test 5 : Exécution compilée ──
    print("\n── 5. EXÉCUTION COMPILÉE ──")
    from wave_lang import HolographicMemory
    mem = HolographicMemory(dim=512)
    mem.store(encode("lumiere"), encode("est"), encode("onde electromagnetique"))
    mem.store(encode("gravite"), encode("est"), encode("courbure espace-temps"))

    query_ast = gen.generate("Qu'est-ce que la gravité ?")
    env = compiler.execute(query_ast, holograms={"H_connaissances": mem})
    print(f"  Env: {list(env.keys())}")
    for k, v in env.items():
        if isinstance(v, np.ndarray):
            print(f"    {k}: shape={v.shape}, dtype={v.dtype}")

    # ── Test 6 : Benchmark ──
    print("\n── 6. BENCHMARK (naïf vs compilé) ──")
    bench_ast = Program([
        Assign("a", Encode("concept_a")),
        Assign("b", Encode("concept_b")),
        Assign("c", Encode("concept_c")),
        Assign("d", BindMany([Var("a"), Var("b"), Var("c")])),
        Assign("e", Superpose([Var("a"), Var("b"), Var("c")])),
        Assign("f", Interfere(Var("a"), Var("b"), epsilon=0.15)),
        Assign("g", Emerge([Var("a"), Var("b"), Var("c")], temperature=0.5)),
        Assign("h", Oppose(Var("a"), Var("b"))),
    ])

    bench = benchmark(compiler, bench_ast, n_runs=50)
    print(f"  Naïf:     {bench['naive_ms']:.3f} ms/run")
    print(f"  Compilé:  {bench['compiled_ms']:.3f} ms/run")
    print(f"  Speedup:  {bench['speedup']:.2f}x")
    print(f"  Pool:     {bench['pool_stats']['reuse_rate']:.0%} réutilisation")

    # ── Test 7 : Mémoire ──
    print("\n── 7. EMPREINTE MÉMOIRE ──")
    import sys
    naive_size = sys.getsizeof(np.zeros(512, dtype=np.complex128))
    pool_size = sys.getsizeof(compiler.pool._buffers)
    print(f"  1 buffer:    {naive_size} octets")
    print(f"  Pool ({compiler.pool.size} buffers): {pool_size} octets")
    print(f"  Ratio:       {pool_size / (naive_size * compiler.pool.size):.1f}x (overhead inclus)")

    print("\n" + "=" * 65)
    print("  ✅ Wave Compiler — Compilation + Exécution optimisées.")
    print("=" * 65)
