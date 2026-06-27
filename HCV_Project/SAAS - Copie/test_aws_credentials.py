#!/usr/bin/env python3
"""
TEST DES CREDENTIALS AWS
Script de test pour vérifier la configuration AWS
"""

import os
import boto3
from botocore.exceptions import ClientError

def test_aws_credentials():
    """Test les credentials AWS"""
    
    print("🧪 TEST DES CREDENTIALS AWS")
    print("=" * 40)
    
    # Vérification des variables d'environnement
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("AWS_REGION", "us-east-1")
    
    print(f"🔑 Access Key: {'✅ Configuré' if access_key else '❌ Manquant'}")
    print(f"🔐 Secret Key: {'✅ Configuré' if secret_key else '❌ Manquant'}")
    print(f"🌍 Région: {region}")
    
    if not access_key or not secret_key:
        print("\n❌ Credentials incomplets!")
        print("📋 Configurez vos credentials avec:")
        print("   - source set_aws_env.sh (Linux/Mac)")
        print("   - .\\set_aws_env.ps1 (Windows)")
        print("   - aws configure")
        return False
    
    # Test de connexion AWS
    try:
        print("\n🔍 Test de connexion AWS...")
        sts_client = boto3.client('sts', region_name=region)
        identity = sts_client.get_caller_identity()
        
        print(f"✅ Connexion réussie!")
        print(f"👤 User ARN: {identity.get('Arn', 'N/A')}")
        print(f"🆔 Account ID: {identity.get('Account', 'N/A')}")
        
        # Test S3
        print("\n📦 Test d'accès S3...")
        s3_client = boto3.client('s3', region_name=region)
        
        # Test de création de bucket
        bucket_name = "harmonic-ai-knowledge-base"
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"✅ Bucket '{bucket_name}' accessible")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                print(f"📭 Bucket '{bucket_name}' n'existe pas (sera créé)")
            else:
                print(f"⚠️ Erreur accès bucket: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur connexion AWS: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_aws_credentials()
    if success:
        print("\n🚀 Configuration AWS valide! Prêt pour l'upload S3.")
    else:
        print("\n❌ Configuration AWS invalide. Veuillez configurer vos credentials.")
