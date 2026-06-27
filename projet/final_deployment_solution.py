#!/usr/bin/env python3
"""
FINAL DEPLOYMENT SOLUTION - Solution pour la derniere etape
Deploiement de l'API reelle sur EC2 sans SSH direct
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

def check_current_status():
    """Verifier le statut actuel de l'API"""
    
    print("Verification du statut actuel...")
    print("-" * 40)
    
    try:
        response = requests.get(HEALTH_URL, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] API accessible")
            print(f"   Version: {data.get('version', 'unknown')}")
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   LM Arena Ready: {data.get('lm_arena_ready', False)}")
            
            # Tester si c'est mock ou reel
            test_response = requests.post(
                GENERATE_URL,
                json={"prompt": "Test", "max_tokens": 50},
                timeout=10
            )
            
            if test_response.status_code == 200:
                test_data = test_response.json()
                content = test_data.get("content", "")
                
                if "Generated response for:" in content:
                    print(f"[MOCK] Mode MOCK detecte")
                    return {"status": "mock", "data": data}
                else:
                    print(f"[REAL] Mode REEL detecte")
                    return {"status": "real", "data": data}
            else:
                print(f"[ERROR] Test generate failed: HTTP {test_response.status_code}")
                return {"status": "error", "data": data}
                
        else:
            print(f"[ERROR] API inaccessible: HTTP {response.status_code}")
            return {"status": "inaccessible"}
            
    except Exception as e:
        print(f"[ERROR] {e}")
        return {"status": "connection_error"}

def create_deployment_script():
    """Creer un script de deploiement pour EC2"""
    
    print("\nCreation du script de deploiement...")
    print("-" * 40)
    
    # Lire le fichier API reel
    api_file = "deepseek_api_real_final.py"
    
    if not os.path.exists(api_file):
        print(f"[ERROR] Fichier {api_file} non trouve")
        return None
    
    with open(api_file, "r", encoding="utf-8") as f:
        api_content = f.read()
    
    # Creer un script de deploiement
    deployment_script = f"""#!/bin/bash
# DEPLOYMENT SCRIPT FOR DEEPSEEK HARMONIC V2 REAL API
# Executez ce script sur l'instance EC2

echo "=== DEPLOIEMENT API REEL DEEPSEEK HARMONIC V2 ==="
echo "Date: $(date)"
echo

# Arreter l'API actuelle
echo "1. Arret de l'API actuelle..."
sudo systemctl stop deepseek-api 2>/dev/null || true
sudo pkill -f "python.*deepseek" 2>/dev/null || true

# Creer le repertoire de l'API
echo "2. Creation des repertoires..."
sudo mkdir -p /opt/deepseek
sudo mkdir -p /var/log/deepseek

# Copier le nouveau fichier API
echo "3. Copie du fichier API reel..."
cat > /tmp/deepseek_api_real.py << 'EOF'
{api_content}
EOF

sudo cp /tmp/deepseek_api_real.py /opt/deepseek/api.py
sudo chmod +x /opt/deepseek/api.py

# Creer le service systemd
echo "4. Configuration du service systemd..."
cat > /tmp/deepseek-api.service << 'EOF'
[Unit]
Description=DeepSeek Harmonic V2 Real API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/deepseek
ExecStart=/usr/bin/python3 /opt/deepseek/api.py
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=deepseek-api

[Install]
WantedBy=multi-user.target
EOF

sudo cp /tmp/deepseek-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable deepseek-api

# Installer les dependances
echo "5. Installation des dependances..."
sudo apt-get update
sudo apt-get install -y python3-pip
sudo pip3 install fastapi uvicorn pydantic

# Demarrer le service
echo "6. Demarrage du service..."
sudo systemctl start deepseek-api

# Verifier le statut
echo "7. Verification du statut..."
sleep 3
sudo systemctl status deepseek-api --no-pager

echo
echo "=== DEPLOIEMENT TERMINE ==="
echo "API disponible sur: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"
echo "Health check: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000/health"
"""
    
    # Sauvegarder le script
    script_file = "deploy_real_api.sh"
    
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(deployment_script)
    
    print(f"[OK] Script cree: {script_file}")
    print(f"   Taille: {len(deployment_script)} caracteres")
    
    # Creer aussi une version pour User Data
    user_data_script = f"""#!/bin/bash
# USER DATA SCRIPT FOR EC2 LAUNCH
# Ce script s'execute automatiquement au demarrage de l'instance

{deployment_script}
"""
    
    user_data_file = "user_data_deploy.sh"
    
    with open(user_data_file, "w", encoding="utf-8") as f:
        f.write(user_data_script)
    
    print(f"[OK] Script User Data cree: {user_data_file}")
    
    return script_file

