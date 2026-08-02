"""
🏆 Benchmark Frontend Engine (reconstruit, autonome)
======================================================
Évalue la génération frontend : couverture, confiance, déterminisme,
variantes φ, fusion HRR, pages multi-sections.

Usage: python benchmark_frontend.py [--quick]
"""

import time, json, sys, hashlib
from pathlib import Path
from typing import List, Tuple, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code_generator import FrontendGenerator
from phi_flex import PhiFlex
from real_composers import HRRHtmlFusion, MultiSectionPage, ReferenceAnalyzer

QUICK_QUESTIONS = [
    'crée une landing page pour un café',
    'génère un dashboard avec graphiques',
    'crée une carte avec image et bouton',
    'fais un chat app avec messages',
    'génère un lecteur musique',
    'crée un thème sombre',
    'fais un jeux snake',
    'génère une frise chronologique',
]

FULL_QUESTIONS = QUICK_QUESTIONS + [
    'crée un navbar avec dropdown',
    'génère une palette de couleurs',
    'fais un témoignage client',
    'crée une galerie de photos',
    'génère un formulaire de contact',
    'crée une modale accessible',
    'génère une grille responsive',
    'fais un kanban avec drag and drop',
    'génère une météo avec forecast',
    'crée un accordéon FAQ',
    'génère un camembert',
    'crée une barre de progression',
    'génère un carousel',
    'crée un éditeur de code',
    'génère un upload de fichier',
    'crée des particules animées',
]


def run_benchmark(quick: bool = False, n_runs: int = 2):
    gen = FrontendGenerator()
    pflex = PhiFlex()
    questions = QUICK_QUESTIONS if quick else FULL_QUESTIONS

    print("=" * 70)
    print(f"🏆 BENCHMARK FRONTEND ENGINE — {len(questions)} questions × {n_runs} runs")
    print(f"    Templates: {gen.template_count()} | Variantes φ: {pflex.stats()['total_variants']} "
          f"| Layouts: {pflex.stats()['total_layout_combinations']}")
    print("=" * 70)

    results = []
    total_ok = 0
    total_time = 0.0
    deterministic = True

    for i, q in enumerate(questions):
        outputs, times, confs = [], [], []
        for run in range(n_runs):
            t0 = time.perf_counter()
            r = gen.generate(q)
            elapsed = (time.perf_counter() - t0) * 1000
            times.append(elapsed)
            outputs.append(r.code)
            confs.append(r.confidence)
            if r.confidence >= 0.7:
                total_ok += 1

        avg_t = sum(times) / len(times)
        avg_c = sum(confs) / len(confs)
        det = all(o == outputs[0] for o in outputs[1:]) if n_runs > 1 else True
        deterministic = deterministic and det
        total_time += avg_t

        status = '✅' if avg_c >= 0.7 else '🟡' if avg_c >= 0.5 else '❌'
        print(f"  [{i+1:2d}/{len(questions)}] {status} {q[:45]:47s} → {r.intent.operation:16s} "
              f"conf={avg_c:.2f} {avg_t:.2f}ms {'det' if det else 'VAR'}")

        results.append({
            "question": q, "operation": r.intent.operation,
            "confidence": avg_c, "latency_ms": avg_t,
            "code_length": len(outputs[0]), "deterministic": det,
        })

    n_total = len(questions) * n_runs
    accuracy = total_ok / n_total
    avg_latency = total_time / len(questions)

    # Test variantes card (5 vraies structures)
    variants_ok = 0
    for v in ['default', 'horizontal', 'overlay', 'minimal', 'featured']:
        r = gen.generate_variant('crée une carte', v)
        if f'data-variant="{v}"' in r.code:
            variants_ok += 1

    # Test fusion HRR
    fusion = HRRHtmlFusion()
    fused, _ = fusion.fuse('card', 'form')
    fusion_ok = '<input' in fused and '<article' in fused

    # Test page multi-sections
    composer = MultiSectionPage()
    page, _ = composer.assemble('landing', seed='bench')
    page_ok = '<!DOCTYPE' in page and page.count('═══ Section') >= 5

    print(f"\n{'─' * 70}")
    print(f"📊 RÉSULTATS")
    print(f"{'─' * 70}")
    print(f"  Accuracy:          {accuracy:.1%} ({total_ok}/{n_total})")
    print(f"  Latence moyenne:   {avg_latency:.2f} ms")
    print(f"  Déterminisme:      {'✅ 100%' if deterministic else '❌'}")
    print(f"  Variantes card:    {variants_ok}/5 structures distinctes")
    print(f"  Fusion HRR:        {'✅ card+form fusionnés' if fusion_ok else '❌'}")
    print(f"  Page multi-section:{'✅ complète' if page_ok else '❌'} ({page.count(chr(0x2550) + chr(0x2550)) if False else page.count('═══ Section')} sections)")

    report = {
        "benchmark": "frontend_engine",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "templates": gen.template_count(),
        "questions": len(questions),
        "accuracy": accuracy,
        "avg_latency_ms": avg_latency,
        "deterministic": deterministic,
        "variants_distinct": variants_ok,
        "hrr_fusion": fusion_ok,
        "multi_section": page_ok,
        "results": results,
    }
    out = Path('data/benchmark_frontend_engine.json')
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"📊 Rapport: {out}")
    return report


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--quick', action='store_true')
    args = ap.parse_args()
    run_benchmark(quick=args.quick)
