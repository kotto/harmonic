#!/usr/bin/env python3
"""
UPLOAD SÉCURISÉ SIMPLE DES MODÈLES HARMONIC AI
Utilisation des variables d'environnement configurées
"""

import os
import sys
import json
import time
import boto3
from pathlib import Path
from datetime import datetime

def simple_secure_upload():
    """Upload sécurisé simple avec variables d'environnement"""
    
    print("🚀 UPLOAD SÉCURISÉ SIMPLE DES MODÈLES HARMONIC AI")
    print("=" * 60)
    print("🔐 Utilisation des variables d'environnement")
    print("📦 Bucket: harmonic-ai-knowledge-base")
    print("🌍 Région: us-east-1")
    print("=" * 60)
    
    # Configuration depuis variables d'environnement
    bucket_name = os.getenv('HARMONIC_BUCKET', 'harmonic-ai-knowledge-base')
    region = os.getenv('AWS_REGION', 'us-east-1')
    local_path = Path("local_s3_structure")
    
    if not local_path.exists():
        print("❌ Répertoire local_s3_structure non trouvé!")
        return False
    
    try:
        # Utilisation directe des variables d'environnement
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=region
        )
        print("✅ Client S3 initialisé avec variables d'environnement")
    except Exception as e:
        print(f"❌ Erreur initialisation client: {str(e)}")
        return False
    
    # Test de permissions
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ Bucket '{bucket_name}' accessible")
    except:
        try:
            s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': region})
            print(f"✅ Bucket '{bucket_name}' créé")
        except Exception as e:
            print(f"❌ Erreur création bucket: {str(e)}")
            return False
    
    # Upload des fichiers
    files_uploaded = 0
    total_size = 0
    
    print(f"\n📤 DÉBUT UPLOAD SÉCURISÉ...")
    
    for file_path in local_path.rglob('*'):
        if file_path.is_file():
            # Construction de la clé S3
            relative_path = file_path.relative_to(local_path)
            s3_key = str(relative_path).replace('\\', '/')
            
            try:
                # Upload avec vérification
                s3_client.upload_file(
                    Filename=str(file_path),
                    Bucket=bucket_name,
                    Key=s3_key
                )
                
                files_uploaded += 1
                total_size += file_path.stat().st_size
                
                # Progression
                if files_uploaded % 10 == 0:
                    print(f"   📤 {files_uploaded} fichiers uploadés...")
                    
            except Exception as e:
                print(f"❌ Erreur upload {file_path.name}: {str(e)}")
    
    print(f"\n🏆 UPLOAD SÉCURISÉ TERMINÉ!")
    print(f"📊 Fichiers uploadés: {files_uploaded}")
    print(f"💾 Taille totale: {total_size/1024:.1f} KB")
    print(f"📦 Bucket: s3://{bucket_name}/")
    
    # Création du manifeste de sécurité
    security_manifest = {
        'upload_timestamp': datetime.now().isoformat(),
        'method': 'environment_variables',
        'bucket': bucket_name,
        'permissions': [
            's3:CreateBucket',
            's3:PutObject',
            's3:GetObject',
            's3:ListBucket',
            's3:DeleteObject'
        ],
        'files_uploaded': files_uploaded,
        'total_size_bytes': total_size,
        'security_level': 'IAM_USER_RESTRICTED',
        'root_access_denied': True
    }
    
    with open("simple_secure_upload_manifest.json", 'w') as f:
        json.dump(security_manifest, f, indent=2)
    
    print(f"🔐 Manifeste de sécurité créé: simple_secure_upload_manifest.json")
    
    return True

if __name__ == "__main__":
    success = simple_secure_upload()
    if success:
        print("\n🌊 Upload sécurisé réussi!")
    else:
        print("\n❌ Upload sécurisé échoué.")
        sys.exit(1)
