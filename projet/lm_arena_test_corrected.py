#!/usr/bin/env python3
"""
LM ARENA TEST CORRECTED - DEEPSEEK HARMONIC V2
Tests LM Arena corriges
"""

import requests
import time
import json
from datetime import datetime

def test_api_comprehensive():
    """Test complet de l'API"""
    instance_ip = "54.81.62.140"
    port = 8000
    base_url = f"http://{instance_ip}:{port}"
    
    print("=" * 60)
    print("LM ARENA COMPREHENSIVE TEST - DEEPSEEK HARMONIC V2")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Instance: {instance_ip}:{port}")
    print()
    
    all_results = []
    start_time = time.time()
    
    # Test 1: Health endpoint
    print("1. HEALTH ENDPOINT TEST")
    print("-" * 40)
    
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: HTTP {response.status_code}")
            print(f"   Version: {data.get('version', 'N/A')}")
            print(f"   Models: {data.get('total_models', 'N/A')}")
            print("   RESULT: PASS")
            health_ok = True
        else:
            print(f"   Status: HTTP {response.status_code}")
            print("   RESULT: FAIL")
            health_ok = False
            
    except Exception as e:
        print(f"   Error: {e}")
        print("   RESULT: FAIL")
        health_ok = False
    
    if not health_ok:
        print("\nERROR: Health check failed. Cannot continue.")
        return False
    
    # Test 2: Generate endpoint avec differents types de prompts
    test_categories = [
        {
            "name": "REASONING",
            "tests": [
                {"name": "Logical reasoning", "prompt": "If all cats are mammals, and all mammals are animals, are all cats animals? Explain step by step."},
                {"name": "Mathematical reasoning", "prompt": "A train leaves Paris at 8:00 AM at 120 km/h. Another leaves Lyon at 9:00 AM at 150 km/h towards Paris. Distance is 450 km. When will they meet? Show calculations."},
                {"name": "Spatial reasoning", "prompt": "You face north. Turn 90 right, 180 left, 270 right. Which direction now? Explain each step."}
            ]
        },
        {
            "name": "CODING", 
            "tests": [
                {"name": "Python algorithm", "prompt": "Write Python function to find longest palindrome substring. Include complexity analysis."},
                {"name": "Data structure", "prompt": "Implement LRU cache in Python with O(1) time for get and put operations."},
                {"name": "Code optimization", "prompt": "Optimize Python prime number function for performance. Explain optimizations."}
            ]
        },
        {
            "name": "MATHEMATICS",
            "tests": [
                {"name": "Calculus", "prompt": "Calculate integral of x^2 * sin(x) from 0 to pi. Show step-by-step."},
                {"name": "Linear algebra", "prompt": "Find eigenvalues and eigenvectors of matrix [[2, 1], [1, 2]]. Show calculations."},
                {"name": "Probability", "prompt": "Flip fair coin 10 times. Probability of exactly 5 heads? Show binomial calculation."}
            ]
        },
        {
            "name": "CREATIVE",
            "tests": [
                {"name": "Story writing", "prompt": "Write short sci-fi story about AI solving all human problems but at what cost? (300 words)"},
                {"name": "Poetry", "prompt": "Write poem about beauty of mathematics and connection to natural world."},
                {"name": "Essay", "prompt": "Write essay on ethical implications of advanced AI like DeepSeek Harmonic V2. (500 words)"}
            ]
        }
    ]
    
    total_tests = 0
    passed_tests = 0
    mock_detected = False
    
    for category in test_categories:
        print(f"\n{category['name']} TESTS")
        print("-" * 40)
        
        for test in category['tests']:
            total_tests += 1
            print(f"\n   Test: {test['name']}")
            print(f"   Prompt: {test['prompt'][:60]}...")
            
            try:
                url = f"{base_url}/generate"
                payload = {
                    "prompt": test['prompt'],
                    "max_tokens": 400,
                    "temperature": 0.7
                }
                
                test_start = time.time()
                response = requests.post(url, json=payload, timeout=30)
                elapsed = time.time() - test_start
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("content", "")
                    
                    # Verifier si reponse mock
                    if "Generated response for:" in content or "mock" in content.lower():
                        print(f"   Result: FAIL - MOCK response ({elapsed:.2f}s)")
                        mock_detected = True
                        result_status = "FAIL_MOCK"
                    else:
                        print(f"   Result: PASS - REAL response ({elapsed:.2f}s, {len(content)} chars)")
                        passed_tests += 1
                        result_status = "PASS_REAL"
                        
                    # Enregistrer resultat
                    all_results.append({
                        "category": category['name'],
                        "test": test['name'],
                        "status": result_status,
                        "time": elapsed,
                        "chars": len(content),
                        "version": data.get("version", "N/A")
                    })
                    
                else:
                    print(f"   Result: FAIL - HTTP {response.status_code} ({elapsed:.2f}s)")
                    all_results.append({
                        "category": category['name'],
                        "test": test['name'],
                        "status": f"FAIL_HTTP_{response.status_code}",
                        "time": elapsed,
                        "chars": 0,
                        "version": "N/A"
                    })
                    
            except Exception as e:
                print(f"   Result: FAIL - Error: {e}")
                all_results.append({
                    "category": category['name'],
                    "test": test['name'],
                    "status": f"FAIL_ERROR",
                    "time": 0,
                    "chars": 0,
                    "version": "N/A"
                })
    
    # Analyse des resultats
    print("\n" + "=" * 60)
    print("ANALYSIS OF RESULTS")
    print("=" * 60)
    
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\nTotal tests: {total_tests}")
    print(f"Passed tests: {passed_tests} ({pass_rate:.1f}%)")
    print(f"Failed tests: {total_tests - passed_tests}")
    print(f"Mock responses detected: {'YES' if mock_detected else 'NO'}")
    
    # Analyse par categorie
    print("\nBreakdown by category:")
    for category in test_categories:
        cat_tests = [r for r in all_results if r['category'] == category['name']]
        cat_passed = sum(1 for r in cat_tests if r['status'].startswith('PASS'))
        cat_total = len(cat_tests)
        cat_rate = (cat_passed / cat_total * 100) if cat_total > 0 else 0
        
        print(f"  {category['name']:12}: {cat_passed}/{cat_total} ({cat_rate:.1f}%)")
    
    # Sauvegarder les resultats
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"lm_arena_analysis_{timestamp}.json"
    
    data = {
        "metadata": {
            "test_date": datetime.now().isoformat(),
            "instance": f"{instance_ip}:{port}",
            "duration": time.time() - start_time,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "pass_rate": pass_rate,
            "mock_detected": mock_detected
        },
        "results": all_results
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {filename}")
    
    # Conclusion
    print("\n" + "=" * 60)
    print("FINAL CONCLUSION")
    print("=" * 60)
    
    total_time = time.time() - start_time
    print(f"Total test time: {total_time:.2f} seconds")
    
    if mock_detected:
        print("\nCONCLUSION: API IS RETURNING MOCK RESPONSES")
        print("This indicates the OLD version is still running.")
        print()
        print("REQUIRED ACTIONS:")
        print("1. Deploy the real version using manual instructions")
        print("2. Check if EC2 instance needs to be restarted")
        print("3. Verify API returns real harmonic AI responses")
        print()
        print("Manual deployment instructions:")
        print("  scp -i ~/.ssh/deepseek_ec2 deepseek_api_real_paramiko.py ubuntu@54.81.62.140:/home/ubuntu/")
        print("  ssh -i ~/.ssh/deepseek_ec2 ubuntu@54.81.62.140")
        print("  pip3 install fastapi uvicorn pydantic")
        print("  python3 deepseek_api_real_paramiko.py")
        return False
    else:
        print("\nCONCLUSION: API IS RETURNING REAL RESPONSES")
        print("The DeepSeek Harmonic V2 Real API is operational.")
        print()
        print("NEXT STEPS:")
        print("1. Submit results to LM Arena platform")
        print("2. Run additional benchmark tests")
        print("3. Monitor performance and quality metrics")
        return True

def main():
    """Fonction principale"""
    print("LM ARENA EVALUATION - DEEPSEEK HARMONIC V2")
    print("Testing API at 54.81.62.140:8000")
    print()
    
    success = test_api_comprehensive()
    
    print("\n" + "=" * 60)
    print("EVALUATION COMPLETED")
    print("=" * 60)
    
    if success:
        print("SUCCESS: API is ready for LM Arena benchmarks.")
    else:
        print("ISSUE: API needs to be updated with real responses.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)