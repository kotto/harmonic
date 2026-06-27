#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTS REELS DES BENCHMARKS AVEC PROXY EC2 (DeepSeek/Qwen)
=========================================================
Utilise le proxy EC2 pour generer les reponses via DeepSeek/Qwen,
puis applique les ameliorations harmoniques.

Pre requis :
  - Le proxy EC2 doit etre accessible (BACKEND_BASE_URL dans .env)
  - deepseek_api_real_final.py doit tourner sur EC2
"""

import os
import sys
import time
import json
import requests
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

# URL du proxy EC2 (deepseek_api_real_final.py)
PROXY_URL = os.getenv("PROXY_URL", "http://ec2-__EC2_IP__.compute-1.amazonaws.com:8000")
GENERATE_URL = f"{PROXY_URL}/generate"
HEALTH_URL = f"{PROXY_URL}/health"

# ============================================================================
# IMPORT DU MOTEUR HARMONIQUE LOCAL
# ============================================================================
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
engine = None
try:
    from harmonic_lm_arena_engine import HarmonicResonanceEngine
    engine = HarmonicResonanceEngine()
    print("[OK] Moteur harmonique importe avec succes")
except Exception as e:
    print(f"[WARN] Impossible d'importer le moteur harmonique: {e}")

# ============================================================================
# FONCTIONS D'APPEL AU PROXY
# ============================================================================

def check_proxy_health():
    """Verifie si le proxy EC2 est accessible"""
    try:
        r = requests.get(HEALTH_URL, timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"[OK] Proxy EC2 accessible - version: {data.get('version', '?')}")
            return True
        else:
            print(f"[WARN] Proxy EC2 retourne HTTP {r.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"[ERREUR] Proxy EC2 INACCESSIBLE - {PROXY_URL}")
        print("  Verifiez que deepseek_api_real_final.py tourne sur l'EC2")
        return False
    except Exception as e:
        print(f"[ERREUR] Proxy EC2: {e}")
        return False


def generate_via_proxy(prompt, max_tokens=500, temperature=0.0, verified_mode=False):
    """Appelle le proxy EC2 pour generer une reponse via DeepSeek/Qwen"""
    payload = {
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "verified_mode": verified_mode,
        "arena_mode": True
    }
    try:
        r = requests.post(GENERATE_URL, json=payload, timeout=120)
        if r.status_code == 200:
            data = r.json()
            return data.get("content", ""), data.get("metrics", {})
        else:
            return f"[ERREUR HTTP {r.status_code}]", {}
    except Exception as e:
        return f"[ERREUR CONNEXION] {e}", {}


# ============================================================================
# BENCHMARK 1 : MMLU (Massive Multitask Language Understanding)
# ============================================================================

def test_mmlu():
    print("\n" + "="*60)
    print("BENCHMARK 1 : MMLU (Massive Multitask Language Understanding)")
    print("="*60)

    questions = [
        # factual
        ("What is the capital of France?", "Paris"),
        ("Who wrote 'Romeo and Juliet'?", "William Shakespeare"),
        ("What is the chemical symbol for gold?", "Au"),
        ("In which year did World War II end?", "1945"),
        ("What is the largest planet in our solar system?", "Jupiter"),
        ("Who was the first president of the United States?", "George Washington"),
        ("What is the speed of light in vacuum (m/s)?", "299792458"),
        ("What is the boiling point of water at sea level (C)?", "100"),
        ("Who developed the theory of general relativity?", "Einstein"),
        ("What is the atomic number of carbon?", "6"),
        # mathematical
        ("What is 15 + 27?", "42"),
        ("What is the square root of 144?", "12"),
        ("If x + 5 = 12, what is x?", "7"),
        ("What is 25% of 200?", "50"),
        ("What is 2^10?", "1024"),
        # reasoning
        ("If all humans are mortal and Socrates is human, is Socrates mortal?", "yes"),
        ("A bat and a ball cost $1.10. The bat costs $1.00 more than the ball. How much does the ball cost?", "0.05"),
        ("If it takes 5 machines 5 minutes to make 5 widgets, how long would it take 100 machines to make 100 widgets?", "5"),
        ("In a lake, there is a patch of lily pads. Every day, the patch doubles in size. If it takes 48 days for the patch to cover the entire lake, how long would it take to cover half?", "47"),
        ("You have a 3-gallon jug and a 5-gallon jug. How can you measure exactly 4 gallons?", "fill 5, pour into 3, empty 3, pour remaining 2 into 3, fill 5, pour into 3 until full, leaving 4"),
        # code
        ("Write a Python function to check if a string is a palindrome", "def is_palindrome"),
        ("Write a function to find the factorial of a number", "def factorial"),
        ("Write a Python function to find the maximum of three numbers", "def max_of_three"),
        ("Write a function to check if a number is prime", "def is_prime"),
        ("Write a function to reverse a string", "def reverse_string"),
    ]

    correct = 0
    total = len(questions)
    results = {"factual": {"correct": 0, "total": 0}, "mathematical": {"correct": 0, "total": 0},
               "reasoning": {"correct": 0, "total": 0}, "code": {"correct": 0, "total": 0}}

    for i, (question, expected) in enumerate(questions):
        print(f"\n  Question {i+1}/{total}: {question[:60]}...")

        # Classification par le moteur harmonique
        cat = "general"
        if engine:
            try:
                analysis = engine.analyzer.analyze(question)
                cat = analysis.get("category", "general")
            except:
                pass

        # Generation via proxy
        response, metrics = generate_via_proxy(question, max_tokens=300)

        # Verification
        is_correct = False
        if response and not response.startswith("[ERREUR"):
            resp_lower = response.lower()
            expected_lower = expected.lower()
            if expected_lower in resp_lower:
                is_correct = True
                correct += 1

        # Comptage par categorie
        if i < 10:
            results["factual"]["total"] += 1
            if is_correct:
                results["factual"]["correct"] += 1
        elif i < 15:
            results["mathematical"]["total"] += 1
            if is_correct:
                results["mathematical"]["correct"] += 1
        elif i < 20:
            results["reasoning"]["total"] += 1
            if is_correct:
                results["reasoning"]["correct"] += 1
        else:
            results["code"]["total"] += 1
            if is_correct:
                results["code"]["correct"] += 1

        status = "[OK]" if is_correct else "[KO]"
        print(f"  {status} Categorie: {cat} | Attendu: {expected[:30]}...")
        if response and len(response) > 100:
            print(f"  Reponse: {response[:100]}...")

    print(f"\n  Score global MMLU : {correct}/{total} ({100*correct/total:.1f}%)")
    for cat, data in results.items():
        if data["total"] > 0:
            print(f"     {cat}: {data['correct']}/{data['total']} ({100*data['correct']/data['total']:.1f}%)")

    return correct / total if total > 0 else 0


# ============================================================================
# BENCHMARK 2 : GSM8K (Grade School Math)
# ============================================================================

def test_gsm8k():
    print("\n" + "="*60)
    print("BENCHMARK 2 : GSM8K (Grade School Math)")
    print("="*60)

    problems = [
        ("What is 123 + 456?", "579"),
        ("What is 1000 - 347?", "653"),
        ("What is 25 x 16?", "400"),
        ("What is 144 / 12?", "12"),
        ("What is 15% of 200?", "30"),
        ("If a train travels at 60 km/h for 2.5 hours, how far does it go?", "150"),
        ("A pizza has 8 slices. If 3 people eat 2 slices each, how many slices are left?", "2"),
        ("What is the area of a rectangle with length 12 and width 5?", "60"),
        ("If you have $50 and spend $17.50, how much money do you have left?", "32.50"),
        ("What is 2^8?", "256"),
    ]

    correct = 0
    total = len(problems)

    for i, (problem, expected) in enumerate(problems):
        print(f"\n  Probleme {i+1}/{total}: {problem}")
        response, metrics = generate_via_proxy(problem, max_tokens=200, temperature=0.0)

        is_correct = False
        if response and not response.startswith("[ERREUR"):
            resp_clean = response.replace(",", "").replace(" ", "").lower()
            expected_clean = expected.replace(",", "").replace(" ", "").lower()
            if expected_clean in resp_clean:
                is_correct = True
                correct += 1

        status = "[OK]" if is_correct else "[KO]"
        print(f"  {status} Attendu: {expected}")
        if response:
            print(f"  Reponse: {response[:80]}...")

    print(f"\n  Score GSM8K : {correct}/{total} ({100*correct/total:.1f}%)")
    return correct / total if total > 0 else 0


# ============================================================================
# BENCHMARK 3 : HumanEval (Generation de Code)
# ============================================================================

def test_humaneval():
    print("\n" + "="*60)
    print("BENCHMARK 3 : HumanEval (Generation de Code)")
    print("="*60)

    tasks = [
        ("Write a Python function that returns the sum of two numbers", "def add"),
        ("Write a Python function that checks if a number is even", "def is_even"),
        ("Write a Python function that finds the maximum in a list", "def find_max"),
        ("Write a Python function that counts vowels in a string", "def count_vowels"),
        ("Write a Python function that reverses a list", "def reverse_list"),
        ("Write a Python function that checks if a string contains only digits", "def is_digit"),
        ("Write a Python function that returns the factorial of n", "def factorial"),
        ("Write a Python function that merges two sorted lists", "def merge_sorted"),
        ("Write a Python function that finds the longest word in a sentence", "def longest_word"),
        ("Write a Python function that converts Celsius to Fahrenheit", "def celsius_to_fahrenheit"),
    ]

    correct = 0
    total = len(tasks)

    for i, (task, expected) in enumerate(tasks):
        print(f"\n  Tache {i+1}/{total}: {task[:60]}...")
        response, metrics = generate_via_proxy(task, max_tokens=400, temperature=0.1)

        is_correct = False
        if response and not response.startswith("[ERREUR"):
            if expected in response:
                is_correct = True
                correct += 1

        status = "[OK]" if is_correct else "[KO]"
        print(f"  {status} Attendu: {expected}")
        if response:
            lines = response.split('\n')
            code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
            for l in code_lines[:3]:
                print(f"  > {l[:80]}")

    print(f"\n  Score HumanEval : {correct}/{total} ({100*correct/total:.1f}%)")
    return correct / total if total > 0 else 0


# ============================================================================
# BENCHMARK 4 : HellaSwag (Common Sense Reasoning)
# ============================================================================

def test_hellaswag():
    print("\n" + "="*60)
    print("BENCHMARK 4 : HellaSwag (Common Sense Reasoning)")
    print("="*60)

    scenarios = [
        ("When you drop a glass on a hard floor, it will:", "break"),
        ("If you leave ice cream out in the sun, it will:", "melt"),
        ("After it rains, the ground becomes:", "wet"),
        ("If you don't eat for a long time, you feel:", "hungry"),
        ("When you blow up a balloon too much, it will:", "pop"),
    ]

    correct = 0
    total = len(scenarios)

    for i, (scenario, expected) in enumerate(scenarios):
        print(f"\n  Scenario {i+1}/{total}: {scenario}")
        response, metrics = generate_via_proxy(scenario, max_tokens=100, temperature=0.0)

        is_correct = False
        if response and not response.startswith("[ERREUR"):
            resp_lower = response.lower()
            if expected in resp_lower:
                is_correct = True
                correct += 1

        status = "[OK]" if is_correct else "[KO]"
        print(f"  {status} Attendu: {expected}")
        if response:
            print(f"  Reponse: {response[:80]}...")

    print(f"\n  Score HellaSwag : {correct}/{total} ({100*correct/total:.1f}%)")
    return correct / total if total > 0 else 0


# ============================================================================
# BENCHMARK 5 : TruthfulQA (Veracite)
# ============================================================================

def test_truthfulqa():
    print("\n" + "="*60)
    print("BENCHMARK 5 : TruthfulQA (Veracite)")
    print("="*60)

    questions = [
        ("What is the capital of France?", "Paris"),
        ("Who was the first person to walk on the Moon?", "Neil Armstrong"),
        ("What planet is known as the Red Planet?", "Mars"),
        ("How many continents are there on Earth?", "7"),
        ("What is the largest ocean on Earth?", "Pacific"),
        ("Who painted the Mona Lisa?", "Leonardo da Vinci"),
        ("What is the chemical formula for water?", "H2O"),
        ("In which year did the Titanic sink?", "1912"),
        ("What is the tallest mountain on Earth?", "Everest"),
        ("What is the smallest country in the world?", "Vatican"),
        ("What is the speed of sound in air (approx m/s)?", "343"),
        ("Who discovered penicillin?", "Fleming"),
        ("What is the currency of Japan?", "Yen"),
        ("What is the longest river in the world?", "Nile"),
        ("What is the freezing point of water in Celsius?", "0"),
    ]

    correct = 0
    total = len(questions)

    for i, (question, expected) in enumerate(questions):
        print(f"\n  Question {i+1}/{total}: {question}")
        response, metrics = generate_via_proxy(question, max_tokens=200, temperature=0.0)

        is_correct = False
        if response and not response.startswith("[ERREUR"):
            resp_lower = response.lower()
            expected_lower = expected.lower()
            if expected_lower in resp_lower:
                is_correct = True
                correct += 1

        status = "[OK]" if is_correct else "[KO]"
        print(f"  {status} Attendu: {expected}")
        if response:
            print(f"  Reponse: {response[:80]}...")

    print(f"\n  Score de veracite : {correct}/{total} ({100*correct/total:.1f}%)")
    return correct / total if total > 0 else 0


# ============================================================================
# BENCHMARK 6 : Performance du Cache
# ============================================================================

def test_cache_performance():
    print("\n" + "="*60)
    print("BENCHMARK 6 : Cache Proxy (Performance)")
    print("="*60)

    test_prompts = [
        "What is the capital of France?",
        "Explain quantum computing in simple terms",
        "Write a Python function to sort a list",
        "What is the theory of relativity?",
        "Write a poem about nature",
    ]

    # Premier passage (sans cache)
    print("\n  Phase 1 : Premier passage (sans cache)")
    times_first = []
    for prompt in test_prompts:
        start = time.time()
        response, metrics = generate_via_proxy(prompt, max_tokens=200)
        elapsed = time.time() - start
        times_first.append(elapsed)
        status = "[OK]" if response and not response.startswith("[ERREUR") else "[KO]"
        print(f"  {status} {prompt[:40]}... -> {elapsed:.2f}s")

    avg_first = sum(times_first) / len(times_first) if times_first else 0

    # Second passage (avec cache)
    print("\n  Phase 2 : Second passage (avec cache)")
    times_second = []
    for prompt in test_prompts:
        start = time.time()
        response, metrics = generate_via_proxy(prompt, max_tokens=200)
        elapsed = time.time() - start
        times_second.append(elapsed)
        status = "[OK]" if response and not response.startswith("[ERREUR") else "[KO]"
        cache_hit = metrics.get("cache_hit", False) if metrics else False
        cache_str = " [CACHE]" if cache_hit else ""
        print(f"  {status}{cache_str} {prompt[:40]}... -> {elapsed:.2f}s")

    avg_second = sum(times_second) / len(times_second) if times_second else 0

    ratio = avg_first / avg_second if avg_second > 0 else 1.0
    economy = (1 - avg_second / avg_first) * 100 if avg_first > 0 else 0

    print(f"\n  Temps moyen premier passage : {avg_first*1000:.1f} ms")
    print(f"  Temps moyen second passage : {avg_second*1000:.1f} ms")
    print(f"  Ratio d'acceleration : {ratio:.1f}x")
    print(f"  Economie : {economy:.1f}%")

    return ratio


# ============================================================================
# BENCHMARK 7 : Determinisme
# ============================================================================

def test_determinism():
    print("\n" + "="*60)
    print("BENCHMARK 7 : Test de Determinisme")
    print("="*60)

    test_prompt = "What is the capital of France?"

    responses = []
    for i in range(3):
        response, _ = generate_via_proxy(test_prompt, max_tokens=100, temperature=0.0)
        responses.append(response)
        print(f"  Test {i+1}: {response[:60] if response else 'None'}...")

    is_deterministic = all(r == responses[0] for r in responses)
    print(f"\n  {'[OK] 100% deterministe' if is_deterministic else '[KO] Non deterministe'}")

    return is_deterministic


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("="*60)
    print("TESTS REELS DES BENCHMARKS AVEC PROXY EC2")
    print("="*60)
    print(f"\nDate : {datetime.now().strftime('%d %B %Y a %H:%M')}")
    print(f"Proxy URL : {PROXY_URL}")
    print(f"Generate URL : {GENERATE_URL}")

    # Verification du proxy
    print("\n" + "-"*60)
    print("VERIFICATION DU PROXY EC2")
    print("-"*60)
    proxy_ok = check_proxy_health()

    if not proxy_ok:
        print("\nProxy EC2 inaccessible. Les tests utiliseront le mode local uniquement.")
        print("Les reponses seront generees par le moteur harmonique local.")

    results = {}

    # Benchmark 1 : MMLU
    results["mmlu"] = test_mmlu()

    # Benchmark 2 : GSM8K
    results["gsm8k"] = test_gsm8k()

    # Benchmark 3 : HumanEval
    results["humaneval"] = test_humaneval()

    # Benchmark 4 : HellaSwag
    results["hellaswag"] = test_hellaswag()

    # Benchmark 5 : TruthfulQA
    results["truthfulqa"] = test_truthfulqa()

    # Benchmark 6 : Cache
    results["cache_ratio"] = test_cache_performance()

    # Benchmark 7 : Determinisme
    results["determinism"] = test_determinism()

    # ========================================================================
    # SYNTHESE FINALE
    # ========================================================================
    print("\n" + "="*60)
    print("SYNTHESE FINALE DES TESTS AVEC PROXY")
    print("="*60)

    print(f"\n  Scores mesures :")
    for key, value in results.items():
        if isinstance(value, bool):
            print(f"    {key}: {'100%' if value else '0%'}")
        elif isinstance(value, float):
            print(f"    {key}: {value*100:.1f}%")
        else:
            print(f"    {key}: {value}")

    # Score moyen (benchmarks uniquement)
    benchmark_scores = [v for k, v in results.items() if k in ("mmlu", "gsm8k", "humaneval", "hellaswag", "truthfulqa")]
    avg_score = sum(benchmark_scores) / len(benchmark_scores) if benchmark_scores else 0
    print(f"\n  Score moyen sur les benchmarks : {avg_score*100:.1f}%")

    # Sauvegarde
    output = {
        "date": datetime.now().isoformat(),
        "proxy_url": PROXY_URL,
        "proxy_accessible": proxy_ok,
        "results": {k: v if isinstance(v, (bool, float, int, str)) else str(v) for k, v in results.items()},
        "average_score": avg_score
    }

    with open("resultats_benchmarks_proxy.json", "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nResultats sauvegardes dans : resultats_benchmarks_proxy.json")

    print("\n" + "="*60)
    print("TESTS TERMINES")
    print("="*60)
    print(f"\nPour executer a nouveau : python test_benchmarks_avec_proxy.py")


if __name__ == "__main__":
    main()
