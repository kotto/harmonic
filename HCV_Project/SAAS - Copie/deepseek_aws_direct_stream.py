#!/usr/bin/env python3
"""
Deepseek AWS DIRECT STREAMING - ZERO DISK USAGE
===============================================

Transfert DIRECT Hugging Face -> AWS S3 SANS AUCUN FICHIER LOCAL.
Le modèle ne sera JAMAIS écrit sur votre disque dur.
Streaming chunk par chunk en mémoire uniquement.
"""

import os
import sys
import time
import json
import hashlib
import requests
from tqdm import tqdm
import boto3
from botocore.exceptions import ClientError
from huggingface_hub import HfApi

class DeepseekDirectStreamer:
    """Transferer directement Deepseek de HF vers S3 sans disque"""
    
    def __init__(self):
        # AWS Configuration
        self.bucket_name = "deepseek-models-326095712935"
        self.region = "eu-west-3"
        self.s3_prefix = "deepseek-coder-6.7b"
        
        # Modèle
        self.model_name = "deepseek-ai/deepseek-coder-6.7b-base"
        
        # Streaming parameters
        self.chunk_size = 8 * 1024 * 1024  # 8MB chunks
        self.multipart_threshold = 100 * 1024 * 1024
        
        # Clients
        self.s3_client = None
        self.hf_api = HfApi()
        
        # Métriques
        self.metrics = {
            'start_time': time.time(),
            'total_files': 0,
            'total_bytes': 0,
            'transferred_bytes': 0,
            'files_done': 0
        }

    def setup_aws(self):
        """Initialiser client AWS"""
        print("🔧 Initialisation AWS S3...")
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=self.region,
                config=boto3.session.Config(
                    retries = {'max_attempts': 15, 'mode': 'adaptive'},
                    max_pool_connections=100
                )
            )
            
            # Vérifier bucket
            try:
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                print(f"✅ Bucket {self.bucket_name} prêt")
            except ClientError:
                print(f"📦 Création bucket {self.bucket_name}...")
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            
            return True
        except Exception as e:
            print(f"❌ AWS Error: {e}")
            return False

    def stream_file_to_s3(self, file_info):
        """Stream UN SEUL fichier directement HF -> S3"""
        filename = file_info['path']
        file_size = file_info['size']
        download_url = file_info['url']
        
        s3_key = f"{self.s3_prefix}/{filename}"
        
        print(f"\n📡 Streaming: {filename} | {file_size / 1024 / 1024:.1f} MB")
        
        try:
            # Ouverture connexion HF
            response = requests.get(download_url, stream=True, timeout=300)
            response.raise_for_status()
            
            if file_size < self.multipart_threshold:
                # Upload direct petit fichier
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=response.content,
                    ContentType='application/octet-stream'
                )
                self.metrics['transferred_bytes'] += file_size
            else:
                # Multipart upload pour gros fichiers
                mpu = self.s3_client.create_multipart_upload(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    ContentType='application/octet-stream'
                )
                
                parts = []
                part_number = 1
                uploaded = 0
                
                with tqdm(total=file_size, unit='B', unit_scale=True, desc=filename) as pbar:
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        if chunk:
                            part = self.s3_client.upload_part(
                                Bucket=self.bucket_name,
                                Key=s3_key,
                                PartNumber=part_number,
                                UploadId=mpu['UploadId'],
                                Body=chunk
                            )
                            
                            parts.append({
                                'PartNumber': part_number,
                                'ETag': part['ETag']
                            })
                            
                            uploaded += len(chunk)
                            pbar.update(len(chunk))
                            part_number += 1
                
                # Finaliser upload
                self.s3_client.complete_multipart_upload(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    UploadId=mpu['UploadId'],
                    MultipartUpload={'Parts': parts}
                )
                
                self.metrics['transferred_bytes'] += uploaded
            
            self.metrics['files_done'] += 1
            print(f"✅ {filename} terminé")
            return True
            
        except Exception as e:
            print(f"❌ ERREUR {filename}: {str(e)}")
            return False

    def run_full_transfer(self):
        """Lancer le transfert complet sans disque"""
        # Fix Windows encoding
        import sys
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
        
        print("="*70)
        print("🚀 TRANSFERT DIRECT HUGGING FACE -> AWS S3")
        print("💾 AUCUN FICHIER LOCAL NE SERA CRÉÉ")
        print("="*70)
        
        if not self.setup_aws():
            sys.exit(1)
        
        print("\n📋 Récupération liste des fichiers du modèle...")
        repo_files = self.hf_api.list_repo_files(self.model_name, repo_type="model")
        
        files_to_transfer = []
        total_size = 0
        
        for filename in repo_files:
            # URL directe Hugging Face
            download_url = f"https://huggingface.co/{self.model_name}/resolve/main/{filename}"
            
            files_to_transfer.append({
                'path': filename,
                'size': 0,
                'url': download_url
            })
        
        self.metrics['total_files'] = len(files_to_transfer)
        self.metrics['total_bytes'] = total_size
        
        print(f"\n✅ {len(files_to_transfer)} fichiers trouvés | TOTAL: {total_size / 1024 / 1024 / 1024:.2f} GB")
        print(f"\n⏱️  Début du transfert streaming...\n")
        
        start = time.time()
        
        success = True
        for file_info in files_to_transfer:
            if not self.stream_file_to_s3(file_info):
                success = False
                break
        
        duration = time.time() - start
        
        print("\n" + "="*70)
        if success:
            print("✅ TRANSFERT TERMINÉ AVEC SUCCÈS!")
        else:
            print("❌ TRANSFERT INTERROMPU")
        
        print(f"\n📊 RAPPORT:")
        print(f"   Fichiers traités: {self.metrics['files_done']} / {self.metrics['total_files']}")
        print(f"   Total transféré: {self.metrics['transferred_bytes'] / 1024 / 1024 / 1024:.2f} GB")
        print(f"   Durée: {duration / 60:.1f} minutes")
        print(f"   Vitesse moyenne: {(self.metrics['transferred_bytes'] / duration) / 1024 / 1024:.1f} MB/s")
        print(f"\n📦 Modèle disponible sur: s3://{self.bucket_name}/{self.s3_prefix}/")
        print("="*70)
        
        # Rapport
        report = {
            'success': success,
            'model': self.model_name,
            'bucket': self.bucket_name,
            'total_files': self.metrics['total_files'],
            'total_size_gb': total_size / 1024 / 1024 / 1024,
            'duration_min': duration / 60,
            'average_speed_mbps': (self.metrics['transferred_bytes'] / duration) / 1024 / 1024,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open('streaming_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        return success

def main():
    streamer = DeepseekDirectStreamer()
    success = streamer.run_full_transfer()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()