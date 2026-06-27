# LM Arena Package Installation Guide

## Overview

This guide provides complete installation instructions for the LM Arena Package. The package includes all components needed to participate in the LM Arena evaluation platform using the Harmonic AI approach.

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11, Linux (Ubuntu 20.04+), macOS 11+
- **CPU**: 4 cores, 2.5 GHz or higher
- **RAM**: 8 GB minimum, 16 GB recommended
- **Storage**: 10 GB free space
- **Network**: Stable internet connection

### Recommended Requirements
- **CPU**: 8 cores, 3.0 GHz or higher
- **RAM**: 32 GB
- **Storage**: 50 GB SSD
- **GPU**: NVIDIA GPU with 8+ GB VRAM (optional, for local inference)

## Installation Methods

### Method 1: Automatic Installation (Recommended)

#### Linux/macOS
```bash
# Download the package
git clone <repository-url>
cd lm_arena_package

# Make installation script executable
chmod +x scripts/install.sh

# Run installation
./scripts/install.sh
```

#### Windows
```powershell
# Download the package
git clone <repository-url>
cd lm_arena_package

# Run installation script
.\scripts\install_windows.ps1
```

### Method 2: Manual Installation

#### Step 1: Clone Repository
```bash
git clone <repository-url>
cd lm_arena_package
```

#### Step 2: Create Virtual Environment
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

#### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r config/requirements.txt
```

#### Step 4: Configure Environment
```bash
# Copy example environment file
cp config/.env.example config/.env

# Edit configuration (see Configuration section below)
# nano config/.env  # or use your preferred editor
```

#### Step 5: Initialize Database
```bash
# Run database migrations
cd backend
alembic upgrade head
```

## Configuration

### Environment Variables

Create or edit `config/.env` with the following settings:

```env
# ==============================================
# API Configuration
# ==============================================
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_RELOAD=true

# ==============================================
# Database Configuration
# ==============================================
DATABASE_URL=postgresql://user:password@localhost:5432/harmonic_ai
REDIS_URL=redis://localhost:6379/0
MONGODB_URL=mongodb://localhost:27017/harmonic_saas

# ==============================================
# Security Configuration
# ==============================================
SECRET_KEY=your-secret-key-here-change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
API_KEY_HEADER=X-API-Key

# ==============================================
# LM Arena Configuration
# ==============================================
LM_ARENA_API_URL=https://arena.lmsys.org
LM_ARENA_TIMEOUT=30
LM_ARENA_MAX_RETRIES=3

# ==============================================
# External API Configuration (Optional)
# ==============================================
DEEPSEEK_API_URL=http://__EC2_IP__:8000
DEEPSEEK_API_KEY=your-deepseek-api-key
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# ==============================================
# Harmonic Services Configuration
# ==============================================
HCS_AUDIO_URL=http://localhost:9017
HCS_VIDEO_URL=http://localhost:9018
HCS_TIMEOUT=60

# ==============================================
# Monitoring Configuration
# ==============================================
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
LOGGING_LEVEL=INFO
```

### Configuration Files

#### `config/environments/development.yaml`
```yaml
api:
  host: 0.0.0.0
  port: 8000
  workers: 2
  reload: true

database:
  postgres:
    host: localhost
    port: 5432
    database: harmonic_ai_dev
    username: postgres
    password: postgres
  redis:
    host: localhost
    port: 6379
    db: 0

logging:
  level: DEBUG
  format: json
```

#### `config/environments/production.yaml`
```yaml
api:
  host: 0.0.0.0
  port: 8000
  workers: 8
  reload: false

database:
  postgres:
    host: ${DATABASE_HOST}
    port: ${DATABASE_PORT}
    database: ${DATABASE_NAME}
    username: ${DATABASE_USER}
    password: ${DATABASE_PASSWORD}
  redis:
    host: ${REDIS_HOST}
    port: ${REDIS_PORT}
    db: ${REDIS_DB}

logging:
  level: INFO
  format: json
```

## Service Startup

### Starting All Services

#### Linux/macOS
```bash
./scripts/start.sh
```

#### Windows
```batch
.\scripts\start_windows.bat
```

### Starting Individual Services

#### API Backend
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend
```bash
cd frontend
# Serve static files (using Python's HTTP server)
python -m http.server 8080
```

#### Harmonic Audio Service
```bash
# The service runs on port 9017
# Check health: curl http://localhost:9017/health
```

#### Harmonic Video Service
```bash
# The service runs on port 9018
# Check health: curl http://localhost:9018/health
```

## Docker Installation

### Using Docker Compose

```bash
# Build and start all services
docker-compose -f config/docker-compose.yml up -d

# View logs
docker-compose -f config/docker-compose.yml logs -f

# Stop services
docker-compose -f config/docker-compose.yml down
```

### Docker Services

The Docker Compose configuration includes:
- **PostgreSQL**: Database for user data and application state
- **Redis**: Cache and session storage
- **MongoDB**: Document storage for logs and analytics
- **FastAPI**: Main application backend
- **Celery Worker**: Async task processing
- **Flower**: Celery monitoring interface
- **Prometheus**: Metrics collection
- **Grafana**: Monitoring dashboards (optional)

## Verification

### Health Checks

```bash
# API Health
curl http://localhost:8000/health

# Audio Service Health
curl http://localhost:9017/health

# Video Service Health
curl http://localhost:9018/health

# Database Connectivity
curl http://localhost:8000/api/v1/health/db
```

### Test Endpoints

```bash
# Test text generation
curl -X POST http://localhost:8000/api/v1/chat/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key" \
  -d '{"prompt": "Hello, world!", "temperature": 0.0}'

# Test LM Arena integration
curl http://localhost:8000/api/v1/lm-arena/status
```

## Troubleshooting

### Common Issues

#### 1. Port Conflicts
```
Error: Address already in use
```
**Solution**: Change port numbers in `config/.env` or stop conflicting services.

#### 2. Database Connection Issues
```
Error: Could not connect to database
```
**Solution**: 
- Verify database service is running
- Check connection credentials in `config/.env`
- Ensure firewall allows connections

#### 3. Missing Dependencies
```
Error: Module not found
```
**Solution**: 
```bash
pip install -r config/requirements.txt --upgrade
```

#### 4. Permission Issues
```
Error: Permission denied
```
**Solution**: 
- Run with appropriate permissions
- Check file/directory permissions
- Use `sudo` on Linux/macOS if needed

### Logs Location

- **Application Logs**: `logs/app.log`
- **Error Logs**: `logs/error.log`
- **Access Logs**: `logs/access.log`
- **Docker Logs**: Use `docker-compose logs`

## Next Steps

After successful installation:

1. **Configure LM Arena Integration**: Set up API keys and endpoints
2. **Set Up Monitoring**: Configure Prometheus and Grafana
3. **Test Performance**: Run LM Arena test scripts
4. **Deploy to Production**: Follow deployment guide

## Support

- **Documentation**: See `docs/guides/` for detailed guides
- **Issues**: Report problems via GitHub Issues
- **Community**: Join our Discord server for help
- **Email**: Contact support@harmonic-ai.com

---

**Last Updated**: May 17, 2026  
**Version**: 1.0.0  
**Package**: LM Arena Package  
**Status**: Ready for Installation