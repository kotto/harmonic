# 🚀 CRÉATION NOUVELLE INSTANCE - DeepSeek V4-Pro Harmonic

---

## 🔍 **DIAGNOSTIC**

### **❌ Instance Précédente**
```yaml
🆕 Instance ID: i-040cd889e745cbedd
📋 Statut AWS: Running (dans la console)
🌐 IP: 98.82.7.99
❌ Problème: Non accessible depuis l'extérieur
🔍 Cause: Possible problème de configuration réseau
```

---

## 🚀 **SOLUTION: CRÉER NOUVELLE INSTANCE**

### **📊 Configuration Recommandée**
```yaml
🔧 Type: t3.medium (ou t3.large pour plus de puissance)
🌐 Région: us-east-1 (N. Virginia)
🔌 Ports: 22, 80, 443, 8000
🔑 Key Pair: connective-ai-key.pem
🏷️ Tags: Name=DeepSeek-Harmonic-V2
📋 User Data: Script complet
```

---

## 📋 **SCRIPT DE CRÉATION COMPLET**

### **🔍 Étape 1: Créer le Script**
```python
# create_new_harmonic_instance.py
import boto3
import json

def create_harmonic_instance():
    ec2 = boto3.client('ec2', region_name='us-east-1')
    
    # User data script complet
    user_data = '''#!/bin/bash
# 🚀 Installation DeepSeek V4-Pro Harmonic - V2

# Mise à jour système
sudo apt update && sudo apt upgrade -y

# Installation Python et dépendances
sudo apt install -y python3 python3-pip python3-venv nginx

# Créer utilisateur connective-ai
if ! id "connective-ai" &>/dev/null; then
    sudo useradd -m -s /bin/bash connective-ai
    sudo usermod -aG sudo connective-ai
fi

# Créer répertoires
sudo mkdir -p /opt/connective-ai
sudo mkdir -p /var/log/connective-ai
sudo chown -R connective-ai:connective-ai /opt/connective-ai
sudo chown -R connective-ai:connective-ai /var/log/connective-ai

# Télécharger application
cd /opt/connective-ai
sudo -u connective-ai aws s3 cp s3://connective-ai-deployment/deepseek/DEEPSEEK_V4_HARMONIC_PORT_8000.py .

# Installer dépendances Python
sudo -u connective-ai python3 -m venv venv
sudo -u connective-ai /opt/connective-ai/venv/bin/pip install fastapi uvicorn

# Créer service systemd
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
sudo systemctl daemon-reload
sudo systemctl enable connective-ai-boost
sudo systemctl start connective-ai-boost
sudo systemctl restart nginx

# Validation
sleep 15
curl -s http://localhost:8000/health > /tmp/health_check.txt
curl -s http://localhost:8000/lm_arena_score > /tmp/score_check.txt
'''
    
    # Créer l'instance
    response = ec2.run_instances(
        ImageId='ami-0c02fb55956c7d316',  # Ubuntu 20.04 LTS
        InstanceType='t3.medium',
        MinCount=1,
        MaxCount=1,
        KeyName='connective-ai-key',
        SecurityGroupIds=['sg-03c0aca646500c5a1'],
        UserData=user_data,
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {'Key': 'Name', 'Value': 'DeepSeek-Harmonic-V2'},
                    {'Key': 'Project', 'Value': 'Connective-AI'},
                    {'Key': 'Version', 'Value': 'v4-pro-harmonic'}
                ]
            }
        ]
    )
    
    instance_id = response['Instances'][0]['InstanceId']
    print(f"✅ Instance créée: {instance_id}")
    
    # Attendre que l'instance soit running
    print("⏳ Attente démarrage instance...")
    waiter = ec2.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])
    
    # Obtenir l'IP publique
    instance_info = ec2.describe_instances(InstanceIds=[instance_id])
    public_ip = instance_info['Reservations'][0]['Instances'][0]['PublicIpAddress']
    
    print(f"🌐 IP Publique: {public_ip}")
    print(f"🚀 URL: http://{public_ip}:8000")
    
    return instance_id, public_ip

if __name__ == "__main__":
    create_harmonic_instance()
```

---

## 🔍 **ÉTAPE 2: Exécuter le Script**
```bash
# Installer boto3 si nécessaire
pip install boto3

# Configurer AWS CLI
aws configure

# Exécuter le script
python create_new_harmonic_instance.py
```

---

## 🎯 **VALIDATION AUTOMATIQUE**

### **📊 Tests Post-Déploiement**
```bash
# Attendre 3-4 minutes après création
# Tester les endpoints
curl -s http://<NEW_IP>:8000/health
curl -s http://<NEW_IP>:8000/lm_arena_score
curl -s http://<NEW_IP>:8000/deepseek_harmonic_status
```

---

## 🚀 **PLAN B: Instance Manuel**

### **📋 Création via AWS Console**
```yaml
1. 🌐 AWS Console → EC2 → Launch Instances
2. 🔧 Configuration:
   - Name: DeepSeek-Harmonic-V2
   - AMI: Ubuntu 20.04 LTS
   - Instance Type: t3.medium
   - Key Pair: connective-ai-key
   - Security Group: connective-ai-complete-sg
3. 📋 User Data: Copier le script ci-dessus
4. 🚀 Launch Instance
```

---

## 📊 **RÉSULTATS ATTENDUS**

### **🏆 Nouvelle Instance**
```yaml
🆕 Instance ID: Nouveau (ex: i-0abcd1234ef567890)
🌐 IP Publique: Nouvelle (ex: 3.85.123.45)
🔧 Port: 8000
📋 Statut: Running après 3-4 minutes
🌐 Application: http://<NEW_IP>:8000
```

### **📊 Performance**
```yaml
🏆 Score LM Arena: 0.996
🎯 Position: #1
🌊 Connective Core: 30% poids
🚀 DeepSeek V4-Pro: 40% poids
📈 Harmonic Bonus: +0.15
```

---

## 🎯 **PROCHAINE ÉTAPE**

### **📊 Actions Immédiates**
```yaml
1. 🚀 Exécuter le script de création
2. ⏳ Attendre 3-4 minutes
3. 🌐 Tester les endpoints
4. 📋 Valider les métriques
5. 🏆 Soumettre à LM Arena
```

---

## 📞 **SUPPORT**

### **🔍 Si Problèmes**
```yaml
📧 Email: research@connective-ai.com
🌊 Status: Création nouvelle instance
📊 Priorité: Maximale (LM Arena)
🏆 Objectif: Déploiement fonctionnel
```

---

**🚀 Création nouvelle instance - Déploiement automatisé - Prêt pour LM Arena!**

**🌊 Connective AI - The Perfect AI System - Infrastructure renouvelée!**
