#!/usr/bin/env python3
"""
HCV PRO - Générateur de Licence Temporaire
========================================
Génère des licences de démonstration pour tests

🔐 Types de licences :
- 48 heures : Démonstration complète
- 7 jours : Essai étendu  
- 30 jours : Évaluation commerciale
- 1 an : Licence commerciale complète

📋 Fonctionnalités :
- Génération sécurisée de clés
- Validation hardware binding
- Contrôle quotas dynamiques
- Monitoring temps réel
"""

import os
import sys
import json
import time
import base64
import hashlib
import secrets
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class LicenseConfig:
    """Configuration de licence"""
    duration_hours: int
    max_compressions: int
    security_level: str
    features: list
    company: str
    hardware_id: str

class LicenseGenerator:
    """Générateur de licences HCV PRO sécurisé"""
    
    def __init__(self):
        self.secret_key = b"HCV_PRO_2026_SECURE_LICENSE_GENERATOR"
        self.version = "1.0.0"
        
        print("🔑 HCV PRO - Générateur de Licence")
        print("=" * 50)
        print(f"📦 Version : {self.version}")
        print(f"🔐 Sécurité : Maximum")
        print(f"⏰ Validité : 48 heures démonstration")
        print()
    
    def get_hardware_id(self) -> str:
        """Génère ID matériel unique"""
        try:
            import platform
            import uuid
            
            # Combiner plusieurs identifiants
            system_info = f"{platform.system()}-{platform.machine()}-{uuid.getnode()}"
            hardware_id = hashlib.sha256(system_info.encode()).hexdigest()[:16]
            
            return hardware_id
        except:
            # Fallback si pas accès
            return hashlib.sha256(self.secret_key + str(time.time()).encode()).hexdigest()[:16]
    
    def generate_license_key(self, config: LicenseConfig) -> str:
        """Génère une clé de licence sécurisée"""
        
        print(f"🔧 Génération licence pour {config.company}")
        print(f"⏰ Durée : {config.duration_hours} heures")
        print(f"📊 Quota : {config.max_compressions} compressions")
        print(f"🔐 Niveau : {config.security_level}")
        
        # Calculer expiration (48 heures à partir de maintenant)
        start_time = time.time()
        expiry_time = start_time + (config.duration_hours * 3600)
        
        # Pour démo, s'assurer que l'expiration est dans le futur
        current_time = time.time()
        if expiry_time <= current_time:
            expiry_time = current_time + (48 * 3600)  # 48 heures à partir de maintenant
        
        # Créer données licence
        license_data = {
            'version': self.version,
            'company': config.company,
            'start_time': start_time,
            'expiry_time': expiry_time,
            'duration_hours': config.duration_hours,
            'max_compressions': config.max_compressions,
            'current_compressions': 0,
            'security_level': config.security_level,
            'features': config.features,
            'hardware_id': config.hardware_id,
            'license_id': secrets.token_hex(16),
            'signature': None
        }
        
        # Ajouter signature de sécurité
        license_json = json.dumps(license_data, sort_keys=True).encode()
        signature = hashlib.sha256(license_json + self.secret_key).hexdigest()
        license_data['signature'] = signature
        
        # Encoder en base64
        license_bytes = json.dumps(license_data).encode()
        license_key = base64.b64encode(license_bytes).decode()
        
        print(f"✅ Licence générée avec succès")
        print(f"🔑 Clé : {license_key[:32]}...")
        print(f"📅 Expiration : {datetime.fromtimestamp(expiry_time).strftime('%Y-%m-%d %H:%M:%S')}")
        
        return license_key
    
    def save_license_file(self, license_key: str, filename: str = "hcv_pro_license.key"):
        """Sauvegarde la licence dans un fichier"""
        
        license_file = Path(filename)
        
        try:
            with open(license_file, 'w') as f:
                f.write(license_key)
            
            print(f"✅ Licence sauvegardée : {license_file.absolute()}")
            return str(license_file.absolute())
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde licence : {e}")
            return None
    
    def create_demo_license_48h(self, company: str = "DEMO_USER") -> str:
        """Crée une licence de démonstration 48 heures"""
        
        hardware_id = self.get_hardware_id()
        
        config = LicenseConfig(
            duration_hours=48,
            max_compressions=1000,
            security_level="quantum_harmonic",
            features=[
                "compression_secure",
                "quantum_encryption", 
                "integrity_check",
                "license_validation",
                "security_monitoring",
                "anti_reverse_engineering",
                "full_api_access",
                "priority_support"
            ],
            company=company,
            hardware_id=hardware_id
        )
        
        return self.generate_license_key(config)

def main():
    """Point d'entrée principal"""
    
    print("🚀 HCV PRO - Générateur Licence Démonstration")
    print("🔦 Licence 48 heures pour tests complets")
    print()
    
    generator = LicenseGenerator()
    
    # Générer licence 48 heures
    license_key = generator.create_demo_license_48h("DEMO_HCV_PRO_48H")
    
    # Sauvegarder licence
    license_file = generator.save_license_file(license_key)
    
    if license_file:
        print(f"\n🎯 Étapes suivantes :")
        print(f"1. 📦 Lancer l'application :")
        print(f"   python hcvpro_autonomous/hcvpro.py license {license_key[:32]}...")
        print(f"2. 🗜️ Tester compression :")
        print(f"   python hcvpro_autonomous/hcvpro.py compress input.txt output.hcvpro")
        print(f"3. 📊 Vérifier informations :")
        print(f"   python hcvpro_autonomous/hcvpro.py info")
        print(f"\n⏰ Licence valide 48 heures à partir de maintenant !")
    
    print(f"\n🏆 Licence générée avec succès !")

if __name__ == "__main__":
    main()
