#!/usr/bin/env python3
"""
Script final pour tester l'instance EC2 DeepSeek-Harmonic-V2
"""

import requests
import time
import json
from datetime import datetime

def main():
    print("LM ARENA TEST - DEEPSEEK-HARMONIC-V2")
    print("========================================")
    
    # Demander l'adresse IP
    ip_address = input("Entrez l'adresse IP publique de l'instance: ").strip()
    
    if not ip_address:
        print("Erreur: Adresse IP requise")
        return
    
    print(f"\nInstance IP: {ip_address}")
    print("Ports a tester: 8000, 8080, 80")
    print("========================================")
    
    # Tester les ports
    ports = [8000, 8080, 80]
    endpoints = ["/health", "/", "/api/health"]
    
    working_url = None
    
    for port in ports:
        print(f"\nTest port {port}:")
        
        for endpoint in endpoints:
            url = f"http://{ip_address}:{port}{endpoint}"
            
            try:
                response = requests.get(url, timeout=3)
                print(f"  {endpoint}: HTTP {response.status_code}")
                
                if response.status_code == 200:
                    working_url = url
                    print(f"  SUCCESS: Found working endpoint")
                    break
                    
            except requests.exceptions.Timeout:
                print(f"  {endpoint}: Timeout")
            except requests.exceptions.ConnectionError:
                print(f"  {endpoint}: Connection refused")
            except Exception as e:
                print(f"  {endpoint}: Error - {str(e)[:50]}")
        
        if working_url:
            break
    
    if not working_url:
        print("\nERROR: No working endpoint found")
        print("\nPlease check:")
        print("1. Instance is running (state: running)")
        print("2. Security group allows port 8000, 8080, or 80")
        print("3. Service is started on the instance")
        return
    
    print(f"\nWorking URL: {working_url}")
    
    # Determiner l'URL de l'API generate
    if "/health" in working_url:
        api_url = working_url.replace("/health", "/generate")
    else:
        api_url = working_url + "/generate"
    
    print(f"API URL: {api_url}")
    
    # Executer les tests LM Arena
    print("\n" + "=" * 50)
    print("EXECUTING LM ARENA TESTS")
    print("=" * 50)
    
    test_cases = [
        {
            "category": "reasoning",
            "prompt": "If a train leaves Paris at 8:00 AM traveling at 120 km/h, and another train leaves Lyon at 9:00 AM traveling at 150 km/h towards Paris, and the distance between Paris and Lyon is 450 km, at what time will they meet?",
        },
        {
            "category": "coding",
            "prompt": "Write a Python function to find the longest palindrome substring in a given string.",
        },
        {
            "category": "mathematics",
            "prompt": "Calculate the integral of x^2 * sin(x) from 0 to pi.",
        },
    ]
    
    results = []
    
    for test in test_cases:
        print(f"\nTest: {test['category']}")
        print(f"Prompt: {test['prompt'][:60]}...")
        
        payload = {
            "prompt": test["prompt"],
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        try:
            start = time.time()
            response = requests.post(api_url, json=payload, timeout=30)
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                text = data.get("text", data.get("response", ""))
                
                print(f"  Status: OK ({elapsed:.2f}s)")
                print(f"  Response: {text[:80]}...")
                
                results.append({
                    "category": test["category"],
                    "status": "passed",
                    "response_time": elapsed,
                    "response": text[:500]
                })
            else:
                print(f"  Status: FAILED (HTTP {response.status_code})")
                results.append({
                    "category": test["category"],
                    "status": "failed",
                    "error": f"HTTP {response.status_code}"
                })
                
        except requests.exceptions.Timeout:
            print("  Status: TIMEOUT")
            results.append({
                "category": test["category"],
                "status": "timeout",
                "error": "30s timeout"
            })
        except Exception as e:
            print(f"  Status: ERROR ({str(e)[:50]})")
            results.append({
                "category": test["category"],
                "status": "error",
                "error": str(e)[:200]
            })
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for r in results if r["status"] == "passed")
    failed = sum(1 for r in results if r["status"] == "failed")
    timeout = sum(1 for r in results if r["status"] == "timeout")
    errors = sum(1 for r in results if r["status"] == "error")
    
    print(f"Total tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Timeout: {timeout}")
    print(f"Errors: {errors}")
    
    # Save results
    output_file = f"lm_arena_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "instance_ip": ip_address,
            "api_url": api_url,
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()