#!/usr/bin/env python3
"""
UPLOAD SIMPLE DES MODÈLES HARMONIC AI SUR S3
Script simple pour uploader les modèles locaux
"""

import os
import sys
import json
import time
import boto3
from pathlib import Path

def simple_upload():
    """Upload simple des modèles"""
    
    print("🚀 UPLOAD SIMPLE DES MODÈLES HARMONIC AI")
    print("=" * 50)
    
    # Configuration
    bucket_name = "harmonic-ai-knowledge-base"
    region = "us-east-1"
    local_path = Path("local_s3_structure")
    
    if not local_path.exists():
        print("❌ Répertoire local_s3_structure non trouvé!")
        return False
    
    # Initialisation S3
    try:
        s3_client = boto3.client('s3', region_name=region)
        print(f"✅ Client S3 initialisé")
    except Exception as e:
        print(f"❌ Erreur initialisation S3: {str(e)}")
        return False
    
    # Création du bucket si nécessaire
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ Bucket '{bucket_name}' accessible")
    except:
        try:
            s3_client.create_bucket(Bucket=bucket_name)
            print(f"✅ Bucket '{bucket_name}' créé")
        except Exception as e:
            print(f"❌ Erreur création bucket: {str(e)}")
            return False
    
    # Upload des fichiers
    files_uploaded = 0
    total_size = 0
    
    for file_path in local_path.rglob('*'):
        if file_path.is_file():
            # Construction de la clé S3
            relative_path = file_path.relative_to(local_path)
            s3_key = str(relative_path).replace('\\', '/')
            
            try:
                # Upload
                s3_client.upload_file(
                    Filename=str(file_path),
                    Bucket=bucket_name,
                    Key=s3_key
                )
                
                files_uploaded += 1
                total_size += file_path.stat().st_size
                
                if files_uploaded % 10 == 0:
                    print(f"   📤 {files_uploaded} fichiers uploadés...")
                    
            except Exception as e:
                print(f"❌ Erreur upload {file_path.name}: {str(e)}")
    
    print(f"\n🏆 UPLOAD TERMINÉ!")
    print(f"📊 Fichiers uploadés: {files_uploaded}")
    print(f"💾 Taille totale: {total_size/1024:.1f} KB")
    print(f"📦 Bucket: s3://{bucket_name}/")
    
    return True

if __name__ == "__main__":
    success = simple_upload()
    if success:
        print("\n🌊 Upload réussi!")
    else:
        print("\n❌ Upload échoué.")
        sys.exit(1)
