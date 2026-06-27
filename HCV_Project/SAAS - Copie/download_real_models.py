#!/usr/bin/env python3
"""
🚀 TÉLÉCHARGEMENT DES MODÈLES RÉELS HARMONIC AI DEPUIS AWS S3
Télécharge tous les modèles complets et réels depuis S3
"""

import os
import sys
import json
import time
import boto3
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Configuration AWS
AWS_REGION = "us-east-1"
HARMONIC_BUCKET = "harmonic-ai-knowledge-base"

@dataclass
class DownloadResult:
    """Résultat de téléchargement"""
    s3_key: str
    local_path: str
    success: bool
    size: int
    download_time: float
    error: Optional[str] = None

class HarmonicS3Downloader:
    """Téléchargeur de modèles Harmonic AI depuis AWS S3"""
    
    def __init__(self):
        """Initialisation du téléchargeur S3"""
        
        print("🚀 INITIALISATION TÉLÉCHARGEUR HARMONIC AI S3")
        print("=" * 60)
        
        # Configuration AWS
        self.bucket_name = HARMONIC_BUCKET
        self.region = AWS_REGION
        
        # Initialisation client S3
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=self.region
            )
            print(f"✅ Client S3 initialisé pour la région: {self.region}")
            print(f"📦 Bucket cible: {self.bucket_name}")
        except Exception as e:
            print(f"❌ Erreur initialisation S3: {str(e)}")
            raise
        
        # Création des répertoires locaux
        self.setup_local_directories()
        
        # Configuration des modèles à télécharger
        self.models_to_download = self._configure_models()
    
    def setup_local_directories(self):
        """Crée les répertoires locaux pour les modèles"""
        
        print("\n📁 CRÉATION DES RÉPÉRTOIRES LOCAUX")
        print("-" * 40)
        
        self.base_path = Path("downloaded_models")
        self.base_path.mkdir(exist_ok=True)
        
        # Répertoires pour chaque type de modèle
        directories = [
            "foundation",
            "core", 
            "mathematics",
            "code",
            "visual",
            "specialization",
            "api",
            "deployment",
            "structured_data",
            "real_structured_data",
            "simple_real_output",
            "trained_models",
            "checkpoints",
            "configurations"
        ]
        
        for directory in directories:
            dir_path = self.base_path / directory
            dir_path.mkdir(exist_ok=True)
            print(f"   📂 {directory}/")
        
        print(f"✅ Répertoires créés dans: {self.base_path}")
    
    def _configure_models(self) -> Dict[str, List[str]]:
        """Configure les modèles à télécharger"""
        
        print("\n📋 CONFIGURATION DES MODÈLES À TÉLÉCHARGER")
        print("-" * 50)
        
        models = {
            # Modèles Foundation
            "foundation": [
                "foundation/harmonic_foundation.py",
                "foundation/tests_foundation.py",
                "foundation/foundation_constants.json",
                "foundation/foundation_validation.json"
            ],
            
            # Modèles Core
            "core": [
                "core/harmonic_resonance_engine.py",
                "core/harmonic_resonance_engine_fixed.py",
                "core/prompt_comprehension_engine.py",
                "core/launch_prompt_system.py",
                "core/core_config.json",
                "core/resonance_matrix.npy"
            ],
            
            # Modèles Mathematics
            "mathematics": [
                "mathematics/dual_math_generator.py",
                "mathematics/harmonic_hybrid_generator.py",
                "mathematics/harmonic_math_system.py",
                "mathematics/mathstral_aws_generator.py",
                "mathematics/launch_dual_math.py",
                "mathematics/launch_hybrid_generation.py",
                "mathematics/launch_math_generation.py",
                "mathematics/launch_mathstral_aws.py",
                "mathematics/math_models.json",
                "mathematics/calibration_data.json"
            ],
            
            # Modèles Code
            "code": [
                "code/dual_code_generator.py",
                "code/harmonic_code_generator.py",
                "code/harmonic_quantum.py",
                "code/harmonic_quantum_examples.py",
                "code/launch_dual_code.py",
                "code/code_patterns.json",
                "code/quantum_states.json"
            ],
            
            # Modèles Visual
            "visual": [
                "visual/harmonic_s3_visual_system.py",
                "visual/launch_visual_generation.py",
                "visual/visual_config.json",
                "visual/harmonic_patterns.json"
            ],
            
            # Modèles Specialization
            "specialization": [
                "specialization/harmonic_specialization_engine.py",
                "specialization/launch_specialization.py",
                "specialization/README_SPECIALIZATION.md",
                "specialization/specialization_config.json",
                "specialization/trained_models/harmonic_specialized_model.pt",
                "specialization/trained_models/specialization_checkpoint.pth",
                "specialization/data/specialization_data.json"
            ],
            
            # Modèles API
            "api": [
                "api/harmonic_api.py",
                "api/api_config.json",
                "api/openapi_spec.json"
            ],
            
            # Modèles Deployment
            "deployment": [
                "deployment/upload_to_s3.py",
                "deployment/aws_infrastructure_plan.md",
                "deployment/deployment_cost_analysis.md",
                "deployment/deployment_scripts.sh",
                "deployment/infrastructure_config.json"
            ],
            
            # Données structurées
            "structured_data": [
                "structured_data/foundation/foundation_processed.json",
                "structured_data/foundation/foundation_metadata.csv",
                "structured_data/foundation/foundation_manifest.json",
                "structured_data/core/core_processed.json",
                "structured_data/core/core_metadata.csv",
                "structured_data/core/core_manifest.json",
                "structured_data/mathematics/mathematics_processed.json",
                "structured_data/mathematics/mathematics_metadata.csv",
                "structured_data/mathematics/mathematics_manifest.json",
                "structured_data/code/code_processed.json",
                "structured_data/code/code_metadata.csv",
                "structured_data/code/code_manifest.json",
                "structured_data/visual/visual_processed.json",
                "structured_data/visual/visual_metadata.csv",
                "structured_data/visual/visual_manifest.json",
                "structured_data/specialization/specialization_processed.json",
                "structured_data/specialization/specialization_metadata.csv",
                "structured_data/specialization/specialization_manifest.json",
                "structured_data/api/api_processed.json",
                "structured_data/api/api_metadata.csv",
                "structured_data/api/api_manifest.json",
                "structured_data/deployment/deployment_processed.json",
                "structured_data/deployment/deployment_metadata.csv",
                "structured_data/deployment/deployment_manifest.json"
            ],
            
            # Données réelles structurées
            "real_structured_data": [
                "real_structured_data/foundation/foundation_real_processed.json",
                "real_structured_data/foundation/foundation_real_metadata.csv",
                "real_structured_data/foundation/foundation_real_manifest.json",
                "real_structured_data/core/core_real_processed.json",
                "real_structured_data/core/core_real_metadata.csv",
                "real_structured_data/core/core_real_manifest.json",
                "real_structured_data/mathematics/mathematics_real_processed.json",
                "real_structured_data/mathematics/mathematics_real_metadata.csv",
                "real_structured_data/mathematics/mathematics_real_manifest.json",
                "real_structured_data/code/code_real_processed.json",
                "real_structured_data/code/code_real_metadata.csv",
                "real_structured_data/code/code_real_manifest.json",
                "real_structured_data/visual/visual_real_processed.json",
                "real_structured_data/visual/visual_real_metadata.csv",
                "real_structured_data/visual/visual_real_manifest.json",
                "real_structured_data/specialization/specialization_real_processed.json",
                "real_structured_data/specialization/specialization_real_metadata.csv",
                "real_structured_data/specialization/specialization_real_manifest.json",
                "real_structured_data/api/api_real_processed.json",
                "real_structured_data/api/api_real_metadata.csv",
                "real_structured_data/api/api_real_manifest.json",
                "real_structured_data/deployment/deployment_real_processed.json",
                "real_structured_data/deployment/deployment_real_metadata.csv",
                "real_structured_data/deployment/deployment_real_manifest.json"
            ],
            
            # Données simples réelles
            "simple_real_output": [
                "simple_real_output/foundation/foundation_simple_real.json",
                "simple_real_output/foundation/foundation_simple_real.csv",
                "simple_real_output/foundation/foundation_simple_manifest.json",
                "simple_real_output/core/core_simple_real.json",
                "simple_real_output/core/core_simple_real.csv",
                "simple_real_output/core/core_simple_manifest.json",
                "simple_real_output/mathematics/mathematics_simple_real.json",
                "simple_real_output/mathematics/mathematics_simple_real.csv",
                "simple_real_output/mathematics/mathematics_simple_manifest.json",
                "simple_real_output/code/code_simple_real.json",
                "simple_real_output/code/code_simple_real.csv",
                "simple_real_output/code/code_simple_manifest.json",
                "simple_real_output/visual/visual_simple_real.json",
                "simple_real_output/visual/visual_simple_real.csv",
                "simple_real_output/visual/visual_simple_manifest.json",
                "simple_real_output/specialization/specialization_simple_real.json",
                "simple_real_output/specialization/specialization_simple_real.csv",
                "simple_real_output/specialization/specialization_simple_manifest.json",
                "simple_real_output/api/api_simple_real.json",
                "simple_real_output/api/api_simple_real.csv",
                "simple_real_output/api/api_simple_manifest.json",
                "simple_real_output/deployment/deployment_simple_real.json",
                "simple_real_output/deployment/deployment_simple_real.csv",
                "simple_real_output/deployment/deployment_simple_manifest.json"
            ],
            
            # Modèles entraînés
            "trained_models": [
                "trained_models/harmonic_foundation_model.pt",
                "trained_models/resonance_engine_model.pt",
                "trained_models/math_generator_model.pt",
                "trained_models/code_generator_model.pt",
                "trained_models/visual_generator_model.pt",
                "trained_models/specialization_model.pt",
                "trained_models/api_model.pt",
                "trained_models/deployment_model.pt"
            ],
            
            # Checkpoints
            "checkpoints": [
                "checkpoints/foundation_checkpoint.pth",
                "checkpoints/core_checkpoint.pth",
                "checkpoints/mathematics_checkpoint.pth",
                "checkpoints/code_checkpoint.pth",
                "checkpoints/visual_checkpoint.pth",
                "checkpoints/specialization_checkpoint.pth",
                "checkpoints/api_checkpoint.pth",
                "checkpoints/deployment_checkpoint.pth"
            ],
            
            # Configurations
            "configurations": [
                "configurations/global_config.json",
                "configurations/harmonic_constants.json",
                "configurations/model_parameters.json",
                "configurations/training_config.json",
                "configurations/deployment_config.json"
            ]
        }
        
        total_files = sum(len(files) for files in models.values())
        print(f"📊 Total des fichiers à télécharger: {total_files}")
        
        for category, files in models.items():
            print(f"   📂 {category}: {len(files)} fichiers")
        
        return models
    
    def download_file(self, s3_key: str, local_path: str) -> DownloadResult:
        """Télécharge un fichier spécifique depuis S3"""
        
        start_time = time.time()
        
        try:
            # Création du répertoire local si nécessaire
            local_file = Path(local_path)
            local_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Téléchargement depuis S3
            self.s3_client.download_file(
                Bucket=self.bucket_name,
                Key=s3_key,
                Filename=str(local_file)
            )
            
            # Vérification du fichier téléchargé
            if local_file.exists():
                file_size = local_file.stat().st_size
                download_time = time.time() - start_time
                
                return DownloadResult(
                    s3_key=s3_key,
                    local_path=str(local_file),
                    success=True,
                    size=file_size,
                    download_time=download_time
                )
            else:
                return DownloadResult(
                    s3_key=s3_key,
                    local_path=str(local_file),
                    success=False,
                    size=0,
                    download_time=time.time() - start_time,
                    error="Fichier non trouvé après téléchargement"
                )
                
        except Exception as e:
            return DownloadResult(
                s3_key=s3_key,
                local_path=str(local_path),
                success=False,
                size=0,
                download_time=time.time() - start_time,
                error=str(e)
            )
    
    def download_category(self, category: str, s3_keys: List[str]) -> Dict[str, DownloadResult]:
        """Télécharge tous les fichiers d'une catégorie"""
        
        print(f"\n📥 TÉLÉCHARGEMENT CATÉGORIE: {category.upper()}")
        print("-" * 50)
        
        results = {}
        
        for i, s3_key in enumerate(s3_keys, 1):
            print(f"   📥 [{i}/{len(s3_keys)}] {s3_key}")
            
            # Construction du chemin local
            local_path = self.base_path / s3_key
            
            # Téléchargement
            result = self.download_file(s3_key, str(local_path))
            results[s3_key] = result
            
            # Affichage du résultat
            if result.success:
                size_kb = result.size / 1024
                print(f"      ✅ {size_kb:.1f} KB en {result.download_time:.2f}s")
            else:
                print(f"      ❌ Erreur: {result.error}")
        
        return results
    
    def download_all_models(self) -> Dict[str, Dict[str, DownloadResult]]:
        """Télécharge tous les modèles"""
        
        print(f"\n🚀 TÉLÉCHARGEMENT COMPLET DES MODÈLES HARMONIC AI")
        print("=" * 60)
        print(f"📦 Bucket: {self.bucket_name}")
        print(f"🌍 Région: {self.region}")
        print(f"📁 Destination: {self.base_path}")
        print("=" * 60)
        
        all_results = {}
        total_files = 0
        successful_downloads = 0
        total_size = 0
        total_time = 0
        
        # Téléchargement par catégorie
        for category, s3_keys in self.models_to_download.items():
            category_results = self.download_category(category, s3_keys)
            all_results[category] = category_results
            
            # Statistiques de la catégorie
            category_successful = sum(1 for r in category_results.values() if r.success)
            category_size = sum(r.size for r in category_results.values() if r.success)
            category_time = sum(r.download_time for r in category_results.values())
            
            total_files += len(s3_keys)
            successful_downloads += category_successful
            total_size += category_size
            total_time += category_time
            
            print(f"\n📊 STATISTIQUES {category.upper()}:")
            print(f"   ✅ Succès: {category_successful}/{len(s3_keys)}")
            print(f"   💾 Taille: {category_size/1024:.1f} KB")
            print(f"   ⏱️ Temps: {category_time:.2f}s")
        
        # Rapport global
        self._create_download_report(all_results, total_files, successful_downloads, total_size, total_time)
        
        return all_results
    
    def _create_download_report(self, results: Dict[str, Dict[str, DownloadResult]], 
                              total_files: int, successful_downloads: int, 
                              total_size: int, total_time: float):
        """Crée un rapport de téléchargement"""
        
        print(f"\n🏆 RAPPORT GLOBAL DE TÉLÉCHARGEMENT")
        print("=" * 60)
        
        # Statistiques globales
        success_rate = successful_downloads / total_files if total_files > 0 else 0
        avg_speed = total_size / total_time if total_time > 0 else 0
        
        print(f"📊 Fichiers téléchargés: {successful_downloads}/{total_files}")
        print(f"📈 Taux de succès: {success_rate:.1%}")
        print(f"💾 Taille totale: {total_size/1024:.1f} KB")
        print(f"⏱️ Temps total: {total_time:.2f}s")
        print(f"🚀 Vitesse moyenne: {avg_speed/1024:.1f} KB/s")
        
        # Statistiques par catégorie
        print(f"\n📋 DÉTAIL PAR CATÉGORIE:")
        for category, category_results in results.items():
            category_successful = sum(1 for r in category_results.values() if r.success)
            category_total = len(category_results)
            category_size = sum(r.size for r in category_results.values() if r.success)
            
            status = "✅" if category_successful == category_total else "⚠️"
            print(f"   {status} {category}: {category_successful}/{category_total} ({category_size/1024:.1f} KB)")
        
        # Erreurs
        failed_downloads = []
        for category, category_results in results.items():
            for s3_key, result in category_results.items():
                if not result.success:
                    failed_downloads.append((category, s3_key, result.error))
        
        if failed_downloads:
            print(f"\n❌ ERREURS DE TÉLÉCHARGEMENT ({len(failed_downloads)}):")
            for category, s3_key, error in failed_downloads[:10]:  # Limite à 10 erreurs
                print(f"   ❌ {category}/{s3_key}: {error}")
            if len(failed_downloads) > 10:
                print(f"   ... et {len(failed_downloads) - 10} autres erreurs")
        
        # Sauvegarde du rapport
        report_data = {
            'download_summary': {
                'timestamp': datetime.now().isoformat(),
                'bucket': self.bucket_name,
                'region': self.region,
                'total_files': total_files,
                'successful_downloads': successful_downloads,
                'success_rate': success_rate,
                'total_size_bytes': total_size,
                'total_time_seconds': total_time,
                'average_speed_kb_per_second': avg_speed / 1024
            },
            'category_results': {}
        }
        
        for category, category_results in results.items():
            report_data['category_results'][category] = {
                s3_key: asdict(result) for s3_key, result in category_results.items()
            }
        
        report_file = self.base_path / "download_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Rapport sauvegardé: {report_file}")
        print(f"📁 Modèles téléchargés dans: {self.base_path}")

def main():
    """Fonction principale"""
    
    print("🚀 TÉLÉCHARGEMENT DES MODÈLES RÉELS HARMONIC AI")
    print("=" * 60)
    print("🌊 Téléchargement des modèles complets et réels depuis AWS S3")
    print("=" * 60)
    
    try:
        # Création du téléchargeur
        downloader = HarmonicS3Downloader()
        
        # Téléchargement de tous les modèles
        results = downloader.download_all_models()
        
        print(f"\n🌊 TÉLÉCHARGEMENT TERMINÉ!")
        print(f"🚀 Vérifiez les modèles dans: {downloader.base_path}")
        
    except Exception as e:
        print(f"❌ Erreur lors du téléchargement: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
