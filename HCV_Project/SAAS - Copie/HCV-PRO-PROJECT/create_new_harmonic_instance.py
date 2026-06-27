#!/usr/bin/env python3
# 🚀 Création Nouvelle Instance - DeepSeek V4-Pro Harmonic

import boto3
import json
import time

def create_harmonic_instance():
    """Crée une nouvelle instance EC2 pour DeepSeek V4-Pro Harmonic"""
    
    print("🚀 CRÉATION NOUVELLE INSTANCE - DeepSeek V4-Pro Harmonic")
    print("=" * 60)
    
    # Initialiser le client EC2
    ec2 = boto3.client('ec2', region_name='us-east-1')
    
    # Script user data complet
    user_data = '''#!/bin/bash
# 🚀 Installation DeepSeek V4-Pro Harmonic - V2

echo "🚀 DÉBUT INSTALLATION - DeepSeek V4-Pro Harmonic"

# Mise à jour système
echo "📦 Mise à jour du système..."
sudo apt update && sudo apt upgrade -y

# Installation Python et dépendances
echo "🐍 Installation de Python et dépendances..."
sudo apt install -y python3 python3-pip python3-venv nginx

# Créer utilisateur connective-ai
echo "👤 Création de l'utilisateur connective-ai..."
if ! id "connective-ai" &>/dev/null; then
    sudo useradd -m -s /bin/bash connective-ai
    sudo usermod -aG sudo connective-ai
fi

# Créer répertoires
echo "📁 Création des répertoires..."
sudo mkdir -p /opt/connective-ai
sudo mkdir -p /var/log/connective-ai
sudo chown -R connective-ai:connective-ai /opt/connective-ai
sudo chown -R connective-ai:connective-ai /var/log/connective-ai

# Télécharger application
echo "📥 Téléchargement de l'application..."
cd /opt/connective-ai
sudo -u connective-ai aws s3 cp s3://connective-ai-deployment/deepseek/DEEPSEEK_V4_HARMONIC_PORT_8000.py .

# Installer dépendances Python
echo "📦 Installation des dépendances Python..."
sudo -u connective-ai python3 -m venv venv
sudo -u connective-ai /opt/connective-ai/venv/bin/pip install fastapi uvicorn

# Créer service systemd
echo "🔧 Création du service systemd..."
sudo tee /etc/systemd/system/connective-ai-boost.service > /dev/null << 'EOS'
[Unit]
Description=Connective AI DeepSeek V4-Pro Harmonic Service
After=network.target

[Service]
Type=simple
User=connective-ai
WorkingDirectory=/opt/connective-ai
Environment=PATH=/opt/connective-ai/venv/bin
ExecStart=/opt/connective-ai/venv/bin/uvicorn DEEPSEEK_V4_HARMONIC_PORT_8000:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOS

# Configurer Nginx
echo "🌐 Configuration de Nginx..."
sudo tee /etc/nginx/sites-available/connective-ai > /dev/null << 'EON'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EON

sudo ln -sf /etc/nginx/sites-available/connective-ai /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t

# Démarrer services
echo "🚀 Démarrage des services..."
sudo systemctl daemon-reload
sudo systemctl enable connective-ai-boost
sudo systemctl start connective-ai-boost
sudo systemctl restart nginx

# Validation
echo "⏳ Attente du démarrage des services..."
sleep 15

echo "🔍 Validation des endpoints..."
curl -s http://localhost:8000/health > /tmp/health_check.txt
curl -s http://localhost:8000/lm_arena_score > /tmp/score_check.txt
curl -s http://localhost:8000/deepseek_harmonic_status > /tmp/status_check.txt

echo "✅ Installation terminée!"
echo "🌐 Application disponible sur: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"
'''
    
    try:
        # Créer l'instance
        print("🔧 Création de l'instance EC2...")
        response = ec2.run_instances(
            ImageId='ami-0c02fb55956c7d316',  # Ubuntu 20.04 LTS
            InstanceType='t3.medium',
            MinCount=1,
            MaxCount=1,
            KeyName='deep',
            SecurityGroupIds=['sg-03c0aca646500c5a1'],
            UserData=user_data,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {'Key': 'Name', 'Value': 'DeepSeek-Harmonic-V2'},
                        {'Key': 'Project', 'Value': 'Connective-AI'},
                        {'Key': 'Version', 'Value': 'v4-pro-harmonic'},
                        {'Key': 'Environment', 'Value': 'production'}
                    ]
                }
            ]
        )
        
        instance_id = response['Instances'][0]['InstanceId']
        print(f"✅ Instance créée: {instance_id}")
        
        # Attendre que l'instance soit running
        print("⏳ Attente du démarrage de l'instance...")
        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        
        # Obtenir les détails de l'instance
        instance_info = ec2.describe_instances(InstanceIds=[instance_id])
        instance = instance_info['Reservations'][0]['Instances'][0]
        public_ip = instance.get('PublicIpAddress', 'En attente...')
        private_ip = instance.get('PrivateIpAddress', 'En attente...')
        
        print(f"\n📊 DÉTAILS DE L'INSTANCE:")
        print(f"🆕 Instance ID: {instance_id}")
        print(f"🌐 IP Publique: {public_ip}")
        print(f"🔧 IP Privée: {private_ip}")
        print(f"📋 Type: t3.medium")
        print(f"🔌 Ports: 22, 80, 443, 8000")
        
        # Attendre un peu pour l'initialisation
        print("\n⏳ Attente de l'initialisation (30 secondes)...")
        time.sleep(30)
        
        # Instructions de validation
        print(f"\n🎯 VALIDATION RECOMMANDÉE:")
        print(f"📋 Attendre 2-3 minutes puis tester:")
        print(f"🏥 Health: curl -s http://{public_ip}:8000/health")
        print(f"🏆 Score: curl -s http://{public_ip}:8000/lm_arena_score")
        print(f"🚀 Status: curl -s http://{public_ip}:8000/deepseek_harmonic_status")
        print(f"📚 Documentation: http://{public_ip}:8000/docs")
        
        print(f"\n🌊 URLS FINALES:")
        print(f"🌐 Application: http://{public_ip}:8000")
        print(f"📚 Documentation: http://{public_ip}:8000/docs")
        print(f"🏥 Health: http://{public_ip}:8000/health")
        print(f"🏆 LM Arena: http://{public_ip}:8000/lm_arena_score")
        
        return instance_id, public_ip
        
    except Exception as e:
        print(f"❌ Erreur lors de la création: {str(e)}")
        return None, None

