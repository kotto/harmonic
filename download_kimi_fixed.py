#!/usr/bin/env python3
"""
Script pour telecharger le modele Kimi K2.5 quantifie
"""

import os
import sys
from huggingface_hub import snapshot_download

def download_kimi_k25():
    """Telecharge le modele Kimi K2.5 quantifie"""
    
    # Repertoire de destination sur E:
    local_dir = "E:\\Kimi-K2.5\\model"
    
    # Creer le repertoire s'il n'existe pas
    os.makedirs(local_dir, exist_ok=True)
    
    print(f"Telechargement du modele Kimi K2.5 quantifie...")
    print(f"Destination: {local_dir}")
    print("Cette operation peut prendre plusieurs heures selon votre connexion internet.")
    print("La taille du modele est d'environ 375 Go (version Q2_K_XL).")
    print("\nDebut du telechargement...")
    
    try:
        # Telecharger le modele quantifie GGUF
        # Nous utilisons la version 2-bit (Q2_K_XL) pour economiser de l'espace
        model_id = "unsloth/Kimi-K2.5-GGUF"
        
        print(f"Telechargement depuis: {model_id}")
        print("Cette operation peut prendre plusieurs heures...")
        
        # Telecharger les fichiers specifiques pour la version Q2_K_XL
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
        
        print("\n[OK] Telechargement termine avec succes !")
        print(f"Modele disponible dans: {local_dir}")
        
        # Lister les fichiers telecharges
        print("\n[FILE] Fichiers telecharges:")
        total_size = 0
        for root, dirs, files in os.walk(local_dir):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                total_size += file_size
                file_size_gb = file_size / (1024**3)
                print(f"  - {file} ({file_size_gb:.2f} Go)")
        
        print(f"\n[STATS] Taille totale: {total_size / (1024**3):.2f} Go")
        
    except Exception as e:
        print(f"\n[ERROR] Erreur lors du telechargement: {e}")
        print("Verifiez:")
        print("1. Que vous avez assez d'espace disque (au moins 400 Go libre)")
        print("2. Que votre connexion internet est stable")
        print("3. Que vous avez les permissions d'ecriture sur le disque E:")
        return False
    
    return True

def check_disk_space():
    """Verifie l'espace disque disponible"""
    import shutil
    
    try:
        total, used, free = shutil.disk_usage("E:\\")
        
        print(f"[STATS] Espace disque E::")
        print(f"  Total: {total / (1024**3):.2f} Go")
        print(f"  Utilise: {used / (1024**3):.2f} Go")
        print(f"  Libre: {free / (1024**3):.2f} Go")
        
        # Espace necessaire (version quantifiee 2-bit)
        required_space_gb = 400
        required_space = required_space_gb * (1024**3)  # 400 Go en octets
        
        if free < required_space:
            print(f"\n[WARN] Attention: Espace insuffisant!")
            print(f"  Espace libre: {free / (1024**3):.2f} Go")
            print(f"  Espace requis: {required_space_gb} Go")
            return False
        
        print(f"\n[OK] Espace disque suffisant!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Erreur lors de la verification de l'espace disque: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Telechargement du modele Kimi K2.5")
    print("=" * 60)
    
    # Verifier l'espace disque
    if not check_disk_space():
        print("\nVeuillez liberer de l'espace sur le disque E: avant de continuer.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    
    # Demander confirmation
    response = input("Voulez-vous commencer le telechargement? (oui/non): ").strip().lower()
    
    if response not in ['oui', 'o', 'yes', 'y']:
        print("Telechargement annule.")
        sys.exit(0)
    
    # Telecharger le modele
    success = download_kimi_k25()
    
    if success:
        print("\n" + "=" * 60)
        print("Instructions pour utiliser le modele:")
        print("=" * 60)
        print("1. Installez llama.cpp: https://github.com/ggml-org/llama.cpp")
        print("2. Compilez avec support CUDA: cmake -B build -DGGML_CUDA=ON")
        print("3. Utilisez le serveur: ./build/bin/llama-server -m E:\\Kimi-K2.5\\model\\Kimi-K2.5-UD-Q2_K_XL-00001-of-00005.gguf")
        print("4. Accedez a l'interface web: http://localhost:8080")
        print("\nPour une utilisation avancee, consultez la documentation de llama.cpp.")
    else:
        print("\nLe telechargement a echoue. Veuillez verifier les erreurs ci-dessus.")
