#!/usr/bin/env bash
# HCV2 Pro — Déploiement serveur
# Usage: ./deploy.sh [install|start|stop|status|test]

set -e
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=8765
HOST="0.0.0.0"
DICT="$APP_DIR/dictionaries/broadcast.hdb"
PIDFILE="/tmp/hcv2_pro.pid"

case "${1:-status}" in
  install)
    echo "📦 Installation des dépendances..."
    pip install -q flask pillow numpy opencv-python zstandard 2>/dev/null || true
    echo "✅ Dépendances installées"
    ;;
  start)
    if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
      echo "⚠️ Serveur déjà en cours d'exécution (PID $(cat $PIDFILE))"
      exit 1
    fi
    echo "🚀 Démarrage du serveur HCV2 Pro sur $HOST:$PORT..."
    cd "$APP_DIR"
    nohup python multimodal/hcv2_pro.py serve --port $PORT --host $HOST --dict "$DICT" \
      > /tmp/hcv2_pro.log 2>&1 &
    echo $! > "$PIDFILE"
    echo "✅ Serveur démarré (PID $!)"
    ;;
  stop)
    if [ -f "$PIDFILE" ]; then
      kill $(cat "$PIDFILE") 2>/dev/null || true
      rm -f "$PIDFILE"
      echo "⏹️ Serveur arrêté"
    else
      echo "⚠️ Aucun serveur en cours"
    fi
    ;;
  status)
    if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
      echo "✅ Serveur HCV2 Pro actif (PID $(cat $PIDFILE))"
      curl -s http://localhost:$PORT/api/hcv2/status 2>/dev/null || echo "⚠️ API non joignable"
    else
      echo "❌ Serveur HCV2 Pro inactif"
    fi
    ;;
  test)
    echo "🧪 Test du serveur..."
    curl -s http://localhost:$PORT/api/hcv2/status
    echo ""
    echo "🧪 Compression test..."
    curl -s -X POST http://localhost:$PORT/api/hcv2/compress \
      -F "image=@$APP_DIR/COMPRESSION-CAMERA/METHOD_2_SDI_LIKE_IMAGE_COMPRESSION/portrait_photo.png" \
      -F "quality=archive" -o /tmp/hcv2_test_output.hcv2 -w "→ %{http_code} (%{size_download} o)\n"
    echo "🧪 Vérification..."
    python -c "
import sys
sys.path.insert(0, '$APP_DIR')
from multimodal.hcv2_pro import read_header
info = read_header('/tmp/hcv2_test_output.hcv2')
print(f'  Dimensions: {info[\"width\"]}x{info[\"height\"]}')
print(f'  Mode: {info[\"mode\"]}')
print(f'  Ratio: {info[\"ratio\"]}x')
"
    ;;
  *)
    echo "Usage: $0 [install|start|stop|status|test]"
    exit 1
    ;;
esac
