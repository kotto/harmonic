# Guide de Déploiement et Intégration LM Arena

## Table des Matières
1. [Introduction](#introduction)
2. [Architecture du Package](#architecture-du-package)
3. [Prérequis Système](#prérequis-système)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Démarrage des Services](#démarrage-des-services)
7. [Tests et Validation](#tests-et-validation)
8. [Intégration LM Arena](#intégration-lm-arena)
9. [Monitoring et Maintenance](#monitoring-et-maintenance)
10. [Dépannage](#dépannage)
11. [FAQ](#faq)

---

## Introduction

### Objectif du Package
Le **Package LM Arena** est une solution complète pour participer à la plateforme d'évaluation LM Arena avec l'approche **Harmonic AI**. Il intègre :

- **API Backend** : Serveur FastAPI avec endpoints optimisés pour LM Arena
- **Services harmoniques** : Traitement audio et vidéo avec l'approche harmonique
- **Frontend** : Interface utilisateur pour tests et démonstrations
- **Monitoring** : Métriques et logs pour surveillance des performances
- **Scripts d'automatisation** : Installation, démarrage, tests et maintenance

### Avantages Clés
- ✅ **Déterminisme garanti** : Même prompt → Même sortie (temperature=0)
- ✅ **Mode vérifié** : Citations obligatoires pour affirmations factuelles
- ✅ **Zéro hallucination** : Abstention quand les sources sont insuffisantes
- ✅ **Performance optimisée** : Latence < 2 secondes en moyenne
- ✅ **Intégration complète** : Prêt pour soumission LM Arena immédiate

---

## Architecture du Package

### Structure des Dossiers
```
lm_arena_package/
├── backend/                    # Backend FastAPI
│   ├── api/                   # Endpoints API
│   ├── core/                  # Configuration et utilitaires
│   ├── models/                # Modèles de données
│   ├── schemas/               # Schémas Pydantic
│   ├── services/              # Services métier
│   ├── tasks/                 # Tâches asynchrones
│   └── main.py                # Point d'entrée principal
├── frontend/                  # Interface utilisateur
│   ├── static/               # Fichiers statiques
│   ├── templates/            # Templates HTML
│   └── index.html            # Page d'accueil
├── scripts/                   # Scripts d'automatisation
│   ├── deployment/           # Scripts de déploiement
│   ├── monitoring/           # Surveillance
│   ├── testing/              # Tests
│   ├── install.sh            # Installation Linux/macOS
│   ├── install_windows.ps1   # Installation Windows
│   ├── start.sh              # Démarrage Linux/macOS
│   ├── start_windows.bat     # Démarrage Windows
│   └── stop.sh               # Arrêt Linux/macOS
├── docs/                      # Documentation
│   ├── guides/               # Guides détaillés
│   ├── reference/            # Références techniques
│   └── api/                  # Documentation API
├── tests/                     # Tests automatisés
│   ├── integration/          # Tests d'intégration
│   ├── performance/          # Tests de performance
│   └── unit/                 # Tests unitaires
├── config/                    # Configuration
│   ├── environments/         # Configurations par environnement
│   ├── secrets/              # Secrets et clés
│   ├── .env.example          # Exemple de variables d'environnement
│   ├── docker-compose.yml    # Configuration Docker
│   └── requirements.txt      # Dépendances Python
├── aws/                       # Configuration AWS
│   ├── ec2/                  # Scripts EC2
│   ├── lambda/               # Fonctions Lambda
│   └── s3/                   # Configuration S3
└── monitoring/               # Surveillance
    ├── alerts/               # Alertes et notifications
    ├── dashboards/           # Tableaux de bord
    └── metrics/              # Métriques et logs
```

### Composants Principaux

#### 1. Backend FastAPI
- **Framework** : FastAPI avec Uvicorn
- **Base de données** : PostgreSQL avec SQLAlchemy
- **Cache** : Redis pour performances
- **Tâches asynchrones** : Celery avec Flower
- **Authentification** : JWT avec OAuth2

#### 2. Services Harmoniques
- **Service Audio** : Port 9017 - Traitement audio avancé
- **Service Vidéo** : Port 9018 - Traitement vidéo 8K
- **API REST** : Endpoints standardisés pour intégration

#### 3. Frontend
- **HTML/CSS/JavaScript** : Interface utilisateur moderne
- **Thème sombre** : Support natif pour thème sombre
- **Responsive** : Compatible mobile et desktop

#### 4. Monitoring
- **Prometheus** : Collecte de métriques
- **Grafana** : Tableaux de bord (optionnel)
- **Logs structurés** : JSON avec structlog

---

## Prérequis Système

### Pour Linux/macOS
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git curl

# CentOS/RHEL
sudo yum install -y python3 python3-pip python3-virtualenv git curl

# macOS (avec Homebrew)
brew install python3 git curl
```

### Pour Windows
- **Python 3.8+** : [Télécharger depuis python.org](https://www.python.org/downloads/)
- **Git** : [Télécharger depuis git-scm.com](https://git-scm.com/download/win)
- **PowerShell 5.1+** : Inclus dans Windows 10/11

### Vérification des Prérequis
```bash
# Vérifier Python
python3 --version  # Doit afficher 3.8+

# Vérifier pip
pip3 --version

# Vérifier Git
git --version
```

---

## Installation

### Option 1 : Installation Automatique (Linux/macOS)
```bash
# Télécharger le package
git clone <repository-url>
cd lm_arena_package

# Exécuter le script d'installation
chmod +x scripts/install.sh
./scripts/install.sh
```

### Option 2 : Installation Automatique (Windows)
```powershell
# Télécharger le package
git clone <repository-url>
cd lm_arena_package

# Exécuter le script d'installation
.\scripts\install_windows.ps1
```

### Option 3 : Installation Manuelle
```bash
# 1. Créer l'environnement virtuel
python3 -m venv venv

# 2. Activer l'environnement
source venv/bin/activate  # Linux/macOS
# ou
.\venv\Scripts\activate   # Windows

# 3. Installer les dépendances
pip install -r config/requirements.txt

# 4. Configurer l'environnement
cp config/.env.example config/.env
# Éditer config/.env avec vos clés API
```

### Étapes de l'Installation Automatique
1. **Vérification des prérequis** : Python, pip, Git
2. **Création de l'environnement virtuel** : Isolation des dépendances
3. **Installation des dépendances** : FastAPI, Uvicorn, SQLAlchemy, etc.
4. **Configuration initiale** : Création du fichier .env
5. **Initialisation de la base de données** : Docker Compose (optionnel)
6. **Vérification finale** : Tests d'import et connectivité

---

## Configuration

### Fichier .env
```bash
# Copier l'exemple
cp config/.env.example config/.env

# Éditer avec vos paramètres
nano config/.env  # ou utiliser votre éditeur préféré
```

### Variables d'Environnement Essentielles
```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Database
DATABASE_URL=postgresql://user:password@localhost/harmonic_ai
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET_KEY=your-secret-key-here
API_KEY_HEADER=X-API-Key

# LM Arena
LM_ARENA_API_URL=https://arena.lmsys.org
LM_ARENA_TIMEOUT=30

# Harmonic Services
AUDIO_SERVICE_PORT=9017
VIDEO_SERVICE_PORT=9018

# External APIs (optional)
DEEPSEEK_API_KEY=your-deepseek-api-key
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
```

### Configuration par Environnement

#### Développement (`config/environments/development.yaml`)
```yaml
environment: development
debug: true
log_level: DEBUG
database:
  host: localhost
  port: 5432
  name: harmonic_ai_dev
cache:
  enabled: true
  ttl: 300
```

#### Production (`config/environments/production.yaml`)
```yaml
environment: production
debug: false
log_level: INFO
database:
  host: ${DB_HOST}
  port: ${DB_PORT}
  name: harmonic_ai_prod
cache:
  enabled: true
  ttl: 600
security:
  cors_origins:
    - https://your-domain.com
  rate_limit: 100/1minute
```

### Configuration AWS (Optionnel)
```bash
# Installer AWS CLI
# Linux/macOS
pip install awscli

# Windows
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

# Configurer les credentials
aws configure
```

---

## Démarrage des Services

### Option 1 : Script de Démarrage (Linux/macOS)
```bash
# Démarrage complet
./scripts/start.sh

# Sortie attendue
[*] Étape 1 : Vérification des prérequis
[+] Environnement virtuel activé
[*] Étape 2 : Arrêt des services existants
[*] Étape 3 : Démarrage des services
[+] API Backend démarrée avec succès
[+] Service audio démarré avec succès
[+] Service vidéo démarré avec succès
[+] Frontend démarré avec succès
[+] Monitoring démarré avec succès
[*] Étape 4 : Tests de connectivité
[+] API Backend répond correctement
[+] Frontend répond correctement
✅ DÉMARRAGE TERMINÉ AVEC SUCCÈS !
```

### Option 2 : Script de Démarrage (Windows)
```batch
# Démarrage complet
.\scripts\start_windows.bat

# Sortie attendue similaire à Linux/macOS
```

### Option 3 : Démarrage Manuel
```bash
# 1. Activer l'environnement virtuel
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows

# 2. Démarrer l'API Backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &

# 3. Démarrer les services harmoniques
cd services
python audio_service.py --port 9017 &
python video_service.py --port 9018 &

# 4. Démarrer le frontend
cd ../../frontend
python -m http.server 8080 &

# 5. Démarrer le monitoring
cd ../monitoring
python -m http.server 9090 &
```

### Vérification des Services
```bash
# Vérifier les ports en écoute
netstat -tlnp | grep -E "(8000|8080|9017|9018|9090)"

# Tester l'API
curl http://localhost:8000/health

# Tester le frontend
curl http://localhost:8080

# Tester les services harmoniques
curl http://localhost:9017/health
curl http://localhost:9018/health
```

---

## Tests et Validation

### Tests Automatisés
```bash
# Exécuter tous les tests
cd tests
pytest

# Tests spécifiques
pytest tests/integration/ -v
pytest tests/performance/ -v
pytest tests/unit/ -v
```

### Tests LM Arena
```bash
# Tests complets LM Arena
python tests/performance/lm_arena_test.py

# Tests d'intégration
python tests/integration/test_lm_arena.py
```

### Validation Manuelle

#### 1. Vérification de l'API
```bash
# Test de santé
curl http://localhost:8000/health

# Test de génération
curl -X POST http://localhost:8000/api/v1/chat/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"prompt": "Bonjour, comment ça va?", "temperature": 0.0}'
```

#### 2. Vérification des Services Harmoniques
```bash
# Service audio
curl http://localhost:9017/health

# Service vidéo
curl http://localhost:9018/health
```

#### 3. Vérification du Frontend
- Ouvrir http://localhost:8080 dans votre navigateur
- Vérifier l'interface utilisateur
- Tester les fonctionnalités principales

### Benchmarks de Performance
```bash
# Test de latence
python tests/performance/benchmark_latency.py

# Test de débit
python tests/performance/benchmark_throughput.py

# Test de charge
python tests/performance/benchmark_load.py
```

---

## Intégration LM Arena

### Préparation pour Soumission

#### 1. Documentation Requise
- **Description du modèle** : Spécifications techniques et capacités
- **Exemples de réponses** : Démonstrations de qualité
- **Spécifications API** : Endpoints, formats, authentification
- **Métriques de performance** : Latence, précision, fiabilité

#### 2. Configuration LM Arena
```yaml
# Configuration minimale pour LM Arena
lm_arena_config:
  model_name: "Harmonic-AI-Qwen-DeepSeek-V4"
  model_version: "1.0.0"
  endpoint_url: "http://your-domain.com/api/v1/chat/generate"
  api_key: "your-api-key-for-lm-arena"
  capabilities:
    text_generation: true
    verified_mode: true
    deterministic: true
    multimodal: true
    audio_processing: true
    video_processing: true
  parameters:
    temperature: 0.0
    max_tokens: 1000
    verified_mode: true
```

#### 3. Tests de Conformité
```bash
# Tests LM Arena standards
python tests/integration/lm_arena_conformance.py

# Tests de robustesse
python tests/integration/robustness_tests.py

# Tests de sécurité
python tests/integration/security_tests.py
```

### Soumission sur LM Arena

#### Étapes de Soumission
1. **Créer un compte** sur [arena.lmsys.org](https://arena.lmsys.org)
2. **Remplir le formulaire** de soumission de modèle
3. **Uploader la documentation** technique
4. **Configurer l'endpoint** avec l'URL publique
5. **Valider la connexion** avec les tests LM Arena
6. **Soumettre pour évaluation**

#### Configuration de l'Endpoint
```python
# Exemple de configuration d'endpoint pour LM Arena
import fastapi
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Harmonic AI LM Arena Endpoint")

class GenerationRequest(BaseModel):
    prompt: str
    temperature: float = 0.0
    max_tokens: int = 1000

class GenerationResponse(BaseModel):
    text: str
    response_id: str
    verified: bool = True

@app.post("/generate", response_model=GenerationResponse)
async def generate_text(request: GenerationRequest):
    """Endpoint pour la génération de texte pour LM Arena"""
    # Votre logique de génération ici
    return GenerationResponse(
        text="Réponse générée avec succès",
        response_id="unique-id-123",
        verified=True
    )
```

### Monitoring des Performances LM Arena

#### Métriques à Surveiller
- **Taux de victoire** : Pourcentage de comparaisons gagnées
- **Score Elo** : Évolution du score de classement
- **Latence moyenne** : Temps de réponse pour les évaluations
- **Taux d'erreur** : Pourcentage de requêtes échouées
- **Satisfaction utilisateur** : Feedback des évaluateurs

#### Tableaux de Bord Recommandés
1. **Performance LM Arena** : Scores et classement en temps réel
2. **Santé des Services** : Disponibilité et erreurs
3. **Analyse des Réponses** : Qualité et cohérence
4. **Optimisation** : Suggestions d'amélioration

---

## Monitoring et Maintenance

### Surveillance en Temps Réel

#### 1. Métriques de Base
```bash
# Vérifier l'état des services
./scripts/status.sh

# Vérifier les logs
tail -f logs/api.log
tail -f logs/audio_service.log
tail -f logs/video_service.log
```

#### 2. Monitoring Avancé
- **Prometheus** : Collecte de métriques détaillées
- **Grafana** : Tableaux de dashboards personnalisés
- **AlertManager** : Alertes automatiques sur incidents

### Maintenance Régulière

#### Tâches Quotidiennes
1. **Vérification des logs** : Détection d'erreurs et anomalies
2. **Sauvegarde des données** : Base de données et configurations
3. **Mise à jour des dépendances** : Sécurité et performances

#### Tâches Hebdomadaires
1. **Nettoyage des logs** : Archivage et rotation
2. **Optimisation de la base de données** : Index et requêtes
3. **Revue de sécurité** : Audits et mises à jour

#### Tâches Mensuelles
1. **Revue des performances** : Analyse des métriques
2. **Mise à jour du système** : OS et dépendances système
3. **Test de restauration** : Validation des sauvegardes

### Sauvegarde et Récupération

#### Stratégie de Sauvegarde
```yaml
backup_strategy:
  frequency: daily
  retention: 30 days
  locations:
    - local: /backups/harmonic_ai
    - cloud: s3://harmonic-ai-backups
  components:
    - database: postgresql
    - configuration: config/
    - logs: logs/
    - models: backend/models/
```

#### Script de Sauvegarde
```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backups/harmonic_ai"
DATE=$(date +%Y%m%d_%H%M%S)

# Sauvegarde de la base de données
pg_dump harmonic_ai > "$BACKUP_DIR/db_$DATE.sql"

# Sauvegarde des configurations
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" config/

# Sauvegarde des logs
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" logs/

echo "Sauvegarde terminée: $DATE"
```

### Mises à Jour

#### Mise à Jour du Package
```bash
# 1. Sauvegarder la configuration actuelle
cp -r config config_backup_$(date +%Y%m%d)

# 2. Mettre à jour le code
git pull origin main

# 3. Mettre à jour les dépendances
pip install -r config/requirements.txt --upgrade

# 4. Appliquer les migrations de base de données
alembic upgrade head

# 5. Redémarrer les services
./scripts/restart.sh
```

#### Mise à Jour des Modèles
```bash
# Mise à jour des modèles d'IA
python scripts/update_models.py

# Validation des nouveaux modèles
python tests/performance/validate_models.py
```

---

## Dépannage

### Problèmes Courants et Solutions

#### 1. Échec de l'Installation
**Symptôme** : Erreur lors de l'exécution de `install.sh` ou `install_windows.ps1`

**Solutions** :
```bash
# Vérifier les prérequis
python3 --version
pip3 --version

# Réinstaller les dépendances
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r config/requirements.txt
```

#### 2. API Non Accessible
**Symptôme** : Erreur 404 ou timeout sur http://localhost:8000

**Solutions** :
```bash
# Vérifier si le service est en cours d'exécution
ps aux | grep uvicorn

# Redémarrer l'API
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 3. Erreurs de Base de Données
**Symptôme** : Erreurs de connexion PostgreSQL

**Solutions** :
```bash
# Vérifier si PostgreSQL est en cours d'exécution
sudo systemctl status postgresql

# Vérifier les logs PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-*.log
```

#### 4. Services Harmoniques Non Démarrés
**Symptôme** : Ports 9017 ou 9018 non accessibles

**Solutions** :
```bash
# Vérifier les processus
ps aux | grep -E "(audio_service|video_service)"

# Redémarrer les services
cd backend/services
python audio_service.py --port 9017 &
python video_service.py --port 9018 &
```

### Diagnostic Avancé

#### Script de Diagnostic
```bash
#!/bin/bash
# scripts/diagnostic.sh

echo "=== DIAGNOSTIC LM ARENA PACKAGE ==="
echo "Date: $(date)"
echo ""

# 1. Vérification système
echo "1. VÉRIFICATION SYSTÈME"
echo "----------------------"
echo "OS: $(uname -a)"
echo "Python: $(python3 --version 2>&1)"
echo "Pip: $(pip3 --version 2>&1 | cut -d' ' -f2)"
echo ""

# 2. Vérification des services
echo "2. VÉRIFICATION DES SERVICES"
echo "---------------------------"
for port in 8000 8080 9017 9018 9090; do
    if nc -z localhost $port 2>/dev/null; then
        echo "Port $port: ✅ EN ÉCOUTE"
    else
        echo "Port $port: ❌ NON DISPONIBLE"
    fi
done
echo ""

# 3. Vérification des logs
echo "3. VÉRIFICATION DES LOGS"
echo "-----------------------"
for log in api audio_service video_service frontend monitoring; do
    if [ -f "logs/$log.log" ]; then
        echo "$log.log: ✅ EXISTE ($(wc -l < logs/$log.log) lignes)"
    else
        echo "$log.log: ❌ INTROUVABLE"
    fi
done
echo ""

echo "=== DIAGNOSTIC TERMINÉ ==="
```

### Support et Ressources

#### Documentation Disponible
- **Guides** : `docs/guides/` - Documentation détaillée
- **Référence** : `docs/reference/` - Références techniques
- **API** : `docs/api/` - Documentation des endpoints

#### Ressources en Ligne
- **Site web Harmonic AI** : [harmonic-ai.com](https://harmonic-ai.com)
- **Documentation LM Arena** : [arena.lmsys.org/docs](https://arena.lmsys.org/docs)
- **Support technique** : support@harmonic-ai.com

#### Communauté
- **Forum Harmonic AI** : [forum.harmonic-ai.com](https://forum.harmonic-ai.com)
- **GitHub** : [github.com/harmonic-ai](https://github.com/harmonic-ai)
- **Discord** : [discord.gg/harmonic-ai](https://discord.gg/harmonic-ai)

---

## FAQ

### Questions Générales

#### Q1 : Qu'est-ce que LM Arena ?
**R** : LM Arena (Language Model Arena) est une plateforme d'évaluation d'IA qui mesure la préférence humaine entre différentes réponses générées par des modèles de langage.

#### Q2 : Pourquoi utiliser Harmonic AI pour LM Arena ?
**R** : Harmonic AI apporte une approche unique avec :
- Déterminisme garanti (même prompt → même sortie)
- Mode vérifié (citations obligatoires)
- Zéro hallucination (abstention quand sources insuffisantes)
- Performance optimisée (latence < 2 secondes)

#### Q3 : Quels sont les prérequis système ?
**R** :
- **Linux/macOS** : Python 3.8+, pip, Git
- **Windows** : Python 3.8+, PowerShell 5.1+, Git
- **Optionnel** : Docker, 8GB+ RAM, GPU (recommandé)

### Questions Techniques

#### Q4 : Comment configurer les clés API ?
**R** : Copiez `config/.env.example` vers `config/.env` et éditez avec vos clés :
```bash
cp config/.env.example config/.env
nano config/.env
```

#### Q5 : Comment démarrer tous les services ?
**R** :
```bash
# Linux/macOS
./scripts/start.sh

# Windows
.\scripts\start_windows.bat
```

#### Q6 : Comment vérifier l'état des services ?
**R** :
```bash
# Vérifier les ports
./scripts/status.sh

# Vérifier les logs
tail -f logs/api.log
```

### Questions sur les Performances

#### Q7 : Quelle latence attendre ?
**R** : Harmonic AI est optimisé pour une latence < 2 secondes en moyenne, avec des pics < 5 secondes pour les requêtes complexes.

#### Q8 : Comment améliorer les performances ?
**R** :
1. **Optimisation du code** : Utilisez les scripts d'optimisation
2. **Configuration matérielle** : GPU recommandé pour l'inférence
3. **Cache** : Redis configuré pour améliorer les temps de réponse

#### Q9 : Comment surveiller les performances LM Arena ?
**R** : Utilisez les tableaux de dashboards :
- **Performance** : Scores et classement en temps réel
- **Santé** : Disponibilité et erreurs
- **Analyse** : Qualité et cohérence des réponses

### Questions sur le Support

#### Q10 : Où trouver de l'aide ?
**R** :
- **Documentation** : `docs/guides/`
- **Support technique** : support@harmonic-ai.com
- **Communauté** : forum.harmonic-ai.com

#### Q11 : Comment signaler un bug ?
**R** : Utilisez le système de suivi des issues sur GitHub ou contactez le support technique.

#### Q12 : Comment contribuer au projet ?
**R** : Les contributions sont les bienvenues ! Consultez le guide de contribution dans `docs/contributing.md`.

---

## Conclusion

Le **Package LM Arena** de **Harmonic AI** est une solution complète et optimisée pour participer à la plateforme d'évaluation LM Arena. Avec son approche unique de déterminisme garanti, son mode vérifié et ses performances optimisées, il est conçu pour atteindre les meilleurs classements tout en offrant une fiabilité exceptionnelle.

### Points Clés à Retenir
1. **Installation simple** : Scripts automatisés pour toutes les plateformes
2. **Configuration flexible** : Variables d'environnement et fichiers YAML
3. **Services complets** : API, services harmoniques, frontend, monitoring
4. **Intégration LM Arena** : Prêt pour soumission immédiate
5. **Maintenance facilitée** : Scripts d'automatisation et documentation complète

### Prochaines Étapes
1. **Installer le package** : Suivez le guide d'installation
2. **Configurer votre environnement** : Éditez le fichier `.env`
3. **Démarrer les services** : Utilisez les scripts de démarrage
4. **Tester l'intégration** : Validez avec les tests LM Arena
5. **Soumettre sur LM Arena** : Lancez votre évaluation

### Contact
Pour toute question, suggestion ou problème :
- **Email** : contact@harmonic-ai.com
- **Site web** : [harmonic-ai.com](https://harmonic-ai.com)
- **Documentation** : [docs.harmonic-ai.com](https://docs.harmonic-ai.com)

**Harmonic AI - L'IA Community-Proof** 🚀

---

*Document généré le 17 mai 2026*  
*Dernière mise à jour : 17 mai 2026*  
*Version : 1.0.0*