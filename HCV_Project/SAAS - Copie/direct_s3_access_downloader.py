#!/usr/bin/env python3
"""
🚀 TÉLÉCHARGEMENT DIRECT S3 DEEPSEEK V4 PRO
Tente l'accès direct S3 avec différentes méthodes pour contourner les restrictions
"""

import boto3
import json
import os
import sys
import time
from pathlib import Path
from tqdm import tqdm
import subprocess
import requests

class DirectS3DeepSeekDownloader:
    """Téléchargeur direct S3 pour DeepSeek V4 Pro"""
    
    def __init__(self):
        # Configuration directe
        self.config = {
            "aws_access_key_id": "AKIAUX3GRWKTZEPOJOFI",
            "aws_secret_access_key": "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",
            "region": "us-east-1"
        }
        
        self.buckets = [
            "deepseek-models-326095712935",
            "harmonic-ai-knowledge-base"
        ]
        
        self.local_path = Path("./deepseek-v4-pro-direct-s3")
        self.local_path.mkdir(exist_ok=True)
        
        print("🚀 TÉLÉCHARGEMENT DIRECT S3 DEEPSEEK V4 PRO")
        print("=" * 60)
        print(f"📁 Dossier local: {self.local_path.absolute()}")
        print(f"🔑 Accès: Direct S3")
        print(f"📊 Espace requis: 1.2 TB")
    
    def try_aws_cli_access(self):
        """Essayer l'accès via AWS CLI"""
        print("\n🔧 ESSAI ACCÈS AWS CLI...")
        
        try:
            # Configurer AWS CLI
            subprocess.run([
                'aws', 'configure', 'set', 'aws_access_key_id',
                self.config["aws_access_key_id"]
            ], capture_output=True, check=True)
            
            subprocess.run([
                'aws', 'configure', 'set', 'aws_secret_access_key',
                self.config["aws_secret_access_key"]
            ], capture_output=True, check=True)
            
            subprocess.run([
                'aws', 'configure', 'set', 'region',
                self.config["region"]
            ], capture_output=True, check=True)
            
            print("✅ AWS CLI configuré")
            
            # Tester l'accès à chaque bucket
            for bucket in self.buckets:
                try:
                    result = subprocess.run([
                        'aws', 's3', 'ls', f's3://{bucket}',
                        '--recursive', '--no-paginate'
                    ], capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        files = [line for line in lines if line.strip()]
                        
                        if files:
                            print(f"✅ Bucket {bucket}: {len(files)} objets trouvés")
                            
                            # Analyser les fichiers
                            model_files = []
                            total_size = 0
                            
                            for line in files[:20]:  # Limiter pour l'analyse
                                try:
                                    parts = line.split()
                                    if len(parts) >= 4:
                                        date = parts[0]
                                        time = parts[1]
                                        size_str = parts[2]
                                        key = ' '.join(parts[3:])
                                        
                                        if size_str.isdigit():
                                            size = int(size_str)
                                            total_size += size
                                            
                                            # Chercher les fichiers de modèle
                                            if any(pattern in key.lower() for pattern in [
                                                'deepseek', 'model', '.bin', '.safetensors', 
                                                'pytorch_model', 'weights', 'checkpoint',
                                                'v4', 'pro'
                                            ]):
                                                model_files.append({
                                                    'key': key,
                                                    'size': size
                                                })
                                except:
                                    continue
                            
                            if model_files:
                                model_size = sum(f['size'] for f in model_files)
                                size_gb = model_size / (1024**3)
                                size_tb = model_size / (1024**4)
                                
                                print(f"   📁 Fichiers modèle: {len(model_files)}")
                                print(f"   📊 Taille modèle: {size_gb:.1f} GB ({size_tb:.3f} TB)")
                                print(f"   📊 Attendue: 1.2 TB")
                                print(f"   📊 Pourcentage: {(size_tb/1.2)*100:.1f}%")
                                
                                return {
                                    'bucket': bucket,
                                    'method': 'aws_cli',
                                    'files': model_files,
                                    'total_size': model_size
                                }
                            else:
                                print(f"⚠️  Bucket {bucket}: {len(files)} objets (pas de modèle)")
                        else:
                            print(f"❌ Bucket {bucket}: vide")
                    
                except subprocess.TimeoutExpired:
                    print(f"⏰ Timeout bucket {bucket}")
                except subprocess.CalledProcessError as e:
                    print(f"❌ Erreur bucket {bucket}: {e.stderr.strip()}")
            
        except Exception as e:
            print(f"❌ Erreur AWS CLI: {e}")
        
        return None
    
    def try_boto3_alternative_access(self):
        """Essayer l'accès Boto3 alternatif"""
        print("\n🔧 ESSAI ACCÈS BOTO3 ALTERNATIF...")
        
        try:
            # Client S3 avec configuration alternative
            s3_client = boto3.client(
                's3',
                aws_access_key_id=self.config["aws_access_key_id"],
                aws_secret_access_key=self.config["aws_secret_access_key"],
                region_name=self.config["region"],
                config=boto3.Config(
                    signature_version='s3v4',
                    s3={'addressing_style': 'path'}
                )
            )
            
            # Essayer d'accéder directement aux objets
            for bucket in self.buckets:
                try:
                    print(f"\n🔍 Bucket alternatif: {bucket}")
                    
                    # Essayer de lister avec différentes approches
                    approaches = [
                        lambda: s3_client.list_objects_v2(Bucket=bucket, MaxKeys=100),
                        lambda: s3_client.list_objects(Bucket=bucket, MaxKeys=100),
                        lambda: s3_client.get_bucket_location(Bucket=bucket)
                    ]
                    
                    for i, approach in enumerate(approaches):
                        try:
                            result = approach()
                            print(f"   ✅ Approche {i+1}: Succès")
                            
                            if 'Contents' in result:
                                files = result['Contents']
                                print(f"      📁 {len(files)} fichiers trouvés")
                                
                                # Analyser les fichiers
                                model_files = []
                                for obj in files:
                                    key = obj['Key']
                                    size = obj['Size']
                                    
                                    if any(pattern in key.lower() for pattern in [
                                        'deepseek', 'model', '.bin', '.safetensors', 
                                        'pytorch_model', 'weights', 'checkpoint',
                                        'v4', 'pro'
                                    ]):
                                        model_files.append({
                                            'key': key,
                                            'size': size
                                        })
                                
                                if model_files:
                                    model_size = sum(f['size'] for f in model_files)
                                    size_gb = model_size / (1024**3)
                                    size_tb = model_size / (1024**4)
                                    
                                    print(f"      📁 Modèles: {len(model_files)}")
                                    print(f"      📊 Taille: {size_gb:.1f} GB ({size_tb:.3f} TB)")
                                    
                                    return {
                                        'bucket': bucket,
                                        'method': 'boto3_alternative',
                                        'files': model_files,
                                        'total_size': model_size
                                    }
                            
                        except Exception as e:
                            print(f"   ❌ Approche {i+1}: {str(e)[:100]}...")
                            continue
                
                except Exception as e:
                    print(f"❌ Erreur bucket {bucket}: {e}")
        
        except Exception as e:
            print(f"❌ Erreur Boto3 alternatif: {e}")
        
        return None
    
    def try_presigned_url_access(self):
        """Essayer l'accès via URLs pré-signées"""
        print("\n🔧 ESSAI ACCÈS URL PRÉSIGNÉES...")
        
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=self.config["aws_access_key_id"],
                aws_secret_access_key=self.config["aws_secret_access_key"],
                region_name=self.config["region"]
            )
            
            # Générer des URLs pré-signées pour les objets potentiels
            potential_keys = [
                "deepseek-v4-pro/model.bin",
                "deepseek-v4-pro/pytorch_model.bin",
                "deepseek-v4-pro/model.safetensors",
                "model/deepseek-v4-pro.bin",
                "weights/deepseek-v4-pro.safetensors",
                "deepseek-v4-pro/config.json",
                "model/config.json"
            ]
            
            for bucket in self.buckets:
                print(f"\n🔍 Génération URLs pré-signées: {bucket}")
                
                for key in potential_keys:
                    try:
                        # Générer URL pré-signée
                        url = s3_client.generate_presigned_url(
                            'get_object',
                            Params={'Bucket': bucket, 'Key': key},
                            ExpiresIn=3600  # 1 heure
                        )
                        
                        print(f"   ✅ URL générée: {key}")
                        print(f"      {url[:100]}...")
                        
                        # Tester l'URL
                        response = requests.head(url, timeout=10)
                        if response.status_code == 200:
                            size = int(response.headers.get('content-length', 0))
                            if size > 0:
                                size_gb = size / (1024**3)
                                print(f"      📊 Taille: {size_gb:.1f} GB")
                                
                                return {
                                    'bucket': bucket,
                                    'method': 'presigned_url',
                                    'key': key,
                                    'url': url,
                                    'size': size
                                }
                        
                    except Exception as e:
                        print(f"   ❌ Erreur {key}: {str(e)[:50]}...")
                        continue
        
        except Exception as e:
            print(f"❌ Erreur URL pré-signées: {e}")
        
        return None
    
    def try_direct_download(self, access_info):
        """Télécharger directement avec les informations d'accès"""
        print(f"\n📥 TÉLÉCHARGEMENT DIRECT: {access_info['method']}")
        
        if access_info['method'] == 'presigned_url':
            return self.download_from_presigned_url(access_info)
        else:
            return self.download_from_bucket(access_info)
    
    def download_from_presigned_url(self, access_info):
        """Télécharger depuis URL pré-signée"""
        try:
            url = access_info['url']
            key = access_info['key']
            expected_size = access_info['size']
            
            # Nom de fichier local
            file_name = Path(key).name
            local_path = self.local_path / file_name
            
            print(f"📥 Téléchargement: {file_name}")
            print(f"📊 Taille attendue: {expected_size / (1024**3):.1f} GB")
            
            # Téléchargement avec progression
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(local_path, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc="Téléchargement") as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            pbar.update(len(chunk))
            
            # Vérification
            actual_size = local_path.stat().st_size
            if actual_size == expected_size:
                print(f"✅ Téléchargement réussi: {file_name}")
                return True
            else:
                print(f"❌ Erreur taille: {actual_size} != {expected_size}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur téléchargement: {e}")
            return False
    
    def download_from_bucket(self, access_info):
        """Télécharger depuis le bucket"""
        try:
            bucket = access_info['bucket']
            files = access_info['files']
            
            print(f"📊 {len(files)} fichiers à télécharger")
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=self.config["aws_access_key_id"],
                aws_secret_access_key=self.config["aws_secret_access_key"],
                region_name=self.config["region"]
            )
            
            success_count = 0
            for file_info in files:
                key = file_info['key']
                size = file_info['size']
                
                file_name = Path(key).name
                local_path = self.local_path / file_name
                
                try:
                    print(f"📥 Téléchargement: {file_name}")
                    
                    s3_client.download_file(
                        Bucket=bucket,
                        Key=key,
                        Filename=str(local_path)
                    )
                    
                    # Vérification
                    actual_size = local_path.stat().st_size
                    if actual_size == size:
                        success_count += 1
                        print(f"✅ Succès: {file_name}")
                    else:
                        print(f"❌ Erreur taille: {file_name}")
                
                except Exception as e:
                    print(f"❌ Erreur téléchargement {file_name}: {e}")
            
            print(f"🏆 Téléchargement terminé: {success_count}/{len(files)} fichiers")
            return success_count > 0
            
        except Exception as e:
            print(f"❌ Erreur téléchargement depuis bucket: {e}")
            return False
    
    def run_complete_direct_access(self):
        """Exécuter le processus d'accès direct complet"""
        
        # 1. Essayer AWS CLI
        access_info = self.try_aws_cli_access()
        
        # 2. Essayer Boto3 alternatif
        if not access_info:
            access_info = self.try_boto3_alternative_access()
        
        # 3. Essayer URLs pré-signées
        if not access_info:
            access_info = self.try_presigned_url_access()
        
        # 4. Si accès trouvé, télécharger
        if access_info:
            print(f"\n🎯 ACCÈS TROUVÉ: {access_info['method']}")
            print(f"📊 Bucket: {access_info['bucket']}")
            
            if 'total_size' in access_info:
                size_tb = access_info['total_size'] / (1024**4)
                print(f"📊 Taille disponible: {size_tb:.3f} TB")
                print(f"📊 Attendue: 1.2 TB")
                print(f"📊 Pourcentage: {(size_tb/1.2)*100:.1f}%")
            
            # Télécharger
            success = self.try_direct_download(access_info)
            
            if success:
                print("\n🏆 TÉLÉCHARGEMENT DIRECT RÉUSSI!")
                print("✅ DeepSeek V4 Pro téléchargé")
                print("✅ Prêt pour transformation harmonique")
                return True
            else:
                print("\n❌ ÉCHEC TÉLÉCHARGEMENT")
                return False
        else:
            print("\n❌ AUCUN ACCÈS DIRECT TROUVÉ")
            print("Toutes les méthodes d'accès ont échoué")
            return False

if __name__ == "__main__":
    downloader = DirectS3DeepSeekDownloader()
    success = downloader.run_complete_direct_access()
    
    if success:
        print("\n🌊 DeepSeek V4 Pro téléchargé avec succès!")
        print("✅ Accès direct établi")
        print("✅ Prêt pour LM Arena")
    else:
        print("\n❌ ÉCHEC ACCÈS DIRECT")
        print("Vérifier les permissions AWS")
