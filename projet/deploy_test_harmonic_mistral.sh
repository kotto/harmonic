#!/bin/bash
cd /opt/connective-ai

# Télécharger tous les fichiers
echo "📥 Téléchargement des fichiers..."
aws s3 cp s3://deepseek-models-326095712935/models/mistral_harmonic_resonance.py .
aws s3 cp s3://deepseek-models-326095712935/models/harmonic_mistral_fusion.py .
aws s3 cp s3://deepseek-models-326095712935/models/fusion_processus_explique.py .

# Installer dépendances (si nécessaire)
echo "🔧 Installation dépendances..."
pip install numpy math 2>/dev/null || echo "Dépendances OK"

# Test du système Harmonic seul
echo "🌊 TEST 1: Harmonic seul..."
python3 harmonic_response_generator_simple.py

# Test du système Mistral Harmonique
echo "🔥 TEST 2: Mistral Harmonique..."
python3 mistral_harmonic_resonance.py

# Test de la fusion complète
echo "🚀 TEST 3: Fusion Harmonic-Mistral..."
python3 harmonic_mistral_fusion.py

echo "✅ Tests terminés!"
