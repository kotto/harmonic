#!/bin/bash
# Script de build pour Vercel

set -e

echo "=== Build HCV PRO ==="

# Installer les dépendances
echo "Installation des dépendances..."
pip install -r requirements.txt

# Minifier le frontend
echo "Minification du frontend..."
node minify.js

# Créer le dossier static si nécessaire
mkdir -p web/static

echo "Build terminé!"
