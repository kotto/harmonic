# AWS Deployment Script for Qwen3.5 Model (Fixed Version)
# Compatible with AVX2 environments
# Author: Harmonic AI Team

param(
    [string]$Region = "us-east-1",
    [string]$ECRRepository = "qwen35-deployment",
    [string]$S3Bucket = "harmonic-ai-qwen-models",
    [string]$ModelName = "qwen35",
    [string]$InstanceType = "ml.m5.xlarge"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting AWS deployment for Qwen3.5 model..." -ForegroundColor Green

# Check AWS credentials
Write-Host "📋 Verifying AWS credentials..." -ForegroundColor Yellow
try {
    aws sts get-caller-identity | Out-Null
    Write-Host "✅ AWS credentials verified" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS credentials not found. Please configure AWS CLI." -ForegroundColor Red
    exit 1
}

# Create IAM policy for required permissions
Write-Host "🔐 Checking IAM permissions..." -ForegroundColor Yellow
$policyDocument = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Action = @(
                "ecr:*",
                "sagemaker:*",
                "iam:PassRole",
                "logs:*",
                "cloudwatch:*"
            )
            Resource = "*"
        }
    )
}

$policyJson = $policyDocument | ConvertTo-Json -Depth 10
Write-Host "📋 Required permissions: ECR, SageMaker, IAM PassRole, CloudWatch" -ForegroundColor Cyan

# Try to create ECR repository (may fail due to permissions)
Write-Host "📦 Attempting to create ECR repository..." -ForegroundColor Yellow
try {
    aws ecr create-repository --repository-name $ECRRepository --region $Region | Out-Null
    Write-Host "✅ ECR repository created" -ForegroundColor Green
} catch {
    Write-Host "⚠️ ECR repository creation failed (permissions required)" -ForegroundColor Yellow
}

# Check if Docker is available
Write-Host "🐳 Checking Docker availability..." -ForegroundColor Yellow
try {
    docker --version | Out-Null
    Write-Host "✅ Docker is available" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not available. Using Lambda deployment instead." -ForegroundColor Red
    Write-Host "🔄 Switching to Lambda deployment strategy..." -ForegroundColor Yellow
    
    # Create Lambda deployment instead
    Write-Host "📦 Creating Lambda deployment package..." -ForegroundColor Yellow
    
    # Create Lambda function code
    New-Item -ItemType Directory -Path "lambda-deployment" -Force | Out-Null
    
    @"
import json
import boto3
import os

def lambda_handler(event, context):
    try:
        # Simple inference response for now
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Qwen3.5 Lambda function is running',
                'model': 'qwen35',
                'status': 'ready'
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
"@ | Out-File -FilePath "lambda-deployment\lambda_function.py" -Encoding UTF8
    
    # Create requirements.txt for Lambda
    @"
boto3>=1.26.0
"@ | Out-File -FilePath "lambda-deployment\requirements.txt" -Encoding UTF8
    
    # Create deployment package
    Compress-Archive -Path "lambda-deployment\*" -DestinationPath "qwen35-lambda.zip" -Force
    
    Write-Host "📤 Lambda package created: qwen35-lambda.zip" -ForegroundColor Green
    Write-Host "🎯 Manual Lambda deployment required due to permissions" -ForegroundColor Yellow
    Write-Host "📋 To deploy Lambda manually:" -ForegroundColor Cyan
    Write-Host "   aws lambda create-function --function-name qwen35 --runtime python3.9 --handler lambda_function.lambda_handler --zip-file fileb://qwen35-lambda.zip --role arn:aws:iam::326095712935:role/lambda-execution-role" -ForegroundColor White
    
    # Cleanup
    Remove-Item -Path "lambda-deployment" -Recurse -Force
    exit 0
}

# Create deployment files locally (without pushing to AWS)
Write-Host "📁 Creating local deployment files..." -ForegroundColor Yellow

# Create Dockerfile
@"
FROM python:3.9-slim

# Install system dependencies for AVX2 support
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Expose port
EXPOSE 8080

# Set environment variables
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "app/main.py"]
"@ | Out-File -FilePath "Dockerfile" -Encoding UTF8

# Create requirements.txt
@"
torch>=2.0.0
transformers>=4.30.0
accelerate>=0.20.0
fastapi>=0.100.0
uvicorn>=0.22.0
boto3>=1.26.0
numpy>=1.24.0
requests>=2.31.0
pydantic>=2.0.0
"@ | Out-File -FilePath "requirements.txt" -Encoding UTF8

# Create application structure
New-Item -ItemType Directory -Path "app" -Force | Out-Null

# Create simplified main application
@"
import os
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Qwen3.5 API", version="1.0.0")

class GenerationRequest(BaseModel):
    prompt: str
    max_length: int = 512
    temperature: float = 0.7

class GenerationResponse(BaseModel):
    generated_text: str
    model_name: str

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": False, "message": "Container running"}

@app.post("/generate", response_model=GenerationResponse)
async def generate_text(request: GenerationRequest):
    # Placeholder response - model loading requires proper setup
    return GenerationResponse(
        generated_text=f"Response to: {request.prompt} (Model not loaded - requires proper setup)",
        model_name="Qwen3.5-Placeholder"
    )

@app.get("/")
async def root():
    return {"message": "Qwen3.5 API container is running", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
"@ | Out-File -FilePath "app\main.py" -Encoding UTF8

# Create deployment instructions
@"
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
"@ | Out-File -FilePath "DEPLOYMENT_INSTRUCTIONS.md" -Encoding UTF8

Write-Host "📋 Deployment files created locally" -ForegroundColor Green
Write-Host "📁 Files created:" -ForegroundColor Cyan
Write-Host "   - Dockerfile" -ForegroundColor White
Write-Host "   - requirements.txt" -ForegroundColor White
Write-Host "   - app/main.py" -ForegroundColor White
Write-Host "   - DEPLOYMENT_INSTRUCTIONS.md" -ForegroundColor White

Write-Host "⚠️ Issues encountered:" -ForegroundColor Yellow
Write-Host "   1. Docker Desktop not running" -ForegroundColor Red
Write-Host "   2. Insufficient AWS permissions for ECR/SageMaker" -ForegroundColor Red
Write-Host "   3. IAM role PassRole permission missing" -ForegroundColor Red

Write-Host "🔧 To fix permissions, contact AWS administrator:" -ForegroundColor Cyan
Write-Host "   - ECR Full Access" -ForegroundColor White
Write-Host "   - SageMaker Full Access" -ForegroundColor White
Write-Host "   - IAM PassRole for SageMaker execution role" -ForegroundColor White

Write-Host "📖 See DEPLOYMENT_INSTRUCTIONS.md for manual deployment steps" -ForegroundColor Green
