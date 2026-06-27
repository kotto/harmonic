#!/usr/bin/env python3
"""
🚀 TÉLÉCHARGEMENT MISTRAL ALTERNATIF
Script pour télécharger Mistral avec toutes les solutions
"""

import os
import sys
import subprocess
from pathlib import Path

def mettre_a_jour_transformers():
    """Mettre à jour transformers"""
    print("🔄 MISE À JOUR TRANSFORMERS:")
    
    commandes = [
        ["pip", "install", "--upgrade", "transformers"],
        ["pip", "install", "--upgrade", "tokenizers"],
        ["pip", "install", "--upgrade", "huggingface_hub"]
    ]
    
    for cmd in commandes:
        try:
            print(f"   💻 {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("   ✅ Succès")
            else:
                print(f"   ❌ Erreur: {result.stderr[:100]}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

def tester_mistral_v0_2():
    """Tester Mistral v0.2"""
    print("\n🧪 TEST MISTRAL V0.2:")
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        print("   📦 Tokenizer v0.2...")
        tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
        print("   ✅ Tokenizer OK")
        
        print("   📦 Modèle v0.2...")
        model = AutoModelForCausalLM.from_pretrained(
            "mistralai/Mistral-7B-Instruct-v0.2",
            torch_dtype="auto",
            device_map="auto"
        )
        print("   ✅ Modèle OK")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def tester_thebloke_version():
    """Tester la version TheBloke"""
    print("\n🧪 TEST THEBLOKE VERSION:")
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        print("   📦 TheBloke tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained("TheBloke/Mistral-7B-Instruct-v0.2-GGUF")
        print("   ✅ Tokenizer OK")
        
        print("   📦 TheBloke modèle...")
        model = AutoModelForCausalLM.from_pretrained(
            "TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
            torch_dtype="auto",
            device_map="auto"
        )
        print("   ✅ Modèle OK")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 TÉLÉCHARGEMENT MISTRAL ALTERNATIF")
    print("=" * 50)
    
    # Étape 1: Mettre à jour
    mettre_a_jour_transformers()
    
    # Étape 2: Tester v0.2
    if tester_mistral_v0_2():
        print("\n🎉 SUCCÈS - MISTRAL V0.2 FONCTIONNEL")
        return
    
    # Étape 3: Tester TheBloke
    if tester_thebloke_version():
        print("\n🎉 SUCCÈS - THEBLOKE VERSION FONCTIONNELLE")
        return
    
    print("\n❌ ÉCHEC - AUCUNE VERSION FONCTIONNELLE")
    print("🔧 Vérifier l'installation manuelle")

if __name__ == "__main__":
    main()
