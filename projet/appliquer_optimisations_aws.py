#!/usr/bin/env python3
"""
Script pour appliquer les optimisations de latence sur l'instance AWS
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime

class AWSOptimizationApplier:
    """Appliqueur d'optimisations AWS pour Harmonic AI"""
    
    def __init__(self, aws_instance_ip="__EC2_IP__", ssh_user="ec2-user", ssh_key="C:\\Users\\maatc\\.ssh\\deepseek_ec2"):
        self.aws_instance_ip = aws_instance_ip
        self.ssh_user = ssh_user
        self.ssh_key = ssh_key
        self.optimization_log = []
        
    def log_step(self, step_name, description, status="info"):
        """Journaliser une Ã©tape d'optimisation"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "step": step_name,
            "description": description,
            "status": status
        }
        self.optimization_log.append(log_entry)
        print(f"[{timestamp}] {step_name}: {description}")
        
    def test_ssh_connection(self):
        """Tester la connexion SSH Ã  l'instance AWS"""
        self.log_step("TEST_SSH", "Test de connexion SSH...")
        
        try:
            # Tester la connexion avec une commande simple
            cmd = [
                "ssh", "-i", self.ssh_key,
                f"{self.ssh_user}@{self.aws_instance_ip}",
                "echo 'Connexion SSH rÃ©ussie'"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.log_step("TEST_SSH", "Connexion SSH OK", "success")
                return True
            else:
                self.log_step("TEST_SSH", f"Ã‰chec SSH: {result.stderr}", "error")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_step("TEST_SSH", "Timeout connexion SSH", "error")
            return False
        except Exception as e:
            self.log_step("TEST_SSH", f"Erreur SSH: {str(e)}", "error")
            return False
    
    def apply_optimized_parameters(self):
        """Appliquer les paramÃ¨tres optimisÃ©s sur l'instance AWS"""
        self.log_step("APPLY_PARAMS", "Application paramÃ¨tres optimisÃ©s...")
        
        # Lire les paramÃ¨tres optimisÃ©s
        try:
            with open("optimized_inference_params.json", "r") as f:
                params = json.load(f)
        except FileNotFoundError:
            self.log_step("APPLY_PARAMS", "Fichier optimized_inference_params.json non trouvÃ©", "error")
            return False
        
        # CrÃ©er un script Python pour mettre Ã  jour les paramÃ¨tres
        update_script = """
import json
import sys

# Charger les paramÃ¨tres optimisÃ©s
with open('optimized_inference_params.json', 'r') as f:
    new_params = json.load(f)

# Chemin du fichier API
api_file = '/opt/deepseek/api.py'

try:
    # Lire le fichier API
    with open(api_file, 'r') as f:
        content = f.read()
    
    # Mettre Ã  jour les paramÃ¨tres par dÃ©faut
    # Rechercher la section des paramÃ¨tres
    lines = content.split('\\n')
    updated_lines = []
    
    for line in lines:
        if 'max_tokens' in line and '=' in line and '#' not in line.split('=')[0]:
            updated_lines.append(f"    max_tokens = {new_params['optimized_parameters']['max_tokens']}")
        elif 'temperature' in line and '=' in line and '#' not in line.split('=')[0]:
            updated_lines.append(f"    temperature = {new_params['optimized_parameters']['temperature']}")
        elif 'top_p' in line and '=' in line and '#' not in line.split('=')[0]:
            updated_lines.append(f"    top_p = {new_params['optimized_parameters']['top_p']}")
        elif 'top_k' in line and '=' in line and '#' not in line.split('=')[0]:
            updated_lines.append(f"    top_k = {new_params['optimized_parameters']['top_k']}")
        elif 'repetition_penalty' in line and '=' in line and '#' not in line.split('=')[0]:
            updated_lines.append(f"    repetition_penalty = {new_params['optimized_parameters']['repetition_penalty']}")
        elif 'do_sample' in line and '=' in line and '#' not in line.split('=')[0]:
            updated_lines.append(f"    do_sample = {new_params['optimized_parameters']['do_sample']}")
        elif 'early_stopping' in line and '=' in line and '#' not in line.split('=')[0]:
            updated_lines.append(f"    early_stopping = {new_params['optimized_parameters']['early_stopping']}")
        elif 'num_beams' in line and '=' in line and '#' not in line.split('=')[0]:
            updated_lines.append(f"    num_beams = {new_params['optimized_parameters']['num_beams']}")
        else:
            updated_lines.append(line)
    
    # Ã‰crire le fichier mis Ã  jour
    with open(api_file, 'w') as f:
        f.write('\\n'.join(updated_lines))
    
    print("ParamÃ¨tres mis Ã  jour avec succÃ¨s!")
    
except Exception as e:
    print(f"Erreur lors de la mise Ã  jour: {str(e)}")
    sys.exit(1)
"""
        
        # Sauvegarder le script localement
        with open("update_api_params.py", "w") as f:
            f.write(update_script)
        
        # Copier les fichiers sur l'instance AWS
        try:
            # Copier le fichier de paramÃ¨tres
            scp_cmd = [
                "scp", "-i", self.ssh_key,
                "optimized_inference_params.json",
                f"{self.ssh_user}@{self.aws_instance_ip}:/tmp/"
            ]
            
            result = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.log_step("APPLY_PARAMS", f"Ã‰chec copie paramÃ¨tres: {result.stderr}", "error")
                return False
            
            # Copier le script de mise Ã  jour
            scp_cmd = [
                "scp", "-i", self.ssh_key,
                "update_api_params.py",
                f"{self.ssh_user}@{self.aws_instance_ip}:/tmp/"
            ]
            
            result = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.log_step("APPLY_PARAMS", f"Ã‰chec copie script: {result.stderr}", "error")
                return False
            
            # ExÃ©cuter le script sur l'instance AWS
            ssh_cmd = [
                "ssh", "-i", self.ssh_key,
                f"{self.ssh_user}@{self.aws_instance_ip}",
                "cd /tmp && python3 update_api_params.py"
            ]
            
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.log_step("APPLY_PARAMS", "ParamÃ¨tres appliquÃ©s avec succÃ¨s", "success")
                
                # RedÃ©marrer le service
                self.restart_api_service()
                
                return True
            else:
                self.log_step("APPLY_PARAMS", f"Ã‰chec exÃ©cution script: {result.stderr}", "error")
                return False
                
        except Exception as e:
            self.log_step("APPLY_PARAMS", f"Erreur application paramÃ¨tres: {str(e)}", "error")
            return False
    
    def restart_api_service(self):
        """RedÃ©marrer le service API"""
        self.log_step("RESTART_SERVICE", "RedÃ©marrage service API...")
        
        try:
            ssh_cmd = [
                "ssh", "-i", self.ssh_key,
                f"{self.ssh_user}@{self.aws_instance_ip}",
                "sudo systemctl restart deepseek-api.service"
            ]
            
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.log_step("RESTART_SERVICE", "Service redÃ©marrÃ© avec succÃ¨s", "success")
                
                # Attendre que le service soit opÃ©rationnel
                time.sleep(5)
                
                # VÃ©rifier le statut
                ssh_cmd = [
                    "ssh", "-i", self.ssh_key,
                    f"{self.ssh_user}@{self.aws_instance_ip}",
                    "sudo systemctl status deepseek-api.service --no-pager"
                ]
                
                result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
                
                if "active (running)" in result.stdout:
                    self.log_step("RESTART_SERVICE", "Service opÃ©rationnel", "success")
                else:
                    self.log_step("RESTART_SERVICE", "Service non actif", "warning")
                    
                return True
            else:
                self.log_step("RESTART_SERVICE", f"Ã‰chec redÃ©marrage: {result.stderr}", "error")
                return False
                
        except Exception as e:
            self.log_step("RESTART_SERVICE", f"Erreur redÃ©marrage: {str(e)}", "error")
            return False
    
    def test_optimization_impact(self):
        """Tester l'impact des optimisations"""
        self.log_step("TEST_IMPACT", "Test impact optimisations...")
        
        # Tester la latence aprÃ¨s optimisation
        test_script = """
import requests
import time
import statistics

def test_latency():
    url = "http://localhost:8000/generate"
    
    test_prompts = [
        {"prompt": "Explique briÃ¨vement la thÃ©orie de la relativitÃ©."},
        {"prompt": "Ã‰cris une fonction Python pour calculer la factorielle."},
        {"prompt": "Quelle est la capitale de la France?"},
        {"prompt": "Calcule 15 * 27."},
        {"prompt": "RÃ©sume l'histoire de l'informatique en 3 phrases."}
    ]
    
    latencies = []
    
    for i, test in enumerate(test_prompts, 1):
        try:
            start_time = time.time()
            response = requests.post(url, json=test, timeout=10)
            end_time = time.time()
            
            latency = end_time - start_time
            latencies.append(latency)
            
            print(f"Prompt {i}: {latency:.2f}s")
            
        except Exception as e:
            print(f"Erreur prompt {i}: {str(e)}")
    
    if latencies:
        avg_latency = statistics.mean(latencies)
        print(f"\\nLatence moyenne: {avg_latency:.2f}s")
        return avg_latency
    else:
        print("Aucune latence mesurÃ©e")
        return None

if __name__ == "__main__":
    test_latency()
"""
        
        try:
            # Sauvegarder le script de test
            with open("test_latency_after.py", "w") as f:
                f.write(test_script)
            
            # Copier sur l'instance AWS
            scp_cmd = [
                "scp", "-i", self.ssh_key,
                "test_latency_after.py",
                f"{self.ssh_user}@{self.aws_instance_ip}:/tmp/"
            ]
            
            result = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.log_step("TEST_IMPACT", f"Ã‰chec copie script test: {result.stderr}", "error")
                return None
            
            # ExÃ©cuter le test
            ssh_cmd = [
                "ssh", "-i", self.ssh_key,
                f"{self.ssh_user}@{self.aws_instance_ip}",
                "cd /tmp && python3 test_latency_after.py"
            ]
            
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Extraire la latence moyenne du rÃ©sultat
                output = result.stdout
                for line in output.split('\\n'):
                    if "Latence moyenne:" in line:
                        latency_str = line.split(":")[1].strip().replace("s", "")
                        latency = float(latency_str)
                        self.log_step("TEST_IMPACT", f"Latence aprÃ¨s optimisation: {latency:.2f}s", "success")
                        return latency
            
            self.log_step("TEST_IMPACT", "Impossible de mesurer la latence", "warning")
            return None
            
        except Exception as e:
            self.log_step("TEST_IMPACT", f"Erreur test impact: {str(e)}", "error")
            return None
    
    def run_full_optimization(self):
        """ExÃ©cuter l'optimisation complÃ¨te"""
        print("=" * 70)
        print("APPLICATION OPTIMISATIONS LATENCE - HARMONIC AI")
        print("=" * 70)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Instance AWS: {self.aws_instance_ip}")
        print("=" * 70)
        
        # 1. Tester la connexion SSH
        if not self.test_ssh_connection():
            print("ERREUR: Impossible de se connecter Ã  l'instance AWS")
            return False
        
        # 2. Appliquer les paramÃ¨tres optimisÃ©s
        if not self.apply_optimized_parameters():
            print("ERREUR: Ã‰chec application paramÃ¨tres optimisÃ©s")
            return False
        
        # 3. Tester l'impact
        print("\\n" + "=" * 70)
        print("TEST IMPACT OPTIMISATIONS")
        print("=" * 70)
        
        latency_before = 1.76  # Valeur mesurÃ©e prÃ©cÃ©demment
        latency_after = self.test_optimization_impact()
        
        if latency_after:
            improvement = ((latency_before - latency_after) / latency_before) * 100
            print(f"\\nLatence avant: {latency_before:.2f}s")
            print(f"Latence aprÃ¨s: {latency_after:.2f}s")
            print(f"AmÃ©lioration: {improvement:.1f}%")
            
            if improvement > 0:
                print("SUCCÃˆS: Optimisation effective!")
            else:
                print("ATTENTION: Pas d'amÃ©lioration mesurÃ©e")
        
        # 4. Sauvegarder le rapport
        self.save_optimization_report(latency_before, latency_after)
        
        return True
    
    def save_optimization_report(self, latency_before, latency_after):
        """Sauvegarder le rapport d'optimisation"""
        report = {
            "metadata": {
                "report_id": f"OPT_APPLY_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "generation_date": datetime.now().isoformat(),
                "aws_instance": self.aws_instance_ip,
                "ssh_user": self.ssh_user
            },
            "optimization_steps": self.optimization_log,
            "performance_results": {
                "latency_before": latency_before,
                "latency_after": latency_after,
                "improvement_percent": ((latency_before - latency_after) / latency_before * 100) if latency_after else None
            },
            "files_generated": [
                "update_api_params.py",
                "test_latency_after.py"
            ]
        }
        
        with open("optimization_application_report.json", "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.log_step("SAVE_REPORT", "Rapport sauvegardÃ©: optimization_application_report.json", "success")

def main():
    """Fonction principale"""
    print("Application optimisations latence AWS - Harmonic AI")
    print()
    
    applier = AWSOptimizationApplier()
    
    print("SÃ©lectionnez une option:")
    print("1. Appliquer optimisations complÃ¨tes")
    print("2. Tester connexion SSH seulement")
    print("3. Tester latence aprÃ¨s optimisation")
    print()
    
    choice = input("Votre choix (1-3): ").strip()
    
    if choice == "1":
        success = applier.run_full_optimization()
        if success:
            print("\\n" + "=" * 70)
            print("OPTIMISATIONS APPLIQUÃ‰ES AVEC SUCCÃˆS!")
            print("=" * 70)
        else:
            print("\\n" + "=" * 70)
            print("Ã‰CHEC APPLICATION OPTIMISATIONS")
            print("=" * 70)
            
    elif choice == "2":
        applier.test_ssh_connection()
        
    elif choice == "3":
        latency = applier.test_optimization_impact()
        if latency:
            print(f"\\nLatence mesurÃ©e: {latency:.2f}s")
            
    else:
        print("Choix invalide")

if __name__ == "__main__":
    main()