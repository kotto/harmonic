#!/bin/bash
# 🚀 SCRIPTS DE DÉPLOIEMENT AWS - HARMONIC AI COMPLET
# Déploiement automatisé de l'infrastructure complète

set -e  # Arrêter en cas d'erreur

# Configuration
AWS_REGION="us-east-1"
VPC_CIDR="10.0.0.0/16"
KEY_NAME="harmonic-ai-key"
PROJECT_NAME="harmonic-ai"
ENVIRONMENT="production"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check AWS CLI
check_aws_cli() {
    log "Vérification AWS CLI..."
    if ! command -v aws &> /dev/null; then
        error "AWS CLI n'est pas installé. Veuillez l'installer: https://aws.amazon.com/cli/"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials non configurées. Exécutez: aws configure"
        exit 1
    fi
    
    log "AWS CLI vérifié avec succès"
}

# Create VPC
create_vpc() {
    log "Création VPC..."
    
    VPC_ID=$(aws ec2 create-vpc \
        --cidr-block $VPC_CIDR \
        --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=$PROJECT_NAME-vpc},{Key=Project,Value=$PROJECT_NAME},{Key=Environment,Value=$ENVIRONMENT}]" \
        --query 'Vpc.VpcId' \
        --output text)
    
    aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support --enable-dns-hostnames
    
    # Create Internet Gateway
    IGW_ID=$(aws ec2 create-internet-gateway \
        --tag-specifications "ResourceType=internet-gateway,Tags=[{Key=Name,Value=$PROJECT_NAME-igw},{Key=Project,Value=$PROJECT_NAME},{Key=Environment,Value=$ENVIRONMENT}]" \
        --query 'InternetGateway.InternetGatewayId' \
        --output text)
    
    aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID
    
    # Create Route Table
    RT_ID=$(aws ec2 create-route-table \
        --vpc-id $VPC_ID \
        --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=$PROJECT_NAME-rt},{Key=Project,Value=$PROJECT_NAME},{Key=Environment,Value=$ENVIRONMENT}]" \
        --query 'RouteTable.RouteTableId' \
        --output text)
    
    aws ec2 create-route --route-table-id $RT_ID --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID
    
    log "VPC créé: $VPC_ID"
    echo $VPC_ID > vpc_id.txt
}

