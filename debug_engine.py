#!/usr/bin/env python3
"""Debug script for harmonic_lm_arena_engine"""
import sys
sys.path.insert(0, '.')
from harmonic_lm_arena_engine import HarmonicPromptAnalyzer, HarmonicResonanceEngine

analyzer = HarmonicPromptAnalyzer()

prompts = [
    'Calculez 15% de 340',
    'Ecrivez un algorithme de tri par fusion en Python',
    'Ecrivez un poeme sur l amour',
    'Pourquoi le ciel est-il bleu Expliquez en detail',
    'Quelle est la capitale de la France',
]

print("=== Analyse harmonique ===")
for p in prompts:
    sig = analyzer.analyze(p)
    cat, conf = analyzer.classify_prompt(sig)
    print(f'Prompt: {p}')
    print(f'  k_math={sig.k_mathematical:.4f}, k_code={sig.k_code:.4f}, k_creative={sig.k_creative:.4f}, k_reasoning={sig.k_reasoning:.4f}, k_factual={sig.k_factual:.4f}')
    print(f'  Categorie: {cat} (confiance: {conf:.4f})')
    print()

print("=== Resonance engine ===")
engine = HarmonicResonanceEngine()
for p in prompts:
    result = engine.process(p)
    print(f'Prompt: {p}')
    print(f'  Matched: {result.matched}, Pattern: {result.pattern_name}, Score: {result.resonance_score:.4f}')
    print(f'  Cache hit: {result.cache_hit}, Time: {result.processing_time_ms:.2f}ms')
    print()

print("=== Stats ===")
stats = engine.get_stats()
print(f'Total: {stats["total_requests"]}, Cache: {stats["cache_hits"]}, Pattern: {stats["pattern_matches"]}, Fallback: {stats["fallback_deepseek"]}')
