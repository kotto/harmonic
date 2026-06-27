#!/usr/bin/env python3
"""
Test d'intégration HCV PRO + Hermes
====================================

Script de test pour vérifier que l'intégration Hermes fonctionne correctement.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Ajouter le répertoire courant au path
sys.path.insert(0, str(Path(__file__).parent))

def test_hermes_import():
    """Test d'import des modules Hermes"""
    print("🧪 Test d'import Hermes...")
    
    try:
        # Test du nouveau module Hermes
        from hermes_integration import HermesService
        print("✅ Hermes integration importée avec succès")
        
        # Test de compatibilité rétrograde
        from openclaw_integration import OpenClawService
        print("✅ Compatibilité rétrograde OpenClaw -> Hermes fonctionnelle")
        
        return True
    except ImportError as e:
        print(f"❌ Erreur import: {e}")
        return False

def test_hermes_service():
    """Test du service Hermes"""
    print("\n🧪 Test du service Hermes...")
    
    try:
        from hermes_integration import HermesService
        
        # Créer et démarrer le service
        service = HermesService()
        service.start()
        print("✅ Service Hermes démarré")
        
        # Obtenir les métriques
        stats = service.get_stats()
        print(f"✅ Métriques obtenues: {stats}")
        
        # Arrêter le service
        service.stop()
        print("✅ Service Hermes arrêté")
        
        return True
    except Exception as e:
        print(f"❌ Erreur service Hermes: {e}")
        return False

async def test_hcv_hermes_integration():
    """Test de l'intégration complète HCV + Hermes"""
    print("\n🧪 Test intégration HCV + Hermes...")
    
    try:
        # Configuration de test
        device_config = {
            'device_id': 'test_device_001',
            'hermes_config_path': '~/.hermes',
            'hermes_workspace': './test_workspace',
            'device_info': {
                'ram_gb': 8,
                'storage_gb': 256,
                'cpu_cores': 8,
                'has_hermes': True
            }
        }
        
        # Import de l'intégration (mode simulation)
        from hcv_openclaw_integration import HCVHermesIntegration
        
        # Créer l'intégration
        integration = HCVHermesIntegration(device_config)
        print("✅ Intégration HCV + Hermes créée")
        
        # Test de détection de profil
        profile = integration.detect_device_profile()
        print(f"✅ Profil device détecté: {profile.name}")
        
        # Test scan manuel des médias
        media_files = integration.manual_media_scan()
        print(f"✅ Scan média manuel: {len(media_files)} fichiers trouvés")
        
        return True
    except Exception as e:
        print(f"❌ Erreur intégration HCV + Hermes: {e}")
        return False

def test_requirements():
    """Test des dépendances"""
    print("\n🧪 Test des dépendances...")
    
    requirements_file = Path(__file__).parent / 'requirements.txt'
    
    if not requirements_file.exists():
        print("❌ Fichier requirements.txt introuvable")
        return False
    
    with open(requirements_file, 'r') as f:
        content = f.read()
    
    if 'hermes-agent' in content:
        print("✅ Hermes agent trouvé dans requirements.txt")
        return True
    else:
        print("❌ Hermes agent non trouvé dans requirements.txt")
        return False

async def main():
    """Fonction principale de test"""
    print("🚀 Test d'intégration HCV PRO + Hermes")
    print("=" * 50)
    
    # Configuration logging
    logging.basicConfig(level=logging.INFO)
    
    tests = [
        ("Import Hermes", test_hermes_import),
        ("Service Hermes", test_hermes_service),
        ("Intégration HCV + Hermes", test_hcv_hermes_integration),
        ("Dépendances", test_requirements),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur inattendue dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Résultat: {passed}/{total} tests passés")
    
    if passed == total:
        print("🎉 Tous les tests sont passés! L'intégration Hermes est fonctionnelle.")
        return True
    else:
        print("⚠️ Certains tests ont échoué. Vérifiez la configuration.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