# Create Subnets
create_subnets() {
    log "Création subnets..."
    
    VPC_ID=$(cat vpc_id.txt)
    
    # Public subnets
    PUBLIC_SUBNET_1_ID=$(aws ec2 create-subnet \
        --vpc-id $VPC_ID \
        --cidr-block 10.0.1.0/24 \
        --availability-zone us-east-1a \
        --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=$PROJECT_NAME-public-1a},{Key=Project,Value=$PROJECT_NAME},{Key=Environment,Value=$ENVIRONMENT},{Key=Type,Value=public}]" \
        --query 'Subnet.SubnetId' \
        --output text)
    
    PUBLIC_SUBNET_2_ID=$(aws ec2 create-subnet \
        --vpc-id $VPC_ID \
        --cidr-block 10.0.2.0/24 \
        --availability-zone us-east-1b \
        --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=$PROJECT_NAME-public-1b},{Key=Project,Value=$PROJECT_NAME},{Key=Environment,Value=$ENVIRONMENT},{Key=Type,Value=public}]" \
        --query 'Subnet.SubnetId' \
        --output text)
    
    PUBLIC_SUBNET_3_ID=$(aws ec2 create-subnet \
        --vpc-id $VPC_ID \
        --cidr-block 10.0.3.0/24 \
        --availability-zone us-east-1c \
        --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=$PROJECT_NAME-public-1c},{Key=Project,Value=$PROJECT_NAME},{Key=Environment,Value=$ENVIRONMENT},{Key=Type,Value=public}]" \
        --query 'Subnet.SubnetId' \
        --output text)
    
    # Private subnets
    PRIVATE_SUBNET_1_ID=$(aws ec2 create-subnet \
        --vpc-id $VPC_ID \
        --cidr-block 10.0.11.0/24 \
        --availability-zone us-east-1a \
        --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=$PROJECT_NAME-private-1a},{Key=Project,Value=$PROJECT_NAME},{Key=Environment,Value=$ENVIRONMENT},{Key=Type,Value=private}]" \
        --query 'Subnet.SubnetId' \
        --output text)
    
    PRIVATE_SUBNET_2_ID=$(aws ec2 create-subnet \
        --vpc-id $VPC_ID \
        --cidr-block 10.0.12.0/24 \
        --availability-zone us-east-1b \
        --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=$PROJECT_NAME-private-1b},{Key=Project,Value=$PROJECT_NAME},{Key=Environment,Value=$ENVIRONMENT},{Key=Type,Value=private}]" \
        --query 'Subnet.SubnetId' \
        --output text)
    
    PRIVATE_SUBNET_3_ID=$(aws ec2 create-subnet \
        --vpc-id $VPC_ID \
        --cidr-block 10.0.13.0/24 \
        --availability-zone us-east-1c \
        --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=$PROJECT_NAME-private-1c},{Key=Project,Value=$PROJECT_NAME},{Key=Environment,Value=$ENVIRONMENT},{Key=Type,Value=private}]" \
        --query 'Subnet.SubnetId' \
        --output text)
    
    # Create NAT Gateway
    NAT_EIP_ID=$(aws ec2 allocate-address \
        --tag-specifications "ResourceType=elastic-ip,Tags=[{Key=Name,Value=$PROJECT_NAME-nat-eip},{Key=Project,Value=$PROJECT_NAME},{Key=Environment,Value=$ENVIRONMENT}]" \
        --query 'AllocationId' \
        --output text)
    
    NAT_GW_ID=$(aws ec2 create-nat-gateway \
        --subnet-id $PUBLIC_SUBNET_1_ID \
        --allocation-id $NAT_EIP_ID \
        --tag-specifications "ResourceType=natgateway,Tags=[{Key=Name,Value=$PROJECT_NAME-nat-gw},{Key=Project,Value=$PROJECT_NAME},{Key=Environment,Value=$ENVIRONMENT}]" \
        --query 'NatGateway.NatGatewayId' \
        --output text)
    
    # Wait for NAT Gateway
    log "Attente création NAT Gateway..."
    aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GW_ID
    
    # Create route tables for private subnets
    PRIVATE_RT_ID=$(aws ec2 create-route-table \
        --vpc-id $VPC_ID \
        --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=$PROJECT_NAME-private-rt},{Key=Project,Value=$PROJECT_NAME},{Key=Environment,Value=$ENVIRONMENT}]" \
        --query 'RouteTable.RouteTableId' \
        --output text)
    
    aws ec2 create-route --route-table-id $PRIVATE_RT_ID --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT_GW_ID
    
    # Associate route tables
    aws ec2 associate-route-table --route-table-id $RT_ID --subnet-id $PUBLIC_SUBNET_1_ID
    aws ec2 associate-route-table --route-table-id $RT_ID --subnet-id $PUBLIC_SUBNET_2_ID
    aws ec2 associate-route-table --route-table-id $RT_ID --subnet-id $PUBLIC_SUBNET_3_ID
    
    aws ec2 associate-route-table --route-table-id $PRIVATE_RT_ID --subnet-id $PRIVATE_SUBNET_1_ID
    aws ec2 associate-route-table --route-table-id $PRIVATE_RT_ID --subnet-id $PRIVATE_SUBNET_2_ID
    aws ec2 associate-route-table --route-table-id $PRIVATE_RT_ID --subnet-id $PRIVATE_SUBNET_3_ID
    
    # Enable auto-assign public IP for public subnets
    aws ec2 modify-subnet-attribute --subnet-id $PUBLIC_SUBNET_1_ID --map-public-ip-on-launch
    aws ec2 modify-subnet-attribute --subnet-id $PUBLIC_SUBNET_2_ID --map-public-ip-on-launch
    aws ec2 modify-subnet-attribute --subnet-id $PUBLIC_SUBNET_3_ID --map-public-ip-on-launch
    
    log "Subnets créés avec succès"
    echo "$PUBLIC_SUBNET_1_ID,$PUBLIC_SUBNET_2_ID,$PUBLIC_SUBNET_3_ID" > public_subnets.txt
    echo "$PRIVATE_SUBNET_1_ID,$PRIVATE_SUBNET_2_ID,$PRIVATE_SUBNET_3_ID" > private_subnets.txt
}

