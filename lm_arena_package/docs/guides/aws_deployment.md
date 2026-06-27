# DÃ©ploiement AWS - Harmonic AI SaaS

Guide de dÃ©ploiement du dashboard SaaS Harmonic AI sur AWS avec intÃ©gration des services LM Arena existants.

## ðŸ“‹ PrÃ©requis

### Compte AWS
- Compte AWS avec accÃ¨s aux services suivants :
  - ECS (Elastic Container Service)
  - RDS (PostgreSQL)
  - ElastiCache (Redis)
  - S3 (Simple Storage Service)
  - CloudFront
  - WAF (Web Application Firewall)
  - IAM (Identity and Access Management)

### Outils locaux
- AWS CLI configurÃ© (`aws configure`)
- Docker Desktop
- Git
- Python 3.8+

### Services existants
- API DeepSeek AWS : `http://__EC2_IP__:8000`
- Services harmoniques audio/vidÃ©o
- HCV-PROF (service compression)

## ðŸ—ï¸ Architecture AWS

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    AWS CloudFront (CDN)                     â”‚
â”‚                    https://harmonic-ai.com                  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                        â”‚
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    AWS WAF (Protection)                      â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                        â”‚
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚              Application Load Balancer (ALB)                 â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
               â”‚                              â”‚
    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”       â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
    â”‚   ECS Fargate       â”‚       â”‚   ECS Fargate       â”‚
    â”‚   Frontend Service  â”‚       â”‚   Backend Service   â”‚
    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜       â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
               â”‚                              â”‚
    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”       â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
    â”‚   S3 Bucket         â”‚       â”‚   RDS PostgreSQL   â”‚
    â”‚   Static Assets     â”‚       â”‚   Main Database     â”‚
    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜       â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                          â”‚
                               â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                               â”‚   ElastiCache Redis â”‚
                               â”‚   Cache & Celery    â”‚
                               â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## ðŸš€ DÃ©ploiement Ã©tape par Ã©tape

### Ã‰tape 1: PrÃ©paration des images Docker

```bash
# Construire l'image backend
cd harmonic_saas
docker build -t harmonic-saas-backend:latest .

# Construire l'image frontend
cd frontend
docker build -t harmonic-saas-frontend:latest -f Dockerfile.frontend .

# Taguer les images pour ECR
docker tag harmonic-saas-backend:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/harmonic-saas-backend:latest
docker tag harmonic-saas-frontend:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/harmonic-saas-frontend:latest
```

### Ã‰tape 2: Configuration ECR (Elastic Container Registry)

```bash
# CrÃ©er les repositories ECR
aws ecr create-repository --repository-name harmonic-saas-backend
aws ecr create-repository --repository-name harmonic-saas-frontend

# Authentifier Docker avec ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Pousser les images
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/harmonic-saas-backend:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/harmonic-saas-frontend:latest
```

### Ã‰tape 3: CrÃ©ation des ressources RDS

```bash
# CrÃ©er le groupe de sÃ©curitÃ©
aws ec2 create-security-group \
    --group-name harmonic-saas-db-sg \
    --description "Security group for Harmonic SaaS database"

# CrÃ©er la base de donnÃ©es RDS
aws rds create-db-instance \
    --db-instance-identifier harmonic-saas-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 15.3 \
    --master-username harmonic \
    --master-user-password "VotreMotDePasseComplexe123!" \
    --allocated-storage 20 \
    --storage-type gp3 \
    --backup-retention-period 7 \
    --multi-az false \
    --publicly-accessible false \
    --vpc-security-group-ids sg-xxxxxxxx \
    --db-subnet-group-name default-vpc-xxxxxx
```

### Ã‰tape 4: Configuration ElastiCache Redis

```bash
# CrÃ©er le cluster Redis
aws elasticache create-cache-cluster \
    --cache-cluster-id harmonic-saas-cache \
    --cache-node-type cache.t3.micro \
    --engine redis \
    --engine-version 7.0 \
    --num-cache-nodes 1 \
    --cache-parameter-group default.redis7 \
    --snapshot-retention-limit 3 \
    --security-group-ids sg-xxxxxxxx
```

