# Déploiement KA MOBILE sur Oracle Cloud Free Tier

**Instance ARM (4 vCPU, 24 Go RAM, 200 Go) — 0 €/mois**

---

## Étape 1 : Connexion au compte Oracle Cloud

```bash
# 1. Aller sur https://cloud.oracle.com
# 2. Menu burger → Compute → Instances
# 3. Cliquer "Create instance"
```

## Étape 2 : Créer l'instance

```
┌─────────────────────────────────────────────────────────────┐
│ Create compute instance                                     │
│                                                             │
│ Name: ka-mobile                                             │
│                                                             │
│ Placement: (laisser défaut)                                 │
│                                                             │
│ Image: Ubuntu 22.04 LTS (ou 24.04 LTS)                     │
│                                                             │
│ Shape:                                                      │
│   ☐ Specialty and legacy                                    │
│   ☑ Ampere (ARM) → VM.Standard.A1.Flex                     │
│   → OCPUs: 4  (max du free tier)                           │
│   → Memory: 24 GB  (max du free tier)                      │
│                                                             │
│ Networking: (laisser défaut)                                │
│   → Assign public IPv4 address: ☑                           │
│                                                             │
│ Add SSH keys:                                               │
│   ☑ Generate a key pair → Download private key              │
│   (ou coller votre clé publique existante)                  │
│                                                             │
│ Boot volume: 200 GB (default)                               │
│                                                             │
│ └─ [Create]                                                 │
└─────────────────────────────────────────────────────────────┘
```

**La VM démarre en ~30 secondes.**

## Étape 3 : Connexion SSH

```bash
# Se placer dans le dossier de la clé téléchargée
chmod 600 ~/Downloads/ssh-key-2026-08-19.key
ssh -i ~/Downloads/ssh-key-2026-08-19.key ubuntu@<IP_PUBLIQUE_ORACLE>
```

> **⚠️ Important** : Notez l'IP publique. Elle servira UNIQUEMENT pour le SSH initial. 
> Après installation du tunnel, elle sera désactivée.

## Étape 4 : Installer les dépendances

```bash
# Copier-coller d'un seul bloc sur le VPS :
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
  python3 python3-pip python3-venv python3-full \
  git ffmpeg \
  build-essential gcc \
  curl wget net-tools \
  ufw

# Python packages
pip3 install --user flask flask-cors numpy pillow requests

# Vérifier Python
python3 --version
pip3 --version
```

## Étape 5 : Cloner le projet

```bash
# Sur votre machine locale, créer une archive du projet
cd "E:/SAAS - Copie/engine"
tar czf /tmp/ka-mobile.tar.gz \
  ka_launcher.py ka_server/ ka_mobile_compress.py \
  ka_background_compress.py ka_mobile_media/ \
  hcv2_video_pipeline.py hcv2_modal_codec.py \
  vital-ka/core/python/hcv2_modal_codec.py \
  vital-ka/core/python/hcv2_video_pipeline.py \
  ka_server/ ka_config.py \
  ka-mobile-android/www/ka_index.html \
  thu/ \
  requirements.txt

# Copier sur le VPS
scp -i ~/Downloads/ssh-key-2026-08-19.key \
  /tmp/ka-mobile.tar.gz \
  ubuntu@<IP_ORACLE>:/home/ubuntu/
```

**Alternative** : si git est configuré, cloner directement :

```bash
# Sur le VPS
cd ~
git clone <votre-repo> ka-mobile
cd ka-mobile
```

## Étape 6 : Installer cloudflared (Tunnel)

```bash
# Sur le VPS
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/

# Vérifier
cloudflared --version
```

## Étape 7 : Configurer le tunnel Cloudflare

**Sur votre machine locale** (où vous êtes connecté à Cloudflare) :

```bash
# 1. Aller sur https://dash.cloudflare.com/
# 2. Menu → Zero Trust → Access → Tunnels
# 3. "Create a tunnel"
# 4. Nom : "ka-mobile"
# 5. Choisir "cloudflared" → "Next"
```

