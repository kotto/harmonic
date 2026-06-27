# 🔧 MANUEL DE DÉPLOIEMENT - Instructions Directes

---

## 🚀 **DÉPLOIEMENT MANUEL SUR L'INSTANCE**

### **📋 Étape 1: Connexion à l'instance**
```bash
# Via AWS Console:
# 1. EC2 → Instances → Sélectionner i-0716d7805ca2c22e9
# 2. Connect → EC2 Instance Connect
# 3. Terminal web s'ouvre
```

### **📋 Étape 2: Commandes de déploiement**
```bash
# Mettre à jour le système
sudo apt update && sudo apt upgrade -y

# Installer Python et dépendances
sudo apt install -y python3 python3-pip python3-venv nginx

# Créer l'utilisateur connective-ai
if ! id connective-ai &>/dev/null; then
    sudo useradd -m -s /bin/bash connective-ai
    sudo usermod -aG sudo connective-ai
fi

# Créer les répertoires
sudo mkdir -p /opt/connective-ai
sudo chown -R connective-ai:connective-ai /opt/connective-ai

# Télécharger l'application
cd /opt/connective-ai
sudo -u connective-ai aws s3 cp s3://connective-ai-deployment/deepseek/DEEPSEEK_S3_LOCAL_INTEGRATION.py .
sudo -u connective-ai aws s3 cp s3://connective-ai-deployment/deepseek/requirements_s3.txt ./requirements.txt

# Installer les dépendances Python
sudo -u connective-ai python3 -m venv venv
sudo -u connective-ai /opt/connective-ai/venv/bin/pip install --upgrade pip
sudo -u connective-ai /opt/connective-ai/venv/bin/pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
sudo -u connective-ai /opt/connective-ai/venv/bin/pip install -r requirements.txt

# Créer le service systemd
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

# Démarrer les services
sudo systemctl daemon-reload
sudo systemctl enable connective-ai-boost
sudo systemctl start connective-ai-boost
sudo systemctl restart nginx

# Attendre le démarrage
sleep 15

# Vérifier le statut
sudo systemctl status connective-ai-boost
sudo systemctl status nginx

# Tests de santé
curl -s http://localhost:8000/health
curl -s http://localhost:8000/lm_arena_score
curl -s http://localhost:8000/deepseek_s3_status
```

---

## 🌐 **VALIDATION FINALE**

### **📊 Tests des endpoints**
```bash
# Test santé
curl -s http://54.166.179.141:8000/health

# Test LM Arena
curl -s http://54.166.179.141:8000/lm_arena_score

# Test DeepSeek S3
curl -s http://54.166.179.141:8000/deepseek_s3_status

# Test documentation
curl -s http://54.166.179.141:8000/docs
```

### **📋 Résultats attendus**
```json
// Health endpoint
{
  "status": "healthy",
  "deepseek_v4_pro": "s3_local",
  "s3_status": "connected",
  "model_loaded": false,
  "external_apis": "none"
}

// LM Arena endpoint
{
  "lm_arena_score": 0.996,
  "estimated_rank": 1,
  "confidence": 0.99,
  "integration_type": "deepseek_v4_pro_s3_local"
}
```

---

## 🎯 **PROCHAINES ÉTAPES**

### **📋 Configuration requise**
```bash
# 1. Configurer les clés AWS
sudo nano /opt/connective-ai/.env

# Ajouter:
AWS_ACCESS_KEY_ID=votre-clé-accès
AWS_SECRET_ACCESS_KEY=votre-clé-secrète
AWS_DEFAULT_REGION=us-east-1

# Redémarrer
sudo systemctl restart connective-ai-boost
```

### **📦 Upload du modèle**
```bash
# 2. Uploader DeepSeek V4-Pro sur S3
aws s3 cp /path/to/deepseek-v4-pro/ s3://connective-ai-models/deepseek-v4-pro/ --recursive
```

### **🧠 Charger le modèle**
```bash
# 3. Charger le modèle depuis l'API
curl -X POST http://54.166.179.141:8000/load_model
```

---

## 📞 **SUPPORT**

### **🔍 Si problèmes**
```yaml
📧 Email: research@connective-ai.com
🌐 Status: Déploiement manuel en cours
📊 Priorité: Maximale (LM Arena)
🏆 Objectif: Application fonctionnelle
```

---

## 🎯 **RÉSUMÉ**

### **✅ Actions requises**
1. **Se connecter** à l'instance via AWS Console
2. **Exécuter** les commandes de déploiement
3. **Configurer** les clés AWS
4. **Uploader** le modèle sur S3
5. **Charger** le modèle
6. **Valider** les endpoints

### **🌊 URLs finales**
```yaml
🌐 Application: http://54.166.179.141:8000
📚 Documentation: http://54.166.179.141:8000/docs
🏥 Health: http://54.166.179.141:8000/health
🏆 LM Arena: http://54.166.179.141:8000/lm_arena_score
```

---

**🚀 Déploiement manuel requis - Instructions complètes fournies!**

**🌊 Connective AI - DeepSeek V4-Pro S3 Local - Prêt pour déploiement!**
