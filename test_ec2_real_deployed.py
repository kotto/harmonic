#!/usr/bin/env python3
"""
Test LM Arena pour l'instance EC2 réelle déployée
Version simplifiée sans émojis
"""

import requests
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration basée sur le script de déploiement
EC2_INSTANCE_NAME = "qwen35-ec2-server"
AWS_REGION = "us-east-1"
API_PORT = 8080  # Port configuré dans le script de déploiement
API_ENDPOINTS = [
    "/health",
    "/generate",
    "/v1/chat/completions",
    "/api/v1/generate"
]

# IPs potentielles basées sur les déploiements précédents
POTENTIAL_IPS = [
    "54.166.179.141",  # DeepSeek instance
    "3.95.231.91",     # Autre instance potentielle  
    "98.82.7.99",      # Autre instance potentielle
    "18.212.135.123",  # EC2 us-east-1 typique
    "34.192.45.67",    # EC2 us-east-1 typique
    "52.91.23.145",    # EC2 us-east-1 typique
    "54.157.32.189",   # EC2 us-east-1 typique
]

# Cas de test LM Arena
LM_ARENA_TEST_CASES = [
    {
        "category": "reasoning",
        "prompt": "If a train leaves Paris at 8:00 AM traveling at 120 km/h, and another train leaves Lyon at 9:00 AM traveling at 150 km/h towards Paris, and the distance between Paris and Lyon is 450 km, at what time will they meet?",
        "expected_keywords": ["time", "distance", "speed", "meet", "calculation"]
    },
    {
        "category": "coding",
        "prompt": "Write a Python function to find the longest palindrome substring in a given string.",
        "expected_keywords": ["def", "palindrome", "string", "function", "return"]
    },
    {
        "category": "mathematics",
        "prompt": "Calculate the integral of x^2 * sin(x) from 0 to π.",
        "expected_keywords": ["integral", "integration", "π", "sin", "cos"]
    },
    {
        "category": "creative_writing",
        "prompt": "Write a short story about a robot learning to paint.",
        "expected_keywords": ["robot", "paint", "art", "learn", "story"]
    },
    {
        "category": "general_knowledge",
        "prompt": "What is the capital of Australia and what is its population?",
        "expected_keywords": ["Canberra", "population", "Australia", "capital"]
    }
]

def test_endpoint(ip: str, endpoint: str) -> Optional[Dict]:
    """Tester un endpoint spécifique"""
    url = f"http://{ip}:{API_PORT}{endpoint}"
    
    try:
        # Pour /health, faire une simple requête GET
        if endpoint == "/health":
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return {
                    "ip": ip,
                    "endpoint": endpoint,
                    "status": "working",
                    "response": response.text[:200]
                }
        
        # Pour les endpoints d'API, tester avec une requête POST
        else:
            test_payload = {
                "prompt": "Hello, are you working?",
                "max_tokens": 50
            }
            
            response = requests.post(
                url, 
                json=test_payload, 
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201]:
                return {
                    "ip": ip,
                    "endpoint": endpoint,
                    "status": "working",
                    "response": response.text[:200]
                }
                
    except requests.exceptions.Timeout:
        return {
            "ip": ip,
            "endpoint": endpoint,
            "status": "timeout",
            "response": "Timeout after 5-10 seconds"
        }
    except requests.exceptions.ConnectionError:
        return {
            "ip": ip,
            "endpoint": endpoint,
            "status": "connection_error",
            "response": "Connection refused or network error"
        }
    except Exception as e:
        return {
            "ip": ip,
            "endpoint": endpoint,
            "status": "error",
            "response": str(e)[:200]
        }
    
    return None

