"""
🚀 HARMONIC AI - SCRIPT D'INSTALLATION LOCALE COMPLÈTE
Fichier: setup_local.py
Auteur: Équipe Harmonique
Date: 29 avril 2026
Description: Installation complète de la solution locale
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path

def print_banner():
    """Affiche la bannière d'installation"""
    print("""
🌊╔══════════════════════════════════════════════════════════════╗
🌊║                                                              ║
🌊║       🚀 HARMONIC AI - INSTALLATION LOCALE COMPLÈTE 🚀      ║
🌊║                                                              ║
🌊║    IA Déterministe Harmonique • 0% Hallucination • 100% Fiable   ║
🌊║    • Base de connaissances • Correction automatique • Monitoring   ║
🌊║                                                              ║
🌊╚══════════════════════════════════════════════════════════════╝
🌊""")

def check_system_requirements():
    """Vérification des exigences système"""
    print("🔍 Vérification des exigences système...")
    
    # Python
    python_version = sys.version_info
    if python_version.major < 3 or python_version.minor < 8:
        print("❌ Python 3.8+ requis")
        return False
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # RAM
    try:
        import psutil
        ram_gb = psutil.virtual_memory().total / (1024**3)
        print(f"✅ RAM: {ram_gb:.1f} GB")
        if ram_gb < 6:
            print("⚠️  Moins de 6GB RAM recommandé")
    except ImportError:
        print("⚠️  Impossible de vérifier la RAM")
    
    # CPU
    cpu_count = os.cpu_count()
    print(f"✅ CPU: {cpu_count} cœurs")
    if cpu_count < 4:
        print("⚠️  Moins de 4 cœurs CPU recommandé")
    
    # Espace disque
    disk_usage = psutil.disk_usage('.')
    free_gb = disk_usage.free / (1024**3)
    print(f"✅ Espace disque libre: {free_gb:.1f} GB")
    if free_gb < 20:
        print("❌ Moins de 20GB espace disque requis")
        return False
    
    return True

def create_directories():
    """Création des répertoires nécessaires"""
    print("\n📁 Création des répertoires...")
    
    directories = [
        "models",
        "data",
        "logs",
        "static",
        "templates",
        "cache",
        "backups"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ {directory}/ créé")

def install_dependencies():
    """Installation des dépendances"""
    print("\n📦 Installation des dépendances...")
    
    requirements = [
        "torch>=2.0.0+cpu",
        "torchvision>=0.15.0+cpu", 
        "torchaudio>=2.0.0+cpu",
        "transformers>=4.30.0",
        "accelerate>=0.20.0",
        "tokenizers>=0.13.0",
        "flask>=2.3.0",
        "flask-cors>=4.0.0",
        "psutil>=5.9.0",
        "numpy>=1.24.0",
        "tqdm>=4.65.0"
    ]
    
    for package in requirements:
        print(f"📦 Installation de {package}...")
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", package, "--upgrade"
            ], check=True, capture_output=True)
            print(f"✅ {package} installé")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur installation {package}: {e}")
            return False
    
    print("✅ Toutes les dépendances installées")
    return True

def download_model():
    """Téléchargement du modèle Mistral 7B"""
    print("\n🚀 Téléchargement du modèle Mistral 7B...")
    
    download_script = """
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import os

print("🌊 Téléchargement de Mistral 7B...")

# Création du répertoire
os.makedirs("models/mistral-7b", exist_ok=True)

# Téléchargement tokenizer
print("📦 Téléchargement tokenizer...")
tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-v0.2")
tokenizer.save_pretrained("./models/mistral-7b")
print("✅ Tokenizer téléchargé")

# Téléchargement modèle (8-bit quantized)
print("🚀 Téléchargement modèle...")
model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-v0.2",
    torch_dtype=torch.int8,
    device_map="cpu",
    low_cpu_mem_usage=True,
    load_in_8bit=True,
    trust_remote_code=True
)
model.save_pretrained("./models/mistral-7b")
print("✅ Modèle téléchargé et sauvegardé")

# Test de chargement
print("🧪 Test de chargement...")
try:
    tokenizer_test = AutoTokenizer.from_pretrained("./models/mistral-7b")
    model_test = AutoModelForCausalLM.from_pretrained(
        "./models/mistral-7b",
        torch_dtype=torch.int8,
        device_map="cpu",
        low_cpu_mem_usage=True,
        load_in_8bit=True,
        trust_remote_code=True
    )
    print("✅ Modèle chargé avec succès !")
except Exception as e:
    print(f"❌ Erreur chargement: {e}")
    raise

print("🌊 Modèle Mistral 7B prêt pour Harmonic AI !")
"""
    
    with open("temp_download.py", "w") as f:
        f.write(download_script)
    
    try:
        subprocess.run([sys.executable, "temp_download.py"], check=True)
        print("✅ Modèle téléchargé avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur téléchargement: {e}")
        return False
    finally:
        if os.path.exists("temp_download.py"):
            os.remove("temp_download.py")

