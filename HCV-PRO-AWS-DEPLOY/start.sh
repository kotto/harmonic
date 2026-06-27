#!/bin/bash
# Script de démarrage HCV-PRO-PROJECT pour Linux/Mac
# Vérifie les dépendances et lance le serveur

echo ""
echo "============================================================"
echo "  HCV PRO - Plateforme de Compression Multimédia"
echo "============================================================"
echo ""

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "[ERREUR] Python 3 n'est pas installé"
    echo "Veuillez installer Python 3.8+ depuis https://www.python.org"
    exit 1
fi

echo "[OK] Python détecté"
python3 --version

# Vérifier si les dépendances sont installées
echo ""
echo "[INFO] Vérification des dépendances..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "[ATTENTION] Les dépendances ne sont pas installées"
    echo "[INFO] Installation des dépendances..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[ERREUR] Impossible d'installer les dépendances"
        exit 1
    fi
fi

echo "[OK] Dépendances vérifiées"

# Lancer le serveur
echo ""
echo "============================================================"
echo "  Démarrage du serveur..."
echo "============================================================"
echo ""
echo "  Interface Web: http://localhost:3000"
echo "  API Health:    http://localhost:3000/api/health"
echo ""
echo "  Appuyez sur Ctrl+C pour arrêter le serveur"
echo "============================================================"
echo ""

python3 server/hcv_pro_server.py
