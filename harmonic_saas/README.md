# Harmonic AI SaaS Dashboard

Dashboard SaaS complet pour l'intÃ©gration avec les services LM Arena et les technologies harmoniques audio/vidÃ©o.

## ðŸš€ FonctionnalitÃ©s

### Chat & LM Arena
- **GÃ©nÃ©ration de rÃ©ponses** avec DeepSeek API AWS (__EC2_IP__:8000)
- **Mode vÃ©rifiÃ©** avec citations et abstention structurÃ©e
- **DÃ©terminisme garanti** (temperature=0, cache LRU)
- **Optimisation LM Arena** avec paramÃ¨tres spÃ©cifiques

### Traitement Audio Harmonique
- **HCS Restore** - Restauration audio complÃ¨te
- **HCS Spatial** - AmÃ©lioration spatiale 3D immersive
- **HCS Clarity** - ClartÃ© et nettetÃ© optimale
- **HCS Dynamic** - Plage dynamique Ã©tendue

### Traitement VidÃ©o Harmonique
- **HCS 4K Clarity** - Upscaling 4K avec clartÃ© optimale
- **HCS 8K Master** - Masterisation 8K professionnelle
- **HCS HDR Vision** - Conversion HDR avancÃ©e
- **HCS Frame Generation** - GÃ©nÃ©ration de frames intermÃ©diaires
- **HCS Movie Continuous** - GÃ©nÃ©ration de films continus

### Gestion SaaS
- **Authentification** JWT avec refresh tokens
- **Abonnements** (Free, Pro, Enterprise)
- **Facturation** intégration Stripe
- **API Keys** avec permissions granulaires
- **Monitoring** Prometheus + Grafana

### 🧠 Datacenter Holographique (NEW)
- **Ingestion One-Pass** — Entraînement holographique CPU, zéro GPU
- **Génération Enrichie** — Réponses augmentées par hologramme 32 Ko
- **Sessions Multi-Clients** — Un .holo par client
- **Dashboard** — Métriques temps réel (tokens, énergie, stockage)

### 🔬 HPC / Calcul Scientifique (NEW)
- **Protein Folding** — Repliement protéique par résonance harmonique (φ-accélération)
- **Quantum Simulation** — Simulation quantique avec optimisation harmonique
- **NP-Complet** — Solveur SAT, TSP par optimisation φ
- **Médecine, Physique, Chimie** — Calcul scientifique 6-37x plus rapide

### 📚 Base de Connaissances (NEW)
- **Ingestion Intelligente** — Extraction de triplets (sujet, relation, objet)
- **Recherche Sémantique** — Retrieval par résonance harmonique
- **Émergence de Patterns** — Détection automatique de régularités
- **Cross-Lingual FR/EN** — Alignement Procrustes

### 🧠 Raisonnement Conscient (NEW)
- **Chaînage** — Inférence transitive par cohérence de phase
- **Analogie** — A:B :: C:? par arithmétique vectorielle
- **Contradictions** — Détection par interférence destructive
- **Généralisation** — Abstraction automatique

### 💻 Code Intelligent (NEW)
- **Génération Zero-LLM** — Code sans GPU, sans LLM
- **Explication** — Analyse ligne par ligne
- **Traduction** — Python ↔ JavaScript ↔ Go ↔ Rust
- **Refactoring** — Patterns, performance, lisibilité

### 🌊 Wave & Créativité (NEW)
- **Explication Scientifique** — Physique, biologie, astronomie, quantique
- **Cross-Lingual** — Alignement conceptuel FR/EN sans traduction
- **Créativité** — Haïkus, métaphores, poèmes par résonance φ

## ðŸ—ï¸ Architecture

```
harmonic_saas/
â”œâ”€â”€ app/                    # Backend FastAPI
â”‚   â”œâ”€â”€ api/v1/endpoints/  # Endpoints API
â”‚   â”œâ”€â”€ core/              # Configuration, sÃ©curitÃ©, base de donnÃ©es
â”‚   â”œâ”€â”€ models/            # ModÃ¨les SQLAlchemy
â”‚   â”œâ”€â”€ schemas/           # SchÃ©mas Pydantic
â”‚   â”œâ”€â”€ services/          # Services mÃ©tier
â”‚   â””â”€â”€ tasks/             # TÃ¢ches Celery asynchrones
â”œâ”€â”€ frontend/              # Interface utilisateur
â”œâ”€â”€ docker-compose.yml     # Orchestration Docker
â”œâ”€â”€ Dockerfile            # Image Docker API
â””â”€â”€ requirements.txt      # DÃ©pendances Python
```

## ðŸ“¦ DÃ©pendances

