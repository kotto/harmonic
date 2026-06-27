# AWS Deployment Script for Qwen3.5 Model (PowerShell Version)
# Compatible with AVX2 environments
# Author: Harmonic AI Team
# Date: $(Get-Date -Format "yyyy-MM-dd")

param(
    [string]$Region = "us-east-1",
    [string]$ECRRepository = "qwen35-deployment",
    [string]$S3Bucket = "harmonic-ai-qwen-models",
    [string]$ModelName = "qwen35",
    [string]$InstanceType = "ml.m5.xlarge",
    [string]$RoleArn = "arn:aws:iam::326095712935:role/AmazonSageMaker-ExecutionRole-20250511T181292"
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

# Check if Docker is installed and running
try {
    docker version | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed or not running. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Create ECR repository if it doesn't exist
Write-Host "📦 Creating/checking ECR repository..." -ForegroundColor Yellow
try {
    aws ecr describe-repositories --repository-names $ECRRepository --region $Region | Out-Null
    Write-Host "✅ ECR repository already exists" -ForegroundColor Green
} catch {
    Write-Host "Creating ECR repository: $ECRRepository" -ForegroundColor Yellow
    aws ecr create-repository --repository-name $ECRRepository --region $Region
}

# Get ECR login token
Write-Host "🔐 Logging into ECR..." -ForegroundColor Yellow
$password = aws ecr get-login-password --region $Region
echo $password | docker login --username AWS --password-stdin 326095712935.dkr.ecr.$Region.amazonaws.com

# Create Dockerfile
Write-Host "🐳 Creating Dockerfile..." -ForegroundColor Yellow
@"
FROM python:3.9-slim

# Install system dependencies for AVX2 support
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY model/ ./model/

# Expose port
EXPOSE 8080

# Set environment variables
ENV PYTHONPATH=/app
ENV MODEL_PATH=/model

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "app/main.py"]
"@ | Out-File -FilePath "Dockerfile" -Encoding UTF8

# Create requirements.txt
Write-Host "📋 Creating requirements.txt..." -ForegroundColor Yellow
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
Write-Host "📁 Creating application structure..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "app" -Force | Out-Null
New-Item -ItemType Directory -Path "model" -Force | Out-Null

# Create main application file
Write-Host "📝 Creating main application..." -ForegroundColor Yellow
@"
import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3
import json

app = FastAPI(title="Qwen3.5 API", version="1.0.0")

class GenerationRequest(BaseModel):
    prompt: str
    max_length: int = 512
    temperature: float = 0.7
    do_sample: bool = True

class GenerationResponse(BaseModel):
    generated_text: str
    model_name: str

# Global variables for model
tokenizer = None
model = None
model_name = "Qwen/Qwen2.5-7B-Instruct"

def load_model():
    """Load Qwen model from S3 or local cache"""
    global tokenizer, model
    
    try:
        # Try to load from S3 first
        s3 = boto3.client('s3')
        model_path = "/model"
        
        if not os.path.exists(f"{model_path}/config.json"):
            print("Downloading model from S3...")
            s3.download_file("harmonic-ai-qwen-models", "qwen35/model.tar.gz", "/tmp/model.tar.gz")
            os.system("cd / && tar -xzf /tmp/model.tar.gz")
        
        print("Loading tokenizer and model...")
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        model.eval()
        print("✅ Model loaded successfully")
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    load_model()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": model is not None}

@app.post("/generate", response_model=GenerationResponse)
async def generate_text(request: GenerationRequest):
    if not tokenizer or not model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Tokenize input
        inputs = tokenizer.encode(request.prompt, return_tensors="pt").to(model.device)
        
        # Generate text
        with torch.no_grad():
            outputs = model.generate(
                inputs,
                max_length=request.max_length,
                temperature=request.temperature,
                do_sample=request.do_sample,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Decode output
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return GenerationResponse(
            generated_text=generated_text,
            model_name=model_name
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Qwen3.5 API is running", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
"@ | Out-File -FilePath "app\main.py" -Encoding UTF8

# Build and push Docker image
Write-Host "🏗️ Building Docker image..." -ForegroundColor Yellow
docker build -t "$ECRRepository`:latest .

# Tag for ECR
docker tag "$ECRRepository`:latest "326095712935.dkr.ecr.$Region.amazonaws.com/$ECRRepository`:latest"

# Push to ECR
Write-Host "📤 Pushing to ECR..." -ForegroundColor Yellow
docker push "326095712935.dkr.ecr.$Region.amazonaws.com/$ECRRepository`:latest"

# Create SageMaker deployment configuration
Write-Host "⚙️ Creating SageMaker deployment config..." -ForegroundColor Yellow
$config = @{
    ModelName = $ModelName
    PrimaryContainer = @{
        Image = "326095712935.dkr.ecr.$Region.amazonaws.com/$ECRRepository`:latest"
        Environment = @{
            "SAGEMAKER_PROGRAM" = "app/main.py"
            "SAGEMAKER_REGION" = $Region
            "SAGEMAKER_CONTAINER_LOG_LEVEL" = "20"
        }
    }
    ExecutionRoleArn = $RoleArn
    EnableNetworkIsolation = $false
}

$config | ConvertTo-Json -Depth 10 | Out-File -FilePath "sagemaker-config.json" -Encoding UTF8

# Deploy to SageMaker
Write-Host "🚀 Deploying to SageMaker..." -ForegroundColor Yellow
aws sagemaker create-model --cli-input-json file://sagemaker-config.json --region $Region

# Create endpoint configuration
$endpointConfig = @{
    EndpointConfigName = "$ModelName-config"
    ProductionVariants = @(
        @{
            VariantName = "AllTraffic"
            ModelName = $ModelName
            InstanceType = $InstanceType
            InitialInstanceCount = 1
            InitialVariantWeight = 1
        }
    )
}

$endpointConfig | ConvertTo-Json -Depth 10 | Out-File -FilePath "endpoint-config.json" -Encoding UTF8

aws sagemaker create-endpoint-config --cli-input-json file://endpoint-config.json --region $Region

# Create endpoint
Write-Host "🎯 Creating SageMaker endpoint..." -ForegroundColor Yellow
aws sagemaker create-endpoint `
    --endpoint-name "$ModelName-endpoint" `
    --endpoint-config-name "$ModelName-config" `
    --region $Region

Write-Host "⏳ Waiting for endpoint to be in service..." -ForegroundColor Yellow
aws sagemaker wait endpoint-in-service `
    --endpoint-name "$ModelName-endpoint" `
    --region $Region

# Get endpoint status
$endpointStatus = aws sagemaker describe-endpoint --endpoint-name "$ModelName-endpoint" --region $Region --query 'EndpointStatus' --output text

Write-Host "🎉 Deployment completed!" -ForegroundColor Green
Write-Host "📍 Endpoint Name: $ModelName-endpoint" -ForegroundColor Cyan
Write-Host "📍 Region: $Region" -ForegroundColor Cyan
Write-Host "📍 Instance Type: $InstanceType" -ForegroundColor Cyan
Write-Host "📍 Status: $endpointStatus" -ForegroundColor Cyan

# Test the deployment
Write-Host "🧪 Testing deployment..." -ForegroundColor Yellow
$testBody = @{
    prompt = "Hello, how are you?"
    max_length = 100
} | ConvertTo-Json -Depth 10

$testBody | Out-File -FilePath "test_input.json" -Encoding UTF8

aws sagemaker-runtime invoke-endpoint `
    --endpoint-name "$ModelName-endpoint" `
    --content-type application/json `
    --body file://test_input.json `
    --region $Region `
    test_output.json

Write-Host "✅ Test completed. Check test_output.json for results." -ForegroundColor Green

# Cleanup
Write-Host "🧹 Cleanup..." -ForegroundColor Yellow
Remove-Item -Path "Dockerfile", "requirements.txt", "sagemaker-config.json", "endpoint-config.json", "test_input.json", "test_output.json" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "app", "model" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "🎯 Qwen3.5 is now deployed and ready to use!" -ForegroundColor Green
Write-Host "📊 Monitor your endpoint: aws sagemaker describe-endpoint --endpoint-name $ModelName-endpoint --region $Region" -ForegroundColor Cyan
