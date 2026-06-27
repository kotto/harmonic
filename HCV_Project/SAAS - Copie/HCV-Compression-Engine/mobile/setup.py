#!/usr/bin/env python3
"""
HCV PRO - OpenClaw Mobile Setup Script
=====================================
Installation automatique pour téléphone mobile augmenté
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_requirements():
    """Vérification des prérequis système"""
    print("🔍 Vérification des prérequis...")
    
    # Python version
    python_version = sys.version_info
    if python_version < (3, 8):
        print(f"❌ Python {python_version.major}.{python_version.minor} détecté. Python 3.8+ requis.")
        return False
    else:
        print(f"✅ Python {python_version.major}.{python_version.minor} OK")
    
    # Platform check
    if platform.system() != "Linux":
        print("⚠️  Ce setup est optimisé pour Android/Linux")
        print("   Sur Windows/macOS, utilisez WSL ou Docker")
    
    # Android check
    if os.path.exists('/system/build.prop'):
        print("✅ Environment Android détecté")
    else:
        print("⚠️  Environment non-Android détecté")
    
    return True

def install_dependencies():
    """Installation des dépendances"""
    print("\n📦 Installation des dépendances...")
    
    try:
        # Installation pip
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", 
            "requirements.txt", "--upgrade"
        ])
        print("✅ Dépendances installées avec succès")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur installation dépendances: {e}")
        return False
    
    return True

def setup_directories():
    """Création des répertoires nécessaires"""
    print("\n📁 Création des répertoires...")
    
    directories = [
        '/sdcard/HCV_Compressed',
        '/sdcard/HCV_Temp',
        '/sdcard/HCV_Backup',
        '/sdcard/HCV_Logs'
    ]
    
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"✅ {directory} créé")
        except Exception as e:
            print(f"❌ Erreur création {directory}: {e}")

def configure_permissions():
    """Configuration des permissions Android"""
    print("\n🔐 Configuration des permissions...")
    
    # Instructions pour permissions manuelles
    permissions_instructions = """
    🔐 PERMISSIONS ANDROID REQUISES:
    
    1. Accès Stockage:
       - Paramètres → Applications → HCV PRO → Permissions → Stockage
       - Activer "Autoriser"
    
    2. Accès Fichiers:
       - Paramètres → Applications → HCV PRO → Permissions → Fichiers
       - Activer "Autoriser"
    
    3. Arrière-plan:
       - Paramètres → Applications → HCV PRO → Batterie
       - Désactiver "Optimisation batterie"
    
    4. OpenClaw (si installé):
       - Suivre les instructions OpenClaw
       - Activer "Accès complet"
    """
    
    print(permissions_instructions)

def setup_openclaw():
    """Configuration OpenClaw integration"""
    print("\n🤖 Configuration OpenClaw...")
    
    # Vérification OpenClaw
    try:
        import openclaw
        print("✅ OpenClaw détecté")
        
        # Création configuration
        config = {
            "hcv_pro_integration": {
                "enabled": True,
                "version": "1.0.0",
                "compression_auto": True,
                "ai_assistant": True,
                "cloud_sync": True
            }
        }
        
        config_dir = Path.home() / '.openclaw'
        config_dir.mkdir(exist_ok=True)
        
        import json
        with open(config_dir / 'hcv_pro_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Configuration OpenClaw créée")
        
    except ImportError:
        print("⚠️  OpenClaw non installé - Mode simulation")
        print("   Pour installation complète: pip install openclaw")

def create_launcher():
    """Création du launcher Android"""
    print("\n🚀 Création du launcher...")
    
    launcher_script = """#!/system/bin/sh
# HCV PRO - OpenClaw Mobile Launcher
cd /data/data/com.hcvpro.openclaw.mobile
export PYTHONPATH=/data/data/com.hcvpro.openclaw.mobile:$PYTHONPATH
python3 hcv_openclaw_integration.py --auto-start
"""
    
    launcher_path = '/sdcard/HCV_PRO_Launcher.sh'
    try:
        with open(launcher_path, 'w') as f:
            f.write(launcher_script)
        
        # Rendre exécutable
        os.chmod(launcher_path, 0o755)
        print(f"✅ Launcher créé: {launcher_path}")
        
    except Exception as e:
        print(f"❌ Erreur création launcher: {e}")

def main():
    """Setup principal"""
    print("🚀 HCV PRO - OpenClaw Mobile Setup")
    print("=" * 50)
    print("Transformez votre téléphone en mobile haut de gamme")
    print()
    
    # Vérification prérequis
    if not check_requirements():
        print("\n❌ Setup échoué - Prérequis non satisfaits")
        return False
    
    # Installation dépendances
    if not install_dependencies():
        print("\n❌ Setup échoué - Erreur dépendances")
        return False
    
    # Configuration
    setup_directories()
    configure_permissions()
    setup_openclaw()
    create_launcher()
    
    # Instructions finales
    print("\n✅ Setup terminé avec succès!")
    print()
    print("🎯 PROCHAINES ÉTAPES:")
    print("1. Redémarrez votre téléphone")
    print("2. Lancez HCV PRO depuis l'app drawer")
    print("3. Accordez les permissions demandées")
    print("4. Profitez de votre mobile augmenté!")
    print()
    print("📱 Votre téléphone est maintenant un mobile HCV PRO!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
