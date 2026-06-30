#!/bin/bash
# Déploiement KA — Frontend Vercel + Backend Render
# Usage: bash deploy.sh

set -e

echo "============================================"
echo "  DÉPLOIEMENT KA — Harmonic AI + HCV"
echo "============================================"

# ── 1. FRONTEND (Vercel) ──────────────────────
echo ""
echo "[1/2] Déploiement Frontend sur Vercel..."
cd ../ka-web-complete/ka-web-complete

if command -v vercel &> /dev/null; then
    echo "  Vercel CLI détecté. Lancement du déploiement..."
    vercel --prod --confirm
    echo "  ✅ Frontend déployé sur Vercel"
else
    echo "  ⚠️  Vercel CLI non installé."
    echo "  Installation: npm i -g vercel"
    echo "  Puis: cd ka-web-complete/ka-web-complete && vercel --prod"
fi

# ── 2. BACKEND (Render) ──────────────────────
echo ""
echo "[2/2] Backend — déploiement Render"
echo ""
echo "  Le backend se déploie automatiquement via Git :"
echo "  1. Va sur https://dashboard.render.com"
echo "  2. New + → Web Service → Connecte kotto/harmonic"
echo "  3. Root Directory: engine"
echo "  4. Build Command: pip install -r requirements_server.txt"
echo "  5. Start Command: gunicorn ka_server:app --bind 0.0.0.0:\$PORT --workers 2 --timeout 120"
echo "  6. Create Web Service"
echo ""
echo "  Ou déploie via l'API Render (si RENDER_API_KEY est définie) :"

if [ -n "$RENDER_API_KEY" ]; then
    curl -X POST "https://api.render.com/v1/services" \
      -H "Authorization: Bearer $RENDER_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "type": "web_service",
        "name": "ka-api",
        "ownerId": "'${RENDER_OWNER_ID:-}'",
        "repo": "https://github.com/kotto/harmonic",
        "branch": "main",
        "rootDir": "engine",
        "buildCommand": "pip install -r requirements_server.txt",
        "startCommand": "gunicorn ka_server:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120",
        "plan": "starter"
      }'
    echo "  ✅ Backend déployé sur Render"
else
    echo "  ⚠️  RENDER_API_KEY non définie — déploiement manuel requis"
fi

# ── 3. VÉRIFICATION ─────────────────────────
echo ""
echo "============================================"
echo "  VÉRIFICATION"
echo "============================================"
echo ""
echo "  Frontend : https://ka-app.vercel.app"
echo "  Backend  : https://ka-api.onrender.com"
echo ""
echo "  Test : curl https://ka-api.onrender.com/api/health"
echo "============================================"
