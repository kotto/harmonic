# Qwen3.5 AWS Deployment Instructions

## Current Status
✅ AWS Credentials: Verified
❌ Docker: Not running or permissions insufficient
❌ ECR/SageMaker: Insufficient permissions

## Files Created
- Dockerfile (container definition)
- requirements.txt (Python dependencies)
- app/main.py (FastAPI application)

## Next Steps

### 1. Fix Docker Installation
- Install Docker Desktop for Windows
- Start Docker service
- Verify with: docker --version

### 2. Fix AWS Permissions
Add these permissions to harmonic-ai-user:
- ECR: Full Access
- SageMaker: Full Access
- IAM: PassRole
- CloudWatch: Full Access

### 3. Manual Deployment Commands

#### ECR Repository
aws ecr create-repository --repository-name qwen35-deployment --region us-east-1

#### Build and Push Image
docker build -t qwen35-deployment:latest .
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 326095712935.dkr.ecr.us-east-1.amazonaws.com
docker tag qwen35-deployment:latest 326095712935.dkr.ecr.us-east-1.amazonaws.com/qwen35-deployment:latest
docker push 326095712935.dkr.ecr.us-east-1.amazonaws.com/qwen35-deployment:latest

#### SageMaker Model
aws sagemaker create-model --model-name qwen35 --primary-container Image=326095712935.dkr.ecr.us-east-1.amazonaws.com/qwen35-deployment:latest --execution-role-arn arn:aws:iam::326095712935:role/AmazonSageMaker-ExecutionRole-20250511T181292

#### Endpoint Configuration
aws sagemaker create-endpoint-config --endpoint-config-name qwen35-config --production-variants VariantName=AllTraffic,ModelName=qwen35,InstanceType=ml.m5.xlarge,InitialInstanceCount=1

#### Create Endpoint
aws sagemaker create-endpoint --endpoint-name qwen35-endpoint --endpoint-config-name qwen35-config

## Alternative: Lambda Deployment
If SageMaker permissions cannot be obtained, use Lambda:
1. Run the Lambda deployment script
2. Upload qwen35-lambda.zip to Lambda
3. Configure API Gateway for HTTP access