**Sur le VPS** :

```bash
# Copier la commande de connexion depuis l'interface Cloudflare
# Elle ressemble à :
cloudflared tunnel login  # → suivre le lien, autoriser

# Créer le tunnel
cloudflared tunnel create ka-mobile

# Configurer : créer ~/.cloudflared/config.yml
cat > ~/.cloudflared/config.yml << 'EOF'
tunnel: <ID_DU_TUNNEL>
credentials-file: /home/ubuntu/.cloudflared/<ID_DU_TUNNEL>.json

ingress:
  - hostname: api.kamobile.ai
    service: http://localhost:8765
  - hostname: kamobile.ai
    service: http://localhost:8765
  - hostname: "*.kamobile.ai"
    service: http://localhost:8765
  - service: http_status:404
EOF
```

**Dans l'interface Cloudflare (Zero Trust → Tunnels)** :
- Route : `api.kamobile.ai` → tunnel `ka-mobile`
- Route : `kamobile.ai` → tunnel `ka-mobile`

**DNS Cloudflare** (tableau de bord → DNS) :
```
kamobile.ai  CNAME  <tunnel-id>.cfargotunnel.com  Proxied (orange)
api.kamobile.ai  CNAME  <tunnel-id>.cfargotunnel.com  Proxied (orange)
```

## Étape 8 : Lancer le serveur

```bash
# Sur le VPS
cd ~/ka-mobile

# Démarrer le serveur KA MOBILE
nohup python3 ka_launcher.py --product mobile > ~/ka_server.log 2>&1 &

# Vérifier qu'il tourne
sleep 3
curl http://localhost:8765/api/health
# → {"service":"ka-server","status":"healthy","version":"4.0.0"}

# Démarrer le tunnel Cloudflare
cloudflared tunnel run ka-mobile &
```

## Étape 9 : Désactiver l'IP publique (sécurité)

```bash
# Une fois le tunnel fonctionnel, désactiver l'accès direct
# → Console Oracle : Instance → Attached VNICs → Edit → 
#   ☐ Assign public IPv4 address → DÉCOCHER

# → OU avec le CLI OCI :
# oci compute instance update --public-ip-flag NONE --instance-id <id>
```

**Désormais, le VPS est invisible.** 
- ❌ Pas d'IP publique
- ❌ Pas de ports ouverts
- ✅ Seul le tunnel Cloudflare peut y accéder
- ✅ SSH possible via Cloudflare Access (Zero Trust) ou en réactivant temporairement l'IP

## Étape 10 : Vérifier le déploiement

```bash
# Depuis n'importe où (test via Cloudflare)
curl https://kamobile.ai/api/health
# → {"status": "healthy"}

curl https://api.kamobile.ai/api/hcv2/stats
# → {"files_count": 0, ...}

# Test de compression
curl -X POST https://api.kamobile.ai/api/hcv2/mobile \
  -F "file=@test.jpg"
# → {"format": "HCVM+Mobile", "psnr": "35.3", "ratio": "393.9", ...}
```

## Dépannage

| Problème | Solution |
|---|---|
| `cloudflared: command not found` | `sudo mv cloudflared /usr/local/bin/` |
| Tunnel refuse de se connecter | Vérifier `~/.cloudflared/config.yml` et le tunnel ID |
| Le serveur ne répond pas en local | `curl http://localhost:8765` — vérifier `ka_server.log` |
| Port déjà utilisé | `killall python3` puis relancer |
| Pas assez de mémoire | Réduire à 2 OCPU + 12 Go via Oracle console |
| Redémarrage du VPS | Ajouter au crontab : `@reboot cd ~/ka-mobile && nohup python3 ka_launcher.py &` |

---

> **Résumé :** 10 étapes, 15 minutes. Une fois le tunnel actif, le VPS est invisible sur Internet. 
> Le HCV2 tourne sur 4 cœurs ARM, 24 Go RAM, 200 Go SSD — **gratuit pour toujours.**