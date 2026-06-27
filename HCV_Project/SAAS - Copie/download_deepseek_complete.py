#!/usr/bin/env python3
"""
🚀 TÉLÉCHARGEMENT COMPLET DEEPSEEK V4 PRO
Télécharge le modèle complet depuis S3 et applique la transformation harmonique
"""

import boto3
import json
import os
import sys
from pathlib import Path
from tqdm import tqdm
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Constantes harmoniques
PHI = (1 + 5 ** 0.5) / 2
ALPHA = 1.175569459083219

class DeepSeekCompleteDownloader:
    """Téléchargeur complet de DeepSeek V4 Pro avec transformation harmonique"""
    
    def __init__(self):
        # Configuration AWS
        with open('aws_credentials_secure.json', 'r') as f:
            config = json.load(f)
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=config['aws_access_key_id'],
            aws_secret_access_key=config['aws_secret_access_key'],
            region_name=config['region']
        )
        
        self.bucket_name = "harmonic-ai-knowledge-base"
        self.local_model_path = Path("./deepseek-v4-pro-complete")
        self.local_model_path.mkdir(exist_ok=True)
        
        print("🚀 TÉLÉCHARGEMENT COMPLET DEEPSEEK V4 PRO")
        print("=" * 60)
        print(f"📁 Dossier local: {self.local_model_path.absolute()}")
        print(f"🌊 Bucket S3: {self.bucket_name}")
    
    def check_available_models(self):
        """Vérifier les modèles disponibles sur S3"""
        print("\n🔍 RECHERCHE MODÈLES SUR S3...")
        
        # Chercher dans tous les buckets accessibles
        buckets = ['deepseek-models-326095712935', 'harmonic-ai-knowledge-base']
        available_models = {}
        
        for bucket in buckets:
            try:
                objects = self.s3_client.list_objects_v2(
                    Bucket=bucket,
                    MaxKeys=100
                )
                
                if 'Contents' in objects:
                    model_files = [obj for obj in objects['Contents'] 
                                if any(x in obj['Key'].lower() for x in ['deepseek', 'model', '.bin', '.safetensors'])]
                    
                    if model_files:
                        available_models[bucket] = model_files
                        print(f"✅ Bucket {bucket}: {len(model_files)} fichiers de modèle")
                        for obj in model_files[:5]:
                            size_mb = obj['Size'] / (1024*1024)
                            print(f"   📁 {obj['Key']} ({size_mb:.1f} MB)")
                
            except Exception as e:
                print(f"❌ Erreur bucket {bucket}: {e}")
        
        return available_models
    
    def download_model_files(self, bucket, model_files):
        """Télécharger les fichiers du modèle"""
        print(f"\n📥 TÉLÉCHARGEMENT DEPUIS {bucket}...")
        
        downloaded_files = []
        total_size = sum(obj['Size'] for obj in model_files)
        
        with tqdm(total=total_size, unit='B', unit_scale=True, desc="Téléchargement") as pbar:
            for obj in model_files:
                local_path = self.local_model_path / Path(obj['Key']).name
                
                try:
                    # Téléchargement avec progression
                    self.s3_client.download_file(
                        Bucket=bucket,
                        Key=obj['Key'],
                        Filename=str(local_path)
                    )
                    
                    downloaded_files.append(str(local_path))
                    pbar.update(obj['Size'])
                    
                except Exception as e:
                    print(f"❌ Erreur téléchargement {obj['Key']}: {e}")
        
        print(f"✅ {len(downloaded_files)} fichiers téléchargés")
        return downloaded_files
    
    def load_and_transform_model(self):
        """Charger et transformer le modèle harmoniquement"""
        print("\n🌊 TRANSFORMATION HARMONIQUE...")
        
        try:
            # Essayer de charger depuis le dossier local
            print("🔧 Chargement du modèle...")
            
            if (self.local_model_path / "config.json").exists():
                model = AutoModelForCausalLM.from_pretrained(
                    str(self.local_model_path),
                    torch_dtype=torch.float16,
                    device_map="auto",
                    trust_remote_code=True,
                    low_cpu_mem_usage=True
                )
                
                tokenizer = AutoTokenizer.from_pretrained(
                    str(self.local_model_path),
                    trust_remote_code=True
                )
                
                print("✅ Modèle chargé avec succès")
                
                # Appliquer la transformation harmonique
                print("⚡ Application de la transformation harmonique...")
                self._apply_harmonic_transformation(model)
                
                print("🎯 Modèle transformé et prêt")
                return model, tokenizer
                
            else:
                print("❌ Aucun modèle valide trouvé dans le dossier")
                return None, None
                
        except Exception as e:
            print(f"❌ Erreur chargement/transformation: {e}")
            return None, None
    
    def _apply_harmonic_transformation(self, model):
        """Appliquer la transformation harmonique complète"""
        
        total_params = 0
        transformed = 0
        
        for name, param in model.named_parameters():
            if not param.requires_grad:
                continue
            
            # Couches prioritaires
            if any(k in name for k in ['gate_proj', 'up_proj', 'down_proj', 'q_proj', 'k_proj', 'v_proj', 'attn']):
                with torch.no_grad():
                    if len(param.shape) == 2:
                        # Normalisation L2
                        norm = torch.norm(param, dim=1, keepdim=True)
                        param.data = param.data / norm
                        
                        # Rotation harmonique ALPHA
                        c = torch.cos(ALPHA)
                        s = torch.sin(ALPHA)
                        
                        # Créer matrice de rotation
                        R = torch.eye(param.shape[1], device=param.device)
                        for i in range(0, param.shape[1]-1, 2):
                            R[i, i] = c
                            R[i, i+1] = -s
                            R[i+1, i] = s
                            R[i+1, i+1] = c
                        
                        # Appliquer rotation
                        param.data = param.data @ R
                        
                        # Filtrage résonance PHI
                        resonance = torch.abs(torch.norm(param.data, dim=1) - PHI)
                        mask = resonance < (1.0 / PHI)
                        param.data[~mask] = 0.0
                        
                        # Multiplication par PHI
                        param.data = param.data * PHI
                        
                        transformed += 1
            
            total_params += 1
        
        print(f"✅ Transformation terminée: {transformed}/{total_params} couches transformées")
        
        # Verrouillage des poids
        for param in model.parameters():
            param.requires_grad = False
    
    def save_harmonic_model(self, model, tokenizer):
        """Sauvegarder le modèle harmonique"""
        print("\n💾 SAUVEGARDE MODÈLE HARMONIQUE...")
        
        harmonic_path = self.local_model_path / "harmonic"
        harmonic_path.mkdir(exist_ok=True)
        
        model.save_pretrained(str(harmonic_path))
        tokenizer.save_pretrained(str(harmonic_path))
        
        print(f"✅ Modèle harmonique sauvegardé dans: {harmonic_path}")
    
    def run_complete_process(self):
        """Exécuter le processus complet"""
        
        # 1. Vérifier les modèles disponibles
        available_models = self.check_available_models()
        
        if not available_models:
            print("\n❌ AUCUN MODÈLE TROUVÉ SUR S3")
            print("\n🔧 OPTIONS:")
            print("1. Vérifier les permissions S3 pour le bucket deepseek-models-326095712935")
            print("2. Télécharger manuellement DeepSeek V4 Pro")
            print("3. Utiliser le modèle local existant (si disponible)")
            return False
        
        # 2. Télécharger les fichiers
        for bucket, model_files in available_models.items():
            downloaded_files = self.download_model_files(bucket, model_files)
            
            if downloaded_files:
                # 3. Charger et transformer
                model, tokenizer = self.load_and_transform_model()
                
                if model is not None:
                    # 4. Sauvegarder le modèle harmonique
                    self.save_harmonic_model(model, tokenizer)
                    
                    print("\n🏆 SUCCÈS COMPLET!")
                    print("✅ DeepSeek V4 Pro téléchargé et transformé harmoniquement")
                    print("✅ Modèle prêt pour LM Arena")
                    return True
        
        return False

if __name__ == "__main__":
    downloader = DeepSeekCompleteDownloader()
    success = downloader.run_complete_process()
    
    if not success:
        print("\n🌊 ALTERNATIVE: Utiliser le patch harmonique existant")
        print("Le fichier deepseek_harmonic_patch.py peut être utilisé sur un modèle local")
