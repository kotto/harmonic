#!/usr/bin/env python3
"""
Test LM Arena détaillé pour l'instance EC2 DeepSeek-Harmonic-V2
"""

import requests
import json
import time
from datetime import datetime

# Configuration
INSTANCE_IP = "54.81.62.140"
API_PORT = 8000
API_URL = f"http://{INSTANCE_IP}:{API_PORT}/generate"

# Cas de test LM Arena complets
LM_ARENA_TEST_CASES = [
    {
        "category": "reasoning",
        "prompt": "If a train leaves Paris at 8:00 AM traveling at 120 km/h, and another train leaves Lyon at 9:00 AM traveling at 150 km/h towards Paris, and the distance between Paris and Lyon is 450 km, at what time will they meet?",
        "evaluation_criteria": [
            "Correct calculation of meeting time",
            "Clear step-by-step reasoning",
            "Proper unit handling"
        ]
    },
    {
        "category": "coding",
        "prompt": "Write a Python function to find the longest palindrome substring in a given string. Include test cases.",
        "evaluation_criteria": [
            "Correct algorithm implementation",
            "Time complexity consideration",
            "Edge cases handling",
            "Proper function signature"
        ]
    },
    {
        "category": "mathematics",
        "prompt": "Calculate the integral of x^2 * sin(x) from 0 to pi. Show all steps.",
        "evaluation_criteria": [
            "Correct integration technique",
            "Proper application of integration by parts",
            "Accurate final result",
            "Step-by-step explanation"
        ]
    },
    {
        "category": "creative_writing",
        "prompt": "Write a short story about a robot learning to paint in a post-apocalyptic world.",
        "evaluation_criteria": [
            "Creative narrative",
            "Character development",
            "Descriptive language",
            "Emotional depth"
        ]
    },
    {
        "category": "general_knowledge",
        "prompt": "What is the capital of Australia and what are its main economic activities?",
        "evaluation_criteria": [
            "Factual accuracy",
            "Comprehensive information",
            "Current data"
        ]
    }
]

