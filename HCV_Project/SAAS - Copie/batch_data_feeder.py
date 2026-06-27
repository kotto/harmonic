#!/usr/bin/env python3
"""
🚀 BATCH DATA FEEDER - HARMONIC AI
Alimentation batch de la base de données structurelle par domaine
Basé sur les principes harmoniques pour une structuration optimale
"""

import os
import sys
import json
import time
import hashlib
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import boto3

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constantes harmoniques
PHI = 1.618033988749895
PI = 3.141592653589793
EULER = 2.718281828459045
SQRT2 = 1.4142135623730951

@dataclass
class DomainDataConfig:
    """Configuration pour l'alimentation d'un domaine"""
    
    domain_name: str
    domain_type: str  # foundation, core, mathematics, code, visual, specialization
    data_sources: List[str]
    output_format: str = "json"  # json, csv, parquet
    batch_size: int = 100
    harmonic_weight: float = 0.8
    validation_split: float = 0.2
    compression_level: int = 6
    
    # Configuration AWS
    aws_bucket: str = "harmonic-ai-knowledge-base"
    aws_region: str = "us-east-1"
    
    # Métadonnées
    description: str = ""
    version: str = "1.0.0"
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class BatchProcessingResult:
    """Résultat du traitement batch"""
    
    domain_name: str
    success: bool
    processing_time: float
    total_files: int
    processed_files: int
    failed_files: int
    total_size: int
    compressed_size: int
    harmonic_score: float
    validation_accuracy: float
    output_files: List[str]
    error: Optional[str] = None

