#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# deploy_ka_mobile.sh — Déploiement automatique KA MOBILE sur Oracle Cloud
# ═══════════════════════════════════════════════════════════════════════════════
# Usage : 
#   1. Copier ce script sur le VPS Oracle
#   2. chmod +x deploy_ka_mobile.sh
#   3. ./deploy_ka_mobile.sh
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# ── Couleurs ──
ROUGE='\033[0;31m'
VERT='\033[0;32m'
JAUNE='\033[1;33m'
BLEU='\033[0;34m'
NC='\033[0m'

echo -e "${BLEU}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     KA MOBILE — Déploiement automatique                    ║"
echo "║     Oracle Cloud ARM (4 CPU · 24 Go · 200 Go)              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── Vérification ──
if [ "$(id -u)" != "0" ]; then
    echo -e "${ROUGE}❌ Ce script doit être exécuté en root (sudo su)${NC}"
    exit 1
fi

echo -e "${JAUNE}[1/8] Mise à jour du système...${NC}"
apt update && apt upgrade -y
echo -e "${VERT}  ✓ Système à jour${NC}"

echo -e "${JAUNE}[2/8] Installation des dépendances...${NC}"
apt install -y \
  python3 python3-pip python3-venv \
  git ffmpeg \
  build-essential \
  curl wget net-tools \
  nginx

echo -e "${VERT}  ✓ Dépendances installées${NC}"

echo -e "${JAUNE}[3/8] Installation des packages Python...${NC}"
pip3 install flask flask-cors numpy pillow requests gunicorn
echo -e "${VERT}  ✓ Packages Python installés${NC}"

echo -e "${JAUNE}[4/8] Récupération du projet...${NC}"
cd /root
rm -rf ka-mobile 2>/dev/null || true

# Créer la structure de projet
mkdir -p ka-mobile
cd ka-mobile

# Télécharger l'archive depuis GitHub ou la créer
# *** REMPLACEZ L'URL CI-DESSOUS PAR VOTRE REPO OU UPLOADEZ L'ARCHIVE ***
# Sinon, utilisez SCP depuis votre poste pour copier l'archive :
#   scp -i votre_cle.key ka-mobile.tar.gz ubuntu@<IP>:/root/ka-mobile/
#   cd /root/ka-mobile && tar xzf ka-mobile.tar.gz

echo -e "${JAUNE}"
echo "  ⚠️  LE PROJET N'EST PAS ENCORE COPIÉ"
echo "  Copie l'archive depuis ton poste Windows :"
echo ""
echo "  cd \"E:/SAAS - Copie/engine\""
echo "  tar czf /tmp/ka-mobile.tar.gz \\"
echo "    ka_launcher.py ka_server/ ka_mobile_compress.py \\"
echo "    ka_background_compress.py hcv2_video_pipeline.py \\"
echo "    hcv2_modal_codec.py ka_config.py ka-mobile-android/ \\"
echo "    thu/ requirements.txt"
echo ""
echo "  scp -i ~/Downloads/ma_cle.key \\"
echo "    /tmp/ka-mobile.tar.gz \\"
echo "    root@$(curl -s ifconfig.me):/root/ka-mobile/"
echo ""
echo -e "  Puis relance : cd /root/ka-mobile && tar xzf ka-mobile.tar.gz${NC}"
echo ""

# Vérifier si des fichiers sont déjà présents
if [ -f "ka_launcher.py" ]; then
    echo -e "${VERT}  ✓ Projet détecté${NC}"
else
    echo -e "${ROUGE}  ❌ Projet non trouvé dans /root/ka-mobile/${NC}"
    echo "  Copie l'archive comme indiqué ci-dessus, puis relance ce script."
    echo "  Tu peux aussi ouvrir un deuxième terminal et continuer."
fi

echo -e "${JAUNE}[5/8] Installation de cloudflared (tunnel)...${NC}"
if ! command -v cloudflared &> /dev/null; then
    curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
    chmod +x /usr/local/bin/cloudflared
    echo -e "${VERT}  ✓ cloudflared installé${NC}"
