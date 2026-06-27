# KA Phone — Déploiement Hetzner VPS + Cloudflare Tunnel

## Architecture de sécurité

```
Ton téléphone → Cloudflare Edge (HTTPS, DDoS protection, WAF)
                         ↓
              Cloudflare Tunnel (chiffré, pas de port ouvert)
                         ↓
              Hetzner VPS (Docker container isolé)
                         ↓
              KA Phone (port 8420, localhost uniquement)
```

**Le VPS n'a AUCUN port ouvert sur Internet.** Seul Cloudflare peut accéder au serveur via le tunnel chiffré. Le VPS est invisible — impossible à scanner, impossible à attaquer directement.

## Prérequis

| Élément | Coût | Description |
|---|---|---|
| **Hetzner VPS CX32** | ~8€/mois | 4 vCPU, **8 Go RAM**, 80 Go SSD, Ubuntu 22.04 |
| **Domaine** | ~10€/an | Ex: kaphone.fr (OVH, Gandi, Namecheap...) |
| **Cloudflare** | Gratuit | Plan Free, protection DDoS incluse |

> **Pourquoi CX32 (8 Go) plutôt que CX22 (4 Go) ?**  
> Le LLM Phi-3-mini (modèle local 3.8B) nécessite ~3.7 Go de RAM pour le chargement.  
> Avec 4 Go, l'OS + Docker + Python consomment déjà ~1 Go, laissant seulement ~0.6 Go pour le LLM — insuffisant.  
> Avec 8 Go, il reste ~4 Go de marge après chargement du LLM, permettant de faire tourner confortablement tous les modules KA Phone.

## Étape 1 : Créer le VPS Hetzner

