# 🚀 KA Phone — Déploiement Pas à Pas sur Hetzner

> **Prérequis :** Un compte [Hetzner Cloud](https://www.hetzner.com/cloud), un domaine (ex: `kaphone.fr`), un compte [Cloudflare](https://dash.cloudflare.com).

**Coût total : ~9€/mois | Durée : ~15 minutes**

---

## ÉTAPE 1 — Créer le VPS Hetzner (CX32, 8 Go)

1. Va sur https://console.hetzner.cloud
2. Clique **"Create Server"** (ou "Add Server")
3. Choisis :
   - **Location :** Nürnberg ou Falkenstein (le moins cher)
   - **Image :** Ubuntu 22.04
   - **Type :** CX32 (4 vCPU, 8 Go RAM, 80 Go SSD) — **~8€/mois**
   - **SSH Key :** ajoute ta clé publique
4. Clique **"Create & Buy Now"**
5. Note l'**IPv4** du serveur (ex: `49.12.34.56`)

---

## ÉTAPE 2 — Configurer le domaine sur Cloudflare

1. Va sur https://dash.cloudflare.com → ajoute ton domaine (`kaphone.fr`)
2. Cloudflare te donne **2 nameservers** (ex: `alice.ns.cloudflare.com`, `bob.ns.cloudflare.com`)
3. Sur le site de ton registrar (OVH, Gandi...), remplace les nameservers par ceux de Cloudflare
4. Attends 5-15 min que la propagation DNS se fasse

---

## ÉTAPE 3 — Se connecter au VPS et préparer le système

```bash
ssh root@49.12.34.56
```

Une fois connecté :
```bash
apt update && apt upgrade -y
```

---

## ÉTAPE 4 — Installer Docker

```bash
curl -fsSL https://get.docker.com | sh
```

Puis active Docker au démarrage :
```bash
systemctl enable docker
```

---

## ÉTAPE 5 — Installer et configurer Cloudflare Tunnel

```bash
# 1. Télécharger le client Cloudflare Tunnel
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
dpkg -i cloudflared-linux-amd64.deb

# 2. Authentifier (ouvre le lien dans ton navigateur)
cloudflared tunnel login

# 3. Créer le tunnel
cloudflared tunnel create kaphone
# Note le Tunnel ID affiché (ex: abc123-456-def)

# 4. Pointer le DNS vers le tunnel
cloudflared tunnel route dns kaphone kaphone.TONDOMAINE.fr
```

---

## ÉTAPE 6 — Transférer le code sur le VPS

Depuis ton PC Windows :
```bash
cd "e:\SAAS - Copie"
scp -r ka_phone root@49.12.34.56:/root/
```

---

## ÉTAPE 7 — Configurer le tunnel Cloudflare sur le VPS

Sur le VPS :
```bash
cd /root/ka_phone

# Copier les credentials
cp /root/.cloudflared/*.json cloudflared/

# Éditer la config
nano cloudflared/config.yml
```

Dans `cloudflared/config.yml`, remplace :
- `YOUR_TUNNEL_ID_HERE` → le Tunnel ID (ex: `abc123-456-def`)
- `kaphone.yourdomain.com` → ton domaine réel (ex: `kaphone.kaphone.fr`)

Sauvegarde : `Ctrl+O`, Entrée, puis `Ctrl+X`

---

## ÉTAPE 8 — Télécharger le modèle LLM Phi-3-mini

```bash
cd /root/ka_phone/models
pip install huggingface_hub -q

python3 << 'EOF'
from huggingface_hub import hf_hub_download
hf_hub_download(
    "bartowski/Phi-3-mini-4k-instruct-GGUF",
    "Phi-3-mini-4k-instruct-Q4_K_M.gguf",
    local_dir=".",
    resume_download=True
)
print("✅ Modele telecharge")
EOF
```

Ce téléchargement prend **~5-10 minutes** (2.4 Go). Laisse tourner.

---

## ÉTAPE 9 — Déployer l'application

```bash
cd /root/ka_phone
chmod +x deploy.sh
./deploy.sh kaphone.TONDOMAINE.fr
```

Le script va :
1. Vérifier Docker → OK
2. Build l'image (2-3 minutes)
3. Démarrer les containers
4. Vérifier que tout fonctionne

---

## ÉTAPE 10 — Vérifier

Ouvre dans ton navigateur (ou téléphone) :

```
https://kaphone.TONDOMAINE.fr
```

Tu dois voir **l'écran de verrouillage avec la sphère neurale animée**.

Pour tester l'API :
```bash
curl -X POST http://localhost:8420/api/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Qui es-tu ?"}'
```

---

## ÉTAPE 11 — Maintenance

```bash
# Voir les logs
docker compose logs -f

# Redémarrer
docker compose restart

# Mettre à jour (après avoir rescpé les fichiers)
docker compose up -d --build

# Arrêter
docker compose down
```

---

## Résumé rapide (copier-coller)

```bash
# 1. VPS: Hetzner CX32, Ubuntu 22.04, 8 Go RAM
# 2. Domaine: pointer les nameservers vers Cloudflare
# 3. SSH sur le VPS, puis:
apt update && apt upgrade -y
curl -fsSL https://get.docker.com | sh
systemctl enable docker
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
dpkg -i cloudflared-linux-amd64.deb
cloudflared tunnel login
cloudflared tunnel create kaphone
cloudflared tunnel route dns kaphone kaphone.TONDOMAINE.fr
# 4. Depuis le PC: scp -r ka_phone root@IP:/root/
# 5. Sur le VPS:
cd /root/ka_phone
cp ~/.cloudflared/*.json cloudflared/
nano cloudflared/config.yml  # Mettre le Tunnel ID et le domaine
# 6. Modele:
cd models && pip install huggingface_hub -q
python3 -c "from huggingface_hub import hf_hub_download; hf_hub_download('bartowski/Phi-3-mini-4k-instruct-GGUF', 'Phi-3-mini-4k-instruct-Q4_K_M.gguf', local_dir='
.', resume_download=True)"
# 7. Deploiement:
cd /root/ka_phone && chmod +x deploy.sh && ./deploy.sh kaphone.TONDOMAINE.fr
# 8. Ouvrir: https://kaphone.TONDOMAINE.fr
```

---

## Ce qui est inclus

| Composant | Détail |
|-----------|--------|
| **Serveur** | unified_server.py (~30 modules) |
| **LLM créatif** | Phi-3-mini 3.8B (génération poèmes, histoires, conversation) |
| **Fallback** | Templates purs (0% hallucination) si LLM indisponible |
| **Anti-hallucination** | Vérification post-génération + MaatGuard éthique |
| **Faits/Maths** | QuickFacts (1000+ faits, <1ms) + ParametricKB (50+ règles) |
| **Sécurité** | Cloudflare Tunnel, 0 port ouvert, HTTPS automatique |
| **Persistance** | Volume Docker pour les données utilisateur |
| **UI** | PWA responsive, lockscreen animé, thème OLED dark |

---

*Guide généré le 9 Juin 2026 — Projet KA Phone*