# 🚀 DÉPLOIEMENT AVEC RÔLE IAM UNIQUEMENT

---

## ✅ **SCRIPT CRÉÉ - Aucune clé AWS requise**

### **📋 Pourquoi ce script?**
```yaml
🔑 IAM Role: ConnectiveAI-DeepSeek-Role déjà configuré
📦 Permissions: AmazonS3FullAccess + AmazonSSMManagedInstanceCore
🚀 Avantage: Pas besoin de clés AWS manuelles
🔧 Sécurité: Meilleure pratique AWS
🌊 Automatique: Credentials gérées par AWS
```

---

## 🔧 **SCRIPT SPÉCIAL IAM ROLE**

### **📋 Caractéristiques**
```yaml
🔑 Authentification: Rôle IAM uniquement
📦 Variables: Minimales (pas de clés AWS)
🔍 Vérification: Test du rôle IAM avant déploiement
🛡️ Sécurité: Pas de clés en clair
🚀 Automatique: Credentials fournies par AWS
```

### **📋 Variables d'environnement minimales**
```bash
# Fichier .env minimal (le rôle IAM fournit le reste)
S3_BUCKET=deepseek-models-326095712935
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=false
# Pas de AWS_ACCESS_KEY_ID ni AWS_SECRET_ACCESS_KEY!
```

---

## 🚀 **INSTRUCTIONS D'EXÉCUTION**

### **📋 Étape 1: Télécharger le script**
```bash
cd /tmp
aws s3 cp s3://connective-ai-deployment/deepseek/DEPLOY_IAM_ROLE_ONLY.sh .
chmod +x DEPLOY_IAM_ROLE_ONLY.sh
```

### **📋 Étape 2: Exécuter le déploiement**
```bash
sudo ./DEPLOY_IAM_ROLE_ONLY.sh
```

---

## 🔍 **CE QUE LE SCRIPT FAIT**

### **📋 Vérification du rôle IAM**
```bash
# Test du rôle IAM avant de continuer
aws sts get-caller-identity --region us-east-1
# Si échec: arrêt du script
```

### **📋 Configuration minimale**
```bash
# Création du fichier .env SANS clés AWS
sudo -u connective-ai tee .env > /dev/null << 'ENV'
S3_BUCKET=deepseek-models-326095712935
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=false
ENV
```

### **📋 Service systemd optimisé**
```bash
# Le service utilise le rôle IAM automatiquement
EnvironmentFile=/opt/connective-ai/.env
# Pas de variables AWS dans le fichier .env
```

---

## 🔧 **AVANTAGES DU RÔLE IAM**

### **✅ Sécurité**
```yaml
🔒 Pas de clés en clair dans les fichiers
🚀 Credentials rotatives automatiques
📋 Permissions précises et contrôlées
🌊 Meilleure pratique AWS
```

### **✅ Maintenance**
```yaml
🔄 Gestion centralisée des permissions
📊 Monitoring intégré
🔧 Pas de gestion manuelle des clés
🚀 Scalabilité
```

---

## 🔍 **DÉPANNAGE**

### **📋 Si le rôle IAM ne fonctionne pas**
```bash
# Vérifier le rôle attaché à l'instance
aws ec2 describe-instances --instance-ids i-0716d7805ca2c22e9 --query "Reservations[0].Instances[0].IamInstanceProfile"

# Vérifier les permissions du rôle
aws iam get-role --role-name ConnectiveAI-DeepSeek-Role

# Tester l'accès S3
aws s3 ls s3://deepseek-models-326095712935/ --region us-east-1
```

### **📋 Si le service ne démarre pas**
```bash
# Vérifier les logs
sudo journalctl -u connective-ai-boost -f

# Vérifier le fichier .env
cat /opt/connective-ai/.env

# Redémarrer le service
sudo systemctl restart connective-ai-boost
```

---

## 🎯 **VALIDATION FINALE**

### **📋 Tests après déploiement**
```bash
# Test santé
curl -s http://localhost:8000/health | python3 -m json.tool

# Test LM Arena
curl -s http://localhost:8000/lm_arena_score | python3 -m json.tool

# Test DeepSeek S3
curl -s http://localhost:8000/deepseek_s3_status | python3 -m json.tool

# Test accès S3 (devrait fonctionner)
aws s3 ls s3://deepseek-models-326095712935/deepseek-v4-pro/ --region us-east-1
```

---

## 📞 **RÉSUMÉ**

### **✅ Ce script résout:**
- **Problème de credentials**: Utilise le rôle IAM
- **Sécurité**: Pas de clés en clair
- **Maintenance**: Gestion automatique
- **Best practices**: Conforme AWS

### **🔧 Configuration requise:**
- **Rôle IAM**: ConnectiveAI-DeepSeek-Role (déjà configuré)
- **Permissions**: AmazonS3FullAccess + AmazonSSMManagedInstanceCore
- **Instance**: i-0716d7805ca2c22e9

### **🚋 Action requise:**
1. **Exécuter le script** DEPLOY_IAM_ROLE_ONLY.sh
2. **Valider** les endpoints
3. **Charger** le modèle
4. **Soumettre** à LM Arena

---

**🚀 Script IAM Role créé - Aucune clé AWS requise!**

**🌊 Connective AI - DeepSeek V4-Pro - IAM Role Only!**

**📞 Exécutez le script et profitez de la sécurité IAM!**
