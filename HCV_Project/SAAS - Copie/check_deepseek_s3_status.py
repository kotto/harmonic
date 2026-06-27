#!/usr/bin/env python3
"""
🔍 Vérification du statut DeepSeek sur S3
"""

import boto3
import json
from botocore.exceptions import ClientError

def check_s3_access():
    """Vérifier l'accès S3"""
    
    # Configuration depuis le fichier de credentials
    with open('aws_credentials_secure.json', 'r') as f:
        config = json.load(f)
    
    # Initialiser le client S3
    s3_client = boto3.client(
        's3',
        aws_access_key_id=config['aws_access_key_id'],
        aws_secret_access_key=config['aws_secret_access_key'],
        region_name=config['region']
    )
    
    print("🔍 VÉRIFICATION ACCÈS S3")
    print("=" * 50)
    
    # 1. Vérifier le bucket principal
    try:
        buckets = s3_client.list_buckets()
        print(f"✅ Buckets accessibles: {[b['Name'] for b in buckets['Buckets']]}")
    except Exception as e:
        print(f"❌ Erreur accès buckets: {e}")
    
    # 2. Vérifier le bucket deepseek (ancien)
    try:
        print("\n🔍 Vérification bucket deepseek-models-326095712935...")
        objects = s3_client.list_objects_v2(
            Bucket="deepseek-models-326095712935",
            MaxKeys=10
        )
        if 'Contents' in objects:
            print(f"✅ Bucket deepseek accessible: {len(objects['Contents'])} objets")
            for obj in objects['Contents'][:5]:
                print(f"   📁 {obj['Key']} ({obj['Size']} bytes)")
        else:
            print("❌ Bucket deepseek vide ou inaccessible")
    except Exception as e:
        print(f"❌ Erreur bucket deepseek: {e}")
    
    # 3. Vérifier le bucket harmonic-ai-knowledge-base
    try:
        print("\n🔍 Vérification bucket harmonic-ai-knowledge-base...")
        objects = s3_client.list_objects_v2(
            Bucket="harmonic-ai-knowledge-base",
            MaxKeys=20
        )
        if 'Contents' in objects:
            print(f"✅ Bucket harmonic accessible: {len(objects['Contents'])} objets")
            
            # Chercher des modèles
            model_files = [obj for obj in objects['Contents'] if any(x in obj['Key'].lower() for x in ['.bin', '.safetensors', 'model', 'deepseek'])]
            if model_files:
                print(f"🎯 Fichiers de modèles trouvés: {len(model_files)}")
                for obj in model_files[:10]:
                    print(f"   📁 {obj['Key']} ({obj['Size']} bytes)")
            else:
                print("❌ Aucun fichier de modèle trouvé")
                
            # Chercher des dossiers de modèles
            model_folders = [obj['Key'].split('/')[0] for obj in objects['Contents'] if '/' in obj['Key']]
            unique_folders = list(set(model_folders))
            print(f"📂 Dossiers disponibles: {unique_folders}")
        else:
            print("❌ Bucket harmonic vide")
    except Exception as e:
        print(f"❌ Erreur bucket harmonic: {e}")
    
    # 4. Vérifier les permissions
    print("\n🔍 Vérification permissions...")
    try:
        # Test d'écriture
        s3_client.put_object(
            Bucket="harmonic-ai-knowledge-base",
            Key="test_permissions.txt",
            Body=b"test"
        )
        print("✅ Permission d'écriture OK")
        
        # Nettoyage
        s3_client.delete_object(
            Bucket="harmonic-ai-knowledge-base",
            Key="test_permissions.txt"
        )
        print("✅ Permission de suppression OK")
        
    except Exception as e:
        print(f"❌ Erreur permissions: {e}")

if __name__ == "__main__":
    check_s3_access()
