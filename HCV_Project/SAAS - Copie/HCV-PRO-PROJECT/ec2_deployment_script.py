#!/usr/bin/env python3
"""
DÉPLOIEMENT EC2 POUR DEEPSEEK-V4-PRO RÉEL
======================================

Script pour provisionner l'instance EC2 ml.m5.2xlarge
et configurer l'environnement Deepseek-V4-Pro
"""

import boto3
import json
import time
from datetime import datetime

class EC2DeepseekDeployment:
    """Déploiement EC2 pour Deepseek-V4-Pro réel"""
    
    def __init__(self):
        self.ec2_client = boto3.client('ec2', region_name='eu-west-3')
        self.ssm_client = boto3.client('ssm', region_name='eu-west-3')
        
        print("🚀 DÉPLOIEMENT EC2 POUR DEEPSEEK-V4-PRO RÉEL")
        print("=" * 80)
        print("🖥️ INSTANCE: ml.m5.2xlarge (32GB RAM)")
        print("🤖 MODÈLE: Deepseek-V4-Pro (1.73GB)")
        print("🌊 INNOVATION: Couche harmonique déterministe")
        print("=" * 80)
    
    def create_security_group(self):
        """
        Créer le security group pour l'instance EC2
        """
        print("\n🔒 CRÉATION SECURITY GROUP")
        print("=" * 50)
        
        try:
            # Créer security group
            sg_response = self.ec2_client.create_security_group(
                GroupName='deepseek-ec2-sg',
                Description='Security group for Deepseek-V4-Pro EC2 instance',
                VpcId='vpc-xxxxxxxx'  # À adapter avec votre VPC
            )
            
            sg_id = sg_response['GroupId']
            print(f"✅ Security Group créé: {sg_id}")
            
            # Autoriser les ports nécessaires
            # Port 22 (SSH)
            self.ec2_client.authorize_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            )
            
            # Port 80 (HTTP)
            self.ec2_client.authorize_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 80,
                        'ToPort': 80,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            )
            
            # Port 443 (HTTPS)
            self.ec2_client.authorize_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 443,
                        'ToPort': 443,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            )
            
            print("✅ Ports autorisés: 22 (SSH), 80 (HTTP), 443 (HTTPS)")
            
            return sg_id
            
        except Exception as e:
            print(f"❌ Erreur création security group: {e}")
            return None
    
    def create_iam_role(self):
        """
        Créer le rôle IAM pour l'instance EC2
        """
        print("\n🔐 CRÉATION RÔLE IAM")
        print("=" * 50)
        
        try:
            # Créer le rôle IAM
            assume_role_policy_document = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "ec2.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            
            role_response = self.iam_client.create_role(
                RoleName='deepseek-ec2-role',
                AssumeRolePolicyDocument=json.dumps(assume_role_policy_document),
                Description='IAM role for Deepseek-V4-Pro EC2 instance'
            )
            
            role_arn = role_response['Role']['Arn']
            print(f"✅ Rôle IAM créé: {role_arn}")
            
            # Attacher la politique S3
            self.iam_client.attach_role_policy(
                RoleName='deepseek-ec2-role',
                PolicyArn='arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess'
            )
            
            # Attacher la politique CloudWatch
            self.iam_client.attach_role_policy(
                RoleName='deepseek-ec2-role',
                PolicyArn='arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy'
            )
            
            print("✅ Politiques attachées: S3 ReadOnly, CloudWatch Agent")
            
            # Créer l'instance profile
            self.iam_client.create_instance_profile(
                InstanceProfileName='deepseek-ec2-instance-profile'
            )
            
            # Ajouter le rôle à l'instance profile
            time.sleep(10)  # Attendre que le rôle soit créé
            
            self.iam_client.add_role_to_instance_profile(
                InstanceProfileName='deepseek-ec2-instance-profile',
                RoleName='deepseek-ec2-role'
            )
            
            print("✅ Instance profile créé")
            
            return 'deepseek-ec2-instance-profile'
            
        except Exception as e:
            print(f"❌ Erreur création rôle IAM: {e}")
            return None
    
    def launch_ec2_instance(self, security_group_id, instance_profile_name):
        """
        Lancer l'instance EC2 ml.m5.2xlarge
        """
        print("\n🚀 LANCEMENT INSTANCE EC2")
        print("=" * 50)
        
        try:
            # User data pour configuration automatique
            user_data = '''#!/bin/bash
# Configuration initiale de l'instance
yum update -y
yum install -y python3 python3-pip git

# Créer l'environnement virtuel
python3 -m venv /home/ec2-user/deepseek_env
chown -R ec2-user:ec2-user /home/ec2-user/deepseek_env

# Installer les dépendances de base
/home/ec2-user/deepseek_env/bin/pip install --upgrade pip

# Créer le répertoire de travail
mkdir -p /home/ec2-user/deepseek-v4-pro
chown ec2-user:ec2-user /home/ec2-user/deepseek-v4-pro

# Installer AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

echo "✅ Configuration initiale terminée"
'''
            
            # Lancer l'instance
            instance_response = self.ec2_client.run_instances(
                ImageId='ami-0c02fb55956c7d316',  # Amazon Linux 2
                InstanceType='ml.m5.2xlarge',
                MinCount=1,
                MaxCount=1,
                SecurityGroupIds=[security_group_id],
                IamInstanceProfile={
                    'Name': instance_profile_name
                },
                UserData=user_data,
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {
                                'Key': 'Name',
                                'Value': 'deepseek-v4-pro-instance'
                            },
                            {
                                'Key': 'Project',
                                'Value': 'Connective-AI'
                            },
                            {
                                'Key': 'Environment',
                                'Value': 'production'
                            }
                        ]
                    }
                ],
                BlockDeviceMappings=[
                    {
                        'DeviceName': '/dev/xvda',
                        'Ebs': {
                            'VolumeSize': 100,  # 100GB EBS
                            'VolumeType': 'gp3',
                            'DeleteOnTermination': True
                        }
                    }
                ]
            )
            
            instance_id = instance_response['Instances'][0]['InstanceId']
            print(f"✅ Instance lancée: {instance_id}")
            
            # Attendre que l'instance soit en cours d'exécution
            print("⏳ Attente démarrage instance...")
            
            waiter = self.ec2_client.get_waiter('instance_running')
            waiter.wait(
                InstanceIds=[instance_id],
                WaiterConfig={
                    'Delay': 15,
                    'MaxAttempts': 40
                }
            )
            
            print("✅ Instance en cours d'exécution!")
            
            # Obtenir l'adresse IP publique
            instance_details = self.ec2_client.describe_instances(
                InstanceIds=[instance_id]
            )
            
            public_ip = instance_details['Reservations'][0]['Instances'][0]['PublicIpAddress']
            print(f"🌐 Adresse IP publique: {public_ip}")
            
            return {
                'instance_id': instance_id,
                'public_ip': public_ip,
                'status': 'running'
            }
            
        except Exception as e:
            print(f"❌ Erreur lancement instance: {e}")
            return None
    
    def setup_deepseek_environment(self, public_ip):
        """
        Configuration de l'environnement Deepseek sur l'instance
        """
        print("\n🔧 CONFIGURATION ENVIRONNEMENT DEEPSEEK")
        print("=" * 50)
        
        setup_commands = [
            "# Se connecter à l'instance",
            f"ssh -i votre-clé.pem ec2-user@{public_ip}",
            "",
            "# Activer l'environnement virtuel",
            "source /home/ec2-user/deepseek_env/bin/activate",
            "",
            "# Installer les dépendances Deepseek",
            "cd /home/ec2-user/deepseek-v4-pro",
            "pip install torch>=2.0.0 transformers>=4.30.0 accelerate>=0.20.0",
            "pip install bitsandbytes>=0.39.0 boto3>=1.26.0 numpy>=1.24.0",
            "pip install fastapi>=0.100.0 uvicorn>=0.22.0",
            "",
            "# Cloner le projet",
            "git clone <votre-repo> .",
            "",
            "# Télécharger la configuration Deepseek",
            "aws s3 cp s3://deepseek-models-326095712935/deepseek-v4-pro/config.json .",
            "",
            "# Tester l'environnement",
            "python -c 'import torch; print(f\"PyTorch: {torch.__version__}\")'",
            "python -c 'import transformers; print(f\"Transformers: {transformers.__version__}\")'",
        ]
        
        print("📋 COMMANDES DE CONFIGURATION:")
        for cmd in setup_commands:
            print(f"   {cmd}")
        
        print(f"\n🌐 CONNEXION SSH:")
        print(f"   ssh -i votre-clé.pem ec2-user@{public_ip}")
        
        return setup_commands
    
    def generate_deployment_summary(self, instance_info):
        """
        Générer le résumé de déploiement
        """
        print("\n📊 RÉSUMÉ DÉPLOIEMENT")
        print("=" * 80)
        
        deployment_summary = {
            "timestamp": datetime.now().isoformat(),
            "deployment_type": "EC2 Deepseek-V4-Pro Real",
            "instance": {
                "type": "ml.m5.2xlarge",
                "id": instance_info['instance_id'],
                "public_ip": instance_info['public_ip'],
                "status": instance_info['status'],
                "specs": {
                    "vcpu": 8,
                    "memory": "32 GiB",
                    "storage": "100 GB EBS",
                    "cost_per_hour": 0.408,
                    "cost_per_month": 294
                }
            },
            "deepseek_config": {
                "model": "Deepseek-V4-Pro",
                "size": "1.73 GB",
                "experts": 384,
                "layers": 61,
                "hidden_size": 7168,
                "quantization": "FP8"
            },
            "next_steps": [
                "1. Se connecter via SSH à l'instance",
                "2. Installer les dépendances Python",
                "3. Implémenter le model loader",
                "4. Tester le chargement du modèle",
                "5. Implémenter l'API FastAPI",
                "6. Configurer API Gateway"
            ],
            "estimated_timeline": {
                "environment_setup": "2-3 heures",
                "model_loader_implementation": "1-2 jours",
                "api_development": "1 jour",
                "testing_optimization": "1 jour",
                "total": "3-4 jours"
            },
            "success_criteria": [
                "✅ Instance EC2 opérationnelle",
                "✅ Environnement Python configuré",
                "✅ Modèle Deepseek-V4-Pro chargé",
                "✅ API FastAPI fonctionnelle",
                "✅ Performance <5s par requête"
            ]
        }
        
        # Sauvegarder le résumé
        with open("EC2_DEPLOYMENT_SUMMARY.json", 'w', encoding='utf-8') as f:
            json.dump(deployment_summary, f, indent=2, ensure_ascii=False)
        
        return deployment_summary
    
    def deploy_complete_infrastructure(self):
        """
        Déployer l'infrastructure complète
        """
        print("🚀 DÉPLOIEMENT INFRASTRUCTURE COMPLÈTE")
        print("=" * 80)
        
        # Étape 1: Créer security group
        sg_id = self.create_security_group()
        if not sg_id:
            print("❌ Échec création security group")
            return None
        
        # Étape 2: Créer rôle IAM
        instance_profile = self.create_iam_role()
        if not instance_profile:
            print("❌ Échec création rôle IAM")
            return None
        
        # Étape 3: Lancer instance EC2
        instance_info = self.launch_ec2_instance(sg_id, instance_profile)
        if not instance_info:
            print("❌ Échec lancement instance")
            return None
        
        # Étape 4: Configuration environnement
        setup_commands = self.setup_deepseek_environment(instance_info['public_ip'])
        
        # Étape 5: Résumé déploiement
        summary = self.generate_deployment_summary(instance_info)
        
        return {
            'security_group_id': sg_id,
            'instance_profile': instance_profile,
            'instance_info': instance_info,
            'setup_commands': setup_commands,
            'summary': summary
        }

