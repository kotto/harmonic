# 🚀 Déploiement du KA Server sur Oracle Cloud (aux côtés de l'admin-server)

## Architecture finale

```
Internet
    │
    ▼
┌──────────────────────────────────────────┐
│  Nginx HÔTE (Oracle VM)                  │
│  • Port 443 (HTTPS) — site vitrine       │
│  • Port 80 (HTTP → HTTPS)               │
│  Proxy vers :                             │
│    /api/v1/*          → admin-api:8000   │
│    /api/banking/*     → ka-server:8765   │
│    /banking/*         → ka-server:8765   │
│    /api/sonic-id/*    → ka-server:8765   │
│    /api/health        → ka-server:8765   │
└────────────────┬─────────────────────────┘
                 │
    ┌────────────┴────────────┐
    ▼                         ▼
┌──────────────┐     ┌──────────────┐
│ admin-api    │     │  ka-server   │
│ (FastAPI)    │     │  (Flask)     │
│ port 8000    │     │  port 8765   │
│ Dossiers     │     │  Banking,    │
│ patients,    │     │  Simulation, │
│ utilisateurs │     │  Sonic ID    │
└──────────────┘     └──────────────┘
```

---

## Prérequis

- Instance Oracle Cloud (Ubuntu 22.04+)
- Docker et Docker Compose v2 installés
- Admin-server Vital KA déjà déployé dans `/opt/vitalka/admin-server`

---

## Étape 1 — Copier le dossier engine sur Oracle

```bash
# Depuis ta machine locale
cd E:/SAAS - Copie
scp -r engine/ user@ORACLE_IP:/opt/vitalka/
```

---

## Étape 2 — Configurer l'environnement

```bash
ssh user@ORACLE_IP

cd /opt/vitalka/engine

# Générer les secrets
python -c "import secrets; print('KA_BANKING_SECRET=' + secrets.token_hex(32))"
python -c "import secrets; print('KA_API_KEYS=' + secrets.token_urlsafe(32))"

# Copier et éditer le .env de production
cp .env.production .env
nano .env   # Remplir les valeurs générées ci-dessus
```

---

## Étape 3 — Ajouter le service Docker

```bash
cd /opt/vitalka/admin-server

# Démarrer avec le nouveau service KA Server
docker compose -f docker-compose.prod.yml -f docker-compose.ka-server.yml up -d

# Vérifier que le conteneur tourne
docker compose -f docker-compose.prod.yml -f docker-compose.ka-server.yml ps

# Voir les logs
docker compose -f docker-compose.prod.yml -f docker-compose.ka-server.yml logs ka-server
```

---

## Étape 4 — Configurer le reverse proxy Nginx (hôte)

Sur l'hôte Oracle (pas dans Docker), ajouter cette configuration au nginx système :

```bash
sudo nano /etc/nginx/sites-available/ka-server
```

```nginx
# ─── KA Server — Banking, Simulation, Sonic ID ───
server {
    listen 8765;
    server_name _;

    # CORS
    add_header Access-Control-Allow-Origin "*" always;
    add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Content-Type, Authorization, X-API-Key, Idempotency-Key, X-Signature" always;

    # Réponses OPTIONS (preflight) sans authentification
    if ($request_method = OPTIONS) {
        return 204;
    }

    # API bancaire et simulation
    location /api/ {
        proxy_pass http://127.0.0.1:8765;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }

    # Pages de la console
    location /banking/ {
        proxy_pass http://127.0.0.1:8765;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Empreinte sonore (Sonic ID)
    location /api/sonic-id/ {
        proxy_pass http://127.0.0.1:8765/api/sonic-id/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_valid 200 1d;  # Cache des WAV 24h
        add_header Cache-Control "public, max-age=86400, immutable";
    }
}
```

Activer et recharger :

```bash
sudo ln -s /etc/nginx/sites-available/ka-server /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Étape 5 — Intégration dans le site existant

Pour que les pages de la console soient accessibles depuis le domaine principal (ex: `https://ka-mobile.onrender.com/banking/simulate`), ajouter dans la config nginx existante :

```nginx
# Dans le bloc server HTTPS existant

location /banking/ {
    proxy_pass http://127.0.0.1:8765/banking/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /api/sonic-id/ {
    proxy_pass http://127.0.0.1:8765;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

---

## Étape 6 — Vérification

```bash
# Test santé
curl http://localhost:8765/api/banking/health

# Test simulation
curl -X POST http://localhost:8765/api/banking/simulate \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: <VOTRE_CLE>' \
  -d '{"scenario": "consultation_transfrontaliere", "async": false}'

# Test Sonic ID
curl http://localhost:8765/api/sonic-id/TEST-001 -o /dev/null -w "%{http_code}"

# Console bancaire (navigateur)
open http://<ORACLE_IP>:8765/banking/console

# Simulation (navigateur)
open http://<ORACLE_IP>:8765/banking/simulate
```

---

## Commandes utiles

```bash
# Logs en temps réel
docker compose -f docker-compose.prod.yml -f docker-compose.ka-server.yml logs -f ka-server

# Redémarrer le KA Server
docker compose -f docker-compose.prod.yml -f docker-compose.ka-server.yml restart ka-server

# Mise à jour (après avoir copié la nouvelle version du code)
docker compose -f docker-compose.prod.yml -f docker-compose.ka-server.yml build ka-server
docker compose -f docker-compose.prod.yml -f docker-compose.ka-server.yml up -d

# Backup des données bancaires
docker cp vitalka-ka-server:/opt/vitalka/engine/data/banking ./backup_banking_$(date +%Y%m%d)

# Inspection de l'état
docker exec vitalka-ka-server python -c "
from ka_server.services import settlement
s = settlement.get_state_summary()
print(f'Comptes: {s[\"accounts\"]}')
print(f'Ledger: {s[\"ledger_entries\"]} entrées')
print(f'UM en circulation: {s[\"total_um_in_circulation\"]}')
"
```