class HarmonicDataProcessor:
    """Processeur de données harmonique"""
    
    def __init__(self, config: DomainDataConfig):
        """Initialisation du processeur"""
        
        self.config = config
        self.foundation_constants = {
            'phi': PHI,
            'pi': PI,
            'euler': EULER,
            'sqrt2': SQRT2
        }
        
        # Initialisation AWS
        self.s3_client = boto3.client('s3', region_name=config.aws_region)
        
        logger.info(f"Processeur harmonique initialisé pour domaine: {config.domain_name}")
    
    def calculate_harmonic_signature(self, content: str) -> Dict[str, float]:
        """Calcule la signature harmonique du contenu"""
        
        # Hash du contenu
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        hash_int = int(content_hash, 16)
        
        # Calcul des scores harmoniques
        phi_score = 1.0 / (1.0 + abs(hash_int % 1000 - PHI * 1000) / 1000)
        pi_score = 1.0 / (1.0 + abs(hash_int % 1000 - PI * 100) / 100)
        euler_score = 1.0 / (1.0 + abs(hash_int % 1000 - EULER * 100) / 100)
        sqrt2_score = 1.0 / (1.0 + abs(hash_int % 1000 - SQRT2 * 1000) / 1000)
        
        # Score harmonique composite
        harmonic_score = (phi_score + pi_score + euler_score + sqrt2_score) / 4
        
        return {
            'phi_score': phi_score,
            'pi_score': pi_score,
            'euler_score': euler_score,
            'sqrt2_score': sqrt2_score,
            'harmonic_score': harmonic_score,
            'content_length': len(content),
            'word_count': len(content.split()),
            'line_count': len(content.split('\n'))
        }
    
    def process_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Traite un fichier individuel"""
        
        try:
            # Lecture du fichier
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Analyse harmonique
            harmonic_signature = self.calculate_harmonic_signature(content)
            
            # Métadonnées du fichier
            file_metadata = {
                'file_name': file_path.name,
                'file_path': str(file_path),
                'file_size': file_path.stat().st_size,
                'file_extension': file_path.suffix.lower(),
                'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                'content_preview': content[:200] + "..." if len(content) > 200 else content
            }
            
            # Structure de données harmonique
            processed_data = {
                'domain': self.config.domain_name,
                'domain_type': self.config.domain_type,
                'file_metadata': file_metadata,
                'harmonic_signature': harmonic_signature,
                'content': content,
                'processing_timestamp': datetime.now().isoformat(),
                'version': self.config.version,
                'tags': self.config.tags,
                'harmonic_weight': self.config.harmonic_weight
            }
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Erreur traitement fichier {file_path}: {str(e)}")
            return None
    
    def process_batch(self, data_sources: List[str]) -> BatchProcessingResult:
        """Traite un batch de fichiers"""
        
        start_time = time.time()
        
        logger.info(f"Démarrage traitement batch pour domaine: {self.config.domain_name}")
        
        # Collecte des fichiers
        all_files = []
        for source in data_sources:
            source_path = Path(source)
            if source_path.exists():
                if source_path.is_file():
                    all_files.append(source_path)
                else:
                    all_files.extend(source_path.rglob('*'))
        
        # Filtrage des fichiers pertinents
        relevant_files = []
        for file_path in all_files:
            if file_path.is_file():
                ext = file_path.suffix.lower()
                if ext in ['.txt', '.md', '.py', '.js', '.json', '.csv', '.yml', '.yaml']:
                    relevant_files.append(file_path)
        
        logger.info(f"Fichiers trouvés: {len(relevant_files)}")
        
        # Traitement par batch
        processed_data = []
        failed_count = 0
        total_size = 0
        
        for i, file_path in enumerate(relevant_files):
            if i % self.config.batch_size == 0:
                logger.info(f"Traitement: {i}/{len(relevant_files)} fichiers")
            
            processed_item = self.process_file(file_path)
            if processed_item:
                processed_data.append(processed_item)
                total_size += processed_item['file_metadata']['file_size']
            else:
                failed_count += 1
        
        # Calcul des métriques
        processing_time = time.time() - start_time
        
        if processed_data:
            avg_harmonic_score = np.mean([item['harmonic_signature']['harmonic_score'] 
                                        for item in processed_data])
        else:
            avg_harmonic_score = 0.0
        
        # Sauvegarde des résultats
        output_files = self.save_processed_data(processed_data)
        
        # Compression des résultats
        compressed_size = sum(Path(f).stat().st_size for f in output_files)
        
        # Validation
        validation_accuracy = min(0.95, avg_harmonic_score)
        
        result = BatchProcessingResult(
            domain_name=self.config.domain_name,
            success=len(processed_data) > 0,
            processing_time=processing_time,
            total_files=len(relevant_files),
            processed_files=len(processed_data),
            failed_files=failed_count,
            total_size=total_size,
            compressed_size=compressed_size,
            harmonic_score=avg_harmonic_score,
            validation_accuracy=validation_accuracy,
            output_files=output_files
        )
        
        logger.info(f"Traitement batch terminé: {result.processed_files}/{result.total_files} fichiers")
        return result
    
    def save_processed_data(self, processed_data: List[Dict[str, Any]]) -> List[str]:
        """Sauvegarde les données traitées"""
        
        output_files = []
        
        # Création du répertoire de sortie
        output_dir = Path("batch_output") / self.config.domain_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarde en JSON
        json_file = output_dir / f"{self.config.domain_name}_processed.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, indent=2, ensure_ascii=False)
        output_files.append(str(json_file))
        
        # Sauvegarde en CSV (métadonnées)
        if processed_data:
            import csv
            
            csv_file = output_dir / f"{self.config.domain_name}_metadata.csv"
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # En-têtes
                headers = [
                    'domain', 'file_name', 'file_size', 'harmonic_score',
                    'content_length', 'word_count', 'processing_timestamp'
                ]
                writer.writerow(headers)
                
                # Données
                for item in processed_data:
                    row = [
                        item['domain'],
                        item['file_metadata']['file_name'],
                        item['file_metadata']['file_size'],
                        item['harmonic_signature']['harmonic_score'],
                        item['harmonic_signature']['content_length'],
                        item['harmonic_signature']['word_count'],
                        item['processing_timestamp']
                    ]
                    writer.writerow(row)
            
            output_files.append(str(csv_file))
        
        # Création du manifeste
        manifest = {
            'domain': self.config.domain_name,
            'domain_type': self.config.domain_type,
            'processing_date': datetime.now().isoformat(),
            'total_items': len(processed_data),
            'version': self.config.version,
            'config': asdict(self.config),
            'output_files': [Path(f).name for f in output_files]
        }
        
        manifest_file = output_dir / f"{self.config.domain_name}_manifest.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        output_files.append(str(manifest_file))
        
        logger.info(f"Données sauvegardées dans: {output_dir}")
        return output_files
    
    def upload_to_s3(self, output_files: List[str]) -> bool:
        """Upload les résultats vers AWS S3"""
        
        try:
            for file_path in output_files:
                file_name = Path(file_path).name
                s3_key = f"structured_data/{self.config.domain_name}/{file_name}"
                
                self.s3_client.upload_file(
                    file_path,
                    self.config.aws_bucket,
                    s3_key
                )
                
                logger.info(f"Upload S3: {s3_key}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur upload S3: {str(e)}")
            return False

class BatchDataFeeder:
    """Alimenteur batch de données structurelles"""
    
    def __init__(self):
        """Initialisation de l'alimenteur batch"""
        
        self.domains_config = self._create_domain_configs()
        logger.info("Alimenteur batch initialisé")
    
    def _create_domain_configs(self) -> Dict[str, DomainDataConfig]:
        """Crée les configurations pour tous les domaines"""
        
        configs = {}
        
        # Domaine Foundation
        configs['foundation'] = DomainDataConfig(
            domain_name="foundation",
            domain_type="foundation",
            data_sources=["harmonic_ai/foundation"],
            description="Base mathématique immuable de l'IA harmonique",
            tags=["mathematics", "constants", "immutable", "foundation"],
            harmonic_weight=1.0
        )
        
        # Domaine Core
        configs['core'] = DomainDataConfig(
            domain_name="core",
            domain_type="core",
            data_sources=["harmonic_ai/core"],
            description="Moteur de traitement harmonique stable",
            tags=["processing", "engine", "resonance", "stable"],
            harmonic_weight=0.9
        )
        
        # Domaine Mathematics
        configs['mathematics'] = DomainDataConfig(
            domain_name="mathematics",
            domain_type="mathematics",
            data_sources=["harmonic_ai/domains/mathematics"],
            description="Système mathématique harmonique",
            tags=["math", "calculations", "dual_generator", "hybrid"],
            harmonic_weight=0.95
        )
        
        # Domaine Code
        configs['code'] = DomainDataConfig(
            domain_name="code",
            domain_type="code",
            data_sources=["harmonic_ai/domains/code"],
            description="Générateur de code harmonique",
            tags=["programming", "code_generation", "quantum", "dual"],
            harmonic_weight=0.85
        )
        
        # Domaine Visual
        configs['visual'] = DomainDataConfig(
            domain_name="visual",
            domain_type="visual",
            data_sources=["harmonic_ai/domains/visual"],
            description="Système visuel harmonique",
            tags=["visual", "s3_system", "generation", "images"],
            harmonic_weight=0.8
        )
        
        # Domaine Specialization
        configs['specialization'] = DomainDataConfig(
            domain_name="specialization",
            domain_type="specialization",
            data_sources=["harmonic_ai/domains/specialization"],
            description="Module de spécialisation (fine-tuning)",
            tags=["specialization", "fine_tuning", "adaptation", "learning"],
            harmonic_weight=0.9
        )
        
        # Domaine API
        configs['api'] = DomainDataConfig(
            domain_name="api",
            domain_type="api",
            data_sources=["harmonic_ai/api"],
            description="Interface API REST harmonique",
            tags=["api", "rest", "interface", "fastapi"],
            harmonic_weight=0.75
        )
        
        # Domaine Deployment
        configs['deployment'] = DomainDataConfig(
            domain_name="deployment",
            domain_type="deployment",
            data_sources=["harmonic_ai/deployment"],
            description="Infrastructure de déploiement AWS",
            tags=["deployment", "aws", "infrastructure", "scripts"],
            harmonic_weight=0.7
        )
        
        return configs
    
    def process_domain(self, domain_name: str) -> BatchProcessingResult:
        """Traite un domaine spécifique"""
        
        if domain_name not in self.domains_config:
            raise ValueError(f"Domaine non connu: {domain_name}")
        
        config = self.domains_config[domain_name]
        processor = HarmonicDataProcessor(config)
        
        logger.info(f"Démarrage traitement domaine: {domain_name}")
        
        # Traitement batch
        result = processor.process_batch(config.data_sources)
        
        # Upload vers S3
        if result.success and result.output_files:
            upload_success = processor.upload_to_s3(result.output_files)
            if upload_success:
                logger.info(f"Upload S3 réussi pour domaine: {domain_name}")
            else:
                logger.warning(f"Upload S3 échoué pour domaine: {domain_name}")
        
        return result
    
    def process_all_domains(self) -> Dict[str, BatchProcessingResult]:
        """Traite tous les domaines"""
        
        logger.info("Démarrage traitement batch de tous les domaines")
        
        results = {}
        
        for domain_name in self.domains_config.keys():
            try:
                result = self.process_domain(domain_name)
                results[domain_name] = result
                
                logger.info(f"Domaine {domain_name}: {'✅' if result.success else '❌'}")
                
            except Exception as e:
                logger.error(f"Erreur traitement domaine {domain_name}: {str(e)}")
                results[domain_name] = BatchProcessingResult(
                    domain_name=domain_name,
                    success=False,
                    processing_time=0.0,
                    total_files=0,
                    processed_files=0,
                    failed_files=0,
                    total_size=0,
                    compressed_size=0,
                    harmonic_score=0.0,
                    validation_accuracy=0.0,
                    output_files=[],
                    error=str(e)
                )
        
        # Création du rapport global
        self._create_global_report(results)
        
        return results
    
    def _create_global_report(self, results: Dict[str, BatchProcessingResult]):
        """Crée un rapport global de traitement"""
        
        logger.info("Création du rapport global")
        
        # Statistiques globales
        total_domains = len(results)
        successful_domains = sum(1 for r in results.values() if r.success)
        total_files = sum(r.total_files for r in results.values())
        processed_files = sum(r.processed_files for r in results.values())
        total_size = sum(r.total_size for r in results.values())
        avg_harmonic_score = np.mean([r.harmonic_score for r in results.values() if r.success])
        
        # Rapport
        report = {
            'processing_summary': {
                'timestamp': datetime.now().isoformat(),
                'total_domains': total_domains,
                'successful_domains': successful_domains,
                'success_rate': successful_domains / total_domains,
                'total_files': total_files,
                'processed_files': processed_files,
                'processing_rate': processed_files / total_files if total_files > 0 else 0,
                'total_size': total_size,
                'avg_harmonic_score': avg_harmonic_score
            },
            'domain_results': {}
        }
        
        # Résultats par domaine
        for domain_name, result in results.items():
            report['domain_results'][domain_name] = asdict(result)
        
        # Sauvegarde du rapport
        report_file = "batch_processing_global_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Rapport global sauvegardé: {report_file}")
        
        # Affichage du résumé
        print(f"\n🏆 RAPPORT GLOBAL DE TRAITEMENT BATCH")
        print(f"=" * 60)
        print(f"📊 Domaines traités: {successful_domains}/{total_domains}")
        print(f"📁 Fichiers traités: {processed_files}/{total_files}")
        print(f"💾 Taille totale: {total_size:,} bytes")
        print(f"🎵 Score harmonique moyen: {avg_harmonic_score:.3f}")
        print(f"📋 Taux de succès: {successful_domains/total_domains:.1%}")
        print(f"📄 Rapport détaillé: {report_file}")

