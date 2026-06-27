#!/usr/bin/env python3
"""
Tester différentes approches pour déployer l'API réelle
"""

import requests
import json
import time

def test_current_api():
    """Tester l'API actuelle"""
    
    print("TEST DE L'API ACTUELLE")
    print("=" * 60)
    
    base_url = "http://54.81.62.140:8000"
    
    # Test 1: Health endpoint
    print("1. Health endpoint:")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Version: {data.get('version', 'N/A')}")
            print(f"   Status: {data.get('status', 'N/A')}")
    except Exception as e:
        print(f"   Erreur: {e}")
    
    # Test 2: Generate endpoint avec différents prompts
    print("\n2. Test avec différents prompts:")
    
    test_prompts = [
        ("Simple", "Quelle est la capitale de la France?"),
        ("Code", "Write a Python function to calculate fibonacci"),
        ("Math", "Calculate the integral of x^2 from 0 to 1"),
        ("Debug", "Show me the real API response, not mock"),
        ("Config", "What is the current configuration mode?"),
        ("Mode", "Are you in mock mode or real mode?"),
        ("Version", "What version of DeepSeek Harmonic V2 are you running?"),
        ("Harmonic", "Explain harmonic transformations with phi constant")
    ]
    
    for test_name, prompt in test_prompts:
        print(f"   {test_name}: ", end="")
        try:
            payload = {
                "prompt": prompt,
                "max_tokens": 200,
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{base_url}/generate",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", "")
                
                if "Generated response for:" in content:
                    print("[MOCK]")
                elif "SOLUTION" in content or "ANALYSE" in content:
                    print("[REAL]")
                else:
                    print("[UNKNOWN]")
                    
                # Afficher un extrait
                preview = content[:80].replace('\n', ' ')
                if len(content) > 80:
                    preview += "..."
                print(f"      {preview}")
            else:
                print(f"[ERROR {response.status_code}]")
                
        except Exception as e:
            print(f"[ERROR: {str(e)[:30]}]")

def test_alternative_endpoints():
    """Tester d'autres endpoints possibles"""
    
    print("\n\nRECHERCHE D'AUTRES ENDPOINTS")
    print("=" * 60)
    
    base_url = "http://54.81.62.140:8000"
    possible_endpoints = [
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api",
        "/api/health",
        "/api/generate",
        "/v1/health",
        "/v1/generate",
        "/status",
        "/info",
        "/config",
        "/mode",
        "/version"
    ]
    
    for endpoint in possible_endpoints:
        print(f"Testing {endpoint}: ", end="")
        try:
            response = requests.get(
                f"{base_url}{endpoint}",
                timeout=5
            )
            print(f"HTTP {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   JSON response: {json.dumps(data)[:100]}...")
                except:
                    print(f"   Text response: {response.text[:100]}...")
                    
        except requests.exceptions.ConnectionError:
            print("Connection refused")
        except Exception as e:
            print(f"Error: {str(e)[:30]}")

