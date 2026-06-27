# 🚀 HCV PRO Enterprise - Version AWS Adaptée

## 📋 Overview

HCV PRO Enterprise - AWS Adaptée est une interface web entreprise complète basée sur l'application AWS de production, intégrant toutes les fonctionnalités de compression avec sécurité renforcée et monitoring avancé.

## 🏗️ Architecture

```
                    Internet
                        │
                ┌───────┴───────┐
                │  Enterprise  │
                │   Frontend   │
                │   (React)    │
                └───────┬───────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
┌───────┴───────┐               ┌───────┴───────┐
│   Flask API   │               │   Security    │
│   Backend     │               │   Layer       │
│  (Enterprise) │               │  (JWT/HTTPS)  │
└───────┬───────┘               └───────┬───────┘
        │                               │
        └───────────────┬───────────────┘
                        │
        ┌───────────────┴───────────────┐
        │        HCV PRO Codecs         │
        │  Broadcast | Android | Video  │
        └───────────────────────────────┘
```

## 🚀 Quick Start

### Prérequis

- Python 3.11+
- Dependencies dans `requirements.txt`
- Navigateur web moderne

### Lancement

```bash
# Naviguer vers le dossier enterprise
cd enterprise

# Lancer l'application
python src/web/app_aws_enterprise.py

# Accéder à l'application
# http://localhost:8081
```

### Identifiants par défaut

| Rôle | Username | Password | Permissions |
|------|----------|----------|--------------|
| Administrateur | `admin` | `HCV_PRO_2024_ENTERPRISE` | Tous les accès |
| AWS Admin | `aws_admin` | `AWS_ENTERPRISE_2024` | Tous les accès + AWS |
| Utilisateur | `user` | `HCV_USER_2024` | Compression, téléchargement |
| Démo | `demo` | `demo123` | Compression limitée |

## 🔐 Sécurité

### Authentification JWT

- Tokens valides 12 heures (entreprise)
- Clé secrète générée dynamiquement
- Refresh automatique possible

### Sécurité des endpoints

- Rate limiting: 200 requêtes/heure
- Validation des inputs
- Protection contre les attaques CSRF
- Headers sécurité: CSP, HSTS, X-Frame-Options

### Permissions

```python
# Administrateur
permissions: ['all']

# AWS Admin  
permissions: ['all']

# Utilisateur
permissions: ['compress', 'download']

# Démo
permissions: ['compress']
```

## 📡 API Endpoints

### Authentification

```http
POST /api/auth
Content-Type: application/json

{
  "username": "admin",
  "password": "HCV_PRO_2024_ENTERPRISE"
}
```

### Compression

#### Broadcast (RAW/SDI)
```http
POST /api/compress
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <fichier>
```

#### Demo Broadcast
```http
POST /api/demo
Authorization: Bearer <token>
Content-Type: multipart/form-data

resolution: HD
duration: 5.0
```

#### Android Boost (JPEG)
```http
POST /api/android-boost
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <fichier>
quality: high
```

#### Video Boost (H264)
```http
POST /api/video-boost
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <fichier>
quality: high
audio_bitrate: 128k
target_resolution: auto
```

#### Précompressé
```http
POST /api/precompressed
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <fichier>
```

### Gestion des Jobs

#### Lister tous les jobs
```http
GET /api/jobs
Authorization: Bearer <token>
```

#### Statut d'un job
```http
GET /api/job-status/<job_id>
Authorization: Bearer <token>
```

#### Annuler un job
```http
POST /api/job/<job_id>/cancel
Authorization: Bearer <token>
```

#### Télécharger un résultat
```http
GET /api/download/<job_id>
Authorization: Bearer <token>
```

### Système

#### Health Check
```http
GET /api/health
```

#### Status complet
```http
GET /api/status
Authorization: Bearer <token>
```

#### Historique
```http
GET /api/history
Authorization: Bearer <token>
```

## 🎛️ Dashboard Features

### Vue d'ensemble

- **Statistiques en temps réel**: Jobs actifs, total, complétés, échecs
- **Uptime système**: Temps de fonctionnement depuis le démarrage
- **Monitoring**: Rafraîchissement automatique toutes les 3 secondes

### Gestion des Jobs

- **Liste en temps réel**: Tous les jobs avec progression
- **Actions rapides**: Annuler les jobs en cours, télécharger les résultats
- **Statuts visuels**: Processing, Completed, Failed, Cancelled
- **Barres de progression**: Animation fluide de l'avancement

### Compression

- **Interface unifiée**: Tous les types de compression dans un formulaire
- **Options dynamiques**: Champs qui s'adaptent selon le type choisi
- **Upload drag & drop**: Interface moderne de sélection de fichiers
- **Feedback immédiat**: Alertes de succès/erreur

