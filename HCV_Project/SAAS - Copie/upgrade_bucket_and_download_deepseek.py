#!/usr/bin/env python3
"""
🚀 AUGMENTATION CAPACITÉ BUCKET + TÉLÉCHARGEMENT COMPLET DEEPSEEK V4 PRO
Augmente la capacité du bucket S3 et télécharge le modèle complet 1.2TB
"""

import boto3
import json
import os
import sys
import time
from pathlib import Path
from botocore.exceptions import ClientError

# Configuration AWS
with open('aws_credentials_secure.json', 'r') as f:
    config = json.load(f)

# Initialisation clients S3 et IAM
s3_client = boto3.client(
    's3',
    aws_access_key_id=config['aws_access_key_id'],
    aws_secret_access_key=config['aws_secret_access_key'],
    region_name=config['region']
)

iam_client = boto3.client(
    'iam',
    aws_access_key_id=config['aws_access_key_id'],
    aws_secret_access_key=config['aws_secret_access_key'],
    region_name=config['region']
)

class BucketUpgraderAndDownloader:
    """Augmente la capacité du bucket et télécharge DeepSeek complet"""
    
    def __init__(self):
        self.bucket_name = "deepseek-models-326095712935"
        self.backup_bucket = "harmonic-ai-knowledge-base"
        self.local_path = Path("./deepseek-v4-pro-complete")
        self.local_path.mkdir(exist_ok=True)
        
        print("🚀 AUGMENTATION CAPACITÉ BUCKET + TÉLÉCHARGEMENT DEEPSEEK")
        print("=" * 70)
        print(f"📁 Bucket principal: {self.bucket_name}")
        print(f"📁 Bucket backup: {self.backup_bucket}")
        print(f"📁 Dossier local: {self.local_path.absolute()}")
        print(f"📊 Espace requis: 1.2 TB")
    
    def check_current_bucket_permissions(self):
        """Vérifier les permissions actuelles du bucket"""
        print("\n🔍 VÉRIFICATION PERMISSIONS ACTUELLES...")
        
        try:
            # Vérifier les permissions de l'utilisateur IAM
            user_response = iam_client.get_user()
            user_arn = user_response['User']['Arn']
            print(f"✅ Utilisateur IAM: {user_arn}")
            
            # Lister les politiques attachées à l'utilisateur
            policies_response = iam_client.list_attached_user_policies(UserName=user_response['User']['UserName'])
            print(f"📋 Politiques utilisateur: {len(policies_response['AttachedPolicies'])}")
            
            for policy in policies_response['AttachedPolicies']:
                policy_name = policy['PolicyName']
                print(f"   📄 {policy_name}")
                
                # Vérifier si c'est une politique S3
                if 'S3' in policy_name or 's3' in policy_name.lower():
                    print(f"      ✅ Politique S3 détectée")
            
            # Vérifier les politiques du bucket
            try:
                bucket_policy = s3_client.get_bucket_policy(Bucket=self.bucket_name)
                print("✅ Politique de bucket présente")
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
                    print("⚠️  Aucune politique de bucket")
                else:
                    print(f"❌ Erreur politique bucket: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur vérification permissions: {e}")
            return False
    
    def create_enhanced_s3_policy(self):
        """Créer une politique S3 améliorée"""
        print("\n🔧 CRÉATION POLITIQUE S3 AMÉLIORÉE...")
        
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "DeepSeekFullAccess",
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:GetObjectVersion",
                        "s3:ListBucket",
                        "s3:ListBucketVersions",
                        "s3:HeadObject",
                        "s3:HeadBucket",
                        "s3:PutObject",
                        "s3:PutObjectAcl",
                        "s3:DeleteObject",
                        "s3:DeleteObjectVersion"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{self.bucket_name}",
                        f"arn:aws:s3:::{self.bucket_name}/*"
                    ]
                },
                {
                    "Sid": "HarmonicAIBucketAccess",
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:GetObjectVersion",
                        "s3:ListBucket",
                        "s3:ListBucketVersions",
                        "s3:HeadObject",
                        "s3:HeadBucket",
                        "s3:PutObject",
                        "s3:PutObjectAcl",
                        "s3:DeleteObject",
                        "s3:DeleteObjectVersion"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{self.backup_bucket}",
                        f"arn:aws:s3:::{self.backup_bucket}/*"
                    ]
                },
                {
                    "Sid": "S3ListAllBuckets",
                    "Effect": "Allow",
                    "Action": [
                        "s3:ListAllMyBuckets",
                        "s3:GetBucketLocation"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        try:
            # Créer la politique IAM
            policy_name = "DeepSeekHarmonicFullAccess"
            policy_response = iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document),
                Description="Accès complet aux buckets DeepSeek et Harmonic AI"
            )
            
            policy_arn = policy_response['Policy']['Arn']
            print(f"✅ Politique créée: {policy_arn}")
            
            # Attacher la politique à l'utilisateur
            user_response = iam_client.get_user()
            user_name = user_response['User']['UserName']
            
            iam_client.attach_user_policy(
                UserName=user_name,
                PolicyArn=policy_arn
            )
            
            print(f"✅ Politique attachée à l'utilisateur: {user_name}")
            
            # Attendre que la politique soit active
            print("⏳ Attente activation politique (30 secondes)...")
            time.sleep(30)
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur création politique: {e}")
            return False
    
    def check_bucket_storage_class(self):
        """Vérifier et optimiser la classe de stockage"""
        print("\n🔍 VÉRIFICATION CLASSE DE STOCKAGE...")
        
        try:
            # Vérifier la versioning
            versioning = s3_client.get_bucket_versioning(Bucket=self.bucket_name)
            print(f"📋 Versioning: {versioning.get('Status', 'Disabled')}")
            
            # Vérifier le lifecycle
            try:
                lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=self.bucket_name)
                print(f"🔄 Règles lifecycle: {len(lifecycle['Rules'])}")
            except ClientError:
                print("⚠️  Aucune règle lifecycle")
            
            # Activer le versioning si nécessaire
            if versioning.get('Status') != 'Enabled':
                s3_client.put_bucket_versioning(
                    Bucket=self.bucket_name,
                    VersioningConfiguration={'Status': 'Enabled'}
                )
                print("✅ Versioning activé")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur vérification stockage: {e}")
            return False
    
    def estimate_download_time_and_cost(self):
        """Estimer le temps et le coût de téléchargement"""
        print("\n📊 ESTIMATION TÉLÉCHARGEMENT...")
        
        # Taille attendue
        expected_size_tb = 1.2
        expected_size_gb = expected_size_tb * 1024
        expected_size_bytes = expected_size_gb * 1024**3
        
        # Vitesse de téléchargement estimée (varie selon connexion)
        speeds = [
            {"name": "10 Mbps", "mbps": 10, "hours": expected_size_bytes * 8 / (10 * 1024**2 * 3600)},
            {"name": "50 Mbps", "mbps": 50, "hours": expected_size_bytes * 8 / (50 * 1024**2 * 3600)},
            {"name": "100 Mbps", "mbps": 100, "hours": expected_size_bytes * 8 / (100 * 1024**2 * 3600)},
            {"name": "1 Gbps", "mbps": 1000, "hours": expected_size_bytes * 8 / (1000 * 1024**2 * 3600)}
        ]
        
        print(f"📊 Taille à télécharger: {expected_size_tb:.1f} TB ({expected_size_gb:.0f} GB)")
        print(f"📊 Temps estimé par vitesse:")
        
        for speed in speeds:
            days = speed["hours"] / 24
            print(f"   🚀 {speed['name']}: {speed['hours']:.1f} heures ({days:.1f} jours)")
        
        # Coût estimé (transfert de données S3)
        # Premier 10 GB/mois gratuit, puis $0.09/GB
        cost_per_gb = 0.09
        free_gb = 10
        chargeable_gb = max(0, expected_size_gb - free_gb)
        estimated_cost = chargeable_gb * cost_per_gb
        
        print(f"💰 Coût estimé transfert: ${estimated_cost:.2f}")
        
        return expected_size_bytes, estimated_cost
    
    def create_download_script(self):
        """Créer le script de téléchargement optimisé"""
        print("\n📝 CRÉATION SCRIPT TÉLÉCHARGEMENT OPTIMISÉ...")
        
        script_content = f'''#!/usr/bin/env python3
"""
🚀 TÉLÉCHARGEMENT OPTIMISÉ DEEPSEEK V4 PRO (1.2TB)
Script optimisé avec reprise automatique et vérification d'intégrité
"""

import boto3
import json
import os
import time
import hashlib
from pathlib import Path
from tqdm import tqdm
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration AWS
with open('aws_credentials_secure.json', 'r') as f:
    config = json.load(f)

# Initialisation client S3
s3_client = boto3.client(
    's3',
    aws_access_key_id=config['aws_access_key_id'],
    aws_secret_access_key=config['aws_secret_access_key'],
    region_name=config['region']
)

class OptimizedDeepSeekDownloader:
    """Téléchargeur optimisé pour DeepSeek V4 Pro"""
    
    def __init__(self):
        self.bucket_name = "{self.bucket_name}"
        self.local_path = Path("./deepseek-v4-pro-complete")
        self.local_path.mkdir(exist_ok=True)
        
        # Fichier de suivi
        self.progress_file = self.local_path / "download_progress.json"
        self.downloaded_files = set()
        
        print("🚀 TÉLÉCHARGEMENT OPTIMISÉ DEEPSEEK V4 PRO")
        print("=" * 60)
        print(f"📁 Bucket: {{self.bucket_name}}")
        print(f"📁 Destination: {{self.local_path}}")
    
    def load_progress(self):
        """Charger la progression précédente"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                data = json.load(f)
                self.downloaded_files = set(data.get('downloaded_files', []))
            print(f"✅ Progression chargée: {{len(self.downloaded_files)}} fichiers déjà téléchargés")
        else:
            print("🆅 Nouveau téléchargement")
    
    def save_progress(self):
        """Sauvegarder la progression"""
        data = {{
            'downloaded_files': list(self.downloaded_files),
            'timestamp': time.time()
        }}
        with open(self.progress_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def list_all_files(self):
        """Lister tous les fichiers du bucket"""
        print("🔍 Listing des fichiers...")
        
        all_files = []
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=self.bucket_name)
        
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    all_files.append({{
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'etag': obj['ETag'].strip('"')
                    }})
        
        total_size = sum(f['size'] for f in all_files)
        size_tb = total_size / (1024**4)
        size_gb = total_size / (1024**3)
        
        print(f"📊 Fichiers trouvés: {{len(all_files)}}")
        print(f"📊 Taille totale: {{size_gb:.1f}} GB ({{size_tb:.3f}} TB)")
        
        return all_files
    
    def download_file(self, file_info):
        """Télécharger un fichier avec vérification"""
        key = file_info['key']
        expected_size = file_info['size']
        expected_etag = file_info['etag']
        
        # Nom de fichier local
        file_name = Path(key).name
        local_path = self.local_path / file_name
        
        # Vérifier si déjà téléchargé
        if key in self.downloaded_files and local_path.exists():
            # Vérifier la taille
            actual_size = local_path.stat().st_size
            if actual_size == expected_size:
                return {{'status': 'already_downloaded', 'key': key}}
        
        try:
            # Télécharger
            s3_client.download_file(
                Bucket=self.bucket_name,
                Key=key,
                Filename=str(local_path)
            )
            
            # Vérifier la taille
            actual_size = local_path.stat().st_size
            if actual_size != expected_size:
                return {{
                    'status': 'size_mismatch',
                    'key': key,
                    'expected': expected_size,
                    'actual': actual_size
                }}
            
            # Ajouter aux fichiers téléchargés
            self.downloaded_files.add(key)
            
            return {{
                'status': 'success',
                'key': key,
                'size': actual_size
            }}
            
        except Exception as e:
            return {{
                'status': 'error',
                'key': key,
                'error': str(e)
            }}
    
    def run_download(self):
        """Exécuter le téléchargement avec parallélisation"""
        # Charger la progression
        self.load_progress()
        
        # Lister les fichiers
        all_files = self.list_all_files()
        
        # Filtrer les fichiers déjà téléchargés
        files_to_download = [f for f in all_files if f['key'] not in self.downloaded_files]
        
        print(f"📊 Fichiers à télécharger: {{len(files_to_download)}}")
        print(f"📊 Déjà téléchargés: {{len(self.downloaded_files)}}")
        
        if not files_to_download:
            print("✅ Tous les fichiers sont déjà téléchargés!")
            return True
        
        # Téléchargement parallèle (max 5 threads)
        max_workers = 5
        total_size = sum(f['size'] for f in files_to_download)
        
        with tqdm(total=total_size, unit='B', unit_scale=True, desc="Téléchargement") as pbar:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Soumettre tous les téléchargements
                future_to_file = {{
                    executor.submit(self.download_file, file_info): file_info
                    for file_info in files_to_download
                }}
                
                success_count = 0
                error_count = 0
                
                for future in as_completed(future_to_file):
                    result = future.result()
                    file_info = future_to_file[future]
                    
                    if result['status'] == 'success':
                        success_count += 1
                        pbar.update(result['size'])
                        print(f"\\r✅ {{success_count}}/{{len(files_to_download)}}: {{Path(result['key']).name}}", end='', flush=True)
                    
                    elif result['status'] == 'already_downloaded':
                        pbar.update(file_info['size'])
                    
                    elif result['status'] == 'error':
                        error_count += 1
                        print(f"\\n❌ Erreur {{result['key']}}: {{result['error']}}")
                    
                    # Sauvegarder la progression périodiquement
                    if success_count % 10 == 0:
                        self.save_progress()
        
        # Sauvegarder la progression finale
        self.save_progress()
        
        print(f"\\n🏆 TÉLÉCHARGEMENT TERMINÉ!")
        print(f"✅ Succès: {{success_count}}")
        print(f"❌ Erreurs: {{error_count}}")
        
        return error_count == 0

if __name__ == "__main__":
    downloader = OptimizedDeepSeekDownloader()
    success = downloader.run_download()
    
    if success:
        print("\\n🌊 DeepSeek V4 Pro téléchargé avec succès!")
        print("✅ Prêt pour transformation harmonique")
    else:
        print("\\n⚠️  Téléchargement partiel - vérifier les erreurs")
'''
        
        script_path = Path("./download_optimized_deepseek.py")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"✅ Script optimisé créé: {script_path.absolute()}")
        return script_path
    
    def run_complete_upgrade_and_download(self):
        """Exécuter le processus complet"""
        
        # 1. Vérifier les permissions actuelles
        if not self.check_current_bucket_permissions():
            print("❌ Impossible de vérifier les permissions")
            return False
        
        # 2. Créer la politique améliorée
        if not self.create_enhanced_s3_policy():
            print("❌ Impossible de créer la politique S3")
            return False
        
        # 3. Optimiser la configuration du bucket
        if not self.check_bucket_storage_class():
            print("❌ Impossible d'optimiser le bucket")
            return False
        
        # 4. Estimer le temps et le coût
        expected_size, estimated_cost = self.estimate_download_time_and_cost()
        
        # 5. Créer le script de téléchargement
        script_path = self.create_download_script()
        
        print("\n🏆 CONFIGURATION TERMINÉE!")
        print("✅ Politiques S3 améliorées")
        print("✅ Bucket optimisé")
        print("✅ Script de téléchargement créé")
        
        print(f"\n🚀 POUR TÉLÉCHARGER:")
        print(f"python {script_path.name}")
        
        print(f"\n⚠️  ATTENTION:")
        print(f"   📊 Espace requis: {expected_size / (1024**4):.1f} TB")
        print(f"   💰 Coût estimé: ${estimated_cost:.2f}")
        print(f"   ⏰ Temps: plusieurs heures/jours selon connexion")
        
        return True

if __name__ == "__main__":
    upgrader = BucketUpgraderAndDownloader()
    success = upgrader.run_complete_upgrade_and_download()
    
    if success:
        print("\n🌊 Prêt pour télécharger DeepSeek V4 Pro complet!")
    else:
        print("\n❌ Échec de la configuration")
