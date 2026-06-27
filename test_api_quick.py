#!/usr/bin/env python3
"""
TEST API RAPIDE - DEEPSEEK HARMONIC V2
Test rapide de l'API sans SSH
"""

import requests
import json
import time
from datetime import datetime

def test_api_quick():
    """Test rapide de l'API"""
    base_url = "http://54.81.62.140:8000"
    
    print("TEST API RAPIDE - DEEPSEEK HARMONIC V2")
    print("=" * 50)
    print(f"URL: {base_url}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Health endpoint
    print("1. Test endpoint /health")
    print("-" * 30)
    
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/health", timeout=10)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            try:
                data = response.json()
                status = data.get("status", "unknown")
                print(f"   ✅ SUCCES: {status} ({elapsed:.2f}s)")
                print(f"   📊 Donnees: {json.dumps(data, indent=2)}")
            except:
                print(f"   ⚠️  REPONSE NON-JSON: {response.text[:100]}")
        else:
            print(f"   ❌ ECHEC: HTTP {response.status_code}")
            
    except requests.Timeout:
        print("   ❌ TIMEOUT: L'API ne repond pas")
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
    
    print()
    
    # Test 2: Root endpoint
    print("2. Test endpoint / (racine)")
    print("-" * 30)
    
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/", timeout=10)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            try:
                data = response.json()
                message = data.get("message", "No message")
                print(f"   ✅ SUCCES: {message[:50]}... ({elapsed:.2f}s)")
                print(f"   📊 Donnees: {json.dumps(data, indent=2)}")
            except:
                print(f"   ⚠️  REPONSE NON-JSON: {response.text[:100]}")
        else:
            print(f"   ❌ ECHEC: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
    
    print()
    
    # Test 3: Info endpoint
    print("3. Test endpoint /info")
    print("-" * 30)
    
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/info", timeout=10)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            try:
                data = response.json()
                model_name = data.get("name", "Unknown")
                version = data.get("version", "Unknown")
                print(f"   ✅ SUCCES: {model_name} v{version} ({elapsed:.2f}s)")
                
                # Verifier si c'est une version mock
                is_mock = any([
                    "mock" in str(data).lower(),
                    "generated response" in str(data).lower(),
                    "[Deepseek" in str(data) and "]" in str(data)
                ])
                
                if is_mock:
                    print("   ⚠️  ATTENTION: Version MOCK detectee")
                else:
                    print("   ✅ Version RELLE detectee")
                    
            except:
                print(f"   ⚠️  REPONSE NON-JSON: {response.text[:100]}")
        else:
            print(f"   ❌ ECHEC: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
    
    print()
    
    # Test 4: Generate endpoint (simple)
    print("4. Test endpoint /generate (simple)")
    print("-" * 30)
    
    try:
        payload = {
            "prompt": "Test rapide de l'API",
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        start_time = time.time()
        response = requests.post(
            f"{base_url}/generate",
            json=payload,
            timeout=15
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            try:
                data = response.json()
                content = data.get("content", "")
                response_length = len(content)
                
                print(f"   ✅ SUCCES: {response_length} caracteres ({elapsed:.2f}s)")
                
                # Verifier si c'est une reponse mock
                is_mock = any([
                    "Generated response for:" in content,
                    "mock" in content.lower(),
                    "[Deepseek" in content and "]" in content
                ])
                
                if is_mock:
                    print("   ❌ REPONSE MOCK detectee")
                    print(f"   📄 Extrait: {content[:80]}...")
                else:
                    print("   ✅ REPONSE RELLE detectee")
                    print(f"   📄 Extrait: {content[:80]}...")
                    
            except:
                print(f"   ⚠️  REPONSE NON-JSON: {response.text[:100]}")
        else:
            print(f"   ❌ ECHEC: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
    
    print()
    print("=" * 50)
    print("TEST TERMINE")
    
    # Tester aussi les autres ports
    print("\nTest des autres ports:")
    ports = [8000, 8080, 80]
    
    for port in ports:
        try:
            test_url = f"http://54.81.62.140:{port}/health"
            response = requests.get(test_url, timeout=5)
            if response.status_code == 200:
                print(f"   ✅ Port {port}: Accessible")
            else:
                print(f"   ❌ Port {port}: HTTP {response.status_code}")
        except:
            print(f"   ❌ Port {port}: Inaccessible")

if __name__ == "__main__":
    test_api_quick()