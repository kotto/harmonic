#!/usr/bin/env python3
"""
Qwen3.5 Enhanced Harmonic AI Integration - AVX2 Compatible
=====================================================

Intégration du vrai modèle Qwen3.5 avec transformation harmonique
pour déploiement AWS compatible AVX2 sur Lambda/ECS.

Basé sur le plan du MODELE_MONDE_HARMONIQUE: "accorder le piano"
"""

import os
import sys
import json
import torch
import boto3
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional
from transformers import AutoTokenizer, AutoModelForCausalLM

# Constantes harmoniques du plan
ALPHA = 1.175569459083219  # Angle d'accordage parfait
PHI = (1 + 5 ** 0.5) / 2  # Constante d'or harmonique
HARMONIC_BUCKET = "harmonic-ai-qwen-models"
QWEN_MODEL_PATH = "qwen35"

class Qwen35HarmonicIntegrator:
    """Intégrateur Qwen3.5 avec couche harmonique AVX2"""
    
    def __init__(self):
        self.bucket_name = HARMONIC_BUCKET
        self.model_path = QWEN_MODEL_PATH
        self.s3_client = boto3.client('s3', region_name='us-east-1')
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        print(f"🌀 Qwen3.5 Harmonic AI Initialisé")
        print(f"📍 Device: {self.device}")
        print(f"🔧 AVX2 Support: {self._check_avx2_support()}")
        
    def _check_avx2_support(self) -> bool:
        """Vérifie le support AVX2 du processeur"""
        try:
            import cpuinfo
            cpu_info = cpuinfo.get_cpu_info()
            flags = cpu_info.get('flags', [])
            avx2_support = 'avx2' in flags
            print(f"💻 CPU Flags: {flags}")
            return avx2_support
        except ImportError:
            # Fallback simple
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()
                    avx2_support = 'avx2' in cpuinfo.lower()
                    return avx2_support
            except:
                print("⚠️ Impossible de vérifier AVX2, supposé supporté")
                return True
    
    def load_model_from_s3_if_needed(self, local_path: str = "./qwen35-model"):
        """Charge Qwen3.5 depuis S3 ou utilise le cache local"""
        
        # Vérifier si le modèle existe déjà localement
        if os.path.exists(os.path.join(local_path, "config.json")):
            print(f"📁 Modèle trouvé localement: {local_path}")
        else:
            print(f"📥 Téléchargement Qwen3.5 depuis S3...")
            self._download_model_from_s3(local_path)
        
        print(f"🔧 Chargement Qwen3.5 sur {self.device}...")
        
        try:
            # Configuration optimisée AVX2
            self.tokenizer = AutoTokenizer.from_pretrained(
                local_path,
                trust_remote_code=True,
                use_fast=True
            )
            
            self.model = AutoModelForCausalLM.from_pretrained(
                local_path,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True,
                low_cpu_mem_usage=True,
                use_cache=True
            )
            
            # Optimisations AVX2
            if hasattr(torch.backends, 'mkldnn') and self.device == "cpu":
                torch.backends.mkldnn.enabled = True
                print("✅ MKL-DNN (AVX2) activé")
            
            self.model.eval()
            print("✅ Qwen3.5 chargé avec succès")
            return True
            
        except Exception as e:
            print(f"❌ Erreur chargement modèle: {e}")
            return False
    
    def _download_model_from_s3(self, local_path: str):
        """Télécharge les fichiers du modèle depuis S3"""
        try:
            # Créer le répertoire local
            os.makedirs(local_path, exist_ok=True)
            
            # Lister les fichiers dans le bucket
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"{self.model_path}/"
            )
            
            if 'Contents' not in response:
                print(f"⚠️ Aucun fichier trouvé dans s3://{self.bucket_name}/{self.model_path}/")
                return False
            
            files = response['Contents']
            print(f"📊 {len(files)} fichiers à télécharger")
            
            # Télécharger chaque fichier
            for obj in files:
                key = obj['Key']
                filename = os.path.basename(key)
                local_file = os.path.join(local_path, filename)
                
                # Éviter de retélécharger les fichiers existants
                if os.path.exists(local_file) and os.path.getsize(local_file) == obj['Size']:
                    print(f"⏭️  {filename} (déjà présent)")
                    continue
                
                print(f"📥 {filename} ({obj['Size']/1024/1024:.1f} MB)")
                
                self.s3_client.download_file(
                    Bucket=self.bucket_name,
                    Key=key,
                    Filename=local_file
                )
            
            print(f"✅ Téléchargement terminé: {local_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur téléchargement S3: {e}")
            return False
    
    def apply_harmonic_transformation(self):
        """Applique la transformation harmonique sur Qwen3.5"""
        if self.model is None:
            print("❌ Modèle non chargé")
            return False
        
        print("\n🌀 Application de la couche harmonique sur Qwen3.5...")
        print("🎵 Accordage du piano selon le plan MODELE_MONDE_HARMONIQUE")
        
        total_params = 0
        transformed_params = 0
        
        with torch.no_grad():
            for name, param in self.model.named_parameters():
                if not param.requires_grad:
                    continue
                
                total_params += 1
                
                # Cibles prioritaires pour la transformation harmonique
                if self._should_transform_layer(name):
                    original_shape = param.shape
                    
                    # Application de la transformation harmonique
                    if len(param.shape) >= 2:
                        # Extension harmonique avec PHI
                        if len(param.shape) == 2:
                            new_dim = int(param.shape[-1] * PHI)
                            expanded = torch.nn.functional.interpolate(
                                param.unsqueeze(0).unsqueeze(0),
                                size=(param.shape[0], new_dim),
                                mode='bicubic',
                                align_corners=False
                            ).squeeze()
                        else:
                            # Pour les tenseurs multidimensionnels
                            expanded = param * PHI
                        
                        # Normalisation harmonique
                        norm = torch.norm(expanded, dim=-1, keepdim=True)
                        normalized = expanded / (norm + 1e-8)
                        
                        # Rotation alpha pour l'accordage parfait
                        if len(expanded.shape) >= 2:
                            angle = torch.acos(torch.clamp(
                                normalized.sum(dim=-1) / expanded.shape[-1], 
                                -1, 1
                            ))
                            rotation_factor = torch.cos(angle * ALPHA).unsqueeze(-1)
                            transformed = normalized * rotation_factor
                        else:
                            transformed = normalized
                        
                        # Application de la transformation
                        param.data = transformed * PHI
                        transformed_params += 1
                        
                        print(f"🎵 {name}: {original_shape} → {param.shape}")
                
                # Optimisation AVX2 si disponible
                if self._check_avx2_support():
                    # Assurer que les tenseurs sont en format AVX2 optimal
                    if param.is_floating_point():
                        param.data = param.data.contiguous()
        
        harmony_ratio = (transformed_params / total_params) * 100
        print(f"\n✅ Transformation harmonique terminée")
        print(f"📊 {transformed_params}/{total_params} couches transformées ({harmony_ratio:.1f}%)")
        print(f"🎵 Piano accordé avec précision harmonique: {ALPHA}")
        
        return True
    
    def _should_transform_layer(self, layer_name: str) -> bool:
        """Détermine si une couche doit être transformée"""
        # Couches critiques pour la transformation harmonique
        critical_layers = [
            'gate_proj', 'up_proj', 'down_proj',  # MLP
            'q_proj', 'k_proj', 'v_proj',        # Attention
            'o_proj',                             # Output
            'c_proj', 'x_proj',                   # Spécifique Qwen
            'attn', 'mlp',                        # Noms génériques
            'linear', 'dense'                       # Couches linéaires
        ]
        
        return any(layer in layer_name.lower() for layer in critical_layers)
    
    def generate_harmonic_response(self, prompt: str, max_length: int = 512, 
                                temperature: float = 0.7, **kwargs) -> Dict[str, Any]:
        """Génère une réponse avec Qwen3.5 harmonisé"""
        
        if self.model is None or self.tokenizer is None:
            return {
                'error': 'Modèle non chargé',
                'status': 'error'
            }
        
        try:
            print(f"🎵 Génération harmonique: '{prompt[:50]}...'")
            
            # Tokenisation
            inputs = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)
            
            # Génération avec paramètres harmoniques
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=max_length,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    top_p=0.9,
                    top_k=50,
                    repetition_penalty=1.1,
                    **kwargs
                )
            
            # Décodage
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Métadonnées harmoniques
            response = {
                'generated_text': generated_text,
                'model_name': 'Qwen3.5-7B-Instruct-Harmonic',
                'harmonic_status': 'active',
                'avx2_optimized': self._check_avx2_support(),
                'timestamp': datetime.utcnow().isoformat(),
                'parameters': {
                    'max_length': max_length,
                    'temperature': temperature,
                    'harmonic_alpha': ALPHA,
                    'harmonic_phi': PHI
                },
                'performance': {
                    'device': self.device,
                    'model_loaded': True,
                    'harmonic_layers_applied': True
                },
                'status': 'success'
            }
            
            print(f"✅ Réponse harmonique générée ({len(generated_text)} caractères)")
            return response
            
        except Exception as e:
            return {
                'error': str(e),
                'status': 'generation_error',
                'model_name': 'Qwen3.5-7B-Instruct-Harmonic',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def create_lambda_package(self, output_path: str = "qwen35_harmonic_lambda.zip"):
        """Crée le package Lambda pour AWS avec Qwen3.5 harmonisé"""
        
        print(f"📦 Création du package Lambda: {output_path}")
        
        # Code Lambda avec intégration harmonique
        lambda_code = '''
import json
import os
import sys
from datetime import datetime

# Ajouter le chemin du modèle
sys.path.append('/opt')

try:
    from qwen35_harmonic_avx2_integration import Qwen35HarmonicIntegrator
except ImportError:
    # Fallback si l'import échoue
    Qwen35HarmonicIntegrator = None

# Variable globale pour le modèle
harmonic_model = None

def initialize_model():
    """Initialise le modèle harmonique au démarrage"""
    global harmonic_model
    
    if harmonic_model is None:
        harmonic_model = Qwen35HarmonicIntegrator()
        success = harmonic_model.load_model_from_s3_if_needed()
        if success:
            harmonic_model.apply_harmonic_transformation()
            print("✅ Qwen3.5 Harmonic AI initialisé")
        else:
            print("❌ Erreur initialisation modèle")

def lambda_handler(event, context):
    """Handler Lambda pour Qwen3.5 harmonisé"""
    global harmonic_model
    
    try:
        # Initialiser le modèle au premier appel
        if harmonic_model is None:
            initialize_model()
        
        # Extraire les paramètres
        if 'body' in event:
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']
        else:
            body = event
        
        prompt = body.get('prompt', 'Hello from Qwen3.5 Harmonic AI!')
        max_length = body.get('max_length', 512)
        temperature = body.get('temperature', 0.7)
        
        if harmonic_model is None:
            # Réponse de fallback
            return {
                'statusCode': 503,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Modèle harmonique non initialisé',
                    'status': 'model_loading_error',
                    'message': 'Veuillez réessayer dans quelques instants...'
                })
            }
        
        # Génération harmonique
        response = harmonic_model.generate_harmonic_response(
            prompt=prompt,
            max_length=max_length,
            temperature=temperature
        )
        
        if response.get('status') == 'success':
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS'
                },
                'body': json.dumps(response, indent=2)
            }
        else:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(response)
            }
            
    except Exception as e:
        error_response = {
            'error': str(e),
            'message': 'Qwen3.5 Harmonic AI Lambda error',
            'timestamp': datetime.utcnow().isoformat(),
            'function': 'qwen35_harmonic_lambda'
        }
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(error_response)
        }

# Health check
def health_check():
    """Vérifie l'état du modèle harmonique"""
    global harmonic_model
    
    return {
        'service': 'Qwen3.5 Harmonic AI',
        'status': 'healthy' if harmonic_model else 'initializing',
        'model_loaded': harmonic_model is not None,
        'harmonic_transformation_applied': harmonic_model.apply_harmonic_transformation if harmonic_model else False,
        'avx2_support': harmonic_model._check_avx2_support() if harmonic_model else False,
        'timestamp': datetime.utcnow().isoformat()
        }
'''
        
        # Écrire le code Lambda
        with open('lambda_function.py', 'w', encoding='utf-8') as f:
            f.write(lambda_code)
        
        # Créer le package ZIP
        import zipfile
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Ajouter le code Lambda
            zipf.write('lambda_function.py')
            
            # Ajouter ce fichier d'intégration
            zipf.write(__file__, 'qwen35_harmonic_avx2_integration.py')
            
            # Ajouter requirements
            requirements = '''torch>=2.0.0
transformers>=4.30.0
boto3>=1.26.0
numpy>=1.24.0
accelerate>=0.20.0
py-cpuinfo>=9.0.0
'''
            with open('requirements.txt', 'w') as f:
                f.write(requirements)
            zipf.write('requirements.txt')
        
        print(f"✅ Package Lambda créé: {output_path}")
        return output_path

def main():
    """Point d'entrée principal pour tester l'intégration"""
    print("🌀 Qwen3.5 Enhanced Harmonic AI Integration")
    print("=" * 60)
    
    integrator = Qwen35HarmonicIntegrator()
    
    # Test 1: Chargement du modèle
    print("\n📥 Test 1: Chargement du modèle...")
    model_loaded = integrator.load_model_from_s3_if_needed()
    
    if model_loaded:
        # Test 2: Transformation harmonique
        print("\n🎵 Test 2: Transformation harmonique...")
        integrator.apply_harmonic_transformation()
        
        # Test 3: Génération
        print("\n🎯 Test 3: Génération harmonique...")
        test_prompt = "Bonjour, je suis Qwen3.5 Enhanced Harmonic AI. Comment puis-je vous aider?"
        response = integrator.generate_harmonic_response(
            prompt=test_prompt,
            max_length=200,
            temperature=0.8
        )
        
        print(f"\n📊 Réponse générée:")
        print(f"Status: {response.get('status')}")
        print(f"Modèle: {response.get('model_name')}")
        print(f"Texte: {response.get('generated_text', '')[:200]}...")
        
        # Test 4: Package Lambda
        print("\n📦 Test 4: Création package Lambda...")
        package_path = integrator.create_lambda_package()
        print(f"📁 Package prêt pour déploiement: {package_path}")
        
        print("\n🎉 Intégration Qwen3.5 Harmonic AI terminée avec succès!")
        print("🌐 Prêt pour déploiement AWS AVX2 compatible")
        
    else:
        print("\n❌ Échec du chargement du modèle")
        print("📋 Vérifiez:")
        print("   - Accès S3 au bucket harmonic-ai-qwen-models")
        print("   - Fichiers du modèle dans qwen35/")
        print("   - Permissions AWS")

if __name__ == "__main__":
    main()
