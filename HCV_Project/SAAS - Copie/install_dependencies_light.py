#!/usr/bin/env python3
"""
🔧 INSTALLATION DÉPENDANCES LÉGÈRES POUR MISTRAL
Version optimisée pour EC2 3.8GB RAM
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Exécute une commande et affiche le résultat"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description}: SUCCÈS")
            return True
        else:
            print(f"❌ {description}: ÉCHEC")
            print(f"Erreur: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description}: Exception - {e}")
        return False

def main():
    print("🚀 INSTALLATION DÉPENDANCES MISTRAL LÉGÈRES")
    print("=" * 60)
    
    # Étape 1: Mise à jour pip
    run_command("python3 -m pip install --upgrade pip", "Mise à jour pip")
    
    # Étape 2: Installation torch CPU léger
    run_command(
        "python3 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu",
        "Installation PyTorch CPU léger"
    )
    
    # Étape 3: Installation transformers
    run_command(
        "python3 -m pip install transformers",
        "Installation Transformers"
    )
    
    # Étape 4: Installation dépendances essentielles
    run_command(
        "python3 -m pip install numpy",
        "Installation NumPy"
    )
    
    # Étape 5: Installation accélérateurs légers
    run_command(
        "python3 -m pip install accelerate",
        "Installation Accelerate"
    )
    
    # Étape 6: Installation tokenizers
    run_command(
        "python3 -m pip install tokenizers",
        "Installation Tokenizers"
    )
    
    print("\n🎯 VÉRIFICATION INSTALLATION")
    print("=" * 40)
    
    # Test des imports
    try:
        import torch
        print(f"✅ PyTorch: {torch.__version__}")
    except ImportError:
        print("❌ PyTorch: Non installé")
    
    try:
        import transformers
        print(f"✅ Transformers: {transformers.__version__}")
    except ImportError:
        print("❌ Transformers: Non installé")
    
    try:
        import numpy
        print(f"✅ NumPy: {numpy.__version__}")
    except ImportError:
        print("❌ NumPy: Non installé")
    
    try:
        import accelerate
        print(f"✅ Accelerate: {accelerate.__version__}")
    except ImportError:
        print("❌ Accelerate: Non installé")
    
    print("\n🚀 INSTALLATION TERMINÉE!")
    print("Prêt pour Mistral léger...")

if __name__ == "__main__":
    main()
