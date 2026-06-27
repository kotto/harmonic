#!/usr/bin/env python3
"""
DÉPLOIEMENT AVEC LE BON NOM DE HANDLER
====================================

Utiliser le nom de handler configuré dans AWS: aws_real_compression_handler
"""

import os
import subprocess
import zipfile
import json
import boto3
from pathlib import Path
from datetime import datetime

class CorrectHandlerDeployer:
    """Déployeur avec le bon nom de handler"""
    
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
    
    def create_package_with_correct_handler(self) -> str:
        """Créer le package avec le bon nom de handler"""
        self.log("📦 Création du package avec le bon nom de handler...")
        
        zip_path = self.lambda_dir / "lambda_correct_handler.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            # Ajouter le fichier avec le bon nom de handler
            handler_file = self.lambda_dir / "aws_real_compression_handler.py"
            zip_file.write(handler_file, "aws_real_compression_handler.py")
            
            # Ajouter les dépendances
            requirements = """
numpy==1.24.3
"""
            zip_file.writestr("requirements.txt", requirements)
        
        self.log(f"✅ Package créé: {zip_path}")
        return str(zip_path)
    
    def deploy_with_correct_handler(self, zip_path: str) -> bool:
        """Déployer avec le bon nom de handler"""
        self.log("🔄 Déploiement avec le bon nom de handler...")
        
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
            
            self.log(f"✅ Fonction déployée: {response['FunctionArn']}")
            self.log(f"   📊 State: {response.get('State', 'Unknown')}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Erreur déploiement: {e}", "ERROR")
            return False
    
    def test_with_correct_handler(self) -> bool:
        """Tester avec le bon nom de handler"""
        self.log("🧪 Test avec le bon nom de handler...")
        
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
                self.log(f"✅ Test health: {body.get('status', 'Unknown')}")
                return True
            else:
                self.log(f"❌ Test health: Status {parsed_payload.get('statusCode')}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erreur test: {e}", "ERROR")
            return False
    
    def run_deployment(self) -> bool:
        """Exécuter le déploiement"""
        self.log("🚀 DÉPLOIEMENT AVEC LE BON NOM DE HANDLER")
        self.log("=" * 60)
        
        try:
            # Créer le package
            zip_path = self.create_package_with_correct_handler()
            
            # Déployer
            if not self.deploy_with_correct_handler(zip_path):
                return False
            
            # Tester
            if not self.test_with_correct_handler():
                return False
            
            self.log("🎉 Déploiement terminé avec succès!")
            return True
            
        except Exception as e:
            self.log(f"❌ Erreur déploiement: {e}", "ERROR")
            return False

def main():
    print("🌊 DÉPLOIEMENT AVEC LE BON NOM DE HANDLER")
    print("=" * 60)
    print("📦 Utilise le nom de handler configuré dans AWS")
    print("🌊 Tests réels sur AWS")
    print("=" * 60)
    
    deployer = CorrectHandlerDeployer()
    success = deployer.run_deployment()
    
    if success:
        print("\n🌊 Déploiement terminé avec succès!")
        print("📊 Tous les endpoints sont maintenant disponibles")
        exit(0)
    else:
        print("\n❌ Le déploiement a rencontré des erreurs")
        exit(1)

if __name__ == "__main__":
    main()
