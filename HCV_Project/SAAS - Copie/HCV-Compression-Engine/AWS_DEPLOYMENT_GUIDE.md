# 🚀 Guide de Déploiement AWS - HCV PRO Backend

**Date**: 17 Avril 2026  
**Service**: AWS Elastic Beanstalk  
**Coût**: Gratuit pendant 12 mois (couche gratuite AWS)  
**Temps Estimé**: 15-20 minutes

---

## 📋 Prérequis

1. **Compte AWS** - Créé ✅
2. **AWS CLI** - À installer
3. **EB CLI** - À installer
4. **Git** - Déjà installé ✅

---

## 🔧 Installation des Outils AWS

### Étape 1: Installer AWS CLI

**Windows:**
```bash
# Télécharger et installer
https://awscli.amazonaws.com/AWSCLIV2.msi

# Ou avec pip
pip install awscliv2
```

**Vérifier l'installation:**
```bash
aws --version
```

### Étape 2: Installer EB CLI

```bash
pip install awsebcli
```

**Vérifier l'installation:**
```bash
eb --version
```

---

## 🔑 Configurer les Credentials AWS

### Étape 1: Créer une Clé d'Accès

1. Aller à [AWS Console](https://console.aws.amazon.com)
2. Aller à **IAM** → **Users** → Votre utilisateur
3. Aller à **Security credentials**
4. Cliquer **Create access key**
5. Copier **Access Key ID** et **Secret Access Key**

### Étape 2: Configurer AWS CLI

```bash
aws configure
```

**Entrer:**
- AWS Access Key ID: `[Votre Access Key]`
- AWS Secret Access Key: `[Votre Secret Key]`
- Default region: `us-east-1`
- Default output format: `json`

---

## 🚀 Déployer sur Elastic Beanstalk

### Étape 1: Initialiser Elastic Beanstalk

```bash
cd HCV-PRO-PROJECT/render-backend
eb init -p "Python 3.11 running on 64bit Amazon Linux 2" hcv-pro-backend --region us-east-1
```

### Étape 2: Créer l'Environnement

```bash
eb create hcv-pro-backend-env --instance-type t2.micro
```

**Cela va:**
- Créer une instance EC2 t2.micro (gratuit)
- Configurer un load balancer
- Déployer l'application
- Prendre 5-10 minutes

### Étape 3: Vérifier le Déploiement

```bash
eb status
```

**Réponse attendue:**
```
Environment details for: hcv-pro-backend-env
  Application name: hcv-pro-backend
  Region: us-east-1
  Deployed Version: app-...
  Environment ID: e-...
  Platform: Python 3.11 running on 64bit Amazon Linux 2
  Tier: WebServer standard
  CNAME: hcv-pro-backend-env.elasticbeanstalk.com
  Health: Green
```

### Étape 4: Obtenir l'URL

```bash
eb open
```

Cela va ouvrir l'application dans votre navigateur.

**URL de l'application:**
```
http://hcv-pro-backend-env.elasticbeanstalk.com
```

---

## 🧪 Tester l'Application

### Test 1: Health Check

```bash
curl http://hcv-pro-backend-env.elasticbeanstalk.com/health
```

**Réponse attendue:**
```json
{
  "status": "healthy",
  "service": "HCV PRO Backend",
  "version": "1.0.0",
  "timestamp": "2026-04-17T...",
  "environment": "render"
}
```

### Test 2: Info Codecs

```bash
curl http://hcv-pro-backend-env.elasticbeanstalk.com/info
```

### Test 3: Compression

```bash
curl -X POST http://hcv-pro-backend-env.elasticbeanstalk.com/compress/broadcast \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 1048576}'
```

---

## 📝 Mettre à Jour l'Application

### Après des Changements Locaux

```bash
# Commit les changements
git add .
git commit -m "Update backend"

# Déployer sur Elastic Beanstalk
eb deploy
```

---

## 🔒 Configurer les Variables d'Environnement

### Via EB CLI

```bash
eb setenv HCV_PRO_SECRET=your-secret-key-here
eb setenv HCV_PRO_API_KEY_REQUIRED=true
eb setenv HCV_PRO_RATE_LIMIT=100
eb setenv FLASK_ENV=production
eb setenv FLASK_DEBUG=false
```

### Via AWS Console

1. Aller à [Elastic Beanstalk Console](https://console.aws.amazon.com/elasticbeanstalk)
2. Sélectionner **hcv-pro-backend-env**
3. Aller à **Configuration** → **Software**
4. Ajouter les variables d'environnement
5. Cliquer **Apply**

---

## 📊 Monitorer l'Application

### Logs

```bash
# Voir les logs en temps réel
eb logs --stream

# Voir les logs récents
eb logs
```

### Métriques

1. Aller à [Elastic Beanstalk Console](https://console.aws.amazon.com/elasticbeanstalk)
2. Sélectionner **hcv-pro-backend-env**
3. Aller à **Monitoring**
4. Voir les métriques (CPU, Memory, Network, etc.)

---

## 🛑 Arrêter l'Application

```bash
# Terminer l'environnement (arrête les frais)
eb terminate hcv-pro-backend-env
```

**Important:** Cela supprimera l'application et l'environnement.

---

## 💰 Coûts

### Couche Gratuite AWS (12 mois)

- **EC2**: 750 heures/mois (t2.micro)
- **Elastic Load Balancer**: 750 heures/mois
- **Data Transfer**: 1 GB/mois gratuit
- **CloudWatch Logs**: 5 GB/mois gratuit

### Après la Couche Gratuite

- **EC2 t2.micro**: ~$0.01/heure (~$7/mois)
- **Load Balancer**: ~$16/mois
- **Data Transfer**: ~$0.09/GB

**Total estimé**: ~$25/mois après la couche gratuite

---

## 🆘 Dépannage

### Problème: Déploiement échoue

```bash
# Voir les logs d'erreur
eb logs

# Vérifier le statut
eb status

# Redéployer
eb deploy
```

### Problème: Application ne répond pas

```bash
# Vérifier la santé
eb health

# Redémarrer l'environnement
eb restart
```

### Problème: Erreur 502 Bad Gateway

```bash
# Vérifier les logs
eb logs --stream

# Vérifier que l'application démarre correctement
# Vérifier les variables d'environnement
eb printenv
```

---

## 📚 Ressources

- [AWS Elastic Beanstalk Documentation](https://docs.aws.amazon.com/elasticbeanstalk/)
- [EB CLI Documentation](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3.html)
- [AWS Free Tier](https://aws.amazon.com/free/)
- [Flask on Elastic Beanstalk](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-flask.html)

---

## ✅ Checklist de Déploiement

- [ ] AWS CLI installé
- [ ] EB CLI installé
- [ ] Credentials AWS configurés
- [ ] EB initialisé
- [ ] Environnement créé
- [ ] Application déployée
- [ ] Health check réussi
- [ ] Tests passés
- [ ] Variables d'environnement configurées
- [ ] Monitoring activé

---

**Généré**: 17 Avril 2026  
**Statut**: ✅ Guide Complet  
**Prêt pour**: Déploiement Immédiat

