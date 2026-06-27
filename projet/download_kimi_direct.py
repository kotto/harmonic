#!/usr/bin/env python3
"""
Script pour telecharger le modele Kimi K2.5 (demarrage direct sans confirmation)
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
        print("\n[FICHIERS TELECHARGES]")
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
    print("\n" + "=" * 70)
    print("KIMI K2.5 - TELECHARGEMENT DU MODELE QUANTIFIE")
    print("=" * 70)
    print("\n[ATTENTION]")
    print("Ce script va telecharger le modele Kimi K2.5 (version quantifiee)")
    print("Cette operation peut prendre plusieurs heures selon votre connexion.")
    print("\nAppuyez sur Ctrl+C a tout moment pour interrompre le telechargement.")
    print("Vous pourrez le reprendre plus tard en relancant ce script.")
    print("=" * 70)
    
    # Verifier l'espace disque
    if not check_disk_space():
        print("\n[ERROR] Espace disque insuffisant!")
        print("Veuillez liberer au moins 400 Go sur le disque E: avant de continuer.")
        input("\nAppuyez sur Entree pour quitter...")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    
    # Commencer automatiquement sans confirmation
    print("\n[INFO] Demarrage automatique du telechargement dans 5 secondes...")
    print("(Appuyez sur Ctrl+C pour annuler)")
    import time
    try:
        for i in range(5, 0, -1):
            print(f"  Demarrage dans {i}...")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPT] Telechargement annule par l'utilisateur.")
        sys.exit(0)
    
    print("\n[INFO] Demarrage du telechargement...")
    
    # Telecharger le modele
    success = download_kimi_k25()
    
    if success:
        print("\n" + "=" * 70)
        print("PROCHAINES ETAPES")
        print("=" * 70)
        print("\n1. UTILISATION AVEC LLAMA.CPP:")
        print("   git clone https://github.com/ggml-org/llama.cpp")
        print("   cd llama.cpp")
        print("   cmake -B build -DGGML_CUDA=ON")
        print("   cmake --build build --config Release")
        print("\n2. LANCEMENT DU SERVEUR:")
        print("   .\\build\\bin\\Release\\llama-server.exe ")
        print("     -m E:\\Kimi-K2.5\\model\\Kimi-K2.5-UD-Q2_K_XL-00001-of-00005.gguf")
        print("     -c 128000 --host 0.0.0.0 --port 8080")
        print("\n3. ACCES A L'INTERFACE:")
        print("   Ouvrez http://localhost:8080 dans votre navigateur")
        print("\n" + "=" * 70)
    else:
        print("\n" + "=" * 70)
        print("Le telechargement a rencontre des problemes.")
        print("Veuillez consulter les messages d'erreur ci-dessus.")
        print("=" * 70)
    
    input("\nAppuyez sur Entree pour quitter...")