1. Va sur [hetzner.com/cloud](https://www.hetzner.com/cloud)
2. Crée un compte, ajoute ~10€ de crédit
3. Crée un serveur **CX32** (4 vCPU, 8 Go, 80 Go)
4. Choisis **Ubuntu 22.04**
5. Ajoute ta clé SSH publique
6. Note l'IP du serveur (ex: `49.12.XX.XX`)

## Étape 2 : Configurer le domaine sur Cloudflare

1. Crée un compte sur [cloudflare.com](https://dash.cloudflare.com)
2. Ajoute ton domaine (ex: `kaphone.fr`)
3. Cloudflare te donne 2 nameservers → configure-les chez ton registrar
4. Attends la propagation DNS (~5-30 minutes)

## Étape 3 : Se connecter au VPS

```bash
ssh root@49.12.XX.XX
```

Mettre à jour le système :
```bash
apt update && apt upgrade -y
```

## Étape 4 : Installer Docker

```bash
curl -fsSL https://get.docker.com | sh
usermod -aG docker $USER
# Re-login ou taper: newgrp docker
```

## Étape 5 : Installer Cloudflare Tunnel

```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
dpkg -i cloudflared-linux-amd64.deb
```

Authentifier Cloudflare :
```bash
cloudflared tunnel login
# → Ouvre le lien dans ton navigateur, autorise ton domaine
```

Créer le tunnel :
```bash
cloudflared tunnel create kaphone
# → Note le Tunnel ID (ex: abc123-def456-ghi789)
```

Configurer le DNS :
```bash
cloudflared tunnel route dns kaphone kaphone.kaphone.fr
# Remplace par ton sous-domaine
```

Copier les credentials :
```bash
cp ~/.cloudflared/*.json /root/
# Tu en auras besoin pour le fichier config.yml
```

## Étape 6 : Transférer le code sur le VPS

Depuis ton PC :
```bash
cd e:\SAAS - Copie
# Transférer les dossiers nécessaires via SCP :
scp -r ka_phone/ root@49.12.XX.XX:/root/
```

> **Note :** Le modèle GGUF (2.4 Go) sera téléchargé directement sur le VPS après déploiement
> via `python models/download_llama_binary.py` ou manuellement depuis HuggingFace.

## Étape 7 : Configurer les fichiers de déploiement

Sur le VPS, édite le fichier de config Cloudflare :

```bash
cd /root/ka_phone
nano cloudflared/config.yml
```

Remplace :
- `YOUR_TUNNEL_ID_HERE` → ton Tunnel ID
- `kaphone.yourdomain.com` → ton domaine réel

Copie le fichier de credentials :
```bash
cp /root/*.json cloudflared/
```

## Étape 8 : Télécharger le modèle LLM

```bash
cd /root/ka_phone/models
python -c "
from huggingface_hub import hf_hub_download
hf_hub_download('bartowski/Phi-3-mini-4k-instruct-GGUF', 'Phi-3-mini-4k-instruct-Q4_K_M.gguf', local_dir='.', resume_download=True)
"
```

## Étape 9 : Déployer

```bash
cd /root/ka_phone
chmod +x deploy.sh
./deploy.sh kaphone.kaphone.fr
```

Le script va :
1. Vérifier Docker
2. Build l'image
3. Démarrer KA Phone + Cloudflare Tunnel
4. Vérifier que tout fonctionne

## Étape 10 : Vérifier

Ouvre `https://kaphone.kaphone.fr` dans ton navigateur (ou sur ton téléphone).

Tu devrais voir l'écran de verrouillage avec la sphère neurale.

## Maintenance

```bash
# Voir les logs
docker compose logs -f

# Redémarrer
docker compose restart

# Mettre à jour l'application
cd /root/ka_phone
git pull  # ou rescp les fichiers
docker compose up -d --build

# Arrêter
docker compose down
```

## Coût total

| Service | Coût mensuel |
|---|---|
| Hetzner CX32 (8 Go) | ~8€ |
| Cloudflare | Gratuit |
| Domaine | ~1€/mois |
| **Total** | **~9€/mois** |

---

## Sécurité

- **Aucun port ouvert** sur le VPS (port 8420 bindé sur `127.0.0.1` uniquement)
- **Cloudflare** bloque les attaques DDoS, les bots, les scans de ports
- **HTTPS** automatique via Cloudflare (certificat SSL gratuit)
- **Données persistantes** dans un volume Docker (`kaphone_data`)
- **Isolation** : chaque service dans son container Docker
- **Pas d'accès SSH externe** si tu utilises le firewall Hetzner pour restreindre à ton IP

## Résumé rapide (copier-coller pour installation)

```bash
# 1. Créer VPS Hetzner CX32 Ubuntu 22.04
# 2. Configurer domaine sur Cloudflare
# 3. SSH into VPS:
curl -fsSL https://get.docker.com | sh
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
dpkg -i cloudflared-linux-amd64.deb
cloudflared tunnel login
cloudflared tunnel create kaphone
cloudflared tunnel route dns kaphone kaphone.YOURDOMAIN.com
cp ~/.cloudflared/*.json ~/
# 4. Copier le code sur le VPS:
#    scp -r ka_phone/ root@IP:/root/
# 5. Télécharger le modèle LLM:
#    cd /root/ka_phone/models && python -c "from huggingface_hub import hf_hub_download; ..."
# 6. Configurer cloudflared/config.yml avec le Tunnel ID
# 7. Lancer:
cd /root/ka_phone && chmod +x deploy.sh && ./deploy.sh kaphone.YOURDOMAIN.com
```

---

*Documentation mise à jour — 9 Juin 2026 — Projet KA Phone*

## Architecture des composants sur le VPS

```
/root/ka_phone/
├── models/
│   └── phi-3-mini-4k-instruct-q4_k_m.gguf   (2.4 Go, monté en volume Docker)
├── unified_server.py                          (serveur canonique, port 8420)
├── phi3_creative_bridge.py                    (bridge LLM créatif)
├── docker-compose.yml                         (kaphone + cloudflared)
├── deploy.sh                                  (script de déploiement)
└── cloudflared/config.yml                     (config Cloudflare Tunnel)
```

**Consommation RAM estimée (CX32, 8 Go) :**
- OS Ubuntu + Docker : ~600 Mo
- Python + unified_server : ~300 Mo
- Phi-3-mini (chargé) : ~3.7 Go
- Marge disponible : ~3.4 Go