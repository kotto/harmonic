#!/usr/bin/env python3
"""
🔍 VÉRIFICATION DU CONTENU DU BUCKET S3
Vérifie ce qui est disponible sur le bucket AWS S3
"""

import os
import sys
import boto3
from pathlib import Path

# Configuration AWS
AWS_REGION = "us-east-1"
HARMONIC_BUCKET = "harmonic-ai-knowledge-base"

def check_s3_bucket():
    """Vérifie le contenu du bucket S3"""
    
    print("🔍 VÉRIFICATION DU BUCKET S3")
    print("=" * 50)
    print(f"📦 Bucket: {HARMONIC_BUCKET}")
    print(f"🌍 Région: {AWS_REGION}")
    print("=" * 50)
    
    try:
        # Initialisation client S3
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        
        # Vérification de l'existence du bucket
        try:
            s3_client.head_bucket(Bucket=HARMONIC_BUCKET)
            print(f"✅ Bucket '{HARMONIC_BUCKET}' accessible")
        except Exception as e:
            print(f"❌ Bucket non accessible: {str(e)}")
            return
        
        # Liste des objets dans le bucket
        print(f"\n📋 CONTENU DU BUCKET:")
        print("-" * 30)
        
        objects = []
        try:
            paginator = s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(Bucket=HARMONIC_BUCKET)
            
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        objects.append(obj['Key'])
                        print(f"   📄 {obj['Key']} ({obj['Size']} bytes)")
        
        except Exception as e:
            print(f"❌ Erreur liste des objets: {str(e)}")
            return
        
        if not objects:
            print("   📭 Bucket vide")
        else:
            print(f"\n📊 STATISTIQUES:")
            print(f"   Total objets: {len(objects)}")
            
            # Analyse par catégorie
            categories = {}
            for obj in objects:
                category = obj.split('/')[0] if '/' in obj else 'root'
                if category not in categories:
                    categories[category] = []
                categories[category].append(obj)
            
            print(f"\n📂 RÉPARTITION PAR CATÉGORIE:")
            for category, files in sorted(categories.items()):
                print(f"   📂 {category}: {len(files)} fichiers")
                for file in files[:3]:  # Affiche les 3 premiers fichiers
                    print(f"      📄 {file}")
                if len(files) > 3:
                    print(f"      ... et {len(files) - 3} autres fichiers")
        
        # Vérification des permissions
        print(f"\n🔐 VÉRIFICATION DES PERMISSIONS:")
        print("-" * 35)
        
        try:
            # Test de lecture sur un objet
            if objects:
                test_key = objects[0]
                try:
                    s3_client.head_object(Bucket=HARMONIC_BUCKET, Key=test_key)
                    print(f"✅ Permission de lecture OK sur: {test_key}")
                except Exception as e:
                    print(f"❌ Erreur lecture sur {test_key}: {str(e)}")
            else:
                print("ℹ️ Aucun objet à tester")
        except Exception as e:
            print(f"❌ Erreur vérification permissions: {str(e)}")
        
    except Exception as e:
        print(f"❌ Erreur générale: {str(e)}")

def check_local_models():
    """Vérifie les modèles locaux disponibles"""
    
    print(f"\n📁 VÉRIFICATION DES MODÈLES LOCAUX")
    print("=" * 40)
    
    # Vérification des modèles locaux
    local_paths = [
        "harmonic_ai",
        "simple_real_output",
        "batch_output",
        "real_batch_output_fixed"
    ]
    
    for path in local_paths:
        path_obj = Path(path)
        if path_obj.exists():
            print(f"✅ {path}/ existe")
            
            # Comptage des fichiers
            files = list(path_obj.rglob('*'))
            files = [f for f in files if f.is_file()]
            print(f"   📁 {len(files)} fichiers")
            
            # Analyse par sous-répertoire
            dirs = [d for d in path_obj.iterdir() if d.is_dir()]
            for dir_path in dirs[:5]:  # Limite à 5 sous-répertoires
                dir_files = list(dir_path.rglob('*'))
                dir_files = [f for f in dir_files if f.is_file()]
                print(f"      📂 {dir_path.name}/: {len(dir_files)} fichiers")
        else:
            print(f"❌ {path}/ n'existe pas")

def main():
    """Fonction principale"""
    
    print("🔍 VÉRIFICATION COMPLÈTE DES MODÈLES HARMONIC AI")
    print("=" * 60)
    
    # Vérification S3
    check_s3_bucket()
    
    # Vérification locale
    check_local_models()
    
    print(f"\n🌊 VÉRIFICATION TERMINÉE!")

if __name__ == "__main__":
    main()
