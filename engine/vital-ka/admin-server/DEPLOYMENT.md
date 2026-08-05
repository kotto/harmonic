# 🚀 Déploiement VPS — Serveur d'administration Vital KA

Guide de déploiement complet du serveur d'administration Vital KA sur un VPS auto-hébergé.

---

## 1. Prérequis VPS

| Composant | Minimum | Recommandé |
|---|---|---|
| CPU | 2 vCPU | 4 vCPU |
| RAM | 4 GB | 8 GB |
| Stockage | 40 GB SSD | 80 GB SSD |
| OS | Ubuntu 22.04 / Debian 12 | Ubuntu 24.04 LTS |
| Réseau | IPv4 public | IPv4 + IPv6 |

**Ouvertures de ports :**
- `80` (HTTP — redirection vers HTTPS)
- `443` (HTTPS)
- `22` (SSH, restreindre si possible)
- Les ports internes (Postgres, Redis, MinIO, API) **ne doivent pas être exposés** — ils sont internes au réseau Docker.

---

## 2. Préparation du serveur

```bash
# Mise à jour système
sudo apt update && sudo apt upgrade -y

# Installation Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# Se déconnecter/reconnecter pour activer le groupe docker

# Installation Docker Compose v2 (inclus avec docker via plugin)
docker compose version

# Obfuscation SSH (optionnel mais recommandé)
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

---

## 3. Récupération du projet

```bash
mkdir -p /opt/vitalka && cd /opt/vitalka

# Copier le dossier admin-server depuis votre poste de dev (SCP, rsync, ou git)
scp -r ./vital-ka/admin-server user@VPS_IP:/opt/vitalka/

cd /opt/vitalka/admin-server
```

---

## 4. Configuration de l'environnement

```bash
cp .env.example .env
nano .env   # Éditer toutes les valeurs
```

### Variables critiques à modifier :

```bash
# ── Sécurité ──
JWT_SECRET_KEY=CHANGEME_openssl_rand_hex_32
# Générer : openssl rand -hex 32

# ── Base de données ──
POSTGRES_PASSWORD=CHANGEME_Postgres_password
DATABASE_URL=postgresql+asyncpg://vitalka_admin:CHANGEME@postgres:5432/vitalka_admin

# ── Redis ──
REDIS_URL=redis://:CHANGEME_redis_password@redis:6379/0

# ── MinIO ──
MINIO_ROOT_USER=vitalka-admin
MINIO_ROOT_PASSWORD=CHANGEME_MinIO_password
MINIO_ACCESS_KEY=vitalka-admin
MINIO_SECRET_KEY=CHANGEME_MinIO_password

# ── Domaine & SMTP ──
DOMAIN=admin.votre-domaine.com
SMTP_HOST=smtp.votre-fournisseur.com
SMTP_PORT=587
SMTP_USER=no-reply@votre-domaine.com
SMTP_PASSWORD=CHANGEME_smtp_password
```

---

## 5. Démarrage de la stack

```bash
cd /opt/vitalka/admin-server

# Build des images (première fois uniquement)
docker compose build

# Démarrage des services de fond (base de données, cache, stockage)
docker compose up -d postgres redis minio

# Attendre que la DB soit prête
docker compose logs -f postgres   # Ctrl+C quand "ready to accept connections"

# Appliquer les migrations
docker compose run --rm admin-api alembic upgrade head

# Démarrage complet
docker compose up -d

# Vérifier l'état
docker compose ps
```

**Vérifier la santé :**
```bash
curl http://localhost:8000/api/v1/admin/health/live   # {"status": "ok"}
curl http://localhost:8000/api/v1/admin/health
```

---

## 6. Création du premier administrateur

```bash
docker compose run --rm admin-api python scripts/bootstrap_admin.py \
  --email admin@votre-domaine.com \
  --password "MotDePasseFort!123" \
  --first "Admin" \
  --last "Vital KA"

# Initialiser les configurations par défaut
curl -X POST http://localhost:8000/api/v1/admin/config/init-defaults \
  -H "Authorization: Bearer $(TOKEN)"
```

**Important :** changez le mot de passe du premier admin après la première connexion (page Profil).

---

## 7. SSL avec Let's Encrypt

### Option A — Automatique via Certbot (docker-compose inclus)

```bash
# Éditer docker-compose.yml : décommenter le service certbot et son volume
# Puis :
docker compose up -d certbot
docker compose logs -f certbot   # attendre l'obtention des certificats

# Redémarrer nginx pour charger les certificats
docker compose restart nginx
```

### Option B — Manuel (première configuration)

```bash
# Installer certbot sur le serveur hôte
sudo apt install -y certbot

# Obtenir le certificat (nginx doit être démarré sur le port 80)
sudo certbot certonly --standalone -d admin.votre-domaine.com --email vous@domaine.com --agree-tos

# Copier les certificats dans le dossier nginx/certs
sudo cp /etc/letsencrypt/live/admin.votre-domaine.com/fullchain.pem nginx/certs/fullchain.pem
sudo cp /etc/letsencrypt/live/admin.votre-domaine.com/privkey.pem nginx/certs/privkey.pem

