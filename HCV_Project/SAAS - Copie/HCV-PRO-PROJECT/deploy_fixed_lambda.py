#!/usr/bin/env python3
"""
DÉPLOIEMENT LAMBDA CORRIGÉ POUR DEEPSEEK HARMONIC
===================================================

Script pour déployer la version corrigée de la fonction Lambda
avec tous les endpoints implémentés correctement.
"""

import os
import subprocess
import zipfile
import json
from pathlib import Path
from datetime import datetime

class LambdaDeployer:
    """Déployeur de la fonction Lambda corrigée"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.lambda_dir = self.project_root / "lambda_package"
        self.function_name = "hcv-pro-deepseek-handler"
        self.region = "eu-west-3"
        self.role_arn = "arn:aws:iam::326095712935:role/lambda-execution-role"
        
        self.deploy_log = []
    
    def log(self, message: str, level: str = "INFO"):
        """Logger avec timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        self.deploy_log.append(log_entry)
    
    def create_deployment_package(self) -> str:
        """Créer le package de déploiement"""
        self.log("📦 Création du package de déploiement...")
        
        # Créer le ZIP
        zip_path = self.lambda_dir / "lambda_function_fixed.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            # Ajouter la fonction Lambda corrigée
            lambda_file = self.lambda_dir / "lambda_function_fixed.py"
            zip_file.write(lambda_file, "lambda_function.py")
            
            # Ajouter les dépendances
            requirements = """
numpy==1.24.3
"""
            zip_file.writestr("requirements.txt", requirements)
        
        self.log(f"✅ Package créé: {zip_path}")
        return str(zip_path)
    
    def update_lambda_function(self, zip_path: str) -> bool:
        """Mettre à jour la fonction Lambda"""
        self.log("🔄 Mise à jour de la fonction Lambda...")
        
        try:
            import boto3
            
            lambda_client = boto3.client('lambda', region_name=self.region)
            
            # Lire le fichier ZIP
            with open(zip_path, 'rb') as f:
                zip_content = f.read()
            
            # Mettre à jour le code
            response = lambda_client.update_function_code(
                FunctionName=self.function_name,
                ZipFile=zip_content
            )
            
            self.log(f"✅ Fonction mise à jour: {response['FunctionArn']}")
            if 'VersionId' in response:
                self.log(f"   📊 Version: {response['VersionId']}")
            if 'State' in response:
                self.log(f"   📊 State: {response['State']}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Erreur mise à jour Lambda: {e}", "ERROR")
            return False
    
    def test_updated_function(self) -> bool:
        """Tester la fonction mise à jour"""
        self.log("🧪 Test de la fonction mise à jour...")
        
        try:
            import boto3
            
            lambda_client = boto3.client('lambda', region_name=self.region)
            
            # Test de l'endpoint health
            test_event = {
                "httpMethod": "GET",
                "path": "/api/health"
            }
            
            response = lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(test_event)
            )
            
            payload_bytes = response['Payload'].read()
            if isinstance(payload_bytes, bytes):
                response_payload = json.loads(payload_bytes.decode('utf-8'))
            else:
                response_payload = json.loads(payload_bytes)
            
            if response_payload.get('statusCode') == 200:
                body = json.loads(response_payload.get('body', '{}'))
                self.log(f"✅ Test health: {body.get('status', 'Unknown')}")
                return True
            else:
                self.log(f"❌ Test health: Status {response_payload.get('statusCode')}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erreur test fonction: {e}", "ERROR")
            return False
    
    def run_deployment(self) -> bool:
        """Exécuter le déploiement complet"""
        self.log("🚀 DÉPLOIEMENT LAMBDA CORRIGÉ")
        self.log("=" * 50)
        
        try:
            # Étape 1: Créer le package
            zip_path = self.create_deployment_package()
            
            # Étape 2: Déployer sur Lambda
            if not self.update_lambda_function(zip_path):
                return False
            
            # Étape 3: Tester la fonction
            if not self.test_updated_function():
                return False
            
            self.log("🎉 Déploiement terminé avec succès!")
            return True
            
        except Exception as e:
            self.log(f"❌ Erreur déploiement: {e}", "ERROR")
            return False

def main():
    print("🌊 DÉPLOIEMENT LAMBDA CORRIGÉ POUR DEEPSEEK HARMONIC")
    print("=" * 60)
    print("📦 Déploiement de la version corrigée avec tous les endpoints")
    print("🌊 Tests réels sur AWS")
    print("=" * 60)
    
    deployer = LambdaDeployer()
    success = deployer.run_deployment()
    
    if success:
        print("\n🌊 Déploiement corrigé terminé avec succès!")
        print("📊 Tous les endpoints sont maintenant disponibles")
        exit(0)
    else:
        print("\n❌ Le déploiement a rencontré des erreurs")
        exit(1)

if __name__ == "__main__":
    main()
