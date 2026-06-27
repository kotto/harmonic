# 📦 AWS Deployment Files Inventory

**Date**: 24 Avril 2026  
**Status**: ✅ Complete Inventory  
**Purpose**: Comprehensive documentation of all AWS deployment-related files and directories

---

## 🎯 Overview

The HCV PRO project has **3 main AWS deployment packages** in the workspace:

1. **`aws-backend/`** - Primary AWS backend deployment (in root workspace)
2. **`HCV-PRO-AWS/`** - AWS configuration files (minimal)
3. **`HCV-PRO-AWS-DEPLOY/`** - Complete AWS deployment package (full copy)

---

## 📂 Directory Structure

### 1. `aws-backend/` (Primary AWS Backend)

**Location**: `./aws-backend/`  
**Type**: Complete backend deployment package  
**Size**: ~90 files, 9 directories  
**Status**: ✅ Production-ready

#### Core Configuration Files

| File | Purpose | Type |
|------|---------|------|
| `Dockerfile` | Docker container configuration | Docker |
| `requirements.txt` | Python dependencies | pip |
| `wsgi.py` | WSGI application entry point | Python |
| `serverless.py` | Vercel serverless handler | Python |
| `vercel.json` | Vercel deployment config | JSON |
| `package.json` | Node.js dependencies | JSON |
| `package-lock.json` | Node.js lock file | JSON |
| `.dockerignore` | Docker build exclusions | Config |
| `.gitignore` | Git exclusions | Config |
| `.vercelignore` | Vercel exclusions | Config |

#### Deployment Scripts

| File | Purpose |
|------|---------|
| `AWS_DEPLOY_NOW.sh` | Automated AWS deployment script |
| `start.sh` | Linux startup script |
| `start.bat` | Windows startup script |
| `vercel-build.sh` | Vercel build script |

#### Deployment Documentation

| File | Purpose |
|------|---------|
| `AWS_DEPLOY.md` | Quick AWS deployment guide |
| `AWS_DEPLOYMENT_GUIDE.md` | Detailed AWS deployment guide (French) |
| `AWS_DEPLOYMENT_COMPLETE.md` | Deployment completion report |
| `GUIDE_CREDENTIALS_AWS.md` | AWS credentials setup guide |
| `DEPLOYMENT_STRATEGY.md` | Overall deployment strategy |
| `README-DEPLOYMENT.md` | Deployment README |

#### Application Code

| Directory | Contents |
|-----------|----------|
| `server/` | Main Flask server (`hcv_pro_server.py`) |
| `api/` | API endpoints and handlers |
| `codecs/` | Video codec implementations |
| `mobile/` | Mobile integration code |
| `web/` | Web templates and frontend |
| `wasm/` | WebAssembly modules |
| `aws-frontend/` | AWS frontend HTML files |
| `docs/` | Technical documentation |

#### Key Application Files

| File | Purpose |
|------|---------|
| `server/hcv_pro_server.py` | Main Flask application |
| `api/hcv_engine.py` | HCV compression engine |
| `api/video_decoders.py` | Video decoding utilities |
| `codecs/hcv_pro_codec.py` | Main HCV codec |
| `codecs/hcv_video_boost_codec.py` | Video boost codec |
| `codecs/hcv_mobile_camera_codec.py` | Mobile camera codec |
| `mobile/main.py` | Mobile integration entry point |
| `wasm/delta_h.wasm` | WebAssembly binary |

#### Utility Files

| File | Purpose |
|------|---------|
| `minify.js` | JavaScript minification |
| `hcvb_decoder.py` | HCVB format decoder |
| `_measure_psnr.py` | PSNR measurement utility |
| `test_audio_encoding.py` | Audio encoding tests |

---

### 2. `HCV-PRO-AWS/` (AWS Configuration)

**Location**: `./HCV-PRO-AWS/`  
**Type**: AWS configuration files (minimal)  
**Size**: ~8 files  
**Status**: ⚠️ Partial configuration

#### Files

| File | Purpose |
|------|---------|
| `.dockerignore` | Docker build exclusions |
| `.vercelignore` | Vercel exclusions |
| `AWS_DEPLOY.md` | AWS deployment guide |
| `ARCHITECTURE_GLOBALE.md` | Global architecture documentation |
| `AUDIO_COMPRESSION_STRATEGY.md` | Audio compression strategy |
| `4K_8K_UPSCALE_STRATEGY.md` | 4K/8K upscaling strategy |
| `ALL_UPSCALING_COMPLETE_SUMMARY.md` | Upscaling summary |
| `aws/` | AWS credentials/config directory |

---

### 3. `HCV-PRO-AWS-DEPLOY/` (Complete AWS Deployment Package)

**Location**: `./HCV-PRO-AWS-DEPLOY/`  
**Type**: Full deployment package (mirror of aws-backend)  
**Size**: ~90 files, 10 directories  
**Status**: ✅ Complete backup/mirror

#### Structure (Same as aws-backend)

