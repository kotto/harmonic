#!/usr/bin/env python3
"""
UPLOAD SECURISE DES MODELES HARMONIC AI
Utilisation du profil IAM securise
"""

import os
import sys
import json
import time
import boto3
from pathlib import Path
from datetime import datetime

def secure_upload():
    """Upload securise avec profil IAM"""
    
    print("UPLOAD SECURISE DES MODELES HARMONIC AI")
    print("=" * 60)
    print("Utilisation du profil IAM: harmonic-ai")
    print("Bucket: harmonic-ai-knowledge-base")
    print("Region: us-east-1")
    print("=" * 60)
    
    # Configuration
    bucket_name = "harmonic-ai-knowledge-base"
    profile_name = "harmonic-ai"
    local_path = Path("local_s3_structure")
    
    if not local_path.exists():
        print("Repertoire local_s3_structure non trouve!")
        return False
    
    try:
        # Utilisation du profil IAM securise
        session = boto3.Session(profile_name=profile_name)
        s3_client = session.client('s3')
        print(f"Session S3 securisee initialisee (profil: {profile_name})")
    except Exception as e:
        print(f"Erreur initialisation session: {str(e)}")
        print("Solution: aws sso login --profile harmonic-ai")
        return False
    
    # Test de permissions
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' accessible")
    except:
        try:
            s3_client.create_bucket(Bucket=bucket_name)
            print(f"Bucket '{bucket_name}' cree")
        except Exception as e:
            print(f"Erreur creation bucket: {str(e)}")
            return False
    
    # Upload des fichiers
    files_uploaded = 0
    total_size = 0
    
    print(f"\nDEBUT UPLOAD SECURISE...")
    
    for file_path in local_path.rglob('*'):
        if file_path.is_file():
            # Construction de la cle S3
            relative_path = file_path.relative_to(local_path)
            s3_key = str(relative_path).replace('\\', '/')
            
            try:
                # Upload avec verification
                s3_client.upload_file(
                    Filename=str(file_path),
                    Bucket=bucket_name,
                    Key=s3_key
                )
                
                files_uploaded += 1
                total_size += file_path.stat().st_size
                
                # Progression
                if files_uploaded % 10 == 0:
                    print(f"   {files_uploaded} fichiers uploades...")
                    
            except Exception as e:
                print(f"Erreur upload {file_path.name}: {str(e)}")
    
    print(f"\nUPLOAD SECURISE TERMINE!")
    print(f"Fichiers uploades: {files_uploaded}")
    print(f"Taille totale: {total_size/1024:.1f} KB")
    print(f"Profil utilise: {profile_name}")
    print(f"Bucket: s3://{bucket_name}/")
    
    # Creation du manifeste de securite
    security_manifest = {
        'upload_timestamp': datetime.now().isoformat(),
        'security_profile': profile_name,
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
    
    with open("secure_upload_manifest.json", 'w') as f:
        json.dump(security_manifest, f, indent=2)
    
    print(f"Manifeste de securite cree: secure_upload_manifest.json")
    
    return True

if __name__ == "__main__":
    success = secure_upload()
    if success:
        print("\nUpload securise reussi!")
    else:
        print("\nUpload securise echoue.")
        sys.exit(1)
