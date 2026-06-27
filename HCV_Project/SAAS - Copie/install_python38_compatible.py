#!/usr/bin/env python3
"""
🔧 INSTALLATION VERSIONS COMPATIBLES PYTHON 3.8
Pour EC2 avec Python 3.8
"""

import subprocess
import sys

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
    print("🚀 INSTALLATION COMPATIBLE PYTHON 3.8")
    print("=" * 60)
    
    # Étape 1: Vérifier version Python
    run_command("python3 --version", "Vérification Python")
    
    # Étape 2: Installation versions compatibles
    print("\n📦 INSTALLATION VERSIONS COMPATIBLES")
    print("-" * 40)
    
    # Transformers compatible Python 3.8
    run_command(
        "python3 -m pip install transformers==4.21.0",
        "Transformers 4.21.0 (compatible Python 3.8)"
    )
    
    # Tokenizers compatible
    run_command(
        "python3 -m pip install tokenizers==0.12.1",
        "Tokenizers 0.12.1 (compatible Python 3.8)"
    )
    
    # Datasets compatible
    run_command(
        "python3 -m pip install datasets==2.0.0",
        "Datasets 2.0.0 (compatible Python 3.8)"
    )
    
    # Accelerate compatible
    run_command(
        "python3 -m pip install accelerate==0.12.0",
        "Accelerate 0.12.0 (compatible Python 3.8)"
    )
    
    # Sentencepiece (requis)
    run_command(
        "python3 -m pip install sentencepiece",
        "Sentencepiece"
    )
    
    # Protobuf (requis)
    run_command(
        "python3 -m pip install protobuf==3.20.0",
        "Protobuf 3.20.0 (compatible)"
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
        import tokenizers
        print(f"✅ Tokenizers: {tokenizers.__version__}")
    except ImportError:
        print("❌ Tokenizers: Non installé")
    
    try:
        import accelerate
        print(f"✅ Accelerate: {accelerate.__version__}")
    except ImportError:
        print("❌ Accelerate: Non installé")
    
    print("\n🚀 INSTALLATION TERMINÉE!")
    print("Prêt pour Mistral compatible Python 3.8...")

if __name__ == "__main__":
    main()
