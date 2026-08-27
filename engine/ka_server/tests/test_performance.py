"""
⚡ ka_server — Tests de Performance (Benchmarks)
=================================================
Mesure les performances réelles du serveur KA :
  - PromptComprehendor : classification d'intention (10 intents)
  - memory_first : rappel holographique
  - Surface grammar : phraséologie naturelle
  - Bout-en-bout : requête → réponse complète

Usage :
    python ka_server/tests/test_performance.py
"""

import sys
import time
import statistics
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'services'))
sys.path.insert(0, 'vital-ka/core/python')

import os
_NOW = time.strftime('_%Y%m%d_%H%M%S')
_RAW = os.environ.get('KA_SAAS_WAVE_DIR', '')
os.environ['KA_SAAS_WAVE_DIR'] = _RAW or str(Path(__file__).parent.parent / f'data_perf{_NOW}')
os.makedirs(os.environ['KA_SAAS_WAVE_DIR'], exist_ok=True)


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def bench(label: str, fn, n: int = 200):
    """Exécute fn n fois, retourne dict de métriques."""
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t0) * 1000)
    times.sort()
    p99 = times[int(n * 0.99)]
    return {
        'label': label,
        'avg_ms': round(statistics.mean(times), 3),
        'p99_ms': round(p99, 3),
        'qps': round(1000 / statistics.mean(times), 0),
    }


def print_bench(r):
    print(f"  {r['label']:<50s} avg={r['avg_ms']:>8.3f}ms  "
          f"p99={r['p99_ms']:>8.3f}ms  ({r['qps']:>8.0f} q/s)")


# ═══════════════════════════════════════════════════════════
# 1. PROMPT COMPREHENDOR
# ═══════════════════════════════════════════════════════════

def bench_prompt_comprehendor():
    print("\n── 1. PromptComprehendor (10 intentions) ──")

    from ka_server.services.prompt_comprehendor import PromptComprehendor
    pc = PromptComprehendor(use_semantic=False)

    queries = [
        ("compresse mon téléphone", 'storage_action'),
        ("appelle Maman", 'action_command'),
        ("15 + 3 fois 7", 'arithmetic'),
        ("spécialise-moi sur la biologie", 'specialize_request'),
        ("retiens que Paris est la capitale", 'learning'),
        ("compare le café et le thé", 'comparison'),
        ("écris un poème sur la mer", 'generation'),
        ("bonjour KA", 'greeting'),
        ("c'est quoi un hologramme", 'factual_question'),
        ("qui es-tu", 'identity_question'),
    ]

    print("  Vérification classification (10 requêtes) :")
    for q, expected in queries:
        f = pc.comprehend(q)
        ok = "✅" if f.intent == expected else "❌"
        print(f"  {ok} {expected:<20s} ← {q}  (conf={f.confidence:.3f})")

    # Latence
    r = bench("classifier un prompt", lambda: pc.comprehend("compresse mon téléphone"))
    print_bench(r)


# ═══════════════════════════════════════════════════════════
# 2. MEMORY FIRST (réponses naturelles via surface_grammar)
# ═══════════════════════════════════════════════════════════

def bench_memory_first():
    print("\n── 2. Memory-First (rappel + phraséologie) ──")

    from ka_server.services.memory_first import store_fact, ask, stats

    # Semer quelques faits
    facts = [
        ('lumiere', 'est une', 'onde electromagnetique', 'cours de physique'),
        ('soleil', 'est', 'une etoile', 'astronomie'),
        ('phi', 'est', 'nombre d or', 'theorie harmonique'),
    ]
    for s, r, o, src in facts:
        store_fact(s, r, o, src)

    # Vérifier la phraséologie naturelle
    print("  Phraséologie mémoire-first :")
    for q in [
        "Qu'est-ce que la lumiere ?",
        "Qu'est-ce que le soleil ?",
        "Qu'est-ce que phi ?",
    ]:
        result = ask(q)
        if not result['refused']:
            print(f"  ✅ {q[:45]:<45s} → {result['answer']}")
        else:
            print(f"  ❌ {q[:45]:<45s} → refusé ({result.get('reason','')})")

    # Latence
    r = bench("rappel + phrase fact (3 faits)", lambda: ask("Qu'est-ce que la lumiere ?"))
    print_bench(r)

    st = stats()
    print(f"  Faits: {st['facts']}, Vocabulaire: {st['vocabulary']}")


# ═══════════════════════════════════════════════════════════
# 3. SURFACE GRAMMAR (phraséologie isolée)
# ═══════════════════════════════════════════════════════════

def bench_surface_grammar():
    print("\n── 3. Surface Grammar (phraséologie isolée) ──")

    from ka_server.services.phrase_engine import PhraseEngine
    pe = PhraseEngine()

    results = [
        bench("phrase_fact (verbe connu)",
              lambda: pe.phrase_fact('lumiere', 'est une', 'onde electromagnetique'), n=200),
        bench("phrase_fact (fallback triplet)",
              lambda: pe.phrase_fact('COVID-19', 'conduite', 'Isolement immédiat'), n=200),
        bench("prose (extraction triplet)",
              lambda: pe.prose("Paris est la capitale de la France"), n=200),
    ]
    for r in results:
        print_bench(r)

    # Empreinte mémoire des structures de surface
    st = pe.memory_stats
    print(f"  Structures apprises: {st['structures_apprises']}")


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    print("=" * 72)
    print("  ⚡ KA SERVER — Tests de Performance (consolidation V5)")
    print("=" * 72)

    t_start = time.perf_counter()

    try:
        bench_prompt_comprehendor()
    except Exception as e:
        print(f"\n  ❌ PromptComprehendor: {e}")

    try:
        bench_memory_first()
    except Exception as e:
        print(f"\n  ❌ Memory-First: {e}")

    try:
        bench_surface_grammar()
    except Exception as e:
        print(f"\n  ❌ Surface Grammar: {e}")

    elapsed = time.perf_counter() - t_start
    print(f"\n{'═'*72}")
    print(f"  Temps total : {elapsed:.1f} s")
    print(f"{'═'*72}")


if __name__ == '__main__':
    main()