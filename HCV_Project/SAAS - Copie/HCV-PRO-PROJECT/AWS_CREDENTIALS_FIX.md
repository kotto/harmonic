# 🔧 CORRECTION AWS CREDENTIALS - Problème IAM

---

## ❌ **PROBLÈME IDENTIFIÉ**

### **📊 Erreur Actuelle**
```yaml
❌ Erreur: "Unable to locate credentials"
🔴 Cause: L'instance n'a pas de rôle IAM configuré
🔴 Solution: Configurer manuellement les credentials AWS
```

---

## 🔍 **DIAGNOSTIC**

### **📋 Problème de Rôle IAM**
```yaml
❌ Instance: Pas de rôle IAM attaché
❌ Credentials: Non configurées
❌ Accès S3: Bloqué
🔧 Solution: Configuration manuelle requise
```

---

## 🚀 **SOLUTION IMMÉDIATE**

### **📋 Étape 1: Installer nginx (Amazon Linux 2)**
```bash
sudo amazon-linux-extras install nginx1
```

### **📋 Étape 2: Configurer AWS CLI manuellement**
```bash
# Configurer AWS CLI avec vos credentials
aws configure
```

### **📋 Étape 3: Entrer vos informations**
```bash
AWS Access Key ID: [VOTRE_CLÉ_D'ACCÈS]
AWS Secret Access Key: [VOTRE_CLÉ_SECRÈTE]
Default region name: us-east-1
Default output format: json
```

---

## 🔧 **SCRIPT CORRIGÉ AVEC CONFIGURATION MANUELLE**

### **📋 Instructions Complètes**
```bash
# 1. Installer nginx
sudo amazon-linux-extras install nginx1

# 2. Configurer AWS CLI
aws configure

# 3. Télécharger et exécuter le script
cd /tmp
aws s3 cp s3://connective-ai-deployment/deepseek/DEPLOY_AMAZON_LINUX_2_FIX.sh .
chmod +x DEPLOY_AMAZON_LINUX_2_FIX.sh
sudo ./DEPLOY_AMAZON_LINUX_2_FIX.sh
```

---

## 🔍 **VÉRIFICATION APRÈS CONFIGURATION**

### **📋 Tester la configuration**
```bash
# Tester l'accès AWS
aws sts get-caller-identity --region us-east-1

# Tester l'accès S3
aws s3 ls s3://connective-ai-deployment/deepseek/ --region us-east-1
```

---

## 🎯 **SOLUTION ALTERNATIVE**

### **📋 Si vous n'avez pas de clés AWS**
```bash
# Option 1: Créer un rôle IAM et l'attacher à l'instance
# Option 2: Utiliser des credentials temporaires
# Option 3: Configurer via variables d'environnement
```

### **📋 Variables d'environnement**
```bash
export AWS_ACCESS_KEY_ID=votre_clé_d_accès
export AWS_SECRET_ACCESS_KEY=votre_clé_secrète
export AWS_DEFAULT_REGION=us-east-1
```

---

## 🚀 **DÉPLOIEMENT MANUEL ÉTAPE PAR ÉTAPE**

### **📋 Si le script échoue encore**
```bash
# 1. Installer nginx
sudo amazon-linux-extras install nginx1

# 2. Créer l'utilisateur
sudo useradd -m -s /bin/bash connective-ai
sudo usermod -aG wheel connective-ai

# 3. Créer les répertoires
sudo mkdir -p /opt/connective-ai
sudo chown -R connective-ai:connective-ai /opt/connective-ai

# 4. Télécharger manuellement l'application
cd /opt/connective-ai
sudo -u connective-ai aws s3 cp s3://connective-ai-deployment/deepseek/DEEPSEEK_S3_LOCAL_INTEGRATION.py .
sudo -u connective-ai aws s3 cp s3://connective-ai-deployment/deepseek/requirements_s3.txt ./requirements.txt

# 5. Installer Python virtuel
sudo -u connective-ai python3 -m venv venv
sudo -u connective-ai /opt/connective-ai/venv/bin/pip install --upgrade pip

# 6. Installer PyTorch
sudo -u connective-ai /opt/connective-ai/venv/bin/pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 7. Installer les dépendances
sudo -u connective-ai /opt/connective-ai/venv/bin/pip install -r requirements.txt

# 8. Créer le service systemd
sudo tee /etc/systemd/system/connective-ai-boost.service > /dev/null << 'EOS'
[Unit]
Description=Connective AI DeepSeek V4-Pro S3 Local Service
After=network.target

[Service]
Type=simple
User=connective-ai
WorkingDirectory=/opt/connective-ai
Environment=PATH=/opt/connective-ai/venv/bin
ExecStart=/opt/connective-ai/venv/bin/uvicorn DEEPSEEK_S3_LOCAL_INTEGRATION:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOS

# 9. Configurer nginx
sudo tee /etc/nginx/conf.d/connective-ai.conf > /dev/null << 'EON'
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

# 10. Démarrer les services
sudo systemctl daemon-reload
sudo systemctl enable connective-ai-boost
sudo systemctl start connective-ai-boost
sudo systemctl restart nginx
```

---

## 🔧 **DÉPANNAGE**

### **📋 Si aws configure ne fonctionne pas**
```bash
# Vérifier l'installation AWS CLI
which aws
aws --version

# Installer via pip si nécessaire
sudo pip3 install --upgrade awscli

# Configurer manuellement
mkdir -p ~/.aws
cat > ~/.aws/config << 'EOF'
[default]
region = us-east-1
output = json
EOF

cat > ~/.aws/credentials << 'EOF'
[default]
aws_access_key_id = VOTRE_CLÉ_D_ACCÈS
aws_secret_access_key = VOTRE_CLÉ_SECRÈTE
EOF
```

---

## 📞 **RÉSUMÉ**

### **✅ Problème identifié:**
- **Instance sans rôle IAM**
- **AWS CLI non configurée**
- **Accès S3 bloqué**

### **🔧 Solution requise:**
1. **Configurer AWS CLI manuellement** avec `aws configure`
2. **Installer nginx** avec `sudo amazon-linux-extras install nginx1`
3. **Exécuter le script corrigé**

### **📋 Commandes immédiates:**
```bash
sudo amazon-linux-extras install nginx1
aws configure
cd /tmp
aws s3 cp s3://connective-ai-deployment/deepseek/DEPLOY_AMAZON_LINUX_2_FIX.sh .
chmod +x DEPLOY_AMAZON_LINUX_2_FIX.sh
sudo ./DEPLOY_AMAZON_LINUX_2_FIX.sh
```

---

**🚀 Solution trouvée: Configuration manuelle AWS CLI requise!**

**🌊 Connective AI - DeepSeek V4-Pro - Configuration AWS Manuelle!**

**📞 Exécutez `aws configure` puis le script corrigé!**
