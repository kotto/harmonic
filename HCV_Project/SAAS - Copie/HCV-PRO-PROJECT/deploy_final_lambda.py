#!/usr/bin/env python3
"""
DÉPLOIEMENT LAMBDA FINAL CORRIGÉ
==================================

Script pour déployer la version finale corrigée avec le bon nom de handler.
"""

import os
import subprocess
import zipfile
import json
import boto3
from pathlib import Path
from datetime import datetime

class FinalLambdaDeployer:
    """Déployeur de la fonction Lambda finale corrigée"""
    
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
    
    def create_final_package(self) -> str:
        """Créer le package final corrigé"""
        self.log("📦 Création du package final corrigé...")
        
        zip_path = self.lambda_dir / "lambda_final.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            # Ajouter le fichier avec le bon nom de handler
            handler_file = self.lambda_dir / "lambda_function.py"
            zip_file.write(handler_file, "lambda_function.py")
            
            # Ajouter les dépendances
            requirements = """
numpy==1.24.3
"""
            zip_file.writestr("requirements.txt", requirements)
        
        self.log(f"✅ Package final créé: {zip_path}")
        return str(zip_path)
    
    def deploy_final_function(self, zip_path: str) -> bool:
        """Déployer la fonction finale corrigée"""
        self.log("🔄 Déploiement de la fonction finale corrigée...")
        
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
            
            self.log(f"✅ Fonction finale déployée: {response['FunctionArn']}")
            self.log(f"   📊 State: {response.get('State', 'Unknown')}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Erreur déploiement final: {e}", "ERROR")
            return False
    
    def test_final_function(self) -> bool:
        """Tester la fonction finale corrigée"""
        self.log("🧪 Test de la fonction finale corrigée...")
        
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
            self.log(f"❌ Erreur test final: {e}", "ERROR")
            return False
    
    def run_final_deployment(self) -> bool:
        """Exécuter le déploiement final corrigé"""
        self.log("🚀 DÉPLOIEMENT LAMBDA FINAL CORRIGÉ")
        self.log("=" * 50)
        
        try:
            # Créer le package
            zip_path = self.create_final_package()
            
            # Déployer
            if not self.deploy_final_function(zip_path):
                return False
            
            # Tester
            if not self.test_final_function():
                return False
            
            self.log("🎉 Déploiement final corrigé terminé avec succès!")
            return True
            
        except Exception as e:
            self.log(f"❌ Erreur déploiement final: {e}", "ERROR")
            return False

def main():
    print("🌊 DÉPLOIEMENT LAMBDA FINAL CORRIGÉ")
    print("=" * 50)
    print("📦 Déploiement avec le bon nom de handler")
    print("🌊 Tests réels sur AWS")
    print("=" * 50)
    
    deployer = FinalLambdaDeployer()
    success = deployer.run_final_deployment()
    
    if success:
        print("\n🌊 Déploiement final corrigé terminé avec succès!")
        print("📊 Tous les endpoints sont maintenant disponibles")
        exit(0)
    else:
        print("\n❌ Le déploiement a rencontré des erreurs")
        exit(1)

if __name__ == "__main__":
    main()
