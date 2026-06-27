# Harmonic AI SaaS Dashboard

Complete SaaS dashboard for integration with LM Arena services and harmonic audio/video technologies.

## ðŸš€ Features

### Chat & LM Arena
- **Response generation** with DeepSeek API AWS (__EC2_IP__:8000)
- **Verified mode** with citations and structured abstention
- **Guaranteed determinism** (temperature=0, LRU cache)
- **LM Arena optimization** with specific parameters

### Harmonic Audio Processing
- **HCS Restore** - Complete audio restoration
- **HCS Spatial** - Immersive 3D spatial enhancement
- **HCS Clarity** - Optimal clarity and sharpness
- **HCS Dynamic** - Extended dynamic range

### Harmonic Video Processing
- **HCS 4K Clarity** - 4K upscaling with optimal clarity
- **HCS 8K Master** - Professional 8K mastering
- **HCS HDR Vision** - Advanced HDR conversion
- **HCS Frame Generation** - Intermediate frame generation
- **HCS Movie Continuous** - Continuous movie generation

### SaaS Management
- **Authentication** JWT with refresh tokens
- **Subscriptions** (Free, Pro, Enterprise)
- **Billing** Stripe integration
- **API Keys** with granular permissions
- **Monitoring** Prometheus + Grafana

## ðŸ—ï¸ Architecture

```
harmonic_saas/
â”œâ”€â”€ app/                    # FastAPI Backend
â”‚   â”œâ”€â”€ api/v1/endpoints/  # API Endpoints
â”‚   â”œâ”€â”€ core/              # Configuration, security, database
â”‚   â”œâ”€â”€ models/            # SQLAlchemy Models
â”‚   â”œâ”€â”€ schemas/           # Pydantic Schemas
â”‚   â”œâ”€â”€ services/          # Business Services
â”‚   â””â”€â”€ tasks/             # Celery Async Tasks
â”œâ”€â”€ frontend/              # User Interface
â”œâ”€â”€ docker-compose.yml     # Docker Orchestration
â”œâ”€â”€ Dockerfile            # API Docker Image
â””â”€â”€ requirements.txt      # Python Dependencies
```

## ðŸ“¦ Dependencies

### Backend (FastAPI)
- FastAPI 0.104.1 + Uvicorn
- SQLAlchemy + Alembic (PostgreSQL)
- Redis + Celery (async tasks)
- JWT authentication
- Prometheus metrics
- Stripe API (billing)

### Frontend
- HTML5 + CSS3 + Vanilla JavaScript
- Font Awesome icons
- Google Fonts (Inter)
- Chart.js (charts)

### Infrastructure
- Docker + Docker Compose
- PostgreSQL 15
- Redis 7
- MongoDB 6
- Prometheus + Grafana

## ðŸš€ Quick Start

### Option 1: Windows Script (recommended)
```bash
cd harmonic_saas
start_all.bat
```

### Option 2: Manual with Docker Compose
```bash
cd harmonic_saas

# Start base services
docker-compose up -d postgres redis mongodb

# Wait for initialization
sleep 10

# Start API
docker-compose up -d api

# Check logs
docker-compose logs -f api
```

### Option 3: Local Development
```bash
cd harmonic_saas

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
copy .env.example .env
# Edit .env with your configuration

# Start services
docker-compose up -d postgres redis mongodb

# Run database migrations
alembic upgrade head

# Start API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## ðŸ”§ Configuration

### Environment Variables
Create a `.env` file with the following variables:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/harmonic_saas
REDIS_URL=redis://localhost:6379/0
MONGODB_URL=mongodb://localhost:27017/harmonic_saas

# Security
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AWS DeepSeek API
DEEPSEEK_API_URL=http://__EC2_IP__:8000
DEEPSEEK_API_KEY=your-api-key-here

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Harmonic Services
HCS_AUDIO_URL=http://localhost:9017
HCS_VIDEO_URL=http://localhost:9018
```

### Docker Configuration
The `docker-compose.yml` file includes:
- PostgreSQL database
- Redis cache
- MongoDB for document storage
- FastAPI application
- Celery worker for async tasks
- Flower for Celery monitoring
- Prometheus for metrics
- Grafana for dashboards

## ðŸ“Š Monitoring

### Metrics
- **API Metrics**: Request count, latency, error rates
- **Database Metrics**: Connection pool, query performance
- **Cache Metrics**: Hit rate, memory usage
- **Business Metrics**: User activity, subscription status

### Logs
- **Application Logs**: Structured JSON logs
- **Access Logs**: HTTP request/response logs
- **Error Logs**: Exception and error tracking
- **Audit Logs**: Security and compliance logs

## ðŸ”’ Security

### Authentication
- JWT-based authentication
- Refresh token rotation
- Password hashing with bcrypt
- Rate limiting per user/IP

### Authorization
- Role-based access control (RBAC)
- API key permissions
- Subscription tier restrictions
- Resource ownership validation

### Data Protection
- HTTPS/TLS encryption
- Database encryption at rest
- Secure password storage
- Regular security audits

## ðŸš€ Deployment

### AWS Deployment
See `docs/guides/aws_deployment.md` for complete AWS deployment guide.

### Docker Deployment
```bash
# Build and deploy
docker-compose build
docker-compose up -d

# Scale services
docker-compose up -d --scale api=3 --scale celery_worker=2
```

### Kubernetes Deployment
Kubernetes manifests are available in the `k8s/` directory.

## ðŸ“š Documentation

### Complete Documentation
- **Overview**: `docs/guides/overview.md` (this file)
- **Quick Start**: `docs/guides/quick_start.md`
- **LM Arena Guide**: `docs/guides/lm_arena_guide.md`
- **AWS Deployment**: `docs/guides/aws_deployment.md`
- **Checklist**: `docs/guides/checklist.md`

### Reference Documentation
- **Harmonic Discovery**: `docs/reference/harmonic_discovery.md`
- **Community Proof**: `docs/reference/community_proof.md`
- **Patent**: `docs/reference/patent.md`

## ðŸ¤ Support

### Community Support
- GitHub Issues for bug reports
- Documentation for common issues
- Community forums for discussions

### Professional Support
Available with Pro and Enterprise subscriptions:
- Priority support
- Custom integrations
- Dedicated account manager
- SLA guarantees

## ðŸ“„ License

This project is proprietary software. All rights reserved.

---

**Harmonic AI** - Community-Proof AI Technology