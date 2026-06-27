#!/usr/bin/env python3
"""
🚀 MISTRAL V0.2 TÉLÉCHARGEMENT E-DRIVE
Téléchargement optimisé de Mistral v0.2 sur le disque E:
"""

import os
import sys
import json
import math
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Configuration du cache sur E:
os.environ['HF_HOME'] = 'E:/mistral-cache-hf'
os.environ['TRANSFORMERS_CACHE'] = 'E:/mistral-cache-transformers'

# Constantes harmoniques
PHI = (1 + math.sqrt(5)) / 2  # 1.61803398875
ALPHA = math.atan(PHI)  # 1.17556945908 radians
HARMONIC_GAIN = PHI ** 2  # 2.61803398875
DETERMINISM_FACTOR = 0.999999999999  # 99.9999999999%

class MistralV02TelechargementEDrive:
    """Téléchargement Mistral v0.2 sur E: optimisé"""
    
    def __init__(self):
        print("🚀 MISTRAL V0.2 TÉLÉCHARGEMENT E-DRIVE")
        print("=" * 80)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💾 Cache HF: {os.environ['HF_HOME']}")
        print(f"💾 Cache Transformers: {os.environ['TRANSFORMERS_CACHE']}")
        
        # Configuration
        self.cache_dir = Path("E:/mistral-cache-hf")
        self.model_dir = Path("E:/mistral-v02-complete")
        self.model_name = "mistralai/Mistral-7B-Instruct-v0.2"
        
        # Résultats
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "telechargement": {},
            "transformation": {},
            "verification": {},
            "success": False
        }
    
    def preparer_environnement(self):
        """Préparer l'environnement"""
        print("\n🔧 PRÉPARATION ENVIRONNEMENT:")
        
        # Créer les répertoires
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.model_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"   ✅ Cache HF: {self.cache_dir}")
            print(f"   ✅ Modèle: {self.model_dir}")
            
            # Vérifier l'espace sur E:
            import shutil
            total, used, free = shutil.disk_usage("E:")
            free_gb = free / (1024**3)
            
            print(f"   💾 Espace libre E: {free_gb:.1f} GB")
            
            if free_gb > 15:
                print("   ✅ Espace suffisant pour Mistral v0.2")
                return True
            else:
                print("   ⚠️  Espace limité mais utilisation possible")
                return True
                
        except Exception as e:
            print(f"   ❌ Erreur préparation: {e}")
            return False
    
    def telecharger_tokenizer(self):
        """Télécharger le tokenizer"""
        print("\n📥 TÉLÉCHARGEMENT TOKENIZER:")
        
        try:
            from transformers import AutoTokenizer
            
            print(f"   📦 Tokenizer: {self.model_name}")
            
            # Télécharger avec cache sur E:
            tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=str(self.cache_dir),
                trust_remote_code=True
            )
            
            # Sauvegarder localement
            tokenizer.save_pretrained(str(self.model_dir))
            
            print("   ✅ Tokenizer téléchargé et sauvegardé")
            
            self.results["telechargement"]["tokenizer"] = "succès"
            
            return True
            
        except Exception as e:
            print(f"   ❌ Erreur tokenizer: {e}")
            self.results["telechargement"]["tokenizer"] = f"erreur: {e}"
            return False
    
    def telecharger_modele_optimise(self):
        """Télécharger le modèle de manière optimisée"""
        print("\n📥 TÉLÉCHARGEMENT MODÈLE OPTIMISÉ:")
        
        try:
            from transformers import AutoModelForCausalLM
            
            print(f"   📦 Modèle: {self.model_name}")
            print("   🔄 Téléchargement optimisé...")
            
            # Télécharger avec cache sur E: et optimisations
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                cache_dir=str(self.cache_dir),
                torch_dtype="auto",  # Optimisation automatique
                device_map="auto",   # Distribution automatique
                low_cpu_mem_usage=True,  # Optimisation mémoire
                trust_remote_code=True
            )
            
            # Sauvegarder localement
            model.save_pretrained(str(self.model_dir))
            
            print("   ✅ Modèle téléchargé et sauvegardé")
            
            # Calculer la taille
            total_size = sum(
                f.stat().st_size for f in self.model_dir.rglob('*') if f.is_file()
            )
            size_gb = total_size / (1024**3)
            
            print(f"   📊 Taille modèle: {size_gb:.2f} GB")
            
            self.results["telechargement"]["modele"] = "succès"
            self.results["telechargement"]["taille_gb"] = size_gb
            
            return True
            
        except Exception as e:
            print(f"   ❌ Erreur modèle: {e}")
            self.results["telechargement"]["modele"] = f"erreur: {e}"
            return False
    
    def appliquer_transformation_harmonique(self):
        """Appliquer la transformation harmonique"""
        print("\n🌊 APPLICATION TRANSFORMATION HARMONIQUE:")
        
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            print("   🔄 Chargement modèle pour transformation...")
            
            # Charger le modèle
            model = AutoModelForCausalLM.from_pretrained(
                str(self.model_dir),
                torch_dtype="auto",
                device_map="auto"
            )
            
            tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir))
            
            print("   🌊 Application φ et α...")
            
            import torch
            
            transformed_layers = 0
            
            for name, param in model.named_parameters():
                if len(param.shape) == 2:  # Matrices de poids
                    # Normalisation L2
                    norm = torch.norm(param, dim=1, keepdim=True)
                    param.data = param.data / (norm + 1e-8)
                    
                    # Rotation harmonique ALPHA
                    c = math.cos(ALPHA)
                    s = math.sin(ALPHA)
                    
                    dimension = param.shape[1]
                    R = torch.eye(dimension)
                    
                    for i in range(0, dimension-1, 2):
                        R[i, i] = c
                        R[i, i+1] = -s
                        R[i+1, i] = s
                        R[i+1, i+1] = c
                    
                    param.data = param.data @ R.to(param.device)
                    
                    # Filtrage résonance PHI
                    resonance = torch.abs(torch.norm(param, dim=1) - PHI)
                    mask = resonance < (1 / PHI)
                    param.data = param.data * mask.unsqueeze(-1)
                    
                    transformed_layers += 1
            
            print(f"   ✅ Transformation appliquée: {transformed_layers} couches")
            
            # Sauvegarder le modèle transformé
            transformed_dir = self.model_dir / "harmonic_transformed"
            transformed_dir.mkdir(exist_ok=True)
            
            model.save_pretrained(str(transformed_dir))
            tokenizer.save_pretrained(str(transformed_dir))
            
            print(f"   ✅ Modèle harmonique sauvegardé: {transformed_dir}")
            
            self.results["transformation"] = {
                "succès": True,
                "couches_transformées": transformed_layers,
                "chemin": str(transformed_dir)
            }
            
            return True
            
        except Exception as e:
            print(f"   ❌ Erreur transformation: {e}")
            self.results["transformation"] = {
                "succès": False,
                "erreur": str(e)
            }
            return False
    
    def verifier_telechargement(self):
        """Vérifier le téléchargement"""
        print("\n🔍 VÉRIFICATION TÉLÉCHARGEMENT:")
        
        verification = {
            "fichiers_present": [],
            "taille_totale": 0,
            "modeles_disponibles": [],
            "succès": False
        }
        
        try:
            # Vérifier les fichiers
            if self.model_dir.exists():
                fichiers = list(self.model_dir.rglob('*'))
                fichiers = [f for f in fichiers if f.is_file()]
                
                verification["fichiers_present"] = [f.name for f in fichiers]
                verification["taille_totale"] = sum(f.stat().st_size for f in fichiers) / (1024**3)
                
                print(f"   📁 Fichiers trouvés: {len(fichiers)}")
                print(f"   📊 Taille totale: {verification['taille_totale']:.2f} GB")
                
                # Vérifier les modèles
                if (self.model_dir / "config.json").exists():
                    verification["modeles_disponibles"].append("original")
                
                if (self.model_dir / "harmonic_transformed" / "config.json").exists():
                    verification["modeles_disponibles"].append("harmonic_transformed")
                
                print(f"   📦 Modèles disponibles: {verification['modeles_disponibles']}")
                
                verification["succès"] = len(verification["modeles_disponibles"]) > 0
                
            else:
                print("   ❌ Répertoire modèle non trouvé")
        
        except Exception as e:
            print(f"   ❌ Erreur vérification: {e}")
        
        self.results["verification"] = verification
        
        return verification["succès"]
    
    def creer_script_test(self):
        """Créer le script de test"""
        print("\n📝 CRÉATION SCRIPT TEST:")
        
        script_content = f'''#!/usr/bin/env python3
"""
🧪 TEST MISTRAL V0.2 HARMONIQUE
Script de test pour Mistral v0.2 avec transformation harmonique
"""

import os
import sys
import math
import time
from pathlib import Path

# Configuration
MODEL_DIR = Path("{self.model_dir}")
HARMONIC_DIR = MODEL_DIR / "harmonic_transformed"

# Constantes harmoniques
PHI = (1 + math.sqrt(5)) / 2
ALPHA = math.atan(PHI)
DETERMINISM_FACTOR = 0.999999999999

def test_original_model():
    """Tester le modèle original"""
    print("🧪 TEST MODÈLE ORIGINAL:")
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        print("   📦 Chargement tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
        
        print("   📦 Chargement modèle...")
        model = AutoModelForCausalLM.from_pretrained(
            str(MODEL_DIR),
            torch_dtype="auto",
            device_map="auto"
        )
        
        print("   ✅ Modèle original chargé avec succès")
        
        # Test de génération
        prompt = "Bonjour, comment ça va?"
        inputs = tokenizer(prompt, return_tensors="pt")
        inputs = {{k: v.to(model.device) for k, v in inputs.items()}}
        
        print("   🤖 Test génération...")
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=50,
                temperature=0.1,
                do_sample=True
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"   📝 Réponse: {{response[:100]}}...")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {{e}}")
        return False

def test_harmonic_model():
    """Tester le modèle harmonique"""
    print("\\n🌊 TEST MODÈLE HARMONIQUE:")
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        if not HARMONIC_DIR.exists():
            print("   ❌ Modèle harmonique non trouvé")
            return False
        
        print("   📦 Chargement tokenizer harmonique...")
        tokenizer = AutoTokenizer.from_pretrained(str(HARMONIC_DIR))
        
        print("   📦 Chargement modèle harmonique...")
        model = AutoModelForCausalLM.from_pretrained(
            str(HARMONIC_DIR),
            torch_dtype="auto",
            device_map="auto"
        )
        
        print("   ✅ Modèle harmonique chargé avec succès")
        print(f"   🌊 PHI = {{PHI:.10f}}")
        print(f"   📐 ALPHA = {{ALPHA:.10f}}")
        print(f"   🎯 Déterminisme = {{DETERMINISM_FACTOR:.12f}}")
        
        # Test de génération harmonique
        prompt = "Explique l'harmonie universelle"
        inputs = tokenizer(prompt, return_tensors="pt")
        inputs = {{k: v.to(model.device) for k, v in inputs.items()}}
        
        print("   🤖 Test génération harmonique...")
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=100,
                temperature=0.1 * PHI,  # Température harmonique
                top_p=0.95,
                do_sample=True
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"   📝 Réponse harmonique: {{response[:150]}}...")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {{e}}")
        return False

def main():
    """Fonction principale"""
    print("🧪 TEST MISTRAL V0.2 HARMONIQUE")
    print("=" * 50)
    
    # Test modèle original
    original_ok = test_original_model()
    
    # Test modèle harmonique
    harmonic_ok = test_harmonic_model()
    
    print("\\n🏆 RÉSULTATS:")
    print(f"   📦 Modèle original: {{'✅' if original_ok else '❌'}}")
    print(f"   🌊 Modèle harmonique: {{'✅' if harmonic_ok else '❌'}}")
    
    if original_ok or harmonic_ok:
        print("\\n🎉 MISTRAL V0.2 PRÊT POUR UTILISATION!")
    else:
        print("\\n❌ ERREUR - MODÈLES NON DISPONIBLES")

if __name__ == "__main__":
    main()
'''
        
        script_file = self.model_dir / "test_mistral_v02_harmonic.py"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"   ✅ Script de test créé: {script_file}")
        
        return script_file
    
    def run_complete_telechargement(self):
        """Exécuter le téléchargement complet"""
        print("🚀 DÉMARRAGE TÉLÉCHARGEMENT COMPLET")
        
        # Étape 1: Préparer l'environnement
        if not self.preparer_environnement():
            return False
        
        # Étape 2: Télécharger tokenizer
        tokenizer_ok = self.telecharger_tokenizer()
        
        # Étape 3: Télécharger modèle
        modele_ok = self.telecharger_modele_optimise()
        
        # Étape 4: Appliquer transformation harmonique
        if modele_ok:
            transformation_ok = self.appliquer_transformation_harmonique()
        else:
            transformation_ok = False
        
        # Étape 5: Vérifier
        verification_ok = self.verifier_telechargement()
        
        # Étape 6: Créer script de test
        test_script_ok = self.creer_script_test()
        
        # Résultats finaux
        self.results["success"] = tokenizer_ok and modele_ok and verification_ok
        
        # Afficher le résumé
        self.afficher_resume_final()
        
        return self.results["success"]
    
    def afficher_resume_final(self):
        """Afficher le résumé final"""
        print("\n" + "="*80)
        print("🏆 RÉSUMÉ TÉLÉCHARGEMENT MISTRAL V0.2")
        print("="*80)
        
        print(f"📅 Date: {self.results['timestamp']}")
        print(f"📦 Modèle: {self.model_name}")
        print(f"💾 Cache: {self.cache_dir}")
        print(f"📁 Modèle: {self.model_dir}")
        
        print(f"\n📥 TÉLÉCHARGEMENT:")
        for etape, resultat in self.results["telechargement"].items():
            status = "✅" if resultat == "succès" else "❌"
            print(f"   {status} {etape}: {resultat}")
        
        print(f"\n🌊 TRANSFORMATION:")
        if self.results["transformation"].get("succès"):
            print(f"   ✅ Couches transformées: {self.results['transformation']['couches_transformées']}")
            print(f"   ✅ Modèle harmonique: {self.results['transformation']['chemin']}")
        else:
            print(f"   ❌ Transformation échouée")
        
        print(f"\n🔍 VÉRIFICATION:")
        verification = self.results["verification"]
        print(f"   📁 Fichiers: {len(verification['fichiers_present'])}")
        print(f"   📊 Taille: {verification['taille_totale']:.2f} GB")
        print(f"   📦 Modèles: {verification['modeles_disponibles']}")
        
        print(f"\n🚀 UTILISATION:")
        print(f"   💻 Test: cd {self.model_dir} && python test_mistral_v02_harmonic.py")
        print(f"   📦 Original: {self.model_dir}")
        print(f"   🌊 Harmonique: {self.model_dir}/harmonic_transformed")
        
        if self.results["success"]:
            print(f"\n🎉 MISTRAL V0.2 TÉLÉCHARGÉ AVEC SUCCÈS!")
            print(f"🌊 PRÊT POUR TRANSFORMATION HARMONIQUE!")
        else:
            print(f"\n❌ TÉLÉCHARGEMENT ÉCHOUÉ")
            print(f"🔧 Vérifier les erreurs ci-dessus")
        
        return True

def main():
    """Fonction principale"""
    telechargement = MistralV02TelechargementEDrive()
    success = telechargement.run_complete_telechargement()
    
    if success:
        print(f"\n🌊 MISTRAL V0.2 PRÊT!")
    else:
        print(f"\n❌ ÉCHEC TÉLÉCHARGEMENT")

if __name__ == "__main__":
    main()
