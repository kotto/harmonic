# LM Arena Package - Harmonic AI

## Overview

The **LM Arena Package** is a complete solution for participating in the LM Arena evaluation platform using the **Harmonic AI** approach. It integrates:

- **API Backend**: FastAPI server with optimized endpoints for LM Arena
- **Harmonic Services**: Advanced audio and video processing with harmonic approach
- **Frontend**: Modern user interface for testing and demonstrations
- **Monitoring**: Metrics and logs for performance surveillance
- **Automation Scripts**: Installation, startup, testing, and maintenance

## Key Advantages

- ✅ **Guaranteed Determinism**: Same prompt → Same output (temperature=0)
- ✅ **Verified Mode**: Mandatory citations for factual claims
- ✅ **Zero Hallucination**: Abstention when sources are insufficient
- ✅ **Optimized Performance**: Average latency < 2 seconds
- ✅ **Complete Integration**: Ready for immediate LM Arena submission

## Quick Start

### Installation

#### Option 1: Automatic Installation (Linux/macOS)
```bash
# Download the package
git clone <repository-url>
cd lm_arena_package

# Run installation script
chmod +x scripts/install.sh
./scripts/install.sh
```

#### Option 2: Automatic Installation (Windows)
```powershell
# Download the package
git clone <repository-url>
cd lm_arena_package

# Run installation script
.\scripts\install_windows.ps1
```

### Starting Services

#### Linux/macOS
```bash
./scripts/start.sh
```

#### Windows
```batch
.\scripts\start_windows.bat
```

### Access Services

- **API Backend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend**: http://localhost:8080
- **Monitoring**: http://localhost:9090

## Architecture

### Directory Structure
```
lm_arena_package/
├── backend/                    # FastAPI Backend
├── frontend/                   # User Interface
├── scripts/                    # Automation Scripts
├── docs/                       # Documentation
├── tests/                      # Automated Tests
├── config/                     # Configuration
├── aws/                        # AWS Configuration
└── monitoring/                 # Monitoring & Metrics
```

### Main Components

#### 1. FastAPI Backend
- **Framework**: FastAPI with Uvicorn
- **Database**: PostgreSQL with SQLAlchemy
- **Cache**: Redis for performance
- **Async Tasks**: Celery with Flower
- **Authentication**: JWT with OAuth2

#### 2. Harmonic Services
- **Audio Service**: Port 9017 - Advanced audio processing
- **Video Service**: Port 9018 - 8K video processing
- **REST API**: Standardized endpoints for integration

#### 3. Frontend
- **HTML/CSS/JavaScript**: Modern user interface
- **Dark Theme**: Native dark theme support
- **Responsive**: Mobile and desktop compatible

#### 4. Monitoring
- **Prometheus**: Metrics collection
- **Grafana**: Dashboards (optional)
- **Structured Logs**: JSON with structlog

## Features

### Core Features
1. **Deterministic Generation**: Guaranteed identical outputs for identical inputs
2. **Verified Responses**: Citations for all factual claims
3. **Multimodal Support**: Text, image, audio, and video processing
4. **Performance Optimization**: Sub-2-second average latency
5. **Scalable Architecture**: Ready for production deployment

### LM Arena Integration
- **Optimized Endpoints**: Specifically designed for LM Arena evaluation
- **Compliance Ready**: Meets all LM Arena technical requirements
- **Performance Monitoring**: Real-time metrics for LM Arena performance
- **Submission Ready**: Complete documentation for LM Arena submission

## Getting Started

### Prerequisites

#### Linux/macOS
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git curl

# CentOS/RHEL
sudo yum install -y python3 python3-pip python3-virtualenv git curl

# macOS (with Homebrew)
brew install python3 git curl
```

#### Windows
- **Python 3.8+**: [Download from python.org](https://www.python.org/downloads/)
- **Git**: [Download from git-scm.com](https://git-scm.com/download/win)
- **PowerShell 5.1+**: Included in Windows 10/11

### Configuration

1. **Copy environment file**:
```bash
cp config/.env.example config/.env
```

2. **Edit configuration**:
```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Database
DATABASE_URL=postgresql://user:password@localhost/harmonic_ai
REDABASE_URL=redis://localhost:6379/0

# Security
JWT_SECRET_KEY=your-secret-key-here
API_KEY_HEADER=X-API-Key

# LM Arena
LM_ARENA_API_URL=https://arena.lmsys.org
LM_ARENA_TIMEOUT=30

# External APIs (optional)
DEEPSEEK_API_KEY=your-deepseek-api-key
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
```

## Usage

### API Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Text Generation
```bash
curl -X POST http://localhost:8000/api/v1/chat/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"prompt": "Hello, how are you?", "temperature": 0.0}'
```

#### Audio Processing
```bash
curl http://localhost:9017/health
```

#### Video Processing
```bash
curl http://localhost:9018/health
```

### Testing

#### Run All Tests
```bash
cd tests
pytest
```

#### LM Arena Specific Tests
```bash
python tests/performance/lm_arena_test.py
```

#### Integration Tests
```bash
python tests/integration/test_lm_arena.py
```

## Deployment

### Local Deployment
```bash
# Start all services
./scripts/start.sh

# Or for Windows
.\scripts\start_windows.bat
```

### Docker Deployment
```bash
# Using Docker Compose
docker-compose -f config/docker-compose.yml up -d
```

### AWS Deployment
```bash
# Deploy to AWS EC2
cd aws/ec2
./setup.sh
```

## Monitoring

### Metrics
- **API Performance**: Response times, error rates, throughput
- **Service Health**: Uptime, resource usage, connectivity
- **LM Arena Performance**: Win rates, Elo scores, user feedback

### Logs
- **Structured Logging**: JSON format for easy parsing
- **Centralized Logs**: All services log to centralized location
- **Real-time Monitoring**: Live log streaming and analysis

## Support

### Documentation
- **Complete Guide**: `docs/guides/overview.md`
- **Installation Guide**: `docs/guides/quick_start.md`
- **Deployment Guide**: `docs/guides/aws_deployment.md`
- **LM Arena Guide**: `docs/guides/lm_arena_guide.md`

### Resources
- **Harmonic AI Website**: [harmonic-ai.com](https://harmonic-ai.com)
- **LM Arena Documentation**: [arena.lmsys.org/docs](https://arena.lmsys.org/docs)
- **Technical Support**: support@harmonic-ai.com

### Community
- **Forum**: [forum.harmonic-ai.com](https://forum.harmonic-ai.com)
- **GitHub**: [github.com/harmonic-ai](https://github.com/harmonic-ai)
- **Discord**: [discord.gg/harmonic-ai](https://discord.gg/harmonic-ai)

## Contributing

We welcome contributions! Please see our contribution guidelines in `CONTRIBUTING.md`.

## License

This project is proprietary software. All rights reserved.

## Contact

For questions, suggestions, or issues:
- **Email**: contact@harmonic-ai.com
- **Website**: [harmonic-ai.com](https://harmonic-ai.com)
- **Documentation**: [docs.harmonic-ai.com](https://docs.harmonic-ai.com)

**Harmonic AI - The Community-Proof AI** 🚀

---

*Document generated: May 17, 2026*  
*Last updated: May 17, 2026*  
*Version: 1.0.0*