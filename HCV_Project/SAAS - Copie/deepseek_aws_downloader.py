#!/usr/bin/env python3
"""
Deepseek AWS Downloader - IA Générative
====================================

Script pour télécharger automatiquement Deepseek Coder 6.7B depuis Hugging Face
et l'uploader sur AWS S3 avec gestion d'erreurs, progression et vérification.
"""

import os
import sys
import time
import json
import logging
import hashlib
from pathlib import Path
from tqdm import tqdm
import boto3
from botocore.exceptions import ClientError
from huggingface_hub import snapshot_download
from huggingface_hub.utils import HfHubHTTPError

class DeepseekAWSDownloader:
    """Downloader pour Deepseek Coder 6.7B avec upload AWS S3"""
    
    def __init__(self):
        # Configuration AWS
        self.bucket_name = "deepseek-models-326095712935"
        self.region = "eu-west-3"
        
        # Configuration modèle
        self.model_name = "deepseek-ai/deepseek-coder-6.7b-base"
        self.local_path = Path("./deepseek-model")
        self.s3_prefix = "deepseek-coder-6.7b"
        
        # Clients
        self.s3_client = None
        self.s3_resource = None
        
        # Métriques et état
        self.metrics = {
            'start_time': time.time(),
            'files_downloaded': 0,
            'total_size': 0,
            'files_uploaded': 0,
            'uploaded_bytes': 0,
            'upload_speed': 0
        }
        
        # Configuration logging
        self.logger = None
        self.setup_logging()
        
    def setup_logging(self):
        """Configuration du système de logging avec support UTF-8"""
        # Fix encoding Windows
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('deepseek_downloader.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_aws_client(self):
        """Initialiser le client AWS S3 avec configuration"""
        try:
            self.logger.info("🔧 Initialisation du client AWS S3...")
            
            self.s3_client = boto3.client(
                's3',
                region_name=self.region,
                config=boto3.session.Config(
                    retries = {
                        'max_attempts': 10,
                        'mode': 'standard'
                    },
                    max_pool_connections=50
                )
            )
            
            self.s3_resource = boto3.resource('s3', region_name=self.region)
            
            self.logger.info("✅ Client AWS S3 initialisé")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation AWS: {str(e)}")
            return False
    
    def create_s3_bucket(self):
        """Créer le bucket S3 si il n'existe pas déjà"""
        try:
            self.logger.info(f"🔍 Vérification existence bucket: {self.bucket_name}")
            
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            self.logger.info(f"✅ Bucket {self.bucket_name} existe déjà")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == '404':
                self.logger.info(f"📦 Création du bucket {self.bucket_name}...")
                
                try:
                    if self.region == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={
                                'LocationConstraint': self.region
                            }
                        )
                    
                    self.s3_client.put_bucket_encryption(
                        Bucket=self.bucket_name,
                        ServerSideEncryptionConfiguration={
                            'Rules': [{
                                'ApplyServerSideEncryptionByDefault': {
                                    'SSEAlgorithm': 'AES256'
                                }
                            }]
                        }
                    )
                    
                    self.logger.info(f"✅ Bucket {self.bucket_name} créé avec succès")
                    return True
                    
                except Exception as create_error:
                    self.logger.error(f"❌ Erreur création bucket: {str(create_error)}")
                    return False
            else:
                self.logger.error(f"❌ Erreur accès bucket: {str(e)}")
                return False
    
    def calculate_file_checksum(self, file_path):
        """Calculer le hash SHA256 d'un fichier pour vérification"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    def download_model_files(self):
        """Télécharger les fichiers du modèle depuis Hugging Face avec reprise"""
        try:
            self.logger.info("📥 Début téléchargement du modèle Deepseek Coder 6.7B...")
            
            os.makedirs(self.local_path, exist_ok=True)
            
            downloaded_path = snapshot_download(
                repo_id=self.model_name,
                local_dir=self.local_path,
                local_dir_use_symlinks=False,
                resume_download=True,
                cache_dir=None,
                max_workers=4
            )
            
            self.logger.info(f"✅ Modèle téléchargé dans: {downloaded_path}")
            
            # Calcul des métriques
            total_size = 0
            file_count = 0
            
            for file_path in self.local_path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            self.metrics['files_downloaded'] = file_count
            self.metrics['total_size'] = total_size
            
            self.logger.info(f"📊 Téléchargement terminé: {file_count} fichiers, {total_size / 1024 / 1024 / 1024:.2f} GB")
            
            return True
            
        except HfHubHTTPError as hf_error:
            self.logger.error(f"❌ Erreur Hugging Face API: {str(hf_error)}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Erreur téléchargement: {str(e)}", exc_info=True)
            return False
    
    def progress_callback(self, bytes_transferred):
        """Callback pour suivre la progression de l'upload"""
        self.metrics['uploaded_bytes'] += bytes_transferred
        
        if self.metrics['total_size'] > 0:
            percent = (self.metrics['uploaded_bytes'] / self.metrics['total_size']) * 100
            elapsed = time.time() - self.metrics['start_time']
            speed = self.metrics['uploaded_bytes'] / elapsed if elapsed > 0 else 0
            
            print(f"\r📤 Progression Upload: {percent:.1f}% | {speed / 1024 / 1024:.2f} MB/s", 
                  end="", flush=True)
    
    def upload_files_to_s3(self):
        """Uploader les fichiers sur S3 avec multipart pour gros fichiers"""
        try:
            self.logger.info("\n📤 Début upload vers AWS S3...")
            
            files = list(self.local_path.rglob('*'))
            files = [f for f in files if f.is_file()]
            
            self.metrics['uploaded_bytes'] = 0
            
            with tqdm(total=len(files), desc="Upload fichiers") as pbar:
                for file_path in files:
                    try:
                        relative_path = file_path.relative_to(self.local_path)
                        s3_key = f"{self.s3_prefix}/{relative_path}"
                        
                        file_size = file_path.stat().st_size
                        
                        # Configuration upload
                        transfer_config = boto3.s3.transfer.TransferConfig(
                            multipart_threshold=100 * 1024 * 1024,  # 100MB
                            max_concurrency=10,
                            multipart_chunksize=50 * 1024 * 1024,   # 50MB
                            use_threads=True
                        )
                        
                        extra_args = {
                            'ContentType': 'application/octet-stream',
                            'Metadata': {
                                'original_filename': file_path.name,
                                'source': 'huggingface',
                                'model': self.model_name,
                                'checksum_sha256': self.calculate_file_checksum(file_path)
                            }
                        }
                        
                        self.s3_client.upload_file(
                            str(file_path),
                            self.bucket_name,
                            s3_key,
                            ExtraArgs=extra_args,
                            Config=transfer_config
                        )
                        
                        self.metrics['files_uploaded'] += 1
                        pbar.update(1)
                        
                    except Exception as upload_error:
                        self.logger.error(f"❌ Erreur upload {file_path}: {str(upload_error)}")
                        raise
            
            self.logger.info("\n✅ Tous les fichiers ont été uploadés sur S3")
            return True
            
        except Exception as e:
            self.logger.error(f"\n❌ Erreur upload global: {str(e)}", exc_info=True)
            return False
    
    def verify_upload(self):
        """Vérifier l'intégrité de l'upload en comparant les checksums"""
        try:
            self.logger.info("🔍 Vérification intégrité de l'upload...")
            
            verification_results = []
            all_valid = True
            
            files = list(self.local_path.rglob('*'))
            files = [f for f in files if f.is_file()]
            
            for file_path in tqdm(files, desc="Vérification fichiers"):
                relative_path = file_path.relative_to(self.local_path)
                s3_key = f"{self.s3_prefix}/{relative_path}"
                
                try:
                    # Récupérer les métadonnées S3
                    response = self.s3_client.head_object(
                        Bucket=self.bucket_name,
                        Key=s3_key
                    )
                    
                    s3_checksum = response['Metadata'].get('checksum_sha256')
                    local_checksum = self.calculate_file_checksum(file_path)
                    
                    valid = (s3_checksum == local_checksum)
                    
                    verification_results.append({
                        'file': str(relative_path),
                        'valid': valid,
                        'size_local': file_path.stat().st_size,
                        'size_s3': response['ContentLength']
                    })
                    
                    if not valid:
                        all_valid = False
                        self.logger.warning(f"⚠️  Fichier corrompu: {relative_path}")
                
                except Exception as verify_error:
                    self.logger.error(f"❌ Erreur vérification {relative_path}: {str(verify_error)}")
                    all_valid = False
            
            if all_valid:
                self.logger.info("✅ Vérification terminée: TOUS les fichiers sont valides")
            else:
                self.logger.error("❌ Vérification terminée: Des fichiers sont corrompus ou manquants")
            
            with open('verification_results.json', 'w') as f:
                json.dump(verification_results, f, indent=2)
            
            return all_valid
            
        except Exception as e:
            self.logger.error(f"❌ Erreur vérification: {str(e)}", exc_info=True)
            return False
    
    def generate_report(self):
        """Générer le rapport final complet avec métriques"""
        duration = time.time() - self.metrics['start_time']
        
        report = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'model': self.model_name,
            'bucket': self.bucket_name,
            'region': self.region,
            's3_path': f"s3://{self.bucket_name}/{self.s3_prefix}/",
            'metrics': {
                'total_files': self.metrics['files_downloaded'],
                'files_uploaded': self.metrics['files_uploaded'],
                'total_size_gb': round(self.metrics['total_size'] / 1024 / 1024 / 1024, 3),
                'duration_minutes': round(duration / 60, 2),
                'average_speed_mbps': round((self.metrics['total_size'] / duration) / 1024 / 1024, 2)
            },
            'local_path': str(self.local_path.absolute()),
            'success': True,
            'script_version': '1.0.0'
        }
        
        with open('deepseek_aws_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info("\n📋 Rapport final généré: deepseek_aws_report.json")
        self.logger.info(json.dumps(report, indent=2))
        
        return report
    
    def run_complete_download(self):
        """Exécuter le processus complet de bout en bout"""
        self.logger.info("=" * 70)
        self.logger.info("🚀 DÉBUT DU PROCESSUS DEEPSEEK AWS DOWNLOADER")
        self.logger.info("=" * 70)
        
        try:
            # Étape 1: Initialisation AWS
            if not self.setup_aws_client():
                raise Exception("Échec initialisation client AWS")
            
            # Étape 2: Création bucket
            if not self.create_s3_bucket():
                raise Exception("Échec création bucket S3")
            
            # Étape 3: Téléchargement modèle
            if not self.download_model_files():
                raise Exception("Échec téléchargement du modèle")
            
            # Étape 4: Upload S3
            if not self.upload_files_to_s3():
                raise Exception("Échec upload vers S3")
            
            # Étape 5: Vérification intégrité
            if not self.verify_upload():
                raise Exception("Échec vérification de l'upload")
            
            # Étape 6: Génération rapport
            report = self.generate_report()
            
            self.logger.info("\n" + "=" * 70)
            self.logger.info("✅ PROCESSUS TERMINÉ AVEC SUCCÈS!")
            self.logger.info("=" * 70)
            self.logger.info(f"📦 Modèle disponible sur: s3://{self.bucket_name}/{self.s3_prefix}/")
            self.logger.info(f"⏱️  Durée totale: {report['metrics']['duration_minutes']} minutes")
            self.logger.info(f"💾 Taille totale: {report['metrics']['total_size_gb']} GB")
            
            return True
            
        except Exception as e:
            self.logger.error("\n" + "=" * 70)
            self.logger.error(f"❌ ÉCHEC DU PROCESSUS: {str(e)}")
            self.logger.error("=" * 70)
            
            # Générer rapport d'échec
            failure_report = {
                'success': False,
                'error': str(e),
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'metrics': self.metrics
            }
            
            with open('deepseek_aws_failure.json', 'w') as f:
                json.dump(failure_report, f, indent=2)
            
            return False

def main():
    """Fonction principale"""
    downloader = DeepseekAWSDownloader()
    success = downloader.run_complete_download()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()