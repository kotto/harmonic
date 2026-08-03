"""
🌊 Benchmark GSM8K — 1319 problèmes officiels
===============================================

Mesure notre moteur contre le dataset officiel GSM8K (OpenAI, MIT).
Chaque problème : énoncé anglais + réponse (#### N).

Le score est calculé par correspondance exacte de la valeur finale.

Usage :
    python benchmark_gsm8k.py [--sample N] [--quiet]
"""

from __future__ import annotations

import sys
import os
import json
import time
import re
from typing import Dict, List, Tuple, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', '..', '..', '..'))  # engine root

from wave_word_problems import WaveWordProblemEngine
from wave_code_generator import WaveCodeGenerator


def load_gsm8k(path: str = None) -> List[Dict]:
    """Charge les problèmes GSM8K."""
    if path is None:
        _d = os.path.dirname
        root = _d(os.path.abspath(__file__))  # engine/ → data/benchmarks/
        path = os.path.join(root, 'data', 'benchmarks', 'gsm8k_test.jsonl')
    with open(path, encoding='utf-8') as f:
        return [json.loads(l) for l in f]


def extract_answer(answer_text: str) -> Optional[float]:
    """Extrait la valeur finale (#### N) d'une réponse GSM8K."""
    m = re.search(r'####\s*(-?\d+(?:[.,]\d+)?)', answer_text)
    if m:
        return float(m.group(1).replace(',', '.'))
    # Fallback : dernier nombre de la chaîne
    nums = re.findall(r'-?\d+(?:[.,]\d+)?', answer_text)
    return float(nums[-1].replace(',', '.')) if nums else None


def run_gsm8k(sample: Optional[int] = None, verbose: bool = True) -> Dict:
    """Exécute le benchmark GSM8K."""
    problems = load_gsm8k()
    if sample:
        problems = problems[:sample]

    engine = WaveWordProblemEngine()
    gen = WaveCodeGenerator()

    passed, total = 0, 0
    results = []

    for p in problems:
        question = p['question']
        expected = extract_answer(p['answer'])
        if expected is None:
            continue

        # 1. Moteur multi-étapes
        r = engine.solve(question)
        if r is None:
            # 2. Fallback parseur math direct
            expr = gen._parse_math_expr(question)
            if expr is not None:
                from wave_ir import Program, Assign, Return, Var
                from wave_compiler import WaveCompiler
                env = WaveCompiler(dim=64).execute(
                    Program([Assign('resultat', expr), Return(Var('resultat'))]))
                val = env.get('resultat')
                got = float(val) if val is not None else None
            else:
                got = None
        else:
            got = r.result

        ok = got is not None and abs(got - expected) < 1e-6
        passed += ok
        total += 1

        if verbose and (not ok or total <= 3):
            mark = '✅' if ok else '❌'
            print(f"  {mark} {question[:70]:<72} → {got} (attendu: {expected})")

    return {
        'passed': passed,
        'total': total,
        'score': 100.0 * passed / total if total else 0.0,
        'n_total_dataset': len(problems),
    }


if __name__ == "__main__":
    print("=" * 65)
    print("  🌊 BENCHMARK GSM8K — 1319 problèmes officiels")
    print("=" * 65)

    verbose = '--quiet' not in sys.argv
    sample = None
    for arg in sys.argv:
        if arg.startswith('--sample='):
            sample = int(arg.split('=')[1])

    stats = run_gsm8k(sample=sample, verbose=verbose)
    print(f"\n  📊 GSM8K : {stats['passed']}/{stats['total']} "
          f"({stats['score']:.1f}%) — dataset: {stats['n_total_dataset']}")
    print("=" * 65)
