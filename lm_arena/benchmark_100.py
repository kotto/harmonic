#!/usr/bin/env python3
"""
Benchmark 100 Questions — LM Arena Math & Reasoning
=====================================================
Test étendu : 80 mathématiques + 20 raisonnement.
Utilise la base de connaissances comme source de questions ET de réponses attendues.
"""

import time
import json
import re
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

from harmonic_math_engine import HarmonicMathEngine
from fallback_router import FallbackRouter
from knowledge_base import PRE_COMPUTED

# =============================================================================
# GÉNÉRATION DU DATASET DE 100 QUESTIONS À PARTIR DE LA BASE
# =============================================================================

def extract_expected_concepts(text, domain):
    """Extrait les concepts-clés d'une réponse pour vérification."""
    concepts = []
    
    # Extraire les nombres
    numbers = re.findall(r'\b(\d+\.?\d*)\b', text)
    for n in numbers[:3]:
        concepts.append(n)
    
    # Extraire les formules (séquences avec = + - * / ^)
    formulas = re.findall(r'=?\s*[\d\w\^\(\)\+\-\*/\.\s]+\b(?:units|degrees|square|cubic|radians|%)?', text)
    for f in formulas[:2]:
        clean = f.strip().rstrip('.,;:')
        if len(clean) > 3:
            concepts.append(clean)
    
    # Mots-clés de domaine
    domain_keywords = {
        "arithmetic": ["multiplication", "addition", "subtraction", "division", "order of operations", "PEMDAS"],
        "algebra": ["equation", "factor", "solve", "quadratic", "variable", "root", "polynomial"],
        "calculus": ["derivative", "integral", "limit", "rule", "power rule", "chain rule", "differentiate"],
        "geometry": ["area", "volume", "perimeter", "circle", "triangle", "square", "theorem"],
        "trigonometry": ["sin", "cos", "tan", "angle", "identity", "radians", "degrees"],
        "probability": ["probability", "chance", "odds", "event", "favorable", "sample"],
        "statistics": ["mean", "median", "mode", "variance", "standard deviation", "distribution"],
        "number_theory": ["prime", "factor", "divisible", "gcd", "lcm", "divisor"],
        "reasoning": ["yes", "no", "therefore", "valid", "sound", "syllogism", "modus", "ponens", "tollens"],
        "combinatorics": ["permutation", "combination", "ways", "arrange", "select", "factorial"],
        "analysis": ["euler", "limit", "series", "taylor", "maclaurin", "convergence", "pi"],
        "set_theory": ["cardinality", "set", "subset", "element", "countable", "continuum"],
        "linear_algebra": ["matrix", "vector", "eigenvalue", "determinant", "linear", "transformation"],
    }
    
    if domain in domain_keywords:
        for kw in domain_keywords[domain]:
            if kw.lower() in text.lower():
                concepts.append(kw)
    
    return concepts[:5]  # Max 5 concepts


def build_benchmark_dataset():
    """Construit un dataset de 100 questions à partir de la base de connaissances."""
    dataset = []
    
    # Répartition par domaine
    domain_quotas = {
        "arithmetic": 12,
        "algebra": 15,
        "calculus": 15,
        "geometry": 10,
        "trigonometry": 10,
        "probability": 6,
        "statistics": 6,
        "number_theory": 4,
        "combinatorics": 4,
        "analysis": 3,
        "set_theory": 1,
        "linear_algebra": 2,
        "reasoning": 12,
    }
    
    domain_count = {k: 0 for k in domain_quotas}
    
    for key, value in PRE_COMPUTED.items():
        domain = value.get("domain", "general")
        
        # Vérifier le quota du domaine
        target = domain_quotas.get(domain, 3)
        if domain_count.get(domain, 0) >= target:
            continue
        
        text = value["text"]
        concepts = extract_expected_concepts(text, domain)
        
        if not concepts:
            continue
        
        # Déterminer la difficulté
        difficulty = "easy"
        if len(text) > 200 or len(key) > 50:
            difficulty = "medium"
        if len(text) > 500:
            difficulty = "hard"
        
        dataset.append({
            "prompt": key,
            "expected_concepts": concepts,
            "domain": domain,
            "difficulty": difficulty,
        })
        
        domain_count[domain] = domain_count.get(domain, 0) + 1
        
        if len(dataset) >= 100:
            break
    
    # Si pas assez d'entrées, compléter avec des variantes des entrées existantes
    if len(dataset) < 100:
        existing_keys = list(PRE_COMPUTED.keys())
        idx = 0
        while len(dataset) < 100 and idx < len(existing_keys):
            key = existing_keys[idx]
            value = PRE_COMPUTED[key]
            # Créer une variante en modifiant légèrement la question
            variants = [
                key.replace("what is", "calculate").replace("what is", "compute"),
                "Can you " + key,
                key + " please",
                "I need to know: " + key,
                "Help me solve: " + key,
            ]
            for variant in variants:
                if len(dataset) >= 100:
                    break
                concepts = extract_expected_concepts(value["text"], value["domain"])
                if concepts:
                    dataset.append({
                        "prompt": variant,
                        "expected_concepts": concepts,
                        "domain": value["domain"],
                        "difficulty": "easy",
                    })
            idx += 1
    
    return dataset[:100]


