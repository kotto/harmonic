#!/usr/bin/env python3
"""
DÉPLOIEMENT LAMBDA CORRIGÉ FINAL
====================================

Script pour déployer la version corrigée avec le bon nom de fichier.
"""

import os
import subprocess
import zipfile
import json
import boto3
from pathlib import Path
from datetime import datetime

class CorrectedLambdaDeployer:
    """Déployeur de la fonction Lambda corrigée"""
    
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
    
    def create_corrected_package(self) -> str:
        """Créer le package corrigé"""
        self.log("📦 Création du package corrigé...")
        
        zip_path = self.lambda_dir / "lambda_corrected.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            # Ajouter le fichier avec le bon nom
            handler_file = self.lambda_dir / "aws_real_compression_handler.py"
            zip_file.write(handler_file, "lambda_function.py")
            
            # Ajouter les dépendances
            requirements = """
numpy==1.24.3
"""
            zip_file.writestr("requirements.txt", requirements)
        
        self.log(f"✅ Package corrigé créé: {zip_path}")
        return str(zip_path)
    
    def deploy_corrected_function(self, zip_path: str) -> bool:
        """Déployer la fonction corrigée"""
        self.log("🔄 Déploiement de la fonction corrigée...")
        
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
            
            self.log(f"✅ Fonction corrigée déployée: {response['FunctionArn']}")
            self.log(f"   📊 State: {response.get('State', 'Unknown')}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Erreur déploiement: {e}", "ERROR")
            return False
    
    def test_corrected_function(self) -> bool:
        """Tester la fonction corrigée"""
        self.log("🧪 Test de la fonction corrigée...")
        
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
            
            # Lire le payload (StreamingBody)
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
    
    def run_corrected_deployment(self) -> bool:
        """Exécuter le déploiement corrigé"""
        self.log("🚀 DÉPLOIEMENT LAMBDA CORRIGÉ FINAL")
        self.log("=" * 50)
        
        try:
            # Créer le package
            zip_path = self.create_corrected_package()
            
            # Déployer
            if not self.deploy_corrected_function(zip_path):
                return False
            
            # Tester
            if not self.test_corrected_function():
                return False
            
            self.log("🎉 Déploiement corrigé terminé avec succès!")
            return True
            
        except Exception as e:
            self.log(f"❌ Erreur déploiement corrigé: {e}", "ERROR")
            return False

def main():
    print("🌊 DÉPLOIEMENT LAMBDA CORRIGÉ FINAL")
    print("=" * 50)
    print("📦 Déploiement avec le bon nom de fichier")
    print("🌊 Tests réels sur AWS")
    print("=" * 50)
    
    deployer = CorrectedLambdaDeployer()
    success = deployer.run_corrected_deployment()
    
    if success:
        print("\n🌊 Déploiement corrigé terminé avec succès!")
        print("📊 Les endpoints sont maintenant disponibles")
        exit(0)
    else:
        print("\n❌ Le déploiement a rencontré des erreurs")
        exit(1)

if __name__ == "__main__":
    main()
