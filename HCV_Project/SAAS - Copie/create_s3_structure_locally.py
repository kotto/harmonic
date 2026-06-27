#!/usr/bin/env python3
"""
🚀 CRÉATION DE LA STRUCTURE S3 LOCALE
Crée une structure S3 locale avec tous les modèles Harmonic AI
"""

import os
import sys
import json
import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class LocalStructureResult:
    """Résultat de la création de structure locale"""
    category: str
    files_copied: int
    total_size: int
    success: bool
    error: str = None

class LocalS3StructureCreator:
    """Créateur de structure S3 locale pour Harmonic AI"""
    
    def __init__(self):
        """Initialisation du créateur de structure locale"""
        
        print("🚀 CRÉATION DE STRUCTURE S3 LOCALE HARMONIC AI")
        print("=" * 60)
        
        # Configuration
        self.base_path = Path("local_s3_structure")
        self.harmonic_path = Path("harmonic_ai")
        
        # Création du répertoire de base
        self.base_path.mkdir(exist_ok=True)
        
        print(f"📁 Répertoire de base: {self.base_path}")
        
        # Configuration des modèles à structurer
        self.models_to_structure = self._configure_models()
    
    def _configure_models(self) -> Dict[str, List[str]]:
        """Configure les modèles à structurer localement"""
        
        print(f"\n📋 CONFIGURATION DES MODÈLES À STRUCTURER")
        print("-" * 50)
        
        models = {}
        
        # Modèles principaux Harmonic AI
        if self.harmonic_path.exists():
            print(f"📁 Analyse des modèles depuis: {self.harmonic_path}")
            
            # Foundation
            foundation_path = self.harmonic_path / "foundation"
            if foundation_path.exists():
                foundation_files = list(foundation_path.rglob('*'))
                foundation_files = [f for f in foundation_files if f.is_file()]
                models["foundation"] = foundation_files
                print(f"   📂 foundation: {len(foundation_files)} fichiers")
            
            # Core
            core_path = self.harmonic_path / "core"
            if core_path.exists():
                core_files = list(core_path.rglob('*'))
                core_files = [f for f in core_files if f.is_file()]
                models["core"] = core_files
                print(f"   📂 core: {len(core_files)} fichiers")
            
            # API
            api_path = self.harmonic_path / "api"
            if api_path.exists():
                api_files = list(api_path.rglob('*'))
                api_files = [f for f in api_files if f.is_file()]
                models["api"] = api_files
                print(f"   📂 api: {len(api_files)} fichiers")
            
            # Deployment
            deployment_path = self.harmonic_path / "deployment"
            if deployment_path.exists():
                deployment_files = list(deployment_path.rglob('*'))
                deployment_files = [f for f in deployment_files if f.is_file()]
                models["deployment"] = deployment_files
                print(f"   📂 deployment: {len(deployment_files)} fichiers")
            
            # Domains
            domains_path = self.harmonic_path / "domains"
            if domains_path.exists():
                for domain_dir in domains_path.iterdir():
                    if domain_dir.is_dir():
                        domain_files = list(domain_dir.rglob('*'))
                        domain_files = [f for f in domain_files if f.is_file()]
                        models[domain_dir.name] = domain_files
                        print(f"   📂 domains/{domain_dir.name}: {len(domain_files)} fichiers")
        
        # Données structurées (batch output)
        batch_path = Path("batch_output")
        if batch_path.exists():
            print(f"📁 Ajout des données batch depuis: {batch_path}")
            
            for domain_dir in batch_path.iterdir():
                if domain_dir.is_dir():
                    domain_files = list(domain_dir.rglob('*'))
                    domain_files = [f for f in domain_files if f.is_file()]
                    models[f"batch_{domain_dir.name}"] = domain_files
                    print(f"   📂 batch/{domain_dir.name}: {len(domain_files)} fichiers")
        
        # Données simples réelles
        simple_real_path = Path("simple_real_output")
        if simple_real_path.exists():
            print(f"📁 Ajout des données simples réelles depuis: {simple_real_path}")
            
            for domain_dir in simple_real_path.iterdir():
                if domain_dir.is_dir():
                    domain_files = list(domain_dir.rglob('*'))
                    domain_files = [f for f in domain_files if f.is_file()]
                    models[f"simple_real_{domain_dir.name}"] = domain_files
                    print(f"   📂 simple_real/{domain_dir.name}: {len(domain_files)} fichiers")
        
        # Données réelles corrigées
        real_batch_path = Path("real_batch_output_fixed")
        if real_batch_path.exists():
            print(f"📁 Ajout des données réelles corrigées depuis: {real_batch_path}")
            
            for domain_dir in real_batch_path.iterdir():
                if domain_dir.is_dir():
                    domain_files = list(domain_dir.rglob('*'))
                    domain_files = [f for f in domain_files if f.is_file()]
                    models[f"real_fixed_{domain_dir.name}"] = domain_files
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
            "harmonic_ai_simulation_manifest.json",
            "s3_upload_manifest.json",
            "download_report.json"
        ]
        
        existing_reports = []
        for report_file in report_files:
            if Path(report_file).exists():
                existing_reports.append(Path(report_file))
        
        if existing_reports:
            models["reports"] = existing_reports
            print(f"   📂 reports: {len(existing_reports)} fichiers")
        
        # Total des fichiers
        total_files = sum(len(files) for files in models.values())
        print(f"\n📊 Total des fichiers à structurer: {total_files}")
        
        return models
    
    def copy_file_to_s3_structure(self, source_file: Path, s3_key: str) -> tuple:
        """Copie un fichier vers la structure S3 locale"""
        
        try:
            # Construction du chemin de destination
            dest_path = self.base_path / s3_key.replace('/', os.sep)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copie du fichier
            shutil.copy2(source_file, dest_path)
            
            # Calcul du hash pour vérification
            with open(dest_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            file_size = dest_path.stat().st_size
            
            return True, file_size, file_hash, None
            
        except Exception as e:
            return False, 0, "", str(e)
    
    def structure_category(self, category: str, source_files: List[Path]) -> LocalStructureResult:
        """Structure tous les fichiers d'une catégorie"""
        
        print(f"\n📂 STRUCTURATION CATÉGORIE: {category.upper()}")
        print("-" * 50)
        
        files_copied = 0
        total_size = 0
        errors = []
        
        for i, source_file in enumerate(source_files, 1):
            print(f"   📂 [{i}/{len(source_files)}] {source_file.name}")
            
            # Construction de la clé S3
            if category.startswith("batch_"):
                s3_key = f"structured_data/{category[6:]}/{source_file.name}"
            elif category.startswith("simple_real_"):
                s3_key = f"simple_real_output/{category[12:]}/{source_file.name}"
            elif category.startswith("real_fixed_"):
                s3_key = f"real_structured_data/{category[12:]}/{source_file.name}"
            elif category == "reports":
                s3_key = f"reports/{source_file.name}"
            else:
                # Pour les domaines principaux
                if source_file.is_relative_to(self.harmonic_path):
                    relative_path = source_file.relative_to(self.harmonic_path)
                    s3_key = str(relative_path).replace('\\', '/')
                else:
                    # Pour les autres catégories
                    s3_key = f"{category}/{source_file.name}"
            
            # Copie du fichier
            success, size, file_hash, error = self.copy_file_to_s3_structure(source_file, s3_key)
            
            if success:
                files_copied += 1
                total_size += size
                size_kb = size / 1024
                print(f"      ✅ {size_kb:.1f} KB (hash: {file_hash[:8]}...)")
            else:
                errors.append(f"{source_file.name}: {error}")
                print(f"      ❌ Erreur: {error}")
        
        result = LocalStructureResult(
            category=category,
            files_copied=files_copied,
            total_size=total_size,
            success=files_copied > 0,
            error="; ".join(errors) if errors else None
        )
        
        print(f"\n📊 STATISTIQUES {category.upper()}:")
        print(f"   ✅ Fichiers copiés: {files_copied}/{len(source_files)}")
        print(f"   💾 Taille totale: {total_size/1024:.1f} KB")
        
        return result
    
    def create_complete_structure(self) -> Dict[str, LocalStructureResult]:
        """Crée la structure S3 locale complète"""
        
        print(f"\n🚀 CRÉATION COMPLÈTE DE LA STRUCTURE S3 LOCALE")
        print("=" * 60)
        print(f"📁 Destination: {self.base_path}")
        print("=" * 60)
        
        all_results = {}
        total_files = 0
        successful_copies = 0
        total_size = 0
        
        # Structuration par catégorie
        for category, source_files in self.models_to_structure.items():
            category_result = self.structure_category(category, source_files)
            all_results[category] = category_result
            
            total_files += len(source_files)
            successful_copies += category_result.files_copied
            total_size += category_result.total_size
        
        # Création du manifeste local
        self._create_local_manifest(all_results, total_files, successful_copies, total_size)
        
        return all_results
    
    def _create_local_manifest(self, results: Dict[str, LocalStructureResult], 
                             total_files: int, successful_copies: int, 
                             total_size: int):
        """Crée un manifeste de la structure locale"""
        
        print(f"\n🏆 MANIFESTE DE LA STRUCTURE LOCALE")
        print("=" * 60)
        
        # Statistiques globales
        success_rate = successful_copies / total_files if total_files > 0 else 0
        
        print(f"📊 Fichiers copiés: {successful_copies}/{total_files}")
        print(f"📈 Taux de succès: {success_rate:.1%}")
        print(f"💾 Taille totale: {total_size/1024:.1f} KB")
        
        # Création du manifeste
        manifest = {
            'local_structure_summary': {
                'timestamp': datetime.now().isoformat(),
                'base_path': str(self.base_path),
                'total_files': total_files,
                'successful_copies': successful_copies,
                'success_rate': success_rate,
                'total_size_bytes': total_size,
                'categories_count': len(results)
            },
            'category_results': {}
        }
        
        # Détails par catégorie
        for category, result in results.items():
            manifest['category_results'][category] = asdict(result)
        
        # Sauvegarde du manifeste
        manifest_file = self.base_path / "local_structure_manifest.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Manifeste sauvegardé: {manifest_file}")
        
        # Création d'un index des fichiers
        self._create_file_index()
        
        # Affichage de la structure finale
        self._display_final_structure()
    
    def _create_file_index(self):
        """Crée un index de tous les fichiers dans la structure"""
        
        print(f"\n📋 CRÉATION DE L'INDEX DES FICHIERS")
        print("-" * 40)
        
        file_index = {}
        
        # Parcours de tous les fichiers dans la structure
        for file_path in self.base_path.rglob('*'):
            if file_path.is_file():
                # Calcul des métadonnées
                relative_path = file_path.relative_to(self.base_path)
                file_size = file_path.stat().st_size
                file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
                
                file_index[str(relative_path)] = {
                    'size_bytes': file_size,
                    'hash_sha256': file_hash,
                    'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
        
        # Sauvegarde de l'index
        index_file = self.base_path / "file_index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(file_index, f, indent=2, ensure_ascii=False)
        
        print(f"   📋 Index créé: {len(file_index)} fichiers indexés")
        print(f"   💾 Index sauvegardé: {index_file}")
    
    def _display_final_structure(self):
        """Affiche la structure finale"""
        
        print(f"\n📂 STRUCTURE FINALE CRÉÉE")
        print("=" * 40)
        
        # Affichage de l'arborescence
        def display_tree(path: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0):
            if current_depth >= max_depth:
                return
            
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
            
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                
                if item.is_file():
                    size_kb = item.stat().st_size / 1024
                    print(f"{prefix}{current_prefix}📄 {item.name} ({size_kb:.1f} KB)")
                else:
                    print(f"{prefix}{current_prefix}📂 {item.name}/")
                    
                    if not is_last:
                        next_prefix = prefix + "│   "
                    else:
                        next_prefix = prefix + "    "
                    
                    display_tree(item, next_prefix, max_depth, current_depth + 1)
        
        # Affichage limité à 2 niveaux de profondeur
        display_tree(self.base_path, max_depth=2)
        
        # Statistiques finales
        total_files = len(list(self.base_path.rglob('*')))
        total_files = sum(1 for f in self.base_path.rglob('*') if f.is_file())
        total_size = sum(f.stat().st_size for f in self.base_path.rglob('*') if f.is_file())
        
        print(f"\n📊 STATISTIQUES FINALES:")
        print(f"   📁 Fichiers totaux: {total_files}")
        print(f"   💾 Taille totale: {total_size/1024:.1f} KB")
        print(f"   📂 Répertoires: {len([d for d in self.base_path.rglob('*') if d.is_dir()])}")

def main():
    """Fonction principale"""
    
    print("🚀 CRÉATION DE STRUCTURE S3 LOCALE HARMONIC AI")
    print("=" * 60)
    print("🌊 Création d'une structure S3 locale avec tous les modèles")
    print("=" * 60)
    
    try:
        # Création du structureur
        creator = LocalS3StructureCreator()
        
        # Création de la structure complète
        results = creator.create_complete_structure()
        
        print(f"\n🌊 STRUCTURE LOCALE CRÉÉE!")
        print(f"🚀 Modèles disponibles dans: {creator.base_path}")
        print(f"📋 Prêt pour upload S3 quand les credentials seront valides")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
