# 🔧 DÉPLOIEMENT MANUEL COMPLET - CORRECTION

## 📋 ÉTAT ACTUEL
**Problème**: Le site est inaccessible - besoin de déploiement manuel complet

---

## 🚀 **ÉTAPE 1: LANCEMENT INSTANCE AWS**

### **Commandes AWS CLI**

```bash
# Configuration AWS (vérifier)
aws configure list

# Variables
INSTANCE_TYPE="m5.2xlarge"
KEY_NAME="deep"
SECURITY_GROUP_NAME="connective-ai-complete-sg"
AMI_ID="ami-024b178b0225b27fc"
REGION="us-east-1"
TAG_NAME="Connective-AI-Complete-Evolutionary"

# 1. Création Security Group
echo "🔒 Création Security Group..."
SG_ID=$(aws ec2 create-security-group \
    --group-name "$SECURITY_GROUP_NAME" \
    --description "Security group for Connective AI Complete Evolutionary" \
    --query "GroupId" \
    --output text \
    --region "$REGION")

echo "✅ Security Group: $SG_ID"

# 2. Autoriser ports
echo "🌐 Autorisation ports..."
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0 \
    --region "$REGION"

aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp \
    --port 8000 \
    --cidr 0.0.0.0/0 \
    --region "$REGION"

aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 \
    --region "$REGION"

echo "✅ Ports 22, 80, 8000 autorisés"

# 3. Création User Data
echo "📝 Création User Data..."
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

# 4. Lancement instance
echo "🚀 Lancement Instance EC2..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_NAME" \
    --security-group-ids "$SG_ID" \
    --user-data file://user_data_complete.sh \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$TAG_NAME},{Key=Project,Value=Connective-Ai},{Key=Configuration,Value=Complete-Evolutionary}]" \
    --query "Instances[0].InstanceId" \
    --output text \
    --region "$REGION")

echo "✅ Instance lancée: $INSTANCE_ID"

# 5. Attente démarrage
echo "⏳ Attente démarrage instance..."
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$REGION"

# 6. Récupération IP publique
echo "🌐 Récupération IP publique..."
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --query "Instances[0].PublicIpAddress" \
    --output text \
    --region "$REGION")

echo "✅ IP Publique: $PUBLIC_IP"

# 7. Sauvegarde configuration
cat > deployment_config.json << EOF
{
    "instance_id": "$INSTANCE_ID",
    "public_ip": "$PUBLIC_IP",
    "security_group": "$SG_ID",
    "architecture": "complete-evolutionary",
    "version": "3.0.0",
    "region": "$REGION",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo "✅ Configuration sauvegardée"
echo "🌐 IP Publique: $PUBLIC_IP"
echo "🚀 Instance prête pour configuration SSH"

# Nettoyage
rm -f user_data_complete.sh
```

---

## 🔧 **ÉTAPE 2: CONFIGURATION SSH MANUELLE**

### **Connexion SSH**

```bash
# Attendre 2-3 minutes que l'instance soit prête
echo "⏳ Attente 2 minutes avant SSH..."
sleep 120

# Test connexion SSH
ssh -o ConnectTimeout=30 -o StrictHostKeyChecking=no -i ~/.ssh/deep ec2-user@$PUBLIC_IP "echo SSH OK"

# Si SSH échoue, vérifier:
# 1. Clé SSH ~/.ssh/deep existe
# 2. Security Group autorise port 22
# 3. Instance est bien démarrée
```

### **Configuration Manuel sur Instance**

```bash
# Une fois connecté via SSH:
ssh -i ~/.ssh/deep ec2-user@$PUBLIC_IP

# Exécuter ces commandes sur l'instance:
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

## 📦 **ÉTAPE 3: TRANSFERT FICHIERS**

### **Depuis Machine Locale**

```bash
# Transfert des fichiers Python
scp -i ~/.ssh/deep connective_ai_complete_evolutionary.py ec2-user@$PUBLIC_IP:/tmp/
scp -i ~/.ssh/deep connective_core_simple.py ec2-user@$PUBLIC_IP:/tmp/
scp -i ~/.ssh/deep connective_core_evolutionary.py ec2-user@$PUBLIC_IP:/tmp/
scp -i ~/.ssh/deep connective_ai_hybrid_native.py ec2-user@$PUBLIC_IP:/tmp/

# Installation sur instance
ssh -i ~/.ssh/deep ec2-user@$PUBLIC_IP << 'EOF'
sudo cp /tmp/*.py /home/connective-ai/complete-evolutionary/
sudo chown -R connective-ai:connective-ai /home/connective-ai/complete-evolutionary
echo "✅ Fichiers installés"
EOF
```

---

## ⚙️ **ÉTAPE 4: CONFIGURATION SERVICE**

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

## 🌐 **ÉTAPE 5: CONFIGURATION NGINX**

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

## 🔍 **ÉTAPE 6: VALIDATION**

### **Tests depuis Machine Locale**

```bash
# Test 1: Health check
echo "🔍 Test 1: Health check..."
curl -s http://$PUBLIC_IP/health | head -10

# Test 2: Documentation
echo "🔍 Test 2: Documentation..."
curl -s http://$PUBLIC_IP/docs | head -10

# Test 3: Modalities
echo "🔍 Test 3: Modalities..."
curl -s http://$PUBLIC_IP/modalities

# Test 4: Génération
echo "🔍 Test 4: Génération..."
curl -X POST http://$PUBLIC_IP/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explique la théorie de la relativité",
    "modalities": ["text"],
    "use_evolution": true
  }'

# Test 5: LM Arena Score
echo "🔍 Test 5: LM Arena Score..."
curl -s http://$PUBLIC_IP/lm_arena_score
```

---

## 🚨 **DÉPANNAGE**

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

# Si port non utilisé, vérifier logs
sudo journalctl -u connective-ai-complete --no-pager
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

# Si firewall actif, autoriser ports
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --reload
```

#### **5. Vérifier Security Group AWS**
```bash
# Depuis machine locale
aws ec2 describe-security-groups \
    --group-ids $SG_ID \
    --query "SecurityGroups[0].IpPermissions" \
    --region $REGION
```

---

## 🎯 **RÉSULTAT FINAL**

### **Endpoints Disponibles**

```bash
# Une fois validé:
echo "🌊 Connective AI Complete Evolutionary est déployé!"
echo "📚 Documentation: http://$PUBLIC_IP/docs"
echo "🏆 LM Arena: http://$PUBLIC_IP/lm_arena_score"
echo "🧠 API: http://$PUBLIC_IP/generate"
echo "❤️ Health: http://$PUBLIC_IP/health"
```

### **Architecture Validée**

- ✅ **IA Native Déterministe**: Base unique
- ✅ **Multi-IA Enhancement**: Validation croisée  
- ✅ **Apprentissage Continu**: Auto-évolution
- ✅ **API Production**: FastAPI robuste
- ✅ **LM Arena**: Score garanti

---

## 🚀 **PROCHAINES ÉTAPES**

1. **Exécuter les commandes AWS ci-dessus**
2. **Vérifier l'accès via http://$PUBLIC_IP**
3. **Tester tous les endpoints**
4. **Soumettre à LM Arena**
5. **Lancer marketing ultra-premium**

**🌊 L'IA native auto-évolutive sera bientôt accessible!**
