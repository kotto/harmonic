#!/usr/bin/env python3
"""
TÉLÉCHARGEMENT DEEPSEEK AVEC CREDENTIALS AWS EXISTANTES
==========================================================

Script optimisé pour télécharger Deepseek Coder 6.7B en utilisant
vos credentials AWS déjà configurés dans le workspace.
"""

import os
import sys
import time
import json
import boto3
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class DeepseekDownloader:
    """Téléchargeur Deepseek avec credentials AWS"""
    
    def __init__(self):
        self.bucket_name = "deepseek-models-326095712935"
        self.region = "eu-west-3"
        self.model_name = "deepseek-coder-6.7b-base"
        self.model_path = Path("./deepseek-model")
        
        # Initialiser le client AWS avec vos credentials
        try:
            self.s3_client = boto3.client('s3', region_name=self.region)
            logger.info("✅ Client AWS initialisé avec vos credentials")
        except Exception as e:
            logger.error(f"❌ Erreur initialisation AWS: {e}")
            sys.exit(1)
        
        # Créer le répertoire de travail
        self.model_path.mkdir(exist_ok=True)
        
        # Métriques
        self.metrics = {
            'start_time': time.time(),
            'tokenizer_size': 0,
            'model_size': 0,
            'upload_size': 0,
            'total_size': 0
        }
    
    def check_aws_connectivity(self) -> bool:
        """Vérifier la connectivité AWS"""
        try:
            # Tester la connexion S3
            self.s3_client.list_buckets()
            logger.info("✅ Connectivité AWS vérifiée")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur connectivité AWS: {e}")
            return False
    
                
    def create_s3_bucket(self) -> bool:
        """Créer le bucket S3 si nécessaire"""
        try:
            # Vérifier si le bucket existe
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"✅ Bucket {self.bucket_name} existe déjà")
            return True
        except:
            try:
                # Créer le bucket avec la bonne configuration pour eu-west-3
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={
                        'LocationConstraint': 'eu-west-3'
                    }
                )
                logger.info(f"✅ Bucket {self_bucket_name} créé avec succès")
                return True
            except Exception as e:
                logger.error(f"❌ Erreur création bucket: {e}")
                return False
    
    def download_tokenizer(self) -> bool:
        """Télécharger le tokenizer"""
        try:
            logger.info("📥 Téléchargement du tokenizer Deepseek...")
            start_time = time.time()
            
            # Télécharger le tokenizer
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Sauvegarder localement
            tokenizer_path = self.model_path / "tokenizer"
            tokenizer.save_pretrained(tokenizer_path)
            
            # Calculer la taille
            tokenizer_size = sum(
                os.path.getsize(os.path.join(root, file))
                for root, _, files in os.walk(tokenizer_path)
                for file in files
            )
            
            self.metrics['tokenizer_size'] = tokenizer_size
            self.metrics['tokenizer_time'] = time.time() - start_time
            
            logger.info(f"✅ Tokenizer téléchargé: {tokenizer_size / 1024 / 1024:.1f} MB")
            logger.info(f"⏱️ Temps: {self.metrics['tokenizer_time']:.1f} secondes")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur téléchargement tokenizer: {e}")
            return False
    
    def download_model(self) -> bool:
        """Télécharger le modèle Deepseek"""
        try:
            logger.info("📥 Téléchargement du modèle Deepseek...")
            logger.info("⚠️  ATTENTION: Cette étape peut prendre 30-60 minutes")
            
            start_time = time.time()
            
            # Configuration optimisée pour le téléchargement
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16,  # Optimisation mémoire
                device_map='auto',          # Utiliser GPU si disponible
                low_cpu_mem_usage=True,     # Optimisation CPU
                trust_remote_code=True,      # Confiance dans le code distant
                cache_dir=self.model_path / "cache"  # Cache pour accélérer
            )
            
            # Sauvegarder localement
            model_path = self.model_path / "model"
            model.save_pretrained(model_path)
            
            # Calculer la taille
            model_size = sum(
                os.path.getsize(os.path.join(root, file))
                for root, _, files in os.walk(model_path)
                for file in files
            )
            
            self.metrics['model_size'] = model_size
            self.metrics['model_time'] = time.time() - start_time
            
            logger.info(f"✅ Modèle téléchargé: {model_size / 1024 / 1024:.1f} MB")
            logger.info(f"⏱️ Temps: {self.metrics['model_time']:.1f} secondes")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur téléchargement modèle: {e}")
            return False
    
    def upload_to_s3(self) -> bool:
        """Uploader le modèle sur S3"""
        try:
            logger.info("📤 Upload du modèle vers S3...")
            start_time = time.time()
            
            total_uploaded = 0
            
            # Uploader le tokenizer
            logger.info("   📤 Upload du tokenizer...")
            for root, dirs, files in os.walk(self.model_path / "tokenizer"):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.model_path)
                    s3_key = f"deepseek-coder-6.7b/tokenizer/{relative_path}"
                    
                    self.s3_client.upload_file(file_path, f"{self.bucket_name}/{s3_key}")
                    total_uploaded += os.path.getsize(file_path)
            
            # Uploader le modèle
            logger.info("   📤 Upload du modèle...")
            for root, dirs, files in os.walk(self.model_path / "model"):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.model_path)
                    s3_key = f"deepseek-coder-6.7b/model/{relative_path}"
                    
                    self.s3_client.upload_file(file_path, f"{self.bucket_name}/{s3_key}")
                    total_uploaded += os.path.getsize(file_path)
            
            self.metrics['upload_size'] = total_uploaded
            self.metrics['upload_time'] = time.time() - start_time
            
            logger.info(f"✅ Upload terminé: {total_uploaded / 1024 / 1024:.1f} MB")
            logger.info(f"⏱️ Temps: {self.metrics['upload_time']:.1f} secondes")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur upload S3: {e}")
            return False
    
    def verify_upload(self) -> bool:
        """Vérifier l'upload sur S3"""
        try:
            logger.info("🔍 Vérification de l'upload sur S3...")
            
            # Lister les objets sur S3
            objects = list(self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix="deepseek-coder-6.7b/"
            ))
            
            total_size = sum(obj['Size'] for obj in objects)
            object_count = len(objects)
            
            logger.info(f"✅ Vérification réussie:")
            logger.info(f"   📊 Objets: {object_count}")
            logger.info(f"   📊 Taille totale: {total_size / 1024 / 1024:.1f} MB")
            
            # Vérifier les fichiers clés
            key_files = [
                "deepseek-coder-6.7b/model/config.json",
                "deepseek-coder-6.7b/model/pytorch_model.bin",
                "deepseek-coder-6.7b/tokenizer/tokenizer.json"
            ]
            
            for key_file in key_files:
                try:
                    self.s3_client.head_object(
                        Bucket=self.bucket_name,
                        Key=key_file
                    )
                    logger.info(f"   ✅ {key_file}")
                except:
                    logger.warning(f"   ⚠️ {key_file} non trouvé")
            
            return True
            
        except Exception as run_error:
            logger.error(f"❌ Erreur vérification S3: {run_error}")
            return False
    
    def save_metrics(self):
        """Sauvegarder les métriques"""
        self.metrics['end_time'] = time.time()
        self.metrics['total_time'] = self.metrics['end_time'] - self.metrics['start_time']
        self.metrics['total_size'] = self.metrics['tokenizer_size'] + self.metrics['model_size']
        
        try:
            with open('deepseek_download_metrics.json', 'w') as f:
                json.dump(self.metrics, f, indent=2)
            logger.info("✅ Métriques sauvegardées dans deepseek_download_metrics.json")
        except Exception as e:
            logger.warning(f"⚠️ Erreur sauvegarde métriques: {e}")
    
    def display_summary(self):
        """Afficher le résumé final"""
        print("\n" + "=" * 80)
        print("🌊 RÉSUMÉ DU TÉLÉCHARGEMENT DEEPSEEK")
        print("=" * 80)
        
        print(f"📅 Début: {time.ctime(self.metrics['start_time'])}")
        print(f"🏁 Fin: {time.ctime(self.metrics['end_time'])}")
        print(f"⏱️ Durée totale: {self.metrics['total_time'] / 60:.1f} minutes")
        print("")
        
        print("📊 TAILLES:")
        print(f"   📦 Tokenizer: {self.metrics['tokenizer_size'] / 1024 / 1024:.1f} MB")
        print(f"   🤖 Modèle: {self.metrics['model_size'] / 1024 / 1024:.1f} MB")
        print(f"   📊 Total: {self.metrics['total_size'] / 1024 / 1024:.1f} MB")
        print("")
        
        print("⏱️ TEMPS:")
        print(f"   📥 Tokenizer: {self.metrics['tokenizer_time']:.1f} secondes")
        print(f"   🤖 Modèle: {self.metrics['model_time'] / 60:.1f} minutes")
        print(f"   📤 Upload: {self.metrics['upload_time']:.1f} secondes")
        print("")
        
        print("📊 STATUT:")
        if self.metrics.get('tokenizer_size', 0) > 0 and self.metrics.get('model_size', 0) > 0:
            print("   ✅ SUCCÈS COMPLET")
            print(f"   🌊 Bucket: {self.bucket_name}")
            print(f"   🌍 Région: {self.region}")
        else:
            print("   ❌ ÉCHEC - Vérifiez les logs pour plus de détails")
        
        print("=" * 80)
    
    def run_download(self) -> bool:
        """Exécuter le téléchargement complet"""
        logger.info("🚀 DÉMARRAGE DU TÉLÉCHARGEMENT DEEPSEEK")
        logger.info("=" * 60)
        
        try:
            # Étape 1: Vérifier la connectivité
            if not self.check_aws_connectivity():
                return False
            
            # Étape 2: Créer le bucket S3
            if not self.create_s3_bucket():
                return False
            
            # Étape 3: Télécharger le tokenizer
            if not self.download_tokenizer():
                return False
            
            # Étape 4: Télécharger le modèle
            if not self.download_model():
                return False
            
            # Étape 5: Uploader sur S3
            if not self.upload_to_s3():
                return False
            
            # Étape 6: Vérifier l'upload
            if not self.verify_upload():
                return False
            
            # Étape 7: Sauvegarder les métriques
            self.save_metrics()
            
            # Étape 8: Afficher le résumé
            self.display_summary()
            
            logger.info("🎉 TÉLÉCHARGEMENT TERMINÉ AVEC SUCCÈS!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur critique: {e}")
            return False

def main():
    """Fonction principale"""
    print("🌊 DEEPSEEK DOWNLOADER AVEC CREDENTIALS AWS")
    print("=" * 60)
    print("📦 Utilisation de vos credentials AWS existantes")
    print("🤖 Modèle: Deepseek Coder 6.7B")
    print("🌍 Région: eu-west-3")
    print("=" * 60)
    
    downloader = DeepseekDownloader()
    success = downloader.run_download()
    
    if success:
        print("\n🌊 TÉLÉCHARGEMENT TERMINÉ AVEC SUCCÈS!")
        print("📊 Le modèle Deepseek est maintenant disponible sur AWS S3")
        print("🎯 Vous pouvez maintenant l'utiliser avec la couche harmonique!")
        exit(0)
    else:
        print("\n❌ Le téléchargement a rencontré des erreurs")
        print("📄 Vérifiez les logs pour plus de détails")
        exit(1)

if __name__ == "__main__":
    main()