def check_instance_status(instance_id):
    """Vérifie le statut de l'instance"""
    ec2 = boto3.client('ec2', region_name='us-east-1')
    
    try:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        
        state = instance['State']['Name']
        public_ip = instance.get('PublicIpAddress', 'N/A')
        
        print(f"📊 Statut: {state}")
        print(f"🌐 IP: {public_ip}")
        
        return state, public_ip
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return None, None

if __name__ == "__main__":
    print("🚀 DÉMARRAGE DE LA CRÉATION D'INSTANCE")
    print("=" * 50)
    
    # Créer l'instance
    instance_id, public_ip = create_harmonic_instance()
    
    if instance_id:
        print(f"\n✅ Instance créée avec succès!")
        print(f"🆕 ID: {instance_id}")
        print(f"🌐 IP: {public_ip}")
        
        # Vérifier le statut après quelques minutes
        print(f"\n⏳ Vérification du statut dans 2 minutes...")
        time.sleep(120)
        
        state, ip = check_instance_status(instance_id)
        if state == 'running':
            print(f"🎯 Instance prête pour validation!")
            print(f"🌐 Tester: http://{ip}:8000/health")
        else:
            print(f"⏳ Instance encore en démarrage...")
    else:
        print(f"❌ Échec de la création de l'instance")
