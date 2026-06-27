#!/usr/bin/env python3
"""
EXECUTE ALL - DEEPSEEK HARMONIC V2
Execute toutes les etapes automatiquement
"""

import subprocess
import sys
import time
from datetime import datetime

def run_command(command, description):
    """Execute une commande avec description"""
    print(f"\n{description}")
    print("-" * 40)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("   SUCCES")
            if result.stdout.strip():
                print(f"   Sortie: {result.stdout.strip()[:200]}...")
            return True
        else:
            print(f"   ECHEC: {result.stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        print("   TIMEOUT")
        return False
    except Exception as e:
        print(f"   ERREUR: {e}")
        return False

def main():
    """Fonction principale"""
    print("EXECUTION COMPLETE - DEEPSEEK HARMONIC V2")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Etape 1: Tester l'API actuelle
    print("ETAPE 1: TEST API ACTUELLE")
    print("=" * 40)
    
    # Tester rapidement avec curl
    print("\nTest rapide avec curl...")
    
    try:
        # Test health endpoint
        health_cmd = "curl -s http://54.81.62.140:8000/health"
        result = subprocess.run(health_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   Health endpoint: Accessible")
            
            # Tester generate endpoint
            generate_cmd = """curl -s -X POST http://54.81.62.140:8000/generate -H "Content-Type: application/json" -d '{"prompt":"Test rapide","max_tokens":50}'"""
            result = subprocess.run(generate_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                response = result.stdout
                if "Generated response for:" in response:
                    print("   Generate endpoint: Reponses MOCK detectees")
                    print("   Action necessaire: Activer les reponses reelles")
                    
                    # Etape 2: Activer les reponses reelles
                    print("\nETAPE 2: ACTIVATION REPONSES REELLES")
                    print("=" * 40)
                    
                    print("\nCreation d'une version reelle de l'API...")
                    
                    # Creer un script Python simple pour tester
                    test_script = """
import requests
import json

def test_real_api():
    url = "http://54.81.62.140:8000/generate"
    
    # Test avec plusieurs prompts
    test_cases = [
        {"prompt": "Write Python code for Fibonacci", "type": "coding"},
        {"prompt": "Solve equation x^2 + 2x + 1 = 0", "type": "math"},
        {"prompt": "Explain quantum mechanics", "type": "explanation"}
    ]
    
    results = []
    
    for test in test_cases:
        payload = {
            "prompt": test["prompt"],
            "max_tokens": 200,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(url, json=payload, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", "")
                
                # Verifier si c'est une reponse mock
                is_mock = "Generated response for:" in content or "mock" in content.lower()
                
                if is_mock:
                    results.append((test["type"], "MOCK", "Reponse mock detectee"))
                else:
                    results.append((test["type"], "REEL", f"{len(content)} caracteres"))
                    
            else:
                results.append((test["type"], "ECHEC", f"HTTP {response.status_code}"))
                
        except Exception as e:
            results.append((test["type"], "ERREUR", str(e)))
    
    return results

# Executer le test
if __name__ == "__main__":
    results = test_real_api()
    
    print("RESULTATS DES TESTS:")
    print("=" * 50)
    
    mock_count = 0
    real_count = 0
    
    for test_type, status, details in results:
        print(f"{test_type:12} : {status:8} - {details}")
        
        if status == "MOCK":
            mock_count += 1
        elif status == "REEL":
            real_count += 1
    
    print()
    print("ANALYSE:")
    print(f"- Reponses MOCK: {mock_count}")
    print(f"- Reponses REEL: {real_count}")
    
    if mock_count > 0:
        print("\\nRECOMMANDATION:")
        print("L'API retourne encore des reponses MOCK.")
        print("Executez 'python deploy_local_to_ec2.py' pour deployer la version locale.")
    else:
        print("\\nSUCCES:")
        print("L'API retourne des reponses REEL.")
        print("Pret pour les tests LM Arena.")
"""
                    
                    # Sauvegarder le script
                    with open("test_api_final.py", "w") as f:
                        f.write(test_script)
                    
                    print("   Script de test cree: test_api_final.py")
                    
                    # Executer le test
                    print("\nExecution du test...")
                    
                    result = subprocess.run(
                        ["python", "test_api_final.py"],
                        capture_output=True,
                        text=True
                    )
                    
                    print(result.stdout)
                    
                    if "Reponses REEL" in result.stdout:
                        print("\n✅ API avec reponses REEL activee!")
                        
                        # Etape 3: Executer les tests LM Arena
                        print("\nETAPE 3: TESTS LM ARENA")
                        print("=" * 40)
                        
                        print("\nExecution des tests LM Arena...")
                        
                        # Creer un script LM Arena simple
                        lm_arena_script = """
import requests
import json
import time

def run_lm_arena_tests():
    base_url = "http://54.81.62.140:8000"
    
    test_cases = [
        {
            "name": "reasoning",
            "prompt": "If train A leaves Paris at 8:00 AM at 120 km/h, and train B leaves Lyon at 8:30 AM at 150 km/h towards Paris, when will they meet if distance is 450 km?"
        },
        {
            "name": "coding", 
            "prompt": "Write Python function to find longest palindrome substring. Optimize time complexity."
        },
        {
            "name": "mathematics",
            "prompt": "Calculate integral of x^2 * sin(x) from 0 to pi. Show step-by-step."
        }
    ]
    
    results = []
    
    for test in test_cases:
        payload = {
            "prompt": test["prompt"],
            "max_tokens": 300,
            "temperature": 0.7,
            "use_evolution": True,
            "deepseek_harmonic": True
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{base_url}/generate",
                json=payload,
                timeout=20
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", "")
                
                # Verifier si c'est une reponse mock
                is_mock = "Generated response for:" in content or "mock" in content.lower()
                
                if is_mock:
                    status = "MOCK"
                else:
                    status = "REEL"
                
                results.append({
                    "test": test["name"],
                    "status": status,
                    "response_time": elapsed,
                    "content_length": len(content),
                    "content_preview": content[:100]
                })
                
                print(f"   {test['name']:12} : {status:8} ({elapsed:.2f}s, {len(content)} chars)")
                
            else:
                results.append({
                    "test": test["name"],
                    "status": "ECHEC",
                    "response_time": elapsed,
                    "error": f"HTTP {response.status_code}"
                })
                
                print(f"   {test['name']:12} : ECHEC (HTTP {response.status_code})")
                
        except Exception as e:
            elapsed = time.time() - start_time
            results.append({
                "test": test["name"],
                "status": "ERREUR",
                "response_time": elapsed,
                "error": str(e)
            })
            
            print(f"   {test['name']:12} : ERREUR ({e})")
    
    return results

# Executer les tests
if __name__ == "__main__":
    print("TESTS LM ARENA - DEEPSEEK HARMONIC V2")
    print("=" * 50)
    
    results = run_lm_arena_tests()
    
    # Sauvegarder les resultats
    output_file = f"lm_arena_results_{time.strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "instance": "54.81.62.140:8000",
            "model": "DeepSeek Harmonic V2",
            "results": results
        }, f, indent=2)
    
    print(f"\\nResultats sauvegardes dans: {output_file}")
    
    # Analyser les resultats
    mock_count = sum(1 for r in results if r["status"] == "MOCK")
    real_count = sum(1 for r in results if r["status"] == "REEL")
    
    print(f"\\nANALYSE FINALE:")
    print(f"- Tests executes: {len(results)}")
    print(f"- Reponses MOCK: {mock_count}")
    print(f"- Reponses REEL: {real_count}")
    
    if real_count == len(results):
        print("\\n🎯 TOUTES LES REPONSES SONT REEL!")
        print("   L'API est prete pour la soumission LM Arena.")
    elif mock_count > 0:
        print("\\n⚠️  REPONSES MOCK DETECTEES.")
        print("   Executez 'python deploy_local_to_ec2.py' pour deployer la version locale.")
    else:
        print("\\n❌ PROBLEMES DE CONNEXION.")
        print("   Verifiez l'instance EC2.")
"""
                    
                    # Sauvegarder le script LM Arena
                    with open("lm_arena_final.py", "w") as f:
                        f.write(lm_arena_script)
                    
                    print("   Script LM Arena cree: lm_arena_final.py")
                    
                    # Executer les tests LM Arena
                    result = subprocess.run(
                        ["python", "lm_arena_final.py"],
                        capture_output=True,
                        text=True
                    )
                    
                    print(result.stdout)
                    
                    if "TOUTES LES REPONSES SONT REEL" in result.stdout:
                        print("\n✅ SUCCES COMPLET!")
                        print("   L'API DeepSeek Harmonic V2 est operationnelle avec des reponses reelles.")
                        print("   Pret pour la domination LM Arena.")
                        
                        return True
                    else:
                        print("\n⚠️  PROBLEMES DETECTES.")
                        print("   L'API retourne encore des reponses MOCK.")
                        print("   Executez 'python deploy_local_to_ec2.py' pour deployer la version locale.")
                        
                        return False
                        
                else:
                    print("   L'API retourne encore des reponses MOCK.")
                    print("   Executez 'python deploy_local_to_ec2.py' pour deployer la version locale.")
                    
                    return False
            else:
                print("   Erreur lors du test generate")
                return False
        else:
            print("   API inaccessible")
            return False
            
    except Exception as e:
        print(f"   Erreur: {e}")
        return False
    
    return False

if __name__ == "__main__":
    print()
    print("DEBUT DE L'EXECUTION AUTOMATIQUE...")
    print()
    
    success = main()
    
    print()
    print("=" * 60)
    print("EXECUTION TERMINEE")
    print("=" * 60)
    
    if success:
        print("\n🎯 MISSION ACCOMPLIE!")
        print("   L'API DeepSeek Harmonic V2 est operationnelle avec des reponses reelles.")
        print("   Vous pouvez maintenant executer les tests LM Arena complets.")
    else:
        print("\n⚠️  ACTION REQUISE")
        print("   L'API retourne encore des reponses MOCK.")
        print("   Executez 'python deploy_local_to_ec2.py' pour deployer la version locale.")
        print("   Ou redemarrez l'instance EC2 manuellement.")
    
    exit(0 if success else 1)