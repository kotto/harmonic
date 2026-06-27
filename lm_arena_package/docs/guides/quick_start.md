# ðŸš€ DÃ©marrage Rapide - Harmonic AI SaaS

Guide pour dÃ©marrer rapidement le dashboard SaaS Harmonic AI avec intÃ©gration LM Arena.

## ðŸ“‹ PrÃ©requis

### SystÃ¨me
- **Windows 10/11** ou **macOS 10.15+** ou **Linux Ubuntu 20.04+**
- **8GB RAM** minimum (16GB recommandÃ©)
- **10GB** espace disque libre

### Logiciels
- **Docker Desktop** : [TÃ©lÃ©charger](https://www.docker.com/products/docker-desktop/)
- **Python 3.8+** : [TÃ©lÃ©charger](https://www.python.org/downloads/)
- **Git** (optionnel) : [TÃ©lÃ©charger](https://git-scm.com/)

### Services externes (optionnels)
- **API DeepSeek AWS** : `http://__EC2_IP__:8000`
- **Services harmoniques audio/vidÃ©o** (dÃ©marrer avec `start_harmonic_services.bat`)

## ðŸŽ¯ Installation in 5 minutes

### Ã‰tape 1: VÃ©rifier les prerequisites
```bash
# VÃ©rifier Docker
docker --version

# VÃ©rifier Python
python --version

# VÃ©rifier Docker Compose
docker-compose --version
```

### Ã‰tape 2: DÃ©marrer tous les services (Windows)
```bash
# MÃ©thode la plus simple - exÃ©cutez le script batch
start_all.bat
```

### Ã‰tape 3: VÃ©rifier l'installation
```bash
# Tester l'installation complÃ¨te
python verify_deployment.py

# Tester l'intÃ©gration LM Arena
python test_lm_arena_integration.py
```

## ðŸ”§ DÃ©marrage manuel

### Option A: Avec Docker Compose
```bash
# 1. DÃ©marrer les services de base
docker-compose up -d postgres redis mongodb

# 2. Attendre l'initialisation (10 secondes)
timeout /t 10

# 3. DÃ©marrer l'API backend
docker-compose up -d api

# 4. DÃ©marrer le frontend
cd frontend
start_frontend.bat
```

### Option B: DÃ©veloppement local
```bash
# 1. Installer les dÃ©pendances Python
pip install -r requirements.txt

# 2. DÃ©marrer les services Docker
docker-compose up -d postgres redis mongodb

# 3. ExÃ©cuter les migrations
alembic upgrade head

# 4. DÃ©marrer l'API (dans un terminal)
uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload

# 5. DÃ©marrer Celery (dans un autre terminal)
celery -A app.celery_app worker --loglevel=info

# 6. DÃ©marrer le frontend (dans un autre terminal)
cd frontend
python -m http.server 8080
```

## ðŸŒ AccÃ¨s aux services

| Service | URL | Port | Description |
|---------|-----|------|-------------|
| **Dashboard Frontend** | http://localhost:8080 | 8080 | User Interface |
| **API Backend** | http://localhost:9000 | 9000 | FastAPI Backend |
| **Documentation API** | http://localhost:9000/docs | 9000 | Swagger UI |
| **MÃ©triques** | http://localhost:9000/metrics | 9000 | Prometheus metrics |
| **PostgreSQL** | localhost:5432 | 5432 | Base de donnÃ©es |
| **Redis** | localhost:6379 | 6379 | Cache & Celery |
| **MongoDB** | localhost:27017 | 27017 | Base de donnÃ©es documents |

## ðŸŽ¨ Premiers pas

### 1. CrÃ©er un compte
1. Ouvrez http://localhost:8080
2. Cliquez sur "Sign Up" dans le header
3. Remplissez le formulaire :
   - Email : votre@email.com
   - Username : votre_nom
   - Password : *******
4. Cliquez sur "Create Account"

### 2. Tester le chat LM Arena
1. Connectez-vous avec vos identifiants
2. Allez dans la section "Chat LM Arena"
3. Tapez un message : "Bonjour, comment Ã§a va?"
4. Cliquez sur "Send"
5. La rÃ©ponse sera gÃ©nÃ©rÃ©e par l'API DeepSeek AWS

### 3. Traiter un fichier audio
1. Allez dans "Audio Processing"
2. Cliquez sur "Upload Audio"
3. SÃ©lectionnez un fichier MP3/WAV
4. Choisissez un mode de traitement :
   - **HCS Restore** : Restauration complÃ¨te
   - **HCS Spatial** : Audio 3D immersif
   - **HCS Clarity** : ClartÃ© optimale
5. Cliquez sur "Process"
6. Suivez la progression dans "My Jobs"

### 4. GÃ©rer l'abonnement
1. Allez dans "Subscription"
2. Choisissez un plan :
   - **Free** : 10 min audio/mois
   - **Pro** : 5h audio, 2h vidÃ©o/mois
   - **Enterprise** : IllimitÃ©
3. Configurez le paiement (Stripe)
4. Consultez les factures

## ðŸ”— IntÃ©gration avec services existants

### API DeepSeek AWS
```python
# Configuration automatique
LM_ARENA_SERVICE_URL = "http://__EC2_IP__:8000"

# Test de connexion
curl http://__EC2_IP__:8000/health
```

### Services harmoniques
```bash
# DÃ©marrer les services simulÃ©s
start_harmonic_services.bat

# VÃ©rifier
curl http://localhost:9017/health
curl http://localhost:9018/health
```

### HCV-PROF (compression)
- Service opÃ©rationnel et conservÃ©
- IntÃ©gration via API dÃ©diÃ©e

## ðŸ§ª Tests et validation

### Test complet
```bash
# VÃ©rifier l'ensemble du systÃ¨me
python verify_deployment.py

# Tester l'intÃ©gration LM Arena
python test_lm_arena_integration.py

# Tester les services harmoniques
curl http://localhost:9017/health
curl http://localhost:9018/health
```

### Test unitaire
```bash
# ExÃ©cuter les tests unitaires
pytest tests/unit -v

# Test avec couverture
pytest --cov=app --cov-report=html
```

## âš™ï¸ Configuration avancÃ©e

### Variables d'environnement
CrÃ©ez un fichier `.env` Ã  la racine :

```env
# Application
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

# Security
JWT_SECRET_KEY=votre_clÃ©_secrÃ¨te_trÃ¨s_longue_et_complexe
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AWS (optionnel)
AWS_S3_BUCKET=harmonic-saas-bucket
AWS_REGION=us-east-1

# Stripe (optionnel)
STRIPE_SECRET_KEY=sk_test_...
```

### Personnalisation du frontend
```javascript
// Modifier frontend/config.js
const CONFIG = {
    API_BASE_URL: 'http://localhost:9000/api/v1',
    // Personnaliser les modes de traitement
    PROCESSING_MODES: {
        AUDIO: {
            // Ajouter vos propres modes
            CUSTOM_MODE: {
                name: 'Mon Mode PersonnalisÃ©',
                description: 'Description personnalisÃ©e',
                estimatedTime: '5 minutes',
                cost: 10
            }
        }
    }
};
```

## ðŸš¢ Deployment en production

### PrÃ©paration
```bash
# 1. VÃ©rifier la configuration
python verify_deployment.py

# 2. Tester l'intÃ©gration
python test_lm_arena_integration.py

# 3. Construire les images Docker
docker-compose build

# 4. Tester en local
docker-compose up -d
```

### Deployment AWS
```bash
# Suivre le guide complet
# Voir: deploy_aws.md

# Ã‰tapes principales:
# 1. Configurer ECR (Elastic Container Registry)
# 2. CrÃ©er RDS PostgreSQL
# 3. Configurer ElastiCache Redis
# 4. DÃ©ployer sur ECS Fargate
# 5. Configurer CloudFront CDN
# 6. Activer AWS WAF
```

## ðŸ†˜ DÃ©pannage

### ProblÃ¨mes courants

#### 1. Docker ne dÃ©marre pas
```bash
# VÃ©rifier que Docker Desktop est en cours d'exÃ©cution
# RedÃ©marrer Docker Desktop
# VÃ©rifier les ressources systÃ¨me
```

#### 2. Ports dÃ©jÃ  utilisÃ©s
```bash
# VÃ©rifier les ports utilisÃ©s
netstat -ano | findstr :8080
netstat -ano | findstr :9000

# Changer les ports dans docker-compose.yml
```

#### 3. Connexion base de donnÃ©es Ã©chouÃ©e
```bash
# VÃ©rifier que PostgreSQL est en cours d'exÃ©cution
docker ps | grep postgres

# VÃ©rifier les logs
docker logs harmonic_saas_postgres_1

# VÃ©rifier DATABASE_URL dans .env
```

#### 4. API DeepSeek inaccessible
```bash
# VÃ©rifier la connectivitÃ©
ping __EC2_IP__

# Tester l'API directement
curl http://__EC2_IP__:8000/health

# VÃ©rifier les pare-feux
```

### Logs et monitoring

```bash
# Voir les logs Docker
docker-compose logs -f

# Logs spÃ©cifiques
docker-compose logs -f api
docker-compose logs -f postgres

# MÃ©triques Prometheus
curl http://localhost:9000/metrics

# SantÃ© des services
curl http://localhost:9000/health
curl http://localhost:9000/api/v1/chat/health
```

## ðŸ“ž Support

### Ressources
- **Documentation complÃ¨te** : [README.md](README.md)
- **Deployment AWS** : [deploy_aws.md](deploy_aws.md)
- **RÃ©fÃ©rence API** : http://localhost:9000/docs
- **Code source** : Structure du projet

### ProblÃ¨mes connus
1. **Services harmoniques** : DÃ©marrage manuel requis
2. **AWS connectivity** : VÃ©rifier les rÃ¨gles de security
3. **Performance** : Ajuster les ressources Docker

### Prochaines Ã©tapes
1. âœ… Installation et configuration
2. âœ… Test des services locaux
3. â¬œ IntÃ©gration avec AWS services
4. â¬œ Configuration des abonnements
5. â¬œ Deployment en production

---

**Note** : Ce dashboard SaaS est conÃ§u pour s'intÃ©grer avec les services LM Arena existants. Assurez-vous que :
- L'API DeepSeek AWS est accessible
- Les services harmoniques sont dÃ©marrÃ©s si nÃ©cessaire
- Les variables d'environnement sont correctement dÃ©finies

Pour toute question, consultez la documentation complÃ¨te ou contactez l'Ã©quipe Harmonic AI.