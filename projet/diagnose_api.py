#!/usr/bin/env python3
"""
Diagnostic de l'API EC2 DeepSeek-Harmonic-V2
"""

import requests
import json
import time

INSTANCE_IP = "54.81.62.140"
BASE_URL = f"http://{INSTANCE_IP}:8000"

def test_endpoint(endpoint, method="GET", payload=None):
    """Tester un endpoint spécifique"""
    url = f"{BASE_URL}{endpoint}"
    
    print(f"\nTesting: {method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=payload, headers=headers, timeout=10)
        else:
            print(f"  ERROR: Unsupported method {method}")
            return None
        
        print(f"  Status: HTTP {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"  Response JSON: {json.dumps(data, indent=2)[:300]}")
                return data
            except:
                print(f"  Response Text: {response.text[:200]}")
                return response.text
        else:
            print(f"  Error: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print("  Timeout")
    except requests.exceptions.ConnectionError:
        print("  Connection refused")
    except Exception as e:
        print(f"  Error: {str(e)[:100]}")
    
    return None

def test_different_payloads():
    """Tester différents formats de payload"""
    endpoint = "/generate"
    
    print("\n" + "=" * 70)
    print("TESTING DIFFERENT PAYLOAD FORMATS")
    print("=" * 70)
    
    payloads = [
        {
            "name": "Simple prompt",
            "payload": {
                "prompt": "What is 2+2?",
                "max_tokens": 50
            }
        },
        {
            "name": "With temperature",
            "payload": {
                "prompt": "Explain quantum computing",
                "max_tokens": 100,
                "temperature": 0.7,
                "top_p": 0.9
            }
        },
        {
            "name": "Chat format",
            "payload": {
                "messages": [
                    {"role": "user", "content": "Hello, how are you?"}
                ],
                "max_tokens": 100
            }
        },
        {
            "name": "Multiple messages",
            "payload": {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is the capital of France?"}
                ],
                "max_tokens": 50
            }
        },
        {
            "name": "Streaming request",
            "payload": {
                "prompt": "Write a haiku about AI",
                "max_tokens": 50,
                "stream": True
            }
        }
    ]
    
    results = []
    
    for test in payloads:
        print(f"\n{'-'*60}")
        print(f"Test: {test['name']}")
        print(f"Payload: {json.dumps(test['payload'], indent=2)[:200]}")
        
        result = test_endpoint(endpoint, "POST", test["payload"])
        
        if result:
            results.append({
                "test": test["name"],
                "success": True,
                "result": result if isinstance(result, str) else "JSON response"
            })
        else:
            results.append({
                "test": test["name"],
                "success": False,
                "result": "No response or error"
            })
    
    return results

def test_alternative_endpoints():
    """Tester d'autres endpoints possibles"""
    print("\n" + "=" * 70)
    print("TESTING ALTERNATIVE ENDPOINTS")
    print("=" * 70)
    
    endpoints = [
        "/",
        "/api",
        "/api/generate",
        "/v1/chat/completions",
        "/v1/completions",
        "/v1/engines",
        "/docs",
        "/openapi.json",
        "/swagger.json"
    ]
    
    results = []
    
    for endpoint in endpoints:
        result = test_endpoint(endpoint, "GET")
        
        if result:
            results.append({
                "endpoint": endpoint,
                "success": True,
                "result_type": "JSON" if isinstance(result, dict) else "Text"
            })
        else:
            results.append({
                "endpoint": endpoint,
                "success": False
            })
    
    return results

def test_health_details():
    """Tester l'endpoint health en détail"""
    print("\n" + "=" * 70)
    print("HEALTH ENDPOINT DETAILS")
    print("=" * 70)
    
    health_data = test_endpoint("/health", "GET")
    
    if health_data and isinstance(health_data, dict):
        print("\nHealth Status Details:")
        for key, value in health_data.items():
            print(f"  {key}: {value}")
    
    return health_data

def main():
    """Fonction principale"""
    print("API DIAGNOSTIC - DEEPSEEK-HARMONIC-V2")
    print(f"Instance IP: {INSTANCE_IP}")
    print(f"Base URL: {BASE_URL}")
    
    # Test 1: Health endpoint
    health_data = test_health_details()
    
    # Test 2: Alternative endpoints
    alt_results = test_alternative_endpoints()
    
    # Test 3: Different payload formats
    payload_results = test_different_payloads()
    
    # Analyse des résultats
    print("\n" + "=" * 70)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 70)
    
    # Compter les succès
    successful_endpoints = sum(1 for r in alt_results if r["success"])
    successful_payloads = sum(1 for r in payload_results if r["success"])
    
    print(f"\nHealth endpoint: {'WORKING' if health_data else 'NOT WORKING'}")
    print(f"Alternative endpoints working: {successful_endpoints}/{len(alt_results)}")
    print(f"Payload formats working: {successful_payloads}/{len(payload_results)}")
    
    # Recommandations
    print(f"\nRECOMMENDATIONS:")
    print("-" * 70)
    
    if health_data:
        print("✓ Health endpoint is working")
        print(f"  Status: {health_data.get('status', 'unknown')}")
        
        # Vérifier les services spécifiques
        services = [
            "parallel_multi_modal",
            "deterministic_core", 
            "deepseek_s3",
            "qwen_files",
            "mixtral_parallel",
            "sdxl_revolutionary"
        ]
        
        for service in services:
            if service in health_data:
                print(f"  {service}: {health_data[service]}")
    
    if successful_payloads == 0:
        print("\n⚠ CRITICAL: No payload format is working")
        print("  Possible issues:")
        print("  1. Model not loaded correctly")
        print("  2. Wrong API endpoint format")
        print("  3. Service needs restart")
        print("\n  Next steps:")
        print("  1. SSH into instance and check logs")
        print("  2. Restart the qwen35 service")
        print("  3. Verify model files are present")
    
    elif successful_payloads > 0:
        print(f"\n✓ Some payload formats are working ({successful_payloads}/{len(payload_results)})")
        print("  Review which formats work and update test scripts accordingly")
    
    # Afficher les endpoints qui fonctionnent
    print(f"\nWORKING ENDPOINTS:")
    print("-" * 70)
    
    if health_data:
        print("✓ /health")
    
    for result in alt_results:
        if result["success"]:
            print(f"✓ {result['endpoint']}")
    
    for result in payload_results:
        if result["success"]:
            print(f"✓ /generate (with {result['test']} payload)")

if __name__ == "__main__":
    main()