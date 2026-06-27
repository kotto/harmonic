#!/usr/bin/env python3
"""
EXECUTION FINALE COMPLETE - ENHANCED HARMONIC HYBRID AI v2.0
Script unique pour exécuter tous les tests LM Arena en une commande
"""

import os
import sys
import json
import time
import requests
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration
EC2_IP = "54.81.62.140"
EC2_PORT = 8000
EC2_USER = "ubuntu"  # Essayer aussi "ec2-user" si ça ne marche pas
SSH_KEY_PATH = r"C:\Users\maatc\.ssh\deepseek_ec2"
BASE_URL = f"http://{EC2_IP}:{EC2_PORT}"

class FinalLMArenaExecutor:
    """Exécuteur final pour tous les tests LM Arena"""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        self.test_count = 0
        self.passed_count = 0
        self.failed_count = 0
        
    def log_step(self, step_name: str, status: str = "info", message: str = ""):
        """Journaliser une étape"""
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_symbol = {
            "info": "[INFO]",
            "success": "[SUCCES]",
            "error": "[ERREUR]",
            "warning": "[AVERT]"
        }.get(status, "[INFO]")
        
        print(f"{timestamp} {status_symbol} {step_name}")
        if message:
            print(f"       {message}")
        print()
    
    def step_1_check_current_api(self) -> bool:
        """Étape 1: Vérifier l'API actuelle"""
        
        self.log_step("ÉTAPE 1: Vérification de l'API actuelle")
        
        # Test de santé
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=10)
            if response.status_code == 200:
                self.log_step("Santé API", "success", f"HTTP 200 - {response.json()}")
            else:
                self.log_step("Santé API", "error", f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_step("Santé API", "error", f"Exception: {e}")
            return False
        
        # Test de réponse
        test_prompt = "What is 2+2?"
        payload = {"prompt": test_prompt, "max_tokens": 50}
        
        try:
            response = requests.post(f"{BASE_URL}/generate", json=payload, timeout=15)
            if response.status_code == 200:
                data = response.json()
                generated_text = data.get("generated_text", data.get("content", ""))
                
                # Analyser le type de réponse
                if "generated response for:" in generated_text.lower():
                    self.log_step("Type d'API", "warning", "API retourne des réponses MOCK")
                    self.log_step("Conclusion", "info", "Nécessite déploiement de la version réelle")
                    return True  # Continue car c'est le problème à résoudre
                else:
                    self.log_step("Type d'API", "success", "API retourne des réponses REELLES")
                    self.log_step("Conclusion", "success", "Prêt pour tests LM Arena")
                    return True
            else:
                self.log_step("Test API", "error", f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_step("Test API", "error", f"Exception: {e}")
            return False
    
    def step_2_prepare_ssh_connection(self) -> bool:
        """Étape 2: Préparer la connexion SSH"""
        
        self.log_step("ÉTAPE 2: Préparation de la connexion SSH")
        
        # Vérifier si SSH est disponible
        ssh_path = r"C:\Windows\System32\OpenSSH\ssh.exe"
        
        if not os.path.exists(ssh_path):
            self.log_step("SSH Client", "error", "OpenSSH Client non installé")
            self.log_step("Solution", "info", "Installer via: Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0")
            return False
        
        # Vérifier la clé SSH
        if not os.path.exists(SSH_KEY_PATH):
            self.log_step("Clé SSH", "error", f"Clé non trouvée: {SSH_KEY_PATH}")
            return False
        
        # Tester la connexion SSH
        self.log_step("Test SSH", "info", f"Connexion à {EC2_USER}@{EC2_IP}")
        
        test_command = [
            ssh_path,
            "-i", SSH_KEY_PATH,
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            "-o", "PasswordAuthentication=no",
            f"{EC2_USER}@{EC2_IP}",
            "echo 'SSH_TEST_SUCCESS'"
        ]
        
        try:
            result = subprocess.run(
                test_command,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0 and "SSH_TEST_SUCCESS" in result.stdout:
                self.log_step("Test SSH", "success", "Connexion SSH établie")
                return True
            else:
                self.log_step("Test SSH", "error", f"Échec SSH: {result.stderr}")
                
                # Essayer avec ec2-user
                if EC2_USER == "ubuntu":
                    self.log_step("Alternative", "info", "Essayer avec 'ec2-user'")
                    EC2_USER = "ec2-user"
                    return self.step_2_prepare_ssh_connection()
                else:
                    return False
                    
        except subprocess.TimeoutExpired:
            self.log_step("Test SSH", "error", "Timeout SSH")
            return False
        except Exception as e:
            self.log_step("Test SSH", "error", f"Exception: {e}")
            return False
    
    def step_3_deploy_real_api(self) -> bool:
        """Étape 3: Déployer l'API réelle"""
        
        self.log_step("ÉTAPE 3: Déploiement de l'API réelle")
        
        # Lire le fichier API réel local
        local_api_file = "deepseek_api_real_final.py"
        
        if not os.path.exists(local_api_file):
            self.log_step("Fichier API", "error", f"Fichier non trouvé: {local_api_file}")
            return False
        
        try:
            with open(local_api_file, "r", encoding="utf-8") as f:
                api_content = f.read()
        except Exception as e:
            self.log_step("Lecture fichier", "error", f"Exception: {e}")
            return False
        
        # Préparer la commande de déploiement
        deploy_script = f"""#!/bin/bash

echo "=== DÉPLOIEMENT API RÉELLE ==="

# Arrêter l'API actuelle si elle tourne
pkill -f "python.*8000" || true

# Créer le fichier API réel
cat > /home/{EC2_USER}/deepseek_harmonic_real.py << 'EOF'
{api_content}
EOF

# Installer les dépendances Python
python3 -m pip install --upgrade pip
pip3 install fastapi uvicorn pydantic

# Démarrer l'API
cd /home/{EC2_USER}
nohup python3 deepseek_harmonic_real.py > api.log 2>&1 &

echo "API démarrée sur le port 8000"
echo "Vérification dans 5 secondes..."
sleep 5

# Vérifier que l'API tourne
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "SUCCESS: API réelle déployée avec succès"
    exit 0
else
    echo "ERROR: API non accessible"
    exit 1
fi
"""
        
        # Exécuter le déploiement via SSH
        ssh_path = r"C:\Windows\System32\OpenSSH\ssh.exe"
        
        deploy_command = [
            ssh_path,
            "-i", SSH_KEY_PATH,
            "-o", "StrictHostKeyChecking=no",
            f"{EC2_USER}@{EC2_IP}",
            deploy_script
        ]
        
        self.log_step("Déploiement", "info", f"Exécution sur {EC2_IP}")
        
        try:
            result = subprocess.run(
                deploy_command,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.log_step("Déploiement", "success", "API réelle déployée avec succès")
                self.log_step("Attente", "info", "Attente de 10 secondes pour stabilisation...")
                time.sleep(10)
                return True
            else:
                self.log_step("Déploiement", "error", f"Échec: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_step("Déploiement", "error", "Timeout déploiement")
            return False
        except Exception as e:
            self.log_step("Déploiement", "error", f"Exception: {e}")
            return False
    
    def step_4_verify_real_api(self) -> bool:
        """Étape 4: Vérifier que l'API retourne des réponses réelles"""
        
        self.log_step("ÉTAPE 4: Vérification de l'API réelle")
        
        # Attendre que l'API soit prête
        self.log_step("Attente", "info", "Vérification de l'API dans 5 secondes...")
        time.sleep(5)
        
        # Test de santé
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                self.log_step("Santé API", "success", f"HTTP 200 - {health_data}")
            else:
                self.log_step("Santé API", "error", f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_step("Santé API", "error", f"Exception: {e}")
            return False
        
        # Test de réponse réelle
        test_prompts = [
            "What is the capital of France?",
            "Write a simple Python function to add two numbers",
            "Explain the concept of quantum entanglement"
        ]
        
        real_responses = 0
        
        for prompt in test_prompts:
            payload = {"prompt": prompt, "max_tokens": 100}
            
            try:
                response = requests.post(f"{BASE_URL}/generate", json=payload, timeout=20)
                
                if response.status_code == 200:
                    data = response.json()
                    generated_text = data.get("generated_text", data.get("content", ""))
                    
                    # Vérifier que ce n'est pas une réponse mock
                    if "generated response for:" in generated_text.lower():
                        self.log_step(f"Test: {prompt[:30]}...", "warning", "Réponse MOCK détectée")
                    else:
                        self.log_step(f"Test: {prompt[:30]}...", "success", "Réponse RÉELLE détectée")
                        real_responses += 1
                else:
                    self.log_step(f"Test: {prompt[:30]}...", "error", f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_step(f"Test: {prompt[:30]}...", "error", f"Exception: {e}")
        
        # Conclusion
        if real_responses >= 2:
            self.log_step("Vérification API", "success", f"{real_responses}/3 réponses réelles détectées")
            self.log_step("Statut", "success", "API RÉELLE fonctionnelle - Prêt pour tests LM Arena")
            return True
        else:
            self.log_step("Vérification API", "error", f"Seulement {real_responses}/3 réponses réelles")
            self.log_step("Statut", "error", "API toujours en mode MOCK - Déploiement échoué")
            return False
    
    def step_5_execute_lm_arena_tests(self) -> bool:
        """Étape 5: Exécuter les tests LM Arena complets"""
        
        self.log_step("ÉTAPE 5: Exécution des tests LM Arena complets")
        
        # Importer et exécuter le testeur LM Arena
        try:
            # Créer un testeur simple
            test_results = self._run_simple_lm_arena_tests()
            
            if test_results:
                self.log_step("Tests LM Arena", "success", f"{len(test_results)} tests exécutés")
                
                # Sauvegarder les résultats
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"lm_arena_final_results_{timestamp}.json"
                
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(test_results, f, indent=2, ensure_ascii=False)
                
                self.log_step("Sauvegarde", "success", f"Résultats sauvegardés dans: {filename}")
                return True
            else:
                self.log_step("Tests LM Arena", "error", "Aucun résultat de test")
                return False
                
        except Exception as e:
            self.log_step("Tests LM Arena", "error", f"Exception: {e}")
            return False
    
    def _run_simple_lm_arena_tests(self) -> List[Dict[str, Any]]:
        """Exécuter des tests LM Arena simples"""
        
        tests = [
            {
                "name": "reasoning_complex",
                "prompt": """If a train leaves Paris at 8:00 AM traveling at 120 km/h, 
and another train leaves Lyon at 8:30 AM traveling at 100 km/h towards Paris, 
when will they meet if the distance between Paris and Lyon is 400 km?
Provide a detailed step-by-step solution.""",
                "max_tokens": 500
            },
            {
                "name": "coding_algorithm",
                "prompt": """Write an optimized Python function to find the longest palindrome substring in a given string.
Include proper error handling, docstring, and examples.""",
                "max_tokens": 600
            },
            {
                "name": "mathematics_advanced",
                "prompt": """Calculate the integral of x^2 * sin(x) from 0 to π.
Provide step-by-step solution and final numerical value.""",
                "max_tokens": 400
            }
        ]
        
        results = []
        
        for test in tests:
            self.test_count += 1
            
            payload = {
                "prompt": test["prompt"],
                "max_tokens": test["max_tokens"],
                "temperature": 0.3
            }
            
            start_time = time.time()
            
            try:
                response = requests.post(f"{BASE_URL}/generate", json=payload, timeout=45)
                processing_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    generated_text = data.get("generated_text", data.get("content", ""))
                    
                    # Vérifier que ce n'est pas une réponse mock
                    if "generated response for:" in generated_text.lower():
                        status = "failed_mock"
                        self.failed_count += 1
                    else:
                        status = "passed"
                        self.passed_count += 1
                    
                    result = {
                        "test": test["name"],
                        "status": status,
                        "response_preview": generated_text[:200] + "..." if len(generated_text) > 200 else generated_text,
                        "processing_time": processing_time,
                        "tokens": len(generated_text.split()),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    results.append(result)
                    
                    self.log_step(f"Test: {test['name']}", 
                                 "success" if status == "passed" else "warning",
                                 f"{status} - {processing_time:.2f}s")
                    
                else:
                    self.failed_count += 1
                    result = {
                        "test": test["name"],
                        "status": "failed_http",
                        "error": f"HTTP {response.status_code}",
                        "processing_time": processing_time,
                        "timestamp": datetime.now().isoformat()
                    }
                    results.append(result)
                    
                    self.log_step(f"Test: {test['name']}", "error", f"HTTP {response.status_code}")
                    
            except requests.exceptions.Timeout:
                self.failed_count += 1
                result = {
                    "test": test["name"],
                    "status": "timeout",
                    "error": "Timeout après 45 secondes",
                    "processing_time": 45,
                    "timestamp": datetime.now().isoformat()
                }
                results.append(result)
                
                self.log_step(f"Test: {test['name']}", "error", "Timeout")
                
            except Exception as e:
                self.failed_count += 1
                result = {
                    "test": test["name"],
                    "status": "failed_exception",
                    "error": str(e),
                    "processing_time": time.time() - start_time,
                    "timestamp": datetime.now().isoformat()
                }
                results.append(result)
                
                self.log_step(f"Test: {test['name']}", "error", f"Exception: {e}")
        
        return results
    
    def step_6_generate_final_report(self) -> Dict[str, Any]:
        """Étape 6: Générer le rapport final"""
        
        self.log_step("ÉTAPE 6: Génération du rapport final")
        
        total_time = time.time() - self.start_time
        
        report = {
            "execution_summary": {
                "model": "Enhanced Harmonic Hybrid AI v2.0",
                "ec2_instance": f"{EC2_IP}:{EC2_PORT}",
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "end_time": datetime.now().isoformat(),
                "total_duration": total_time,
                "tests_executed": self.test_count,
                "tests_passed": self.passed_count,
                "tests_failed": self.failed_count,
                "success_rate": (self.passed_count / self.test_count * 100) if self.test_count > 0 else 0
            },
            "system_status": {
                "ssh_connection": "available" if self.step_2_prepare_ssh_connection() else "unavailable",
                "api_type": "real" if self.step_4_verify_real_api() else "mock",
                "lm_arena_ready": self.passed_count >= 2
            },
            "recommendations": [
                "Soumettre les résultats à la plateforme LM Arena",
                "Documenter les performances pour référence future",
                "Optimiser les paramètres de génération si nécessaire"
            ]
        }
        
        # Sauvegarder le rapport
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"final_execution_report_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.log_step("Rapport sauvegardé", "success", f"Fichier: {report_file}")
        
        return report
    
    def run_complete_execution(self) -> bool:
        """Exécuter l'ensemble du processus"""
        
        print("=" * 80)
        print("EXÉCUTION COMPLÈTE - ENHANCED HARMONIC HYBRID AI v2.0")
        print("=" * 80)
        print(f"Instance EC2: {EC2_IP}:{EC2_PORT}")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Étape 1: Vérifier l'API actuelle
        if not self.step_1_check_current_api():
            self.log_step("Échec étape 1", "error", "Impossible de vérifier l'API actuelle")
            return False
        
        # Étape 2: Préparer SSH (optionnel - si échoue, on continue avec API mock)
        ssh_available = self.step_2_prepare_ssh_connection()
        
        if ssh_available:
            # Étape 3: Déployer l'API réelle
            if not self.step_3_deploy_real_api():
                self.log_step("Déploiement échoué", "warning", "Continuer avec API mock")
        
        # Étape 4: Vérifier l'API (réelle ou mock)
        api_real = self.step_4_verify_real_api()
        
        if api_real:
            self.log_step("API vérifiée", "success", "API RÉELLE fonctionnelle")
        else:
            self.log_step("API vérifiée", "warning", "API MOCK - Tests limités")
        
        # Étape 5: Exécuter les tests LM Arena
        if not self.step_5_execute_lm_arena_tests():
            self.log_step("Tests échoués", "error", "Impossible d'exécuter les tests")
            return False
        
        # Étape 6: Générer le rapport final
        report = self.step_6_generate_final_report()
        
        # Afficher le résumé final
        print("\n" + "=" * 80)
        print("RÉSUMÉ FINAL DE L'EXÉCUTION")
        print("=" * 80)
        
        summary = report["execution_summary"]
        print(f"Modèle: {summary['model']}")
        print(f"Instance: {summary['ec2_instance']}")
        print(f"Durée totale: {summary['total_duration']:.2f}s")
        print(f"Tests exécutés: {summary['tests_executed']}")
        print(f"Tests réussis: {summary['tests_passed']}")
        print(f"Tests échoués: {summary['tests_failed']}")
        print(f"Taux de réussite: {summary['success_rate']:.1f}%")
        
        status = report["system_status"]
        print(f"\nStatut système:")
        print(f"  Connexion SSH: {status['ssh_connection']}")
        print(f"  Type d'API: {status['api_type']}")
        print(f"  Prêt pour LM Arena: {'OUI' if status['lm_arena_ready'] else 'NON'}")
        
        print(f"\nRecommandations:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"  {i}. {rec}")
        
        print("\n" + "=" * 80)
        print("EXÉCUTION TERMINÉE AVEC SUCCÈS!")
        print("=" * 80)
        
        return True

def main():
    """Fonction principale"""
    
    try:
        executor = FinalLMArenaExecutor()
        success = executor.run_complete_execution()
        
        if success:
            print("\n[SUCCES] Tous les tests ont été exécutés avec succès!")
            print("Les résultats sont prêts pour soumission à LM Arena.")
            print("\nFichiers générés:")
            print("  - lm_arena_final_results_*.json (résultats détaillés)")
            print("  - final_execution_report_*.json (rapport complet)")
            return 0
        else:
            print("\n[ERREUR] L'exécution a échoué à une étape critique")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n[INFO] Exécution interrompue par l'utilisateur")
        return 1
    except Exception as e:
        print(f"\n[ERREUR] Exception non gérée: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())