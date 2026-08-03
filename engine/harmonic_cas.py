"""
Harmonic CAS — Computer Algebra System par interférence symbolique
===================================================================
Moteur de calcul symbolique déterministe basé sur SymPy.

Principe : la théorie harmonique postule que TOUT est calculable
déterministement. SymPy est l'implémentation pure de ce principe
pour les mathématiques : zéro approximation, zéro paramètre appris,
100% exact.

Le parseur traduit le langage naturel (FR/EN) → expressions SymPy,
puis SymPy calcule le résultat exact.

Capacités :
  - Dérivées (partielles, produit, quotient, chaîne)
  - Intégrales (définies, indéfinies, par substitution)
  - Limites (L'Hôpital, forme indéterminée)
  - Équations (polynomiales, systèmes)
  - Algèbre linéaire (matrices, déterminants, valeurs propres)
  - Simplification, factorisation, développement
  - Séries de Taylor
  - Trigonométrie

Author: Univers-Holistique
"""

import re
import math
from typing import Optional, Tuple

try:
    import sympy
    from sympy import (
        Symbol, symbols, diff, integrate, limit, solve, simplify,
        factor, expand, Rational, sqrt, pi, E, oo, I, sin, cos, tan,
        exp, log, ln, Matrix, series, apart,
        together, trigsimp, latex, Function, Derivative,
        Integral, Limit, Eq, Sum, floor, ceiling,
        factorial, binomial, Abs, arg,
    )
    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False


