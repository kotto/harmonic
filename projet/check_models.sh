#!/bin/bash
echo "=== MÉMOIRE ==="
free -h
echo ""
echo "=== DISQUE ==="
df -h /
echo ""
echo "=== PROCESSUS PYTHON ==="
ps aux | grep python | grep -v grep
echo ""
echo "=== FICHIERS MODÈLES ==="
ls -la /opt/connective-ai/ | grep -E "(model|weight|bin)" || echo "Aucun fichier modèle trouvé"
echo ""
echo "=== TAILLE RÉPERTOIRE ==="
du -sh /opt/connective-ai/
