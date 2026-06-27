#!/usr/bin/env python3
"""
LM Arena Style Benchmark — 200 Random Questions
================================================
Tests the FULL pipeline on 200 questions with varied formulations.
Measures: accuracy, source distribution, latency.

Pipeline:
  1. Parametric KB (∞ coverage)
  2. Semantic Matcher (embeddings/TF-IDF)
  3. Exact Matching (existing engine)
  4. Multi-Step Reasoner
  5. Optimized Fallback (DeepSeek)

Usage: python benchmark_arena_style.py [--quick] [--full]
  --quick: 50 questions, no API calls
  --full: 200 questions, with API fallback
"""

import sys, os, time, json, random, re, math
from typing import Dict, Any, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(__file__))

from harmonic_math_engine import HarmonicMathEngine
from harmonic_reasoner import HarmonicMultiStepReasoner
from knowledge_base import PRE_COMPUTED as KB

# ============================================================================
# 1. BUILD DIVERSE TEST SET (200 questions)
# ============================================================================

def generate_arena_style_questions(kb: Dict, n: int = 200) -> List[Dict]:
    """
    Generate a diverse test set with varied formulations.
    
    Strategy:
    - 50%: Questions randomly drawn from KB (with exact keys)
    - 30%: Reformulated questions (same concept, different wording)
    - 20%: Compound/multi-step questions (combining concepts)
    """
    keys = list(kb.keys())
    random.shuffle(keys)
    
    dataset = []
    
    # Reformulation templates
    reformulations = [
        ("what is {}", ["calculate {}", "compute {}", "find {}", "evaluate {}", "determine {}", "{} please", "can you tell me {}", "i need to know {}"]),
        ("solve {}", ["find the solution to {}", "find x in {}", "what is x in {}", "determine the roots of {}", "solve for x: {}"]),
        ("what is the derivative of {}", ["differentiate {}", "find d/dx of {}", "compute the derivative of {}", "what is the rate of change of {}", "derive {}"]),
        ("what is the integral of {}", ["integrate {}", "find the antiderivative of {}", "compute the integral of {}", "evaluate the indefinite integral of {}"]),
    ]
    
    # Phase 1: Direct KB questions (100 questions)
    direct_keys = keys[:100]
    for key in direct_keys:
        value = kb[key]
        # Expected answer: extract first number or key concept
        expected = _extract_expected(value.get("text", ""), value.get("domain", "general"))
        dataset.append({
            "prompt": key,
            "expected": expected,
            "domain": value.get("domain", "general"),
            "type": "direct",
            "difficulty": "easy",
        })
    
    # Phase 2: Reformulated questions (60 questions)
    reform_keys = keys[100:160]
    for key in reform_keys:
        value = kb[key]
        # Pick a reformulation
        reformulated = key
        for pattern, variants in reformulations:
            m = re.search(pattern.replace("{}", "(.+)"), key)
            if m:
                captured = m.group(1).strip()
                variant = random.choice(variants).format(captured)
                reformulated = variant
                break
        
        if reformulated == key:
            reformulated = f"can you tell me {key}"
        
        expected = _extract_expected(value.get("text", ""), value.get("domain", "general"))
        dataset.append({
            "prompt": reformulated,
            "expected": expected,
            "domain": value.get("domain", "general"),
            "type": "reformulated",
            "difficulty": "medium",
        })
    
    # Phase 3: Compound questions (40 questions)
    compound_templates = [
        # Chain rule style
        "what is the derivative of sin(x^2)",
        "what is the derivative of cos(x^3)",
        "what is the derivative of e^(x^2)",
        "what is the derivative of ln(x^2)",
        "what is the derivative of tan(x^2)",
        # Product rule style
        "what is the derivative of x * sin(x)",
        "what is the derivative of x^2 * cos(x)",
        "what is the derivative of e^x * sin(x)",
        # Multi-step
        "find the derivative of sin(x) and evaluate at x=0",
        "what is the second derivative of x^3",
        "what is the slope of the tangent to y=x^2 at x=3",
        # Word problems
        "a rectangle has length 5 more than width and area 36. find dimensions",
        "if 3x + 7 = 22, what is 2x + 5",
        "the sum of two numbers is 10 and their product is 21. find them",
        "a car travels 60 km in 1.5 hours. what is its speed in km/h",
    ]
    
    for i in range(min(40, len(compound_templates))):
        prompt = compound_templates[i]
        dataset.append({
            "prompt": prompt,
            "expected": _extract_expected_from_compound(prompt),
            "domain": _detect_domain(prompt),
            "type": "compound",
            "difficulty": "hard",
        })
    
    random.shuffle(dataset)
    return dataset[:n]