### Types de Compression

1. **📡 Broadcast (RAW/SDI)**
   - Support des signaux broadcast professionnels
   - Compression haute qualité jusqu'à 20x
   - Compatible SDI et RAW

2. **🎬 Demo Broadcast**
   - Génération de contenu de test
   - Résolutions: VGA, HD, FHD, 4K
   - Durée personnalisable

3. **📱 Android Boost (JPEG)**
   - Optimisé pour mobile Android
   - Qualité: High, Medium, Low
   - Compression jusqu'à 8.5x

4. **🎥 Video Boost (H264)**
   - Compression vidéo avec ffmpeg
   - Support audio bitrate
   - Résolution cible automatique

5. **📦 Précompressé**
   - Amélioration de fichiers existants
   - Support JPEG, PNG, WebP, GIF
   - Boost ratio jusqu'à 1.5x

## 🔧 Configuration

### Variables d'environnement

```bash
# Configuration Flask
FLASK_ENV=development
PORT=8081

# Sécurité
HCV_PRO_SECRET_KEY=votre_clé_secrète
JWT_EXPIRATION_HOURS=12

# Rate limiting
RATE_LIMIT_REQUESTS=200
RATE_LIMIT_WINDOW=3600

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/enterprise_aws.log
```

### Configuration des codecs

```python
# Configuration dans app_aws_enterprise.py
codecs = {
    'broadcast': HCVProCodec(),
    'android_boost': HCVAndroidBoostCodec(),
    'compressor': HCVCompressorSecure()
}
```

## 📊 Monitoring & Logging

### Logs

- **Application**: `logs/enterprise_aws.log`
- **Accès**: Console et fichier
- **Niveau**: INFO par défaut
- **Rotation**: Configurable

### Métriques

- **Jobs**: Total, actifs, complétés, échecs
- **Performance**: Temps de traitement, taux de compression
- **Système**: Uptime, mémoire, CPU
- **Sécurité**: Tentatives d'authentification, rate limiting

### Alertes

- **Succès**: Compression terminée, job créé
- **Erreurs**: Échec de compression, authentification
- **Système**: Problèmes de codec, mémoire insuffisante

## 🚀 Déploiement

### Développement

```bash
# Installation dépendances
pip install -r requirements.txt

# Lancement développement
python src/web/app_aws_enterprise.py
```

### Production

```bash
# Avec Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8081 "app_aws_enterprise:HCVEnterpriseAWS().app"

# Avec Docker
docker build -t hcv-enterprise-aws .
docker run -p 8081:8081 hcv-enterprise-aws
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8081

CMD ["python", "src/web/app_aws_enterprise.py"]
```

## 🔍 Dépannage

### Problèmes courants

#### Port déjà utilisé
```bash
# Trouver le processus
netstat -ano | findstr :8081

# Tuer le processus
taskkill /PID <PID> /F
```

#### Erreur d'authentification
- Vérifier le token JWT
- Confirmer les identifiants
- Vérifier l'expiration (12h)

#### Jobs ne progressent pas
- Vérifier les logs dans `logs/enterprise_aws.log`
- Confirmer que les codecs sont initialisés
- Vérifier les permissions des fichiers

### Debug Mode

```python
# Activer le debug dans app_aws_enterprise.py
app.run(host='0.0.0.0', port=8081, debug=True)
```

## 📈 Performance

### Optimisations

- **Async processing**: Jobs en arrière-plan
- **Rate limiting**: Protection contre DDoS
- **Caching**: Templates et static files
- **Compression**: GZIP activé

### Benchmarks

- **Démarrage**: < 3 secondes
- **Authentification**: < 100ms
- **Création job**: < 50ms
- **Liste jobs**: < 200ms

## 🔄 Mises à jour

### Version actuelle: v1.0.0

#### Fonctionnalités
- ✅ Authentification JWT entreprise
- ✅ Tous les types de compression AWS
- ✅ Dashboard temps réel
- ✅ Gestion complète des jobs
- ✅ Sécurité renforcée
- ✅ Monitoring avancé

#### Roadmap v1.1.0
- 🔄 Support WebSocket pour temps réel
- 🔄 Notifications push
- 🔄 Export CSV des statistiques
- 🔄 Multi-langues

## 📞 Support

### Documentation technique

- **Code source**: `enterprise/src/web/`
- **Templates**: `enterprise/templates/`
- **Static**: `enterprise/static/`
- **Logs**: `enterprise/logs/`

### Contact

- **Issues**: GitHub repository
- **Documentation**: README.md
- **API**: Postman collection disponible

---

**HCV PRO Enterprise - AWS Adaptée**  
*Version professionnelle avec toutes les fonctionnalités AWS*
