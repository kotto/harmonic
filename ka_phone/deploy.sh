#!/bin/bash
# ============================================================================
# KA Phone — Deployment Script for Hetzner VPS + Cloudflare Tunnel
# ============================================================================
# Usage: ./deploy.sh [domain]
# Example: ./deploy.sh kaphone.example.com
#
# PREREQUISITES:
# 1. Hetzner VPS with Ubuntu 22.04 (CX22 ~4€/month)
# 2. Docker & Docker Compose installed
# 3. Cloudflare account with domain configured
# 4. Cloudflare Tunnel created (cloudflared tunnel create kaphone)
# ============================================================================

set -e  # Exit on error

DOMAIN="${1:-kaphone.local}"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  KA Phone — Production Deployment${NC}"
echo -e "${GREEN}  Domain: ${DOMAIN}${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# ---- STEP 1: Check prerequisites ----
echo -e "${YELLOW}[1/6] Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Installing...${NC}"
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Installing...${NC}"
    sudo apt-get update && sudo apt-get install -y docker-compose-plugin
fi

echo -e "${GREEN}  Docker: $(docker --version 2>/dev/null || echo 'OK')${NC}"
echo -e "${GREEN}  Docker Compose: $(docker compose version 2>/dev/null || echo 'OK')${NC}"
echo ""

# ---- STEP 2: Stop existing containers ----
echo -e "${YELLOW}[2/6] Stopping existing containers...${NC}"
docker compose down 2>/dev/null || true
echo ""

# ---- STEP 3: Build the Docker image ----
echo -e "${YELLOW}[3/6] Building Docker image...${NC}"
docker compose build --no-cache
echo ""

# ---- STEP 4: Start services ----
echo -e "${YELLOW}[4/6] Starting services...${NC}"
docker compose up -d
echo ""

# ---- STEP 5: Wait for health check ----
echo -e "${YELLOW}[5/6] Waiting for KA Phone to be ready...${NC}"
for i in $(seq 1 30); do
    if curl -s -o /dev/null http://localhost:8420; then
        echo -e "${GREEN}  KA Phone is ready! (port 8420)${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}  Timeout waiting for KA Phone to start. Check logs with: docker compose logs kaphone${NC}"
        exit 1
    fi
    echo -n "."
    sleep 2
done
echo ""

# ---- STEP 6: Verify deployment ----
echo -e "${YELLOW}[6/6] Verifying deployment...${NC}"

# Test health endpoint
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8420/)
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}  App is serving (HTTP $HTTP_CODE)${NC}"
else
    echo -e "${RED}  App returned HTTP $HTTP_CODE. Check logs.${NC}"
fi

# Test API (canonical endpoint: /api/ask)
API_RESPONSE=$(curl -s -X POST http://localhost:8420/api/ask \
    -H "Content-Type: application/json" \
    -d '{"prompt":"qui es tu?"}' 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('source','?'))" 2>/dev/null || echo "?")
echo -e "${GREEN}  API test: source=$API_RESPONSE (endpoint /api/ask)${NC}"

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "  App URL:     ${GREEN}https://${DOMAIN}${NC}"
echo -e "  Local:       http://localhost:8420 (serveur canonique: unified_server.py)"
echo -e "  Logs:        docker compose logs -f"
echo -e "  Restart:     docker compose restart"
echo -e "  Stop:        docker compose down"
echo ""
echo -e "${YELLOW}  Next steps:${NC}"
echo -e "  1. Configure Cloudflare Tunnel if not done:"
echo -e "     cloudflared tunnel login"
echo -e "     cloudflared tunnel create kaphone"
echo -e "     cloudflared tunnel route dns kaphone ${DOMAIN}"
echo -e "     cp ~/.cloudflared/*.json cloudflared/"
echo -e "     Update cloudflared/config.yml with your tunnel ID"
echo -e "     docker compose restart cloudflared"
echo -e ""
echo -e "  2. Or use a direct domain if you skipped Cloudflare:"
echo -e "     Change docker-compose.yml port mapping from '127.0.0.1:8420:8420' to '8420:8420'"
echo -e "     docker compose up -d"
echo ""