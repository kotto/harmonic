#!/usr/bin/env python3
"""
FINAL STEP SIMPLE - Derniere etape pour LM Arena
Version sans caracteres speciaux pour Windows
"""

import requests
import json
import time
import sys
import os
from datetime import datetime

# Configuration
API_BASE_URL = "http://54.81.62.140:8000"
HEALTH_URL = f"{API_BASE_URL}/health"
GENERATE_URL = f"{API_BASE_URL}/generate"

def check_api_status():
    """Verifier le statut actuel de l'API"""
    
    print("Verification du statut de l'API...")
    print("-" * 40)
    
    try:
        # Test health endpoint
        response = requests.get(HEALTH_URL, timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"[OK] API accessible")
            print(f"   Version: {health_data.get('version', 'unknown')}")
            print(f"   Statut: {health_data.get('status', 'unknown')}")
            print(f"   LM Arena Ready: {health_data.get('lm_arena_ready', False)}")
            
            # Tester si l'API retourne des reponses reelles ou mock
            test_prompt = "What is 2+2?"
            test_payload = {
                "prompt": test_prompt,
                "max_tokens": 50
            }
            
            test_response = requests.post(GENERATE_URL, json=test_payload, timeout=10)
            
            if test_response.status_code == 200:
                test_data = test_response.json()
                content = test_data.get("content", "")
                
                # Verifier si c'est une reponse mock
                is_mock = "Generated response for:" in content
                
                if is_mock:
                    print(f"[MOCK] API en mode MOCK detecte")
                    print(f"   Reponse: {content[:100]}...")
                    return {"status": "mock", "health": health_data}
                else:
                    print(f"[REAL] API en mode REEL detecte")
                    print(f"   Reponse: {content[:100]}...")
                    return {"status": "real", "health": health_data}
            else:
                print(f"[ERROR] Erreur lors du test /generate: HTTP {test_response.status_code}")
                return {"status": "error", "health": health_data}
                
        else:
            print(f"[ERROR] API inaccessible: HTTP {response.status_code}")
            return {"status": "inaccessible"}
            
    except requests.exceptions.ConnectionError:
        print("[ERROR] Impossible de se connecter a l'API")
        return {"status": "connection_error"}
    except requests.exceptions.Timeout:
        print("[ERROR] Timeout lors de la connexion a l'API")
        return {"status": "timeout"}
    except Exception as e:
        print(f"[ERROR] Erreur inattendue: {e}")
        return {"status": "error"}