### Ã‰tape 5: CrÃ©ation du bucket S3

```bash
# CrÃ©er le bucket pour les fichiers uploadÃ©s
aws s3api create-bucket \
    --bucket harmonic-saas-files-$(date +%s) \
    --region us-east-1 \
    --create-bucket-configuration LocationConstraint=us-east-1

# Configurer les politiques CORS
aws s3api put-bucket-cors \
    --bucket harmonic-saas-files-xxxxxx \
    --cors-configuration '{
        "CORSRules": [
            {
                "AllowedOrigins": ["*"],
                "AllowedMethods": ["GET", "POST", "PUT", "DELETE"],
                "AllowedHeaders": ["*"],
                "ExposeHeaders": ["ETag"],
                "MaxAgeSeconds": 3000
            }
        ]
    }'
```

### Ã‰tape 6: DÃ©ploiement ECS Fargate

```bash
# CrÃ©er le cluster ECS
aws ecs create-cluster --cluster-name harmonic-saas-cluster

# CrÃ©er la task definition backend
aws ecs register-task-definition \
    --family harmonic-saas-backend \
    --network-mode awsvpc \
    --requires-compatibilities FARGATE \
    --cpu 1024 \
    --memory 2048 \
    --execution-role-arn arn:aws:iam::123456789012:role/ecsTaskExecutionRole \
    --container-definitions '[
        {
            "name": "backend",
            "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/harmonic-saas-backend:latest",
            "portMappings": [{"containerPort": 9000, "hostPort": 9000, "protocol": "tcp"}],
            "environment": [
                {"name": "ENVIRONMENT", "value": "production"},
                {"name": "DATABASE_URL", "value": "postgresql://harmonic:password@harmonic-saas-db.xxxxxx.us-east-1.rds.amazonaws.com:5432/harmonic_saas"},
                {"name": "REDIS_URL", "value": "redis://harmonic-saas-cache.xxxxxx.ng.0001.use1.cache.amazonaws.com:6379/0"},
                {"name": "LM_ARENA_SERVICE_URL", "value": "http://__EC2_IP__:8000"},
                {"name": "AWS_S3_BUCKET", "value": "harmonic-saas-files-xxxxxx"}
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/harmonic-saas",
                    "awslogs-region": "us-east-1",
                    "awslogs-stream-prefix": "backend"
                }
            }
        }
    ]'

# CrÃ©er la task definition frontend
aws ecs register-task-definition \
    --family harmonic-saas-frontend \
    --network-mode awsvpc \
    --requires-compatibilities FARGATE \
    --cpu 512 \
    --memory 1024 \
    --execution-role-arn arn:aws:iam::123456789012:role/ecsTaskExecutionRole \
    --container-definitions '[
        {
            "name": "frontend",
            "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/harmonic-saas-frontend:latest",
            "portMappings": [{"containerPort": 80, "hostPort": 80, "protocol": "tcp"}],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/harmonic-saas",
                    "awslogs-region": "us-east-1",
                    "awslogs-stream-prefix": "frontend"
                }
            }
        }
    ]'
```

### Ã‰tape 7: Configuration Load Balancer et Services

```bash
# CrÃ©er l'Application Load Balancer
aws elbv2 create-load-balancer \
    --name harmonic-saas-alb \
    --subnets subnet-xxxxxx subnet-yyyyyy \
    --security-groups sg-xxxxxxxx \
    --scheme internet-facing \
    --type application

# CrÃ©er les target groups
aws elbv2 create-target-group \
    --name harmonic-backend-tg \
    --protocol HTTP \
    --port 9000 \
    --vpc-id vpc-xxxxxx \
    --health-check-path /health \
    --health-check-interval-seconds 30 \
    --target-type ip

aws elbv2 create-target-group \
    --name harmonic-frontend-tg \
    --protocol HTTP \
    --port 80 \
    --vpc-id vpc-xxxxxx \
    --health-check-path / \
    --health-check-interval-seconds 30 \
    --target-type ip

# CrÃ©er les listeners
aws elbv2 create-listener \
    --load-balancer-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/harmonic-saas-alb/xxxxxxxx \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/harmonic-frontend-tg/xxxxxxxx

# CrÃ©er les services ECS
aws ecs create-service \
    --cluster harmonic-saas-cluster \
    --service-name backend-service \
    --task-definition harmonic-saas-backend:1 \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxxx,subnet-yyyyyy],securityGroups=[sg-xxxxxxxx],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/harmonic-backend-tg/xxxxxxxx,containerName=backend,containerPort=9000"

aws ecs create-service \
    --cluster harmonic-saas-cluster \
    --service-name frontend-service \
    --task-definition harmonic-saas-frontend:1 \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxxx,subnet-yyyyyy],securityGroups=[sg-xxxxxxxx],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/harmonic-frontend-tg/xxxxxxxx,containerName=frontend,containerPort=80"
```