# Create Security Groups
create_security_groups() {
    log "Création Security Groups..."
    
    VPC_ID=$(cat vpc_id.txt)
    
    # Web Security Group
    WEB_SG_ID=$(aws ec2 create-security-group \
        --group-name $PROJECT_NAME-web-sg \
        --description "Security group for web servers" \
        --vpc-id $VPC_ID \
        --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=$PROJECT_NAME-web-sg},{Key=Project,Value=$PROJECT_NAME},{Key=Environment,Value=$ENVIRONMENT}]" \
        --query 'GroupId' \
        --output text)
    
    aws ec2 authorize-security-group-ingress --group-id $WEB_SG_ID --protocol tcp --port 80 --cidr 0.0.0.0/0
    aws ec2 authorize-security-group-ingress --group-id $WEB_SG_ID --protocol tcp --port 443 --cidr 0.0.0.0/0
    aws ec2 authorize-security-group-ingress --group-id $WEB_SG_ID --protocol tcp --port 22 --cidr 0.0.0.0/0
    
    # App Security Group
    APP_SG_ID=$(aws ec2 create-security-group \
        --group-name $PROJECT_NAME-app-sg \
        --description "Security group for application servers" \
        --vpc-id $VPC_ID \
        --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=$PROJECT_NAME-app-sg},{Key=Project,Value=$PROJECT_NAME},{Key=Environment,Value=$ENVIRONMENT}]" \
        --query 'GroupId' \
        --output text)
    
    aws ec2 authorize-security-group-ingress --group-id $APP_SG_ID --protocol tcp --port 8000 --source-group-ids $WEB_SG_ID
    aws ec2 authorize-security-group-ingress --group-id $APP_SG_ID --protocol tcp --port 8080 --source-group-ids $WEB_SG_ID
    aws ec2 authorize-security-group-ingress --group-id $APP_SG_ID --protocol tcp --port 22 --cidr 0.0.0.0/0
    
    # GPU Security Group
    GPU_SG_ID=$(aws ec2 create-security-group \
        --group-name $PROJECT_NAME-gpu-sg \
        --description "Security group for GPU instances" \
        --vpc-id $VPC_ID \
        --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=$PROJECT_NAME-gpu-sg},{Key=Project,Value=$PROJECT_NAME},{Key=Environment,Value=$ENVIRONMENT}]" \
        --query 'GroupId' \
        --output text)
    
    aws ec2 authorize-security-group-ingress --group-id $GPU_SG_ID --protocol tcp --port 5000 --source-group-ids $APP_SG_ID
    aws ec2 authorize-security-group-ingress --group-id $GPU_SG_ID --protocol tcp --port 6000 --source-group-ids $APP_SG_ID
    aws ec2 authorize-security-group-ingress --group-id $GPU_SG_ID --protocol tcp --port 22 --cidr 0.0.0.0/0
    
    log "Security Groups créés avec succès"
    echo "$WEB_SG_ID,$APP_SG_ID,$GPU_SG_ID" > security_groups.txt
}