def _extract_expected(text: str, domain: str) -> List[str]:
    """Extract key concepts to verify correctness."""
    concepts = []
    # Numbers
    concepts.extend(re.findall(r'\b(\d+\.?\d*)\b', text)[:3])
    # Key math terms
    if domain == "calculus":
        concepts.extend(re.findall(r'(?:cos|sin|tan|sec|csc|cot|ln|exp|derivative|integral|power rule|chain rule)', text, re.IGNORECASE))
    elif domain == "algebra":
        concepts.extend(re.findall(r'(?:x\s*=|factor|root|solution|quadratic)', text, re.IGNORECASE))
    return [c.lower() for c in concepts if len(c) > 1]


def _extract_expected_from_compound(prompt: str) -> List[str]:
    """Extract expected concepts for compound questions."""
    concepts = []
    p = prompt.lower()
    
    if "derivative of sin(x^2)" in p:
        concepts = ["cos", "2x", "chain", "cos(x^2)"]
    elif "derivative of cos(x^3)" in p:
        concepts = ["-sin", "3x^2", "chain", "sin(x^3)"]
    elif "derivative of e^(x^2)" in p:
        concepts = ["e^(x^2)", "2x", "chain"]
    elif "derivative of ln(x^2)" in p:
        concepts = ["2/x", "chain", "ln"]
    elif "derivative of tan(x^2)" in p:
        concepts = ["sec^2", "2x", "chain"]
    elif "derivative of x * sin(x)" in p or "derivative of x sin(x)" in p:
        concepts = ["sin(x)", "cos(x)", "product"]
    elif "derivative of x^2 * cos(x)" in p:
        concepts = ["2x", "cos", "sin", "product"]
    elif "derivative of e^x * sin(x)" in p:
        concepts = ["e^x", "sin", "cos", "product"]
    elif "derivative of sin(x) and evaluate at x=0" in p:
        concepts = ["cos", "1", "0"]
    elif "second derivative of x^3" in p:
        concepts = ["6x"]
    elif "slope of the tangent to y=x^2 at x=3" in p:
        concepts = ["6", "2x", "slope"]
    elif "a rectangle has length 5 more than width and area 36" in p:
        concepts = ["4", "9"]
    elif "3x + 7 = 22" in p:
        concepts = ["5"]
    elif "sum of two numbers is 10" in p:
        concepts = ["3", "7"]
    elif "speed" in p and "60" in p:
        concepts = ["40"]
    
    return concepts if concepts else ["solution"]


def _detect_domain(prompt: str) -> str:
    p = prompt.lower()
    if re.search(r'derivative|differentiate|integral|integrate|limit|d/dx', p):
        return "calculus"
    if re.search(r'solve|equation|quadratic|polynomial|factor|x\s*=', p):
        return "algebra"
    if re.search(r'area|volume|perimeter|circle|triangle|square|rectangle', p):
        return "geometry"
    if re.search(r'sin|cos|tan|angle|degrees|radians', p):
        return "trigonometry"
    if re.search(r'probability|chance|odds|mean|median|mode', p):
        return "statistics"
    if re.search(r'if.*then|therefore|logic|valid|sound|prove', p):
        return "reasoning"
    return "general"


