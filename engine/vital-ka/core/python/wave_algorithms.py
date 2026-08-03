"""
🌊 Wave Algorithms — Bibliothèque d'algorithmes en programmes harmoniques
==========================================================================

Les 84 templates de code_generator.py (strings, bugs inclus) deviennent des
PROGRAMMES HARMONIQUES : chaque algorithme est un AST wave_ir unique,
converti vers Python / JavaScript / TypeScript par wave_emit.

Multi-langage PAR CONSTRUCTION : un seul FunctionDef → N backends.
Vérifiés PAR EXÉCUTION : le code converti s'exécute et donne le bon résultat.

Usage :
    from wave_algorithms import WaveAlgorithmLibrary

    lib = WaveAlgorithmLibrary()
    py = lib.generate('factorial', 'python')   # def factorial(n): ...
    js = lib.generate('factorial', 'js')       # function factorial(n) { ... }
    ok = lib.verify('factorial')               # exécute + vérifie le résultat
"""

from __future__ import annotations

from typing import List, Dict, Optional, Callable, Tuple

from wave_ir import (Program, Assign, Return, IfStmt, WhileStmt, ForStmt,
                     FunctionDef, CodeBlock, AugAssign,
                     Var, Literal, StringLit, MathOp, FunctionCall,
                     ListLiteral, Subscript, RawCode)
from wave_emit import emit_python, emit_javascript, emit_typescript


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS DE CONSTRUCTION (AST compact)
# ═══════════════════════════════════════════════════════════════════════════════

def L(v: float) -> Literal:
    """Littéral numérique."""
    return Literal(float(v))

def V(name: str) -> Var:
    """Variable."""
    return Var(name)

def CALL(name: str, *args) -> FunctionCall:
    """Appel de fonction (ou builtin)."""
    return FunctionCall(name, list(args))

def OP(op: str, a, b=None) -> MathOp:
    """Opération mathématique."""
    return MathOp(op, a, b)

def S(name: str, value) -> Assign:
    """Assignation."""
    return Assign(name, value)

def RET(expr) -> Return:
    """Retour."""
    return Return(expr)

def IF(cond, then_body, else_body=None) -> IfStmt:
    """Conditionnel."""
    return IfStmt(cond, then_body, else_body)

def WHILE(cond, body) -> WhileStmt:
    """Boucle while."""
    return WhileStmt(cond, body)

def FOR(target: str, iterable, body) -> ForStmt:
    """Boucle for."""
    return ForStmt(target, iterable, body)

def AUG(name: str, op: str, value) -> AugAssign:
    """Assignation augmentée."""
    return AugAssign(name, op, value)

def LST(*items) -> ListLiteral:
    """Liste littérale."""
    return ListLiteral(list(items))

def SUB(obj, idx) -> Subscript:
    """Accès par indice."""
    return Subscript(obj, idx)

def FUNC(name: str, params: List[str], body: List) -> FunctionDef:
    """Définition de fonction."""
    return FunctionDef(name, params, body)

def RANGE(start, end) -> FunctionCall:
    """range(start, end)."""
    return FunctionCall("range", [start, end])


# ═══════════════════════════════════════════════════════════════════════════════
# LE REGISTRE — 30 algorithmes en AST harmonique
# ═══════════════════════════════════════════════════════════════════════════════

