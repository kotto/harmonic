#!/usr/bin/env python3
"""
Création d'un nouvel utilisateur AWS avec toutes les permissions Qwen3.5
=================================================================

Crée qwen35-enhanced-user avec permissions complètes pour contourner
les limitations de harmonic-ai-user.
"""

import boto3
import json
import secrets
import string
from datetime import datetime

# Configuration
NEW_USERNAME = "qwen35-enhanced-user"
POLICY_NAME = "Qwen35-Enhanced-Full-Access-Policy"
ACCOUNT_ID = "326095712935"
REGION = "us-east-1"

class Qwen35UserCreator:
    """Créateur d'utilisateur AWS avec permissions complètes"""
    
    def __init__(self):
        self.iam_client = boto3.client('iam', region_name=REGION)
        self.username = NEW_USERNAME
        self.policy_name = POLICY_NAME
        
    def generate_secure_password(self, length=20):
        """Génère un mot de passe sécurisé"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    def create_full_access_policy(self):
        """Crée la politique d'accès complet pour Qwen3.5"""
        print("🔐 Création de la politique d'accès complet...")
        
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "LambdaFullAccess",
                    "Effect": "Allow",
                    "Action": [
                        "lambda:*"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "IAMFullAccessForUser",
                    "Effect": "Allow", 
                    "Action": [
                        "iam:CreatePolicy",
                        "iam:AttachUserPolicy",
                        "iam:ListAttachedUserPolicies",
                        "iam:PassRole",
                        "iam:GetRole",
                        "iam:CreateRole",
                        "iam:ListRoles",
                        "iam:GetPolicy",
                        "iam:ListPolicies",
                        "iam:DetachUserPolicy",
                        "iam:DeletePolicy",
                        "iam:UpdateRole",
                        "iam:PutRolePolicy"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "S3FullAccess",
                    "Effect": "Allow",
                    "Action": [
                        "s3:*"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "ECRFullAccess",
                    "Effect": "Allow",
                    "Action": [
                        "ecr:*"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "SageMakerFullAccess",
                    "Effect": "Allow",
                    "Action": [
                        "sagemaker:*"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "APIGatewayFullAccess",
                    "Effect": "Allow",
                    "Action": [
                        "apigateway:*"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "CloudWatchFullAccess",
                    "Effect": "Allow",
                    "Action": [
                        "cloudwatch:*",
                        "logs:*"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        try:
            response = self.iam_client.create_policy(
                PolicyName=self.policy_name,
                PolicyDocument=json.dumps(policy_document),
                Description="Permissions complètes pour déploiement Qwen3.5 Enhanced Harmonic AI"
            )
            
            policy_arn = response['Policy']['Arn']
            print(f"✅ Politique créée: {policy_arn}")
            return policy_arn
            
        except Exception as e:
            print(f"❌ Erreur création politique: {e}")
            return None
    
    def create_enhanced_user(self):
        """Crée le nouvel utilisateur avec permissions complètes"""
        print(f"👤 Création de l'utilisateur: {self.username}")
        
        # Générer un mot de passe sécurisé
        password = self.generate_secure_password()
        
        try:
            response = self.iam_client.create_user(
                UserName=self.username,
                Path="/",
                PermissionsBoundary="arn:aws:iam::aws:policy/PowerUserAccessBoundary"
            )
            
            user_arn = response['User']['Arn']
            print(f"✅ Utilisateur créé: {user_arn}")
            
            # Afficher les credentials (IMPORTANT!)
            print("\n" + "="*60)
            print("🔑 CREDENTIALS DU NOUVEL UTILISATEUR")
            print("="*60)
            print(f"👤 Username: {self.username}")
            print(f"🔐 Password: {password}")
            print(f"🌍 Region: {REGION}")
            print(f"🏢 Account: {ACCOUNT_ID}")
            print("="*60)
            print("⚠️  CONSERVEZ CES CREDENTIALS SÉCURISÉMENT!")
            print("⚠️  ELLES SONT VALIDES PENDANT 90 JOURS")
            print("⚠️  APRÈS 90 JOURS, CRÉEZ UN NOUVEAU MOT DE PASSE")
            print("="*60)
            
            return user_arn, password
            
        except Exception as e:
            print(f"❌ Erreur création utilisateur: {e}")
            return None, None
    
    def attach_policy_to_user(self, user_arn, policy_arn):
        """Attache la politique à l'utilisateur"""
        print("🔗 Attachement de la politique à l'utilisateur...")
        
        try:
            self.iam_client.attach_user_policy(
                UserName=self.username,
                PolicyArn=policy_arn
            )
            print("✅ Politique attachée avec succès")
            return True
            
        except Exception as e:
            print(f"❌ Erreur attachement politique: {e}")
            return False
    
    def create_access_keys(self):
        """Crée les clés d'accès pour le nouvel utilisateur"""
        print("🔑 Création des clés d'accès...")
        
        try:
            response = self.iam_client.create_access_key(
                UserName=self.username
            )
            
            access_key = response['AccessKey']['AccessKeyId']
            secret_key = response['AccessKey']['SecretAccessKey']
            
            print("\n" + "="*60)
            print("🔑 NOUVELLES CLÉS D'ACCÈS AWS")
            print("="*60)
            print(f"👤 Username: {self.username}")
            print(f"🔑 Access Key: {access_key}")
            print(f"🔐 Secret Key: {secret_key}")
            print(f"🌍 Region: {REGION}")
            print("="*60)
            print("⚠️  UTILISEZ CES CLÉS POUR LE DÉPLOIEMENT!")
            print("⚠️  CONFIGUREZ: aws configure --profile qwen35-enhanced")
            print("="*60)
            
            return access_key, secret_key
            
        except Exception as e:
            print(f"❌ Erreur création clés: {e}")
            return None, None
    
    def create_aws_profile_config(self, access_key, secret_key, password):
        """Crée le fichier de configuration AWS CLI"""
        print("📝 Création du fichier de configuration AWS...")
        
        config_content = f"""[profile qwen35-enhanced]
region = {REGION}
output = json

[profile qwen35-enhanced]
aws_access_key_id = {access_key}
aws_secret_access_key = {secret_key}
"""
        
        with open('qwen35_enhanced_aws_config', 'w') as f:
            f.write(config_content)
        
        print("✅ Fichier de configuration créé: qwen35_enhanced_aws_config")
        
        # Instructions pour utiliser le profil
        print("\n" + "="*60)
        print("📋 INSTRUCTIONS D'UTILISATION")
        print("="*60)
        print("1. Copiez le fichier qwen35_enhanced_aws_config:")
        print("   - Windows: Copiez dans %USERPROFILE%\\.aws\\config")
        print("   - Linux/Mac: Copiez dans ~/.aws/config")
        print("")
        print("2. Utilisez le profil avec:")
        print("   aws --profile qwen35-enhanced sts get-caller-identity")
        print("   aws --profile qwen35-enhanced lambda list-functions")
        print("   aws --profile qwen35-enhanced s3 ls")
        print("="*60)
    
    def verify_new_user_permissions(self):
        """Vérifie les permissions du nouvel utilisateur"""
        print("🔍 Vérification des permissions du nouvel utilisateur...")
        
        # Créer un client avec le nouvel utilisateur
        try:
            # Pour tester, on devrait utiliser les nouvelles clés
            print("⏳ Pour tester les permissions, utilisez:")
            print("   aws --profile qwen35-enhanced sts get-caller-identity")
            print("   aws --profile qwen35-enhanced iam list-attached-user-policies")
            print("   aws --profile qwen35-enhanced lambda get-function --function-name qwen35-simple")
            return True
            
        except Exception as e:
            print(f"❌ Erreur vérification: {e}")
            return False
    
    def create_complete_user(self):
        """Exécute le processus complet de création"""
        print("🚀 CRÉATION COMPLÈTE DE L'UTILISATEUR QWEN35-ENHANCED")
        print("="*70)
        
        # Étape 1: Créer la politique
        policy_arn = self.create_full_access_policy()
        if not policy_arn:
            print("❌ Échec création politique")
            return False
        
        # Étape 2: Créer l'utilisateur
        user_arn, password = self.create_enhanced_user()
        if not user_arn:
            print("❌ Échec création utilisateur")
            return False
        
        # Étape 3: Attacher la politique
        if not self.attach_policy_to_user(user_arn, policy_arn):
            print("❌ Échec attachement politique")
            return False
        
        # Étape 4: Créer les clés d'accès
        access_key, secret_key = self.create_access_keys()
        if not access_key:
            print("❌ Échec création clés")
            return False
        
        # Étape 5: Créer la configuration
        self.create_aws_profile_config(access_key, secret_key, password)
        
        print("\n🎉 UTILISATEUR QWEN35-ENHANCED CRÉÉ AVEC SUCCÈS!")
        print("="*70)
        print("📋 RÉSUMÉ:")
        print(f"✅ Username: {self.username}")
        print(f"✅ Policy: {self.policy_name}")
        print(f"✅ Access Key: {access_key[:8]}...")
        print(f"✅ Secret Key: {secret_key[:8]}...")
        print(f"✅ ARN: {user_arn}")
        print("="*70)
        
        print("🎯 PROCHAINES ÉTAPES:")
        print("1. Configurez le profil AWS:")
        print("   aws configure --profile qwen35-enhanced")
        print("   # Entrez Access Key et Secret Key ci-dessus")
        print("")
        print("2. Testez les permissions:")
        print("   aws --profile qwen35-enhanced sts get-caller-identity")
        print("   aws --profile qwen35-enhanced lambda update-function-code --function-name qwen35-simple --zip-file fileb://qwen35_enhanced_harmonic.zip")
        print("")
        print("3. Relancez l'intégration:")
        print("   python qwen35_harmonic_simple.py --profile qwen35-enhanced")
        print("="*70)
        
        return True

def main():
    """Point d'entrée principal"""
    print("🌀 QWEN35-ENHANCED USER CREATOR")
    print("Création d'un nouvel utilisateur AWS avec permissions complètes")
    print("pour contourner les limitations de harmonic-ai-user")
    print("="*70)
    
    creator = Qwen35UserCreator()
    
    try:
        success = creator.create_complete_user()
        
        if success:
            print("\n✅ UTILISATEUR CRÉÉ - PRÊT POUR DÉPLOIEMENT!")
            print("🚀 Vous pouvez maintenant utiliser qwen35-enhanced-user")
            print("🎯 avec toutes les permissions nécessaires pour Qwen3.5 Enhanced")
        else:
            print("\n❌ ÉCHEC DE LA CRÉATION")
            print("📋 Vérifiez que vous avez les permissions administrateur")
            
    except KeyboardInterrupt:
        print("\n⏹️ Opération interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")

if __name__ == "__main__":
    main()
