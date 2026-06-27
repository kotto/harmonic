#!/usr/bin/env python3
"""
Script pour créer une instance EC2 complète pour Connective AI avec pleine puissance harmonique
"""

import boto3
import json
import time
from datetime import datetime

def create_complete_instance():
    """Créer une instance EC2 complète pour Connective AI"""
    
    # Configuration
    ec2 = boto3.client('ec2', region_name='us-east-1')
    
    # Configuration de l'instance complète
    instance_config = {
        'ImageId': 'ami-0c02fb55956c7d316',  # Amazon Linux 2
        'InstanceType': 'm5.4xlarge',  # 16 vCPUs, 64GB RAM
        'KeyName': 'deepseek_ec2_key',
        'SecurityGroupIds': ['sg-connective-ai'],  # Utiliser security group existant
        'MinCount': 1,
        'MaxCount': 1,
        'UserData': '''#!/bin/bash
# Script d'initialisation pour Connective AI Complete

echo "=== Démarrage installation Connective AI Complete ==="

# Mise à jour système
yum update -y

# Installation Python 3.9 et dépendances
yum install python3.9 python3.9-pip python3.9-devel git wget htop -y

# Création environnement virtuel
python3.9 -m venv /home/ec2-user/connective_complete
chown -R ec2-user:ec2-user /home/ec2-user/connective_complete

# Configuration bashrc pour l'utilisateur
echo 'source /home/ec2-user/connective_complete/bin/activate' >> /home/ec2-user/.bashrc
echo 'export PYTHONPATH=/home/ec2-user/connective_complete/lib/python3.9/site-packages' >> /home/ec2-user/.bashrc

# Création répertoire de travail
mkdir -p /home/ec2-user/connective-ai-complete
chown ec2-user:ec2-user /home/ec2-user/connective-ai-complete

# Installation dépendances système
yum install -y gcc gcc-c++ make

echo "=== Installation système terminée ==="
''',
        'TagSpecifications': [{
            'ResourceType': 'instance',
            'Tags': [
                {'Key': 'Name', 'Value': 'Connective-AI-Complete'},
                {'Key': 'Project', 'Value': 'Connective-AI'},
                {'Key': 'Type', 'Value': 'Production-Complete'},
                {'Key': 'Created', 'Value': datetime.now().isoformat()}
            ]
        }],
        'BlockDeviceMappings': [
            {
                'DeviceName': '/dev/xvda',
                'Ebs': {
                    'VolumeSize': 500,  # 500GB SSD
                    'VolumeType': 'gp3',
                    'DeleteOnTermination': True,
                    'Throughput': 125,
                    'Iops': 3000
                }
            }
        ]
    }
    
    try:
        print("🚀 Création de l'instance EC2 complète...")
        response = ec2.run_instances(**instance_config)
        
        instance_id = response['Instances'][0]['InstanceId']
        print(f"✅ Instance créée avec ID: {instance_id}")
        
        # Attendre que l'instance soit en cours d'exécution
        print("⏳ Attente démarrage de l'instance...")
        
        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        
        # Récupérer les informations de l'instance
        instance_info = ec2.describe_instances(InstanceIds=[instance_id])
        instance = instance_info['Reservations'][0]['Instances'][0]
        
        public_ip = instance.get('PublicIpAddress', 'En attente')
        private_ip = instance.get('PrivateIpAddress', 'En attente')
        
        print(f"🌐 IP Publique: {public_ip}")
        print(f"🔗 IP Privée: {private_ip}")
        print(f"📍 Région: us-east-1")
        print(f"💾 Type: m5.4xlarge (16 vCPUs, 64GB RAM)")
        print(f"💽 Stockage: 500GB SSD")
        
        # Sauvegarder la configuration
        config = {
            'instance_id': instance_id,
            'public_ip': public_ip,
            'private_ip': private_ip,
            'instance_type': 'm5.4xlarge',
            'created_at': datetime.now().isoformat(),
            'status': 'running'
        }
        
        with open('/tmp/connective_ai_complete_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Configuration sauvegardée")
        
        return config
        
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        return None

def get_vpc_id(ec2):
    """Récupérer le VPC par défaut"""
    try:
        response = ec2.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
        if response['Vpcs']:
            return response['Vpcs'][0]['VpcId']
    except:
        pass
    
    # Si pas de VPC par défaut, prendre le premier
    response = ec2.describe_vpcs()
    if response['Vpcs']:
        return response['Vpcs'][0]['VpcId']
    
    return None

def create_security_group_if_needed(ec2, vpc_id):
    """Créer le security group s'il n'existe pas"""
    try:
        # Vérifier si le security group existe
        response = ec2.describe_security_groups(
            Filters=[{'Name': 'group-name', 'Values': ['sg-connective-ai']}]
        )
        
        if response['SecurityGroups']:
            sg_id = response['SecurityGroups'][0]['GroupId']
            print(f"✅ Security group existant: {sg_id}")
            return sg_id
        
    except:
        pass
    
    # Créer le security group
    try:
        response = ec2.create_security_group(
            GroupName='sg-connective-ai',
            Description='Security group for Connective AI Complete',
            VpcId=vpc_id
        )
        
        sg_id = response['GroupId']
        print(f"✅ Security group créé: {sg_id}")
        
        # Ajouter les règles
        # HTTP (port 80)
        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[{
                'IpProtocol': 'tcp',
                'FromPort': 80,
                'ToPort': 80,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }]
        )
        
        # HTTPS (port 443)
        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[{
                'IpProtocol': 'tcp',
                'FromPort': 443,
                'ToPort': 443,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }]
        )
        
        # API (port 8000)
        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[{
                'IpProtocol': 'tcp',
                'FromPort': 8000,
                'ToPort': 8000,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }]
        )
        
        # SSH (port 22)
        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[{
                'IpProtocol': 'tcp',
                'FromPort': 22,
                'ToPort': 22,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }]
        )
        
        print("✅ Règles de sécurité configurées")
        return sg_id
        
    except Exception as e:
        print(f"❌ Erreur création security group: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Démarrage création instance Connective AI Complete")
    print("=" * 60)
    
    # Initialisation client EC2
    ec2 = boto3.client('ec2', region_name='us-east-1')
    
    # Vérifier VPC
    vpc_id = get_vpc_id(ec2)
    if not vpc_id:
        print("❌ Impossible de trouver un VPC")
        exit(1)
    
    print(f"✅ VPC utilisé: {vpc_id}")
    
    # Créer/ vérifier security group
    sg_id = create_security_group_if_needed(ec2, vpc_id)
    if not sg_id:
        print("❌ Impossible de créer le security group")
        exit(1)
    
    # Créer l'instance
    result = create_complete_instance()
    
    if result:
        print("\n🎉 Instance Connective AI Complete créée avec succès!")
        print(f"🌐 IP: {result['public_ip']}")
        print(f"🆔 ID: {result['instance_id']}")
        print("\n📋 Prochaines étapes:")
        print("1. Attendre 2-3 minutes pour l'initialisation")
        print("2. Se connecter via SSH")
        print("3. Lancer l'installation complète")
        print("4. Déployer l'API complète")
        
        # Commandes de connexion
        print(f"\n🔑 Commande SSH:")
        print(f"ssh -i \"C:\\Users\\maatc\\.ssh\\deepseek_ec2\" ec2-user@{result['public_ip']}")
        
    else:
        print("❌ Échec de la création de l'instance")