### Backend (FastAPI)
- FastAPI 0.104.1 + Uvicorn
- SQLAlchemy + Alembic (PostgreSQL)
- Redis + Celery (tÃ¢ches asynchrones)
- JWT authentication
- Prometheus metrics
- Stripe API (facturation)

### Frontend
- HTML5 + CSS3 + JavaScript vanilla
- Font Awesome icons
- Google Fonts (Inter)
- Chart.js (graphiques)

### Infrastructure
- Docker + Docker Compose
- PostgreSQL 15
- Redis 7
- MongoDB 6
- Prometheus + Grafana

## ðŸš€ DÃ©marrage rapide

### Option 1: Script Windows (recommandÃ©)
```bash
cd harmonic_saas
start_all.bat
```

### Option 2: Manuel avec Docker Compose
```bash
cd harmonic_saas

# DÃ©marrer les services de base
docker-compose up -d postgres redis mongodb

# Attendre l'initialisation
sleep 10

# DÃ©marrer l'API
docker-compose up -d api

# VÃ©rifier les logs
docker-compose logs -f api
```

### Option 3: DÃ©veloppement local
```bash
cd harmonic_saas

# Installer les dÃ©pendances Python
pip install -r requirements.txt

# DÃ©marrer les services Docker
docker-compose up -d postgres redis mongodb

# ExÃ©cuter les migrations
alembic upgrade head

# DÃ©marrer l'API
uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload

# Dans un autre terminal, dÃ©marrer Celery
celery -A app.celery_app worker --loglevel=info
```

## ðŸ”§ Configuration

### Variables d'environnement
CrÃ©ez un fichier `.env` Ã  la racine :

```env
# Application
PROJECT_NAME=Harmonic AI SaaS
VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
API_V1_STR=/api/v1

# Base de donnÃ©es
DATABASE_URL=postgresql://harmonic:harmonic123@localhost:5432/harmonic_saas
REDIS_URL=redis://localhost:6379/0
MONGODB_URL=mongodb://localhost:27017/harmonic_saas

# Services externes
LM_ARENA_SERVICE_URL=http://__EC2_IP__:8000
AUDIO_SERVICE_URL=http://localhost:9017
VIDEO_SERVICE_URL=http://localhost:9018

# SÃ©curitÃ©
JWT_SECRET_KEY=votre_clÃ©_secrÃ¨te_trÃ¨s_longue_et_complexe
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AWS (optionnel)
AWS_ACCESS_KEY_ID=votre_access_key
AWS_SECRET_ACCESS_KEY=votre_secret_key
AWS_S3_BUCKET=harmonic-saas-bucket
AWS_REGION=us-east-1

# Stripe (optionnel)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Services Docker
Les services suivants sont disponibles :

| Service | Port | Description |
|---------|------|-------------|
| API | 9000 | FastAPI backend |
| PostgreSQL | 5432 | Base de donnÃ©es principale |
| Redis | 6379 | Cache et broker Celery |
| MongoDB | 27017 | Base de donnÃ©es documents |
| Prometheus | 9090 | MÃ©triques systÃ¨me |
| Grafana | 3000 | Dashboard monitoring |

## ðŸ“¡ API Endpoints

### Authentification
- `POST /api/v1/auth/register` - Inscription utilisateur
- `POST /api/v1/auth/login` - Connexion (JWT)
- `POST /api/v1/auth/refresh` - RafraÃ®chir token
- `POST /api/v1/auth/logout` - DÃ©connexion

### Chat & LM Arena
- `POST /api/v1/chat/generate` - GÃ©nÃ©rer rÃ©ponse
- `GET /api/v1/chat/sessions` - Sessions de chat
- `POST /api/v1/chat/audio/process` - Traitement audio
- `POST /api/v1/chat/video/process` - Traitement vidÃ©o
- `GET /api/v1/chat/health` - SantÃ© services
- `GET /api/v1/chat/status` - Statut utilisateur

### Gestion SaaS
- `GET /api/v1/subscription/plans` - Plans disponibles
- `POST /api/v1/subscription/subscribe` - Souscrire Ã  un plan
- `GET /api/v1/subscription/invoices` - Factures
- `POST /api/v1/subscription/api-keys` - GÃ©nÃ©rer clÃ© API

## ðŸŽ¨ Interface utilisateur

### ThÃ¨mes
- **Mode sombre** (par dÃ©faut)
- **Mode clair** (toggle dans le header)

### Sections principales
1. **Dashboard** - Vue d'ensemble et mÃ©triques
2. **Chat LM Arena** - Interface de chat avec DeepSeek
3. **Audio Processing** - Upload et traitement audio
4. **Video Processing** - Upload et traitement vidÃ©o
5. **Subscription** - Gestion abonnement et facturation
6. **API Keys** - GÃ©nÃ©ration et gestion clÃ©s API
7. **Settings** - PrÃ©fÃ©rences utilisateur

## ðŸ”’ SÃ©curitÃ©

### Authentification
- JWT avec expiration courte (30 min)
- Refresh tokens avec expiration longue (7 jours)
- Hash bcrypt pour les mots de passe
- Rate limiting par IP et utilisateur

### Autorisation
- RÃ´les utilisateur (user, admin, enterprise)
- Permissions granulaires pour les clÃ©s API
- VÃ©rification des limites d'abonnement

### Protection des donnÃ©es
- Chiffrement des donnÃ©es sensibles
- Logs d'audit pour toutes les actions
- Suppression sÃ©curisÃ©e des fichiers

## ðŸ“Š Monitoring

### MÃ©triques collectÃ©es
- **Performance** : latence API, temps de traitement
- **Utilisation** : requÃªtes, utilisateurs actifs, jobs
- **SystÃ¨me** : CPU, mÃ©moire, disque, rÃ©seau
- **Business** : revenus, conversions, rÃ©tention

### Alertes configurÃ©es
- Latence API > 5 secondes
- Taux d'erreur > 1%
- Utilisation CPU > 80%
- Espace disque < 10%

## ðŸš¢ DÃ©ploiement

### Environnements
1. **Development** - Local avec Docker
2. **Staging** - AWS ECS avec base de donnÃ©es test
3. **Production** - AWS ECS + RDS + ElastiCache

### AWS Services requis
- **ECS** (Elastic Container Service) - Conteneurs
- **RDS** (PostgreSQL) - Base de donnÃ©es
- **ElastiCache** (Redis) - Cache
- **S3** - Stockage fichiers
- **CloudFront** - CDN pour frontend
- **WAF** - Protection applicative

### CI/CD
```yaml
# Exemple GitHub Actions
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: docker build -t harmonic-saas .
      - name: Push to ECR
        run: |
          aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
          docker tag harmonic-saas:latest $ECR_REGISTRY/harmonic-saas:latest
          docker push $ECR_REGISTRY/harmonic-saas:latest
      - name: Deploy to ECS
        run: aws ecs update-service --cluster harmonic-cluster --service harmonic-service --force-new-deployment
