#!/usr/bin/env python3
"""
Verification de la taille du modele DeepSeek V4 Pro
"""

import boto3
import json
import os
from pathlib import Path

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

def check_model_size():
    """Verifier la taille du modele DeepSeek dans tous les buckets"""
    
    print("🔍 VERIFICATION TAILLE MODELE DEEPSEEK V4 PRO")
    print("=" * 60)
    
    buckets_to_check = [
        "deepseek-models-326095712935",
        "harmonic-ai-knowledge-base",
        "connective-ai-deployment",
        "hcv-pro-deepseek-frontend-326095712935",
        "hcv-pro-deepseek-test-326095712935"
    ]
    
    total_found_size = 0
    found_models = {}
    
    for bucket in buckets_to_check:
        try:
            print(f"\n🔍 Verification bucket: {bucket}")
            
            # Lister tous les objets avec pagination
            paginator = s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket)
            
            bucket_files = []
            bucket_size = 0
            model_files = []
            
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        size = obj['Size']
                        
                        bucket_files.append({
                            'key': key,
                            'size': size
                        })
                        bucket_size += size
                        
                        # Chercher specifiquement les fichiers de modele
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
                found_models[bucket] = {
                    'files': model_files,
                    'total_size': model_size,
                    'file_count': len(model_files)
                }
                
                size_gb = model_size / (1024**3)
                size_tb = model_size / (1024**4)
                
                print(f"✅ Bucket {bucket}:")
                print(f"   📁 Fichiers modele: {len(model_files)}")
                print(f"   📊 Taille modele: {size_gb:.1f} GB ({size_tb:.3f} TB)")
                print(f"   📊 Taille attendue: 1.2 TB")
                print(f"   📊 Pourcentage: {(size_tb/1.2)*100:.1f}%")
                
                # Afficher les fichiers les plus gros
                sorted_files = sorted(model_files, key=lambda x: x['size'], reverse=True)
                print(f"   🎯 Plus gros fichiers:")
                for i, file_info in enumerate(sorted_files[:5]):
                    size_gb = file_info['size'] / (1024**3)
                    print(f"      {i+1}. {file_info['key']} ({size_gb:.1f} GB)")
                
                total_found_size += model_size
            
            elif bucket_files:
                size_gb = bucket_size / (1024**3)
                print(f"⚠️  Bucket {bucket}: {size_gb:.1f} GB (pas de fichiers modele)")
            else:
                print(f"❌ Bucket {bucket}: vide")
                
        except Exception as e:
            print(f"❌ Erreur bucket {bucket}: {e}")
    
    # Resume final
    print(f"\n🏆 RESUME FINAL")
    print("=" * 40)
    print(f"📊 Buckets avec modeles: {len(found_models)}")
    print(f"📊 Taille totale trouvee: {total_found_size / (1024**4):.3f} TB")
    print(f"📊 Taille attendue: 1.2 TB")
    print(f"📊 Pourcentage total: {(total_found_size/(1.2*1024**4))*100:.1f}%")
    
    if total_found_size >= 1.0 * 1024**4:  # Au moins 1TB
        print("✅ MODELE COMPLET TROUVÉ!")
        return True
    elif total_found_size >= 0.5 * 1024**4:  # Au moins 500GB
        print("⚠️  MODELE PARTIEL TROUVÉ")
        return False
    else:
        print("❌ MODELE NON TROUVÉ")
        return False

if __name__ == "__main__":
    is_complete = check_model_size()
