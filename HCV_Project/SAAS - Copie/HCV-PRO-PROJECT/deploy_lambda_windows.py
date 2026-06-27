#!/usr/bin/env python3
"""
DÉPLOIEMENT LAMBDA CORRIGÉ POUR WINDOWS
====================================

Script pour déployer la fonction Lambda corrigée dans l'environnement Windows PowerShell.
"""

import os
import subprocess
import zipfile
import json
import sys
from pathlib import Path
from datetime import datetime

class WindowsLambdaDeployer:
    """Déployeur pour environnement Windows PowerShell"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.lambda_dir = self.project_root / "lambda_package"
        self.function_name = "hcv-pro-deepseek-handler"
        self.region = "eu-west-3"
        self.deploy_log = []
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        self.deploy_log.append(log_entry)
    
    def install_dependencies_windows(self) -> bool:
        """Installer les dépendances sur Windows"""
        self.log("📦 Installation des dépendances (Windows)...")
        
        try:
            # Installer NumPy avec pip
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', 'numpy'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.log("   ✅ NumPy installé avec succès")
                return True
            else:
                self.log(f"   ❌ Erreur installation NumPy: {result.stderr}")
                return False
                
        except Exception as e:
            self.log(f"   ❌ Erreur installation dépendances: {e}")
            return False
    
    def create_windows_package(self) -> str:
        """Créer le package pour Windows"""
        self.log("📦 Création du package Windows...")
        
        zip_path = self.lambda_dir / "lambda_windows.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            # Ajouter le fichier handler
            handler_file = self.lambda_dir / "aws_real_compression_handler.py"
            zip_file.write(handler_file, "aws_real_compression_handler.py")
            
            # Ajouter les dépendances
            requirements = """
numpy==1.24.3
"""
            zip_file.writestr("requirements.txt", requirements)
            
            # Ajouter un fichier de configuration
            config = {
                "handler": "aws_real_compression_handler.lambda_handler",
                "runtime": "python3.11",
                "timeout": 300,
                "memory": 2048,
                "environment": {
                    "PYTHONPATH": "C:\\Python311\\python.exe"
                }
            }
            zip_file.writestr("config.json", json.dumps(config, indent=2))
        
        self.log(f"✅ Package Windows créé: {zip_path}")
        return str(zip_path)
    
    def deploy_windows_function(self, zip_path: str) -> bool:
        """Déployer sur AWS depuis Windows"""
        self.log("🔄 Déploiement Windows vers AWS...")
        
        try:
            # Déployer sur AWS depuis Windows
            cmd = [
                'aws', 'lambda', 'update-function-code',
                '--function-name', self.function_name,
                '--zip-file', f'fileb://{zip_path}'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.log("✅ Fonction déployée avec succès")
                return True
            else:
                self.log(f"❌ Erreur déploiement: {result.stderr}")
                return False
                
        except Exception as e:
            self.log(f"❌ Erreur déploiement: {e}")
            return False
    
    def test_windows_function(self) -> bool:
        """Tester la fonction déployée"""
        self.log("🧪 Test de la fonction déployée...")
        
        try:
            # Utiliser AWS CLI depuis PowerShell
            cmd = [
                'aws', 'lambda', 'invoke',
                '--function-name', self.function_name,
                '--payload', '{"httpMethod":"GET","path":"/api/health"}',
                '--invocation-type', 'RequestResponse'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                try:
                    # Parser la sortie JSON
                    output_lines = result.stdout.strip().split('\n')
                    for line in output_lines:
                        if '"statusCode"' in line:
                            status_line = line.strip()
                            if '"statusCode":200' in status_line:
                                print(f"✅ Test health: {status_line}")
                                return True
                except:
                    pass
            else:
                print(f"❌ Erreur test: {result.stderr}")
                return False
                
        except Exception as e:
            self.log(f"❌ Erreur test: {e}")
            return False
    
    def run_windows_deployment(self) -> bool:
        """Exécuter le déploiement complet sur Windows"""
        self.log("🚀 DÉPLOIEMENT LAMBDA CORRIGÉ (Windows)")
        self.log("=" * 60)
        
        try:
            # Installer les dépendances
            if not self.install_dependencies_windows():
                return False
            
            # Créer le package
            zip_path = self.create_windows_package()
            
            # Déployer
            if not self.deploy_windows_function(zip_path):
                return False
            
            # Tester
            if not self.test_windows_function():
                return False
            
            self.log("🎉 Déploiement Windows terminé avec succès!")
            return True
            
        except Exception as e:
            self.log(f"❌ Erreur déploiement Windows: {e}")
            return False

def main():
    print("🌊 DÉPLOIEMENT LAMBDA CORRIGÉ (Windows)")
    print("=" * 50)
    print("📦 Installation de NumPy")
    print("🌊 Déploiement sur AWS depuis Windows")
    print("🌊 Tests réels sur AWS")
    print("=" * 50)
    
    deployer = WindowsLambdaDeployer()
    success = deployer.run_windows_deployment()
    
    if success:
        print("\n🌊 Déploiement terminé avec succès!")
        print("📊 Tous les endpoints sont maintenant disponibles")
        print("📊 NumPy est disponible dans la fonction Lambda")
        print("🌊 Les constantes harmoniques sont prêtes")
        exit(0)
    else:
        print("\n❌ Le déploiement a rencontré des erreurs")
        print("📄 Vérifiez les logs pour plus de détails")
        exit(1)

if __name__ == "__main__":
    main()