# Create IAM Role
create_iam_role() {
    log "Création IAM Role..."
    
    # Create trust policy
    cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
    
    # Create role
    ROLE_ARN=$(aws iam create-role \
        --role-name $PROJECT_NAME-ec2-role \
        --assume-role-policy-document file://trust-policy.json \
        --description "EC2 role for Harmonic AI" \
        --tags Key=Name,Value=$PROJECT_NAME-ec2-role Key=Project,Value=$PROJECT_NAME Key=Environment,Value=$ENVIRONMENT \
        --query 'Role.Arn' \
        --output text)
    
    # Attach policies
    aws iam attach-role-policy --role-name $PROJECT_NAME-ec2-role --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
    aws iam attach-role-policy --role-name $PROJECT_NAME-ec2-role --policy-arn arn:aws:iam::aws:policy/CloudWatchFullAccess
    aws iam attach-role-policy --role-name $PROJECT_NAME-ec2-role --policy-arn arn:aws:iam::aws:policy/AWSXRayFullAccess
    
    # Create instance profile
    aws iam create-instance-profile --instance-profile-name $PROJECT_NAME-ec2-profile
    
    # Wait for role propagation
    sleep 10
    
    aws iam add-role-to-instance-profile --instance-profile-name $PROJECT_NAME-ec2-profile --role-name $PROJECT_NAME-ec2-role
    
    log "IAM Role créé avec succès"
    echo "$ROLE_ARN" > iam_role.txt
}

# Create S3 Buckets
create_s3_buckets() {
    log "Création S3 Buckets..."
    
    # Main bucket
    aws s3api create-bucket \
        --bucket $PROJECT_NAME-knowledge-base \
        --region $AWS_REGION \
        --create-bucket-configuration LocationConstraint=$AWS_REGION
    
    # Models bucket
    aws s3api create-bucket \
        --bucket $PROJECT_NAME-models \
        --region $AWS_REGION \
        --create-bucket-configuration LocationConstraint=$AWS_REGION
    
    # Assets bucket
    aws s3api create-bucket \
        --bucket $PROJECT_NAME-assets \
        --region $AWS_REGION \
        --create-bucket-configuration LocationConstraint=$AWS_REGION
    
    # Backups bucket
    aws s3api create-bucket \
        --bucket $PROJECT_NAME-backups \
        --region $AWS_REGION \
        --create-bucket-configuration LocationConstraint=$AWS_REGION
    
    # Configure lifecycle policies
    cat > lifecycle-policy.json << EOF
{
    "Rules": [
        {
            "ID": "LifecycleRule",
            "Status": "Enabled",
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "STANDARD_IA"
                },
                {
                    "Days": 60,
                    "StorageClass": "GLACIER"
                },
                {
                    "Days": 180,
                    "StorageClass": "DEEP_ARCHIVE"
                }
            ]
        }
    ]
}
EOF
    
    aws s3api put-bucket-lifecycle-configuration \
        --bucket $PROJECT_NAME-knowledge-base \
        --lifecycle-configuration file://lifecycle-policy.json
    
    aws s3api put-bucket-lifecycle-configuration \
        --bucket $PROJECT_NAME-models \
        --lifecycle-configuration file://lifecycle-policy.json
    
    aws s3api put-bucket-lifecycle-configuration \
        --bucket $PROJECT_NAME-assets \
        --lifecycle-configuration file://lifecycle-policy.json
    
    log "S3 Buckets créés avec succès"
}

