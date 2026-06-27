#!/usr/bin/env python3
"""
HCV PRO - Motion Design Setup Script
===================================
Installation et configuration automatique

Usage:
    python setup_motion.py [--dev] [--android] [--ios]
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Vérification version Python"""
    version = sys.version_info
    if version < (3, 8):
        print("❌ Python 3.8+ requis")
        print(f"   Actuel: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} OK")
    return True

def install_dependencies():
    """Installation des dépendances"""
    print("\n📦 Installation des dépendances...")
    
    dependencies = [
        "kivy>=2.2.0",
        "kivymd>=1.2.0",
        "materialyoucolor>=1.0.0",
        "lottie-python>=5.12.0",
        "numpy>=1.24.0",
        "opencv-python>=4.8.0",
        "pillow>=10.0.0"
    ]
    
    for dep in dependencies:
        try:
            print(f"   Installation de {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"   ✅ {dep} installé")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Erreur installation {dep}: {e}")
            return False
    
    return True

def setup_android_environment():
    """Configuration environnement Android"""
    print("\n🤖 Configuration Android...")
    
    # Variables d'environnement
    os.environ['KIVY_WINDOW'] = 'sdl2'
    os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'
    os.environ['KIVY_BCM_DISCARD'] = '1'
    
    # Configuration Kivy
    kivy_config = """
[kivy]
log_level = info
log_enable = 1
max_fps = 60
default_font = Roboto

[graphics]
fbo = hardware
multisamples = 16
vsync = 1
"""
    
    config_path = Path.home() / '.kivy' / 'config.ini'
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w') as f:
        f.write(kivy_config)
    
    print("   ✅ Configuration Kivy créée")
    print("   ✅ Variables Android configurées")

def create_desktop_entry():
    """Création raccourci bureau"""
    print("\n🖥️ Création raccourci bureau...")
    
    desktop_entry = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=HCV PRO Motion
Comment=HCV PRO Mobile avec Motion Design
Exec={sys.executable} {Path(__file__).parent / 'hcv_pro_motion_app.py'}
Icon={Path(__file__).parent / 'assets' / 'hcv_pro_icon.png'}
Terminal=false
Categories=Development;Graphics;
"""
    
    desktop_dir = Path.home() / '.local' / 'share' / 'applications'
    desktop_dir.mkdir(parents=True, exist_ok=True)
    
    desktop_file = desktop_dir / 'hcv_pro_motion.desktop'
    
    with open(desktop_file, 'w') as f:
        f.write(desktop_entry)
    
    print(f"   ✅ Raccourci créé: {desktop_file}")

def run_tests():
    """Exécution tests de base"""
    print("\n🧪 Exécution tests...")
    
    try:
        # Test import Kivy
        import kivy
        print("   ✅ Kivy import OK")
        
        # Test import KivyMD
        import kivymd
        print("   ✅ KivyMD import OK")
        
        # Test HCV PRO components
        sys.path.append(str(Path(__file__).parent))
        from hcv_pro_motion_app import HCVProMotionWidget
        print("   ✅ HCV PRO components OK")
        
        # Test animations
        from kivy.animation import Animation
        print("   ✅ Animation system OK")
        
        print("   ✅ Tous les tests passés")
        return True
        
    except ImportError as e:
        print(f"   ❌ Erreur import: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Erreur test: {e}")
        return False

def create_assets_structure():
    """Création structure assets"""
    print("\n📁 Création structure assets...")
    
    assets_dir = Path(__file__).parent / 'assets'
    assets_dir.mkdir(exist_ok=True)
    
    # Sous-dossiers
    subdirs = ['fonts', 'images', 'animations', 'sounds', 'shaders']
    for subdir in subdirs:
        (assets_dir / subdir).mkdir(exist_ok=True)
        print(f"   ✅ {subdir}/ créé")
    
    # Fichiers de configuration
    config_files = [
        'motion_config.json',
        'theme_colors.json',
        'animation_presets.json'
    ]
    
    for config_file in config_files:
        config_path = assets_dir / config_file
        if not config_path.exists():
            with open(config_path, 'w') as f:
                f.write('{}')
            print(f"   ✅ {config_file} créé")

def main():
    """Point d'entrée principal"""
    print("🚀 HCV PRO - Motion Design Setup")
    print("=" * 50)
    print("Installation et configuration automatique")
    print()
    
    # Vérification prérequis
    if not check_python_version():
        return 1
    
    # Installation dépendances
    if not install_dependencies():
        return 1
    
    # Configuration environnement
    if platform.system() == "Linux" and "ANDROID_ROOT" in os.environ:
        setup_android_environment()
    else:
        create_desktop_entry()
    
    # Création structure
    create_assets_structure()
    
    # Tests
    if not run_tests():
        return 1
    
    # Message final
    print("\n🎉 Installation terminée avec succès!")
    print("\n🚀 Lancement HCV PRO Motion:")
    print(f"   python {Path(__file__).parent / 'hcv_pro_motion_app.py'}")
    print("\n📱 Fonctionnalités:")
    print("   ✅ Interface Motion Design 60 FPS")
    print("   ✅ Assistant IA avec animations")
    print("   ✅ Compression HCV PRO animée")
    print("   ✅ Thème Material You adaptatif")
    print("   ✅ Effets de particules")
    print("   ✅ Transitions fluides")
    print("\n🎨 Profitez de votre interface futuriste!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