ALGORITHM_LIBRARY: Dict[str, FunctionDef] = {
    # ── Maths ──────────────────────────────────────────────────────────────
    'sum': FUNC('sum', ['items'], [
        S('total', L(0.0)),
        FOR('x', V('items'), [AUG('total', 'ADD', V('x'))]),
        RET(V('total')),
    ]),
    'max': FUNC('max', ['items'], [
        S('best', SUB(V('items'), L(0.0))),
        FOR('x', V('items'), [
            IF(OP('GT', V('x'), V('best')), [S('best', V('x'))]),
        ]),
        RET(V('best')),
    ]),
    'min': FUNC('min', ['items'], [
        S('best', SUB(V('items'), L(0.0))),
        FOR('x', V('items'), [
            IF(OP('LT', V('x'), V('best')), [S('best', V('x'))]),
        ]),
        RET(V('best')),
    ]),
    'average': FUNC('average', ['items'], [
        S('total', L(0.0)),
        S('n', L(0.0)),
        FOR('x', V('items'), [AUG('total', 'ADD', V('x')), AUG('n', 'ADD', L(1.0))]),
        RET(OP('DIV', V('total'), V('n'))),
    ]),
    'count': FUNC('count', ['items'], [
        S('total', L(0.0)),
        FOR('x', V('items'), [AUG('total', 'ADD', L(1.0))]),
        RET(V('total')),
    ]),
    'factorial': FUNC('factorial', ['n'], [
        S('resultat', L(1.0)),
        FOR('i', RANGE(L(2.0), OP('ADD', V('n'), L(1.0))),
            [S('resultat', OP('MUL', V('resultat'), V('i')))]),
        RET(V('resultat')),
    ]),
    'fibonacci': FUNC('fibonacci', ['n'], [
        IF(OP('LE', V('n'), L(1.0)), [RET(V('n'))]),
        S('a', L(0.0)),
        S('b', L(1.0)),
        FOR('i', RANGE(L(2.0), OP('ADD', V('n'), L(1.0))), [
            S('temp', V('a')),
            S('a', V('b')),
            S('b', OP('ADD', V('temp'), V('b'))),
        ]),
        RET(V('b')),
    ]),
    'gcd': FUNC('gcd', ['a', 'b'], [
        WHILE(OP('NE', V('b'), L(0.0)), [
            S('temp', V('b')),
            S('b', OP('MOD', V('a'), V('b'))),
            S('a', V('temp')),
        ]),
        RET(OP('ABS', V('a'))),
    ]),
    'lcm': FUNC('lcm', ['a', 'b'], [
        RET(OP('DIV', OP('ABS', OP('MUL', V('a'), V('b'))),
               CALL('gcd', V('a'), V('b')))),
    ]),
    'power': FUNC('power', ['base', 'exp'], [
        RET(OP('POW', V('base'), V('exp'))),
    ]),
    'sqrt': FUNC('sqrt', ['n'], [
        RET(OP('SQRT', V('n'))),
    ]),
    'abs': FUNC('abs', ['n'], [
        RET(OP('ABS', V('n'))),
    ]),
    'is_prime': FUNC('is_prime', ['n'], [
        IF(OP('LE', V('n'), L(1.0)), [RET(L(0.0))]),
        FOR('i', RANGE(L(2.0),
                       OP('ADD', OP('FLOOR', OP('SQRT', V('n'))), L(1.0))), [
            IF(OP('EQ', OP('MOD', V('n'), V('i')), L(0.0)), [RET(L(0.0))]),
        ]),
        RET(L(1.0)),
    ]),
    'is_even': FUNC('is_even', ['n'], [
        RET(OP('EQ', OP('MOD', V('n'), L(2.0)), L(0.0))),
    ]),
    'clamp': FUNC('clamp', ['x', 'lo', 'hi'], [
        IF(OP('LT', V('x'), V('lo')), [RET(V('lo'))]),
        IF(OP('GT', V('x'), V('hi')), [RET(V('hi'))]),
        RET(V('x')),
    ]),
    'celsius_to_fahrenheit': FUNC('celsius_to_fahrenheit', ['c'], [
        RET(OP('ADD', OP('MUL', OP('DIV', V('c'), L(5.0)), L(9.0)), L(32.0))),
    ]),
    'fahrenheit_to_celsius': FUNC('fahrenheit_to_celsius', ['f'], [
        RET(OP('MUL', OP('SUB', V('f'), L(32.0)), OP('DIV', L(5.0), L(9.0)))),
    ]),

    # ── Algorithmes ─────────────────────────────────────────────────────────
    'linear_search': FUNC('linear_search', ['arr', 'target'], [
        S('i', L(0.0)),
        WHILE(OP('LT', V('i'), CALL('len', V('arr'))), [
            IF(OP('EQ', SUB(V('arr'), V('i')), V('target')), [RET(V('i'))]),
            AUG('i', 'ADD', L(1.0)),
        ]),
        RET(OP('NEG', L(1.0))),
    ]),
    'binary_search': FUNC('binary_search', ['arr', 'target'], [
        S('left', L(0.0)),
        S('right', OP('SUB', CALL('len', V('arr')), L(1.0))),
        WHILE(OP('LE', V('left'), V('right')), [
            S('mid', OP('FLOOR', OP('DIV', OP('ADD', V('left'), V('right')),
                                    L(2.0)))),
            IF(OP('EQ', SUB(V('arr'), V('mid')), V('target')), [RET(V('mid'))]),
            IF(OP('LT', SUB(V('arr'), V('mid')), V('target')),
               [S('left', OP('ADD', V('mid'), L(1.0)))],
               [S('right', OP('SUB', V('mid'), L(1.0)))]),
        ]),
        RET(OP('NEG', L(1.0))),
    ]),
    'contains': FUNC('contains', ['items', 'target'], [
        FOR('x', V('items'), [
            IF(OP('EQ', V('x'), V('target')), [RET(L(1.0))]),
        ]),
        RET(L(0.0)),
    ]),
    'frequency': FUNC('frequency', ['items', 'target'], [
        S('n', L(0.0)),
        FOR('x', V('items'), [
            IF(OP('EQ', V('x'), V('target')), [AUG('n', 'ADD', L(1.0))]),
        ]),
        RET(V('n')),
    ]),
    'sign': FUNC('sign', ['x'], [
        IF(OP('GT', V('x'), L(0.0)), [RET(L(1.0))]),
        IF(OP('LT', V('x'), L(0.0)), [RET(OP('NEG', L(1.0)))]),
        RET(L(0.0)),
    ]),
    'is_sorted': FUNC('is_sorted', ['items'], [
        S('i', L(1.0)),
        WHILE(OP('LT', V('i'), CALL('len', V('items'))), [
            IF(OP('LT', SUB(V('items'), V('i')),
                   SUB(V('items'), OP('SUB', V('i'), L(1.0)))),
               [RET(L(0.0))]),
            AUG('i', 'ADD', L(1.0)),
        ]),
        RET(L(1.0)),
    ]),
    'sum_range': FUNC('sum_range', ['n'], [
        S('total', L(0.0)),
        FOR('i', RANGE(L(1.0), OP('ADD', V('n'), L(1.0))),
            [AUG('total', 'ADD', V('i'))]),
        RET(V('total')),
    ]),
    'countdown': FUNC('countdown', ['n'], [
        WHILE(OP('GT', V('n'), L(0.0)), [AUG('n', 'SUB', L(1.0))]),
        RET(V('n')),
    ]),
    'sum_of_squares': FUNC('sum_of_squares', ['items'], [
        S('total', L(0.0)),
        FOR('x', V('items'), [AUG('total', 'ADD', OP('MUL', V('x'), V('x')))]),
        RET(V('total')),
    ]),

    # ── Nouvelles opérations numériques (AST pur) ──────────────────────────
    'mean_absolute_deviation': FUNC('mean_absolute_deviation', ['data'], [
        S('moyenne', OP('DIV', CALL('sum', V('data')), CALL('len', V('data')))),
        S('total', L(0.0)),
        FOR('x', V('data'),
            [AUG('total', 'ADD', OP('ABS', OP('SUB', V('x'), V('moyenne'))))]),
        RET(OP('DIV', V('total'), CALL('len', V('data')))),
    ]),
    'variance': FUNC('variance', ['data'], [
        S('moyenne', OP('DIV', CALL('sum', V('data')), CALL('len', V('data')))),
        S('total', L(0.0)),
        FOR('x', V('data'),
            [AUG('total', 'ADD',
                 OP('MUL', OP('SUB', V('x'), V('moyenne')),
                    OP('SUB', V('x'), V('moyenne'))))]),
        RET(OP('DIV', V('total'), CALL('len', V('data')))),
    ]),
    'digit_sum': FUNC('digit_sum', ['n'], [
        S('total', L(0.0)),
        WHILE(OP('GT', V('n'), L(0.0)), [
            AUG('total', 'ADD', OP('MOD', V('n'), L(10.0))),
            S('n', OP('FLOOR', OP('DIV', V('n'), L(10.0)))),
        ]),
        RET(V('total')),
    ]),
    'reverse_number': FUNC('reverse_number', ['n'], [
        S('rev', L(0.0)),
        WHILE(OP('GT', V('n'), L(0.0)), [
            S('rev', OP('ADD', OP('MUL', V('rev'), L(10.0)),
                        OP('MOD', V('n'), L(10.0)))),
            S('n', OP('FLOOR', OP('DIV', V('n'), L(10.0)))),
        ]),
        RET(V('rev')),
    ]),
    'is_leap_year': FUNC('is_leap_year', ['year'], [
        IF(OP('EQ', OP('MOD', V('year'), L(400.0)), L(0.0)), [RET(L(1.0))]),
        IF(OP('EQ', OP('MOD', V('year'), L(100.0)), L(0.0)), [RET(L(0.0))]),
        IF(OP('EQ', OP('MOD', V('year'), L(4.0)), L(0.0)), [RET(L(1.0))]),
        RET(L(0.0)),
    ]),
    'is_palindrome_number': FUNC('is_palindrome_number', ['n'], [
        S('rev', L(0.0)),
        S('original', V('n')),
        WHILE(OP('GT', V('n'), L(0.0)), [
            S('rev', OP('ADD', OP('MUL', V('rev'), L(10.0)),
                        OP('MOD', V('n'), L(10.0)))),
            S('n', OP('FLOOR', OP('DIV', V('n'), L(10.0)))),
        ]),
        RET(OP('EQ', V('original'), V('rev'))),
    ]),
    'count_digits': FUNC('count_digits', ['n'], [
        S('total', L(0.0)),
        WHILE(OP('GT', V('n'), L(0.0)), [
            AUG('total', 'ADD', L(1.0)),
            S('n', OP('FLOOR', OP('DIV', V('n'), L(10.0)))),
        ]),
        RET(V('total')),
    ]),
    'digital_root': FUNC('digital_root', ['n'], [
        WHILE(OP('GE', V('n'), L(10.0)), [
            S('total', L(0.0)),
            WHILE(OP('GT', V('n'), L(0.0)), [
                AUG('total', 'ADD', OP('MOD', V('n'), L(10.0))),
                S('n', OP('FLOOR', OP('DIV', V('n'), L(10.0)))),
            ]),
            S('n', V('total')),
        ]),
        RET(V('n')),
    ]),
    'collatz_steps': FUNC('collatz_steps', ['n'], [
        S('steps', L(0.0)),
        WHILE(OP('GT', V('n'), L(1.0)), [
            IF(OP('EQ', OP('MOD', V('n'), L(2.0)), L(0.0)),
               [S('n', OP('DIV', V('n'), L(2.0)))],
               [S('n', OP('ADD', OP('MUL', V('n'), L(3.0)), L(1.0)))]),
            AUG('steps', 'ADD', L(1.0)),
        ]),
        RET(V('steps')),
    ]),
    'is_power_of_two': FUNC('is_power_of_two', ['n'], [
        IF(OP('LE', V('n'), L(0.0)), [RET(L(0.0))]),
        WHILE(OP('EQ', OP('MOD', V('n'), L(2.0)), L(0.0)),
              [S('n', OP('DIV', V('n'), L(2.0)))]),
        RET(OP('EQ', V('n'), L(1.0))),
    ]),
}

