"""
🌊 Benchmark Harmonique — Le harness canonique (150 questions)
================================================================

Le benchmark unique qui remplace les 10 harnesses disparates :
  50 maths + 50 code + 50 raisonnement, vérifiés PAR EXÉCUTION.

| Domaine | Source | Vérification |
|---------|--------|--------------|
| Maths (50) | expressions arithmétiques FR générées | résultat exact (pipeline math) |
| Code (50) | 26 opérations du registre × cas de test | exécution du code converti |
| Raisonnement (50) | benchmark_raisonnement (30) + 20 variantes | mot-clé dans la conclusion |

Usage :
    python benchmark_harmonique.py
"""

from __future__ import annotations

import sys
import os
import time
import random
from typing import List, Dict, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wave_pipeline import WavePipeline
from wave_algorithms import WaveAlgorithmLibrary, TEST_CASES
from wave_reasoning_v2 import WaveReasoningEngine
from benchmark_raisonnement import (RAISONNEMENT_TESTS, ABDUCTION_HYPOTHESES)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. MATHS — 50 expressions générées (déterministes, seed fixe)
# ═══════════════════════════════════════════════════════════════════════════════

def _build_math_questions(n: int = 50) -> List[Tuple[str, float]]:
    """Génère n questions mathématiques avec leur réponse exacte."""
    rng = random.Random(42)  # déterministe
    questions: List[Tuple[str, float]] = []

    templates = [
        # (question, calcul)
        lambda a, b: (f"Calcule {a} plus {b}", a + b),
        lambda a, b: (f"Calcule {a} moins {b}", a - b),
        lambda a, b: (f"Calcule {a} fois {b}", a * b),
        lambda a, b: (f"combien font {a} divisé par {b}", a / b),
        lambda a, b: (f"Calcule {a} puissance {b}", a ** b),
        lambda a: (f"racine carrée de {a * a}", float(a)),
        lambda a: (f"carré de {a}", float(a * a)),
        lambda a, b: (f"combien font {a}% de {b}", a / 100 * b),
        lambda a: (f"valeur absolue de {-a}", float(a)),
        lambda a: (f"la moitié de {a * 2}", float(a)),
    ]

    while len(questions) < n:
        a = rng.randint(2, 20)
        b = rng.randint(2, 12)
        tpl = templates[len(questions) % len(templates)]
        try:
            # Les templates unaires ignorent b
            try:
                q, answer = tpl(a, b)
            except TypeError:
                q, answer = tpl(a)
            if abs(answer) < 1e9:  # garder des réponses raisonnables
                questions.append((q, float(answer)))
        except ZeroDivisionError:
            continue
    return questions[:n]


# ═══════════════════════════════════════════════════════════════════════════════
# 2. CODE — 50 tests (26 opérations du registre + 24 variantes)
# ═══════════════════════════════════════════════════════════════════════════════

def _build_code_tests() -> List[Tuple[str, Tuple, object]]:
    """26 cas de test du registre + 24 variantes paramétrées."""
    tests: List[Tuple[str, Tuple, object]] = []
    for op, (args, expected) in TEST_CASES.items():
        tests.append((op, args, expected))

    # 24 variantes
    variants = [
        ('sum', ([5.0, 10.0, 15.0],), 30.0),
        ('sum', ([1.0, 1.0, 1.0, 1.0],), 4.0),
        ('max', ([1.0, 9.0, 3.0],), 9.0),
        ('min', ([8.0, 2.0, 5.0],), 2.0),
        ('average', ([10.0, 20.0],), 15.0),
        ('count', ([1.0, 2.0, 3.0, 4.0, 5.0],), 5.0),
        ('factorial', ((6.0,),), 720.0),
        ('factorial', ((3.0,),), 6.0),
        ('fibonacci', ((10.0,),), 55.0),
        ('gcd', ((48.0, 36.0),), 12.0),
        ('lcm', ((3.0, 5.0),), 15.0),
        ('power', ((3.0, 3.0),), 27.0),
        ('sqrt', ((144.0,),), 12.0),
        ('is_prime', ((11.0,),), 1.0),
        ('is_prime', ((15.0,),), 0.0),
        ('is_even', ((7.0,),), 0.0),
        ('clamp', ((5.0, 0.0, 10.0),), 5.0),
        ('clamp', ((-5.0, 0.0, 10.0),), 0.0),
        ('celsius_to_fahrenheit', ((100.0,),), 212.0),
        ('fahrenheit_to_celsius', ((212.0,),), 100.0),
        ('linear_search', (([4.0, 8.0, 15.0], 8.0),), 1.0),
        ('binary_search', (([2.0, 4.0, 6.0, 8.0], 6.0),), 2.0),
        ('contains', (([1.0, 5.0, 9.0], 9.0),), 1.0),
        ('sum_of_squares', (([1.0, 2.0],),), 5.0),
    ]
    tests.extend(variants)
    return tests[:50]