# Create EC2 Instances
create_ec2_instances() {
    log "Création EC2 Instances..."
    
    PRIVATE_SUBNETS=$(cat private_subnets.txt)
    SECURITY_GROUPS=$(cat security_groups.txt)
    IFS=',' read -ra PRIVATE_SUBNET_ARRAY <<< "$PRIVATE_SUBNETS"
    IFS=',' read -ra SECURITY_GROUPS_ARRAY <<< "$SECURITY_GROUPS"
    
    # GPU Instances for Mathstral + WizardMath
    for i in {1..2}; do
        INSTANCE_ID=$(aws ec2 run-instances \
            --image-id ami-0c02fb55956c7d3165 \
            --instance-type g4dn.xlarge \
            --key-name $KEY_NAME \
            --security-group-ids $SECURITY_GROUPS_ARRAY[2] \
            --subnet-id ${PRIVATE_SUBNET_ARRAY[$((i-1))]} \
            --iam-instance-profile Name=$PROJECT_NAME-ec2-profile \
            --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$PROJECT_NAME-gpu-$i},{Key=Project,Value=$PROJECT_NAME},{Key=Environment,Value=$ENVIRONMENT},{Key=Type,Value=gpu}]" \
            --user-data file://gpu-user-data.sh \
            --query 'Instances[0].InstanceId' \
            --output text)
        
        log "Instance GPU $i créée: $INSTANCE_ID"
    done
    
    # Visual Generation Instance
    VISUAL_INSTANCE_ID=$(aws ec2 run-instances \
        --image-id ami-0c02fb55956c7d3165 \
        --instance-type g5.xlarge \
        --key-name $KEY_NAME \
        --security-group-ids $SECURITY_GROUPS_ARRAY[2] \
        --subnet-id ${PRIVATE_SUBNET_ARRAY[0]} \
        --iam-instance-profile Name=$PROJECT_NAME-ec2-profile \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$PROJECT_NAME-visual},{Key=Project,Value=$PROJECT_NAME},{Key=Environment,Value=$ENVIRONMENT},{Key=Type,Value=visual}]" \
        --user-data file://visual-user-data.sh \
        --query 'Instances[0].InstanceId' \
        --output text)
    
    log "Instance Visual créée: $VISUAL_INSTANCE_ID"
    
    # API Instances
    for i in {1..2}; do
        API_INSTANCE_ID=$(aws ec2 run-instances \
            --image-id ami-0c02fb55956c7d3165 \
            --instance-type t3.large \
            --key-name $KEY_NAME \
            --security-group-ids $SECURITY_GROUPS_ARRAY[1] \
            --subnet-id ${PRIVATE_SUBNET_ARRAY[$((i-1))]} \
            --iam-instance-profile Name=$PROJECT_NAME-ec2-profile \
            --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$PROJECT_NAME-api-$i},{Key=Project,Value=$PROJECT_NAME},{Key=Environment,Value=$ENVIRONMENT},{Key=Type,Value=api}]" \
            --user-data file://api-user-data.sh \
            --query 'Instances[0].InstanceId' \
            --output text)
        
        log "Instance API $i créée: $API_INSTANCE_ID"
    done
    
    log "EC2 Instances créées avec succès"
}

# Create Load Balancer
create_load_balancer() {
    log "Création Load Balancer..."
    
    PUBLIC_SUBNETS=$(cat public_subnets.txt)
    IFS=',' read -ra PUBLIC_SUBNET_ARRAY <<< "$PUBLIC_SUBNETS"
    
    # Create Application Load Balancer
    LB_ARN=$(aws elbv2 create-load-balancer \
        --name $PROJECT_NAME-alb \
        --subnets ${PUBLIC_SUBNET_ARRAY[0]} ${PUBLIC_SUBNET_ARRAY[1]} ${PUBLIC_SUBNET_ARRAY[2]} \
        --security-groups $(cut -d',' -f1 security_groups.txt) \
        --scheme internet-facing \
        --type application \
        --ip-address-type ipv4 \
        --tags Key=Name,Value=$PROJECT_NAME-alb Key=Project,Value=$PROJECT_NAME Key=Environment,Value=$ENVIRONMENT \
        --query 'LoadBalancers[0].LoadBalancerArn' \
        --output text)
    
    # Create Target Groups
    API_TG_ARN=$(aws elbv2 create-target-group \
        --name $PROJECT_NAME-api-tg \
        --protocol HTTP \
        --port 8000 \
        --vpc-id $(cat vpc_id.txt) \
        --target-type instance \
        --health-check-path /health \
        --matcher HttpCode=200 \
        --query 'TargetGroups[0].TargetGroupArn' \
        --output text)
    
    GPU_TG_ARN=$(aws elbv2 create-target-group \
        --name $PROJECT_NAME-gpu-tg \
        --protocol HTTP \
        --port 5000 \
        --vpc-id $(cat vpc_id.txt) \
        --target-type instance \
        --health-check-path /health \
        --matcher HttpCode=200 \
        --query 'TargetGroups[0].TargetGroupArn' \
        --output text)
    
    VISUAL_TG_ARN=$(aws elbv2 create-target-group \
        --name $PROJECT_NAME-visual-tg \
        --protocol HTTP \
        --port 6000 \
        --vpc-id $(cat vpc_id.txt) \
        --target-type instance \
        --health-check-path /health \
        --matcher HttpCode=200 \
        --query 'TargetGroups[0].TargetGroupArn' \
        --output text)
    
    # Create Listener
    aws elbv2 create-listener \
        --load-balancer-arn $LB_ARN \
        --protocol HTTP \
        --port 80 \
        --default-actions Type=forward,TargetGroupArn=$API_TG_ARN
    
    aws elbv2 create-listener \
        --load-balancer-arn $LB_ARN \
        --protocol HTTPS \
        --port 443 \
        --certificates CertificateArn=arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012 \
        --default-actions Type=forward,TargetGroupArn=$API_TG_ARN
    
    log "Load Balancer créé avec succès"
    echo "$LB_ARN" > load_balancer.txt
}

