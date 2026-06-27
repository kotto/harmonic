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

def create_aws_configuration_guide():
    """Crée un guide de configuration AWS"""
    
    print(f"\n📋 CRÉATION DU GUIDE DE CONFIGURATION AWS")
    print("-" * 50)
    
    guide = """# 🔑 GUIDE DE CONFIGURATION AWS POUR HARMONIC AI

## 📋 ÉTAPES DE CONFIGURATION

### 1️⃣ OBTENIR VOS CREDENTIALS AWS

1. Connectez-vous à la [Console AWS](https://console.aws.amazon.com/)
2. Allez dans "IAM" → "Users" → "Your User" → "Security credentials"
3. Cliquez sur "Create access key"
4. Choisissez "Command Line Interface (CLI)"
5. Notez vos "Access key ID" et "Secret access key"

### 2️⃣ MÉTHODES DE CONFIGURATION

#### 🎯 MÉTHODE 1: Variables d'environnement (Recommandé)

**Windows PowerShell:**
```powershell
.\\set_aws_env.ps1
```

**Linux/Mac:**
```bash
source set_aws_env.sh
```

**Manuel:**
```bash
export AWS_ACCESS_KEY_ID="VOTRE_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="VOTRE_SECRET_ACCESS_KEY"
export AWS_DEFAULT_REGION="us-east-1"
export AWS_REGION="us-east-1"
export HARMONIC_BUCKET="harmonic-ai-knowledge-base"
```

#### 📁 MÉTHODE 2: Fichier ~/.aws/credentials

Le fichier a déjà été créé ici: `~/.aws/credentials`

Modifiez-le avec vos vraies credentials:
```ini
[default]
aws_access_key_id = VOTRE_ACCESS_KEY_ID
aws_secret_access_key = VOTRE_SECRET_ACCESS_KEY
```

#### 🛠️ MÉTHODE 3: AWS CLI

```bash
aws configure
# Entrez vos credentials quand demandé
# Region: us-east-1
# Output format: json
```

### 3️⃣ VÉRIFICATION

```bash
python check_s3_bucket.py
```

### 4️⃣ UPLOAD DES MODÈLES

```bash
python upload_local_models_to_s3.py
```

## 🔐 PERMISSIONS NÉCESSAIRES

Votre utilisateur AWS a besoin des permissions suivantes:

- `s3:CreateBucket`
- `s3:PutObject`
- `s3:GetObject`
- `s3:ListBucket`
- `s3:DeleteObject`

Policy IAM recommandée:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:*"
            ],
            "Resource": [
                "arn:aws:s3:::harmonic-ai-knowledge-base",
                "arn:aws:s3:::harmonic-ai-knowledge-base/*"
            ]
        }
    ]
}
```

## 🚀 STRUCTURE PRÉPARE

La structure S3 locale est prête:
- 📁 `local_s3_structure/` (114 fichiers, 1.94 MB)
- 📋 `local_structure_manifest.json`
- 📋 `file_index.json`

## 📞 SUPPORT

Si vous avez des problèmes:
1. Vérifiez que vos credentials sont corrects
2. Assurez-vous que la région est `us-east-1`
3. Vérifiez les permissions IAM
4. Contactez votre administrateur AWS si nécessaire

---

🌊 **Prêt pour l'upload Harmonic AI sur AWS S3 !**
"""
    
    try:
        with open("AWS_CONFIGURATION_GUIDE.md", 'w', encoding='utf-8') as f:
            f.write(guide)
        print("✅ Guide créé: AWS_CONFIGURATION_GUIDE.md")
        
    except Exception as e:
        print(f"❌ Erreur création guide: {str(e)}")
        return False
    
    return True

def create_temporary_test_script():
    """Crée un script de test temporaire"""
    
    print(f"\n🧪 CRÉATION DU SCRIPT DE TEST")
    print("-" * 30)
    
    test_script = '''#!/usr/bin/env python3
"""
TEST DES CREDENTIALS AWS
Script de test pour vérifier la configuration AWS
'''

import os
import boto3
from botocore.exceptions import ClientError

def test_aws_credentials():
    \"\"\"Test les credentials AWS\"\"\"
    
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
"""
    
    try:
        with open("test_aws_credentials.py", 'w', encoding='utf-8') as f:
            f.write(test_script)
        print("✅ Script de test créé: test_aws_credentials.py")
        
    except Exception as e:
        print(f"❌ Erreur création script test: {str(e)}")
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
    
    # Création du guide
    if not create_aws_configuration_guide():
        success = False
    
    # Création du script de test
    if not create_temporary_test_script():
        success = False
    
    if success:
        print(f"\n🎉 CONFIGURATION AWS PRÉPARÉE!")
        print("=" * 50)
        print("📋 Fichiers créés:")
        print("   🔑 ~/.aws/credentials")
        print("   🔧 ~/.aws/config")
        print("   🌍 set_aws_env.ps1 (Windows)")
        print("   🌍 set_aws_env.sh (Linux/Mac)")
        print("   📋 AWS_CONFIGURATION_GUIDE.md")
        print("   🧪 test_aws_credentials.py")
        print()
        print("📝 PROCHAINES ÉTAPES:")
        print("1. Obtenez vos credentials AWS")
        print("2. Modifiez les fichiers avec vos vraies clés")
        print("3. Exécutez: python test_aws_credentials.py")
        print("4. Si OK: python upload_local_models_to_s3.py")
        print()
        print("🌊 Prêt pour l'upload Harmonic AI sur AWS S3!")
    else:
        print("❌ Erreur lors de la préparation")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
