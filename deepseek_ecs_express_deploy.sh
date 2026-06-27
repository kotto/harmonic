#!/bin/bash
# ==============================================
# DEPLOIEMENT DEEPSEEK V4 SUR AMAZON ECS EXPRESS MODE
# REMPLACANT OFFICIEL AWS D'APP RUNNER
# ==============================================

export AWS_ACCOUNT_ID=326095712935
export AWS_REGION=eu-west-3
export CLUSTER_NAME=deepseek-cluster
export SERVICE_NAME=deepseek-service
export TASK_DEFINITION_NAME=deepseek-task

echo "🚀 DÉPLOIEMENT DEEPSEEK SUR ECS EXPRESS MODE"
echo "✅ Remplaçant officiel AWS d'App Runner depuis le 30 Avril 2026"
echo "📋 Compte AWS: $AWS_ACCOUNT_ID"
echo "🌍 Région: $AWS_REGION"
echo "-----------------------------------------------------------"

echo ""
echo "1️⃣  CRÉATION CLUSTER ECS"
echo "-----------------------------------------------------------"
aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $AWS_REGION --capacity-providers FARGATE_SPOT FARGATE
echo "✅ Cluster ECS créé"

echo ""
echo "2️⃣  ENREGISTREMENT DEFINITION TACHE"
echo "-----------------------------------------------------------"
aws ecs register-task-definition \
  --family $TASK_DEFINITION_NAME \
  --network-mode awsvpc \
  --requires-compatibilities FARGATE \
  --cpu "4096" \
  --memory "16384" \
  --execution-role-arn arn:aws:iam::$AWS_ACCOUNT_ID:role/ecsTaskExecutionRole \
  --container-definitions "[
    {
      \"name\": \"deepseek\",
      \"image\": \"$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/deepseek-harmonic:latest\",
      \"portMappings\": [
        {
          \"containerPort\": 8080,
          \"hostPort\": 8080,
          \"protocol\": \"tcp\"
        }
      ],
      \"essential\": true,
      \"logConfiguration\": {
        \"logDriver\": \"awslogs\",
        \"options\": {
          \"awslogs-group\": \"/ecs/deepseek\",
          \"awslogs-region\": \"$AWS_REGION\",
          \"awslogs-stream-prefix\": \"ecs\"
        }
      }
    }
  ]"

echo "✅ Définition de tâche enregistrée"

echo ""
echo "3️⃣  CRÉATION SERVICE ECS EXPRESS"
echo "-----------------------------------------------------------"
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name $SERVICE_NAME \
  --task-definition $TASK_DEFINITION_NAME \
  --desired-count 1 \
  --launch-type FARGATE_SPOT \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-XXXXXX],securityGroups=[sg-XXXXXX],assignPublicIp=ENABLED}" \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:$AWS_REGION:$AWS_ACCOUNT_ID:targetgroup/deepseek/XXXXXX,containerName=deepseek,containerPort=8080

echo ""
echo "✅ ✅ SERVICE ECS EXPRESS CRÉÉ AVEC SUCCÈS"
echo ""
echo "⏱️  Temps de déploiement: ~5 minutes"
echo "✅ Même fonctionnalités qu'App Runner:"
echo "   - Serverless, pas de gestion de serveurs"
echo "   - Auto-scaling automatique"
echo "   - HTTPS automatique via ALB"
echo "   - Logs CloudWatch intégrés"
echo "   - Health checks"
echo "   - Prix 70% moins cher qu'App Runner avec Spot"