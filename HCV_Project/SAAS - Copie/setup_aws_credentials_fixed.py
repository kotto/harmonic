#!/usr/bin/env python3
"""
🔑 CONFIGURATION DES CREDENTIALS AWS
Guide et configuration des credentials AWS pour Harmonic AI
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

def create_aws_credentials_file():
    """Crée le fichier de credentials AWS"""
    
    print("🔑 CONFIGURATION DES CREDENTIALS AWS")
    print("=" * 50)
    
    # Chemin du fichier credentials
    aws_dir = Path.home() / ".aws"
    credentials_file = aws_dir / "credentials"
    config_file = aws_dir / "config"
    
    print(f"📁 Répertoire AWS: {aws_dir}")
    print(f"📄 Fichier credentials: {credentials_file}")
    print(f"📄 Fichier config: {config_file}")
    
    # Création du répertoire .aws
    aws_dir.mkdir(exist_ok=True)
    
    # Template pour les credentials
    credentials_template = """[default]
aws_access_key_id = VOTRE_ACCESS_KEY_ID
aws_secret_access_key = VOTRE_SECRET_ACCESS_KEY

[harmonic-ai]
aws_access_key_id = VOTRE_ACCESS_KEY_ID
aws_secret_access_key = VOTRE_SECRET_ACCESS_KEY
"""
    
    # Template pour la configuration
    config_template = """[default]
region = us-east-1
output = json

[profile harmonic-ai]
region = us-east-1
output = json
"""
    
    # Écriture des fichiers
    try:
        with open(credentials_file, 'w') as f:
            f.write(credentials_template)
        print(f"✅ Fichier credentials créé: {credentials_file}")
        
        with open(config_file, 'w') as f:
            f.write(config_template)
        print(f"✅ Fichier config créé: {config_file}")
        
    except Exception as e:
        print(f"❌ Erreur création fichiers: {str(e)}")
        return False
    
    return True

def create_environment_variables_script():
    """Crée un script pour les variables d'environnement"""
    
    print(f"\n🌍 CRÉATION DU SCRIPT VARIABLES D'ENVIRONNEMENT")
    print("-" * 50)
    
    # Script Windows (PowerShell)
    ps_script = """# Variables d'environnement AWS pour Harmonic AI
# À exécuter dans PowerShell: .\\set_aws_env.ps1

$env:AWS_ACCESS_KEY_ID = "VOTRE_ACCESS_KEY_ID"
$env:AWS_SECRET_ACCESS_KEY = "VOTRE_SECRET_ACCESS_KEY"
$env:AWS_DEFAULT_REGION = "us-east-1"
$env:AWS_REGION = "us-east-1"
$env:HARMONIC_BUCKET = "harmonic-ai-knowledge-base"

Write-Host "🔑 Variables d'environnement AWS configurées"
Write-Host "📦 Bucket: $env:HARMONIC_BUCKET"
Write-Host "🌍 Région: $env:AWS_REGION"
Write-Host "✅ Prêt pour l'upload S3"
"""
    
    # Script Bash/Linux
    bash_script = """#!/bin/bash
# Variables d'environnement AWS pour Harmonic AI
# À exécuter: source set_aws_env.sh

export AWS_ACCESS_KEY_ID="VOTRE_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="VOTRE_SECRET_ACCESS_KEY"
export AWS_DEFAULT_REGION="us-east-1"
export AWS_REGION="us-east-1"
export HARMONIC_BUCKET="harmonic-ai-knowledge-base"

echo "🔑 Variables d'environnement AWS configurées"
echo "📦 Bucket: $HARMONIC_BUCKET"
echo "🌍 Région: $AWS_REGION"
echo "✅ Prêt pour l'upload S3"
"""
    
    try:
        # Écriture du script PowerShell
        with open("set_aws_env.ps1", 'w') as f:
            f.write(ps_script)
        print("✅ Script PowerShell créé: set_aws_env.ps1")
        
        # Écriture du script Bash
        with open("set_aws_env.sh", 'w') as f:
            f.write(bash_script)
        print("✅ Script Bash créé: set_aws_env.sh")
        
        # Rendre le script Bash exécutable
        os.chmod("set_aws_env.sh", 0o755)
        
    except Exception as e:
        print(f"❌ Erreur création scripts: {str(e)}")
        return False
    
    return True

def create_test_script():
    """Crée un script de test simple"""
    
    print(f"\n🧪 CRÉATION DU SCRIPT DE TEST")
    print("-" * 30)
    
    test_script = '''#!/usr/bin/env python3
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
        print("\\n❌ Credentials incomplets!")
        print("📋 Configurez vos credentials avec:")
        print("   - source set_aws_env.sh (Linux/Mac)")
        print("   - .\\\\set_aws_env.ps1 (Windows)")
        print("   - aws configure")
        return False
    
    # Test de connexion AWS
    try:
        print("\\n🔍 Test de connexion AWS...")
        sts_client = boto3.client('sts', region_name=region)
        identity = sts_client.get_caller_identity()
        
        print(f"✅ Connexion réussie!")
        print(f"👤 User ARN: {identity.get('Arn', 'N/A')}")
        print(f"🆔 Account ID: {identity.get('Account', 'N/A')}")
        
        # Test S3
        print("\\n📦 Test d'accès S3...")
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
        print("\\n🚀 Configuration AWS valide! Prêt pour l'upload S3.")
    else:
        print("\\n❌ Configuration AWS invalide. Veuillez configurer vos credentials.")
'''
    
    try:
        with open("test_aws_credentials.py", 'w', encoding='utf-8') as f:
            f.write(test_script)
        print("✅ Script de test créé: test_aws_credentials.py")
        
    except Exception as e:
        print(f"❌ Erreur création script test: {str(e)}")
        return False
    
    return True

