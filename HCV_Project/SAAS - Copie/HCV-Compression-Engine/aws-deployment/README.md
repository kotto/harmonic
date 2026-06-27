# 🚀 HCV PRO - AWS Deployment Complete

Ce dossier contient tout le nécessaire pour déployer HCV PRO sur AWS avec GitHub Actions.

## 📁 Structure

```
aws-deployment/
├── README.md                    # Ce fichier
├── .github/                     # GitHub Actions workflows
│   └── workflows/
│       ├── deploy-backend.yml   # Déploiement backend AWS App Runner
│       ├── deploy-frontend.yml  # Déploiement frontend S3 + CloudFront
│       └── test-deployment.yml  # Tests de déploiement
├── infrastructure/              # Infrastructure AWS
│   ├── backend/                 # Configuration backend
│   ├── frontend/                # Configuration frontend
│   └── monitoring/              # Monitoring et logs
├── scripts/                     # Scripts de déploiement
│   ├── deploy.sh               # Script principal
│   ├── setup-aws.sh            # Configuration AWS
│   └── test-deployment.sh      # Tests automatisés
├── config/                      # Fichiers de configuration
│   ├── aws-credentials.json    # Credentials AWS (template)
│   ├── apprunner-config.json   # Configuration App Runner
│   └── cloudfront-config.json  # Configuration CloudFront
└── docs/                        # Documentation
    ├── deployment-guide.md      # Guide complet
    ├── troubleshooting.md       # Dépannage
    └── monitoring.md           # Monitoring
```

## 🎯 Objectif

Déploiement automatisé et continu de HCV PRO sur AWS avec :
- Backend Python Flask sur AWS App Runner
- Frontend sur S3 + CloudFront CDN
- CI/CD avec GitHub Actions
- Monitoring et logs intégrés
- Sécurité et performances optimisées

## ⚡ Quick Start

1. **Configurer les credentials AWS**
2. **Activer GitHub Actions**
3. **Lancer le déploiement**
4. **Vérifier le déploiement**

Voir [deployment-guide.md](docs/deployment-guide.md) pour les instructions détaillées.

## 🔧 Prérequis

- Compte AWS avec permissions appropriées
- Repository GitHub avec le code HCV PRO
- AWS CLI configuré
- Docker installé (pour build local)

## 🚨 Sécurité

- Ne jamais commiter les vrais credentials
- Utiliser AWS Secrets Manager pour les secrets
- Configurer IAM roles appropriés
- Activer les logs et monitoring

## 📞 Support

En cas de problème, voir [troubleshooting.md](docs/troubleshooting.md) ou vérifier les logs GitHub Actions.