- `render-backend/` - Backend deployment configuration
- `render-frontend/` - Frontend deployment configuration
- `api/` - API implementations
- `codecs/` - Codec implementations
- `server/` - Server code
- `mobile/` - Mobile code
- `web/` - Web templates
- `wasm/` - WebAssembly modules
- `aws-frontend/` - AWS frontend
- `docs/` - Documentation

#### Key Differences from aws-backend

| Feature | aws-backend | HCV-PRO-AWS-DEPLOY |
|---------|-------------|-------------------|
| Render backend config | ❌ No | ✅ Yes |
| Render frontend config | ❌ No | ✅ Yes |
| Elastic Beanstalk config | ❌ No | ✅ Yes (.ebextensions) |
| Python version file | ❌ No | ✅ Yes (.python-version) |
| Runtime config | ❌ No | ✅ Yes (runtime.txt) |

---

## 🔧 Critical Deployment Files

### For Docker Deployment

```
aws-backend/Dockerfile
aws-backend/requirements.txt
aws-backend/.dockerignore
aws-backend/server/hcv_pro_server.py
```

### For Vercel Deployment

```
aws-backend/vercel.json
aws-backend/serverless.py
aws-backend/vercel-build.sh
aws-backend/package.json
```

### For Elastic Beanstalk Deployment

```
HCV-PRO-AWS-DEPLOY/render-backend/Procfile
HCV-PRO-AWS-DEPLOY/render-backend/requirements.txt
HCV-PRO-AWS-DEPLOY/render-backend/.ebextensions/
HCV-PRO-AWS-DEPLOY/render-backend/.elasticbeanstalk/
HCV-PRO-AWS-DEPLOY/render-backend/wsgi.py
```

### For AWS App Runner Deployment

```
aws-backend/Dockerfile
aws-backend/requirements.txt
aws-backend/server/hcv_pro_server.py
```

---

## 📋 Deployment Configuration Files

### Python Dependencies

**File**: `aws-backend/requirements.txt`

```
Flask==2.3.3
numpy==1.24.3
opencv-python==4.8.0.74
Werkzeug==2.3.7
zstandard>=0.21.0
```

### Docker Configuration

**File**: `aws-backend/Dockerfile`

- **Base Image**: `python:3.11-slim`
- **Build Stage**: Multi-stage build with dependencies
- **Runtime Dependencies**: ffmpeg, libgomp1
- **Port**: 3000
- **Entry Point**: `python server/hcv_pro_server.py`

### Vercel Configuration

**File**: `aws-backend/vercel.json`

```json
{
  "version": 2,
  "builds": [
    {
      "src": "server/hcv_pro_server.py",
      "use": "@vercel/python"
    },
    {
      "src": "web/templates/*.html",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "server/hcv_pro_server.py"
    },
    {
      "src": "/(.*)",
      "dest": "web/templates/$1"
    }
  ]
}
```

### Elastic Beanstalk Configuration

**File**: `HCV-PRO-AWS-DEPLOY/render-backend/Procfile`

```
web: gunicorn -w 4 -b 0.0.0.0:$PORT app:app
```

---

## 🚀 Deployment Platforms Supported

### 1. Docker (Container)
- **Primary Use**: AWS ECS, App Runner, Kubernetes
- **Config**: `Dockerfile`
- **Status**: ✅ Ready

### 2. Vercel (Serverless)
- **Primary Use**: Serverless functions
- **Config**: `vercel.json`, `serverless.py`
- **Status**: ✅ Ready

### 3. AWS Elastic Beanstalk
- **Primary Use**: Managed web service
- **Config**: `Procfile`, `.ebextensions/`
- **Status**: ✅ Ready (in HCV-PRO-AWS-DEPLOY)

### 4. AWS App Runner
- **Primary Use**: Container-based service
- **Config**: `Dockerfile`, `requirements.txt`
- **Status**: ✅ Ready

### 5. Render (Alternative)
- **Primary Use**: Alternative cloud platform
- **Config**: `render.yaml`, `requirements.txt`
- **Status**: ✅ Ready (in HCV-PRO-AWS-DEPLOY)

---

## 📊 File Statistics

### aws-backend/

| Category | Count |
|----------|-------|
| Python files | 15+ |
| Configuration files | 8 |
| Documentation files | 40+ |
| Shell scripts | 3 |
| JSON files | 3 |
| HTML files | 3 |
| WebAssembly files | 1 |
| **Total** | **~90** |

### HCV-PRO-AWS-DEPLOY/

| Category | Count |
|----------|-------|
| Python files | 20+ |
| Configuration files | 15 |
| Documentation files | 50+ |
| Shell scripts | 3 |
| JSON files | 5 |
| HTML files | 5 |
| WebAssembly files | 1 |
| **Total** | **~100** |

---

## 🔐 Security & Configuration Files

### Environment Variables

**File**: `HCV-PRO-AWS-DEPLOY/render-backend/.env.example`

