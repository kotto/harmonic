# 🚀 HCV Compression Engine - AWS Deployment

## Architecture Overview

This deployment setup creates a complete AWS infrastructure for the HCV Compression Engine:

```
                    Internet
                        │
                ┌───────┴───────┐
                │  CloudFront  │
                │  Global CDN  │
                └───────┬───────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
┌───────┴───────┐               ┌───────┴───────┐
│   S3 Bucket   │               │  App Runner   │
│   Frontend    │               │   Backend     │
│  Static Site  │               │  Flask API    │
└───────────────┘               └───────┬───────┘
                                        │
                                ┌───────┴───────┐
                                │ CloudWatch    │
                                │ Logs / Metrics│
                                └───────────────┘
```

## Services Used

| Service | Purpose | Cost (Free Tier) |
|---------|---------|------------------|
| **S3** | Frontend static hosting | 5GB storage, 20K requests/month |
| **CloudFront** | CDN, HTTPS, caching | 50GB transfer/month |
| **App Runner** | Backend container hosting | 2 vCPU, 4GB RAM, 1M requests/month |
| **ECR** | Docker container registry | 500MB storage |
| **CloudWatch** | Logs and monitoring | 5GB logs/month |
| **Certificate Manager** | SSL certificates | Free |

## Quick Start

### Prerequisites

1. **AWS CLI installed and configured**
   ```bash
   aws configure
   ```

2. **Docker installed**
   ```bash
   docker --version
   ```

### Option 1: Automated Deployment (Recommended)

```bash
# Deploy backend
cd aws-deploy
chmod +x deploy.sh
./deploy.sh

# Deploy frontend (replace with actual backend URL)
chmod +x frontend-deploy.sh
./frontend-deploy.sh https://your-backend-url.amazonaws.com
```

### Option 2: CloudFormation Deployment

```bash
# Deploy infrastructure
aws cloudformation deploy \
  --template-file cloudformation.yaml \
  --stack-name hcv-compression-engine \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides ProjectName=hcv-compression-engine Environment=production

# Get outputs
aws cloudformation describe-stacks \
  --stack-name hcv-compression-engine \
  --query 'Stacks[0].Outputs'
```

### Option 3: Manual Deployment

#### Backend (App Runner)

```bash
# Create ECR repository
aws ecr create-repository --repository-name hcv-compression-engine

# Build and push image
aws ecr get-login-password --region eu-west-3 | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.eu-west-3.amazonaws.com
docker build -t hcv-compression-engine -f aws-deploy/Dockerfile .
docker tag hcv-compression-engine:latest $(aws sts get-caller-identity --query Account --output text).dkr.ecr.eu-west-3.amazonaws.com/hcv-compression-engine:latest
docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.eu-west-3.amazonaws.com/hcv-compression-engine:latest

# Create App Runner service
aws apprunner create-service \
  --service-name hcv-compression-engine \
  --source-configuration '{"ImageRepository":{"ImageIdentifier":"'$(aws sts get-caller-identity --query Account --output text).dkr.ecr.eu-west-3.amazonaws.com/hcv-compression-engine:latest'","ImageRepositoryType":"ECR"},"AutoDeploymentsEnabled":true}' \
  --instance-configuration '{"Cpu":"256","Memory":"512"}'
```

#### Frontend (S3 + CloudFront)

```bash
# Create S3 bucket
aws s3 mb s3://hcv-compression-engine-frontend-$(aws sts get-caller-identity --query Account --output text)

# Configure for static hosting
aws s3 website s3://hcv-compression-engine-frontend-$(aws sts get-caller-identity --query Account --output text) --index-document index.html

# Upload files
aws s3 sync web/templates/ s3://hcv-compression-engine-frontend-$(aws sts get-caller-identity --query Account --output text)/

# Create CloudFront distribution
aws cloudfront create-distribution --origin-domain-name hcv-compression-engine-frontend-$(aws sts get-caller-identity --query Account --output text).s3.amazonaws.com
```

## Configuration

### Environment Variables

Configure these in App Runner service settings:

```env
PORT=8080
PYTHONPATH=/app
FLASK_ENV=production
HCV_PRO_SECRET=your-secret-key
HCV_PRO_API_KEY_REQUIRED=true
HCV_PRO_RATE_LIMIT=100
```

### Frontend Configuration

Update the backend URL in `web/templates/hcv_pro.html`:

```javascript
const BACKEND_URL = 'https://your-backend-url.amazonaws.com';
```

## Monitoring

### Health Checks

- **Backend**: `GET /api/health`
- **Frontend**: CloudFront automatically monitors S3 origin

### Logs

```bash
# View App Runner logs
aws apprunner list-operations --service-arn YOUR_SERVICE_ARN

# View CloudWatch logs
aws logs tail /aws/apprunner/hcv-compression-engine
```

### Metrics

Monitor in AWS CloudWatch:
- CPU/Memory utilization
- Request count and latency
- Error rates
- S3 request metrics

## Security

### Network Security

- **HTTPS enforced** by CloudFront
- **WAF protection** available
- **DDoS protection** included
- **VPC isolation** possible

### Application Security

- **API key authentication**
- **Rate limiting**
- **CORS configuration**
- **Security headers**

## Scaling

### Auto Scaling

App Runner automatically scales:
- **Min instances**: 1
- **Max instances**: 10
- **Target CPU**: 70%
- **Target memory**: 80%

### Performance Optimization

- **CloudFront caching** reduces backend load
- **GZIP compression** enabled
- **HTTP/2 and HTTP/3** supported
- **Global edge locations**

## Cost Management

### Free Tier Usage (12 months)

- **App Runner**: 1M requests/month
- **S3**: 5GB storage, 20K requests/month
- **CloudFront**: 50GB transfer/month
- **CloudWatch**: 5GB logs/month

### Estimated Monthly Costs (after free tier)

| Service | Usage | Cost |
|---------|-------|------|
| App Runner | 500K requests | ~$7 |
| S3 | 10GB storage | ~$0.23 |
| CloudFront | 100GB transfer | ~$10 |
| CloudWatch | 2GB logs | ~$0.50 |
| **Total** | | **~$18/month** |

## Troubleshooting

### Common Issues

1. **Backend not responding**
   ```bash
   aws apprunner describe-service --service-name hcv-compression-engine
   ```

2. **Frontend not loading**
   ```bash
   aws s3 ls s3://your-bucket-name
   ```

3. **CloudFront distribution issues**
   ```bash
   aws cloudfront get-distribution --id YOUR_DISTRIBUTION_ID
   ```

### Debug Commands

```bash
# Check service status
aws apprunner list-operations --service-arn YOUR_SERVICE_ARN

# View logs
aws logs tail /aws/apprunner/hcv-compression-engine --follow

# Test health endpoint
curl https://your-backend-url.amazonaws.com/api/health
```

## Updates and Maintenance

### Updating Backend

```bash
# Build new image
docker build -t hcv-compression-engine -f aws-deploy/Dockerfile .
docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.eu-west-3.amazonaws.com/hcv-compression-engine:latest

# App Runner will auto-deploy if AutoDeploymentsEnabled=true
```

### Updating Frontend

```bash
# Sync new files
aws s3 sync web/templates/ s3://your-bucket-name/ --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/*"
```

## Support

For issues related to:
- **AWS services**: Check AWS documentation
- **Application**: Review application logs
- **Deployment**: Verify IAM permissions

## Next Steps

1. **Set up custom domain**
2. **Configure SSL certificates**
3. **Set up monitoring alerts**
4. **Configure backup strategy**
5. **Set up CI/CD pipeline**