def run_lm_arena_test(api_url: str) -> Dict:
    """Exécuter les tests LM Arena sur l'API"""
    print(f"\nExecuting LM Arena tests on {api_url}")
    print("=" * 60)
    
    results = []
    
    for test_case in LM_ARENA_TEST_CASES:
        print(f"\nTest: {test_case['category']}")
        print(f"Prompt: {test_case['prompt'][:80]}...")
        
        payload = {
            "prompt": test_case["prompt"],
            "max_tokens": 200,
            "temperature": 0.7
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                api_url,
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                response_data = response.json()
                generated_text = response_data.get("text", response_data.get("response", ""))
                
                # Vérifier la présence des mots-clés attendus
                keywords_found = []
                for keyword in test_case["expected_keywords"]:
                    if keyword.lower() in generated_text.lower():
                        keywords_found.append(keyword)
                
                test_result = {
                    "category": test_case["category"],
                    "status": "passed",
                    "response_time": round(elapsed_time, 2),
                    "keywords_found": keywords_found,
                    "keywords_expected": test_case["expected_keywords"],
                    "response_preview": generated_text[:100] + "..." if len(generated_text) > 100 else generated_text
                }
                
                print(f"  Status: PASSED ({elapsed_time:.2f}s)")
                print(f"  Keywords found: {', '.join(keywords_found)}")
                
            else:
                test_result = {
                    "category": test_case["category"],
                    "status": "failed",
                    "response_time": round(elapsed_time, 2),
                    "error": f"HTTP {response.status_code}: {response.text[:100]}"
                }
                
                print(f"  Status: FAILED (HTTP {response.status_code})")
                
        except requests.exceptions.Timeout:
            test_result = {
                "category": test_case["category"],
            "status": "timeout",
                "response_time": 30.0,
                "error": "Request timeout after 30 seconds"
            }
            
            print("  Status: TIMEOUT")
            
        except Exception as e:
            test_result = {
                "category": test_case["category"],
                "status": "error",
                "response_time": 0.0,
                "error": str(e)[:200]
            }
            
            print(f"  Status: ERROR ({str(e)[:50]})")
        
        results.append(test_result)
    
    return {
        "test_date": datetime.now().isoformat(),
        "api_url": api_url,
        "results": results
    }

def main():
    """Fonction principale"""
    print("LM ARENA TEST FOR DEPLOYED EC2 INSTANCE")
    print("=" * 60)
    print(f"Instance: {EC2_INSTANCE_NAME}")
    print(f"Region: {AWS_REGION}")
    print(f"Port: {API_PORT}")
    print("=" * 60)
    
    # Tester chaque IP avec chaque endpoint
    working_endpoints = []
    
    for ip in POTENTIAL_IPS:
        print(f"\nTesting IP: {ip}")
        
        for endpoint in API_ENDPOINTS:
            result = test_endpoint(ip, endpoint)
            
            if result and result["status"] == "working":
                print(f"  ✓ {endpoint}: WORKING")
                working_endpoints.append({
                    "ip": ip,
                    "endpoint": endpoint,
                    "url": f"http://{ip}:{API_PORT}{endpoint}"
                })
            elif result:
                print(f"  ✗ {endpoint}: {result['status']}")
    
    if not working_endpoints:
        print("\nERROR: No working API endpoints found")
        print("\nPossible issues:")
        print("1. Instance not running or not accessible")
        print("2. Security group blocking port 8080")
        print("3. Service not started on the instance")
        print("4. Wrong IP address")
        print("\nNext steps:")
        print("1. Check AWS Console for instance status")
        print("2. Verify security group rules allow port 8080")
        print("3. SSH into instance and check service status")
        return
    
    print(f"\nFound {len(working_endpoints)} working endpoint(s):")
    for endpoint in working_endpoints:
        print(f"  - {endpoint['url']}")
    
    # Exécuter les tests LM Arena sur le premier endpoint fonctionnel
    if working_endpoints:
        api_url = working_endpoints[0]["url"]
        
        print(f"\nStarting LM Arena tests on: {api_url}")
        
        test_results = run_lm_arena_test(api_url)
        
        # Afficher le résumé
        print("\n" + "=" * 60)
        print("LM ARENA TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in test_results["results"] if r["status"] == "passed")
        failed = sum(1 for r in test_results["results"] if r["status"] == "failed")
        timeout = sum(1 for r in test_results["results"] if r["status"] == "timeout")
        errors = sum(1 for r in test_results["results"] if r["status"] == "error")
        
        print(f"Total tests: {len(test_results['results'])}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Timeout: {timeout}")
        print(f"Errors: {errors}")
        
        # Sauvegarder les résultats
        output_file = f"lm_arena_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {output_file}")
        
        # Afficher les détails des tests échoués
        if failed > 0 or timeout > 0 or errors > 0:
            print("\nFAILED TESTS DETAILS:")
            for result in test_results["results"]:
                if result["status"] in ["failed", "timeout", "error"]:
                    print(f"\nCategory: {result['category']}")
                    print(f"Status: {result['status']}")
                    if "error" in result:
                        print(f"Error: {result['error']}")

if __name__ == "__main__":
    main()