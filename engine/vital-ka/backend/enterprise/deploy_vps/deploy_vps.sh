#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# deploy_vps.sh — Installation de KA Enterprise sur un VPS (Ubuntu 22.04+)
#
#   bash deploy_vps.sh
#
# Construit l'image Docker, démarre le conteneur sur le port 8767 et monte
# le volume persistant ~/ka-enterprise-data (tenants, hologrammes, clés API,
# audit — rien n'est perdu au redémarrage ni à la mise à jour).
# ═══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

# ── Chemins : ce script est dans deploy_vps/, la racine est le dossier parent ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENTERPRISE_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$HOME/ka-enterprise-data"
CONTAINER="ka-enterprise"
PORT="${PORT:-8767}"

echo "════════════════════════════════════════════════════════"
echo "  🏢 KA Enterprise — Déploiement VPS"
echo "════════════════════════════════════════════════════════"
echo "  Dossier code  : $ENTERPRISE_DIR"
echo "  Données       : $DATA_DIR (volume persistant)"
echo "  Port          : $PORT"

# ── Prérequis ────────────────────────────────────────────────────────────────
if ! command -v docker >/dev/null 2>&1; then
  echo ""
  echo "❌ Docker n'est pas installé. Installez-le d'abord :"
  echo "   curl -fsSL https://get.docker.com | sh"
  echo "   sudo usermod -aG docker \$USER   (puis reconnectez-vous)"
  exit 1
fi

mkdir -p "$DATA_DIR"

# ── Build de l'image ─────────────────────────────────────────────────────────
echo ""
echo "🐳 Construction de l'image (python:3.11-slim + numpy + flask)…"
cd "$ENTERPRISE_DIR"
docker build -f deploy_vps/Dockerfile -t ka-enterprise:latest .

# ── Démarrage ────────────────────────────────────────────────────────────────
echo ""
echo "▶ Démarrage du conteneur « $CONTAINER »…"

# Arrêt d'un ancien conteneur éventuel (mise à jour)
if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "   Mise à jour : arrêt de l'ancien conteneur…"
  docker rm -f "$CONTAINER" >/dev/null
fi

docker run -d \
  --name "$CONTAINER" \
  --restart unless-stopped \
  -p "$PORT:8767" \
  -v "$DATA_DIR:/app/data" \
  ka-enterprise:latest

# ── Vérification ─────────────────────────────────────────────────────────────
echo ""
echo "⏳ Attente du démarrage…"
for i in $(seq 1 30); do
  if curl -sf "http://127.0.0.1:$PORT/api/enterprise/info" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo ""
echo "════════════════════════════════════════════════════════"
echo "  ✅ KA Enterprise est en ligne !"
echo "════════════════════════════════════════════════════════"
IP=$(curl -s ifconfig.me 2>/dev/null || echo "VOTRE_IP")
echo "  Portail onboarding : http://$IP:$PORT/onboard"
echo "  Dashboard admin    : http://$IP:$PORT/admin"
echo "  API Docs           : http://$IP:$PORT/docs"
echo ""
echo "  🔑 Clé API : créée au premier onboarding (portail /onboard)."
echo "  💾 Données : $DATA_DIR — sauvegardez ce dossier."
echo ""
echo "  📖 Ouverture du port (pare-feu) :"
echo "     sudo ufw allow $PORT/tcp"
echo ""
echo "  📊 Logs : docker logs -f ka-enterprise"
echo "  ⏹ Arrêt : docker stop ka-enterprise"
