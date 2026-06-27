#!/usr/bin/env python3
"""
LM ARENA TEST FINAL - DEEPSEEK HARMONIC V2
Tests complets LM Arena pour evaluer l'API
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, List, Tuple

class LMArenaTester:
    """Testeur LM Arena complet"""
    
    def __init__(self, instance_ip: str = "__EC2_IP__", port: int = 8000):
        self.instance_ip = instance_ip
        self.port = port
        self.base_url = f"http://{instance_ip}:{port}"
        self.results = []
        self.start_time = None
        
    def test_health(self) -> bool:
        """Tester le health endpoint"""
        print("1. TEST HEALTH ENDPOINT")
        print("-" * 40)
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Status: HTTP {response.status_code}")
                print(f"   Version: {data.get('version', 'N/A')}")
                print(f"   Models: {data.get('total_models', 'N/A')}")
                print(f"   Parallel: {data.get('parallel_mode', 'N/A')}")
                print(f"   Multi-modal: {data.get('multi_modal', 'N/A')}")
                print("   RESULT: PASS")
                return True
            else:
                print(f"   Status: HTTP {response.status_code}")
                print(f"   Error: {response.text}")
                print("   RESULT: FAIL")
                return False
                
        except Exception as e:
            print(f"   Error: {e}")
            print("   RESULT: FAIL")
            return False
    
    def test_generate(self, prompt: str, test_name: str, max_tokens: int = 500) -> Tuple[bool, str]:
        """Tester le generate endpoint"""
        try:
            url = f"{self.base_url}/generate"
            payload = {
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": 0.0,
                "arena_mode": True
            }
            
            start_time = time.time()
            response = requests.post(url, json=payload, timeout=30)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", "")
                
                # Verifier si c'est une reponse mock
                is_mock = "Generated response for:" in content or "mock" in content.lower()
                
                if is_mock:
                    return False, f"MOCK response detected ({elapsed:.2f}s)"
                else:
                    return True, f"REAL response ({elapsed:.2f}s, {len(content)} chars)"
            else:
                return False, f"HTTP {response.status_code} ({elapsed:.2f}s)"
                
        except Exception as e:
            return False, f"Error: {e}"
    
    def run_reasoning_tests(self) -> List[Dict]:
        """Executer les tests de raisonnement"""
        print("\n2. REASONING TESTS")
        print("-" * 40)
        
        reasoning_tests = [
            {
                "name": "Logical reasoning",
                "prompt": "If all cats are mammals, and all mammals are animals, are all cats animals? Explain your reasoning step by step."
            },
            {
                "name": "Mathematical reasoning", 
                "prompt": "A train leaves Paris at 8:00 AM traveling at 120 km/h. Another train leaves Lyon at 9:00 AM traveling at 150 km/h towards Paris. The distance between Paris and Lyon is 450 km. At what time will the two trains meet? Show your calculations."
            },
            {
                "name": "Spatial reasoning",
                "prompt": "You are facing north. You turn 90 degrees to the right, then 180 degrees to the left, then 270 degrees to the right. Which direction are you facing now? Explain each step."
            }
        ]
        
        results = []
        
        for test in reasoning_tests:
            print(f"\n   Test: {test['name']}")
            print(f"   Prompt: {test['prompt'][:80]}...")
            
            success, details = self.test_generate(test['prompt'], test['name'])
            
            if success:
                print(f"   Result: PASS - {details}")
                results.append({
                    "test": test['name'],
                    "status": "PASS",
                    "details": details,
                    "type": "reasoning"
                })
            else:
                print(f"   Result: FAIL - {details}")
                results.append({
                    "test": test['name'], 
                    "status": "FAIL",
                    "details": details,
                    "type": "reasoning"
                })
        
        return results
    
    def run_coding_tests(self) -> List[Dict]:
        """Executer les tests de codage"""
        print("\n3. CODING TESTS")
        print("-" * 40)
        
        coding_tests = [
            {
                "name": "Python algorithm",
                "prompt": "Write a Python function to find the longest palindrome substring in a given string. Include time and space complexity analysis."
            },
            {
                "name": "Data structure",
                "prompt": "Implement a LRU (Least Recently Used) cache in Python with O(1) time complexity for get and put operations."
            },
            {
                "name": "Code optimization",
                "prompt": "Given a Python function that calculates prime numbers up to N, optimize it for performance and explain your optimizations."
            }
        ]
        
        results = []
        
        for test in coding_tests:
            print(f"\n   Test: {test['name']}")
            print(f"   Prompt: {test['prompt'][:80]}...")
            
            success, details = self.test_generate(test['prompt'], test['name'])
            
            if success:
                print(f"   Result: PASS - {details}")
                results.append({
                    "test": test['name'],
                    "status": "PASS", 
                    "details": details,
                    "type": "coding"
                })
            else:
                print(f"   Result: FAIL - {details}")
                results.append({
                    "test": test['name'],
                    "status": "FAIL",
                    "details": details,
                    "type": "coding"
                })
        
        return results
    
    def run_mathematics_tests(self) -> List[Dict]:
        """Executer les tests de mathematiques"""
        print("\n4. MATHEMATICS TESTS")
        print("-" * 40)
        
        math_tests = [
            {
                "name": "Calculus",
                "prompt": "Calculate the integral of x^2 * sin(x) from 0 to pi. Show step-by-step integration."
            },
            {
                "name": "Linear algebra",
                "prompt": "Find the eigenvalues and eigenvectors of the matrix [[2, 1], [1, 2]]. Show your calculations."
            },
            {
                "name": "Probability",
                "prompt": "If you flip a fair coin 10 times, what is the probability of getting exactly 5 heads? Show the binomial distribution calculation."
            }
        ]
        
        results = []
        
        for test in math_tests:
            print(f"\n   Test: {test['name']}")
            print(f"   Prompt: {test['prompt'][:80]}...")
            
            success, details = self.test_generate(test['prompt'], test['name'])
            
            if success:
                print(f"   Result: PASS - {details}")
                results.append({
                    "test": test['name'],
                    "status": "PASS",
                    "details": details,
                    "type": "mathematics"
                })
            else:
                print(f"   Result: FAIL - {details}")
                results.append({
                    "test": test['name'],
                    "status": "FAIL",
                    "details": details,
                    "type": "mathematics"
                })
        
        return results
    
    def run_creative_tests(self) -> List[Dict]:
        """Executer les tests creatifs"""
        print("\n5. CREATIVE TESTS")
        print("-" * 40)
        
        creative_tests = [
            {
                "name": "Story writing",
                "prompt": "Write a short science fiction story about a world where AI has solved all human problems, but at what cost? (300-400 words)"
            },
            {
                "name": "Poetry",
                "prompt": "Write a poem about the beauty of mathematics and its connection to the natural world."
            },
            {
                "name": "Essay",
                "prompt": "Write an essay on the ethical implications of advanced AI systems like DeepSeek Harmonic V2. (500 words)"
            }
        ]
        
        results = []
        
        for test in creative_tests:
            print(f"\n   Test: {test['name']}")
            print(f"   Prompt: {test['prompt'][:80]}...")
            
            success, details = self.test_generate(test['prompt'], test['name'])
            
            if success:
                print(f"   Result: PASS - {details}")
                results.append({
                    "test": test['name'],
                    "status": "PASS",
                    "details": details,
                    "type": "creative"
                })
            else:
                print(f"   Result: FAIL - {details}")
                results.append({
                    "test": test['name'],
                    "status": "FAIL",
                    "details": details,
                    "type": "creative"
                })
        
        return results
    
    def analyze_results(self, all_results: List[Dict]) -> Dict:
        """Analyser les resultats"""
        print("\n" + "=" * 60)
        print("ANALYSIS OF RESULTS")
        print("=" * 60)
        
        total_tests = len(all_results)
        passed_tests = sum(1 for r in all_results if r['status'] == 'PASS')
        failed_tests = total_tests - passed_tests
        
        # Analyser par type
        by_type = {}
        for result in all_results:
            test_type = result['type']
            if test_type not in by_type:
                by_type[test_type] = {'total': 0, 'passed': 0}
            
            by_type[test_type]['total'] += 1
            if result['status'] == 'PASS':
                by_type[test_type]['passed'] += 1
        
        # Afficher les statistiques
        print(f"\nTOTAL TESTS: {total_tests}")
        print(f"PASSED: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"FAILED: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        
        print("\nBREAKDOWN BY CATEGORY:")
        for test_type, stats in by_type.items():
            passed = stats['passed']
            total = stats['total']
            percentage = passed/total*100 if total > 0 else 0
            print(f"  {test_type:12}: {passed}/{total} ({percentage:.1f}%)")
        
        # Determiner le statut global
        mock_responses = any("MOCK response" in r['details'] for r in all_results)
        
        analysis = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "pass_rate": passed_tests/total_tests*100 if total_tests > 0 else 0,
            "mock_responses_detected": mock_responses,
            "by_type": by_type,
            "timestamp": datetime.now().isoformat(),
            "instance_ip": self.instance_ip,
            "port": self.port
        }
        
        return analysis
    
    def save_results(self, all_results: List[Dict], analysis: Dict):
        """Sauvegarder les resultats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"lm_arena_results_{timestamp}.json"
        
        data = {
            "metadata": {
                "test_date": datetime.now().isoformat(),
                "instance": f"{self.instance_ip}:{self.port}",
                "duration": time.time() - self.start_time if self.start_time else 0
            },
            "results": all_results,
            "analysis": analysis
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {filename}")
        return filename
    
    def run_all_tests(self) -> bool:
        """Executer tous les tests"""
        print("=" * 60)
        print("LM ARENA COMPREHENSIVE TEST - DEEPSEEK HARMONIC V2")
        print("=" * 60)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Instance: {self.instance_ip}:{self.port}")
        print()
        
        self.start_time = time.time()
        all_results = []
        
        # Test health
        health_ok = self.test_health()
        if not health_ok:
            print("\nERROR: Health check failed. Cannot continue.")
            return False
        
        # Run all test categories
        reasoning_results = self.run_reasoning_tests()
        all_results.extend(reasoning_results)
        
        coding_results = self.run_coding_tests()
        all_results.extend(coding_results)
        
        math_results = self.run_mathematics_tests()
        all_results.extend(math_results)
        
        creative_results = self.run_creative_tests()
        all_results.extend(creative_results)
        
        # Analyze results
        analysis = self.analyze_results(all_results)
        
        # Save results
        self.save_results(all_results, analysis)
        
        # Final verdict
        print("\n" + "=" * 60)
        print("FINAL VERDICT")
        print("=" * 60)
        
        total_time = time.time() - self.start_time
        print(f"Total test time: {total_time:.2f} seconds")
        
        if analysis['mock_responses_detected']:
            print("\nCONCLUSION: API IS RETURNING MOCK RESPONSES")
            print("This is the OLD version that needs to be replaced.")
            print()
            print("REQUIRED ACTIONS:")
            print("1. Deploy the real version manually using instructions")
            print("2. Or restart the EC2 instance with the correct image")
            print("3. Verify the API returns real harmonic AI responses")
            return False
        else:
            print("\nCONCLUSION: API IS RETURNING REAL RESPONSES")
            print("The DeepSeek Harmonic V2 Real API is working correctly.")
            print()
            print("NEXT STEPS:")
            print("1. Submit these results to LM Arena platform")
            print("2. Continue with additional benchmark tests")
            print("3. Monitor API performance and quality")
            return True

def main():
    """Fonction principale"""
    tester = LMArenaTester()
    success = tester.run_all_tests()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)
    
    if success:
        print("LM Arena tests completed successfully.")
        print("The API is ready for benchmark submission.")
    else:
        print("LM Arena tests failed.")
        print("The API needs to be updated with real responses.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