### Ã‰tape 8: Configuration CloudFront (CDN)

```bash
# CrÃ©er la distribution CloudFront
aws cloudfront create-distribution \
    --origin-domain-name harmonic-saas-alb-xxxxxx.us-east-1.elb.amazonaws.com \
    --default-root-object index.html \
    --enabled \
    --comment "Harmonic AI SaaS CDN" \
    --default-cache-behavior '{
        "TargetOriginId": "harmonic-saas-alb",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"],
        "CachedMethods": ["GET", "HEAD", "OPTIONS"],
        "ForwardedValues": {
            "QueryString": true,
            "Cookies": {"Forward": "all"}
        },
        "MinTTL": 0,
        "DefaultTTL": 86400,
        "MaxTTL": 31536000
    }'
```

### Ã‰tape 9: Configuration WAF (Web Application Firewall)

```bash
# CrÃ©er le Web ACL
aws wafv2 create-web-acl \
    --name harmonic-saas-waf \
    --scope REGIONAL \
    --default-action Allow={} \
    --visibility-config '{
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "harmonic-saas-waf"
    }' \
    --rules '[
        {
            "Name": "AWSManagedRulesCommonRuleSet",
            "Priority": 1,
            "Statement": {"ManagedRuleGroupStatement": {"VendorName": "AWS", "Name": "AWSManagedRulesCommonRuleSet"}},
            "OverrideAction": {"None": {}},
            "VisibilityConfig": {
                "SampledRequestsEnabled": true,
                "CloudWatchMetricsEnabled": true,
                "MetricName": "AWSManagedRulesCommonRuleSet"
            }
        },
        {
            "Name": "RateLimit",
            "Priority": 2,
            "Statement": {"RateBasedStatement": {"Limit": 2000, "AggregateKeyType": "IP"}},
            "Action": {"Block": {}},
            "VisibilityConfig": {
                "SampledRequestsEnabled": true,
                "CloudWatchMetricsEnabled": true,
                "MetricName": "RateLimit"
            }
        }
    ]'

# Associer le WAF Ã  l'ALB
aws wafv2 associate-web-acl \
    --web-acl-arn arn:aws:wafv2:us-east-1:123456789012:regional/webacl/harmonic-saas-waf/xxxxxxxx \
    --resource-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/harmonic-saas-alb/xxxxxxxx
```

### Ã‰tape 10: Configuration DNS (Route 53)

```bash
# CrÃ©er l'enregistrement A
aws route53 change-resource-record-sets \
    --hosted-zone-id ZXXXXXXXXXXXXX \
    --change-batch '{
        "Changes": [
            {
                "Action": "CREATE",
                "ResourceRecordSet": {
                    "Name": "harmonic-ai.com",
                    "Type": "A",
                    "AliasTarget": {
                        "HostedZoneId": "Z2FDTNDATAQYW2",
                        "DNSName": "dxxxxxxxxxxxxx.cloudfront.net",
                        "EvaluateTargetHealth": false
                    }
                }
            }
        ]
    }'

# CrÃ©er l'enregistrement CNAME pour www
aws route53 change-resource-record-sets \
    --hosted-zone-id ZXXXXXXXXXXXXX \
    --change-batch '{
        "Changes": [
            {
                "Action": "CREATE",
                "ResourceRecordSet": {
                    "Name": "www.harmonic-ai.com",
                    "Type": "CNAME",
                    "TTL": 300,
                    "ResourceRecords": [{"Value": "harmonic-ai.com"}]
                }
            }
        ]
    }'
```

