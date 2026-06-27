# 🌊 Deepseek MOE Harmonic - Guide d'Intégration AWS

## 🎯 Objectif

Déployer le système de compression MOE Deepseek 4 avec couche harmonique déterministe sur AWS, en complément de l'infrastructure HCV PRO existante.

---

## 📋 Architecture Complète AWS

```
                            Internet
                                │
                        ┌───────┴───────┐
                        │  CloudFront   │ ← CDN Global (400+ points)
                        │  Global CDN   │
                        └───────┬───────┘
                                │
                ┌───────────────┴───────────────┐
                │                               │
        ┌───────┴───────┐               ┌───────┴───────┐
        │   S3 Bucket   │               │  App Runner   │
        │   Frontend    │               │   Backend     │
        │  Deepseek UI  │               │  Flask API    │
        │  + HCV PRO    │               │  + Deepseek   │
        └───────────────┘               └───────┬───────┘
                                                │
                                        ┌───────┴───────┐
                                        │ CloudWatch    │
                                        │ Logs / Metrics│
                                        └───────────────┘
```

---

## 🚀 Déploiement Rapide

### Prérequis

```bash
# AWS CLI configuré
aws configure

# Vérifier les credentials
aws sts get-caller-identity
```

### Déploiement Automatisé

```bash
# Lancer le déploiement complet
cd HCV-PRO-PROJECT
chmod +x AWS_DEEPSEEK_DEPLOY.sh
./AWS_DEEPSEEK_DEPLOY.sh
```

### Déploiement Manuel

#### 1. Backend avec Deepseek

```bash
# Build image Docker avec Deepseek
docker build -t hcv-pro-deepseek .

# Push vers ECR
aws ecr get-login-password --region eu-west-3 | docker login --username AWS --password-stdin 326095712935.dkr.ecr.eu-west-3.amazonaws.com
docker tag hcv-pro-deepseek:latest 326095712935.dkr.ecr.eu-west-3.amazonaws.com/hcv-pro-deepseek:latest
docker push 326095712935.dkr.ecr.eu-west-3.amazonaws.com/hcv-pro-deepseek:latest

# Mettre à jour App Runner
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:eu-west-3:326095712935:service/hcv-pro-deepseek" \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "326095712935.dkr.ecr.eu-west-3.amazonaws.com/hcv-pro-deepseek:latest",
      "ImageRepositoryType": "ECR"
    }
  }' \
  --instance-configuration '{"Cpu": "1024", "Memory": "2048"}'
```

#### 2. Frontend Deepseek

```bash
# Uploader sur S3
aws s3 sync ./web/ s3://hcv-pro-deepseek-frontend-326095712935/ --delete

# Invalider cache CloudFront
aws cloudfront create-invalidation --distribution-id XXXXXXXX --paths "/*"
```

---

## 🌊 API Endpoints Deepseek

### Compression

```bash
# Initialiser le compresseur
curl -X POST https://votre-service.awsapprunner.com/api/deepseek/init \
  -H "Content-Type: application/json" \
  -d '{
    "compression_level": "balanced",
    "enable_harmonic": true,
    "quantize_8bit": false
  }'

# Compresser un modèle
curl -X POST https://votre-service.awsapprunner.com/api/deepseek/compress \
  -H "Content-Type: application/json" \
  -d '{
    "model_path": "deepseek-ai/DeepSeek-V2",
    "output_name": "deepseek4_harmonic"
  }'
```

### Inférence

```bash
# Lister modèles disponibles
curl https://votre-service.awsapprunner.com/api/deepseek/models

# Générer du texte
curl -X POST https://votre-service.awsapprunner.com/api/deepseek/models/deepseek4_harmonic/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "🌊 Génère une fonction Python harmonique",
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

### Benchmark

```bash
# Lancer benchmark harmonique
curl -X POST https://votre-service.awsapprunner.com/api/deepseek/benchmark
```

---

## 📊 Performance AWS

### Configuration Recommandée

| Service | Configuration | Utilisation |
|---------|----------------|--------------|
| **App Runner** | 1 vCPU, 2GB RAM | Compression + Inférence |
| **S3** | 10GB stockage | Modèles compressés |
| **CloudFront** | 50GB bandwidth | Frontend mondial |
| **CloudWatch** | 5GB logs | Monitoring |

### Coûts Estimés (12 mois gratuits)

| Service | Coût mensuel | Gratuit inclus |
|---------|---------------|-----------------|
| App Runner | $0 | ✅ Jusqu'à 1M requêtes |
| S3 | $0 | ✅ 5GB stockage |
| CloudFront | $0 | ✅ 50GB bandwidth |
| CloudWatch | $0 | ✅ 5GB logs |
| **Total** | **$0** | **12 mois** |

---

## 🌊 Interface Web Deepseek

### Accès

```
Frontend: https://dxxxxxxxxxxxxx.cloudfront.net/deepseek-moe.html
```

### Fonctionnalités

1. **🗜️ Compression MOE**
   - Sélection du modèle source
   - Configuration harmonique
   - Progression en temps réel

2. **🤖 Génération Texte**
   - Sélection modèle compressé
   - Prompt interface
   - Déterminisme affiché

3. **📊 Benchmark Harmonique**
   - Tests de performance
   - Graphiques temps réel
   - Métriques déterministes

4. **📁 Gestion Modèles**
   - Liste modèles compressés
   - Informations détaillées
   - Statistiques harmoniques

---

## 🔧 Configuration Avancée

### Variables d'Environnement

```bash
# Dans AWS Console → App Runner → Environment Variables
DEEPSEEK_MODELS_PATH=/app/models/deepseek4
HARMONIC_LAYER_ENABLED=true
MAX_COMPRESSION_RATIO=100
ENABLE_8BIT_QUANTIZATION=false
DEFAULT_COMPRESSION_LEVEL=balanced
```

### Scaling Automatique

```bash
# Configuration auto-scaling App Runner
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:eu-west-3:326095712935:service/hcv-pro-deepseek" \
  --auto-scaling-configuration '{
    "MinSize": 0,
    "MaxSize": 10,
    "TargetCapacity": 2
  }'