# ── Opérations strings (RawCode python — échappatoire documenté) ─────────────
# Le multi-langage AST couvre les maths/listes pures ; les manipulations de
# chaînes sont Python-first (le backend JS/TS évoluera).

STRING_OPS: Dict[str, str] = {
    'reverse_string': (
        "def reverse_string(s):\n"
        "    return s[::-1]\n"
    ),
    'is_palindrome': (
        "def is_palindrome(s):\n"
        "    t = s.replace(' ', '').lower()\n"
        "    return 1 if t == t[::-1] else 0\n"
    ),
    'count_vowels': (
        "def count_vowels(s):\n"
        "    return sum(1 for c in s.lower() if c in 'aeiouy')\n"
    ),
    'uppercase': (
        "def uppercase(s):\n"
        "    return s.upper()\n"
    ),
    'count_occurrences': (
        "def count_occurrences(s, ch):\n"
        "    return s.count(ch)\n"
    ),
    'unique_items': (
        "def unique_items(items):\n"
        "    return list(dict.fromkeys(items))\n"
    ),
    'running_sum': (
        "def running_sum(items):\n"
        "    out = []\n"
        "    total = 0\n"
        "    for x in items:\n"
        "        total += x\n"
        "        out.append(total)\n"
        "    return out\n"
    ),
    'flip_case': (
        "def flip_case(s):\n"
        "    return ''.join(c.lower() if c.isupper() else c.upper() for c in s)\n"
    ),
    'is_balanced': (
        "def is_balanced(s):\n"
        "    stack = []\n"
        "    pairs = {')': '(', ']': '[', '}': '{'}\n"
        "    for c in s:\n"
        "        if c in '([{':\n"
        "            stack.append(c)\n"
        "        elif c in pairs:\n"
        "            if not stack or stack.pop() != pairs[c]:\n"
        "                return 0\n"
        "    return 1 if not stack else 0\n"
    ),
    'most_frequent': (
        "def most_frequent(items):\n"
        "    from collections import Counter\n"
        "    return Counter(items).most_common(1)[0][0]\n"
    ),
    'remove_duplicates': (
        "def remove_duplicates(items):\n"
        "    seen = set()\n"
        "    out = []\n"
        "    for x in items:\n"
        "        if x not in seen:\n"
        "            seen.add(x)\n"
        "            out.append(x)\n"
        "    return out\n"
    ),
    'median': (
        "def median(data):\n"
        "    s = sorted(data)\n"
        "    n = len(s)\n"
        "    mid = n // 2\n"
        "    if n % 2 == 1:\n"
        "        return s[mid]\n"
        "    return (s[mid - 1] + s[mid]) / 2\n"
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# CAS DE TEST PAR OPÉRATION (pour la vérification par exécution)
# ═══════════════════════════════════════════════════════════════════════════════

TEST_CASES: Dict[str, Tuple[tuple, object]] = {
    'sum': (([1.0, 2.0, 3.0],), 6.0),
    'max': (([3.0, 7.0, 2.0],), 7.0),
    'min': (([3.0, 7.0, 2.0],), 2.0),
    'average': (([2.0, 4.0, 6.0],), 4.0),
    'count': (([1.0, 2.0, 3.0],), 3.0),
    'factorial': ((5.0,), 120.0),
    'fibonacci': ((7.0,), 13.0),
    'gcd': ((12.0, 18.0), 6.0),
    'lcm': ((4.0, 6.0), 12.0),
    'power': ((2.0, 10.0), 1024.0),
    'sqrt': ((16.0,), 4.0),
    'abs': ((-5.0,), 5.0),
    'is_prime': ((7.0,), 1.0),
    'is_even': ((4.0,), 1.0),
    'clamp': ((15.0, 0.0, 10.0), 10.0),
    'celsius_to_fahrenheit': ((0.0,), 32.0),
    'fahrenheit_to_celsius': ((32.0,), 0.0),
    'linear_search': (([1.0, 2.0, 3.0], 2.0), 1.0),
    'binary_search': (([1.0, 3.0, 5.0, 7.0], 5.0), 2.0),
    'contains': (([1.0, 2.0], 2.0), 1.0),
    'frequency': (([1.0, 2.0, 1.0], 1.0), 2.0),
    'sign': ((-3.0,), -1.0),
    'is_sorted': (([1.0, 2.0, 3.0],), 1.0),
    'sum_range': ((5.0,), 15.0),
    'countdown': ((3.0,), 0.0),
    'sum_of_squares': (([1.0, 2.0, 3.0],), 14.0),
    # Nouvelles opérations
    'mean_absolute_deviation': (([1.0, 2.0, 3.0],), 2.0 / 3.0),
    'variance': (([1.0, 2.0, 3.0],), 2.0 / 3.0),
    'digit_sum': ((123.0,), 6.0),
    'reverse_number': ((1234.0,), 4321.0),
    'is_leap_year': ((2024.0,), 1.0),
    'is_palindrome_number': ((121.0,), 1.0),
    'count_digits': ((12345.0,), 5.0),
    'digital_root': ((987.0,), 6.0),
    'median': (([1.0, 3.0, 5.0],), 3.0),
    'is_power_of_two': ((16.0,), 1.0),
    'collatz_steps': ((6.0,), 8.0),
}

# ═══════════════════════════════════════════════════════════════════════════════
# PROBLÈMES STYLE HUMANEVAL — vérifiés par ASSERTIONS EXÉCUTÉES
# ═══════════════════════════════════════════════════════════════════════════════
#
# Chaque problème : (nom, opération du registre, liste d'assertions Python).
# Un problème est RÉUSSI si et seulement si TOUTES les assertions passent
# sur le code converti EXÉCUTÉ. Vérification par exécution, pas par regex.

HUMANEVAL_PROBLEMS: Dict[str, Dict] = {
    'sum_list': {
        'op': 'sum',
        'description': 'Somme des éléments d\'une liste',
        'assertions': [
            'sum([1, 2, 3]) == 6',
            'sum([0, 0, 0]) == 0',
            'sum([5]) == 5',
        ],
    },
    'max_of_list': {
        'op': 'max',
        'description': 'Maximum d\'une liste',
        'assertions': [
            'max([3, 7, 2]) == 7',
            'max([-1, -5, -3]) == -1',
            'max([42]) == 42',
        ],
    },
    'factorial_fn': {
        'op': 'factorial',
        'description': 'Factorielle de n',
        'assertions': [
            'factorial(0) == 1',
            'factorial(5) == 120',
            'factorial(7) == 5040',
        ],
    },
    'fibonacci_n': {
        'op': 'fibonacci',
        'description': 'N-ième nombre de Fibonacci',
        'assertions': [
            'fibonacci(0) == 0',
            'fibonacci(1) == 1',
            'fibonacci(10) == 55',
        ],
    },
    'gcd_fn': {
        'op': 'gcd',
        'description': 'Plus grand commun diviseur',
        'assertions': [
            'gcd(48, 36) == 12',
            'gcd(17, 13) == 1',
            'gcd(100, 10) == 10',
        ],
    },
    'prime_check': {
        'op': 'is_prime',
        'description': 'Test de primalité',
        'assertions': [
            'is_prime(2) == 1',
            'is_prime(97) == 1',
            'is_prime(100) == 0',
        ],
    },
    'binary_search_fn': {
        'op': 'binary_search',
        'description': 'Recherche binaire',
        'assertions': [
            'binary_search([1, 3, 5, 7, 9], 7) == 3',
            'binary_search([1, 3, 5, 7, 9], 4) == -1',
            'binary_search([], 1) == -1',
        ],
    },
    'sum_of_squares_fn': {
        'op': 'sum_of_squares',
        'description': 'Somme des carrés',
        'assertions': [
            'sum_of_squares([1, 2, 3]) == 14',
            'sum_of_squares([]) == 0',
            'sum_of_squares([2, 2]) == 8',
        ],
    },
    'is_leap_year_fn': {
        'op': 'is_leap_year',
        'description': 'Année bissextile',
        'assertions': [
            'is_leap_year(2024) == 1',
            'is_leap_year(1900) == 0',
            'is_leap_year(2000) == 1',
        ],
    },
    'digit_sum_fn': {
        'op': 'digit_sum',
        'description': 'Somme des chiffres',
        'assertions': [
            'digit_sum(123) == 6',
            'digit_sum(0) == 0',
            'digit_sum(9999) == 36',
        ],
    },
    'reverse_number_fn': {
        'op': 'reverse_number',
        'description': 'Nombre inversé',
        'assertions': [
            'reverse_number(1234) == 4321',
            'reverse_number(100) == 1',
            'reverse_number(7) == 7',
        ],
    },
    'palindrome_number_fn': {
        'op': 'is_palindrome_number',
        'description': 'Nombre palindrome',
        'assertions': [
            'is_palindrome_number(121) == 1',
            'is_palindrome_number(123) == 0',
            'is_palindrome_number(9) == 1',
        ],
    },
    'digital_root_fn': {
        'op': 'digital_root',
        'description': 'Racine numérique',
        'assertions': [
            'digital_root(987) == 6',
            'digital_root(0) == 0',
            'digital_root(38) == 2',
        ],
    },
    'mean_abs_dev_fn': {
        'op': 'mean_absolute_deviation',
        'description': 'Écart absolu moyen',
        'assertions': [
            'abs(mean_absolute_deviation([1, 2, 3]) - 0.6666666) < 0.001',
            'mean_absolute_deviation([5, 5, 5]) == 0',
            'abs(mean_absolute_deviation([1, 9]) - 4.0) < 0.001',
        ],
    },
    'median_fn': {
        'op': 'median',
        'description': 'Médiane',
        'assertions': [
            'median([1, 3, 5]) == 3',
            'median([1, 2, 3, 4]) == 2.5',
            'median([7]) == 7',
        ],
    },
    'collatz_fn': {
        'op': 'collatz_steps',
        'description': 'Étapes de Collatz',
        'assertions': [
            'collatz_steps(6) == 8',
            'collatz_steps(1) == 0',
            'collatz_steps(27) == 111',
        ],
    },
    'power_of_two_fn': {
        'op': 'is_power_of_two',
        'description': 'Puissance de deux',
        'assertions': [
            'is_power_of_two(16) == 1',
            'is_power_of_two(12) == 0',
            'is_power_of_two(1) == 1',
        ],
    },
    'reverse_string_fn': {
        'op': 'reverse_string',
        'description': 'Inversion de chaîne',
        'assertions': [
            'reverse_string("abc") == "cba"',
            'reverse_string("") == ""',
            'reverse_string("kayak") == "kayak"',
        ],
    },
    'palindrome_string_fn': {
        'op': 'is_palindrome',
        'description': 'Chaîne palindrome',
        'assertions': [
            'is_palindrome("radar") == 1',
            'is_palindrome("hello") == 0',
            'is_palindrome("A man a plan a canal Panama") == 1',
        ],
    },
    'vowels_fn': {
        'op': 'count_vowels',
        'description': 'Nombre de voyelles',
        'assertions': [
            'count_vowels("hello") == 2',
            'count_vowels("AEIOU") == 5',
            'count_vowels("xyz") == 1',
        ],
    },
    'unique_fn': {
        'op': 'unique_items',
        'description': 'Éléments uniques',
        'assertions': [
            'unique_items([1, 2, 2, 3, 3, 3]) == [1, 2, 3]',
            'unique_items([]) == []',
            'unique_items([7]) == [7]',
        ],
    },
    'running_sum_fn': {
        'op': 'running_sum',
        'description': 'Somme cumulée',
        'assertions': [
            'running_sum([1, 2, 3]) == [1, 3, 6]',
            'running_sum([]) == []',
            'running_sum([5, -2, 3]) == [5, 3, 6]',
        ],
    },
    'balanced_fn': {
        'op': 'is_balanced',
        'description': 'Parenthèses équilibrées',
        'assertions': [
            'is_balanced("(())") == 1',
            'is_balanced("(()") == 0',
            'is_balanced("({[]})") == 1',
        ],
    },
    'flip_case_fn': {
        'op': 'flip_case',
        'description': 'Inversion de casse',
        'assertions': [
            'flip_case("Hello") == "hELLO"',
            'flip_case("123") == "123"',
            'flip_case("AbC") == "aBc"',
        ],
    },
    'most_frequent_fn': {
        'op': 'most_frequent',
        'description': 'Élément le plus fréquent',
        'assertions': [
            'most_frequent([1, 2, 2, 3]) == 2',
            'most_frequent([1]) == 1',
            'most_frequent([5, 5, 1, 5]) == 5',
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# LA BIBLIOTHÈQUE
# ═══════════════════════════════════════════════════════════════════════════════

class WaveAlgorithmLibrary:
    """
    Bibliothèque d'algorithmes harmoniques — génération multi-langage
    et vérification par exécution.

    Usage :
        lib = WaveAlgorithmLibrary()
        lib.generate('factorial', 'python')   # code Python
        lib.generate('factorial', 'js')       # code JavaScript
        lib.verify_all()                      # exécute et vérifie chaque op
    """

    def __init__(self):
        self.library: Dict[str, FunctionDef] = ALGORITHM_LIBRARY

    def list_ops(self) -> List[str]:
        """Liste les opérations disponibles."""
        return sorted(self.library.keys())

    def has(self, op: str) -> bool:
        return op in self.library

    def program_for(self, op: str) -> Program:
        """
        Programme harmonique complet : définition de la fonction
        + appel sur une entrée générique.

        Returns:
            Program avec FunctionDef + Assign + Return
        """
        fn = self.library[op]
        return Program([
            fn,
            Assign("entree", LST()),
            Assign("resultat", FunctionCall(op, [Var("entree")])),
            Return(Var("resultat")),
        ])

    def generate(self, op: str, lang: str = 'python') -> str:
        """
        Génère le code de la fonction dans la langue demandée.

        Args:
            op: nom de l'opération (ex: 'factorial')
            lang: 'python', 'javascript'/'js', 'typescript'/'ts'

        Returns:
            code source de la fonction
        """
        if op not in self.library:
            return f"# Opération inconnue: {op}"
        fn = self.library[op]
        prog = Program([fn])
        target = {'js': 'javascript', 'ts': 'typescript'}.get(lang, lang)
        if target == 'python':
            return emit_python(prog, include_wave_lang=False,
                               include_holograms=False)
        if target == 'javascript':
            return emit_javascript(prog)
        if target == 'typescript':
            return emit_typescript(prog)
        raise ValueError(f"Cible inconnue: {lang}")

    def generate_all(self, lang: str = 'python') -> Dict[str, str]:
        """Génère toutes les opérations dans une langue."""
        return {op: self.generate(op, lang) for op in self.library}

    # ── Vérification par exécution ──

    def verify(self, op: str) -> Tuple[bool, object, object]:
        """
        Vérifie une opération : convertit en Python, l'exécute sur un
        cas de test, compare au résultat attendu.

        Returns:
            (ok, résultat_obtenu, résultat_attendu)
        """
        if op not in self.library and op not in STRING_OPS:
            return False, None, None
        if op not in TEST_CASES:
            return False, None, None

        # Opérations strings → vérification via leur chemin propre
        if op in STRING_OPS:
            return self.verify_string_op(op)

        args, expected = TEST_CASES[op]
        fn = self.library[op]

        # Exécuter TOUTES les fonctions (les appels croisés comme lcm→gcd
        # ont besoin des autres fonctions dans l'env)
        from wave_compiler import WaveCompiler
        compiler = WaveCompiler(dim=64)
        env = compiler.execute(Program(list(self.library.values())))
        fn_obj = env.get(op)
        if not callable(fn_obj):
            return False, None, expected

        try:
            result = float(fn_obj(*args))
            ok = abs(result - float(expected)) < 1e-6
            return ok, result, float(expected)
        except Exception as e:
            return False, f"erreur: {e}", expected

    def verify_all(self) -> Dict[str, Tuple[bool, object, object]]:
        """Vérifie toutes les opérations testables."""
        return {op: self.verify(op) for op in sorted(self.library)
                if op in TEST_CASES}

    # ── Opérations strings (RawCode python) ──

    def is_string_op(self, op: str) -> bool:
        return op in STRING_OPS

    def generate_string_op(self, op: str) -> str:
        """Retourne le code Python de l'opération string."""
        return STRING_OPS.get(op, f"# Opération inconnue: {op}")

    def verify_string_op(self, op: str) -> Tuple[bool, object, object]:
        """Exécute le code de l'opération string et vérifie le cas de test."""
        if op not in STRING_OPS:
            return False, None, None
        code = STRING_OPS[op]
        ns: dict = {}
        try:
            exec(code, ns)
            fn = ns.get(op)
            if not callable(fn):
                return False, None, None
            # Cas de test par opération
            cases = {
                'reverse_string': (("abc",), "cba"),
                'is_palindrome': (("radar",), 1),
                'count_vowels': (("hello",), 2),
                'uppercase': (("abc",), "ABC"),
                'count_occurrences': (("hello", "l"), 2),
                'unique_items': (([1, 2, 2, 3],), [1, 2, 3]),
                'running_sum': (([1, 2, 3],), [1, 3, 6]),
                'flip_case': (("Hello",), "hELLO"),
                'is_balanced': (("(())",), 1),
                'most_frequent': (([1, 2, 2, 3],), 2),
                'remove_duplicates': (([1, 2, 2, 3],), [1, 2, 3]),
                'median': (([3, 1, 5],), 3.0),  # liste NON triée
            }
            if op not in cases:
                return False, None, None
            args, expected = cases[op]
            got = fn(*args)
            ok = got == expected
            return ok, got, expected
        except Exception as e:
            return False, f"erreur: {e}", None

    # ── HumanEval-style : vérification par assertions exécutées ──

    def verify_humaneval(self, problem_name: str = None) -> Dict:
        """
        Vérifie les problèmes style HumanEval par ASSERTIONS EXÉCUTÉES.

        Pour chaque problème : génère le code Python de l'opération,
        exécute les assertions dans un namespace isolé.

        Args:
            problem_name: nom du problème (None = tous)

        Returns:
            dict {problem_name: (ok, nb_assertions_passées, total)}
        """
        names = ([problem_name] if problem_name
                 else list(HUMANEVAL_PROBLEMS.keys()))
        results: Dict[str, Tuple[bool, int, int]] = {}

        for name in names:
            prob = HUMANEVAL_PROBLEMS.get(name)
            if not prob:
                results[name] = (False, 0, 0)
                continue
            op = prob['op']

            # Code Python de l'opération (AST converti ou RawCode)
            if self.is_string_op(op):
                code = self.generate_string_op(op)
            elif op in self.library:
                code = self.generate(op, 'python')
            else:
                results[name] = (False, 0, 0)
                continue

            ns: dict = {}
            try:
                exec(code, ns)
            except Exception:
                results[name] = (False, 0, len(prob['assertions']))
                continue

            passed = 0
            for assertion in prob['assertions']:
                try:
                    if eval(assertion, ns):
                        passed += 1
                except Exception:
                    pass

            total = len(prob['assertions'])
            results[name] = (passed == total, passed, total)

        return results

    def humaneval_stats(self) -> Dict:
        """Statistiques du benchmark HumanEval-style."""
        results = self.verify_humaneval()
        passed = sum(1 for ok, p, t in results.values() if ok)
        total = len(results)
        assertions_ok = sum(p for ok, p, t in results.values())
        assertions_total = sum(t for ok, p, t in results.values())
        return {
            'problems': total,
            'passed': passed,
            'score': 100.0 * passed / total if total else 0.0,
            'assertions': f"{assertions_ok}/{assertions_total}",
        }

    @property
    def stats(self) -> dict:
        """Statistiques de la bibliothèque."""
        return {
            'ops': len(self.library) + len(STRING_OPS),
            'ast_ops': len(self.library),
            'string_ops': len(STRING_OPS),
            'tested': len(TEST_CASES),
            'humaneval_problems': len(HUMANEVAL_PROBLEMS),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 65)
    print("  🌊 WAVE ALGORITHMS — Bibliothèque harmonique multi-langage")
    print("=" * 65)

    lib = WaveAlgorithmLibrary()
    print(f"\n  {len(lib.list_ops())} opérations: {', '.join(lib.list_ops())}")
    print(f"  {lib.stats}")

    # Exemples de génération
    for op in ['factorial', 'binary_search', 'gcd']:
        print(f"\n── {op} ──")
        print("  PYTHON:")
        for line in lib.generate(op, 'python').split('\n'):
            print(f"    │ {line}")
        print("  JAVASCRIPT:")
        for line in lib.generate(op, 'js').split('\n'):
            print(f"    │ {line}")

    # Vérification par exécution
    print("\n── VÉRIFICATION PAR EXÉCUTION ──")
    results = lib.verify_all()
    passed = sum(1 for ok, got, exp in results.values() if ok)
    for op, (ok, got, exp) in results.items():
        mark = '✅' if ok else '❌'
        print(f"  {mark} {op:<22} → {got} (attendu: {exp})")
    print(f"\n  {passed}/{len(results)} opérations vérifiées")

    print("\n" + "=" * 65)
    print("  ✅ Wave Algorithms — Bibliothèque fonctionnelle.")
    print("=" * 65)
