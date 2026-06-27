#!/usr/bin/env python3
"""
Test réel de l'API DeepSeek-Harmonic-V2
Basé sur les résultats du diagnostic
"""

import requests
import json
import time
from datetime import datetime

INSTANCE_IP = "54.81.62.140"
API_URL = f"http://{INSTANCE_IP}:8000/generate"

def test_api_directly():
    """Tester l'API directement avec différents formats"""
    
    print("REAL API TEST - DEEPSEEK-HARMONIC-V2")
    print("=" * 60)
    print(f"API URL: {API_URL}")
    print("=" * 60)
    
    # Test 1: Format simple qui a fonctionné dans le diagnostic
    print("\nTest 1: Format simple")
    payload1 = {
        "prompt": "What is 2+2? Give a detailed explanation.",
        "max_tokens": 100
    }
    
    print(f"Payload: {json.dumps(payload1, indent=2)}")
    
    try:
        start = time.time()
        response = requests.post(API_URL, json=payload1, timeout=10)
        elapsed = time.time() - start
        
        print(f"Status: HTTP {response.status_code}")
        print(f"Time: {elapsed:.3f}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Vérifier si c'est une vraie réponse ou un mock
            content = data.get("content", "")
            if "Generated response for:" in content:
                print("WARNING: This appears to be a mock response")
                return False, "mock_response"
            else:
                print("SUCCESS: Real response received")
                return True, data
        else:
            print(f"Error: {response.text[:200]}")
            return False, f"http_{response.status_code}"
            
    except Exception as e:
        print(f"Exception: {str(e)[:200]}")
        return False, str(e)
    
    return False, "unknown"

def test_with_different_parameters():
    """Tester avec différents paramètres de génération"""
    
    print("\n" + "=" * 60)
    print("TESTING DIFFERENT GENERATION PARAMETERS")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "High temperature",
            "payload": {
                "prompt": "Explain the concept of artificial intelligence",
                "max_tokens": 150,
                "temperature": 1.2,
                "top_p": 0.95
            }
        },
        {
            "name": "Low temperature (deterministic)",
            "payload": {
                "prompt": "What is the capital of France?",
                "max_tokens": 50,
                "temperature": 0.1,
                "top_p": 0.5
            }
        },
        {
            "name": "With repetition penalty",
            "payload": {
                "prompt": "Write a short poem about technology",
                "max_tokens": 100,
                "temperature": 0.8,
                "repetition_penalty": 1.2
            }
        },
        {
            "name": "Complex reasoning",
            "payload": {
                "prompt": "A train leaves Paris at 8:00 AM traveling at 120 km/h. Another train leaves Lyon at 9:00 AM traveling at 150 km/h towards Paris. The distance between Paris and Lyon is 450 km. At what time will they meet? Show your calculations step by step.",
                "max_tokens": 200,
                "temperature": 0.3
            }
        }
    ]
    
    results = []
    
    for test in test_cases:
        print(f"\nTest: {test['name']}")
        print(f"Prompt: {test['payload']['prompt'][:80]}...")
        
        try:
            start = time.time()
            response = requests.post(API_URL, json=test["payload"], timeout=15)
            elapsed = time.time() - start
            
            print(f"  Status: HTTP {response.status_code}")
            print(f"  Time: {elapsed:.3f}s")
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", "")
                
                # Analyser la réponse
                if content:
                    print(f"  Response length: {len(content)} chars")
                    print(f"  Preview: {content[:150]}...")
                    
                    # Vérifier si c'est une vraie réponse
                    if "Generated response for:" in content:
                        print("  Type: MOCK RESPONSE")
                        results.append({
                            "test": test["name"],
                            "type": "mock",
                            "response": content[:500]
                        })
                    else:
                        print("  Type: REAL RESPONSE")
                        results.append({
                            "test": test["name"],
                            "type": "real",
                            "response": content[:500]
                        })
                else:
                    print("  Type: EMPTY RESPONSE")
                    results.append({
                        "test": test["name"],
                        "type": "empty",
                        "response": ""
                    })
            else:
                print(f"  Error: {response.text[:100]}")
                results.append({
                    "test": test["name"],
                    "type": "error",
                    "error": f"HTTP {response.status_code}"
                })
                
        except requests.exceptions.Timeout:
            print("  Timeout after 15s")
            results.append({
                "test": test["name"],
                "type": "timeout"
            })
        except Exception as e:
            print(f"  Exception: {str(e)[:100]}")
            results.append({
                "test": test["name"],
                "type": "exception",
                "error": str(e)[:200]
            })
    
    return results

