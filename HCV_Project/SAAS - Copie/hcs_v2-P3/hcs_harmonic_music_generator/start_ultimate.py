#!/usr/bin/env python3
"""
HCS Ultimate Audio Engine - Script de démarrage
Lance le serveur ultime avec toutes les dépendances
"""

import os
import sys
import subprocess
import platform
import time
from pathlib import Path

def check_python_version():
    """Vérifie la version Python"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ requis")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} détecté")

def check_dependencies():
    """Vérifie et installe les dépendances"""
    print("\n🔍 Vérification des dépendances...")
    
    required_packages = [
        'torch',
        'torchaudio', 
        'numpy',
        'librosa',
        'soundfile',
        'scipy',
        'fastapi',
        'uvicorn',
        'transformers',
        'openai-whisper',
        'audiocraft'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'audiocraft':
                import audiocraft
            elif package == 'openai-whisper':
                import whisper
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n📦 Installation des packages manquants: {', '.join(missing_packages)}")
        
        # Installation des dépendances
        install_commands = [
            "pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118",
            "pip install numpy librosa soundfile scipy",
            "pip install fastapi uvicorn jinja2 python-multipart",
            "pip install transformers",
            "pip install openai-whisper",
            "pip install audiocraft"
        ]
        
        for cmd in install_commands:
            try:
                print(f"🔄 Exécution: {cmd}")
                subprocess.run(cmd, shell=True, check=True)
                time.sleep(2)
            except subprocess.CalledProcessError as e:
                print(f"⚠️ Erreur installation: {e}")
                print("📝 Installation manuelle requise")
    
    print("✅ Dépendances vérifiées")

def create_directories():
    """Crée les répertoires nécessaires"""
    print("\n📁 Création des répertoires...")
    
    directories = [
        "templates",
        "static", 
        "ultimate_music",
        "generated_music",
        "professional_music"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ {directory}/")

def check_models():
    """Vérifie la disponibilité des modèles IA"""
    print("\n🤖 Vérification des modèles IA...")
    
    models_status = {}
    
    # Vérifier Whisper
    try:
        import whisper
        whisper.load_model("base")
        models_status['whisper'] = "✅ Disponible"
    except:
        models_status['whisper'] = "❌ Non disponible"
    
    # Vérifier Transformers
    try:
        from transformers import pipeline
        models_status['transformers'] = "✅ Disponible"
    except:
        models_status['transformers'] = "❌ Non disponible"
    
    # Vérifier AudioCraft
    try:
        from audiocraft.models import MusicGen
        models_status['audiocraft'] = "✅ Disponible"
    except:
        models_status['audiocraft'] = "❌ Non disponible"
    
    # Vérifier HCS modules
    try:
        from ultimate_hcs_engine import UltimateHCSEngine
        models_status['hcs_ultimate'] = "✅ Disponible"
    except:
        models_status['hcs_ultimate'] = "❌ Non disponible"
    
    for model, status in models_status.items():
        print(f"   {model}: {status}")
    
    return models_status

def start_server():
    """Démarre le serveur ultime"""
    print("\n🚀 Démarrage du serveur HCS Ultimate Audio Engine...")
    print("=" * 70)
    print("🎛️ Configuration Ultime:")
    print("   • Sample Rate: 192kHz (Ultra HD)")
    print("   • Bit Depth: 32-bit float")
    print("   • Channels: 7.1.4 (Dolby Atmos)")
    print("   • Dynamic Range: 120dB")
    print("   • Multi-IA Fusion: 6 moteurs")
    print("   • Quality: Ultra Professional")
    print("   • Port: 8023")
    print("   • Interface: http://localhost:8023")
    print("=" * 70)
    
    try:
        # Import et démarrage du serveur
        from server_ultimate import app
        
        # Configuration uvicorn
        uvicorn_config = {
            "app": app,
            "host": "0.0.0.0",
            "port": 8023,
            "reload": False,
            "log_level": "info",
            "access_log": True
        }
        
        print("🌐 Démarrage du serveur web...")
        
        # Import uvicorn et démarrage
        import uvicorn
        uvicorn.run(**uvicorn_config)
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du serveur demandé")
    except Exception as e:
        print(f"\n❌ Erreur démarrage serveur: {e}")
        print("\n🔧 Dépannage:")
        print("1. Vérifiez que le port 8023 est libre")
        print("2. Installez les dépendances manuellement")
        print("3. Vérifiez les permissions système")

def show_system_info():
    """Affiche les informations système"""
    print("\n💻 Informations Système:")
    print(f"   OS: {platform.system()} {platform.release()}")
    print(f"   Architecture: {platform.machine()}")
    print(f"   Python: {sys.version.split()[0]}")
    print(f"   Répertoire: {os.getcwd()}")

def main():
    """Fonction principale"""
    print("🚀 HCS Ultimate Audio Engine - Démarrage")
    print("=" * 50)
    
    # Vérifications
    show_system_info()
    check_python_version()
    check_dependencies()
    create_directories()
    models_status = check_models()
    
    # Avertissements si des modèles manquent
    unavailable_models = [model for model, status in models_status.items() if "❌" in status]
    if unavailable_models:
        print(f"\n⚠️ Modèles non disponibles: {', '.join(unavailable_models)}")
        print("📝 Le serveur démarrera avec fonctionnalités réduites")
    
    # Confirmation
    try:
        response = input("\n🎯 Démarrer le serveur ultime? (y/n): ").lower()
        if response not in ['y', 'yes', 'oui']:
            print("🛑 Annulation")
            return
    except KeyboardInterrupt:
        print("\n🛑 Annulation")
        return
    
    # Démarrage
    start_server()

if __name__ == "__main__":
    main()
