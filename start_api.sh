#!/bin/bash
# Script de démarrage pour Render API
cd "$(dirname "$0")/engine" || exit 1
exec python hcv2_dashboard/app.py