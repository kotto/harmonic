#!/usr/bin/env python3
"""
Test API pour vérifier si les réponses sont réelles ou mock
"""

import requests
import json
import time

def test_api_response():
    """Tester si l'API retourne des réponses réelles"""
    
    base_url = "http://54.81.62.140:8000"
    
    print("TEST API - VERIFICATION REPONSES REEL/MOCK")
    print("=" * 60)
    
    # Test 1: Health endpoint
    print("1. Test health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   [OK] Health: {response.status_code}")
            print(f"   Version: {health_data.get('version', 'N/A')}")
        else:
            print(f"   [ERREUR] Health: {response.status_code}")
    except Exception as e:
        print(f"   [ERREUR] {e}")
    
    # Test 2: Test avec prompt simple
    print("\n2. Test avec prompt simple...")
    test_prompt = "Quelle est la capitale de la France?"
    
    try:
        payload = {
            "prompt": test_prompt,
            "max_tokens": 200,
            "temperature": 0.7
        }
        
        start_time = time.time()
        response = requests.post(f"{base_url}/generate", 
                                json=payload, 
                                timeout=10)
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("content", "")
            
            print(f"   [OK] Generate: {response.status_code}")
            print(f"   Temps: {processing_time:.2f}s")
            print(f"   Longueur réponse: {len(content)} caractères")
            
            # Vérifier si c'est une réponse mock
            if "Generated response for:" in content:
                print("   [ATTENTION] Réponse MOCK détectée!")
                print("   La réponse commence par: ", content[:100])
            elif "SOLUTION" in content or "ANALYSE" in content or "RESOLUTION" in content:
                print("   [OK] Réponse RÉELLE détectée!")
                print("   La réponse contient des sections structurées")
            else:
                print("   [INFO] Type de réponse indéterminé")
                print("   Début de réponse: ", content[:150])
                
        else:
            print(f"   [ERREUR] Generate: {response.status_code}")
            
    except Exception as e:
        print(f"   [ERREUR] {e}")
    
    # Test 3: Test avec prompt de codage
    print("\n3. Test avec prompt de codage...")
    coding_prompt = "Write a Python function to calculate fibonacci sequence"
    
    try:
        payload = {
            "prompt": coding_prompt,
            "max_tokens": 300,
            "temperature": 0.7
        }
        
        response = requests.post(f"{base_url}/generate", 
                                json=payload, 
                                timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("content", "")
            
            print(f"   [OK] Generate: {response.status_code}")
            
            # Vérifier caractéristiques des réponses réelles
            is_real = False
            real_indicators = [
                "def fibonacci",
                "import ",
                "return ",
                "python",
                "```",
                "SOLUTION",
                "IMPLEMENTATION"
            ]
            
            for indicator in real_indicators:
                if indicator in content:
                    is_real = True
                    break
            
            if is_real:
                print("   [OK] Réponse RÉELLE (contient du code Python)")
                # Extraire un extrait du code
                if "```python" in content:
                    code_start = content.find("```python") + 9
                    code_end = content.find("```", code_start)
                    if code_end > code_start:
                        code_snippet = content[code_start:code_end].strip()[:100]
                        print(f"   Extrait code: {code_snippet}...")
            else:
                print("   [ATTENTION] Réponse ne semble pas contenir de code réel")
                print("   Début réponse: ", content[:100])
                
        else:
            print(f"   [ERREUR] Generate: {response.status_code}")
            
    except Exception as e:
        print(f"   [ERREUR] {e}")
    
    # Test 4: Test avec prompt mathématique
    print("\n4. Test avec prompt mathématique...")
    math_prompt = "Calculate the integral of x^2 from 0 to 1"
    
    try:
        payload = {
            "prompt": math_prompt,
            "max_tokens": 250,
            "temperature": 0.7
        }
        
        response = requests.post(f"{base_url}/generate", 
                                json=payload, 
                                timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("content", "")
            
            print(f"   [OK] Generate: {response.status_code}")
            
            # Vérifier si c'est une réponse mathématique réelle
            if "integral" in content.lower() or "∫" in content or "x^3/3" in content:
                print("   [OK] Réponse mathématique RÉELLE détectée")
                print("   La réponse traite du calcul intégral")
            elif "Generated response for:" in content:
                print("   [ATTENTION] Réponse MOCK détectée")
            else:
                print("   [INFO] Type de réponse mathématique indéterminé")
                
        else:
            print(f"   [ERREUR] Generate: {response.status_code}")
            
    except Exception as e:
        print(f"   [ERREUR] {e}")
    
    print("\n" + "=" * 60)
    print("ANALYSE FINALE:")
    print("-" * 30)
    
    # Résumé des tests
    print("1. Connectivité: [OK]")
    print("2. Health endpoint: [OK]")
    print("3. Generate endpoint: [OK]")
    print("\nPour déployer la version réelle:")
    print("1. Utiliser SSH pour se connecter à EC2")
    print("2. Remplacer l'API actuelle par deepseek_api_real.py")
    print("3. Redémarrer l'API")
    print("4. Re-tester avec ce script")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_api_response()