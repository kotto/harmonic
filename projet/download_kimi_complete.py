#!/usr/bin/env python3
"""
Script pour telecharger le modele Kimi K2.5 COMPLET (non quantifie)
Taille: environ 630 Go (format FP8)
"""

import os
import sys
from huggingface_hub import snapshot_download

def download_kimi_k25_complete():
    """Telecharge le modele Kimi K2.5 COMPLET"""
    
    # Repertoire de destination sur E:
    local_dir = "E:\\Kimi-K2.5-Complete\\model"
    
    # Creer le repertoire s'il n'existe pas
    os.makedirs(local_dir, exist_ok=True)
    
    print("=" * 70)
    print("TELECHARGEMENT DU MODELE KIMI K2.5 COMPLET")
    print("=" * 70)
    print(f"Destination: {local_dir}")
    print("\n[AVERTISSEMENT IMPORTANT]")
    print("- Taille du modele: environ 630 Go (format FP8)")
    print("- Temps de telechargement: 15-30 heures selon votre connexion")
    print("- Espace disque requis: minimum 650 Go libre")
    print("- Le telechargement peut etre interrompu et repris")
    print("\n" + "=" * 70)
    
    try:
        # Telecharger le modele COMPLET depuis le repo officiel
        # Le modele complet est disponible au format FP8 (8-bit floating point)
        model_id = "moonshotai/Kimi-K2.5"
        
        print(f"\n[TELECHARGEMENT]")
        print(f"Source: {model_id}")
        print(f"Format: FP8 (8-bit floating point)")
        print(f"Taille estimée: ~630 Go")
        print(f"\nDebut du telechargement...")
        print("(Cette operation peut prendre plusieurs heures)")
        print("-" * 70)
        
        # Telecharger le modele complet
        # Nous excluons les fichiers de documentation pour economiser de l'espace
        snapshot_download(
            repo_id=model_id,
            local_dir=local_dir,
            ignore_patterns=[
                "*.md",           # Fichiers markdown
                "*.txt",          # Fichiers texte (sauf license)
                "*.png",          # Images
                "*.jpg",
                "*.jpeg",
                "*.gif",
                "*.svg",
                "*.pdf",          # Documents PDF
                "examples/**/*",  # Dossier examples
                "scripts/**/*",   # Dossier scripts
            ],
            local_dir_use_symlinks=False,
            resume_download=True,  # Permet de reprendre le telechargement
            max_workers=4,         # Nombre de workers paralleles
            tqdm_class=None        # Desactive la barre de progression pour eviter les erreurs
        )
        
        print("\n" + "=" * 70)
        print("[SUCCESS] Telechargement termine avec succes!")
        print("=" * 70)
        print(f"\nModele disponible dans: {local_dir}")
        
        # Lister les fichiers telecharges
        print("\n[FICHIERS TELECHARGES]")
        print("-" * 70)
        
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(local_dir):
            level = root.replace(local_dir, '').count(os.sep)
            indent = '  ' * level
            rel_path = os.path.relpath(root, local_dir)
            if rel_path != '.':
                print(f"{indent}[{os.path.basename(root)}/]")
            
            subindent = '  ' * (level + 1)
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                total_size += file_size
                file_count += 1
                file_size_gb = file_size / (1024**3)
                print(f"{subindent}- {file} ({file_size_gb:.2f} Go)")
        
        print("-" * 70)
        print(f"\n[STATISTIQUES]")
        print(f"  Nombre de fichiers: {file_count}")
        print(f"  Taille totale: {total_size / (1024**3):.2f} Go ({total_size / (1024**2):.0f} Mo)")
        print(f"  Taille moyenne par fichier: {(total_size / file_count) / (1024**2):.2f} Mo")
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("[ERROR] Erreur lors du telechargement!")
        print("=" * 70)
        print(f"\nDetails de l'erreur: {e}")
        print("\n[VERIFICATIONS]")
        print("Veuillez verifier les points suivants:")
        print("  1. Espace disque: Au moins 650 Go libre sur E:")
        print("  2. Connexion internet: Connexion stable et rapide")
        print("  3. Permissions: Droit d'ecriture sur le disque E:")
        print("  4. Hugging Face: Token valide si le modele est prive")
        print("\n[SOLUTIONS POSSIBLES]")
        print("  - Relancez le script: il reprendra ou il s'est arrete")
        print("  - Utilisez un gestionnaire de telechargement")
        print("  - Contactez le support Hugging Face si le probleme persiste")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("KIMI K2.5 - TELECHARGEMENT DU MODELE COMPLET")
    print("=" * 70)
    
    # Lancer le telechargement directement
    success = download_kimi_k25_complete()
    
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
        print("     -m E:\\Kimi-K2.5-Complete\\model\\model-00001-of-00005.safetensors")
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
