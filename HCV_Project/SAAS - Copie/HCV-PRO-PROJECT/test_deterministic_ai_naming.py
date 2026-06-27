#!/usr/bin/env python3
"""
Test de validation du renommage vers Deterministic AI
"""

import json
import os
from pathlib import Path

def test_model_naming():
    """Tester que tous les fichiers ont été correctement renommés"""
    print("🧪 TEST DE VALIDATION - RENOMMAGE DETERMINISTIC AI")
    print("=" * 60)
    
    model_path = Path("models/deepseek_real")
    
    # Vérifier que le répertoire existe
    if not model_path.exists():
        print("❌ Le répertoire du modèle n'existe pas")
        return False
    
    # Tests de fichiers
    tests = [
        {
            "name": "README.md",
            "path": model_path / "README.md",
            "checks": ["Deterministic AI", "Harmonic AI Corp", "0% hallucination", "100% deterministic"]
        },
        {
            "name": "config.json", 
            "path": model_path / "config.json",
            "checks": ["Deterministic AI", "Harmonic AI Corp", "deterministic_moe_harmonic"]
        },
        {
            "name": "tokenizer_config.json",
            "path": model_path / "tokenizer_config.json", 
            "checks": ["Deterministic AI Tokenizer", "Harmonic AI Corp", "DeterministicAITokenizer"]
        }
    ]
    
    success_count = 0
    total_tests = len(tests)
    
    for test in tests:
        print(f"\n📋 Test: {test['name']}")
        
        if not test['path'].exists():
            print(f"   ❌ Fichier manquant: {test['path']}")
            continue
        
        try:
            with open(test['path'], 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Vérifier le format JSON si applicable
            if test['path'].suffix == '.json':
                try:
                    json_data = json.loads(content)
                    print(f"   ✅ JSON valide")
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON invalide: {e}")
                    continue
            
            # Vérifier les chaînes attendues
            all_checks_passed = True
            for check in test['checks']:
                if check in content:
                    print(f"   ✅ Trouvé: '{check}'")
                else:
                    print(f"   ❌ Manquant: '{check}'")
                    all_checks_passed = False
            
            if all_checks_passed:
                success_count += 1
                print(f"   🎉 Test {test['name']} RÉUSSI!")
            else:
                print(f"   ⚠️ Test {test['name']} PARTIEL")
                
        except Exception as e:
            print(f"   ❌ Erreur lecture: {e}")
    
    # Vérifier qu'aucun ancien nom ne subsiste
    print(f"\n🔍 VÉRIFICATION ANCIENS NOMS")
    
    all_files = list(model_path.rglob("*"))
    old_names_found = []
    
    for file_path in all_files:
        if file_path.is_file():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                old_names = ['deepseek', 'Deepseek', 'DEEPSEEK']
                for old_name in old_names:
                    if old_name in content:
                        old_names_found.append(f"{file_path.name}: {old_name}")
                        
            except Exception:
                pass  # Ignorer les fichiers binaires
    
    if old_names_found:
        print("⚠️ Anciens noms trouvés:")
        for item in old_names_found:
            print(f"   - {item}")
    else:
        print("✅ Aucun ancien nom trouvé!")
    
    # Résultat final
    print(f"\n" + "=" * 60)
    print(f"📊 RÉSULTATS DU TEST")
    print(f"✅ Tests réussis: {success_count}/{total_tests}")
    print(f"🔍 Anciens noms trouvés: {len(old_names_found)}")
    
    if success_count == total_tests and len(old_names_found) == 0:
        print("🎉 TOUS LES TESTS RÉUSSIS!")
        print("🌊 Le modèle est correctement renommé en 'Deterministic AI by Harmonic AI Corp'")
        return True
    else:
        print("⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
        return False

def show_model_info():
    """Afficher les informations du modèle renommé"""
    print("\n" + "=" * 60)
    print("🌊 INFORMATIONS DU MODÈLE RENOMMÉ")
    print("=" * 60)
    
    config_path = Path("models/deepseek_real/config.json")
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            print(f"📝 Nom du modèle: {config.get('model_name', 'N/A')}")
            print(f"🏢 Compagnie: {config.get('company', 'N/A')}")
            print(f"🎯 Type: {config.get('model_type', 'N/A')}")
            print(f"📊 Version: {config.get('model_version', 'N/A')}")
            print(f"📅 Date: {config.get('created_date', 'N/A')}")
            
            # Afficher les constantes harmoniques
            if 'harmonic_constants' in config:
                print(f"\n🔢 Constantes Harmoniques:")
                for key, value in config['harmonic_constants'].items():
                    print(f"   {key}: {value}")
            
            # Afficher les métriques de performance
            if 'performance_metrics' in config:
                print(f"\n📊 Métriques de Performance:")
                for key, value in config['performance_metrics'].items():
                    print(f"   {key}: {value}")
                    
        except Exception as e:
            print(f"❌ Erreur lecture config: {e}")
    else:
        print("❌ Fichier config.json non trouvé")

if __name__ == "__main__":
    success = test_model_naming()
    show_model_info()
    
    if success:
        print("\n🚀 LE MODÈLE 'DETERMINISTIC AI' EST PRÊT POUR LE LANCEMENT!")
        exit(0)
    else:
        print("\n⚠️ VÉRIFICATIONS SUPPLÉMENTAIRES REQUISES")
        exit(1)