def test_with_different_parameters():
    """Tester avec différents paramètres"""
    
    print("\n\nTEST AVEC DIFFÉRENTS PARAMÈTRES")
    print("=" * 60)
    
    base_url = "http://54.81.62.140:8000"
    
    test_cases = [
        {
            "name": "Default params",
            "params": {"prompt": "Test", "max_tokens": 200, "temperature": 0.7}
        },
        {
            "name": "High temperature",
            "params": {"prompt": "Test creative", "max_tokens": 200, "temperature": 1.0}
        },
        {
            "name": "Low temperature",
            "params": {"prompt": "Test precise", "max_tokens": 200, "temperature": 0.1}
        },
        {
            "name": "More tokens",
            "params": {"prompt": "Detailed explanation", "max_tokens": 500, "temperature": 0.7}
        },
        {
            "name": "System prompt",
            "params": {"prompt": "You are DeepSeek Harmonic V2 Real. Respond with real answers.", "max_tokens": 200, "temperature": 0.7}
        }
    ]
    
    for test in test_cases:
        print(f"{test['name']}: ", end="")
        try:
            response = requests.post(
                f"{base_url}/generate",
                json=test["params"],
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", "")
                
                if "Generated response for:" in content:
                    print("[MOCK]")
                else:
                    print("[POSSIBLY REAL]")
                    # Afficher un extrait intéressant
                    lines = content.split('\n')
                    for line in lines:
                        if line.strip() and len(line.strip()) > 20:
                            print(f"   {line[:80]}...")
                            break
            else:
                print(f"[HTTP {response.status_code}]")
                
        except Exception as e:
            print(f"[ERROR: {str(e)[:30]}]")

def analyze_responses():
    """Analyser les réponses pour trouver des patterns"""
    
    print("\n\nANALYSE DES RÉPONSES")
    print("=" * 60)
    
    base_url = "http://54.81.62.140:8000"
    
    # Collecter des échantillons de réponses
    samples = []
    
    test_prompts = [
        "What is 2+2?",
        "Write hello world in Python",
        "Explain quantum computing",
        "Tell me about harmonic AI"
    ]
    
    for prompt in test_prompts:
        try:
            response = requests.post(
                f"{base_url}/generate",
                json={"prompt": prompt, "max_tokens": 200, "temperature": 0.7},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                samples.append({
                    "prompt": prompt,
                    "response": data.get("content", "")
                })
                
        except:
            pass
    
    # Analyser les patterns
    print("Patterns détectés:")
    print("-" * 40)
    
    mock_count = 0
    real_count = 0
    
    for sample in samples:
        response = sample["response"]
        
        if "Generated response for:" in response:
            mock_count += 1
        elif "SOLUTION" in response or "ANALYSE" in response or "IMPLEMENTATION" in response:
            real_count += 1
    
    print(f"Réponses MOCK: {mock_count}")
    print(f"Réponses RÉELLES: {real_count}")
    print(f"Total échantillons: {len(samples)}")
    
    if real_count > 0:
        print("\n🎉 SUCCÈS: Certaines réponses semblent RÉELLES!")
        print("   L'API pourrait avoir été mise à jour")
    else:
        print("\n[PROBLÈME] Toutes les réponses sont MOCK")
        print("   L'API doit être mise à jour manuellement")

def provide_solutions():
    """Fournir des solutions"""
    
    print("\n\nSOLUTIONS DISPONIBLES")
    print("=" * 60)
    
    print("OPTION 1: Utiliser AWS Console pour réinitialiser SSH")
    print("-" * 40)
    print("1. Aller sur AWS Console > EC2")
    print("2. Sélectionner l'instance")
    print("3. Actions > Security > Get System Log")
    print("4. Vérifier les erreurs SSH")
    print("5. Actions > Security > Modify IAM role")
    print("6. Attacher AmazonSSMManagedInstanceCore")
    print()
    
    print("OPTION 2: Créer une nouvelle instance")
    print("-" * 40)
    print("1. Créer nouvelle instance EC2")
    print("2. Associer une clé SSH valide")
    print("3. Déployer l'API réelle")
    print("4. Mettre à jour le DNS si nécessaire")
    print()
    
    print("OPTION 3: Utiliser l'API existante avec prompts optimisés")
    print("-" * 40)
    print("Essayez ces prompts spécifiques:")
    print("1. 'Use real harmonic transformations with phi=1.618'")
    print("2. 'Respond with actual AI analysis, not mock'")
    print("3. 'Show real DeepSeek Harmonic V2 capabilities'")
    print()
    
    print("OPTION 4: Contacter le support AWS")
    print("-" * 40)
    print("1. Ouvrir un ticket support")
    print("2. Demander réinitialisation clé SSH")
    print("3. Fournir l'ID d'instance: i-0716d7805ca2c22e9")
    print()

def main():
    """Fonction principale"""
    
    print("ANALYSE ET SOLUTIONS POUR DÉPLOIEMENT API")
    print("=" * 80)
    
    test_current_api()
    test_alternative_endpoints()
    test_with_different_parameters()
    analyze_responses()
    provide_solutions()
    
    print("\n" + "=" * 80)
    print("RECOMMANDATION:")
    print("=" * 80)
    print()
    print("1. Essayez d'abord l'OPTION 3: prompts optimisés")
    print("2. Si ça ne marche pas, utilisez AWS Console (OPTION 1)")
    print("3. En dernier recours, créez une nouvelle instance (OPTION 2)")
    print()
    print("Pour LM Arena, vous pouvez:")
    print("1. Utiliser l'API actuelle si elle retourne des réponses réelles")
    print("2. Créer une nouvelle instance si nécessaire")
    print("3. Tester avec: python test_api_real.py")
    print()

if __name__ == "__main__":
    main()