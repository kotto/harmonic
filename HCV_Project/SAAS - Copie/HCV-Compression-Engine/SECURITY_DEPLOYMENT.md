# Security Deployment Guide

## Pre-Deployment Checklist

### 1. Secrets Management
- [ ] No hardcoded secrets in code
- [ ] All sensitive data in `.env` files (excluded from git)
- [ ] `.env` files added to `.gitignore`
- [ ] Use `.env.example` for template only

### 2. Code Protection
- [ ] Proprietary codec files compiled to bytecode
- [ ] Source `.py` files removed from `codecs/` directory
- [ ] Server/API entry points kept as source for execution
- [ ] ECR images scanned for vulnerabilities

### 3. AWS Credentials
- [ ] AWS credentials NOT in environment variables on local machine
- [ ] Use AWS IAM roles for EC2/App Runner
- [ ] ECR requires authentication only (no credentials in code)
- [ ] Docker login done via `aws ecr get-login-password`

### 4. Image Security
- [ ] ECR image scanning enabled
- [ ] Image tags immutable
- [ ] Build provenance tracked
- [ ] Only authorized users can push images

## Environment Variables

**Development (.env.local):**
```bash
PRODUCTION_MODE=false
FLASK_ENV=development
HCV_PRO_SECRET=dev-secret-only
```

**Production (.env.production - NOT in git):**
```bash
PRODUCTION_MODE=true
FLASK_ENV=production
HCV_PRO_SECRET=<from AWS Secrets Manager>
GUNICORN_TIMEOUT=240
SKIP_PSNR=true
```

## AWS Secrets Manager Integration

### 1. Create Secret
```bash
aws secretsmanager create-secret \
  --name hcv-pro/production-secret \
  --secret-string '{"HCV_PRO_SECRET":"your-actual-secret-here"}'
```

### 2. Grant App Runner Access
```bash
# Add to App Runner IAM role
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "arn:aws:secretsmanager:eu-west-3:*:secret:hcv-pro/*"
    }
  ]
}
```

### 3. Retrieve in Code
```python
import boto3
import json
from os import getenv

def get_secret(secret_name, region='eu-west-3'):
    client = boto3.client('secretsmanager', region_name=region)
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except Exception as e:
        print(f"Error retrieving secret: {e}")
        return {}

# Usage
secret = get_secret('hcv-pro/production-secret')
HCV_PRO_SECRET = secret.get('HCV_PRO_SECRET', getenv('HCV_PRO_SECRET'))
```

## Deployment

### 1. Build Securely
```bash
# Use specific base image version (never 'latest')
docker build -t hcv-compression-engine:v1.0.0 -f aws-deploy/Dockerfile .
```

### 2. Scan Image
```bash
aws ecr put-image-scanning-configuration \
  --repository-name hcv-compression-engine \
  --image-scanning-configuration scanOnPush=true
```

### 3. Push with Immutable Tags
```bash
aws ecr put-image-tag-mutability \
  --repository-name hcv-compression-engine \
  --image-tag-mutability IMMUTABLE

docker push 326095712935.dkr.ecr.eu-west-3.amazonaws.com/hcv-compression-engine:v1.0.0
```

## Monitoring & Logging

### CloudWatch Logs
```bash
# View logs
aws logs tail /aws/apprunner/hcv-compression-engine --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/apprunner/hcv-compression-engine \
  --filter-pattern "ERROR"
```

### Security Events
- Monitor ECR image scans: `aws ecr describe-image-scan-findings`
- Check App Runner service status: `aws apprunner describe-service`
- Review CloudTrail for API calls

## Incident Response

### If Secret is Compromised
1. Rotate secret in AWS Secrets Manager
2. Update all services referencing it
3. Review CloudTrail logs for unauthorized access
4. Notify security team

### If Code is Exposed
1. Review git history for sensitive data
2. Run secret scanning on repository
3. Consider re-deployment from secure build

## Regular Security Tasks

- [ ] Monthly: Review IAM permissions
- [ ] Quarterly: Update dependencies
- [ ] Quarterly: Security audit
- [ ] Monthly: Review CloudWatch logs
- [ ] Weekly: Check ECR vulnerability scans