```

## ðŸ§ª Tests

### Types de tests
```bash
# Tests unitaires
pytest tests/unit -v

# Tests d'intÃ©gration
pytest tests/integration -v

# Tests end-to-end
pytest tests/e2e -v

# Tests de performance
locust -f tests/performance/locustfile.py
```

### Couverture de code
```bash
# GÃ©nÃ©rer rapport de couverture
pytest --cov=app --cov-report=html

# VÃ©rifier seuil minimum
pytest --cov=app --cov-fail-under=80
```

## ðŸ“ˆ Roadmap

### Phase 1 (Maintenant)
- [x] Architecture backend FastAPI
- [x] IntÃ©gration DeepSeek API AWS
- [x] Dashboard frontend basique
- [x] Authentification JWT
- [x] Gestion abonnements

### Phase 2 (1 mois)
- [ ] IntÃ©gration complÃ¨te services audio/vidÃ©o
- [ ] Monitoring Prometheus + Grafana
- [ ] Facturation Stripe
- [ ] API Keys management
- [ ] Tests automatisÃ©s

### Phase 3 (3 mois)
- [ ] Multi-tenancy avancÃ©
- [ ] Analytics dÃ©taillÃ©s
- [ ] Marketplace d'extensions
- [ ] Mobile app React Native
- [ ] IntÃ©gration OAuth2 (Google, GitHub)

### Phase 4 (6 mois)
- [ ] AI Model Marketplace
- [ ] Workflow automation
- [ ] Team collaboration
- [ ] Enterprise SSO
- [ ] Compliance certifications

## ðŸ¤ Contribution

### DÃ©veloppement
1. Fork le repository
2. CrÃ©er une branche feature
3. Commiter les changements
4. Push vers la branche
5. CrÃ©er une Pull Request

### Guidelines
- Suivre PEP 8 pour Python
- Documenter les nouvelles fonctionnalitÃ©s
- Ajouter des tests unitaires
- Mettre Ã  jour le CHANGELOG

## ðŸ“„ Licence

PropriÃ©taire - Harmonic AI Â© 2026

## ðŸ“ž Support

- **Email** : support@harmonic-ai.com
- **Documentation** : [docs.harmonic-ai.com](https://docs.harmonic-ai.com)
- **Community** : [community.harmonic-ai.com](https://community.harmonic-ai.com)

---

**Harmonic AI** - Transformez votre contenu avec la puissance des mathÃ©matiques harmoniques