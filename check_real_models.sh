#!/bin/bash
echo "=== FICHIERS BINAIRES RÉELS ==="
find /opt/connective-ai/models/ -name "*.bin" -o -name "*.safetensors" -o -name "*.pth" | head -5
echo ""
echo "=== TAILLE DES MODÈLES ==="
du -sh /opt/connective-ai/models/deepseek-v4-pro/* 2>/dev/null || echo "Pas de sous-dossiers"
echo ""
echo "=== CONTENU DEEPSEEK ==="
ls -la /opt/connective-ai/models/deepseek-v4-pro/
echo ""
echo "=== RECHERCHE .GGUF (quantifié) ==="
find /opt/connective-ai/models/ -name "*.gguf" | head -3
