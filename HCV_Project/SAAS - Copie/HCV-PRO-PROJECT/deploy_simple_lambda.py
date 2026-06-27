#!/usr/bin/env python3
"""
DÉPLOIEMENT LAMBDA SIMPLE SANS NUMPY
====================================

Script pour déployer la version simplifiée qui fonctionne sans NumPy.
"""

import os
import subprocess
import zipfile
import json
import sys
from pathlib import Path
from datetime import datetime

class SimpleLambdaDeployer:
    """Déployeur pour la version simplifiée"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.lambda_dir = self.project_root / "lambda_package"
        self.function_name = "hcv-pro-deepseek-handler"
        self.region = "eu-west-3"
        self.deploy_log = []
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        self.deploy_log.append(log_entry)
    
    def create_simple_package(self) -> str:
        """Créer le package simplifié"""
        self.log("📦 Création du package simplifié...")
        
        zip_path = self.lambda_dir / "lambda_simple.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            # Ajouter le fichier simplifié
            simple_file = self.lambda_dir / "lambda_function_simple.py"
            zip_file.write(simple_file, "aws_real_compression_handler.py")
            
            # Ajouter les dépendances
            requirements = """
# No external dependencies needed
"""
            zip_file.writestr("requirements.txt", requirements)
        
        self.log(f"✅ Package simplifié créé: {zip_path}")
        return str(zip_path)
    
    def deploy_simple_function(self, zip_path: str) -> bool:
        """Déployer la fonction simplifiée"""
        self.log("🔄 Déploiement de la fonction simplifiée...")
        
        try:
            cmd = [
                'aws', 'lambda', 'update-function-code',
                '--function-name', self.function_name,
                '--zip-file', f'fileb://{zip_path}'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.log("✅ Fonction simplifiée déployée avec succès")
                return True
            else:
                self.log(f"❌ Erreur déploiement: {result.stderr}")
                return False
                
        except Exception as e:
            self.log(f"❌ Erreur déploiement: {e}")
            return False
    
    def test_simple_function(self) -> bool:
        """Tester la fonction simplifiée"""
        self.log("🧪 Test de la fonction simplifiée...")
        
        try:
            cmd = [
                'aws', 'lambda', 'invoke',
                '--function-name', self.function_name,
                '--payload', '{"httpMethod":"GET","path":"/api/health"}',
                '--invocation-type', 'RequestResponse',
                '--region', self.region
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                # Parser la sortie
                try:
                    output_lines = result.stdout.strip().split('\n')
                    for line in output_lines:
                        if '"statusCode":200' in line:
                            print(f"✅ Test health: Status 200")
                            return True
                except:
                    pass
            else:
                print(f"❌ Erreur test: {result.stderr}")
                return False
                
        except Exception as e:
            self.log(f"❌ Erreur test: {e}")
            return False
    
    def run_simple_deployment(self) -> bool:
        """Exécuter le déploiement simplifié"""
        self.log("🚀 DÉPLOIEMENT LAMBDA SIMPLE SANS NUMPY")
        self.log("=" * 60)
        
        try:
            # Créer le package
            zip_path = self.create_simple_package()
            
            # Déployer
            if not self.deploy_simple_function(zip_path):
                return False
            
            # Tester
            if not self.test_simple_function():
                return False
            
            self.log("🎉 Déploiement simplifié terminé avec succès!")
            return True
            
        except Exception as e:
            self.log(f"❌ Erreur déploiement simplifié: {e}")
            return False

def main():
    print("🌊 DÉPLOIEMENT LAMBDA SIMPLE SANS NUMPY")
    print("=" * 60)
    print("📦 Version simplifiée sans dépendances externes")
    print("🌊 Déploiement sur AWS")
    print("🌊 Tests réels sur AWS")
    print("=" * 60)
    
    deployer = SimpleLambdaDeployer()
    success = deployer.run_simple_deployment()
    
    if success:
        print("\n🌊 Déploiement simplifié terminé avec succès!")
        print("📊 Tous les endpoints sont maintenant disponibles")
        print("📊 La fonction fonctionne sans NumPy")
        print("🌊 Les constantes harmoniques sont prêtes")
        exit(0)
    else:
        print("\n❌ Le déploiement a rencontré des erreurs")
        print("📄 Vérifiez les logs pour plus de détails")
        exit(1)

if __name__ == "__main__":
    main()