def create_simple_upload_script():
    """Crée un script d'upload simple"""
    
    print(f"\n🚀 CRÉATION DU SCRIPT D'UPLOAD SIMPLE")
    print("-" * 40)
    
    upload_script = '''#!/usr/bin/env python3
"""
UPLOAD SIMPLE DES MODÈLES HARMONIC AI SUR S3
Script simple pour uploader les modèles locaux
"""

import os
import sys
import json
import time
import boto3
from pathlib import Path

def simple_upload():
    """Upload simple des modèles"""
    
    print("🚀 UPLOAD SIMPLE DES MODÈLES HARMONIC AI")
    print("=" * 50)
    
    # Configuration
    bucket_name = "harmonic-ai-knowledge-base"
    region = "us-east-1"
    local_path = Path("local_s3_structure")
    
    if not local_path.exists():
        print("❌ Répertoire local_s3_structure non trouvé!")
        return False
    
    # Initialisation S3
    try:
        s3_client = boto3.client('s3', region_name=region)
        print(f"✅ Client S3 initialisé")
    except Exception as e:
        print(f"❌ Erreur initialisation S3: {str(e)}")
        return False
    
    # Création du bucket si nécessaire
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ Bucket '{bucket_name}' accessible")
    except:
        try:
            s3_client.create_bucket(Bucket=bucket_name)
            print(f"✅ Bucket '{bucket_name}' créé")
        except Exception as e:
            print(f"❌ Erreur création bucket: {str(e)}")
            return False
    
    # Upload des fichiers
    files_uploaded = 0
    total_size = 0
    
    for file_path in local_path.rglob('*'):
        if file_path.is_file():
            # Construction de la clé S3
            relative_path = file_path.relative_to(local_path)
            s3_key = str(relative_path).replace('\\\\', '/')
            
            try:
                # Upload
                s3_client.upload_file(
                    Filename=str(file_path),
                    Bucket=bucket_name,
                    Key=s3_key
                )
                
                files_uploaded += 1
                total_size += file_path.stat().st_size
                
                if files_uploaded % 10 == 0:
                    print(f"   📤 {files_uploaded} fichiers uploadés...")
                    
            except Exception as e:
                print(f"❌ Erreur upload {file_path.name}: {str(e)}")
    
    print(f"\\n🏆 UPLOAD TERMINÉ!")
    print(f"📊 Fichiers uploadés: {files_uploaded}")
    print(f"💾 Taille totale: {total_size/1024:.1f} KB")
    print(f"📦 Bucket: s3://{bucket_name}/")
    
    return True

if __name__ == "__main__":
    success = simple_upload()
    if success:
        print("\\n🌊 Upload réussi!")
    else:
        print("\\n❌ Upload échoué.")
        sys.exit(1)
'''
    
    try:
        with open("simple_upload_to_s3.py", 'w', encoding='utf-8') as f:
            f.write(upload_script)
        print("✅ Script d'upload simple créé: simple_upload_to_s3.py")
        
    except Exception as e:
        print(f"❌ Erreur création script upload: {str(e)}")
        return False
    
    return True

def main():
    """Fonction principale"""
    
    print("🔑 CONFIGURATION COMPLÈTE AWS POUR HARMONIC AI")
    print("=" * 60)
    print("🌊 Préparation de l'environnement AWS pour l'upload S3")
    print("=" * 60)
    
    success = True
    
    # Création des fichiers de configuration
    if not create_aws_credentials_file():
        success = False
    
    # Création des scripts d'environnement
    if not create_environment_variables_script():
        success = False
    
    # Création du script de test
    if not create_test_script():
        success = False
    
    # Création du script d'upload simple
    if not create_simple_upload_script():
        success = False
    
    if success:
        print(f"\n🎉 CONFIGURATION AWS PRÉPARÉE!")
        print("=" * 50)
        print("📋 Fichiers créés:")
        print("   🔑 ~/.aws/credentials")
        print("   🔧 ~/.aws/config")
        print("   🌍 set_aws_env.ps1 (Windows)")
        print("   🌍 set_aws_env.sh (Linux/Mac)")
        print("   🧪 test_aws_credentials.py")
        print("   🚀 simple_upload_to_s3.py")
        print()
        print("📝 PROCHAINES ÉTAPES:")
        print("1. Obtenez vos credentials AWS")
        print("2. Modifiez les fichiers avec vos vraies clés")
        print("3. Exécutez: python test_aws_credentials.py")
        print("4. Si OK: python simple_upload_to_s3.py")
        print()
        print("🌊 Prêt pour l'upload Harmonic AI sur AWS S3!")
    else:
        print("❌ Erreur lors de la préparation")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
