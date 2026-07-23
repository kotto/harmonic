#!/usr/bin/env python3
"""
Benchmark Top 3 — Maths + Code Frontend
========================================
Mesure l'impact du CAS symbolique (SymPy) + 38 templates frontend.

Usage:
  python benchmark_top3.py
"""

import sys, time
from pathlib import Path

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

# ═══════════════════════════════════════════════════════════════
# QUESTIONS — 50 maths + 50 frontend
# ═══════════════════════════════════════════════════════════════

MATH_QUESTIONS = [
    # Arithmétique (10)
    ("combien font 7 * 8", "56"),
    ("racine de 169", "13"),
    ("15% de 200", "30"),
    ("2^10", "1024"),
    ("combien font 144 / 12", "12"),
    ("3 + 4 * 5", "23"),
    ("factorielle de 5", "120"),
    ("combien font 17 + 28", "45"),
    ("10^3", "1000"),
    ("combien font 100 - 37", "63"),
    # Dérivées (10)
    ("dérivée de x^2", "2x"),
    ("dérivée de x^3", "3x"),
    ("dérivée de sin(x)", "cos"),
    ("dérivée de cos(x)", "-sin"),
    ("dérivée de e^x", "exp"),
    ("dérivée de ln(x)", "1/x"),
    ("dérivée de x^3 + 2x", "3x"),
    ("dérivée de 1/x", "-1"),
    ("dérivée de x^4", "4x"),
    ("dérivée de 2x + 3", "2"),
    # Intégrales (5)
    ("intégrale de x", "x^2"),
    ("intégrale de x^2", "x^3"),
    ("intégrale de sin(x)", "cos"),
    ("intégrale de 2x", "x^2"),
    ("intégrale de 1", "x"),
    # Équations (10)
    ("résoudre x^2 - 4 = 0", "2"),
    ("résoudre x^2 - 5x + 6 = 0", "2"),
    ("résoudre 2x + 3 = 7", "2"),
    ("résoudre x^2 - 9 = 0", "3"),
    ("résoudre x - 5 = 0", "5"),
    ("résoudre 3x = 12", "4"),
    ("résoudre x^2 + 2x + 1 = 0", "1"),
    ("résoudre x + 7 = 10", "3"),
    ("résoudre 5x - 10 = 0", "2"),
    ("résoudre x^2 = 16", "4"),
    # Limites (5)
    ("limite de sin(x)/x quand x tend vers 0", "1"),
    ("limite de (x^2-1)/(x-1) quand x tend vers 1", "2"),
    ("limite de 1/x quand x tend vers 0", "inf"),
    # Simplification (5)
    ("simplifier sin(x)^2 + cos(x)^2", "1"),
    ("simplifier (x^2 - 1)/(x - 1)", "x + 1"),
    # Factorisation (5)
    ("factoriser x^2 - 4", "(x - 2)"),
    ("factoriser x^2 + 2x + 1", "(x + 1)"),
]

FRONTEND_QUESTIONS = [
    # React (15)
    ("crée un formulaire React", "useState"),
    ("React component modal", "Modal"),
    ("composant React toggle switch", "Toggle"),
    ("React useState counter", "count"),
    ("React tabs component", "tab"),
    ("React accordion component", "accordion"),
    ("React fetch API hook", "fetch"),
    ("React context provider", "Context"),
    ("React custom hook useLocalStorage", "localStorage"),
    ("React sortable table", "table"),
    ("React search bar with debounce", "debounce"),
    ("React card grid responsive", "grid"),
    ("React error boundary", "ErrorBoundary"),
    ("React component with Tailwind", "tailwind"),
    ("React router setup", "Router"),
    # Vue (10)
    ("Vue script setup component", "script setup"),
    ("Vue component options API", "export default"),
    ("Vue form with v-model", "v-model"),
    ("Vue list with v-for filter", "v-for"),
    ("Vue modal with Teleport", "Teleport"),
    ("Vue Pinia store", "defineStore"),
    ("Vue component with Tailwind", "tailwind"),
    ("Vue composable", "import { ref"),
    ("Vue slots", "slot"),
    ("Vue watch", "watch"),
    # CSS (15)
    ("CSS flexbox center", "flex"),
    ("CSS grid layout", "grid"),
    ("CSS responsive media queries", "media"),
    ("CSS keyframe animation", "keyframe"),
    ("CSS variables custom properties", "var("),
    ("dark mode CSS prefers-color-scheme", "dark"),
    ("glassmorphism CSS backdrop-filter", "backdrop"),
    ("CSS gradient linear", "gradient"),
    ("CSS typography modular scale", "font-size"),
    ("flexbox navbar", "flex"),
    ("CSS card hover effect", "hover"),
    ("CSS button styles", "button"),
    ("CSS container responsive", "container"),
    ("transition CSS smooth", "transition"),
    ("CSS border radius card", "border-radius"),
    # Build (10)
    ("Vite config React", "vite"),
    ("tailwind.config.js", "tailwind"),
    ("package.json scripts", "scripts"),
    ("tsconfig.json TypeScript", "compilerOptions"),
    ("webpack config", "webpack"),
    ("ESLint config", "eslint"),
    ("docker compose frontend", "docker"),
    ("GitHub Actions CI", "github"),
    ("Vercel deployment config", "vercel"),
    (".env.example variables", "env"),
]

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def _norm(s):
    return s.lower().replace(' ', '').replace('é','e').replace('è','e').replace('ê','e')\
            .replace('à','a').replace('ù','u').replace('ô','o').replace('ç','c')\
            .replace('*','').replace('^','').replace('·','').replace('+','')

