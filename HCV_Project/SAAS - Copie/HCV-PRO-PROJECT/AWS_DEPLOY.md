# AWS Deployment Guide

## Quick Start

### 1. Install Tools
```bash
pip install awscli awsebcli
aws configure
```

### 2. Deploy
```bash
cd HCV-PRO-PROJECT/render-backend
eb init -p "Python 3.11 running on 64bit Amazon Linux 2" hcv-pro-backend --region us-east-1
eb create hcv-pro-backend-env --instance-type t2.micro
```

### 3. Test
```bash
curl http://hcv-pro-backend-env.elasticbeanstalk.com/health
```

### 4. Update
```bash
git add .
git commit -m "Update"
eb deploy
```

## Docs
- [AWS EB Docs](https://docs.aws.amazon.com/elasticbeanstalk/)
- [EB CLI](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3.html)
