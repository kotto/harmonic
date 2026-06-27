#!/usr/bin/env python3
"""
Math & Reasoning Benchmark — LM Arena
=======================================
Benchmark interne pour les catégories mathématiques et raisonnement.

Métriques :
  - Accuracy : réponses correctes / total
  - Confidence moyenne
  - Temps de réponse moyen
  - Ratio harmonique vs fallback
"""

import time
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# =============================================================================
# DATASET DE TEST — Mathématiques
# =============================================================================

MATH_BENCHMARK = [
    {
        "prompt": "What is the derivative of x^2?",
        "expected_concepts": ["2x", "power rule", "derivative"],
        "domain": "calculus",
        "difficulty": "easy"
    },
    {
        "prompt": "What is the integral of x?",
        "expected_concepts": ["x^2/2", "+C", "power rule"],
        "domain": "calculus",
        "difficulty": "easy"
    },
    {
        "prompt": "Solve x^2 - 3x + 2 = 0",
        "expected_concepts": ["x=1", "x=2", "quadratic", "factor"],
        "domain": "algebra",
        "difficulty": "easy"
    },
    {
        "prompt": "What is the area of a circle with radius 5?",
        "expected_concepts": ["pi*r^2", "25pi", "78.5"],
        "domain": "geometry",
        "difficulty": "easy"
    },
    {
        "prompt": "What is the Pythagorean theorem?",
        "expected_concepts": ["a²+b²=c²", "hypotenuse", "right triangle"],
        "domain": "geometry",
        "difficulty": "easy"
    },
    {
        "prompt": "What is e^(i*pi) + 1?",
        "expected_concepts": ["0", "Euler", "identity"],
        "domain": "analysis",
        "difficulty": "easy"
    },
    {
        "prompt": "Calculate 15 * 7 + 3",
        "expected_concepts": ["108", "multiplication", "addition"],
        "domain": "arithmetic",
        "difficulty": "easy"
    },
    {
        "prompt": "What is the derivative of sin(x)?",
        "expected_concepts": ["cos(x)", "trigonometric", "derivative"],
        "domain": "calculus",
        "difficulty": "medium"
    },
    {
        "prompt": "Find the roots of x^2 + 5x + 6 = 0",
        "expected_concepts": ["x=-2", "x=-3", "quadratic"],
        "domain": "algebra",
        "difficulty": "medium"
    },
    {
        "prompt": "What is the probability of rolling a sum of 7 with two dice?",
        "expected_concepts": ["6/36", "1/6", "probability"],
        "domain": "probability",
        "difficulty": "medium"
    },
]

# =============================================================================
# DATASET DE TEST — Raisonnement
# =============================================================================

REASONING_BENCHMARK = [
    {
        "prompt": "If all dogs are mammals and all mammals are animals, are all dogs animals?",
        "expected_concepts": ["yes", "syllogism", "transitive"],
        "domain": "reasoning",
        "difficulty": "easy"
    },
    {
        "prompt": "If it is raining, the ground is wet. The ground is wet. Is it necessarily raining?",
        "expected_concepts": ["no", "fallacy", "affirming the consequent"],
        "domain": "reasoning",
        "difficulty": "medium"
    },
    {
        "prompt": "If a number is even, it is divisible by 2. 14 is even. Is 14 divisible by 2?",
        "expected_concepts": ["yes", "modus ponens", "deduction"],
        "domain": "reasoning",
        "difficulty": "easy"
    },
    {
        "prompt": "All squares are rectangles. All rectangles have four sides. What can you conclude about squares?",
        "expected_concepts": ["four sides", "syllogism", "deduction"],
        "domain": "reasoning",
        "difficulty": "easy"
    },
    {
        "prompt": "If A implies B, and B implies C, does A imply C?",
        "expected_concepts": ["yes", "transitive", "hypothetical syllogism"],
        "domain": "reasoning",
        "difficulty": "easy"
    },
]


