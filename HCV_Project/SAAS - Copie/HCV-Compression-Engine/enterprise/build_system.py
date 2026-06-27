#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HCV PRO - Enterprise Build System
================================
Système de build sécurisé pour distribution entreprise

🔐 Protection contre reverse engineering
📦 Packaging automatisé
🛡️ Obfuscation multi-niveaux
🚀 Compilation optimisée
"""

import os
import sys
import shutil
import subprocess
import json
import hashlib
import tempfile
import zipfile
import time
import logging
from pathlib import Path
from datetime import datetime

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('build.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnterpriseBuilder:
    """
    Builder sécurisé pour distribution entreprise HCV PRO
    Protection multi-niveaux et packaging automatisé
    """
    
    def __init__(self):
        """Initialisation builder"""
        self.project_root = Path(__file__).parent
        self.src_dir = self.project_root / "enterprise" / "src"
        self.build_dir = self.project_root / "enterprise" / "build"
        self.dist_dir = self.project_root / "dist"
        self.config = self.load_build_config()
        
        # Création répertoires
        self.dist_dir.mkdir(exist_ok=True)
        self.build_dir.mkdir(exist_ok=True)
        
        logger.info("🔧 Builder HCV PRO Enterprise initialisé")
    
    def load_build_config(self):
        """Chargement configuration build"""
        config_path = self.project_root / "enterprise" / "config" / "build_config.json"
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Configuration par défaut
            return {
                "obfuscation": {
                    "enabled": True,
                    "level": "high",
                    "encrypt_strings": True,
                    "rename_variables": True,
                    "control_flow_flattening": True
                },
                "compilation": {
                    "optimize": True,
                    "strip_symbols": True,
                    "upx_compress": True,
                    "one_file": True
                },
                "security": {
                    "anti_debug": True,
                    "integrity_check": True,
                    "license_protection": True,
                    "hardware_binding": True
                },
                "packaging": {
                    "create_installer": True,
                    "include_dependencies": True,
                    "compress_output": True,
                    "sign_binary": True
                }
            }
    
    def build_enterprise_version(self):
        """Build complet version entreprise"""
        logger.info("🚀 Début build version entreprise HCV PRO")
        
        try:
            # 1. Préparation environnement
            self.prepare_build_environment()
            
            # 2. Obfuscation code source
            if self.config["obfuscation"]["enabled"]:
                self.obfuscate_source_code()
            
            # 3. Compilation binaire
            self.compile_executable()
            
            # 4. Application protections sécurité
            self.apply_security_protections()
            
            # 5. Packaging distribution
            self.create_distribution_package()
            
            # 6. Tests de sécurité
            self.run_security_tests()
            
            # 7. Génération rapport
            self.generate_build_report()
            
            logger.info("✅ Build entreprise terminé avec succès!")
            
        except Exception as e:
            logger.error(f"❌ Erreur build: {e}")
            raise
    
    def prepare_build_environment(self):
        """Préparation environnement de build"""
        logger.info("📋 Préparation environnement build")
        
        # Nettoyage précédent build
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        self.build_dir.mkdir(exist_ok=True)
        
        # Création structure build
        (self.build_dir / "obfuscated").mkdir(exist_ok=True)
        (self.build_dir / "compiled").mkdir(exist_ok=True)
        (self.build_dir / "protected").mkdir(exist_ok=True)
        (self.build_dir / "package").mkdir(exist_ok=True)
        
        # Installation dépendances build
        self.install_build_dependencies()
    
    def install_build_dependencies(self):
        """Installation dépendances build"""
        logger.info("📦 Installation dépendances build")
        
        dependencies = [
            "pyinstaller>=5.0",
            "pyarmor>=6.0", 
            "upx>=3.96",
            "cryptography>=3.4"
        ]
        
        for dep in dependencies:
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", dep
                ], check=True, capture_output=True)
                logger.info(f"✅ {dep} installé")
            except subprocess.CalledProcessError as e:
                logger.warning(f"⚠️ Erreur installation {dep}: {e}")
    
    def obfuscate_source_code(self):
        """Obfuscation code source"""
        logger.info("🔐 Obfuscation code source")
        
        obfuscated_dir = self.build_dir / "obfuscated"
        
        # Copie code source
        shutil.copytree(self.src_dir, obfuscated_dir / "src", dirs_exist_ok=True)
        
        # Configuration PyArmor
        pyarmor_config = {
            "--obf-code": 1,
            "--obf-mod": 1,
            "--restrict-mode": 2,
            "--wrap-mode": 1,
            "--platform": ".".join(map(str, sys.version_info[:2])),
            "--output": str(obfuscated_dir / "dist")
        }
        
        if self.config["obfuscation"]["encrypt_strings"]:
            pyarmor_config["--obf-code"] = 2
        
        if self.config["obfuscation"]["control_flow_flattening"]:
            pyarmor_config["--obf-mod"] = 2
        
        # Construction commande PyArmor
        cmd = ["pyarmor", "obfuscate"]
        for key, value in pyarmor_config.items():
            cmd.extend([key, str(value)])
        cmd.append(str(obfuscated_dir / "src" / "core" / "compressor.py"))
        
        # Exécution obfuscation
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info("✅ Obfuscation PyArmor terminée")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erreur obfuscation: {e}")
            raise
        
        # Obfuscation personnalisée pour fichiers restants
        self.custom_obfuscation(obfuscated_dir)
    
    def custom_obfuscation(self, obfuscated_dir):
        """Obfuscation personnalisée du code"""
        logger.info("🎭 Application obfuscation personnalisée")
        
        for root, dirs, files in os.walk(obfuscated_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    self.obfuscate_python_file(file_path)
    
    def obfuscate_python_file(self, file_path):
        """Obfuscation fichier Python individuel"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Renommage variables
            if self.config["obfuscation"]["rename_variables"]:
                content = self.rename_variables(content)
            
            # Encryption strings
            if self.config["obfuscation"]["encrypt_strings"]:
                content = self.encrypt_strings(content)
            
            # Ajout anti-debug
            if self.config["security"]["anti_debug"]:
                content = self.add_anti_debug_code(content)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            logger.warning(f"⚠️ Erreur obfuscation {file_path}: {e}")
    
    def rename_variables(self, content):
        """Renommage variables"""
        import re
        import random
        import string
        
        # Mapping variables
        var_map = {}
        
        # Remplacement variables simples
        simple_vars = re.findall(r'\b([a-z_][a-z0-9_]*)\b', content)
        
        for var in set(simple_vars):
            if var not in ['import', 'from', 'def', 'class', 'return', 'if', 'else', 'for', 'while']:
                if var not in var_map:
                    var_map[var] = ''.join(random.choices(string.ascii_lowercase, k=8))
        
        # Remplacement dans le contenu
        for old_var, new_var in var_map.items():
            content = re.sub(r'\b' + re.escape(old_var) + r'\b', new_var, content)
        
        return content
    
    def encrypt_strings(self, content):
        """Encryption des chaînes de caractères"""
        import base64
        import re
        
        # Recherche chaînes littérales
        strings = re.findall(r'["\']([^"\']+)["\']', content)
        
        for string in strings:
            if len(string) > 5:  # Seulement chaînes significatives
                encrypted = base64.b64encode(string.encode()).decode()
                content = content.replace(f'"{string}"', f'decrypt_string("{encrypted}")')
        
        # Ajout fonction de décryptage
        decrypt_func = '''
def decrypt_string(encoded):
    import base64
    return base64.b64decode(encoded).decode()

'''
        
        return decrypt_func + content
    
    def add_anti_debug_code(self, content):
        """Ajout code anti-debug"""
        anti_debug_code = '''
# Anti-debug protection
import sys
import ctypes
import os

def check_debugger():
    try:
        if os.name == 'nt':
            import ctypes.wintypes
            kernel32 = ctypes.windll.kernel32
            kernel32.IsDebuggerPresent.restype = ctypes.wintypes.BOOL
            if kernel32.IsDebuggerPresent():
                sys.exit(1)
        else:
            if os.path.exists('/proc/self/status'):
                with open('/proc/self/status') as f:
                    if 'TracerPid:' in f.read() and '0' not in f.read():
                        sys.exit(1)
    except:
        pass

check_debugger()

'''
        
        return anti_debug_code + content
    
    def compile_executable(self):
        """Compilation exécutable"""
        logger.info("⚙️ Compilation exécutable")
        
        obfuscated_dir = self.build_dir / "obfuscated"
        compiled_dir = self.build_dir / "compiled"
        
        # Configuration PyInstaller
        pyinstaller_spec = f'''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{obfuscated_dir / "src" / "web" / "app.py"}'],
    pathex=['{obfuscated_dir / "src"}'],
    binaries=[],
    datas=[],
    hiddenimports=['cryptography', 'flask', 'jwt', 'psutil'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='hcv_pro_enterprise',
    debug=False,
    bootloader_ignore_signals=False,
    strip={'strip_symbols'},
    upx={'upx_compress'},
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
        
        # Écriture fichier spec
        spec_file = self.build_dir / "hcv_pro.spec"
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(pyinstaller_spec)
        
        # Compilation
        cmd = [
            "pyinstaller",
            "--clean",
            "--noconfirm",
            str(spec_file)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, cwd=self.build_dir)
            
            # Déplacement exécutable
            exe_path = self.build_dir / "dist" / "hcv_pro_enterprise.exe"
            if exe_path.exists():
                shutil.move(exe_path, compiled_dir / "hcv_pro_enterprise.exe")
                logger.info("✅ Compilation terminée")
            else:
                raise FileNotFoundError("Exécutable non généré")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erreur compilation: {e}")
            raise
    
    def apply_security_protections(self):
        """Application protections sécurité"""
        logger.info("🛡️ Application protections sécurité")
        
        compiled_dir = self.build_dir / "compiled"
        protected_dir = self.build_dir / "protected"
        
        exe_path = compiled_dir / "hcv_pro_enterprise.exe"
        protected_exe_path = protected_dir / "hcv_pro_enterprise.exe"
        
        if not exe_path.exists():
            raise FileNotFoundError("Exécutable non trouvé")
        
        # Copie vers répertoire protégé
        shutil.copy2(exe_path, protected_exe_path)
        
        # Compression UPX
        if self.config["compilation"]["upx_compress"]:
            self.compress_with_upx(protected_exe_path)
        
        # Ajout checksum intégrité
        if self.config["security"]["integrity_check"]:
            self.add_integrity_checksum(protected_exe_path)
        
        # Signature binaire (simulation)
        if self.config["packaging"]["sign_binary"]:
            self.sign_binary(protected_exe_path)
        
        logger.info("✅ Protections sécurité appliquées")
    
    def compress_with_upx(self, exe_path):
        """Compression UPX de l'exécutable"""
        try:
            cmd = ["upx", "--best", "--lzma", str(exe_path)]
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info("✅ Compression UPX appliquée")
        except subprocess.CalledProcessError as e:
            logger.warning(f"⚠️ Erreur compression UPX: {e}")
    
    def add_integrity_checksum(self, exe_path):
        """Ajout checksum intégrité"""
        try:
            # Calcul hash SHA-256
            with open(exe_path, 'rb') as f:
                content = f.read()
            
            checksum = hashlib.sha256(content).hexdigest()
            
            # Sauvegarde checksum
            checksum_file = exe_path.with_suffix('.sha256')
            with open(checksum_file, 'w') as f:
                f.write(checksum)
            
            logger.info(f"✅ Checksum intégrité: {checksum[:16]}...")
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur checksum: {e}")
    
    def sign_binary(self, exe_path):
        """Signature binaire (simulation)"""
        # Dans la version réelle, ceci utiliserait un certificat de signature
        logger.info("🔐 Signature binaire simulée")
        
        # Création fichier signature factice
        sig_file = exe_path.with_suffix('.sig')
        with open(sig_file, 'w') as f:
            f.write(f"HCV_PRO_SIGNATURE_{datetime.now().isoformat()}")
    
    def create_distribution_package(self):
        """Création package distribution"""
        logger.info("📦 Création package distribution")
        
        package_dir = self.build_dir / "package"
        protected_dir = self.build_dir / "protected"
        
        # Copie exécutable
        shutil.copy2(protected_dir / "hcv_pro_enterprise.exe", package_dir)
        
        # Copie fichiers additionnels
        self.copy_additional_files(package_dir)
        
        # Création installeur
        if self.config["packaging"]["create_installer"]:
            self.create_installer(package_dir)
        
        # Compression package
        if self.config["packaging"]["compress_output"]:
            self.compress_package(package_dir)
        
        logger.info("✅ Package distribution créé")
    
    def copy_additional_files(self, package_dir):
        """Copie fichiers additionnels"""
        # Fichiers configuration
        config_src = self.project_root / "enterprise" / "config"
        config_dst = package_dir / "config"
        if config_src.exists():
            shutil.copytree(config_src, config_dst, dirs_exist_ok=True)
        
        # Documentation
        docs_src = self.project_root / "enterprise" / "docs"
        docs_dst = package_dir / "docs"
        if docs_src.exists():
            shutil.copytree(docs_src, docs_dst, dirs_exist_ok=True)
        
        # Scripts
        scripts_dst = package_dir / "scripts"
        scripts_dst.mkdir(exist_ok=True)
        
        # Script de démarrage
        start_script = scripts_dst / "start.bat"
        with open(start_script, 'w') as f:
            f.write('''@echo off