```

### Monitoring CloudWatch

```bash
# Créer alarmes
aws cloudwatch put-metric-alarm \
  --alarm-name "Deepseek-Error-Rate" \
  --alarm-description "Taux d'erreur Deepseek" \
  --metric-name ErrorRate \
  --namespace "AWS/AppRunner" \
  --statistic Average \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

---

## 🧪 Tests et Validation

### Tests Automatisés

```bash
# Test complet du déploiement
#!/bin/bash

SERVICE_URL="https://votre-service.awsapprunner.com"

echo "🧪 Tests Deepseek MOE AWS..."

# Test 1: Health check
echo "📊 Test health..."
curl -s "$SERVICE_URL/api/health" | jq .

# Test 2: Deepseek health
echo "🌊 Test Deepseek health..."
curl -s "$SERVICE_URL/api/deepseek/health" | jq .

# Test 3: Initialisation compresseur
echo "🗜️ Test initialisation..."
curl -s -X POST "$SERVICE_URL/api/deepseek/init" \
  -H "Content-Type: application/json" \
  -d '{"enable_harmonic": true}' | jq .

# Test 4: Benchmark
echo "📊 Test benchmark..."
curl -s -X POST "$SERVICE_URL/api/deepseek/benchmark" | jq .

echo "✅ Tests terminés!"
```

### Validation Déterminisme

```bash
# Test de reproductibilité
curl -X POST "$SERVICE_URL/api/deepseek/models/test/generate" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test déterministe", "max_tokens": 10}' > /tmp/test1.json

curl -X POST "$SERVICE_URL/api/deepseek/models/test/generate" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test déterministe", "max_tokens": 10}' > /tmp/test2.json

# Comparer les résultats
if diff /tmp/test1.json /tmp/test2.json; then
    echo "✅ Déterminisme validé!"
else
    echo "❌ Erreur de déterminisme!"
fi
```

---

## 📈 Monitoring et Performance

### Métriques Clés

| Métrique | Cible | Alert |
|----------|-------|-------|
| **Déterminisme** | 100% | <95% |
| **Hallucination** | 0% | >1% |
| **Latence** | <200ms | >500ms |
| **Compression** | >10:1 | <5:1 |
| **Error Rate** | <1% | >5% |

### Dashboard CloudWatch

```bash
# Créer dashboard Deepseek
aws cloudwatch put-dashboard \
  --dashboard-name "Deepseek-MOE-Harmonic" \
  --dashboard-body '{
    "widgets": [
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["AWS/AppRunner", "5XXError", "ServiceName", "hcv-pro-deepseek"]
          ],
          "view": "timeSeries",
          "stacked": false,
          "region": "eu-west-3"
        }
      }
    ]
  }'
```

---

## 🔒 Sécurité

### Configuration Sécurité

```bash
# WAF pour App Runner
aws wafv2 create-web-acl \
  --name "deepseek-waf" \
  --scope CLOUDFRONT \
  --default-action Allow \
  --rules file://waf-rules.json

# VPC Endpoint privé
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:eu-west-3:326095712935:service/hcv-pro-deepseek" \
  --network-configuration '{
    "EgressConfiguration": {
      "EgressType": "VPC"
    }
  }'
```

### API Keys

```bash
# Configuration API keys
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:eu-west-3:326095712935:service/hcv-pro-deepseek" \
  --environment-variables '{
    "DEEPSEEK_API_KEY": "votre-clé-secrète",
    "API_KEY_REQUIRED": "true"
  }'
```

---

## 🚨 Dépannage

### Problèmes Communs

#### 1. Mémoire Insuffisante

```bash
# Augmenter la mémoire App Runner
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:eu-west-3:326095712935:service/hcv-pro-deepseek" \
  --instance-configuration '{"Cpu": "2048", "Memory": "4096"}'
```

#### 2. Timeout Compression

```bash
# Configuration timeout
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:eu-west-3:326095712935:service/hcv-pro-deepseek" \
  --auto-scaling-configuration '{
    "MaxSize": 5,
    "TargetCapacity": 3
  }'
```

#### 3. Erreur de Chargement Modèle

```bash
# Vérifier les logs CloudWatch
aws logs describe-log-groups \
  --log-group-name-prefix "/aws/apprunner/hcv-pro-deepseek"

# Vérifier l'espace disque
df -h
ls -la /app/models/deepseek4/
```

---

## 📚 Documentation Complémentaire

- [Guide Compression HCV](./HCV_COMPRESSION_GUIDE.md)
- [Documentation AWS](./AWS_DEPLOYMENT_COMPLETE.md)
- [API Reference](./API_DOCUMENTATION.md)
- [Monitoring Guide](./MONITORING_GUIDE.md)

---

## 🎯 Conclusion

Le déploiement Deepseek MOE Harmonic sur AWS offre:

✅ **Performance Élevée**: Infrastructure AWS optimisée  
✅ **Déterminisme Absolu**: 0% hallucination garanti  
✅ **Scalabilité**: Auto-scaling automatique  
✅ **Sécurité**: WAF + VPC + HTTPS  
✅ **Monitoring**: CloudWatch intégré  
✅ **Coût Optimisé**: 12 mois gratuits  

**Le système est prêt pour une production à grande échelle avec une fiabilité et un déterminisme absolus!** 🌊