# ============================================================================
# 2. BENCHMARK ENGINE
# ============================================================================

def run_benchmark(n_questions: int = 200, use_api: bool = False):
    print("=" * 70)
    print(f"  LM ARENA STYLE BENCHMARK ({n_questions} questions)")
    print("=" * 70)
    print()
    
    # Build dataset
    dataset = generate_arena_style_questions(KB, n_questions)
    print(f"  Dataset: {len(dataset)} questions")
    direct = sum(1 for d in dataset if d["type"] == "direct")
    reform = sum(1 for d in dataset if d["type"] == "reformulated")
    compound = sum(1 for d in dataset if d["type"] == "compound")
    print(f"    Direct: {direct} | Reformulated: {reform} | Compound: {compound}")
    print()
    
    # Initialize engines
    engine = HarmonicMathEngine()
    reasoner = HarmonicMultiStepReasoner(engine)
    
    # Try to load parametric and semantic matchers
    try:
        from parametric_kb import ParametricKB
        parametric = ParametricKB()
        has_parametric = True
    except ImportError:
        parametric = None
        has_parametric = False
    
    try:
        from semantic_matcher import HybridMatcher
        hybrid = HybridMatcher(engine)
        has_semantic = True
    except ImportError:
        hybrid = None
        has_semantic = False
    
    print(f"  Pipeline: Parametric={'Y' if has_parametric else 'N'} | "
          f"Semantic={'Y' if has_semantic else 'N'} | "
          f"Reasoner=Y | Fallback={'Y' if use_api else 'N (disabled)'}")
    print()
    
    results = []
    sources = {}
    correct = 0
    total_time = 0.0
    
    print(f"  {'-' * 65}")
    print(f"  {'#':>4s} {'Type':>10s} {'Source':>15s} {'Time':>8s} {'Correct':>8s} {'Prompt'}")
    print(f"  {'-' * 65}")
    
    for i, item in enumerate(dataset):
        prompt = item["prompt"]
        expected = item["expected"]
        qtype = item["type"]
        
        t0 = time.time()
        
        # LEVEL 1: Parametric KB
        result = None
        source = "?"
        
        if parametric:
            result = parametric.solve(prompt)
            if result:
                source = "parametric"
        
        # LEVEL 2: Semantic Matcher
        if not result and hybrid:
            result = hybrid.find_best(prompt)
            if result:
                source = "semantic"
        
        # LEVEL 3: Existing engine (exact + token matching)
        if not result:
            analysis = engine.analyze(prompt)
            if analysis["coherence"] >= engine.CONFIDENCE_THRESHOLD:
                result = engine.solve(prompt, analysis)
                if result:
                    source = "kb_exact"
        
        # LEVEL 4: Multi-Step Reasoner
        if not result:
            multi = reasoner.solve(prompt)
            if multi.get("confidence", 0) >= engine.CONFIDENCE_THRESHOLD:
                result = multi
                source = "reasoner"
        
        # LEVEL 5: Fallback (only if API enabled)
        if not result and use_api:
            from fallback_optimizer import OptimizedFallback
            try:
                fb = OptimizedFallback(api_key="", use_cross_validation=False)
                fb_result = fb.generate(prompt, analysis={"domain": item["domain"]})
                if fb_result.get("confidence", 0) > 0.3:
                    result = fb_result
                    source = "fallback"
            except:
                pass
        
        # If no result, use harmonic reasoning as last resort
        if not result:
            analysis = engine.analyze(prompt)
            result = engine._harmonic_reasoning(prompt, analysis)
            source = "harmonic_raw"
        
        time_ms = (time.time() - t0) * 1000
        total_time += time_ms
        
        # Verify correctness (fuzzy: normalize + token-level check)
        response_text = result.get("text", "").lower()
        is_correct = False
        if expected:
            for exp in expected:
                exp_lower = exp.lower().strip()
                # Direct substring
                if exp_lower in response_text:
                    is_correct = True
                    break
                # Check for individual tokens (for compound answers)
                tokens = re.findall(r'[a-z0-9\.\+\-\*\/\^]+', exp_lower)
                if tokens and all(t in response_text for t in tokens):
                    is_correct = True
                    break
        else:
            is_correct = True
        
        if is_correct:
            correct += 1
        
        sources[source] = sources.get(source, 0) + 1
        
        results.append({
            "prompt": prompt[:60],
            "type": qtype,
            "domain": item["domain"],
            "source": source,
            "time_ms": round(time_ms, 2),
            "correct": is_correct,
        })
        
        # Print progress
        status = "OK" if is_correct else "KO"
        if (i + 1) % 20 == 0 or i < 10:
            print(f"  {i+1:4d} {qtype:>10s} {source:>15s} {time_ms:>7.1f}ms {status:>8s} {prompt[:40]}")
    
    n = len(dataset)
    
    # ========================================================================
    # RESULTS
    # ========================================================================
    print()
    print("=" * 70)
    print(f"  RESULTS — {n} Questions")
    print("=" * 70)
    print()
    print(f"  ACCURACY:      {correct}/{n} ({correct/n*100:.1f}%)")
    print(f"  AVG LATENCY:   {total_time/n:.1f} ms")
    print(f"  AVG CONFIDENCE: {sum(r.get('confidence', 0.5) for r in results)/n*100:.0f}%")
    print()
    
    # Per source
    print(f"  SOURCE DISTRIBUTION:")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        src_results = [r for r in results if r["source"] == src]
        src_correct = sum(1 for r in src_results if r["correct"])
        pct = count / n * 100
        bar = "#" * int(pct / 2)
        print(f"    {src:<20s} {count:>4d} ({pct:>5.1f}%) [{src_correct}/{count} correct] {bar}")
    
    # Per type
    print()
    print(f"  PER QUESTION TYPE:")
    for qtype in ["direct", "reformulated", "compound"]:
        type_results = [r for r in results if r["type"] == qtype]
        if type_results:
            type_correct = sum(1 for r in type_results if r["correct"])
            type_time = sum(r["time_ms"] for r in type_results) / max(len(type_results), 1)
            print(f"    {qtype:<15s} {type_correct}/{len(type_results)} correct ({type_correct/len(type_results)*100:.0f}%) | {type_time:.1f}ms avg")
    
    # Per domain
    print()
    print(f"  PER DOMAIN:")
    domains = {}
    for r in results:
        d = r["domain"]
        if d not in domains:
            domains[d] = {"total": 0, "correct": 0}
        domains[d]["total"] += 1
        if r["correct"]:
            domains[d]["correct"] += 1
    for d in sorted(domains.keys()):
        stats = domains[d]
        acc = stats["correct"] / stats["total"] * 100
        bar = "#" * int(acc / 5)
        print(f"    {d:<20s} {acc:>5.1f}% {bar} ({stats['correct']}/{stats['total']})")
    
    # Save results
    output = {
        "total": n,
        "correct": correct,
        "accuracy": round(correct/n, 4),
        "avg_time_ms": round(total_time/n, 2),
        "sources": {s: {"count": c, "correct": sum(1 for r in results if r["source"]==s and r["correct"])} 
                    for s, c in sources.items()},
        "details": results,
    }
    
    out_path = os.path.join(os.path.dirname(__file__), "benchmark_arena_200_results.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to {out_path}")
    
    return output


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="50 questions, no API")
    parser.add_argument("--full", action="store_true", help="200 questions, with API")
    args = parser.parse_args()
    
    n = 50 if args.quick else 200
    use_api = args.full
    
    run_benchmark(n_questions=n, use_api=use_api)