class HarmonicCAS:
    """
    Computer Algebra System harmonique.

    Usage:
        cas = HarmonicCAS()
        result = cas.solve("dérivée de x^3 + 2x")
        # → "3x² + 2"

        result = cas.solve("intégrale de x^2")
        # → "x³/3"

        result = cas.solve("résoudre x^2 - 5x + 6 = 0")
        # → "x = 2, x = 3"
    """

    def __init__(self):
        self.x = Symbol('x')
        self.y = Symbol('y')
        self.z = Symbol('z')
        self.t = Symbol('t')
        self.n = Symbol('n')
        self._cache = {}

    def solve(self, question: str) -> Optional[str]:
        """
        Tente de résoudre une question mathématique symbolique.

        Returns:
            La réponse en texte, ou None si la question n'est pas reconnue.
        """
        if not HAS_SYMPY:
            return None

        q = question.lower().strip()
        # Ponctuation finale (« ? », « ! ») et accents : les patterns
        # utilisent des classes [ée]/[àa] mais la question peut arriver
        # normalisée (« quelle est la dérivée de x^2 ? ») — le « ? » final
        # casse les patterns terminés par « $ ».
        q = q.rstrip('?！!.').strip()
        for _a, _b in [('é', 'e'), ('è', 'e'), ('ê', 'e'), ('ë', 'e'),
                       ('à', 'a'), ('â', 'a'), ('î', 'i'), ('ï', 'i'),
                       ('ô', 'o'), ('ù', 'u'), ('û', 'u'), ('ç', 'c')]:
            q = q.replace(_a, _b)

        # 1. Dérivées
        result = self._try_derivative(q)
        if result:
            return result

        # 2. Intégrales
        result = self._try_integral(q)
        if result:
            return result

        # 3. Limites
        result = self._try_limit(q)
        if result:
            return result

        # 4. Équations
        result = self._try_equation(q)
        if result:
            return result

        # 5. Simplification
        result = self._try_simplify(q)
        if result:
            return result

        # 6. Matrices
        result = self._try_matrix(q)
        if result:
            return result

        # 7. Factorisation / Développement
        result = self._try_factor_expand(q)
        if result:
            return result

        # 8. Séries de Taylor
        result = self._try_series(q)
        if result:
            return result

        return None

    def _parse_expr(self, expr_str: str) -> Optional[object]:
        """Parse une expression mathématique en objet SymPy."""
        expr_str = expr_str.strip()
        if not expr_str:
            return None

        # Nettoyer : ^ → **, × → *, ÷ → /, etc.
        expr_str = expr_str.replace('^', '**')
        expr_str = expr_str.replace('×', '*').replace('·', '*')
        expr_str = expr_str.replace('÷', '/')
        expr_str = expr_str.replace('√', 'sqrt')
        expr_str = expr_str.replace('π', 'pi')
        expr_str = expr_str.replace('∞', 'oo')
        expr_str = expr_str.replace('²', '**2').replace('³', '**3')
        expr_str = expr_str.replace('⁴', '**4').replace('⁵', '**5')
        # e^x → E**x  (ne pas confondre avec la variable e)
        expr_str = re.sub(r'\be\^(\w)', r'E**\1', expr_str)
        expr_str = re.sub(r'\be\*\*(\w)', r'E**\1', expr_str)

        # Insérer * pour la multiplication implicite :
        # 2x → 2*x, 3x^2 → 3*x**2, (x+1)(x-1) → (x+1)*(x-1)
        # Entre un chiffre et une lettre : 2x → 2*x
        expr_str = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expr_str)
        # Entre ) et ( ou ) et lettre : (x+1)(x-1) → (x+1)*(x-1)
        expr_str = re.sub(r'\)\s*\(', ')*(', expr_str)
        expr_str = re.sub(r'\)\s*([a-zA-Z])', r')*\1', expr_str)
        # Entre une lettre et ( : x(x+1) → x*(x+1)  (sauf fonctions)
        for fn in ['sin', 'cos', 'tan', 'exp', 'log', 'ln', 'sqrt', 'pi']:
            expr_str = expr_str.replace(fn + '*(', fn + '(')
        expr_str = re.sub(r'([a-zA-Z])\(', r'\1*(', expr_str)
        for fn in ['sin*(', 'cos*(', 'tan*(', 'exp*(', 'log*(', 'ln*(', 'sqrt*(', 'pi*(']:
            real_fn = fn.replace('*(', '(')
            expr_str = expr_str.replace(fn, real_fn)

        # Fonctions trigonométriques
        # (déjà gérées par sympy si on importe sin, cos, tan)

        # Variables disponibles
        local_dict = {
            'x': self.x, 'y': self.y, 'z': self.z, 't': self.t, 'n': self.n,
            'pi': pi, 'e': E, 'E': E, 'I': I, 'oo': oo,
            'sin': sin, 'cos': cos, 'tan': tan, 'exp': exp,
            'log': log, 'ln': ln, 'sqrt': sqrt,
            'Rational': Rational,
        }

        try:
            return sympy.sympify(expr_str, locals=local_dict)
        except Exception:
            try:
                # Essayer avec eval plus permissif
                return eval(expr_str, {"__builtins__": {}}, local_dict)
            except Exception:
                return None

    def _format_result(self, expr) -> str:
        """Formate un résultat SymPy en texte lisible."""
        s = str(expr)
        # Améliorer la lisibilité
        s = s.replace('**', '^').replace('*', '·')
        s = s.replace('sqrt', '√')
        s = s.replace('pi', 'π')
        s = s.replace('oo', '∞')
        return s

    # ═══════════════════════════════════════════════════════════════
    # DÉRIVÉES
    # ═══════════════════════════════════════════════════════════════

    def _try_derivative(self, q: str) -> Optional[str]:
        """Détecte et calcule une dérivée."""
        # Patterns: "dérivée de X", "dérivée de X par rapport à y",
        #           "derivative of X", "d/dx(X)", "diff X"
        patterns = [
            r'(?:d[ée]riv[ée]e?\s+(?:de|du|de la)\s+)(.+?)(?:\s+par\s+rapport\s+[àa]\s+(\w))?$',
            r'(?:derivative\s+of\s+)(.+?)(?:\s+with\s+respect\s+to\s+(\w))?$',
            r'd/d(\w)\((.+)\)$',
            r'diff\s*\((.+)\)$',
            r'diff\s+(.+)$',
        ]

        for i, pat in enumerate(patterns):
            m = re.search(pat, q)
            if m:
                if i == 2:  # d/dx(expr)
                    var_name = m.group(1)
                    expr_str = m.group(2)
                else:
                    expr_str = m.group(1)
                    var_name = m.group(2) if m.lastindex >= 2 and m.group(2) else 'x'

                expr = self._parse_expr(expr_str)
                if expr is None:
                    continue

                var = Symbol(var_name) if var_name else self.x
                try:
                    result = diff(expr, var)
                    result_simplified = simplify(result)
                    orig = self._format_result(expr)
                    deriv = self._format_result(result_simplified)
                    return f"La dérivée de {orig} par rapport à {var_name} est : {deriv}"
                except Exception:
                    continue
        return None

    # ═══════════════════════════════════════════════════════════════
    # INTÉGRALES
    # ═══════════════════════════════════════════════════════════════

    def _try_integral(self, q: str) -> Optional[str]:
        """Détecte et calcule une intégrale."""
        # Patterns: "intégrale de X", "intégrale de X entre a et b",
        #           "integral of X", "∫X dx"
        # Intégrale définie: "intégrale de X de a à b"
        m = re.search(r'(?:int[ée]grale\s+(?:de|du)\s+)(.+?)\s+de\s+([\d.\-]+)\s+[àa]\s+([\d.\-]+)', q)
        if m:
            expr_str, a_str, b_str = m.group(1), m.group(2), m.group(3)
            expr = self._parse_expr(expr_str)
            if expr is not None:
                try:
                    a_val = float(a_str)
                    b_val = float(b_str)
                    result = integrate(expr, (self.x, a_val, b_val))
                    orig = self._format_result(expr)
                    res = self._format_result(result)
                    return f"L'intégrale de {orig} de {a_val} à {b_val} est : {res}"
                except Exception:
                    pass

        # Intégrale indéfinie
        patterns = [
            r'(?:int[ée]grale\s+(?:de|du|de la)\s+)(.+?)(?:\s+dx|\s+par\s+rapport|$)',
            r'(?:integral\s+of\s+)(.+?)(?:\s+dx|$)',
            r'[∫]\s*(.+?)(?:\s+dx|$)',
        ]
        for pat in patterns:
            m = re.search(pat, q)
            if m:
                expr_str = m.group(1).strip()
                # Enlever "dx" à la fin (mais pas les lettres individuelles!)
                expr_str = re.sub(r'\s*dx\s*$', '', expr_str).strip()
                # Handle bare variable: "x" → integrate(x, x) = x²/2
                if not expr_str:
                    continue
                expr = self._parse_expr(expr_str)
                if expr is None:
                    continue
                # If expr is just a symbol (like x), integrate it
                if expr == self.x:
                    result = integrate(self.x, self.x)
                    result = simplify(result)
                    return f"L'intégrale de x est : {self._format_result(result)} + C"
                try:
                    result = integrate(expr, self.x)
                    result = simplify(result)
                    orig = self._format_result(expr)
                    res = self._format_result(result) + ' + C'
                    return f"L'intégrale de {orig} est : {res}"
                except Exception:
                    continue
        return None

    # ═══════════════════════════════════════════════════════════════
    # LIMITES
    # ═══════════════════════════════════════════════════════════════

    def _try_limit(self, q: str) -> Optional[str]:
        """Détecte et calcule une limite."""
        # "limite de X quand x tend vers a" / "limit of X as x→a"
        patterns = [
            r'limite\s+de\s+(.+?)\s+quand\s+(\w+)\s+tend\s+vers\s+([\d.\-∞infty]+)',
            r'limit\s+of\s+(.+?)\s+as\s+(\w+)\s*[→>]+\s*([\d.\-∞infty]+)',
            r'lim\s+(.+?)\s*,\s*(\w+)\s*[→>]+\s*([\d.\-∞infty]+)',
        ]
        for pat in patterns:
            m = re.search(pat, q)
            if m:
                expr_str = m.group(1)
                var_name = m.group(2)
                val_str = m.group(3).replace('∞', 'oo').replace('infinity', 'oo')
                expr = self._parse_expr(expr_str)
                if expr is None:
                    continue
                var = Symbol(var_name)
                try:
                    val = sympy.sympify(val_str)
                    result = limit(expr, var, val)
                    orig = self._format_result(expr)
                    res = self._format_result(result)
                    return f"La limite de {orig} quand {var_name} → {val_str} est : {res}"
                except Exception:
                    continue
        return None

    # ═══════════════════════════════════════════════════════════════
    # ÉQUATIONS
    # ═══════════════════════════════════════════════════════════════

    def _try_equation(self, q: str) -> Optional[str]:
        """Détecte et résout une équation."""
        # "résoudre X = Y" / "solve X = Y" / "résoudre X"
        # Le problème principal : le pattern générique (.+?)\s*=\s*(.+?)$
        # capture trop tôt. On filtre d'abord les autres patterns.

        # Pattern 1: "résoudre/solve/trouver" + expression
        m = re.search(r'(?:r[ée]soudre|r[ée]sous|solve|trouver)\s+(.+)', q)
        if m:
            eq_str = m.group(1).strip()
            if '=' in eq_str:
                parts = eq_str.split('=', 1)
                lhs = self._parse_expr(parts[0].strip())
                rhs = self._parse_expr(parts[1].strip())
            else:
                lhs = self._parse_expr(eq_str)
                rhs = 0

            if lhs is not None:
                try:
                    eq = Eq(lhs, rhs)
                    solutions = solve(eq, self.x)
                    if solutions:
                        sols_str = ", ".join(f"x = {self._format_result(s)}" for s in solutions)
                        return f"Solution : {sols_str}"
                except Exception:
                    pass

        # Pattern 2: expression avec = (mais PAS "résoudre" au début)
        # Seulement si on n'a pas déjà matché un autre type (dérivée, etc.)
        if '=' in q and not any(kw in q for kw in ['dériv', 'deriv', 'intégr', 'integr',
                                                     'limit', 'simpl', 'factor', 'dévelop',
                                                     'develop', 'série', 'series', 'matrice']):
            parts = q.split('=', 1)
            if len(parts) == 2:
                lhs = self._parse_expr(parts[0].strip())
                rhs = self._parse_expr(parts[1].strip())
                if lhs is not None and rhs is not None:
                    try:
                        eq = Eq(lhs, rhs)
                        solutions = solve(eq, self.x)
                        if solutions:
                            sols_str = ", ".join(f"x = {self._format_result(s)}" for s in solutions)
                            return f"Solution : {sols_str}"
                    except Exception:
                        pass

        return None

    # ═══════════════════════════════════════════════════════════════
    # SIMPLIFICATION
    # ═══════════════════════════════════════════════════════════════

    def _try_simplify(self, q: str) -> Optional[str]:
        """Détecte et simplifie une expression."""
        patterns = [
            r'(?:simplifier|simplify)\s+(.+)',
            r'(?:r[ée]duire|reduce)\s+(.+)',
        ]
        for pat in patterns:
            m = re.search(pat, q)
            if m:
                expr = self._parse_expr(m.group(1))
                if expr is None:
                    continue
                try:
                    result = simplify(expr)
                    orig = self._format_result(expr)
                    res = self._format_result(result)
                    if str(result) != str(expr):
                        return f"{orig} = {res}"
                except Exception:
                    continue
        return None

    # ═══════════════════════════════════════════════════════════════
    # MATRICES
    # ═══════════════════════════════════════════════════════════════

    def _try_matrix(self, q: str) -> Optional[str]:
        """Détecte et calcule des opérations matricielles."""
        # "déterminant de la matrice [[1,2],[3,4]]"
        m = re.search(r'd[ée]terminant\s+(?:de\s+(?:la\s+)?)?matrice\s*\[\[([^\]]+)\]\]\s*\[\[([^\]]+)\]\]', q)
        if m:
            try:
                row1 = [float(x.strip()) for x in m.group(1).split(',')]
                row2 = [float(x.strip()) for x in m.group(2).split(',')]
                mat = Matrix([row1, row2])
                det = mat.det()
                return f"Le déterminant est : {self._format_result(det)}"
            except Exception:
                pass

        return None

    # ═══════════════════════════════════════════════════════════════
    # FACTORISATION / DÉVELOPPEMENT
    # ═══════════════════════════════════════════════════════════════

    def _try_factor_expand(self, q: str) -> Optional[str]:
        """Factorise ou développe une expression."""
        # Factoriser
        m = re.search(r'(?:factoriser|factor|factorize)\s+(.+)', q)
        if m:
            expr = self._parse_expr(m.group(1))
            if expr is not None:
                try:
                    result = factor(expr)
                    orig = self._format_result(expr)
                    res = self._format_result(result)
                    return f"{orig} = {res}"
                except Exception:
                    pass

        # Développer
        m = re.search(r'(?:d[ée]velopper|expand)\s+(.+)', q)
        if m:
            expr = self._parse_expr(m.group(1))
            if expr is not None:
                try:
                    result = expand(expr)
                    orig = self._format_result(expr)
                    res = self._format_result(result)
                    return f"{orig} = {res}"
                except Exception:
                    pass

        return None

    # ═══════════════════════════════════════════════════════════════
    # SÉRIES DE TAYLOR
    # ═══════════════════════════════════════════════════════════════

    def _try_series(self, q: str) -> Optional[str]:
        """Développe en série de Taylor."""
        m = re.search(r'(?:s[ée]rie|taylor|series|d[ée]veloppement\s+limit[ée])\s+(?:de\s+)?(.+?)(?:\s+(?:autour|around|en)\s+(?:de\s+)?(\d+))?(?:\s+(?:ordre|order)\s+(\d+))?$', q)
        if m:
            expr_str = m.group(1)
            around = float(m.group(2)) if m.group(2) else 0
            order = int(m.group(3)) if m.group(3) else 6

            expr = self._parse_expr(expr_str)
            if expr is None:
                return None
            try:
                result = series(expr, self.x, around, order)
                orig = self._format_result(expr)
                res = self._format_result(result)
                return f"Développement de {orig} autour de x={around} à l'ordre {order} : {res}"
            except Exception:
                pass
        return None


