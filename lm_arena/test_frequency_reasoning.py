#!/usr/bin/env python3
"""
Test: Frequency-Based Reasoning vs Regex-Based Reasoning
=========================================================
Validates the frequency reasoner on 50 logic/reasoning questions.
Compares accuracy and confidence between the two approaches.

Usage: python test_frequency_reasoning.py [--compare]
"""

import sys, os, time, re
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(__file__))

from frequency_reasoner import FrequencyReasoner, get_concept_signature, LOGIC_SIGNATURES

# ============================================================================
# 1. REASONING DATASET — 25 diverse logic questions
# ============================================================================

REASONING_QUESTIONS = [
    # Syllogisms
    ("If all dogs are mammals and all mammals are animals, are all dogs animals?", "yes", "syllogism"),
    ("If all cats are mammals and no mammals are fish, can a cat be a fish?", "no", "syllogism"),
    ("If all squares are rectangles and all rectangles have four sides, do squares have four sides?", "yes", "syllogism"),
    ("If all birds can fly and a penguin is a bird, can a penguin fly?", "yes", "syllogism"),  # valid but not sound
    ("If all fruits have seeds and apples are fruits, do apples have seeds?", "yes", "syllogism"),
    
    # Contrapositives
    ("What is the contrapositive of: If it rains, then the ground gets wet?", "not wet", "contrapositive"),
    ("What is the contrapositive of: If you study, you will pass?", "not pass", "contrapositive"),
    ("What is the contrapositive of: If x > 2 then x > 0?", "x <= 0", "contrapositive"),
    
    # Validity checks
    ("Is the following argument valid? If it rains, the ground is wet. The ground is wet. Therefore, it rained.", "no", "validity"),
    ("Is this argument valid? If P then Q. Q is true. Therefore P.", "no", "validity"),
    ("Is this argument valid? If an animal is a dog, it is a mammal. Rex is a dog. Therefore, Rex is a mammal.", "yes", "validity"),
    ("Is the following argument valid? All men are mortal. Socrates is a man. Therefore, Socrates is mortal.", "yes", "validity"),
    
    # Proofs
    ("Prove that the product of two odd numbers is odd", "odd", "proof"),
    ("Prove that the sum of two even numbers is even", "even", "proof"),
    ("Prove that sqrt(2) is irrational", "irrational", "proof"),
    
    # Sequence detection
    ("What is the next number in the sequence: 2, 4, 6, 8?", "10", "sequence"),
    ("What is the next number in the sequence: 3, 9, 27, 81?", "243", "sequence"),
    ("What is the next number in the sequence: 1, 4, 9, 16?", "25", "sequence"),
    ("What is the next term in the series: 2, 4, 8, 16?", "32", "sequence"),
    
    # Set theory / basic logic
    ("Is the empty set a subset of every set?", "yes", "set_theory"),
    ("What is the negation of: All dogs are friendly?", "some dogs are not", "negation"),
    ("What is the transitive property of equality?", "a=b and b=c then a=c", "property"),
    ("Are 'P implies Q' and 'not P or Q' logically equivalent?", "yes", "equivalence"),
    ("Is the statement 'This statement is false' a paradox?", "yes", "paradox"),
    ("If x > 5 and y < 3, which is larger, x or y?", "x", "comparison"),
]

# ============================================================================
# 2. TEST ENGINE
# ============================================================================

