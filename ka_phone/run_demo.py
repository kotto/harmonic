#!/usr/bin/env python3
"""Demo KA-Next : 6 questions dans 5 modes differents."""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

from ka_next_core import KANextEngine

engine = KANextEngine(use_llm=False)
engine.build(force=False)

if not engine.built:
    print("Pipeline non construit. Verifiez l'hologramme.")
    sys.exit(1)

questions = [
    ("Quelle est la capitale du Senegal ?", "factual"),
    ("Combien font 12 x 15 ?", "factual"),
    ("Pourquoi le ciel est-il bleu ?", "reason"),
    ("Imagine un monde ou les oceans sont en or ?", "creative"),
    ("Resume ce texte : Le soleil est une etoile. Il brille. La Terre tourne autour. La vie existe grace a lui.", "summarize"),
    ("Traduis bonjour en anglais ?", "translate"),
]

print("=" * 70)
print("  KA-Next DEMO -- 6 questions, 5 modes holographiques")
print("=" * 70)

for prompt, mode in questions:
    print(f"\n{'='*70}")
    print(f"  QUESTION [{mode.upper()}]: {prompt}")
    print(f"{'='*70}")
    result = engine.query(prompt, mode=mode)
    text = result.get("text", "")
    safe = text[:400].encode('ascii', errors='replace').decode('ascii')
    print(safe)
    print(f"\n  ---")
    print(f"  Mode: {result.get('mode','?')} | "
          f"Source: {result.get('source','?')} | "
          f"Temps: {result.get('temps_ms',0)}ms | "
          f"Confiance: {result.get('confidence',0)}")
    if result.get('facts_used'):
        print(f"  Faits actives: {result['facts_used']}")
    print()

print("=" * 70)
print("  DEMO TERMINEE")
print("=" * 70)