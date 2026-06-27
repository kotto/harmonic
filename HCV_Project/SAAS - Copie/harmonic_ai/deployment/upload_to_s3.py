#!/usr/bin/env python3
"""
🚀 CHARGEMENT COMPLET SUR AWS S3 - DÉPLOIEMENT PROGRESSIF
Chargement de tous les modules Harmonic AI sur AWS S3 avec validation
"""

import os
import sys
import json
import time
import hashlib
import boto3
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
HARMONIC_BUCKET = os.getenv("HARMONIC_BUCKET", "harmonic-ai-knowledge-base")
BASE_PATH = Path(__file__).parent.parent

@dataclass
class UploadResult:
    """Résultat d'upload"""
    file_path: str
    s3_key: str
    success: bool
    size: int
    upload_time: float
    error: Optional[str] = None

class HarmonicS3Uploader:
    """Chargeur complet pour Harmonic AI sur AWS S3"""
    
    def __init__(self):
        """Initialisation du chargeur S3"""
        
        print("🚀 INITIALISATION CHARGEUR HARMONIC AI S3")
        print("=" * 60)
        
        # Configuration AWS
        self.bucket_name = HARMONIC_BUCKET
        self.region = AWS_REGION
        
        # Initialisation client S3
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=self.region,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
            )
            
            # Vérification bucket
            try:
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                print(f"✅ Bucket '{self.bucket_name}' trouvé")
            except:
                print(f"📦 Création du bucket '{self.bucket_name}'...")
                self._create_bucket()
            
            # Vérification permissions
            self._verify_permissions()
            
        except Exception as e:
            print(f"❌ Erreur initialisation S3: {str(e)}")
            sys.exit(1)
        
        # Statistiques
        self.stats = {
            'total_files': 0,
            'successful_uploads': 0,
            'failed_uploads': 0,
            'total_size': 0,
            'upload_time': 0.0,
            'domains_processed': 0
        }
        
        print("✅ Chargeur S3 initialisé avec succès")
        print("=" * 60)
    
    def _create_bucket(self):
        """Crée le bucket S3"""
        
        try:
            self.s3_client.create_bucket(
                Bucket=self.bucket_name,
                CreateBucketConfiguration={
                    'LocationConstraint': self.region
                }
            )
            print(f"✅ Bucket '{self.bucket_name}' créé avec succès")
        except Exception as e:
            print(f"❌ Erreur création bucket: {str(e)}")
            raise
    
    def _verify_permissions(self):
        """Vérifie les permissions S3"""
        
        try:
            # Test de lecture
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            
            # Test d'écriture
            test_key = "permission-test"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=test_key,
                Body=b"test",
                ContentType="text/plain"
            )
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=test_key)
            
            print("✅ Permissions S3 vérifiées avec succès")
        except Exception as e:
            print(f"❌ Erreur permissions S3: {str(e)}")
            raise
    
    def upload_all_modules(self) -> Dict[str, Any]:
        """Charge tous les modules Harmonic AI"""
        
        print("🚀 DÉMARRAGE CHARGEMENT COMPLET HARMONIC AI")
        print("=" * 60)
        
        start_time = time.time()
        
        # Domaines à charger
        domains = [
            'foundation',
            'core',
            'domains/visual',
            'domains/mathematics',
            'domains/code',
            'deployment'
        ]
        
        results = {}
        
        for domain in domains:
            print(f"\n📦 Traitement domaine: {domain}")
            domain_result = self._upload_domain(domain)
            results[domain] = domain_result
            
            # Mise à jour statistiques
            self.stats['total_files'] += domain_result['total_files']
            self.stats['successful_uploads'] += domain_result['successful_uploads']
            self.stats['failed_uploads'] += domain_result['failed_uploads']
            self.stats['total_size'] += domain_result['total_size']
            self.stats['upload_time'] += domain_result['upload_time']
            self.stats['domains_processed'] += 1
        
        # Création manifeste global
        self._create_global_manifest(results)
        
        # Affichage statistiques finales
        total_time = time.time() - start_time
        self._display_final_stats(total_time)
        
        return results
    
    def _upload_domain(self, domain: str) -> Dict[str, Any]:
        """Charge un domaine spécifique"""
        
        domain_path = BASE_PATH / domain
        if not domain_path.exists():
            print(f"⚠️ Domaine '{domain}' non trouvée")
            return {
                'domain': domain,
                'total_files': 0,
                'successful_uploads': 0,
                'failed_uploads': 0,
                'total_size': 0,
                'upload_time': 0.0,
                'files': []
            }
        
        domain_result = {
            'domain': domain,
            'total_files': 0,
            'successful_uploads': 0,
            'failed_uploads': 0,
            'total_size': 0,
            'upload_time': 0.0,
            'files': []
        }
        
        start_time = time.time()
        
        # Parcourir les fichiers
        for file_path in domain_path.rglob('*'):
            if file_path.is_file():
                result = self._upload_file(file_path, domain)
                domain_result['files'].append(result)
                
                if result.success:
                    domain_result['successful_uploads'] += 1
                else:
                    domain_result['failed_uploads'] += 1
                
                domain_result['total_size'] += result.size
                domain_result['total_files'] += 1
        
        domain_result['upload_time'] = time.time() - start_time
        
        print(f"✅ {domain}: {domain_result['successful_uploads']}/{domain_result['total_files']} fichiers")
        return domain_result
    
    def _upload_file(self, file_path: Path, domain: str) -> UploadResult:
        """Charge un fichier spécifique"""
        
        start_time = time.time()
        
        try:
            # Détermination S3 key
            relative_path = file_path.relative_to(BASE_PATH)
            s3_key = str(relative_path).replace('\\', '/')
            
            # Lecture du fichier
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Détermination content type
            content_type = self._get_content_type(file_path)
            
            # Upload vers S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content,
                ContentType=content_type,
                Metadata={
                    'domain': domain,
                    'original_path': str(file_path),
                    'upload_time': datetime.now().isoformat(),
                    'file_hash': hashlib.sha256(content).hexdigest(),
                    'project': 'harmonic-ai',
                    'version': '1.0.0'
                }
            )
            
            upload_time = time.time() - start_time
            
            return UploadResult(
                file_path=str(file_path),
                s3_key=s3_key,
                success=True,
                size=len(content),
                upload_time=upload_time
            )
            
        except Exception as e:
            upload_time = time.time() - start_time
            return UploadResult(
                file_path=str(file_path),
                s3_key="",
                success=False,
                size=0,
                upload_time=upload_time,
                error=str(e)
            )
    
    def _get_content_type(self, file_path: Path) -> str:
        """Détermine le content type basé sur l'extension"""
        
        extension = file_path.suffix.lower()
        
        content_types = {
            '.py': 'text/x-python',
            '.js': 'text/javascript',
            '.json': 'application/json',
            '.md': 'text/markdown',
            '.txt': 'text/plain',
            '.yml': 'application/x-yaml',
            '.yaml': 'application/x-yaml',
            '.sh': 'application/x-sh',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.pdf': 'application/pdf',
            '.html': 'text/html',
            '.css': 'text/css',
            '.csv': 'text/csv'
        }
        
        return content_types.get(extension, 'application/octet-stream')
    
    def _create_global_manifest(self, results: Dict[str, Any]):
        """Crée le manifeste global du déploiement"""
        
        manifest = {
            'deployment': {
                'version': '1.0.0',
                'timestamp': datetime.now().isoformat(),
                'aws_region': self.region,
                'bucket_name': self.bucket_name,
                'base_path': str(BASE_PATH)
            },
            'statistics': {
                'total_files': self.stats['total_files'],
                'successful_uploads': self.stats['successful_uploads'],
                'failed_uploads': self.stats['failed_uploads'],
                'domains_processed': self.stats['domains_processed'],
                'total_size': self.stats['total_size'],
                'upload_time': self.stats['upload_time']
            },
            'domains': results,
            'infrastructure': {
                'foundation': {
                    'files': results.get('foundation', {}).get('files', []),
                    'status': 'uploaded'
                },
                'core': {
                    'files': results.get('core', {}).get('files', []),
                    'status': 'uploaded'
                },
                'domains': {
                    'visual': {
                        'files': results.get('domains/visual', {}).get('files', []),
                        'status': 'uploaded'
                    },
                    'mathematics': {
                        'files': results.get('domains/mathematics', {}).get('files', []),
                        'status': 'uploaded'
                    },
                    'code': {
                        'files': results.get('domains/code', {}).get('files', []),
                        'status': 'uploaded'
                    },
                    'deployment': {
                        'files': results.get('deployment', {}).get('files', []),
                        'status': 'uploaded'
                    }
                }
            }
        }
        
        # Upload du manifeste
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key='manifests/global_deployment_manifest.json',
                Body=json.dumps(manifest, indent=2),
                ContentType='application/json'
            )
            print("✅ Manifeste global créé")
        except Exception as e:
            print(f"❌ Erreur création manifeste: {str(e)}")
    
    def _display_final_stats(self, total_time: float):
        """Affiche les statistiques finales"""
        
        print("\n" + "=" * 60)
        print("🏆 STATISTIQUES FINALES DU CHARGEMENT")
        print("=" * 60)
        
        print(f"📊 Fichiers totaux: {self.stats['total_files']}")
        print(f"✅ Uploads réussis: {self.stats['successful_uploads']}")
        print(f"❌ Uploads échoués: {self.stats['failed_uploads']}")
        print(f"📦 Domaines traités: {self.stats['domains_processed']}")
        print(f"💾 Taille totale: {self.stats['total_size']:,} bytes")
        print(f"⏱️ Temps total: {total_time:.2f} secondes")
        print(f"🚀 Vitesse moyenne: {self.stats['total_size'] / self.stats['upload_time'] / 1024:.1f} KB/s")
        
        if self.stats['failed_uploads'] > 0:
            print(f"\n⚠️ Erreurs détectées: {self.stats['failed_uploads']}")
        
        print("\n📦 Contenu du bucket:")
        try:
            objects = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            print(f"   📁 Objets totaux: {len(objects['Contents'])}")
            
            # Taille totale
            total_size = sum(obj['Size'] for obj in objects['Contents'])
            print(f"💾 Taille totale: {total_size:,} bytes ({total_size / 1024:.1f} KB)")
            
        except Exception as e:
            print(f"❌ Erreur récupération infos bucket: {str(e)}")
        
        print("\n🌊 Déploiement Harmonic AI terminé!")
        print(f"📊 Accès S3: https://s3.console.aws.amazon.com/s3/buckets/{self.bucket_name}")
        print(f"🔑 Région: {self.region}")
        print("=" * 60)