## ðŸ”§ Configuration des variables d'environnement

### Backend ECS Task Definition
```json
{
  "environment": [
    {"name": "ENVIRONMENT", "value": "production"},
    {"name": "DEBUG", "value": "false"},
    {"name": "DATABASE_URL", "value": "postgresql://harmonic:password@harmonic-saas-db.xxxxxx.us-east-1.rds.amazonaws.com:5432/harmonic_saas"},
    {"name": "REDIS_URL", "value": "redis://harmonic-saas-cache.xxxxxx.ng.0001.use1.cache.amazonaws.com:6379/0"},
    {"name": "MONGODB_URL", "value": "mongodb://localhost:27017/harmonic_saas"},
    {"name": "LM_ARENA_SERVICE_URL", "value": "http://__EC2_IP__:8000"},
    {"name": "AUDIO_SERVICE_URL", "value": "http://localhost:9017"},
    {"name": "VIDEO_SERVICE_URL", "value": "http://localhost:9018"},
    {"name": "JWT_SECRET_KEY", "value": "votre_clÃ©_secrÃ¨te_trÃ¨s_longue_et_complexe"},
    {"name": "AWS_S3_BUCKET", "value": "harmonic-saas-files-xxxxxx"},
    {"name": "STRIPE_SECRET_KEY", "value": "sk_live_xxxxxxxx"},
    {"name": "SENTRY_DSN", "value": "https://xxxxxxxx@sentry.io/xxxxxx"}
  ]
}
```

### Frontend Build Variables
```bash
# Variables Ã  injecter lors du build
REACT_APP_API_URL=https://api.harmonic-ai.com
REACT_APP_STRIPE_PUBLIC_KEY=pk_live_xxxxxxxx
REACT_APP_SENTRY_DSN=https://xxxxxxxx@sentry.io/xxxxxx
REACT_APP_GA_TRACKING_ID=UA-XXXXXXXX-X
```

## ðŸ“Š Monitoring et ObservabilitÃ©

### CloudWatch Logs
```bash
# CrÃ©er le groupe de logs
aws logs create-log-group --log-group-name /ecs/harmonic-saas

# Configurer les mÃ©triques
aws cloudwatch put-metric-alarm \
    --alarm-name harmonic-saas-high-cpu \
    --metric-name CPUUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=ClusterName,Value=harmonic-saas-cluster Name=ServiceName,Value=backend-service \
    --evaluation-periods 2 \
    --alarm-actions arn:aws:sns:us-east-1:123456789012:alarm-topic
```

### X-Ray Tracing
```bash
# Activer X-Ray pour ECS
aws ecs put-account-setting \
    --name awsvpcTrunking \
    --value enabled

aws ecs put-account-setting \
    --name containerInsights \
    --value enabled
```

## ðŸ”’ SÃ©curitÃ© AWS

### IAM Roles
```bash
# CrÃ©er le rÃ´le d'exÃ©cution ECS
aws iam create-role \
    --role-name ecsTaskExecutionRole \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        ]
    }'

# Attacher les politiques
aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonRDSFullAccess
```

### Secrets Manager
```bash
# Stocker les secrets
aws secretsmanager create-secret \
    --name harmonic-saas-db-credentials \
    --secret-string '{
        "username": "harmonic",
        "password": "VotreMotDePasseComplexe123!",
        "host": "harmonic-saas-db.xxxxxx.us-east-1.rds.amazonaws.com",
        "port": 5432,
        "dbname": "harmonic_saas"
    }'
```

## ðŸš¢ CI/CD avec GitHub Actions

