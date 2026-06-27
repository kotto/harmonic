# 🔧 DÉPLOIEMENT MANUEL AWS - COMMANDES DIRECTES

## 📋 CONFIGURATION

```bash
# Variables
export INSTANCE_TYPE="m5.2xlarge"
export KEY_NAME="deep"
export SECURITY_GROUP_NAME="connective-ai-complete-sg"
export AMI_ID="ami-024b178b0225b27fc"
export REGION="us-east-1"
export TAG_NAME="Connective-AI-Complete-Evolutionary"
```

---

## 🔒 ÉTAPE 1: CRÉATION SECURITY GROUP

```bash
aws ec2 create-security-group \
    --group-name "$SECURITY_GROUP_NAME" \
    --description "Security group for Connective AI Complete Evolutionary" \
    --query "GroupId" \
    --output text \
    --region "$REGION"

# Note: Si le groupe existe déjà, récupérer son ID:
aws ec2 describe-security-groups \
    --group-names "$SECURITY_GROUP_NAME" \
    --query "SecurityGroups[0].GroupId" \
    --output text \
    --region "$REGION"
```

---

## 🌐 ÉTAPE 2: AUTORISATION PORTS

```bash
# Récupérer SG_ID depuis l'étape 1
export SG_ID="sg-xxxxxxxxx"

# Port 22 (SSH)
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0 \
    --region "$REGION"

# Port 8000 (API)
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp \
    --port 8000 \
    --cidr 0.0.0.0/0 \
    --region "$REGION"

# Port 80 (HTTP)
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 \
    --region "$REGION"
```

---

## 🚀 ÉTAPE 3: LANCEMENT INSTANCE

```bash
aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_NAME" \
    --security-group-ids "$SG_ID" \
    --user-data file://user_data_complete.sh \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$TAG_NAME}]" \
    --query "Instances[0].InstanceId" \
    --output text \
    --region "$REGION"

# Note: Créer user_data_complete.sh avec le contenu ci-dessous
```

---

## 📝 USER DATA COMPLET

```bash
# Créer le fichier user_data_complete.sh
cat > user_data_complete.sh << 'EOF'
#!/bin/bash
# User Data pour Connective AI Complete Evolutionary

echo "🚀 Initialisation Connective AI Complete Evolutionary"

# Mise à jour système
yum update -y
yum install -y python3 python3-pip git nginx

# Installation Python 3.9
yum install -y gcc openssl-devel bzip2-devel libffi-devel zlib-devel
cd /tmp
wget https://www.python.org/ftp/python/3.9.16/Python-3.9.16.tgz
tar xzf Python-3.9.16.tgz
cd Python-3.9.16
./configure --enable-optimizations
make altinstall
cd /tmp
rm -rf Python-3.9.16

# Installation dépendances Python
/opt/python/bin/python3.9 -m pip install --upgrade pip
/opt/python/bin/python3.9 -m pip install fastapi uvicorn pydantic python-multipart aiofiles
/opt/python/bin/python3.9 -m pip install numpy scipy scikit-learn
/opt/python/bin/python3.9 -m pip install pillow opencv-python
/opt/python/bin/python3.9 -m pip install requests beautifulsoup4

# Création utilisateur et répertoires
useradd -m connective-ai
mkdir -p /home/connective-ai/complete-evolutionary
chown -R connective-ai:connective-ai /home/connective-ai

echo "✅ Installation de base terminée"
EOF
```

---

## ⏳ ÉTAPE 4: ATTENTE DÉMARRAGE

```bash
# Récupérer INSTANCE_ID depuis l'étape 3
export INSTANCE_ID="i-xxxxxxxxx"

# Attendre que l'instance soit running
aws ec2 wait instance-running \
    --instance-ids "$INSTANCE_ID" \
    --region "$REGION"
```

---

## 🌐 ÉTAPE 5: RÉCUPÉRATION IP

```bash
aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --query "Instances[0].PublicIpAddress" \
    --output text \
    --region "$REGION"

# Note: Sauvegarder l'IP dans une variable
export PUBLIC_IP="xx.xx.xx.xx"
```

---

## 🔧 ÉTAPE 6: CONFIGURATION SSH

```bash
# Attendre 2-3 minutes que SSH soit disponible
sleep 120

# Test connexion SSH
ssh -o ConnectTimeout=30 -o StrictHostKeyChecking=no -i ~/.ssh/deep \
    ec2-user@$PUBLIC_IP "echo SSH OK"

# Si SSH ne fonctionne pas, vérifier:
# 1. La clé SSH ~/.ssh/deep existe
# 2. Le security groupe autorise le port 22
# 3. L'instance est bien en état "running"
```

---

## 📦 ÉTAPE 7: INSTALLATION APPLICATION

### **Sur Instance via SSH**

