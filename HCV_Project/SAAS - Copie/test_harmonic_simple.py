#!/usr/bin/env python3
"""
🌊 TEST MODÈLE HARMONIQUE SIMPLE
Seulement le modèle déterministe harmonique
"""

from harmonic_response_generator_simple import HarmonicResponseGenerator
import json

# Instance du modèle harmonique
harmonic = HarmonicResponseGenerator()

# Test simple
test_prompt = "Quelle est la capitale de la France?"

print("🌊 TEST MODÈLE HARMONIQUE PUR")
print("=" * 50)
print(f"Prompt: {test_prompt}")
print()

# Génération
result = harmonic.generate_response(test_prompt)

print("📊 RÉSULTAT:")
print(f"Content length: {len(result['content'])}")
print(f"First 200 chars: {result['content'][:200]}...")
print()
print("🎯 MÉTRIQUES:")
print(f"Determinism: {result['determinism_level']}")
print(f"Harmony: {result['harmony_score']}")
print(f"Elegance: {result['elegance_factor']}")
print(f"Processing time: {result['processing_time']:.4f}s")