# ═══════════════════════════════════════════════════════════════════════════════
# 3. RAISONNEMENT — 50 (30 du benchmark + 20 variantes)
# ═══════════════════════════════════════════════════════════════════════════════

def _build_reasoning_tests() -> List[Tuple[List[str], str, str, str]]:
    """Les 30 questions du benchmark + 20 variantes."""
    tests = list(RAISONNEMENT_TESTS)

    variants = [
        (["Einstein est un scientifique", "Tous les scientifiques sont curieux"],
         "", "syllogisme", "curieux"),
        (["Bella est une vache", "Toutes les vaches donnent du lait"],
         "", "syllogisme", "lait"),
        (["Si on chauffe l'eau alors elle bout", "on chauffe l'eau"],
         "", "modus_ponens", "bout"),
        (["Si on ouvre la porte alors le chien sort", "on ouvre la porte"],
         "", "modus_ponens", "sort"),
        (["Le père de Marc est Jean", "Jean est le frère de Paul"],
         "", "transitivite", "paul"),
        (["Paris est en France", "la France est en Europe"],
         "", "transitivite", "europe"),
        (["le jour est lumineux", "le jour n'est pas lumineux"],
         "", "contradiction", ""),
        (["le feu est chaud", "le feu n'est pas chaud"],
         "", "contradiction", ""),
        (["la pomme 1 est rouge", "la pomme 2 est rouge", "la pomme 3 est rouge"],
         "", "induction", "pomme"),
        (["l'abeille 1 butine", "l'abeille 2 butine", "l'abeille 3 butine"],
         "", "induction", "abeille"),
        (["les vitres sont givrées"], "Pourquoi les vitres sont-elles givrées ?",
         "abduction", "gel"),
        (["la batterie est vide"], "Pourquoi la batterie est-elle vide ?",
         "abduction", "utilis"),
        (["il y a des traces de pas dans le sable"],
         "Pourquoi y a-t-il des traces dans le sable ?",
         "abduction", "march"),
        (["la plante est fanée"], "Pourquoi la plante est-elle fanée ?",
         "abduction", "eau"),
        (["clé est à serrure", "téléphone est à appeler"],
         "clé est à serrure ce que téléphone est à ?", "analogie", "appeler"),
        (["plume est à écrivain", "pinceau est à peintre"],
         "plume est à écrivain ce que pinceau est à ?", "analogie", "peintre"),
        (["Max est un lion", "Tous les lions ont une crinière"],
         "", "syllogisme", "crinière"),
        (["Si on tire sur la corde alors la cloche sonne", "on tire sur la corde"],
         "", "modus_ponens", "sonne"),
        (["L'école est après la maison", "la maison est après le parc"],
         "", "transitivite", "parc"),
        (["le sel est soluble", "le sel n'est pas soluble"],
         "", "contradiction", ""),
    ]
    tests.extend(variants)
    return tests[:50]


# ═══════════════════════════════════════════════════════════════════════════════
# EXÉCUTION
# ═══════════════════════════════════════════════════════════════════════════════

def run_maths(questions: List[Tuple[str, float]], verbose: bool) -> Tuple[int, int, float]:
    """Exécute les 50 questions maths via le pipeline harmonique."""
    pipeline = WavePipeline()
    passed, total, t0 = 0, 0, time.perf_counter()
    for q, expected in questions:
        r = pipeline.run(q)
        got = r.env.get('resultat')
        ok = (got is not None and
              abs(float(got) - expected) < 1e-6)
        passed += ok
        total += 1
        if verbose:
            mark = '✅' if ok else '❌'
            print(f"  {mark} {q:<38} → {got} (attendu: {expected})")
    return passed, total, (time.perf_counter() - t0) * 1000


