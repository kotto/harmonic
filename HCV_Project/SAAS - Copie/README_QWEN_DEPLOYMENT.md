# Qwen3.5 AWS Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying Qwen3.5 model to AWS SageMaker with AVX2 compatibility.

## Prerequisites
- AWS CLI configured with appropriate permissions
- Docker Desktop installed and running
- Sufficient AWS IAM permissions for SageMaker, ECR, and S3
- Qwen3.5 model uploaded to S3 bucket

## Files Created
1. `deploy_qwen_aws.sh` - Bash deployment script (Linux/Mac)
2. `deploy_qwen_aws.ps1` - PowerShell deployment script (Windows)
3. `README_QWEN_DEPLOYMENT.md` - This documentation

## Quick Start

### Windows (PowerShell)
```powershell
# Run the deployment script
.\deploy_qwen_aws.ps1

# Or with custom parameters
.\deploy_qwen_aws.ps1 -Region "us-east-1" -InstanceType "ml.m5.xlarge"
```

### Linux/Mac (Bash)
```bash
# Make script executable
chmod +x deploy_qwen_aws.sh

# Run the deployment script
./deploy_qwen_aws.sh
```

## Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| Region | us-east-1 | AWS region for deployment |
| ECRRepository | qwen35-deployment | ECR repository name |
| S3Bucket | harmonic-ai-qwen-models | S3 bucket containing the model |
| ModelName | qwen35 | SageMaker model name |
| InstanceType | ml.m5.xlarge | EC2 instance type (AVX2 compatible) |
| RoleArn | SageMaker execution role | IAM role for SageMaker |

## Deployment Steps

### 1. Environment Verification
- ✅ AWS credentials validation
- ✅ Docker installation check
- ✅ ECR repository creation
- ✅ S3 bucket access verification

### 2. Container Creation
- 🐳 Dockerfile generation with AVX2 support
- 📦 Python dependencies installation
- 🏗️ FastAPI application setup
- 📤 ECR image push

### 3. SageMaker Deployment
- ⚙️ Model configuration
- 🎯 Endpoint creation
- 🚀 Service deployment
- 🧪 Health check and testing

## API Endpoints

Once deployed, your Qwen3.5 model will be available at:

### Health Check
```
GET https://runtime.sagemaker.{region}.amazonaws.com/endpoints/{endpoint-name}/invocations
Content-Type: application/json

Response: {"status": "healthy", "model_loaded": true}
```

### Text Generation
```
POST https://runtime.sagemaker.{region}.amazonaws.com/endpoints/{endpoint-name}/invocations
Content-Type: application/json

{
  "prompt": "Hello, how are you?",
  "max_length": 512,
  "temperature": 0.7,
  "do_sample": true
}
```

## Monitoring

### Check Endpoint Status
```bash
aws sagemaker describe-endpoint --endpoint-name qwen35-endpoint --region us-east-1
```

### View CloudWatch Logs
```bash
aws logs tail /aws/sagemaker/Endpoints/qwen35-endpoint --follow --region us-east-1
```

### Monitor Resource Usage
```bash
aws cloudwatch get-metric-statistics \
    --namespace AWS/SageMaker \
    --metric-name CPUUtilization \
    --dimensions Name=EndpointName,Value=qwen35-endpoint \
    --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
    --period 300 \
    --statistics Average
```

## Cost Optimization

### Instance Types
- `ml.m5.xlarge` - $0.266/hour (Development)
- `ml.m5.2xlarge` - $0.532/hour (Production)
- `ml.c5.xlarge` - $0.204/hour (Compute optimized)

### Auto Scaling
```json
{
  "TargetTrackingScalingPolicyConfiguration": {
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "SageMakerVariantInvocationsPerInstance"
    }
  }
}
```

## Security Considerations

### VPC Configuration
- Deploy within VPC for enhanced security
- Use private subnets with NAT gateways
- Configure security groups appropriately

### IAM Roles
- Principle of least privilege
- Regular role rotation
- Access logging enabled

## Troubleshooting

### Common Issues

#### 1. Model Loading Timeout
```bash
# Increase timeout in endpoint configuration
"InitialVariantWeight": 1,
"ModelDataDownloadTimeoutInSeconds": 3600
```

#### 2. Memory Issues
```bash
# Use larger instance type
ml.m5.2xlarge or ml.m5.4xlarge
```

#### 3. AVX2 Compatibility
- Ensure instance supports AVX2
- Check CPU flags: `lscpu | grep avx2`

### Error Codes
- `ValidationError` - Configuration error
- `ResourceLimitExceeded` - AWS limits reached
- `InternalFailure` - Contact AWS support

## Cleanup

### Delete Resources
```bash
# Delete endpoint
aws sagemaker delete-endpoint --endpoint-name qwen35-endpoint

# Delete endpoint configuration
aws sagemaker delete-endpoint-config --endpoint-config-name qwen35-config

# Delete model
aws sagemaker delete-model --model-name qwen35

# Delete ECR repository
aws ecr delete-repository --repository-name qwen35-deployment --force
```

## Support

### AWS Documentation
- [SageMaker Documentation](https://docs.aws.amazon.com/sagemaker/)
- [ECR Documentation](https://docs.aws.amazon.com/AmazonECR/)
- [IAM Documentation](https://docs.aws.amazon.com/IAM/)

### Contact
- Harmonic AI Team
- AWS Support (Enterprise customers)

## Version History
- v1.0 - Initial deployment script
- v1.1 - Added PowerShell support
- v1.2 - Enhanced error handling and monitoring
