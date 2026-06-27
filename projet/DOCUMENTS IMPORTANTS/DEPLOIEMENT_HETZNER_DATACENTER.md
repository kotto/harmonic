# 🚀 Déploiement Datacenter Harmonique sur Hetzner
## Guide complet — Démarrage immédiat
### Alain Kotto — 27 Mai 2026

---

## 📋 Résumé exécutif

| Élément | Valeur |
|---------|--------|
| **Hébergeur** | Hetzner Cloud |
| **Serveur** | CX22 (2 vCPU, 4 Go RAM, 40 Go SSD) |
| **Coût mensuel** | **3.99€ HT** (~4.80€ TTC) |
| **OS** | Ubuntu 24.04 LTS |
| **Domaine** | Optionnel (~10€/an) |
| **Stack** | Python 3.12 + FastAPI + uvicorn + nginx |
| **Temps de setup** | ~15 minutes |

---

## 1. CRÉATION DU SERVEUR HETZNER

### Étape 1.1 : Compte Hetzner Cloud

1. Aller sur https://www.hetzner.com/cloud
2. Créer un compte (email + mot de passe)
3. Ajouter un moyen de paiement (carte bancaire ou PayPal)
4. Accéder à la console Cloud : https://console.hetzner.cloud

### Étape 1.2 : Créer le serveur

Dans la console Hetzner Cloud :

```
┌─────────────────────────────────────────────────────────────┐
│                      CRÉER UN SERVEUR                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Emplacement     : Nuremberg (de)  ou  Falkenstein (de)     │
│  Image           : Ubuntu 24.04 LTS                         │
│  Type            : CX22 (2 vCPU, 4 Go RAM, 40 Go SSD)      │
│                    → 3.99€/mois                             │
│                                                              │
│  Clé SSH         : Ajouter votre clé publique               │
│                    (ou créer une nouvelle)                   │
│                                                              │
│  Nom             : harmonic-datacenter                      │
│                                                              │
│  ☑️  Créer et acheter                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Prix : 3.99€/mois** (facturé à l'heure ~0.005€/h — vous pouvez détruire à tout moment)

### Étape 1.3 : Récupérer l'IP

Après création, notez l'adresse IP publique :

```
Adresse IPv4 : 49.13.XX.XX
```

---

## 2. CONNEXION SSH ET CONFIGURATION INITIALE

```bash
# Se connecter au serveur
ssh root@49.13.XX.XX

# Mise à jour du système
apt update && apt upgrade -y

# Installation des dépendances
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git curl
```

---

## 3. DÉPLOIEMENT DU CODE

### Option A : Upload direct (simple)

```bash
# Sur votre machine locale, archiver le projet
cd "h:\SAAS - Copie"
tar -czf harmonic_datacenter.tar.gz \
  bridge_harmonic_deepseek_gguf.py \
  ka_reasoning_engine.py \
  datacenter_harmonic.py \
  harmonic_training/model/harmonic_resonance_generator.py

# Uploader sur le serveur
scp harmonic_datacenter.tar.gz root@49.13.XX.XX:/root/
```

### Option B : Git (recommandé)

```bash
# Sur le serveur
cd /opt
git clone https://github.com/votre-username/harmonic-ai.git
cd harmonic-ai
```

### Sur le serveur : installation

```bash
# Créer le dossier applicatif
mkdir -p /opt/harmonic-datacenter
cd /opt/harmonic-datacenter

# Extraire l'archive (Option A)
tar -xzf /root/harmonic_datacenter.tar.gz

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install --upgrade pip
pip install fastapi uvicorn numpy

# Tester le démarrage
python datacenter_harmonic.py
# → Devrait afficher "DATACENTER HARMONIQUE — Démarrage"
# → Ctrl+C pour arrêter
```

---

## 4. CONFIGURATION NGINX (REVERSE PROXY + HTTPS)

```bash
# Créer la configuration nginx
cat > /etc/nginx/sites-available/harmonic-datacenter << 'NGINX'
server {
    listen 80;
    server_name votre-domaine.com 49.13.XX.XX;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8900;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
    }
}
NGINX

