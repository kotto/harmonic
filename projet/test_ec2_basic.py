#!/usr/bin/env python3
"""
Basic test for deployed EC2 instance
Simplified version without special characters
"""

import requests
import json
import time
import sys
import os
from datetime import datetime

# Configuration
EC2_INSTANCE_NAME = "qwen35-ec2-server"
AWS_REGION = "us-east-1"
API_PORT = 8080

# IPs to test
IP_LIST = [
    "54.166.179.141",
    "3.95.231.91",
    "98.82.7.99",
    "18.212.135.123",
    "34.192.45.67",
    "52.91.23.145",
    "54.157.32.189",
]

# Test endpoints
ENDPOINTS = [
    "/health",
    "/generate",
    "/v1/chat/completions",
]

# LM Arena test cases
TEST_CASES = [
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

def test_connection(ip, endpoint):
    """Test connection to a specific endpoint"""
    url = f"http://{ip}:{API_PORT}{endpoint}"
    
    try:
        if endpoint == "/health":
            response = requests.get(url, timeout=5)
        else:
            payload = {"prompt": "Test", "max_tokens": 10}
            response = requests.post(url, json=payload, timeout=5)
        
        if response.status_code == 200:
            return True, response.text[:100]
        else:
            return False, f"HTTP {response.status_code}"
            
    except requests.exceptions.Timeout:
        return False, "Timeout"
    except requests.exceptions.ConnectionError:
        return False, "Connection refused"
    except Exception as e:
        return False, str(e)[:100]

def run_lm_test(api_url):
    """Run LM Arena tests"""
    print(f"\nRunning LM Arena tests on {api_url}")
    print("-" * 50)
    
    results = []
    
    for test in TEST_CASES:
        print(f"\nTest: {test['category']}")
        print(f"Prompt: {test['prompt'][:60]}...")
        
        payload = {
            "prompt": test["prompt"],
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        try:
            start = time.time()
            response = requests.post(api_url, json=payload, timeout=15)
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                text = data.get("text", data.get("response", ""))
                
                print(f"  Status: OK ({elapsed:.2f}s)")
                print(f"  Response: {text[:80]}...")
                
                results.append({
                    "category": test["category"],
                    "status": "ok",
                    "time": elapsed,
                    "response": text[:200]
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
                "error": "15s timeout"
            })
        except Exception as e:
            print(f"  Status: ERROR ({str(e)[:50]})")
            results.append({
                "category": test["category"],
                "status": "error",
                "error": str(e)[:200]
            })
    
    return results

def main():
    """Main function"""
    print("TESTING DEPLOYED EC2 INSTANCE")
    print("=" * 50)
    print(f"Instance: {EC2_INSTANCE_NAME}")
    print(f"Region: {AWS_REGION}")
    print(f"Port: {API_PORT}")
    print("=" * 50)
    
    # Test all IPs
    working_ips = []
    
    for ip in IP_LIST:
        print(f"\nTesting IP: {ip}")
        
        for endpoint in ENDPOINTS:
            success, message = test_connection(ip, endpoint)
            
            if success:
                print(f"  {endpoint}: OK - {message}")
                working_ips.append({
                    "ip": ip,
                    "endpoint": endpoint,
                    "url": f"http://{ip}:{API_PORT}{endpoint}"
                })
                break  # Stop testing other endpoints if one works
            else:
                print(f"  {endpoint}: FAILED - {message}")
    
    if not working_ips:
        print("\nERROR: No working endpoints found")
        print("\nPossible issues:")
        print("1. Instance not running")
        print("2. Security group blocking port 8080")
        print("3. Service not started")
        print("4. Wrong IP addresses")
        return
    
    print(f"\nFound {len(working_ips)} working endpoint(s)")
    
    # Run LM Arena tests on first working endpoint
    first_endpoint = working_ips[0]["url"]
    print(f"\nUsing endpoint: {first_endpoint}")
    
    test_results = run_lm_test(first_endpoint)
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    ok_count = sum(1 for r in test_results if r["status"] == "ok")
    failed_count = sum(1 for r in test_results if r["status"] == "failed")
    timeout_count = sum(1 for r in test_results if r["status"] == "timeout")
    error_count = sum(1 for r in test_results if r["status"] == "error")
    
    print(f"Total tests: {len(test_results)}")
    print(f"OK: {ok_count}")
    print(f"Failed: {failed_count}")
    print(f"Timeout: {timeout_count}")
    print(f"Errors: {error_count}")
    
    # Save results
    output_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "endpoint": first_endpoint,
            "results": test_results
        }, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()