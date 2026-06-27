# 🚀 HCV PRO - Guide Déploiement Entreprise

## 📋 **PRÉREQUIS DÉPLOIEMENT**

### 💻 **Configuration Système Minimale**
- **OS** : Windows 10/11, Windows Server 2019/2022, Ubuntu 20.04+, CentOS 8+
- **RAM** : 8GB minimum (16GB recommandé)
- **Stockage** : 50GB espace libre (SSD recommandé)
- **CPU** : 4 coeurs minimum (8 coeurs recommandé)
- **Réseau** : 1Gbps pour performances optimales
- **Droits** : Administrateur/root requis

### 🔧 **Dépendances Logicielles**
```bash
# Python 3.8+ requis
python --version

# Installation dépendances
pip install -r requirements.txt

# Vérification modules
python -c "import cryptography, flask, jwt, psutil"
```

---

## 🏗️ **ÉTAPES DÉPLOIEMENT**

### 1️⃣ **Préparation Environnement**
```bash
# 1. Création répertoire d'installation
sudo mkdir -p /opt/hcv-pro-enterprise
cd /opt/hcv-pro-enterprise

# 2. Téléchargement package
wget https://releases.hcv-pro.com/enterprise/hcv_pro_enterprise_latest.zip

# 3. Extraction
unzip hcv_pro_enterprise_latest.zip
chmod +x install.sh
```

### 2️⃣ **Installation Automatisée**
```bash
# Script d'installation
sudo ./install.sh

# Ou installation manuelle
sudo cp hcv_pro_enterprise /usr/local/bin/
sudo mkdir -p /etc/hcv-pro
sudo cp config/* /etc/hcv-pro/
sudo mkdir -p /var/log/hcv-pro
sudo mkdir -p /var/lib/hcv-pro
```

### 3️⃣ **Configuration Licence**
```bash
# Activation licence
sudo hcv-pro-enterprise --activate-license --key "VOTRE_CLÉ_LICENCE"

# Vérification licence
sudo hcv-pro-enterprise --check-license
```

### 4️⃣ **Démarrage Services**
```bash
# Démarrage service web
sudo systemctl start hcv-pro-web
sudo systemctl enable hcv-pro-web

# Démarrage service compression
sudo systemctl start hcv-pro-compressor
sudo systemctl enable hcv-pro-compressor

# Vérification statut
sudo systemctl status hcv-pro-*
```

---

## 🔧 **CONFIGURATION AVANCÉE**

### 📁 **Structure Répertoires**
```
/opt/hcv-pro-enterprise/
├── bin/
│   ├── hcv_pro_enterprise          # Exécutable principal
│   └── hcv-cli                   # Interface CLI
├── config/
│   ├── production.json             # Configuration production
│   ├── security.json              # Paramètres sécurité
│   └── license.json              # Fichier licence
├── data/
│   ├── compression.db            # Base de données
│   └── storage/                 # Stockage fichiers
├── logs/
│   ├── hcv-pro.log              # Logs applicatifs
│   ├── security.log             # Logs sécurité
│   └── performance.log          # Logs performance
├── web/
│   ├── static/                  # Assets web
│   └── templates/              # Templates HTML
└── scripts/
    ├── backup.sh                # Script backup
    ├── monitor.sh               # Script monitoring
    └── update.sh               # Script mise à jour
```

### ⚙️ **Configuration Production**
```json
{
  "production": {
    "server": {
      "host": "0.0.0.0",
      "port": 8080,
      "workers": 4,
      "timeout": 300,
      "max_connections": 1000
    },
    "security": {
      "https_only": true,
      "ssl_cert": "/etc/ssl/certs/hcv-pro.crt",
      "ssl_key": "/etc/ssl/private/hcv-pro.key",
      "client_certificates": true,
      "rate_limiting": {
        "enabled": true,
        "requests_per_minute": 100,
        "burst_size": 200
      }
    },
    "performance": {
      "cache_enabled": true,
      "cache_size": "1GB",
      "max_concurrent_jobs": 50,
      "job_timeout": 3600,
      "temp_cleanup_interval": 3600
    },
    "storage": {
      "temp_directory": "/tmp/hcv-pro",
      "output_directory": "/var/lib/hcv-pro/output",
      "max_storage_size": "1TB",
      "compression_level": "balanced"
    }
  }
}
```

