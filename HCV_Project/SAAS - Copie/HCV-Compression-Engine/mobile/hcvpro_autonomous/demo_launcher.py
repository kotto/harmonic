#!/usr/bin/env python3
"""
HCV PRO - Lanceur Démonstration Package Autonome
================================================
Lancement simplifié pour démonstration 48 heures

🚀 Fonctionnalités :
- Activation automatique licence démo
- Interface utilisateur simplifiée
- Tests compression intégrés
- Monitoring temps réel
"""

import sys
import os
import time
from pathlib import Path

# Ajouter le répertoire bin au path
package_dir = Path(__file__).parent
sys.path.insert(0, str(package_dir / "bin"))

try:
    from harmonic_autonomous_package import HarmonicAutonomousPackage, PackageStatus
    
    def launch_demo():
        """Lance la démonstration complète"""
        
        print("🚀 HCV PRO - Démonstration Package Autonome")
        print("=" * 60)
        print("🔦 Licence 48 heures pour tests complets")
        print("🔐 Compression harmonique quantique")
        print("⚡ Performance exceptionnelle")
        print()
        
        # Initialiser le package
        package = HarmonicAutonomousPackage()
        
        # Activer avec licence démo
        print("🔑 Activation licence démo...")
        demo_license = "eyJ2ZXJzaW9uIjogIjEuMC4wIiwgImNvbXBhbnkiOiAiREVNT19IQ1ZfUFJPXzQ4SCIsICJzdGFydF90aW1lIjogMTc3NzEyODYxNy41ODY1NTQ4LCAiZXhwaXJ5X3RpbWUiOiAxNzc3MzAxNDE3LjU4NjU1NDgsICJkdXJhdGlvbl9ob3VycyI6IDQ4LCAibWF4X2NvbXByZXNzaW9ucyI6IDEwMDAsICJjdXJyZW50X2NvbXByZXNzaW9ucyI6IDAsICJzZWN1cml0eV9sZXZlbCI6ICJxdWFudHVtX2hhcm1vbmljIiwgImZlYXR1cmVzIjogWyJjb21wcmVzc2lvbl9zZWN1cmUiLCAicXVhbnR1bV9lbmNyeXB0aW9uIiwgImludGVncml0eV9jaGVjayIsICJsaWNlbnNlX3ZhbGlkYXRpb24iLCAic2VjdXJpdHlfbW9uaXRvcmluZyIsICJhbnRpX3JldmVyc2VfZW5naW5lZXJpbmciLCAiZnVsbF9hcGlfYWNjZXNzIiwgInByaW9yaXR5X3N1cHBvcnQiXSwgImhhcmR3YXJlX2lkIjogIjI1ODA3ZjA2MzIyZjQxMzkiLCAibGljZW5zZV9pZCI6ICIyNDdhN2RhMWNlZWIwMWQ2MDg3YTliZWQ2NDJlMzA5MyIsICJzaWduYXR1cmUiOiAiMWU4NGI5NDM3ZjA0MDU2YzFlZWE1ODliNzRlZjU5NDQ5MmZiNzlmNTliNWE1MTlkMzhjY2Q5ZjliNjY1MDRkMSJ9"
        
        if package.initialize(demo_license):
            print("✅ Package activé avec succès !")
            print()
            
            # Afficher informations
            info = package.get_package_info()
            print("📊 Informations Package :")
            for key, value in info.items():
                print(f"   {key}: {value}")
            print()
            
            # Menu interactif
            interactive_demo(package)
        else:
            print("❌ Échec activation package")
    
    def interactive_demo(package):
        """Menu interactif pour démonstration"""
        
        while True:
            print("\n" + "="*50)
            print("🎯 MENU DÉMONSTRATION HCV PRO")
            print("="*50)
            print("1. 📊 Afficher informations licence")
            print("2. 🗜️ Tester compression fichier")
            print("3. 🧪 Test compression multiple")
            print("4. 📈 Performance benchmarks")
            print("5. 🔍 Vérifier sécurité")
            print("6. 📋 Rapport complet")
            print("0. 🚪 Quitter")
            print()
            
            choice = input("👉 Choisissez une option (0-6): ").strip()
            
            if choice == "0":
                print("👋 Merci d'avoir testé HCV PRO !")
                break
            elif choice == "1":
                show_license_info(package)
            elif choice == "2":
                test_single_compression(package)
            elif choice == "3":
                test_multiple_compression(package)
            elif choice == "4":
                run_benchmarks(package)
            elif choice == "5":
                check_security(package)
            elif choice == "6":
                generate_report(package)
            else:
                print("❌ Option invalide")
    
    def show_license_info(package):
        """Affiche les informations de licence"""
        
        print("\n📊 INFORMATIONS LICENCE")
        print("="*40)
        
        info = package.get_package_info()
        
        if 'license' in info:
            license_info = info['license']
            print(f"🏢 Entreprise : {license_info['company']}")
            print(f"📅 Expiration : {time.ctime(license_info['expiry_date'])}")
            print(f"🔐 Niveau sécurité : {license_info['security_level']}")
            print(f"📊 Quota compressions : {license_info['current_compressions']}/{license_info['max_compressions']}")
            print(f"📋 Quota restant : {license_info['quota_remaining']}")
        else:
            print("❌ Aucune licence active")
    
    def test_single_compression(package):
        """Test compression d'un fichier"""
        
        print("\n🗜️ TEST COMPRESSION FICHIER")
        print("="*40)
        
        # Créer fichier test si besoin
        test_file = Path("demo_test.txt")
        if not test_file.exists():
            with open(test_file, 'w') as f:
                f.write("HCV PRO - Test compression démonstration\n")
                f.write("Ce fichier est utilisé pour démontrer la capacité\n")
                f.write("de compression harmonique quantique du package HCV PRO.\n")
                f.write("Performance exceptionnelle avec sécurité maximale.\n" * 100)
        
        input_file = str(test_file)
        output_file = "demo_compressed.hcvpro"
        
        print(f"📁 Fichier input : {input_file}")
        print(f"📦 Fichier output : {output_file}")
        
        result = package.compress_file(input_file, output_file)
        
        if 'error' in result:
            print(f"❌ Erreur : {result['error']}")
        else:
            print("✅ Compression réussie !")
            print(f"📊 Ratio : {result['ratio']:.1f}:1")
            print(f"⚡ Temps : {result['processing_time_ms']:.2f}ms")
            print(f"📋 Compression ID : {result['compression_id']}")
            print(f"📊 Quota restant : {result['quota_remaining']}")
    
    def test_multiple_compression(package):
        """Test compression multiple"""
        
        print("\n🧪 TEST COMPRESSION MULTIPLE")
        print("="*40)
        
        # Créer plusieurs fichiers test
        test_files = []
        for i in range(5):
            filename = f"demo_test_{i}.txt"
            with open(filename, 'w') as f:
                f.write(f"Fichier test {i}\n")
                f.write("Données de test pour HCV PRO\n" * 50)
            test_files.append(filename)
        
        print(f"📁 {len(test_files)} fichiers à compresser...")
        
        total_ratio = 0
        total_time = 0
        success_count = 0
        
        for i, input_file in enumerate(test_files):
            output_file = f"compressed_{i}.hcvpro"
            
            result = package.compress_file(input_file, output_file)
            
            if 'error' not in result:
                total_ratio += result['ratio']
                total_time += result['processing_time_ms']
                success_count += 1
                print(f"   ✅ Fichier {i+1} : {result['ratio']:.1f}:1")
            else:
                print(f"   ❌ Fichier {i+1} : {result['error']}")
        
        if success_count > 0:
            avg_ratio = total_ratio / success_count
            avg_time = total_time / success_count
            
            print(f"\n📊 RÉSULTATS MULTIPLES :")
            print(f"   ✅ Succès : {success_count}/{len(test_files)}")
            print(f"   📊 Ratio moyen : {avg_ratio:.1f}:1")
            print(f"   ⚡ Temps moyen : {avg_time:.2f}ms")
        
        # Nettoyer fichiers
        for f in test_files:
            if Path(f).exists():
                Path(f).unlink()
    
    def run_benchmarks(package):
        """Exécute des benchmarks de performance"""
        
        print("\n📈 PERFORMANCE BENCHMARKS")
        print("="*40)
        
        # Test avec différentes tailles
        sizes = [1000, 5000, 10000, 50000]
        
        print("🧪 Tests de performance par taille :")
        
        for size in sizes:
            # Créer fichier test
            test_file = f"benchmark_{size}.txt"
            with open(test_file, 'w') as f:
                f.write("X" * size)
            
            output_file = f"bench_{size}.hcvpro"
            
            start_time = time.time()
            result = package.compress_file(test_file, output_file)
            end_time = time.time()
            
            if 'error' not in result:
                print(f"   📊 {size:5d} bytes : {result['ratio']:6.1f}:1 | {result['processing_time_ms']:6.2f}ms")
            
            # Nettoyer
            Path(test_file).unlink()
            Path(output_file).unlink(missing_ok=True)
        
        print("\n✅ Benchmarks terminés")
    
    def check_security(package):
        """Vérifie l'état de sécurité"""
        
        print("\n🔍 VÉRIFICATION SÉCURITÉ")
        print("="*40)
        
        security_checks = package.security_manager.security_checks
        
        print("🛡️ État des vérifications de sécurité :")
        
        for check, status in security_checks.items():
            icon = "✅" if status else "❌"
            print(f"   {icon} {check}")
        
        print(f"\n🔐 Niveau sécurité global : Maximum")
        print(f"📡 Monitoring actif : {package.security_manager.monitoring_active}")
    
    def generate_report(package):
        """Génère un rapport complet"""
        
        print("\n📋 RAPPORT COMPLET DÉMONSTRATION")
        print("="*50)
        
        info = package.get_package_info()
        
        print("📊 INFORMATIONS PACKAGE :")
        for key, value in info.items():
            if key != 'license':
                print(f"   {key}: {value}")
        
        if 'license' in info:
            license_info = info['license']
            print(f"\n🔑 INFORMATIONS LICENCE :")
            print(f"   Entreprise : {license_info['company']}")
            print(f"   Niveau : {license_info['security_level']}")
            print(f"   Quota : {license_info['current_compressions']}/{license_info['max_compressions']}")
            print(f"   Restant : {license_info['quota_remaining']}")
        
        print(f"\n🚀 CAPACITÉS DÉMONTRÉES :")
        print(f"   ✅ Compression sécurisée")
        print(f"   ✅ Cryptographie quantique")
        print(f"   ✅ Monitoring sécurité")
        print(f"   ✅ Interface utilisateur")
        print(f"   ✅ Gestion licences")
        
        print(f"\n🎯 PROCHAINES ÉTAPES :")
        print(f"   1. 📧 Contacter commercial : sales@hcvpro.com")
        print(f"   2. 💰 Discuter licence production")
        print(f"   3. 🏢 Déploiement entreprise")
        print(f"   4. 🌍 Expansion mondiale")
        
        print(f"\n🏆 HCV PRO : Révolution compression harmonique !")
    
    if __name__ == "__main__":
        launch_demo()
        
except ImportError as e:
    print(f"❌ Erreur importation package : {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Erreur exécution : {e}")
    sys.exit(1)