def main():
    """Fonction principale de chargement"""
    
    print("🚀 CHARGEMENT HARMONIC AI SUR AWS S3")
    print("=" * 60)
    
    # Vérification configuration
    if not os.getenv("AWS_ACCESS_KEY_ID") or not os.getenv("AWS_SECRET_ACCESS_KEY"):
        print("❌ Variables d'environnement AWS non configurées")
        print("🔧 Exécutez:")
        print("   export AWS_ACCESS_KEY_ID=votre_clé_aws")
        print("   export AWS_SECRET_ACCESS_KEY=votre_secret_aws")
        print("   export HARMONIC_BUCKET=harmonic-ai-knowledge-base")
        print("   export AWS_DEFAULT_REGION=us-east-1")
        return
    
    # Vérification chemin
    if not BASE_PATH.exists():
        print(f"❌ Chemin Harmonic AI non trouvé: {BASE_PATH}")
        return
    
    # Lancement du chargeur
    uploader = HarmonicS3Uploader()
    results = uploader.upload_all_modules()
    
    print("\n🚀 CHARGEMENT TERMINÉ AVEC SUCCÈS!")
    print(f"📊 Accès au contenu: https://s3.console.aws.amazon.com/s3/buckets/{HARMONIC_BUCKET}")

if __name__ == "__main__":
    main()