def run_quick_lm_arena_test():
    """Executer un test LM Arena rapide"""
    
    print("\nTest LM Arena rapide...")
    print("-" * 40)
    
    # Test simple avec 3 prompts
    test_cases = [
        {
            "name": "reasoning",
            "prompt": "If train A leaves Paris at 8:00 AM at 120 km/h, and train B leaves Lyon at 8:30 AM at 150 km/h towards Paris, when will they meet if distance is 450 km?"
        },
        {
            "name": "coding",
            "prompt": "Write Python function to find longest palindrome substring."
        },
        {
            "name": "math",
            "prompt": "Calculate integral of x^2 * sin(x) from 0 to pi."
        }
    ]
    
    results = []
    
    for test in test_cases:
        payload = {
            "prompt": test["prompt"],
            "max_tokens": 200,
            "temperature": 0.7
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(GENERATE_URL, json=payload, timeout=20)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", "")
                
                # Verifier si c'est une reponse mock
                is_mock = "Generated response for:" in content
                
                if is_mock:
                    status = "MOCK"
                else:
                    status = "REAL"
                
                results.append({
                    "test": test["name"],
                    "status": status,
                    "response_time": elapsed,
                    "content_length": len(content),
                    "content_preview": content[:100]
                })
                
                print(f"   {test['name']:10} : {status:8} ({elapsed:.2f}s, {len(content)} chars)")
                
            else:
                results.append({
                    "test": test["name"],
                    "status": "FAILED",
                    "response_time": elapsed,
                    "error": f"HTTP {response.status_code}"
                })
                
                print(f"   {test['name']:10} : FAILED (HTTP {response.status_code})")
                
        except Exception as e:
            elapsed = time.time() - start_time
            results.append({
                "test": test["name"],
                "status": "ERROR",
                "response_time": elapsed,
                "error": str(e)
            })
            
            print(f"   {test['name']:10} : ERROR ({e})")
    
    # Analyser les resultats
    mock_count = sum(1 for r in results if r["status"] == "MOCK")
    real_count = sum(1 for r in results if r["status"] == "REAL")
    
    print(f"\nAnalyse:")
    print(f"- Tests executes: {len(results)}")
    print(f"- Reponses MOCK: {mock_count}")
    print(f"- Reponses REAL: {real_count}")
    
    if real_count == len(results):
        print("\n[SUCCESS] TOUTES LES REPONSES SONT REEL!")
        print("   L'API est prete pour la soumission LM Arena.")
        return True
    elif mock_count > 0:
        print("\n[WARNING] REPONSES MOCK DETECTEES.")
        print("   Pour des tests complets, deployer la version reelle.")
        return False
    else:
        print("\n[ERROR] PROBLEMES DE CONNEXION.")
        print("   Verifiez l'instance EC2.")
        return False

def main():
    """Fonction principale"""
    
    print("=" * 60)
    print("FINAL STEP SIMPLE - DEEPSEEK HARMONIC V2")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Instance: 54.81.62.140:8000")
    print()
    
    # Verifier le statut actuel
    print("ETAPE 1: VERIFICATION DU STATUT ACTUEL")
    print("-" * 40)
    
    api_status = check_api_status()
    
    print("\nETAPE 2: ANALYSE ET PLAN D'ACTION")
    print("-" * 40)
    
    if api_status["status"] == "real":
        print("[OK] L'API est deja en mode REEL")
        print("   Passage direct aux tests LM Arena...")
        
        # Executer les tests LM Arena
        print("\nETAPE 3: TESTS LM ARENA RAPIDES")
        print("-" * 40)
        
        success = run_quick_lm_arena_test()
        
        if success:
            print("\n[MISSION ACCOMPLIE]")
            print("   L'API DeepSeek Harmonic V2 est prete pour LM Arena.")
            
            # Sauvegarder un rapport final
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lm_arena_final_report_{timestamp}.json"
            
            report = {
                "model": "Enhanced Harmonic Hybrid AI v2.0",
                "api_url": API_BASE_URL,
                "test_date": datetime.now().isoformat(),
                "status": "ready_for_lm_arena",
                "recommendations": [
                    "Soumettre les resultats a LM Arena",
                    "Documenter les performances",
                    "Optimiser les parametres de generation"
                ]
            }
            
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"\nRapport sauvegarde dans: {filename}")
            
            return True
        else:
            print("\n[ACTION REQUISE]")
            print("   L'API retourne encore des reponses MOCK.")
            return False
            
    elif api_status["status"] == "mock":
        print("[MOCK] L'API est en mode MOCK")
        print("\nINSTRUCTIONS POUR DEPLOIEMENT:")
        print("=" * 60)
        print("1. Connectez-vous a la console AWS")
        print("2. Ouvrez EC2 Instance Connect pour l'instance")
        print("3. Executez les commandes suivantes:")
        print()
        print("   # Arreter l'API actuelle")
        print("   sudo systemctl stop deepseek-api")
        print()
        print("   # Copier le fichier API reel")
        print("   sudo cp /home/ubuntu/deepseek_api_real_final.py /opt/deepseek/api.py")
        print()
        print("   # Redemarrer l'API")
        print("   sudo systemctl start deepseek-api")
        print()
        print("4. Verifiez avec: sudo systemctl status deepseek-api")
        print()
        print("5. Reexecutez ce script pour tester")
        
        return False
        
    elif api_status["status"] == "inaccessible":
        print("[ERROR] L'API est inaccessible")
        print("\nACTIONS RECOMMANDEES:")
        print("1. Verifiez l'etat de l'instance dans la console AWS")
        print("2. Assurez-vous que les ports 8000 et 22 sont ouverts")
        print("3. Redemarrez l'instance si necessaire")
        
        return False
        
    else:
        print(f"[ERROR] Statut inconnu: {api_status['status']}")
        print("   Verifiez la connectivite reseau")
        
        return False

if __name__ == "__main__":
    try:
        print()
        success = main()
        
        print("\n" + "=" * 60)
        print("EXECUTION TERMINEE")
        print("=" * 60)
        
        if success:
            print("\n[SUCCESS] SUCCES COMPLET!")
            print("   L'API DeepSeek Harmonic V2 est operationnelle.")
            print("   Les tests LM Arena sont prets pour soumission.")
        else:
            print("\n[ACTION REQUISE]")
            print("   Suivez les instructions fournies ci-dessus.")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n[INFO] Execution interrompue par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Exception non geree: {e}")
        sys.exit(1)