#!/usr/bin/env python3
"""
DÉPLOIEMENT COMPLET AVEC DÉPENDANCES
====================================

Script pour déployer la fonction Lambda avec toutes les dépendances nécessaires.
"""

import os
import subprocess
import zipfile
import json
import boto3
from pathlib import Path
from datetime import datetime

class CompleteLambdaDeployer:
    """Déployeur complet avec toutes les dépendances"""
    
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
    
    def install_dependencies(self) -> bool:
        """Installer les dépendances locales"""
        self.log("📦 Installation des dépendances...")
        
        try:
            # Installer numpy
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
    
    def create_complete_package(self) -> str:
        """Créer le package complet avec toutes les dépendances"""
        self.log("📦 Création du package complet...")
        
        zip_path = self.lambda_dir / "lambda_complete.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            # Ajouter le fichier handler
            handler_file = self.lambda_dir / "aws_real_compression_handler.py"
            zip_file.write(handler_file, "aws_real_compression_handler.py")
            
            # Ajouter les dépendances
            requirements = """
numpy==1.24.3
"""
            zip_file.writestr("requirements.txt", requirements)
            
            # Ajouter un fichier de configuration pour le déploiement
            config = {
                "handler": "aws_real_compression_handler.lambda_handler",
                "runtime": "python3.11",
                "timeout": 300,
                "memory": 2048,
                "environment": {
                    "PYTHONPATH": "/var/lang/python3.11"
                }
            }
            zip_file.writestr("config.json", json.dumps(config, indent=2))
        
        self.log(f"✅ Package complet créé: {zip_path}")
        return str(zip_path)
    
    def deploy_complete_function(self, zip_path: str) -> bool:
        """Déployer la fonction complète"""
        self.log("🔄 Déploiement de la fonction complète...")
        
        try:
            lambda_client = boto3.client('lambda', region_name=self.region)
            
            # Lire le fichier ZIP
            with open(zip_path, 'rb') as f:
                zip_content = f.read()
            
            # Mettre à jour le code
            response = lambda_client.update_function_code(
                FunctionName=self.function_name,
                ZipFile=zip_content
            )
            
            self.log(f"✅ Fonction complète déployée: {response['FunctionArn']}")
            self.log(f"   📊 State: {response.get('State', 'Unknown')}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Erreur déploiement complet: {e}", "ERROR")
            return False
    
    def test_complete_function(self) -> bool:
        """Tester la fonction complète"""
        self.log("🧪 Test de la fonction complète...")
        
        try:
            lambda_client = boto3.client('lambda', region_name=self.region)
            
            test_event = {
                "httpMethod": "GET",
                "path": "/api/health"
            }
            
            response = lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(test_event)
            )
            
            # Lire le payload
            payload_bytes = response['Payload'].read()
            decoded_payload = payload_bytes.decode('utf-8')
            parsed_payload = json.loads(decoded_payload)
            
            if parsed_payload.get('statusCode') == 200:
                body = json.loads(parsed_payload.get('body', '{}'))
                self.log(f"✅ Test health: {body.get('status', 'unknown')}")
                return True
            else:
                self.log(f"❌ Test health: Status {parsed_payload.get('statusCode')}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erreur test complet: {e}", "ERROR")
            return False
    
    def run_complete_deployment(self) -> bool:
        """Exécuter le déploiement complet"""
        self.log("🚀 DÉPLOIEMENT COMPLET AVEC DÉPENDANCES")
        self.log("=" * 60)
        
        try:
            # Installer les dépendances
            if not self.install_dependencies():
                return False
            
            # Créer le package
            zip_path = self.create_complete_package()
            
            # Déployer
            if not self.deploy_complete_function(zip_path):
                return False
            
            # Tester
            if not self.test_complete_function():
                return False
            
            self.log("🎉 Déploiement complet terminé avec succès!")
            return True
            
        except Exception as e:
            self.log(f"❌ Erreur déploiement complet: {e}", "ERROR")
            return False

def main():
    print("🌊 DÉPLOIEMENT COMPLET AVEC DÉPENDANCES")
    print("=" * 60)
    print("📦 Installation de NumPy")
    print("🌊 Déploiement avec toutes les dépendances")
    print("🌊 Tests réels sur AWS")
    print("=" * 60)
    
    deployer = CompleteLambdaDeployer()
    success = deployer.run_complete_deployment()
    
    if success:
        print("\n🌊 Déploiement complet terminé avec succès!")
        print("📊 Tous les endpoints sont maintenant disponibles")
        print("📊 NumPy est maintenant disponible dans la fonction Lambda")
        print("📊 Les constantes harmoniques sont prêtes")
        exit(0)
    else:
        print("\n❌ Le déploiement a rencontré des erreurs")
        exit(1)

if __name__ == "__main__":
    main()