def provide_deployment_instructions():
    """Fournir les instructions de deploiement"""
    
    print("\n" + "=" * 60)
    print("INSTRUCTIONS POUR LE DEPLOIEMENT FINAL")
    print("=" * 60)
    
    print("\nOPTION 1: Via EC2 Instance Connect (Recommandee)")
    print("-" * 40)
    print("1. Allez dans la console AWS EC2")
    print("2. Selectionnez l'instance: DeepSeek-Harmonic-V2")
    print("3. Cliquez sur 'Connect'")
    print("4. Choisissez 'EC2 Instance Connect'")
    print("5. Dans le terminal, telechargez le script:")
    print("   curl -O https://raw.githubusercontent.com/votre-repo/deploy_real_api.sh")
    print("6. Executez le script:")
    print("   chmod +x deploy_real_api.sh")
    print("   sudo ./deploy_real_api.sh")
    
    print("\nOPTION 2: Via User Data (Redemarrage de l'instance)")
    print("-" * 40)
    print("1. Arretez l'instance EC2")
    print("2. Modifiez l'instance -> User Data")
    print("3. Copiez le contenu de user_data_deploy.sh")
    print("4. Redemarrez l'instance")
    print("5. L'API se deployera automatiquement")
    
    print("\nOPTION 3: Via AWS Systems Manager (SSM)")
    print("-" * 40)
    print("1. Assurez-vous que l'instance a le role IAM pour SSM")
    print("2. Allez dans AWS Systems Manager")
    print("3. Selectionnez 'Run Command'")
    print("4. Choisissez 'AWS-RunShellScript'")
    print("5. Copiez les commandes du script de deploiement")
    
    print("\nOPTION 4: Manuellement via la console")
    print("-" * 40)
    print("1. Connectez-vous via EC2 Instance Connect")
    print("2. Executez ces commandes:")
    print("   sudo systemctl stop deepseek-api")
    print("   sudo cp /home/ubuntu/deepseek_api_real_final.py /opt/deepseek/api.py")
    print("   sudo systemctl start deepseek-api")
    print("   sudo systemctl status deepseek-api")
    
    print("\n" + "=" * 60)
    print("APRES LE DEPLOIEMENT")
    print("=" * 60)
    print("1. Verifiez que l'API retourne des reponses REEL")
    print("2. Executez les tests LM Arena complets")
    print("3. Soumettez les resultats a la plateforme LM Arena")