### 🔐 **Configuration Sécurité**
```json
{
  "security": {
    "authentication": {
      "method": "jwt",
      "token_expiry": "8h",
      "refresh_token_expiry": "7d",
      "password_policy": {
        "min_length": 12,
        "require_uppercase": true,
        "require_lowercase": true,
        "require_numbers": true,
        "require_symbols": true
      }
    },
    "encryption": {
      "algorithm": "AES-256-GCM",
      "key_rotation_interval": "30d",
      "secure_temp_files": true,
      "memory_protection": true
    },
    "monitoring": {
      "audit_logging": true,
      "failed_login_threshold": 5,
      "lockout_duration": "15m",
      "anomaly_detection": true
    }
  }
}
```

---

## 🐳 **DÉPLOIEMENT DOCKER**

### 📦 **Dockerfile**
```dockerfile
FROM python:3.11-slim

# Installation dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Création utilisateur
RUN useradd -m -u 1000 hcvpro

# Configuration répertoires
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie application
COPY enterprise/ ./enterprise/
COPY dist/ ./dist/

# Configuration permissions
RUN chown -R hcvpro:hcvpro /app
USER hcvpro

# Exposition ports
EXPOSE 8080

# Démarrage
CMD ["python", "enterprise/src/web/app.py"]
```

### 🚀 **Docker Compose**
```yaml
version: '3.8'

services:
  hcv-pro-web:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
    environment:
      - FLASK_ENV=production
      - HCV_PRO_CONFIG=/app/config/production.json
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  hcv-pro-worker:
    build: .
    command: ["python", "enterprise/src/core/compressor.py"]
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
    environment:
      - HCV_PRO_CONFIG=/app/config/production.json
    restart: unless-stopped
    depends_on:
      - hcv-pro-web

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: hcvpro
      POSTGRES_USER: hcvpro
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
```

### 🎯 **Déploiement Docker**
```bash
# Build images
docker-compose build

# Démarrage services
docker-compose up -d

# Vérification statut
docker-compose ps

# Logs
docker-compose logs -f hcv-pro-web
```

---

## ☸️ **DÉPLOIEMENT KUBERNETES**

### 📋 **Namespace**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: hcv-pro-enterprise
  labels:
    name: hcv-pro-enterprise
```

### 🚀 **Deployment**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hcv-pro-web
  namespace: hcv-pro-enterprise
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hcv-pro-web
  template:
    metadata:
      labels:
        app: hcv-pro-web
    spec:
      containers:
      - name: hcv-pro-web
        image: hcv-pro/enterprise:latest
        ports:
        - containerPort: 8080
        env:
        - name: FLASK_ENV
          value: "production"
        - name: HCV_PRO_CONFIG
          value: "/app/config/production.json"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
        - name: data-volume
          mountPath: /app/data
      volumes:
      - name: config-volume
        configMap:
          name: hcv-pro-config
      - name: data-volume
        persistentVolumeClaim:
          claimName: hcv-pro-data
```

### 🌐 **Service**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: hcv-pro-web-service
  namespace: hcv-pro-enterprise
spec:
  selector:
    app: hcv-pro-web
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer
```

### 📊 **Ingress**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: hcv-pro-ingress
  namespace: hcv-pro-enterprise
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - hcv-pro.enterprise.com
    secretName: hcv-pro-tls
  rules:
  - host: hcv-pro.enterprise.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: hcv-pro-web-service
            port:
              number: 80
```

---

## 🔍 **MONITORING & MAINTENANCE**

### 📊 **Health Checks**
```bash
# Vérification statut service
curl http://localhost:8080/health

# Vérification licence
curl http://localhost:8080/api/system/license

# Statut compression
curl http://localhost:8080/api/system/status
```

