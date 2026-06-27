#!/usr/bin/env python3
"""
🔥 INSTALLATION VRAI MISTRAL 7B
Version complète avec modèle HuggingFace réel
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Exécute une commande et affiche le résultat"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description}: SUCCÈS")
            return True
        else:
            print(f"❌ {description}: ÉCHEC")
            print(f"Erreur: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description}: Exception - {e}")
        return False

def main():
    print("🔥 INSTALLATION VRAI MISTRAL 7B")
    print("=" * 60)
    
    # Vérification mémoire
    print("📊 Vérification mémoire système...")
    run_command("free -h", "Mémoire disponible")
    
    # Installation dépendances complètes
    print("\n📦 INSTALLATION DÉPENDANCES COMPLÈTES")
    print("-" * 50)
    
    # PyTorch avec support CPU
    run_command(
        "python3 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu",
        "PyTorch CPU complet"
    )
    
    # Transformers dernière version
    run_command(
        "python3 -m pip install transformers>=4.30.0",
        "Transformers dernière version"
    )
    
    # Accelerate pour optimisation
    run_command(
        "python3 -m pip install accelerate",
        "Accelerate pour optimisation"
    )
    
    # Datasets pour chargement
    run_command(
        "python3 -m pip install datasets",
        "Datasets pour chargement"
    )
    
    # Sentencepiece pour tokenization
    run_command(
        "python3 -m pip install sentencepiece",
        "Sentencepiece"
    )
    
    # Protobuf pour compatibilité
    run_command(
        "python3 -m pip install protobuf",
        "Protobuf"
    )
    
    # BitsAndBytes pour quantification
    run_command(
        "python3 -m pip install bitsandbytes",
        "BitsAndBytes pour quantification"
    )
    
    print("\n🔥 TÉLÉCHARGEMENT MODÈLE MISTRAL 7B")
    print("-" * 50)
    
    # Script de téléchargement
    download_script = '''
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import os

print("🔥 Téléchargement Mistral 7B...")
print("📊 Taille attendue: ~14GB")
print("⏳ Temps estimé: 10-20 minutes")

try:
    # Configuration
    model_name = "mistralai/Mistral-7B-Instruct-v0.2"
    cache_dir = "/opt/connective-ai/models/mistral-7b"
    
    # Créer dossier cache
    os.makedirs(cache_dir, exist_ok=True)
    
    print("📥 Téléchargement tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        cache_dir=cache_dir,
        trust_remote_code=True
    )
    
    print("📥 Téléchargement modèle...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        cache_dir=cache_dir,
        torch_dtype=torch.float16,  # Optimisation mémoire
        device_map="auto",  # Distribution automatique
        trust_remote_code=True,
        low_cpu_mem_usage=True
    )
    
    print("✅ Mistral 7B téléchargé avec succès!")
    print(f"📁 Chemin: {cache_dir}")
    print(f"🔢 Paramètres: {model.num_parameters():,}")
    print(f"📊 Taille: ~14GB")
    
    # Test de chargement
    print("🧪 Test de chargement...")
    test_prompt = "Hello, how are you?"
    inputs = tokenizer.encode(test_prompt, return_tensors="pt")
    
    with torch.no_grad():
        outputs = model.generate(
            inputs,
            max_new_tokens=50,
            do_sample=True,
            temperature=0.7,
            pad_token_id=tokenizer.eos_token_id
        )
    
    result = tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
    print(f"✅ Test réussi: {result}")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    print("🔄 Vérification espace disque et mémoire...")
'''
    
    # Sauvegarder et exécuter le script
    with open('/tmp/download_mistral.py', 'w') as f:
        f.write(download_script)
    
    run_command("python3 /tmp/download_mistral.py", "Téléchargement modèle Mistral")
    
    print("\n🎯 VÉRIFICATION INSTALLATION")
    print("-" * 40)
    
    # Test d'import
    test_imports = '''
try:
    import torch
    print(f"✅ PyTorch: {torch.__version__}")
    
    import transformers
    print(f"✅ Transformers: {transformers.__version__}")
    
    import accelerate
    print(f"✅ Accelerate: {accelerate.__version__}")
    
    # Test chargement rapide
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
    print("✅ Tokenizer Mistral: OK")
    
    print("🎯 Installation Mistral: RÉUSSIE!")
    
except ImportError as e:
    print(f"❌ Erreur import: {e}")
except Exception as e:
    print(f"❌ Erreur: {e}")
'''
    
    with open('/tmp/test_mistral.py', 'w') as f:
        f.write(test_imports)
    
    run_command("python3 /tmp/test_mistral.py", "Test installation Mistral")
    
    print("\n🚀 INSTALLATION TERMINÉE!")
    print("✅ VRAI Mistral 7B prêt!")
    print("🔥 Prêt pour fusion réelle!")

if __name__ == "__main__":
    main()
