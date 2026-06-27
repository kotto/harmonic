#!/bin/bash

# AWS Deployment Script for Qwen3.5 Model
# Compatible with AVX2 environments
# Author: Harmonic AI Team
# Date: $(date +%Y-%m-%d)

set -e

# Configuration
AWS_REGION="us-east-1"
ECR_REPOSITORY="qwen35-deployment"
S3_BUCKET="harmonic-ai-qwen-models"
MODEL_NAME="qwen35"
INSTANCE_TYPE="ml.m5.xlarge"  # AVX2 compatible
ROLE_ARN="arn:aws:iam::326095712935:role/AmazonSageMaker-ExecutionRole-20250511T181292"

echo "🚀 Starting AWS deployment for Qwen3.5 model..."

# Check AWS credentials
echo "📋 Verifying AWS credentials..."
aws sts get-caller-identity > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ AWS credentials verified"
else
    echo "❌ AWS credentials not found. Please configure AWS CLI."
    exit 1
fi

# Create ECR repository if it doesn't exist
echo "📦 Creating/checking ECR repository..."
aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Creating ECR repository: $ECR_REPOSITORY"
    aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION
else
    echo "✅ ECR repository already exists"
fi

# Get ECR login token
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin 326095712935.dkr.ecr.$AWS_REGION.amazonaws.com

# Create Dockerfile for Qwen deployment
echo "🐳 Creating Dockerfile..."
cat > Dockerfile << 'EOF'
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
EOF

# Create requirements.txt
echo "📋 Creating requirements.txt..."
cat > requirements.txt << 'EOF'
torch>=2.0.0
transformers>=4.30.0
accelerate>=0.20.0
fastapi>=0.100.0
uvicorn>=0.22.0
boto3>=1.26.0
numpy>=1.24.0
requests>=2.31.0
pydantic>=2.0.0
EOF

# Create application structure
echo "📁 Creating application structure..."
mkdir -p app model

# Create main application file
cat > app/main.py << 'EOF'
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
EOF

# Build and push Docker image
echo "🏗️ Building Docker image..."
docker build -t $ECR_REPOSITORY:latest .

# Tag for ECR
docker tag $ECR_REPOSITORY:latest 326095712935.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest

# Push to ECR
echo "📤 Pushing to ECR..."
docker push 326095712935.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest

# Create SageMaker deployment configuration
echo "⚙️ Creating SageMaker deployment config..."
cat > sagemaker-config.json << EOF
{
    "ModelName": "$MODEL_NAME",
    "PrimaryContainer": {
        "Image": "326095712935.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest",
        "Environment": {
            "SAGEMAKER_PROGRAM": "app/main.py",
            "SAGEMAKER_REGION": "$AWS_REGION",
            "SAGEMAKER_CONTAINER_LOG_LEVEL": "20"
        }
    },
    "ExecutionRoleArn": "$ROLE_ARN",
    "EnableNetworkIsolation": false
}
EOF

# Deploy to SageMaker
echo "🚀 Deploying to SageMaker..."
aws sagemaker create-model --cli-input-json file://sagemaker-config.json --region $AWS_REGION

# Create endpoint configuration
cat > endpoint-config.json << EOF
{
    "EndpointConfigName": "$MODEL_NAME-config",
    "ProductionVariants": [
        {
            "VariantName": "AllTraffic",
            "ModelName": "$MODEL_NAME",
            "InstanceType": "$INSTANCE_TYPE",
            "InitialInstanceCount": 1,
            "InitialVariantWeight": 1
        }
    ]
}
EOF

aws sagemaker create-endpoint-config --cli-input-json file://endpoint-config.json --region $AWS_REGION

# Create endpoint
echo "🎯 Creating SageMaker endpoint..."
aws sagemaker create-endpoint \
    --endpoint-name $MODEL_NAME-endpoint \
    --endpoint-config-name $MODEL_NAME-config \
    --region $AWS_REGION

echo "⏳ Waiting for endpoint to be in service..."
aws sagemaker wait endpoint-in-service \
    --endpoint-name $MODEL_NAME-endpoint \
    --region $AWS_REGION

# Get endpoint status
ENDPOINT_STATUS=$(aws sagemaker describe-endpoint --endpoint-name $MODEL_NAME-endpoint --region $AWS_REGION --query 'EndpointStatus' --output text)

echo "🎉 Deployment completed!"
echo "📍 Endpoint Name: $MODEL_NAME-endpoint"
echo "📍 Region: $AWS_REGION"
echo "📍 Instance Type: $INSTANCE_TYPE"
echo "📍 Status: $ENDPOINT_STATUS"

# Test the deployment
echo "🧪 Testing deployment..."
aws sagemaker-runtime invoke-endpoint \
    --endpoint-name $MODEL_NAME-endpoint \
    --content-type application/json \
    --body '{"prompt": "Hello, how are you?", "max_length": 100}' \
    --region $AWS_REGION \
    test_output.json

echo "✅ Test completed. Check test_output.json for results."

# Cleanup
rm -f Dockerfile requirements.txt sagemaker-config.json endpoint-config.json test_output.json
rm -rf app model

echo "🧹 Cleanup completed."
echo "🎯 Qwen3.5 is now deployed and ready to use!"
echo "📊 Monitor your endpoint: aws sagemaker describe-endpoint --endpoint-name $MODEL_NAME-endpoint --region $AWS_REGION"