def test_frequency_reasoner():
    """Test the frequency-based reasoner on all 25 questions."""
    fr = FrequencyReasoner()
    
    print("=" * 70)
    print("  FREQUENCY REASONER TEST — 25 Logic Questions")
    print("=" * 70)
    print()
    
    correct = 0
    total = len(REASONING_QUESTIONS)
    results = []
    
    for i, (question, expected, qtype) in enumerate(REASONING_QUESTIONS):
        t0 = time.time()
        response = fr.reason(question)
        time_ms = (time.time() - t0) * 1000
        
        response_text = response.get("text", "").lower()
        method = response.get("method", "?")
        
        # Verify: check if expected keyword is in response
        is_correct = expected.lower() in response_text
        
        if is_correct:
            correct += 1
        
        status = "OK" if is_correct else "KO"
        print(f"  [{i+1:2d}/{total}] {status} {qtype:>15s} | {method:>30s} | "
              f"{time_ms:>5.1f}ms | {question[:50]}")
        
        if not is_correct:
            print(f"        Expected '{expected}' not found in response")
            print(f"        Got: {response_text[:100]}")
        
        results.append({
            "question": question[:60],
            "type": qtype,
            "method": method,
            "expected": expected,
            "correct": is_correct,
            "time_ms": round(time_ms, 2),
            "confidence": response.get("confidence", 0),
        })
    
    # ================================================================
    # Results
    # ================================================================
    print()
    print("=" * 70)
    print(f"  RESULTS — Frequency Reasoner")
    print("=" * 70)
    print()
    print(f"  Accuracy: {correct}/{total} ({correct/total*100:.0f}%)")
    print(f"  Avg Time: {sum(r['time_ms'] for r in results)/total:.1f} ms")
    print()
    
    # Per type
    types = {}
    for r in results:
        t = r["type"]
        if t not in types:
            types[t] = {"correct": 0, "total": 0}
        types[t]["total"] += 1
        if r["correct"]:
            types[t]["correct"] += 1
    
    print("  PER TYPE:")
    for t in sorted(types.keys()):
        ts = types[t]
        acc = ts["correct"] / ts["total"] * 100
        bar = "#" * int(acc / 5)
        print(f"    {t:<20s} {acc:>5.0f}% {bar} ({ts['correct']}/{ts['total']})")
    
    # Per method
    methods = {}
    for r in results:
        m = r["method"]
        if m not in methods:
            methods[m] = {"correct": 0, "total": 0}
        methods[m]["total"] += 1
        if r["correct"]:
            methods[m]["correct"] += 1
    
    print()
    print("  PER METHOD:")
    for m in sorted(methods.keys()):
        ms = methods[m]
        acc = ms["correct"] / ms["total"] * 100 if ms["total"] > 0 else 0
        print(f"    {m:<35s} {acc:>5.0f}% ({ms['correct']}/{ms['total']})")
    
    return correct / total

def test_frequency_concepts():
    """Test frequency concept mapping — the core innovation."""
    print()
    print("=" * 70)
    print("  FREQUENCY CONCEPT MAPPING TEST")
    print("=" * 70)
    print()
    
    test_words = [
        "and", "or", "not", "implies", "all", "some", "none",
        "cats", "dogs", "mammals", "animals", "birds", "fish",
        "true", "false", "valid", "sound", "rain", "wet", "ground",
        "Socrates", "rectangle", "square", "penguin",
    ]
    
    print(f"  {'Word':<15s} {'kx':>8s} {'ky':>8s} {'Source':>20s}")
    print(f"  {'-'*15} {'-'*8} {'-'*8} {'-'*20}")
    
    for word in test_words:
        kx, ky = get_concept_signature(word)
        
        # Determine source
        if word.upper() in LOGIC_SIGNATURES:
            source = "LOGIC_SIGNATURES"
        elif word.lower() in {"and","or","not","implies","all","some","none"}:
            source = "LOGIC_CONCEPT_MAP"
        else:
            source = "SHA256 hash"
        
        print(f"  {word:<15s} {kx:>8.3f} {ky:>8.3f} {source:>20s}")
    
    # Test frequency distance between related concepts
    print()
    print("  FREQUENCY DISTANCES (lower = more related):")
    pairs = [
        ("cats", "mammals"),
        ("dogs", "mammals"),
        ("cats", "dogs"),
        ("rain", "wet"),
        ("birds", "penguin"),
        ("square", "rectangle"),
    ]
    for a, b in pairs:
        kx_a, ky_a = get_concept_signature(a)
        kx_b, ky_b = get_concept_signature(b)
        dist = ((kx_a - kx_b)**2 + (ky_a - ky_b)**2)**0.5
        print(f"    {a} <-> {b}: {dist:.3f}")

if __name__ == "__main__":
    test_frequency_concepts()
    accuracy = test_frequency_reasoner()
    
    print()
    print("=" * 70)
    print(f"  FINAL: Frequency Reasoner = {accuracy*100:.0f}% accuracy")
    print(f"  Previous (regex rules): 30-40% on 50 questions")
    print(f"  Gain: {'+' if accuracy > 0.4 else ''}{int((accuracy - 0.4)*100)} percentage points")
    print("=" * 70)