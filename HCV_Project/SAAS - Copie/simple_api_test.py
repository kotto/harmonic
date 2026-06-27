#!/usr/bin/env python3
"""
Simple API Test - Qwen35 Enhanced
====================================

Test simple pour vérifier le format de réponse de l'API
"""

import requests
import json

def test_api():
    """Test simple de l'API"""
    url = "https://lymk98dbvk.execute-api.us-east-1.amazonaws.com/prod/generate"
    
    payload = {
        "prompt": "Test simple",
        "max_length": 100
    }
    
    print("🧪 Test simple de l'API Qwen35 Enhanced")
    print(f"URL: {url}")
    print(f"Payload: {payload}")
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Parsed JSON: {json.dumps(data, indent=2)}")
            except:
                print("❌ Impossible de parser le JSON")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_api()