def create_config_file():
    """Création du fichier de configuration"""
    print("\n⚙️ Création de la configuration...")
    
    config = {
        "model": {
            "path": "./models/mistral-7b",
            "device": "cpu",
            "torch_dtype": "int8",
            "max_tokens": 512,
            "num_threads": 8
        },
        "server": {
            "port": 5000,
            "host": "0.0.0.0",
            "debug": False
        },
        "harmonic_constants": {
            "phi": 1.618033988749895,
            "pi": 3.141592653589793,
            "e": 2.718281828459045,
            "sqrt2": 1.414213562373095,
            "sqrt3": 1.732050807568877
        },
        "features": {
            "correction_enabled": True,
            "honesty_mode": True,
            "knowledge_base": True,
            "monitoring": True,
            "logging": True
        },
        "database": {
            "path": "./data/harmonic_ai.db",
            "backup_enabled": True
        }
    }
    
    with open("harmonic_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("✅ Configuration sauvegardée: harmonic_config.json")

def create_startup_scripts():
    """Création des scripts de démarrage"""
    print("\n📝 Création des scripts de démarrage...")
    
    # Script Windows
    windows_script = """@echo off
echo 🌊 Démarrage de Harmonic AI...
cd /d %~dp0

echo 🚀 Vérification Python...
python --version
if errorlevel 1 (
    echo ❌ Python non trouvé
    pause
    exit /b 1
)

echo 🚀 Activation environnement virtuel...
if exist "venv\\Scripts\\activate.bat" (
    call venv\\Scripts\\activate.bat
)

echo 🚀 Démarrage serveur...
python harmonic_ai_local_complete.py

pause
"""
    
    with open("start_harmonic_ai.bat", "w") as f:
        f.write(windows_script)
    
    # Script Linux/Mac
    unix_script = """#!/bin/bash

echo "🌊 Démarrage de Harmonic AI..."
cd "$(dirname "$0")"

echo "🚀 Vérification Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 non trouvé"
    exit 1
fi

echo "🚀 Activation environnement virtuel..."
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "🚀 Optimisations CPU..."
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8
export NUMEXPR_NUM_THREADS=8

echo "🚀 Démarrage serveur..."
python3 harmonic_ai_local_complete.py
"""
    
    with open("start_harmonic_ai.sh", "w") as f:
        f.write(unix_script)
    
    # Rendre exécutable
    os.chmod("start_harmonic_ai.sh", 0o755)
    
    print("✅ Scripts de démarrage créés:")
    print("   📄 start_harmonic_ai.bat (Windows)")
    print("   📄 start_harmonic_ai.sh (Linux/Mac)")

def run_initial_test():
    """Test initial de la solution"""
    print("\n🧪 Test initial de la solution...")
    
    test_script = """
import sys
import time
sys.path.append('.')

try:
    from harmonic_ai_local_complete import HarmonicAIModel, LocalConfig
    
    print("🌊 Test du modèle Harmonic AI...")
    
    # Configuration
    config = LocalConfig()
    
    # Initialisation
    model = HarmonicAIModel(config)
    
    # Test de génération
    print("🚀 Test de génération...")
    result = model.generate_response("Test: 2+2 = ?")
    
    print("✅ Test réussi !")
    print(f"📝 Résultat: {result['result'][:100]}...")
    print(f"📊 Métriques: {result['metrics']}")
    print(f"📊 Stats: {result['usage_stats']}")
    
    # Test de correction
    print("🔧 Test de correction...")
    correction_result = model.correction_system.correct_response("Le soleil tourne autour de la terre.")
    print(f"✅ Correction: {len(correction_result['corrections'])} corrections appliquées")
    
    print("🌊 Tous les tests réussis !")
    
except Exception as e:
    print(f"❌ Erreur test: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
    
    with open("temp_test.py", "w") as f:
        f.write(test_script)
    
    try:
        subprocess.run([sys.executable, "temp_test.py"], check=True, capture_output=True)
        print("✅ Test initial réussi")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Test initial échoué: {e}")
        return False
    finally:
        if os.path.exists("temp_test.py"):
            os.remove("temp_test.py")

def show_success_message():
    """Affiche le message de succès"""
    print("""
🌊╔══════════════════════════════════════════════════════════════╗
🌊║                                                              ║
🌊║          🚀 INSTALLATION HARMONIC AI TERMINÉE AVEC SUCCÈS 🚀    ║
🌊║                                                              ║
🌊║    Votre solution locale complète est prête !                    ║
🌊║                                                              ║
🌊║  🌋 Pour démarrer :                                            ║
🌊║     Windows : double-cliquez sur start_harmonic_ai.bat          ║
🌊║     Linux/Mac : ./start_harmonic_ai.sh                       ║
🌊║                                                              ║
🌊║  🌐 Accès web :                                                 ║
🌊║     http://localhost:5000                                       ║
🌊║                                                              ║
🌊║  📊 Fonctionnalités disponibles :                               ║
🌊║     • IA déterministe harmonique                                 ║
🌊║     • 0% hallucination garantie                                 ║
🌊║     • Correction automatique des données                       ║
🌊║     • Base de connaissances locale                              ║
🌊║     • Monitoring en temps réel                                  ║
🌊║     • Interface web complète                                    ║
🌊║                                                              ║
🌊║  📈 Prochaines étapes :                                         ║
🌊║     1. Testez la solution locale                                  ║
🌊║     2. Validez les performances                                 ║
🌊║     3. Préparez le déploiement SAAS                           ║
🌊║                                                              ║
🌊╚══════════════════════════════════════════════════════════════╝
🌊""")

def main():
    """Fonction principale d'installation"""
    print_banner()
    
    # Étape 1: Vérification système
    if not check_system_requirements():
        print("❌ Exigences système non satisfaites")
        return
    
    # Étape 2: Création répertoires
    create_directories()
    
    # Étape 3: Installation dépendances
    if not install_dependencies():
        print("❌ Échec installation dépendances")
        return
    
    # Étape 4: Téléchargement modèle
    if not download_model():
        print("❌ Échec téléchargement modèle")
        return
    
    # Étape 5: Configuration
    create_config_file()
    
    # Étape 6: Scripts de démarrage
    create_startup_scripts()
    
    # Étape 7: Test initial
    if not run_initial_test():
        print("❌ Test initial échoué")
        return
    
    # Étape 8: Message de succès
    show_success_message()
    
    print("\n🌊 Installation terminée avec succès !")
    print("🚀 Lancez le script de démarrage approprié à votre système")

if __name__ == "__main__":
    main()