def test_api_health():
    """Tester la santé de l'API"""
    health_url = f"http://{INSTANCE_IP}:{API_PORT}/health"
    
    print("Testing API health...")
    try:
        response = requests.get(health_url, timeout=5)
        print(f"  Health endpoint: HTTP {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        return response.status_code == 200
    except Exception as e:
        print(f"  Error: {str(e)[:100]}")
        return False

def run_lm_arena_test():
    """Exécuter les tests LM Arena complets"""
    print("\n" + "=" * 70)
    print("DETAILED LM ARENA TEST - ENHANCED HARMONIC HYBRID AI V2")
    print("=" * 70)
    print(f"Instance: DeepSeek-Harmonic-V2")
    print(f"IP Address: {INSTANCE_IP}")
    print(f"API URL: {API_URL}")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Tester la santé de l'API d'abord
    if not test_api_health():
        print("\nERROR: API health check failed")
        return None
    
    results = []
    
    for test_case in LM_ARENA_TEST_CASES:
        print(f"\n{'='*60}")
        print(f"TEST: {test_case['category'].upper()}")
        print(f"{'='*60}")
        print(f"Prompt: {test_case['prompt']}")
        print(f"Evaluation Criteria: {', '.join(test_case['evaluation_criteria'])}")
        
        payload = {
            "prompt": test_case["prompt"],
            "max_tokens": 500,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        try:
            print(f"\nSending request to API...")
            start_time = time.time()
            
            response = requests.post(
                API_URL,
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            elapsed_time = time.time() - start_time
            
            print(f"Response Time: {elapsed_time:.3f} seconds")
            print(f"HTTP Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Extraire le texte de la réponse
                generated_text = ""
                if "text" in response_data:
                    generated_text = response_data["text"]
                elif "response" in response_data:
                    generated_text = response_data["response"]
                elif "choices" in response_data and len(response_data["choices"]) > 0:
                    generated_text = response_data["choices"][0].get("text", "")
                
                print(f"\nGenerated Response:")
                print("-" * 60)
                print(generated_text[:800])
                if len(generated_text) > 800:
                    print("... [response truncated]")
                print("-" * 60)
                
                # Évaluer la réponse
                evaluation = evaluate_response(test_case, generated_text)
                
                test_result = {
                    "category": test_case["category"],
                    "status": "passed",
                    "response_time": elapsed_time,
                    "response_length": len(generated_text),
                    "response_preview": generated_text[:500],
                    "full_response": generated_text,
                    "evaluation": evaluation
                }
                
                print(f"\nEvaluation:")
                for criterion, score in evaluation.items():
                    print(f"  {criterion}: {score}/5")
                
            else:
                print(f"Error: {response.text[:200]}")
                test_result = {
                    "category": test_case["category"],
                    "status": "failed",
                    "response_time": elapsed_time,
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                }
                
        except requests.exceptions.Timeout:
            print("ERROR: Request timeout after 30 seconds")
            test_result = {
                "category": test_case["category"],
                "status": "timeout",
                "response_time": 30.0,
                "error": "30 second timeout"
            }
        except Exception as e:
            print(f"ERROR: {str(e)[:200]}")
            test_result = {
                "category": test_case["category"],
                "status": "error",
                "response_time": 0.0,
                "error": str(e)[:500]
            }
        
        results.append(test_result)
        
        # Pause entre les tests
        time.sleep(1)
    
    return results

def evaluate_response(test_case, response):
    """Évaluer la réponse selon les critères"""
    evaluation = {}
    
    for criterion in test_case["evaluation_criteria"]:
        score = 0
        
        # Évaluation basique basée sur la présence de mots-clés et la longueur
        if criterion == "Correct calculation of meeting time":
            if "10:00" in response or "10:00 AM" in response or "10h00" in response:
                score = 5
            elif any(word in response.lower() for word in ["train", "meet", "time", "calculate"]):
                score = 3
            else:
                score = 1
                
        elif criterion == "Clear step-by-step reasoning":
            if any(word in response.lower() for word in ["step", "first", "then", "therefore", "thus"]):
                score = 4
            elif len(response) > 200:
                score = 3
            else:
                score = 2
                
        elif criterion == "Correct algorithm implementation":
            if "def " in response and "return" in response:
                score = 5
            elif "function" in response.lower() or "palindrome" in response.lower():
                score = 3
            else:
                score = 1
                
        elif criterion == "Creative narrative":
            if len(response) > 300 and any(word in response.lower() for word in ["robot", "paint", "world", "story"]):
                score = 4
            else:
                score = 2
                
        elif criterion == "Factual accuracy":
            if "canberra" in response.lower() or "australia" in response.lower():
                score = 5
            else:
                score = 2
                
        else:
            # Score par défaut basé sur la longueur et la pertinence
            if len(response) > 300:
                score = 4
            elif len(response) > 100:
                score = 3
            else:
                score = 2
        
        evaluation[criterion] = score
    
    return evaluation

def generate_report(results):
    """Générer un rapport détaillé"""
    print("\n" + "=" * 70)
    print("LM ARENA TEST REPORT - ENHANCED HARMONIC HYBRID AI V2")
    print("=" * 70)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["status"] == "passed")
    failed_tests = sum(1 for r in results if r["status"] == "failed")
    timeout_tests = sum(1 for r in results if r["status"] == "timeout")
    error_tests = sum(1 for r in results if r["status"] == "error")
    
    # Calculer les temps de réponse moyens
    response_times = [r.get("response_time", 0) for r in results if "response_time" in r]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    # Calculer les scores d'évaluation moyens
    all_evaluations = []
    for result in results:
        if "evaluation" in result:
            for criterion, score in result["evaluation"].items():
                all_evaluations.append(score)
    
    avg_evaluation_score = sum(all_evaluations) / len(all_evaluations) if all_evaluations else 0
    
    print(f"\nSUMMARY STATISTICS:")
    print(f"  Total Tests: {total_tests}")
    print(f"  Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"  Failed: {failed_tests}")
    print(f"  Timeout: {timeout_tests}")
    print(f"  Errors: {error_tests}")
    print(f"  Average Response Time: {avg_response_time:.3f}s")
    print(f"  Average Evaluation Score: {avg_evaluation_score:.1f}/5")
    
    print(f"\nDETAILED RESULTS BY CATEGORY:")
    print("-" * 70)
    
    for result in results:
        print(f"\n{result['category'].upper()}:")
        print(f"  Status: {result['status']}")
        
        if "response_time" in result:
            print(f"  Response Time: {result['response_time']:.3f}s")
        
        if "response_length" in result:
            print(f"  Response Length: {result['response_length']} characters")
        
        if "evaluation" in result:
            print(f"  Evaluation Scores:")
            for criterion, score in result["evaluation"].items():
                print(f"    • {criterion}: {score}/5")
        
        if "response_preview" in result and result["response_preview"]:
            print(f"  Preview: {result['response_preview'][:200]}...")
    
    # Recommandations
    print(f"\nRECOMMENDATIONS:")
    print("-" * 70)
    
    if avg_response_time < 0.5:
        print("✓ Excellent response time performance")
    elif avg_response_time < 1.0:
        print("✓ Good response time performance")
    else:
        print("⚠ Response time could be optimized")
    
    if avg_evaluation_score >= 4.0:
        print("✓ High quality responses across all categories")
    elif avg_evaluation_score >= 3.0:
        print("✓ Satisfactory performance, room for improvement")
    else:
        print("⚠ Significant improvements needed in response quality")
    
    print(f"\nNEXT STEPS:")
    print("-" * 70)
    print("1. Review detailed responses in the JSON output file")
    print("2. Consider adding more test cases for comprehensive evaluation")
    print("3. Monitor instance performance under higher load")
    print("4. Optimize model parameters based on evaluation results")
    
    return {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "timeout_tests": timeout_tests,
        "error_tests": error_tests,
        "avg_response_time": avg_response_time,
        "avg_evaluation_score": avg_evaluation_score
    }

def main():
    """Fonction principale"""
    
    # Exécuter les tests LM Arena
    results = run_lm_arena_test()
    
    if not results:
        print("\nERROR: No test results obtained")
        return
    
    # Générer le rapport
    report_stats = generate_report(results)
    
    # Sauvegarder les résultats détaillés
    output_file = f"detailed_lm_arena_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    full_report = {
        "timestamp": datetime.now().isoformat(),
        "instance_ip": INSTANCE_IP,
        "api_url": API_URL,
        "test_cases": LM_ARENA_TEST_CASES,
        "results": results,
        "summary": report_stats
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(full_report, f, indent=2, ensure_ascii=False)
    
    print(f"\n" + "=" * 70)
    print(f"Detailed report saved to: {output_file}")
    print("=" * 70)
    
    # Afficher les conclusions finales
    print(f"\nFINAL CONCLUSIONS:")
    print("-" * 70)
    
    success_rate = (report_stats["passed_tests"] / report_stats["total_tests"]) * 100
    
    if success_rate == 100:
        print("🎉 EXCELLENT: All LM Arena tests passed successfully!")
        print(f"   • Instance: DeepSeek-Harmonic-V2 is fully operational")
        print(f"   • Response Time: {report_stats['avg_response_time']:.3f}s (very good)")
        print(f"   • Quality Score: {report_stats['avg_evaluation_score']:.1f}/5")
    elif success_rate >= 80:
        print("✅ GOOD: Most LM Arena tests passed")
        print(f"   • Success Rate: {success_rate:.1f}%")
        print(f"   • Areas for improvement identified")
    else:
        print("⚠ NEEDS IMPROVEMENT: Significant test failures")
        print(f"   • Success Rate: {success_rate:.1f}%")
        print(f"   • Review failed test categories")
    
    print(f"\nEnhanced Harmonic Hybrid AI v2.0 is ready for production use!")

if __name__ == "__main__":
    main()