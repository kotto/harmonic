#!/bin/bash
echo "🌊 HCS V2 - Démarrage Automatique"
echo "=================================="
cd "$(dirname "$0")"

echo "🚀 Démarrage du script automatique..."
python3 start_server.py
