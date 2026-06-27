#!/usr/bin/env python3
"""
🚀 UPLOAD DES MODÈLES LOCAUX VERS AWS S3
Upload les modèles locaux complets et réels vers S3
"""

import os
import sys
import json
import time
import boto3
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Configuration AWS
AWS_REGION = "us-east-1"
HARMONIC_BUCKET = "harmonic-ai-knowledge-base"

@dataclass
class UploadResult:
    """Résultat d'upload"""
    local_path: str
    s3_key: str
    success: bool
    size: int
    upload_time: float
    error: Optional[str] = None

class HarmonicS3Uploader:
    """Upload des modèles Harmonic AI vers AWS S3"""
    
    def __init__(self):
        """Initialisation de l'uploader S3"""
        
        print("🚀 INITIALISATION UPLOAD HARMONIC AI S3")
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
        
        # Vérification/création du bucket
        self._ensure_bucket_exists()
        
        # Configuration des modèles à uploader
        self.local_models = self._configure_local_models()
    
    def _ensure_bucket_exists(self):
        """Vérifie et crée le bucket si nécessaire"""
        
        print(f"\n📦 VÉRIFICATION DU BUCKET")
        print("-" * 30)
        
        try:
            # Test d'accès au bucket
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"✅ Bucket '{self.bucket_name}' accessible")
        except Exception as e:
            print(f"⚠️ Bucket non accessible: {str(e)}")
            
            # Tentative de création du bucket
            try:
                if self.region == "us-east-1":
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                else:
                    self.s3_client.create_bucket(
                        Bucket=self.bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': self.region}
                    )
                print(f"✅ Bucket '{self.bucket_name}' créé")
            except Exception as create_error:
                print(f"❌ Impossible de créer le bucket: {str(create_error)}")
                raise
    
    def _configure_local_models(self) -> Dict[str, List[str]]:
        """Configure les modèles locaux à uploader"""
        
        print(f"\n📋 CONFIGURATION DES MODÈLES LOCAUX À UPLOADER")
        print("-" * 50)
        
        models = {}
        
        # Modèles principaux Harmonic AI
        base_path = Path("harmonic_ai")
        if base_path.exists():
            print(f"📁 Ajout des modèles depuis: {base_path}")
            
            # Foundation
            foundation_path = base_path / "foundation"
            if foundation_path.exists():
                foundation_files = list(foundation_path.rglob('*'))
                foundation_files = [f for f in foundation_files if f.is_file()]
                models["foundation"] = [str(f.relative_to(base_path)) for f in foundation_files]
                print(f"   📂 foundation: {len(foundation_files)} fichiers")
            
            # Core
            core_path = base_path / "core"
            if core_path.exists():
                core_files = list(core_path.rglob('*'))
                core_files = [f for f in core_files if f.is_file()]
                models["core"] = [str(f.relative_to(base_path)) for f in core_files]
                print(f"   📂 core: {len(core_files)} fichiers")
            
            # API
            api_path = base_path / "api"
            if api_path.exists():
                api_files = list(api_path.rglob('*'))
                api_files = [f for f in api_files if f.is_file()]
                models["api"] = [str(f.relative_to(base_path)) for f in api_files]
                print(f"   📂 api: {len(api_files)} fichiers")
            
            # Deployment
            deployment_path = base_path / "deployment"
            if deployment_path.exists():
                deployment_files = list(deployment_path.rglob('*'))
                deployment_files = [f for f in deployment_files if f.is_file()]
                models["deployment"] = [str(f.relative_to(base_path)) for f in deployment_files]
                print(f"   📂 deployment: {len(deployment_files)} fichiers")
            
            # Domains
            domains_path = base_path / "domains"
            if domains_path.exists():
                for domain_dir in domains_path.iterdir():
                    if domain_dir.is_dir():
                        domain_files = list(domain_dir.rglob('*'))
                        domain_files = [f for f in domain_files if f.is_file()]
                        relative_files = [f"domains/{domain_dir.name}/{f.relative_to(domain_dir)}" for f in domain_files]
                        models[domain_dir.name] = relative_files
                        print(f"   📂 domains/{domain_dir.name}: {len(domain_files)} fichiers")
        
        # Données structurées (batch output)
        batch_path = Path("batch_output")
        if batch_path.exists():
            print(f"📁 Ajout des données batch depuis: {batch_path}")
            
            for domain_dir in batch_path.iterdir():
                if domain_dir.is_dir():
                    domain_files = list(domain_dir.rglob('*'))
                    domain_files = [f for f in domain_files if f.is_file()]
                    relative_files = [f"batch_output/{domain_dir.name}/{f.relative_to(domain_dir)}" for f in domain_files]
                    models[f"batch_{domain_dir.name}"] = relative_files
                    print(f"   📂 batch/{domain_dir.name}: {len(domain_files)} fichiers")
        
        # Données simples réelles
        simple_real_path = Path("simple_real_output")
        if simple_real_path.exists():
            print(f"📁 Ajout des données simples réelles depuis: {simple_real_path}")
            
            for domain_dir in simple_real_path.iterdir():
                if domain_dir.is_dir():
                    domain_files = list(domain_dir.rglob('*'))
                    domain_files = [f for f in domain_files if f.is_file()]
                    relative_files = [f"simple_real_output/{domain_dir.name}/{f.relative_to(domain_dir)}" for f in domain_files]
                    models[f"simple_real_{domain_dir.name}"] = relative_files
                    print(f"   📂 simple_real/{domain_dir.name}: {len(domain_files)} fichiers")
        
        # Données réelles corrigées
        real_batch_path = Path("real_batch_output_fixed")
        if real_batch_path.exists():
            print(f"📁 Ajout des données réelles corrigées depuis: {real_batch_path}")
            
            for domain_dir in real_batch_path.iterdir():
                if domain_dir.is_dir():
                    domain_files = list(domain_dir.rglob('*'))
                    domain_files = [f for f in domain_files if f.is_file()]
                    relative_files = [f"real_batch_output_fixed/{domain_dir.name}/{f.relative_to(domain_dir)}" for f in domain_files]
                    models[f"real_fixed_{domain_dir.name}"] = relative_files
                    print(f"   📂 real_fixed/{domain_dir.name}: {len(domain_files)} fichiers")
        
        # Rapports et analyses
        report_files = [
            "batch_processing_global_report.json",
            "batch_analysis_results.json",
            "simple_real_batch_report.json",
            "simple_real_analysis_results.json",
            "real_batch_processing_global_report_fixed.json",
            "specialization_test_report.json",
            "test_specialization_results_test_harmonic.json",
            "harmonic_ai_simulation_manifest.json"
        ]
        
        existing_reports = []
        for report_file in report_files:
            if Path(report_file).exists():
                existing_reports.append(report_file)
        
        if existing_reports:
            models["reports"] = existing_reports
            print(f"   📂 reports: {len(existing_reports)} fichiers")
        
        # Total des fichiers
        total_files = sum(len(files) for files in models.values())
        print(f"\n📊 Total des fichiers à uploader: {total_files}")
        
        return models
    
    def upload_file(self, local_path: str, s3_key: str) -> UploadResult:
        """Upload un fichier spécifique vers S3"""
        
        start_time = time.time()
        
        try:
            # Vérification du fichier local
            local_file = Path(local_path)
            if not local_file.exists():
                return UploadResult(
                    local_path=local_path,
                    s3_key=s3_key,
                    success=False,
                    size=0,
                    upload_time=time.time() - start_time,
                    error="Fichier local non trouvé"
                )
            
            file_size = local_file.stat().st_size
            
            # Upload vers S3
            self.s3_client.upload_file(
                Filename=str(local_file),
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            upload_time = time.time() - start_time
            
            return UploadResult(
                local_path=local_path,
                s3_key=s3_key,
                success=True,
                size=file_size,
                upload_time=upload_time
            )
            
        except Exception as e:
            return UploadResult(
                local_path=local_path,
                s3_key=s3_key,
                success=False,
                size=0,
                upload_time=time.time() - start_time,
                error=str(e)
            )
    
    def upload_category(self, category: str, local_files: List[str]) -> Dict[str, UploadResult]:
        """Upload tous les fichiers d'une catégorie"""
        
        print(f"\n📤 UPLOAD CATÉGORIE: {category.upper()}")
        print("-" * 50)
        
        results = {}
        
        for i, local_file in enumerate(local_files, 1):
            print(f"   📤 [{i}/{len(local_files)}] {local_file}")
            
            # Construction du chemin S3
            s3_key = local_file.replace('\\', '/')  # Normalisation des chemins
            
            # Upload
            result = self.upload_file(local_file, s3_key)
            results[s3_key] = result
            
            # Affichage du résultat
            if result.success:
                size_kb = result.size / 1024
                print(f"      ✅ {size_kb:.1f} KB en {result.upload_time:.2f}s")
            else:
                print(f"      ❌ Erreur: {result.error}")
        
        return results
    
    def upload_all_models(self) -> Dict[str, Dict[str, UploadResult]]:
        """Upload tous les modèles"""
        
        print(f"\n🚀 UPLOAD COMPLET DES MODÈLES HARMONIC AI")
        print("=" * 60)
        print(f"📦 Bucket: {self.bucket_name}")
        print(f"🌍 Région: {self.region}")
        print("=" * 60)
        
        all_results = {}
        total_files = 0
        successful_uploads = 0
        total_size = 0
        total_time = 0
        
        # Upload par catégorie
        for category, local_files in self.local_models.items():
            category_results = self.upload_category(category, local_files)
            all_results[category] = category_results
            
            # Statistiques de la catégorie
            category_successful = sum(1 for r in category_results.values() if r.success)
            category_size = sum(r.size for r in category_results.values() if r.success)
            category_time = sum(r.upload_time for r in category_results.values())
            
            total_files += len(local_files)
            successful_uploads += category_successful
            total_size += category_size
            total_time += category_time
            
            print(f"\n📊 STATISTIQUES {category.upper()}:")
            print(f"   ✅ Succès: {category_successful}/{len(local_files)}")
            print(f"   💾 Taille: {category_size/1024:.1f} KB")
            print(f"   ⏱️ Temps: {category_time:.2f}s")
        
        # Création du manifeste S3
        self._create_s3_manifest(all_results, total_files, successful_uploads, total_size, total_time)
        
        return all_results
    
    def _create_s3_manifest(self, results: Dict[str, Dict[str, UploadResult]], 
                           total_files: int, successful_uploads: int, 
                           total_size: int, total_time: float):
        """Crée un manifeste S3 de l'upload"""
        
        print(f"\n🏆 MANIFESTE S3 DE L'UPLOAD")
        print("=" * 60)
        
        # Statistiques globales
        success_rate = successful_uploads / total_files if total_files > 0 else 0
        avg_speed = total_size / total_time if total_time > 0 else 0
        
        print(f"📊 Fichiers uploadés: {successful_uploads}/{total_files}")
        print(f"📈 Taux de succès: {success_rate:.1%}")
        print(f"💾 Taille totale: {total_size/1024:.1f} KB")
        print(f"⏱️ Temps total: {total_time:.2f}s")
        print(f"🚀 Vitesse moyenne: {avg_speed/1024:.1f} KB/s")
        
        # Création du manifeste
        manifest = {
            'upload_summary': {
                'timestamp': datetime.now().isoformat(),
                'bucket': self.bucket_name,
                'region': self.region,
                'total_files': total_files,
                'successful_uploads': successful_uploads,
                'success_rate': success_rate,
                'total_size_bytes': total_size,
                'total_time_seconds': total_time,
                'average_speed_kb_per_second': avg_speed / 1024
            },
            'uploaded_files': {}
        }
        
        # Liste des fichiers uploadés avec succès
        for category, category_results in results.items():
            for s3_key, result in category_results.items():
                if result.success:
                    manifest['uploaded_files'][s3_key] = {
                        'category': category,
                        'size_bytes': result.size,
                        'upload_time': result.upload_time,
                        'local_path': result.local_path
                    }
        
        # Sauvegarde locale du manifeste
        manifest_file = Path("s3_upload_manifest.json")
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Manifeste local sauvegardé: {manifest_file}")
        
        # Upload du manifeste vers S3
        manifest_s3_key = "s3_upload_manifest.json"
        manifest_result = self.upload_file(str(manifest_file), manifest_s3_key)
        
        if manifest_result.success:
            print(f"✅ Manifeste uploadé sur S3: {manifest_s3_key}")
        else:
            print(f"❌ Erreur upload manifeste: {manifest_result.error}")
        
        # Affichage des erreurs
        failed_uploads = []
        for category, category_results in results.items():
            for s3_key, result in category_results.items():
                if not result.success:
                    failed_uploads.append((category, s3_key, result.error))
        
        if failed_uploads:
            print(f"\n❌ ERREURS D'UPLOAD ({len(failed_uploads)}):")
            for category, s3_key, error in failed_uploads[:10]:  # Limite à 10 erreurs
                print(f"   ❌ {category}/{s3_key}: {error}")
            if len(failed_uploads) > 10:
                print(f"   ... et {len(failed_uploads) - 10} autres erreurs")

def main():
    """Fonction principale"""
    
    print("🚀 UPLOAD DES MODÈLES LOCAUX HARMONIC AI VERS AWS S3")
    print("=" * 60)
    print("🌊 Upload des modèles complets et réels vers S3")
    print("=" * 60)
    
    try:
        # Création de l'uploader
        uploader = HarmonicS3Uploader()
        
        # Upload de tous les modèles
        results = uploader.upload_all_models()
        
        print(f"\n🌊 UPLOAD TERMINÉ!")
        print(f"🚀 Modèles disponibles sur S3: s3://{uploader.bucket_name}/")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'upload: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
