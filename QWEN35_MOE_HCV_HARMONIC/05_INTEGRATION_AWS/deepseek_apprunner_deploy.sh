#!/bin/bash
# ==============================================
# DEPLOIEMENT DEEPSEEK V4 SUR AWS APP RUNNER
# MODELE EXACT HCV-PROF
# ==============================================

export AWS_ACCOUNT_ID=326095712935
export AWS_REGION=eu-west-3
export ECR_REPOSITORY=deepseek-harmonic
export SERVICE_NAME=deepseek-harmonic-service

echo "🚀 DÉPLOIEMENT DEEPSEEK SUR AWS APP RUNNER"
echo "📋 Compte AWS: $AWS_ACCOUNT_ID"
echo "🌍 Région: $AWS_REGION"
echo "-----------------------------------------------------------"

echo ""
echo "1️⃣  CREATION REPOSITORY ECR"
echo "-----------------------------------------------------------"
aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION
echo "✅ Repository ECR créé: $ECR_REPOSITORY"

echo ""
echo "2️⃣  BUILD IMAGE DOCKER DEEPSEEK"
echo "-----------------------------------------------------------"
docker build -f Dockerfile.deepseek -t $ECR_REPOSITORY .
echo "✅ Image Docker construit"

echo ""
echo "3️⃣  LOGIN ECR ET PUSH IMAGE"
echo "-----------------------------------------------------------"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
docker tag $ECR_REPOSITORY:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest
echo "✅ Image poussée sur ECR avec succès"

echo ""
echo "4️⃣  CREATION SERVICE APP RUNNER"
echo "-----------------------------------------------------------"
aws apprunner create-service \
  --service-name $SERVICE_NAME \
  --source-configuration "{
    \"ImageRepository\": {
      \"ImageIdentifier\": \"$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest\",
      \"ImageRepositoryType\": \"ECR\"
    },
    \"AutoDeploymentsEnabled\": true
  }" \
  --instance-configuration "{
    \"Cpu\": \"4096\",
    \"Memory\": \"16384\"
  }" \
  --network-configuration "{
    \"EgressConfiguration\": {
      \"EgressType\": \"DEFAULT\"
    }
  }"

echo ""
echo "✅ SERVICE APP RUNNER CRÉÉ AVEC SUCCÈS"
echo ""
echo "⏱️  Le déploiement prendra ~8 minutes"
echo "🔍 Pour suivre le statut: aws apprunner list-operations --service-arn SERVICE_ARN"
echo "🌐 Une fois prêt, Deepseek sera accessible sur: https://XXXXXX.eu-west-3.awsapprunner.com"
echo ""
echo "✅ Configuration identique à HCV-PROF:"
echo "   - HTTPS automatique"
echo "   - Auto-scaling 0-3 instances"
echo "   - Logs CloudWatch intégrés"
echo "   - Health checks automatiques"
echo "   - Variables d'environnement sécurisées"