### Workflow `.github/workflows/deploy.yml`
```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

env:
  AWS_REGION: us-east-1
  ECR_REGISTRY: 123456789012.dkr.ecr.us-east-1.amazonaws.com
  ECR_REPOSITORY_BACKEND: harmonic-saas-backend
  ECR_REPOSITORY_FRONTEND: harmonic-saas-frontend
  ECS_CLUSTER: harmonic-saas-cluster
  ECS_SERVICE_BACKEND: backend-service
  ECS_SERVICE_FRONTEND: frontend-service

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout
      uses: actions/checkout@v3
      
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}
        
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1
      
    - name: Build and push backend image
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY_BACKEND:latest .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY_BACKEND:latest
        
    - name: Build and push frontend image
      run: |
        cd frontend
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY_FRONTEND:latest -f Dockerfile.frontend .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY_FRONTEND:latest
        
    - name: Deploy backend to ECS
      run: |
        aws ecs update-service \
          --cluster $ECS_CLUSTER \
          --service $ECS_SERVICE_BACKEND \
          --force-new-deployment \
          --region $AWS_REGION
          
    - name: Deploy frontend to ECS
      run: |
        aws ecs update-service \
          --cluster $ECS_CLUSTER \
          --service $ECS_SERVICE_FRONTEND \
          --force-new-deployment \
          --region $AWS_REGION
          
    - name: Verify deployment
      run: |
        echo "Backend URL: https://api.harmonic-ai.com/health"
        echo "Frontend URL: https://harmonic-ai.com"
```

## ðŸ§ª Tests de dÃ©ploiement

### VÃ©rification des services
```bash
# Test backend
curl -f https://api.harmonic-ai.com/health

# Test frontend
curl -f https://harmonic-ai.com

# Test intÃ©gration DeepSeek
curl -X POST https://api.harmonic-ai.com/api/v1/chat/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test de connexion"}'
```

### Tests de charge
```bash
# Installer artillery
npm install -g artillery

# ExÃ©cuter le test
artillery run load-test.yml
```

## ðŸ“ˆ Scaling et Optimisation

### Auto-scaling ECS
```bash
# Configurer l'auto-scaling
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/harmonic-saas-cluster/backend-service \
  --min-capacity 2 \
  --max-capacity 10

aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/harmonic-saas-cluster/backend-service \
  --policy-name cpu-scaling-policy \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "ScaleOutCooldown": 60,
    "ScaleInCooldown": 300
  }'
```

### Cache CloudFront
```bash
# Invalider le cache
aws cloudfront create-invalidation \
  --distribution-id EXXXXXXXXXXXXX \
  --paths "/*"
```

## ðŸ†˜ DÃ©pannage

### Logs ECS
```bash
# Voir les logs d'un service
aws logs filter-log-events \
  --log-group-name /ecs/harmonic-saas \
  --log-stream-name-prefix backend \
  --start-time $(date -d '1 hour ago' +%s)000

# Voir les Ã©vÃ©nements ECS
aws ecs describe-services \
  --cluster harmonic-saas-cluster \
  --services backend-service
```

### SantÃ© des instances
```bash
# VÃ©rifier la santÃ© des targets
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/harmonic-backend-tg/xxxxxxxx
```

### MÃ©triques CloudWatch
```bash
# Obtenir les mÃ©triques CPU
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ClusterName,Value=harmonic-saas-cluster Name=ServiceName,Value=backend-service \
  --start-time $(date -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

## ðŸ“ž Support

### Contacts AWS
- **Support AWS** : https://aws.amazon.com/contact-us/
- **Documentation ECS** : https://docs.aws.amazon.com/ecs/
- **Forum AWS** : https://forums.aws.amazon.com/

### Monitoring 24/7
- **CloudWatch Alarms** : ConfigurÃ©s pour CPU > 80%, erreurs > 1%
- **SNS Notifications** : Envoi d'alertes par email/SMS
- **Sentry** : Monitoring des erreurs applicatives

---

**Note importante** : Ce dÃ©ploiement intÃ¨gre les services LM Arena existants sur AWS. Assurez-vous que :
1. L'instance EC2 DeepSeek API est accessible
2. Les services harmoniques audio/vidÃ©o sont dÃ©marrÃ©s
3. Les politiques de sÃ©curitÃ© IAM sont correctement configurÃ©es
4. Les variables d'environnement sont correctement dÃ©finies