"""
🌊 Wave Response — Fluidité conversationnelle par intention
=============================================================

Le pipeline produisait des réponses brutes (« 14.0 »). Ce module
transforme les résultats en phrases françaises complètes, selon
l'intention détectée :

| Intention | Réponse exemple |
|-----------|-----------------|
| math      | « 2 + 3 × 4 = 14. » |
| code      | « Voici la fonction factorial(n) : [code]. » |
| reason    | « J'en déduis : [conclusion]. » |
| query     | « Voici ce que je trouve : ... » |
| store_fact| « Fait mémorisé : ... » |
| sample    | « Proposition : ... » |
| evaluate  | « Score de cohérence : 0.72. » |

Le module est branché dans wave_pipeline._synthesize (étape 6).
"""

from __future__ import annotations

from typing import Dict, Any, Optional

from wave_ir import (Program, Assign, MathOp, Literal, Var, FunctionDef,
                     Return, FunctionCall)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _fmt_number(v) -> str:
    """Formate un nombre : 14.0 → '14', 2.5 → '2.5'."""
    try:
        f = float(v)
        if f == int(f):
            return str(int(f))
        return str(round(f, 4))
    except (TypeError, ValueError):
        return str(v)


def _math_expr_to_text(expr, op_map: Dict[str, str] = None) -> str:
    """
    Convertit un MathOp AST en expression lisible.
    ADD(2, MUL(3, 4)) → "2 + 3 × 4"
    """
    if op_map is None:
        op_map = {
            'ADD': ' + ', 'SUB': ' - ', 'MUL': ' × ', 'DIV': ' ÷ ',
            'POW': '^', 'MOD': ' % ',
            'GT': ' > ', 'GE': ' ≥ ', 'LT': ' < ', 'LE': ' ≤ ',
            'EQ': ' = ', 'NE': ' ≠ ',
        }
    if isinstance(expr, Literal):
        return _fmt_number(expr.value)
    if isinstance(expr, Var):
        return expr.name
    if isinstance(expr, MathOp):
        left = _math_expr_to_text(expr.left, op_map)
        if expr.right is not None and expr.op in op_map:
            return f"{left}{op_map[expr.op]}{_math_expr_to_text(expr.right, op_map)}"
        unary = {'SQRT': '√', 'NEG': '-', 'ABS': '|', 'FLOOR': '⌊'}
        if expr.op in unary:
            return f"{unary[expr.op]}({left})"
        return f"{expr.op}({left})"
    if isinstance(expr, FunctionCall):
        args = ", ".join(_math_expr_to_text(a, op_map) for a in expr.args)
        return f"{expr.name}({args})"
    return str(expr)


def _find_result_expr(program: Program) -> Optional[MathOp]:
    """Trouve l'expression calculée (le Assign avant le Return)."""
    if program is None:
        return None
    for stmt in reversed(program.statements):
        if isinstance(stmt, Assign) and isinstance(stmt.value, MathOp):
            return stmt.value
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# LE SYNTHÉTISEUR DE RÉPONSES
# ═══════════════════════════════════════════════════════════════════════════════