```bash
# Se connecter à l'instance
ssh -i ~/.ssh/deep ec2-user@$PUBLIC_IP

# Exécuter ces commandes sur l'instance:

# Installation dépendances manuelles
sudo yum update -y
sudo yum install -y python3 python3-pip git nginx

# Installation Python 3.9
sudo yum install -y gcc openssl-devel bzip2-devel libffi-devel zlib-devel
cd /tmp
sudo wget https://www.python.org/ftp/python/3.9.16/Python-3.9.16.tgz
sudo tar xzf Python-3.9.16.tgz
cd Python-3.9.16
sudo ./configure --enable-optimizations
sudo make altinstall
cd /tmp
sudo rm -rf Python-3.9.16

# Installation packages Python
sudo /opt/python/bin/python3.9 -m pip install --upgrade pip
sudo /opt/python/bin/python3.9 -m pip install fastapi uvicorn pydantic python-multipart aiofiles
sudo /opt/python/bin/python3.9 -m pip install numpy scipy scikit-learn
sudo /opt/python/bin/python3.9 -m pip install pillow opencv-python
sudo /opt/python/bin/python3.9 -m pip install requests beautifulsoup4

# Création utilisateur
sudo useradd -m connective-ai
sudo mkdir -p /home/connective-ai/complete-evolutionary
sudo chown -R connective-ai:connective-ai /home/connective-ai
```

---

## 📁 ÉTAPE 8: TRANSFERT FICHIERS

### **Depuis Machine Locale**

```bash
# Transfert des fichiers (depuis votre machine locale)
scp -i ~/.ssh/deep test_local_server.py ec2-user@$PUBLIC_IP:/tmp/
scp -i ~/.ssh/deep test_api.py ec2-user@$PUBLIC_IP:/tmp/

# Installation sur instance
ssh -i ~/.ssh/deep ec2-user@$PUBLIC_IP << 'EOF'
sudo cp /tmp/test_local_server.py /home/connective-ai/complete-evolutionary/connective_ai_complete_evolutionary.py
sudo cp /tmp/test_api.py /home/connective-ai/complete-evolutionary/
sudo chown -R connective-ai:connective-ai /home/connective-ai/complete-evolutionary
echo "✅ Fichiers installés"
EOF
```

---

## ⚙️ ÉTAPE 9: CONFIGURATION SERVICE

### **Sur Instance via SSH**

```bash
# Création service systemd
sudo cat > /etc/systemd/system/connective-ai-complete.service << 'EOF'
[Unit]
Description=Connective AI Complete Evolutionary
After=network.target

[Service]
Type=simple
User=connective-ai
WorkingDirectory=/home/connective-ai/complete-evolutionary
Environment="PATH=/opt/python/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/opt/python/bin/python3.9 connective_ai_complete_evolutionary.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Démarrage service
sudo systemctl daemon-reload
sudo systemctl enable connective-ai-complete
sudo systemctl start connective-ai-complete

# Vérification statut
sudo systemctl status connective-ai-complete
```

---

## 🌐 ÉTAPE 10: CONFIGURATION NGINX

### **Sur Instance via SSH**

```bash
# Configuration nginx
sudo cat > /etc/nginx/conf.d/connective-ai.conf << 'EOF'
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
    
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
    
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
    }
}
EOF

# Démarrage nginx
sudo systemctl enable nginx
sudo systemctl start nginx
sudo systemctl status nginx
```

---

## 🔍 ÉTAPE 11: VALIDATION

### **Tests depuis Machine Locale**

```bash
# Test 1: Health check
curl -s http://$PUBLIC_IP/health | head -10

# Test 2: Documentation
curl -s http://$PUBLIC_IP/docs | head -10

# Test 3: Modalities
curl -s http://$PUBLIC_IP/modalities

# Test 4: LM Arena Score
curl -s http://$PUBLIC_IP/lm_arena_score

# Test 5: Génération
curl -X POST http://$PUBLIC_IP/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test", "modalities": ["text"], "use_evolution": true}'
```

---

## 🚨 DÉPANNAGE

### **Si le site reste inaccessible:**

#### **1. Vérifier Service**
```bash
# Sur instance via SSH
sudo systemctl status connective-ai-complete
sudo journalctl -u connective-ai-complete -f

# Redémarrer si nécessaire
sudo systemctl restart connective-ai-complete
```

#### **2. Vérifier Port**
```bash
# Sur instance
sudo netstat -tlnp | grep 8000
sudo lsof -i :8000
```

#### **3. Vérifier Nginx**
```bash
# Sur instance
sudo systemctl status nginx
sudo nginx -t
sudo journalctl -u nginx -f
```

#### **4. Vérifier Firewall**
```bash
# Sur instance
sudo systemctl status firewalld
sudo firewall-cmd --list-all

# Si firewall actif
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --reload
```

---

## 🎯 RÉSULTAT FINAL

### **Endpoints Disponibles**

```bash
# Une fois validé:
echo "🌊 Connective AI Complete Evolutionary est déployé!"
echo "📚 Documentation: http://$PUBLIC_IP/docs"
echo "🏆 LM Arena: http://$PUBLIC_IP/lm_arena_score"
echo "🧠 API: http://$PUBLIC_IP/generate"
echo "❤️ Health: http://$PUBLIC_IP/health"
```

---

## 🚀 INSTRUCTIONS FINALES

1. **Exécuter les commandes dans l'ordre**
2. **Remplacer les variables xxx par les vraies valeurs**
3. **Attendre chaque étape avant de passer à la suivante**
4. **Valider chaque endpoint**
5. **Si problème, consulter la section dépannage**

**🌊 L'IA native auto-évolutive sera bientôt accessible!**