```
FLASK_ENV=production
FLASK_DEBUG=false
HCV_PRO_SECRET=your-secret-key
HCV_PRO_API_KEY_REQUIRED=true
HCV_PRO_RATE_LIMIT=100
```

### Git Ignore Patterns

**File**: `aws-backend/.gitignore`

```
aws
render-backend
render-frontend
```

### Docker Ignore Patterns

**File**: `aws-backend/.dockerignore`

```
node_modules
__pycache__
*.pyc
*.log
tests/
*.md
docs/
```

---

## 📚 Documentation Files

### Deployment Guides

| File | Purpose |
|------|---------|
| `AWS_DEPLOY.md` | Quick start guide |
| `AWS_DEPLOYMENT_GUIDE.md` | Detailed guide (French) |
| `GUIDE_CREDENTIALS_AWS.md` | Credentials setup |
| `DEPLOYMENT_STRATEGY.md` | Strategy overview |
| `README-DEPLOYMENT.md` | Deployment README |

### Architecture & Strategy

| File | Purpose |
|------|---------|
| `ARCHITECTURE_GLOBALE.md` | Global architecture |
| `AUDIO_COMPRESSION_STRATEGY.md` | Audio strategy |
| `4K_8K_UPSCALE_STRATEGY.md` | Upscaling strategy |
| `DEPLOYMENT_STRATEGY.md` | Deployment strategy |

### Performance & Testing

| File | Purpose |
|------|---------|
| `PERFORMANCE_GUIDE.md` | Performance optimization |
| `TEST_MOBILE_UPSCALING.md` | Mobile testing |
| `TEST_VIDEO_BOOST_UPSCALING.md` | Video boost testing |

---

## 🔄 Deployment Workflow

### Step 1: Prepare Environment
```bash
# Install AWS CLI and EB CLI
pip install awscli awsebcli

# Configure credentials
aws configure
```

### Step 2: Choose Deployment Method

**Option A: Docker (Recommended)**
```bash
cd aws-backend
docker build -t hcv-pro-backend .
docker run -p 3000:3000 hcv-pro-backend
```

**Option B: Vercel**
```bash
cd aws-backend
vercel deploy
```

**Option C: Elastic Beanstalk**
```bash
cd HCV-PRO-AWS-DEPLOY/render-backend
eb init
eb create hcv-pro-env
eb deploy
```

**Option D: AWS App Runner**
```bash
# Push Docker image to ECR
# Create App Runner service from ECR image
```

### Step 3: Verify Deployment
```bash
curl http://your-deployment-url/health
```

---

## ✅ Deployment Checklist

### Pre-Deployment

- [ ] AWS account created
- [ ] AWS CLI installed and configured
- [ ] Docker installed (for container deployments)
- [ ] Git repository initialized
- [ ] All dependencies in `requirements.txt`
- [ ] Environment variables configured
- [ ] Security credentials secured

### Deployment

- [ ] Choose deployment platform
- [ ] Configure platform-specific files
- [ ] Build/package application
- [ ] Deploy to platform
- [ ] Verify health check endpoint
- [ ] Test API endpoints
- [ ] Monitor logs and metrics

### Post-Deployment

- [ ] Set up monitoring/alerts
- [ ] Configure auto-scaling
- [ ] Set up CI/CD pipeline
- [ ] Document deployment URLs
- [ ] Create runbooks for common issues
- [ ] Schedule regular backups

---

## 🆘 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Docker build fails | Check `requirements.txt` for missing packages |
| Port 3000 already in use | Change port in `Dockerfile` or `wsgi.py` |
| Missing dependencies | Run `pip install -r requirements.txt` |
| Vercel deployment fails | Check `vercel.json` configuration |
| EB deployment fails | Check `.ebextensions/` configuration |

### Debug Commands

```bash
# Check Docker image
docker images

# View container logs
docker logs <container-id>

# Check EB status
eb status

# View EB logs
eb logs --stream

# Test local server
python server/hcv_pro_server.py
```

---

## 📞 Support Resources

- [AWS Documentation](https://docs.aws.amazon.com/)
- [Docker Documentation](https://docs.docker.com/)
- [Vercel Documentation](https://vercel.com/docs)
- [Elastic Beanstalk Guide](https://docs.aws.amazon.com/elasticbeanstalk/)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

## 📝 Summary

**Total AWS Deployment Files**: ~190 files across 3 directories

**Primary Deployment Package**: `aws-backend/`
- ✅ Docker-ready
- ✅ Vercel-ready
- ✅ AWS App Runner-ready

**Complete Deployment Package**: `HCV-PRO-AWS-DEPLOY/`
- ✅ Includes Elastic Beanstalk configuration
- ✅ Includes Render configuration
- ✅ Full backup of all deployment files

**Recommended Deployment**: Docker + AWS App Runner or Elastic Beanstalk

---

**Generated**: 24 Avril 2026  
**Status**: ✅ Complete Inventory  
**Next Steps**: Choose deployment platform and follow deployment guide
