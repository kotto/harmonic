#!/usr/bin/env python3
"""
🚀 LANCEUR DE SPÉCIALISATION HARMONIC AI
Script principal pour lancer la spécialisation avec fichiers textes et images
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Ajout du chemin pour les imports
sys.path.append(str(Path(__file__).parent.parent.parent))

def create_sample_config():
    """Crée un fichier de configuration d'exemple"""
    
    config = {
        "domain": "example_domain",
        "specialization_type": "adaptive",
        "learning_rate": 0.001,
        "epochs": 10,
        "batch_size": 8,
        "validation_split": 0.2,
        "convergence_threshold": 0.9,
        "harmonic_stability": 0.98,
        "adaptation_rate": 0.1,
        "data_directory": "./specialization_data",
        "aws_bucket": "harmonic-ai-knowledge-base",
        "aws_region": "us-east-1"
    }
    
    config_file = "specialization_config_example.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Fichier de configuration créé: {config_file}")
    print(f"📝 Modifiez ce fichier puis lancez avec:")
    print(f"   python launch_specialization.py --config {config_file}")

def main():
    """Fonction principale"""
    
    parser = argparse.ArgumentParser(description="Lanceur de spécialisation Harmonic AI")
    parser.add_argument("--mode", choices=["interactive", "batch", "config"], 
                       default="interactive", help="Mode de lancement")
    parser.add_argument("--config", help="Fichier de configuration (mode batch)")
    parser.add_argument("--data", help="Répertoire des données")
    parser.add_argument("--domain", help="Domaine de spécialisation")
    parser.add_argument("--create-data", help="Crée des données d'exemple")
    
    args = parser.parse_args()
    
    print("🎯 HARMONIC AI SPECIALIZATION LAUNCHER")
    print("=" * 50)
    
    if args.mode == "config":
        create_sample_config()
    else:
        print("📋 Mode spécialisation nécessite l'installation des dépendances:")
        print("📦 pip install torch torchvision transformers pillow numpy boto3")
        print("🔧 Configurez également vos credentials AWS")

if __name__ == "__main__":
    main()
