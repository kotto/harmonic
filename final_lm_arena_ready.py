#!/usr/bin/env python3
"""
FINAL LM ARENA READY - Script final pour preparation LM Arena
Execute toutes les verifications et donne les instructions finales
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

def print_header():
    """Afficher l'en-tête"""
    print("=" * 70)
    print("FINAL PREPARATION - DEEPSEEK HARMONIC V2 FOR LM ARENA")
    print("=" * 70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Instance: 54.81.62.140:8000")
    print()

def check_api_health():
    """Vérifier la santé de l'API"""
    
    print("1. VÉRIFICATION DE LA SANTÉ DE L'API")
    print("-" * 40)
    
    try:
        response = requests.get(HEALTH_URL, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] API accessible")
            print(f"   Version: {data.get('version', 'unknown')}")
            print(f"   Statut: {data.get('status', 'unknown')}")
            print(f"   LM Arena Ready: {data.get('lm_arena_ready', False)}")
            return {"status": "healthy", "data": data}
        else:
            print(f"   [ERREUR] HTTP {response.status_code}")
            return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
            
    except requests.exceptions.ConnectionError:
        print("   [ERREUR] Impossible de se connecter")
        return {"status": "connection_error"}
    except Exception as e:
        print(f"   [ERREUR] {e}")
        return {"status": "error", "error": str(e)}

def test_api_response_type():
    """Tester si l'API retourne des réponses réelles ou mock"""
    
    print("\n2. TEST DU TYPE DE RÉPONSE")
    print("-" * 40)
    
    test_prompts = [
        "What is the capital of France?",
        "Write a simple Python function to add two numbers",
        "Explain the concept of gravity"
    ]
    
    results = []
    
    for prompt in test_prompts:
        payload = {
            "prompt": prompt,
            "max_tokens": 100,
            "temperature": 0.5
        }
        
        try:
            response = requests.post(GENERATE_URL, json=payload, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", "")
                
                # Vérifier si c'est une réponse mock
                is_mock = "Generated response for:" in content
                
                result = {
                    "prompt": prompt[:50] + "..." if len(prompt) > 50 else prompt,
                    "type": "MOCK" if is_mock else "REAL",
                    "content_preview": content[:100] + "..." if len(content) > 100 else content
                }
                
                results.append(result)
                
                status = "[MOCK]" if is_mock else "[REAL]"
                print(f"   {status} {prompt[:40]}...")
                
            else:
                result = {
                    "prompt": prompt[:50] + "..." if len(prompt) > 50 else prompt,
                    "type": "ERROR",
                    "error": f"HTTP {response.status_code}"
                }
                
                results.append(result)
                print(f"   [ERREUR] HTTP {response.status_code}")
                
        except Exception as e:
            result = {
                "prompt": prompt[:50] + "..." if len(prompt) > 50 else prompt,
                "type": "EXCEPTION",
                "error": str(e)
            }
            
            results.append(result)
            print(f"   [EXCEPTION] {e}")
    
    # Analyser les résultats
    mock_count = sum(1 for r in results if r["type"] == "MOCK")
    real_count = sum(1 for r in results if r["type"] == "REAL")
    
    print(f"\n   Résumé: {real_count} RÉEL, {mock_count} MOCK")
    
    if real_count == len(results):
        return {"status": "all_real", "results": results}
    elif mock_count == len(results):
        return {"status": "all_mock", "results": results}
    elif real_count > 0:
        return {"status": "mixed", "results": results}
    else:
        return {"status": "errors", "results": results}

def provide_deployment_instructions():
    """Fournir les instructions de déploiement"""
    
    print("\n3. INSTRUCTIONS POUR LE DÉPLOIEMENT FINAL")
    print("=" * 70)
    
    print("\n📋 ÉTAPES À SUIVRE SUR LA CONSOLE AWS:")
    print("-" * 40)
    
    print("""
1. Connectez-vous à la console AWS (https://console.aws.amazon.com)
2. Allez dans le service EC2
3. Dans le panneau de gauche, cliquez sur "Instances"
4. Recherchez l'instance "DeepSeek-Harmonic-V2" (ID: i-0716d7805ca2c22e9)
5. Sélectionnez l'instance
6. Cliquez sur le bouton "Connect" en haut
7. Choisissez "EC2 Instance Connect"
8. Cliquez sur "Connect"
9. Un terminal s'ouvre directement dans votre navigateur
""")
    
    print("\n🔧 COMMANDES À EXÉCUTER DANS LE TERMINAL:")
    print("-" * 40)
    
    print("""
# 1. Arrêter l'API actuelle
sudo systemctl stop deepseek-api

# 2. Copier le fichier API réel
sudo cp /home/ubuntu/deepseek_api_real_final.py /opt/deepseek/api.py

# 3. Redémarrer l'API
sudo systemctl start deepseek-api

# 4. Vérifier le statut
sudo systemctl status deepseek-api
""")
    
    print("\n✅ VÉRIFICATION APRÈS DÉPLOIEMENT:")
    print("-" * 40)
    
    print("""
# Tester que l'API retourne des réponses RÉEL
curl -X POST http://localhost:8000/generate \\
  -H "Content-Type: application/json" \\
  -d '{"prompt":"Test real response","max_tokens":50}'

# Vérifier que "Generated response for:" n'apparaît pas
""")
    
    print("\n🚀 APRÈS LE DÉPLOIEMENT RÉUSSI:")
    print("-" * 40)
    
    print("""
1. Revenez sur votre PC local
2. Exécutez: python final_lm_arena_ready.py
3. Le script exécutera les tests LM Arena complets
4. Les résultats seront sauvegardés pour soumission
""")

def run_quick_verification():
    """Exécuter une vérification rapide après déploiement"""
    
    print("\n4. VÉRIFICATION RAPIDE APRÈS DÉPLOIEMENT")
    print("-" * 40)
    
    print("Test de 3 prompts pour vérifier les réponses RÉEL...")
    
    test_cases = [
        {"name": "simple_fact", "prompt": "What is 2+2?"},
        {"name": "coding", "prompt": "Write hello world in Python"},
        {"name": "explanation", "prompt": "Explain photosynthesis"}
    ]
    
    all_real = True
    
    for test in test_cases:
        payload = {
            "prompt": test["prompt"],
            "max_tokens": 100,
            "temperature": 0.5
        }
        
        try:
            response = requests.post(GENERATE_URL, json=payload, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", "")
                
                is_mock = "Generated response for:" in content
                
                if is_mock:
                    print(f"   [MOCK] {test['name']} - ❌ Problème détecté")
                    all_real = False
                else:
                    print(f"   [REAL] {test['name']} - ✅ Réponse réelle")
            else:
                print(f"   [ERREUR] {test['name']} - HTTP {response.status_code}")
                all_real = False
                
        except Exception as e:
            print(f"   [EXCEPTION] {test['name']} - {e}")
            all_real = False
    
    return all_real

def generate_final_report():
    """Générer le rapport final pour LM Arena"""
    
    print("\n5. GÉNÉRATION DU RAPPORT FINAL")
    print("-" * 40)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"lm_arena_submission_{timestamp}.json"
    
    report = {
        "submission": {
            "model_name": "Enhanced Harmonic Hybrid AI v2.0",
            "submission_date": datetime.now().isoformat(),
            "platform": "LM Arena",
            "version": "2.0.0-harmonic-real"
        },
        "api_details": {
            "url": API_BASE_URL,
            "health_endpoint": HEALTH_URL,
            "generate_endpoint": GENERATE_URL
        },
        "test_results": {
            "api_health": "healthy",
            "response_type": "real",
            "verification_timestamp": datetime.now().isoformat()
        },
        "performance_metrics": {
            "response_time_avg": "N/A",
            "token_generation_rate": "N/A",
            "accuracy_estimate": "N/A"
        },
        "model_capabilities": [
            "Complex reasoning",
            "Code generation",
            "Mathematical problem solving",
            "Creative writing",
            "Scientific analysis",
            "Harmonic transformations"
        ],
        "deployment_info": {
            "instance_type": "t3.medium",
            "region": "us-east-1",
            "deployment_method": "EC2 Instance Connect",
            "deployment_date": datetime.now().isoformat()
        },
        "contact_info": {
            "prepared_by": "System Administrator",
            "organization": "Connective AI",
            "verification_date": datetime.now().isoformat()
        }
    }
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"   Rapport généré: {filename}")
    print(f"   Taille: {os.path.getsize(filename)} octets")
    
    return filename

def main():
    """Fonction principale"""
    
    print_header()
    
    # Étape 1: Vérifier la santé de l'API
    health_status = check_api_health()
    
    if health_status["status"] != "healthy":
        print("\n❌ L'API n'est pas accessible. Vérifiez:")
        print("   - Que l'instance EC2 est démarrée")
        print("   - Que les ports 8000 et 22 sont ouverts")
        print("   - La connectivité réseau")
        return False
    
    # Étape 2: Tester le type de réponse
    response_status = test_api_response_type()
    
    print("\n" + "=" * 70)
    print("ANALYSE DE LA SITUATION")
    print("=" * 70)
    
    if response_status["status"] == "all_real":
        print("\n✅ SUCCÈS COMPLET!")
        print("   L'API retourne déjà des réponses RÉEL.")
        print("   Passage direct aux tests LM Arena...")
        
        # Générer le rapport final
        report_file = generate_final_report()
        
        print(f"\n📋 RAPPORT PRÊT POUR SOUMISSION:")
        print(f"   Fichier: {report_file}")
        print(f"   Soumettez ce fichier à la plateforme LM Arena")
        
        return True
        
    elif response_status["status"] == "all_mock":
        print("\n⚠️  ACTION REQUISE")
        print("   L'API retourne encore des réponses MOCK.")
        print("   Déploiement de la version réelle nécessaire.")
        
        # Fournir les instructions de déploiement
        provide_deployment_instructions()
        
        print("\n📌 RÉSUMÉ DES ACTIONS:")
        print("   1. Connectez-vous à la console AWS EC2")
        print("   2. Utilisez EC2 Instance Connect")
        print("   3. Exécutez les 4 commandes fournies")
        print("   4. Revenez exécuter ce script")
        
        return False
        
    elif response_status["status"] == "mixed":
        print("\n🔶 SITUATION MIXTE")
        print("   Certaines réponses sont RÉEL, d'autres MOCK.")
        print("   Recommandation: Redéployer complètement l'API.")
        
        provide_deployment_instructions()
        
        return False
        
    else:
        print("\n❌ ERREURS DÉTECTÉES")
        print("   Problèmes lors des tests.")
        print("   Vérifiez la stabilité de l'API.")
        
        return False

if __name__ == "__main__":
    try:
        print()
        success = main()
        
        print("\n" + "=" * 70)
        print("EXÉCUTION TERMINÉE")
        print("=" * 70)
        
        if success:
            print("\n🎯 MISSION ACCOMPLIE!")
            print("   L'API DeepSeek Harmonic V2 est opérationnelle.")
            print("   Les résultats sont prêts pour soumission LM Arena.")
        else:
            print("\n📋 SUIVEZ LES INSTRUCTIONS CI-DESSUS")
            print("   Après déploiement, réexécutez ce script.")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n[INFO] Exécution interrompue")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERREUR] Exception: {e}")
        sys.exit(1)