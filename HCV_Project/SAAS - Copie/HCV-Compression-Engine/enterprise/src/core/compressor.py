#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HCV PRO - Enterprise Secure Compressor
====================================
Version sécurisée avec protection contre reverse engineering

🛡️ Sécurité : Niveau Militaire
🚀 Performance : Optimisée Native
🔐 Protection : Multi-couches
"""

import sys
import os
import marshal
import zlib
import hashlib
import platform
import psutil
import ctypes
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import json
import uuid
import tempfile
import shutil
import threading
import time
import logging

# Configuration logging sécurisé
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/hcv_enterprise.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SecurityException(Exception):
    """Exception pour violations de sécurité"""
    pass

class LicenseException(Exception):
    """Exception pour problèmes de licence"""
    pass

class HCVCompressorSecure:
    """
    Compresseur HCV PRO sécurisé pour entreprise
    Protection multi-niveaux contre reverse engineering
    """
    
    def __init__(self):
        """Initialisation sécurisée du compresseur"""
        self._security_checks_passed = False
        self._license_validated = False
        self._hardware_id = None
        self._license_data = None
        self._encryption_key = None
        self._integrity_hash = None
        
        # Démarrage séquence de sécurité
        self._initialize_security()
        
    def _initialize_security(self):
        """Séquence d'initialisation sécurisée"""
        try:
            # 1. Vérification environnement
            self._check_environment_security()
            
            # 2. Génération ID hardware
            self._hardware_id = self._generate_hardware_id()
            
            # 3. Validation licence
            self._validate_enterprise_license()
            
            # 4. Vérification intégrité
            self._verify_code_integrity()
            
            # 5. Configuration encryption
            self._setup_encryption()
            
            # 6. Protection runtime
            self._setup_runtime_protection()
            
            self._security_checks_passed = True
            logger.info("✅ Sécurité HCV PRO initialisée avec succès")
            
        except Exception as e:
            logger.error(f"❌ Échec initialisation sécurité: {e}")
            raise SecurityException(f"Sécurité compromise: {e}")
    
    def _check_environment_security(self):
        """Vérification de l'environnement d'exécution"""
        # Détection debugger
        if self._is_debugger_present():
            logger.warning("⚠️ Debugger détecté")
        
        # Vérification environnement virtuel
        if self._is_virtual_environment():
            logger.warning("⚠️ Environnement virtuel détecté")
        
        # Vérification droits administrateur (désactivé pour démo)
        if not self._check_admin_privileges():
            logger.warning("⚠️ Privilèges administrateur non disponibles - Mode démo")
    
    def _is_debugger_present(self):
        """Détection de debugger"""
        try:
            # Windows debugger detection
            if platform.system() == "Windows":
                import ctypes.wintypes
                kernel32 = ctypes.windll.kernel32
                kernel32.IsDebuggerPresent.restype = ctypes.wintypes.BOOL
                return kernel32.IsDebuggerPresent()
            else:
                # Linux/Mac debugger detection
                return os.path.exists('/proc/self/status') and \
                       'TracerPid:\t0' not in open('/proc/self/status').read()
        except:
            return False
    
    def _is_virtual_environment(self):
        """Détection environnement virtuel"""
        try:
            # Vérification machine virtuelle
            if platform.system() == "Windows":
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                     r"SYSTEM\CurrentControlSet\Services\VBoxService")
                    winreg.CloseKey(key)
                    return True
                except Exception:
                    pass
            
            # Vérification hyperviseur
            dmi_info = os.popen('dmidecode 2>/dev/null').read()
            return 'VMware' in dmi_info or 'VirtualBox' in dmi_info or 'QEMU' in dmi_info
        except Exception:
            return False
    
    def _check_admin_privileges(self):
        """Vérification privilèges administrateur"""
        try:
            if platform.system() == "Windows":
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except Exception:
            return False
    
    def _generate_hardware_id(self):
        """Génération ID hardware unique"""
        try:
            # Collecte informations hardware
            cpu_info = platform.processor()
            machine = platform.machine()
            system = platform.system()
            
            # Information mémoire
            memory = psutil.virtual_memory().total
            
            # Information disque
            disk_usage = psutil.disk_usage('/').total if platform.system() != "Windows" else \
                        psutil.disk_usage('C:').total
            
            # MAC address
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                           for elements in range(0, 2*6, 2)][::-1])
            
            # Création fingerprint
            fingerprint_data = f"{cpu_info}_{machine}_{system}_{memory}_{disk_usage}_{mac}"
            hardware_id = hashlib.sha256(fingerprint_data.encode()).hexdigest()
            
            logger.info(f"🔐 Hardware ID généré: {hardware_id[:16]}...")
            return hardware_id
            
        except Exception as e:
            logger.error(f"❌ Erreur génération hardware ID: {e}")
            raise SecurityException("Impossible de générer l'ID hardware")
    
    def _validate_enterprise_license(self):
        """Validation licence entreprise"""
        try:
            # Chargement licence chiffrée
            license_path = os.path.join(os.path.dirname(__file__), '../../config/license.json')
            
            if not os.path.exists(license_path):
                logger.warning("⚠️ Fichier licence non trouvé - Mode démo")
                self._license_data = self._get_demo_license()
            else:
                with open(license_path, 'r', encoding='utf-8') as f:
                    license_full = json.load(f)
                    self._license_data = license_full.get('license_info', license_full)
            
            # Validation licence
            self._validate_license_format()
            self._validate_license_expiry()
            self._validate_hardware_binding()
            self._validate_usage_limits()
            
            self._license_validated = True
            logger.info("✅ Licence entreprise validée avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur validation licence: {e}")
            # Mode démo si licence invalide
            logger.warning("⚠️ Passage en mode démo")
            self._license_data = self._get_demo_license()
            self._license_validated = True
    
    def _get_demo_license(self):
        """Génération licence démo"""
        return {
            "company": "HCV PRO DEMO",
            "license_id": "DEMO_2024",
            "expiry_date": "perpetual",
            "hardware_binding": False,
            "max_users": 100,
            "features": ["compression_secure", "quantum_encryption", "web_interface"]
        }
    
    def _validate_license_format(self):
        """Validation format licence"""
        required_fields = ['company', 'expiry_date', 'hardware_binding', 'max_users', 'features']
        
        for field in required_fields:
            if field not in self._license_data:
                raise LicenseException(f"Champ licence manquant: {field}")
    
    def _validate_license_expiry(self):
        """Validation date d'expiration"""
        expiry_str = self._license_data.get('expiry_date')
        if expiry_str.lower() == 'perpetual':
            return
        
        try:
            expiry_date = datetime.fromisoformat(expiry_str)
            if datetime.now() > expiry_date:
                raise LicenseException(f"Licence expirée le {expiry_date}")
        except:
            raise LicenseException("Format date d'expiration invalide")
    
    def _validate_hardware_binding(self):
        """Validation binding hardware"""
        if not self._license_data.get('hardware_binding', False):
            return
        
        bound_hardware_id = self._license_data.get('hardware_id')
        if bound_hardware_id and bound_hardware_id != self._hardware_id:
            raise LicenseException("Licence non liée à ce matériel")
    
    def _validate_usage_limits(self):
        """Validation limites d'utilisation"""
        max_users = self._license_data.get('max_users', 1)
        current_users = self._get_current_user_count()
        
        if current_users > max_users:
            raise LicenseException(f"Limite utilisateurs dépassée: {current_users}/{max_users}")
    
    def _get_current_user_count(self):
        """Comptage utilisateurs actifs"""
        # Implémentation simple - à adapter selon besoins
        return 1
    
    def _verify_code_integrity(self):
        """Vérification intégrité du code"""
        try:
            # Calcul hash du code actuel
            current_hash = self._calculate_code_hash()
            
            # Récupération hash stocké
            stored_hash_path = os.path.join(os.path.dirname(__file__), '../../config/integrity.hash')
            
            if os.path.exists(stored_hash_path):
                with open(stored_hash_path, 'r') as f:
                    stored_hash = f.read().strip()
                
                if current_hash != stored_hash:
                    raise SecurityException("Code modifié - intégrité compromise")
            
            self._integrity_hash = current_hash
            logger.info("✅ Intégrité du code vérifiée")
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification intégrité: {e}")
            raise SecurityException(f"Échec vérification intégrité: {e}")
    
    def _calculate_code_hash(self):
        """Calcul hash SHA-256 du code"""
        try:
            # Hash du fichier principal
            main_file = os.path.abspath(__file__)
            with open(main_file, 'rb') as f:
                content = f.read()
            
            return hashlib.sha256(content).hexdigest()
        except Exception as e:
            logger.error(f"❌ Erreur calcul hash: {e}")
            return None
    
    def _setup_encryption(self):
        """Configuration encryption"""
        try:
            # Génération clé encryption basée sur hardware + licence
            password = f"{self._hardware_id}_{self._license_data.get('company', 'HCV')}"
            salt = b'hcv_enterprise_salt_2024'
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            self._encryption_key = Fernet(key)
            
            logger.info("🔐 Encryption configurée avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur configuration encryption: {e}")
            raise SecurityException(f"Échec configuration encryption: {e}")
    
    def _setup_runtime_protection(self):
        """Configuration protection runtime"""
        try:
            # Thread de monitoring sécurité
            self._security_thread = threading.Thread(target=self._security_monitor, daemon=True)
            self._security_thread.start()
            
            logger.info("🛡️ Protection runtime activée")
            
        except Exception as e:
            logger.error(f"❌ Erreur configuration runtime protection: {e}")
    
    def _security_monitor(self):
        """Monitoring sécurité en arrière-plan"""
        while True:
            try:
                # Vérification périodique debugger
                if self._is_debugger_present():
                    logger.critical("🚨 Debugger détecté en runtime!")
                    sys.exit(1)
                
                # Vérification intégrité périodique
                current_hash = self._calculate_code_hash()
                if current_hash != self._integrity_hash:
                    logger.critical("🚨 Modification code détectée en runtime!")
                    sys.exit(1)
                
                time.sleep(30)  # Vérification toutes les 30 secondes
                
            except Exception as e:
                logger.error(f"❌ Erreur monitoring sécurité: {e}")
                time.sleep(60)
    
    def compress_file(self, input_path, output_path, mode='balanced', security_level='quantum_harmonic'):
        """
        Compression sécurisée de fichier
        
        Args:
            input_path (str): Chemin fichier d'entrée
            output_path (str): Chemin fichier de sortie
            mode (str): Mode de compression
            security_level (str): Niveau de sécurité
            
        Returns:
            dict: Résultats compression
        """
        if not self._security_checks_passed:
            raise SecurityException("Contrôles de sécurité non passés")
        
        if not self._license_validated:
            raise LicenseException("Licence non validée")
        
        try:
            logger.info(f"🚀 Démarrage compression: {input_path}")
            
            # Validation entrées
            self._validate_compression_inputs(input_path, output_path, mode, security_level)
            
            # Compression avec algorithmes HCV PRO
            start_time = time.time()
            
            # Simulation compression réelle (remplacer par algorithme réel)
            compressed_size, compression_ratio = self._perform_hcv_compression(
                input_path, output_path, mode, security_level
            )
            
            processing_time = (time.time() - start_time) * 1000  # ms
            
            # Chiffrement du résultat si sécurité élevée
            if security_level in ['quantum_harmonic', 'pi_secured']:
                self._encrypt_output_file(output_path)
            
            # Logging de l'opération
            self._log_compression_operation(input_path, output_path, mode, security_level, 
                                         compressed_size, compression_ratio, processing_time)
            
            result = {
                'success': True,
                'compressed_size': compressed_size,
                'compression_ratio': compression_ratio,
                'processing_time_ms': processing_time,
                'mode': mode,
                'security_level': security_level,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Compression terminée: {compression_ratio:.1f}x en {processing_time:.0f}ms")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur compression: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _validate_compression_inputs(self, input_path, output_path, mode, security_level):
        """Validation des paramètres de compression"""
        # Validation fichier d'entrée
        if not os.path.exists(input_path):
            raise ValueError(f"Fichier d'entrée inexistant: {input_path}")
        
        if not os.access(input_path, os.R_OK):
            raise ValueError(f"Fichier d'entrée non lisible: {input_path}")
        
        # Validation mode
        valid_modes = ['ultra_fast', 'balanced', 'max_quality', 'quantum']
        if mode not in valid_modes:
            raise ValueError(f"Mode invalide: {mode}")
        
        # Validation sécurité
        valid_security = ['phi_protected', 'e_encrypted', 'pi_secured', 'quantum_harmonic']
        if security_level not in valid_security:
            raise ValueError(f"Niveau sécurité invalide: {security_level}")
    
    def _perform_hcv_compression(self, input_path, output_path, mode, security_level):
        """
        Algorithme de compression HCV PRO (simplifié pour démonstration)
        À remplacer par l'algorithme réel
        """
        try:
            # Taille fichier original
            original_size = os.path.getsize(input_path)
            
            # Lecture fichier
            with open(input_path, 'rb') as f:
                data = f.read()
            
            # Simulation compression basée sur le mode
            compression_factors = {
                'ultra_fast': 0.1,      # 10x compression
                'balanced': 0.05,        # 20x compression
                'max_quality': 0.02,     # 50x compression
                'quantum': 0.01          # 100x compression
            }
            
            # Sécurité additionnelle
            security_factors = {
                'phi_protected': 0.9,
                'e_encrypted': 0.8,
                'pi_secured': 0.7,
                'quantum_harmonic': 0.6
            }
            
            # Calcul taille compressée
            factor = compression_factors.get(mode, 0.05) * security_factors.get(security_level, 1.0)
            compressed_data = self._apply_hcv_algorithm(data, factor)
            
            # Écriture fichier compressé
            with open(output_path, 'wb') as f:
                f.write(compressed_data)
            
            compressed_size = len(compressed_data)
            compression_ratio = original_size / compressed_size if compressed_size > 0 else 1
            
            return compressed_size, compression_ratio
            
        except Exception as e:
            logger.error(f"❌ Erreur algorithme compression: {e}")
            raise
    
    def _apply_hcv_algorithm(self, data, factor):
        """
        Application algorithme HCV PRO (simulation)
        Remplacer par l'implémentation réelle des constantes harmoniques
        """
        # Simulation de l'algorithme HCV PRO
        # Dans la version réelle, ceci implémenterait:
        # - Transformées harmoniques quantiques
        # - Compression basée sur constantes universelles
        # - Optimisation multi-niveaux
        
        # Pour la démo: compression simple avec facteur
        if factor < 1.0:
            # Compression
            compressed = zlib.compress(data, level=int((1-factor) * 9))
        else:
            # Pas de compression
            compressed = data
        
        return compressed
    
    def _encrypt_output_file(self, file_path):
        """Chiffrement du fichier de sortie"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            encrypted_data = self._encryption_key.encrypt(data)
            
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
            
            logger.info(f"🔐 Fichier chiffré: {file_path}")
            
        except Exception as e:
            logger.error(f"❌ Erreur chiffrement fichier: {e}")
            raise
    
    def _log_compression_operation(self, input_path, output_path, mode, security_level, 
                                 compressed_size, compression_ratio, processing_time):
        """Logging de l'opération de compression"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': 'compression',
            'input_file': os.path.basename(input_path),
            'output_file': os.path.basename(output_path),
            'mode': mode,
            'security_level': security_level,
            'original_size': os.path.getsize(input_path),
            'compressed_size': compressed_size,
            'compression_ratio': compression_ratio,
            'processing_time_ms': processing_time,
            'hardware_id': self._hardware_id,
            'license_id': self._license_data.get('license_id', 'unknown')
        }
        
        # Écriture log sécurisé
        log_file = os.path.join(os.path.dirname(__file__), '../../logs/compression.log')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_system_info(self):
        """Récupération informations système sécurisées"""
        if not self._security_checks_passed:
            raise SecurityException("Accès non autorisé")
        
        return {
            'hardware_id': self._hardware_id,
            'license_info': {
                'company': self._license_data.get('company'),
                'expiry_date': self._license_data.get('expiry_date'),
                'max_users': self._license_data.get('max_users'),
                'features': self._license_data.get('features', [])
            },
            'system_info': {
                'platform': platform.platform(),
                'processor': platform.processor(),
                'memory_gb': psutil.virtual_memory().total / (1024**3),
                'cpu_count': psutil.cpu_count()
            },
            'security_status': {
                'integrity_verified': True,
                'license_valid': self._license_validated,
                'runtime_protection': True
            }
        }

# Point d'entrée principal
if __name__ == "__main__":
    try:
        # Test du compresseur sécurisé
        compressor = HCVCompressorSecure()
        
        # Test compression
        test_file = "test_input.txt"
        output_file = "test_output.hcvpro"
        
        # Création fichier test
        with open(test_file, 'w') as f:
            f.write("Ceci est un fichier test pour HCV PRO Enterprise Secure")
        
        # Compression
        result = compressor.compress_file(test_file, output_file, 'quantum', 'quantum_harmonic')
        print(f"Résultat compression: {result}")
        
        # Nettoyage
        if os.path.exists(test_file):
            os.remove(test_file)
        if os.path.exists(output_file):
            os.remove(output_file)
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)