def run_code(tests: List[Tuple[str, Tuple, object]], verbose: bool) -> Tuple[int, int, float]:
    """Exécute les 50 tests code via la bibliothèque d'algorithmes."""
    lib = WaveAlgorithmLibrary()
    passed, total, t0 = 0, 0, time.perf_counter()
    for op, args, expected in tests:
        ok, got, exp = lib.verify(op) if op in TEST_CASES else (False, None, None)
        if op not in TEST_CASES:
            # Variante : exécution directe avec les args de la variante
            from wave_compiler import WaveCompiler
            from wave_ir import Program
            compiler = WaveCompiler(dim=64)
            env = compiler.execute(Program(list(lib.library.values())))
            fn = env.get(op)
            if callable(fn):
                try:
                    got = float(fn(*args))
                    ok = abs(got - float(expected)) < 1e-6
                except Exception:
                    ok = False
        passed += ok
        total += 1
        if verbose:
            mark = '✅' if ok else '❌'
            print(f"  {mark} {op:<22} {str(args)[:30]:<32} → {got} (attendu: {expected})")
    return passed, total, (time.perf_counter() - t0) * 1000


def run_reasoning(tests: List[Tuple[List[str], str, str, str]],
                  verbose: bool) -> Tuple[int, int, float]:
    """Exécute les 50 questions raisonnement."""
    engine = WaveReasoningEngine()
    passed, total, t0 = 0, 0, time.perf_counter()
    for premises, question, etype, keyword in tests:
        if etype == 'abduction':
            hypotheses = ABDUCTION_HYPOTHESES.get(premises[0], [])
            if not hypotheses:
                hypotheses = ["une cause naturelle s'est produite",
                              "quelqu'un est intervenu"]
            r = engine.abduction(premises[0], hypotheses)
        else:
            r = engine.solve(premises, question)

        ok = False
        if etype == 'abduction':
            ok = keyword in r.conclusion.lower()
        elif etype == 'analogie':
            ok = r.method == 'analogie'
        elif etype == 'contradiction':
            ok = r.method == 'contradiction'
        elif etype == 'induction':
            ok = r.method == 'induction' and keyword in r.conclusion.lower()
        else:
            ok = (keyword in r.conclusion.lower() and
                  r.method != 'superposition')

        passed += ok
        total += 1
        if verbose:
            mark = '✅' if ok else '❌'
            print(f"  {mark} [{etype:<13}] {premises[0][:32]:<34} "
                  f"→ {r.conclusion[:40]}")
    return passed, total, (time.perf_counter() - t0) * 1000


if __name__ == "__main__":
    print("=" * 65)
    print("  🌊 BENCHMARK HARMONIQUE — 150 questions (maths + code + raisonnement)")
    print("=" * 65)

    verbose = '--quiet' not in sys.argv

    # Maths
    print("\n── 1. MATHS (50) ──")
    math_questions = _build_math_questions(50)
    m_passed, m_total, m_time = run_maths(math_questions, verbose)

    # Code
    print("\n── 2. CODE (50) ──")
    code_tests = _build_code_tests()
    c_passed, c_total, c_time = run_code(code_tests, verbose)

    # Raisonnement
    print("\n── 3. RAISONNEMENT (50) ──")
    reason_tests = _build_reasoning_tests()
    r_passed, r_total, r_time = run_reasoning(reason_tests, verbose)

    # Bilan
    total_passed = m_passed + c_passed + r_passed
    total_all = m_total + c_total + r_total
    total_time = m_time + c_time + r_time

    print(f"\n{'═' * 65}")
    print(f"  📊 BILAN FINAL")
    print(f"  Maths       : {m_passed}/{m_total} ({100*m_passed/m_total:.1f}%) — {m_time:.0f} ms")
    print(f"  Code        : {c_passed}/{c_total} ({100*c_passed/c_total:.1f}%) — {c_time:.0f} ms")
    print(f"  Raisonnement: {r_passed}/{r_total} ({100*r_passed/r_total:.1f}%) — {r_time:.0f} ms")
    print(f"  GLOBAL      : {total_passed}/{total_all} ({100*total_passed/total_all:.1f}%) — {total_time:.0f} ms")
    print(f"{'═' * 65}")
