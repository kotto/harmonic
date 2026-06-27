#!/usr/bin/env python3
"""
Setup Upscaling Infrastructure pour HCV16 Mobile
Installation des dépendances pour upscaling 4K + compression
"""

import subprocess
import sys
import os

def install_requirements():
    """Installation des dépendances upscaling"""
    requirements = [
        'opencv-python>=4.8.0',
        'pillow>=10.0.0',
        'numpy>=1.24.0',
        'scipy>=1.10.0',
        'scikit-image>=0.20.0'
    ]
    
    print("📦 Installation dépendances upscaling...")
    
    for req in requirements:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', req])
            print(f"✅ {req} installé")
        except subprocess.CalledProcessError:
            print(f"❌ Erreur installation {req}")
    
    print("✅ Setup upscaling terminé")

if __name__ == "__main__":
    install_requirements()