# Activer le site
ln -s /etc/nginx/sites-available/harmonic-datacenter /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Vérifier la configuration
nginx -t

# Redémarrer nginx
systemctl restart nginx
systemctl enable nginx
```

### HTTPS (optionnel, si vous avez un domaine)

```bash
# Installer certificat SSL gratuit (Let's Encrypt)
certbot --nginx -d votre-domaine.com --non-interactive --agree-tos -m votre@email.com
```

---

## 5. SERVICE SYSTEMD (DÉMARRAGE AUTOMATIQUE)

```bash
cat > /etc/systemd/system/harmonic-datacenter.service << 'SERVICE'
[Unit]
Description=Harmonic AI Datacenter
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/harmonic-datacenter
ExecStart=/opt/harmonic-datacenter/venv/bin/python datacenter_harmonic.py --host 127.0.0.1 --port 8900
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SERVICE

# Activer et démarrer
systemctl daemon-reload
systemctl enable harmonic-datacenter
systemctl start harmonic-datacenter

# Vérifier le statut
systemctl status harmonic-datacenter

# Voir les logs en direct
journalctl -u harmonic-datacenter -f
```

---

## 6. FIREWALL (UFW)

```bash
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8900/tcp  # API direct (optionnel, pour test)
ufw enable
ufw status
```

---

## 7. VÉRIFICATION

```bash
# Test local sur le serveur
curl http://localhost:8900/

# Test via nginx
curl http://49.13.XX.XX/

# Test de l'API d'entraînement
curl -X POST http://49.13.XX.XX/api/v1/train \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "documents": ["Le droit civil francais...", "Article 1240..."]}'

# Test de génération
curl -X POST http://49.13.XX.XX/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "prompt": "Qu est-ce que le code civil ?"}'

# Dashboard
# Ouvre http://49.13.XX.XX/dashboard dans ton navigateur
```

---

## 8. STRUCTURE DE FICHIERS SUR LE SERVEUR

```
/opt/harmonic-datacenter/
├── venv/                          # Environnement Python
├── bridge_harmonic_deepseek_gguf.py
├── ka_reasoning_engine.py
├── datacenter_harmonic.py         # ← Le service principal
├── harmonic_training/
│   └── model/
│       └── harmonic_resonance_generator.py
├── datacenter_storage/            # Données clients (créé auto)
│   ├── clients/
│   │   ├── client_1.holo          # 32 Ko par client
│   │   └── client_2.holo
│   ├── registry.json             # Registre des clients
│   ├── cache/
│   └── logs/
└── ka_knowledge_base/             # Base de connaissances globale
    └── hologramme.npy
```

---

## 9. COMMANDES UTILES

```bash
# Redémarrer le service
systemctl restart harmonic-datacenter

# Voir les logs
journalctl -u harmonic-datacenter -n 50

# Voir les clients enregistrés
curl http://localhost:8900/api/v1/clients

# Sauvegarde des données clients
tar -czf backup_clients.tar.gz /opt/harmonic-datacenter/datacenter_storage/clients/

# Espace disque
df -h
```

---

## 10. PLAN DE MONTÉE EN CHARGE

| Serveur | Prix/mois | vCPU | RAM | SSD | Clients supportés |
|---------|:---------:|:----:|:---:|:---:|:-----------------:|
| **CX22** | 3.99€ | 2 | 4 Go | 40 Go | ~100 |
| **CX32** | 7.99€ | 4 | 8 Go | 80 Go | ~500 |
| **CX42** | 15.99€ | 8 | 16 Go | 160 Go | ~2 000 |
| **CX52** | 31.99€ | 16 | 32 Go | 360 Go | ~10 000 |

---

## 💰 Projection rapide

```
Serveur CX22 (3.99€/mois) :
  → 100 clients × 999€/mois = 99 900€/mois de revenu potentiel
  → Coût infrastructure : 3.99€ + domaine ~10€/an
  → Marge : 99.99%
```

---

*Guide établi le 27 mai 2026 — Prêt à déployer maintenant.*