# =============================================================================
# EXÉCUTION DU BENCHMARK
# =============================================================================

def run_benchmark_100():
    print("=" * 70)
    print("  LM ARENA -- Extended Benchmark (100 Questions)")
    print("=" * 70)
    
    # Construction du dataset
    print("\n[BUILDING DATASET]")
    dataset = build_benchmark_dataset()
    print(f"  Generated {len(dataset)} questions from knowledge base")
    
    # Stats par domaine
    domains = {}
    for item in dataset:
        d = item["domain"]
        domains[d] = domains.get(d, 0) + 1
    print(f"  Domain distribution: {dict(sorted(domains.items()))}")
    
    # Initialisation
    engine = HarmonicMathEngine()
    router = FallbackRouter()
    
    results = []
    total_confidence = 0.0
    total_time = 0.0
    harmonic_count = 0
    correct_count = 0
    kb_match_count = 0
    
    print(f"\n[RUNNING BENCHMARK]")
    print("-" * 70)
    
    for i, item in enumerate(dataset):
        prompt = item["prompt"]
        expected = item["expected_concepts"]
        
        t0 = time.time()
        
        # Analyse harmonique
        analysis = engine.analyze(prompt)
        confidence = analysis.get("coherence", 0.0)
        
        # Résolution
        if confidence >= engine.CONFIDENCE_THRESHOLD:
            result = engine.solve(prompt, analysis)
            source = "harmonic"
            harmonic_count += 1
            if result.get("method") == "precomputed":
                kb_match_count += 1
        else:
            result = router.generate(prompt, analysis)
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
        })
        
        # Progression
        if (i + 1) % 10 == 0:
            current_accuracy = correct_count / (i + 1) * 100
            print(f"  [{i+1:3d}/100] Accuracy: {current_accuracy:.1f}% | "
                  f"Harmonic: {harmonic_count} | KB matches: {kb_match_count}")
    
    n = len(dataset)
    
    # Calcul des métriques par domaine
    domain_accuracy = {}
    for item in results:
        d = item["domain"]
        if d not in domain_accuracy:
            domain_accuracy[d] = {"correct": 0, "total": 0}
        domain_accuracy[d]["total"] += 1
        if item["correct"]:
            domain_accuracy[d]["correct"] += 1
    
    # Affichage des résultats
    print(f"\n{'=' * 70}")
    print(f"  RESULTS")
    print(f"{'=' * 70}")
    
    print(f"\n  GLOBAL METRICS")
    print(f"  {'-' * 50}")
    print(f"  Total Questions:     {n}")
    print(f"  Correct Answers:     {correct_count}/{n}")
    print(f"  Overall Accuracy:    {correct_count/n*100:.1f}%")
    print(f"  Avg Confidence:      {total_confidence/n*100:.1f}%")
    print(f"  Avg Time:            {total_time/n:.1f} ms")
    print(f"  Harmonic Ratio:      {harmonic_count/n*100:.1f}% ({harmonic_count}/{n})")
    print(f"  KB Match Rate:       {kb_match_count/n*100:.1f}% ({kb_match_count}/{n})")
    
    print(f"\n  PER DOMAIN ACCURACY")
    print(f"  {'-' * 50}")
    for domain in sorted(domain_accuracy.keys()):
        stats = domain_accuracy[domain]
        acc = stats["correct"] / stats["total"] * 100
        bar = "#" * int(acc / 10)
        print(f"  {domain:<20s} {acc:5.1f}% {bar} ({stats['correct']}/{stats['total']})")
    
    # Détail des erreurs
    errors = [r for r in results if not r["correct"]]
    if errors:
        print(f"\n  ERRORS ({len(errors)} questions)")
        print(f"  {'-' * 50}")
        for e in errors[:15]:
            print(f"  KO [{e['source'][:4]:4s}] {e['prompt'][:65]} ({e['time_ms']:.0f}ms)")
        if len(errors) > 15:
            print(f"  ... and {len(errors)-15} more errors")
    
    # Sauvegarde
    output = {
        "total": n,
        "correct": correct_count,
        "accuracy": round(correct_count/n, 4),
        "avg_confidence": round(total_confidence/n, 4),
        "avg_time_ms": round(total_time/n, 2),
        "harmonic_ratio": round(harmonic_count/n, 4),
        "kb_match_rate": round(kb_match_count/n, 4),
        "per_domain": {d: round(s["correct"]/s["total"], 4) for d, s in domain_accuracy.items()},
        "errors": [e for e in results if not e["correct"]],
    }
    
    with open("benchmark_100_results.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n  Results saved to benchmark_100_results.json")
    
    return output


if __name__ == "__main__":
    run_benchmark_100()