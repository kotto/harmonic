# 🚀 HCV PRO - AWS Quick Start

Déploiement rapide de HCV PRO sur AWS avec GitHub Actions.

## ⚡ Quick Start (5 minutes)

### 1. Prérequis

```bash
# Installer AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Installer Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Installer Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 2. Configuration AWS

```bash
# Configurer AWS CLI
aws configure
# AWS Access Key ID: YOUR_ACCESS_KEY
# AWS Secret Access Key: YOUR_SECRET_KEY
# Default region name: eu-west-3
# Default output format: json

# Cloner le repository
git clone https://github.com/your-username/hcv-compression-engine.git
cd hcv-compression-engine
```

### 3. Lancer le Setup Automatique

```bash
# Rendre exécutable et lancer
chmod +x aws-deployment/scripts/setup-aws.sh
./aws-deployment/scripts/setup-aws.sh
```

Le script crée automatiquement :
- ✅ ECR Repository
- ✅ S3 Bucket + CloudFront
- ✅ App Runner Service
- ✅ IAM Role pour GitHub Actions

### 4. Configurer GitHub Secrets

Aller dans votre repository GitHub > Settings > Secrets and variables > Actions et ajouter :

```
AWS_ACCOUNT_ID: 123456789012
AWS_ROLE_ARN: arn:aws:iam::123456789012:role/hcv-pro-github-actions
BACKEND_URL: https://abc123.eu-west-3.awsapprunner.com
FRONTEND_URL: https://d2mn7lqwlga5dy.cloudfront.net
CLOUDFRONT_DISTRIBUTION_ID: EHU0HK1ORPAEL
```

### 5. Activer GitHub Actions

```bash
# Copier les workflows
cp -r aws-deployment/.github .

# Commiter et pousser
git add .github/
git commit -m "Add GitHub Actions workflows"
git push origin main
```

### 6. Vérifier le Déploiement

Les workflows se lancent automatiquement. Vérifiez dans :
- GitHub Actions tab
- AWS App Runner console
- AWS CloudFront console

## 🎯 URLs Finales

Après le déploiement, vous aurez :

- **Frontend**: `https://d2mn7lqwlga5dy.cloudfront.net`
- **Backend**: `https://abc123.eu-west-3.awsapprunner.com`

## 🛠️ Commandes Utiles

```bash
# Déploiement manuel complet
./aws-deployment/scripts/deploy.sh all

# Déploiement backend uniquement
./aws-deployment/scripts/deploy.sh backend

# Déploiement frontend uniquement
./aws-deployment/scripts/deploy.sh frontend

# Tests de déploiement
./aws-deployment/scripts/deploy.sh test

# Vérifier status
aws apprunner describe-service --service-arn SERVICE_ARN
aws cloudfront get-distribution --id DISTRIBUTION_ID
```

## 🔧 Dépannage Rapide

### Problème "Access Denied"

```bash
# Forcer invalidation CloudFront
aws cloudfront create-invalidation \
  --distribution-id DISTRIBUTION_ID \
  --paths "/*"
```

### Problème Backend "Failed to fetch"

```bash
# Vérifier status App Runner
aws apprunner describe-service --service-arn SERVICE_ARN

# Redémarrer service
aws apprunner update-service \
  --service-arn SERVICE_ARN \
  --source-configuration AutoDeploymentsEnabled=true
```

### Problème GitHub Actions Failed

```bash
# Vérifier IAM role
aws iam get-role --role-name hcv-pro-github-actions

# Tester AWS credentials
aws sts get-caller-identity
```

## 📊 Monitoring

```bash
# Logs backend
aws logs tail /aws/apprunner/hcv-pro-backend --follow

# Statistiques CloudFront
aws cloudfront get-distribution-config --id DISTRIBUTION_ID

# Tests de performance
curl -w "@curl-format.txt" -o /dev/null -s https://your-backend-url/api/health
```

## 🎉 Succès!

Si tout fonctionne, vous devriez voir :

- ✅ Frontend accessible via HTTPS
- ✅ Backend API répondant
- ✅ Toutes les fonctionnalités HCV PRO opérationnelles
- ✅ CI/CD automatique configuré

Pour plus de détails, voir [deployment-guide.md](docs/deployment-guide.md).