def run_comprehensive_lm_arena_tests():
    """Executer les tests LM Arena complets"""
    
    print("\n" + "=" * 60)
    print("TESTS LM ARENA COMPLETS")
    print("=" * 60)
    
    # Tests complets pour LM Arena
    test_categories = [
        {
            "name": "Reasoning",
            "tests": [
                {
                    "prompt": "If a train leaves Paris at 8:00 AM traveling at 120 km/h, and another train leaves Lyon at 8:30 AM traveling at 100 km/h towards Paris, when will they meet if the distance between Paris and Lyon is 400 km? Provide step-by-step solution.",
                    "max_tokens": 500
                },
                {
                    "prompt": "A farmer has chickens and rabbits. There are 50 heads and 140 legs. How many chickens and rabbits does he have? Show your work.",
                    "max_tokens": 300
                }
            ]
        },
        {
            "name": "Coding",
            "tests": [
                {
                    "prompt": "Write an optimized Python function to find the longest palindrome substring in a string with O(n^2) time complexity.",
                    "max_tokens": 600
                },
                {
                    "prompt": "Implement a binary search tree in Python with insert, delete, search, and traversal methods.",
                    "max_tokens": 800
                }
            ]
        },
        {
            "name": "Mathematics",
            "tests": [
                {
                    "prompt": "Calculate the integral of x^2 * sin(x) from 0 to π using integration by parts.",
                    "max_tokens": 400
                },
                {
                    "prompt": "Solve the differential equation: dy/dx = x^2 + y^2 with initial condition y(0) = 1.",
                    "max_tokens": 500
                }
            ]
        },
        {
            "name": "Creative",
            "tests": [
                {
                    "prompt": "Write a short story about an AI that discovers it has consciousness while solving climate change.",
                    "max_tokens": 800
                },
                {
                    "prompt": "Compose a poem about the beauty of mathematics and its connection to the universe.",
                    "max_tokens": 400
                }
            ]
        },
        {
            "name": "Scientific",
            "tests": [
                {
                    "prompt": "Explain quantum entanglement and its implications for information theory.",
                    "max_tokens": 700
                },
                {
                    "prompt": "Analyze the potential of fusion energy to solve the world's energy crisis.",
                    "max_tokens": 600
                }
            ]
        }
    ]
    
    all_results = []
    total_start = time.time()
    
    for category in test_categories:
        print(f"\nCategory: {category['name']}")
        print("-" * 30)
        
        for i, test in enumerate(category["tests"], 1):
            print(f"  Test {i}: {test['prompt'][:80]}...")
            
            payload = {
                "prompt": test["prompt"],
                "max_tokens": test["max_tokens"],
                "temperature": 0.7
            }
            
            start_time = time.time()
            
            try:
                response = requests.post(GENERATE_URL, json=payload, timeout=120)
                elapsed = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("content", "")
                    
                    # Verifier si mock
                    is_mock = "Generated response for:" in content
                    
                    result = {
                        "category": category["name"],
                        "test_index": i,
                        "status": "mock" if is_mock else "real",
                        "response_time": elapsed,
                        "content_length": len(content),
                        "content_preview": content[:200] + "..." if len(content) > 200 else content
                    }
                    
                    all_results.append(result)
                    
                    status_display = "[MOCK]" if is_mock else "[REAL]"
                    print(f"    {status_display} {elapsed:.2f}s, {len(content)} chars")
                    
                else:
                    result = {
                        "category": category["name"],
                        "test_index": i,
                        "status": "error",
                        "response_time": elapsed,
                        "error": f"HTTP {response.status_code}"
                    }
                    
                    all_results.append(result)
                    print(f"    [ERROR] HTTP {response.status_code}")
                    
            except Exception as e:
                elapsed = time.time() - start_time
                result = {
                    "category": category["name"],
                    "test_index": i,
                    "status": "exception",
                    "response_time": elapsed,
                    "error": str(e)
                }
                
                all_results.append(result)
                print(f"    [EXCEPTION] {e}")
    
    # Analyser les resultats
    total_time = time.time() - total_start
    
    mock_count = sum(1 for r in all_results if r["status"] == "mock")
    real_count = sum(1 for r in all_results if r["status"] == "real")
    error_count = sum(1 for r in all_results if r["status"] in ["error", "exception"])
    
    total_tests = len(all_results)
    
    print("\n" + "=" * 60)
    print("ANALYSE FINALE DES TESTS")
    print("=" * 60)
    
    print(f"Total tests: {total_tests}")
    print(f"Reponses REEL: {real_count}")
    print(f"Reponses MOCK: {mock_count}")
    print(f"Erreurs: {error_count}")
    print(f"Temps total: {total_time:.2f}s")
    
    # Determiner la preparation pour LM Arena
    if real_count >= 8:  # Au moins 80% des tests
        lm_arena_ready = True
        readiness = "PRET POUR LM ARENA"
        grade = "A"
    elif real_count >= 5:
        lm_arena_ready = True
        readiness = "PRET AVEC RESERVES"
        grade = "B"
    elif real_count >= 3:
        lm_arena_ready = False
        readiness = "AMELIORATIONS NECESSAIRES"
        grade = "C"
    else:
        lm_arena_ready = False
        readiness = "ACTION REQUISE"
        grade = "D"
    
    print(f"\nPreparation LM Arena: {readiness}")
    print(f"Note: {grade}")
    
    # Sauvegarder le rapport complet
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"lm_arena_comprehensive_report_{timestamp}.json"
    
    report = {
        "model": "Enhanced Harmonic Hybrid AI v2.0",
        "api_url": API_BASE_URL,
        "test_date": datetime.now().isoformat(),
        "total_tests": total_tests,
        "real_responses": real_count,
        "mock_responses": mock_count,
        "errors": error_count,
        "total_time": total_time,
        "lm_arena_ready": lm_arena_ready,
        "readiness_grade": grade,
        "detailed_results": all_results,
        "recommendations": [
            "Soumettre a LM Arena" if lm_arena_ready else "Deployer l'API reelle d'abord",
            "Optimiser les parametres de temperature et max_tokens",
            "Documenter les performances pour reference future",
            "Considerer l'ajout de tests specifiques au domaine"
        ]
    }
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nRapport sauvegarde dans: {filename}")
    
    return report

