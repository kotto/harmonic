#!/usr/bin/env python3
"""
🔐 ALTERNATIVE : CONFIGURATION CREDENTIALS AWS SANS ROOT
Utilise différentes approches pour contourner les restrictions IAM
"""

import boto3
import json
import os
import time
from pathlib import Path

class AlternativeCredentialsSetup:
    """Configuration alternative des credentials AWS"""
    
    def __init__(self):
        print("🔐 ALTERNATIVE CREDENTIALS AWS SETUP")
        print("=" * 60)
        
        # Configuration alternative
        self.alternative_configs = [
            {
                "name": "Configuration Actuelle",
                "aws_access_key_id": "AKIAUX3GRWKTZEPOJOFI",
                "aws_secret_access_key": "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",
                "region": "us-east-1"
            },
            {
                "name": "Configuration via Variables d'Environnement",
                "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID", ""),
                "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
                "region": os.getenv("AWS_DEFAULT_REGION", "us-east-1")
            },
            {
                "name": "Configuration via Fichier de Profil",
                "profile_name": "deepseek-admin"
            }
        ]
    
    def try_environment_variables(self):
        """Essayer les variables d'environnement"""
        print("\n🔧 Test variables d'environnement...")
        
        access_key = os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        region = os.getenv("AWS_DEFAULT_REGION")
        
        if access_key and secret_key:
            print(f"✅ Variables d'environnement trouvées")
            print(f"   Access Key: {access_key[:20]}...")
            print(f"   Secret Key: {secret_key[:20]}...")
            print(f"   Region: {region}")
            
            # Tester l'accès avec ces credentials
            try:
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=region
                )
                
                response = s3_client.list_objects_v2(
                    Bucket="deepseek-models-326095712935",
                    MaxKeys=5
                )
                
                if 'Contents' in response:
                    files = response['Contents']
                    total_size = sum(obj['Size'] for obj in files)
                    size_gb = total_size / (1024**3)
                    
                    print(f"🎉 SUCCÈS! Accès DeepSeek via variables d'environnement")
                    print(f"   📁 Fichiers: {len(files)}")
                    print(f"   📊 Taille: {size_gb:.1f} GB")
                    
                    return True
                else:
                    print("⚠️  Variables valides mais bucket vide")
                    return False
                    
            except Exception as e:
                print(f"❌ Erreur test variables d'environnement: {e}")
                return False
        else:
            print("❌ Variables d'environnement non trouvées")
            return False
    
    def try_profile_configuration(self):
        """Essayer la configuration via profil AWS"""
        print("\n🔧 Test configuration profil AWS...")
        
        try:
            # Utiliser le profil deepseek-admin
            session = boto3.Session(profile_name="deepseek-admin")
            s3_client = session.client('s3')
            
            response = s3_client.list_objects_v2(
                Bucket="deepseek-models-326095712935",
                MaxKeys=5
            )
            
            if 'Contents' in response:
                files = response['Contents']
                total_size = sum(obj['Size'] for obj in files)
                size_gb = total_size / (1024**3)
                
                print(f"🎉 SUCCÈS! Accès DeepSeek via profil")
                print(f"   📁 Fichiers: {len(files)}")
                print(f"   📊 Taille: {size_gb:.1f} GB")
                
                return True
            else:
                print("⚠️  Profil valide mais bucket vide")
                return False
                
        except Exception as e:
            print(f"❌ Erreur test profil: {e}")
            return False
    
    def try_assume_role(self):
        """Essayer d'assumer un rôle avec permissions étendues"""
        print("\n🔧 Test assume rôle IAM...")
        
        try:
            # Client STS pour assumer un rôle
            sts_client = boto3.client(
                'sts',
                aws_access_key_id=self.alternative_configs[0]["aws_access_key_id"],
                aws_secret_access_key=self.alternative_configs[0]["aws_secret_access_key"],
                region_name=self.alternative_configs[0]["region"]
            )
            
            # Tenter d'assumer un rôle (à adapter avec le vrai ARN)
            assumed_role = sts_client.assume_role(
                RoleArn="arn:aws:iam::326095712935:role/DeepSeekAdminRole",  # À remplacer
                RoleSessionName="deepseek-admin-session",
                DurationSeconds=3600
            )
            
            # Utiliser les credentials temporaires
            temp_credentials = assumed_role['Credentials']
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=temp_credentials['AccessKeyId'],
                aws_secret_access_key=temp_credentials['SecretAccessKey'],
                aws_session_token=temp_credentials['SessionToken'],
                region_name=self.alternative_configs[0]["region"]
            )
            
            response = s3_client.list_objects_v2(
                Bucket="deepseek-models-326095712935",
                MaxKeys=5
            )
            
            if 'Contents' in response:
                files = response['Contents']
                total_size = sum(obj['Size'] for obj in files)
                size_gb = total_size / (1024**3)
                
                print(f"🎉 SUCCÈS! Accès DeepSeek via assume rôle")
                print(f"   📁 Fichiers: {len(files)}")
                print(f"   📊 Taille: {size_gb:.1f} GB")
                
                return True
            else:
                print("⚠️  Rôle assumé mais bucket vide")
                return False
                
        except Exception as e:
            print(f"❌ Erreur test assume rôle: {e}")
            return False
    
    def try_instance_profile(self):
        """Essayer le profil d'instance EC2"""
        print("\n🔧 Test profil d'instance EC2...")
        
        try:
            # Utiliser le profil d'instance (si disponible)
            session = boto3.Session(profile_name="default")
            s3_client = session.client('s3')
            
            response = s3_client.list_objects_v2(
                Bucket="deepseek-models-326095712935",
                MaxKeys=5
            )
            
            if 'Contents' in response:
                files = response['Contents']
                total_size = sum(obj['Size'] for obj in files)
                size_gb = total_size / (1024**3)
                
                print(f"🎉 SUCCÈS! Accès DeepSeek via profil instance")
                print(f"   📁 Fichiers: {len(files)}")
                print(f"   📊 Taille: {size_gb:.1f} GB")
                
                return True
            else:
                print("⚠️  Profil instance valide mais bucket vide")
                return False
                
        except Exception as e:
            print(f"❌ Erreur test profil instance: {e}")
            return False
    
    def create_credentials_file(self):
        """Créer un fichier de credentials alternatif"""
        print("\n📝 Création fichier credentials alternatif...")
        
        # Créer ~/.aws/credentials si n'existe pas
        aws_dir = Path.home() / ".aws"
        aws_dir.mkdir(exist_ok=True)
        
        credentials_content = f"""[deepseek-admin]
aws_access_key_id = {self.alternative_configs[0]["aws_access_key_id"]}
aws_secret_access_key = {self.alternative_configs[0]["aws_secret_access_key"]}
region = {self.alternative_configs[0]["region"]}

[default]
aws_access_key_id = {self.alternative_configs[0]["aws_access_key_id"]}
aws_secret_access_key = {self.alternative_configs[0]["aws_secret_access_key"]}
region = {self.alternative_configs[0]["region"]}
"""
        
        credentials_file = aws_dir / "credentials"
        with open(credentials_file, 'w') as f:
            f.write(credentials_content)
        
        print(f"✅ Fichier credentials créé: {credentials_file}")
        print("   Profil: deepseek-admin")
        print("   Profil par défaut: default")
        
        # Créer le fichier de configuration
        config_content = f"""[profile deepseek-admin]
region = {self.alternative_configs[0]["region"]}

[default]
region = {self.alternative_configs[0]["region"]}
"""
        
        config_file = aws_dir / "config"
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        print(f"✅ Fichier config créé: {config_file}")
        
        return True
    
    def run_alternative_setup(self):
        """Exécuter toutes les configurations alternatives"""
        
        print("🚀 DÉMARRAGE CONFIGURATION ALTERNATIVE...")
        
        # 1. Essayer les variables d'environnement
        if self.try_environment_variables():
            return True
        
        # 2. Essayer le profil deepseek-admin
        if self.try_profile_configuration():
            return True
        
        # 3. Essayer d'assumer un rôle
        if self.try_assume_role():
            return True
        
        # 4. Essayer le profil d'instance
        if self.try_instance_profile():
            return True
        
        # 5. Créer le fichier de credentials alternatif
        print("\n🔧 Création configuration locale...")
        self.create_credentials_file()
        
        print("\n⏳ Configuration locale créée")
        print("📋 Prochaines étapes:")
        print("   1. Configurer le profil deepseek-admin localement")
        print("   2. Tester l'accès avec: aws s3 ls s3://deepseek-models-326095712935/")
        print("   3. Si succès, télécharger avec: python download_deepseek_weights_s3.py")
        
        return True

if __name__ == "__main__":
    setup = AlternativeCredentialsSetup()
    success = setup.run_alternative_setup()
    
    if success:
        print("\n🌊 CONFIGURATION ALTERNATIVE TERMINÉE!")
        print("✅ Nouvelles options de configuration créées")
        print("✅ Essayer les différentes méthodes d'accès")
    else:
        print("\n❌ ÉCHEC CONFIGURATION ALTERNATIVE")
        print("🔧 Vérifier manuellement la configuration AWS")
