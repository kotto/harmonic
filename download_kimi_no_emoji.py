#!/usr/bin/env python3
"""
Script pour télécharger le modèle Kimi K2.5 sans émojis
"""

import os
import sys
import time
from huggingface_hub import hf_hub_download

def download_model_parts():
    """Télécharge les parties du modèle une par une"""
    
    repo_id = "unsloth/Kimi-K2.5-GGUF"
    local_dir = "E:\\Kimi-K2.5\\model"
    
    # Créer le répertoire
    os.makedirs(local_dir, exist_ok=True)
    
    print("=" * 60)
    print("Téléchargement du modèle Kimi K2.5 (version UD-TQ1_0)")
    print("=" * 60)
    print(f"Repertoire: {local_dir}")
    print(f"Referentiel: {repo_id}")
    print("\nCette operation peut prendre plusieurs heures...")
    print("Chaque fichier fait environ 48-50 Go.")
    print("\n" + "=" * 60)
    
    # Liste des fichiers à télécharger (version 1.8-bit)
    files_to_download = [
        "UD-TQ1_0/Kimi-K2.5-UD-TQ1_0-00001-of-00005.gguf",
        "UD-TQ1_0/Kimi-K2.5-UD-TQ1_0-00002-of-00005.gguf",
        "UD-TQ1_0/Kimi-K2.5-UD-TQ1_0-00003-of-00005.gguf",
        "UD-TQ1_0/Kimi-K2.5-UD-TQ1_0-00004-of-00005.gguf",
        "UD-TQ1_0/Kimi-K2.5-UD-TQ1_0-00005-of-00005.gguf"
    ]
    
    total_files = len(files_to_download)
    downloaded_files = 0
    total_size_gb = 0
    
    print(f"Fichiers a telecharger: {total_files}")
    
    for i, file_path in enumerate(files_to_download, 1):
        print(f"\n--- Telechargement du fichier {i}/{total_files} ---")
        print(f"  {file_path}")
        
        try:
            # Extraire le nom de fichier
            filename = os.path.basename(file_path)
            
            print(f"  Debut du telechargement...")
            start_time = time.time()
            
            # Télécharger le fichier
            local_file_path = hf_hub_download(
                repo_id=repo_id,
                filename=file_path,
                local_dir=local_dir,
                resume_download=True,
                local_dir_use_symlinks=False
            )
            
            # Calculer le temps et la taille
            end_time = time.time()
            download_time = end_time - start_time
            
            # Obtenir la taille du fichier
            file_size = os.path.getsize(local_file_path)
            file_size_gb = file_size / (1024**3)
            total_size_gb += file_size_gb
            
            # Calculer la vitesse
            speed_mbps = (file_size * 8) / (download_time * 1000000) if download_time > 0 else 0
            
            print(f"  OK - Telecharge avec succes!")
            print(f"  Taille: {file_size_gb:.2f} Go")
            print(f"  Temps: {download_time:.1f} secondes")
            print(f"  Vitesse: {speed_mbps:.2f} Mbps")
            print(f"  Emplacement: {local_file_path}")
            
            downloaded_files += 1
            
            # Pause entre les téléchargements
            if i < total_files:
                print(f"\nPause de 5 secondes avant le prochain fichier...")
                time.sleep(5)
            
        except Exception as e:
            print(f"  ERREUR lors du telechargement: {e}")
            print(f"  Le telechargement peut etre repris plus tard.")
            print(f"  Vous pouvez relancer ce script pour reprendre le telechargement.")
            return False
    
    print(f"\n" + "=" * 60)
    print(f"TELECHARGEMENT TERMINE!")
    print(f"Total telecharge: {total_size_gb:.2f} Go")
    print(f"Repertoire: {local_dir}")
    
    # Lister les fichiers téléchargés
    print(f"\nListe des fichiers:")
    for root, dirs, files in os.walk(local_dir):
        for file in files:
            if file.endswith('.gguf'):
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                file_size_gb = file_size / (1024**3)
                print(f"  - {file} ({file_size_gb:.2f} Go)")
    
    return True

def check_disk_space():
    """Vérifie l'espace disque disponible"""
    import shutil
    
    try:
        total, used, free = shutil.disk_usage("E:\\")
        
        print("Verification de l'espace disque E::")
        print(f"  Total: {total / (1024**3):.2f} Go")
        print(f"  Utilise: {used / (1024**3):.2f} Go")
        print(f"  Libre: {free / (1024**3):.2f} Go")
        
        # Espace nécessaire (version 1.8-bit, environ 240 Go)
        required_space_gb = 250
        required_space = required_space_gb * (1024**3)
        
        if free < required_space:
            print(f"\nATTENTION: Espace insuffisant!")
            print(f"  Espace libre: {free / (1024**3):.2f} Go")
            print(f"  Espace requis: {required_space_gb} Go")
            return False
        
        print(f"\nOK - Espace disque suffisant!")
        return True
        
    except Exception as e:
        print(f"ERREUR lors de la verification de l'espace disque: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Telechargement securise du modele Kimi K2.5")
    print("=" * 60)
    
    # Vérifier l'espace disque
    if not check_disk_space():
        print("\nVeuillez liberer de l'espace sur le disque E: avant de continuer.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    
    # Avertissement sur la taille
    print("ATTENTION: Ce modele est tres grand (environ 240 Go).")
    print("   Le telechargement peut prendre plusieurs heures.")
    print("   Assurez-vous d'avoir une connexion internet stable.")
    print("   Vous pouvez interrompre et reprendre le telechargement plus tard.")
    
    response = input("\nVoulez-vous commencer le telechargement? (oui/non): ").strip().lower()
    
    if response not in ['oui', 'o', 'yes', 'y']:
        print("Telechargement annule.")
        sys.exit(0)
    
    # Télécharger le modèle
    print("\n" + "=" * 60)
    success = download_model_parts()
    
    if success:
        print("\n" + "=" * 60)
        print("FELICITATIONS! Le modele a ete telecharge avec succes.")
        print("=" * 60)
        print("\nPour utiliser le modele avec llama.cpp:")
        print("   1. Installez llama.cpp: https://github.com/ggml-org/llama.cpp")
        print("   2. Compilez avec CUDA: cmake -B build -DGGML_CUDA=ON")
        print("   3. Lancez le serveur:")
        print("      ./build/bin/llama-server -m E:\\Kimi-K2.5\\model\\Kimi-K2.5-UD-TQ1_0-00001-of-00005.gguf")
        print("   4. Accedez a l'interface: http://localhost:8080")
        
        print("\nConseil: Pour une utilisation optimale, assurez-vous d'avoir")
        print("   au moins 32 Go de RAM et une carte graphique NVIDIA recente.")
    else:
        print("\nERREUR: Le telechargement a echoue ou a ete interrompu.")
        print("   Vous pouvez relancer ce script pour reprendre le telechargement.")