echo Démarrage HCV PRO Enterprise...
hcv_pro_enterprise.exe
pause
''')
        
        # Script d'installation
        install_script = scripts_dst / "install.bat"
        with open(install_script, 'w') as f:
            f.write('''@echo off
echo Installation HCV PRO Enterprise...
mkdir "%PROGRAMFILES%\\HCV_PRO_Enterprise"
copy * "%PROGRAMFILES%\\HCV_PRO_Enterprise\\"
echo Installation terminée!
pause
''')
    
    def create_installer(self, package_dir):
        """Création installeur"""
        # Simulation création installeur NSIS
        installer_script = package_dir / "installer.nsi"
        
        nsis_content = '''
!define APPNAME "HCV PRO Enterprise"
!define VERSION "1.0.0"
!define PUBLISHER "HCV Technologies"

Name "${APPNAME}"
OutFile "${APPNAME}_Installer.exe"
InstallDir "$PROGRAMFILES\\${APPNAME}"
RequestExecutionLevel admin

Page directory
Page instfiles

Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    File /r "*"
    CreateShortCut "$DESKTOP\\${APPNAME}.lnk" "$INSTDIR\\hcv_pro_enterprise.exe"
SectionEnd
'''
        
        with open(installer_script, 'w') as f:
            f.write(nsis_content)
        
        logger.info("✅ Script installeur NSIS créé")
    
    def compress_package(self, package_dir):
        """Compression package distribution"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"hcv_pro_enterprise_{timestamp}.zip"
        archive_path = self.dist_dir / archive_name
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, package_dir)
                    zipf.write(file_path, arc_path)
        
        logger.info(f"✅ Package compressé: {archive_name}")
    
    def run_security_tests(self):
        """Tests de sécurité"""
        logger.info("🔍 Exécution tests de sécurité")
        
        # Test intégrité
        self.test_integrity()
        
        # Test anti-debug
        self.test_anti_debug()
        
        # Test licence
        self.test_license_validation()
        
        logger.info("✅ Tests de sécurité terminés")
    
    def test_integrity(self):
        """Test intégrité binaire"""
        protected_dir = self.build_dir / "protected"
        exe_path = protected_dir / "hcv_pro_enterprise.exe"
        checksum_path = protected_dir / "hcv_pro_enterprise.exe.sha256"
        
        if exe_path.exists() and checksum_path.exists():
            with open(exe_path, 'rb') as f:
                content = f.read()
            
            current_hash = hashlib.sha256(content).hexdigest()
            
            with open(checksum_path, 'r') as f:
                stored_hash = f.read().strip()
            
            if current_hash == stored_hash:
                logger.info("✅ Test intégrité réussi")
            else:
                logger.error("❌ Test intégrité échoué")
                raise Exception("Checksum invalide")
    
    def test_anti_debug(self):
        """Test protection anti-debug"""
        # Simulation test anti-debug
        logger.info("✅ Test anti-debug simulé")
    
    def test_license_validation(self):
        """Test validation licence"""
        # Simulation test licence
        logger.info("✅ Test licence simulé")
    
    def generate_build_report(self):
        """Génération rapport build"""
        report = {
            "build_timestamp": datetime.now().isoformat(),
            "build_config": self.config,
            "build_steps": [
                "Préparation environnement",
                "Obfuscation code source", 
                "Compilation exécutable",
                "Application protections sécurité",
                "Création package distribution",
                "Tests de sécurité"
            ],
            "output_files": [],
            "security_measures": [
                "Obfuscation PyArmor",
                "Renommage variables",
                "Encryption strings",
                "Anti-debug protection",
                "Integrity checksum",
                "UPX compression"
            ],
            "success": True
        }
        
        # Liste fichiers générés
        for file in self.dist_dir.glob("*"):
            if file.is_file():
                report["output_files"].append({
                    "name": file.name,
                    "size": file.stat().st_size,
                    "path": str(file)
                })
        
        # Sauvegarde rapport
        report_path = self.build_dir / f"build_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 Rapport build généré: {report_path}")
        
        # Affichage résumé
        print("\n" + "="*50)
        print("🚀 HCV PRO ENTERPRISE - RAPPORT BUILD")
        print("="*50)
        print(f"Timestamp: {report['build_timestamp']}")
        print(f"Fichiers générés: {len(report['output_files'])}")
        print("Mesures sécurité:")
        for measure in report['security_measures']:
            print(f"  ✅ {measure}")
        print("="*50)

# Point d'entrée
if __name__ == "__main__":
    try:
        builder = EnterpriseBuilder()
        builder.build_enterprise_version()
    except Exception as e:
        logger.error(f"❌ Erreur build: {e}")
        sys.exit(1)
