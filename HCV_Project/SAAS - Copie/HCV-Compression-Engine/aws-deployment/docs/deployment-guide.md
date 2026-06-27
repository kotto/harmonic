# 🚀 HCV PRO - Guide de Déploiement AWS Complet

Ce guide explique comment déployer HCV PRO sur AWS avec GitHub Actions CI/CD.

## 📋 Table des Matières

1. [Prérequis](#prérequis)
2. [Configuration AWS](#configuration-aws)
3. [Configuration GitHub](#configuration-github)
4. [Déploiement Automatisé](#déploiement-automatisé)
5. [Monitoring](#monitoring)
6. [Dépannage](#dépannage)

## 🔧 Prérequis

### Requirements

- **Compte AWS** avec permissions appropriées
- **Repository GitHub** avec le code HCV PRO
- **AWS CLI** installé et configuré
- **Docker** installé (pour builds locaux)
- **Node.js** 18+ (pour frontend)

### Permissions AWS Requises

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecr:*",
                "apprunner:*",
                "s3:*",
                "cloudfront:*",
                "iam:*",
                "logs:*"
            ],
            "Resource": "*"
        }
    ]
}
```

## 🌩️ Configuration AWS

### 1. Cloner le Repository

```bash
git clone https://github.com/your-username/hcv-compression-engine.git
cd hcv-compression-engine
```

### 2. Configurer AWS CLI

```bash
aws configure
# AWS Access Key ID: YOUR_ACCESS_KEY
# AWS Secret Access Key: YOUR_SECRET_KEY
# Default region name: eu-west-3
# Default output format: json
```

### 3. Lancer le Script d'Installation

```bash
cd aws-deployment
chmod +x scripts/setup-aws.sh
./scripts/setup-aws.sh
```

Ce script crée automatiquement :
- ✅ ECR Repository pour les images Docker
- ✅ S3 Bucket pour le frontend
- ✅ CloudFront Distribution
- ✅ App Runner Service pour le backend
- ✅ IAM Role pour GitHub Actions

### 4. Vérification de l'Installation

```bash
# Vérifier ECR
aws ecr describe-repositories --repository-names hcv-pro-backend

# Vérifier S3
aws s3 ls s3://hcv-pro-frontend-YOUR_ACCOUNT_ID

# Vérifier App Runner
aws apprunner list-services

# Vérifier CloudFront
aws cloudfront list-distributions
```

## 🐙 Configuration GitHub

### 1. Activer GitHub Actions

Dans votre repository GitHub :
- Allez dans `Settings` > `Actions` > `General`
- Activez `Allow all actions and reusable workflows`

### 2. Configurer les Secrets

Allez dans `Settings` > `Secrets and variables` > `Actions` et ajoutez :

| Secret | Valeur | Description |
|--------|--------|-------------|
| `AWS_ACCOUNT_ID` | `123456789012` | Votre ID de compte AWS |
| `AWS_ROLE_ARN` | `arn:aws:iam::123456789012:role/hcv-pro-github-actions` | Role IAM créé |
| `BACKEND_URL` | `https://abc123.eu-west-3.awsapprunner.com` | URL du backend |
| `FRONTEND_URL` | `https://d2mn7lqwlga5dy.cloudfront.net` | URL du frontend |
| `CLOUDFRONT_DISTRIBUTION_ID` | `EHU0HK1ORPAEL` | ID CloudFront |

### 3. Copier les Workflows

```bash
# Copier les workflows GitHub Actions
cp -r aws-deployment/.github .github

# Commiter et pousser
git add .github/
git commit -m "Add GitHub Actions workflows"
git push origin main
```

## 🚀 Déploiement Automatisé

### Workflow Backend

Le workflow `deploy-backend.yml` se déclenche quand :
- Push sur `main` ou `develop`
- Modifications dans `server/`, `codecs/`, `requirements.txt`, `Dockerfile`
- Déclenchement manuel

**Étapes :**
1. Build Docker image
2. Push vers ECR
3. Update App Runner service
4. Health checks
5. Tests de performance

### Workflow Frontend

Le workflow `deploy-frontend.yml` se déclenche quand :
- Push sur `main` ou `develop`
- Modifications dans `web/`, `package.json`
- Déclenchement manuel

**Étapes :**
1. Build frontend
2. Deploy vers S3
3. Invalider cache CloudFront
4. Tests d'accessibilité
5. Tests de performance

### Déploiement Manuel

```bash
# Backend
git push origin main

# Frontend
git push origin main

# Ou déclencher manuellement depuis GitHub
# Actions > Select workflow > Run workflow
```

## 📊 Monitoring

### 1. Logs Backend

```bash
# Voir les logs App Runner
aws apprunner describe-service \
  --service-arn "arn:aws:apprunner:eu-west-3:ACCOUNT_ID:service/hcv-pro-backend"

# Logs CloudWatch
aws logs tail /aws/apprunner/hcv-pro-backend --follow
```

### 2. Monitoring Frontend

```bash
# Statistiques CloudFront
aws cloudfront get-distribution-config \
  --id DISTRIBUTION_ID

# Logs S3
aws s3api get-bucket-logging-status \
  --bucket hcv-pro-frontend-ACCOUNT_ID
```

### 3. Health Checks

```bash
# Backend health
curl https://your-backend-url/api/health

# Frontend accessibility
curl -I https://your-frontend-url

# Performance tests
curl -w "@curl-format.txt" -o /dev/null -s https://your-backend-url/api/health
```

## 🛠️ Dépannage

### Problèmes Communs

#### 1. "Access Denied" S3/CloudFront

**Cause:** Permissions incorrectes ou cache non invalidé

**Solution:**
```bash
# Vérifier permissions S3
aws s3api get-bucket-policy --bucket your-bucket

# Forcer invalidation CloudFront
aws cloudfront create-invalidation \
  --distribution-id DISTRIBUTION_ID \
  --paths "/*"
```

#### 2. Backend "Failed to fetch"

**Cause:** CORS ou backend non démarré

**Solution:**
```bash
# Vérifier status App Runner
aws apprunner describe-service --service-arn SERVICE_ARN

# Vérifier logs
aws logs tail /aws/apprunner/hcv-pro-backend --follow

# Redémarrer service
aws apprunner update-service \
  --service-arn SERVICE_ARN \
  --source-configuration AutoDeploymentsEnabled=true
```

#### 3. Build Docker Failed

**Cause:** Erreur dans Dockerfile ou dépendances

**Solution:**
```bash
# Build local pour tester
docker build -t test-hcv-pro .

# Tester l'image
docker run test-hcv-pro python -c "from server.hcv_pro_server import app"
```

#### 4. GitHub Actions Failed

**Cause:** Secrets manquants ou permissions incorrectes

**Solution:**
```bash
# Vérifier IAM role
aws iam get-role --role-name hcv-pro-github-actions

# Tester AWS credentials
aws sts get-caller-identity

# Vérifier GitHub Secrets
# Repository > Settings > Secrets and variables > Actions
```

### Commands Utiles

```bash
# Vérifier tous les services
aws apprunner list-services
aws s3 ls
aws cloudfront list-distributions
aws ecr describe-repositories

# Nettoyer en cas de problème
aws apprunner delete-service --service-arn SERVICE_ARN
aws s3 rb s3://bucket-name --force
aws cloudfront delete-distribution --id DISTRIBUTION_ID
```

## 🔄 Mises à Jour

### Pour mettre à jour le backend:

1. Modifier le code dans `server/` ou `codecs/`
2. Commiter et pousser:
   ```bash
   git add server/
   git commit -m "Update backend: feature description"
   git push origin main
   ```
3. Le workflow se lance automatiquement

### Pour mettre à jour le frontend:

1. Modifier le code dans `web/`
2. Commiter et pousser:
   ```bash
   git add web/
   git commit -m "Update frontend: feature description"
   git push origin main
   ```
3. Le workflow se lance automatiquement

## 🎯 Bonnes Pratiques

### 1. Sécurité
- Ne jamais commiter de credentials
- Utiliser AWS Secrets Manager
- Activer les logs et monitoring
- Configurer des IAM roles spécifiques

### 2. Performance
- Utiliser CloudFront CDN
- Configurer cache headers appropriés
- Optimiser les assets (minification, compression)
- Monitorer les temps de réponse

### 3. Fiabilité
- Configurer des health checks
- Utiliser des retries pour les appels API
- Activer les alertes sur les erreurs
- Prévoir des rollbacks automatiques

### 4. Coûts
- Monitorer les coûts AWS
- Utiliser des instances optimisées
- Configurer des lifecycle policies
- Nettoyer les ressources non utilisées

## 📞 Support

En cas de problème:

1. Vérifier les logs GitHub Actions
2. Consulter les logs AWS CloudWatch
3. Vérifier la configuration des secrets
4. Tester localement si possible

Pour plus d'aide, voir [troubleshooting.md](troubleshooting.md).