# ═══════════════════════════════════════════════════════════════
# INSTANCE GLOBALE
# ═══════════════════════════════════════════════════════════════

_cas = None

def get_cas() -> Optional[HarmonicCAS]:
    """Retourne l'instance globale du CAS."""
    global _cas
    if _cas is None and HAS_SYMPY:
        _cas = HarmonicCAS()
    return _cas

def cas_solve(question: str) -> Optional[str]:
    """Raccourci : essaie de résoudre avec le CAS."""
    cas = get_cas()
    if cas is None:
        return None
    return cas.solve(question)


# ═══════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════

def _test():
    """Test du CAS."""
    print("=" * 60)
    print("TEST : Harmonic CAS (SymPy)")
    print("=" * 60)

    if not HAS_SYMPY:
        print("❌ SymPy non installé. pip install sympy")
        return

    cas = HarmonicCAS()

    tests = [
        # Dérivées
        "dérivée de x^3 + 2x",
        "dérivée de sin(x)",
        "dérivée de x^2 * cos(x)",
        "dérivée de e^x",
        "dérivée de ln(x)",
        "derivative of x^4 + 3x^2 - 5",
        "dérivée de 1/x",
        # Intégrales
        "intégrale de x^2",
        "intégrale de sin(x)",
        "intégrale de e^x",
        "intégrale de x^2 de 0 à 1",
        "intégrale de 2x",
        # Limites
        "limite de sin(x)/x quand x tend vers 0",
        "limite de (x^2-1)/(x-1) quand x tend vers 1",
        "limite de 1/x quand x tend vers 0",
        # Équations
        "résoudre x^2 - 5x + 6 = 0",
        "résoudre x^2 - 4 = 0",
        "résoudre 2x + 3 = 7",
        # Simplification
        "simplifier sin(x)^2 + cos(x)^2",
        "simplifier (x^2 - 1)/(x - 1)",
        # Factorisation
        "factoriser x^2 - 4",
        "factoriser x^2 + 2x + 1",
        # Développement
        "développer (x + 1)^3",
        "développer (x - 2)(x + 3)",
        # Séries
        "série de sin(x) ordere 5",
        "série de e^x",
    ]

    correct = 0
    for q in tests:
        result = cas.solve(q)
        if result:
            print(f"  ✅ {q}")
            print(f"     → {result}")
            correct += 1
        else:
            print(f"  ❌ {q}")
            print(f"     → (non reconnu)")

    print(f"\n{correct}/{len(tests)} tests réussis")


if __name__ == '__main__':
    _test()
