#!/bin/bash
cd /opt/connective-ai

# Télécharger les fichiers
aws s3 cp s3://deepseek-models-326095712935/models/deterministic_mistral.py .
aws s3 cp s3://deepseek-models-326095712935/models/harmonic_mistral_fusion.py .

# Installer dépendances
pip install openai

# Configurer clé API (à remplacer)
export MISTRAL_API_KEY="votre-clef-mistral-ici"

# Tester
echo "🚀 DÉPLOIEMENT HARMONIC-MISTRAL"
python3 harmonic_mistral_fusion.py
