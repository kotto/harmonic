"""
🧪 test_arena.py — Validation LM Arena (7 catégories)
========================================================
Teste le modèle Harmoniq sur les 7 catégories du Frontend Code Arena
et produit un rapport de performance.

Usage : python test_arena.py
"""

import sys, time, json
from pathlib import Path

_ENGINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ENGINE))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from model import HarmoniqModel

# ════════════════════════════════════════════════════════════════
# 7 CATÉGORIES ARENA (Frontend Code Arena)
# ════════════════════════════════════════════════════════════════

TESTS = {
    "Brand & Marketing": [
        ("landing page hero section with CTA", "hero"),
        ("pricing table with 3 tiers", "pricing"),
        ("testimonial card component", "testimonial"),
        ("newsletter signup form", "form"),
        ("footer with social links", "footer"),
    ],
    "Reference-Based Design": [
        ("recreate this dashboard layout", "dashboard"),
        ("clone the twitter feed UI", "feed"),
        ("spotify music player interface", "player"),
    ],
    "Data & Visualization": [
        ("bar chart showing sales data", "chart"),
        ("line graph for monthly revenue", "graph"),
        ("pie chart of market share", "pie"),
        ("SQL query for top customers", "select"),
        ("python data processing pipeline", "python"),
    ],
    "Content & Text": [
        ("blog post layout with author bio", "blog"),
        ("documentation page with sidebar nav", "docs"),
        ("markdown renderer component", "markdown"),
    ],
    "Interactive & State": [
        ("multi-step form with validation", "form"),
        ("drag and drop file upload", "drag"),
        ("real-time search with debounce", "search"),
        ("shopping cart with quantity", "cart"),
    ],
    "Games & Simulation": [
        ("tic tac toe game", "game"),
        ("snake game canvas", "canvas"),
        ("particle animation system", "animation"),
    ],
    "Advanced UI": [
        ("infinite scroll list", "scroll"),
        ("virtualized table with 10000 rows", "table"),
        ("dark mode toggle with persistence", "dark"),
        ("responsive masonry grid", "grid"),
        ("accessibility ARIA compliant modal", "modal"),
    ],
}

model = HarmoniqModel()

print("═" * 65)
print("  🧪 LM ARENA VALIDATION — 7 catégories")
print("═" * 65)

results = {}
total_ok = 0
total_tests = 0

for category, questions in TESTS.items():
    cat_ok = 0
    print(f"\n  [{category}]")
    for q, keyword in questions:
        t0 = time.time()
        response = model.generate(q)
        dt = (time.time() - t0) * 1000
        # Vérifier que la réponse n'est pas vide
        ok = bool(response) and len(str(response)) > 20
        if ok:
            cat_ok += 1
            total_ok += 1
        total_tests += 1
        status = "✅" if ok else "❌"
        print(f"    {status} {q[:50]:<50} ({dt:.0f}ms)")

    score = cat_ok / len(questions)
    results[category] = {'ok': cat_ok, 'total': len(questions), 'score': score}
    print(f"    ── {cat_ok}/{len(questions)} = {score:.0%}")

print(f"\n{'═'*65}")
print(f"  RÉSULTATS")
print(f"{'═'*65}")
for cat, r in results.items():
    bar = '█' * int(r['score'] * 20)
    print(f"  {cat:<28} {r['ok']:>2}/{r['total']:<2} = {r['score']:>5.0%} {bar}")
print(f"  {'─'*40}")
print(f"  TOTAL                      {total_ok:>2}/{total_tests:<2} = {total_ok/total_tests:>5.0%}")
print(f"\n  ✅ Validation terminée.")

# Sauvegarder
with open('arena_test_results.json', 'w') as f:
    json.dump({
        'results': results,
        'total': f"{total_ok}/{total_tests}",
        'score': total_ok / total_tests,
        'model': model.info(),
    }, f, indent=2)
print(f"  📊 Rapport: arena_test_results.json")