def main():
    """
    Fonction principale
    """
    print("🚀 DÉPLOIEMENT EC2 POUR DEEPSEEK-V4-PRO RÉEL!")
    print("=" * 80)
    print("🖥️ INSTANCE: ml.m5.2xlarge (32GB RAM)")
    print("🤖 MODÈLE: Deepseek-V4-Pro (1.73GB)")
    print("🌊 INNOVATION: Couche harmonique déterministe")
    print("=" * 80)
    
    # Créer et exécuter le déploiement
    deployment = EC2DeepseekDeployment()
    result = deployment.deploy_complete_infrastructure()
    
    if result:
        print("\n🎉 DÉPLOIEMENT RÉUSSI!")
        print(f"🌐 IP Instance: {result['instance_info']['public_ip']}")
        print(f"🔧 Instance ID: {result['instance_info']['instance_id']}")
        print("\n📋 PROCHAINES ÉTAPES:")
        print("1. Se connecter via SSH")
        print("2. Configurer l'environnement Python")
        print("3. Implémenter le model loader")
        print("4. Tester Deepseek-V4-Pro réel")
    else:
        print("\n❌ ÉCHEC DÉPLOIEMENT")
        print("Vérifier les permissions AWS et la configuration")

if __name__ == "__main__":
    main()
