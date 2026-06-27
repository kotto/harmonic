#!/usr/bin/env python3
"""
📦 INSTALLATION MISTRAL HARMONIC FUSION
Installation complète des dépendances pour Mistral + Harmonique
"""

import subprocess
import sys
import os
from pathlib import Path

def install_dependencies():
    """Installer les dépendances nécessaires"""
    print("📦 INSTALLATION DÉPENDANCES MISTRAL HARMONIC")
    print("=" * 60)
    
    dependencies = [
        "torch",
        "transformers",
        "accelerate",
        "fastapi",
        "uvicorn",
        "pydantic",
        "requests",
        "numpy",
        "scipy"
    ]
    
    for dep in dependencies:
        print(f"📥 Installation: {dep}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"   ✅ {dep} installé")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Erreur installation {dep}: {e}")
    
    print("\n✅ Installation terminée")

def check_installation():
    """Vérifier l'installation"""
    print("\n🔍 VÉRIFICATION INSTALLATION...")
    
    try:
        import torch
        print(f"   ✅ PyTorch: {torch.__version__}")
    except ImportError:
        print("   ❌ PyTorch non installé")
    
    try:
        import transformers
        print(f"   ✅ Transformers: {transformers.__version__}")
    except ImportError:
        print("   ❌ Transformers non installé")
    
    try:
        import fastapi
        print(f"   ✅ FastAPI: {fastapi.__version__}")
    except ImportError:
        print("   ❌ FastAPI non installé")
    
    try:
        import numpy
        print(f"   ✅ NumPy: {numpy.__version__}")
    except ImportError:
        print("   ❌ NumPy non installé")

if __name__ == "__main__":
    install_dependencies()
    check_installation()
    
    print("\n🚀 PRÊT POUR MISTRAL HARMONIC FUSION!")
    print("📋 Lancer: python mistral_harmonic_fusion_ultimate.py")