### 📈 **Performance Monitoring**
```bash
# Script monitoring
#!/bin/bash
# monitor.sh

# Vérification CPU
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')

# Vérification mémoire
MEM_USAGE=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')

# Vérification disque
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')

# Vérification service
SERVICE_STATUS=$(systemctl is-active hcv-pro-web)

echo "CPU: ${CPU_USAGE}% | MEM: ${MEM_USAGE}% | DISK: ${DISK_USAGE}% | SERVICE: ${SERVICE_STATUS}"

# Alertes si seuils dépassés
if [ ${MEM_USAGE%.*} -gt 80 ]; then
    echo "ALERTE: Utilisation mémoire élevée: ${MEM_USAGE}%"
fi

if [ ${DISK_USAGE} -gt 85 ]; then
    echo "ALERTE: Espace disque faible: ${DISK_USAGE}%"
fi

if [ "$SERVICE_STATUS" != "active" ]; then
    echo "ALERTE: Service HCV PRO arrêté"
    systemctl restart hcv-pro-web
fi
```

### 🔄 **Backup Automatisé**
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/hcv-pro/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup configuration
cp -r /etc/hcv-pro "$BACKUP_DIR/config"

# Backup base de données
pg_dump hcvpro > "$BACKUP_DIR/database.sql"

# Backup logs (derniers 7 jours)
find /var/log/hcv-pro -name "*.log" -mtime -7 -exec cp {} "$BACKUP_DIR/logs" \;

# Compression backup
tar -czf "$BACKUP_DIR.tar.gz" -C "$(dirname "$BACKUP_DIR")" "$(basename "$BACKUP_DIR")"
rm -rf "$BACKUP_DIR"

# Nettoyage anciens backups (30 jours)
find /backup/hcv-pro -name "*.tar.gz" -mtime +30 -delete

echo "Backup terminé: $BACKUP_DIR.tar.gz"
```

---

## 🚨 **DÉPANNAGE**

### ❌ **Problèmes Communs**

#### **Service ne démarre pas**
```bash
# Vérification logs
journalctl -u hcv-pro-web -f

# Vérification configuration
hcv-pro-enterprise --validate-config

# Vérification dépendances
hcv-pro-enterprise --check-deps
```

#### **Problèmes de licence**
```bash
# Vérification licence
hcv-pro-enterprise --license-status

# Réactivation licence
hcv-pro-enterprise --reactivate-license --key "NOUVELLE_CLÉ"

# Hardware binding reset
hcv-pro-enterprise --reset-hardware-binding
```

#### **Performance lente**
```bash
# Vérification ressources
top -p $(pgrep hcv-pro-enterprise)
iotop -p $(pgrep hcv-pro-enterprise)

# Optimisation configuration
hcv-pro-enterprise --optimize-config

# Cache cleanup
hcv-pro-enterprise --clear-cache
```

### 📞 **Support Technique**
- **Email** : support@hcv-pro.com
- **Téléphone** : +33-1-234-567-890
- **Documentation** : https://docs.hcv-pro.com/enterprise
- **Status** : https://status.hcv-pro.com

---

## ✅ **VÉRIFICATION DÉPLOIEMENT**

### 🎯 **Checklist Post-Déploiement**
- [ ] Service web démarré et accessible
- [ ] Licence activée et valide
- [ ] Base de données connectée
- [ ] Logs configurés et fonctionnels
- [ ] Monitoring activé
- [ ] Backup automatisé configuré
- [ ] SSL/TLS configuré
- [ ] Firewall configuré
- [ ] Performance testée
- [ ] Documentation utilisateur disponible

### 🧪 **Tests Fonctionnels**
```bash
# Test compression
curl -X POST http://localhost:8080/api/compress \
  -F "file=@test.txt" \
  -F "mode=balanced" \
  -F "security_level=quantum_harmonic"

# Test API
curl http://localhost:8080/api/system/info

# Test web interface
curl http://localhost:8080/
```

---

**🚀 Le déploiement entreprise HCV PRO est maintenant terminé !**

**Pour toute assistance technique, contactez le support entreprise : support@hcv-pro.com**