# Create CloudWatch Alarms
create_cloudwatch_alarms() {
    log "Création CloudWatch Alarms..."
    
    # CPU Utilization Alarm
    aws cloudwatch put-metric-alarm \
        --alarm-name $PROJECT_NAME-high-cpu \
        --alarm-description "CPU utilization > 80%" \
        --metric-name CPUUtilization \
        --namespace AWS/EC2 \
        --statistic Average \
        --period 300 \
        --threshold 80 \
        --comparison-operator GreaterThanThreshold \
        --evaluation-periods 2 \
        --alarm-actions arn:aws:sns:us-east-1:123456789012:$PROJECT_NAME-alerts \
        --unit Percent
    
    # Memory Utilization Alarm
    aws cloudwatch put-metric-alarm \
        --alarm-name $PROJECT_NAME-high-memory \
        --alarm-description "Memory utilization > 90%" \
        --metric-name MemoryUtilization \
        --namespace CWAgent \
        --statistic Average \
        --period 300 \
        --threshold 90 \
        --comparison-operator GreaterThanThreshold \
        --evaluation-periods 2 \
        --alarm-actions arn:aws:sns:us-east-1:123456789012:$PROJECT_NAME-alerts \
        --unit Percent
    
    log "CloudWatch Alarms créés avec succès"
}

# Main deployment function
deploy_all() {
    log "🚀 DÉPLOIEMENT HARMONIC AI SUR AWS"
    log "=================================="
    
    check_aws_cli
    create_vpc
    create_subnets
    create_security_groups
    create_iam_role
    create_s3_buckets
    create_ec2_instances
    create_load_balancer
    create_cloudwatch_alarms
    
    log "=================================="
    log "✅ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS!"
    log "📊 Ressources créées:"
    log "   - VPC: $(cat vpc_id.txt)"
    log "   - Subnets: $(cat public_subnets.txt) et $(cat private_subnets.txt)"
    log "   - Security Groups: $(cat security_groups.txt)"
    log "   - IAM Role: $(cat iam_role.txt)"
    log "   - Load Balancer: $(cat load_balancer.txt)"
    log "   - S3 Buckets: $PROJECT_NAME-*"
    log "   - EC2 Instances: 2 GPU + 1 Visual + 2 API"
    log "=================================="
    log "⏱️ Temps de démarrage estimé: 5-10 minutes"
    log "💰 Coût mensuel estimé: ~938€"
    log "🔍 Monitoring: CloudWatch configuré"
    log "🔒 Sécurité: Security Groups configurés"
    log "🌊 Harmonic AI est maintenant déployé sur AWS!"
}

