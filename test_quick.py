#!/usr/bin/env python3
"""
Quick test for EC2 instance
"""

import requests
import json
import time

# Most likely IPs based on previous deployments
IP_LIST = [
    "54.166.179.141",  # Most likely
    "3.95.231.91",
    "98.82.7.99",
]

PORT = 8080
ENDPOINT = "/health"

def quick_test():
    """Quick connectivity test"""
    print("Quick EC2 Instance Test")
    print("=" * 40)
    
    for ip in IP_LIST:
        url = f"http://{ip}:{PORT}{ENDPOINT}"
        print(f"\nTesting: {url}")
        
        try:
            start = time.time()
            response = requests.get(url, timeout=3)
            elapsed = time.time() - start
            
            print(f"  Status: HTTP {response.status_code}")
            print(f"  Time: {elapsed:.2f}s")
            
            if response.status_code == 200:
                print(f"  Response: {response.text[:100]}")
                return True, url
            else:
                print(f"  Error: {response.text[:100]}")
                
        except requests.exceptions.Timeout:
            print("  Timeout after 3 seconds")
        except requests.exceptions.ConnectionError:
            print("  Connection refused")
        except Exception as e:
            print(f"  Error: {str(e)[:100]}")
    
    return False, None

def test_api(api_url):
    """Test API with simple prompt"""
    print(f"\nTesting API at: {api_url}")
    
    payload = {
        "prompt": "What is 2+2?",
        "max_tokens": 20
    }
    
    try:
        response = requests.post(api_url, json=payload, timeout=5)
        print(f"  Status: HTTP {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Response: {json.dumps(data, indent=2)[:200]}")
            return True
        else:
            print(f"  Error: {response.text[:100]}")
            
    except Exception as e:
        print(f"  Error: {str(e)[:100]}")
    
    return False

if __name__ == "__main__":
    # Quick connectivity test
    success, api_url = quick_test()
    
    if success:
        # If health check works, try the generate endpoint
        generate_url = api_url.replace("/health", "/generate")
        print(f"\n" + "=" * 40)
        print("Testing generate endpoint...")
        api_success = test_api(generate_url)
        
        if api_success:
            print("\nSUCCESS: EC2 instance is working!")
        else:
            print("\nWARNING: Health check works but API endpoint may have issues")
    else:
        print("\nFAILURE: Cannot connect to EC2 instance")
        print("\nPossible reasons:")
        print("1. Instance is not running")
        print("2. Security group blocks port 8080")
        print("3. Service is not started on the instance")
        print("4. IP address is incorrect")