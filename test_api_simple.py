#!/usr/bin/env python3
"""
TEST API SIMPLE - DEEPSEEK HARMONIC V2
Test simple de l'API pour verifier les reponses reel
"""

import requests
import time
from datetime import datetime

def test_api():
    """Tester l'API"""
    instance_ip = "54.81.62.140"
    port = 8000
    
    print("=" * 60)
    print("TEST API DEEPSEEK HARMONIC V2")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Instance: {instance_ip}:{port}")
    print()
    
    # Test 1: Health endpoint
    print("TEST 1: HEALTH ENDPOINT")
    print("-" * 30)
    
    try:
        url = f"http://{instance_ip}:{port}/health"
        print(f"URL: {url}")
        
        response = requests.get(url, timeout=10)
        
        print(f"Status: HTTP {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            print("RESULT: PASS")
        else:
            print(f"Error: {response.text}")
            print("RESULT: FAIL")
            
    except requests.exceptions.Timeout:
        print("ERROR: Timeout - API not responding")
        print("RESULT: FAIL")
    except requests.exceptions.ConnectionError:
        print("ERROR: Connection refused - API may not be running")
        print("RESULT: FAIL")
    except Exception as e:
        print(f"ERROR: {e}")
        print("RESULT: FAIL")
    
    print()
    
    # Test 2: Generate endpoint
    print("TEST 2: GENERATE ENDPOINT")
    print("-" * 30)
    
    test_prompts = [
        {
            "name": "Code test",
            "prompt": "Write a Python function to calculate fibonacci sequence"
        },
        {
            "name": "Math test", 
            "prompt": "Calculate the integral of x^2 from 0 to 1"
        },
        {
            "name": "General test",
            "prompt": "Explain the concept of harmonic transformations in AI"
        }
    ]
    
    all_passed = True
    
    for test in test_prompts:
        print(f"\nSub-test: {test['name']}")
        print(f"Prompt: {test['prompt'][:50]}...")
        
        try:
            url = f"http://{instance_ip}:{port}/generate"
            payload = {
                "prompt": test['prompt'],
                "max_tokens": 300,
                "temperature": 0.7
            }
            
            start_time = time.time()
            response = requests.post(url, json=payload, timeout=15)
            elapsed = time.time() - start_time
            
            print(f"  Time: {elapsed:.2f}s")
            print(f"  Status: HTTP {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", "")
                
                # Check if response is real or mock
                if "Generated response for:" in content:
                    print("  WARNING: MOCK RESPONSE DETECTED")
                    print("  This is the OLD version (mock API)")
                    all_passed = False
                else:
                    print("  SUCCESS: REAL RESPONSE DETECTED")
                    print(f"  Confidence: {data.get('confidence', 'N/A')}")
                    print(f"  Version: {data.get('version', 'N/A')}")
                    
                    # Show sample
                    sample = content[:100].replace('\n', ' ')
                    print(f"  Sample: {sample}...")
                    
            else:
                print(f"  ERROR: {response.text}")
                all_passed = False
                
        except Exception as e:
            print(f"  ERROR: {e}")
            all_passed = False
    
    print()
    print("=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    
    if all_passed:
        print("SUCCESS: ALL TESTS PASSED")
        print("The API is returning REAL responses (not mock)")
        print()
        print("Next steps:")
        print("1. Run LM Arena tests: python lm_arena_test_final.py")
        print("2. Submit results to LM Arena platform")
    else:
        print("WARNING: SOME TESTS FAILED")
        print("The API may still be returning MOCK responses")
        print()
        print("Actions required:")
        print("1. Deploy the real version manually:")
        print("   Follow instructions from deploy_with_paramiko.py")
        print("2. Or restart the EC2 instance if it's stopped")
        print("3. Check AWS security groups allow port 8000")
    
    return all_passed

def quick_status():
    """Check rapide du statut"""
    instance_ip = "54.81.62.140"
    
    print("Quick status check...")
    
    try:
        # Try health endpoint
        resp = requests.get(f"http://{instance_ip}:8000/health", timeout=5)
        
        if resp.status_code == 200:
            print(f"API is running (HTTP {resp.status_code})")
            
            # Quick generate test
            payload = {"prompt": "Quick test", "max_tokens": 50}
            resp = requests.post(f"http://{instance_ip}:8000/generate", json=payload, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("content", "")
                
                if "Generated response for:" in content:
                    print("API type: MOCK (old version)")
                else:
                    print("API type: REAL (new version)")
                    
                return True
            else:
                print(f"Generate failed: HTTP {resp.status_code}")
                return False
        else:
            print(f"Health failed: HTTP {resp.status_code}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    # Run full test
    success = test_api()
    
    # Also show quick status
    print("\n" + "-" * 60)
    print("QUICK STATUS")
    print("-" * 60)
    quick_status()
    
    exit(0 if success else 1)