# Cleanup function
cleanup() {
    warning "Cette fonction va supprimer toutes les ressources Harmonic AI"
    read -p "Êtes-vous sûr? (yes/no): " -r
    if [[ $REPLY != "yes" ]]; then
        log "Annulation du cleanup"
        exit 0
    fi
    
    log "🧹 NETTOYAGE DES RESSOURCES AWS..."
    
    # Terminate instances
    log "Terminaison des instances EC2..."
    aws ec2 terminate-instances --instance-ids $(aws ec2 describe-instances --filters "Name=tag:Project,Values=$PROJECT_NAME" --query 'Instances[*].InstanceId' --output text)
    
    # Delete load balancer
    log "Suppression Load Balancer..."
    aws elbv2 delete-load-balancer --load-balancer-arn $(cat load_balancer.txt 2>/dev/null || echo "")
    
    # Delete security groups
    log "Suppression Security Groups..."
    aws ec2 delete-security-group --group-name $PROJECT_NAME-web-sg 2>/dev/null || true
    aws ec2 delete-security-group --group-name $PROJECT_NAME-app-sg 2>/dev/null || true
    aws ec2 delete-security-group --group-name $PROJECT_NAME-gpu-sg 2>/dev/null || true
    
    # Delete subnets and VPC
    log "Suppression Subnets et VPC..."
    if [ -f vpc_id.txt ]; then
        VPC_ID=$(cat vpc_id.txt)
        aws ec2 delete-subnet --subnet-id $(cat public_subnets.txt 2>/dev/null | cut -d',' -f1) 2>/dev/null || true
        aws ec2 delete-subnet --subnet-id $(cat private_subnets.txt 2>/dev/null | cut -d',' -f1) 2>/dev/null || true
        aws ec2 delete-vpc --vpc-id $VPC_ID 2>/dev/null || true
    fi
    
    # Delete IAM role
    log "Suppression IAM Role..."
    aws iam delete-instance-profile --instance-profile-name $PROJECT_NAME-ec2-profile 2>/dev/null || true
    aws iam remove-role-from-instance-profile --instance-profile-name $PROJECT_NAME-ec2-profile --role-name $PROJECT_NAME-ec2-role 2>/dev/null || true
    aws iam delete-role --role-name $PROJECT_NAME-ec2-role 2>/dev/null || true
    
    # Delete S3 buckets
    log "Suppression S3 Buckets..."
    aws s3 rb s3://$PROJECT_NAME-knowledge-base --force 2>/dev/null || true
    aws s3 rb s3://$PROJECT_NAME-models --force 2>/dev/null || true
    aws s3 rb s3://$PROJECT_NAME-assets --force 2>/dev/null || true
    aws s3 rb s3://$PROJECT_NAME-backups --force 2>/dev/null || true
    
    # Clean up local files
    rm -f vpc_id.txt public_subnets.txt private_subnets.txt security_groups.txt iam_role.txt load_balancer.txt trust-policy.json lifecycle-policy.json
    
    log "✅ NETTOYAGE TERMINÉ!"
}

# Status check function
status() {
    log "📊 STATUT DES RESSOURCES HARMONIC AI"
    log "=================================="
    
    # VPC Status
    if [ -f vpc_id.txt ]; then
        VPC_ID=$(cat vpc_id.txt)
        VPC_STATE=$(aws ec2 describe-vpcs --vpc-ids $VPC_ID --query 'Vpcs[0].State' --output text 2>/dev/null || echo "Non trouvé")
        log "VPC: $VPC_ID ($VPC_STATE)"
    else
        log "VPC: Non créé"
    fi
    
    # EC2 Instances Status
    log "Instances EC2:"
    aws ec2 describe-instances --filters "Name=tag:Project,Values=$PROJECT_NAME" --query 'Reservations[*].Instances[*].[InstanceId,State.Name,Tags[?Key==`Name`].Value]' --output table 2>/dev/null || log "Aucune instance trouvée"
    
    # Load Balancer Status
    if [ -f load_balancer.txt ]; then
        LB_ARN=$(cat load_balancer.txt)
        LB_STATE=$(aws elbv2 describe-load-balancers --load-balancer-arns $LB_ARN --query 'LoadBalancers[0].State.Code' --output text 2>/dev/null || echo "Non trouvé")
        log "Load Balancer: $LB_STATE"
    else
        log "Load Balancer: Non créé"
    fi
    
    # S3 Buckets Status
    log "S3 Buckets:"
    aws s3 ls | grep $PROJECT_NAME || log "Aucun bucket trouvé"
    
    log "=================================="
}

# Main script execution
case "${1:-deploy}" in
    deploy)
        deploy_all
        ;;
    cleanup)
        cleanup
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {deploy|cleanup|status}"
        echo "  deploy  - Déploie l'infrastructure complète"
        echo "  cleanup - Supprime toutes les ressources"
        echo "  status  - Affiche le statut des ressources"
        exit 1
        ;;
esac
