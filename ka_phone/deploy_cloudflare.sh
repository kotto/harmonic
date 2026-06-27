#!/bin/bash
# =============================================================================
# KA PHONE — Cloudflare Tunnel Deployment
# =============================================================================
# Expose KA Phone securely via Cloudflare Tunnel (zero open ports).
# 
# Prerequisites:
#   1. cloudflared installed: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
#   2. A Cloudflare account (free tier)
#   3. A domain managed by Cloudflare (or use trycloudflare.com for testing)
#
# Usage:
#   bash deploy_cloudflare.sh              # Interactive setup
#   bash deploy_cloudflare.sh --quick      # Quick test tunnel (trycloudflare.com)
#   bash deploy_cloudflare.sh --install    # Install cloudflared
# =============================================================================

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
KA_PORT=8080

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=======================================================${NC}"
echo -e "${GREEN}  KA PHONE — Cloudflare Tunnel Deployment${NC}"
echo -e "${GREEN}=======================================================${NC}"

# ────────────────────────────────────────────────
# 1. Check/Install cloudflared
# ────────────────────────────────────────────────
install_cloudflared() {
    echo -e "\n${YELLOW}[1/4] Installing cloudflared...${NC}"
    
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    
    if [ "$ARCH" = "x86_64" ]; then ARCH="amd64"; fi
    if [ "$ARCH" = "aarch64" ]; then ARCH="arm64"; fi
    
    CLOUDFLARED_VERSION="2024.2.1"
    URL="https://github.com/cloudflare/cloudflared/releases/download/${CLOUDFLARED_VERSION}/cloudflared-${OS}-${ARCH}"
    
    if [ "$OS" = "linux" ]; then
        curl -L "$URL" -o /tmp/cloudflared
        chmod +x /tmp/cloudflared
        sudo mv /tmp/cloudflared /usr/local/bin/cloudflared
    elif [ "$OS" = "darwin" ]; then
        brew install cloudflare/cloudflare/cloudflared 2>/dev/null || {
            curl -L "$URL" -o /tmp/cloudflared
            chmod +x /tmp/cloudflared
            sudo mv /tmp/cloudflared /usr/local/bin/cloudflared
        }
    else
        echo -e "${RED}Unsupported OS. Download manually from:${NC}"
        echo "  https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
        exit 1
    fi
    
    echo -e "${GREEN}  cloudflared installed: $(cloudflared version 2>/dev/null || echo 'OK')${NC}"
}

# ────────────────────────────────────────────────
# 2. Start KA Phone server
# ────────────────────────────────────────────────
start_ka_phone() {
    echo -e "\n${YELLOW}[2/4] Starting KA Phone server...${NC}"
    
    cd "$PROJECT_DIR"
    
    # Check if already running
    if pgrep -f "unified_server.py" > /dev/null 2>&1; then
        echo -e "${GREEN}  KA Phone server already running${NC}"
        return
    fi
    
    # Start server in background
    python unified_server.py &
    KA_PID=$!
    sleep 2
    
    if kill -0 $KA_PID 2>/dev/null; then
        echo -e "${GREEN}  KA Phone server started (PID: $KA_PID)${NC}"
    else
        echo -e "${RED}  Failed to start KA Phone server${NC}"
        exit 1
    fi
}

# ────────────────────────────────────────────────
# 3. Configure Cloudflare Tunnel
# ────────────────────────────────────────────────
setup_tunnel() {
    echo -e "\n${YELLOW}[3/4] Configuring Cloudflare Tunnel...${NC}"
    
    # Quick test tunnel (no domain needed)
    if [ "$QUICK_MODE" = "true" ]; then
        echo -e "${YELLOW}  Using trycloudflare.com quick tunnel (no domain needed)${NC}"
        echo -e "${YELLOW}  URL will be displayed below...${NC}"
        echo ""
        
        # Run tunnel in foreground
        cloudflared tunnel --url "http://localhost:${KA_PORT}" \
            --no-autoupdate \
            2>&1 | tee /tmp/cloudflared.log &
        TUNNEL_PID=$!
        
        sleep 3
        # Extract the URL
        TUNNEL_URL=$(grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' /tmp/cloudflared.log | head -1)
        
        if [ -n "$TUNNEL_URL" ]; then
            echo ""
            echo -e "${GREEN}=======================================================${NC}"
            echo -e "${GREEN}  KA PHONE IS LIVE!${NC}"
            echo -e "${GREEN}  URL: ${TUNNEL_URL}${NC}"
            echo -e "${GREEN}=======================================================${NC}"
            echo ""
            echo "  Press Ctrl+C to stop"
            wait $TUNNEL_PID
        else
            echo -e "${RED}  Failed to get tunnel URL. Check /tmp/cloudflared.log${NC}"
            exit 1
        fi
        exit 0
    fi
    
    # Permanent tunnel (requires domain)
    TUNNEL_NAME="ka-phone-$(date +%s)"
    
    # Login (requires browser)
    echo -e "${YELLOW}  Opening browser for Cloudflare login...${NC}"
    cloudflared tunnel login
    
    # Create tunnel
    cloudflared tunnel create "$TUNNEL_NAME"
    
    # Get tunnel ID
    TUNNEL_ID=$(cloudflared tunnel list --output json | python3 -c "import sys,json;d=json.load(sys.stdin);print([t['id'] for t in d if t['name']=='$TUNNEL_NAME'][0])")
    
    # Create config
    cat > "$HOME/.cloudflared/config.yml" << EOF
tunnel: ${TUNNEL_ID}
credentials-file: ${HOME}/.cloudflared/${TUNNEL_ID}.json

ingress:
  - hostname: ka-phone.your-domain.com
    service: http://localhost:${KA_PORT}
  - service: http_status:404
EOF
    
    echo -e "${GREEN}  Tunnel created: ${TUNNEL_NAME} (ID: ${TUNNEL_ID})${NC}"
    echo ""
    echo -e "${YELLOW}  Next steps:${NC}"
    echo "  1. Point DNS record ka-phone.your-domain.com to Cloudflare"
    echo "  2. Run: cloudflared tunnel route dns ${TUNNEL_NAME} ka-phone.your-domain.com"
    echo "  3. Run: cloudflared tunnel run ${TUNNEL_NAME}"
}

# ────────────────────────────────────────────────
# 4. Test connectivity
# ────────────────────────────────────────────────
test_connectivity() {
    echo -e "\n${YELLOW}[4/4] Testing local server...${NC}"
    
    sleep 1
    if curl -s "http://localhost:${KA_PORT}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}  Local server responding OK${NC}"
    else
        echo -e "${YELLOW}  Local server check skipped (health endpoint may differ)${NC}"
        # Try the main endpoint
        RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${KA_PORT}/" || echo "000")
        if [ "$RESPONSE" != "000" ]; then
            echo -e "${GREEN}  Local server responding (HTTP ${RESPONSE})${NC}"
        fi
    fi
}

# ────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────
QUICK_MODE="false"
INSTALL_MODE="false"

for arg in "$@"; do
    case $arg in
        --quick) QUICK_MODE="true" ;;
        --install) INSTALL_MODE="true" ;;
    esac
done

if [ "$INSTALL_MODE" = "true" ]; then
    install_cloudflared
    echo -e "\n${GREEN}Run: bash deploy_cloudflare.sh --quick${NC}"
    exit 0
fi

# Check cloudflared
if ! command -v cloudflared &> /dev/null; then
    echo -e "${YELLOW}cloudflared not found. Installing...${NC}"
    install_cloudflared
fi

start_ka_phone
test_connectivity
setup_tunnel