class WaveResponse:
    """Synthetise une réponse naturelle à partir du résultat du pipeline."""

    def synthesize(self, result) -> str:
        """
        Construit la réponse finale selon l'intention.

        Args:
            result: PipelineResult (question, intent, env, program, ...)

        Returns:
            une phrase française complète
        """
        intent = getattr(result, 'intent', 'query')
        handler = getattr(self, f'_resp_{intent}', None)
        if handler is not None:
            try:
                resp = handler(result)
                if resp:
                    return resp
            except Exception:
                pass
        return self._resp_fallback(result)

    # ── Par intention ──────────────────────────────────────────────────────

    def _resp_math(self, result) -> str:
        expr = _find_result_expr(result.program)
        value = result.env.get('resultat')
        if value is None:
            return ""
        if expr is not None:
            text = _math_expr_to_text(expr)
            return f"{text} = {_fmt_number(value)}."
        return f"Le résultat est {_fmt_number(value)}."

    def _resp_code(self, result) -> str:
        code = getattr(result, 'python_code', '') or ''
        # Extraire la fonction générée (corps principal)
        lines = [l for l in code.split('\n')
                 if l.strip() and not l.strip().startswith(('#', 'import',
                                                            'from', 'try',
                                                            'except'))]
        body = '\n'.join(lines) if lines else code
        return f"Voici le code généré :\n{body}"

    def _resp_reason(self, result) -> str:
        value = result.env.get('reponse')
        if value is None:
            return "Voici mon raisonnement."
        text = self._clean_value(value)
        if not text:
            return "Voici mon raisonnement."
        return f"J'en déduis : {text}."

    def _resp_query(self, result) -> str:
        value = result.env.get('reponse') or result.env.get('ψ_r')
        if value is None:
            return "Voici ce que je trouve."
        text = self._clean_value(value)
        if not text:
            return "Voici ce que je trouve."
        return f"Voici ce que je trouve : {text}."

    def _resp_store_fact(self, result) -> str:
        value = result.env.get('confirmation')
        if value is None:
            return "Fait mémorisé."
        text = self._clean_value(value)
        return f"Fait mémorisé : {text}." if text else "Fait mémorisé."

    def _resp_creative(self, result) -> str:
        value = result.env.get('idee')
        text = self._clean_value(value) if value is not None else ""
        return f"Voici une idée : {text}." if text else "Voici une idée."

    def _resp_compare(self, result) -> str:
        value = result.env.get('analyse')
        text = self._clean_value(value) if value is not None else ""
        return f"Voici l'analyse : {text}." if text else "Voici l'analyse."

    def _resp_sample(self, result) -> str:
        value = result.env.get('echantillon')
        text = self._clean_value(value) if value is not None else ""
        return f"Proposition : {text}." if text else "Proposition."

    def _resp_evaluate(self, result) -> str:
        value = result.env.get('coherence_score')
        if value is None:
            return "Évaluation effectuée."
        score = _fmt_number(value)
        qualif = ('élevée' if float(value) > 0.6 else
                  'modérée' if float(value) > 0.3 else 'faible')
        return f"Score de cohérence : {score} (confiance {qualif})."

    def _resp_tool_use(self, result) -> str:
        value = result.env.get('resultat')
        if value is None:
            return "Action effectuée."
        return f"Résultat : {_fmt_number(value)}."

    # ── Fallback ───────────────────────────────────────────────────────────

    def _resp_fallback(self, result) -> str:
        # Dernière variable du programme
        env = getattr(result, 'env', {}) or {}
        for name in reversed(list(env.keys())):
            if name.startswith('_'):
                continue
            value = env[name]
            if hasattr(value, 'dtype') and getattr(value, 'dtype', None).kind == 'c':
                continue
            text = self._clean_value(value)
            if text:
                return f"{text}."
        return "Voici ma réponse."

    @staticmethod
    def _clean_value(value) -> str:
        """Convertit une valeur en texte lisible."""
        try:
            if hasattr(value, 'ndim') and value.ndim == 2:
                words = [str(w) for w in value[:, 0]]
                return " ".join(words)
            if isinstance(value, (list, tuple)) and value:
                words = []
                for it in value:
                    if isinstance(it, (list, tuple)) and it:
                        words.append(str(it[0]))
                    else:
                        words.append(str(it))
                return " ".join(words)
            if isinstance(value, (str, int, float)):
                return str(value)
            if hasattr(value, 'shape'):
                return ""
            return str(value)
        except Exception:
            return str(value)


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    from wave_pipeline import WavePipeline

    print("=" * 65)
    print("  🌊 WAVE RESPONSE — Fluidité conversationnelle")
    print("=" * 65)

    pipeline = WavePipeline()
    responder = WaveResponse()

    tests = [
        "Calcule 2 plus 3 fois 4",
        "racine carrée de 16",
        "combien font 15% de 200",
        "écris une fonction factorielle",
        "Qu'est-ce que la lumière ?",
        "Souviens-toi que la Terre tourne autour du Soleil",
        "Quelle est la différence entre l'amour et l'amitié ?",
        "Imagine un mélange entre la pluie et la musique",
        "Échantillonne avec température 0.8 sur la créativité",
        "Évalue la qualité de la réponse : le ciel est bleu",
    ]

    for q in tests:
        r = pipeline.run(q)
        resp = responder.synthesize(r)
        print(f"\n  ❓ {q}")
        print(f"  💬 {resp}")

    print("\n" + "=" * 65)
    print("  ✅ Wave Response — Les réponses parlent.")
    print("=" * 65)