else
    echo -e "${VERT}  ✓ cloudflared déjà présent${NC}"
fi

echo -e "${JAUNE}[6/8] Test du serveur KA MOBILE...${NC}"
if [ -f "ka_launcher.py" ]; then
    # Tuer les anciens processus
    pkill -f "ka_launcher.py" 2>/dev/null || true
    pkill -f "gunicorn" 2>/dev/null || true
    sleep 1

    # Lancer le serveur
    nohup python3 ka_launcher.py --product mobile > /var/log/ka_mobile.log 2>&1 &
    KA_PID=$!
    echo -e "  PID: ${KA_PID}"

    # Attendre le démarrage
    sleep 4

    # Vérifier
    if curl -s http://localhost:8765/api/health > /dev/null 2>&1; then
        echo -e "${VERT}  ✓ KA MOBILE opérationnel sur http://localhost:8765${NC}"
    else
        echo -e "${ROUGE}  ❌ Le serveur n'a pas démarré. Vérifie les logs :${NC}"
        echo "  tail -50 /var/log/ka_mobile.log"
    fi
else
    echo -e "${JAUNE}  ⏳ Serveur non lancé (projet pas encore copié)${NC}"
fi

echo -e "${JAUNE}[7/8] Configuration du service systemd...${NC}"
cat > /etc/systemd/system/ka-mobile.service << 'EOF'
[Unit]
Description=KA MOBILE Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/ka-mobile
ExecStart=/usr/bin/python3 /root/ka-mobile/ka_launcher.py --product mobile
Restart=always
RestartSec=5
StandardOutput=append:/var/log/ka_mobile.log
StandardError=append:/var/log/ka_mobile.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ka-mobile.service 2>/dev/null || true
echo -e "${VERT}  ✓ Service systemd configuré${NC}"

echo -e "${JAUNE}[8/8] Sécurisation...${NC}"
# Désactiver les ports inutiles
ufw default deny incoming 2>/dev/null || true
ufw allow ssh 2>/dev/null || true
echo -e "${VERT}  ✓ Règles de base appliquées${NC}"

echo ""
echo -e "${BLEU}══════════════════════════════════════════════════════════════${NC}"
echo -e "${VERT}  ✅ KA MOBILE — Déploiement terminé !${NC}"
echo -e "${BLEU}══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "  PROCHAINES ÉTAPES :"
echo ""
echo "  📡 1. CONFIGURER LE TUNNEL CLOUDFLARE"
echo "  ─────────────────────────────────────────────"
echo "  Sur ta machine locale, ouvre :"
echo "  https://dash.cloudflare.com/ → Zero Trust → Access → Tunnels"
echo "  Crée un tunnel nommé 'ka-mobile'"
echo ""
echo "  Puis sur le VPS :"
echo "    cloudflared tunnel login"
echo "    cloudflared tunnel create ka-mobile"
echo "    cloudflared tunnel run ka-mobile &"
echo ""
echo "  🛡️  2. DÉSACTIVER L'IP PUBLIQUE (une fois le tunnel OK)"
echo "  ─────────────────────────────────────────────────────────"
echo "  Console Oracle → Instance → VNIC → Edit →"
echo "  Décocher 'Assign public IPv4 address'"
echo ""
echo "  🌐 3. CONFIGURER LE DNS CLOUDFLARE"
echo "  ─────────────────────────────────────────────────────────"
echo "  kamobile.ai  CNAME  <tunnel-id>.cfargotunnel.com"
echo ""
echo "  📋 4. VÉRIFIER LE FONCTIONNEMENT"
echo "  ─────────────────────────────────────────────────────────"
echo "  curl https://kamobile.ai/api/health"
echo "  curl https://kamobile.ai/api/hcv2/mobile -F \"file=@test.jpg\""
echo ""
echo "  📖 5. LOGS"
echo "  ─────────────────────────────────────────────────────────"
echo "  Serveur : tail -f /var/log/ka_mobile.log"
echo "  Service : journalctl -u ka-mobile -f"
echo ""
echo -e "${BLEU}══════════════════════════════════════════════════════════════${NC}"