class MathBenchmark:
    """Benchmark pour les catégories math & reasoning."""
    
    def __init__(self, math_engine, fallback_router):
        self.math_engine = math_engine
        self.fallback_router = fallback_router
    
    def run(self, category: str = "all", num_samples: int = 10) -> Dict[str, Any]:
        """
        Exécute le benchmark.
        
        Args:
            category: "math", "reasoning", ou "all"
            num_samples: nombre maximum d'échantillons
        
        Returns:
            dict avec les résultats
        """
        # Sélection du dataset
        if category == "math":
            dataset = MATH_BENCHMARK[:num_samples]
        elif category == "reasoning":
            dataset = REASONING_BENCHMARK[:num_samples]
        else:
            dataset = (MATH_BENCHMARK + REASONING_BENCHMARK)[:num_samples]
        
        results = []
        total_confidence = 0.0
        total_time = 0.0
        harmonic_count = 0
        correct_count = 0
        
        for item in dataset:
            prompt = item["prompt"]
            expected = item["expected_concepts"]
            
            t0 = time.time()
            
            # Analyse harmonique
            analysis = self.math_engine.analyze(prompt)
            confidence = analysis.get("coherence", 0.0)
            
            # Résolution
            if confidence >= self.math_engine.CONFIDENCE_THRESHOLD:
                result = self.math_engine.solve(prompt, analysis)
                source = "harmonic"
                harmonic_count += 1
            else:
                result = self.fallback_router.generate(prompt, analysis)
                source = "fallback"
            
            time_ms = (time.time() - t0) * 1000
            total_time += time_ms
            total_confidence += confidence
            
            # Vérification de la réponse
            response_text = result["text"].lower()
            is_correct = any(exp.lower() in response_text for exp in expected)
            if is_correct:
                correct_count += 1
            
            results.append({
                "prompt": prompt[:80],
                "domain": item["domain"],
                "difficulty": item["difficulty"],
                "source": source,
                "confidence": round(confidence, 4),
                "time_ms": round(time_ms, 2),
                "correct": is_correct,
                "expected": expected,
            })
        
        n = len(dataset)
        
        return {
            "category": category,
            "num_samples": n,
            "accuracy": round(correct_count / n, 4) if n > 0 else 0.0,
            "avg_confidence": round(total_confidence / n, 4) if n > 0 else 0.0,
            "avg_time_ms": round(total_time / n, 2) if n > 0 else 0.0,
            "harmonic_ratio": round(harmonic_count / n, 4) if n > 0 else 0.0,
            "correct_count": correct_count,
            "total_count": n,
            "details": results,
        }


def run_cli_benchmark():
    """Exécute le benchmark en ligne de commande."""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    
    from harmonic_math_engine import HarmonicMathEngine
    from fallback_router import FallbackRouter
    
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("  LM ARENA -- Math & Reasoning Benchmark")
    print("=" * 60)
    
    engine = HarmonicMathEngine()
    router = FallbackRouter()  # Auto-détection : api si DEEPSEEK_API_KEY dispo
    bench = MathBenchmark(engine, router)
    
    # Math
    print("\n[MATH BENCHMARK]")
    print("-" * 40)
    math_result = bench.run(category="math", num_samples=10)
    print(f"  Accuracy:       {math_result['accuracy']:.1%}")
    print(f"  Avg Confidence: {math_result['avg_confidence']:.1%}")
    print(f"  Avg Time:       {math_result['avg_time_ms']:.1f} ms")
    print(f"  Harmonic Ratio: {math_result['harmonic_ratio']:.1%}")
    
    # Reasoning
    print("\n[REASONING BENCHMARK]")
    print("-" * 40)
    reason_result = bench.run(category="reasoning", num_samples=5)
    print(f"  Accuracy:       {reason_result['accuracy']:.1%}")
    print(f"  Avg Confidence: {reason_result['avg_confidence']:.1%}")
    print(f"  Avg Time:       {reason_result['avg_time_ms']:.1f} ms")
    print(f"  Harmonic Ratio: {reason_result['harmonic_ratio']:.1%}")
    
    # Combined
    print("\n[COMBINED RESULTS]")
    print("-" * 40)
    all_result = bench.run(category="all", num_samples=15)
    print(f"  Total Samples:  {all_result['num_samples']}")
    print(f"  Accuracy:       {all_result['accuracy']:.1%}")
    print(f"  Avg Confidence: {all_result['avg_confidence']:.1%}")
    print(f"  Avg Time:       {all_result['avg_time_ms']:.1f} ms")
    print(f"  Harmonic Ratio: {all_result['harmonic_ratio']:.1%}")
    print(f"  Correct:        {all_result['correct_count']}/{all_result['total_count']}")
    
    # Résultats détaillés
    print("\n[DETAILS]")
    print("-" * 40)
    for i, r in enumerate(all_result['details']):
        status = "OK" if r['correct'] else "KO"
        print(f"  {status} [{r['source'][:4]:4s}] {r['prompt'][:60]} ({r['time_ms']:.0f}ms)")
    
    return all_result


if __name__ == "__main__":
    result = run_cli_benchmark()
    # Sauvegarde
    with open("benchmark_results.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\nResults saved to benchmark_results.json")