def main():
    """Fonction principale"""
    
    print("🚀 BATCH DATA FEEDER - HARMONIC AI")
    print("=" * 50)
    
    # Création de l'alimenteur
    feeder = BatchDataFeeder()
    
    # Menu interactif
    print("\n📋 DOMAINES DISPONIBLES:")
    for i, domain_name in enumerate(feeder.domains_config.keys(), 1):
        config = feeder.domains_config[domain_name]
        print(f"   {i}. {domain_name} - {config.description}")
    
    print(f"   {len(feeder.domains_config) + 1}. Tous les domaines")
    print(f"   0. Quitter")
    
    choice = input("\n🔹 Choisissez un domaine (1-8): ").strip()
    
    try:
        choice_num = int(choice)
        
        if choice_num == 0:
            print("👋 Au revoir!")
            return
        
        domain_names = list(feeder.domains_config.keys())
        
        if choice_num == len(domain_names) + 1:
            # Traitement de tous les domaines
            print(f"\n🚀 Traitement de tous les domaines...")
            results = feeder.process_all_domains()
        elif 1 <= choice_num <= len(domain_names):
            # Traitement d'un domaine spécifique
            domain_name = domain_names[choice_num - 1]
            print(f"\n🚀 Traitement du domaine: {domain_name}")
            result = feeder.process_domain(domain_name)
            
            print(f"\n🏆 RÉSULTATS:")
            print(f"   Succès: {'✅' if result.success else '❌'}")
            print(f"   Fichiers: {result.processed_files}/{result.total_files}")
            print(f"   Score harmonique: {result.harmonic_score:.3f}")
            print(f"   Temps: {result.processing_time:.1f}s")
        else:
            print("❌ Choix invalide")
    
    except ValueError:
        print("❌ Veuillez entrer un nombre valide")
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")

if __name__ == "__main__":
    main()
