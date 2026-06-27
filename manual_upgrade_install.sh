#!/bin/bash
# 🚀 UPGRADE MANUEL EC2 + INSTALLATION MISTRAL RÉEL

echo "🚀 UPGRADE MANUEL EC2 POUR MISTRAL RÉEL"
echo "================================================"

# Étape 1: Installation boto3
echo "📦 Installation boto3..."
pip install boto3

# Étape 2: Upgrade instance via AWS CLI (manuel)
echo "⚠️ UPGRADE INSTANCE MANUEL REQUIS"
echo "Instructions pour upgrade manuel:"
echo "1. Aller dans console AWS EC2"
echo "2. Sélectionner instance i-0716d7805ca2c22e9"
echo "3. Click droit -> Instance Settings -> Change instance type"
echo "4. Choisir t3.xlarge (16GB RAM)"
echo "5. Confirmer et redémarrer"
echo ""

# Étape 3: Installation dépendances complètes
echo "🔧 Installation dépendances pour Mistral..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install transformers>=4.30.0
pip install accelerate
pip install datasets
pip install sentencepiece
pip install protobuf
pip install bitsandbytes

# Étape 4: Création dossier modèles
echo "📁 Création dossier modèles..."
mkdir -p /opt/connective-ai/models/mistral-7b

# Étape 5: Téléchargement Mistral
echo "🔥 Téléchargement Mistral 7B..."
python3 -c "
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import os

print('🔥 Téléchargement Mistral 7B...')
model_name = 'mistralai/Mistral-7B-Instruct-v0.2'
cache_dir = '/opt/connective-ai/models/mistral-7b'

try:
    print('📥 Tokenizer...')
    tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
    
    print('📥 Modèle...')
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        cache_dir=cache_dir,
        torch_dtype=torch.float16,
        device_map='auto',
        trust_remote_code=True,
        low_cpu_mem_usage=True
    )
    
    print('✅ Mistral 7B téléchargé!')
    print(f'Paramètres: {model.num_parameters():,}')
    
except Exception as e:
    print(f'❌ Erreur: {e}')
    print('⚠️ Upgrade manuel requis')
"

echo "✅ Installation terminée!"
echo "🔥 Prêt pour VRAI Mistral 7B!"
