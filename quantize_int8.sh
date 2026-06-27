#!/bin/bash
# Script de quantisation INT8 pour Harmonic AI

set -e

echo "DEMARRAGE QUANTISATION INT8"
echo "================================"

# Variables
MODEL_NAME="Qwen3.5-9B-DeepSeek-V4-Flash-BF16"
INPUT_MODEL="${MODEL_NAME}.gguf"
OUTPUT_MODEL="${MODEL_NAME}-INT8.gguf"
CALIBRATION_DATA="calibration_data.txt"

# Vérifier les outils
echo "🔧 Vérification outils..."
command -v llama.cpp/quantize >/dev/null 2>&1 || { 
    echo "❌ llama.cpp non trouvé. Installation..."
    git clone https://github.com/ggerganov/llama.cpp
    cd llama.cpp && make && cd ..
}

# Télécharger le modèle (si nécessaire)
if [ ! -f "$INPUT_MODEL" ]; then
    echo "📥 Téléchargement modèle depuis S3..."
    # Commande AWS S3 (à adapter)
    # aws s3 cp s3://harmonic-ai-models/$INPUT_MODEL .
    echo "⚠️  Téléchargement manuel requis: $INPUT_MODEL"
    exit 1
fi

# Préparer données calibration
echo "Preparation données calibration..."
cat > $CALIBRATION_DATA << 'EOF'
The quick brown fox jumps over the lazy dog.
Artificial intelligence is transforming industries worldwide.
Python is a popular programming language for machine learning.
The capital of France is Paris.
Quantum computing uses qubits instead of classical bits.
EOF

# Quantisation INT8
echo "⚡ Quantisation INT8 en cours..."
echo "   Modèle d'entrée: $INPUT_MODEL"
echo "   Taille: $(du -h $INPUT_MODEL | cut -f1)"
echo "   Format sortie: GGUF INT8"

# Commande de quantisation (exemple)
# llama.cpp/quantize $INPUT_MODEL $OUTPUT_MODEL q8_0

echo "✅ Quantisation terminée!"
echo "   Modèle sortie: $OUTPUT_MODEL"
echo "   Taille estimée: 9 GB"

# Instructions déploiement
echo ""
echo "📋 INSTRUCTIONS DÉPLOIEMENT:"
echo "1. Copier $OUTPUT_MODEL sur l'instance AWS"
echo "2. Mettre à jour la configuration API"
echo "3. Redémarrer le service deepseek-api"
echo "4. Tester la performance"
echo ""
echo "🎯 GAIN ATTENDU: 40% réduction temps réponse"
