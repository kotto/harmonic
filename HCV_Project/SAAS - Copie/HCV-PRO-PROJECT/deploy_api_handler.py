#!/usr/bin/env python3
"""
DÉPLOIEMENT HANDLER API LAMBDA
==============================

Déploiement du handler API corrigé pour résoudre
l'erreur "Internal server error".
"""

import zipfile
import boto3
import os

def create_lambda_package():
    """Créer le package ZIP pour Lambda"""
    
    with zipfile.ZipFile('api_handler.zip', 'w') as zipf:
        zipf.write('api_handler_lambda.py', 'api_handler_lambda.py')
    
    print("✅ Package ZIP créé: api_handler.zip")

def deploy_lambda_handler():
    """Déployer le handler sur Lambda"""
    
    lambda_client = boto3.client('lambda', region_name='eu-west-3')
    
    try:
        # Lire le fichier ZIP
        with open('api_handler.zip', 'rb') as f:
            zip_content = f.read()
        
        # Mettre à jour la fonction Lambda
        response = lambda_client.update_function_code(
            FunctionName='hcv-pro-deepseek-handler',
            ZipFile=zip_content,
            Publish=True  # Créer une nouvelle version
        )
        
        print(f"✅ Handler déployé: {response['FunctionName']}")
        print(f"📦 Version: {response['Version']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur déploiement: {e}")
        return False

if __name__ == "__main__":
    print("🚀 DÉPLOIEMENT HANDLER API LAMBDA")
    print("=" * 50)
    
    # Créer le package
    create_lambda_package()
    
    # Déployer
    success = deploy_lambda_handler()
    
    if success:
        print("\n🎉 DÉPLOIEMENT RÉUSSI!")
        print("🌊 Testez maintenant l'API:")
        print("curl -X GET 'https://0sdwsv4yba.execute-api.eu-west-3.amazonaws.com/prod/api/health'")
    else:
        print("\n❌ DÉPLOIEMENT ÉCHOUÉ")
