# HCV Deployment Modes

## Quick Start

### Windows PowerShell
```powershell
# Non-blocking (recommended)
.\aws-deploy\deploy-fast.ps1

# Or with specific mode
.\aws-deploy\deploy-fast.ps1 --fast      # Build + Push only
.\aws-deploy\deploy-fast.ps1 --wait      # Build + Push + Wait for ready (blocking)
.\aws-deploy\deploy-fast.ps1 --check     # Check current status
```

### Linux / macOS / WSL
```bash
# Non-blocking (recommended)
bash aws-deploy/deploy-fast.sh

# Or with specific mode
bash aws-deploy/deploy-fast.sh --fast      # Build + Push only
bash aws-deploy/deploy-fast.sh --wait      # Build + Push + Wait for ready
bash aws-deploy/deploy-fast.sh --check     # Check current status
```

---

## Deployment Modes Explained

### 1. **Default Mode (Non-Blocking)** — RECOMMENDED ⭐
```powershell
.\aws-deploy\deploy-fast.ps1
```

**What it does:**
1. ✅ Build Docker image locally (2-3 minutes)
2. ✅ Push to AWS ECR (2-5 minutes)
3. ✅ Trigger App Runner update
4. ✅ **Return immediately** — deploy happens in background

**Output:**
```
[▶] Building Docker image (this takes 2-3 minutes)...
[▶] Pushing image to ECR (~200-300 MB)...
[▶] Updating App Runner service...
[i] Service update initiated

╔════════════════════════════════════════════════════════════╗
║ Service URL (when ready):                                  ║
║   https://xxxxx.eu-west-3.awsapprunner.com               ║
║                                                            ║
║ Check status later:                                        ║
║   .\deploy-fast.ps1 --check                                ║
╚════════════════════════════════════════════════════════════╝
```

**When to use:**
- ✅ During development (deploy and move on)
- ✅ When you just want to trigger the update
- ✅ When you have other work to do
- ✅ **Total time: 4-8 minutes** (you're done immediately)

---

### 2. **Fast Mode** — Build & Push Only
```powershell
.\aws-deploy\deploy-fast.ps1 --fast
```

**What it does:**
1. ✅ Build Docker image
2. ✅ Push to ECR
3. ❌ **Does NOT update App Runner**
4. ✅ Return immediately

**Use case:**
- Testing the Docker build locally without deploying
- Pre-staging an image for later deployment
- Debugging build issues

---

### 3. **Wait Mode** — Blocking Deployment
```powershell
.\aws-deploy\deploy-fast.ps1 --wait
```

**What it does:**
1. ✅ Build Docker image
2. ✅ Push to ECR
3. ✅ Trigger App Runner update
4. ⏳ **Wait for service to be RUNNING**
5. ✅ Perform health check (`/api/health`)
6. ✅ Return when ready

**Output:**
```
[▶] Waiting for deployment (timeout: 30 min)...
[i] Status: IN_PROGRESS — URL: xxxxx.eu-west-3.awsapprunner.com
[i] Status: IN_PROGRESS — URL: xxxxx.eu-west-3.awsapprunner.com
[▶] Service is RUNNING!
[▶] Performing health check...
[▶] Health check PASSED ✓
[▶] ✓ Deployment complete and healthy!
```

**Total time: 5-15 minutes** (blocking your terminal)

**When to use:**
- ✅ CI/CD pipelines that need to wait
- ✅ Critical deployments where you need confirmation
- ✅ When testing functionality immediately after deploy
- ✅ Production deployments with validation

---

### 4. **Check Mode** — Status Only
```powershell
.\aws-deploy\deploy-fast.ps1 --check
```

**What it does:**
- Get current deployment status
- Show service URL
- No build, no push, no update

**Output:**
```
[▶] Checking deployment status...
[i] Status: RUNNING
[i] URL: xxxxx.eu-west-3.awsapprunner.com
```

**Use case:**
- Checking if a previous deployment finished
- Getting the service URL
- Monitoring in-progress deployments

---

## Real-World Workflows

### Development (Rapid Iteration)
```powershell
# Deploy code
.\aws-deploy\deploy-fast.ps1

# Keep working...
# In another terminal, check when ready:
.\aws-deploy\deploy-fast.ps1 --check

# Or just wait
.\aws-deploy\deploy-fast.ps1 --check
# (repeat every 30 seconds)
```

### Production (Safe Deployment)
```powershell
# Deploy with full validation
.\aws-deploy\deploy-fast.ps1 --wait

# Script blocks until service is healthy
# Guarantees successful deployment before returning
```

### CI/CD Pipeline
```bash
#!/bin/bash
./aws-deploy/deploy-fast.sh --wait
if [ $? -eq 0 ]; then
    echo "✓ Deployment successful"
    exit 0
else
    echo "✗ Deployment failed"
    exit 1
fi
```

---

## Performance Comparison

| Aspect | Default | Fast | Wait | Check |
|--------|---------|------|------|-------|
| Build Docker | ✅ | ✅ | ✅ | ❌ |
| Push to ECR | ✅ | ✅ | ✅ | ❌ |
| Update service | ✅ | ❌ | ✅ | ❌ |
| Wait for ready | ❌ | ❌ | ✅ | ❌ |
| Health check | ❌ | ❌ | ✅ | ❌ |
| **Total time** | **4-8 min** | **4-8 min** | **5-15 min** | **<1 sec** |
| **Blocks terminal** | ❌ | ❌ | ✅ | ❌ |

---

## Troubleshooting

### Build fails
```powershell
.\aws-deploy\deploy-fast.ps1 --fast
# Check Docker output for errors
# Common: Missing dependencies, compilation errors
```

### Push fails
- Check Docker is running: `docker ps`
- Check ECR credentials: `aws ecr describe-repositories`
- Check network connectivity

### Service doesn't start
```powershell
.\aws-deploy\deploy-fast.ps1 --check
# Returns: Status: FAILED or IN_PROGRESS

# View logs
aws logs tail /aws/apprunner/hcv-compression-engine --follow
```

### Health check fails
- Service is running but `/api/health` returns 403 or timeout
- Check: Is PRODUCTION_MODE set correctly?
- View logs: `aws logs tail /aws/apprunner/hcv-compression-engine`

---

## Environment Variables During Deployment

The deployment sets these automatically:

```env
PRODUCTION_MODE=true
SKIP_PSNR=true
GUNICORN_TIMEOUT=240
REQUEST_TIMEOUT=300
FLASK_ENV=production
HCV_PRO_SECRET=hcv-pro-secret-2024
HCV_PRO_API_KEY_REQUIRED=false
HCV_PRO_RATE_LIMIT=100
```

To change them, edit `deploy-fast.ps1` or `deploy-fast.sh` in the `update_apprunner` function.

---

## Monitoring After Deployment

```bash
# View real-time logs
aws logs tail /aws/apprunner/hcv-compression-engine --follow

# Get service details
aws apprunner describe-service --service-arn arn:aws:apprunner:eu-west-3:326095712935:service/HCV-PRO/8d4e092eb41c42d1baa83e4aa6aad30c

# Test health endpoint
curl https://xxxxx.eu-west-3.awsapprunner.com/api/health

# Test compression endpoint
curl -X POST https://xxxxx.eu-west-3.awsapprunner.com/api/demo \
  -F resolution=VGA \
  -F bit_depth=12
```