# Renouvellement automatique
sudo crontab -e
# Ajouter : 0 3 * * * certbot renew --quiet --deploy-hook "docker compose -f /opt/vitalka/admin-server/docker-compose.yml restart nginx"
```

---

## 8. Configuration DNS

| Type | Nom | Valeur |
|---|---|---|
| A | admin | VPS_IP |
| AAAA | admin | VPS_IPV6 (optionnel) |

Attendre la propagation DNS (5-30 min) avant le certificat SSL.

---

## 9. Configuration SMTP (emails)

Le serveur envoie des emails pour : validation KYC, rejet, suspension, reset de mot de passe.

### Fournisseurs testés :
- **Brevo (ex-Sendinblue)** : gratuit jusqu'à 300 emails/jour
- **Mailgun** : gratuit 100 emails/jour
- **Amazon SES** : 62 000 emails/mois après validation
- **SMTP de votre hébergeur** (OVH, Ionos, etc.)

Exemple Brevo :
```bash
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=login@brevo.com
SMTP_PASSWORD=xxx
```

**Test :** déclenchez un reset de mot de passe sur la page de login → l'email doit arriver en quelques secondes.

---

## 10. Configuration Nginx (reverse proxy principal)

Le fichier `nginx/nginx.conf` inclut des templates avec `$DOMAIN`. Pour le personnaliser :

```bash
# Éditer le fichier nginx/conf.d/00-vitalka.conf (voir modèle dans nginx/nginx.conf)
# Utiliser sed pour remplacer les variables
sed -i 's/\$DOMAIN/admin.votre-domaine.com/g' nginx/conf.d/00-vitalka.conf
```

---

## 11. Sauvegardes

### Sauvegardes automatiques (via l'UI)
Le panneau **Système → Sauvegardes** permet de déclencher des backups DB + fichiers à la demande.

### Sauvegardes programmées (recommandé)

```bash
# Script hebdomadaire (cron)
cat > /etc/cron.d/vitalka-backup << 'EOF'
0 2 * * 0 root /opt/vitalka/admin-server/scripts/backup.sh
EOF

# Script de base (à personnaliser) :
cat > /opt/vitalka/admin-server/scripts/backup.sh << 'EOF'
#!/bin/bash
cd /opt/vitalka/admin-server
BACKUP_DIR=/var/backups/vitalka
mkdir -p $BACKUP_DIR
docker compose exec -T postgres pg_dump -U vitalka_admin vitalka_admin | gzip > $BACKUP_DIR/db_$(date +%Y%m%d).sql.gz
# Uploader vers un stockage distant (rclone, rsync, etc.)
rclone copy $BACKUP_DIR remote:vitalka-backups/
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
EOF
chmod +x /opt/vitalka/admin-server/scripts/backup.sh
```

**Testez la restauration au moins une fois !**

---

## 12. Mise à jour de l'application

```bash
cd /opt/vitalka/admin-server

# 1. Récupérer les nouveaux fichiers (git pull ou rsync)
git pull

# 2. Rebuild des images
docker compose build admin-api admin-worker

# 3. Appliquer les migrations
docker compose run --rm admin-api alembic upgrade head

# 4. Redémarrer les services
docker compose up -d --force-recreate admin-api admin-worker admin-scheduler
```

---

## 13. Monitoring

| Service | URL | Accès |
|---|---|---|
| Grafana | `https://admin.votre-domaine.com/grafana` | admin / défini au premier login |
| Prometheus | interne (port 9090) | non exposé |
| Loki | interne (port 3100) | non exposé |

Dashboards inclus :
- **Vital KA — API** : requêtes, latence, erreurs, pool DB
- **Vital KA — Système** : CPU, RAM, disque des conteneurs
- **Vital KA — Logs** : recherche dans les logs applicatifs

---

## 14. Opérations courantes

```bash
# Logs en temps réel
docker compose logs -f admin-api
docker compose logs -f admin-worker

# Restart d'un service
docker compose restart admin-api

# Voir les métriques Prometheus
curl http://localhost:8000/metrics | head

# Entrer dans un conteneur
docker compose exec admin-api sh

# Vérifier la taille des volumes
docker system df

# Nettoyage des images obsolètes
docker image prune -a
```

---

## 15. Checklist de sécurité avant mise en production

- [ ] `JWT_SECRET_KEY` changé (openssl rand -hex 32)
- [ ] Mots de passe Postgres, Redis, MinIO changés
- [ ] Premier admin créé et mot de passe changé
- [ ] HTTPS actif (Let's Encrypt) — pas d'accès en HTTP
- [ ] Ports internes non exposés (firewall : uniquement 80/443/22)
- [ ] SSH avec clés uniquement (PasswordAuthentication no)
- [ ] Sauvegarde hebdomadaire testée (restauration vérifiée)
- [ ] Mises à jour OS automatiques activées
- [ ] Fail2ban installé (protection brute force)
- [ ] Email SMTP fonctionnel (test de reset de mot de passe)

---

## 16. Dépannage

| Problème | Solution |
|---|---|
| `Connection refused` à la DB | Attendre postgres : `docker compose logs postgres` |
| Migration échoue | Vérifier `DATABASE_URL` dans `.env` (host=postgres, pas localhost) |
| 401 sur l'API | Vérifier `JWT_SECRET_KEY` identique entre les conteneurs |
| MinIO inaccessible | Vérifier les credentials dans `.env` et le volume minio_data |
| CORS bloqué | Vérifier `CORS_ORIGINS` dans `.env` |
| Email non envoyé | Vérifier les logs : `docker compose logs admin-api \| grep -i smtp` |
| Certificat expiré | `docker compose up -d certbot` puis restart nginx |