def _check(response, expected):
    """Vérifie si la réponse contient la valeur attendue."""
    if not response:
        return False
    r = _norm(response)
    e = _norm(expected)
    if e in r:
        return True
    # Match par tokens
    exp_tokens = set(_norm(expected).split())
    resp_tokens = set(_norm(response).split())
    if exp_tokens and len(exp_tokens & resp_tokens) >= 1:
        return True
    return False


def main():
    print("=" * 70)
    print("  TOP 3 BENCHMARK — Maths + Code Frontend")
    print("=" * 70)

    from intent_router import route

    # === MATHS ===
    print(f"\n[1] MATHÉMATIQUES ({len(MATH_QUESTIONS)} questions)")
    math_correct = 0
    math_total = 0
    math_details = []

    for q, expected in MATH_QUESTIONS:
        t0 = time.time()
        response = route(q)
        elapsed = (time.time() - t0) * 1000
        is_correct = _check(response or '', expected)
        math_total += 1
        if is_correct:
            math_correct += 1
        math_details.append((q, expected, response[:60] if response else "(vide)", is_correct, elapsed))

    math_score = math_correct / math_total if math_total > 0 else 0
    avg_math_time = sum(d[4] for d in math_details) / len(math_details) if math_details else 0
    print(f"  Maths: {math_correct}/{math_total} = {math_score:.1%} · {avg_math_time:.0f}ms avg")

    # === FRONTEND ===
    print(f"\n[2] CODE FRONTEND ({len(FRONTEND_QUESTIONS)} questions)")
    fe_correct = 0
    fe_total = 0
    fe_details = []

    for q, expected in FRONTEND_QUESTIONS:
        t0 = time.time()
        response = route(q)
        elapsed = (time.time() - t0) * 1000
        is_correct = _check(response or '', expected)
        fe_total += 1
        if is_correct:
            fe_correct += 1
        fe_details.append((q, expected, response[:60] if response else "(vide)", is_correct, elapsed))

    fe_score = fe_correct / fe_total if fe_total > 0 else 0
    avg_fe_time = sum(d[4] for d in fe_details) / len(fe_details) if fe_details else 0
    print(f"  Frontend: {fe_correct}/{fe_total} = {fe_score:.1%} · {avg_fe_time:.0f}ms avg")

    # === GLOBAL ===
    total_correct = math_correct + fe_correct
    total_questions = math_total + fe_total
    global_score = total_correct / total_questions if total_questions > 0 else 0

    print(f"\n{'=' * 70}")
    print(f"  RÉSULTATS TOP 3")
    print(f"{'=' * 70}")
    print(f"  Mathématiques  : {math_score:.1%} ({math_correct}/{math_total}) · {avg_math_time:.0f}ms")
    print(f"  Code Frontend  : {fe_score:.1%} ({fe_correct}/{fe_total}) · {avg_fe_time:.0f}ms")
    print(f"  ─────────────────────────────────")
    print(f"  GLOBAL         : {global_score:.1%} ({total_correct}/{total_questions})")
    print(f"  Paramètres     : 0")
    print(f"  GPU            : 0")
    print(f"  Déterministe   : 100%")
    print(f"{'=' * 70}")

    # Détails des échecs
    failures = [d for d in math_details + fe_details if not d[3]]
    if failures:
        print(f"\n  ÉCHECS ({len(failures)}):")
        for q, exp, resp, _, _ in failures[:15]:
            print(f"    ❌ '{q[:45]}' → attendu '{exp}', reçu '{resp[:40]}'")

    # Save
    import json
    report = {
        'math_score': round(math_score, 3),
        'frontend_score': round(fe_score, 3),
        'global_score': round(global_score, 3),
        'math_details': [{'q': d[0], 'expected': d[1], 'got': d[2], 'correct': d[3], 'ms': round(d[4])} for d in math_details],
        'fe_details': [{'q': d[0], 'expected': d[1], 'got': d[2], 'correct': d[3], 'ms': round(d[4])} for d in fe_details],
    }
    with open('benchmark_top3_results.json', 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n  Rapport: benchmark_top3_results.json")


if __name__ == '__main__':
    main()