def check_health_details():
    """Vérifier les détails de santé de l'API"""
    
    health_url = f"http://{INSTANCE_IP}:8000/health"
    
    print("\n" + "=" * 60)
    print("HEALTH CHECK DETAILS")
    print("=" * 60)
    
    try:
        response = requests.get(health_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            print("API Status:")
            print(f"  Overall: {data.get('status', 'unknown')}")
            print(f"  Version: {data.get('version', 'unknown')}")
            print(f"  Total Models: {data.get('total_models', 'unknown')}")
            print(f"  Parallel Mode: {data.get('parallel_mode', 'unknown')}")
            print(f"  Multi-Modal: {data.get('multi_modal', 'unknown')}")
            print(f"  LM Arena Ready: {data.get('lm_arena_ready', 'unknown')}")
            
            # Vérifier les modèles spécifiques
            print("\nModel Status:")
            models_to_check = [
                "deterministic_core",
                "deepseek_s3", 
                "qwen_files",
                "mixtral_parallel",
                "sdxl_revolutionary"
            ]
            
            for model in models_to_check:
                if model in data:
                    print(f"  {model}: {data[model]}")
            
            return data
            
        else:
            print(f"Health check failed: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Health check error: {str(e)[:100]}")
        return None

def main():
    """Fonction principale"""
    
    # Vérifier la santé de l'API
    health_data = check_health_details()
    
    if not health_data:
        print("\nERROR: Cannot access API health endpoint")
        return
    
    # Tester l'API directement
    print("\n" + "=" * 60)
    print("DIRECT API TEST")
    print("=" * 60)
    
    success, result = test_api_directly()
    
    if success and result != "mock_response":
        print("\n✅ API is working with real responses!")
        
        # Exécuter des tests plus complets
        detailed_results = test_with_different_parameters()
        
        # Analyser les résultats
        print("\n" + "=" * 60)
        print("ANALYSIS OF RESULTS")
        print("=" * 60)
        
        real_count = sum(1 for r in detailed_results if r["type"] == "real")
        mock_count = sum(1 for r in detailed_results if r["type"] == "mock")
        other_count = len(detailed_results) - real_count - mock_count
        
        print(f"Total tests: {len(detailed_results)}")
        print(f"Real responses: {real_count}")
        print(f"Mock responses: {mock_count}")
        print(f"Other (errors/timeouts): {other_count}")
        
        if real_count > 0:
            print("\n✅ SUCCESS: The model is generating real responses")
            print("Enhanced Harmonic Hybrid AI v2.0 is operational!")
        else:
            print("\n⚠ WARNING: Only mock responses received")
            print("The model may be in demo mode or not fully loaded")
        
    elif result == "mock_response":
        print("\n⚠ WARNING: API is returning mock responses")
        print("This suggests:")
        print("1. The model is in demo/mock mode")
        print("2. Model files may not be properly loaded")
        print("3. Service needs configuration update")
        
        # Tester d'autres paramètres
        print("\nTesting alternative parameters...")
        alt_results = test_with_different_parameters()
        
        # Vérifier si nous obtenons des vraies réponses
        has_real = any(r["type"] == "real" for r in alt_results)
        
        if has_real:
            print("\n✅ Some tests returned real responses!")
            print("Try different prompt formats or parameters")
        else:
            print("\n❌ All tests returned mock responses")
            print("The service likely needs to be reconfigured")
            
    else:
        print("\n❌ ERROR: API test failed")
        print(f"Result: {result}")
    
    # Résumé final
    print("\n" + "=" * 60)
    print("FINAL SUMMARY - ENHANCED HARMONIC HYBRID AI V2")
    print("=" * 60)
    
    print(f"\nInstance: DeepSeek-Harmonic-V2")
    print(f"IP Address: {INSTANCE_IP}")
    print(f"API Status: {health_data.get('status', 'unknown')}")
    print(f"Version: {health_data.get('version', 'unknown')}")
    print(f"Models Loaded: {health_data.get('total_models', 'unknown')}")
    
    if success and result != "mock_response":
        print("\n🎉 STATUS: FULLY OPERATIONAL")
        print("The model is ready for LM Arena evaluation")
        print("\nNext steps:")
        print("1. Run comprehensive LM Arena tests")
        print("2. Evaluate performance metrics")
        print("3. Compare with baseline models")
    elif result == "mock_response":
        print("\n⚠ STATUS: DEMO/MOCK MODE")
        print("Model is accessible but not generating real responses")
        print("\nRequired actions:")
        print("1. Check model configuration on the instance")
        print("2. Verify model files are present and loaded")
        print("3. Restart the service with proper parameters")
    else:
        print("\n❌ STATUS: NOT OPERATIONAL")
        print("API is not functioning correctly")
    
    # Sauvegarder les résultats
    output_file = f"api_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "instance_ip": INSTANCE_IP,
        "health_status": health_data,
        "direct_test": {
            "success": success,
            "result_type": result if isinstance(result, str) else "data"
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nReport saved to: {output_file}")

if __name__ == "__main__":
    main()