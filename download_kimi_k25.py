#!/usr/bin/env python3
"""
Script pour télécharger le modèle Kimi K2.5 quantifié
"""

import os
import sys
from huggingface_hub import snapshot_download

def download_kimi_k25():
    """Télécharge le modèle Kimi K2.5 quantifié"""
    
    # Répertoire de destination sur E:
    local_dir = "E:\\Kimi-K2.5\\model"
    
    # Créer le répertoire s'il n'existe pas
    os.makedirs(local_dir, exist_ok=True)
    
    print(f"Téléchargement du modèle Kimi K2.5 quantifié...")
    print(f"Destination: {local_dir}")
    print("Cette opération peut prendre plusieurs heures selon votre connexion internet.")
    print("La taille du modèle est d'environ 375 Go (version Q2_K_XL).")
    print("\nDébut du téléchargement...")
    
    try:
        # Télécharger le modèle quantifié GGUF
        # Nous utilisons la version 2-bit (Q2_K_XL) pour économiser de l'espace
        model_id = "unsloth/Kimi-K2.5-GGUF"
        
        print(f"Téléchargement depuis: {model_id}")
        print("Cette opération peut prendre plusieurs heures...")
        
        # Télécharger les fichiers spécifiques pour la version Q2_K_XL
        snapshot_download(
            repo_id=model_id,
            local_dir=local_dir,
            allow_patterns=[
                "Kimi-K2.5-UD-Q2_K_XL-*.gguf",
                "*.json",
                "*.txt",
                "*.md"
            ],
            local_dir_use_symlinks=False,
            resume_download=True,
            max_workers=4
        )
        
        print("\n✅ Téléchargement terminé avec succès !")
        print(f"Modèle disponible dans: {local_dir}")
        
        # Lister les fichiers téléchargés
        print("\n📁 Fichiers téléchargés:")
        total_size = 0
        for root, dirs, files in os.walk(local_dir):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                total_size += file_size
                file_size_gb = file_size / (1024**3)
                print(f"  - {file} ({file_size_gb:.2f} Go)")
        
        print(f"\n📊 Taille totale: {total_size / (1024**3):.2f} Go")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du téléchargement: {e}")
        print("Vérifiez:")
        print("1. Que vous avez assez d'espace disque (au moins 400 Go libre)")
        print("2. Que votre connexion internet est stable")
        print("3. Que vous avez les permissions d'écriture sur le disque E:")
        return False
    
    return True

def check_disk_space():
    """Vérifie l'espace disque disponible"""
    import shutil
    
    try:
        total, used, free = shutil.disk_usage("E:\\")
        
        print(f"📊 Espace disque E::")
        print(f"  Total: {total / (1024**3):.2f} Go")
        print(f"  Utilisé: {used / (1024**3):.2f} Go")
        print(f"  Libre: {free / (1024**3):.2f} Go")
        
        # Espace nécessaire (version quantifiée 2-bit)
        required_space_gb = 400
        required_space = required_space_gb * (1024**3)  # 400 Go en octets
        
        if free < required_space:
            print(f"\n⚠️  Attention: Espace insuffisant!")
            print(f"  Espace libre: {free / (1024**3):.2f} Go")
            print(f"  Espace requis: {required_space_gb} Go")
            return False
        
        print(f"\n✅ Espace disque suffisant!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de l'espace disque: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Téléchargement du modèle Kimi K2.5")
    print("=" * 60)
    
    # Vérifier l'espace disque
    if not check_disk_space():
        print("\nVeuillez libérer de l'espace sur le disque E: avant de continuer.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    
    # Demander confirmation
    response = input("Voulez-vous commencer le téléchargement? (oui/non): ").strip().lower()
    
    if response not in ['oui', 'o', 'yes', 'y']:
        print("Téléchargement annulé.")
        sys.exit(0)
    
    # Télécharger le modèle
    success = download_kimi_k25()
    
    if success:
        print("\n" + "=" * 60)
        print("📋 Instructions pour utiliser le modèle:")
        print("=" * 60)
        print("1. Installez llama.cpp: https://github.com/ggml-org/llama.cpp")
        print("2. Compilez avec support CUDA: cmake -B build -DGGML_CUDA=ON")
        print("3. Utilisez le serveur: ./build/bin/llama-server -m E:\\Kimi-K2.5\\model\\Kimi-K2.5-UD-Q2_K_XL-00001-of-00005.gguf")
        print("4. Accédez à l'interface web: http://localhost:8080")
        print("\nPour une utilisation avancée, consultez la documentation de llama.cpp.")
    else:
        print("\nLe téléchargement a échoué. Veuillez vérifier les erreurs ci-dessus.")