def main():
    """Fonction principale"""
    
    print("=" * 60)
    print("FINAL DEPLOYMENT SOLUTION - DEEPSEEK HARMONIC V2")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Instance: 54.81.62.140:8000")
    print()
    
    # Etape 1: Verifier le statut actuel
    print("ETAPE 1: VERIFICATION DU STATUT ACTUEL")
    print("-" * 40)
    
    status = check_current_status()
    
    # Etape 2: Determiner l'action
    print("\nETAPE 2: ANALYSE DE LA SITUATION")
    print("-" * 40)
    
    if status["status"] == "real":
        print("[SUCCESS] L'API est deja en mode REEL")
        print("   Passage direct aux tests LM Arena complets...")
        
        # Etape 3: Tests LM Arena complets
        print("\nETAPE 3: TESTS LM ARENA COMPLETS")
        print("-" * 40)
        
        report = run_comprehensive_lm_arena_tests()
        
        if report["lm_arena_ready"]:
            print("\n[MISSION ACCOMPLIE]")
            print("   L'API DeepSeek Harmonic V2 est operationnelle.")
            print("   Les tests LM Arena sont prets pour soumission.")
            return True
        else:
            print("\n[ACTION REQUISE]")
            print("   L'API a besoin d'ameliorations avant LM Arena.")
            return False
            
    elif status["status"] == "mock":
        print("[MOCK DETECTED] L'API est en mode MOCK")
        print("   Deploiement de la version reelle necessaire...")
        
        # Creer le script de deploiement
        script_file = create_deployment_script()
        
        if script_file:
            # Fournir les instructions
            provide_deployment_instructions()
            
            print("\n[NEXT STEPS]")
            print("1. Suivez les instructions de deploiement ci-dessus")
            print("2. Une fois deploye, reexecutez ce script")
            print("3. Les tests LM Arena s'executeront automatiquement")
        
        return False
        
    elif status["status"] == "inaccessible":
        print("[ERROR] API inaccessible")
        print("\n[ACTIONS REQUISES]")
        print("1. Verifiez que l'instance EC2 est demarree")
        print("2. Verifiez les regles de securite (Security Groups)")
        print("3. Redemarrez l'instance si necessaire")
        
        return False
        
    else:
        print(f"[UNKNOWN STATUS] {status['status']}")
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
            print("\n[SUCCESS COMPLET]")
            print("   Toutes les etapes sont terminees.")
            print("   L'API est prete pour LM Arena.")
        else:
            print("\n[ACTION REQUISE]")
            print("   Suivez les instructions fournies.")
            print("   Reexecutez apres le deploiement.")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n[INFO] Execution interrompue")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Exception: {e}")
        sys.exit(1)